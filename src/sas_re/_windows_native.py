"""Private CP3B Windows ABI adapter; importing this module performs no native I/O.

There is deliberately no pathname/drive/volume bootstrap. A future independently
qualified caller must own the retained NTFS volume-root handle. The public
preflight gate remains BLOCKED; these primitives alone do not establish locality,
authorization, an approved writer policy or native security qualification.
"""

import ctypes as C
from dataclasses import dataclass
import os
import platform
import struct
import sys

from ._authorization_paths import _portable_component, _text
from ._io_common import EvidenceError, MAX_FILES, MAX_DIRECTORIES


DWORD = C.c_uint32
WORD = C.c_uint16
HANDLE = C.c_void_p
BOOL = C.c_int32
NTSTATUS = C.c_int32
ULONG_PTR = C.c_uint64
LARGE_INTEGER = C.c_int64

MAX_HANDLES = 4096
QUERY_BYTES = 65536
MAX_QUERY_CALLS = 128
MAX_ENTRIES = MAX_FILES + MAX_DIRECTORIES + 2
READ_CHUNK = 65536
FILE_ATTRIBUTE_DIRECTORY = 0x10
FILE_ATTRIBUTE_REPARSE_POINT = 0x400
# Device, offline, virtual, recall-on-open and recall-on-data-access are refused.
UNSUPPORTED_ATTRIBUTES = 0x40 | 0x1000 | 0x10000 | 0x40000 | 0x400000


@dataclass(frozen=True)
class ObjectIdentity:
    volume_serial: int
    file_id: bytes


@dataclass(frozen=True)
class ObjectInfo:
    identity: ObjectIdentity
    directory: bool
    size: int
    links: int
    delete_pending: bool
    attributes: int
    creation_time: int
    last_write_time: int
    change_time: int
    reparse_tag: int = 0


@dataclass(frozen=True)
class VolumeInfo:
    filesystem: str
    serial: int
    max_component_length: int
    flags: int


@dataclass(frozen=True)
class DirectoryEntry:
    name: str
    file_id: bytes
    attributes: int
    size: int
    reparse_tag: int = 0


class _UNICODE_STRING(C.Structure):
    _fields_ = [("Length", WORD), ("MaximumLength", WORD), ("Buffer", C.POINTER(WORD))]


class _OBJECT_ATTRIBUTES(C.Structure):
    _fields_ = [("Length", DWORD), ("RootDirectory", HANDLE),
                ("ObjectName", C.POINTER(_UNICODE_STRING)), ("Attributes", DWORD),
                ("SecurityDescriptor", C.c_void_p), ("SecurityQualityOfService", C.c_void_p)]


class _STATUS(C.Union):
    _fields_ = [("Status", NTSTATUS), ("Pointer", C.c_void_p)]


class _IO_STATUS_BLOCK(C.Structure):
    _fields_ = [("Result", _STATUS), ("Information", ULONG_PTR)]


class _FILE_ID_INFO(C.Structure):
    _fields_ = [("VolumeSerialNumber", C.c_uint64), ("FileId", C.c_ubyte * 16)]


class _FILE_STANDARD_INFO(C.Structure):
    _fields_ = [("AllocationSize", LARGE_INTEGER), ("EndOfFile", LARGE_INTEGER),
                ("NumberOfLinks", DWORD), ("DeletePending", C.c_ubyte), ("Directory", C.c_ubyte)]


class _FILE_BASIC_INFO(C.Structure):
    _fields_ = [("CreationTime", LARGE_INTEGER), ("LastAccessTime", LARGE_INTEGER),
                ("LastWriteTime", LARGE_INTEGER), ("ChangeTime", LARGE_INTEGER),
                ("FileAttributes", DWORD)]


class _FILE_ATTRIBUTE_TAG_INFO(C.Structure):
    _fields_ = [("FileAttributes", DWORD), ("ReparseTag", DWORD)]


class _OVERLAPPED(C.Structure):
    _fields_ = [("Internal", ULONG_PTR), ("InternalHigh", ULONG_PTR),
                ("Offset", DWORD), ("OffsetHigh", DWORD), ("hEvent", HANDLE)]


