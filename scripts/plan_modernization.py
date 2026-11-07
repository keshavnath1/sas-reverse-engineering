"""Check reviewed INTAKE configuration and report a proposed plan without running a candidate."""

import argparse
import json
from pathlib import Path
import sys

from sas_re.platform_io import require_evidence_io
from sas_re.safeio import EvidenceError, _parse_json, secure_read

sys.path.insert(0, str(Path(__file__).resolve().parent))
from migrate_projection_sort import load_plan
from migration_candidate import AUTHORITY
from review_copilot_notes import LIMIT
from review_intake import build_review, identity, json_bytes, modernization_drafts
from review_mig5 import DOWNSTREAM_REVISION, REVISION, load_subject


DRAFT_NAMES = {
    "migration-profile.yaml": "MIGRATION_PROFILE.json",
    "tie-out.yaml": "TIE_OUT.json",
}


def verified_subject(package, intake):
    raw_manifest = secure_read(package, "MANIFEST.json", LIMIT)
    manifest = _parse_json(raw_manifest)
    if not isinstance(manifest, dict):
        raise ValueError("REVIEW_PACKAGE_UNSUPPORTED")
    revision = manifest.get("package_revision")
    if revision in (REVISION, DOWNSTREAM_REVISION):
        if intake is not None:
            raise ValueError("PINNED_SUBJECT_REQUIRES_ITS_OWN_INPUTS")
        return load_subject(package, identity(raw_manifest)["sha256"])

    if intake is None:
        raise ValueError("INTAKE_REQUIRED")
    files = build_review(intake)
    for name, raw in files.items():
        if secure_read(package, name, LIMIT) != raw:
            raise ValueError("MIGRATION_EVIDENCE_MISMATCH")
    return _parse_json(files["MANIFEST.json"]), files


def candidate_plan(manifest, intake, package, manifest_sha256):
    revision = manifest["package_revision"]
    if revision in (REVISION, DOWNSTREAM_REVISION):
        downstream = revision == DOWNSTREAM_REVISION
        return {
            "candidate": "MIG-5/MIG-6/MOD-2" if downstream else "MIG-5",
            "scenario": manifest["scenario"],
            "sources": manifest["sources"],
            "continuation": "scripts/review_mig5.py",
        }
    plan = load_plan(intake, package)
    if plan["input_manifest_sha256"] != manifest_sha256:
        raise ValueError("MIGRATION_EVIDENCE_MISMATCH")
    return {"candidate": "MIG-2", "continuation": "scripts/review_to_migration.py", **plan}


def required_choices(candidate):
    downstream = candidate == "MIG-5/MIG-6/MOD-2"
    if candidate == "MIG-2":
        ordering = "ASCENDING_KEY_STABLE_TIES"
    elif downstream:
        ordering = "EXPORT_ASCENDING_ID_SCORE_ORIGINAL_PRE_SORT"
    else:
        ordering = "ORIGINAL_INPUT_ORDER"
    return {
        "migration-profile.yaml": {
            "target": {"runtime": "python", "distributed": False},
            "execution": {"multiplicity_policy": "PRESERVE",
                          "ordering_policy": ordering,
                          "category_policy": "PINNED_MOD2_MAPPING" if downstream else "NOT_APPLICABLE"},
        },
        "tie-out.yaml": {
            "checks": {"source_coverage": "REVIEWED",
                       "population_and_multiplicity": "EXACT",
                       "ordering_and_output": "EXACT",
                       "numeric_tolerance": "PINNED_MOD2_TOLERANCE" if downstream else "EXACT"},
        },
    }


def check_configuration(name, config, draft, choices, pending, refusals):
    normalized = dict(config)
    normalized["status"] = "DRAFT"
    if config.get("status") == "DRAFT":
        pending.append(f"{name}:status")
    elif config.get("status") != "REVIEWED":
        refusals.append({"field": f"{name}:status", "code": "CONFIGURATION_STATUS_UNSUPPORTED"})

    for section, fields in choices.items():
        actual = config.get(section)
        if not isinstance(actual, dict):
            raise ValueError("CONFIGURATION_INVALID")
        normalized[section] = dict(actual)
        for field, supported in fields.items():
            if field not in actual:
                raise ValueError("CONFIGURATION_INVALID")
            value = actual[field]
            label = f"{name}:{section}.{field}"
            if value == draft[section][field]:
                pending.append(label)
            elif json_bytes(value) != json_bytes(supported):
                refusals.append({"field": label, "code": "CONFIGURATION_POLICY_UNSUPPORTED"})
            normalized[section][field] = draft[section][field]
    if json_bytes(normalized) != json_bytes(draft):
        raise ValueError("CONFIGURATION_CONTRACT_MISMATCH")


