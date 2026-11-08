"""Public end-to-end controls for the MIG-5 handoff and evidence pins."""

from hashlib import sha256
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
import uuid

from test_review_workflow import ROOT, call, remove_destination


SCRIPT = ROOT / "scripts/migrate_preparation_gates.py"


@unittest.skipUnless(sys.platform in ("darwin", "linux"), "Existing POSIX evidence workflow")
class PreparationGateIntegrationTests(unittest.TestCase):
    def destination(self, checkpoint):
        path = Path("/tmp") / f"sas-re-{checkpoint}-{uuid.uuid4().hex}"
        self.addCleanup(remove_destination, path)
        return path

    def review(self, fixture, *options):
        with TemporaryDirectory() as temp:
            source = Path(temp).resolve() / "public.sas"
            raw = (ROOT / fixture).read_bytes()
            source.write_bytes(raw)
            output = self.destination("source")
            result = call(output, script=ROOT / "scripts/review_source.py", extra=(
                "--source", str(source), "--source-sha256", sha256(raw).hexdigest(), *options,
            ))
        self.assertEqual(result.returncode, 0, result.stderr)
        return output.resolve() / "EVIDENCE.json"

    def test_integrated_outcomes_replay_and_refuse_changed_evidence(self):
        prep = self.review("examples/mig3/preparation.sas.txt", "--lines", "1:12",
                           "--recover-status-rules", "--recover-missing-exclusions")
        pop = self.review("examples/mig4/population.sas.txt", "--lines", "1:1", "--lines", "14:14",
                          "--recover-sql-gates")
        args = ("--preparation-evidence", str(prep), "--population-evidence", str(pop))
        copies = []
        for _ in range(2):
            output = self.destination("mig5")
            result = call(output, script=SCRIPT, extra=args)
            self.assertEqual(result.returncode, 0, result.stderr)
            copies.append({path.name: path.read_bytes() for path in output.iterdir()})
        self.assertEqual(*copies)
        files = copies[0]
        self.assertEqual(files["PREPARATION_EVIDENCE.json"], prep.read_bytes())
        self.assertEqual(files["POPULATION_EVIDENCE.json"], pop.read_bytes())
        manifest = json.loads(files["MANIFEST.json"])
        self.assertEqual(manifest["semantic_acceptance"], "BLOCKED")
        for name, item in manifest["files"].items():
            self.assertEqual(item["sha256"], sha256(files[name]).hexdigest())
        validation = json.loads(files["VALIDATION.json"])
        self.assertEqual([item["comparison"] for item in validation["scenarios"]], ["PASS"] * 6)
        runs = {item["scenario"]: item for item in json.loads(files["SCENARIO_RESULTS.json"])}
        self.assertEqual(runs["passes"]["handoff_ids"], [1, 0])
        self.assertEqual(runs["passes"]["preparation"]["summary"]["candidate_row_end_count"], 3)
        self.assertEqual(runs["empty"]["handoff_ids"], [])
        self.assertEqual(runs["duplicates"]["handoff_ids"], [1, 1])
        self.assertEqual(runs["duplicates"]["population"]["duplicate_groups"],
                         [{"id": 1, "duplicate_count": 2}])
        self.assertEqual(runs["count_mismatch"]["population"]["first_blocking_gate"], 5)
        self.assertEqual(runs["guard_disabled"]["population"]["gates"][4]["reason"], "OPTION_DISABLED")
        self.assertEqual(runs["invalid_identifier"]["population"], "NOT_RUN")
        self.assertTrue(all(run["sas_process_continuation"] == "UNOBSERVED" for run in runs.values()))

        for evidence in (prep, pop):
            original = evidence.read_bytes()
            evidence.write_bytes(original + b"\n")
            destination = self.destination("mig5")
            result = call(destination, script=SCRIPT, extra=args)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn(b"MIGRATION_EVIDENCE_MISMATCH", result.stderr)
            self.assertFalse(destination.exists())
            evidence.write_bytes(original)
