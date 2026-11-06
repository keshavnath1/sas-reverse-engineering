# Open decisions and compatibility risks

Status: CP3C planning/security review approved at `a29af0ec024945b15d31435e7041d45e92278c68`.
CP3B is accepted only within its limited simulated-test scope. Native Windows
qualification and public source access remain BLOCKED. Updated 2026-11-05.

**Current checkpoint authorization:** documentation only:
[bootstrap design](CP3C_BOOTSTRAP_DESIGN.md) and
[qualification plan](CP3C_QUALIFICATION_PLAN.md), with necessary decision/practice
updates and applicable existing checks. No implementation, dependency, Windows
source access, publication or output-store creation. All 596 tests and frozen
boundaries are preserved. Stop after CP3C planning for explicit approval.

**Accepted CP3B:** private retained-handle implementation and simulated/unit tests
at the baseline above; [design](CP3B_DESIGN.md) and [validation](CP3B_VALIDATION.md).
No approved volume bootstrap, native qualification or public override exists.

**Accepted CP3A:** the user accepted the separate POSIX preflight within its tested
scope at `f841ca25d511230d77ab1c3eded3f59602a79f5d`. Its behavior and original tests are preserved.

**Historical CP3 readiness authorization:** the user accepted CP2 at
`fe3bbe98704fd33fb9516b53e8786e516dce9e1e` and authorized only
[CP3 readiness](CP3_READINESS.md), [security test planning](CP3_SECURITY_TEST_PLAN.md),
proposed native qualification instructions and necessary ledger updates. No native
source reading, publication, locks, schema/history changes, dependencies, private
intake or P2B/P3 execution is approved. CP3-R01–R10 below identify missing decisions;
none is approved merely by being recommended. Stop for explicit implementation approval.

**Historical P2B checkpoint authorization:** the user accepted P2A at
`56154dd75a0149043c36081da9704b0a939230e1` and approved only a read-only P2B
assessment and documentation checkpoint. Deliverables are
[P2B_READINESS.md](P2B_READINESS.md),
[BEST_PRACTICES_ADOPTION.md](BEST_PRACTICES_ADOPTION.md) and necessary decision-ledger
updates. No code/tests, isolated runner, provider adapter, grader, gold or campaign
is authorized. This supersedes the older stop wording only for documentation;
P2B execution and independent semantic acceptance remain BLOCKED.

**Historical P2A authorization:** the user reviewed planning commit
`e13705c67c5984b2cb6bc8d4c797a188fd6421e2` and approved D08-A/B for deterministic
synthetic reconstruction, canonical v2, reviewed public fixtures, CLI/CI and
validation only. [P2A_DESIGN.md](P2A_DESIGN.md) records implementation choices;
[P2A_VALIDATION.md](P2A_VALIDATION.md) records actual checks. P2B's model/provider,
protected gold, independent acceptance and isolation remain unapproved. Public
tests cannot satisfy D09. The historical planning text below is superseded only
for the explicitly approved P2A scope.

**P1 update, 2026-11-05:** the user approved D01–D03 for P0 and D04–D07 for
synthetic P1. The tables below retain the original recommendations for traceability;
their pending-approval language is historical. [APPROVALS.md](APPROVALS.md) records
the authorization. [P1_DESIGN.md](P1_DESIGN.md) records the implemented rationale
and conservative ID policy. D08–D12 remain open. Production data/provenance and
storage authorization remain unresolved; D07 permits synthetic P1 only. The later
local example authorized a read-only readiness check, not a synthetic label,
private-data ingestion feature, semantic extraction or publication of its files.

**P2 planning update:** the user reviewed and accepted P1 at
`5c8aea7588290925250b76c9cbd5091a3ea89f13`, including hosted CI verification,
and authorized only this planning checkpoint. [P2_READINESS.md](P2_READINESS.md)
and [P2_EVALUATION_DESIGN.md](P2_EVALUATION_DESIGN.md) specify D08/D09
recommendations. Neither their creation nor P1 acceptance approves P2 implementation.

Companion: [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md). Recommendations
distinguish observed implementation, proposed design and missing decisions.
No decision becomes human-approved merely by appearing in these documents.

## Current approval ledger

