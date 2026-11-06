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
