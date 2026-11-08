"""Reconstruct bounded semantic evidence without executing SAS.

JSON schemas remain the record authority: this module consumes a v1 inventory
and v2 profile and emits v2 semantic records. Authorized, read-only source reads
bind citations and spans to ORIGINAL BYTES, not normalized text. Profile
assumptions, source inferences, and unresolved proof obligations stay distinct.

Rebuilding records checks deterministic source consistency, not independent
semantic acceptance. Outputs remain drafts; human reviewers own business intent
and approvals. No SAS runtime equivalence or benchmark execution is asserted.
"""

from copy import deepcopy
from fractions import Fraction
import hashlib
from pathlib import PurePosixPath

from .contracts import validate_contract, validate_versioned_contract
from .evidence import (
    build_inventory,
    byte_lines,
    citation,
    coverage,
    digest,
    record_id,
    validate_scope,
)
from .safeio import EvidenceError, _parse_json, safe_relative, secure_read


def _check(name, value):
    validate_contract(name, value, version="2.0")


def _expressions(value):
    if isinstance(value, dict):
        if value.get("kind") in {"literal", "name", "unary", "binary", "group", "lag"}:
            yield value
        for key, child in value.items():
            if key not in {"span", "definition_span"}:
                yield from _expressions(child)
    elif isinstance(value, list):
        for child in value:
            yield from _expressions(child)


def _names(value):
    return {expr["name"].lower() for expr in _expressions(value) if expr["kind"] == "name"}


def _decimal(value):
    if value == ".":
        return None
    try:
        result = Fraction(value)
    except (ValueError, ZeroDivisionError):
        raise EvidenceError("PROFILE_NUMERIC_INVALID") from None
    if (
        abs(result) > 2**20
        or result.denominator > 1024
        or result.denominator & (result.denominator - 1)
    ):
        raise EvidenceError("PROFILE_NUMERIC_OUTSIDE_SUBSET", "BLOCKED")
    return result


def _bound(expression, ranges):
    """Return conservative exact-rational bounds, not executed row values."""
    kind = expression["kind"]
    if kind == "literal":
        value = _decimal(expression["lexeme"])
        return (Fraction(0), Fraction(0), 1) if value is None else (value, value, value.denominator)
    if kind == "name":
        return ranges.get(expression["name"].lower())
    if kind == "group":
        return _bound(expression["expression"], ranges)
    if kind == "lag":
        return _bound(expression["argument"], ranges)
    if kind == "unary":
        value = _bound(expression["operand"], ranges)
        if value and expression["operator"] == "-":
            return (-value[1], -value[0], value[2])
        return value
    left, right = _bound(expression["left"], ranges), _bound(expression["right"], ranges)
    if left is None or right is None:
        return None
    op = expression["operator"]
    if op == "+":
        value = (left[0] + right[0], left[1] + right[1], max(left[2], right[2]))
    elif op == "-":
        value = (left[0] - right[1], left[1] - right[0], max(left[2], right[2]))
    elif op == "*":
        products = [a * b for a in left[:2] for b in right[:2]]
        value = (min(products), max(products), left[2] * right[2])
    else:
        # Division is restricted to a literal nonzero power of two; no guessed
        # data-dependent denominator or floating point equivalence.
        divisor = right[0]
        literal = expression["right"]
        while literal["kind"] in {"group", "unary"}:
            literal = literal["expression"] if literal["kind"] == "group" else literal["operand"]
        if right[0] != right[1] or not divisor or literal["kind"] != "literal":
            return None
        numerator = abs(divisor.numerator)
        if numerator & (numerator - 1):
            return None
        values = [left[0] / divisor, left[1] / divisor]
        value = (min(values), max(values), left[2] * numerator)
    if value[2] > 2**1074 or max(abs(value[0]), abs(value[1])) * value[2] > 2**53:
        return None
    return value


