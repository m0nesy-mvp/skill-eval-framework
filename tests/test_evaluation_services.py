"""Tests for deterministic evaluation services and explicit v0.3 policy paths."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal

import pytest
from conftest import DIGEST, NOW, make_definition_data
from validation_helpers import complete_runtime_graph

from skill_eval_framework.evaluation import (
    AcceptanceEvaluationError,
    GateEvaluationError,
    MetricEvaluationError,
    OverallEvaluationError,
    calculate_metric_result,
    calculate_overall_score,
    evaluate_acceptance,
    evaluate_gate,
    evaluate_three_valued_quantifier,
)
from skill_eval_framework.schemas.definition import (
    GateBasedAcceptancePolicy,
    LinearBoundedNormalization,
    OverallMetricContribution,
    WeightedNormalizedMeanOverallScorePolicy,
)
from skill_eval_framework.schemas.definition_v03 import (
    BenchmarkDefinitionV03,
    GateSpecificationV03,
    MetricSpecificationV03,
)
from skill_eval_framework.schemas.results import GateEvaluationPath, GraderResult, MetricResult


def _v03_definition() -> BenchmarkDefinitionV03:
    data = deepcopy(make_definition_data())
    metric = data["metric_specifications"][0]
    for field in (
        "result_selection_policy",
        "aggregation_unit",
        "eligibility_policy",
        "contribution_mapping",
        "unit_reduction",
        "aggregation_rule",
        "weighting_policy",
        "completeness_policy",
    ):
        metric.pop(field)
    metric["execution_policy"] = {
        "selection": {"mode": "all_distinct"},
        "eligibility": {
            "eligible_semantics": ["satisfied", "violated"],
            "non_substantive": "exclude_and_trace",
            "missing_input": "unavailable",
        },
        "contribution_mapping": [
            {
                "source_semantic": "satisfied",
                "numeric_value": "1",
                "contribution_unit": "unit_interval",
                "explanation": "Satisfied contributes one.",
            },
            {
                "source_semantic": "violated",
                "numeric_value": "0",
                "contribution_unit": "unit_interval",
                "explanation": "Violated contributes zero.",
            },
        ],
        "aggregation_unit": "per_target",
        "unit_reduction": {"mode": "mean"},
        "weighting": {"mode": "equal_per_unit"},
        "aggregation": {"mode": "mean"},
        "completeness": {"mode": "strict", "empty_denominator": "unavailable"},
    }
    return BenchmarkDefinitionV03.model_validate(data)


def _v03_metric(
    *, selection: str = "all_distinct", reduction: str = "mean", unit: str = "per_target"
) -> MetricSpecificationV03:
    metric = _v03_definition().metric_specifications[0].model_dump(mode="python")
    metric["execution_policy"]["selection"]["mode"] = selection
    if selection in {"first_distinct", "final_distinct_raw"}:
        metric["execution_policy"]["selection"]["order"] = "attempt_index_ascending"
    metric["execution_policy"]["unit_reduction"]["mode"] = reduction
    metric["execution_policy"]["aggregation_unit"] = unit
    return MetricSpecificationV03.model_validate(metric)


def _retry_result(
    graph: object, *, judgment: str, episode_id: str = "E002"
) -> tuple[object, GraderResult]:
    episode = graph.episodes[0].model_copy(update={"episode_id": episode_id, "attempt_index": 2})
    result_data = graph.grader_results[0].model_dump(mode="python")
    result_data.update(
        {"grader_result_id": "GR002", "episode_id": episode_id, "judgment": judgment}
    )
    if judgment == "insufficient_evidence":
        result_data["explanation"].update(
            {"supported_failure_criterion": None, "insufficiency_gaps": ["No decisive evidence."]}
        )
    elif judgment == "violated":
        result_data["explanation"]["supported_failure_criterion"] = "Expected outcome is absent."
    return episode, GraderResult.model_validate(result_data)


def _direct_gate(
    graph: object, *, selection: str = "all_distinct", quantifier: str = "any"
) -> GateSpecificationV03:
    data = {
        "gate_id": "GATE001",
        "name": "Direct semantic gate",
        "scope": "whole benchmark",
        "condition": {
            "condition_type": "grader_result_semantic",
            "targets": [{"test_case_id": "TC001", "contract_id": "C001"}],
            "selection": {"mode": selection},
            "trigger_result_semantics": ["violated"],
            "quantifier": quantifier,
        },
        "unavailable_handling": "indeterminate",
        "result_semantics": graph.benchmark.gate_specifications[0].result_semantics,
        "explanation_requirements": ["Report selected judgments."],
    }
    if selection in {"first_distinct", "final_distinct_raw"}:
        data["condition"]["selection"]["order"] = "attempt_index_ascending"
    return GateSpecificationV03.model_validate(data)


def _metric_with(result: MetricResult, **updates: object) -> MetricResult:
    data = result.model_dump(mode="python")
    data.update(updates)
    return MetricResult.model_validate(data)


def test_metric_service_executes_v03_typed_policy() -> None:
    graph = complete_runtime_graph()
    benchmark = _v03_definition()
    result = calculate_metric_result(
        benchmark.metric_specifications[0],
        run_id="RUN001",
        metric_result_id="MR001",
        created_at=NOW,
        grader_results=graph.grader_results,
        episodes=graph.episodes,
    )
    assert result.status == "available"
    assert result.value is not None
    assert result.value.canonical_value == Decimal("1")


def test_three_valued_quantifier_rules_and_empty_domain() -> None:
    assert evaluate_three_valued_quantifier(["MATCH", "UNKNOWN"], "any") == "true"
    assert evaluate_three_valued_quantifier(["NON_MATCH", "UNKNOWN"], "any") == "unknown"
    assert evaluate_three_valued_quantifier(["MATCH", "UNKNOWN"], "all") == "unknown"
    assert evaluate_three_valued_quantifier(["NON_MATCH", "UNKNOWN"], "all") == "false"
    assert evaluate_three_valued_quantifier([], "any") == "unknown"


def test_metric_threshold_gate_uses_canonical_decimal_and_unavailable_mapping() -> None:
    graph = complete_runtime_graph()
    specification = GateSpecificationV03.model_validate(
        {
            "gate_id": "GATE001",
            "name": "Minimum satisfaction",
            "scope": "whole benchmark",
            "condition": {
                "condition_type": "metric_threshold",
                "metric_id": "M001",
                "comparator": "lt",
                "threshold_value": "0.8",
            },
            "unavailable_handling": "indeterminate",
            "result_semantics": graph.benchmark.gate_specifications[0].result_semantics,
            "explanation_requirements": ["Report the compared canonical value."],
        }
    )
    gate = evaluate_gate(
        specification,
        run_id="RUN001",
        gate_result_id="GATER001",
        created_at=NOW,
        metric_results=[graph.metric_results[0]],
    )
    assert gate.result == "OPEN"
    assert gate.evaluation_path == GateEvaluationPath.CONDITION_FALSE
    changed_metric = _metric_with(
        graph.metric_results[0],
        value={"value_kind": "rate", "canonical_value": Decimal("0.7995")},
    )
    triggered = evaluate_gate(
        specification,
        run_id="RUN001",
        gate_result_id="GATER002",
        created_at=NOW,
        metric_results=[changed_metric],
    )
    assert triggered.result == "TRIGGERED"
    assert triggered.input_summary.observed_canonical_value == Decimal("0.7995")
    unavailable = _metric_with(
        graph.metric_results[0],
        status="unavailable",
        value=None,
        unavailable_reason="empty_denominator",
        unavailable_explanation="No eligible denominator.",
    )
    unknown = evaluate_gate(
        specification,
        run_id="RUN001",
        gate_result_id="GATER003",
        created_at=NOW,
        metric_results=[unavailable],
    )
    assert unknown.result == "INDETERMINATE"
    assert unknown.evaluation_path == GateEvaluationPath.UNKNOWN_INDETERMINATE


def test_metric_availability_gate_distinguishes_missing_and_unavailable() -> None:
    graph = complete_runtime_graph()
    data = deepcopy(make_definition_data()["gate_specifications"][0])
    data["condition"] = {
        "condition_type": "metric_availability",
        "metric_id": "M001",
        "trigger_on": "unavailable",
    }
    specification = GateSpecificationV03.model_validate(data)
    missing = evaluate_gate(
        specification,
        run_id="RUN001",
        gate_result_id="GATER001",
        created_at=NOW,
    )
    assert missing.result == "INDETERMINATE"
    unavailable = _metric_with(
        graph.metric_results[0],
        status="unavailable",
        value=None,
        unavailable_reason="empty_denominator",
        unavailable_explanation="No eligible denominator.",
    )
    triggered = evaluate_gate(
        specification,
        run_id="RUN001",
        gate_result_id="GATER002",
        created_at=NOW,
        metric_results=[unavailable],
    )
    assert triggered.result == "TRIGGERED"
    assert triggered.trigger_source == "condition"


def _overall_policy() -> WeightedNormalizedMeanOverallScorePolicy:
    return WeightedNormalizedMeanOverallScorePolicy(
        mode="weighted_normalized_mean",
        metric_contributions=[
            OverallMetricContribution(
                metric_id="M001",
                weight=Decimal("3"),
                normalization={"type": "identity_unit_interval"},
                unavailable_result_handling="overall_unavailable",
                missing_result_handling="overall_unavailable",
            ),
            OverallMetricContribution(
                metric_id="M002",
                weight=Decimal("1"),
                normalization={"type": "identity_unit_interval"},
                unavailable_result_handling="exclude_and_renormalize",
                missing_result_handling="exclude_and_renormalize",
            ),
        ],
        minimum_available_weight_fraction=Decimal("0.75"),
        canonical_scale="unit_interval",
        canonical_precision=2,
    )


def test_overall_weighted_mean_is_decimal_and_finally_rounded() -> None:
    graph = complete_runtime_graph()
    first = _metric_with(
        graph.metric_results[0],
        value={"value_kind": "rate", "canonical_value": Decimal("0.8")},
    )
    second = _metric_with(
        first,
        metric_id="M002",
        metric_result_id="MR002",
        value={"value_kind": "rate", "canonical_value": Decimal("0.6")},
    )
    outcome = calculate_overall_score(
        _overall_policy(),
        run_id="RUN001",
        definition_digest=DIGEST,
        metric_results=[second, first],
    )
    assert outcome.evaluation_status == "available"
    assert outcome.canonical_value == Decimal("0.75")
    assert [trace.metric_id for trace in outcome.contribution_traces] == ["M001", "M002"]


def test_overall_exclude_and_renormalize_and_missing_are_not_zero() -> None:
    graph = complete_runtime_graph()
    first = _metric_with(
        graph.metric_results[0],
        value={"value_kind": "rate", "canonical_value": Decimal("0.8")},
    )
    outcome = calculate_overall_score(
        _overall_policy(),
        run_id="RUN001",
        definition_digest=DIGEST,
        metric_results=[first],
    )
    assert outcome.evaluation_status == "available"
    assert outcome.canonical_value == Decimal("0.8")
    assert outcome.contribution_traces[1].application_state == "missing"
    unavailable = _metric_with(
        first,
        status="unavailable",
        value=None,
        metric_id="M001",
        unavailable_reason="empty_denominator",
        unavailable_explanation="No eligible denominator.",
    )
    outcome_unavailable = calculate_overall_score(
        _overall_policy(),
        run_id="RUN001",
        definition_digest=DIGEST,
        metric_results=[unavailable],
    )
    assert outcome_unavailable.evaluation_status == "unavailable"
    assert outcome_unavailable.canonical_value is None


def test_overall_rejects_out_of_range_normalized_value() -> None:
    graph = complete_runtime_graph()
    metric = _metric_with(
        graph.metric_results[0],
        value={"value_kind": "rate", "canonical_value": Decimal("1.1")},
    )
    policy = _overall_policy().model_copy(
        update={"metric_contributions": [_overall_policy().metric_contributions[0]]}
    )
    with pytest.raises(OverallEvaluationError, match="outside"):
        calculate_overall_score(
            policy, run_id="RUN001", definition_digest=DIGEST, metric_results=[metric]
        )


def test_overall_linear_normalization_higher_and_lower_is_decimal() -> None:
    graph = complete_runtime_graph()
    metric = _metric_with(
        graph.metric_results[0],
        value={"value_kind": "scalar", "canonical_value": Decimal("75")},
    )
    for direction, expected in (
        ("higher_is_better", Decimal("0.75")),
        ("lower_is_better", Decimal("0.25")),
    ):
        contribution = OverallMetricContribution(
            metric_id="M001",
            weight=Decimal("1"),
            normalization=LinearBoundedNormalization(
                type="linear_bounded",
                source_min=Decimal("0"),
                source_max=Decimal("100"),
                direction=direction,
            ),
            unavailable_result_handling="overall_unavailable",
            missing_result_handling="overall_unavailable",
        )
        policy = WeightedNormalizedMeanOverallScorePolicy(
            mode="weighted_normalized_mean",
            metric_contributions=[contribution],
            minimum_available_weight_fraction=Decimal("1"),
            canonical_scale="unit_interval",
            canonical_precision=2,
        )
        outcome = calculate_overall_score(
            policy, run_id="RUN001", definition_digest=DIGEST, metric_results=[metric]
        )
        assert outcome.canonical_value == expected


def test_overall_pending_and_invalid_states_are_not_semantic_scores() -> None:
    policy = _overall_policy()
    pending = calculate_overall_score(
        policy,
        run_id="RUN001",
        definition_digest=DIGEST,
        run_state="pending",
    )
    invalid = calculate_overall_score(
        policy,
        run_id="RUN001",
        definition_digest=DIGEST,
        run_state="invalid",
    )
    assert pending.evaluation_status == "not_produced_run_pending"
    assert invalid.evaluation_status == "not_produced_run_invalid"


def _acceptance_policy() -> GateBasedAcceptancePolicy:
    return GateBasedAcceptancePolicy(
        mode="gate_based",
        participating_gates=[
            {
                "gate_id": "GATE001",
                "indeterminate_handling": "overall_indeterminate",
                "missing_result_handling": "overall_blocked",
            }
        ],
    )


def test_acceptance_propagation_is_independent_of_overall() -> None:
    graph = complete_runtime_graph()
    open_gate = graph.gate_results[0]
    acceptable = evaluate_acceptance(
        _acceptance_policy(), run_id="RUN001", definition_digest=DIGEST, gate_results=[open_gate]
    )
    assert acceptable.acceptance == "ACCEPTABLE"
    triggered = open_gate.model_copy(
        update={
            "result": "TRIGGERED",
            "evaluation_path": "condition_true",
            "trigger_source": "condition",
        }
    )
    blocked = evaluate_acceptance(
        _acceptance_policy(), run_id="RUN001", definition_digest=DIGEST, gate_results=[triggered]
    )
    assert blocked.acceptance == "BLOCKED"
    missing = evaluate_acceptance(
        _acceptance_policy(), run_id="RUN001", definition_digest=DIGEST, gate_results=[]
    )
    assert missing.acceptance == "BLOCKED"


def test_acceptance_disabled_pending_invalid_and_bad_state() -> None:
    from skill_eval_framework.schemas.definition import DisabledAcceptancePolicy

    disabled = evaluate_acceptance(
        DisabledAcceptancePolicy(mode="disabled"), run_id="RUN001", definition_digest=DIGEST
    )
    assert disabled.evaluation_status == "disabled"
    pending = evaluate_acceptance(
        _acceptance_policy(), run_id="RUN001", definition_digest=DIGEST, run_state="pending"
    )
    assert pending.evaluation_status == "not_produced_run_pending"
    invalid = evaluate_acceptance(
        _acceptance_policy(), run_id="RUN001", definition_digest=DIGEST, run_state="invalid"
    )
    assert invalid.evaluation_status == "not_produced_run_invalid"
    with pytest.raises(AcceptanceEvaluationError):
        evaluate_acceptance(
            _acceptance_policy(), run_id="RUN001", definition_digest=DIGEST, run_state="failed"
        )


def test_metric_all_distinct_mean_uses_exact_decimal_contributions() -> None:
    graph = complete_runtime_graph()
    retry_episode, retry_result = _retry_result(graph, judgment="violated")
    metric = calculate_metric_result(
        _v03_metric(),
        run_id="RUN001",
        metric_result_id="MR010",
        created_at=NOW,
        grader_results=[graph.grader_results[0], retry_result],
        episodes=[graph.episodes[0], retry_episode],
    )
    assert metric.value is not None
    assert metric.value.canonical_value == Decimal("0.5")
    assert metric.coverage.distinct_result_count == 2


def test_metric_final_raw_selects_last_non_substantive_without_fallback() -> None:
    graph = complete_runtime_graph()
    retry_episode, retry_result = _retry_result(graph, judgment="insufficient_evidence")
    metric = calculate_metric_result(
        _v03_metric(selection="final_distinct_raw"),
        run_id="RUN001",
        metric_result_id="MR011",
        created_at=NOW,
        grader_results=[graph.grader_results[0], retry_result],
        episodes=[graph.episodes[0], retry_episode],
    )
    assert metric.status == "unavailable"
    assert metric.unavailable_reason == "empty_denominator"
    assert metric.coverage.selected_result_count == 1
    assert metric.coverage.insufficient_evidence_count == 1


def test_metric_final_eligible_excludes_last_non_substantive_and_keeps_first() -> None:
    graph = complete_runtime_graph()
    retry_episode, retry_result = _retry_result(graph, judgment="insufficient_evidence")
    metric = calculate_metric_result(
        _v03_metric(reduction="final_eligible"),
        run_id="RUN001",
        metric_result_id="MR012",
        created_at=NOW,
        grader_results=[graph.grader_results[0], retry_result],
        episodes=[graph.episodes[0], retry_episode],
    )
    assert metric.status == "available"
    assert metric.value is not None
    assert metric.value.canonical_value == Decimal("1")


def test_metric_strict_missing_input_is_unavailable_not_zero() -> None:
    graph = complete_runtime_graph()
    metric = calculate_metric_result(
        _v03_metric(),
        run_id="RUN001",
        metric_result_id="MR013",
        created_at=NOW,
        episodes=graph.episodes,
    )
    assert metric.status == "unavailable"
    assert metric.unavailable_reason == "required_inputs_missing"
    assert metric.value is None
    assert metric.missing_inputs


def test_direct_grader_gate_shared_selection_and_any_all_truth_tables() -> None:
    graph = complete_runtime_graph()
    retry_episode, retry_result = _retry_result(graph, judgment="violated")
    gate = evaluate_gate(
        _direct_gate(graph, selection="all_distinct", quantifier="any"),
        run_id="RUN001",
        gate_result_id="GATER010",
        created_at=NOW,
        grader_results=[graph.grader_results[0], retry_result],
        episodes=[graph.episodes[0], retry_episode],
    )
    assert gate.result == "TRIGGERED"
    assert gate.input_summary.condition_outcome == "true"
    all_gate = evaluate_gate(
        _direct_gate(graph, selection="all_distinct", quantifier="all"),
        run_id="RUN001",
        gate_result_id="GATER011",
        created_at=NOW,
        grader_results=[graph.grader_results[0], retry_result],
        episodes=[graph.episodes[0], retry_episode],
    )
    assert all_gate.result == "OPEN"


def test_direct_grader_gate_final_raw_and_known_non_trigger_semantics() -> None:
    graph = complete_runtime_graph()
    retry_episode, retry_result = _retry_result(graph, judgment="insufficient_evidence")
    gate = evaluate_gate(
        _direct_gate(graph, selection="final_distinct_raw"),
        run_id="RUN001",
        gate_result_id="GATER012",
        created_at=NOW,
        grader_results=[graph.grader_results[0], retry_result],
        episodes=[graph.episodes[0], retry_episode],
    )
    assert gate.result == "OPEN"
    assert gate.input_summary.grader_contributions[0].contribution == "NON_MATCH"


def test_direct_grader_gate_first_and_sole_selection_are_not_implicit_fallbacks() -> None:
    graph = complete_runtime_graph()
    retry_episode, retry_result = _retry_result(graph, judgment="violated")
    first_gate = evaluate_gate(
        _direct_gate(graph, selection="first_distinct"),
        run_id="RUN001",
        gate_result_id="GATER014",
        created_at=NOW,
        grader_results=[graph.grader_results[0], retry_result],
        episodes=[graph.episodes[0], retry_episode],
    )
    assert first_gate.result == "OPEN"
    with pytest.raises(GateEvaluationError, match="sole_distinct"):
        evaluate_gate(
            _direct_gate(graph, selection="sole_distinct"),
            run_id="RUN001",
            gate_result_id="GATER015",
            created_at=NOW,
            grader_results=[graph.grader_results[0], retry_result],
            episodes=[graph.episodes[0], retry_episode],
        )


def test_direct_grader_gate_missing_target_uses_unavailable_handling() -> None:
    graph = complete_runtime_graph()
    gate = evaluate_gate(
        _direct_gate(graph, selection="sole_distinct"),
        run_id="RUN001",
        gate_result_id="GATER013",
        created_at=NOW,
        episodes=graph.episodes,
    )
    assert gate.result == "INDETERMINATE"
    assert gate.evaluation_path == GateEvaluationPath.UNKNOWN_INDETERMINATE


def test_v02_metric_is_rejected_instead_of_guessing_free_text() -> None:
    graph = complete_runtime_graph()
    with pytest.raises(MetricEvaluationError, match="unsupported executable definition version"):
        calculate_metric_result(
            graph.benchmark.metric_specifications[0],
            run_id="RUN001",
            metric_result_id="MR014",
            created_at=NOW,
        )
