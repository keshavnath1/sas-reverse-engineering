"""Bind the existing PY-1 candidate to an approved public six-rule source review."""

import argparse
from collections import Counter
from dataclasses import asdict
from pathlib import Path
import sys

from sas_re.platform_io import require_evidence_io
from sas_re.safeio import EvidenceError, _parse_json, ensure_disjoint, secure_read

sys.path.insert(0, str(Path(__file__).resolve().parent))
from migration_candidate import AUTHORITY
from migration_review import anchor
from mvp1_demo import scratch_destination, write_bundle
from preparation_candidate import Character, NumericMissing, SyntheticRecord, prepare
from review_copilot_notes import LIMIT
from review_intake import identity, json_bytes
from review_source import MAX_SPAN_BYTES, single_review


EXAMPLE = Path(__file__).resolve().parents[1] / "examples/mig3"
NUMERIC_FIELDS = [f"n{i}" for i in range(1, 13)]
CHARACTER_FIELDS = [f"c{i}" for i in range(1, 6)]


def bind_rules(source, expected_digest, evidence_bytes):
    original = identity(source)
    if original["sha256"] != expected_digest:
        raise ValueError("MIGRATION_SOURCE_SHA256_MISMATCH")
    lines = len(source.splitlines())
    if not lines:
        raise ValueError("MIGRATION_EMPTY_SOURCE")
    evidence, _ = single_review(source, (1, lines), expected_digest,
                                recover_rules=True, recover_missing=True)
    if json_bytes(evidence) != evidence_bytes:
        raise ValueError("MIGRATION_EVIDENCE_MISMATCH")
    operation = evidence["declared_operation"] or {}
    recovery = operation.get("status_rule_recovery", {})
    rules = recovery.get("rules", [])
    if (evidence["syntax_recognition"] != "SUPPORTED" or operation["kind"] != "DATA_STEP"
            or evidence["source"]["selected_span"]["end"] != len(source)
            or recovery.get("status") != "RECOVERED"
            or recovery.get("fallthrough") != "NO_ASSIGNMENT_BY_PAIR"
            or len(rules) != 6 or operation["unsupported_statements"]
            or operation["input"] == operation["output"]
            or operation["selected_columns"] != ["case_id", "id", *NUMERIC_FIELDS,
                                                  *CHARACTER_FIELDS, "default"]):
        raise ValueError("MIGRATION_SIX_RULE_CONTRACT_UNSUPPORTED")

    # Compare declarations with the fixed public PY-1 contract. No predicates
    # are executed here, and no schema is inferred from the source.
    delete = {"kind": "DELETE", "scope": "CURRENT_ROW_ITERATION",
              "on_match": "SKIP_REMAINING_STATEMENTS_AND_SUPPRESS_OUTPUT"}
    predicates = [
        {"variable": "status", "operator": "NOT IN", "values": ["A", "B"]},
        {"variable": "status", "operator": "=", "value": "A"},
        {"variable": "status", "operator": "=", "value": "B"},
        {"function": "MISSING", "arguments": ["id"], "evaluation": "DIRECT"},
        *({"function": "CMISS", "arguments": fields, "evaluation": "COMPARISON",
           "operator": ">", "value_lexeme": "0"} for fields in (NUMERIC_FIELDS, CHARACTER_FIELDS)),
    ]
    actions = [delete, *({"kind": "ASSIGN_NUMERIC_LITERAL", "target": "default", "lexeme": value}
                         for value in ("1", "0")), delete, delete, delete]
    prerequisites = ((), (0,), (0, 1), (0,), (0, 3), (0, 3, 4))
    bindings = []
    end = 0
    for index, (rule, predicate, action, before) in enumerate(
        zip(rules, predicates, actions, prerequisites, strict=True)
    ):
        span = rule["span"]
        if (rule["predicate"] != predicate or rule["action"] != action
                or rule["when"] != [{"rule_index": i, "predicate_result": False} for i in before]
                or not end <= span["start"] < span["end"] <= len(source)
                or identity(source[span["start"]:span["end"]])["sha256"] != span["sha256"]):
            raise ValueError("MIGRATION_SIX_RULE_CONTRACT_UNSUPPORTED")
        end = span["end"]
        bindings.append({
            "rule_index": index, "span": span, "anchor": anchor(span),
            "evidence_pointer": f"/declared_operation/status_rule_recovery/rules/{index}",
        })
    return {
        "source": original, "evidence": identity(evidence_bytes), "rules": bindings,
        "dataset_declarations": {"input": operation["input"], "output": operation["output"]},
        "candidate_assumptions": {
            "input_descriptors": "PY1_PUBLIC_TYPED_CONTRACT",
            "isolated_pair": "PY1_PROBE_OMITS_RULE_0",
            "candidate_row_end": "PYTHON_ONLY_SAS_DATASET_OUTPUT_UNOBSERVED",
        },
        "copilot_review_notes": "SEPARATE_OPTIONAL_ARTIFACT",
        **AUTHORITY,
    }


