# CP3B Windows read-only protocol design

Approved baseline: `f841ca25d511230d77ab1c3eded3f59602a79f5d`.
The user approved CP3B implementation and synthetic tests, with an explicit
instruction to implement only a defensible subset if critical native assumptions
cannot be established. This design records that subset. It does **not** enable
Windows source access through the public API. Native qualification is BLOCKED.

## Implemented boundary and missing prerequisite

Observed baseline: CP2 validates declarations without physical authority; CP3A
uses a separate `LocalInspectionPolicy`, retained POSIX descriptors and a single-use
preflight. CP1 blocks full Windows evidence commands before scope-file access.
Those interfaces, identity rules, contracts and persistence behavior are preserved.

Implemented: a private Windows ABI adapter and retained-handle reader protocol,
using the existing CP2 logical declarations and CP3A policy fields. There is no
second evidence model, native-ID artifact, authorization receipt or publication
method. Source bytes are returned unchanged only after complete checks and cleanup.
The new pure `preflight_capabilities()` and additive CLI status field describe the
private implementation and its missing prerequisites separately from full evidence.

**Unimplemented prerequisite:** securely obtaining a retained volume-root directory
handle that is bound to an independently approved physical local NTFS volume.
Drive letters, volume GUID strings, formatted serials, `FILE_TYPE_DISK` and matching
file IDs do not establish that authorization/locality guarantee. No approved real
Windows host, dependency environment or native security observer was supplied.
Consequently `open_preflight` still denies Windows with
`FILESYSTEM_CAPABILITY_UNAVAILABLE`, gate BLOCKED; evidence CLI exit code remains
2. This occurs before policy/path inspection, native DLL loading, source content,
or store creation. There is no configuration, environment variable, caller flag
or public handle-injection API to bypass the gate. Private modules are trusted
implementation code, not a sandbox against callers who modify/import internals.

The internal session owns a retained volume-root handle supplied by a future
qualified bootstrap. Today only the independent memory-only fake invokes it.
It does not itself authenticate that handle, prove local backing or qualify NTFS.
This is a functional limitation, not a native feature declared complete but untested.

## Native adapter and resource ownership

`_windows_native.py` imports without loading a DLL. Constructing its private
adapter requires actual `win32`/`nt`, x64, reported kernel major 10/build at least
22000 and supported ABI. That version screen is not a Windows client-edition or
host qualification check; only Windows 11 x64 is the proposed qualification target.
Fixed-width ctypes types explicitly implement LLP64 layouts; lengths, offsets,
alignments and little-endian pointer widths are checked. DLL lookup is restricted
to System32. No extra package, privileged helper, shell command or network service
is used. Constructor availability is never platform qualification.

| Operation | Candidate implementation and enforced bounds |
|---|---|
| Child acquisition | `NtCreateFile`, one validated literal component, retained parent handle, existing-only `FILE_OPEN`; directory/non-directory and synchronous options plus `FILE_OPEN_REPARSE_POINT`. No arbitrary pathname, create, write, delete, backup or fallback open |
| Rights | Metadata files: READ_ATTRIBUTES/SYNCHRONIZE only; directories additionally LIST_DIRECTORY/TRAVERSE. Data files add READ_DATA only after complete metadata preflight. Directory sharing permits read/write/delete under the explicit quiescent model; files share READ only, with no weaker retry |
| Handle/object checks | `GetFileType`, `GetHandleInformation`, attribute/tag, basic/standard and FILE_ID_INFO queries. Reject nondisk, inheritable/protected handles, every reparse object, device/virtual/offline/recall attributes, delete-pending, inconsistent metadata, invalid IDs and file links other than one |
| Volume checks | `GetVolumeInformationByHandleW`: exact NTFS, nonzero serial, component limit 255 and persistent ACL capability; repeat full tuple and 64-bit identity serial checks. DWORD volume serial and FILE_ID_INFO's 64-bit serial are stored/compared independently, never equated or treated as hardware identity |
| Enumeration | Handle-relative extended directory query, 64 KiB initialized buffer, maximum 128 calls and 2,002 records including structural dot entries. Validate offsets, alignment, UTF-16 lengths, progress, duplicate names, size and 128-bit IDs. Only validated `.`/`..` are excluded; hidden/system names remain |
| Read | `ReadFile` with explicit OVERLAPPED offsets on synchronous handles, at most 64 KiB per call; byte buffers only. Metadata handles have no read-offset registration. Rewind changes the internal offset, not a source path |
| Close | Owned returned handles close once; failed/informational opens, cancellation after a returned handle, reused handle numbers and inspection failures release ownership. Uncertain close blocks success; the session attempts every other owned handle before returning an error |

Finite memory/call/handle bounds are not OS-call deadlines. A synchronous native
call can block in the kernel; immediate cancellation and trace-complete cleanup
under actual Windows failures remain unqualified. No guarantee is fabricated.

Primary API evidence reviewed: [NtCreateFile](https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntcreatefile),
[handle metadata](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getfileinformationbyhandleex),
[directory layout](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_id_extd_dir_info),
[volume query](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getvolumeinformationbyhandlew),
[ReadFile](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-readfile),
[handle flags](https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-gethandleinformation)
and [CloseHandle](https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-closehandle).
The documented synchronous ReadFile/OVERLAPPED offset mechanism supports this
candidate implementation. Documentation is not an observed native security result.

