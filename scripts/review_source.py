"""Review one explicitly selected SAS SORT or DATA-step span as source evidence."""

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import sys

from sas_re.platform_io import require_evidence_io
from sas_re.safeio import EvidenceError, secure_read
from sas_re.sas_subset import parse_source

ROOT = Path(__file__).resolve().parents[1]
# Isolated Python excludes the script directory.
sys.path.insert(0, str(ROOT / "scripts"))
from migration_review import (
    anchor, logistic_lines, missing_rule_relationships, render as render_migration_review, rule_description,
)
from mvp1_demo import scratch_destination, write_bundle
from source_interval import inspect_logistic, inventory as interval_inventory
from source_rules import recover as recover_status_rules

MAX_SPAN_BYTES = 64 * 1024
STATUS = {
    "artifact_authority": "DRAFT",
    "behavioral_evidence": "UNAVAILABLE",
    "semantic_verification": "UNVERIFIABLE",
    "semantic_acceptance": "BLOCKED",
    "benchmark_execution": "NOT_RUN",
    "execution_behavior": "UNKNOWN",
    "key_schema": "UNKNOWN",
    "supported_profile_reconstruction": "NOT_RUN",
}
BOUNDARIES = {
    "upstream": "UNRESOLVED",
    "downstream": "UNRESOLVED",
}


def line_span(raw, first, last):
    line_start = 0
    for number, terminator in enumerate(re.finditer(rb"\r\n|\r|\n|\Z", raw), 1):
        if terminator.end() == line_start:
            break
        if number == first:
            start = line_start
        if number == last:
            return start, terminator.end()
        line_start = terminator.end()
    raise ValueError("LINE_RANGE_OUTSIDE_SOURCE")


def original_location(location, first, start):
    return {
        "line_start": first + location["line_start"] - 1,
        "line_end": first + location["line_end"] - 1,
        "start": start + location["start"],
        "end": start + location["end"],
    }


def inspect_data(parsed, span, first, start, recover_rules=False, recover_missing=False):
    operation, = parsed["operations"]
    statements = [item for item in parsed["statements"] if item["classification"] != "COMMENT"]
    if ([item["classification"] for item in (statements[0], statements[-1])]
            != ["HEADER", "TERMINATOR"]
            or statements[0]["span"]["start"] != operation["span"]["start"]
            or statements[-1]["span"]["end"] != operation["span"]["end"]):
        return None, ["SINGLE_TERMINATED_DATA_STEP_REQUIRED"]

    declarations = {}
    for kind in ("output", "input", "keep"):
        matches = [fact for fact in operation["facts"] if fact["kind"] == kind]
        if len(matches) != 1:
            return None, ["SINGLE_DATA_SET_KEEP_REQUIRED"]
        declarations[kind] = matches[0]
    input_fact = declarations["input"]
    if input_fact["mode"] != "SET" or len(input_fact["datasets"]) != 1:
        return None, ["SINGLE_SET_INPUT_REQUIRED"]

    def bounds(location):
        return location["start"], location["end"]

    def bound_location(location):
        a, b = bounds(location)
        return {**original_location(location, first, start), "sha256": sha256(span[a:b]).hexdigest()}

    # Parser fact spans can exclude the semicolon. Bind each declaration to
    # its containing statement before deciding which statements are gaps.
    declaration_locations = {}
    for kind, fact in declarations.items():
        a, b = bounds(fact["span"])
        location = next(item["span"] for item in statements
                        if item["span"]["start"] <= a and b <= item["span"]["end"])
        declaration_locations[kind] = location
    recovered = {bounds(location) for location in declaration_locations.values()}
    gaps = {
        bounds(item["span"]): (item["span"], set())
        for item in statements[1:-1] if bounds(item["span"]) not in recovered
    }
    for issue in parsed["issues"]:
        location = issue["span"]
        gaps.setdefault(bounds(location), (location, set()))[1].add(issue["code"])
    unsupported = [
        {
            "span": bound_location(location),
            "reason_codes": sorted(codes) or ["TRANSFORMATION_OUTSIDE_REVIEW_SCOPE"],
            "effect": "ROW_SELECTION_OR_VALUE_DERIVATION_UNRESOLVED",
        }
        for _, (location, codes) in sorted(gaps.items())
    ]
    result = {
        "kind": "DATA_STEP",
        "input": input_fact["datasets"][0],
        "output": declarations["output"]["dataset"],
        "selected_columns": declarations["keep"]["names"],
        "span": bound_location(operation["span"]),
        "declaration_spans": {kind: bound_location(location) for kind, location in declaration_locations.items()},
        "unsupported_statements": unsupported,
        "row_selection": "UNKNOWN",
        "selected_column_values_and_derivation": "UNKNOWN",
        "input_schema": "UNKNOWN",
        "output_schema": "UNKNOWN",
    }
    if recover_rules:
        rules = recover_status_rules(span, include_missing=recover_missing)
        for rule in rules:
            rule["span"] = bound_location(rule["span"])
            gap = next(item for item in unsupported if item["span"] == rule["span"])
            rule["parser_reason_codes"] = gap["reason_codes"]
            rule["classification"] = "SOURCE_RECOGNIZED"
        result["status_rule_recovery"] = {
            "status": "RECOVERED" if rules else "UNRESOLVED",
            "rules": rules,
            "fallthrough": "NO_ASSIGNMENT_BY_PAIR" if rules else "UNKNOWN",
            "execution_verification": "UNVERIFIED",
        }
        if recover_missing and rules and len(rules) < 6:
            result["status_rule_recovery"]["status"] = "PARTIAL"
        recovered_spans = [rule["span"] for rule in rules]
        result["unsupported_statements"] = [
            gap for gap in unsupported if gap["span"] not in recovered_spans
        ]
    return result, []


