"""Run the bounded SQL-2 population and abort-gate candidate on public cases."""

import argparse
from collections import Counter
from pathlib import Path
import sys

from sas_re.platform_io import require_evidence_io
from sas_re.safeio import EvidenceError, _parse_json, ensure_disjoint, secure_read

sys.path.insert(0, str(Path(__file__).resolve().parent))
from migration_candidate import AUTHORITY
from migration_review import anchor
from mvp1_demo import scratch_destination, write_bundle
from preparation_candidate import NumericMissing
from review_intake import identity, json_bytes
from review_source import MAX_SPAN_BYTES, dependency_review


EXAMPLE = Path(__file__).resolve().parents[1] / "tests/fixtures/candidate-execution/population-gates"
LIMIT = 262144


def bind_plan(raw, digest, evidence_bytes):
    if identity(raw)["sha256"] != digest:
        raise ValueError("MIGRATION_SOURCE_SHA256_MISMATCH")
    supplied = _parse_json(evidence_bytes)
    if supplied.get("review_format") != "source-only-dependency/4":
        raise ValueError("MIGRATION_SQL2_EVIDENCE_REQUIRED")
    selections = supplied["selections"]
    if len(selections) != 2:
        raise ValueError("MIGRATION_SQL2_EVIDENCE_REQUIRED")
    ranges = [(item["selected_span"]["line_start"], item["selected_span"]["line_end"])
              for item in selections]
    if not 1 <= ranges[0][0] <= ranges[0][1] < ranges[1][0] <= ranges[1][1]:
        raise ValueError("MIGRATION_INVALID_REVIEW_RANGES")
    recovery = "status_rule_recovery" in (selections[0].get("declared_operation") or {})
    # Replay accepted source recovery. A changed declaration with a matching
    # self-reported hash still cannot substitute for an original finding.
    for recover_missing in ((False, True) if recovery else (False,)):
        evidence, _ = dependency_review(raw, ranges, digest, recover_rules=recovery,
                                        recover_missing=recover_missing, recover_sql=True)
        if json_bytes(evidence) == evidence_bytes:
            break
    else:
        raise ValueError("MIGRATION_EVIDENCE_MISMATCH")

    interval = evidence["interval_effects"]
    findings = interval["findings"]
    sql = [i for i, item in enumerate(findings) if "sql_declaration" in item]
    gates = [i for i, item in enumerate(findings) if "gate_declaration" in item]
    if (len(sql) != 3 or len(gates) != 6 or sql + gates != sorted(sql + gates)
            or interval["status"] != "INSPECTED" or interval["shared_writer_identified"] is not False
            or any("POTENTIAL_ABORT" in item.get("control_gates", []) and i not in gates
                   for i, item in enumerate(findings))):
        raise ValueError("MIGRATION_SQL_GATE_CONTRACT_UNSUPPORTED")

    group, scalar, count = (findings[i] for i in sql)
    group_decl, scalar_decl, count_decl = (item["sql_declaration"] for item in (group, scalar, count))
    shared = interval["shared_dataset"]
    if ([item["kind"] for item in (group_decl, scalar_decl, count_decl)]
            != ["DUPLICATE_GROUP_SIZES", "SCALAR_INTO", "DUPLICATE_GROUP_COUNT"]
            or group["reads"] != [shared] or scalar["reads"] != [shared]
            or len(group["writes"]) != 1 or count["reads"] != group["writes"]
            or count_decl["group_query_start"] != group["span"]["start"]):
        raise ValueError("MIGRATION_SQL_GATE_CONTRACT_UNSUPPORTED")

    bindings = scalar_decl["bindings"] + count_decl["bindings"]
    if [item["expression"] for item in bindings] != [
        "COUNT(*)", "COUNT(DISTINCT id)", "SUM(CASE WHEN MISSING(id) THEN 1 ELSE 0 END)", "COUNT(*)",
    ] or len({item["target"] for item in bindings}) != 4:
        raise ValueError("MIGRATION_SQL_GATE_CONTRACT_UNSUPPORTED")
    total, distinct, missing, repeated = (item["target"] for item in bindings)
    gate_records = [findings[i]["gate_declaration"] for i in gates]
    guard = gate_records[4]
    expected = gate_records[5]["operand"].get("variable")
    if (guard["action"] != "GUARD" or guard["transform"] != "UPCASE"
            or guard["operator"] != "=" or guard["operand"] != {"literal": "Y"}
            or not expected or len({total, distinct, missing, repeated, guard["variable"], expected}) != 6):
        raise ValueError("MIGRATION_SQL_GATE_CONTRACT_UNSUPPORTED")

    def cite(index):
        span = findings[index]["span"]
        return {"span": span, "anchor": anchor(span),
                "evidence_pointer": f"/interval_effects/findings/{index}"}

    scalar_start, count_start = scalar["span"]["start"], count["span"]["start"]
    gate_plan = []
    for index, record, condition in zip(
        (*gates[:4], gates[5]), (*gate_records[:4], gate_records[5]),
        (
            (total, "=", {"literal": "0"}, {total: scalar_start}, None),
            (missing, "NE", {"literal": "0"}, {missing: scalar_start}, None),
            (repeated, "NE", {"literal": "0"}, {repeated: count_start}, None),
            (total, "NE", {"variable": distinct}, {total: scalar_start, distinct: scalar_start}, None),
            (total, "NE", {"variable": expected}, {total: scalar_start}, findings[gates[4]]["span"]["start"]),
        ), strict=True,
    ):
        if (record["action"] != "ABORT_REQUEST"
                or tuple(record.get(key) for key in ("variable", "operator", "operand", "into_sources", "guard_start"))
                != condition):
            raise ValueError("MIGRATION_SQL_GATE_CONTRACT_UNSUPPORTED")
        gate_plan.append({**cite(index), "declaration": record})
    return {
        "source": identity(raw), "evidence": identity(evidence_bytes), "prepared_dataset": shared,
        "duplicate_audit": cite(sql[0]),
        "aggregates": dict(zip(
            ("prepared_rows", "unique_ids", "missing_ids", "duplicate_ids"),
            ({"target": item["target"], **cite(index)} for item, index in
             zip(bindings, (sql[1], sql[1], sql[1], sql[2]), strict=True)), strict=True)),
        "guard": {**cite(gates[4]), "declaration": guard},
        "gates": gate_plan, "expected_count_variable": expected,
        "sas_abort_effect": "UNRESOLVED", "sort_reachability": "UNESTABLISHED",
        "other_interval_effects": "UNRESOLVED",
        "candidate_policy": "STOP_AT_FIRST_TRUE_GATE",
        "candidate_identifier_contract": "EXACT_RANGE_INTEGER_OR_EXPLICIT_NUMERIC_MISSING_TAG",
        "candidate_missing_policy": "EXCLUDED_FROM_DISTINCT_COUNT_GROUPED_BY_TAG_IN_DUPLICATE_AUDIT",
        "reference_obligations": [
            "Bind the submitted source and prepared dataset version to one observed SAS run.",
            "Verify identifier descriptors, missing-tag grouping, distinct counts and empty SUM behavior.",
            "Observe actual INTO values, flag expansion, gate reachability and abort effects.",
        ],
        **AUTHORITY,
    }


