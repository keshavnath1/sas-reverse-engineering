"""Conditionally sort and export the full records of one pinned MIG-5 scenario."""

import argparse
import csv
import io
import math
from pathlib import Path
import sys

from sas_re.platform_io import require_evidence_io
from sas_re.safeio import EvidenceError, _parse_json, ensure_disjoint, secure_read

sys.path.insert(0, str(Path(__file__).resolve().parent))
from migrate_preparation import CHARACTER_FIELDS, NUMERIC_FIELDS
from migrate_preparation_gates import LIMIT, ROOT, build_package
from migration_candidate import AUTHORITY
from migration_review import anchor
from mvp1_demo import scratch_destination, write_bundle
from review_intake import identity, json_bytes


COLUMNS = ("id", *NUMERIC_FIELDS, *CHARACTER_FIELDS, "Default")
SCENARIOS = ("passes", "empty", "duplicates", "count_mismatch", "guard_disabled", "invalid_identifier")
CSV_POLICY = {
    "columns": COLUMNS, "header": True, "delimiter": ",", "quoting": "MINIMAL_DOUBLE_QUOTE",
    "line_endings": "LF", "encoding": "UTF-8_NO_BOM",
    "numeric_format": "PYTHON_INTEGER_DECIMAL_OR_FINITE_FLOAT_REPR",
    "character_whitespace": "PRESERVE_STORED_FOUR_CHARACTER_VALUES",
    "missing_values": "REFUSED_NO_SENTINEL",
}


def sort_records(outputs):
    records = []
    for output in outputs:
        if type(output) is not dict or set(output) != {
            "case_id", "id", "numeric_group", "character_group", "default",
        }:
            raise ValueError("MIGRATION_EXPORT_RECORD_UNSUPPORTED")
        key, numeric, characters, label = (output[k] for k in
                                            ("id", "numeric_group", "character_group", "default"))
        if (type(key) is not int or abs(key) > 2**53
                or type(label) is not int or label not in (0, 1)
                or not isinstance(numeric, list) or len(numeric) != len(NUMERIC_FIELDS)
                or not isinstance(characters, list) or len(characters) != len(CHARACTER_FIELDS)
                or not isinstance(output["case_id"], str) or len(output["case_id"]) != 3
                or not output["case_id"].isascii() or not output["case_id"].isalnum()):
            raise ValueError("MIGRATION_EXPORT_RECORD_UNSUPPORTED")
        if any(not (type(value) is int and abs(value) <= 2**53
                    or type(value) is float and math.isfinite(value)) for value in numeric):
            raise ValueError("MIGRATION_EXPORT_NUMERIC_UNSUPPORTED")
        if any(type(item) is not dict or item.keys() != {"text"}
               or not isinstance(item["text"], str) or len(item["text"]) != 4
               or any(not 32 <= ord(char) <= 126 for char in item["text"]) for item in characters):
            raise ValueError("MIGRATION_EXPORT_CHARACTER_UNSUPPORTED")
        values = (key, *numeric, *(item["text"] for item in characters), label)
        records.append(dict(zip(COLUMNS, values, strict=True)))
    return sorted(records, key=lambda row: row["id"])


def csv_bytes(records):
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=COLUMNS, delimiter=",", quotechar='"',
                            doublequote=True, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
    return buffer.getvalue().encode("utf-8")


