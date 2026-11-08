"""Import-safe evidence API with a guarded, lazily selected filesystem backend.

Filesystem operations refuse unsupported capabilities before accessing caller
paths. Pure helpers keep their byte/validation rules and need no backend. Source
reads return original bytes; this API neither interprets nor executes SAS.

The backend owns filesystem checks and publication. Record schemas remain the
JSON contract authority; safe I/O and matching hashes do not establish semantic
acceptance or authenticated provenance against a filesystem owner.
"""

from dataclasses import dataclass
from pathlib import Path

from ._io_common import (
    ARTIFACT_NAMES,
    MAX_BYTES,
    MAX_FILES,
    MAX_DEPTH,
    MAX_DIRECTORIES,
    EvidenceError,
    safe_relative,
    canonical_bytes,
    _parse_json,
)
from .platform_io import get_backend, require_evidence_io


def require_safe_root(path: Path | str) -> Path:
    """Check an existing absolute directory without following symlink components.

    Args:
        path: Directory to check; no directory is created.

    Returns:
        The checked path, not a retained descriptor or future identity guarantee.

    Raises:
        EvidenceError: Capabilities are unavailable or the path is unsafe/missing.
    """
    return get_backend().require_safe_root(path)


def ensure_disjoint(store: Path | str, source_roots: list[Path] | tuple[Path, ...]) -> None:
    """Refuse output equal to, inside, or containing an authorized source root.

    Args:
        store: Absolute output path; this check does not create it.
        source_roots: Existing source directories to check without symlinks.

    Raises:
        EvidenceError: Capabilities, path checks, or the separation check fail.
    """
    return get_backend().ensure_disjoint(store, source_roots)


def secure_read(root: Path | str, relative: str, max_bytes: int = MAX_BYTES) -> bytes:
    """Read bounded original bytes without modifying the source file.

    Args:
        root: Existing absolute directory, traversed without symlinks.
        relative: Safe slash-separated path beneath the root.
        max_bytes: Positive integer read limit, no greater than MAX_BYTES.

    Returns:
        Bytes from a regular, singly linked file that passes read-time checks.

    Raises:
        EvidenceError: Capabilities are unavailable, inputs or file types are
            unsafe, the limit is exceeded, or the file changes during reading.
    """
    return get_backend().secure_read(root, relative, max_bytes)


def enumerate_files(root: Path | str) -> list[str]:
    """Inventory a directory recursively within the shared traversal bounds.

    Args:
        root: Existing absolute directory to inspect without modifying it.

    Returns:
        Sorted safe relative paths for regular, singly linked files. The list
        does not retain handles or guarantee that later reads see the same files.

    Raises:
        EvidenceError: Capabilities are unavailable, traversal is unsafe, bounds
            are exceeded, or a checked directory changes during traversal.
    """
    return get_backend().enumerate_files(root)


def read_json(path: Path | str, max_bytes: int = MAX_BYTES) -> object:
    """Securely read and parse JSON without validating a record schema.

    Args:
        path: JSON file path, made absolute by the backend.
        max_bytes: Positive integer read limit, no greater than MAX_BYTES.

    Returns:
        The parsed JSON value, not necessarily a dictionary.

    Raises:
        EvidenceError: Capability, secure-read, or JSON parsing checks fail.
    """
    return get_backend().read_json(path, max_bytes)


@dataclass(frozen=True)
class Attempt:
    """Immutable handle carrying an attempt's recorded directory identity.

    Freezing this handle does not freeze filesystem contents or grant approval
    to publish a candidate. The backend checks the stored identity when used.

    Args:
        path: Attempt directory path.
        workspace_id: Workspace identifier recorded when the attempt began.
        run_id: Run identifier recorded when the attempt began.
        attempt_id: Attempt identifier recorded when the attempt began.
        directory_identity: Recorded device/inode pair, not a live descriptor.
    """

    path: Path
    workspace_id: str
    run_id: str
    attempt_id: str
    directory_identity: tuple[int, int]

    def publish(self, artifacts: dict[str, dict], seal_metadata: dict) -> dict:
        """Install evidence artifacts without clobbering, then write the seal.

        This mutates the attempt directory under the backend's publisher lock.
        A failure may leave partial files for inspection; it is not a rollback
        transaction. Publication here is not a human approval or SAS proof.

        Args:
            artifacts: Allowed artifact filenames mapped to JSON dictionaries.
            seal_metadata: Seal fields consistent with the started attempt;
                artifact hashes are supplied by the backend.

        Returns:
            The completed seal dictionary with artifact hashes and identities.

        Raises:
            EvidenceError: Capabilities or record checks fail, directory identity
                changes, publication is busy/already sealed, or writes fail.
        """
        backend = get_backend()
        # Carry the recorded identity across the facade; do not rebind to the path.
        return backend.Attempt(
            self.path, self.workspace_id, self.run_id, self.attempt_id, self.directory_identity
        ).publish(artifacts, seal_metadata)


class AttemptStore:
    """Facade for an append-only local store kept separate from source roots.

    Construction may create store directories and records their identity. The
    backend owns filesystem resources and checks; this facade retains its store
    object, not an open descriptor or authority to bypass publication gates.

    Args:
        path: Absolute output directory to open or create.
        source_roots: Existing authorized source directories that must not overlap.

    Raises:
        EvidenceError: Capabilities, path safety, separation, or creation fail.
    """

    def __init__(self, path: Path | str, source_roots: list[Path] | tuple[Path, ...]) -> None:
        self._store = get_backend().AttemptStore(path, source_roots)

    @property
    def path(self) -> Path:
        """Return the recorded store path without accessing the filesystem."""
        return self._store.path

    @property
    def directory_identity(self) -> tuple[int, int]:
        """Return the recorded device/inode pair, without a fresh identity check."""
        return self._store.directory_identity

    def begin(self, workspace_id: str, run_id: str, attempt_id: str, metadata: dict) -> Attempt:
        """Reserve a new attempt directory and write its starting record.

        Existing attempt IDs are refused rather than reused. Failed creation can
        leave partial directories or files; callers must not treat them as sealed.

        Args:
            workspace_id: Safe workspace identifier.
            run_id: Safe run identifier.
            attempt_id: New safe attempt identifier within the run.
            metadata: JSON dictionary consistent with the starting identities.

        Returns:
            A handle carrying the newly recorded attempt directory identity.

        Raises:
            EvidenceError: Capabilities or metadata checks fail, the store identity
                changes, the attempt exists, or creation/publication fails.
        """
        # Recheck capabilities even though the backend store is already retained.
        require_evidence_io()
        attempt = self._store.begin(workspace_id, run_id, attempt_id, metadata)
        return Attempt(
            attempt.path,
            attempt.workspace_id,
            attempt.run_id,
            attempt.attempt_id,
            attempt.directory_identity,
        )

    def read_attempt(
        self, workspace_id: str, run_id: str, attempt_id: str
    ) -> tuple[dict[str, dict], dict]:
        """Read sealed records and check their identities, content set, and hashes.

        This is read-only integrity checking, not schema validation, authenticated
        provenance, human approval, or semantic acceptance.

        Args:
            workspace_id: Safe workspace identifier.
            run_id: Safe run identifier.
            attempt_id: Safe identifier of the sealed attempt to read.

        Returns:
            Artifact dictionaries (excluding the starting record) and the seal.

        Raises:
            EvidenceError: Capabilities or safe reads fail, the store identity
                changes, the attempt is incomplete, or seal/content checks fail.
        """
        require_evidence_io()
        return self._store.read_attempt(workspace_id, run_id, attempt_id)
