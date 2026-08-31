"""Smoke coverage for the packaged Skill entrypoints and public CLI example."""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "assets" / "examples" / "minimal"
DEFINITION = EXAMPLE / "definition.json"
RUN_INPUT = EXAMPLE / "run-input.json"
EXPECTED_DIGEST = "sha256:51469ca8e5639afb34bcadb7a6ddd27db711ad4b99c1fcbadc3f2d0f35a54c1d"


def _run_cli(*args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "skill_eval_framework.cli", *(str(arg) for arg in args)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


@pytest.fixture
def example_tmp_path() -> Iterator[Path]:
    with TemporaryDirectory(prefix=".public-example-", dir=ROOT) as directory:
        yield Path(directory)


def test_packaged_skill_entrypoints_exist_and_state_current_boundary() -> None:
    paths = [
        ROOT / "SKILL.md",
        ROOT / "README.md",
        ROOT / "references" / "design-workflow.md",
        ROOT / "references" / "runtime-evaluation.md",
        ROOT / "references" / "executable-policy-v03.md",
        ROOT / "references" / "cli.md",
        DEFINITION,
        RUN_INPUT,
    ]
    assert all(path.is_file() for path in paths)

    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "BenchmarkDefinitionV03" in skill
    assert "AUDIT-001" in skill
    assert "ACCEPTED_RISK" in skill


def test_public_example_validate_and_digest() -> None:
    validated = _run_cli("validate", DEFINITION)
    digested = _run_cli("digest", DEFINITION)

    assert validated.returncode == 0, validated.stderr
    assert json.loads(validated.stdout)["status"] == "valid"
    assert digested.returncode == 0, digested.stderr
    assert digested.stdout.strip() == EXPECTED_DIGEST
    assert _load(RUN_INPUT)["definition_ref"]["definition_digest"] == EXPECTED_DIGEST


def test_public_example_evaluate(example_tmp_path: Path) -> None:
    output = example_tmp_path / "evaluation.json"
    result = _run_cli(
        "evaluate",
        "--definition",
        DEFINITION,
        "--run-input",
        RUN_INPUT,
        "--output",
        output,
    )

    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    payload = _load(output)
    assert summary["run_validity"] == "valid"
    assert summary["scorecard_status"] == "finalized_evaluation"
    assert payload["metric_results"][0]["value"]["canonical_value"] == "1"
    assert payload["gate_results"][0]["result"] == "OPEN"
    assert payload["overall_score_outcome"]["canonical_value"] == "1.00"
    assert payload["acceptance_evaluation"]["acceptance"] == "ACCEPTABLE"
