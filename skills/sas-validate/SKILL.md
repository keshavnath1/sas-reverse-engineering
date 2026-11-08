---
name: sas-validate
description: Define engineering checks, tie-out criteria and independent SAS reference obligations for an evidence-backed migration.
---

# sas-validate

1. Establish the exact subject and identify available structural checks,
   public expectations, observed candidate results, and attributable SAS
   evidence. Record checks performed separately from checks proposed.
2. Specify cases for the actual operation boundaries, including keys, types,
   missing values, order, multiplicity, state and numerical tolerances where
   relevant. Explain how each reference output would be bound to a run.
3. Return a validation plan and unresolved obligations. Use observed tie-out
   results only when the selected package contains them. Leave unavailable
   comparisons unverified and require human review of acceptance criteria.

Follow the [repository rules](../../AGENTS.md). Use the selected authorized
package and cite its evidence. Keep drafts DRAFT, verification UNVERIFIABLE,
acceptance BLOCKED, and unperformed execution NOT_RUN.

## Reference material

For the original offline example, see [`MANIFEST.json`](../../examples/offline-review/MANIFEST.json), [`EVIDENCE.md`](../../examples/offline-review/EVIDENCE.md), [`TIEOUT.json`](../../examples/offline-review/TIEOUT.json), [`DECISION_REVIEW.md`](../../examples/offline-review/DECISION_REVIEW.md).
For its related technical details, see [mvp3_cases.py](../../tests/mvp3_cases.py), [mvp3_tieout.py](../../scripts/mvp3_tieout.py), [SYNTHETIC_TIEOUT_VALIDATION.md](../../docs/SYNTHETIC_TIEOUT_VALIDATION.md).
