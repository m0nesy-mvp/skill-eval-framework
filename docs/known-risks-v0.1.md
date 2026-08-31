# Known Risks v0.1

## 1. Purpose and scope

This document records risks explicitly accepted for the internal v0.1 release of
`skill-eval-framework`.

It is a release risk register. It does not modify the Frozen Definition,
Evaluation, Runtime, or Result design, and it does not claim that an accepted
risk has been fixed or closed.

## 2. AUDIT-001 — Derived semantic results are not independently recomputed

**Status:** `ACCEPTED_RISK`

**Original audit severity:** `P0` under the original strict audit model

**Scope:** internal trusted execution environment

### 2.1 Technical finding

Final integrity currently validates structural and reference integrity, but it
does not independently recompute caller-supplied `MetricResult`, `GateResult`,
`OverallScoreOutcome`, or `AcceptanceEvaluation` semantics.

This preserves the Full Design-to-Code Audit finding: a direct Python caller can
construct derived Result objects that are structurally valid but semantically
incorrect, and current final integrity can accept those objects without
expected-vs-actual semantic verification.

### 2.2 Risk acceptance decision

AUDIT-001 is accepted for the internal v0.1 release because the supported
internal execution workflow derives all semantic Results exclusively through
the deterministic evaluation services:

```text
GraderResults
-> deterministic Metric evaluator
-> deterministic Gate evaluator
-> Overall evaluator
-> Acceptance evaluator
-> finalization
```

Supplying business-constructed derived semantic Result objects directly to
finalization is outside the supported execution workflow.

### 2.3 Residual risk

Direct Python callers can still construct structurally valid but semantically
incorrect derived Result objects. Current final integrity does not independently
recompute their semantics, so the trusted-environment assumption remains an
enforced workflow convention rather than a finalization-boundary guarantee.

### 2.4 Mitigation

The official CLI and orchestration path MUST pass only derived Results produced
by the deterministic Metric, Gate, Overall, and Acceptance evaluation services.
They MUST NOT treat business-constructed derived semantic Results as a supported
input to finalization.

### 2.5 Future hardening

Add deterministic semantic-integrity recomputation, or equivalent
expected-vs-actual verification, at the finalization boundary. The verification
should reuse the deterministic evaluation authority rather than introduce a
second implementation of Metric, Gate, Overall, or Acceptance semantics.

### 2.6 Non-closure statement

```text
AUDIT-001 != CLOSED
AUDIT-001 != FIXED
AUDIT-001 == ACCEPTED_RISK
```

The risk acceptance decision changes release treatment only. It does not lower
the original finding's severity under the strict audit model, alter its
technical facts, or provide evidence that semantic-integrity verification has
been implemented.
