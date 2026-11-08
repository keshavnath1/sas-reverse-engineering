"""Public design, fixed-score and gate checks for MOD-2."""

from copy import deepcopy
from hashlib import sha256
import json
import runpy
import sys
import unittest

import test_migrate_preparation_gates as integration
from test_review_workflow import ROOT, call


SCRIPT = ROOT / "scripts/score_prepared_logistic.py"
EXAMPLE = ROOT / "tests/fixtures/candidate-execution/fixed-logistic-scoring"
MODEL = EXAMPLE / "model.sas.txt"
COLUMNS = ["intercept", *(f"n{i}" for i in range(1, 13)), "c1:ALT", "c1:OTHER",
           "c2:ALT", "c3:ALT", "c4:ALT", "c5:ALT"]


@unittest.skipUnless(sys.platform in ("darwin", "linux"), "Existing POSIX evidence workflow")
class FixedLogisticScoringTests(unittest.TestCase):
    destination = integration.PreparationGateIntegrationTests.destination
    review = integration.PreparationGateIntegrationTests.review

    def test_public_pre_sort_scores_and_block_are_reproducible(self):
        prep = self.review("tests/fixtures/candidate-execution/preparation-rules/preparation.sas.txt", "--lines", "1:12",
                           "--recover-status-rules", "--recover-missing-exclusions")
        pop = self.review("tests/fixtures/candidate-execution/population-gates/population.sas.txt", "--lines", "1:1", "--lines", "14:14",
                          "--recover-sql-gates")
        args = ("--model-source", str(MODEL), "--model-source-sha256", sha256(MODEL.read_bytes()).hexdigest(),
                "--preparation-evidence", str(prep), "--population-evidence", str(pop))
        captures = []
        for scenario in ("passes", "passes", "duplicates"):
            destination = self.destination("mod2")
            result = call(destination, script=SCRIPT, extra=(*args, "--scenario", scenario))
            self.assertEqual(result.returncode, 0, result.stderr)
            files = {path.name: path.read_bytes() for path in destination.iterdir()}
            manifest = json.loads(files["MANIFEST.json"])
            self.assertEqual(manifest["fitting"], "NOT_RUN")
            self.assertEqual(manifest["semantic_acceptance"], "BLOCKED")
            self.assertEqual(set(manifest["files"]), set(files) - {"MANIFEST.json"})
            for name, value in manifest["files"].items():
                self.assertEqual(value["sha256"], sha256(files[name]).hexdigest())
            validation = json.loads(files["VALIDATION.json"])
            if scenario == "duplicates":
                self.assertEqual(set(files), {"PLAN.json", "VALIDATION.json", "MANIFEST.json"})
                self.assertEqual((validation["candidate_gate"], validation["scoring"]), ("BLOCK", "NOT_RUN"))
                continue
            self.assertEqual(validation["comparison"], "PASS")
            captures.append(files)
            design = json.loads(files["DESIGN.json"])
            self.assertEqual(design["columns"], COLUMNS)
            self.assertEqual([row["values"] for row in design["rows"]],
                             [[1] * 13 + [0] * 6, [1, 0] + [1] * 11 + [1, 0, 0, 0, 0, 0]])
            scores = json.loads(files["SCORES.json"])["rows"]
            self.assertEqual([(row["case_id"], row["id"], row["eta"]) for row in scores],
                             [("C01", 1, 1.5), ("C02", 0, 0.5)])
            self.assertAlmostEqual(scores[0]["phat"], 0.8175744761936437, delta=1e-15)
            self.assertAlmostEqual(scores[1]["phat"], 0.6224593312018546, delta=1e-15)
        self.assertEqual(*captures)

    def test_mapping_numeric_stability_and_refusals(self):
        runner = runpy.run_path(str(SCRIPT))
        raw = MODEL.read_bytes()
        _, model = runner["recover_model"](raw, sha256(raw).hexdigest())
        with self.assertRaisesRegex(ValueError, "MODEL_SOURCE_IDENTITY_REFUSED"):
            runner["recover_model"](raw + b"\n", sha256(raw).hexdigest())
        mapping = json.loads((EXAMPLE / "MAPPING.json").read_bytes())
        contract = runner["design_contract"](model, mapping)
        self.assertEqual(list(contract["numeric_source_to_public_slot"].items()),
                         [(f"x{i}", f"n{i}") for i in range(1, 13)])
        row = {"case_id": "T01", "id": 2, "default": 1, "numeric_group": list(range(1, 13)),
               "character_group": [{"text": alias} for alias in ("Z   ", "Z   ", "X   ", "X   ", "X   ")]}
        values = runner["encode_row"](row, contract)["values"]
        self.assertEqual(values, [1, *range(1, 13), 0, 1, 1, 0, 0, 0])
        for override in ({"default": True}, {"numeric_group": [None] * 12},
                         {"numeric_group": [float("inf")] * 12},
                         {"character_group": [{"text": "X"}] * 5}):
            with self.subTest(override=override), self.assertRaises(ValueError):
                runner["encode_row"]({**row, **override}, contract)
        mapping["levels"]["c1"].append(["X   ", "DUPLICATE"])
        with self.assertRaisesRegex(ValueError, "MODEL_CLASS_MAPPING_INVALID"):
            runner["design_contract"](model, mapping)
        spec = json.loads((EXAMPLE / "COEFFICIENTS.json").read_bytes())
        for replacement in (["n1", 0], ["intercept", float("nan")], ["unknown", 0]):
            wrong = deepcopy(spec)
            wrong["coefficients"][0] = replacement
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                runner["coefficients_for"](COLUMNS, wrong)
        with self.assertRaises(ValueError):
            runner["coefficients_for"](COLUMNS, {**spec, "coefficients": spec["coefficients"][1:]})
        self.assertEqual(runner["score"]([1], [1000]), (1000, 1))
        self.assertEqual(runner["score"]([1], [-1000]), (-1000, 0))
