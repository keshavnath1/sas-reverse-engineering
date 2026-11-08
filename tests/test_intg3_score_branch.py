"""Public MOD-2 fixture binding checks for the integrated operator path."""

from pathlib import Path
import runpy
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from test_review_workflow import ROOT


@unittest.skipUnless(sys.platform in ("darwin", "linux"), "Existing POSIX evidence workflow")
class IntegratedScoreFixtureTests(unittest.TestCase):
    def test_mapping_and_coefficient_bytes_are_pinned(self):
        runner = runpy.run_path(str(ROOT / "scripts/score_prepared_logistic.py"))
        load = runner["load_model_fixtures"]
        originals = {name: (runner["EXAMPLE"] / name).read_bytes() for name in runner["FIXTURE_PINS"]}
        with TemporaryDirectory() as temp:
            fixtures = Path(temp).resolve()
            for name, raw in originals.items():
                (fixtures / name).write_bytes(raw)
            with patch.dict(load.__globals__, EXAMPLE=fixtures):
                self.assertEqual(load(), originals)
                for name, raw in originals.items():
                    with self.subTest(name=name):
                        (fixtures / name).write_bytes(raw + b"\n")
                        with self.assertRaisesRegex(ValueError, "MODEL_PUBLIC_FIXTURE_IDENTITY_MISMATCH"):
                            load()
                        (fixtures / name).write_bytes(raw)
