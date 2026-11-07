"""Prepare or continue the pinned public MIG-5 operator review."""

import argparse
from pathlib import Path
import sys

from sas_re.platform_io import require_evidence_io
from sas_re.safeio import EvidenceError, _parse_json, ensure_disjoint, secure_read

sys.path.insert(0, str(Path(__file__).resolve().parent))
from migrate_preparation_gates import EVIDENCE_PINS, LIMIT, PINS, ROOT, build_package
from migration_candidate import AUTHORITY
from mvp1_demo import scratch_destination, write_bundle
from review_intake import identity, json_bytes
from review_source import dependency_review, single_review


REVISION = "public-mig5-review/1"
PREPARATION = "PREPARATION_EVIDENCE.json"
POPULATION = "POPULATION_EVIDENCE.json"


def build_subject():
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
    prep = "examples/mig3/preparation.sas.txt"
    pop = "examples/mig4/population.sas.txt"
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
    files["MANIFEST.json"] = json_bytes({
        "package_revision": REVISION,
        "scope": "public-synthetic",
        "candidate_scope": "PINNED_MIG5_PREPARATION_AND_POPULATION_GATES",
        "scenario": "ALL_PINNED_MIG5_SCENARIOS",
        "sas_dataset_continuity": "UNESTABLISHED",
        "inputs": inputs,
        "sources": [{"path": prep, "evidence": PREPARATION}, {"path": pop, "evidence": POPULATION}],
        "files": {name: identity(raw) for name, raw in files.items()},
        **AUTHORITY,
    })
    return files


def load_subject(package, manifest_sha256):
    files = build_subject()
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
    raw_record = secure_read(record.parent, record.name, LIMIT)
    raw_approval = secure_read(approval.parent, approval.name, LIMIT) if approval else None
    gate = review_claims(package, raw_record, _parse_json(raw_approval) if approval else None)
    if gate["decision"] != "PASS":
        return (1 if gate["decision"] == "REVIEW_REQUIRED" else 2), gate
    try:
        subject, _ = load_subject(package, gate["manifest_sha256"])
        if (secure_read(record.parent, record.name, LIMIT) != raw_record
                or secure_read(approval.parent, approval.name, LIMIT) != raw_approval):
            raise ValueError("APPROVED_REVIEW_CHANGED")
        files, passed = build_package(package / PREPARATION, package / POPULATION)
        candidate_manifest = files.pop("MANIFEST.json")
        candidate = _parse_json(candidate_manifest)
        if {**candidate["inputs"], **candidate["runner"]} != subject["inputs"]:
            raise ValueError("MIGRATION_APPROVED_INPUTS_CHANGED")
        files["CANDIDATE_MANIFEST.json"] = candidate_manifest
        files["GATE.json"] = json_bytes(gate)
        files["MANIFEST.json"] = json_bytes({
            "package_revision": "public-integrated-mig5/1",
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
            **AUTHORITY,
        })
        write_bundle(scratch, leaf, files, names=tuple(files))
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
    proceed = commands.add_parser("continue", allow_abbrev=False)
    for command in (prepare, proceed):
        command.add_argument("--destination", required=True)
    proceed.add_argument("--package", required=True, type=Path)
    proceed.add_argument("--record", required=True, type=Path)
    proceed.add_argument("--approval", type=Path)
    args = parser.parse_args()
    try:
        require_evidence_io()
        scratch, leaf = scratch_destination(args.destination, "intg3a")
        if args.command == "prepare":
            files = build_subject()
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
