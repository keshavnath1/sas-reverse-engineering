"""CP3A descriptor-only filesystem metadata, never source-content access.

These transient values are neither approval tokens nor canonical evidence. The
caller retains descriptors and checks object/name relationships separately. This
narrow policy accepts local APFS on Darwin and a single, whole-filesystem mount
of ext4/xfs/btrfs/tmpfs on Linux. Unknown ABIs, filesystems and mount arrangements
are BLOCKED; existing legacy readers do not use this module.
"""

from __future__ import annotations

import ctypes
from dataclasses import dataclass
from functools import lru_cache
import os
import stat
import sys

from .._io_common import EvidenceError


@dataclass(frozen=True)
class FilesystemIdentity:
    """Local, ephemeral identity; equality requires the same observed mount."""

    platform: str
    filesystem_type: str
    device: int
    fsid: tuple[int, int]
    mount_id: int | None
    mount_flags: int


class _DarwinStatfs(ctypes.Structure):
    # Installed macOS SDK sys/mount.h __DARWIN_STRUCT_STATFS64 (LP64).
    _fields_ = [
        ("f_bsize", ctypes.c_uint32),
        ("f_iosize", ctypes.c_int32),
        ("f_blocks", ctypes.c_uint64),
        ("f_bfree", ctypes.c_uint64),
        ("f_bavail", ctypes.c_uint64),
        ("f_files", ctypes.c_uint64),
        ("f_ffree", ctypes.c_uint64),
        ("f_fsid", ctypes.c_int32 * 2),
        ("f_owner", ctypes.c_uint32),
        ("f_type", ctypes.c_uint32),
        ("f_flags", ctypes.c_uint32),
        ("f_fssubtype", ctypes.c_uint32),
        ("f_fstypename", ctypes.c_char * 16),
        ("f_mntonname", ctypes.c_char * 1024),
        ("f_mntfromname", ctypes.c_char * 1024),
        ("f_flags_ext", ctypes.c_uint32),
        ("f_reserved", ctypes.c_uint32 * 7),
    ]


class _LinuxStatfs(ctypes.Structure):
    # LP64 x86_64/aarch64 Linux statfs ABI; no architecture guessing/fallback.
    _fields_ = [
        ("f_type", ctypes.c_long),
        ("f_bsize", ctypes.c_long),
        ("f_blocks", ctypes.c_ulong),
        ("f_bfree", ctypes.c_ulong),
        ("f_bavail", ctypes.c_ulong),
        ("f_files", ctypes.c_ulong),
        ("f_ffree", ctypes.c_ulong),
        ("f_fsid", ctypes.c_int32 * 2),
        ("f_namelen", ctypes.c_long),
        ("f_frsize", ctypes.c_long),
        ("f_flags", ctypes.c_long),
        ("f_spare", ctypes.c_long * 4),
    ]


_LINUX_TYPES = {"ext4": 0xEF53, "xfs": 0x58465342, "btrfs": 0x9123683E, "tmpfs": 0x01021994}
_PROC_MAGIC = 0x9FA0
_MAX_MOUNT_BYTES = 1024 * 1024
_MAX_MOUNTS = 4096
_MAX_FDINFO_BYTES = 64 * 1024


def _blocked(code: str = "PHYSICAL_FILESYSTEM_UNAVAILABLE") -> EvidenceError:
    return EvidenceError(code, "BLOCKED")


@lru_cache(maxsize=2)
def _statfs_function(platform: str):
    """Retain one trusted C binding per ABI; never cache filesystem observations."""
    if platform == "darwin":
        library = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)
        function, structure = library.fstatfs64, _DarwinStatfs
    else:
        # Resolve from the already loaded process C runtime, not a caller
        # supplied library path or a search-directory dependency.
        library = ctypes.CDLL(None, use_errno=True)
        function, structure = library.fstatfs, _LinuxStatfs
    function.argtypes = [ctypes.c_int, ctypes.POINTER(structure)]
    function.restype = ctypes.c_int
    return function


