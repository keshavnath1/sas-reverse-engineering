"""Public review regressions for the graph composer, not independent acceptance.

Expected constraints were reviewed by the coordinating architecture review before
these cases were added: compile-time projection, guarded state ranges, sorted-key
invalidation, unknown references and conditional column lineage. These fixtures
are public development material and do not contain protected evaluator answers.
"""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from sas_re.contracts import load_schema, validate_contract
from sas_re.evidence import build_inventory, record_id
from sas_re.safeio import EvidenceError
from sas_re.semantic import reconstruct, validate_v2


class GraphReviewTests(unittest.TestCase):
    def prepare(self, text, *, extra=None, rows=None, sorted_by=None, columns=None, missing_policy="SAS_ORDINARY_MISSING_EQUALS_MISSING"):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name).resolve()
        sources = {"main.sas": text, **(extra or {})}
        profile = {"schema_version": "2.0", "profile_id": "sas94-synthetic-v1",
            "numeric_missing_join_policy": missing_policy,
            "entrypoints": ["synthetic:main.sas"], "inputs": [{"name": "work.a", "module_id": "main",
                "columns": [{"name": name, "type": "NUMERIC", "length": 8} for name in (columns or ["x"])],
                "rows": rows if rows is not None else [["1"], ["2"]], "sorted_by": sorted_by or []}],
            "log_bindings": [], "lst_bindings": []}
        for name, source in sources.items():
            (root / name).write_text(source)
        (root / "profile.json").write_text(json.dumps(profile))
        scope = {"schema_version": "1.0", "workspace_id": "synthetic", "run_id": "run", "module_ids": ["main"],
            "synthetic": True, "roots": [{"root_id": "synthetic", "path": str(root)}],
            "files": [{"file_key": "synthetic:" + name, "root_id": "synthetic", "path": name,
                       "kind": "SAS" if name == "main.sas" else "CONFIG" if name == "profile.json" else "INCLUDE",
                       "module_id": "main", "encoding": "utf-8"} for name in [*sources, "profile.json"]],
            "dependencies": [{"dependency_id": "include" + str(i), "from_file_key": "synthetic:main.sas",
                "to_file_key": "synthetic:" + name, "kind": "INCLUDE", "status": "DECLARED"} for i, name in enumerate(extra or {})],
            "log_associations": []}
        inventory = build_inventory(scope, "attempt")
        graph = reconstruct(scope, inventory, profile, profile_file_key="synthetic:profile.json")
        return scope, inventory, profile, graph

    def codes(self, graph):
        return {issue["code"] for issue in graph["unknowns"]}

    def test_keep_before_assignment_is_compile_time_projection(self):
        *_, graph = self.prepare("data work.b; set work.a; keep y; y=x+1; run;")
        out = next(d["dataset_id"] for d in graph["datasets"] if d["name"] == "work.b")
        self.assertEqual([c["name"] for c in graph["columns"] if c["dataset_id"] == out], ["y"])
        self.assertNotIn("KEEP_COLUMN_UNRESOLVED", self.codes(graph))

    def test_drop_before_assignment_removes_final_column(self):
        *_, graph = self.prepare("data work.b; set work.a; drop y; y=x+1; run;")
        out = next(d["dataset_id"] for d in graph["datasets"] if d["name"] == "work.b")
        self.assertEqual([c["name"] for c in graph["columns"] if c["dataset_id"] == out], ["x"])
        self.assertNotIn("DROP_COLUMN_UNRESOLVED", self.codes(graph))

    def test_changed_sort_key_cannot_prove_downstream_by_order(self):
        *_, graph = self.prepare("data work.b; set work.a; x=-x; run; data work.c; set work.b; by x; y=1; run;", sorted_by=["x"])
        self.assertIn("BY_SORT_PRECONDITION_UNRESOLVED", self.codes(graph))
        self.assertEqual(graph["operations"][-1]["order_contract"]["precondition"], "UNRESOLVED")

    def test_nonlinear_retained_recurrence_does_not_claim_exactness(self):
        *_, graph = self.prepare("data work.b; set work.a; retain n 1048576; n=n*1048576; run;")
        self.assertIn("NUMERIC_EXACTNESS_UNRESOLVED", self.codes(graph))
        self.assertEqual(graph["operations"][0]["numeric_policy"]["exactness"], "UNRESOLVED")

    def test_mutually_retained_recurrence_is_conservative(self):
        *_, graph = self.prepare("data work.b; set work.a; retain n 1; retain m 1; n=m; m=n*1048576; run;")
        self.assertIn("NUMERIC_EXACTNESS_UNRESOLVED", self.codes(graph))

    def test_sum_of_retained_state_has_explicit_recurrence_blocker(self):
        *_, graph = self.prepare("data work.b;set work.a;retain n 1;n+n+1;run;", rows=[["2"]] * 60)
        self.assertIn("SUM_STATE_RECURRENCE_UNRESOLVED", self.codes(graph))
        self.assertEqual(graph["operations"][0]["numeric_policy"]["exactness"], "UNRESOLVED")

    def test_input_read_before_set_records_prior_iteration_state(self):
        *_, graph = self.prepare("data work.b;y=x+1;set work.a;run;")
        self.assertIn("INPUT_READ_ORDER_UNRESOLVED", self.codes(graph))
        op = graph["operations"][0]
        self.assertTrue(any(s["kind"] == "INPUT_PDV" for s in op["state_effects"]))
        self.assertTrue(any(l["input_phase"] == "PRIOR_ITERATION_OR_INITIAL_MISSING" for l in op["lineage"]))
        self.assertTrue(any(e["type"] == "STATE" for e in graph["edges"]))

    def test_set_overrides_retain_initialization_for_input_column(self):
        *_, graph = self.prepare("data work.b;retain x 0;set work.a;y=x*1048576*1048576+1;run;", rows=[["1048576"]])
        self.assertIn("NUMERIC_EXACTNESS_UNRESOLVED", self.codes(graph))

    def test_failed_numeric_bound_cannot_leak_old_range_to_consumer(self):
        *_, graph = self.prepare("data work.b;set work.a;x=x*1048576*1048576*1048576+1;run;data work.c;set work.b;y=x+1;run;")
        self.assertEqual(graph["operations"][-1]["numeric_policy"]["exactness"], "UNRESOLVED")
        self.assertIn("PRODUCER_EVIDENCE_UNRESOLVED", self.codes(graph))

    def test_unsupported_producer_taints_following_numeric_and_order_proof(self):
        *_, graph = self.prepare("data work.b;set work.a;x=sqrt(x);run;data work.c;set work.b;by x;y=x+1;run;", sorted_by=["x"])
        op = graph["operations"][-1]
        self.assertEqual(op["numeric_policy"]["exactness"], "UNRESOLVED")
        self.assertEqual(op["order_contract"]["precondition"], "UNRESOLVED")

    def test_late_by_precondition_blocker_taints_consumer_bounds(self):
        *_, graph = self.prepare("data work.b;set work.a;by x;y=x+1;run;data work.c;set work.b;z=y+1;run;")
        self.assertIn("BY_SORT_PRECONDITION_UNRESOLVED", self.codes(graph))
        self.assertIn("PRODUCER_EVIDENCE_UNRESOLVED", self.codes(graph))
        self.assertEqual(graph["operations"][-1]["numeric_policy"]["exactness"], "UNRESOLVED")

    def test_derived_missing_join_keys_require_explicit_policy(self):
        *_, graph = self.prepare("data work.b;set work.a;x=.;run;data work.c;set work.a;x=.;run;proc sql;create table work.d as select b.x as x from work.b as b inner join work.c as c on b.x=c.x;quit;", missing_policy="UNRESOLVED")
        self.assertIn("MISSING_JOIN_KEY_POLICY_UNRESOLVED", self.codes(graph))

    def test_guarded_reset_does_not_erase_large_prior_bound(self):
        *_, graph = self.prepare("data work.b; set work.a; retain n 1048576; if x=0 then n=0; y=n*1048576*1048576; run;")
        self.assertIn("NUMERIC_EXACTNESS_UNRESOLVED", self.codes(graph))

    def test_if_unknown_column_remains_unresolved(self):
        *_, graph = self.prepare("data work.b; set work.a; if missing_column=1 then y=2; run;")
        self.assertIn("COLUMN_REFERENCE_UNRESOLVED", self.codes(graph))

    def test_sql_where_unknown_column_remains_unresolved(self):
        *_, graph = self.prepare("proc sql; create table work.b as select a.x as y from work.a as a where a.absent=1; quit;")
        self.assertIn("COLUMN_REFERENCE_UNRESOLVED", self.codes(graph))

    def test_guard_dependencies_include_input_condition_column(self):
        *_, graph = self.prepare("data work.b; set work.a; if x=1 then y=2; run;")
        input_ds = next(d["dataset_id"] for d in graph["datasets"] if d["name"] == "work.a")
        input_col = next(c["column_id"] for c in graph["columns"] if c["dataset_id"] == input_ds)
        guards = [v for v in graph["operations"][0]["control_lineage"] if v["role"] == "ASSIGNMENT_GUARD"]
        self.assertEqual(len(guards), 1)
        self.assertEqual(guards[0]["input_column_ids"], [input_col])

    def test_subsetting_filter_has_control_lineage(self):
        *_, graph = self.prepare("data work.b; set work.a; if x>0; run;")
        selections = [v for v in graph["operations"][0]["control_lineage"] if v["role"] == "ROW_SELECTION"]
        self.assertEqual(len(selections), 1)
        self.assertTrue(selections[0]["input_column_ids"])

    def test_assignment_chain_refs_prior_fact_not_invented_input_column(self):
        *_, graph = self.prepare("data work.b; set work.a; y=x+1; z=y*2; run;")
        op = graph["operations"][0]
        y_index = next(i for i, f in enumerate(op["facts"]) if f["kind"] == "assignment" and f["target"] == "y")
        z_index = next(i for i, f in enumerate(op["facts"]) if f["kind"] == "assignment" and f["target"] == "z")
        line = next(l for l in op["lineage"] if l["fact_index"] == z_index)
        self.assertEqual(line["input_fact_indices"], [y_index])
        self.assertEqual(line["input_column_ids"], [])

    def test_literal_include_fragment_has_original_citations(self):
        *_, graph = self.prepare("data work.b; set work.a; %include 'fragment.sas'; run;", extra={"fragment.sas": "y=x+1;"})
        op = next(o for o in graph["operations"] if o["kind"] == "DATA_STEP")
        assignment = next(f for f in op["facts"] if f["kind"] == "assignment")
        self.assertEqual(assignment["span"]["file_key"], "synthetic:fragment.sas")
        self.assertIn("synthetic:fragment.sas", {c["file_key"] for c in op["citations"]})
        self.assertFalse(graph["unknowns"])

    def test_missing_include_is_cited_unknown_without_scope_expansion(self):
        *_, graph = self.prepare("%include 'absent.sas'; data work.b; set work.a; run;")
        self.assertIn("UNRESOLVED_INCLUDE", self.codes(graph))
        issue = next(i for i in graph["unknowns"] if i["code"] == "UNRESOLVED_INCLUDE")
        self.assertTrue(issue["citations"])

    def test_valid_citations_and_rehashed_false_order_fail_reconstruction_check(self):
        scope, inventory, profile, graph = self.prepare("data work.b; set work.a; y=x+1; run;")
        altered = deepcopy(graph)
        op = altered["operations"][0]
        op["order_contract"]["kind"] = "ASCENDING_KEYS"
        op["order_contract"]["keys"] = ["x"]
        from p2a_support import all_citations, reidentify
        before = all_citations(graph)
        reidentify(altered, inventory)
        self.assertTrue(before)
        self.assertEqual(all_citations(altered), before)
        validate_contract("Graph", altered, version="2.0")
        with self.assertRaisesRegex(EvidenceError, "RECONSTRUCTION_SOURCE_MISMATCH"):
            validate_v2(scope, inventory, altered, profile, profile_file_key="synthetic:profile.json")

    def test_closed_expression_contract_rejects_hidden_formula_fields(self):
        *_, graph = self.prepare("data work.b; set work.a; y=x+1; run;")
        altered = deepcopy(graph)
        fact = next(f for f in altered["operations"][0]["facts"] if f["kind"] == "assignment")
        fact["expression"]["alternate_formula"] = "x-1"
        with self.assertRaisesRegex(EvidenceError, "SCHEMA_INVALID"):
            validate_contract("Graph", altered, version="2.0")
        self.assertNotIn("Inventory", load_schema("2.0")["$defs"])
