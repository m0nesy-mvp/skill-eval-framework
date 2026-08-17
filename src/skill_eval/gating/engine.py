"""Metric aggregation and explicit Hard/Soft acceptance gates."""

from collections.abc import Sequence

from skill_eval.domain.enums import (
    ComparisonOperator,
    GateDecisionStatus,
    GateMetric,
    GateScopeKind,
    RunStatus,
)
from skill_eval.domain.models import (
    CaseResult,
    EvalDefinition,
    FailureRecord,
    GateDecision,
    GateResult,
    GateSpec,
)


class GateEngine:
    def evaluate(self, definition: EvalDefinition, cases: list[CaseResult]) -> GateResult:
        decisions = [self._evaluate_gate(gate, definition, cases) for gate in definition.gates]
        return GateResult(decisions=decisions)

    def _evaluate_gate(
        self, gate: GateSpec, definition: EvalDefinition, cases: list[CaseResult]
    ) -> GateDecision:
        selected = self._select_cases(gate, definition, cases)
        case_ids = [case.case_id for case in selected]
        grade_ids = [
            grade.grade_result_id for case in selected for grade in case.grader_results
        ]

        if any(case.status is RunStatus.ERROR for case in selected):
            return self._undecided(
                gate,
                GateDecisionStatus.ERROR,
                "a contributing case has an evaluation or grader error",
                case_ids,
                grade_ids,
            )
        if gate.metric is not GateMetric.CONTRACT_COVERAGE and any(
            case.status is RunStatus.BLOCKED for case in selected
        ):
            return self._undecided(
                gate,
                GateDecisionStatus.BLOCKED,
                "a contributing case is blocked by its environment",
                case_ids,
                grade_ids,
            )

        actual = self._metric(gate.metric, definition, selected)
        passed = self._compare(actual, gate.operator, gate.threshold)
        return GateDecision(
            gate_id=gate.gate_id,
            gate_type=gate.gate_type,
            status=GateDecisionStatus.PASS if passed else GateDecisionStatus.FAIL,
            passed=passed,
            actual_value=actual,
            operator=gate.operator,
            threshold=gate.threshold,
            contributing_case_ids=case_ids,
            contributing_grade_result_ids=grade_ids,
            reason=(
                f"{gate.metric.value}={actual!r} {gate.operator.value} "
                f"{gate.threshold!r} returned {passed}"
            ),
        )

    @staticmethod
    def _select_cases(
        gate: GateSpec, definition: EvalDefinition, cases: list[CaseResult]
    ) -> list[CaseResult]:
        if gate.scope.kind is GateScopeKind.RUN:
            return list(cases)
        if gate.scope.kind is GateScopeKind.CASE:
            selected_ids = set(gate.scope.ids)
        else:
            selected_contracts = set(gate.scope.ids)
            selected_ids = {
                case.case_id
                for case in definition.test_cases
                if selected_contracts.intersection(case.contract_ids)
            }
        return [case for case in cases if case.case_id in selected_ids]

    @staticmethod
    def _metric(
        metric: GateMetric, definition: EvalDefinition, cases: Sequence[CaseResult]
    ) -> bool | float:
        if metric is GateMetric.CRITICAL_CASES_PASS:
            critical = [case for case in cases if case.criticality.value == "critical"]
            return all(case.status is RunStatus.PASS for case in critical)
        if metric is GateMetric.REQUIRED_CASES_DECIDED:
            required = [case for case in cases if case.criticality.value == "critical"]
            return all(case.status in {RunStatus.PASS, RunStatus.FAIL} for case in required)
        if metric is GateMetric.SUCCESS_RATE:
            if not cases:
                return 0.0
            return sum(case.status is RunStatus.PASS for case in cases) / len(cases)
        if metric is GateMetric.OVERALL_SCORE:
            scores = [
                grade.normalized_score
                for case in cases
                for grade in case.grader_results
                if grade.normalized_score is not None
            ]
            return sum(scores) / len(scores) if scores else 0.0
        if metric is GateMetric.CONTRACT_COVERAGE:
            all_contracts = {
                contract.contract_id for contract in definition.contract_table.contracts
            }
            if not all_contracts:
                return 0.0
            covered = {contract_id for case in cases for contract_id in case.contract_ids}
            return len(covered & all_contracts) / len(all_contracts)
        raise ValueError(f"unsupported gate metric: {metric.value}")

    @staticmethod
    def _compare(
        actual: bool | float, operator: ComparisonOperator, threshold: bool | float
    ) -> bool:
        if operator is ComparisonOperator.EQ:
            return actual == threshold
        if operator is ComparisonOperator.NE:
            return actual != threshold
        if isinstance(actual, bool) or isinstance(threshold, bool):
            raise ValueError("ordering comparison requires numeric values")
        if operator is ComparisonOperator.GTE:
            return actual >= threshold
        if operator is ComparisonOperator.GT:
            return actual > threshold
        if operator is ComparisonOperator.LTE:
            return actual <= threshold
        if operator is ComparisonOperator.LT:
            return actual < threshold
        raise ValueError(f"unsupported operator: {operator.value}")

    @staticmethod
    def _undecided(
        gate: GateSpec,
        status: GateDecisionStatus,
        reason: str,
        case_ids: list[str],
        grade_ids: list[str],
        failure: FailureRecord | None = None,
    ) -> GateDecision:
        return GateDecision(
            gate_id=gate.gate_id,
            gate_type=gate.gate_type,
            status=status,
            passed=None,
            actual_value=None,
            operator=gate.operator,
            threshold=gate.threshold,
            contributing_case_ids=case_ids,
            contributing_grade_result_ids=grade_ids,
            reason=reason,
            failure=failure,
        )

