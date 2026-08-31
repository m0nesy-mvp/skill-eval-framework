# Public API and Definition version policy v0.1

## Status

`AUDIT-006: CLOSED`

The public version boundary is explicit:

| Definition | Role | Closure profile |
|---|---|---|
| `BenchmarkDefinitionV03` | Current executable Definition | `skill-eval-frozen-definition-closure-v1` |
| `BenchmarkDefinitionV02` | Historical compatibility Definition | `skill-eval-frozen-definition-closure-v0` |

The `skill-eval` CLI accepts `BenchmarkDefinitionV03` only.

## Import policy

Use the aggregate schema API for current executable code:

```python
from skill_eval_framework.schemas import BenchmarkDefinition
```

The aggregate unsuffixed Definition, Metric, and Gate names resolve to their
v0.3 executable forms. Versioned modules publish versioned names only:

```python
from skill_eval_framework.schemas.definition_v03 import BenchmarkDefinitionV03
from skill_eval_framework.schemas.definition_v02 import BenchmarkDefinitionV02
```

The legacy `skill_eval_framework.schemas.definition` module remains available
for historical v0.2 compatibility. Its unsuffixed names are historical and
must not be interpreted as the current executable API. No removal schedule is
declared for that compatibility module.

## Version-aware helpers

Generic Definition validation, digest, and Run-binding helpers dispatch on the
concrete Definition root type. Explicit versioned helpers are also available
when a caller wants to pin the protocol:

- `validate_benchmark_definition_v02` / `validate_benchmark_definition_v03`;
- `compute_definition_digest_v02` / `compute_definition_digest_v03`;
- `verify_run_definition_binding_v02` / `verify_run_definition_binding_v03`.

Cross-version Definition/profile pairs are rejected. v0.2 free-text Metric or
Gate policy fields never enter the v0.3 executable path.

## Compatibility boundary

Historical v0.2 parsing and closure-v0 digest behavior remain supported for
explicit compatibility use. New executable definitions and all supported CLI
workflows use v0.3 and closure profile v1.
