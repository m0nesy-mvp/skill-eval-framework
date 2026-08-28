"""Serialization and schema-generation checks."""

import json
from typing import Any

from skill_eval_framework.schemas.definition import BenchmarkDefinition
from skill_eval_framework.schemas.results import Scorecard
from skill_eval_framework.schemas.runtime import Run


def test_definition_json_round_trip_preserves_model(definition_data: dict[str, Any]) -> None:
    original = BenchmarkDefinition.model_validate(definition_data)
    restored = BenchmarkDefinition.model_validate_json(original.model_dump_json())
    assert restored == original


def test_run_json_round_trip_preserves_model(run_data: dict[str, Any]) -> None:
    original = Run.model_validate(run_data)
    restored = Run.model_validate_json(original.model_dump_json())
    assert restored == original


def test_scorecard_json_round_trip_preserves_model(scorecard_data: dict[str, Any]) -> None:
    original = Scorecard.model_validate(scorecard_data)
    restored = Scorecard.model_validate_json(original.model_dump_json())
    assert restored == original


def test_definition_json_schema_contains_discriminators() -> None:
    schema_text = json.dumps(BenchmarkDefinition.model_json_schema())
    assert '"discriminator"' in schema_text
    assert '"condition_type"' in schema_text
    assert '"mode"' in schema_text
