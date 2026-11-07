"""Review an explicitly scoped public synthetic intake directory."""

import argparse
from contextlib import suppress
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
from migration_review import anchor, location, render
from mvp1_demo import scratch_destination, write_bundle
from review_source import dependency_review, inspect_range, line_span, single_review


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
SUPPORT_SUFFIXES = {
    "note": (".txt", ".md"),
    "log": (".log",),
    "listing": (".lst",),
    "configuration": (".cfg", ".ini", ".json", ".yaml", ".yml", ".toml"),
}
SOURCE_SUFFIXES = (".sas", ".sas.txt")


def validate_scope(scope):
    if not isinstance(scope, dict):
        raise ValueError("INTAKE_MANIFEST_INVALID")
    version = scope.get("version")
    if type(version) is not int or version not in (1, 2):
        raise ValueError("INTAKE_MANIFEST_VERSION_UNSUPPORTED")
    required = {"version", "scope", "sources"}
    if version == 1:
        required.add("mode")
    if not required <= scope.keys() or scope.keys() - required - {"supporting"}:
        raise ValueError("INTAKE_MANIFEST_INVALID")
    if scope["scope"] != "public-synthetic":
        raise ValueError("INTAKE_PUBLIC_SYNTHETIC_SCOPE_REQUIRED")
    sources = scope["sources"]
    if not isinstance(sources, list):
        raise ValueError("INTAKE_MANIFEST_INVALID")
    if version == 1 and len(sources) > 1:
        raise ValueError("INTAKE_MULTIPLE_SOURCES_UNSUPPORTED")
    if version == 2 and len(sources) != 2:
        raise ValueError("INTAKE_TWO_SOURCES_REQUIRED")
    if not sources:
        raise ValueError("INTAKE_MANIFEST_INVALID")
    source_keys = {"path", "sha256", "ranges"} | ({"mode"} if version == 2 else set())
    if any(not isinstance(source, dict) or set(source) != source_keys for source in sources):
        raise ValueError("INTAKE_MANIFEST_INVALID")
    sources = [{**source, "mode": scope["mode"]} for source in sources] if version == 1 else sources
    supporting = scope.get("supporting", [])
    if (not isinstance(supporting, list) or len(supporting) > 4
            or any(not isinstance(item, dict) or set(item) != {"path", "sha256", "role"}
                   for item in supporting)):
        raise ValueError("INTAKE_MANIFEST_INVALID")
    names = {"scope.json"}
    for item in [*sources, *supporting]:
        name = safe_relative(item["path"])
        if "/" in name or name.lower() in names:
            raise ValueError("INTAKE_FILE_NAME_UNSUPPORTED")
        names.add(name.lower())
        digest = item["sha256"]
        if not isinstance(digest, str) or not re.fullmatch("[0-9a-f]{64}", digest):
            raise ValueError("INTAKE_SHA256_INVALID")
    for source in sources:
        validate_source(source)
    for item in supporting:
        name = item["path"].lower()
        if name.endswith(SOURCE_SUFFIXES):
            raise ValueError("INTAKE_MULTIPLE_SOURCES_UNSUPPORTED")
        role = item["role"]
        if not isinstance(role, str) or not name.endswith(SUPPORT_SUFFIXES.get(role, ())):
            raise ValueError("INTAKE_SUPPORT_ROLE_UNSUPPORTED")
    return sources, supporting


def validate_source(source):
    if not source["path"].lower().endswith(SOURCE_SUFFIXES):
        raise ValueError("INTAKE_SOURCE_TYPE_UNSUPPORTED")
    mode = source["mode"]
    if not isinstance(mode, str) or mode not in SINGLE_MODES.keys() | PAIR_MODES:
        raise ValueError("INTAKE_REVIEW_MODE_UNSUPPORTED")
    ranges = source["ranges"]
    if (not isinstance(ranges, list) or len(ranges) != (2 if mode in PAIR_MODES else 1)
            or any(not isinstance(pair, list) or len(pair) != 2
                   or any(type(n) is not int or n < 1 for n in pair)
                   or pair[0] > pair[1] for pair in ranges)
            or len(ranges) == 2 and ranges[0][1] >= ranges[1][0]):
        raise ValueError("INTAKE_RANGES_INVALID_FOR_MODE")


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


