"""Application orchestration for the complete in-memory MVP 0 evaluation flow."""

from pathlib import Path

from skill_eval.domain.enums import (
    ExecutionStatus,
    FailureCode,
    FailureDomain,
    GateDecisionStatus,
    GateType,
    GradeOutcome,
    RunStatus,
)
from skill_eval.domain.models import (
    CaseResult,
    ContractCoverage,
    EvalDefinition,
    EvalResult,
    FailureRecord,
    GateDecision,
    GradeContext,
    GradeResult,
    GraderSpec,
    TestCase,
    TraceabilityRecord,
    TraceabilitySnapshot,
)
from skill_eval.domain.ports import ExecutionAdapter
from skill_eval.evidence.store import EvidenceStore
from skill_eval.gating.engine import GateEngine
from skill_eval.grading.deterministic import DeterministicGrader
from skill_eval.grading.registry import GraderRegistry
from skill_eval.validation.design import validate_eval_design


class InvalidEvalDesignError(ValueError):
    """The Eval Definition failed preflight and execution was not started."""


class EvalRunner:
    def __init__(self, gate_engine: GateEngine | None = None) -> None:
        self._gate_engine = gate_engine or GateEngine()

    def run(
        self,
        definition: EvalDefinition,
        execution_adapter: ExecutionAdapter,
        fixture_root: Path,
        run_id: str,
    ) -> EvalResult:
        validation = validate_eval_design(definition)
        if not validation.is_valid:
            messages = "; ".join(
                finding.message
                for finding in validation.findings
                if finding.severity.value == "error"
            )
            raise InvalidEvalDesignError(messages)

        rubrics = {rubric.rubric_id: rubric for rubric in definition.rubrics}
        registry = GraderRegistry([DeterministicGrader(rubrics)])
        grader_specs = {grader.grader_id: grader for grader in definition.graders}
        cases: list[CaseResult] = []
        failures: list[FailureRecord] = []
        evidence_refs: list[str] = []

        for case in definition.test_cases:
            envelope = execution_adapter.execute(case, fixture_root)
            evidence_refs.extend(item.evidence_id for item in envelope.evidence)
            if envelope.execution.status is not ExecutionStatus.COMPLETED:
                assert envelope.execution.error is not None
                failures.append(envelope.execution.error)
                not_run_grades = self._not_run_grades(
                    case,
                    grader_specs,
                    "execution was blocked"
                    if envelope.execution.status is ExecutionStatus.BLOCKED
                    else "execution failed",
                )
                cases.append(
                    CaseResult(
                        case_id=case.case_id,
                        contract_ids=case.contract_ids,
                        criticality=case.criticality,
                        status=(
                            RunStatus.BLOCKED
                            if envelope.execution.status is ExecutionStatus.BLOCKED
                            else RunStatus.ERROR
                        ),
                        execution_id=envelope.execution.execution_id,
                        grader_results=not_run_grades,
                        failure_refs=[envelope.execution.error.failure_id],
                    )
                )
                continue

            view = EvidenceStore(envelope.evidence).view()
            grades: list[GradeResult] = []
            case_failures: list[FailureRecord] = []
            for assertion in case.expected:
                for grader_id in assertion.grader_ids:
                    spec = grader_specs[grader_id]
                    grader = registry.require(spec.kind.value)
                    grade = grader.grade(
                        assertion,
                        spec,
                        view,
                        GradeContext(run_id=run_id, case_id=case.case_id),
                    )
                    grades.append(grade)
                    if grade.failure is not None:
                        case_failures.append(grade.failure)
                    elif grade.outcome is GradeOutcome.UNSATISFIED:
                        case_failures.append(
                            FailureRecord(
                                failure_id=f"failure:{grade.grade_result_id}:skill",
                                domain=FailureDomain.SKILL,
                                code=FailureCode.SKILL_FAILURE,
                                message=grade.reason,
                                case_id=case.case_id,
                                grader_id=grade.grader_id,
                                evidence_refs=grade.evidence_refs,
                            )
                        )

            if any(grade.outcome is GradeOutcome.ERROR for grade in grades):
                case_status = RunStatus.ERROR
            elif any(grade.outcome is GradeOutcome.UNSATISFIED for grade in grades):
                case_status = RunStatus.FAIL
            else:
                case_status = RunStatus.PASS
            failures.extend(case_failures)
            cases.append(
                CaseResult(
                    case_id=case.case_id,
                    contract_ids=case.contract_ids,
                    criticality=case.criticality,
                    status=case_status,
                    execution_id=envelope.execution.execution_id,
                    grader_results=grades,
                    failure_refs=[failure.failure_id for failure in case_failures],
                )
            )

        gate_result = self._gate_engine.evaluate(definition, cases)
        status = self._overall_status(cases, gate_result.decisions)
        coverage = self._coverage(definition, cases)
        all_grades = [grade for case in cases for grade in case.grader_results]
        traceability = self._traceability(definition, all_grades)
        return EvalResult(
            run_id=run_id,
            status=status,
            case_results=cases,
            contract_coverage=coverage,
            grader_results=all_grades,
            gate_result=gate_result,
            failures=failures,
            evidence_refs=list(dict.fromkeys(evidence_refs)),
            traceability=traceability,
        )

    @staticmethod
    def _overall_status(cases: list[CaseResult], decisions: list[GateDecision]) -> RunStatus:
        if any(case.status is RunStatus.ERROR for case in cases) or any(
            decision.status is GateDecisionStatus.ERROR for decision in decisions
        ):
            return RunStatus.ERROR
        if any(
            decision.gate_type is GateType.HARD
            and decision.status is GateDecisionStatus.FAIL
            for decision in decisions
        ):
            return RunStatus.FAIL
        if any(case.status is RunStatus.BLOCKED for case in cases) or any(
            decision.status is GateDecisionStatus.BLOCKED for decision in decisions
        ):
            return RunStatus.BLOCKED
        if any(decision.status is GateDecisionStatus.FAIL for decision in decisions):
            return RunStatus.FAIL
        return RunStatus.PASS

    @staticmethod
    def _coverage(definition: EvalDefinition, cases: list[CaseResult]) -> ContractCoverage:
        contract_ids = {
            contract.contract_id for contract in definition.contract_table.contracts
        }
        covered = {contract_id for case in cases for contract_id in case.contract_ids}
        uncovered = sorted(contract_ids - covered)
        return ContractCoverage(
            covered=len(contract_ids) - len(uncovered),
            total=len(contract_ids),
            rate=(len(contract_ids) - len(uncovered)) / len(contract_ids),
            uncovered_contract_ids=uncovered,
        )

    @staticmethod
    def _traceability(
        definition: EvalDefinition, grades: list[GradeResult]
    ) -> TraceabilitySnapshot:
        grade_by_key = {
            (grade.case_id, grade.expected_id, grade.grader_id): grade for grade in grades
        }
        contract_by_id = {
            contract.contract_id: contract for contract in definition.contract_table.contracts
        }
        records: list[TraceabilityRecord] = []
        for case in definition.test_cases:
            for assertion in case.expected:
                for contract_id in assertion.contract_ids:
                    contract = contract_by_id[contract_id]
                    for requirement_id in contract.requirement_ids:
                        for grader_id in assertion.grader_ids:
                            grade = grade_by_key.get(
                                (case.case_id, assertion.expected_id, grader_id)
                            )
                            if grade is not None:
                                records.append(
                                    TraceabilityRecord(
                                        requirement_id=requirement_id,
                                        contract_id=contract_id,
                                        case_id=case.case_id,
                                        expected_id=assertion.expected_id,
                                        grader_id=grader_id,
                                        grade_result_id=grade.grade_result_id,
                                    )
                                )
        return TraceabilitySnapshot(records=records)

    @staticmethod
    def _not_run_grades(
        case: TestCase,
        grader_specs: dict[str, GraderSpec],
        reason: str,
    ) -> list[GradeResult]:
        results: list[GradeResult] = []
        for assertion in case.expected:
            for grader_id in assertion.grader_ids:
                if grader_id not in grader_specs:
                    raise KeyError(f"unknown grader: {grader_id}")
                results.append(
                    GradeResult(
                        grade_result_id=(
                            f"grade:{case.case_id}:{assertion.expected_id}:{grader_id}"
                        ),
                        grader_id=grader_id,
                        case_id=case.case_id,
                        expected_id=assertion.expected_id,
                        outcome=GradeOutcome.NOT_RUN,
                        passed=None,
                        raw_score=None,
                        normalized_score=None,
                        reason=reason,
                        evidence_refs=[],
                        failure=None,
                    )
                )
        return results