def evaluate(plan, ids, flag, expected_count):
    if (not isinstance(ids, list) or len(ids) > 10000 or flag not in ("Y", "y", "N", "n")
            or (expected_count is not None and (type(expected_count) is not int or expected_count < 0))
            or (flag.upper() == "Y" and expected_count is None)):
        raise ValueError("MIGRATION_POPULATION_INPUT_UNSUPPORTED")
    numbers, missing = Counter(), Counter()
    for value in ids:
        if type(value) is int and -(2**53) <= value <= 2**53:
            numbers[value] += 1
        elif isinstance(value, dict) and value.keys() == {"tag"}:
            missing[NumericMissing(value["tag"]).tag] += 1
        else:
            raise ValueError("MIGRATION_IDENTIFIER_UNSUPPORTED")
    duplicates = [{"id": value, "duplicate_count": count}
                  for value, count in sorted(numbers.items()) if count > 1]
    duplicates.extend({"id": {"tag": tag}, "duplicate_count": count}
                      for tag, count in sorted(missing.items()) if count > 1)
    stats = {"prepared_rows": len(ids), "unique_ids": len(numbers), "missing_ids": sum(missing.values()),
             "duplicate_ids": len(duplicates)}
    values = {item["target"]: stats[metric] for metric, item in plan["aggregates"].items()}
    values[plan["expected_count_variable"]] = expected_count
    decisions = []
    first = None
    guard = {"source": plan["guard"], "status": "NOT_EVALUATED", "reason": "EARLIER_BLOCK"}
    for position, gate in enumerate(plan["gates"], 1):
        record = gate["declaration"]
        event = {"position": position, "source": gate, "status": "NOT_EVALUATED", "block_requested": False}
        if first is not None:
            event["reason"] = "EARLIER_BLOCK"
        elif position == 5 and flag.upper() != "Y":
            guard.update(status="EVALUATED", predicate=False, reason="OPTION_DISABLED")
            event["reason"] = "OPTION_DISABLED"
        else:
            if position == 5:
                guard = {"source": plan["guard"], "status": "EVALUATED", "predicate": True}
            left = values[record["variable"]]
            operand = record["operand"]
            right = values[operand["variable"]] if "variable" in operand else 0
            matched = left == right if record["operator"] == "=" else left != right
            event.update(status="EVALUATED", left=left, right=right, predicate=matched, block_requested=matched)
            if matched:
                first = position
        decisions.append(event)
    return {"statistics": stats, "duplicate_groups": duplicates, "gates": decisions, "optional_guard": guard,
            "flag": flag, "expected_count": expected_count, "first_blocking_gate": first,
            "continuation": "BLOCK" if first else "PROCEED", "sas_abort_effect": "UNRESOLVED"}


