"""Pure execution-plan operations."""

from __future__ import annotations

from skill_eval_framework.schemas.runtime import (
    PlannedAttemptSlot,
    Run,
    RunExecutionPlan,
    RunExecutionStatus,
    RunTestCaseDisposition,
)

from .errors import ExecutionPlanError


def admit_retry_attempt(
    source: Run | RunExecutionPlan,
    test_case_id: str,
) -> RunExecutionPlan:
    """Return a plan with one monotonically appended retry slot.

    Passing a Run additionally enforces the terminal-plan sealing boundary. Passing a
    bare plan is useful for pure plan manipulation and has no lifecycle context.
    """

    if isinstance(source, Run):
        if is_execution_plan_sealed(source):
            raise ExecutionPlanError("sealed Run execution plan cannot admit a retry")
        plan = source.execution_plan
    else:
        plan = source
    selected = next(
        (item for item in plan.test_cases if item.test_case_id == test_case_id),
        None,
    )
    if selected is None:
        raise ExecutionPlanError(f"unknown TestCase {test_case_id!r}")
    if selected.disposition != RunTestCaseDisposition.SCHEDULED:
        raise ExecutionPlanError(
            f"TestCase {test_case_id!r} is intentionally_not_scheduled and cannot retry"
        )
    current_indexes = [slot.attempt_index for slot in selected.attempt_slots]
    next_index = max(current_indexes, default=0) + 1
    replacement = selected.model_copy(
        update={
            "attempt_slots": [*selected.attempt_slots, PlannedAttemptSlot(attempt_index=next_index)]
        }
    )
    test_cases = [
        replacement if item.test_case_id == test_case_id else item for item in plan.test_cases
    ]
    return plan.model_copy(update={"test_cases": test_cases})


def is_execution_plan_sealed(run: Run) -> bool:
    """Terminal Run execution states seal the nested execution plan."""

    return RunExecutionStatus(run.execution_status) in {
        RunExecutionStatus.COMPLETED,
        RunExecutionStatus.PARTIAL,
        RunExecutionStatus.BLOCKED,
        RunExecutionStatus.FAILED,
        RunExecutionStatus.CANCELLED,
    }
