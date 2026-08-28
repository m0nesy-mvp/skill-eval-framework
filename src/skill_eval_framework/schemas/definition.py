"""Pydantic mappings for frozen Benchmark Definition schemas."""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, model_validator

from .common import (
    BenchmarkId,
    CanonicalPrecision,
    ContractId,
    Digest,
    EvidenceSpecificationId,
    FiniteDecimal,
    GateSpecificationId,
    GraderSpecificationId,
    MetricSpecificationId,
    NonEmptyStr,
    PositiveDecimal,
    RequirementId,
    SchemaModel,
    TestCaseId,
    UnitFraction,
    ensure_unique,
)


class DefinitionStatus(StrEnum):
    DRAFT = "draft"
    FROZEN = "frozen"


class RequirementSource(StrEnum):
    SKILL = "skill"
    USER = "user"
    PROJECT = "project"
    INTERFACE = "interface"
    OTHER = "other"


class EvaluationType(StrEnum):
    OUTCOME = "outcome"
    WORKFLOW = "workflow"


class ContractCriticality(StrEnum):
    NORMAL = "normal"
    CRITICAL = "critical"


class Requirement(SchemaModel):
    requirement_id: RequirementId
    statement: NonEmptyStr
    source: RequirementSource
    source_ref: NonEmptyStr | None = None
    evaluation_type: EvaluationType


