# Draft product requirements

UNVERIFIED · public synthetic draft

```text
artifact_authority: DRAFT
semantic_verification: UNVERIFIABLE
semantic_acceptance: BLOCKED
benchmark_execution: NOT_RUN
```

Graph SHA-256 `385423530208b08635de832bed57698b7278490f2cb7a43f08fd754b80df9155` · preview `mvp1-draft-preview/1` · diagnostics `p3-a1-dependency-diagnostics/1`

## Scope and proposed objective

**HYPOTHESIS** Use this workflow to define a reproducible transformation and a shared correctness test for candidate replacements. The business purpose and consumers need an owner.

## What the supplied workflow represents

**OBSERVATION** [O1](EVIDENCE.md#o1) (PROC_SORT) writes `work.sorted`. Sort `work.a` into `work.sorted` by `key`, `subkey`. (fact 0)

**OBSERVATION** [O2](EVIDENCE.md#o2) (DATA_STEP) writes `work.final`. SET reads `work.sorted`. (fact 1) BY keys in declared order: `key`, `subkey` (ascending). (fact 2) Assignment: `y = (x / 2)`. (fact 3)

## Functional requirements for review

### O1 · PROC_SORT

**OBSERVATION** [O1](EVIDENCE.md#o1) reads `work.a` and writes `work.sorted` at the dataset level.

**HYPOTHESIS** Require a candidate to reproduce this boundary. Compare the input/output row multiset, counts and the full composite key sequence. Challenge equal keys and ordinary numeric missing keys separately.

### O2 · DATA_STEP

**OBSERVATION** [O2](EVIDENCE.md#o2) reads `work.sorted` and writes `work.final` at the dataset level.

**HYPOTHESIS** Require a candidate to reproduce this boundary. Trace first and last rows of each key prefix, equal keys and a group split at a chunk boundary. Compare derived values for finite and missing inputs with a separately justified tolerance.

**INFERENCE** Treat `work.sorted` on [E3](EVIDENCE.md#e3) as a producer/consumer interface. Confirm the exact dataset version at that handoff.

## Proposed nonfunctional requirements and open questions

**HYPOTHESIS** Make a run reproducible from fixed input bytes, versions and policy choices. Keep peak memory and elapsed time within budgets a workload owner must supply.

**ASSUMPTION** Who consumes the output? Which population, row key, duplicate policy, tie order and absolute/relative tolerance would they accept? What hardware, data volume and completion window should the alternatives be tested against?

**HYPOTHESIS** Before migration, agree on those answers and an independent reference. Require complete row/key coverage and a discrepancy report against the same acceptance criteria for both candidates.
