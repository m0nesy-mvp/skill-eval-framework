"""Pydantic mappings for frozen Result and Scorecard schemas."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, model_validator

from .common import (
    ContractId,
    Digest,
    FiniteDecimal,
    GateSpecificationId,
    GraderSpecificationId,
    MetricSpecificationId,
    NonEmptyStr,
    NonNegativeInt,
    PositiveInt,
    SchemaModel,
    TestCaseId,
    UnitInterval,
    ensure_unique,
)
from .runtime import EvidenceTargetRef, FrozenDefinitionRef, SubjectReference


class GraderJudgment(StrEnum):
    SATISFIED = "satisfied"
    VIOLATED = "violated"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    NOT_EXERCISED = "not_exercised"


class EvidenceContribution(SchemaModel):
    evidence_id: NonEmptyStr
    contribution: NonEmptyStr


class GraderExplanation(SchemaModel):
    evidence_contributions: list[EvidenceContribution]
    observed_facts: list[NonEmptyStr]
    semantic_basis: NonEmptyStr
    supported_failure_criterion: NonEmptyStr | None = None
    supported_failure_mode: NonEmptyStr | None = None
    insufficiency_gaps: list[NonEmptyStr]
    inference_notes: list[NonEmptyStr]


class RubricDimensionResult(SchemaModel):
    dimension_name: NonEmptyStr
    selected_anchor_label: NonEmptyStr | None = None
    local_value: FiniteDecimal | None = None
    explanation: NonEmptyStr


class RubricResult(SchemaModel):
    dimensions: list[RubricDimensionResult]
    overall_interpretation: NonEmptyStr | None = None


class GraderResult(SchemaModel):
    grader_result_id: NonEmptyStr
    run_id: NonEmptyStr
    episode_id: NonEmptyStr
    grader_id: GraderSpecificationId
    test_case_id: TestCaseId
    contract_id: ContractId
    evidence_ids: list[NonEmptyStr]
    judgment: GraderJudgment
    explanation: GraderExplanation
    rubric_result: RubricResult | None = None
    created_at: datetime

    @property
    def logical_key(self) -> tuple[str, str, GraderSpecificationId, TestCaseId, ContractId]:
        return (
            self.run_id,
            self.episode_id,
            self.grader_id,
            self.test_case_id,
            self.contract_id,
        )

    @model_validator(mode="after")
    def validate_judgment_explanation(self) -> "GraderResult":
        ensure_unique(list(self.evidence_ids), "evidence_ids")
        if self.judgment == GraderJudgment.VIOLATED:
            if self.explanation.supported_failure_criterion is None:
                raise ValueError("violated judgment requires supported_failure_criterion")
        elif (
            self.judgment in {GraderJudgment.SATISFIED, GraderJudgment.NOT_EXERCISED}
            and self.explanation.supported_failure_criterion is not None
        ):
            raise ValueError(
                "satisfied and not_exercised must not include supported_failure_criterion"
            )
        if (
            self.judgment == GraderJudgment.INSUFFICIENT_EVIDENCE
            and not self.explanation.insufficiency_gaps
        ):
            raise ValueError("insufficient_evidence requires insufficiency_gaps")
        return self


class MetricResultStatus(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class MetricValueKind(StrEnum):
    RATE = "rate"
    COUNT = "count"
    SCALAR = "scalar"


class MetricValue(SchemaModel):
    value_kind: MetricValueKind
    canonical_value: FiniteDecimal
    unit: NonEmptyStr | None = None
    display_value: NonEmptyStr | None = None


class MetricCoverageSummary(SchemaModel):
    expected_input_count: NonNegativeInt
    available_raw_result_count: NonNegativeInt
    distinct_result_count: NonNegativeInt
    selected_result_count: NonNegativeInt
    substantive_eligible_count: NonNegativeInt
    not_exercised_count: NonNegativeInt
    insufficient_evidence_count: NonNegativeInt
    unavailable_input_count: NonNegativeInt
    declared_aggregation_unit: NonEmptyStr
    contributing_unit_count: NonNegativeInt
    denominator: FiniteDecimal | None = None
    coverage_ratio: UnitInterval | None = None


class MetricInputDisposition(StrEnum):
    INCLUDED = "included"
    EXCLUDED = "excluded"


class MetricInputTrace(SchemaModel):
    grader_result_id: NonEmptyStr
    disposition: MetricInputDisposition
    reason: NonEmptyStr
    aggregation_unit_key: NonEmptyStr | None = None
    contribution_value: FiniteDecimal | None = None


class MissingMetricInput(SchemaModel):
    test_case_id: TestCaseId
    contract_id: ContractId
    reason: NonEmptyStr


class MetricUnavailableReason(StrEnum):
    EMPTY_DENOMINATOR = "empty_denominator"
    COMPLETENESS_FAILED = "completeness_failed"
    REQUIRED_INPUTS_MISSING = "required_inputs_missing"
    INCOMPATIBLE_INPUT_VALUES = "incompatible_input_values"


class MetricResult(SchemaModel):
    metric_result_id: NonEmptyStr
    run_id: NonEmptyStr
    metric_id: MetricSpecificationId
    status: MetricResultStatus
    value: MetricValue | None = None
    unavailable_reason: MetricUnavailableReason | None = None
    unavailable_explanation: NonEmptyStr | None = None
    coverage: MetricCoverageSummary
    input_traces: list[MetricInputTrace]
    missing_inputs: list[MissingMetricInput]
    created_at: datetime

    @property
    def logical_key(self) -> tuple[str, MetricSpecificationId]:
        return (self.run_id, self.metric_id)

    @model_validator(mode="after")
    def validate_availability(self) -> "MetricResult":
        ensure_unique([item.grader_result_id for item in self.input_traces], "input_traces")
        ensure_unique(
            [(item.test_case_id, item.contract_id) for item in self.missing_inputs],
            "missing_inputs",
        )
        if self.status == MetricResultStatus.AVAILABLE:
            if self.value is None:
                raise ValueError("available MetricResult requires value")
            if self.unavailable_reason is not None or self.unavailable_explanation is not None:
                raise ValueError("available MetricResult must not include unavailable fields")
        else:
            if self.value is not None:
                raise ValueError("unavailable MetricResult must not include value")
            if self.unavailable_reason is None or self.unavailable_explanation is None:
                raise ValueError("unavailable MetricResult requires reason and explanation")
        return self


class GateSemantic(StrEnum):
    OPEN = "OPEN"
    TRIGGERED = "TRIGGERED"
    INDETERMINATE = "INDETERMINATE"


class GateEvaluationPath(StrEnum):
    CONDITION_TRUE = "condition_true"
    CONDITION_FALSE = "condition_false"
    UNKNOWN_INDETERMINATE = "unknown_indeterminate"
    UNKNOWN_TRIGGERED = "unknown_triggered"


class GateTriggerSource(StrEnum):
    CONDITION = "condition"
    UNAVAILABLE_HANDLING = "unavailable_handling"


class GateGraderContribution(SchemaModel):
    grader_result_id: NonEmptyStr | None = None
    target: EvidenceTargetRef
    contribution: Literal["MATCH", "NON_MATCH", "UNKNOWN"]
    detail: NonEmptyStr


class GateInputSummary(SchemaModel):
    condition_type: Literal["grader_result", "metric_threshold", "metric_availability"]
    grader_contributions: list[GateGraderContribution]
    metric_result_id: NonEmptyStr | None = None
    metric_input_state: Literal["available", "unavailable", "missing", "not_applicable"]
    observed_canonical_value: FiniteDecimal | None = None
    comparator_outcome: Literal["true", "false", "unknown", "not_applicable"]
    quantifier: Literal["any", "all", "not_applicable"]
    condition_outcome: Literal["true", "false", "unknown"]

    @model_validator(mode="after")
    def validate_condition_shape(self) -> "GateInputSummary":
        if self.condition_type == "grader_result":
            if self.metric_result_id is not None or self.observed_canonical_value is not None:
                raise ValueError("grader_result summary must not include Metric fields")
            if self.metric_input_state != "not_applicable":
                raise ValueError("grader_result summary requires not_applicable Metric state")
            if self.comparator_outcome != "not_applicable":
                raise ValueError("grader_result summary requires not_applicable comparator")
            if self.quantifier == "not_applicable":
                raise ValueError("grader_result summary requires any or all quantifier")
        else:
            if self.grader_contributions:
                raise ValueError("Metric Gate summary must not include grader contributions")
            if self.quantifier != "not_applicable":
                raise ValueError("Metric Gate summary requires not_applicable quantifier")
            if self.metric_input_state == "not_applicable":
                raise ValueError("Metric Gate summary requires a Metric input state")
            if self.metric_input_state == "missing" and self.metric_result_id is not None:
                raise ValueError("missing Metric input must not include metric_result_id")
            if self.metric_input_state != "missing" and self.metric_result_id is None:
                raise ValueError("existing Metric input requires metric_result_id")
            if self.metric_input_state != "available" and self.observed_canonical_value is not None:
                raise ValueError("only available Metric input may include canonical value")
        return self


class GateResult(SchemaModel):
    gate_result_id: NonEmptyStr
    run_id: NonEmptyStr
    gate_id: GateSpecificationId
    result: GateSemantic
    evaluation_path: GateEvaluationPath
    trigger_source: GateTriggerSource | None = None
    input_summary: GateInputSummary
    explanation: NonEmptyStr
    created_at: datetime

    @property
    def logical_key(self) -> tuple[str, GateSpecificationId]:
        return (self.run_id, self.gate_id)

    @model_validator(mode="after")
    def validate_evaluation_mapping(self) -> "GateResult":
        expected = {
            GateEvaluationPath.CONDITION_TRUE: (
                GateSemantic.TRIGGERED,
                GateTriggerSource.CONDITION,
            ),
            GateEvaluationPath.CONDITION_FALSE: (GateSemantic.OPEN, None),
            GateEvaluationPath.UNKNOWN_INDETERMINATE: (GateSemantic.INDETERMINATE, None),
            GateEvaluationPath.UNKNOWN_TRIGGERED: (
                GateSemantic.TRIGGERED,
                GateTriggerSource.UNAVAILABLE_HANDLING,
            ),
        }[self.evaluation_path]
        if (self.result, self.trigger_source) != expected:
            raise ValueError("Gate result, evaluation_path, and trigger_source are inconsistent")
        expected_outcome = {
            GateEvaluationPath.CONDITION_TRUE: "true",
            GateEvaluationPath.CONDITION_FALSE: "false",
            GateEvaluationPath.UNKNOWN_INDETERMINATE: "unknown",
            GateEvaluationPath.UNKNOWN_TRIGGERED: "unknown",
        }[self.evaluation_path]
        if self.input_summary.condition_outcome != expected_outcome:
            raise ValueError("input_summary condition outcome does not match evaluation_path")
        return self


class ExpectedEpisodeApplicationRef(SchemaModel):
    application_type: Literal["episode"]
    test_case_id: TestCaseId
    attempt_index: PositiveInt

    @property
    def logical_key(self) -> tuple[str, TestCaseId, int]:
        return (self.application_type, self.test_case_id, self.attempt_index)


class ExpectedGraderApplicationRef(SchemaModel):
    application_type: Literal["grader_result"]
    episode_id: NonEmptyStr
    grader_id: GraderSpecificationId
    test_case_id: TestCaseId
    contract_id: ContractId

    @property
    def logical_key(self) -> tuple[str, str, GraderSpecificationId, TestCaseId, ContractId]:
        return (
            self.application_type,
            self.episode_id,
            self.grader_id,
            self.test_case_id,
            self.contract_id,
        )


class ExpectedMetricApplicationRef(SchemaModel):
    application_type: Literal["metric_result"]
    metric_id: MetricSpecificationId

    @property
    def logical_key(self) -> tuple[str, MetricSpecificationId]:
        return (self.application_type, self.metric_id)


class ExpectedGateApplicationRef(SchemaModel):
    application_type: Literal["gate_result"]
    gate_id: GateSpecificationId

    @property
    def logical_key(self) -> tuple[str, GateSpecificationId]:
        return (self.application_type, self.gate_id)


type ExpectedApplicationRef = Annotated[
    ExpectedEpisodeApplicationRef
    | ExpectedGraderApplicationRef
    | ExpectedMetricApplicationRef
    | ExpectedGateApplicationRef,
    Field(discriminator="application_type"),
]


class MissingApplicationRecord(SchemaModel):
    application_ref: ExpectedApplicationRef
    diagnostic_ids: list[NonEmptyStr]
    explanation: NonEmptyStr


class ScorecardResultInventory(SchemaModel):
    episode_ids: list[NonEmptyStr]
    grader_result_ids: list[NonEmptyStr]
    metric_result_ids: list[NonEmptyStr]
    gate_result_ids: list[NonEmptyStr]
    missing_applications: list[MissingApplicationRecord]

    @model_validator(mode="after")
    def validate_local_uniqueness(self) -> "ScorecardResultInventory":
        ensure_unique(list(self.episode_ids), "episode_ids")
        ensure_unique(list(self.grader_result_ids), "grader_result_ids")
        ensure_unique(list(self.metric_result_ids), "metric_result_ids")
        ensure_unique(list(self.gate_result_ids), "gate_result_ids")
        ensure_unique(
            [item.application_ref.logical_key for item in self.missing_applications],
            "missing_applications",
        )
        return self


class DefinitionPolicyRef(SchemaModel):
    definition_digest: Digest
    policy_path: Literal["/overall_score_policy", "/acceptance_policy"]


class OverallEvaluationStatus(StrEnum):
    DISABLED = "disabled"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    NOT_PRODUCED_RUN_PENDING = "not_produced_run_pending"
    NOT_PRODUCED_RUN_INVALID = "not_produced_run_invalid"
    PRODUCTION_FAILED = "production_failed"


class OverallUnavailableReason(StrEnum):
    PARTICIPATING_METRIC_UNAVAILABLE = "participating_metric_unavailable"
    PARTICIPATING_METRIC_MISSING = "participating_metric_missing"
    AVAILABLE_WEIGHT_BELOW_MINIMUM = "available_weight_below_minimum"
    EMPTY_INCLUDED_SET = "empty_included_set"


class OverallMetricContributionTrace(SchemaModel):
    metric_id: MetricSpecificationId
    weight: FiniteDecimal
    metric_result_id: NonEmptyStr | None = None
    application_state: Literal["available", "unavailable", "missing"]
    policy_handling: Literal["included", "overall_unavailable", "exclude_and_renormalize"]
    normalized_value: FiniteDecimal | None = None
    weighted_contribution: FiniteDecimal | None = None
    exclusion_reason: NonEmptyStr | None = None


class OverallScoreOutcome(SchemaModel):
    policy_ref: DefinitionPolicyRef
    evaluation_status: OverallEvaluationStatus
    canonical_value: FiniteDecimal | None = None
    contribution_traces: list[OverallMetricContributionTrace]
    total_selected_weight: FiniteDecimal | None = None
    available_weight: FiniteDecimal | None = None
    available_weight_fraction: UnitInterval | None = None
    minimum_required_weight_fraction: UnitInterval | None = None
    final_included_denominator: FiniteDecimal | None = None
    unavailable_reason: OverallUnavailableReason | None = None
    diagnostic_ids: list[NonEmptyStr]
    explanation: NonEmptyStr

    @model_validator(mode="after")
    def validate_status_shape(self) -> "OverallScoreOutcome":
        ensure_unique(list(self.diagnostic_ids), "diagnostic_ids")
        weight_values = (
            self.total_selected_weight,
            self.available_weight,
            self.available_weight_fraction,
            self.minimum_required_weight_fraction,
            self.final_included_denominator,
        )
        if self.evaluation_status == OverallEvaluationStatus.AVAILABLE:
            if self.canonical_value is None or not self.contribution_traces:
                raise ValueError("available Overall requires value and contribution traces")
            if any(value is None for value in weight_values):
                raise ValueError("available Overall requires all weight fields")
            if self.unavailable_reason is not None:
                raise ValueError("available Overall must not include unavailable_reason")
        elif self.evaluation_status == OverallEvaluationStatus.UNAVAILABLE:
            if self.canonical_value is not None:
                raise ValueError("unavailable Overall must not include canonical_value")
            if self.unavailable_reason is None or not self.contribution_traces:
                raise ValueError("unavailable Overall requires reason and contribution traces")
            if any(value is None for value in weight_values):
                raise ValueError("unavailable Overall requires all coverage and weight fields")
        elif self.evaluation_status == OverallEvaluationStatus.DISABLED:
            if self.canonical_value is not None or self.unavailable_reason is not None:
                raise ValueError("non-semantic Overall status must not include value or reason")
            if self.contribution_traces or any(value is not None for value in weight_values):
                raise ValueError("disabled Overall must not include calculation fields")
        else:
            if self.canonical_value is not None or self.unavailable_reason is not None:
                raise ValueError("non-semantic Overall status must not include value or reason")
            if self.evaluation_status == OverallEvaluationStatus.PRODUCTION_FAILED:
                if not self.diagnostic_ids:
                    raise ValueError("production_failed Overall requires diagnostic_ids")
        return self


class AcceptanceEvaluationStatus(StrEnum):
    DISABLED = "disabled"
    PRODUCED = "produced"
    NOT_PRODUCED_RUN_PENDING = "not_produced_run_pending"
    NOT_PRODUCED_RUN_INVALID = "not_produced_run_invalid"
    PRODUCTION_FAILED = "production_failed"


class AcceptanceSemantic(StrEnum):
    ACCEPTABLE = "ACCEPTABLE"
    BLOCKED = "BLOCKED"
    INDETERMINATE = "INDETERMINATE"


class AcceptanceGateContributionTrace(SchemaModel):
    gate_id: GateSpecificationId
    gate_result_id: NonEmptyStr | None = None
    application_state: Literal["OPEN", "TRIGGERED", "INDETERMINATE", "MISSING"]
    policy_handling: Literal["open", "actual_triggered", "overall_indeterminate", "overall_blocked"]
    propagation_outcome: Literal["no_block", "blocked", "indeterminate"]
    explanation: NonEmptyStr


class AcceptanceEvaluation(SchemaModel):
    policy_ref: DefinitionPolicyRef
    evaluation_status: AcceptanceEvaluationStatus
    acceptance: AcceptanceSemantic | None = None
    gate_contributions: list[AcceptanceGateContributionTrace]
    diagnostic_ids: list[NonEmptyStr]
    explanation: NonEmptyStr

    @model_validator(mode="after")
    def validate_status_shape(self) -> "AcceptanceEvaluation":
        ensure_unique(list(self.diagnostic_ids), "diagnostic_ids")
        if self.evaluation_status == AcceptanceEvaluationStatus.PRODUCED:
            if self.acceptance is None or not self.gate_contributions:
                raise ValueError("produced Acceptance requires semantic and gate contributions")
        elif self.evaluation_status == AcceptanceEvaluationStatus.DISABLED:
            if self.acceptance is not None:
                raise ValueError("only produced Acceptance may include acceptance semantic")
            if self.gate_contributions:
                raise ValueError("disabled Acceptance must not include gate contributions")
        else:
            if self.acceptance is not None:
                raise ValueError("only produced Acceptance may include acceptance semantic")
            if (
                self.evaluation_status == AcceptanceEvaluationStatus.PRODUCTION_FAILED
                and not self.diagnostic_ids
            ):
                raise ValueError("production_failed Acceptance requires diagnostic_ids")
        return self


class ScorecardFinalizationStatus(StrEnum):
    INTERIM = "interim"
    FINALIZED_EVALUATION = "finalized_evaluation"
    FINALIZED_AUDIT = "finalized_audit"


class Scorecard(SchemaModel):
    scorecard_id: NonEmptyStr
    run_id: NonEmptyStr
    definition_ref: FrozenDefinitionRef
    subject_ref: SubjectReference
    result_inventory: ScorecardResultInventory
    diagnostic_ids: list[NonEmptyStr]
    overall_score_outcome: OverallScoreOutcome
    acceptance_evaluation: AcceptanceEvaluation
    finalization_status: ScorecardFinalizationStatus
    finalized_at: datetime | None = None

    @property
    def logical_key(self) -> str:
        return self.run_id

    @model_validator(mode="after")
    def validate_finalization_timestamp(self) -> "Scorecard":
        ensure_unique(list(self.diagnostic_ids), "diagnostic_ids")
        finalized = self.finalization_status != ScorecardFinalizationStatus.INTERIM
        if finalized and self.finalized_at is None:
            raise ValueError("finalized Scorecard requires finalized_at")
        if not finalized and self.finalized_at is not None:
            raise ValueError("interim Scorecard must not include finalized_at")
        return self
