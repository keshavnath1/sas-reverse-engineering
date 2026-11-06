# Draft module specifications

UNVERIFIED · public synthetic draft

```text
artifact_authority: DRAFT
semantic_verification: UNVERIFIABLE
semantic_acceptance: BLOCKED
benchmark_execution: NOT_RUN
```

Graph SHA-256 `385423530208b08635de832bed57698b7278490f2cb7a43f08fd754b80df9155` · preview `mvp1-draft-preview/1` · diagnostics `p3-a1-dependency-diagnostics/1`

## Module `main`

### O1 · PROC_SORT

**OBSERVATION** [O1](EVIDENCE.md#o1) reads `work.a` and writes `work.sorted`. Incident edge references: [E2](EVIDENCE.md#e2), [E3](EVIDENCE.md#e3).

**OBSERVATION** The graph records the following facts, in fact-index order.

- Fact 0 · Sort `work.a` into `work.sorted` by `key`, `subkey`. (`synthetic:main.sas` lines 3–3, bytes [87, 101))

**OBSERVATION** Order `ASCENDING_KEYS`, keys `key`, `subkey`, input precondition `NOT_REQUIRED`, tie order `UNSPECIFIED`. Cardinality rule `SORT_PRESERVES_ROWS`.

**OBSERVATION** Numeric representation `SAS_NUMERIC_8`, missing order `ORDINARY_MISSING_BELOW_FINITE`, arithmetic `PROPAGATE_EXCEPT_SUM_STATEMENT`, expression order `SOURCE_TREE_NO_REASSOCIATION`. Runtime equivalence `NOT_ASSERTED`.

**HYPOTHESIS** Candidate validation: Compare the input/output row multiset, counts and the full composite key sequence. Challenge equal keys and ordinary numeric missing keys separately.

### O2 · DATA_STEP

**OBSERVATION** [O2](EVIDENCE.md#o2) reads `work.sorted` and writes `work.final`. Incident edge references: [E1](EVIDENCE.md#e1), [E2](EVIDENCE.md#e2), [E3](EVIDENCE.md#e3).

**OBSERVATION** The graph records the following facts, in fact-index order.

- Fact 0 · Output dataset `work.final`. (`synthetic:main.sas` lines 5–5, bytes [107, 123))
- Fact 1 · SET reads `work.sorted`. (`synthetic:main.sas` lines 6–6, bytes [124, 139))
- Fact 2 · BY keys in declared order: `key`, `subkey` (ascending). (`synthetic:main.sas` lines 7–7, bytes [141, 154))
- Fact 3 · Assignment: `y = (x / 2)`. (`synthetic:main.sas` lines 8–8, bytes [156, 165))

**OBSERVATION** Order `INPUT_ORDER`, keys `key`, `subkey`, input precondition `SOURCE_SORT`, tie order `UNSPECIFIED`. Cardinality rule `INPUT_ROWS_OR_SUBSET`.

**OBSERVATION** Numeric representation `SAS_NUMERIC_8`, missing order `ORDINARY_MISSING_BELOW_FINITE`, arithmetic `PROPAGATE_EXCEPT_SUM_STATEMENT`, expression order `SOURCE_TREE_NO_REASSOCIATION`. Runtime equivalence `NOT_ASSERTED`.

**OBSERVATION** Fact 2 records BY state, initialization `GROUP_FLAGS`, persistence `BY_KEY_PREFIX` and reset `KEY_PREFIX_CHANGE`.

**HYPOTHESIS** Candidate validation: Trace first and last rows of each key prefix, equal keys and a group split at a chunk boundary. Compare derived values for finite and missing inputs with a separately justified tolerance.

**OBSERVATION** 0 unresolved issue record(s) apply here or globally. The [evidence summary](EVIDENCE.md#proof-obligations) identifies the bindings.

**ASSUMPTION** Effects outside represented facts, unsupported constructs, physical dataset versions and behavior across partitions still need source-aware review.
