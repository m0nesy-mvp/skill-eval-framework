"""Canonical serialization primitives for the Frozen Definition closure."""

from __future__ import annotations

import json
from collections.abc import Sequence
from decimal import Decimal
from enum import Enum
from typing import Any, cast
from unicodedata import normalize

from pydantic import BaseModel

from skill_eval_framework.schemas.definition import BenchmarkDefinition

from .errors import CanonicalizationError, UnsupportedClosureProfileError

CLOSURE_PROFILE = "skill-eval-frozen-definition-closure-v0"


def normalize_canonical_string(value: str) -> str:
    """Apply the profile's NFC and line-ending normalization to a string."""

    return normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))


def canonical_decimal(value: Decimal) -> str:
    """Return the profile's exact, non-exponent decimal token."""

    if not value.is_finite():
        raise CanonicalizationError("canonical decimals must be finite")
    if value.is_zero():
        return "0"
    text = format(value, "f")
    sign = ""
    if text.startswith("-"):
        sign, text = "-", text[1:]
    integer, separator, fraction = text.partition(".")
    integer = integer.lstrip("0") or "0"
    if separator:
        fraction = fraction.rstrip("0")
    return f"{sign}{integer}{'.' + fraction if fraction else ''}"


_IDENTIFIED_COLLECTIONS: dict[str, str] = {
    "requirements": "requirement_id",
    "contracts": "contract_id",
    "test_cases": "test_case_id",
    "evidence_specifications": "evidence_spec_id",
    "grader_specifications": "grader_id",
    "metric_specifications": "metric_id",
    "gate_specifications": "gate_id",
    "semantic_resource_bindings": "resource_ref",
    "metric_contributions": "metric_id",
    "participating_gates": "gate_id",
}

_PAIR_COLLECTIONS = {"targets", "inputs"}
_STRING_COLLECTIONS = {
    "requirement_ids",
    "success_criteria",
    "failure_criteria",
    "failure_modes",
    "preconditions",
    "fixtures",
    "initial_state",
    "observation_requirements",
    "provenance_requirements",
    "context_requirements",
    "qualification_requirements",
    "evidence_spec_ids",
    "judgment_criteria",
    "insufficiency_handling",
    "explanation_requirements",
    "eligible_result_semantics",
    "non_substantive_handling",
    "unavailable_input_handling",
    "transparency_requirements",
    "trigger_result_semantics",
}
_TARGET_COLLECTIONS = {"expected_assertions"}
_MAPPING_COLLECTIONS = {"contribution_mapping"}


def _duplicate_keys(keys: Sequence[Any]) -> bool:
    try:
        return len(keys) != len(set(keys))
    except TypeError as exc:  # pragma: no cover - schema values are scalar/typed models
        raise CanonicalizationError("collection identity is not hashable") from exc


def _sort_collection(keys: Sequence[Any], items: Sequence[Any]) -> list[Any]:
    pairs = zip(keys, items, strict=True)
    return [item for _, item in sorted(pairs, key=lambda pair: cast(Any, pair[0]))]


def _list_key(field_name: str, item: Any) -> Any | None:
    if field_name in _IDENTIFIED_COLLECTIONS:
        id_field = _IDENTIFIED_COLLECTIONS[field_name]
        return normalize_canonical_string(str(getattr(item, id_field)))
    if field_name in _PAIR_COLLECTIONS:
        return (
            normalize_canonical_string(str(item.test_case_id)),
            normalize_canonical_string(str(item.contract_id)),
        )
    if field_name in _TARGET_COLLECTIONS:
        return normalize_canonical_string(str(item.contract_id))
    if field_name in _MAPPING_COLLECTIONS:
        return (
            normalize_canonical_string(str(item.source_semantics)),
            normalize_canonical_string(str(item.contribution_semantics)),
        )
    if field_name in _STRING_COLLECTIONS:
        if not isinstance(item, str):
            raise CanonicalizationError(f"{field_name} must contain strings")
        return normalize_canonical_string(item)
    return None


