"""Import-safe CP1 selection; capability availability is not qualification.

No user setting can force a backend. Selection inspects runtime metadata only,
never source paths, directories, Git, network services or platform test probes.
"""

from importlib import import_module
import os
import sys
from types import ModuleType

from ._io_common import EvidenceError


_CAPABILITIES = (
    "source_read",
    "root_traversal",
    "enumeration",
    "file_identity",
    "publisher_lock",
    "no_clobber_publication",
)
_FLAGS = (
    "O_RDONLY",
    "O_WRONLY",
    "O_CREAT",
    "O_EXCL",
    "O_DIRECTORY",
    "O_NOFOLLOW",
    "O_NONBLOCK",
    "O_CLOEXEC",
)
_CALLS = (
    "open",
    "close",
    "dup",
    "mkdir",
    "fsync",
    "fstat",
    "stat",
    "scandir",
    "read",
    "write",
    "fchmod",
    "link",
    "unlink",
)


def filesystem_capabilities() -> dict:
    """Describe implementation prerequisites, not filesystem security or PASS.

    Windows is explicitly denied even if a compatibility layer exposes some
    POSIX names. Other unqualified platforms are denied as well. All existing
    per-operation POSIX permission/link/race checks remain mandatory.
    """
    platform, os_name = sys.platform, os.name
    missing = []
    if platform == "win32" or os_name == "nt":
        reason = "WINDOWS_BACKEND_NOT_IMPLEMENTED"
    elif os_name != "posix" or platform not in {"darwin", "linux"}:
        reason = "PLATFORM_NOT_SUPPORTED"
    else:
        missing.extend(
            "os." + name
            for name in _FLAGS
            if type(getattr(os, name, None)) is not int
            or (name != "O_RDONLY" and getattr(os, name, 0) == 0)
        )
        missing.extend("os." + name for name in _CALLS if not callable(getattr(os, name, None)))
        for group, names in (
            ("supports_dir_fd", ("open", "mkdir", "stat", "link", "unlink")),
            ("supports_fd", ("scandir",)),
            ("supports_follow_symlinks", ("stat", "link")),
        ):
            for name in names:
                if getattr(os, name, None) not in getattr(os, group, ()):
                    missing.append("os." + name + ":" + group)
        try:
            locking = import_module("fcntl")
            if not callable(getattr(locking, "flock", None)):
                missing.append("fcntl.flock")
            for name in ("LOCK_EX", "LOCK_NB", "LOCK_UN"):
                if type(getattr(locking, name, None)) is not int or getattr(locking, name, 0) == 0:
                    missing.append("fcntl." + name)
        except (ImportError, OSError):
            missing.append("fcntl")
        reason = "POSIX_PRIMITIVES_UNAVAILABLE" if missing else None
    state = "BLOCKED" if reason else "AVAILABLE"
    return {
        "platform": platform,
        "os_name": os_name,
        "backend": "blocked" if reason else "posix",
        "evidence_io": state,
        "reason": reason,
        "missing_primitives": sorted(missing),
        "capabilities": {name: state for name in _CAPABILITIES},
        "qualification": "Availability only; no filesystem or semantic qualification is implied.",
        "mitigation": (
            "Use an already qualified POSIX environment; Windows evidence I/O "
            "requires separately approved CP3/CP4 implementation and qualification."
            if reason
            else None
        ),
    }


def require_evidence_io() -> None:
    """Deny before any caller-supplied path access or output reservation."""
    if filesystem_capabilities()["evidence_io"] != "AVAILABLE":
        raise EvidenceError("FILESYSTEM_CAPABILITY_UNAVAILABLE", "BLOCKED")


def preflight_capabilities() -> dict:
    """CP3B reader status only; never probes paths or loads a native DLL.

    No environment variable, injected handle or declaration can override this
    public gate. The private Windows protocol is not a qualified public reader.
    Preserve the existing full-evidence capability/exit-code contract separately.
    """
    if sys.platform == "win32" or os.name == "nt":
        return {
            "backend": "windows",
            "read_only_preflight": "BLOCKED",
            "private_protocol": "IMPLEMENTED_UNQUALIFIED",
            "volume_bootstrap": "NOT_IMPLEMENTED",
            "native_qualification": "BLOCKED",
            "reason": "WINDOWS_VOLUME_BINDING_AND_QUALIFICATION_UNAVAILABLE",
            "publication": "BLOCKED",
        }
    current = filesystem_capabilities()
    return {
        "backend": current["backend"],
        "read_only_preflight": current["evidence_io"],
        "reason": current["reason"],
        "qualification": "Per-operation filesystem checks and explicit local policy remain required.",
    }


def get_backend() -> ModuleType:
    """Load only the existing POSIX implementation after the capability gate."""
    require_evidence_io()
    try:
        return import_module("sas_re._filesystem._posix_io")
    except (ImportError, AttributeError):
        # No ordinary open/pathlib/lock-free fallback on a broken runtime.
        raise EvidenceError("FILESYSTEM_CAPABILITY_UNAVAILABLE", "BLOCKED") from None
