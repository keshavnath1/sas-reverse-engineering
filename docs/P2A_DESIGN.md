# P2A deterministic semantic reconstruction foundation

P2A implements the user-approved D08-A/B subset from the planning baseline
`e13705c67c5984b2cb6bc8d4c797a188fd6421e2`. D08-C and D09 remain open for P2B.
This is a static, synthetic-only implementation: **semantic acceptance BLOCKED,
semantic verification UNVERIFIABLE, authority DRAFT, benchmarks NOT_RUN**.
Public tests establish tested reconstruction behavior, not independent reliability.
Actual checks and failures are recorded in [P2A_VALIDATION.md](P2A_VALIDATION.md).

## Authority and compatibility

The exact specification ZIP remains SHA-256
`e3cbf3d9df6cc20c594261556c5e3ea1dfc292c9c1a30672c2d7b1a736b9718e`.
Pack document 02 controls workflow; 04 requires independent evidence checks;
06 describes reconstruction; 10 supplies implementation expectations. The user's
P2A/P2B split supersedes the earlier requirement to provision an isolated evaluator
before any deterministic P2 work. It does not waive that requirement for acceptance.

Agent-mastery remains a read-only reference pinned to
`bc754e0f1204a99020c864df2a5b25983005e09c`. No downstream formats, gates or files
change. REA is not used as a SAS parser. No agent framework or model is selected.

The v1 schema bytes and P1 identity/publication primitives remain unchanged.
`validate_contract()` still defaults to v1; v2 requires an explicit version or
the opt-in `validate_versioned_contract()` dispatcher. P1 `seal-source` rejects
v2 graphs. Historical reports keep their original structural-only meanings.

## Canonical graph v2

The composed graph remains the sole factual artifact. V2 adds ordered facts to
their owning operation, original byte spans and P1 line citations, expression
trees with literal lexemes, numeric policies, state effects, cardinality and
ordering contracts, data/control lineage, and statement coverage. Parser objects
exist only transiently while composing this graph; they are not another persisted
source of truth. Module views contain IDs and the parent graph hash only.

Original-byte P1 inventory, file identities, scope fingerprint and citation rules
remain authoritative. The CONFIG profile is an authorized source file: its bytes
participate in the fingerprint and are rechecked. New graph records use the P1
payload-hash algorithm. Semantic payload changes yield new operation/edge IDs;
unchanged facts and scope retain their IDs across new attempts. Column/node IDs
are computed before operation IDs and edges, avoiding circular hash definitions.

There is one operation per DATA step, SQL CREATE, SORT, macro binding/reference,
or include. Assignment facts retain statement order and definition/use anchors.
Lineage references source column IDs and earlier fact indexes; conditional and
selection dependencies are recorded separately. State dependencies can be self
edges. No missing edge establishes independence or an optimization opportunity.

Enrichment from a sealed v1 record produces a separate hash-bound revision map
in the reconstruction report: predecessor/current graph hashes, added/removed/
retained operation IDs and overlapping-source-anchor mappings. The mapping says
`semantic_equivalence: NOT_ASSERTED`. It does not rewrite old evidence or preserve
an old operation ID after changing its meaning. An inventory-only predecessor has
no operation lineage and therefore a null revision map.

## Closed source profile

The normative allowlist and excluded language families remain in
[P2_READINESS.md](P2_READINESS.md). Implemented forms include constrained numeric
DATA assignments/IF/KEEP/DROP; single/two-input SET concatenation; two-input BY
match-merge; one/two-key BY and FIRST/LAST; single-variable RETAIN, sum statements
and guarded call-site LAG/LAG2; distinct-output PROC SORT; one-table SQL or a single
INNER/LEFT equality join with explicit aliases, numeric WHERE and optional ORDER
BY; literal open-code macro definitions/references; and authorized literal includes.

Includes are expanded at their encounter position, using only a declared INCLUDE
dependency and authorized bytes. Complete blocks and statement fragments preserve
the original file/byte spans of each fact. No fabricated span is assigned to
expanded text. Repeated, cyclic, missing, dynamic or escaping includes are blocked.
Unreached authorized SAS/include files are explicit unknowns. Source comments and
LOG/LST instructions cannot execute tools or grant approval; macro-sensitive SAS
comments are not silently discarded as semantically inert text.

The profile document is strict JSON in a declared CONFIG file:

- `schema_version: "2.0"`, `profile_id: "sas94-synthetic-v1"` and ordered
  authorized SAS `entrypoints`.
- `inputs`: explicit WORK datasets, module owner, NUMERIC length-8 columns,
  synthetic rows as original decimal/missing lexemes, and declared ascending keys.
- `numeric_missing_join_policy`: explicitly
  `SAS_ORDINARY_MISSING_EQUALS_MISSING` or `UNRESOLVED`. This is language context,
  not a supplied expected answer. Unknown policy blocks affected missing-key joins.
- `log_bindings` and `lst_bindings`: declared P1 association, exact original
  operation-file/byte-start anchor, inclusive line range and completeness declaration.
  LST additionally declares title, header/data lines and named fixed-width columns.

