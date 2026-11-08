"""Prepare an unreviewed GATE-1 record from one Copilot JSON draft."""

import argparse
from pathlib import Path
import sys

from sas_re.platform_io import require_evidence_io
from sas_re.safeio import EvidenceError, _parse_json, ensure_disjoint, secure_read

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mvp1_demo import scratch_destination, write_bundle
from review_claim_gate import AUTHORITY, DELIVERABLES, review_claims
from review_copilot_notes import LIMIT
from review_intake import identity, json_bytes
from review_mig5 import DOWNSTREAM_REVISION


def prepare_record(package, raw_draft):
    draft = _parse_json(raw_draft)
    if (not isinstance(draft, dict)
            or set(draft) != {"version", "manifest_sha256", "deliverables", "claims"}
            or type(draft["version"]) is not int or draft["version"] != 1
            or not isinstance(draft["claims"], list)):
        raise ValueError("CLAIM_DRAFT_INVALID")
    manifest_raw = secure_read(package, "MANIFEST.json", LIMIT)
    manifest_digest = identity(manifest_raw)["sha256"]
    if draft["manifest_sha256"] != manifest_digest:
        raise ValueError("REVIEW_MANIFEST_SHA256_MISMATCH")
    manifest = _parse_json(manifest_raw)

    deliverables = draft["deliverables"]
    if not isinstance(deliverables, dict) or set(deliverables) != set(DELIVERABLES):
        raise ValueError("CLAIM_DELIVERABLES_INVALID")
    prefix = None
    if manifest.get("package_revision") == DOWNSTREAM_REVISION:
        prefix = f'{manifest["scenario"]}/'
    bound_files = {"MANIFEST.json", *manifest["files"]}
    sections = {name: set() for name in DELIVERABLES}
    for claim in draft["claims"]:
        if not isinstance(claim, dict):
            raise ValueError("CLAIM_DRAFT_INVALID")
        name, section = claim.get("deliverable"), claim.get("section")
        if isinstance(name, str) and name in sections and isinstance(section, str) and section.strip():
            sections[name].add(section)
        claim["disposition"] = "UNREVIEWED"
        refs = claim.get("evidence")
        if prefix and isinstance(refs, list):
            for ref in refs:
                filename = ref.get("file") if isinstance(ref, dict) else None
                if isinstance(filename, str) and filename.startswith(prefix):
                    basename = filename.removeprefix(prefix)
                    if basename in bound_files:
                        ref["file"] = basename

    for name in DELIVERABLES:
        if isinstance(deliverables[name], str):
            if len(sections[name]) > 1:
                raise ValueError(f"CLAIM_DRAFT_AMBIGUOUS_SECTIONS:{name}")
            title = next(iter(sections[name]), "Review")
            deliverables[name] = {title: deliverables[name]}

    record = json_bytes(draft)
    if len(record) > LIMIT:
        raise ValueError("CLAIM_RECORD_TOO_LARGE")
    return record, review_claims(package, record)


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--draft", type=Path, required=True, help="one Copilot JSON object")
    parser.add_argument("--destination", required=True, help="fresh /tmp/sas-re-claim-preflight-<label>")
    args = parser.parse_args()
    try:
        require_evidence_io()
        scratch, leaf = scratch_destination(args.destination, "claim-preflight")
        package, draft = args.package.absolute(), args.draft.absolute()
        ensure_disjoint(scratch / leaf, [package])
        raw = secure_read(draft.parent, draft.name, LIMIT)
        record, gate = prepare_record(package, raw)
        report = {**gate, "copilot_draft": identity(raw)}
        files = {"COPILOT_DRAFT.json": raw, "CLAIMS_UNREVIEWED.json": record,
                 "PREFLIGHT.json": json_bytes(report)}
        write_bundle(scratch, leaf, files, names=tuple(files))
    except (EvidenceError, OSError, ValueError, TypeError, KeyError, AttributeError, IndexError) as error:
        code = (error.code if isinstance(error, EvidenceError) else str(error)
                if isinstance(error, ValueError) else "CLAIM_DRAFT_REFUSED")
        sys.stdout.buffer.write(json_bytes({"decision": "BLOCK", "blocks": [{"code": code}], **AUTHORITY}))
        return 2
    sys.stdout.buffer.write(files["PREFLIGHT.json"])
    return 0 if gate["decision"] == "REVIEW_REQUIRED" else 2


if __name__ == "__main__":
    sys.exit(main())
