"""Public engineering expectations for the bounded running-balance candidate."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from run_running_balance import PACKAGE, PACKAGE_SHA256, build_result, run_pipeline


@unittest.skipUnless(sys.platform in ("darwin", "linux"), "Existing POSIX evidence workflow")
class RunningBalanceTests(unittest.TestCase):
    def test_published_profile_and_cli_replay(self):
        result = build_result(PACKAGE)
        expected = {
            "work.running": [[1, 1, 2, 2, None, None],
                             [1, 1, None, 2, None, 1],
                             [2, 1, 4, 4, 2, 1]],
            "work.export_order": [[1, 1, 2, 2, None, None],
                                  [1, 1, None, 2, None, 1],
                                  [2, 1, 4, 4, 2, 1]],
            "work.enriched": [[1, 2, 3], [1, 2, 3], [2, 4, 5]],
        }
        self.assertEqual({name: data["rows"] for name, data in result["outputs"].items()}, expected)
        self.assertEqual(result["package_manifest_sha256"], PACKAGE_SHA256)
        self.assertEqual(result["reference_experiment"], "NOT_RUN")
        self.assertEqual(result["semantic_acceptance"], "BLOCKED")
        command = [sys.executable, "-IB", str(ROOT / "scripts/run_running_balance.py")]
        first = subprocess.check_output(command)
        self.assertEqual(first, subprocess.check_output(command))
        self.assertEqual(json.loads(first), result)

    def test_state_ties_missing_and_join_multiplicity(self):
        running, ordered, enriched = run_pipeline(
            [[".", "1", "2"], [".", "1", "0"], [".", "2", "3"],
             ["1", "2", "-1"], ["1", "2", "4"], ["2", "1", "."]],
            [[".", "5"], [".", "5"], [".", "."], ["1", "0"], ["1", "-2"], ["1", "7"]],
        )
        self.assertEqual(running, [
            (None, 1, 2, 2, None, None), (None, 1, 0, 2, None, 1),
            (None, 2, 3, 5, 2, 1), (1, 2, -1, -1, None, None),
            (1, 2, 4, 3, 3, 1), (2, 1, None, 0, None, 1),
        ])
        self.assertEqual(ordered, running)
        self.assertCountEqual(enriched, [
            (None, 2, 5), (None, 2, 5), (None, 2, 5), (None, 2, 5),
            (None, 5, 5), (None, 5, 5), (1, -1, 7), (1, 3, 7),
        ])
        self.assertEqual(run_pipeline([], []), ([], [], []))

    def test_unsupported_input_refused(self):
        with self.assertRaisesRegex(ValueError, "INPUT_ORDER_REQUIRED"):
            run_pipeline([["1", "2", "0"], ["1", "1", "0"]], [])
        for value in (".A", "0.1", 2, "NaN", "2097152"):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "UNSUPPORTED_NUMERIC"):
                run_pipeline([["1", "1", value]], [])
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_ROW_SHAPE"):
            run_pipeline([["1", "2"]], [])
        with self.assertRaisesRegex(ValueError, "BALANCE_OUTSIDE_DOMAIN"):
            run_pipeline([["1", "1", "1048576"], ["1", "1", "1"]], [])
        with self.assertRaisesRegex(ValueError, "JOIN_CARDINALITY_LIMIT"):
            run_pipeline([["1", "1", "0"]] * 101, [["1", "1"]] * 100)

    def test_exact_evidence_binding(self):
        with TemporaryDirectory() as temporary:
            package = Path(temporary).resolve() / "package"
            shutil.copytree(PACKAGE, package)
            self.assertEqual(build_result(package), build_result(PACKAGE))
            graph = package / "evidence/EVIDENCE.json"
            graph.write_bytes(graph.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "PACKAGE_PAYLOAD_IDENTITY_MISMATCH"):
                build_result(package)
            manifest = package / "MANIFEST.json"
            manifest.write_bytes(manifest.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "UNSUPPORTED_PACKAGE_IDENTITY"):
                build_result(package)
