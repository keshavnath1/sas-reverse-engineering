"""Prepare or continue the pinned public MIG-5 operator review."""

import argparse
from pathlib import Path
import sys

from sas_re.platform_io import require_evidence_io
from sas_re.safeio import EvidenceError, _parse_json, ensure_disjoint, secure_read

sys.path.insert(0, str(Path(__file__).resolve().parent))
from configured_continuation import (add_configuration_arguments, load_configuration,
                                     publication_metadata)
from migrate_preparation_gates import EVIDENCE_PINS, LIMIT, PINS, ROOT, build_package
from migrate_sort_export import SCENARIOS
from migration_candidate import AUTHORITY
from mvp1_demo import scratch_destination, write_bundle
from review_intake import identity, json_bytes
from review_source import dependency_review, single_review


REVISION = "public-mig5-review/1"
DOWNSTREAM_REVISION = "public-mig5-downstream-review/1"
MODEL = "MODEL_EVIDENCE.json"
MODEL_SOURCE = "tests/fixtures/candidate-execution/fixed-logistic-scoring/model.sas.txt"
MODEL_SHA256 = "0f6741a10b6fc29de02fdd9a4500c95f2cc948814d109c1643cfd893a7e58a4c"
BRANCH_RUNNERS = ("scripts/migrate_sort_export.py", "scripts/score_prepared_logistic.py",
                  "scripts/mvp1_demo.py")
PREPARATION = "PREPARATION_EVIDENCE.json"
POPULATION = "POPULATION_EVIDENCE.json"


def build_subject(scenario=None):
    inputs = {}
    source_bytes = {}
    for name, pin in PINS.items():
        path = ROOT / name
        raw = secure_read(path.parent, path.name, LIMIT)
        inputs[name] = identity(raw)
        if inputs[name]["sha256"] != pin:
            raise ValueError("MIGRATION_PINNED_INPUT_MISMATCH")
        if name.endswith(".sas.txt"):
            source_bytes[name] = raw
    runner = ROOT / "scripts/migrate_preparation_gates.py"
    inputs["scripts/migrate_preparation_gates.py"] = identity(secure_read(runner.parent, runner.name, LIMIT))
    prep = "tests/fixtures/candidate-execution/preparation-rules/preparation.sas.txt"
    pop = "tests/fixtures/candidate-execution/population-gates/population.sas.txt"
    prep_evidence, prep_report = single_review(
        source_bytes[prep], (1, 12), PINS[prep], recover_rules=True, recover_missing=True)
    pop_evidence, pop_report = dependency_review(
        source_bytes[pop], [(1, 1), (14, 14)], PINS[pop], recover_sql=True)
    files = {
        PREPARATION: json_bytes(prep_evidence), POPULATION: json_bytes(pop_evidence),
        "PREPARATION.md": prep_report, "POPULATION.md": pop_report,
    }
    if tuple(identity(files[name])["sha256"] for name in (PREPARATION, POPULATION)) != EVIDENCE_PINS:
        raise ValueError("MIGRATION_EVIDENCE_MISMATCH")
    manifest = {
        "package_revision": REVISION,
        "scope": "public-synthetic",
        "candidate_scope": "PINNED_MIG5_PREPARATION_AND_POPULATION_GATES",
        "scenario": "ALL_PINNED_MIG5_SCENARIOS",
        "sas_dataset_continuity": "UNESTABLISHED",
        "inputs": inputs,
        "sources": [{"path": prep, "evidence": PREPARATION}, {"path": pop, "evidence": POPULATION}],
        **AUTHORITY,
    }
    if scenario is not None:
        add_downstream_subject(files, manifest, scenario)
    manifest["files"] = {name: identity(raw) for name, raw in files.items()}
    files["MANIFEST.json"] = json_bytes(manifest)
    return files


def read_input(name):
    path = ROOT / name
    return secure_read(path.parent, path.name, LIMIT)


