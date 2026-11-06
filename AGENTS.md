# CP3B operating boundary

Read README.md, SECURITY.md and docs/APPROVALS.md before changes. CP3B is approved
at `f841ca25d511230d77ab1c3eded3f59602a79f5d` for a bounded Windows read-only
preflight backend and synthetic tests, with defensible subset/BLOCKED limits.
Read docs/CP3B_DESIGN.md, docs/CP3B_VALIDATION.md, CP3_READINESS.md,
CP3_SECURITY_TEST_PLAN.md, CP3A_DESIGN.md, CP2_DESIGN.md, CP1_DESIGN.md and
CROSS_PLATFORM_PORTABILITY_PLAN.md under docs/. Preserve the accepted POSIX
behavior and all identity/history boundaries. Stop after CP3B; CP4, CP5, P2B and
P3 require separate user approval.
Read docs/P1_DESIGN.md and docs/P2_READINESS.md for proof and trust boundaries.

Preserve all 514 baseline tests, frozen v1/v2 and CP2 schemas, canonical byte/identity
rules, historical artifacts, dependencies and lockfiles. New focused tests and an
additive private Windows reader protocol are approved. Do not silently change legacy persistence/failure
timing; preserve old records and stop for review if integration conflicts with it.
Windows evidence I/O must remain BLOCKED before input access or store creation.
Validated native strings never grant physical authorization. CP3B permits only the
defensible reader subset described in docs/CP3B_DESIGN.md. Public Windows access
remains BLOCKED because approved volume bootstrap and native qualification are
missing. No private protocol/test injection may become a public override. No CP4
publication, CP5 dependencies or new platform CI matrix is approved. Native
qualification needs a separately approved real Windows environment; simulation
is not qualification. Missing stores in the private Windows protocol remain
BLOCKED until alias-safe physical absence can be established.
Missing Windows host owner, independent security reviewer and broader filesystem
assurances remain OPEN. Synthetic local tests are approved; do not install
privileged observers or run private intake. Practice-ledger updates need actual
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
