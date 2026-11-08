"""Independently reviewed public reconstruction cases and counterclaims preserve blocked semantic authority."""

from copy import deepcopy
import hashlib
from pathlib import Path
import tempfile
import unittest

from support.paths import REPOSITORY_ROOT as ROOT
from sas_re.contracts import validate_contract
from sas_re.evidence import build_inventory, record_id
from sas_re.safeio import EvidenceError
from sas_re.semantic import reconstruct, validate_v2

from p2a_expectations import (
    EVIDENCE_BOUNDARIES,
    EXPECTATION_REVIEW,
    PUBLIC_CASES,
    UNSUPPORTED_CASES,
)
from p2a_support import (
    PROFILE_KEY,
    all_citations,
    anchored_operation,
    condition,
    dataset_operation,
    facts_of,
    make_case,
    prepare_case,
    reidentify,
    tree,
)


def _one(items):
    if len(items) != 1:
        raise AssertionError("Expected one matching canonical record, got " + str(len(items)))
    return items[0]


def assert_fact(test, case, graph, profile, expected):
    """Compare candidate fields to separately reviewed public obligations."""
    predicate, subject, value = expected["predicate"], expected["subject"], expected["value"]
    if expected["anchor"]["file"].endswith((".log", ".lst")):
        anchor = expected["anchor"]
        observations = [
            o
            for o in graph["log_observations"]
            if o["log_citation"]["file_key"] == "synthetic:" + anchor["file"]
            and o["log_citation"]["line_start"] == anchor["line"]
        ]
        metric = {
            "read_count": "READ_ROWS",
            "output_count": "OUTPUT_ROWS",
            "warning": "WARNING_COUNT",
            "real_time": "ELAPSED_SECONDS",
            "cpu_time": "CPU_SECONDS",
            "cell": "LST_CELL",
        }[predicate]
        observation = _one(
            [
                o
                for o in observations
                if o["metric"] == metric and (predicate != "cell" or o["column"] == subject)
            ]
        )
        if predicate == "warning":
            test.assertEqual(observation["value_lexeme"], "1")
            raw_line = case["files"][anchor["file"]].splitlines()[anchor["line"] - 1].decode()
            test.assertEqual(raw_line.removeprefix("WARNING: "), value)
        else:
            test.assertEqual(observation["value_lexeme"].strip(), value["lexeme"])
        if predicate in {"read_count", "output_count"}:
            test.assertEqual(observation["dataset"], subject.lower())
            test.assertEqual(observation["unit"], "rows")
            test.assertEqual(
                value["role"], "INPUT_READ_COUNT" if metric == "READ_ROWS" else "OUTPUT_ROW_COUNT"
            )
        elif predicate in {"real_time", "cpu_time"}:
            test.assertEqual(observation["unit"], value["unit"])
            test.assertEqual(graph["benchmark_execution"], value["benchmark"])
        elif predicate == "cell":
            test.assertEqual(
                {"NUMBER": "NUMERIC", "MISSING": "MISSING", "BLANK": "BLANK"}[
                    observation["cell_kind"]
                ],
                value["kind"],
            )
            binding = _one(profile["lst_bindings"])
            column = _one([c for c in binding["columns"] if c["name"] == subject])
            test.assertEqual((column["start"], column["end"]), (value["start"], value["end"]))
            test.assertEqual(observation["row"] + binding["data_start_line"] - 1, value["row"])
        return
    op = anchored_operation(graph, expected)
    facts = op["facts"]
    inp = next(iter(facts_of(op, "input")), None)
    sql = next(iter(facts_of(op, "sql")), None)
    if predicate == "read_datasets":
        ids = {d["dataset_id"]: d["name"] for d in graph["datasets"]}
        test.assertCountEqual([ids[n] for n in op["reads"] if n in ids], value)
    elif predicate == "assignment_order":
        test.assertEqual([f["target"] for f in facts_of(op, "assignment")], value)
    elif predicate == "expression":
        expression = (
            _one([s["expression"] for s in sql["select"] if s["output"] == subject])
            if sql
            else _one(
                [f["expression"] for f in facts_of(op, "assignment") if f["target"] == subject]
            )
        )
        test.assertEqual(tree(expression), value)
    elif predicate == "subsetting_if":
        fact = _one(facts_of(op, "subset_if"))
        test.assertEqual(
            condition(fact["condition"]), {k: value[k] for k in ("column", "operator", "literal")}
        )
        test.assertEqual(
            [f["target"] for f in facts[: facts.index(fact)] if f["kind"] == "assignment"],
            value["after_assignments"],
        )
    elif predicate == "output_columns":
        ds = _one([d for d in graph["datasets"] if d["name"] == subject])
        test.assertEqual(
            [c["name"] for c in graph["columns"] if c["dataset_id"] == ds["dataset_id"]], value
        )
    elif predicate in {"input_sequence", "set_mode"}:
        test.assertEqual(inp["mode"], "SET")
        test.assertEqual(
            inp["datasets"], value if predicate == "input_sequence" else ["work.a", "work.b"]
        )
        test.assertEqual(op["order_contract"]["kind"], "CONCATENATION_ORDER")
    elif predicate == "source_columns":
        columns = {c["column_id"]: c for c in graph["columns"]}
        datasets = {d["dataset_id"]: d for d in graph["datasets"]}
        lineage = _one(
            [f for f in op["lineage"] if columns[f["output_column_id"]]["name"] == subject]
        )
        names = [
            datasets[columns[n]["dataset_id"]]["name"] + "." + columns[n]["name"]
            for n in lineage["input_column_ids"]
        ]
        test.assertCountEqual(names, value)
    elif predicate == "input_mode":
        test.assertEqual(inp["mode"], "MERGE")
        test.assertEqual(value, "SAS_MATCH_MERGE")
    elif predicate in {"required_input_order", "by_keys"}:
        test.assertEqual(op["order_contract"]["keys"], value)
        test.assertTrue(op["order_contract"]["requires_sorted_inputs"])
        test.assertNotEqual(op["order_contract"]["precondition"], "UNRESOLVED")
    elif predicate in {"cardinality_per_key", "cardinality_per_matching_key"}:
        test.assertEqual(
            op["cardinality"],
            {
                "MAX_INPUT_GROUP_COUNT": "MATCH_MERGE_MAX_PER_BY_GROUP_OR_SUBSET",
                "PRODUCT_INPUT_GROUP_COUNTS": "SQL_JOIN_MULTIPLICITY_OR_SUBSET",
            }[value],
        )
    elif predicate == "exhausted_input_values":
        state = _one([s for s in op["state_effects"] if s["kind"] == "MERGE"])
        test.assertEqual((state["persistence"], state["reset"]), ("WITHIN_BY_GROUP", "BY_GROUP"))
        test.assertEqual(value, "RETAIN_WITHIN_BY_GROUP")
    elif predicate == "retain_initial_literal":
        test.assertEqual(
            _one([f for f in facts_of(op, "retain") if f["target"] == subject])["initial"][
                "lexeme"
            ],
            value,
        )
    elif predicate == "reset":
        reset = _one([f for f in facts_of(op, "assignment") if f["target"] == subject])
        test.assertEqual(condition(reset["guard"]), value["condition"])
        test.assertEqual(reset["expression"]["lexeme"], value["literal"])
        test.assertEqual(
            facts.index(reset) < facts.index(_one(facts_of(op, "sum"))), value["before_sum"]
        )
    elif predicate == "sum_state":
        state = _one(
            [s for s in op["state_effects"] if s["kind"] == "SUM" and s["target"] == subject]
        )
        test.assertEqual(state["persistence"] == "ACROSS_ROWS", value["retained"])
        test.assertEqual(state["initialization"], "ZERO_UNLESS_RETAIN_INITIALIZED")
        test.assertEqual(value["default_initial"], "0")
        test.assertEqual(
            op["numeric_policy"]["missing_arithmetic"], "PROPAGATE_EXCEPT_SUM_STATEMENT"
        )
        test.assertEqual(value["missing_expression"], "ZERO")
        test.assertEqual(
            _one(facts_of(op, "retain"))["initial"]["lexeme"], value["explicit_initial"]
        )
    elif predicate == "by_prefix_effect":
        state = _one([s for s in op["state_effects"] if s["kind"] == "BY"])
        test.assertEqual(
            (state["persistence"], state["reset"]), ("BY_KEY_PREFIX", "KEY_PREFIX_CHANGE")
        )
        test.assertEqual(value, "EARLIER_KEY_CHANGE_STARTS_LATER_KEY_GROUP")
    elif predicate == "state_dependency":
        test.assertEqual(value, "SELF")
        test.assertTrue(
            any(
                e["type"] == "STATE"
                and e["from_operation_id"] == e["to_operation_id"] == op["operation_id"]
                for e in graph["edges"]
            )
        )
    elif predicate == "lag_queue":
        state = _one(
            [s for s in op["state_effects"] if s["kind"] == "LAG" and s["target"] == subject]
        )
        fact = facts[state["fact_index"]]
        test.assertEqual(state["queue_size"], value["length"])
        test.assertEqual(fact["expression"]["argument"]["name"], value["argument"])
        test.assertEqual(state["call_policy"], "EXECUTED_CALLS_ONLY")
        test.assertEqual(value["advance"], "ONLY_WHEN_CALLED")
        test.assertEqual(state["reset"] != "NONE_IMPLICIT", value["by_reset"])
        if value["guard"] is None:
            test.assertIsNone(state["guard"])
        else:
            guard = condition(state["guard"])
            test.assertEqual("{column} {operator} {literal}".format(**guard), value["guard"])
    elif predicate == "queue_ownership":
        states = [s for s in op["state_effects"] if s["kind"] == "LAG"]
        test.assertEqual(len(states), 2)
        test.assertEqual(len({s["fact_index"] for s in states}), 2)
        test.assertEqual(value, "DISTINCT_CALL_SITES")
    elif predicate in {
        "sort_order",
        "order_by",
        "tie_order",
        "numeric_missing_order",
        "output_order",
    }:
        if predicate == "sort_order":
            test.assertEqual(_one(facts_of(op, "sort"))["keys"], value)
            test.assertEqual(op["order_contract"]["keys"], value)
        elif predicate == "order_by":
            test.assertEqual(sql["order_by"], value)
            test.assertEqual(op["order_contract"]["keys"], value)
        elif predicate == "tie_order":
            test.assertEqual(op["order_contract"]["tie_order"], value)
        elif predicate == "numeric_missing_order":
            test.assertEqual(op["numeric_policy"]["missing_order"], "ORDINARY_MISSING_BELOW_FINITE")
            test.assertEqual(value, "BEFORE_FINITE_NUMBERS")
        else:
            test.assertEqual(op["order_contract"]["kind"], value)
            test.assertEqual(sql["order_by"], [])
    elif predicate == "producer_dependency":
        producer = dataset_operation(graph, value["producer_output"])
        consumer = dataset_operation(graph, subject)
        test.assertTrue(
            any(
                e["type"] == value["kind"]
                and e["from_operation_id"] == producer["operation_id"]
                and e["to_operation_id"] == consumer["operation_id"]
                for e in graph["edges"]
            )
        )
    elif predicate == "join_kind":
        test.assertEqual(sql["join"]["kind"], value)
    elif predicate == "join_condition":
        test.assertEqual(sql["join"]["left"]["name"], value["left"])
        test.assertEqual(sql["join"]["right"]["name"], value["right"])
        test.assertEqual(value["operator"], "=")
    elif predicate == "where":
        test.assertEqual(
            condition(sql["where"]), {k: value[k] for k in ("column", "operator", "literal")}
        )
        test.assertEqual("AFTER_JOIN" if sql["join"] else "BEFORE_PROJECTION", value["placement"])
    elif predicate == "numeric_missing_equality":
        test.assertEqual(
            op["numeric_policy"]["missing_join"], "SAS_ORDINARY_MISSING_EQUALS_MISSING"
        )
        test.assertEqual(value, "ORDINARY_MISSING_EQUALS_ORDINARY_MISSING")
    elif predicate == "unmatched_left_row_survival":
        test.assertEqual(sql["join"]["kind"], "LEFT")
        test.assertIsNotNone(sql["where"])
        test.assertEqual(value, "SUBJECT_TO_WHERE")
    elif predicate == "literal_binding":
        binding = _one([f for f in facts_of(op, "macro_binding") if f["name"] == subject])
        test.assertEqual(binding["value"], value)
    elif predicate == "include_order":
        test.assertEqual(_one(facts_of(op, "include"))["target_file_key"], "synthetic:" + subject)
        test.assertLess(op["sequence"], dataset_operation(graph, "work.expanded")["sequence"])
        test.assertEqual(value, "BEFORE_DATA_STEP")
    elif predicate in {"expanded_output", "expanded_input"}:
        use = _one(
            [
                f
                for f in facts_of(op, "macro_use")
                if f["span"]["line_start"] == expected["anchor"]["line"]
            ]
        )
        span = use["span"]
        test.assertEqual(
            case["files"][expected["anchor"]["file"]][span["start"] : span["end"]].decode(),
            value["token"],
        )
        test.assertEqual(
            use["definition_span"]["file_key"], "synthetic:" + value["definition_file"]
        )
        test.assertEqual(use["definition_span"]["line_start"], value["definition_line"])
        test.assertEqual(
            _one(facts_of(op, "output"))["dataset"]
            if predicate == "expanded_output"
            else inp["datasets"][0],
            value["value"],
        )
    else:
        test.fail("No assertion adapter for reviewed predicate: " + predicate)


