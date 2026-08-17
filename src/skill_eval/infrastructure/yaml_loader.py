"""Safe YAML loading at the framework boundary."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from skill_eval.domain.models import EvalDefinition


class DefinitionLoadError(ValueError):
    """A definition could not be parsed or validated structurally."""


def load_eval_definition(path: Path) -> EvalDefinition:
    try:
        raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise DefinitionLoadError(f"cannot read Eval Definition: {exc}") from exc

    if not isinstance(raw, dict):
        raise DefinitionLoadError("Eval Definition root must be a mapping")

    try:
        return EvalDefinition.model_validate(raw)
    except ValidationError as exc:
        raise DefinitionLoadError(f"invalid Eval Definition: {exc}") from exc

