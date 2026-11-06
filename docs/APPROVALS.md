# Scope approval record

On 2026-11-05 the user explicitly approved D01, D02 and D03 as recommended:

- New local repository `sas-reverse-engineering` under the current workspace,
  with separate Git history and no remote publication.
- Exact specification ZIP SHA-256
  `e3cbf3d9df6cc20c594261556c5e3ea1dfc292c9c1a30672c2d7b1a736b9718e`.
- Python 3.12 and Step 2/P0 foundation only, pinned to Agent-mastery commit
  `bc754e0f1204a99020c864df2a5b25983005e09c`.

Authorized: package scaffold, reproducible dependency setup, minimal honest CLI,
Git/security exclusions, scaffold CI, downstream metadata/drift check, README and
local foundation tests. Stop after P0; P1 requires separate user approval.

`IMPLEMENTATION_PLAN.md` preserves the historical Step 1 copy. The pending
decision language is superseded by the dated approvals here. This
engineering-scope approval is not a downstream PRD, ADR,
oracle, tie-out, runtime, merge or release approval.

The user subsequently authorized pushing this P0 repository to
`https://github.com/keshavnath1/sas-reverse-engineering` on 2026-11-05.
This supersedes the initial local-only publication restriction. P1 remains
unapproved at that time; publication does not change any downstream human approval boundary.

On 2026-11-05 the user explicitly approved Step 3/P1 and D04–D07, including the
complete continuation and acceptance checklist supplied as pasted text. Approved:
versioned source contracts, explicit synthetic scope, raw-byte identity and
citations, supplied-record structural verification, append-only attempts,
inventory/seal/verify CLI, adversarial tests, documentation and CI. P1 must be
checked in the development checkout, fresh checkout and installed wheel.

The source graph is one composed graph per scoped run; module views reference
canonical IDs. IDs change when source context or supplied operation facts change.
Log associations require declarations; unresolved dependencies remain explicit.
Read-only intake, traversal/symlink protection and safe publication are required.
Local SHA-256 proves integrity comparisons, not authenticated production provenance.

This supersedes the earlier P0-only implementation restriction. It does not
authorize P2, private intake, SAS execution, agents, architectural recommendations,
PRD/ADR generation, downstream integration, or any human approval claim.
Stop after P1 and await review and explicit P2 approval.

On 2026-11-05 the user reviewed P2 planning at
`e13705c67c5984b2cb6bc8d4c797a188fd6421e2` and explicitly approved **P2A only**,
including D08-A (exact synthetic SAS subset) and D08-B (canonical graph v2).
Authorized: deterministic reconstruction, versioned contracts and validators,
explicit identity lineage, source-grounded public synthetic regression fixtures
whose expectations are independently reviewed, CLI/CI and design/validation docs.
Preserve v1 evidence, source read-only boundaries and append-only attempts.

D08-C and D09 remain open for P2B. No model provider, protected-gold environment,
independent evaluator or semantic acceptance claim is authorized. Public tests
demonstrate bounded reconstruction behavior only. Semantic acceptance remains
BLOCKED and benchmark execution NOT_RUN. Do not execute SAS, read private business
inputs, change Agent-mastery or start P2B/P3. Stop after P2A and provide the missing
P2B readiness decisions for separate review.

On 2026-11-05 the user reviewed and accepted P2A at
`56154dd75a0149043c36081da9704b0a939230e1` and approved **P2B readiness only**:
a read-only assessment and documentation checkpoint. Authorized deliverables are
`docs/P2B_READINESS.md`, `docs/BEST_PRACTICES_ADOPTION.md` and necessary
decision-ledger updates. Assess D08-C and D09-A/B/C, propose sentinel-only proof,
budgets/stops and the next authorization, and backfill practice evidence only
from attributable existing records. Preserve P0/P1/P2A code/tests, source hashes
and Agent-mastery compatibility pins.