def reconstruct(
    scope: dict,
    inventory: dict,
    profile: dict,
    predecessor: dict | None = None,
    *,
    profile_file_key: str,
) -> dict:
    """Build a draft v2 graph from authorized source and synthetic assumptions.

    Reads authorized evidence without writing artifacts or mutating input records.
    Unsupported semantics remain unresolved; a successful return does not grant
    semantic acceptance or publication authority. SAS is never executed.

    Args:
        scope: Authorization scope and module ownership declarations.
        inventory: V1 inventory whose identities must match current evidence.
        profile: V2 synthetic input and interpretation assumptions.
        predecessor: Optional versioned graph checked by ``revision_map``;
            the resulting map is not attached to the returned graph.
        profile_file_key: Inventoried CONFIG file binding the profile to bytes.

    Returns:
        A schema-validated v2 graph with byte-bound evidence and proof limits.

    Raises:
        EvidenceError: If contracts, authorization, evidence identities, supported
            limits, or optional predecessor checks fail.
    """
    from .sas_subset import parse_source
    from .observations import extract_observations

    roots = validate_scope(scope)
    validate_contract("Inventory", inventory)
    _check("Profile", profile)
    if inventory != build_inventory(scope, inventory["attempt_id"]):
        raise EvidenceError("STALE_SOURCE")
    files = {f["file_key"]: f for f in inventory["files"]}
    config = files.get(profile_file_key)
    if config is None or config["kind"] != "CONFIG" or config["encoding"] not in {"utf-8", "ascii"}:
        raise EvidenceError("PROFILE_NOT_AUTHORIZED")
    raw_config = secure_read(roots[config["root_id"]], config["path"])
    # Equal parsed JSON is insufficient: the profile must also match inventoried bytes.
    if (
        _parse_json(raw_config) != profile
        or hashlib.sha256(raw_config).hexdigest() != config["sha256"]
    ):
        raise EvidenceError("PROFILE_SOURCE_MISMATCH")
    source_files = {key: f for key, f in files.items() if f["kind"] in {"SAS", "INCLUDE"}}
    if (
        len(source_files) > 20
        or len(scope["module_ids"]) > 8
        or sum(f["line_count"] for f in source_files.values()) > 10000
    ):
        raise EvidenceError("RECONSTRUCTION_BUDGET_EXCEEDED", "BLOCKED")
    raw_sources = {}
    for key, file in source_files.items():
        if file["encoding"] not in {"ascii", "utf-8"}:
            raise EvidenceError("RECONSTRUCTION_ENCODING_UNSUPPORTED", "BLOCKED")
        raw_sources[key] = secure_read(roots[file["root_id"]], file["path"])
        if hashlib.sha256(raw_sources[key]).hexdigest() != file["sha256"]:
            raise EvidenceError("STALE_SOURCE")
    if any(
        key not in source_files or source_files[key]["kind"] != "SAS"
        for key in profile["entrypoints"]
    ):
        raise EvidenceError("ENTRYPOINT_NOT_AUTHORIZED")
    profile_citation = citation(scope, inventory, profile_file_key, 1, config["line_count"])
    fingerprint = inventory["source_fingerprint"]
    graph = {
        "schema_version": "2.0",
        **{
            k: inventory[k]
            for k in ("workspace_id", "run_id", "attempt_id", "module_ids", "source_fingerprint")
        },
        "scope_manifest_sha256": digest(inventory),
        "inventory_schema_version": "1.0",
        "profile_file_key": profile_file_key,
        "profile_sha256": config["sha256"],
        "interpretation_profile": profile["profile_id"],
        "artifact_authority": "DRAFT",
        "semantic_verification": "UNVERIFIABLE",
        "semantic_acceptance": "BLOCKED",
        "benchmark_execution": "NOT_RUN",
        "datasets": [],
        "columns": [],
        "operations": [],
        "edges": [],
        "log_observations": [],
        "unknowns": [],
        "contradictions": [],
        "statement_coverage": [],
    }

    def bound_span(span):
        key, start, end = span["file_key"], span["start"], span["end"]
        if key not in raw_sources or not 0 <= start < end <= len(raw_sources[key]):
            raise EvidenceError("PARSER_SPAN_INVALID")
        raw = raw_sources[key]
        # Spans index ORIGINAL BYTES; raw line starts retain CRLF widths.
        offset = 0
        touched = []
        for number, line in enumerate(byte_lines(raw), 1):
            if offset < end and offset + len(line) > start:
                touched.append(number)
            offset += len(line)
        if not touched or [span["line_start"], span["line_end"]] != [touched[0], touched[-1]]:
            raise EvidenceError("PARSER_LINE_INVALID")
        return {
            **span,
            "citation": citation(scope, inventory, key, touched[0], touched[-1]),
            "byte_sha256": hashlib.sha256(raw[start:end]).hexdigest(),
        }

    def bind(value):
        if isinstance(value, dict):
            if set(value) == {"file_key", "start", "end", "line_start", "line_end"}:
                return bound_span(value)
            return {key: bind(child) for key, child in value.items()}
        if isinstance(value, list):
            return [bind(child) for child in value]
        return value

    def issue(code, *, span=None, operation_ids=None, file_key=None, contradiction=False, cit=None):
        spans = [bound_span(span)] if span else []
        citations = [s["citation"] for s in spans] + ([cit] if cit else [])
        keys = sorted(
            {s["file_key"] for s in spans}
            | ({file_key} if file_key else set())
            | {c["file_key"] for c in citations}
        )
        value = {
            "kind": "CONTRADICTION" if contradiction else "OTHER",
            "file_keys": keys,
            "operation_ids": operation_ids or [],
            "status": "UNRESOLVED",
            "code": code,
            "citations": citations,
            "spans": spans,
            "missing_proof": code,
        }
        value["issue_id"] = "issue_" + digest(value)[:24]
        target = graph["contradictions" if contradiction else "unknowns"]
        if value not in target:
            target.append(value)

    for original in inventory["unknowns"]:
        graph["unknowns"].append(
            {
                **original,
                "code": original["kind"],
                "citations": [],
                "spans": [],
                "missing_proof": original["kind"],
            }
        )
    used = set()

    def include_loader(from_key, literal):
        safe_relative(literal)
        source = files[from_key]
        rel = str(PurePosixPath(source["path"]).parent / literal)
        safe_relative(rel)
        target = source["root_id"] + ":" + rel
        # A safe same-root path still requires an inventoried, declared dependency.
        if target not in source_files or source_files[target]["kind"] != "INCLUDE":
            raise KeyError("INCLUDE_NOT_AUTHORIZED")
        if not any(
            d["from_file_key"] == from_key
            and d["to_file_key"] == target
            and d["kind"] == "INCLUDE"
            and d["status"] == "DECLARED"
            for d in inventory["dependencies"]
        ):
            raise KeyError("INCLUDE_DEPENDENCY_UNDECLARED")
        if target in used:
            raise ValueError("REPEATED_INCLUDE_UNSUPPORTED")
        used.add(target)
        return target, raw_sources[target]

    parsed_ops, statements, parser_issues = [], [], []
    macros = {}
    for entry in profile["entrypoints"]:
        if entry in used:
            issue("REPEATED_ENTRYPOINT_UNSUPPORTED", file_key=entry)
            continue
        used.add(entry)
        if not raw_sources[entry].strip():
            issue("EMPTY_ENTRYPOINT", file_key=entry)
        result = parse_source(
            raw_sources[entry], file_key=entry, macros=macros, include_loader=include_loader
        )
        parsed_ops.extend(result["operations"])
        statements.extend(result["statements"])
        parser_issues.extend(result["issues"])
    if len(parsed_ops) > 100:
        raise EvidenceError("RECONSTRUCTION_BUDGET_EXCEEDED", "BLOCKED")
    for key in sorted(source_files.keys() - used):
        issue("SOURCE_NOT_REACHED", file_key=key)
    for parsed_issue in parser_issues:
        issue(parsed_issue["code"], span=parsed_issue["span"])

    datasets, columns, schemas, orders, ranges, declared_rows, row_bounds, tainted_outputs = (
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        set(),
    )

    def dataset(name, owner, role, cites):
        name = name.lower()
        if name not in datasets:
            value = {
                "module_id": owner,
                "name": name,
                "semantic_verification": "UNVERIFIABLE",
                "role": role,
                "citations": cites,
            }
            value["dataset_id"] = record_id("ds", fingerprint, value, "dataset_id")
            datasets[name] = value
            graph["datasets"].append(value)
        return datasets[name]

    def column(dsname, name, cites):
        key = (dsname.lower(), name.lower())
        if key not in columns:
            ds = datasets[key[0]]
            value = {
                "module_id": ds["module_id"],
                "dataset_id": ds["dataset_id"],
                "name": key[1],
                "semantic_verification": "UNVERIFIABLE",
                "type": "NUMERIC",
                "length": 8,
                "citations": cites,
            }
            value["column_id"] = record_id("col", fingerprint, value, "column_id")
            columns[key] = value
            graph["columns"].append(value)
        return columns[key]

    for source in profile["inputs"]:
        name = source["name"].lower()
        names = [c["name"].lower() for c in source["columns"]]
        if (
            name in datasets
            or len(names) != len(set(names))
            or source["module_id"] not in inventory["module_ids"]
        ):
            raise EvidenceError("PROFILE_INPUT_OWNER_INVALID")
        if any(key.lower() not in names for key in source["sorted_by"]):
            raise EvidenceError("PROFILE_SORT_COLUMN_INVALID")
        dataset(name, source["module_id"], "INPUT", [profile_citation])
        schemas[name] = names
        for name_col in names:
            column(name, name_col, [profile_citation])
        vals = [[] for _ in names]
        rows = []
        for row in source["rows"]:
            if len(row) != len(names):
                raise EvidenceError("PROFILE_ROW_WIDTH_INVALID")
            numbers = [_decimal(item) for item in row]
            rows.append(numbers)
            for bucket, number in zip(vals, numbers):
                if number is not None:
                    bucket.append(number)
        declared_rows[name] = rows
        row_bounds[name] = len(rows)
        ranges[name] = {
            col: (
                min(v) if v else Fraction(0),
                max(v) if v else Fraction(0),
                max((x.denominator for x in v), default=1),
            )
            for col, v in zip(names, vals)
        }
        sort_keys = [key.lower() for key in source["sorted_by"]]
        ordered_rows = [
            tuple(
                (0, 0) if row[names.index(key)] is None else (1, row[names.index(key)])
                for key in sort_keys
            )
            for row in rows
        ]
        if ordered_rows != sorted(ordered_rows):
            issue(
                "DECLARED_SORT_CONTRADICTED",
                file_key=profile_file_key,
                contradiction=True,
                cit=profile_citation,
            )
            orders[name] = ([], "UNRESOLVED")
        else:
            orders[name] = (sort_keys, "DECLARED_SYNTHETIC_INPUT")

    anchors = {}
    producers = {}
    context_tainted = False
    for sequence, parsed in enumerate(parsed_ops):
        span = parsed["span"]
        owner = files[span["file_key"]]["module_id"]
        facts = parsed["facts"]
        reads = [name.lower() for name in parsed["reads"]]
        writes = [name.lower() for name in parsed["writes"]]
        source_cit = citation(
            scope, inventory, span["file_key"], span["line_start"], span["line_end"]
        )
        op_issues = []

        def problem(code):
            if code not in op_issues:
                op_issues.append(code)

        if context_tainted:
            problem("PRIOR_SOURCE_UNRESOLVED")
        if parsed.get("issues"):
            context_tainted = True
        for read in reads:
            if read not in datasets:
                dataset(read, owner, "UNRESOLVED", [source_cit])
                schemas[read], orders[read], ranges[read], row_bounds[read] = (
                    [],
                    ([], "UNRESOLVED"),
                    {},
                    0,
                )
                problem("INPUT_SCHEMA_UNRESOLVED")
            if read in tainted_outputs:
                problem("PRODUCER_EVIDENCE_UNRESOLVED")
        if any(name in datasets for name in writes):
            problem("DATASET_OVERWRITE_UNSUPPORTED")
        output_names = list(dict.fromkeys(name for read in reads for name in schemas[read]))
        env = {}
        for read in reads:
            for col, bounds in ranges[read].items():
                if col in env:
                    old = env[col]
                    env[col] = (
                        min(old[0], bounds[0]),
                        max(old[1], bounds[1]),
                        max(old[2], bounds[2]),
                    )
                else:
                    env[col] = bounds
        input_env = dict(env)
        for read in reads:
            for col in schemas[read]:
                if col not in ranges[read]:
                    input_env.pop(col, None)
                    env.pop(col, None)
        sql = next((f for f in facts if f["kind"] == "sql"), None)
        by = next((f for f in facts if f["kind"] == "by"), None)
        inp = next((f for f in facts if f["kind"] == "input"), None)
        sort = next((f for f in facts if f["kind"] == "sort"), None)
        iteration_bound = sum(row_bounds.get(name, 0) for name in reads)
        retained = {f["target"] for f in facts if f["kind"] in {"retain", "sum"}}
        input_index = next((i for i, f in enumerate(facts) if f["kind"] == "input"), None)
        early_input_reads = []
        if input_index is not None:
            input_columns = {name for read in reads for name in schemas[read]}
            for index, fact in enumerate(facts[:input_index]):
                if (
                    fact["kind"] in {"assignment", "sum", "subset_if"}
                    and _names(fact) & input_columns
                ):
                    early_input_reads.append(index)
                    problem("INPUT_READ_ORDER_UNRESOLVED")
        keep_lists, drop_names = [], set()
        if sql:
            output_names = [item["output"].lower() for item in sql["select"]]
            env = {
                i["alias"].lower() + "." + col: bounds
                for i in sql["inputs"]
                for col, bounds in ranges[i["dataset"].lower()].items()
            }
            if len(output_names) != len(set(output_names)):
                problem("SQL_DUPLICATE_OUTPUT_UNSUPPORTED")
        # SAS RETAIN initializes at compile time, irrespective of its textual
        # position. SUM also retains and defaults to zero absent explicit RETAIN.
        for fact in facts:
            if fact["kind"] == "retain":
                try:
                    env[fact["target"]] = _bound(fact["initial"], env)
                except EvidenceError:
                    env[fact["target"]] = None
            elif fact["kind"] == "sum":
                env.setdefault(fact["target"], (Fraction(0), Fraction(0), 1))
        for name in list(env):
            if env[name] is None:
                problem("NUMERIC_EXACTNESS_UNRESOLVED")
                del env[name]
        for fact in facts:
            if fact["kind"] == "input":
                # SET/MERGE supplies the current input PDV values at this
                # source statement; RETAIN initialization cannot replace them.
                for col in {name for read in reads for name in schemas[read]}:
                    env.pop(col, None)
                env.update(input_env)
            if fact["kind"] in {"assignment", "sum", "retain"}:
                target = fact["target"].lower()
                if target not in output_names:
                    output_names.append(target)
                expr = fact.get("expression", fact.get("initial"))
                previous_bounds = env.get(target)
                if _names(expr) - set(env):
                    problem("COLUMN_REFERENCE_UNRESOLVED")
                try:
                    bounds = _bound(expr, env)
                except EvidenceError:
                    bounds = None
                if bounds is None:
                    problem("NUMERIC_EXACTNESS_UNRESOLVED")
                else:
                    if fact["kind"] == "sum":
                        if retained & _names(expr):
                            problem("SUM_STATE_RECURRENCE_UNRESOLVED")
                        prior = env.get(target, (Fraction(0), Fraction(0), 1))
                        bounds = (
                            prior[0] + min(Fraction(0), bounds[0]) * iteration_bound,
                            prior[1] + max(Fraction(0), bounds[1]) * iteration_bound,
                            max(prior[2], bounds[2]),
                        )
                    elif (
                        fact["kind"] == "assignment"
                        and target in retained
                        and retained & _names(expr)
                        and not (inp and inp["mode"] == "SET" and target in input_env)
                    ):
                        # Recurrent multiplication/division and mutually stateful
                        # recurrences require a proof not available in this pilot.
                        if (
                            expr["kind"] == "binary"
                            and expr["operator"] in {"+", "-"}
                            and expr["left"].get("kind") == "name"
                            and expr["left"].get("name") == target
                            and not retained & _names(expr["right"])
                        ):
                            delta = _bound(expr["right"], env)
                            if delta is not None:
                                if expr["operator"] == "-":
                                    delta = (-delta[1], -delta[0], delta[2])
                                prior = env.get(target)
                                bounds = (
                                    (
                                        prior[0] + min(Fraction(0), delta[0]) * iteration_bound,
                                        prior[1] + max(Fraction(0), delta[1]) * iteration_bound,
                                        max(prior[2], delta[2]),
                                    )
                                    if prior
                                    else None
                                )
                            else:
                                bounds = None
                        else:
                            bounds = None
                    if bounds is None or max(abs(bounds[0]), abs(bounds[1])) * bounds[2] > 2**53:
                        problem("NUMERIC_EXACTNESS_UNRESOLVED")
                        bounds = None
                if bounds is not None and fact.get("guard") and previous_bounds is not None:
                    bounds = (
                        min(bounds[0], previous_bounds[0]),
                        max(bounds[1], previous_bounds[1]),
                        max(bounds[2], previous_bounds[2]),
                    )
                if bounds is not None and fact["kind"] != "retain":
                    env[target] = bounds
                elif bounds is None:
                    env.pop(target, None)
            if fact["kind"] == "keep":
                keep_lists.append(set(fact["names"]))
            if fact["kind"] == "drop":
                drop_names.update(fact["names"])
            if fact["kind"] == "sql":
                for selection in fact["select"]:
                    if _names(selection["expression"]) - set(env):
                        problem("COLUMN_REFERENCE_UNRESOLVED")
                    try:
                        bounds = _bound(selection["expression"], env)
                    except EvidenceError:
                        bounds = None
                    if bounds is None:
                        problem("NUMERIC_EXACTNESS_UNRESOLVED")
                    else:
                        env[selection["output"].lower()] = bounds
                if set(fact["order_by"]) - set(output_names):
                    problem("SQL_ORDER_COLUMN_UNRESOLVED")
                for expr in [fact["where"], fact["join"]]:
                    if _names(expr) - set(env):
                        problem("COLUMN_REFERENCE_UNRESOLVED")
                if fact["join"] and profile["numeric_missing_join_policy"] == "UNRESOLVED":
                    for reference in _names(fact["join"]):
                        alias, name = reference.split(".")
                        for source in fact["inputs"]:
                            ds = source["dataset"]
                            if source["alias"] == alias and (
                                ds not in declared_rows
                                or name in schemas[ds]
                                and any(
                                    row[schemas[ds].index(name)] is None
                                    for row in declared_rows[ds]
                                )
                            ):
                                problem("MISSING_JOIN_KEY_POLICY_UNRESOLVED")
            condition = fact.get("guard", fact.get("condition"))
            if condition:
                if condition["kind"] == "by_flag":
                    if not by or condition["key"] not in by["keys"]:
                        problem("BY_FLAG_UNRESOLVED")
                elif _names(condition) - set(env):
                    problem("COLUMN_REFERENCE_UNRESOLVED")
        pdv_names = list(output_names)
        for keep in keep_lists:
            if keep - set(pdv_names):
                problem("KEEP_COLUMN_UNRESOLVED")
            output_names = [name for name in output_names if name in keep]
        if drop_names - set(pdv_names):
            problem("DROP_COLUMN_UNRESOLVED")
        output_names = [name for name in output_names if name not in drop_names]
        for write in writes:
            if write not in datasets:
                dataset(write, owner, "OUTPUT", [source_cit])
                schemas[write] = output_names
                ranges[write] = {name: env[name] for name in output_names if name in env}
                row_bounds[write] = (
                    iteration_bound
                    if not sql or len(reads) == 1
                    else row_bounds.get(reads[0], 0) * max(1, row_bounds.get(reads[1], 0))
                )
                for name in output_names:
                    column(write, name, [source_cit])
        # Unresolved producer evidence cannot become a downstream numeric proof.
        if parsed.get("issues") or op_issues:
            for write in writes:
                tainted_outputs.add(write)
                ranges[write] = {}
        order = {
            "kind": "UNSPECIFIED",
            "keys": [],
            "requires_sorted_inputs": False,
            "precondition": "NOT_REQUIRED",
            "tie_order": "UNSPECIFIED",
        }
        cardinality = "NOT_APPLICABLE"
        if parsed["kind"] == "DATA_STEP":
            cardinality = (
                "INPUT_ROWS_OR_SUBSET" if len(reads) == 1 else "CONCATENATED_ROWS_OR_SUBSET"
            )
            order["kind"] = "INPUT_ORDER" if len(reads) == 1 else "CONCATENATION_ORDER"
            if by:
                keys = by["keys"]
                order.update(keys=keys, requires_sorted_inputs=True)
                proofs = [
                    orders[read][1] if orders[read][0][: len(keys)] == keys else "UNRESOLVED"
                    for read in reads
                ]
                order["precondition"] = (
                    "UNRESOLVED"
                    if not proofs or "UNRESOLVED" in proofs
                    else "SOURCE_SORT"
                    if "SOURCE_SORT" in proofs
                    else "DECLARED_SYNTHETIC_INPUT"
                )
                if order["precondition"] == "UNRESOLVED":
                    problem("BY_SORT_PRECONDITION_UNRESOLVED")
                if any(key not in schemas[read] for read in reads for key in keys):
                    problem("BY_COLUMN_UNRESOLVED")
            if inp and inp["mode"] == "MERGE":
                cardinality = "MATCH_MERGE_MAX_PER_BY_GROUP_OR_SUBSET"
                if len(reads) != 2 or not by or len(by["keys"]) != 1:
                    problem("MERGE_SHAPE_UNSUPPORTED")
                elif (set(schemas[reads[0]]) & set(schemas[reads[1]])) - set(by["keys"]):
                    problem("MERGE_SHARED_NONKEY_UNSUPPORTED")
        if sort:
            cardinality = "SORT_PRESERVES_ROWS"
            order.update(kind="ASCENDING_KEYS", keys=sort["keys"])
            if set(sort["keys"]) - set(output_names):
                problem("SORT_COLUMN_UNRESOLVED")
        if sql:
            cardinality = "SQL_JOIN_MULTIPLICITY_OR_SUBSET"
            if sql["order_by"]:
                order.update(kind="ASCENDING_KEYS", keys=sql["order_by"])
        for write in writes:
            if parsed.get("issues") or op_issues:
                tainted_outputs.add(write)
                ranges[write] = {}
            if sort or sql and sql["order_by"]:
                orders[write] = (order["keys"], "SOURCE_SORT")
            elif by and order["precondition"] != "UNRESOLVED":
                orders[write] = (by["keys"], order["precondition"])
            elif len(reads) == 1 and not sql:
                orders[write] = orders[reads[0]]
            else:
                orders[write] = ([], "UNRESOLVED")
            changed_keys = {f["target"] for f in facts if f["kind"] in {"assignment", "sum"}}
            if changed_keys & set(orders[write][0]):
                orders[write] = ([], "UNRESOLVED")
            if write in tainted_outputs:
                orders[write] = ([], "UNRESOLVED")
        state_effects, lineage, flags, definitions, control_lineage = [], [], set(), {}, []
        for index, fact in enumerate(facts):
            kind = fact["kind"]
            input_phase = (
                "PRIOR_ITERATION_OR_INITIAL_MISSING"
                if index in early_input_reads
                else "CURRENT_ITERATION"
                if kind not in {"macro_binding", "macro_use", "include", "retain"}
                else "STATIC"
            )

            def reference_ids(references):
                input_ids, prior_facts = [], []
                for reference in references:
                    if sql and "." in reference:
                        alias, col = reference.split(".")
                        ds_names = [
                            item["dataset"]
                            for item in sql["inputs"]
                            if item["alias"].lower() == alias
                        ]
                    else:
                        col = reference
                        if reference in definitions:
                            prior_facts.append(definitions[reference])
                            ds_names = []
                        else:
                            ds_names = reads
                    input_ids.extend(
                        columns[(name, col)]["column_id"]
                        for name in ds_names
                        if (name, col) in columns
                    )
                return sorted(set(input_ids)), sorted(set(prior_facts))

            controls = []
            if fact.get("guard"):
                controls.append(("ASSIGNMENT_GUARD", fact["guard"]))
            if kind == "subset_if":
                controls.append(("ROW_SELECTION", fact["condition"]))
            if kind == "sql":
                controls += [("SQL_ON", fact["join"]), ("SQL_WHERE", fact["where"])]
            if kind == "by":
                input_ids, prior_facts = reference_ids(set(fact["keys"]))
                control_lineage.append(
                    {
                        "fact_index": index,
                        "input_column_ids": input_ids,
                        "input_fact_indices": prior_facts,
                        "role": "BY_GROUP",
                        "input_phase": "STATIC",
                    }
                )
            for role, condition in controls:
                if condition is None:
                    continue
                references = _names(condition)
                if condition.get("kind") == "by_flag" and by and condition["key"] in by["keys"]:
                    references.update(by["keys"][: by["keys"].index(condition["key"]) + 1])
                input_ids, prior_facts = reference_ids(references)
                control_lineage.append(
                    {
                        "fact_index": index,
                        "input_column_ids": input_ids,
                        "input_fact_indices": prior_facts,
                        "role": role,
                        "input_phase": input_phase,
                    }
                )
            if index in early_input_reads:
                flags.add("OTHER")
                state_effects.append(
                    {
                        "fact_index": index,
                        "kind": "INPUT_PDV",
                        "target": fact.get("target"),
                        "initialization": "MISSING_PDV",
                        "persistence": "ACROSS_ROWS",
                        "reset": "INPUT_STATEMENT",
                        "queue_size": None,
                        "call_policy": "NOT_APPLICABLE",
                        "guard": bind(fact.get("guard")),
                    }
                )
            if kind in {"retain", "sum", "by"} or kind == "input" and fact["mode"] == "MERGE":
                state_kind = "MERGE" if kind == "input" else kind.upper()
                flags.add(state_kind)
                state_effects.append(
                    {
                        "fact_index": index,
                        "kind": state_kind,
                        "target": fact.get("target"),
                        "initialization": {
                            "RETAIN": "LITERAL",
                            "SUM": "ZERO_UNLESS_RETAIN_INITIALIZED",
                            "BY": "GROUP_FLAGS",
                            "MERGE": "INPUT_BY_GROUP",
                        }[state_kind],
                        "persistence": "WITHIN_BY_GROUP"
                        if state_kind == "MERGE"
                        else "BY_KEY_PREFIX"
                        if state_kind == "BY"
                        else "ACROSS_ROWS",
                        "reset": "BY_GROUP"
                        if state_kind == "MERGE"
                        else "KEY_PREFIX_CHANGE"
                        if state_kind == "BY"
                        else "ONLY_EXPLICIT_ASSIGNMENT",
                        "queue_size": None,
                        "call_policy": "NOT_APPLICABLE",
                        "guard": bind(fact.get("guard")),
                    }
                )
            for expr in _expressions(fact):
                if expr["kind"] == "lag":
                    flags.add("LAG")
                    state_effects.append(
                        {
                            "fact_index": index,
                            "kind": "LAG",
                            "target": fact.get("target"),
                            "initialization": "MISSING_QUEUE",
                            "persistence": "ACROSS_ROWS",
                            "reset": "NONE_IMPLICIT",
                            "queue_size": expr["queue_size"],
                            "call_policy": "EXECUTED_CALLS_ONLY",
                            "guard": bind(fact.get("guard")),
                        }
                    )
            if kind in {"macro_binding", "macro_use"}:
                flags.add("GLOBAL_MACRO")
            if kind in {"input", "sort"}:
                for write in writes:
                    for name in schemas[write]:
                        incoming = [
                            columns[(read, name)]["column_id"]
                            for read in reads
                            if (read, name) in columns
                        ]
                        if incoming:
                            lineage.append(
                                {
                                    "fact_index": index,
                                    "output_column_id": columns[(write, name)]["column_id"],
                                    "input_column_ids": sorted(set(incoming)),
                                    "input_fact_indices": [],
                                    "input_phase": "CURRENT_ITERATION",
                                }
                            )
            selections = (
                fact["select"]
                if kind == "sql"
                else [
                    {
                        "output": fact["target"],
                        "expression": fact.get("expression", fact.get("initial")),
                    }
                ]
                if kind in {"assignment", "sum", "retain"}
                else []
            )
            for select in selections:
                references = _names(select["expression"]) | _names(fact.get("guard"))
                if kind == "sum" or fact.get("guard"):
                    # The skipped branch / implicit accumulation consumes the
                    # previous value as well as the newly computed expression.
                    references.add(select["output"])
                # BY flags are control dependence on the input grouping keys.
                guard = fact.get("guard")
                if guard and guard.get("kind") == "by_flag":
                    references.update(
                        by["keys"][: by["keys"].index(guard["key"]) + 1]
                        if by and guard["key"] in by["keys"]
                        else []
                    )
                if kind == "sql":
                    references |= _names(fact["where"]) | _names(fact["join"])
                input_ids, prior_facts = reference_ids(references)
                for write in writes:
                    if (write, select["output"]) in columns:
                        lineage.append(
                            {
                                "fact_index": index,
                                "output_column_id": columns[(write, select["output"])]["column_id"],
                                "input_column_ids": sorted(set(input_ids)),
                                "input_fact_indices": sorted(set(prior_facts)),
                                "input_phase": input_phase,
                            }
                        )
                definitions[select["output"]] = index
        bound_facts = bind(facts)
        citations = [source_cit]

        def collect_citations(value):
            if isinstance(value, dict):
                if "citation" in value and value["citation"] not in citations:
                    citations.append(value["citation"])
                for child in value.values():
                    collect_citations(child)
            elif isinstance(value, list):
                for child in value:
                    collect_citations(child)

        collect_citations(bound_facts)
        rules = []
        if by:
            rules.append("BY_PREFIX_KEY_FLAGS")
        if inp and inp["mode"] == "MERGE":
            rules += ["MERGE_ADVANCE_WITH_RETAINED_EXHAUSTED_INPUT", "MERGE_NOT_CARTESIAN"]
        if sql:
            rules.append("SQL_ON_BEFORE_WHERE")
            if profile["numeric_missing_join_policy"] == "SAS_ORDINARY_MISSING_EQUALS_MISSING":
                rules.append("SQL_MISSING_EQUALS_MISSING")
        if "SUM" in flags:
            rules.append("SUM_SKIP_MISSING")
        if "LAG" in flags:
            rules.append("LAG_QUEUE_PER_CALLSITE")
        op = {
            "module_id": owner,
            "kind": parsed["kind"],
            "citations": citations,
            "reads": sorted(
                {datasets[name]["dataset_id"] for name in reads}
                | {columns[(name, col)]["column_id"] for name in reads for col in schemas[name]}
            ),
            "writes": sorted(
                {datasets[name]["dataset_id"] for name in writes}
                | {columns[(name, col)]["column_id"] for name in writes for col in schemas[name]}
            ),
            "stateful_constructs": sorted(flags),
            "classification": "INFERENCE",
            "semantic_verification": "UNVERIFIABLE",
            "span": bound_span(span),
            "sequence": sequence,
            "facts": bound_facts,
            "lineage": lineage,
            "state_effects": state_effects,
            "control_lineage": control_lineage,
            "order_contract": order,
            "numeric_policy": {
                "storage": "SAS_NUMERIC_8",
                "missing_order": "ORDINARY_MISSING_BELOW_FINITE",
                "missing_arithmetic": "PROPAGATE_EXCEPT_SUM_STATEMENT",
                "expression_order": "SOURCE_TREE_NO_REASSOCIATION",
                "runtime_equivalence": "NOT_ASSERTED",
                "exactness": "UNRESOLVED"
                if parsed.get("issues") or op_issues
                else "BOUNDED_SYNTHETIC_PRECONDITIONS",
                "missing_join": profile["numeric_missing_join_policy"],
            },
            "cardinality": cardinality,
            "interpretation_rules": rules,
        }
        op["operation_id"] = record_id("op", fingerprint, op, "operation_id")
        graph["operations"].append(op)
        anchors[(span["file_key"], span["start"])] = op
        for code in op_issues:
            issue(code, span=span, operation_ids=[op["operation_id"]])
        for pi in parsed.get("issues", []):
            issue(pi["code"], span=pi["span"], operation_ids=[op["operation_id"]])
        for name in writes:
            producers.setdefault(name, []).append(op)

    def edge(first, second, kind, node_ids):
        value = {
            "from_operation_id": first["operation_id"],
            "to_operation_id": second["operation_id"],
            "type": kind,
            "node_ids": sorted(node_ids),
            "evidence_operation_ids": sorted({first["operation_id"], second["operation_id"]}),
            "classification": "INFERENCE",
            "semantic_verification": "UNVERIFIABLE",
        }
        value["edge_id"] = record_id("edge", fingerprint, value, "edge_id")
        if value not in graph["edges"]:
            graph["edges"].append(value)

    for op in graph["operations"]:
        for prior in graph["operations"][: op["sequence"]]:
            shared = set(prior["writes"]) & set(op["reads"])
            if shared:
                edge(prior, op, "DATA", shared)
                if (
                    op["order_contract"]["requires_sorted_inputs"]
                    and prior["order_contract"]["kind"] == "ASCENDING_KEYS"
                ):
                    edge(prior, op, "ORDER", shared)
        if op["state_effects"]:
            edge(op, op, "STATE", op["writes"])
        for fact in op["facts"]:
            if fact["kind"] == "macro_use":
                definition = fact["definition_span"]
                for prior in graph["operations"]:
                    if any(
                        f["kind"] == "macro_binding" and f["span"] == definition
                        for f in prior["facts"]
                    ):
                        edge(prior, op, "STATE", [])
    for statement in statements:
        span = statement["span"]
        owners = [
            graph["operations"][index]
            for index, parsed in enumerate(parsed_ops)
            if any(s["span"] == span for s in parsed["statements"])
        ]
        if len(owners) > 1:
            owners = [op for op in owners if op["kind"] == "INCLUDE"]
        graph["statement_coverage"].append(
            {
                "span": bound_span(span),
                "classification": statement["classification"],
                "operation_id": owners[0]["operation_id"] if len(owners) == 1 else None,
            }
        )
    observations, observation_issues = extract_observations(scope, inventory, profile, anchors)
    for obs in observations:
        obs["observation_id"] = record_id("log", fingerprint, obs, "observation_id")
        graph["log_observations"].append(obs)
        op = next(
            o for o in graph["operations"] if o["operation_id"] == obs["source_operation_ids"][0]
        )
        if obs["metric"] in {"READ_ROWS", "OUTPUT_ROWS", "OUTPUT_COLUMNS"}:
            field = "reads" if obs["metric"] == "READ_ROWS" else "writes"
            ds = datasets.get(obs["dataset"])
            if ds is None or ds["dataset_id"] not in op[field]:
                issue(
                    "LOG_DATASET_SOURCE_CONTRADICTION",
                    contradiction=True,
                    cit=obs["log_citation"],
                    operation_ids=[op["operation_id"]],
                )
            elif obs["metric"] == "OUTPUT_COLUMNS" and int(obs["value_lexeme"]) != len(
                schemas[obs["dataset"]]
            ):
                issue(
                    "LOG_COLUMN_COUNT_CONTRADICTION",
                    contradiction=True,
                    cit=obs["log_citation"],
                    operation_ids=[op["operation_id"]],
                )
    for found in observation_issues:
        cit = (
            citation(scope, inventory, found["file_key"], found["line_start"], found["line_end"])
            if found["line_start"]
            else None
        )
        issue(
            found["code"], file_key=found["file_key"], contradiction=found["contradiction"], cit=cit
        )
    graph["coverage"] = coverage(graph, inventory)
    _check("Graph", graph)
    if inventory != build_inventory(scope, inventory["attempt_id"]):
        raise EvidenceError("STALE_SOURCE")
    if predecessor is not None:
        revision_map(predecessor, graph)
    return graph