def analyze_source(source, source_spec, *, dependency_anchors=False):
    ranges = source_spec["ranges"]
    mode = source_spec["mode"]
    digest = source_spec["sha256"]
    if mode in PAIR_MODES:
        evidence, readme = dependency_review(source, ranges, digest,
                                             recover_sql=mode == "data-sort-sql")
    else:
        evidence, readme = single_review(source, ranges[0], digest,
                                         recover_logistic=mode == "logistic",
                                         dependency_anchors=dependency_anchors)
        operation = evidence["declared_operation"]
        if operation and operation["kind"] != SINGLE_MODES[mode]:
            raise ValueError("INTAKE_OPERATION_MODE_MISMATCH")
    evidence.setdefault("reference_experiment", "NOT_RUN")
    evidence.setdefault("historical_source_run_provenance", "UNBOUND")
    return evidence, readme


def declared_accesses(evidence):
    """Read existing selected-operation facts with their original citations."""
    selections = evidence.get("selections", [evidence])
    for selection in selections:
        op = selection["declared_operation"]
        if not op:
            continue
        if op["kind"] == "DATA_STEP":
            spans = op["declaration_spans"]
            yield "read", op["input"], spans["input"]
            yield "write", op["output"], spans["output"]
        elif op["kind"] == "PROC_LOGISTIC":
            yield "read", op["input"], op["header"]["span"]
            yield "write", op["output"], op["score_columns"]["span"]
            for dataset in op["ods_output"]["datasets"].values():
                yield "write", dataset, op["ods_output"]["span"]
        else:  # Bounded PROC SORT uses one span for its input and output.
            yield "read", op["input"], op["span"]
            yield "write", op["output"], op["span"]


def two_source_review(sources, source_bytes, inputs, scope_name):
    files, reviews, accesses = {}, [], []
    lines = ["# Public synthetic two-source intake review", "",
             "See [MANIFEST.json](MANIFEST.json) for input identities and per-source coverage.", "",
             "## Source reviews", ""]
    for index, spec in enumerate(sorted(sources, key=lambda entry: entry["path"]), 1):
        path = spec["path"]
        evidence, readme = analyze_source(source_bytes[path], spec, dependency_anchors=True)
        json_name, review_name = f"SOURCE_{index}.json", f"SOURCE_{index}.md"
        report = render(evidence) if spec["mode"] in PAIR_MODES else readme
        files[json_name] = json_bytes(evidence)
        files[review_name] = report.replace(b"](EVIDENCE.json)", f"]({json_name})".encode(), 1)
        reviews.append({
            "path": path, "evidence": json_name, "review": review_name,
            "review_mode": spec["mode"], "review_status": evidence["review_status"],
            "coverage": review_coverage(evidence, len(source_bytes[path])),
        })
        lines.append(f"- `{path}` · [{evidence['review_status']} review]({review_name}) · "
                     f"[source evidence]({json_name}).")
        accesses.extend((path, review_name, kind, dataset, span)
                        for kind, dataset, span in declared_accesses(evidence))

    lines.extend(["", "## Cross-file MAP", ""])
    dependencies = []
    for path, review, kind, dataset, span in accesses:
        if kind != "write":
            continue
        for other, other_review, other_kind, other_dataset, other_span in accesses:
            if other == path or other_kind != "read" or other_dataset != dataset:
                continue
            writer, reader = anchor(span), anchor(other_span)
            dependencies.append({
                "dataset": dataset, "classification": "POTENTIAL",
                "basis": "MATCHING_SOURCE_DECLARED_DATASET_ACCESSES",
                "execution_order": "UNRESOLVED", "dataset_version": "UNRESOLVED",
                "writer": {"path": path, "anchor": writer},
                "reader": {"path": other, "anchor": reader},
            })
            lines.append(f"- **POTENTIAL** · `{dataset}` · declared write in "
                         f"[`{path}` {location(span)}]({review}#{writer}) → declared read in "
                         f"[`{other}` {location(other_span)}]({other_review}#{reader}).")
    if not dependencies:
        lines.append("- **UNRESOLVED** · No matching selected writer and reader was recovered.")
    lines.extend([
        "", "Cross-file execution order, runtime dataset identity and lineage remain unresolved.",
        "This MAP compares selected operation declarations. Uninspected bytes, interval effects and "
        "include or macro expansion may contain other dependencies.",
        "", "## Draft requirements and validation obligations", "",
        "- Retain each source's separate identity and follow the linked review for its selected "
        "requirements, unresolved syntax and behavioral checks.",
        "- For each potential handoff, establish the producer invocation and the dataset version "
        "read by the consumer using attributable execution evidence. Verify schema, keys, "
        "row values and multiplicity at the boundary.",
        "- Confirm any required ordering and gate outcomes before planning a combined workflow.",
    ])
    files["README.md"] = ("\n".join(lines) + "\n").encode("utf-8")
    manifest = {
        **{key: evidence[key] for key in STATUS_FIELDS},
        "package_revision": "public-intake-review/3",
        "scope": scope_name, "inputs": inputs, "sources": reviews,
        "review_status": "BLOCKED" if any(r["review_status"] == "BLOCKED" for r in reviews) else "PARTIAL",
        "cross_file_dependencies": dependencies,
        "cross_file_resolution": "POTENTIAL" if dependencies else "UNRESOLVED",
        "copilot_review": "NOT_TESTED",
        "files": {name: identity(data) for name, data in files.items()},
    }
    files["MANIFEST.json"] = json_bytes(manifest)
    return files


