"""Public operator handoff and approval-gated MIG-2 integration checks."""

from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
import unittest
import uuid

from test_review_workflow import ROOT, call, remove_destination


EXAMPLE = ROOT / "examples/mig2"


@unittest.skipUnless(sys.platform in ("darwin", "linux"), "Existing POSIX evidence workflow")
class IntegratedReviewTests(unittest.TestCase):
    def setUp(self):
        root = Path(self.enterContext(TemporaryDirectory())).resolve()
        self.intake = root / "intake"
        shutil.copytree(EXAMPLE / "public-input", self.intake)
        self.record = root / "claims.json"
        self.approval = root / "approval.json"
        self.package = self.build_package()

    def destination(self, stage):
        path = Path("/tmp") / f"sas-re-{stage}-{uuid.uuid4().hex}"
        self.addCleanup(remove_destination, path)
        return path

    def build_package(self):
        path = self.destination("int1")
        result = call(path, script=ROOT / "scripts/review_intake.py",
                      extra=("--intake", str(self.intake)))
        self.assertEqual(result.returncode, 0, result.stderr)
        return path.resolve()

    def write_claims(self, *, negative=False, digest=None):
        statements = (
            ("reconstruction", "The DATA output is work.projected.",
             "SOURCE_DECLARED", "SOURCE_1.json", "/declared_operation/output"),
            ("prd", "The SORT input is work.projected.",
             "SOURCE_DECLARED", "SOURCE_2.json", "/declared_operation/input"),
            ("dependency_analysis", "The matching names support a potential handoff.",
             "INFERRED", "MANIFEST.json", "/cross_file_dependencies/0/classification"),
            ("verification_plan", "Execution order still requires evidence.",
             "UNRESOLVED", "MANIFEST.json", "/cross_file_dependencies/0/execution_order"),
            ("adr", "Semantic acceptance is blocked.",
             "PACKAGE_METADATA", "MANIFEST.json", "/semantic_acceptance"),
        )
        deliverables = {name: {"Review": text} for name, text, *_ in statements}
        if negative:
            deliverables["reconstruction"]["Review"] += " Traced the declared handoff."
        record = {
            "version": 1,
            "manifest_sha256": digest or sha256((self.package / "MANIFEST.json").read_bytes()).hexdigest(),
            "deliverables": deliverables,
            "claims": [
                {"id": name, "text": text, "classification": classification,
                 "evidence": [{"file": file, "pointer": pointer}],
                 "deliverable": name, "section": "Review", "disposition": "APPROVED"}
                for name, text, classification, file, pointer in statements
            ],
        }
        self.record.write_text(json.dumps(record), encoding="utf-8")
        self.approval.write_text(json.dumps({
            "record_sha256": sha256(self.record.read_bytes()).hexdigest(),
            "reviewer": "Synthetic test reviewer", "decision": "APPROVED",
        }), encoding="utf-8")

    def invoke(self, *review_args, stage="intg1", script="review_to_migration.py"):
        path = self.destination(stage)
        rows = EXAMPLE / "CASES.json"
        result = call(path, script=ROOT / "scripts" / script, extra=(
            "--intake", str(self.intake), "--package", str(self.package),
            "--rows", str(rows), "--rows-sha256", sha256(rows.read_bytes()).hexdigest(),
            *review_args,
        ))
        return result, path

    def assert_paused(self, decision, code, *args):
        result, path = self.invoke(*args)
        self.assertEqual(result.returncode, 1 if decision == "REVIEW_REQUIRED" else 2)
        report = json.loads(result.stdout)
        self.assertEqual(report["decision"], decision)
        self.assertIn(code, [item["code"] for item in report.get("pending", []) + report.get("blocks", [])])
        self.assertFalse(path.exists())

    def test_manual_checkpoints_refuse_publication(self):
        self.assert_paused("REVIEW_REQUIRED", "COPILOT_CLAIM_RECORD_REQUIRED")
        record = ("--record", str(self.record))
        approval = ("--approval", str(self.approval))
        self.assert_paused("BLOCK", "FILE_NOT_FOUND", *record)
        self.write_claims(digest="0" * 64)
        self.assert_paused("BLOCK", "CLAIM_INPUT_REFUSED", *record, *approval)
        self.write_claims(negative=True)
        self.assert_paused("BLOCK", "DECLARED_HANDOFF", *record, *approval)
        self.write_claims()
        self.assert_paused("REVIEW_REQUIRED", "BOUND_HUMAN_APPROVAL_REQUIRED", *record)
        self.record.write_bytes(self.record.read_bytes() + b"\n")
        self.assert_paused("REVIEW_REQUIRED", "BOUND_HUMAN_APPROVAL_REQUIRED", *record, *approval)

    def test_pass_reuses_candidate_and_preserves_review(self):
        def snapshot(path):
            return {item.name: item.read_bytes() for item in path.iterdir()}

        before = snapshot(self.package)
        self.assertEqual(before, snapshot(self.build_package()))
        self.write_claims()
        bundles = []
        for _ in range(2):
            result, path = self.invoke("--record", str(self.record), "--approval", str(self.approval))
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(json.loads(result.stdout)["decision"], "PASS")
            bundles.append(snapshot(path))
        self.assertEqual(*bundles)
        manifest = json.loads(bundles[0]["MANIFEST.json"])
        self.assertEqual(manifest["semantic_acceptance"], "BLOCKED")
        for path, key in ((self.record, "claim_record"), (self.approval, "reviewer_approval")):
            self.assertEqual(manifest[key]["sha256"], sha256(path.read_bytes()).hexdigest())
        for name, entry in manifest["files"].items():
            self.assertEqual(entry["sha256"], sha256(bundles[0][name]).hexdigest())

        result, legacy = self.invoke(stage="mig2", script="migrate_projection_sort.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in ("PLAN.json", "ROWS.json", "VALIDATION.json"):
            self.assertEqual(bundles[0][name], (legacy / name).read_bytes())
        self.assertEqual(before, snapshot(self.package))

    def test_gate_pass_cannot_enable_unsupported_source(self):
        scope_path = self.intake / "scope.json"
        scope = json.loads(scope_path.read_bytes())
        raw = b"data work.projected; set work.samples; score=score+1; keep score reading; run;\n"
        (self.intake / "project.sas.txt").write_bytes(raw)
        scope["sources"][0]["sha256"] = sha256(raw).hexdigest()
        scope_path.write_text(json.dumps(scope), encoding="utf-8")
        self.package = self.build_package()
        self.write_claims()
        result, path = self.invoke("--record", str(self.record), "--approval", str(self.approval))
        self.assertEqual(result.returncode, 2)
        report = json.loads(result.stdout)
        self.assertEqual(report["decision"], "PASS")
        self.assertEqual(report["reason"], "MIGRATION_UNSUPPORTED_OR_UNINSPECTED_SOURCE")
        self.assertFalse(path.exists())
