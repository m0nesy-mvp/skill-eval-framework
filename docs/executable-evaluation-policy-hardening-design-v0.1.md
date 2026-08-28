# Executable Evaluation Policy Hardening Design v0.1

Status: `EXECUTABLE_EVALUATION_POLICY_DESIGN_V0_FREEZE_READY: YES`

Scope: successor design for the implementation-discovered Metric and direct-Grader Gate execution blocker.

This document does not implement Python services. It defines the smallest machine-readable policy surface that a later implementation may consume. The historical v0.2 Definition design and its evidence remain unchanged.

## 1. Baseline and blocker

The implementation baseline is:

```text
dfbca2870e73da9fbfdb8794b24caa950db78e9e
feat: implement frozen definition digest
```

The previous Evaluation Services attempt established two real blockers:

1. `MetricSpecification` carries several execution authorities as unconstrained strings.
2. `GraderResultGateCondition.result_selection_policy` carries the same kind of unconstrained selection authority.

The problem is not that the strings are hard to parse. The problem is that two conforming implementations have no frozen rule that tells them which interpretation is authoritative. A substring test, regular expression, NLP interpretation, hidden conventional phrase, expression parser, or `eval` would create a new implementation-specific authority.

The hardening target is therefore:

```text
Definition-time policy = typed machine-readable authority
human-readable explanation = separate descriptive field
```

## 2. Authority and versioning decision

The authority order remains:

```text
Frozen Design
> Pydantic schema
> validator/runtime implementation
> implementation convenience
```

The existing v0.2 documents are historical frozen baselines. They are not silently rewritten.

The successor is:

```text
Benchmark Definition schema v0.3
Executable Evaluation Policy hardening
```

The closure profile also changes:

```text
skill-eval-frozen-definition-closure-v1
```

Reason: v0.3 changes the typed shape and canonical meaning of Definition policy fields. Keeping `skill-eval-frozen-definition-closure-v0` would allow one profile identifier to denote two different canonical object shapes and therefore two different byte protocols. A new profile is the smallest safe identity boundary; it is not algorithm negotiation or fallback.

Existing v0.2 Definitions, v0 closure digests, and v0 conformance vectors remain valid historical evidence. They are not silently migrated by the evaluator. A later explicit migration tool may construct a v0.3 Definition and therefore a new v1 digest, but migration is outside this design and is not an automatic compatibility path.

## 3. Executability audit

### 3.1 Descriptive-only fields retained as text

These fields do not directly select, group, reduce, weight, or aggregate values and remain human-readable:

- `MetricSpecification.name`
- `MetricCompletenessPolicy.transparency_requirements`
- `MetricResultSemantics.interpretation`
- `MetricResultSemantics.direction` (validated against executable scale where required, but retained as explanatory meaning)
- `MetricResultSemantics.scale` (validated compatibility label, not an executor operator)
- `MetricResultSemantics.denominator_meaning`
- `GateSpecification.name`
- `GateSpecification.scope`
- `GateResultSemantics.open_meaning`
- `GateResultSemantics.triggered_meaning`
- `GateResultSemantics.indeterminate_meaning`
- `GateResultSemantics.blocking_effect`
- `GateSpecification.explanation_requirements`
- design rationale, purpose rationale, and semantic review prose

Descriptive fields may explain an executable policy, but a calculator must never infer policy from them.

### 3.2 Executable authority fields

The following become typed structures or enums:

- result selection
- eligibility handling
- numeric contribution mapping
- aggregation unit
- unit reduction
- final aggregation
- weighting
- completeness and empty-denominator behavior
- direct-Grader Gate result selection
- direct-Grader Gate trigger semantics

### 3.3 Mixed fields split into authority and explanation

The current `contribution_semantics` string is mixed. It currently tries to describe both the meaning of a contribution and the numeric value used by a calculator. In v0.3 it is split into:

```text
ContributionRule:
- source_semantic: ResultSemantic
- numeric_value: finite Decimal
- contribution_unit: ContributionUnit
- explanation: NonEmptyStr
```