This does not approve a provider, candidate agent, semantic grader, isolation
infrastructure, hidden gold or campaign. D08-C and D09 execution decisions remain
open; independent semantic acceptance remains BLOCKED. Stop after documentation
for review. The prior remote-publication authorization remains in effect, without
granting any later implementation or downstream authority.

On 2026-11-05 the user reviewed portability plan commit
`1c172fbb79a8ba07bf72f2f40ecf0f5db02b564a` and explicitly approved **CP1 only**:
import-safe shared code, narrow backend/capability selection, explicit denial
before source/store I/O, pure CLI/contract access, POSIX regression preservation,
focused tests, CP1 design/validation documentation and a small practice-ledger
update. Frozen v1/v2 schemas, identity/byte algorithms, artifact formats and the
Agent-mastery pin must remain unchanged. Publication authorization remains valid.

Proposed Windows qualification target: Windows 11 x64/NTFS, PowerShell 7 preferred,
Python 3.12. This is not platform qualification or permission to install Windows
dependencies/extend lock hashes. If an approved actual environment is absent,
native Windows qualification is BLOCKED. Existing macOS/Linux checks may run.
No Git, model/provider, cloud, Docker or WSL runtime prerequisite may be added.

CP2 authorization envelopes, CP3/CP4 Windows reading/publication, CP5 functionality,
AI adapters, P2B/P3 and downstream modifications remain unapproved. Semantic
acceptance stays BLOCKED, authority DRAFT and benchmarks NOT_RUN. Stop after CP1
and report actual platforms, commands, failures/corrections and proof limits.

On 2026-11-05 the user accepted CP1 at
`0061b7bf038f7b36add830912258232f174af197` within its tested scope and explicitly
approved **CP2 only**: a separately versioned local authorization envelope,
deterministic logical-scope projection, native path syntax validation without
filesystem access, public validators, synthetic independent compatibility vectors,
adversarial tests and design/validation/practice-ledger updates. Existing 411
regressions, frozen v1/v2 schemas, sealed artifacts, identity rules and compatibility
pin must remain unchanged. Publication authorization remains in effect.

This approves the bounded CP2 contract/projection work proposed under CP-D02;
it does not approve physical authorization, a local binding receipt/consumer,
Windows I/O, CP3–CP5, P2B/P3 or downstream integration. A path string never grants
source permission. No private workload, SAS execution, provider, Windows dependency
installation or lock extension is authorized. Native Windows qualification remains
BLOCKED unless actually executed in an approved environment. Semantic acceptance
stays BLOCKED, authority DRAFT and benchmarks NOT_RUN. Stop after CP2 for review.

On 2026-11-05 the user accepted CP2 within its approved scope at
`fe3bbe98704fd33fb9516b53e8786e516dce9e1e` and authorized **CP3 readiness and
implementation design only**. Approved: read-only review of CP1/CP2 bindings,
native Windows security design, proposed POSIX physical-alias strengthening,
fail-closed outcomes, adversarial tests/qualification instructions, and necessary
decision/practice-ledger updates. Deliverables are `CP3_READINESS.md` and
`CP3_SECURITY_TEST_PLAN.md`. Missing host owner, independent security reviewer,
filesystem assumptions and approval requirements must remain OPEN.

This does not authorize CP3 source reading, CP4 publication/locks, schema or
historical-artifact changes, dependency installation/lock changes, Agent-mastery
modifications, private intake, SAS execution, P2B, P3 or architecture generation.
Proposed tests are not execution permission or qualification evidence. Native
Windows qualification remains BLOCKED; semantic acceptance stays BLOCKED,
verification UNVERIFIABLE, authority DRAFT and benchmarks NOT_RUN. Prior repository
publication authorization remains in effect. Stop after documentation and wait
for explicit CP3 implementation approval.

