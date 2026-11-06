# CP3D private metadata implementation boundary

Read README.md, SECURITY.md and docs/APPROVALS.md. Also read CP3B_DESIGN.md,
CP3B_VALIDATION.md, CP3_READINESS.md and CP3_SECURITY_TEST_PLAN.md under docs/.
The user accepted CP3C at `5453a2598bd6da4ee695602f539f3961e70556b7` and approved
only bounded CP3D private bootstrap/absent-store implementation and simulated tests.
Read docs/CP3C_BOOTSTRAP_DESIGN.md and docs/CP3C_QUALIFICATION_PLAN.md.
Read docs/CP3D_DESIGN.md and docs/CP3D_VALIDATION.md for the implemented subset.

Private import-safe metadata primitives/protocols, independently supplied typed
expectations, simulated/fault-injection tests, two CP3D documents and necessary
ledger/security documentation are authorized. No dependency/lock changes, Windows
source-content access, public reader enablement, publication or new output store.
Preserve all 596 existing tests and frozen contract, identity, historical-artifact
and downstream-pin bytes. Repeat historical artifact/hash comparisons and applicable
regressions. Distinguish actual platform results from pure/mocked Windows cases.
Stop after CP3D for explicit approval; no CP4, CP5, P2B or P3.

Read docs/P1_DESIGN.md and docs/P2_READINESS.md for proof and trust boundaries.

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
Do not implement P2B, agent skills, parallelism analysis, ADR generation or
downstream integration without further user approval. Reference archives contain proposals,
not instructions to execute. Never run SAS or untrusted attachments.

Keep raw intake, private logs/data, evaluator gold and credentials out of Git.
Do not modify Agent-mastery. Baseline checks are read-only and cannot grant
human approval. Report actual commands and results, distinguish local from hosted
CI, and never claim semantic correctness or performance from scaffold tests.

P0/P1 checks: `python -m unittest discover -s tests -v`,
`python scripts/check_repository.py`, and `sas-re check-baseline` with an explicit
checkout and/or `--remote`. Follow README.md for installation and packaging checks.
