# CLI reference

## Install for repository development

```powershell
uv sync --frozen --extra dev
```

This installs `skill-eval` in `.venv\Scripts`. Activate the environment or use
the executable path directly.

## Commands

```powershell
skill-eval validate assets\examples\minimal\definition.json
skill-eval digest assets\examples\minimal\definition.json
skill-eval evaluate `
  --definition assets\examples\minimal\definition.json `
  --run-input assets\examples\minimal\run-input.json `
  --output example-evaluation.json
```

`validate` accepts a v0.3 Definition and performs schema plus cross-object
validation. `digest` emits its closure-v1 SHA-256 identity. `evaluate` verifies
the binding, validates the Runtime graph, derives all downstream results, and
writes a complete JSON bundle.

For the public example, successful evaluation yields a valid completed Run, an
available Metric value of `1`, an `OPEN` Gate, Overall `1.00`, `ACCEPTABLE`
Acceptance, and a `finalized_evaluation` Scorecard.

## Input/output contract

- Input root: `skill-eval-evaluation-input/v0.1`.
- Output root: `skill-eval-evaluation-output/v0.1`.
- Input accepts upstream Runtime products and GraderResults only.
- Result IDs and timestamps are caller-supplied for deterministic output.
- Repeating evaluation with identical files produces byte-identical JSON.
- Success writes a compact summary to stdout and the full bundle to `--output`.
- Failure writes structured JSON to stderr and returns a nonzero exit code.

Error categories include I/O, input schema, Definition schema/validation,
Definition identity, Runtime graph, evaluation, and finalization errors.

The longer contract reference remains at `docs/cli-usage-v0.1.md`.
