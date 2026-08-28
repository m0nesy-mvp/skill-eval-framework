from __future__ import annotations

from copy import deepcopy

import pytest
from conftest import make_definition_data, make_run_data
from validation_helpers import complete_runtime_graph

from skill_eval_framework.digest import compute_definition_digest
from skill_eval_framework.runtime import (
    expected_applications_for_run,
    finalize_run_validity,
    prevalidate_run,
)
from skill_eval_framework.schemas.definition_v03 import BenchmarkDefinitionV03
from skill_eval_framework.schemas.runtime import (
    DefinitionClosureProfile,
    FrozenDefinitionRef,
    Run,
    RunValidityStatus,
)
from skill_eval_framework.validation import validate_run_definition_binding, validate_run_graph


def _v03_policy() -> dict[str, object]:
    return {
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
    metric["execution_policy"] = _v03_policy()
    return BenchmarkDefinitionV03.model_validate(data)


def _v03_run(benchmark: BenchmarkDefinitionV03) -> Run:
    run_data = make_run_data()
    run_data["definition_ref"]["definition_closure_profile"] = DefinitionClosureProfile.V1
    run_data["definition_ref"]["definition_digest"] = compute_definition_digest(benchmark)
    return Run.model_validate(run_data)


def test_frozen_definition_ref_accepts_v0_and_v1_profiles() -> None:
    graph = complete_runtime_graph()
    assert graph.run.definition_ref.definition_closure_profile == DefinitionClosureProfile.V0
    benchmark = _v03_definition()
    run = _v03_run(benchmark)
    assert run.definition_ref.definition_closure_profile == DefinitionClosureProfile.V1


def test_frozen_definition_ref_rejects_unknown_profile() -> None:
    with pytest.raises(ValueError):
        FrozenDefinitionRef.model_validate(
            {
                "benchmark_id": "skill.eval.v0",
                "benchmark_version": "0.1.0",
                "definition_closure_profile": "skill-eval-frozen-definition-closure-v9",
                "definition_digest": "sha256:" + "a" * 64,
            }
        )


def test_v0_and_v1_definition_binding_pairs_are_explicit() -> None:
    graph = complete_runtime_graph()
    assert validate_run_definition_binding(graph.benchmark, graph.run).is_valid
    benchmark = _v03_definition()
    run = _v03_run(benchmark)
    assert validate_run_definition_binding(benchmark, run).is_valid
    assert not validate_run_definition_binding(
        benchmark,
        run.model_copy(
            update={
                "definition_ref": run.definition_ref.model_copy(
                    update={"definition_closure_profile": DefinitionClosureProfile.V0}
                )
            }
        ),
    ).is_valid
    assert not validate_run_definition_binding(
        graph.benchmark,
        graph.run.model_copy(
            update={
                "definition_ref": graph.run.definition_ref.model_copy(
                    update={"definition_closure_profile": DefinitionClosureProfile.V1}
                )
            }
        ),
    ).is_valid


def test_v03_runtime_preflight_verifies_digest_and_preserves_pending() -> None:
    benchmark = _v03_definition()
    run = _v03_run(benchmark)
    checked = prevalidate_run(benchmark, run)
    assert checked.validity_status == RunValidityStatus.PENDING
    assert checked.validity_findings == []


def test_v03_runtime_preflight_rejects_same_identity_digest_drift() -> None:
    benchmark = _v03_definition()
    run = _v03_run(benchmark)
    drifted = benchmark.model_copy(update={"description": "changed content"})
    checked = prevalidate_run(drifted, run)
    assert checked.validity_status == RunValidityStatus.INVALID
    assert any(item.code == "RUN_DEFINITION_DIGEST_MISMATCH" for item in checked.validity_findings)


@pytest.mark.parametrize(
    ("field", "value"),
    [("benchmark_id", "skill.eval.other"), ("benchmark_version", "9.9.9")],
)
def test_v03_runtime_preflight_rejects_identity_mismatch(field: str, value: str) -> None:
    benchmark = _v03_definition()
    run = _v03_run(benchmark)
    ref = run.definition_ref.model_copy(update={field: value})
    checked = prevalidate_run(benchmark, run.model_copy(update={"definition_ref": ref}))
    assert checked.validity_status == RunValidityStatus.INVALID


def test_snapshot_ref_cannot_override_definition_digest_mismatch() -> None:
    benchmark = _v03_definition()
    run = _v03_run(benchmark)
    ref = run.definition_ref.model_copy(
        update={"definition_digest": "sha256:" + "b" * 64, "definition_snapshot_ref": "other.json"}
    )
    report = validate_run_definition_binding(
        benchmark, run.model_copy(update={"definition_ref": ref})
    )
    assert any(item.code == "RUN_DEFINITION_DIGEST_MISMATCH" for item in report.issues)


def test_v03_expected_application_identity_matches_v0_shape() -> None:
    graph = complete_runtime_graph()
    benchmark = _v03_definition()
    run = _v03_run(benchmark).model_copy(
        update={
            "execution_plan": graph.run.execution_plan,
            "execution_status": graph.run.execution_status,
            "validity_status": RunValidityStatus.PENDING,
            "validity_findings": [],
            "started_at": graph.run.started_at,
            "ended_at": graph.run.ended_at,
            "episode_ids": graph.run.episode_ids,
        }
    )
    expected = expected_applications_for_run(benchmark, run, graph.episodes)
    expected_v02 = expected_applications_for_run(graph.benchmark, graph.run, graph.episodes)
    assert [item.logical_key for item in expected] == [item.logical_key for item in expected_v02]
    assert sum(item.application_type == "episode" for item in expected) == 1
    assert sum(item.application_type == "grader_result" for item in expected) == 1
    assert sum(item.application_type == "metric_result" for item in expected) == 1
    assert sum(item.application_type == "gate_result" for item in expected) == 1


def test_v03_runtime_graph_and_final_integrity_pass() -> None:
    graph = complete_runtime_graph()
    benchmark = _v03_definition()
    digest = compute_definition_digest(benchmark)
    run = _v03_run(benchmark).model_copy(
        update={
            "execution_status": graph.run.execution_status,
            "validity_status": RunValidityStatus.PENDING,
            "validity_findings": [],
            "started_at": graph.run.started_at,
            "ended_at": graph.run.ended_at,
            "episode_ids": graph.run.episode_ids,
        }
    )
    scorecard = graph.scorecard.model_copy(
        update={
            "definition_ref": run.definition_ref,
            "overall_score_outcome": graph.scorecard.overall_score_outcome.model_copy(
                update={
                    "policy_ref": graph.scorecard.overall_score_outcome.policy_ref.model_copy(
                        update={"definition_digest": digest}
                    )
                }
            ),
            "acceptance_evaluation": graph.scorecard.acceptance_evaluation.model_copy(
                update={
                    "policy_ref": graph.scorecard.acceptance_evaluation.policy_ref.model_copy(
                        update={"definition_digest": digest}
                    )
                }
            ),
            "finalization_status": "interim",
            "finalized_at": None,
        }
    )
    assert validate_run_graph(
        benchmark,
        run,
        graph.episodes,
        graph.artifacts,
        graph.evidence,
        graph.grader_results,
        graph.metric_results,
        graph.gate_results,
        graph.diagnostics,
        scorecard,
    ).is_valid
    finalized = finalize_run_validity(
        benchmark,
        run,
        episodes=graph.episodes,
        artifacts=graph.artifacts,
        evidence=graph.evidence,
        grader_results=graph.grader_results,
        metric_results=graph.metric_results,
        gate_results=graph.gate_results,
        diagnostics=graph.diagnostics,
        scorecard=scorecard,
    )
    assert finalized.validity_status == RunValidityStatus.VALID


def test_v03_final_integrity_rejects_definition_drift() -> None:
    graph = complete_runtime_graph()
    benchmark = _v03_definition()
    run = _v03_run(benchmark).model_copy(
        update={
            "execution_status": graph.run.execution_status,
            "started_at": graph.run.started_at,
            "ended_at": graph.run.ended_at,
            "episode_ids": graph.run.episode_ids,
        }
    )
    scorecard = graph.scorecard.model_copy(update={"definition_ref": run.definition_ref})
    drifted = benchmark.model_copy(update={"description": "changed content"})
    finalized = finalize_run_validity(
        drifted,
        run,
        episodes=graph.episodes,
        artifacts=graph.artifacts,
        evidence=graph.evidence,
        grader_results=graph.grader_results,
        metric_results=graph.metric_results,
        gate_results=graph.gate_results,
        diagnostics=graph.diagnostics,
        scorecard=scorecard,
    )
    assert finalized.validity_status == RunValidityStatus.INVALID
    assert any(
        item.code == "RUN_DEFINITION_DIGEST_MISMATCH" for item in finalized.validity_findings
    )


def test_v0_scorecard_definition_ref_remains_accepted() -> None:
    graph = complete_runtime_graph()
    assert graph.scorecard.definition_ref.definition_closure_profile == DefinitionClosureProfile.V0
    assert graph.validate().is_valid
