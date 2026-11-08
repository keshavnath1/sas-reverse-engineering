"""CP3B simulated/unit-only reader obligations; zero native qualification claims.

The in-memory fixture is independently authored and has no filesystem bridge.
There are no skipped native tests: unavailable Windows obligations stay BLOCKED
in the qualification report and public capability gate.
"""

from contextlib import ExitStack, contextmanager, redirect_stdout
from copy import deepcopy
from dataclasses import replace
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import textwrap
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from cp2_vectors import (EXPECTED_IDENTITIES, EXPECTED_SCOPE_SHA256, RAW_OTHER,
                         RAW_VARIANTS, envelope, operation_payload, oracle_files,
                         oracle_hash, oracle_id)
from sas_re._io_common import EvidenceError
from sas_re._windows_preflight import WindowsPreflight, _request_windows
from sas_re.authorization import authorization_scope_identity, validate_authorization
from sas_re import platform_io
from sas_re.cli import main
from sas_re.preflight import LocalInspectionPolicy, open_preflight
from windows_fake import FakeWindows, REPARSE


@contextmanager
def no_external_io():
    """The candidate protocol may use the fake only; no Python-path fallback."""
    with ExitStack() as stack:
        for name in ("builtins.open", "io.open", "os.open", "os.mkdir", "os.makedirs",
                     "os.unlink", "os.rename", "os.replace", "subprocess.Popen",
                     "socket.socket"):
            stack.enter_context(patch(name, side_effect=AssertionError(
                "Unit-only protocol attempted filesystem/process/network access: " + name)))
        yield


