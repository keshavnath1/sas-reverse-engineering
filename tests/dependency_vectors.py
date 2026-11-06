"""Independent public P3-A1 graph vectors and literal mathematical expectations.

Authored before the candidate diagnostic module. This module imports only the
standard library: it does not parse SAS, reconstruct evidence or call production
identity/diagnostic helpers. Supplied citation/hash strings are synthetic claims,
not claims that source files exist or have been inspected. The small constructors
below spell out frozen v2 preimages; EXPECTED contains literal graph-math answers.
These public examples cannot establish independently accepted SAS semantics.
"""

from copy import deepcopy
import hashlib
import json


FINGERPRINT = "1" * 64
SOURCE_SHA256 = "2" * 64
EXCERPT_SHA256 = "3" * 64
AUTHORITY = {
    "artifact_authority": "DRAFT", "semantic_verification": "UNVERIFIABLE",
    "semantic_acceptance": "BLOCKED", "benchmark_execution": "NOT_RUN",
}
LIMITS = {
    "operations": 100, "modules": 8, "edges": 10_000, "nodes": 2_000,
    "facts": 5_000, "json_values": 200_000, "depth": 64,
    "canonical_bytes": 8 * 1024 * 1024,
}


def oracle_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def oracle_hash(value):
    return hashlib.sha256(oracle_bytes(value)).hexdigest()


def oracle_id(prefix, record, id_field, fingerprint=FINGERPRINT):
    payload = {key: value for key, value in record.items() if key != id_field}
    return prefix + "_" + oracle_hash({"source_fingerprint": fingerprint,
                                      "payload": payload})


def citation(sequence=0, module="main"):
    return {"file_key": "synthetic:" + module + ".sas",
            "source_sha256": SOURCE_SHA256, "line_start": sequence + 1,
            "line_end": sequence + 1, "excerpt_sha256": EXCERPT_SHA256}


def span(sequence=0, module="main"):
    return {"file_key": "synthetic:" + module + ".sas", "start": sequence * 100,
            "end": sequence * 100 + 99, "line_start": sequence + 1,
            "line_end": sequence + 1, "citation": citation(sequence, module),
            "byte_sha256": EXCERPT_SHA256}


def dataset(name="work.shared", module="main"):
    value = {"module_id": module, "name": name,
             "semantic_verification": "UNVERIFIABLE", "role": "UNRESOLVED",
             "citations": []}
    value["dataset_id"] = oracle_id("ds", value, "dataset_id")
    return value


def column(parent, name="x"):
    value = {"module_id": parent["module_id"], "dataset_id": parent["dataset_id"],
             "name": name, "semantic_verification": "UNVERIFIABLE", "type": "NUMERIC",
             "length": 8, "citations": []}
    value["column_id"] = oracle_id("col", value, "column_id")
    return value


def operation(sequence=0, module="main", **updates):
    value = {
        "module_id": module, "kind": "DATA_STEP", "citations": [citation(sequence, module)],
        "reads": [], "writes": [], "stateful_constructs": [],
        "classification": "INFERENCE", "semantic_verification": "UNVERIFIABLE",
        "span": span(sequence, module), "sequence": sequence, "facts": [],
        "lineage": [], "control_lineage": [], "state_effects": [],
        "order_contract": {"kind": "UNSPECIFIED", "keys": [],
                           "requires_sorted_inputs": False, "precondition": "NOT_REQUIRED",
                           "tie_order": "UNSPECIFIED"},
        "numeric_policy": {"storage": "SAS_NUMERIC_8",
                           "missing_order": "ORDINARY_MISSING_BELOW_FINITE",
                           "missing_arithmetic": "PROPAGATE_EXCEPT_SUM_STATEMENT",
                           "expression_order": "SOURCE_TREE_NO_REASSOCIATION",
                           "runtime_equivalence": "NOT_ASSERTED",
                           "exactness": "BOUNDED_SYNTHETIC_PRECONDITIONS",
                           "missing_join": "SAS_ORDINARY_MISSING_EQUALS_MISSING"},
        "cardinality": "NOT_APPLICABLE", "interpretation_rules": [],
    }
    value.update(deepcopy(updates))
    value["operation_id"] = oracle_id("op", value, "operation_id")
    return value


