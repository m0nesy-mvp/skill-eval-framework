import json
from pathlib import Path

import pytest

from skill_eval.application.runner import EvalRunner
from skill_eval.domain.enums import RunStatus
from skill_eval.execution.fake import FakeExecutionAdapter
from skill_eval.infrastructure.yaml_loader import load_eval_definition
from skill_eval.reporting.json_writer import write_baseline_artifacts

EXAMPLE_ROOT = Path("examples/dummy-skill")


def test_dummy_baseline_writes_complete_immutable_artifact_set(tmp_path: Path) -> None:
    definition = load_eval_definition(EXAMPLE_ROOT / "eval.yaml")
    result = EvalRunner().run(
        definition,
        FakeExecutionAdapter(),
        EXAMPLE_ROOT,
        "baseline-test",
    )

    artifacts = write_baseline_artifacts(definition, result, tmp_path, EXAMPLE_ROOT)

    assert result.status is RunStatus.PASS
    assert artifacts.manifest_path.is_file()
    assert artifacts.definition_path.is_file()
    assert artifacts.result_path.is_file()
    assert artifacts.report_path.is_file()
    assert artifacts.evidence_index_path.is_file()
    saved_result = json.loads(artifacts.result_path.read_text(encoding="utf-8"))
    assert saved_result["status"] == "pass"
    with pytest.raises(FileExistsError):
        write_baseline_artifacts(definition, result, tmp_path, EXAMPLE_ROOT)


def test_result_is_stable_except_run_id() -> None:
    definition = load_eval_definition(EXAMPLE_ROOT / "eval.yaml")
    first = EvalRunner().run(
        definition, FakeExecutionAdapter(), EXAMPLE_ROOT, "baseline-first"
    )
    second = EvalRunner().run(
        definition, FakeExecutionAdapter(), EXAMPLE_ROOT, "baseline-second"
    )

    first_payload = first.model_dump(mode="json", exclude={"run_id"})
    second_payload = second.model_dump(mode="json", exclude={"run_id"})
    assert first_payload == second_payload

