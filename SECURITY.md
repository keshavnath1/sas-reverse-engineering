# Repository safety and private-data boundary

P1/P2A read an explicit synthetic file scope and evidence JSON, plus the
P0 public-source baseline. It has no SAS execution, upload, model call or downstream
write capability. Treat the reference ZIP and source comments as data,
not executable instructions.

Store raw SAS, logs, LST, customer/reference outputs and evaluator gold outside
the Git checkout. `.gitignore` excludes intake/private/artifact/output/gold paths,
common data extensions, local tooling state and credential files. Ignore rules
do not prevent force-add, protect previously tracked files, or inspect file content.

`scripts/check_repository.py` checks tracked files for prohibited paths/extensions,
symlink files, the reference archive hash and a limited set of credential formats.
SK-1 permits one repository discovery pointer, `.agents/skills -> ../skills`.
The guard checks its exact Git-index mode and target as well as its working-tree
target, requires real in-repository parent/target directories and scans the
canonical skill files normally. Other `.agents` paths and symlinks remain denied.
Content checks cover both index and working-tree bytes. For other tracked files,
the local symlink check applies to the working tree. A staged symlink replaced locally by a regular
file is rejected on the CI checkout, not by that local mode check.
It emits filenames only, never matching secret values. It is not a comprehensive
DLP system and cannot detect arbitrary PII, every secret format, or mistakes hidden
in otherwise allowed text. Review staged content before committing or publishing.

P1/P2A fixtures are labeled synthetic strings in Python tests. Tests create temporary
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
executed. P2A follows literal includes only through explicitly authorized file
identities and declared dependency links; it cannot expand source scope.

Artifacts contain declared identifiers, paths relative to roots, hashes, supplied
structured graph facts and code-only diagnostics; full source/log excerpts and
absolute source roots are excluded. Arbitrary identifiers can still encode private
information. `synthetic: true` is an authorization declaration, not an automated
PII detector. P2A artifacts additionally contain original token/numeric lexemes,
formulas, identifiers, state facts and fixed-layout observation cells. Those fields
can reveal source information: **do not provide real data to P1 or P2A**. Publication is not a
redaction or anonymization guarantee.

P2A's public fixture author and reviewer are separate development agents in the
same environment, not a protected-gold boundary. The deterministic source checker
shares reconstruction code. No public test result establishes evaluator isolation
or independent semantic reliability. P2B must provision and test those controls;
semantic acceptance stays BLOCKED. No model provider or outbound source channel
is configured by P2A.

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

## CP1 capability boundary

Shared serializers, error types and contract/identity logic import without the
POSIX filesystem backend. Windows and unrecognized platforms are denied; there
is no unsafe open/pathlib/lock-free fallback or user-selectable backend override.
Evidence workflows check capabilities before opening even their scope manifest.
Public I/O helpers and retained attempt/store methods also check the boundary.
Local downstream checkout checks deny unsupported traversal before resolving
paths or running Git. Trusted bundled schema/baseline reads remain available.

On macOS/Linux the selector checks required open flags, callables, descriptor and
no-follow support, and actual fcntl locking members. These checks establish API
availability only: original POSIX traversal, permissions, mutation detection,
locking and publication checks still run. CP1 does not resolve the physical alias
or post-seal durability questions recorded in the portability plan, qualify a
new filesystem, or strengthen the existing trusted-owner threat model.

Native Windows execution is not verified by simulated platform tests. Windows
source authorization, handle traversal, ACLs, locking and publication remain
unimplemented. Qualification is BLOCKED without an approved Windows interpreter
and dependencies; do not relax the lock or install them without approval.

## CP2 declaration boundary

The separately versioned local authorization envelope is input data, not an
authenticated approval, physical authorization or capability token. Its public
validator performs pure syntax/reference checks and reads trusted bundled schemas
only. Native paths are never resolved/opened, and no existing evidence workflow
consumes the envelope. Validated Windows declarations still encounter the same
CP1 BLOCKED boundary before source reads or store creation.

Case/Unicode comparison screens detect some string aliases; they cannot establish
physical identity, volume type, permissions, reparse/symlink absence, mapped-drive
or mount disjointness. Those guarantees require separately approved future work.
No human identity, signature, timestamp or approval is invented; caller metadata
remains DECLARED with human approval NOT_VERIFIED.

