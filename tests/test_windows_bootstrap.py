"""Independent CP3D metadata-only simulation; NOT native Windows qualification.

The oracle is an in-memory namespace, not an NTFS emulator. No fixture method can
read source content, create a store, alter an ACL or invoke a native API. Aliases
are independently assigned fixture facts, never inferred from Python casefold.
"""

from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field, replace
import unittest
from unittest.mock import patch

from cp2_vectors import envelope
from sas_re._io_common import EvidenceError
from sas_re._windows_bootstrap import (
    AbsenceObservation, DirectoryExpectation, HostContext,
    HostVolumeExpectations, LookupKind, LookupResult, MetadataExpectations,
    MetadataSession, classify_lookup,
)
from sas_re._windows_bootstrap_native import DeviceInfo
from sas_re._windows_native import ObjectIdentity, ObjectInfo, VolumeInfo
from sas_re.authorization import authorization_scope_identity, validate_authorization
from sas_re.preflight import LocalInspectionPolicy


@contextmanager
def no_external_io():
    with ExitStack() as stack:
        for name in ("builtins.open", "io.open", "os.open", "os.mkdir", "os.makedirs",
                     "os.unlink", "os.rename", "os.replace", "subprocess.Popen",
                     "socket.socket"):
            stack.enter_context(patch(name, side_effect=AssertionError(
                "Metadata simulation attempted external I/O: " + name)))
        yield


@dataclass
class Node:
    info: ObjectInfo
    children: dict = field(default_factory=dict)
    aliases: dict = field(default_factory=dict)
    case_mode: object = False
    volume: VolumeInfo = VolumeInfo("NTFS", 0x91, 255, 8)
    device: DeviceInfo = DeviceInfo(7, 0)
    sentinel: bytes = b"original bytes: no candidate read API exists\r\n"


class MetadataFake:
    """Separately constructed expected inventory and mutable namespace oracle."""

    def __init__(self, testcase):
        self.testcase = testcase
        self.events, self.closed, self.active = [], [], {}
        self.before = None
        self.counter, self.next_handle = 0, 100
        self.root = self.node()
        self.anchor, self.source, self.logs, self.parent = [self.node() for _ in range(4)]
        self.root.children["Synthetic"] = self.anchor
        self.anchor.children.update(Sources=self.source, Logs=self.logs, NewOutput=self.parent)
        self.host = HostContext("synthetic-host-inventory", "synthetic-ordinary-token")
        self.targets = (r"\Device\HarddiskVolume7",)
        self.locator = self.targets[0] + "\\"
        self.lookup_override = None
        self.close_fault = None

    def node(self, *, directory=True):
        self.counter += 1
        return Node(ObjectInfo(ObjectIdentity(0x100000007, self.counter.to_bytes(16, "little")),
                               directory, 0, 1, False, 0x10 if directory else 0x20,
                               100, 200, 300))

    def _event(self, name, *arguments):
        self.events.append((name, *arguments))
        if self.before is not None:
            self.before(name, *arguments)

    def _handle(self, node):
        handle = self.next_handle
        self.next_handle += 1
        self.active[handle] = node
        return handle

    def context(self):
        self._event("context")
        return self.host

    def mappings(self, name):
        self._event("mapping", name)
        self.testcase.assertEqual(name, "C:")
        return self.targets

    def open_root(self, locator):
        self._event("root", locator)
        self.testcase.assertEqual(locator, self.locator)
        return self._handle(self.root)

    def inspect(self, handle):
        self._event("inspect", handle)
        return self.active[handle].info

    def volume(self, handle):
        self._event("volume", handle)
        return self.active[handle].volume

    def device(self, handle):
        self._event("device", handle)
        return self.active[handle].device

    def case_sensitive(self, handle):
        self._event("case", handle)
        return self.active[handle].case_mode

    def lookup(self, parent, name):
        self._event("lookup", parent, name)
        self.testcase.assertIs(type(name), str)
        self.testcase.assertTrue(name and name not in {".", ".."})
        self.testcase.assertFalse(any(char in name for char in "\\/:\x00"))
        owner = self.active[parent]
        if self.lookup_override is not None:
            value = self.lookup_override(owner, name)
            if value is not None:
                return value
        actual = owner.aliases.get(name, name)
        if actual not in owner.children:
            return LookupResult(LookupKind.NAME_NOT_FOUND, 0xC0000034)
        return LookupResult(LookupKind.PRESENT, 0, self._handle(owner.children[actual]), actual)

    def close(self, handle):
        self._event("close", handle)
        self.testcase.assertNotIn(handle, self.closed, "Retried close or double ownership")
        self.closed.append(handle)
        del self.active[handle]
        if self.close_fault is not None:
            error, self.close_fault = self.close_fault, None
            raise error

    def expected(self):
        return MetadataExpectations(
            HostVolumeExpectations(self.host, "supplied-inspection-reference",
                "supplied-physical-backing-reference", self.locator, "C:", self.targets,
                self.root.info.identity, self.root.volume, self.root.device),
            tuple(DirectoryExpectation(parts, node.info.identity) for parts, node in (
                (("Synthetic",), self.anchor), (("Synthetic", "Sources"), self.source),
                (("Synthetic", "Logs"), self.logs), (("Synthetic", "NewOutput"), self.parent))),
            ("Synthetic", "NewOutput"))

    def snapshot(self):
        def visit(node, seen):
            if id(node) in seen:
                return ("retained alias", node.info.identity)
            return (node.info, node.volume, node.device, node.case_mode, node.sentinel,
                    tuple(sorted(node.aliases.items())),
                    tuple((name, visit(child, seen | {id(node)}))
                          for name, child in sorted(node.children.items())))
        return visit(self.root, set())


