"""Object-local tests for Runtime models."""

from copy import deepcopy
from datetime import datetime
from typing import Any

import pytest
from conftest import DIGEST, NOW
from pydantic import ValidationError

from skill_eval_framework.schemas.runtime import (
    Artifact,
    Episode,
    Evidence,
    Run,
    RunExecutionPlan,
    RunTestCasePlan,
    TraceEvent,
)


def test_representative_pending_run_is_valid(run_data: dict[str, Any]) -> None:
    run = Run.model_validate(run_data)
    assert run.logical_key == "RUN001"


def test_scheduled_plan_requires_attempt_slot() -> None:
    with pytest.raises(ValidationError, match="at least one attempt slot"):
        RunTestCasePlan.model_validate(
            {
                "test_case_id": "TC001",
                "disposition": "scheduled",
                "attempt_slots": [],
                "reason": None,
            }
        )


def test_valid_scheduled_plan_accepts_ordered_slots() -> None:
    plan = RunTestCasePlan.model_validate(
        {
            "test_case_id": "TC001",
            "disposition": "scheduled",
            "attempt_slots": [{"attempt_index": 1}, {"attempt_index": 2}],
        }
    )
    assert [slot.attempt_index for slot in plan.attempt_slots] == [1, 2]


def test_intentionally_unscheduled_plan_rejects_attempt_slots() -> None:
    with pytest.raises(ValidationError, match="must have no slots"):
        RunTestCasePlan.model_validate(
            {
                "test_case_id": "TC001",
                "disposition": "intentionally_not_scheduled",
                "attempt_slots": [{"attempt_index": 1}],
                "reason": "Excluded by the frozen plan.",
            }
        )


def test_intentionally_unscheduled_plan_requires_reason() -> None:
    with pytest.raises(ValidationError, match="requires a reason"):
        RunTestCasePlan.model_validate(
            {
                "test_case_id": "TC001",
                "disposition": "intentionally_not_scheduled",
                "attempt_slots": [],
                "reason": None,
            }
        )


def test_attempt_slots_must_start_at_one() -> None:
    with pytest.raises(ValidationError, match="start at 1"):
        RunTestCasePlan.model_validate(
            {
                "test_case_id": "TC001",
                "disposition": "scheduled",
                "attempt_slots": [{"attempt_index": 2}, {"attempt_index": 3}],
            }
        )


def test_attempt_slots_must_be_strictly_increasing() -> None:
    with pytest.raises(ValidationError, match="strictly increasing"):
        RunTestCasePlan.model_validate(
            {
                "test_case_id": "TC001",
                "disposition": "scheduled",
                "attempt_slots": [{"attempt_index": 1}, {"attempt_index": 3}, {"attempt_index": 2}],
            }
        )


def test_attempt_slots_reject_duplicate_indexes() -> None:
    with pytest.raises(ValidationError, match="duplicate"):
        RunTestCasePlan.model_validate(
            {
                "test_case_id": "TC001",
                "disposition": "scheduled",
                "attempt_slots": [{"attempt_index": 1}, {"attempt_index": 1}],
            }
        )


def test_attempt_slot_index_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        RunTestCasePlan.model_validate(
            {
                "test_case_id": "TC001",
                "disposition": "scheduled",
                "attempt_slots": [{"attempt_index": 0}],
            }
        )


def test_execution_plan_rejects_duplicate_test_cases() -> None:
    case = {
        "test_case_id": "TC001",
        "disposition": "scheduled",
        "attempt_slots": [{"attempt_index": 1}],
    }
    with pytest.raises(ValidationError, match="test_cases.test_case_id"):
        RunExecutionPlan.model_validate({"test_cases": [case, case]})


def test_invalid_run_requires_confirmed_finding(run_data: dict[str, Any]) -> None:
    run_data["validity_status"] = "invalid"
    with pytest.raises(ValidationError, match="requires at least one validity finding"):
        Run.model_validate(run_data)


