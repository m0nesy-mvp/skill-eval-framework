"""Deterministic whole-Benchmark Acceptance propagation from Gate Results."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from skill_eval_framework.schemas.definition import (
    AcceptancePolicy,
    DisabledAcceptancePolicy,
    GateBasedAcceptancePolicy,
)
from skill_eval_framework.schemas.results import (
    AcceptanceEvaluation,
    AcceptanceEvaluationStatus,
    AcceptanceGateContributionTrace,
    AcceptanceSemantic,
    DefinitionPolicyRef,
    GateResult,
    GateSemantic,
)

from .errors import AcceptanceEvaluationError


def evaluate_acceptance(
    policy: AcceptancePolicy,
    *,
    run_id: str,
    definition_digest: str,
    gate_results: Sequence[GateResult] = (),
    run_state: str = "valid",
) -> AcceptanceEvaluation:
    """Evaluate only explicit participating Gates; Overall is intentionally ignored."""

    policy_ref = DefinitionPolicyRef(
        definition_digest=definition_digest,
        policy_path="/acceptance_policy",
    )
    if run_state == "pending":
        status = AcceptanceEvaluationStatus.NOT_PRODUCED_RUN_PENDING
        return AcceptanceEvaluation(
            policy_ref=policy_ref,
            evaluation_status=status,
            acceptance=None,
            gate_contributions=[],
            diagnostic_ids=[],
            explanation="Acceptance is not produced while the Run is pending.",
        )
    if run_state == "invalid":
        return AcceptanceEvaluation(
            policy_ref=policy_ref,
            evaluation_status=AcceptanceEvaluationStatus.NOT_PRODUCED_RUN_INVALID,
            acceptance=None,
            gate_contributions=[],
            diagnostic_ids=[],
            explanation="Acceptance is not produced for an invalid Run.",
        )
    if run_state != "valid":
        raise AcceptanceEvaluationError(f"unsupported Run state: {run_state!r}")
    if isinstance(policy, DisabledAcceptancePolicy):
        return AcceptanceEvaluation(
            policy_ref=policy_ref,
            evaluation_status=AcceptanceEvaluationStatus.DISABLED,
            acceptance=None,
            gate_contributions=[],
            diagnostic_ids=[],
            explanation="Acceptance policy is disabled.",
        )
    if not isinstance(policy, GateBasedAcceptancePolicy):
        raise AcceptanceEvaluationError(f"unsupported Acceptance policy: {type(policy).__name__}")

    by_gate: dict[str, GateResult] = {}
    for result in gate_results:
        if result.run_id != run_id:
            raise AcceptanceEvaluationError("Acceptance inputs must belong to the current Run")
        if result.gate_id in by_gate:
            raise AcceptanceEvaluationError(f"duplicate GateResult for gate {result.gate_id!r}")
        by_gate[result.gate_id] = result

    traces: list[AcceptanceGateContributionTrace] = []
    blocked = False
    indeterminate = False
    for contribution in sorted(policy.participating_gates, key=lambda item: item.gate_id):
        handling: Literal["open", "actual_triggered", "overall_indeterminate", "overall_blocked"]
        gate_result = by_gate.get(contribution.gate_id)
        if gate_result is None:
            state = "MISSING"
            handling = contribution.missing_result_handling
            if handling == "overall_blocked":
                blocked = True
                propagation = "blocked"
            else:
                indeterminate = True
                propagation = "indeterminate"
            explanation = f"Required Gate {contribution.gate_id} Result is missing."
            result_id = None
        else:
            result_id = gate_result.gate_result_id
            state = GateSemantic(gate_result.result).value
            if gate_result.result == GateSemantic.TRIGGERED:
                handling = "actual_triggered"
                blocked = True
                propagation = "blocked"
                explanation = f"Gate {contribution.gate_id} is actually TRIGGERED."
            elif gate_result.result == GateSemantic.INDETERMINATE:
                handling = contribution.indeterminate_handling
                if handling == "overall_blocked":
                    blocked = True
                    propagation = "blocked"
                else:
                    indeterminate = True
                    propagation = "indeterminate"
                explanation = (
                    f"Gate {contribution.gate_id} is INDETERMINATE; policy propagation applied."
                )
            else:
                handling = "open"
                propagation = "no_block"
                explanation = f"Gate {contribution.gate_id} is OPEN."
        traces.append(
            AcceptanceGateContributionTrace(
                gate_id=contribution.gate_id,
                gate_result_id=result_id,
                application_state=state,
                policy_handling=handling,
                propagation_outcome=propagation,
                explanation=explanation,
            )
        )

    if blocked:
        semantic = AcceptanceSemantic.BLOCKED
        explanation = "Acceptance is BLOCKED by a participating Gate or fail-closed policy."
    elif indeterminate:
        semantic = AcceptanceSemantic.INDETERMINATE
        explanation = "Acceptance is INDETERMINATE because a participating Gate is unresolved."
    else:
        semantic = AcceptanceSemantic.ACCEPTABLE
        explanation = "All participating Gate Results are OPEN."
    return AcceptanceEvaluation(
        policy_ref=policy_ref,
        evaluation_status=AcceptanceEvaluationStatus.PRODUCED,
        acceptance=semantic,
        gate_contributions=traces,
        diagnostic_ids=[],
        explanation=explanation,
    )


__all__ = ["evaluate_acceptance"]
