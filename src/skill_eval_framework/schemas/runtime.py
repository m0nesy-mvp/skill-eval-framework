"""Pydantic mappings for frozen Runtime schemas."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, model_validator

from .common import (
    BenchmarkId,
    ContractId,
    Digest,
    EvidenceSpecificationId,
    JsonScalar,
    NonEmptyStr,
    PositiveInt,
    SchemaModel,
    TestCaseId,
    ensure_unique,
)


class ObjectType(StrEnum):
    RUN = "run"
    EPISODE = "episode"
    ARTIFACT = "artifact"
    EVIDENCE = "evidence"
    GRADER_RESULT = "grader_result"
    METRIC_RESULT = "metric_result"
    GATE_RESULT = "gate_result"
    SCORECARD = "scorecard"
    TRACE_EVENT = "trace_event"
    DEFINITION = "definition"
    POLICY = "policy"
    SUBJECT = "subject"


class DefinitionClosureProfile(StrEnum):
    """Closed Runtime vocabulary for supported Definition closure profiles."""

    V0 = "skill-eval-frozen-definition-closure-v0"
    V1 = "skill-eval-frozen-definition-closure-v1"


class ObjectRef(SchemaModel):
    object_type: ObjectType
    object_ref: NonEmptyStr


class FrozenDefinitionRef(SchemaModel):
    benchmark_id: BenchmarkId
    benchmark_version: NonEmptyStr
    definition_closure_profile: DefinitionClosureProfile
    definition_digest: Digest
    definition_snapshot_ref: NonEmptyStr | None = None


class SubjectReference(SchemaModel):
    subject_ref: NonEmptyStr
    subject_kind: NonEmptyStr
    version_ref: NonEmptyStr | None = None
    content_digest: Digest | None = None
    identity_metadata: dict[NonEmptyStr, JsonScalar] | None = None


class RuntimeExecutionContext(SchemaModel):
    execution_context_id: NonEmptyStr
    orchestrator: NonEmptyStr
    environment_ref: NonEmptyStr | None = None
    configuration_ref: NonEmptyStr | None = None
    configuration_digest: Digest | None = None
    context_metadata: dict[NonEmptyStr, JsonScalar] | None = None


class PlannedAttemptSlot(SchemaModel):
    attempt_index: PositiveInt


class RunTestCaseDisposition(StrEnum):
    SCHEDULED = "scheduled"
    INTENTIONALLY_NOT_SCHEDULED = "intentionally_not_scheduled"


class RunTestCasePlan(SchemaModel):
    test_case_id: TestCaseId
    disposition: RunTestCaseDisposition
    attempt_slots: list[PlannedAttemptSlot]
    reason: NonEmptyStr | None = None

    @model_validator(mode="after")
    def validate_disposition_and_slots(self) -> "RunTestCasePlan":
        indexes = [slot.attempt_index for slot in self.attempt_slots]
        ensure_unique(indexes, "attempt_slots.attempt_index")
        if indexes and indexes[0] != 1:
            raise ValueError("attempt indexes must start at 1")
        if any(
            current <= previous for previous, current in zip(indexes, indexes[1:], strict=False)
        ):
            raise ValueError("attempt indexes must be strictly increasing")
        if self.disposition == RunTestCaseDisposition.SCHEDULED:
            if not self.attempt_slots:
                raise ValueError("scheduled test case requires at least one attempt slot")
            if self.reason is not None:
                raise ValueError("scheduled test case must not include a reason")
        else:
            if self.attempt_slots:
                raise ValueError("intentionally_not_scheduled test case must have no slots")
            if self.reason is None:
                raise ValueError("intentionally_not_scheduled test case requires a reason")
        return self


class RunExecutionPlan(SchemaModel):
    test_cases: list[RunTestCasePlan]

    @model_validator(mode="after")
    def validate_test_case_ids(self) -> "RunExecutionPlan":
        ensure_unique([item.test_case_id for item in self.test_cases], "test_cases.test_case_id")
        return self


class RunExecutionStatus(StrEnum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunValidityStatus(StrEnum):
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"


class ValidityStage(StrEnum):
    PRE_EXECUTION = "pre_execution"
    FINAL_INTEGRITY = "final_integrity"


class ValidityFinding(SchemaModel):
    code: NonEmptyStr
    stage: ValidityStage
    message: NonEmptyStr
    related_object_refs: list[ObjectRef]


class Run(SchemaModel):
    run_id: NonEmptyStr
    definition_ref: FrozenDefinitionRef
    subject_ref: SubjectReference
    execution_context: RuntimeExecutionContext
    execution_plan: RunExecutionPlan
    execution_status: RunExecutionStatus
    validity_status: RunValidityStatus
    validity_findings: list[ValidityFinding]
    created_at: datetime
    started_at: datetime | None = None
    ended_at: datetime | None = None
    episode_ids: list[NonEmptyStr]
    diagnostic_ids: list[NonEmptyStr]

    @property
    def logical_key(self) -> str:
        return self.run_id

    @model_validator(mode="after")
    def validate_local_state(self) -> "Run":
        ensure_unique(list(self.episode_ids), "episode_ids")
        ensure_unique(list(self.diagnostic_ids), "diagnostic_ids")
        terminal = self.execution_status in {
            RunExecutionStatus.COMPLETED,
            RunExecutionStatus.PARTIAL,
            RunExecutionStatus.BLOCKED,
            RunExecutionStatus.FAILED,
            RunExecutionStatus.CANCELLED,
        }
        if terminal and self.ended_at is None:
            raise ValueError("terminal Run requires ended_at")
        if not terminal and self.ended_at is not None:
            raise ValueError("non-terminal Run must not include ended_at")
        if (
            self.execution_status
            in {
                RunExecutionStatus.RUNNING,
                RunExecutionStatus.COMPLETED,
                RunExecutionStatus.PARTIAL,
            }
            and self.started_at is None
        ):
            raise ValueError("running, completed, or partial Run requires started_at")
        if self.execution_status == RunExecutionStatus.PARTIAL and not self.episode_ids:
            raise ValueError("partial Run requires at least one Episode")
        if self.validity_status == RunValidityStatus.INVALID and not self.validity_findings:
            raise ValueError("invalid Run requires at least one validity finding")
        if self.validity_status != RunValidityStatus.INVALID and self.validity_findings:
            raise ValueError("only invalid Run may contain confirmed validity findings")
        return self


class EpisodeExecutionStatus(StrEnum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TraceEvent(SchemaModel):
    trace_event_id: NonEmptyStr
    event_index: PositiveInt
    actor: NonEmptyStr
    event_type: NonEmptyStr
    semantic_summary: NonEmptyStr | None = None
    content_ref: NonEmptyStr | None = None
    tool_ref: NonEmptyStr | None = None
    operation: NonEmptyStr | None = None
    result_ref: NonEmptyStr | None = None
    occurred_at: datetime | None = None

    @model_validator(mode="after")
    def validate_observation_pointer(self) -> "TraceEvent":
        if self.semantic_summary is None and self.content_ref is None:
            raise ValueError("TraceEvent requires semantic_summary or content_ref")
        return self


class Episode(SchemaModel):
    episode_id: NonEmptyStr
    run_id: NonEmptyStr
    test_case_id: TestCaseId
    attempt_index: PositiveInt
    execution_status: EpisodeExecutionStatus
    created_at: datetime
    started_at: datetime | None = None
    ended_at: datetime | None = None
    trace_events: list[TraceEvent]
    artifact_ids: list[NonEmptyStr]
    evidence_ids: list[NonEmptyStr]
    diagnostic_ids: list[NonEmptyStr]

    @property
    def logical_key(self) -> tuple[str, TestCaseId, int]:
        return (self.run_id, self.test_case_id, self.attempt_index)

    @model_validator(mode="after")
    def validate_local_state(self) -> "Episode":
        indexes = [event.event_index for event in self.trace_events]
        ensure_unique([event.trace_event_id for event in self.trace_events], "trace_event_id")
        ensure_unique(indexes, "event_index")
        if indexes != sorted(indexes):
            raise ValueError("trace event indexes must be strictly increasing")
        ensure_unique(list(self.artifact_ids), "artifact_ids")
        ensure_unique(list(self.evidence_ids), "evidence_ids")
        ensure_unique(list(self.diagnostic_ids), "diagnostic_ids")
        terminal = self.execution_status in {
            EpisodeExecutionStatus.COMPLETED,
            EpisodeExecutionStatus.BLOCKED,
            EpisodeExecutionStatus.FAILED,
            EpisodeExecutionStatus.CANCELLED,
        }
        if terminal and self.ended_at is None:
            raise ValueError("terminal Episode requires ended_at")
        if not terminal and self.ended_at is not None:
            raise ValueError("non-terminal Episode must not include ended_at")
        if (
            self.execution_status
            in {
                EpisodeExecutionStatus.RUNNING,
                EpisodeExecutionStatus.COMPLETED,
                EpisodeExecutionStatus.FAILED,
            }
            and self.started_at is None
        ):
            raise ValueError("running, completed, or failed Episode requires started_at")
        return self


class ArtifactRelationType(StrEnum):
    PRODUCED = "produced"
    CONSUMED = "consumed"
    OBSERVED = "observed"


class ArtifactRelation(SchemaModel):
    relation: ArtifactRelationType
    episode_id: NonEmptyStr | None = None
    trace_event_id: NonEmptyStr | None = None
    source: NonEmptyStr

    @model_validator(mode="after")
    def validate_trace_scope(self) -> "ArtifactRelation":
        if self.trace_event_id is not None and self.episode_id is None:
            raise ValueError("trace_event_id requires episode_id")
        return self


class Artifact(SchemaModel):
    artifact_id: NonEmptyStr
    run_id: NonEmptyStr
    artifact_kind: NonEmptyStr
    locator: NonEmptyStr
    media_type: NonEmptyStr | None = None
    content_digest: Digest | None = None
    producer: NonEmptyStr
    relations: Annotated[list[ArtifactRelation], Field(min_length=1)]
    metadata: dict[NonEmptyStr, JsonScalar] | None = None

    @property
    def logical_key(self) -> str:
        return self.artifact_id


class EvidenceTargetRef(SchemaModel):
    test_case_id: TestCaseId
    contract_id: ContractId


class EvidenceSourceType(StrEnum):
    ARTIFACT = "artifact"
    TRACE_EVENT = "trace_event"
    STATE_OBSERVATION = "state_observation"
    RUNTIME_OUTPUT = "runtime_output"


class EvidenceSourceRef(SchemaModel):
    source_type: EvidenceSourceType
    source_id: NonEmptyStr
    locator: NonEmptyStr | None = None
    portion_ref: NonEmptyStr | None = None


class EvidenceObservation(SchemaModel):
    summary: NonEmptyStr
    content_ref: NonEmptyStr | None = None


class EvidenceProvenance(SchemaModel):
    source_refs: Annotated[list[EvidenceSourceRef], Field(min_length=1)]
    collector: NonEmptyStr
    observed_from: NonEmptyStr


class EvidenceContext(SchemaModel):
    context_summary: NonEmptyStr
    related_trace_event_ids: list[NonEmptyStr]

    @model_validator(mode="after")
    def validate_trace_ids(self) -> "EvidenceContext":
        ensure_unique(list(self.related_trace_event_ids), "related_trace_event_ids")
        return self


class QualificationCheck(SchemaModel):
    requirement: NonEmptyStr
    outcome: Literal["passed"]
    detail: NonEmptyStr


class EvidenceQualification(SchemaModel):
    status: Literal["qualified"]
    checks: Annotated[list[QualificationCheck], Field(min_length=1)]
    qualified_by: NonEmptyStr
    qualified_at: datetime


class Evidence(SchemaModel):
    evidence_id: NonEmptyStr
    run_id: NonEmptyStr
    episode_id: NonEmptyStr
    evidence_spec_id: EvidenceSpecificationId
    qualified_targets: Annotated[list[EvidenceTargetRef], Field(min_length=1)]
    observation: EvidenceObservation
    provenance: EvidenceProvenance
    context: EvidenceContext
    qualification: EvidenceQualification

    @property
    def logical_key(self) -> str:
        return self.evidence_id

    @model_validator(mode="after")
    def validate_targets(self) -> "Evidence":
        ensure_unique(
            [(target.test_case_id, target.contract_id) for target in self.qualified_targets],
            "qualified_targets",
        )
        return self


class DiagnosticPhase(StrEnum):
    DEFINITION_BINDING = "definition_binding"
    ENVIRONMENT = "environment"
    COLLECTION = "collection"
    GRADING = "grading"
    METRIC = "metric"
    GATE = "gate"
    SCORECARD = "scorecard"
    ORCHESTRATION = "orchestration"


class RuntimeDiagnostic(SchemaModel):
    diagnostic_id: NonEmptyStr
    run_id: NonEmptyStr
    episode_id: NonEmptyStr | None = None
    phase: DiagnosticPhase
    code: NonEmptyStr
    message: NonEmptyStr
    related_object_refs: list[ObjectRef]
    occurred_at: datetime
    retryable: bool | None = None

    @property
    def logical_key(self) -> str:
        return self.diagnostic_id