def _native_statfs(fd: int, platform: str):
    """Query an existing descriptor through an explicitly checked LP64 ABI."""
    try:
        machine = os.uname().machine
        if (
            ctypes.sizeof(ctypes.c_void_p) != 8
            or ctypes.sizeof(ctypes.c_long) != 8
            or ctypes.sizeof(ctypes.c_int) != 4
        ):
            raise _blocked("PHYSICAL_FILESYSTEM_ABI_UNAVAILABLE")
        if platform == "darwin":
            if machine not in {"arm64", "x86_64"} or ctypes.sizeof(_DarwinStatfs) != 2168:
                raise _blocked("PHYSICAL_FILESYSTEM_ABI_UNAVAILABLE")
            structure = _DarwinStatfs
        elif platform == "linux":
            if machine not in {"x86_64", "aarch64"} or ctypes.sizeof(_LinuxStatfs) != 120:
                raise _blocked("PHYSICAL_FILESYSTEM_ABI_UNAVAILABLE")
            structure = _LinuxStatfs
        else:
            raise _blocked()
        function = _statfs_function(platform)
        value = structure()
        if function(fd, ctypes.byref(value)) != 0:
            raise _blocked()
        return value
    except (AttributeError, OSError, TypeError, ValueError):
        raise _blocked("PHYSICAL_FILESYSTEM_ABI_UNAVAILABLE") from None


def _darwin_identity(fd: int, device: int) -> FilesystemIdentity:
    value = _native_statfs(fd, "darwin")
    fsid = tuple(value.f_fsid)
    # MNT_LOCAL; reject union, ignored ownership and automount. The only
    # accepted extended flag is the documented root-group Data-volume bit;
    # FSKit and unknown future extended semantics are not qualified here.
    if (
        value.f_fstypename != b"apfs"
        or not value.f_flags & 0x00001000
        or value.f_flags & (0x00000020 | 0x00200000 | 0x00400000)
        or value.f_flags_ext & ~0x00000001
        or fsid == (0, 0)
    ):
        raise _blocked("PHYSICAL_FILESYSTEM_UNSUPPORTED")
    return FilesystemIdentity("darwin", "apfs", device, fsid, None, value.f_flags)


def _read_proc_metadata(parts: tuple[str, ...], limit: int) -> bytes:
    """Read bounded *kernel metadata*, explicitly distinct from source bytes.

    A numeric current PID avoids following /proc/self. Every component is opened
    relative to a retained descriptor, no-follow, and verified as procfs. The
    caller cannot provide paths. No /proc/PID/fd symlink is followed or reopened.
    """
    handles: list[int] = []
    try:
        directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
        handles.append(os.open("/proc", directory_flags))
        for component in (str(os.getpid()),) + parts:
            if _native_statfs(handles[-1], "linux").f_type != _PROC_MAGIC:
                raise _blocked("PHYSICAL_MOUNT_METADATA_UNAVAILABLE")
            last = len(handles) == len(parts) + 1
            flags = (
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
                if last
                else directory_flags
            )
            handles.append(os.open(component, flags, dir_fd=handles[-1]))
        fd = handles[-1]
        if (
            not stat.S_ISREG(os.fstat(fd).st_mode)
            or _native_statfs(fd, "linux").f_type != _PROC_MAGIC
        ):
            raise _blocked("PHYSICAL_MOUNT_METADATA_UNAVAILABLE")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(fd, min(64 * 1024, limit + 1 - total))
            if not chunk:
                return b"".join(chunks)
            chunks.append(chunk)
            total += len(chunk)
            if total > limit:
                raise _blocked("PHYSICAL_MOUNT_METADATA_LIMIT")
    except OSError:
        raise _blocked("PHYSICAL_MOUNT_METADATA_UNAVAILABLE") from None
    finally:
        close_uncertain = False
        for fd in reversed(handles):
            try:
                os.close(fd)
            except OSError:
                # A failed close may already have released/reused the number.
                # Attempt every owned handle once, never retry an ambiguous FD.
                close_uncertain = True
        if close_uncertain:
            raise _blocked("PHYSICAL_METADATA_CLOSE_UNCERTAIN") from None


def _fd_mount_id(raw: bytes, inode: int) -> int:
    fields = {}
    try:
        if not raw or len(raw) > _MAX_FDINFO_BYTES or len(raw.splitlines()) > 128:
            raise ValueError
        for line in raw.splitlines():
            if line.startswith((b"mnt_id:", b"ino:")):
                key, value = line.split(b":", 1)
                value = value.strip()
                if key in fields or not value.isdigit() or len(value) > 20:
                    raise ValueError
                fields[key] = int(value)
        if fields.get(b"ino") != inode or fields.get(b"mnt_id", 0) <= 0:
            raise ValueError
        return fields[b"mnt_id"]
    except ValueError:
        raise _blocked("PHYSICAL_MOUNT_METADATA_UNAVAILABLE") from None


