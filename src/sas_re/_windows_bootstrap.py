"""Private CP3D metadata protocol; native acquisition remains BLOCKED.

Expectation records are independently supplied comparison data, NOT approvals.
Only simulated adapters currently implement this complete seam. No public factory,
reader integration, serialized receipt, file-data operation or creation exists.
"""

from dataclasses import dataclass
from enum import Enum
import re
from typing import Protocol

from ._io_common import EvidenceError
from ._windows_native import ObjectIdentity, ObjectInfo, VolumeInfo, _component
from ._windows_preflight import _request_windows, _fingerprint
from ._windows_bootstrap_native import DeviceInfo
from ._authorization_paths import _native_parts

NAME_NOT_FOUND = 0xC0000034
MAX_MAPPING_OBSERVATIONS = 8
MAX_DIRECTORIES = 128
_UNSAFE = 0x40 | 0x400 | 0x1000 | 0x10000 | 0x40000 | 0x400000


def _blocked(code):
    raise EvidenceError("CP3D_" + code, "BLOCKED")


class LookupKind(Enum):
    PRESENT = "PRESENT"
    NAME_NOT_FOUND = "CANDIDATE_NAME_NOT_FOUND"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class LookupResult:
    kind: LookupKind
    raw_status: int
    handle: int | None = None
    long_name: str | None = None


def classify_lookup(status: int) -> LookupKind:
    """Pure status decoder, not completion/ownership handling or absence proof.

    A future native adapter must first establish completion and retain all native
    buffers until then. Error IOSB values need not equal the routine's status.
    This function never calls an API and cannot discharge that obligation.
    """
    if type(status) is not int or not -(1 << 31) <= status <= 0xffffffff:
        return LookupKind.BLOCKED
    unsigned = status & 0xffffffff
    if unsigned == 0:
        return LookupKind.PRESENT
    if unsigned == NAME_NOT_FOUND:
        return LookupKind.NAME_NOT_FOUND
    return LookupKind.BLOCKED


@dataclass(frozen=True)
class HostContext:
    host_reference: str
    token_reference: str


@dataclass(frozen=True)
class HostVolumeExpectations:
    context: HostContext
    inspection_reference: str
    backing_reference: str
    root_locator: str
    mapping_name: str
    mapping_targets: tuple[str, ...]
    root_identity: ObjectIdentity
    volume: VolumeInfo
    device: DeviceInfo


@dataclass(frozen=True)
class DirectoryExpectation:
    components: tuple[str, ...]
    identity: ObjectIdentity


@dataclass(frozen=True)
class MetadataExpectations:
    volume: HostVolumeExpectations
    directories: tuple[DirectoryExpectation, ...]
    store_parent: tuple[str, ...]


@dataclass(frozen=True)
class AbsenceObservation:
    """Transient observation only; not authorization, reservation or a token."""
    parent_identity: ObjectIdentity
    missing_component: str
    remaining_suffix: tuple[str, ...]


class _MetadataAPI(Protocol):
    def context(self) -> HostContext: ...
    def mappings(self, name: str) -> tuple[str, ...]: ...
    def open_root(self, locator: str) -> int: ...
    def inspect(self, handle: int) -> ObjectInfo: ...
    def volume(self, handle: int) -> VolumeInfo: ...
    def device(self, handle: int) -> DeviceInfo: ...
    def case_sensitive(self, handle: int) -> bool: ...
    def lookup(self, parent: int, name: str) -> LookupResult: ...
    def close(self, handle: int) -> None: ...


def _identity(value):
    return (type(value) is ObjectIdentity and type(value.volume_serial) is int
            and 0 < value.volume_serial < 1 << 64 and type(value.file_id) is bytes
            and len(value.file_id) == 16 and any(value.file_id))


def _reference(value):
    return (type(value) is str and 1 <= len(value) <= 256
            and value == value.strip() and all(ord(c) >= 32 for c in value))


