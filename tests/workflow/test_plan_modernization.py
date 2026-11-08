"""Modernization plans route reviewed public subjects without granting publication authority."""

from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from uuid import uuid4

from workflow.test_review_workflow import ROOT, call, remove_destination


@unittest.skipUnless(sys.platform in ("darwin", "linux"), "Existing POSIX evidence workflow")
class ModernizationPlanningTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(TemporaryDirectory())).resolve()
        self.intake = self.root / "INTAKE"
        shutil.copytree(
            ROOT / "tests/fixtures/candidate-execution/projection-and-sort/public-input",
            self.intake,
        )
        self.package = self.destination("int1")
        result = call(
            self.package,
            script=ROOT / "scripts/review_intake.py",
            extra=("--intake", str(self.intake), "--modernization-drafts"),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.package = self.package.resolve()

    def destination(self, stage):
        path = Path("/tmp") / f"sas-re-{stage}-{uuid4().hex}"
        self.addCleanup(remove_destination, path)
        return path

    def invoke(self, *extra, pinned=False):
        intake = [] if pinned else ["--intake", str(self.intake)]
        return subprocess.run(
            [
                sys.executable,
                "-IB",
                str(ROOT / "scripts/plan_modernization.py"),
                "--package",
                str(self.package),
                *intake,
                *extra,
            ],
            capture_output=True,
            timeout=60,
        )

    def reviewed(self, ordering="ASCENDING_KEY_STABLE_TIES", *, downstream=False, pinned=False):
        emitted = self.invoke("--emit-drafts", pinned=pinned)
        self.assertEqual(emitted.returncode, 0, emitted.stdout)
        drafts = json.loads(emitted.stdout)
        profile = drafts["migration-profile.yaml"]
        profile.update(
            status="REVIEWED",
            target={"runtime": "python", "distributed": False},
            execution={
                "multiplicity_policy": "PRESERVE",
                "ordering_policy": ordering,
                "category_policy": "PINNED_MOD2_MAPPING" if downstream else "NOT_APPLICABLE",
            },
        )
        tie_out = drafts["tie-out.yaml"]
        tie_out.update(
            status="REVIEWED",
            checks={
                "source_coverage": "REVIEWED",
                "population_and_multiplicity": "EXACT",
                "ordering_and_output": "EXACT",
                "numeric_tolerance": "PINNED_MOD2_TOLERANCE" if downstream else "EXACT",
            },
        )
        for name, config in drafts.items():
            (self.root / name).write_text(json.dumps(config), encoding="utf-8")
        return (
            "--profile",
            str(self.root / "migration-profile.yaml"),
            "--tie-out",
            str(self.root / "tie-out.yaml"),
        )

    def test_drafts_require_review_and_reviewed_mig2_replays_without_publication(self):
        before = {path.name: path.read_bytes() for path in self.package.iterdir()}
        pending = self.invoke()
        self.assertEqual(pending.returncode, 1, pending.stdout)
        report = json.loads(pending.stdout)
        self.assertIn("migration-profile.yaml:target.runtime", report["pending"])
        self.assertIn("tie-out.yaml:checks.numeric_tolerance", report["pending"])
        self.assertNotIn("plan", report)
        args = self.reviewed()
        planned = self.invoke(*args)
        self.assertEqual(planned.returncode, 0, planned.stdout)
        self.assertEqual(planned.stdout, self.invoke(*args).stdout)
        report = json.loads(planned.stdout)
        self.assertEqual(report["decision"], "PLAN_PROPOSED")
        self.assertEqual(report["plan"]["candidate"], "MIG-2")
        self.assertEqual(report["plan"]["handoff"]["execution_order"], "UNRESOLVED")
        self.assertEqual(report["reference_experiment"], "NOT_RUN")
        self.assertEqual(report["semantic_acceptance"], "BLOCKED")
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.package.iterdir()})

        destination = self.destination("intg1")
        rows = ROOT / "tests/fixtures/candidate-execution/projection-and-sort/CASES.json"
        result = call(
            destination,
            script=ROOT / "scripts/review_to_migration.py",
            extra=(
                "--intake",
                str(self.intake),
                "--package",
                str(self.package),
                "--rows",
                str(rows),
                "--rows-sha256",
                "0" * 64,
            ),
        )
        self.assertEqual(json.loads(result.stdout)["decision"], "REVIEW_REQUIRED")
        self.assertFalse(destination.exists())

    def test_rechecks_edited_policy_and_stale_binding(self):
        args = self.reviewed()
        path = self.root / "migration-profile.yaml"
        original = path.read_bytes()
        for section, field, value in (
            ("target", "runtime", "spark"),
            ("execution", "ordering_policy", "EXPORT_ASCENDING_ID_SCORE_ORIGINAL_PRE_SORT"),
            ("binding", "manifest_sha256", "0" * 64),
        ):
            with self.subTest(field=field):
                config = json.loads(original)
                config[section][field] = value
                path.write_text(json.dumps(config), encoding="utf-8")
                rejected = self.invoke(*args)
                self.assertEqual(rejected.returncode, 2, rejected.stdout)
                report = json.loads(rejected.stdout)
                self.assertNotIn("plan", report)
                if section == "binding":
                    self.assertEqual(report["reason"], "CONFIGURATION_BINDING_MISMATCH")
                else:
                    self.assertEqual(
                        report["refusals"][0]["field"], f"migration-profile.yaml:{section}.{field}"
                    )
        path.write_bytes(original)
        self.assertEqual(self.invoke(*args).returncode, 0)

    def test_replays_source_and_evidence_identities(self):
        args = self.reviewed()
        for path, reason in (
            (self.intake / "project.sas.txt", "SOURCE_SHA256_MISMATCH"),
            (self.package / "SOURCE_1.json", "MIGRATION_EVIDENCE_MISMATCH"),
        ):
            with self.subTest(path=path.name):
                original = path.read_bytes()
                path.write_bytes(original + b"\n")
                result = self.invoke(*args)
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertEqual(json.loads(result.stdout)["reason"], reason)
                path.write_bytes(original)

    def test_other_valid_intake_scope_has_no_candidate_plan(self):
        self.intake = ROOT / "tests/fixtures/source-reconstruction/intake-sources"
        destination = self.destination("int1")
        result = call(
            destination,
            script=ROOT / "scripts/review_intake.py",
            extra=("--intake", str(self.intake), "--modernization-drafts"),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.package = destination.resolve()
        result = self.invoke()
        self.assertEqual(result.returncode, 2, result.stdout)
        report = json.loads(result.stdout)
        self.assertEqual(report["reason"], "MIGRATION_TWO_SOURCE_PACKAGE_REQUIRED")
        self.assertNotIn("plan", report)

    def test_pinned_subjects_keep_separate_candidate_routes(self):
        for scenario, candidate, order in (
            (None, "MIG-5", "ORIGINAL_INPUT_ORDER"),
            ("passes", "MIG-5/MIG-6/MOD-2", "EXPORT_ASCENDING_ID_SCORE_ORIGINAL_PRE_SORT"),
        ):
            with self.subTest(scenario=scenario):
                destination = self.destination("intg3a")
                cmd = [
                    sys.executable,
                    "-IB",
                    str(ROOT / "scripts/review_mig5.py"),
                    "prepare",
                    "--destination",
                    str(destination),
                ]
                if scenario:
                    cmd.extend(("--scenario", scenario))
                prepared = subprocess.run(cmd, capture_output=True, timeout=60)
                self.assertEqual(prepared.returncode, 0, prepared.stdout)
                self.package = destination.resolve()
                args = self.reviewed(order, downstream=scenario is not None, pinned=True)
                result = self.invoke(*args, pinned=True)
                self.assertEqual(result.returncode, 0, result.stdout)
                self.assertEqual(json.loads(result.stdout)["plan"]["candidate"], candidate)
                if scenario:
                    args = self.reviewed("ASCENDING_KEY_STABLE_TIES", downstream=True, pinned=True)
                    rejected = self.invoke(*args, pinned=True)
                    self.assertEqual(rejected.returncode, 2, rejected.stdout)
                    self.assertNotIn("plan", json.loads(rejected.stdout))


def configured_arguments(test, package, root, *, intake=None):
    """Prepare reviewed fixture bytes through the planner's CLI."""
    prefix = [
        sys.executable,
        "-IB",
        str(ROOT / "scripts/plan_modernization.py"),
        "--package",
        str(package),
    ]
    if intake is not None:
        prefix.extend(("--intake", str(intake)))

    def run(*args):
        return subprocess.run([*prefix, *args], capture_output=True, timeout=60)

    drafts = json.loads(run("--emit-drafts").stdout)
    profile, tie_out = root / "profile.yaml", root / "tie-out.yaml"
    args = ("--profile", str(profile), "--tie-out", str(tie_out))
    names = {"migration-profile.yaml": profile, "tie-out.yaml": tie_out}
    for name, path in names.items():
        path.write_text(json.dumps(drafts[name]), encoding="utf-8")
    pending = run(*args)
    test.assertEqual(pending.returncode, 1, pending.stdout)
    for name, choices in json.loads(pending.stdout)["supported_operator_policy"].items():
        drafts[name].update(status="REVIEWED", **choices)
        names[name].write_text(json.dumps(drafts[name]), encoding="utf-8")
    plan = root / "plan.json"

    def replan():
        result = run(*args)
        test.assertEqual(result.returncode, 0, result.stdout)
        plan.write_bytes(result.stdout)
        return {
            "plan": {"bytes": len(result.stdout), "sha256": sha256(result.stdout).hexdigest()},
            "configuration_inputs": json.loads(result.stdout)["configuration_inputs"],
        }

    return (*args, "--modernization-plan", str(plan)), replan