def edge(first, second, kind="DATA", nodes=()):
    value = {"from_operation_id": first["operation_id"],
             "to_operation_id": second["operation_id"], "type": kind,
             "node_ids": list(nodes),
             "evidence_operation_ids": sorted({first["operation_id"], second["operation_id"]}),
             "classification": "INFERENCE", "semantic_verification": "UNVERIFIABLE"}
    value["edge_id"] = oracle_id("edge", value, "edge_id")
    return value


def issue(identifier="inventory-opaque-issue", operations=(), contradiction=False):
    return {"issue_id": identifier,
            "kind": "CONTRADICTION" if contradiction else "DYNAMIC_DEPENDENCY",
            "file_keys": [], "operation_ids": list(operations), "status": "UNRESOLVED",
            "code": "SYNTHETIC_CONTRADICTION" if contradiction else "DYNAMIC_DEPENDENCY",
            "citations": [], "spans": [],
            "missing_proof": "Independent evidence of the declared synthetic dependency"}


def observation(op):
    value = {"module_id": op["module_id"], "run_id": "run-1", "attempt_id": "attempt-1",
             "association_id": "synthetic-log-association", "execution_id": "synthetic-execution",
             "log_citation": {**citation(), "file_key": "synthetic:run.log"},
             "source_operation_ids": [op["operation_id"]], "metric": "ELAPSED_SECONDS",
             "classification": "OBSERVATION", "semantic_verification": "UNVERIFIABLE",
             "value_lexeme": "0.125", "unit": "seconds", "dataset": None,
             "row": None, "column": None, "cell_kind": None}
    value["observation_id"] = oracle_id("log", value, "observation_id")
    return value


def refresh_coverage(graph):
    """Only supplied local counts; file inventory is deliberately unavailable."""
    graph["coverage"] = {"file_count": 1, "covered_source_file_count": 1,
                         **{singular + "_count": len(graph[plural]) for singular, plural in (
                             ("operation", "operations"), ("dataset", "datasets"),
                             ("column", "columns"), ("edge", "edges"),
                             ("log_observation", "log_observations"),
                             ("unknown", "unknowns"), ("contradiction", "contradictions"))}}
    return graph


def graph(operations=(), datasets=(), columns=(), edges=(), unknowns=(), contradictions=(),
          log_observations=(), modules=("main",)):
    value = {"schema_version": "2.0", "workspace_id": "p3-a1-public-synthetic",
             "run_id": "run-1", "attempt_id": "attempt-1", "module_ids": list(modules),
             "scope_manifest_sha256": "4" * 64, "source_fingerprint": FINGERPRINT,
             "inventory_schema_version": "1.0", "profile_file_key": "synthetic:profile.json",
             "profile_sha256": "5" * 64, "interpretation_profile": "sas94-synthetic-v1",
             **AUTHORITY,
             "datasets": deepcopy(list(datasets)), "columns": deepcopy(list(columns)),
             "operations": deepcopy(list(operations)), "edges": deepcopy(list(edges)),
             "log_observations": deepcopy(list(log_observations)),
             "unknowns": deepcopy(list(unknowns)), "contradictions": deepcopy(list(contradictions)),
             "statement_coverage": []}
    return refresh_coverage(value)


# These literal topology declarations are fixture INPUT, never an expected answer
# computed by reachability, SCC, candidate code or source reconstruction.
TOPOLOGIES = {
    "single": (1, []),
    "chain": (3, [(0, 1), (1, 2)]),
    "diamond": (4, [(0, 1), (0, 2), (1, 3), (2, 3)]),
    "disconnected": (4, [(0, 1), (2, 3)]),
    "cycle": (2, [(0, 1), (1, 0)]),
}