def inventory_intake(intake):
    """Propose a scope from whole-file recognitions without authorizing it."""
    inventory, sources, supporting, blockers = [], [], [], []
    for name in enumerate_files(intake):
        lower = name.lower()
        is_source = lower.endswith(SOURCE_SUFFIXES)
        role = next((role for role, suffixes in SUPPORT_SUFFIXES.items()
                     if lower.endswith(suffixes)), None)
        entry = {"path": name, "inspection": "NAME_ONLY"}
        inventory.append(entry)
        if lower == "scope.json" or "/" in name or not (is_source or role):
            blockers.append({"path": name, "code": "EXISTING_SCOPE" if lower == "scope.json"
                             else "INTAKE_FILE_REQUIRES_MANUAL_SCOPING"})
            continue
        try:
            raw = secure_read(intake, name, 65536 if is_source else 16384)
        except EvidenceError as error:
            if error.code != "FILE_SIZE_LIMIT":
                raise
            blockers.append({"path": name, "code": error.code})
            continue
        entry.update(identity(raw), inspection="IDENTITY_ONLY")
        if not is_source:
            entry["role"] = role
            supporting.append({"path": name, "sha256": entry["sha256"], "role": role})
            continue

        lines = len(re.findall(rb"[^\r\n]*(?:\r\n|\r|\n)|[^\r\n]+$", raw))
        if not lines:
            blockers.append({"path": name, "code": "EMPTY_SOURCE"})
            continue
        _, operation, reasons = inspect_range(raw, 1, lines)
        if not operation:
            _, operation, logistic_reasons = inspect_range(raw, 1, lines, recover_logistic=True)
            if not operation:
                reasons = sorted(set(reasons + logistic_reasons))
        entry.update(inspection="WHOLE_SOURCE_PROBE", reason_codes=reasons)
        if not operation:
            entry["syntax_recognition"] = "UNSUPPORTED"
            blockers.append({"path": name, "code": "INTAKE_SOURCE_REQUIRES_MANUAL_SCOPING"})
            continue
        entry["syntax_recognition"] = "PARTIAL" if operation.get("unsupported_statements") else "SUPPORTED"
        mode = next(mode for mode, kind in SINGLE_MODES.items() if kind == operation["kind"])
        sources.append({"path": name, "sha256": entry["sha256"], "ranges": [[1, lines]], "mode": mode})

    proposal = None
    if not blockers:
        proposal = {"version": 1 if len(sources) == 1 else 2, "scope": "public-synthetic",
                    "sources": sources, "supporting": supporting}
        if len(sources) == 1:
            proposal["mode"] = sources[0].pop("mode")
        try:
            validate_scope(proposal)
        except ValueError as error:
            blockers.append({"code": str(error)})
            proposal = None
    return {"inventory": inventory, "proposed_scope": proposal, "blockers": blockers,
            "reference_experiment": "NOT_RUN", "semantic_verification": "UNVERIFIABLE",
            "semantic_acceptance": "BLOCKED"}


