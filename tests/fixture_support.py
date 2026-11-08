"""Synthetic-only P1 fixtures constructed in a caller-owned temporary directory.

make_scope(root) writes root/sources and returns the explicit authorization.
make_graph(scope, attempt='attempt1') returns (inventory, composed_graph).
No file here is a production example or an observed SAS execution result.
"""

import copy
from pathlib import Path

from sas_re.evidence import build_inventory, citation, coverage, digest, record_id


SYNTHETIC_SOURCES = {
    "producer.sas": b"/* SYNTHETIC FIXTURE; never executed. */\n%include 'includes/constants.sas';\ndata work.stage;\n  value = 1;\nrun;\n",
    "consumer.sas": b"/* SYNTHETIC FIXTURE; never executed. */\ndata work.final;\n  set work.stage;\n  doubled = value * 2;\nrun;\n",
    "includes/constants.sas": b"/* SYNTHETIC INCLUDE FIXTURE; never executed. */\n%let synthetic_constant = 1;\n",
    "settings.cfg": b"/* SYNTHETIC CONFIG FIXTURE; never executed. */\n-nologo\n",
    "producer.log": b"NOTE: SYNTHETIC FIXTURE; no SAS execution occurred.\nNOTE: The data set WORK.STAGE has 1 observations.\n",
    "producer.lst": b"SYNTHETIC LISTING FIXTURE; no SAS execution occurred.\nvalue\n1\n",
}


def make_scope(root: Path) -> dict:
    source = Path(root).resolve() / "sources"
    source.mkdir(parents=True, exist_ok=True)
    kinds = {"producer.sas": "SAS", "consumer.sas": "SAS", "includes/constants.sas": "INCLUDE",
             "settings.cfg": "CONFIG", "producer.log": "LOG", "producer.lst": "LST"}
    for relative, data in SYNTHETIC_SOURCES.items():
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return {
        "schema_version": "1.0", "workspace_id": "synthetic-workspace", "run_id": "synthetic-run",
        "module_ids": ["prepare", "analyze"], "synthetic": True,
        "roots": [{"root_id": "synthetic", "path": str(source)}],
        "files": [{"file_key": "synthetic:" + name, "root_id": "synthetic", "path": name,
                   "kind": kind, "module_id": "analyze" if name == "consumer.sas" else "prepare",
                   "encoding": "utf-8"} for name, kind in kinds.items()],
        "dependencies": [
            {"dependency_id": "include-constants", "from_file_key": "synthetic:producer.sas",
             "to_file_key": "synthetic:includes/constants.sas", "kind": "INCLUDE", "status": "DECLARED"},
            {"dependency_id": "config-settings", "from_file_key": "synthetic:producer.sas",
             "to_file_key": "synthetic:settings.cfg", "kind": "CONFIG", "status": "DECLARED"}],
        "log_associations": [
            {"association_id": "declared-log", "log_file_key": "synthetic:producer.log",
             "source_file_keys": ["synthetic:producer.sas"], "execution_id": "synthetic-execution",
             "run_id": "synthetic-run", "status": "DECLARED"},
            {"association_id": "declared-listing", "log_file_key": "synthetic:producer.lst",
             "source_file_keys": ["synthetic:producer.sas"], "execution_id": "synthetic-execution",
             "run_id": "synthetic-run", "status": "DECLARED"}],
    }


def refresh_coverage(graph: dict, inventory: dict) -> None:
    graph["coverage"] = coverage(graph, inventory)


