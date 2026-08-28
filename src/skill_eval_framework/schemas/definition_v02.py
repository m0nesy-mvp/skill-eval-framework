"""Explicit import surface for the historical Benchmark Definition v0.2 schema."""

from .definition import *  # noqa: F403
from .definition import (
    BenchmarkDefinition,
    GraderResultGateCondition,
    MetricSpecification,
)

BenchmarkDefinitionV02 = BenchmarkDefinition

__all__ = [
    "BenchmarkDefinitionV02",
    "BenchmarkDefinition",
    "MetricSpecification",
    "GraderResultGateCondition",
]
