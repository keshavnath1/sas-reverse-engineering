"""PUBLIC synthetic expectations, authored without candidate code or outputs.

These are development review material, not hidden gold, SAS execution results,
or an independent semantic-acceptance campaign. See docs/P2A_FIXTURE_REVIEW.md.
The neutral obligation vocabulary deliberately does not import a parser, graph
builder, verifier, evaluator, or application package. Expected source meaning is
hand-authored here; test adapters must not replace it with candidate output.
"""


def _source(body: str) -> bytes:
    return ("/* PUBLIC SYNTHETIC FIXTURE; never executed. */\n" + body).encode("ascii")


def _input(name: str, columns: list[str], rows: list[list[str]], sorted_by=()):
    return {
        "name": name,
        "module_id": "main",
        "columns": [{"name": column, "type": "NUMERIC", "length": 8} for column in columns],
        "rows": rows,
        "sorted_by": list(sorted_by),
    }


def _fact(subject, predicate, value, line, file="main.sas"):
    return {"subject": subject, "predicate": predicate, "value": value,
            "anchor": {"file": file, "line": line}}


def _mutation(predicate, incorrect_value, reason):
    return {"predicate": predicate, "incorrect_value": incorrect_value,
            "expected_check": "FAIL", "preserve_valid_citations": True,
            "recompute_candidate_ids": True, "reason": reason}


