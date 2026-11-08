"""Adversarial synthetic filesystem and publication checks preserve fail-closed attempt semantics."""

import hashlib
import multiprocessing
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sas_re.safeio import (
    Attempt,
    AttemptStore,
    EvidenceError,
    canonical_bytes,
    ensure_disjoint,
    enumerate_files,
    read_json,
    require_safe_root,
    safe_relative,
    secure_read,
)
import sas_re._filesystem._posix_io as safeio


def _concurrent_begin(path, ready, start, results):
    """A separate process contends for the exact same attempt directory."""
    store = AttemptStore(Path(path), [])
    ready.put(True)
    if not start.wait(15):
        results.put(("TIMEOUT", "BLOCKED"))
        return
    try:
        store.begin("synthetic", "run1", "attempt1", {})
        results.put(("STARTED", "PASS"))
    except EvidenceError as error:
        results.put((error.code, error.gate))


def _concurrent_publish(path, directory_identity, ready, start, results, writer):
    attempt = Attempt(Path(path), "workspace1", "run1", "attempt1", directory_identity)
    ready.put(True)
    if not start.wait(15):
        results.put(("TIMEOUT", "BLOCKED"))
        return
    try:
        attempt.publish(
            {"source_inventory.json": {"writer": writer}},
            {
                "schema_version": "1.0.0",
                "stage": "DISCOVER",
                "module_ids": ["module1"],
                "stage_gate": "PASS",
                "artifact_authority": "DRAFT",
                "semantic_verification": "UNVERIFIABLE",
            },
        )
        results.put(("COMPLETE", "PASS"))
    except EvidenceError as error:
        results.put((error.code, error.gate))


def _exit_before_seal(path, directory_identity):
    attempt = Attempt(Path(path), "workspace1", "run1", "attempt1", directory_identity)
    original = safeio._atomic_json

    def crash(fd, name, payload):
        if name == "seal.json":
            os._exit(71)
        return original(fd, name, payload)

    with patch("sas_re._filesystem._posix_io._atomic_json", side_effect=crash):
        attempt.publish(
            {"source_inventory.json": {"synthetic": True}},
            {
                "schema_version": "1.0.0",
                "stage": "DISCOVER",
                "module_ids": ["module1"],
                "stage_gate": "PASS",
                "artifact_authority": "DRAFT",
                "semantic_verification": "UNVERIFIABLE",
            },
        )


class SafeIOTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / "source"
        self.source.mkdir()
        self.file = self.source / "program.sas"
        self.file.write_bytes(b"/* SYNTHETIC ONLY */\r\ndata work.test;\r\nrun;\r\n")

    def assert_error(self, code, callable_, *args, **kwargs):
        with self.assertRaises(EvidenceError) as error:
            callable_(*args, **kwargs)
        self.assertEqual(error.exception.code, code)
        return error.exception

    def test_source_read_preserves_original_bytes_and_newlines(self):
        before = self.file.read_bytes()
        before_metadata = self.file.stat()
        self.assertEqual(secure_read(self.source, "program.sas"), before)
        self.assertEqual(self.file.read_bytes(), before)
        self.assertEqual(self.file.stat().st_mtime_ns, before_metadata.st_mtime_ns)
        self.assertEqual(self.file.stat().st_mode, before_metadata.st_mode)

    def test_relative_names_reject_traversal_ambiguous_and_control_paths(self):
        for value in [
            "",
            "/etc/passwd",
            "../secret",
            "a/../b",
            "a/./b",
            "a//b",
            "a/",
            "a\\b",
            "a\x00b",
            "a\nb",
            "é.sas",
            "a b",
            ".",
            "..",
            "x" * 129,
        ]:
            with self.subTest(value=repr(value)):
                self.assert_error("UNSAFE_PATH", safe_relative, value)
        self.assertEqual(safe_relative("includes/synthetic_v1.sas"), "includes/synthetic_v1.sas")

    def test_root_requires_absolute_path_and_rejects_symlink_components(self):
        self.assert_error("ABSOLUTE_ROOT_REQUIRED", require_safe_root, Path("relative"))
        link = self.root / "link"
        link.symlink_to(self.source, target_is_directory=True)
        self.assert_error("UNSAFE_OR_UNAVAILABLE_PATH", require_safe_root, link)
        self.assert_error("UNSAFE_OR_UNAVAILABLE_PATH", secure_read, link, "program.sas")

    def test_nul_controls_and_unencodable_root_paths_fail_with_fixed_code(self):
        for value in [
            str(self.root) + "/private\x00root",
            str(self.root) + "/private\nroot",
            str(self.root) + "/private\ud800root",
        ]:
            with self.subTest(value=repr(value)):
                error = self.assert_error("UNSAFE_PATH", require_safe_root, value)
                self.assertNotIn("private", str(error))

    def test_source_symlink_and_symlink_directory_are_rejected(self):
        (self.source / "alias.sas").symlink_to(self.file)
        self.assert_error("UNSAFE_OR_UNAVAILABLE_FILE", secure_read, self.source, "alias.sas")
        self.assert_error("UNSAFE_FILE_TYPE", enumerate_files, self.source)
        (self.source / "alias.sas").unlink()
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "secret.txt").write_bytes(b"synthetic private sentinel")
        (self.source / "escape").symlink_to(outside, target_is_directory=True)
        self.assert_error(
            "UNSAFE_OR_UNAVAILABLE_PATH", secure_read, self.source, "escape/secret.txt"
        )
        self.assert_error("UNSAFE_FILE_TYPE", enumerate_files, self.source)

    def test_hardlinked_file_rejected(self):
        os.link(self.file, self.source / "alias.sas")
        self.assert_error("UNSAFE_FILE_TYPE", secure_read, self.source, "program.sas")
        self.assert_error("UNSAFE_FILE_TYPE", enumerate_files, self.source)

    def test_fifo_is_rejected_without_blocking(self):
        os.mkfifo(self.source / "pipe")
        self.assert_error("UNSAFE_FILE_TYPE", secure_read, self.source, "pipe")
        self.assert_error("UNSAFE_FILE_TYPE", enumerate_files, self.source)

    def test_file_size_read_limits_and_depth_are_bounded(self):
        self.assert_error("FILE_SIZE_LIMIT", secure_read, self.source, "program.sas", 4)
        for limit in [0, -1, True, safeio.MAX_BYTES + 1]:
            self.assert_error("INVALID_READ_LIMIT", secure_read, self.source, "program.sas", limit)
        self.assert_error("PATH_DEPTH_LIMIT", safe_relative, "/".join(["a"] * 33))

    def test_inventory_is_sorted_and_bounded(self):
        (self.source / "includes").mkdir()
        (self.source / "includes" / "x.sas").write_bytes(b"/* SYNTHETIC */")
        self.assertEqual(enumerate_files(self.source), ["includes/x.sas", "program.sas"])
        with patch.object(safeio, "MAX_FILES", 1):
            self.assert_error("INVENTORY_LIMIT", enumerate_files, self.source)
        with patch.object(safeio, "MAX_DIRECTORIES", 0):
            self.assert_error("INVENTORY_LIMIT", enumerate_files, self.source)

    def test_source_changed_during_read_rejected(self):
        original_read = os.read
        changed = False

        def mutating_read(fd, count):
            nonlocal changed
            data = original_read(fd, count)
            if not changed:
                changed = True
                self.file.write_bytes(b"/* SYNTHETIC CHANGED */")
            return data

        with patch("sas_re._filesystem._posix_io.os.read", side_effect=mutating_read):
            self.assert_error("FILE_CHANGED_DURING_READ", secure_read, self.source, "program.sas")

    def test_replacement_during_read_rejected(self):
        original_read = os.read
        changed = False

        def replacing_read(fd, count):
            nonlocal changed
            data = original_read(fd, count)
            if not changed:
                changed = True
                replacement = self.source / "replacement"
                replacement.write_bytes(self.file.read_bytes())
                replacement.replace(self.file)
            return data

        with patch("sas_re._filesystem._posix_io.os.read", side_effect=replacing_read):
            self.assert_error("FILE_CHANGED_DURING_READ", secure_read, self.source, "program.sas")

    def test_canonical_json_utf8_sorted_and_finite(self):
        self.assertEqual(canonical_bytes({"z": "é", "a": 1}), b'{"a":1,"z":"\xc3\xa9"}\n')
        for value in [float("nan"), float("inf"), {1: "bad key"}, {"x": object()}]:
            self.assert_error("JSON_INVALID", canonical_bytes, value)

    def test_json_duplicates_nonfinite_utf8_and_excess_depth_rejected(self):
        fixture = self.source / "record.json"
        cases = [
            (b'{"x":1,"x":2}', "JSON_DUPLICATE_KEY"),
            (b'{"x":NaN}', "JSON_NONFINITE"),
            (b'{"x":Infinity}', "JSON_NONFINITE"),
            (b'{"x":1e9999}', "JSON_INVALID"),
            (b'{"x":"\xff"}', "JSON_INVALID"),
            (b"[" * 66 + b"0" + b"]" * 66, "JSON_DEPTH_LIMIT"),
        ]
        for content, code in cases:
            fixture.write_bytes(content)
            with self.subTest(code=code):
                self.assert_error(code, read_json, fixture)

    def test_output_store_cannot_overlap_source(self):
        for path in [self.source, self.source / "artifacts", self.root]:
            with self.subTest(path=path):
                self.assert_error("OUTPUT_SOURCE_OVERLAP", ensure_disjoint, path, [self.source])
                self.assert_error("OUTPUT_SOURCE_OVERLAP", AttemptStore, path, [self.source])
        self.assertFalse((self.source / "artifacts").exists())

    def test_errors_do_not_echo_source_paths_or_os_messages(self):
        with self.assertRaises(EvidenceError) as error:
            secure_read(self.source, "private_sentinel_not_found")
        self.assertNotIn("private_sentinel", str(error.exception))
        self.assertNotIn(str(self.source), str(error.exception))
        self.assertEqual(str(EvidenceError("private contents")), "INVALID_ERROR_CODE")


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.store = AttemptStore(self.root / "artifacts", [])
        self.metadata = {"schema_version": "1.0.0", "stage": "DISCOVER", "module_ids": ["module1"]}
        self.seal_metadata = {
            **self.metadata,
            "stage_gate": "PASS",
            "artifact_authority": "DRAFT",
            "semantic_verification": "UNVERIFIABLE",
        }

    def begin(self):
        return self.store.begin("workspace1", "run1", "attempt1", self.metadata)

    def assert_error(self, code, callable_, *args, **kwargs):
        with self.assertRaises(EvidenceError) as error:
            callable_(*args, **kwargs)
        self.assertEqual(error.exception.code, code)
        return error.exception

    def test_publish_roundtrip_seal_hashes_original_bytes_and_attempt_metadata(self):
        attempt = self.begin()
        records = {
            "source_inventory.json": {"synthetic": True},
            "validation_report.json": {"stage_gate": "PASS"},
        }
        seal = attempt.publish(records, self.seal_metadata)
        loaded, read_seal = self.store.read_attempt("workspace1", "run1", "attempt1")
        self.assertEqual(loaded, records)
        self.assertEqual(seal, read_seal)
        self.assertEqual(seal["publication_state"], "COMPLETE")
        for name, digest in seal["artifacts"].items():
            self.assertEqual(hashlib.sha256((attempt.path / name).read_bytes()).hexdigest(), digest)
            self.assertEqual((attempt.path / name).stat().st_mode & 0o777, 0o400)
        self.assertIn("attempt.json", seal["artifacts"])

    def test_duplicate_attempt_and_repeat_publication_never_overwrite(self):
        attempt = self.begin()
        started = (attempt.path / "attempt.json").read_bytes()
        error = self.assert_error("ATTEMPT_EXISTS", self.begin)
        self.assertEqual(error.gate, "BLOCKED")
        self.assertEqual((attempt.path / "attempt.json").read_bytes(), started)
        attempt.publish({"source_inventory.json": {"synthetic": True}}, self.seal_metadata)
        sealed = (attempt.path / "seal.json").read_bytes()
        self.assert_error(
            "ATTEMPT_ALREADY_SEALED",
            attempt.publish,
            {"source_inventory.json": {"changed": True}},
            self.seal_metadata,
        )
        self.assertEqual((attempt.path / "seal.json").read_bytes(), sealed)

    def test_interrupted_publication_preserves_partial_files_without_success_seal(self):
        attempt = self.begin()
        original = safeio._atomic_json

        def interrupted(fd, name, payload):
            if name == "seal.json":
                raise RuntimeError("synthetic crash before seal")
            return original(fd, name, payload)

        with patch("sas_re._filesystem._posix_io._atomic_json", side_effect=interrupted):
            with self.assertRaises(RuntimeError):
                attempt.publish({"source_inventory.json": {"synthetic": True}}, self.seal_metadata)
        self.assertTrue((attempt.path / "source_inventory.json").is_file())
        self.assertTrue((attempt.path / "attempt.json").is_file())
        self.assertFalse((attempt.path / "seal.json").exists())
        error = self.assert_error(
            "INCOMPLETE_ATTEMPT", self.store.read_attempt, "workspace1", "run1", "attempt1"
        )
        self.assertEqual(error.gate, "BLOCKED")
        self.assert_error(
            "INCOMPLETE_ATTEMPT",
            attempt.publish,
            {"source_inventory.json": {"synthetic": True}},
            self.seal_metadata,
        )

    def test_partial_file_write_is_retained_and_never_sealed(self):
        attempt = self.begin()
        original_write = os.write
        calls = 0

        def interrupted(fd, data):
            nonlocal calls
            calls += 1
            if calls > 1:
                raise OSError("synthetic private diagnostics")
            return original_write(fd, data[:3])

        with patch("sas_re._filesystem._posix_io.os.write", side_effect=interrupted):
            error = self.assert_error(
                "PUBLICATION_IO_FAILURE",
                attempt.publish,
                {"source_inventory.json": {"synthetic": True}},
                self.seal_metadata,
            )
        self.assertNotIn("private diagnostics", str(error))
        self.assertTrue(list(attempt.path.glob("*.tmp")))
        self.assertFalse((attempt.path / "seal.json").exists())
        self.assert_error(
            "INCOMPLETE_ATTEMPT", self.store.read_attempt, "workspace1", "run1", "attempt1"
        )

    def test_missing_seal_is_blocked_even_if_attempt_has_no_artifacts(self):
        self.begin()
        self.assert_error(
            "INCOMPLETE_ATTEMPT", self.store.read_attempt, "workspace1", "run1", "attempt1"
        )

    def test_actual_process_exit_before_seal_retains_failed_attempt(self):
        attempt = self.begin()
        process = multiprocessing.get_context("spawn").Process(
            target=_exit_before_seal, args=(str(attempt.path), attempt.directory_identity)
        )
        process.start()
        try:
            process.join(timeout=15)
            self.assertEqual(process.exitcode, 71)
        finally:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
        self.assertEqual(
            set(child.name for child in attempt.path.iterdir()),
            {"attempt.json", "source_inventory.json"},
        )
        self.assert_error(
            "INCOMPLETE_ATTEMPT", self.store.read_attempt, "workspace1", "run1", "attempt1"
        )
        self.assert_error("ATTEMPT_EXISTS", self.begin)

    def test_artifact_tampering_is_detected(self):
        attempt = self.begin()
        attempt.publish({"source_inventory.json": {"synthetic": True}}, self.seal_metadata)
        artifact = attempt.path / "source_inventory.json"
        artifact.chmod(0o600)
        artifact.write_bytes(b'{"synthetic":false}\n')
        self.assert_error(
            "ARTIFACT_HASH_MISMATCH", self.store.read_attempt, "workspace1", "run1", "attempt1"
        )

    def test_extra_file_and_missing_file_are_detected(self):
        attempt = self.begin()
        attempt.publish({"source_inventory.json": {"synthetic": True}}, self.seal_metadata)
        extra = attempt.path / "extra.json"
        extra.write_bytes(b"{}\n")
        self.assert_error(
            "ATTEMPT_CONTENT_MISMATCH", self.store.read_attempt, "workspace1", "run1", "attempt1"
        )
        extra.unlink()
        (attempt.path / "source_inventory.json").unlink()
        self.assert_error(
            "ATTEMPT_CONTENT_MISMATCH", self.store.read_attempt, "workspace1", "run1", "attempt1"
        )

    def test_attempt_and_seal_identity_conflicts_rejected(self):
        self.assert_error(
            "ATTEMPT_IDENTITY_MISMATCH",
            self.store.begin,
            "workspace1",
            "run1",
            "attempt1",
            {"run_id": "another"},
        )
        attempt = self.begin()
        self.assert_error(
            "ATTEMPT_IDENTITY_MISMATCH",
            attempt.publish,
            {"source_inventory.json": {}},
            {"run_id": "another"},
        )
        self.assert_error(
            "ATTEMPT_IDENTITY_MISMATCH",
            attempt.publish,
            {"source_inventory.json": {}},
            {**self.seal_metadata, "module_ids": ["other"]},
        )
        self.assertFalse((attempt.path / "seal.json").exists())
        attempt.publish({"source_inventory.json": {}}, self.seal_metadata)
        seal_path = attempt.path / "seal.json"
        seal = read_json(seal_path)
        seal["module_ids"] = ["other"]
        seal_path.chmod(0o600)
        seal_path.write_bytes(canonical_bytes(seal))
        self.assert_error(
            "ATTEMPT_IDENTITY_MISMATCH", self.store.read_attempt, "workspace1", "run1", "attempt1"
        )

    def test_artifact_filename_allowlist_blocks_traversal_and_arbitrary_files(self):
        attempt = self.begin()
        for name in ["../escape.json", "seal.json", "attempt.json", "unapproved.json"]:
            with self.subTest(name=name):
                self.assert_error(
                    "INVALID_ARTIFACT_NAMES", attempt.publish, {name: {}}, self.seal_metadata
                )
        self.assertEqual(set(child.name for child in attempt.path.iterdir()), {"attempt.json"})

    def test_existing_artifact_never_replaced_by_atomic_install(self):
        attempt = self.begin()
        with safeio._directory(attempt.path) as fd:
            safeio._atomic_json(fd, "source_inventory.json", {"first": True})
            self.assert_error(
                "ARTIFACT_EXISTS",
                safeio._atomic_json,
                fd,
                "source_inventory.json",
                {"first": False},
            )
        self.assertEqual(read_json(attempt.path / "source_inventory.json"), {"first": True})

    def test_store_parent_symlink_and_attempt_symlink_rejected(self):
        (self.root / "alias").symlink_to(self.root / "artifacts", target_is_directory=True)
        self.assert_error(
            "UNSAFE_OR_UNAVAILABLE_PATH", AttemptStore, self.root / "alias" / "new", []
        )
        self.assertFalse((self.root / "artifacts" / "new").exists())
        (self.root / "artifacts" / "workspace1").symlink_to(self.root, target_is_directory=True)
        self.assert_error("PUBLICATION_IO_FAILURE", self.begin)
        self.assertFalse((self.root / "run1").exists())

    def test_actual_multiprocess_attempt_reservation_race(self):
        context = multiprocessing.get_context("spawn")
        ready = context.Queue()
        results = context.Queue()
        start = context.Event()
        processes = [
            context.Process(
                target=_concurrent_begin, args=(str(self.store.path), ready, start, results)
            )
            for _ in range(2)
        ]
        for process in processes:
            process.start()
        try:
            for _ in processes:
                self.assertTrue(ready.get(timeout=15))
            start.set()
            outcomes = [results.get(timeout=15) for _ in processes]
            self.assertCountEqual(outcomes, [("STARTED", "PASS"), ("ATTEMPT_EXISTS", "BLOCKED")])
            for process in processes:
                process.join(timeout=15)
                self.assertEqual(process.exitcode, 0)
        finally:
            for process in processes:
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=5)
            ready.close()
            results.close()
        attempt = self.store.path / "synthetic" / "run1" / "attempt1"
        self.assertEqual(set(child.name for child in attempt.iterdir()), {"attempt.json"})
        self.assert_error(
            "INCOMPLETE_ATTEMPT", self.store.read_attempt, "synthetic", "run1", "attempt1"
        )

    def test_actual_multiprocess_publication_race_has_one_complete_writer(self):
        attempt = self.begin()
        context = multiprocessing.get_context("spawn")
        ready = context.Queue()
        results = context.Queue()
        start = context.Event()
        processes = [
            context.Process(
                target=_concurrent_publish,
                args=(str(attempt.path), attempt.directory_identity, ready, start, results, index),
            )
            for index in range(2)
        ]
        for process in processes:
            process.start()
        try:
            for _ in processes:
                self.assertTrue(ready.get(timeout=15))
            start.set()
            outcomes = [results.get(timeout=15) for _ in processes]
            self.assertEqual(outcomes.count(("COMPLETE", "PASS")), 1)
            self.assertEqual(
                sum(
                    result in {("ATTEMPT_BUSY", "BLOCKED"), ("ATTEMPT_ALREADY_SEALED", "BLOCKED")}
                    for result in outcomes
                ),
                1,
            )
            for process in processes:
                process.join(timeout=15)
                self.assertEqual(process.exitcode, 0)
        finally:
            for process in processes:
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=5)
            ready.close()
            results.close()
        records, seal = self.store.read_attempt("workspace1", "run1", "attempt1")
        self.assertIn(records["source_inventory.json"]["writer"], {0, 1})
        self.assertEqual(seal["publication_state"], "COMPLETE")
        self.assertEqual(
            set(child.name for child in attempt.path.iterdir()),
            {"attempt.json", "source_inventory.json", "seal.json"},
        )


if __name__ == "__main__":
    unittest.main()
