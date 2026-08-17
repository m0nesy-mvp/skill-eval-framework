"""Public protocols for replaceable MVP 0 components."""

from pathlib import Path
from typing import Protocol

from skill_eval.domain.models import (
    CaseResult,
    EvalDefinition,
    EvalResult,
    EvalRunManifest,
    ExecutionEnvelope,
    ExpectedAssertion,
    GateResult,
    GradeContext,
    GradeResult,
    GraderSpec,
    ReportArtifacts,
    TestCase,
)
from skill_eval.evidence.store import EvidenceView


class ExecutionAdapter(Protocol):
    def execute(self, case: TestCase, fixture_root: Path) -> ExecutionEnvelope: ...


class Grader(Protocol):
    @property
    def kind(self) -> str: ...

    def grade(
        self,
        assertion: ExpectedAssertion,
        spec: GraderSpec,
        evidence: EvidenceView,
        context: GradeContext,
    ) -> GradeResult: ...


class GateEvaluator(Protocol):
    def evaluate(self, definition: EvalDefinition, cases: list[CaseResult]) -> GateResult: ...


class ReportRenderer(Protocol):
    def render(
        self,
        manifest: EvalRunManifest,
        result: EvalResult,
        output_dir: Path,
    ) -> ReportArtifacts: ...
