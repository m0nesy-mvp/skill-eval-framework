"""Deterministic, declaration-only grading for MVP 0."""

import re
from collections.abc import Mapping
from typing import cast

from pydantic import JsonValue

from skill_eval.domain.enums import (
    DeterministicOperation,
    FailureCode,
    FailureDomain,
    GradeOutcome,
    GraderKind,
)
from skill_eval.domain.models import (
    Evidence,
    ExpectedAssertion,
    FailureRecord,
    GradeContext,
    GradeResult,
    GraderSpec,
    Rubric,
)
from skill_eval.evidence.store import EvidenceView
from skill_eval.scoring.rubrics import score_binary


class GraderEvaluationError(ValueError):
    """Evidence or configuration cannot produce a valid deterministic decision."""


class DeterministicGrader:
    def __init__(self, rubrics: Mapping[str, Rubric] | None = None) -> None:
        self._rubrics = dict(rubrics or {})

    @property
    def kind(self) -> str:
        return GraderKind.DETERMINISTIC.value

    def grade(
        self,
        assertion: ExpectedAssertion,
        spec: GraderSpec,
        evidence: EvidenceView,
        context: GradeContext,
    ) -> GradeResult:
        grade_result_id = f"grade:{context.case_id}:{assertion.expected_id}:{spec.grader_id}"
        selected = self._select_evidence(spec, evidence)
        evidence_refs = [item.evidence_id for item in selected]
        try:
            passed = self._evaluate(spec, selected)
            rubric = self._rubric(assertion)
            raw_score, normalized_score = score_binary(passed, rubric)
        except (GraderEvaluationError, KeyError, TypeError, ValueError, re.error) as exc:
            failure = FailureRecord(
                failure_id=f"failure:{grade_result_id}",
                domain=FailureDomain.GRADER,
                code=(
                    FailureCode.INSUFFICIENT_EVIDENCE
                    if not selected
                    else FailureCode.GRADER_FAILURE
                ),
                message=str(exc),
                case_id=context.case_id,
                grader_id=spec.grader_id,
                evidence_refs=evidence_refs,
                retryable=False,
            )
            return GradeResult(
                grade_result_id=grade_result_id,
                grader_id=spec.grader_id,
                case_id=context.case_id,
                expected_id=assertion.expected_id,
                outcome=GradeOutcome.ERROR,
                passed=None,
                raw_score=None,
                normalized_score=None,
                reason=str(exc),
                evidence_refs=evidence_refs,
                failure=failure,
            )

        return GradeResult(
            grade_result_id=grade_result_id,
            grader_id=spec.grader_id,
            case_id=context.case_id,
            expected_id=assertion.expected_id,
            outcome=GradeOutcome.SATISFIED if passed else GradeOutcome.UNSATISFIED,
            passed=passed,
            raw_score=raw_score,
            normalized_score=normalized_score,
            reason=f"{spec.operation.value} returned {passed}",
            evidence_refs=evidence_refs,
            failure=None,
        )

    def _rubric(self, assertion: ExpectedAssertion) -> Rubric | None:
        if assertion.rubric_id is None:
            return None
        try:
            return self._rubrics[assertion.rubric_id]
        except KeyError as exc:
            raise GraderEvaluationError(f"unknown rubric: {assertion.rubric_id}") from exc

    @staticmethod
    def _select_evidence(spec: GraderSpec, evidence: EvidenceView) -> tuple[Evidence, ...]:
        requested_id = spec.config.get("evidence_id")
        if requested_id is not None:
            if not isinstance(requested_id, str):
                raise GraderEvaluationError("config.evidence_id must be a string")
            selected = evidence.get(requested_id)
            if selected is None or selected.kind is not spec.evidence_kind:
                return ()
            return (selected,)
        return evidence.by_kind(spec.evidence_kind)

    def _evaluate(self, spec: GraderSpec, evidence: tuple[Evidence, ...]) -> bool:
        operation = spec.operation
        if operation is DeterministicOperation.EXISTS:
            return bool(evidence)
        if operation is DeterministicOperation.NOT_EXISTS:
            return not evidence
        if operation is DeterministicOperation.COUNT_EQUALS:
            expected_count = spec.config.get("expected")
            if not isinstance(expected_count, int) or isinstance(expected_count, bool):
                raise GraderEvaluationError("count_equals requires integer config.expected")
            return len(evidence) == expected_count
        if not evidence:
            raise GraderEvaluationError(f"no {spec.evidence_kind.value} evidence is available")
        if len(evidence) != 1:
            raise GraderEvaluationError(
                "operation requires exactly one evidence item; configure evidence_id"
            )

        actual = evidence[0].data
        expected = spec.config.get("expected")
        if operation is DeterministicOperation.EQUALS:
            return bool(actual == expected)
        if operation is DeterministicOperation.NOT_EQUALS:
            return bool(actual != expected)
        if operation is DeterministicOperation.CONTAINS:
            if not isinstance(actual, (str, list, dict)):
                raise GraderEvaluationError("contains requires string, list, or object evidence")
            return expected in actual
        if operation is DeterministicOperation.MATCHES_REGEX:
            if not isinstance(actual, str) or not isinstance(expected, str):
                raise GraderEvaluationError("matches_regex requires string evidence and expected")
            return re.search(expected, actual) is not None
        if operation is DeterministicOperation.FIELD_EQUALS:
            field = spec.config.get("field")
            if not isinstance(field, str) or not field:
                raise GraderEvaluationError("field_equals requires non-empty config.field")
            return self._resolve_field(actual, field) == expected
        raise GraderEvaluationError(f"unsupported operation: {operation.value}")

    @staticmethod
    def _resolve_field(value: JsonValue | None, path: str) -> JsonValue:
        current: object = value
        for segment in path.split("."):
            if not isinstance(current, dict) or segment not in current:
                raise GraderEvaluationError(f"field does not exist: {path}")
            current = current[segment]
        return cast(JsonValue, current)
