"""Deterministic Metric evaluation for executable Definition v0.3 policies."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
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


@dataclass(frozen=True, slots=True)
class _EligibleContribution:
    input_key: tuple[str, str]
    unit_key: str
    attempt: AttemptResult
    value: Decimal


@dataclass(frozen=True, slots=True)
class _TraceRecord:
    input_key: tuple[str, str]
    unit_key: str
    attempt_index: int
    grader_result_id: str
    disposition: MetricInputDisposition
    reason: str
    contribution_value: Decimal | None

    def to_schema(self) -> MetricInputTrace:
        return MetricInputTrace(
            grader_result_id=self.grader_result_id,
            disposition=self.disposition,
            reason=self.reason,
            aggregation_unit_key=self.unit_key,
            contribution_value=self.contribution_value,
        )


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
    input_keys = sorted((item.test_case_id, item.contract_id) for item in specification.inputs)
    eligible_by_unit: dict[str, list[_EligibleContribution]] = defaultdict(list)
    trace_records: list[_TraceRecord] = []
    missing_inputs: list[MissingMetricInput] = []
    selected_count = 0
    distinct_count = 0
    available_raw_count = 0
    eligible_count = 0
    not_exercised_count = 0
    insufficient_count = 0
    unavailable_input_count = 0

    for input_key in input_keys:
        candidates = tuple(
            sorted(candidates_by_input.get(input_key, ()), key=lambda item: item.attempt_index)
        )
        distinct_count += len(candidates)
        available_raw_count += len(candidates)
        try:
            selected = select_attempt_results(candidates, policy.selection)
        except AttemptSelectionError as exc:
            raise MetricEvaluationError(str(exc)) from exc
        selected_count += len(selected)
        if not candidates:
            unavailable_input_count += 1
            missing_inputs.append(
                MissingMetricInput(
                    test_case_id=input_key[0],
                    contract_id=input_key[1],
                    reason="No same-Run GraderResult was available for this Metric input.",
                )
            )
        selected_attempt_indexes = {item.attempt_index for item in selected}
        unit_key = _unit_key(policy.aggregation_unit, *input_key)
        for candidate in candidates:
            result = candidate.result
            if candidate.attempt_index not in selected_attempt_indexes:
                trace_records.append(
                    _TraceRecord(
                        input_key=input_key,
                        unit_key=unit_key,
                        attempt_index=candidate.attempt_index,
                        grader_result_id=result.grader_result_id,
                        disposition=MetricInputDisposition.EXCLUDED,
                        reason=(f"Excluded by {policy.selection.mode.value} attempt selection."),
                        contribution_value=None,
                    )
                )
                continue
            semantic = ResultSemantic(result.judgment)
            contribution = mapping.get(semantic)
            if contribution is None:
                if semantic == ResultSemantic.NOT_EXERCISED:
                    not_exercised_count += 1
                elif semantic == ResultSemantic.INSUFFICIENT_EVIDENCE:
                    insufficient_count += 1
                trace_records.append(
                    _TraceRecord(
                        input_key=input_key,
                        unit_key=unit_key,
                        attempt_index=candidate.attempt_index,
                        grader_result_id=result.grader_result_id,
                        disposition=MetricInputDisposition.EXCLUDED,
                        reason=f"Judgment {semantic.value} is not eligible under the policy.",
                        contribution_value=None,
                    )
                )
            else:
                eligible_count += 1
                eligible_by_unit[unit_key].append(
                    _EligibleContribution(
                        input_key=input_key,
                        unit_key=unit_key,
                        attempt=candidate,
                        value=contribution,
                    )
                )

    for input_key, candidates in candidates_by_input.items():
        grader_ids = {item.result.grader_id for item in candidates}
        if len(grader_ids) > 1:
            raise MetricEvaluationError(
                f"Metric input {input_key!r} resolves to multiple Grader authorities"
            )

    expected_units = {
        _unit_key(policy.aggregation_unit, test_case_id, contract_id)
        for test_case_id, contract_id in input_keys
    }
    reduced: dict[str, Decimal] = {}
    for unit_key in sorted(expected_units):
        contributions = sorted(
            eligible_by_unit.get(unit_key, []),
            key=lambda item: (
                item.input_key[0],
                item.input_key[1],
                item.attempt.attempt_index,
            ),
        )
        if not contributions:
            continue
        if policy.unit_reduction.mode == UnitReductionMode.SINGLE:
            if len(contributions) > 1:
                raise MetricEvaluationError(
                    f"single reduction requires one eligible contribution for unit {unit_key!r}"
                )
            included_ids = {contributions[0].attempt.result.grader_result_id}
            reduced[unit_key] = contributions[0].value
        elif policy.unit_reduction.mode == UnitReductionMode.MEAN:
            included_ids = {
                contribution.attempt.result.grader_result_id for contribution in contributions
            }
            reduced[unit_key] = sum(
                (contribution.value for contribution in contributions), Decimal("0")
            ) / len(contributions)
        else:
            if len({contribution.input_key for contribution in contributions}) > 1:
                raise MetricEvaluationError(
                    "final_eligible cannot merge multiple MetricInputs into one aggregation unit"
                )
            included_ids = {contributions[-1].attempt.result.grader_result_id}
            reduced[unit_key] = contributions[-1].value

        for unit_contribution in contributions:
            grader_result_id = unit_contribution.attempt.result.grader_result_id
            is_included = grader_result_id in included_ids
            if is_included:
                reason = (
                    "Included as the final eligible contribution by unit reduction."
                    if policy.unit_reduction.mode == UnitReductionMode.FINAL_ELIGIBLE
                    else f"Included by {policy.unit_reduction.mode.value} unit reduction."
                )
            else:
                reason = (
                    "Excluded by final_eligible unit reduction because a later eligible "
                    "contribution exists."
                )
            trace_records.append(
                _TraceRecord(
                    input_key=unit_contribution.input_key,
                    unit_key=unit_contribution.unit_key,
                    attempt_index=unit_contribution.attempt.attempt_index,
                    grader_result_id=grader_result_id,
                    disposition=(
                        MetricInputDisposition.INCLUDED
                        if is_included
                        else MetricInputDisposition.EXCLUDED
                    ),
                    reason=reason,
                    contribution_value=unit_contribution.value,
                )
            )

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

    ordered_traces = [
        record.to_schema()
        for record in sorted(
            trace_records,
            key=lambda item: (
                item.unit_key,
                item.input_key[0],
                item.input_key[1],
                item.attempt_index,
            ),
        )
    ]
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
