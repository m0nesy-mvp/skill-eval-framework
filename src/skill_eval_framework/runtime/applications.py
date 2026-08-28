"""Episode admission and expected-application orchestration."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from skill_eval_framework.schemas.results import (
    ExpectedApplicationRef,
    GateResult,
    GraderResult,
    MetricResult,
    MissingApplicationRecord,
)
from skill_eval_framework.schemas.runtime import (
    Episode,
    EpisodeExecutionStatus,
    Run,
    RunExecutionStatus,
    RunTestCaseDisposition,
    RuntimeDiagnostic,
    RunValidityStatus,
)
from skill_eval_framework.validation import (
    derive_expected_applications,
    derive_missing_applications,
)
from skill_eval_framework.validation.definition import SupportedBenchmarkDefinition

from .errors import ExecutionPlanError, RuntimeServiceError
from .planning import is_execution_plan_sealed


def create_episode_for_slot(
    run: Run,
    episodes: Sequence[Episode],
    *,
    episode_id: str,
    test_case_id: str,
    attempt_index: int,
    created_at: datetime,
) -> Episode:
    """Create an empty, auditable Episode for one admitted scheduled slot."""

    if RunValidityStatus(run.validity_status) == RunValidityStatus.INVALID:
        raise RuntimeServiceError("invalid Run cannot admit a new Episode")
    if is_execution_plan_sealed(run):
        raise ExecutionPlanError("sealed Run cannot create a new Episode")
    if RunExecutionStatus(run.execution_status) not in {
        RunExecutionStatus.CREATED,
        RunExecutionStatus.RUNNING,
    }:
        raise RuntimeServiceError("Episode admission requires an active Run")
    planned = any(
        item.test_case_id == test_case_id
        and item.disposition == RunTestCaseDisposition.SCHEDULED
        and any(slot.attempt_index == attempt_index for slot in item.attempt_slots)
        for item in run.execution_plan.test_cases
    )
    if not planned:
        raise ExecutionPlanError(
            f"no scheduled slot for TestCase {test_case_id!r}, attempt {attempt_index}"
        )
    if any(item.episode_id == episode_id for item in episodes):
        raise ExecutionPlanError(f"Episode ID {episode_id!r} already exists")
    if any(
        item.run_id == run.run_id
        and item.test_case_id == test_case_id
        and item.attempt_index == attempt_index
        for item in episodes
    ):
        raise ExecutionPlanError("Episode logical key already exists")
    return Episode(
        episode_id=episode_id,
        run_id=run.run_id,
        test_case_id=test_case_id,
        attempt_index=attempt_index,
        execution_status=EpisodeExecutionStatus.CREATED,
        created_at=created_at,
        started_at=None,
        ended_at=None,
        trace_events=[],
        artifact_ids=[],
        evidence_ids=[],
        diagnostic_ids=[],
    )


def expected_applications_for_run(
    benchmark: SupportedBenchmarkDefinition,
    run: Run,
    episodes: Sequence[Episode],
) -> tuple[ExpectedApplicationRef, ...]:
    """Expose the frozen validation derivation at the runtime coordination boundary."""

    return derive_expected_applications(benchmark, run, episodes)


def missing_applications_for_final_inventory(
    benchmark: SupportedBenchmarkDefinition,
    run: Run,
    *,
    episodes: Sequence[Episode],
    grader_results: Sequence[GraderResult],
    metric_results: Sequence[MetricResult],
    gate_results: Sequence[GateResult],
    diagnostics: Sequence[RuntimeDiagnostic] = (),
) -> tuple[MissingApplicationRecord, ...]:
    """Derive missing identities only for an explicitly final/sealed context."""

    if not is_execution_plan_sealed(run):
        raise RuntimeServiceError("missing applications require a terminal Run")
    del diagnostics
    expected = expected_applications_for_run(benchmark, run, episodes)
    return derive_missing_applications(
        expected,
        episodes,
        grader_results,
        metric_results,
        gate_results,
    )


__all__ = [
    "create_episode_for_slot",
    "expected_applications_for_run",
    "missing_applications_for_final_inventory",
]
