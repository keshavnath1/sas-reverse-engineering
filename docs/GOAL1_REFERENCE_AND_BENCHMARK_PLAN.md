# GOAL-1 SAS reference and benchmark follow-up

**Status DRAFT.** Owner assignments are pending. SAS reference and benchmark execution are **NOT_RUN**. Semantic verification is **UNVERIFIABLE**, semantic acceptance is **BLOCKED**, and historical SAS provenance is **UNBOUND**.

This plan follows the published GOAL-1 manifest with SHA-256 `7167740a9fa6f362dbbc5128dd7d74f016128f861d3ed84584f8229f552e1399` and the human-approved review record with SHA-256 `b71abc7930dd948f06187d0c66c101413c19f37dbb4231da903576a4a09f2b8d`. [Published manifest](../examples/goal1/MANIFEST.json) · [Review approval](GOAL1_REVIEW_APPROVAL.md) · [Validation contracts](../examples/goal1/VALIDATION.md)

## SAS reference runs

BV-4 covers preparation only. SQL and gate behavior requires a separate SAS reference experiment. On continuation, export consumes eligible records sorted by ID. Fixed scoring consumes the same eligible population in original pre-sort order. Fitting and ODS form a separate workstream.

Before execution, identify the authorized SAS environment and custodian, settle the business rules used in each comparison, and agree on cases and numeric tolerances. For each run, retain the program, input, candidate, and output identities and hashes, the SAS version and options, the execution date and operator, and the reviewed LOG/LST. The independent reviewer records a result and supporting artifact references for each criterion. Record missing evidence and discrepancies explicitly.

| Run | Evidence needed | Acceptance criteria |
| --- | --- | --- |
| Preparation (R1) | BV-4 plain and instrumented runs, typed input and output rows, descriptors, and traces tied to the run. Include cases for character padding and special numeric missing values. | Plain and instrumented business outputs agree first. Then compare candidate and reference row identity, multiplicity, eligibility, assignments, and first exclusion using comparable observed events. |
| Population and gates (R2–R3) | Separate attributable SQL and macro runs. Capture prepared dataset identity, descriptors and typed IDs, grouped counts, resolved `INTO` and flag values, expected-count inputs, first block or continuation, and whether SORT ran. Include proceed, duplicate block, and expected-count cases. | Establish continuity from preparation to each consumer. Match group sizes, repeated-group counts, evaluated gate order, first block, skipped checks, and downstream reachability under the agreed policy. |
| SORT and export (R4) | Typed before-and-after rows and descriptors, duplicate and missing-key cases at the applicable boundary, export options, destination behavior, status, and exact output bytes. | Match row preservation and multiplicity, approved ordering and ties, schema and column order, padding, and exact serialization under the agreed CSV contract. Confirm overwrite behavior against that contract. |
| Fixed scoring (R5) | Eligible pre-sort rows and original ordinals, typed descriptors, event orientation, formatted CLASS levels, reference coding, design, fixed coefficients, and typed scored rows. | Match case identities, order and categorical encoding exactly. Compare eta and probability against numeric tolerances agreed before execution. Verify the bound coefficients and score the same eligible population used by export. |
| Fitting and ODS (ADR C) | If separately authorized, retain fitted coefficients, estimation and convergence settings and diagnostics, ODS descriptors, and typed scored rows tied to the same run. | Review model design and fitting behavior against separately agreed criteria. Record a separate result for fitting and ODS. |

The evidence package should include a run manifest, checksums, comparison results, and independent review findings. Reconcile any mismatch or record it as open before claiming parity for that boundary. Use the exact subject and final review-record digests for any approval-gated publication under R6. [BV-4 custodian experiment](../examples/bv4-reference/README.md)

## Benchmarks

1. **Define the workload and budgets.** Use native Python as the baseline for bounded public inputs. Document row count and width, key cardinality, skew, and missingness. Agree on latency, throughput, memory, and recovery budgets before measuring. Use representative cases that cover both continuation and block.
2. **Check correctness first.** Across benchmark runs, compare exact eligible rows, audit and gate outcomes, sorted export bytes, and fixed scores under the agreed numeric policy. Keep inputs, output contract, correctness checks, and publication policy constant. Report candidate consistency and SAS parity separately.
3. **Capture repeatable measurements.** Record code and fixture hashes, runtime and host versions, resource limits, partition counts where applicable, warm-up, repetitions, and raw per-run measurements. Report phase and end-to-end time, throughput, peak memory, and I/O. Include startup and serialization, and measure distributed transfer or spill when evaluating a distributed runtime.
4. **Review results against budgets.** A baseline passes only when it meets the agreed correctness and resource criteria for the declared workload. Record any breached budget and the phase responsible. Revisit ADR B when representative evidence shows a baseline constraint. Any distributed candidate must preserve the shared eligible snapshot, global export order, original scoring order, and publication and recovery behavior. [Optimization review](../examples/goal1/OPTIMIZATION.md)

## Owner roles

| Role | Responsibility | Assignment |
| --- | --- | --- |
| Business and consumer policy owners | Set status, event, gate, export, and scoring policies and confirm release criteria. | PENDING |
| Authorized SAS custodian | Run the approved reference cases and attest to the environment, inputs, and captured evidence. | PENDING |
| Independent comparison reviewer | Review provenance, approve comparison rules before execution, and assess results and discrepancies. | PENDING |
| Benchmark owner | Define workloads, run controlled comparisons, and retain measurements and reproducibility details. | PENDING |
| Budget and architecture approver | Set performance and recovery budgets and decide whether benchmark evidence warrants reopening ADR B. | PENDING |