`explanation` remains descriptive. `numeric_value` is the only numeric authority. A Grader judgment never inherently means a number; the Metric-local rule supplies that mapping.

The current eligibility handling strings are also mixed. Their machine behavior becomes typed variants, while any human rationale remains a separate explanation/rationale field.

## 4. Shared result-selection authority

Metric and direct-Grader Gate use one shared Definition-time policy type:

```text
AttemptSelectionPolicy:
- mode: all_distinct | sole_distinct | first_distinct | final_distinct_raw
- order: attempt_index_ascending (required for first/final)
```

`attempt_index` is the only ordering authority. Timestamp, arrival order, Result ID, filesystem order, and list construction order are not ordering authorities.

Semantics:

| mode | behavior |
|---|---|
| `all_distinct` | select every distinct logical attempt-level Result after logical-duplicate validation |
| `sole_distinct` | require exactly one distinct Result; zero is unavailable and multiplicity is a policy execution failure |
| `first_distinct` | select the first distinct Result by ascending `Episode.attempt_index` |
| `final_distinct_raw` | select the final distinct Result by ascending `Episode.attempt_index`; do not fallback when that Result is non-substantive or unavailable |

The selector does not include `final_eligible`. Final eligible is a post-eligibility unit-reduction mode and is therefore intentionally distinct from final raw selection.

Selection is always applied after logical identity integrity and before eligibility:

```text
associate same-Run Results
→ validate logical uniqueness
→ apply AttemptSelectionPolicy
→ apply eligibility
```

The shared type prevents Metric and direct-Grader Gate from developing two subtly different selector authorities.

## 5. Result semantic vocabulary

The Definition policy vocabulary uses exactly these lowercase tokens:

```text
satisfied
violated
insufficient_evidence
not_exercised
```

They are the Definition-facing semantic vocabulary and map one-to-one to the existing Runtime `GraderJudgment` values. A future implementation may place the shared vocabulary in a common schema module, but Definition policy must not depend on a Runtime Result object or on a Runtime ID.

The boundaries remain fixed:

- `insufficient_evidence` is not `violated`;
- `not_exercised` is not `violated`;
- missing Grader Result is not `insufficient_evidence`;
- engine failure produces no semantic Grader Result;
- eligibility never rewrites the original Grader judgment.

## 6. Metric executable policy

The v0.3 Metric policy is a closed, minimal structure:

```text
MetricExecutionPolicy:
- selection: AttemptSelectionPolicy
- eligibility: EligibilityPolicy
- contribution_mapping: list[ContributionRule]
- aggregation_unit: per_target | per_contract | per_test_case
- unit_reduction: UnitReductionPolicy
- weighting: equal_per_unit
- aggregation: mean
- completeness: CompletenessPolicy
```

The existing descriptive `MetricSpecification` fields remain available only as explanation or are replaced by these typed fields in the v0.3 schema. There is no `custom: str` escape hatch and no arbitrary expression field.

### 6.1 EligibilityPolicy

```text
EligibilityPolicy:
- eligible_semantics: non-empty set[ResultSemantic]
- non_substantive: exclude_and_trace
- missing_input: unavailable
```

`eligible_semantics` is explicit. A normal binary compliance Metric uses `{satisfied, violated}`. `insufficient_evidence` and `not_exercised` are excluded and separately counted in the Result trace. Missing inputs remain unavailable and are never converted to a semantic judgment.

`exclude_and_trace` does not mean that a Metric is always available. Completeness still decides whether the remaining eligible population retains the declared Metric meaning.

### 6.2 ContributionRule

```text
ContributionRule:
- source_semantic: ResultSemantic
- numeric_value: finite Decimal
- contribution_unit: unit_interval
- explanation: NonEmptyStr
```

For a binary compliance Metric:

```text
satisfied → 1, unit_interval
violated  → 0, unit_interval
```

The numeric values are explicit Definition authority. No calculator may derive them from `full contribution`, `zero contribution`, `pass`, `fail`, or another phrase. Every eligible semantic must have exactly one mapping, and mappings for non-eligible semantics are rejected.

