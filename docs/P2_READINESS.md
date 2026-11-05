# P2 readiness: bounded semantic reconstruction

Status: **PROPOSED — planning only; P2 implementation is not approved.**
Historical planning status at `e13705c`. The subsequent user instruction approved
D08-A/B for deterministic **P2A only**; D08-C/D09 and independent acceptance remain
open for P2B. See [P2A_DESIGN.md](P2A_DESIGN.md) and [APPROVALS.md](APPROVALS.md).
Prepared 2026-11-05. The user accepted P1 at
`5c8aea7588290925250b76c9cbd5091a3ea89f13` and requested this design checkpoint.
Read with [P2_EVALUATION_DESIGN.md](P2_EVALUATION_DESIGN.md) and the current
approval ledger in [OPEN_DECISIONS.md](OPEN_DECISIONS.md).

## Evidence and authority

Observed: P1 has explicit synthetic scope, original-byte identities, a composed
graph, citation/reference checks, append-only attempts and structural verification.
Its graph and report semantic fields are fixed to `UNVERIFIABLE`. The existing
design and validation reports describe 138 tests and their proof limits; those
tests were not rerun locally for this documentation-only checkpoint.

Inspected at the accepted commit: `AGENTS.md`, `docs/P1_DESIGN.md`,
`docs/P1_VALIDATION.md`, `docs/OPEN_DECISIONS.md`, the v1 schema bundle, and
`contracts.py`, `evidence.py`, `runs.py`, `cli.py` and the publication interfaces.
The reference archive remains SHA-256
`e3cbf3d9df6cc20c594261556c5e3ea1dfc292c9c1a30672c2d7b1a736b9718e`.
Relevant pack requirements are documents 02, 04, 06 and 10, the evaluation matrix
and the synthetic-example guidance. Document 02 controls workflow; 04 requires
independent semantic checks; 06 defines P2 reconstruction and graph visualization.
The published examples are development material, not withheld evaluation gold.

All choices below are proposed designs, not implemented features or measured
results. Official SAS references support the stated language distinctions;
they do not establish that this repository implements them. Agent-mastery remains
read-only at `bc754e0f1204a99020c864df2a5b25983005e09c`.

## D08 recommendation and proof boundary

Build a **static, synthetic-only interpretation pilot** for the exact subset
below. Produce the same canonical source graph, with a narrow versioned semantic
extension, then independently check it. Do not execute SAS, emulate a complete
SAS runtime, translate programs or optimize them. Recognizing a construct and
recording its conditional meaning is different from proving actual output parity.

Use SAS 9.4 DATA-step/PROC SQL language behavior as the proposed interpretation
profile. Record the profile and cited reference revisions with every run; older
official references below support longstanding rules, not a tested installation.
There is no licensed SAS execution environment or observed runtime configuration
in this pilot. An environment-dependent claim without evidence remains unresolved.

Private/local examples previously supplied for readiness checks are excluded
from this synthetic pilot. Do not copy, derive hidden fixtures from, upload or
label those files synthetic. Non-synthetic support needs a separate scope and
contract decision; it is not implicitly approved by this planning checkpoint.

### Exact first-pilot subset

Every positive fixture must satisfy all relevant restrictions. Unsupported
constructs are detected and represented with cited unknowns; they are never
silently skipped. A file containing unsupported code cannot receive complete
semantic PASS even if some operations are correctly reconstructed.

