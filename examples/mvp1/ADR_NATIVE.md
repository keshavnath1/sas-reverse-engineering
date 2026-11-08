# Candidate ADR · Native Python

UNVERIFIED · public synthetic draft

```text
artifact_authority: DRAFT
semantic_verification: UNVERIFIABLE
semantic_acceptance: BLOCKED
benchmark_execution: NOT_RUN
```

Graph SHA-256 `385423530208b08635de832bed57698b7278490f2cb7a43f08fd754b80df9155` · preview `mvp1-draft-preview/1` · diagnostics `p3-a1-dependency-diagnostics/1`

## Decision under review

**HYPOTHESIS** Use native Python as the comparison baseline. Model named datasets as local row sequences, order with an explicit composite-key comparator, and carry BY state through a single ordered scan where required. Expose intermediate rows for inspection.

**HYPOTHESIS** A local representation may simplify tie-out and avoid transfer costs. Row objects, sorting scratch space and the intermediate may exceed workstation memory. Bound input plus sort workspace before any trial.

## Source-to-candidate mapping

**HYPOTHESIS** [O1](EVIDENCE.md#o1) (PROC_SORT). Test a local sort with an explicit missing-key comparator and tie policy. Compare the input/output row multiset, counts and the full composite key sequence. Challenge equal keys and ordinary numeric missing keys separately.

**HYPOTHESIS** [O2](EVIDENCE.md#o2) (DATA_STEP). Test a row-by-row reference with explicit missing values and group reset rules. Trace first and last rows of each key prefix, equal keys and a group split at a chunk boundary. Compare derived values for finite and missing inputs with a separately justified tolerance.

**HYPOTHESIS** For [E1](EVIDENCE.md#e1) (STATE): Compare the state immediately before and after an input chunk boundary. Change the leading key while the trailing key repeats. Split a group across two chunks and compare its boundary rows to a single uninterrupted reference scan.

**HYPOTHESIS** For [E2](EVIDENCE.md#e2) (ORDER): Challenge tied rows and confirm the candidate satisfies the declared ordering requirement.

**HYPOTHESIS** For [E3](EVIDENCE.md#e3) (DATA): Compare the intermediate row multiset at the handoff before comparing the final values.

## Common tie-out and benchmark proposal

**ASSUMPTION** An owner must supply the input population, versioned output reference, key/duplicate policy, treatment of tied rows and numerical tolerance. P2B semantic review and human selection are outstanding.

**HYPOTHESIS** Use the same hashed cases for both candidates. Compare row counts, multisets per composite key, missing-value placement, order across groups and arithmetic at rounding boundaries. Report discrepancy rows and maximum absolute/relative error. Review unresolved ties separately; avoid manufacturing a tie-breaker.

**HYPOTHESIS** After correctness review and separate benchmark approval, pin versions and hardware; record input bytes, skew, memory budget and cache state. Run one cold and five warm trials per agreed size. Collect end-to-end elapsed time, CPU time and peak memory including sort and I/O; record spill and transferred bytes where applicable.

**HYPOTHESIS** Defer if the largest approved case exceeds the memory budget or the comparator cannot preserve missing-key and group behavior. On a tie-out failure, retain the existing boundary and its reference output; reopen the disputed operation. Neither candidate has a measured result.