class WindowsBootstrapSimulatedTests(unittest.TestCase):
    def setUp(self):
        self.value = envelope("windows")
        validate_authorization(self.value, expected_platform="windows")
        self.api = MetadataFake(self)
        self.expected = self.api.expected()
        self.policy = LocalInspectionPolicy(
            "C:\\Synthetic", tuple((item["root_id"], item["path"])
                                    for item in self.value["bindings"]),
            "C:\\Synthetic\\NewOutput\\store", self.value["logical_scope"]["workspace_id"],
            self.value["logical_scope"]["run_id"], authorization_scope_identity(self.value),
            "QUIESCENT_SYNTHETIC_TRUSTED_WRITERS")

    def session(self):
        return MetadataSession(self.api, self.value, self.policy, self.expected)

    def assert_disposed(self):
        self.assertFalse(self.api.active)
        self.assertEqual(len(self.api.closed), len(set(self.api.closed)))
        self.assertTrue(set(event[0] for event in self.api.events) <= {
            "context", "mapping", "root", "inspect", "volume", "device", "case", "lookup", "close"})

    def blocked(self, action=None, *, code=None, zero_events=False):
        with no_external_io(), self.assertRaises(EvidenceError) as caught:
            (self.session if action is None else action)()
        self.assertEqual(caught.exception.gate, "BLOCKED")
        if code:
            self.assertEqual(caught.exception.code, code)
        self.assert_disposed()
        if zero_events:
            self.assertEqual(self.api.events, [])
        return caught.exception

    def volume_expectation(self, **changes):
        self.expected = replace(self.expected, volume=replace(self.expected.volume, **changes))

    def test_positive_absence_retains_metadata_only_and_preserves_original_bytes(self):
        before = self.api.snapshot()
        with no_external_io(), self.session() as session:
            self.assertEqual(session.state, "BOUND")
            result = session.inspect_absence()
            self.assertEqual(result, AbsenceObservation(self.api.parent.info.identity, "store", ()))
            session.recheck_absence()
            self.assertEqual(session.state, "OBSERVED")
            self.assertTrue(self.api.active)
        self.assertEqual(session.state, "CLOSED")
        self.assertEqual(before, self.api.snapshot())
        self.assert_disposed()
        self.assertEqual(sum(event[0] == "root" for event in self.api.events), 1)

    def test_missing_multiple_suffixes_stops_at_first_missing_name(self):
        self.policy = replace(self.policy, store_path=self.policy.store_path + "\\nested\\leaf")
        with no_external_io(), self.session() as session:
            self.assertEqual(session.inspect_absence().remaining_suffix, ("nested", "leaf"))
        self.assertFalse(any(event[0] == "lookup" and event[2] in {"nested", "leaf"}
                             for event in self.api.events))
        self.assert_disposed()

    def test_genuine_sibling_with_shared_source_ancestor_is_allowed(self):
        self.policy = replace(self.policy, store_path="C:\\Synthetic\\new-store")
        self.expected = replace(self.expected, store_parent=("Synthetic",),
            directories=tuple(d for d in self.expected.directories if d.components[-1] != "NewOutput"))
        with no_external_io(), self.session() as session:
            self.assertEqual(session.inspect_absence().parent_identity, self.api.anchor.info.identity)
        self.assert_disposed()

    def test_missing_expectations_rejected_before_api_calls(self):
        self.expected = None
        self.blocked(zero_events=True)

    def test_empty_inspection_reference_rejected_before_api_calls(self):
        self.volume_expectation(inspection_reference="")
        self.blocked(zero_events=True)

    def test_empty_host_and_backing_references_are_not_inferred(self):
        for change in (dict(context=HostContext("", "token")), dict(backing_reference=" ")):
            with self.subTest(change=change):
                self.expected = self.api.expected()
                self.volume_expectation(**change)
                self.blocked(zero_events=True)

    def test_invalid_root_only_locators_do_not_trigger_drive_search(self):
        for locator in ("C:\\", "\\??\\C:\\", r"\Device\HarddiskVolume7\Synthetic",
                        "\\Device\\HarddiskVolume0\\", "\\Device\\Mup\\", ""):
            with self.subTest(locator=locator):
                self.expected = self.api.expected()
                self.volume_expectation(root_locator=locator)
                self.blocked(zero_events=True)

    def test_unrelated_drive_mapping_is_rejected_purely(self):
        self.volume_expectation(mapping_name="D:")
        self.blocked(zero_events=True)

    def test_incomplete_or_historical_mapping_expectations_rejected_purely(self):
        for targets in ((), self.api.targets * 2, (r"\??\D:\folder",),
                        (self.api.targets[0], r"\Device\HarddiskVolume8"),
                        self.api.targets * 129):
            with self.subTest(targets=targets[:2]):
                self.expected = self.api.expected()
                self.volume_expectation(mapping_targets=targets)
                self.blocked(zero_events=True)

    def test_wrong_host_context_stops_before_mapping_or_root(self):
        self.api.host = HostContext("different-host", "different-token")
        self.blocked(code="CP3D_HOST_CONTEXT_CHANGED")
        self.assertEqual(self.api.events, [("context",)])

    def test_wrong_mapping_stops_before_root(self):
        self.api.targets = (r"\Device\HarddiskVolume8",)
        self.blocked(code="CP3D_MAPPING_CHANGED")
        self.assertFalse(any(event[0] == "root" for event in self.api.events))

    def test_unexpected_prior_mapping_is_not_silently_ignored(self):
        self.api.targets += (r"\Device\HarddiskVolume8",)
        self.blocked(code="CP3D_MAPPING_CHANGED")

    def test_mapping_change_after_acquisition_invalidates_and_releases_root(self):
        def change(name, *arguments):
            if name == "root":
                self.api.targets = (r"\Device\HarddiskVolume8",)
        self.api.before = change
        self.blocked(code="CP3D_MAPPING_CHANGED")
        self.assertTrue(self.api.closed)

    def test_mapping_observation_bound_has_no_ninth_native_attempt(self):
        with no_external_io():
            session = self.session()
            session.inspect_absence()
            for _ in range(4):
                session.recheck_absence()
            self.blocked(session.recheck_absence, code="CP3D_MAPPING_LIMIT")
        self.assertEqual(sum(event[0] == "mapping" for event in self.api.events), 8)

    def test_duplicate_directory_identity_rejected_purely(self):
        entries = list(self.expected.directories)
        entries[1] = replace(entries[1], identity=entries[0].identity)
        self.expected = replace(self.expected, directories=tuple(entries))
        self.blocked(zero_events=True)

    def test_unexpected_or_missing_directory_declaration_rejected_purely(self):
        self.expected = replace(self.expected, directories=self.expected.directories[:-1])
        self.blocked(zero_events=True)

    def test_unsafe_directory_components_rejected_purely(self):
        for component in ("..", "a/b", "a\\b", "x:stream", "NUL", "x."):
            with self.subTest(component=component):
                self.expected = self.api.expected()
                entries = list(self.expected.directories)
                entries[0] = replace(entries[0], components=(component,))
                self.expected = replace(self.expected, directories=tuple(entries))
                self.blocked(zero_events=True)

    def test_directory_component_container_types_and_depth_are_bounded(self):
        for parts in (["Synthetic"], "Synthetic", (True,), (None,), ("x",) * 65):
            with self.subTest(parts=parts):
                self.expected = self.api.expected()
                entries = list(self.expected.directories)
                entries[0] = replace(entries[0], components=parts)
                self.expected = replace(self.expected, directories=tuple(entries))
                self.blocked(zero_events=True)

    def test_directory_inventory_over_bound_rejected_before_any_api_call(self):
        self.expected = replace(self.expected, directories=self.expected.directories * 33)
        self.blocked(zero_events=True)

    def test_store_parent_equal_to_source_rejected_before_api_calls(self):
        self.policy = replace(self.policy, store_path="C:\\Synthetic\\Sources\\new-store")
        self.expected = replace(self.expected, store_parent=("Synthetic", "Sources"),
            directories=tuple(d for d in self.expected.directories if d.components[-1] != "NewOutput"))
        self.blocked(zero_events=True, code="CP3D_STORE_OVERLAP")

    def test_wrong_root_identity_is_not_rebound(self):
        self.api.root.info = replace(self.api.root.info, identity=ObjectIdentity(0x100000007, b"x" * 16))
        self.blocked(code="CP3D_OBJECT_UNSAFE")
        self.assertFalse(any(event[0] == "lookup" for event in self.api.events))

    def test_dword_volume_serial_and_64_bit_identity_are_not_truncated_or_equated(self):
        self.api.root.volume = replace(self.api.root.volume, serial=7)
        self.blocked(code="CP3D_VOLUME_CHANGED")

    def test_parent_physical_alias_rejected_by_expected_object_identity(self):
        self.api.anchor.children["NewOutput"] = self.api.source
        self.blocked(code="CP3D_OBJECT_UNSAFE")

    def test_reparse_root_and_ancestor_refused_before_descent(self):
        for target in ("root", "anchor"):
            with self.subTest(target=target):
                self.api = MetadataFake(self)
                node = getattr(self.api, target)
                node.info = replace(node.info, attributes=0x410, reparse_tag=0xA0000003)
                self.blocked(code="CP3D_OBJECT_UNSAFE")
                self.assertFalse(any(event[0] == "lookup" and event[2] == "Sources"
                                     for event in self.api.events))

    def test_non_directory_or_pending_delete_root_refused(self):
        for change in (dict(directory=False), dict(delete_pending=True)):
            with self.subTest(change=change):
                self.api = MetadataFake(self)
                self.api.root.info = replace(self.api.root.info, **change)
                self.blocked(code="CP3D_OBJECT_UNSAFE")

    def test_remote_removable_unknown_and_unsupported_locality_block(self):
        for device in (DeviceInfo(0x14, 0), DeviceInfo(7, 0x10), DeviceInfo(7, 1), None):
            with self.subTest(device=device):
                self.api = MetadataFake(self)
                self.api.root.device = device
                self.blocked(code="CP3D_VOLUME_CHANGED")

    def test_unknown_case_behavior_is_not_assumed_case_insensitive(self):
        for mode in (True, None, 0, "False"):
            with self.subTest(mode=mode):
                self.api = MetadataFake(self)
                self.api.parent.case_mode = mode
                self.blocked(code="CP3D_CASE_BEHAVIOR_UNAVAILABLE")

    def test_alias_parent_long_name_does_not_bind_expected_identity(self):
        self.api.anchor.children["SOURCES"] = self.api.anchor.children.pop("Sources")
        self.api.anchor.aliases["Sources"] = "SOURCES"
        self.blocked(code="CP3D_PARENT_BINDING_UNAVAILABLE")

    def test_missing_expected_parent_is_not_an_absent_store_proof(self):
        del self.api.anchor.children["NewOutput"]
        self.blocked(code="CP3D_PARENT_BINDING_UNAVAILABLE")

    def test_case_alias_collision_is_present_even_without_requested_long_name(self):
        self.api.parent.children["STORE"] = self.api.node()
        self.api.parent.aliases["store"] = "STORE"
        self.blocked(lambda: self.session().inspect_absence(), code="CP3D_STORE_PRESENT_OR_ALIAS")

    def test_short_name_alias_collision_is_present_even_without_requested_long_name(self):
        self.api.parent.children["Long Artifact Directory"] = self.api.node()
        self.api.parent.aliases["store"] = "Long Artifact Directory"
        self.blocked(lambda: self.session().inspect_absence(), code="CP3D_STORE_PRESENT_OR_ALIAS")

    def test_existing_file_is_collision_not_directory_type_not_found(self):
        self.api.parent.children["store"] = self.api.node(directory=False)
        self.blocked(lambda: self.session().inspect_absence(), code="CP3D_STORE_PRESENT_OR_ALIAS")

    def test_existing_reparse_is_collision_not_candidate_absence(self):
        node = self.api.node()
        node.info = replace(node.info, attributes=0x410, reparse_tag=0xDEADBEEF)
        self.api.parent.children["store"] = node
        self.blocked(lambda: self.session().inspect_absence(), code="CP3D_STORE_PRESENT_OR_ALIAS")

    def test_other_native_statuses_never_prove_absence(self):
        for status in (0xC000003A, 0xC000000F, 0xC0000022, 0xC0000043, 0xC0000103,
                       0x103, 1, 0xFFFFFFFF):
            with self.subTest(status=hex(status)):
                self.api = MetadataFake(self)
                self.api.lookup_override = lambda owner, name: (
                    LookupResult(LookupKind.NAME_NOT_FOUND, status) if name == "store" else None)
                self.blocked(lambda: self.session().inspect_absence(), code="CP3D_LOOKUP_UNAVAILABLE")

    def test_invalid_lookup_shape_rejected_and_known_handles_cleaned(self):
        self.api.lookup_override = lambda owner, name: "not a typed result"
        self.blocked(code="CP3D_LOOKUP_INVALID")

    def test_pending_borrowed_handle_is_never_adopted_or_closed(self):
        borrowed = self.api._handle(self.api.node())
        self.api.lookup_override = lambda owner, name: LookupResult(LookupKind.BLOCKED, 0x103, borrowed)
        with no_external_io(), self.assertRaises(EvidenceError) as caught:
            self.session()
        self.assertEqual(caught.exception.code, "CP3D_LOOKUP_OWNERSHIP_UNAVAILABLE")
        self.assertEqual(set(self.api.active), {borrowed})
        self.assertNotIn(borrowed, self.api.closed)
        self.api.close(borrowed)  # The simulated adapter, not the session, owns it.
        self.assert_disposed()

    def test_present_label_cannot_transfer_failed_or_pending_operation_resources(self):
        for status in (0x103, 0xC0000022, 0xC0000034):
            with self.subTest(status=hex(status)):
                self.api = MetadataFake(self)
                retained = self.api._handle(self.api.node())
                self.api.lookup_override = lambda owner, name: LookupResult(
                    LookupKind.PRESENT, status, retained, name)
                with no_external_io(), self.assertRaises(EvidenceError) as caught:
                    self.session()
                self.assertEqual(caught.exception.code, "CP3D_LOOKUP_OWNERSHIP_UNAVAILABLE")
                self.assertEqual(set(self.api.active), {retained})
                self.assertNotIn(retained, self.api.closed)
                # The fake completion owner explicitly releases after the test.
                # This proves protocol non-adoption, not native I/O completion.
                self.api.close(retained)
                self.assert_disposed()

    def test_malformed_observed_metadata_cannot_hide_behind_python_equality(self):
        for change in (dict(links=True), dict(links=2), dict(size=False),
                       dict(creation_time=True), dict(change_time=2**63),
                       dict(reparse_tag=False), dict(attributes=2**32 + 0x10)):
            with self.subTest(change=change):
                self.api = MetadataFake(self)
                self.api.root.info = replace(self.api.root.info, **change)
                self.blocked(code="CP3D_OBJECT_UNSAFE")

    def test_malformed_observed_device_record_cannot_equal_expected_zero(self):
        self.api.root.device = DeviceInfo(7, False)
        self.blocked(code="CP3D_VOLUME_CHANGED")

    def test_raw_metadata_oserror_becomes_blocked_and_closes_owned_handles(self):
        def denied(name, *arguments):
            if name == "inspect":
                raise PermissionError("synthetic metadata access denied")
        self.api.before = denied
        self.blocked(code="CP3D_METADATA_UNAVAILABLE")

    def test_duplicate_live_handle_is_not_closed_twice(self):
        def borrowed(owner, name):
            return LookupResult(LookupKind.PRESENT, 0, next(iter(self.api.active)), name)
        self.api.lookup_override = borrowed
        self.blocked(code="CP3D_HANDLE_UNAVAILABLE")

    def test_insertion_between_absence_observations_invalidates_session(self):
        probes = 0
        def insert(name, *arguments):
            nonlocal probes
            if name == "lookup" and arguments[1] == "store":
                probes += 1
                if probes == 2:
                    self.api.parent.children["store"] = self.api.node()
        self.api.before = insert
        self.blocked(lambda: self.session().inspect_absence(), code="CP3D_STORE_PRESENT_OR_ALIAS")

    def test_parent_replacement_after_observation_invalidates_without_rebind(self):
        with no_external_io():
            session = self.session()
            session.inspect_absence()
            self.api.anchor.children["NewOutput"] = self.api.node()
            self.blocked(session.recheck_absence, code="CP3D_OBJECT_UNSAFE")

    def test_root_mutation_after_observation_invalidates(self):
        with no_external_io():
            session = self.session()
            session.inspect_absence()
            self.api.root.info = replace(self.api.root.info, change_time=301)
            self.blocked(session.recheck_absence, code="CP3D_BINDING_CHANGED")

    def test_cancellation_after_acquisition_releases_all_owned_handles(self):
        def cancel(name, *arguments):
            if name == "lookup" and arguments[1] == "Sources":
                raise KeyboardInterrupt("synthetic cancellation")
        self.api.before = cancel
        with no_external_io(), self.assertRaises(KeyboardInterrupt):
            self.session()
        self.assert_disposed()

    def test_lookup_exception_disposes_every_acquired_handle(self):
        def deny(name, *arguments):
            if name == "lookup" and arguments[1] == "Sources":
                raise EvidenceError("CP3D_ACCESS_UNAVAILABLE", "BLOCKED")
        self.api.before = deny
        self.blocked(code="CP3D_ACCESS_UNAVAILABLE")

    def test_uncertain_close_blocks_success_and_still_attempts_other_handles(self):
        with no_external_io():
            session = self.session()
            session.inspect_absence()
            owned = set(self.api.active)
            self.api.close_fault = OSError("injected uncertain close after release")
            self.blocked(session.close, code="CP3D_CLOSE_UNCERTAIN")
        self.assertTrue(owned <= set(self.api.closed))

    def test_closed_or_replayed_session_does_not_access_namespace(self):
        with no_external_io():
            session = self.session()
            session.inspect_absence()
            session.close()
            before = list(self.api.events)
            self.blocked(session.recheck_absence, code="CP3D_SESSION_STATE")
            self.blocked(session.inspect_absence, code="CP3D_SESSION_STATE")
            session.close()
        self.assertEqual(self.api.events, before)

    def test_second_initial_absence_request_is_rejected(self):
        with no_external_io():
            session = self.session()
            session.inspect_absence()
            self.blocked(session.inspect_absence, code="CP3D_SESSION_STATE")

    def test_incomplete_or_unsupported_volume_expectations_are_purely_blocked(self):
        for change in (dict(volume=VolumeInfo("FAT32", 1, 255, 8)),
                       dict(volume=VolumeInfo("NTFS", 1, 255, 0)),
                       dict(device=DeviceInfo(7, 0x10)), dict(device=DeviceInfo(7, 1))):
            with self.subTest(change=change):
                self.expected = self.api.expected()
                self.volume_expectation(**change)
                self.blocked(zero_events=True)

    def test_status_classification_has_only_two_nonblocked_outcomes(self):
        self.assertIs(classify_lookup(0), LookupKind.PRESENT)
        for status in (0xC0000034, 0xC0000034 - 2**32):
            self.assertIs(classify_lookup(status), LookupKind.NAME_NOT_FOUND)
        for status in (True, None, "0", -2**31 - 1, 2**32, 0x103, 1, 0xC000003A):
            self.assertIs(classify_lookup(status), LookupKind.BLOCKED)
