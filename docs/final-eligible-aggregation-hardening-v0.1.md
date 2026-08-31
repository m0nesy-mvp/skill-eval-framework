# Final-Eligible Aggregation Hardening v0.1

Status: `AUDIT_002_DESIGN_HARDENING_FREEZE_READY`

Target: Benchmark Definition schema v0.3

Scope: Definition-time legality of `final_eligible` unit reduction when explicit
Metric inputs derive to aggregation units.

This document is a versioned hardening addendum. It does not rewrite the
historical Benchmark Definition v0.2 design or the existing v0.3 executable
policy design. It freezes the smallest missing legality invariant discovered by
the Full Design-to-Code Conformance Audit. It does not implement the invariant.

## 1. Problem

`BenchmarkDefinitionV03` currently accepts a `MetricSpecificationV03` where:

```text
multiple MetricInputs
-> the same derived aggregation unit
-> unit_reduction.mode = final_eligible
```

The deterministic evaluator cannot execute that combination. It preserves
`Episode.attempt_index` order within each MetricInput, but the Frozen Definition
does not define a total order between different MetricInputs that derive to the
same unit.

Different MetricInputs have no Frozen:

- global attempt timeline;
- cross-input attempt ordering;
- test-case ordering authority;
- contract ordering authority; or
- tie-break rule when local attempt indexes are equal.

The current evaluator therefore rejects the combination with a defensive error
instead of producing a Result. The Definition layer must reject the undefined
combination before execution.

## 2. Existing authority

The existing executable v0.3 design freezes the following rules:

1. `Episode.attempt_index` is the only attempt ordering authority. Timestamp,
   arrival order, Result ID, filesystem order, and list construction order are
   not ordering authorities.
2. Attempt selection is performed independently for the distinct Grader Results
   associated with one MetricInput.
3. `final_eligible` is not an attempt selector. It is a post-eligibility
   unit-reduction mode and requires `all_distinct` selection.
4. Aggregation-unit identity is derived only from explicit MetricInput identity:
   - `per_target` -> `(test_case_id, contract_id)`;
   - `per_contract` -> `contract_id`;
   - `per_test_case` -> `test_case_id`.
5. Every MetricInput belongs to exactly one derived aggregation unit.
6. Undefined advanced ordering or grouping behavior must not be supplied by an
   implementation-specific convention.

The Metric Specification Guide also fixes the semantic pipeline:

```text
resolve explicit MetricInput population
-> associate and validate logical Grader Results
-> select attempts for each MetricInput
-> apply eligibility
-> map contributions
-> derive aggregation units
-> apply unit reduction
-> apply weighting and final aggregation
```

It distinguishes final raw selection from final eligible reduction and does not
give MetricInput list order any semantic authority.

## 3. Authority review decision

### 3.1 Compatibility with existing authority

The minimum restriction is compatible with existing authority.

When one derived unit contains exactly one MetricInput, every eligible
contribution in that unit belongs to one attempt sequence. The existing
`Episode.attempt_index` authority is therefore sufficient to identify the final
eligible contribution.

When one derived unit contains multiple MetricInputs, the existing authority
provides multiple local attempt sequences but no rule that merges them into one
total order. Rejecting that combination preserves the rule that an executor must
not invent ordering authority.

### 3.2 Effect on existing legal semantics

The restriction does not change any currently defined, executable semantic
case:

- all `per_target + final_eligible` specifications with unique MetricInput pairs
  remain legal;
- `per_contract + final_eligible` remains legal when each Contract unit has one
  MetricInput;
- `per_test_case + final_eligible` remains legal when each Test Case unit has one
  MetricInput;
- `single` and `mean` retain their existing semantics;
- attempt selection, eligibility, contribution mapping, weighting,
  completeness, and final aggregation are unchanged.

The restriction closes only the combination for which no cross-input ordering
semantics were frozen and for which the current evaluator cannot produce an
authoritative Result.

### 3.3 Versioning decision

This decision is a versioned v0.3 hardening addendum. It does not require a
Benchmark Definition schema v0.4.

Reasons:

- no field is added, removed, renamed, or retyped;
- no executable enum value changes meaning;
- no previously defined executable behavior changes;
- no canonical Definition field or collection classification changes;
- no digest byte protocol changes;
- `skill-eval-frozen-definition-closure-v1` remains the correct closure profile;
- the addendum rejects an undefined and currently unexecutable policy
  combination instead of introducing new semantics.

A future design that adds cross-MetricInput ordering would be a semantic
expansion and would require a separate versioning review. This hardening does
not authorize that expansion.

## 4. Frozen decision

For every `MetricSpecificationV03` where:

```text
execution_policy.unit_reduction.mode == final_eligible
```

