"""Independent synthetic acceptance cases for P1, not SAS semantic evaluation."""

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fixture_support import make_graph, make_scope, refresh_coverage, reidentify, SYNTHETIC_SOURCES
from sas_re.contracts import validate_contract
from sas_re.evidence import (build_inventory, byte_lines, citation, digest, module_view,
                             revision_map, scope_identity, validate_record, validate_scope)
from sas_re.safeio import EvidenceError, secure_read


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.scope = make_scope(self.root)
        self.source = self.root / "sources"
        self.inventory, self.graph = make_graph(self.scope)

    def assert_error(self, code, function, *args, **kwargs):
        with self.assertRaises(EvidenceError) as error:
            function(*args, **kwargs)
        self.assertEqual(error.exception.code, code)
        return error.exception

    def check(self, graph=None, inventory=None):
        return validate_record(self.scope, inventory or self.inventory, graph or self.graph)

    def changed_record(self, change):
        graph = copy.deepcopy(self.graph)
        change(graph)
        reidentify(graph)
        return graph

    def test_complete_composed_graph_passes_structural_checks_without_semantic_claim(self):
        result = self.check()
        self.assertEqual(result["stage_gate"], "PASS")
        self.assertEqual(result["structural_verification"], "PASSED")
        self.assertEqual(result["semantic_verification"], "UNVERIFIABLE")
        self.assertEqual(result["benchmark_execution"], "NOT_RUN")
        self.assertEqual(result["artifact_authority"], "DRAFT")
        self.assertEqual(result["coverage"], {
            "file_count": 6, "operation_count": 2, "dataset_count": 2, "column_count": 2,
            "edge_count": 1, "log_observation_count": 1, "unknown_count": 0,
            "contradiction_count": 0, "covered_source_file_count": 2})

    def test_inventory_hashes_are_actual_original_source_bytes(self):
        self.assertEqual(len(self.inventory["files"]), 6)
        for item in self.inventory["files"]:
            original = SYNTHETIC_SOURCES[item["path"]]
            self.assertEqual(item["sha256"], hashlib.sha256(original).hexdigest())
            self.assertEqual(item["size_bytes"], len(original))
            self.assertEqual((self.source / item["path"]).read_bytes(), original)
            self.assertNotIn("excerpt", item)

    def test_citation_hash_includes_exact_original_line_endings(self):
        raw = SYNTHETIC_SOURCES["producer.sas"]
        c = self.graph["operations"][0]["citations"][0]
        self.assertEqual(c["source_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(c["excerpt_sha256"], hashlib.sha256(b"data work.stage;\n  value = 1;\nrun;\n").hexdigest())
        self.assertNotIn("text", c)

    def test_missing_scoped_file_blocks_inventory(self):
        (self.source / "settings.cfg").unlink()
        self.assertEqual(self.assert_error("SCOPE_MISSING_FILE", build_inventory,
                                           self.scope, "attempt2").gate, "BLOCKED")

    def test_unauthorized_added_file_is_never_content_read(self):
        sentinel = b"PRIVATE-SYNTHETIC-SENTINEL-DO-NOT-READ"
        (self.source / "unauthorized.txt").write_bytes(sentinel)
        with patch("sas_re.evidence.secure_read", side_effect=AssertionError("no file contents authorized yet")) as reader:
            self.assertEqual(self.assert_error("SCOPE_ADDED_FILE", build_inventory,
                                               self.scope, "attempt2").gate, "BLOCKED")
            reader.assert_not_called()

    def test_forged_inventory_citation_cannot_read_undeclared_file(self):
        target = self.source / "private-sentinel.txt"
        target.write_bytes(b"PRIVATE SYNTHETIC SENTINEL\n")
        inventory = copy.deepcopy(self.inventory)
        forged = copy.deepcopy(inventory["files"][0])
        forged.update(file_key="synthetic:private-sentinel.txt", path="private-sentinel.txt",
                      sha256=hashlib.sha256(target.read_bytes()).hexdigest())
        inventory["files"].append(forged)
        with patch("sas_re.evidence.secure_read", side_effect=AssertionError("must not read undeclared bytes")) as reader:
            self.assert_error("CITATION_FILE_INVALID", citation, self.scope, inventory,
                              "synthetic:private-sentinel.txt", 1, 1)
            reader.assert_not_called()

    def test_forged_inventory_citation_declaration_mismatch_never_reads(self):
        changes = [("path", "settings.cfg"), ("encoding", "latin-1"), ("kind", "CONFIG"),
                   ("module_id", "analyze"), ("root_id", "unlisted")]
        for field, value in changes:
            inventory = copy.deepcopy(self.inventory)
            item = next(f for f in inventory["files"] if f["path"] == "producer.sas")
            item[field] = value
            with self.subTest(field=field), patch("sas_re.evidence.secure_read", side_effect=AssertionError("read")) as reader:
                self.assert_error("CITATION_FILE_INVALID", citation, self.scope, inventory,
                                  "synthetic:producer.sas", 1, 1)
                reader.assert_not_called()

    def test_source_mutation_between_file_reads_rejected(self):
        changed = False

        def mutate_after_earlier_read(root, relative, *args, **kwargs):
            nonlocal changed
            raw = secure_read(root, relative, *args, **kwargs)
            if relative == "producer.sas" and not changed:
                changed = True
                (self.source / "consumer.sas").write_bytes(SYNTHETIC_SOURCES["consumer.sas"] + b"/* changed */\n")
            return raw

        with patch("sas_re.evidence.secure_read", side_effect=mutate_after_earlier_read):
            self.assert_error("SOURCE_CHANGED_DURING_READ", build_inventory, self.scope, "attempt2")

    def test_fabricated_inventory_hash_is_rejected_even_with_updated_manifest_digest(self):
        inventory = copy.deepcopy(self.inventory)
        inventory["files"][0]["sha256"] = "0" * 64
        graph = copy.deepcopy(self.graph)
        graph["scope_manifest_sha256"] = digest(inventory)
        self.assert_error("STALE_SOURCE", validate_record, self.scope, inventory, graph)

    def test_wrong_inventory_manifest_digest_is_rejected(self):
        self.graph["scope_manifest_sha256"] = "0" * 64
        self.assert_error("INVENTORY_HASH_MISMATCH", self.check)

    def test_changed_include_invalidates_old_evidence_without_modifying_it(self):
        before = json.dumps(self.graph, sort_keys=True)
        (self.source / "includes/constants.sas").write_bytes(b"/* SYNTHETIC CHANGED INCLUDE */\n%let synthetic_constant = 2;\n")
        self.assert_error("STALE_SOURCE", self.check)
        self.assertEqual(json.dumps(self.graph, sort_keys=True), before)

    def test_invalid_citation_span_rejected_after_identity_recalculation(self):
        for start, end in [(5, 3), (1, 999)]:
            graph = self.changed_record(lambda g: g["operations"][0]["citations"][0].update(
                line_start=start, line_end=end))
            with self.subTest(start=start, end=end):
                self.assert_error("CITATION_RANGE_INVALID", self.check, graph)
        for start, end in [(0, 1), (True, 1), (1, False)]:
            self.assert_error("CITATION_RANGE_INVALID", citation, self.scope, self.inventory,
                              "synthetic:producer.sas", start, end)

    def test_fabricated_citation_source_and_excerpt_hashes_rejected(self):
        for field in ("source_sha256", "excerpt_sha256"):
            graph = self.changed_record(lambda g: g["operations"][0]["citations"][0].update({field: "0" * 64}))
            with self.subTest(field=field):
                self.assert_error("CITATION_HASH_MISMATCH", self.check, graph)

    def test_duplicate_operation_ids_rejected(self):
        self.graph["operations"].append(copy.deepcopy(self.graph["operations"][0]))
        self.assert_error("DUPLICATE_OPERATIONS", self.check)

    def test_changed_supplied_operation_cannot_retain_old_identity(self):
        previous_id = self.graph["operations"][0]["operation_id"]
        self.graph["operations"][0]["stateful_constructs"] = ["RETAIN"]
        self.assert_error("UNSTABLE_OPERATIONS_ID", self.check)
        reidentify(self.graph)
        self.assertNotEqual(self.graph["operations"][0]["operation_id"], previous_id)
        self.assertEqual(self.check()["stage_gate"], "PASS")

    def test_dangling_column_dataset_rejected(self):
        graph = self.changed_record(lambda g: g["columns"][0].update(dataset_id="ds_" + "0" * 64))
        self.assert_error("DANGLING_COLUMN_DATASET", self.check, graph)

    def test_dangling_operation_node_rejected(self):
        graph = self.changed_record(lambda g: g["operations"][0]["writes"].append("ds_" + "0" * 64))
        self.assert_error("DANGLING_OPERATION_NODE", self.check, graph)

    def test_dangling_edge_operation_and_node_rejected(self):
        graph = self.changed_record(lambda g: g["edges"][0].update(to_operation_id="op_" + "0" * 64))
        self.assert_error("DANGLING_EDGE_OPERATION", self.check, graph)
        graph = self.changed_record(lambda g: g["edges"][0]["node_ids"].append("col_" + "0" * 64))
        self.assert_error("DANGLING_EDGE_NODE", self.check, graph)

    def test_producer_consumer_mismatch_rejected(self):
        graph = self.changed_record(lambda g: g["operations"][1].update(reads=[]))
        self.assert_error("PRODUCER_CONSUMER_MISMATCH", self.check, graph)

    def test_run_attempt_workspace_and_module_graph_ownership_checked(self):
        for field, value in [("workspace_id", "another"), ("run_id", "another"),
                             ("attempt_id", "another"), ("module_ids", ["prepare"])]:
            graph = copy.deepcopy(self.graph)
            graph[field] = value
            with self.subTest(field=field):
                self.assert_error("RECORD_OWNER_MISMATCH", self.check, graph)

    def test_unknown_module_and_column_ownership_rejected(self):
        graph = self.changed_record(lambda g: g["datasets"][0].update(module_id="undeclared"))
        self.assert_error("MODULE_OWNER_MISMATCH", self.check, graph)
        graph = self.changed_record(lambda g: g["columns"][0].update(module_id="analyze"))
        self.assert_error("COLUMN_OWNER_MISMATCH", self.check, graph)

    def test_operation_source_module_ownership_rejected(self):
        graph = self.changed_record(lambda g: g["operations"][0].update(module_id="analyze"))
        self.assert_error("OPERATION_SOURCE_OWNER_MISMATCH", self.check, graph)

    def test_matching_log_filename_does_not_invent_provenance(self):
        self.scope["log_associations"] = []
        inventory, graph = make_graph(self.scope)
        self.assertEqual({i["kind"] for i in inventory["unknowns"]}, {"MISSING_LOG_PROVENANCE"})
        self.assertEqual(len(inventory["unknowns"]), 2)
        graph["log_observations"] = []
        refresh_coverage(graph, inventory)
        report = validate_record(self.scope, inventory, graph)
        self.assertEqual(report["stage_gate"], "BLOCKED")
        self.assertEqual(report["semantic_verification"], "UNVERIFIABLE")

    def test_log_observation_missing_association_blocks(self):
        graph = self.changed_record(lambda g: g["log_observations"][0].update(association_id="invented"))
        self.assertEqual(self.assert_error("MISSING_LOG_PROVENANCE", self.check, graph).gate, "BLOCKED")

    def test_multiple_execution_associations_for_one_log_are_ambiguous(self):
        other = copy.deepcopy(self.scope["log_associations"][0])
        other.update(association_id="different-association", execution_id="different-execution")
        self.scope["log_associations"].append(other)
        error = self.assert_error("AMBIGUOUS_LOG_PROVENANCE", build_inventory, self.scope, "attempt2")
        self.assertEqual(error.gate, "BLOCKED")

    def test_contradictory_log_run_and_execution_rejected(self):
        scope = copy.deepcopy(self.scope)
        scope["log_associations"][0]["run_id"] = "another-run"
        self.assert_error("LOG_RUN_MISMATCH", build_inventory, scope, "attempt1")
        for field, value, code in [("run_id", "wrong", "LOG_OWNER_MISMATCH"),
                                   ("attempt_id", "wrong", "LOG_OWNER_MISMATCH"),
                                   ("execution_id", "wrong", "LOG_EXECUTION_MISMATCH")]:
            graph = self.changed_record(lambda g: g["log_observations"][0].update({field: value}))
            with self.subTest(field=field):
                self.assert_error(code, self.check, graph)

    def test_log_source_association_must_name_declared_source(self):
        self.scope["log_associations"][0]["source_file_keys"] = ["synthetic:missing.sas"]
        self.assert_error("LOG_SOURCE_MISSING", build_inventory, self.scope, "attempt1")

    def test_log_observation_cannot_reference_other_source_operation(self):
        graph = self.changed_record(lambda g: g["log_observations"][0].update(
            source_operation_ids=[g["operations"][1]["operation_id"]]))
        self.assert_error("LOG_SOURCE_MISMATCH", self.check, graph)

    def test_inconsistent_coverage_counts_rejected(self):
        for field in self.graph["coverage"]:
            graph = copy.deepcopy(self.graph)
            graph["coverage"][field] += 1
            with self.subTest(field=field):
                self.assert_error("COVERAGE_MISMATCH", self.check, graph)

    def test_dynamic_and_missing_dependencies_remain_explicit_unknowns(self):
        for target, expected in [(None, "DYNAMIC_DEPENDENCY"), ("synthetic:missing.sas", "MISSING_DEPENDENCY")]:
            scope = copy.deepcopy(self.scope)
            scope["dependencies"][0].update(to_file_key=target, status="UNRESOLVED")
            inventory, graph = make_graph(scope)
            self.assertEqual(inventory["unknowns"][0]["kind"], expected)
            report = validate_record(scope, inventory, graph)
            self.assertEqual(report["stage_gate"], "BLOCKED")
            graph["unknowns"] = []
            refresh_coverage(graph, inventory)
            self.assert_error("OMITTED_UNKNOWN", validate_record, scope, inventory, graph)

    def test_unknown_edge_requires_explicit_unknown_record(self):
        graph = self.changed_record(lambda g: g["edges"][0].update(type="UNKNOWN"))
        self.assert_error("UNKNOWN_EDGE_NOT_RECORDED", self.check, graph)
        graph["unknowns"] = [{"issue_id": "uncertain-edge", "kind": "OTHER", "file_keys": [],
                              "operation_ids": [o["operation_id"] for o in graph["operations"]],
                              "status": "UNRESOLVED"}]
        refresh_coverage(graph, self.inventory)
        self.assertEqual(self.check(graph)["stage_gate"], "BLOCKED")

    def test_explicit_contradictions_fail_even_when_structurally_consistent(self):
        self.graph["contradictions"] = [{"issue_id": "contradiction1", "kind": "CONTRADICTION",
                                        "file_keys": ["synthetic:producer.sas"], "operation_ids": [],
                                        "status": "UNRESOLVED"}]
        refresh_coverage(self.graph, self.inventory)
        report = self.check()
        self.assertEqual(report["stage_gate"], "FAIL")
        self.assertEqual(report["semantic_verification"], "UNVERIFIABLE")

    def test_contradiction_cannot_be_misplaced_as_unknown(self):
        self.graph["unknowns"] = [{"issue_id": "concealed-contradiction", "kind": "CONTRADICTION",
                                  "file_keys": [], "operation_ids": [], "status": "UNRESOLVED"}]
        refresh_coverage(self.graph, self.inventory)
        error = self.assert_error("MISPLACED_CONTRADICTION", self.check)
        self.assertEqual(error.gate, "FAIL")

    def test_dangling_unknown_reference_rejected(self):
        self.graph["unknowns"] = [{"issue_id": "unknown1", "kind": "OTHER",
                                  "file_keys": ["synthetic:missing.sas"], "operation_ids": [],
                                  "status": "UNRESOLVED"}]
        refresh_coverage(self.graph, self.inventory)
        self.assert_error("DANGLING_ISSUE_REFERENCE", self.check)

    def test_false_human_approval_or_semantic_verification_claims_rejected(self):
        for field, value in [("artifact_authority", "APPROVED"), ("semantic_verification", "VERIFIED"),
                             ("human_approved", True)]:
            graph = copy.deepcopy(self.graph)
            graph[field] = value
            with self.subTest(field=field):
                self.assert_error("SCHEMA_INVALID", self.check, graph)

    def test_valid_schema_is_insufficient_for_integrity_or_semantic_verification(self):
        graph = self.changed_record(lambda g: g["operations"][0]["citations"][0].update(excerpt_sha256="0" * 64))
        self.assertIsNone(validate_contract("Graph", graph))
        self.assert_error("CITATION_HASH_MISMATCH", self.check, graph)
        graph = self.changed_record(lambda g: g["log_observations"][0].update(value=999))
        report = self.check(graph)
        self.assertEqual(report["stage_gate"], "PASS")
        self.assertEqual(report["semantic_verification"], "UNVERIFIABLE")

    def test_scoped_paths_and_real_data_flag_are_rejected(self):
        for name in ["../escape.sas", "/absolute.sas", "includes/../producer.sas"]:
            scope = copy.deepcopy(self.scope)
            scope["files"][0].update(path=name, file_key="synthetic:" + name)
            self.assert_error("UNSAFE_PATH", validate_scope, scope)
        scope = copy.deepcopy(self.scope)
        scope["synthetic"] = False
        self.assert_error("SCHEMA_INVALID", validate_scope, scope)

    def test_operation_ids_are_stable_across_attempts_and_root_relocation(self):
        _, other = make_graph(self.scope, "attempt2")
        self.assertEqual([o["operation_id"] for o in self.graph["operations"]],
                         [o["operation_id"] for o in other["operations"]])
        scope = make_scope(self.root / "relocated")
        inventory, relocated = make_graph(scope)
        self.assertEqual(scope_identity(self.scope), scope_identity(scope))
        self.assertEqual(self.inventory["source_fingerprint"], inventory["source_fingerprint"])
        self.assertEqual(self.graph, relocated)

    def test_explicit_revision_mapping_on_include_change_does_not_claim_equivalence(self):
        (self.source / "includes/constants.sas").write_bytes(b"/* SYNTHETIC NEW REVISION */\n%let synthetic_constant = 2;\n")
        _, revised = make_graph(self.scope, "attempt2")
        mapping = revision_map(self.graph, revised)
        self.assertEqual(mapping["retained_operation_ids"], [])
        self.assertEqual(len(mapping["removed_operation_ids"]), 2)
        self.assertEqual(len(mapping["added_operation_ids"]), 2)
        self.assertEqual(mapping["semantic_equivalence"], "NOT_ASSERTED")

    def test_module_views_only_reference_canonical_ids_and_graph_digest(self):
        view = module_view(self.graph, "analyze")
        self.assertEqual(view["operation_ids"], [self.graph["operations"][1]["operation_id"]])
        self.assertEqual(view["source_record_sha256"], digest(self.graph))
        self.assertEqual(set(view["dataset_ids"]), {d["dataset_id"] for d in self.graph["datasets"]})
        self.assertEqual(view["edge_ids"], [self.graph["edges"][0]["edge_id"]])
        self.assertNotIn("operations", view)
        self.assert_error("UNKNOWN_MODULE", module_view, self.graph, "missing")

    def test_column_only_module_reference_includes_owning_dataset(self):
        graph = self.changed_record(lambda g: g["operations"][1].update(reads=[g["columns"][0]["column_id"]]))
        graph["edges"][0]["node_ids"] = [graph["columns"][0]["column_id"]]
        reidentify(graph)
        self.assertEqual(self.check(graph)["stage_gate"], "PASS")
        self.assertIn(graph["datasets"][0]["dataset_id"], module_view(graph, "analyze")["dataset_ids"])


class BytePolicyTests(unittest.TestCase):
    def test_only_cr_lf_crlf_are_line_separators_and_original_bytes_survive(self):
        self.assertEqual(byte_lines(b"a\r\nb\rc\nd\x85e\x0bf"), [b"a\r\n", b"b\r", b"c\n", b"d\x85e\x0bf"])
        self.assertEqual(byte_lines(b""), [])
        self.assertEqual(byte_lines(b"\n\n"), [b"\n", b"\n"])
        self.assertEqual(byte_lines(b"no newline"), [b"no newline"])

    def test_encoding_newline_bom_and_binary_metadata_use_original_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            scope = make_scope(root)
            source = root / "sources"
            entry = next(f for f in scope["files"] if f["path"] == "producer.sas")
            cases = [
                (b"\xef\xbb\xbf/* SYNTHETIC */\r\nrun;\r\n", "utf-8-sig", "CRLF", 2),
                (b"/* SYNTHETIC \xe9 */\rdata;\nrun;", "latin-1", "MIXED", 3),
                (b"/* SYNTHETIC */\rrun;", "ascii", "CR", 2),
                (b"/* SYNTHETIC */", "utf-8", "NONE", 1),
                (b"\xff\x00\r\n", "binary", "BINARY", 0),
            ]
            for raw, encoding, newline, count in cases:
                with self.subTest(encoding=encoding, newline=newline):
                    (source / "producer.sas").write_bytes(raw)
                    entry["encoding"] = encoding
                    inventory = build_inventory(scope, "attempt1")
                    record = next(f for f in inventory["files"] if f["path"] == "producer.sas")
                    self.assertEqual(record["sha256"], hashlib.sha256(raw).hexdigest())
                    self.assertEqual(record["newline"], newline)
                    self.assertEqual(record["line_count"], count)
                    if encoding == "binary":
                        with self.assertRaises(EvidenceError) as error:
                            citation(scope, inventory, "synthetic:producer.sas", 1, 1)
                        self.assertEqual(error.exception.code, "CITATION_FILE_INVALID")
                    else:
                        c = citation(scope, inventory, "synthetic:producer.sas", 1, count)
                        self.assertEqual(c["excerpt_sha256"], hashlib.sha256(raw).hexdigest())
            (source / "producer.sas").write_bytes(b"\xff")
            entry["encoding"] = "utf-8"
            with self.assertRaises(EvidenceError) as error:
                build_inventory(scope, "attempt2")
            self.assertEqual(error.exception.code, "ENCODING_MISMATCH")


if __name__ == "__main__":
    unittest.main()
