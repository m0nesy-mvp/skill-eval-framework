"""Deterministic cross-object validation for Runtime and Result graphs."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Hashable, Sequence
from typing import Protocol

from skill_eval_framework.schemas.definition import (
    BenchmarkDefinition,
    DisabledAcceptancePolicy,
    DisabledOverallScorePolicy,
    GateBasedAcceptancePolicy,
    GraderResultGateCondition,
    MetricAvailabilityGateCondition,
    MetricThresholdGateCondition,
    WeightedNormalizedMeanOverallScorePolicy,
)
from skill_eval_framework.schemas.results import (
    AcceptanceEvaluationStatus,
    ExpectedApplicationRef,
    ExpectedEpisodeApplicationRef,
    ExpectedGateApplicationRef,
    ExpectedGraderApplicationRef,
    ExpectedMetricApplicationRef,
    GateResult,
    GraderResult,
    MetricResult,
    MissingApplicationRecord,
    OverallEvaluationStatus,
    Scorecard,
    ScorecardFinalizationStatus,
)
from skill_eval_framework.schemas.runtime import (
    Artifact,
    DiagnosticPhase,
    Episode,
    EpisodeExecutionStatus,
    Evidence,
    EvidenceSourceType,
    ObjectType,
    Run,
    RunTestCaseDisposition,
    RuntimeDiagnostic,
    RunValidityStatus,
)

from .common import IssueCollector, ValidationReport, group_by, unique_items
from .definition import AssertionKey, DefinitionIndex, build_definition_index


class _RunOwned(Protocol):
    run_id: str


def _application_sort_key(application: ExpectedApplicationRef) -> tuple[str, ...]:
    if isinstance(application, ExpectedEpisodeApplicationRef):
        return ("episode", application.test_case_id, f"{application.attempt_index:020d}")
    if isinstance(application, ExpectedGraderApplicationRef):
        return (
            "grader_result",
            application.episode_id,
            application.grader_id,
            application.test_case_id,
            application.contract_id,
        )
    if isinstance(application, ExpectedMetricApplicationRef):
        return ("metric_result", application.metric_id)
    return ("gate_result", application.gate_id)


def derive_expected_episode_applications(run: Run) -> tuple[ExpectedEpisodeApplicationRef, ...]:
    """Derive Episode identities solely from scheduled plan slots."""

    applications = [
        ExpectedEpisodeApplicationRef(
            application_type="episode",
            test_case_id=test_case.test_case_id,
            attempt_index=slot.attempt_index,
        )
        for test_case in run.execution_plan.test_cases
        if test_case.disposition == RunTestCaseDisposition.SCHEDULED
        for slot in test_case.attempt_slots
    ]
    return tuple(sorted(applications, key=_application_sort_key))


def derive_expected_grader_applications(
    benchmark: BenchmarkDefinition,
    episodes: Sequence[Episode],
) -> tuple[ExpectedGraderApplicationRef, ...]:
    """Derive completed-Episode Grader identities from authoritative Definition coverage."""

    index = build_definition_index(benchmark)
    applications: list[ExpectedGraderApplicationRef] = []
    for episode in episodes:
        if episode.execution_status != EpisodeExecutionStatus.COMPLETED:
            continue
        test_case = index.test_cases.get(episode.test_case_id)
        if test_case is None:
            continue
        for assertion in test_case.expected_assertions:
            owners = index.grader_targets.get((test_case.test_case_id, assertion.contract_id), ())
            if len(owners) != 1:
                continue
            applications.append(
                ExpectedGraderApplicationRef(
                    application_type="grader_result",
                    episode_id=episode.episode_id,
                    grader_id=owners[0].grader.grader_id,
                    test_case_id=test_case.test_case_id,
                    contract_id=assertion.contract_id,
                )
            )
    return tuple(sorted(applications, key=_application_sort_key))


def derive_expected_metric_applications(
    benchmark: BenchmarkDefinition,
) -> tuple[ExpectedMetricApplicationRef, ...]:
    """Derive one expected application for every Frozen MetricSpecification."""

    applications = [
        ExpectedMetricApplicationRef(application_type="metric_result", metric_id=metric.metric_id)
        for metric in benchmark.metric_specifications
    ]
    return tuple(sorted(applications, key=_application_sort_key))


def derive_expected_gate_applications(
    benchmark: BenchmarkDefinition,
) -> tuple[ExpectedGateApplicationRef, ...]:
    """Derive all Gate applications independently of Acceptance participation."""

    applications = [
        ExpectedGateApplicationRef(application_type="gate_result", gate_id=gate.gate_id)
        for gate in benchmark.gate_specifications
    ]
    return tuple(sorted(applications, key=_application_sort_key))


def derive_expected_applications(
    benchmark: BenchmarkDefinition,
    run: Run,
    episodes: Sequence[Episode],
) -> tuple[ExpectedApplicationRef, ...]:
    """Compose the four Frozen expected-application identity sets."""

    applications: list[ExpectedApplicationRef] = []
    applications.extend(derive_expected_episode_applications(run))
    applications.extend(derive_expected_grader_applications(benchmark, episodes))
    applications.extend(derive_expected_metric_applications(benchmark))
    applications.extend(derive_expected_gate_applications(benchmark))
    return tuple(sorted(applications, key=_application_sort_key))


def _actual_application_keys(
    episodes: Sequence[Episode],
    grader_results: Sequence[GraderResult],
    metric_results: Sequence[MetricResult],
    gate_results: Sequence[GateResult],
) -> set[tuple[Hashable, ...]]:
    keys: set[tuple[Hashable, ...]] = set()
    keys.update(("episode", item.test_case_id, item.attempt_index) for item in episodes)
    keys.update(
        (
            "grader_result",
            item.episode_id,
            item.grader_id,
            item.test_case_id,
            item.contract_id,
        )
        for item in grader_results
    )
    keys.update(("metric_result", item.metric_id) for item in metric_results)
    keys.update(("gate_result", item.gate_id) for item in gate_results)
    return keys


def derive_missing_applications(
    expected: Sequence[ExpectedApplicationRef],
    episodes: Sequence[Episode],
    grader_results: Sequence[GraderResult],
    metric_results: Sequence[MetricResult],
    gate_results: Sequence[GateResult],
) -> tuple[MissingApplicationRecord, ...]:
    """Return new typed records for expected identities that lack actual objects.

    The caller controls lifecycle timing. This pure helper does not infer that an active
    Run is final and does not mutate a Scorecard or Run.
    """

    actual_keys = _actual_application_keys(
        episodes,
        grader_results,
        metric_results,
        gate_results,
    )
    missing = [
        MissingApplicationRecord(
            application_ref=application,
            diagnostic_ids=[],
            explanation=(
                "Expected application has no actual object in the supplied final inventory."
            ),
        )
        for application in expected
        if application.logical_key not in actual_keys
    ]
    return tuple(sorted(missing, key=lambda record: _application_sort_key(record.application_ref)))


def _report_duplicate_ids[T](
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
                f"{label} ID {item_id!r} is duplicated in the Run graph.",
                f"{path_prefix}[{item_id}]",
            )


def _report_duplicate_logical_keys[T](
    collector: IssueCollector,
    items: Sequence[T],
    key: Callable[[T], Hashable],
    *,
    code: str,
    path_prefix: str,
    label: str,
) -> None:
    groups: dict[Hashable, list[T]] = defaultdict(list)
    for item in items:
        groups[key(item)].append(item)
    for logical_key, group in groups.items():
        if len(group) > 1:
            collector.add(
                code,
                f"{label} logical key {logical_key!r} occurs {len(group)} times.",
                f"{path_prefix}[{logical_key!r}]",
            )


def validate_run_graph(
    benchmark: BenchmarkDefinition,
    run: Run,
    episodes: Sequence[Episode] = (),
    artifacts: Sequence[Artifact] = (),
    evidence: Sequence[Evidence] = (),
    grader_results: Sequence[GraderResult] = (),
    metric_results: Sequence[MetricResult] = (),
    gate_results: Sequence[GateResult] = (),
    diagnostics: Sequence[RuntimeDiagnostic] = (),
    scorecard: Scorecard | None = None,
) -> ValidationReport:
    """Validate one Benchmark/Run graph without executing evaluation semantics."""

    collector = IssueCollector()
    index = build_definition_index(benchmark)
    groups = _RuntimeGroups(
        episodes=group_by(episodes, lambda item: str(item.episode_id)),
        artifacts=group_by(artifacts, lambda item: str(item.artifact_id)),
        evidence=group_by(evidence, lambda item: str(item.evidence_id)),
        grader_results=group_by(grader_results, lambda item: str(item.grader_result_id)),
        metric_results=group_by(metric_results, lambda item: str(item.metric_result_id)),
        gate_results=group_by(gate_results, lambda item: str(item.gate_result_id)),
        diagnostics=group_by(diagnostics, lambda item: str(item.diagnostic_id)),
    )

    _validate_runtime_identity_uniqueness(
        collector,
        episodes,
        artifacts,
        evidence,
        grader_results,
        metric_results,
        gate_results,
        diagnostics,
    )
    _validate_run_binding_and_plan(benchmark, run, episodes, collector)
    _validate_episodes(run, episodes, collector)
    _validate_artifacts(run, artifacts, groups, collector)
    _validate_evidence(run, evidence, groups, index, collector)
    _validate_declared_runtime_refs(run, episodes, groups, collector)
    _validate_grader_results(run, grader_results, groups, index, collector)
    _validate_metric_results(run, metric_results, groups, index, collector)
    _validate_gate_results(run, gate_results, groups, index, collector)
    _validate_diagnostics(run, diagnostics, groups, collector)
    _validate_declared_diagnostic_refs(run, episodes, scorecard, groups, collector)
    _validate_validity_finding_refs(run, groups, scorecard, collector)
    if scorecard is not None:
        _validate_scorecard(
            benchmark,
            run,
            episodes,
            grader_results,
            metric_results,
            gate_results,
            groups,
            scorecard,
            collector,
        )
    return collector.report()


class _RuntimeGroups:
    def __init__(
        self,
        *,
        episodes: dict[str, tuple[Episode, ...]],
        artifacts: dict[str, tuple[Artifact, ...]],
        evidence: dict[str, tuple[Evidence, ...]],
        grader_results: dict[str, tuple[GraderResult, ...]],
        metric_results: dict[str, tuple[MetricResult, ...]],
        gate_results: dict[str, tuple[GateResult, ...]],
        diagnostics: dict[str, tuple[RuntimeDiagnostic, ...]],
    ) -> None:
        self.episodes = episodes
        self.artifacts = artifacts
        self.evidence = evidence
        self.grader_results = grader_results
        self.metric_results = metric_results
        self.gate_results = gate_results
        self.diagnostics = diagnostics


def _validate_runtime_identity_uniqueness(
    collector: IssueCollector,
    episodes: Sequence[Episode],
    artifacts: Sequence[Artifact],
    evidence: Sequence[Evidence],
    grader_results: Sequence[GraderResult],
    metric_results: Sequence[MetricResult],
    gate_results: Sequence[GateResult],
    diagnostics: Sequence[RuntimeDiagnostic],
) -> None:
    _report_duplicate_ids(
        collector,
        episodes,
        lambda item: str(item.episode_id),
        code="RUN_DUPLICATE_EPISODE_ID",
        path_prefix="episodes",
        label="Episode",
    )
    _report_duplicate_ids(
        collector,
        artifacts,
        lambda item: str(item.artifact_id),
        code="RUN_DUPLICATE_ARTIFACT_ID",
        path_prefix="artifacts",
        label="Artifact",
    )
    _report_duplicate_ids(
        collector,
        evidence,
        lambda item: str(item.evidence_id),
        code="RUN_DUPLICATE_EVIDENCE_ID",
        path_prefix="evidence",
        label="Evidence",
    )
    _report_duplicate_ids(
        collector,
        grader_results,
        lambda item: str(item.grader_result_id),
        code="RUN_DUPLICATE_GRADER_RESULT_ID",
        path_prefix="grader_results",
        label="GraderResult",
    )
    _report_duplicate_ids(
        collector,
        metric_results,
        lambda item: str(item.metric_result_id),
        code="RUN_DUPLICATE_METRIC_RESULT_ID",
        path_prefix="metric_results",
        label="MetricResult",
    )
    _report_duplicate_ids(
        collector,
        gate_results,
        lambda item: str(item.gate_result_id),
        code="RUN_DUPLICATE_GATE_RESULT_ID",
        path_prefix="gate_results",
        label="GateResult",
    )
    _report_duplicate_ids(
        collector,
        diagnostics,
        lambda item: str(item.diagnostic_id),
        code="RUN_DUPLICATE_DIAGNOSTIC_ID",
        path_prefix="diagnostics",
        label="RuntimeDiagnostic",
    )
    _report_duplicate_logical_keys(
        collector,
        episodes,
        lambda item: item.logical_key,
        code="RUN_EPISODE_LOGICAL_DUPLICATE",
        path_prefix="episodes",
        label="Episode",
    )
    _report_duplicate_logical_keys(
        collector,
        grader_results,
        lambda item: item.logical_key,
        code="RUN_GRADER_LOGICAL_DUPLICATE",
        path_prefix="grader_results",
        label="GraderResult",
    )
    _report_duplicate_logical_keys(
        collector,
        metric_results,
        lambda item: item.logical_key,
        code="RUN_METRIC_LOGICAL_DUPLICATE",
        path_prefix="metric_results",
        label="MetricResult",
    )
    _report_duplicate_logical_keys(
        collector,
        gate_results,
        lambda item: item.logical_key,
        code="RUN_GATE_LOGICAL_DUPLICATE",
        path_prefix="gate_results",
        label="GateResult",
    )


def _validate_run_binding_and_plan(
    benchmark: BenchmarkDefinition,
    run: Run,
    episodes: Sequence[Episode],
    collector: IssueCollector,
) -> None:
    if run.definition_ref.benchmark_id != benchmark.benchmark_id:
        collector.add(
            "RUN_DEFINITION_ID_MISMATCH",
            "Run benchmark_id does not match the supplied BenchmarkDefinition.",
            "run.definition_ref.benchmark_id",
        )
    if run.definition_ref.benchmark_version != benchmark.version:
        collector.add(
            "RUN_DEFINITION_VERSION_MISMATCH",
            "Run benchmark_version does not match the supplied BenchmarkDefinition.",
            "run.definition_ref.benchmark_version",
        )
    definition_test_case_ids = {item.test_case_id for item in benchmark.test_cases}
    plan_groups = group_by(
        run.execution_plan.test_cases,
        lambda item: str(item.test_case_id),
    )
    for test_case_id, group in plan_groups.items():
        if len(group) > 1:
            collector.add(
                "RUN_PLAN_TEST_CASE_DUPLICATE",
                f"RunExecutionPlan contains TestCase {test_case_id!r} more than once.",
                f"run.execution_plan.test_cases[{test_case_id}]",
            )
    plan_ids = {item.test_case_id for item in run.execution_plan.test_cases}
    for missing_id in definition_test_case_ids - plan_ids:
        collector.add(
            "RUN_PLAN_TEST_CASE_MISSING",
            f"RunExecutionPlan is missing TestCase {missing_id!r}.",
            f"run.execution_plan.test_cases[{missing_id}]",
        )
    for unknown_id in plan_ids - definition_test_case_ids:
        collector.add(
            "RUN_PLAN_TEST_CASE_UNKNOWN",
            f"RunExecutionPlan contains unknown TestCase {unknown_id!r}.",
            f"run.execution_plan.test_cases[{unknown_id}]",
        )
    planned_slots = {
        (test_case.test_case_id, slot.attempt_index)
        for test_case in run.execution_plan.test_cases
        if test_case.disposition == RunTestCaseDisposition.SCHEDULED
        for slot in test_case.attempt_slots
    }
    for episode in episodes:
        if (episode.test_case_id, episode.attempt_index) not in planned_slots:
            collector.add(
                "RUN_UNPLANNED_EPISODE",
                f"Episode {episode.episode_id!r} does not match a scheduled plan slot.",
                f"episodes[{episode.episode_id}]",
            )


def _validate_episodes(run: Run, episodes: Sequence[Episode], collector: IssueCollector) -> None:
    for episode in episodes:
        if episode.run_id != run.run_id:
            collector.add(
                "RUN_CROSS_RUN_REFERENCE",
                f"Episode {episode.episode_id!r} belongs to Run {episode.run_id!r}, "
                f"not {run.run_id!r}.",
                f"episodes[{episode.episode_id}].run_id",
            )


def _validate_artifacts(
    run: Run,
    artifacts: Sequence[Artifact],
    groups: _RuntimeGroups,
    collector: IssueCollector,
) -> None:
    episodes = unique_items(groups.episodes)
    for artifact in artifacts:
        path = f"artifacts[{artifact.artifact_id}]"
        if artifact.run_id != run.run_id:
            collector.add(
                "RUN_CROSS_RUN_REFERENCE",
                f"Artifact {artifact.artifact_id!r} belongs to another Run.",
                f"{path}.run_id",
            )
        for relation in artifact.relations:
            if relation.episode_id is None:
                continue
            episode = episodes.get(relation.episode_id)
            if episode is None:
                collector.add(
                    "RUN_ARTIFACT_EPISODE_UNKNOWN",
                    "Artifact relation references unknown or ambiguous Episode "
                    f"{relation.episode_id!r}.",
                    f"{path}.relations[{relation.episode_id}]",
                )
                continue
            if episode.run_id != run.run_id:
                collector.add(
                    "RUN_CROSS_RUN_REFERENCE",
                    "Artifact relation resolves to an Episode from another Run.",
                    f"{path}.relations[{relation.episode_id}]",
                )
            if relation.trace_event_id is not None and relation.trace_event_id not in {
                event.trace_event_id for event in episode.trace_events
            }:
                collector.add(
                    "RUN_ARTIFACT_TRACE_EVENT_UNKNOWN",
                    f"Artifact relation trace_event_id {relation.trace_event_id!r} does not exist "
                    f"in Episode {episode.episode_id!r}.",
                    f"{path}.relations[{relation.episode_id}].trace_event_id",
                )


def _validate_evidence(
    run: Run,
    evidence_items: Sequence[Evidence],
    groups: _RuntimeGroups,
    index: DefinitionIndex,
    collector: IssueCollector,
) -> None:
    episodes = unique_items(groups.episodes)
    artifacts = unique_items(groups.artifacts)
    for evidence in evidence_items:
        path = f"evidence[{evidence.evidence_id}]"
        if evidence.run_id != run.run_id:
            collector.add(
                "RUN_CROSS_RUN_REFERENCE",
                f"Evidence {evidence.evidence_id!r} belongs to another Run.",
                f"{path}.run_id",
            )
        episode = episodes.get(evidence.episode_id)
        if episode is None:
            collector.add(
                "RUN_EVIDENCE_EPISODE_UNKNOWN",
                f"Evidence references unknown or ambiguous Episode {evidence.episode_id!r}.",
                f"{path}.episode_id",
            )
        elif episode.run_id != run.run_id:
            collector.add(
                "RUN_CROSS_RUN_REFERENCE",
                "Evidence resolves to an Episode from another Run.",
                f"{path}.episode_id",
            )
        specification = index.evidence_specifications.get(evidence.evidence_spec_id)
        if specification is None:
            collector.add(
                "RUN_EVIDENCE_SPEC_UNKNOWN",
                f"Evidence references unknown or ambiguous EvidenceSpecification "
                f"{evidence.evidence_spec_id!r}.",
                f"{path}.evidence_spec_id",
            )
            specification_targets: set[AssertionKey] = set()
        else:
            specification_targets = {
                (target.test_case_id, target.contract_id) for target in specification.targets
            }
        for target in evidence.qualified_targets:
            key = (target.test_case_id, target.contract_id)
            pair = f"{target.test_case_id}/{target.contract_id}"
            if key not in index.assertion_pairs or key not in specification_targets:
                collector.add(
                    "RUN_EVIDENCE_TARGET_INVALID",
                    f"Evidence qualified target {pair!r} is not authorized by its "
                    "Definition target graph.",
                    f"{path}.qualified_targets[{pair}]",
                )
            if episode is not None and target.test_case_id != episode.test_case_id:
                collector.add(
                    "RUN_EVIDENCE_TARGET_EPISODE_MISMATCH",
                    f"Evidence target TestCase {target.test_case_id!r} does not match Episode "
                    f"TestCase {episode.test_case_id!r}.",
                    f"{path}.qualified_targets[{pair}]",
                )
        for source in evidence.provenance.source_refs:
            source_path = f"{path}.provenance.source_refs[{source.source_id}]"
            if source.source_type == EvidenceSourceType.ARTIFACT:
                artifact = artifacts.get(source.source_id)
                if artifact is None:
                    collector.add(
                        "RUN_EVIDENCE_ARTIFACT_SOURCE_UNKNOWN",
                        f"Evidence source Artifact {source.source_id!r} is unknown or ambiguous.",
                        source_path,
                    )
                else:
                    if artifact.run_id != run.run_id:
                        collector.add(
                            "RUN_CROSS_RUN_REFERENCE",
                            "Evidence source Artifact belongs to another Run.",
                            source_path,
                        )
                    related_episode_ids = {
                        relation.episode_id
                        for relation in artifact.relations
                        if relation.episode_id is not None
                    }
                    if evidence.episode_id not in related_episode_ids:
                        collector.add(
                            "RUN_EVIDENCE_ARTIFACT_EPISODE_MISMATCH",
                            "Evidence source Artifact has no relation to the Evidence Episode.",
                            source_path,
                        )
            elif source.source_type == EvidenceSourceType.TRACE_EVENT:
                if episode is None or source.source_id not in {
                    event.trace_event_id for event in episode.trace_events
                }:
                    collector.add(
                        "RUN_EVIDENCE_TRACE_SOURCE_UNKNOWN",
                        f"TraceEvent source {source.source_id!r} does not exist in the "
                        "Evidence Episode.",
                        source_path,
                    )


def _validate_declared_runtime_refs(
    run: Run,
    episodes: Sequence[Episode],
    groups: _RuntimeGroups,
    collector: IssueCollector,
) -> None:
    """Resolve typed object-id lists that are owned by Run or Episode."""

    episode_groups = groups.episodes
    artifact_groups = groups.artifacts
    evidence_groups = groups.evidence
    for episode_id in run.episode_ids:
        episode_matches = episode_groups.get(episode_id, ())
        path = f"run.episode_ids[{episode_id}]"
        if not episode_matches:
            collector.add(
                "RUN_EPISODE_REF_UNKNOWN",
                f"Run references unknown Episode {episode_id!r}.",
                path,
            )
        elif any(item.run_id != run.run_id for item in episode_matches):
            collector.add(
                "RUN_CROSS_RUN_REFERENCE",
                "Run episode_ids contains an Episode from another Run.",
                path,
            )
    for episode in episodes:
        episode_path = f"episodes[{episode.episode_id}]"
        for artifact_id in episode.artifact_ids:
            artifact_matches = artifact_groups.get(artifact_id, ())
            path = f"{episode_path}.artifact_ids[{artifact_id}]"
            if not artifact_matches:
                collector.add(
                    "RUN_EPISODE_ARTIFACT_UNKNOWN",
                    f"Episode references unknown Artifact {artifact_id!r}.",
                    path,
                )
            elif any(item.run_id != run.run_id for item in artifact_matches):
                collector.add(
                    "RUN_CROSS_RUN_REFERENCE",
                    "Episode artifact_ids contains an Artifact from another Run.",
                    path,
                )
        for evidence_id in episode.evidence_ids:
            evidence_matches = evidence_groups.get(evidence_id, ())
            path = f"{episode_path}.evidence_ids[{evidence_id}]"
            if not evidence_matches:
                collector.add(
                    "RUN_EPISODE_EVIDENCE_UNKNOWN",
                    f"Episode references unknown Evidence {evidence_id!r}.",
                    path,
                )
            elif any(item.run_id != run.run_id for item in evidence_matches):
                collector.add(
                    "RUN_CROSS_RUN_REFERENCE",
                    "Episode evidence_ids contains Evidence from another Run.",
                    path,
                )


def _validate_grader_results(
    run: Run,
    grader_results: Sequence[GraderResult],
    groups: _RuntimeGroups,
    index: DefinitionIndex,
    collector: IssueCollector,
) -> None:
    episodes = unique_items(groups.episodes)
    evidence = unique_items(groups.evidence)
    for result in grader_results:
        path = f"grader_results[{result.grader_result_id}]"
        if result.run_id != run.run_id:
            collector.add(
                "RUN_CROSS_RUN_REFERENCE",
                f"GraderResult {result.grader_result_id!r} belongs to another Run.",
                f"{path}.run_id",
            )
        episode = episodes.get(result.episode_id)
        if episode is None:
            collector.add(
                "RUN_GRADER_EPISODE_UNKNOWN",
                f"GraderResult references unknown or ambiguous Episode {result.episode_id!r}.",
                f"{path}.episode_id",
            )
        elif episode.run_id != run.run_id:
            collector.add(
                "RUN_CROSS_RUN_REFERENCE",
                "GraderResult resolves to an Episode from another Run.",
                f"{path}.episode_id",
            )
        elif episode.test_case_id != result.test_case_id:
            collector.add(
                "RUN_GRADER_EPISODE_TARGET_MISMATCH",
                "GraderResult test_case_id does not match its Episode.",
                f"{path}.test_case_id",
            )
        key = (result.test_case_id, result.contract_id)
        owners = index.grader_targets.get(key, ())
        owner = owners[0] if len(owners) == 1 else None
        if owner is None or owner.grader.grader_id != result.grader_id:
            collector.add(
                "RUN_GRADER_TARGET_INVALID",
                "GraderResult does not match the unique authoritative GraderTarget.",
                f"{path}.grader_id",
            )
        allowed_evidence_spec_ids = (
            set(owner.target.evidence_spec_ids) if owner is not None else set()
        )
        for evidence_id in result.evidence_ids:
            item = evidence.get(evidence_id)
            evidence_path = f"{path}.evidence_ids[{evidence_id}]"
            if item is None:
                collector.add(
                    "RUN_GRADER_EVIDENCE_UNKNOWN",
                    f"GraderResult references unknown or ambiguous Evidence {evidence_id!r}.",
                    evidence_path,
                )
                continue
            if item.run_id != run.run_id or item.episode_id != result.episode_id:
                collector.add(
                    "RUN_CROSS_RUN_REFERENCE",
                    "GraderResult Evidence does not belong to the same Run and Episode.",
                    evidence_path,
                )
            qualified_pairs = {
                (target.test_case_id, target.contract_id) for target in item.qualified_targets
            }
            if item.evidence_spec_id not in allowed_evidence_spec_ids or key not in qualified_pairs:
                collector.add(
                    "RUN_GRADER_EVIDENCE_INCOMPATIBLE",
                    f"Evidence {evidence_id!r} is not authorized for this GraderTarget.",
                    evidence_path,
                )


def _validate_metric_results(
    run: Run,
    metric_results: Sequence[MetricResult],
    groups: _RuntimeGroups,
    index: DefinitionIndex,
    collector: IssueCollector,
) -> None:
    grader_results = unique_items(groups.grader_results)
    for result in metric_results:
        path = f"metric_results[{result.metric_result_id}]"
        if result.run_id != run.run_id:
            collector.add(
                "RUN_CROSS_RUN_REFERENCE",
                f"MetricResult {result.metric_result_id!r} belongs to another Run.",
                f"{path}.run_id",
            )
        specification = index.metric_specifications.get(result.metric_id)
        if specification is None:
            collector.add(
                "RUN_METRIC_SPEC_UNKNOWN",
                f"MetricResult references unknown or ambiguous Metric {result.metric_id!r}.",
                f"{path}.metric_id",
            )
            population: set[AssertionKey] = set()
        else:
            population = {(item.test_case_id, item.contract_id) for item in specification.inputs}
        for trace in result.input_traces:
            grader_result = grader_results.get(trace.grader_result_id)
            trace_path = f"{path}.input_traces[{trace.grader_result_id}]"
            if grader_result is None:
                collector.add(
                    "RUN_METRIC_GRADER_RESULT_UNKNOWN",
                    f"Metric input trace references unknown or ambiguous GraderResult "
                    f"{trace.grader_result_id!r}.",
                    trace_path,
                )
                continue
            if grader_result.run_id != run.run_id:
                collector.add(
                    "RUN_CROSS_RUN_REFERENCE",
                    "Metric input trace references a GraderResult from another Run.",
                    trace_path,
                )
            pair = (grader_result.test_case_id, grader_result.contract_id)
            if pair not in population:
                collector.add(
                    "RUN_METRIC_INPUT_OUTSIDE_POPULATION",
                    "Metric input trace GraderResult is outside the Frozen Metric "
                    "input population.",
                    trace_path,
                )
            owners = index.grader_targets.get(pair, ())
            if len(owners) != 1 or owners[0].grader.grader_id != grader_result.grader_id:
                collector.add(
                    "RUN_METRIC_GRADER_TARGET_INVALID",
                    "Metric input trace GraderResult is not the authoritative Grader "
                    "application for its target pair.",
                    trace_path,
                )
        for missing_input in result.missing_inputs:
            if (missing_input.test_case_id, missing_input.contract_id) not in population:
                collector.add(
                    "RUN_METRIC_MISSING_INPUT_OUTSIDE_POPULATION",
                    "MissingMetricInput is outside the Frozen Metric input population.",
                    f"{path}.missing_inputs[{missing_input.test_case_id}/{missing_input.contract_id}]",
                )


def _validate_gate_results(
    run: Run,
    gate_results: Sequence[GateResult],
    groups: _RuntimeGroups,
    index: DefinitionIndex,
    collector: IssueCollector,
) -> None:
    grader_results = unique_items(groups.grader_results)
    metric_results = unique_items(groups.metric_results)
    for result in gate_results:
        path = f"gate_results[{result.gate_result_id}]"
        if result.run_id != run.run_id:
            collector.add(
                "RUN_CROSS_RUN_REFERENCE",
                f"GateResult {result.gate_result_id!r} belongs to another Run.",
                f"{path}.run_id",
            )
        gate = index.gate_specifications.get(result.gate_id)
        if gate is None:
            collector.add(
                "RUN_GATE_SPEC_UNKNOWN",
                f"GateResult references unknown or ambiguous Gate {result.gate_id!r}.",
                f"{path}.gate_id",
            )
            continue
        condition = gate.condition
        if isinstance(condition, GraderResultGateCondition):
            if result.input_summary.condition_type != "grader_result":
                collector.add(
                    "RUN_GATE_SOURCE_TYPE_MISMATCH",
                    "GateResult input_summary type does not match the Grader-result "
                    "Gate condition.",
                    f"{path}.input_summary.condition_type",
                )
            allowed_targets = {(item.test_case_id, item.contract_id) for item in condition.targets}
            for contribution in result.input_summary.grader_contributions:
                target = (contribution.target.test_case_id, contribution.target.contract_id)
                contribution_path = (
                    f"{path}.input_summary.grader_contributions"
                    f"[{contribution.target.test_case_id}/{contribution.target.contract_id}]"
                )
                if target not in allowed_targets:
                    collector.add(
                        "RUN_GATE_GRADER_TARGET_INVALID",
                        "GateResult Grader contribution target is outside the Gate "
                        "condition targets.",
                        contribution_path,
                    )
                if contribution.grader_result_id is not None:
                    grader_result = grader_results.get(contribution.grader_result_id)
                    if grader_result is None:
                        collector.add(
                            "RUN_GATE_GRADER_RESULT_UNKNOWN",
                            "GateResult references an unknown or ambiguous GraderResult.",
                            contribution_path,
                        )
                    elif grader_result.run_id != run.run_id:
                        collector.add(
                            "RUN_CROSS_RUN_REFERENCE",
                            "GateResult references a GraderResult from another Run.",
                            contribution_path,
                        )
                    elif (grader_result.test_case_id, grader_result.contract_id) != target:
                        collector.add(
                            "RUN_GATE_GRADER_RESULT_TARGET_MISMATCH",
                            "GateResult GraderResult does not match its contribution target.",
                            contribution_path,
                        )
        elif isinstance(condition, MetricThresholdGateCondition):
            _validate_metric_gate_source(
                run,
                result,
                condition.metric_id,
                "metric_threshold",
                metric_results,
                collector,
            )
        elif isinstance(condition, MetricAvailabilityGateCondition):
            _validate_metric_gate_source(
                run,
                result,
                condition.metric_id,
                "metric_availability",
                metric_results,
                collector,
            )


def _validate_metric_gate_source(
    run: Run,
    result: GateResult,
    expected_metric_id: str,
    expected_condition_type: str,
    metric_results: dict[str, MetricResult],
    collector: IssueCollector,
) -> None:
    path = f"gate_results[{result.gate_result_id}].input_summary"
    if result.input_summary.condition_type != expected_condition_type:
        collector.add(
            "RUN_GATE_SOURCE_TYPE_MISMATCH",
            "GateResult input_summary type does not match the Frozen Metric Gate condition.",
            f"{path}.condition_type",
        )
    metric_result_id = result.input_summary.metric_result_id
    if metric_result_id is None:
        return
    metric_result = metric_results.get(metric_result_id)
    if metric_result is None:
        collector.add(
            "RUN_GATE_METRIC_RESULT_UNKNOWN",
            f"GateResult references unknown or ambiguous MetricResult {metric_result_id!r}.",
            f"{path}.metric_result_id",
        )
    elif metric_result.run_id != run.run_id:
        collector.add(
            "RUN_CROSS_RUN_REFERENCE",
            "GateResult references a MetricResult from another Run.",
            f"{path}.metric_result_id",
        )
    elif metric_result.metric_id != expected_metric_id:
        collector.add(
            "RUN_GATE_METRIC_RESULT_MISMATCH",
            "GateResult MetricResult does not match the Gate condition metric_id.",
            f"{path}.metric_result_id",
        )


def _validate_diagnostics(
    run: Run,
    diagnostics: Sequence[RuntimeDiagnostic],
    groups: _RuntimeGroups,
    collector: IssueCollector,
) -> None:
    episodes = unique_items(groups.episodes)
    for diagnostic in diagnostics:
        path = f"diagnostics[{diagnostic.diagnostic_id}]"
        if diagnostic.run_id != run.run_id:
            collector.add(
                "RUN_CROSS_RUN_REFERENCE",
                f"RuntimeDiagnostic {diagnostic.diagnostic_id!r} belongs to another Run.",
                f"{path}.run_id",
            )
        if diagnostic.episode_id is not None:
            episode = episodes.get(diagnostic.episode_id)
            if episode is None:
                collector.add(
                    "RUN_DIAGNOSTIC_EPISODE_UNKNOWN",
                    "RuntimeDiagnostic references an unknown or ambiguous Episode.",
                    f"{path}.episode_id",
                )
            elif episode.run_id != run.run_id:
                collector.add(
                    "RUN_CROSS_RUN_REFERENCE",
                    "RuntimeDiagnostic references an Episode from another Run.",
                    f"{path}.episode_id",
                )


def _validate_diagnostic_id_list(
    run: Run,
    diagnostic_ids: Sequence[str],
    path: str,
    groups: _RuntimeGroups,
    collector: IssueCollector,
) -> None:
    diagnostics = unique_items(groups.diagnostics)
    for diagnostic_id in diagnostic_ids:
        diagnostic = diagnostics.get(diagnostic_id)
        if diagnostic is None:
            collector.add(
                "RUN_DIAGNOSTIC_REF_UNKNOWN",
                f"Diagnostic reference {diagnostic_id!r} is unknown or ambiguous.",
                f"{path}[{diagnostic_id}]",
            )
        elif diagnostic.run_id != run.run_id:
            collector.add(
                "RUN_CROSS_RUN_REFERENCE",
                "Diagnostic reference resolves to another Run.",
                f"{path}[{diagnostic_id}]",
            )


def _validate_declared_diagnostic_refs(
    run: Run,
    episodes: Sequence[Episode],
    scorecard: Scorecard | None,
    groups: _RuntimeGroups,
    collector: IssueCollector,
) -> None:
    _validate_diagnostic_id_list(
        run,
        run.diagnostic_ids,
        "run.diagnostic_ids",
        groups,
        collector,
    )
    for episode in episodes:
        _validate_diagnostic_id_list(
            run,
            episode.diagnostic_ids,
            f"episodes[{episode.episode_id}].diagnostic_ids",
            groups,
            collector,
        )
    if scorecard is None:
        return
    _validate_diagnostic_id_list(
        run,
        scorecard.diagnostic_ids,
        f"scorecards[{scorecard.scorecard_id}].diagnostic_ids",
        groups,
        collector,
    )
    for record in scorecard.result_inventory.missing_applications:
        _validate_diagnostic_id_list(
            run,
            record.diagnostic_ids,
            (
                f"scorecards[{scorecard.scorecard_id}].result_inventory"
                f".missing_applications[{record.application_ref.logical_key!r}].diagnostic_ids"
            ),
            groups,
            collector,
        )
    _validate_diagnostic_id_list(
        run,
        scorecard.overall_score_outcome.diagnostic_ids,
        f"scorecards[{scorecard.scorecard_id}].overall_score_outcome.diagnostic_ids",
        groups,
        collector,
    )
    _validate_diagnostic_id_list(
        run,
        scorecard.acceptance_evaluation.diagnostic_ids,
        f"scorecards[{scorecard.scorecard_id}].acceptance_evaluation.diagnostic_ids",
        groups,
        collector,
    )


def _validate_validity_finding_refs(
    run: Run,
    groups: _RuntimeGroups,
    scorecard: Scorecard | None,
    collector: IssueCollector,
) -> None:
    for finding in run.validity_findings:
        for reference in finding.related_object_refs:
            if reference.object_type == ObjectType.RUN and reference.object_ref != run.run_id:
                collector.add(
                    "RUN_VALIDITY_REF_CROSS_RUN",
                    "ValidityFinding references a different Run identity.",
                    f"run.validity_findings[{finding.code}].related_object_refs",
                )
                continue
            resolved_run_ids: list[str] = []
            if reference.object_type == ObjectType.EPISODE:
                resolved_run_ids = [
                    item.run_id for item in groups.episodes.get(reference.object_ref, ())
                ]
            elif reference.object_type == ObjectType.ARTIFACT:
                resolved_run_ids = [
                    item.run_id for item in groups.artifacts.get(reference.object_ref, ())
                ]
            elif reference.object_type == ObjectType.EVIDENCE:
                resolved_run_ids = [
                    item.run_id for item in groups.evidence.get(reference.object_ref, ())
                ]
            elif reference.object_type == ObjectType.GRADER_RESULT:
                resolved_run_ids = [
                    item.run_id for item in groups.grader_results.get(reference.object_ref, ())
                ]
            elif reference.object_type == ObjectType.METRIC_RESULT:
                resolved_run_ids = [
                    item.run_id for item in groups.metric_results.get(reference.object_ref, ())
                ]
            elif reference.object_type == ObjectType.GATE_RESULT:
                resolved_run_ids = [
                    item.run_id for item in groups.gate_results.get(reference.object_ref, ())
                ]
            elif (
                reference.object_type == ObjectType.SCORECARD
                and scorecard is not None
                and reference.object_ref == scorecard.scorecard_id
            ):
                resolved_run_ids = [scorecard.run_id]
            if any(object_run_id != run.run_id for object_run_id in resolved_run_ids):
                collector.add(
                    "RUN_VALIDITY_REF_CROSS_RUN",
                    "ValidityFinding resolves to an object from another Run.",
                    f"run.validity_findings[{finding.code}].related_object_refs",
                )


def _validate_scorecard(
    benchmark: BenchmarkDefinition,
    run: Run,
    episodes: Sequence[Episode],
    grader_results: Sequence[GraderResult],
    metric_results: Sequence[MetricResult],
    gate_results: Sequence[GateResult],
    groups: _RuntimeGroups,
    scorecard: Scorecard,
    collector: IssueCollector,
) -> None:
    path = f"scorecards[{scorecard.scorecard_id}]"
    if scorecard.run_id != run.run_id:
        collector.add(
            "RUN_CROSS_RUN_REFERENCE",
            "Scorecard run_id does not match the supplied Run.",
            f"{path}.run_id",
        )
    if scorecard.definition_ref != run.definition_ref:
        collector.add(
            "RUN_SCORECARD_DEFINITION_REF_MISMATCH",
            "Scorecard definition_ref must exactly match Run.definition_ref.",
            f"{path}.definition_ref",
        )
    if scorecard.subject_ref != run.subject_ref:
        collector.add(
            "RUN_SCORECARD_SUBJECT_REF_MISMATCH",
            "Scorecard subject_ref must exactly match Run.subject_ref.",
            f"{path}.subject_ref",
        )
    _validate_inventory_ids(run, scorecard, groups, collector)
    _validate_overall_refs(benchmark, run, scorecard, groups, collector)
    _validate_acceptance_refs(benchmark, run, scorecard, groups, collector)
    _validate_scorecard_finalization(benchmark, run, scorecard, collector)
    if scorecard.finalization_status != ScorecardFinalizationStatus.INTERIM:
        _validate_final_inventory_closure(
            benchmark,
            run,
            episodes,
            grader_results,
            metric_results,
            gate_results,
            scorecard,
            collector,
        )


def _validate_inventory_ids(
    run: Run,
    scorecard: Scorecard,
    groups: _RuntimeGroups,
    collector: IssueCollector,
) -> None:
    inventory = scorecard.result_inventory
    _validate_inventory_field(
        run,
        scorecard,
        inventory.episode_ids,
        groups.episodes,
        "episode_ids",
        collector,
    )
    _validate_inventory_field(
        run,
        scorecard,
        inventory.grader_result_ids,
        groups.grader_results,
        "grader_result_ids",
        collector,
    )
    _validate_inventory_field(
        run,
        scorecard,
        inventory.metric_result_ids,
        groups.metric_results,
        "metric_result_ids",
        collector,
    )
    _validate_inventory_field(
        run,
        scorecard,
        inventory.gate_result_ids,
        groups.gate_results,
        "gate_result_ids",
        collector,
    )


def _validate_inventory_field[T: _RunOwned](
    run: Run,
    scorecard: Scorecard,
    object_ids: Sequence[str],
    object_groups: dict[str, tuple[T, ...]],
    field_name: str,
    collector: IssueCollector,
) -> None:
    for object_id in object_ids:
        group = object_groups.get(object_id)
        path = f"scorecards[{scorecard.scorecard_id}].result_inventory.{field_name}[{object_id}]"
        if group is None or len(group) != 1:
            collector.add(
                "RUN_INVENTORY_REF_UNKNOWN",
                f"Scorecard inventory reference {object_id!r} is unknown or ambiguous.",
                path,
            )
        elif group[0].run_id != run.run_id:
            collector.add(
                "RUN_CROSS_RUN_REFERENCE",
                "Scorecard inventory reference resolves to another Run.",
                path,
            )


def _validate_scorecard_finalization(
    benchmark: BenchmarkDefinition,
    run: Run,
    scorecard: Scorecard,
    collector: IssueCollector,
) -> None:
    if scorecard.finalization_status != ScorecardFinalizationStatus.FINALIZED_EVALUATION:
        return
    path = f"scorecards[{scorecard.scorecard_id}]"
    if run.validity_status != RunValidityStatus.VALID:
        collector.add(
            "RUN_FINALIZED_EVALUATION_REQUIRES_VALID_RUN",
            "finalized_evaluation requires Run validity_status=valid.",
            f"{path}.finalization_status",
        )
    overall_status = scorecard.overall_score_outcome.evaluation_status
    if isinstance(benchmark.overall_score_policy, DisabledOverallScorePolicy):
        allowed_overall = {OverallEvaluationStatus.DISABLED}
    else:
        allowed_overall = {
            OverallEvaluationStatus.AVAILABLE,
            OverallEvaluationStatus.UNAVAILABLE,
        }
    if overall_status not in allowed_overall:
        collector.add(
            "RUN_FINALIZED_EVALUATION_OVERALL_STATE_INVALID",
            "Overall outcome state is incompatible with finalized_evaluation and its "
            "Frozen policy.",
            f"{path}.overall_score_outcome.evaluation_status",
        )
    acceptance_status = scorecard.acceptance_evaluation.evaluation_status
    if isinstance(benchmark.acceptance_policy, DisabledAcceptancePolicy):
        allowed_acceptance = {AcceptanceEvaluationStatus.DISABLED}
    else:
        allowed_acceptance = {AcceptanceEvaluationStatus.PRODUCED}
    if acceptance_status not in allowed_acceptance:
        collector.add(
            "RUN_FINALIZED_EVALUATION_ACCEPTANCE_STATE_INVALID",
            "Acceptance state is incompatible with finalized_evaluation and its Frozen policy.",
            f"{path}.acceptance_evaluation.evaluation_status",
        )


def _validate_overall_refs(
    benchmark: BenchmarkDefinition,
    run: Run,
    scorecard: Scorecard,
    groups: _RuntimeGroups,
    collector: IssueCollector,
) -> None:
    outcome = scorecard.overall_score_outcome
    path = f"scorecards[{scorecard.scorecard_id}].overall_score_outcome"
    if outcome.policy_ref.definition_digest != run.definition_ref.definition_digest:
        collector.add(
            "RUN_OVERALL_POLICY_DIGEST_MISMATCH",
            "Overall policy_ref digest does not match Run.definition_ref.",
            f"{path}.policy_ref.definition_digest",
        )
    if outcome.policy_ref.policy_path != "/overall_score_policy":
        collector.add(
            "RUN_OVERALL_POLICY_PATH_INVALID",
            "Overall outcome must reference /overall_score_policy.",
            f"{path}.policy_ref.policy_path",
        )
    policy = benchmark.overall_score_policy
    membership = (
        {item.metric_id for item in policy.metric_contributions}
        if isinstance(policy, WeightedNormalizedMeanOverallScorePolicy)
        else set()
    )
    metric_results = unique_items(groups.metric_results)
    for trace in outcome.contribution_traces:
        trace_path = f"{path}.contribution_traces[{trace.metric_id}]"
        if trace.metric_id not in membership:
            collector.add(
                "RUN_OVERALL_METRIC_NOT_PARTICIPATING",
                f"Overall trace Metric {trace.metric_id!r} is not in Frozen policy membership.",
                trace_path,
            )
        if trace.application_state == "missing":
            if trace.metric_result_id is not None:
                collector.add(
                    "RUN_OVERALL_MISSING_HAS_RESULT_REF",
                    "Missing Overall contribution must not include metric_result_id.",
                    f"{trace_path}.metric_result_id",
                )
            continue
        if trace.metric_result_id is None:
            collector.add(
                "RUN_OVERALL_RESULT_REF_MISSING",
                "Available/unavailable Overall contribution requires metric_result_id.",
                f"{trace_path}.metric_result_id",
            )
            continue
        metric_result = metric_results.get(trace.metric_result_id)
        if metric_result is None:
            collector.add(
                "RUN_OVERALL_METRIC_RESULT_UNKNOWN",
                "Overall contribution references unknown or ambiguous MetricResult.",
                f"{trace_path}.metric_result_id",
            )
        elif metric_result.run_id != run.run_id:
            collector.add(
                "RUN_CROSS_RUN_REFERENCE",
                "Overall contribution references a MetricResult from another Run.",
                f"{trace_path}.metric_result_id",
            )
        elif metric_result.metric_id != trace.metric_id:
            collector.add(
                "RUN_OVERALL_METRIC_RESULT_MISMATCH",
                "Overall trace metric_id does not match the referenced MetricResult.",
                f"{trace_path}.metric_result_id",
            )
    if outcome.evaluation_status == OverallEvaluationStatus.PRODUCTION_FAILED:
        _validate_production_diagnostics(
            run,
            scorecard,
            outcome.diagnostic_ids,
            "/overall_score_policy",
            groups,
            path,
            collector,
        )


def _validate_acceptance_refs(
    benchmark: BenchmarkDefinition,
    run: Run,
    scorecard: Scorecard,
    groups: _RuntimeGroups,
    collector: IssueCollector,
) -> None:
    evaluation = scorecard.acceptance_evaluation
    path = f"scorecards[{scorecard.scorecard_id}].acceptance_evaluation"
    if evaluation.policy_ref.definition_digest != run.definition_ref.definition_digest:
        collector.add(
            "RUN_ACCEPTANCE_POLICY_DIGEST_MISMATCH",
            "Acceptance policy_ref digest does not match Run.definition_ref.",
            f"{path}.policy_ref.definition_digest",
        )
    if evaluation.policy_ref.policy_path != "/acceptance_policy":
        collector.add(
            "RUN_ACCEPTANCE_POLICY_PATH_INVALID",
            "Acceptance evaluation must reference /acceptance_policy.",
            f"{path}.policy_ref.policy_path",
        )
    policy = benchmark.acceptance_policy
    participation = (
        {item.gate_id for item in policy.participating_gates}
        if isinstance(policy, GateBasedAcceptancePolicy)
        else set()
    )
    gate_results = unique_items(groups.gate_results)
    for trace in evaluation.gate_contributions:
        trace_path = f"{path}.gate_contributions[{trace.gate_id}]"
        if trace.gate_id not in participation:
            collector.add(
                "RUN_ACCEPTANCE_GATE_NOT_PARTICIPATING",
                f"Acceptance trace Gate {trace.gate_id!r} is not a participating Gate.",
                trace_path,
            )
        if trace.application_state == "MISSING":
            if trace.gate_result_id is not None:
                collector.add(
                    "RUN_ACCEPTANCE_MISSING_HAS_RESULT_REF",
                    "MISSING Acceptance contribution must not include gate_result_id.",
                    f"{trace_path}.gate_result_id",
                )
            continue
        if trace.gate_result_id is None:
            collector.add(
                "RUN_ACCEPTANCE_RESULT_REF_MISSING",
                "Non-MISSING Acceptance contribution requires gate_result_id.",
                f"{trace_path}.gate_result_id",
            )
            continue
        gate_result = gate_results.get(trace.gate_result_id)
        if gate_result is None:
            collector.add(
                "RUN_ACCEPTANCE_GATE_RESULT_UNKNOWN",
                "Acceptance contribution references unknown or ambiguous GateResult.",
                f"{trace_path}.gate_result_id",
            )
        elif gate_result.run_id != run.run_id:
            collector.add(
                "RUN_CROSS_RUN_REFERENCE",
                "Acceptance contribution references a GateResult from another Run.",
                f"{trace_path}.gate_result_id",
            )
        elif gate_result.gate_id != trace.gate_id:
            collector.add(
                "RUN_ACCEPTANCE_GATE_RESULT_MISMATCH",
                "Acceptance trace gate_id does not match the referenced GateResult.",
                f"{trace_path}.gate_result_id",
            )
    if evaluation.evaluation_status == AcceptanceEvaluationStatus.PRODUCTION_FAILED:
        _validate_production_diagnostics(
            run,
            scorecard,
            evaluation.diagnostic_ids,
            "/acceptance_policy",
            groups,
            path,
            collector,
        )


def _validate_production_diagnostics(
    run: Run,
    scorecard: Scorecard,
    diagnostic_ids: Sequence[str],
    policy_path: str,
    groups: _RuntimeGroups,
    path: str,
    collector: IssueCollector,
) -> None:
    diagnostics = unique_items(groups.diagnostics)
    for diagnostic_id in diagnostic_ids:
        diagnostic = diagnostics.get(diagnostic_id)
        if diagnostic is None or diagnostic.run_id != run.run_id:
            continue
        if diagnostic.phase != DiagnosticPhase.SCORECARD:
            collector.add(
                "RUN_PRODUCTION_DIAGNOSTIC_PHASE_INVALID",
                "Production-failure diagnostic must use phase=scorecard.",
                f"{path}.diagnostic_ids[{diagnostic_id}]",
            )
        associated = any(
            (reference.object_type == ObjectType.POLICY and reference.object_ref == policy_path)
            or (
                reference.object_type == ObjectType.SCORECARD
                and reference.object_ref == scorecard.scorecard_id
            )
            for reference in diagnostic.related_object_refs
        )
        if not associated:
            collector.add(
                "RUN_PRODUCTION_DIAGNOSTIC_ASSOCIATION_MISSING",
                "Production-failure diagnostic is not directly associated with its "
                "policy or Scorecard.",
                f"{path}.diagnostic_ids[{diagnostic_id}]",
            )


def _validate_final_inventory_closure(
    benchmark: BenchmarkDefinition,
    run: Run,
    episodes: Sequence[Episode],
    grader_results: Sequence[GraderResult],
    metric_results: Sequence[MetricResult],
    gate_results: Sequence[GateResult],
    scorecard: Scorecard,
    collector: IssueCollector,
) -> None:
    expected = derive_expected_applications(benchmark, run, episodes)
    expected_keys = {application.logical_key for application in expected}
    actual_groups: dict[tuple[Hashable, ...], list[str]] = defaultdict(list)
    for episode in episodes:
        actual_groups[("episode", episode.test_case_id, episode.attempt_index)].append(
            episode.episode_id
        )
    for grader_result in grader_results:
        actual_groups[
            (
                "grader_result",
                grader_result.episode_id,
                grader_result.grader_id,
                grader_result.test_case_id,
                grader_result.contract_id,
            )
        ].append(grader_result.grader_result_id)
    for metric_result in metric_results:
        actual_groups[("metric_result", metric_result.metric_id)].append(
            metric_result.metric_result_id
        )
    for gate_result in gate_results:
        actual_groups[("gate_result", gate_result.gate_id)].append(gate_result.gate_result_id)
    missing_groups: dict[tuple[Hashable, ...], list[MissingApplicationRecord]] = defaultdict(list)
    for record in scorecard.result_inventory.missing_applications:
        missing_groups[record.application_ref.logical_key].append(record)

    for application in expected:
        key = application.logical_key
        actual_count = len(actual_groups.get(key, ()))
        missing_count = len(missing_groups.get(key, ()))
        path = f"scorecards[{scorecard.scorecard_id}].result_inventory.applications[{key!r}]"
        if actual_count == 0 and missing_count == 0:
            collector.add(
                "RUN_EXPECTED_APPLICATION_MISSING",
                "Expected application is represented by neither an actual object nor "
                "a missing record.",
                path,
            )
        if actual_count > 0 and missing_count > 0:
            collector.add(
                "RUN_INVENTORY_CONFLICT",
                "Expected application is represented by both actual and missing inventory entries.",
                path,
            )
    for actual_key in actual_groups.keys() - expected_keys:
        collector.add(
            "RUN_UNEXPECTED_ACTUAL_APPLICATION",
            "Actual object does not match any expected application identity.",
            f"scorecards[{scorecard.scorecard_id}].result_inventory.applications[{actual_key!r}]",
        )
    for missing_key in missing_groups.keys() - expected_keys:
        collector.add(
            "RUN_UNEXPECTED_MISSING_APPLICATION",
            "Missing record does not match any expected application identity.",
            f"scorecards[{scorecard.scorecard_id}].result_inventory.applications[{missing_key!r}]",
        )

    inventory = scorecard.result_inventory
    exact_sets = (
        (set(inventory.episode_ids), {item.episode_id for item in episodes}, "episode_ids"),
        (
            set(inventory.grader_result_ids),
            {item.grader_result_id for item in grader_results},
            "grader_result_ids",
        ),
        (
            set(inventory.metric_result_ids),
            {item.metric_result_id for item in metric_results},
            "metric_result_ids",
        ),
        (
            set(inventory.gate_result_ids),
            {item.gate_result_id for item in gate_results},
            "gate_result_ids",
        ),
    )
    for inventory_ids, actual_ids, field_name in exact_sets:
        if inventory_ids != actual_ids:
            collector.add(
                "RUN_INVENTORY_ACTUAL_SET_MISMATCH",
                f"Final Scorecard {field_name} does not exactly match the supplied "
                "actual object set.",
                f"scorecards[{scorecard.scorecard_id}].result_inventory.{field_name}",
                tuple(sorted(inventory_ids ^ actual_ids)),
            )
