---
name: sas-analyze
description: Assess SAS dependencies, state and optimization opportunities using the selected evidence package.
---

# sas-analyze

1. Use the supplied graph or TRACE/MAP and any existing diagnostic output.
   Resolve operation and edge references. Distinguish data, order, state and
   resource constraints from runtime behavior.
2. Identify where preparation, materialization, filtering, sorting, joining
   or partitioning might change values, order, multiplicity or side effects.
   Missing edges leave independence unproved. Require evidence of version
   continuity and state handling before proposing a safe split.
3. Return each proposed optimization with its cited constraint, expected
   benefit as a hypothesis, correctness obligations and the evidence needed
   to measure it. Keep scheduling and performance claims conditional.

Follow the [repository rules](../../AGENTS.md). Use the selected authorized
package and cite its evidence. Keep drafts DRAFT, verification UNVERIFIABLE,
acceptance BLOCKED, and unperformed execution NOT_RUN.

## Reference material

For the original offline example, see [`MANIFEST.json`](../../examples/offline-review/MANIFEST.json), [`EVIDENCE.md`](../../examples/offline-review/EVIDENCE.md), [`ARCHITECTURE.md`](../../examples/offline-review/ARCHITECTURE.md), [`DECISION_REVIEW.md`](../../examples/offline-review/DECISION_REVIEW.md).
For its related technical details, see [_dependency_diagnostics.py](../../src/sas_re/_dependency_diagnostics.py), [P3_A1_DESIGN.md](../../docs/P3_A1_DESIGN.md).
