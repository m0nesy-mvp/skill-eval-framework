"""Deterministic cross-object validation for frozen Benchmark Definitions."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import cast

from skill_eval_framework.schemas.common import ResultSemantic
from skill_eval_framework.schemas.definition import (
    BenchmarkDefinition,
    Contract,
    EvidenceSpecification,
    GateBasedAcceptancePolicy,
    GateSpecification,
    GraderResultGateCondition,
    GraderSpecification,
    GraderTarget,
    MetricAvailabilityGateCondition,
    MetricSpecification,
    MetricThresholdGateCondition,
    Requirement,
    TestCase,
    WeightedNormalizedMeanOverallScorePolicy,
)
from skill_eval_framework.schemas.definition_v03 import (
    BenchmarkDefinitionV03,
    GateSpecificationV03,
    GraderResultGateConditionV03,
    MetricSpecificationV03,
)

from .common import IssueCollector, ValidationReport, group_by, unique_items

type AssertionKey = tuple[str, str]
type SupportedBenchmarkDefinition = BenchmarkDefinition | BenchmarkDefinitionV03
type SupportedMetricSpecification = MetricSpecification | MetricSpecificationV03
type SupportedGateSpecification = GateSpecification | GateSpecificationV03


@dataclass(frozen=True, slots=True)
class AuthoritativeGraderTarget:
    """Resolved Definition-time owner of one ExpectedAssertion pair."""

    grader: GraderSpecification
    target: GraderTarget


@dataclass(frozen=True, slots=True)
class DefinitionIndex:
    """Read-only lookup index; not a Core Object or serialization model."""

    requirements: dict[str, Requirement]
    contracts: dict[str, Contract]
    test_cases: dict[str, TestCase]
    assertion_pairs: frozenset[AssertionKey]
    evidence_specifications: dict[str, EvidenceSpecification]
    grader_specifications: dict[str, GraderSpecification]
    grader_targets: dict[AssertionKey, tuple[AuthoritativeGraderTarget, ...]]
    metric_specifications: dict[str, SupportedMetricSpecification]
    gate_specifications: dict[str, SupportedGateSpecification]


def _stable_pair(test_case_id: str, contract_id: str) -> str:
    return f"{test_case_id}/{contract_id}"


def _report_namespace_duplicates[T](
    collector: IssueCollector,
    items: Sequence[T],
    key: Callable[[T], str],
    *,
    code: str,
    path_prefix: str,
    label: str,
) -> None:
    for item_id, group in group_by(items, key).items():
        if len(group) > 1:
            collector.add(
                code,
                f"{label} ID {item_id!r} is duplicated within its namespace.",
                f"{path_prefix}[{item_id}]",
            )


def build_definition_index(benchmark: SupportedBenchmarkDefinition) -> DefinitionIndex:
    """Build unambiguous graph lookups without validating or mutating the Definition."""

    requirements = unique_items(group_by(benchmark.requirements, lambda item: item.requirement_id))
    contracts = unique_items(group_by(benchmark.contracts, lambda item: item.contract_id))
    test_cases = unique_items(group_by(benchmark.test_cases, lambda item: item.test_case_id))
    evidence_specifications = unique_items(
        group_by(benchmark.evidence_specifications, lambda item: item.evidence_spec_id)
    )
    grader_specifications = unique_items(
        group_by(benchmark.grader_specifications, lambda item: item.grader_id)
    )
    metric_items = cast(Sequence[SupportedMetricSpecification], benchmark.metric_specifications)
    gate_items = cast(Sequence[SupportedGateSpecification], benchmark.gate_specifications)
    metric_specifications = unique_items(group_by(metric_items, lambda item: item.metric_id))
    gate_specifications = unique_items(group_by(gate_items, lambda item: item.gate_id))

    assertion_pairs = frozenset(
        (test_case.test_case_id, assertion.contract_id)
        for test_case in test_cases.values()
        for assertion in test_case.expected_assertions
    )
    target_groups: dict[AssertionKey, list[AuthoritativeGraderTarget]] = defaultdict(list)
    for grader in grader_specifications.values():
        for target in grader.targets:
            target_groups[(target.test_case_id, target.contract_id)].append(
                AuthoritativeGraderTarget(grader=grader, target=target)
            )

    return DefinitionIndex(
        requirements=requirements,
        contracts=contracts,
        test_cases=test_cases,
        assertion_pairs=assertion_pairs,
        evidence_specifications=evidence_specifications,
        grader_specifications=grader_specifications,
        grader_targets={key: tuple(value) for key, value in target_groups.items()},
        metric_specifications=metric_specifications,
        gate_specifications=gate_specifications,
    )


def _validate_definition_graph(benchmark: SupportedBenchmarkDefinition) -> ValidationReport:
    """Validate deterministic references, coverage, and namespace integrity."""

    collector = IssueCollector()
    _validate_namespaces(benchmark, collector)
    index = build_definition_index(benchmark)
    _validate_contracts(benchmark, index, collector)
    _validate_test_cases(benchmark, index, collector)
    _validate_evidence(benchmark, index, collector)
    _validate_graders(benchmark, index, collector)
    _validate_metrics(benchmark, index, collector)
    _validate_gates(benchmark, index, collector)
    _validate_policies(benchmark, index, collector)
    _validate_resources(benchmark, collector)
    return collector.report()


def validate_benchmark_definition_v02(benchmark: BenchmarkDefinition) -> ValidationReport:
    """Validate an explicitly selected historical v0.2 Definition."""

    if not isinstance(benchmark, BenchmarkDefinition):
        raise TypeError("validate_benchmark_definition_v02 requires a v0.2 Definition")
    return _validate_definition_graph(benchmark)


def validate_benchmark_definition_v03(benchmark: BenchmarkDefinitionV03) -> ValidationReport:
    """Validate an explicitly selected executable-policy v0.3 Definition."""

    if not isinstance(benchmark, BenchmarkDefinitionV03):
        raise TypeError("validate_benchmark_definition_v03 requires a v0.3 Definition")
    return _validate_definition_graph(benchmark)


def validate_benchmark_definition(benchmark: SupportedBenchmarkDefinition) -> ValidationReport:
    """Dispatch explicitly by the concrete versioned Definition model."""

    if isinstance(benchmark, BenchmarkDefinitionV03):
        return validate_benchmark_definition_v03(benchmark)
    if isinstance(benchmark, BenchmarkDefinition):
        return validate_benchmark_definition_v02(benchmark)
    raise TypeError("benchmark must be an explicit v0.2 or v0.3 BenchmarkDefinition")


def _validate_namespaces(
    benchmark: SupportedBenchmarkDefinition,
    collector: IssueCollector,
) -> None:
    metric_items = cast(Sequence[SupportedMetricSpecification], benchmark.metric_specifications)
    gate_items = cast(Sequence[SupportedGateSpecification], benchmark.gate_specifications)
    _report_namespace_duplicates(
        collector,
        benchmark.requirements,
        lambda item: item.requirement_id,
        code="DEF_DUPLICATE_REQUIREMENT_ID",
        path_prefix="requirements",
        label="Requirement",
    )
    _report_namespace_duplicates(
        collector,
        benchmark.contracts,
        lambda item: item.contract_id,
        code="DEF_DUPLICATE_CONTRACT_ID",
        path_prefix="contracts",
        label="Contract",
    )
    _report_namespace_duplicates(
        collector,
        benchmark.test_cases,
        lambda item: item.test_case_id,
        code="DEF_DUPLICATE_TEST_CASE_ID",
        path_prefix="test_cases",
        label="TestCase",
    )
    _report_namespace_duplicates(
        collector,
        benchmark.evidence_specifications,
        lambda item: item.evidence_spec_id,
        code="DEF_DUPLICATE_EVIDENCE_SPEC_ID",
        path_prefix="evidence_specifications",
        label="EvidenceSpecification",
    )
    _report_namespace_duplicates(
        collector,
        benchmark.grader_specifications,
        lambda item: item.grader_id,
        code="DEF_DUPLICATE_GRADER_ID",
        path_prefix="grader_specifications",
        label="GraderSpecification",
    )
    _report_namespace_duplicates(
        collector,
        metric_items,
        lambda item: item.metric_id,
        code="DEF_DUPLICATE_METRIC_ID",
        path_prefix="metric_specifications",
        label="MetricSpecification",
    )
    _report_namespace_duplicates(
        collector,
        gate_items,
        lambda item: item.gate_id,
        code="DEF_DUPLICATE_GATE_ID",
        path_prefix="gate_specifications",
        label="GateSpecification",
    )


def _validate_contracts(
    benchmark: SupportedBenchmarkDefinition,
    index: DefinitionIndex,
    collector: IssueCollector,
) -> None:
    covered_requirements: set[str] = set()
    for contract in benchmark.contracts:
        path = f"contracts[{contract.contract_id}]"
        for requirement_id in contract.requirement_ids:
            requirement = index.requirements.get(requirement_id)
            if requirement is None:
                collector.add(
                    "DEF_UNKNOWN_REQUIREMENT_REF",
                    f"Contract {contract.contract_id!r} references unknown or ambiguous "
                    f"Requirement {requirement_id!r}.",
                    f"{path}.requirement_ids[{requirement_id}]",
                    (f"requirement:{requirement_id}",),
                )
                continue
            covered_requirements.add(requirement_id)
            if contract.evaluation_type != requirement.evaluation_type:
                collector.add(
                    "DEF_CONTRACT_EVALUATION_TYPE_MISMATCH",
                    f"Contract {contract.contract_id!r} evaluation_type "
                    f"{contract.evaluation_type.value!r} does not match Requirement "
                    f"{requirement_id!r} evaluation_type {requirement.evaluation_type.value!r}.",
                    f"{path}.evaluation_type",
                    (f"requirement:{requirement_id}",),
                )
    for requirement in benchmark.requirements:
        if requirement.requirement_id not in covered_requirements:
            collector.add(
                "DEF_REQUIREMENT_UNCOVERED",
                f"Requirement {requirement.requirement_id!r} is not covered by any Contract.",
                f"requirements[{requirement.requirement_id}]",
            )


def _validate_test_cases(
    benchmark: SupportedBenchmarkDefinition,
    index: DefinitionIndex,
    collector: IssueCollector,
) -> None:
    covered_contracts: set[str] = set()
    for test_case in benchmark.test_cases:
        for assertion in test_case.expected_assertions:
            pair = _stable_pair(test_case.test_case_id, assertion.contract_id)
            if assertion.contract_id not in index.contracts:
                collector.add(
                    "DEF_UNKNOWN_CONTRACT_REF",
                    f"ExpectedAssertion {pair!r} references an unknown or ambiguous Contract.",
                    f"test_cases[{test_case.test_case_id}].expected_assertions[{assertion.contract_id}]",
                    (f"contract:{assertion.contract_id}",),
                )
            else:
                covered_contracts.add(assertion.contract_id)
    for contract in benchmark.contracts:
        if contract.contract_id not in covered_contracts:
            collector.add(
                "DEF_CONTRACT_UNCOVERED",
                f"Contract {contract.contract_id!r} is not exercised by any ExpectedAssertion.",
                f"contracts[{contract.contract_id}]",
            )


def _validate_evidence(
    benchmark: SupportedBenchmarkDefinition,
    index: DefinitionIndex,
    collector: IssueCollector,
) -> None:
    covered_pairs: set[AssertionKey] = set()
    for specification in benchmark.evidence_specifications:
        for target in specification.targets:
            key = (target.test_case_id, target.contract_id)
            pair = _stable_pair(*key)
            if key not in index.assertion_pairs:
                collector.add(
                    "DEF_EVIDENCE_TARGET_INVALID",
                    f"EvidenceSpecification {specification.evidence_spec_id!r} target {pair!r} "
                    "does not resolve to an ExpectedAssertion pair.",
                    f"evidence_specifications[{specification.evidence_spec_id}].targets[{pair}]",
                    (f"test_case:{target.test_case_id}", f"contract:{target.contract_id}"),
                )
            else:
                covered_pairs.add(key)
    for key in index.assertion_pairs:
        if key not in covered_pairs:
            pair = _stable_pair(*key)
            collector.add(
                "DEF_EVIDENCE_COVERAGE_MISSING",
                f"ExpectedAssertion pair {pair!r} has no EvidenceSpecification coverage.",
                f"expected_assertions[{pair}]",
            )


def _validate_graders(
    benchmark: SupportedBenchmarkDefinition,
    index: DefinitionIndex,
    collector: IssueCollector,
) -> None:
    for grader in benchmark.grader_specifications:
        for target in grader.targets:
            key = (target.test_case_id, target.contract_id)
            pair = _stable_pair(*key)
            path = f"grader_specifications[{grader.grader_id}].targets[{pair}]"
            if key not in index.assertion_pairs:
                collector.add(
                    "DEF_GRADER_TARGET_INVALID",
                    f"Grader target {pair!r} does not resolve to an ExpectedAssertion pair.",
                    path,
                )
            for evidence_spec_id in target.evidence_spec_ids:
                specification = index.evidence_specifications.get(evidence_spec_id)
                if specification is None:
                    collector.add(
                        "DEF_UNKNOWN_EVIDENCE_SPEC_REF",
                        f"Grader {grader.grader_id!r} references unknown or ambiguous "
                        f"EvidenceSpecification {evidence_spec_id!r}.",
                        f"{path}.evidence_spec_ids[{evidence_spec_id}]",
                    )
                    continue
                specification_targets = {
                    (item.test_case_id, item.contract_id) for item in specification.targets
                }
                if key not in specification_targets:
                    collector.add(
                        "DEF_GRADER_EVIDENCE_TARGET_MISMATCH",
                        f"EvidenceSpecification {evidence_spec_id!r} does not cover Grader "
                        f"target {pair!r}.",
                        f"{path}.evidence_spec_ids[{evidence_spec_id}]",
                    )
    for key in index.assertion_pairs:
        owners = index.grader_targets.get(key, ())
        pair = _stable_pair(*key)
        if not owners:
            collector.add(
                "DEF_GRADER_COVERAGE_MISSING",
                f"ExpectedAssertion pair {pair!r} has no authoritative GraderTarget.",
                f"expected_assertions[{pair}]",
            )
        elif len(owners) > 1:
            collector.add(
                "DEF_GRADER_COVERAGE_DUPLICATE",
                f"ExpectedAssertion pair {pair!r} has {len(owners)} GraderTargets; "
                "exactly one is required.",
                f"expected_assertions[{pair}]",
                tuple(f"grader:{owner.grader.grader_id}" for owner in owners),
            )


def _validate_metrics(
    benchmark: SupportedBenchmarkDefinition,
    index: DefinitionIndex,
    collector: IssueCollector,
) -> None:
    for metric in benchmark.metric_specifications:
        for metric_input in metric.inputs:
            key = (metric_input.test_case_id, metric_input.contract_id)
            pair = _stable_pair(*key)
            path = f"metric_specifications[{metric.metric_id}].inputs[{pair}]"
            if key not in index.assertion_pairs:
                collector.add(
                    "DEF_METRIC_INPUT_INVALID",
                    f"Metric input {pair!r} does not resolve to an ExpectedAssertion pair.",
                    path,
                )
                continue
            owners = index.grader_targets.get(key, ())
            if len(owners) != 1:
                collector.add(
                    "DEF_METRIC_GRADER_RESOLUTION_INVALID",
                    f"Metric input {pair!r} resolves to {len(owners)} GraderTargets; "
                    "exactly one is required.",
                    path,
                )
            elif isinstance(metric, MetricSpecificationV03):
                _validate_v03_metric_semantics(metric, owners, collector)


def _supported_result_semantics(grader: GraderSpecification) -> frozenset[ResultSemantic]:
    """Return canonical semantics that the Grader can actually emit."""

    supported = {
        ResultSemantic.SATISFIED,
        ResultSemantic.VIOLATED,
        ResultSemantic.INSUFFICIENT_EVIDENCE,
    }
    if grader.result_semantics.not_exercised is not None:
        supported.add(ResultSemantic.NOT_EXERCISED)
    return frozenset(supported)


def _validate_v03_metric_semantics(
    metric: MetricSpecificationV03,
    owners: tuple[AuthoritativeGraderTarget, ...],
    collector: IssueCollector,
) -> None:
    declared = metric.execution_policy.eligibility.eligible_semantics
    mapped = metric.execution_policy.contribution_mapping
    for owner in owners:
        supported = _supported_result_semantics(owner.grader)
        for semantic in declared:
            if semantic not in supported:
                collector.add(
                    "DEF_V03_METRIC_SEMANTIC_INCOMPATIBLE",
                    f"Metric {metric.metric_id!r} declares eligible semantic "
                    f"{semantic.value!r} not supported by authoritative Grader "
                    f"{owner.grader.grader_id!r}.",
                    f"metric_specifications[{metric.metric_id}].execution_policy"
                    f".eligibility.eligible_semantics[{semantic.value}]",
                    (f"metric:{metric.metric_id}", f"grader:{owner.grader.grader_id}"),
                )
        for rule in mapped:
            if rule.source_semantic not in supported:
                collector.add(
                    "DEF_V03_METRIC_SEMANTIC_INCOMPATIBLE",
                    f"Metric {metric.metric_id!r} maps semantic "
                    f"{rule.source_semantic.value!r} not supported by authoritative "
                    f"Grader {owner.grader.grader_id!r}.",
                    f"metric_specifications[{metric.metric_id}].execution_policy"
                    f".contribution_mapping[{rule.source_semantic.value}]",
                    (f"metric:{metric.metric_id}", f"grader:{owner.grader.grader_id}"),
                )


def _validate_gates(
    benchmark: SupportedBenchmarkDefinition,
    index: DefinitionIndex,
    collector: IssueCollector,
) -> None:
    for gate in benchmark.gate_specifications:
        condition = gate.condition
        if isinstance(condition, (GraderResultGateCondition, GraderResultGateConditionV03)):
            for target in condition.targets:
                key = (target.test_case_id, target.contract_id)
                pair = _stable_pair(*key)
                path = f"gate_specifications[{gate.gate_id}].condition.targets[{pair}]"
                if key not in index.assertion_pairs:
                    collector.add(
                        "DEF_GATE_TARGET_INVALID",
                        f"Gate target {pair!r} does not resolve to an ExpectedAssertion pair.",
                        path,
                    )
                elif len(index.grader_targets.get(key, ())) != 1:
                    collector.add(
                        "DEF_GATE_GRADER_RESOLUTION_INVALID",
                        f"Gate target {pair!r} does not resolve to exactly one GraderTarget.",
                        path,
                    )
                elif isinstance(condition, GraderResultGateConditionV03):
                    _validate_v03_gate_semantics(gate, condition, key, index, collector)
        elif (
            isinstance(
                condition,
                (MetricThresholdGateCondition, MetricAvailabilityGateCondition),
            )
            and condition.metric_id not in index.metric_specifications
        ):
            collector.add(
                "DEF_GATE_UNKNOWN_METRIC_REF",
                f"Gate {gate.gate_id!r} references unknown or ambiguous Metric "
                f"{condition.metric_id!r}.",
                f"gate_specifications[{gate.gate_id}].condition.metric_id",
            )


def _validate_v03_gate_semantics(
    gate: SupportedGateSpecification,
    condition: GraderResultGateConditionV03,
    key: AssertionKey,
    index: DefinitionIndex,
    collector: IssueCollector,
) -> None:
    owners = index.grader_targets.get(key, ())
    if len(owners) != 1:
        return
    supported = _supported_result_semantics(owners[0].grader)
    for semantic in condition.trigger_result_semantics:
        if semantic not in supported:
            collector.add(
                "DEF_V03_GATE_TRIGGER_SEMANTIC_INCOMPATIBLE",
                f"Gate {gate.gate_id!r} triggers on semantic {semantic.value!r} not "
                f"supported by authoritative Grader {owners[0].grader.grader_id!r}.",
                f"gate_specifications[{gate.gate_id}].condition"
                f".trigger_result_semantics[{semantic.value}]",
                (f"gate:{gate.gate_id}", f"grader:{owners[0].grader.grader_id}"),
            )


def _validate_policies(
    benchmark: SupportedBenchmarkDefinition,
    index: DefinitionIndex,
    collector: IssueCollector,
) -> None:
    overall_policy = benchmark.overall_score_policy
    if isinstance(overall_policy, WeightedNormalizedMeanOverallScorePolicy):
        for overall_contribution in overall_policy.metric_contributions:
            if overall_contribution.metric_id not in index.metric_specifications:
                collector.add(
                    "DEF_OVERALL_UNKNOWN_METRIC_REF",
                    f"Overall policy references unknown or ambiguous Metric "
                    f"{overall_contribution.metric_id!r}.",
                    f"overall_score_policy.metric_contributions[{overall_contribution.metric_id}]",
                )
    acceptance_policy = benchmark.acceptance_policy
    if isinstance(acceptance_policy, GateBasedAcceptancePolicy):
        for gate_contribution in acceptance_policy.participating_gates:
            if gate_contribution.gate_id not in index.gate_specifications:
                collector.add(
                    "DEF_ACCEPTANCE_UNKNOWN_GATE_REF",
                    f"Acceptance policy references unknown or ambiguous Gate "
                    f"{gate_contribution.gate_id!r}.",
                    f"acceptance_policy.participating_gates[{gate_contribution.gate_id}]",
                )


def _validate_resources(
    benchmark: SupportedBenchmarkDefinition,
    collector: IssueCollector,
) -> None:
    groups = group_by(
        benchmark.semantic_resource_bindings,
        lambda binding: str(binding.resource_ref),
    )
    for resource_ref, group in groups.items():
        if len(group) > 1:
            collector.add(
                "DEF_DUPLICATE_RESOURCE_REF",
                f"Semantic resource_ref {resource_ref!r} is duplicated.",
                f"semantic_resource_bindings[{resource_ref}]",
            )