Local paths and caller metadata are excluded by an explicit versioned projection
from canonical graph/source identities and never added to sealed artifacts. Keep
actual envelopes outside Git (the existing ignored `local/` is suitable). CP2 uses
only synthetic declarations in public tests. See [CP2 design](https://github.com/keshavnath1/sas-reverse-engineering/blob/eb9794167339d1991800c290a2b24ac10a57edf8/docs/CP2_DESIGN.md)
for the deliberately restricted path profile and proof limits. Native Windows
qualification and independent semantic acceptance remain BLOCKED.

## CP3A additive POSIX boundary

The separately invoked [CP3A API](https://github.com/keshavnath1/sas-reverse-engineering/blob/eb9794167339d1991800c290a2b24ac10a57edf8/docs/CP3A_DESIGN.md) consumes a CP2 envelope
only with an independent exact local inspection policy. It confines roots/store
inspection beneath an existing dedicated owned anchor on a qualified filesystem,
retains and rechecks descriptor/name identities, rejects unexpected directories
before descent, and obtains all read handles before source content. It creates
no output. Existing commands/publishers and their persisted failure timing remain
unchanged; CP3A success does not authorize publication or later reuse.

Synthetic/quiescent scope and trusted writers, ACL principals, administrators and
mount namespace are explicit preconditions. Ownership/mode checks are not a full
ACL audit or authentication service. Repeated metadata/byte checks are not an
atomic hostile-writer snapshot; unavailable required guarantees block. Linux
procfs metadata inspection is fixed-path/no-follow/bounded and distinct from source
content. Native paths/IDs and policy data stay outside portable artifacts/hashes.

Windows remains BLOCKED before caller-path I/O. No native Windows access,
publication redesign, dependency/lock change, private intake or new approval
claim is introduced. [Validation](https://github.com/keshavnath1/sas-reverse-engineering/blob/eb9794167339d1991800c290a2b24ac10a57edf8/docs/CP3A_VALIDATION.md) records actual native
tests separately from simulated cases, in-process observers and unresolved
independent security/native-tracing qualification.

## CP3B blocked Windows protocol

[CP3B](https://github.com/keshavnath1/sas-reverse-engineering/blob/eb9794167339d1991800c290a2b24ac10a57edf8/docs/CP3B_DESIGN.md) adds private existing-only relative-handle primitives
and a reader protocol. It does not provide an approved physical-volume bootstrap,
locality proof or public Windows source access. The existing public capability
gate denies before caller-path inspection/DLL loading/content/output; no override
is exposed. The new status field distinguishes this partial implementation.

Only simulated/unit tests exercise Windows operations. Named native host owner,
independent security reviewer, observer and approved offline runtime are OPEN.
No native Windows qualification, ACL isolation, hostile-writer snapshot or bounded
kernel-call cancellation claim follows from test results. Full Windows evidence
commands and publication remain BLOCKED. Earlier 'unimplemented Windows reader'
statements above describe the historical boundary; current public access remains
unavailable despite the private CP3B implementation.

The private subset requires a preexisting disjoint store location for metadata
inspection; absent/aliased prefixes block rather than asserting unsafe absence.
No store is created. All source read handles must be acquired before content;
original bytes remain unchanged and cleanup uncertainty prevents a successful
result. No frozen evidence schema, canonical ID, POSIX behavior or history changes.

## CP3D private metadata subset

[CP3D](https://github.com/keshavnath1/sas-reverse-engineering/blob/eb9794167339d1991800c290a2b24ac10a57edf8/docs/CP3D_DESIGN.md) adds typed external comparison records and a private
metadata-only bootstrap/absence protocol. It is exercised by independent memory
fixtures only, not wired into the public gate or CP3B reader. References and
matching object IDs do not authenticate an inspection grant, prove physical
backing or approve a host. Local identities never enter portable evidence hashes.

The new native adapter binds only bounded, explicitly named DOS mapping queries;
even these have not been executed on an approved Windows host. It binds no Nt
filesystem call. Context/root/lookup/metadata/close methods unconditionally BLOCK
before filesystem access: native authority, reparse/alias and completion guarantees
are unresolved. There is no qualification boolean, source read or creation method.

Only a completed successful lookup transfers a handle to the simulated protocol.
An inconsistent pending/failed result leaves resources with its adapter; the
protocol cannot cancel, close or free them safely. Native acquisition is disabled
so this is not a claim to implement native pending-I/O cleanup. Absence observations
are temporary, under quiescent trusted writers, and never reservations or creation
permissions. No snapshot/ABA, ACL isolation or native certification is claimed.
All public Windows access remains BLOCKED/exit 2. See
[actual checks and unresolved gates](https://github.com/keshavnath1/sas-reverse-engineering/blob/eb9794167339d1991800c290a2b24ac10a57edf8/docs/CP3D_VALIDATION.md).