def mig3_ids(package, digest):
    raw = secure_read(package, "MANIFEST.json", LIMIT)
    if identity(raw)["sha256"] != digest:
        raise ValueError("MIGRATION_PREPARATION_MANIFEST_MISMATCH")
    manifest = _parse_json(raw)
    if (any(manifest.get(key) != value for key, value in AUTHORITY.items())
            or set(manifest.get("candidate", {})) != {"migrate_preparation.py", "preparation_candidate.py"}):
        raise ValueError("MIGRATION_PREPARATION_PACKAGE_UNSUPPORTED")
    rows = secure_read(package, "ROWS.json", LIMIT)
    if identity(rows) != manifest["files"]["ROWS.json"]:
        raise ValueError("MIGRATION_PREPARATION_PAYLOAD_MISMATCH")
    ids = []
    for row in _parse_json(rows):
        if row["mode"] == "full" and row["candidate_row_end_reached"] is True:
            if row["sas_dataset_output"] != "UNOBSERVED" or type(row["candidate_output"]["id"]) is not int:
                raise ValueError("MIGRATION_PREPARATION_ROW_UNSUPPORTED")
            ids.append(row["candidate_output"]["id"])
    return ids, {"manifest_sha256": digest, "rows": identity(rows), "scope": "FULL_MODE_CANDIDATE_ROW_END"}


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--source", type=Path, required=True, help="authorized public synthetic source")
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--mig3-package", type=Path)
    parser.add_argument("--mig3-manifest-sha256")
    parser.add_argument("--destination", required=True, help="fresh /tmp/sas-re-mig4-<label> directory")
    args = parser.parse_args()
    if bool(args.mig3_package) != bool(args.mig3_manifest_sha256):
        parser.error("supply both MIG-3 binding arguments")
    try:
        require_evidence_io()
        scratch, leaf = scratch_destination(args.destination, "mig4")
        source, evidence = args.source.absolute(), args.evidence.absolute()
        roots = [source.parent, evidence.parent]
        if args.mig3_package:
            roots.append(args.mig3_package.absolute())
        ensure_disjoint(scratch / leaf, roots)
        plan = bind_plan(secure_read(source.parent, source.name, MAX_SPAN_BYTES),
                         args.source_sha256, secure_read(evidence.parent, evidence.name, LIMIT))
        plan["source"]["path"] = source.name
        raw_cases = secure_read(EXAMPLE, "CASES.json", LIMIT)
        results, checks = [], []
        for case in _parse_json(raw_cases):
            result = evaluate(plan, case["ids"], case["flag"], case["expected_count"])
            stats = result["statistics"]
            observed = [stats["prepared_rows"], stats["unique_ids"], stats["missing_ids"],
                        result["duplicate_groups"], result["first_blocking_gate"]]
            results.append({"case_id": case["id"], "input_ids": case["ids"], **result})
            checks.append({"case_id": case["id"], "expected": case["expected"], "observed": observed,
                           "comparison": "PASS" if observed == case["expected"] else "FAIL"})
        preparation = None
        if args.mig3_package:
            ids, preparation = mig3_ids(args.mig3_package.absolute(), args.mig3_manifest_sha256)
            results.append({"case_id": "mig3_full_candidate", "input_ids": ids,
                            "engineering_comparison": "NOT_RUN", **evaluate(plan, ids, "N", None)})
        passed = all(check["comparison"] == "PASS" for check in checks)
        files = {"PLAN.json": json_bytes(plan), "POPULATION.json": json_bytes(results),
                 "VALIDATION.json": json_bytes({
                     "basis": "PUBLIC_PYTHON_ENGINEERING_EXPECTATIONS",
                     "comparison": "PASS" if passed else "FAIL", "cases": checks, **AUTHORITY,
                 })}
        scripts = Path(__file__).resolve().parent
        files["MANIFEST.json"] = json_bytes({
            "source": plan["source"], "evidence": plan["evidence"], "public_cases": identity(raw_cases),
            "mig3_input": preparation,
            "candidate": {name: identity(secure_read(scripts, name, LIMIT))
                          for name in (Path(__file__).name, "preparation_candidate.py")},
            "files": {name: identity(payload) for name, payload in files.items()}, **AUTHORITY,
        })
        write_bundle(scratch, leaf, files, names=tuple(files))
    except FileExistsError:
        parser.exit(2, "BLOCKED: destination exists\n")
    except EvidenceError as error:
        parser.exit(2, f"{error.gate}: {error.code}\n")
    except (KeyError, TypeError, AttributeError, UnicodeError, IndexError):
        parser.exit(2, "REFUSED: MIGRATION_INPUT_INVALID\n")
    except ValueError as error:
        parser.exit(2, f"REFUSED: {error}\n")
    except OSError:
        parser.exit(2, "REFUSED: FILE_IO_REFUSED\n")
    print(json_bytes({"open": str(scratch / leaf / "PLAN.json"),
                      "manifest_sha256": identity(files["MANIFEST.json"])["sha256"],
                      "comparison": "PASS" if passed else "FAIL"}).decode(), end="")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