def _expression_for(tree_value, template):
    leaves = []

    def visit(value):
        if isinstance(value, dict):
            if value.get("kind") in {"literal", "name"}:
                leaves.append(value)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(template)

    def build(value):
        if value[0] in {"name", "literal"}:
            return deepcopy(
                _one(
                    [
                        leaf
                        for leaf in leaves
                        if leaf["kind"] == value[0]
                        and leaf.get("name", leaf.get("lexeme")) == value[1]
                    ]
                )
            )
        return {
            "kind": "binary",
            "operator": value[0],
            "left": build(value[1]),
            "right": build(value[2]),
            "span": deepcopy(template["span"]),
        }

    return build(tree_value)


def mutate(graph, case_name, mutation):
    """Encode the reviewed counterclaim or omission; never change source bytes."""
    op = next(
        (o for o in graph["operations"] if o["kind"] in {"DATA_STEP", "PROC_SQL", "PROC_SORT"}),
        None,
    )
    predicate, wrong = mutation["predicate"], mutation["incorrect_value"]
    sql = next(iter(facts_of(op, "sql")), None)
    if predicate == "expression":
        expression_owner = sql["select"][0] if sql else facts_of(op, "assignment")[0]
        expression_owner["expression"] = _expression_for(wrong, expression_owner["expression"])
    elif predicate == "assignment_order":
        positions = [i for i, f in enumerate(op["facts"]) if f["kind"] == "assignment"]
        op["facts"][positions[0]], op["facts"][positions[1]] = (
            op["facts"][positions[1]],
            op["facts"][positions[0]],
        )
    elif predicate == "read_datasets":
        op["reads"] = []
    elif predicate == "input_sequence":
        _one(facts_of(op, "input"))["datasets"] = wrong
    elif predicate in {"cardinality_per_key", "cardinality_per_matching_key"}:
        op["cardinality"] = (
            "SQL_JOIN_MULTIPLICITY_OR_SUBSET"
            if predicate == "cardinality_per_key"
            else "MATCH_MERGE_MAX_PER_BY_GROUP_OR_SUBSET"
        )
    elif predicate == "exhausted_input_values":
        op["state_effects"] = [s for s in op["state_effects"] if s["kind"] != "MERGE"]
    elif predicate == "sum_state":
        op["state_effects"] = [s for s in op["state_effects"] if s["kind"] != "SUM"]
    elif predicate == "reset":
        reset = _one([f for f in facts_of(op, "assignment") if f["target"] == "balance"])
        reset["guard"]["key"] = "subkey"
    elif predicate == "by_prefix_effect":
        _one([s for s in op["state_effects"] if s["kind"] == "BY"])["reset"] = "BY_GROUP"
    elif predicate == "lag_queue":
        _one([s for s in op["state_effects"] if s["kind"] == "LAG" and s["target"] == "previous"])[
            "guard"
        ] = None
        _one([f for f in facts_of(op, "assignment") if f["target"] == "previous"])["guard"] = None
    elif predicate == "queue_ownership":
        states = [s for s in op["state_effects"] if s["kind"] == "LAG"]
        states[1]["fact_index"] = states[0]["fact_index"]
    elif predicate == "tie_order":
        if wrong == "STABLE_INPUT_ORDER":
            op["order_contract"]["tie_order"] = wrong
        else:
            sql["order_by"] = ["total"]
            op["order_contract"]["keys"] = ["total"]
    elif predicate == "producer_dependency":
        graph["edges"] = [e for e in graph["edges"] if e["type"] != "DATA"]
    elif predicate == "numeric_missing_order":
        op["numeric_policy"]["missing_order"] = wrong
    elif predicate == "numeric_missing_equality":
        op["numeric_policy"]["missing_join"] = wrong
    elif predicate == "unmatched_left_row_survival":
        sql["where"] = None
    elif predicate == "output_order":
        op["order_contract"]["kind"] = wrong
    elif predicate == "expanded_input":
        _one(facts_of(op, "input"))["datasets"] = [wrong["value"]]
    elif predicate == "expanded_output":
        use = _one([f for f in facts_of(op, "macro_use") if f["name"] == "member"])
        definition = _one(
            [
                f
                for o in graph["operations"]
                for f in facts_of(o, "macro_binding")
                if f["name"] == "source"
            ]
        )
        use["definition_span"] = deepcopy(definition["span"])
    elif predicate in {"output_count", "real_time", "cell"}:
        metric = {
            "output_count": "OUTPUT_ROWS",
            "real_time": "ELAPSED_SECONDS",
            "cell": "LST_CELL",
        }[predicate]
        matches = [o for o in graph["log_observations"] if o["metric"] == metric]
        if predicate == "cell":
            matches = [
                o
                for o in matches
                if o["column"] == wrong["column"]
                and o["log_citation"]["line_start"] == wrong["row"]
            ]
        observation = _one(matches)
        if "lexeme" in wrong:
            observation["value_lexeme"] = wrong["lexeme"]
        if "unit" in wrong:
            observation["unit"] = wrong["unit"]
        if "kind" in wrong:
            observation["cell_kind"] = wrong["kind"]
    else:
        raise AssertionError("No mutation adapter for " + predicate + " in " + case_name)


class PublicReconstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if EXPECTATION_REVIEW["status"] != "REVIEWED_FOR_PUBLIC_DEVELOPMENT":
            raise AssertionError("Expected answers must be independently reviewed before test use")
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.cases = {}
        for name, case in PUBLIC_CASES.items():
            cls.cases[name] = make_case(Path(cls.temporary.name) / name, case)

    def test_reviewed_expectation_digest(self):
        expected_path = ROOT / "tests" / "p2a_expectations.py"
        self.assertEqual(
            hashlib.sha256(expected_path.read_bytes()).hexdigest(),
            "f42549738a041db87d3547adec59ddfd0f9b15aa2621f1cf0b7ea7fa9f7ffd93",
        )


def _positive(name):
    def test(self):
        scope, inventory, profile, graph = self.cases[name]
        report = validate_v2(scope, inventory, graph, profile, profile_file_key=PROFILE_KEY)
        self.assertEqual(report["reconstruction_status"], "COMPLETE", graph["unknowns"])
        self.assertEqual(report["source_consistency"], "PASSED")
        self.assertEqual(report["stage_gate"], "BLOCKED")
        self.assertEqual(report["semantic_acceptance"], "BLOCKED")
        self.assertEqual(report["semantic_verification"], "UNVERIFIABLE")

    return test