def add_downstream_subject(files, manifest, scenario):
    from score_prepared_logistic import load_model_fixtures, recover_model

    if scenario not in SCENARIOS:
        raise ValueError("MIGRATION_SCENARIO_UNSUPPORTED")
    source = read_input(MODEL_SOURCE)
    model_evidence, _ = recover_model(source, MODEL_SHA256)
    fixtures = load_model_fixtures()
    files.update(fixtures)
    files[MODEL] = json_bytes(model_evidence)
    manifest["inputs"][MODEL_SOURCE] = identity(source)
    manifest["inputs"].update({f"tests/fixtures/candidate-execution/fixed-logistic-scoring/{name}": identity(raw)
                               for name, raw in fixtures.items()})
    manifest["inputs"].update({name: identity(read_input(name)) for name in BRANCH_RUNNERS})
    manifest["sources"].append({"path": MODEL_SOURCE, "evidence": MODEL})
    manifest.update(package_revision=DOWNSTREAM_REVISION, scenario=scenario,
                    candidate_scope="PINNED_MIG5_MIG6_MOD2",
                    sas_export_execution="UNOBSERVED", sas_scoring_equivalence="UNVERIFIED")


def run_downstream(upstream, subject):
    from migrate_sort_export import build_export_from_upstream
    from score_prepared_logistic import build_scoring_from_upstream

    scenario = subject["scenario"]
    selected = next(row for row in _parse_json(upstream["SCENARIO_RESULTS.json"])
                    if row["scenario"] == scenario)
    if selected["continuation"] != "PROCEED":
        return {}, True
    export, export_pass = build_export_from_upstream(upstream, scenario)
    scoring, scoring_pass = build_scoring_from_upstream(
        ROOT / MODEL_SOURCE, MODEL_SHA256, upstream, scenario)
    inputs = subject["inputs"]
    export_manifest = _parse_json(export["MANIFEST.json"])
    score_manifest = _parse_json(scoring["MANIFEST.json"])
    upstream_identity = identity(upstream["MANIFEST.json"])
    if (any(manifest["upstream_manifest"] != upstream_identity or manifest["scenario"] != scenario
            for manifest in (export_manifest, score_manifest))
            or any(export_manifest["runner"][name] != inputs[name]
                   for name in ("scripts/migrate_sort_export.py", "scripts/mvp1_demo.py"))
            or score_manifest["runner"] != inputs["scripts/score_prepared_logistic.py"]
            or score_manifest["source_review"] != subject["files"][MODEL]
            or any(score_manifest["source"][key] != inputs[MODEL_SOURCE][key]
                   for key in ("sha256", "bytes"))
            or any(score_manifest["fixtures"][name] != inputs[f"tests/fixtures/candidate-execution/fixed-logistic-scoring/{name}"]
                   for name in ("MAPPING.json", "COEFFICIENTS.json"))):
        raise ValueError("MIGRATION_APPROVED_INPUTS_CHANGED")
    files = {name: export[name] for name in ("SORTED_ROWS.json", "PREPARED_EXPORT.csv")}
    files.update({name: scoring[name] for name in ("DESIGN.json", "SCORES.json")})
    for prefix, branch in (("EXPORT", export), ("SCORING", scoring)):
        for name in ("PLAN.json", "VALIDATION.json"):
            files[f"{prefix}_{name}"] = branch[name]
    return files, export_pass and scoring_pass


def load_subject(package, manifest_sha256):
    supplied = secure_read(package, "MANIFEST.json", LIMIT)
    if identity(supplied)["sha256"] != manifest_sha256:
        raise ValueError("REVIEW_MANIFEST_SHA256_MISMATCH")
    candidate = _parse_json(supplied)
    downstream = candidate.get("package_revision") == DOWNSTREAM_REVISION
    files = build_subject(candidate["scenario"] if downstream else None)
    manifest = files["MANIFEST.json"]
    if identity(manifest)["sha256"] != manifest_sha256:
        raise ValueError("REVIEW_MANIFEST_SHA256_MISMATCH")
    for name, raw in files.items():
        if secure_read(package, name, LIMIT) != raw:
            raise ValueError("REVIEW_PACKAGE_PAYLOAD_MISMATCH")
    return _parse_json(manifest), files


