"""Review the approved public INT-1 fixture from a caller-selected directory."""

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

from sas_re.platform_io import require_evidence_io
from sas_re.safeio import EvidenceError, enumerate_files, secure_read

sys.path.insert(0, str(Path(__file__).resolve().parent))
from migration_review import render
from mvp1_demo import scratch_destination, write_bundle
from review_source import dependency_review


SCOPE_SHA256 = "268585d9ac407d5d26b924aed49b5e7fe5edac55928576209ee20cae86ebf9ba"
INPUTS = ["pipeline.sas.txt", "scope.json"]
STATUS_FIELDS = (
    "artifact_authority", "behavioral_evidence", "semantic_verification",
    "semantic_acceptance", "reference_experiment", "benchmark_execution",
    "historical_source_run_provenance",
)


def identity(data):
    return {"bytes": len(data), "sha256": sha256(data).hexdigest()}


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def build_review(intake):
    if enumerate_files(intake) != INPUTS:
        raise ValueError("INTAKE_FILE_SET_MISMATCH")
    scope_bytes = secure_read(intake, "scope.json", 4096)
    if sha256(scope_bytes).hexdigest() != SCOPE_SHA256:
        raise ValueError("INTAKE_SCOPE_NOT_APPROVED")
    scope = json.loads(scope_bytes)
    source = secure_read(intake, scope["source"], 65536)
    source_id = identity(source)
    if source_id["sha256"] != scope["sha256"]:
        raise ValueError("SOURCE_SHA256_MISMATCH")

    evidence, readme = dependency_review(source, scope["ranges"], source_id["sha256"],
                                         recover_sql=True)
    files = {
        "README.md": readme,
        "EVIDENCE.json": json_bytes(evidence),
        "MIGRATION_REVIEW.md": render(evidence),
    }
    manifest = {
        **{key: evidence[key] for key in STATUS_FIELDS},
        "package_revision": "public-intake-review/1",
        "scope": scope["scope"],
        "inputs": {"scope.json": identity(scope_bytes), scope["source"]: source_id},
        "source_evidence": "EVIDENCE.json",
        "copilot_review": "NOT_TESTED",
        "files": {name: identity(data) for name, data in files.items()},
    }
    files["MANIFEST.json"] = json_bytes(manifest)
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--intake", required=True, type=Path, help="approved public fixture directory")
    parser.add_argument("--destination", required=True, help="fresh /tmp/sas-re-int1-<label> directory")
    args = parser.parse_args()
    try:
        require_evidence_io()
        scratch, leaf = scratch_destination(args.destination, "int1")
        destination = scratch / leaf
        if os.path.lexists(destination):
            raise FileExistsError
        files = build_review(args.intake.absolute())
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