derive one logical aggregation-unit key for every explicit MetricInput using
`execution_policy.aggregation_unit`.

Each resulting aggregation-unit key MUST occur exactly once across
`MetricSpecificationV03.inputs`.

If any derived aggregation-unit key occurs more than once, the Benchmark
Definition is invalid.

This rule is additional to the existing invariant:

```text
final_eligible requires selection.mode == all_distinct
```

Both invariants must hold.

## 5. Machine-implementable legality invariant

Let:

```text
I = MetricSpecificationV03.inputs
U = MetricSpecificationV03.execution_policy.aggregation_unit
R = MetricSpecificationV03.execution_policy.unit_reduction.mode
```

For each input `i` in `I`, derive `unit_key(U, i)` as:

```text
unit_key(per_target, i)    = (i.test_case_id, i.contract_id)
unit_key(per_contract, i)  = i.contract_id
unit_key(per_test_case, i) = i.test_case_id
```

The legality rule is:

```text
if R == final_eligible:
    for every distinct key K derived from I:
        count(i in I where unit_key(U, i) == K) MUST equal 1
```

Equivalent executable predicate:

```text
R != final_eligible
OR
len([unit_key(U, i) for i in I])
    == len(set(unit_key(U, i) for i in I))
```

The rule depends only on:

- `MetricSpecificationV03.inputs`;
- `execution_policy.aggregation_unit`; and
- `execution_policy.unit_reduction.mode`.

It does not depend on Benchmark-wide references, Runtime Episodes, actual
GraderResults, timestamps, Result IDs, input list order, or implementation
state.

## 6. Ordering rationale

`final_eligible` is meaningful only when all eligible contributions in one unit
share one Frozen attempt sequence.

With exactly one MetricInput per unit:

```text
one MetricInput
-> one local distinct-attempt sequence
-> Episode.attempt_index ascending
-> final eligible contribution
```

With multiple MetricInputs per unit:

```text
MetricInput A -> local attempt sequence A
MetricInput B -> local attempt sequence B
```

No Frozen authority answers whether an attempt from A precedes, follows, or ties
an attempt from B. MetricInput list order, Test Case ID, Contract ID, Result ID,
timestamp, and arrival order MUST NOT fill that gap.

The minimum safe v0.3 behavior is therefore rejection at Definition validation,
not an invented merge order.

## 7. Valid examples

### A. Per-target, one explicit input

```text
inputs:
- TC1/C1

aggregation_unit: per_target
unit_reduction: final_eligible
```

Derived units:

```text
(TC1, C1) -> one MetricInput
```

Result: `VALID`

### B. Per-contract, distinct Contract units

```text
inputs:
- TC1/C1
- TC2/C2

aggregation_unit: per_contract
unit_reduction: final_eligible
```

Provided `C1 != C2`, derived units are:

```text
C1 -> one MetricInput
C2 -> one MetricInput
```

Result: `VALID`

### C. Per-contract, same Test Case but distinct Contract units

```text
inputs:
- TC1/C1
- TC1/C2

aggregation_unit: per_contract
unit_reduction: final_eligible
```

Provided `C1 != C2`, derived units are:

```text
C1 -> one MetricInput
C2 -> one MetricInput
```

Result: `VALID`

The shared Test Case does not merge Contract aggregation units.

### Additional valid boundary: per-test-case with distinct Test Cases

```text
inputs:
- TC1/C1
- TC2/C1

aggregation_unit: per_test_case
unit_reduction: final_eligible
```

Provided `TC1 != TC2`, each Test Case unit has one MetricInput.

Result: `VALID`

## 8. Invalid examples

### D. Per-contract, multiple inputs in one Contract unit

```text
inputs:
- TC1/C1
- TC2/C1

aggregation_unit: per_contract
unit_reduction: final_eligible
```

Derived unit:

```text
C1 -> two MetricInputs
```

Result: `INVALID`

The two MetricInputs have separate local attempt sequences. No cross-input total
order is Frozen.

### E. Per-test-case, multiple inputs in one Test Case unit

```text
inputs:
- TC1/C1
- TC1/C2

aggregation_unit: per_test_case
unit_reduction: final_eligible
```

Derived unit:

```text
TC1 -> two MetricInputs
```

Result: `INVALID`

Contract ID does not provide an ordering rule inside a Test Case unit.

## 9. Other reducers

This restriction applies only when:

```text
unit_reduction.mode == final_eligible
```

It does not change `single` or `mean`:

- `single` retains its existing rule that exactly one eligible contribution is
  required for a unit;
- `mean` retains its existing rule that all eligible contributions in a unit
  are averaged arithmetically.