class WindowsPreflightSimulatedTests(unittest.TestCase):
    def setUp(self):
        self.value = envelope("windows")
        validate_authorization(self.value, expected_platform="windows")
        self.api = FakeWindows(self)

    def policy(self, **changes):
        values = dict(anchor="C:\\Synthetic",
                      source_roots=tuple((item["root_id"], item["path"])
                                         for item in self.value["bindings"]),
                      store_path="C:\\Synthetic\\NewOutput\\store",
                      workspace_id=self.value["logical_scope"]["workspace_id"],
                      run_id=self.value["logical_scope"]["run_id"],
                      scope_sha256=authorization_scope_identity(self.value),
                      source_model="QUIESCENT_SYNTHETIC_TRUSTED_WRITERS")
        values.update(changes)
        return LocalInspectionPolicy(**values)

    def session(self, *, policy=None):
        # Test seam only: independently supplied fake volume-root handle. The
        # public API has no root-handle injection or qualification override.
        return WindowsPreflight(self.api, self.api.root_handle, self.value,
                                self.policy() if policy is None else policy,
                                ("C:", "Synthetic"))

    def blocked(self, action, *, code=None, reads=False):
        with no_external_io(), self.assertRaises(EvidenceError) as caught:
            action()
        self.assertEqual(caught.exception.gate, "BLOCKED")
        self.assertTrue(caught.exception.code.startswith("CP3B_"))
        if code is not None:
            self.assertEqual(caught.exception.code, code)
        self.assertNotIn("C:\\", str(caught.exception))
        self.assertFalse(self.api.active, "Every fake retained handle must close")
        self.assertEqual(len(self.api.closed), len(set(self.api.closed)))
        if not reads:
            self.assertFalse(self.api.reads())

    def read(self, *, policy=None):
        with no_external_io(), self.session(policy=policy) as session:
            self.assertEqual(session.state, "READY")
            result = session.read_sources()
            self.assertEqual(session.state, "CLOSED")
        self.assertFalse(self.api.active)
        return result

    def test_positive_original_bytes_all_handles_barrier_and_no_source_mutation(self):
        before = self.api.snapshot()
        self.assertEqual(self.read(), self.api.expected)
        self.assertEqual(self.api.snapshot(), before)
        self.assertTrue(self.api.reads())
        self.assertIs(self.api.anchor.children["NewOutput"], self.api.output_parent)
        self.assertFalse(self.api.store.children)
        self.assertEqual(len(self.api.closed), len(set(self.api.closed)))

    def test_ready_is_metadata_and_handle_acquisition_without_source_content(self):
        with no_external_io(), self.session() as session:
            self.assertEqual(session.state, "READY")
            self.assertEqual(len(self.api.data_opens()), 3)
            self.assertFalse(self.api.reads())
        self.assertFalse(self.api.active)

    def test_existing_sibling_store_is_inspected_without_content_or_mutation(self):
        store = self.api.node("Historical", directory=True)
        seal = self.api.node("manifest.json", data=b'{"authority":"DRAFT"}\n')
        store.children["manifest.json"] = seal
        self.api.anchor.children["Historical"] = store
        before = self.api.snapshot()
        self.assertEqual(self.read(policy=self.policy(store_path="C:\\Synthetic\\Historical")),
                         self.api.expected)
        self.assertEqual(self.api.snapshot(), before)
        self.assertFalse(any(event[0] == "open" and event[2] == "manifest.json"
                             for event in self.api.events))

    def test_root_physical_equality_is_rejected(self):
        self.api.anchor.children["Logs"] = self.api.source
        self.blocked(self.session)

    def test_store_physical_alias_equal_to_source_is_rejected(self):
        self.api.anchor.children["Alias"] = self.api.source
        self.blocked(lambda: self.session(policy=self.policy(store_path="C:\\Synthetic\\Alias")))

    def test_store_inside_source_stops_before_descending(self):
        self.blocked(lambda: self.session(policy=self.policy(
            store_path="C:\\Synthetic\\Sources\\includes\\output")))
        self.assertFalse(any(event[0] == "open" and event[2] in {"includes", "output"}
                             for event in self.api.events))

    def test_store_ancestor_of_source_is_rejected(self):
        self.blocked(lambda: self.session(policy=self.policy(store_path="C:\\Synthetic")))

    def test_reparse_volume_root_is_rejected_before_child_open(self):
        self.api.root.attributes |= REPARSE
        self.api.root.reparse_tag = 0xA0000003
        self.blocked(self.session)
        self.assertFalse(any(event[0] == "open" for event in self.api.events))

    def test_reparse_anchor_is_rejected_before_descending(self):
        self.api.anchor.attributes |= REPARSE
        self.api.anchor.reparse_tag = 0xA000000C
        self.blocked(self.session)
        self.assertFalse(any(event[0] == "open" and event[2] in {"Sources", "Logs"}
                             for event in self.api.events))

    def test_reparse_source_root_is_rejected_before_source_descendants(self):
        self.api.source.attributes |= REPARSE
        self.api.source.reparse_tag = 0xA0000003
        self.blocked(self.session)
        self.assertFalse(any(event[0] == "open" and event[2] == "main.sas"
                             for event in self.api.events))

    def test_reparse_intermediate_is_rejected_before_leaf_open(self):
        self.api.includes.attributes |= REPARSE
        self.api.includes.reparse_tag = 0x8000001B
        self.blocked(self.session)
        self.assertFalse(any(event[0] == "open" and event[2] == "common.sas"
                             for event in self.api.events))

    def test_reparse_leaf_known_and_unknown_tags_are_rejected(self):
        for tag in (0xA000000C, 0xA0000003, 0x8000001B, 0xDEADBEEF):
            with self.subTest(tag=tag):
                self.api = FakeWindows(self)
                self.api.files["src:main.sas"].attributes |= REPARSE
                self.api.files["src:main.sas"].reparse_tag = tag
                self.blocked(self.session)

    def test_nonzero_reparse_tag_without_attribute_is_ambiguous(self):
        self.api.files["src:main.sas"].reparse_tag = 0xDEADBEEF
        self.blocked(self.session)

    def test_unsupported_volume_filesystems_are_blocked(self):
        for name in ("ReFS", "FAT32", "exFAT", "SMB", "", "ntfs"):
            with self.subTest(filesystem=name):
                self.api = FakeWindows(self)
                self.api.root.filesystem = name
                self.blocked(self.session)

    def test_source_volume_change_is_blocked(self):
        self.api.files["src:main.sas"].serial += 1
        self.blocked(self.session)

    def test_identity_volume_mismatch_with_same_low_serial_is_blocked(self):
        self.api.files["src:main.sas"].serial += 1 << 32
        self.blocked(self.session)

    def test_zero_file_identity_is_ambiguous(self):
        self.api.files["src:main.sas"].number = 0
        self.blocked(self.session)

    def test_duplicate_file_identity_is_rejected(self):
        self.api.files["src:main.sas"].number = self.api.files["logs:run.log"].number
        self.blocked(self.session)

    def test_hardlinks_and_delete_pending_are_rejected(self):
        for field, value in (("links", 0), ("links", 2), ("delete_pending", True)):
            with self.subTest(field=field, value=value):
                self.api = FakeWindows(self)
                setattr(self.api.files["src:main.sas"], field, value)
                self.blocked(self.session)

    def test_unexpected_file_including_hidden_system_entries_is_rejected(self):
        for name, attributes in (("other.sas", 0), (".hidden", 2), ("System", 4)):
            with self.subTest(name=name):
                self.api = FakeWindows(self)
                extra = self.api.node(name, data=b"must never be read")
                extra.attributes = attributes
                self.api.source.children[name] = extra
                self.blocked(self.session)
                self.assertFalse(any(event[0] == "open" and event[2] == name
                                     for event in self.api.events))

    def test_unexpected_empty_directory_is_not_descended(self):
        self.api.source.children["Unauthorized"] = self.api.node("Unauthorized", directory=True)
        self.blocked(self.session)
        self.assertFalse(any(event[0] == "open" and event[2] == "Unauthorized"
                             for event in self.api.events))

    def test_missing_declared_file_has_zero_data_opens(self):
        del self.api.source.children["main.sas"]
        self.blocked(self.session)
        self.assertFalse(self.api.data_opens())

    def test_duplicate_enumeration_record_is_rejected(self):
        self.api.entries_override = lambda node, entries: entries + entries[:1]
        self.blocked(self.session)

    def test_case_alias_enumeration_is_not_silently_normalized(self):
        self.api.source.children["MAIN.SAS"] = self.api.source.children.pop("main.sas")
        self.blocked(self.session)

    def test_directory_record_identity_mismatch_is_rejected(self):
        self.api.entries_override = lambda node, entries: tuple(
            replace(entry, file_id=b"\xff" * 16) if entry.name == "main.sas" else entry
            for entry in entries)
        self.blocked(self.session)

    def test_denied_directory_listing_has_zero_content_reads(self):
        self.api.includes.deny_entries = True
        self.blocked(self.session)

    def test_denied_last_metadata_file_has_zero_data_opens(self):
        self.api.files["src:main.sas"].deny_metadata = True
        self.blocked(self.session)
        self.assertFalse(self.api.data_opens())

    def test_denied_last_data_file_has_zero_earlier_file_reads(self):
        self.api.files["src:main.sas"].deny_data = True
        self.blocked(self.session)
        attempts = self.api.data_opens()
        self.assertEqual(len(attempts), 3)
        self.assertEqual(attempts[-1][2], "main.sas")

    def test_nonregular_or_native_unsafe_object_is_blocked(self):
        self.api.files["src:main.sas"].native_unsafe = True
        self.blocked(self.session)

    def test_leaf_replacement_during_read_handle_acquisition_is_blocked(self):
        def replace_before_data(operation, *arguments):
            if operation == "open" and arguments[1] == "main.sas" and arguments[3]:
                self.api.source.children["main.sas"] = self.api.node("main.sas", data=b"outside")
        self.api.before = replace_before_data
        self.blocked(self.session)

    def test_root_replacement_after_ready_is_blocked_before_bytes(self):
        session = self.session()
        self.api.anchor.children["Sources"] = self.api.node("Sources", directory=True)
        self.blocked(session.read_sources)

    def test_intermediate_replacement_after_ready_is_blocked_before_bytes(self):
        session = self.session()
        self.api.source.children["includes"] = self.api.node("includes", directory=True)
        self.blocked(session.read_sources)

    def test_added_hardlink_after_ready_is_blocked_before_bytes(self):
        session = self.session()
        self.api.files["src:main.sas"].links = 2
        self.blocked(session.read_sources)

    def test_replaced_store_parent_after_ready_is_blocked_before_bytes(self):
        session = self.session()
        self.api.anchor.children["NewOutput"] = self.api.node("NewOutput", directory=True)
        self.blocked(session.read_sources)

    def test_absent_store_is_unproven_and_remains_absent_without_content_reads(self):
        del self.api.anchor.children["NewOutput"]
        before = self.api.snapshot()
        self.blocked(self.session, code="CP3B_STORE_ABSENCE_UNPROVEN")
        self.assertFalse(self.api.data_opens())
        self.assertNotIn("NewOutput", self.api.anchor.children)
        self.assertEqual(self.api.snapshot(), before)

    def test_store_case_alias_is_not_treated_as_absence(self):
        self.blocked(lambda: self.session(policy=self.policy(
            store_path="C:\\Synthetic\\newoutput\\store")), code="CP3B_NAME_AMBIGUOUS")

    def test_same_length_mutation_with_restored_mtime_during_read_is_detected(self):
        changed = False
        def mutate_after_read(operation, result, *arguments):
            nonlocal changed
            if operation == "read" and result and not changed:
                node = self.api.active[arguments[0]][0]
                node.data = b"x" * len(node.data)
                node.changed += 1
                changed = True
        self.api.after = mutate_after_read
        self.blocked(lambda: self.session().read_sources(), reads=True)
        self.assertTrue(changed)

    def test_second_byte_pass_detects_changed_bytes_with_all_timestamps_restored(self):
        changed = False
        def mutate_at_rewind(operation, *arguments):
            nonlocal changed
            if (operation == "rewind" and not changed
                    and any(event[1] == arguments[0] for event in self.api.reads())):
                node = self.api.active[arguments[0]][0]
                node.data = b"x" * len(node.data)
                changed = True
        self.api.before = mutate_at_rewind
        self.blocked(lambda: self.session().read_sources(), reads=True)
        self.assertTrue(changed)

    def test_empty_regular_source_is_read_without_inventing_bytes(self):
        self.api.files["src:main.sas"].data = b""
        self.assertEqual(self.read(), {**self.api.expected, "src:main.sas": b""})

    def test_negative_and_oversize_file_lengths_block_before_data_open(self):
        for size in (-1, 8 * 1024 * 1024 + 1):
            with self.subTest(size=size):
                self.api = FakeWindows(self)
                self.api.files["src:main.sas"].reported_size = size
                self.blocked(self.session)
                self.assertFalse(self.api.data_opens())

    def test_read_oserror_and_cancellation_release_every_handle(self):
        for exception in (OSError("synthetic read failure"), KeyboardInterrupt()):
            with self.subTest(exception=type(exception).__name__):
                self.api = FakeWindows(self)
                session = self.session()
                def fail_on_read(operation, *arguments):
                    if operation == "read":
                        raise exception
                self.api.before = fail_on_read
                if isinstance(exception, KeyboardInterrupt):
                    with no_external_io(), self.assertRaises(KeyboardInterrupt):
                        session.read_sources()
                    self.assertFalse(self.api.active)
                else:
                    self.blocked(session.read_sources, reads=True)

    def test_context_cancellation_closes_handles_without_reading(self):
        with self.assertRaises(KeyboardInterrupt), no_external_io(), self.session():
            raise KeyboardInterrupt()
        self.assertFalse(self.api.active)
        self.assertFalse(self.api.reads())

    def test_uncertain_close_blocks_success_attempts_every_handle_once(self):
        session = self.session()
        retained = set(self.api.active)
        self.api.close_failure = True
        self.blocked(session.read_sources, reads=True)
        self.assertTrue(retained <= set(self.api.closed))
        session.close()
        self.assertEqual(len(self.api.closed), len(set(self.api.closed)))

    def test_native_evidence_error_on_close_still_attempts_all_handles(self):
        session = self.session()
        retained = set(self.api.active)
        original = self.api.close
        once = True
        def close_then_report(handle):
            nonlocal once
            original(handle)
            if once:
                once = False
                raise EvidenceError("CP3B_NATIVE_CLOSE_UNCERTAIN", "BLOCKED")
        self.api.close = close_then_report
        self.blocked(session.read_sources, reads=True)
        self.assertTrue(retained <= set(self.api.closed))

    def test_handle_bound_closes_the_just_acquired_handle_too(self):
        with patch("sas_re._windows_preflight.MAX_HANDLES", 2):
            self.blocked(self.session)
        self.assertGreaterEqual(len(self.api.closed), 3)

    def test_total_byte_limit_has_exact_positive_and_negative_boundary(self):
        total = sum(len(value) for value in self.api.expected.values())
        with patch("sas_re._windows_preflight.MAX_TOTAL_BYTES", total):
            self.assertEqual(self.read(), self.api.expected)
        self.api = FakeWindows(self)
        with patch("sas_re._windows_preflight.MAX_TOTAL_BYTES", total - 1):
            self.blocked(self.session)
        self.assertFalse(self.api.data_opens())

    def test_file_directory_and_depth_limits_fail_without_content(self):
        for constant, bound in (("MAX_FILES", 2), ("MAX_DIRECTORIES", 0), ("MAX_DEPTH", 0)):
            with self.subTest(constant=constant):
                self.api = FakeWindows(self)
                with patch("sas_re._windows_preflight." + constant, bound):
                    self.blocked(self.session)

    def test_oversize_and_wrong_type_read_results_are_blocked(self):
        for bad_result in (b"x" * 65537, bytearray(b"x")):
            with self.subTest(kind=type(bad_result).__name__):
                self.api = FakeWindows(self)
                session = self.session()
                self.api.read = lambda handle, count: bad_result
                self.blocked(session.read_sources, reads=True)

    def test_caller_mutation_after_ready_cannot_change_bound_scope(self):
        session = self.session()
        self.value["logical_scope"]["files"].clear()
        self.value["bindings"][0]["path"] = "D:\\Unapproved\\root"
        self.assertEqual(session.read_sources(), self.api.expected)
        self.assertFalse(self.api.active)

    def test_scope_policy_mismatch_closes_bootstrap_handle_before_metadata(self):
        self.blocked(lambda: self.session(policy=self.policy(run_id="wrong-run")))
        self.assertEqual([event[0] for event in self.api.events], ["close"])

    def test_pure_windows_request_detaches_declarations_without_physical_authority(self):
        before = deepcopy(self.value)
        with no_external_io():
            detached, anchor = _request_windows(self.value, self.policy())
        self.assertEqual(anchor, ("C:", "Synthetic"))
        self.assertEqual(detached, before)
        detached["logical_scope"]["files"].clear()
        self.assertEqual(self.value, before)
        self.assertEqual(self.value["authorization"]["human_approval"], "NOT_VERIFIED")
        self.assertFalse(self.api.events)
        self.api.close(self.api.root_handle)

    def test_unrelated_volume_entries_are_not_enumerated_during_bootstrap(self):
        self.api.root.children["Unapproved sibling"] = self.api.node("Unapproved sibling", directory=True)
        root_handle = self.api.root_handle
        def no_root_enumeration(operation, *arguments):
            if operation == "entries" and arguments[0] == root_handle:
                self.fail("Bootstrap enumerated volume entries outside the dedicated anchor")
        self.api.before = no_root_enumeration
        self.assertEqual(self.read(), self.api.expected)

    def test_success_is_single_use_and_provides_no_publication_api(self):
        session = self.session()
        self.assertEqual(session.read_sources(), self.api.expected)
        self.blocked(session.read_sources, reads=True)
        self.assertFalse(hasattr(session, "publish"))
        self.assertFalse(hasattr(session, "create_store"))

    def test_original_byte_vectors_preserve_cross_platform_cp2_identities(self):
        for variant, raw in RAW_VARIANTS.items():
            with self.subTest(variant=variant):
                self.api = FakeWindows(self, variant)
                actual = self.read()
                self.assertEqual(actual, {"src:main.sas": raw, **RAW_OTHER})
                expected = EXPECTED_IDENTITIES[variant]
                self.assertEqual(hashlib.sha256(actual["src:main.sas"]).hexdigest(),
                                 expected["main_sha256"])
                self.assertEqual(authorization_scope_identity(self.value), EXPECTED_SCOPE_SHA256)
                self.assertEqual(authorization_scope_identity(envelope("posix")), EXPECTED_SCOPE_SHA256)
                files = oracle_files(variant)
                for entry in files:
                    self.assertEqual(hashlib.sha256(actual[entry["file_key"]]).hexdigest(),
                                     entry["sha256"])
                fingerprint = oracle_hash({"scope_sha256": EXPECTED_SCOPE_SHA256, "files": files})
                self.assertEqual(fingerprint, expected["source_fingerprint"])
                self.assertEqual(oracle_id("op", fingerprint, operation_payload()), expected["operation_id"])

    def test_simulated_windows_public_entry_still_denies_before_any_path_access(self):
        # No native environment is claimed by patching platform detection.
        with patch("sys.platform", "win32"), no_external_io(), \
                patch("sas_re._windows_native.WindowsNative", side_effect=AssertionError("Native load")), \
                patch("sas_re._windows_preflight.WindowsPreflight", side_effect=AssertionError("Reader load")), \
                self.assertRaises(EvidenceError) as caught:
            open_preflight(self.value, policy=self.policy())
        self.assertEqual(caught.exception.gate, "BLOCKED")
        self.assertEqual(caught.exception.code, "FILESYSTEM_CAPABILITY_UNAVAILABLE")
        self.assertEqual(len(self.api.events), 0)
        self.api.close(self.api.root_handle)