def _linux_mount_type(raw: bytes, mount_id: int, device: int, magic: int) -> str:
    """Validate a bounded mount table; reject bind/subvolume/duplicate aliases."""
    try:
        lines = raw.splitlines()
        if not lines or len(raw) > _MAX_MOUNT_BYTES or len(lines) > _MAX_MOUNTS:
            raise ValueError
        seen = set()
        candidates = []
        device_entries = 0
        expected_device = f"{os.major(device)}:{os.minor(device)}".encode("ascii")
        for line in lines:
            fields = line.split()
            separator = fields.index(b"-")
            if (
                separator < 6
                or len(fields) != separator + 4
                or not fields[0].isdigit()
                or not fields[1].isdigit()
                or len(fields[0]) > 20
                or len(fields[1]) > 20
                or not fields[3].startswith(b"/")
                or not fields[4].startswith(b"/")
            ):
                raise ValueError
            identifier = int(fields[0])
            if identifier <= 0 or identifier in seen:
                raise ValueError
            seen.add(identifier)
            if fields[2] == expected_device:
                device_entries += 1
            if identifier == mount_id:
                candidates.append((fields[2], fields[3], fields[separator + 1]))
        if len(candidates) != 1 or device_entries != 1:
            raise _blocked("PHYSICAL_MOUNT_AMBIGUOUS")
        found_device, mount_root, kind_raw = candidates[0]
        kind = kind_raw.decode("ascii")
        if found_device != expected_device or mount_root != b"/":
            raise _blocked("PHYSICAL_MOUNT_AMBIGUOUS")
        if kind not in _LINUX_TYPES or _LINUX_TYPES[kind] != magic:
            raise _blocked("PHYSICAL_FILESYSTEM_UNSUPPORTED")
        return kind
    except (ValueError, UnicodeError, IndexError, OverflowError):
        raise _blocked("PHYSICAL_MOUNT_METADATA_UNAVAILABLE") from None


def _linux_identity(fd: int, device: int, inode: int) -> FilesystemIdentity:
    value = _native_statfs(fd, "linux")
    if value.f_type not in _LINUX_TYPES.values() or tuple(value.f_fsid) == (0, 0):
        raise _blocked("PHYSICAL_FILESYSTEM_UNSUPPORTED")
    first = _fd_mount_id(_read_proc_metadata(("fdinfo", str(fd)), _MAX_FDINFO_BYTES), inode)
    table = _read_proc_metadata(("mountinfo",), _MAX_MOUNT_BYTES)
    kind = _linux_mount_type(table, first, device, value.f_type)
    second = _fd_mount_id(_read_proc_metadata(("fdinfo", str(fd)), _MAX_FDINFO_BYTES), inode)
    if first != second or table != _read_proc_metadata(("mountinfo",), _MAX_MOUNT_BYTES):
        raise _blocked("PHYSICAL_MOUNT_CHANGED")
    return FilesystemIdentity("linux", kind, device, tuple(value.f_fsid), first, value.f_flags)


def filesystem_identity(fd: int) -> FilesystemIdentity:
    """Inspect an already retained file/directory; never open supplied paths.

    The caller must prohibit mount changes and untrusted writers in its dedicated
    inspection anchor, retain all descriptors, and recheck relationships. These
    observations are not an atomic snapshot or evidence of human authorization.
    """
    if os.name != "posix" or sys.platform not in {"darwin", "linux"}:
        raise _blocked()
    if type(fd) is not int or fd < 0:
        raise _blocked()
    try:
        before = os.fstat(fd)
        if not (stat.S_ISDIR(before.st_mode) or stat.S_ISREG(before.st_mode)):
            raise _blocked("PHYSICAL_FILESYSTEM_UNSUPPORTED")
        if sys.platform == "darwin":
            result = _darwin_identity(fd, before.st_dev)
        else:
            result = _linux_identity(fd, before.st_dev, before.st_ino)
        after = os.fstat(fd)
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise _blocked("PHYSICAL_OBJECT_CHANGED")
        return result
    except OSError:
        raise _blocked() from None