def _context(value):
    return (type(value) is HostContext and _reference(value.host_reference)
            and _reference(value.token_reference))


def _volume(value):
    return (type(value) is VolumeInfo and type(value.filesystem) is str
            and value.filesystem == "NTFS" and type(value.serial) is int
            and 0 < value.serial < 1 << 32 and type(value.max_component_length) is int
            and value.max_component_length == 255 and type(value.flags) is int
            and 0 <= value.flags < 1 << 32 and bool(value.flags & 8))


def _device(value):
    return (type(value) is DeviceInfo and type(value.device_type) is int
            and value.device_type == 7 and type(value.characteristics) is int
            and value.characteristics in (0, 0x20))


def _parts(value):
    if type(value) is not tuple or len(value) > 64:
        _blocked("EXPECTATIONS_INVALID")
    for component in value:
        _component(component)
    return value


def _validate(envelope, policy, expected):
    # Reuse CP2 and CP3B pure scope/policy checks. Native strings grant no rights.
    _, anchor = _request_windows(envelope, policy)
    if type(expected) is not MetadataExpectations or type(expected.volume) is not HostVolumeExpectations:
        _blocked("EXPECTATIONS_REQUIRED")
    volume = expected.volume
    if (not _context(volume.context)
            or not all(_reference(item) for item in (
                volume.context.host_reference, volume.context.token_reference,
                volume.inspection_reference, volume.backing_reference))
            or type(volume.root_locator) is not str
            or re.fullmatch(r"\\Device\\HarddiskVolume[1-9][0-9]{0,5}\\", volume.root_locator) is None
            or type(volume.mapping_name) is not str
            or volume.mapping_name != anchor[0]
            or re.fullmatch(r"[A-Z]:", volume.mapping_name) is None
            or type(volume.mapping_targets) is not tuple
            or not 1 <= len(volume.mapping_targets) <= 128
            or any(type(target) is not str or target != volume.root_locator[:-1]
                   for target in volume.mapping_targets)
            or len(set(volume.mapping_targets)) != len(volume.mapping_targets)
            or not _identity(volume.root_identity)):
        _blocked("EXPECTATIONS_INVALID")
    v, device = volume.volume, volume.device
    if not _volume(v) or not _device(device):
        _blocked("VOLUME_EXPECTATIONS_UNSUPPORTED")
    if type(expected.directories) is not tuple or not 1 <= len(expected.directories) <= MAX_DIRECTORIES:
        _blocked("EXPECTATIONS_INVALID")
    directories, identities = {}, {volume.root_identity}
    for item in expected.directories:
        if type(item) is not DirectoryExpectation or not _identity(item.identity):
            _blocked("EXPECTATIONS_INVALID")
        parts = _parts(item.components)
        if (not parts or parts in directories or item.identity in identities
                or item.identity.volume_serial != volume.root_identity.volume_serial):
            _blocked("EXPECTATIONS_AMBIGUOUS")
        directories[parts] = item.identity
        identities.add(item.identity)
    store_parts = _native_parts("windows", policy.store_path)[1:]
    parent = _parts(expected.store_parent)
    if len(parent) >= len(store_parts) or store_parts[:len(parent)] != parent:
        _blocked("STORE_SCOPE_MISMATCH")
    anchor_parts = anchor[1:]
    if parent[:len(anchor_parts)] != anchor_parts:
        _blocked("STORE_SCOPE_MISMATCH")
    source_parts = tuple(_native_parts("windows", path)[1:] for _, path in policy.source_roots)
    required = set()
    for parts in (*source_parts, parent):
        required.update(parts[:index] for index in range(1, len(parts) + 1))
    if set(directories) != required:
        _blocked("DIRECTORY_SCOPE_MISMATCH")
    # Logical aliases/nesting rejected before I/O; physical identities rechecked.
    for left in source_parts:
        if parent[:len(left)] == left:
            _blocked("STORE_OVERLAP")
        for right in source_parts:
            if left != right and right[:len(left)] == left:
                _blocked("SOURCE_OVERLAP")
    return directories, source_parts, store_parts


