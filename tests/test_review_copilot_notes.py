"""Public INT-4 review record and package binding checks."""

from copy import deepcopy
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
import uuid

from test_review_workflow import ROOT, call, remove_destination


EXAMPLE = ROOT / "examples/copilot-review"


@unittest.skipUnless(sys.platform in ("darwin", "linux"), "Existing POSIX evidence workflow")
class CopilotNotesTests(unittest.TestCase):
    def setUp(self):
        scratch = TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.record_file = Path(scratch.name).resolve() / "record.json"
        self.record = json.loads((EXAMPLE / "REVIEW_DRAFT.json").read_bytes())
        self.package = self.destination("int1")
        result = call(self.package, script=ROOT / "scripts/review_intake.py",
                      extra=("--intake", str(EXAMPLE / "public-input")))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["manifest_sha256"], self.record["manifest_sha256"])
        self.original = self.snapshot()
        self.record.update(reviewer="Synthetic test operator", human_approval="APPROVED")

    def destination(self, checkpoint):
        path = Path("/tmp") / f"sas-re-{checkpoint}-{uuid.uuid4().hex}"
        self.addCleanup(remove_destination, path)
        return path

    def snapshot(self):
        return {path.name: path.read_bytes() for path in self.package.iterdir()}

    def invoke(self, record):
        self.record_file.write_text(json.dumps(record), encoding="utf-8")
        destination = self.destination("int5")
        return call(destination, script=ROOT / "scripts/review_copilot_notes.py",
                    extra=("--package", str(self.package.resolve()), "--record", str(self.record_file))), destination

    def test_review_is_deterministic_and_preserves_package(self):
        outputs = []
        for _ in range(2):
            result, path = self.invoke(self.record)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual({item.name for item in path.iterdir()}, {"COPILOT_REVIEW.json"})
            outputs.append((path / "COPILOT_REVIEW.json").read_bytes())
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(json.loads(outputs[0]), self.record)
        self.assertEqual({item["disposition"] for item in self.record["findings"]},
                         {"ACCEPTED", "REJECTED", "NEEDS_EVIDENCE"})
        self.assertEqual(self.snapshot(), self.original)

    def test_refuses_missing_approval_bad_binding_and_unresolved_citations(self):
        cases = (
            ({"human_approval": "PENDING"}, None, "REVIEW_HUMAN_APPROVAL_REQUIRED"),
            ({"manifest_sha256": "0" * 64}, None, "REVIEW_MANIFEST_SHA256_MISMATCH"),
            ({}, {"path": "missing.sas.txt"}, "REVIEW_CITATION_INVALID"),
            ({}, {"path": "order.sas.txt"}, "REVIEW_CITATION_INVALID"),
            ({}, {"anchor": "bytes-0-16"}, "REVIEW_CITATION_INVALID"),
            ({}, {"anchor": "bytes-0-999"}, "REVIEW_CITATION_INVALID"),
        )
        for fields, citation, code in cases:
            with self.subTest(fields=fields, citation=citation):
                record = deepcopy(self.record)
                record.update(fields)
                if citation:
                    record["findings"][0]["citations"][0].update(citation)
                result, path = self.invoke(record)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn(code.encode(), result.stderr)
                self.assertFalse(path.exists())
        self.assertEqual(self.snapshot(), self.original)
        with (self.package / "SOURCE_2.md").open("ab") as report:
            report.write(b"\n")
        result, path = self.invoke(self.record)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn(b"REVIEW_PACKAGE_PAYLOAD_MISMATCH", result.stderr)
        self.assertFalse(path.exists())
