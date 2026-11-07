"""Source-only review checks using disposable public synthetic SAS text."""

from hashlib import sha256
import json
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory
import unittest
import uuid

from test_review_workflow import ROOT, call, remove_destination


SCRIPT = ROOT / "scripts/review_source.py"
SORT = b"proc sort data=work.a out=work.b;\r\n  by id;\r\nrun;"
STATUS_UNIT = (
    b"if category not in ('A','B','C') then delete;\r\n"
    b"if category = 'A' then label = 1;\r\n"
    b"else if category = 'B' then label = 0;\r\n"
)
LATER_GAPS = (
    b"if missing(key) then delete;\r\n"
    b"if cmiss(x, y) > 0 then delete;\r\n"
    b"if cmiss(z) > 0 then delete;\r\n"
)
PREFIX = "/* café */\r\n%unreviewed_driver;\r\n".encode()


@unittest.skipUnless(sys.platform in ("darwin", "linux"), "Existing POSIX scratch writer")
class SourceReviewTests(unittest.TestCase):
    def setUp(self):
        scratch = "/private/tmp" if sys.platform == "darwin" else "/tmp"
        directory = self.enterContext(TemporaryDirectory(dir=scratch))
        self.source = Path(directory) / "input.sas"

    def review(self, raw, lines="3:5", expected=None, destination=None, second_lines=None, recover_rules=False):
        self.source.write_bytes(raw)
        if destination is None:
            destination = Path("/tmp") / f"sas-re-source-{uuid.uuid4().hex}"
            self.addCleanup(remove_destination, destination)
        run = call(destination, script=SCRIPT, extra=(
            "--source", str(self.source), "--source-sha256", expected or sha256(raw).hexdigest(),
            "--lines", lines, *(("--lines", second_lines) if second_lines else ()),
            *(("--recover-status-rules",) if recover_rules else ()),
        ))
        return run, destination

    def test_supported_span_is_bound_to_original_bytes_and_deterministic(self):
        raw = PREFIX + SORT
        run, destination = self.review(raw)
        self.assertEqual(run.returncode, 0, run.stderr)
        files = {p.name: p.read_bytes() for p in destination.iterdir()}
        self.assertEqual(set(files), {"README.md", "EVIDENCE.json"})
        evidence = json.loads(files["EVIDENCE.json"])
        self.assertEqual(evidence["source_identity"], "VERIFIED")
        self.assertEqual(evidence["syntax_recognition"], "SUPPORTED")
        self.assertEqual(evidence["source"]["sha256"], sha256(raw).hexdigest())
        self.assertEqual(evidence["source"]["selected_span"], {
            "line_start": 3, "line_end": 5, "start": len(PREFIX), "end": len(raw),
            "sha256": sha256(SORT).hexdigest(),
        })
        operation = evidence["declared_operation"]
        self.assertEqual(operation["span"]["start"], len(PREFIX))
        self.assertEqual(operation["ordering_span"]["line_start"], 4)
        key = operation["ordering_span"]
        self.assertEqual(raw[key["start"]:key["end"]], b"by id;")
        self.assertEqual((operation["input"], operation["output"], operation["ordering_keys"]),
                         ("work.a", "work.b", ["id"]))
        self.assertEqual(evidence["boundaries"], {"upstream": "UNRESOLVED", "downstream": "UNRESOLVED"})
        for field, value in {
            "key_schema": "UNKNOWN", "supported_profile_reconstruction": "NOT_RUN",
            "behavioral_evidence": "UNAVAILABLE", "semantic_verification": "UNVERIFIABLE",
            "semantic_acceptance": "BLOCKED", "artifact_authority": "DRAFT",
            "benchmark_execution": "NOT_RUN",
        }.items():
            self.assertEqual(evidence[field], value)
        self.assertNotIn(b"PASS", files["EVIDENCE.json"])
        self.assertNotIn(b"proc sort", files["README.md"].lower())
        again, second = self.review(raw)
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual({p.name: p.read_bytes() for p in second.iterdir()}, files)
        refused, _ = self.review(raw, destination=destination)
        self.assertEqual(refused.returncode, 2)
        self.assertEqual({p.name: p.read_bytes() for p in destination.iterdir()}, files)

    def test_mismatched_hash_and_out_of_range_refuse_output(self):
        raw = PREFIX + SORT
        run, destination = self.review(raw, expected="0" * 64)
        self.assertEqual(run.returncode, 2)
        self.assertIn(b"SOURCE_SHA256_MISMATCH", run.stderr)
        self.assertFalse(destination.exists())
        run, destination = self.review(raw + b"\n", lines="3:6")
        self.assertEqual(run.returncode, 2)
        self.assertIn(b"LINE_RANGE_OUTSIDE_SOURCE", run.stderr)
        self.assertFalse(destination.exists())

    def test_unsupported_spans_publish_only_bound_refusal_evidence(self):
        for raw in (SORT.replace(b"by id", b"by descending id"),
                    b"%include 'missing.sas';", SORT + b"\n" + SORT):
            with self.subTest(size=len(raw)):
                count = len(raw.splitlines())
                run, destination = self.review(raw, lines=f"1:{count}")
                self.assertEqual(run.returncode, 2, run.stderr)
                evidence = json.loads((destination / "EVIDENCE.json").read_bytes())
                self.assertEqual(evidence["source_identity"], "VERIFIED")
                self.assertEqual(evidence["syntax_recognition"], "UNSUPPORTED")
                self.assertEqual(evidence["source"]["selected_span"]["sha256"], sha256(raw).hexdigest())
                self.assertIsNone(evidence["declared_operation"])
                self.assertTrue(evidence["reason_codes"])

    def test_data_step_recovers_declarations_and_six_separate_gaps(self):
        statements = [
            b"data work.target;",
            b"set work.input;",
            b"if category not in ('A','B') then delete;",
            b"if category = 'A' then label = 1;",
            b"else if category = 'B' then label = 0;",
            b"if missing(key) then delete;",
            b"if cmiss(x,",
            b" y) > 0 then delete;",
            b"if cmiss(z) > 0 then delete;",
            b"keep key label;",
            b"run;",
        ]
        raw = PREFIX + b"\r\n".join(statements)
        run, dest = self.review(raw, lines="3:13")
        self.assertEqual(run.returncode, 0, run.stderr)
        evidence = json.loads((dest / "EVIDENCE.json").read_bytes())
        self.assertEqual(evidence["source"]["sha256"], sha256(raw).hexdigest())
        self.assertEqual(evidence["source"]["selected_span"]["start"], len(PREFIX))
        self.assertEqual(evidence["source"]["selected_span"]["end"], len(raw))
        self.assertEqual(evidence["review_status"], "PARTIAL")
        self.assertEqual(evidence["syntax_recognition"], "PARTIAL")
        self.assertEqual(evidence["supported_profile_reconstruction"], "NOT_RUN")
        op = evidence["declared_operation"]
        self.assertEqual((op["kind"], op["input"], op["output"], op["selected_columns"]),
                         ("DATA_STEP", "work.input", "work.target", ["key", "label"]))
        for key, index in (("output", 0), ("input", 1), ("keep", 9)):
            location = op["declaration_spans"][key]
            self.assertEqual(location["line_start"], index + 3)
            self.assertEqual(raw[location["start"]:location["end"]], statements[index])
        gaps = op["unsupported_statements"]
        expected = [(2, 2), (3, 3), (4, 4), (5, 5), (6, 7), (8, 8)]
        self.assertEqual(len(gaps), len(expected))
        for gap, (first, last) in zip(gaps, expected, strict=True):
            location = gap["span"]
            text = b"\r\n".join(statements[first:last + 1])
            start = len(PREFIX) + sum(len(line) + 2 for line in statements[:first])
            self.assertEqual(location, {
                "line_start": first + 3, "line_end": last + 3,
                "start": start, "end": start + len(text), "sha256": sha256(text).hexdigest(),
            })
            self.assertTrue(gap["reason_codes"])
        self.assertEqual(op["row_selection"], "UNKNOWN")
        self.assertEqual(op["selected_column_values_and_derivation"], "UNKNOWN")
        self.assertNotIn("control_lineage", op)
        self.assertEqual(evidence["behavioral_evidence"], "UNAVAILABLE")
        readme = (dest / "README.md").read_bytes()
        self.assertIn(b"2 output selections", readme)
        self.assertNotIn(statements[3], readme)
        self.assertNotIn(b"PASS", (dest / "EVIDENCE.json").read_bytes())
        again, second = self.review(raw, lines="3:13")
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual({p.name: p.read_bytes() for p in dest.iterdir()},
                         {p.name: p.read_bytes() for p in second.iterdir()})

    def test_data_review_requires_one_terminated_step_and_one_set_input(self):
        raw = b"data work.target; set work.input; label = 1; keep label; run;"
        run, dest = self.review(raw, lines="1:1")
        self.assertEqual(run.returncode, 0, run.stderr)
        op = json.loads((dest / "EVIDENCE.json").read_bytes())["declared_operation"]
        self.assertEqual(op["unsupported_statements"][0]["reason_codes"],
                         ["TRANSFORMATION_OUTSIDE_REVIEW_SCOPE"])
        for bad in (raw.removesuffix(b" run;"), raw.replace(b"set work.input;", b"set work.input work.other;")):
            run, dest = self.review(bad, lines="1:1")
            self.assertEqual(run.returncode, 2, run.stderr)
            self.assertIsNone(json.loads((dest / "EVIDENCE.json").read_bytes())["declared_operation"])

    def test_two_ranges_bind_a_declared_connection_and_leave_middle_unexamined(self):
        data = (b"data work.Mixed;\r\nset work.input;\r\n"
                b"if missing(id) then delete;\r\nkeep id label;\r\nrun;\r\n")
        middle = b"%unexamined; data work.mixed; run;\r\n"
        sort = b"proc sort data=WORK.MIXED out=work.result; by id; run;"
        raw = PREFIX + data + middle + sort
        run, dest = self.review(raw, lines="3:7", second_lines="9:9")
        self.assertEqual(run.returncode, 0, run.stderr)
        payload = (dest / "EVIDENCE.json").read_bytes()
        evidence = json.loads(payload)
        self.assertEqual(evidence["source"]["sha256"], sha256(raw).hexdigest())
        first, second = evidence["selections"]
        for item, expected, start in ((first, data, len(PREFIX)),
                                      (second, sort, len(PREFIX + data + middle))):
            location = item["selected_span"]
            self.assertEqual((location["start"], location["end"]), (start, start + len(expected)))
            self.assertEqual(location["sha256"], sha256(expected).hexdigest())
        self.assertEqual(first["declared_operation"]["selected_columns"], ["id", "label"])
        self.assertEqual(len(first["declared_operation"]["unsupported_statements"]), 1)
        self.assertEqual(second["declared_operation"]["ordering_keys"], ["id"])
        self.assertEqual(evidence["connection"], {
            "classification": "SOURCE_DECLARED", "execution_verification": "EXECUTION_UNVERIFIED",
            "data_output": "work.mixed", "sort_input": "work.mixed",
        })
        self.assertEqual(evidence["intervening_span"], {
            "status": "UNEXAMINED", "start": len(PREFIX + data), "end": len(PREFIX + data + middle),
        })
        self.assertNotIn(middle, payload)
        self.assertEqual(evidence["semantic_acceptance"], "BLOCKED")
        again, other = self.review(raw, lines="3:7", second_lines="9:9")
        self.assertEqual(again.returncode, 0, again.stderr)
        for name in ("README.md", "EVIDENCE.json"):
            self.assertEqual((dest / name).read_bytes(), (other / name).read_bytes())

    def test_migration_review_links_to_existing_source_records(self):
        data = (b"data work.stage;\r\nset work.input;\r\n"
                b"if missing(id) then delete;\r\nkeep id default;\r\nrun;\r\n")
        middle = (b"proc sql;\r\ncreate table work.audit as select id from work.stage;\r\n"
                  b"quit;\r\n%if &n = 0 %then %abort_run(empty);\r\n")
        sort = b"proc sort data=work.stage out=work.final; by id; run;"
        raw = data + middle + sort
        run, dest = self.review(raw, lines="1:5", second_lines="10:10")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual({file.name for file in dest.iterdir()},
                         {"README.md", "EVIDENCE.json", "MIGRATION_REVIEW.md"})
        evidence = json.loads((dest / "EVIDENCE.json").read_bytes())
        report = (dest / "MIGRATION_REVIEW.md").read_text()
        trace, rest = report.split("## MAP", 1)
        mapping, obligations = rest.split("## Behavioral obligations", 1)
        data, sort = evidence["selections"]
        operation = data["declared_operation"]
        spans = [
            data["selected_span"], sort["selected_span"],
            *operation["declaration_spans"].values(),
            *(gap["span"] for gap in operation["unsupported_statements"]),
            sort["declared_operation"]["span"], sort["declared_operation"]["ordering_span"],
            *(finding["span"] for finding in evidence["interval_effects"]["findings"]),
        ]
        expected = {f"bytes-{span['start']}-{span['end']}" for span in spans}
        self.assertCountEqual(re.findall(r'id="(bytes-[0-9]+-[0-9]+)"', trace), expected)
        for section in (mapping, obligations):
            references = set(re.findall(r"\]\(#(bytes-[0-9]+-[0-9]+)\)", section))
            self.assertTrue(references)
            self.assertLessEqual(references, expected)
        for item in operation["unsupported_statements"]:
            gap = item["span"]
            reference = f"bytes-{gap['start']}-{gap['end']}"
            self.assertIn(gap["sha256"], trace)
            self.assertIn(f"](#{reference})", obligations)
        for finding in evidence["interval_effects"]["findings"]:
            span = finding["span"]
            self.assertIn(f"](#bytes-{span['start']}-{span['end']})", mapping)
        self.assertIn("SOURCE_DECLARED / EXECUTION_UNVERIFIED", mapping)
        self.assertIn("SORT reachability is UNESTABLISHED", mapping)
        self.assertIn("No direct writer identified", mapping)
        self.assertIn("`Default` derivation", obligations)
        self.assertIn("HYPOTHETICAL", obligations)
        self.assertNotIn("work.audit", mapping + obligations)
        self.assertNotIn("if missing(id)", report)
        self.assertNotIn("PASS", report)
        for key in ("artifact_authority", "behavioral_evidence", "semantic_verification",
                    "semantic_acceptance", "benchmark_execution"):
            self.assertIn(f"{key}: {evidence[key]}", report)
        again, other = self.review(raw, lines="1:5", second_lines="10:10")
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual((dest / "MIGRATION_REVIEW.md").read_bytes(),
                         (other / "MIGRATION_REVIEW.md").read_bytes())

    def test_nonmatching_connection_and_ambiguous_selection(self):
        data = b"data work.target; set work.input; keep id; run;\n"
        sort = b"proc sort data=work.other out=work.sorted; by id; run;"
        run, dest = self.review(data + sort, lines="1:1", second_lines="2:2")
        self.assertEqual(run.returncode, 0, run.stderr)
        evidence = json.loads((dest / "EVIDENCE.json").read_bytes())
        self.assertEqual(evidence["connection"]["classification"], "UNRESOLVED")
        for raw, second in ((data + sort, "1:2"),
                            (data.replace(b"set work.input", b"set work.input work.extra") + sort, "2:2")):
            run, dest = self.review(raw, lines="1:1", second_lines=second)
            self.assertEqual(run.returncode, 2, run.stderr)
            self.assertFalse(dest.exists())

    def test_interval_inventory_binds_reads_outputs_and_control_gates(self):
        data = b"data work.stage; set work.input; keep id; run;\r\n"
        middle = [
            b"proc sql noprint;",
            b"create table work.audit as select id from work.stage;",
            b"select count(*) into :n from work.stage;",
            b"quit;",
            b"%check_step;",
            b"%if &n = 0 %then %abort_run(empty);",
            b"ods output Summary=work.summary;",
            b"proc means data=work.stage;",
            b"run;",
        ]
        interval = b"\r\n".join(middle) + b"\r\n"
        sort = b"proc sort data=work.stage out=work.final; by id; run;"
        run, dest = self.review(data + interval + sort, lines="1:1", second_lines="11:11")
        self.assertEqual(run.returncode, 0, run.stderr)
        evidence = json.loads((dest / "EVIDENCE.json").read_bytes())
        self.assertEqual(evidence["connection"]["classification"], "SOURCE_DECLARED")
        self.assertEqual(evidence["connection"]["execution_verification"], "EXECUTION_UNVERIFIED")
        effects = evidence["interval_effects"]
        self.assertEqual(effects["sha256"], sha256(interval).hexdigest())
        self.assertEqual(effects["direct_reads"], ["work.stage"])
        self.assertEqual(effects["other_outputs"], ["work.audit", "work.summary"])
        self.assertIs(effects["shared_writer_identified"], False)
        self.assertEqual(effects["sort_reachability"], "UNESTABLISHED")
        findings = {item["span"]["line_start"]: item for item in effects["findings"]}
        self.assertEqual(findings[3]["writes"], ["work.audit"])
        self.assertEqual(findings[4]["reads"], ["work.stage"])
        self.assertEqual(findings[6]["unknown_effects"], ["MACRO_DEPENDENT_EFFECTS"])
        self.assertIn("POTENTIAL_ABORT", findings[7]["control_gates"])
        self.assertEqual(findings[8]["ods_outputs"], ["work.summary"])
        for line, item in findings.items():
            original = middle[line - 2]
            start = len(data) + sum(len(part) + 2 for part in middle[:line - 2])
            self.assertEqual(item["span"], {
                "start": start, "end": start + len(original), "line_start": line,
                "line_end": line, "sha256": sha256(original).hexdigest(),
            })
        review = (dest / "README.md").read_text()
        self.assertIn("No direct writer identified within the inspected supported source forms; unresolved effects remain.", review)
        self.assertNotIn("create table", review.lower())

    def test_interval_inventory_distinguishes_writer_from_unavailable_inspection(self):
        data = b"data work.stage; set work.input; keep id; run;\n"
        sort = b"proc sort data=work.stage out=work.final; by id; run;"
        for middle, expected in ((b"data work.stage; set work.other; run;\n", True),
                                 (b"\xff\n", None)):
            with self.subTest(writer=expected):
                run, dest = self.review(data + middle + sort, lines="1:1", second_lines="3:3")
                self.assertEqual(run.returncode, 0, run.stderr)
                effects = json.loads((dest / "EVIDENCE.json").read_bytes())["interval_effects"]
                self.assertIs(effects["shared_writer_identified"], expected)
                if expected:
                    self.assertEqual(effects["findings"][0]["writes"], ["work.stage"])
                else:
                    self.assertEqual(effects["status"], "UNAVAILABLE")
                    self.assertEqual(effects["findings"][0]["unknown_effects"], ["INTERVAL_NOT_UTF8"])


    def test_status_rules_preserve_order_polarity_linkage_and_later_gaps(self):
        header = b"data work.stage;\r\nset work.input;\r\n"
        raw = PREFIX + header + STATUS_UNIT + LATER_GAPS + b"keep key label;\r\nrun;"
        run, dest = self.review(raw, lines="3:12", recover_rules=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        evidence = json.loads((dest / "EVIDENCE.json").read_bytes())
        operation = evidence["declared_operation"]
        recovery = operation["status_rule_recovery"]
        rules = recovery["rules"]
        self.assertEqual(recovery["status"], "RECOVERED")
        self.assertEqual(recovery["fallthrough"], "NO_ASSIGNMENT_BY_PAIR")
        self.assertEqual(recovery["execution_verification"], "UNVERIFIED")
        self.assertEqual([rule["predicate"] for rule in rules], [
            {"variable": "category", "operator": "NOT IN", "values": ["A", "B", "C"]},
            {"variable": "category", "operator": "=", "value": "A"},
            {"variable": "category", "operator": "=", "value": "B"},
        ])
        # C exercises representable fallthrough. Nonmembers take DELETE.
        # These are source relationships, with no candidate row evaluation.
        self.assertEqual([rule["when"] for rule in rules], [
            [],
            [{"rule_index": 0, "predicate_result": False}],
            [{"rule_index": 0, "predicate_result": False},
             {"rule_index": 1, "predicate_result": False}],
        ])
        self.assertEqual(rules[0]["action"], {
            "kind": "DELETE", "scope": "CURRENT_ROW_ITERATION",
            "on_match": "SKIP_REMAINING_STATEMENTS_AND_SUPPRESS_OUTPUT",
        })
        self.assertEqual([r["action"] for r in rules[1:]], [
            {"kind": "ASSIGN_NUMERIC_LITERAL", "target": "label", "lexeme": "1"},
            {"kind": "ASSIGN_NUMERIC_LITERAL", "target": "label", "lexeme": "0"},
        ])
        gaps = operation["unsupported_statements"]
        self.assertEqual(len(gaps), 3)
        start = len(PREFIX + header)
        for record, statement, line in zip(rules + gaps,
                                           (STATUS_UNIT + LATER_GAPS).splitlines(), range(5, 11), strict=True):
            span = record["span"]
            self.assertEqual(span, {
                "line_start": line, "line_end": line, "start": start, "end": start + len(statement),
                "sha256": sha256(statement).hexdigest(),
            })
            self.assertEqual(raw[span["start"]:span["end"]], statement)
            start += len(statement) + 2
        for gap in gaps:
            self.assertIn("UNRESOLVED", gap["effect"])
        for rule in rules:
            self.assertEqual(rule["classification"], "SOURCE_RECOGNIZED")
            self.assertTrue(rule["parser_reason_codes"])
        self.assertEqual(evidence["review_format"], "source-only-data/2")
        self.assertEqual(evidence["source"]["sha256"], sha256(raw).hexdigest())
        self.assertEqual(evidence["syntax_recognition"], "PARTIAL")
        self.assertEqual(operation["selected_column_values_and_derivation"], "UNKNOWN")
        report = (dest / "README.md").read_text()
        for phrase in ("NOT IN", "NO_ASSIGNMENT_BY_PAIR", "Later unresolved", "Execution UNVERIFIED"):
            self.assertIn(phrase, report)
        for file in dest.iterdir():
            self.assertNotIn(b"PASS", file.read_bytes())
        again, other = self.review(raw, lines="3:12", recover_rules=True)
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual({p.name: p.read_bytes() for p in dest.iterdir()},
                         {p.name: p.read_bytes() for p in other.iterdir()})

    def test_status_rule_ambiguous_or_unsupported_units_remain_gaps(self):
        variants = [
            STATUS_UNIT.replace(b"not in", b"in"),
            STATUS_UNIT.replace(b"then delete", b"then output"),
            STATUS_UNIT.replace(b"else if", b"if"),
            STATUS_UNIT.replace(b"else if", b"label=7; else if"),
            STATUS_UNIT.replace(b"else if", b"else if other=0 then"),
            STATUS_UNIT.replace(b"label = 0", b"other = 0"),
            STATUS_UNIT.replace(b"label = 0", b"label = label+1"),
            STATUS_UNIT.replace(b"label = 0", b"label = ."),
            STATUS_UNIT + b"else label=9;\r\n",
            b"if key=0 then delete;\r\n" + STATUS_UNIT,
            STATUS_UNIT.replace(b"'A','B','C'", b"('A','B'),'C'"),
        ]
        for unit in variants:
            with self.subTest(unit=unit):
                raw = b"data work.stage; set work.input; " + unit + b"keep key label; run;"
                lines = f"1:{len(raw.splitlines())}"
                baseline, old = self.review(raw, lines=lines)
                run, dest = self.review(raw, lines=lines, recover_rules=True)
                self.assertEqual(baseline.returncode, 0, baseline.stderr)
                self.assertEqual(run.returncode, 0, run.stderr)
                before = json.loads((old / "EVIDENCE.json").read_bytes())["declared_operation"]
                after = json.loads((dest / "EVIDENCE.json").read_bytes())["declared_operation"]
                self.assertEqual(after["status_rule_recovery"]["status"], "UNRESOLVED")
                self.assertEqual(after["status_rule_recovery"]["rules"], [])
                self.assertEqual(before["unsupported_statements"], after["unsupported_statements"])

    def test_status_rule_review_links_reuse_trace_and_sort_stays_unchanged(self):
        # Doubled quote, Unicode and punctuation exercise literal decoding and safe presentation.
        unit = STATUS_UNIT.replace(b"'A'", "'Aé''|<b>'".encode())
        data = b"data work.stage;\r\nset work.input;\r\n" + unit + LATER_GAPS + b"keep key label;\r\nrun;\r\n"
        sort = b"proc sort data=work.stage out=work.sorted; by key; run;"
        raw = data + sort
        run, dest = self.review(raw, lines="1:10", second_lines="11:11", recover_rules=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        e = json.loads((dest / "EVIDENCE.json").read_bytes())
        self.assertEqual(e["review_format"], "source-only-dependency/2")
        rules = e["selections"][0]["declared_operation"]["status_rule_recovery"]["rules"]
        self.assertEqual(rules[0]["predicate"]["values"][0], "Aé'|<b>")
        report = (dest / "MIGRATION_REVIEW.md").read_text()
        trace, mapping = report.split("## MAP")
        for rule in rules:
            span = rule["span"]
            anchor = f"bytes-{span['start']}-{span['end']}"
            self.assertEqual(trace.count(f'id="{anchor}"'), 1)
            self.assertIn(f"](#{anchor})", mapping)
        self.assertNotIn("<b>", report)
        self.assertNotIn("NOT IN", mapping)
        self.assertIn("NO_ASSIGNMENT_BY_PAIR", mapping)
        self.assertIn("Later unresolved effects", mapping)
        self.assertEqual(e["semantic_acceptance"], "BLOCKED")
        self.assertEqual(e["behavioral_evidence"], "UNAVAILABLE")
        self.assertEqual(e["supported_profile_reconstruction"], "NOT_RUN")
        for recover in (False, True):
            run, output = self.review(raw, lines="11:11", recover_rules=recover)
            self.assertEqual(run.returncode, 0, run.stderr)
            files = {p.name: p.read_bytes() for p in output.iterdir()}
            if not recover:
                original = files
            else:
                self.assertEqual(files, original)
