---
name: sas-architect
description: Compare the draft native Python and Spark designs for the fixed public SAS workflow. Use to connect dependency constraints and behavioral controls to conditional design choices and missing proof.
---

Review one existing [manifest-bound package](../../examples/offline-review/MANIFEST.json) or a requested fresh output of [review_workflow.py](../../scripts/review_workflow.py). Read [ARCHITECTURE.md](../../examples/offline-review/ARCHITECTURE.md), [ADR_NATIVE.md](../../examples/offline-review/ADR_NATIVE.md), [ADR_SPARK.md](../../examples/offline-review/ADR_SPARK.md) and [DECISION_REVIEW.md](../../examples/offline-review/DECISION_REVIEW.md). Follow their links into [EVIDENCE.md](../../examples/offline-review/EVIDENCE.md) and the full [TIEOUT.json](../../examples/offline-review/TIEOUT.json).

For a fresh run, read every named document from that output directory. Links above locate the checked-in example.

1. Trace the actual subject. E4 DATA and E2 ORDER bind the sorted intermediate to its consumer. E3 STATE is a conservative BY annotation. O2 fact 3 reads the current value for division. Keep the represented edge and the separate question of cross-row value dependence visible. Runtime ordering needs additional proof.
2. Before using controls, reconcile all 17 case IDs against the bound decision review. Require each `verdict` to equal `expected_verdict` and `matches_specification` to be true. Check discrepancy details and modeled scope against the case explanation. An expected FAIL records deliberate defect detection. Carry UNVERIFIABLE outcomes and case-specific limits into the review. Use the decision review's explanations of B04, B12 and B17 when assessing partitioning, validator behavior and the unresolved include.
3. Use the existing decision-review matrix to compare both candidates against the same tie-out obligations. For Python, assess workstation memory and local order preservation. For Spark, assess order, state and multiplicity across exchanges and retries. Retain the matrix's open numerical, missing-value and performance obligations.
4. Return a short decision note giving the obligation, original operation/edge/fact or source span, case ID and verdict, implication for each candidate, then the next test or human decision. Notes may be returned directly in chat or separately from the generated package. Report file-guided use, Codex discovery, typed skill loading and completed model execution only as individually observed. Use [downstream compatibility](../../docs/COMPATIBILITY.md) only as a read-only reference.

Stop if required evidence or cases are missing, duplicated, mismatched or disagree with the bound package. Keep production selection BLOCKED. Do not produce a schedule, speedup estimate, benchmark, SAS/Spark execution or downstream handoff. Native Windows evidence I/O remains BLOCKED.

```text
artifact_authority: DRAFT
semantic_verification: UNVERIFIABLE
semantic_acceptance: BLOCKED
benchmark_execution: NOT_RUN
```
