"""Definition and semantic-resource digest verification helpers."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from hmac import compare_digest

from skill_eval_framework.schemas.definition import BenchmarkDefinition, DefinitionResourceBinding
from skill_eval_framework.schemas.runtime import FrozenDefinitionRef

from .canonical import CLOSURE_PROFILE, canonicalize_frozen_definition
from .errors import (
    DigestMismatchError,
    SemanticResourceDigestMismatchError,
    UnsupportedClosureProfileError,
)

type ResourceResolver = Mapping[str, bytes] | Callable[[str], bytes | None]


@dataclass(frozen=True, slots=True)
class DigestVerificationResult:
    """Typed detail for callers that need more than a boolean match."""

    expected_digest: str
    computed_digest: str
    matches: bool


def _check_profile(profile: str) -> None:
    if profile != CLOSURE_PROFILE:
        raise UnsupportedClosureProfileError(f"unsupported closure profile: {profile!r}")


def _sha256(content: bytes) -> str:
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def compute_definition_digest(
    benchmark: BenchmarkDefinition,
    *,
    closure_profile: str = CLOSURE_PROFILE,
) -> str:
    """Compute the content-identity digest of a complete Frozen Definition."""

    _check_profile(closure_profile)
    return _sha256(canonicalize_frozen_definition(benchmark, closure_profile=closure_profile))


def verify_definition_digest(
    benchmark: BenchmarkDefinition,
    expected_digest: str,
    *,
    closure_profile: str = CLOSURE_PROFILE,
) -> bool:
    """Return whether ``expected_digest`` matches the computed Definition digest."""

    computed = compute_definition_digest(benchmark, closure_profile=closure_profile)
    return compare_digest(computed, expected_digest)


def verify_definition_digest_result(
    benchmark: BenchmarkDefinition,
    expected_digest: str,
    *,
    closure_profile: str = CLOSURE_PROFILE,
) -> DigestVerificationResult:
    computed = compute_definition_digest(benchmark, closure_profile=closure_profile)
    return DigestVerificationResult(
        expected_digest, computed, compare_digest(computed, expected_digest)
    )


def compute_semantic_resource_digest(content: bytes) -> str:
    """Hash raw resolved resource bytes; logical refs are never opened implicitly."""

    if not isinstance(content, bytes):
        raise TypeError("semantic resource content must be bytes")
    return _sha256(content)


def verify_semantic_resource(binding: DefinitionResourceBinding, content: bytes) -> bool:
    """Return whether raw bytes match one DefinitionResourceBinding."""

    return compare_digest(compute_semantic_resource_digest(content), binding.content_digest)


def assert_semantic_resource(binding: DefinitionResourceBinding, content: bytes) -> None:
    if not verify_semantic_resource(binding, content):
        raise SemanticResourceDigestMismatchError(
            f"resource {binding.resource_ref!r} does not match its content digest"
        )


def _resolve_resource(resolver: ResourceResolver, resource_ref: str) -> bytes | None:
    if isinstance(resolver, Mapping):
        return resolver.get(resource_ref)
    return resolver(resource_ref)


def verify_run_definition_binding(
    run_definition_ref: FrozenDefinitionRef,
    benchmark: BenchmarkDefinition,
    resource_contents: ResourceResolver | None = None,
) -> bool:
    """Verify a Run's complete Definition identity and explicitly supplied resources."""

    _check_profile(run_definition_ref.definition_closure_profile)
    if (
        run_definition_ref.benchmark_id != benchmark.benchmark_id
        or run_definition_ref.benchmark_version != benchmark.version
    ):
        return False
    if not verify_definition_digest(
        benchmark,
        run_definition_ref.definition_digest,
        closure_profile=run_definition_ref.definition_closure_profile,
    ):
        return False
    for binding in benchmark.semantic_resource_bindings:
        if resource_contents is None:
            return False
        content = _resolve_resource(resource_contents, binding.resource_ref)
        if content is None or not verify_semantic_resource(binding, content):
            return False
    return True


def detect_same_version_drift(
    expected_ref: FrozenDefinitionRef,
    computed_digest: str,
) -> bool:
    """Return true only for same id/version/profile with a different digest."""

    _check_profile(expected_ref.definition_closure_profile)
    return expected_ref.definition_digest != computed_digest


def assert_definition_digest(
    benchmark: BenchmarkDefinition,
    expected_digest: str,
    *,
    closure_profile: str = CLOSURE_PROFILE,
) -> None:
    if not verify_definition_digest(benchmark, expected_digest, closure_profile=closure_profile):
        raise DigestMismatchError(f"Definition digest mismatch: expected {expected_digest!r}")


__all__ = [
    "DigestVerificationResult",
    "ResourceResolver",
    "assert_definition_digest",
    "assert_semantic_resource",
    "compute_definition_digest",
    "compute_semantic_resource_digest",
    "detect_same_version_drift",
    "verify_definition_digest",
    "verify_definition_digest_result",
    "verify_run_definition_binding",
    "verify_semantic_resource",
]
