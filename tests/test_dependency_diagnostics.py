"""P3-A1 public diagnostic obligations A01–A26, in roadmap order.

All graph-math answers and bound-input digests come from the independently
frozen vectors. New malformed/challenge inputs are built with that oracle.
These checks exercise development behavior on supplied graphs only.
"""

import builtins
from contextlib import ExitStack, contextmanager, redirect_stdout
from copy import deepcopy
from importlib import import_module
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import dependency_vectors as v
from sas_re import _dependency_diagnostics as diagnostic
from sas_re.cli import main
from sas_re.contracts import validate_contract


NO_PATH = "no represented dependency path; independence unproved."
EDGE_FIELDS = ("edge_id", "type", "from_operation_id", "to_operation_id",
               "node_ids", "evidence_operation_ids")


def ids(g):
    return [op["operation_id"] for op in g["operations"]]


def named_pairs(g, labels):
    by_label = dict(zip("ABCD", ids(g)))
    return [(by_label[a], by_label[b]) for a, b in labels]


def direction(row):
    return row["from_operation_id"], row["to_operation_id"]


def original_ids(g, labels):
    by_direction = {direction(row): row["edge_id"] for row in g["edges"]}
    return [by_direction[pair] for pair in named_pairs(g, labels)]


def replace_id(record, prefix, id_field):
    record[id_field] = v.oracle_id(prefix, record, id_field)


def issue_rows(analysis):
    return [row for row in analysis["blockers"] if "issue_id" in row and row["issue_id"] is not None]


def assert_no_claims(case, value):
    if isinstance(value, dict):
        forbidden = {"schedule", "execution_waves", "safe_concurrency", "opportunities",
                     "runtime_recommendation", "speedup", "human_approval"}
        case.assertFalse(forbidden.intersection(value), "A diagnostic exposed a planner claim")
        for child in value.values():
            assert_no_claims(case, child)
    elif isinstance(value, list):
        for child in value:
            assert_no_claims(case, child)
    elif isinstance(value, str):
        case.assertNotIn(value.upper(), {"PASS", "VERIFIED", "APPROVED", "INDEPENDENT", "ELIGIBLE"})


@contextmanager
def offline_calls():
    # Permit read-only reads of the two trusted package schemas, even with an
    # empty schema cache. Resolve package roots before installing the traps.
    contracts = import_module("sas_re.contracts")
    package = Path(contracts.__file__).parent
    schemas = {str(package / "contracts" / version / "evidence.schema.json")
               for version in ("v1", "v2")}

    def schema_reads(original):
        def checked(file, mode="r", *args, **kwargs):
            if isinstance(file, int) or os.fsdecode(file) not in schemas or mode not in {"r", "rt", "rb"}:
                raise AssertionError("Diagnostic attempted a non-schema open")
            return original(file, mode, *args, **kwargs)
        return checked

    forbidden = {
        "sas_re.semantic": ("reconstruct", "validate_v2", "build_inventory", "validate_scope", "secure_read"),
        "sas_re.evidence": ("build_inventory", "validate_scope", "validate_record", "secure_read", "citation"),
        "sas_re.observations": ("extract_observations",),
        "sas_re.semantic_runs": ("execute", "load_profile"),
        "sas_re.runs": ("execute", "_publish"),
        "sas_re.safeio": ("require_safe_root", "ensure_disjoint", "secure_read", "enumerate_files", "read_json"),
        "sas_re.platform_io": ("require_evidence_io", "get_backend"),
    }
    modules = {name: import_module(name) for name in forbidden}
    safeio = modules["sas_re.safeio"]
    targets = [(modules[name], field) for name, fields in forbidden.items() for field in fields]
    targets.extend((safeio.AttemptStore, field) for field in ("__init__", "begin", "read_attempt"))
    targets.extend([(safeio.Attempt, "publish"), (subprocess, "Popen"), (subprocess, "run"),
                    (socket, "socket"), (socket, "create_connection"), (socket, "getaddrinfo")])
    targets.extend((os, name) for name in
                   ("open", "mkdir", "listdir", "scandir", "link", "unlink", "remove", "rename",
                    "replace", "write", "system", "popen", "fork", "posix_spawn", "execve", "spawnv")
                   if hasattr(os, name))

    # Catch direct imports captured before patching the source module as well.
    originals = {id(getattr(owner, field)) for owner, field in targets}
    targets.extend((diagnostic, name) for name, obj in vars(diagnostic).items() if id(obj) in originals)
    original_import = builtins.__import__

    def offline_import(name, *args, **kwargs):
        if name.split(".")[0] in {"openai", "anthropic", "google", "boto3", "huggingface_hub",
                                  "saspy", "git", "gitlab", "requests", "httpx"}:
            raise AssertionError("Diagnostic attempted a provider, SAS, Git or network client import")
        return original_import(name, *args, **kwargs)

    with ExitStack() as stack:
        for owner, field in targets:
            stack.enter_context(patch.object(owner, field, side_effect=AssertionError("Offline trap: " + field)))
        stack.enter_context(patch.object(builtins, "__import__", side_effect=offline_import))
        stack.enter_context(patch.object(builtins, "open", side_effect=schema_reads(builtins.open)))
        stack.enter_context(patch.object(io, "open", side_effect=schema_reads(io.open)))
        yield


