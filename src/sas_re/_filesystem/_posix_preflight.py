"""CP3A retained POSIX handles; no writes, publication or path-based source reopen.

Internal implementation. A trusted/quiescent owner model is required; repeat
checks detect relevant changes but do not provide an atomic hostile-writer snapshot.
"""

from dataclasses import dataclass
import hashlib
import os
import stat

from .._io_common import EvidenceError, MAX_BYTES, MAX_FILES, MAX_DIRECTORIES, MAX_DEPTH
from ._posix_filesystem import filesystem_identity
from ..platform_io import require_evidence_io


_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
_READ_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
MAX_HANDLES = 4096
MAX_TOTAL_BYTES = 64 * 1024 * 1024


def _identity(info):
    return info.st_dev, info.st_ino


def _binding(info):
    return info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid


def _fingerprint(info):
    return (*_binding(info), info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _owned(info):
    # These are minimum mode/ownership checks, not a full ACL/authentication audit.
    # Other effective writers (including ACL grants) remain explicitly trusted.
    if info.st_uid != os.geteuid() or info.st_mode & 0o022:
        raise EvidenceError("CP3A_OWNER_POLICY_UNAVAILABLE", "BLOCKED")


@dataclass
class _Directory:
    fd: int
    parent: object
    name: str
    initial: object
    qualified: bool


@dataclass
class _File:
    parent: _Directory
    name: str
    initial: object
    fd: int | None = None


class PosixPreflight:
    def __init__(self, envelope, policy, anchor_parts):
        self._state = "CLOSED"
        self._fds = []
        self._directories = []
        self._cache = {}
        self._memberships = []
        self._files = {}
        self._missing_store = None
        self._filesystem = None
        self._directory_count = 0
        self._scope = envelope["logical_scope"]
        try:
            rootfd = self._track(os.open("/", _DIR_FLAGS))
            root = _Directory(rootfd, None, "", os.fstat(rootfd), False)
            self._directories.append(root)
            anchor = root
            for name in anchor_parts:
                anchor = self._directory(anchor, name, qualified=False)
            _owned(os.fstat(anchor.fd))
            self._filesystem = filesystem_identity(anchor.fd)
            self._anchor = anchor
            # An existing dedicated anchor is the physical containment boundary.
            # No mount transition is allowed inside it; bootstrap may cross the
            # normal macOS system/data layout before the anchor is established.
            roots = {}
            for root_id, path in sorted(policy.source_roots):
                parts = tuple(path[1:].split("/"))[len(anchor_parts) :]
                roots[root_id] = self._walk(anchor, parts)
            store_parts = tuple(policy.store_path[1:].split("/"))[len(anchor_parts) :]
            source_ids = {_identity(item.initial) for item in roots.values()}
            store = self._walk(anchor, store_parts, allow_missing=True, forbidden=source_ids)
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
                raise EvidenceError("CP3A_MEMBERSHIP_CHANGED", "BLOCKED")
            self._recheck()  # Global Q2: no source data handles opened yet.
            total = sum(item.initial.st_size for item in self._files.values())
            if total > MAX_TOTAL_BYTES:
                raise EvidenceError("CP3A_LIMIT", "BLOCKED")
            # Q2R: finish EVERY acquisition before any source-content read.
            for key in sorted(self._files):
                item = self._files[key]
                item.fd = self._track(os.open(item.name, _READ_FLAGS, dir_fd=item.parent.fd))
                current = os.fstat(item.fd)
                self._regular(current)
                self._same_filesystem(item.fd)
                if _fingerprint(current) != _fingerprint(item.initial):
                    raise EvidenceError("CP3A_BINDING_CHANGED", "BLOCKED")
            self._recheck()
            self._state = "READY"
        except BaseException as error:
            self.close()
            if isinstance(error, OSError):
                raise EvidenceError("CP3A_ACCESS_UNAVAILABLE", "BLOCKED") from None
            raise

    @property
    def state(self):
        return self._state

    def _track(self, fd):
        self._fds.append(fd)
        if len(self._fds) > MAX_HANDLES:
            raise EvidenceError("CP3A_LIMIT", "BLOCKED")
        if os.get_inheritable(fd):
            raise EvidenceError("CP3A_DESCRIPTOR_UNAVAILABLE", "BLOCKED")
        return fd

    def _same_filesystem(self, fd):
        if filesystem_identity(fd) != self._filesystem:
            raise EvidenceError("CP3A_FILESYSTEM_BOUNDARY", "BLOCKED")

    def _directory(self, parent, name, *, qualified=True):
        key = parent.fd, name
        before = os.stat(name, dir_fd=parent.fd, follow_symlinks=False)
        if not stat.S_ISDIR(before.st_mode):
            raise EvidenceError("CP3A_UNSAFE_TYPE")
        if key in self._cache:
            directory = self._cache[key]
            if _binding(before) != _binding(directory.initial):
                raise EvidenceError("CP3A_BINDING_CHANGED", "BLOCKED")
            return directory
        fd = self._track(os.open(name, _DIR_FLAGS, dir_fd=parent.fd))
        after = os.fstat(fd)
        if _binding(before) != _binding(after):
            raise EvidenceError("CP3A_BINDING_CHANGED", "BLOCKED")
        if qualified:
            _owned(after)
            self._same_filesystem(fd)
        directory = _Directory(fd, parent, name, after, qualified)
        self._directories.append(directory)
        self._cache[key] = directory
        return directory

    def _walk(self, anchor, parts, allow_missing=False, forbidden=frozenset()):
        current = anchor
        for index, name in enumerate(parts):
            if _identity(current.initial) in forbidden:
                # Do not descend into a source tree while inspecting an invalid
                # output target, including an alias spelling of that root.
                raise EvidenceError("CP3A_STORE_OVERLAP")
            try:
                current = self._directory(current, name)
            except FileNotFoundError:
                if not allow_missing:
                    raise
                self._missing_store = (current, name, parts[index:])
                return current
        return current

    def _ancestry(self, directory):
        result = set()
        while True:
            result.add(_identity(directory.initial))
            if directory is self._anchor:
                return result
            directory = directory.parent

    def _disjoint(self, roots, store):
        entries = list(roots.values())
        for index, left in enumerate(entries):
            for right in entries[index + 1 :]:
                if _identity(left.initial) in self._ancestry(right) or _identity(
                    right.initial
                ) in self._ancestry(left):
                    raise EvidenceError("CP3A_SOURCE_OVERLAP")
            if _identity(left.initial) in self._ancestry(store) or (
                self._missing_store is None and _identity(store.initial) in self._ancestry(left)
            ):
                raise EvidenceError("CP3A_STORE_OVERLAP")

    def _names(self, directory):
        names = []
        with os.scandir(directory.fd) as iterator:
            for entry in iterator:
                names.append(entry.name)
                if len(names) > MAX_FILES + MAX_DIRECTORIES:
                    raise EvidenceError("CP3A_LIMIT", "BLOCKED")
        if len(set(names)) != len(names):
            raise EvidenceError("CP3A_MEMBERSHIP_CHANGED", "BLOCKED")
        return set(names)

    def _regular(self, info):
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise EvidenceError("CP3A_UNSAFE_TYPE")
        _owned(info)
        if not 0 <= info.st_size <= MAX_BYTES:
            raise EvidenceError("CP3A_LIMIT", "BLOCKED")

    def _inspect(self, directory, trie, depth):
        if depth > MAX_DEPTH:
            raise EvidenceError("CP3A_LIMIT", "BLOCKED")
        before = os.fstat(directory.fd)
        # Compare the COMPLETE list before descending, including empty/hidden dirs.
        if self._names(directory) != set(trie):
            raise EvidenceError("CP3A_MEMBERSHIP_CHANGED", "BLOCKED")
        self._memberships.append((directory, frozenset(trie), _fingerprint(before)))
        for name, child in sorted(trie.items()):
            info = os.stat(name, dir_fd=directory.fd, follow_symlinks=False)
            if type(child) is dict:
                self._directory_count += 1
                if self._directory_count > MAX_DIRECTORIES:
                    raise EvidenceError("CP3A_LIMIT", "BLOCKED")
                self._inspect(self._directory(directory, name), child, depth + 1)
            else:
                self._regular(info)
                if child in self._files or len(self._files) >= MAX_FILES:
                    raise EvidenceError("CP3A_LIMIT", "BLOCKED")
                self._files[child] = _File(directory, name, info)

    def _recheck(self):
        # Check namespace bindings, not just retained objects. No source pathname
        # is reopened; stat is relative to the retained, verified parent handle.
        for directory in self._directories:
            current = os.fstat(directory.fd)
            if _binding(current) != _binding(directory.initial):
                raise EvidenceError("CP3A_BINDING_CHANGED", "BLOCKED")
            if directory.parent is not None:
                named = os.stat(directory.name, dir_fd=directory.parent.fd, follow_symlinks=False)
                if _binding(named) != _binding(current):
                    raise EvidenceError("CP3A_BINDING_CHANGED", "BLOCKED")
            if directory.qualified or directory is self._anchor:
                _owned(current)
                self._same_filesystem(directory.fd)
        if self._missing_store:
            parent, name, _ = self._missing_store
            try:
                os.stat(name, dir_fd=parent.fd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                raise EvidenceError("CP3A_BINDING_CHANGED", "BLOCKED")
        for directory, names, before in self._memberships:
            if self._names(directory) != names or _fingerprint(os.fstat(directory.fd)) != before:
                raise EvidenceError("CP3A_MEMBERSHIP_CHANGED", "BLOCKED")
        for item in self._files.values():
            named = os.stat(item.name, dir_fd=item.parent.fd, follow_symlinks=False)
            if _fingerprint(named) != _fingerprint(item.initial):
                raise EvidenceError("CP3A_BINDING_CHANGED", "BLOCKED")
            if item.fd is not None:
                if _fingerprint(os.fstat(item.fd)) != _fingerprint(item.initial):
                    raise EvidenceError("CP3A_SOURCE_CHANGED", "BLOCKED")
                self._same_filesystem(item.fd)

    def _read(self, item):
        os.lseek(item.fd, 0, os.SEEK_SET)
        chunks = []
        total = 0
        while True:
            chunk = os.read(item.fd, min(64 * 1024, MAX_BYTES + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > MAX_BYTES:
                raise EvidenceError("CP3A_LIMIT", "BLOCKED")
        if total != item.initial.st_size or _fingerprint(os.fstat(item.fd)) != _fingerprint(
            item.initial
        ):
            raise EvidenceError("CP3A_SOURCE_CHANGED", "BLOCKED")
        return b"".join(chunks)

    def read_sources(self):
        """Return all original bytes only after two passes and final rechecks.

        Single use; closes on success/failure. Returned data is not a permission
        receipt or sealed evidence. No encoding/newline normalization is applied.
        """
        try:
            require_evidence_io()
            if self._state != "READY":
                raise EvidenceError("CP3A_SESSION_CLOSED", "BLOCKED")
            self._state = "READING"
            self._recheck()
            result = {}
            total = 0
            for key, item in sorted(self._files.items()):
                self._recheck()
                raw = self._read(item)
                total += len(raw)
                if total > MAX_TOTAL_BYTES:
                    raise EvidenceError("CP3A_LIMIT", "BLOCKED")
                result[key] = raw
            self._recheck()
            for key, item in sorted(self._files.items()):
                self._recheck()
                if (
                    hashlib.sha256(self._read(item)).digest()
                    != hashlib.sha256(result[key]).digest()
                ):
                    raise EvidenceError("CP3A_SOURCE_CHANGED", "BLOCKED")
            self._recheck()
            return result
        except OSError:
            raise EvidenceError("CP3A_ACCESS_UNAVAILABLE", "BLOCKED") from None
        finally:
            self.close()

    def close(self):
        self._state = "CLOSED"
        # A failed close must not prevent releasing every other retained handle.
        # Never retry an ambiguous POSIX close: the fd number may be reused.
        uncertain = False
        while self._fds:
            try:
                os.close(self._fds.pop())
            except OSError:
                uncertain = True
        if uncertain:
            raise EvidenceError("CP3A_CLOSE_UNCERTAIN", "BLOCKED")

    def __enter__(self):
        if self._state != "READY":
            raise EvidenceError("CP3A_SESSION_CLOSED", "BLOCKED")
        return self

    def __exit__(self, *_):
        self.close()
