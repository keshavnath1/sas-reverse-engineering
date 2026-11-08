"""Reconstruction publication binds immutable attempts, original evidence, and conservative observations."""

import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from p2a_expectations import PUBLIC_CASES
from p2a_support import make_case, prepare_case
from sas_re.cli import main
from sas_re.contracts import load_schema, validate_contract, validate_versioned_contract
from sas_re.evidence import build_inventory, citation, coverage, digest, record_id
from sas_re.runs import execute as p1_execute
from sas_re.safeio import EvidenceError, canonical_bytes
from sas_re.semantic import module_view, reconstruct, revision_map, validate_v2
from sas_re.semantic_runs import execute


class P2ARunTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.scope, self.profile = prepare_case(self.root, PUBLIC_CASES["data_order_and_filter"])
        self.scope_path = self.root / "scope.json"
        self.scope_path.write_bytes(canonical_bytes(self.scope))
        self.store = self.root / "artifacts"
        self.profile_key = "synthetic:profile.json"
        self.source = Path(self.scope["roots"][0]["path"])
        self.workspace, self.run = self.scope["workspace_id"], self.scope["run_id"]

    def discover(self, attempt="inventory1"):
        return p1_execute("discover", self.scope_path, self.store, self.run, attempt)

    def reconstruct(self, attempt="reconstruct1", subject="inventory1", **kw):
        return execute(
            "reconstruct-source",
            self.scope_path,
            kw.get("store", self.store),
            self.run,
            attempt,
            kw.get("profile", self.profile_key),
            inventory_attempt=subject,
        )

    def check(self, subject="reconstruct1", output="check1"):
        return execute(
            "check-reconstruction",
            self.scope_path,
            self.store,
            self.run,
            subject,
            self.profile_key,
            verification_attempt=output,
        )

    def attempt_path(self, attempt):
        return self.store / self.workspace / self.run / attempt

    def read(self, attempt, artifact):
        return json.loads((self.attempt_path(attempt) / artifact).read_bytes())

    def test_complete_reconstruction_and_check_remain_blocked(self):
        self.assertEqual(self.discover()[1], 0)
        report, code = self.reconstruct()
        self.assertEqual(code, 2, report)
        self.assertEqual(report["reconstruction_status"], "COMPLETE", report)
        self.assertEqual(report["source_consistency"], "PASSED")
        checked, code = self.check()
        self.assertEqual(code, 2, checked)
        self.assertEqual(checked["source_consistency"], "PASSED", checked)
        for value in (report, checked):
            self.assertEqual(value["semantic_acceptance"], "BLOCKED")
            self.assertEqual(value["semantic_verification"], "UNVERIFIABLE")
            self.assertEqual(value["benchmark_execution"], "NOT_RUN")
            self.assertEqual(value["artifact_authority"], "DRAFT")
        self.assertEqual(
            checked["subject_seal_sha256"], digest(self.read("reconstruct1", "seal.json"))
        )

    def test_append_only_rejects_reuse_without_changing_prior_bytes(self):
        self.discover()
        self.reconstruct()
        before = {p.name: p.read_bytes() for p in self.attempt_path("reconstruct1").iterdir()}
        report, code = self.reconstruct()
        self.assertEqual((code, report["findings"][0]["code"]), (2, "ATTEMPT_EXISTS"))
        self.assertEqual(
            before, {p.name: p.read_bytes() for p in self.attempt_path("reconstruct1").iterdir()}
        )

    def test_stale_source_invalidates_reconstruction_and_checks(self):
        self.discover()
        self.reconstruct()
        source = self.source / "main.sas"
        source.write_bytes(source.read_bytes() + b"/* PUBLIC source revision */\n")
        for value in (self.check(), self.reconstruct("new", "inventory1")):
            self.assertEqual(value[1], 1, value)
            self.assertEqual(value[0]["findings"][0]["code"], "STALE_SOURCE")
        self.assertFalse((self.attempt_path("new") / "source_record.json").exists())

    def test_profile_revision_invalidates_source_fingerprint(self):
        self.discover()
        self.reconstruct()
        profile = self.source / "profile.json"
        profile.write_bytes(profile.read_bytes() + b"\n")
        result, code = self.check()
        self.assertEqual((code, result["findings"][0]["code"]), (1, "STALE_SOURCE"))

    def test_private_scope_rejected_before_store(self):
        self.scope["synthetic"] = False
        self.scope_path.write_bytes(canonical_bytes(self.scope))
        report, code = self.reconstruct()
        self.assertEqual((code, report["findings"][0]["code"]), (1, "SCHEMA_INVALID"))
        self.assertFalse(self.store.exists())

    def test_unapproved_profile_key_never_reads_external_file(self):
        self.discover()
        sentinel = self.root / "outside.json"
        sentinel.write_text("protected synthetic sentinel")
        report, code = self.reconstruct(profile=str(sentinel))
        self.assertEqual((code, report["findings"][0]["code"]), (1, "PROFILE_NOT_AUTHORIZED"))
        self.assertNotIn("sentinel", json.dumps(report))

    def test_output_cannot_overlap_source(self):
        self.discover()
        report, code = self.reconstruct(store=self.source / "output")
        self.assertEqual((code, report["findings"][0]["code"]), (1, "OUTPUT_SOURCE_OVERLAP"))
        self.assertFalse((self.source / "output").exists())

    def test_source_links_are_not_followed(self):
        self.discover()
        original = self.source / "main.sas"
        external = self.root / "outside.txt"
        external.write_bytes(original.read_bytes())
        original.unlink()
        original.symlink_to(external)
        report, code = self.reconstruct()
        self.assertEqual(code, 1, report)
        self.assertEqual(report["findings"][0]["code"], "UNSAFE_FILE_TYPE")

    def test_added_source_is_blocked_without_contents_read(self):
        self.discover()
        (self.source / "unapproved.sas").write_text("SYNTHETIC SENTINEL SECRET")
        report, code = self.reconstruct()
        self.assertEqual((code, report["findings"][0]["code"]), (2, "SCOPE_ADDED_FILE"))
        self.assertNotIn("SECRET", json.dumps(report))

    def test_unsealed_subject_cannot_be_used(self):
        self.discover()
        (self.attempt_path("inventory1") / "seal.json").unlink()
        report, code = self.reconstruct()
        self.assertEqual((code, report["findings"][0]["code"]), (2, "INCOMPLETE_ATTEMPT"))

    def test_sound_blocked_inventory_carries_unknowns(self):
        self.scope["dependencies"].append(
            {
                "dependency_id": "dynamic",
                "from_file_key": "synthetic:main.sas",
                "to_file_key": None,
                "kind": "INCLUDE",
                "status": "UNRESOLVED",
            }
        )
        self.scope_path.write_bytes(canonical_bytes(self.scope))
        self.assertEqual(self.discover()[1], 2)
        report, code = self.reconstruct()
        self.assertEqual(code, 2, report)
        self.assertEqual(report["reconstruction_status"], "PARTIAL")
        self.assertTrue(self.read("reconstruct1", "source_record.json")["unknowns"])

    def test_tampered_published_graph_is_rejected(self):
        self.discover()
        self.reconstruct()
        path = self.attempt_path("reconstruct1") / "source_record.json"
        path.chmod(0o600)
        path.write_bytes(path.read_bytes() + b"\n")
        result, code = self.check()
        self.assertEqual((code, result["findings"][0]["code"]), (1, "ARTIFACT_HASH_MISMATCH"))

    def test_no_subprocess_or_network_in_reconstruction(self):
        self.discover()
        before = {p.name: p.read_bytes() for p in self.source.iterdir()}
        with (
            patch("subprocess.run", side_effect=AssertionError("subprocess")),
            patch("subprocess.Popen", side_effect=AssertionError("subprocess")),
            patch("socket.socket", side_effect=AssertionError("network")),
        ):
            result, code = self.reconstruct()
        self.assertEqual(code, 2, result)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.source.iterdir()})

    def test_version_dispatch_and_v1_refuse_v2_graph(self):
        self.discover()
        self.reconstruct()
        graph = self.read("reconstruct1", "source_record.json")
        validate_versioned_contract("Graph", graph)
        with self.assertRaises(EvidenceError):
            validate_contract("Graph", graph)
        altered = copy.deepcopy(graph)
        altered["schema_version"] = "99.0"
        with self.assertRaises(EvidenceError):
            validate_versioned_contract("Graph", altered)
        path = self.root / "provided.json"
        path.write_bytes(canonical_bytes(graph))
        result, code = p1_execute(
            "seal-source", self.scope_path, self.store, self.run, "old-command", path
        )
        self.assertEqual((code, result["findings"][0]["code"]), (1, "SCHEMA_INVALID"))

    def test_v1_to_v2_lineage_preserves_history(self):
        inventory = build_inventory(self.scope, "old-record")
        op = {
            "module_id": "main",
            "kind": "DATA_STEP",
            "citations": [citation(self.scope, inventory, "synthetic:main.sas", 2, 8)],
            "reads": [],
            "writes": [],
            "stateful_constructs": [],
            "classification": "INFERENCE",
            "semantic_verification": "UNVERIFIABLE",
        }
        op["operation_id"] = record_id("op", inventory["source_fingerprint"], op, "operation_id")
        old = {
            "schema_version": "1.0",
            **{
                k: inventory[k]
                for k in (
                    "workspace_id",
                    "run_id",
                    "attempt_id",
                    "module_ids",
                    "source_fingerprint",
                )
            },
            "scope_manifest_sha256": digest(inventory),
            "artifact_authority": "DRAFT",
            "semantic_verification": "UNVERIFIABLE",
            "operations": [op],
            "datasets": [],
            "columns": [],
            "edges": [],
            "log_observations": [],
            "unknowns": [],
            "contradictions": [],
        }
        old["coverage"] = coverage(old, inventory)
        path = self.root / "old.json"
        path.write_bytes(canonical_bytes(old))
        self.assertEqual(
            p1_execute("seal-source", self.scope_path, self.store, self.run, "old-record", path)[1],
            0,
        )
        before = {p.name: p.read_bytes() for p in self.attempt_path("old-record").iterdir()}
        report, code = self.reconstruct(subject="old-record")
        self.assertEqual(code, 2, report)
        self.assertIsNotNone(report["lineage"])
        self.assertEqual(report["lineage"]["semantic_equivalence"], "NOT_ASSERTED")
        self.assertEqual(report["lineage"]["retained_operation_ids"], [])
        self.assertTrue(report["lineage"]["operation_mappings"][0]["current_operation_ids"])
        self.assertEqual(self.check()[0]["source_consistency"], "PASSED")
        self.assertEqual(
            before, {p.name: p.read_bytes() for p in self.attempt_path("old-record").iterdir()}
        )

    def test_derived_module_view_has_ids_and_graph_hash_only(self):
        self.discover()
        self.reconstruct()
        graph = self.read("reconstruct1", "source_record.json")
        view = module_view(graph, "main")
        self.assertEqual(view["source_record_sha256"], digest(graph))
        self.assertEqual(
            view["operation_ids"], sorted(o["operation_id"] for o in graph["operations"])
        )
        self.assertNotIn("facts", view)
        self.assertNotIn("operations", view)

    def test_cli_outputs_blocked_acceptance_and_supports_explicit_subject(self):
        self.discover()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(
                [
                    "reconstruct-source",
                    "--scope",
                    str(self.scope_path),
                    "--store",
                    str(self.store),
                    "--run",
                    self.run,
                    "--attempt",
                    "cli",
                    "--inventory-attempt",
                    "inventory1",
                    "--profile-file",
                    self.profile_key,
                ]
            )
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(output.getvalue())["semantic_acceptance"], "BLOCKED")

    def test_cross_module_graph_and_view_retain_foreign_producer(self):
        case = copy.deepcopy(PUBLIC_CASES["sort_and_producer_consumer"])
        source = case["files"]["main.sas"]
        split = source.index(b"data work.final;")
        case["files"] = {"main.sas": source[:split], "consumer.sas": source[split:]}

        def profile_edit(profile):
            profile["entrypoints"].append("synthetic:consumer.sas")

        def scope_edit(scope):
            scope["module_ids"].append("consumer")
            file = next(f for f in scope["files"] if f["path"] == "consumer.sas")
            file.update(kind="SAS", module_id="consumer")

        scope, inventory, profile, graph = make_case(
            self.root / "modules", case, profile_edit=profile_edit, scope_edit=scope_edit
        )
        report = validate_v2(scope, inventory, graph, profile, profile_file_key=self.profile_key)
        self.assertEqual(report["reconstruction_status"], "COMPLETE")
        operations = {op["operation_id"]: op for op in graph["operations"]}
        data = next(e for e in graph["edges"] if e["type"] == "DATA")
        self.assertEqual(operations[data["from_operation_id"]]["module_id"], "main")
        self.assertEqual(operations[data["to_operation_id"]]["module_id"], "consumer")
        view = module_view(graph, "consumer")
        producer = next(d for d in graph["datasets"] if d["name"] == "work.sorted")
        self.assertIn(producer["dataset_id"], view["dataset_ids"])