| Item | Status | Boundary |
|---|---|---|
| D01–D03 | APPROVED by the user for P0 | Repository/toolchain/baselines; subsequent remote publication was separately authorized |
| D04–D07 | APPROVED by the user for synthetic P1 | One canonical graph, byte identity, explicit scope/provenance and local safe publication |
| P1 result | ACCEPTED by the user's review | Structural scope at the exact commit above; not semantic correctness |
| P2 readiness documentation | APPROVED scope for this checkpoint | Only the two P2 design documents and this decision ledger |
| D08-A and D08-B | APPROVED for P2A | Exact synthetic subset and canonical v2 evolution; deterministic reconstruction and reviewed public tests only |
| P2A result | ACCEPTED by the user's review | Commit `56154dd75a0149043c36081da9704b0a939230e1`; public synthetic scope, no independent semantic acceptance |
| P2B readiness documentation | APPROVED for this checkpoint | Two readiness/practice documents and necessary decision-ledger updates only; preserve code, tests, hashes and downstream pin |
| D08-C and D09-A/B/C below | RECOMMENDED, NOT APPROVED for P2B | No provider selection, protected-gold grader, isolation deployment or independent acceptance |
| D10–D12 | OPEN | Business/oracle/runtime/downstream choices remain later human decisions |
| CP1 result | ACCEPTED by the user | `0061b7bf038f7b36add830912258232f174af197`; native Windows qualification still BLOCKED |
| CP2 result | ACCEPTED by the user | `fe3bbe98704fd33fb9516b53e8786e516dce9e1e`; declarations/projection only, no physical authorization |
| CP3 readiness documentation | APPROVED for current checkpoint | Design, proposed tests/instructions and factual ledger updates only |
| CP3A implementation | APPROVED bounded subset | Separate POSIX preflight, physical alias checks and synthetic verification only; no legacy failure-timing change |
| CP3B implementation | APPROVED bounded subset | Private read-only native layer/protocol; public Windows access BLOCKED until physical bootstrap and qualification |
| CP3B result | ACCEPTED within limited simulated-test scope | `a29af0ec024945b15d31435e7041d45e92278c68`; not native security qualification |
| CP3C planning/security review | APPROVED documentation only | Two planning documents, necessary ledgers and applicable existing checks; no implementation or provisioning |
| Broader Windows native qualification | OPEN, NOT APPROVED | Requires separately approved real environment, owners and security evidence |
| CP4/CP5 implementation | OPEN, NOT APPROVED | No publication/locks or dependency/qualification expansion implied by CP3 planning |

## CP3 readiness decisions

Rows remain **OPEN** except CP3-R10's explicitly approved CP3A/CP3B implementation subsets below.
Recommendations define review questions, not authenticated
approval or installed controls. [APPROVALS.md](APPROVALS.md) records the actual user
scope. The Windows owner and independent reviewer have not been supplied; do not
infer either from a GitHub account, workstation username or development subagent.

| ID | Missing decision / accountable input | Proposed resolution and consequence if unresolved |
|---|---|---|
| CP3-R01 | Named Windows host owner; exact supported host tuple | Propose Windows 11 x64, fixed local NTFS, Python 3.12 and PowerShell 7; record exact builds/configuration. Native qualification BLOCKED until owner/environment supplied |
| CP3-R02 | Named independent security reviewer | Human-owned review of API protocol, threat model and native evidence; separate development-agent review does not satisfy this role. Security acceptance remains BLOCKED |
| CP3-R03 | Native API/ABI and finite resource policy | Review narrow stdlib FFI, single-component relative opens, reparse rejection and object-type checks; resolve NtCreateFile/OBJ_DONT_REPARSE contract uncertainty and buffer/handle/call/deadline bounds. No implementation fallback if guarantees unavailable |
| CP3-R04 | Physical bootstrap and run inspection authority | Host-owned scoped policy and independently approved volume expectation; exact provisioning/authentication OPEN. CP2 has no store field: approve a separate explicit local store-ancestor inspection request, with no create grant. No persistent receipt or new evidence schema assumed |
| CP3-R05 | Filesystem, writer and ACL trust assumptions | Initial dedicated quiescent synthetic scope on one approved local NTFS volume; trusted host administrators/writers, cloud/network/device aliases excluded. Review enforceable preconditions and residual race limits; no arbitrary hostile-writer snapshot claim |
| CP3-R06 | macOS/Linux physical equivalence and supported filesystems | Qualify retained descriptors, ancestry, case/Unicode aliases and mount identities on exact APFS/Linux configurations; preserve normal macOS bootstrap transitions. Intel and untested mount arrangements remain unqualified |
| CP3-R07 | Fixture custodian, privileged setup, independent observer and retention | Approve disposable fixtures, observation coverage/positive controls and local trace retention; ordinary application runs remain unelevated. Required cases without trustworthy observation remain BLOCKED |
| CP3-R08 | Approved Windows interpreter and offline dependency artifacts | Existing lock lacks Windows artifacts. Obtain separate installation/hash-extension approval; do not add dependencies or install anything during readiness |
| CP3-R09 | Earlier-denial compatibility and native diagnostics | Review stricter directory/alias policy and pre-store preflight integration: current POSIX workflows begin attempts before complete scope checks. Preserve historical attempts, successful compatible bytes, old FAIL/BLOCKED conventions; freeze exact new codes before implementation |
| CP3-R10 | CP3A/CP3B bounded subsets APPROVED | CP3B private implementation and synthetic unit coverage are approved; native environment/qualification, CP4/CP5/P2B/P3 and downstream integration remain separate |

