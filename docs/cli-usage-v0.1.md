# Skill Eval CLI usage v0.1

## Scope

The v0.1 CLI is a thin JSON entry point over the existing schema, validation,
digest, Runtime, and evaluation APIs. It supports explicit executable
`BenchmarkDefinitionV03` inputs only. It is not a subject executor, grader
platform, registry, or reporting application.

This document describes the repository-local development installation. Formal
release packaging is intentionally out of scope.

## Development installation

From the repository root on Windows:

```powershell
uv sync --frozen --extra dev
```

This installs the `skill-eval` console entry point into `.venv\Scripts`.

## Commands

Validate the structure and cross-object graph of an executable v0.3 Definition:

```powershell
.venv\Scripts\skill-eval.exe validate tests\fixtures\e2e\controlled\definition.json
```

Compute its canonical v1 digest:

```powershell
.venv\Scripts\skill-eval.exe digest tests\fixtures\e2e\controlled\definition.json
```

Run the deterministic evaluation pipeline and write a complete JSON bundle:

```powershell
.venv\Scripts\skill-eval.exe evaluate `
  --definition tests\fixtures\e2e\controlled\definition.json `
  --run-input tests\fixtures\e2e\controlled\run-input.json `
  --output evaluation.json
```

Success writes a compact JSON summary to stdout and the full result bundle to
the requested output path. Failures write a structured JSON object to stderr
and return a non-zero exit code.

## Evaluation input contract

The root `input_version` must be `skill-eval-evaluation-input/v0.1`. The input
contains only caller-controlled identity, fixed timestamps and IDs, execution
plan, completed Episode facts, Artifacts, qualified Evidence, GraderResults,
and Runtime diagnostics.

The `definition_ref` must bind all of these fields explicitly:

- the same benchmark ID and benchmark version as the Definition;
- `skill-eval-frozen-definition-closure-v1`;
- the exact digest printed by `skill-eval digest`;
- an optional snapshot reference.

`result_ids` supplies stable IDs for the MetricResults, GateResults, and
Scorecard that the framework will produce. Its Metric and Gate keys must
exactly match the Definition.

The input schema forbids extra fields. In particular, it does not accept
caller-provided `metric_results`, `gate_results`, `overall_score_outcome`, or
`acceptance_evaluation`.

## Evaluation output contract

The output root is `skill-eval-evaluation-output/v0.1` and includes:

- Definition identity and closure profile;
- the finalized valid Run and completed Episodes;
- upstream Artifacts, Evidence, GraderResults, and diagnostics;
- framework-produced MetricResults and GateResults;
- framework-produced OverallScoreOutcome and AcceptanceEvaluation;
- the finalized Scorecard and complete actual/missing inventory.

All IDs and timestamps that enter authoritative output come from the input.
The CLI does not call `uuid4`, `datetime.now`, or random generators. Repeating
an evaluation with the same files produces byte-identical output JSON.

## Real Skill example

The `real-skill` fixture represents a small Structured Task Summary Skill. The
Skill instructions require a JSON object with exactly `summary`, `priority`,
and `next_action`. Subject execution is deliberately represented by the
pre-generated `subject-output.json` fixture; it is separate from framework
evaluation.

Run it with:

```powershell
.venv\Scripts\skill-eval.exe evaluate `
  --definition tests\fixtures\e2e\real-skill\definition.json `
  --run-input tests\fixtures\e2e\real-skill\run-input.json `
  --output real-skill-evaluation.json
```

The qualified evidence supports a `satisfied` GraderResult. The deterministic
Metric therefore equals `1`; the Gate checks whether that value is less than
`1`, so it remains `OPEN`; Overall is `1.00`; Acceptance is `ACCEPTABLE`; and
the Scorecard is `finalized_evaluation` with no missing applications.

## Error categories

Structured stderr distinguishes:

- `io_error`;
- `input_schema_error`;
- `definition_schema_error`;
- `definition_validation_error` with Definition issue codes;
- `definition_identity_error` with digest/profile binding issue codes;
- `runtime_graph_error` with Runtime issue codes;
- `evaluation_error`;
- `finalization_error`.

## Trusted-boundary limitation

AUDIT-001 remains an accepted risk for trusted internal operation. The
supported CLI path enforces its mitigation: caller-provided GraderResults are
the final externally supplied semantic products, and the CLI then invokes the
framework's deterministic Metric, Gate, Overall, and Acceptance authorities
before Runtime and Scorecard finalization.

The CLI does not prove semantic recomputation for arbitrary caller-constructed
derived Results. Callers that bypass this supported path remain outside the
supported trust boundary.

AUDIT-006 also remains open and non-blocking for this internal CLI. The CLI
avoids the public v0.2/v0.3 ambiguity by selecting `BenchmarkDefinitionV03`
and the v1 closure profile explicitly. Public API cleanup remains a packaging
readiness concern.
