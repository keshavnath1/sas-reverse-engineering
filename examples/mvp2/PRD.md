# Draft product requirements

UNVERIFIED · public synthetic draft

```text
artifact_authority: DRAFT
semantic_verification: UNVERIFIABLE
semantic_acceptance: BLOCKED
benchmark_execution: NOT_RUN
```

Graph SHA-256 `19f41dea50825469a89d8fc545fee1d87f09af946d130d62de8f946d90b78017` · preview `mvp2-multimodule-preview/1` · diagnostics `p3-a1-dependency-diagnostics/1`

## Scope and proposed objective

**HYPOTHESIS** Use this workflow to define a reproducible transformation and a shared correctness test for candidate replacements. The business purpose and consumers need an owner.

## What the supplied workflow represents

**OBSERVATION** [O1](EVIDENCE.md#o1) (PROC_SORT, module `prepare`) writes `work.ordered`. Sort `work.observations` into `work.ordered` by `batch`, `sequence`. ([O1 fact 0](EVIDENCE.md#o1-fact-0))

**OBSERVATION** [O2](EVIDENCE.md#o2) (DATA_STEP, module `enrich`) writes `work.scaled`. SET reads `work.ordered`. ([O2 fact 1](EVIDENCE.md#o2-fact-1)) BY keys in declared order: `batch`, `sequence` (ascending). ([O2 fact 2](EVIDENCE.md#o2-fact-2)) Assignment: `scaled = (value / 2)`. ([O2 fact 3](EVIDENCE.md#o2-fact-3))

**OBSERVATION** [O3](EVIDENCE.md#o3) (PROC_SQL, module `enrich`) writes `work.adjusted`. FROM `work.scaled` as `s`, `work.offsets` as `r`. INNER JOIN on `s.batch = r.batch`. WHERE `s.scaled > 0`. Project `batch = s.batch`, `adjusted = (s.scaled + r.offset)`. ORDER BY `batch`. ([O3 fact 1](EVIDENCE.md#o3-fact-1))

**OBSERVATION** [O4](EVIDENCE.md#o4) (INCLUDE, module `enrich`) has no listed output node. INCLUDE literal `postcheck.sas`. Target unresolved; effects UNKNOWN. ([O4 fact 0](EVIDENCE.md#o4-fact-0))

## Functional requirements for review

**OBSERVATION** `prepare` [O1](EVIDENCE.md#o1) produces `work.ordered` for `enrich` [O2](EVIDENCE.md#o2) on [E4](EVIDENCE.md#e4).

**OBSERVATION** [O4 fact 0](EVIDENCE.md#o4-fact-0) names `postcheck.sas` without a bound target. Its reads, writes and downstream effects are UNKNOWN.

**ASSUMPTION** Obtain separately authorized target evidence before treating the represented outputs as the complete workflow.

### O1 · PROC_SORT

**OBSERVATION** [O1](EVIDENCE.md#o1) reads `work.observations` and writes `work.ordered` at the dataset level.

**HYPOTHESIS** Require a candidate to reproduce this boundary. Compare the input/output row multiset, counts and the full composite key sequence. Challenge equal keys and ordinary numeric missing keys separately.

### O2 · DATA_STEP

**OBSERVATION** [O2](EVIDENCE.md#o2) reads `work.ordered` and writes `work.scaled` at the dataset level.

**HYPOTHESIS** Require a candidate to reproduce this boundary. Trace first and last rows of each key prefix, equal keys and a group split at a chunk boundary. Compare derived values for finite and missing inputs with a separately justified tolerance.

### O3 · PROC_SQL

**OBSERVATION** [O3](EVIDENCE.md#o3) reads `work.offsets`, `work.scaled` and writes `work.adjusted` at the dataset level.

**HYPOTHESIS** Require a candidate to reproduce this boundary. Compare the projected values, qualifying row multiset and requested order. Challenge duplicate and missing keys, tied output rows and the effect of predicate placement.

### O4 · INCLUDE

**OBSERVATION** [O4](EVIDENCE.md#o4) has no represented dataset accesses. Its effects require further evidence.

**HYPOTHESIS** Require a candidate to reproduce this boundary. Obtain authorized evidence for the target and its effects before accepting workflow completeness.

**INFERENCE** Treat `work.scaled` on [E1](EVIDENCE.md#e1) as a producer/consumer interface. Confirm the exact dataset version at that handoff.
**INFERENCE** Treat `work.ordered` on [E4](EVIDENCE.md#e4) as a producer/consumer interface. Confirm the exact dataset version at that handoff.

## Proposed nonfunctional requirements and open questions

**HYPOTHESIS** Make a run reproducible from fixed input bytes, versions and policy choices. Keep peak memory and elapsed time within budgets a workload owner must supply.

**ASSUMPTION** Who consumes the output? Which population, row key, duplicate policy, tie order and absolute/relative tolerance would they accept? What hardware, data volume and completion window should the alternatives be tested against?

**HYPOTHESIS** Before migration, agree on those answers and an independent reference. Require complete row/key coverage and a discrepancy report against the same acceptance criteria for both candidates.
