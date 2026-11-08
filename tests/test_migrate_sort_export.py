"""Public gate, full-record sorting and deterministic CSV checks."""

from copy import deepcopy
import csv
from hashlib import sha256
import io
import json
import runpy
import sys
import unittest

import test_migrate_preparation_gates as integration
from test_review_workflow import ROOT, call


SCRIPT = ROOT / "scripts/migrate_sort_export.py"


@unittest.skipUnless(sys.platform in ("darwin", "linux"), "Existing POSIX evidence workflow")
class ConditionalSortExportTests(unittest.TestCase):
    destination = integration.PreparationGateIntegrationTests.destination
    review = integration.PreparationGateIntegrationTests.review

    def test_public_gate_controls_export_and_manifest(self):
        prep = self.review("examples/mig3/preparation.sas.txt", "--lines", "1:12",
                           "--recover-status-rules", "--recover-missing-exclusions")
        pop = self.review("examples/mig4/population.sas.txt", "--lines", "1:1", "--lines", "14:14",
                          "--recover-sql-gates")
        args = ("--preparation-evidence", str(prep), "--population-evidence", str(pop))
        captures = []
        for scenario, decision, execution in (
            ("passes", "PROCEED", "EXECUTED"),
            ("passes", "PROCEED", "EXECUTED"),
            ("guard_disabled", "PROCEED", "EXECUTED"),
            ("empty", "BLOCK", "SKIPPED_BY_CANDIDATE_GATE"),
            ("duplicates", "BLOCK", "SKIPPED_BY_CANDIDATE_GATE"),
            ("count_mismatch", "BLOCK", "SKIPPED_BY_CANDIDATE_GATE"),
            ("invalid_identifier", "NOT_RUN", "SKIPPED_BY_INPUT_REFUSAL"),
        ):
            with self.subTest(scenario=scenario):
                destination = self.destination("mig6")
                result = call(destination, script=SCRIPT, extra=(*args, "--scenario", scenario))
                self.assertEqual(result.returncode, 0, result.stderr)
                files = {path.name: path.read_bytes() for path in destination.iterdir()}
                report = json.loads(files["SCENARIO_RESULT.json"])
                self.assertEqual((report["continuation"], report["downstream_execution"]),
                                 (decision, execution))
                self.assertEqual(json.loads(files["VALIDATION.json"])["comparison"], "PASS")
                manifest = json.loads(files["MANIFEST.json"])
                self.assertEqual(manifest["semantic_acceptance"], "BLOCKED")
                self.assertEqual(set(manifest["files"]), set(files) - {"MANIFEST.json"})
                self.assertEqual(files["PREPARATION_EVIDENCE.json"], prep.read_bytes())
                self.assertEqual(files["POPULATION_EVIDENCE.json"], pop.read_bytes())
                for name, item in manifest["files"].items():
                    self.assertEqual(item["sha256"], sha256(files[name]).hexdigest())
                downstream = {"SORTED_ROWS.json", "PREPARED_EXPORT.csv"}
                if decision == "PROCEED":
                    self.assertTrue(downstream <= files.keys())
                    records = json.loads(files["SORTED_ROWS.json"])
                    self.assertEqual([row["id"] for row in records], [0, 1])
                    self.assertTrue(all(len(row) == 19 and "case_id" not in row for row in records))
                    header = ["id", *(f"n{i}" for i in range(1, 13)),
                              *(f"c{i}" for i in range(1, 6)), "Default"]
                    rows = [[0, 0, *([1] * 11), ".   ", *(["X   "] * 4), 0],
                            [1, *([1] * 12), *(["X   "] * 5), 1]]
                    expected = "\n".join(",".join(map(str, row)) for row in [header, *rows]) + "\n"
                    self.assertEqual(files["PREPARED_EXPORT.csv"], expected.encode())
                else:
                    self.assertFalse(downstream & files.keys())
                if scenario == "duplicates":
                    self.assertEqual(report["handoff_ids"], [1, 1])
                if scenario == "passes":
                    captures.append(files)
        self.assertEqual(*captures)

    def test_adapter_stable_ties_preserve_fields_and_reject_bad_records(self):
        runner = runpy.run_path(str(SCRIPT))
        first = {"case_id": "D01", "id": 2, "numeric_group": [1] * 12,
                 "character_group": [{"text": ' ," '} for _ in range(5)], "default": 1}
        second = {**first, "case_id": "D02", "default": 0}
        earlier = {**first, "id": 1, "numeric_group": [-0.0, *([1] * 11)]}
        records = runner["sort_records"]([first, second, earlier, first])
        self.assertEqual([(row["id"], row["Default"]) for row in records],
                         [(1, 1), (2, 1), (2, 0), (2, 1)])
        parsed = list(csv.DictReader(io.StringIO(runner["csv_bytes"](records).decode())))
        self.assertEqual(parsed[0]["n1"], "-0.0")
        self.assertEqual(parsed[0]["c1"], ' ," ')
        for field, value in (("id", True), ("default", None), ("numeric_group", [None] * 12),
                             ("character_group", [{"text": "short?"}] * 5)):
            bad = deepcopy(first)
            bad[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                runner["sort_records"]([bad])
        with self.assertRaises(ValueError):
            runner["sort_records"]([{"id": 1}])
