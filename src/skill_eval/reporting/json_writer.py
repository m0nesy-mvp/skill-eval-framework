"""Immutable baseline artifact writer for MVP 0."""

import hashlib
import json
import platform
from datetime import UTC, datetime
from pathlib import Path

from skill_eval import __version__
from skill_eval.domain.enums import RunKind
from skill_eval.domain.models import (
    EnvironmentSnapshot,
    EvalDefinition,
    EvalResult,
    EvalRunManifest,
    ReportArtifacts,
)
from skill_eval.reporting.markdown import render_markdown


def _json_text(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _sha256(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_baseline_artifacts(
    definition: EvalDefinition,
    result: EvalResult,
    output_root: Path,
    fixture_root: Path,
) -> ReportArtifacts:
    run_directory = output_root / result.run_id
    run_directory.mkdir(parents=True, exist_ok=False)
    evidence_directory = run_directory / "evidence"
    evidence_directory.mkdir()

    definition_path = run_directory / "resolved-eval-definition.json"
    result_path = run_directory / "result.json"
    report_path = run_directory / "report.md"
    manifest_path = run_directory / "manifest.json"
    evidence_index_path = evidence_directory / "index.json"

    definition_text = _json_text(definition.model_dump(mode="json"))
    definition_path.write_text(definition_text, encoding="utf-8")
    result_path.write_text(
        _json_text(result.model_dump(mode="json")), encoding="utf-8"
    )
    evidence_index_path.write_text(
        _json_text({"evidence_refs": result.evidence_refs}), encoding="utf-8"
    )

    now = datetime.now(UTC)
    target = definition.contract_table.target_skill
    manifest = EvalRunManifest(
        manifest_version="0.1",
        run_id=result.run_id,
        run_kind=RunKind.BASELINE,
        target_skill_id=target.skill_id,
        skill_version=target.version,
        skill_content_hash=target.content_hash,
        eval_version=definition.eval_version,
        eval_definition_hash=_sha256(definition_text),
        testcase_version=definition.eval_version,
        grader_versions={item.grader_id: item.version for item in definition.graders},
        environment=EnvironmentSnapshot(
            python_version=platform.python_version(),
            platform=platform.platform(),
            framework_version=__version__,
        ),
        configuration={"fixture_root": str(fixture_root.resolve())},
        started_at=now,
        finished_at=now,
        result_ref=result_path.name,
        gate_result_ref=f"{result_path.name}#/gate_result",
    )
    manifest_path.write_text(
        _json_text(manifest.model_dump(mode="json")), encoding="utf-8"
    )
    report_path.write_text(render_markdown(manifest, result), encoding="utf-8")

    return ReportArtifacts(
        run_directory=run_directory,
        manifest_path=manifest_path,
        definition_path=definition_path,
        result_path=result_path,
        report_path=report_path,
        evidence_index_path=evidence_index_path,
    )
