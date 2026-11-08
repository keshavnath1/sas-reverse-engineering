"""CP3D pure/fault-injection tests; no Windows qualification or native calls.

Wire bytes are independently constructed here. Fake DLL callables never acquire
handles, inspect a real namespace, read sources or create filesystem objects.
"""

import ctypes
import importlib.util
import struct
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from sas_re import _windows_bootstrap_native as native
from sas_re._io_common import EvidenceError


def mapping_record(*names):
    return ("\x00".join(names) + "\x00\x00").encode("utf-16-le")


def fake_adapter(query):
    # Test bypass of constructor only; no production bypass parameter exists.
    result = object.__new__(native.NativeMetadata)
    result._query_mapping = query
    result._mapping_observations = 0
    return result


class DosMappingRecordUnitTests(unittest.TestCase):
    def blocked(self, raw, count):
        with self.assertRaises(EvidenceError) as caught:
            native.parse_dos_mappings(raw, count)
        self.assertEqual(caught.exception.gate, "BLOCKED")

    def test_current_and_prior_order_is_preserved(self):
        raw = mapping_record(r"\Device\HarddiskVolume4", r"\Device\HarddiskVolume3")
        self.assertEqual(native.parse_dos_mappings(raw, len(raw) // 2),
                         (r"\Device\HarddiskVolume4", r"\Device\HarddiskVolume3"))

    def test_substitution_and_duplicate_observations_are_not_identity_proof(self):
        raw = mapping_record(r"\??\D:\folder", r"\??\D:\folder")
        self.assertEqual(native.parse_dos_mappings(raw, len(raw) // 2),
                         (r"\??\D:\folder", r"\??\D:\folder"))

    def test_count_is_utf16_units_including_non_bmp_characters(self):
        raw = mapping_record("\\Device\\volume-\U0001f512")
        self.assertEqual(native.parse_dos_mappings(raw, len(raw) // 2),
                         ("\\Device\\volume-\U0001f512",))
        self.blocked(raw, len(raw))

    def test_buffer_slack_cannot_supply_missing_termination(self):
        raw = mapping_record(r"\Device\HarddiskVolume4")
        self.blocked(raw + bytes(40), len(raw) // 2 - 1)
        self.assertEqual(native.parse_dos_mappings(raw + b"x\x00", len(raw) // 2),
                         (r"\Device\HarddiskVolume4",))

    def test_truncated_odd_empty_and_oversize_buffers_block(self):
        for raw, count in ((b"", 0), (b"x", 1), (b"\x00" * 4, 2),
                           (b"\x00" * 7, 3), (bytes(65538), 32769)):
            with self.subTest(length=len(raw), count=count):
                self.blocked(raw, count)

    def test_empty_entries_and_control_characters_block(self):
        for names in (("",), ("x", ""), ("", "x"), ("x\ny",), ("x\ty",)):
            raw = mapping_record(*names)
            with self.subTest(names=names):
                self.blocked(raw, len(raw) // 2)

    def test_bad_utf16_and_wrong_input_types_block(self):
        self.blocked(b"\x00\xd8\x00\x00\x00\x00", 3)
        for raw, count in ((bytearray(mapping_record("x")), 3),
                           (mapping_record("x"), True), (mapping_record("x"), 3.0)):
            self.blocked(raw, count)

    def test_exact_entry_limit_and_excess(self):
        raw = mapping_record(*[str(index) for index in range(128)])
        self.assertEqual(len(native.parse_dos_mappings(raw, len(raw) // 2)), 128)
        raw = mapping_record(*[str(index) for index in range(129)])
        self.blocked(raw, len(raw) // 2)


class NativeMetadataCallUnitTests(unittest.TestCase):
    def test_import_is_safe_even_with_native_loader_trap(self):
        spec = importlib.util.spec_from_file_location("sas_re._cp3d_import_probe", native.__file__)
        probe = importlib.util.module_from_spec(spec)
        with patch.object(native.C, "WinDLL", create=True,
                          side_effect=AssertionError("native DLL loaded")) as loader, \
                patch.dict(native.sys.modules, {spec.name: probe}):
            spec.loader.exec_module(probe)
        loader.assert_not_called()

    def test_nonwindows_constructor_does_not_load_a_dll(self):
        with patch.object(native.sys, "platform", "darwin"), \
                patch.object(native.C, "WinDLL", create=True) as loader:
            with self.assertRaises(EvidenceError) as caught:
                native.NativeMetadata()
        self.assertEqual(caught.exception.code, "CP3D_NATIVE_UNAVAILABLE")
        loader.assert_not_called()

    def test_mock_windows_constructor_binds_only_named_mapping_api(self):
        # This is simulated platform selection, not a Windows run.
        query = Mock()
        kernel = SimpleNamespace(QueryDosDeviceW=query)
        with patch.object(native.sys, "platform", "win32"), \
                patch.object(native.os, "name", "nt"), \
                patch.object(native.platform, "machine", return_value="AMD64"), \
                patch.object(native.sys, "getwindowsversion", create=True,
                             return_value=SimpleNamespace(major=10, build=22000)), \
                patch.object(native.C, "WinDLL", create=True, return_value=kernel) as loader:
            api = native.NativeMetadata()
        loader.assert_called_once_with("kernel32.dll", use_last_error=True, winmode=0x800)
        query.assert_not_called()
        self.assertEqual(query.restype, ctypes.c_uint32)
        self.assertFalse(hasattr(api, "_open"))
        self.assertFalse(hasattr(api, "_read"))
        self.assertFalse(hasattr(api, "_ntdll"))

    def test_invalid_query_names_do_not_reach_native_call(self):
        query = Mock(side_effect=AssertionError("query must not occur"))
        api = fake_adapter(query)
        for name in (None, "", "c:", "C:\\", "\\??\\C:", "GLOBALROOT", "C:*", "C:\x00",
                     "Volume{bad}", "C:\\folder", "\\Device\\HarddiskVolume1"):
            with self.subTest(name=name), self.assertRaises(EvidenceError):
                api.mappings(name)
        query.assert_not_called()
        self.assertEqual(api._mapping_observations, 0)

    def test_one_named_fixed_buffer_call_without_fallback(self):
        record = mapping_record(r"\Device\HarddiskVolume4")

        def query(name, output, units):
            self.assertEqual(bytes(name), "C:\x00".encode("utf-16-le"))
            self.assertEqual(units, 32768)
            self.assertEqual(ctypes.sizeof(output), 65536)
            ctypes.memmove(output, record, len(record))
            return len(record) // 2

        api = fake_adapter(Mock(side_effect=query))
        self.assertEqual(api.mappings("C:"), (r"\Device\HarddiskVolume4",))
        api._query_mapping.assert_called_once()

    def test_explicit_volume_guid_query_is_not_a_drive_scan(self):
        name = "Volume{01234567-89ab-cdef-0123-456789abcdef}"
        record = mapping_record(r"\Device\HarddiskVolume4")

        def query(query_name, output, units):
            self.assertEqual(bytes(query_name), (name + "\x00").encode("utf-16-le"))
            ctypes.memmove(output, record, len(record))
            return len(record) // 2

        api = fake_adapter(query)
        self.assertEqual(api.mappings(name), (r"\Device\HarddiskVolume4",))

    def test_failed_calls_exhaust_observation_budget_without_retries(self):
        query = Mock(return_value=0)
        api = fake_adapter(query)
        for _ in range(8):
            with self.assertRaises(EvidenceError) as caught:
                api.mappings("C:")
            self.assertEqual(caught.exception.code, "CP3D_MAPPING_UNAVAILABLE")
        with self.assertRaises(EvidenceError) as caught:
            api.mappings("C:")
        self.assertEqual(caught.exception.code, "CP3D_MAPPING_OBSERVATION_LIMIT")
        self.assertEqual(query.call_count, 8)

    def test_bad_native_lengths_block_without_retry(self):
        for count in (True, 2, -1, 32769, 0xffffffff):
            query = Mock(return_value=count)
            with self.subTest(count=count), self.assertRaises(EvidenceError):
                fake_adapter(query).mappings("C:")
            query.assert_called_once()

    def test_cancellation_consumes_attempt_without_handle_or_retry(self):
        query = Mock(side_effect=KeyboardInterrupt)
        api = fake_adapter(query)
        with self.assertRaises(KeyboardInterrupt):
            api.mappings("C:")
        self.assertEqual(api._mapping_observations, 1)
        query.assert_called_once()

    def test_every_filesystem_entry_blocks_without_using_supplied_values(self):
        api = fake_adapter(Mock(side_effect=AssertionError("unexpected mapping")))
        for method, args in (("context", ()), ("open_root", (object(),)),
                             ("inspect", (object(),)), ("volume", (object(),)),
                             ("device", (object(),)), ("case_sensitive", (object(),)),
                             ("lookup", (object(), object())), ("close", (object(),))):
            with self.subTest(method=method), self.assertRaises(EvidenceError) as caught:
                getattr(api, method)(*args)
            self.assertEqual(caught.exception.code, "CP3D_NATIVE_COMPLETION_UNQUALIFIED")
            self.assertEqual(caught.exception.gate, "BLOCKED")
        api._query_mapping.assert_not_called()
        self.assertFalse(hasattr(api, "read"))
        self.assertFalse(hasattr(api, "create"))


class DeviceRecordUnitTests(unittest.TestCase):
    def test_fixed_width_fields_preserved_without_implying_locality(self):
        for device, flags in ((7, 0), (7, 0x10), (7, 0x40), (2, 0), (0xffffffff, 0xffffffff)):
            with self.subTest(device=device, flags=flags):
                actual = native.parse_device_information(struct.pack("<II", device, flags))
                self.assertEqual((actual.device_type, actual.characteristics), (device, flags))

    def test_malformed_device_records_block(self):
        for raw in (b"", bytes(7), bytes(9), bytearray(8), None):
            with self.subTest(raw=raw), self.assertRaises(EvidenceError) as caught:
                native.parse_device_information(raw)
            self.assertEqual(caught.exception.code, "CP3D_DEVICE_RECORD_INVALID")


if __name__ == "__main__":
    unittest.main()
