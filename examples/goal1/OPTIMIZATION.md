# Dependency and optimization review

These are **INFERRED** opportunities for the public candidate design. Benchmark execution is package metadata with value `NOT_RUN`.

| Opportunity and basis | Invariants and unresolved risks | Measurement before selection |
| --- | --- | --- |
| Reuse one preparation pass and a versioned eligible-row snapshot. [Preparation](TRACE_MAP.md#prep), [rules](TRACE_MAP.md#rules), [MAP](TRACE_MAP.md#map). | Preserve typed values, provenance, multiplicity, row-end eligibility and the original ordinal. A retry must consume the same snapshot; memory and persistence costs remain unknown. | Compare repeated preparation against shared snapshot materialization and reads, with memory and byte accounting. |
| Fuse compatible population counts and reuse grouped audit. [SQL](TRACE_MAP.md#queries). | Exact distinct and group counts require global reconciliation. Local counts cannot be summed for distinct IDs. Null and comparison policies must match the approved contract. | Compare peak memory, aggregation and spill under controlled ID cardinality and skew. |
| Execute export and scoring independently after PROCEED. [Gates](TRACE_MAP.md#gates), [MAP](TRACE_MAP.md#map). | Both branches must consume the same eligible snapshot. Export needs global order, scoring needs original ordinal, and neither branch may publish on a blocked run. Concurrent memory pressure and partial publication need review. | Compare sequential and concurrent branch wall time, peak memory, I/O and failure recovery. |
| Partition row-local work before global audit and sorting. [Rules](TRACE_MAP.md#rules), [SORT](TRACE_MAP.md#sort). | Keep guard order within each row, preserve multiplicity and define tie ordering. Unknown SAS state and macro effects preclude inferring SAS independence. Single CSV publication can become a bottleneck. | Vary partitions and skew; measure shuffle, spill, merge and output costs after correctness comparison. |
