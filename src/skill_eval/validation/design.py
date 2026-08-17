"""Deterministic preflight validation for an Eval Definition."""

import json
from collections import Counter, defaultdict
from collections.abc import Iterable

from skill_eval.domain.enums import (
    ComparisonOperator,
    Criticality,
    GateMetric,
    GateScopeKind,
    TestCaseCategory,
    ValidationSeverity,
)
from skill_eval.domain.models import EvalDefinition, ValidationFinding, ValidationReport

SUPPORTED_SCHEMA_VERSIONS = {"0.1"}
BOOLEAN_METRICS = {GateMetric.CRITICAL_CASES_PASS, GateMetric.REQUIRED_CASES_DECIDED}
NUMERIC_METRICS = {
    GateMetric.SUCCESS_RATE,
    GateMetric.OVERALL_SCORE,
    GateMetric.CONTRACT_COVERAGE,
}
BOOLEAN_OPERATORS = {ComparisonOperator.EQ, ComparisonOperator.NE}
NUMERIC_OPERATORS = set(ComparisonOperator)
NEGATIVE_CATEGORIES = {
    TestCaseCategory.NEGATIVE,
    TestCaseCategory.SAFETY,
    TestCaseCategory.SIDE_EFFECT,
}


def _duplicates(values: Iterable[str]) -> set[str]:
    counts = Counter(values)
    return {value for value, count in counts.items() if count > 1}


def _finding(
    severity: ValidationSeverity, code: str, message: str, *refs: str
) -> ValidationFinding:
    return ValidationFinding(
        severity=severity,
        code=code,
        message=message,
        object_refs=list(refs),
    )