def validate_v2(
    scope: dict, inventory: dict, graph: dict, profile: dict, *, profile_file_key: str
) -> dict:
    """Check source-grounded consistency, leaving independent acceptance blocked.

    Reads evidence through ``reconstruct`` without writing artifacts or mutating
    inputs. Matching reconstruction establishes consistency only, not an
    independent oracle, SAS execution, or permission to publish.

    Args:
        scope: Authorization scope for the reconstruction reads.
        inventory: V1 inventory binding the graph to current evidence.
        graph: V2 graph to compare exactly with deterministic reconstruction.
        profile: V2 synthetic assumptions used for reconstruction.
        profile_file_key: Inventoried CONFIG file containing the profile.

    Returns:
        A v2 report whose stage gate is FAIL for contradictions and otherwise
        BLOCKED; semantic acceptance remains BLOCKED in either case.

    Raises:
        EvidenceError: If contract validation or reconstruction fails, or the
            supplied graph differs from the reconstructed graph.
    """
    _check("Graph", graph)
    expected = reconstruct(scope, inventory, profile, profile_file_key=profile_file_key)
    if graph != expected:
        raise EvidenceError("RECONSTRUCTION_SOURCE_MISMATCH")
    findings = [{"code": "P2B_INDEPENDENT_ACCEPTANCE_NOT_RUN", "gate": "BLOCKED"}]
    if graph["unknowns"]:
        findings.append({"code": "UNRESOLVED_UNKNOWNS", "gate": "BLOCKED"})
    if graph["contradictions"]:
        findings.append({"code": "DECLARED_CONTRADICTIONS", "gate": "FAIL"})
    result = {
        "schema_version": "2.0",
        "stage_gate": "FAIL" if graph["contradictions"] else "BLOCKED",
        "structural_verification": "PASSED",
        "source_consistency": "PASSED",
        "reconstruction_status": "PARTIAL"
        if graph["unknowns"] or graph["contradictions"]
        else "COMPLETE",
        "semantic_verification": "UNVERIFIABLE",
        "semantic_acceptance": "BLOCKED",
        "benchmark_execution": "NOT_RUN",
        "artifact_authority": "DRAFT",
        "findings": findings,
        "coverage": graph["coverage"],
    }
    _check("Report", result)
    return result


