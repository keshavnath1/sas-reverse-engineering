"""CP3B ABI/parser/call-shape unit tests; never native Windows qualification.

These fixtures construct Windows wire records independently with struct.pack.
Fake functions stand in for DLL calls; no native source handle is opened.
"""

import ctypes
import struct
import unittest
from unittest.mock import Mock, patch

from sas_re import _windows_native as native
from sas_re._io_common import EvidenceError


def record(name, *, attributes=0x20, tag=0, next_offset=0, identifier=7, size=5):
    encoded = name.encode("utf-16-le")
    header = struct.pack("<IIqqqqqqIIII16s", next_offset, 999, 1, 2, 3, 4,
                         size, 4096, attributes, len(encoded), 0, tag,
                         identifier.to_bytes(16, "little"))
    return header + encoded


def adapter():
    # Deliberately bypass only the unavailable DLL constructor in unit fixtures.
    value = object.__new__(native.WindowsNative)
    value._owned, value._closed, value._offsets = set(), set(), {}
    value._close = Mock(return_value=1)
    return value


def object_info(*, directory=False):
    return native.ObjectInfo(native.ObjectIdentity(123, bytes([7]) * 16),
                             directory, 5, 1, False, 0x10 if directory else 0x20,
                             1, 2, 3)


class WindowsDirectoryRecordUnitTests(unittest.TestCase):
    def assert_blocked(self, raw):
        with self.assertRaises(EvidenceError) as caught:
            native.parse_directory_buffer(raw)
        self.assertEqual(caught.exception.gate, "BLOCKED")

    def test_independent_hidden_system_and_unicode_records(self):
        first = record(".hidden", attributes=0x6, next_offset=104)
        first += bytes(104 - len(first))
        entries = native.parse_directory_buffer(first + record("café.sas", identifier=8))
        self.assertEqual([e.name for e in entries], [".hidden", "café.sas"])
        self.assertEqual(entries[0].attributes, 6)
        self.assertEqual(entries[1].file_id, b"\x08" + bytes(15))

    def test_undefined_tag_normalized_only_without_reparse_attribute(self):
        self.assertEqual(native.parse_directory_buffer(record("a", tag=0x1234))[0].reparse_tag, 0)
        self.assertEqual(native.parse_directory_buffer(
            record("a", attributes=0x400, tag=0xf1234567))[0].reparse_tag, 0xf1234567)

    def test_truncated_odd_and_oversized_names_block(self):
        good = record("abc")
        for raw in (b"", good[:88], good[:-1], bytes(native.QUERY_BYTES + 1)):
            with self.subTest(length=len(raw)):
                self.assert_blocked(raw)
        for length in (0, 1, 511, 512, 0xffffffff):
            raw = bytearray(good)
            struct.pack_into("<I", raw, 60, length)
            self.assert_blocked(bytes(raw))

    def test_bad_offsets_and_duplicate_entries_block(self):
        for offset in (1, 80, 88, 97, 0xfffffff8):
            self.assert_blocked(record("abc", next_offset=offset) + bytes(104))
        first = record("abc", next_offset=96)
        self.assert_blocked(first + bytes(96 - len(first)) + record("abc", identifier=8))

    def test_bad_utf16_slashes_nul_negative_sizes_and_empty_identity_block(self):
        for name in ("a\x00b", "a/b", "a\\b"):
            self.assert_blocked(record(name))
        raw = bytearray(record("x"))
        raw[88:90] = b"\x00\xd8"
        self.assert_blocked(bytes(raw))
        self.assert_blocked(record("x", size=-1))
        self.assert_blocked(record("x", identifier=0))


