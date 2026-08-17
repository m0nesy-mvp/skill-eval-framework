"""Closed vocabularies used by MVP 0 domain models."""

from enum import StrEnum


class Criticality(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EvidenceKind(StrEnum):
    SCREENSHOT = "screenshot"
    UI_TREE = "ui_tree"
    LOG = "log"
    ACTION = "action"
    TOOL_CALL = "tool_call"
    FINAL_STATE = "final_state"
    ARTIFACT = "artifact"
    METADATA = "metadata"


class TestCaseCategory(StrEnum):
    HAPPY_PATH = "happy_path"
    BOUNDARY = "boundary"
    NEGATIVE = "negative"
    AMBIGUOUS_INPUT = "ambiguous_input"
    MISSING_INPUT = "missing_input"
    TOOL_FAILURE = "tool_failure"
    RECOVERY = "recovery"
    SAFETY = "safety"
    SIDE_EFFECT = "side_effect"
    IDEMPOTENCY = "idempotency"


class GraderKind(StrEnum):
    DETERMINISTIC = "deterministic"


class DeterministicOperation(StrEnum):
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    MATCHES_REGEX = "matches_regex"
    FIELD_EQUALS = "field_equals"
    COUNT_EQUALS = "count_equals"


class GateType(StrEnum):
    HARD = "hard"
    SOFT = "soft"


class GateMetric(StrEnum):
    CRITICAL_CASES_PASS = "critical_cases_pass"
    SUCCESS_RATE = "success_rate"
    OVERALL_SCORE = "overall_score"
    CONTRACT_COVERAGE = "contract_coverage"
    REQUIRED_CASES_DECIDED = "required_cases_decided"


class ComparisonOperator(StrEnum):
    EQ = "eq"
    NE = "ne"
    GTE = "gte"
    GT = "gt"
    LTE = "lte"
    LT = "lt"


class GateScopeKind(StrEnum):
    RUN = "run"
    CASE = "case"
    CONTRACT = "contract"


class ValidationSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ExecutionStatus(StrEnum):
    COMPLETED = "completed"
    BLOCKED = "blocked"
    ERROR = "error"


class FailureDomain(StrEnum):
    SKILL = "skill"
    ENVIRONMENT = "environment"
    EVAL = "eval"
    GRADER = "grader"


class FailureCode(StrEnum):
    SKILL_FAILURE = "skill_failure"
    PLANNING_FAILURE = "planning_failure"
    NAVIGATION_FAILURE = "navigation_failure"
    WRONG_TOOL = "wrong_tool"
    WRONG_PARAMETER = "wrong_parameter"
    WRONG_TARGET = "wrong_target"
    MISSING_CONFIRMATION = "missing_confirmation"
    PREMATURE_SIDE_EFFECT = "premature_side_effect"
    RECOVERY_FAILURE = "recovery_failure"
    TIMEOUT = "timeout"
    ENVIRONMENT_FAILURE = "environment_failure"
    EVAL_CASE_FAILURE = "eval_case_failure"
    EVAL_DESIGN_FAILURE = "eval_design_failure"
    CONFIGURATION_FAILURE = "configuration_failure"
    TRACEABILITY_FAILURE = "traceability_failure"
    GRADER_FAILURE = "grader_failure"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    UNSUPPORTED_EVIDENCE = "unsupported_evidence"
    UNKNOWN = "unknown"


class GradeOutcome(StrEnum):
    SATISFIED = "satisfied"
    UNSATISFIED = "unsatisfied"
    ERROR = "error"
    NOT_RUN = "not_run"


class RunStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    BLOCKED = "blocked"
    ERROR = "error"


class GateDecisionStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    BLOCKED = "blocked"
    ERROR = "error"


class RunKind(StrEnum):
    BASELINE = "baseline"
    CANDIDATE = "candidate"
