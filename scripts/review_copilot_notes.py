"""Validate and save operator-supplied notes beside a public two-source review."""

import argparse
from pathlib import Path
import re
import sys

from sas_re.platform_io import require_evidence_io
from sas_re.safeio import EvidenceError, _parse_json, ensure_disjoint, read_json, secure_read

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mvp1_demo import scratch_destination, write_bundle
from review_intake import identity, json_bytes


LIMIT = 262144


def load_review_payloads(package, manifest_sha256):
    raw = secure_read(package, "MANIFEST.json", LIMIT)
    if identity(raw)["sha256"] != manifest_sha256:
        raise ValueError("REVIEW_MANIFEST_SHA256_MISMATCH")
    manifest = _parse_json(raw)
    if (manifest["scope"] != "public-synthetic"
            or manifest["package_revision"] != "public-intake-review/3"):
        raise ValueError("REVIEW_PACKAGE_UNSUPPORTED")

    sources = manifest["sources"]
    if len(sources) != 2 or set(manifest["files"]) != {
        "README.md", "SOURCE_1.json", "SOURCE_1.md", "SOURCE_2.json", "SOURCE_2.md",
    }:
        raise ValueError("REVIEW_PACKAGE_UNSUPPORTED")

    payloads = {}
    for name, expected in manifest["files"].items():
        payload = secure_read(package, name, LIMIT)
        if identity(payload) != expected:
            raise ValueError("REVIEW_PACKAGE_PAYLOAD_MISMATCH")
        payloads[name] = payload

    return manifest, payloads


def citation_index(package, manifest_sha256):
    manifest, payloads = load_review_payloads(package, manifest_sha256)
    citations = {}
    for index, source in enumerate(manifest["sources"], 1):
        path = source["path"]
        if (path in citations or source["evidence"] != f"SOURCE_{index}.json"
                or source["review"] != f"SOURCE_{index}.md"):
            raise ValueError("REVIEW_PACKAGE_UNSUPPORTED")
        evidence = _parse_json(payloads[source["evidence"]])
        original = manifest["inputs"][path]
        if any(evidence["source"][key] != original[key] for key in ("bytes", "sha256")):
            raise ValueError("REVIEW_SOURCE_IDENTITY_MISMATCH")
        anchors = re.findall(rb'<a id="(bytes-([0-9]+)-([0-9]+))"></a>', payloads[source["review"]])
        citations[path] = {name.decode("ascii") for name, start, end in anchors
                           if 0 <= int(start) < int(end) <= original["bytes"]}
    return citations


def validate_review(package, record):
    """Check binding and citation existence. Dispositions remain operator assertions."""
    if not isinstance(record, dict) or set(record) != {
        "manifest_sha256", "reviewer", "copilot_interaction", "human_approval", "findings",
    }:
        raise ValueError("REVIEW_RECORD_INVALID")
    if not isinstance(record["reviewer"], str) or not record["reviewer"].strip():
        raise ValueError("REVIEW_REVIEWER_REQUIRED")
    if record["copilot_interaction"] != "OBSERVED":
        raise ValueError("REVIEW_INTERACTION_NOT_OBSERVED")
    if record["human_approval"] != "APPROVED":
        raise ValueError("REVIEW_HUMAN_APPROVAL_REQUIRED")

    findings = record["findings"]
    if not isinstance(findings, list) or not findings:
        raise ValueError("REVIEW_FINDINGS_REQUIRED")
    citations = citation_index(package, record["manifest_sha256"])
    for finding in findings:
        if not isinstance(finding, dict) or set(finding) != {
            "claim", "citations", "disposition", "review_note",
        }:
            raise ValueError("REVIEW_FINDING_INVALID")
        if (finding["disposition"] not in ("ACCEPTED", "REJECTED", "NEEDS_EVIDENCE")
                or any(not isinstance(finding[key], str) or not finding[key].strip()
                       for key in ("claim", "review_note"))):
            raise ValueError("REVIEW_FINDING_INVALID")
        refs = finding["citations"]
        if not isinstance(refs, list) or not refs:
            raise ValueError("REVIEW_CITATION_REQUIRED")
        for ref in refs:
            if (not isinstance(ref, dict) or set(ref) != {"path", "anchor"}
                    or any(not isinstance(value, str) for value in ref.values())
                    or ref["anchor"] not in citations.get(ref["path"], ())):
                raise ValueError("REVIEW_CITATION_INVALID")
    return json_bytes(record)


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--destination", required=True, help="fresh /tmp/sas-re-int5-<label> directory")
    args = parser.parse_args()
    try:
        require_evidence_io()
        scratch, leaf = scratch_destination(args.destination, "int5")
        package = args.package.absolute()
        ensure_disjoint(scratch / leaf, [package])
        record = validate_review(package, read_json(args.record.absolute(), LIMIT))
        name = "COPILOT_REVIEW.json"
        write_bundle(scratch, leaf, {name: record}, names=(name,))
    except FileExistsError:
        parser.exit(2, "BLOCKED: destination exists\n")
    except EvidenceError as error:
        parser.exit(2, f"{error.gate}: {error.code}\n")
    except (KeyError, TypeError, AttributeError, UnicodeError):
        parser.exit(2, "REFUSED: REVIEW_PACKAGE_INVALID\n")
    except ValueError as error:
        parser.exit(2, f"REFUSED: {error}\n")
    except OSError:
        parser.exit(2, "REFUSED: FILE_IO_REFUSED\n")
    print(scratch / leaf / name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
