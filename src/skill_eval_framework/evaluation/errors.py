"""Small typed error boundary for deterministic evaluation services."""


class EvaluationServiceError(Exception):
    """Base error for evaluation service misuse or unavailable execution semantics."""


class MetricEvaluationError(EvaluationServiceError):
    """Raised when a Metric policy cannot be executed deterministically."""


class GateEvaluationError(EvaluationServiceError):
    """Raised when a Gate cannot be executed deterministically."""


class OverallEvaluationError(EvaluationServiceError):
    """Raised when Overall calculation cannot produce a semantic outcome."""


class AcceptanceEvaluationError(EvaluationServiceError):
    """Raised when Acceptance evaluation cannot produce a semantic outcome."""


class UnsupportedDefinitionVersionError(EvaluationServiceError):
    """Raised when a service receives a historical non-executable Definition model."""
