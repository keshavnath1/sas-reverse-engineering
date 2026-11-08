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

For the original offline example, see [`MANIFEST.json`](../../tests/fixtures/source-reconstruction/offline-review-package/MANIFEST.json), [`EVIDENCE.md`](../../tests/fixtures/source-reconstruction/offline-review-package/EVIDENCE.md), [`ARCHITECTURE.md`](../../tests/fixtures/source-reconstruction/offline-review-package/ARCHITECTURE.md), [`DECISION_REVIEW.md`](../../tests/fixtures/source-reconstruction/offline-review-package/DECISION_REVIEW.md).
For its related technical details, see [_dependency_diagnostics.py](../../src/sas_re/_review/_dependency_diagnostics.py), [DEPENDENCY_ANALYSIS_DESIGN.md](../../docs/DEPENDENCY_ANALYSIS_DESIGN.md).
