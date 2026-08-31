"""Shared types and validators for the frozen schema layer."""

from collections.abc import Hashable, Mapping, Sequence
from copy import deepcopy
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Any, Never, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)


def _require_non_empty(value: str) -> str:
    if not value.strip():
        raise ValueError("value must be non-empty after trimming whitespace")
    return value


def ensure_unique(values: Sequence[Hashable], field_name: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must not contain duplicate values")


NonEmptyStr = Annotated[str, AfterValidator(_require_non_empty)]
RequirementId = Annotated[str, StringConstraints(pattern=r"^R\d{3,}$")]
ContractId = Annotated[str, StringConstraints(pattern=r"^C\d{3,}$")]
TestCaseId = Annotated[str, StringConstraints(pattern=r"^TC\d{3,}$")]
EvidenceSpecificationId = Annotated[str, StringConstraints(pattern=r"^ES\d{3,}$")]
GraderSpecificationId = Annotated[str, StringConstraints(pattern=r"^G\d{3,}$")]
MetricSpecificationId = Annotated[str, StringConstraints(pattern=r"^M\d{3,}$")]
GateSpecificationId = Annotated[str, StringConstraints(pattern=r"^GATE\d{3,}$")]
BenchmarkId = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Za-z][A-Za-z0-9._-]*$"),
]
Digest = Annotated[
    str,
    StringConstraints(pattern=r"^sha256:[0-9a-f]{64}$"),
]
PositiveInt = Annotated[int, Field(gt=0)]
NonNegativeInt = Annotated[int, Field(ge=0)]
FiniteDecimal = Annotated[Decimal, Field(allow_inf_nan=False)]
FiniteFloat = Annotated[float, Field(allow_inf_nan=False)]
PositiveDecimal = Annotated[Decimal, Field(gt=0, allow_inf_nan=False)]
UnitFraction = Annotated[Decimal, Field(gt=0, le=1, allow_inf_nan=False)]
UnitInterval = Annotated[Decimal, Field(ge=0, le=1, allow_inf_nan=False)]
CanonicalPrecision = Annotated[int, Field(ge=1, le=12)]

# Frozen Runtime design permits only small scalar audit claims and explicitly forbids
# nested arbitrary payloads. The exact scalar vocabulary is not otherwise enumerated.
type JsonScalar = str | int | FiniteFloat | bool


class SchemaModel(BaseModel):
    """Base model for all strict frozen-schema records."""

    model_config = ConfigDict(extra="forbid", validate_default=True)


class FrozenList[T](list[T]):
    """JSON-compatible list that rejects every in-place mutation."""

    def _reject_mutation(self, *args: object, **kwargs: object) -> Never:
        del args, kwargs
        raise TypeError("authoritative Runtime/Result collections are immutable")

    __setitem__ = _reject_mutation
    __delitem__ = _reject_mutation
    __iadd__ = _reject_mutation
    __imul__ = _reject_mutation
    append = _reject_mutation
    clear = _reject_mutation
    extend = _reject_mutation
    insert = _reject_mutation
    pop = _reject_mutation
    remove = _reject_mutation
    reverse = _reject_mutation
    sort = _reject_mutation

    def __deepcopy__(self, memo: dict[int, object]) -> "FrozenList[T]":
        copied = type(self)(deepcopy(list(self), memo))
        memo[id(self)] = copied
        return copied


class FrozenDict[K, V](dict[K, V]):
    """JSON-compatible dict that rejects every in-place mutation."""

    def _reject_mutation(self, *args: object, **kwargs: object) -> Never:
        del args, kwargs
        raise TypeError("authoritative Runtime/Result collections are immutable")

    __setitem__ = _reject_mutation
    __delitem__ = _reject_mutation
    __ior__ = _reject_mutation
    clear = _reject_mutation
    pop = _reject_mutation
    popitem = _reject_mutation
    setdefault = _reject_mutation
    update = _reject_mutation

    def __deepcopy__(self, memo: dict[int, object]) -> "FrozenDict[K, V]":
        copied = type(self)(deepcopy(dict(self), memo))
        memo[id(self)] = copied
        return copied


def _freeze_runtime_value(value: Any) -> Any:
    if isinstance(value, list):
        return FrozenList(_freeze_runtime_value(item) for item in value)
    if isinstance(value, dict):
        return FrozenDict((key, _freeze_runtime_value(item)) for key, item in value.items())
    return value


class RuntimeResultModel(SchemaModel):
    """Detached immutable base for authoritative Runtime/Result snapshots."""

    model_config = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def _freeze_authoritative_collections(self) -> Self:
        for field_name in type(self).model_fields:
            value = object.__getattribute__(self, field_name)
            object.__setattr__(self, field_name, _freeze_runtime_value(value))
        return self

    def model_copy(
        self,
        *,
        update: Mapping[str, Any] | None = None,
        deep: bool = True,
    ) -> Self:
        """Return a detached frozen snapshot even when Pydantic's shallow default is requested."""

        del deep
        frozen_update = (
            {key: _freeze_runtime_value(deepcopy(value)) for key, value in update.items()}
            if update is not None
            else None
        )
        copied = super().model_copy(update=frozen_update, deep=True)
        for field_name in type(copied).model_fields:
            value = object.__getattribute__(copied, field_name)
            object.__setattr__(copied, field_name, _freeze_runtime_value(value))
        return copied


class ResultSemantic(StrEnum):
    """Canonical semantic vocabulary shared by Definition and Runtime schemas."""

    SATISFIED = "satisfied"
    VIOLATED = "violated"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    NOT_EXERCISED = "not_exercised"
