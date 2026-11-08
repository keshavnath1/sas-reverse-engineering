"""CP3A explicit, read-only POSIX inspection; declarations never grant approval.

The trusted local caller supplies a separate exact inspection policy. This is
not an authentication service, serialized capability, or publication permission.
No legacy workflow consumes this API and no output store is created.
"""

from dataclasses import dataclass
from importlib import import_module

from ._authorization_paths import _native_parts
from ._io_common import EvidenceError, _parse_json, canonical_bytes, MAX_DEPTH
from .authorization import validate_authorization, authorization_scope_identity
from .platform_io import require_evidence_io


SOURCE_MODEL = "QUIESCENT_SYNTHETIC_TRUSTED_WRITERS"


@dataclass(frozen=True)
class LocalInspectionPolicy:
    """Exact invocation scope supplied independently by the trusted host caller.

    NOT a verified human approval. The anchor must be dedicated and caller-owned;
    every root/store must be beneath it. Do not derive policy automatically from
    an untrusted envelope. Host writers/administrators must be trusted/quiescent.
    """

    anchor: str
    source_roots: tuple[tuple[str, str], ...]
    store_path: str
    workspace_id: str
    run_id: str
    scope_sha256: str
    source_model: str


def _request(envelope: object, policy: LocalInspectionPolicy) -> tuple[dict, tuple[str, ...]]:
    if type(policy) is not LocalInspectionPolicy:
        raise EvidenceError("CP3A_POLICY_REQUIRED", "BLOCKED")
    validate_authorization(envelope, expected_platform="posix")
    # Strict built-in JSON was validated first; detach without invoking caller
    # copy hooks, and never mutate the frozen declaration or its projection.
    detached = _parse_json(canonical_bytes(envelope))
    logical = detached["logical_scope"]
    if (
        any(
            type(getattr(policy, field)) is not str
            for field in (
                "anchor",
                "store_path",
                "workspace_id",
                "run_id",
                "scope_sha256",
                "source_model",
            )
        )
        or type(policy.source_roots) is not tuple
        or any(
            type(item) is not tuple
            or len(item) != 2
            or any(type(value) is not str for value in item)
            for item in policy.source_roots
        )
    ):
        raise EvidenceError("CP3A_POLICY_MISMATCH")
    expected = tuple(sorted((item["root_id"], item["path"]) for item in detached["bindings"]))
    if (
        tuple(sorted(policy.source_roots)) != expected
        or policy.workspace_id != logical["workspace_id"]
        or policy.run_id != logical["run_id"]
        or policy.scope_sha256 != authorization_scope_identity(detached)
    ):
        raise EvidenceError("CP3A_POLICY_MISMATCH")
    if policy.source_model != SOURCE_MODEL:
        raise EvidenceError("CP3A_WRITER_POLICY_UNAVAILABLE", "BLOCKED")
    anchor = _native_parts("posix", policy.anchor)
    if len(anchor) > 64:
        raise EvidenceError("CP3A_LIMIT", "BLOCKED")
    for path, is_source in [(path, True) for _, path in expected] + [(policy.store_path, False)]:
        parts = _native_parts("posix", path)
        if parts[: len(anchor)] != anchor or (is_source and len(parts) == len(anchor)):
            raise EvidenceError("CP3A_OUTSIDE_ANCHOR")
        if len(parts) - len(anchor) > MAX_DEPTH:
            raise EvidenceError("CP3A_LIMIT", "BLOCKED")
    return detached, anchor


def open_preflight(envelope: object, *, policy: LocalInspectionPolicy | None = None):
    """Bind metadata, prove disjointness, acquire ALL read handles; read no bytes.

    Use as a context manager and call ``read_sources()`` once for a detached
    file-key -> original bytes mapping. No reusable permission receipt, arbitrary
    path reader, inventory publisher, or native identity artifact is returned.
    Missing guarantees fail BLOCKED. Windows denies before supplied-path access.
    """
    require_evidence_io()
    detached, anchor = _request(envelope, policy)
    try:
        backend = import_module("sas_re._filesystem._posix_preflight")
    except (ImportError, AttributeError):
        raise EvidenceError("CP3A_FILESYSTEM_UNAVAILABLE", "BLOCKED") from None
    return backend.PosixPreflight(detached, policy, anchor)
