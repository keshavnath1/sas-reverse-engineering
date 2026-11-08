"""Public decision-review checks against the accepted evidence and hand-authored cases."""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest

from mvp2_fixture import make_multi_module_case
from mvp3_cases import CASES
from sas_re._decision_review import ReviewBindingError, render_review
from test_dependency_diagnostics import offline_calls


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples/mvp4/DECISION_REVIEW.md"
SCRIPT = ROOT / "scripts/mvp4_review.py"
LINK = re.compile(r"\[([^]\n]+)\]\(([^)\n]+)\)")
# Minimal witnesses required for these distinct obligations. An overlapping case can
# support more than one row; the unresolved include can never supply a positive O4 test.
WITNESSES = {
    "sort_set": ({"B05", "B07", "B11"}, {"o1-fact-0", "e2"}),
    "state_value": ({"B01", "B10"}, {"o2-fact-3", "e3"}),
    "join_where": ({"B02", "B09", "B13"}, {"o3-fact-1"}),
    "missing": ({"B14", "B15"}, {"o3-fact-1"}),
    "sql_ties": ({"B03", "B06", "B08", "B12"}, {"o3-fact-1"}),
    "precision": ({"B10", "B16"}, {"o2-fact-3"}),
    "partition": ({"B04"}, {"e3"}),
    "include": ({"B17"}, {"o4-fact-0"}),
}


def report_bytes(value):
    # The original development script's full stdout format, including its final LF.
    return (json.dumps(value, allow_nan=False) + "\n").encode()


