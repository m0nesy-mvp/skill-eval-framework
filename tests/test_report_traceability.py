from pathlib import Path

from skill_eval.application.runner import EvalRunner
from skill_eval.execution.fake import FakeExecutionAdapter
from skill_eval.infrastructure.yaml_loader import load_eval_definition
from skill_eval.reporting.json_writer import write_baseline_artifacts

EXAMPLE_ROOT = Path("examples/dummy-skill")


def test_markdown_report_contains_full_failure_explanation_chain(tmp_path: Path) -> None:
    definition = load_eval_definition(EXAMPLE_ROOT / "eval.yaml")
    failing_case = definition.test_cases[0].model_copy(
        update={"input": {"fixture": "fixtures/fail.json"}}
    )
    definition = definition.model_copy(update={"test_cases": [failing_case]})
    result = EvalRunner().run(
        definition,
        FakeExecutionAdapter(),
        EXAMPLE_ROOT,
        "baseline-failure-report",
    )

    artifacts = write_baseline_artifacts(definition, result, tmp_path, EXAMPLE_ROOT)
    report = artifacts.report_path.read_text(encoding="utf-8")

    assert "Overall status: **FAIL**" in report
    assert "req-greeting" in report
    assert "contract-greeting" in report
    assert "case-greeting-happy" in report
    assert "expected-greeting" in report
    assert "grader-greeting" in report
    assert "skill/skill_failure" in report
