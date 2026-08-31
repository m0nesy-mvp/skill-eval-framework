"""Explicit versioned imports for the historical Benchmark Definition v0.2 schema."""

from .definition import (
    BenchmarkDefinition as BenchmarkDefinitionV02,
)
from .definition import (
    GateCondition as GateConditionV02,
)
from .definition import (
    GateSpecification as GateSpecificationV02,
)
from .definition import (
    GraderResultGateCondition as GraderResultGateConditionV02,
)
from .definition import (
    MetricNormalization as MetricNormalizationV02,
)
from .definition import (
    MetricSpecification as MetricSpecificationV02,
)

__all__ = [
    "BenchmarkDefinitionV02",
    "GateConditionV02",
    "GateSpecificationV02",
    "GraderResultGateConditionV02",
    "MetricNormalizationV02",
    "MetricSpecificationV02",
]