| Area | Supported positive forms | Facts that must be preserved | Unresolved/unsupported boundary |
|---|---|---|---|
| Lexical framing | UTF-8/ASCII; semicolon statements; ordinary ASCII identifiers; nonnested block comments; restricted statement/macro comments as defined below; single/double quotes with doubled-quote escaping | Original-byte spans, statement sequence, case-insensitive name resolution; source text is never agent instructions | Unclosed tokens, unsafe-to-discard macro-bearing comments, name literals, ambiguous encoding or unfamiliar syntax block the region |
| Names and inputs | Explicit `work.name`; synthetic input schemas/rows declared in authorized fixture files; one output dataset name written once per case | Dataset/column owner and producer; exact input preconditions | Implicit librefs, engines/views, dataset overwrites, unknown schemas or external data access |
| DATA step | One output, one SET or MERGE source statement; numeric assignments and parenthesized arithmetic `+ - * /`; literal numeric comparisons; simple `IF condition THEN assignment;` or subsetting `IF condition;`; explicit KEEP/DROP lists | Ordered statement facts, expression tree with original lexemes, filter location and column lineage | DO/arrays, loops, multiple outputs, explicit OUTPUT/DELETE/STOP, chained comparisons, implicit conversions, dataset options or arbitrary functions |
| SET | One `SET work.a;` or `SET work.a work.b;`, without BY on a multi-input SET | Input order and concatenation, both producers, columns and output writes | Multiple/conditional SET statements, POINT/KEY, lists/ranges and interleaving SET+BY |
| MERGE | Two inputs, `MERGE work.a work.b; BY key;`; one ascending numeric key, compatible key types, disjoint nonkey column names; synthetic inputs have explicit sortedness evidence | SAS match-merge behavior, group-wise input advancement and retained input values; both producers and sort precondition | No-BY merge, IN/END/options, shared nonkey variables, unknown ordering/type properties; no automatic SQL equivalence |
| BY groups | One or two ascending numeric keys for a single-input DATA step; FIRST/LAST references; simple `IF FIRST.key THEN accumulator=0;` | Group boundaries including prefix-key effects, ordered input, exact reset point | DESCENDING, NOTSORTED, GROUPFORMAT, indexes, character collation; BY alone does not prove sorted input |
| State | Numeric `RETAIN name literal;`; sum statement `name + expression;`; direct `lag(x)`/`lag2(x)` assignment, optionally guarded by a supported simple numeric IF | Initialization, per-iteration persistence, reset conditions and statement order; one queue per LAG call site, advanced only on executed calls | Complex conditional call graphs, LAG of computed/dynamic arguments, arrays or arbitrary state machines; no presumed BY reset |
| PROC SORT | `PROC SORT DATA=work.a OUT=work.sorted; BY key [key2]; RUN;` with distinct output | Source-level sort operation and resulting order contract, not evidence of a completed run | NODUP options, in-place sort, sort stability/tie order, locale-dependent ordering or runtime cost |
| PROC SQL | One CREATE TABLE AS SELECT per PROC block; explicit qualified column list and numeric expressions/aliases; one FROM input or two inputs with one INNER/LEFT equality join; simple numeric WHERE; optional ascending ORDER BY | Qualified column lineage, ON versus WHERE placement, multiplicity, missing-value policy, explicit order or unspecified order | SELECT *, aggregate/remerge, DISTINCT, subqueries, UNION, INTO, DML, pass-through, conversion and advanced functions |
| Macro references | Open-code `%LET name=literal;`, defined once before use; direct `&name`/`&name.` substitution in dataset-name tokens; explicit literal quoted `%INCLUDE` already in scope | Definition and use citations, token substitution and include order; no shell/environment lookup | Macro definitions/calls, reassignment, `&&`, quoting functions, `%SYSFUNC`, `%IF/%DO`, runtime symbol assignment, autocall search or macro-built include paths |
| LOG | Frozen synthetic English templates for read/output row counts, WARNING lines, `real time` and `cpu time` in decimal seconds; explicit execution and step binding | Original decimal lexeme/unit, metric role, zero counts, operation/run association and segment completeness | Other formats/units, multiple ambiguous steps, missing/truncated segments or guessed source linkage |
| LST | One declared synthetic title/header/table layout, numeric cells and explicit blank/missing markers, bound to one operation/run | Cited cell/label, coordinates and missing-marker distinction; observation only | Arbitrary reports, pagination heuristics, model coefficient interpretation, statistical inference or entire-dataset reconstruction |

The subset is a closed allowlist, not “anything that looks similar.” For example,
arithmetic inside SQL is covered only by the same numeric restrictions, not by a
general SQL expression evaluator. Null/missing join keys are permitted only in
cases with an explicit reviewed SAS numeric-missing interpretation; SQL NULL or
Python NaN rules cannot be substituted.