def continue_mig5(args, scratch, leaf):
    from review_claim_gate import review_claims

    package = args.package.absolute()
    ensure_disjoint(scratch / leaf, [package])
    record = args.record.absolute()
    approval = args.approval.absolute() if args.approval else None
    configuration = load_configuration(args)
    raw_record = secure_read(record.parent, record.name, LIMIT)
    raw_approval = secure_read(approval.parent, approval.name, LIMIT) if approval else None
    gate = review_claims(package, raw_record, _parse_json(raw_approval) if approval else None,
                         configuration=configuration[0] if configuration else None)
    if gate["decision"] != "PASS":
        return (1 if gate["decision"] == "REVIEW_REQUIRED" else 2), gate
    try:
        subject, _ = load_subject(package, gate["manifest_sha256"])
        if (secure_read(record.parent, record.name, LIMIT) != raw_record
                or secure_read(approval.parent, approval.name, LIMIT) != raw_approval):
            raise ValueError("APPROVED_REVIEW_CHANGED")
        if configuration and configuration[2]["input_manifest_sha256"] != gate["manifest_sha256"]:
            raise ValueError("MODERNIZATION_SUBJECT_CHANGED")
        files, passed = build_package(package / PREPARATION, package / POPULATION)
        candidate_manifest = files["MANIFEST.json"]
        candidate = _parse_json(candidate_manifest)
        actual = {**candidate["inputs"], **candidate["runner"]}
        if any(subject["inputs"][name] != value for name, value in actual.items()):
            raise ValueError("MIGRATION_APPROVED_INPUTS_CHANGED")
        downstream = subject["package_revision"] == DOWNSTREAM_REVISION
        if downstream and passed:
            branch_files, passed = run_downstream(files, subject)
            files.update(branch_files)
        files["CANDIDATE_MANIFEST.json"] = files.pop("MANIFEST.json")
        files["GATE.json"] = json_bytes(gate)
        candidate_route = "MIG-5/MIG-6/MOD-2" if downstream else "MIG-5"
        modernization = publication_metadata(configuration, files, gate["manifest_sha256"], candidate_route)
        files["MANIFEST.json"] = json_bytes({
            "package_revision": ("public-integrated-mig5-downstream/1" if downstream
                                 else "public-integrated-mig5/1"),
            "input_manifest_sha256": gate["manifest_sha256"],
            "source_evidence": subject["sources"],
            "scenario": subject["scenario"],
            "claim_record": identity(raw_record),
            "reviewer_approval": identity(raw_approval),
            "implementations": {
                name: identity(secure_read(ROOT / "scripts", name, LIMIT))
                for name in ("review_mig5.py", "review_claim_gate.py")
            },
            "files": {name: identity(raw) for name, raw in files.items()},
            **modernization,
            **AUTHORITY,
        })
        write_bundle(scratch, leaf, files, names=tuple(files), allow_csv=downstream)
    except (EvidenceError, OSError, ValueError) as error:
        return 2, {**gate, "migration": "REFUSED", "reason": refusal_code(error)}
    return (0 if passed else 1), {
        **gate, "migration": "PUBLISHED", "comparison": "PASS" if passed else "FAIL",
        "output_manifest_sha256": identity(files["MANIFEST.json"])["sha256"],
    }


def refusal_code(error):
    if isinstance(error, EvidenceError):
        return error.code
    if isinstance(error, ValueError):
        return str(error)
    return "MIG5_INPUT_REFUSED"


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", allow_abbrev=False)
    prepare.add_argument("--scenario", choices=SCENARIOS)
    proceed = commands.add_parser("continue", allow_abbrev=False)
    for command in (prepare, proceed):
        command.add_argument("--destination", required=True)
    proceed.add_argument("--package", required=True, type=Path)
    proceed.add_argument("--record", required=True, type=Path)
    proceed.add_argument("--approval", type=Path)
    add_configuration_arguments(proceed)
    args = parser.parse_args()
    try:
        require_evidence_io()
        scratch, leaf = scratch_destination(args.destination, "intg3a")
        if args.command == "prepare":
            files = build_subject(args.scenario)
            write_bundle(scratch, leaf, files, names=tuple(files))
            status, result = 0, {"manifest_sha256": identity(files["MANIFEST.json"])["sha256"]}
        else:
            status, result = continue_mig5(args, scratch, leaf)
    except (EvidenceError, OSError, ValueError, KeyError, TypeError, AttributeError, IndexError) as error:
        status, result = 2, {"decision": "BLOCK", "blocks": [{
            "code": refusal_code(error),
        }]}
    sys.stdout.buffer.write(json_bytes({**result, **AUTHORITY}))
    return status


if __name__ == "__main__":
    sys.exit(main())
