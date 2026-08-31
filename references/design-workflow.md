# Benchmark design workflow

Use this reference when the benchmark has not yet reached a frozen executable
Definition. The authoritative design chain is:

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
```

## Operating rules

1. Read the Target Skill entrypoint and only its delegated resources. Separate
   normative requirements from implementation facts and assumptions.
2. Freeze Requirements before treating Contracts as authoritative. Every
   Contract must state observable success, failure, and failure modes.
3. Give every expected assertion a Test Case and Contract identity. Design
   normal, negative, missing-prerequisite, and boundary cases as applicable.
4. Specify the observation, provenance, context, and qualification required for
   Evidence before running a case.
5. Make each Grader target and result semantics explicit. GraderResult is the
   final externally supplied semantic product in the supported CLI workflow.
6. Define typed Metric and Gate policies before execution. Do not encode
   executable behavior in prose.
7. Validate all references and coverage, freeze the Definition, then compute
   its digest. Never alter a frozen Definition in place after seeing results.

## Detailed design references

| Design stage | Repository authority |
|---|---|
| End-to-end process | `docs/universal-skill-eval-design-process-v1.1-scope-frozen.md` |
| Requirement | `docs/guides/requirement-extraction-guide-v0.1.md` |
| Contract | `docs/guides/contract-design-guide-v0.md` |
| Test Case | `docs/guides/test-case-design-guide-v0.md` |
| Evidence | `docs/guides/evidence-specification-guide-v0.md` |
| Grader | `docs/guides/grader-specification-guide-v0.md` |
| Metric | `docs/guides/metric-specification-guide-v0.md` |
| Gate | `docs/guides/gate-specification-guide-v0.md` |

These detailed documents preserve design history and frozen decisions. Their
historical readiness labels do not override the current executable v0.3 public
API or the current repository test result.