def _blocked(code: str) -> None:
    raise EvidenceError(code, "BLOCKED")


def _check_abi() -> None:
    """Fixed LLP64 x64 layout, checked even in synthetic non-Windows tests."""
    layouts = ((_UNICODE_STRING, 16, 8), (_OBJECT_ATTRIBUTES, 48, 8),
               (_IO_STATUS_BLOCK, 16, 8), (_FILE_ID_INFO, 24, 8),
               (_FILE_STANDARD_INFO, 24, 8), (_FILE_BASIC_INFO, 40, 8),
               (_FILE_ATTRIBUTE_TAG_INFO, 8, 4), (_OVERLAPPED, 32, 8))
    if (C.sizeof(HANDLE) != 8 or sys.byteorder != "little"
            or any(C.sizeof(cls) != size or C.alignment(cls) != alignment
                   for cls, size, alignment in layouts)
            or _OBJECT_ATTRIBUTES.RootDirectory.offset != 8
            or _OBJECT_ATTRIBUTES.ObjectName.offset != 16
            or _OBJECT_ATTRIBUTES.Attributes.offset != 24
            or _UNICODE_STRING.Buffer.offset != 8
            or _IO_STATUS_BLOCK.Information.offset != 8
            or _FILE_STANDARD_INFO.Directory.offset != 21
            or _FILE_BASIC_INFO.FileAttributes.offset != 32
            or _OVERLAPPED.hEvent.offset != 24):
        _blocked("CP3B_ABI_UNAVAILABLE")


def _component(name: str) -> bytes:
    try:
        _text(name)
        _portable_component(name)
        raw = name.encode("utf-16-le")
    except (EvidenceError, UnicodeError):
        _blocked("CP3B_COMPONENT_INVALID")
    if not 2 <= len(raw) <= 510:
        _blocked("CP3B_COMPONENT_INVALID")
    return raw


def parse_directory_buffer(raw: bytes) -> tuple[DirectoryEntry, ...]:
    """Parse bounded FILE_ID_EXTD_DIR_INFO records; no filtering of hidden names.

    GetFileInformationByHandleEx has no returned-byte count. Its output buffer is
    zero-initialized and the chain terminates only at NextEntryOffset == 0.
    Unused ReparsePointTag is undefined without its attribute and normalized to 0.
    """
    if type(raw) is not bytes or not 90 <= len(raw) <= QUERY_BYTES:
        _blocked("CP3B_DIRECTORY_RECORD_INVALID")
    offset = 0
    result = []
    names = set()
    while True:
        if offset % 8 or offset + 88 > len(raw) or len(result) >= MAX_ENTRIES:
            _blocked("CP3B_DIRECTORY_RECORD_INVALID")
        next_offset = struct.unpack_from("<I", raw, offset)[0]
        size = struct.unpack_from("<q", raw, offset + 40)[0]
        attributes, length, _, tag = struct.unpack_from("<IIII", raw, offset + 56)
        end = offset + 88 + length
        if (not 2 <= length <= 510 or length % 2 or end > len(raw) or size < 0
                or (next_offset and (next_offset % 8 or next_offset < 88 + length
                                     or offset + next_offset + 88 > len(raw)))):
            _blocked("CP3B_DIRECTORY_RECORD_INVALID")
        try:
            name = raw[offset + 88:end].decode("utf-16-le", errors="strict")
        except UnicodeError:
            _blocked("CP3B_DIRECTORY_RECORD_INVALID")
        if not name or "\x00" in name or "/" in name or "\\" in name or name in names:
            _blocked("CP3B_DIRECTORY_RECORD_INVALID")
        file_id = raw[offset + 72:offset + 88]
        if file_id == bytes(16):
            _blocked("CP3B_IDENTITY_UNAVAILABLE")
        names.add(name)
        result.append(DirectoryEntry(name, file_id, attributes, size,
                                     tag if attributes & FILE_ATTRIBUTE_REPARSE_POINT else 0))
        if not next_offset:
            return tuple(result)
        offset += next_offset