Current next action: review the CP3C design/qualification documents and resolve
required inputs below. No proposed mechanism is an approved or qualified control.
CP3A's existing POSIX behavior and legacy publication timing stay unchanged.
Missing native prerequisites remain OPEN/BLOCKED. Stop after CP3C planning.

## CP3C review decisions

All rows are **OPEN**. Recommendations below describe conditions for later approval,
not human decisions or permission to execute. CP3C does not implement a new grant,
schema, identity, native harness or bootstrap API.

| ID | Required accountable decision | Recommendation / consequence if unresolved |
|---|---|---|
| CP3C-D01 | Host owner and authentic initial metadata-inspection authority | Independently provisioned host-local grant for one root-only candidate, exact token/anchor/source/store scope and quiescent policy; issuer, authenticity, ACL protection, expiry/revocation OPEN. CP2 or OS access alone cannot approve lookup |
| CP3C-D02 | Physical-volume binding and native lookup/API review | Approve host/storage inventory, root/volume identity method, bounded DOS observations, retained-handle locality query and exact native namespace/reparse protocol. Serial/GUID/path alone insufficient; unprovable backing or clone ambiguity BLOCKED |
| CP3C-D03 | Alias-safe absent-store proof | Review typed single-component metadata lookup/status, case-mode query, exact existing-parent/long-name binding and temporal validity. All missing-store acceptance stays BLOCKED pending implementation/native proof; no creation authority |
| CP3C-D04 | Pending I/O, completion lifetime and cancellation | Prove synchronous completion of qualified calls or separately design completion/cancellation and retained buffer/status/handle ownership. BLOCKED/close alone is not proof pending I/O ended; deadline/observer obligations OPEN |
| CP3C-D05 | Exact native host/runtime and offline artifacts | Supply Windows11 client x64 build, local fixed NTFS configuration/backing, CPython3.12 and PowerShell versions/hashes, all Windows wheel hashes and explicit provisioning approval. No lock extension/install authorized here |
| CP3C-D06 | Named independent reviewer, custodian and observer | Approve ordinary-user lane, separately provisioned hostile fixtures, observer positive controls and trace retention. No inferred owner, privileged setup or successful skipped obligation |
| CP3C-D07 | Finite native qualification manifest and limits | Freeze individual C01–C20/T01–T26 cases, exact diagnostics, counts, independent expected facts, native deadlines and proof exclusions before execution. Missing cases BLOCKED, no simulated/native denominator mixing |
| CP3C-D08 | Separate implementation, execution and activation approvals | Review plan first; then explicitly approve narrowly scoped implementation/provisioning/metadata tests. Synthetic content-read qualification and public-reader activation require their own explicit scopes; CP4/CP5/P2B/P3 remain separate |

## Decision register

D01–D07 retain their historical recommendations below; their approval status is
the ledger above. D08/D09 now have concrete proposals rather than implementation
authorization.

