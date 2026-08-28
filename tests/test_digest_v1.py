"""Conformance tests for the v1 Frozen Definition closure protocol."""

from copy import deepcopy
from hashlib import sha256
from typing import Any

import pytest
from conftest import make_definition_data
from test_definition_v03_schema import definition_v03_data

from skill_eval_framework.digest import (
    CLOSURE_PROFILE,
    CLOSURE_PROFILE_V1,
    CanonicalizationError,
    UnsupportedClosureProfileError,
    canonicalize_frozen_definition,
    canonicalize_frozen_definition_v02,
    canonicalize_frozen_definition_v03,
    compute_definition_digest,
    compute_definition_digest_v02,
    compute_definition_digest_v03,
    verify_definition_digest_v02,
    verify_definition_digest_v03,
)
from skill_eval_framework.schemas.definition import BenchmarkDefinition
from skill_eval_framework.schemas.definition_v03 import BenchmarkDefinitionV03

VECTOR_A_DIGEST = "sha256:2993ae35813c668650111852c7d2288d7a319305b329498d3f83c7a775e18878"
VECTOR_B_DIGEST = "sha256:6e424529752e20182298ec952ae51b5159c92047eecee3adac746597b3e9eb58"


def _v02() -> BenchmarkDefinition:
    return BenchmarkDefinition.model_validate(make_definition_data())


def _v03(data: dict[str, Any] | None = None) -> BenchmarkDefinitionV03:
    return BenchmarkDefinitionV03.model_validate(definition_v03_data() if data is None else data)


def _vector_b_data() -> dict[str, Any]:
    data = definition_v03_data()
    data["description"] = "Cafe\u0301\r\n中文\r nested"
    data["metric_specifications"][0]["execution_policy"]["selection"] = {
        "mode": "final_distinct_raw",
        "order": "attempt_index_ascending",
    }
    data["gate_specifications"][0]["condition"] = {
        "condition_type": "grader_result_semantic",
        "targets": [{"test_case_id": "TC001", "contract_id": "C001"}],
        "selection": {"mode": "first_distinct", "order": "attempt_index_ascending"},
        "trigger_result_semantics": ["violated", "satisfied"],
        "quantifier": "any",
    }
    return data


def test_v02_historical_vector_and_bytes_unchanged() -> None:
    benchmark = _v02()
    canonical = canonicalize_frozen_definition_v02(benchmark)
    assert canonical == canonicalize_frozen_definition(benchmark)
    assert compute_definition_digest_v02(benchmark) == (
        "sha256:e3001a339eb733b388979f54ba6291ff68ebdba39c5a0dc24a1eb5d2a1d6d218"
    )
    assert verify_definition_digest_v02(benchmark, compute_definition_digest_v02(benchmark))


def test_v03_fixed_vectors_and_independent_sha256() -> None:
    vector_a = _v03()
    vector_b = _v03(_vector_b_data())
    canonical_a = canonicalize_frozen_definition_v03(vector_a)
    canonical_b = canonicalize_frozen_definition_v03(vector_b)
    assert compute_definition_digest_v03(vector_a) == VECTOR_A_DIGEST
    assert compute_definition_digest_v03(vector_b) == VECTOR_B_DIGEST
    # Independent verification path: hashlib over the fixed canonical bytes.
    assert f"sha256:{sha256(canonical_a).hexdigest()}" == VECTOR_A_DIGEST
    assert f"sha256:{sha256(canonical_b).hexdigest()}" == VECTOR_B_DIGEST
    assert b'"closure_profile":"skill-eval-frozen-definition-closure-v1"' in canonical_a
    assert verify_definition_digest_v03(vector_a, VECTOR_A_DIGEST)


def test_generic_digest_dispatch_and_cross_version_profiles() -> None:
    v02 = _v02()
    v03 = _v03()
    assert compute_definition_digest(v02) == compute_definition_digest_v02(v02)
    assert compute_definition_digest(v03) == compute_definition_digest_v03(v03)
    assert canonicalize_frozen_definition(v03).startswith(b'{"benchmark_definition":')
    with pytest.raises(UnsupportedClosureProfileError):
        canonicalize_frozen_definition_v03(v03, closure_profile=CLOSURE_PROFILE)
    with pytest.raises(UnsupportedClosureProfileError):
        canonicalize_frozen_definition_v02(v02, closure_profile=CLOSURE_PROFILE_V1)
    with pytest.raises(UnsupportedClosureProfileError):
        compute_definition_digest(v03, closure_profile=CLOSURE_PROFILE)
    with pytest.raises(UnsupportedClosureProfileError):
        compute_definition_digest(v02, closure_profile=CLOSURE_PROFILE_V1)