def inspect_span(span, first, start, recover_rules=False, recover_missing=False):
    if len(span) > MAX_SPAN_BYTES:
        return None, ["SPAN_SIZE_LIMIT"]
    # Keep macro processing outside this entry point, including literal LET.
    if b"%" in span or b"&" in span:
        return None, ["MACRO_MARKER_OUTSIDE_SCOPE"]
    try:
        parsed = parse_source(span, file_key="source")
    except UnicodeDecodeError:
        return None, ["SPAN_NOT_UTF8"]
    operations = parsed["operations"]
    if len(operations) == 1 and operations[0]["kind"] == "DATA_STEP":
        return inspect_data(parsed, span, first, start, recover_rules, recover_missing)
    if parsed["issues"]:
        return None, sorted({issue["code"] for issue in parsed["issues"]})
    statements = [item["classification"] for item in parsed["statements"]
                  if item["classification"] != "COMMENT"]
    if (len(operations) != 1 or operations[0]["kind"] != "PROC_SORT"
            or statements != ["HEADER", "FACT", "TERMINATOR"]):
        return None, ["SINGLE_SORT_REQUIRED"]
    operation = operations[0]
    fact, = operation["facts"]

    return {
        "kind": "PROC_SORT",
        "input": fact["input"],
        "output": fact["output"],
        "ordering_keys": fact["keys"],
        "declared_direction": "ASCENDING",
        "span": original_location(operation["span"], first, start),
        "ordering_span": original_location(fact["span"], first, start),
    }, []