| ID / needed by | Decision | Recommendation | Consequence if unresolved |
|---|---|---|---|
| D01 / P0 | New repository name, local location, owner and eventual visibility | Local `sas-reverse-engineering/` under the current workspace; separate Git history; no remote publication in P0 | Cannot finalize bootstrap destination; current two documents remain in workspace `docs/` |
| D02 / P0 | Is the supplied v2 ZIP the intended `reference/` baseline, or is another pack missing? | Accept the exact archive hash recorded in the plan; preserve provenance and explicitly map the misencoded audit filename when copying it | A different pack may change requirements; do not silently substitute |
| D03 / P0 | Approve P0-only scope and initial toolchain | Python 3.12, package plus CLI, reproducible dependency pinning, local checks and GitHub Actions definition; no runtime libraries or agent framework yet | No implementation is authorized by this planning step |
| D04 / P1 | Canonical graph ownership across modules | One composed scoped-run source record with module-tagged operations and immutable module views; one reconciler/publisher | Per-module graphs can miss or disagree about cross-module edges |
| D05 / P1 | Source identity, stable IDs and hash canonicalization | Hash original bytes; version payload/envelope rules; IDs stable for identical source spans and operation kinds; explicit revision mapping after edits; declared encoding and newline policy | Citation and identity tests cannot be precise; decide whether logical identity survives line shifts |
| D06 / P1 | Scope authorization and log provenance | Explicit allowed roots, required dependencies and declared source/log run bindings; no implicit expansion or guessed matches; unresolved dynamic includes remain blocked | Inventory cannot establish completeness or log linkage; actual run provenance needs external evidence |
| D07 / before private intake | Evidence retention, permitted data, and seal trust model | Synthetic-only M1; private external read-only intake later; metadata-only reports; access-controlled immutable storage/trusted digest history for production | Local hashes alone do not provide authenticated or adversary-resistant history; PII handling cannot be inferred |
| D08 / P2A–P2B | Exact bounded semantic subset, canonical representation and reconstruction environment | D08-A/B approved for deterministic P2A; D08-C provider/runtime policy remains open for P2B | No model/provider or independent acceptance may be inferred from deterministic implementation |
| D09 / P2–P5 | Independent gold, two-lane semantic evaluation and enforced isolation | Approve D09-A/B/C below and P2_EVALUATION_DESIGN.md; separate gold custodian/evaluator identity and fixed metrics/gates | No hidden-gold or independent semantic reliability claim until access-denial tests and frozen-corpus checks actually pass |
| D10 / P4–P6 | Business intent, corrected legacy behavior, keys, oracle, tolerances and population | Leave unresolved in upstream drafts; domain owner chooses in downstream interview/specify/test gates | No parity or release claim, no convenient sample/population default |
| D11 / P4–P6 | Platform constraints and benchmark protocol | Assess Spark/Ray/Dask/native fairly; agree resources, data sizes, repetitions, cache conditions, objectives and training equivalence before measurement | No winner, cost ranking or speedup assertion; benchmark status stays NOT_RUN |
| D12 / P7 | Receiving-side owner and authorization | Separate Agent-mastery change proposal, isolated branch, independent reconciliation and existing human gates | Candidate handoff may be packaged in P6 but cannot be automatically imported or approved |

D01–D07 and D08-A/B have been decided for their approved phases. D08-C/D09 are
the P2B approval checkpoint. D10–D12 remain future decisions and must not be guessed.

## D08/D09 proposed resolutions requiring human input

| Item | Recommendation | Still needed before implementation |
|---|---|---|
| D08-A: semantics and granularity | APPROVED and accepted P2A: static synthetic SAS 9.4-profile subset; top-level operations with ordered internal facts and explicit unsupported blockers | No SAS execution, private pilot or independent acceptance approved |
| D08-B: canonical contract | APPROVED and accepted P2A: canonical v2 numerical/order/state/step facts; reused P1 inventory/citations/IDs; immutable v1 and explicit lineage | Independent verifier judgments remain P2B and must not rewrite candidate seals |
| D08-C: environment and budgets | New readiness recommendation: frozen deterministic P2A candidate plus separately implemented model reviewer for the first pilot; earlier model-candidate option remains an alternative. Per model role/case: three calls/32k aggregate input/8k aggregate output/five minutes maximum | Approve topology; name actual provider/model revision, endpoint/account/data policy, supported controls, usage accounting and dollar ceiling. No provider or topology selected; no live call authorized |
| D09-A: gold ownership | SAS domain author plus second reviewer; separate custodian freezes source, source-anchored facts, exact expected gates, evaluator and denominator versions before runs | Named author/reviewer/custodian and private gold store; no maker-generated expected answers or copying public examples into “hidden” gold |
| D09-B: isolation | First authorize only B1 sentinel probes and trusted handoff on dedicated Linux host/VM, separate identities/process/mount/network boundaries, positive controls and explicit denial tests; gold comes later | Named host/admin/security reviewer, approved image/runtime/policy, location, retention and spending ceiling; no host supplied or tested. Shared-user folders/chats are not an acceptable fallback |
| D09-C: corpus, metrics and feedback | 12 families × P/N/U = 36 hidden cases; reconstruction and checker-challenge lanes; five fixed attempts per case/lane; all required positive facts correct, exact negative gates, 100% obligation coverage and zero critical false approvals | Approval of strict finite-pilot thresholds, repetition/transport-failure policy and restricted diagnostic release; actual gold-derived assertion denominators frozen before running |