def build_export(prep, population, scenario):
    upstream, passed = build_package(prep, population)
    if not passed:
        raise ValueError("MIGRATION_UPSTREAM_ENGINEERING_COMPARISON_FAILED")
    run = next(item for item in _parse_json(upstream["SCENARIO_RESULTS.json"])
               if item["scenario"] == scenario)
    validation = next(item for item in _parse_json(upstream["VALIDATION.json"])["scenarios"]
                      if item["scenario"] == scenario)
    evidence = _parse_json(upstream["POPULATION_EVIDENCE.json"])
    sort = evidence["selections"][1]["declared_operation"]
    if (sort["kind"], sort["ordering_keys"], sort["declared_direction"]) != (
        "PROC_SORT", ["id"], "ASCENDING",
    ):
        raise ValueError("MIGRATION_SORT_CONTRACT_UNSUPPORTED")
    plan = _parse_json(upstream["PLAN.json"])
    plan["downstream"] = {
        "public_sort": {
            "evidence_file": "POPULATION_EVIDENCE.json",
            "evidence_pointer": "/selections/1/declared_operation",
            "anchor": anchor(sort["span"]),
            "by_anchor": anchor(sort["ordering_span"]),
            "selected_span": evidence["selections"][1]["selected_span"],
        },
        "export": {
            "classification": "HISTORICAL_SOURCE_CITED_MIGRATION_ASSUMPTION",
            "reference": "EX-1 reviewed export boundary",
            "source_sha256": "fe1bbbd9e531d53103aad52caafbd616a8365e9bcc81241ffa466aaa1c218f85",
            "line_range": [394, 399],
            "declarations": ["PROC EXPORT DATA=WORK.PREPARED_EXPORT", "DBMS=CSV", "REPLACE",
                             "FOLLOWING_STATUS_CHECK_MACRO"],
            "public_sort_to_historical_export_binding": "UNESTABLISHED",
        },
        "candidate_sort": "STABLE_ASCENDING_INTEGER_ID_FULL_RECORD",
        "candidate_csv": CSV_POLICY,
        "candidate_publication": "FRESH_DESTINATION_NO_REPLACE",
        "sas_export_execution": "UNOBSERVED",
    }
    files = {name: upstream[name] for name in ("PREPARATION_EVIDENCE.json", "POPULATION_EVIDENCE.json")}
    decision = run["continuation"]
    downstream = {"comparison": "NOT_RUN"}
    if decision == "PROCEED":
        eligible = [row["candidate_output"] for row in run["preparation"]["rows"]
                    if row["mode"] == "full" and row["candidate_row_end_reached"]]
        if [row["id"] for row in eligible] != run["handoff_ids"]:
            raise ValueError("MIGRATION_EXPORT_HANDOFF_MISMATCH")
        records = sort_records(eligible)
        observed = [row["id"] for row in records]
        passed = observed == [0, 1]
        downstream = {"comparison": "PASS" if passed else "FAIL",
                      "expected_sorted_ids": [0, 1], "observed_sorted_ids": observed}
        files["SORTED_ROWS.json"] = json_bytes(records)
        files["PREPARED_EXPORT.csv"] = csv_bytes(records)
        run["downstream_execution"] = "EXECUTED"
    else:
        run["downstream_execution"] = ("SKIPPED_BY_CANDIDATE_GATE" if decision == "BLOCK"
                                       else "SKIPPED_BY_INPUT_REFUSAL")
    files.update({
        "PLAN.json": json_bytes(plan),
        "SCENARIO_RESULT.json": json_bytes(run),
        "VALIDATION.json": json_bytes({
            "basis": "PUBLIC_PYTHON_ENGINEERING_EXPECTATIONS",
            "comparison": "PASS" if passed else "FAIL", "upstream": validation,
            "downstream": downstream, **AUTHORITY,
        }),
    })
    manifest = _parse_json(upstream["MANIFEST.json"])
    manifest["upstream_manifest"] = identity(upstream["MANIFEST.json"])
    manifest["scenario"] = scenario
    for name in ("migrate_sort_export.py", "mvp1_demo.py"):
        manifest["runner"][f"scripts/{name}"] = identity(secure_read(ROOT / "scripts", name, LIMIT))
    manifest["files"] = {name: identity(raw) for name, raw in files.items()}
    files["MANIFEST.json"] = json_bytes(manifest)
    return files, passed


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--preparation-evidence", type=Path, required=True)
    parser.add_argument("--population-evidence", type=Path, required=True)
    parser.add_argument("--scenario", choices=SCENARIOS, default="passes")
    parser.add_argument("--destination", required=True, help="fresh /tmp/sas-re-mig6-<label> directory")
    args = parser.parse_args()
    try:
        require_evidence_io()
        scratch, leaf = scratch_destination(args.destination, "mig6")
        prep, population = args.preparation_evidence.absolute(), args.population_evidence.absolute()
        ensure_disjoint(scratch / leaf, [prep.parent, population.parent])
        files, passed = build_export(prep, population, args.scenario)
        write_bundle(scratch, leaf, files, names=tuple(files), allow_csv=True)
    except FileExistsError:
        parser.exit(2, "BLOCKED: destination exists\n")
    except EvidenceError as error:
        parser.exit(2, f"{error.gate}: {error.code}\n")
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
