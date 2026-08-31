from __future__ import annotations

from validation_helpers import codes, complete_runtime_graph

from skill_eval_framework.schemas.results import (
    AcceptanceGateContributionTrace,
    DefinitionPolicyRef,
    MissingApplicationRecord,
    OverallMetricContributionTrace,
)
from skill_eval_framework.schemas.runtime import RuntimeDiagnostic
from skill_eval_framework.validation import validate_run_graph


def test_finalized_scorecard_with_closed_inventory_is_valid() -> None:
    graph = complete_runtime_graph()
    assert validate_run_graph(
        graph.benchmark,
        graph.run,
        graph.episodes,
        graph.artifacts,
        graph.evidence,
        graph.grader_results,
        graph.metric_results,
        graph.gate_results,
        graph.diagnostics,
        graph.scorecard,
    ).is_valid


def test_final_inventory_requires_missing_or_actual_for_every_expected_application() -> None:
    graph = complete_runtime_graph()
    graph.scorecard = graph.scorecard.model_copy(
        update={
            "result_inventory": graph.scorecard.result_inventory.model_copy(
                update={"metric_result_ids": []}
            )
        }
    )
    graph.metric_results = []
    assert "RUN_EXPECTED_APPLICATION_MISSING" in codes(graph.validate())


def test_actual_and_missing_entries_conflict() -> None:
    graph = complete_runtime_graph()
    graph.scorecard = graph.scorecard.model_copy(
        update={
            "result_inventory": graph.scorecard.result_inventory.model_copy(
                update={
                    "missing_applications": [
                        MissingApplicationRecord(
                            application_ref={
                                "application_type": "metric_result",
                                "metric_id": "M001",
                            },
                            diagnostic_ids=[],
                            explanation="Metric was not produced.",
                        )
                    ]
                }
            )
        }
    )
    assert "RUN_INVENTORY_CONFLICT" in codes(graph.validate())


def test_inventory_reference_cannot_cross_runs() -> None:
    graph = complete_runtime_graph()
    foreign = graph.metric_results[0].model_copy(
        update={"metric_result_id": "MR999", "run_id": "OTHER"}
    )
    graph.metric_results.append(foreign)
    graph.scorecard = graph.scorecard.model_copy(
        update={
            "result_inventory": graph.scorecard.result_inventory.model_copy(
                update={
                    "metric_result_ids": [
                        *graph.scorecard.result_inventory.metric_result_ids,
                        "MR999",
                    ]
                }
            )
        }
    )
    assert "RUN_CROSS_RUN_REFERENCE" in codes(graph.validate())


def test_overall_policy_digest_must_match_definition_ref() -> None:
    graph = complete_runtime_graph()
    graph.scorecard = graph.scorecard.model_copy(
        update={
            "overall_score_outcome": graph.scorecard.overall_score_outcome.model_copy(
                update={
                    "policy_ref": DefinitionPolicyRef(
                        definition_digest="sha256:" + "b" * 64,
                        policy_path="/overall_score_policy",
                    )
                }
            )
        }
    )
    assert "RUN_OVERALL_POLICY_DIGEST_MISMATCH" in codes(graph.validate())


def test_overall_trace_metric_result_must_resolve() -> None:
    graph = complete_runtime_graph()
    graph.benchmark.overall_score_policy = {
        "mode": "weighted_normalized_mean",
        "metric_contributions": [
            {
                "metric_id": "M001",
                "weight": "1",
                "normalization": {"type": "identity_unit_interval"},
                "unavailable_result_handling": "overall_unavailable",
                "missing_result_handling": "overall_unavailable",
            }
        ],
        "minimum_available_weight_fraction": "1",
        "canonical_scale": "unit_interval",
        "canonical_precision": 4,
    }
    graph.scorecard = graph.scorecard.model_copy(
        update={
            "overall_score_outcome": graph.scorecard.overall_score_outcome.model_copy(
                update={
                    "evaluation_status": "available",
                    "canonical_value": "1",
                    "contribution_traces": [
                        OverallMetricContributionTrace(
                            metric_id="M001",
                            weight="1",
                            metric_result_id="MR999",
                            application_state="available",
                            policy_handling="included",
                            normalized_value="1",
                            weighted_contribution="1",
                        )
                    ],
                    "total_selected_weight": "1",
                    "available_weight": "1",
                    "available_weight_fraction": "1",
                    "minimum_required_weight_fraction": "1",
                    "final_included_denominator": "1",
                }
            )
        }
    )
    assert "RUN_OVERALL_METRIC_RESULT_UNKNOWN" in codes(graph.validate())


