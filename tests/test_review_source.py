"""Source-only review checks using disposable public synthetic SAS text."""

from hashlib import sha256
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
import uuid

from test_review_workflow import ROOT, call, remove_destination


SCRIPT = ROOT / "scripts/review_source.py"
SORT = b"proc sort data=work.a out=work.b;\r\n  by id;\r\nrun;"
PREFIX = "/* café */\r\n%unreviewed_driver;\r\n".encode()


@unittest.skipUnless(sys.platform in ("darwin", "linux"), "Existing POSIX scratch writer")
class SourceReviewTests(unittest.TestCase):
    def setUp(self):
        scratch = "/private/tmp" if sys.platform == "darwin" else "/tmp"
        directory = self.enterContext(TemporaryDirectory(dir=scratch))
        self.source = Path(directory) / "input.sas"

    def review(self, raw, lines="3:5", expected=None, destination=None, second_lines=None):
        self.source.write_bytes(raw)
        if destination is None:
            destination = Path("/tmp") / f"sas-re-source-{uuid.uuid4().hex}"
            self.addCleanup(remove_destination, destination)
        run = call(destination, script=SCRIPT, extra=(
            "--source", str(self.source), "--source-sha256", expected or sha256(raw).hexdigest(),
            "--lines", lines, *(("--lines", second_lines) if second_lines else ()),
        ))
        return run, destination

    def test_supported_span_is_bound_to_original_bytes_and_deterministic(self):
        raw = PREFIX + SORT
        run, destination = self.review(raw)
        self.assertEqual(run.returncode, 0, run.stderr)
        files = {p.name: p.read_bytes() for p in destination.iterdir()}
        self.assertEqual(set(files), {"README.md", "EVIDENCE.json"})
        evidence = json.loads(files["EVIDENCE.json"])
        self.assertEqual(evidence["source_identity"], "VERIFIED")
        self.assertEqual(evidence["syntax_recognition"], "SUPPORTED")
        self.assertEqual(evidence["source"]["sha256"], sha256(raw).hexdigest())
        self.assertEqual(evidence["source"]["selected_span"], {
            "line_start": 3, "line_end": 5, "start": len(PREFIX), "end": len(raw),
            "sha256": sha256(SORT).hexdigest(),
        })
        operation = evidence["declared_operation"]
        self.assertEqual(operation["span"]["start"], len(PREFIX))
        self.assertEqual(operation["ordering_span"]["line_start"], 4)
        key = operation["ordering_span"]
        self.assertEqual(raw[key["start"]:key["end"]], b"by id;")
        self.assertEqual((operation["input"], operation["output"], operation["ordering_keys"]),
                         ("work.a", "work.b", ["id"]))
        self.assertEqual(evidence["boundaries"], {"upstream": "UNRESOLVED", "downstream": "UNRESOLVED"})
        for field, value in {
            "key_schema": "UNKNOWN", "supported_profile_reconstruction": "NOT_RUN",
            "behavioral_evidence": "UNAVAILABLE", "semantic_verification": "UNVERIFIABLE",
            "semantic_acceptance": "BLOCKED", "artifact_authority": "DRAFT",
            "benchmark_execution": "NOT_RUN",
        }.items():
            self.assertEqual(evidence[field], value)
        self.assertNotIn(b"PASS", files["EVIDENCE.json"])
        self.assertNotIn(b"proc sort", files["README.md"].lower())
        again, second = self.review(raw)
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual({p.name: p.read_bytes() for p in second.iterdir()}, files)
        refused, _ = self.review(raw, destination=destination)
        self.assertEqual(refused.returncode, 2)
        self.assertEqual({p.name: p.read_bytes() for p in destination.iterdir()}, files)

    def test_mismatched_hash_and_out_of_range_refuse_output(self):
        raw = PREFIX + SORT
        run, destination = self.review(raw, expected="0" * 64)
        self.assertEqual(run.returncode, 2)
        self.assertIn(b"SOURCE_SHA256_MISMATCH", run.stderr)
        self.assertFalse(destination.exists())
        run, destination = self.review(raw + b"\n", lines="3:6")
        self.assertEqual(run.returncode, 2)
        self.assertIn(b"LINE_RANGE_OUTSIDE_SOURCE", run.stderr)
        self.assertFalse(destination.exists())

    def test_unsupported_spans_publish_only_bound_refusal_evidence(self):
        for raw in (SORT.replace(b"by id", b"by descending id"),
                    b"%include 'missing.sas';", SORT + b"\n" + SORT):
            with self.subTest(size=len(raw)):
                count = len(raw.splitlines())
                run, destination = self.review(raw, lines=f"1:{count}")
                self.assertEqual(run.returncode, 2, run.stderr)
                evidence = json.loads((destination / "EVIDENCE.json").read_bytes())
                self.assertEqual(evidence["source_identity"], "VERIFIED")
                self.assertEqual(evidence["syntax_recognition"], "UNSUPPORTED")
                self.assertEqual(evidence["source"]["selected_span"]["sha256"], sha256(raw).hexdigest())
                self.assertIsNone(evidence["declared_operation"])
                self.assertTrue(evidence["reason_codes"])

    def test_data_step_recovers_declarations_and_six_separate_gaps(self):
        statements = [
            b"data work.target;",
            b"set work.input;",
            b"if category not in ('A','B') then delete;",
            b"if category = 'A' then label = 1;",
            b"else if category = 'B' then label = 0;",
            b"if missing(key) then delete;",
            b"if cmiss(x,",
            b" y) > 0 then delete;",
            b"if cmiss(z) > 0 then delete;",
            b"keep key label;",
            b"run;",
        ]
        raw = PREFIX + b"\r\n".join(statements)
        run, dest = self.review(raw, lines="3:13")
        self.assertEqual(run.returncode, 0, run.stderr)
        evidence = json.loads((dest / "EVIDENCE.json").read_bytes())
        self.assertEqual(evidence["source"]["sha256"], sha256(raw).hexdigest())
        self.assertEqual(evidence["source"]["selected_span"]["start"], len(PREFIX))
        self.assertEqual(evidence["source"]["selected_span"]["end"], len(raw))
        self.assertEqual(evidence["review_status"], "PARTIAL")
        self.assertEqual(evidence["syntax_recognition"], "PARTIAL")
        self.assertEqual(evidence["supported_profile_reconstruction"], "NOT_RUN")
        op = evidence["declared_operation"]
        self.assertEqual((op["kind"], op["input"], op["output"], op["selected_columns"]),
                         ("DATA_STEP", "work.input", "work.target", ["key", "label"]))
        for key, index in (("output", 0), ("input", 1), ("keep", 9)):
            location = op["declaration_spans"][key]
            self.assertEqual(location["line_start"], index + 3)
            self.assertEqual(raw[location["start"]:location["end"]], statements[index])
        gaps = op["unsupported_statements"]
        expected = [(2, 2), (3, 3), (4, 4), (5, 5), (6, 7), (8, 8)]
        self.assertEqual(len(gaps), len(expected))
        for gap, (first, last) in zip(gaps, expected, strict=True):
            location = gap["span"]
            text = b"\r\n".join(statements[first:last + 1])
            start = len(PREFIX) + sum(len(line) + 2 for line in statements[:first])
            self.assertEqual(location, {
                "line_start": first + 3, "line_end": last + 3,
                "start": start, "end": start + len(text), "sha256": sha256(text).hexdigest(),
            })
            self.assertTrue(gap["reason_codes"])
        self.assertEqual(op["row_selection"], "UNKNOWN")
        self.assertEqual(op["selected_column_values_and_derivation"], "UNKNOWN")
        self.assertNotIn("control_lineage", op)
        self.assertEqual(evidence["behavioral_evidence"], "UNAVAILABLE")
        readme = (dest / "README.md").read_bytes()
        self.assertIn(b"2 output selections", readme)
        self.assertNotIn(statements[3], readme)
        self.assertNotIn(b"PASS", (dest / "EVIDENCE.json").read_bytes())
        again, second = self.review(raw, lines="3:13")
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual({p.name: p.read_bytes() for p in dest.iterdir()},
                         {p.name: p.read_bytes() for p in second.iterdir()})

    def test_data_review_requires_one_terminated_step_and_one_set_input(self):
        raw = b"data work.target; set work.input; label = 1; keep label; run;"
        run, dest = self.review(raw, lines="1:1")
        self.assertEqual(run.returncode, 0, run.stderr)
        op = json.loads((dest / "EVIDENCE.json").read_bytes())["declared_operation"]
        self.assertEqual(op["unsupported_statements"][0]["reason_codes"],
                         ["TRANSFORMATION_OUTSIDE_REVIEW_SCOPE"])
        for bad in (raw.removesuffix(b" run;"), raw.replace(b"set work.input;", b"set work.input work.other;")):
            run, dest = self.review(bad, lines="1:1")
            self.assertEqual(run.returncode, 2, run.stderr)
            self.assertIsNone(json.loads((dest / "EVIDENCE.json").read_bytes())["declared_operation"])

    def test_two_ranges_bind_a_declared_connection_and_leave_middle_unexamined(self):
        data = (b"data work.Mixed;\r\nset work.input;\r\n"
                b"if missing(id) then delete;\r\nkeep id label;\r\nrun;\r\n")
        middle = b"%unexamined; data work.mixed; run;\r\n"
        sort = b"proc sort data=WORK.MIXED out=work.result; by id; run;"
        raw = PREFIX + data + middle + sort
        run, dest = self.review(raw, lines="3:7", second_lines="9:9")
        self.assertEqual(run.returncode, 0, run.stderr)
        payload = (dest / "EVIDENCE.json").read_bytes()
        evidence = json.loads(payload)
        self.assertEqual(evidence["source"]["sha256"], sha256(raw).hexdigest())
        first, second = evidence["selections"]
        for item, expected, start in ((first, data, len(PREFIX)),
                                      (second, sort, len(PREFIX + data + middle))):
            location = item["selected_span"]
            self.assertEqual((location["start"], location["end"]), (start, start + len(expected)))
            self.assertEqual(location["sha256"], sha256(expected).hexdigest())
        self.assertEqual(first["declared_operation"]["selected_columns"], ["id", "label"])
        self.assertEqual(len(first["declared_operation"]["unsupported_statements"]), 1)
        self.assertEqual(second["declared_operation"]["ordering_keys"], ["id"])
        self.assertEqual(evidence["connection"], {
            "classification": "SOURCE_DECLARED", "execution_verification": "EXECUTION_UNVERIFIED",
            "data_output": "work.mixed", "sort_input": "work.mixed",
        })
        self.assertEqual(evidence["intervening_span"], {
            "status": "UNEXAMINED", "start": len(PREFIX + data), "end": len(PREFIX + data + middle),
        })
        self.assertNotIn(middle, payload)
        self.assertEqual(evidence["semantic_acceptance"], "BLOCKED")
        again, other = self.review(raw, lines="3:7", second_lines="9:9")
        self.assertEqual(again.returncode, 0, again.stderr)
        for name in ("README.md", "EVIDENCE.json"):
            self.assertEqual((dest / name).read_bytes(), (other / name).read_bytes())

    def test_nonmatching_connection_and_ambiguous_selection(self):
        data = b"data work.target; set work.input; keep id; run;\n"
        sort = b"proc sort data=work.other out=work.sorted; by id; run;"
        run, dest = self.review(data + sort, lines="1:1", second_lines="2:2")
        self.assertEqual(run.returncode, 0, run.stderr)
        evidence = json.loads((dest / "EVIDENCE.json").read_bytes())
        self.assertEqual(evidence["connection"]["classification"], "UNRESOLVED")
        for raw, second in ((data + sort, "1:2"),
                            (data.replace(b"set work.input", b"set work.input work.extra") + sort, "2:2")):
            run, dest = self.review(raw, lines="1:1", second_lines=second)
            self.assertEqual(run.returncode, 2, run.stderr)
            self.assertFalse(dest.exists())
