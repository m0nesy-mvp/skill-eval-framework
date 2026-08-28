from __future__ import annotations

from validation_helpers import codes, complete_runtime_graph

from skill_eval_framework.schemas.definition import EvidenceTarget
from skill_eval_framework.schemas.runtime import (
    PlannedAttemptSlot,
    RunExecutionPlan,
    RunValidityStatus,
)


def test_complete_runtime_graph_is_valid() -> None:
    assert complete_runtime_graph().validate().is_valid


def test_plan_must_cover_definition_test_case() -> None:
    graph = complete_runtime_graph()
    graph.run.execution_plan = RunExecutionPlan(test_cases=[])
    assert "RUN_PLAN_TEST_CASE_MISSING" in codes(graph.validate())


def test_unknown_plan_test_case_is_reported() -> None:
    graph = complete_runtime_graph()
    graph.run.execution_plan.test_cases[0].test_case_id = "TC999"
    assert "RUN_PLAN_TEST_CASE_UNKNOWN" in codes(graph.validate())


def test_duplicate_plan_test_case_is_reported() -> None:
    graph = complete_runtime_graph()
    graph.run.execution_plan.test_cases.append(graph.run.execution_plan.test_cases[0].model_copy())
    assert "RUN_PLAN_TEST_CASE_DUPLICATE" in codes(graph.validate())


def test_episode_without_planned_slot_is_reported() -> None:
    graph = complete_runtime_graph()
    graph.episodes[0].attempt_index = 2
    assert "RUN_UNPLANNED_EPISODE" in codes(graph.validate())


def test_duplicate_episode_logical_key_is_reported() -> None:
    graph = complete_runtime_graph()
    graph.episodes.append(graph.episodes[0].model_copy(update={"episode_id": "E002"}))
    assert "RUN_EPISODE_LOGICAL_DUPLICATE" in codes(graph.validate())


def test_artifact_relation_cannot_cross_runs() -> None:
    graph = complete_runtime_graph()
    graph.artifacts[0].relations[0].episode_id = "E999"
    graph.episodes.append(
        graph.episodes[0].model_copy(update={"episode_id": "E999", "run_id": "OTHER"})
    )
    assert "RUN_CROSS_RUN_REFERENCE" in codes(graph.validate())


def test_evidence_episode_cannot_cross_runs() -> None:
    graph = complete_runtime_graph()
    graph.evidence[0].episode_id = "E999"
    graph.episodes.append(
        graph.episodes[0].model_copy(update={"episode_id": "E999", "run_id": "OTHER"})
    )
    assert "RUN_CROSS_RUN_REFERENCE" in codes(graph.validate())


def test_evidence_target_must_match_episode() -> None:
    graph = complete_runtime_graph()
    graph.evidence[0].qualified_targets = [EvidenceTarget(test_case_id="TC999", contract_id="C001")]
    assert "RUN_EVIDENCE_TARGET_INVALID" in codes(graph.validate())


def test_grader_evidence_spec_must_be_compatible() -> None:
    graph = complete_runtime_graph()
    graph.evidence[0].evidence_spec_id = "ES999"
    assert "RUN_GRADER_EVIDENCE_INCOMPATIBLE" in codes(graph.validate())


def test_grader_target_must_match_definition() -> None:
    graph = complete_runtime_graph()
    graph.grader_results[0].contract_id = "C999"
    assert "RUN_GRADER_TARGET_INVALID" in codes(graph.validate())


def test_duplicate_grader_logical_key_is_reported() -> None:
    graph = complete_runtime_graph()
    graph.grader_results.append(
        graph.grader_results[0].model_copy(update={"grader_result_id": "GR002"})
    )
    assert "RUN_GRADER_LOGICAL_DUPLICATE" in codes(graph.validate())


def test_metric_input_must_be_same_run() -> None:
    graph = complete_runtime_graph()
    foreign = graph.grader_results[0].model_copy(
        update={"grader_result_id": "GR999", "run_id": "OTHER"}
    )
    graph.grader_results.append(foreign)
    graph.metric_results[0].input_traces[0].grader_result_id = "GR999"
    assert "RUN_CROSS_RUN_REFERENCE" in codes(graph.validate())


def test_metric_input_outside_population_is_reported() -> None:
    graph = complete_runtime_graph()
    graph.grader_results[0].contract_id = "C999"
    assert "RUN_METRIC_INPUT_OUTSIDE_POPULATION" in codes(graph.validate())


def test_metric_input_must_use_authoritative_grader() -> None:
    graph = complete_runtime_graph()
    graph.grader_results[0].grader_id = "G999"
    assert "RUN_METRIC_GRADER_TARGET_INVALID" in codes(graph.validate())


def test_duplicate_metric_logical_key_is_reported() -> None:
    graph = complete_runtime_graph()
    graph.metric_results.append(
        graph.metric_results[0].model_copy(update={"metric_result_id": "MR002"})
    )
    assert "RUN_METRIC_LOGICAL_DUPLICATE" in codes(graph.validate())


def test_gate_metric_input_must_be_same_run() -> None:
    graph = complete_runtime_graph()
    foreign = graph.metric_results[0].model_copy(
        update={"metric_result_id": "MR999", "run_id": "OTHER"}
    )
    graph.metric_results.append(foreign)
    graph.gate_results[0].input_summary.metric_result_id = "MR999"
    assert "RUN_CROSS_RUN_REFERENCE" in codes(graph.validate())


def test_duplicate_gate_logical_key_is_reported() -> None:
    graph = complete_runtime_graph()
    graph.gate_results.append(
        graph.gate_results[0].model_copy(update={"gate_result_id": "GATER002"})
    )
    assert "RUN_GATE_LOGICAL_DUPLICATE" in codes(graph.validate())


def test_diagnostic_reference_must_resolve() -> None:
    graph = complete_runtime_graph()
    graph.run.diagnostic_ids = ["D999"]
    assert "RUN_DIAGNOSTIC_REF_UNKNOWN" in codes(graph.validate())


def test_run_validity_status_must_match_finalized_scorecard() -> None:
    graph = complete_runtime_graph()
    graph.run.validity_status = RunValidityStatus.PENDING
    assert "RUN_FINALIZED_EVALUATION_REQUIRES_VALID_RUN" in codes(graph.validate())


def test_cross_run_grader_episode_is_reported() -> None:
    graph = complete_runtime_graph()
    graph.grader_results[0].episode_id = "E999"
    assert "RUN_GRADER_EPISODE_UNKNOWN" in codes(graph.validate())


def test_runtime_issue_order_is_deterministic() -> None:
    first = complete_runtime_graph()
    first.episodes.append(
        first.episodes[0].model_copy(update={"episode_id": "E002", "attempt_index": 2})
    )
    first.run.execution_plan = first.run.execution_plan.model_copy(
        update={
            "test_cases": [
                first.run.execution_plan.test_cases[0].model_copy(
                    update={"attempt_slots": [PlannedAttemptSlot(attempt_index=1)]}
                )
            ]
        }
    )
    second = first.clone()
    second.episodes.reverse()
    assert first.validate().issues == second.validate().issues
