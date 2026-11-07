# Candidate ADR · Spark

UNVERIFIED · public synthetic draft

```text
artifact_authority: DRAFT
semantic_verification: UNVERIFIABLE
semantic_acceptance: BLOCKED
benchmark_execution: NOT_RUN
```

Graph SHA-256 `19f41dea50825469a89d8fc545fee1d87f09af946d130d62de8f946d90b78017` · preview `mvp2-multimodule-preview/1` · diagnostics `p3-a1-dependency-diagnostics/1`

## Decision under review

**HYPOTHESIS** Consider Spark only if measured input and intermediate sizes exceed an approved single-workstation resource budget. A partitioned representation might accommodate larger inputs but adds shuffle, spill, serialization and key-skew costs.

**HYPOTHESIS** Evaluate a keyed exchange, explicit sort and row transformation. Check global key sequence on output and continuity of every affected group at exchange boundaries. Local partition sorting alone cannot establish the required end-to-end order.

## Decision matrix

**HYPOTHESIS** Both candidates require the same correctness reference. UNKNOWN marks evidence still needed to compare them.

| Criterion | Evidence and open question | Native Python hypothesis | Spark hypothesis |
|---|---|---|---|
| Workload size | [O1](EVIDENCE.md#o1), [O2](EVIDENCE.md#o2), [O3](EVIDENCE.md#o3), [O4](EVIDENCE.md#o4). Production rows, bytes and skew: UNKNOWN. | Size a single-host trial including the intermediate. | Consider distribution only if measured scale warrants it. |
| Ordering | ORDER: [E2](EVIDENCE.md#e2). SQL output: [O3 fact 1](EVIDENCE.md#o3-fact-1) by `batch`. Acceptable order among ties: UNKNOWN. | Check the full key comparator and missing-key placement. | Check ordering after exchanges and at consumption. |
| Partition boundaries | STATE: [E3](EVIDENCE.md#e3). Safe split keys: UNKNOWN. | Compare chunk boundaries with one continuous scan. | Vary partition count and split a tied group; compare boundary rows. |
| Memory | DATA: [E1](EVIDENCE.md#e1), [E4](EVIDENCE.md#e4). Peak bytes, headroom and spill: UNKNOWN. | Budget input, sort scratch and join multiplicity. | Budget per-worker skew, shuffle buffers and spill. |
| Data movement | Logical handoffs: [E1](EVIDENCE.md#e1), [E4](EVIDENCE.md#e4). Physical transfers: UNKNOWN. | Measure local intermediate materialization. | Measure repartition and serialization bytes before proposing reuse. |
| Operations | Workflow: [O1](EVIDENCE.md#o1), [O2](EVIDENCE.md#o2), [O3](EVIDENCE.md#o3), [O4](EVIDENCE.md#o4). Operator capacity, recovery budget and supported deployment: UNKNOWN. | Test local restart at the intermediate. | Test retry and duplicate-output handling; identify a runtime owner. |
| Validation obligations | Review [O3 fact 1](EVIDENCE.md#o3-fact-1) and the [proof obligations](EVIDENCE.md#proof-obligations). Independent reference and tolerances: UNKNOWN. | Trace duplicates, missing keys and filtering against an independent reference. | Use the same reference across partitions and retries; reconcile row multisets before timing. |

**OBSERVATION** [O4 fact 0](EVIDENCE.md#o4-fact-0) names `postcheck.sas` without a bound target. Its reads, writes and downstream effects are UNKNOWN.

**ASSUMPTION** Obtain separately authorized target evidence before treating the represented outputs as the complete workflow.


## Source-to-candidate mapping

**HYPOTHESIS** [O1](EVIDENCE.md#o1) (PROC_SORT). Test an explicit distribution and sort policy for the full key. Compare the input/output row multiset, counts and the full composite key sequence. Challenge equal keys and ordinary numeric missing keys separately.

**HYPOTHESIS** [O2](EVIDENCE.md#o2) (DATA_STEP). Test row expressions and ordered state across partition boundaries. Trace first and last rows of each key prefix, equal keys and a group split at a chunk boundary. Compare derived values for finite and missing inputs with a separately justified tolerance.

**HYPOTHESIS** [O3](EVIDENCE.md#o3) (PROC_SQL). Test key redistribution, predicate placement and the output ordering contract. Compare the projected values, qualifying row multiset and requested order. Challenge duplicate and missing keys, tied output rows and the effect of predicate placement.

**HYPOTHESIS** [O4](EVIDENCE.md#o4) (INCLUDE). Keep effects outside the supplied graph open for source review. Obtain authorized evidence for the target and its effects before accepting workflow completeness.

**HYPOTHESIS** For [E1](EVIDENCE.md#e1) (DATA): Compare the intermediate row multiset at the handoff before comparing the final values.

**HYPOTHESIS** For [E2](EVIDENCE.md#e2) (ORDER): Challenge tied rows and confirm the candidate satisfies the declared ordering requirement.

**HYPOTHESIS** For [E3](EVIDENCE.md#e3) (STATE): Compare the state immediately before and after an input chunk boundary. Change the leading key while the trailing key repeats. Split a group across two chunks and compare its boundary rows to a single uninterrupted reference scan.

**HYPOTHESIS** For [E4](EVIDENCE.md#e4) (DATA): Compare the intermediate row multiset at the handoff before comparing the final values.

**HYPOTHESIS** At [O1](EVIDENCE.md#o1) compare `work.ordered` by `batch`, `sequence`. Check the multiset of projected rows within each tied group and the order between groups.

**HYPOTHESIS** At [O2](EVIDENCE.md#o2) compare `work.scaled` by `batch`, `sequence`. Check the multiset of projected rows within each tied group and the order between groups.

**HYPOTHESIS** At [O3](EVIDENCE.md#o3) compare `work.adjusted` by `batch`. Check the multiset of projected rows within each tied group and the order between groups.

## Common tie-out and benchmark proposal

**ASSUMPTION** An owner must supply the input population, versioned output reference, key/duplicate policy, treatment of tied rows and numerical tolerance. P2B semantic review and human selection are outstanding.

**HYPOTHESIS** Use the same hashed cases for both candidates. Use only keys and columns present at each boundary. Report missing rows, unexpected duplicates, discrepancies in tied groups and maximum absolute/relative error at rounding boundaries.

**HYPOTHESIS** After correctness review and separate benchmark approval, pin versions and hardware; record input bytes, skew, memory budget and cache state. Run one cold and five warm trials per agreed size. Collect end-to-end elapsed time, CPU time and peak memory including sort and I/O; record spill and transferred bytes where applicable.

**HYPOTHESIS** Defer unless resource evidence justifies distribution and group-boundary tests pass under different partition counts, skew and retries. On a tie-out failure, retain the existing boundary and its reference output; reopen the disputed operation. Neither candidate has a measured result.