def test_valid_run_rejects_confirmed_finding(run_data: dict[str, Any]) -> None:
    run_data["validity_status"] = "valid"
    run_data["validity_findings"] = [
        {
            "code": "DIGEST_MISMATCH",
            "stage": "pre_execution",
            "message": "Digest does not match.",
            "related_object_refs": [{"object_type": "definition", "object_ref": DIGEST}],
        }
    ]
    with pytest.raises(ValidationError, match="only invalid Run"):
        Run.model_validate(run_data)


def test_terminal_run_requires_ended_at(run_data: dict[str, Any]) -> None:
    run_data["execution_status"] = "completed"
    with pytest.raises(ValidationError, match="requires ended_at"):
        Run.model_validate(run_data)


def test_partial_run_requires_actual_episode(run_data: dict[str, Any]) -> None:
    run_data["execution_status"] = "partial"
    run_data["started_at"] = NOW
    run_data["ended_at"] = NOW
    with pytest.raises(ValidationError, match="requires at least one Episode"):
        Run.model_validate(run_data)


def test_trace_event_requires_summary_or_content_ref() -> None:
    with pytest.raises(ValidationError, match="semantic_summary or content_ref"):
        TraceEvent.model_validate(
            {
                "trace_event_id": "TE001",
                "event_index": 1,
                "actor": "subject",
                "event_type": "message",
            }
        )


def test_episode_trace_indexes_are_strictly_increasing() -> None:
    data = {
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
                "trace_event_id": "TE002",
                "event_index": 2,
                "actor": "subject",
                "event_type": "message",
                "semantic_summary": "Second",
            },
            {
                "trace_event_id": "TE001",
                "event_index": 1,
                "actor": "user",
                "event_type": "message",
                "semantic_summary": "First",
            },
        ],
        "artifact_ids": [],
        "evidence_ids": [],
        "diagnostic_ids": [],
    }
    with pytest.raises(ValidationError, match="strictly increasing"):
        Episode.model_validate(data)


def test_artifact_trace_relation_requires_episode() -> None:
    with pytest.raises(ValidationError, match="requires episode_id"):
        Artifact.model_validate(
            {
                "artifact_id": "A001",
                "run_id": "RUN001",
                "artifact_kind": "response",
                "locator": "artifact://A001",
                "producer": "subject",
                "relations": [
                    {
                        "relation": "produced",
                        "trace_event_id": "TE001",
                        "source": "trace",
                    }
                ],
            }
        )


def test_artifact_requires_at_least_one_relation() -> None:
    with pytest.raises(ValidationError):
        Artifact.model_validate(
            {
                "artifact_id": "A001",
                "run_id": "RUN001",
                "artifact_kind": "response",
                "locator": "artifact://A001",
                "producer": "subject",
                "relations": [],
            }
        )


def test_evidence_qualification_only_accepts_passed_checks() -> None:
    data = {
        "evidence_id": "EV001",
        "run_id": "RUN001",
        "episode_id": "E001",
        "evidence_spec_id": "ES001",
        "qualified_targets": [{"test_case_id": "TC001", "contract_id": "C001"}],
        "observation": {"summary": "Expected output exists."},
        "provenance": {
            "source_refs": [{"source_type": "trace_event", "source_id": "TE001"}],
            "collector": "trace collector",
            "observed_from": "subject response",
        },
        "context": {"context_summary": "Test response", "related_trace_event_ids": ["TE001"]},
        "qualification": {
            "status": "qualified",
            "checks": [{"requirement": "Attributable", "outcome": "failed", "detail": "No"}],
            "qualified_by": "collector",
            "qualified_at": datetime(2026, 8, 28, 10, 1),
        },
    }
    with pytest.raises(ValidationError):
        Evidence.model_validate(data)


def test_nested_unknown_runtime_field_is_forbidden(run_data: dict[str, Any]) -> None:
    data = deepcopy(run_data)
    data["definition_ref"]["fallback_digest"] = DIGEST
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        Run.model_validate(data)
