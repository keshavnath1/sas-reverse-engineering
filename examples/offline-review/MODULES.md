# Draft module specifications

UNVERIFIED · public synthetic draft

```text
artifact_authority: DRAFT
semantic_verification: UNVERIFIABLE
semantic_acceptance: BLOCKED
benchmark_execution: NOT_RUN
```

Graph SHA-256 `19f41dea50825469a89d8fc545fee1d87f09af946d130d62de8f946d90b78017` · preview `mvp2-multimodule-preview/1` · diagnostics `p3-a1-dependency-diagnostics/1`

## Module `prepare`

### O1 · PROC_SORT

**OBSERVATION** [O1](EVIDENCE.md#o1) reads `work.observations` and writes `work.ordered`. Incident edge references: [E2](EVIDENCE.md#e2), [E4](EVIDENCE.md#e4).

**OBSERVATION** The graph records the following facts, in fact-index order.

- [O1 fact 0](EVIDENCE.md#o1-fact-0) · Sort `work.observations` into `work.ordered` by `batch`, `sequence`. (`synthetic:prepare.sas` lines 3–3, bytes [99, 117))

**OBSERVATION** [O1](EVIDENCE.md#o1) · Order `ASCENDING_KEYS`, keys `batch`, `sequence`, input precondition `NOT_REQUIRED`, tie order `UNSPECIFIED`. Cardinality rule `SORT_PRESERVES_ROWS`.

**OBSERVATION** [O1](EVIDENCE.md#o1) · Numeric representation `SAS_NUMERIC_8`, missing order `ORDINARY_MISSING_BELOW_FINITE`, arithmetic `PROPAGATE_EXCEPT_SUM_STATEMENT`, expression order `SOURCE_TREE_NO_REASSOCIATION`. Runtime equivalence `NOT_ASSERTED`.

**OBSERVATION** [O1](EVIDENCE.md#o1) records these value and control inputs.

| Output or control | Input columns | Earlier facts | Input phase | Source fact |
|---|---|---|---|---|
| `work.ordered.batch` | `work.observations.batch` | none listed | `CURRENT_ITERATION` | [O1 fact 0](EVIDENCE.md#o1-fact-0) |
| `work.ordered.sequence` | `work.observations.sequence` | none listed | `CURRENT_ITERATION` | [O1 fact 0](EVIDENCE.md#o1-fact-0) |
| `work.ordered.value` | `work.observations.value` | none listed | `CURRENT_ITERATION` | [O1 fact 0](EVIDENCE.md#o1-fact-0) |

**HYPOTHESIS** Candidate validation: Compare the input/output row multiset, counts and the full composite key sequence. Challenge equal keys and ordinary numeric missing keys separately.

**OBSERVATION** 2 unresolved issue record(s) apply here or globally. The [evidence summary](EVIDENCE.md#proof-obligations) identifies the bindings.

**ASSUMPTION** Effects outside represented facts, unsupported constructs, physical dataset versions and behavior across partitions still need source-aware review.

## Module `enrich`

### O2 · DATA_STEP

**OBSERVATION** [O2](EVIDENCE.md#o2) reads `work.ordered` and writes `work.scaled`. Incident edge references: [E1](EVIDENCE.md#e1), [E2](EVIDENCE.md#e2), [E3](EVIDENCE.md#e3), [E4](EVIDENCE.md#e4).

**OBSERVATION** The graph records the following facts, in fact-index order.

- [O2 fact 0](EVIDENCE.md#o2-fact-0) · Output dataset `work.scaled`. (`synthetic:enrich.sas` lines 2–2, bytes [48, 65))
- [O2 fact 1](EVIDENCE.md#o2-fact-1) · SET reads `work.ordered`. (`synthetic:enrich.sas` lines 3–3, bytes [66, 82))
- [O2 fact 2](EVIDENCE.md#o2-fact-2) · BY keys in declared order: `batch`, `sequence` (ascending). (`synthetic:enrich.sas` lines 4–4, bytes [84, 101))
- [O2 fact 3](EVIDENCE.md#o2-fact-3) · Assignment: `scaled = (value / 2)`. (`synthetic:enrich.sas` lines 5–5, bytes [103, 121))

**OBSERVATION** [O2](EVIDENCE.md#o2) · Order `INPUT_ORDER`, keys `batch`, `sequence`, input precondition `SOURCE_SORT`, tie order `UNSPECIFIED`. Cardinality rule `INPUT_ROWS_OR_SUBSET`.

**OBSERVATION** [O2](EVIDENCE.md#o2) · Numeric representation `SAS_NUMERIC_8`, missing order `ORDINARY_MISSING_BELOW_FINITE`, arithmetic `PROPAGATE_EXCEPT_SUM_STATEMENT`, expression order `SOURCE_TREE_NO_REASSOCIATION`. Runtime equivalence `NOT_ASSERTED`.

**OBSERVATION** [O2 fact 2](EVIDENCE.md#o2-fact-2) records BY state, initialization `GROUP_FLAGS`, persistence `BY_KEY_PREFIX` and reset `KEY_PREFIX_CHANGE`.

**OBSERVATION** [O2](EVIDENCE.md#o2) records these value and control inputs.

| Output or control | Input columns | Earlier facts | Input phase | Source fact |
|---|---|---|---|---|
| `work.scaled.batch` | `work.ordered.batch` | none listed | `CURRENT_ITERATION` | [O2 fact 1](EVIDENCE.md#o2-fact-1) |
| `work.scaled.sequence` | `work.ordered.sequence` | none listed | `CURRENT_ITERATION` | [O2 fact 1](EVIDENCE.md#o2-fact-1) |
| `work.scaled.value` | `work.ordered.value` | none listed | `CURRENT_ITERATION` | [O2 fact 1](EVIDENCE.md#o2-fact-1) |
| `work.scaled.scaled` | `work.ordered.value` | none listed | `CURRENT_ITERATION` | [O2 fact 3](EVIDENCE.md#o2-fact-3) |
| `BY_GROUP` | `work.ordered.sequence`, `work.ordered.batch` | none listed | `STATIC` | [O2 fact 2](EVIDENCE.md#o2-fact-2) |

**INFERENCE** The BY annotation at [O2](EVIDENCE.md#o2) models group flags. It does not establish that an assigned value depends on a previous row. Review the assignment's value lineage separately before proposing any partition boundary.

**HYPOTHESIS** Candidate validation: Trace first and last rows of each key prefix, equal keys and a group split at a chunk boundary. Compare derived values for finite and missing inputs with a separately justified tolerance.

### O3 · PROC_SQL

**OBSERVATION** [O3](EVIDENCE.md#o3) reads `work.offsets`, `work.scaled` and writes `work.adjusted`. Incident edge references: [E1](EVIDENCE.md#e1).

**OBSERVATION** The graph records the following facts, in fact-index order.

- [O3 fact 0](EVIDENCE.md#o3-fact-0) · Output dataset `work.adjusted`. (`synthetic:enrich.sas` lines 8–12, bytes [138, 330))
- [O3 fact 1](EVIDENCE.md#o3-fact-1) · FROM `work.scaled` as `s`, `work.offsets` as `r`. INNER JOIN on `s.batch = r.batch`. WHERE `s.scaled > 0`. Project `batch = s.batch`, `adjusted = (s.scaled + r.offset)`. ORDER BY `batch`. (`synthetic:enrich.sas` lines 8–12, bytes [138, 330))

**OBSERVATION** [O3](EVIDENCE.md#o3) · Order `ASCENDING_KEYS`, keys `batch`, input precondition `NOT_REQUIRED`, tie order `UNSPECIFIED`. Cardinality rule `SQL_JOIN_MULTIPLICITY_OR_SUBSET`.

**OBSERVATION** [O3](EVIDENCE.md#o3) · Numeric representation `SAS_NUMERIC_8`, missing order `ORDINARY_MISSING_BELOW_FINITE`, arithmetic `PROPAGATE_EXCEPT_SUM_STATEMENT`, expression order `SOURCE_TREE_NO_REASSOCIATION`. Runtime equivalence `NOT_ASSERTED`.

**OBSERVATION** [O3](EVIDENCE.md#o3) records these value and control inputs. Value rows may include ON and WHERE inputs. The SELECT expression identifies the arithmetic operands. The numeric missing-key policy is `SAS_ORDINARY_MISSING_EQUALS_MISSING`.

| Output or control | Input columns | Earlier facts | Input phase | Source fact |
|---|---|---|---|---|
| `work.adjusted.batch` | `work.offsets.batch`, `work.scaled.batch`, `work.scaled.scaled` | none listed | `CURRENT_ITERATION` | [O3 fact 1](EVIDENCE.md#o3-fact-1) |
| `work.adjusted.adjusted` | `work.offsets.batch`, `work.scaled.batch`, `work.scaled.scaled`, `work.offsets.offset` | none listed | `CURRENT_ITERATION` | [O3 fact 1](EVIDENCE.md#o3-fact-1) |
| `SQL_ON` | `work.offsets.batch`, `work.scaled.batch` | none listed | `CURRENT_ITERATION` | [O3 fact 1](EVIDENCE.md#o3-fact-1) |
| `SQL_WHERE` | `work.scaled.scaled` | none listed | `CURRENT_ITERATION` | [O3 fact 1](EVIDENCE.md#o3-fact-1) |

**INFERENCE** At [O3 fact 1](EVIDENCE.md#o3-fact-1), multiple rows matching a join key may yield multiple result rows before the WHERE filter, if present. Confirm multiplicity with duplicate and missing keys; no runtime count is available here.
**INFERENCE** [O3 fact 1](EVIDENCE.md#o3-fact-1) orders by `batch`. Relative order within a tied key remains unspecified.

**HYPOTHESIS** Candidate validation: Compare the projected values, qualifying row multiset and requested order. Challenge duplicate and missing keys, tied output rows and the effect of predicate placement.

### O4 · INCLUDE

**OBSERVATION** [O4](EVIDENCE.md#o4) reads none listed and writes none listed. Incident edge references: none listed.

**OBSERVATION** The graph records the following facts, in fact-index order.

- [O4 fact 0](EVIDENCE.md#o4-fact-0) · INCLUDE literal `postcheck.sas`. Target unresolved; effects UNKNOWN. (`synthetic:enrich.sas` lines 14–14, bytes [338, 363))

**OBSERVATION** [O4](EVIDENCE.md#o4) · Order `UNSPECIFIED`, keys none listed, input precondition `NOT_REQUIRED`, tie order `UNSPECIFIED`. Cardinality rule `NOT_APPLICABLE`.

**OBSERVATION** [O4](EVIDENCE.md#o4) · Numeric representation `SAS_NUMERIC_8`, missing order `ORDINARY_MISSING_BELOW_FINITE`, arithmetic `PROPAGATE_EXCEPT_SUM_STATEMENT`, expression order `SOURCE_TREE_NO_REASSOCIATION`. Runtime equivalence `NOT_ASSERTED`.

**HYPOTHESIS** Candidate validation: Obtain authorized evidence for the target and its effects before accepting workflow completeness.

**OBSERVATION** 3 unresolved issue record(s) apply here or globally. The [evidence summary](EVIDENCE.md#proof-obligations) identifies the bindings.

**ASSUMPTION** Effects outside represented facts, unsupported constructs, physical dataset versions and behavior across partitions still need source-aware review.