@unittest.skipUnless(sys.platform in ("darwin", "linux"), "Original P2A fixture I/O requires POSIX")
class DecisionReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as scratch:
            *_, cls.graph = make_multi_module_case(Path(scratch))
        cls.report = runpy.run_path(str(ROOT / "scripts/mvp3_tieout.py"))["build_report"]()
        cls.raw = report_bytes(cls.report)
        cls.text = render_review(cls.graph, cls.raw).decode()
        cls.rows = [line for line in cls.text.splitlines() if line.startswith("|")]

    def check_refusal(self, graph, raw):
        with self.assertRaises(ReviewBindingError):
            render_review(graph, raw)

    def test_exact_subject_repeats_without_caller_io_and_matches_sample(self):
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(),
                         "aee7cbd480b1f6794888616af9c55e8896ecb13fa3dc1585d1b012f0a8508600")
        snapshot = deepcopy(self.graph)
        with offline_calls():
            first = render_review(self.graph, self.raw)
            again = render_review(dict(reversed(self.graph.items())), self.raw)
        self.assertEqual(self.graph, snapshot)
        self.assertEqual(first, again)
        self.assertEqual(first, SAMPLE.read_bytes())
        self.assertTrue(first.endswith(b"\n"))
        for field in ("artifact_authority", "semantic_verification", "semantic_acceptance", "benchmark_execution"):
            self.assertIn(f"{field}: {self.report[field]}", self.text)

    def test_matrix_links_to_original_operations_and_attested_case_outcomes(self):
        ids = set()
        lines = (ROOT / "tests/mvp3_cases.py").read_text().splitlines()
        expected = {case_id.split("-", 1)[0]: (case_id, verdict)
                    for case_id, (_, _, verdict, _) in CASES.items()}
        for row in self.rows:
            plain = LINK.sub(r"\1", row).replace("*", "").replace("`", "")
            for label, dest in LINK.findall(row):
                match = re.search(r"\b(B\d\d)\b", label)
                if not match:
                    continue
                short = match.group(1)
                case_id, verdict = expected[short]
                source = re.search(r"tests/mvp3_cases\.py#L(\d+)$", dest)
                self.assertIsNotNone(source, (short, dest))
                self.assertIn(f'"{case_id}"', lines[int(source.group(1)) - 1])
                expected_label = "deliberate FAIL" if verdict == "FAIL" else verdict
                self.assertRegex(plain, rf"\b{short}\s*(?:[·:—–-]\s*)?{expected_label}\b")
                ids.add(short)
        self.assertEqual(ids, set(expected))
        for subject, (required_cases, anchors) in WITNESSES.items():
            with self.subTest(subject=subject):
                matches = [r for r in self.rows if required_cases <= set(re.findall(r"\bB\d\d\b", r))
                           and anchors <= set(re.findall(r"EVIDENCE\.md#(\w[\w-]*)", r))]
                self.assertEqual(len(matches), 1)
                requirement, controls, native, spark, next_test = matches[0].strip("|").split("|")
                self.assertTrue(requirement.strip() and controls.strip() and next_test.strip())
                self.assertTrue(native.strip() and spark.strip())
                self.assertNotEqual(native.strip(), spark.strip())

    def test_missing_proof_and_unmeasured_tradeoffs_remain_open(self):
        def row(case):
            return next(line for line in self.rows if case in line)

        # Presence in a table alone is insufficient: these limits concern different
        # subjects. B04 probes a public two-chunk function; B17 passes only O1–O3.
        self.assertIn("postcheck.sas", row("B17"))
        self.assertRegex(row("B17"), r"(?i)unverifiable|unresolved|blocked")
        self.assertRegex(row("B17"), r"(?i)subset|O1.{0,9}O3")
        self.assertRegex(row("B15"), r"\.A|special missing")
        self.assertRegex(row("B16"), r"9007199254740993|2\^53|precision")
        self.assertRegex(row("B04"), r"(?i)chunk|split")
        self.assertRegex(row("B04"), r"(?i)partition")
        sizing = [line for line in self.rows if re.search("workload|hardware|capacity", line, re.I)
                  and not re.search(r"\bB\d\d\b", line)]
        self.assertTrue(sizing, "Resource planning needs a row distinct from measured case evidence")
        self.assertTrue(any(re.search("UNKNOWN|NOT_RUN|unmeasured", r, re.I) for r in sizing))
        self.assertRegex(self.text, r"(?i)deliberate.{0,30}FAIL")
        self.assertRegex(self.text, r"(?i)unexpected|refus")
        self.assertNotRegex(self.text, r"(?i)\b(?:\d+(?:\.\d+)?[x×] faster|HUMAN_APPROVED)\b")
        self.assertIn("ADR_NATIVE.md", self.text)
        self.assertIn("ADR_SPARK.md", self.text)
        evidence = (ROOT / "examples/mvp2/EVIDENCE.md").read_text()
        heads = {h.lower().replace(" ", "-") for h in re.findall(r"(?m)^#{1,6} (.+)$", evidence)}
        for anchor in re.findall(r"EVIDENCE\.md#(\w[\w-]*)", self.text):
            self.assertIn(anchor, heads)

    def test_deleted_source_cases_or_changed_subject_cannot_render(self):
        for data in (b"", self.raw[:-1], report_bytes({})):
            with self.subTest(size=len(data)):
                self.check_refusal(self.graph, data)
        # Same byte count and valid JSON, but no longer the accepted numeric challenge.
        altered_bytes = self.raw.replace(b"9007199254740993", b"9007199254740992")
        self.assertNotEqual(altered_bytes, self.raw)
        self.check_refusal(self.graph, altered_bytes)
        for field in ("source_sha256", "specification_sha256", "original_fixture_sha256", "original_mvp2_graph_sha256"):
            altered = deepcopy(self.report)
            del altered["reference"][field]
            with self.subTest(missing=field):
                self.check_refusal(self.graph, report_bytes(altered))
        altered = deepcopy(self.report)
        del altered["cases"][0]
        self.check_refusal(self.graph, report_bytes(altered))
        altered = deepcopy(self.graph)
        altered["unknowns"] = []
        altered["coverage"]["unknown_count"] = 0
        self.check_refusal(altered, self.raw)

    def test_unexpected_control_failure_and_hidden_counterexamples_refuse(self):
        for prefix, changes in (
            ("B01", {"verdict": "FAIL", "expected_verdict": "FAIL", "matches_specification": True}),
            ("B09", {"discrepancies": [], "matches_specification": True}),
            ("B12", {"matches_specification": False}),
            ("B15", {"verdict": "PASS", "observed": {}}),
            ("B17", {"full_workflow_gate": "PASS"}),
        ):
            changed = deepcopy(self.report)
            case = next(case for case in changed["cases"] if case["case_id"].startswith(prefix))
            case.update(changes)
            with self.subTest(prefix=prefix):
                self.check_refusal(self.graph, report_bytes(changed))
        changed = deepcopy(self.report)
        case = next(case for case in changed["cases"] if case["case_id"].startswith("B12"))
        # Integer 0 compares equal to False in Python but changes the attested JSON evidence.
        case["policy"]["observed_acceptance"] = 0
        self.check_refusal(self.graph, report_bytes(changed))

    def test_refuses_status_promotion_in_report_or_graph(self):
        for field, false_value in (("semantic_acceptance", "PASS"), ("semantic_verification", "VERIFIED"),
                                   ("artifact_authority", "APPROVED"), ("benchmark_execution", "PASSED")):
            with self.subTest(field=field):
                self.check_refusal(self.graph, report_bytes({**self.report, field: false_value}))
                self.check_refusal({**self.graph, field: false_value}, self.raw)
        altered = deepcopy(self.report)
        altered["unresolved_include"]["verdict"] = "PASS"
        self.check_refusal(self.graph, report_bytes(altered))

    def test_offline_development_script_emits_sample_on_stdout(self):
        guard = """
import runpy, sys
def deny(event, args):
    if event.startswith(('socket.', 'subprocess.', 'os.system', 'os.spawn', 'os.posix_spawn', 'os.fork', 'os.exec')):
        raise AssertionError(event)
sys.addaudithook(deny)
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name='__main__')
"""
        with tempfile.TemporaryDirectory() as cwd:
            run = subprocess.run([sys.executable, "-IB", "-c", guard, str(SCRIPT)], cwd=cwd, env={**os.environ, "PATH": ""},
                                 capture_output=True, timeout=60)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(run.stdout, SAMPLE.read_bytes())
            self.assertEqual(list(Path(cwd).iterdir()), [])

    def test_script_refuses_drift_before_executing_fixture_declarations(self):
        with tempfile.TemporaryDirectory() as tmp:
            scratch = Path(tmp)
            for name in ("scripts/mvp4_review.py", "scripts/mvp1_demo.py", "scripts/mvp3_tieout.py",
                         "tests/mvp2_fixture.py", "tests/p2a_support.py", "tests/mvp2_expectations.py",
                         "tests/mvp3_cases.py", "docs/SYNTHETIC_TIEOUT_VALIDATION.md", "examples/mvp2/EVIDENCE.md",
                         "examples/mvp2/ADR_NATIVE.md", "examples/mvp2/ADR_SPARK.md"):
                target = scratch / name
                target.parent.mkdir(exist_ok=True, parents=True)
                shutil.copyfile(ROOT / name, target)

            def invoke():
                return subprocess.run([sys.executable, "-IB", scratch / "scripts/mvp4_review.py"],
                                      cwd=scratch, capture_output=True, timeout=60)

            control = invoke()
            self.assertEqual(control.returncode, 0, control.stderr)
            self.assertEqual(control.stdout, SAMPLE.read_bytes())

            adr = scratch / "examples/mvp2/ADR_SPARK.md"
            original_adr = adr.read_bytes()
            adr.write_bytes(original_adr + b"\nAltered synthetic ADR.\n")
            changed = invoke()
            self.assertEqual(changed.returncode, 2)
            self.assertFalse(changed.stdout)
            self.assertIn(b"BLOCKED", changed.stderr)
            adr.write_bytes(original_adr)

            fixture = scratch / "tests/mvp2_expectations.py"
            with fixture.open("ab") as output:
                output.write(b'\nraise RuntimeError("UNVERIFIED_FIXTURE_EXECUTED")\n')
            refused = invoke()
            self.assertEqual(refused.returncode, 2)
            self.assertFalse(refused.stdout)
            self.assertIn(b"BLOCKED", refused.stderr)
            self.assertNotIn(b"UNVERIFIED_FIXTURE_EXECUTED", refused.stderr)