def review_text(evidence, *, dependency_anchors=False):
    source = evidence["source"]
    span = source["selected_span"]
    lines = [
        "# Source-only SAS review", "",
        "See [EVIDENCE.json](EVIDENCE.json) for the source and span bindings.", "",
        "~~~text",
        *(f"{key}: {value}" for key, value in evidence.items() if isinstance(value, str)),
        "~~~", "",
        f"**Verified source identity.** SHA-256 `{source['sha256']}`.",
        f"Selected lines {span['line_start']}–{span['line_end']}, original bytes "
        f"[{span['start']}, {span['end']}). Span SHA-256 `{span['sha256']}`.", "",
        "Syntax recognition concerns the selected bytes in isolation. Surrounding SAS context "
        "and actual execution remain unknown.", "",
    ]
    operation = evidence["declared_operation"]
    if operation is None:
        lines += ["**Unsupported span.** Review reason codes in the evidence register."]
    elif operation["kind"] == "PROC_LOGISTIC":
        lines.extend(logistic_lines(operation))
    elif operation["kind"] == "DATA_STEP":
        columns = ", ".join(f"`{name}`" for name in operation["selected_columns"])
        input_anchor = output_anchor = ""
        if dependency_anchors:
            spans = operation["declaration_spans"]
            input_anchor = f'<a id="{anchor(spans["input"])}"></a>'
            output_anchor = f'<a id="{anchor(spans["output"])}"></a>'
        lines += [
            "## Declared dependency map", "",
            f"Unresolved upstream → {input_anchor}`{operation['input']}` → DATA step "
            f"→ {output_anchor}`{operation['output']}` → unresolved downstream.", "",
            f"KEEP declares {len(operation['selected_columns'])} output selections: {columns}.",
            "Input and output schemas, row selection, selected values and label derivation remain unknown.", "",
            "## Unsupported statement register", "",
        ]
        for gap in operation["unsupported_statements"]:
            location = gap["span"]
            reasons = ", ".join(gap["reason_codes"])
            lines.append(f"- Lines {location['line_start']}–{location['line_end']}, original bytes "
                         f"[{location['start']}, {location['end']}), SHA-256 `{location['sha256']}`. "
                         f"{reasons}. Row selection or value derivation remains unresolved.")
        if not operation["unsupported_statements"]:
            lines.append("The review recovered the declared input, output and selection.")
        lines += [
            "", "## Draft requirements and architecture", "",
            "- Confirm input and output descriptors and use the declared KEEP selection as a "
            "candidate output contract.",
            "- Establish the ordered transformation and exclusion rules with bound reference "
            "rows before specifying survivor counts or derived label values.",
            "- Consider a local preparation stage when the input and working set fit memory. "
            "A partitioned alternative requires evidence for row selection, branch order, "
            "state dependencies and output preservation across partitions and retries.",
        ]
    else:
        keys = ", ".join(f"`{key}`" for key in operation["ordering_keys"])
        marker = f'<a id="{anchor(operation["span"])}"></a>' if dependency_anchors else ""
        lines += [
            "## Declared dependency map", "",
            f"{marker}Unresolved upstream → `{operation['input']}` → SORT by {keys} ascending "
            f"→ `{operation['output']}` → unresolved downstream.", "",
            "## Draft requirements and architecture", "",
            f"- Confirm the input descriptor, including the type and storage length of {keys} "
            "and the columns carried through the SORT. The current supported profile needs "
            "numeric keys and compatible input metadata.",
            "- Compare row multiplicity and values before and after ordering under a confirmed "
            "key comparison policy. Establish missing-value and equal-key behavior with a "
            "bound reference before accepting results.",
            "- Consider local sorting if the input and sort workspace fit memory. A distributed "
            "candidate needs evidence for global ordering and row preservation across partitions "
            "and retries. Runtime selection remains open.", "",
            "The upstream producer, downstream consumers and side effects require separate "
            "evidence. Behavioral reference outputs are unavailable.",
        ]
    if operation and "status_rule_recovery" in operation:
        recovery = operation["status_rule_recovery"]
        lines += ["", "## Ordered source rules", "", f"Recovery {recovery['status']}. Execution UNVERIFIED.", ""]
        for rule in recovery["rules"]:
            location = rule["span"]
            marker = f'<a id="{anchor(location)}"></a>' if evidence["review_format"].endswith("/3") else ""
            lines.append(f"- {marker}Lines {location['line_start']}–{location['line_end']}, "
                         f"bytes [{location['start']}, {location['end']}), SHA-256 `{location['sha256']}`. "
                         + rule_description(rule))
        if recovery["rules"]:
            lines += ["", "A true exclusion guard terminates this row before either assignment. "
                      "The linked alternative is tested only when the first assignment guard is false. "
                      "Neither branch matching yields NO_ASSIGNMENT_BY_PAIR. "
                      "Later unresolved statements may still exclude or change an assigned row. "
                      "Schema and comparison behavior require independent reference evidence."]
        lines.extend(missing_rule_relationships(recovery["rules"]))
    return ("\n".join(lines) + "\n").encode("utf-8")


