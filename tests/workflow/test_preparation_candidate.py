"""Public preparation-candidate assumptions preserve rule fallthrough, missing values, and source spans.

These engineering expectations are not SAS reference answers or independently accepted gold."""

from dataclasses import asdict, replace
import json
from pathlib import Path
import runpy
from types import SimpleNamespace
import unittest


from support.paths import REPOSITORY_ROOT as ROOT

SPANS = (
    ((317, 317), (13097, 13161)),
    ((319, 319), (13167, 13215)),
    ((320, 320), (13220, 13272)),
    ((322, 322), (13278, 13305)),
    ((324, 326), (13311, 13495)),
    ((328, 329), (13501, 13604)),
)


class PreparationCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = SimpleNamespace(**runpy.run_path(str(ROOT / "scripts/preparation_candidate.py")))

    def row(self, status="A       ", **changes):
        return replace(
            self.c.SyntheticRecord(
                case_id="T01",
                status=self.c.Character(status),
                id=7.5,
                numeric_group=(0, -2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12),
                character_group=tuple(
                    self.c.Character(x) for x in (".   ", "x   ", " Y  ", "0   ", "zz  ")
                ),
            ),
            **changes,
        )

    @staticmethod
    def events(result):
        return [(e.rule_index, e.action, e.predicate_result) for e in result.trace]

    def test_both_assignments_rejoin_and_preserve_public_values(self):
        for status, branch, value in (("A       ", 1, 1), ("B       ", 2, 0)):
            with self.subTest(branch=branch):
                row = self.row(status, id=0)
                result = self.c.prepare(row)
                self.assertEqual(result.disposition, "SURVIVED")
                self.assertIsNone(result.first_exclusion_rule)
                self.assertEqual(result.label_assignment_branch, branch)
                self.assertEqual((result.output.default, result.output.id), (value, 0))
                self.assertEqual(result.output.numeric_group, row.numeric_group)
                self.assertEqual(result.output.character_group, row.character_group)
                prefix = [(0, "PREDICATE", False), (1, "PREDICATE", branch == 1)]
                if branch == 2:
                    prefix.append((2, "PREDICATE", True))
                self.assertEqual(
                    self.events(result),
                    prefix
                    + [
                        (branch, f"ASSIGN_DEFAULT_{value}", None),
                        (3, "PREDICATE", False),
                        (4, "PREDICATE", False),
                        (5, "PREDICATE", False),
                    ],
                )

    def test_status_polarity_case_and_padding_without_normalization(self):
        for status in ("C       ", "a       ", " A      ", "        ", ".       "):
            with self.subTest(status=status):
                result = self.c.prepare(self.row(status, id=self.c.NumericMissing()))
                self.assertEqual((result.disposition, result.first_exclusion_rule), ("EXCLUDED", 0))
                self.assertIsNone(result.output)
                self.assertIsNone(result.label_assignment_branch)
                self.assertEqual(
                    self.events(result), [(0, "PREDICATE", True), (0, "EXCLUDE_CURRENT_ROW", None)]
                )

    def test_isolated_pair_fallthrough_and_rejoin_are_explicit(self):
        for initial in (9, self.c.NumericMissing(".Z")):
            row = self.row("C       ", initial_default=initial)
            result = self.c.prepare(row, mode="isolated_pair")
            self.assertEqual(result.mode, "isolated_pair")
            self.assertIsNone(result.label_assignment_branch)
            self.assertEqual(result.output.default, initial)
            self.assertEqual(
                self.events(result),
                [
                    (1, "PREDICATE", False),
                    (2, "PREDICATE", False),
                    (2, "NO_ASSIGNMENT_BY_PAIR", None),
                    (3, "PREDICATE", False),
                    (4, "PREDICATE", False),
                    (5, "PREDICATE", False),
                ],
            )
            excluded = self.c.prepare(
                replace(row, id=self.c.NumericMissing()), mode="isolated_pair"
            )
            self.assertEqual(excluded.first_exclusion_rule, 3)
            self.assertIsNone(excluded.label_assignment_branch)
            self.assertEqual(
                self.events(excluded)[-2:],
                [(3, "PREDICATE", True), (3, "EXCLUDE_CURRENT_ROW", None)],
            )
        for status, branch in (("A       ", 1), ("B       ", 2)):
            result = self.c.prepare(self.row(status), mode="isolated_pair")
            self.assertEqual(result.label_assignment_branch, branch)
            self.assertNotIn(0, [e.rule_index for e in result.trace])

    def test_ordinary_and_special_numeric_missing_exclude_after_assignment(self):
        for tag in (".", "._", *(f".{x}" for x in "ABCDEFGHIJKLMNOPQRSTUVWXYZ")):
            with self.subTest(tag=tag):
                result = self.c.prepare(self.row("B       ", id=self.c.NumericMissing(tag)))
                self.assertEqual(
                    (result.first_exclusion_rule, result.label_assignment_branch), (3, 2)
                )
                self.assertIsNone(result.output)
                self.assertEqual([e.rule_index for e in result.trace], [0, 1, 2, 2, 3, 3])
        for position, tag in ((0, "."), (6, ".A"), (11, "._")):
            group = list(self.row().numeric_group)
            group[position] = self.c.NumericMissing(tag)
            result = self.c.prepare(self.row(numeric_group=tuple(group)))
            self.assertEqual((result.first_exclusion_rule, result.label_assignment_branch), (4, 1))
            self.assertEqual(
                self.events(result)[-2:], [(4, "PREDICATE", True), (4, "EXCLUDE_CURRENT_ROW", None)]
            )

    def test_character_missing_and_overlapping_exclusions_stop_at_first_rule(self):
        missing = self.c.NumericMissing()
        numbers = (missing,) + self.row().numeric_group[1:]
        for position in (0, 4):
            chars = list(self.row().character_group)
            chars[position] = self.c.Character("    ")
            for status, identifier, group, first, branch in (
                ("A       ", 7.5, self.row().numeric_group, 5, 1),
                ("B       ", 7.5, self.row().numeric_group, 5, 2),
                ("A       ", missing, numbers, 3, 1),
                ("B       ", 7.5, numbers, 4, 2),
                ("C       ", missing, numbers, 0, None),
            ):
                with self.subTest(position=position, first=first, branch=branch):
                    result = self.c.prepare(
                        self.row(
                            status, id=identifier, numeric_group=group, character_group=tuple(chars)
                        )
                    )
                    self.assertEqual(
                        (result.first_exclusion_rule, result.label_assignment_branch),
                        (first, branch),
                    )
                    self.assertIsNone(result.output)
                    self.assertEqual(self.events(result)[-1], (first, "EXCLUDE_CURRENT_ROW", None))
                    self.assertTrue(all(e.rule_index <= first for e in result.trace))

    def test_determinism_source_references_and_evidence_boundaries(self):
        row = self.row("B       ")
        before = asdict(row)
        first = self.c.prepare(row)
        self.assertEqual(first, self.c.prepare(row))
        self.assertEqual(
            json.dumps(asdict(first), sort_keys=True),
            json.dumps(asdict(self.c.prepare(row)), sort_keys=True),
        )
        self.assertEqual(before, asdict(row))
        self.assertEqual({e.rule_index for e in first.trace}, set(range(6)))
        for event in first.trace:
            self.assertEqual((event.source_lines, event.source_bytes), SPANS[event.rule_index])
        self.assertEqual(
            {
                name: getattr(first, name)
                for name in (
                    "artifact_authority",
                    "behavioral_evidence",
                    "semantic_verification",
                    "semantic_acceptance",
                    "reference_experiment",
                    "benchmark_execution",
                )
            },
            {
                "artifact_authority": "DRAFT",
                "behavioral_evidence": "UNAVAILABLE",
                "semantic_verification": "UNVERIFIABLE",
                "semantic_acceptance": "BLOCKED",
                "reference_experiment": "NOT_RUN",
                "benchmark_execution": "NOT_RUN",
            },
        )

    def test_unsupported_inputs_are_rejected_not_coerced(self):
        for tag in ("A", ".a", "", ".AA", None, 0):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                self.c.NumericMissing(tag)
        for text in (None, b"A", "", "x\t  ", "x\n  ", "é   "):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.c.Character(text)
        invalid = [
            self.row(id=x) for x in (None, True, ".A", float("nan"), float("inf"), 2**53 + 1)
        ]
        invalid += [
            self.row(initial_default=True),
            self.row(case_id="toolong"),
            replace(self.row(), status="A       "),
            replace(self.row(), status=self.c.Character("A")),
            self.row(numeric_group=(1,) * 11),
            self.row(numeric_group=[1] * 12),
            self.row(character_group=(self.c.Character("X"),) * 5),
            self.row(character_group=(None,) * 5),
        ]
        invalid += [self.row("C       ", numeric_group=(None,) * 12)]
        for row in [None, {}, *invalid]:
            with self.subTest(row=row), self.assertRaises(ValueError):
                self.c.prepare(row)
        for mode in (None, True, "probe", "FULL"):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                self.c.prepare(self.row(), mode=mode)


if __name__ == "__main__":
    unittest.main()