def topology(name):
    count, pairs = TOPOLOGIES[name]
    nodes = [dataset("work.link" + str(i)) for i in range(len(pairs))]
    ops = []
    for index in range(count):
        ops.append(operation(index,
                   reads=[nodes[j]["dataset_id"] for j, (_, target) in enumerate(pairs) if target == index],
                   writes=[nodes[j]["dataset_id"] for j, (source, _) in enumerate(pairs) if source == index]))
    edges = [edge(ops[source], ops[target], nodes=[nodes[j]["dataset_id"]])
             for j, (source, target) in enumerate(pairs)]
    return graph(ops, nodes, edges=edges)


def shared_access(kind="RAW", *, column_variant=None):
    parent = dataset()
    cols = [column(parent, "x"), column(parent, "y")]
    first, second = parent["dataset_id"], parent["dataset_id"]
    if column_variant == "parent_column":
        second = cols[0]["column_id"]
    elif column_variant == "column_parent":
        first = cols[0]["column_id"]
    elif column_variant == "distinct_columns":
        first, second = cols[0]["column_id"], cols[1]["column_id"]
    left = {"reads": [first]} if kind == "WAR" else {"writes": [first]}
    right = {"reads": [second]} if kind == "RAW" else {"writes": [second]}
    return graph([operation(0, **left), operation(1, **right)], [parent], cols)


def state_cycle(kind="RETAIN"):
    target = dataset()
    loc = span()
    literal = {"kind": "literal", "span": loc, "lexeme": "0"}
    if kind == "RETAIN":
        fact = {"kind": "retain", "span": loc, "target": "x", "initial": literal}
    else:
        expr = {"kind": "lag", "span": loc, "name": "lag", "argument": literal, "queue_size": 1}
        fact = {"kind": "assignment", "span": loc, "target": "x", "expression": expr, "guard": None}
    effect = {"fact_index": 0, "kind": kind, "target": "x",
              "initialization": "LITERAL" if kind == "RETAIN" else "MISSING_QUEUE",
              "persistence": "ACROSS_ROWS",
              "reset": "ONLY_EXPLICIT_ASSIGNMENT" if kind == "RETAIN" else "NONE_IMPLICIT",
              "queue_size": None if kind == "RETAIN" else 1,
              "call_policy": "NOT_APPLICABLE" if kind == "RETAIN" else "EXECUTED_CALLS_ONLY",
              "guard": None}
    op = operation(0, facts=[fact], stateful_constructs=[kind], state_effects=[effect],
                   writes=[target["dataset_id"]])
    return graph([op], [target], edges=[edge(op, op, "STATE", [target["dataset_id"]])])


def macro_control():
    incoming, outgoing = dataset("work.in", "prepare"), dataset("work.out", "main")
    x, y = column(incoming), column(outgoing, "y")
    definition = {"kind": "macro_binding", "span": span(0, "prepare"), "name": "bound", "value": "1"}
    first = operation(0, "prepare", kind="MACRO", facts=[definition], stateful_constructs=["GLOBAL_MACRO"])
    loc = span(1)
    use = {"kind": "macro_use", "span": loc, "name": "bound", "value": "1", "definition_span": definition["span"]}
    assignment = {"kind": "assignment", "span": loc, "target": "y",
                  "expression": {"kind": "literal", "span": loc, "lexeme": "1"}, "guard": None}
    condition = {"kind": "comparison", "span": loc,
                 "left": {"kind": "name", "span": loc, "name": "x", "lexeme": "x"},
                 "operator": ">", "right": {"kind": "literal", "span": loc, "lexeme": "0"}}
    subset = {"kind": "subset_if", "span": loc, "condition": condition}
    second = operation(1, facts=[use, assignment, subset], stateful_constructs=["GLOBAL_MACRO"],
                       reads=[incoming["dataset_id"], x["column_id"]], writes=[outgoing["dataset_id"], y["column_id"]],
                       control_lineage=[{"fact_index": 2, "input_column_ids": [x["column_id"]],
                                         "input_fact_indices": [1], "role": "ROW_SELECTION",
                                         "input_phase": "CURRENT_ITERATION"}],
                       lineage=[{"fact_index": 1, "output_column_id": y["column_id"],
                                 "input_column_ids": [x["column_id"]], "input_fact_indices": [],
                                 "input_phase": "CURRENT_ITERATION"}])
    return graph([first, second], [incoming, outgoing], [x, y],
                 [edge(first, second, "STATE")], modules=["prepare", "main"])


