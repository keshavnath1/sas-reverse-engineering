"""Public configurable migration and pinned legacy compatibility checks."""

from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
import unittest
import uuid

from test_review_workflow import ROOT, call, remove_destination


EXAMPLE = ROOT / "tests/fixtures/candidate-execution/projection-and-sort"
SCRIPT = ROOT / "scripts/migrate_projection_sort.py"


@unittest.skipUnless(sys.platform in ("darwin", "linux"), "Existing POSIX evidence workflow")
class ConfigurableMigrationTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.intake = self.root / "public-input"
        shutil.copytree(EXAMPLE / "public-input", self.intake)
        self.rows = self.root / "cases.json"
        shutil.copyfile(EXAMPLE / "CASES.json", self.rows)

    def destination(self, checkpoint):
        path = Path("/tmp") / f"sas-re-{checkpoint}-{uuid.uuid4().hex}"
        self.addCleanup(remove_destination, path)
        return path

    def package(self, intake):
        destination = self.destination("int1")
        result = call(destination, script=ROOT / "scripts/review_intake.py",
                      extra=("--intake", str(intake)))
        self.assertEqual(result.returncode, 0, result.stderr)
        return destination.resolve()

    def invoke(self, package, digest=None):
        destination = self.destination("mig2")
        result = call(destination, script=SCRIPT, extra=(
            "--intake", str(self.intake), "--package", str(package), "--rows", str(self.rows),
            "--rows-sha256", digest if digest is not None else sha256(self.rows.read_bytes()).hexdigest(),
        ))
        return result, destination

    def assert_refused(self, package, reason, digest=None):
        result, path = self.invoke(package, digest)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn(reason.encode(), result.stderr)
        self.assertFalse(path.exists())

    def test_different_identifiers_and_repeatable_typed_outputs(self):
        package = self.package(self.intake)
        snapshots = []
        for _ in range(2):
            result, path = self.invoke(package)
            self.assertEqual(result.returncode, 0, result.stderr)
            snapshots.append({item.name: item.read_bytes() for item in path.iterdir()})
        self.assertEqual(*snapshots)
        files = snapshots[0]
        plan = json.loads(files["PLAN.json"])
        self.assertEqual(plan["projection"]["columns"], ["score", "reading"])
        self.assertEqual(plan["handoff"]["dataset"], "work.projected")
        self.assertEqual(plan["handoff"]["classification"], "POTENTIAL")
        self.assertEqual(plan["handoff"]["execution_order"], "UNRESOLVED")
        observed = json.loads(files["ROWS.json"])
        self.assertEqual([row["reading"] for row in observed], [1, 1, 1, 3])
        self.assertEqual([type(row["score"]) for row in observed], [float, int, float, int])
        self.assertEqual(observed[0], observed[2])
        self.assertTrue(all(set(row) == {"score", "reading"} for row in observed))
        self.assertEqual(json.loads(files["VALIDATION.json"])["comparison"], "PASS")
        manifest = json.loads(files["MANIFEST.json"])
        self.assertEqual(manifest["semantic_acceptance"], "BLOCKED")
        self.assertEqual(manifest["input_rows"]["sha256"], sha256(self.rows.read_bytes()).hexdigest())
        for name, identity in manifest["files"].items():
            self.assertEqual(identity["sha256"], sha256(files[name]).hexdigest())

        cases = json.loads(self.rows.read_bytes())
        expected = cases.pop("expected")
        self.rows.write_text(json.dumps(cases), encoding="utf-8")
        result, path = self.invoke(package)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads((path / "VALIDATION.json").read_bytes())["comparison"], "NOT_RUN")
        cases["expected"] = expected[1:]
        self.rows.write_text(json.dumps(cases), encoding="utf-8")
        result, path = self.invoke(package)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads((path / "VALIDATION.json").read_bytes())["comparison"], "FAIL")

    def test_refuses_invalid_rows_and_forged_evidence(self):
        package = self.package(self.intake)
        self.assert_refused(package, "MIGRATION_ROWS_SHA256_MISMATCH", "0" * 64)
        cases = json.loads(self.rows.read_bytes())
        for row in ({"reading": 1}, {"reading": True, "score": 2, "annotation": ""},
                    {"reading": 1, "score": None, "annotation": ""}):
            with self.subTest(row=row):
                self.rows.write_text(json.dumps({**cases, "input": [row]}), encoding="utf-8")
                self.assert_refused(package, "MIGRATION_ROW_")
        self.rows.unlink()
        self.assert_refused(package, "FILE_NOT_FOUND", "0" * 64)
        shutil.copyfile(EXAMPLE / "CASES.json", self.rows)

        evidence = package / "SOURCE_2.json"
        raw = evidence.read_bytes() + b"\n"
        evidence.write_bytes(raw)
        path = package / "MANIFEST.json"
        manifest = json.loads(path.read_bytes())
        manifest["files"][evidence.name] = {"sha256": sha256(raw).hexdigest(), "bytes": len(raw)}
        path.write_text(json.dumps(manifest), encoding="utf-8")
        self.assert_refused(package, "MIGRATION_EVIDENCE_MISMATCH")

    def test_refuses_unimplemented_data_and_ambiguous_handoff(self):
        scope_path = self.intake / "scope.json"
        scope = json.loads(scope_path.read_bytes())
        for data, reason in (
            (b"data work.projected; set work.samples; score=score+1; keep score reading; run;\n",
             "MIGRATION_UNSUPPORTED_OR_UNINSPECTED_SOURCE"),
            (b"data work.projected; set work.sorted; keep score reading; run;\n",
             "MIGRATION_HANDOFF_UNRESOLVED_OR_AMBIGUOUS"),
        ):
            with self.subTest(reason=reason):
                (self.intake / "project.sas.txt").write_bytes(data)
                scope["sources"][0]["sha256"] = sha256(data).hexdigest()
                scope_path.write_text(json.dumps(scope), encoding="utf-8")
                self.assert_refused(self.package(self.intake), reason)

    def test_projection_manifest_binds_unchanged_fixture_and_relocated_code(self):
        package = self.package(ROOT / "tests/fixtures/source-reconstruction/agent-review/public-input")
        output = self.destination("mig1")
        result = call(output, script=ROOT / "scripts/migration_candidate.py",
                      extra=("--package", str(package)))
        self.assertEqual(result.returncode, 0, result.stderr)
        # Historical manifest 2b25ea6 remains bound to the pre-relocation code.
        # Only the candidate locator/code identity changed; input and case truth did not.
        manifest = json.loads((output / "MANIFEST.json").read_bytes())
        self.assertEqual(manifest["input_manifest_sha256"],
                         "8bfc638d5c4db4f60001010ee7abbb3db175c29f44696b0403c621fed953227a")
        self.assertEqual(manifest["files"]["CASES.json"]["sha256"],
                         "2377b8ea027a44f6f59c96f1f195d631988435278b8fd1997a0da52535fd787e")
        self.assertEqual(sha256((output / "MANIFEST.json").read_bytes()).hexdigest(),
                         "6d8acd03366865568e7906aa4aaac50d90022f10a794dac8ab5f2d2ffd5666d5")