def _fact_test(name, expected):
    def test(self):
        _, _, profile, graph = self.cases[name]
        assert_fact(self, PUBLIC_CASES[name], graph, profile, expected)

    return test


def _mutation_test(name, mutation):
    def test(self):
        scope, inventory, profile, original = self.cases[name]
        changed = deepcopy(original)
        citations = all_citations(original)
        self.assertTrue(citations)
        mutate(changed, name, mutation)
        reidentify(changed, inventory)
        self.assertNotEqual(changed, original)
        self.assertTrue(all_citations(changed) <= citations)
        for op in changed["operations"]:
            self.assertEqual(
                op["operation_id"],
                record_id("op", changed["source_fingerprint"], op, "operation_id"),
            )
        schema_forbidden = (
            mutation["predicate"]
            in {"numeric_missing_order", "numeric_missing_equality", "real_time"}
            or mutation["incorrect_value"] == "STABLE_INPUT_ORDER"
        )
        if schema_forbidden:
            with self.assertRaises(EvidenceError) as caught:
                validate_contract("Graph", changed, version="2.0")
            self.assertEqual(caught.exception.code, "SCHEMA_INVALID")
        else:
            validate_contract("Graph", changed, version="2.0")
            with self.assertRaises(EvidenceError) as caught:
                validate_v2(scope, inventory, changed, profile, profile_file_key=PROFILE_KEY)
            self.assertEqual(caught.exception.code, "RECONSTRUCTION_SOURCE_MISMATCH")

    return test


