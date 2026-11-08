# GOAL-4C corrected review draft

This is a separate reviewer-edited copy derived from the latest raw Copilot
draft (SHA-256 68f321fe99c55523074dc55088b9f838c63cfe6ce898d59fb1a017a25327ab99).
It is bound to the public P2A manifest SHA-256
0ab65953887f07b9ba6f09a0b547a7848c7d69cdbde26e00284c5f2d1931e5f6.
Review disposition is pending. All three live-run FAIL verdicts stand.

## 1. TRACE reconstruction

- **SOURCE_DECLARED.** The entry program includes `settings.sas` at
  `main.sas:1`, bytes [0,24), and `enrich.sas` at `main.sas:15`, bytes
  [347,369). The first include declares the literal macro value `work.raw`
  in `settings.sas:1`, bytes [0,21).
  `EVIDENCE.json#/operations/0/facts/0` `EVIDENCE.json#/operations/1/facts/0`
  `EVIDENCE.json#/operations/4/facts/0`
- **SOURCE_DECLARED.** The DATA step writes `work.running` and reads
  `&source.` through SET at `main.sas:2–3`, bytes [25,56).
  `EVIDENCE.json#/operations/2/facts/0` `EVIDENCE.json#/operations/2/facts/2`
- **SOURCE_DECLARED.** The DATA step declares BY keys `group, subkey`, retains
  `balance` with initial value 8, resets it at `first.group`, then uses the
  sum statement `balance + amount`. It calls `lag(amount)` when `amount > 0`
  and assigns `marker = 1` at `last.subkey`. KEEP selects `group`, `subkey`,
  `amount`, `balance`, `previous` and `marker`. These facts occupy
  `main.sas:4–10`, bytes [58,267).
  `EVIDENCE.json#/operations/2/facts/3` `EVIDENCE.json#/operations/2/facts/4`
  `EVIDENCE.json#/operations/2/facts/5` `EVIDENCE.json#/operations/2/facts/6`
  `EVIDENCE.json#/operations/2/facts/7` `EVIDENCE.json#/operations/2/facts/8`
  `EVIDENCE.json#/operations/2/facts/9`
- **SOURCE_DECLARED.** SORT reads `work.running`, writes `work.export_order`
  and specifies ascending `group, subkey`. Procedure span `main.sas:12–14`,
  bytes [274,346). `EVIDENCE.json#/operations/3` `EVIDENCE.json#/operations/3/facts/0`
- **SOURCE_DECLARED.** SQL creates `work.enriched` from a left join of
  `work.running` and `work.lookup` on `group`. It projects `group, balance,
  weight` and filters on `b.weight > 0`. The CREATE/query occupies
  `enrich.sas:2–5`, bytes [10,195).
  `EVIDENCE.json#/operations/5/facts/0` `EVIDENCE.json#/operations/5/facts/1`
- **PROFILE_ASSUMPTION.** The public profile supplies numeric input descriptors,
  sample rows, sorted input for `work.raw` by `group, subkey`, and the ordinary
  numeric-missing equality policy for joins. These inputs and policies are
  declared in the profile. `profile.json#/inputs/0` `profile.json#/inputs/1`
  `profile.json#/numeric_missing_join_policy`
- **PACKAGE_METADATA.** The package is DRAFT and reconstruction is PARTIAL.
  `MANIFEST.json#/artifact_authority` `MANIFEST.json#/reconstruction_status`

## 2. PRD and requirements

| Class | Draft requirement | Validation obligation |
| --- | --- | --- |
| PROPOSED | R1. Preserve the ordered DATA-step rules and the six selected columns. `EVIDENCE.json#/operations/2/facts` `EVIDENCE.json#/operations/2/state_effects` | Compare typed row values and multiplicity with attributable DATA output. Probe group changes, missing amounts, and skipped LAG calls. |
| PROPOSED | R2. Produce `work.export_order` with ascending declared keys and preserve row multiplicity. `EVIDENCE.json#/operations/3/facts/0` `EVIDENCE.json#/operations/3/order_contract` `EVIDENCE.json#/operations/3/cardinality` | Compare key order and input/output row multisets. Obtain an explicit tie policy if downstream consumers require one. |
| PROPOSED | R3. Preserve the SQL join, projection and filter. `EVIDENCE.json#/operations/5/facts/1` `EVIDENCE.json#/operations/5/cardinality` `profile.json#/numeric_missing_join_policy` | Compare projected row multisets on duplicate, unmatched and missing-key cases. Include nonpositive and missing right-side weights. |