No particular person, model, evaluator host, hidden corpus or semantic test result
has been supplied/verified by this checkpoint. If those dependencies are absent,
future implementation/evaluation must report BLOCKED rather than invent them.

### P2B readiness refinements, proposed only

[P2B_READINESS.md](P2B_READINESS.md) assesses D08-C and D09-A/B/C without approving
them. The minimum next authorization is B1's sentinel-only proof, not the campaign.
Provider and gold choices need not block B1 because B1 has neither; they block
later live evaluation. Named infrastructure/ownership/cost decisions still block B1.

- **D08-C topology and cost:** retain the 360 case-attempt schedule. A deterministic
  candidate requires 360 model reviewer role-cases (up to 1,080 calls); a model
  candidate as well requires 540 role-cases (up to 1,620 calls). The documented
  token ceilings and hypothetical price sensitivity are estimates, not usage,
  current vendor quotes or provider-supported settings.
- **D08-C synthetic policy:** local synthetic approval does not authorize model
  transmission. Obtain endpoint retention/training/region and account approval;
  gold, expected labels, restricted diagnostics and private intake never enter
  candidate/reviewer model context. No cache or billing capabilities assumed.
- **D09-A ownership:** domain author, independent second reviewer, custodian and
  adjudication/release responsibilities must be named. Public examples cannot
  become hidden gold. No expected-answer authoring occurs in this checkpoint.
- **D09-B proof:** exact eventual principals and host controls, harmless canaries,
  permitted-access positive controls, denied reads/writes/egress, protected hashes
  and receipt-bound submission copies. Local stub tests do not verify live
  provider behavior; administrators remain trusted. No probes were executed here.
- **D09-C eligibility and stops:** complete sealed semantic PARTIAL/BLOCKED evidence
  is eligible for U tests; incomplete structural publication is not. Lane V
  semantic attacks must pass structural checks without P2A semantic prefiltering.
  Preserve all scheduled entries after a stop; no automatic hidden transport
  retries or feedback repair. Seeded challenge defects are inputs, not scored
  failures. Freeze strict thresholds/denominators and protect diagnostics.
- **Practice evidence:** the companion ledger backfills only attributable
  historical records. Its final report and any cost/quality experiments require
  future authorization; no telemetry or effectiveness benefit is invented.

### Canonical-model compatibility decision

Observed: P1 v1 cannot serialize exact expressions, state reset, row ordering or
detailed LOG/LST semantics, and its semantic status is constant UNVERIFIABLE.
D08-B is the approved P2A evolution of that same factual graph,
not a second graph/IR. Facts remain in canonical nodes/operations/edges; verifier
reports contain judgments and references only. Adding semantic payload changes
operation IDs under D05, so v1-to-v2 lineage must be explicit. Golden test anchors
cannot depend solely on candidate operation IDs because a wrong interpretation
also changes the ID. P2A preserves v1 schema bytes and historical artifacts.

The pack's P2 “DAG” is a derived canonical-ID visualization preserving state
cycles/unknowns. It does not authorize P3 scheduling or independence analysis.
Its P5 evaluation roadmap does not defer the independent semantic and security
checks explicitly required for this P2 pilot.

## Specification conflicts and proposed resolutions

