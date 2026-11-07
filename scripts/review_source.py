"""Review one explicitly selected SAS SORT span as source evidence."""

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
from mvp1_demo import scratch_destination, write_bundle

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


def inspect_sort(span, first, start):
    if len(span) > MAX_SPAN_BYTES:
        return None, ["SPAN_SIZE_LIMIT"]
    # Keep macro processing outside this entry point, including literal LET.
    if b"%" in span or b"&" in span:
        return None, ["MACRO_MARKER_OUTSIDE_SCOPE"]
    try:
        parsed = parse_source(span, file_key="source")
    except UnicodeDecodeError:
        return None, ["SPAN_NOT_UTF8"]
    if parsed["issues"]:
        return None, sorted({issue["code"] for issue in parsed["issues"]})
    operations = parsed["operations"]
    statements = [item["classification"] for item in parsed["statements"]
                  if item["classification"] != "COMMENT"]
    if (len(operations) != 1 or operations[0]["kind"] != "PROC_SORT"
            or statements != ["HEADER", "FACT", "TERMINATOR"]):
        return None, ["SINGLE_SORT_REQUIRED"]
    operation = operations[0]
    fact, = operation["facts"]

    def original_location(location):
        return {
            "line_start": first + location["line_start"] - 1,
            "line_end": first + location["line_end"] - 1,
            "start": start + location["start"],
            "end": start + location["end"],
        }

    return {
        "kind": "PROC_SORT",
        "input": fact["input"],
        "output": fact["output"],
        "ordering_keys": fact["keys"],
        "declared_direction": "ASCENDING",
        "span": original_location(operation["span"]),
        "ordering_span": original_location(fact["span"]),
    }, []


def review_text(evidence):
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
    else:
        keys = ", ".join(f"`{key}`" for key in operation["ordering_keys"])
        lines += [
            "## Declared dependency map", "",
            f"Unresolved upstream → `{operation['input']}` → SORT by {keys} ascending "
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
    return ("\n".join(lines) + "\n").encode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--source", required=True, type=Path, help="absolute path to one authorized SAS file")
    parser.add_argument("--source-sha256", required=True, help="expected SHA-256 of original file bytes")
    parser.add_argument("--lines", required=True, help="inclusive FIRST:LAST line range")
    parser.add_argument("--destination", required=True, help="fresh /tmp/sas-re-source-<label> directory")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-fA-F]{64}", args.source_sha256):
        parser.error("--source-sha256 requires 64 hexadecimal digits")
    if not re.fullmatch(r"[1-9][0-9]{0,7}:[1-9][0-9]{0,7}", args.lines):
        parser.error("--lines requires positive FIRST:LAST line numbers")
    first, last = map(int, args.lines.split(":"))
    if first > last:
        parser.error("--lines requires FIRST <= LAST")
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
        start, end = line_span(raw, first, last)
        span = raw[start:end]
        operation, reasons = inspect_sort(span, first, start)
        evidence = {
            **STATUS,
            "review_format": "source-only-sort/1",
            "source_identity": "VERIFIED",
            "syntax_recognition": "SUPPORTED" if operation else "UNSUPPORTED",
            "review_status": "PARTIAL" if operation else "BLOCKED",
            "source": {
                "sha256": source_digest,
                "bytes": len(raw),
                "selected_span": {
                    "line_start": first, "line_end": last, "start": start, "end": end,
                    "sha256": sha256(span).hexdigest(),
                },
            },
            "declared_operation": operation,
            "reason_codes": reasons,
            "boundaries": BOUNDARIES,
        }
        files = {
            "README.md": review_text(evidence),
            "EVIDENCE.json": (json.dumps(evidence, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        }
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
    return 0 if operation else 2


if __name__ == "__main__":
    sys.exit(main())