def reidentify(graph: dict) -> None:
    """Re-hash intentionally edited fixture records and preserve their references."""
    fingerprint = graph["source_fingerprint"]
    node_map = {}
    for dataset in graph["datasets"]:
        previous = dataset["dataset_id"]
        dataset["dataset_id"] = record_id("ds", fingerprint, dataset, "dataset_id")
        node_map[previous] = dataset["dataset_id"]
    for column in graph["columns"]:
        previous = column["column_id"]
        column["dataset_id"] = node_map.get(column["dataset_id"], column["dataset_id"])
        column["column_id"] = record_id("col", fingerprint, column, "column_id")
        node_map[previous] = column["column_id"]
    operation_map = {}
    for operation in graph["operations"]:
        previous = operation["operation_id"]
        for field in ("reads", "writes"):
            operation[field] = [node_map.get(value, value) for value in operation[field]]
        operation["operation_id"] = record_id("op", fingerprint, operation, "operation_id")
        operation_map[previous] = operation["operation_id"]
    for edge in graph["edges"]:
        for field in ("from_operation_id", "to_operation_id"):
            edge[field] = operation_map.get(edge[field], edge[field])
        edge["evidence_operation_ids"] = [operation_map.get(value, value) for value in edge["evidence_operation_ids"]]
        edge["node_ids"] = [node_map.get(value, value) for value in edge["node_ids"]]
        edge["edge_id"] = record_id("edge", fingerprint, edge, "edge_id")
    for observation in graph["log_observations"]:
        observation["source_operation_ids"] = [operation_map.get(value, value) for value in observation["source_operation_ids"]]
        observation["observation_id"] = record_id("log", fingerprint, observation, "observation_id")
    for issue in graph["unknowns"] + graph["contradictions"]:
        issue["operation_ids"] = [operation_map.get(value, value) for value in issue["operation_ids"]]


def make_graph(scope: dict, attempt: str = "attempt1") -> tuple[dict, dict]:
    inventory = build_inventory(scope, attempt)
    fingerprint = inventory["source_fingerprint"]

    def identified(prefix, field, record):
        return {**record, field: record_id(prefix, fingerprint, record, field)}

    stage = identified("ds", "dataset_id", {
        "module_id": "prepare", "name": "work.stage", "semantic_verification": "UNVERIFIABLE"})
    final = identified("ds", "dataset_id", {
        "module_id": "analyze", "name": "work.final", "semantic_verification": "UNVERIFIABLE"})
    value = identified("col", "column_id", {
        "module_id": "prepare", "dataset_id": stage["dataset_id"], "name": "value",
        "semantic_verification": "UNVERIFIABLE"})
    doubled = identified("col", "column_id", {
        "module_id": "analyze", "dataset_id": final["dataset_id"], "name": "doubled",
        "semantic_verification": "UNVERIFIABLE"})
    producer = identified("op", "operation_id", {
        "module_id": "prepare", "kind": "DATA_STEP",
        "citations": [citation(scope, inventory, "synthetic:producer.sas", 3, 5)],
        "reads": [], "writes": [stage["dataset_id"], value["column_id"]], "stateful_constructs": [],
        "classification": "OBSERVATION", "semantic_verification": "UNVERIFIABLE"})
    consumer = identified("op", "operation_id", {
        "module_id": "analyze", "kind": "DATA_STEP",
        "citations": [citation(scope, inventory, "synthetic:consumer.sas", 2, 5)],
        "reads": [stage["dataset_id"], value["column_id"]],
        "writes": [final["dataset_id"], doubled["column_id"]], "stateful_constructs": [],
        "classification": "OBSERVATION", "semantic_verification": "UNVERIFIABLE"})
    edge = identified("edge", "edge_id", {
        "from_operation_id": producer["operation_id"], "to_operation_id": consumer["operation_id"],
        "type": "DATA", "node_ids": [stage["dataset_id"], value["column_id"]],
        "evidence_operation_ids": [producer["operation_id"], consumer["operation_id"]],
        "classification": "INFERENCE", "semantic_verification": "UNVERIFIABLE"})
    observation = identified("log", "observation_id", {
        "module_id": "prepare", "run_id": inventory["run_id"], "attempt_id": attempt,
        "association_id": "declared-log", "execution_id": "synthetic-execution",
        "log_citation": citation(scope, inventory, "synthetic:producer.log", 2, 2),
        "source_operation_ids": [producer["operation_id"]], "metric": "ROW_COUNT", "value": 1,
        "classification": "OBSERVATION", "semantic_verification": "UNVERIFIABLE"})
    graph = {
        "schema_version": "1.0", "workspace_id": inventory["workspace_id"], "run_id": inventory["run_id"],
        "attempt_id": attempt, "module_ids": inventory["module_ids"][:],
        "scope_manifest_sha256": digest(inventory), "source_fingerprint": fingerprint,
        "artifact_authority": "DRAFT", "semantic_verification": "UNVERIFIABLE",
        "datasets": [stage, final], "columns": [value, doubled], "operations": [producer, consumer],
        "edges": [edge], "log_observations": [observation], "unknowns": copy.deepcopy(inventory["unknowns"]),
        "contradictions": [],
    }
    refresh_coverage(graph, inventory)
    return inventory, graph