def module_view(graph: dict, module_id: str) -> dict:
    """Derive a module's ID index, not a second editable factual graph.

    Performs no evidence I/O and does not mutate the canonical graph. Referenced
    nodes and incident edges may cross module ownership boundaries.

    Args:
        graph: Schema-valid v2 canonical graph supplying record authority.
        module_id: Declared module whose records and references are selected.

    Returns:
        A v2 draft view bound to the graph digest, with sorted record IDs.

    Raises:
        EvidenceError: If a contract fails or the module is not declared.
    """
    _check("Graph", graph)
    if module_id not in graph["module_ids"]:
        raise EvidenceError("UNKNOWN_MODULE")
    ops = {o["operation_id"] for o in graph["operations"] if o["module_id"] == module_id}
    nodes = {
        n for o in graph["operations"] if o["operation_id"] in ops for n in o["reads"] + o["writes"]
    }
    nodes.update(n["dataset_id"] for n in graph["columns"] if n["column_id"] in nodes)
    value = {
        "schema_version": "2.0",
        **{k: graph[k] for k in ("workspace_id", "run_id", "attempt_id")},
        "module_id": module_id,
        "source_record_sha256": digest(graph),
        "operation_ids": sorted(ops),
        "dataset_ids": sorted(
            n["dataset_id"]
            for n in graph["datasets"]
            if n["module_id"] == module_id or n["dataset_id"] in nodes
        ),
        "column_ids": sorted(
            n["column_id"]
            for n in graph["columns"]
            if n["module_id"] == module_id or n["column_id"] in nodes
        ),
        "edge_ids": sorted(
            e["edge_id"]
            for e in graph["edges"]
            if e["from_operation_id"] in ops or e["to_operation_id"] in ops
        ),
        "log_observation_ids": sorted(
            o["observation_id"] for o in graph["log_observations"] if o["module_id"] == module_id
        ),
        "artifact_authority": "DRAFT",
        "semantic_verification": "UNVERIFIABLE",
    }
    _check("ModuleView", value)
    return value


