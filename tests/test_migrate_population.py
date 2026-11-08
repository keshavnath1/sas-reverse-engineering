"""Public engineering controls for SQL-2 population and gate binding."""

from hashlib import sha256
import json
from pathlib import Path
import runpy
import sys
from tempfile import TemporaryDirectory
import unittest
import uuid

from test_review_workflow import ROOT, call, remove_destination


SCRIPT = ROOT / "scripts/migrate_population.py"


@unittest.skipUnless(sys.platform in ("darwin", "linux"), "Existing POSIX evidence workflow")
class PopulationMigrationTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.source = Path(temp.name).resolve() / "population.sas"
        self.source.write_bytes((ROOT / "tests/fixtures/candidate-execution/population-gates/population.sas.txt").read_bytes())
        self.digest = sha256(self.source.read_bytes()).hexdigest()

    def destination(self, checkpoint):
        path = Path("/tmp") / f"sas-re-{checkpoint}-{uuid.uuid4().hex}"
        self.addCleanup(remove_destination, path)
        return path

    def review(self):
        package = self.destination("source")
        run = call(package, script=ROOT / "scripts/review_source.py", extra=(
            "--source", str(self.source), "--source-sha256", self.digest,
            "--lines", "1:1", "--lines", "14:14", "--recover-sql-gates",
        ))
        self.assertEqual(run.returncode, 0, run.stderr)
        return package.resolve()

    def invoke(self, review, *extra):
        destination = self.destination("mig4")
        return call(destination, script=SCRIPT, extra=(
            "--source", str(self.source), "--source-sha256", self.digest,
            "--evidence", str(review / "EVIDENCE.json"), *extra,
        )), destination

    def test_population_decisions_and_source_citations_are_deterministic(self):
        review = self.review()
        original = {p.name: p.read_bytes() for p in review.iterdir()}
        runs = []
        for _ in range(2):
            result, destination = self.invoke(review)
            self.assertEqual(result.returncode, 0, result.stderr)
            runs.append({p.name: p.read_bytes() for p in destination.iterdir()})
        self.assertEqual(*runs)
        files = runs[0]
        validation = json.loads(files["VALIDATION.json"])
        self.assertEqual(validation["comparison"], "PASS")
        self.assertEqual(len(validation["cases"]), 8)
        self.assertEqual(validation["semantic_acceptance"], "BLOCKED")
        population = {case["case_id"]: case for case in json.loads(files["POPULATION.json"])}
        self.assertEqual(population["two_groups"]["statistics"]["duplicate_ids"], 2)
        self.assertEqual(population["two_groups"]["duplicate_groups"][1]["duplicate_count"], 3)
        overlap = population["overlap"]
        self.assertEqual([gate["status"] for gate in overlap["gates"]],
                         ["EVALUATED", "EVALUATED", "NOT_EVALUATED", "NOT_EVALUATED", "NOT_EVALUATED"])
        self.assertEqual(overlap["optional_guard"]["reason"], "EARLIER_BLOCK")
        self.assertEqual(population["distinct"]["gates"][4]["reason"], "OPTION_DISABLED")
        self.assertEqual(population["expected_match"]["continuation"], "PROCEED")
        self.assertEqual(population["expected_mismatch"]["first_blocking_gate"], 5)
        evidence = json.loads(original["EVIDENCE.json"])
        for case in population.values():
            for event in [*case["gates"], case["optional_guard"]]:
                source = event["source"]
                index = int(source["evidence_pointer"].rsplit("/", 1)[1])
                self.assertEqual(source["span"], evidence["interval_effects"]["findings"][index]["span"])
                self.assertIn(f'id="{source["anchor"]}"'.encode(), original["MIGRATION_REVIEW.md"])
        self.assertEqual({p.name: p.read_bytes() for p in review.iterdir()}, original)

    def test_refuses_invalid_ids_and_changed_gate_evidence(self):
        review = self.review()
        runner = runpy.run_path(str(SCRIPT))
        plan = runner["bind_plan"](self.source.read_bytes(), self.digest,
                                   (review / "EVIDENCE.json").read_bytes())
        for value in (True, 1.0, None, "1", 2**53 + 1, {"tag":".AB"}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                runner["evaluate"](plan, [value], "N", None)
        with self.assertRaises(ValueError):
            runner["evaluate"](plan, [1], "Y", None)

        self.source.write_bytes(self.source.read_bytes().replace(b"&missing_ids ne 0", b"&missing_ids = 0"))
        result, output = self.invoke(review)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn(b"MIGRATION_SOURCE_SHA256_MISMATCH", result.stderr)
        self.assertFalse(output.exists())
        self.digest = sha256(self.source.read_bytes()).hexdigest()
        for package, diagnostic in ((review, b"MIGRATION_EVIDENCE_MISMATCH"),
                                    (self.review(), b"MIGRATION_SQL_GATE_CONTRACT_UNSUPPORTED")):
            result, output = self.invoke(package)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn(diagnostic, result.stderr)
            self.assertFalse(output.exists())