class DependencyDiagnosticTests(unittest.TestCase):
    def diagnostic(self, g, expected_hash=None):
        digest = expected_hash if expected_hash is not None else v.oracle_hash(g)
        result = diagnostic.diagnose(g, digest)
        self.assertEqual(result["parent_graph_sha256"], digest)
        self.assertTrue(result["algorithm"])
        self.assertEqual({key: result[key] for key in v.AUTHORITY}, v.AUTHORITY)
        self.assertEqual({key: result["subject"][key] for key in ("workspace_id", "run_id",
                         "attempt_id", "source_fingerprint")},
                         {key: g[key] for key in ("workspace_id", "run_id", "attempt_id", "source_fingerprint")})
        self.assertEqual(result["analysis"]["eligibility"], "REJECTED" if g["contradictions"] else "BLOCKED")
        assert_no_claims(self, result)
        return result

    def frozen(self, name):
        g = v.fixture_catalog()[name]
        digest = v.FROZEN_GRAPH_SHA256[name]
        self.assertEqual(v.oracle_hash(g), digest, "The independent fixture changed")
        return g, self.diagnostic(g, digest)

    def expect_refusal(self, g, expected_code=None):
        with self.assertRaises(diagnostic.DiagnosticError) as failure:
            diagnostic.diagnose(g, v.oracle_hash(g))
        if expected_code:
            self.assertEqual(failure.exception.code, expected_code)

    def check_reach(self, g, analysis, labels):
        self.assertCountEqual([direction(row) for row in analysis["reachability"]], named_pairs(g, labels))

    def check_edges(self, g, actual):
        # Node and evidence lists are set-like. Compare their members, not an
        # incidental traversal order. Every original typed edge must survive.
        self.assertCountEqual([row["edge_id"] for row in actual], [row["edge_id"] for row in g["edges"]])
        original = {row["edge_id"]: row for row in g["edges"]}
        for row in actual:
            expected = original[row["edge_id"]]
            for field in EDGE_FIELDS[:4]:
                self.assertEqual(row[field], expected[field])
            for field in EDGE_FIELDS[4:]:
                self.assertCountEqual(row[field], expected[field])

    def check_issue(self, row, collection, issue):
        self.assertEqual(row["issue_id"], issue["issue_id"])
        self.assertEqual(row["source_collection"], collection)
        self.assertEqual(row["code"], "DECLARED_" + issue["kind"])
        self.assertEqual(row["category"], "UNKNOWN" if collection == "unknowns" else "CONTRADICTION")
        self.assertEqual(row["scope"], "LOCAL" if issue["operation_ids"] else "GLOBAL")
        self.assertCountEqual(row["operation_ids"], issue["operation_ids"])
        self.assertCountEqual(row["file_keys"], issue["file_keys"])
        self.assertTrue(row["missing_proof"].strip())
        self.assertNotEqual(row["missing_proof"], issue["missing_proof"])

    def check_conflict(self, name, expectation):
        g, result = self.frozen(name)
        analysis = result["analysis"]
        pairs = named_pairs(g, [expectation["pair"]])
        self.assertEqual([(r["earlier_operation_id"], r["later_operation_id"]) for r in analysis["conflicts"]], pairs)
        finding, = analysis["conflicts"]
        self.assertEqual(finding["kind"], expectation["conflict"])
        self.assertEqual(finding["uncertainty"], "UNVERSIONED_DATASET")
        self.assertTrue(finding["missing_proof"])
        self.assertEqual(finding["dataset_ids"], [g["datasets"][0]["dataset_id"]])
        uses = {node for op in g["operations"] for node in op["reads"] + op["writes"]}
        self.assertEqual(set(finding["node_ids"]), uses)
        self.assertEqual(analysis["dependencies"], [])
        self.assertEqual(analysis["reachability"], [])
        self.assertEqual(g["edges"], [])

    def test_single_operation(self):
        g, r = self.frozen("single")
        a = r["analysis"]
        self.assertEqual([row["operation_id"] for row in a["operation_constraints"]], ids(g))
        self.assertEqual(a["dependencies"], [])
        self.assertEqual(a["reachability"], v.EXPECTED["single"]["reachable"])
        self.assertEqual(a["no_path_pairs"], v.EXPECTED["single"]["no_path"])
        component, = a["components"]
        self.assertEqual(component["operation_ids"], ids(g))
        self.assertFalse(component["cyclic"])
        self.assertEqual(component["edge_ids"], [])

    def test_data_chain_witness(self):
        g, r = self.frozen("chain")
        a = r["analysis"]
        self.check_edges(g, a["dependencies"])
        self.check_reach(g, a, v.EXPECTED["chain"]["reachable"])
        first, middle, last = ids(g)
        expected = original_ids(g, v.EXPECTED["chain"]["paths"][("A", "C")])
        self.assertEqual(diagnostic.witness(r, first, last), expected)
        row, = [row for row in a["reachability"] if direction(row) == (first, last)]
        self.assertEqual((row["predecessor_operation_id"], row["edge_id"]), (middle, expected[-1]))

    def test_diamond(self):
        g, r = self.frozen("diamond")
        a = r["analysis"]
        self.check_edges(g, a["dependencies"])
        self.check_reach(g, a, v.EXPECTED["diamond"]["reachable"])
        first, second, _, last = ids(g)
        expected = original_ids(g, v.EXPECTED["diamond"]["paths"][("A", "D")])
        self.assertEqual(diagnostic.witness(r, first, last), expected)
        row, = [row for row in a["reachability"] if direction(row) == (first, last)]
        self.assertEqual((row["predecessor_operation_id"], row["edge_id"]), (second, expected[-1]))
        self.assertFalse(any(comp["cyclic"] for comp in a["components"]))

    def test_disconnected_branches(self):
        g, r = self.frozen("disconnected")
        a = r["analysis"]
        self.check_reach(g, a, v.EXPECTED["disconnected"]["reachable"])
        # All missing directed pairs, including reverse directions within branches.
        missing = v.EXPECTED["disconnected"]["no_path"] + [
            ("A", "D"), ("D", "A"), ("B", "C"), ("C", "B"), ("B", "A"), ("D", "C")]
        self.assertCountEqual([direction(row) for row in a["no_path_pairs"]], named_pairs(g, missing))
        for row in a["no_path_pairs"]:
            self.assertEqual(row["reason"], NO_PATH)
            self.assertEqual(diagnostic.witness(r, *direction(row)), [])

    def test_missing_raw_edge(self):
        self.check_conflict("raw", v.EXPECTED["raw"])

    def test_waw_conflict(self):
        self.check_conflict("waw", v.EXPECTED["waw"])

    def test_war_conflict(self):
        self.check_conflict("war", v.EXPECTED["war"])

    def test_dataset_column_alias(self):
        for variant in v.EXPECTED["aliases"]["variants"]:
            with self.subTest(variant=variant):
                self.check_conflict("alias_" + variant, v.EXPECTED["aliases"])

    def test_state_self_cycle(self):
        for kind in v.EXPECTED["state"]["effects"]:
            with self.subTest(state=kind):
                g, r = self.frozen(kind.lower())
                a = r["analysis"]
                self.check_reach(g, a, v.EXPECTED["state"]["reachable"])
                self.check_edges(g, a["dependencies"])
                comp, = a["components"]
                self.assertTrue(comp["cyclic"])
                self.assertEqual(comp["operation_ids"], ids(g))
                edge_id = g["edges"][0]["edge_id"]
                self.assertEqual(comp["edge_ids"], [edge_id])
                op = g["operations"][0]
                self.assertEqual(diagnostic.witness(r, op["operation_id"], op["operation_id"]), [edge_id])
                row, = a["operation_constraints"]
                self.assertEqual(row["state_effects"], op["state_effects"])

    def test_multi_operation_cycle(self):
        g, r = self.frozen("cycle")
        a = r["analysis"]
        self.check_reach(g, a, v.EXPECTED["cycle"]["reachable"])
        comp, = a["components"]
        self.assertTrue(comp["cyclic"])
        self.assertCountEqual(comp["operation_ids"], ids(g))
        self.assertCountEqual(comp["edge_ids"], [row["edge_id"] for row in g["edges"]])
        first, second = ids(g)
        both = original_ids(g, [("A", "B"), ("B", "A")])
        self.assertEqual(diagnostic.witness(r, first, first), both)
        self.assertEqual(diagnostic.witness(r, second, second), list(reversed(both)))

    def test_cross_module_macro_control(self):
        g, r = self.frozen("macro_control")
        a = r["analysis"]
        self.check_reach(g, a, v.EXPECTED["macro_control"]["reachable"])
        self.check_edges(g, a["dependencies"])
        self.assertEqual(a["dependencies"][0]["type"], v.EXPECTED["macro_control"]["edge_type"])
        source = g["operations"][1]
        row, = [row for row in a["operation_constraints"] if row["operation_id"] == source["operation_id"]]
        self.assertEqual(row["module_id"], v.EXPECTED["macro_control"]["operation_owner"])
        self.assertEqual(row["lineage"], source["lineage"])
        self.assertEqual(row["control_lineage"], source["control_lineage"])
        control, = row["control_lineage"]
        self.assertEqual((control["fact_index"], control["input_fact_indices"]), (2, [1]))
        self.assertEqual(a["node_owners"][control["input_column_ids"][0]], "prepare")

    def test_order_preconditions(self):
        for condition in v.EXPECTED["order"]["preconditions"]:
            with self.subTest(precondition=condition):
                g, r = self.frozen("order_" + condition.lower())
                a = r["analysis"]
                self.check_edges(g, a["dependencies"])
                self.assertEqual(a["dependencies"][0]["type"], "ORDER")
                by_id = {row["operation_id"]: row for row in a["operation_constraints"]}
                for op in g["operations"]:
                    for field in ("cardinality", "numeric_policy", "order_contract"):
                        self.assertEqual(by_id[op["operation_id"]][field], op[field])
                second = g["operations"][1]["operation_id"]
                obligations = {row["code"] for row in a["blockers"] if second in row["operation_ids"]}
                self.assertIn("ORDER_PRECONDITION", obligations)
                self.assertIn("TIE_ORDER_UNSPECIFIED", obligations)

    def test_resource_not_precedence(self):
        g, r = self.frozen("resource")
        a = r["analysis"]
        self.check_edges(g, a["resource_annotations"])
        self.assertEqual(a["dependencies"], v.EXPECTED["resource"]["causal_edges"])
        self.check_reach(g, a, v.EXPECTED["resource"]["reachable"])
        self.assertCountEqual([direction(row) for row in a["no_path_pairs"]], named_pairs(g, [("A", "B"), ("B", "A")]))
        self.assertTrue(all(row["reason"] == NO_PATH for row in a["no_path_pairs"]))

    def test_side_effect_and_unknown_edges(self):
        g, r = self.frozen("side_unknown")
        a = r["analysis"]
        self.check_reach(g, a, v.EXPECTED["side_unknown"]["reachable"])
        self.check_edges(g, a["dependencies"])
        self.assertCountEqual([row["type"] for row in a["dependencies"]], v.EXPECTED["side_unknown"]["types"])
        codes = {row["code"] for row in a["blockers"] if row["missing_proof"]}
        self.assertTrue({"SIDE_EFFECT_EDGE", "UNKNOWN_EDGE"}.issubset(codes))

    def test_unknown_scope(self):
        for scope in v.EXPECTED["unknown"]["variants"]:
            with self.subTest(scope=scope):
                g, r = self.frozen(scope.lower() + "_unknown")
                finding, = issue_rows(r["analysis"])
                self.assertEqual(finding["category"], "UNKNOWN")
                self.assertEqual(finding["scope"], scope)
                self.assertEqual(finding["operation_ids"], [] if scope == "GLOBAL" else ids(g))
                self.check_issue(finding, "unknowns", g["unknowns"][0])

    def test_contradiction_precedence(self):
        g, r = self.frozen("contradiction")
        findings = issue_rows(r["analysis"])
        self.assertCountEqual([row["category"] for row in findings], ["CONTRADICTION", "UNKNOWN"])
        by_id = {row["issue_id"]: row for row in findings}
        for collection in ("unknowns", "contradictions"):
            for issue in g[collection]:
                self.check_issue(by_id[issue["issue_id"]], collection, issue)
        self.assertEqual(r["analysis"]["eligibility"], "REJECTED")

        # Caller-authored text is addressable in the exact parent graph. It
        # cannot declare a verdict or supply planner advice in a finding.
        advice = "Run these operations concurrently on Spark."
        op = v.operation()
        kinds = ("MISSING_DEPENDENCY", "DYNAMIC_DEPENDENCY", "MISSING_LOG_PROVENANCE",
                 "OTHER", "CONTRADICTION")
        issues = []
        for i, kind in enumerate(kinds):
            issue = v.issue("issue-" + str(i), [op["operation_id"]] if i % 2 == 0 else [])
            issue.update(kind=kind, code="VERIFIED", missing_proof=advice,
                         file_keys=["synthetic:review.sas"])
            issues.append(issue)
        g = v.graph([op], unknowns=issues[:-1], contradictions=issues[-1:])
        before = v.oracle_bytes(g)
        result = self.diagnostic(g)
        self.assertEqual(v.oracle_bytes(g), before)
        self.assertNotIn(advice, json.dumps(result))
        self.assertNotIn('"VERIFIED"', json.dumps(result))
        self.assertEqual(result["analysis"]["eligibility"], "REJECTED")
        findings = issue_rows(result["analysis"])
        self.assertCountEqual([row["issue_id"] for row in findings], [issue["issue_id"] for issue in issues])
        by_id = {row["issue_id"]: row for row in findings}
        for issue in issues:
            with self.subTest(injected_issue=issue["kind"]):
                collection = "contradictions" if issue["kind"] == "CONTRADICTION" else "unknowns"
                self.check_issue(by_id[issue["issue_id"]], collection, issue)
        self.assertEqual(len({row["missing_proof"] for row in findings}), len(kinds))

        edited = deepcopy(g)
        for issue in edited["unknowns"] + edited["contradictions"]:
            issue.update(code="APPROVED", missing_proof="Choose Dask and start both steps.")
        second = self.diagnostic(edited)
        self.assertNotEqual(result["parent_graph_sha256"], second["parent_graph_sha256"])
        self.assertEqual(issue_rows(second["analysis"]), findings)
        self.assertNotIn("Choose Dask and start both steps.", json.dumps(second))
        self.assertNotIn('"APPROVED"', json.dumps(second))

    def test_identity_integrity(self):
        parent = v.dataset()
        op = v.operation()
        # Fixtures with independently valid references. Each forged payload is
        # altered without updating its old ID or any original reference to it.
        base = v.graph([op, v.operation(1)], [parent], [v.column(parent)],
                       edges=[v.edge(op, v.operation(1), "STATE")], log_observations=[v.observation(op)])
        self.diagnostic(base)
        alterations = {
            "operations": ("cardinality", "SORT_PRESERVES_ROWS"),
            "datasets": ("name", "work.changed"),
            "columns": ("name", "changed"),
            "edges": ("type", "SIDE_EFFECT"),
            "log_observations": ("value_lexeme", "10.00"),
        }
        for collection, (field, other) in alterations.items():
            for change in ("duplicate", "forged"):
                with self.subTest(collection=collection, change=change):
                    g = deepcopy(base)
                    if change == "duplicate":
                        g[collection].append(deepcopy(g[collection][0]))
                        v.refresh_coverage(g)
                    else:
                        g[collection][0][field] = other
                    self.expect_refusal(g, "DUPLICATE_RECORD_ID" if change == "duplicate" else "RECORD_ID_MISMATCH")

        opaque = v.issue("inventory-id-authored-before-v2-enrichment")
        opaque.update(operation_ids=[op["operation_id"]], spans=[v.span()], file_keys=["synthetic:main.sas"],
                      missing_proof="Enriched obligation, original inventory unavailable")
        enriched = v.graph([op], unknowns=[opaque])
        before = v.oracle_bytes(enriched)
        accepted = self.diagnostic(enriched)
        finding, = issue_rows(accepted["analysis"])
        self.check_issue(finding, "unknowns", opaque)
        self.assertEqual(v.oracle_bytes(enriched), before)

    def test_reference_integrity(self):
        template = v.macro_control()
        absent_op, absent_col, absent_ds = "op_" + "e" * 64, "col_" + "e" * 64, "ds_" + "e" * 64
        # Rehash the changed operation, and isolate it from its old incident
        # edges. Only its deliberately invalid local reference is under test.
        variants = (
            ("read", "reads", None, [absent_col]),
            ("write", "writes", None, [absent_ds]),
            ("data-fact", "lineage", "fact_index", 3),
            ("control-fact", "control_lineage", "fact_index", 3),
            ("data-column", "lineage", "input_column_ids", [absent_col]),
            ("output-column", "lineage", "output_column_id", absent_col),
            ("control-column", "control_lineage", "input_column_ids", [absent_col]),
            ("data-self", "lineage", "input_fact_indices", [1]),
            ("data-future", "lineage", "input_fact_indices", [2]),
            ("control-self", "control_lineage", "input_fact_indices", [2]),
            ("control-out-of-range", "control_lineage", "input_fact_indices", [3]),
        )
        for name, field, nested, bad in variants:
            with self.subTest(reference=name):
                g = deepcopy(template)
                g["edges"].clear()
                op = g["operations"][1]
                if nested is None:
                    op[field] = bad
                else:
                    op[field][0][nested] = bad
                replace_id(op, "op", "operation_id")
                self.expect_refusal(v.refresh_coverage(g))

        for field, value in (("from_operation_id", absent_op), ("to_operation_id", absent_op),
                             ("evidence_operation_ids", [absent_op]), ("node_ids", [absent_ds])):
            with self.subTest(edge_reference=field):
                g = deepcopy(template)
                edge = g["edges"][0]
                edge[field] = value
                replace_id(edge, "edge", "edge_id")
                self.expect_refusal(g)

        op = v.operation()
        ds = v.dataset()
        col = v.column(ds)
        col["dataset_id"] = absent_ds
        replace_id(col, "col", "column_id")
        effect = v.state_cycle()["operations"][0]
        effect["state_effects"][0]["fact_index"] = 1
        replace_id(effect, "op", "operation_id")
        obs = v.observation(op)
        obs["source_operation_ids"] = [absent_op]
        replace_id(obs, "log", "observation_id")
        statement = v.graph([op])
        statement["statement_coverage"] = [{"operation_id": absent_op, "classification": "FACT", "span": v.span()}]
        invalid = {
            "parent-dataset": v.graph([op], [ds], [col]),
            "module": v.graph([v.operation(module="absent")]),
            "state-fact": v.graph([effect], [ds]),
            "observation-owner-reference": v.graph([op], log_observations=[obs]),
            "unknown-operation": v.graph([op], unknowns=[v.issue(operations=[absent_op])]),
            "statement-operation": statement,
        }
        for name, g in invalid.items():
            with self.subTest(reference=name):
                self.expect_refusal(g)

    def test_version_sequence_ownership(self):
        wrong_version = v.graph([v.operation()])
        wrong_version["schema_version"] = "1.0"
        ds = v.dataset(module="main")
        wrong_col = v.column(ds)
        wrong_col["module_id"] = "prepare"
        replace_id(wrong_col, "col", "column_id")
        source = v.operation()
        wrong_obs = v.observation(source)
        wrong_obs["run_id"] = "another-run"
        replace_id(wrong_obs, "log", "observation_id")
        negative_sequence = deepcopy(source)
        negative_sequence["sequence"] = -1
        replace_id(negative_sequence, "op", "operation_id")
        cases = {
            "version": wrong_version,
            "sequence-gap": v.graph([source, v.operation(2)]),
            "sequence-negative": v.graph([negative_sequence]),
            "duplicate-sequence": v.graph([source, v.operation(0, kind="PROC_SORT")]),
            "column-dataset-owner": v.graph([source], [ds], [wrong_col], modules=["main", "prepare"]),
            "observation-run-owner": v.graph([source], log_observations=[wrong_obs]),
        }
        for name, g in cases.items():
            with self.subTest(invalidity=name):
                self.expect_refusal(g)

        # A log's module is the owner of its declared log file. The associated
        # source operation can belong to another module.
        obs = v.observation(source)
        obs["module_id"] = "prepare"
        replace_id(obs, "log", "observation_id")
        self.diagnostic(v.graph([source], log_observations=[obs], modules=["main", "prepare"]))

    def test_rehashed_false_graph_not_verified(self):
        # Suppose A and B actually have disjoint effects. A fabricated dataset
        # and internally coherent write/read/edge declarations bind together,
        # and an alternative graph omitting this edge also passes v2 shape.
        shared = v.dataset()
        node = shared["dataset_id"]
        first, last = v.operation(writes=[node]), v.operation(1, reads=[node])
        for claim in ("invented_edge", "omitted_edge"):
            with self.subTest(claim=claim):
                edges = [v.edge(first, last, nodes=[node])] if claim == "invented_edge" else []
                g = v.graph([first, last], [shared], edges=edges)
                validate_contract("Graph", g, version="2.0")
                a = self.diagnostic(g)["analysis"]
                if edges:
                    self.check_reach(g, a, [("A", "B")])
                else:
                    self.assertEqual(a["reachability"], [])
                    self.assertEqual([row["reason"] for row in a["no_path_pairs"]], [NO_PATH] * 2)

    def test_no_input_mutation(self):
        good = v.macro_control()
        malformed = deepcopy(good)
        malformed["edges"][0]["type"] = "RESOURCE"  # Deliberately stale edge ID.
        oversized = v.graph([v.operation(i) for i in range(v.LIMITS["operations"] + 1)])
        for scenario, g in (("success", good), ("invalid", malformed), ("over-bound", oversized)):
            with self.subTest(outcome=scenario):
                before, before_bytes = deepcopy(g), v.oracle_bytes(g)
                if scenario == "success":
                    result = self.diagnostic(g)
                    op = next(row for row in result["analysis"]["operation_constraints"] if row["sequence"] == 1)
                    op["lineage"][0]["input_column_ids"].clear()
                    op["control_lineage"][0]["input_fact_indices"].append(999)
                    op["order_contract"]["keys"].append("changed")
                    result["analysis"]["dependencies"][0]["evidence_operation_ids"].clear()
                else:
                    self.expect_refusal(g)
                self.assertEqual(v.oracle_bytes(g), before_bytes)
                self.assertEqual(g, before)

    def test_determinism_and_order(self):
        g, original = self.frozen("diamond")
        self.assertEqual(self.diagnostic(deepcopy(g)), original)
        # Reverse graph collection order only. Do not reorder the inputs inside
        # an identity-bound operation, edge or node, or normalize before hashing.
        for name, fixture, fields in (("diamond", g, ["datasets", "edges", "operations"]),
                                      ("macro", v.macro_control(), ["module_ids", "datasets", "columns"])):
            with self.subTest(collection_permutation=name):
                shuffled = deepcopy(fixture)
                for field in fields:
                    shuffled[field].reverse()
                before, after = self.diagnostic(fixture), self.diagnostic(shuffled)
                self.assertNotEqual(before["parent_graph_sha256"], after["parent_graph_sha256"])
                self.assertEqual(before["analysis"], after["analysis"])

        g = v.graph([v.operation(), v.operation(1)])
        g["statement_coverage"] = [{"operation_id": op["operation_id"], "classification": "HEADER",
                                    "span": op["span"]} for op in g["operations"]]
        before = self.diagnostic(g)
        g["statement_coverage"].reverse()
        after = self.diagnostic(g)
        self.assertNotEqual(before["parent_graph_sha256"], after["parent_graph_sha256"])
        self.assertEqual(after["analysis"]["statement_coverage"], g["statement_coverage"])
        self.assertNotEqual(before["analysis"]["statement_coverage"], after["analysis"]["statement_coverage"])

        facts = [v.state_cycle()["operations"][0]["facts"][0], v.order_graph()["operations"][1]["facts"][0]]
        ordered, reversed_facts = v.operation(facts=facts), v.operation(facts=list(reversed(facts)))
        before, after = self.diagnostic(v.graph([ordered])), self.diagnostic(v.graph([reversed_facts]))
        self.assertNotEqual(before["analysis"], after["analysis"])
        self.assertEqual(before["analysis"]["operation_constraints"][0]["fact_kinds"], ["retain", "by"])
        self.assertEqual(after["analysis"]["operation_constraints"][0]["fact_kinds"], ["by", "retain"])

    def test_subject_binding(self):
        base = v.topology("single")
        old = self.diagnostic(base)
        old_digest = old["parent_graph_sha256"]
        op_changed = v.graph([v.operation(kind="PROC_SORT")])
        edge_changed = deepcopy(base)
        edge_changed["edges"].append(v.edge(base["operations"][0], base["operations"][0], "STATE"))
        v.refresh_coverage(edge_changed)
        for name, g in (("operation", op_changed), ("edge", edge_changed),
                        ("workspace", {**base, "workspace_id": "other-workspace"}),
                        ("run", {**base, "run_id": "other-run"}),
                        ("attempt", {**base, "attempt_id": "other-attempt"})):
            with self.subTest(change=name):
                with self.assertRaises(diagnostic.DiagnosticError):
                    diagnostic.diagnose(g, old_digest)
                rebound = self.diagnostic(g)
                self.assertNotEqual(rebound["parent_graph_sha256"], old_digest)
                self.assertEqual(old["parent_graph_sha256"], old_digest)

    def test_finite_bounds(self):
        def count_graph(name, size):
            g = v.graph()
            # Guard isolation avoids conflating collection limits with schema,
            # uniqueness, identity, or the independent JSON complexity budget.
            if name == "facts":
                g["operations"] = [{"facts": [None] * (size // 2)},
                                   {"facts": [None] * (size - size // 2)}]
            elif name == "nodes":
                g["datasets"], g["columns"] = [None] * (size // 2), [None] * (size - size // 2)
            else:
                key = "module_ids" if name == "modules" else name
                g[key] = [None] * size
            return g

        def json_input(name, size):
            if name == "depth":
                value = None
                for _ in range(size):
                    value = [value]
                return value
            if name == "json_values":
                # Root dict + one object key + child list + scalar occurrences.
                return {"k": [None] * (size - 3)}
            # Finite UTF-8 bytes include enclosing quotes and the canonical LF.
            return "x" * (size - 3)

        for name, limit in v.LIMITS.items():
            collection = name in {"operations", "modules", "edges", "nodes", "facts"}
            check = diagnostic._check_counts if collection else diagnostic._bounded_copy
            for offset in (-1, 0, 1):
                with self.subTest(limit=name, offset=offset):
                    value = count_graph(name, limit + offset) if collection else json_input(name, limit + offset)
                    if offset == 1:
                        with self.assertRaises(diagnostic.DiagnosticError) as failure:
                            check(value)
                        self.assertEqual(failure.exception.code, "LIMIT_" + name.upper())
                    else:
                        check(value)

        # An unescaped character count would undercount multibyte UTF-8 or JSON
        # string escapes. Separately exceed aggregate size with a shared object.
        byte_limit = v.LIMITS["canonical_bytes"]
        shared = ["𐐷" * (byte_limit // 8)]
        for name, value in (("multibyte", "𐐷" * (byte_limit // 4)),
                            ("escaped", "\x01" * (byte_limit // 6 + 1)),
                            ("repeated_reference", [shared, shared])):
            with self.subTest(encoding=name):
                with self.assertRaises(diagnostic.DiagnosticError) as failure:
                    diagnostic._bounded_copy(value)
                self.assertEqual(failure.exception.code, "LIMIT_CANONICAL_BYTES")

        class HostileDict(dict):
            def items(self):
                raise AssertionError("A dict subclass method ran")

        class HostileKey(str):
            def encode(self, *args, **kwargs):
                raise AssertionError("A string subclass method ran")

            def __len__(self):
                raise AssertionError("A string subclass method ran")

        cyclic = []
        cyclic.append({"again": cyclic})
        invalid = {"cycle": cyclic, "tuple": (1,), "set": {1}, "bytes": b"x",
                   "non-string-key": {0: True}, "hostile-key": {HostileKey("k"): 1},
                   "hostile-dict": HostileDict(k=1), "object": object(), "nan": float("nan"),
                   "positive-infinity": float("inf"), "negative-infinity": -float("inf"),
                   "unpaired-surrogate": "\udabc", "huge-integer": 1 << 100_000}
        for name, value in invalid.items():
            with self.subTest(non_json=name):
                with self.assertRaises(diagnostic.DiagnosticError):
                    diagnostic._bounded_copy(value)
                with self.assertRaises(diagnostic.DiagnosticError):
                    diagnostic.diagnose({"malformed": value}, "0" * 64)

        # Two choices in each of 24 layers gives 2**24 distinct start-to-end
        # paths. Exact reachable pairs = 2*L**2 + 2*L + 1 for this topology.
        layers = 24
        stage_indices = [[0]] + [[1 + 2*i, 2 + 2*i] for i in range(layers)] + [[2*layers + 1]]
        links = [(a, b) for left, right in zip(stage_indices, stage_indices[1:]) for a in left for b in right]
        datasets = [v.dataset(f"work.link{a}_{b}") for a, b in links]
        nodes = {pair: ds["dataset_id"] for pair, ds in zip(links, datasets)}
        ops = [v.operation(i, reads=[nodes[a, b] for a, b in links if b == i],
                           writes=[nodes[a, b] for a, b in links if a == i]) for i in range(2*layers + 2)]
        edges = [v.edge(ops[a], ops[b], nodes=[nodes[a, b]]) for a, b in links]
        g = v.graph(ops, datasets, edges=edges)
        result = self.diagnostic(g)
        rows = result["analysis"]["reachability"]
        self.assertEqual(len(rows), 2 * layers**2 + 2 * layers + 1)
        self.assertEqual(len({direction(row) for row in rows}), len(rows))
        self.assertLessEqual(len(rows), len(ops)**2)
        for row in rows:
            self.assertEqual(set(row), {"from_operation_id", "to_operation_id", "predecessor_operation_id", "edge_id"})
        first_route = [stage[0] for stage in stage_indices]
        expected_ids = [v.edge(ops[a], ops[b], nodes=[nodes[a, b]])["edge_id"]
                        for a, b in zip(first_route, first_route[1:])]
        self.assertEqual(diagnostic.witness(result, ops[0]["operation_id"], ops[-1]["operation_id"]), expected_ids)

    def test_pure_offline_operation(self):
        g = v.macro_control()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.txt"
            source.write_bytes(b"public synthetic offline sentinel")
            g["profile_file_key"] = "synthetic:" + str(source)
            digest = v.oracle_hash(g)
            with offline_calls():
                r = diagnostic.diagnose(g, digest)
            self.assertEqual(r["parent_graph_sha256"], digest)
            self.assertEqual(list(root.iterdir()), [source])
            self.assertEqual(source.read_bytes(), b"public synthetic offline sentinel")

    def test_authority_and_gate_preservation(self):
        for name in v.FROZEN_GRAPH_SHA256:
            with self.subTest(fixture=name):
                self.frozen(name)

        # Reuse the baseline capability-denial harness (trusted schema reads
        # allowed; caller path opens/mutations, subprocesses and sockets trapped).
        # Import the module, not its TestCase into this suite's discovery scope.
        from test_platform_io import BlockedIOTests
        gates = BlockedIOTests()
        gates.setUp()
        self.addCleanup(gates.doCleanups)
        commands = ("analyze-parallelism", "discover", "seal-source", "verify-source",
                    "reconstruct-source", "check-reconstruction")
        for command in commands:
            with self.subTest(command=command), gates.denied_environment():
                argv = [command, "--scope", str(gates.scope), "--store", str(gates.store),
                        "--run", "run1", "--attempt", "attempt1"]
                if command == "seal-source":
                    argv += ["--record", str(gates.record)]
                if command in {"verify-source", "check-reconstruction"}:
                    argv += ["--verification-attempt", "verify1"]
                if command in {"reconstruct-source", "check-reconstruction"}:
                    argv += ["--profile-file", "profile1"]
                if command == "reconstruct-source":
                    argv += ["--inventory-attempt", "inventory1"]
                out = io.StringIO()
                with redirect_stdout(out):
                    code = main(argv)
                report = json.loads(out.getvalue())
                if command == "analyze-parallelism":
                    self.assertEqual(code, 3)
                    self.assertEqual(report["status"], "NOT_IMPLEMENTED")
                    self.assertEqual(report["stage_gate"], "BLOCKED")
                    self.assertFalse(report["inputs_read"])
                    self.assertEqual(report["benchmark_execution"], "NOT_RUN")
                else:
                    gates.assert_blocked_report(report, code, p2a=command in commands[-2:])


if __name__ == "__main__":
    unittest.main()
