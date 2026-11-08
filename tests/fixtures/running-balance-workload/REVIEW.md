# Running-balance modernization review

**Decision requested.** Confirm the running-balance and enrichment rules,
identify the intended consumer of each output, and agree on validation
criteria. Keep runtime selection pending. This public example is a draft
design review with no executable migration for the complete project.

Citations use exact pointers into the [evidence graph](evidence/EVIDENCE.json),
[review manifest](evidence/MANIFEST.json), and [input profile](source/profile.json).
Source coordinates are original half-open byte intervals.

## 1. TRACE and coverage

| Classification | Recovered behavior | Evidence |
| --- | --- | --- |
| SOURCE_DECLARED | The entry program includes settings and later the enrichment program. Settings binds the literal `work.raw`; the DATA step reads through `&source.`. | `main.sas.txt:1 [0,28)` and `main.sas.txt:15 [351,377)`, `settings.sas.txt:1 [0,21)`. `EVIDENCE.json#/operations/0` `EVIDENCE.json#/operations/1` `EVIDENCE.json#/operations/2/facts/1` `EVIDENCE.json#/operations/4` |
| SOURCE_DECLARED | DATA writes `work.running`, declares BY `group, subkey`, initializes retained `balance` to 8, resets it on `first.group`, then adds `amount` with a sum statement. It calls `lag(amount)` when `amount > 0` and sets `marker` on `last.subkey`. KEEP selects `group, subkey, amount, balance, previous, marker`. | `main.sas.txt:2–11 [29,277)`. `EVIDENCE.json#/operations/2/facts` |
| SOURCE_DECLARED | SORT reads `work.running` and writes `work.export_order` by ascending `group, subkey`. | `main.sas.txt:12–14 [278,350)`. `EVIDENCE.json#/operations/3` |
| SOURCE_DECLARED | SQL creates `work.enriched` from a LEFT JOIN of `work.running` to `work.lookup` on `group`, projects `group, balance, weight`, and applies `b.weight > 0` after the join. | `enrich.sas.txt:1–6 [0,202)`. `EVIDENCE.json#/operations/5/facts` |
| PROFILE_ASSUMPTION | Numeric input descriptors, bounded rows, sorted `work.raw` by `group, subkey` and ordinary numeric-missing equality for joins are synthetic profile declarations. | `profile.json#/inputs` `profile.json#/numeric_missing_join_policy` |

**Coverage register.** Reconstruction is COMPLETE within this declared profile,
with three reached source files, six operations and zero recorded unknowns.
The fixture supplies no LOG/LST or attributable runtime evidence. Runtime
order, dataset-version continuity, equal-key SORT order and SAS-equivalent
outputs remain unresolved. There is no declared SQL output order. No
unsupported syntax was recorded for these inputs. Dynamic includes and
arbitrary macros are outside this demonstration.
`MANIFEST.json#/reconstruction_status` `EVIDENCE.json#/coverage`
`EVIDENCE.json#/log_observations` `EVIDENCE.json#/operations/3/order_contract`
`EVIDENCE.json#/operations/5/order_contract`

## 2. Draft PRD and functional specification

**Proposed outcome.** Provide repeatable running-balance, ordered and enriched
datasets with explicit input and output contracts. The source gives technical
rules. The owner must confirm their intended business meaning.

| Proposed requirement | Module contract and acceptance criterion |
| --- | --- |
| R1. Preserve preparation rules. | Accept typed ordered `work.raw`. Produce the six KEEP fields and preserve represented row order. Compare typed values and multiplicity against attributable DATA outputs. Probe group-prefix changes, first/last flags, missing amount, reset before accumulation and rows that skip LAG. `EVIDENCE.json#/operations/2/facts` `EVIDENCE.json#/operations/2/state_effects` |
| R2. Preserve the sorted handoff. | Sort `work.running` on both declared keys and preserve its row multiset. Obtain a tie policy if equal-key order matters to the consumer. `EVIDENCE.json#/operations/3/order_contract` `EVIDENCE.json#/operations/3/cardinality` |
| R3. Preserve enrichment behavior. | Join the prepared population to typed lookup data and apply the projected columns and post-join predicate. Compare projected multisets on matched, duplicate, unmatched and missing-key cases and on missing or nonpositive weights. `EVIDENCE.json#/operations/5/facts/1` `EVIDENCE.json#/operations/5/cardinality` |

**Owner decisions.** Confirm what the balance, marker and positive-weight
filter represent. Confirm whether duplicate lookup keys are permitted, which
consumers rely on either output, whether ties matter and what numeric
tolerances are acceptable. Record decisions separately from the source facts.
`migration-profile.yaml#/approval` `migration-profile.yaml#/execution`
`tie-out.yaml#/checks`

## 3. MAP and optimization assessment

The graph represents two STATE edges, a DATA-step self-edge and a macro
binding feeding preparation, and two DATA edges from preparation, one into
SORT and one into SQL. All four are **INFERRED**. SQL consumes `work.running`
directly. The sorted output is a separate branch. The graph records no SORT-to-SQL
edge. Runtime order and independence remain unproved.
`EVIDENCE.json#/edges/0` `EVIDENCE.json#/edges/1`
`EVIDENCE.json#/edges/2` `EVIDENCE.json#/edges/3`

