---
name: sas-architect
description: Compare the draft native Python and Spark designs for the fixed public SAS workflow. Use to connect dependency constraints and behavioral controls to conditional design choices and missing proof.
---

Use one [manifest-bound package](../../examples/offline-review/MANIFEST.json) from [review_workflow.py](../../scripts/review_workflow.py). Read [ARCHITECTURE.md](../../examples/offline-review/ARCHITECTURE.md), [ADR_NATIVE.md](../../examples/offline-review/ADR_NATIVE.md), [ADR_SPARK.md](../../examples/offline-review/ADR_SPARK.md) and [DECISION_REVIEW.md](../../examples/offline-review/DECISION_REVIEW.md). Follow their links into [EVIDENCE.md](../../examples/offline-review/EVIDENCE.md) and the full [TIEOUT.json](../../examples/offline-review/TIEOUT.json).

For a fresh run, read every named document from that output directory. Links above locate the checked-in example.

1. Trace the actual subject. E4 DATA and E2 ORDER bind the sorted intermediate to its consumer. E3 STATE is a conservative BY annotation. O2 fact 3 reads the current value for division. Keep the represented edge and the separate question of cross-row value dependence visible. Runtime ordering needs additional proof.
2. Interpret controls per case and boundary. An expected FAIL means an injected defect was caught. B12 rejected a validator that forbade a legal permutation within a final SQL batch. B04 exercised one two-chunk split of a scalar calculation. Safe partitioning and group-state continuity still require proof. B17 passes only for O1–O3. The include's effects remain UNKNOWN.
3. Use one tie-out for both candidates covering the full intermediate key sequence and multiplicity, the actual SORT stream consumed by SET, duplicate join fan-out, missing arithmetic, and per-batch final row multisets. For Python, ask whether the intermediate and join fit workstation memory. For Spark, ask how order, group state and row multiplicity survive exchanges and retries. Leave special missings, host-dependent precision, representative size, hardware, cost and timing open where evidence is absent.
4. Return a short decision note giving the obligation, original operation/edge/fact or source span, case ID and verdict, implication for each candidate, then the next test or human decision. Keep notes outside the package. Use [downstream compatibility](../../docs/COMPATIBILITY.md) only as a read-only reference.

Stop if evidence or case outcomes disagree with the bound package. Keep production selection BLOCKED. Do not produce a schedule, speedup estimate, benchmark, SAS/Spark execution or downstream handoff. Native Windows evidence I/O remains BLOCKED.

```text
artifact_authority: DRAFT
semantic_verification: UNVERIFIABLE
semantic_acceptance: BLOCKED
benchmark_execution: NOT_RUN
```
