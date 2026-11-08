"""Bind a replayed modernization proposal to an existing candidate publication."""

from argparse import Namespace
from pathlib import Path

from sas_re.safeio import _parse_json, secure_read

from migration_candidate import AUTHORITY
from review_copilot_notes import LIMIT
from review_intake import identity, json_bytes


def add_configuration_arguments(parser):
    parser.add_argument("--modernization-plan", type=Path)
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--tie-out", type=Path)


def load_configuration(args):
    paths = {
        "plan": getattr(args, "modernization_plan", None),
        "migration-profile.yaml": getattr(args, "profile", None),
        "tie-out.yaml": getattr(args, "tie_out", None),
    }
    if not any(paths.values()):
        return None
    if not all(paths.values()):
        raise ValueError("MODERNIZATION_CONFIGURATION_ARGUMENTS_REQUIRED")

    from plan_modernization import plan_review

    path = paths["plan"].absolute()
    raw = secure_read(path.parent, path.name, LIMIT)
    status, report = plan_review(Namespace(
        intake=getattr(args, "intake", None), package=args.package,
        profile=args.profile, tie_out=args.tie_out, emit_drafts=False,
    ))
    if status or report.get("decision") != "PLAN_PROPOSED":
        raise ValueError("MODERNIZATION_PLAN_REQUIRED")
    if json_bytes(report) != raw:
        raise ValueError("MODERNIZATION_PLAN_CHANGED")
    binding = {"plan": identity(raw), "configuration_inputs": report["configuration_inputs"]}
    verify_configuration_files(paths, binding)
    return binding, raw, report, paths


def verify_configuration_files(paths, binding):
    identities = {"plan": binding["plan"], **binding["configuration_inputs"]}
    for name, path in paths.items():
        path = path.absolute()
        if identity(secure_read(path.parent, path.name, LIMIT)) != identities[name]:
            raise ValueError("MODERNIZATION_CONFIGURATION_CHANGED")


def publication_metadata(configuration, files, manifest_sha256, candidate, *, input_count=None):
    if configuration is None:
        return {}
    binding, raw, report, paths = configuration
    if (report["input_manifest_sha256"] != manifest_sha256
            or report["candidate"] != candidate):
        raise ValueError("MODERNIZATION_SUBJECT_CHANGED")
    verify_configuration_files(paths, binding)
    checks = {"source_coverage": {"status": "REVIEWED", "sources": report["source_coverage"]}}
    validation = _parse_json(files["VALIDATION.json"])
    if candidate == "MIG-2":
        rows = _parse_json(files["ROWS.json"])
        checks.update(
            eligible_rows={"status": "OBSERVED", "count": len(rows)},
            multiplicity={"status": "OBSERVED", "input_count": input_count,
                          "output_count": len(rows)},
            candidate_gate={"status": "NOT_APPLICABLE"},
            ordering_and_output={"status": validation["comparison"], "artifact": "ROWS.json"},
        )
    else:
        runs = _parse_json(files["SCENARIO_RESULTS.json"])
        scenario = report["plan"]["scenario"]
        checks["population_and_gate"] = [
            {
                "scenario": run["scenario"],
                "eligible_count": len(run["handoff_ids"]) if "handoff_ids" in run else None,
                "eligible_ids": run.get("handoff_ids"),
                "candidate_gate": run["continuation"],
                "duplicate_groups": check["observed"].get("duplicate_groups"),
                "first_blocking_gate": check["observed"].get("first_blocking_gate"),
                "comparison": check["comparison"],
            }
            for run, check in zip(runs, validation["scenarios"])
            if scenario == "ALL_PINNED_MIG5_SCENARIOS" or run["scenario"] == scenario
        ]
        checks["ordering_and_output"] = {
            "status": (_parse_json(files["EXPORT_VALIDATION.json"])["downstream"]["comparison"]
                       if "EXPORT_VALIDATION.json" in files else "NOT_RUN"),
        }
    checks["csv_bytes"] = (
        {"status": "OBSERVED", "comparison": "UNAVAILABLE", **identity(files["PREPARED_EXPORT.csv"])}
        if "PREPARED_EXPORT.csv" in files else {"status": "NOT_RUN"}
    )
    scoring = files.get("SCORING_VALIDATION.json")
    if scoring:
        scoring = _parse_json(scoring)
        checks["fixed_scoring"] = {
            "status": scoring["comparison"], "artifact": "SCORING_VALIDATION.json",
            "probability_absolute_tolerance": scoring.get("probability_absolute_tolerance"),
        }
    else:
        checks["fixed_scoring"] = {"status": "NOT_RUN"}
    files["MODERNIZATION_PLAN.json"] = raw
    files["ENGINEERING_TIE_OUT.json"] = json_bytes({
        "basis": "PUBLIC_SYNTHETIC_ENGINEERING",
        "checks": checks,
        **AUTHORITY,
    })
    scripts = Path(__file__).resolve().parent
    return {
        "modernization": binding,
        "modernization_implementations": {
            name: identity(secure_read(scripts, name, LIMIT))
            for name in ("configured_continuation.py", "plan_modernization.py")
        },
    }
