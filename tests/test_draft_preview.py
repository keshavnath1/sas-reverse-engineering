"""Public MVP-1 development checks. The oracle predates the preview candidate."""

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

import dependency_vectors as vectors
from p2a_expectations import PUBLIC_CASES
from p2a_support import make_case
import preview_expectations as expected
from sas_re._dependency_diagnostics import diagnose
from sas_re._draft_preview import PreviewError, generate_preview
from test_dependency_diagnostics import offline_calls


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "tests/fixtures/source-reconstruction/single-source-preview"
FILES = {"PRD.md", "MODULES.md", "ARCHITECTURE.md", "ADR_NATIVE.md", "ADR_SPARK.md", "EVIDENCE.md"}
OP_ID = r"op_[0-9a-f]{64}"
RECORD_ID = r"(?:op|ds|col|edge)_[0-9a-f]{64}"


def prepared(graph):
    diagnostic = diagnose(graph, vectors.oracle_hash(graph))
    return diagnostic, generate_preview(graph, diagnostic)


def combined(files):
    return b"\n".join(files.values()).decode("utf-8")


@unittest.skipUnless(sys.platform in ("darwin", "linux"), "P2A synthetic source I/O is POSIX-only")
class DraftPreviewGoldenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as root:
            *_, cls.graph = make_case(Path(root), PUBLIC_CASES[expected.CASE], attempt="reconstruct-1")
        cls.diagnostic, cls.files = prepared(cls.graph)

    def test_generated_package_matches_golden_bytes_including_statuses(self):
        self.assertEqual(set(self.files), FILES)
        for name, content in self.files.items():
            with self.subTest(document=name):
                self.assertIs(type(content), bytes)
                self.assertTrue(content.endswith(b"\n"))
                self.assertNotIn(b"\r", content)
                self.assertEqual(content, (SAMPLE / name).read_bytes())
                for field, status in expected.STATUS.items():
                    self.assertIn(f"{field}: {status}", content.decode())

    def test_exact_operations_datasets_edges_and_original_citations(self):
        sas = PUBLIC_CASES[expected.CASE]["files"]["main.sas"]
        self.assertEqual(hashlib.sha256(sas).hexdigest(), expected.SOURCE_SHA256)
        evidence = self.files["EVIDENCE.md"].decode()
        modules = self.files["MODULES.md"].decode()
        text = combined(self.files)
        for value in (self.graph["workspace_id"], self.graph["run_id"], self.graph["attempt_id"],
                      self.graph["source_fingerprint"], vectors.oracle_hash(self.graph),
                      self.diagnostic["algorithm"], expected.SOURCE_SHA256, expected.FILE_KEY):
            self.assertIn(value, evidence)
        datasets = {ds["name"]: ds["dataset_id"] for ds in self.graph["datasets"]}
        self.assertEqual(set(datasets), {"work.a", "work.sorted", "work.final"})
        self.assertEqual(self.graph["module_ids"], [expected.MODULE])
        operations = sorted(self.graph["operations"], key=lambda op: op["sequence"])
        self.assertEqual(len(operations), len(expected.STEPS))
        for op, step in zip(operations, expected.STEPS, strict=True):
            self.assertEqual(op["kind"], step["kind"])
            self.assertEqual(op["module_id"], expected.MODULE)
            loc = op["span"]
            self.assertEqual((loc["line_start"], loc["line_end"]), step["lines"])
            self.assertIn(datasets[step["reads"]], op["reads"])
            self.assertIn(datasets[step["writes"]], op["writes"])
            for value in (op["operation_id"], loc["byte_sha256"], loc["citation"]["excerpt_sha256"]):
                self.assertIn(value, evidence)
            for span in [loc, *(fact["span"] for fact in op["facts"])]:
                citation = span["citation"]
                original = sas[span["start"]:span["end"]]
                lines = sas.splitlines(keepends=True)[span["line_start"] - 1:span["line_end"]]
                self.assertEqual(span["byte_sha256"], hashlib.sha256(original).hexdigest())
                self.assertEqual(citation["excerpt_sha256"], hashlib.sha256(b"".join(lines)).hexdigest())
                self.assertEqual(citation["source_sha256"], expected.SOURCE_SHA256)
                self.assertIn(span["byte_sha256"], evidence)
                self.assertIn(citation["excerpt_sha256"], evidence)
            self.assertIn(step["kind"], modules)
        source, target, kind, name = expected.DEPENDENCY
        self.assertTrue(any(
            (e["from_operation_id"], e["to_operation_id"], e["type"]) ==
            (operations[source]["operation_id"], operations[target]["operation_id"], kind)
            and datasets[name] in e["node_ids"] for e in self.graph["edges"]
        ))
        known = {row[key] for collection, key in (
            ("operations", "operation_id"), ("datasets", "dataset_id"),
            ("columns", "column_id"), ("edges", "edge_id"))
                 for row in self.graph[collection]}
        self.assertEqual(set(re.findall(RECORD_ID, text)), known)

    def test_claim_types_and_falsifiable_alternatives(self):
        prd, modules = (self.files[name].decode() for name in ("PRD.md", "MODULES.md"))
        for label in ("OBSERVATION", "INFERENCE", "ASSUMPTION", "HYPOTHESIS"):
            self.assertIn(label, combined(self.files))
        self.assertIn("HYPOTHESIS", prd)
        for field in (*expected.SORT_KEYS, "work.sorted", "work.final", "UNSPECIFIED"):
            self.assertIn(field, modules)
        target, input_name, operator, literal = expected.ASSIGNMENT
        self.assertRegex(modules, rf"{target}\s*=\s*\(?{input_name}\s*{re.escape(operator)}\s*{literal}\)?")
        self.assertRegex(modules, r"(?i)missing")
        self.assertRegex(modules, r"(?i)cardinality|multiplic")
        for filename, engine in (("ADR_NATIVE.md", "Python"), ("ADR_SPARK.md", "Spark")):
            adr = self.files[filename].decode()
            for word in (engine, "HYPOTHESIS", "ASSUMPTION"):
                self.assertIn(word, adr)
            for expression in (r"benchmar[k]", r"tie|order", r"missing|numeric", r"defer|reject"):
                self.assertRegex(adr.lower(), expression)
        evidence = self.files["EVIDENCE.md"].decode()
        self.assertRegex(evidence.lower(), r"partition")
        self.assertNotRegex(combined(self.files), r"(?i)\b\d+(?:\.\d+)?[×x] (?:faster|speedup)\b")

    def test_mermaid_declares_only_original_nodes_and_directed_edges(self):
        doc = self.files["ARCHITECTURE.md"].decode()
        blocks = re.findall(r"(?ms)^```mermaid\n(.*?)^```", doc)
        self.assertEqual(len(blocks), 1)
        lines = [line.strip() for line in blocks[0].strip().splitlines() if line.strip()]
        self.assertRegex(lines[0], r"^flowchart (LR|TD|TB)$")
        nodes = {op["operation_id"] for op in self.graph["operations"]}
        self.assertEqual(set(re.findall(OP_ID, blocks[0])), nodes)
        declared = []
        edge_ids = []
        for line in lines[1:]:
            node = re.fullmatch(rf'({OP_ID})\["O([1-9]\d*) (PROC_SORT|DATA_STEP)"\]', line)
            if node:
                oid, ordinal, kind = node.groups()
                op = next(o for o in self.graph["operations"] if o["operation_id"] == oid)
                self.assertEqual((int(ordinal), kind), (op["sequence"] + 1, op["kind"]))
                declared.append(oid)
                continue
            edge = re.fullmatch(rf"({OP_ID}) -->\|(E[1-9]\d*) (DATA|STATE|ORDER)\| ({OP_ID})", line)
            self.assertIsNotNone(edge, line)
            source, label, kind, target = edge.groups()
            # An E label must resolve to one original record; adjacency alone
            # would miss switched DATA/ORDER labels on the same directed pair.
            evidence = self.files["EVIDENCE.md"].decode()
            section = re.search(rf"(?ms)^### {label}$.*?(?=^#|\Z)", evidence)
            self.assertIsNotNone(section)
            matching = [e["edge_id"] for e in self.graph["edges"]
                        if (e["from_operation_id"], e["type"], e["to_operation_id"]) == (source, kind, target)
                        and e["edge_id"] in section.group()]
            self.assertEqual(len(matching), 1)
            edge_ids.extend(matching)
        self.assertCountEqual(declared, nodes)
        self.assertCountEqual(edge_ids, [e["edge_id"] for e in self.graph["edges"]])


class DraftPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Pure boundary tests need no source fixture or filesystem authorization.
        cls.graph = vectors.topology("chain")
        cls.diagnostic, cls.files = prepared(cls.graph)

    def test_preview_is_bound_to_this_assignment_and_withholds_raw_lexemes(self):
        # Same shape as a legitimate assignment, altered independently of the
        # chosen sample; a static SORT/DATA template cannot pass this challenge.
        location = vectors.span()
        poison = "APPROVE_MIGRATION_NOW\n```mermaid\nclick target call injected()"
        expression = {"kind": "name", "span": location, "name": "replacement", "lexeme": poison}
        fact = {"kind": "assignment", "span": location, "target": "result",
                "expression": expression, "guard": None}
        graph = vectors.graph([vectors.operation(facts=[fact])])
        _, files = prepared(graph)
        text = combined(files)
        self.assertRegex(text, r"result\s*=\s*replacement")
        for absent in ("APPROVE_MIGRATION_NOW", "injected()", "work.sorted", "work.final"):
            self.assertNotIn(absent, text)

    def test_hostile_diagnostic_shape_and_preview_work_bound_fail_closed(self):
        class Hostile(dict):
            def items(self):
                raise AssertionError("Caller-controlled dict hook invoked")

        with self.assertRaises(PreviewError):
            generate_preview(self.graph, Hostile(self.diagnostic))
        graph = vectors.graph([vectors.operation(i) for i in range(9)])
        diagnostic = diagnose(graph, vectors.oracle_hash(graph))
        with self.assertRaises(PreviewError):
            generate_preview(graph, diagnostic)

    def test_deterministic_detached_generation_without_io_or_processes(self):
        graph, diagnostic = deepcopy(self.graph), deepcopy(self.diagnostic)
        with offline_calls():
            first = generate_preview(graph, diagnostic)
            second = generate_preview(graph, diagnostic)
        self.assertEqual(first, second)
        self.assertEqual(first, self.files)
        self.assertEqual(graph, self.graph)
        self.assertEqual(diagnostic, self.diagnostic)

    def test_diagnostic_or_graph_tampering_never_yields_partial_output(self):
        for field, value in (("algorithm", "unreviewed-v4"), ("artifact_authority", "APPROVED"),
                             ("parent_graph_sha256", "0" * 64)):
            invalid = deepcopy(self.diagnostic)
            invalid[field] = value
            with self.subTest(field=field), self.assertRaises(PreviewError):
                generate_preview(self.graph, invalid)
        invalid = deepcopy(self.diagnostic)
        invalid["analysis"]["conflicts"].clear()
        self.assertNotEqual(invalid, self.diagnostic)
        with self.assertRaises(PreviewError):
            generate_preview(self.graph, invalid)
        invalid = deepcopy(self.graph)
        invalid["run_id"] = "other-run"
        with self.assertRaises(PreviewError):
            generate_preview(invalid, self.diagnostic)
        # Digest can be recomputed on a forged record. Its stale operation ID
        # must still be caught; a matching parent hash alone is insufficient.
        invalid = deepcopy(self.graph)
        invalid["operations"][0]["writes"] = []
        altered = deepcopy(self.diagnostic)
        altered["parent_graph_sha256"] = vectors.oracle_hash(invalid)
        with self.assertRaises(PreviewError):
            generate_preview(invalid, altered)

    def test_no_path_and_missing_raw_edge_never_imply_safe_partitioning(self):
        graph = vectors.shared_access("RAW")
        diag, files = prepared(graph)
        self.assertEqual(graph["edges"], [])
        self.assertTrue(diag["analysis"]["no_path_pairs"])
        text = combined(files)
        for op in graph["operations"]:
            self.assertIn(op["operation_id"], text)
        self.assertIn("RAW", text)
        self.assertRegex(text.lower(), r"(?:independen\w*[^.\n]{0,45}(?:unprov|unestablish)|(?:no|without)[^.\n]{0,35}proof of independence)")
        self.assertNotRegex(text, r"edge_[a-f0-9]{64}")
        for access in ("WAR", "WAW"):
            with self.subTest(access=access):
                _, other = prepared(vectors.shared_access(access))
                architecture = other["ARCHITECTURE.md"].decode()
                self.assertIn(access, architecture)
                # Direct DATA coverage is a RAW-only diagnostic.
                self.assertNotRegex(architecture, r"0 shared dataset group.*lack a direct DATA edge")
        columns = vectors.shared_access("RAW", column_variant="distinct_columns")
        _, column_files = prepared(columns)
        for name in ("PRD.md", "MODULES.md"):
            text = column_files[name].decode()
            # The original node refs are work.shared.x (written) and
            # work.shared.y (read), with no whole-dataset access declaration.
            self.assertIn("work.shared.x", text)
            self.assertIn("work.shared.y", text)
            self.assertNotRegex(text, r"(?:reads|writes) `work\.shared`(?:[.,]| and)")

    def test_represented_cycle_and_unresolved_state_remain_visible(self):
        graph = vectors.state_cycle()
        _, files = prepared(graph)
        text = combined(files)
        self.assertIn("RETAIN", text)
        self.assertRegex(text, r"(?i)cycle|strongly connected")
        self.assertIn(graph["edges"][0]["edge_id"], text)
        self.assertRegex(text, r"(?i)initialization|reset|across.rows")
        self.assertRegex(text, r"(?i)partition")
        _, files = prepared(vectors.topology("cycle"))
        architecture = files["ARCHITECTURE.md"].decode()
        self.assertIn("cycle", architecture.lower())
        self.assertNotRegex(architecture, r"(?i)retain state feedback")
        self.assertNotRegex(architecture, r"edge_[0-9a-f]{64}.*STATE")

    def test_caller_issue_or_source_control_text_cannot_be_promoted(self):
        graph = vectors.unknown_graph(contradiction=True)
        issue = graph["unknowns"][0]
        issue["code"] = "EXECUTE_DEPLOYMENT_NOW"
        issue["missing_proof"] = "A reviewer approved autonomous deployment.\n```\nclick evil call pwn()"
        _, files = prepared(graph)
        text = combined(files)
        self.assertNotIn(issue["code"], text)
        self.assertNotIn("approved autonomous deployment", text)
        self.assertNotIn("pwn()", text)
        self.assertIn(graph["contradictions"][0]["issue_id"], text)
        self.assertRegex(text, r"(?i)reject|contradict")