class MetadataSession:
    """Owns metadata handles from a private seam; no transfer to a source reader.

    The native implementation refuses acquisition. A matching simulated context
    or expectation record is not approval/authentication or Windows qualification.
    Quiescent trusted namespace writers are required; checks cannot rule out ABA.
    """

    def __init__(self, api: _MetadataAPI, envelope, policy, expected: MetadataExpectations):
        self._api = api
        self._handles = []
        self._nodes = {}
        self._state = "CLOSED"
        self._mapping_calls = 0
        self._observation = None
        directories, self._sources, self._store = _validate(envelope, policy, expected)
        self._expected = expected
        try:
            self._mapping()
            root = self._track(api.open_root(expected.volume.root_locator))
            self._nodes[()] = (root, self._inspect(root, expected.volume.root_identity))
            for parts in sorted(directories, key=lambda item: (len(item), item)):
                parent = self._nodes[parts[:-1]][0]
                result = self._lookup(parent, parts[-1])
                if result.kind is not LookupKind.PRESENT or result.long_name != parts[-1]:
                    _blocked("PARENT_BINDING_UNAVAILABLE")
                info = self._inspect(result.handle, directories[parts])
                self._nodes[parts] = (result.handle, info)
            self._state = "BOUND"
            self._recheck_bindings()
        except BaseException as error:
            self.close()
            if isinstance(error, OSError):
                _blocked("METADATA_UNAVAILABLE")
            raise

    @property
    def state(self):
        return self._state

    def _track(self, handle):
        if type(handle) is not int or not 0 < handle < (1 << 64) - 1 or handle in self._handles:
            _blocked("HANDLE_UNAVAILABLE")
        self._handles.append(handle)
        if len(self._handles) > MAX_DIRECTORIES + 2:
            _blocked("HANDLE_LIMIT")
        return handle

    def _mapping(self):
        if self._mapping_calls >= MAX_MAPPING_OBSERVATIONS:
            _blocked("MAPPING_LIMIT")
        self._mapping_calls += 1
        volume = self._expected.volume
        context = self._api.context()
        if not _context(context) or context != volume.context:
            _blocked("HOST_CONTEXT_CHANGED")
        targets = self._api.mappings(volume.mapping_name)
        if (type(targets) is not tuple or not 1 <= len(targets) <= 128
                or any(type(item) is not str for item in targets)
                or targets != volume.mapping_targets):
            _blocked("MAPPING_CHANGED")

    def _inspect(self, handle, identity):
        info = self._api.inspect(handle)
        if (type(info) is not ObjectInfo or not _identity(info.identity)
                or info.identity != identity or info.directory is not True
                or type(info.attributes) is not int or not 0 <= info.attributes < 1 << 32
                or info.attributes & _UNSAFE or not info.attributes & 0x10
                or info.delete_pending is not False or type(info.reparse_tag) is not int
                or info.reparse_tag != 0 or type(info.links) is not int
                or info.links != 1 or type(info.size) is not int or not 0 <= info.size < 1 << 63
                or any(type(value) is not int or not 0 <= value < 1 << 63 for value in (
                    info.creation_time, info.last_write_time, info.change_time))):
            _blocked("OBJECT_UNSAFE")
        volume, device = self._api.volume(handle), self._api.device(handle)
        if (not _volume(volume) or not _device(device)
                or volume != self._expected.volume.volume or device != self._expected.volume.device):
            _blocked("VOLUME_CHANGED")
        if self._api.case_sensitive(handle) is not False:
            _blocked("CASE_BEHAVIOR_UNAVAILABLE")
        return info

    def _lookup(self, parent, name):
        _component(name)
        result = self._api.lookup(parent, name)
        if type(result) is not LookupResult:
            _blocked("LOOKUP_INVALID")
        # The seam may transfer only COMPLETED successful handles. Failed/pending
        # calls retain their resources inside the adapter; no unsafe close here.
        if result.kind is LookupKind.PRESENT:
            if classify_lookup(result.raw_status) is not LookupKind.PRESENT:
                _blocked("LOOKUP_OWNERSHIP_UNAVAILABLE")
            self._track(result.handle)
            if type(result.long_name) is not str:
                _blocked("LOOKUP_INVALID")
        elif result.handle is not None or result.long_name is not None:
            _blocked("LOOKUP_OWNERSHIP_UNAVAILABLE")
        if (result.kind not in (LookupKind.PRESENT, LookupKind.NAME_NOT_FOUND)
                or classify_lookup(result.raw_status) is not result.kind):
            _blocked("LOOKUP_UNAVAILABLE")
        return result

    def _release(self, handle):
        self._handles.remove(handle)
        try:
            self._api.close(handle)
        except BaseException:
            _blocked("CLOSE_UNCERTAIN")

    def _recheck_bindings(self):
        self._mapping()
        for parts, (handle, initial) in self._nodes.items():
            current = self._inspect(handle, initial.identity)
            if _fingerprint(current) != _fingerprint(initial):
                _blocked("BINDING_CHANGED")
            if parts:
                parent = self._nodes[parts[:-1]][0]
                probe = self._lookup(parent, parts[-1])
                if probe.kind is not LookupKind.PRESENT or probe.long_name != parts[-1]:
                    _blocked("BINDING_CHANGED")
                observed = self._inspect(probe.handle, initial.identity)
                if _fingerprint(observed) != _fingerprint(initial):
                    _blocked("BINDING_CHANGED")
                self._release(probe.handle)

    def _negative(self):
        parent_parts = self._expected.store_parent
        parent, info = self._nodes[parent_parts]
        # Native lookup must also search case/DOS aliases, without an object-type
        # constraint. ANY present object collides, even a file or unknown spelling.
        result = self._lookup(parent, self._store[len(parent_parts)])
        if result.kind is not LookupKind.NAME_NOT_FOUND:
            _blocked("STORE_PRESENT_OR_ALIAS")
        for parts in self._sources:
            for end in range(len(parts), len(parent_parts) + 1):
                node = self._nodes.get(parent_parts[:end])
                if node is not None and node[1].identity == self._nodes[parts][1].identity:
                    _blocked("STORE_OVERLAP")
        return AbsenceObservation(info.identity, self._store[len(parent_parts)],
                                  self._store[len(parent_parts) + 1:])

    def inspect_absence(self):
        try:
            if self._state != "BOUND":
                _blocked("SESSION_STATE")
            self._recheck_bindings()
            first = self._negative()
            self._recheck_bindings()
            if self._negative() != first:
                _blocked("ABSENCE_CHANGED")
            self._observation = first
            self._state = "OBSERVED"
            return first
        except BaseException as error:
            self.close()
            if isinstance(error, OSError):
                _blocked("METADATA_UNAVAILABLE")
            raise

    def recheck_absence(self):
        try:
            if self._state != "OBSERVED":
                _blocked("SESSION_STATE")
            self._recheck_bindings()
            if self._negative() != self._observation:
                _blocked("ABSENCE_CHANGED")
        except BaseException as error:
            self.close()
            if isinstance(error, OSError):
                _blocked("METADATA_UNAVAILABLE")
            raise

    def close(self):
        self._state = "CLOSED"
        self._observation = None
        uncertain = False
        while self._handles:
            try:
                self._api.close(self._handles.pop())
            except BaseException:
                uncertain = True
        if uncertain:
            _blocked("CLOSE_UNCERTAIN")

    def __enter__(self):
        if self._state not in ("BOUND", "OBSERVED"):
            _blocked("SESSION_STATE")
        return self

    def __exit__(self, *_):
        self.close()
