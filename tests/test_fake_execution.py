from pathlib import Path

import pytest

from skill_eval.domain.enums import EvidenceKind, ExecutionStatus
from skill_eval.evidence.store import EvidenceStore
from skill_eval.execution.fake import FakeExecutionAdapter, FakeExecutionError
from skill_eval.infrastructure.yaml_loader import load_eval_definition

EXAMPLE_ROOT = Path("examples/dummy-skill")


def test_fake_execution_loads_and_hashes_evidence() -> None:
    definition = load_eval_definition(EXAMPLE_ROOT / "eval.yaml")
    case = definition.test_cases[0]

    envelope = FakeExecutionAdapter().execute(case, EXAMPLE_ROOT)
    view = EvidenceStore(envelope.evidence).view()

    assert envelope.execution.status is ExecutionStatus.COMPLETED
    assert len(view.by_kind(EvidenceKind.FINAL_STATE)) == 1
    assert view.require("evidence-final-state").sha256 is not None


def test_fake_execution_preserves_environment_failure() -> None:
    definition = load_eval_definition(EXAMPLE_ROOT / "eval.yaml")
    case = definition.test_cases[0].model_copy(
        update={"input": {"fixture": "fixtures/blocked.json"}}
    )

    envelope = FakeExecutionAdapter().execute(case, EXAMPLE_ROOT)

    assert envelope.execution.status is ExecutionStatus.BLOCKED
    assert envelope.execution.error is not None
    assert envelope.execution.error.domain.value == "environment"


def test_fake_execution_rejects_path_escape() -> None:
    definition = load_eval_definition(EXAMPLE_ROOT / "eval.yaml")
    case = definition.test_cases[0].model_copy(update={"input": {"fixture": "../eval.yaml"}})

    with pytest.raises(FakeExecutionError, match="escapes fixture root"):
        FakeExecutionAdapter().execute(case, EXAMPLE_ROOT)


def test_evidence_store_rejects_duplicate_ids() -> None:
    definition = load_eval_definition(EXAMPLE_ROOT / "eval.yaml")
    envelope = FakeExecutionAdapter().execute(definition.test_cases[0], EXAMPLE_ROOT)

    with pytest.raises(ValueError, match="duplicate evidence id"):
        EvidenceStore([envelope.evidence[0], envelope.evidence[0]])
