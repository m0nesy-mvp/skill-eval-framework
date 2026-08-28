"""Small exception hierarchy for runtime orchestration misuse."""


class RuntimeServiceError(Exception):
    """Base error for deterministic runtime service misuse."""


class InvalidTransitionError(RuntimeServiceError):
    """Raised when a lifecycle transition is not frozen/allowed."""


class ExecutionPlanError(RuntimeServiceError):
    """Raised when an execution-plan operation cannot be admitted."""


class IntegrityFinalizationError(RuntimeServiceError):
    """Raised when final validity cannot be finalized at this lifecycle point."""
