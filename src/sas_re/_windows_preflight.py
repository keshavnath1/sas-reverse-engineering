"""CP3B private retained-handle protocol. Native bootstrap is NOT implemented.

Only synthetic simulated adapters exercise this orchestration today. A caller
cannot obtain this session through the public API. A future separately reviewed
bootstrap must establish a qualified local NTFS volume handle and native security
qualification before wiring this protocol into public access. No paths/IDs here
are evidence artifacts or approval tokens.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Protocol

from ._authorization_paths import _comparison, _native_parts, _text
from ._io_common import (EvidenceError, MAX_BYTES, MAX_DEPTH, MAX_DIRECTORIES,
                         MAX_FILES, _parse_json, canonical_bytes)
from .authorization import authorization_scope_identity, validate_authorization
from .preflight import LocalInspectionPolicy, SOURCE_MODEL
from ._windows_native import DirectoryEntry, ObjectInfo, VolumeInfo

MAX_HANDLES = 4096
MAX_TOTAL_BYTES = 64 * 1024 * 1024
# Reparse, offline, recall-on-open/data-access: no hydration or namespace redirect.
_UNSAFE_ATTRIBUTES = 0x40 | 0x400 | 0x1000 | 0x10000 | 0x40000 | 0x400000
_DIRECTORY = 0x10


class _ReadAPI(Protocol):
    """Internal native seam. No pathname bootstrap or write method exists."""

    def open_child(self, parent_handle: int, name: str, *, directory: bool,
                   read_data: bool = False) -> int: ...
    def inspect(self, handle: int) -> ObjectInfo: ...
    def volume(self, handle: int) -> VolumeInfo: ...
    def entries(self, handle: int) -> tuple[DirectoryEntry, ...]: ...
    def read(self, handle: int, limit: int) -> bytes: ...
    def rewind(self, handle: int) -> None: ...
    def close(self, handle: int) -> None: ...


def _blocked(code):
    raise EvidenceError("CP3B_" + code, "BLOCKED")


def _request_windows(envelope, policy):
    """Pure invocation-scope consistency only; NOT physical authorization."""
    if type(policy) is not LocalInspectionPolicy:
        _blocked("POLICY_REQUIRED")
    validate_authorization(envelope, expected_platform="windows")
    detached = _parse_json(canonical_bytes(envelope))
    logical = detached["logical_scope"]
    if (any(type(getattr(policy, field)) is not str for field in (
            "anchor", "store_path", "workspace_id", "run_id", "scope_sha256", "source_model"))
            or type(policy.source_roots) is not tuple
            or any(type(item) is not tuple or len(item) != 2
                   or any(type(value) is not str for value in item) for item in policy.source_roots)):
        _blocked("POLICY_MISMATCH")
    expected = tuple(sorted((item["root_id"], item["path"]) for item in detached["bindings"]))
    if (tuple(sorted(policy.source_roots)) != expected
            or policy.workspace_id != logical["workspace_id"]
            or policy.run_id != logical["run_id"]
            or policy.scope_sha256 != authorization_scope_identity(detached)):
        _blocked("POLICY_MISMATCH")
    if policy.source_model != SOURCE_MODEL:
        _blocked("WRITER_POLICY_UNAVAILABLE")
    anchor = _native_parts("windows", policy.anchor)
    if len(anchor) > 64:
        _blocked("LIMIT")
    for path, source in [(path, True) for _, path in expected] + [(policy.store_path, False)]:
        parts = _native_parts("windows", path)
        if parts[:len(anchor)] != anchor or (source and len(parts) == len(anchor)):
            _blocked("OUTSIDE_ANCHOR")
        if len(parts) - len(anchor) > MAX_DEPTH:
            _blocked("LIMIT")
    return detached, anchor


def _binding(info):
    return info.identity, info.directory, info.attributes, info.creation_time


def _fingerprint(info):
    # Last-access time deliberately excluded: ordinary reads may update it.
    return (_binding(info), info.size, info.links, info.delete_pending,
            info.last_write_time, info.change_time, info.reparse_tag)


@dataclass
class _Directory:
    handle: int
    parent: _Directory | None
    name: str
    initial: ObjectInfo
    scoped: bool = True


@dataclass
class _File:
    parent: _Directory
    name: str
    initial: ObjectInfo
    metadata_handle: int
    read_handle: int | None = None


class WindowsPreflight:
    """Internal protocol consuming ownership of an already retained volume root.

    No native path bootstrap, public factory, backend override or approval flag.
    The adapter is an internal OS seam, not an externally supplied authorization
    service. Current executable coverage is simulation/unit-only.
    """

    def __init__(self, api: _ReadAPI, root_handle: int, envelope: object,
                 policy: LocalInspectionPolicy, anchor_parts: tuple[str, ...]):
        self._api = api
        self._handles = []
        self._state = "CLOSED"
        self._directories = []
        self._cache = {}
        self._memberships = []
        self._files = {}
        self._missing_store = None
        self._directory_count = 0
        self._volume = None
        self._serial = None
        try:
            self._track(root_handle)
            detached, expected_anchor = _request_windows(envelope, policy)
            if anchor_parts != expected_anchor:
                _blocked("POLICY_MISMATCH")
            self._scope = detached["logical_scope"]
            self._volume = self._api.volume(root_handle)
            # Necessary features only. This cannot prove locality or approve a
            # volume. That missing bootstrap guarantee keeps public I/O blocked.
            if (self._volume.filesystem != "NTFS" or self._volume.serial == 0
                    or self._volume.max_component_length != 255
                    or self._volume.flags & 0x8 == 0):  # FILE_PERSISTENT_ACLS
                _blocked("VOLUME_UNAVAILABLE")
            info = self._api.inspect(root_handle)
            self._serial = info.identity.volume_serial
            self._check(info, directory=True)
            root = _Directory(root_handle, None, "", info, False)
            self._directories.append(root)
            anchor = root
            for name in anchor_parts[1:]:  # Drive spelling is never opened.
                anchor = self._directory(anchor, name, scoped=False)
            self._anchor = anchor
            roots = {}
            for root_id, path in sorted(policy.source_roots):
                roots[root_id] = self._walk(anchor, _native_parts("windows", path)[len(anchor_parts):])
            source_ids = {item.initial.identity for item in roots.values()}
            store = self._walk(anchor, _native_parts("windows", policy.store_path)[len(anchor_parts):],
                               allow_missing=True, forbidden=source_ids)
            self._disjoint(roots, store)
            for root_id, directory in roots.items():
                trie = {}
                for item in self._scope["files"]:
                    if item["root_id"] != root_id:
                        continue
                    node = trie
                    parts = item["path"].split("/")
                    for part in parts[:-1]:
                        node = node.setdefault(part, {})
                    node[parts[-1]] = item["file_key"]
                self._inspect(directory, trie, 0)
            if len(self._files) != len(self._scope["files"]):
                _blocked("MEMBERSHIP_CHANGED")
            if sum(item.initial.size for item in self._files.values()) > MAX_TOTAL_BYTES:
                _blocked("LIMIT")
            self._recheck()  # All metadata and memberships before data opens.
            for key, item in sorted(self._files.items()):
                item.read_handle = self._track(self._api.open_child(
                    item.parent.handle, item.name, directory=False, read_data=True))
                self._verify(item.read_handle, item.initial, directory=False)
            self._recheck()  # Every data handle held before READY, still zero reads.
            self._state = "READY"
        except BaseException as error:
            self.close()
            if isinstance(error, OSError):
                _blocked("ACCESS_UNAVAILABLE")
            raise

    @property
    def state(self):
        return self._state

    def _track(self, handle):
        if type(handle) is not int or handle <= 0 or handle in self._handles:
            _blocked("HANDLE_UNAVAILABLE")
        self._handles.append(handle)
        if len(self._handles) > MAX_HANDLES:
            _blocked("LIMIT")
        return handle

    def _check(self, info, *, directory):
        if (info.directory is not directory or info.attributes & _UNSAFE_ATTRIBUTES
                or bool(info.attributes & _DIRECTORY) != directory or info.reparse_tag
                or info.delete_pending or info.identity.volume_serial == 0
                or info.identity.volume_serial != self._serial
                or type(info.identity.file_id) is not bytes or len(info.identity.file_id) != 16
                or not any(info.identity.file_id)):
            _blocked("UNSAFE_OBJECT")
        if not directory and (info.links != 1 or not 0 <= info.size <= MAX_BYTES):
            _blocked("UNSAFE_FILE")

    def _verify(self, handle, initial, *, directory, full=True):
        current = self._api.inspect(handle)
        self._check(current, directory=directory)
        if self._api.volume(handle) != self._volume:
            _blocked("VOLUME_CHANGED")
        compare = _fingerprint if full else _binding
        if compare(current) != compare(initial):
            _blocked("BINDING_CHANGED")
        return current

    def _entries(self, directory):
        result, aliases = {}, set()
        entries = self._api.entries(directory.handle)
        if len(entries) > MAX_FILES + MAX_DIRECTORIES:
            _blocked("LIMIT")
        for entry in entries:
            try:
                _text(entry.name)
                if (entry.name in {".", ".."} or any(char in entry.name for char in "\\/\x00")
                        or len(entry.name.encode("utf-16-le")) > 510):
                    _blocked("NAME_UNAVAILABLE")
            except EvidenceError:
                _blocked("NAME_UNAVAILABLE")
            comparison = _comparison(entry.name)
            if entry.name in result or comparison in aliases:
                _blocked("NAME_AMBIGUOUS")
            if (type(entry.file_id) is not bytes or len(entry.file_id) != 16
                    or not any(entry.file_id)):
                _blocked("UNSAFE_ENTRY")
            result[entry.name] = entry
            aliases.add(comparison)
        return result

    def _named(self, parent, name):
        # Exact long name required; no DOS short-name/case/normalization lookup.
        entry = self._entries(parent).get(name)
        if entry is None:
            _blocked("BINDING_CHANGED")
        if entry.attributes & _UNSAFE_ATTRIBUTES or entry.reparse_tag:
            _blocked("UNSAFE_ENTRY")
        return entry

    def _entry_matches(self, entry, info):
        if (entry.file_id != info.identity.file_id or entry.attributes != info.attributes
                or (not info.directory and entry.size != info.size)):
            _blocked("BINDING_CHANGED")

    def _directory(self, parent, name, *, scoped=True):
        entry = self._named(parent, name) if scoped else None
        if entry is not None and not entry.attributes & _DIRECTORY:
            _blocked("UNSAFE_OBJECT")
        key = parent.handle, name
        if key in self._cache:
            directory = self._cache[key]
            current = self._verify(directory.handle, directory.initial, directory=True, full=False)
            if entry is not None:
                self._entry_matches(entry, current)
            return directory
        handle = self._track(self._api.open_child(parent.handle, name, directory=True))
        info = self._api.inspect(handle)
        self._check(info, directory=True)
        if self._api.volume(handle) != self._volume:
            _blocked("VOLUME_CHANGED")
        if entry is not None:
            self._entry_matches(entry, info)
        directory = _Directory(handle, parent, name, info, scoped)
        self._directories.append(directory)
        self._cache[key] = directory
        return directory

    def _walk(self, anchor, parts, allow_missing=False, forbidden=frozenset()):
        current = anchor
        for name in parts:
            if current.initial.identity in forbidden:
                _blocked("STORE_OVERLAP")
            entries = self._entries(current)
            if name not in entries:
                if not allow_missing:
                    _blocked("BINDING_CHANGED")
                if any(_comparison(name) == _comparison(other) for other in entries):
                    _blocked("NAME_AMBIGUOUS")
                # String absence does not prove NTFS lookup absence (DOS names,
                # collation and namespace aliases). No approved absence proof
                # exists yet. Require an existing disjoint store for this subset.
                _blocked("STORE_ABSENCE_UNPROVEN")
            current = self._directory(current, name)
        return current

    def _ancestry(self, directory):
        result = set()
        while True:
            result.add(directory.initial.identity)
            if directory is self._anchor:
                return result
            directory = directory.parent

    def _disjoint(self, roots, store):
        entries = list(roots.values())
        for index, left in enumerate(entries):
            for right in entries[index + 1:]:
                if (left.initial.identity in self._ancestry(right)
                        or right.initial.identity in self._ancestry(left)):
                    _blocked("SOURCE_OVERLAP")
            if (left.initial.identity in self._ancestry(store)
                    or (self._missing_store is None and store.initial.identity in self._ancestry(left))):
                _blocked("STORE_OVERLAP")

    def _inspect(self, directory, trie, depth):
        if depth > MAX_DEPTH:
            _blocked("LIMIT")
        before = self._api.inspect(directory.handle)
        entries = self._entries(directory)
        if set(entries) != set(trie):
            _blocked("MEMBERSHIP_CHANGED")
        self._memberships.append((directory, frozenset(trie), _fingerprint(before)))
        for name, child in sorted(trie.items()):
            if type(child) is dict:
                self._directory_count += 1
                if self._directory_count > MAX_DIRECTORIES:
                    _blocked("LIMIT")
                self._inspect(self._directory(directory, name), child, depth + 1)
            else:
                if child in self._files or len(self._files) >= MAX_FILES:
                    _blocked("LIMIT")
                handle = self._track(self._api.open_child(directory.handle, name, directory=False))
                info = self._api.inspect(handle)
                self._check(info, directory=False)
                if self._api.volume(handle) != self._volume:
                    _blocked("VOLUME_CHANGED")
                self._entry_matches(entries[name], info)
                if any(item.initial.identity == info.identity for item in self._files.values()):
                    _blocked("FILE_ALIAS")
                self._files[child] = _File(directory, name, info, handle)

    def _recheck(self):
        for directory in self._directories:
            current = self._verify(directory.handle, directory.initial, directory=True, full=False)
            if directory.parent is not None:
                if directory.scoped:
                    self._entry_matches(self._named(directory.parent, directory.name), current)
                else:
                    # Do not enumerate unrelated siblings outside the anchor.
                    probe = self._track(self._api.open_child(directory.parent.handle,
                                            directory.name, directory=True))
                    try:
                        self._verify(probe, directory.initial, directory=True, full=False)
                    finally:
                        self._handles.remove(probe)
                        self._api.close(probe)
        if self._missing_store:
            parent, name = self._missing_store
            if name in self._entries(parent):
                _blocked("BINDING_CHANGED")
        for directory, names, fingerprint in self._memberships:
            if (set(self._entries(directory)) != names
                    or _fingerprint(self._api.inspect(directory.handle)) != fingerprint):
                _blocked("MEMBERSHIP_CHANGED")
        for item in self._files.values():
            info = self._verify(item.metadata_handle, item.initial, directory=False)
            self._entry_matches(self._named(item.parent, item.name), info)
            if item.read_handle is not None:
                self._verify(item.read_handle, item.initial, directory=False)

    def _read(self, item):
        self._api.rewind(item.read_handle)
        chunks, total = [], 0
        while True:
            limit = min(64 * 1024, MAX_BYTES + 1 - total)
            chunk = self._api.read(item.read_handle, limit)
            if type(chunk) is not bytes or len(chunk) > limit:
                _blocked("READ_UNAVAILABLE")
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > MAX_BYTES:
                _blocked("LIMIT")
        self._verify(item.read_handle, item.initial, directory=False)
        if total != item.initial.size:
            _blocked("SOURCE_CHANGED")
        return b"".join(chunks)

    def read_sources(self):
        try:
            if self._state != "READY":
                _blocked("SESSION_CLOSED")
            self._state = "READING"
            self._recheck()
            result = {}
            for key, item in sorted(self._files.items()):
                self._recheck()
                result[key] = self._read(item)
            self._recheck()
            for key, item in sorted(self._files.items()):
                self._recheck()
                if hashlib.sha256(self._read(item)).digest() != hashlib.sha256(result[key]).digest():
                    _blocked("SOURCE_CHANGED")
            self._recheck()
            return result
        except OSError:
            _blocked("ACCESS_UNAVAILABLE")
        finally:
            self.close()

    def close(self):
        self._state = "CLOSED"
        uncertain = False
        while self._handles:
            try:
                self._api.close(self._handles.pop())
            except BaseException:
                # Exhaust ownership even on wrapper failure or cancellation.
                uncertain = True
        if uncertain:
            _blocked("CLOSE_UNCERTAIN")

    def __enter__(self):
        if self._state != "READY":
            _blocked("SESSION_CLOSED")
        return self

    def __exit__(self, *_):
        self.close()
