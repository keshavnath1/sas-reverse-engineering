# CP3 native security test and qualification plan

Baseline: `fe3bbe98704fd33fb9516b53e8786e516dce9e1e`. Prepared 2026-11-05.
**PROPOSED, NOT EXECUTED.** No native harness or reader is implemented by this
checkpoint. All new security cases below are NOT_RUN; native Windows qualification
is BLOCKED. The [readiness design](CP3_READINESS.md) defines the proposed protocol
and its OPEN API, bootstrap, trust and compatibility decisions.

This document specifies future tests, not permission to run them. Only synthetic,
disposable fixtures in separately authorized locations may be used. Do not point
qualification at private intake, system directories, existing evidence stores or
Agent-mastery. Preserve semantic BLOCKED, verification UNVERIFIABLE, authority
DRAFT and benchmarks NOT_RUN regardless of security-test outcomes.

## Environments and ownership

| Environment | Proposed qualification subset | Evidence currently available | Required before native qualification |
|---|---|---|---|
| Windows | Windows 11 x64, one approved local fixed NTFS volume; ordinary unelevated account; Python 3.12; PowerShell 7 preferred | No native execution in this checkpoint; CP1 simulated denial and CP2 pure vectors are historical development evidence | Named host owner and independent security reviewer OPEN; exact OS/Python/PowerShell builds, filesystem settings, offline dependencies, volume bootstrap, fixture custodian and observation method OPEN |
| macOS | Native Apple Silicon first, exact supported macOS/APFS case configuration and bootstrap mount policy | Previously reported macOS regressions; current planning host details recorded in readiness checks | Named owner/reviewer, native alias/race fixtures, actual filesystem/ACL/writer policy and observation proof OPEN; Intel qualification separately OPEN |
| Linux | Existing supported native development/CI environment, exact filesystem/mount namespace recorded | Historical Linux regressions; any new hosted run must be reported separately | Native mount/alias qualification OPEN; no WSL/VM/cloud dependency for workstation use |

The lock currently covers the approved macOS ARM64 and manylinux x64 dependency
artifacts, not a Windows installation. Selecting a newer Python 3.12 patch or
adding Windows wheel hashes needs separate approval; no packages are installed
here. Missing environments or required fixtures are BLOCKED, never counted as
successful skipped tests. A Linux CI pass cannot qualify macOS or Windows.

## Test stages and independent observations

| Stage | Allowed access | Required negative evidence |
|---|---|---|
| Q0: pure declarations | Trusted bundled contracts; pure validation/projection | No access to any supplied source/root/store path; caller approval metadata grants nothing |
| Q1: authorized physical inspection | Only explicitly authorized ancestor/root metadata, directory names and declared file metadata, through retained handles | No source-file data rights/reads, no undeclared-directory descent, no create/write/delete |
| Q2: complete binding | Verify all roots/files, ownership, membership, physical identities/ancestry and store disjointness | No source bytes until every obligation is satisfied; no output store |
| Q2R: all-file read readiness | After Q2, acquire all read-only data handles through verified parents; check identities, rights and sharing conditions | No content read until every required handle succeeds; any failure closes all handles |
| Q3: read-only intake | Bounded data reads using the complete retained handle set; repeated state/membership/hash checks | No source mutation or output creation, including on success, exceptions and cancellation |

Directory listing and file data access share some native access-bit values; the
observer must classify the object type and operation. A successful metadata-only
open is not permission to read file data. The independent oracle must verify Q2
completion from the declared fixture and observed calls, not trust a candidate
"authorized" log marker. Q2R may request file-data rights only after Q2; it must
perform no data read until all files pass, including a denied last file.

For every native case, the fixture custodian must retain a pre-run and post-run
inventory of original bytes/SHA-256, exact names, object IDs, file lengths, link
counts, relevant modification/change times, modes/ACLs and expected ancestry.
The custodian reads fixtures through a separate oracle; attribute its events
separately from the process under test. Keep raw local paths, native IDs and traces
outside Git and portable evidence artifacts. Retention/access owner is OPEN.

