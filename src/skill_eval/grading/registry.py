"""Explicit registry for supported grader implementations."""

from skill_eval.domain.ports import Grader


class GraderRegistry:
    def __init__(self, graders: list[Grader]) -> None:
        self._by_kind: dict[str, Grader] = {}
        for grader in graders:
            if grader.kind in self._by_kind:
                raise ValueError(f"duplicate grader kind: {grader.kind}")
            self._by_kind[grader.kind] = grader

    def require(self, kind: str) -> Grader:
        grader = self._by_kind.get(kind)
        if grader is None:
            raise KeyError(f"unsupported grader kind: {kind}")
        return grader

