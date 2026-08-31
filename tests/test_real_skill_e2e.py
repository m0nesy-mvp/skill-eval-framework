"""End-to-end proof for a small real Skill benchmark fixture."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "e2e" / "real-skill"
DEFINITION = FIXTURE / "definition.json"
RUN_INPUT = FIXTURE / "run-input.json"
SUBJECT_OUTPUT = FIXTURE / "subject-output.json"
EXPECTED_DIGEST = "sha256:23353a52fad7526364d8b38b51fc5f961750d1de1c93c56bc935c7dc75de9e3d"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_structured_task_summary_skill_evaluates_end_to_end() -> None:
    subject_output = _load(SUBJECT_OUTPUT)
    assert set(subject_output) == {"summary", "priority", "next_action"}
    assert subject_output["priority"] in {"low", "medium", "high"}
    assert subject_output["next_action"] == (
        "Draft the slide outline and send it to the team for review."
    )
    run_input = _load(RUN_INPUT)
    artifact_digest = run_input["artifacts"][0]["content_digest"]
    assert artifact_digest == f"sha256:{hashlib.sha256(SUBJECT_OUTPUT.read_bytes()).hexdigest()}"

    with TemporaryDirectory(prefix=".real-skill-e2e-", dir=ROOT) as directory:
        output_path = Path(directory) / "evaluation.json"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "skill_eval_framework.cli",
                "evaluate",
                "--definition",
                str(DEFINITION),
                "--run-input",
                str(RUN_INPUT),
                "--output",
                str(output_path),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        payload = _load(output_path)

    assert payload["definition_identity"] == {
        "benchmark_id": "structured-task-summary.skill",
        "benchmark_version": "1.0.0",
        "definition_closure_profile": "skill-eval-frozen-definition-closure-v1",
        "definition_digest": EXPECTED_DIGEST,
        "definition_snapshot_ref": "definition.json",
    }
    assert payload["run"]["execution_status"] == "completed"
    assert payload["run"]["validity_status"] == "valid"
    assert payload["episodes"][0]["episode_id"] == "E-REAL-001"
    assert payload["grader_results"][0]["judgment"] == "satisfied"
    metric = payload["metric_results"][0]
    assert metric["status"] == "available"
    assert metric["value"]["canonical_value"] == "1"
    assert metric["coverage"]["denominator"] == "1"
    assert metric["input_traces"][0]["grader_result_id"] == "GR-REAL-001"
    gate = payload["gate_results"][0]
    assert gate["result"] == "OPEN"
    assert gate["input_summary"]["observed_canonical_value"] == "1"
    assert gate["input_summary"]["comparator_outcome"] == "false"
    assert payload["overall_score_outcome"]["canonical_value"] == "1.00"
    assert payload["acceptance_evaluation"]["acceptance"] == "ACCEPTABLE"
    assert payload["scorecard"]["finalization_status"] == "finalized_evaluation"
    assert payload["scorecard"]["result_inventory"]["missing_applications"] == []
