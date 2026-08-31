"""Subprocess coverage for the thin v0.1 command-line interface."""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Iterator
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import pytest
from conftest import make_definition_data

ROOT = Path(__file__).resolve().parents[1]
CONTROLLED = ROOT / "tests" / "fixtures" / "e2e" / "controlled"
DEFINITION = CONTROLLED / "definition.json"
RUN_INPUT = CONTROLLED / "run-input.json"
EXPECTED_DIGEST = "sha256:bc7aadd77f76f4f5bc32d57f7829616f86a00b3a320a4155e176cd986e3df9c1"


def _run_cli(*args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "skill_eval_framework.cli", *(str(arg) for arg in args)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _error(result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    value = json.loads(result.stderr)
    assert isinstance(value, dict)
    return value


@pytest.fixture
def cli_tmp_path() -> Iterator[Path]:
    """Keep subprocess artifacts inside the writable repository on Windows."""

    with TemporaryDirectory(prefix=".cli-test-", dir=ROOT) as directory:
        yield Path(directory)


def test_validate_command_accepts_explicit_v03_definition() -> None:
    result = _run_cli("validate", DEFINITION)

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload == {
        "benchmark_id": "skill.eval.v0",
        "benchmark_version": "0.1.0",
        "command": "validate",
        "definition_type": "BenchmarkDefinitionV03",
        "issues": [],
        "status": "valid",
    }


def test_validate_command_reports_cross_object_issue_codes(cli_tmp_path: Path) -> None:
    invalid = _load(DEFINITION)
    invalid["contracts"][0]["requirement_ids"] = ["R999"]
    path = cli_tmp_path / "invalid-definition.json"
    _write(path, invalid)

    result = _run_cli("validate", path)

    assert result.returncode == 1
    payload = _error(result)
    assert payload["error_type"] == "definition_validation_error"
    assert {item["code"] for item in payload["details"]} == {
        "DEF_REQUIREMENT_UNCOVERED",
        "DEF_UNKNOWN_REQUIREMENT_REF",
    }


def test_digest_command_uses_v1_authority() -> None:
    result = _run_cli("digest", DEFINITION)

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.strip() == EXPECTED_DIGEST


def test_evaluate_happy_path_serializes_complete_bundle(cli_tmp_path: Path) -> None:
    output = cli_tmp_path / "evaluation.json"

    result = _run_cli(
        "evaluate",
        "--definition",
        DEFINITION,
        "--run-input",
        RUN_INPUT,
        "--output",
        output,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    summary = json.loads(result.stdout)
    assert summary["run_validity"] == "valid"
    assert summary["scorecard_status"] == "finalized_evaluation"
    payload = _load(output)
    assert payload["output_version"] == "skill-eval-evaluation-output/v0.1"
    assert payload["definition_identity"]["definition_digest"] == EXPECTED_DIGEST
    assert payload["definition_identity"]["definition_closure_profile"].endswith("-v1")
    assert payload["run"]["execution_status"] == "completed"
    assert payload["run"]["validity_status"] == "valid"
    assert payload["episodes"][0]["execution_status"] == "completed"
    assert payload["grader_results"][0]["judgment"] == "satisfied"
    assert payload["metric_results"][0]["status"] == "available"
    assert payload["metric_results"][0]["value"]["canonical_value"] == "1"
    assert payload["gate_results"][0]["result"] == "OPEN"
    assert payload["overall_score_outcome"]["canonical_value"] == "1.00"
    assert payload["acceptance_evaluation"]["acceptance"] == "ACCEPTABLE"
    assert payload["scorecard"]["finalization_status"] == "finalized_evaluation"


def test_evaluate_rejects_definition_digest_or_profile_mismatch(cli_tmp_path: Path) -> None:
    value = _load(RUN_INPUT)
    value["definition_ref"]["definition_digest"] = "sha256:" + "0" * 64
    input_path = cli_tmp_path / "mismatched-input.json"
    output = cli_tmp_path / "should-not-exist.json"
    _write(input_path, value)

    result = _run_cli(
        "evaluate",
        "--definition",
        DEFINITION,
        "--run-input",
        input_path,
        "--output",
        output,
    )

    assert result.returncode == 1
    payload = _error(result)
    assert payload["error_type"] == "definition_identity_error"
    assert {item["code"] for item in payload["details"]} == {"RUN_DEFINITION_DIGEST_MISMATCH"}
    assert not output.exists()


def test_evaluate_rejects_invalid_runtime_graph(cli_tmp_path: Path) -> None:
    value = _load(RUN_INPUT)
    value["evidence"][0]["episode_id"] = "E999"
    input_path = cli_tmp_path / "invalid-graph.json"
    output = cli_tmp_path / "should-not-exist.json"
    _write(input_path, value)

    result = _run_cli(
        "evaluate",
        "--definition",
        DEFINITION,
        "--run-input",
        input_path,
        "--output",
        output,
    )

    assert result.returncode == 1
    payload = _error(result)
    assert payload["error_type"] == "runtime_graph_error"
    assert any(item["code"] == "RUN_EVIDENCE_EPISODE_UNKNOWN" for item in payload["details"])
    assert not output.exists()


def test_evaluate_missing_grader_uses_core_unavailable_semantics(cli_tmp_path: Path) -> None:
    value = _load(RUN_INPUT)
    value["grader_results"] = []
    input_path = cli_tmp_path / "missing-grader.json"
    output = cli_tmp_path / "missing-grader-output.json"
    _write(input_path, value)

    result = _run_cli(
        "evaluate",
        "--definition",
        DEFINITION,
        "--run-input",
        input_path,
        "--output",
        output,
    )

    assert result.returncode == 0, result.stderr
    payload = _load(output)
    assert payload["run"]["validity_status"] == "valid"
    assert payload["metric_results"][0]["status"] == "unavailable"
    assert payload["metric_results"][0]["unavailable_reason"] == "required_inputs_missing"
    assert payload["gate_results"][0]["result"] == "INDETERMINATE"
    assert payload["overall_score_outcome"]["evaluation_status"] == "unavailable"
    assert payload["acceptance_evaluation"]["acceptance"] == "INDETERMINATE"
    missing = payload["scorecard"]["result_inventory"]["missing_applications"]
    assert missing[0]["application_ref"]["application_type"] == "grader_result"


def test_evaluate_rejects_v02_free_text_definition(cli_tmp_path: Path) -> None:
    path = cli_tmp_path / "v02-definition.json"
    _write(path, make_definition_data())
    output = cli_tmp_path / "should-not-exist.json"

    result = _run_cli(
        "evaluate",
        "--definition",
        path,
        "--run-input",
        RUN_INPUT,
        "--output",
        output,
    )

    assert result.returncode == 1
    assert _error(result)["error_type"] == "definition_schema_error"
    assert not output.exists()


def test_evaluate_rejects_caller_supplied_derived_results(cli_tmp_path: Path) -> None:
    value = _load(RUN_INPUT)
    value["metric_results"] = [
        {
            "metric_result_id": "FORGED",
            "metric_id": "M001",
            "status": "available",
        }
    ]
    input_path = cli_tmp_path / "forged-derived-result.json"
    output = cli_tmp_path / "should-not-exist.json"
    _write(input_path, value)

    result = _run_cli(
        "evaluate",
        "--definition",
        DEFINITION,
        "--run-input",
        input_path,
        "--output",
        output,
    )

    assert result.returncode == 1
    payload = _error(result)
    assert payload["error_type"] == "input_schema_error"
    assert any(
        item["path"] == "metric_results" and item["code"] == "extra_forbidden"
        for item in payload["details"]
    )
    assert not output.exists()


def test_evaluate_rerun_is_byte_deterministic(cli_tmp_path: Path) -> None:
    first = cli_tmp_path / "first.json"
    second = cli_tmp_path / "second.json"

    first_result = _run_cli(
        "evaluate",
        "--definition",
        DEFINITION,
        "--run-input",
        RUN_INPUT,
        "--output",
        first,
    )
    second_result = _run_cli(
        "evaluate",
        "--definition",
        DEFINITION,
        "--run-input",
        RUN_INPUT,
        "--output",
        second,
    )

    assert first_result.returncode == second_result.returncode == 0
    assert first.read_bytes() == second.read_bytes()


def test_evaluate_invalid_definition_stops_before_output(cli_tmp_path: Path) -> None:
    invalid = deepcopy(_load(DEFINITION))
    invalid["metric_specifications"][0]["inputs"][0]["contract_id"] = "C999"
    definition_path = cli_tmp_path / "invalid-definition.json"
    output = cli_tmp_path / "should-not-exist.json"
    _write(definition_path, invalid)

    result = _run_cli(
        "evaluate",
        "--definition",
        definition_path,
        "--run-input",
        RUN_INPUT,
        "--output",
        output,
    )

    assert result.returncode == 1
    assert _error(result)["error_type"] == "definition_validation_error"
    assert not output.exists()
