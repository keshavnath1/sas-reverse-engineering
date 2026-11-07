---
name: sas-architect
description: Compare the draft native Python and Spark designs for either approved public SAS workflow. Use to connect dependency constraints and behavioral controls to conditional design choices and missing proof.
---

Review one existing [manifest-bound package](../../examples/offline-review/MANIFEST.json) or a requested fresh output of [review_workflow.py](../../scripts/review_workflow.py). Read [ARCHITECTURE.md](../../examples/offline-review/ARCHITECTURE.md), [ADR_NATIVE.md](../../examples/offline-review/ADR_NATIVE.md), [ADR_SPARK.md](../../examples/offline-review/ADR_SPARK.md) and, when manifest-listed, [DECISION_REVIEW.md](../../examples/offline-review/DECISION_REVIEW.md). Follow their links into [EVIDENCE.md](../../examples/offline-review/EVIDENCE.md) and any manifest-listed [TIEOUT.json](../../examples/offline-review/TIEOUT.json).

For a fresh run, read every named document from that output directory. Links above locate the checked-in example.

1. Trace the selected subject, graph, source spans and module ownership. Interpret its actual DATA, ORDER, STATE and RESOURCE records. MVP-2 E3 is conservative BY state with current-row division. The stateful fixture represents retained accumulation and explicit resets. Assess value lineage alongside state effects before proposing any split.
2. Inspect evidence availability first. The stateful manifest declares behavioral_evidence UNAVAILABLE and omits tie-out and decision reports. Continue a draft review using source evidence, ADRs and explicit missing-reference obligations. The legacy MVP-2 manifest identifies available reports in its files map. Only that fixture uses the 17 MVP-3 cases, including B04/B12/B17. Reconcile expected and observed verdicts, matches_specification, discrepancies and scope before citing controls. Expected negative-control FAIL is deliberate defect detection.
3. Use the selected ADR matrix and any available decision review to compare both candidates against the same correctness obligations. Hand-authored expectations without an approved behavioral report remain reference material requiring a future tie-out. For Python, assess workstation memory and local order preservation. For Spark, assess order, state and multiplicity across exchanges and retries. Retain the matrix's open numerical, missing-value and performance obligations.
4. Return a short decision note giving the obligation, original operation/edge/fact or source span, case ID and verdict, implication for each candidate, then the next test or human decision. Notes may be returned directly in chat or separately from the generated package. Report file-guided use, Codex discovery, typed skill loading and completed model execution only as individually observed. Use [downstream compatibility](../../docs/COMPATIBILITY.md) only as a read-only reference.

Stop if required evidence or declared available cases are missing, duplicated, mismatched or disagree with the bound package. Reject unavailable evidence accompanied by purported passing results. Keep production selection BLOCKED. Do not produce a schedule, speedup estimate, benchmark, SAS/Spark execution or downstream handoff. Native Windows evidence I/O remains BLOCKED.

```text
artifact_authority: DRAFT
semantic_verification: UNVERIFIABLE
semantic_acceptance: BLOCKED
benchmark_execution: NOT_RUN
```
