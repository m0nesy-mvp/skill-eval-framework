# Skill Eval Framework

## What it does

This project is a platform-neutral MVP for evaluating a target Skill through an explicit chain:

```text
Requirement -> Contract -> Test Case -> Evidence -> Grader -> Gate -> Report
```

MVP 0 uses manually authored YAML, fake execution fixtures, deterministic graders, explicit
acceptance gates, JSON results, and Markdown reports.

## Setup

```powershell
uv sync --dev
```

If the Windows user-level `uv` cache or managed-Python directory is unavailable, keep both
operations project-local and use the installed interpreter explicitly:

```powershell
$env:UV_CACHE_DIR = Join-Path $PWD ".uv-cache"
uv sync --dev --no-managed-python --no-python-downloads --python (Get-Command python).Source
```

## Validation and execution

```powershell
uv run skill-eval validate examples/dummy-skill/eval.yaml
uv run skill-eval run examples/dummy-skill/eval.yaml --output .runs
```

## Development checks

```powershell
uv run pytest
uv run ruff check .
uv run mypy src
```

## Current limitations

- Target Skill requirements, contracts, and cases are authored manually.
- Execution is fixture-backed; no real Skill or platform collector is included.
- Only deterministic graders are supported.
- Baseline-versus-candidate comparison and optimization are not implemented.
- `no_unapproved_side_effect` is a future capability. It is intentionally not an MVP 0 metric;
  using it in an Eval Definition is a validation error.
- No Codex `SKILL.md` is included.
