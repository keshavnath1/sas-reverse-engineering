"""MVP-2 public development checks against the pre-rendering source expectations."""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid

import mvp2_expectations as expected
from mvp2_fixture import make_multi_module_case
from dependency_vectors import AUTHORITY, oracle_hash
from p2a_support import tree
from sas_re._dependency_diagnostics import diagnose
from sas_re._draft_preview import PreviewError, generate_preview

ROOT = Path(__file__).resolve().parents[1]
FILES = {"PRD.md", "MODULES.md", "ARCHITECTURE.md", "EVIDENCE.md", "ADR_NATIVE.md", "ADR_SPARK.md"}
LINK = re.compile(r"\[[^\]\n]*\]\(([^)\n]+)\)")
RECORD_ID = re.compile(r"\b(op|ds|col|edge)_[0-9a-f]{64}\b")


def preview(graph):
    diagnostic = diagnose(graph, oracle_hash(graph))
    return {name: data.decode("utf-8") for name, data in generate_preview(graph, diagnostic).items()}


class HistoricalPreviewTests(unittest.TestCase):
    def test_original_six_documents_match_accepted_bytes(self):
        # Read from 022c672 before this increment; no renderer or Git lookup.
        accepted = {
            "ADR_NATIVE.md": "afce343c9db09474ed974a55d70982fa288a5a42623d47809640650b297da544",
            "ADR_SPARK.md": "d718a16c8ee27e4e3eeada4c81e1918488962bb5ab930d129d6e545ccee39c4f",
            "ARCHITECTURE.md": "846348781598842998d7caa960d8f938c2b1797e2269adaa235f690a744b0e41",
            "EVIDENCE.md": "199c52abd4e7ce4da6cb13f985eabfa32876f80382bac2a7baef4b95442fc4e1",
            "MODULES.md": "902a4e57d339a45fa6d245dc75f2f8e9775d7a949395e0eb50801b45da19aeda",
            "PRD.md": "de83688ceef11315a859bbfe68d310c21fd7a0cdd182c216934b906b55489f7c",
        }
        actual = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT / "tests/fixtures/source-reconstruction/single-source-preview").iterdir()}
        self.assertEqual(actual, accepted)