for _name, _case in PUBLIC_CASES.items():
    setattr(PublicReconstructionTests, "test_complete_" + _name, _positive(_name))
    for _index, _expected in enumerate(_case["facts"]):
        setattr(
            PublicReconstructionTests,
            f"test_fact_{_name}_{_index:02d}_{_expected['predicate']}",
            _fact_test(_name, _expected),
        )
    for _index, _counterclaim in enumerate(_case["mutations"]):
        setattr(
            PublicReconstructionTests,
            f"test_mutation_{_name}_{_index:02d}_{_counterclaim['predicate']}",
            _mutation_test(_name, _counterclaim),
        )


def _boundary_input(name, extra):
    columns = ["key", "subkey", "x", extra]
    return {
        "name": name,
        "module_id": "main",
        "columns": [{"name": c, "type": "NUMERIC", "length": 8} for c in columns],
        "rows": [["1", "1", "1", "1"]],
        "sorted_by": ["key", "subkey"],
    }


class PublicBoundaryTests(unittest.TestCase):
    pass


def _syntax_boundary(case):
    def test(self):
        source_case = deepcopy(case)
        source_case["inputs"] = [
            _boundary_input("work.a", "left_value"),
            _boundary_input("work.b", "right_value"),
            _boundary_input("work.c", "third_value"),
        ]
        if case["id"] == "include_repeat":
            source_case["files"]["constants.sas"] = (
                b"/* PUBLIC SYNTHETIC INCLUDE */\n%let member=one;\n"
            )
        with tempfile.TemporaryDirectory() as temporary:
            scope, inventory, profile, graph = make_case(temporary, source_case)
            report = validate_v2(scope, inventory, graph, profile, profile_file_key=PROFILE_KEY)
        self.assertEqual(report["reconstruction_status"], "PARTIAL")
        self.assertEqual(report["semantic_acceptance"], "BLOCKED")
        self.assertTrue(graph["unknowns"], case["reason"])
        syntax_unknowns = [
            u
            for u in graph["unknowns"]
            if u["code"]
            not in {
                "INPUT_SCHEMA_UNRESOLVED",
                "COLUMN_REFERENCE_UNRESOLVED",
                "MERGE_SHARED_NONKEY_UNSUPPORTED",
                "BY_SORT_PRECONDITION_UNRESOLVED",
            }
        ]
        self.assertTrue(
            syntax_unknowns, "Boundary did not exercise its source restriction: " + case["reason"]
        )
        self.assertTrue(any(u["citations"] for u in syntax_unknowns))

    return test