The user subsequently approved **CP3A implementation only** at
`07ddcda5a78a9a2f9f093a94e722532f44e3044b`: bounded macOS/Linux physical
source/store disjointness, a separate read-only authorization/preflight boundary,
declared-prefix membership, all-file read readiness, retained-handle mutation/
replacement checks, BLOCKED diagnostics, synthetic adversarial tests, development/
fresh-checkout/wheel verification and design/validation/ledger updates.

Preserve all 456 baseline tests, original-byte/graph/citation identities, frozen
schemas, prior seals, append-only history and the downstream pin. This does not
approve silent changes to legacy persistence/failure timing. If integration
conflicts with those behaviors, preserve old records and stop for explicit review.
The implemented CP3A path is additive and creates no output; legacy workflows are
not rewritten. Run-specific local inspection remains separate from this project
implementation approval and from unverified CP2 caller metadata.

No Windows source access, CP4 publication redesign, CP5 packaging/release
qualification, private intake, SAS execution, dependency/provider change,
Agent-mastery modification, P2B or P3 is authorized. Existing publication permission
for this repository continues. Stop after CP3A; do not begin CP3B automatically.

The user accepted CP3A within its tested POSIX scope at
`f841ca25d511230d77ab1c3eded3f59602a79f5d` and approved **CP3B implementation only**:
an import-safe, fail-closed Windows read-only synthetic preflight backend, narrow
native APIs, focused independent test vectors and design/validation/ledger updates.
If critical native assumptions cannot be established, implement only the defensible
subset and report the rest BLOCKED. All 514 regressions and frozen contracts,
identities, artifacts, POSIX behavior and downstream pin must be preserved.

Actual native Windows qualification requires a separately approved real Windows
environment. No host/owner/dependency environment or native bootstrap approval was
provided by this implementation authorization. Simulations cannot qualify native
support. Public Windows evidence/publication stays BLOCKED. No new dependency,
lock change, private intake, SAS execution, Agent-mastery modification, CP4, CP5,
P2B or P3 is approved. DRAFT/UNVERIFIABLE/BLOCKED/NOT_RUN authority and verification
conventions remain. Stop after CP3B. Existing remote-publication authorization
continues; it does not grant later runtime or human security approval.

The user accepted CP3B at `a29af0ec024945b15d31435e7041d45e92278c68`
within its limited simulated-test scope and authorized **CP3C planning and
security review only**. Approved deliverables: Windows volume-bootstrap design,
absent-store proof design, native API assumption review, actual-environment and
offline dependency prerequisites, ordinary-versus-provisioned qualification cases,
independent evidence/acceptance criteria, necessary decision/practice records and
applicable existing documentation/preservation/CI checks.

No implementation, dependency/lock change, Windows source-content access, public
reader enablement, publication or new output-store creation is approved. No private
SAS intake/execution, Agent-mastery change, CP4, CP5, P2B or P3. Preserve all 596
tests and frozen contracts/identities/history. Missing host owners, human reviewers,
provisioning and authorization remain OPEN; native guarantees remain BLOCKED.
Repository publication authorization persists for the documentation checkpoint;
it does not authorize a Windows environment or native test execution. Stop after
planning for explicit further approval.

On 2026-11-06 the user accepted CP3C planning at
`5453a2598bd6da4ee695602f539f3961e70556b7` and authorized **CP3D only**:
bounded private import-safe Windows bootstrap/absent-store primitives, typed
independently supplied host/volume expectations, retained metadata identity checks,
defensible locality/mapping queries, typed lookup outcomes, simulated/fault tests,
design/validation documents and necessary ledgers. Unsupported API/completion
guarantees must remain BLOCKED rather than acquire a weaker fallback.

Preserve all 596 historical tests, frozen contracts/identities/history, existing
POSIX behavior and Agent-mastery pin; repeat artifact/hash comparisons. This is
not native qualification, public Windows reader/workflow activation, deployment,
CP4 publication, source-content access or permission to create/modify a source or
store. No private inputs/SAS, dependency/lock changes, self-approved inspection
grant, drive scan or new runtime service/provider requirement. Host/reviewer,
provisioning and native authority remain OPEN. Stop after CP3D; CP4/CP5/P2B/P3
need separate approval. Existing repository-push authorization remains valid.

