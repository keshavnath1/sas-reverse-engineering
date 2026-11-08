# Engineering-practice adoption and evidence ledger

Prepared 2026-11-05. Historical project baseline:
`56154dd75a0149043c36081da9704b0a939230e1` (accepted P2A).
This is a retrospective comparison with Jim Thompson's published practices,
not proof that every historical action was caused by those guides. Alignment
with a practice does not establish reduced cost, latency or defects.
P2B is at a documentation-only readiness checkpoint; execution remains BLOCKED.

## Sources and attribution

Primary guidance was read from `jimthompson5802/coding-assistant-practices` at
commit **`abdf5661855dae25e002578fe25c961a6200db5d`**, verified through the GitHub
connector on 2026-11-05. This is the same tip recorded in the original project
plan; this assessment read the actual pinned guide files. The sources below are
paraphrased and linked, not imported as repository instructions or software.

| ID | Primary source | Practice used in this ledger |
|---|---|---|
| J0 | [README](https://github.com/jimthompson5802/coding-assistant-practices/blob/abdf5661855dae25e002578fe25c961a6200db5d/README.md) | Guide index and limitations of local usage counters |
| J1 | [Model selection](https://github.com/jimthompson5802/coding-assistant-practices/blob/abdf5661855dae25e002578fe25c961a6200db5d/model-selection-guidance.md), common-practice sections 1.1–1.8 | Match capability to task; assess cost per successful outcome |
| J2 | [Planning practices](https://github.com/jimthompson5802/coding-assistant-practices/blob/abdf5661855dae25e002578fe25c961a6200db5d/coding-assistant-planning-practices.md), 1.1–1.12 | Repository-aware, proportional plans, stages, acceptance and developer gates |
| J3 | [Open and closed loops](https://github.com/jimthompson5802/coding-assistant-practices/blob/abdf5661855dae25e002578fe25c961a6200db5d/open-vs-closed-loop-practices.md), sections 2 and 4 | Observable feedback, bounded correction and verification integrity |
| J4 | [Subagents](https://github.com/jimthompson5802/coding-assistant-practices/blob/abdf5661855dae25e002578fe25c961a6200db5d/subagent-practices.md), 1.1–1.9 | Bounded delegation, separate review and central reconciliation |
| J5 | [Context management](https://github.com/jimthompson5802/coding-assistant-practices/blob/abdf5661855dae25e002578fe25c961a6200db5d/context-window-management.md), 1.1–1.8 | Progressive retrieval, focused tasks and durable milestones |
| J6 | [Cache guidance](https://github.com/jimthompson5802/coding-assistant-practices/blob/abdf5661855dae25e002578fe25c961a6200db5d/cache-token-guidance.md), 1.2–1.8 | Stable reusable context and measurements with explicit limits |

The pinned repository's MIT license was inspected. Product-specific examples in
these guides are the author's guidance, not verification of this account's model
availability, pricing, retention or cache controls. No counter scripts were run,
no user session logs inspected and no usage values inferred from missing logs.

The supplied v2 ZIP remains SHA-256
`e3cbf3d9df6cc20c594261556c5e3ea1dfc292c9c1a30672c2d7b1a736b9718e`.
Its `docs/10_ENGINEERING_PRACTICES_TO_EXECUTABLE_CONTROLS.md` is the project's
adaptation of guidance into proposed controls, SHA-256
`c562f8de0fb90b4ec2230e7be7a2836fd67085d9e6eb29e6826192fc262ee1da`.
Its embedded `references/Jim Thompson Best Practices_ A Deep Learning Guide.md`
lists **Manus AI** as author and is a secondary explanatory guide, SHA-256
`d373d4599488514b2954c4f6c08909fb4bc4c9daef06b45cab66492ac2bd9a76`.
Do not attribute that secondary text to Jim as a direct quotation. Pack documents
01/08/10 require a later evidence showcase; their proposed demonstrations are not
results. The separate embedded Agent-mastery audit's reported 43 tests were not
rerun here and do not establish this repository's behavior.

## Status rules

- **DEMONSTRATED:** an attributable existing commit/report/test record supports
  the exact narrow claim. It does not imply independent reproduction in this audit.
- **PARTIAL:** some components are evidenced but a material part of the practice
  or its proof remains missing. The missing part must be named.
- **NOT_APPLICABLE:** deliberately outside that phase's authorized scope; state
  why. This status is not a passing score or a waiver for a later phase.
- **NOT_VERIFIED:** proposed, absent, unmeasured or not supported by retained
  evidence. Unknown usage is not zero usage; unrun work is not a failure rate.

These are documentation assessment labels, not new product enums or semantic
verdicts. No aggregate adoption percentage is calculated. One practice can be
demonstrated for a bounded control while its broader effectiveness is unverified.

## Historical evidence register

| Evidence ID | Immutable implementation / record | What it supports and does not support |
|---|---|---|
| E0 | P0 implementation [`2c34b98`](https://github.com/keshavnath1/sas-reverse-engineering/commit/2c34b9838308012b545010b84044ae2fc803375b), report/correction [`6893fd2`](https://github.com/keshavnath1/sas-reverse-engineering/commit/6893fd2e7a2bde1f3333ffb65dafb8c1698afcb3); [P0 validation](P0_VALIDATION.md) | 25 distinct foundation tests across three install modes; pinned baselines, blocked placeholders, staged-content guard and corrected YAML. Recorded read-only reviewer did not execute tests. Hosted CI was NOT_RUN at that historical checkpoint |
| E1 | P1 implementation [`0e1f682`](https://github.com/keshavnath1/sas-reverse-engineering/commit/0e1f6822871d3aa6956695a776672b63454c7958), report [`5c8aea7`](https://github.com/keshavnath1/sas-reverse-engineering/commit/5c8aea7588290925250b76c9cbd5091a3ea89f13); [P1 validation](P1_VALIDATION.md) | 138 cumulative tests, development/fresh/wheel and separately recorded review run; citations, scope, races/crashes, append-only attempts and false-authority rejection. Structural evidence only |
| E1-CI | [Run 42094717277](https://github.com/keshavnath1/sas-reverse-engineering/actions/runs/42094717277) at `0e1f682` | Historical report records both jobs and 138 checkout/wheel tests passing; not evidence of independent semantics |
| E2 | P2 planning [`e13705c`](https://github.com/keshavnath1/sas-reverse-engineering/commit/e13705c67c5984b2cb6bc8d4c797a188fd6421e2); P2A implementation [`e5f5eb2`](https://github.com/keshavnath1/sas-reverse-engineering/commit/e5f5eb2fde973acf2dd059b4522247aa6fd2283c); report updates `7da79ab` and [`56154dd`](https://github.com/keshavnath1/sas-reverse-engineering/commit/56154dd75a0149043c36081da9704b0a939230e1); [P2A validation](P2A_VALIDATION.md) | 389 cumulative tests; 187 public tests; 26 valid-citation mutations, of which 22 pass schema and fail source consistency, four fail closed schema. Complete reconstruction still has BLOCKED semantic acceptance |
| E2-CI | [Recorded run 42104309091](https://github.com/keshavnath1/sas-reverse-engineering/actions/runs/42104309091) at `7da79ab`; [accepted run 42104609308](https://github.com/keshavnath1/sas-reverse-engineering/actions/runs/42104609308) at `56154dd` | Exact hosted records, distinct from local runs and later commits. CI success is regression evidence, not evaluator isolation |
| E2-R | [Public fixture review](P2A_FIXTURE_REVIEW.md) at accepted P2A baseline; [expectations](../tests/p2a_expectations.py) | Separate expectation author did not read candidate implementation/output; root reviewed before consumption. Same development environment, no human SAS certification or protected gold. Reviewed expectation SHA `f42549738a041db87d3547adec59ddfd0f9b15aa2621f1cf0b7ea7fa9f7ffd93` |
| EG | [Implementation plan](IMPLEMENTATION_PLAN.md), [approvals](APPROVALS.md), [decisions](OPEN_DECISIONS.md); historical versions at accepted P2A commit | Recorded user scope gates and deferred decisions; publication authorization does not approve later phases or downstream release |
| EB | [P2 evaluation design](P2_EVALUATION_DESIGN.md) and [P2B readiness](P2B_READINESS.md) | Proposed ownership, isolation, costs and strict gates. No deployed controls, gold or campaign results |

Local document/test links are navigation aids. Historical claims bind the immutable
commits above; later edits must not rewrite those past results. Counts 25 → 138 →
389 are overlapping cumulative suites, not additive distinct tests. Repeating a
suite in three installation modes does not create three independent semantic
samples. Reported test durations measure test runs, not assistant productivity,
SAS workload performance or cost savings.

## Phase-by-phase ledger

Each cell is limited by its evidence IDs and the qualifications below. Future
means P3–P7; none of those phases is authorized by this checkpoint.

| Practice / bounded claim | P0 | P1 | P2A | P2B | Future |
|---|---|---|---|---|---|
| J2: repository-aware plans, acceptance criteria and phase gates | DEMONSTRATED E0/EG | DEMONSTRATED E1/EG | DEMONSTRATED E2/EG | PARTIAL EB: readiness only | NOT_VERIFIED |
| J5: durable plans/decisions and versioned checkpoints | DEMONSTRATED E0 | DEMONSTRATED E1 | DEMONSTRATED E2 | PARTIAL EB: no evaluator checkpoints | NOT_VERIFIED |
| J3: executable feedback and preserved regressions | DEMONSTRATED E0 | DEMONSTRATED E1 | DEMONSTRATED E2 | NOT_VERIFIED | NOT_VERIFIED |
| J3: verification integrity and explicit proof limits | DEMONSTRATED E0 | DEMONSTRATED E1 | DEMONSTRATED E2 | PARTIAL EB: protocol only | NOT_VERIFIED |
| J5: focused progressive context, with actual retrieval evidence | PARTIAL E0/EG | PARTIAL E1 | PARTIAL E2 | NOT_VERIFIED | NOT_VERIFIED |
| J1: task-appropriate capability and evaluated model selection | PARTIAL E0 | PARTIAL E1 | PARTIAL E2 | NOT_VERIFIED, D08-C open | NOT_VERIFIED |
| J3: bounded correction with enforced retry/escalation policy | PARTIAL E0 | PARTIAL E1 | PARTIAL E2 | NOT_VERIFIED | NOT_VERIFIED |
| J4: separate development review and central integration | DEMONSTRATED E0, narrow review record | DEMONSTRATED E1 | DEMONSTRATED E2-R | NOT_VERIFIED for deployed roles | NOT_VERIFIED |
| J4: subagents improve quality/latency/total usage versus serial work | NOT_VERIFIED | NOT_VERIFIED | NOT_VERIFIED | NOT_VERIFIED | NOT_VERIFIED |
| Project adaptation: protected independent semantic evaluation | NOT_APPLICABLE, foundation | NOT_APPLICABLE, structural scope | PARTIAL E2-R, public review only | NOT_VERIFIED | NOT_VERIFIED |
| J1/J6: authoritative token/cache/billing and cost comparisons | NOT_VERIFIED | NOT_VERIFIED | NOT_VERIFIED | NOT_VERIFIED | NOT_VERIFIED |
| J2/project adaptation: phase scope respected; no self-approval | DEMONSTRATED E0/EG | DEMONSTRATED E1/EG | DEMONSTRATED E2/EG | PARTIAL EB, planned gates | NOT_VERIFIED |
| Project adaptation: runtime benchmarks and architecture adoption | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE to semantic pilot | NOT_VERIFIED |

Qualifications and counterevidence are part of the ledger:

- **Focused context:** plans and citations provide focused entry points; P1
  enforces file scope and P2A bounds syntax/source size. These do not show which
  context an assistant actually loaded, whether retrieval omitted dependencies,
  or whether context/latency improved. A future role retrieval ledger and
  quality-matched comparison are missing. This checkpoint read-only delegation
  is not a usage experiment.
- **Model choice:** deterministic code is appropriate for hashes, paths and
  bounded reconstruction, but no product provider/model routing was evaluated.
  Development assistant usage is not product evaluation usage. The proposed
  deterministic candidate in P2B readiness remains a human decision.
- **Bounded repair:** reports preserve concrete failures/fixes, explicit attempts
  and source invalidation. There is no implemented end-to-end agent retry-budget
  controller or complete historical retry ledger. Parser limits are not agent
  repair limits. Do not backfill a compliant retry count from successful commits.
- **Separate review:** P0 recorded independent read-only review without a suite
  rerun; P1 recorded separate probes and tests; P2A recorded public expectation
  authorship/review and cross-reviews. Shared environment and shared source-checker
  logic prevent a claim of independent semantic acceptance.
- **Human ownership:** current contracts/status behavior reject false upstream
  approval and keep future commands blocked. The upstream repository does not
  establish an authentic downstream signature or enforce Agent-mastery's entire
  approval chain. Downstream integration has not been implemented or tested.
- **Metrics:** no observed token, cache, invoice, total-agent-cost or productivity
  comparison is in the cited phase records. Cache hits cannot be inferred from
  stable prompts. Upstream scripts' ability to report usage is not evidence that
  they were used here. Missing telemetry stays NOT_VERIFIED.

Concrete feedback examples already in the records:

| Phase | Finding and response | Retained proof and limit |
|---|---|---|
| P0 | Corrected workflow YAML quoting and staged-content secret-guard gap | E0 command/results and regression; not complete data-loss prevention |
| P1 | Rejected forged inventory citations, detected cross-file mutation and clarified ambiguous observations | E1 failures/fixes and [workflow tests](../tests/test_runs.py)/[safe I/O tests](../tests/test_safeio.py); integrity, not SAS meaning |
| P2A | Corrected source anchors, conservative state/numeric bounds, ordering propagation and LOG/LST ambiguity | E2 failures/fixes and [graph tests](../tests/test_p2a_graph.py)/[workflow tests](../tests/test_p2a_runs.py); reviewed public expectations were not weakened to fit outputs, according to E2-R |

## Pack showcase obligations and later phases

| Pack document 10 demonstration | Current status | Evidence required for the broader claim |
|---|---|---|
| Scoped retrieval versus loading every log | NOT_VERIFIED | Authorized comparable tasks, retrieval spans, dependency recall, total context/latency measurements |
| Independent rejection of a false ADR with a valid citation | NOT_APPLICABLE to completed phases; future NOT_VERIFIED | Independently evaluated ADR verifier and exact counterevidence; P2A graph mutations are narrower public regressions |
| Missing evidence stops with UNVERIFIABLE | DEMONSTRATED for P1/P2A's bounded controls | E1/E2; no generalized arbitrary-SAS coverage claim |
| Source changes invalidate checkpoints and ADRs | PARTIAL | E1/E2 demonstrate checkpoint invalidation; ADR invalidation is future NOT_VERIFIED |
| Selective subagents versus serial investigation | NOT_VERIFIED | Same authorized tasks, quality gates, total calls/usage/retries and elapsed-time evidence; agent count alone is insufficient |

| Future phase | Practice obligation to carry forward | Status and required evidence |
|---|---|---|
| P2B | Separate ownership, protected expected facts, bounded roles, frozen feedback and observable costs | NOT_VERIFIED; named custody, reviewed sentinel proof, real capability matrix, immutable handoff and full preregistered attempt ledger |
| P3 | Evidence-driven challenge of proposed computation changes | NOT_VERIFIED; authorized implementation and independent counterexamples before any safety claim |
| P4 | Separate exploration, closed review and human decision on requirements/design drafts | NOT_VERIFIED; claim-to-source links, independent review and unresolved assumptions; no fabricated comparisons |
| P5 | Repeated independent verification as skills/contracts change | NOT_VERIFIED; versioned evaluators, access controls and complete negative-case records; P2B is an earlier bounded prerequisite, not completion of all P5 work |
| P6 | Reproducible draft handoff with explicit compatibility limits | NOT_VERIFIED; immutable manifest, stale/tampered rejection and no approval impersonation |
| P7 | Human-owned downstream reconciliation and approval | NOT_VERIFIED; separately authorized integration and demonstrated non-bypass at the frozen downstream baseline |

These are evidence obligations, not new PRDs, ADRs, parallelism designs or
authorization to implement those phases. No claimed runtime winner, speedup or
full-population parity follows from the practice ledger.

## Proposed final best-practices evidence report

Create a final report only at a separately authorized completion checkpoint;
the proposed name is `docs/BEST_PRACTICES_EVIDENCE_REPORT.md`. It should contain:

1. Immutable guide/pack/product/evaluator/environment identities, authorized
   scope, dates and an evidence index separating observed, reported and proposed.
2. A claim-level ledger: practice ID, project adaptation, phase, one of the four
   statuses, immutable evidence pointer, counterevidence, limitations and
   accountable reviewer. Preserve this historical ledger as the baseline.
3. Planned versus observed stages and approval boundaries; exact commands, exit
   codes, artifacts/hashes and installation/CI identity. Note unavailable logs.
4. Failure/correction history with attempt IDs, hypothesis, owning component,
   original failure and final outcome; no erased attempts or altered oracle.
5. Independence evidence: named gold author/reviewer/custodian, actual effective
   access policy, positive/negative sentinel controls, handoff receipts, gold
   freeze and leakage review. Development agent separation is not a substitute.
6. Full finite-pilot results: preregistered obligations and denominators, all
   scheduled/attempted/completed cases, abstentions, critical errors, stops and
   retained limitations. Public fixture tests stay separate from withheld results.
7. Efficiency evidence only for separately authorized comparisons: same tasks
   and quality gates, frozen configurations, total candidate/reviewer/retry usage,
   provider-observed units, wall time, documented rates and actual charges
   distinguished. Human effort requires recorded observations, not reconstruction.
8. Gaps and future obligations, downstream boundaries and a sanitized public
   summary. Protected answers, detailed hidden-case diagnostics and credentials
   remain outside the public report and Git.

For any later efficiency comparison, preregister the quality/correctness gate,
baseline, task set and stop rule. Include failed attempts in cost per successful
task; account for all roles and retries, not only the winning answer. Distinguish
input totals from included cached subsets so tokens are not counted twice.
Report cache discounts only from supported authoritative accounting. Model or
tool changes need a separately frozen comparison; do not tune against hidden
acceptance feedback. No such experiment is authorized or measured here.

Acceptance criteria for that report:

- Every DEMONSTRATED claim resolves to an immutable record supporting its exact
  scope. Recorded versus independently rerun results are distinguished.
- Every PARTIAL/NOT_VERIFIED item names its missing evidence; NOT_APPLICABLE has
  a phase-specific reason. No invented historical usage or adoption percentage.
- Full attempt and obligation totals reconcile, with critical failures,
  incomplete work and stopped entries retained. No best-of-five or weakened gates.
- Independence claims require named accountable ownership and tested deployment
  boundaries, not model disagreement, public fixture tests or separate chats.
- No savings or reliability claim is inferred from test counts, agent count,
  suite durations, hypothetical rates or unseen invoices. Unavailable metrics
  remain unavailable; a truthful report may remain PARTIAL.
- P0/P1/P2A compatibility/regression evidence binds exact commits and hashes;
  semantic PASS, benchmark execution and human approval remain distinct.
- A custodian reviews public output for leakage, and a named human reviewer
  approves the report's scope and limitations. This does not grant downstream
  release approval or authorize unfinished phases.

## This checkpoint's evidence boundary

The assessment used existing Git records, repository reports/test names,
read-only ZIP inspection/hash checks and pinned upstream guide reads. It did not
rerun historical suites locally, inspect private intake/session logs, execute
usage counters, create gold or perform access-isolation tests. Exact current
documentation checks are recorded in [P2B_READINESS.md](P2B_READINESS.md).
Readiness plans and a practice ledger are the deliverables; they are not a
successful P2B evaluation or an effectiveness measurement.

## CP1 bounded update

CP1 is separately authorized at portability baseline
`1c172fbb79a8ba07bf72f2f40ecf0f5db02b564a`; see [design](CP1_DESIGN.md) and
[actual validation](CP1_VALIDATION.md). Historical phase entries above are unchanged.

| Practice | CP1 evidence and limit |
|---|---|
| J2/J5: bounded scope and durable plan | Explicit CP1 approval, design and validation record; CP2–CP5/P2B/P3 remain unapproved |
| J3: executable feedback and preserved verification | Original regressions plus capability-denial tests, frozen hashes, unchanged moved-function ASTs and baseline/candidate artifact-byte comparison; exact failures/corrections recorded in validation |
| J4: focused delegation and central review | Separate read-only boundary/preservation audits and focused-test author; root reconciled findings including missing regex import and insufficient fcntl-member probing. Shared development environment, not protected independent semantics |
| J3: explicit proof limits | Simulated Windows selection is distinct from actual execution; native Windows qualification remains BLOCKED without an approved environment |
| J1/J6: efficiency, model choice and cost | NOT_VERIFIED; no provider comparison, usage/cache/billing telemetry or savings claim. Test durations are not workload benchmarks |

These records demonstrate bounded engineering controls, not native Windows
production readiness, semantic acceptance or a completed portability project.

## CP2 bounded update

CP2 is separately authorized at `0061b7bf038f7b36add830912258232f174af197`;
see [design](CP2_DESIGN.md), [validation](CP2_VALIDATION.md) and [approval](APPROVALS.md).
Historical phase records above are unchanged.

| Practice | CP2 evidence and limit |
|---|---|
| J2/J5: explicit scope and durable decisions | Independent input contract, fixed legacy projection and stop before binding consumption; CP3–CP5/P2B/P3 remain unapproved |
| J3: observable feedback and integrity | Frozen-schema/source/artifact comparisons, original regressions, malformed input and no-I/O sentinels; exact commands/failures/corrections in validation |
| J4: bounded delegation and separate review | Read-only contract audit, separate path-policy author, independent golden-vector author using frozen rules before reading candidate code; root reconciled API semantics and complete-path bounds |
| J3: independent expected facts | Literal preimage and pinned hashes checked with a separate hashlib/JSON oracle and frozen inventory pipeline; public shared-environment development evidence, not protected SAS semantic acceptance |
| J3: honest qualification/authority | Declaration validation grants no physical access or authenticated human approval; simulated Windows checks never count as native execution |
| J1/J6: efficiency and cost | NOT_VERIFIED; no usage/cache/invoice telemetry, model comparison or productivity claim |

These controls demonstrate bounded identity compatibility and unchanged evidence
boundaries. They do not establish native Windows readiness or benchmark results.

## CP3 readiness evidence update

This is a documentation-only review of accepted CP2 baseline
`fe3bbe98704fd33fb9516b53e8786e516dce9e1e`. See [readiness](CP3_READINESS.md),
[proposed tests](CP3_SECURITY_TEST_PLAN.md) and [actual approval](APPROVALS.md).
Historical implementation/test results above are unchanged.

| Practice | Evidence obtained in this checkpoint and limit |
|---|---|
| J2/J5: scope and durable decisions | Readiness design, finite test families, proposed native instructions and OPEN ownership/implementation gates. Documents demonstrate planning, not deployed native controls |
| J4: focused delegation and central review | Three read-only reviews covered Windows API design, POSIX alias/order gaps and qualification/governance. Root reconciled shared-environment findings; no named independent security reviewer or protected evaluator is supplied |
| J3: explicit counterevidence and proof limits | Inspected baseline shows lexical overlap checks, reopened roots, undeclared-directory descent and attempt creation before complete inventory checks. Design distinguishes these gaps from retained no-follow/read-only controls and proposes tests rather than claiming fixes |
| J3: review corrections | Clarified directory-traversal versus file-execution rights, insufficient non-directory type evidence, all-file read readiness and earlier-denial compatibility. Corrected an empty-scope test proposal and qualified which identities change with source bytes. Primary API documentation is not native qualification |
| J3: preserved evidence | Documentation/static preservation checks and any separately identified hosted regression result are recorded in readiness. No new local native security test, alias probe, source intake or Windows execution was performed |
| J1/J6: efficiency, provider choice and costs | NOT_VERIFIED; no usage, cache, billing, productivity or benchmark measurement. Reviewer count and document completeness imply no effectiveness gain |

All proposed native tests remain NOT_RUN, and native Windows qualification remains
BLOCKED. Development-agent review does not resolve CP3-R02 or establish semantic
acceptance. This ledger records obtained evidence only; it does not approve CP3
implementation or any later phase.

## CP3A bounded implementation evidence

Approved baseline `07ddcda5a78a9a2f9f093a94e722532f44e3044b`; see
[design](CP3A_DESIGN.md), [actual validation](CP3A_VALIDATION.md) and
[scope approval](APPROVALS.md). The historical CP3 planning record above is unchanged.

| Practice | Evidence and limit |
|---|---|
| J2/J5: bounded plan and compatibility gates | Separate read-only API, exact local policy and dedicated anchor; legacy publisher/failure timing untouched. CP3B/Windows/CP4/later phases remain unapproved |
| J3: executable security feedback | Native synthetic alias/permission/race tests, all-read-handles barrier and source/store mutation tripwires; mode checks and in-process observation do not prove ACL isolation or native trace completeness |
| J3: evidence/identity preservation | Original 456 tests retained; independent baseline/candidate sealed-byte/full-report comparisons and frozen vectors. Exact commands, failures, counts and hashes in validation |
| J4: focused delegation and review | Separate filesystem implementation, adversarial-test author, read-only security review and baseline comparison; root integrated policy/session and corrected test capability classification and writer-policy denial. Shared environment, not independent semantic certification |
| J3: honest unresolved guarantees | Unsupported mounts/ABIs fail BLOCKED; explicit quiescent/trusted-writer assumptions. Native Windows, comprehensive ACL/observer and hostile-writer guarantees remain unqualified |
| J1/J6: efficiency and cost | NOT_VERIFIED; no provider, token/cache/billing or productivity measurements. Test timings are not SAS benchmarks; quadratic rechecks are disclosed |

This evidence supports the bounded CP3A engineering claims only. It does not
resolve the named independent reviewer/host decisions or grant downstream approval.

## CP3B bounded implementation evidence

Approved baseline `f841ca25d511230d77ab1c3eded3f59602a79f5d`; see
[design](CP3B_DESIGN.md), [actual validation](CP3B_VALIDATION.md) and
[approval](APPROVALS.md). Earlier phase records are unchanged.

| Practice | Evidence obtained and limit |
|---|---|
| J2/J5: bounded scope and durable decisions | Private read-only protocol/native layer, separate status, explicit missing bootstrap/native qualification, no public override or publication change |
| J3: executable feedback | Independent memory-only handle/object fixtures, rights/parser injections, zero-read barriers, source/store snapshots and cleanup faults. Unit-only Windows evidence, not native security qualification |
| J4: delegated authorship and separate review | Separate native-layer author, adversarial fixture author and read-only security audit. Root integrated and corrected ancestor enumeration, unsafe absence conclusions, cleanup and alias limits; shared development environment is not independent human security acceptance |
| J3: preserved evidence | Original tests and frozen schema/identity/history comparisons; exact commands, failures/corrections and results are recorded in validation |
| J3: explicit uncertainty | Missing Windows host/owner/observer/bootstrap stay OPEN/BLOCKED; no successful skips substitute for native hostile-fixture obligations |
| J1/J6: efficiency, provider choice and cost | NOT_VERIFIED; no token/cache/billing, productivity, model comparison or SAS benchmark measurements |

This demonstrates bounded development controls only. It does not grant semantic
acceptance, native support or permission to start CP4/CP5/P2B/P3.

## CP3C planning and security-review evidence

Reviewed accepted baseline `a29af0ec024945b15d31435e7041d45e92278c68`; see
[bootstrap design](CP3C_BOOTSTRAP_DESIGN.md),
[qualification plan and actual checks](CP3C_QUALIFICATION_PLAN.md) and
[scope approval](APPROVALS.md). Historical phase evidence above is unchanged.

| Practice | Evidence obtained and limit |
|---|---|
| J2/J5: bounded scope and durable decisions | Documentation-only conditional bootstrap/absence design, OPEN ownership/provisioning decisions and explicit stop gates; no deployed native assurance |
| J4: focused delegation and separate review | Three read-only reviews covered volume authority/locality, native absence/alias semantics and qualification/ACL/completion evidence. Shared development environment; no independent human security sign-off |
| J3: counterevidence and proof limits | Distinguished root locator from approved physical binding; identified typed-status gap, temporal absence limits, enumeration documentation ambiguity, ACL trust assumptions and unresolved pending-I/O buffer lifetime |
| J3: executable preservation feedback | Existing documentation/guard/preservation checks and attributable CI results are recorded in the qualification plan. New native fixture execution remains NOT_RUN/BLOCKED |
| J3: proposed independent tests | Positive observer controls, ordinary/provisioned lanes and finite native case families specified; a planned matrix is not executed evidence or a passing denominator |
| J1/J6: efficiency, provider choice and cost | NOT_VERIFIED; no token/cache/billing, productivity, model-comparison or workload performance evidence |

These observations justify review prerequisites, not native platform support,
semantic acceptance, output publication or any later-phase approval.

## CP3D bounded private implementation evidence

Approved baseline `5453a2598bd6da4ee695602f539f3961e70556b7`; see
[design](CP3D_DESIGN.md), [actual validation](CP3D_VALIDATION.md) and
[scope approval](APPROVALS.md). Earlier records remain historical.

| Practice | Evidence obtained and limit |
|---|---|
| J2/J5: narrow scope and durable decisions | Private metadata protocol/typed expectations and bounded mapping primitive; all native filesystem/context methods blocked without an enabling flag; no public integration |
| J4: independent authorship and review | Separate native primitive author, simulated-test author and read-only preservation/security reviewer. Shared development environment, not independent human acceptance |
| J3: executable feedback | 71 new pure/mocked/simulated cases plus 596 unchanged regressions; alias/collision, identity/race, limits, before-I/O denial and exact-once ownership oracles |
| J3: counterevidence and corrections | Pending-status ownership transfer, malformed metadata comparison and OSError diagnostics tightened; native completion/authority gaps explicitly left blocked |
| J3: historical evidence preservation | Independent baseline/candidate P1/P2A full-byte and complete-report comparisons; frozen schemas/vectors/lock/pin unchanged. Commands and results in validation |
| J1/J6: efficiency, providers and cost | NOT_VERIFIED; no token/cache/billing, productivity, provider comparison or workload benchmark measurements |

No native Windows execution, certification, authentic inspection grant, human
reviewer approval or semantic acceptance follows from these development results.

## Post-CP3D roadmap review evidence

Reviewed accepted baseline `d6b25d35a97290bb5c72673b9267c9d6dd3564d7`;
see [roadmap and actual checks](POST_CP3D_ROADMAP.md) and
[current decision boundary](OPEN_DECISIONS.md). This is documentation only.

| Practice | Evidence obtained and limit |
|---|---|
| J2/J5: bounded work and durable decisions | Recommended one private synthetic dependency/blocker increment with explicit approval, exclusions, finite analysis bounds and stopping conditions; no P3 implementation |
| J4: focused independent development review | Separate read-only reviews of canonical graph coverage, normative workflow/P2B gates and CP1–CP3D portability evidence; not human security/semantic certification |
| J3: evidence and counterevidence | Recorded missing hazard/effect completeness, unversioned dataset overwrite, source-reading validator boundary, state cycles and non-authoritative synthetic timing; no absence-of-edge independence claim |
| J3: proposed tests versus observed checks | A01–A26 are planned public graph-math obligations, NOT_RUN. Documentation/byte-preservation checks are recorded separately; historical 667 regressions remain attributed to CP3D |
| J5: separate work and approval dependencies | Core experiment, P2B mandatory semantic gate and native security/release qualification have distinct prerequisites. Review corrected diagram order, graph-only identity/lineage proof limits, bound-specific test assertions and separation of pure diagnostic I/O from existing regression fixtures |
| J1/J6: efficiency and cost | NOT_VERIFIED; prioritization is a recommendation, not measured productivity, speedup, model/provider performance or cost evidence |

No host, reviewer, provider, native permission, independent acceptance or next-phase
approval was supplied or inferred by this reassessment.

## P3-A1 engineering evidence

The user accepted the [roadmap](POST_CP3D_ROADMAP.md) at
`dba5b3aa5a60ef384bfc57a90b46ca72ea4f27dc` and approved only the private
diagnostic experiment before P2B. See the [approval](APPROVALS.md),
[design](P3_A1_DESIGN.md) and [validation](P3_A1_VALIDATION.md).

| Practice | Evidence and limit |
|---|---|
| J2/J5 bounded scope | The roadmap fixes the input, finite bounds, A01–A26 obligations and review gate. RMAP-01 authorizes engineering only. Independent source/graph acceptance and draft PRD/module specifications still precede operational P3 |
| J4 separate expectation author | A separate author froze [public vectors](../tests/dependency_vectors.py) with literal graph answers and standard-library identity preimages before candidate implementation, at `0e1b80fe60c412ddbf19a0c93c4291f4fe3bfd95`. The authors share the development environment. Protected P2B evaluation and independent human semantic review remain outstanding |
| J3 observable baseline | The accepted roadmap checkout passed its 667 regressions on macOS ARM64. Its synthetic P1 and P2A replays each matched all 15 historical artifact files byte for byte and the complete parsed reports. The validation record distinguishes this baseline from candidate runs |
| J3/J4 adversarial feedback | A reviewer reproduced a caller-controlled `VERIFIED` code and scheduler instruction echoed in an issue finding. P3-A1 now uses fixed wording from the issue kind and references the untrusted parent. Five attribution subtests exercise this boundary. All 693 methods passed in development, fresh checkout and installed wheel on macOS; 133 explicit subtest variants across the 26 new methods. These runs do not establish SAS semantic correctness |
| J1/J6 efficiency and cost | NOT_VERIFIED. No provider, token/cache, billing, productivity or workload performance measurements |

These checks support public engineering evidence only. Semantic verification is
UNVERIFIABLE, semantic acceptance BLOCKED, authority DRAFT and benchmarks NOT_RUN.

## P2B-B1 isolation readiness planning

Reviewed at accepted P3-A1 baseline `5e62727b9b8e463cf6c7dd1bc68172801a7868f6`.
The [isolation design](P2B_B1_ISOLATION_DESIGN.md) and
[test plan](P2B_B1_TEST_PLAN.md) are specifications for future review.

| Practice | Evidence at this checkpoint | Limit |
|---|---|---|
| J2/J5: scope and stop gates | The plan ties one native host/policy tuple to named human admission decisions, an offline stub and a finite sentinel schedule | Host, independent reviewer, retention and budget are OPEN. No deployment, run or isolation verdict |
| J3: evidence and counterexamples | Every proposed denial needs corroboration outside the role; controls distinguish real denial from an absent object or broken runner. The handoff distinguishes a torn copy, a committed but unacknowledged receipt and receipt substitution | The controls and counterexamples are NOT_RUN; no protected answers, semantic evaluation or cost estimate |
| J4: separate review | A read-only design review identified the distinction between namespace invisibility and backing permissions, the risk from surviving writable descriptors, and when a fresh-context exclusion check can be observed. These constraints are reflected in the documents | Same-workspace development review is not a real-host witness or independent human security sign-off |

## Workstation execution planning

Planning baseline `13a82fdb48248215548a57463aafc075edeb7e41`, 2026-11-06.

| Practice | Attributable evidence and limit |
|---|---|
| J2/J5 bounded planning | The [execution plan](WORKSTATION_EXECUTION_PLAN.md) and [compatibility matrix](WORKSTATION_COMPATIBILITY_MATRIX.md) record the two shell targets, offline Python prerequisite and separate approval gate for workstation scripts. This demonstrates planning only. |
| J3 evidence attribution | The [P3-A1 validation record](P3_A1_VALIDATION.md) distinguishes historical macOS arm64 and hosted Linux regressions from simulated Windows denial checks. The [B1 checklist](P2B_B1_APPROVAL_CHECKLIST.md) records zero sentinel launches. No workstation qualification test ran in this checkpoint. |
| J3 direct observation | The existing macOS wheel answered help, version and status from outside the checkout with an empty executable search path; 29 installed Python/JSON files matched the baseline. No proposed launcher or native Windows test ran. |

## WS-1 engineering checkpoint

The user accepted the workstation plan at
`a79b15fefd878f1ecc9c0e4969e1c6a211120a41` and approved the W01–W06 scope.
The detached baseline below precedes candidate validation. See the
[WS-1 design](WS1_DESIGN.md) and [validation record](WS1_VALIDATION.md).

| Practice | Attributable evidence and limit |
|---|---|
| J2/J5 scope and approval | Approval covers three read-only launcher arguments. The shipped launcher leaves the inventory path and pin empty. Positive development fixtures cannot authorize workstation installation or native Windows access. |
| J3 baseline preservation | The detached planning commit passed all 693 original tests on macOS arm64 with CPython 3.12.5. Its P1/P2A demos matched 30 historical artifact files and both complete reports. The audit also checked eight frozen hashes and three P3-A1 hashes. |
| J3 provenance | All 29 package Python/JSON files matched across the detached baseline, historical wheel and existing local site-packages. This comparison establishes development provenance. Workstation release approval is OPEN and native Windows qualification is BLOCKED / NOT_RUN. |

WS-1 validation now records 29 focused tests, three macOS runs of all 722 tests,
byte-identical P1/P2A replays, and successful direct/launcher stream comparisons
using a synthetic approval of an installed project wheel. Review tightened the
file inventory to refuse unexpected entries before opening their content. This is
public engineering evidence; no native Windows or release trust claim follows.

## WS-2A offline installation planning

The user accepted the [WS-1 validation record](WS1_VALIDATION.md) at
`767b2c3154de7fb451c4278e22f25633d9a025d0` within its tested scope. WS-2A
adds planning evidence only.

| Practice | Attributable evidence and limit |
|---|---|
| J2/J5 bounded planning | The [kit plan](WS2A_OFFLINE_KIT_PLAN.md) and [installation test plan](WS2A_INSTALLATION_TEST_PLAN.md) distinguish human artifact and release decisions from future installer work and native trials. The [open decisions](OPEN_DECISIONS.md#ws-2a-decisions-requiring-separate-approval) identify the missing owners, trust anchor and platform-specific closures. |
| J3 evidence attribution | The accepted WS-1 record attributes three 722-test suites to macOS ARM64 and two 722-test suites to hosted Linux x64 at implementation commit `27ecad95a43d68c991d33c0b3aff44b94cf72696`. Its successful launcher dispatches used synthetic inventories. Native Windows W01–W06 are BLOCKED / NOT_RUN. WS-2A installation tests are proposed and NOT_RUN. |

Read-only design review identified two reproducibility controls: pip's target process
needs its own verified startup boundary, and generated Windows console wrappers need
a pinned ZIP timestamp. The kit plan and proposed I10/I12 observations now cover them;
neither was tested on Windows. WS-2A preservation checks left all 106 baseline files
outside the three ledger edits unchanged.
