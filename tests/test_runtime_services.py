from __future__ import annotations

from copy import deepcopy

import pytest
from validation_helpers import complete_runtime_graph

from skill_eval_framework.runtime import (
    ExecutionPlanError,
    IntegrityFinalizationError,
    InvalidTransitionError,
    RuntimeServiceError,
    admit_retry_attempt,
    build_final_inventory,
    build_interim_inventory,
    build_scorecard_inventory,
    create_episode_for_slot,
    create_interim_scorecard,
    create_run,
    expected_applications_for_run,
    finalize_run_validity,
    finalize_scorecard,
    is_execution_plan_sealed,
    make_runtime_diagnostic,
    missing_applications_for_final_inventory,
    prevalidate_run,
    transition_episode,
    transition_run_execution,
)
from skill_eval_framework.schemas.runtime import (
    DiagnosticPhase,
    EpisodeExecutionStatus,
    ObjectRef,
    ObjectType,
    PlannedAttemptSlot,
    RunExecutionPlan,
    RunExecutionStatus,
    RunTestCaseDisposition,
    RunTestCasePlan,
    RunValidityStatus,
    ValidityFinding,
    ValidityStage,
)


def test_create_run_starts_pending_and_created() -> None:
    graph = complete_runtime_graph()
    created = create_run(
        run_id="RUN002",
        definition_ref=graph.run.definition_ref,
        subject_ref=graph.run.subject_ref,
        execution_context=graph.run.execution_context,
        execution_plan=graph.run.execution_plan,
        created_at=graph.run.created_at,
    )
    assert created.execution_status == RunExecutionStatus.CREATED
    assert created.validity_status == RunValidityStatus.PENDING
    assert created.validity_findings == []
    assert created.episode_ids == []


def test_preflight_pass_preserves_pending_validity() -> None:
    graph = complete_runtime_graph()
    run = graph.run.model_copy(
        update={
            "execution_status": RunExecutionStatus.CREATED,
            "validity_status": RunValidityStatus.PENDING,
            "started_at": None,
            "ended_at": None,
            "episode_ids": [],
        }
    )
    checked = prevalidate_run(graph.benchmark, run)
    assert checked.validity_status == RunValidityStatus.PENDING
    assert checked.validity_findings == []
    assert run.validity_status == RunValidityStatus.PENDING


def test_preflight_definition_failure_returns_invalid_run() -> None:
    graph = complete_runtime_graph()
    graph.benchmark.contracts[0].requirement_ids = ["R999"]
    run = graph.run.model_copy(
        update={"validity_status": RunValidityStatus.PENDING, "validity_findings": []}
    )
    checked = prevalidate_run(graph.benchmark, run)
    assert checked.validity_status == RunValidityStatus.INVALID
    assert checked.validity_findings
    assert checked.validity_findings[0].stage == ValidityStage.PRE_EXECUTION


def test_preflight_invalid_plan_returns_invalid_run() -> None:
    graph = complete_runtime_graph()
    run = graph.run.model_copy(
        update={
            "execution_plan": RunExecutionPlan(test_cases=[]),
            "execution_status": RunExecutionStatus.CREATED,
            "validity_status": RunValidityStatus.PENDING,
            "validity_findings": [],
            "started_at": None,
            "ended_at": None,
            "episode_ids": [],
        }
    )
    checked = prevalidate_run(graph.benchmark, run)
    assert checked.validity_status == RunValidityStatus.INVALID
    assert any(item.code == "RUN_PLAN_TEST_CASE_MISSING" for item in checked.validity_findings)


def test_preflight_rejects_already_finalized_validity() -> None:
    graph = complete_runtime_graph()
    with pytest.raises(InvalidTransitionError):
        prevalidate_run(graph.benchmark, graph.run)