def build_review(intake):
    scope_bytes = secure_read(intake, "scope.json", 4096)
    legacy = sha256(scope_bytes).hexdigest() == SCOPE_SHA256
    scope = _parse_json(scope_bytes)
    if legacy:
        sources = [{"path": scope["source"], "sha256": scope["sha256"],
                    "ranges": scope["ranges"], "mode": "data-sort-sql"}]
        supporting = []
    else:
        if isinstance(scope, dict) and "version" not in scope:
            raise ValueError("INTAKE_SCOPE_NOT_APPROVED")
        sources, supporting = validate_scope(scope)
    entries = [*sources, *supporting]
    if enumerate_files(intake) != sorted(["scope.json", *(item["path"] for item in entries)]):
        raise ValueError("INTAKE_FILE_SET_MISMATCH")
    inputs = {"scope.json": identity(scope_bytes)}
    source_bytes = {}
    for spec in sources:
        name = spec["path"]
        raw = secure_read(intake, name, 65536)
        inputs[name] = identity(raw)
        if inputs[name]["sha256"] != spec["sha256"]:
            raise ValueError("SOURCE_SHA256_MISMATCH")
        source_bytes[name] = raw
    for item in supporting:
        info = identity(secure_read(intake, item["path"], 16384))
        if info["sha256"] != item["sha256"]:
            raise ValueError("SUPPORT_SHA256_MISMATCH")
        inputs[item["path"]] = {**info, "role": item["role"], "inspection": "IDENTITY_ONLY"}
    for spec in sources:
        for pair in spec["ranges"]:
            line_span(source_bytes[spec["path"]], *pair)

    if len(sources) == 2:
        return two_source_review(sources, source_bytes, inputs, scope["scope"])

    source_spec, = sources
    source = source_bytes[source_spec["path"]]
    mode = source_spec["mode"]
    evidence, readme = analyze_source(source, source_spec)
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


