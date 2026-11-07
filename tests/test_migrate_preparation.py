"""Focused public controls for binding SM-3B evidence to PY-1."""

from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest
import uuid

from test_review_workflow import ROOT, call, remove_destination


SCRIPT = ROOT / "scripts/migrate_preparation.py"
SOURCE = ROOT / "examples/mig3/preparation.sas.txt"


@unittest.skipUnless(sys.platform in ("darwin", "linux"), "Existing POSIX evidence workflow")
class PreparationMigrationTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.source = Path(temporary.name).resolve() / "preparation.sas"
        self.raw = SOURCE.read_bytes()
        self.source.write_bytes(self.raw)

    def destination(self, checkpoint):
        destination = Path("/tmp") / f"sas-re-{checkpoint}-{uuid.uuid4().hex}"
        self.addCleanup(remove_destination, destination)
        return destination

    def review(self, *, missing=True):
        destination = self.destination("source")
        result = call(destination, script=ROOT / "scripts/review_source.py", extra=(
            "--source", str(self.source), "--source-sha256", sha256(self.source.read_bytes()).hexdigest(),
            "--lines", "1:12", "--recover-status-rules",
            *(("--recover-missing-exclusions",) if missing else ()),
        ))
        self.assertEqual(result.returncode, 0, result.stderr)
        return destination.resolve()

    def invoke(self, review, digest=None):
        destination = self.destination("mig3")
        result = call(destination, script=SCRIPT, extra=(
            "--source", str(self.source),
            "--source-sha256", digest or sha256(self.source.read_bytes()).hexdigest(),
            "--evidence", str(review / "EVIDENCE.json"),
        ))
        return result, destination

    def test_execution_and_traces_are_bound_and_reproducible(self):
        review = self.review()
        original = {item.name: item.read_bytes() for item in review.iterdir()}
        snapshots = []
        for _ in range(2):
            run, output = self.invoke(review)
            self.assertEqual(run.returncode, 0, run.stderr)
            snapshots.append({item.name: item.read_bytes() for item in output.iterdir()})
        self.assertEqual(*snapshots)
        files = snapshots[0]
        manifest = json.loads(files["MANIFEST.json"])
        self.assertEqual(manifest["evidence"]["sha256"], sha256(original["EVIDENCE.json"]).hexdigest())
        self.assertEqual(manifest["source"]["sha256"], sha256(self.raw).hexdigest())
        for name, payload in manifest["files"].items():
            self.assertEqual(payload["sha256"], sha256(files[name]).hexdigest())
        validation = json.loads(files["VALIDATION.json"])
        self.assertEqual(validation["comparison"], "PASS")
        self.assertEqual(validation["semantic_acceptance"], "BLOCKED")
        self.assertEqual(len(validation["cases"]), 14)
        self.assertEqual(validation["summary"]["first_exclusions_by_rule"],
                         {"0": 2, "3": 4, "4": 3, "5": 2})
        self.assertEqual(validation["summary"]["candidate_row_end_count"], 3)
        rows = {row["input"]["case_id"]: row for row in json.loads(files["ROWS.json"])}
        evidence = json.loads(original["EVIDENCE.json"])
        rules = evidence["declared_operation"]["status_rule_recovery"]["rules"]
        for row in rows.values():
            self.assertEqual(row["sas_dataset_output"], "UNOBSERVED")
            for event in row["trace"]:
                span = rules[event["rule_index"]]["span"]
                self.assertEqual(event["span"], span)
                self.assertIn(f'id="{event["anchor"]}"'.encode(), original["README.md"])
                self.assertEqual(span["sha256"], sha256(self.raw[span["start"]:span["end"]]).hexdigest())
        for case, reached in {"C01": [0, 1, 3, 4, 5], "C02": [0, 1, 2, 3, 4, 5],
                              "C04": [0], "C11": [0, 1, 3], "C12": [0, 1, 2, 3, 4],
                              "P01": [1, 2, 3, 4, 5], "P02": [1, 2, 3]}.items():
            self.assertEqual([event["rule_index"] for event in rows[case]["trace"]
                              if event["action"] == "PREDICATE"], reached)
        self.assertEqual(rows["P01"]["candidate_output"]["default"], 9)
        self.assertIn("NO_ASSIGNMENT_BY_PAIR", [event["action"] for event in rows["P01"]["trace"]])
        self.assertEqual(rows["C02"]["candidate_output"]["character_group"][0], {"text": ".   "})
        self.assertEqual({item.name: item.read_bytes() for item in review.iterdir()}, original)
        self.assertEqual(self.source.read_bytes(), self.raw)

    def test_refuses_changed_partial_or_mismatched_rule_evidence(self):
        review = self.review()

        def refused(package, code, digest=None):
            result, destination = self.invoke(package, digest)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn(code, result.stderr)
            self.assertFalse(destination.exists())

        refused(review, b"MIGRATION_SOURCE_SHA256_MISMATCH", "0" * 64)
        refused(self.review(missing=False), b"MIGRATION_EVIDENCE_MISMATCH")
        self.source.write_bytes(self.raw.replace(b"Default=1", b"Default=7"))
        refused(review, b"MIGRATION_EVIDENCE_MISMATCH")
        refused(self.review(), b"MIGRATION_SIX_RULE_CONTRACT_UNSUPPORTED")
        self.source.write_bytes(self.raw.replace(b"n1,n2,n3", b"n2,n1,n3"))
        refused(self.review(), b"MIGRATION_SIX_RULE_CONTRACT_UNSUPPORTED")