def run_cases(cases, bindings):
    def number(value):
        return NumericMissing(value) if isinstance(value, str) else value

    rows, checks, exclusions, labels = [], [], Counter(), Counter()
    for case in cases:
        case_id = case["id"]
        mode = case.get("mode", "full")
        values = {"id": int(case_id[1:]), **dict.fromkeys(NUMERIC_FIELDS, 1),
                  **dict.fromkeys(CHARACTER_FIELDS, "X"), **case.get("overrides", {})}
        record = SyntheticRecord(
            case_id, Character(case["status"].ljust(8)), number(values["id"]),
            tuple(number(values[field]) for field in NUMERIC_FIELDS),
            tuple(Character(values[field].ljust(4)) for field in CHARACTER_FIELDS),
            9 if mode == "isolated_pair" else NumericMissing(),
        )
        result = prepare(record, mode=mode)
        output = asdict(result.output) if result.output else None
        observed = [result.first_exclusion_rule, result.label_assignment_branch,
                    output["default"] if output else None]
        checks.append({"case_id": case_id, "expected": case["expected"], "observed": observed,
                       "comparison": "PASS" if observed == case["expected"] else "FAIL"})
        if result.first_exclusion_rule is not None:
            exclusions[str(result.first_exclusion_rule)] += 1
        if result.label_assignment_branch is not None:
            labels[str(result.label_assignment_branch)] += 1
        rows.append({
            "input": asdict(record), "mode": mode, "candidate_output": output,
            "candidate_row_end_reached": output is not None, "sas_dataset_output": "UNOBSERVED",
            "first_exclusion_rule": result.first_exclusion_rule,
            "label_assignment_branch": result.label_assignment_branch,
            "trace": [{"action": event.action, "predicate_result": event.predicate_result,
                       **bindings[event.rule_index]} for event in result.trace],
        })
    return rows, checks, {
        "first_exclusions_by_rule": dict(exclusions), "assignments_by_rule": dict(labels),
        "candidate_row_end_count": sum(row["candidate_row_end_reached"] for row in rows),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--source", type=Path, required=True, help="approved public synthetic source")
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--evidence", type=Path, required=True, help="existing SM-3B EVIDENCE.json")
    parser.add_argument("--destination", required=True, help="fresh /tmp/sas-re-mig3-<label> directory")
    args = parser.parse_args()
    try:
        require_evidence_io()
        scratch, leaf = scratch_destination(args.destination, "mig3")
        source, evidence = args.source.absolute(), args.evidence.absolute()
        ensure_disjoint(scratch / leaf, [source.parent, evidence.parent])
        plan = bind_rules(secure_read(source.parent, source.name, MAX_SPAN_BYTES),
                          args.source_sha256, secure_read(evidence.parent, evidence.name, LIMIT))
        plan["source"]["path"] = source.name
        cases = secure_read(EXAMPLE, "CASES.json", LIMIT)
        rows, checks, summary = run_cases(_parse_json(cases), plan["rules"])
        passed = all(check["comparison"] == "PASS" for check in checks)
        files = {
            "PLAN.json": json_bytes(plan), "ROWS.json": json_bytes(rows),
            "VALIDATION.json": json_bytes({
                "basis": "PUBLIC_PYTHON_ENGINEERING_EXPECTATIONS",
                "comparison": "PASS" if passed else "FAIL",
                "comparison_fields": ["first_exclusion_rule", "label_assignment_branch",
                                      "survivor_default"],
                "summary": summary, "cases": checks, **AUTHORITY,
            }),
        }
        scripts = Path(__file__).resolve().parent
        files["MANIFEST.json"] = json_bytes({
            "source": plan["source"], "evidence": plan["evidence"], "public_cases": identity(cases),
            "candidate": {name: identity(secure_read(scripts, name, LIMIT))
                          for name in (Path(__file__).name, "preparation_candidate.py")},
            "files": {name: identity(payload) for name, payload in files.items()}, **AUTHORITY,
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
                      "comparison": "PASS" if passed else "FAIL"}).decode(), end="")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