v0.3 formally supports `unit_interval` contributions. Count and arbitrary scalar contribution units are deferred and are not represented as executable v0.3 values until a separate method validation freezes their scale and aggregation semantics.

### 6.3 Aggregation units

The v0.3 enum is deliberately small:

```text
per_target
per_contract
per_test_case
```

Derivation is fixed:

- `per_target`: `(test_case_id, contract_id)`;
- `per_contract`: `contract_id`;
- `per_test_case`: `test_case_id`.

Every input belongs to exactly one unit. No `custom` label, name selector, tag selector, or Runtime-discovered group is allowed.

### 6.4 UnitReductionPolicy

The minimum supported set is:

```text
UnitReductionPolicy:
- mode: single | mean | final_eligible
```

Semantics:

- `single`: exactly one eligible contribution per unit is required; multiplicity is not silently collapsed;
- `mean`: arithmetic mean of all eligible contributions in the unit;
- `final_eligible`: preserve attempt order from `all_distinct`, then choose the final eligible contribution after eligibility and mapping. It is invalid with `first_distinct`, `final_distinct_raw`, or another selector that already reduces to one raw Result.

`final_eligible` is the only v0.3 post-eligibility attempt-sensitive reducer. `worst`, `best`, ordinal distance, median, percentile, and arbitrary reducers are deferred.

An empty unit has no contribution. Under the v0.3 strict completeness policy it makes the Metric unavailable; it is not a synthetic zero.

### 6.5 Final aggregation

v0.3 supports one final rule:

```text
mean
```

It computes the arithmetic mean of included unit contributions after unit reduction. This is sufficient for the validated binary per-target and per-contract method scenarios. `rate`, `count`, `sum`, `min`, `max`, weighted mean, formulas, and statistical estimators are deferred until real validation demonstrates a need and supplies exact semantics.

### 6.6 Weighting

v0.3 supports one weighting policy:

```text
equal_per_unit
```

Each contributing aggregation unit has equal weight. Case count, Contract criticality, Gate importance, failure severity, display order, and Metric-internal weights never become implicit weights.

Unequal weights are deferred. They require a structured unit-weight mapping, normalization rule, omitted-unit behavior, and new semantic validation; retaining `weighting_policy: str` would recreate the blocker.

### 6.7 Completeness and empty denominator

The v0.3 supported policy is:

```text
CompletenessPolicy:
- mode: strict
- empty_denominator: unavailable
```

Strict means every expected aggregation unit must have an eligible contribution after selection, eligibility, and reduction. Any missing required input, empty unit, or zero eligible denominator produces a normal `MetricResult(status=unavailable)` with a typed reason and complete trace.

Partial-threshold completeness and eligible-only descriptive Metrics are deferred from the executable v0.3 vocabulary. The historical Guide discusses them, but the current repository has not frozen a single threshold operator, coverage denominator, or interpretation that two implementations could apply identically.

Count-zero semantics are also deferred. A count Metric may be added only with an explicit complete-population authority; zero must never be a division-by-zero fallback for rate or mean.

## 7. Direct-Grader Gate design

`GraderResultGateCondition` uses the same `AttemptSelectionPolicy` as Metric. Its executable shape becomes:

```text
DirectGraderGatePolicy:
- selection: AttemptSelectionPolicy
- trigger_result_semantics: non-empty set[ResultSemantic]
- quantifier: any | all
```

The fixed processing order is:

```text
resolve explicit target pairs
→ associate same-Run Results
→ validate logical uniqueness
→ shared attempt selection
→ classify MATCH / NON_MATCH / UNKNOWN
→ apply one Gate-level quantifier
→ apply unavailable_handling only to UNKNOWN
```

Classification is fixed:

- selected semantic in `trigger_result_semantics` → `MATCH`;
- known selected semantic not in the trigger set → `NON_MATCH`;
- missing required selected Result or unavailable selection identity/order → `UNKNOWN`;
- `insufficient_evidence` and `not_exercised` are known `NON_MATCH` unless explicitly included in the trigger set.

