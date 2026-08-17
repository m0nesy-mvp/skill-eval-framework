"""Minimal validate and run command line interface for MVP 0."""

import argparse
import sys
from pathlib import Path
from uuid import uuid4

from skill_eval.application.runner import EvalRunner, InvalidEvalDesignError
from skill_eval.domain.enums import RunStatus
from skill_eval.domain.models import EvalDefinition
from skill_eval.execution.fake import FakeExecutionAdapter, FakeExecutionError
from skill_eval.infrastructure.yaml_loader import DefinitionLoadError, load_eval_definition
from skill_eval.reporting.json_writer import write_baseline_artifacts
from skill_eval.validation.design import validate_eval_design

EXIT_BY_STATUS = {
    RunStatus.PASS: 0,
    RunStatus.FAIL: 1,
    RunStatus.BLOCKED: 2,
    RunStatus.ERROR: 3,
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="skill-eval")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate", help="validate an Eval Definition")
    validate.add_argument("definition", type=Path)
    run = subparsers.add_parser("run", help="run a fake-execution baseline")
    run.add_argument("definition", type=Path)
    run.add_argument("--output", type=Path, default=Path(".runs"))
    return parser


def _print_report(definition_path: Path) -> tuple[EvalDefinition | None, int]:
    try:
        definition = load_eval_definition(definition_path)
    except DefinitionLoadError as exc:
        print(f"Validation: ERROR\n- {exc}", file=sys.stderr)
        return None, 4
    report = validate_eval_design(definition)
    for finding in report.findings:
        print(f"{finding.severity.value.upper()} {finding.code}: {finding.message}")
    if report.is_valid:
        print("Validation: PASS")
        return definition, 0
    print("Validation: ERROR", file=sys.stderr)
    return None, 3


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    definition, validation_exit = _print_report(args.definition)
    if definition is None:
        return validation_exit
    if args.command == "validate":
        return 0

    try:
        run_id = f"baseline-{uuid4()}"
        result = EvalRunner().run(
            definition,
            FakeExecutionAdapter(),
            args.definition.parent,
            run_id,
        )
        artifacts = write_baseline_artifacts(
            definition,
            result,
            args.output,
            args.definition.parent,
        )
    except (FakeExecutionError, InvalidEvalDesignError, OSError, ValueError) as exc:
        print(f"Run: ERROR\n- {exc}", file=sys.stderr)
        return 3

    print(f"Run: {result.status.value.upper()}")
    print(f"Artifacts: {artifacts.run_directory.resolve()}")
    return EXIT_BY_STATUS[result.status]


if __name__ == "__main__":
    raise SystemExit(main())