### Pilot grammar restrictions

These restrictions are normative for the proposal, not a parser implementation:

- Ordinary names match `[A-Za-z_][A-Za-z0-9_]{0,31}`. Dataset names are exactly
  `work.name`; qualified SQL references are `alias.column`. Resolve names
  case-insensitively while retaining original spellings and bytes.
- Numeric literals are optional sign plus decimal digits with an optional decimal
  fraction, or ordinary missing `.`. No exponent, hexadecimal or special-missing
  literals. Supported expressions combine names/literals using parentheses,
  unary sign and binary `+ - * /`, with normal SAS precedence and original tree
  retained. Positive fixtures use 8-byte numeric attributes and finite integers
  of magnitude at most 2^20 or dyadic fractions with denominator at most 1024;
  all intermediate finite results must remain exactly representable in the
  registered profile. Division uses nonzero power-of-two constants.
  Anything needing a rounding/overflow policy outside that profile is unresolved.
- A DATA-step condition is one numeric variable compared with one numeric
  literal by `=`, `^=`, `<`, `<=`, `>` or `>=`, or a single `FIRST.key`/`LAST.key`
  flag. No AND/OR/NOT, chained predicates, ELSE or DO groups. The single THEN
  action is an assignment or sum statement; direct LAG/LAG2 is allowed only as
  the whole assignment RHS. KEEP/DROP use explicit space-separated names.
- SQL inputs require distinct explicit aliases (`FROM work.a AS a`, optionally
  one `INNER JOIN` or `LEFT JOIN work.b AS b`). ON is exactly one numeric-key
  equality `a.key=b.key`. WHERE is one qualified numeric column comparison with
  a literal using the operators above. Every selected expression has a unique
  explicit `AS output_name`. ORDER BY uses one or two output names, ascending;
  no ordinal positions, compound predicates or implicit aliases.
- `%LET` binds a single ordinary name or complete `work.name` token, with no
  quotes, whitespace inside the value, `%` or `&`. Only `work.&member` or a
  whole `&dataset` token, optionally with the terminating dot, may use that
  binding. No nested/repeated expansion, macro references inside strings or
  multiple macro references in a dataset token. Each name is defined once.
- `%INCLUDE` has one quoted, literal, safe relative path mapped to an already
  authorized file key. Include cycles and repeated inclusion of the same file
  are unsupported initially. Missing targets do not expand the authorized scope.
