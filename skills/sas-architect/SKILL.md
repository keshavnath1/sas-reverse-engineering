---
name: sas-architect
description: Draft HLD, LLD and architecture decisions grounded in SAS evidence and supported candidate contracts.
---

# sas-architect

1. Use the selected reconstruction, requirements and validation findings to
   identify module boundaries, dependencies, interfaces, state ownership and
   unresolved effects. Trace each design decision to the relevant evidence.
2. Draft an HLD and LLD and record meaningful alternatives in ADRs. Compare
   native Python with distributed options such as Spark, Ray or Dask when
   workload evidence justifies it. Explain ordering, partitioning, state,
   resource and validation obligations for each viable option.
3. Check existing candidate contracts before proposing execution. Report gaps
   and keep runtime selection pending until its criteria are met. Return design
   drafts and the decisions requiring human review.

Follow the [repository rules](../../AGENTS.md). Use the selected authorized
package and cite its evidence. Keep drafts DRAFT, verification UNVERIFIABLE,
acceptance BLOCKED, and unperformed execution NOT_RUN.

## Reference material

For the original offline example, see [`ARCHITECTURE.md`](../../examples/offline-review/ARCHITECTURE.md), [`ADR_NATIVE.md`](../../examples/offline-review/ADR_NATIVE.md), [`ADR_SPARK.md`](../../examples/offline-review/ADR_SPARK.md), [`DECISION_REVIEW.md`](../../examples/offline-review/DECISION_REVIEW.md), [`TIEOUT.json`](../../examples/offline-review/TIEOUT.json).