def test_execution_transition_does_not_change_validity() -> None:
    graph = complete_runtime_graph()
    run = graph.run.model_copy(
        update={
            "execution_status": RunExecutionStatus.CREATED,
            "validity_status": RunValidityStatus.PENDING,
            "started_at": None,
            "ended_at": None,
            "episode_ids": [],
        }
    )
    transitioned = transition_run_execution(
        run,
        RunExecutionStatus.RUNNING,
        timestamp=graph.run.created_at,
    )
    assert transitioned.execution_status == RunExecutionStatus.RUNNING
    assert transitioned.validity_status == RunValidityStatus.PENDING
    assert run.execution_status == RunExecutionStatus.CREATED


def test_run_transition_running_to_completed_sets_end_time() -> None:
    graph = complete_runtime_graph()
    run = graph.run.model_copy(
        update={
            "execution_status": RunExecutionStatus.RUNNING,
            "validity_status": RunValidityStatus.PENDING,
            "ended_at": None,
        }
    )
    transitioned = transition_run_execution(
        run,
        RunExecutionStatus.COMPLETED,
        timestamp=graph.run.ended_at,
    )
    assert transitioned.execution_status == RunExecutionStatus.COMPLETED
    assert transitioned.ended_at == graph.run.ended_at


def test_run_created_to_completed_is_not_assumed_allowed() -> None:
    graph = complete_runtime_graph()
    run = graph.run.model_copy(
        update={
            "execution_status": RunExecutionStatus.CREATED,
            "validity_status": RunValidityStatus.PENDING,
            "started_at": None,
            "ended_at": None,
            "episode_ids": [],
        }
    )
    with pytest.raises(InvalidTransitionError):
        transition_run_execution(run, RunExecutionStatus.COMPLETED, timestamp=graph.run.created_at)


def test_run_created_to_blocked_is_supported() -> None:
    graph = complete_runtime_graph()
    run = graph.run.model_copy(
        update={
            "execution_status": RunExecutionStatus.CREATED,
            "validity_status": RunValidityStatus.PENDING,
            "started_at": None,
            "ended_at": None,
            "episode_ids": [],
        }
    )
    blocked = transition_run_execution(
        run, RunExecutionStatus.BLOCKED, timestamp=graph.run.ended_at
    )
    assert blocked.execution_status == RunExecutionStatus.BLOCKED
    assert blocked.started_at is None
    assert blocked.ended_at == graph.run.ended_at


def test_run_created_to_cancelled_is_supported() -> None:
    graph = complete_runtime_graph()
    run = graph.run.model_copy(
        update={
            "execution_status": RunExecutionStatus.CREATED,
            "validity_status": RunValidityStatus.PENDING,
            "started_at": None,
            "ended_at": None,
            "episode_ids": [],
        }
    )
    cancelled = transition_run_execution(
        run,
        RunExecutionStatus.CANCELLED,
        timestamp=graph.run.ended_at,
    )
    assert cancelled.execution_status == RunExecutionStatus.CANCELLED
    assert cancelled.ended_at == graph.run.ended_at


def test_run_terminal_status_cannot_transition_again() -> None:
    graph = complete_runtime_graph()
    with pytest.raises(InvalidTransitionError):
        transition_run_execution(
            graph.run,
            RunExecutionStatus.RUNNING,
            timestamp=graph.run.created_at,
        )


def test_admit_retry_appends_next_attempt_without_mutating_plan() -> None:
    graph = complete_runtime_graph()
    original = deepcopy(graph.run.execution_plan.model_dump())
    updated = admit_retry_attempt(graph.run.execution_plan, "TC001")
    assert [slot.attempt_index for slot in updated.test_cases[0].attempt_slots] == [1, 2]
    assert graph.run.execution_plan.model_dump() == original


