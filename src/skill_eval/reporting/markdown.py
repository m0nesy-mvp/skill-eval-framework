"""Human-readable rendering from an already-decided EvalResult."""

from skill_eval.domain.models import EvalResult, EvalRunManifest


def render_markdown(manifest: EvalRunManifest, result: EvalResult) -> str:
    lines = [
        "# Skill Eval Baseline Report",
        "",
        f"- Run ID: `{manifest.run_id}`",
        f"- Target Skill: `{manifest.target_skill_id}` `{manifest.skill_version}`",
        f"- Eval version: `{manifest.eval_version}`",
        f"- Overall status: **{result.status.value.upper()}**",
        "",
        "## Case Results",
        "",
        "| Case | Status | Contracts | Execution |",
        "|---|---|---|---|",
    ]
    for case in result.case_results:
        lines.append(
            f"| `{case.case_id}` | {case.status.value} | "
            f"{', '.join(f'`{item}`' for item in case.contract_ids)} | "
            f"`{case.execution_id}` |"
        )

    lines.extend(
        [
            "",
            "## Acceptance Gates",
            "",
            "| Gate | Type | Status | Actual | Operator | Threshold | Contributors |",
            "|---|---|---|---:|---|---:|---|",
        ]
    )
    for decision in result.gate_result.decisions:
        lines.append(
            f"| `{decision.gate_id}` | {decision.gate_type.value} | "
            f"{decision.status.value} | {decision.actual_value} | "
            f"{decision.operator.value} | {decision.threshold} | "
            f"{', '.join(f'`{item}`' for item in decision.contributing_grade_result_ids)} |"
        )

    lines.extend(["", "## Failures", ""])
    if result.failures:
        for failure in result.failures:
            evidence = ", ".join(f"`{item}`" for item in failure.evidence_refs) or "none"
            lines.append(
                f"- `{failure.failure_id}` [{failure.domain.value}/{failure.code.value}]: "
                f"{failure.message}; evidence: {evidence}"
            )
    else:
        lines.append("No failures recorded.")

    lines.extend(
        [
            "",
            "## Contract Coverage",
            "",
            f"- Covered: {result.contract_coverage.covered}/{result.contract_coverage.total}",
            f"- Rate: {result.contract_coverage.rate:.3f}",
            "",
            "## Traceability",
            "",
            "| Requirement | Contract | Case | Expected | Grader | Grade Result |",
            "|---|---|---|---|---|---|",
        ]
    )
    for record in result.traceability.records:
        lines.append(
            f"| `{record.requirement_id}` | `{record.contract_id}` | `{record.case_id}` | "
            f"`{record.expected_id}` | `{record.grader_id}` | "
            f"`{record.grade_result_id}` |"
        )
    lines.append("")
    return "\n".join(lines)
