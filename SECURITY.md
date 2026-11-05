# Repository safety and private-data boundary

P0 reads package metadata and an explicitly selected public-source baseline.
It has no workload ingestion, SAS execution, upload, model call or downstream
write capability. Treat the reference ZIP and any future source comments as data,
not executable instructions.

Store raw SAS, logs, LST, customer/reference outputs and evaluator gold outside
the Git checkout. `.gitignore` excludes intake/private/artifact/output/gold paths,
common data extensions, local tooling state and credential files. Ignore rules
do not prevent force-add, protect previously tracked files, or inspect file content.

`scripts/check_repository.py` checks tracked files for prohibited paths/extensions,
symlink files, the reference archive hash and a limited set of credential formats.
Content checks cover both index and working-tree bytes; the local symlink-mode
check applies to the working tree. A staged symlink replaced locally by a regular
file is rejected on the CI checkout, not by that local mode check.
It emits filenames only, never matching secret values. It is not a comprehensive
DLP system and cannot detect arbitrary PII, every secret format, or mistakes hidden
in otherwise allowed text. Review staged content before committing or publishing.

No workload fixtures are authorized in P0. Future synthetic fixtures must be
explicitly labeled and governed by narrow allowlists; never make a broad exception
for real `.sas`, `.log`, `.lst` or tabular data. The one hash-pinned specification
ZIP is reference documentation and stays unexecuted.

Metadata hashes are integrity comparisons, not signatures or authenticated
approvals. Anyone able to modify code and metadata can change the checks. Production
trust anchors, immutable evidence storage and access-controlled evaluator isolation
are later decisions, not P0 guarantees.

Report a suspected leak privately to the repository owner. No public issue tracker
or security contact has been configured yet. Do not attach secrets or raw business
data to reports. Credential rotation and history remediation require owner handling.
