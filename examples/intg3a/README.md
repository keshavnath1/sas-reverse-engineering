# INTG-3A pinned public MIG-5 operator review

Use the existing Python 3.12 development environment from the checkout
root. This opt-in route uses the checked-in public preparation and
population fragments, cases and scenario suite. It regenerates the exact
SM-3B six-rule and SQL-2 source evidence with the existing analyzers and
checks the MIG-5 pins before writing a review subject.

```bash
python3.12 -IB scripts/review_mig5.py prepare \
  --destination /tmp/sas-re-intg3a-review-example
```

Use an unused scratch name for each destination. On macOS use the
physical `/private/tmp` path when reading a generated package. On Linux
use `/tmp`. The versioned `public-mig5-review/1` manifest binds the evidence
and review report bytes, original source identities, public cases, scenario
suite and candidate implementation. It describes a public engineering
subject with unestablished SAS dataset continuity.

Open a real Copilot Agent session manually. Supply the manifest, both
`PREPARATION_EVIDENCE.json` and `POPULATION_EVIDENCE.json`, and their
`PREPARATION.md` and `POPULATION.md` reports from this exact package.
Include the pinned public sources and scenario definitions for context.
Ask for reconstruction, PRD, dependency analysis, verification plan and
ADR. Ask Copilot to cite actual record pointers and preserve the boundary
between SAS declarations, unresolved runtime behavior and Python choices.
The report anchors refer to the original source byte coordinates.

Save the complete deliverables and material claims outside the package
using the [existing GATE-1 record and approval contract](../gate1/README.md).
Use the SHA-256 of this subject's `MANIFEST.json` in the claim record.
The [claim preflight](../gate1/README.md#prepare-a-copilot-draft-for-review)
can wrap flat deliverables, prepare unreviewed claims and show GATE-1
findings before human review.
GATE-1 requires a source declaration claim from each evidence file.
For example, cite a preparation rule at
`/declared_operation/status_rule_recovery/rules/0/predicate` in
`PREPARATION_EVIDENCE.json`. For SQL-2, cite an existing
`/interval_effects/findings/<index>/sql_declaration` or
`/interval_effects/findings/<index>/gate_declaration` in
`POPULATION_EVIDENCE.json`. Resolve the actual index from the bound file.
The manifest's `/sas_dataset_continuity` is `UNRESOLVED` claim evidence.
Its `/candidate_scope`, `/scenario`, and authority statuses are
`PACKAGE_METADATA`.

A human reviewer must inspect both exact evidence files, the full prose,
the completeness of the claims, and the candidate assumptions. The gate
checks citations and dispositions. The operator supplies evidence of any
live Agent session and the reviewer supplies their own decision. Record
dispositions, then bind approval to the SHA-256 of the final claim record
bytes. The record's manifest digest binds that approval to the review
subject. An edited record needs fresh approval.

```bash
python3.12 -IB scripts/review_mig5.py continue \
  --package /private/tmp/sas-re-intg3a-review-example \
  --record /private/tmp/claims.json --approval /private/tmp/approval.json \
  --destination /tmp/sas-re-intg3a-migration-example
```

Omit approval to check the record before human approval. GATE-1
`REVIEW_REQUIRED` exits 1 and `BLOCK` exits 2. Both leave the destination
absent. On `PASS` the operator command verifies the subject again and
runs the existing MIG-5 builder on the two pinned evidence files.

Candidate `PROCEED` and `BLOCK` describe Python scenario outcomes.
The package retains ordered preparation decisions, population audits and
gate diagnostics for both. `VALIDATION.json` compares against public
engineering expectations, including expected blocks. A failed comparison
exits 1 and preserves its diagnostics. `CANDIDATE_MANIFEST.json` preserves
the standalone MIG-5 manifest bytes. The outer manifest binds the approval,
subject, scenario suite and output bytes. The route ends at the population
gates. SAS semantic verification remains `UNVERIFIABLE` and acceptance
`BLOCKED`.

The [MIG-2 operator command](../intg1/README.md) still uses its existing
arguments and output schema. Fresh MIG-2 manifests record the new
GATE-1 implementation digest. Previously published manifests retain
their original bytes.

## Include SORT, CSV and fixed-coefficient scoring

Use the same operator command with an explicit scenario when preparing a
review subject. The versioned `public-mig5-downstream-review/1` subject
binds that scenario, the public model source and recovered declarations,
the exact mapping and coefficient files, and both downstream runners.
The existing preparation and population evidence is still required.

```bash
python3.12 -IB scripts/review_mig5.py prepare --scenario passes \
  --destination /tmp/sas-re-intg3a-branches-review
```

In addition to the preparation and population files, supply Copilot the
bound `MODEL_EVIDENCE.json`, `MAPPING.json`, and `COEFFICIENTS.json` from the
same subject. Include the public model source listed in the manifest.
GATE-1 requires a source declaration citation from the model evidence
as well. One example is `/declared_operation/model/response`. The mapping
and coefficient files support candidate engineering claims. Keep the
reference coding, event policy and fixed coefficients separate from SAS
runtime behavior. The Copilot session and human review are manual.

Use the same `continue` command with the new review package, its claim
record, an exact-byte approval, and a fresh output destination. The
scenario comes from the approved manifest. A different scenario requires
its own review subject and approval. Choices are `passes`, `guard_disabled`,
`empty`, `duplicates`, `count_mismatch`, and `invalid_identifier`.

When the selected scenario returns `PROCEED`, MIG-6 sorts and exports all
19 business fields. The CSV preserves the candidate's header, order,
quoting, padding and LF policy. The case identifier stays in diagnostic
evidence and is absent from sorted rows and CSV. MOD-2 reads the same
eligible records in their original pre-sort order and writes its design
and fixed scores. The output includes each branch's plan and engineering
validation. Model fitting remains `NOT_RUN`.

When the selected scenario blocks or refuses input, the package contains
only MIG-5 diagnostics and approval records. GATE-1 refusal or any evidence
identity mismatch prevents publication altogether. Repeat the same
approved command in another fresh destination to compare output bytes.
