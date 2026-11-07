"""Review an explicitly scoped public synthetic intake directory."""

import argparse
from hashlib import sha256
import json
import os
import re
from pathlib import Path
import sys

from sas_re.platform_io import require_evidence_io
from sas_re.safeio import (EvidenceError, _parse_json, ensure_disjoint, enumerate_files,
                          safe_relative, secure_read)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from migration_review import render
from mvp1_demo import scratch_destination, write_bundle
from review_source import dependency_review, line_span, single_review


SCOPE_SHA256 = "268585d9ac407d5d26b924aed49b5e7fe5edac55928576209ee20cae86ebf9ba"
STATUS_FIELDS = (
    "artifact_authority", "behavioral_evidence", "semantic_verification",
    "semantic_acceptance", "reference_experiment", "benchmark_execution",
    "historical_source_run_provenance",
)


def identity(data):
    return {"bytes": len(data), "sha256": sha256(data).hexdigest()}


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


SINGLE_MODES = {"data": "DATA_STEP", "sort": "PROC_SORT", "logistic": "PROC_LOGISTIC"}
PAIR_MODES = {"data-sort", "data-sort-sql"}


def validate_scope(scope):
    required = {"version", "scope", "sources", "mode"}
    if (not isinstance(scope, dict) or not required <= scope.keys()
            or scope.keys() - required - {"supporting"}):
        raise ValueError("INTAKE_MANIFEST_INVALID")
    if type(scope["version"]) is not int or scope["version"] != 1:
        raise ValueError("INTAKE_MANIFEST_VERSION_UNSUPPORTED")
    if scope["scope"] != "public-synthetic":
        raise ValueError("INTAKE_PUBLIC_SYNTHETIC_SCOPE_REQUIRED")
    sources = scope["sources"]
    if not isinstance(sources, list) or not sources:
        raise ValueError("INTAKE_MANIFEST_INVALID")
    if len(sources) > 1:
        raise ValueError("INTAKE_MULTIPLE_SOURCES_UNSUPPORTED")
    mode = scope["mode"]
    if not isinstance(mode, str) or mode not in SINGLE_MODES.keys() | PAIR_MODES:
        raise ValueError("INTAKE_REVIEW_MODE_UNSUPPORTED")
    source = sources[0]
    supporting = scope.get("supporting", [])
    if (not isinstance(source, dict) or set(source) != {"path", "sha256", "ranges"}
            or not isinstance(supporting, list) or len(supporting) > 4
            or any(not isinstance(item, dict) or set(item) != {"path", "sha256", "role"}
                   for item in supporting)):
        raise ValueError("INTAKE_MANIFEST_INVALID")
    names = {"scope.json"}
    for item in [source, *supporting]:
        name = safe_relative(item["path"])
        if "/" in name or name.lower() in names:
            raise ValueError("INTAKE_FILE_NAME_UNSUPPORTED")
        names.add(name.lower())
        digest = item["sha256"]
        if not isinstance(digest, str) or not re.fullmatch("[0-9a-f]{64}", digest):
            raise ValueError("INTAKE_SHA256_INVALID")
    if not source["path"].lower().endswith((".sas", ".sas.txt")):
        raise ValueError("INTAKE_SOURCE_TYPE_UNSUPPORTED")
    for item in supporting:
        name = item["path"].lower()
        if name.endswith((".sas", ".sas.txt")):
            raise ValueError("INTAKE_MULTIPLE_SOURCES_UNSUPPORTED")
        if item["role"] != "note" or not name.endswith((".txt", ".md")):
            raise ValueError("INTAKE_SUPPORT_ROLE_UNSUPPORTED")
    ranges = source["ranges"]
    if (not isinstance(ranges, list) or len(ranges) != (2 if mode in PAIR_MODES else 1)
            or any(not isinstance(pair, list) or len(pair) != 2
                   or any(type(n) is not int or n < 1 for n in pair)
                   or pair[0] > pair[1] for pair in ranges)
            or len(ranges) == 2 and ranges[0][1] >= ranges[1][0]):
        raise ValueError("INTAKE_RANGES_INVALID_FOR_MODE")
    return source, supporting


def review_coverage(evidence, size):
    selections = evidence.get("selections")
    if selections:
        spans = [item["selected_span"] for item in selections]
    else:
        spans = [evidence["source"]["selected_span"]]
    covered = [{"start": span["start"], "end": span["end"], "kind": "SELECTED_SOURCE_REVIEW"}
               for span in spans]
    if selections and evidence["interval_effects"]["status"] == "INSPECTED":
        interval = evidence["intervening_span"]
        covered.insert(1, {"start": interval["start"], "end": interval["end"],
                           "kind": "BOUNDED_INTERVAL_INVENTORY"})
    result = []
    end = 0
    for span in covered:
        if end < span["start"]:
            result.append({"start": end, "end": span["start"], "kind": "UNINSPECTED"})
        if span["start"] < span["end"]:
            result.append(span)
        end = span["end"]
    if end < size:
        result.append({"start": end, "end": size, "kind": "UNINSPECTED"})
    return result