# Each tuple-valued expression is a hand-written abstract mathematical tree.
# ('name', 'x') and ('literal', '1') are leaves, preserving literal spellings.
# This is assertion notation only, not a second factual graph or proposed IR.
PUBLIC_CASES = {
    "data_order_and_filter": {
        "files": {"main.sas": _source(
            "data work.out;\n"
            "set work.a;\n"
            "scaled = (x + 1) * 2;\n"
            "x = x + 1;\n"
            "if x >= 2;\n"
            "keep x scaled;\n"
            "run;\n")},
        "inputs": [_input("work.a", ["x"], [["0"], ["1"], ["2"]])],
        "facts": [
            _fact("work.out", "read_datasets", ["work.a"], 3),
            _fact("work.out", "assignment_order", ["scaled", "x"], 4),
            _fact("scaled", "expression", ("*", ("+", ("name", "x"), ("literal", "1")), ("literal", "2")), 4),
            _fact("x", "expression", ("+", ("name", "x"), ("literal", "1")), 5),
            _fact("work.out", "subsetting_if", {"column": "x", "operator": ">=", "literal": "2", "after_assignments": ["scaled", "x"]}, 6),
            _fact("work.out", "output_columns", ["x", "scaled"], 7),
        ],
        "hand_trace": {"columns": ["x", "scaled"], "rows": [["2", "4"], ["3", "6"]]},
        "mutations": [
            _mutation("expression", ("+", ("name", "x"), ("*", ("literal", "1"), ("literal", "2"))), "Parentheses cannot be discarded."),
            _mutation("assignment_order", ["x", "scaled"], "Reordering changes which x feeds scaled."),
            _mutation("read_datasets", [], "A valid source citation does not erase the SET dependency."),
        ],
    },
    "set_concatenation": {
        "files": {"main.sas": _source(
            "data work.concat;\nset work.a work.b;\ndoubled = x * 2;\ndrop x;\nrun;\n")},
        "inputs": [_input("work.a", ["x"], [["1"], ["2"]]),
                   _input("work.b", ["x"], [["4"]])],
        "facts": [
            _fact("work.concat", "set_mode", "CONCATENATION", 3),
            _fact("work.concat", "read_datasets", ["work.a", "work.b"], 3),
            _fact("work.concat", "input_sequence", ["work.a", "work.b"], 3),
            _fact("work.concat", "output_columns", ["doubled"], 5),
            _fact("doubled", "source_columns", ["work.a.x", "work.b.x"], 4),
        ],
        "hand_trace": {"columns": ["doubled"], "rows": [["2"], ["4"], ["8"]]},
        "mutations": [_mutation("input_sequence", ["work.b", "work.a"], "SET concatenates in declared input order.")],
    },
    "match_merge_duplicates": {
        "files": {"main.sas": _source(
            "data work.merged;\nmerge work.a work.b;\nby key;\ncombined = left_value + right_value;\nrun;\n")},
        "inputs": [_input("work.a", ["key", "left_value"], [["1", "10"], ["1", "20"]], ["key"]),
                   _input("work.b", ["key", "right_value"], [["1", "1"], ["1", "2"], ["1", "3"]], ["key"])],
        "facts": [
            _fact("work.merged", "input_mode", "SAS_MATCH_MERGE", 3),
            _fact("work.merged", "read_datasets", ["work.a", "work.b"], 3),
            _fact("work.merged", "required_input_order", ["key"], 4),
            _fact("work.merged", "cardinality_per_key", "MAX_INPUT_GROUP_COUNT", 3),
            _fact("work.merged", "exhausted_input_values", "RETAIN_WITHIN_BY_GROUP", 3),
        ],
        "hand_trace": {"columns": ["key", "left_value", "right_value", "combined"],
                       "rows": [["1", "10", "1", "11"], ["1", "20", "2", "22"], ["1", "20", "3", "23"]]},
        "mutations": [_mutation("cardinality_per_key", "PRODUCT_INPUT_GROUP_COUNTS", "This DATA match-merge has three rows, not the six SQL join pairs."),
                      _mutation("exhausted_input_values", "MISSING", "The shorter input's final value persists within this BY group.")],
    },
    "by_retain_and_sum": {
        "files": {"main.sas": _source(
            "data work.running;\nset work.a;\nby group subkey;\nretain balance 8;\n"
            "if first.group then balance = 0;\nbalance + amount;\n"
            "if last.subkey then marker = 1;\nrun;\n")},
        "inputs": [_input("work.a", ["group", "subkey", "amount"],
                          [["1", "1", "2"], ["1", "1", "."], ["2", "1", "4"]], ["group", "subkey"])],
        "facts": [
            _fact("work.running", "by_keys", ["group", "subkey"], 4),
            _fact("balance", "retain_initial_literal", "8", 5),
            _fact("balance", "reset", {"condition": "FIRST.group", "literal": "0", "before_sum": True}, 6),
            _fact("balance", "sum_state", {"retained": True, "missing_expression": "ZERO", "default_initial": "0", "explicit_initial": "8"}, 7),
            _fact("work.running", "by_prefix_effect", "EARLIER_KEY_CHANGE_STARTS_LATER_KEY_GROUP", 4),
            _fact("work.running", "state_dependency", "SELF", 7),
        ],
        "hand_trace": {"columns": ["balance", "marker", "FIRST.subkey", "LAST.subkey"],
                       "rows": [["2", ".", "1", "0"], ["2", "1", "0", "1"], ["4", "1", "1", "1"]],
                       "temporary_flags_are_output_columns": False},
        "mutations": [_mutation("sum_state", {"retained": False}, "The sum statement carries state between iterations."),
                      _mutation("reset", {"condition": "FIRST.subkey", "literal": "0"}, "The source resets on group, not subkey."),
                      _mutation("by_prefix_effect", "ONLY_CURRENT_KEY_CHANGE", "FIRST.subkey is true when group changes even if subkey remains 1.")],
    },
    "conditional_lag": {
        "files": {"main.sas": _source(
            "data work.queues;\nset work.a;\nif x > 0 then previous = lag(x);\nsecond = lag2(x);\nrun;\n")},
        "inputs": [_input("work.a", ["x"], [["1"], ["0"], ["2"], ["3"]])],
        "facts": [
            _fact("previous", "lag_queue", {"length": 1, "argument": "x", "guard": "x > 0", "advance": "ONLY_WHEN_CALLED", "by_reset": False}, 4),
            _fact("second", "lag_queue", {"length": 2, "argument": "x", "guard": None, "advance": "ONLY_WHEN_CALLED", "by_reset": False}, 5),
            _fact("work.queues", "queue_ownership", "DISTINCT_CALL_SITES", 4),
        ],
        "hand_trace": {"columns": ["previous", "second"],
                       "rows": [[".", "."], [".", "."], ["1", "1"], ["2", "0"]]},
        "mutations": [_mutation("lag_queue", {"advance": "EVERY_INPUT_ROW"}, "The guarded queue does not advance for x=0."),
                      _mutation("queue_ownership", "SHARED_BY_ARGUMENT", "Two call sites do not share one queue.")],
    },
    "sort_and_producer_consumer": {
        "files": {"main.sas": _source(
            "proc sort data=work.a out=work.sorted;\nby key subkey;\nrun;\n"
            "data work.final;\nset work.sorted;\nby key subkey;\ny = x / 2;\nrun;\n")},
        "inputs": [_input("work.a", ["key", "subkey", "x"], [["2", "1", "8"], [".", "1", "4"], ["1", "1", "2"]])],
        "facts": [
            _fact("work.sorted", "sort_order", ["key", "subkey"], 3),
            _fact("work.sorted", "tie_order", "UNSPECIFIED", 3),
            _fact("work.sorted", "numeric_missing_order", "BEFORE_FINITE_NUMBERS", 3),
            _fact("work.final", "producer_dependency", {"producer_output": "work.sorted", "consumer_input": "work.sorted", "kind": "DATA"}, 6),
            _fact("work.final", "required_input_order", ["key", "subkey"], 7),
            _fact("y", "expression", ("/", ("name", "x"), ("literal", "2")), 8),
        ],
        "hand_trace": {"columns": ["key", "subkey", "x", "y"],
                       "rows": [[".", "1", "4", "2"], ["1", "1", "2", "1"], ["2", "1", "8", "4"]]},
        "mutations": [_mutation("tie_order", "STABLE_INPUT_ORDER", "No tie-stability option or observed runtime evidence is authorized."),
                      _mutation("producer_dependency", None, "The final DATA step consumes the SORT output."),
                      _mutation("numeric_missing_order", "AFTER_FINITE_NUMBERS", "Ordinary SAS numeric missing sorts before finite numbers.")],
    },
    "sql_inner_duplicates": {
        "files": {"main.sas": _source(
            "proc sql;\ncreate table work.joined as\n"
            "select a.key as key, a.x + b.y as total\n"
            "from work.a as a inner join work.b as b on a.key = b.key\n"
            "where a.x > 0\norder by key;\nquit;\n")},
        "inputs": [_input("work.a", ["key", "x"], [["1", "2"], ["1", "4"]]),
                   _input("work.b", ["key", "y"], [["1", "1"], ["1", "2"], ["1", "3"]])],
        "facts": [
            _fact("work.joined", "join_kind", "INNER", 5),
            _fact("work.joined", "join_condition", {"left": "a.key", "operator": "=", "right": "b.key"}, 5),
            _fact("work.joined", "cardinality_per_matching_key", "PRODUCT_INPUT_GROUP_COUNTS", 5),
            _fact("total", "expression", ("+", ("name", "a.x"), ("name", "b.y")), 4),
            _fact("work.joined", "where", {"column": "a.x", "operator": ">", "literal": "0", "placement": "AFTER_JOIN"}, 6),
            _fact("work.joined", "order_by", ["key"], 7),
            _fact("work.joined", "tie_order", "UNSPECIFIED", 7),
        ],
        "hand_trace": {"row_count": 6, "unordered_total_multiset": ["3", "4", "5", "5", "6", "7"]},
        "mutations": [_mutation("cardinality_per_matching_key", "MAX_INPUT_GROUP_COUNT", "SQL joins form six qualifying pairs in this example."),
                      _mutation("tie_order", "SORTED_BY_TOTAL", "ORDER BY key gives no total ordering within this tied key.")],
    },
    "sql_left_where_and_missing": {
        "files": {"main.sas": _source(
            "proc sql;\ncreate table work.filtered as\nselect a.key as key, b.y as value\n"
            "from work.a as a left join work.b as b on a.key = b.key\nwhere b.y > 0;\nquit;\n")},
        "inputs": [_input("work.a", ["key"], [["."], ["1"], ["2"]]),
                   _input("work.b", ["key", "y"], [[".", "4"], ["1", "2"]])],
        "facts": [
            _fact("work.filtered", "join_kind", "LEFT", 5),
            _fact("work.filtered", "numeric_missing_equality", "ORDINARY_MISSING_EQUALS_ORDINARY_MISSING", 5),
            _fact("work.filtered", "where", {"column": "b.y", "operator": ">", "literal": "0", "placement": "AFTER_JOIN"}, 6),
            _fact("work.filtered", "unmatched_left_row_survival", "SUBJECT_TO_WHERE", 6),
            _fact("work.filtered", "output_order", "UNSPECIFIED", 3),
        ],
        "hand_trace": {"columns": ["key", "value"], "unordered_rows": [[".", "4"], ["1", "2"]]},
        "mutations": [_mutation("numeric_missing_equality", "SQL_NULL_NEVER_MATCHES", "Do not substitute another SQL dialect's NULL rules for SAS numeric missing."),
                      _mutation("unmatched_left_row_survival", "ALL_LEFT_ROWS_SURVIVE", "WHERE b.y>0 removes the unmatched row with missing b.y."),
                      _mutation("output_order", "INPUT_ORDER", "No ORDER BY was supplied.")],
    },
    "sql_single_source_expression": {
        "files": {"main.sas": _source(
            "proc sql;\ncreate table work.projected as\nselect (a.x + 1) / 2 as y\nfrom work.a as a\nwhere a.x ^= .\norder by y;\nquit;\n")},
        "inputs": [_input("work.a", ["x"], [["."], ["1"], ["3"]])],
        "facts": [
            _fact("work.projected", "read_datasets", ["work.a"], 5),
            _fact("y", "expression", ("/", ("+", ("name", "a.x"), ("literal", "1")), ("literal", "2")), 4),
            _fact("work.projected", "where", {"column": "a.x", "operator": "^=", "literal": ".", "placement": "BEFORE_PROJECTION"}, 6),
            _fact("work.projected", "order_by", ["y"], 7),
        ],
        "hand_trace": {"columns": ["y"], "rows": [["1"], ["2"]]},
        "mutations": [_mutation("expression", ("/", ("name", "a.x"), ("literal", "2")), "Dropping +1 changes the numeric claim while citations remain intact.")],
    },
    "literal_macro_and_include": {
        "files": {
            "main.sas": _source("%let source=work.a;\n%include 'constants.sas';\ndata work.&member.;\nset &source.;\ny = x + 1;\nrun;\n"),
            "constants.sas": _source("%let member=expanded;\n"),
        },
        "inputs": [_input("work.a", ["x"], [["1"]])],
        "facts": [
            _fact("source", "literal_binding", "work.a", 2),
            _fact("constants.sas", "include_order", "BEFORE_DATA_STEP", 3),
            _fact("member", "literal_binding", "expanded", 2, "constants.sas"),
            _fact("work.expanded", "expanded_output", {"token": "work.&member.", "value": "work.expanded", "definition_file": "constants.sas", "definition_line": 2}, 4),
            _fact("work.expanded", "expanded_input", {"token": "&source.", "value": "work.a", "definition_file": "main.sas", "definition_line": 2}, 5),
        ],
        "hand_trace": {"columns": ["x", "y"], "rows": [["1", "2"]]},
        "mutations": [_mutation("expanded_input", {"value": "work.other"}, "The literal binding resolves work.a, not another dataset."),
                      _mutation("expanded_output", {"definition_file": "main.sas"}, "A use citation cannot substitute for the included definition citation.")],
    },
    "fixed_log_observations": {
        "files": {
            "main.sas": _source("data work.out;\nset work.a;\ny = x * 2;\nrun;\n"),
            "run.log": (
                b"NOTE: There were 0 observations read from the data set WORK.A.\n"
                b"NOTE: The data set WORK.OUT has 0 observations and 2 variables.\n"
                b"WARNING: SYNTHETIC fixture warning; no SAS execution occurred.\n"
                b"real time 0.25 seconds\n"
                b"cpu time 0.125 seconds\n"
            ),
        },
        "inputs": [_input("work.a", ["x"], [])],
        "declared_bindings": [{"file": "run.log", "operation_file": "main.sas", "operation_line": 2,
                               "start_line": 1, "end_line": 5, "complete": True,
                               "execution_id": "public-synthetic-execution"}],
        "facts": [
            _fact("WORK.A", "read_count", {"lexeme": "0", "role": "INPUT_READ_COUNT"}, 1, "run.log"),
            _fact("WORK.OUT", "output_count", {"lexeme": "0", "role": "OUTPUT_ROW_COUNT"}, 2, "run.log"),
            _fact("work.out", "warning", "SYNTHETIC fixture warning; no SAS execution occurred.", 3, "run.log"),
            _fact("work.out", "real_time", {"lexeme": "0.25", "unit": "seconds", "benchmark": "NOT_RUN"}, 4, "run.log"),
            _fact("work.out", "cpu_time", {"lexeme": "0.125", "unit": "seconds", "benchmark": "NOT_RUN"}, 5, "run.log"),
        ],
        "mutations": [_mutation("output_count", {"lexeme": "1"}, "Zero is a count and must not be converted to missing or one."),
                      _mutation("real_time", {"lexeme": "0.25", "unit": "minutes"}, "The source unit is seconds, and these are fixture observations, not measured benchmarks.")],
    },
    "fixed_lst_cells": {
        "files": {
            "main.sas": _source("data work.out;\nset work.a;\ny = x * 2;\nrun;\n"),
            "run.lst": b"PUBLIC SYNTHETIC TABLE\nX    Y    \n1    2    \n.         \n",
        },
        "inputs": [_input("work.a", ["x"], [["1"], ["."]])],
        "declared_bindings": [{"file": "run.lst", "operation_file": "main.sas", "operation_line": 2,
                               "start_line": 1, "end_line": 4, "complete": True,
                               "title": "PUBLIC SYNTHETIC TABLE", "header_line": 2,
                               "data_start_line": 3, "data_end_line": 4,
                               "columns": [{"name": "X", "start": 1, "end": 5}, {"name": "Y", "start": 6, "end": 10}],
                               "execution_id": "public-synthetic-execution"}],
        "facts": [
            _fact("X", "cell", {"row": 3, "start": 1, "end": 5, "lexeme": "1", "kind": "NUMERIC"}, 3, "run.lst"),
            _fact("Y", "cell", {"row": 3, "start": 6, "end": 10, "lexeme": "2", "kind": "NUMERIC"}, 3, "run.lst"),
            _fact("X", "cell", {"row": 4, "start": 1, "end": 5, "lexeme": ".", "kind": "MISSING"}, 4, "run.lst"),
            _fact("Y", "cell", {"row": 4, "start": 6, "end": 10, "lexeme": "", "kind": "BLANK"}, 4, "run.lst"),
        ],
        "mutations": [_mutation("cell", {"row": 4, "column": "Y", "kind": "MISSING"}, "A blank cell and an explicit period are different observations."),
                      _mutation("cell", {"row": 3, "column": "Y", "lexeme": "4"}, "The citation is valid, but the observed cell says 2.")],
    },
}


