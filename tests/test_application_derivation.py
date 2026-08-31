from __future__ import annotations

from validation_helpers import complete_runtime_graph

from skill_eval_framework.schemas.runtime import PlannedAttemptSlot, RunTestCaseDisposition
from skill_eval_framework.validation import (
    derive_expected_applications,
    derive_expected_episode_applications,
    derive_expected_gate_applications,
    derive_expected_grader_applications,
    derive_expected_metric_applications,
    derive_missing_applications,
)


def test_expected_episode_applications_follow_scheduled_slots() -> None:
    graph = complete_runtime_graph()
    expected = derive_expected_episode_applications(graph.run)
    assert [item.logical_key for item in expected] == [("episode", "TC001", 1)]


def test_intentionally_unscheduled_case_has_no_episode_application() -> None:
    graph = complete_runtime_graph()
    test_case = graph.run.execution_plan.test_cases[0].model_copy(
        update={
            "disposition": RunTestCaseDisposition.INTENTIONALLY_NOT_SCHEDULED,
            "attempt_slots": [],
            "reason": "Not in this run.",
        }
    )
    graph.run = graph.run.model_copy(
        update={
            "execution_plan": graph.run.execution_plan.model_copy(
                update={"test_cases": [test_case]}
            )
        }
    )
    assert derive_expected_episode_applications(graph.run) == ()


def test_completed_episode_derives_authoritative_grader_application() -> None:
    graph = complete_runtime_graph()
    expected = derive_expected_grader_applications(graph.benchmark, graph.episodes)
    assert [item.logical_key for item in expected] == [
        ("grader_result", "E001", "G001", "TC001", "C001")
    ]


def test_failed_episode_does_not_require_grader_application() -> None:
    graph = complete_runtime_graph()
    graph.episodes[0] = graph.episodes[0].model_copy(update={"execution_status": "failed"})
    assert derive_expected_grader_applications(graph.benchmark, graph.episodes) == ()


def test_repeated_episode_slots_produce_distinct_expected_applications() -> None:
    graph = complete_runtime_graph()
    plan = graph.run.execution_plan.test_cases[0]
    plan = plan.model_copy(
        update={"attempt_slots": [*plan.attempt_slots, PlannedAttemptSlot(attempt_index=2)]}
    )
    graph.run = graph.run.model_copy(
        update={
            "execution_plan": graph.run.execution_plan.model_copy(update={"test_cases": [plan]})
        }
    )
    expected = derive_expected_episode_applications(graph.run)
    assert [item.logical_key for item in expected] == [
        ("episode", "TC001", 1),
        ("episode", "TC001", 2),
    ]


def test_each_metric_specification_has_one_expected_application() -> None:
    graph = complete_runtime_graph()
    expected = derive_expected_metric_applications(graph.benchmark)
    assert [item.logical_key for item in expected] == [("metric_result", "M001")]


def test_each_gate_specification_has_one_expected_application() -> None:
    graph = complete_runtime_graph()
    expected = derive_expected_gate_applications(graph.benchmark)
    assert [item.logical_key for item in expected] == [("gate_result", "GATE001")]


def test_gate_derivation_is_independent_of_acceptance_participation() -> None:
    graph = complete_runtime_graph()
    graph.benchmark.gate_specifications.append(
        graph.benchmark.gate_specifications[0].model_copy(update={"gate_id": "GATE002"})
    )
    assert {item.gate_id for item in derive_expected_gate_applications(graph.benchmark)} == {
        "GATE001",
        "GATE002",
    }


def test_missing_application_derivation_is_pure_and_typed() -> None:
    graph = complete_runtime_graph()
    expected = derive_expected_applications(graph.benchmark, graph.run, graph.episodes)
    before = graph.scorecard.result_inventory.model_dump()
    missing = derive_missing_applications(
        expected,
        graph.episodes,
        graph.grader_results,
        [],
        graph.gate_results,
    )
    assert [item.application_ref.logical_key for item in missing] == [("metric_result", "M001")]
    assert graph.scorecard.result_inventory.model_dump() == before
    assert all(item.diagnostic_ids == [] for item in missing)


def test_expected_application_order_is_stable_when_episodes_are_shuffled() -> None:
    graph = complete_runtime_graph()
    test_case = graph.run.execution_plan.test_cases[0]
    test_case = test_case.model_copy(
        update={
            "attempt_slots": [
                *test_case.attempt_slots,
                PlannedAttemptSlot(attempt_index=2),
            ]
        }
    )
    graph.run = graph.run.model_copy(
        update={
            "execution_plan": graph.run.execution_plan.model_copy(
                update={"test_cases": [test_case]}
            )
        }
    )
    graph.episodes.append(
        graph.episodes[0].model_copy(update={"episode_id": "E002", "attempt_index": 2})
    )
    first = derive_expected_applications(graph.benchmark, graph.run, graph.episodes)
    graph.episodes.reverse()
    second = derive_expected_applications(graph.benchmark, graph.run, graph.episodes)
    assert first == second
