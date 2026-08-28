"""Object-local tests for Result and Scorecard models."""

from copy import deepcopy
from decimal import Decimal
from typing import Any

import pytest
from conftest import DIGEST, NOW
from pydantic import TypeAdapter, ValidationError

from skill_eval_framework.schemas.results import (
    AcceptanceEvaluation,
    DefinitionPolicyRef,
    ExpectedApplicationRef,
    GateResult,
    GraderResult,
    MetricCoverageSummary,
    MetricResult,
    OverallScoreOutcome,
    Scorecard,
    ScorecardResultInventory,
)


def grader_result_data(judgment: str = "satisfied") -> dict[str, object]:
    return {
        "grader_result_id": "GR001",
        "run_id": "RUN001",
        "episode_id": "E001",
        "grader_id": "G001",
        "test_case_id": "TC001",
        "contract_id": "C001",
        "evidence_ids": ["EV001"],
        "judgment": judgment,
        "explanation": {
            "evidence_contributions": [
                {"evidence_id": "EV001", "contribution": "Shows the output."}
            ],
            "observed_facts": ["Output exists."],
            "semantic_basis": "The observation satisfies the contract.",
            "supported_failure_criterion": None,
            "supported_failure_mode": None,
            "insufficiency_gaps": [],
            "inference_notes": [],
        },
        "rubric_result": None,
        "created_at": NOW,
    }


def metric_result_data(status: str = "available") -> dict[str, object]:
    return {
        "metric_result_id": "MR001",
        "run_id": "RUN001",
        "metric_id": "M001",
        "status": status,
        "value": {"value_kind": "rate", "canonical_value": "1", "unit": "ratio"},
        "unavailable_reason": None,
        "unavailable_explanation": None,
        "coverage": {
            "expected_input_count": 1,
            "available_raw_result_count": 1,
            "distinct_result_count": 1,
            "selected_result_count": 1,
            "substantive_eligible_count": 1,
            "not_exercised_count": 0,
            "insufficient_evidence_count": 0,
            "unavailable_input_count": 0,
            "declared_aggregation_unit": "contract application",
            "contributing_unit_count": 1,
            "denominator": "1",
            "coverage_ratio": "1",
        },
        "input_traces": [
            {
                "grader_result_id": "GR001",
                "disposition": "included",
                "reason": "Eligible substantive result.",
                "aggregation_unit_key": "TC001:C001",
                "contribution_value": "1",
            }
        ],
        "missing_inputs": [],
        "created_at": NOW,
    }


def test_violated_grader_result_requires_failure_criterion() -> None:
    with pytest.raises(ValidationError, match="supported_failure_criterion"):
        GraderResult.model_validate(grader_result_data("violated"))


def test_satisfied_grader_result_rejects_failure_criterion() -> None:
    data = grader_result_data()
    data["explanation"]["supported_failure_criterion"] = "Output is absent."
    with pytest.raises(ValidationError, match="satisfied and not_exercised"):
        GraderResult.model_validate(data)


def test_insufficient_grader_result_requires_gaps() -> None:
    with pytest.raises(ValidationError, match="insufficiency_gaps"):
        GraderResult.model_validate(grader_result_data("insufficient_evidence"))


def test_insufficient_grader_result_may_name_criterion_with_missing_support() -> None:
    data = grader_result_data("insufficient_evidence")
    data["explanation"]["supported_failure_criterion"] = "Expected output is absent."
    data["explanation"]["insufficiency_gaps"] = ["Attribution evidence is missing."]
    result = GraderResult.model_validate(data)
    assert result.judgment == "insufficient_evidence"


def test_grader_result_exposes_frozen_logical_key() -> None:
    result = GraderResult.model_validate(grader_result_data())
    assert result.logical_key == ("RUN001", "E001", "G001", "TC001", "C001")


def test_available_metric_requires_value() -> None:
    data = metric_result_data()
    data["value"] = None
    with pytest.raises(ValidationError, match="requires value"):
        MetricResult.model_validate(data)


