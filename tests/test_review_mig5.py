"""Exercise the approval boundary on the pinned public MIG-5 subject."""

from hashlib import sha256
import csv
import io
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from uuid import uuid4

from test_review_workflow import ROOT, call, remove_destination


SCRIPT = ROOT / "scripts/review_mig5.py"
PREP = "PREPARATION_EVIDENCE.json"
POP = "POPULATION_EVIDENCE.json"


@unittest.skipUnless(sys.platform in ("darwin", "linux"), "Existing POSIX evidence workflow")
class Mig5OperatorTests(unittest.TestCase):
    def destination(self, stage="intg3a"):
        path = Path("/tmp") / f"sas-re-{stage}-{uuid4().hex}"
        self.addCleanup(remove_destination, path)
        return path

    def run_operator(self, mode, destination, *args):
        result = subprocess.run([sys.executable, "-IB", str(SCRIPT), mode, "--destination",
                                 str(destination), *map(str, args)], capture_output=True, timeout=60)
        return result.returncode, json.loads(result.stdout)

    def setUp(self):
        root = Path(self.enterContext(TemporaryDirectory())).resolve()
        self.record = root / "claims.json"
        self.approval = root / "approval.json"
        self.package = self.prepare()
        evidence = json.loads((self.package / POP).read_bytes())
        index = next(i for i, item in enumerate(evidence["interval_effects"]["findings"])
                     if "sql_declaration" in item)
        statements = (
            ("reconstruction", "The first preparation rule tests status membership.", "SOURCE_DECLARED", PREP,
             "/declared_operation/status_rule_recovery/rules/0/predicate"),
            ("prd", "The population fragment declares a duplicate audit.", "SOURCE_DECLARED", POP,
             f"/interval_effects/findings/{index}/sql_declaration"),
            ("dependency_analysis", "SAS dataset continuity is unresolved.", "UNRESOLVED",
             "MANIFEST.json", "/sas_dataset_continuity"),
            ("verification_plan", "Behavioral evidence is unavailable.", "PACKAGE_METADATA",
             "MANIFEST.json", "/behavioral_evidence"),
            ("adr", "The public route runs the pinned scenario suite.", "PACKAGE_METADATA",
             "MANIFEST.json", "/scenario"),
        )
        self.claims = {
            "version": 1,
            "manifest_sha256": sha256((self.package / "MANIFEST.json").read_bytes()).hexdigest(),
            "deliverables": {name: {"Review": text} for name, text, *_ in statements},
            "claims": [
                {"id": name, "text": text, "classification": classification, "deliverable": name,
                 "section": "Review", "disposition": "APPROVED",
                 "evidence": [{"file": file, "pointer": pointer}]}
                for name, text, classification, file, pointer in statements
            ],
        }
        self.approve()

    def approve(self):
        self.record.write_text(json.dumps(self.claims), encoding="utf-8")
        self.approval.write_text(json.dumps({
            "record_sha256": sha256(self.record.read_bytes()).hexdigest(),
            "reviewer": "Synthetic test reviewer", "decision": "APPROVED",
        }), encoding="utf-8")

    def prepare(self, scenario=None):
        path = self.destination()
        args = ("--scenario", scenario) if scenario is not None else ()
        status, report = self.run_operator("prepare", path, *args)
        self.assertEqual(status, 0, report)
        return path.resolve()

    def proceed(self, approved=True):
        path = self.destination()
        args = ["--package", self.package, "--record", self.record]
        if approved:
            args.extend(("--approval", self.approval))
        status, report = self.run_operator("continue", path, *args)
        return status, report, path

    def assert_refused(self, status, decision, code, *, approved=True):
        observed, report, path = self.proceed(approved)
        self.assertEqual(observed, status, report)
        self.assertEqual(report["decision"], decision)
        self.assertIn(code, [item["code"] for item in report.get("blocks", []) + report.get("pending", [])])
        self.assertFalse(path.exists())

    def test_approval_binding_and_refusal(self):
        self.assert_refused(1, "REVIEW_REQUIRED", "BOUND_HUMAN_APPROVAL_REQUIRED", approved=False)
        self.record.write_bytes(self.record.read_bytes() + b"\n")
        self.assert_refused(1, "REVIEW_REQUIRED", "BOUND_HUMAN_APPROVAL_REQUIRED")
        self.claims["deliverables"]["adr"]["Review"] += " Traced the declared handoff."
        self.approve()
        self.assert_refused(2, "BLOCK", "DECLARED_HANDOFF")
        self.claims["deliverables"]["adr"]["Review"] = "The public route runs the pinned scenario suite."
        claim = self.claims["claims"][1]
        claim.update(classification="PACKAGE_METADATA",
                     evidence=[{"file": "MANIFEST.json", "pointer": "/scenario"}])
        self.approve()
        self.assert_refused(1, "REVIEW_REQUIRED", "PINNED_EVIDENCE_CLAIM_REQUIRED")

    def test_evidence_cannot_be_changed_removed_or_rebound(self):
        for name in (PREP, POP):
            with self.subTest(name=name):
                evidence = self.package / name
                raw = evidence.read_bytes()
                evidence.write_bytes(raw + b"\n")
                self.assert_refused(2, "BLOCK", "REVIEW_PACKAGE_PAYLOAD_MISMATCH")
                evidence.unlink()
                self.assert_refused(2, "BLOCK", "FILE_NOT_FOUND")
                evidence.write_bytes(raw)

        manifest_path = self.package / "MANIFEST.json"
        manifest = json.loads(manifest_path.read_bytes())
        raw = (self.package / PREP).read_bytes() + b"\n"
        (self.package / PREP).write_bytes(raw)
        manifest["files"][PREP] = {"sha256": sha256(raw).hexdigest(), "bytes": len(raw)}
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        self.claims["manifest_sha256"] = sha256(manifest_path.read_bytes()).hexdigest()
        self.approve()
        self.assert_refused(2, "BLOCK", "REVIEW_MANIFEST_SHA256_MISMATCH")

    def test_publication_replays_and_preserves_standalone_mig5(self):
        def snapshot(path):
            return {item.name: item.read_bytes() for item in path.iterdir()}

        subject = snapshot(self.package)
        self.assertEqual(subject, snapshot(self.prepare()))
        copies = []
        for _ in range(2):
            status, report, path = self.proceed()
            self.assertEqual(status, 0, report)
            self.assertEqual((report["decision"], report["migration"], report["comparison"]),
                             ("PASS", "PUBLISHED", "PASS"))
            copies.append(snapshot(path))
        self.assertEqual(*copies)
        files = copies[0]
        self.assertEqual(subject, snapshot(self.package))
        output = self.destination("mig5")
        result = call(output, script=ROOT / "scripts/migrate_preparation_gates.py", extra=(
            "--preparation-evidence", str(self.package / PREP),
            "--population-evidence", str(self.package / POP),
        ))
        self.assertEqual(result.returncode, 0, result.stderr)
        for name, raw in snapshot(output).items():
            self.assertEqual(files["CANDIDATE_MANIFEST.json" if name == "MANIFEST.json" else name], raw)
        runs = {row["scenario"]: row for row in json.loads(files["SCENARIO_RESULTS.json"])}
        self.assertEqual(runs["passes"]["continuation"], "PROCEED")
        self.assertEqual(runs["duplicates"]["continuation"], "BLOCK")
        self.assertEqual(runs["duplicates"]["population"]["duplicate_groups"],
                         [{"id": 1, "duplicate_count": 2}])
        self.assertNotIn("PREPARED_EXPORT.csv", files)
        self.assertNotIn("SCORES.json", files)
        manifest = json.loads(files["MANIFEST.json"])
        self.assertEqual(manifest["semantic_acceptance"], "BLOCKED")
        self.assertEqual(manifest["input_manifest_sha256"], self.claims["manifest_sha256"])
        self.assertEqual(manifest["reviewer_approval"]["sha256"], sha256(self.approval.read_bytes()).hexdigest())
        for name, identity in manifest["files"].items():
            self.assertEqual(identity["sha256"], sha256(files[name]).hexdigest())

    def select_scenario(self, scenario):
        self.package = self.prepare(scenario)
        self.claims["manifest_sha256"] = sha256((self.package / "MANIFEST.json").read_bytes()).hexdigest()
        claims = self.claims["claims"]
        if not any(claim["id"] == "model" for claim in claims):
            text = "The public model declares the Default response."
            self.claims["deliverables"]["reconstruction"]["Review"] += "\n" + text
            claims.append({"id": "model", "text": text, "classification": "SOURCE_DECLARED",
                           "deliverable": "reconstruction", "section": "Review",
                           "disposition": "APPROVED", "evidence": [{
                               "file": "MODEL_EVIDENCE.json",
                               "pointer": "/declared_operation/model/response",
                           }]})
        self.approve()

    def test_downstream_proceeds_and_replays_from_original_order(self):
        self.select_scenario("passes")
        outputs = []
        for _ in range(2):
            status, report, destination = self.proceed()
            self.assertEqual(status, 0, report)
            self.assertEqual((report["decision"], report["comparison"]), ("PASS", "PASS"))
            outputs.append({path.name: path.read_bytes() for path in destination.iterdir()})
        self.assertEqual(*outputs)
        files = outputs[0]
        manifest = json.loads(files["MANIFEST.json"])
        self.assertEqual(set(manifest["files"]), files.keys() - {"MANIFEST.json"})
        for name, expected in manifest["files"].items():
            self.assertEqual(expected, {"sha256": sha256(files[name]).hexdigest(),
                                        "bytes": len(files[name])})
        rows = json.loads(files["SORTED_ROWS.json"])
        self.assertEqual([row["id"] for row in rows], [0, 1])
        expected_columns = {"id", "Default", *(f"n{i}" for i in range(1, 13)),
                            *(f"c{i}" for i in range(1, 6))}
        self.assertTrue(all(row.keys() == expected_columns for row in rows))
        csv_rows = list(csv.DictReader(io.StringIO(files["PREPARED_EXPORT.csv"].decode())))
        self.assertEqual(csv_rows, [{key: str(value) for key, value in row.items()} for row in rows])
        self.assertEqual([row["id"] for row in json.loads(files["DESIGN.json"])["rows"]], [1, 0])
        scores = json.loads(files["SCORES.json"])["rows"]
        self.assertEqual([(row["case_id"], row["id"], row["eta"]) for row in scores],
                         [("C01", 1, 1.5), ("C02", 0, 0.5)])
        self.assertEqual(json.loads(files["SCORING_VALIDATION.json"])["comparison"], "PASS")
        self.assertEqual(json.loads(files["EXPORT_VALIDATION.json"])["comparison"], "PASS")

    def test_downstream_block_publishes_only_upstream_diagnostics(self):
        scenarios = (
            ("empty", "BLOCK", 1),
            ("duplicates", "BLOCK", 3),
            ("count_mismatch", "BLOCK", 5),
            ("invalid_identifier", "NOT_RUN", None),
        )
        for scenario, continuation, blocking_gate in scenarios:
            with self.subTest(scenario=scenario):
                self.select_scenario(scenario)
                status, report, destination = self.proceed()
                self.assertEqual(status, 0, report)
                self.assertEqual((report["decision"], report["comparison"]), ("PASS", "PASS"))
                files = {path.name for path in destination.iterdir()}
                self.assertEqual(files, {"PREPARATION_EVIDENCE.json", "POPULATION_EVIDENCE.json",
                                         "PLAN.json", "SCENARIO_RESULTS.json", "VALIDATION.json",
                                         "CANDIDATE_MANIFEST.json", "GATE.json", "MANIFEST.json"})
                runs = json.loads((destination / "SCENARIO_RESULTS.json").read_bytes())
                selected = next(run for run in runs if run["scenario"] == scenario)
                self.assertEqual(selected["continuation"], continuation)
                if blocking_gate is not None:
                    self.assertEqual(selected["population"]["first_blocking_gate"], blocking_gate)
                manifest = json.loads((destination / "MANIFEST.json").read_bytes())
                self.assertEqual(manifest["scenario"], scenario)
                self.assertEqual(manifest["reference_experiment"], "NOT_RUN")
                self.assertEqual(manifest["semantic_acceptance"], "BLOCKED")

    def test_disabled_expected_count_guard_allows_both_branches(self):
        self.select_scenario("guard_disabled")
        status, report, destination = self.proceed()
        self.assertEqual(status, 0, report)
        self.assertEqual((report["decision"], report["comparison"]), ("PASS", "PASS"))
        rows = json.loads((destination / "SORTED_ROWS.json").read_bytes())
        scores = json.loads((destination / "SCORES.json").read_bytes())["rows"]
        self.assertEqual([row["id"] for row in rows], [0, 1])
        self.assertEqual([row["id"] for row in scores], [1, 0])

    def test_downstream_subject_requires_model_claim_and_exact_fixture_bytes(self):
        self.select_scenario("passes")
        self.assert_refused(1, "REVIEW_REQUIRED", "BOUND_HUMAN_APPROVAL_REQUIRED", approved=False)
        self.record.write_bytes(self.record.read_bytes() + b"\n")
        self.assert_refused(1, "REVIEW_REQUIRED", "BOUND_HUMAN_APPROVAL_REQUIRED")
        adr = self.claims["deliverables"]["adr"]
        original = adr["Review"]
        adr["Review"] += " Traced the declared handoff."
        self.approve()
        self.assert_refused(2, "BLOCK", "DECLARED_HANDOFF")
        adr["Review"] = original
        model = self.claims["claims"].pop()
        self.approve()
        self.assert_refused(1, "REVIEW_REQUIRED", "PINNED_EVIDENCE_CLAIM_REQUIRED")
        self.claims["claims"].append(model)
        self.approve()
        for name in ("MAPPING.json", "COEFFICIENTS.json"):
            with self.subTest(name=name):
                path = self.package / name
                raw = path.read_bytes()
                path.write_bytes(raw + b"\n")
                self.assert_refused(2, "BLOCK", "REVIEW_PACKAGE_PAYLOAD_MISMATCH")
                path.write_bytes(raw)
        self.package = self.prepare("duplicates")
        self.assert_refused(2, "BLOCK", "REVIEW_MANIFEST_SHA256_MISMATCH")
