# CP3C planning and security-review boundary

Read README.md, SECURITY.md and docs/APPROVALS.md. Also read CP3B_DESIGN.md,
CP3B_VALIDATION.md, CP3_READINESS.md and CP3_SECURITY_TEST_PLAN.md under docs/.
The user accepted CP3B at `a29af0ec024945b15d31435e7041d45e92278c68` only within
its limited simulated-test scope and approved CP3C planning/security review only.
Read docs/CP3C_BOOTSTRAP_DESIGN.md and docs/CP3C_QUALIFICATION_PLAN.md.

Create/update only the two CP3C planning documents and necessary decision,
approval/operating-boundary and best-practices records. No implementation or test-code changes,
dependency/lock changes, Windows source-content access, public reader enablement,
publication or new output store. Preserve all 596 tests and frozen contract,
identity, historical-artifact and downstream-pin bytes. Run applicable existing
documentation/preservation/CI checks and identify actual versus historical results.
Stop after planning for explicit approval; no CP4, CP5, P2B or P3.

Read docs/P1_DESIGN.md and docs/P2_READINESS.md for proof and trust boundaries.

The accepted CP3B private protocol stays unqualified; it has no approved volume
bootstrap or alias-safe absent-store proof. Keep public Windows access BLOCKED
before supplied-path access and store creation. Validated CP2 strings do not grant
physical authority. No test-only injection becomes a public override. Missing
native guarantees, including completion/buffer lifetime, remain BLOCKED.
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
