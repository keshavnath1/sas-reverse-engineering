"""POSIX mount metadata checks reject unsupported objects; injected records are not native qualification."""

import ctypes
from dataclasses import FrozenInstanceError
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from sas_re._filesystem import _posix_filesystem as filesystem
from sas_re._io_common import EvidenceError


class MetadataPolicyTests(unittest.TestCase):
    def assert_blocked(self, operation, code=None):
        with self.assertRaises(EvidenceError) as raised:
            operation()
        self.assertEqual(raised.exception.gate, "BLOCKED")
        if code:
            self.assertEqual(raised.exception.code, code)

    def test_windows_denies_before_descriptor_or_library_access(self):
        with (
            patch.object(sys, "platform", "win32"),
            patch.object(os, "fstat", side_effect=AssertionError("descriptor access")),
            patch.object(ctypes, "CDLL", side_effect=AssertionError("library access")),
        ):
            self.assert_blocked(lambda: filesystem.filesystem_identity(1))

    def test_unknown_platform_denies_before_descriptor_access(self):
        with (
            patch.object(sys, "platform", "other"),
            patch.object(os, "fstat", side_effect=AssertionError("descriptor access")),
        ):
            self.assert_blocked(lambda: filesystem.filesystem_identity(1))

    def test_invalid_descriptor_values_are_blocked(self):
        for value in (True, None, -1, "3"):
            with self.subTest(value=value):
                self.assert_blocked(lambda: filesystem.filesystem_identity(value))

    def test_unrecognized_native_abi_does_not_load_library(self):
        with (
            patch.object(os, "uname", return_value=SimpleNamespace(machine="unknown")),
            patch.object(ctypes, "CDLL", side_effect=AssertionError("library access")),
        ):
            for platform in ("darwin", "linux"):
                self.assert_blocked(
                    lambda: filesystem._native_statfs(1, platform),
                    "PHYSICAL_FILESYSTEM_ABI_UNAVAILABLE",
                )

    def test_missing_native_library_has_no_fallback(self):
        filesystem._statfs_function.cache_clear()
        with (
            patch.object(os, "uname", return_value=SimpleNamespace(machine="x86_64")),
            patch.object(ctypes, "CDLL", side_effect=OSError("unavailable")),
        ):
            self.assert_blocked(
                lambda: filesystem._native_statfs(1, "darwin"),
                "PHYSICAL_FILESYSTEM_ABI_UNAVAILABLE",
            )

    def test_darwin_local_apfs_policy_and_immutable_identity(self):
        value = filesystem._DarwinStatfs()
        value.f_fstypename = b"apfs"
        value.f_flags = 0x1000
        value.f_fsid[:] = (5, 6)
        with patch.object(filesystem, "_native_statfs", return_value=value):
            result = filesystem._darwin_identity(99, 123)
        self.assertEqual(result.filesystem_type, "apfs")
        self.assertEqual(result.device, 123)
        self.assertEqual(result.fsid, (5, 6))
        self.assertIsNone(result.mount_id)
        with self.assertRaises(FrozenInstanceError):
            result.device = 124

    def test_darwin_unqualified_flags_types_and_zero_identity_blocked(self):
        for kind, flags, extended, fsid in (
            (b"nfs", 0x1000, 0, (1, 2)),
            (b"apfs", 0, 0, (1, 2)),
            (b"apfs", 0x1020, 0, (1, 2)),
            (b"apfs", 0x201000, 0, (1, 2)),
            (b"apfs", 0x401000, 0, (1, 2)),
            (b"apfs", 0x1000, 2, (1, 2)),
            (b"apfs", 0x1000, 4, (1, 2)),
            (b"apfs", 0x1000, 0, (0, 0)),
        ):
            with self.subTest(kind=kind, flags=flags, extended=extended, fsid=fsid):
                value = filesystem._DarwinStatfs()
                value.f_fstypename = kind
                value.f_flags = flags
                value.f_flags_ext = extended
                value.f_fsid[:] = fsid
                with patch.object(filesystem, "_native_statfs", return_value=value):
                    self.assert_blocked(
                        lambda: filesystem._darwin_identity(99, 123),
                        "PHYSICAL_FILESYSTEM_UNSUPPORTED",
                    )

    def test_linux_fd_metadata_matches_the_retained_inode(self):
        raw = b"pos:\t0\nflags:\t02100000\nmnt_id:\t42\nino:\t1234\n"
        self.assertEqual(filesystem._fd_mount_id(raw, 1234), 42)
        self.assert_blocked(lambda: filesystem._fd_mount_id(raw, 1235))

    def test_linux_missing_duplicate_malformed_metadata_blocked(self):
        for raw in (
            b"",
            b"ino: 4\n",
            b"mnt_id: 1\nino: 4\nmnt_id: 1\n",
            b"mnt_id: 1\nino: 4\nino: 4\n",
            b"mnt_id: -1\nino: 4\n",
            b"mnt_id: not-number\nino: 4\n",
            b"x\n" * 129,
        ):
            with self.subTest(raw=raw[:60]):
                self.assert_blocked(lambda: filesystem._fd_mount_id(raw, 4))

    def table(self, kind="ext4", root="/", identifier=42, device="8:1"):
        return f"{identifier} 1 {device} {root} /fixtures rw - {kind} /dev/synthetic rw\n".encode()

    def test_linux_known_local_whole_filesystem_mounts(self):
        for kind, magic in filesystem._LINUX_TYPES.items():
            with self.subTest(kind=kind):
                self.assertEqual(
                    filesystem._linux_mount_type(self.table(kind), 42, os.makedev(8, 1), magic),
                    kind,
                )

    def test_linux_duplicate_device_mounts_blocked_even_whole_root_bind(self):
        raw = self.table() + self.table(identifier=43)
        self.assert_blocked(
            lambda: filesystem._linux_mount_type(raw, 42, os.makedev(8, 1), 0xEF53),
            "PHYSICAL_MOUNT_AMBIGUOUS",
        )

    def test_linux_subdirectory_bind_or_subvolume_blocked(self):
        self.assert_blocked(
            lambda: filesystem._linux_mount_type(
                self.table(root="/subvolume"), 42, os.makedev(8, 1), 0xEF53
            ),
            "PHYSICAL_MOUNT_AMBIGUOUS",
        )

    def test_linux_unknown_wrong_device_or_missing_mount_blocked(self):
        for raw, mount_id, magic in (
            (self.table("nfs"), 42, 0x6969),
            (self.table("ext3"), 42, 0xEF53),
            (self.table(), 42, 0x01021994),
            (self.table(device="8:2"), 42, 0xEF53),
            (self.table(), 43, 0xEF53),
        ):
            with self.subTest(raw=raw, mount_id=mount_id, magic=magic):
                self.assert_blocked(
                    lambda: filesystem._linux_mount_type(raw, mount_id, os.makedev(8, 1), magic)
                )

    def test_linux_malformed_duplicate_or_excess_mount_records_blocked(self):
        for raw in (
            b"",
            b"bad\n",
            self.table() + self.table(),
            self.table().replace(b"42 1", b"x 1"),
            self.table().replace(b" /fixtures ", b" relative "),
            b"x" * (filesystem._MAX_MOUNT_BYTES + 1),
        ):
            with self.subTest(length=len(raw)):
                self.assert_blocked(
                    lambda: filesystem._linux_mount_type(raw, 42, os.makedev(8, 1), 0xEF53)
                )

    def test_linux_metadata_snapshot_change_blocks(self):
        value = filesystem._LinuxStatfs()
        value.f_type = 0xEF53
        value.f_fsid[:] = (1, 2)
        fdinfo = b"mnt_id: 42\nino: 123\n"
        raw_reads = (fdinfo, self.table(), fdinfo, self.table(identifier=43))
        with (
            patch.object(filesystem, "_native_statfs", return_value=value),
            patch.object(filesystem, "_read_proc_metadata", side_effect=raw_reads),
        ):
            self.assert_blocked(
                lambda: filesystem._linux_identity(5, os.makedev(8, 1), 123),
                "PHYSICAL_MOUNT_CHANGED",
            )

    def test_procfs_failure_closes_acquired_metadata_descriptor(self):
        value = SimpleNamespace(f_type=0)
        with (
            patch.object(os, "open", return_value=101) as opened,
            patch.object(os, "close") as closed,
            patch.object(filesystem, "_native_statfs", return_value=value),
        ):
            self.assert_blocked(
                lambda: filesystem._read_proc_metadata(("mountinfo",), 32),
                "PHYSICAL_MOUNT_METADATA_UNAVAILABLE",
            )
        opened.assert_called_once()
        closed.assert_called_once_with(101)

    def test_procfs_close_failure_attempts_every_handle_once_and_blocks(self):
        value = SimpleNamespace(f_type=filesystem._PROC_MAGIC)
        with (
            patch.object(os, "open", side_effect=(101, 102, 103)),
            patch.object(os, "fstat", return_value=SimpleNamespace(st_mode=0o100400)),
            patch.object(os, "read", return_value=b""),
            patch.object(
                os, "close", side_effect=(OSError("uncertain close"), None, None)
            ) as closed,
            patch.object(filesystem, "_native_statfs", return_value=value),
        ):
            self.assert_blocked(
                lambda: filesystem._read_proc_metadata(("mountinfo",), 32),
                "PHYSICAL_METADATA_CLOSE_UNCERTAIN",
            )
        self.assertEqual([call.args[0] for call in closed.call_args_list], [103, 102, 101])

    @unittest.skipUnless(
        os.name == "posix" and sys.platform in {"darwin", "linux"},
        "Native POSIX metadata only; does not qualify Windows",
    )
    def test_native_synthetic_directory_and_file_have_same_mount_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source = root / "synthetic.txt"
            original = b"synthetic original bytes\r\n"
            source.write_bytes(original)
            root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
            file_fd = os.open(
                "synthetic.txt", os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=root_fd
            )
            try:
                left = filesystem.filesystem_identity(root_fd)
                right = filesystem.filesystem_identity(file_fd)
                self.assertEqual(left, right)
                self.assertEqual(left.device, os.fstat(file_fd).st_dev)
                self.assertEqual(os.lseek(file_fd, 0, os.SEEK_CUR), 0)
            finally:
                os.close(file_fd)
                os.close(root_fd)
            self.assertEqual(source.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
