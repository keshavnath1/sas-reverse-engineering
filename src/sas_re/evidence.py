"""P1 byte identity and supplied-record consistency. No SAS semantic extraction."""

import copy
import hashlib
import re
from pathlib import Path

from sas_re.contracts import validate_contract
from sas_re.safeio import (EvidenceError, canonical_bytes, enumerate_files,
                           require_safe_root, safe_relative, secure_read)


def digest(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def identity(prefix: str, fingerprint: str, payload: dict) -> str:
    """IDs bind the entire source scope and all supplied identity-bearing facts."""
    return prefix + "_" + digest({"source_fingerprint": fingerprint, "payload": payload})


def record_id(prefix: str, fingerprint: str, record: dict, id_field: str) -> str:
    return identity(prefix, fingerprint, {k: v for k, v in record.items() if k != id_field})


def _unique(values: list, code: str) -> None:
    if len(values) != len(set(values)):
        raise EvidenceError(code)


def scope_identity(scope: dict) -> str:
    """Physical root locations are authorization bindings, not portable identities."""
    value = copy.deepcopy(scope)
    value["roots"] = [{"root_id": r["root_id"]} for r in sorted(scope["roots"], key=lambda x: x["root_id"])]
    value["module_ids"] = sorted(value["module_ids"])
    for field, key in [("files", "file_key"), ("dependencies", "dependency_id"),
                       ("log_associations", "association_id")]:
        value[field] = sorted(value[field], key=lambda x: x[key])
    for link in value["log_associations"]:
        link["source_file_keys"] = sorted(link["source_file_keys"])
    return digest(value)


def validate_scope(scope: dict) -> dict[str, Path]:
    validate_contract("Scope", scope)
    roots = {item["root_id"]: Path(item["path"]) for item in scope["roots"]}
    _unique([item["root_id"] for item in scope["roots"]], "DUPLICATE_ROOT")
    for root in roots.values():
        require_safe_root(root)
    for first, path in roots.items():
        for second, other in roots.items():
            if first != second and (path == other or path in other.parents or other in path.parents):
                raise EvidenceError("OVERLAPPING_ROOTS")
    _unique([item["file_key"] for item in scope["files"]], "DUPLICATE_FILE")
    _unique([(item["root_id"], item["path"]) for item in scope["files"]], "DUPLICATE_FILE")
    for item in scope["files"]:
        safe_relative(item["path"])
        if item["root_id"] not in roots or item["module_id"] not in scope["module_ids"]:
            raise EvidenceError("SCOPE_OWNER_MISMATCH")
        if item["file_key"] != item["root_id"] + ":" + item["path"]:
            raise EvidenceError("FILE_KEY_MISMATCH")
    _unique([item["dependency_id"] for item in scope["dependencies"]], "DUPLICATE_DEPENDENCY")
    _unique([item["association_id"] for item in scope["log_associations"]], "DUPLICATE_LOG_ASSOCIATION")
    return roots


def byte_lines(data: bytes) -> list[bytes]:
    # Only CR, LF and CRLF delimit lines. Do not normalize bytes or strip a BOM.
    return [line for line in re.findall(rb"[^\r\n]*(?:\r\n|\r|\n|$)", data) if line]


def _newline(data: bytes) -> str:
    found = set(re.findall(rb"\r\n|\r|\n", data))
    if len(found) > 1:
        return "MIXED"
    return {b"\n": "LF", b"\r\n": "CRLF", b"\r": "CR"}.get(next(iter(found), b""), "NONE")


def _issue(kind: str, keys: list[str], seed: object) -> dict:
    return {"issue_id": "issue_" + digest(seed)[:24], "kind": kind,
            "file_keys": sorted(keys), "operation_ids": [], "status": "UNRESOLVED"}


def build_inventory(scope: dict, attempt_id: str) -> dict:
    roots = validate_scope(scope)
    declared = {item["file_key"]: item for item in scope["files"]}
    # Authorize enumeration independently. Never read the contents of added files.
    for root_id, root in roots.items():
        actual = {root_id + ":" + name for name in enumerate_files(root)}
        expected = {key for key, item in declared.items() if item["root_id"] == root_id}
        if actual - expected:
            raise EvidenceError("SCOPE_ADDED_FILE", "BLOCKED")
        if expected - actual:
            raise EvidenceError("SCOPE_MISSING_FILE", "BLOCKED")
    files = []
    total = 0
    for key, item in sorted(declared.items()):
        raw = secure_read(roots[item["root_id"]], item["path"])
        total += len(raw)
        if total > 64 * 1024 * 1024:
            raise EvidenceError("SCOPE_TOO_LARGE", "BLOCKED")
        if item["encoding"] != "binary":
            try:
                raw.decode(item["encoding"], errors="strict")
            except UnicodeError:
                raise EvidenceError("ENCODING_MISMATCH") from None
        entry = {**item, "sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw),
                 "line_count": len(byte_lines(raw)) if item["encoding"] != "binary" else 0,
                 "newline": _newline(raw) if item["encoding"] != "binary" else "BINARY"}
        entry["file_id"] = identity("file", "", entry)
        files.append(entry)
    unknowns = []
    for dep in scope["dependencies"]:
        if dep["from_file_key"] not in declared:
            raise EvidenceError("DEPENDENCY_SOURCE_MISSING")
        target = dep["to_file_key"]
        if dep["status"] == "UNRESOLVED" or target is None or target not in declared:
            keys = [dep["from_file_key"]]
            if target in declared:
                keys.append(target)
            unknowns.append(_issue("DYNAMIC_DEPENDENCY" if target is None else "MISSING_DEPENDENCY", keys, dep))
    linked = set()
    for association in scope["log_associations"]:
        if association["run_id"] != scope["run_id"]:
            raise EvidenceError("LOG_RUN_MISMATCH")
        log_key = association["log_file_key"]
        if log_key in linked:
            raise EvidenceError("AMBIGUOUS_LOG_PROVENANCE", "BLOCKED")
        if log_key not in declared or declared[log_key]["kind"] not in {"LOG", "LST"}:
            raise EvidenceError("LOG_FILE_MISMATCH")
        for key in association["source_file_keys"]:
            if key not in declared or declared[key]["kind"] not in {"SAS", "INCLUDE"}:
                raise EvidenceError("LOG_SOURCE_MISSING", "BLOCKED")
        linked.add(log_key)
    for key, item in declared.items():
        if item["kind"] in {"LOG", "LST"} and key not in linked:
            unknowns.append(_issue("MISSING_LOG_PROVENANCE", [key], key))
    # A second bounded byte pass catches changes to earlier files while later
    # files were read. This is not an OS-wide snapshot or a production lock.
    for item in files:
        raw = secure_read(roots[item["root_id"]], item["path"])
        if hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise EvidenceError("SOURCE_CHANGED_DURING_READ")
    # Re-enumerate after reads, so additions/removals during inventory are detected.
    for root_id, root in roots.items():
        if {root_id + ":" + name for name in enumerate_files(root)} != {
                key for key, item in declared.items() if item["root_id"] == root_id}:
            raise EvidenceError("SCOPE_CHANGED_DURING_READ")
    scope_sha = scope_identity(scope)
    value = {"schema_version": "1.0", "workspace_id": scope["workspace_id"],
             "run_id": scope["run_id"], "attempt_id": attempt_id,
             "module_ids": sorted(scope["module_ids"]), "scope_sha256": scope_sha,
             "source_fingerprint": digest({"scope_sha256": scope_sha, "files": files}),
             "files": files, "dependencies": sorted(scope["dependencies"], key=lambda x: x["dependency_id"]),
             "log_associations": sorted(scope["log_associations"], key=lambda x: x["association_id"]),
             "unknowns": sorted(unknowns, key=lambda x: x["issue_id"])}
    validate_contract("Inventory", value)
    return value


def citation(scope: dict, inventory: dict, file_key: str, start: int, end: int) -> dict:
    """Construct a byte-exact locator, without returning or storing source text."""
    roots = validate_scope(scope)
    validate_contract("Inventory", inventory)
    declared = next((f for f in scope["files"] if f["file_key"] == file_key), None)
    item = next((f for f in inventory["files"] if f["file_key"] == file_key), None)
    if (declared is None or item is None or item["encoding"] == "binary"
            or any(item[key] != value for key, value in declared.items())):
        raise EvidenceError("CITATION_FILE_INVALID")
    data = secure_read(roots[item["root_id"]], item["path"])
    if hashlib.sha256(data).hexdigest() != item["sha256"]:
        raise EvidenceError("STALE_SOURCE")
    lines = byte_lines(data)
    if type(start) is not int or type(end) is not int or not 1 <= start <= end <= len(lines):
        raise EvidenceError("CITATION_RANGE_INVALID")
    return {"file_key": file_key, "source_sha256": item["sha256"], "line_start": start,
            "line_end": end, "excerpt_sha256": hashlib.sha256(b"".join(lines[start - 1:end])).hexdigest()}


def coverage(graph: dict, inventory: dict) -> dict:
    return {"file_count": len(inventory["files"]), "operation_count": len(graph["operations"]),
            "dataset_count": len(graph["datasets"]), "column_count": len(graph["columns"]),
            "edge_count": len(graph["edges"]), "log_observation_count": len(graph["log_observations"]),
            "unknown_count": len(graph["unknowns"]), "contradiction_count": len(graph["contradictions"]),
            "covered_source_file_count": len({c["file_key"] for op in graph["operations"] for c in op["citations"]})}


def validation_report(findings: list[dict] | None = None, counts: dict | None = None,
                      structural: str = "PASSED") -> dict:
    findings = findings or []
    gates = {f["gate"] for f in findings}
    gate = "FAIL" if "FAIL" in gates else "BLOCKED" if gates else "PASS"
    result = {"schema_version": "1.0", "stage_gate": gate, "structural_verification": structural,
              "semantic_verification": "UNVERIFIABLE", "benchmark_execution": "NOT_RUN",
              "artifact_authority": "DRAFT", "findings": findings, "coverage": counts}
    validate_contract("Report", result)
    return result


def error_report(error: EvidenceError) -> dict:
    return validation_report([{"code": error.code, "gate": error.gate}],
                             structural="FAILED" if error.gate == "FAIL" else "BLOCKED")


def validate_record(scope: dict, inventory: dict, graph: dict) -> dict:
    """Checks supplied relationships and locators, never their SAS semantic truth."""
    validate_contract("Inventory", inventory)
    validate_contract("Graph", graph)
    for field in ["workspace_id", "run_id", "attempt_id", "module_ids", "source_fingerprint"]:
        if graph[field] != inventory[field]:
            raise EvidenceError("RECORD_OWNER_MISMATCH")
    if graph["scope_manifest_sha256"] != digest(inventory):
        raise EvidenceError("INVENTORY_HASH_MISMATCH")
    if inventory != build_inventory(scope, inventory["attempt_id"]):
        raise EvidenceError("STALE_SOURCE")
    modules = set(inventory["module_ids"])
    files = {f["file_key"]: f for f in inventory["files"]}
    tables = {}
    for field, id_field, prefix in [("datasets", "dataset_id", "ds"), ("columns", "column_id", "col"),
                                   ("operations", "operation_id", "op"), ("edges", "edge_id", "edge"),
                                   ("log_observations", "observation_id", "log")]:
        _unique([x[id_field] for x in graph[field]], "DUPLICATE_" + field.upper())
        tables[field] = {x[id_field]: x for x in graph[field]}
        for item in graph[field]:
            if "module_id" in item and item["module_id"] not in modules:
                raise EvidenceError("MODULE_OWNER_MISMATCH")
            if item[id_field] != record_id(prefix, inventory["source_fingerprint"], item, id_field):
                raise EvidenceError("UNSTABLE_" + field.upper() + "_ID")
    datasets, columns, operations = tables["datasets"], tables["columns"], tables["operations"]
    nodes = {**datasets, **columns}
    for item in columns.values():
        if item["dataset_id"] not in datasets:
            raise EvidenceError("DANGLING_COLUMN_DATASET")
        if item["module_id"] != datasets[item["dataset_id"]]["module_id"]:
            raise EvidenceError("COLUMN_OWNER_MISMATCH")
    for op in operations.values():
        if any(n not in nodes for n in op["reads"] + op["writes"]):
            raise EvidenceError("DANGLING_OPERATION_NODE")
        for c in op["citations"]:
            if c["file_key"] not in files or files[c["file_key"]]["kind"] in {"LOG", "LST", "REFERENCE"}:
                raise EvidenceError("OPERATION_CITATION_FILE_INVALID")
            if files[c["file_key"]]["module_id"] != op["module_id"]:
                raise EvidenceError("OPERATION_SOURCE_OWNER_MISMATCH")
            if c != citation(scope, inventory, c["file_key"], c["line_start"], c["line_end"]):
                raise EvidenceError("CITATION_HASH_MISMATCH")
    for edge in graph["edges"]:
        source, target = edge["from_operation_id"], edge["to_operation_id"]
        if source not in operations or target not in operations or any(
                op not in operations for op in edge["evidence_operation_ids"]):
            raise EvidenceError("DANGLING_EDGE_OPERATION")
        if any(n not in nodes for n in edge["node_ids"]):
            raise EvidenceError("DANGLING_EDGE_NODE")
        if edge["type"] == "DATA":
            if not edge["node_ids"] or any(n not in operations[source]["writes"] or
                                           n not in operations[target]["reads"] for n in edge["node_ids"]):
                raise EvidenceError("PRODUCER_CONSUMER_MISMATCH")
        if edge["type"] == "UNKNOWN" and not any(
                source in issue["operation_ids"] and target in issue["operation_ids"] for issue in graph["unknowns"]):
            raise EvidenceError("UNKNOWN_EDGE_NOT_RECORDED")
    issues = graph["unknowns"] + graph["contradictions"]
    _unique([i["issue_id"] for i in issues], "DUPLICATE_ISSUE")
    for issue in issues:
        if any(k not in files for k in issue["file_keys"]) or any(k not in operations for k in issue["operation_ids"]):
            raise EvidenceError("DANGLING_ISSUE_REFERENCE")
    for issue in inventory["unknowns"]:
        if issue not in graph["unknowns"]:
            raise EvidenceError("OMITTED_UNKNOWN")
    if any(issue["kind"] != "CONTRADICTION" for issue in graph["contradictions"]):
        raise EvidenceError("INVALID_CONTRADICTION")
    if any(issue["kind"] == "CONTRADICTION" for issue in graph["unknowns"]):
        raise EvidenceError("MISPLACED_CONTRADICTION")
    associations = {a["association_id"]: a for a in inventory["log_associations"]}
    for observation in graph["log_observations"]:
        if observation["run_id"] != inventory["run_id"] or observation["attempt_id"] != inventory["attempt_id"]:
            raise EvidenceError("LOG_OWNER_MISMATCH")
        association = associations.get(observation["association_id"])
        if association is None:
            raise EvidenceError("MISSING_LOG_PROVENANCE", "BLOCKED")
        if observation["execution_id"] != association["execution_id"]:
            raise EvidenceError("LOG_EXECUTION_MISMATCH")
        c = observation["log_citation"]
        if c["file_key"] != association["log_file_key"] or files[c["file_key"]]["module_id"] != observation["module_id"]:
            raise EvidenceError("LOG_CITATION_MISMATCH")
        if c != citation(scope, inventory, c["file_key"], c["line_start"], c["line_end"]):
            raise EvidenceError("LOG_CITATION_HASH_MISMATCH")
        for op_id in observation["source_operation_ids"]:
            if op_id not in operations:
                raise EvidenceError("DANGLING_LOG_OPERATION")
            if not any(c["file_key"] in association["source_file_keys"] for c in operations[op_id]["citations"]):
                raise EvidenceError("LOG_SOURCE_MISMATCH")
    counts = coverage(graph, inventory)
    if graph["coverage"] != counts:
        raise EvidenceError("COVERAGE_MISMATCH")
    findings = []
    if graph["unknowns"]:
        findings.append({"code": "UNRESOLVED_UNKNOWNS", "gate": "BLOCKED"})
    if graph["contradictions"]:
        findings.append({"code": "DECLARED_CONTRADICTIONS", "gate": "FAIL"})
    return validation_report(findings, counts)


def module_view(graph: dict, module_id: str) -> dict:
    validate_contract("Graph", graph)
    if module_id not in graph["module_ids"]:
        raise EvidenceError("UNKNOWN_MODULE")
    ops = {o["operation_id"] for o in graph["operations"] if o["module_id"] == module_id}
    node_refs = {n for o in graph["operations"] if o["operation_id"] in ops for n in o["reads"] + o["writes"]}
    node_refs.update(n["dataset_id"] for n in graph["columns"] if n["column_id"] in node_refs)
    view = {"schema_version": "1.0", **{k: graph[k] for k in ("workspace_id", "run_id", "attempt_id")},
            "module_id": module_id, "source_record_sha256": digest(graph), "operation_ids": sorted(ops),
            "dataset_ids": sorted(n["dataset_id"] for n in graph["datasets"] if n["module_id"] == module_id or n["dataset_id"] in node_refs),
            "column_ids": sorted(n["column_id"] for n in graph["columns"] if n["module_id"] == module_id or n["column_id"] in node_refs),
            "edge_ids": sorted(e["edge_id"] for e in graph["edges"] if e["from_operation_id"] in ops or e["to_operation_id"] in ops),
            "log_observation_ids": sorted(o["observation_id"] for o in graph["log_observations"] if o["module_id"] == module_id),
            "artifact_authority": "DRAFT", "semantic_verification": "UNVERIFIABLE"}
    validate_contract("ModuleView", view)
    return view


def revision_map(previous: dict, current: dict) -> dict:
    for record in (previous, current):
        validate_contract("Graph", record)
        for op in record["operations"]:
            if op["operation_id"] != record_id("op", record["source_fingerprint"], op, "operation_id"):
                raise EvidenceError("UNSTABLE_OPERATIONS_ID")
    if previous["workspace_id"] != current["workspace_id"] or previous["run_id"] != current["run_id"]:
        raise EvidenceError("REVISION_OWNER_MISMATCH")
    old = {o["operation_id"] for o in previous["operations"]}
    new = {o["operation_id"] for o in current["operations"]}
    result = {"schema_version": "1.0", "previous_record_sha256": digest(previous),
              "current_record_sha256": digest(current), "retained_operation_ids": sorted(old & new),
              "removed_operation_ids": sorted(old - new), "added_operation_ids": sorted(new - old),
              "semantic_equivalence": "NOT_ASSERTED"}
    validate_contract("RevisionMap", result)
    return result
