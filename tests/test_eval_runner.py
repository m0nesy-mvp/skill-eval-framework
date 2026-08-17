from pathlib import Path

from skill_eval.application.runner import EvalRunner
from skill_eval.domain.enums import RunStatus
from skill_eval.execution.fake import FakeExecutionAdapter
from skill_eval.infrastructure.yaml_loader import load_eval_definition

EXAMPLE_ROOT = Path("examples/dummy-skill")


def test_eval_result_contains_complete_traceability_chain() -> None:
    definition = load_eval_definition(EXAMPLE_ROOT / "eval.yaml")

    result = EvalRunner().run(
        definition,
        FakeExecutionAdapter(),
        EXAMPLE_ROOT,
        "run-trace",
    )

    assert result.status is RunStatus.PASS
    record = result.traceability.records[0]
    assert record.requirement_id == "req-greeting"
    assert record.contract_id == "contract-greeting"
    assert record.case_id == "case-greeting-happy"
    assert record.expected_id == "expected-greeting"
    assert record.grader_id == "grader-greeting"
    assert record.grade_result_id == result.grader_results[0].grade_result_id
    assert result.gate_result.decisions[0].contributing_grade_result_ids == [
        result.grader_results[0].grade_result_id
    ]
