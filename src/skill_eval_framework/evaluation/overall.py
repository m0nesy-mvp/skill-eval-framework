"""Decimal-only Overall Score calculation for structured executable policies."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Literal

from skill_eval_framework.schemas.definition import (
    DisabledOverallScorePolicy,
    IdentityUnitIntervalNormalization,
    LinearBoundedNormalization,
    OverallScorePolicy,
    WeightedNormalizedMeanOverallScorePolicy,
)
from skill_eval_framework.schemas.results import (
    DefinitionPolicyRef,
    MetricResult,
    MetricResultStatus,
    OverallEvaluationStatus,
    OverallMetricContributionTrace,
    OverallScoreOutcome,
    OverallUnavailableReason,
)

from .errors import OverallEvaluationError


def _metric_map(run_id: str, results: Sequence[MetricResult]) -> dict[str, MetricResult]:
    output: dict[str, MetricResult] = {}
    for result in results:
        if result.run_id != run_id:
            raise OverallEvaluationError("Overall inputs must belong to the current Run")
        if result.metric_id in output:
            raise OverallEvaluationError(f"duplicate MetricResult for metric {result.metric_id!r}")
        output[result.metric_id] = result
    return output


def _normalize(value: Decimal, normalization: object) -> Decimal:
    if isinstance(normalization, IdentityUnitIntervalNormalization):
        normalized = value
    elif isinstance(normalization, LinearBoundedNormalization):
        denominator = normalization.source_max - normalization.source_min
        if normalization.direction == "higher_is_better":
            normalized = (value - normalization.source_min) / denominator
        else:
            normalized = (normalization.source_max - value) / denominator
    else:  # pragma: no cover - discriminated Pydantic union
        raise OverallEvaluationError(f"unsupported normalization: {type(normalization).__name__}")
    if not Decimal("0") <= normalized <= Decimal("1"):
        raise OverallEvaluationError(
            "Metric canonical value is outside the declared normalization range"
        )
    return normalized


def _outcome(
    *,
    policy_ref: DefinitionPolicyRef,
    status: OverallEvaluationStatus,
    traces: list[OverallMetricContributionTrace],
    total_weight: Decimal | None,
    available_weight: Decimal | None,
    available_fraction: Decimal | None,
    minimum_fraction: Decimal | None,
    denominator: Decimal | None,
    reason: OverallUnavailableReason | None,
    explanation: str,
    value: Decimal | None = None,
) -> OverallScoreOutcome:
    return OverallScoreOutcome(
        policy_ref=policy_ref,
        evaluation_status=status,
        canonical_value=value,
        contribution_traces=traces,
        total_selected_weight=total_weight,
        available_weight=available_weight,
        available_weight_fraction=available_fraction,
        minimum_required_weight_fraction=minimum_fraction,
        final_included_denominator=denominator,
        unavailable_reason=reason,
        diagnostic_ids=[],
        explanation=explanation,
    )


def calculate_overall_score(
    policy: OverallScorePolicy,
    *,
    run_id: str,
    definition_digest: str,
    metric_results: Sequence[MetricResult] = (),
    run_state: str = "valid",
) -> OverallScoreOutcome:
    """Apply one Frozen Overall policy to same-Run Metric Results."""

    policy_ref = DefinitionPolicyRef(
        definition_digest=definition_digest,
        policy_path="/overall_score_policy",
    )
    if run_state == "pending":
        return _outcome(
            policy_ref=policy_ref,
            status=OverallEvaluationStatus.NOT_PRODUCED_RUN_PENDING,
            traces=[],
            total_weight=None,
            available_weight=None,
            available_fraction=None,
            minimum_fraction=None,
            denominator=None,
            reason=None,
            explanation="Overall is not produced while the Run is pending.",
        )
    if run_state == "invalid":
        return _outcome(
            policy_ref=policy_ref,
            status=OverallEvaluationStatus.NOT_PRODUCED_RUN_INVALID,
            traces=[],
            total_weight=None,
            available_weight=None,
            available_fraction=None,
            minimum_fraction=None,
            denominator=None,
            reason=None,
            explanation="Overall is not produced for an invalid Run.",
        )
    if run_state != "valid":
        raise OverallEvaluationError(f"unsupported Run state: {run_state!r}")
    if isinstance(policy, DisabledOverallScorePolicy):
        return _outcome(
            policy_ref=policy_ref,
            status=OverallEvaluationStatus.DISABLED,
            traces=[],
            total_weight=None,
            available_weight=None,
            available_fraction=None,
            minimum_fraction=None,
            denominator=None,
            reason=None,
            explanation="Overall policy is disabled.",
        )
    if not isinstance(policy, WeightedNormalizedMeanOverallScorePolicy):
        raise OverallEvaluationError(f"unsupported Overall policy: {type(policy).__name__}")

    results = _metric_map(run_id, metric_results)
    contributions = sorted(policy.metric_contributions, key=lambda item: item.metric_id)
    total_weight = sum((item.weight for item in contributions), Decimal("0"))
    included_weight = Decimal("0")
    available_weight = Decimal("0")
    numerator = Decimal("0")
    traces: list[OverallMetricContributionTrace] = []
    blocking_reason: OverallUnavailableReason | None = None
    for contribution in contributions:
        metric = results.get(contribution.metric_id)
        state: Literal["available", "unavailable", "missing"]
        handling: Literal["included", "overall_unavailable", "exclude_and_renormalize"]
        if metric is None:
            state = "missing"
            handling = contribution.missing_result_handling
            metric_result_id = None
            normalized = None
            weighted = None
            exclusion_reason = "Metric Result is missing."
            if handling == "overall_unavailable":
                blocking_reason = (
                    blocking_reason or OverallUnavailableReason.PARTICIPATING_METRIC_MISSING
                )
        elif metric.status == MetricResultStatus.UNAVAILABLE:
            state = "unavailable"
            handling = contribution.unavailable_result_handling
            metric_result_id = metric.metric_result_id
            normalized = None
            weighted = None
            exclusion_reason = "Metric Result is unavailable."
            if handling == "overall_unavailable":
                blocking_reason = (
                    blocking_reason or OverallUnavailableReason.PARTICIPATING_METRIC_UNAVAILABLE
                )
        else:
            if metric.value is None:
                raise OverallEvaluationError("available MetricResult has no canonical value")
            state = "available"
            handling = "included"
            metric_result_id = metric.metric_result_id
            normalized = _normalize(metric.value.canonical_value, contribution.normalization)
            included_weight += contribution.weight
            available_weight += contribution.weight
            weighted = normalized * contribution.weight
            numerator += weighted
            exclusion_reason = None
        traces.append(
            OverallMetricContributionTrace(
                metric_id=contribution.metric_id,
                weight=contribution.weight,
                metric_result_id=metric_result_id,
                application_state=state,
                policy_handling=handling,
                normalized_value=normalized,
                weighted_contribution=weighted,
                exclusion_reason=exclusion_reason,
            )
        )

    available_fraction = available_weight / total_weight
    if blocking_reason is not None:
        return _outcome(
            policy_ref=policy_ref,
            status=OverallEvaluationStatus.UNAVAILABLE,
            traces=traces,
            total_weight=total_weight,
            available_weight=available_weight,
            available_fraction=available_fraction,
            minimum_fraction=policy.minimum_available_weight_fraction,
            denominator=included_weight,
            reason=blocking_reason,
            explanation="A participating Metric is unavailable under the Overall policy.",
        )
    if included_weight == 0:
        return _outcome(
            policy_ref=policy_ref,
            status=OverallEvaluationStatus.UNAVAILABLE,
            traces=traces,
            total_weight=total_weight,
            available_weight=available_weight,
            available_fraction=available_fraction,
            minimum_fraction=policy.minimum_available_weight_fraction,
            denominator=Decimal("0"),
            reason=OverallUnavailableReason.EMPTY_INCLUDED_SET,
            explanation="No available Metric contributed to Overall.",
        )
    if available_fraction < policy.minimum_available_weight_fraction:
        return _outcome(
            policy_ref=policy_ref,
            status=OverallEvaluationStatus.UNAVAILABLE,
            traces=traces,
            total_weight=total_weight,
            available_weight=available_weight,
            available_fraction=available_fraction,
            minimum_fraction=policy.minimum_available_weight_fraction,
            denominator=included_weight,
            reason=OverallUnavailableReason.AVAILABLE_WEIGHT_BELOW_MINIMUM,
            explanation="Available Metric weight is below the policy minimum.",
        )
    quantum = Decimal("1").scaleb(-policy.canonical_precision)
    value = (numerator / included_weight).quantize(quantum, rounding=ROUND_HALF_EVEN)
    return _outcome(
        policy_ref=policy_ref,
        status=OverallEvaluationStatus.AVAILABLE,
        traces=traces,
        total_weight=total_weight,
        available_weight=available_weight,
        available_fraction=available_fraction,
        minimum_fraction=policy.minimum_available_weight_fraction,
        denominator=included_weight,
        reason=None,
        explanation="Weighted normalized mean is available.",
        value=value,
    )


__all__ = ["calculate_overall_score"]
