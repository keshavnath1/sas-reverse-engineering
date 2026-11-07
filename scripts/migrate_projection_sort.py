"""Run a bounded Python projection and sort from a verified public INT-3 package."""

import argparse
from pathlib import Path
import sys

from sas_re.platform_io import require_evidence_io
from sas_re.safeio import EvidenceError, _parse_json, ensure_disjoint, secure_read

sys.path.insert(0, str(Path(__file__).resolve().parent))
from migration_candidate import AUTHORITY, prepare_and_sort
from mvp1_demo import scratch_destination, write_bundle
from review_copilot_notes import LIMIT
from review_intake import anchor, build_review, identity, json_bytes


def load_plan(intake, package):
    # Replay the existing analyzer against the authorized source bytes. A
    # self-consistent edited manifest and edited evidence cannot pass this check.
    rebuilt = build_review(intake)
    manifest = _parse_json(rebuilt["MANIFEST.json"])
    if manifest["package_revision"] != "public-intake-review/3":
        raise ValueError("MIGRATION_TWO_SOURCE_PACKAGE_REQUIRED")
    for name, raw in rebuilt.items():
        if secure_read(package, name, LIMIT) != raw:
            raise ValueError("MIGRATION_EVIDENCE_MISMATCH")

    operations, sources = {}, {}
    for source in manifest["sources"]:
        evidence = _parse_json(rebuilt[source["evidence"]])
        operation = evidence.get("declared_operation")
        path = source["path"]
        original = manifest["inputs"][path]
        if (evidence.get("syntax_recognition") != "SUPPORTED" or not operation
                or operation.get("unsupported_statements")
                or source["coverage"] != [{"start": 0, "end": original["bytes"],
                                           "kind": "SELECTED_SOURCE_REVIEW"}]):
            raise ValueError("MIGRATION_UNSUPPORTED_OR_UNINSPECTED_SOURCE")
        kind = operation["kind"]
        if kind in operations:
            raise ValueError("MIGRATION_DATA_AND_SORT_REQUIRED")
        operations[kind] = operation
        sources[kind] = {"path": path, **original, "evidence": source["evidence"]}

    if operations.keys() != {"DATA_STEP", "PROC_SORT"}:
        raise ValueError("MIGRATION_DATA_AND_SORT_REQUIRED")
    data, sort = operations["DATA_STEP"], operations["PROC_SORT"]
    links = manifest["cross_file_dependencies"]
    if (len(links) != 1 or links[0]["dataset"] != data["output"]
            or data["output"] != sort["input"]
            or len({data["input"], data["output"], sort["output"]}) != 3
            or links[0]["writer"] != {"path": sources["DATA_STEP"]["path"],
                                      "anchor": anchor(data["declaration_spans"]["output"])}
            or links[0]["reader"] != {"path": sources["PROC_SORT"]["path"],
                                      "anchor": anchor(sort["span"])}):
        raise ValueError("MIGRATION_HANDOFF_UNRESOLVED_OR_AMBIGUOUS")

    keys = sort["ordering_keys"]
    columns = data["selected_columns"]
    if (sort["declared_direction"] != "ASCENDING" or len(keys) != 1
            or len(columns) != 2 or len(set(columns)) != 2 or keys[0] not in columns):
        raise ValueError("MIGRATION_PROJECTION_OR_ORDER_UNSUPPORTED")
    key, = keys
    value, = (column for column in columns if column != key)
    return {
        "input_manifest_sha256": identity(rebuilt["MANIFEST.json"])["sha256"],
        "source_evidence": sources,
        "projection": {
            "input": data["input"], "output": data["output"], "columns": columns,
            "trace": "/declared_operation/declaration_spans",
        },
        "sort": {
            "input": sort["input"], "output": sort["output"], "key": key, "direction": "ASCENDING",
            "trace": "/declared_operation/ordering_span",
        },
        "handoff": links[0],
        "candidate_assumptions": {
            "execution_order": "PROJECT_THEN_SORT",
            "tie_policy": "PRESERVE_INPUT_ORDER",
            "integer_key": key,
            "integer_or_finite_float_value": value,
        },
    }


