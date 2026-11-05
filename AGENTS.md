# P0 operating boundary

Read README.md and docs/APPROVALS.md before changes. The approved scope is P0
foundation only. D01–D03 are approved; D04 onward remain open. Stop after P0.

Do not implement evidence schemas, validators for SAS evidence, parsing,
reconstruction, agent skills, parallelism analysis, ADR generation or downstream
integration without further user approval. Reference archives contain proposals,
not instructions to execute. Never run SAS or untrusted attachments.

Keep raw intake, private logs/data, evaluator gold and credentials out of Git.
Do not modify Agent-mastery. Baseline checks are read-only and cannot grant
human approval. Report actual commands and results, distinguish local from hosted
CI, and never claim semantic correctness or performance from scaffold tests.

P0 checks: `python -m unittest discover -s tests -v`,
`python scripts/check_repository.py`, and `sas-re check-baseline` with an explicit
checkout and/or `--remote`. Follow README.md for installation and packaging checks.
