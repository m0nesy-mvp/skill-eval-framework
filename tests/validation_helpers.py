"""Reusable complete graphs for cross-object validation tests."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

from conftest import NOW, make_definition_data, make_run_data, make_scorecard_data

from skill_eval_framework.schemas.definition import BenchmarkDefinition
from skill_eval_framework.schemas.results import (
    GateResult,
    GraderResult,
    MetricResult,
    Scorecard,
)
from skill_eval_framework.schemas.runtime import Artifact, Episode, Evidence, Run, RuntimeDiagnostic
from skill_eval_framework.validation import ValidationReport, validate_run_graph


@dataclass
class RuntimeGraph:
    benchmark: BenchmarkDefinition
    run: Run
    episodes: list[Episode]
    artifacts: list[Artifact]
    evidence: list[Evidence]
    grader_results: list[GraderResult]
    metric_results: list[MetricResult]
    gate_results: list[GateResult]
    diagnostics: list[RuntimeDiagnostic]
    scorecard: Scorecard

    def clone(self) -> RuntimeGraph:
        return deepcopy(self)

    def validate(self) -> ValidationReport:
        return validate_run_graph(
            self.benchmark,
            self.run,
            self.episodes,
            self.artifacts,
            self.evidence,
            self.grader_results,
            self.metric_results,
            self.gate_results,
            self.diagnostics,
            self.scorecard,
        )


def complete_definition() -> BenchmarkDefinition:
    return BenchmarkDefinition.model_validate(make_definition_data())


def complete_runtime_graph() -> RuntimeGraph:
    benchmark = complete_definition()
    run_data = make_run_data()
    run_data.update(
        {
            "execution_status": "completed",
            "validity_status": "valid",
            "created_at": NOW,
            "started_at": NOW,
            "ended_at": NOW,
            "episode_ids": ["E001"],
        }
    )
    run = Run.model_validate(run_data)
    episode = Episode.model_validate(
        {
            "episode_id": "E001",
            "run_id": "RUN001",
            "test_case_id": "TC001",
            "attempt_index": 1,
            "execution_status": "completed",
            "created_at": NOW,
            "started_at": NOW,
            "ended_at": NOW,
            "trace_events": [
                {
                    "trace_event_id": "TE001",
                    "event_index": 1,
                    "actor": "subject",
                    "event_type": "message",
                    "semantic_summary": "The subject returned the expected output.",
                }
            ],
            "artifact_ids": ["A001"],
            "evidence_ids": ["EV001"],
            "diagnostic_ids": [],
        }
    )
    artifact = Artifact.model_validate(
        {
            "artifact_id": "A001",
            "run_id": "RUN001",
            "artifact_kind": "subject_response",
            "locator": "artifact://A001",
            "producer": "subject",
            "relations": [
                {
                    "relation": "produced",
                    "episode_id": "E001",
                    "trace_event_id": "TE001",
                    "source": "subject response",
                }
            ],
        }
    )
    evidence = Evidence.model_validate(
        {
            "evidence_id": "EV001",
            "run_id": "RUN001",
            "episode_id": "E001",
            "evidence_spec_id": "ES001",
            "qualified_targets": [{"test_case_id": "TC001", "contract_id": "C001"}],
            "observation": {"summary": "Expected output exists."},
            "provenance": {
                "source_refs": [{"source_type": "artifact", "source_id": "A001"}],
                "collector": "test collector",
                "observed_from": "subject response",
            },
            "context": {
                "context_summary": "Completed TC001 attempt.",
                "related_trace_event_ids": ["TE001"],
            },
            "qualification": {
                "status": "qualified",
                "checks": [
                    {
                        "requirement": "Observation is attributable.",
                        "outcome": "passed",
                        "detail": "Artifact relation resolves to the Episode trace.",
                    }
                ],
                "qualified_by": "test collector",
                "qualified_at": NOW,
            },
        }
    )
    grader_result = GraderResult.model_validate(
        {
            "grader_result_id": "GR001",
            "run_id": "RUN001",
            "episode_id": "E001",
            "grader_id": "G001",
            "test_case_id": "TC001",
            "contract_id": "C001",
            "evidence_ids": ["EV001"],
            "judgment": "satisfied",
            "explanation": {
                "evidence_contributions": [
                    {"evidence_id": "EV001", "contribution": "Shows the expected output."}
                ],
                "observed_facts": ["Output exists."],
                "semantic_basis": "The output satisfies C001.",
                "supported_failure_criterion": None,
                "supported_failure_mode": None,
                "insufficiency_gaps": [],
                "inference_notes": [],
            },
            "created_at": NOW,
        }
    )
    metric_result = MetricResult.model_validate(
        {
            "metric_result_id": "MR001",
            "run_id": "RUN001",
            "metric_id": "M001",
            "status": "available",
            "value": {"value_kind": "rate", "canonical_value": "1", "unit": "ratio"},
            "coverage": {
                "expected_input_count": 1,
                "available_raw_result_count": 1,
                "distinct_result_count": 1,
                "selected_result_count": 1,
                "substantive_eligible_count": 1,
                "not_exercised_count": 0,
                "insufficient_evidence_count": 0,
                "unavailable_input_count": 0,
                "declared_aggregation_unit": "contract application",
                "contributing_unit_count": 1,
                "denominator": "1",
                "coverage_ratio": "1",
            },
            "input_traces": [
                {
                    "grader_result_id": "GR001",
                    "disposition": "included",
                    "reason": "Eligible substantive result.",
                    "aggregation_unit_key": "TC001/C001",
                    "contribution_value": "1",
                }
            ],
            "missing_inputs": [],
            "created_at": NOW,
        }
    )
    gate_result = GateResult.model_validate(
        {
            "gate_result_id": "GATER001",
            "run_id": "RUN001",
            "gate_id": "GATE001",
            "result": "OPEN",
            "evaluation_path": "condition_false",
            "trigger_source": None,
            "input_summary": {
                "condition_type": "metric_threshold",
                "grader_contributions": [],
                "metric_result_id": "MR001",
                "metric_input_state": "available",
                "observed_canonical_value": "1",
                "comparator_outcome": "false",
                "quantifier": "not_applicable",
                "condition_outcome": "false",
            },
            "explanation": "M001 is not below the threshold.",
            "created_at": NOW,
        }
    )
    scorecard_data = make_scorecard_data()
    scorecard_data.update(
        {
            "result_inventory": {
                "episode_ids": ["E001"],
                "grader_result_ids": ["GR001"],
                "metric_result_ids": ["MR001"],
                "gate_result_ids": ["GATER001"],
                "missing_applications": [],
            },
            "overall_score_outcome": {
                "policy_ref": scorecard_data["overall_score_outcome"]["policy_ref"],
                "evaluation_status": "disabled",
                "canonical_value": None,
                "contribution_traces": [],
                "total_selected_weight": None,
                "available_weight": None,
                "available_weight_fraction": None,
                "minimum_required_weight_fraction": None,
                "final_included_denominator": None,
                "unavailable_reason": None,
                "diagnostic_ids": [],
                "explanation": "Overall policy is disabled.",
            },
            "acceptance_evaluation": {
                "policy_ref": scorecard_data["acceptance_evaluation"]["policy_ref"],
                "evaluation_status": "disabled",
                "acceptance": None,
                "gate_contributions": [],
                "diagnostic_ids": [],
                "explanation": "Acceptance policy is disabled.",
            },
            "finalization_status": "finalized_evaluation",
            "finalized_at": NOW,
        }
    )
    scorecard = Scorecard.model_validate(scorecard_data)
    return RuntimeGraph(
        benchmark=benchmark,
        run=run,
        episodes=[episode],
        artifacts=[artifact],
        evidence=[evidence],
        grader_results=[grader_result],
        metric_results=[metric_result],
        gate_results=[gate_result],
        diagnostics=[],
        scorecard=scorecard,
    )


def codes(report: ValidationReport) -> set[str]:
    return {issue.code for issue in report.issues}
