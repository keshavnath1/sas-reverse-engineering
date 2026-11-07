# Implementation and validation contracts

## Existing implementations and observations

| Module | Reused implementation | Bound public engineering evidence |
| --- | --- | --- |
| Preparation | [MIG-3](../mig3/README.md) and [PY-1](../../scripts/preparation_candidate.py) via [MIG-5](../../scripts/migrate_preparation_gates.py) | `SCENARIO_RESULTS.json` and `VALIDATION.json` record first exclusions, assignments and row-end outcomes. The isolated P01 probe remains separate from handoff. |
| Population and gates | [MIG-4](../../scripts/migrate_population.py) via MIG-5 | The `passes` case returns PROCEED with input IDs [1, 0]. The `duplicates` case returns BLOCK at gate 3 with one repeated group, ID 1 with size 2. Both match public expectations. |
| Export | [MIG-6](../mig6/README.md) | `EXPORT_VALIDATION.json` reports PASS for `passes`, with sorted IDs [0, 1]. `SORTED_ROWS.json` and `PREPARED_EXPORT.csv` record the candidate output. No export artifacts are present for `duplicates`. |
| Score | [MOD-2](../mod2/README.md) | `SCORES.json` keeps IDs [1, 0], with eta 1.5 and 0.5 and probabilities approximately 0.817574 and 0.622459. `SCORING_VALIDATION.json` reports PASS against fixed public expectations using absolute tolerance 1e-15. No design or scores are present for `duplicates`. |

All observed values above are **CANDIDATE_ENGINEERING**. Use the linked standalone guides to run the existing commands. The INTG-4R publication and replay compared 16 files for `passes` and 8 for `duplicates`. GATE-1 passed separately for both exact claim records. The `duplicates` candidate block was expected. The original INTG-4 live review remains FAIL. Fitting, convergence and ODS production remain NOT_RUN.

## Independent reference contract

| Boundary | Required evidence and comparison |
| --- | --- |
| [Preparation](TRACE_MAP.md#rules) | Use the [BV-4 custodian experiment](../bv4-reference/README.md) with exact program/input hashes, SAS environment, descriptors, typed input/output rows, trace and reviewed LOG/LST. Compare plain and instrumented business outputs first. Match row identity, multiplicity, character padding, special numeric missings, assignment and first exclusion using comparable observed events. |
| [Population and gates](TRACE_MAP.md#queries) | A controlled attributable SQL/macro run must capture the prepared dataset identity and descriptors, typed IDs, grouped audit, resolved INTO and flag values, actual abort or continuation observations and whether SORT was reached. Verify version continuity from preparation to each consuming step. BV-4 covers preparation only. |
| [SORT and export](TRACE_MAP.md#sort) | Capture descriptors and typed rows before/after SORT, duplicate and missing-key cases, export options and destination behavior, exact output bytes and attributable status. Compare row preservation, ordering/ties, format, padding and serialization. |
| [Model and ODS](TRACE_MAP.md#model) | Capture eligibility, descriptors, event orientation, formatted CLASS levels, reference coding/design, coefficients, fit and convergence diagnostics, ODS descriptors and typed scored rows. Match by row identity; establish exact categorical/identity checks and justified numeric tolerances for coefficients, eta and probability before comparison. Verify fixed scoring separately from fitting. |

Reference execution requires an authorized SAS custodian and independently reviewed evidence. Historical provenance remains UNBOUND.

## Benchmark contract

After correctness checks, select bounded public inputs with documented row widths, sizes, cardinality, skew and missingness. Use a controlled environment and hold input, output, correctness checks and publication policy constant across runs. Record code/fixture hashes, runtime versions, host and resource limits, partition counts, warm-up and repetitions. Measure phase and end-to-end elapsed time, peak memory, I/O and distributed transfer/spill where applicable. Include startup and serialization costs. Compare exact eligible rows, audit/gates, sorted export and fixed scores before using results for a decision. Agree on throughput, latency and memory budgets with stakeholders. Benchmark execution remains NOT_RUN.

## Human-review checklist

- Recompute the manifest and payload identities. Check source declarations against original coordinates and review candidate claims against the bound outputs.
- Confirm coverage of the full prose, including inferred handoffs and unsupported behavior.
- Resolve business questions, acceptance criteria and runtime decision scope separately.
- Require a fresh exact-byte review record and explicit approval for any approval-gated continuation. Earlier INTG-4R approval covers its own claim bytes only.
- Assign independent SAS comparison and benchmark owners before elevating either claim.
