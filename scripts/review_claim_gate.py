"""Review structured claims and the three known public E2E contradictions."""

import argparse
from pathlib import Path
import re
import sys

from sas_re.platform_io import require_evidence_io
from sas_re.safeio import EvidenceError, _parse_json, read_json, secure_read

sys.path.insert(0, str(Path(__file__).resolve().parent))
from review_copilot_notes import LIMIT, load_review_payloads
from review_intake import STATUS_FIELDS, identity, json_bytes


DELIVERABLES = ("reconstruction", "prd", "dependency_analysis", "verification_plan", "adr")
CLASSIFICATIONS = {"SOURCE_DECLARED", "CANDIDATE_ENGINEERING", "INFERRED",
                   "UNRESOLVED", "PACKAGE_METADATA"}
KNOWN_CONTRADICTIONS = (
    ("INTRA_SOURCE_SEQUENCE", re.compile(r"\bintra[- ]source sequence\b")),
    ("DECLARED_HANDOFF", re.compile(r"\btraced the declared handoff\b")),
    ("PARTIAL_RUNTIME_LINEAGE_PROOF",
     re.compile(r"\bruntime dataset lineage proof across sources\s*:\s*partially supported\b")),
)
AUTHORITY = dict(zip(STATUS_FIELDS, (
    "DRAFT", "UNAVAILABLE", "UNVERIFIABLE", "BLOCKED", "NOT_RUN", "NOT_RUN", "UNBOUND",
), strict=True))


def pointer_value(document, pointer):
    """Resolve the small pointer subset used by these review packages."""
    if not isinstance(pointer, str) or not pointer.startswith("/") or "~" in pointer:
        raise ValueError("EVIDENCE_POINTER_INVALID")
    for part in pointer[1:].split("/"):
        if isinstance(document, list):
            if not re.fullmatch(r"0|[1-9][0-9]{0,8}", part):
                raise ValueError("EVIDENCE_POINTER_INVALID")
            document = document[int(part)]
        else:
            document = document[part]
    return document


def evidence_classification(filename, pointer):
    if filename == "MANIFEST.json":
        if pointer in {f"/{field}" for field in (*STATUS_FIELDS, "review_status", "copilot_review")}:
            return "PACKAGE_METADATA"
        if re.fullmatch(r"/cross_file_dependencies/[0-9]+/(dataset_version|execution_order)", pointer):
            return "UNRESOLVED"
        if pointer.startswith("/cross_file_dependencies/") or pointer == "/cross_file_resolution":
            return "INFERRED"
    elif re.fullmatch(r"/declared_operation/(input|output|selected_columns|ordering_keys|declared_direction)",
                      pointer):
        return "SOURCE_DECLARED"
    elif re.fullmatch(r"/declared_operation/(input_schema|output_schema|row_selection|selected_column_values_and_derivation)",
                      pointer) or pointer in ("/execution_behavior", "/key_schema"):
        return "UNRESOLVED"
    return None


