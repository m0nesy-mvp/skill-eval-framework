"""Object-local tests for the executable Benchmark Definition v0.3 schema."""

from copy import deepcopy
from decimal import Decimal
from typing import Any

import pytest
from conftest import make_definition_data
from pydantic import TypeAdapter, ValidationError

from skill_eval_framework.schemas.common import ResultSemantic
from skill_eval_framework.schemas.definition import BenchmarkDefinition as BenchmarkDefinitionV02
from skill_eval_framework.schemas.definition_v03 import (
    AggregationUnit,
    AttemptSelectionPolicy,
    BenchmarkDefinitionV03,
    GateConditionV03,
    GraderResultGateConditionV03,
    MetricSpecificationV03,
    UnitReductionMode,
)


def metric_v03_data(**policy_overrides: Any) -> dict[str, Any]:
    policy: dict[str, Any] = {
        "selection": {"mode": "all_distinct"},
        "eligibility": {
            "eligible_semantics": ["satisfied", "violated"],
            "non_substantive": "exclude_and_trace",
            "missing_input": "unavailable",
        },
        "contribution_mapping": [
            {
                "source_semantic": "satisfied",
                "numeric_value": "1",
                "contribution_unit": "unit_interval",
                "explanation": "Satisfied contributes one.",
            },
            {
                "source_semantic": "violated",
                "numeric_value": "0",
                "contribution_unit": "unit_interval",
                "explanation": "Violated contributes zero.",
            },
        ],
        "aggregation_unit": "per_target",
        "unit_reduction": {"mode": "mean"},
        "weighting": {"mode": "equal_per_unit"},
        "aggregation": {"mode": "mean"},
        "completeness": {"mode": "strict", "empty_denominator": "unavailable"},
    }
    policy.update(policy_overrides)
    return {
        "metric_id": "M001",
        "name": "Contract satisfaction rate",
        "inputs": [{"test_case_id": "TC001", "contract_id": "C001"}],
        "execution_policy": policy,
        "result_semantics": {
            "interpretation": "Share of satisfied applications.",
            "direction": "Higher is better.",
            "scale": "Unit interval.",
            "denominator_meaning": "Eligible contract applications.",
        },
    }


def definition_v03_data() -> dict[str, Any]:
    data = deepcopy(make_definition_data())
    data["metric_specifications"] = [metric_v03_data()]
    return data


def test_valid_v03_metric_and_definition() -> None:
    metric = MetricSpecificationV03.model_validate(metric_v03_data())
    definition = BenchmarkDefinitionV03.model_validate(definition_v03_data())
    assert metric.execution_policy.aggregation_unit == AggregationUnit.PER_TARGET
    assert definition.metric_specifications[0].metric_id == "M001"


def test_old_free_text_metric_fields_rejected_by_v03() -> None:
    data = metric_v03_data()
    data.pop("execution_policy")
    data["result_selection_policy"] = "Use the final attempt."
    with pytest.raises(ValidationError):
        MetricSpecificationV03.model_validate(data)


@pytest.mark.parametrize(
    ("mode", "order"),
    [
        ("all_distinct", None),
        ("sole_distinct", None),
        ("first_distinct", "attempt_index_ascending"),
        ("final_distinct_raw", "attempt_index_ascending"),
    ],
)
def test_attempt_selection_modes(mode: str, order: str | None) -> None:
    data: dict[str, Any] = {"mode": mode}
    if order is not None:
        data["order"] = order
    policy = AttemptSelectionPolicy.model_validate(data)
    assert policy.mode.value == mode


def test_unknown_selector_rejected() -> None:
    with pytest.raises(ValidationError):
        AttemptSelectionPolicy.model_validate({"mode": "latest_timestamp"})


def test_order_required_for_first_and_final() -> None:
    with pytest.raises(ValidationError):
        AttemptSelectionPolicy.model_validate({"mode": "first_distinct"})
    with pytest.raises(ValidationError):
        AttemptSelectionPolicy.model_validate({"mode": "final_distinct_raw"})


def test_final_eligible_requires_all_distinct() -> None:
    valid = MetricSpecificationV03.model_validate(
        metric_v03_data(unit_reduction={"mode": "final_eligible"})
    )
    assert valid.execution_policy.unit_reduction.mode == UnitReductionMode.FINAL_ELIGIBLE

    with pytest.raises(ValidationError):
        MetricSpecificationV03.model_validate(
            metric_v03_data(
                selection={"mode": "final_distinct_raw", "order": "attempt_index_ascending"},
                unit_reduction={"mode": "final_eligible"},
            )
        )


def test_canonical_semantic_and_binary_contribution() -> None:
    metric = MetricSpecificationV03.model_validate(metric_v03_data())
    rules = metric.execution_policy.contribution_mapping
    assert metric.execution_policy.eligibility.eligible_semantics == [
        ResultSemantic.SATISFIED,
        ResultSemantic.VIOLATED,
    ]
    assert rules[0].numeric_value == Decimal("1")
    assert rules[1].numeric_value == Decimal("0")
    with pytest.raises(ValidationError):
        MetricSpecificationV03.model_validate(
            metric_v03_data(
                eligibility={
                    "eligible_semantics": ["satisfied", "unknown"],
                    "non_substantive": "exclude_and_trace",
                    "missing_input": "unavailable",
                }
            )
        )


