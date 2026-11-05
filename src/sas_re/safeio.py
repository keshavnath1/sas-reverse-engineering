"""Bounded, read-only source access and append-only local evidence publication.

POSIX descriptor-relative operations prevent symlink traversal. Local filesystem
owners can still alter files or recompute hashes; this is integrity checking, not
authenticated provenance or a protection against a malicious operating system.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Iterator
import uuid


MAX_BYTES = 8 * 1024 * 1024
MAX_FILES = 1000
MAX_DEPTH = 32
MAX_DIRECTORIES = 1000
ARTIFACT_NAMES = frozenset({
    "source_inventory.json", "source_record.json", "validation_report.json",
    "verification_report.json",
})
_COMPONENT = re.compile(r"[A-Za-z0-9_.-]{1,128}\Z", re.ASCII)
_CODE = re.compile(r"[A-Z][A-Z0-9_]{0,79}\Z", re.ASCII)
_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
_READ_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC


class EvidenceError(Exception):
    """Public errors contain a fixed diagnostic code, never input contents."""

    def __init__(self, code: str, gate: str = "FAIL") -> None:
        self.code = code if isinstance(code, str) and _CODE.fullmatch(code) else "INVALID_ERROR_CODE"
        self.gate = gate if gate in {"FAIL", "BLOCKED"} else "FAIL"
        super().__init__(self.code)


def safe_relative(relative: str) -> str:
    """Validate a portable, unambiguous, POSIX-relative file or directory name."""
    if not isinstance(relative, str) or not relative or len(relative) > 4096:
        raise EvidenceError("UNSAFE_PATH")
    parts = relative.split("/")
    if any(part in {".", ".."} or not _COMPONENT.fullmatch(part) for part in parts):
        raise EvidenceError("UNSAFE_PATH")
    if len(parts) > MAX_DEPTH:
        raise EvidenceError("PATH_DEPTH_LIMIT")
    return relative


def _identifier(value: str) -> str:
    if safe_relative(value) != value or "/" in value:
        raise EvidenceError("UNSAFE_ID")
    return value


def _absolute(path: Path | str) -> Path:
    try:
        path = Path(path)
        text = str(path)
        text.encode("utf-8", errors="strict")
    except (TypeError, ValueError, UnicodeError):
        raise EvidenceError("UNSAFE_PATH") from None
    if len(text) > 4096 or any(ord(char) < 32 for char in text):
        raise EvidenceError("UNSAFE_PATH")
    if not path.is_absolute() or ".." in path.parts:
        raise EvidenceError("ABSOLUTE_ROOT_REQUIRED")
    return path


@contextmanager
def _directory(path: Path | str, *, create: bool = False) -> Iterator[int]:
    path = _absolute(path)
    fd = None
    try:
        fd = os.open("/", _DIR_FLAGS)
        for component in path.parts[1:]:
            if create:
                try:
                    os.mkdir(component, mode=0o700, dir_fd=fd)
                    os.fsync(fd)
                except FileExistsError:
                    pass
            next_fd = os.open(component, _DIR_FLAGS, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        yield fd
    except OSError as error:
        if error.errno == errno.ENOENT:
            raise EvidenceError("PATH_NOT_FOUND", "BLOCKED") from None
        raise EvidenceError("UNSAFE_OR_UNAVAILABLE_PATH") from None
    finally:
        if fd is not None:
            os.close(fd)


def require_safe_root(path: Path | str) -> Path:
    """Require an existing absolute directory with no symlink components."""
    path = _absolute(path)
    with _directory(path):
        pass
    return path


def ensure_disjoint(store: Path | str, source_roots: list[Path] | tuple[Path, ...]) -> None:
    """Disallow output equal to, inside, or containing an authorized source root."""
    store = _absolute(store)
    for root in source_roots:
        root = require_safe_root(root)
        if store == root or store in root.parents or root in store.parents:
            raise EvidenceError("OUTPUT_SOURCE_OVERLAP")


def _fingerprint(info: os.stat_result) -> tuple[int, ...]:
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_size,
            info.st_mtime_ns, info.st_ctime_ns)


def _names(fd: int, limit: int) -> list[str]:
    names = []
    with os.scandir(fd) as entries:
        for entry in entries:
            names.append(entry.name)
            if len(names) > limit:
                raise EvidenceError("INVENTORY_LIMIT")
    return sorted(names)


def _read_fd(parent: int, name: str, max_bytes: int) -> bytes:
    fd = None
    try:
        fd = os.open(name, _READ_FLAGS, dir_fd=parent)
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise EvidenceError("UNSAFE_FILE_TYPE")
        if before.st_size > max_bytes:
            raise EvidenceError("FILE_SIZE_LIMIT")
        chunks = []
        total = 0
        while True:
            chunk = os.read(fd, min(64 * 1024, max_bytes + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > max_bytes:
                raise EvidenceError("FILE_SIZE_LIMIT")
        after = os.fstat(fd)
        named = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if (_fingerprint(before) != _fingerprint(after)
                or _fingerprint(after) != _fingerprint(named) or total != after.st_size):
            raise EvidenceError("FILE_CHANGED_DURING_READ")
        return b"".join(chunks)
    except OSError as error:
        if error.errno == errno.ENOENT:
            raise EvidenceError("FILE_NOT_FOUND", "BLOCKED") from None
        raise EvidenceError("UNSAFE_OR_UNAVAILABLE_FILE") from None
    finally:
        if fd is not None:
            os.close(fd)


def secure_read(root: Path | str, relative: str, max_bytes: int = MAX_BYTES) -> bytes:
    """Read one regular, singly linked file without following any symlinks."""
    safe_relative(relative)
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or not 0 < max_bytes <= MAX_BYTES:
        raise EvidenceError("INVALID_READ_LIMIT")
    with _directory(root) as root_fd:
        parent = os.dup(root_fd)
        try:
            parts = relative.split("/")
            for component in parts[:-1]:
                next_fd = os.open(component, _DIR_FLAGS, dir_fd=parent)
                os.close(parent)
                parent = next_fd
            return _read_fd(parent, parts[-1], max_bytes)
        except OSError:
            raise EvidenceError("UNSAFE_OR_UNAVAILABLE_PATH") from None
        finally:
            os.close(parent)


def enumerate_files(root: Path | str) -> list[str]:
    """Bounded recursive inventory; reject unsafe names, links and special files."""
    files: list[str] = []
    directories = 0

    def visit(fd: int, prefix: str = "") -> None:
        nonlocal directories
        before = os.fstat(fd)
        names = _names(fd, MAX_FILES + MAX_DIRECTORIES)
        for name in names:
            relative = safe_relative(prefix + name)
            info = os.stat(name, dir_fd=fd, follow_symlinks=False)
            if stat.S_ISDIR(info.st_mode):
                directories += 1
                if directories > MAX_DIRECTORIES:
                    raise EvidenceError("INVENTORY_LIMIT")
                child = os.open(name, _DIR_FLAGS, dir_fd=fd)
                try:
                    if (info.st_dev, info.st_ino) != (os.fstat(child).st_dev, os.fstat(child).st_ino):
                        raise EvidenceError("DIRECTORY_CHANGED_DURING_READ")
                    visit(child, relative + "/")
                finally:
                    os.close(child)
            elif stat.S_ISREG(info.st_mode) and info.st_nlink == 1:
                files.append(relative)
                if len(files) > MAX_FILES:
                    raise EvidenceError("INVENTORY_LIMIT")
            else:
                raise EvidenceError("UNSAFE_FILE_TYPE")
        if _fingerprint(before) != _fingerprint(os.fstat(fd)):
            raise EvidenceError("DIRECTORY_CHANGED_DURING_READ")

    with _directory(root) as fd:
        visit(fd)
    return sorted(files)


def _json_depth(value: object, depth: int = 0) -> None:
    if depth > 64:
        raise EvidenceError("JSON_DEPTH_LIMIT")
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise EvidenceError("JSON_INVALID")
            _json_depth(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            _json_depth(child, depth + 1)


def canonical_bytes(obj: object) -> bytes:
    """Canonical local JSON policy: sorted compact UTF-8, finite numbers, final LF."""
    try:
        _json_depth(obj)
        return (json.dumps(obj, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise EvidenceError("JSON_INVALID") from None


def _parse_json(raw: bytes) -> object:
    def pairs(items: list[tuple[str, object]]) -> dict:
        result = {}
        for key, value in items:
            if key in result:
                raise EvidenceError("JSON_DUPLICATE_KEY")
            result[key] = value
        return result

    def nonfinite(_: str) -> None:
        raise EvidenceError("JSON_NONFINITE")

    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=nonfinite)
        _json_depth(value)
        # JSON's exponent syntax can overflow Python floats without parse_constant.
        canonical_bytes(value)
        return value
    except (ValueError, UnicodeError, RecursionError):
        raise EvidenceError("JSON_INVALID") from None


def read_json(path: Path | str, max_bytes: int = MAX_BYTES) -> object:
    path = Path(path).absolute()
    return _parse_json(secure_read(path.parent, path.name, max_bytes))


def _atomic_json(fd: int, name: str, payload: dict) -> bytes:
    raw = canonical_bytes(payload)
    if len(raw) > MAX_BYTES:
        raise EvidenceError("FILE_SIZE_LIMIT")
    temporary = "." + name + "." + uuid.uuid4().hex + ".tmp"
    out = None
    try:
        out = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                      0o600, dir_fd=fd)
        offset = 0
        while offset < len(raw):
            written = os.write(out, raw[offset:])
            if written <= 0:
                raise EvidenceError("PUBLICATION_IO_FAILURE", "BLOCKED")
            offset += written
        os.fchmod(out, 0o400)
        os.fsync(out)
        os.close(out)
        out = None
        # Linking installs atomically and, unlike rename(), cannot replace a file.
        os.link(temporary, name, src_dir_fd=fd, dst_dir_fd=fd, follow_symlinks=False)
        os.unlink(temporary, dir_fd=fd)
        os.fsync(fd)
        return raw
    except FileExistsError:
        raise EvidenceError("ARTIFACT_EXISTS", "BLOCKED") from None
    except OSError:
        raise EvidenceError("PUBLICATION_IO_FAILURE", "BLOCKED") from None
    finally:
        if out is not None:
            os.close(out)
        # Partial temporary files intentionally survive failures for inspection.


def _identity(info: os.stat_result) -> tuple[int, int]:
    return info.st_dev, info.st_ino


@dataclass(frozen=True)
class Attempt:
    path: Path
    workspace_id: str
    run_id: str
    attempt_id: str
    directory_identity: tuple[int, int]

    def publish(self, artifacts: dict[str, dict], seal_metadata: dict) -> dict:
        if not isinstance(artifacts, dict) or not artifacts or not artifacts.keys() <= ARTIFACT_NAMES:
            raise EvidenceError("INVALID_ARTIFACT_NAMES")
        if any(not isinstance(value, dict) for value in artifacts.values()):
            raise EvidenceError("INVALID_ARTIFACT_RECORD")
        if not isinstance(seal_metadata, dict) or "artifacts" in seal_metadata:
            raise EvidenceError("INVALID_SEAL_METADATA")
        identities = {"workspace_id": self.workspace_id, "run_id": self.run_id, "attempt_id": self.attempt_id}
        for key, value in identities.items():
            if key in seal_metadata and seal_metadata[key] != value:
                raise EvidenceError("ATTEMPT_IDENTITY_MISMATCH")
        if seal_metadata.get("publication_state", "COMPLETE") != "COMPLETE":
            raise EvidenceError("INVALID_SEAL_METADATA")
        canonical_bytes(seal_metadata)
        for value in artifacts.values():
            canonical_bytes(value)
        with _directory(self.path) as fd:
            if _identity(os.fstat(fd)) != self.directory_identity:
                raise EvidenceError("ATTEMPT_DIRECTORY_CHANGED")
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                raise EvidenceError("ATTEMPT_BUSY", "BLOCKED") from None
            try:
                names = set(_names(fd, 16))
                if "seal.json" in names:
                    raise EvidenceError("ATTEMPT_ALREADY_SEALED", "BLOCKED")
                if names != {"attempt.json"}:
                    raise EvidenceError("INCOMPLETE_ATTEMPT", "BLOCKED")
                started = _read_fd(fd, "attempt.json", MAX_BYTES)
                payload = _parse_json(started)
                if (not isinstance(payload, dict) or payload.get("publication_state") != "STARTED"
                        or any(payload.get(key) != value for key, value in identities.items())):
                    raise EvidenceError("ATTEMPT_IDENTITY_MISMATCH")
                for key in ("schema_version", "module_ids", "stage"):
                    if key in payload and payload[key] != seal_metadata.get(key):
                        raise EvidenceError("ATTEMPT_IDENTITY_MISMATCH")
                hashes = {"attempt.json": hashlib.sha256(started).hexdigest()}
                for name in sorted(artifacts):
                    hashes[name] = hashlib.sha256(_atomic_json(fd, name, artifacts[name])).hexdigest()
                seal = {**seal_metadata, **identities, "artifacts": hashes, "publication_state": "COMPLETE"}
                _atomic_json(fd, "seal.json", seal)
                return seal
            finally:
                fcntl.flock(fd, fcntl.LOCK_UN)


class AttemptStore:
    def __init__(self, path: Path | str, source_roots: list[Path] | tuple[Path, ...]) -> None:
        self.path = _absolute(path)
        ensure_disjoint(self.path, source_roots)
        with _directory(self.path, create=True) as fd:
            self.directory_identity = _identity(os.fstat(fd))

    def _ids(self, workspace_id: str, run_id: str, attempt_id: str) -> tuple[str, str, str]:
        return tuple(_identifier(value) for value in (workspace_id, run_id, attempt_id))

    def begin(self, workspace_id: str, run_id: str, attempt_id: str, metadata: dict) -> Attempt:
        ids = self._ids(workspace_id, run_id, attempt_id)
        identities = dict(zip(("workspace_id", "run_id", "attempt_id"), ids))
        if not isinstance(metadata, dict):
            raise EvidenceError("INVALID_ATTEMPT_METADATA")
        if any(key in metadata and metadata[key] != value for key, value in identities.items()):
            raise EvidenceError("ATTEMPT_IDENTITY_MISMATCH")
        if metadata.get("publication_state", "STARTED") != "STARTED":
            raise EvidenceError("INVALID_ATTEMPT_METADATA")
        started = {**metadata, **identities, "publication_state": "STARTED"}
        canonical_bytes(started)
        with _directory(self.path) as root_fd:
            if _identity(os.fstat(root_fd)) != self.directory_identity:
                raise EvidenceError("STORE_DIRECTORY_CHANGED")
            fd = os.dup(root_fd)
            try:
                for index, name in enumerate(ids):
                    try:
                        os.mkdir(name, mode=0o700, dir_fd=fd)
                        os.fsync(fd)
                    except FileExistsError:
                        if index == 2:
                            raise EvidenceError("ATTEMPT_EXISTS", "BLOCKED") from None
                    child = os.open(name, _DIR_FLAGS, dir_fd=fd)
                    os.close(fd)
                    fd = child
                identity = _identity(os.fstat(fd))
                _atomic_json(fd, "attempt.json", started)
            except OSError:
                raise EvidenceError("PUBLICATION_IO_FAILURE", "BLOCKED") from None
            finally:
                os.close(fd)
        return Attempt(self.path.joinpath(*ids), *ids, identity)

    def read_attempt(self, workspace_id: str, run_id: str, attempt_id: str) -> tuple[dict[str, dict], dict]:
        ids = self._ids(workspace_id, run_id, attempt_id)
        path = self.path.joinpath(*ids)
        identities = dict(zip(("workspace_id", "run_id", "attempt_id"), ids))
        with _directory(self.path) as root_fd:
            if _identity(os.fstat(root_fd)) != self.directory_identity:
                raise EvidenceError("STORE_DIRECTORY_CHANGED")
        with _directory(path) as fd:
            names = set(_names(fd, 16))
            if "seal.json" not in names:
                raise EvidenceError("INCOMPLETE_ATTEMPT", "BLOCKED")
            seal = _parse_json(_read_fd(fd, "seal.json", MAX_BYTES))
            if (not isinstance(seal, dict) or seal.get("publication_state") != "COMPLETE"
                    or any(seal.get(key) != value for key, value in identities.items())):
                raise EvidenceError("INVALID_SEAL")
            hashes = seal.get("artifacts")
            if (not isinstance(hashes, dict) or "attempt.json" not in hashes or len(hashes) < 2
                    or not hashes.keys() <= ARTIFACT_NAMES | {"attempt.json"}
                    or any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value)
                           for value in hashes.values())):
                raise EvidenceError("INVALID_SEAL")
            if names != set(hashes) | {"seal.json"}:
                raise EvidenceError("ATTEMPT_CONTENT_MISMATCH")
            artifacts = {}
            for name, expected in hashes.items():
                raw = _read_fd(fd, name, MAX_BYTES)
                if hashlib.sha256(raw).hexdigest() != expected:
                    raise EvidenceError("ARTIFACT_HASH_MISMATCH")
                record = _parse_json(raw)
                if not isinstance(record, dict):
                    raise EvidenceError("INVALID_ARTIFACT_RECORD")
                if name == "attempt.json":
                    if (record.get("publication_state") != "STARTED"
                            or any(record.get(key) != value for key, value in identities.items())):
                        raise EvidenceError("ATTEMPT_IDENTITY_MISMATCH")
                    for key in ("schema_version", "module_ids", "stage"):
                        if key in record and record[key] != seal.get(key):
                            raise EvidenceError("ATTEMPT_IDENTITY_MISMATCH")
                else:
                    artifacts[name] = record
            if set(_names(fd, 16)) != names:
                raise EvidenceError("ATTEMPT_CONTENT_MISMATCH")
            return artifacts, seal
