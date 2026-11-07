"""Check explicit P2A Markdown citations before human review."""

import argparse
from pathlib import Path
import re
import sys

from sas_re.platform_io import require_evidence_io
from sas_re.safeio import EvidenceError, _parse_json, secure_read

sys.path.insert(0, str(Path(__file__).resolve().parent))

from review_claim_gate import AUTHORITY, pointer_value
from review_intake import identity, json_bytes, modernization_drafts


CITATION = re.compile(r"`([\w.-]+)#(/[^\s`]+)`")


def check_citations(package, intake, draft):
    manifest_raw = secure_read(package, "MANIFEST.json", 65536)
    manifest = _parse_json(manifest_raw)
    if manifest.get("package_revision") != "public-intake-p2a/1":
        raise ValueError("P2A_PACKAGE_REQUIRED")
    payloads = {"MANIFEST.json": manifest_raw}
    for name in ("INVENTORY.json", "EVIDENCE.json"):
        raw = secure_read(package, name)
        if identity(raw) != manifest["files"][name]:
            raise ValueError("P2A_PAYLOAD_IDENTITY_MISMATCH")
        payloads[name] = raw
    for name, limit in (("scope.json", 4096), ("profile.json", 16384)):
        raw = secure_read(intake, name, limit)
        if identity(raw) != manifest["inputs"][name]:
            raise ValueError("P2A_INPUT_IDENTITY_MISMATCH")
        payloads[name] = raw
    expected = modernization_drafts(payloads)
    for name, key in (("migration-profile.yaml", "MIGRATION_PROFILE.json"),
                      ("tie-out.yaml", "TIE_OUT.json")):
        raw = secure_read(package, name, 65536)
        if raw != expected[key]:
            raise ValueError("P2A_DRAFT_IDENTITY_MISMATCH")
        payloads[name] = raw
    documents = {name: _parse_json(raw) for name, raw in payloads.items()}
    findings, checked = [], 0
    for number, line in enumerate(draft.decode("utf-8").splitlines(), 1):
        for match in CITATION.finditer(line):
            filename, pointer = match.groups()
            checked += 1
            try:
                pointer_value(documents[filename], pointer)
            except (KeyError, IndexError, TypeError, ValueError):
                findings.append({"code": "P2A_CITATION_UNRESOLVED", "line": number,
                                 "file": filename, "pointer": pointer})
        if "#/" in CITATION.sub("", line):
            findings.append({"code": "P2A_CITATION_FORMAT_INVALID", "line": number})
    if not checked:
        findings.append({"code": "P2A_CITATIONS_REQUIRED"})
    return {**AUTHORITY, "decision": "BLOCK" if findings else "REVIEW_REQUIRED",
            "manifest": identity(manifest_raw), "draft": identity(draft),
            "citations_checked": checked, "findings": findings}


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    for name in ("package", "intake", "draft"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        require_evidence_io()
        draft = args.draft.absolute()
        report = check_citations(args.package.absolute(), args.intake.absolute(),
                                 secure_read(draft.parent, draft.name, 262144))
    except (EvidenceError, OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        code = error.code if isinstance(error, EvidenceError) else "P2A_PREFLIGHT_REFUSED"
        report = {**AUTHORITY, "decision": "BLOCK", "findings": [{"code": code}]}
    sys.stdout.buffer.write(json_bytes(report))
    return 2 if report["decision"] == "BLOCK" else 0


if __name__ == "__main__":
    sys.exit(main())