def inspect_range(raw, first, last, recover_rules=False, recover_missing=False, recover_logistic=False):
    start, end = line_span(raw, first, last)
    span = raw[start:end]
    if recover_logistic:
        operation, reasons = inspect_logistic(span, first, start, MAX_SPAN_BYTES)
    else:
        operation, reasons = inspect_span(span, first, start, recover_rules, recover_missing)
    location = {
        "line_start": first, "line_end": last, "start": start, "end": end,
        "sha256": sha256(span).hexdigest(),
    }
    return location, operation, reasons


def dependency_review(raw, ranges, source_digest, recover_rules=False, recover_missing=False, recover_sql=False):
    selections = []
    for first, last in ranges:
        span, operation, reasons = inspect_range(raw, first, last, recover_rules, recover_missing)
        selections.append({"selected_span": span, "declared_operation": operation,
                           "reason_codes": reasons})
    data, sort = (item["declared_operation"] for item in selections)
    if not data or not sort or (data["kind"], sort["kind"]) != ("DATA_STEP", "PROC_SORT"):
        raise ValueError("DATA_THEN_SORT_REQUIRED")

    # The parser already normalizes ordinary SAS identifiers to lowercase.
    matched = data["output"] == sort["input"]
    connection = {
        "classification": "SOURCE_DECLARED" if matched else "UNRESOLVED",
        "execution_verification": "EXECUTION_UNVERIFIED",
        "data_output": data["output"],
        "sort_input": sort["input"],
    }
    first_span, last_span = (item["selected_span"] for item in selections)
    # Retain the RS-4 operation-parse boundary. The separate inventory
    # describes the limited inspection of these same intervening bytes.
    intermediate = {
        "status": "UNEXAMINED",
        "start": first_span["end"],
        "end": last_span["start"],
    }
    interval = interval_inventory(
        raw, intermediate["start"], intermediate["end"],
        first_span["line_end"] + 1, data["output"] if matched else None, MAX_SPAN_BYTES, recover_sql=recover_sql,
    )
    evidence = {
        **STATUS,
        "review_format": "source-only-dependency/2" if recover_rules else "source-only-dependency/1",
        "source_identity": "VERIFIED",
        "syntax_recognition": "PARTIAL" if data["unsupported_statements"] else "SUPPORTED",
        "review_status": "PARTIAL",
        "source": {"sha256": source_digest, "bytes": len(raw)},
        "selections": selections,
        "connection": connection,
        "intervening_span": intermediate,
        "interval_effects": interval,
        "boundaries": BOUNDARIES,
    }
    if recover_missing:
        evidence["review_format"] = "source-only-dependency/3"
    if recover_sql:
        evidence.update(review_format="source-only-dependency/4", reference_experiment="NOT_RUN",
                        historical_source_run_provenance="UNBOUND")
    relationship = (
        f"DATA writes and SORT reads the declared dataset `{data['output']}`."
        if matched else
        f"DATA writes `{data['output']}` while SORT reads `{sort['input']}`. The connection is unresolved."
    )
    columns = ", ".join(f"`{name}`" for name in data["selected_columns"])
    keys = ", ".join(f"`{key}`" for key in sort["ordering_keys"])
    lines = [
        "# Source-only DATA and SORT review", "",
        "See [EVIDENCE.json](EVIDENCE.json) for hashes, original spans and parser reasons.", "",
        "~~~text",
        *(f"{key}: {value}" for key, value in evidence.items() if isinstance(value, str)),
        "~~~", "",
        "## Declared dependencies", "",
        f"DATA reads `{data['input']}` and writes `{data['output']}`.",
        f"SORT reads `{sort['input']}` and writes `{sort['output']}` by {keys} ascending.",
        f"{connection['classification']} / EXECUTION_UNVERIFIED. {relationship}", "",
        f"Intervening bytes [{intermediate['start']}, {intermediate['end']}) are outside the selected operations. "
        "The limited inventory below records recognizable references and unresolved effects. "
        "Runtime dataset identity, version and successful execution remain unknown.", "",
        f"KEEP declares {len(data['selected_columns'])} output selections ({columns}).",
        "Input and output schemas, key type, row survival and label derivation remain unknown.", "",
        "## Unresolved DATA statements", "",
    ]
    for gap in data["unsupported_statements"]:
        location = gap["span"]
        reasons = ", ".join(gap["reason_codes"])
        lines.append(f"- Lines {location['line_start']}–{location['line_end']}. {reasons}.")
    if not data["unsupported_statements"]:
        lines.append("The review recovered the declared input, output and selection.")
    lines += [
        "", "## Intervening source effects", "",
        f"Inventory {interval['status']}. Interval SHA-256 {interval['sha256']}.",
        "Explicit reads: " + (", ".join(interval["direct_reads"]) or "none identified") + ".",
        "Explicit outputs other than the shared dataset: " + (", ".join(interval["other_outputs"]) or "none identified") + ".",
        "SORT reachability remains unestablished.",
    ]
    if interval["shared_writer_identified"] is True:
        lines.append("An explicit output targets the shared dataset and may replace it.")
    elif interval["shared_writer_identified"] is False:
        lines.append("No direct writer identified within the inspected supported source forms; unresolved effects remain.")
    for item in interval["findings"]:
        location = item["span"]
        effects = [f"{key}: {', '.join(values)}" for key, values in item.items()
                   if key not in {"span", "sql_declaration", "gate_declaration"} and values]
        lines.append(f"- Lines {location['line_start']}–{location['line_end']}, "
                     f"bytes [{location['start']}, {location['end']}). " + ". ".join(effects) + ".")
    lines += [
        "", "## Candidate requirements and proof obligations", "",
        "- Bind the prepared dataset version to both operations and account for intervening effects.",
        "- Confirm the boundary schemas and numeric key contract. Establish row eligibility, "
        "label values, row preservation and ordering against attributable reference outputs.",
        "- Resolve upstream and downstream effects separately. Behavioral evidence is unavailable.",
    ]
    if recover_rules or recover_sql:
        lines += ["", "See [MIGRATION_REVIEW.md](MIGRATION_REVIEW.md) for ordered source-rule "
                  "recovery, TRACE links and unresolved behavior."]
    return evidence, ("\n".join(lines) + "\n").encode("utf-8")


