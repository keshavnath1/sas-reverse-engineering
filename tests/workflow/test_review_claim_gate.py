"""Independent claim acceptance requires citations, retained negative prose, and fresh byte-bound approval."""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import runpy
import sys
from tempfile import TemporaryDirectory
import unittest

from workflow.test_review_workflow import ROOT


NEGATIVES = {
    "dependency_analysis": ("[SOURCE_DECLARED] Intra-source sequence:", "INTRA_SOURCE_SEQUENCE"),
    "reconstruction": (
        "Traced the declared handoff between producer/consumer datasets.",
        "DECLARED_HANDOFF",
    ),
    "adr": (
        "Runtime dataset lineage proof across sources: Partially supported",
        "PARTIAL_RUNTIME_LINEAGE_PROOF",
    ),
}


@unittest.skipUnless(sys.platform in ("darwin", "linux"), "Existing POSIX evidence workflow")
class ClaimAcceptanceGateTests(unittest.TestCase):
    def setUp(self):
        self.gate = runpy.run_path(str(ROOT / "scripts/review_claim_gate.py"))
        from review_intake import build_review

        temp = self.enterContext(TemporaryDirectory())
        root = Path(temp).resolve()
        intake = root / "public-input"
        intake.mkdir()
        sources = []
        for name, mode, raw in (
            (
                "select_ticks.sas.txt",
                "data",
                b"data work.tick_projection;\n  set work.public_ticks;\n  keep tick_key magnitude;\nrun;\n",
            ),
            (
                "sort_ticks.sas.txt",
                "sort",
                b"proc sort data=work.tick_projection out=work.tick_sequence;\n  by tick_key;\nrun;\n",
            ),
        ):
            (intake / name).write_bytes(raw)
            sources.append(
                {
                    "path": name,
                    "mode": mode,
                    "sha256": sha256(raw).hexdigest(),
                    "ranges": [[1, len(raw.splitlines())]],
                }
            )
        scope = {"version": 2, "scope": "public-synthetic", "sources": sources}
        (intake / "scope.json").write_text(json.dumps(scope, indent=2) + "\n", encoding="utf-8")
        self.package = root / "review"
        self.package.mkdir()
        files = build_review(intake)
        for name, raw in files.items():
            (self.package / name).write_bytes(raw)
        self.manifest = sha256(files["MANIFEST.json"]).hexdigest()
        self.assertEqual(
            self.manifest, "a853c8e499a8d159c960b0412063b8299d9820ef760853f7748f66515850e763"
        )
        statements = [
            (
                "reconstruction",
                "The DATA statement declares work.tick_projection as output.",
                "SOURCE_DECLARED",
                "SOURCE_1.json",
                "/declared_operation/output",
            ),
            (
                "prd",
                "The SORT statement declares work.tick_projection as input.",
                "SOURCE_DECLARED",
                "SOURCE_2.json",
                "/declared_operation/input",
            ),
            (
                "dependency_analysis",
                "Matching names support a potential cross-file handoff.",
                "INFERRED",
                "MANIFEST.json",
                "/cross_file_dependencies/0/classification",
            ),
            (
                "verification_plan",
                "The manifest records semantic acceptance as BLOCKED.",
                "PACKAGE_METADATA",
                "MANIFEST.json",
                "/semantic_acceptance",
            ),
            (
                "adr",
                "The runtime dataset version remains unresolved.",
                "UNRESOLVED",
                "MANIFEST.json",
                "/cross_file_dependencies/0/dataset_version",
            ),
        ]
        self.record = {
            "version": 1,
            "manifest_sha256": self.manifest,
            "deliverables": {name: {"Review": text} for name, text, *_ in statements},
            "claims": [
                {
                    "id": f"C{i}",
                    "text": text,
                    "classification": classification,
                    "evidence": [{"file": file, "pointer": pointer}],
                    "deliverable": name,
                    "section": "Review",
                    "disposition": "APPROVED",
                }
                for i, (name, text, classification, file, pointer) in enumerate(statements, 1)
            ],
        }

    def evaluate(self, record, approved=True, digest=None):
        raw = self.gate["json_bytes"](record)
        approval = (
            {
                "record_sha256": digest or sha256(raw).hexdigest(),
                "reviewer": "test reviewer",
                "decision": "APPROVED",
            }
            if approved
            else None
        )
        return self.gate["review_claims"](self.package, raw, approval)

    def test_retained_negative_prose_blocks_even_with_correct_structured_claims(self):
        for name, (negative, code) in NEGATIVES.items():
            with self.subTest(name=name):
                record = deepcopy(self.record)
                record["deliverables"][name]["Review"] += "\n\n" + negative
                result = self.evaluate(record)
                self.assertEqual(result["decision"], "BLOCK")
                self.assertIn(
                    {"deliverable": name, "section": "Review", "code": code}, result["blocks"]
                )

    def test_bound_approval_and_deterministic_results(self):
        accepted = self.evaluate(self.record)
        self.assertEqual(accepted["decision"], "PASS")
        self.assertEqual(self.evaluate(self.record), accepted)
        self.assertEqual(self.evaluate(self.record, approved=False)["decision"], "REVIEW_REQUIRED")
        self.assertEqual(self.evaluate(self.record, digest="0" * 64)["decision"], "REVIEW_REQUIRED")
        record = deepcopy(self.record)
        record["claims"][4]["disposition"] = "UNREVIEWED"
        record["claims"][4]["text"] += " An intervening operation may have changed the data."
        record["deliverables"]["adr"]["Review"] = record["claims"][4]["text"]
        self.assertEqual(self.evaluate(record)["decision"], "REVIEW_REQUIRED")

    def test_missing_citations_and_classification_promotions_block(self):
        for index, patch, code in (
            (0, {"evidence": []}, "CLAIM_EVIDENCE_REQUIRED"),
            (
                0,
                {"evidence": [{"file": "SOURCE_1.json", "pointer": "/wrong"}]},
                "CLAIM_EVIDENCE_UNRESOLVED",
            ),
            (2, {"classification": "SOURCE_DECLARED"}, "CLAIM_EVIDENCE_CLASSIFICATION_CONFLICT"),
            (3, {"classification": "SOURCE_DECLARED"}, "CLAIM_EVIDENCE_CLASSIFICATION_CONFLICT"),
            (
                4,
                {"classification": "CANDIDATE_ENGINEERING"},
                "CLAIM_EVIDENCE_CLASSIFICATION_CONFLICT",
            ),
        ):
            with self.subTest(index=index, patch=patch):
                record = deepcopy(self.record)
                record["claims"][index].update(patch)
                result = self.evaluate(record)
                self.assertEqual(result["decision"], "BLOCK")
                self.assertIn(code, [item["code"] for item in result["blocks"]])

    def test_preflight_preserves_prose_and_requires_fresh_byte_bound_approval(self):
        prepare = runpy.run_path(str(ROOT / "scripts/prepare_claim_record.py"))["prepare_record"]
        draft = deepcopy(self.record)
        draft["deliverables"]["prd"] = draft["deliverables"]["prd"]["Review"] + "\n\nDraft context."
        raw = self.gate["json_bytes"](draft)
        prepared, report = prepare(self.package, raw)
        self.assertEqual((prepared, report), prepare(self.package, raw))
        record = json.loads(prepared)
        self.assertEqual(record["deliverables"]["prd"], {"Review": draft["deliverables"]["prd"]})
        self.assertEqual(report["decision"], "REVIEW_REQUIRED")
        self.assertFalse(report["blocks"])
        self.assertEqual(report["record_sha256"], sha256(prepared).hexdigest())
        self.assertTrue(all(claim["disposition"] == "UNREVIEWED" for claim in record["claims"]))
        for claim in record["claims"]:
            claim["disposition"] = "APPROVED"
        self.assertEqual(
            self.evaluate(record, digest=report["record_sha256"])["decision"], "REVIEW_REQUIRED"
        )
        self.assertEqual(self.evaluate(record)["decision"], "PASS")

    def test_preflight_retains_citation_and_prose_defects(self):
        prepare = runpy.run_path(str(ROOT / "scripts/prepare_claim_record.py"))["prepare_record"]
        draft = deepcopy(self.record)
        name, (text, code) = next(iter(NEGATIVES.items()))
        draft["deliverables"][name] = draft["deliverables"][name]["Review"] + "\n\n" + text
        draft["claims"][0]["evidence"][0]["pointer"] = "/wrong"
        prepared, report = prepare(self.package, self.gate["json_bytes"](draft))
        self.assertEqual(report["decision"], "BLOCK")
        self.assertEqual(
            {item["code"] for item in report["blocks"]},
            {code, "CLAIM_EVIDENCE_UNRESOLVED", "CLAIM_EVIDENCE_CLASSIFICATION_CONFLICT"},
        )
        self.assertEqual(
            json.loads(prepared)["deliverables"][name]["Review"], draft["deliverables"][name]
        )
        draft["manifest_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "REVIEW_MANIFEST_SHA256_MISMATCH"):
            prepare(self.package, self.gate["json_bytes"](draft))
