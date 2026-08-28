"""Machine-executability audit helpers for the deterministic evaluator."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EvaluationFinding:
    code: str
    authority: str
    problem: str
    reason: str
    blocking: bool
    recommendation: str


def metric_executability_findings() -> tuple[EvaluationFinding, ...]:
    """Return no blocker: v0.3 Metric policies are typed and executable."""

    return ()


def gate_executability_findings() -> tuple[EvaluationFinding, ...]:
    """Return no blocker: v0.3 direct-Grader selection is typed and executable."""

    return ()


__all__ = [
    "EvaluationFinding",
    "gate_executability_findings",
    "metric_executability_findings",
]
