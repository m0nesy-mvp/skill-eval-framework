"""Deterministic evaluation services and explicit v0 execution boundaries."""

from .acceptance import evaluate_acceptance
from .audit import (
    EvaluationFinding,
    gate_executability_findings,
    metric_executability_findings,
)
from .errors import (
    AcceptanceEvaluationError,
    EvaluationServiceError,
    GateEvaluationError,
    MetricEvaluationError,
    OverallEvaluationError,
    UnsupportedDefinitionVersionError,
)
from .gate import evaluate_gate, evaluate_three_valued_quantifier
from .metric import calculate_metric_result
from .overall import calculate_overall_score
from .selection import AttemptResult, AttemptSelectionError, select_attempt_results

__all__ = [
    "AcceptanceEvaluationError",
    "EvaluationFinding",
    "EvaluationServiceError",
    "AttemptResult",
    "AttemptSelectionError",
    "GateEvaluationError",
    "MetricEvaluationError",
    "OverallEvaluationError",
    "UnsupportedDefinitionVersionError",
    "calculate_metric_result",
    "calculate_overall_score",
    "evaluate_acceptance",
    "evaluate_gate",
    "evaluate_three_valued_quantifier",
    "gate_executability_findings",
    "metric_executability_findings",
    "select_attempt_results",
]
