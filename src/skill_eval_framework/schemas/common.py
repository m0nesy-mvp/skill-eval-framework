"""Shared types and validators for the frozen schema layer."""

from collections.abc import Hashable, Sequence
from decimal import Decimal
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints


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