def test_duplicate_or_incomplete_contribution_mapping_rejected() -> None:
    duplicate = metric_v03_data(
        contribution_mapping=[
            {
                "source_semantic": "satisfied",
                "numeric_value": "1",
                "contribution_unit": "unit_interval",
                "explanation": "First.",
            },
            {
                "source_semantic": "satisfied",
                "numeric_value": "1",
                "contribution_unit": "unit_interval",
                "explanation": "Duplicate.",
            },
        ]
    )
    with pytest.raises(ValidationError):
        MetricSpecificationV03.model_validate(duplicate)

    with pytest.raises(ValidationError):
        MetricSpecificationV03.model_validate(
            metric_v03_data(
                contribution_mapping=[
                    {
                        "source_semantic": "satisfied",
                        "numeric_value": "1",
                        "contribution_unit": "unit_interval",
                        "explanation": "Only one mapping.",
                    }
                ]
            )
        )


@pytest.mark.parametrize("aggregation_unit", ["per_target", "per_contract", "per_test_case"])
def test_closed_aggregation_units(aggregation_unit: str) -> None:
    metric = MetricSpecificationV03.model_validate(
        metric_v03_data(aggregation_unit=aggregation_unit)
    )
    assert metric.execution_policy.aggregation_unit.value == aggregation_unit


def test_unknown_aggregation_and_deferred_policy_values_rejected() -> None:
    with pytest.raises(ValidationError):
        MetricSpecificationV03.model_validate(metric_v03_data(aggregation_unit="custom"))
    with pytest.raises(ValidationError):
        MetricSpecificationV03.model_validate(
            metric_v03_data(
                completeness={
                    "mode": "partial_threshold",
                    "empty_denominator": "unavailable",
                }
            )
        )


def test_local_policy_lists_are_unique_and_values_are_typed() -> None:
    with pytest.raises(ValidationError):
        MetricSpecificationV03.model_validate(
            metric_v03_data(
                eligibility={
                    "eligible_semantics": ["satisfied", "satisfied"],
                    "non_substantive": "exclude_and_trace",
                    "missing_input": "unavailable",
                }
            )
        )
    with pytest.raises(ValidationError):
        MetricSpecificationV03.model_validate(
            metric_v03_data(
                contribution_mapping=[
                    {
                        "source_semantic": "satisfied",
                        "numeric_value": "1.1",
                        "contribution_unit": "unit_interval",
                        "explanation": "Out of range.",
                    },
                    {
                        "source_semantic": "violated",
                        "numeric_value": "0",
                        "contribution_unit": "unit_interval",
                        "explanation": "Zero.",
                    },
                ]
            )
        )


def test_direct_grader_gate_uses_shared_selector_and_typed_trigger() -> None:
    condition = TypeAdapter(GateConditionV03).validate_python(
        {
            "condition_type": "grader_result_semantic",
            "targets": [{"test_case_id": "TC001", "contract_id": "C001"}],
            "selection": {"mode": "first_distinct", "order": "attempt_index_ascending"},
            "trigger_result_semantics": ["satisfied"],
            "quantifier": "any",
        }
    )
    assert isinstance(condition, GraderResultGateConditionV03)
    assert isinstance(condition.selection, AttemptSelectionPolicy)
    assert condition.trigger_result_semantics == [ResultSemantic.SATISFIED]


def test_gate_selector_and_trigger_duplicates_rejected() -> None:
    base = {
        "condition_type": "grader_result_semantic",
        "targets": [{"test_case_id": "TC001", "contract_id": "C001"}],
        "selection": {"mode": "all_distinct"},
        "trigger_result_semantics": ["satisfied", "satisfied"],
        "quantifier": "all",
    }
    with pytest.raises(ValidationError):
        TypeAdapter(GateConditionV03).validate_python(base)
    base["trigger_result_semantics"] = []
    with pytest.raises(ValidationError):
        TypeAdapter(GateConditionV03).validate_python(base)


def test_v02_historical_model_remains_constructible_and_does_not_silently_become_v03() -> None:
    historical = BenchmarkDefinitionV02.model_validate(make_definition_data())
    assert historical.metric_specifications[0].result_selection_policy
    with pytest.raises(ValidationError):
        BenchmarkDefinitionV03.model_validate(make_definition_data())


def test_v03_json_round_trip_and_unknown_fields() -> None:
    original = BenchmarkDefinitionV03.model_validate(definition_v03_data())
    restored = BenchmarkDefinitionV03.model_validate_json(original.model_dump_json())
    assert restored == original
    invalid = definition_v03_data()
    invalid["metric_specifications"][0]["execution_policy"]["unexpected"] = True
    with pytest.raises(ValidationError):
        BenchmarkDefinitionV03.model_validate(invalid)
