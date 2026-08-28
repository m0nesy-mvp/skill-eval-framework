"""Typed, deterministic outputs shared by cross-object validators."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """One deterministic implementation-layer validation finding."""

    code: str
    message: str
    path: str
    related_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """Immutable, deterministically ordered validation output."""

    issues: tuple[ValidationIssue, ...]

    @property
    def is_valid(self) -> bool:
        return not self.issues


class IssueCollector:
    """Collect issues without mutating any validated graph object."""

    def __init__(self) -> None:
        self._issues: list[ValidationIssue] = []

    def add(
        self,
        code: str,
        message: str,
        path: str,
        related_refs: Sequence[str] = (),
    ) -> None:
        self._issues.append(
            ValidationIssue(
                code=code,
                message=message,
                path=path,
                related_refs=tuple(sorted(related_refs)),
            )
        )

    def extend(self, issues: Iterable[ValidationIssue]) -> None:
        self._issues.extend(issues)

    def report(self) -> ValidationReport:
        unique = set(self._issues)
        ordered = tuple(
            sorted(
                unique,
                key=lambda issue: (
                    issue.code,
                    issue.path,
                    issue.message,
                    issue.related_refs,
                ),
            )
        )
        return ValidationReport(issues=ordered)


def group_by[T](items: Sequence[T], key: Callable[[T], str]) -> dict[str, tuple[T, ...]]:
    """Group records by stable ID without choosing among duplicates."""

    groups: dict[str, list[T]] = {}
    for item in items:
        groups.setdefault(key(item), []).append(item)
    return {item_id: tuple(group) for item_id, group in groups.items()}


def unique_items[T](groups: dict[str, tuple[T, ...]]) -> dict[str, T]:
    """Return only unambiguous ID resolutions."""

    return {item_id: group[0] for item_id, group in groups.items() if len(group) == 1}
