"""Run the public MIG-1 DATA projection and stable integer-key sort candidate."""

import argparse
import math
from pathlib import Path
import sys

from sas_re.platform_io import require_evidence_io
from sas_re.safeio import EvidenceError, _parse_json, ensure_disjoint, secure_read

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mvp1_demo import scratch_destination, write_bundle
from review_copilot_notes import LIMIT, citation_index, validate_review
from review_intake import identity, json_bytes


PACKAGE_SHA256 = "8bfc638d5c4db4f60001010ee7abbb3db175c29f44696b0403c621fed953227a"
EXAMPLE = Path(__file__).resolve().parents[1] / "tests/fixtures/candidate-execution/projection"
AUTHORITY = {
    "artifact_authority": "DRAFT",
    "behavioral_evidence": "UNAVAILABLE",
    "semantic_verification": "UNVERIFIABLE",
    "semantic_acceptance": "BLOCKED",
    "reference_experiment": "NOT_RUN",
    "benchmark_execution": "NOT_RUN",
    "historical_source_run_provenance": "UNBOUND",
}


def prepare_and_sort(rows):
    staged = []
    for row in rows:
        if type(row) is not dict or row.keys() != {"id", "amount", "memo"}:
            raise ValueError("MIGRATION_ROW_FIELDS_UNSUPPORTED")
        key, amount = row["id"], row["amount"]
        if (type(key) is not int or type(row["memo"]) is not str
                or type(amount) not in (int, float)
                or type(amount) is float and not math.isfinite(amount)):
            raise ValueError("MIGRATION_ROW_TYPES_UNSUPPORTED")
        # prepare.sas.txt, SOURCE_2.json /declared_operation/declaration_spans/keep.
        staged.append({"id": key, "amount": amount})
    # order.sas.txt, SOURCE_1.md#bytes-0-56. Stable ties are a candidate choice.
    return sorted(staged, key=lambda row: row["id"])


def build_result(package, notes_path):
    notes = {"status": "NOT_SUPPLIED"}
    if notes_path is None:
        citation_index(package, PACKAGE_SHA256)
    else:
        raw = secure_read(notes_path.parent, notes_path.name, LIMIT)
        record = _parse_json(raw)
        if not isinstance(record, dict) or record.get("manifest_sha256") != PACKAGE_SHA256:
            raise ValueError("MIGRATION_REVIEW_BINDING_MISMATCH")
        validate_review(package, record)
        notes = {"status": "OPERATOR_APPROVAL_RECORDED", **identity(raw)}

    cases_bytes = secure_read(EXAMPLE, "CASES.json", LIMIT)
    cases = _parse_json(cases_bytes)
    observed = prepare_and_sort(cases["input"])
    # Compare serialized values to distinguish, for example, 17 from 17.0.
    passed = json_bytes(observed) == json_bytes(cases["expected"])
    files = {
        "README.md": secure_read(EXAMPLE, "README.md", LIMIT),
        "CASES.json": cases_bytes,
        "VALIDATION.json": json_bytes({
            "basis": "PUBLIC_SYNTHETIC_ENGINEERING_EXPECTATIONS",
            "verdict": "PASS" if passed else "FAIL",
            "expected": cases["expected"],
            "observed": observed,
            **AUTHORITY,
        }),
    }
    script = Path(__file__).resolve()
    files["MANIFEST.json"] = json_bytes({
        "input_manifest_sha256": PACKAGE_SHA256,
        "candidate": {"path": "scripts/migration_candidate.py",
                      **identity(secure_read(script.parent, script.name, LIMIT))},
        "operator_review_notes": notes,
        "files": {name: identity(raw) for name, raw in files.items()},
        **AUTHORITY,
    })
    return files, passed


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--review-notes", type=Path)
    parser.add_argument("--destination", required=True, help="fresh /tmp/sas-re-mig1-<label> directory")
    args = parser.parse_args()
    try:
        require_evidence_io()
        scratch, leaf = scratch_destination(args.destination, "mig1")
        package = args.package.absolute()
        ensure_disjoint(scratch / leaf, [package])
        notes = args.review_notes.absolute() if args.review_notes else None
        files, passed = build_result(package, notes)
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
    print(json_bytes({"open": str(scratch / leaf / "README.md"),
                      "manifest_sha256": identity(files["MANIFEST.json"])["sha256"],
                      "engineering_validation": "PASS" if passed else "FAIL"}).decode(), end="")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
