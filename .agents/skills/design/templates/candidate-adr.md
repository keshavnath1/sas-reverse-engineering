# <decision>: <candidate strategy>

**Architecture:** DRAFT · **Runtime:** NOT_SELECTED · **Human approval:** NOT_APPROVED
**Semantic/parity/performance checks:** NOT_RUN

## Context and recommendation

Cite source O/D/U IDs and original spans; distinguish supported opportunity, assumption and unmeasured bottleneck. State the conditional recommendation, not a selected decision.

## Design and alternatives

Link ARCHITECTURE.md HLD/LLD. Summarize algorithm/partition/key/order/state/materialization changes and native Python/PySpark/Ray/Dask fit or exclusions; mention Cython only if justified. Assess dependencies, mutable state, side effects, transfer/scheduling/memory/recovery costs and unknowns.

## Preserved invariants and proof obligations

Cite formulas, filters, missing semantics, multiplicity, order/group/model/output invariants. Separate correctness obligations from performance hypotheses; refer to VALIDATION_PLAN.md for future human choices. Missing edges are not independence proof.

## Consequences and human decisions

State tradeoffs, unresolved evidence, reversal/rollback idea (not implemented), and human-owned scope, architecture, tolerance, execution and release decisions. Recommendation is not approval.