def test_available_metric_with_canonical_value_is_valid() -> None:
    result = MetricResult.model_validate(metric_result_data())
    assert result.status == "available"
    assert result.value is not None


def test_unavailable_metric_requires_reason_and_explanation() -> None:
    data = metric_result_data("unavailable")
    data["value"] = None
    with pytest.raises(ValidationError, match="requires reason and explanation"):
        MetricResult.model_validate(data)


def test_unavailable_metric_forbids_value() -> None:
    data = metric_result_data("unavailable")
    data["unavailable_reason"] = "empty_denominator"
    data["unavailable_explanation"] = "No eligible inputs formed a denominator."
    with pytest.raises(ValidationError, match="must not include value"):
        MetricResult.model_validate(data)


def test_metric_canonical_zero_is_a_valid_value() -> None:
    data = metric_result_data()
    data["value"]["canonical_value"] = "0"
    result = MetricResult.model_validate(data)
    assert result.value is not None
    assert result.value.canonical_value == Decimal("0")


def test_metric_coverage_counts_cannot_be_negative() -> None:
    data = metric_result_data()
    data["coverage"]["expected_input_count"] = -1
    with pytest.raises(ValidationError):
        MetricResult.model_validate(data)


@pytest.mark.parametrize(
    ("path", "result", "trigger_source", "condition_outcome"),
    [
        ("condition_true", "TRIGGERED", "condition", "true"),
        ("condition_false", "OPEN", None, "false"),
        ("unknown_indeterminate", "INDETERMINATE", None, "unknown"),
        ("unknown_triggered", "TRIGGERED", "unavailable_handling", "unknown"),
    ],
)
def test_gate_evaluation_paths_have_exact_semantic_mapping(
    path: str, result: str, trigger_source: str | None, condition_outcome: str
) -> None:
    gate = GateResult.model_validate(
        {
            "gate_result_id": "GATER001",
            "run_id": "RUN001",
            "gate_id": "GATE001",
            "result": result,
            "evaluation_path": path,
            "trigger_source": trigger_source,
            "input_summary": {
                "condition_type": "metric_threshold",
                "grader_contributions": [],
                "metric_result_id": "MR001",
                "metric_input_state": "available",
                "observed_canonical_value": "0.9",
                "comparator_outcome": condition_outcome,
                "quantifier": "not_applicable",
                "condition_outcome": condition_outcome,
            },
            "explanation": "Frozen mapping applied.",
            "created_at": NOW,
        }
    )
    assert gate.result == result


def test_gate_result_rejects_inconsistent_trigger_source() -> None:
    with pytest.raises(ValidationError, match="inconsistent"):
        GateResult.model_validate(
            {
                "gate_result_id": "GATER001",
                "run_id": "RUN001",
                "gate_id": "GATE001",
                "result": "OPEN",
                "evaluation_path": "condition_true",
                "trigger_source": None,
                "input_summary": {
                    "condition_type": "grader_result",
                    "grader_contributions": [],
                    "metric_input_state": "not_applicable",
                    "comparator_outcome": "not_applicable",
                    "quantifier": "any",
                    "condition_outcome": "true",
                },
                "explanation": "Invalid mapping.",
                "created_at": NOW,
            }
        )


def test_expected_application_union_rejects_cross_variant_fields() -> None:
    with pytest.raises(ValidationError):
        TypeAdapter(ExpectedApplicationRef).validate_python(
            {
                "application_type": "metric_result",
                "metric_id": "M001",
                "gate_id": "GATE001",
            }
        )


def test_inventory_rejects_duplicate_result_ids() -> None:
    with pytest.raises(ValidationError, match="metric_result_ids"):
        ScorecardResultInventory.model_validate(
            {
                "episode_ids": [],
                "grader_result_ids": [],
                "metric_result_ids": ["MR001", "MR001"],
                "gate_result_ids": [],
                "missing_applications": [],
            }
        )