Native-contract limits remain explicit: function-specific NtCreateFile attributes
support zero/CASE_INSENSITIVE, so no reliance on OBJ_DONT_REPARSE is introduced.
Its directory-compatible option list omits OPEN_REPARSE_POINT despite documenting
that flag separately; the combination needs independent native review. Extended
directory-query support varies by OS/driver and must be observed. Reparse/hydration
side effects, ACL enforcement and sharing semantics remain unexecuted obligations.
Undefined directory ReparsePointTag data is normalized to zero only when the
reparse attribute is absent; every actual reparse object is rejected.

## Authorization and reader ordering

The pure `_request_windows` validates the existing CP2 contract, detaches canonical
JSON, and compares exact workspace/run/scope hash, roots and an independent
`LocalInspectionPolicy`. It requires `QUIESCENT_SYNTHETIC_TRUSTED_WRITERS`, a strict
source-descendant anchor, bounded path depth, and a store inside that anchor.
A policy is trusted-caller invocation data, never fabricated human approval.
CP2 approval metadata stays DECLARED/NOT_VERIFIED. Public access is blocked even
if these pure checks succeed.

The private protocol follows the CP3 stages:

1. Q0: validate/detach declarations and policy before native metadata inspection.
2. Q1: traverse literal ancestor components through retained directory handles;
   never enumerate unrelated ancestor siblings. Within the scoped anchor, retain
   roots and the existing store ancestry. Compare endpoint/ancestry identities in
   both directions; genuine siblings may share the volume/anchor.
3. Q2: compare every source directory's complete names against the declaration
   prefix tree before descending. Reject unexpected entries, ambiguous name
   spellings, nonregular files, hardlinks, aliases, unsupported volume observations
   and incomplete membership. Retain every metadata handle and recheck bindings.
4. Q2R: acquire every required data handle relative to the verified parent; compare
   complete original metadata/identity. No content read is possible before all
   handles pass and the global recheck completes.
5. Q3: read retained handles in bounded chunks; recheck all bindings/membership,
   metadata and volumes around reads; perform a second byte/hash pass and final
   global checks. Return the complete mapping only if cleanup also succeeds.

Bootstrap-ancestor name binding is rechecked by temporary relative directory
handles, not whole-parent enumeration. Exact ancestor spelling and alternate
namespace aliases are not qualified: the unavailable bootstrap must resolve that
obligation before public activation. Scoped names must match complete enumerated
long names exactly; conservative NFC/casefold comparisons reject ambiguities and
never rewrite canonical identifiers or source bytes.

**Existing stores only in the private Windows subset.** Missing exact long names
do not prove namespace absence under NTFS collation/DOS aliases. An absent store
prefix therefore returns `CP3B_STORE_ABSENCE_UNPROVEN`/BLOCKED, with zero source
reads, and comparison aliases return `CP3B_NAME_AMBIGUOUS`. No target is created,
even on success. CP3A's supported absent-store behavior is unchanged. Supporting
Windows missing stores requires a separately reviewed native absence proof; it
cannot be enabled by ignoring a failed exact-name lookup.

Bounds: existing 1,000 files, 1,000 scoped directories, depth 32, 8 MiB/file and
64 MiB aggregate; 4,096 simultaneously retained handles and 64 bootstrap path
components. Native metadata/parser faults and unknown guarantees fail BLOCKED.
New security diagnostics are fixed `CP3B_*` codes, without paths or source text.
Malformed CP2 declarations retain their existing validation errors. Full-evidence
Windows capability reason/exit conventions remain unchanged for compatibility.

## Preservation and proof limits

Only a separate status field and capability reporter touch shared runtime code.
The POSIX reader/publisher, preflight entry point, v1/v2 schemas, CP2 schema and
projection, hash/identity algorithms, downstream pin and historical tests remain
byte-unchanged. No new sealed artifact format or local-root field is introduced.
Transient handle/volume IDs stay in process memory. Read-only results do not grant
publication, authenticated approval, semantic verification or reusable access.

All Windows tests in this checkpoint are explicitly **simulated/unit-only**.
Independent fixture authorship and an independent development audit reduce shared
implementation mistakes; they are not native Windows tests, an independent human
security sign-off, protected-gold evaluation or SAS semantic proof. Repeated reads
are mutation detection under quiescent/trusted writers, not an atomic snapshot:
preexisting writable mappings, ACL/attribute writers, administrators and final
race windows remain trust-model limits. Access-time effects are never restored.

CP3-R01/R02/R04/R05/R07/R08 and native parts of R03/R09 remain OPEN: named Windows
host owner, independent reviewer, physical bootstrap, writer/ACL policy, fixture
custody/observer, approved offline Windows environment and native diagnostic review.
[CP3 security test plan](CP3_SECURITY_TEST_PLAN.md) remains the native qualification
obligation. [Validation](CP3B_VALIDATION.md) distinguishes actual evidence from
unexecuted cases. DRAFT authority, UNVERIFIABLE verification, BLOCKED independent
semantic acceptance and NOT_RUN benchmarks are unchanged. Stop after CP3B; no
CP4, CP5, P2B or P3 is implemented or authorized here.
