"""Pydantic models for the executable Benchmark Definition v0.3 schema.

The module is intentionally separate from :mod:`definition`, which remains the
historical v0.2 schema. v0.3 replaces executable prose with closed typed
policies while retaining the descriptive portions of the Definition contract.
"""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, model_validator

from .common import (
    BenchmarkId,
    GateSpecificationId,
    MetricSpecificationId,
    NonEmptyStr,
    ResultSemantic,
    SchemaModel,
    UnitInterval,
    ensure_unique,
)
from .definition import (
    AcceptancePolicy,
    Contract,
    DefinitionResourceBinding,
    DefinitionStatus,
    EvidenceSpecification,
    GateResultSemantics,
    GateTarget,
    GraderSpecification,
    MetricAvailabilityGateCondition,
    MetricInput,
    MetricResultSemantics,
    MetricThresholdGateCondition,
    OverallScorePolicy,
    Requirement,
    TestCase,
)


class AttemptSelectionMode(StrEnum):
    ALL_DISTINCT = "all_distinct"
    SOLE_DISTINCT = "sole_distinct"
    FIRST_DISTINCT = "first_distinct"
    FINAL_DISTINCT_RAW = "final_distinct_raw"


class AttemptOrdering(StrEnum):
    ATTEMPT_INDEX_ASCENDING = "attempt_index_ascending"


class AttemptSelectionPolicy(SchemaModel):
    mode: AttemptSelectionMode
    order: AttemptOrdering | None = None

    @model_validator(mode="after")
    def validate_order_requirement(self) -> "AttemptSelectionPolicy":
        requires_order = self.mode in {
            AttemptSelectionMode.FIRST_DISTINCT,
            AttemptSelectionMode.FINAL_DISTINCT_RAW,
        }
        if requires_order and self.order is None:
            raise ValueError(f"{self.mode.value} requires attempt_index_ascending order")
        return self


class NonSubstantiveHandling(StrEnum):
    EXCLUDE_AND_TRACE = "exclude_and_trace"


class MissingInputHandling(StrEnum):
    UNAVAILABLE = "unavailable"


class EligibilityPolicy(SchemaModel):
    eligible_semantics: Annotated[list[ResultSemantic], Field(min_length=1)]
    non_substantive: NonSubstantiveHandling
    missing_input: MissingInputHandling

    @model_validator(mode="after")
    def validate_semantics(self) -> "EligibilityPolicy":
        ensure_unique(list(self.eligible_semantics), "eligible_semantics")
        return self


class ContributionUnit(StrEnum):
    UNIT_INTERVAL = "unit_interval"


class ContributionRule(SchemaModel):
    source_semantic: ResultSemantic
    numeric_value: UnitInterval
    contribution_unit: ContributionUnit
    explanation: NonEmptyStr


class AggregationUnit(StrEnum):
    PER_TARGET = "per_target"
    PER_CONTRACT = "per_contract"
    PER_TEST_CASE = "per_test_case"


class UnitReductionMode(StrEnum):
    SINGLE = "single"
    MEAN = "mean"
    FINAL_ELIGIBLE = "final_eligible"


class UnitReductionPolicy(SchemaModel):
    mode: UnitReductionMode


class WeightingMode(StrEnum):
    EQUAL_PER_UNIT = "equal_per_unit"


class WeightingPolicy(SchemaModel):
    mode: WeightingMode


class AggregationMode(StrEnum):
    MEAN = "mean"


class AggregationPolicy(SchemaModel):
    mode: AggregationMode


class CompletenessMode(StrEnum):
    STRICT = "strict"


class EmptyDenominatorHandling(StrEnum):
    UNAVAILABLE = "unavailable"


class CompletenessPolicy(SchemaModel):
    mode: CompletenessMode
    empty_denominator: EmptyDenominatorHandling
    # Descriptive only; executors use mode and empty_denominator above.
    transparency_requirements: list[NonEmptyStr] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_transparency_requirements(self) -> "CompletenessPolicy":
        ensure_unique(list(self.transparency_requirements), "transparency_requirements")
        return self