def test_admit_retry_uses_next_max_index_without_reuse() -> None:
    graph = complete_runtime_graph()
    test_case = graph.run.execution_plan.test_cases[0]
    plan = graph.run.execution_plan.model_copy(
        update={
            "test_cases": [
                test_case.model_copy(
                    update={
                        "attempt_slots": [
                            *test_case.attempt_slots,
                            PlannedAttemptSlot(attempt_index=2),
                        ]
                    }
                )
            ]
        }
    )
    updated = admit_retry_attempt(plan, "TC001")
    assert [slot.attempt_index for slot in updated.test_cases[0].attempt_slots] == [1, 2, 3]


def test_admit_retry_unknown_test_case_fails() -> None:
    graph = complete_runtime_graph()
    with pytest.raises(ExecutionPlanError):
        admit_retry_attempt(graph.run.execution_plan, "TC999")


def test_admit_retry_intentionally_unscheduled_fails() -> None:
    graph = complete_runtime_graph()
    plan = graph.run.execution_plan.model_copy(
        update={
            "test_cases": [
                RunTestCasePlan(
                    test_case_id="TC001",
                    disposition=RunTestCaseDisposition.INTENTIONALLY_NOT_SCHEDULED,
                    attempt_slots=[],
                    reason="Excluded for this run.",
                )
            ]
        }
    )
    with pytest.raises(ExecutionPlanError):
        admit_retry_attempt(plan, "TC001")


def test_sealed_run_rejects_retry_admission() -> None:
    graph = complete_runtime_graph()
    assert is_execution_plan_sealed(graph.run)
    with pytest.raises(ExecutionPlanError):
        admit_retry_attempt(graph.run, "TC001")


def test_create_episode_for_valid_slot() -> None:
    graph = complete_runtime_graph()
    run = graph.run.model_copy(
        update={
            "execution_status": RunExecutionStatus.RUNNING,
            "validity_status": RunValidityStatus.PENDING,
            "ended_at": None,
        }
    )
    episode = create_episode_for_slot(
        run,
        [],
        episode_id="E002",
        test_case_id="TC001",
        attempt_index=1,
        created_at=graph.run.created_at,
    )
    assert episode.execution_status == EpisodeExecutionStatus.CREATED
    assert episode.run_id == run.run_id
    assert episode.trace_events == []


def test_create_episode_unplanned_slot_fails() -> None:
    graph = complete_runtime_graph()
    run = graph.run.model_copy(
        update={"execution_status": RunExecutionStatus.RUNNING, "ended_at": None}
    )
    with pytest.raises(ExecutionPlanError):
        create_episode_for_slot(
            run,
            [],
            episode_id="E002",
            test_case_id="TC001",
            attempt_index=2,
            created_at=graph.run.created_at,
        )


def test_create_episode_duplicate_logical_key_fails() -> None:
    graph = complete_runtime_graph()
    run = graph.run.model_copy(
        update={"execution_status": RunExecutionStatus.RUNNING, "ended_at": None}
    )
    with pytest.raises(ExecutionPlanError):
        create_episode_for_slot(
            run,
            graph.episodes,
            episode_id="E002",
            test_case_id="TC001",
            attempt_index=1,
            created_at=graph.run.created_at,
        )


def test_create_episode_sealed_run_fails() -> None:
    graph = complete_runtime_graph()
    with pytest.raises(ExecutionPlanError):
        create_episode_for_slot(
            graph.run,
            [],
            episode_id="E002",
            test_case_id="TC001",
            attempt_index=1,
            created_at=graph.run.created_at,
        )


def test_create_episode_invalid_run_fails() -> None:
    graph = complete_runtime_graph()
    invalid = graph.run.model_copy(update={"validity_status": RunValidityStatus.INVALID})
    with pytest.raises(RuntimeServiceError):
        create_episode_for_slot(
            invalid,
            [],
            episode_id="E002",
            test_case_id="TC001",
            attempt_index=1,
            created_at=graph.run.created_at,
        )