def single_review(raw, selected_range, source_digest, *, recover_rules=False,
                  recover_missing=False, recover_logistic=False, dependency_anchors=False):
    selected_span, operation, reasons = inspect_range(
        raw, *selected_range, recover_rules=recover_rules,
        recover_missing=recover_missing, recover_logistic=recover_logistic,
    )
    is_data = operation is not None and operation["kind"] == "DATA_STEP"
    syntax = "SUPPORTED" if operation else "UNSUPPORTED"
    if is_data and operation["unsupported_statements"]:
        syntax = "PARTIAL"
    evidence = {
        **STATUS,
        "review_format": "source-only-data/1" if is_data else "source-only-sort/1",
        "source_identity": "VERIFIED",
        "syntax_recognition": syntax,
        "review_status": "PARTIAL" if operation else "BLOCKED",
        "source": {
            "sha256": source_digest,
            "bytes": len(raw),
            "selected_span": selected_span,
        },
        "declared_operation": operation,
        "reason_codes": reasons,
        "boundaries": BOUNDARIES,
    }
    if is_data and recover_rules:
        evidence["review_format"] = "source-only-data/2"
    if is_data and recover_missing:
        evidence["review_format"] = "source-only-data/3"
    if recover_logistic:
        evidence.update(review_format="source-only-logistic/1", reference_experiment="NOT_RUN",
                        historical_source_run_provenance="UNBOUND")
    readme = review_text(evidence, dependency_anchors=dependency_anchors)
    return evidence, readme


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--source", required=True, type=Path, help="absolute path to one authorized SAS file")
    parser.add_argument("--source-sha256", required=True, help="expected SHA-256 of original file bytes")
    parser.add_argument("--lines", required=True, action="append", help="inclusive FIRST:LAST, repeat for DATA then SORT")
    parser.add_argument("--recover-status-rules", action="store_true",
                        help="opt in to bounded source-only status rule recovery")
    parser.add_argument("--recover-missing-exclusions", action="store_true",
                        help="extend status recovery with ordered MISSING and CMISS exclusions")
    parser.add_argument("--recover-sql-gates", action="store_true",
                        help="recover bounded SQL and abort declarations between two ranges")
    parser.add_argument("--recover-logistic", action="store_true",
                        help="recover one bounded ODS and PROC LOGISTIC fit-to-score range")
    parser.add_argument("--destination", required=True, help="fresh /tmp/sas-re-source-<label> directory")
    args = parser.parse_args()
    if args.recover_missing_exclusions and not args.recover_status_rules:
        parser.error("--recover-missing-exclusions requires --recover-status-rules")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", args.source_sha256):
        parser.error("--source-sha256 requires 64 hexadecimal digits")
    if len(args.lines) not in (1, 2):
        parser.error("supply one or two --lines ranges")
    if args.recover_sql_gates and len(args.lines) != 2:
        parser.error("--recover-sql-gates requires two --lines ranges")
    if args.recover_logistic and (len(args.lines) != 1 or args.recover_status_rules
                                  or args.recover_missing_exclusions or args.recover_sql_gates):
        parser.error("--recover-logistic requires one --lines range and no other recovery flags")
    ranges = []
    for value in args.lines:
        if not re.fullmatch(r"[1-9][0-9]{0,7}:[1-9][0-9]{0,7}", value):
            parser.error("--lines requires positive FIRST:LAST line numbers")
        first, last = map(int, value.split(":"))
        if first > last:
            parser.error("--lines requires FIRST <= LAST")
        ranges.append((first, last))
    if len(ranges) == 2 and ranges[0][1] >= ranges[1][0]:
        parser.error("two --lines ranges must be in source order and disjoint")
    source = args.source
    if not source.is_absolute() or ".." in source.parts or source.suffix.lower() != ".sas":
        parser.error("--source requires an absolute .sas path without parent traversal")

    try:
        require_evidence_io()
        scratch, leaf = scratch_destination(args.destination, "source")
        if os.path.lexists(scratch / leaf):
            raise FileExistsError
        if any(parent.samefile(ROOT) for parent in source.resolve(strict=True).parents):
            raise ValueError("SOURCE_MUST_BE_OUTSIDE_CHECKOUT")
        raw = secure_read(source.parent, source.name)
        source_digest = sha256(raw).hexdigest()
        if source_digest != args.source_sha256.lower():
            parser.exit(2, "source_identity: REFUSED (SOURCE_SHA256_MISMATCH)\n")
        if len(ranges) == 2:
            evidence, readme = dependency_review(
                raw, ranges, source_digest, args.recover_status_rules, args.recover_missing_exclusions,
                recover_sql=args.recover_sql_gates,
            )
        else:
            evidence, readme = single_review(
                raw, ranges[0], source_digest, recover_rules=args.recover_status_rules,
                recover_missing=args.recover_missing_exclusions, recover_logistic=args.recover_logistic,
            )
        files = {
            "README.md": readme,
            "EVIDENCE.json": (json.dumps(evidence, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        }
        if len(ranges) == 2:
            files["MIGRATION_REVIEW.md"] = render_migration_review(evidence)
        write_bundle(scratch, leaf, files, names=tuple(files))
    except FileExistsError:
        parser.exit(2, "BLOCKED: destination exists\n")
    except (EvidenceError, OSError, ValueError) as error:
        reason = str(error) if isinstance(error, ValueError) else getattr(error, "code", "FILE_IO_REFUSED")
        parser.exit(2, f"REFUSED: {reason}\n")

    print(json.dumps({
        "open": str(scratch / leaf / "README.md"),
        "evidence_sha256": sha256(files["EVIDENCE.json"]).hexdigest(),
        "source_identity": evidence["source_identity"],
        "syntax_recognition": evidence["syntax_recognition"],
    }, indent=2))
    return 0 if evidence["review_status"] == "PARTIAL" else 2


if __name__ == "__main__":
    sys.exit(main())