def build_review(intake):
    scope_bytes = secure_read(intake, "scope.json", 4096)
    legacy = sha256(scope_bytes).hexdigest() == SCOPE_SHA256
    scope = _parse_json(scope_bytes)
    if legacy:
        source_spec = {"path": scope["source"], "sha256": scope["sha256"], "ranges": scope["ranges"]}
        supporting, mode = [], "data-sort-sql"
    else:
        if isinstance(scope, dict) and "version" not in scope:
            raise ValueError("INTAKE_SCOPE_NOT_APPROVED")
        source_spec, supporting = validate_scope(scope)
        mode = scope["mode"]
    entries = [source_spec, *supporting]
    if enumerate_files(intake) != sorted(["scope.json", *(item["path"] for item in entries)]):
        raise ValueError("INTAKE_FILE_SET_MISMATCH")
    source = secure_read(intake, source_spec["path"], 65536)
    source_id = identity(source)
    if source_id["sha256"] != source_spec["sha256"]:
        raise ValueError("SOURCE_SHA256_MISMATCH")
    inputs = {"scope.json": identity(scope_bytes), source_spec["path"]: source_id}
    for item in supporting:
        info = identity(secure_read(intake, item["path"], 16384))
        if info["sha256"] != item["sha256"]:
            raise ValueError("SUPPORT_SHA256_MISMATCH")
        inputs[item["path"]] = {**info, "role": item["role"], "inspection": "IDENTITY_ONLY"}

    ranges = source_spec["ranges"]
    for pair in ranges:
        line_span(source, *pair)
    if mode in PAIR_MODES:
        evidence, readme = dependency_review(source, ranges, source_id["sha256"],
                                             recover_sql=mode == "data-sort-sql")
    else:
        evidence, readme = single_review(source, ranges[0], source_id["sha256"],
                                         recover_logistic=mode == "logistic")
        operation = evidence["declared_operation"]
        if operation and operation["kind"] != SINGLE_MODES[mode]:
            raise ValueError("INTAKE_OPERATION_MODE_MISMATCH")
    if not legacy:
        evidence.setdefault("reference_experiment", "NOT_RUN")
        evidence.setdefault("historical_source_run_provenance", "UNBOUND")
    files = {
        "README.md": readme,
        "EVIDENCE.json": json_bytes(evidence),
    }
    if mode in PAIR_MODES:
        files["MIGRATION_REVIEW.md"] = render(evidence)
    manifest = {
        **{key: evidence[key] for key in STATUS_FIELDS},
        "package_revision": "public-intake-review/1",
        "scope": scope["scope"],
        "inputs": inputs,
        "source_evidence": "EVIDENCE.json",
        "copilot_review": "NOT_TESTED",
        "files": {name: identity(data) for name, data in files.items()},
    }
    if not legacy:
        manifest.update(package_revision="public-intake-review/2", review_mode=mode,
                        review_status=evidence["review_status"],
                        coverage=review_coverage(evidence, len(source)))
    files["MANIFEST.json"] = json_bytes(manifest)
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--intake", required=True, type=Path, help="authorized public synthetic directory")
    parser.add_argument("--destination", required=True, help="fresh /tmp/sas-re-int1-<label> directory")
    args = parser.parse_args()
    try:
        require_evidence_io()
        scratch, leaf = scratch_destination(args.destination, "int1")
        destination = scratch / leaf
        if os.path.lexists(destination):
            raise FileExistsError
        intake = args.intake.absolute()
        ensure_disjoint(destination, [intake])
        files = build_review(intake)
        write_bundle(scratch, leaf, files, names=tuple(files))
    except FileExistsError:
        parser.exit(2, "BLOCKED: destination exists\n")
    except EvidenceError as error:
        parser.exit(2, f"{error.gate}: {error.code}\n")
    except ValueError as error:
        parser.exit(2, f"REFUSED: {error}\n")
    except OSError:
        parser.exit(2, "REFUSED: FILE_IO_REFUSED\n")
    print(json.dumps({"open": str(destination / "README.md"),
                      "manifest_sha256": sha256(files["MANIFEST.json"]).hexdigest()}))
    return 2 if json.loads(files["MANIFEST.json"]).get("review_status") == "BLOCKED" else 0


if __name__ == "__main__":
    sys.exit(main())
