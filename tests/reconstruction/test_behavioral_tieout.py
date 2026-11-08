"""Independent behavioral tieout controls distinguish ordering, multiplicity, and numeric boundaries."""

from collections import Counter
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from mvp2_expectations import INPUTS
from mvp3_cases import CASES, FIXTURES, FINAL_TIE_WITNESS


from support.paths import REPOSITORY_ROOT as ROOT

SCRIPT = ROOT / "scripts/mvp3_tieout.py"


def numeric_row(row):
    return tuple(None if cell == "." else Decimal(cell) for cell in row)


class BehavioralTieoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.oracle = runpy.run_path(str(SCRIPT))
        cls.report = cls.oracle["build_report"]()
        cls.by_id = {case["case_id"]: case for case in cls.report["cases"]}

    def differences(self, expected, observed):
        return self.oracle["discrepancies"](expected, observed)

    def test_frozen_table_and_input_identity(self):
        spec = ROOT / "tests/mvp3_cases.py"
        self.assertEqual(
            hashlib.sha256(spec.read_bytes()).hexdigest(),
            "7ca4c6b50cdc7f5b7ce2ee422f5adfe883dba82a39b064140fba2d7a70702342",
        )
        original = {name: rows for name, _, _, rows in INPUTS}
        self.assertEqual(FIXTURES["mvp2"]["observations"], original["work.observations"])
        self.assertEqual(FIXTURES["mvp2"]["offsets"], original["work.offsets"])
        graph_hash = "19f41dea50825469a89d8fc545fee1d87f09af946d130d62de8f946d90b78017"
        self.assertIn(graph_hash, json.dumps(self.report))
        self.assertIn(
            graph_hash,
            (
                ROOT / "tests/fixtures/source-reconstruction/dependency-aware-preview/EVIDENCE.md"
            ).read_text(),
        )

    def test_changed_source_cannot_be_reported_as_the_historical_subject(self):
        with tempfile.TemporaryDirectory() as tmp:
            scratch = Path(tmp)
            (scratch / "scripts").mkdir()
            (scratch / "tests").mkdir()
            shutil.copyfile(SCRIPT, scratch / "scripts" / SCRIPT.name)
            shutil.copytree(
                ROOT / "tests/fixtures/source-reconstruction/dependency-aware-preview",
                scratch / "tests/fixtures/source-reconstruction/dependency-aware-preview",
            )
            for name in ("mvp2_expectations.py", "mvp3_cases.py"):
                shutil.copyfile(ROOT / "tests" / name, scratch / "tests" / name)
            command = [
                sys.executable,
                "-IBS",
                scratch / "scripts" / SCRIPT.name,
                "--case",
                "B01-published-workflow",
            ]
            control = subprocess.run(command, cwd=scratch, capture_output=True, timeout=30)
            self.assertEqual(control.returncode, 0, control.stderr)
            individual = json.loads(control.stdout)
            self.assertEqual(
                [c["case_id"] for c in individual["cases"]], ["B01-published-workflow"]
            )
            self.assertEqual(set(individual["inputs"]), {"mvp2"})
            source = scratch / "tests/mvp2_expectations.py"
            raw = source.read_bytes()
            self.assertEqual(raw.count(b"scaled = value / 2"), 1)
            source.write_bytes(raw.replace(b"scaled = value / 2", b"scaled = value / 3"))
            altered = subprocess.run(command, cwd=scratch, capture_output=True, timeout=30)
            self.assertNotEqual(altered.returncode, 0)
            self.assertFalse(altered.stdout)

    def test_mutating_returned_report_does_not_change_frozen_inputs(self):
        expected = deepcopy(self.report)
        returned = self.oracle["build_report"]()["cases"][0]["expected"]
        original = returned["ordered"]
        try:
            returned["ordered"] = ()
            self.assertEqual(self.oracle["build_report"](), expected)
        finally:
            returned["ordered"] = original

    def test_all_declared_outcomes_and_first_discrepancy(self):
        self.assertEqual(len(self.report["cases"]), len(CASES))
        self.assertEqual(set(self.by_id), set(CASES))
        for case_id, (input_id, probe, verdict, stage) in CASES.items():
            with self.subTest(case_id=case_id):
                case = self.by_id[case_id]
                self.assertEqual(
                    (case["input_id"], case["probe"], case["verdict"], case["expected_verdict"]),
                    (input_id, probe, verdict, verdict),
                )
                self.assertIn("expected", case)
                self.assertIn("observed", case)
                self.assertEqual(case["full_workflow_gate"], "BLOCKED")
                self.assertIs(case["matches_specification"], True)
                if verdict == "FAIL":
                    first = case["discrepancies"][0]
                    self.assertEqual(first["stage"], stage)
                    self.assertTrue(first["reason"])
                elif verdict == "PASS":
                    self.assertFalse(case["discrepancies"])

    def test_numeric_and_join_reference_against_frozen_rows(self):
        for name in ("mvp2", "filters", "sequence_witness"):
            fixture = FIXTURES[name]
            for reverse in (False, True):
                with self.subTest(fixture=name, reverse=reverse):
                    # Reordering the declarations can choose another tie order,
                    # but it cannot lose a row or detach DATA from its SORT input.
                    obs, offsets = fixture["observations"], fixture["offsets"]
                    if reverse:
                        obs, offsets = obs[::-1], offsets[::-1]
                    observed = self.oracle["reference_rows"](obs, offsets)
                    for stage, expected_rows in fixture["expected"].items():
                        self.assertEqual(
                            Counter(map(numeric_row, observed[stage])),
                            Counter(map(numeric_row, expected_rows)),
                        )
                    self.assertEqual(self.differences(fixture["expected"], observed), [])
        result = self.oracle["reference_rows"](
            FIXTURES["filters"]["observations"], FIXTURES["filters"]["offsets"]
        )
        self.assertEqual(
            Counter(map(numeric_row, result["adjusted"])),
            Counter({(1, Decimal("3.5")): 2, (1, None): 1}),
        )
        self.assertEqual(numeric_row(result["scaled"][0]), (1, None, 0, 0))
        self.assertIn((1, 0, None, None), map(numeric_row, result["scaled"]))

    def test_wrong_missing_last_model_detected_by_frozen_key_sequence(self):
        fixture = FIXTURES["mvp2"]
        reference_rows = self.oracle["reference_rows"]
        with patch.dict(reference_rows.__globals__, {"_ascending": lambda x: (x is None, x or 0)}):
            wrong = reference_rows(fixture["observations"], fixture["offsets"])
            self.assertEqual(wrong["ordered"][-1][0], ".")
            differences = self.differences(fixture["expected"], wrong)
            self.assertTrue(differences, "The frozen rows place ordinary missing first")
            self.assertEqual(differences[0]["stage"], "ordered")

    def test_python_missing_and_precision_boundaries(self):
        with self.assertRaises(TypeError):
            sorted([None, -1])
        with self.assertRaises(TypeError):
            _ = None / 2
        nan = float("nan")
        self.assertNotEqual(nan, float("nan"))
        self.assertNotIn(float("nan"), {nan: 1})
        self.assertEqual(float(2**53 + 1), float(2**53))
        self.assertNotEqual(int(float(2**53 + 1)), 2**53 + 1)
        observed = self.by_id["B01-published-workflow"]["observed"]["adjusted"]
        self.assertIn((None, 13), map(numeric_row, observed))

    def test_upstream_ties_are_free_but_set_follows_the_selected_sort(self):
        fixture = FIXTURES["mvp2"]
        expected = fixture["expected"]
        permuted = deepcopy(expected)
        for stage in ("ordered", "scaled"):
            first, a, b, last = permuted[stage]
            permuted[stage] = (first, b, a, last)
        self.assertEqual(self.differences(expected, permuted), [])
        permuted["ordered"] = expected["ordered"]
        self.assertEqual(self.differences(expected, permuted)[0]["stage"], "scaled")
        # Same batch, different sequence. Moving -1 ahead of ordinary missing
        # breaks the composite order even if DATA follows the moved rows.
        filters = FIXTURES["filters"]["expected"]
        wrong = deepcopy(filters)
        for stage in ("ordered", "scaled"):
            first, second, *rest = wrong[stage]
            wrong[stage] = (second, first, *rest)
        self.assertEqual(self.differences(filters, wrong)[0]["stage"], "ordered")
        sorted_rows = expected["ordered"]
        split = fixture["split_after"]
        self.assertEqual(sorted_rows[split - 1][:2], sorted_rows[split][:2])
        observed = self.oracle["candidate_rows"](
            fixture["observations"], fixture["offsets"], "split", split_after=split
        )
        self.assertEqual(self.differences(expected, observed), [])
        self.assertEqual(list(self.by_id["B04-split-by-group"]["chunks"]), [2, 2])

    def test_final_order_and_multiplicity_are_distinct_contracts(self):
        expected = FIXTURES["sequence_witness"]["expected"]
        observed = {**expected, "adjusted": FINAL_TIE_WITNESS}
        self.assertEqual(self.differences(expected, observed), [])
        self.assertEqual(
            self.differences(expected, {**observed, "adjusted": FINAL_TIE_WITNESS[::-1]})[0][
                "stage"
            ],
            "adjusted",
        )
        fixture = FIXTURES["filters"]
        observed = self.oracle["candidate_rows"](
            fixture["observations"], fixture["offsets"], "drop_matches"
        )
        self.assertLess(len(observed["adjusted"]), len(fixture["expected"]["adjusted"]))
        self.assertEqual(self.differences(fixture["expected"], observed)[0]["stage"], "adjusted")
        # Same row count and same distinct values; one duplicate occurrence is wrong.
        wrong_bag = {**fixture["expected"], "adjusted": (("1", "."), ("1", "."), ("1", "3.5"))}
        self.assertEqual(self.differences(fixture["expected"], wrong_bag)[0]["stage"], "adjusted")

    def test_coincidental_tie_order_versus_overstrict_candidate_policy(self):
        self.assertEqual(self.by_id["B03-sequence-coincidence"]["verdict"], "PASS")
        self.assertEqual(self.by_id["B06-final-tie-permutation"]["verdict"], "PASS")
        case = self.by_id["B12-overstrict-sequence"]
        self.assertEqual(self.differences(case["expected"], case["observed"]), [])
        policy = case["policy"]
        self.assertEqual(list(map(tuple, policy["offered_final_rows"])), list(FINAL_TIE_WITNESS))
        self.assertIs(policy["expected_acceptance"], True)
        self.assertIs(policy["observed_acceptance"], False)
        self.assertIs(policy["accepts_own_order"], True)

    def test_unknown_cases_and_unresolved_include_grant_no_acceptance(self):
        for case_id in ("B15-special-missing", "B16-precision-boundary"):
            case = self.by_id[case_id]
            self.assertEqual(case["verdict"], "UNVERIFIABLE")
            self.assertIsNone(case["expected"])
            self.assertIsNone(case["observed"])
        self.assertEqual(self.by_id["B17-unresolved-include"]["verdict"], "PASS")
        self.assertEqual(self.report["full_workflow_gate"], "BLOCKED")
        gap = self.report["unresolved_include"]
        self.assertEqual(
            (gap["operation"], gap["target"], gap["verdict"]),
            ("O4", "postcheck.sas", "UNVERIFIABLE"),
        )

    def test_numeric_equivalence_and_invalid_candidate_rows(self):
        expected = FIXTURES["filters"]["expected"]
        observed = deepcopy(expected)
        # Match numbers by exact value, not formatting. Signed zero is finite;
        # the ordinary missing token is distinct even when performing a sum.
        row = ("1.0", ".", "-0", "0.0")
        observed["scaled"] = (row, *expected["scaled"][1:])
        self.assertEqual(self.differences(expected, observed), [])
        for invalid in (("1", "0"), ("1", "NaN"), ("1", "3.5", "2")):
            with self.subTest(invalid=invalid):
                altered = {**expected, "adjusted": (*expected["adjusted"][:2], invalid)}
                self.assertEqual(self.differences(expected, altered)[0]["stage"], "adjusted")

    def test_stdlib_only_execution_reports_the_same_authority(self):
        guard = """
import runpy, sys
class NoEngine:
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] == 'sas_re':
            raise AssertionError('Behavioral oracle imported planner: ' + fullname)
sys.meta_path.insert(0, NoEngine())
def deny(event, args):
    if event.startswith(('socket.', 'subprocess.', 'os.system', 'os.spawn', 'os.posix_spawn', 'os.fork', 'os.exec')):
        raise AssertionError(event)
sys.addaudithook(deny)
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name='__main__')
"""
        with tempfile.TemporaryDirectory() as cwd:
            run = subprocess.run(
                [sys.executable, "-IBS", "-c", guard, str(SCRIPT)],
                cwd=cwd,
                env={**os.environ, "PATH": ""},
                capture_output=True,
                timeout=30,
            )
        self.assertEqual(run.returncode, 0, run.stderr)
        decoded = json.loads(run.stdout)
        self.assertEqual(decoded, json.loads(json.dumps(self.report)))
        for field, status in {
            "artifact_authority": "DRAFT",
            "semantic_verification": "UNVERIFIABLE",
            "semantic_acceptance": "BLOCKED",
            "benchmark_execution": "NOT_RUN",
        }.items():
            self.assertEqual(decoded[field], status)
