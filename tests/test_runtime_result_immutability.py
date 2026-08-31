from __future__ import annotations

import pytest
from pydantic import ValidationError
from validation_helpers import complete_runtime_graph

from skill_eval_framework.runtime import (
    admit_retry_attempt,
    create_interim_scorecard,
    finalize_scorecard,
    transition_run_execution,
)
from skill_eval_framework.schemas.runtime import RunExecutionStatus, RunValidityStatus


def test_terminal_run_rejects_execution_status_assignment() -> None:
    run = complete_runtime_graph().run

    with pytest.raises(ValidationError, match="Instance is frozen"):
        run.execution_status = RunExecutionStatus.RUNNING

    assert run.execution_status == RunExecutionStatus.COMPLETED


def test_terminal_run_rejects_validity_reversal_assignment() -> None:
    run = complete_runtime_graph().run

    with pytest.raises(ValidationError, match="Instance is frozen"):
        run.validity_status = RunValidityStatus.PENDING

    assert run.validity_status == RunValidityStatus.VALID


def test_finalized_scorecard_rejects_assignment() -> None:
    scorecard = complete_runtime_graph().scorecard

    with pytest.raises(ValidationError, match="Instance is frozen"):
        scorecard.finalization_status = "interim"

    assert scorecard.finalization_status.value == "finalized_evaluation"


def test_authoritative_results_reject_assignment() -> None:
    graph = complete_runtime_graph()

    for result in (
        graph.grader_results[0],
        graph.metric_results[0],
        graph.gate_results[0],
    ):
        with pytest.raises(ValidationError, match="Instance is frozen"):
            result.run_id = "OTHER"
        assert result.run_id == graph.run.run_id


def test_transition_returns_detached_nested_snapshot() -> None:
    graph = complete_runtime_graph()
    old = graph.run.model_copy(
        update={
            "execution_status": RunExecutionStatus.RUNNING,
            "validity_status": RunValidityStatus.PENDING,
            "ended_at": None,
        }
    )
    new = transition_run_execution(
        old,
        RunExecutionStatus.COMPLETED,
        timestamp=graph.run.ended_at,
    )

    assert new is not old
    assert new.execution_plan is not old.execution_plan
    assert new.execution_plan.test_cases is not old.execution_plan.test_cases
    assert new.execution_plan.test_cases[0] is not old.execution_plan.test_cases[0]
    assert (
        new.execution_plan.test_cases[0].attempt_slots
        is not old.execution_plan.test_cases[0].attempt_slots
    )

    old_dump = old.model_dump()
    new_dump = new.model_dump()
    with pytest.raises(TypeError, match="collections are immutable"):
        old.execution_plan.test_cases.clear()
    with pytest.raises(TypeError, match="collections are immutable"):
        new.execution_plan.test_cases.clear()
    assert old.model_dump() == old_dump
    assert new.model_dump() == new_dump


def test_execution_plan_retry_is_detached_from_source_plan() -> None:
    graph = complete_runtime_graph()
    old = graph.run.execution_plan
    new = admit_retry_attempt(old, "TC001")

    assert new is not old
    assert new.test_cases is not old.test_cases
    assert new.test_cases[0] is not old.test_cases[0]
    assert new.test_cases[0].attempt_slots is not old.test_cases[0].attempt_slots
    assert [slot.attempt_index for slot in old.test_cases[0].attempt_slots] == [1]
    assert [slot.attempt_index for slot in new.test_cases[0].attempt_slots] == [1, 2]

    with pytest.raises(TypeError, match="collections are immutable"):
        old.test_cases[0].attempt_slots.append(new.test_cases[0].attempt_slots[-1])
    with pytest.raises(TypeError, match="collections are immutable"):
        new.test_cases[0].attempt_slots.pop()


