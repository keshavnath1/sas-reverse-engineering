# CP3 readiness operating boundary

Read README.md and docs/APPROVALS.md before changes. CP2 is accepted at
`fe3bbe98704fd33fb9516b53e8786e516dce9e1e`. CP3 is approved for readiness and
implementation design only: docs/CP3_READINESS.md, docs/CP3_SECURITY_TEST_PLAN.md,
proposed native qualification instructions and necessary decision-ledger updates.
Read docs/CP2_DESIGN.md, docs/CP1_DESIGN.md and
docs/CROSS_PLATFORM_PORTABILITY_PLAN.md. Preserve the
existing P2A deterministic synthetic subset. D01–D07 and D08-A/B are approved for
their bounded phases; D08-C and D09 remain open for P2B. Stop after CP3 planning;
explicit CP3 implementation approval is required before source-access changes.
Read docs/P1_DESIGN.md and docs/P2_READINESS.md for proof and trust boundaries.

Do not change code/tests, frozen v1/v2 or CP2 schemas, canonical byte/identity rules,
historical artifacts, dependencies or lockfiles in this checkpoint.
Windows evidence I/O must remain BLOCKED before input access or store creation.
Validated native strings never grant physical authorization. No envelope consumer,
CP3/CP4 Windows I/O/publication, CP5 dependencies or
new platform CI matrix is approved. Native Windows qualification needs an actual
approved interpreter/dependency environment; simulation is not qualification.
Missing host owner, independent security reviewer, filesystem assumptions and
implementation approval remain OPEN. Do not provision fixtures, install observers
or run private intake as part of readiness. Practice-ledger updates need actual
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
