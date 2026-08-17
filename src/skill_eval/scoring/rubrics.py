"""Rubric mapping and the framework-level binary default score policy."""

from skill_eval.domain.models import Rubric


def score_binary(passed: bool, rubric: Rubric | None) -> tuple[float, float]:
    if rubric is None:
        score = 1.0 if passed else 0.0
        return score, score

    matching = [level for level in rubric.levels if level.passed is passed]
    if len(matching) != 1:
        raise ValueError(f"rubric {rubric.rubric_id} must have one level for passed={passed}")
    raw_score = matching[0].score
    normalized = (raw_score - rubric.minimum_score) / (
        rubric.maximum_score - rubric.minimum_score
    )
    return raw_score, normalized

