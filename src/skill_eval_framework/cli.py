"""Thin JSON CLI over the authoritative Skill Eval Framework core APIs."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, NoReturn, TextIO

from pydantic import ValidationError, model_validator

from skill_eval_framework.digest import CLOSURE_PROFILE_V1, compute_definition_digest_v03
from skill_eval_framework.evaluation import (
    EvaluationServiceError,
    calculate_metric_result,
    calculate_overall_score,
    evaluate_acceptance,
    evaluate_gate,
)
from skill_eval_framework.runtime import (
    IntegrityFinalizationError,
    RuntimeServiceError,
    build_final_inventory,
    create_episode_for_slot,
    create_interim_scorecard,
    create_run,
    finalize_run_validity,
    finalize_scorecard,
    prevalidate_run,
    transition_episode,
    transition_run_execution,
)
from skill_eval_framework.schemas.common import (
    GateSpecificationId,
    MetricSpecificationId,
    NonEmptyStr,
    SchemaModel,
)
from skill_eval_framework.schemas.definition_v03 import BenchmarkDefinitionV03
from skill_eval_framework.schemas.results import GraderResult
from skill_eval_framework.schemas.runtime import (
    Artifact,
    Episode,
    EpisodeExecutionStatus,
    Evidence,
    FrozenDefinitionRef,
    RunExecutionPlan,
    RunExecutionStatus,
    RuntimeDiagnostic,
    RuntimeExecutionContext,
    RunValidityStatus,
    SubjectReference,
)
from skill_eval_framework.validation import (
    ValidationIssue,
    validate_benchmark_definition_v03,
    validate_run_definition_binding,
    validate_run_graph,
)

INPUT_VERSION = "skill-eval-evaluation-input/v0.1"
OUTPUT_VERSION = "skill-eval-evaluation-output/v0.1"


class ResultIdentifiers(SchemaModel):
    """Caller-controlled stable IDs for Results produced by the core evaluators."""

    metric_result_ids: dict[MetricSpecificationId, NonEmptyStr]
    gate_result_ids: dict[GateSpecificationId, NonEmptyStr]
    scorecard_id: NonEmptyStr


class EvaluationInput(SchemaModel):
    """CLI transport envelope containing only upstream Runtime products."""

    input_version: Literal["skill-eval-evaluation-input/v0.1"]
    definition_ref: FrozenDefinitionRef
    run_id: NonEmptyStr
    subject_ref: SubjectReference
    execution_context: RuntimeExecutionContext
    execution_plan: RunExecutionPlan
    run_created_at: datetime
    run_started_at: datetime
    run_ended_at: datetime
    run_diagnostic_ids: list[NonEmptyStr]
    episodes: list[Episode]
    artifacts: list[Artifact]
    evidence: list[Evidence]
    grader_results: list[GraderResult]
    diagnostics: list[RuntimeDiagnostic]
    result_ids: ResultIdentifiers
    result_created_at: datetime
    finalized_at: datetime

    @model_validator(mode="after")
    def validate_terminal_execution_input(self) -> EvaluationInput:
        if self.run_started_at < self.run_created_at:
            raise ValueError("run_started_at must not precede run_created_at")
        if self.run_ended_at < self.run_started_at:
            raise ValueError("run_ended_at must not precede run_started_at")
        if any(
            episode.execution_status != EpisodeExecutionStatus.COMPLETED
            for episode in self.episodes
        ):
            raise ValueError("evaluate currently requires completed Episode inputs")
        return self


class CliFailure(Exception):
    """Structured command failure rendered as deterministic JSON on stderr."""

    def __init__(
        self,
        error_type: str,
        message: str,
        *,
        details: Sequence[dict[str, object]] = (),
    ) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message
        self.details = list(details)


def _json_payload(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CliFailure("io_error", f"cannot read {path}: {exc}") from exc
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CliFailure(
            "input_schema_error",
            f"invalid JSON in {path}: line {exc.lineno}, column {exc.colno}",
        ) from exc
    if not isinstance(value, dict):
        raise CliFailure("input_schema_error", f"JSON root in {path} must be an object")
    return value


def _validation_error_details(exc: ValidationError) -> list[dict[str, object]]:
    return [
        {
            "path": ".".join(str(part) for part in error["loc"]),
            "code": error["type"],
            "message": error["msg"],
        }
        for error in exc.errors(include_url=False, include_input=False)
    ]


def _issue_details(issues: Sequence[ValidationIssue]) -> list[dict[str, object]]:
    return [{"path": issue.path, "code": issue.code, "message": issue.message} for issue in issues]


def _load_definition(path: Path) -> BenchmarkDefinitionV03:
    try:
        return BenchmarkDefinitionV03.model_validate(_json_payload(path))
    except ValidationError as exc:
        raise CliFailure(
            "definition_schema_error",
            "Definition is not a valid BenchmarkDefinitionV03",
            details=_validation_error_details(exc),
        ) from exc


def _validated_definition(path: Path) -> BenchmarkDefinitionV03:
    benchmark = _load_definition(path)
    report = validate_benchmark_definition_v03(benchmark)
    if report.issues:
        raise CliFailure(
            "definition_validation_error",
            "Definition failed cross-object validation",
            details=_issue_details(report.issues),
        )
    return benchmark


def _load_evaluation_input(path: Path) -> EvaluationInput:
    try:
        return EvaluationInput.model_validate(_json_payload(path))
    except ValidationError as exc:
        raise CliFailure(
            "input_schema_error",
            "run input does not match the CLI evaluation input contract",
            details=_validation_error_details(exc),
        ) from exc


def _validate_result_ids(benchmark: BenchmarkDefinitionV03, value: EvaluationInput) -> None:
    expected_metrics = {item.metric_id for item in benchmark.metric_specifications}
    supplied_metrics = set(value.result_ids.metric_result_ids)
    expected_gates = {item.gate_id for item in benchmark.gate_specifications}
    supplied_gates = set(value.result_ids.gate_result_ids)
    details: list[dict[str, object]] = []
    if supplied_metrics != expected_metrics:
        details.append(
            {
                "path": "result_ids.metric_result_ids",
                "code": "CLI_METRIC_RESULT_IDS_MISMATCH",
                "message": "keys must exactly match Definition metric IDs",
            }
        )
    if supplied_gates != expected_gates:
        details.append(
            {
                "path": "result_ids.gate_result_ids",
                "code": "CLI_GATE_RESULT_IDS_MISMATCH",
                "message": "keys must exactly match Definition gate IDs",
            }
        )
    if details:
        raise CliFailure("input_schema_error", "Result ID mapping is incomplete", details=details)


def _materialize_episodes(run: object, value: EvaluationInput) -> list[Episode]:
    from skill_eval_framework.schemas.runtime import Run

    if not isinstance(run, Run):  # pragma: no cover - internal type guard
        raise TypeError("run must be a Run")
    episodes: list[Episode] = []
    ordered = sorted(
        value.episodes,
        key=lambda item: (str(item.test_case_id), item.attempt_index, item.episode_id),
    )
    for source in ordered:
        if source.run_id != value.run_id:
            raise CliFailure(
                "runtime_graph_error",
                f"Episode {source.episode_id} belongs to a different Run",
                details=[
                    {
                        "path": f"episodes.{source.episode_id}.run_id",
                        "code": "CLI_EPISODE_RUN_MISMATCH",
                        "message": "Episode run_id must match the CLI run_id",
                    }
                ],
            )
        if source.started_at is None or source.ended_at is None:
            raise CliFailure(
                "input_schema_error",
                f"completed Episode {source.episode_id} requires timestamps",
            )
        episode = create_episode_for_slot(
            run,
            episodes,
            episode_id=source.episode_id,
            test_case_id=source.test_case_id,
            attempt_index=source.attempt_index,
            created_at=source.created_at,
        )
        episode = episode.model_copy(
            update={
                "trace_events": source.trace_events,
                "artifact_ids": source.artifact_ids,
                "evidence_ids": source.evidence_ids,
                "diagnostic_ids": source.diagnostic_ids,
            }
        )
        episode = transition_episode(
            episode,
            EpisodeExecutionStatus.RUNNING,
            timestamp=source.started_at,
        )
        episode = transition_episode(
            episode,
            EpisodeExecutionStatus.COMPLETED,
            timestamp=source.ended_at,
        )
        episodes.append(episode)
    return episodes


def _orchestrate_evaluation(
    benchmark: BenchmarkDefinitionV03,
    value: EvaluationInput,
) -> dict[str, object]:
    _validate_result_ids(benchmark, value)
    run = create_run(
        run_id=value.run_id,
        definition_ref=value.definition_ref,
        subject_ref=value.subject_ref,
        execution_context=value.execution_context,
        execution_plan=value.execution_plan,
        created_at=value.run_created_at,
    )
    binding = validate_run_definition_binding(benchmark, run)
    if binding.issues:
        raise CliFailure(
            "definition_identity_error",
            "Run Definition identity does not match the supplied Definition",
            details=_issue_details(binding.issues),
        )
    run = prevalidate_run(benchmark, run)
    if run.validity_status == RunValidityStatus.INVALID:
        raise CliFailure(
            "definition_validation_error",
            "Run prevalidation failed",
            details=[
                {"path": "run", "code": item.code, "message": item.message}
                for item in run.validity_findings
            ],
        )
    run = transition_run_execution(
        run,
        RunExecutionStatus.RUNNING,
        timestamp=value.run_started_at,
    )
    episodes = _materialize_episodes(run, value)
    run = run.model_copy(
        update={
            "episode_ids": [item.episode_id for item in episodes],
            "diagnostic_ids": value.run_diagnostic_ids,
        }
    )
    run = transition_run_execution(
        run,
        RunExecutionStatus.COMPLETED,
        timestamp=value.run_ended_at,
    )

    artifacts = sorted(value.artifacts, key=lambda item: item.artifact_id)
    evidence = sorted(value.evidence, key=lambda item: item.evidence_id)
    grader_results = sorted(
        value.grader_results,
        key=lambda item: (
            item.episode_id,
            str(item.test_case_id),
            str(item.contract_id),
            str(item.grader_id),
            item.grader_result_id,
        ),
    )
    diagnostics = sorted(value.diagnostics, key=lambda item: item.diagnostic_id)
    upstream_report = validate_run_graph(
        benchmark,
        run,
        episodes,
        artifacts,
        evidence,
        grader_results,
        (),
        (),
        diagnostics,
    )
    if upstream_report.issues:
        raise CliFailure(
            "runtime_graph_error",
            "upstream Runtime graph failed validation",
            details=_issue_details(upstream_report.issues),
        )

    try:
        metric_results = [
            calculate_metric_result(
                specification,
                run_id=value.run_id,
                metric_result_id=value.result_ids.metric_result_ids[specification.metric_id],
                created_at=value.result_created_at,
                grader_results=grader_results,
                episodes=episodes,
            )
            for specification in sorted(
                benchmark.metric_specifications,
                key=lambda item: item.metric_id,
            )
        ]
        gate_results = [
            evaluate_gate(
                specification,
                run_id=value.run_id,
                gate_result_id=value.result_ids.gate_result_ids[specification.gate_id],
                created_at=value.result_created_at,
                grader_results=grader_results,
                metric_results=metric_results,
                episodes=episodes,
            )
            for specification in sorted(
                benchmark.gate_specifications,
                key=lambda item: item.gate_id,
            )
        ]
        pending_overall = calculate_overall_score(
            benchmark.overall_score_policy,
            run_id=value.run_id,
            definition_digest=value.definition_ref.definition_digest,
            metric_results=metric_results,
            run_state="pending",
        )
        pending_acceptance = evaluate_acceptance(
            benchmark.acceptance_policy,
            run_id=value.run_id,
            definition_digest=value.definition_ref.definition_digest,
            gate_results=gate_results,
            run_state="pending",
        )
    except EvaluationServiceError as exc:
        raise CliFailure("evaluation_error", str(exc)) from exc

    interim = create_interim_scorecard(
        scorecard_id=value.result_ids.scorecard_id,
        benchmark=benchmark,
        run=run,
        episodes=episodes,
        grader_results=grader_results,
        metric_results=metric_results,
        gate_results=gate_results,
        diagnostics=diagnostics,
        overall_score_outcome=pending_overall,
        acceptance_evaluation=pending_acceptance,
    )
    final_inventory = build_final_inventory(
        benchmark,
        run,
        episodes=episodes,
        grader_results=grader_results,
        metric_results=metric_results,
        gate_results=gate_results,
        diagnostics=diagnostics,
    )
    interim = interim.model_copy(update={"result_inventory": final_inventory})
    finalized_run = finalize_run_validity(
        benchmark,
        run,
        episodes=episodes,
        artifacts=artifacts,
        evidence=evidence,
        grader_results=grader_results,
        metric_results=metric_results,
        gate_results=gate_results,
        diagnostics=diagnostics,
        scorecard=interim,
    )
    if finalized_run.validity_status != RunValidityStatus.VALID:
        raise CliFailure(
            "runtime_graph_error",
            "Run failed final integrity validation",
            details=[
                {"path": "run", "code": item.code, "message": item.message}
                for item in finalized_run.validity_findings
            ],
        )

    try:
        overall = calculate_overall_score(
            benchmark.overall_score_policy,
            run_id=value.run_id,
            definition_digest=value.definition_ref.definition_digest,
            metric_results=metric_results,
        )
        acceptance = evaluate_acceptance(
            benchmark.acceptance_policy,
            run_id=value.run_id,
            definition_digest=value.definition_ref.definition_digest,
            gate_results=gate_results,
        )
    except EvaluationServiceError as exc:
        raise CliFailure("evaluation_error", str(exc)) from exc

    try:
        scorecard = finalize_scorecard(
            scorecard=interim,
            benchmark=benchmark,
            run=finalized_run,
            episodes=episodes,
            artifacts=artifacts,
            evidence=evidence,
            grader_results=grader_results,
            metric_results=metric_results,
            gate_results=gate_results,
            diagnostics=diagnostics,
            overall_score_outcome=overall,
            acceptance_evaluation=acceptance,
            finalization_status="finalized_evaluation",
            finalized_at=value.finalized_at,
        )
    except IntegrityFinalizationError as exc:
        raise CliFailure("finalization_error", str(exc)) from exc

    return {
        "output_version": OUTPUT_VERSION,
        "definition_identity": value.definition_ref.model_dump(mode="json"),
        "run": finalized_run.model_dump(mode="json"),
        "episodes": [item.model_dump(mode="json") for item in episodes],
        "artifacts": [item.model_dump(mode="json") for item in artifacts],
        "evidence": [item.model_dump(mode="json") for item in evidence],
        "grader_results": [item.model_dump(mode="json") for item in grader_results],
        "metric_results": [item.model_dump(mode="json") for item in metric_results],
        "gate_results": [item.model_dump(mode="json") for item in gate_results],
        "diagnostics": [item.model_dump(mode="json") for item in diagnostics],
        "overall_score_outcome": overall.model_dump(mode="json"),
        "acceptance_evaluation": acceptance.model_dump(mode="json"),
        "scorecard": scorecard.model_dump(mode="json"),
    }


def _write_json(path: Path, payload: object) -> None:
    try:
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise CliFailure("io_error", f"cannot write {path}: {exc}") from exc


def _emit(stream: TextIO, payload: object) -> None:
    stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def _validate_command(path: Path) -> dict[str, object]:
    benchmark = _validated_definition(path)
    return {
        "command": "validate",
        "status": "valid",
        "definition_type": "BenchmarkDefinitionV03",
        "benchmark_id": benchmark.benchmark_id,
        "benchmark_version": benchmark.version,
        "issues": [],
    }


def _digest_command(path: Path) -> str:
    benchmark = _validated_definition(path)
    return compute_definition_digest_v03(benchmark, closure_profile=CLOSURE_PROFILE_V1)


def _evaluate_command(
    definition_path: Path,
    input_path: Path,
    output_path: Path,
) -> dict[str, object]:
    benchmark = _validated_definition(definition_path)
    value = _load_evaluation_input(input_path)
    output = _orchestrate_evaluation(benchmark, value)
    _write_json(output_path, output)
    return {
        "command": "evaluate",
        "status": "success",
        "output": str(output_path),
        "run_id": value.run_id,
        "definition_digest": value.definition_ref.definition_digest,
        "run_validity": output["run"]["validity_status"],  # type: ignore[index]
        "scorecard_status": output["scorecard"]["finalization_status"],  # type: ignore[index]
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="skill-eval")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate", help="validate a v0.3 Definition")
    validate_parser.add_argument("definition", type=Path)
    digest_parser = subparsers.add_parser("digest", help="compute a v1 Definition digest")
    digest_parser.add_argument("definition", type=Path)
    evaluate_parser = subparsers.add_parser("evaluate", help="run deterministic evaluation")
    evaluate_parser.add_argument("--definition", type=Path, required=True)
    evaluate_parser.add_argument("--run-input", type=Path, required=True)
    evaluate_parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""

    args = _parser().parse_args(argv)
    try:
        if args.command == "validate":
            _emit(sys.stdout, _validate_command(args.definition))
        elif args.command == "digest":
            sys.stdout.write(_digest_command(args.definition) + "\n")
        elif args.command == "evaluate":
            _emit(
                sys.stdout,
                _evaluate_command(args.definition, args.run_input, args.output),
            )
        else:  # pragma: no cover - argparse guarantees a known command
            raise AssertionError(f"unhandled command: {args.command}")
    except CliFailure as exc:
        _emit(
            sys.stderr,
            {
                "status": "error",
                "error_type": exc.error_type,
                "message": exc.message,
                "details": exc.details,
            },
        )
        return 1
    except RuntimeServiceError as exc:
        _emit(
            sys.stderr,
            {
                "status": "error",
                "error_type": "runtime_graph_error",
                "message": str(exc),
                "details": [],
            },
        )
        return 1
    return 0


def _run() -> NoReturn:
    raise SystemExit(main())


if __name__ == "__main__":
    _run()
