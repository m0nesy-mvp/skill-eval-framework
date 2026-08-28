"""Representative frozen-schema fixtures."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any

import pytest

NOW = datetime(2026, 8, 28, 10, 0, 0)
DIGEST = "sha256:" + "a" * 64


def make_definition_data() -> dict[str, Any]:
    return {
        "benchmark_id": "skill.eval.v0",
        "name": "Skill evaluation",
        "version": "0.1.0",
        "description": "Representative frozen definition",
        "status": "frozen",
        "requirements": [
            {
                "requirement_id": "R001",
                "statement": "The subject returns the expected outcome.",
                "source": "skill",
                "source_ref": "SKILL.md#workflow",
                "evaluation_type": "outcome",
            }
        ],
        "contracts": [
            {
                "contract_id": "C001",
                "requirement_ids": ["R001"],
                "statement": "The expected outcome is observable.",
                "evaluation_type": "outcome",
                "criticality": "critical",
                "success_criteria": ["Expected output exists."],
                "failure_criteria": ["Expected output is absent."],
                "failure_modes": ["The subject omits the output."],
            }
        ],
        "test_cases": [
            {
                "test_case_id": "TC001",
                "task": "Produce the expected output.",
                "preconditions": [],
                "fixtures": [],
                "initial_state": [],
                "interaction_steps": [
                    {"trigger": "Request the output.", "response": "Subject responds."}
                ],
                "expected_assertions": [
                    {"contract_id": "C001", "expectation": "Output is present."}
                ],
            }
        ],
        "evidence_specifications": [
            {
                "evidence_spec_id": "ES001",
                "targets": [{"test_case_id": "TC001", "contract_id": "C001"}],
                "observation_requirements": ["Observe the response."],
                "provenance_requirements": ["Retain the trace reference."],
                "context_requirements": [],
                "qualification_requirements": ["The response is attributable."],
            }
        ],
        "grader_specifications": [
            {
                "grader_id": "G001",
                "targets": [
                    {
                        "test_case_id": "TC001",
                        "contract_id": "C001",
                        "evidence_spec_ids": ["ES001"],
                    }
                ],
                "judgment_criteria": ["Compare observation with the contract."],
                "result_semantics": {
                    "satisfied": "The contract is supported.",
                    "violated": "The contract is contradicted.",
                    "insufficient_evidence": "The evidence cannot decide.",
                    "not_exercised": "The condition was not exercised.",
                },
                "insufficiency_handling": ["List missing observations."],
                "explanation_requirements": ["Cite evidence contributions."],
                "rubric": None,
            }
        ],
        "metric_specifications": [
            {
                "metric_id": "M001",
                "name": "Contract satisfaction rate",
                "inputs": [{"test_case_id": "TC001", "contract_id": "C001"}],
                "result_selection_policy": "Use the final distinct attempt.",
                "aggregation_unit": "contract application",
                "eligibility_policy": {
                    "eligible_result_semantics": ["satisfied", "violated"],
                    "non_substantive_handling": ["Exclude not_exercised."],
                    "unavailable_input_handling": ["Report missing inputs."],
                },
                "contribution_mapping": [
                    {"source_semantics": "satisfied", "contribution_semantics": "1"},
                    {"source_semantics": "violated", "contribution_semantics": "0"},
                ],
                "unit_reduction": "One contribution per contract application.",
                "aggregation_rule": "Arithmetic mean.",
                "weighting_policy": "Equal weight.",
                "completeness_policy": {
                    "minimum_input_requirement": "At least one eligible input.",
                    "partial_result_policy": "Allow a partial result.",
                    "empty_denominator_policy": "Return unavailable.",
                    "transparency_requirements": ["Report the denominator."],
                },
                "result_semantics": {
                    "interpretation": "Share of satisfied applications.",
                    "direction": "Higher is better.",
                    "scale": "Unit interval.",
                    "denominator_meaning": "Eligible contract applications.",
                },
            }
        ],
        "gate_specifications": [
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
                "result_semantics": {
                    "open_meaning": "Threshold is met.",
                    "triggered_meaning": "Threshold is missed.",
                    "indeterminate_meaning": "Metric is unavailable.",
                    "blocking_effect": "Blocks acceptance when participating.",
                },
                "explanation_requirements": ["Report the compared canonical value."],
            }
        ],
        "overall_score_policy": {"mode": "disabled"},
        "acceptance_policy": {"mode": "disabled"},
        "semantic_resource_bindings": [],
    }


def make_run_data() -> dict[str, Any]:
    return {
        "run_id": "RUN001",
        "definition_ref": {
            "benchmark_id": "skill.eval.v0",
            "benchmark_version": "0.1.0",
            "definition_closure_profile": "skill-eval-frozen-definition-closure-v0",
            "definition_digest": DIGEST,
            "definition_snapshot_ref": "definitions/skill.eval.v0.json",
        },
        "subject_ref": {
            "subject_ref": "repo:example@abc123",
            "subject_kind": "repository_revision",
            "version_ref": "abc123",
            "content_digest": None,
            "identity_metadata": {"platform": "windows", "revision_number": 1},
        },
        "execution_context": {
            "execution_context_id": "CTX001",
            "orchestrator": "pytest-fixture",
            "environment_ref": None,
            "configuration_ref": None,
            "configuration_digest": None,
            "context_metadata": {"profile": "test"},
        },
        "execution_plan": {
            "test_cases": [
                {
                    "test_case_id": "TC001",
                    "disposition": "scheduled",
                    "attempt_slots": [{"attempt_index": 1}],
                    "reason": None,
                }
            ]
        },
        "execution_status": "created",
        "validity_status": "pending",
        "validity_findings": [],
        "created_at": NOW,
        "started_at": None,
        "ended_at": None,
        "episode_ids": [],
        "diagnostic_ids": [],
    }


def make_scorecard_data() -> dict[str, Any]:
    run = make_run_data()
    return {
        "scorecard_id": "SC001",
        "run_id": "RUN001",
        "definition_ref": deepcopy(run["definition_ref"]),
        "subject_ref": deepcopy(run["subject_ref"]),
        "result_inventory": {
            "episode_ids": [],
            "grader_result_ids": [],
            "metric_result_ids": [],
            "gate_result_ids": [],
            "missing_applications": [],
        },
        "diagnostic_ids": [],
        "overall_score_outcome": {
            "policy_ref": {
                "definition_digest": DIGEST,
                "policy_path": "/overall_score_policy",
            },
            "evaluation_status": "not_produced_run_pending",
            "canonical_value": None,
            "contribution_traces": [],
            "total_selected_weight": None,
            "available_weight": None,
            "available_weight_fraction": None,
            "minimum_required_weight_fraction": None,
            "final_included_denominator": None,
            "unavailable_reason": None,
            "diagnostic_ids": [],
            "explanation": "Run validity is pending.",
        },
        "acceptance_evaluation": {
            "policy_ref": {
                "definition_digest": DIGEST,
                "policy_path": "/acceptance_policy",
            },
            "evaluation_status": "not_produced_run_pending",
            "acceptance": None,
            "gate_contributions": [],
            "diagnostic_ids": [],
            "explanation": "Run validity is pending.",
        },
        "finalization_status": "interim",
        "finalized_at": None,
    }


@pytest.fixture
def definition_data() -> dict[str, Any]:
    return make_definition_data()


@pytest.fixture
def run_data() -> dict[str, Any]:
    return make_run_data()


@pytest.fixture
def scorecard_data() -> dict[str, Any]:
    return make_scorecard_data()
