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

    def review(self, raw, lines="3:5", expected=None, destination=None):
        self.source.write_bytes(raw)
        if destination is None:
            destination = Path("/tmp") / f"sas-re-source-{uuid.uuid4().hex}"
            self.addCleanup(remove_destination, destination)
        run = call(destination, script=SCRIPT, extra=(
            "--source", str(self.source), "--source-sha256", expected or sha256(raw).hexdigest(),
            "--lines", lines,
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