def review_claims(package, raw_record, approval=None):
    record = _parse_json(raw_record)
    if not isinstance(record, dict) or set(record) != {
        "version", "manifest_sha256", "deliverables", "claims",
    } or type(record["version"]) is not int or record["version"] != 1:
        raise ValueError("CLAIM_RECORD_INVALID")
    manifest, payloads = load_review_payloads(package, record["manifest_sha256"])
    documents = {"MANIFEST.json": manifest}
    for source in manifest["sources"]:
        name = source["evidence"]
        if name not in ("SOURCE_1.json", "SOURCE_2.json") or name in documents:
            raise ValueError("CLAIM_SOURCE_RECORD_INVALID")
        evidence = _parse_json(payloads[name])
        original = manifest["inputs"][source["path"]]
        if any(evidence["source"][key] != original[key] for key in ("bytes", "sha256")):
            raise ValueError("REVIEW_SOURCE_IDENTITY_MISMATCH")
        documents[name] = evidence

    deliverables = record["deliverables"]
    if (not isinstance(deliverables, dict) or set(deliverables) != set(DELIVERABLES)
            or any(not isinstance(sections, dict) or not sections
                   or any(not section.strip() or not isinstance(text, str) or not text.strip()
                          for section, text in sections.items())
                   for sections in deliverables.values())
            or not isinstance(record["claims"], list)):
        raise ValueError("CLAIM_DELIVERABLES_INVALID")
    blocks, pending, seen, covered = [], [], set(), set()
    if manifest["cross_file_dependencies"]:
        for name in DELIVERABLES:
            for section, text in deliverables[name].items():
                prose = " ".join(re.sub(r"[*_\x60]", "", f"{section} {text}").casefold().split())
                for code, pattern in KNOWN_CONTRADICTIONS:
                    if pattern.search(prose):
                        blocks.append({"deliverable": name, "section": section, "code": code})

    for claim in record["claims"]:
        if not isinstance(claim, dict) or set(claim) != {
            "id", "text", "classification", "evidence", "deliverable", "section", "disposition",
        } or any(not isinstance(claim[key], str) or not claim[key].strip()
                 for key in ("id", "text", "classification", "deliverable", "section", "disposition")):
            blocks.append({"code": "CLAIM_FIELDS_REQUIRED"})
            continue
        claim_id, name, classification = claim["id"], claim["deliverable"], claim["classification"]

        def block(code):
            blocks.append({"claim": claim_id, "code": code})

        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", claim_id) or claim_id in seen:
            block("CLAIM_ID_INVALID_OR_DUPLICATE")
        seen.add(claim_id)
        section = claim["section"]
        if claim["text"] not in deliverables.get(name, {}).get(section, ""):
            block("CLAIM_LOCATION_UNRESOLVED")
        else:
            covered.add((name, section))
        if classification not in CLASSIFICATIONS:
            block("CLAIM_CLASSIFICATION_INVALID")
        if claim["disposition"] == "REJECTED":
            block("CLAIM_REJECTED")
        elif claim["disposition"] == "UNREVIEWED":
            pending.append({"claim": claim_id, "code": "CLAIM_HUMAN_REVIEW_REQUIRED"})
        elif claim["disposition"] != "APPROVED":
            block("CLAIM_DISPOSITION_INVALID")

        if not isinstance(claim["evidence"], list) or not claim["evidence"]:
            block("CLAIM_EVIDENCE_REQUIRED")
            continue
        expected_classes = set()
        evidence_files = set()
        for ref in claim["evidence"]:
            try:
                if not isinstance(ref, dict) or set(ref) != {"file", "pointer"}:
                    raise ValueError
                filename, pointer = ref["file"], ref["pointer"]
                value = pointer_value(documents[filename], pointer)
                if value is None:
                    raise ValueError
                expected_classes.add(evidence_classification(filename, pointer))
                evidence_files.add(filename)
            except (IndexError, KeyError, TypeError, ValueError):
                block("CLAIM_EVIDENCE_UNRESOLVED")
        if ((classification == "SOURCE_DECLARED"
             and (expected_classes != {"SOURCE_DECLARED"} or len(evidence_files) != 1))
                or (classification == "PACKAGE_METADATA" and expected_classes != {"PACKAGE_METADATA"})
                or ("PACKAGE_METADATA" in expected_classes and classification != "PACKAGE_METADATA")
                or ("INFERRED" in expected_classes and classification not in {"INFERRED", "UNRESOLVED"})
                or ("UNRESOLVED" in expected_classes and classification != "UNRESOLVED")):
            block("CLAIM_EVIDENCE_CLASSIFICATION_CONFLICT")

    for name in DELIVERABLES:
        if not any(deliverable == name for deliverable, _ in covered):
            pending.append({"deliverable": name, "code": "DELIVERABLE_CLAIMS_REVIEW_REQUIRED"})
    digest = identity(raw_record)["sha256"]
    if not (isinstance(approval, dict) and set(approval) == {"record_sha256", "reviewer", "decision"}
            and approval["record_sha256"] == digest and isinstance(approval["reviewer"], str)
            and approval["reviewer"].strip() and approval["decision"] == "APPROVED"):
        pending.append({"code": "BOUND_HUMAN_APPROVAL_REQUIRED"})
    decision = "BLOCK" if blocks else "REVIEW_REQUIRED" if pending else "PASS"
    return {"decision": decision, "record_sha256": digest, "manifest_sha256": record["manifest_sha256"],
            "blocks": blocks, "pending": pending, **AUTHORITY}


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--record", required=True, type=Path)
    parser.add_argument("--approval", type=Path)
    args = parser.parse_args()
    try:
        require_evidence_io()
        path = args.record.absolute()
        approval = read_json(args.approval.absolute(), LIMIT) if args.approval else None
        result = review_claims(args.package.absolute(), secure_read(path.parent, path.name, LIMIT), approval)
    except (EvidenceError, OSError, ValueError, TypeError, KeyError, AttributeError, IndexError) as error:
        result = {"decision": "BLOCK", "blocks": [{"code": getattr(error, "code", "CLAIM_INPUT_REFUSED")}],
                  **AUTHORITY}
    sys.stdout.buffer.write(json_bytes(result))
    return {"PASS": 0, "REVIEW_REQUIRED": 1, "BLOCK": 2}[result["decision"]]


if __name__ == "__main__":
    sys.exit(main())