def test_inventory_rejects_duplicate_missing_logical_identity() -> None:
    missing = {
        "application_ref": {"application_type": "metric_result", "metric_id": "M001"},
        "diagnostic_ids": ["D001"],
        "explanation": "Calculator did not complete.",
    }
    with pytest.raises(ValidationError, match="missing_applications"):
        ScorecardResultInventory.model_validate(
            {
                "episode_ids": [],
                "grader_result_ids": [],
                "metric_result_ids": [],
                "gate_result_ids": [],
                "missing_applications": [missing, missing],
            }
        )


def test_available_overall_requires_complete_weight_trace() -> None:
    with pytest.raises(ValidationError, match="value and contribution traces"):
        OverallScoreOutcome.model_validate(
            {
                "policy_ref": {
                    "definition_digest": DIGEST,
                    "policy_path": "/overall_score_policy",
                },
                "evaluation_status": "available",
                "contribution_traces": [],
                "diagnostic_ids": [],
                "explanation": "No trace.",
            }
        )


def test_available_overall_with_value_and_weight_trace_is_valid() -> None:
    outcome = OverallScoreOutcome.model_validate(
        {
            "policy_ref": {
                "definition_digest": DIGEST,
                "policy_path": "/overall_score_policy",
            },
            "evaluation_status": "available",
            "canonical_value": "0.9",
            "contribution_traces": [
                {
                    "metric_id": "M001",
                    "weight": "1",
                    "metric_result_id": "MR001",
                    "application_state": "available",
                    "policy_handling": "included",
                    "normalized_value": "0.9",
                    "weighted_contribution": "0.9",
                }
            ],
            "total_selected_weight": "1",
            "available_weight": "1",
            "available_weight_fraction": "1",
            "minimum_required_weight_fraction": "0.8",
            "final_included_denominator": "1",
            "diagnostic_ids": [],
            "explanation": "Weighted normalized mean is available.",
        }
    )
    assert outcome.canonical_value == Decimal("0.9")


def test_disabled_overall_forbids_canonical_value() -> None:
    with pytest.raises(ValidationError, match="must not include value or reason"):
        OverallScoreOutcome.model_validate(
            {
                "policy_ref": {
                    "definition_digest": DIGEST,
                    "policy_path": "/overall_score_policy",
                },
                "evaluation_status": "disabled",
                "canonical_value": "0",
                "contribution_traces": [],
                "diagnostic_ids": [],
                "explanation": "Policy is disabled.",
            }
        )


def test_overall_production_failure_requires_direct_diagnostic() -> None:
    with pytest.raises(ValidationError, match="requires diagnostic_ids"):
        OverallScoreOutcome.model_validate(
            {
                "policy_ref": {
                    "definition_digest": DIGEST,
                    "policy_path": "/overall_score_policy",
                },
                "evaluation_status": "production_failed",
                "contribution_traces": [],
                "diagnostic_ids": [],
                "explanation": "Calculator failed.",
            }
        )


def test_overall_production_failure_may_retain_partial_trace() -> None:
    outcome = OverallScoreOutcome.model_validate(
        {
            "policy_ref": {
                "definition_digest": DIGEST,
                "policy_path": "/overall_score_policy",
            },
            "evaluation_status": "production_failed",
            "contribution_traces": [
                {
                    "metric_id": "M001",
                    "weight": "1",
                    "metric_result_id": "MR001",
                    "application_state": "available",
                    "policy_handling": "included",
                }
            ],
            "diagnostic_ids": ["D001"],
            "explanation": "Calculator failed after selecting the Metric.",
        }
    )
    assert outcome.evaluation_status == "production_failed"


def test_produced_acceptance_requires_semantic_and_gate_trace() -> None:
    with pytest.raises(ValidationError, match="requires semantic and gate contributions"):
        AcceptanceEvaluation.model_validate(
            {
                "policy_ref": {
                    "definition_digest": DIGEST,
                    "policy_path": "/acceptance_policy",
                },
                "evaluation_status": "produced",
                "acceptance": "ACCEPTABLE",
                "gate_contributions": [],
                "diagnostic_ids": [],
                "explanation": "No gates traced.",
            }
        )


