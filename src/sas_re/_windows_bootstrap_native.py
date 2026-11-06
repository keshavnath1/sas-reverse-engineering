"""Private CP3D metadata adapter; import never loads a DLL or accesses paths.

Only bounded, explicitly named DOS mapping observations have a callable native
binding. These observations are neither volume identity nor inspection authority.
The caller must already have independent authority for each named observation.
All filesystem operations remain unconditionally BLOCKED: no completion-safe
native bootstrap/lookup has been qualified, and no caller flag bypasses that gate.
"""

import ctypes as C
from dataclasses import dataclass
import os
import platform
import re
import struct
import sys
from typing import NoReturn

from ._io_common import EvidenceError


MAPPING_BYTES = 65536
MAPPING_UNITS = MAPPING_BYTES // 2
MAX_MAPPING_OBSERVATIONS = 8
MAX_MAPPING_ENTRIES = 128
_DEVICE_NAME = re.compile(
    r"(?:[A-Z]:|Volume\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-"
    r"[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\})\Z"
)


@dataclass(frozen=True)
class DeviceInfo:
    """Transient FILE_FS_DEVICE_INFORMATION observations, not backing proof."""

    device_type: int
    characteristics: int


def _blocked(code: str) -> NoReturn:
    raise EvidenceError(code, "BLOCKED")


def parse_device_information(raw: bytes) -> DeviceInfo:
    """Decode the fixed two-DWORD record without inferring locality/approval."""
    if type(raw) is not bytes or len(raw) != 8:
        _blocked("CP3D_DEVICE_RECORD_INVALID")
    return DeviceInfo(*struct.unpack("<II", raw))


def _mapping_name(name: str) -> bytes:
    # Never permit NULL, an empty query, arbitrary namespace input or a scan.
    if type(name) is not str or _DEVICE_NAME.fullmatch(name) is None:
        _blocked("CP3D_MAPPING_NAME_INVALID")
    return name.encode("utf-16-le")


def parse_dos_mappings(raw: bytes, units: int) -> tuple[str, ...]:
    """Parse exactly the reported UTF-16 MULTI_SZ, retaining current/prior order.

    ``units`` is QueryDosDeviceW's count of UTF-16 code units, not bytes. The
    final extra NUL must lie inside that count; zero-filled buffer slack cannot
    repair an incomplete response. No native collation or alias proof is implied.
    """
    if (type(raw) is not bytes or type(units) is not int
            or len(raw) % 2 or not 6 <= len(raw) <= MAPPING_BYTES
            or not 3 <= units <= len(raw) // 2):
        _blocked("CP3D_MAPPING_RECORD_INVALID")
    selected = raw[:units * 2]
    if not selected.endswith(b"\x00\x00\x00\x00"):
        _blocked("CP3D_MAPPING_RECORD_INVALID")
    try:
        decoded = selected.decode("utf-16-le", errors="strict")
    except UnicodeError:
        _blocked("CP3D_MAPPING_RECORD_INVALID")
    entries = decoded[:-2].split("\x00")
    if (not 1 <= len(entries) <= MAX_MAPPING_ENTRIES
            or any(not entry or any(ord(char) < 32 for char in entry) for entry in entries)):
        _blocked("CP3D_MAPPING_RECORD_INVALID")
    return tuple(entries)


class NativeMetadata:
    """Bounded named observations only; no source handles, reads or publisher.

    Constructor platform checks establish only DLL availability. They do not
    constitute native qualification. A single instance is one thread/session;
    mapping attempts (including failed calls) consume its finite observation cap.
    No Nt function is bound, and no native handle can be acquired or accepted.
    """

    def __init__(self) -> None:
        if (sys.platform != "win32" or os.name != "nt"
                or platform.machine().lower() not in {"amd64", "x86_64"}
                or not hasattr(C, "WinDLL") or C.sizeof(C.c_void_p) != 8
                or sys.byteorder != "little"):
            _blocked("CP3D_NATIVE_UNAVAILABLE")
        try:
            version = sys.getwindowsversion()
            if version.major != 10 or version.build < 22000:
                _blocked("CP3D_NATIVE_UNAVAILABLE")
            # Fixed system DLL search; no caller-controlled DLL or fallback.
            self._kernel = C.WinDLL("kernel32.dll", use_last_error=True, winmode=0x800)
            self._query_mapping = self._kernel.QueryDosDeviceW
            self._query_mapping.argtypes = [C.POINTER(C.c_uint16),
                                            C.POINTER(C.c_uint16), C.c_uint32]
            self._query_mapping.restype = C.c_uint32
        except (AttributeError, OSError):
            _blocked("CP3D_NATIVE_UNAVAILABLE")
        self._mapping_observations = 0

    def mappings(self, name: str) -> tuple[str, ...]:
        encoded = _mapping_name(name)
        if self._mapping_observations >= MAX_MAPPING_OBSERVATIONS:
            _blocked("CP3D_MAPPING_OBSERVATION_LIMIT")
        self._mapping_observations += 1
        query_name = (C.c_uint16 * (len(encoded) // 2 + 1))()
        C.memmove(query_name, encoded, len(encoded))
        output = (C.c_uint16 * MAPPING_UNITS)()
        # One synchronous Win32 metadata call. No growing buffer, retry, search,
        # conversion to another spelling or Nt completion lifetime is involved.
        count = self._query_mapping(query_name, output, MAPPING_UNITS)
        if type(count) is not int or not 3 <= count <= MAPPING_UNITS:
            _blocked("CP3D_MAPPING_UNAVAILABLE")
        return parse_dos_mappings(bytes(output), count)

    def context(self) -> NoReturn:
        # No local machine-name query authenticates an independently approved
        # host/token/code tuple; the authority/context provider is still OPEN.
        _blocked("CP3D_NATIVE_COMPLETION_UNQUALIFIED")

    def open_root(self, locator: str) -> NoReturn:
        _blocked("CP3D_NATIVE_COMPLETION_UNQUALIFIED")

    def inspect(self, handle: int) -> NoReturn:
        _blocked("CP3D_NATIVE_COMPLETION_UNQUALIFIED")

    def volume(self, handle: int) -> NoReturn:
        _blocked("CP3D_NATIVE_COMPLETION_UNQUALIFIED")

    def device(self, handle: int) -> NoReturn:
        _blocked("CP3D_NATIVE_COMPLETION_UNQUALIFIED")

    def case_sensitive(self, handle: int) -> NoReturn:
        _blocked("CP3D_NATIVE_COMPLETION_UNQUALIFIED")

    def lookup(self, parent_handle: int, name: str) -> NoReturn:
        _blocked("CP3D_NATIVE_COMPLETION_UNQUALIFIED")

    def close(self, handle: int) -> NoReturn:
        # This adapter never acquires/accepts handles; do not close a foreign or
        # potentially pending handle just because a number was supplied.
        _blocked("CP3D_NATIVE_COMPLETION_UNQUALIFIED")