The existing `any | all` quantifier and three-valued truth table remain unchanged. No nested boolean DSL, count Gate, ratio Gate, per-target hidden quantifier, or cross-target second quantifier is added.

Metric threshold and Metric availability Gate variants are not semantically changed by this hardening.

## 8. Digest impact

The v0.3 executable policy is part of the complete Frozen Definition closure. The following enter the new closure:

- structured selection policy;
- typed eligibility policy;
- typed numeric contribution mappings;
- aggregation unit;
- unit reduction;
- weighting policy;
- final aggregation;
- completeness and empty-denominator policy;
- structured direct-Grader Gate selection and trigger semantics.

The following remain excluded:

- Runtime IDs and timestamps;
- actual Results, Evidence, Episodes, and Scorecards;
- implementation traces and diagnostics;
- source formatting, comments, and rationale prose;
- `definition_snapshot_ref` and `definition_digest` itself.

Collection classification:

- identified Metric policy collections remain set-like by their IDs;
- `eligible_semantics`, `trigger_result_semantics`, and contribution rules are set-like by their stable semantic/source identity;
- `interaction_steps`, Rubric dimensions, Rubric anchors, and attempt-ordered runtime observations remain ordered;
- the selector mode and policy object keys use the new v1 canonical profile rules.

The closure profile must therefore be `skill-eval-frozen-definition-closure-v1`. v0 vectors are historical and must not be recalculated under v1 semantics. New v1 conformance vectors are required before implementation freeze.

## 9. Validator migration impact

Later implementation work must update three validation layers.

### Structural / Pydantic

- replace executable free-text fields with discriminated typed policies;
- validate enum membership and finite Decimal contribution values;
- reject duplicate semantic mappings and duplicate set-like members;
- enforce `final_eligible` requires `all_distinct`;
- enforce strict completeness and empty-denominator shape;
- reject unknown policy fields and arbitrary expression escape hatches.

### Cross-object Definition validation

- resolve typed Metric inputs to one authoritative Grader target;
- verify every eligible semantic has exactly one contribution mapping;
- verify source semantics belong to the known Result vocabulary;
- verify aggregation-unit derivation is possible for every input;
- verify referenced Metric and Gate IDs;
- verify direct-Grader Gate targets resolve and do not duplicate authority;
- verify normalization, contribution unit, and Result semantics are compatible.

### Runtime / Result validation

- preserve same-Run and logical Result identity;
- supply Episode attempt ordering explicitly;
- distinguish missing Result from insufficient evidence and unavailable Metric;
- reject duplicate logical Result records instead of silently deduplicating;
- verify Metric and Gate traces match the typed policy path;
- keep engine failure outside semantic Result objects.

## 10. Evaluation service migration impact

Later Evaluation Services may implement only the typed v0.3 vocabulary:

1. Metric service consumes the structured policy and produces complete `MetricCoverageSummary` and `MetricInputTrace` values.
2. Direct-Grader Gate consumes the shared selector, then applies the existing three-valued quantifier.
3. Metric threshold Gate consumes only canonical Decimal Metric values.
4. Overall continues using explicit cross-Metric weights and normalization from the existing structured policy.
5. Acceptance continues consuming only explicit participating Gate Results and its existing fail-closed handling.

No service may accept a legacy free-form executable string as an implicit compatibility mode. A v0.2 Definition must either remain a historical artifact or be explicitly migrated to v0.3 before evaluation.

## 10.1 v0.2 to v0.3 field migration map

The successor does not reinterpret old values in place. The conceptual mapping is:

