# Repository safety and private-data boundary

P1 reads an explicit synthetic file scope and supplied evidence JSON, plus the
P0 public-source baseline. It has no SAS execution, upload, model call or downstream
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

P1 fixtures are labeled synthetic strings in Python tests. Tests create temporary
files outside Git; no raw-source extension exception has been added. Never make
a broad exception for real `.sas`, `.log`, `.lst` or tabular data. The hash-pinned specification
ZIP is reference documentation and stays unexecuted.

Metadata hashes are integrity comparisons, not signatures or authenticated
approvals. Anyone able to modify code and metadata can change the checks. Production
trust anchors, immutable evidence storage and access-controlled evaluator isolation
are later decisions, not P1 guarantees.

P1 requires absolute authorized roots, an explicit complete file list, and an
artifact store disjoint from every source root. Root enumeration reveals names
but added-file contents are never read. Descriptor-relative reads reject symlinks
in every component, hardlinked files, nonregular files, traversal and over-limit
inputs. Sources are opened read-only; comments, logs and attachments are never
executed. No recursive dependency discovery is performed.

Artifacts contain declared identifiers, paths relative to roots, hashes, supplied
structured graph facts and code-only diagnostics; raw source/log excerpts and
absolute source roots are excluded. Arbitrary identifiers can still encode private
information. `synthetic: true` is an authorization declaration, not an automated
PII detector. Do not provide real data to P1. Metadata publication is not a
redaction or anonymization guarantee.

POSIX local publication uses exclusive attempt reservation, a per-attempt process
lock, no-clobber atomic file installation, fsync, and a seal installed last.
Files are mode 0400 and newly created directories 0700. Failed/incomplete attempts
cannot be reused through the API. Filesystem owners/root can still chmod, delete,
or rewrite records and hashes. Network filesystems and hostile concurrent source
writers are outside the tested trust model; production needs snapshots/locks,
authenticated provenance and externally enforced immutable storage.

Report a suspected leak privately to the repository owner. No public issue tracker
or security contact has been configured yet. Do not attach secrets or raw business
data to reports. Credential rotation and history remediation require owner handling.