def _handle(value: int) -> HANDLE:
    if type(value) is not int or not 0 < value < (1 << 64) - 1:
        _blocked("CP3B_HANDLE_INVALID")
    return HANDLE(value)


class WindowsNative:
    """Private native primitives, with child-handle ownership and no bootstrap.

    The caller owns its initial retained directory handle and all returned
    handles, closes each once, and supplies quiescent, qualified local NTFS.
    Methods are single-thread/session use; they do not authenticate the caller.
    No ordinary-file, path-resolution or reduced-rights retry is implemented.
    """

    def __init__(self) -> None:
        if (sys.platform != "win32" or os.name != "nt"
                or platform.machine().lower() not in {"amd64", "x86_64"}
                or not hasattr(C, "WinDLL")):
            _blocked("CP3B_NATIVE_UNAVAILABLE")
        _check_abi()
        try:
            version = sys.getwindowsversion()
            if version.major != 10 or version.build < 22000:
                _blocked("CP3B_NATIVE_UNAVAILABLE")
            # LOAD_LIBRARY_SEARCH_SYSTEM32. Never use caller-provided DLL paths.
            self._kernel = C.WinDLL("kernel32.dll", use_last_error=True, winmode=0x800)
            self._ntdll = C.WinDLL("ntdll.dll", use_last_error=True, winmode=0x800)
            self._bind()
        except (AttributeError, OSError):
            _blocked("CP3B_NATIVE_UNAVAILABLE")
        self._owned: set[int] = set()
        self._closed: set[int] = set()
        self._offsets: dict[int, int] = {}

    def _bind(self) -> None:
        def bind(dll, name, args, result):
            function = getattr(dll, name)
            function.argtypes, function.restype = args, result
            return function

        pointer = C.c_void_p
        self._open = bind(self._ntdll, "NtCreateFile",
                          [C.POINTER(HANDLE), DWORD, C.POINTER(_OBJECT_ATTRIBUTES),
                           C.POINTER(_IO_STATUS_BLOCK), pointer, DWORD, DWORD,
                           DWORD, DWORD, pointer, DWORD], NTSTATUS)
        self._query = bind(self._kernel, "GetFileInformationByHandleEx",
                           [HANDLE, C.c_int32, pointer, DWORD], BOOL)
        self._type = bind(self._kernel, "GetFileType", [HANDLE], DWORD)
        self._handle_info = bind(self._kernel, "GetHandleInformation",
                                 [HANDLE, C.POINTER(DWORD)], BOOL)
        self._volume = bind(self._kernel, "GetVolumeInformationByHandleW",
                            [HANDLE, C.POINTER(WORD), DWORD, C.POINTER(DWORD),
                             C.POINTER(DWORD), C.POINTER(DWORD), C.POINTER(WORD), DWORD], BOOL)
        self._read = bind(self._kernel, "ReadFile",
                          [HANDLE, pointer, DWORD, C.POINTER(DWORD), C.POINTER(_OVERLAPPED)], BOOL)
        self._close = bind(self._kernel, "CloseHandle", [HANDLE], BOOL)

    def _live(self, handle: int) -> HANDLE:
        result = _handle(handle)
        if handle in self._closed:
            _blocked("CP3B_HANDLE_CLOSED")
        return result

    def _information(self, handle: int, kind: int, cls):
        value = cls()
        if not self._query(self._live(handle), kind, C.byref(value), C.sizeof(value)):
            _blocked("CP3B_METADATA_UNAVAILABLE")
        return value

    def inspect(self, handle: int) -> ObjectInfo:
        native_handle = self._live(handle)
        flags = DWORD()
        if (self._type(native_handle) != 1
                or not self._handle_info(native_handle, C.byref(flags)) or flags.value != 0):
            _blocked("CP3B_HANDLE_UNSAFE")
        tag = self._information(handle, 9, _FILE_ATTRIBUTE_TAG_INFO)
        if tag.FileAttributes & FILE_ATTRIBUTE_REPARSE_POINT:
            _blocked("CP3B_REPARSE_POINT")
        if tag.FileAttributes & UNSUPPORTED_ATTRIBUTES:
            _blocked("CP3B_OBJECT_UNSUPPORTED")
        identity = self._information(handle, 18, _FILE_ID_INFO)
        standard = self._information(handle, 1, _FILE_STANDARD_INFO)
        basic = self._information(handle, 0, _FILE_BASIC_INFO)
        file_id = bytes(identity.FileId)
        if not identity.VolumeSerialNumber or file_id == bytes(16):
            _blocked("CP3B_IDENTITY_UNAVAILABLE")
        if (standard.Directory not in (0, 1) or standard.DeletePending not in (0, 1)
                or standard.DeletePending or standard.EndOfFile < 0
                or standard.AllocationSize < 0 or not standard.NumberOfLinks
                or tag.FileAttributes != basic.FileAttributes
                or bool(tag.FileAttributes & FILE_ATTRIBUTE_DIRECTORY) != bool(standard.Directory)):
            _blocked("CP3B_METADATA_INCONSISTENT")
        if not standard.Directory and standard.NumberOfLinks != 1:
            _blocked("CP3B_HARDLINK_UNSAFE")
        return ObjectInfo(ObjectIdentity(identity.VolumeSerialNumber, file_id),
                          bool(standard.Directory), standard.EndOfFile, standard.NumberOfLinks,
                          bool(standard.DeletePending), basic.FileAttributes, basic.CreationTime,
                          basic.LastWriteTime, basic.ChangeTime)

    def volume(self, handle: int) -> VolumeInfo:
        # This query is NOT proof of locality, unique volume binding or backing.
        serial, maximum, flags = DWORD(), DWORD(), DWORD()
        name = (WORD * 261)()
        if not self._volume(self._live(handle), None, 0, C.byref(serial),
                            C.byref(maximum), C.byref(flags), name, 261):
            _blocked("CP3B_VOLUME_UNAVAILABLE")
        units = list(name)
        if 0 not in units:
            _blocked("CP3B_VOLUME_UNAVAILABLE")
        raw = b"".join(unit.to_bytes(2, "little") for unit in units[:units.index(0)])
        try:
            filesystem = raw.decode("utf-16-le", errors="strict")
        except UnicodeError:
            _blocked("CP3B_VOLUME_UNAVAILABLE")
        if filesystem != "NTFS" or not serial.value or maximum.value != 255 or not flags.value & 8:
            _blocked("CP3B_VOLUME_UNSUPPORTED")
        return VolumeInfo(filesystem, serial.value, maximum.value, flags.value)

    def open_child(self, parent_handle: int, name: str, *, directory: bool,
                   read_data: bool = False) -> int:
        raw = _component(name)
        if type(directory) is not bool or type(read_data) is not bool or (directory and read_data):
            _blocked("CP3B_ACCESS_INVALID")
        if len(self._owned) >= MAX_HANDLES:
            _blocked("CP3B_HANDLE_LIMIT")
        if not self.inspect(parent_handle).directory:
            _blocked("CP3B_PARENT_UNSAFE")
        buffer = (WORD * (len(raw) // 2 + 1))()
        C.memmove(buffer, raw, len(raw))
        name_info = _UNICODE_STRING(len(raw), len(raw) + 2, buffer)
        attrs = _OBJECT_ATTRIBUTES(C.sizeof(_OBJECT_ATTRIBUTES), self._live(parent_handle),
                                   C.pointer(name_info), 0x40, None, None)
        result, completion = HANDLE(), _IO_STATUS_BLOCK()
        # READ_ATTRIBUTES | SYNCHRONIZE; directory LIST/TRAVERSE use object-specific
        # bits. No write/delete/backup/execute-file rights, no create disposition.
        access = 0x80 | 0x100000 | (0x21 if directory else (1 if read_data else 0))
        options = 0x200000 | 0x20 | (1 if directory else 0x40)
        sharing = 7 if directory else 1
        try:
            status = self._open(C.byref(result), access, C.byref(attrs), C.byref(completion),
                                None, 0, sharing, 1, options, None, 0)
            handle = result.value
            # Do not accept STATUS_PENDING or unexpected informational successes.
            if (status != 0 or completion.Result.Status != 0 or completion.Information != 1
                    or not handle or handle == (1 << 64) - 1):
                _blocked("CP3B_OPEN_UNAVAILABLE")
            self._closed.discard(handle)  # A new successful OS open owns any reused value.
            self._owned.add(handle)
            info = self.inspect(handle)
            if info.directory != directory:
                _blocked("CP3B_OBJECT_TYPE_MISMATCH")
            if read_data:
                self._offsets[handle] = 0
            return handle
        except BaseException:
            # Also covers cancellation after the native call supplied a handle.
            handle = result.value
            if handle and handle != (1 << 64) - 1:
                self._closed.discard(handle)
                self.close(handle)
            raise

    def entries(self, handle: int) -> tuple[DirectoryEntry, ...]:
        directory = self.inspect(handle)
        if not directory.directory:
            _blocked("CP3B_PARENT_UNSAFE")
        entries = []
        seen = set()
        for index in range(MAX_QUERY_CALLS):
            buffer = (C.c_ubyte * QUERY_BYTES)()
            ok = self._query(self._live(handle), 20 if index == 0 else 19,
                             C.byref(buffer), QUERY_BYTES)
            if not ok:
                if C.get_last_error() == 18:  # ERROR_NO_MORE_FILES, never a general error skip.
                    return tuple(entries)
                _blocked("CP3B_ENUMERATION_UNAVAILABLE")
            batch = parse_directory_buffer(bytes(buffer))
            for entry in batch:
                if entry.name in seen or len(seen) >= MAX_ENTRIES:
                    _blocked("CP3B_ENUMERATION_INCOMPLETE")
                seen.add(entry.name)
                if entry.name in {".", ".."}:
                    # Structural records are never traversed. Validate their type
                    # before filtering; every hidden/system ordinary name remains.
                    if (not entry.attributes & FILE_ATTRIBUTE_DIRECTORY
                            or entry.attributes & (FILE_ATTRIBUTE_REPARSE_POINT | UNSUPPORTED_ATTRIBUTES)
                            or (entry.name == "." and entry.file_id != directory.identity.file_id)):
                        _blocked("CP3B_DIRECTORY_RECORD_INVALID")
                    continue
                entries.append(entry)
        _blocked("CP3B_ENUMERATION_LIMIT")

    def rewind(self, handle: int) -> None:
        self._live(handle)
        if handle not in self._offsets:
            _blocked("CP3B_DATA_HANDLE_REQUIRED")
        self._offsets[handle] = 0

    def read(self, handle: int, limit: int) -> bytes:
        self._live(handle)
        if type(limit) is not int or not 1 <= limit <= READ_CHUNK:
            _blocked("CP3B_READ_LIMIT")
        if handle not in self._offsets:
            _blocked("CP3B_DATA_HANDLE_REQUIRED")
        offset = self._offsets[handle]
        if offset > (1 << 63) - 1 - limit:
            _blocked("CP3B_READ_LIMIT")
        buffer, count = (C.c_ubyte * limit)(), DWORD()
        position = _OVERLAPPED(0, 0, offset & 0xffffffff, offset >> 32, None)
        if not self._read(self._live(handle), buffer, limit, C.byref(count), C.byref(position)):
            if C.get_last_error() == 38:  # ERROR_HANDLE_EOF only.
                return b""
            _blocked("CP3B_READ_UNAVAILABLE")
        if count.value > limit:
            _blocked("CP3B_READ_INVALID")
        self._offsets[handle] += count.value
        return bytes(buffer[:count.value])

    def close(self, handle: int) -> None:
        native_handle = self._live(handle)
        self._closed.add(handle)
        self._owned.discard(handle)
        self._offsets.pop(handle, None)
        # One attempt only: an ambiguous result must not close a reused number.
        if not self._close(native_handle):
            _blocked("CP3B_CLOSE_UNCERTAIN")
