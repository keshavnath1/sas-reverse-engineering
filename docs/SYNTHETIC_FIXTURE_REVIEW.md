# Public P2A fixture expectation review

Status: **REVIEWED for public development before test consumption.**
Prepared 2026-11-05. This record concerns public development expectations, not
the protected-gold or evaluator-isolation requirements deferred to P2B.

## Authorship and independence boundary

`tests/p2a_expectations.py` was authored by the `p2a_public_expectations` subagent
from the approved P2 readiness design, the latest P2A authorization, P1 boundary
documentation, and official SAS references. The author did not inspect
`sas_subset.py`, `semantic.py`, any other P2A reconstruction implementation, or
candidate outputs. No application package is imported by the expectation file.
Its only helpers format source bytes, numeric input declarations and hand-authored
obligations. The generated strings are wholly synthetic and public.

This is source-independent expected-answer authorship with a separate review
checkpoint. Both author and reviewer run in the same development environment;
there is no protected gold, isolated evaluator, named human expert certification,
or claim of independent semantic reliability. Hand traces are reasoning examples,
not observed SAS outputs. SAS execution and benchmarks remain `NOT_RUN`.

Before any test imports the expectations, the root implementation agent must
review the source text, input declarations, fact anchors, expected meaning and
counterexamples without generating expected answers from the candidate. Record
the outcome below, correct any finding and re-review affected obligations. A
candidate disagreement must not by itself cause an expected answer to be changed.

| Role | Actor | Action | Status |
|---|---|---|---|
| Expected-answer author | `p2a_public_expectations` | Hand-authored public source cases, neutral obligations, row traces and incorrect-claim mutations | Authored without candidate access |
| Independent public-expectation reviewer | Root agent, separate from expected-answer author | Checked original bytes/anchors, declared inputs, official rules and mutation counterexamples before tests consumed them | REVIEWED 2026-11-05 |
| Human semantic reviewer | Unassigned | Optional additional public-fixture review; mandatory P2B ownership remains open | NOT_ASSIGNED |
| Protected-gold evaluator | Not implemented | P2B authorization and infrastructure required | BLOCKED |

## Coverage and assertion contract

There are 12 positive fixture families: ordered DATA assignments/filter/KEEP;
SET concatenation/DROP; duplicate-key DATA match-merge; two-key BY/RETAIN/sum/reset;
conditional LAG and independent LAG2; SORT and producer-consumer ordering;
SQL INNER duplicate pairs; LEFT join with post-join WHERE and ordinary missing;
single-source SQL expressions; literal macro/include binding; fixed LOG metrics;
and fixed LST cells. Facts use neutral `subject`, `predicate`, `value`, and original
file/line anchors. They are review assertions, not another editable factual graph.
Tests must translate these reviewed assertions into checks on the canonical graph.

Hand traces preserve row order only when defined by the source and declared
inputs. SQL duplicate results use multisets where ties/order are unspecified.
No inference about general output parity follows from these small examples.
The LST blank is intentionally observed as blank even when a program's numeric
value might be missing; an observation parser must not invent a format-to-value
conversion or reconstruct an entire output dataset from this listing.

Mutation expectations specifically challenge wrong dependency, expression tree,
assignment order, reset/retention, queue behavior, duplicate cardinality,
sort/missing order, macro provenance and observation values/units. Mutations must
retain valid original-byte citations and recompute graph IDs so that a hash or
broken citation is not the sole cause of rejection. These are public checker
regressions. They do not constitute the P2B hidden 360-attempt campaign.

Unsupported syntax and contextual evidence gaps cover every declared language
family. Their expected outcome is an explicit blocker, not a claim that SAS itself
rejects the construct. A malformed authorization/contract can fail structurally;
otherwise unsupported source meaning remains cited and unresolved. No case may
promote semantic acceptance above `BLOCKED`, even when all deterministic public
assertions pass.

## Author reference review

The author consulted the official sources below on 2026-11-05. They support
language distinctions, not this implementation's correctness or a tested SAS
installation. Older reference editions document longstanding behavior within
the approved SAS 9.4 interpretation profile; differences beyond the bounded
synthetic subset remain unresolved.

