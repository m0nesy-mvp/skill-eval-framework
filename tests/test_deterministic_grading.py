from copy import deepcopy
from pathlib import Path

import pytest

from skill_eval.domain.enums import DeterministicOperation, EvidenceKind, GradeOutcome
from skill_eval.domain.models import (
    Evidence,
    GradeContext,
    GraderSpec,
    Rubric,
    RubricLevel,
)
from skill_eval.evidence.store import EvidenceStore
from skill_eval.grading.deterministic import DeterministicGrader
from skill_eval.infrastructure.yaml_loader import load_eval_definition

EXAMPLE_ROOT = Path("examples/dummy-skill")


def _definition_parts() -> tuple[object, GraderSpec]:
    definition = load_eval_definition(EXAMPLE_ROOT / "eval.yaml")
    return definition.test_cases[0].expected[0], definition.graders[0]


def _view(data: object) -> object:
    evidence = Evidence(
        evidence_id="evidence-1",
        kind=EvidenceKind.FINAL_STATE,
        source="test",
        media_type="application/json",
        data=data,
    )
    return EvidenceStore([evidence]).view()


def test_binary_grader_without_rubric_maps_pass_to_one() -> None:
    assertion, spec = _definition_parts()
    result = DeterministicGrader().grade(
        assertion,  # type: ignore[arg-type]
        spec,
        _view({"greeting": "Hello, Ada!"}),  # type: ignore[arg-type]
        GradeContext(run_id="run-1", case_id="case-greeting-happy"),
    )

    assert result.outcome is GradeOutcome.SATISFIED
    assert result.passed is True
    assert result.raw_score == 1.0
    assert result.normalized_score == 1.0


def test_binary_grader_without_rubric_maps_fail_to_zero() -> None:
    assertion, spec = _definition_parts()
    result = DeterministicGrader().grade(
        assertion,  # type: ignore[arg-type]
        spec,
        _view({"greeting": "wrong"}),  # type: ignore[arg-type]
        GradeContext(run_id="run-1", case_id="case-greeting-happy"),
    )

    assert result.outcome is GradeOutcome.UNSATISFIED
    assert result.passed is False
    assert result.raw_score == 0.0
    assert result.normalized_score == 0.0


def test_missing_required_evidence_is_error_with_null_scores() -> None:
    assertion, spec = _definition_parts()
    result = DeterministicGrader().grade(
        assertion,  # type: ignore[arg-type]
        spec,
        EvidenceStore([]).view(),
        GradeContext(run_id="run-1", case_id="case-greeting-happy"),
    )

    assert result.outcome is GradeOutcome.ERROR
    assert result.passed is None
    assert result.raw_score is None
    assert result.normalized_score is None
    assert result.failure is not None
    assert result.failure.domain.value == "grader"


def test_explicit_rubric_controls_raw_and_normalized_score() -> None:
    assertion, spec = _definition_parts()
    assertion = assertion.model_copy(update={"rubric_id": "rubric-4"})  # type: ignore[union-attr]
    rubric = Rubric(
        rubric_id="rubric-4",
        version="1.0.0",
        minimum_score=0,
        maximum_score=4,
        levels=[
            RubricLevel(passed=True, score=4, label="full", description="fully satisfied"),
            RubricLevel(passed=False, score=1, label="failed", description="not satisfied"),
        ],
    )

    result = DeterministicGrader({rubric.rubric_id: rubric}).grade(
        assertion,
        spec,
        _view({"greeting": "wrong"}),  # type: ignore[arg-type]
        GradeContext(run_id="run-1", case_id="case-greeting-happy"),
    )

    assert result.raw_score == 1
    assert result.normalized_score == 0.25


@pytest.mark.parametrize(
    ("operation", "data", "config", "expected_pass"),
    [
        ("exists", {"value": 1}, {}, True),
        ("not_exists", {"value": 1}, {}, False),
        ("equals", "hello", {"expected": "hello"}, True),
        ("not_equals", "hello", {"expected": "world"}, True),
        ("contains", ["a", "b"], {"expected": "b"}, True),
        ("matches_regex", "abc-123", {"expected": r"\d+"}, True),
        ("field_equals", {"nested": {"value": 3}}, {"field": "nested.value", "expected": 3}, True),
        ("count_equals", {"value": 1}, {"expected": 1}, True),
    ],
)
def test_supported_operations(
    operation: str, data: object, config: dict[str, object], expected_pass: bool
) -> None:
    assertion, base_spec = _definition_parts()
    raw = deepcopy(base_spec.model_dump(mode="json"))
    raw["operation"] = operation
    raw["config"] = config
    spec = GraderSpec.model_validate(raw)

    result = DeterministicGrader().grade(
        assertion,  # type: ignore[arg-type]
        spec,
        _view(data),  # type: ignore[arg-type]
        GradeContext(run_id="run-1", case_id="case-greeting-happy"),
    )

    assert spec.operation is DeterministicOperation(operation)
    assert result.passed is expected_pass