def test_episode_transition_created_to_running_to_completed() -> None:
    graph = complete_runtime_graph()
    episode = graph.episodes[0].model_copy(
        update={
            "execution_status": EpisodeExecutionStatus.CREATED,
            "started_at": None,
            "ended_at": None,
        }
    )
    running = transition_episode(
        episode, EpisodeExecutionStatus.RUNNING, timestamp=graph.run.created_at
    )
    completed = transition_episode(
        running, EpisodeExecutionStatus.COMPLETED, timestamp=graph.run.ended_at
    )
    assert running.started_at == graph.run.created_at
    assert completed.ended_at == graph.run.ended_at
    assert episode.execution_status == EpisodeExecutionStatus.CREATED


def test_terminal_episode_transition_fails() -> None:
    graph = complete_runtime_graph()
    with pytest.raises(InvalidTransitionError):
        transition_episode(
            graph.episodes[0],
            EpisodeExecutionStatus.RUNNING,
            timestamp=graph.run.created_at,
        )


def test_episode_created_to_cancelled_is_supported() -> None:
    graph = complete_runtime_graph()
    episode = graph.episodes[0].model_copy(
        update={
            "execution_status": EpisodeExecutionStatus.CREATED,
            "started_at": None,
            "ended_at": None,
        }
    )
    cancelled = transition_episode(
        episode,
        EpisodeExecutionStatus.CANCELLED,
        timestamp=graph.run.ended_at,
    )
    assert cancelled.execution_status == EpisodeExecutionStatus.CANCELLED
    assert cancelled.ended_at == graph.run.ended_at


def test_episode_running_to_failed_is_supported() -> None:
    graph = complete_runtime_graph()
    episode = graph.episodes[0].model_copy(
        update={"execution_status": EpisodeExecutionStatus.RUNNING, "ended_at": None}
    )
    failed = transition_episode(
        episode,
        EpisodeExecutionStatus.FAILED,
        timestamp=graph.run.ended_at,
    )
    assert failed.execution_status == EpisodeExecutionStatus.FAILED
    assert failed.ended_at == graph.run.ended_at


def test_expected_application_service_delegates_to_frozen_derivation() -> None:
    graph = complete_runtime_graph()
    from skill_eval_framework.validation import derive_expected_applications

    assert expected_applications_for_run(
        graph.benchmark, graph.run, graph.episodes
    ) == derive_expected_applications(graph.benchmark, graph.run, graph.episodes)


def test_missing_final_inventory_requires_sealed_run() -> None:
    graph = complete_runtime_graph()
    active = graph.run.model_copy(
        update={"execution_status": RunExecutionStatus.RUNNING, "ended_at": None}
    )
    with pytest.raises(RuntimeServiceError):
        missing_applications_for_final_inventory(
            graph.benchmark,
            active,
            episodes=graph.episodes,
            grader_results=graph.grader_results,
            metric_results=graph.metric_results,
            gate_results=graph.gate_results,
        )


def test_missing_episode_is_assembled_for_final_inventory() -> None:
    graph = complete_runtime_graph()
    missing = missing_applications_for_final_inventory(
        graph.benchmark,
        graph.run,
        episodes=[],
        grader_results=[],
        metric_results=graph.metric_results,
        gate_results=graph.gate_results,
    )
    assert [item.application_ref.logical_key for item in missing] == [("episode", "TC001", 1)]


def test_unavailable_metric_result_is_actual_not_missing() -> None:
    graph = complete_runtime_graph()
    unavailable = graph.metric_results[0].model_copy(
        update={
            "status": "unavailable",
            "value": None,
            "unavailable_reason": "required_inputs_missing",
            "unavailable_explanation": "Engine reported missing input.",
        }
    )
    missing = missing_applications_for_final_inventory(
        graph.benchmark,
        graph.run,
        episodes=graph.episodes,
        grader_results=graph.grader_results,
        metric_results=[unavailable],
        gate_results=graph.gate_results,
    )
    assert not any(
        item.application_ref.logical_key == ("metric_result", "M001") for item in missing
    )


