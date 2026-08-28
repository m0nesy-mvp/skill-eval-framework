from __future__ import annotations

from copy import deepcopy

from validation_helpers import codes, complete_definition

from skill_eval_framework.schemas.definition import (
    AcceptanceGateContribution,
    Contract,
    DefinitionResourceBinding,
    EvaluationType,
    EvidenceTarget,
    GateBasedAcceptancePolicy,
    GraderResultGateCondition,
    MetricInput,
    WeightedNormalizedMeanOverallScorePolicy,
)
from skill_eval_framework.validation import validate_benchmark_definition


def test_complete_definition_is_valid() -> None:
    assert validate_benchmark_definition(complete_definition()).is_valid


def test_unknown_requirement_reference() -> None:
    definition = complete_definition().model_copy(deep=True)
    definition.contracts[0].requirement_ids = ["R999"]
    assert "DEF_UNKNOWN_REQUIREMENT_REF" in codes(validate_benchmark_definition(definition))


def test_contract_evaluation_type_mismatch() -> None:
    definition = complete_definition().model_copy(deep=True)
    definition.contracts[0].evaluation_type = EvaluationType.WORKFLOW
    assert "DEF_CONTRACT_EVALUATION_TYPE_MISMATCH" in codes(
        validate_benchmark_definition(definition)
    )


def test_requirement_must_be_covered() -> None:
    definition = complete_definition().model_copy(deep=True)
    extra = definition.requirements[0].model_copy(update={"requirement_id": "R002"})
    definition.requirements.append(extra)
    assert "DEF_REQUIREMENT_UNCOVERED" in codes(validate_benchmark_definition(definition))


def test_unknown_contract_in_expected_assertion() -> None:
    definition = complete_definition().model_copy(deep=True)
    definition.test_cases[0].expected_assertions[0].contract_id = "C999"
    assert "DEF_UNKNOWN_CONTRACT_REF" in codes(validate_benchmark_definition(definition))


def test_contract_must_be_covered_by_assertion() -> None:
    definition = complete_definition().model_copy(deep=True)
    definition.contracts.append(
        Contract(
            contract_id="C002",
            requirement_ids=["R001"],
            statement="A second observable contract.",
            evaluation_type=EvaluationType.OUTCOME,
            criticality="normal",
            success_criteria=["Second output exists."],
            failure_criteria=["Second output is absent."],
            failure_modes=["Second output is omitted."],
        )
    )
    assert "DEF_CONTRACT_UNCOVERED" in codes(validate_benchmark_definition(definition))


def test_evidence_target_pair_must_resolve() -> None:
    definition = complete_definition().model_copy(deep=True)
    definition.evidence_specifications[0].targets = [
        EvidenceTarget(test_case_id="TC001", contract_id="C999")
    ]
    assert "DEF_EVIDENCE_TARGET_INVALID" in codes(validate_benchmark_definition(definition))


def test_every_expected_assertion_needs_evidence_spec() -> None:
    definition = complete_definition().model_copy(deep=True)
    definition.contracts.append(
        Contract(
            contract_id="C002",
            requirement_ids=["R001"],
            statement="A second observable contract.",
            evaluation_type=EvaluationType.OUTCOME,
            criticality="normal",
            success_criteria=["Second output exists."],
            failure_criteria=["Second output is absent."],
            failure_modes=["Second output is omitted."],
        )
    )
    definition.test_cases[0].expected_assertions.append(
        definition.test_cases[0].expected_assertions[0].model_copy(update={"contract_id": "C002"})
    )
    assert "DEF_EVIDENCE_COVERAGE_MISSING" in codes(validate_benchmark_definition(definition))


def test_grader_evidence_target_must_match() -> None:
    definition = complete_definition().model_copy(deep=True)
    definition.evidence_specifications[0].targets = [
        EvidenceTarget(test_case_id="TC001", contract_id="C999")
    ]
    assert "DEF_GRADER_EVIDENCE_TARGET_MISMATCH" in codes(validate_benchmark_definition(definition))


