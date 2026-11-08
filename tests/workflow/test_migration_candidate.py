"""Migration candidates bind reviewed source evidence and reject unsupported typed rows."""

import json
from pathlib import Path
import runpy
import sys
from tempfile import TemporaryDirectory
import unittest
import uuid

from workflow.test_review_workflow import ROOT, call, remove_destination


SCRIPT = ROOT / "scripts/migration_candidate.py"
PUBLIC = ROOT / "tests/fixtures/source-reconstruction/agent-review"


@unittest.skipUnless(sys.platform in ("darwin", "linux"), "Existing POSIX evidence workflow")
class MigrationCandidateTests(unittest.TestCase):
    def destination(self, checkpoint):
        path = Path("/tmp") / f"sas-re-{checkpoint}-{uuid.uuid4().hex}"
        self.addCleanup(remove_destination, path)
        return path

    def test_bound_review_is_reproducible_and_traceable(self):
        package = self.destination("int1")
        intake = call(
            package,
            script=ROOT / "scripts/review_intake.py",
            extra=("--intake", str(PUBLIC / "public-input")),
        )
        self.assertEqual(intake.returncode, 0, intake.stderr)
        original = {p.name: p.read_bytes() for p in package.iterdir()}
        outputs = []
        for _ in range(2):
            target = self.destination("mig1")
            run = call(target, script=SCRIPT, extra=("--package", str(package.resolve())))
            self.assertEqual(run.returncode, 0, run.stderr)
            outputs.append({p.name: p.read_bytes() for p in target.iterdir()})
        self.assertEqual(outputs[0], outputs[1])
        validation = json.loads(outputs[0]["VALIDATION.json"])
        self.assertEqual(validation["verdict"], "PASS")
        self.assertEqual(validation["semantic_acceptance"], "BLOCKED")
        self.assertEqual(
            validation["observed"],
            [
                {"id": 1, "amount": 20.5},
                {"id": 1, "amount": -4},
                {"id": 1, "amount": 20.5},
                {"id": 2, "amount": 0},
                {"id": 3, "amount": 17},
            ],
        )
        manifest = json.loads(outputs[0]["MANIFEST.json"])
        self.assertEqual(
            manifest["input_manifest_sha256"], json.loads(intake.stdout)["manifest_sha256"]
        )
        self.assertEqual(manifest["operator_review_notes"], {"status": "NOT_SUPPLIED"})
        data = json.loads(original["SOURCE_2.json"])["declared_operation"]
        sort = json.loads(original["SOURCE_1.json"])["declared_operation"]
        self.assertEqual(data["selected_columns"], ["id", "amount"])
        keep = data["declaration_spans"]["keep"]
        self.assertEqual((keep["start"], keep["end"]), (35, 50))
        for role in ("writer", "reader"):
            dependency = json.loads(original["MANIFEST.json"])["cross_file_dependencies"][0]
            self.assertIn(dependency[role]["anchor"].encode(), outputs[0]["README.md"])
        self.assertEqual(sort["input"], data["output"])

        with TemporaryDirectory() as temp:
            notes = Path(temp).resolve() / "notes.json"
            record = json.loads((PUBLIC / "REVIEW_DRAFT.json").read_bytes())
            record.update(reviewer="Synthetic test operator", human_approval="APPROVED")
            notes.write_text(json.dumps(record), encoding="utf-8")
            sidecar_before = notes.read_bytes()
            target = self.destination("mig1")
            run = call(
                target,
                script=SCRIPT,
                extra=("--package", str(package.resolve()), "--review-notes", str(notes)),
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            reviewed = json.loads((target / "MANIFEST.json").read_bytes())
            self.assertEqual(
                reviewed["operator_review_notes"]["status"], "OPERATOR_APPROVAL_RECORDED"
            )
            self.assertEqual(
                (target / "VALIDATION.json").read_bytes(), outputs[0]["VALIDATION.json"]
            )
            self.assertEqual(notes.read_bytes(), sidecar_before)
        self.assertEqual({p.name: p.read_bytes() for p in package.iterdir()}, original)
        (package / "SOURCE_1.json").write_bytes(original["SOURCE_1.json"] + b"\n")
        refused = self.destination("mig1")
        run = call(refused, script=SCRIPT, extra=("--package", str(package.resolve())))
        self.assertEqual(run.returncode, 2)
        self.assertIn(b"REVIEW_PACKAGE_PAYLOAD_MISMATCH", run.stderr)
        self.assertFalse(refused.exists())

    def test_candidate_preserves_types_and_refuses_unsupported_rows(self):
        prepare = runpy.run_path(str(SCRIPT))["prepare_and_sort"]
        row = {"id": 1, "amount": 4, "memo": "integer"}
        tied = {**row, "amount": 4.0, "memo": "float"}
        observed = prepare([row, tied, row])
        self.assertEqual([type(item["amount"]) for item in observed], [int, float, int])
        self.assertTrue(all(set(item) == {"id", "amount"} for item in observed))
        self.assertEqual(row["memo"], "integer")
        for invalid in (
            {"id": 1},
            {**row, "id": None},
            {**row, "id": True},
            {**row, "amount": None},
            {**row, "amount": float("nan")},
            {**row, "amount": "4"},
            {**row, "memo": None},
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                prepare([invalid])