def test_missing_diagnostic_association_is_preserved_by_inventory_builder() -> None:
    graph = complete_runtime_graph()
    inventory = build_final_inventory(
        graph.benchmark,
        graph.run,
        episodes=graph.episodes,
        grader_results=graph.grader_results,
        metric_results=[],
        gate_results=[],
        diagnostic_ids_by_application={("metric_result", "M001"): ["D-METRIC"]},
    )
    record = next(
        item
        for item in inventory.missing_applications
        if item.application_ref.logical_key == ("metric_result", "M001")
    )
    assert record.diagnostic_ids == ["D-METRIC"]


def test_missing_grader_result_is_assembled() -> None:
    graph = complete_runtime_graph()
    missing = missing_applications_for_final_inventory(
        graph.benchmark,
        graph.run,
        episodes=graph.episodes,
        grader_results=[],
        metric_results=[],
        gate_results=[],
    )
    assert ("grader_result", "E001", "G001", "TC001", "C001") in {
        item.application_ref.logical_key for item in missing
    }


def test_missing_gate_result_is_assembled() -> None:
    graph = complete_runtime_graph()
    missing = missing_applications_for_final_inventory(
        graph.benchmark,
        graph.run,
        episodes=graph.episodes,
        grader_results=graph.grader_results,
        metric_results=graph.metric_results,
        gate_results=[],
    )
    assert ("gate_result", "GATE001") in {item.application_ref.logical_key for item in missing}


def test_missing_records_are_stably_ordered() -> None:
    graph = complete_runtime_graph()
    first = build_final_inventory(
        graph.benchmark,
        graph.run,
        episodes=[],
        grader_results=[],
        metric_results=[],
        gate_results=[],
    )
    second = build_final_inventory(
        graph.benchmark,
        graph.run,
        episodes=[],
        grader_results=[],
        metric_results=[],
        gate_results=[],
    )
    assert first.missing_applications == second.missing_applications


def test_interim_inventory_does_not_mark_missing() -> None:
    graph = complete_runtime_graph()
    inventory = build_interim_inventory(
        graph.benchmark,
        graph.run,
        episodes=[],
        grader_results=[],
        metric_results=[],
        gate_results=[],
    )
    assert inventory.missing_applications == []


def test_final_inventory_closes_admitted_slot_as_missing() -> None:
    graph = complete_runtime_graph()
    inventory = build_final_inventory(
        graph.benchmark,
        graph.run,
        episodes=[],
        grader_results=[],
        metric_results=[],
        gate_results=[],
    )
    keys = {item.application_ref.logical_key for item in inventory.missing_applications}
    assert ("episode", "TC001", 1) in keys


def test_scorecard_inventory_actual_ids_are_stably_sorted() -> None:
    graph = complete_runtime_graph()
    shuffled = build_scorecard_inventory(
        graph.benchmark,
        graph.run,
        episodes=list(reversed(graph.episodes)),
        grader_results=list(reversed(graph.grader_results)),
        metric_results=list(reversed(graph.metric_results)),
        gate_results=list(reversed(graph.gate_results)),
    )
    normal = build_scorecard_inventory(
        graph.benchmark,
        graph.run,
        episodes=graph.episodes,
        grader_results=graph.grader_results,
        metric_results=graph.metric_results,
        gate_results=graph.gate_results,
    )
    assert shuffled == normal


