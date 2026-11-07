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
            self.assertEqual(sha256(package["MANIFEST.json"]).hexdigest(),
                             "614ced69bb71885cc4e95687983b76de777f653913ebccf7163bb73b86718a5a")
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

    def configurable_fixture(self, root):
        lines = [
            b"%outside_scope;", b"data work.staged; set work.incoming;",
            b"if score < 0 then delete;", b"keep id score; run;",
            b"proc sql; select count(*) into :total trimmed from work.staged; quit;",
            b"%if &total = 0 %then %abort_run(empty);",
            b"proc sort data=work.staged out=work.result; by id; run;",
            b"%outside_scope;",
        ]
        raw = b"\r\n".join(lines) + b"\r\n"
        note = b"Public synthetic scope description.\n"
        (root / "different.sas.txt").write_bytes(raw)
        (root / "context.md").write_bytes(note)
        scope = {
            "version": 1, "scope": "public-synthetic", "mode": "data-sort-sql",
            "sources": [{"path": "different.sas.txt", "sha256": sha256(raw).hexdigest(),
                         "ranges": [[2, 4], [7, 7]]}],
            "supporting": [{"path": "context.md", "sha256": sha256(note).hexdigest(), "role": "note"}],
        }
        (root / "scope.json").write_text(json.dumps(scope))
        return scope, raw, lines

    def test_configurable_pair_has_deterministic_coverage_and_verified_support(self):
        with TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            scope, raw, lines = self.configurable_fixture(root)
            packages = []
            for _ in range(2):
                run, dest = self.invoke(root)
                self.assertEqual(run.returncode, 0, run.stderr)
                packages.append({p.name: p.read_bytes() for p in dest.iterdir()})
            self.assertEqual(*packages)
            evidence = json.loads(packages[0]["EVIDENCE.json"])
            manifest = json.loads(packages[0]["MANIFEST.json"])
            self.assertEqual(evidence["source"]["sha256"], sha256(raw).hexdigest())
            self.assertEqual(evidence["syntax_recognition"], "PARTIAL")
            self.assertEqual(manifest["inputs"]["context.md"]["inspection"], "IDENTITY_ONLY")
            self.assertEqual(manifest["inputs"]["context.md"]["sha256"], scope["supporting"][0]["sha256"])
            coverage = manifest["coverage"]
            self.assertEqual([part["kind"] for part in coverage], [
                "UNINSPECTED", "SELECTED_SOURCE_REVIEW", "BOUNDED_INTERVAL_INVENTORY",
                "SELECTED_SOURCE_REVIEW", "UNINSPECTED",
            ])
            self.assertEqual(coverage[0]["end"], len(lines[0]) + 2)
            self.assertEqual(coverage[-1]["end"], len(raw))
            self.assertEqual([p["end"] for p in coverage[:-1]], [p["start"] for p in coverage[1:]])
            self.assertEqual(evidence["connection"]["classification"], "SOURCE_DECLARED")
            self.assertEqual(evidence["connection"]["execution_verification"], "EXECUTION_UNVERIFIED")
            self.assertEqual(manifest["semantic_acceptance"], "BLOCKED")

    def test_configurable_refuses_invalid_scopes_and_file_changes(self):
        def set_source(scope, key, value):
            scope["sources"][0][key] = value

        cases = [
            (lambda s, _: s.update(version=2), b"INTAKE_MANIFEST_VERSION_UNSUPPORTED"),
            (lambda s, _: s.update(mode="execute"), b"INTAKE_REVIEW_MODE_UNSUPPORTED"),
            (lambda s, _: s.update(mode="sort"), b"INTAKE_RANGES_INVALID_FOR_MODE"),
            (lambda s, _: s["sources"].append(s["sources"][0]), b"INTAKE_MULTIPLE_SOURCES_UNSUPPORTED"),
            (lambda s, _: set_source(s, "path", "../other.sas"), b"UNSAFE_PATH"),
            (lambda s, _: set_source(s, "ranges", [[2, 4], [99, 99]]), b"LINE_RANGE_OUTSIDE_SOURCE"),
            (lambda s, p: (p / "different.sas.txt").write_bytes(b"changed"), b"SOURCE_SHA256_MISMATCH"),
            (lambda s, p: (p / "context.md").write_bytes(b"changed"), b"SUPPORT_SHA256_MISMATCH"),
            (lambda s, p: (p / "context.md").unlink(), b"INTAKE_FILE_SET_MISMATCH"),
            (lambda s, p: (p / "extra.txt").write_bytes(b"extra"), b"INTAKE_FILE_SET_MISMATCH"),
        ]
        for change, reason in cases:
            with self.subTest(reason=reason), TemporaryDirectory() as temp:
                root = Path(temp).resolve()
                scope, _, _ = self.configurable_fixture(root)
                change(scope, root)
                (root / "scope.json").write_text(json.dumps(scope))
                run, dest = self.invoke(root)
                self.assertEqual(run.returncode, 2, run.stderr)
                self.assertIn(reason, run.stderr)
                self.assertFalse(dest.exists())

    def test_single_range_reuses_review_and_reports_unsupported_syntax(self):
        with TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            scope, _, _ = self.configurable_fixture(root)
            scope["mode"] = "sort"
            scope["sources"][0]["ranges"] = [[7, 7]]
            (root / "scope.json").write_text(json.dumps(scope))
            run, dest = self.invoke(root)
            self.assertEqual(run.returncode, 0, run.stderr)
            evidence = json.loads((dest / "EVIDENCE.json").read_bytes())
            self.assertEqual(evidence["declared_operation"]["ordering_keys"], ["id"])
            self.assertIn("Declared dependency map", (dest / "README.md").read_text())
            scope["sources"][0]["ranges"] = [[1, 1]]
            (root / "scope.json").write_text(json.dumps(scope))
            run, dest = self.invoke(root)
            self.assertEqual(run.returncode, 2)
            evidence = json.loads((dest / "EVIDENCE.json").read_bytes())
            self.assertEqual(evidence["syntax_recognition"], "UNSUPPORTED")
            self.assertIn("MACRO_MARKER_OUTSIDE_SCOPE", evidence["reason_codes"])