On 2026-11-06 the user accepted the [post-CP3D roadmap](POST_CP3D_ROADMAP.md)
at `dba5b3aa5a60ef384bfc57a90b46ca72ea4f27dc` and approved **P3-A1 only**.
The explicit development-order exception allows one private, pure dependency
and blocker diagnostic over supplied in-memory public synthetic canonical v2
graphs before P2B. Scope includes independent public vectors, exact A01–A26
obligations, preservation checks, the [design](P3_A1_DESIGN.md),
[validation](P3_A1_VALIDATION.md) and necessary ledger updates.

Keep the 667 baseline tests, frozen contracts, identity and sealed bytes, POSIX
behavior, dependency lock and downstream pin. Only existing synthetic regression
and preservation fixtures may use source/store I/O for their original purposes.
The diagnostic accepts no caller path and publishes nothing. Native Windows
activation and qualification stay BLOCKED. Private intake, SAS execution,
dependency/provider changes and downstream modifications are outside this grant.

The experiment grants no operational P3 transition, independence finding,
schedule or runtime recommendation. P2B execution, P3-A2, P4, CP4 and CP5
require separate approval. Operational P3 still requires independent source and
graph acceptance followed by draft PRD/module specifications. Keep authority
DRAFT, verification UNVERIFIABLE, acceptance BLOCKED and benchmarks NOT_RUN.
Stop after P3-A1 validation for explicit user review.

On 2026-11-06 the user accepted P3-A1 at
`5e62727b9b8e463cf6c7dd1bc68172801a7868f6` within its documented private,
in-memory public synthetic diagnostic scope and approved **P2B-B1 isolation
readiness planning only**. The authorized deliverables are the
[isolation design](P2B_B1_ISOLATION_DESIGN.md), [test plan](P2B_B1_TEST_PLAN.md)
and necessary ledger updates. The proposed 40 sentinel family-runs belong to a
future B1 proof. The 360 scheduled semantic case-attempts belong to B3. Each
schedule requires its own execution authorization.

RMAP-02 and D09-B are OPEN pending human decisions on the host and owner,
administrator, independent security reviewer, runtime/image and policy, storage,
retention and budget. Stop at documentation review. Provisioning, implementing
or running probes and evaluation work in B2/B3 require further explicit scope.
Native Windows qualification stays BLOCKED. Authority is DRAFT, semantic
verification UNVERIFIABLE, independent acceptance BLOCKED and benchmarks NOT_RUN.

On 2026-11-06 the user accepted the B1 planning checkpoint at
`fd9dc0194da9f15ff99805dd5ab6dea38815e684` as documentation only and authorized
the [B1 approval checklist](P2B_B1_APPROVAL_CHECKLIST.md) and necessary
decision-ledger updates. The host, owners, runtime/policy, custody, retention
and budget are OPEN under RMAP-02 and D09-B. Implementation, host provisioning,
sentinel execution and later semantic evaluation each require a separate
explicit authorization. All four decisions are OPEN. B2 preparation and B3
campaign execution each require their own grant.

B1 execution is BLOCKED, with zero sentinel launches and zero B3 semantic
case-attempts. Artifact authority is DRAFT, semantic verification UNVERIFIABLE,
independent semantic acceptance BLOCKED and benchmarks NOT_RUN.

On 2026-11-06 the user authorized a **documentation-only workstation planning
checkpoint** at `13a82fdb48248215548a57463aafc075edeb7e41`. The deliverables
are the [workstation execution plan](WORKSTATION_EXECUTION_PLAN.md),
[compatibility matrix](WORKSTATION_COMPATIBILITY_MATRIX.md) and necessary ledger
updates. The targets for ordinary use are macOS Terminal/Bash and Windows Git
Bash with an existing Python 3.12 installation or an approved offline bundle.
Git commands, AI services, a dedicated host, VMs, Docker, WSL and cloud services
are excluded as ordinary-use prerequisites.