class WindowsNativeCallUnitTests(unittest.TestCase):
    def test_layouts_are_fixed_width_not_host_c_long(self):
        native._check_abi()
        self.assertEqual(ctypes.sizeof(native.DWORD), 4)
        self.assertEqual(ctypes.sizeof(native.WORD), 2)
        self.assertEqual(native._OBJECT_ATTRIBUTES.SecurityDescriptor.offset, 32)
        self.assertEqual(native._FILE_ID_INFO.FileId.offset, 8)

    def test_nonwindows_constructor_fails_before_dll_loading(self):
        with patch.object(native.sys, "platform", "darwin"), \
                patch.object(native.C, "WinDLL", create=True) as loader:
            with self.assertRaises(EvidenceError) as caught:
                native.WindowsNative()
        self.assertEqual(caught.exception.code, "CP3B_NATIVE_UNAVAILABLE")
        loader.assert_not_called()

    def test_component_rejection_precedes_native_parent_inspection(self):
        api = adapter()
        api.inspect = Mock(side_effect=AssertionError("must not inspect"))
        for name in ("..", "a/b", "a\\b", "C:", "\\??\\x", "x:stream", "NUL", "a.",
                     "a ", "*", "x\x00y", "a" * 256):
            with self.subTest(name=name), self.assertRaises(EvidenceError):
                api.open_child(10, name, directory=False)
        api.inspect.assert_not_called()

    def test_exact_relative_existing_only_no_write_open_arguments(self):
        for directory, data, access, sharing, options in (
                (True, False, 0x1000a1, 7, 0x200021),
                (False, False, 0x100080, 1, 0x200060),
                (False, True, 0x100081, 1, 0x200060)):
            with self.subTest(directory=directory, data=data):
                api = adapter()
                api.inspect = Mock(side_effect=[object_info(directory=True), object_info(directory=directory)])

                def open_call(output, rights, attr_pointer, status_pointer, allocation,
                              attrs, share, disposition, flags, ea, ea_length):
                    oa = ctypes.cast(attr_pointer, ctypes.POINTER(native._OBJECT_ATTRIBUTES)).contents
                    self.assertEqual(oa.RootDirectory, 10)
                    self.assertEqual(oa.Attributes, 0x40)
                    self.assertEqual((rights, share, disposition, flags), (access, sharing, 1, options))
                    self.assertEqual((allocation, attrs, ea, ea_length), (None, 0, None, 0))
                    string = oa.ObjectName.contents
                    self.assertEqual(ctypes.string_at(string.Buffer, string.Length), "café.sas".encode("utf-16-le"))
                    ctypes.cast(output, ctypes.POINTER(native.HANDLE))[0] = 20
                    iosb = ctypes.cast(status_pointer, ctypes.POINTER(native._IO_STATUS_BLOCK)).contents
                    iosb.Result.Status, iosb.Information = 0, 1
                    return 0

                api._open = open_call
                self.assertEqual(api.open_child(10, "café.sas", directory=directory, read_data=data), 20)
                self.assertEqual(20 in api._offsets, data)
                api.close(20)
                self.assertFalse(api._owned)

    def test_failed_positive_status_and_cancellation_close_returned_handle(self):
        for status in (0x103, 1, -1073741790, "cancel"):
            api = adapter()
            api.inspect = Mock(return_value=object_info(directory=True))

            def open_call(output, *unused):
                ctypes.cast(output, ctypes.POINTER(native.HANDLE))[0] = 21
                if status == "cancel":
                    raise KeyboardInterrupt()
                return status

            api._open = open_call
            exception = KeyboardInterrupt if status == "cancel" else EvidenceError
            with self.subTest(status=status), self.assertRaises(exception):
                api.open_child(10, "a.sas", directory=False)
            self.assertEqual(api._close.call_count, 1)
            self.assertEqual(api._close.call_args.args[0].value, 21)
            self.assertFalse(api._owned)

    def test_postopen_inspection_failure_closes_handle(self):
        api = adapter()
        api.inspect = Mock(side_effect=[object_info(directory=True), EvidenceError("CP3B_REPARSE_POINT", "BLOCKED")])

        def open_call(output, rights, attrs, status_pointer, *unused):
            ctypes.cast(output, ctypes.POINTER(native.HANDLE))[0] = 22
            iosb = ctypes.cast(status_pointer, ctypes.POINTER(native._IO_STATUS_BLOCK)).contents
            iosb.Information = 1
            return 0

        api._open = open_call
        with self.assertRaisesRegex(EvidenceError, "CP3B_REPARSE_POINT"):
            api.open_child(10, "a.sas", directory=False)
        self.assertEqual(api._close.call_count, 1)
        self.assertFalse(api._owned)

    def test_nonregular_inheritable_and_protected_handles_block_before_metadata(self):
        for object_type, flags in ((0, 0), (2, 0), (3, 0), (1, 1), (1, 2), (1, 4)):
            api = adapter()
            api._type = Mock(return_value=object_type)

            def handle_info(handle, output):
                ctypes.cast(output, ctypes.POINTER(native.DWORD))[0] = flags
                return 1

            api._handle_info = handle_info
            api._query = Mock(side_effect=AssertionError("must not query"))
            with self.subTest(object_type=object_type, flags=flags), self.assertRaises(EvidenceError):
                api.inspect(10)
            api._query.assert_not_called()

    def test_read_preserves_bytes_offsets_and_no_metadata_handle_access(self):
        api = adapter()
        api._offsets[20] = 0
        original = b"\xef\xbb\xbfdata x;\r\nrun;\n\xff"

        def read_call(handle, buffer, limit, count_pointer, position_pointer):
            position = ctypes.cast(position_pointer, ctypes.POINTER(native._OVERLAPPED)).contents
            offset = position.Offset + (position.OffsetHigh << 32)
            value = original[offset:offset + limit]
            ctypes.memmove(buffer, value, len(value))
            ctypes.cast(count_pointer, ctypes.POINTER(native.DWORD))[0] = len(value)
            return 1

        api._read = Mock(side_effect=read_call)
        self.assertEqual(api.read(20, 4) + api.read(20, 65536), original)
        api.rewind(20)
        self.assertEqual(api.read(20, 65536), original)
        calls = api._read.call_count
        for handle, count in ((10, 1), (20, 0), (20, 65537), (20, True)):
            with self.assertRaises(EvidenceError):
                api.read(handle, count)
        self.assertEqual(api._read.call_count, calls)

    def test_close_failure_removes_data_authority_and_never_retries(self):
        api = adapter()
        api._owned.add(20)
        api._offsets[20] = 0
        api._close.return_value = 0
        with self.assertRaisesRegex(EvidenceError, "CP3B_CLOSE_UNCERTAIN"):
            api.close(20)
        self.assertFalse(api._owned)
        self.assertFalse(api._offsets)
        with self.assertRaisesRegex(EvidenceError, "CP3B_HANDLE_CLOSED"):
            api.close(20)
        self.assertEqual(api._close.call_count, 1)

    def test_enumeration_restart_continuation_and_exact_termination(self):
        api = adapter()
        api.inspect = Mock(return_value=object_info(directory=True))
        calls = []

        def query(handle, kind, buffer, length):
            calls.append(kind)
            if len(calls) == 3:
                return 0
            value = record("hidden" if kind == 20 else "system", attributes=6,
                           identifier=len(calls))
            ctypes.memmove(buffer, value, len(value))
            return 1

        api._query = query
        with patch.object(native.C, "get_last_error", return_value=18, create=True):
            self.assertEqual([e.name for e in api.entries(10)], ["hidden", "system"])
        self.assertEqual(calls, [20, 19, 19])
        api._query = Mock(return_value=0)
        with patch.object(native.C, "get_last_error", return_value=5, create=True):
            with self.assertRaisesRegex(EvidenceError, "CP3B_ENUMERATION_UNAVAILABLE"):
                api.entries(10)

    def test_only_valid_structural_directory_entries_are_filtered(self):
        for name, attributes, identifier, valid in (
                (".", 0x10, int.from_bytes(bytes([7]) * 16, "little"), True),
                ("..", 0x10, 1, True), (".", 0x10, 1, False),
                ("..", 0x20, 1, False), ("..", 0x410, 1, False)):
            api = adapter()
            api.inspect = Mock(return_value=object_info(directory=True))
            calls = []

            def query(handle, kind, buffer, length):
                calls.append(kind)
                if len(calls) > 1:
                    return 0
                raw = record(name, attributes=attributes, identifier=identifier)
                ctypes.memmove(buffer, raw, len(raw))
                return 1

            api._query = query
            with self.subTest(name=name, valid=valid), \
                    patch.object(native.C, "get_last_error", return_value=18, create=True):
                if valid:
                    self.assertEqual(api.entries(10), ())
                else:
                    with self.assertRaisesRegex(EvidenceError, "CP3B_DIRECTORY_RECORD_INVALID"):
                        api.entries(10)

    def test_reused_handle_on_failed_open_still_closed_once_for_new_acquisition(self):
        api = adapter()
        api.close(21)
        api.inspect = Mock(return_value=object_info(directory=True))

        def open_call(output, *unused):
            ctypes.cast(output, ctypes.POINTER(native.HANDLE))[0] = 21
            return 0x103

        api._open = open_call
        with self.assertRaisesRegex(EvidenceError, "CP3B_OPEN_UNAVAILABLE"):
            api.open_child(10, "a.sas", directory=False)
        self.assertEqual(api._close.call_count, 2)  # Once for each OS acquisition.

    def test_aggregate_record_bound_includes_filtered_structural_entries(self):
        # Separate native query batches prevent the per-buffer parser bound from
        # masking an aggregate accounting error after dot records are filtered.
        for extra_record in (False, True):
            api = adapter()
            api.inspect = Mock(return_value=object_info(directory=True))
            records = [
                record(".", attributes=0x10, identifier=int.from_bytes(bytes([7]) * 16, "little")),
                record("..", attributes=0x10, identifier=1),
                record("a.sas", identifier=2),
            ]
            if extra_record:
                records.append(record("b.sas", identifier=3))
            calls = []

            def query(handle, kind, buffer, length):
                index = len(calls)
                calls.append(kind)
                if index == len(records):
                    return 0
                ctypes.memmove(buffer, records[index], len(records[index]))
                return 1

            api._query = query
            with self.subTest(extra_record=extra_record), \
                    patch.object(native, "MAX_ENTRIES", 3), \
                    patch.object(native.C, "get_last_error", return_value=18, create=True):
                if extra_record:
                    with self.assertRaisesRegex(EvidenceError, "CP3B_ENUMERATION_INCOMPLETE") as caught:
                        api.entries(10)
                    self.assertEqual(caught.exception.gate, "BLOCKED")
                else:
                    self.assertEqual([entry.name for entry in api.entries(10)], ["a.sas"])
            self.assertEqual(calls, [20, 19, 19, 19])

    def test_native_metadata_reparse_hardlink_and_inconsistency_refusals(self):
        for mutation, code in (
                ({"attributes": 0x420}, "CP3B_REPARSE_POINT"),
                ({"attributes": 0x1020}, "CP3B_OBJECT_UNSUPPORTED"),
                ({"links": 2}, "CP3B_HARDLINK_UNSAFE"),
                ({"pending": 1}, "CP3B_METADATA_INCONSISTENT"),
                ({"directory": 1}, "CP3B_METADATA_INCONSISTENT"),
                ({"size": -1}, "CP3B_METADATA_INCONSISTENT"),
                ({"serial": 0}, "CP3B_IDENTITY_UNAVAILABLE")):
            api = adapter()
            api._type = Mock(return_value=1)
            api._handle_info = Mock(return_value=1)
            values = {"attributes": 0x20, "links": 1, "pending": 0,
                      "directory": 0, "size": 5, "serial": 123} | mutation

            def query(handle, kind, output, size):
                if kind == 9:
                    raw = struct.pack("<II", values["attributes"], 0xf1234567)
                elif kind == 18:
                    raw = struct.pack("<Q16s", values["serial"], bytes([7]) * 16)
                elif kind == 1:
                    raw = struct.pack("<qqIBBxx", 4096, values["size"], values["links"],
                                      values["pending"], values["directory"])
                else:
                    raw = struct.pack("<qqqqIxxxx", 1, 2, 3, 4, values["attributes"])
                ctypes.memmove(output, raw, len(raw))
                return 1

            api._query = query
            with self.subTest(mutation=mutation), self.assertRaisesRegex(EvidenceError, code):
                api.inspect(10)

    def test_volume_query_reports_only_exact_ntfs_and_never_equates_serial_widths(self):
        for filesystem, serial, maximum, flags, valid in (
                ("NTFS", 123, 255, 8, True), ("ReFS", 123, 255, 8, False),
                ("NTFS", 0, 255, 8, False), ("NTFS", 123, 256, 8, False),
                ("NTFS", 123, 255, 0, False)):
            api = adapter()

            def volume(handle, label, label_size, serial_ptr, maximum_ptr, flags_ptr, name, size):
                ctypes.cast(serial_ptr, ctypes.POINTER(native.DWORD))[0] = serial
                ctypes.cast(maximum_ptr, ctypes.POINTER(native.DWORD))[0] = maximum
                ctypes.cast(flags_ptr, ctypes.POINTER(native.DWORD))[0] = flags
                raw = filesystem.encode("utf-16-le")
                ctypes.memmove(name, raw, len(raw))
                return 1

            api._volume = volume
            with self.subTest(filesystem=filesystem, serial=serial, maximum=maximum, flags=flags):
                if valid:
                    self.assertEqual(api.volume(10), native.VolumeInfo("NTFS", 123, 255, 8))
                else:
                    with self.assertRaisesRegex(EvidenceError, "CP3B_VOLUME_UNSUPPORTED"):
                        api.volume(10)


if __name__ == "__main__":
    unittest.main()