- A sum statement retains its accumulator, initializes it to zero unless RETAIN
  supplies an initial value, and treats a missing expression as zero.
  [SAS Sum Statement](https://support.sas.com/documentation/cdl/en/lrdict/64316/HTML/default/a000289454.htm)
- A conditionally executed LAG advances only when called. The fixture's separate
  call sites must retain separate queues and cannot become previous-row access.
  [SAS LAG sample 24665](https://support.sas.com/kb/24/665.html)
- Ordinary numeric missing sorts before finite numbers; unsupported special
  missing values are excluded from the positive fixtures.
  [SAS missing-value order](https://support.sas.com/documentation/cdl/en/lrcon/62955/HTML/default/a000989180.htm)
- BY prefix changes affect FIRST/LAST flags on subsequent keys. Temporary flags
  are not automatically output columns. Sortedness requires separate evidence.
  [SAS BY-group identification](https://support.sas.com/documentation/cdl/en/lrcon/62955/HTML/default/a000761931.htm)
- DATA match-merge uses group-wise input advancement and retained exhausted-input
  values; duplicate groups do not form a Cartesian product.
  [SAS MERGE Statement](https://support.sas.com/documentation/cdl/en/lrdict/64316/HTML/default/a000202970.htm),
  [SAS combining datasets](https://support.sas.com/documentation/cdl/en/lrcon/65287/HTML/default/n1tgk0uanvisvon1r26lc036k0w7.htm)
- ORDER BY declares SQL output ordering; no input-order or tie-stability guarantee
  is invented in its absence or for tied keys.
  [SAS SQL sorting](https://support.sas.com/documentation/cdl/en/sqlproc/63043/HTML/default/p1jr2es0aus2qtn11peo724tt8f4.htm)
- Ordinary numeric missing values match one another in SAS SQL equality joins;
  an unmatched LEFT row supplies missing right-side values, and a post-join
  `WHERE b.y > 0` excludes that row.
  [SAS joins and missing values](https://support.sas.com/documentation/cdl/en/sqlproc/62086/HTML/default/a001361784.htm),
  [SAS joined-table](https://support.sas.com/documentation/cdl/en/proc/61895/HTML/default/a002473691.htm)
- Macro uses depend on their literal definition and delimiter; citations must
  retain both definition and use, including an included definition file.
  [SAS macro variables](https://support.sas.com/documentation/cdl/en/mcrolref/61885/HTML/default/a001071889.htm)

The author did not execute sources, inspect private intake, read hidden answers,
or modify downstream Agent-mastery. Internet retrieval initially timed out for
two official statement pages; the BY and MERGE rules were cross-checked using the
official alternate pages above. This does not establish live-runtime verification.

## Reviewer record

The root agent reviewed all 12 cases, 61 facts, 26 mutations, 70 syntax boundaries
and 16 evidence-boundary descriptions on 2026-11-05 before any development test
consumed the file. The reviewed author's file digest was
`0e2e6992c74ebd13e82bfd11edad5595228c7e94a860b6274d81895749d2d24c`.
Only review-status metadata was subsequently changed; no source, expected fact or
hand trace was adjusted to match candidate output.

The review checked expression/assignment/filter sequence by hand; concatenation
order; the three-row match-merge versus six SQL pairs; reset-before-sum and
temporary BY flags; the guarded LAG sequence and separate LAG2 queue; include
definition/use anchors; and zero counts, timing units and LST blank/period cells.
The reviewer cross-checked BY, SUM and LAG using the cited official pages, and
SQL missing equality and match-merge using official SAS search excerpts after
direct page retrieval timed out. Additional corroboration:
[SAS many-to-many merge sample](https://support.sas.com/kb/24/752.html).

No expected-answer correction was needed. Test adapters must treat LST `row`
here as the physical source line (a graph may separately store table-row index);
warning text can be checked through its original source citation. Boundary tests
must provide otherwise valid input metadata so they exercise the named exclusion,
and repeated-include tests must supply the authorized include target. Public
hand traces explain semantics; they do not require executing a SAS interpreter.

This is a separate agent's review of public assertions, not a human SAS expert
sign-off or evaluator isolation. Future expectation changes need renewed review
and an updated digest; hashes are integrity metadata, not authenticated attestations.

The final public expectation-file hash, including reviewed-status metadata, is
`f42549738a041db87d3547adec59ddfd0f9b15aa2621f1cf0b7ea7fa9f7ffd93`.

Additional public regression obligations arose from source review before their
tests were added: compile-time projection, guarded state bounds, invalidated sort
keys, unresolved references and control lineage. The fixture author separately
reviewed the graph agent's concrete regression expectations, including retained
SUM recurrence, pre-SET reads, input RETAIN bounds and downstream uncertainty.
These tests may deliberately require conservative refusal; they do not assert
that an unproved expression is necessarily inexact in SAS. Parser mechanics were
reviewed by the root agent, and the parser agent independently reviewed observation
header/column ambiguity and append-only workflow behavior. None is hidden gold.
