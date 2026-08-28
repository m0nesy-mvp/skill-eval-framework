"""Object-local tests for frozen Benchmark Definition models."""

from copy import deepcopy
from decimal import Decimal
from typing import Any

import pytest
from pydantic import TypeAdapter, ValidationError

from skill_eval_framework.schemas.definition import (
    AcceptancePolicy,
    BenchmarkDefinition,
    Contract,
    GateCondition,
    LinearBoundedNormalization,
    MetricNormalization,
    MetricThresholdGateCondition,
    OverallScorePolicy,
    Requirement,
)


def test_representative_frozen_definition_is_valid(definition_data: dict[str, Any]) -> None:
    definition = BenchmarkDefinition.model_validate(definition_data)
    assert definition.benchmark_id == "skill.eval.v0"
    assert definition.gate_specifications[0].condition.condition_type == "metric_threshold"


def test_unknown_definition_field_is_forbidden(definition_data: dict[str, Any]) -> None:
    definition_data["unexpected"] = True
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        BenchmarkDefinition.model_validate(definition_data)


def test_requirement_id_uses_frozen_pattern() -> None:
    with pytest.raises(ValidationError):
        Requirement.model_validate(
            {
                "requirement_id": "REQ-1",
                "statement": "Valid statement",
                "source": "skill",
                "evaluation_type": "outcome",
            }
        )


def test_valid_requirement_accepts_frozen_vocabulary() -> None:
    requirement = Requirement.model_validate(
        {
            "requirement_id": "R001",
            "statement": "The output exists.",
            "source": "skill",
            "evaluation_type": "outcome",
        }
    )
    assert requirement.evaluation_type == "outcome"


def test_requirement_rejects_unknown_evaluation_type() -> None:
    with pytest.raises(ValidationError):
        Requirement.model_validate(
            {
                "requirement_id": "R001",
                "statement": "The output exists.",
                "source": "skill",
                "evaluation_type": "quality",
            }
        )


def test_contract_rejects_unknown_criticality(definition_data: dict[str, Any]) -> None:
    contract = deepcopy(definition_data["contracts"][0])
    contract["criticality"] = "severe"
    with pytest.raises(ValidationError):
        Contract.model_validate(contract)


def test_whitespace_only_statement_is_rejected() -> None:
    with pytest.raises(ValidationError, match="non-empty"):
        Requirement.model_validate(
            {
                "requirement_id": "R001",
                "statement": "   ",
                "source": "skill",
                "evaluation_type": "outcome",
            }
        )


def test_contract_requirement_ids_are_unique(definition_data: dict[str, Any]) -> None:
    data = deepcopy(definition_data)
    data["contracts"][0]["requirement_ids"] = ["R001", "R001"]
    with pytest.raises(ValidationError, match="requirement_ids"):
        BenchmarkDefinition.model_validate(data)


def test_test_case_assertion_targets_are_unique(definition_data: dict[str, Any]) -> None:
    data = deepcopy(definition_data)
    assertion = deepcopy(data["test_cases"][0]["expected_assertions"][0])
    data["test_cases"][0]["expected_assertions"].append(assertion)
    with pytest.raises(ValidationError, match="expected_assertions"):
        BenchmarkDefinition.model_validate(data)


def test_evidence_targets_are_unique(definition_data: dict[str, Any]) -> None:
    data = deepcopy(definition_data)
    target = deepcopy(data["evidence_specifications"][0]["targets"][0])
    data["evidence_specifications"][0]["targets"].append(target)
    with pytest.raises(ValidationError, match="targets"):
        BenchmarkDefinition.model_validate(data)


def test_rubric_dimension_requires_two_anchors(definition_data: dict[str, Any]) -> None:
    data = deepcopy(definition_data)
    data["grader_specifications"][0]["rubric"] = {
        "dimensions": [
            {
                "name": "quality",
                "criterion": "Output quality",
                "anchors": [{"label": "good", "meaning": "Good output"}],
            }
        ],
        "overall_interpretation": "Interpret dimensions together.",
    }
    with pytest.raises(ValidationError):
        BenchmarkDefinition.model_validate(data)