| v0.2 field | v0.3 authority | treatment |
|---|---|---|
| `result_selection_policy: str` | `execution_policy.selection` | replace with shared `AttemptSelectionPolicy` |
| `eligibility_policy.eligible_result_semantics` | `execution_policy.eligibility.eligible_semantics` | replace with typed semantic set |
| `eligibility_policy.non_substantive_handling` | `execution_policy.eligibility.non_substantive` | replace with typed variant |
| `eligibility_policy.unavailable_input_handling` | `execution_policy.eligibility.missing_input` | replace with typed variant |
| `contribution_mapping[].source_semantics` | `ContributionRule.source_semantic` | replace with typed semantic |
| `contribution_mapping[].contribution_semantics` | `ContributionRule.numeric_value` + `contribution_unit` + `explanation` | split mixed authority |
| `aggregation_unit: str` | `execution_policy.aggregation_unit` | replace with closed enum |
| `unit_reduction: str` | `execution_policy.unit_reduction` | replace with closed reducer |
| `aggregation_rule: str` | `execution_policy.aggregation` | replace with `mean` |
| `weighting_policy: str` | `execution_policy.weighting` | replace with `equal_per_unit` |
| completeness string fields | `execution_policy.completeness` | replace with strict typed policy |
| `GraderResultGateCondition.result_selection_policy: str` | `DirectGraderGatePolicy.selection` | reuse shared selector |
| `trigger_result_semantics: list[str]` | `DirectGraderGatePolicy.trigger_result_semantics` | typed ResultSemantic set |

`name`, `scope`, interpretation prose, transparency, explanation requirements, and rationale fields are retained as descriptive fields. A v0.2 value that cannot be mapped explicitly is a migration error, not a reason to preserve a free-text executor fallback.

## 11. Controlled method regressions

The following examples are design conformance targets, not implementation output.

### A. All distinct, binary, eligible mean

```text
selection: all_distinct
eligible: satisfied, violated
mapping: satisfied=1, violated=0
unit: per_target
reduction: mean
weighting: equal_per_unit
aggregation: mean
completeness: strict
```

Two eligible contributions `1` and `0` produce canonical Metric value `0.5`.

### B. Final raw, no fallback

```text
selection: final_distinct_raw
```

If the final attempt is `insufficient_evidence`, it is selected, excluded by eligibility, and the strict Metric becomes unavailable. An earlier `satisfied` Result is not revisited.

### C. Final eligible

```text
selection: all_distinct
reduction: final_eligible
```

The evaluator considers all attempts, applies eligibility and contribution mapping, then selects the final eligible contribution using preserved `attempt_index` order. This is not equivalent to final raw.

### D. Per-target aggregation

Each `(test_case_id, contract_id)` receives one unit contribution. Multiple target units are averaged equally.

### E. Per-contract aggregation

Inputs sharing `contract_id` reduce into one Contract unit first; Contract units are then averaged equally. Case multiplicity does not silently become Contract weight.

### F. Strict completeness

If one expected unit has no eligible contribution, the Metric is unavailable with a completeness reason and explicit trace; no zero is inserted.

### G. Partial / eligible-only boundary

These remain deferred in v0.3 because the current authority has not frozen one threshold operator or one coverage interpretation. The design does not leave them as free text.

### H. Direct-Grader Gate

The shared selector supports all, sole, first, and final raw selection. The existing ANY/ALL and MATCH/NON_MATCH/UNKNOWN rules apply without a second quantifier.

### I. Metric threshold Gate

Canonical Metric value `0.8995` compared with `lt 0.90` is `TRUE` and therefore `TRIGGERED`, regardless of a display value such as `0.90`.

### J. Overall and Acceptance

Overall remains independent of Acceptance. A triggered participating Gate blocks Acceptance even when Overall is high; all participating Gates OPEN may produce `ACCEPTABLE` without consuming Overall.

## 12. Three-layer design validation

### Structural validation

- no executable free-text policy fields remain;
- all executable policies have closed discriminated vocabularies;
- no duplicate authority or arbitrary expression escape hatch exists;
- Decimal mappings are finite and exact;
- ordered versus set-like collections are explicit.

### Cross-object validation

- Metric input pairs resolve to authoritative Grader coverage;
- policy references resolve to current Definition IDs;
- contribution source semantics are known and complete;
- aggregation units derive from explicit input identity;
- direct-Grader Gate targets resolve without `grader_id` double authority;
- v0.3 policy references cannot silently point to v0.2 closure content.

### Semantic validation

