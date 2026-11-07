"""Continue a public INT-3 review through GATE-1 and the bounded MIG-2 candidate."""

import argparse
from pathlib import Path
import sys

from sas_re.platform_io import require_evidence_io
from sas_re.safeio import EvidenceError, _parse_json, ensure_disjoint, secure_read

sys.path.insert(0, str(Path(__file__).resolve().parent))
from migrate_projection_sort import load_plan, run_rows
from mvp1_demo import scratch_destination, write_bundle
from review_claim_gate import AUTHORITY, review_claims
from review_copilot_notes import LIMIT
from review_intake import identity, json_bytes


def read_input(path):
    return secure_read(path.parent, path.name, LIMIT)


def continue_review(args):
    require_evidence_io()
    package = args.package.absolute()
    record = args.record.absolute() if args.record else None
    if record is None:
        return 1, {"decision": "REVIEW_REQUIRED", "pending": [{"code": "COPILOT_CLAIM_RECORD_REQUIRED"}]}
    try:
        raw_record = read_input(record)
        raw_approval = read_input(args.approval.absolute()) if args.approval else None
        gate = review_claims(package, raw_record, _parse_json(raw_approval) if raw_approval is not None else None)
    except (EvidenceError, OSError, ValueError, TypeError, KeyError, AttributeError, IndexError) as error:
        return 2, {"decision": "BLOCK", "blocks": [{"code": getattr(error, "code", "CLAIM_INPUT_REFUSED")}]}
    if gate["decision"] != "PASS":
        return (1 if gate["decision"] == "REVIEW_REQUIRED" else 2), gate

    try:
        scratch, leaf = scratch_destination(args.destination, "intg1")
        intake = args.intake.absolute()
        ensure_disjoint(scratch / leaf, [intake, package])
        plan = load_plan(intake, package)
        if plan["input_manifest_sha256"] != gate["manifest_sha256"]:
            raise ValueError("APPROVED_PACKAGE_CHANGED")
        if (identity(read_input(record))["sha256"] != gate["record_sha256"]
                or read_input(args.approval.absolute()) != raw_approval):
            raise ValueError("APPROVED_REVIEW_CHANGED")
        raw_rows = read_input(args.rows.absolute())
        if identity(raw_rows)["sha256"] != args.rows_sha256:
            raise ValueError("MIGRATION_ROWS_SHA256_MISMATCH")
        rows, validation = run_rows(plan, raw_rows)
        files = {
            "PLAN.json": json_bytes({**plan, **AUTHORITY}),
            "ROWS.json": json_bytes(rows),
            "VALIDATION.json": json_bytes({**validation, **AUTHORITY}),
            "GATE.json": json_bytes(gate),
        }
        scripts = Path(__file__).resolve().parent
        files["MANIFEST.json"] = json_bytes({
            "package_revision": "public-integrated-migration/1",
            "input_manifest_sha256": plan["input_manifest_sha256"],
            "source_evidence": plan["source_evidence"],
            "claim_record": identity(raw_record),
            "reviewer_approval": identity(raw_approval),
            "input_rows": identity(raw_rows),
            "implementations": {
                name: identity(secure_read(scripts, name, LIMIT))
                for name in ("review_to_migration.py", "review_claim_gate.py",
                             "migrate_projection_sort.py", "migration_candidate.py")
            },
            "files": {name: identity(raw) for name, raw in files.items()},
            **AUTHORITY,
        })
        write_bundle(scratch, leaf, files, names=tuple(files))
    except FileExistsError:
        return 2, {**gate, "migration": "REFUSED", "reason": "DESTINATION_EXISTS"}
    except EvidenceError as error:
        return 2, {**gate, "migration": "REFUSED", "reason": error.code}
    except ValueError as error:
        return 2, {**gate, "migration": "REFUSED", "reason": str(error)}
    except (OSError, TypeError, KeyError, AttributeError, IndexError):
        return 2, {**gate, "migration": "REFUSED", "reason": "MIGRATION_INPUT_REFUSED"}
    comparison = validation["comparison"]
    return (1 if comparison == "FAIL" else 0), {
        **gate, "migration": "PUBLISHED", "comparison": comparison,
        "output_manifest_sha256": identity(files["MANIFEST.json"])["sha256"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--intake", required=True, type=Path)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--record", type=Path)
    parser.add_argument("--approval", type=Path)
    parser.add_argument("--rows", required=True, type=Path)
    parser.add_argument("--rows-sha256", required=True)
    parser.add_argument("--destination", required=True, help="fresh /tmp/sas-re-intg1-<label> directory")
    args = parser.parse_args()
    try:
        status, result = continue_review(args)
    except EvidenceError as error:
        status, result = 2, {"decision": "BLOCK", "blocks": [{"code": error.code}]}
    sys.stdout.buffer.write(json_bytes({**result, **AUTHORITY}))
    return status


if __name__ == "__main__":
    sys.exit(main())
