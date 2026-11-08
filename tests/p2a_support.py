"""Adapters for reviewed public synthetic expectations, never hidden gold."""

from copy import deepcopy
import json
from pathlib import Path
import re

from sas_re.evidence import build_inventory, coverage, record_id
from sas_re.semantic import reconstruct


PROFILE_KEY = "synthetic:profile.json"


def prepare_case(root, case, *, profile_edit=None, scope_edit=None):
    """Write only a caller-owned temporary synthetic root; return scope/profile."""
    source = Path(root).resolve() / "sources"
    source.mkdir(parents=True)
    files = deepcopy(case["files"])
    profile = {
        "schema_version": "2.0", "profile_id": "sas94-synthetic-v1",
        "entrypoints": ["synthetic:main.sas"], "inputs": deepcopy(case.get("inputs", [])),
        "numeric_missing_join_policy": "SAS_ORDINARY_MISSING_EQUALS_MISSING",
        "log_bindings": [], "lst_bindings": [],
    }
    associations = []
    for index, original in enumerate(case.get("declared_bindings", [])):
        binding = deepcopy(original)
        name = binding.pop("file")
        operation_file = binding.pop("operation_file")
        operation_line = binding.pop("operation_line")
        execution = binding.pop("execution_id")
        association_id = "public-association-" + str(index)
        binding.update(association_id=association_id, operation_file_key="synthetic:" + operation_file,
                       operation_start=sum(map(len, files[operation_file].splitlines(keepends=True)[:operation_line-1])))
        profile["lst_bindings" if name.endswith(".lst") else "log_bindings"].append(binding)
        associations.append({"association_id": association_id, "log_file_key": "synthetic:" + name,
                             "source_file_keys": ["synthetic:" + operation_file],
                             "execution_id": execution, "run_id": "public-run", "status": "DECLARED"})
    if profile_edit:
        profile_edit(profile)
    files["profile.json"] = (json.dumps(profile, sort_keys=True, indent=2) + "\n").encode()
    dependencies = []
    for name, raw in files.items():
        if not name.endswith(".sas"):
            continue
        # This adapter declares only explicit fixture authorization. The product
        # still parses source, enforces exact scope and refuses dynamic includes.
        for include in re.findall(rb"%include\s+['\"]([^'\"]+)['\"]\s*;", raw, re.I):
            literal = include.decode("ascii")
            if literal in files and not any(d["from_file_key"] == "synthetic:" + name and d["to_file_key"] == "synthetic:" + literal for d in dependencies):
                dependencies.append({"dependency_id": "include-" + str(len(dependencies)),
                                     "from_file_key": "synthetic:" + name, "to_file_key": "synthetic:" + literal,
                                     "kind": "INCLUDE", "status": "DECLARED"})
    kinds = {name: "SAS" if name == "main.sas" else "INCLUDE" if name.endswith(".sas") else
             "LOG" if name.endswith(".log") else "LST" if name.endswith(".lst") else "CONFIG" for name in files}
    for name, raw in files.items():
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    scope = {
        "schema_version": "1.0", "workspace_id": "public-workspace", "run_id": "public-run",
        "module_ids": ["main"], "synthetic": True,
        "roots": [{"root_id": "synthetic", "path": str(source)}],
        "files": [{"file_key": "synthetic:" + name, "root_id": "synthetic", "path": name,
                   "kind": kinds[name], "module_id": "main", "encoding": "ascii"} for name in files],
        "dependencies": dependencies, "log_associations": associations,
    }
    if scope_edit:
        scope_edit(scope)
    return scope, profile


def make_case(root, case, *, attempt="reconstruct1", profile_edit=None, scope_edit=None):
    scope, profile = prepare_case(root, case, profile_edit=profile_edit, scope_edit=scope_edit)
    inventory = build_inventory(scope, attempt)
    graph = reconstruct(scope, inventory, profile, profile_file_key=PROFILE_KEY)
    return scope, inventory, profile, graph


def reidentify(graph, inventory):
    """Re-hash intentionally false public claims without stale ID short-circuits."""
    fingerprint = graph["source_fingerprint"]
    operation_ids = {}
    for operation in graph["operations"]:
        old = operation["operation_id"]
        operation["operation_id"] = record_id("op", fingerprint, operation, "operation_id")
        operation_ids[old] = operation["operation_id"]
    for edge in graph["edges"]:
        for field in ("from_operation_id", "to_operation_id"):
            edge[field] = operation_ids.get(edge[field], edge[field])
        edge["evidence_operation_ids"] = sorted(operation_ids.get(x, x) for x in edge["evidence_operation_ids"])
        edge["edge_id"] = record_id("edge", fingerprint, edge, "edge_id")
    for observation in graph["log_observations"]:
        observation["source_operation_ids"] = [operation_ids.get(x, x) for x in observation["source_operation_ids"]]
        observation["observation_id"] = record_id("log", fingerprint, observation, "observation_id")
    for statement in graph["statement_coverage"]:
        statement["operation_id"] = operation_ids.get(statement["operation_id"], statement["operation_id"])
    for issue in graph["unknowns"] + graph["contradictions"]:
        issue["operation_ids"] = [operation_ids.get(x, x) for x in issue["operation_ids"]]
    graph["coverage"] = coverage(graph, inventory)


def dataset_operation(graph, name):
    node = next(item["dataset_id"] for item in graph["datasets"] if item["name"] == name.lower())
    return next(item for item in graph["operations"] if node in item["writes"])


def tree(expression):
    """Project candidate syntax into reviewed assertion notation, no evaluation."""
    kind = expression["kind"]
    if kind == "group":
        return tree(expression["expression"])
    if kind == "name":
        return ("name", expression["name"])
    if kind == "literal":
        return ("literal", expression["lexeme"])
    if kind == "binary":
        return (expression["operator"], tree(expression["left"]), tree(expression["right"]))
    if kind == "unary":
        return (expression["operator"], tree(expression["operand"]))
    raise AssertionError("Expression adapter has no reviewed assertion for " + kind)


def condition(value):
    if value["kind"] == "by_flag":
        return value["flag"].upper() + "." + value["key"]
    return {"column": value["left"]["name"], "operator": value["operator"], "literal": value["right"]["lexeme"]}


def facts_of(operation, kind):
    return [fact for fact in operation["facts"] if fact["kind"] == kind]


def anchored_operation(graph, fact):
    anchor = fact["anchor"]
    owners = [op for op in graph["operations"] if op["span"]["file_key"] == "synthetic:" + anchor["file"]
              and op["span"]["line_start"] <= anchor["line"] <= op["span"]["line_end"]]
    if len(owners) != 1:
        raise AssertionError("Reviewed anchor must have exactly one canonical operation: " + str(anchor))
    return owners[0]


def all_citations(value):
    """Collect citation payloads so mutations demonstrate unchanged evidence."""
    found = []
    if isinstance(value, dict):
        if {"file_key", "source_sha256", "line_start", "line_end", "excerpt_sha256"} <= set(value):
            found.append(json.dumps(value, sort_keys=True))
        for child in value.values():
            found.extend(all_citations(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(all_citations(child))
    return set(found)