class WindowsReaderCapabilityUnitTests(unittest.TestCase):
    """Runtime-selection simulation only; no Windows host is exercised."""

    def test_windows_report_is_pure_and_keeps_reader_and_publication_blocked(self):
        with patch("sys.platform", "win32"), no_external_io(), \
                patch("sas_re.platform_io.import_module", side_effect=AssertionError("Native import")):
            result = platform_io.preflight_capabilities()
            full = platform_io.filesystem_capabilities()
        self.assertEqual(result["read_only_preflight"], "BLOCKED")
        self.assertEqual(result["native_qualification"], "BLOCKED")
        self.assertEqual(result["volume_bootstrap"], "NOT_IMPLEMENTED")
        self.assertEqual(result["private_protocol"], "IMPLEMENTED_UNQUALIFIED")
        self.assertEqual(result["publication"], "BLOCKED")
        self.assertEqual(full["evidence_io"], "BLOCKED")
        self.assertEqual(set(full["capabilities"].values()), {"BLOCKED"})
        json.dumps(result, allow_nan=False)

    def test_nt_os_name_alone_cannot_choose_a_posix_reader(self):
        with patch("sys.platform", "linux"), \
                patch.object(platform_io, "os", SimpleNamespace(name="nt")), no_external_io():
            result = platform_io.preflight_capabilities()
        self.assertEqual(result["backend"], "windows")
        self.assertEqual(result["read_only_preflight"], "BLOCKED")

    def test_mutating_report_or_environment_does_not_enable_a_backend(self):
        with patch("sys.platform", "win32"), no_external_io(), \
                patch.dict(os.environ, {"SAS_RE_BACKEND": "posix", "SAS_RE_WINDOWS_APPROVED": "1"}):
            result = platform_io.preflight_capabilities()
            result.update(read_only_preflight="AVAILABLE", native_qualification="PASS",
                          volume_bootstrap="APPROVED", publication="AVAILABLE")
            again = platform_io.preflight_capabilities()
            self.assertEqual(again["read_only_preflight"], "BLOCKED")
            self.assertEqual(again["native_qualification"], "BLOCKED")
            with self.assertRaises(EvidenceError) as caught:
                platform_io.get_backend()
        self.assertEqual(caught.exception.code, "FILESYSTEM_CAPABILITY_UNAVAILABLE")
        self.assertEqual(caught.exception.gate, "BLOCKED")

    def test_unknown_platform_reader_is_blocked_without_loading_backend(self):
        with patch("sys.platform", "unqualified-unit-target"), no_external_io(), \
                patch.object(platform_io, "os", SimpleNamespace(name="posix")), \
                patch("sas_re.platform_io.import_module", side_effect=AssertionError("Backend import")):
            result = platform_io.preflight_capabilities()
        self.assertEqual(result["read_only_preflight"], "BLOCKED")
        self.assertEqual(result["reason"], "PLATFORM_NOT_SUPPORTED")

    def test_posix_reader_report_preserves_full_capability_gate(self):
        for state in ("AVAILABLE", "BLOCKED"):
            with self.subTest(state=state), patch("sys.platform", "darwin"), \
                    patch.object(platform_io, "os", SimpleNamespace(name="posix")), no_external_io(), \
                    patch.object(platform_io, "filesystem_capabilities", return_value={
                        "backend": "posix" if state == "AVAILABLE" else "blocked",
                        "evidence_io": state, "reason": None if state == "AVAILABLE" else "UNIT_DENIED"}):
                self.assertEqual(platform_io.preflight_capabilities()["read_only_preflight"], state)

    def test_simulated_windows_cli_status_reports_no_new_authority(self):
        # CLI status reads trusted installed metadata, never caller source paths.
        output = io.StringIO()
        with patch("sys.platform", "win32"), redirect_stdout(output), \
                patch("subprocess.Popen", side_effect=AssertionError("Process launch")), \
                patch("socket.socket", side_effect=AssertionError("Network use")):
            code = main(["status"])
        self.assertEqual(code, 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result["read_only_preflight_capabilities"]["read_only_preflight"], "BLOCKED")
        self.assertEqual(result["filesystem_capabilities"]["evidence_io"], "BLOCKED")
        self.assertEqual(result["semantic_acceptance"], "BLOCKED")
        self.assertEqual(result["semantic_verification"], "UNVERIFIABLE")
        self.assertEqual(result["artifact_authority"], "DRAFT")
        self.assertEqual(result["benchmark_execution"], "NOT_RUN")

    def test_fresh_windows_selection_imports_private_layers_without_native_loading(self):
        script = textwrap.dedent("""
            import ctypes
            import importlib.abc
            import socket
            import subprocess
            import sys

            sys.modules.pop("fcntl", None)
            class NoPosix(importlib.abc.MetaPathFinder):
                def find_spec(self, fullname, path=None, target=None):
                    if fullname == "fcntl" or fullname.startswith("sas_re._posix"):
                        raise AssertionError("POSIX import on Windows selection: " + fullname)
                    return None
            sys.meta_path.insert(0, NoPosix())
            def forbidden(*args, **kwargs):
                raise AssertionError("Import attempted native load, execution, or network")
            ctypes.CDLL = forbidden
            ctypes.PyDLL = forbidden
            ctypes.WinDLL = forbidden
            ctypes.OleDLL = forbidden
            subprocess.Popen = forbidden
            socket.socket = forbidden
            socket.create_connection = forbidden
            sys.platform = "win32"
            from sas_re import preflight, platform_io
            from sas_re import _windows_native, _windows_preflight
            assert platform_io.preflight_capabilities()["read_only_preflight"] == "BLOCKED"
            assert "fcntl" not in sys.modules
            assert not any(name.startswith("sas_re._posix") for name in sys.modules)
            assert not hasattr(preflight, "WindowsPreflight")
        """)
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([sys.executable, "-c", script], cwd=folder,
                                    capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
