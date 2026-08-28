"""Scorecard inventory assembly without semantic Result calculation."""

from __future__ import annotations

from collections.abc import Callable, Hashable, Mapping, Sequence
from datetime import datetime

from skill_eval_framework.schemas.definition import BenchmarkDefinition
from skill_eval_framework.schemas.results import (
    AcceptanceEvaluation,
    GateResult,
    GraderResult,
    MetricResult,
    OverallScoreOutcome,
    Scorecard,
    ScorecardFinalizationStatus,
    ScorecardResultInventory,
)
from skill_eval_framework.schemas.runtime import (
    Artifact,
    Episode,
    Evidence,
    Run,
    RuntimeDiagnostic,
)
from skill_eval_framework.validation import (
    derive_expected_applications,
    derive_missing_applications,
)

from .errors import IntegrityFinalizationError, InvalidTransitionError, RuntimeServiceError
from .planning import is_execution_plan_sealed


def build_scorecard_inventory(
    benchmark: BenchmarkDefinition,
    run: Run,
    *,
    episodes: Sequence[Episode],
    grader_results: Sequence[GraderResult],
    metric_results: Sequence[MetricResult],
    gate_results: Sequence[GateResult],
    diagnostics: Sequence[RuntimeDiagnostic] = (),
    final: bool = False,
    diagnostic_ids_by_application: Mapping[tuple[Hashable, ...], Sequence[str]] | None = None,
) -> ScorecardResultInventory:
    """Build deterministic actual/missing inventory, never calculating semantic Results."""

    if final and not is_execution_plan_sealed(run):
        raise RuntimeServiceError("final inventory requires a terminal Run")
    del diagnostics
    inventory = ScorecardResultInventory(
        episode_ids=_sorted_unique_ids(
            episodes,
            key=lambda item: (str(item.test_case_id), item.attempt_index, item.episode_id),
            value=lambda item: item.episode_id,
        ),
        grader_result_ids=_sorted_unique_ids(
            grader_results,
            key=lambda item: (
                str(item.episode_id),
                str(item.test_case_id),
                str(item.contract_id),
                str(item.grader_id),
                item.grader_result_id,
            ),
            value=lambda item: item.grader_result_id,
        ),
        metric_result_ids=_sorted_unique_ids(
            metric_results,
            key=lambda item: (str(item.metric_id), item.metric_result_id),
            value=lambda item: item.metric_result_id,
        ),
        gate_result_ids=_sorted_unique_ids(
            gate_results,
            key=lambda item: (str(item.gate_id), item.gate_result_id),
            value=lambda item: item.gate_result_id,
        ),
        missing_applications=[],
    )
    if not final:
        return inventory
    expected = derive_expected_applications(benchmark, run, episodes)
    missing = derive_missing_applications(
        expected,
        episodes,
        grader_results,
        metric_results,
        gate_results,
    )
    mapping = diagnostic_ids_by_application or {}
    return inventory.model_copy(
        update={
            "missing_applications": [
                record.model_copy(
                    update={
                        "diagnostic_ids": sorted(
                            set(mapping.get(record.application_ref.logical_key, ()))
                        )
                    }
                )
                for record in missing
            ]
        }
    )


def build_interim_inventory(
    benchmark: BenchmarkDefinition,
    run: Run,
    *,
    episodes: Sequence[Episode],
    grader_results: Sequence[GraderResult],
    metric_results: Sequence[MetricResult],
    gate_results: Sequence[GateResult],
    diagnostics: Sequence[RuntimeDiagnostic] = (),
) -> ScorecardResultInventory:
    """Build current actual inventory without marking future absence as missing."""

    return build_scorecard_inventory(
        benchmark,
        run,
        episodes=episodes,
        grader_results=grader_results,
        metric_results=metric_results,
        gate_results=gate_results,
        diagnostics=diagnostics,
        final=False,
    )


def build_final_inventory(
    benchmark: BenchmarkDefinition,
    run: Run,
    *,
    episodes: Sequence[Episode],
    grader_results: Sequence[GraderResult],
    metric_results: Sequence[MetricResult],
    gate_results: Sequence[GateResult],
    diagnostics: Sequence[RuntimeDiagnostic] = (),
    diagnostic_ids_by_application: Mapping[tuple[Hashable, ...], Sequence[str]] | None = None,
) -> ScorecardResultInventory:
    """Build sealed final inventory with typed missing application records."""

    return build_scorecard_inventory(
        benchmark,
        run,
        episodes=episodes,
        grader_results=grader_results,
        metric_results=metric_results,
        gate_results=gate_results,
        diagnostics=diagnostics,
        final=True,
        diagnostic_ids_by_application=diagnostic_ids_by_application,
    )


