---
name: skill-eval-framework
description: Design Skill benchmarks and deterministically validate, digest, and evaluate executable BenchmarkDefinitionV03 files into traceable Scorecards.
---

# Skill Eval Framework

## Purpose

Use this Skill to turn a designed Skill benchmark into a deterministic,
traceable evaluation. The Framework validates a frozen Benchmark Definition,
computes its content identity, consumes completed Runtime facts and
GraderResults, derives Metric/Gate/Overall/Acceptance results, and produces a
Scorecard.

The repository also contains design references for moving from Skill
requirements to Contracts, Test Cases, Evidence, Graders, Metrics, and Gates.

## When to use

Use this Skill when you need to:

- design a benchmark for an Agent Skill;
- validate an executable Benchmark Definition;
- compute a stable Definition digest;
- run deterministic evaluation from qualified upstream products;
- generate a traceable Scorecard;
- audit Definition, Runtime, and Result consistency.

## When not to use

This is not a general Agent runtime, LLM grader hosting platform, browser
automation system, generic Subject executor, benchmark leaderboard, or
scientific meta-evaluation platform. Subject execution and semantic grading
remain outside the deterministic CLI boundary.

## Core workflow

```text
Target Skill
-> Requirement
-> Contract
-> Test Case
-> Evidence Specification
-> Grader Specification
-> Metric Specification
-> Gate Specification
-> BenchmarkDefinitionV03
-> validation
-> digest v1
-> Runtime
-> GraderResults
-> Metric
-> Gate
-> Overall / Acceptance
-> Scorecard
```

Read [references/design-workflow.md](references/design-workflow.md) when the
benchmark is not yet designed. Read
[references/runtime-evaluation.md](references/runtime-evaluation.md) before
constructing evaluation input.

## Operating procedure

1. Confirm the Target Skill revision and freeze its authoritative requirements.
2. Design the benchmark objects using the references; do not invent Runtime
   results before the Definition is frozen.
3. Author a `BenchmarkDefinitionV03` JSON document.
4. Run `skill-eval validate` and stop on any schema or cross-object issue.
5. Run `skill-eval digest`; bind the exact v1 digest and Definition identity
   into the Run input.
6. Execute the Subject and graders outside this Framework. Supply only Runtime
   facts, qualified Evidence, GraderResults, deterministic IDs, and timestamps.
7. Run `skill-eval evaluate` and inspect the output Scorecard, missing-result
   inventory, diagnostics, Metric/Gate results, Overall, and Acceptance.
8. Preserve the frozen Definition, input, output, command, exit code, and
   revision together. A revised Definition requires a new digest and Run.

## Deterministic entrypoints

The existing CLI is the sole deterministic script authority. Do not copy its
Metric, Gate, Overall, Acceptance, Runtime, or digest logic into wrappers.

```powershell
skill-eval validate assets\examples\minimal\definition.json
skill-eval digest assets\examples\minimal\definition.json
skill-eval evaluate `
  --definition assets\examples\minimal\definition.json `
  --run-input assets\examples\minimal\run-input.json `
  --output example-evaluation.json
```

See [references/cli.md](references/cli.md) for installation, input/output
contracts, errors, and verified example outcomes.

## Version boundary

- `BenchmarkDefinitionV03` is the current executable Definition.
- v0.3 uses `skill-eval-frozen-definition-closure-v1`.
- `BenchmarkDefinitionV02` is historical compatibility only.
- v0.2 uses `skill-eval-frozen-definition-closure-v0`.
- The CLI accepts v0.3 only; v0.2 free-text policy never enters its executable
  path.

Read [references/executable-policy-v03.md](references/executable-policy-v03.md)
and [docs/public-api-version-policy-v0.1.md](docs/public-api-version-policy-v0.1.md)
before using the Python API directly.

## Known limitation

`AUDIT-001` remains `ACCEPTED_RISK`. The supported CLI accepts upstream Runtime
products and GraderResults only; the Framework derives Metric, Gate, Overall,
and Acceptance results itself. A direct Python caller can bypass this path and
submit structurally valid but semantically incorrect derived Results to final
integrity checks. This residual risk is documented, not fixed.

Do not claim whole-Skill correctness from one passing case, and do not treat a
passing structural check as proof that Evidence or Grader judgment is
semantically correct.