def test_authoritative_grader_is_required() -> None:
    definition = complete_definition().model_copy(deep=True)
    definition.contracts.append(
        Contract(
            contract_id="C002",
            requirement_ids=["R001"],
            statement="A second observable contract.",
            evaluation_type=EvaluationType.OUTCOME,
            criticality="normal",
            success_criteria=["Second output exists."],
            failure_criteria=["Second output is absent."],
            failure_modes=["Second output is omitted."],
        )
    )
    definition.test_cases[0].expected_assertions.append(
        definition.test_cases[0].expected_assertions[0].model_copy(update={"contract_id": "C002"})
    )
    definition.evidence_specifications.append(
        definition.evidence_specifications[0].model_copy(
            update={
                "evidence_spec_id": "ES002",
                "targets": [EvidenceTarget(test_case_id="TC001", contract_id="C002")],
            }
        )
    )
    assert "DEF_GRADER_COVERAGE_MISSING" in codes(validate_benchmark_definition(definition))


def test_authoritative_grader_cannot_be_duplicated() -> None:
    definition = complete_definition().model_copy(deep=True)
    definition.grader_specifications.append(
        definition.grader_specifications[0].model_copy(update={"grader_id": "G002"})
    )
    assert "DEF_GRADER_COVERAGE_DUPLICATE" in codes(validate_benchmark_definition(definition))


def test_metric_input_pair_must_resolve() -> None:
    definition = complete_definition().model_copy(deep=True)
    definition.metric_specifications[0].inputs = [
        MetricInput(test_case_id="TC999", contract_id="C001")
    ]
    assert "DEF_METRIC_INPUT_INVALID" in codes(validate_benchmark_definition(definition))


def test_grader_gate_target_pair_must_resolve() -> None:
    definition = complete_definition().model_copy(deep=True)
    definition.gate_specifications[0].condition = GraderResultGateCondition(
        condition_type="grader_result_semantic",
        targets=[{"test_case_id": "TC999", "contract_id": "C001"}],
        result_selection_policy="final",
        trigger_result_semantics=["violated"],
        quantifier="any",
    )
    assert "DEF_GATE_TARGET_INVALID" in codes(validate_benchmark_definition(definition))


def test_gate_metric_reference_must_resolve() -> None:
    definition = complete_definition().model_copy(deep=True)
    definition.gate_specifications[0].condition = definition.gate_specifications[
        0
    ].condition.model_copy(update={"metric_id": "M999"})
    assert "DEF_GATE_UNKNOWN_METRIC_REF" in codes(validate_benchmark_definition(definition))


def test_overall_policy_metric_reference_must_resolve() -> None:
    definition = complete_definition().model_copy(deep=True)
    policy = {
        "mode": "weighted_normalized_mean",
        "metric_contributions": [
            {
                "metric_id": "M999",
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
    definition.overall_score_policy = WeightedNormalizedMeanOverallScorePolicy.model_validate(
        policy
    )
    assert "DEF_OVERALL_UNKNOWN_METRIC_REF" in codes(validate_benchmark_definition(definition))


def test_acceptance_policy_gate_reference_must_resolve() -> None:
    definition = complete_definition().model_copy(deep=True)
    definition.acceptance_policy = GateBasedAcceptancePolicy(
        mode="gate_based",
        participating_gates=[
            AcceptanceGateContribution(
                gate_id="GATE999",
                indeterminate_handling="overall_indeterminate",
                missing_result_handling="overall_blocked",
            )
        ],
    )
    assert "DEF_ACCEPTANCE_UNKNOWN_GATE_REF" in codes(validate_benchmark_definition(definition))


def test_duplicate_definition_ids_are_reported() -> None:
    definition = complete_definition().model_copy(deep=True)
    definition.requirements.append(deepcopy(definition.requirements[0]))
    assert any(
        issue.code == "DEF_DUPLICATE_REQUIREMENT_ID"
        for issue in validate_benchmark_definition(definition).issues
    )


def test_duplicate_resource_refs_are_reported() -> None:
    definition = complete_definition().model_copy(deep=True)
    binding = {
        "resource_ref": "skill://same",
        "semantic_role": "skill",
        "content_digest": "sha256:" + "b" * 64,
    }
    definition.semantic_resource_bindings = [
        DefinitionResourceBinding.model_validate(binding),
        DefinitionResourceBinding.model_validate(binding),
    ]
    assert "DEF_DUPLICATE_RESOURCE_REF" in codes(validate_benchmark_definition(definition))


def test_definition_issue_order_is_deterministic() -> None:
    first = complete_definition().model_copy(deep=True)
    first.contracts[0].requirement_ids = ["R999"]
    first.test_cases[0].expected_assertions[0].contract_id = "C999"
    second = first.model_copy(deep=True)
    second.requirements.reverse()
    second.contracts.reverse()
    second.test_cases.reverse()
    assert (
        validate_benchmark_definition(first).issues == validate_benchmark_definition(second).issues
    )