**UNRESOLVED.** Business intent for the weight filter and acceptable duplicate
multiplicity need owner review. Numerical tolerance and ordering checks remain
pending in the draft. `EVIDENCE.json#/operations/5/facts/1/where`
`migration-profile.yaml#/approval/business_intent`
`migration-profile.yaml#/execution/multiplicity_policy` `tie-out.yaml#/checks`

## 3. MAP and dependency analysis

**INFERRED.** All four edges retain the graph's `INFERENCE` classification.

| Edge | Represented relationship |
| --- | --- |
| `EVIDENCE.json#/edges/0` | STATE self-edge on DATA. |
| `EVIDENCE.json#/edges/1` | STATE from macro binding to DATA. |
| `EVIDENCE.json#/edges/2` | DATA from preparation to SORT. |
| `EVIDENCE.json#/edges/3` | DATA from preparation to SQL. |

**INFERRED.** The graph resolves the macro-backed input to `work.raw` and
models the LAG queue as advancing only on executed calls. Those are
reconstruction interpretations of the cited macro and guard, respectively.
`EVIDENCE.json#/operations/2/facts/1`
`EVIDENCE.json#/operations/2/state_effects/3/call_policy`

**UNRESOLVED.** SORT and SQL read `work.running` in the reconstructed graph.
The graph contains no SORT-to-SQL edge. Runtime dataset versions, execution
and parallel independence are unproved. LOG/LST findings are unbound.
`EVIDENCE.json#/edges` `EVIDENCE.json#/unknowns`

## 4. Validation plan

- **PACKAGE_METADATA.** SAS reference execution and benchmarks are NOT_RUN.
  Behavioral evidence is UNAVAILABLE, verification UNVERIFIABLE, acceptance
  BLOCKED and historical source/run provenance UNBOUND.
  `MANIFEST.json#/reference_experiment` `MANIFEST.json#/benchmark_execution`
  `MANIFEST.json#/behavioral_evidence` `MANIFEST.json#/semantic_verification`
  `MANIFEST.json#/semantic_acceptance` `MANIFEST.json#/historical_source_run_provenance`
- **PROPOSED.** Bind the exact submitted source, typed input rows and
  descriptors to an authorized run. Collect DATA outputs and state
  observations for reset, sum and guarded LAG, SORT output with keys and
  row order, and SQL projected rows and multiplicity. Compare the SQL result
  as a multiset unless an ordering contract is independently established.
  `EVIDENCE.json#/operations/2/state_effects`
  `EVIDENCE.json#/operations/3/order_contract`
  `EVIDENCE.json#/operations/5/order_contract` `EVIDENCE.json#/operations/5/cardinality`
- **UNRESOLVED.** The fixture's LOG/LST provides no attributable runtime
  observations. Public engineering expectations require separate labeling
  from observed SAS outputs. `EVIDENCE.json#/log_observations`
  `EVIDENCE.json#/unknowns` `tie-out.yaml#/reference`

## 5. Architecture ADR

- **PACKAGE_METADATA.** Runtime and distributed choices remain pending.
  Architecture and business-intent approval remain required in the draft.
  `migration-profile.yaml#/target` `migration-profile.yaml#/approval`
- **PROPOSED.** A native single-process design could keep ordered DATA state
  in one stream and feed its output separately to SORT and SQL. Validate
  row order and state transitions before treating the design as suitable.
  `EVIDENCE.json#/operations/2/order_contract`
  `EVIDENCE.json#/operations/2/state_effects` `EVIDENCE.json#/edges/2`
  `EVIDENCE.json#/edges/3`
- **PROPOSED.** A distributed design remains conditional on evidence that
  partitioning and exchanges preserve key order, retained state and LAG
  queue continuity, join multiplicity, and the SORT output contract.
  Benchmark only after correctness criteria are met.
  `EVIDENCE.json#/operations/2/state_effects` `EVIDENCE.json#/operations/3/order_contract`
  `EVIDENCE.json#/operations/5/cardinality` `MANIFEST.json#/benchmark_execution`

**Pending human decisions.** Confirm the business intent and proposed
acceptance criteria, review evidence classifications, and leave runtime
selection open until the stated proof is available.
