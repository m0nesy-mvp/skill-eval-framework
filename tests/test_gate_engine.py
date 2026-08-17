from copy import deepcopy
from pathlib import Path

from skill_eval.application.runner import EvalRunner
from skill_eval.domain.enums import GateDecisionStatus, RunStatus
from skill_eval.domain.models import EvalDefinition
from skill_eval.execution.fake import FakeExecutionAdapter
from skill_eval.infrastructure.yaml_loader import load_eval_definition

EXAMPLE_ROOT = Path("examples/dummy-skill")


def _definition_with_fixture(fixture: str) -> EvalDefinition:
    definition = load_eval_definition(EXAMPLE_ROOT / "eval.yaml")
    raw = deepcopy(definition.model_dump(mode="json"))
    raw["test_cases"][0]["input"]["fixture"] = fixture
    return EvalDefinition.model_validate(raw)


def test_all_gates_pass_for_satisfied_critical_case() -> None:
    result = EvalRunner().run(
        _definition_with_fixture("fixtures/pass.json"),
        FakeExecutionAdapter(),
        EXAMPLE_ROOT,
        "run-pass",
    )

    assert result.status is RunStatus.PASS
    assert all(item.status is GateDecisionStatus.PASS for item in result.gate_result.decisions)


def test_hard_gate_failure_produces_fail() -> None:
    result = EvalRunner().run(
        _definition_with_fixture("fixtures/fail.json"),
        FakeExecutionAdapter(),
        EXAMPLE_ROOT,
        "run-fail",
    )

    assert result.status is RunStatus.FAIL
    assert result.failures[0].domain.value == "skill"


def test_environment_block_produces_blocked_not_fail() -> None:
    result = EvalRunner().run(
        _definition_with_fixture("fixtures/blocked.json"),
        FakeExecutionAdapter(),
        EXAMPLE_ROOT,
        "run-blocked",
    )

    assert result.status is RunStatus.BLOCKED
    assert result.failures[0].domain.value == "environment"
    assert result.grader_results[0].outcome.value == "not_run"
    assert result.traceability.records[0].expected_id == "expected-greeting"
    assert all(
        item.status in {GateDecisionStatus.BLOCKED, GateDecisionStatus.PASS}
        for item in result.gate_result.decisions
    )


def test_grader_error_produces_error_not_zero_score() -> None:
    result = EvalRunner().run(
        _definition_with_fixture("fixtures/grader-error.json"),
        FakeExecutionAdapter(),
        EXAMPLE_ROOT,
        "run-error",
    )

    assert result.status is RunStatus.ERROR
    assert result.grader_results[0].normalized_score is None
    assert result.failures[0].domain.value == "grader"