for _case in UNSUPPORTED_CASES:
    setattr(PublicBoundaryTests, "test_unsupported_" + _case["id"], _syntax_boundary(_case))


def _evidence_boundary(boundary):
    def test(self):
        name = boundary["id"]
        source_case = (
            deepcopy(PUBLIC_CASES[boundary["based_on"]])
            if "based_on" in boundary
            else deepcopy(boundary)
        )
        profile_edit = scope_edit = None
        if name == "unknown_input_schema":
            source_case["inputs"] = []
        elif name in {"unknown_merge_order", "unknown_by_order"}:
            for source in source_case["inputs"]:
                source["sorted_by"] = []
        elif name == "shared_merge_nonkey":
            for source in source_case["inputs"]:
                source["columns"][1]["name"] = "value"
        elif name == "non_numeric_key":
            source_case["inputs"][0]["columns"][0]["type"] = "CHARACTER"
        elif name == "include_cycle":
            source_case["inputs"] = []
        elif name in {"unassociated_log", "lst_unbound"}:
            source_case["declared_bindings"] = []
        elif name == "unbound_log_step":
            profile_edit = lambda profile: profile["log_bindings"].clear()  # noqa: E731 -- retain the existing mutation callback
        elif name == "incomplete_log":
            source_case["declared_bindings"][0]["complete"] = False
        elif name in {"log_minutes", "log_error", "log_other_language"}:
            source_case["files"]["run.log"] = boundary["replacement"]
            source_case["declared_bindings"][0]["end_line"] = 1
        elif name == "lst_title_mismatch":
            source_case["files"]["run.lst"] = source_case["files"]["run.lst"].replace(
                b"PUBLIC SYNTHETIC TABLE", b"UNEXPECTED TITLE"
            )
        elif name == "lst_extra_page":
            source_case["files"]["run.lst"] *= 2
        elif name == "lst_non_numeric":
            source_case["files"]["run.lst"] = source_case["files"]["run.lst"].replace(
                b"1    2", b"text 2"
            )
        else:
            self.fail("Missing adapter for reviewed evidence boundary " + name)
        with tempfile.TemporaryDirectory() as temporary:
            if name == "non_numeric_key":
                scope, profile = prepare_case(temporary, source_case)
                inventory = build_inventory(scope, "boundary")
                with self.assertRaises(EvidenceError) as caught:
                    reconstruct(scope, inventory, profile, profile_file_key=PROFILE_KEY)
                self.assertEqual(caught.exception.code, "SCHEMA_INVALID")
                return
            scope, inventory, profile, graph = make_case(
                temporary, source_case, profile_edit=profile_edit, scope_edit=scope_edit
            )
            report = validate_v2(scope, inventory, graph, profile, profile_file_key=PROFILE_KEY)
        self.assertEqual(report["reconstruction_status"], "PARTIAL", boundary["reason"])
        self.assertEqual(report["semantic_acceptance"], "BLOCKED")
        issues = graph["unknowns"] + graph["contradictions"]
        self.assertTrue(issues)
        self.assertTrue(all(u.get("code") for u in issues))
        self.assertEqual(report["stage_gate"], "FAIL" if name == "log_error" else "BLOCKED")

    return test


for _case in EVIDENCE_BOUNDARIES:
    setattr(PublicBoundaryTests, "test_evidence_" + _case["id"], _evidence_boundary(_case))


class PublicPolicyBoundaryTests(unittest.TestCase):
    def test_missing_join_policy_unresolved_blocks_reviewed_missing_keys(self):
        with tempfile.TemporaryDirectory() as temporary:
            scope, inventory, profile, graph = make_case(
                temporary,
                PUBLIC_CASES["sql_left_where_and_missing"],
                profile_edit=lambda p: p.update(numeric_missing_join_policy="UNRESOLVED"),
            )
            report = validate_v2(scope, inventory, graph, profile, profile_file_key=PROFILE_KEY)
        self.assertEqual(report["reconstruction_status"], "PARTIAL")
        self.assertTrue(
            any(u["code"] == "MISSING_JOIN_KEY_POLICY_UNRESOLVED" for u in graph["unknowns"])
        )


if __name__ == "__main__":
    unittest.main()