def create_interim_scorecard(
    *,
    scorecard_id: str,
    benchmark: BenchmarkDefinition,
    run: Run,
    episodes: Sequence[Episode],
    grader_results: Sequence[GraderResult],
    metric_results: Sequence[MetricResult],
    gate_results: Sequence[GateResult],
    diagnostics: Sequence[RuntimeDiagnostic] = (),
    overall_score_outcome: OverallScoreOutcome,
    acceptance_evaluation: AcceptanceEvaluation,
) -> Scorecard:
    """Organize caller-provided views into an interim Scorecard."""

    return Scorecard(
        scorecard_id=scorecard_id,
        run_id=run.run_id,
        definition_ref=run.definition_ref,
        subject_ref=run.subject_ref,
        result_inventory=build_interim_inventory(
            benchmark,
            run,
            episodes=episodes,
            grader_results=grader_results,
            metric_results=metric_results,
            gate_results=gate_results,
            diagnostics=diagnostics,
        ),
        diagnostic_ids=[],
        overall_score_outcome=overall_score_outcome,
        acceptance_evaluation=acceptance_evaluation,
        finalization_status="interim",
        finalized_at=None,
    )


def finalize_scorecard(
    *,
    scorecard: Scorecard,
    benchmark: BenchmarkDefinition,
    run: Run,
    episodes: Sequence[Episode],
    artifacts: Sequence[Artifact],
    evidence: Sequence[Evidence],
    grader_results: Sequence[GraderResult],
    metric_results: Sequence[MetricResult],
    gate_results: Sequence[GateResult],
    diagnostics: Sequence[RuntimeDiagnostic],
    overall_score_outcome: OverallScoreOutcome,
    acceptance_evaluation: AcceptanceEvaluation,
    finalization_status: str,
    finalized_at: datetime,
    diagnostic_ids_by_application: Mapping[tuple[Hashable, ...], Sequence[str]] | None = None,
) -> Scorecard:
    """Finalize an audit/evaluation Scorecard from already-produced view objects."""

    if (
        ScorecardFinalizationStatus(scorecard.finalization_status)
        != ScorecardFinalizationStatus.INTERIM
    ):
        raise InvalidTransitionError("only an interim Scorecard can be finalized")
    if finalization_status == "interim":
        raise InvalidTransitionError(
            "finalization must choose finalized_audit or finalized_evaluation"
        )
    inventory = build_final_inventory(
        benchmark,
        run,
        episodes=episodes,
        grader_results=grader_results,
        metric_results=metric_results,
        gate_results=gate_results,
        diagnostics=diagnostics,
        diagnostic_ids_by_application=diagnostic_ids_by_application,
    )
    candidate = scorecard.model_copy(
        update={
            "run_id": run.run_id,
            "definition_ref": run.definition_ref,
            "subject_ref": run.subject_ref,
            "result_inventory": inventory,
            "overall_score_outcome": overall_score_outcome,
            "acceptance_evaluation": acceptance_evaluation,
            "finalization_status": ScorecardFinalizationStatus(finalization_status),
            "finalized_at": finalized_at,
        }
    )
    from skill_eval_framework.validation import validate_run_graph

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
        candidate,
    )
    if report.issues:
        raise IntegrityFinalizationError(
            "Scorecard finalization failed cross-object integrity validation: "
            + ", ".join(issue.code for issue in report.issues)
        )
    return candidate


def _sorted_unique_ids[T](
    items: Sequence[T],
    *,
    key: Callable[[T], tuple[object, ...]],
    value: Callable[[T], str],
) -> list[str]:
    ordered = sorted(items, key=key)
    ids = [str(value(item)) for item in ordered]
    if len(ids) != len(set(ids)):
        raise RuntimeServiceError("inventory cannot contain duplicate object IDs")
    return ids


__all__ = [
    "build_final_inventory",
    "build_interim_inventory",
    "build_scorecard_inventory",
    "create_interim_scorecard",
    "finalize_scorecard",
]
