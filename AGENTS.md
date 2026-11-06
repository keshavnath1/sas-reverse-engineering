# CP3A operating boundary

Read README.md and docs/APPROVALS.md before changes. CP3A is approved at
`07ddcda5a78a9a2f9f093a94e722532f44e3044b` for bounded POSIX physical authorization
and read-only preflight only. Read docs/CP3A_DESIGN.md, docs/CP3A_VALIDATION.md,
docs/CP3_READINESS.md and docs/CP3_SECURITY_TEST_PLAN.md.
Read docs/CP2_DESIGN.md, docs/CP1_DESIGN.md and
docs/CROSS_PLATFORM_PORTABILITY_PLAN.md. Preserve the
existing P2A deterministic synthetic subset. D01–D07 and D08-A/B are approved for
their bounded phases; D08-C and D09 remain open for P2B. Stop after CP3A;
CP3B and broader CP3 work require explicit further approval.
Read docs/P1_DESIGN.md and docs/P2_READINESS.md for proof and trust boundaries.

Preserve all 456 baseline tests, frozen v1/v2 and CP2 schemas, canonical byte/identity
rules, historical artifacts, dependencies and lockfiles. New focused tests and an
additive POSIX path are approved. Do not silently change legacy persistence/failure
timing; preserve old records and stop for review if integration conflicts with it.
Windows evidence I/O must remain BLOCKED before input access or store creation.
Validated native strings never grant physical authorization. Only the CP3A
separately scoped POSIX consumer is approved. No Windows I/O, CP4 publication,
CP5 dependencies or
new platform CI matrix is approved. Native Windows qualification needs an actual
approved interpreter/dependency environment; simulation is not qualification.
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
