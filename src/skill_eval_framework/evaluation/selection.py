"""Shared deterministic attempt selection for Metric and direct-Grader Gate services."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from skill_eval_framework.schemas.definition_v03 import AttemptSelectionMode, AttemptSelectionPolicy
from skill_eval_framework.schemas.results import GraderResult

from .errors import EvaluationServiceError


@dataclass(frozen=True, slots=True)
class AttemptResult:
    """A GraderResult paired with its authoritative Episode attempt index."""

    attempt_index: int
    result: GraderResult


class AttemptSelectionError(EvaluationServiceError):
    """Raised when a typed selection policy cannot be satisfied."""


def select_attempt_results(
    candidates: Sequence[AttemptResult],
    policy: AttemptSelectionPolicy,
) -> tuple[AttemptResult, ...]:
    """Select attempt-level Results using only Episode attempt order."""

    ordered = tuple(sorted(candidates, key=lambda item: item.attempt_index))
    if any(
        current.attempt_index == previous.attempt_index
        for previous, current in zip(ordered, ordered[1:], strict=False)
    ):
        raise AttemptSelectionError("multiple distinct GraderResults share one attempt index")
    if policy.mode == AttemptSelectionMode.ALL_DISTINCT:
        return ordered
    if policy.mode == AttemptSelectionMode.SOLE_DISTINCT:
        if len(ordered) > 1:
            raise AttemptSelectionError("sole_distinct requires exactly one distinct Result")
        return ordered
    if policy.mode == AttemptSelectionMode.FIRST_DISTINCT:
        return ordered[:1]
    if policy.mode == AttemptSelectionMode.FINAL_DISTINCT_RAW:
        return ordered[-1:]
    raise AttemptSelectionError(f"unsupported attempt selection mode: {policy.mode!r}")


__all__ = ["AttemptResult", "AttemptSelectionError", "select_attempt_results"]