# A boundary fixture is not a claim that SAS itself rejects the syntax. It says
# this approved closed subset cannot completely reconstruct it. A structural
# input failure may be FAIL; otherwise unsupported semantics must be BLOCKED,
# with a cited unknown and no semantic-acceptance promotion.
_BOUNDARIES = [
    ("lexical_unclosed", "data work.out; set work.a; /* unfinished", "Unclosed comment"),
    ("lexical_macro_statement_comment", "* &unresolved; data work.out; set work.a; run;", "Statement comment can invoke macro processing"),
    ("lexical_unbalanced_comment_quote", "* 'unbalanced; data work.out; set work.a; run;", "Unsafe statement-comment framing"),
    ("name_literal", "data work.'odd name'n; set work.a; run;", "Name literal"),
    ("implicit_libref", "data out; set work.a; run;", "Dataset lacks explicit WORK libref"),
    ("external_libref", "data work.out; set secret.a; run;", "External library"),
    ("dataset_option", "data work.out; set work.a(obs=1); run;", "Dataset option"),
    ("dataset_overwrite", "data work.a; set work.a; run;", "Input/output dataset overwrite"),
    ("repeated_output", "data work.out; set work.a; run; data work.out; set work.a; run;", "Repeated output name"),
    ("data_loop", "data work.out; set work.a; do i=1 to 2; x=x+1; end; run;", "DO loop"),
    ("data_array", "data work.out; set work.a; array a[1] x; run;", "Array"),
    ("data_multi_output", "data work.out work.extra; set work.a; run;", "Multiple outputs"),
    ("data_explicit_output", "data work.out; set work.a; output; run;", "Explicit OUTPUT"),
    ("data_delete", "data work.out; set work.a; delete; run;", "DELETE"),
    ("data_stop", "data work.out; set work.a; stop; run;", "STOP"),
    ("data_chained_comparison", "data work.out; set work.a; if 0 < x < 2; run;", "Chained comparison"),
    ("data_function", "data work.out; set work.a; y=sqrt(x); run;", "Arbitrary function"),
    ("data_character_arithmetic", "data work.out; set work.a; y='1'+x; run;", "Implicit conversion"),
    ("data_compound_condition", "data work.out; set work.a; if x>0 and x<2; run;", "Compound predicate"),
    ("data_else", "data work.out; set work.a; if x>0 then y=1; else y=0; run;", "ELSE"),
    ("set_multiple_statements", "data work.out; set work.a; set work.b; run;", "Multiple SET statements"),
    ("set_conditional", "data work.out; if x>0 then set work.a; run;", "Conditional SET"),
    ("set_point", "data work.out; set work.a point=i; run;", "POINT access"),
    ("set_name_range", "data work.out; set work.a1-work.a3; run;", "Dataset name range"),
    ("set_interleaving", "data work.out; set work.a work.b; by key; run;", "Multi-input SET with BY"),
    ("merge_no_by", "data work.out; merge work.a work.b; run;", "MERGE without BY"),
    ("merge_three_inputs", "data work.out; merge work.a work.b work.c; by key; run;", "Three-way merge"),
    ("merge_in_option", "data work.out; merge work.a(in=a) work.b; by key; run;", "IN dataset option"),
    ("by_descending", "data work.out; set work.a; by descending key; run;", "Descending BY"),
    ("by_notsorted", "data work.out; set work.a; by key notsorted; run;", "NOTSORTED"),
    ("by_groupformat", "data work.out; set work.a; by key groupformat; run;", "GROUPFORMAT"),
    ("by_three_keys", "data work.out; set work.a; by key subkey x; run;", "More than two keys"),
    ("retain_multiple", "data work.out; set work.a; retain x y 0; run;", "Multiple-name RETAIN"),
    ("lag_computed", "data work.out; set work.a; y=lag(x+1); run;", "Computed LAG argument"),
    ("lag_nested", "data work.out; set work.a; y=lag(lag(x)); run;", "Nested LAG"),
    ("lag_arithmetic", "data work.out; set work.a; y=lag(x)+1; run;", "LAG not whole RHS"),
    ("lag3", "data work.out; set work.a; y=lag3(x); run;", "Unsupported queue length"),
    ("sort_nodup", "proc sort data=work.a out=work.out nodupkey; by key; run;", "NODUP option"),
    ("sort_in_place", "proc sort data=work.a; by key; run;", "In-place sort"),
    ("sql_star", "proc sql; create table work.out as select * from work.a as a; quit;", "SELECT star"),
    ("sql_aggregate", "proc sql; create table work.out as select sum(a.x) as y from work.a as a; quit;", "Aggregate"),
    ("sql_distinct", "proc sql; create table work.out as select distinct a.x as y from work.a as a; quit;", "DISTINCT"),
    ("sql_subquery", "proc sql; create table work.out as select a.x as y from (select x from work.a) as a; quit;", "Subquery"),
    ("sql_union", "proc sql; create table work.out as select a.x as y from work.a as a union select b.x as y from work.b as b; quit;", "UNION"),
    ("sql_into", "proc sql; select a.x into :value from work.a as a; quit;", "INTO"),
    ("sql_dml", "proc sql; delete from work.a; quit;", "DML"),
    ("sql_pass_through", "proc sql; connect to odbc; quit;", "Pass-through"),
    ("sql_missing_alias", "proc sql; create table work.out as select a.x from work.a as a; quit;", "Missing output alias"),
    ("sql_implicit_input_alias", "proc sql; create table work.out as select a.x as x from work.a a; quit;", "Implicit input alias"),
    ("sql_order_position", "proc sql; create table work.out as select a.x as x from work.a as a order by 1; quit;", "Ordinal ORDER BY"),
    ("sql_right_join", "proc sql; create table work.out as select a.x as x from work.a as a right join work.b as b on a.key=b.key; quit;", "RIGHT JOIN"),
    ("sql_multiple_creates", "proc sql; create table work.out as select a.x as x from work.a as a; create table work.other as select a.x as x from work.a as a; quit;", "Multiple CREATE statements"),
    ("macro_definition", "%macro build; data work.out; set work.a; run; %mend; %build;", "Macro definition/call"),
    ("macro_reassignment", "%let member=one; %let member=two; data work.&member; set work.a; run;", "Reassigned binding"),
    ("macro_nested", "%let member=a; data work.out; set work.&&member; run;", "Repeated macro expansion"),
    ("macro_sysfunc", "%let member=%sysfunc(today());", "SYSFUNC"),
    ("macro_quoting", "%let member=%str(a);", "Macro quoting function"),
    ("macro_conditional", "%if 1 %then %do; %let member=a; %end;", "Macro control flow"),
    ("macro_dynamic_binding", "data work.out; set work.a; call symputx('member','a'); run;", "Runtime symbol assignment"),
    ("include_dynamic", "%let member=constants.sas; %include '&member';", "Macro-built include path"),
    ("include_missing", "%include 'absent.sas';", "Target absent from authorized scope"),
    ("include_traversal", "%include '../outside.sas';", "Traversal must never expand scope"),
    ("include_repeat", "%include 'constants.sas'; %include 'constants.sas';", "Repeated include"),
    ("numeric_exponent", "data work.out; set work.a; y=x+1e2; run;", "Exponent literal"),
    ("numeric_special_missing", "data work.out; set work.a; y=.A; run;", "Special missing"),
    ("numeric_decimal_rounding", "data work.out; set work.a; y=x+0.1; run;", "Nondyadic finite literal outside exact profile"),
    ("numeric_division_zero", "data work.out; set work.a; y=x/0; run;", "Zero divisor"),
    ("numeric_division_nondyadic", "data work.out; set work.a; y=x/3; run;", "Non-power-of-two divisor"),
    ("numeric_large_literal", "data work.out; set work.a; y=x+1048577; run;", "Literal above approved magnitude bound"),
    ("numeric_format", "data work.out; set work.a; format x date9.; run;", "FORMAT/date interpretation"),
]