def test_linear_normalization_requires_increasing_bounds() -> None:
    with pytest.raises(ValidationError, match="source_max"):
        LinearBoundedNormalization.model_validate(
            {
                "type": "linear_bounded",
                "source_min": "1",
                "source_max": "1",
                "direction": "higher_is_better",
            }
        )


def test_gate_condition_discriminator_selects_metric_threshold() -> None:
    adapter = TypeAdapter(GateCondition)
    condition = adapter.validate_python(
        {
            "condition_type": "metric_threshold",
            "metric_id": "M001",
            "comparator": "gte",
            "threshold_value": "0.75",
        }
    )
    assert isinstance(condition, MetricThresholdGateCondition)
    assert condition.threshold_value == Decimal("0.75")


def test_gate_condition_rejects_unknown_variant() -> None:
    with pytest.raises(ValidationError):
        TypeAdapter(GateCondition).validate_python({"condition_type": "custom"})


def test_metric_normalization_discriminator_selects_identity() -> None:
    normalization = TypeAdapter(MetricNormalization).validate_python(
        {"type": "identity_unit_interval"}
    )
    assert normalization.type == "identity_unit_interval"


def test_metric_normalization_rejects_unknown_variant() -> None:
    with pytest.raises(ValidationError):
        TypeAdapter(MetricNormalization).validate_python({"type": "logarithmic"})


def test_overall_policy_discriminator_selects_disabled_variant() -> None:
    policy = TypeAdapter(OverallScorePolicy).validate_python({"mode": "disabled"})
    assert policy.mode == "disabled"


def test_acceptance_policy_discriminator_selects_disabled_variant() -> None:
    policy = TypeAdapter(AcceptancePolicy).validate_python({"mode": "disabled"})
    assert policy.mode == "disabled"


def test_overall_policy_rejects_non_positive_weight() -> None:
    with pytest.raises(ValidationError):
        TypeAdapter(OverallScorePolicy).validate_python(
            {
                "mode": "weighted_normalized_mean",
                "metric_contributions": [
                    {
                        "metric_id": "M001",
                        "weight": "0",
                        "normalization": {"type": "identity_unit_interval"},
                        "unavailable_result_handling": "overall_unavailable",
                        "missing_result_handling": "overall_unavailable",
                    }
                ],
                "minimum_available_weight_fraction": "1",
                "canonical_scale": "unit_interval",
                "canonical_precision": 4,
            }
        )


def test_overall_policy_rejects_precision_above_twelve() -> None:
    with pytest.raises(ValidationError):
        TypeAdapter(OverallScorePolicy).validate_python(
            {
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
                "canonical_precision": 13,
            }
        )


def test_overall_policy_rejects_duplicate_metric_membership() -> None:
    contribution = {
        "metric_id": "M001",
        "weight": "1",
        "normalization": {"type": "identity_unit_interval"},
        "unavailable_result_handling": "overall_unavailable",
        "missing_result_handling": "overall_unavailable",
    }
    with pytest.raises(ValidationError, match="metric_contributions"):
        TypeAdapter(OverallScorePolicy).validate_python(
            {
                "mode": "weighted_normalized_mean",
                "metric_contributions": [contribution, contribution],
                "minimum_available_weight_fraction": "1",
                "canonical_scale": "unit_interval",
                "canonical_precision": 4,
            }
        )


def test_acceptance_policy_rejects_duplicate_gate_membership() -> None:
    contribution = {
        "gate_id": "GATE001",
        "indeterminate_handling": "overall_indeterminate",
        "missing_result_handling": "overall_blocked",
    }
    with pytest.raises(ValidationError, match="participating_gates"):
        TypeAdapter(AcceptancePolicy).validate_python(
            {"mode": "gate_based", "participating_gates": [contribution, contribution]}
        )


def test_resource_digest_requires_lowercase_sha256(definition_data: dict[str, Any]) -> None:
    data = deepcopy(definition_data)
    data["semantic_resource_bindings"] = [
        {"resource_ref": "rubric.md", "semantic_role": "rubric", "content_digest": "SHA256:x"}
    ]
    with pytest.raises(ValidationError):
        BenchmarkDefinition.model_validate(data)
