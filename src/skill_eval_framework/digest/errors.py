"""Typed errors raised by the Frozen Definition digest layer."""


class DigestError(ValueError):
    """Base error for canonicalization and content-identity checks."""


class UnsupportedClosureProfileError(DigestError):
    """Raised when a caller requests a profile not implemented by this package."""


class CanonicalizationError(DigestError):
    """Raised when a Definition cannot be represented by the frozen protocol."""


class DigestMismatchError(DigestError):
    """Raised by strict helpers when a computed digest differs from an expected one."""


class SemanticResourceDigestMismatchError(DigestError):
    """Raised when resolved resource bytes do not match their Definition binding."""
