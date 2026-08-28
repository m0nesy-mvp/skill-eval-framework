"""Cross-object validation tests for Benchmark Definition v0.3."""

from copy import deepcopy
from typing import Any

import pytest
from conftest import make_definition_data

from skill_eval_framework.schemas.definition import BenchmarkDefinition as BenchmarkDefinitionV02
from skill_eval_framework.schemas.definition_v03 import BenchmarkDefinitionV03
from skill_eval_framework.validation import (
    validate_benchmark_definition,
    validate_benchmark_definition_v02,
    validate_benchmark_definition_v03,
)


def _v03_policy() -> dict[str, Any]:
    return {
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


def _v03_data() -> dict[str, Any]:
    data = deepcopy(make_definition_data())
    metric = data["metric_specifications"][0]
    for field in (
        "result_selection_policy",
        "aggregation_unit",
        "eligibility_policy",
        "contribution_mapping",
        "unit_reduction",
        "aggregation_rule",
        "weighting_policy",
        "completeness_policy",
    ):
        metric.pop(field)
    metric["execution_policy"] = _v03_policy()
    return data


def _v03_definition() -> BenchmarkDefinitionV03:
    return BenchmarkDefinitionV03.model_validate(_v03_data())


def _codes(report: Any) -> set[str]:
    return {issue.code for issue in report.issues}


def test_valid_complete_v03_definition_passes() -> None:
    definition = _v03_definition()
    assert validate_benchmark_definition_v03(definition).is_valid
    assert validate_benchmark_definition(definition).is_valid


def test_metric_input_missing_expected_assertion_fails() -> None:
    data = _v03_data()
    data["metric_specifications"][0]["inputs"] = [{"test_case_id": "TC999", "contract_id": "C001"}]
    report = validate_benchmark_definition_v03(BenchmarkDefinitionV03.model_validate(data))
    assert "DEF_METRIC_INPUT_INVALID" in _codes(report)


def test_metric_input_without_authoritative_grader_fails() -> None:
    data = _v03_data()
    data["grader_specifications"][0]["targets"] = [
        {
            "test_case_id": "TC999",
            "contract_id": "C001",
            "evidence_spec_ids": ["ES001"],
        }
    ]
    report = validate_benchmark_definition_v03(BenchmarkDefinitionV03.model_validate(data))
    assert "DEF_METRIC_GRADER_RESOLUTION_INVALID" in _codes(report)


def test_duplicate_authoritative_grader_fails() -> None:
    data = _v03_data()
    duplicate = deepcopy(data["grader_specifications"][0])
    duplicate["grader_id"] = "G002"
    data["grader_specifications"].append(duplicate)
    report = validate_benchmark_definition_v03(BenchmarkDefinitionV03.model_validate(data))
    assert "DEF_GRADER_COVERAGE_DUPLICATE" in _codes(report)


def test_metric_semantics_compatible_and_incompatible() -> None:
    assert validate_benchmark_definition_v03(_v03_definition()).is_valid

    data = _v03_data()
    data["grader_specifications"][0]["result_semantics"]["not_exercised"] = None
    policy = data["metric_specifications"][0]["execution_policy"]
    policy["eligibility"]["eligible_semantics"].append("not_exercised")
    policy["contribution_mapping"].append(
        {
            "source_semantic": "not_exercised",
            "numeric_value": "0",
            "contribution_unit": "unit_interval",
            "explanation": "Not exercised contributes zero.",
        }
    )
    report = validate_benchmark_definition_v03(BenchmarkDefinitionV03.model_validate(data))
    assert "DEF_V03_METRIC_SEMANTIC_INCOMPATIBLE" in _codes(report)


def test_contribution_source_semantic_must_be_upstream_supported() -> None:
    data = _v03_data()
    data["grader_specifications"][0]["result_semantics"]["not_exercised"] = None
    policy = data["metric_specifications"][0]["execution_policy"]
    policy["eligibility"]["eligible_semantics"].append("not_exercised")
    policy["contribution_mapping"].append(
        {
            "source_semantic": "not_exercised",
            "numeric_value": "0",
            "contribution_unit": "unit_interval",
            "explanation": "Not exercised contributes zero.",
        }
    )
    report = validate_benchmark_definition_v03(BenchmarkDefinitionV03.model_validate(data))
    assert "DEF_V03_METRIC_SEMANTIC_INCOMPATIBLE" in _codes(report)


def test_direct_grader_gate_semantic_compatibility() -> None:
    data = _v03_data()
    data["gate_specifications"][0]["condition"] = {
        "condition_type": "grader_result_semantic",
        "targets": [{"test_case_id": "TC001", "contract_id": "C001"}],
        "selection": {"mode": "all_distinct"},
        "trigger_result_semantics": ["violated"],
        "quantifier": "any",
    }
    assert validate_benchmark_definition_v03(BenchmarkDefinitionV03.model_validate(data)).is_valid

    data["grader_specifications"][0]["result_semantics"]["not_exercised"] = None
    data["gate_specifications"][0]["condition"]["trigger_result_semantics"] = ["not_exercised"]
    report = validate_benchmark_definition_v03(BenchmarkDefinitionV03.model_validate(data))
    assert "DEF_V03_GATE_TRIGGER_SEMANTIC_INCOMPATIBLE" in _codes(report)


def test_multi_target_gate_reports_one_incompatible_grader() -> None:
    data = _v03_data()
    data["contracts"].append(deepcopy(data["contracts"][0]) | {"contract_id": "C002"})
    data["test_cases"][0]["expected_assertions"].append(
        {"contract_id": "C002", "expectation": "The second contract is satisfied."}
    )
    data["evidence_specifications"][0]["targets"].append(
        {"test_case_id": "TC001", "contract_id": "C002"}
    )
    second_grader = deepcopy(data["grader_specifications"][0])
    second_grader["grader_id"] = "G002"
    second_grader["targets"] = [
        {
            "test_case_id": "TC001",
            "contract_id": "C002",
            "evidence_spec_ids": ["ES001"],
        }
    ]
    second_grader["result_semantics"]["not_exercised"] = None
    data["grader_specifications"].append(second_grader)
    data["gate_specifications"][0]["condition"] = {
        "condition_type": "grader_result_semantic",
        "targets": [
            {"test_case_id": "TC001", "contract_id": "C001"},
            {"test_case_id": "TC001", "contract_id": "C002"},
        ],
        "selection": {"mode": "all_distinct"},
        "trigger_result_semantics": ["not_exercised"],
        "quantifier": "any",
    }
    report = validate_benchmark_definition_v03(BenchmarkDefinitionV03.model_validate(data))
    assert "DEF_V03_GATE_TRIGGER_SEMANTIC_INCOMPATIBLE" in _codes(report)


@pytest.mark.parametrize("aggregation_unit", ["per_contract", "per_test_case"])
def test_non_target_aggregation_units_have_graph_support(aggregation_unit: str) -> None:
    data = _v03_data()
    data["metric_specifications"][0]["execution_policy"]["aggregation_unit"] = aggregation_unit
    assert validate_benchmark_definition_v03(BenchmarkDefinitionV03.model_validate(data)).is_valid


def test_metric_threshold_gate_and_stale_reference() -> None:
    definition = _v03_definition()
    assert validate_benchmark_definition_v03(definition).is_valid
    stale = definition.model_copy(deep=True)
    stale.gate_specifications[0].condition = stale.gate_specifications[0].condition.model_copy(
        update={"metric_id": "M999"}
    )
    assert "DEF_GATE_UNKNOWN_METRIC_REF" in _codes(validate_benchmark_definition_v03(stale))


def test_overall_and_acceptance_refs_are_checked_for_v03() -> None:
    data = _v03_data()
    data["overall_score_policy"] = {
        "mode": "weighted_normalized_mean",
        "metric_contributions": [
            {
                "metric_id": "M001",
                "weight": "1",
                "normalization": {"type": "identity_unit_interval"},
                "unavailable_result_handling": "overall_unavailable",
                "missing_result_handling": "overall_unavailable",
            }
        ],
        "minimum_available_weight_fraction": "1",
        "canonical_scale": "unit_interval",
        "canonical_precision": 4,
    }
    data["acceptance_policy"] = {
        "mode": "gate_based",
        "participating_gates": [
            {
                "gate_id": "GATE001",
                "indeterminate_handling": "overall_indeterminate",
                "missing_result_handling": "overall_blocked",
            }
        ],
    }
    assert validate_benchmark_definition_v03(BenchmarkDefinitionV03.model_validate(data)).is_valid


def test_explicit_v02_v03_dispatch_does_not_guess() -> None:
    v02 = BenchmarkDefinitionV02.model_validate(make_definition_data())
    v03 = _v03_definition()
    assert validate_benchmark_definition_v02(v02).is_valid
    assert validate_benchmark_definition_v03(v03).is_valid
    with pytest.raises(TypeError):
        validate_benchmark_definition_v02(v03)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        validate_benchmark_definition_v03(v02)  # type: ignore[arg-type]


def test_shuffled_v03_collections_produce_same_report() -> None:
    first = _v03_data()
    first["metric_specifications"][0]["inputs"] = [{"test_case_id": "TC999", "contract_id": "C001"}]
    first["contracts"][0]["requirement_ids"] = ["R999"]
    second = deepcopy(first)
    second["requirements"].reverse()
    second["contracts"].reverse()
    second["test_cases"].reverse()
    second["grader_specifications"].reverse()
    first_report = validate_benchmark_definition_v03(BenchmarkDefinitionV03.model_validate(first))
    second_report = validate_benchmark_definition_v03(BenchmarkDefinitionV03.model_validate(second))
    assert first_report == second_report
