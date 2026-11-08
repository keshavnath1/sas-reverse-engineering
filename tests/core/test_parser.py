"""Synthetic parser mechanics check syntax, original source locations, and refusal boundaries.

These inputs do not establish independently accepted SAS semantics."""

from unittest.mock import patch
import unittest

from sas_re.sas_subset import parse_source


class SasSubsetMechanicsTests(unittest.TestCase):
    def parse(self, value, **kwargs):
        return parse_source(value, file_key="synthetic:main.sas", **kwargs)

    def codes(self, result):
        return {issue["code"] for issue in result["issues"]}

    def test_parse_never_opens_files_executes_or_calls_subprocess(self):
        with (
            patch("builtins.open", side_effect=AssertionError("file access")),
            patch("subprocess.run", side_effect=AssertionError("execution")),
        ):
            result = self.parse(b"data work.b; set work.a; x=x+1; run;")
        self.assertEqual(result["semantic_verification"], "UNVERIFIABLE")
        self.assertEqual(result["semantic_acceptance"], "BLOCKED")

    def test_original_multibyte_and_mixed_newline_locations(self):
        data = "/* synthetic café */\r\ndata work.b;\rset work.a;\nx=x+1;\r\nrun;".encode()
        result = self.parse(data)
        self.assertFalse(result["issues"])
        statements = result["statements"]
        self.assertEqual(len(statements), 5)
        self.assertEqual(statements[2]["span"]["line_start"], 3)
        self.assertEqual(result["operations"][0]["span"]["start"], data.index(b"data"))
        self.assertEqual(result["operations"][0]["span"]["line_start"], 2)
        for statement in statements[1:]:
            span = statement["span"]
            self.assertTrue(data[span["start"] : span["end"]].endswith(b";"))
        expr = result["operations"][0]["facts"][2]["expression"]
        self.assertEqual(data[expr["span"]["start"] : expr["span"]["end"]], b"x+1")

    def test_literal_spelling_parentheses_and_order_preserved(self):
        result = self.parse(b"data work.b; set work.a; y=(X+0002)*3-4; z=1; run;")
        facts = result["operations"][0]["facts"]
        self.assertEqual(
            [f["kind"] for f in facts], ["output", "input", "assignment", "assignment"]
        )
        expression = facts[2]["expression"]
        self.assertEqual(expression["operator"], "-")
        group = expression["left"]["left"]
        self.assertEqual(group["kind"], "group")
        self.assertEqual(group["expression"]["left"]["lexeme"], "X")
        self.assertEqual(group["expression"]["right"]["lexeme"], "0002")

    def test_comment_and_malformed_tail_are_accounted(self):
        data = b"* safe comment; %* balanced 'quoted' comment; data work.b; set work.a; x=1"
        result = self.parse(data)
        self.assertEqual(result["statements"][0]["classification"], "COMMENT")
        self.assertEqual(result["statements"][1]["classification"], "COMMENT")
        self.assertEqual(result["statements"][-1]["span"]["end"], len(data))
        self.assertTrue({"MISSING_SEMICOLON", "UNTERMINATED_BLOCK"} <= self.codes(result))

    def test_unsafe_comments_cannot_disappear(self):
        for value in (
            b"* &hidden;",
            b"* %let x=y;",
            b"* 'bad;",
            b"/* nested /* comment */ */",
            b"* 'semi;colon';",
        ):
            with self.subTest(value=value):
                self.assertTrue(self.parse(value)["issues"])

    def test_invalid_utf8_has_original_byte_range(self):
        data = b"x=\xff;\r\n"
        result = self.parse(data)
        self.assertIn("UNSUPPORTED_ENCODING", self.codes(result))
        self.assertEqual(result["issues"][0]["span"]["end"], len(data))
        self.assertEqual(result["issues"][0]["span"]["line_end"], 1)

    def test_include_uses_only_explicit_callback_and_blocks_missing_target(self):
        called = []

        def loader(file_key, relative):
            called.append((file_key, relative))
            raise KeyError(relative)

        result = self.parse(b'%include "missing.sas";', include_loader=loader)
        self.assertEqual(called, [("synthetic:main.sas", "missing.sas")])
        self.assertIn("UNRESOLVED_INCLUDE", self.codes(result))

    def test_unsafe_and_dynamic_include_paths_never_reach_loader(self):
        for path in (
            "../escape.sas",
            "/tmp/out.sas",
            "sub/../escape.sas",
            "a\\b.sas",
            "&path",
            "a//b.sas",
        ):
            with self.subTest(path=path):
                with patch("builtins.open", side_effect=AssertionError("file access")):
                    result = self.parse(
                        f'%include "{path}";'.encode(),
                        include_loader=lambda *_: self.fail("unsafe path reached loader"),
                    )
                self.assertIn("UNSAFE_INCLUDE", self.codes(result))

    def test_include_macro_bindings_are_temporal_and_keep_definition_anchor(self):
        result = self.parse(
            b'%include "defs.sas"; data work.&out; set work.a; run;',
            include_loader=lambda *_: ("synthetic:defs.sas", b"%let out=b;"),
        )
        self.assertFalse(result["issues"])
        use = result["operations"][-1]["facts"][0]
        self.assertEqual(use["definition_span"]["file_key"], "synthetic:defs.sas")
        self.assertEqual(use["span"]["file_key"], "synthetic:main.sas")
        earlier = self.parse(b"data work.&out; set work.a; run; %let out=b;")
        self.assertIn("UNRESOLVED_MACRO", self.codes(earlier))

    def test_include_fragments_keep_original_spans_and_statement_order(self):
        result = self.parse(
            b'data work.b; set work.a; %include "body.sas"; z=x+2; run;',
            include_loader=lambda *_: ("synthetic:body.sas", b"y=x+1;"),
        )
        self.assertFalse(result["issues"])
        operation = next(o for o in result["operations"] if o["kind"] == "DATA_STEP")
        assignments = [f for f in operation["facts"] if f["kind"] == "assignment"]
        self.assertEqual([f["target"] for f in assignments], ["y", "z"])
        self.assertEqual(assignments[0]["span"]["file_key"], "synthetic:body.sas")
        self.assertEqual(operation["span"]["file_key"], "synthetic:main.sas")

    def test_block_can_continue_across_include_boundaries_without_fabricated_spans(self):
        cases = [
            (b'%include "part.sas"; x=1; run;', b"data work.b; set work.a;"),
            (b'data work.b; set work.a; %include "part.sas";', b"x=1; run;"),
        ]
        for main, part in cases:
            with self.subTest(main=main):
                result = self.parse(main, include_loader=lambda *_: ("synthetic:part.sas", part))
                self.assertFalse(result["issues"])
                for op in result["operations"]:
                    span = op["span"]
                    raw = main if span["file_key"] == "synthetic:main.sas" else part
                    self.assertLessEqual(span["end"], len(raw))

    def test_include_cycles_and_repeats_remain_unresolved(self):
        cycle = self.parse(
            b'%include "main.sas";', include_loader=lambda *_: ("synthetic:main.sas", b"")
        )
        self.assertIn("INCLUDE_CYCLE", self.codes(cycle))
        repeat = self.parse(
            b'%include "part.sas"; %include "part.sas";',
            include_loader=lambda *_: ("synthetic:part.sas", b"* synthetic;"),
        )
        self.assertIn("REPEATED_INCLUDE", self.codes(repeat))

    def test_macro_reassignment_invalidates_prior_value(self):
        result = self.parse(b"%let out=a; %let out=b; data work.&out; set work.c; run;")
        self.assertTrue({"MACRO_REASSIGNMENT", "UNRESOLVED_MACRO"} <= self.codes(result))
        for middle in (b"* %let out=b;", b"%unknown_macro;", b'%include "missing.sas";'):
            with self.subTest(middle=middle):
                changed = self.parse(
                    b"%let out=a; " + middle + b" data work.&out; set work.c; run;"
                )
                self.assertIn("UNRESOLVED_MACRO", self.codes(changed))

    def test_numeric_and_expression_budgets_refuse_without_crashing(self):
        values = [
            b"1" * 5000,
            b"(" * 70 + b"1" + b")" * 70,
            b"+".join([b"x"] * 2000),
            b"0.1",
            b"x/3",
            b"x/y",
        ]
        for expression in values:
            with self.subTest(length=len(expression)):
                self.assertTrue(
                    self.parse(b"data work.b; set work.a; y=" + expression + b"; run;")["issues"]
                )

    def test_case_operation_budget_accounts_for_remaining_bytes(self):
        source = b"".join(f"%let v{i}=x;".encode() for i in range(103))
        result = self.parse(source)
        self.assertIn("PARSER_LIMIT", self.codes(result))
        self.assertEqual(result["statements"][-1]["span"]["end"], len(source))
        self.assertLessEqual(len(result["operations"]), 101)

    def test_line_budget_blocks_instead_of_truncating(self):
        source = b"\n" * 10001 + b"data work.b; set work.a; run;"
        result = self.parse(source)
        self.assertIn("SOURCE_LIMIT", self.codes(result))
        self.assertEqual(result["statements"][0]["span"]["end"], len(source))

    def test_excluded_data_syntax_is_explicitly_blocked(self):
        # Each spelling is an invented syntax boundary challenge, not a gold
        # interpretation of a SAS program or an observed execution result.
        bodies = [
            b"do i=1 to 2;",
            b"array a[2] x y;",
            b"output;",
            b"delete;",
            b"stop;",
            b"x=sum(y,z);",
            b"x=1e3;",
            b"x=.A;",
            b"x='1';",
            b"x=lag(y)+1;",
            b"x=lag(y+1);",
            b"if x>1 and y>2 then z=1;",
            b"if 0<x<2;",
            b"if x>0 then do;",
            b"retain x y 0;",
            b"keep x:;",
            b"by descending x;",
            b"by x notsorted;",
            b"by x groupformat;",
            b"set work.c;",
            b"%let x=y;",
        ]
        for body in bodies:
            with self.subTest(body=body):
                self.assertTrue(
                    self.parse(b"data work.b; set work.a; " + body + b" run;")["issues"]
                )

    def test_excluded_input_sort_and_macro_forms_are_explicitly_blocked(self):
        sources = [
            b"data work.b work.c; set work.a; run;",
            b"data b; set work.a; run;",
            b"data work.b; set work.a(keep=x); run;",
            b"data work.b; merge work.a work.c; run;",
            b"data work.b; set work.a work.c; by x; run;",
            b"proc sort data=work.a; by id; run;",
            b"proc sort data=work.a out=work.a; by id; run;",
            b"proc sort data=work.a out=work.b nodupkey; by id; run;",
            b"%macro a; %mend;",
            b"%if a %then b;",
            b"%let x=&y;",
            b"%let x='a';",
            b"data work.b; set work.a; run; data work.b; set work.c; run;",
        ]
        for source in sources:
            with self.subTest(source=source):
                self.assertTrue(self.parse(source)["issues"])

    def test_data_by_must_follow_its_input_even_across_include_fragments(self):
        # Official SAS BY-statement reference binds BY to the preceding input
        # statement; this checks the syntax-order refusal, not SAS execution.
        for input_statement in (b"set work.a;", b"merge work.a work.c;"):
            with self.subTest(input_statement=input_statement):
                bad = self.parse(b"data work.b; by id; " + input_statement + b" run;")
                self.assertIn("BY_PRECEDES_INPUT", self.codes(bad))
                good = self.parse(b"data work.b; " + input_statement + b" by id; run;")
                self.assertNotIn("BY_PRECEDES_INPUT", self.codes(good))
        included = self.parse(
            b'data work.b; %include "keys.sas"; set work.a; run;',
            include_loader=lambda *_: ("synthetic:keys.sas", b"by id;"),
        )
        issue = next(i for i in included["issues"] if i["code"] == "BY_PRECEDES_INPUT")
        self.assertEqual(issue["span"]["file_key"], "synthetic:keys.sas")

    def test_excluded_sql_syntax_is_explicitly_blocked(self):
        queries = [
            b"select * from work.a as a",
            b"select distinct a.x as x from work.a as a",
            b"select sum(a.x) as x from work.a as a",
            b"select a.x from work.a as a",
            b"select a.x as x from work.a a",
            b"select a.x as x from work.a as a union select b.x as x from work.b as b",
            b"select a.x as x from work.a as a where a.x>0 and a.x<2",
            b"select a.x as x from work.a as a order by 1",
            b"select a.x as x from work.a as a order by x desc",
            b"select a.x as x from work.a as a inner join work.b as b on a.x=b.x and a.y=b.y",
            b"select a.x as x from work.a as a left join work.b as a on a.x=a.x",
            b"select missing.x as x from work.a as a",
        ]
        for query in queries:
            with self.subTest(query=query):
                self.assertTrue(
                    self.parse(b"proc sql; create table work.b as " + query + b"; quit;")["issues"]
                )


if __name__ == "__main__":
    unittest.main()
