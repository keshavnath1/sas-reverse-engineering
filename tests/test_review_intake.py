"""End-to-end checks for the approved public folder and its review package."""

from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
import unittest
import uuid

from test_review_workflow import ROOT, call, remove_destination


FIXTURE = ROOT / "examples/public-intake"
SCRIPT = ROOT / "scripts/review_intake.py"


@unittest.skipUnless(sys.platform in ("darwin", "linux"), "Existing POSIX evidence workflow")
class IntakeReviewTests(unittest.TestCase):
    def invoke(self, intake, destination=None):
        if destination is None:
            destination = Path("/tmp") / f"sas-re-int1-{uuid.uuid4().hex}"
            self.addCleanup(remove_destination, destination)
        return call(destination, script=SCRIPT, extra=("--intake", str(intake))), destination

    def test_public_intake_is_deterministic_and_traceable(self):
        with TemporaryDirectory() as temp:
            copied = Path(temp).resolve() / "INTAKE"
            shutil.copytree(FIXTURE, copied)
            runs = [self.invoke(root) for root in (FIXTURE, copied)]
        packages = []
        for run, destination in runs:
            self.assertEqual(run.returncode, 0, run.stderr)
            package = {p.name: p.read_bytes() for p in destination.iterdir()}
            self.assertEqual(set(package), {"README.md", "EVIDENCE.json", "MIGRATION_REVIEW.md", "MANIFEST.json"})
            manifest = json.loads(package["MANIFEST.json"])
            self.assertEqual(json.loads(run.stdout)["manifest_sha256"],
                             sha256(package["MANIFEST.json"]).hexdigest())
            for name, payload in package.items():
                if name != "MANIFEST.json":
                    self.assertEqual(manifest["files"][name],
                                     {"bytes": len(payload), "sha256": sha256(payload).hexdigest()})
            source = (FIXTURE / "pipeline.sas.txt").read_bytes()
            self.assertEqual(manifest["inputs"]["pipeline.sas.txt"]["sha256"], sha256(source).hexdigest())
            evidence = json.loads(package["EVIDENCE.json"])
            self.assertEqual(evidence["source"], manifest["inputs"]["pipeline.sas.txt"])
            self.assertEqual(evidence["syntax_recognition"], "PARTIAL")
            self.assertEqual(evidence["connection"]["execution_verification"], "EXECUTION_UNVERIFIED")
            self.assertEqual(evidence["interval_effects"]["sort_reachability"], "UNESTABLISHED")
            gaps = evidence["selections"][0]["declared_operation"]["unsupported_statements"]
            self.assertTrue(gaps)
            for gap in gaps:
                span = gap["span"]
                self.assertEqual(sha256(source[span["start"]:span["end"]]).hexdigest(), span["sha256"])
            report = package["MIGRATION_REVIEW.md"].decode()
            for marker in ("## TRACE", "## MAP", "Behavioral obligations", "Native Python", "distributed engine"):
                self.assertIn(marker, report)
            self.assertEqual(manifest["behavioral_evidence"], "UNAVAILABLE")
            self.assertEqual(manifest["semantic_acceptance"], "BLOCKED")
            self.assertEqual(manifest["copilot_review"], "NOT_TESTED")
            packages.append(package)
        self.assertEqual(*packages)

    def test_refuses_unapproved_intake_and_existing_destination(self):
        with TemporaryDirectory() as temp:
            copied = Path(temp).resolve() / "INTAKE"
            shutil.copytree(FIXTURE, copied)
            for name, data, reason in (
                ("extra.txt", b"extra", b"INTAKE_FILE_SET_MISMATCH"),
                ("scope.json", b"{}", b"INTAKE_SCOPE_NOT_APPROVED"),
                ("pipeline.sas.txt", b"changed", b"SOURCE_SHA256_MISMATCH"),
            ):
                with self.subTest(name=name):
                    (copied / name).write_bytes(data)
                    run, dest = self.invoke(copied)
                    self.assertEqual(run.returncode, 2)
                    self.assertIn(reason, run.stderr)
                    self.assertFalse(dest.exists())
                    if (FIXTURE / name).exists():
                        shutil.copyfile(FIXTURE / name, copied / name)
                    else:
                        (copied / name).unlink()
        run, dest = self.invoke(FIXTURE)
        self.assertEqual(run.returncode, 0, run.stderr)
        before = (dest / "MANIFEST.json").read_bytes()
        run, _ = self.invoke(FIXTURE, dest)
        self.assertEqual(run.returncode, 2)
        self.assertEqual((dest / "MANIFEST.json").read_bytes(), before)