Multi-input same-unit Definitions using `single` or `mean` remain governed by
their existing semantics and validation boundaries. This addendum neither
widens nor narrows those reducers.

## 10. Ownership

The authoritative legality check belongs to
`MetricSpecificationV03` local/cross-field validation.

Rationale:

- all required data is contained in one MetricSpecification;
- the invariant does not require Benchmark-wide object resolution;
- invalidity can be detected before digest consumption or execution planning;
- keeping one Definition-time legality truth prevents Schema, cross-object
  validator, evaluator, and CLI from diverging.

The check does not belong primarily to:

- the Benchmark-wide cross-object Definition validator;
- Runtime validation;
- the Metric evaluator;
- CLI or orchestration; or
- a new execution stage.

The cross-object Definition validator may retain a defensive assertion only if
it reuses the same legality helper or otherwise cannot diverge. It MUST NOT
maintain a second independent interpretation of the rule.

## 11. Schema implication

A later implementation migration must extend
`MetricSpecificationV03` local/cross-field validation to:

1. inspect `execution_policy.unit_reduction.mode`;
2. when it is `final_eligible`, derive one aggregation-unit key per explicit
   input using `execution_policy.aggregation_unit`;
3. reject the specification if any key is repeated;
4. preserve the existing `final_eligible requires all_distinct` invariant; and
5. leave `single` and `mean` behavior unchanged.

Definition invalidity must be reported before Evaluation Services execute.

This document does not select an implementation helper name, error-code name, or
Pydantic error-message wording. Those are implementation details provided they
preserve the single invariant above.

## 12. Evaluator implication

The current evaluator error:

```text
final_eligible cannot merge multiple MetricInputs into one aggregation unit
```

may remain as a defensive integrity check.

After the Schema migration, that branch MUST NOT be the normal control path for
a normally validated `MetricSpecificationV03`. The evaluator must not add a
cross-input ordering fallback.

No evaluator change is authorized by this design-only task.

## 13. Regression requirements

The later implementation migration must add tests proving:

1. Example A is valid.
2. Example B is valid when Contract IDs differ.
3. Example C is valid when Contract IDs differ.
4. Example D is rejected at Definition validation.
5. Example E is rejected at Definition validation.
6. `per_test_case + final_eligible` is valid when all Test Case unit keys are
   distinct.
7. `per_target + final_eligible` remains valid for multiple unique target pairs.
8. `final_eligible` still requires `all_distinct` selection.
9. `single` multi-input same-unit behavior is unchanged.
10. `mean` multi-input same-unit behavior is unchanged.
11. A normally validated Definition cannot reach the evaluator's defensive
    multi-input `final_eligible` error.
12. Digest v1 canonicalization and closure-profile selection remain unchanged.

Tests must exercise the legality cross-product across all three aggregation-unit
modes instead of covering only a single-input fixture.

## 14. Non-goals

This hardening does not introduce or authorize:

- cross-MetricInput total ordering;
- Test Case ordering;
- Contract ordering;
- a tie-break rule;
- a global attempt timeline;
- ordering by timestamp, Result ID, input list order, or arrival order;
- a new Core Object;
- a new execution stage;
- a new reducer;
- changes to `single` or `mean`;
- changes to weighting, completeness, or final aggregation;
- implementation changes; or
- CLI, Packaging, or public API work.

## 15. Finding status

With this addendum Frozen:

```text
AUDIT-002: DESIGN_HARDENING_FREEZE_READY

AUDIT-002:
  SEVERITY: P1
  DESIGN_HARDENING_REQUIRED: YES
  DESIGN_STATUS: DESIGN_HARDENING_FREEZE_READY
  IMPLEMENTATION_STATUS: OPEN
  BLOCKING_BEFORE_CLI: YES
```

`AUDIT-002` is not fixed or fully closed by this document. The CLI blocker may
be removed only after the single Definition-time legality invariant and its
regressions are implemented and independently verified.

Historical finding status:

```text
IMP-EVAL-METRIC-POLICY-001:
  DESIGN_LAYER: CLOSED_STILL_VALID
  IMPLEMENTATION_LAYER: OPEN_PENDING_SCHEMA_VALIDATION_AND_TESTS
```

The original typed-policy design remains valid after the undefined combination
is closed by this addendum. Full implementation closure still requires the
Schema/validator migration and regression evidence.

## 16. Freeze decision

```text
AUDIT_002_DESIGN_HARDENING_FREEZE_READY: YES
```

The minimum restriction is compatible with existing authority, preserves all
currently defined legal semantics, rejects only an undefined executable
combination, requires no v0.4 schema or new digest profile, and assigns one
machine-implementable legality truth to `MetricSpecificationV03` local/cross-
field validation.