Inputs with undefined schemas, unsafe authorization or malformed contracts cannot
be silently made valid. Sortedness declarations are checked against synthetic
input rows; contradictory ordering is retained as a contradiction. Derived source
sorts provide conditional ordering support, not proof that a SAS run happened.
SQL has unspecified order without ORDER BY and unspecified tie order even with it.
DATA match-merge cardinality/state remains distinct from SQL join multiplicity.

Numeric expressions retain their exact source tree and statement sequence. The
pilot uses ordinary missing plus small exactly representable finite values;
special missing, implicit conversions, unsupported rounding/overflow behavior and
unproved state recurrences are unresolved. Conservative rational bounds check
preconditions without running SAS or producing translated rows. A blocker can
remain even for a mathematically exact expression if this checker cannot prove
its preconditions. Hand-authored row traces in public fixtures are expectations,
not observed outputs or a general runtime equivalence test.

## Fixed LOG/LST observations

English LOG templates are deliberately closed:

```text
NOTE: There were N observations read from the data set WORK.NAME.
NOTE: The data set WORK.NAME has N observations and M variables.
WARNING: text
real time DECIMAL seconds
cpu time DECIMAL seconds
```

Optional exact DATA/PROCEDURE SORT/PROCEDURE SQL process headers must match the
bound operation; conflicting headers are contradictions and repeated headers
are ambiguous. Each complete segment needs output-count, real-time and CPU-time
lines plus the explicit completeness declaration. Neither the declaration nor
synthetic timing text authenticates an actual execution. ERROR lines contradict
success; unknown templates, units, unbound lines, overlaps and incomplete metrics
remain blockers. Read/output datasets and output column counts are checked
against the bound operation. Warning content stays available through its citation.

LST is one declared fixed-width layout. Column names must be unique, ranges must
not overlap, and titles/headers/rows must fit. Cell observations retain exact
lexemes, physical source citations, table-row index, column, and NUMBER/MISSING/
BLANK distinction. Extra pages, text cells, truncated rows and unbound lines block.
No report layout is treated as an entire output dataset or a statistical model.

## Workflow, validators and proof limits

`reconstruct-source` requires an exact sealed P1 INVENTORY or RECORD attempt and
creates a new v2 RECONSTRUCTION attempt. A sound sealed P1 BLOCKED inventory can
be inspected, with all unknowns carried forward. A failed, stale or incomplete
subject is ineligible. `check-reconstruction` selects an exact v2 attempt, reloads
its predecessor and verifies freshness, seals, lineage and deterministic consistency
in a new RECONSTRUCTION_CHECK attempt. There is no newest-by-time selection.

The source checker validates the closed v2 contract and compares the submitted
graph to deterministic reconstruction from the authorized evidence. It catches
the tested false expressions, dependency/order/state claims and observations even
when citations and payload IDs are valid. **The checker shares reconstruction
logic. It is not an independent semantic reviewer.** Schema rejection and
source-consistency rejection are reported separately in public regression tests.

Reports distinguish structural verification, source consistency, reconstruction
COMPLETE/PARTIAL/NOT_RUN, and semantic acceptance. A supported complete source can
have `source_consistency: PASSED` while the stage gate remains `BLOCKED` because
P2B has not run. Contradictions or invalid evidence produce FAIL. CLI exits are
0 for successful status/P1 operations, 1 for FAIL, 2 for BLOCKED, and 3 for future
commands. No P2A path grants VERIFIED or HUMAN_APPROVED semantics.

P1 safe descriptors, exact file scope, no-follow reads, traversal/hardlink/symlink
refusal, disjoint output roots, exclusive attempt reservation and seal-last atomic
publication remain in use. The artifact allowlist is unchanged; versioned reports
and graphs occupy the existing JSON filenames. Original sources are read-only.
The local filesystem owner remains trusted; hashes are not provenance signatures.

Bounds include 20 SAS/include files, 10,000 source lines, 100 operations, eight
modules, include depth five, plus P1's 8 MiB/file and 64 MiB/scope limits. Lexer,
expression-depth/node and profile bounds are enforced with explicit refusal.
No token/model budget is consumed: D08-C has not selected a provider or runtime.

## Public review and P2B readiness

[P2A_FIXTURE_REVIEW.md](P2A_FIXTURE_REVIEW.md) records separate expected-answer
authorship and review before the public semantic assertions were used. It does
not claim OS isolation or human expert certification. Public examples and error
messages are development material and must never be relabeled withheld gold.

Next, separately approve D08-C and D09: name the SAS gold author, second reviewer
and custodian; choose model/provider revisions and egress/budget rules; provision
the Linux isolation host and evaluator-owned store; freeze source/expected-answer
versions and scoring denominators; test access denial and immutable handoff before
loading gold. Only then authorize P2B's 36-case, five-attempt, two-track campaign
and zero-critical-false-approval gate from [P2_EVALUATION_DESIGN.md](P2_EVALUATION_DESIGN.md).

P2A stops here. No private workload, SAS execution, protected-gold infrastructure,
PRD/ADR, translated code, runtime recommendation, parallelization or downstream
integration is implemented or authorized by this checkpoint.
