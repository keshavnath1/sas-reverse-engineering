"""Synthetic end-to-end P1 CLI checks, including failed-attempt retention."""

import contextlib
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fixture_support import make_graph, make_scope
from sas_re.cli import main
from sas_re.evidence import coverage
from sas_re import _posix_io as safeio
from sas_re.safeio import EvidenceError, canonical_bytes, read_json


class RunTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.scope = make_scope(self.root)
        self.scope_path = self.root / "scope.json"
        self.record_path = self.root / "record.json"
        self.store = self.root / "artifacts"
        self.write_scope()

    def write_scope(self):
        self.scope_path.write_bytes(canonical_bytes(self.scope))

    def attempt_path(self, attempt):
        return self.store / self.scope["workspace_id"] / self.scope["run_id"] / attempt

    def source_path(self, kind):
        source = next(item for item in self.scope["files"] if item["kind"] == kind)
        root = next(item for item in self.scope["roots"] if item["root_id"] == source["root_id"])
        return Path(root["path"]) / source["path"]

    def snapshot(self, path):
        return {str(item.relative_to(path)): item.read_bytes()
                for item in sorted(path.rglob("*")) if item.is_file()}

    def invoke(self, command, attempt="attempt1", *, verification_attempt=None, run=None,
               store=None, record=None):
        argv = [command, "--scope", str(self.scope_path), "--store", str(store or self.store),
                "--run", run or self.scope["run_id"], "--attempt", attempt]
        if command == "seal-source":
            argv += ["--record", str(record or self.record_path)]
        if command == "verify-source":
            argv += ["--verification-attempt", verification_attempt or "verification1"]
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(argv)
        text = output.getvalue()
        result = json.loads(text)
        self.assertEqual(result["semantic_verification"], "UNVERIFIABLE")
        self.assertEqual(result["artifact_authority"], "DRAFT")
        self.assertEqual(result["benchmark_execution"], "NOT_RUN")
        self.assertEqual(code, {"PASS": 0, "FAIL": 1, "BLOCKED": 2}[result["stage_gate"]])
        return code, result, text

    def seal(self, attempt="attempt1"):
        inventory, graph = make_graph(self.scope, attempt=attempt)
        self.record_path.write_bytes(canonical_bytes(graph))
        code, result, text = self.invoke("seal-source", attempt)
        self.assertEqual(code, 0, text)
        return inventory, graph, result

    def assert_finding(self, result, code):
        self.assertIn(code, [finding["code"] for finding in result["findings"]])

    def test_discover_publishes_inventory_and_explicit_integrity_only_seal(self):
        before = {str(root["path"]): self.snapshot(Path(root["path"])) for root in self.scope["roots"]}
        code, result, text = self.invoke("discover")
        self.assertEqual(code, 0, text)
        path = self.attempt_path("attempt1")
        self.assertEqual(set(self.snapshot(path)), {
            "attempt.json", "source_inventory.json", "validation_report.json", "seal.json"})
        inventory = read_json(path / "source_inventory.json")
        self.assertEqual(len(inventory["files"]), len(self.scope["files"]))
        self.assertEqual(inventory["attempt_id"], "attempt1")
        seal = read_json(path / "seal.json")
        self.assertEqual(seal["stage_gate"], "PASS")
        self.assertEqual(seal["semantic_verification"], "UNVERIFIABLE")
        self.assertEqual(seal["artifact_authority"], "DRAFT")
        self.assertEqual(hashlib.sha256((path / "seal.json").read_bytes()).hexdigest(), result["seal_sha256"])
        for root in self.scope["roots"]:
            self.assertEqual(before[str(root["path"])], self.snapshot(Path(root["path"])))

    def test_supplied_record_seal_and_independent_verification_roundtrip(self):
        _, graph, result = self.seal()
        original = self.snapshot(self.attempt_path("attempt1"))
        self.assertEqual(read_json(self.attempt_path("attempt1") / "source_record.json"), graph)
        code, verified, text = self.invoke("verify-source")
        self.assertEqual(code, 0, text)
        self.assertEqual(verified["subject_attempt_id"], "attempt1")
        self.assertEqual(verified["subject_seal_sha256"], result["seal_sha256"])
        self.assertEqual(verified["attempt_id"], "verification1")
        self.assertEqual(original, self.snapshot(self.attempt_path("attempt1")))
        self.assertEqual(set(self.snapshot(self.attempt_path("verification1"))), {
            "attempt.json", "verification_report.json", "seal.json"})

    def test_inventory_only_attempt_can_be_verified(self):
        self.assertEqual(self.invoke("discover")[0], 0)
        code, _, text = self.invoke("verify-source")
        self.assertEqual(code, 0, text)

    def test_duplicate_attempt_blocks_and_preserves_all_original_bytes(self):
        self.seal()
        before = self.snapshot(self.store)
        code, result, _ = self.invoke("discover")
        self.assertEqual(code, 2)
        self.assert_finding(result, "ATTEMPT_EXISTS")
        self.assertEqual(before, self.snapshot(self.store))

    def test_verification_cannot_reuse_subject_or_prior_verification_attempt(self):
        self.seal()
        before = self.snapshot(self.store)
        code, result, _ = self.invoke("verify-source", verification_attempt="attempt1")
        self.assertEqual(code, 2)
        self.assert_finding(result, "VERIFICATION_ATTEMPT_REUSED")
        self.assertEqual(before, self.snapshot(self.store))
        self.assertEqual(self.invoke("verify-source")[0], 0)
        before = self.snapshot(self.store)
        self.assertEqual(self.invoke("verify-source")[0], 2)
        self.assertEqual(before, self.snapshot(self.store))

    def test_changed_source_invalidates_without_rewriting_historical_seal(self):
        _, _, sealed = self.seal()
        before = self.snapshot(self.attempt_path("attempt1"))
        source = self.source_path("SAS")
        source.write_bytes(source.read_bytes() + b"\n/* SYNTHETIC changed source */\n")
        code, result, _ = self.invoke("verify-source")
        self.assertEqual(code, 1)
        self.assert_finding(result, "STALE_SOURCE")
        self.assertEqual(result["subject_seal_sha256"], sealed["seal_sha256"])
        self.assertEqual(before, self.snapshot(self.attempt_path("attempt1")))
        self.assertEqual(read_json(self.attempt_path("verification1") / "seal.json")["stage_gate"], "FAIL")

    def test_changed_include_invalidates_the_composed_scope(self):
        self.seal()
        before = self.snapshot(self.attempt_path("attempt1"))
        source = self.source_path("INCLUDE")
        source.write_bytes(source.read_bytes() + b"\n/* SYNTHETIC changed include */\n")
        code, result, _ = self.invoke("verify-source")
        self.assertEqual(code, 1)
        self.assert_finding(result, "STALE_SOURCE")
        self.assertEqual(before, self.snapshot(self.attempt_path("attempt1")))

    def test_added_and_removed_scoped_files_block_verification_without_history_changes(self):
        self.seal()
        before = self.snapshot(self.attempt_path("attempt1"))
        added = self.source_path("SAS").parent / "unapproved_added.sas"
        added.write_bytes(b"/* SYNTHETIC unauthorized addition */")
        code, result, _ = self.invoke("verify-source", verification_attempt="added-check")
        self.assertEqual(code, 2)
        self.assert_finding(result, "SCOPE_ADDED_FILE")
        added.unlink()
        self.source_path("INCLUDE").unlink()
        code, result, _ = self.invoke("verify-source", verification_attempt="removed-check")
        self.assertEqual(code, 2)
        self.assert_finding(result, "SCOPE_MISSING_FILE")
        self.assertEqual(before, self.snapshot(self.attempt_path("attempt1")))

    def test_failed_validation_attempt_is_sealed_retained_and_not_reusable(self):
        _, graph = make_graph(self.scope, attempt="bad-record")
        graph["coverage"]["operation_count"] += 1
        self.record_path.write_bytes(canonical_bytes(graph))
        code, result, _ = self.invoke("seal-source", "bad-record")
        self.assertEqual(code, 1)
        self.assert_finding(result, "COVERAGE_MISMATCH")
        path = self.attempt_path("bad-record")
        self.assertFalse((path / "source_record.json").exists())
        self.assertTrue((path / "source_inventory.json").exists())
        self.assertEqual(read_json(path / "seal.json")["stage_gate"], "FAIL")
        before = self.snapshot(path)
        self.assertEqual(self.invoke("discover", "bad-record")[0], 2)
        self.assertEqual(before, self.snapshot(path))
        code, result, _ = self.invoke("verify-source", "bad-record")
        self.assertEqual(code, 2)
        self.assert_finding(result, "SUBJECT_NOT_PASSED")

    def test_explicit_contradiction_is_preserved_in_failed_record_attempt(self):
        inventory, graph = make_graph(self.scope, attempt="contradiction")
        graph["contradictions"].append({"issue_id": "contradiction1", "kind": "CONTRADICTION",
            "file_keys": [], "operation_ids": [graph["operations"][0]["operation_id"]],
            "status": "UNRESOLVED"})
        graph["coverage"] = coverage(graph, inventory)
        self.record_path.write_bytes(canonical_bytes(graph))
        code, result, _ = self.invoke("seal-source", "contradiction")
        self.assertEqual(code, 1)
        self.assert_finding(result, "DECLARED_CONTRADICTIONS")
        self.assertEqual(read_json(self.attempt_path("contradiction") / "source_record.json"), graph)
        self.assertEqual(read_json(self.attempt_path("contradiction") / "seal.json")["stage_gate"], "FAIL")

    def test_pre_authorization_rejections_do_not_create_artifact_store(self):
        original = deepcopy(self.scope)
        for mutation in [lambda scope: scope.update(synthetic=False),
                         lambda scope: scope["files"][0].update(path="../outside.sas")]:
            self.scope = deepcopy(original)
            mutation(self.scope)
            self.write_scope()
            code, _, _ = self.invoke("discover")
            self.assertEqual(code, 1)
            self.assertFalse(self.store.exists())
        self.scope = original
        self.write_scope()
        for options in [{"run": "different-run"}, {"attempt": "../escape"}]:
            code, _, _ = self.invoke("discover", **options)
            self.assertEqual(code, 1)
            self.assertFalse(self.store.exists())

    def test_store_overlap_and_symlink_roots_are_rejected_before_publication(self):
        source_root = Path(self.scope["roots"][0]["path"])
        before = self.snapshot(source_root)
        code, result, _ = self.invoke("discover", store=source_root / "artifacts")
        self.assertEqual(code, 1)
        self.assert_finding(result, "OUTPUT_SOURCE_OVERLAP")
        self.assertEqual(before, self.snapshot(source_root))
        alias = self.root / "source-alias"
        alias.symlink_to(source_root, target_is_directory=True)
        self.scope["roots"][0]["path"] = str(alias)
        self.write_scope()
        code, _, _ = self.invoke("discover")
        self.assertEqual(code, 1)
        self.assertFalse(self.store.exists())

    def test_nul_root_path_returns_redacted_json_without_traceback_or_artifacts(self):
        self.scope["roots"][0]["path"] += "/SYNTHETIC_PRIVATE_ROOT\x00"
        self.write_scope()
        code, result, output = self.invoke("discover")
        self.assertEqual(code, 1)
        self.assert_finding(result, "UNSAFE_PATH")
        self.assertNotIn("SYNTHETIC_PRIVATE_ROOT", output)
        self.assertNotIn("Traceback", output)
        self.assertFalse(self.store.exists())

    def test_record_run_module_and_attempt_mismatch_fail_with_retained_attempts(self):
        for field, value in [("run_id", "other-run"), ("module_ids", ["other-module"]),
                             ("attempt_id", "other-attempt")]:
            attempt = "mismatch-" + field
            _, graph = make_graph(self.scope, attempt=attempt)
            graph[field] = value
            self.record_path.write_bytes(canonical_bytes(graph))
            code, result, _ = self.invoke("seal-source", attempt)
            self.assertEqual(code, 1)
            self.assert_finding(result, "RECORD_OWNER_MISMATCH")
            self.assertEqual(read_json(self.attempt_path(attempt) / "seal.json")["stage_gate"], "FAIL")

    def test_missing_log_provenance_is_explicitly_unknown_and_blocked(self):
        self.assertTrue(any(item["kind"] in {"LOG", "LST"} for item in self.scope["files"]))
        self.scope["log_associations"] = []
        self.write_scope()
        code, result, _ = self.invoke("discover")
        self.assertEqual(code, 2)
        self.assert_finding(result, "UNRESOLVED_UNKNOWNS")
        inventory = read_json(self.attempt_path("attempt1") / "source_inventory.json")
        self.assertTrue(any(item["kind"] == "MISSING_LOG_PROVENANCE" for item in inventory["unknowns"]))
        self.assertEqual(inventory["log_associations"], [])
        self.assertEqual(read_json(self.attempt_path("attempt1") / "seal.json")["stage_gate"], "BLOCKED")

    def test_contradictory_log_run_identity_fails_without_invented_association(self):
        self.scope["log_associations"][0]["run_id"] = "another-run"
        self.write_scope()
        code, result, _ = self.invoke("discover")
        self.assertEqual(code, 1)
        self.assert_finding(result, "LOG_RUN_MISMATCH")
        path = self.attempt_path("attempt1")
        self.assertEqual(read_json(path / "seal.json")["stage_gate"], "FAIL")
        self.assertFalse((path / "source_inventory.json").exists())

    def test_false_human_approval_and_semantic_claims_fail_without_leaking_record(self):
        for index, mutation in enumerate([
            {"artifact_authority": "HUMAN_APPROVED"},
            {"semantic_verification": "VERIFIED"},
            {"human_approved": "SYNTHETIC_PRIVATE_APPROVAL_MARKER"},
        ]):
            attempt = f"false-approval-{index}"
            _, graph = make_graph(self.scope, attempt=attempt)
            graph.update(mutation)
            self.record_path.write_bytes(canonical_bytes(graph))
            code, result, output = self.invoke("seal-source", attempt)
            self.assertEqual(code, 1)
            self.assert_finding(result, "SCHEMA_INVALID")
            self.assertNotIn("SYNTHETIC_PRIVATE_APPROVAL_MARKER", output)
            path = self.attempt_path(attempt)
            self.assertFalse((path / "source_record.json").exists())
            for raw in self.snapshot(path).values():
                self.assertNotIn(b"SYNTHETIC_PRIVATE_APPROVAL_MARKER", raw)

    def test_source_contents_are_neither_executed_nor_published(self):
        marker = "SYNTHETIC_PRIVATE_SOURCE_MARKER_837263"
        execution_marker = self.root / "execution-marker"
        source = self.source_path("SAS")
        original = source.read_bytes()
        source.write_bytes(original + (
            f'\n/* {marker} */\nx "touch {execution_marker}";\n'
            f'__import__("pathlib").Path("{execution_marker}").touch()\n'
        ).encode())
        before = self.snapshot(source.parent)
        with patch("subprocess.run", side_effect=AssertionError("source execution")), \
             patch("subprocess.Popen", side_effect=AssertionError("source execution")), \
             patch("os.system", side_effect=AssertionError("source execution")):
            self.seal()
            code, _, output = self.invoke("verify-source")
        self.assertEqual(code, 0)
        self.assertFalse(execution_marker.exists())
        self.assertEqual(before, self.snapshot(source.parent))
        self.assertNotIn(marker, output)
        for raw in self.snapshot(self.store).values():
            self.assertNotIn(marker.encode(), raw)
            self.assertNotIn(original, raw)

    def test_missing_record_path_produces_redacted_sealed_failure(self):
        missing = self.root / "SYNTHETIC_PRIVATE_RECORD_NAME.json"
        code, result, output = self.invoke("seal-source", record=missing)
        self.assertIn(code, (1, 2))
        self.assertNotIn("SYNTHETIC_PRIVATE_RECORD_NAME", output)
        self.assertNotIn(str(self.root), output)
        self.assertEqual(read_json(self.attempt_path("attempt1") / "seal.json")["stage_gate"], result["stage_gate"])

    def test_interrupted_publication_has_no_success_seal_and_blocks_reuse(self):
        original = safeio._atomic_json

        def interrupt(fd, name, payload):
            if name == "seal.json":
                raise EvidenceError("PUBLICATION_IO_FAILURE", "BLOCKED")
            return original(fd, name, payload)

        with patch("sas_re._posix_io._atomic_json", side_effect=interrupt):
            code, result, _ = self.invoke("discover")
        self.assertEqual(code, 2)
        self.assert_finding(result, "PUBLICATION_IO_FAILURE")
        path = self.attempt_path("attempt1")
        self.assertTrue((path / "attempt.json").is_file())
        self.assertTrue((path / "source_inventory.json").is_file())
        self.assertFalse((path / "seal.json").exists())
        before = self.snapshot(path)
        self.assertEqual(self.invoke("discover")[0], 2)
        code, result, _ = self.invoke("verify-source")
        self.assertEqual(code, 2)
        self.assert_finding(result, "INCOMPLETE_ATTEMPT")
        self.assertIsNone(result["subject_seal_sha256"])
        self.assertEqual(before, self.snapshot(path))
        self.assertEqual(read_json(self.attempt_path("verification1") / "seal.json")["stage_gate"], "BLOCKED")

    def test_artifact_tampering_fails_verification_and_preserves_tampered_evidence(self):
        self.seal()
        path = self.attempt_path("attempt1") / "source_inventory.json"
        path.chmod(0o600)
        path.write_bytes(path.read_bytes().replace(b'"schema_version":"1.0"', b'"schema_version":"9.0"'))
        before = self.snapshot(self.attempt_path("attempt1"))
        code, result, _ = self.invoke("verify-source")
        self.assertEqual(code, 1)
        self.assert_finding(result, "ARTIFACT_HASH_MISMATCH")
        self.assertEqual(before, self.snapshot(self.attempt_path("attempt1")))

    def test_cli_requires_explicit_scope_run_attempt_and_new_verification_attempt(self):
        for argv in [["discover"], ["seal-source"], ["verify-source"],
                     ["discover", "--scope", str(self.scope_path), "--store", str(self.store),
                      "--run", self.scope["run_id"]],
                     ["verify-source", "--scope", str(self.scope_path), "--store", str(self.store),
                      "--run", self.scope["run_id"], "--attempt", "attempt1"]]:
            with self.subTest(argv=argv), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    main(argv)
                self.assertEqual(error.exception.code, 2)
                self.assertFalse(self.store.exists())


if __name__ == "__main__":
    unittest.main()