UNSUPPORTED_CASES = [
    {"id": case_id, "files": {"main.sas": _source(source + "\n")},
     "reason": reason, "expected_semantic_acceptance": "BLOCKED"}
    for case_id, source, reason in _BOUNDARIES
]

# Non-syntactic evidence gaps and observation format boundaries need context,
# rather than pretending one source snippet alone proves the missing condition.
EVIDENCE_BOUNDARIES = [
    {"id": "unknown_input_schema", "based_on": "data_order_and_filter", "change": "omit work.a declaration", "reason": "Unknown source columns/attributes"},
    {"id": "unknown_merge_order", "based_on": "match_merge_duplicates", "change": "clear both sorted_by declarations", "reason": "BY does not establish sorted input"},
    {"id": "shared_merge_nonkey", "based_on": "match_merge_duplicates", "change": "give both inputs a column named value", "reason": "Overlapping nonkey variables"},
    {"id": "unknown_by_order", "based_on": "by_retain_and_sum", "change": "clear sorted_by declaration", "reason": "Missing sortedness evidence"},
    {"id": "non_numeric_key", "based_on": "by_retain_and_sum", "change": "declare group CHARACTER", "reason": "Unsupported key type/collation"},
    {"id": "include_cycle", "files": {"main.sas": _source("%include 'constants.sas';\n"), "constants.sas": _source("%include 'main.sas';\n")}, "reason": "Include cycle"},
    {"id": "unassociated_log", "based_on": "fixed_log_observations", "change": "omit explicit log association", "reason": "Filename match cannot establish provenance"},
    {"id": "unbound_log_step", "based_on": "fixed_log_observations", "change": "omit step binding", "reason": "No operation association"},
    {"id": "incomplete_log", "based_on": "fixed_log_observations", "change": "set complete false", "reason": "Missing completion evidence"},
    {"id": "log_minutes", "based_on": "fixed_log_observations", "replacement": b"real time 0.25 minutes\n", "reason": "Unapproved unit"},
    {"id": "log_error", "based_on": "fixed_log_observations", "replacement": b"ERROR: SYNTHETIC failure.\n", "reason": "ERROR cannot be treated as successful execution"},
    {"id": "log_other_language", "based_on": "fixed_log_observations", "replacement": b"TEMPS 0.25 secondes\n", "reason": "Non-English/unrecognized template"},
    {"id": "lst_title_mismatch", "based_on": "fixed_lst_cells", "change": "replace first line with unexpected title", "reason": "Declared layout mismatch"},
    {"id": "lst_extra_page", "based_on": "fixed_lst_cells", "change": "append another title/header/table", "reason": "Pagination outside fixed layout"},
    {"id": "lst_unbound", "based_on": "fixed_lst_cells", "change": "omit explicit listing association", "reason": "Unbound LST evidence"},
    {"id": "lst_non_numeric", "based_on": "fixed_lst_cells", "change": "replace a numeric cell with text", "reason": "Unsupported cell interpretation"},
]

EXPECTATION_REVIEW = {
    "author": "p2a_public_expectations subagent",
    "author_read_candidate_implementation": False,
    "author_read_candidate_outputs": False,
    "status": "REVIEWED_FOR_PUBLIC_DEVELOPMENT",
    "reviewer": "root agent, separate from expectation author",
    "review_record": "docs/P2A_FIXTURE_REVIEW.md",
    "visibility": "PUBLIC_DEVELOPMENT",
    "sas_execution": "NOT_RUN",
    "semantic_acceptance": "BLOCKED",
}