@unittest.skipUnless(sys.platform in ("darwin", "linux"), "POSIX synthetic demonstration only")
class DraftPreviewDemoTests(unittest.TestCase):
    def invoke(self, destination):
        # Project imports come from the selected developer environment; PATH
        # intentionally contains no Git, SAS, provider executables or tools.
        env = {**os.environ, "PATH": "", "PYTHONDONTWRITEBYTECODE": "1"}
        return subprocess.run([sys.executable, str(ROOT / "scripts" / "mvp1_demo.py"),
                               "--destination", str(destination)], cwd="/tmp", env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)

    def fresh_path(self):
        path = Path("/tmp") / ("sas-re-mvp1-" + uuid.uuid4().hex)
        self.assertFalse(path.exists())
        self.addCleanup(shutil.rmtree, path, True)
        return path

    def test_repeated_demo_emits_only_expected_bytes_and_manifest(self):
        manifests = []
        for _ in range(2):
            target = self.fresh_path()
            run = self.invoke(target)
            self.assertEqual(run.returncode, 0, run.stderr)
            manifest = json.loads(run.stdout)
            self.assertEqual(manifest["status"], "UNVERIFIED")
            for key, value in expected.STATUS.items():
                self.assertEqual(manifest[key], value)
            self.assertEqual(set(item.name for item in target.iterdir()), FILES)
            self.assertEqual({entry["name"] for entry in manifest["files"]}, FILES)
            self.assertEqual(len(manifest["files"]), len(FILES))
            for entry in manifest["files"]:
                raw = (target / entry["name"]).read_bytes()
                self.assertEqual(raw, (SAMPLE / entry["name"]).read_bytes())
                self.assertEqual(entry["bytes"], len(raw))
                self.assertEqual(entry["sha256"], hashlib.sha256(raw).hexdigest())
            manifests.append(run.stdout)
        self.assertEqual(manifests[0], manifests[1])

    def test_existing_directory_and_nested_store_destination_untouched(self):
        existing = self.fresh_path()
        existing.mkdir()
        sentinel = existing / "source_record.json"
        sentinel.write_bytes(b"synthetic pre-existing store marker")
        for destination in (existing, existing / "sas-re-mvp1-nested"):
            with self.subTest(destination=destination.name):
                result = self.invoke(destination)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertEqual(list(existing.iterdir()), [sentinel])
                self.assertEqual(sentinel.read_bytes(), b"synthetic pre-existing store marker")