def test_create_interim_scorecard_organizes_without_creating_results() -> None:
    graph = complete_runtime_graph()
    scorecard = create_interim_scorecard(
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
    assert scorecard.finalization_status.value == "interim"
    assert scorecard.result_inventory.metric_result_ids == ["MR001"]


def test_finalize_scorecard_accepts_caller_provided_views() -> None:
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
    assert finalized.finalization_status.value == "finalized_audit"


def test_finalize_scorecard_rejects_invalid_graph() -> None:
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
    graph.evidence[0] = graph.evidence[0].model_copy(update={"episode_id": "E999"})
    with pytest.raises(IntegrityFinalizationError):
        finalize_scorecard(
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


def test_final_integrity_sound_graph_becomes_valid() -> None:
    graph = complete_runtime_graph()
    pending = graph.run.model_copy(
        update={"validity_status": RunValidityStatus.PENDING, "validity_findings": []}
    )
    finalized = finalize_run_validity(
        graph.benchmark,
        pending,
        episodes=graph.episodes,
        artifacts=graph.artifacts,
        evidence=graph.evidence,
        grader_results=graph.grader_results,
        metric_results=graph.metric_results,
        gate_results=graph.gate_results,
        diagnostics=graph.diagnostics,
        scorecard=graph.scorecard,
    )
    assert finalized.validity_status == RunValidityStatus.VALID
    assert finalized.validity_findings == []


def test_final_integrity_cross_run_contamination_becomes_invalid() -> None:
    graph = complete_runtime_graph()
    pending = graph.run.model_copy(
        update={"validity_status": RunValidityStatus.PENDING, "validity_findings": []}
    )
    graph.artifacts[0] = graph.artifacts[0].model_copy(update={"run_id": "OTHER"})
    finalized = finalize_run_validity(
        graph.benchmark,
        pending,
        episodes=graph.episodes,
        artifacts=graph.artifacts,
        evidence=graph.evidence,
        grader_results=graph.grader_results,
        metric_results=graph.metric_results,
        gate_results=graph.gate_results,
        diagnostics=graph.diagnostics,
        scorecard=graph.scorecard,
    )
    assert finalized.validity_status == RunValidityStatus.INVALID
    assert any(item.stage == ValidityStage.FINAL_INTEGRITY for item in finalized.validity_findings)


def test_final_integrity_missing_metric_with_inventory_account_can_remain_valid() -> None:
    graph = complete_runtime_graph()
    pending = graph.run.model_copy(
        update={"validity_status": RunValidityStatus.PENDING, "validity_findings": []}
    )
    inventory = build_final_inventory(
        graph.benchmark,
        pending,
        episodes=graph.episodes,
        grader_results=graph.grader_results,
        metric_results=[],
        gate_results=[],
    )
    scorecard = graph.scorecard.model_copy(update={"result_inventory": inventory})
    finalized = finalize_run_validity(
        graph.benchmark,
        pending,
        episodes=graph.episodes,
        artifacts=graph.artifacts,
        evidence=graph.evidence,
        grader_results=graph.grader_results,
        metric_results=[],
        gate_results=[],
        diagnostics=graph.diagnostics,
        scorecard=scorecard,
    )
    assert finalized.validity_status == RunValidityStatus.VALID


def test_final_integrity_cannot_refinalize_valid_run() -> None:
    graph = complete_runtime_graph()
    with pytest.raises(IntegrityFinalizationError):
        finalize_run_validity(
            graph.benchmark,
            graph.run,
            episodes=graph.episodes,
            artifacts=graph.artifacts,
            evidence=graph.evidence,
            grader_results=graph.grader_results,
            metric_results=graph.metric_results,
            gate_results=graph.gate_results,
            diagnostics=graph.diagnostics,
            scorecard=graph.scorecard,
        )


def test_final_integrity_requires_terminal_execution() -> None:
    graph = complete_runtime_graph()
    active = graph.run.model_copy(
        update={
            "execution_status": RunExecutionStatus.RUNNING,
            "validity_status": RunValidityStatus.PENDING,
            "ended_at": None,
        }
    )
    with pytest.raises(IntegrityFinalizationError):
        finalize_run_validity(
            graph.benchmark,
            active,
            episodes=graph.episodes,
            artifacts=graph.artifacts,
            evidence=graph.evidence,
            grader_results=graph.grader_results,
            metric_results=graph.metric_results,
            gate_results=graph.gate_results,
            diagnostics=graph.diagnostics,
            scorecard=graph.scorecard,
        )


def test_invalid_terminal_run_cannot_become_valid() -> None:
    graph = complete_runtime_graph()
    invalid = graph.run.model_copy(
        update={
            "validity_status": RunValidityStatus.INVALID,
            "validity_findings": [
                ValidityFinding(
                    code="TEST_INVALID",
                    stage=ValidityStage.FINAL_INTEGRITY,
                    message="Already invalid.",
                    related_object_refs=[],
                )
            ],
        }
    )
    with pytest.raises(IntegrityFinalizationError):
        finalize_run_validity(
            graph.benchmark,
            invalid,
            episodes=graph.episodes,
            artifacts=graph.artifacts,
            evidence=graph.evidence,
            grader_results=graph.grader_results,
            metric_results=graph.metric_results,
            gate_results=graph.gate_results,
            diagnostics=graph.diagnostics,
            scorecard=graph.scorecard,
        )


def test_runtime_diagnostic_factory_is_explicit_and_typed() -> None:
    diagnostic = make_runtime_diagnostic(
        diagnostic_id="D001",
        run_id="RUN001",
        phase=DiagnosticPhase.ORCHESTRATION,
        code="RETRYABLE_FAILURE",
        message="The orchestrator failed.",
        occurred_at=complete_runtime_graph().run.created_at,
        related_object_refs=[ObjectRef(object_type=ObjectType.RUN, object_ref="RUN001")],
        retryable=True,
    )
    assert diagnostic.diagnostic_id == "D001"
    assert diagnostic.related_object_refs[0].object_ref == "RUN001"
    assert diagnostic.retryable is True


def test_service_outputs_do_not_fabricate_semantic_results() -> None:
    graph = complete_runtime_graph()
    run = graph.run.model_copy(
        update={"execution_status": RunExecutionStatus.RUNNING, "ended_at": None}
    )
    episode = create_episode_for_slot(
        run,
        [],
        episode_id="E002",
        test_case_id="TC001",
        attempt_index=1,
        created_at=graph.run.created_at,
    )
    inventory = build_interim_inventory(
        graph.benchmark,
        run,
        episodes=[episode],
        grader_results=[],
        metric_results=[],
        gate_results=[],
    )
    assert episode.__class__.__name__ == "Episode"
    assert inventory.grader_result_ids == []
    assert inventory.metric_result_ids == []
    assert inventory.gate_result_ids == []


def test_service_does_not_mutate_run_or_collections() -> None:
    graph = complete_runtime_graph()
    before_run = deepcopy(graph.run.model_dump())
    before_episodes = deepcopy([item.model_dump() for item in graph.episodes])
    _ = build_scorecard_inventory(
        graph.benchmark,
        graph.run,
        episodes=list(reversed(graph.episodes)),
        grader_results=list(reversed(graph.grader_results)),
        metric_results=list(reversed(graph.metric_results)),
        gate_results=list(reversed(graph.gate_results)),
    )
    assert graph.run.model_dump() == before_run
    assert [item.model_dump() for item in graph.episodes] == before_episodes


def test_final_inventory_does_not_turn_missing_metric_into_unavailable_result() -> None:
    graph = complete_runtime_graph()
    inventory = build_final_inventory(
        graph.benchmark,
        graph.run,
        episodes=graph.episodes,
        grader_results=graph.grader_results,
        metric_results=[],
        gate_results=[],
    )
    assert inventory.metric_result_ids == []
    assert any(
        item.application_ref.logical_key == ("metric_result", "M001")
        for item in inventory.missing_applications
    )


def test_final_inventory_does_not_turn_missing_gate_into_indeterminate_result() -> None:
    graph = complete_runtime_graph()
    inventory = build_final_inventory(
        graph.benchmark,
        graph.run,
        episodes=graph.episodes,
        grader_results=graph.grader_results,
        metric_results=graph.metric_results,
        gate_results=[],
    )
    assert inventory.gate_result_ids == []
    assert any(
        item.application_ref.logical_key == ("gate_result", "GATE001")
        for item in inventory.missing_applications
    )
