"""Regression coverage for the public Definition version boundary."""

from skill_eval_framework import schemas
from skill_eval_framework.schemas.definition import (
    BenchmarkDefinition as LegacyBenchmarkDefinition,
)
from skill_eval_framework.schemas.definition import (
    GateSpecification as LegacyGateSpecification,
)
from skill_eval_framework.schemas.definition import (
    MetricSpecification as LegacyMetricSpecification,
)
from skill_eval_framework.schemas.definition_v02 import (
    BenchmarkDefinitionV02,
    GateSpecificationV02,
    MetricSpecificationV02,
)
from skill_eval_framework.schemas.definition_v03 import (
    BenchmarkDefinitionV03,
    GateSpecificationV03,
    MetricSpecificationV03,
)


def test_aggregate_unsuffixed_definition_api_is_current_v03() -> None:
    assert schemas.BenchmarkDefinition is BenchmarkDefinitionV03
    assert schemas.MetricSpecification is MetricSpecificationV03
    assert schemas.GateSpecification is GateSpecificationV03


def test_explicit_v02_exports_preserve_historical_compatibility() -> None:
    assert BenchmarkDefinitionV02 is LegacyBenchmarkDefinition
    assert MetricSpecificationV02 is LegacyMetricSpecification
    assert GateSpecificationV02 is LegacyGateSpecification
    assert schemas.BenchmarkDefinitionV02 is LegacyBenchmarkDefinition


def test_versioned_modules_do_not_publish_unsuffixed_roots() -> None:
    from skill_eval_framework.schemas import definition_v02, definition_v03

    assert "BenchmarkDefinition" not in definition_v02.__all__
    assert "MetricSpecification" not in definition_v02.__all__
    assert "BenchmarkDefinition" not in definition_v03.__all__
    assert "MetricSpecification" not in definition_v03.__all__