def order_graph(precondition="UNRESOLVED"):
    target = dataset()
    loc = span()
    fact = {"kind": "sort", "span": loc, "input": "work.input", "output": "work.shared", "keys": ["x"]}
    first = operation(0, kind="PROC_SORT", facts=[fact], writes=[target["dataset_id"]],
                      cardinality="SORT_PRESERVES_ROWS",
                      order_contract={"kind": "ASCENDING_KEYS", "keys": ["x"],
                                      "requires_sorted_inputs": False, "precondition": "NOT_REQUIRED",
                                      "tie_order": "UNSPECIFIED"})
    second = operation(1, facts=[{"kind": "by", "span": span(1), "keys": ["x"], "ascending": True}],
                       reads=[target["dataset_id"]], stateful_constructs=["BY"],
                       cardinality="MATCH_MERGE_MAX_PER_BY_GROUP_OR_SUBSET",
                       order_contract={"kind": "INPUT_ORDER", "keys": ["x"],
                                       "requires_sorted_inputs": True, "precondition": precondition,
                                       "tie_order": "UNSPECIFIED"})
    return graph([first, second], [target], edges=[edge(first, second, "ORDER", [target["dataset_id"]])])


def typed_edges(kinds=("RESOURCE",)):
    ops = [operation(0), operation(1)]
    issues = [issue("unknown-edge-binding", [o["operation_id"] for o in ops])] if "UNKNOWN" in kinds else []
    return graph(ops, edges=[edge(ops[0], ops[1], kind) for kind in kinds], unknowns=issues)


def unknown_graph(*, global_binding=False, contradiction=False):
    op = operation()
    unknown = issue(operations=[] if global_binding else [op["operation_id"]])
    contradictions = [issue("contradiction-opaque", [op["operation_id"]], True)] if contradiction else []
    return graph([op], unknowns=[unknown], contradictions=contradictions)


# Human-checkable literal expectations. Labels are operation sequence positions
# A=0, B=1, C=2, D=3, never names invented by the candidate. Paths below are edge
# labels from the input topology, not re-created edges. BFS tie-breaking visits
# sequence then canonical ID; A→B→D is therefore the reproducible diamond witness.
EXPECTED = {
    "single": {"reachable": [], "cycles": [], "no_path": []},
    "chain": {"reachable": [("A", "B"), ("A", "C"), ("B", "C")],
              "paths": {("A", "C"): [("A", "B"), ("B", "C")]}, "cycles": []},
    "diamond": {"reachable": [("A", "B"), ("A", "C"), ("A", "D"), ("B", "D"), ("C", "D")],
                "paths": {("A", "D"): [("A", "B"), ("B", "D")]}, "cycles": []},
    "disconnected": {"reachable": [("A", "B"), ("C", "D")], "cycles": [],
                     "no_path": [("A", "C"), ("C", "A"), ("B", "D"), ("D", "B")]},
    "cycle": {"reachable": [("A", "A"), ("A", "B"), ("B", "A"), ("B", "B")],
              "cycles": [("A", "B")]},
    "state": {"reachable": [("A", "A")], "cycles": [("A",)], "effects": ["RETAIN", "LAG"]},
    "resource": {"reachable": [], "causal_edges": [], "resource_count": 1},
    "side_unknown": {"reachable": [("A", "B")], "types": ["SIDE_EFFECT", "UNKNOWN"]},
    "raw": {"conflict": "RAW", "pair": ("A", "B"), "canonical_edge_count": 0},
    "waw": {"conflict": "WAW", "pair": ("A", "B"), "canonical_edge_count": 0,
            "required_uncertainty": "UNVERSIONED_DATASET"},
    "war": {"conflict": "WAR", "pair": ("A", "B"), "canonical_edge_count": 0},
    "aliases": {"variants": ["parent_column", "column_parent", "distinct_columns"],
                "conflict": "WAW", "pair": ("A", "B"), "independence": "UNPROVED"},
    "macro_control": {"reachable": [("A", "B")], "edge_type": "STATE",
                      "local_fact_index": 2, "prior_local_fact_indices": [1],
                      "column_owner": "prepare", "operation_owner": "main"},
    "order": {"edge_type": "ORDER", "preconditions": ["UNRESOLVED", "SOURCE_SORT", "DECLARED_SYNTHETIC_INPUT"],
              "tie_order": "UNSPECIFIED", "scheduling": "NOT_AUTHORIZED"},
    "unknown": {"variants": ["LOCAL", "GLOBAL"], "favorable_scope_verdict": "FORBIDDEN"},
    "contradiction": {"eligible": False, "rejecting_findings": 1, "unknown_findings": 1},
}

