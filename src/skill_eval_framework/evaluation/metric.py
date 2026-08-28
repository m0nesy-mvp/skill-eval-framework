"""Deterministic Metric evaluation for executable Definition v0.3 policies."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from skill_eval_framework.schemas.common import ResultSemantic
from skill_eval_framework.schemas.definition_v03 import (
    AggregationUnit,
    MetricSpecificationV03,
    UnitReductionMode,
)
from skill_eval_framework.schemas.results import (
    GraderResult,
    MetricCoverageSummary,
    MetricInputDisposition,
    MetricInputTrace,
    MetricResult,
    MetricResultStatus,
    MetricUnavailableReason,
    MetricValue,
    MissingMetricInput,
)
from skill_eval_framework.schemas.runtime import Episode

from .errors import MetricEvaluationError
from .selection import AttemptResult, AttemptSelectionError, select_attempt_results


def _episode_map(run_id: str, episodes: Sequence[Episode]) -> dict[str, Episode]:
    output: dict[str, Episode] = {}
    for episode in episodes:
        if episode.run_id != run_id:
            raise MetricEvaluationError("Metric inputs must belong to the current Run")
        if episode.episode_id in output:
            raise MetricEvaluationError(f"duplicate Episode {episode.episode_id!r}")
        output[episode.episode_id] = episode
    return output


def _result_candidates(
    specification: MetricSpecificationV03,
    run_id: str,
    grader_results: Sequence[GraderResult],
    episodes: Sequence[Episode],
) -> dict[tuple[str, str], tuple[AttemptResult, ...]]:
    episode_by_id = _episode_map(run_id, episodes)
    input_keys = {(item.test_case_id, item.contract_id) for item in specification.inputs}
    by_input: dict[tuple[str, str], list[AttemptResult]] = defaultdict(list)
    for result in grader_results:
        if result.run_id != run_id:
            raise MetricEvaluationError("Metric inputs must belong to the current Run")
        episode = episode_by_id.get(result.episode_id)
        if episode is None:
            raise MetricEvaluationError(
                f"GraderResult {result.grader_result_id!r} references an unknown Episode"
            )
        if episode.test_case_id != result.test_case_id:
            raise MetricEvaluationError(
                f"GraderResult {result.grader_result_id!r} does not match its Episode"
            )
        key = (result.test_case_id, result.contract_id)
        if key in input_keys:
            by_input[key].append(AttemptResult(attempt_index=episode.attempt_index, result=result))
    return {key: tuple(values) for key, values in by_input.items()}


def _unit_key(unit: AggregationUnit, test_case_id: str, contract_id: str) -> str:
    if unit == AggregationUnit.PER_TARGET:
        return f"{test_case_id}/{contract_id}"
    if unit == AggregationUnit.PER_CONTRACT:
        return contract_id
    return test_case_id


def calculate_metric_result(
    specification: MetricSpecificationV03,
    *,
    run_id: str,
    metric_result_id: str,
    created_at: datetime,
    grader_results: Sequence[GraderResult] = (),
    episodes: Sequence[Episode] = (),
) -> MetricResult:
    """Execute one typed v0.3 Metric policy without mutating inputs."""

    if not isinstance(specification, MetricSpecificationV03):
        raise MetricEvaluationError("unsupported executable definition version")

    candidates_by_input = _result_candidates(specification, run_id, grader_results, episodes)
    policy = specification.execution_policy
    mapping = {rule.source_semantic: rule.numeric_value for rule in policy.contribution_mapping}
    selected_by_input: dict[tuple[str, str], tuple[AttemptResult, ...]] = {}
    traces: list[MetricInputTrace] = []
    missing_inputs: list[MissingMetricInput] = []
    selected_count = 0
    distinct_count = 0
    available_raw_count = 0
    eligible_count = 0
    not_exercised_count = 0
    insufficient_count = 0
    unavailable_input_count = 0

    for metric_input in specification.inputs:
        input_key = (metric_input.test_case_id, metric_input.contract_id)
        candidates = tuple(
            sorted(candidates_by_input.get(input_key, ()), key=lambda item: item.attempt_index)
        )
        distinct_count += len(candidates)
        available_raw_count += len(candidates)
        try:
            selected = select_attempt_results(candidates, policy.selection)
        except AttemptSelectionError as exc:
            raise MetricEvaluationError(str(exc)) from exc
        selected_by_input[input_key] = selected
        selected_count += len(selected)
        if not selected:
            unavailable_input_count += 1
            missing_inputs.append(
                MissingMetricInput(
                    test_case_id=metric_input.test_case_id,
                    contract_id=metric_input.contract_id,
                    reason="No same-Run GraderResult was available for this Metric input.",
                )
            )
        for selected_item in selected:
            result = selected_item.result
            semantic = ResultSemantic(result.judgment)
            contribution = mapping.get(semantic)
            unit_key = _unit_key(policy.aggregation_unit, *input_key)
            if contribution is None:
                if semantic == ResultSemantic.NOT_EXERCISED:
                    not_exercised_count += 1
                elif semantic == ResultSemantic.INSUFFICIENT_EVIDENCE:
                    insufficient_count += 1
                traces.append(
                    MetricInputTrace(
                        grader_result_id=result.grader_result_id,
                        disposition=MetricInputDisposition.EXCLUDED,
                        reason=f"Judgment {semantic.value} is not eligible under the policy.",
                        aggregation_unit_key=unit_key,
                        contribution_value=None,
                    )
                )
            else:
                eligible_count += 1
                traces.append(
                    MetricInputTrace(
                        grader_result_id=result.grader_result_id,
                        disposition=MetricInputDisposition.INCLUDED,
                        reason=f"Judgment {semantic.value} mapped by the typed policy.",
                        aggregation_unit_key=unit_key,
                        contribution_value=contribution,
                    )
                )

    for input_key, candidates in candidates_by_input.items():
        grader_ids = {item.result.grader_id for item in candidates}
        if len(grader_ids) > 1:
            raise MetricEvaluationError(
                f"Metric input {input_key!r} resolves to multiple Grader authorities"
            )

    eligible_by_unit: dict[str, list[tuple[int, Decimal]]] = defaultdict(list)
    for metric_input in specification.inputs:
        input_key = (metric_input.test_case_id, metric_input.contract_id)
        unit_key = _unit_key(policy.aggregation_unit, *input_key)
        selected = selected_by_input[input_key]
        contributions = [
            (item.attempt_index, mapping[ResultSemantic(item.result.judgment)])
            for item in selected
            if ResultSemantic(item.result.judgment) in mapping
        ]
        if policy.unit_reduction.mode == UnitReductionMode.FINAL_ELIGIBLE:
            contributions = contributions[-1:]
        eligible_by_unit[unit_key].extend(contributions)

    expected_units = {
        _unit_key(policy.aggregation_unit, item.test_case_id, item.contract_id)
        for item in specification.inputs
    }
    reduced: dict[str, Decimal] = {}
    for unit_key in sorted(expected_units):
        contributions = eligible_by_unit.get(unit_key, [])
        if not contributions:
            continue
        if policy.unit_reduction.mode == UnitReductionMode.SINGLE:
            if len(contributions) > 1:
                raise MetricEvaluationError(
                    f"single reduction requires one eligible contribution for unit {unit_key!r}"
                )
            reduced[unit_key] = contributions[0][1]
        elif policy.unit_reduction.mode == UnitReductionMode.MEAN:
            reduced[unit_key] = sum((value for _, value in contributions), Decimal("0")) / len(
                contributions
            )
        else:
            if len(contributions) > 1:
                raise MetricEvaluationError(
                    "final_eligible cannot merge multiple MetricInputs into one aggregation unit"
                )
            reduced[unit_key] = contributions[-1][1]

    contributing_units = len(reduced)
    denominator = Decimal(contributing_units)
    coverage_ratio = denominator / Decimal(len(expected_units)) if expected_units else Decimal("0")
    unavailable_reason: MetricUnavailableReason | None = None
    if unavailable_input_count:
        unavailable_reason = MetricUnavailableReason.REQUIRED_INPUTS_MISSING
    elif contributing_units == 0:
        unavailable_reason = MetricUnavailableReason.EMPTY_DENOMINATOR
    elif len(reduced) != len(expected_units):
        unavailable_reason = (
            MetricUnavailableReason.REQUIRED_INPUTS_MISSING
            if unavailable_input_count
            else MetricUnavailableReason.COMPLETENESS_FAILED
        )

    ordered_traces = sorted(
        traces,
        key=lambda item: (
            item.aggregation_unit_key or "",
            item.grader_result_id,
        ),
    )
    coverage = MetricCoverageSummary(
        expected_input_count=len(specification.inputs),
        available_raw_result_count=available_raw_count,
        distinct_result_count=distinct_count,
        selected_result_count=selected_count,
        substantive_eligible_count=eligible_count,
        not_exercised_count=not_exercised_count,
        insufficient_evidence_count=insufficient_count,
        unavailable_input_count=unavailable_input_count,
        declared_aggregation_unit=policy.aggregation_unit.value,
        contributing_unit_count=contributing_units,
        denominator=denominator,
        coverage_ratio=coverage_ratio,
    )
    if unavailable_reason is not None:
        return MetricResult(
            metric_result_id=metric_result_id,
            run_id=run_id,
            metric_id=specification.metric_id,
            status=MetricResultStatus.UNAVAILABLE,
            value=None,
            unavailable_reason=unavailable_reason,
            unavailable_explanation=(
                "Strict completeness could not produce one eligible contribution for every "
                "expected aggregation unit."
            ),
            coverage=coverage,
            input_traces=ordered_traces,
            missing_inputs=missing_inputs,
            created_at=created_at,
        )
    value = sum(reduced.values(), Decimal("0")) / len(reduced)
    return MetricResult(
        metric_result_id=metric_result_id,
        run_id=run_id,
        metric_id=specification.metric_id,
        status=MetricResultStatus.AVAILABLE,
        value=MetricValue(
            value_kind="rate",
            canonical_value=value,
            unit=policy.aggregation_unit.value,
        ),
        unavailable_reason=None,
        unavailable_explanation=None,
        coverage=coverage,
        input_traces=ordered_traces,
        missing_inputs=missing_inputs,
        created_at=created_at,
    )


__all__ = ["calculate_metric_result"]
