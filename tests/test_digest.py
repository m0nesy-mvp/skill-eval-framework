"""Conformance tests for the Frozen Definition digest protocol."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from hashlib import sha256

import pytest

from skill_eval_framework.digest import (
    CLOSURE_PROFILE,
    CanonicalizationError,
    SemanticResourceDigestMismatchError,
    UnsupportedClosureProfileError,
    canonical_decimal,
    canonicalize_frozen_definition,
    compute_definition_digest,
    compute_semantic_resource_digest,
    verify_definition_digest,
    verify_run_definition_binding,
    verify_semantic_resource,
)
from skill_eval_framework.schemas.definition import BenchmarkDefinition
from skill_eval_framework.schemas.runtime import FrozenDefinitionRef

BASELINE_DIGEST = "sha256:e3001a339eb733b388979f54ba6291ff68ebdba39c5a0dc24a1eb5d2a1d6d218"
CHINESE_DIGEST = "sha256:a67f98898473108b9d0ee8dc5497b0cd409bf5751c0e8796de609183101d9ca4"


def _definition(data: dict[str, object]) -> BenchmarkDefinition:
    return BenchmarkDefinition.model_validate(data)


def test_fixed_conformance_vectors(definition_data: dict[str, object]) -> None:
    baseline = _definition(definition_data)
    chinese_data = deepcopy(definition_data)
    chinese_data["description"] = "Representative frozen definition\nwith Chinese 中文"
    chinese = _definition(chinese_data)

    assert compute_definition_digest(baseline) == BASELINE_DIGEST
    assert compute_definition_digest(chinese) == CHINESE_DIGEST
    assert sha256(canonicalize_frozen_definition(baseline)).hexdigest() == BASELINE_DIGEST[7:]


def test_same_definition_is_byte_and_digest_stable(definition_data: dict[str, object]) -> None:
    benchmark = _definition(definition_data)
    assert canonicalize_frozen_definition(benchmark) == canonicalize_frozen_definition(benchmark)
    assert compute_definition_digest(benchmark) == compute_definition_digest(benchmark)
    assert verify_definition_digest(benchmark, BASELINE_DIGEST)
    assert b"definition_digest" not in canonicalize_frozen_definition(benchmark)


@pytest.mark.parametrize(
    "field",
    [
        "requirements",
        "contracts",
        "test_cases",
        "evidence_specifications",
        "grader_specifications",
        "metric_specifications",
        "gate_specifications",
    ],
)
def test_top_level_set_like_collections_are_order_independent(
    definition_data: dict[str, object], field: str
) -> None:
    second_items = {
        "requirements": {
            "requirement_id": "R002",
            "statement": "A second requirement.",
            "source": "user",
            "evaluation_type": "outcome",
        },
        "contracts": {
            "contract_id": "C002",
            "requirement_ids": ["R001"],
            "statement": "A second contract.",
            "evaluation_type": "outcome",
            "criticality": "normal",
            "success_criteria": ["Second success."],
            "failure_criteria": ["Second failure."],
            "failure_modes": ["Second failure mode."],
        },
        "test_cases": {
            "test_case_id": "TC002",
            "task": "Produce another output.",
            "preconditions": [],
            "fixtures": [],
            "initial_state": [],
            "interaction_steps": [],
            "expected_assertions": [
                {"contract_id": "C001", "expectation": "Another output is present."}
            ],
        },
        "evidence_specifications": {
            "evidence_spec_id": "ES002",
            "targets": [{"test_case_id": "TC001", "contract_id": "C001"}],
            "observation_requirements": ["Observe another response."],
            "provenance_requirements": ["Retain another trace."],
            "context_requirements": [],
            "qualification_requirements": ["Another response is attributable."],
        },
        "grader_specifications": {
            "grader_id": "G002",
            "targets": [
                {"test_case_id": "TC001", "contract_id": "C001", "evidence_spec_ids": ["ES001"]}
            ],
            "judgment_criteria": ["Compare another observation."],
            "result_semantics": {
                "satisfied": "Supported.",
                "violated": "Contradicted.",
                "insufficient_evidence": "Cannot decide.",
            },
            "insufficiency_handling": ["List another missing observation."],
            "explanation_requirements": ["Cite another contribution."],
            "rubric": None,
        },
        "metric_specifications": {
            "metric_id": "M002",
            "name": "Another rate",
            "inputs": [{"test_case_id": "TC001", "contract_id": "C001"}],
            "result_selection_policy": "Use the final attempt.",
            "aggregation_unit": "contract application",
            "eligibility_policy": {
                "eligible_result_semantics": ["satisfied"],
                "non_substantive_handling": ["Exclude not exercised."],
                "unavailable_input_handling": ["Report missing input."],
            },
            "contribution_mapping": [
                {"source_semantics": "satisfied", "contribution_semantics": "1"}
            ],
            "unit_reduction": "One contribution.",
            "aggregation_rule": "Arithmetic mean.",
            "weighting_policy": "Equal weight.",
            "completeness_policy": {
                "minimum_input_requirement": "One eligible input.",
                "partial_result_policy": "Allow partial.",
                "empty_denominator_policy": "Return unavailable.",
                "transparency_requirements": ["Report denominator."],
            },
            "result_semantics": {
                "interpretation": "Another share.",
                "direction": "Higher is better.",
                "scale": "Unit interval.",
                "denominator_meaning": "Eligible applications.",
            },
        },
        "gate_specifications": {
            "gate_id": "GATE002",
            "name": "Another threshold",
            "scope": "whole benchmark",
            "condition": {
                "condition_type": "metric_threshold",
                "metric_id": "M001",
                "comparator": "gte",
                "threshold_value": "0.2",
            },
            "unavailable_handling": "indeterminate",
            "result_semantics": {
                "open_meaning": "Open.",
                "triggered_meaning": "Triggered.",
                "indeterminate_meaning": "Indeterminate.",
                "blocking_effect": "Blocks acceptance.",
            },
            "explanation_requirements": ["Report another value."],
        },
    }
    original_data = deepcopy(definition_data)
    original_data[field].append(deepcopy(second_items[field]))
    original = _definition(original_data)
    reordered = deepcopy(definition_data)
    values = reordered[field]
    assert isinstance(values, list)
    values.append(second_items[field])
    values.reverse()
    assert canonicalize_frozen_definition(original) == canonicalize_frozen_definition(
        _definition(reordered)
    )


def test_nested_set_like_collections_are_order_independent(
    definition_data: dict[str, object],
) -> None:
    original = _definition(definition_data)
    reordered = deepcopy(definition_data)
    metric = reordered["metric_specifications"][0]
    metric["contribution_mapping"].reverse()
    metric["eligibility_policy"]["eligible_result_semantics"].reverse()
    assert canonicalize_frozen_definition(original) == canonicalize_frozen_definition(
        _definition(reordered)
    )


def test_ordered_interaction_steps_change_digest(definition_data: dict[str, object]) -> None:
    data = deepcopy(definition_data)
    data["test_cases"][0]["interaction_steps"].append(
        {"trigger": "Follow-up request.", "response": "Follow-up response."}
    )
    forward = _definition(data)
    reversed_data = deepcopy(data)
    reversed_data["test_cases"][0]["interaction_steps"].reverse()
    assert compute_definition_digest(forward) != compute_definition_digest(
        _definition(reversed_data)
    )


def test_ordered_rubric_dimensions_and_anchors_change_digest(
    definition_data: dict[str, object],
) -> None:
    data = deepcopy(definition_data)
    data["grader_specifications"][0]["rubric"] = {
        "dimensions": [
            {
                "name": "quality",
                "criterion": "Output quality",
                "anchors": [
                    {"label": "low", "meaning": "Low quality"},
                    {"label": "high", "meaning": "High quality"},
                ],
            },
            {
                "name": "clarity",
                "criterion": "Output clarity",
                "anchors": [
                    {"label": "unclear", "meaning": "Unclear"},
                    {"label": "clear", "meaning": "Clear"},
                ],
            },
        ],
        "overall_interpretation": "Interpret together.",
    }
    forward = _definition(data)
    dimensions_reversed = deepcopy(data)
    dimensions_reversed["grader_specifications"][0]["rubric"]["dimensions"].reverse()
    anchors_reversed = deepcopy(data)
    anchors_reversed["grader_specifications"][0]["rubric"]["dimensions"][0]["anchors"].reverse()
    assert compute_definition_digest(forward) != compute_definition_digest(
        _definition(dimensions_reversed)
    )
    assert compute_definition_digest(forward) != compute_definition_digest(
        _definition(anchors_reversed)
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1", "1"),
        ("1.0", "1"),
        ("1.000", "1"),
        ("1e0", "1"),
        ("-0", "0"),
        ("0.5000", "0.5"),
        ("1.25e2", "125"),
    ],
)
def test_decimal_canonicalization(value: str, expected: str) -> None:
    assert canonical_decimal(Decimal(value)) == expected


@pytest.mark.parametrize("value", [Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")])
def test_non_finite_decimal_is_rejected(value: Decimal) -> None:
    with pytest.raises(CanonicalizationError):
        canonical_decimal(value)


def test_unicode_nfc_and_line_endings_are_normalized(definition_data: dict[str, object]) -> None:
    composed = deepcopy(definition_data)
    decomposed = deepcopy(definition_data)
    composed["description"] = "Café\n中文"
    decomposed["description"] = "Cafe\u0301\r\n中文"
    assert canonicalize_frozen_definition(_definition(composed)) == canonicalize_frozen_definition(
        _definition(decomposed)
    )


def test_unsupported_profile_is_explicit(definition_data: dict[str, object]) -> None:
    with pytest.raises(UnsupportedClosureProfileError):
        canonicalize_frozen_definition(_definition(definition_data), closure_profile="unknown")


def test_semantic_resource_verification_uses_raw_bytes(definition_data: dict[str, object]) -> None:
    content = b'{"value": 1}\r\n'
    data = deepcopy(definition_data)
    data["semantic_resource_bindings"] = [
        {
            "resource_ref": "logical/resource.json",
            "semantic_role": "fixture",
            "content_digest": compute_semantic_resource_digest(content),
        }
    ]
    benchmark = _definition(data)
    binding = benchmark.semantic_resource_bindings[0]
    assert verify_semantic_resource(binding, content)
    assert not verify_semantic_resource(binding, b'{"value": 1}')
    with pytest.raises(SemanticResourceDigestMismatchError):
        from skill_eval_framework.digest import assert_semantic_resource

        assert_semantic_resource(binding, b"wrong")

    changed = deepcopy(data)
    changed["semantic_resource_bindings"][0]["content_digest"] = compute_semantic_resource_digest(
        b"changed"
    )
    assert compute_definition_digest(benchmark) != compute_definition_digest(_definition(changed))


def test_run_definition_binding_checks_identity_and_explicit_resources(
    definition_data: dict[str, object],
) -> None:
    content = b"fixture bytes"
    data = deepcopy(definition_data)
    data["semantic_resource_bindings"] = [
        {
            "resource_ref": "logical/fixture",
            "semantic_role": "fixture",
            "content_digest": compute_semantic_resource_digest(content),
        }
    ]
    benchmark = _definition(data)
    ref = FrozenDefinitionRef(
        benchmark_id=benchmark.benchmark_id,
        benchmark_version=benchmark.version,
        definition_closure_profile=CLOSURE_PROFILE,
        definition_digest=compute_definition_digest(benchmark),
        definition_snapshot_ref="machine-independent/ref",
    )
    assert verify_run_definition_binding(ref, benchmark, {"logical/fixture": content})
    assert not verify_run_definition_binding(ref, benchmark)
    assert not verify_run_definition_binding(ref, benchmark, {"logical/fixture": b"wrong"})
    assert not verify_run_definition_binding(
        ref.model_copy(update={"benchmark_version": "9.9"}), benchmark
    )
