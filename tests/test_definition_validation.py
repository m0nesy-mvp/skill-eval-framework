from copy import deepcopy
from pathlib import Path

import pytest

from skill_eval.domain.enums import ValidationSeverity
from skill_eval.domain.models import EvalDefinition
from skill_eval.infrastructure.yaml_loader import DefinitionLoadError, load_eval_definition
from skill_eval.validation.design import validate_eval_design

EXAMPLE = Path("examples/dummy-skill/eval.yaml")


def _raw_definition() -> dict[str, object]:
    definition = load_eval_definition(EXAMPLE)
    return definition.model_dump(mode="json")


def test_valid_definition_loads_and_passes_design_validation() -> None:
    definition = load_eval_definition(EXAMPLE)
    report = validate_eval_design(definition)

    assert report.is_valid
    assert not [item for item in report.findings if item.severity is ValidationSeverity.ERROR]


def test_definition_requires_at_least_one_gate() -> None:
    raw = _raw_definition()
    raw["gates"] = []

    with pytest.raises(ValueError, match="gates"):
        EvalDefinition.model_validate(raw)


def test_future_side_effect_metric_is_rejected() -> None:
    text = EXAMPLE.read_text(encoding="utf-8").replace(
        "metric: critical_cases_pass", "metric: no_unapproved_side_effect", 1
    )
    temporary = EXAMPLE.parent / "invalid-future-metric.yaml"
    temporary.write_text(text, encoding="utf-8")
    try:
        with pytest.raises(DefinitionLoadError, match="no_unapproved_side_effect"):
            load_eval_definition(temporary)
    finally:
        temporary.unlink()


def test_unknown_contract_breaks_traceability() -> None:
    raw = deepcopy(_raw_definition())
    test_cases = raw["test_cases"]
    assert isinstance(test_cases, list)
    assert isinstance(test_cases[0], dict)
    test_cases[0]["contract_ids"] = ["missing-contract"]
    definition = EvalDefinition.model_validate(raw)

    report = validate_eval_design(definition)

    assert not report.is_valid
    assert "unknown_contract" in {item.code for item in report.findings}


def test_boolean_gate_rejects_ordering_operator() -> None:
    raw = deepcopy(_raw_definition())
    gates = raw["gates"]
    assert isinstance(gates, list)
    assert isinstance(gates[0], dict)
    gates[0]["operator"] = "gte"
    definition = EvalDefinition.model_validate(raw)

    report = validate_eval_design(definition)

    assert not report.is_valid
    assert "invalid_gate_operator" in {item.code for item in report.findings}


def test_critical_contract_must_meet_coverage_policy() -> None:
    raw = deepcopy(_raw_definition())
    policy = raw["coverage_policy"]
    assert isinstance(policy, dict)
    policy["minimum_cases_by_criticality"] = {"critical": 2}
    definition = EvalDefinition.model_validate(raw)

    report = validate_eval_design(definition)

    assert not report.is_valid
    assert "insufficient_contract_coverage" in {item.code for item in report.findings}


def test_critical_gate_cannot_use_scope_without_critical_case() -> None:
    raw = deepcopy(_raw_definition())
    test_cases = raw["test_cases"]
    gates = raw["gates"]
    assert isinstance(test_cases, list) and isinstance(test_cases[0], dict)
    assert isinstance(gates, list) and isinstance(gates[0], dict)
    test_cases[0]["criticality"] = "medium"
    policy = raw["coverage_policy"]
    assert isinstance(policy, dict)
    policy["required_categories_by_criticality"] = {}
    definition = EvalDefinition.model_validate(raw)

    report = validate_eval_design(definition)

    assert not report.is_valid
    assert "unreachable_gate_metric" in {item.code for item in report.findings}