class _DecimalToken(str):
    """Internal marker preserving Decimal tokens as JSON numbers."""


def _canonical_model(value: BaseModel, path: tuple[str, ...] = ()) -> Any:
    if value.model_extra:
        raise CanonicalizationError("unknown fields cannot enter the Frozen Definition closure")
    output: dict[str, Any] = {}
    for field_name in type(value).model_fields:
        field_value = getattr(value, field_name)
        if field_value is None:
            continue
        if isinstance(field_value, list):
            keys = [_list_key(field_name, item) for item in field_value]
            if any(key is not None for key in keys):
                if any(key is None for key in keys):
                    raise CanonicalizationError(f"mixed canonical collection semantics: {path}")
                if _duplicate_keys(keys):
                    raise CanonicalizationError(
                        f"duplicate values in set-like collection: {path + (field_name,)}"
                    )
                field_value = _sort_collection(keys, field_value)
        output[field_name] = _canonical_nested(field_value, path + (field_name,))
    return output


def _canonical_nested(value: Any, path: tuple[str, ...]) -> Any:
    if isinstance(value, BaseModel):
        return _canonical_model(value, path)
    if isinstance(value, Enum):
        return _canonical_nested(value.value, path)
    if isinstance(value, str):
        return normalize_canonical_string(value)
    if isinstance(value, Decimal):
        return _DecimalToken(canonical_decimal(value))
    if isinstance(value, (bool, int)):
        return value
    if isinstance(value, list):
        keys = [_list_key(path[-1], item) for item in value]
        if any(key is not None for key in keys):
            if any(key is None for key in keys):
                raise CanonicalizationError(f"mixed canonical collection semantics: {path}")
            if _duplicate_keys(keys):
                raise CanonicalizationError(f"duplicate values in set-like collection: {path}")
            value = _sort_collection(keys, value)
        return [_canonical_nested(item, path) for item in value]
    if value is None:
        raise CanonicalizationError("null is not authorized by the v0.2 Definition schema")
    if isinstance(value, (dict, tuple, set)):
        raise CanonicalizationError("arbitrary containers cannot bypass the Pydantic schema")
    raise CanonicalizationError(f"unsupported canonical value type: {type(value).__name__}")


def _encode(value: Any) -> bytes:
    if isinstance(value, dict):
        members = []
        for key in sorted(value, key=normalize_canonical_string):
            members.append(_encode(normalize_canonical_string(key)) + b":" + _encode(value[key]))
        return b"{" + b",".join(members) + b"}"
    if isinstance(value, list):
        return b"[" + b",".join(_encode(item) for item in value) + b"]"
    if isinstance(value, _DecimalToken):
        return value.encode("ascii")
    if isinstance(value, bool):
        return b"true" if value else b"false"
    if isinstance(value, int):
        return str(value).encode("ascii")
    if isinstance(value, str):
        try:
            return json.dumps(
                value, ensure_ascii=False, separators=(",", ":"), allow_nan=False
            ).encode("utf-8")
        except (UnicodeEncodeError, ValueError) as exc:
            raise CanonicalizationError("string is not a valid Unicode scalar sequence") from exc
    raise CanonicalizationError(f"unsupported encoded value type: {type(value).__name__}")


def canonicalize_frozen_definition(
    benchmark: BenchmarkDefinition,
    *,
    closure_profile: str = CLOSURE_PROFILE,
) -> bytes:
    """Build the canonical envelope and return its deterministic UTF-8 bytes."""

    if closure_profile != CLOSURE_PROFILE:
        raise UnsupportedClosureProfileError(f"unsupported closure profile: {closure_profile!r}")
    if not isinstance(benchmark, BenchmarkDefinition):
        raise CanonicalizationError("canonicalization requires a BenchmarkDefinition instance")
    envelope = {
        "closure_profile": closure_profile,
        "benchmark_definition": _canonical_model(benchmark),
    }
    return _encode(envelope)


__all__ = [
    "CLOSURE_PROFILE",
    "canonical_decimal",
    "canonicalize_frozen_definition",
    "normalize_canonical_string",
]
