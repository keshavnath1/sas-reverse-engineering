# Open decisions and compatibility risks

**Current checkpoint.** The user accepted the MVP-4 demonstration at
`4a19ea1242e8aba685bef3dd53c222f6fde8d6b8` and authorized consolidation
of the existing stages into [one offline developer command](../README.md#run-the-offline-review).
Review usability before selecting the next capability against the six product
objectives. Real intake, expanded syntax, Windows qualification and independent
evaluation remain separate decisions.

**Historical checkpoint, 2026-11-06.** The user accepted MVP-3 as public synthetic
development at `8e9c0484a21c1fa8211f7a5418bac62a4bc1bd48` and approved the
[MVP-4 decision review](../examples/mvp4/DECISION_REVIEW.md). Runtime selection
remains BLOCKED. The include scope, independent reference outputs, tie and numeric
policies, and the workload and resource budgets still need human input.

**Historical checkpoint, 2026-11-06.** The user accepted MVP-2 as an engineering
demonstration at `a82ff2b1f0ae26e545f1e1640eb4ed697f33e56b` and approved the
[MVP-3 public behavioral oracle](MVP3_VALIDATION.md) for its represented
SORT, DATA and SQL subset. Actual SAS runtime settings, wider numeric behavior,
the unresolved include and independent semantic acceptance remain open.

**Historical checkpoint, 2026-11-06.** The user accepted MVP-1 as a public
synthetic draft at `022c672d244a522e25a5aded7f29513f51875b69` and authorized
MVP-2 only. The [second preview](../examples/mvp2/ARCHITECTURE.md) leaves the
include's effects unresolved. Production scale, allowable tie order, numeric
tolerance, reference population and runtime choice are OPEN. Review the package
before any further development or evaluation.

**Historical checkpoint, 2026-11-06.** WS-2A was accepted as planning at
`6e403722d64d15a41b4205cb074bb8d928fad3a2`. Workstation packaging is deferred.
MVP-1 is approved only as a private synthetic [draft preview](../examples/mvp1/PRD.md).
Business purpose, reference population, duplicate/tie policy, numeric tolerance,
resource budget and runtime selection are OPEN. Stop for product review.

**Historical checkpoint, 2026-11-06.** The user accepted WS-1 at
`767b2c3154de7fb451c4278e22f25633d9a025d0` within its tested scope and
approved WS-2A documentation only. The [offline kit plan](WS2A_OFFLINE_KIT_PLAN.md)
and [installation test plan](WS2A_INSTALLATION_TEST_PLAN.md) define future
decisions and proposed observations. Every proposed WS-2A installation case is
NOT_RUN. The repository launcher's approval slots are empty and valid requests stop
at bootstrap with exit 2. See the [WS-1 validation record](WS1_VALIDATION.md).

**Previous checkpoint, 2026-11-06.** The user accepted the workstation plan at
`a79b15fefd878f1ecc9c0e4969e1c6a211120a41` and approved only the three-command
WS-1 Bash launcher, focused W01–W06 tests, documentation and necessary ledgers.
Workstation release approval is OPEN. An accountable owner, independently
authenticated installation inventory and launcher delivery pin are outstanding.
The shipped approval fields are empty. Each valid request returns bootstrap
BLOCKED/2 until an authenticated kit binds the installation. A caller setting
`SAS_RE_PYTHON` cannot grant that authority. The historical wheel provides local
development evidence. See the [WS-1 design](WS1_DESIGN.md) and
[validation record](WS1_VALIDATION.md).

Native Windows qualification is BLOCKED / NOT_RUN. Setup, configuration,
evidence execution and report export through the launcher await separate human
decisions. RMAP-02 and D09-B are OPEN, and B1 execution is BLOCKED. Artifact
authority is DRAFT, semantic verification UNVERIFIABLE, independent acceptance
BLOCKED and benchmarks NOT_RUN.

**Previous checkpoint, 2026-11-06.** The user authorized workstation planning at
`13a82fdb48248215548a57463aafc075edeb7e41`. Ordinary use must work from macOS
Terminal/Bash or Windows Git Bash with Python 3.12 from an existing installation
or an approved offline bundle. It must be possible without Git commands, AI
services, a dedicated Linux host, a VM, Docker, WSL or cloud infrastructure.
The current deliverables are the [execution plan](WORKSTATION_EXECUTION_PLAN.md),
[compatibility matrix](WORKSTATION_COMPATIBILITY_MATRIX.md) and necessary
ledger updates. The proposed WS-1 checkpoint would add one Bash launcher for
`--help`, `--version` and `status` in an already approved installed Python
environment, with focused tests. WS-1 requires separate approval. Setup,
configuration, run and report workflows are design topics at this checkpoint.

The dedicated host assumed by the [B1 checklist](P2B_B1_APPROVAL_CHECKLIST.md)
is unavailable under these constraints. RMAP-02 and D09-B stay OPEN and B1
execution is BLOCKED. Zero sentinel launches and zero B3 semantic case-attempts
have run. Native Windows evidence I/O and qualification are BLOCKED. The
workstation plan confers no authority for CP4/CP5, P2B execution or operational P3.
Authority is DRAFT, semantic verification UNVERIFIABLE, independent semantic
acceptance BLOCKED and benchmarks NOT_RUN.

**Previous checkpoint, 2026-11-06.** The user accepted the B1 isolation design and
test plan at `fd9dc0194da9f15ff99805dd5ab6dea38815e684` as documentation only.
That checkpoint covered the [B1 approval checklist](P2B_B1_APPROVAL_CHECKLIST.md)
and necessary decision-ledger updates. RMAP-02 and D09-B are OPEN. The host,
owners, policy, custody, retention and budget await human decisions. B1 execution
is BLOCKED, with zero sentinel launches and zero B3 semantic case-attempts.

**Previous checkpoint, 2026-11-06.** The user accepted P3-A1 at
`5e62727b9b8e463cf6c7dd1bc68172801a7868f6` for its private diagnostics on
supplied public synthetic graphs and approved P2B-B1 isolation readiness
planning only. The review covers the [isolation design](P2B_B1_ISOLATION_DESIGN.md),
[test plan](P2B_B1_TEST_PLAN.md) and necessary ledgers. RMAP-02 and D09-B are
OPEN. B1 implementation, provisioning and execution require future explicit
authorization. Operational P3, P3-A2, P4, CP4/CP5, private intake and downstream
changes remain outside scope. Independent semantic acceptance and native Windows
qualification stay BLOCKED.

**Accepted CP3D.** The user accepted the private metadata primitives, protocol
and pure/simulated tests at `d6b25d35a97290bb5c72673b9267c9d6dd3564d7`
within their documented scope. Native bootstrap, absence proof and filesystem
authority remain open. See [design](CP3D_DESIGN.md) and
[validation](CP3D_VALIDATION.md).
CP3C's [bootstrap design](CP3C_BOOTSTRAP_DESIGN.md) and
[qualification plan](CP3C_QUALIFICATION_PLAN.md) remain historical planning records.

**Accepted CP3B:** private retained-handle implementation and simulated/unit tests
at `a29af0ec024945b15d31435e7041d45e92278c68`;
[design](CP3B_DESIGN.md) and [validation](CP3B_VALIDATION.md).
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
| P2 readiness documentation | APPROVED planning scope | Only the two P2 design documents and this decision ledger |
| D08-A and D08-B | APPROVED for P2A | Exact synthetic subset and canonical v2 evolution; deterministic reconstruction and reviewed public tests only |
| P2A result | ACCEPTED by the user's review | Commit `56154dd75a0149043c36081da9704b0a939230e1`; public synthetic scope, no independent semantic acceptance |
| P2B readiness documentation | APPROVED planning scope | Two readiness/practice documents and necessary decision-ledger updates only; preserve code, tests, hashes and downstream pin |
| D08-C and D09-A/B/C below | RECOMMENDED, NOT APPROVED for P2B | No provider selection, protected-gold grader, isolation deployment or independent acceptance |
| D10–D12 | OPEN | Business/oracle/runtime/downstream choices remain later human decisions |
| CP1 result | ACCEPTED by the user | `0061b7bf038f7b36add830912258232f174af197`; native Windows qualification still BLOCKED |
| CP2 result | ACCEPTED by the user | `fe3bbe98704fd33fb9516b53e8786e516dce9e1e`; declarations/projection only, no physical authorization |
| CP3 readiness documentation | APPROVED planning scope | Design, proposed tests/instructions and factual ledger updates only |
| CP3A implementation | APPROVED bounded subset | Separate POSIX preflight, physical alias checks and synthetic verification only; no legacy failure-timing change |
| CP3B implementation | APPROVED bounded subset | Private read-only native layer/protocol; public Windows access BLOCKED until physical bootstrap and qualification |
| CP3B result | ACCEPTED within limited simulated-test scope | `a29af0ec024945b15d31435e7041d45e92278c68`; not native security qualification |
| CP3C planning/security review | APPROVED documentation only | Two planning documents, necessary ledgers and applicable existing checks; no implementation or provisioning |
| CP3C result | ACCEPTED planning checkpoint | `5453a2598bd6da4ee695602f539f3961e70556b7`; no native assurance |
| CP3D implementation | APPROVED bounded private subset | Simulated metadata protocol and defensible native primitives only; incomplete native guarantees stay BLOCKED |
| CP3D result | ACCEPTED only in pure/simulated scope | `d6b25d35a97290bb5c72673b9267c9d6dd3564d7`; no native bootstrap, public access or publication |
| Post-CP3D roadmap | ACCEPTED by the user | Planning record at `dba5b3aa5a60ef384bfc57a90b46ca72ea4f27dc` |
| P3-A1 development experiment (RMAP-01) | ACCEPTED within private engineering scope | Private synthetic graph diagnostics and A01–A26 at `5e62727b9b8e463cf6c7dd1bc68172801a7868f6`. See [design](P3_A1_DESIGN.md) and [validation](P3_A1_VALIDATION.md) |
| P2B-B1 isolation readiness | ACCEPTED as documentation only | Isolation design and test plan at `fd9dc0194da9f15ff99805dd5ab6dea38815e684` |
| P2B-B1 approval checklist | APPROVED documentation only | Human decision checklist and necessary decision-ledger updates only |
| Workstation execution planning | ACCEPTED as documentation only | Execution plan and compatibility matrix at `a79b15fefd878f1ecc9c0e4969e1c6a211120a41` |
| WS-1 launcher and W01–W06 | APPROVED bounded engineering scope | Exactly one of `--help`, `--version` or `status`. Stop after validation for review. Release inventory, authentication and target-native qualification are separate decisions |
| WS-1 result | ACCEPTED within tested scope | `767b2c3154de7fb451c4278e22f25633d9a025d0`. Historical macOS ARM64 and hosted Linux x64 results only. Native Windows W01–W06 are BLOCKED / NOT_RUN |
| WS-2A offline kit and installation test plans | APPROVED documentation only | Two plans and necessary ledgers. Stop at documentation review. Future release, implementation and per-target execution decisions are OPEN |
| MVP-1 synthetic experiment | APPROVED for draft generation only | One public fixture, a private renderer and two untested alternatives. P2B independent semantic acceptance stays BLOCKED; P3/P4 operational work needs separate approval. |
| MVP-2 multi-module example | APPROVED for public synthetic draft generation only | One additional fixture and six review documents. Independent semantic acceptance remains BLOCKED. |
| MVP-3 behavioral tie-out | APPROVED for public synthetic development only | Fixed cases for O1–O3, O4 unresolved. Complete-workflow acceptance BLOCKED. |
| MVP-4 decision review | APPROVED for a draft review of fixed public evidence only | Conditional Python/Spark guidance. No production selection or runtime benchmark. |
| Operational P3, P3-A2 and P4 | OPEN, NOT APPROVED | Operational P3 requires independent source/graph acceptance, then draft PRD/module specifications and separate authorization. A1 provides no independence, scheduling or runtime verdict |
| Broader Windows native qualification | OPEN, NOT APPROVED | Requires separately approved real environment, owners and security evidence |
| CP4/CP5 implementation | OPEN, NOT APPROVED | No publication/locks or dependency/qualification expansion implied by CP3 planning |

## WS-2A decisions requiring separate approval

| Decision | Status | Evidence needed for a future decision |
|---|---|---|
| Human release authority | OPEN | Name an accountable release custodian, independent reviewer and target workstation custodian. Record who may approve artifacts, authenticate delivery, revoke a kit and authorize rollback. |
| External trust and artifact approval | OPEN | Approve the external trust root and delivery channel, custody and offline revocation policy. Independently approve the exact interpreter, bootstrap tools, project wheel and complete locked wheel set per tuple. |
| Target-specific lock coverage | OPEN | The current lock covers `rpds-py` on macOS ARM64 and Linux x64 CI. Extending it for Windows x64 or Intel Mac requires independent review of the exact artifact bytes and explicit lock-change authorization. |
| Installer implementation | OPEN | Authorize a bounded implementation scope and its tests after reviewing both WS-2A plans. |
| Native installation and test execution | OPEN | Approve each exact host/OS/CPU, shell and Python tuple, standard-user destination, offline controls and recovery evidence before authorizing provisioning or a trial. All proposed trials are NOT_RUN. |
| Kit release and workstation activation | OPEN | Obtain separate release authorization for a concrete kit. An independent custodian must bind each final installation inventory and authenticate the final launcher through the trusted external channel. Activation of that installation requires its own decision. |

These decisions apply to installation only. Native Windows source access and
qualification are BLOCKED. B1 retains its distinct host and reviewer gates.
P4, CP4 and CP5 each require separate approval. Artifact authority is DRAFT,
semantic verification UNVERIFIABLE, independent acceptance BLOCKED and
benchmarks NOT_RUN.

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

Historical next action after CP3C: review the design/qualification documents and resolve
required inputs below. No proposed mechanism is an approved or qualified control.
CP3A's existing POSIX behavior and legacy publication timing stay unchanged.
Missing native prerequisites remain OPEN/BLOCKED. The user's CP3D approval now
permits only the bounded implementation above; it does not approve qualification.

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

## CP3D remaining gates

The CP3D scope implements the defensible subset, not approval of CP3C's OPEN
runtime decisions. No host owner or independent human reviewer has been supplied.

| ID | Status | Evidence and next requirement |
|---|---|---|
| CP3D-D01 | OPEN / native BLOCKED | Host/token, inspection and backing references are typed external comparison data. Authentic source, protection, issuer, expiry/revocation and exact native execution grant remain missing; no automatic approval loader |
| CP3D-D02 | OPEN / native BLOCKED | Nt root-open flags, exact handle-bound long-name/alias semantics, native device/case queries and synchronous completion/buffer lifetime require review and actual negative fixtures. No Nt filesystem call is bound in CP3D |
| CP3D-D03 | OPEN / native BLOCKED | Simulated repeated absence observations rely on quiescent namespace writers, do not detect every ABA and never reserve a name. No native absent-store success, receipt serialization or CP4 authorization |
| CP3D-D04 | OPEN | Named Windows 11 x64/NTFS owner, independent reviewer, custodian, observer and approved Python/PowerShell/offline artifacts; no provisioning or native execution authorized |
| CP3D-D05 | OPEN | Any native implementation extension, qualification, public reader activation or publication requires separate explicit approval. The P3-A1 engineering exception grants no native authority |

## Decision register

### Post-CP3D sequencing decisions

RMAP-01 was separately approved after the [roadmap](POST_CP3D_ROADMAP.md).
RMAP-02–05 stay OPEN, including ownership and proof obligations for P2B and
native Windows qualification. See the [dated approval](APPROVALS.md).

| ID | Human decision | Boundary / consequence |
|---|---|---|
| RMAP-01 | P3-A1 development only, accepted | Private, pure synthetic canonical v2 dependency/blocker diagnostics and exact A01–A26. Independent source/graph acceptance and draft PRD/module specifications still precede operational P3 |
| RMAP-02 | OPEN. The dedicated host is unavailable under the workstation constraint. Host ownership, administration, independent review, runtime/policy, custody, retention and budget decisions are outstanding | B1 proof is BLOCKED. The [checklist](P2B_B1_APPROVAL_CHECKLIST.md) records implementation, provisioning, sentinel execution and later semantic evaluation as separate OPEN authorizations. B2 preparation and B3 campaign execution have separate gates. Verified parallelism requires P2B acceptance and further claim-specific evidence |
| RMAP-03 | Assign native Windows authority/runtime/reviewer/custodian and approve exact qualification scope | Preserve every CP3C/CP3D blocker; do not make private graph engineering wait for missing Windows infrastructure, and do not treat it as Windows evidence |
| RMAP-04 | Approve later claim-specific semantic/parallelism coverage | Frozen source-subset acceptance does not certify new transformation, scheduling, partition or performance claims. New independent challenge coverage and thresholds need explicit review |
| RMAP-05 | Supply exact release target/runtime tuples and approve qualification execution | The offline native Windows/macOS requirement is already established; preserve operation without runtime Git/Docker/WSL/VM/cloud/editor/provider requirements. CP4/CP5 qualification and Windows dependency approvals remain OPEN |

### Historical product decisions

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
| D09-B: isolation | The accepted B1 plan calls for sentinel probes and trusted handoff on a dedicated Linux host/VM with separate identity, process, mount and network boundaries, positive controls and denial tests | OPEN. That host is unavailable. Workstation checks cannot meet the B1 proof obligations. RMAP-02 prerequisites and separate implementation, provisioning and execution grants are outstanding. An isolation finding also requires independent human review of actual evidence |
| D09-C: corpus, metrics and feedback | 12 families × P/N/U = 36 hidden cases; reconstruction and checker-challenge lanes; five fixed attempts per case/lane; all required positive facts correct, exact negative gates, 100% obligation coverage and zero critical false approvals | Approval of strict finite-pilot thresholds, repetition/transport-failure policy and restricted diagnostic release; actual gold-derived assertion denominators frozen before running |

No particular person, model, evaluator host, hidden corpus or semantic test result
has been supplied/verified by this checkpoint. If those dependencies are absent,
future implementation/evaluation must report BLOCKED rather than invent them.

### P2B readiness refinements, proposed only

The B1 plan calls for 10 sentinel families × 2 untrusted principals × 2 fresh
launches = **40 proposed B1 family-runs**. The later semantic schedule is
36 cases × 2 lanes × 5 repetitions = **360 scheduled B3 case-attempts**. B1 has
zero executed family-runs at this checkpoint. B2 preparation and B3 evaluation
require separate approval after the applicable gates below.

[P2B_READINESS.md](P2B_READINESS.md) assesses D08-C and D09-A/B/C without approving
them. The [B1 checklist](P2B_B1_APPROVAL_CHECKLIST.md) records the separate
decisions required before a sentinel-only proof.
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

The P2B readiness checkpoint ended at documentation. P2B implementation or
campaign execution still requires a separate grant.