# Reviewable scope of all named obligations, including negative/guard cases whose
# exact code names are private API design choices. Expected acceptance/refusal is
# frozen independently of those choices; tests must not copy candidate output.
OBLIGATIONS = {
    "A01": "single canonical operation; empty reachability; no independence approval",
    "A02": "chain exact A→B→C original-edge witness",
    "A03": "diamond four original edges and sequence-first A→B→D witness",
    "A04": "disconnected pairs have no represented path, independence unproved",
    "A05": "missing RAW edge: conflict and missing proof, no canonical edge insertion",
    "A06": "WAW conflict and unversioned overwrite uncertainty",
    "A07": "WAR conflict, no canonical edge insertion",
    "A08": "all three dataset/column alias variants retain WAW uncertainty",
    "A09": "RETAIN and LAG retain STATE self-cycle and full state effects",
    "A10": "two-operation SCC retains both original edges",
    "A11": "macro STATE and cross-module column visible; prior facts local only",
    "A12": "all ordering preconditions and unspecified tie order remain obligations",
    "A13": "RESOURCE retained separately, no semantic reachability",
    "A14": "SIDE_EFFECT and UNKNOWN IDs/types retained; no favorable claim",
    "A15": "scoped unknown attribution and global unknown retained",
    "A16": "contradiction explicitly rejects eligibility alongside unknown",
    "A17": "duplicate/forged reconstructible IDs refuse; enriched issue IDs opaque",
    "A18": "dangling operation/node/module and invalid local fact references refuse",
    "A19": "version/sequence/owner invalidity refuses without conversion",
    "A20": "rehashed shape-valid false graph remains unverified",
    "A21": "success/error/bound refusal never mutates input; detached result",
    "A22": "repeat deterministic; set-like permutations same analysis/different digest; statement order retained",
    "A23": "changed operation/edge/logical subject with old digest refuses; new digest differs",
    "A24": "each limit−1 and limit accepted by own guard, limit+1 refused; invalid JSON refused; bounded layered witnesses",
    "A25": "no source/store/process/network/provider/reconstruction access during call",
    "A26": "all fixed authority fields; placeholder exit 3; Windows early denial exit 2",
}


