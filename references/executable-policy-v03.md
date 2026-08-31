# Executable policy v0.3

`BenchmarkDefinitionV03` replaces the historical v0.2 executable free-text
Metric and direct-Grader Gate policies with closed typed policy objects.

## Metric boundary

The deterministic pipeline is:

```text
resolve inputs
-> select attempts
-> apply eligibility
-> map contributions
-> derive aggregation units
-> reduce each unit
-> apply weights
-> aggregate
-> apply completeness
```

Supported v0.3 choices are deliberately narrow: explicit attempt selectors,
typed eligible semantics, exact Decimal contributions, `per_target`,
`per_contract`, or `per_test_case` units, `single`/`mean`/`final_eligible`
reduction, equal per-unit weighting, mean aggregation, and strict completeness
with an unavailable empty denominator.

`final_eligible` requires `all_distinct` selection and exactly one MetricInput
per derived aggregation unit. The Framework never invents cross-input attempt
ordering.

## Gate boundary

Metric-threshold and availability conditions remain typed. Direct-Grader Gates
reuse the typed attempt-selection policy, explicit trigger semantics, and an
`any` or `all` quantifier. Gate unavailable handling is applied after the whole
condition is evaluated; an individual unknown input does not automatically
override an otherwise determined condition.

## Version and compatibility

- v0.3 executable root: `BenchmarkDefinitionV03`;
- v0.3 digest profile: `skill-eval-frozen-definition-closure-v1`;
- v0.2 compatibility root: `BenchmarkDefinitionV02`;
- v0.2 historical profile: `skill-eval-frozen-definition-closure-v0`.

The CLI never accepts v0.2 free-text policy as executable input. Advanced
formula DSLs, custom weighting, statistical estimators, nested boolean/count
Gates, and automatic v0.2 migration remain outside v0.3.

Detailed authority:

- `docs/executable-evaluation-policy-hardening-design-v0.1.md`;
- `docs/final-eligible-aggregation-hardening-v0.1.md`;
- `docs/public-api-version-policy-v0.1.md`.
