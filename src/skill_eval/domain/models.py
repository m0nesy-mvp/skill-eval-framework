"""Pydantic models for versioned Eval Definitions and design validation."""

from datetime import datetime
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from skill_eval.domain.enums import (
    ComparisonOperator,
    Criticality,
    DeterministicOperation,
    EvidenceKind,
    ExecutionStatus,
    FailureCode,
    FailureDomain,
    GateDecisionStatus,
    GateMetric,
    GateScopeKind,
    GateType,
    GradeOutcome,
    GraderKind,
    RunKind,
    RunStatus,
    TestCaseCategory,
    ValidationSeverity,
)

NonEmptyStr = Annotated[str, Field(min_length=1)]


class DomainModel(BaseModel):
    """Base model that rejects undeclared fields at every public boundary."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class SourceReference(DomainModel):
    source_id: NonEmptyStr
    path: str | None = None
    locator: NonEmptyStr
    content_hash: str | None = None


class SkillRequirement(DomainModel):
    requirement_id: NonEmptyStr
    description: NonEmptyStr
    source_reference: SourceReference
    tags: list[str] = Field(default_factory=list)


class TargetSkillRef(DomainModel):
    skill_id: NonEmptyStr
    version: NonEmptyStr
    content_hash: NonEmptyStr


class EvidenceRequirement(DomainModel):
    kind: EvidenceKind
    minimum_count: int = Field(default=1, ge=1)
    required_fields: list[str] = Field(default_factory=list)


class SkillContract(DomainModel):
    contract_id: NonEmptyStr
    requirement_ids: list[NonEmptyStr] = Field(min_length=1)
    category: NonEmptyStr
    description: NonEmptyStr
    preconditions: list[str] = Field(default_factory=list)
    trigger: NonEmptyStr
    expected_behavior: list[NonEmptyStr] = Field(default_factory=list)
    forbidden_behavior: list[NonEmptyStr] = Field(default_factory=list)
    criticality: Criticality
    required_evidence: list[EvidenceRequirement] = Field(default_factory=list)
    source_references: list[SourceReference] = Field(min_length=1)

    @model_validator(mode="after")
    def require_observable_behavior(self) -> "SkillContract":
        if not self.expected_behavior and not self.forbidden_behavior:
            raise ValueError("a contract must define expected_behavior or forbidden_behavior")
        return self


class ContractTable(DomainModel):
    table_id: NonEmptyStr
    version: NonEmptyStr
    target_skill: TargetSkillRef
    requirements: list[SkillRequirement] = Field(min_length=1)
    contracts: list[SkillContract] = Field(min_length=1)


class EnvironmentRequirement(DomainModel):
    name: NonEmptyStr
    description: NonEmptyStr
    required: bool = True


class ExpectedAssertion(DomainModel):
    expected_id: NonEmptyStr
    contract_ids: list[NonEmptyStr] = Field(min_length=1)
    description: NonEmptyStr
    grader_ids: list[NonEmptyStr] = Field(min_length=1)
    rubric_id: str | None = None


class TestCase(DomainModel):
    case_id: NonEmptyStr
    contract_ids: list[NonEmptyStr] = Field(min_length=1)
    category: TestCaseCategory
    description: NonEmptyStr
    preconditions: list[str] = Field(default_factory=list)
    input: JsonValue
    expected: list[ExpectedAssertion] = Field(min_length=1)
    criticality: Criticality
    environment_requirements: list[EnvironmentRequirement] = Field(default_factory=list)


class GraderSpec(DomainModel):
    grader_id: NonEmptyStr
    version: NonEmptyStr
    kind: GraderKind
    operation: DeterministicOperation
    evidence_kind: EvidenceKind
    config: dict[str, JsonValue] = Field(default_factory=dict)


class RubricLevel(DomainModel):
    passed: bool
    score: float
    label: NonEmptyStr
    description: NonEmptyStr


class Rubric(DomainModel):
    rubric_id: NonEmptyStr
    version: NonEmptyStr
    minimum_score: float
    maximum_score: float
    levels: list[RubricLevel] = Field(min_length=2)

    @model_validator(mode="after")
    def validate_binary_mapping(self) -> "Rubric":
        if self.maximum_score <= self.minimum_score:
            raise ValueError("maximum_score must be greater than minimum_score")
        if {level.passed for level in self.levels} != {True, False}:
            raise ValueError("rubric levels must map both passed=true and passed=false")
        if any(
            level.score < self.minimum_score or level.score > self.maximum_score
            for level in self.levels
        ):
            raise ValueError("rubric level score is outside the declared range")
        return self


class GateScope(DomainModel):
    kind: GateScopeKind = GateScopeKind.RUN
    ids: list[NonEmptyStr] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_ids(self) -> "GateScope":
        if self.kind is GateScopeKind.RUN and self.ids:
            raise ValueError("run scope must not declare ids")
        if self.kind is not GateScopeKind.RUN and not self.ids:
            raise ValueError("case and contract scopes must declare ids")
        return self


class GateSpec(DomainModel):
    gate_id: NonEmptyStr
    gate_type: GateType
    metric: GateMetric
    operator: ComparisonOperator
    threshold: bool | float
    scope: GateScope
    description: NonEmptyStr


class CoveragePolicy(DomainModel):
    minimum_cases_by_criticality: dict[Criticality, int]
    required_categories_by_criticality: dict[Criticality, set[TestCaseCategory]] = Field(
        default_factory=dict
    )
    forbidden_behaviors_require_negative_case: bool = True


class EvalDefinition(DomainModel):
    schema_version: NonEmptyStr
    eval_id: NonEmptyStr
    eval_version: NonEmptyStr
    contract_table: ContractTable
    test_cases: list[TestCase] = Field(min_length=1)
    graders: list[GraderSpec] = Field(min_length=1)
    rubrics: list[Rubric] = Field(default_factory=list)
    gates: list[GateSpec] = Field(min_length=1)
    coverage_policy: CoveragePolicy


class ValidationFinding(DomainModel):
    severity: ValidationSeverity
    code: NonEmptyStr
    message: NonEmptyStr
    object_refs: list[str] = Field(default_factory=list)


class ValidationReport(DomainModel):
    findings: list[ValidationFinding] = Field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not any(item.severity is ValidationSeverity.ERROR for item in self.findings)


class FailureRecord(DomainModel):
    failure_id: NonEmptyStr
    domain: FailureDomain
    code: FailureCode
    message: NonEmptyStr
    case_id: str | None = None
    grader_id: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    retryable: bool = False
    details: dict[str, JsonValue] = Field(default_factory=dict)


class Evidence(DomainModel):
    evidence_id: NonEmptyStr
    kind: EvidenceKind
    source: NonEmptyStr
    media_type: NonEmptyStr
    uri: str | None = None
    data: JsonValue | None = None
    sha256: str | None = None
    captured_at: datetime | None = None
    metadata: dict[str, JsonValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_payload(self) -> "Evidence":
        if self.uri is None and self.data is None:
            raise ValueError("evidence must contain data or a uri")
        return self


class ExecutionResult(DomainModel):
    execution_id: NonEmptyStr
    case_id: NonEmptyStr
    status: ExecutionStatus
    started_at: datetime
    finished_at: datetime
    output: JsonValue | None = None
    observation_refs: list[str] = Field(default_factory=list)
    error: FailureRecord | None = None
    metadata: dict[str, JsonValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_error_state(self) -> "ExecutionResult":
        if self.finished_at < self.started_at:
            raise ValueError("finished_at cannot be before started_at")
        if self.status is ExecutionStatus.COMPLETED and self.error is not None:
            raise ValueError("completed execution cannot contain an error")
        if self.status is not ExecutionStatus.COMPLETED and self.error is None:
            raise ValueError("blocked or errored execution must contain an error")
        return self


class ExecutionEnvelope(DomainModel):
    execution: ExecutionResult
    evidence: list[Evidence] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_evidence_refs(self) -> "ExecutionEnvelope":
        evidence_ids = {item.evidence_id for item in self.evidence}
        missing = set(self.execution.observation_refs) - evidence_ids
        if missing:
            raise ValueError(f"observation_refs contain unknown evidence ids: {sorted(missing)}")
        return self


class GradeContext(DomainModel):
    run_id: NonEmptyStr
    case_id: NonEmptyStr


class GradeResult(DomainModel):
    grade_result_id: NonEmptyStr
    grader_id: NonEmptyStr
    case_id: NonEmptyStr
    expected_id: NonEmptyStr
    outcome: GradeOutcome
    passed: bool | None
    raw_score: float | None
    normalized_score: float | None
    reason: NonEmptyStr
    evidence_refs: list[str] = Field(default_factory=list)
    failure: FailureRecord | None = None

    @model_validator(mode="after")
    def validate_outcome_fields(self) -> "GradeResult":
        decided = self.outcome in {GradeOutcome.SATISFIED, GradeOutcome.UNSATISFIED}
        if decided and (
            self.passed is None or self.raw_score is None or self.normalized_score is None
        ):
            raise ValueError("decided grade requires passed and score values")
        if not decided and any(
            value is not None for value in (self.passed, self.raw_score, self.normalized_score)
        ):
            raise ValueError("undecided grade cannot contain passed or score values")
        if self.outcome is GradeOutcome.ERROR and self.failure is None:
            raise ValueError("errored grade requires a failure record")
        if self.outcome is not GradeOutcome.ERROR and self.failure is not None:
            raise ValueError("only errored grade can contain a failure record")
        return self


class CaseResult(DomainModel):
    case_id: NonEmptyStr
    contract_ids: list[NonEmptyStr]
    criticality: Criticality
    status: RunStatus
    execution_id: NonEmptyStr
    grader_results: list[GradeResult] = Field(default_factory=list)
    failure_refs: list[str] = Field(default_factory=list)


class ContractCoverage(DomainModel):
    covered: int = Field(ge=0)
    total: int = Field(ge=0)
    rate: float = Field(ge=0.0, le=1.0)
    uncovered_contract_ids: list[str] = Field(default_factory=list)


class GateDecision(DomainModel):
    gate_id: NonEmptyStr
    gate_type: GateType
    status: GateDecisionStatus
    passed: bool | None
    actual_value: bool | float | None
    operator: ComparisonOperator
    threshold: bool | float
    contributing_case_ids: list[str] = Field(default_factory=list)
    contributing_grade_result_ids: list[str] = Field(default_factory=list)
    reason: NonEmptyStr
    failure: FailureRecord | None = None


class GateResult(DomainModel):
    decisions: list[GateDecision]


class TraceabilityRecord(DomainModel):
    requirement_id: NonEmptyStr
    contract_id: NonEmptyStr
    case_id: NonEmptyStr
    expected_id: NonEmptyStr
    grader_id: NonEmptyStr
    grade_result_id: NonEmptyStr


class TraceabilitySnapshot(DomainModel):
    records: list[TraceabilityRecord]


class EvalResult(DomainModel):
    run_id: NonEmptyStr
    status: RunStatus
    case_results: list[CaseResult]
    contract_coverage: ContractCoverage
    grader_results: list[GradeResult]
    gate_result: GateResult
    failures: list[FailureRecord]
    evidence_refs: list[str]
    traceability: TraceabilitySnapshot


class EnvironmentSnapshot(DomainModel):
    python_version: NonEmptyStr
    platform: NonEmptyStr
    framework_version: NonEmptyStr


class EvalRunManifest(DomainModel):
    manifest_version: NonEmptyStr
    run_id: NonEmptyStr
    run_kind: RunKind
    target_skill_id: NonEmptyStr
    skill_version: NonEmptyStr
    skill_content_hash: NonEmptyStr
    eval_version: NonEmptyStr
    eval_definition_hash: NonEmptyStr
    testcase_version: NonEmptyStr
    grader_versions: dict[str, str]
    environment: EnvironmentSnapshot
    configuration: dict[str, JsonValue]
    started_at: datetime
    finished_at: datetime
    result_ref: NonEmptyStr
    gate_result_ref: NonEmptyStr
    comparison_parent_run_id: str | None = None

    @model_validator(mode="after")
    def baseline_cannot_have_comparison_parent(self) -> "EvalRunManifest":
        if self.run_kind is RunKind.BASELINE and self.comparison_parent_run_id is not None:
            raise ValueError("baseline run cannot have comparison_parent_run_id")
        return self


class ReportArtifacts(DomainModel):
    run_directory: Path
    manifest_path: Path
    definition_path: Path
    result_path: Path
    report_path: Path
    evidence_index_path: Path