Observe the process under test and children at the native I/O boundary, with
operation, handle/object type, requested rights, result, path/object identity and
ordering sufficient to distinguish metadata from file-data access. A reviewed
observer might use an enterprise-provisioned native trace facility; the
[Process Monitor documentation](https://learn.microsoft.com/en-us/sysinternals/downloads/procmon)
describes a Windows candidate, not an approved dependency or proof of coverage.
macOS/Linux observation mechanisms and their permission requirements remain OPEN.
No tracing driver, privileged tool or service is installed by this plan.

Validate the observer with an independently controlled read and create/write/delete
sequence in a **separate disposable control directory**, outside source roots and
the proposed store. Prove process attribution, access-mask interpretation, ordering
and no dropped events. Missing visibility => qualification BLOCKED. Unit spies and
backend logs complement this evidence; they cannot replace it. Retained trace
records must cover failures and cleanup, not just successful reads.

Two proofs are required together:

1. **Source preservation:** unchanged original bytes and directory membership,
   unchanged relevant security/identity metadata, and no application write/delete/
   ACL-change request. Reads can cause OS-managed access-time updates; do not claim
   all metadata is unchanged or restore timestamps/permissions to hide effects.
2. **No early store:** absent target before/after **and** zero create/write/delete
   attempts against it or its ancestors throughout CP3. Absence at the end alone
   misses create-and-delete; matching bytes alone misses write-and-restore.

Deliberate adversarial writer changes belong to the fixture adversary, must be
attributed separately, and must cause denial/invalidation rather than being
misreported as application writes or a successful unchanged-source run.

## Adversarial matrix

Each row is a family requiring a frozen, finite case list and expected diagnostics
before implementation. Positive controls and every failure path are mandatory.
`DENY` means the reviewed FAIL/1 or BLOCKED/2 mapping in the readiness design;
freeze exact codes without changing legacy mappings. PASS below means a test
assertion passed, never SAS semantic acceptance. Every row is currently NOT_RUN.

| ID | Cases / platform | Required result and observable proof | Fixture setup |
|---|---|---|---|
| T01 | Invalid/empty CP2 scope, forged approval text, platform mismatch, missing inspection policy; all | Invalid contract fails purely. Syntactically valid caller approval text may validate but grants no authority: missing run policy or backend mismatch DENY before supplied-path I/O/store | Standard user, pure synthetic declarations |
| T02 | Missing API/member, wrong ABI/structure length, unsupported filesystem/identity query; Windows and POSIX candidates | BLOCKED, no unsafe open/pathlib fallback; no caller-path I/O for failed capability probe | Unit injection plus actual unavailable/unsupported native cases where approved |
| T03 | Normal single-link files; single-file and multi-file scopes, including zero-byte regular files where permitted; all | Original bytes/IDs agree with frozen CP2 rules; read-only positive control, all resources close, no store | Standard user |
| T04 | Root/ancestor/intermediate/leaf symlink; relative, absolute, dangling and escape targets; all | DENY before target descent/data; outside sentinel untouched and unread | POSIX standard user; Windows approved symlink privilege/Developer Mode fixture setup only |
| T05 | Junction, mounted folder, unknown reparse tag, cloud/offline placeholder; Windows | DENY with no resolution, hydration or outside data access; unknown query/tag BLOCKED | Junction may be standard-user; volume/tag/provider fixtures need separate provisioning |
| T06 | Hardlink inside/outside scope; second link added between metadata and read/recheck; all | Reject link count other than one; detect race or BLOCKED under unavailable assurance; no silent rebinding | Usually standard-user on owned same-volume fixtures; verify actual policy |
| T07 | Source-root equality/nesting through case, Unicode, Windows short/DOS aliases; source/store aliases; all | Physical equality/nesting DENY; canonical spelling unchanged. Unknown alias mechanism BLOCKED, not guessed normalization | Standard-user cases; 8.3 availability or namespace setup may need custodian |
| T08 | Genuine sibling roots/store with common volume or `/` ancestors; all | Positive control allowed through preflight; do not mistake a shared distant ancestor for overlap | Standard user |
| T09 | Store equals source, inside source, ancestor of source; absent store with missing suffix, parent swapped; all | DENY overlap in both directions; incomplete/unstable ancestry BLOCKED; no target/parent creation | Standard user with fixture-only race coordinator |
| T10 | Root or intermediate directory renamed/reparented/replaced after metadata binding; all | Retained identity/name relationships checked; deny stale/mismatched binding before source data; no path-only reopen | Standard user; deterministic barriers plus native races |
| T11 | Declared file replaced between metadata handle and data reopen; all | Compare handle identity before bytes; replacement sentinel never read | Standard user; deterministic barriers plus native races |
| T12 | Unexpected file, empty directory, hidden/system entry or nested unauthorized prefix; all | Bounded name observation only; no file data or descent into undeclared directory; no store | Standard user |
| T13 | Denied directory listing, denied leaf read (including the last file), missing required metadata/security rights; all | DENY/BLOCKED; no ACL repair, privilege escalation or widened scope; no other file's content read before every Q2R handle succeeds | Owned fixture ACLs normally standard user; second-account/protected ACL setup separate |
| T14 | Windows drive remap/SUBST, duplicate serial/ambiguous volume identity, unexpected mount crossing; Windows | BLOCKED if physical volume binding is ambiguous; drive/GUID strings and serial alone insufficient | Isolated custodian-provisioned cases; no system-drive manipulation |
| T15 | POSIX bind mount, alternate mount/namespace, macOS case-sensitive/insensitive APFS and normalization aliases | Identity plus qualified ancestry/mount policy; unknown transitions BLOCKED. Normal approved macOS bootstrap must retain positive control | Ordinary alias cases standard user; mount/volume/namespace setup often privileged |
| T16 | Append/truncate/rewrite/rename/delete during reads; same-length rewrite, restored mtime; all | Changes detected where promised, session invalidated, no success evidence/store; quantify uncovered windows | Standard-user adversary in authorized synthetic scope |
| T17 | Pre-existing writable handle, late writer and surviving writable mapped view; Windows | Sharing conflict or change DENY; no wider sharing retry. A view escaping detection exposes trust-model limit, not a passing snapshot guarantee | Standard-user adversary; exact mapped-view behavior requires native observation |
| T18 | Mutation after one file's final check and before overall completion; all | Demonstrate the stated quiescent-writer precondition and detection limits; arbitrary hostile snapshot claim forbidden | Standard-user adversary; required guarantee unresolved => BLOCKED |
| T19 | Nonregular/device/FIFO/socket objects; all applicable | DENY without data read, execution or hang; no device namespace escape | POSIX owned FIFO/socket standard-user; dangerous device fixtures excluded, use safe injection and separately reviewed native coverage |
| T20 | Limit−1/limit/limit+1 for file count, directory count, depth, bytes; malformed native directory record offsets/lengths/duplicates and no progress | Exact approved limits enforced; bounded handles/buffers/calls; cancellation closes all handles, no partial publication | Standard-user fixtures plus ABI decoder injections; injections not native-driver qualification |
| T21 | Exceptions/cancellation at every acquisition/read/recheck; child process inheritance; all | Handles closed once, no leaked inheritable resources, no writes/store; replayed/closed session denied | Standard user plus unit fault injection |
| T22 | UTF-8/declared encodings, BOM, LF/CRLF, non-ASCII names, case/Unicode variants, reordered declarations; all | Match applicable frozen CP2 vectors: reordered declarations/physical bindings preserve logical identity; changed bytes alter applicable source fingerprints/source-bound IDs, not scope hash; changed logical facts alter applicable logical IDs. No normalization of source or portable graph strings | Standard user, public synthetic literals only |
| T23 | Caller mutation of envelope after validation, forged native identity/handle or cached receipt | Detached/revalidated declarations; no caller-injected resource/approval authority or reuse across runs | Pure/unit tests plus native API-boundary tests |
| T24 | Full Windows inventory/seal/verify/P2A commands with CP4 absent | Existing BLOCKED/exit 2 before even scope-file access or store creation; reader test success cannot enable publisher | Native standard-user CLI tests with independently observed paths |
| T25 | Existing POSIX successful operations and historical failures/attempts | All 456 baseline tests and new approved tests pass; immutable hashes/bytes preserved. Explicit review of earlier failure timing before workflow integration | Approved development checkout; no historical artifacts edited |
| T26 | Offline installed package, no Git/cloud/AI/Docker/WSL, standard user | Pure commands and reviewed reader harness work with only approved runtime/dependencies; full Windows evidence still BLOCKED | Approved offline package/runtime provision; no installation authorized here |

For ACL cases, do not assume denying parent traversal prevents leaf access:
Windows normally permits bypass-traverse checking. Test denied leaf data and
directory-list rights directly. For privilege planning,
[CreateSymbolicLinkW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-createsymboliclinkw)
documents the unprivileged flag's Developer Mode dependency. Do not enable
Developer Mode, change security policy or elevate the application to satisfy tests.

## Privilege separation

- **Ordinary execution lane:** unelevated reader/CLI, owned synthetic directories,
  original-byte vectors, file replacements, limits, hardlinks where permitted,
  permission-denied fixtures and resource cleanup. Confirm actual effective token
  or UID and rights; do not infer them from an account label.
- **Fixture/observer provisioning lane:** host custodian may separately arrange
  symlinks, second accounts, restricted ACLs, alternate volumes, mounts, namespaces,
  reparse/provider fixtures or a privileged observer. Some junction/hardlink setup
  is possible without elevation; record actual requirements rather than imposing
  administrator privileges on every test.
- **Separation rule:** elevated setup/observation must not elevate the process under
  test. Record who created fixtures and who ran the application. Unavailable
  privileged setup leaves the affected required obligation BLOCKED. Never replace
  it with a mock and label native qualification complete.

No public instructions should create a device fixture, change machine policy,
remount a production volume or adjust an existing source ACL. Approve exact
disposable setup/cleanup scripts later; none is supplied or executed here.

## Proposed Windows qualification instructions

These instructions are a future checklist, not commands executed in this checkpoint.
Stop until CP3 implementation and CP3-R01–R10 decisions are reviewed as applicable.

1. Name the host owner, independent security reviewer and fixture custodian. Freeze
   the exact Windows 11 x64/NTFS tuple, source-writer policy, inspection scope,
   physical-volume expectation, trace coverage and stop criteria. Use a standard
   user token for application execution.
2. Obtain an independently hash-verified offline bundle and approved Python 3.12
   environment with Windows dependency artifacts explicitly approved. No Git is
   needed for ordinary execution. VS Code/Copilot are optional editors, not runtime
   authority or dependencies. Do not fetch/install packages, relax hash checking
   or change PowerShell execution policy as part of qualification.
3. In PowerShell, replace the illustrative path with the owner-approved interpreter.
   Record output and each native command's `$LASTEXITCODE` immediately. Expected
   exit code is 0 for the following currently existing pure commands:

   ```powershell
   $Cp3Python = 'C:\ApprovedRuntime\python.exe'
   $PSVersionTable.PSVersion
   & $Cp3Python -c "import platform,sys; print(sys.version); print(platform.platform()); print(platform.machine())"
   $LASTEXITCODE
   & $Cp3Python -m sas_re --help
   $LASTEXITCODE
   & $Cp3Python -m sas_re --version
   $LASTEXITCODE
   & $Cp3Python -m sas_re status
   $LASTEXITCODE
   & $Cp3Python -m unittest discover -s 'C:\ApprovedBundle\tests' -p 'test_authorization*.py' -v
   $LASTEXITCODE
   ```

   The current CP2 subset has 45 tests; freeze the approved bundle's manifest and
   count before a future run. `status` must retain DRAFT/semantic BLOCKED and full
   Windows evidence I/O BLOCKED. Pure success does not qualify physical access.
   Stop on unexpected failures/counts; do not delete tests or install missing
   modules to obtain a pass. A missing approved environment is BLOCKED.
4. Independently provision and inventory approved fixtures and the observer. Verify
   observation positive controls, then execute the future reviewed harness covering
   T01–T26 as applicable. **No CP3 harness command exists yet**; its exact command,
   test list, diagnostics, finite limits and output capture need implementation
   review before use. Do not invent a CLI or enable full evidence workflows.
5. Compare source preservation and no-store proofs, review all denials and missing
   cases, close resources, and retain the report outside source/store/Git under
   the approved retention policy. The independent reviewer must assess limits
   before any qualification acceptance. CP4 publication remains separately blocked.

Do not run the entire existing POSIX-oriented development suite on Windows and
silently exclude failures. The Windows native lane needs its own explicit,
reviewed obligation manifest; preserved POSIX regressions run in their existing
development environments.

## Proposed macOS qualification instructions

1. Freeze host owner/reviewer, exact macOS/Python architecture, actual APFS case
   configuration, permitted system/data volume bootstrap, writer/ACL policy,
   synthetic paths and observation mechanism. Existing regression success alone
   does not establish alias or mount security.
2. Use an already approved interpreter/offline bundle. Illustrative Unix-shell
   commands below are **not executed by this planning checkpoint**. Replace paths
   with approved locations; record each `$?` immediately and stop on nonzero:

   ```sh
   sw_vers
   echo $?
   uname -m
   echo $?
   CP3_PYTHON='/ApprovedRuntime/bin/python3.12'
   "$CP3_PYTHON" -c 'import platform,sys; print(sys.version); print(platform.platform()); print(platform.machine())'
   echo $?
   "$CP3_PYTHON" -m sas_re --help
   echo $?
   "$CP3_PYTHON" -m sas_re --version
   echo $?
   "$CP3_PYTHON" -m sas_re status
   echo $?
   "$CP3_PYTHON" -m unittest discover -s /ApprovedBundle/tests -p 'test_authorization*.py' -v
   echo $?
   ```

3. In a separately approved **development checkout**, preserve the existing
   `python -m unittest discover -s tests -v` suite (456 baseline tests), repository
   guard, fresh checkout/wheel checks and baseline/candidate sealed-byte comparison
   described in [CP2 validation](CP2_VALIDATION.md). Developer repository tests can
   use Git; Git must not become an ordinary installed-package prerequisite.
4. Execute the future reviewed native harness, with standard-user and separately
   provisioned mount/alias cases clearly distinguished. Require T08's normal-layout
   positive control. A blanket mount prohibition that breaks already qualified
   successful POSIX behavior is not an acceptable shortcut.
5. Compare independent inventories/traces and immutable artifact hashes. Record
   exactly which filesystem/architecture combinations were tested. APFS case
   variants and Intel hosts not exercised remain unqualified. Stop for review.

Linux is a development regression/optional native qualification lane, not a
mandatory workstation environment. Use the same evidence obligations with its
exact kernel/filesystem/mount namespace recorded; no container/WSL result may
stand in for native Windows/macOS evidence.

## Acceptance and report obligations for future implementation

- Named owner and independent reviewer; approved exact runtime/filesystem/API
  and trust policy. No required capability is inferred from a path string.
- Native positive controls and each required adversarial obligation executed with
  finite bounds and retained denials; missing environments, observer coverage or
  fixtures => BLOCKED. Report scheduled/executed/passed/failed/blocked counts.
- Zero unauthorized source-data access, source modification by the application,
  output creation or permission repair. Metadata inspection stays within the
  explicit inspection scope, and Q2/Q2R complete before any source data read.
- All 456 existing regressions preserved on supported POSIX environments, plus
  approved new tests. Any intended early-failure persistence change is separately
  reviewed, with historical append-only records and diagnostic conventions intact.
- Frozen v1/v2 schemas, CP2 envelope/projection, compatibility pin, source IDs and
  baseline successful sealed artifact bytes remain unchanged. New native identity
  fields stay transient. Windows reader tests compare byte/identity vectors;
  Windows sealed publication equivalence belongs to CP4, not this checkpoint.
- Full Windows evidence commands continue BLOCKED/2. No CP4 locks/publication,
  CP5 dependency expansion, private intake, SAS execution, P2B/P3 or downstream work.

The future report must include exact code/package hashes; OS/build, CPU, Python
and shell versions; filesystem/mount/ACL assumptions; application token/UID;
owner/reviewer/custodian; fixture and observer versions; commands and exit codes;
all failures/fixes/reruns; raw trace locations and retention; unchanged-source/store
proof; and unresolved exclusions. Report approval references as supplied evidence,
never invent names, signatures or dates. The report's sanitized summary can be
reviewed for Git; raw host-specific evidence stays outside portable artifacts.

Actual documentation-only checks for this checkpoint are recorded in
[CP3_READINESS.md](CP3_READINESS.md). No proposed command or test above is a
reported execution result.