- Positive `* ... ;` statement comments contain neither `%` nor `&` and have
  balanced quotes. `%* ... ;` macro comments also require balanced quotes.
  Other comment cases block rather than being stripped. This matters because
  SAS macro processing can occur inside statement comments; treating source as
  untrusted agent data does not make all SAS comments semantically inert.
  [SAS 9.4 Macro Language Reference, Macro Comment Statement](https://documentation.sas.com/api/docsets/mcrolref/9.4/content/mcrolref.pdf)
- LOG forms are fixed English read-count and output-count NOTE lines naming a
  literal WORK dataset, lines beginning `WARNING:`, and `real time`/`cpu time`
  with decimal-second values. The frozen fixture profile specifies exact tokens
  and explicit line-range-to-step associations; other formats, ERROR lines or
  missing completion evidence cannot be silently treated as a successful run.
- LST uses declared fixed-width columns, one title/header and a bounded row range.
  A numeric literal, `.` and an all-blank cell are distinct. Unexpected titles,
  columns, pagination or layout block interpretation. Layout metadata is allowed
  source evidence; it cannot supply the expected cell answers.

Public boundary tests must cover each excluded syntax family, including dataset
overwrites and macro-bearing comments. Hidden-case tests are additional; the
36-case semantic corpus is not claimed to exhaust the excluded SAS language.

### Numerical, ordering and state obligations

- Preserve expression structure, literal spellings, declared numeric attributes,
  comparisons, missing markers and assignment order. Do not reassociate arithmetic,
  choose tolerances, change population or repair apparent legacy mistakes.
- Positive numeric examples use ordinary numeric missing `.` and small finite
  exactly representable values with no overflow, division by zero or implicit
  conversion. Special missing values, date/time, formats/informats, character
  arithmetic, transcendentals and platform-specific rounding are blockers.
  Arbitrary decimal expressions can be recorded verbatim but receive no numeric
  equivalence verdict outside the approved profile.
- A sum statement has implicit retained state and treats a missing expression
  differently from ordinary addition. Its initialization/reset must be explicit
  in the canonical facts. [SAS sum statement](https://support.sas.com/documentation/cdl/en/lrdict/64316/HTML/default/a000289454.htm)
- A conditional LAG call advances its queue only when called. The interpretation
  must retain the guard, queue size and call-site identity, not describe it as
  the previous dataset row. [SAS LAG explanation](https://support.sas.com/kb/24/665.html)
- Numeric missing values precede ordinary numbers in SAS ordering. Preserve
  that distinction without generalizing to unsupported special/character values.
  [SAS missing-value order](https://support.sas.com/documentation/cdl/en/lrcon/62955/HTML/default/a000989180.htm)
- Concatenation, match-merge and SQL joins are different operations. A many-to-many
  DATA match-merge does not produce the SQL Cartesian combination within a key.
  Preserve the source operation and group advancement instead of replacing it
  with a familiar join. [SAS SET](https://support.sas.com/documentation/cdl/en/lestmtsref/63323/HTML/default/p00hxg3x8lwivcn1f0e9axziw57y.htm),
  [SAS DATA step statements, 9.4](https://documentation.sas.com/api/docsets/lestmtsref/9.4/content/lestmtsref.pdf?locale=en)
- FIRST/LAST boundaries depend on the ordered BY key list. Record sortedness as
  a precondition unless supported by fixture input evidence or a declared sort
  operation. Ties do not establish stable within-key order.
  [SAS BY statement](https://support.sas.com/documentation/cdl/en/lestmtsref/63323/HTML/default/p0yeyftk8ftuckn1o5qzy53284gz.htm)
- PROC SQL without ORDER BY provides no guaranteed output order. With nonunique
  ORDER BY keys, retain uncertainty about ties. Preserve ON/WHERE placement; do
  not claim a left join survives a subsequent filter unchanged.
  [SAS SQL ordering](https://support.sas.com/documentation/cdl/en/sqlproc/63043/HTML/default/p1jr2es0aus2qtn11peo724tt8f4.htm)
- Macro substitution must retain its definition/use chain and quote/dot behavior;
  a literal include is not authority to expand scope.
  [SAS macro references](https://support.sas.com/documentation/cdl/en/mcrolref/61885/HTML/default/a001071889.htm)

Hand-authored synthetic row traces can challenge these interpretations, but they
are independent expectations, not observed SAS outputs. No runtime tie-out or
general numerical fidelity claim follows from passing them.

## One canonical model: required versioned evolution

Observed compatibility gap: v1 operations contain kind, reads/writes, citations
and state flags, but no expression, reset, row-order or per-statement facts.
Log observations lack detailed step/unit/role and LST-cell representation. V1
reports and seals fix semantic status to UNVERIFIABLE and allow only P1 stages
and artifact names. Extra semantic fields are rejected. Merely attaching prose
to v1 would not make those requirements mechanically evaluable.

**Recommendation D08-B:** approve a narrow **canonical graph v2** and separate
versioned semantic-evaluation envelope during future implementation. This evolves
the existing graph; it does not introduce a parallel semantic graph or editable
IR. Leave v1 readers, schemas, artifacts and proof meaning intact. No schema is
created or changed in this checkpoint.

| Reused P1 primitive | Proposed narrow addition |
|---|---|
| Original-byte inventory, file IDs, source fingerprint, citations | Unchanged identity authority; explicit reference to inventory schema version |
| Operations, dataset/column nodes, typed edges and module ownership | Ordered nested semantic facts on their owning canonical record: expression, input mode, sort requirement, state initialization/reset, conditional queue call and macro binding |
| Unknowns/contradictions | Cited reason, affected statement/operation, missing proof and resolution state; no silently discarded source region |
| Log/run association | Step anchor, metric role, original value lexeme/unit, completeness and source role; bounded LST observation variant |
| Append-only attempts and seals | Explicit reconstruction/evaluation stage envelopes and artifact allowlists; new schema/version-aware validation dispatch |
| Derived coverage/views | Source-statement coverage and fact locators derived from the same graph; no competing module graphs |

Candidate semantic fields remain `UNVERIFIABLE`, authority `DRAFT`. The verifier
publishes verdicts against the exact immutable graph hash and fact locator. It
does not modify candidate facts, rewrite v1 reports, or self-grant human approval.
An evaluation result is a judgment about a graph, not another source record.

### Identity, granularity and ownership

1. Keep one operation per DATA step, one per supported CREATE TABLE statement,
   one per PROC SORT and explicit MACRO/INCLUDE reference operations. Represent
   statement-level semantics as ordered facts inside that operation. A single
   composed graph spans all modules; exactly one reconciler publishes it.
2. Each fact carries source citations and a stable locator within its canonical
   owner. Store a formula once at its assignment statement; operation-owned
   lineage facts name the affected column IDs. Columns do not hash a back-reference
   to their owning operation ID. Derived views can join graph/owner/fact locators;
   do not duplicate editable formulas or create column→operation→column hash cycles.
3. Reuse P1 ID derivation: source fingerprint plus all identity-bearing payload
   fields. Semantic additions/corrections therefore change operation IDs and
   dependent edges. Bind new operations to the same P1 file IDs/citations and
   record explicit predecessor graph/operation mappings when enriching v1.
   Never retain an old ID by hiding changed facts outside its hashed payload.
4. Build node IDs, then operation IDs, then edge IDs; semantic facts refer to
   node IDs and source anchors. Exclude back-references that would create hash
   cycles. Revision mappings are separate hash-bound lineage metadata, not input
   to their own identities or an assertion of semantic equivalence.
5. Output dataset names are unique in the pilot, avoiding unresolved dataset
   version/overwrite semantics. Repeated writes are a cited unsupported case;
   implementing general dataset versioning is not an accidental P2 dependency.
6. DATA edges require both structural producer/consumer agreement and semantic
   support. STATE edges may be self-edges for row-to-row state. ORDER edges need
   a specific ordering obligation, not merely adjacent source lines. Do not
   emit RESOURCE opportunities or infer independence from missing edges.
7. Macro-expanded tokens retain original definition/use/include citations; no
   generated token receives a fabricated original-source span. Macro/include
   changes invalidate the full P1 fingerprint and all affected evaluations.

The pack's “DAG” wording is interpreted as a **derived visualization** of the
canonical dependency graph, not a claim that all source behavior is acyclic.
Preserve state cycles and UNKNOWN edges. Any Mermaid view references canonical
IDs/hash; no scheduling DAG, critical path, waves or parallelization advice is P2.

## Proposed reconstruction and checking flow

An explicit P1 inventory/seal is required first. Its schema, byte/hash, identity
and scope checks must be sound; a complete sealed inventory can nevertheless
have an overall BLOCKED gate for named unresolved provenance/dependency facts.
Such facts may be inspected in the uncertainty lane, are carried forward, and
prohibit semantic PASS. Do not relabel the P1 attempt or use `verify-source` to
upgrade it. Failed/stale/partial/unsealed inputs are ineligible for semantic
verification and receive only structural failure diagnostics.

A bounded lexical/framing layer
accounts for every source statement; it does not execute source. Reconstruction
uses only authorized immutable source evidence and the declared semantics profile.
Unknown syntax or hidden context causes a named evidence request within the
existing scope, or BLOCKED if that scope cannot answer it. A literal missing
include remains unresolved until a human authorizes a new scope and attempt.

Candidate output must pass versioned deterministic structure/identity checks
before a separate source-aware reviewer challenges its facts. That reviewer sees
source and candidate, not evaluator gold. A trusted evaluator separately compares
candidate facts and reviewer verdicts to independently authored expectations.
Details and mandatory isolation tests are in the evaluation design.

LOG/LST text cannot create source/run provenance. Only explicit fixture execution
and step associations permit observations. A missing required log blocks a
runtime-observation claim but does not erase independently supported static facts.
Contradictory source/log evidence is preserved with both locators and yields FAIL
for the affected determinate claim. Missing evidence yields BLOCKED, not invented
success. All synthetic timing observations retain benchmark `NOT_RUN`.

## Bounds and implementation dependencies

Proposed case limits: at most 20 SAS/include files, 10,000 source lines, 100
operations, eight modules and include depth five; all existing stricter P1 byte,
path and JSON limits remain. No source/file auto-expansion. Exceeding limits
blocks explicitly. Withheld fixtures should be small enough for their registered
budget; pressure cases test refusal and retrieval, not hidden truncation.

Proposed model budget per role/case: at most three model calls, 32,000 total input
tokens, 8,000 total output tokens and five minutes. Count all retrieval/model
calls; report unknown provider usage as unknown. These are budget recommendations,
not measured optimal settings. Development repair is at most three total attempts
with a stop after two repeated failures without new evidence. Withheld acceptance
runs receive no per-case answer feedback or adaptive repair.

No provider, model revision or isolated execution host has been selected. Human
approval must name them and the allowed tools/data-egress policy. Recommend a
configurable pinned model adapter with read-scope/write-staging tools only; no
unrestricted host shell. A trusted broker may contact the specifically approved
model endpoint with synthetic inputs; the candidate has no general network or
gold access. The evaluator is deterministic and has no model-network path.

After approval, implementation should proceed in independently checked increments:

1. Versioned canonical semantic contract and v1 regression compatibility; frozen
   public fixture grammar and scoring obligations. Do not rewrite old seals.
2. Separate candidate/reviewer/evaluator identities and denied-access tests;
   independently authored, reviewed and frozen hidden gold. No independence claim
   before those tests pass.
3. Bounded candidate reconstruction, statement coverage, independent source-aware
   checks and graph-derived views for the declared subset only.
4. Both evaluation lanes, reproducible reports and a synthetic demo; stop for
   review. PRD/ADR generation, architecture selection, optimization, private intake,
   translated code, SAS execution and downstream integration remain excluded.

## Required approval and future P2 acceptance

Approve the subset/profile and granularity (D08-A), narrow canonical v2 evolution
and explicit ID lineage (D08-B), and execution provider/tool/budget/environment
(D08-C). Approve corpus, gold ownership, isolation and thresholds under D09.
Named people, actual model revision and isolation host remain missing; recommendations
are not substitutes for those decisions.

Future P2 is acceptable only if all of the following are demonstrated:

- All 138 current P0/P1 tests still pass; old v1 structural PASS retains exactly
  its original meaning. New contract/version/ID lineage tests pass without
  weakening P1 path, scope, provenance or publication checks.
- Every declared source statement is accounted for; required supported facts,
  producer/column lineage, ordering and state agree with independent gold.
  Unsupported/ambiguous regions carry explicit citations and correct blockers.
- Valid-citation/false-conclusion and hidden-state/dependency cases receive the
  exact expected semantic verdict and gate, including counterevidence.
- The evaluator isolation, gold immutability and immutable candidate handoff
  tests pass; all frozen pilot cases run in both evaluation lanes with the
  coverage/precision/recall/zero-critical-false-approval conditions specified
  in [P2_EVALUATION_DESIGN.md](P2_EVALUATION_DESIGN.md).
- Source/include/log changes invalidate evaluations through canonical hashes;
  attempts remain append-only; no raw private data, fabricated measurement,
  execution, human-approval claim or downstream mutation occurs.
- Development, fresh-checkout and installed-wheel checks, hosted CI, exact
  evaluator/environment hashes and actual commands/results are recorded. Missing
  isolation infrastructure or failed critical cases means BLOCKED/FAIL, not PASS.

All future P2 extraction, semantic evaluation and isolation tests are **NOT_RUN**
at this planning checkpoint. Approval of these documents must be followed by an
explicit implementation instruction; the plan does not itself start P2.