def revision_map(previous: dict, current: dict) -> dict:
    """Map revision identities and overlapping anchors without asserting equivalence.

    Performs no evidence I/O and does not mutate either graph. Contract and
    operation-ID checks do not independently verify either record's semantics.

    Args:
        previous: Prior graph accepted by the versioned v1/v2 Graph contract.
        current: V2 graph with the same workspace and run ownership.

    Returns:
        A v2 map of retained, removed, and added IDs plus same-module source
        anchor overlaps; semantic equivalence remains NOT_ASSERTED.

    Raises:
        EvidenceError: If contracts or operation identities fail, or current
            schema version, workspace, or run ownership does not match.
    """
    for record in (previous, current):
        validate_versioned_contract("Graph", record)
        for op in record["operations"]:
            if op["operation_id"] != record_id(
                "op", record["source_fingerprint"], op, "operation_id"
            ):
                raise EvidenceError("UNSTABLE_OPERATIONS_ID")
    if current["schema_version"] != "2.0" or any(
        previous[key] != current[key] for key in ("workspace_id", "run_id")
    ):
        raise EvidenceError("REVISION_OWNER_MISMATCH")
    old = {op["operation_id"] for op in previous["operations"]}
    new = {op["operation_id"] for op in current["operations"]}
    mappings = []
    for before in previous["operations"]:
        # Same-module line overlap links anchors only, not behavior or byte identity.
        matches = [
            after["operation_id"]
            for after in current["operations"]
            if before["module_id"] == after["module_id"]
            and any(
                a["file_key"] == b["file_key"]
                and max(a["line_start"], b["line_start"]) <= min(a["line_end"], b["line_end"])
                for a in before["citations"]
                for b in after["citations"]
            )
        ]
        mappings.append(
            {
                "previous_operation_id": before["operation_id"],
                "current_operation_ids": sorted(matches),
                "basis": "OVERLAPPING_SOURCE_ANCHOR_ONLY",
            }
        )
    value = {
        "schema_version": "2.0",
        "previous_record_sha256": digest(previous),
        "current_record_sha256": digest(current),
        "retained_operation_ids": sorted(old & new),
        "removed_operation_ids": sorted(old - new),
        "added_operation_ids": sorted(new - old),
        "semantic_equivalence": "NOT_ASSERTED",
        "previous_schema_version": previous["schema_version"],
        "current_schema_version": "2.0",
        "operation_mappings": mappings,
    }
    _check("RevisionMap", value)
    return value