class P2AObservationReviewTests(unittest.TestCase):
    """Negative obligations independently identified by parser-agent review."""

    def test_wrong_step_header_is_a_source_log_contradiction(self):
        case = copy.deepcopy(PUBLIC_CASES["fixed_log_observations"])
        case["files"]["run.log"] += b"NOTE: PROCEDURE SQL used (Total process time):\n"
        case["declared_bindings"][0]["end_line"] = 6
        with tempfile.TemporaryDirectory() as tmp:
            scope, inventory, profile, graph = make_case(Path(tmp), case)
            self.assertIn(
                "LOG_STEP_HEADER_CONTRADICTION", {x["code"] for x in graph["contradictions"]}
            )
            self.assertEqual(
                validate_v2(
                    scope, inventory, graph, profile, profile_file_key="synthetic:profile.json"
                )["stage_gate"],
                "FAIL",
            )

    def test_duplicate_step_headers_block_ambiguous_segment(self):
        case = copy.deepcopy(PUBLIC_CASES["fixed_log_observations"])
        case["files"]["run.log"] += b"NOTE: DATA statement used (Total process time):\n" * 2
        case["declared_bindings"][0]["end_line"] = 7
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, graph = make_case(Path(tmp), case)
            self.assertIn("AMBIGUOUS_LOG_STEP_HEADERS", {x["code"] for x in graph["unknowns"]})

    def test_duplicate_lst_column_names_rejected_before_ambiguous_locators(self):
        case = copy.deepcopy(PUBLIC_CASES["fixed_lst_cells"])
        case["declared_bindings"][0]["columns"][1]["name"] = "x"
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(EvidenceError) as caught:
            make_case(Path(tmp), case)
        self.assertEqual(caught.exception.code, "LST_COLUMN_NAME_AMBIGUOUS")

    def test_oversized_count_lexeme_is_bounded_without_integer_conversion(self):
        case = copy.deepcopy(PUBLIC_CASES["fixed_log_observations"])
        case["files"]["run.log"] = case["files"]["run.log"].replace(
            b"2 variables", b"9" * 5000 + b" variables"
        )
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, graph = make_case(Path(tmp), case)
            self.assertIn("OBSERVATION_NUMERIC_LIMIT", {x["code"] for x in graph["unknowns"]})


if __name__ == "__main__":
    unittest.main()