def plan_review(args):
    require_evidence_io()
    package = args.package.absolute()
    intake = args.intake.absolute() if args.intake else None
    manifest, files = verified_subject(package, intake)
    manifest_sha256 = identity(files["MANIFEST.json"])["sha256"]
    generated = modernization_drafts(files)
    drafts = {name: _parse_json(generated[internal]) for name, internal in DRAFT_NAMES.items()}
    if args.emit_drafts:
        return 0, drafts

    evidence_names = drafts["migration-profile.yaml"]["binding"]["evidence"]
    report = {
        **AUTHORITY,
        "input_manifest_sha256": manifest_sha256,
        "source_review_status": manifest.get("review_status", "PARTIAL"),
        "source_coverage": manifest.get("sources", manifest.get("coverage", [])),
        "source_backed_declarations": sorted(evidence_names),
        "source_diagnostics": {
            name: {key: evidence[key] for key in ("syntax_recognition", "reason_codes")
                   if key in evidence}
            for name in evidence_names
            if (name.startswith("SOURCE_") or name.endswith("EVIDENCE.json"))
            and (evidence := _parse_json(files[name]))
        },
        "unresolved_obligations": [
            "SAS execution order and runtime dataset identity",
            "Independent SAS reference comparison",
            "GATE-1 claim record, exact-byte human approval, and candidate input validation",
        ],
        "dependencies": manifest.get("cross_file_dependencies", []),
        "existing_pinned_route": "MIG-5/MIG-6/MOD-2 requires a verified INTG-3 subject",
    }
    configs, identities = {}, {}
    for name, path in (("migration-profile.yaml", args.profile), ("tie-out.yaml", args.tie_out)):
        path = path.absolute() if path else package / name
        raw = secure_read(path.parent, path.name, LIMIT)
        configs[name] = _parse_json(raw)
        identities[name] = identity(raw)
        if (not isinstance(configs[name], dict)
                or json_bytes(configs[name].get("binding")) != json_bytes(drafts[name]["binding"])):
            raise ValueError("CONFIGURATION_BINDING_MISMATCH")
    report["configuration_inputs"] = identities

    try:
        proposed = candidate_plan(manifest, intake, package, manifest_sha256)
    except ValueError as error:
        return 2, {**report, "decision": "REFUSED", "reason": str(error)}

    choices = required_choices(proposed["candidate"])
    pending, refusals = [], []
    for name, config in configs.items():
        check_configuration(name, config, drafts[name], choices[name], pending, refusals)
    report.update(candidate=proposed["candidate"], pending=pending, refusals=refusals,
                  supported_operator_policy=choices)
    if refusals:
        return 2, {**report, "decision": "REFUSED"}
    if pending:
        return 1, {**report, "decision": "REVIEW_REQUIRED"}
    return 0, {**report, "decision": "PLAN_PROPOSED", "plan": proposed,
               "operator_policy": {name: {section: configs[name][section] for section in sections}
                                   for name, sections in choices.items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--intake", type=Path, help="required for an INTAKE review package")
    parser.add_argument("--package", required=True, type=Path, help="verified INTAKE or pinned INTG-3 subject")
    parser.add_argument("--profile", type=Path, help="defaults to the package migration-profile.yaml")
    parser.add_argument("--tie-out", type=Path, help="defaults to the package tie-out.yaml")
    parser.add_argument("--emit-drafts", action="store_true", help="print the two draft documents as a JSON mapping")
    args = parser.parse_args()
    if args.emit_drafts and (args.profile or args.tie_out):
        parser.error("--emit-drafts cannot be combined with reviewed configuration paths")
    try:
        status, report = plan_review(args)
    except EvidenceError as error:
        status, report = 2, {**AUTHORITY, "decision": "REFUSED", "reason": error.code}
    except ValueError as error:
        status, report = 2, {**AUTHORITY, "decision": "REFUSED", "reason": str(error)}
    except (OSError, TypeError, KeyError, AttributeError, IndexError):
        status, report = 2, {**AUTHORITY, "decision": "REFUSED", "reason": "PLANNING_INPUT_REFUSED"}
    print(json.dumps(report, indent=2, sort_keys=True))
    return status


if __name__ == "__main__":
    sys.exit(main())