def test_v03_executable_policy_changes_change_digest() -> None:
    base = _v03()
    base_digest = compute_definition_digest_v03(base)

    data = definition_v03_data()
    data["metric_specifications"][0]["execution_policy"]["selection"] = {
        "mode": "final_distinct_raw",
        "order": "attempt_index_ascending",
    }
    assert compute_definition_digest_v03(_v03(data)) != base_digest

    data = definition_v03_data()
    data["metric_specifications"][0]["execution_policy"]["eligibility"]["eligible_semantics"] = [
        "satisfied"
    ]
    data["metric_specifications"][0]["execution_policy"]["contribution_mapping"] = [
        data["metric_specifications"][0]["execution_policy"]["contribution_mapping"][0]
    ]
    assert compute_definition_digest_v03(_v03(data)) != base_digest

    for field, value in (
        ("aggregation_unit", "per_contract"),
        ("unit_reduction", {"mode": "single"}),
    ):
        data = definition_v03_data()
        data["metric_specifications"][0]["execution_policy"][field] = value
        assert compute_definition_digest_v03(_v03(data)) != base_digest

    canonical = canonicalize_frozen_definition_v03(base)
    assert b'"weighting":{"mode":"equal_per_unit"}' in canonical
    assert b'"aggregation":{"mode":"mean"}' in canonical
    assert (
        b'"completeness":{"empty_denominator":"unavailable","mode":"strict",'
        b'"transparency_requirements":[]}'
    ) in canonical


def test_v03_semantic_and_mapping_order_are_set_like() -> None:
    original = _v03()
    data = definition_v03_data()
    policy = data["metric_specifications"][0]["execution_policy"]
    policy["eligibility"]["eligible_semantics"].reverse()
    policy["contribution_mapping"].reverse()
    assert canonicalize_frozen_definition_v03(original) == canonicalize_frozen_definition_v03(
        _v03(data)
    )

    data = definition_v03_data()
    policy = data["metric_specifications"][0]["execution_policy"]
    policy["eligibility"]["eligible_semantics"] = ["satisfied"]
    policy["contribution_mapping"] = [policy["contribution_mapping"][0]]
    assert compute_definition_digest_v03(_v03(data)) != compute_definition_digest_v03(original)


def test_v03_decimal_equivalence_and_descriptive_identity() -> None:
    data = definition_v03_data()
    data["metric_specifications"][0]["execution_policy"]["contribution_mapping"][0][
        "numeric_value"
    ] = "1.000"
    equivalent = _v03(data)
    assert canonicalize_frozen_definition_v03(equivalent) == canonicalize_frozen_definition_v03(
        _v03()
    )

    data["metric_specifications"][0]["execution_policy"]["contribution_mapping"][0][
        "numeric_value"
    ] = "0.5"
    assert compute_definition_digest_v03(_v03(data)) != compute_definition_digest_v03(_v03())

    data = definition_v03_data()
    data["metric_specifications"][0]["result_semantics"]["interpretation"] = "Changed meaning."
    assert compute_definition_digest_v03(_v03(data)) != compute_definition_digest_v03(_v03())


def test_v03_gate_ordering_and_selector_identity() -> None:
    data = definition_v03_data()
    gate = data["gate_specifications"][0]["condition"]
    gate["condition_type"] = "grader_result_semantic"
    gate["selection"] = {"mode": "all_distinct"}
    gate["trigger_result_semantics"] = ["violated", "satisfied"]
    gate["quantifier"] = "any"
    gate.pop("comparator")
    gate.pop("metric_id")
    gate.pop("threshold_value")
    gate["targets"] = [{"test_case_id": "TC001", "contract_id": "C001"}]
    first = _v03(data)

    reordered = deepcopy(data)
    reordered["gate_specifications"][0]["condition"]["trigger_result_semantics"].reverse()
    assert canonicalize_frozen_definition_v03(first) == canonicalize_frozen_definition_v03(
        _v03(reordered)
    )

    changed = deepcopy(data)
    changed["gate_specifications"][0]["condition"]["selection"] = {
        "mode": "first_distinct",
        "order": "attempt_index_ascending",
    }
    assert compute_definition_digest_v03(_v03(changed)) != compute_definition_digest_v03(first)


def test_v03_ordered_sequences_change_digest() -> None:
    data = definition_v03_data()
    data["test_cases"][0]["interaction_steps"].append(
        {"trigger": "Follow-up request.", "response": "Follow-up response."}
    )
    forward = _v03(data)
    reversed_data = deepcopy(data)
    reversed_data["test_cases"][0]["interaction_steps"].reverse()
    assert compute_definition_digest_v03(forward) != compute_definition_digest_v03(
        _v03(reversed_data)
    )


def test_v03_root_and_resource_collections_are_set_like() -> None:
    data = definition_v03_data()
    data["requirements"].append(
        {
            "requirement_id": "R002",
            "statement": "A second requirement.",
            "source": "user",
            "evaluation_type": "outcome",
        }
    )
    data["semantic_resource_bindings"] = [
        {
            "resource_ref": "z-resource",
            "semantic_role": "fixture",
            "content_digest": "sha256:" + "a" * 64,
        },
        {
            "resource_ref": "a-resource",
            "semantic_role": "fixture",
            "content_digest": "sha256:" + "b" * 64,
        },
    ]
    original = _v03(data)
    reordered = deepcopy(data)
    reordered["requirements"].reverse()
    reordered["semantic_resource_bindings"].reverse()
    assert canonicalize_frozen_definition_v03(original) == canonicalize_frozen_definition_v03(
        _v03(reordered)
    )
    changed = deepcopy(data)
    changed["semantic_resource_bindings"][0]["content_digest"] = "sha256:" + "c" * 64
    assert compute_definition_digest_v03(_v03(changed)) != compute_definition_digest_v03(original)


def test_canonicalization_rejects_unknown_types() -> None:
    with pytest.raises(CanonicalizationError):
        canonicalize_frozen_definition_v03(object())  # type: ignore[arg-type]
