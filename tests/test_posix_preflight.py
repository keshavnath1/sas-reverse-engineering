"""Synthetic CP3A native descriptor tests; no SAS execution or publication.

OS-call observation is an in-process test oracle, not privileged kernel tracing
or a claim that arbitrary concurrent writers can be contained.
"""

from contextlib import ExitStack, contextmanager
from copy import deepcopy
import errno
import hashlib
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch

from cp2_vectors import (EXPECTED_IDENTITIES, EXPECTED_SCOPE_SHA256, RAW_OTHER,
                         RAW_VARIANTS, envelope, operation_payload,
                         oracle_files, oracle_hash, oracle_id)
from sas_re.authorization import authorization_scope_identity, validate_authorization
from sas_re.evidence import build_inventory, identity
from sas_re.preflight import LocalInspectionPolicy, open_preflight
from sas_re.safeio import AttemptStore, EvidenceError


def object_id(info):
    return info.st_dev, info.st_ino


class IOObservation:
    """Observe actual descriptors and forbid mutation calls during the reader.

Fixture construction and deliberate adversary actions run outside this guard.
The expected file identities come from an independent pre-run fixture inventory.
"""

    def __init__(self, testcase, expected_ids):
        self.testcase = testcase
        self.expected_ids = set(expected_ids)
        self.active = {}
        self.locations = {}
        self.opens = []
        self.reads = []
        self.scans = []
        self.metadata_reads = []
        self.proc_device = os.stat("/proc").st_dev if sys.platform == "linux" else None
        self.before_open = None
        self.after_open = None
        self.before_read = None
        self.after_read = None
        self.original_open = os.open
        self.original_close = os.close
        self.original_read = os.read
        self.original_fstat = os.fstat
        self.original_scandir = os.scandir

    def open(self, path, flags, mode=0o777, *, dir_fd=None):
        self.testcase.assertEqual(flags & os.O_ACCMODE, os.O_RDONLY)
        self.testcase.assertFalse(flags & (os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        if self.before_open:
            self.before_open(path, flags, dir_fd)
        fd = self.original_open(path, flags, mode, dir_fd=dir_fd)
        info = self.original_fstat(fd)
        self.active[fd] = (object_id(info), stat.S_ISREG(info.st_mode))
        name = os.fsdecode(path)
        self.locations[fd] = (name if name.startswith("/") else
                              self.locations.get(dir_fd, "UNKNOWN").rstrip("/") + "/" + name)
        self.opens.append((path, flags, dir_fd, fd, object_id(info)))
        self.testcase.assertFalse(os.get_inheritable(fd))
        if self.after_open:
            self.after_open(path, flags, dir_fd, fd)
        return fd

    def close(self, fd):
        try:
            return self.original_close(fd)
        finally:
            self.active.pop(fd, None)
            self.locations.pop(fd, None)

    def read(self, fd, count):
        info = self.original_fstat(fd)
        if object_id(info) not in self.expected_ids:
            # Linux filesystem qualification reads fixed, no-follow kernel
            # metadata. Prove its provenance separately; never allow arbitrary
            # non-source data reads just because they are outside this fixture.
            prefix = "/proc/" + str(os.getpid()) + "/"
            location = self.locations.get(fd, "UNKNOWN")
            self.testcase.assertEqual(sys.platform, "linux")
            self.testcase.assertEqual(info.st_dev, self.proc_device)
            self.testcase.assertTrue(location == prefix + "mountinfo" or
                (location.startswith(prefix + "fdinfo/") and
                 location[len(prefix + "fdinfo/"):].isdigit()), location)
            result = self.original_read(fd, count)
            self.metadata_reads.append((location, len(result)))
            return result
        held = {value[0] for value in self.active.values() if value[1]}
        self.testcase.assertTrue(self.expected_ids <= held,
                                 "Source read occurred before every file had a retained read handle")
        self.testcase.assertIn(object_id(self.original_fstat(fd)), self.expected_ids)
        if self.before_read:
            self.before_read(fd, count)
        result = self.original_read(fd, count)
        self.reads.append((fd, count, len(result)))
        if self.after_read:
            self.after_read(fd, result)
        return result

    def scandir(self, fd):
        self.testcase.assertIsInstance(fd, int, "Enumeration must use a retained descriptor")
        self.scans.append(object_id(self.original_fstat(fd)))
        return self.original_scandir(fd)

    @contextmanager
    def guard(self, *, forbid_mutations=True):
        with ExitStack() as stack:
            features = {name: set(getattr(os, name)) for name in
                        ("supports_dir_fd", "supports_fd", "supports_follow_symlinks")}
            def observe(name, replacement):
                original = getattr(os, name)
                mocked = stack.enter_context(patch.object(os, name, side_effect=replacement))
                for members in features.values():
                    if original in members:
                        members.add(mocked)
                return mocked
            observe("open", self.open)
            observe("scandir", self.scandir)
            stack.enter_context(patch("os.close", side_effect=self.close))
            stack.enter_context(patch("os.read", side_effect=self.read))
            stack.enter_context(patch("pathlib.Path.resolve", side_effect=AssertionError("Path-based resolution")))
            if forbid_mutations:
                for name in ("mkdir", "makedirs", "write", "pwrite", "truncate", "ftruncate",
                             "unlink", "remove", "rename", "replace", "link", "symlink",
                             "chmod", "fchmod", "chown", "fchown", "utime"):
                    if hasattr(os, name):
                        observe(name, AssertionError("Reader requested a filesystem mutation: " + name))
                # A fallback file object would bypass os.read observation. All
                # trusted schemas were warmed before the guard; this path may
                # use only retained descriptors, including Linux proc metadata.
                stack.enter_context(patch("builtins.open", side_effect=AssertionError("Path-based file object")))
                stack.enter_context(patch("io.open", side_effect=AssertionError("Path-based file object")))
            # Preserve the actual runtime's feature memberships for observation
            # mocks; no capability is introduced that its original lacked.
            for name, members in features.items():
                stack.enter_context(patch.object(os, name, members))
            stack.enter_context(patch("subprocess.Popen", side_effect=AssertionError("Process launch")))
            stack.enter_context(patch("socket.socket", side_effect=AssertionError("Network access")))
            yield self
        self.testcase.assertEqual(self.active, {}, "Reader leaked descriptors")


@unittest.skipUnless(os.name == "posix" and sys.platform in {"darwin", "linux"},
                     "Native POSIX cases; skipping never qualifies Windows")
class PosixPreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.anchor = Path(self.temp.name).resolve()
        self.anchor.chmod(0o700)
        self.source = self.anchor / "sources"
        self.logs = self.anchor / "logs"
        self.source.mkdir()
        (self.source / "includes").mkdir()
        self.logs.mkdir()
        self.paths = {"src:main.sas": self.source / "main.sas",
                      "src:includes/common.sas": self.source / "includes" / "common.sas",
                      "logs:run.log": self.logs / "run.log"}
        self.expected = {"src:main.sas": RAW_VARIANTS["lf"], **RAW_OTHER}
        for key, path in self.paths.items():
            path.write_bytes(self.expected[key])
        self.value = envelope()
        for binding in self.value["bindings"]:
            binding["path"] = str(self.source if binding["root_id"] == "src" else self.logs)
        self.store = self.anchor / "new-output" / "store"
        # Trusted package-resource loading is distinct from candidate source I/O.
        validate_authorization(self.value)

    def policy(self, *, value=None, store=None, **changes):
        value = self.value if value is None else value
        fields = {"anchor": str(self.anchor),
                  "source_roots": tuple((item["root_id"], item["path"]) for item in value["bindings"]),
                  "store_path": str(self.store if store is None else store),
                  "workspace_id": value["logical_scope"]["workspace_id"],
                  "run_id": value["logical_scope"]["run_id"],
                  "scope_sha256": authorization_scope_identity(value),
                  "source_model": "QUIESCENT_SYNTHETIC_TRUSTED_WRITERS"}
        fields.update(changes)
        return LocalInspectionPolicy(**fields)

    def observation(self):
        return IOObservation(self, [object_id(path.stat()) for path in self.paths.values() if path.exists()])

    def no_access_observation(self):
        observation = self.observation()
        def forbidden(path, flags, parent):
            self.fail("Pure authorization rejection attempted metadata access")
        observation.before_open = forbidden
        return observation

    def denied(self, code, function, *args, gate="BLOCKED", **kwargs):
        with self.assertRaises(EvidenceError) as error:
            function(*args, **kwargs)
        self.assertEqual(error.exception.code, code)
        self.assertEqual(error.exception.gate, gate)
        self.assertNotIn(str(self.anchor), str(error.exception))
        return error.exception

    def read(self, *, value=None, policy=None):
        with open_preflight(self.value if value is None else value,
                            policy=self.policy() if policy is None else policy) as session:
            self.assertEqual(session.state, "READY")
            result = session.read_sources()
            self.assertEqual(session.state, "CLOSED")
            return result

    def snapshot(self):
        return {key: (path.read_bytes(), path.stat().st_mtime_ns,
                      path.stat().st_ctime_ns, path.stat().st_mode,
                      path.stat().st_nlink, object_id(path.stat()))
                for key, path in self.paths.items()}

    def test_positive_sibling_roots_all_handles_ready_original_bytes_no_store(self):
        before = self.snapshot()
        observation = self.observation()
        with observation.guard():
            self.assertEqual(self.read(), self.expected)
        self.assertTrue(observation.reads)
        self.assertEqual(before, self.snapshot())
        self.assertFalse(self.store.parent.exists())

    def test_preflight_is_metadata_and_read_handle_acquisition_without_content(self):
        observation = self.observation()
        with observation.guard():
            with open_preflight(self.value, policy=self.policy()) as session:
                self.assertEqual(session.state, "READY")
                self.assertEqual(observation.reads, [])
                self.assertEqual({item[0] for item in observation.active.values() if item[1]},
                                 observation.expected_ids)
        self.assertFalse(self.store.parent.exists())

    def test_missing_policy_and_forged_approval_are_not_filesystem_authority(self):
        value = deepcopy(self.value)
        value["authorization"]["approval_reference"] = "unverified-approved-by-caller"
        validate_authorization(value)
        with self.no_access_observation().guard():
            self.denied("CP3A_POLICY_REQUIRED", open_preflight, value, policy=None)
        self.assertFalse(self.store.parent.exists())

    def test_policy_owner_run_hash_and_bindings_must_match_before_io(self):
        for changes in ({"workspace_id": "other"}, {"run_id": "other"},
                        {"scope_sha256": "0" * 64},
                        {"source_roots": (("src", str(self.logs)), ("logs", str(self.source)))}):
            policy = self.policy(**changes)
            with self.subTest(changes=changes), self.no_access_observation().guard():
                self.denied("CP3A_POLICY_MISMATCH", open_preflight, self.value,
                            policy=policy, gate="FAIL")

    def test_store_outside_anchor_is_rejected_without_source_content(self):
        policy = self.policy(store=self.anchor.parent / "outside-synthetic-store")
        observation = self.observation()
        with observation.guard():
            self.denied("CP3A_OUTSIDE_ANCHOR", open_preflight, self.value, policy=policy, gate="FAIL")
        self.assertFalse(observation.reads)

    def test_unavailable_writer_assurance_is_blocked_before_metadata(self):
        with self.no_access_observation().guard():
            self.denied("CP3A_WRITER_POLICY_UNAVAILABLE", open_preflight, self.value,
                        policy=self.policy(source_model="ARBITRARY_CONCURRENT_WRITERS"))

    def test_equal_nested_and_ancestor_store_roots_are_physically_rejected(self):
        for target in (self.source, self.source / "absent" / "store", self.anchor,
                       self.source / "includes"):
            observation = self.observation()
            with self.subTest(target=target.name), observation.guard():
                self.denied("CP3A_STORE_OVERLAP", open_preflight, self.value,
                            policy=self.policy(store=target), gate="FAIL")
            self.assertFalse(observation.reads)
        self.assertFalse((self.source / "absent").exists())

    def test_store_inside_unexpected_source_directory_is_rejected_before_descent(self):
        unknown = self.source / "undeclared-output-parent"
        unknown.mkdir()
        unknown_id = object_id(unknown.stat())
        observation = self.observation()
        with observation.guard():
            self.denied("CP3A_STORE_OVERLAP", open_preflight, self.value,
                        policy=self.policy(store=unknown / "store"), gate="FAIL")
        self.assertNotIn(unknown_id, observation.scans)
        self.assertFalse(any(item[4] == unknown_id for item in observation.opens))
        self.assertFalse(observation.reads)
        self.assertFalse((unknown / "store").exists())

    def test_case_alias_store_is_physical_not_casefold_guesswork(self):
        alias = self.anchor / "SOURCES"
        if alias.exists():
            self.assertEqual(object_id(alias.stat()), object_id(self.source.stat()))
            observation = self.observation()
            with observation.guard():
                self.denied("CP3A_STORE_OVERLAP", open_preflight, self.value,
                            policy=self.policy(store=alias), gate="FAIL")
            self.assertFalse(observation.reads)
        else:
            alias.mkdir()
            self.assertNotEqual(object_id(alias.stat()), object_id(self.source.stat()))
            with self.observation().guard():
                self.assertEqual(self.read(policy=self.policy(store=alias)), self.expected)

    def test_unicode_alias_or_distinct_directory_uses_native_object_identity(self):
        renamed = self.anchor / "sourc\u00e9s"
        self.source.rename(renamed)
        self.source = renamed
        for key in ("src:main.sas", "src:includes/common.sas"):
            self.paths[key] = renamed / key.split(":", 1)[1]
        next(item for item in self.value["bindings"] if item["root_id"] == "src")["path"] = str(renamed)
        alias = self.anchor / "source\u0301s"
        if alias.exists():
            self.assertEqual(object_id(alias.stat()), object_id(renamed.stat()))
            with self.observation().guard():
                self.denied("CP3A_STORE_OVERLAP", open_preflight, self.value,
                            policy=self.policy(store=alias), gate="FAIL")
        else:
            alias.mkdir()
            with self.observation().guard():
                self.assertEqual(self.read(policy=self.policy(store=alias)), self.expected)

    def test_source_equal_and_nested_declarations_still_fail_pure_cp2(self):
        for target in (self.source, self.source / "includes"):
            value = deepcopy(self.value)
            next(item for item in value["bindings"] if item["root_id"] == "logs")["path"] = str(target)
            with self.subTest(target=target.name), self.no_access_observation().guard():
                self.denied("AUTHORIZATION_PATH_ALIAS", open_preflight, value,
                            policy=self.policy(), gate="FAIL")

    def test_unexpected_file_is_not_opened_or_read(self):
        for name in ("unexpected.sas", ".hidden.sas"):
            with self.subTest(name=name):
                extra = self.source / name
                extra.write_bytes(b"SYNTHETIC SENTINEL NEVER READ")
                try:
                    observation = self.observation()
                    with observation.guard():
                        self.denied("CP3A_MEMBERSHIP_CHANGED", open_preflight, self.value,
                                    policy=self.policy())
                    self.assertFalse(observation.reads)
                    self.assertFalse(any(str(item[0]) == extra.name for item in observation.opens))
                    self.assertFalse(self.store.parent.exists())
                finally:
                    extra.unlink()

    def test_unexpected_empty_directory_is_rejected_before_descent(self):
        for name in ("unexpected", ".hidden-directory"):
            with self.subTest(name=name):
                extra = self.source / name
                extra.mkdir()
                try:
                    extra_id = object_id(extra.stat())
                    observation = self.observation()
                    with observation.guard():
                        self.denied("CP3A_MEMBERSHIP_CHANGED", open_preflight, self.value,
                                    policy=self.policy())
                    self.assertNotIn(extra_id, observation.scans)
                    self.assertFalse(any(item[4] == extra_id for item in observation.opens))
                    self.assertFalse(observation.reads)
                finally:
                    extra.rmdir()

    def test_unexpected_directory_beside_valid_prefix_is_not_descended(self):
        extra = self.source / "includes" / "unapproved"
        extra.mkdir()
        (extra / "secret.sas").write_bytes(b"SYNTHETIC OUTSIDE SENTINEL")
        extra_id = object_id(extra.stat())
        observation = self.observation()
        with observation.guard():
            self.denied("CP3A_MEMBERSHIP_CHANGED", open_preflight, self.value, policy=self.policy())
        self.assertNotIn(extra_id, observation.scans)
        self.assertFalse(any(item[4] == extra_id for item in observation.opens))
        self.assertFalse(observation.reads)

    def test_missing_last_file_prevents_all_content_reads(self):
        self.paths["src:main.sas"].unlink()
        observation = self.observation()
        with observation.guard():
            self.denied("CP3A_MEMBERSHIP_CHANGED", open_preflight, self.value, policy=self.policy())
        self.assertFalse(observation.reads)
        self.assertFalse(self.store.parent.exists())

    def test_native_denied_last_file_prevents_all_content_reads(self):
        if os.geteuid() == 0:
            self.skipTest("Root bypasses native mode denial; this is not permission qualification")
        target = self.paths["src:main.sas"]
        target.chmod(0)
        observation = self.observation()
        try:
            with observation.guard():
                self.denied("CP3A_ACCESS_UNAVAILABLE", open_preflight, self.value, policy=self.policy())
            self.assertFalse(observation.reads)
            self.assertFalse(self.store.parent.exists())
        finally:
            target.chmod(0o600)

    def test_injected_last_file_open_failure_closes_all_previous_handles(self):
        observation = self.observation()
        def fail_last(path, flags, parent):
            if str(path) == "main.sas":
                raise PermissionError(errno.EACCES, "SYNTHETIC PRIVATE ERROR")
        observation.before_open = fail_last
        with observation.guard():
            self.denied("CP3A_ACCESS_UNAVAILABLE", open_preflight, self.value, policy=self.policy())
        self.assertFalse(observation.reads)
        self.assertTrue(observation.opens)

    def test_oversized_file_is_rejected_from_metadata_before_any_source_read(self):
        from sas_re._io_common import MAX_BYTES
        with self.paths["src:main.sas"].open("wb") as target:
            target.truncate(MAX_BYTES + 1)
        observation = self.observation()
        with observation.guard():
            self.denied("CP3A_LIMIT", open_preflight, self.value, policy=self.policy())
        self.assertFalse(observation.reads)
        self.assertFalse(self.store.parent.exists())

    def test_file_swap_between_metadata_and_last_read_handle_is_rejected(self):
        replacement = self.anchor / "replacement.sas"
        replacement.write_bytes(b"SYNTHETIC REPLACEMENT NEVER READ")
        observation = self.observation()
        def swap(path, flags, parent):
            if str(path) == "main.sas":
                replacement.replace(self.paths["src:main.sas"])
        observation.before_open = swap
        with observation.guard(forbid_mutations=False):
            self.denied("CP3A_BINDING_CHANGED", open_preflight, self.value, policy=self.policy())
        self.assertFalse(observation.reads)

    def test_root_swap_during_last_handle_acquisition_is_rejected_before_ready(self):
        observation = self.observation()
        def swap(path, flags, parent, fd):
            if str(path) == "main.sas":
                self.source.rename(self.anchor / "moved-sources")
                self.source.mkdir()
        observation.after_open = swap
        with observation.guard(forbid_mutations=False):
            self.denied("CP3A_BINDING_CHANGED", open_preflight, self.value, policy=self.policy())
        self.assertFalse(observation.reads)

    def test_source_and_store_symlink_roots_are_never_followed(self):
        link = self.anchor / "alias"
        link.symlink_to(self.source, target_is_directory=True)
        variants = ((deepcopy(self.value), self.policy(store=link)),)
        value = deepcopy(self.value)
        next(item for item in value["bindings"] if item["root_id"] == "src")["path"] = str(link)
        variants += ((value, self.policy(value=value)),)
        for value, policy in variants:
            observation = self.observation()
            with self.subTest(path=policy.store_path), observation.guard():
                self.denied("CP3A_UNSAFE_TYPE", open_preflight, value, policy=policy, gate="FAIL")
            self.assertFalse(observation.reads)

    def test_intermediate_and_leaf_symlinks_are_rejected_without_outside_read(self):
        outside = self.anchor / "outside"
        outside.mkdir()
        (outside / "common.sas").write_bytes(b"SYNTHETIC OUTSIDE CONTENT")
        for mode in ("leaf", "directory"):
            with self.subTest(mode=mode):
                if mode == "leaf":
                    target = self.paths["src:includes/common.sas"]
                    target.unlink()
                    target.symlink_to(outside / "common.sas")
                else:
                    target = self.source / "includes"
                    (target / "common.sas").unlink()
                    target.rmdir()
                    target.symlink_to(outside, target_is_directory=True)
                observation = self.observation()
                with observation.guard():
                    self.denied("CP3A_UNSAFE_TYPE", open_preflight, self.value,
                                policy=self.policy(), gate="FAIL")
                self.assertFalse(observation.reads)

    def test_hardlink_and_fifo_are_rejected_without_content_read(self):
        target = self.paths["src:main.sas"]
        outside_link = self.anchor / "outside-hardlink.sas"
        os.link(target, outside_link)
        observation = self.observation()
        with observation.guard():
            self.denied("CP3A_UNSAFE_TYPE", open_preflight, self.value, policy=self.policy(), gate="FAIL")
        self.assertFalse(observation.reads)
        outside_link.unlink()
        target.unlink()
        os.mkfifo(target)
        observation = self.observation()
        with observation.guard():
            self.denied("CP3A_UNSAFE_TYPE", open_preflight, self.value, policy=self.policy(), gate="FAIL")
        self.assertFalse(observation.reads)

    def test_root_replacement_after_preflight_denies_before_read(self):
        observation = self.observation()
        with observation.guard(forbid_mutations=False):
            session = open_preflight(self.value, policy=self.policy())
            self.source.rename(self.anchor / "moved-sources")
            self.source.mkdir()
            self.denied("CP3A_BINDING_CHANGED", session.read_sources)
            session.close()
        self.assertFalse(observation.reads)
        self.assertFalse(self.store.parent.exists())

    def test_intermediate_directory_replacement_after_preflight_denies_before_read(self):
        observation = self.observation()
        with observation.guard(forbid_mutations=False):
            session = open_preflight(self.value, policy=self.policy())
            (self.source / "includes").rename(self.anchor / "moved-includes")
            (self.source / "includes").mkdir()
            self.denied("CP3A_BINDING_CHANGED", session.read_sources)
            session.close()
        self.assertFalse(observation.reads)

    def test_file_replacement_after_preflight_denies_before_read(self):
        observation = self.observation()
        replacement = self.anchor / "replacement.sas"
        replacement.write_bytes(b"SYNTHETIC REPLACEMENT NEVER READ")
        with observation.guard(forbid_mutations=False):
            session = open_preflight(self.value, policy=self.policy())
            replacement.replace(self.paths["src:main.sas"])
            self.denied("CP3A_MEMBERSHIP_CHANGED", session.read_sources)
            session.close()
        self.assertFalse(observation.reads)

    def test_late_hardlink_invalidates_ready_session_before_content(self):
        observation = self.observation()
        with observation.guard(forbid_mutations=False):
            session = open_preflight(self.value, policy=self.policy())
            os.link(self.paths["src:main.sas"], self.anchor / "late-hardlink.sas")
            with self.assertRaises(EvidenceError) as caught:
                session.read_sources()
            self.assertIn(caught.exception.code, {"CP3A_UNSAFE_TYPE", "CP3A_SOURCE_CHANGED", "CP3A_BINDING_CHANGED"})
            session.close()
        self.assertFalse(observation.reads)

    def test_membership_change_after_preflight_denies_before_read(self):
        observation = self.observation()
        with observation.guard(forbid_mutations=False):
            session = open_preflight(self.value, policy=self.policy())
            (self.source / "late.sas").write_bytes(b"SYNTHETIC LATE FILE")
            self.denied("CP3A_MEMBERSHIP_CHANGED", session.read_sources)
            session.close()
        self.assertFalse(observation.reads)

    def test_same_size_rewrite_with_restored_mtime_is_detected(self):
        target = self.paths["src:main.sas"]
        before = target.stat()
        observation = self.observation()
        with observation.guard(forbid_mutations=False):
            session = open_preflight(self.value, policy=self.policy())
            target.write_bytes(RAW_VARIANTS["changed"])
            os.utime(target, ns=(before.st_atime_ns, before.st_mtime_ns))
            self.denied("CP3A_BINDING_CHANGED", session.read_sources)
            session.close()
        self.assertFalse(observation.reads)

    def test_mutation_after_first_read_invalidates_whole_result(self):
        observation = self.observation()
        mutated = False
        def mutate(fd, raw):
            nonlocal mutated
            if raw and not mutated:
                mutated = True
                self.paths["src:main.sas"].write_bytes(RAW_VARIANTS["changed"])
        observation.after_read = mutate
        with observation.guard(forbid_mutations=False):
            session = open_preflight(self.value, policy=self.policy())
            self.denied("CP3A_BINDING_CHANGED", session.read_sources)
            session.close()
        self.assertTrue(mutated)
        self.assertFalse(self.store.parent.exists())

    def test_mutating_an_already_read_file_invalidates_later_result(self):
        observation = self.observation()
        first = None
        mutated = False
        id_paths = {object_id(path.stat()): path for path in self.paths.values()}
        def mutate_prior(fd, raw):
            nonlocal first, mutated
            current = object_id(observation.original_fstat(fd))
            if raw and first is None:
                first = current
            elif raw and current != first and not mutated:
                mutated = True
                path = id_paths[first]
                path.write_bytes(path.read_bytes() + b"SYNTHETIC LATE CHANGE\n")
        observation.after_read = mutate_prior
        with observation.guard(forbid_mutations=False):
            session = open_preflight(self.value, policy=self.policy())
            self.denied("CP3A_BINDING_CHANGED", session.read_sources)
            session.close()
        self.assertTrue(mutated)
        self.assertFalse(self.store.parent.exists())

    def test_store_parent_replacement_invalidates_session_without_creation(self):
        self.store.parent.mkdir()
        observation = self.observation()
        with observation.guard(forbid_mutations=False):
            session = open_preflight(self.value, policy=self.policy())
            self.store.parent.rename(self.anchor / "old-output")
            self.store.parent.mkdir()
            self.denied("CP3A_BINDING_CHANGED", session.read_sources)
            session.close()
        self.assertFalse(observation.reads)
        self.assertFalse(self.store.exists())

    def test_context_exception_and_closed_session_release_resources(self):
        observation = self.observation()
        with observation.guard():
            with self.assertRaisesRegex(RuntimeError, "synthetic cancellation"):
                with open_preflight(self.value, policy=self.policy()) as session:
                    raise RuntimeError("synthetic cancellation")
            self.assertEqual(session.state, "CLOSED")
            session.close()
            self.denied("CP3A_SESSION_CLOSED", session.read_sources)
        self.assertFalse(observation.reads)

    def test_read_failure_and_keyboard_interrupt_close_resources(self):
        for failure in (OSError(errno.EIO, "synthetic private failure"), KeyboardInterrupt()):
            observation = self.observation()
            def fail(fd, count):
                raise failure
            observation.before_read = fail
            with self.subTest(failure=type(failure).__name__), observation.guard():
                session = open_preflight(self.value, policy=self.policy())
                if isinstance(failure, KeyboardInterrupt):
                    with self.assertRaises(KeyboardInterrupt):
                        session.read_sources()
                else:
                    self.denied("CP3A_ACCESS_UNAVAILABLE", session.read_sources)
                self.assertEqual(session.state, "CLOSED")

    def test_ambiguous_close_blocks_result_and_attempts_all_handles_once(self):
        observation = self.observation()
        with observation.guard():
            session = open_preflight(self.value, policy=self.policy())
            retained = set(observation.active)
            closes = []
            native_close = observation.original_close
            def uncertain_once(fd):
                # Really close this synthetic descriptor, then report EINTR.
                # That is a safe deterministic simulation of uncertain close
                # status; it does not leave a descriptor intentionally leaked.
                native_close(fd)
                if fd in retained:
                    closes.append(fd)
                    if len(closes) == 1:
                        raise OSError(errno.EINTR, "synthetic uncertain close")
            observation.original_close = uncertain_once
            self.denied("CP3A_CLOSE_UNCERTAIN", session.read_sources)
            self.assertEqual(session.state, "CLOSED")
            self.assertEqual(set(closes), retained)
            self.assertEqual(len(closes), len(retained), "Ambiguous close must not be retried")
            session.close()
            self.assertEqual(len(closes), len(retained))
            self.denied("CP3A_SESSION_CLOSED", session.read_sources)
        self.assertTrue(observation.reads)
        self.assertFalse(self.store.parent.exists())

    def test_input_mutation_cannot_rebind_detached_ready_session(self):
        observation = self.observation()
        with observation.guard():
            session = open_preflight(self.value, policy=self.policy())
            self.value["bindings"][0]["path"] = "/outside/forged"
            self.value["logical_scope"]["files"].clear()
            self.assertEqual(session.read_sources(), self.expected)
        self.assertFalse(self.store.parent.exists())

    def test_success_is_single_use_and_never_becomes_publication_authority(self):
        observation = self.observation()
        with observation.guard():
            session = open_preflight(self.value, policy=self.policy())
            self.assertEqual(session.read_sources(), self.expected)
            self.denied("CP3A_SESSION_CLOSED", session.read_sources)
            session.close()
            self.assertFalse(hasattr(session, "publish"))
        self.assertFalse(self.store.parent.exists())

    def test_original_byte_vectors_keep_frozen_source_and_operation_identities(self):
        for variant, raw in RAW_VARIANTS.items():
            with self.subTest(variant=variant):
                self.paths["src:main.sas"].write_bytes(raw)
                with self.observation().guard():
                    actual = self.read()
                expected = EXPECTED_IDENTITIES[variant]
                self.assertEqual(actual, {"src:main.sas": raw, **RAW_OTHER})
                self.assertEqual(hashlib.sha256(actual["src:main.sas"]).hexdigest(),
                                 expected["main_sha256"])
                files = oracle_files(variant)
                for entry in files:
                    self.assertEqual(hashlib.sha256(actual[entry["file_key"]]).hexdigest(), entry["sha256"])
                fingerprint = oracle_hash({"scope_sha256": authorization_scope_identity(self.value),
                                           "files": files})
                self.assertEqual(authorization_scope_identity(self.value), EXPECTED_SCOPE_SHA256)
                self.assertEqual(fingerprint, expected["source_fingerprint"])
                self.assertEqual(identity("op", fingerprint, operation_payload()), expected["operation_id"])
                self.assertEqual(oracle_id("op", fingerprint, operation_payload()), expected["operation_id"])

    def test_existing_sealed_artifacts_remain_byte_identical(self):
        old_scope = {"schema_version": "1.0", **deepcopy(self.value["logical_scope"])}
        old_scope["roots"] = [{"root_id": item["root_id"], "path": item["path"]}
                              for item in self.value["bindings"]]
        old_inventory = build_inventory(old_scope, "historical")
        historical_store = self.anchor / "sealed-history"
        writer = AttemptStore(historical_store, [self.source, self.logs])
        metadata = {"schema_version": "1.0", "stage": "DISCOVER", "module_ids": ["analyze", "prepare"]}
        attempt = writer.begin("synthetic-cp2", "run-1", "historical", metadata)
        attempt.publish({"source_inventory.json": old_inventory}, {
            **metadata, "stage_gate": "BLOCKED", "artifact_authority": "DRAFT",
            "semantic_verification": "UNVERIFIABLE"})
        before = {str(path.relative_to(historical_store)): path.read_bytes()
                  for path in historical_store.rglob("*") if path.is_file()}
        with self.observation().guard():
            self.assertEqual(self.read(policy=self.policy(store=historical_store)), self.expected)
        after = {str(path.relative_to(historical_store)): path.read_bytes()
                 for path in historical_store.rglob("*") if path.is_file()}
        self.assertEqual(before, after)


class PreflightPlatformBoundaryTests(unittest.TestCase):
    def test_windows_selection_denies_before_caller_metadata_or_source_io(self):
        value = envelope("windows")
        validate_authorization(value)
        with patch.object(sys, "platform", "win32"), \
                patch("os.open", side_effect=AssertionError("Windows attempted native access")), \
                patch("os.scandir", side_effect=AssertionError("Windows attempted enumeration")), \
                patch("os.mkdir", side_effect=AssertionError("Windows attempted store creation")):
            with self.assertRaises(EvidenceError) as caught:
                open_preflight(value, policy=None)
        self.assertEqual(caught.exception.gate, "BLOCKED")
        self.assertEqual(caught.exception.code, "FILESYSTEM_CAPABILITY_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