class MetricExecutionPolicy(SchemaModel):
    selection: AttemptSelectionPolicy
    eligibility: EligibilityPolicy
    contribution_mapping: Annotated[list[ContributionRule], Field(min_length=1)]
    aggregation_unit: AggregationUnit
    unit_reduction: UnitReductionPolicy
    weighting: WeightingPolicy
    aggregation: AggregationPolicy
    completeness: CompletenessPolicy

    @model_validator(mode="after")
    def validate_local_policy(self) -> "MetricExecutionPolicy":
        source_semantics = [rule.source_semantic for rule in self.contribution_mapping]
        ensure_unique(source_semantics, "contribution_mapping.source_semantic")

        eligible_semantics = set(self.eligibility.eligible_semantics)
        mapped_semantics = set(source_semantics)
        missing = eligible_semantics - mapped_semantics
        if missing:
            missing_values = ", ".join(sorted(item.value for item in missing))
            raise ValueError(
                f"missing contribution mapping for eligible semantics: {missing_values}"
            )
        unexpected = mapped_semantics - eligible_semantics
        if unexpected:
            unexpected_values = ", ".join(sorted(item.value for item in unexpected))
            raise ValueError(
                f"contribution mapping contains non-eligible semantics: {unexpected_values}"
            )

        if (
            self.unit_reduction.mode == UnitReductionMode.FINAL_ELIGIBLE
            and self.selection.mode != AttemptSelectionMode.ALL_DISTINCT
        ):
            raise ValueError("final_eligible reduction requires all_distinct selection")
        return self


class DirectGraderGatePolicy(SchemaModel):
    selection: AttemptSelectionPolicy
    trigger_result_semantics: Annotated[list[ResultSemantic], Field(min_length=1)]
    quantifier: Literal["any", "all"]

    @model_validator(mode="after")
    def validate_trigger_semantics(self) -> "DirectGraderGatePolicy":
        ensure_unique(list(self.trigger_result_semantics), "trigger_result_semantics")
        return self


class GraderResultGateConditionV03(DirectGraderGatePolicy):
    condition_type: Literal["grader_result_semantic"]
    targets: Annotated[list[GateTarget], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_targets(self) -> "GraderResultGateConditionV03":
        ensure_unique(
            [(target.test_case_id, target.contract_id) for target in self.targets],
            "targets",
        )
        return self


type GateConditionV03 = Annotated[
    GraderResultGateConditionV03 | MetricThresholdGateCondition | MetricAvailabilityGateCondition,
    Field(discriminator="condition_type"),
]


class GateSpecificationV03(SchemaModel):
    gate_id: GateSpecificationId
    name: NonEmptyStr
    scope: NonEmptyStr
    condition: GateConditionV03
    unavailable_handling: Literal["indeterminate", "triggered"]
    result_semantics: GateResultSemantics
    explanation_requirements: Annotated[list[NonEmptyStr], Field(min_length=1)]


class MetricSpecificationV03(SchemaModel):
    metric_id: MetricSpecificationId
    name: NonEmptyStr
    inputs: Annotated[list[MetricInput], Field(min_length=1)]
    execution_policy: MetricExecutionPolicy
    result_semantics: MetricResultSemantics

    @model_validator(mode="after")
    def validate_inputs(self) -> "MetricSpecificationV03":
        ensure_unique(
            [(item.test_case_id, item.contract_id) for item in self.inputs],
            "inputs",
        )
        return self


class BenchmarkDefinitionV03(SchemaModel):
    """Explicit v0.3 root; it never accepts the v0.2 free-text policy fields."""

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
    metric_specifications: Annotated[list[MetricSpecificationV03], Field(min_length=1)]
    gate_specifications: list[GateSpecificationV03]
    overall_score_policy: OverallScorePolicy
    acceptance_policy: AcceptancePolicy
    semantic_resource_bindings: list[DefinitionResourceBinding]


# Convenient unsuffixed names for callers that import this explicit versioned module.
MetricSpecification = MetricSpecificationV03
GraderResultGateCondition = GraderResultGateConditionV03
GateCondition = GateConditionV03
BenchmarkDefinition = BenchmarkDefinitionV03


__all__ = [
    "AggregationMode",
    "AggregationUnit",
    "AggregationPolicy",
    "AttemptOrdering",
    "AttemptSelectionMode",
    "AttemptSelectionPolicy",
    "BenchmarkDefinition",
    "BenchmarkDefinitionV03",
    "CompletenessMode",
    "CompletenessPolicy",
    "ContributionRule",
    "ContributionUnit",
    "DirectGraderGatePolicy",
    "EligibilityPolicy",
    "EmptyDenominatorHandling",
    "GateCondition",
    "GateConditionV03",
    "GateSpecificationV03",
    "GraderResultGateCondition",
    "GraderResultGateConditionV03",
    "MetricExecutionPolicy",
    "MetricSpecification",
    "MetricSpecificationV03",
    "MissingInputHandling",
    "NonSubstantiveHandling",
    "ResultSemantic",
    "UnitReductionMode",
    "UnitReductionPolicy",
    "WeightingMode",
    "WeightingPolicy",
]