def test_produced_acceptance_with_semantic_and_trace_is_valid() -> None:
    evaluation = AcceptanceEvaluation.model_validate(
        {
            "policy_ref": {
                "definition_digest": DIGEST,
                "policy_path": "/acceptance_policy",
            },
            "evaluation_status": "produced",
            "acceptance": "ACCEPTABLE",
            "gate_contributions": [
                {
                    "gate_id": "GATE001",
                    "gate_result_id": "GATER001",
                    "application_state": "OPEN",
                    "policy_handling": "open",
                    "propagation_outcome": "no_block",
                    "explanation": "Participating Gate is open.",
                }
            ],
            "diagnostic_ids": [],
            "explanation": "All participating Gates are open.",
        }
    )
    assert evaluation.acceptance == "ACCEPTABLE"


def test_disabled_acceptance_cannot_claim_acceptable() -> None:
    with pytest.raises(ValidationError, match="only produced"):
        AcceptanceEvaluation.model_validate(
            {
                "policy_ref": {
                    "definition_digest": DIGEST,
                    "policy_path": "/acceptance_policy",
                },
                "evaluation_status": "disabled",
                "acceptance": "ACCEPTABLE",
                "gate_contributions": [],
                "diagnostic_ids": [],
                "explanation": "Disabled policy.",
            }
        )


def test_acceptance_production_failure_requires_direct_diagnostic() -> None:
    with pytest.raises(ValidationError, match="requires diagnostic_ids"):
        AcceptanceEvaluation.model_validate(
            {
                "policy_ref": {
                    "definition_digest": DIGEST,
                    "policy_path": "/acceptance_policy",
                },
                "evaluation_status": "production_failed",
                "gate_contributions": [],
                "diagnostic_ids": [],
                "explanation": "Evaluator failed.",
            }
        )


def test_acceptance_production_failure_may_retain_partial_gate_trace() -> None:
    evaluation = AcceptanceEvaluation.model_validate(
        {
            "policy_ref": {
                "definition_digest": DIGEST,
                "policy_path": "/acceptance_policy",
            },
            "evaluation_status": "production_failed",
            "gate_contributions": [
                {
                    "gate_id": "GATE001",
                    "gate_result_id": "GATER001",
                    "application_state": "OPEN",
                    "policy_handling": "open",
                    "propagation_outcome": "no_block",
                    "explanation": "Gate was processed before evaluator failure.",
                }
            ],
            "diagnostic_ids": ["D002"],
            "explanation": "Evaluator failed before final semantic production.",
        }
    )
    assert evaluation.evaluation_status == "production_failed"


def test_repeated_episode_grader_application_refs_remain_distinct() -> None:
    adapter = TypeAdapter(ExpectedApplicationRef)
    common = {
        "application_type": "grader_result",
        "grader_id": "G001",
        "test_case_id": "TC001",
        "contract_id": "C001",
    }
    episode_21 = adapter.validate_python({**common, "episode_id": "E21"})
    episode_23 = adapter.validate_python({**common, "episode_id": "E23"})
    assert episode_21.logical_key != episode_23.logical_key


def test_finalized_scorecard_requires_finalized_at(scorecard_data: dict[str, Any]) -> None:
    data = deepcopy(scorecard_data)
    data["finalization_status"] = "finalized_audit"
    with pytest.raises(ValidationError, match="requires finalized_at"):
        Scorecard.model_validate(data)


def test_policy_reference_rejects_arbitrary_json_pointer() -> None:
    with pytest.raises(ValidationError):
        DefinitionPolicyRef.model_validate(
            {"definition_digest": DIGEST, "policy_path": "/custom_policy"}
        )


def test_coverage_ratio_stays_in_unit_interval() -> None:
    data = metric_result_data()["coverage"]
    data["coverage_ratio"] = "1.01"
    with pytest.raises(ValidationError):
        MetricCoverageSummary.model_validate(data)