| ID | Observed conflict or gap | Proposed resolution / remaining uncertainty |
|---|---|---|
| C01 | The reference audit proposes early discovery within Agent-mastery; normative 01/02 requires a separate upstream planner | Follow 01/02. Research proposals do not amend downstream workflow. P7 requires separate authorization |
| C02 | Build phase P3 precedes requirements in P4, while document 02's runtime flow drafts requirements before parallelism analysis | Treat phase numbers as development sequencing; enforce document 02 at runtime |
| C03 | README calls for one scoped graph; document 02 also describes per-module/run records | Proposed composed-run graph in D04; module views reference it. Avoid silently choosing incompatible authority models |
| C04 | Proposed source schema v0.1 was smaller than the narrative; P1 v1 covers structural identities but not detailed semantic facts | Approved P2A implements narrow canonical v2 facts and explicit identity lineage; historical v1 remains unchanged |
| C05 | Claim and handoff schemas omit several required narrative fields; enum field names differ across files | One versioned serialization specification with required provenance, counterevidence, preconditions and explicit field-name mapping |
| C06 | Document 10 says generated drafts remain CANDIDATE, while document 02's authority enum uses DRAFT/EVIDENCE_CHECKED | Use document 02's authority enum; candidate is descriptive, not a new authority value |
| C07 | Final checklist asks for three ADRs; requirements call for evaluating four runtime families with justified exclusions | Evaluate all four families; generate full designs for every viable candidate. Do not invent three viable options when evidence excludes them; report the unmet showcase condition |
| C08 | Append-only/immutable evidence is specified without storage, authentication, atomicity, retry or canonicalization details | M1 demonstrates local atomic publication and overwrite prevention under a stated trust model; production immutability is D07 |
| C09 | Hash-valid citations do not establish true dependencies; source/log association and dynamic macros may remain uncertain | Separate integrity and semantic gates; unknown is not independent; source-aware checks cannot be replaced by JSON Schema |
| C10 | ZIP entry spelling of the audit differs from the manifest's Unicode name | Explicit encoding mapping reproduced the content hash. Preserve original archive; do not regenerate a manifest to hide a discrepancy |

## Risk register

| Risk | Evidence classification | Mitigation and proof obligation |
|---|---|---|
| Downstream compatibility mistaken for acceptance | OBSERVED: existing import handles reusable patterns; trace requires approved SPEC/ADRs | P6 reports compatibility only; P7 must demonstrate approval-chain non-bypass |
| Valid structure mistaken for valid semantics | OBSERVED: loose trace/map schema fields; INFERENCE: malicious or erroneous claims can fit those shapes | Test valid-citation/false-independence cases with independent source-aware review; zero critical false approvals on pilot cases |
| Duplicate source authority | OBSERVED: trace and map both describe dependency reconstruction | Handoff must preserve IDs; contradictions reopen source evidence instead of map silently changing it |
| Run contamination | OBSERVED: downstream helper chooses newest state by mtime | Explicit workspace/module/run/attempt selection; concurrency, crash and stale-source tests |
| Unknown macro/state behavior | ASSUMPTION: real workloads may use dynamic includes, external state or proprietary formats; no real workload inspected | Supported-subset declaration, scope omissions and unknown records; never execute SAS to resolve uncertainty automatically |
| Invalid optimization or numerical drift | PROPOSED risk from reordering/state/reductions/training | Shared invariants and tie-out obligations; downstream human approval for changed behavior; measured runtime tests later |
| Evaluator leakage | PROPOSED risk: candidate tools could read local gold | Enforced process/account access boundary and denied-access tests; no independence claim until demonstrated |
| Private source or values exposed in Git/reports | PROPOSED risk for future intake | External intake, local ignored artifacts, synthetic public fixtures, metadata-only reports and leakage tests |
| Unsupported research or performance claims | OBSERVED: pack labels REA cases unreplicated and example verdicts expected | No REA integration claim, no default runtime winner, no measured speedup without actual benchmark evidence |

## What remains unknown

The Step 1 review established no production business schema, authentic source/log
run provenance, reference-output correctness, runtime environment, retention rule,
approver identity or measured performance. The subsequent private example was
only checked locally for readiness; it is outside this synthetic planning scope.
P1 structural tests and the user's CI review do not answer those production
questions. The old audit's smoke tests were not rerun at this checkpoint.
Neither the pack's expected outcomes nor these designs prove semantic reconstruction,
gold isolation or safe parallelism.

## Historical P2B approval boundary and recommended next action

For any later P2B work, review the P2B readiness and practice ledger, then separately authorize B1 only
with its named host, administrator/security reviewer, image/policy, retention and
budget. B1 would implement and test deterministic sentinel probes and trusted
handoff, with no agents, provider calls, semantic grader or hidden gold. Review
that proof before authorizing B2 preparation; full 360-attempt B3 execution needs
another explicit approval after corpus/protocol/provider/custody freeze.

Stop after this documentation checkpoint. No P2B implementation/campaign, P3,
PRD/ADR generation, parallelization analysis, private-data feature, SAS execution
or downstream integration is authorized by it.