- selection precedes eligibility;
- final raw cannot fallback;
- final eligible is post-eligibility reduction;
- missing, unavailable, insufficient, and not-exercised remain distinct;
- no implicit zero or vacuous truth is introduced;
- two conforming implementations use the same selector, units, reducer, weights, and final mean;
- Gate, Overall, and Acceptance boundaries remain independent.

## 13. Deferred advanced policies

Explicitly deferred:

- arbitrary formula or expression DSL;
- custom aggregation groups;
- unequal or derived weights;
- worst/best/median/percentile reducers;
- ordinal distance arithmetic;
- heterogeneous scalar normalization;
- statistical estimators and confidence intervals;
- partial threshold completeness;
- eligible-only descriptive completeness;
- count-zero semantics without a complete population contract;
- nested boolean or count Gates;
- automatic v0.2-to-v0.3 migration.

Deferred behavior is not represented by an executable free-form string. It is absent from the supported v0.3 vocabulary until separately validated and versioned.

## 14. New findings

No new generic blocker was found after replacing the two free-text authorities with the closed design above.

The original findings are closed by this design:

- `IMP-EVAL-METRIC-POLICY-001`: closed by typed selection, eligibility, contribution, unit, reduction, weighting, aggregation, and completeness policies;
- `IMP-EVAL-GATE-GRADER-SELECTION-001`: closed by the shared `AttemptSelectionPolicy`.

This closure is design-level only. It does not claim that the later Pydantic, validator, digest, and Evaluation Service migrations are already implemented.

## 15. Freeze decision

```text
EXECUTABLE_EVALUATION_POLICY_DESIGN_V0_FREEZE_READY: YES
```

The successor schema and closure profile must be treated as one coordinated migration. Implementation may begin only after preserving the v0.2 historical baseline and adding v1 digest conformance vectors.

## 16. Architecture question answers

1. **Which current string fields remain descriptive?** Names, scopes, result interpretations, denominator explanations, transparency requirements, explanation requirements, and rationale prose remain text. Executors never parse them.
2. **Which become executable structured fields?** Selection, eligibility, contribution mapping, aggregation unit, unit reduction, final aggregation, weighting, completeness, empty-denominator behavior, and direct-Grader Gate trigger/selection policy.
3. **What is the exact selection vocabulary?** `all_distinct`, `sole_distinct`, `first_distinct`, and `final_distinct_raw`, with `attempt_index_ascending` ordering where required.
4. **Is selection shared?** Yes. Metric and direct-Grader Gate use the same `AttemptSelectionPolicy`.
5. **How is final raw distinct from final eligible?** Final raw is a selector before eligibility; final eligible is `all_distinct` followed by eligibility/mapping and a `final_eligible` unit reduction.
6. **What are the v0 aggregation units?** `per_target`, `per_contract`, and `per_test_case`.
7. **What unit reductions are supported?** `single`, `mean`, and `final_eligible`; worst/best/ordinal/statistical reducers are deferred.
8. **What final aggregation rules are supported?** `mean` only.
9. **What weighting policies are supported?** `equal_per_unit` only.
10. **How is numeric contribution represented?** A typed finite Decimal `numeric_value` paired with a typed source semantic; no prose-to-number conversion.
11. **How are insufficient, not-exercised, and missing handled?** Eligible semantics are explicit; non-substantive Results are excluded and traced; missing Results are unavailable; none is rewritten as violated.
12. **What completeness policies are executable?** `strict` plus `empty_denominator: unavailable`; partial-threshold and eligible-only modes are deferred.
13. **Which advanced cases are deferred?** Custom groups, arbitrary formulas, unequal weights, count/scalar/ordinal arithmetic, statistical estimators, nested boolean/count Gates, and automatic migration.
14. **Does the Definition schema version change?** Yes: successor `v0.3`; historical v0.2 remains unchanged.
15. **Does the closure profile change?** Yes: `skill-eval-frozen-definition-closure-v1`, because typed policy shape and canonical meaning change.
16. **What code modules must migrate?** Pydantic schemas, local and cross-object validators, Runtime identity/ordering checks, Digest canonicalizer and vectors, and Evaluation Services; no implementation is part of this document.
