"""Read-only evidence indexing for graders."""

from collections.abc import Iterable

from skill_eval.domain.enums import EvidenceKind
from skill_eval.domain.models import Evidence


class EvidenceStore:
    def __init__(self, evidence: Iterable[Evidence]) -> None:
        self._by_id: dict[str, Evidence] = {}
        for item in evidence:
            if item.evidence_id in self._by_id:
                raise ValueError(f"duplicate evidence id: {item.evidence_id}")
            self._by_id[item.evidence_id] = item

    def view(self) -> "EvidenceView":
        return EvidenceView(dict(self._by_id))


class EvidenceView:
    def __init__(self, evidence_by_id: dict[str, Evidence]) -> None:
        self._by_id = evidence_by_id

    def get(self, evidence_id: str) -> Evidence | None:
        return self._by_id.get(evidence_id)

    def require(self, evidence_id: str) -> Evidence:
        item = self.get(evidence_id)
        if item is None:
            raise KeyError(f"unknown evidence id: {evidence_id}")
        return item

    def by_kind(self, kind: EvidenceKind) -> tuple[Evidence, ...]:
        return tuple(item for item in self._by_id.values() if item.kind is kind)

    def ids(self) -> tuple[str, ...]:
        return tuple(self._by_id)