**Optimization hypotheses.** Sharing one materialized prepared population
could avoid repeated preparation if both consumers can use the same version.
Measure its size, memory and I/O before choosing how to share it. Early
projection could reduce data carried through the join if all join, predicate
and output columns are preserved. Moving the right-side predicate into the
join condition can change unmatched-row behavior and needs a separate
correctness proof. Partitioning preparation by BY group needs a proof of
state continuity. In particular, the modeled LAG queue advances only on
executed calls and has no implicit reset at a group boundary.
`EVIDENCE.json#/operations/2/state_effects/3`
`EVIDENCE.json#/operations/5/facts/1`
`EVIDENCE.json#/operations/5/interpretation_rules`

## 4. Validation and engineering tie-out

1. **Structural.** Recompute manifest digests, resolve citations and check
   original byte spans. Replay the generated evidence and configuration drafts.
   These checks were performed for the packaged example.
2. **Proposed engineering checks.** Use small typed public rows to check
   ordered preparation, retained state, guarded queue advancement, row
   multiplicity, key ordering and SQL filter placement against explicitly
   labeled engineering expectations when a candidate becomes available.
3. **Independent reference.** Obtain an attributable source/profile-bound SAS
   submission, typed inputs and outputs, and operation-level state or trace
   observations. Compare preparation rows, SORT order and SQL multisets with
   agreed tolerances. No SAS reference was run.
4. **Performance.** After correctness, measure memory, elapsed time and
   input/output volume on representative workloads. A native baseline comes
   first in the proposed experiment. Benchmarks remain NOT_RUN.

`tie-out.yaml#/checks` `tie-out.yaml#/reference`
`MANIFEST.json#/behavioral_evidence` `MANIFEST.json#/benchmark_execution`

## 5. Architecture and candidate fit

**HLD proposal.** Validate the input contract, run ordered preparation once,
then pass an identified prepared population to two distinct output modules.
Treat external inputs and output consumers as explicit boundaries.

**LLD proposal.** Use a typed row iterator with previous and next BY-key
context for flags. Keep the retained accumulator and per-call-site queue as
separate state. Give the SORT module a two-key ordering contract and a
separately agreed tie policy. Give enrichment a lookup that preserves repeated
matches, applies the join policy, then filters and projects. Verify resource
bounds and type/missing representation before selecting concrete data
structures. `EVIDENCE.json#/operations/2/state_effects`
`EVIDENCE.json#/operations/3/order_contract`
`EVIDENCE.json#/operations/5/facts/1`

**Draft ADR.** Runtime selection is pending.

| Option | Fit and proof required |
| --- | --- |
| Native Python | Start comparison with one ordered stream and explicit state. Measure lookup size, sort memory and spill needs. |
| Spark | Consider when measured sort or join volume warrants distributed exchange. Demonstrate stable ordering and queue-state continuity across partition boundaries, and verify join multiplicity and missing handling. |
| Ray | Consider task-level separation of the two downstream consumers if a common prepared version can be handed off and transfer costs justify it. Keep ordered state within preparation unless a split is proved safe. |
| Dask | Consider partitioned sort and join only with measured memory pressure and verified shuffle and order contracts. Establish whether ordered preparation can remain a separate stage. |

All four options use the same correctness obligations. There is no runtime
selection or measured performance claim.
`migration-profile.yaml#/target` `EVIDENCE.json#/operations/2/state_effects`
`EVIDENCE.json#/operations/5/cardinality` `MANIFEST.json#/benchmark_execution`

### Existing Python candidate applicability

| Operation | Classification | Contract boundary |
| --- | --- | --- |
| Settings INCLUDE | Reconstructable, no candidate execution | Literal include resolves in reconstruction. Existing candidates do not execute include files. `EVIDENCE.json#/operations/0` |
| Literal macro binding | Reconstructable, no candidate execution | The graph carries the binding. Candidates receive explicit typed inputs and do not execute SAS macros. `EVIDENCE.json#/operations/1` |
| Stateful DATA | Reconstructable, no candidate execution | The projection candidate accepts a bounded projection and SORT subject. The preparation candidate expects its pinned six-rule subject, which differs from this BY/RETAIN/SUM/LAG step. `EVIDENCE.json#/operations/2` |
| Two-key SORT | Reconstructable, no candidate execution | The configurable projection/SORT route requires one key and two selected columns. The full-record exporter is pinned to its own approved scenario. Neither contract matches this operation. `EVIDENCE.json#/operations/3` |
| Enrichment INCLUDE | Reconstructable, no candidate execution | The literal include is analyzed as source. There is no candidate continuation for its SQL. `EVIDENCE.json#/operations/4` |
| LEFT JOIN and filter | Reconstructable, no candidate execution | The population audit candidate implements bounded metrics and gates. It does not implement this enrichment join. `EVIDENCE.json#/operations/5` |

The [projection/SORT](../../scripts/migrate_projection_sort.py),
[preparation and population](../../scripts/review_mig5.py), and
[export](../../scripts/migrate_sort_export.py) contracts define these limits.
This project has no eligible continuation. Human review of this package
remains pending. SAS reference execution is NOT_RUN and semantic acceptance
is BLOCKED. `MANIFEST.json#/reference_experiment`
`MANIFEST.json#/semantic_acceptance`