def fixture_catalog():
    """Fresh positive fixtures only; mutation/failure variants are test-owned."""
    values = {name: topology(name) for name in TOPOLOGIES}
    values.update({"raw": shared_access("RAW"), "waw": shared_access("WAW"),
                   "war": shared_access("WAR"), "retain": state_cycle("RETAIN"),
                   "lag": state_cycle("LAG"), "macro_control": macro_control(),
                   "resource": typed_edges(), "side_unknown": typed_edges(("SIDE_EFFECT", "UNKNOWN")),
                   "local_unknown": unknown_graph(), "global_unknown": unknown_graph(global_binding=True),
                   "contradiction": unknown_graph(contradiction=True)})
    for variant in EXPECTED["aliases"]["variants"]:
        values["alias_" + variant] = shared_access("WAW", column_variant=variant)
    for condition in EXPECTED["order"]["preconditions"]:
        values["order_" + condition.lower()] = order_graph(condition)
    op = operation()
    values["observation"] = graph([op], log_observations=[observation(op)])
    return values


# Filled from the independent JSON/hash oracle before candidate implementation.
# Each value binds exact fixture arrays as authored, not a normalized graph.
FROZEN_GRAPH_SHA256 = {
    'single': '1ab1ec526c265f5437e24e5c72c2aced670aa01c9f7fe56262e0df5d6b1a7230',
    'chain': 'f9dec9e215da8ee426e3bed7b8d5abf71180082280a5ee4aedad794c1f826558',
    'diamond': '526cbcb185e08d455f3f9fb74e8eac0c4daf2b6a82bab4fb3a25a8e1642cf447',
    'disconnected': 'a3e4f4cb28a0dea34c8eeaebd1cb1a6869d3e2c7a3e730c961e7e010033e5c5c',
    'cycle': '0333f05fbdd2fe7d52d5cbfcd85a5d447092a36346fd1b47f8e412b8627b27d0',
    'raw': 'c1d40496d3d91b149fb09a07b27459df2e492deba6f8ff60374782ad220a57b6',
    'waw': '49bac46ae9a000b256f43bed2e66431b3116a1a557452fd5dd2b4765f61e3c8a',
    'war': 'ad977b84ca3185635f75823ee72c5f06e55f98418a101a1ebb61c05a65431dae',
    'retain': '6d831c7c96505f5edd793ce2b9ad58e47610ca7102af2b0ab2628568268d8c10',
    'lag': '27154916f43d8cd7147034ff01dd2e89db5d5b7e26c1618b2fcdc6a1731ca7dd',
    'macro_control': '44bc73bccaca1a0793ebee4f417f71b5d8ec54b8391f6d0cd8d09f05900dfeb6',
    'resource': 'cd500f4531097536b4ae7d903541468863770e97e774227e850457423a0378d0',
    'side_unknown': '0a2a7c3e460103b8e0b67d3641bd33c68a579040c2bc8963f2c3cd90995df790',
    'local_unknown': '28d8ec6945dce7855a2dcbdd3e5b6127370a360d77bd1be58045cce988f676ac',
    'global_unknown': 'c36d3c7fff6391c64767fb3e4077091ad1b02ec53370ecdec51f818408450011',
    'contradiction': '3d65e4a59cf6c9583b28c96dcc5de8b5745f3ee75b55ea39ad238d104ef8316f',
    'alias_parent_column': '03460a2ac41cc7059f8810672fc6bda8e084e5dba02199fcba89cce9d1296a86',
    'alias_column_parent': '2616e14843ffac54a3f11c3fa7c89e7aff79707828b68fcac09eaee4c0812a1e',
    'alias_distinct_columns': 'a63790bfa7fce1097de5515e81d72a38a3b031ef196499eb7c0bcce744ca9024',
    'order_unresolved': '6d725f6a375993258fb3c73fcd5439897537ee29bc1505be035304be0c58c27f',
    'order_source_sort': '41986b64eb57929ae782fa533be73d32c00af543e0f635285e5e964d34d64a9a',
    'order_declared_synthetic_input': '72417cd96dadf943f594e7ef2d5d3bc97a6cca6d500342774988889f79c282de',
    'observation': '7a0ce2a61ffe199bf501f3a0d28c49908723fcb12e9eb2bab6297a6699a0ffbf',
}