def validate_eval_design(definition: EvalDefinition) -> ValidationReport:
    findings: list[ValidationFinding] = []

    if definition.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        findings.append(
            _finding(
                ValidationSeverity.ERROR,
                "unsupported_schema_version",
                f"schema_version {definition.schema_version!r} is not supported",
                definition.eval_id,
            )
        )

    requirements = definition.contract_table.requirements
    contracts = definition.contract_table.contracts
    cases = definition.test_cases
    graders = definition.graders
    rubrics = definition.rubrics
    gates = definition.gates

    for label, values in (
        ("requirement", [item.requirement_id for item in requirements]),
        ("contract", [item.contract_id for item in contracts]),
        ("case", [item.case_id for item in cases]),
        ("grader", [item.grader_id for item in graders]),
        ("rubric", [item.rubric_id for item in rubrics]),
        ("gate", [item.gate_id for item in gates]),
    ):
        for duplicate in sorted(_duplicates(values)):
            findings.append(
                _finding(
                    ValidationSeverity.ERROR,
                    "duplicate_id",
                    f"duplicate {label} id: {duplicate}",
                    duplicate,
                )
            )

    requirement_ids = {item.requirement_id for item in requirements}
    contract_ids = {item.contract_id for item in contracts}
    case_ids = {item.case_id for item in cases}
    case_by_id = {item.case_id: item for item in cases}
    grader_by_id = {item.grader_id: item for item in graders}
    rubric_ids = {item.rubric_id for item in rubrics}

    expected_ids = [assertion.expected_id for case in cases for assertion in case.expected]
    for duplicate in sorted(_duplicates(expected_ids)):
        findings.append(
            _finding(
                ValidationSeverity.ERROR,
                "duplicate_id",
                f"duplicate expected id: {duplicate}",
                duplicate,
            )
        )

    for contract in contracts:
        for requirement_id in contract.requirement_ids:
            if requirement_id not in requirement_ids:
                findings.append(
                    _finding(
                        ValidationSeverity.ERROR,
                        "unknown_requirement",
                        f"contract {contract.contract_id} references unknown requirement "
                        f"{requirement_id}",
                        contract.contract_id,
                        requirement_id,
                    )
                )
        for reference in contract.source_references:
            if reference.content_hash is None:
                findings.append(
                    _finding(
                        ValidationSeverity.WARNING,
                        "source_hash_missing",
                        f"source reference {reference.source_id} has no content hash",
                        contract.contract_id,
                        reference.source_id,
                    )
                )

    contract_case_ids: dict[str, set[str]] = defaultdict(set)
    contract_categories: dict[str, set[TestCaseCategory]] = defaultdict(set)
    contract_evidence: dict[str, set[object]] = defaultdict(set)
    normalized_cases: dict[str, str] = {}

    for case in cases:
        signature = json.dumps(
            {
                "contracts": sorted(case.contract_ids),
                "category": case.category,
                "input": case.input,
                "expected": sorted(item.description for item in case.expected),
            },
            sort_keys=True,
            default=str,
        )
        if signature in normalized_cases:
            findings.append(
                _finding(
                    ValidationSeverity.WARNING,
                    "duplicate_case_signature",
                    f"case {case.case_id} duplicates {normalized_cases[signature]}",
                    case.case_id,
                    normalized_cases[signature],
                )
            )
        else:
            normalized_cases[signature] = case.case_id

        for contract_id in case.contract_ids:
            if contract_id not in contract_ids:
                findings.append(
                    _finding(
                        ValidationSeverity.ERROR,
                        "unknown_contract",
                        f"case {case.case_id} references unknown contract {contract_id}",
                        case.case_id,
                        contract_id,
                    )
                )
            contract_case_ids[contract_id].add(case.case_id)
            contract_categories[contract_id].add(case.category)

        for assertion in case.expected:
            if not set(assertion.contract_ids).issubset(set(case.contract_ids)):
                findings.append(
                    _finding(
                        ValidationSeverity.ERROR,
                        "assertion_contract_mismatch",
                        f"assertion {assertion.expected_id} references a contract outside its case",
                        case.case_id,
                        assertion.expected_id,
                    )
                )
            if assertion.rubric_id is not None and assertion.rubric_id not in rubric_ids:
                findings.append(
                    _finding(
                        ValidationSeverity.ERROR,
                        "unknown_rubric",
                        f"assertion {assertion.expected_id} references unknown rubric "
                        f"{assertion.rubric_id}",
                        assertion.expected_id,
                        assertion.rubric_id,
                    )
                )
            for grader_id in assertion.grader_ids:
                grader = grader_by_id.get(grader_id)
                if grader is None:
                    findings.append(
                        _finding(
                            ValidationSeverity.ERROR,
                            "unknown_grader",
                            f"assertion {assertion.expected_id} references unknown grader "
                            f"{grader_id}",
                            assertion.expected_id,
                            grader_id,
                        )
                    )
                    continue
                for contract_id in assertion.contract_ids:
                    contract_evidence[contract_id].add(grader.evidence_kind)

    for contract in contracts:
        case_count = len(contract_case_ids[contract.contract_id])
        minimum = definition.coverage_policy.minimum_cases_by_criticality.get(
            contract.criticality, 0
        )
        if case_count < minimum:
            findings.append(
                _finding(
                    ValidationSeverity.ERROR,
                    "insufficient_contract_coverage",
                    f"contract {contract.contract_id} has {case_count} cases; {minimum} required",
                    contract.contract_id,
                )
            )

        required_categories = definition.coverage_policy.required_categories_by_criticality.get(
            contract.criticality, set()
        )
        missing_categories = required_categories - contract_categories[contract.contract_id]
        if missing_categories:
            findings.append(
                _finding(
                    ValidationSeverity.ERROR,
                    "missing_required_case_category",
                    f"contract {contract.contract_id} lacks categories: "
                    + ", ".join(sorted(item.value for item in missing_categories)),
                    contract.contract_id,
                )
            )

        for requirement in contract.required_evidence:
            if requirement.kind not in contract_evidence[contract.contract_id]:
                findings.append(
                    _finding(
                        ValidationSeverity.ERROR,
                        "unavailable_required_evidence",
                        f"contract {contract.contract_id} requires "
                        f"{requirement.kind.value} evidence "
                        "but no linked grader consumes it",
                        contract.contract_id,
                    )
                )

        if (
            definition.coverage_policy.forbidden_behaviors_require_negative_case
            and contract.forbidden_behavior
            and not (contract_categories[contract.contract_id] & NEGATIVE_CATEGORIES)
        ):
            findings.append(
                _finding(
                    ValidationSeverity.WARNING,
                    "forbidden_behavior_without_negative_case",
                    f"contract {contract.contract_id} has forbidden behavior without "
                    "a negative case",
                    contract.contract_id,
                )
            )

        if contract.criticality is Criticality.CRITICAL and len(
            contract_categories[contract.contract_id]
        ) == 1:
            findings.append(
                _finding(
                    ValidationSeverity.WARNING,
                    "critical_contract_single_category",
                    f"critical contract {contract.contract_id} has only one case category",
                    contract.contract_id,
                )
            )

    for gate in gates:
        is_boolean = gate.metric in BOOLEAN_METRICS
        expected_type = bool if is_boolean else (int, float)
        if not isinstance(gate.threshold, expected_type) or (
            not is_boolean and isinstance(gate.threshold, bool)
        ):
            findings.append(
                _finding(
                    ValidationSeverity.ERROR,
                    "invalid_gate_threshold",
                    f"gate {gate.gate_id} has an invalid threshold for {gate.metric.value}",
                    gate.gate_id,
                )
            )
        allowed_operators = BOOLEAN_OPERATORS if is_boolean else NUMERIC_OPERATORS
        if gate.operator not in allowed_operators:
            findings.append(
                _finding(
                    ValidationSeverity.ERROR,
                    "invalid_gate_operator",
                    f"gate {gate.gate_id} cannot use {gate.operator.value} with "
                    f"{gate.metric.value}",
                    gate.gate_id,
                )
            )
        if gate.scope.kind is GateScopeKind.CASE:
            unknown = set(gate.scope.ids) - case_ids
        elif gate.scope.kind is GateScopeKind.CONTRACT:
            unknown = set(gate.scope.ids) - contract_ids
        else:
            unknown = set()
        if unknown:
            findings.append(
                _finding(
                    ValidationSeverity.ERROR,
                    "invalid_gate_scope",
                    f"gate {gate.gate_id} scope references unknown ids: "
                    f"{', '.join(sorted(unknown))}",
                    gate.gate_id,
                )
            )

        if gate.scope.kind is GateScopeKind.RUN:
            scoped_cases = cases
        elif gate.scope.kind is GateScopeKind.CASE:
            scoped_cases = [case_by_id[item] for item in gate.scope.ids if item in case_by_id]
        else:
            scoped_contracts = set(gate.scope.ids)
            scoped_cases = [
                case for case in cases if scoped_contracts.intersection(case.contract_ids)
            ]
        if gate.metric in BOOLEAN_METRICS and not any(
            case.criticality is Criticality.CRITICAL for case in scoped_cases
        ):
            findings.append(
                _finding(
                    ValidationSeverity.ERROR,
                    "unreachable_gate_metric",
                    f"gate {gate.gate_id} has no critical case in scope",
                    gate.gate_id,
                )
            )

    return ValidationReport(findings=findings)