def test_transition_detaches_episode_and_diagnostic_id_collections() -> None:
    graph = complete_runtime_graph()
    old = graph.run.model_copy(
        update={
            "execution_status": RunExecutionStatus.RUNNING,
            "validity_status": RunValidityStatus.PENDING,
            "ended_at": None,
            "diagnostic_ids": ["D001"],
        }
    )
    new = transition_run_execution(
        old,
        RunExecutionStatus.COMPLETED,
        timestamp=graph.run.ended_at,
    )

    assert new.episode_ids is not old.episode_ids
    assert new.diagnostic_ids is not old.diagnostic_ids
    with pytest.raises(TypeError, match="collections are immutable"):
        old.episode_ids.append("E002")
    with pytest.raises(TypeError, match="collections are immutable"):
        new.diagnostic_ids.append("D002")
    assert old.episode_ids == new.episode_ids == ["E001"]
    assert old.diagnostic_ids == new.diagnostic_ids == ["D001"]


def test_transition_detaches_and_freezes_nested_metadata_dicts() -> None:
    graph = complete_runtime_graph()
    old = graph.run.model_copy(
        update={
            "execution_status": RunExecutionStatus.RUNNING,
            "validity_status": RunValidityStatus.PENDING,
            "ended_at": None,
        }
    )
    new = transition_run_execution(
        old,
        RunExecutionStatus.COMPLETED,
        timestamp=graph.run.ended_at,
    )

    assert new.execution_context.context_metadata is not old.execution_context.context_metadata
    assert new.subject_ref.identity_metadata is not old.subject_ref.identity_metadata
    with pytest.raises(TypeError, match="collections are immutable"):
        old.execution_context.context_metadata["profile"] = "changed"
    with pytest.raises(TypeError, match="collections are immutable"):
        new.subject_ref.identity_metadata.update({"revision_number": 2})
    assert old.execution_context.context_metadata == {"profile": "test"}
    assert new.execution_context.context_metadata == {"profile": "test"}
    assert old.subject_ref.identity_metadata == {
        "platform": "windows",
        "revision_number": 1,
    }
    assert new.subject_ref.identity_metadata == {
        "platform": "windows",
        "revision_number": 1,
    }


def test_scorecard_finalization_detaches_and_freezes_inventory() -> None:
    graph = complete_runtime_graph()
    interim = create_interim_scorecard(
        scorecard_id="SC002",
        benchmark=graph.benchmark,
        run=graph.run,
        episodes=graph.episodes,
        grader_results=graph.grader_results,
        metric_results=graph.metric_results,
        gate_results=graph.gate_results,
        overall_score_outcome=graph.scorecard.overall_score_outcome,
        acceptance_evaluation=graph.scorecard.acceptance_evaluation,
    )
    finalized = finalize_scorecard(
        scorecard=interim,
        benchmark=graph.benchmark,
        run=graph.run,
        episodes=graph.episodes,
        artifacts=graph.artifacts,
        evidence=graph.evidence,
        grader_results=graph.grader_results,
        metric_results=graph.metric_results,
        gate_results=graph.gate_results,
        diagnostics=graph.diagnostics,
        overall_score_outcome=graph.scorecard.overall_score_outcome,
        acceptance_evaluation=graph.scorecard.acceptance_evaluation,
        finalization_status="finalized_audit",
        finalized_at=graph.run.ended_at,
    )

    assert finalized.result_inventory is not interim.result_inventory
    assert finalized.result_inventory.episode_ids is not interim.result_inventory.episode_ids
    assert (
        finalized.result_inventory.missing_applications
        is not interim.result_inventory.missing_applications
    )
    with pytest.raises(TypeError, match="collections are immutable"):
        interim.result_inventory.episode_ids.append("E002")
    with pytest.raises(TypeError, match="collections are immutable"):
        finalized.result_inventory.metric_result_ids.clear()
    assert interim.result_inventory.episode_ids == finalized.result_inventory.episode_ids
    assert (
        interim.result_inventory.metric_result_ids == finalized.result_inventory.metric_result_ids
    )
