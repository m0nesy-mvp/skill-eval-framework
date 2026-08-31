# Runtime evaluation

## Three layers

```text
Definition -> Runtime -> Result
```

- Definition freezes what will be tested, what Evidence is required, and how
  deterministic results are derived.
- Runtime records one Run, its planned attempts, Episodes, trace facts,
  Artifacts, qualified Evidence, GraderResults, and diagnostics.
- Result contains framework-derived MetricResults, GateResults, Overall,
  Acceptance, and the final Scorecard.

One Run binds exactly one frozen Definition and one Subject identity. An
Episode is one scheduled Test Case attempt within that Run.

## Supported evaluation boundary

The CLI input may contain deterministic identity/timestamp fields, the Run
plan, completed Runtime facts, Artifacts, qualified Evidence, GraderResults,
diagnostics, and IDs for results the Framework will create. It must not contain
caller-produced MetricResults, GateResults, OverallScoreOutcome, or
AcceptanceEvaluation.

The deterministic flow is:

```text
GraderResults
-> MetricResults
-> GateResults
-> OverallScoreOutcome
-> AcceptanceEvaluation
-> Scorecard
```

The Scorecard inventory distinguishes expected, actual, and missing
applications. A missing GraderResult can make a Metric unavailable and a Gate
indeterminate without making the Runtime graph structurally invalid.

## Identity and finalization rules

- Bind benchmark ID, Definition version, closure profile, and exact digest.
- For v0.3 use closure profile v1 only.
- Preserve assigned attempt indexes even when an attempt is blocked or fails.
- Use deterministic IDs and timestamps in the input; the CLI does not invent
  random IDs or current timestamps.
- A digest/profile mismatch is an identity error, not a warning.
- Preserve the original Run. A changed Definition produces a new digest and a
  new Run rather than overwriting evidence.

For the full Runtime/Result model, see
`docs/guides/runtime-result-design-guide-v0.md`.
