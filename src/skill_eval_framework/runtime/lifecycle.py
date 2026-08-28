"""Deterministic Run and Episode lifecycle coordination."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from skill_eval_framework.schemas.definition import BenchmarkDefinition
from skill_eval_framework.schemas.results import (
    GateResult,
    GraderResult,
    MetricResult,
    Scorecard,
)
from skill_eval_framework.schemas.runtime import (
    Artifact,
    DiagnosticPhase,
    Episode,
    EpisodeExecutionStatus,
    Evidence,
    FrozenDefinitionRef,
    ObjectRef,
    Run,
    RunExecutionPlan,
    RunExecutionStatus,
    RuntimeDiagnostic,
    RuntimeExecutionContext,
    RunValidityStatus,
    SubjectReference,
    ValidityFinding,
    ValidityStage,
)
from skill_eval_framework.validation import validate_benchmark_definition, validate_run_graph

from .errors import IntegrityFinalizationError, InvalidTransitionError
from .planning import is_execution_plan_sealed


def create_run(
    *,
    run_id: str,
    definition_ref: FrozenDefinitionRef,
    subject_ref: SubjectReference,
    execution_context: RuntimeExecutionContext,
    execution_plan: RunExecutionPlan,
    created_at: datetime,
) -> Run:
    """Create a deterministic initial Run without executing the subject."""

    return Run(
        run_id=run_id,
        definition_ref=definition_ref,
        subject_ref=subject_ref,
        execution_context=execution_context,
        execution_plan=execution_plan,
        execution_status=RunExecutionStatus.CREATED,
        validity_status=RunValidityStatus.PENDING,
        validity_findings=[],
        created_at=created_at,
        started_at=None,
        ended_at=None,
        episode_ids=[],
        diagnostic_ids=[],
    )


def prevalidate_run(
    benchmark: BenchmarkDefinition,
    run: Run,
    *,
    episodes: Sequence[Episode] = (),
    artifacts: Sequence[Artifact] = (),
    evidence: Sequence[Evidence] = (),
    grader_results: Sequence[GraderResult] = (),
    metric_results: Sequence[MetricResult] = (),
    gate_results: Sequence[GateResult] = (),
    diagnostics: Sequence[RuntimeDiagnostic] = (),
    scorecard: Scorecard | None = None,
) -> Run:
    """Run Definition and graph preflight while preserving ``pending`` on success."""

    if RunValidityStatus(run.validity_status) != RunValidityStatus.PENDING:
        raise InvalidTransitionError("preflight is only valid for a pending Run")
    definition_report = validate_benchmark_definition(benchmark)
    graph_report = validate_run_graph(
        benchmark,
        run,
        episodes,
        artifacts,
        evidence,
        grader_results,
        metric_results,
        gate_results,
        diagnostics,
        scorecard,
    )
    issues = (*definition_report.issues, *graph_report.issues)
    if not issues:
        return run.model_copy(
            update={
                "validity_status": RunValidityStatus.PENDING,
                "validity_findings": [],
            }
        )
    findings = [
        ValidityFinding(
            code=issue.code,
            stage=ValidityStage.PRE_EXECUTION,
            message=issue.message,
            related_object_refs=_refs_from_issue(issue.path),
        )
        for issue in sorted(set(issues), key=lambda item: (item.code, item.path, item.message))
    ]
    return run.model_copy(
        update={
            "validity_status": RunValidityStatus.INVALID,
            "validity_findings": findings,
        }
    )


def transition_run_execution(
    run: Run,
    target_status: RunExecutionStatus,
    *,
    timestamp: datetime,
) -> Run:
    """Return a new Run after an explicitly supported execution transition."""

    current = RunExecutionStatus(run.execution_status)
    target = RunExecutionStatus(target_status)
    allowed: dict[RunExecutionStatus, frozenset[RunExecutionStatus]] = {
        RunExecutionStatus.CREATED: frozenset(
            {
                RunExecutionStatus.RUNNING,
                RunExecutionStatus.BLOCKED,
                RunExecutionStatus.FAILED,
                RunExecutionStatus.CANCELLED,
            }
        ),
        RunExecutionStatus.RUNNING: frozenset(
            {
                RunExecutionStatus.COMPLETED,
                RunExecutionStatus.PARTIAL,
                RunExecutionStatus.BLOCKED,
                RunExecutionStatus.FAILED,
                RunExecutionStatus.CANCELLED,
            }
        ),
    }
    if target not in allowed.get(current, frozenset()):
        raise InvalidTransitionError(
            f"Run transition {current.value} -> {target.value} is not allowed"
        )
    updates: dict[str, object] = {"execution_status": target}
    if target == RunExecutionStatus.RUNNING and run.started_at is None:
        updates["started_at"] = timestamp
    if target in {
        RunExecutionStatus.COMPLETED,
        RunExecutionStatus.PARTIAL,
        RunExecutionStatus.BLOCKED,
        RunExecutionStatus.FAILED,
        RunExecutionStatus.CANCELLED,
    }:
        updates["ended_at"] = timestamp
    return run.model_copy(update=updates)


def transition_episode(
    episode: Episode,
    target_status: EpisodeExecutionStatus,
    *,
    timestamp: datetime,
) -> Episode:
    """Return a new Episode on the conservative, Frozen-supported status paths."""

    current = EpisodeExecutionStatus(episode.execution_status)
    target = EpisodeExecutionStatus(target_status)
    allowed: dict[EpisodeExecutionStatus, frozenset[EpisodeExecutionStatus]] = {
        EpisodeExecutionStatus.CREATED: frozenset(
            {
                EpisodeExecutionStatus.RUNNING,
                EpisodeExecutionStatus.BLOCKED,
                EpisodeExecutionStatus.CANCELLED,
            }
        ),
        EpisodeExecutionStatus.RUNNING: frozenset(
            {
                EpisodeExecutionStatus.COMPLETED,
                EpisodeExecutionStatus.BLOCKED,
                EpisodeExecutionStatus.FAILED,
                EpisodeExecutionStatus.CANCELLED,
            }
        ),
    }
    if target not in allowed.get(current, frozenset()):
        raise InvalidTransitionError(
            f"Episode transition {current.value} -> {target.value} is not allowed"
        )
    updates: dict[str, object] = {"execution_status": target}
    if target == EpisodeExecutionStatus.RUNNING and episode.started_at is None:
        updates["started_at"] = timestamp
    if target in {
        EpisodeExecutionStatus.COMPLETED,
        EpisodeExecutionStatus.BLOCKED,
        EpisodeExecutionStatus.FAILED,
        EpisodeExecutionStatus.CANCELLED,
    }:
        updates["ended_at"] = timestamp
    return episode.model_copy(update=updates)


def finalize_run_validity(
    benchmark: BenchmarkDefinition,
    run: Run,
    *,
    episodes: Sequence[Episode],
    artifacts: Sequence[Artifact],
    evidence: Sequence[Evidence],
    grader_results: Sequence[GraderResult],
    metric_results: Sequence[MetricResult],
    gate_results: Sequence[GateResult],
    diagnostics: Sequence[RuntimeDiagnostic],
    scorecard: Scorecard,
) -> Run:
    """Finalize pending validity after terminal execution and inventory closure."""

    if RunValidityStatus(run.validity_status) != RunValidityStatus.PENDING:
        raise IntegrityFinalizationError("Run validity has already been finalized")
    if not is_execution_plan_sealed(run):
        raise IntegrityFinalizationError("final integrity requires a terminal Run")
    validation_scorecard = scorecard.model_copy(update={"finalization_status": "finalized_audit"})
    report = validate_run_graph(
        benchmark,
        run,
        episodes,
        artifacts,
        evidence,
        grader_results,
        metric_results,
        gate_results,
        diagnostics,
        validation_scorecard,
    )
    if report.issues:
        findings = [
            ValidityFinding(
                code=issue.code,
                stage=ValidityStage.FINAL_INTEGRITY,
                message=issue.message,
                related_object_refs=_refs_from_issue(issue.path),
            )
            for issue in report.issues
        ]
        return run.model_copy(
            update={
                "validity_status": RunValidityStatus.INVALID,
                "validity_findings": findings,
            }
        )
    return run.model_copy(
        update={"validity_status": RunValidityStatus.VALID, "validity_findings": []}
    )


def make_runtime_diagnostic(
    *,
    diagnostic_id: str,
    run_id: str,
    phase: DiagnosticPhase,
    code: str,
    message: str,
    occurred_at: datetime,
    episode_id: str | None = None,
    related_object_refs: Sequence[ObjectRef] = (),
    retryable: bool | None = None,
) -> RuntimeDiagnostic:
    """Construct an operational diagnostic without interpreting semantic Results."""

    return RuntimeDiagnostic(
        diagnostic_id=diagnostic_id,
        run_id=run_id,
        episode_id=episode_id,
        phase=phase,
        code=code,
        message=message,
        related_object_refs=list(related_object_refs),
        occurred_at=occurred_at,
        retryable=retryable,
    )


def _refs_from_issue(path: str) -> list[ObjectRef]:
    """Keep finding references conservative when a ValidationIssue has only a path."""

    del path
    return []