def test_acceptance_trace_must_name_participating_gate() -> None:
    graph = complete_runtime_graph()
    graph.benchmark.acceptance_policy = {
        "mode": "gate_based",
        "participating_gates": [
            {
                "gate_id": "GATE001",
                "indeterminate_handling": "overall_indeterminate",
                "missing_result_handling": "overall_blocked",
            }
        ],
    }
    graph.scorecard = graph.scorecard.model_copy(
        update={
            "acceptance_evaluation": graph.scorecard.acceptance_evaluation.model_copy(
                update={
                    "evaluation_status": "produced",
                    "acceptance": "ACCEPTABLE",
                    "gate_contributions": [
                        AcceptanceGateContributionTrace(
                            gate_id="GATE999",
                            gate_result_id="GATER001",
                            application_state="OPEN",
                            policy_handling="open",
                            propagation_outcome="no_block",
                            explanation="Unknown gate.",
                        )
                    ],
                }
            )
        }
    )
    assert "RUN_ACCEPTANCE_GATE_NOT_PARTICIPATING" in codes(graph.validate())


def test_missing_acceptance_trace_cannot_include_result_reference() -> None:
    graph = complete_runtime_graph()
    graph.benchmark.acceptance_policy = {
        "mode": "gate_based",
        "participating_gates": [
            {
                "gate_id": "GATE001",
                "indeterminate_handling": "overall_indeterminate",
                "missing_result_handling": "overall_blocked",
            }
        ],
    }
    graph.scorecard = graph.scorecard.model_copy(
        update={
            "acceptance_evaluation": graph.scorecard.acceptance_evaluation.model_copy(
                update={
                    "evaluation_status": "produced",
                    "acceptance": "INDETERMINATE",
                    "gate_contributions": [
                        AcceptanceGateContributionTrace(
                            gate_id="GATE001",
                            gate_result_id="GATER001",
                            application_state="MISSING",
                            policy_handling="overall_indeterminate",
                            propagation_outcome="indeterminate",
                            explanation="Gate result missing.",
                        )
                    ],
                }
            )
        }
    )
    assert "RUN_ACCEPTANCE_MISSING_HAS_RESULT_REF" in codes(graph.validate())


def test_production_failed_diagnostic_requires_scorecard_phase_and_association() -> None:
    graph = complete_runtime_graph()
    diagnostic = RuntimeDiagnostic.model_validate(
        {
            "diagnostic_id": "D001",
            "run_id": "RUN001",
            "phase": "metric",
            "code": "METRIC_FAIL",
            "message": "Metric production failed.",
            "episode_id": None,
            "related_object_refs": [],
            "occurred_at": "2026-08-28T10:00:00",
        }
    )
    graph.diagnostics = [diagnostic]
    graph.scorecard = graph.scorecard.model_copy(
        update={
            "overall_score_outcome": graph.scorecard.overall_score_outcome.model_copy(
                update={
                    "evaluation_status": "production_failed",
                    "diagnostic_ids": ["D001"],
                }
            )
        }
    )
    assert "RUN_PRODUCTION_DIAGNOSTIC_PHASE_INVALID" in codes(graph.validate())
    assert "RUN_PRODUCTION_DIAGNOSTIC_ASSOCIATION_MISSING" in codes(graph.validate())


def test_interim_scorecard_does_not_require_final_inventory_closure() -> None:
    graph = complete_runtime_graph()
    graph.scorecard = graph.scorecard.model_copy(
        update={
            "finalization_status": "interim",
            "finalized_at": None,
            "result_inventory": graph.scorecard.result_inventory.model_copy(
                update={"metric_result_ids": []}
            ),
        }
    )
    assert "RUN_EXPECTED_APPLICATION_MISSING" not in codes(graph.validate())


def test_finalized_evaluation_requires_valid_run() -> None:
    graph = complete_runtime_graph()
    graph.run = graph.run.model_copy(update={"validity_status": "pending"})
    assert "RUN_FINALIZED_EVALUATION_REQUIRES_VALID_RUN" in codes(graph.validate())