def modernization_drafts(files):
    """Create review inputs bound to the existing evidence package."""
    manifest = _parse_json(files["MANIFEST.json"])
    binding = {
        "manifest_sha256": identity(files["MANIFEST.json"])["sha256"],
        "inputs": manifest["inputs"],
        "evidence": {name: digest for name, digest in manifest["files"].items()
                     if name.endswith(".json")},
    }
    common = {"version": 1, "status": "DRAFT", "binding": binding,
              "source_review_status": manifest.get("review_status", "PARTIAL")}
    profile = {
        **common,
        "target": {"runtime": "PENDING", "distributed": "PENDING"},
        "execution": {"multiplicity_policy": "PENDING", "ordering_policy": "PENDING",
                      "category_policy": "PENDING"},
        "approval": {"architecture": "REQUIRED", "business_intent": "REQUIRED"},
    }
    tie_out = {
        **common,
        "checks": {
            "source_coverage": "REVIEW_REQUIRED",
            "population_and_multiplicity": "PENDING",
            "ordering_and_output": "PENDING",
            "numeric_tolerance": "PENDING",
        },
        "reference": {
            "sas_execution": manifest["reference_experiment"],
            "semantic_verification": manifest["semantic_verification"],
            "semantic_acceptance": manifest["semantic_acceptance"],
        },
    }
    handoff = f"""# INTAKE modernization review

Review manifest SHA-256 `{binding['manifest_sha256']}`.
Start with [source review and TRACE/MAP links](README.md) and verify the
input identities and coverage in [MANIFEST.json](MANIFEST.json).

Review [migration-profile.yaml](migration-profile.yaml) and
[tie-out.yaml](tie-out.yaml) with the operator. Resolve pending decisions
against this subject's evidence.

| Skill | Draft to produce |
| --- | --- |
| sas-reconstruct | Cite selected source spans and record unsupported or uninspected constructs. |
| sas-specify | Derive draft requirements and list open business decisions. |
| sas-analyze | Trace declared dependencies and label potential handoffs and unresolved execution order. |
| sas-validate | Define public engineering checks and separate SAS reference obligations. |
| sas-architect | Compare applicable architecture options and record candidate fit and limitations. |

Save the five deliverables outside this package. Follow the INTG-1 operator
guide for the GATE-1 claim record and separate byte-bound human approval.
The YAML files are review drafts. The existing continuation checks candidate
eligibility against the declared source and the reviewed evidence.
"""
    # JSON is a YAML 1.2 subset and keeps serialization deterministic.
    return {
        "MIGRATION_PROFILE.json": json_bytes(profile),
        "TIE_OUT.json": json_bytes(tie_out),
        "MODERNIZATION_REVIEW.md": handoff.encode("utf-8"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--intake", required=True, type=Path, help="authorized public synthetic directory")
    output = parser.add_mutually_exclusive_group(required=True)
    output.add_argument("--destination", help="fresh /tmp/sas-re-int1-<label> directory")
    output.add_argument("--inventory", action="store_true", help="print a draft inventory and scope proposal")
    parser.add_argument("--modernization-drafts", action="store_true",
                        help="include draft configuration and a five-skill review handoff")
    args = parser.parse_args()
    if args.inventory and args.modernization_drafts:
        parser.error("--modernization-drafts requires --destination")
    try:
        require_evidence_io()
        if args.inventory:
            print(json_bytes(inventory_intake(args.intake.absolute())).decode("utf-8"), end="")
            return 0
        scratch, leaf = scratch_destination(args.destination, "int1")
        destination = scratch / leaf
        if os.path.lexists(destination):
            raise FileExistsError
        intake = args.intake.absolute()
        ensure_disjoint(destination, [intake])
        files = build_review(intake)
        if args.modernization_drafts:
            files.update(modernization_drafts(files))
        write_bundle(scratch, leaf, files, names=tuple(files))
        if args.modernization_drafts:
            # The existing writer creates a fresh, private directory and accepts JSON.
            # Give the JSON-compatible YAML drafts their public filenames there.
            names = {"MIGRATION_PROFILE.json": "migration-profile.yaml",
                     "TIE_OUT.json": "tie-out.yaml"}
            try:
                directory = os.open(destination, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
                try:
                    for old, new in names.items():
                        os.rename(old, new, src_dir_fd=directory, dst_dir_fd=directory)
                finally:
                    os.close(directory)
            except OSError:
                for name in (*files, *names.values()):
                    with suppress(OSError):
                        (destination / name).unlink()
                with suppress(OSError):
                    destination.rmdir()
                raise
    except FileExistsError:
        parser.exit(2, "BLOCKED: destination exists\n")
    except EvidenceError as error:
        parser.exit(2, f"{error.gate}: {error.code}\n")
    except ValueError as error:
        parser.exit(2, f"REFUSED: {error}\n")
    except OSError:
        parser.exit(2, "REFUSED: FILE_IO_REFUSED\n")
    entry = "MODERNIZATION_REVIEW.md" if args.modernization_drafts else "README.md"
    print(json.dumps({"open": str(destination / entry),
                      "manifest_sha256": sha256(files["MANIFEST.json"]).hexdigest()}))
    return 2 if json.loads(files["MANIFEST.json"]).get("review_status") == "BLOCKED" else 0


if __name__ == "__main__":
    sys.exit(main())
