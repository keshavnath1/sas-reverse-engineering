# GATE-1 evidence-claim acceptance contract

Use the existing POSIX development installation and a public two-source
INT-3 review directory. The gate reads the supplied record and package and
writes a deterministic JSON decision to stdout.

```bash
python3.12 -IB scripts/review_claim_gate.py \
  --package /private/tmp/example-review \
  --record /private/tmp/claims.json
```

Use physical paths on macOS. An optional `--approval` points to a separate
operator decision.

The version 1 record has four keys.

| Key | Content |
| --- | --- |
| `version` | Integer `1`. |
| `manifest_sha256` | SHA-256 of the exact existing review manifest. |
| `deliverables` | Five objects named `reconstruction`, `prd`, `dependency_analysis`, `verification_plan` and `adr`. Each maps section names to the full text for that section, including narrative, lists and tables. |
| `claims` | List of material claims with stable IDs, exact text from their sections, classifications, evidence references and dispositions. |

A claim can have this shape. The evidence field uses a file name and pointer
into a JSON record from the bound review.

```json
{
  "id": "HANDOFF-01",
  "text": "Matching names support a potential cross-file handoff.",
  "classification": "INFERRED",
  "evidence": [{"file": "MANIFEST.json", "pointer": "/cross_file_dependencies/0/classification"}],
  "deliverable": "dependency_analysis",
  "section": "Handoff",
  "disposition": "UNREVIEWED"
}
```

`SOURCE_DECLARED` refers to an individual source operation declaration.
`INFERRED` describes relationships derived from source records. `UNRESOLVED`
covers unobserved behavior, including runtime lineage and dataset continuity.
`CANDIDATE_ENGINEERING` covers Python behavior or assumptions. Its source
citations may provide context, with the reviewer responsible for checking
candidate-specific support. `PACKAGE_METADATA` covers manifest status fields.

Before approval, the reviewer checks that the submitted sections reproduce
the deliverables, that the claim list covers all material claims, and that
the exact prose and citations support each classification. The reviewer
records `APPROVED`, `REJECTED`, or `UNREVIEWED` per claim. To approve the
submission, pass a separate JSON object with `record_sha256` set to the digest
of the final record bytes, `reviewer` set to the reviewer label and
`decision` set to `APPROVED`. Reviewer identity and decision are operator
assertions.

| Decision | Exit | Meaning |
| --- | --- | --- |
| `PASS` | 0 | Bounded checks passed, all claims have approved dispositions, and explicit approval binds the exact record. |
| `REVIEW_REQUIRED` | 1 | Human approval, claim disposition, or deliverable claim coverage is incomplete. |
| `BLOCK` | 2 | A known contradiction, invalid binding, missing or unresolved citation, conflicting classification, or rejected claim prevents approval. |

The gate checks manifest and payload identities, source record identity,
claim placement, citation resolution and bounded classification rules.
It scans all submitted prose for the three retained phrases, including
prose absent from the claim list. The phrase rules are specific to the
known failures and can also flag quoted instances of those phrases.
The gate relies on human review for paraphrases, omitted prose, semantic
support and reviewer authority. A resolvable pointer does not establish
that the cited record entails the claim.

The retained controls come from E2E-2's dependency analysis and the wording
that survived E2E-3 in reconstruction and the ADR. The positive control
keeps the producer and reader declarations separate, labels the potential
handoff inferred, and keeps runtime lineage unresolved. Acceptance here
applies to the submitted review. SAS verification stays UNVERIFIABLE and
SAS acceptance stays BLOCKED.