class Contract(SchemaModel):
    contract_id: ContractId
    requirement_ids: Annotated[list[RequirementId], Field(min_length=1)]
    statement: NonEmptyStr
    evaluation_type: EvaluationType
    criticality: ContractCriticality
    success_criteria: Annotated[list[NonEmptyStr], Field(min_length=1)]
    failure_criteria: Annotated[list[NonEmptyStr], Field(min_length=1)]
    failure_modes: Annotated[list[NonEmptyStr], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_local_lists(self) -> "Contract":
        ensure_unique(list(self.requirement_ids), "requirement_ids")
        ensure_unique(list(self.success_criteria), "success_criteria")
        ensure_unique(list(self.failure_criteria), "failure_criteria")
        ensure_unique(list(self.failure_modes), "failure_modes")
        return self


class InteractionStep(SchemaModel):
    trigger: NonEmptyStr
    response: NonEmptyStr


class ExpectedAssertion(SchemaModel):
    contract_id: ContractId
    expectation: NonEmptyStr


class TestCase(SchemaModel):
    test_case_id: TestCaseId
    task: NonEmptyStr
    preconditions: list[NonEmptyStr]
    fixtures: list[NonEmptyStr]
    initial_state: list[NonEmptyStr]
    interaction_steps: list[InteractionStep]
    expected_assertions: Annotated[list[ExpectedAssertion], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_local_lists(self) -> "TestCase":
        ensure_unique(list(self.preconditions), "preconditions")
        ensure_unique(list(self.fixtures), "fixtures")
        ensure_unique(list(self.initial_state), "initial_state")
        assertion_contracts = [item.contract_id for item in self.expected_assertions]
        ensure_unique(assertion_contracts, "expected_assertions.contract_id")
        return self


class EvidenceTarget(SchemaModel):
    test_case_id: TestCaseId
    contract_id: ContractId


class EvidenceSpecification(SchemaModel):
    evidence_spec_id: EvidenceSpecificationId
    targets: Annotated[list[EvidenceTarget], Field(min_length=1)]
    observation_requirements: Annotated[list[NonEmptyStr], Field(min_length=1)]
    provenance_requirements: Annotated[list[NonEmptyStr], Field(min_length=1)]
    context_requirements: list[NonEmptyStr]
    qualification_requirements: Annotated[list[NonEmptyStr], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_local_lists(self) -> "EvidenceSpecification":
        ensure_unique(
            [(target.test_case_id, target.contract_id) for target in self.targets],
            "targets",
        )
        ensure_unique(list(self.observation_requirements), "observation_requirements")
        ensure_unique(list(self.provenance_requirements), "provenance_requirements")
        ensure_unique(list(self.context_requirements), "context_requirements")
        ensure_unique(list(self.qualification_requirements), "qualification_requirements")
        return self


class GraderTarget(SchemaModel):
    test_case_id: TestCaseId
    contract_id: ContractId
    evidence_spec_ids: Annotated[list[EvidenceSpecificationId], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_evidence_spec_ids(self) -> "GraderTarget":
        ensure_unique(list(self.evidence_spec_ids), "evidence_spec_ids")
        return self


class GraderResultSemantics(SchemaModel):
    satisfied: NonEmptyStr
    violated: NonEmptyStr
    insufficient_evidence: NonEmptyStr
    not_exercised: NonEmptyStr | None = None


class RubricAnchor(SchemaModel):
    label: NonEmptyStr
    meaning: NonEmptyStr


class RubricDimension(SchemaModel):
    name: NonEmptyStr
    criterion: NonEmptyStr
    anchors: Annotated[list[RubricAnchor], Field(min_length=2)]

    @model_validator(mode="after")
    def validate_anchor_labels(self) -> "RubricDimension":
        ensure_unique([anchor.label for anchor in self.anchors], "anchors.label")
        return self


class Rubric(SchemaModel):
    dimensions: Annotated[list[RubricDimension], Field(min_length=1)]
    overall_interpretation: NonEmptyStr

    @model_validator(mode="after")
    def validate_dimension_names(self) -> "Rubric":
        ensure_unique([dimension.name for dimension in self.dimensions], "dimensions.name")
        return self


class GraderSpecification(SchemaModel):
    grader_id: GraderSpecificationId
    targets: Annotated[list[GraderTarget], Field(min_length=1)]
    judgment_criteria: Annotated[list[NonEmptyStr], Field(min_length=1)]
    result_semantics: GraderResultSemantics
    insufficiency_handling: Annotated[list[NonEmptyStr], Field(min_length=1)]
    explanation_requirements: Annotated[list[NonEmptyStr], Field(min_length=1)]
    rubric: Rubric | None = None

    @model_validator(mode="after")
    def validate_local_lists(self) -> "GraderSpecification":
        ensure_unique(
            [(target.test_case_id, target.contract_id) for target in self.targets],
            "targets",
        )
        ensure_unique(list(self.judgment_criteria), "judgment_criteria")
        ensure_unique(list(self.insufficiency_handling), "insufficiency_handling")
        ensure_unique(list(self.explanation_requirements), "explanation_requirements")
        return self


class MetricInput(SchemaModel):
    test_case_id: TestCaseId
    contract_id: ContractId


class MetricEligibilityPolicy(SchemaModel):
    eligible_result_semantics: Annotated[list[NonEmptyStr], Field(min_length=1)]
    non_substantive_handling: Annotated[list[NonEmptyStr], Field(min_length=1)]
    unavailable_input_handling: Annotated[list[NonEmptyStr], Field(min_length=1)]


class MetricContributionRule(SchemaModel):
    source_semantics: NonEmptyStr
    contribution_semantics: NonEmptyStr


class MetricCompletenessPolicy(SchemaModel):
    minimum_input_requirement: NonEmptyStr
    partial_result_policy: NonEmptyStr
    empty_denominator_policy: NonEmptyStr
    transparency_requirements: Annotated[list[NonEmptyStr], Field(min_length=1)]


class MetricResultSemantics(SchemaModel):
    interpretation: NonEmptyStr
    direction: NonEmptyStr
    scale: NonEmptyStr
    denominator_meaning: NonEmptyStr


class MetricSpecification(SchemaModel):
    metric_id: MetricSpecificationId
    name: NonEmptyStr
    inputs: Annotated[list[MetricInput], Field(min_length=1)]
    result_selection_policy: NonEmptyStr
    aggregation_unit: NonEmptyStr
    eligibility_policy: MetricEligibilityPolicy
    contribution_mapping: Annotated[list[MetricContributionRule], Field(min_length=1)]
    unit_reduction: NonEmptyStr
    aggregation_rule: NonEmptyStr
    weighting_policy: NonEmptyStr
    completeness_policy: MetricCompletenessPolicy
    result_semantics: MetricResultSemantics

    @model_validator(mode="after")
    def validate_local_population(self) -> "MetricSpecification":
        ensure_unique(
            [(item.test_case_id, item.contract_id) for item in self.inputs],
            "inputs",
        )
        ensure_unique(
            [item.source_semantics for item in self.contribution_mapping],
            "contribution_mapping.source_semantics",
        )
        return self


class GateTarget(SchemaModel):
    test_case_id: TestCaseId
    contract_id: ContractId


class GraderResultGateCondition(SchemaModel):
    condition_type: Literal["grader_result_semantic"]
    targets: Annotated[list[GateTarget], Field(min_length=1)]
    result_selection_policy: NonEmptyStr
    trigger_result_semantics: Annotated[list[NonEmptyStr], Field(min_length=1)]
    quantifier: Literal["any", "all"]

    @model_validator(mode="after")
    def validate_local_membership(self) -> "GraderResultGateCondition":
        ensure_unique(
            [(target.test_case_id, target.contract_id) for target in self.targets],
            "targets",
        )
        ensure_unique(list(self.trigger_result_semantics), "trigger_result_semantics")
        return self


class MetricThresholdGateCondition(SchemaModel):
    condition_type: Literal["metric_threshold"]
    metric_id: MetricSpecificationId
    comparator: Literal["lt", "lte", "gt", "gte", "eq", "neq"]
    threshold_value: FiniteDecimal


class MetricAvailabilityGateCondition(SchemaModel):
    condition_type: Literal["metric_availability"]
    metric_id: MetricSpecificationId
    trigger_on: Literal["unavailable"]


type GateCondition = Annotated[
    GraderResultGateCondition | MetricThresholdGateCondition | MetricAvailabilityGateCondition,
    Field(discriminator="condition_type"),
]


class GateResultSemantics(SchemaModel):
    open_meaning: NonEmptyStr
    triggered_meaning: NonEmptyStr
    indeterminate_meaning: NonEmptyStr
    blocking_effect: NonEmptyStr


class GateSpecification(SchemaModel):
    gate_id: GateSpecificationId
    name: NonEmptyStr
    scope: NonEmptyStr
    condition: GateCondition
    unavailable_handling: Literal["indeterminate", "triggered"]
    result_semantics: GateResultSemantics
    explanation_requirements: Annotated[list[NonEmptyStr], Field(min_length=1)]


class IdentityUnitIntervalNormalization(SchemaModel):
    type: Literal["identity_unit_interval"]


class LinearBoundedNormalization(SchemaModel):
    type: Literal["linear_bounded"]
    source_min: FiniteDecimal
    source_max: FiniteDecimal
    direction: Literal["higher_is_better", "lower_is_better"]

    @model_validator(mode="after")
    def validate_bounds(self) -> "LinearBoundedNormalization":
        if self.source_max <= self.source_min:
            raise ValueError("source_max must be greater than source_min")
        return self


type MetricNormalization = Annotated[
    IdentityUnitIntervalNormalization | LinearBoundedNormalization,
    Field(discriminator="type"),
]


class OverallMetricContribution(SchemaModel):
    metric_id: MetricSpecificationId
    weight: PositiveDecimal
    normalization: MetricNormalization
    unavailable_result_handling: Literal["overall_unavailable", "exclude_and_renormalize"]
    missing_result_handling: Literal["overall_unavailable", "exclude_and_renormalize"]


class DisabledOverallScorePolicy(SchemaModel):
    mode: Literal["disabled"]


class WeightedNormalizedMeanOverallScorePolicy(SchemaModel):
    mode: Literal["weighted_normalized_mean"]
    metric_contributions: Annotated[list[OverallMetricContribution], Field(min_length=1)]
    minimum_available_weight_fraction: UnitFraction
    canonical_scale: Literal["unit_interval"]
    canonical_precision: CanonicalPrecision

    @model_validator(mode="after")
    def validate_metric_membership(self) -> "WeightedNormalizedMeanOverallScorePolicy":
        ensure_unique(
            [contribution.metric_id for contribution in self.metric_contributions],
            "metric_contributions.metric_id",
        )
        return self


type OverallScorePolicy = Annotated[
    DisabledOverallScorePolicy | WeightedNormalizedMeanOverallScorePolicy,
    Field(discriminator="mode"),
]


class AcceptanceGateContribution(SchemaModel):
    gate_id: GateSpecificationId
    indeterminate_handling: Literal["overall_indeterminate", "overall_blocked"]
    missing_result_handling: Literal["overall_indeterminate", "overall_blocked"]


class DisabledAcceptancePolicy(SchemaModel):
    mode: Literal["disabled"]


class GateBasedAcceptancePolicy(SchemaModel):
    mode: Literal["gate_based"]
    participating_gates: Annotated[list[AcceptanceGateContribution], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_gate_membership(self) -> "GateBasedAcceptancePolicy":
        ensure_unique(
            [contribution.gate_id for contribution in self.participating_gates],
            "participating_gates.gate_id",
        )
        return self


type AcceptancePolicy = Annotated[
    DisabledAcceptancePolicy | GateBasedAcceptancePolicy,
    Field(discriminator="mode"),
]


class DefinitionResourceBinding(SchemaModel):
    resource_ref: NonEmptyStr
    semantic_role: NonEmptyStr
    content_digest: Digest


class BenchmarkDefinition(SchemaModel):
    benchmark_id: BenchmarkId
    name: NonEmptyStr
    version: NonEmptyStr
    description: NonEmptyStr | None = None
    status: DefinitionStatus
    requirements: Annotated[list[Requirement], Field(min_length=1)]
    contracts: Annotated[list[Contract], Field(min_length=1)]
    test_cases: Annotated[list[TestCase], Field(min_length=1)]
    evidence_specifications: Annotated[list[EvidenceSpecification], Field(min_length=1)]
    grader_specifications: Annotated[list[GraderSpecification], Field(min_length=1)]
    metric_specifications: Annotated[list[MetricSpecification], Field(min_length=1)]
    gate_specifications: list[GateSpecification]
    overall_score_policy: OverallScorePolicy
    acceptance_policy: AcceptancePolicy
    semantic_resource_bindings: list[DefinitionResourceBinding]