WS-1, the proposed next checkpoint, needs separate approval for one Bash
launcher limited to `--help`, `--version` and `status` in an already approved
installed Python environment, plus focused tests. Setup, configuration, run and
report workflows are design topics only. Stop at documentation review. CP4/CP5,
P2B execution and operational P3 each require separate authorization. B1
execution is BLOCKED by the dedicated-host requirement and native Windows
evidence I/O is BLOCKED pending separate qualification.

On 2026-11-06 the user accepted the workstation plan at
`a79b15fefd878f1ecc9c0e4969e1c6a211120a41` and approved **WS-1 only**.
This covers one read-only Bash launcher for exactly one of `--help`, `--version`
or `status`, the six W01–W06 test families, usage/validation documentation and
necessary ledger updates. Preserve all 693 existing regressions and historical
synthetic evidence. Stop at WS-1 review. See the [design](WS1_DESIGN.md) and
[validation record](WS1_VALIDATION.md).

The production installation inventory and its independently authenticated pin
are outstanding. The shipped launcher leaves both fields empty and returns
bootstrap BLOCKED/2 for each valid request. A historical wheel or a caller's
`SAS_RE_PYTHON` setting cannot supply release authority. Native Windows
qualification is BLOCKED / NOT_RUN. Setup, config, run and report modes, CP4/CP5,
B1/P2B execution, operational P3, private intake and downstream changes each
require separate approval. Artifact authority is DRAFT, semantic verification
UNVERIFIABLE, independent acceptance BLOCKED and benchmarks NOT_RUN.

On 2026-11-06 the user accepted WS-1 at
`767b2c3154de7fb451c4278e22f25633d9a025d0` within its documented, tested
scope. The [WS-1 validation record](WS1_VALIDATION.md) attributes the launcher
results to macOS ARM64 development runs and hosted Linux x64 CI. Successful
dispatch used synthetic approval records. The repository launcher retains empty
approval slots and returns bootstrap BLOCKED/2 for each valid verb. Native
Windows W01–W06 are BLOCKED / NOT_RUN.

The user approved **WS-2A planning only**. Deliverables are the
[offline kit plan](WS2A_OFFLINE_KIT_PLAN.md), the
[installation test plan](WS2A_INSTALLATION_TEST_PLAN.md) and necessary approval,
decision and practice ledger updates. Stop at documentation review. Release
ownership and authentication, approval of exact artifact bytes, installer
implementation, native installation and test execution, kit release and
workstation activation require separate future decisions. All are OPEN. This grant
covers no key, approved hash, kit, lock or package change, provisioning or
installation. Windows source access and qualification, B1/P2B execution, P4,
CP4 and CP5 retain their separate gates.

On 2026-11-06 the user accepted WS-2A as documentation at
`6e403722d64d15a41b4205cb074bb8d928fad3a2` and authorized MVP-1 as a
bounded development experiment. One public synthetic workflow may feed a private,
in-memory [draft architecture preview](../examples/mvp1/ARCHITECTURE.md).
Authority stays DRAFT; verification UNVERIFIABLE, semantic acceptance BLOCKED,
benchmarks NOT_RUN. Stop for review of the package. Runtime selection, operational
P3/P4, P2B evaluation, Windows access, packaging, publication and downstream
integration require separate decisions.

At `022c672d244a522e25a5aded7f29513f51875b69` the user accepted MVP-1 only
as a public synthetic demonstration and approved the bounded MVP-2 experiment.
Its [multi-module draft](../examples/mvp2/ARCHITECTURE.md) and [validation
report](MVP2_VALIDATION.md) are for review. Independent evaluation, migration,
publication, native Windows access and runtime selection retain their separate gates.
