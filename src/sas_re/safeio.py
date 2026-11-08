"""Import-safe evidence API with a guarded, lazily selected filesystem backend.

Pure helpers preserve their original byte/validation rules. Every public I/O
entrypoint denies unsupported capabilities before touching caller paths.
"""

from dataclasses import dataclass
from pathlib import Path

from ._io_common import (ARTIFACT_NAMES, MAX_BYTES, MAX_FILES, MAX_DEPTH,
                         MAX_DIRECTORIES, EvidenceError, safe_relative,
                         canonical_bytes, _parse_json)
from .platform_io import get_backend, require_evidence_io


def require_safe_root(path: Path | str) -> Path:
    return get_backend().require_safe_root(path)


def ensure_disjoint(store: Path | str, source_roots: list[Path] | tuple[Path, ...]) -> None:
    return get_backend().ensure_disjoint(store, source_roots)


def secure_read(root: Path | str, relative: str, max_bytes: int = MAX_BYTES) -> bytes:
    return get_backend().secure_read(root, relative, max_bytes)


def enumerate_files(root: Path | str) -> list[str]:
    return get_backend().enumerate_files(root)


def read_json(path: Path | str, max_bytes: int = MAX_BYTES) -> object:
    return get_backend().read_json(path, max_bytes)


@dataclass(frozen=True)
class Attempt:
    path: Path
    workspace_id: str
    run_id: str
    attempt_id: str
    directory_identity: tuple[int, int]

    def publish(self, artifacts: dict[str, dict], seal_metadata: dict) -> dict:
        backend = get_backend()
        return backend.Attempt(self.path, self.workspace_id, self.run_id,
                               self.attempt_id, self.directory_identity).publish(artifacts, seal_metadata)


class AttemptStore:
    def __init__(self, path: Path | str, source_roots: list[Path] | tuple[Path, ...]) -> None:
        self._store = get_backend().AttemptStore(path, source_roots)

    @property
    def path(self) -> Path:
        return self._store.path

    @property
    def directory_identity(self) -> tuple[int, int]:
        return self._store.directory_identity

    def begin(self, workspace_id: str, run_id: str, attempt_id: str, metadata: dict) -> Attempt:
        require_evidence_io()
        attempt = self._store.begin(workspace_id, run_id, attempt_id, metadata)
        return Attempt(attempt.path, attempt.workspace_id, attempt.run_id,
                       attempt.attempt_id, attempt.directory_identity)

    def read_attempt(self, workspace_id: str, run_id: str, attempt_id: str) -> tuple[dict[str, dict], dict]:
        require_evidence_io()
        return self._store.read_attempt(workspace_id, run_id, attempt_id)
