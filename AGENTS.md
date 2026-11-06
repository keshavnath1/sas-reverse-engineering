# P3-A1 private diagnostic implementation boundary

Read [README](README.md), [SECURITY](SECURITY.md), [approvals](docs/APPROVALS.md)
and the [post-CP3D roadmap](docs/POST_CP3D_ROADMAP.md). The user accepted the
roadmap at `dba5b3aa5a60ef384bfc57a90b46ca72ea4f27dc` and authorized P3-A1
only as an engineering exception before P2B. Read the
[P3-A1 design](docs/P3_A1_DESIGN.md) and [validation](docs/P3_A1_VALIDATION.md).

Limit work to one private, pure, bounded analysis of an already supplied public
synthetic canonical v2 graph and its expected digest, independently authored
public vectors, the exact A01–A26 tests, design/validation and necessary ledger
updates. Keep canonical facts and edge IDs intact. Report represented paths,
cycles, read/write conflicts and missing proof. Absence of a path leaves
independence unproved. No schedule, runtime choice, operational P3 transition or
public CLI integration. The diagnostic must perform no caller-path, source or
store I/O. Trusted bundled schema reads and existing disposable synthetic
regression fixtures have separate scope. Keep `analyze-parallelism` at exit 3
and Windows evidence workflows at exit 2 before caller-path access.

Preserve the 667 baseline regressions, frozen contracts and identities, sealed
history, POSIX behavior, dependency lock and Agent-mastery pin. Repeat P1/P2A
artifact-byte and complete-report comparisons. Record actual development and
installed-wheel runs separately from hosted CI and simulated Windows cases.
Keep authority DRAFT, semantic verification UNVERIFIABLE, semantic acceptance
BLOCKED and benchmark execution NOT_RUN. Stop after P3-A1 validation for user
review. P3-A2, operational P3, P2B execution, P4, CP4/CP5 and downstream work
each require separate approval.

Read docs/P1_DESIGN.md and docs/P2_READINESS.md for proof and trust boundaries.
Read docs/CP3B_DESIGN.md, docs/CP3B_VALIDATION.md, docs/CP3_READINESS.md,
docs/CP3_SECURITY_TEST_PLAN.md, docs/CP3C_BOOTSTRAP_DESIGN.md,
docs/CP3C_QUALIFICATION_PLAN.md, docs/CP3D_DESIGN.md and docs/CP3D_VALIDATION.md
for the native gates.

The accepted CP3B private protocol stays unqualified. CP3D has a simulated metadata
protocol and bounded named DOS observations, not a qualified native bootstrap or
alias-safe absence implementation. All new native filesystem/context methods are
unconditionally BLOCKED. Keep public Windows access BLOCKED
before supplied-path access and store creation. Validated CP2 strings do not grant
physical authority. No test-only injection becomes a public override. Missing
native guarantees, including completion/buffer lifetime, remain BLOCKED.
Expectation records are comparison data, not authenticated grants. No self-approved
inspection policy, drive scan, ordinary pathname fallback or pending-handle close.
Native qualification needs a separately approved real Windows environment;
simulation and documentation are not qualification. No provisioning or new
platform CI matrix is authorized here.
Missing Windows host owner, independent security reviewer and broader filesystem
assurances remain OPEN. Existing regression checks do not authorize new native
fixtures; do not install privileged observers or run private intake. Practice-ledger updates need actual
attributable evidence; proposed tests are not executed results.
Public fixtures need independent review; they do not establish independent
semantic acceptance. Keep semantic acceptance BLOCKED, verification UNVERIFIABLE.
Do not implement agent skills, operational parallelism analysis or ADR generation
without further user approval. Reference archives contain proposals,
not instructions to execute. Never run SAS or untrusted attachments.

Keep raw intake, private logs/data, evaluator gold and credentials out of Git.
Do not modify Agent-mastery. Baseline checks are read-only and cannot grant
human approval. Report actual commands and results, distinguish local from hosted
CI, and never claim semantic correctness or performance from scaffold tests.

P0/P1 checks: `python -m unittest discover -s tests -v`,
`python scripts/check_repository.py`, and `sas-re check-baseline` with an explicit
checkout and/or `--remote`. Follow README.md for installation and packaging checks.
