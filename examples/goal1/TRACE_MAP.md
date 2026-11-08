# Reconstruction and evidence

All byte ranges are half-open and local to the named public fixture. The manifest identifies the original source and recovered evidence bytes. JSON paths below identify existing evidence records.

| Public source | Evidence and coverage |
| --- | --- |
| [Preparation](../mig3/preparation.sas.txt) | `PREPARATION_EVIDENCE.json` → `/declared_operation`. DATA, SET, KEEP and six recovered rules in the reviewed lines 1–12. |
| [Population](../mig4/population.sas.txt) | `POPULATION_EVIDENCE.json` → `/selections`, `/connection` and `/interval_effects/findings`. Two selected operations and bounded interval inventory. |
| [Model](../mod2/model.sas.txt) | `MODEL_EVIDENCE.json` → `/declared_operation`. Bounded logistic, ODS and status-check declarations. |

## TRACE — SOURCE_DECLARED

| Anchor | Original span | Declaration |
| --- | --- | --- |
| <a id="prep"></a>Preparation | Preparation lines 2–3 [77,96), [99,116), lines 10–11 [368,453) | Reads `work.samples`, writes `work.prepared`, declares 20 KEEP selections including audit field `case_id`. Field types and actual values remain unknown. |
| <a id="rules"></a>Rules 0–5 | Preparation lines 4–9, in order [119,158), [161,190), [193,227), [230,257), [260,323), [326,365) | Exclude status outside A/B by current-row DELETE. Assign Default 1 for A or 0 for B in the linked alternative. Neither match makes no assignment. Then test MISSING(id), CMISS(n1–n12) > 0 and CMISS(c1–c5) > 0. Prerequisites by rule are none, 0 false, 0/1 false, 0 false, 0/3 false, and 0/3/4 false. Either assignment path and fallthrough rejoin before rule 3. |
| <a id="queries"></a>SQL | Population lines 3–5 [70,187), [188,360), [361,421) | Group `work.prepared` by id and write `work.dupes` with `duplicate_count` for groups whose COUNT(*) > 1. Positional trimmed INTO maps COUNT(*), COUNT(DISTINCT id) and conditional missing-ID sum to `prepared_rows`, `unique_ids` and `missing_ids`. COUNT(*) over `work.dupes` maps to `duplicate_ids`, the number of repeated groups. |
| <a id="gates"></a>Gates | Population lines 7–12 [428,475), [476,524), [525,578), [579,640), [641,684), [685,764) | Abort requests for zero prepared rows, nonzero missing IDs, nonzero duplicate groups, unequal prepared/distinct counts, and unequal expected/prepared counts under UPCASE(check_expected) = Y. Runtime values and macro effects remain unknown. |
| <a id="sort"></a>SORT | Population line 14 [771,829), key [818,824) | Reads `work.prepared`, writes `work.ordered` by ascending id. The DATA declaration at line 1 [0,51) belongs to this fragment and has its own one-column KEEP. The same-fragment relationship is SOURCE_DECLARED / EXECUTION_UNVERIFIED. |
| <a id="model"></a>Model | Model line 3 [180,229), lines 4–5 [232,389), line 6 [392,485), line 7 [488,548) | LOGISTIC reads `work.prepared_data` directly, specifies DESCENDING, Default, x1–x12 and group_a–group_e, PARAM=REF with Reference A through Reference E. OUTPUT writes `work.sas_scored` with XBETA → sas_eta and PREDICTED → sas_phat. Effective event, design, fit and scores remain unknown. |
| <a id="ods"></a>ODS and status | Model lines 1–2 [0,179), line 9 [554,599), line 10 [600,617) | Five ODS destinations for association, class levels, convergence status, fit statistics and parameter estimates. The following assert_step effect remains unresolved. |

## MAP

- **SOURCE_DECLARED** within the population fixture. The [queries](#queries) reference the prepared table, then the duplicate table. INTO references feed the [gates](#gates). The [SORT](#sort) names the same prepared table; its reachability and the table's version are unestablished.
- **INFERRED** across fragments. Matching prepared names provide a potential preparation-to-population relationship. The logistic fixture uses a differently named input. A public candidate adapter maps the approved eligible records to its model slots; no source-level cross-fragment runtime handoff is established.
- **CANDIDATE_ENGINEERING** for branch control. MIG-5 row-end records enter the population audit. PROCEED releases those records to MIG-6 SORT/CSV and to MOD-2 in original pre-sort order. CSV is a separate sink. See the bound publication's `PLAN.json`, `EXPORT_PLAN.json` and `SCORING_PLAN.json`.
- **UNRESOLVED** for SAS runtime. Macro definitions and expansion, optional flag resolution, abort behavior, input schema, continuity, export serialization, successful fitting, scoring and ODS production require evidence. The public population fixture has no CSV export declaration. MIG-6 documents the separate historical EX-1 assumption in its [guide](../mig6/README.md).
