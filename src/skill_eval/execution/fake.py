"""Fixture-backed execution adapter used exclusively by MVP 0."""

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from skill_eval.domain.models import Evidence, ExecutionEnvelope, ExecutionResult, TestCase


class FakeExecutionError(ValueError):
    """A fake execution fixture is missing or invalid."""


class FakeExecutionAdapter:
    def execute(self, case: TestCase, fixture_root: Path) -> ExecutionEnvelope:
        fixture_name = self._fixture_name(case)
        fixture_path = (fixture_root / fixture_name).resolve()
        root = fixture_root.resolve()
        if root not in fixture_path.parents:
            raise FakeExecutionError("fixture path escapes fixture root")

        try:
            raw: Any = json.loads(fixture_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise FakeExecutionError(f"cannot load fixture {fixture_path}: {exc}") from exc
        if not isinstance(raw, dict):
            raise FakeExecutionError("fixture root must be an object")

        evidence_raw = raw.get("evidence", [])
        if not isinstance(evidence_raw, list):
            raise FakeExecutionError("fixture evidence must be a list")
        try:
            evidence = [Evidence.model_validate(item) for item in evidence_raw]
            evidence = [self._with_hash(item) for item in evidence]
            execution = ExecutionResult.model_validate(raw.get("execution"))
            if execution.case_id != case.case_id:
                raise FakeExecutionError(
                    f"fixture case_id {execution.case_id!r} does not match {case.case_id!r}"
                )
            return ExecutionEnvelope(execution=execution, evidence=evidence)
        except ValidationError as exc:
            raise FakeExecutionError(f"invalid fixture {fixture_path}: {exc}") from exc

    @staticmethod
    def _fixture_name(case: TestCase) -> str:
        if not isinstance(case.input, dict):
            raise FakeExecutionError("case input must be an object containing fixture")
        fixture = case.input.get("fixture")
        if not isinstance(fixture, str) or not fixture:
            raise FakeExecutionError("case input.fixture must be a non-empty string")
        return fixture

    @staticmethod
    def _with_hash(evidence: Evidence) -> Evidence:
        payload = evidence.model_dump(mode="json", exclude={"sha256"})
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        if evidence.sha256 is not None and evidence.sha256 != digest:
            raise FakeExecutionError(f"evidence hash mismatch: {evidence.evidence_id}")
        return evidence.model_copy(update={"sha256": digest})