@unittest.skipUnless(sys.platform in ("darwin", "linux"), "Source reconstruction requires POSIX")
class MultiModulePreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as folder:
            cls.scope, inventory, _, cls.graph = make_multi_module_case(Path(folder))
            cls.file_hashes = {f["file_key"]: f["sha256"] for f in inventory["files"]}
        cls.ops = sorted(cls.graph["operations"], key=lambda op: op["sequence"])
        cls.docs = preview(cls.graph)
        cls.datasets = {ds["dataset_id"]: ds["name"] for ds in cls.graph["datasets"]}
        cls.columns = {c["column_id"]: cls.datasets[c["dataset_id"]] + "." + c["name"] for c in cls.graph["columns"]}

    def test_owned_operations_original_spans_and_facts(self):
        self.assertEqual(set(self.graph["module_ids"]), {step["module"] for step in expected.STEPS})
        owners = {entry["file_key"]: entry["module_id"] for entry in self.scope["files"]}
        declarations = {(d["from_file_key"], d["to_file_key"], d["status"]) for d in self.scope["dependencies"]}
        self.assertIn(("synthetic:enrich.sas", "synthetic:prepare.sas", "DECLARED"), declarations)
        for op, step in zip(self.ops, expected.STEPS, strict=True):
            with self.subTest(sequence=op["sequence"]):
                label = f"O{op['sequence'] + 1}"
                self.assertEqual((op["kind"], op["module_id"]), (step["kind"], step["module"]))
                self.assertEqual({self.datasets[i] for i in op["reads"] if i in self.datasets}, set(step["reads"]))
                self.assertEqual({self.datasets[i] for i in op["writes"] if i in self.datasets}, set(step["writes"]))
                span = op["span"]
                self.assertEqual((span["line_start"], span["line_end"]), step["lines"])
                source = expected.SOURCES[step["file"]]
                self.assertEqual(owners[span["file_key"]], step["module"])
                self.assertEqual(self.file_hashes[span["file_key"]], hashlib.sha256(source).hexdigest())
                for ref in [span, *(f["span"] for f in op["facts"])]:
                    self.assertEqual(ref["file_key"], "synthetic:" + step["file"])
                    citation = ref["citation"]
                    whole_lines = source.splitlines(keepends=True)[ref["line_start"] - 1:ref["line_end"]]
                    for digest, raw in ((ref["byte_sha256"], source[ref["start"]:ref["end"]]),
                                        (citation["source_sha256"], source),
                                        (citation["excerpt_sha256"], b"".join(whole_lines))):
                        self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
                        self.assertIn(digest, self.docs["EVIDENCE.md"])
                for i, fact in enumerate(op["facts"]):
                    anchor = f"{label.lower()}-fact-{i}"
                    self.assertIn(f"EVIDENCE.md#{anchor}", self.docs["MODULES.md"])
                    self.assertIn(f"#### {label} fact {i}", self.docs["EVIDENCE.md"])
                    self.assertIn(fact["span"]["byte_sha256"], self.docs["EVIDENCE.md"])

    def test_mermaid_and_local_references_are_closed_over_canonical_records(self):
        index = {op["operation_id"]: op["sequence"] for op in self.ops}
        edges = [(index[e["from_operation_id"]], index[e["to_operation_id"]], e["type"]) for e in self.graph["edges"]]
        self.assertCountEqual(edges, expected.EDGES)
        diagram = self.docs["ARCHITECTURE.md"].split("```mermaid\n", 1)[1].split("```", 1)[0]
        links = re.findall(r"(op_[a-f0-9]{64}) -->\|(E\d+) (\w+)\| (op_[a-f0-9]{64})", diagram)
        self.assertCountEqual([(index[a], index[b], kind) for a, _, kind, b in links], edges)
        for source, label, kind, target in links:
            section = re.search(rf"(?ms)^### {label}$.*?(?=^#|\Z)", self.docs["EVIDENCE.md"])
            self.assertIsNotNone(section)
            originals = [e["edge_id"] for e in self.graph["edges"]
                         if (e["from_operation_id"], e["type"], e["to_operation_id"]) == (source, kind, target)]
            self.assertTrue(any(identifier in section.group() for identifier in originals))
        expected_ids = set(index) | set(self.datasets) | set(self.columns) | {e["edge_id"] for e in self.graph["edges"]}
        found_ids = {m.group() for doc in self.docs.values() for m in RECORD_ID.finditer(doc)}
        self.assertEqual(found_ids, expected_ids)
        for name, doc in self.docs.items():
            for dest in LINK.findall(doc):
                file, _, anchor = dest.partition("#")
                target = file or name
                self.assertIn(target, FILES, dest)
                if anchor:
                    headings = re.findall(r"(?m)^#{1,6} (.+)$", self.docs[target])
                    ids = {re.sub(r"[^\w-]", "", h.lower().replace(" ", "-")) for h in headings}
                    self.assertIn(anchor, ids, dest)

    def test_original_lineage_reaches_across_module_boundary_and_into_sql(self):
        for seq, output, inputs in expected.LINEAGE:
            op = self.ops[seq]
            # P2A conservatively attaches SQL ON/WHERE control inputs to output
            # lineage in addition to the SELECT expression's scalar operands.
            controls = ({"work.offsets.batch", "work.scaled.batch", "work.scaled.scaled"}
                        if op["kind"] == "PROC_SQL" else set())
            matches = [r for r in op["lineage"] if self.columns[r["output_column_id"]] == output
                       and {self.columns[c] for c in r["input_column_ids"]} == set(inputs) | controls]
            self.assertTrue(matches, (output, inputs))
            for r in matches:
                ref = f"EVIDENCE.md#o{seq + 1}-fact-{r['fact_index']}"
                rows = [line for line in self.docs["MODULES.md"].splitlines()
                        if ref in line and output in line and all(name in line for name in inputs)]
                self.assertTrue(rows, (ref, output, inputs))
        handoff = self.docs["ARCHITECTURE.md"]
        first, second = self.ops[:2]
        source_label, target_label = f"EVIDENCE.md#o{first['sequence'] + 1}", f"EVIDENCE.md#o{second['sequence'] + 1}"
        shared_dataset = expected.STEPS[0]["writes"][0]
        self.assertTrue(any(all(token in line for token in (shared_dataset, source_label, target_label,
                                                            first["module_id"], second["module_id"]))
                            for line in handoff.splitlines()))

    def test_literal_unknown_remains_unresolved_and_has_no_invented_edge(self):
        include = next(op for op in self.ops if op["kind"] == "INCLUDE")
        fact = next(f for f in include["facts"] if f["kind"] == "include")
        self.assertEqual(fact["path"], expected.MISSING_INCLUDE)
        self.assertIsNone(fact["target_file_key"])
        self.assertNotIn("synthetic:" + expected.MISSING_INCLUDE, self.file_hashes)
        bound = [issue for issue in self.graph["unknowns"] if include["operation_id"] in issue["operation_ids"]]
        global_gaps = [issue for issue in self.graph["unknowns"] if not issue["operation_ids"]]
        self.assertTrue(bound)
        self.assertTrue(any(issue["kind"] == "MISSING_DEPENDENCY" for issue in global_gaps))
        self.assertTrue(all(issue["status"] == "UNRESOLVED" for issue in bound))
        self.assertFalse(any(include["operation_id"] in (e["from_operation_id"], e["to_operation_id"])
                             for e in self.graph["edges"]))
        for issue in bound + global_gaps:
            self.assertIn(issue["issue_id"], self.docs["EVIDENCE.md"])
        for name in ("PRD.md", "MODULES.md", "ARCHITECTURE.md"):
            lines = [line.lower() for line in self.docs[name].splitlines() if expected.MISSING_INCLUDE in line]
            self.assertTrue(any("evidence.md#o4-fact-0" in line and re.search("unresolved|unknown", line)
                                for line in lines), name)
        self.assertRegex(self.docs["EVIDENCE.md"].lower(), "independence (?:is )?unproved|effect_completeness_unproved")

    def test_missing_cross_module_data_edge_creates_proof_obligation_only(self):
        changed = deepcopy(self.graph)
        removed = next(e for e in changed["edges"] if e["type"] == "DATA"
                       and e["from_operation_id"] == self.ops[0]["operation_id"] and e["to_operation_id"] == self.ops[1]["operation_id"])
        changed["edges"].remove(removed)
        changed["coverage"]["edge_count"] -= 1
        docs = preview(changed)
        self.assertNotIn(removed["edge_id"], "".join(docs.values()))
        diagram = docs["ARCHITECTURE.md"].split("```mermaid\n", 1)[1].split("```", 1)[0]
        self.assertNotRegex(diagram, rf"{removed['from_operation_id']} -->\|[^|]* DATA\| {removed['to_operation_id']}")
        self.assertRegex(docs["ARCHITECTURE.md"], r"(?i)1 shared dataset group\(s\) lack a direct DATA edge|missing direct DATA")
        with self.assertRaises(PreviewError):
            generate_preview(changed, diagnose(self.graph, oracle_hash(self.graph)))

    def test_order_state_and_sql_assertions_match_the_correct_fact(self):
        sort, consumer, sql, _ = self.ops
        self.assertEqual(tuple(sort["order_contract"]["keys"]), expected.SORT_KEYS)
        self.assertEqual(tuple(consumer["order_contract"]["keys"]), expected.SORT_KEYS)
        self.assertEqual(sort["order_contract"]["tie_order"], "UNSPECIFIED")
        assignment = next(f for f in consumer["facts"] if f["kind"] == "assignment")
        self.assertEqual(tree(assignment["expression"]), ("/", ("name", "value"), ("literal", "2")))
        self.assertEqual(consumer["stateful_constructs"], ["BY"])
        value_index = consumer["facts"].index(assignment)
        scaled = next(r for r in consumer["lineage"] if r["fact_index"] == value_index)
        self.assertEqual((scaled["input_phase"], scaled["input_fact_indices"]), ("CURRENT_ITERATION", []))
        sql_fact = next(f for f in sql["facts"] if f["kind"] == "sql")
        self.assertEqual(sql_fact["join"]["kind"], "INNER")
        self.assertEqual((tree(sql_fact["join"]["left"]), tree(sql_fact["join"]["right"])),
                         (("name", "s.batch"), ("name", "r.batch")))
        self.assertEqual([tree(f["expression"]) for f in sql_fact["select"]],
                         [("name", "s.batch"), ("+", ("name", "s.scaled"), ("name", "r.offset"))])
        where = sql_fact["where"]
        self.assertEqual((tree(where["left"]), where["operator"], tree(where["right"])),
                         (("name", "s.scaled"), ">", ("literal", "0")))
        self.assertEqual(sql_fact["order_by"], ["batch"])
        roles = {item["role"]: {self.columns[i] for i in item["input_column_ids"]} for item in sql["control_lineage"]}
        self.assertEqual(roles, {"SQL_ON": {"work.offsets.batch", "work.scaled.batch"},
                                 "SQL_WHERE": {"work.scaled.scaled"}})
        modules = self.docs["MODULES.md"]
        sql_lines = [line for line in modules.splitlines() if "EVIDENCE.md#o3-fact-1" in line]
        for value in ("s.batch", "r.batch", "s.scaled", "r.offset", "INNER", "ORDER BY"):
            self.assertIn(value.lower(), "\n".join(sql_lines).lower())
        # This simple assignment reads no prior-row value. The conservative
        # BY/STATE record is not independent proof of a recurrence or its absence.
        commentary = self.docs["ARCHITECTURE.md"] + modules
        state = [line for line in commentary.lower().splitlines() if "state annotation" in line or "by annotation" in line]
        self.assertTrue(any("conservative" in line for line in state))
        self.assertTrue(any(re.search(r"(?:does not establish|no independently demonstrated|unproved).*"
                                      r"(?:cross.row|prior.row|previous.row|preceding.row)", line)
                            and "evidence.md#" in line for line in state))
        self.assertIn("UNSPECIFIED", modules)
        self.assertRegex(commentary.lower(), r"partition")

    def test_each_adr_has_actionable_comparison_and_keeps_unmeasured_values_unknown(self):
        dimensions = (r"workload|input (?:size|volume)", r"order", r"partition", r"memory",
                      r"movement|transfer", r"operat", r"validat|tie.out")
        for name in ("ADR_NATIVE.md", "ADR_SPARK.md"):
            lines = self.docs[name].splitlines()
            table = [line for line in lines if line.startswith("|")]
            header = next((row for row in table if "spark" in row.lower() and
                           ("native" in row.lower() or "python" in row.lower())), None)
            self.assertIsNotNone(header, name)
            for pattern in dimensions:
                rows = [row for row in table if re.search(pattern, row.split("|")[1], re.I)]
                self.assertTrue(rows, (name, pattern))
                self.assertTrue(any("EVIDENCE.md#" in row for row in rows), (name, pattern))
            size_and_memory = [row for row in table if re.search("workload|memory", row.split("|")[1], re.I)]
            self.assertTrue(all("UNKNOWN" in row for row in size_and_memory))
            self.assertNotRegex("\n".join(table), r"(?i)\d+(?:\.\d+)?\s*(ms|GB|GiB|x faster)\b")
            ordering = next(row for row in table if "order" in row.split("|")[1].lower())
            self.assertIn("EVIDENCE.md#o3-fact-1", ordering)
            # The final SQL projection lacks sequence, so its tie-out cannot use
            # the two-key grain of the SORT intermediate.
            for index, (dataset, keys) in enumerate((("work.ordered", expected.SORT_KEYS),
                                                      ("work.scaled", expected.SORT_KEYS),
                                                      ("work.adjusted", ("batch",))), start=1):
                candidates = [line for line in lines if f"`{dataset}`" in line and "multiset" in line.lower()]
                self.assertTrue(any(re.findall(r"`([^`]+)`", line) == [dataset, *keys]
                                    and f"EVIDENCE.md#o{index}" in line for line in candidates), dataset)

    def test_both_fresh_demo_destinations_match_golden_bytes_and_manifest(self):
        outputs = []
        for _ in range(2):
            destination = Path("/tmp") / ("sas-re-mvp2-" + uuid.uuid4().hex)
            self.assertFalse(destination.exists())
            self.addCleanup(shutil.rmtree, destination, True)
            run = subprocess.run([sys.executable, "-IB", ROOT / "scripts/mvp2_demo.py",
                                  "--destination", destination], cwd="/tmp", env={**os.environ, "PATH": ""},
                                 capture_output=True, check=False, timeout=60)
            self.assertEqual(run.returncode, 0, run.stderr)
            outputs.append(run.stdout)
            manifest = json.loads(run.stdout)
            self.assertEqual(manifest["status"], "UNVERIFIED")
            self.assertEqual(manifest["fixture"], expected.CASE)
            self.assertEqual(manifest["graph_sha256"], oracle_hash(self.graph))
            self.assertEqual(manifest["source_consistency"], "PASSED")
            self.assertEqual(manifest["reconstruction_status"], "PARTIAL")
            self.assertEqual(manifest["stage_gate"], "BLOCKED")
            self.assertEqual({p.name for p in destination.iterdir()}, FILES)
            self.assertEqual([item["name"] for item in manifest["files"]], sorted(FILES))
            for item in manifest["files"]:
                name = item["name"]
                raw = (destination / name).read_bytes()
                self.assertEqual(raw, self.docs[name].encode())
                self.assertEqual(raw, (ROOT / "tests/fixtures/source-reconstruction/dependency-aware-preview" / name).read_bytes())
                self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()), (item["bytes"], item["sha256"]))
                for field, status in AUTHORITY.items():
                    self.assertIn(f"{field}: {status}\n", raw.decode())
                    self.assertEqual(manifest[field], status)
        self.assertEqual(outputs[0], outputs[1])

    def test_diagnostic_that_hides_a_missing_include_is_rejected(self):
        corrupt = diagnose(self.graph, oracle_hash(self.graph))
        blockers = corrupt["analysis"]["blockers"]
        blockers[:] = [b for b in blockers if "issue_id" not in b]
        self.assertLess(len(blockers), len(diagnose(self.graph, oracle_hash(self.graph))["analysis"]["blockers"]))
        with self.assertRaises(PreviewError):
            generate_preview(self.graph, corrupt)
