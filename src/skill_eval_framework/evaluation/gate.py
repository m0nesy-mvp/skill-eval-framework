"""Deterministic Gate evaluation for executable Definition v0.3 conditions."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from skill_eval_framework.schemas.common import ResultSemantic
from skill_eval_framework.schemas.definition import (
    MetricAvailabilityGateCondition,
    MetricThresholdGateCondition,
)
from skill_eval_framework.schemas.definition_v03 import (
    GateSpecificationV03,
    GraderResultGateConditionV03,
)
from skill_eval_framework.schemas.results import (
    GateEvaluationPath,
    GateGraderContribution,
    GateInputSummary,
    GateResult,
    GateSemantic,
    GateTriggerSource,
    GraderResult,
    MetricResult,
    MetricResultStatus,
)
from skill_eval_framework.schemas.runtime import Episode, EvidenceTargetRef

from .errors import GateEvaluationError
from .selection import AttemptResult, AttemptSelectionError, select_attempt_results


def _metric_map(run_id: str, results: Sequence[MetricResult]) -> dict[str, MetricResult]:
    output: dict[str, MetricResult] = {}
    for result in results:
        if result.run_id != run_id:
            raise GateEvaluationError("Gate inputs must belong to the current Run")
        if result.metric_id in output:
            raise GateEvaluationError(f"duplicate MetricResult for metric {result.metric_id!r}")
        output[result.metric_id] = result
    return output


def _episode_map(run_id: str, episodes: Sequence[Episode]) -> dict[str, Episode]:
    output: dict[str, Episode] = {}
    for episode in episodes:
        if episode.run_id != run_id:
            raise GateEvaluationError("Gate inputs must belong to the current Run")
        if episode.episode_id in output:
            raise GateEvaluationError(f"duplicate Episode {episode.episode_id!r}")
        output[episode.episode_id] = episode
    return output


def _direct_candidates(
    condition: GraderResultGateConditionV03,
    run_id: str,
    grader_results: Sequence[GraderResult],
    episodes: Sequence[Episode],
) -> dict[tuple[str, str], tuple[AttemptResult, ...]]:
    episode_by_id = _episode_map(run_id, episodes)
    targets = {(item.test_case_id, item.contract_id) for item in condition.targets}
    output: dict[tuple[str, str], list[AttemptResult]] = {target: [] for target in targets}
    for result in grader_results:
        if result.run_id != run_id:
            raise GateEvaluationError("Gate inputs must belong to the current Run")
        key = (result.test_case_id, result.contract_id)
        if key not in targets:
            continue
        episode = episode_by_id.get(result.episode_id)
        if episode is None or episode.test_case_id != result.test_case_id:
            raise GateEvaluationError(
                f"GraderResult {result.grader_result_id!r} does not resolve to its Episode"
            )
        output[key].append(AttemptResult(episode.attempt_index, result))
    return {key: tuple(values) for key, values in output.items()}


def _finish_gate(
    *,
    specification: GateSpecificationV03,
    run_id: str,
    gate_result_id: str,
    created_at: datetime,
    summary: GateInputSummary,
    condition_outcome: str,
    explanation: str,
) -> GateResult:
    if condition_outcome == "true":
        path = GateEvaluationPath.CONDITION_TRUE
        result = GateSemantic.TRIGGERED
        trigger_source = GateTriggerSource.CONDITION
    elif condition_outcome == "false":
        path = GateEvaluationPath.CONDITION_FALSE
        result = GateSemantic.OPEN
        trigger_source = None
    elif specification.unavailable_handling == "indeterminate":
        path = GateEvaluationPath.UNKNOWN_INDETERMINATE
        result = GateSemantic.INDETERMINATE
        trigger_source = None
    else:
        path = GateEvaluationPath.UNKNOWN_TRIGGERED
        result = GateSemantic.TRIGGERED
        trigger_source = GateTriggerSource.UNAVAILABLE_HANDLING
    return GateResult(
        gate_result_id=gate_result_id,
        run_id=run_id,
        gate_id=specification.gate_id,
        result=result,
        evaluation_path=path,
        trigger_source=trigger_source,
        input_summary=summary.model_copy(update={"condition_outcome": condition_outcome}),
        explanation=explanation,
        created_at=created_at,
    )


def _compare(actual: Decimal, threshold: Decimal, comparator: str) -> bool:
    comparisons = {
        "lt": actual < threshold,
        "lte": actual <= threshold,
        "gt": actual > threshold,
        "gte": actual >= threshold,
        "eq": actual == threshold,
        "neq": actual != threshold,
    }
    try:
        return comparisons[comparator]
    except KeyError as exc:  # pragma: no cover - schema closes this vocabulary
        raise GateEvaluationError(f"unsupported comparator: {comparator!r}") from exc


def _evaluate_direct_grader_gate(
    specification: GateSpecificationV03,
    condition: GraderResultGateConditionV03,
    *,
    run_id: str,
    gate_result_id: str,
    created_at: datetime,
    grader_results: Sequence[GraderResult],
    episodes: Sequence[Episode],
) -> GateResult:
    candidates_by_target = _direct_candidates(condition, run_id, grader_results, episodes)
    for target_key, candidates in candidates_by_target.items():
        grader_ids = {item.result.grader_id for item in candidates}
        if len(grader_ids) > 1:
            raise GateEvaluationError(
                f"Gate target {target_key!r} resolves to multiple Grader authorities"
            )
    trigger = set(condition.trigger_result_semantics)
    contributions: list[GateGraderContribution] = []
    classifications: list[str] = []
    for target in sorted(condition.targets, key=lambda item: (item.test_case_id, item.contract_id)):
        key = (target.test_case_id, target.contract_id)
        candidates = candidates_by_target[key]
        try:
            selected = select_attempt_results(candidates, condition.selection)
        except AttemptSelectionError as exc:
            raise GateEvaluationError(str(exc)) from exc
        if not selected:
            classifications.append("UNKNOWN")
            contributions.append(
                GateGraderContribution(
                    grader_result_id=None,
                    target=EvidenceTargetRef(
                        test_case_id=target.test_case_id,
                        contract_id=target.contract_id,
                    ),
                    contribution="UNKNOWN",
                    detail="No same-Run GraderResult was available for this target.",
                )
            )
            continue
        for selected_item in selected:
            result = selected_item.result
            classification = "MATCH" if ResultSemantic(result.judgment) in trigger else "NON_MATCH"
            classifications.append(classification)
            detail_word = {"MATCH": "match", "NON_MATCH": "non-match"}[classification]
            contributions.append(
                GateGraderContribution(
                    grader_result_id=result.grader_result_id,
                    target=EvidenceTargetRef(
                        test_case_id=target.test_case_id,
                        contract_id=target.contract_id,
                    ),
                    contribution=classification,
                    detail=(f"Judgment {result.judgment.value} is {detail_word} for this Gate."),
                )
            )
    outcome = evaluate_three_valued_quantifier(classifications, condition.quantifier)
    summary = GateInputSummary(
        condition_type="grader_result",
        grader_contributions=contributions,
        metric_result_id=None,
        metric_input_state="not_applicable",
        observed_canonical_value=None,
        comparator_outcome="not_applicable",
        quantifier=condition.quantifier,
        condition_outcome=outcome,
    )
    return _finish_gate(
        specification=specification,
        run_id=run_id,
        gate_result_id=gate_result_id,
        created_at=created_at,
        summary=summary,
        condition_outcome=outcome,
        explanation=(
            f"Direct-Grader Gate quantifier {condition.quantifier} evaluated deterministically."
        ),
    )


def evaluate_gate(
    specification: GateSpecificationV03,
    *,
    run_id: str,
    gate_result_id: str,
    created_at: datetime,
    grader_results: Sequence[GraderResult] = (),
    metric_results: Sequence[MetricResult] = (),
    episodes: Sequence[Episode] = (),
) -> GateResult:
    """Evaluate one typed v0.3 Gate without mutating upstream Results."""

    if not isinstance(specification, GateSpecificationV03):
        raise GateEvaluationError("unsupported executable definition version")
    condition = specification.condition
    if isinstance(condition, GraderResultGateConditionV03):
        return _evaluate_direct_grader_gate(
            specification,
            condition,
            run_id=run_id,
            gate_result_id=gate_result_id,
            created_at=created_at,
            grader_results=grader_results,
            episodes=episodes,
        )
    metrics = _metric_map(run_id, metric_results)
    metric = metrics.get(condition.metric_id)
    if metric is None:
        state = "missing"
        metric_result_id = None
        actual = None
    else:
        metric_result_id = metric.metric_result_id
        if metric.status == MetricResultStatus.AVAILABLE:
            if metric.value is None:
                raise GateEvaluationError("available MetricResult has no canonical value")
            state = "available"
            actual = metric.value.canonical_value
        else:
            state = "unavailable"
            actual = None
    if isinstance(condition, MetricThresholdGateCondition):
        comparator_outcome = (
            "unknown"
            if actual is None
            else (
                "true"
                if _compare(actual, condition.threshold_value, condition.comparator)
                else "false"
            )
        )
        summary = GateInputSummary(
            condition_type="metric_threshold",
            grader_contributions=[],
            metric_result_id=metric_result_id,
            metric_input_state=state,
            observed_canonical_value=actual,
            comparator_outcome=comparator_outcome,
            quantifier="not_applicable",
            condition_outcome=comparator_outcome,
        )
        return _finish_gate(
            specification=specification,
            run_id=run_id,
            gate_result_id=gate_result_id,
            created_at=created_at,
            summary=summary,
            condition_outcome=comparator_outcome,
            explanation=(
                f"Metric {condition.metric_id} canonical value {actual!s} compared with "
                f"{condition.comparator} {condition.threshold_value!s}."
                if actual is not None
                else f"Metric {condition.metric_id} is {state}; threshold condition is unknown."
            ),
        )
    if isinstance(condition, MetricAvailabilityGateCondition):
        outcome = "unknown" if state == "missing" else "true" if state == "unavailable" else "false"
        summary = GateInputSummary(
            condition_type="metric_availability",
            grader_contributions=[],
            metric_result_id=metric_result_id,
            metric_input_state=state,
            observed_canonical_value=None,
            comparator_outcome="not_applicable",
            quantifier="not_applicable",
            condition_outcome=outcome,
        )
        return _finish_gate(
            specification=specification,
            run_id=run_id,
            gate_result_id=gate_result_id,
            created_at=created_at,
            summary=summary,
            condition_outcome=outcome,
            explanation=f"Metric {condition.metric_id} availability state is {state}.",
        )
    raise GateEvaluationError(f"unsupported Gate condition type: {type(condition).__name__}")


def evaluate_three_valued_quantifier(contributions: Sequence[str], quantifier: str) -> str:
    """Evaluate the Frozen ANY/ALL truth table for classified inputs."""

    if not contributions:
        return "unknown"
    if quantifier == "any":
        if "MATCH" in contributions:
            return "true"
        return "unknown" if "UNKNOWN" in contributions else "false"
    if quantifier == "all":
        if "NON_MATCH" in contributions:
            return "false"
        return "unknown" if "UNKNOWN" in contributions else "true"
    raise GateEvaluationError(f"unsupported quantifier: {quantifier!r}")


__all__ = ["evaluate_gate", "evaluate_three_valued_quantifier"]