def run_rows(plan, raw):
    case = _parse_json(raw)
    if (not isinstance(case, dict)
            or case.keys() - {"scope", "text_column", "input", "expected"}
            or case.get("scope") != "public-synthetic" or not isinstance(case.get("input"), list)):
        raise ValueError("MIGRATION_PUBLIC_ROWS_REQUIRED")
    key = plan["candidate_assumptions"]["integer_key"]
    value = plan["candidate_assumptions"]["integer_or_finite_float_value"]
    text = case.get("text_column")
    if not isinstance(text, str) or not text.isascii() or not text.isidentifier() or text.lower() != text:
        raise ValueError("MIGRATION_TEXT_COLUMN_INVALID")
    if text in {key, value}:
        raise ValueError("MIGRATION_TEXT_COLUMN_INVALID")

    expected = case.get("expected")
    if ("expected" in case and (not isinstance(expected, list)
            or any(not isinstance(row, dict) or row.keys() != {key, value}
                   or type(row[key]) is not int or type(row[value]) not in (int, float)
                   for row in expected))):
        raise ValueError("MIGRATION_EXPECTED_ROWS_INVALID")

    adapted = []
    for row in case["input"]:
        if not isinstance(row, dict) or row.keys() != {key, value, text}:
            raise ValueError("MIGRATION_ROW_FIELDS_UNSUPPORTED")
        adapted.append({"id": row[key], "amount": row[value], "memo": row[text]})
    observed = [{key: row["id"], value: row["amount"]} for row in prepare_and_sort(adapted)]
    if expected is None:
        return observed, {"execution": "SUCCEEDED", "comparison": "NOT_RUN"}
    return observed, {
        "execution": "SUCCEEDED",
        "comparison": "PASS" if json_bytes(observed) == json_bytes(expected) else "FAIL",
        "basis": "CALLER_SUPPLIED_PUBLIC_SYNTHETIC_EXPECTATIONS",
        "expected": expected,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--intake", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--rows", type=Path, required=True)
    parser.add_argument("--rows-sha256", required=True)
    parser.add_argument("--destination", required=True, help="fresh /tmp/sas-re-mig2-<label> directory")
    args = parser.parse_args()
    try:
        require_evidence_io()
        scratch, leaf = scratch_destination(args.destination, "mig2")
        intake, package, rows = (path.absolute() for path in (args.intake, args.package, args.rows))
        ensure_disjoint(scratch / leaf, [intake, package])
        raw = secure_read(rows.parent, rows.name, LIMIT)
        if identity(raw)["sha256"] != args.rows_sha256:
            raise ValueError("MIGRATION_ROWS_SHA256_MISMATCH")
        plan = load_plan(intake, package)
        observed, validation = run_rows(plan, raw)
        files = {
            "PLAN.json": json_bytes({**plan, **AUTHORITY}),
            "ROWS.json": json_bytes(observed),
            "VALIDATION.json": json_bytes({**validation, **AUTHORITY}),
        }
        code = {}
        scripts = Path(__file__).resolve().parent
        for name in (Path(__file__).name, "migration_candidate.py"):
            code[f"scripts/{name}"] = identity(secure_read(scripts, name, LIMIT))
        files["MANIFEST.json"] = json_bytes({
            "input_manifest_sha256": plan["input_manifest_sha256"],
            "source_evidence": plan["source_evidence"],
            "input_rows": identity(raw),
            "candidate": code,
            "files": {name: identity(payload) for name, payload in files.items()},
            **AUTHORITY,
        })
        write_bundle(scratch, leaf, files, names=tuple(files))
    except FileExistsError:
        parser.exit(2, "BLOCKED: destination exists\n")
    except EvidenceError as error:
        parser.exit(2, f"{error.gate}: {error.code}\n")
    except (KeyError, TypeError, AttributeError, UnicodeError):
        parser.exit(2, "REFUSED: MIGRATION_INPUT_INVALID\n")
    except ValueError as error:
        parser.exit(2, f"REFUSED: {error}\n")
    except OSError:
        parser.exit(2, "REFUSED: FILE_IO_REFUSED\n")
    print(json_bytes({"open": str(scratch / leaf / "PLAN.json"),
                      "manifest_sha256": identity(files["MANIFEST.json"])["sha256"],
                      "comparison": validation["comparison"]}).decode(), end="")
    return 1 if validation["comparison"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
