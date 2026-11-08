# CP3C Windows volume bootstrap security design

Reviewed baseline: `a29af0ec024945b15d31435e7041d45e92278c68`.
CP3B is accepted only within its limited simulated-test scope. CP3C authorizes
**planning and security review only**. Everything described as a protocol below
is PROPOSED, not implemented, approved for execution or natively qualified.
Public Windows preflight, absent-store acceptance and all Windows evidence commands
remain BLOCKED. No CP4 publication, locks or output-store creation is designed here.

## Evidence and conclusion

OBSERVED: [CP3B design](CP3B_DESIGN.md), [validation](CP3B_VALIDATION.md),
[CP3 readiness](CP3_READINESS.md), [security test plan](CP3_SECURITY_TEST_PLAN.md),
current `_windows_native.py`, `_windows_preflight.py`, `platform_io.py`, CP2 path/
identity interfaces and repository security/approval records were inspected at
this baseline. The private adapter has no bootstrap/locality query or typed
absence result. It accepts an internal retained root only; public entry denies
Windows before supplied-path access. Its tests do not execute Windows APIs.

PROPOSED conclusion: a bootstrap can be considered only when **three independent
conditions** hold: authentic local inspection authority, a retained object matching
an independently approved host/storage binding, and qualified native API behavior.
Neither a declaration nor a successful open establishes all three. The design is
conditional on trusted Windows/kernel/storage administrators and quiescent approved
writers; it does not defeat a hostile kernel, cloned-device deception or arbitrary
namespace writers. Unavailable required assurance means BLOCKED, not a weaker open.

The missing named owners, actual host and approval mechanism are listed in
[the qualification plan](CP3C_QUALIFICATION_PLAN.md) and CP3C-D01–D08 in
[the decision ledger](OPEN_DECISIONS.md). They remain OPEN.

## Initial authority and trust boundary

Before any candidate-root lookup, require a separately supplied local inspection
grant whose provenance is independently accepted by the host owner/reviewer. Its
proposed fields are a checklist, **not a new implemented schema**:

- Actual host and ordinary-user security context; reviewed code/package identity;
  approval reference as supplied, validity/revocation policy and accountable owner.
- Independently recorded approved volume/backing inventory and expected root/volume
  identity observations, with their collection method, age and limits.
- Exactly one allowed root-only metadata candidate and specifically allowed DOS
  mapping queries; the dedicated anchor and authorized ancestor components.
- Exact CP2 workspace/run/scope hash and source roots; explicit store-target metadata
  inspection scope, including any missing suffix. CP2 has no store field.
- Synthetic-only/quiescent source and namespace-writer policy, permitted ACL/filter/
  storage configuration, bounds and stop rules.

The grant's storage, authenticity, ACL protection, loader, revocation and issuer
are OPEN. Do not create a default grant, trust its self-declared owner, promote
CP2 `declared_by`/`approval_reference`, or copy input declarations into an approval.
A proposed protected host-local record may supply context, but copying its bytes
must not grant access. No signer, signature, date or human decision is invented.
An OS access check remains necessary and distinct from organizational permission.

Candidate root access is metadata access and needs authority **before** the first
open. Identity cannot be checked without opening an object, so the permitted
root-only candidate set must be authorized independently. Do not search all drives
or inspect arbitrary rejected paths. There is no requirement for a service,
administrator token, raw-disk access, Git, WSL, Docker, cloud or AI provider during
ordinary execution. If the approved proof requires privileges unavailable to the
ordinary process, provision evidence separately or remain BLOCKED; never elevate
or enable backup/restore privileges automatically.

## Volume locator versus retained-object proof

| Observation | Permitted use | Insufficient claim |
|---|---|---|
| Drive letter / DOS-device mapping | Detect declared mapping, substitutions and changes in the actual logon context | Not stable volume identity or authorization |
| Volume GUID or native device name | An explicitly authorized root-only locator candidate | Not physical identity; multiple names and mutable mappings exist |
| FILE_ID_INFO serial and 128-bit root ID | Compare retained objects on the approved volume/session | Not a signature, globally unique hardware identity or clone-proof attestation |
| NTFS name, component/ACL capability, device type/characteristics | Necessary filesystem/locality restrictions | Not independent physical-backing proof or writer exclusion |
| Host storage inventory and approval | Establish approved backing/custody under the stated trusted-host model | Not sufficient if stale, unauthenticated, ambiguous or inconsistent with handles |
| Repeated lookup/metadata observations | Detect relevant changes and invalidate the run | Not atomic namespace reservation or hostile-writer snapshot |

Microsoft documents current and prior DOS mappings and local/global namespaces;
these observations must be interpreted in the process's actual security context.
Query only the approved name, parse bounded MULTI_SZ, and distinguish the first
current mapping from undeleted prior mappings. Repeated equality does not lock a
mapping or rule out an ABA change. [QueryDosDeviceW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-querydosdevicew),
[DOS namespaces](https://learn.microsoft.com/en-us/windows-hardware/drivers/kernel/local-and-global-ms-dos-device-names).
A volume can have multiple GUID names; a GUID spelling alone cannot be the trust
anchor. [Volume naming](https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-volume).

### Conditional retained-handle bootstrap

1. **B0, pure gate:** validate/detach CP2 declarations and the independently scoped
   policy. Check implementation/qualification availability without accessing input
   paths. Missing approval, host tuple or capability stops here. Current code stops
   here for all public Windows access; this design does not alter it.
2. **B1, authorized mapping observations:** inspect only approved DOS mappings and
   correlate them with independently provisioned storage expectations. Reject SUBST,
   network/redirected prefixes, unexpected device targets and unresolved aliases.
   Multiple legitimate GUID names are not themselves multiple physical volumes;
   only an explicitly reviewed unambiguous binding can be selected. No guess or
   first-match scan is permitted.
3. **B2, one candidate root open:** proposed private bootstrap opens one exact,
   independently approved filesystem-root locator, existing-only and metadata-only.
   Candidate is `NtCreateFile` with `RootDirectory=NULL`, a root-only native object
   name, directory semantics and the independently qualified reparse-refusal flags.
   No user-supplied source suffix is appended. Caller CP2 paths still cannot contain
   device/extended namespaces. No arbitrary GLOBALROOT override, raw volume/disk
   handle or alternate fallback is exposed. Native object-manager resolution and
   filesystem reparse resolution are different; a filesystem flag is not assumed
   to secure the object namespace. The precise locator/flag protocol remains OPEN.
4. **B3, verify that same handle:** establish actual directory type and independently
   approved volume-root object identity. There is no generic directory-is-volume-root
   type bit; directory status or a trailing slash is insufficient. A qualified
   root-name query is corroboration only. Verify
   noninheritance, supported attributes, absence of reparse/recall/offline behavior,
   full root identity and approved NTFS properties. Compare with independently
   approved host-session observations. Keep DWORD volume serial and FILE_ID_INFO's
   64-bit serial separate; no undocumented truncation/equality rule. Volume labels,
   root names and formatted serials cannot authenticate physical storage.
5. **B4, locality and backing:** add a separately reviewed handle-bound query such
   as `NtQueryVolumeInformationFile(FileFsDeviceInformation)`. Check exact ABI,
   successful completion/result byte count and qualified device characteristics.
   Reject remote/virtual/removable/WebDAV/redirected or unknown arrangements.
   An unsupported query, invalid/unsupported required value, or failed remote-protocol
   query is not evidence of locality. A zero-valued bitmask may be legitimate but
   is not sufficient locality evidence; qualify each field's meaning rather than
   rejecting all zeros generically. Correlate with approved backing inventory;
   local-looking block storage alone cannot exclude SAN/VHD/clone arrangements.
   Any unresolved inconsistency or duplicate physical identity blocks the run.
6. **B5, retain and bind:** retain the verified root throughout the single session.
   Translate approved CP2 drive-root declarations to its relative component list
   only after mapping/identity agreement; do not silently reinterpret an alias.
   Traverse each ancestor and scoped root by a single literal component relative
   to retained handles. Inspect before descent; reject every filesystem reparse,
   mount crossing, unsupported object or changed volume. Do not enumerate unrelated
   ancestors. Exact ancestor-name/alias proof must be qualified, not inferred from
   Python casefold or a final-path string.
7. **B6, recheck and release:** repeat required mapping, root/parent/name/volume and
   scope observations before Q2R/content and at final completion. Any change or
   uncertainty invalidates the session; do not rebind or retry with wider access.
   Attempt release of every owned resource and block success on uncertainty.

This uses a retained directory handle as the operational anchor after B3/B4, not
the locator text. It deliberately leaves the initial independent binding authority
and physical-backing proof as prerequisites. A different volume with copied IDs
must not pass merely because the tuple matches. If the approved host inventory and
namespace policy cannot exclude that ambiguity, there is no accepted bootstrap.

API evidence: [NtCreateFile](https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntcreatefile)
describes absolute/relative opens; its documented flags still need the review below.
[Volume information](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getvolumeinformationbyhandlew)
reports filesystem/formatted-volume metadata. The proposed
[volume query](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntqueryvolumeinformationfile)
accepts directory handles and documents user-mode `Nt` use and output lengths;
it also warns that unsupported members can be zero. Its driver-oriented page is
not proof of an available/qualified user-mode export/ABI on this host.
[Device information](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/ns-wdm-_file_fs_device_information)
and [device characteristics](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-fscc/616b66d5-b335-4e1c-8f87-b4a55e8d3e4a)
support candidate restrictions, not hardware attestation. All new calls are design
proposals only; none was added or invoked in CP3C.

Proposed new bootstrap ceilings: one candidate root open, at most eight explicitly
named mapping observations per session, each with a fixed 64 KiB buffer and at most
128 decoded MULTI_SZ entries; no unbounded retries. These are review proposals,
not measurements or existing constants. Preserve CP3B's 4,096 retained handles,
64 bootstrap components, depth 32, 1,000 files/1,000 scoped directories, 8 MiB/file,
64 MiB aggregate and bounded enumeration. Exact native deadlines/completion policy
remain OPEN; a finite call count is not a wall-clock cancellation guarantee.

## Proposed absent-store proof

OBSERVED: CP3B correctly returns `CP3B_STORE_ABSENCE_UNPROVEN` for missing exact
long names. The adapter currently collapses open failures into a generic blocked
code. Neither that error nor complete long-name enumeration proves absence under
NTFS aliases. Preserve this behavior until separately authorized implementation
and actual native evidence establish the following narrower protocol.

**A0 — authorize and bind existing parents.** The store request explicitly grants
metadata inspection of its parent chain/candidate components, never creation.
Starting from the retained approved root, validate each existing component's exact
long name, object identity, volume, directory type and parent relationship. Unexpected
or inaccessible parents, reparse objects, unsupported case settings and changed
bindings block. An existing store uses the current two-direction ancestry check.

**A1 — qualify native lookup semantics.** Initial profile accepts only ordinary
case-insensitive parent directories with a reviewed handle query establishing that
state. Unknown, enabled or changing per-directory case-sensitive flags block;
never change the setting. `FileCaseSensitiveInfo` and
[case-sensitive information](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/ns-ntifs-_file_case_sensitive_information)
are candidate contracts; the Win32 versus NT information-class values are different
and must not be mixed. [Win32 information classes](https://learn.microsoft.com/en-us/windows/win32/api/minwinbase/ne-minwinbase-file_info_by_handle_class).
NFC/casefold screening is rejection only. NTFS collation/short-name behavior must
be tested directly; extended enumeration has no short-name field.

**A2 — probe one literal component.** Proposed new private metadata lookup uses
retained parent `RootDirectory`, `FILE_OPEN`, `OBJ_CASE_INSENSITIVE`, the qualified
`FILE_OPEN_REPARSE_POINT` behavior and minimum metadata/synchronization rights.
It must not constrain the result to either a directory or a nondirectory: an
existing file or wrong-type alias is a collision, not absence. A returned handle
means PRESENT; inspect/release it and either validate the authorized exact object
or reject the alias/type. No create disposition, fallback spelling or weak retry.

**A3 — preserve typed native outcomes.** Only independently qualified
`STATUS_OBJECT_NAME_NOT_FOUND` (`0xC0000034`) from that exact single-component
lookup is a candidate absence observation. Access denial, sharing failure,
`STATUS_OBJECT_PATH_NOT_FOUND`, `STATUS_NO_SUCH_FILE`, invalid name, type mismatch,
reparse, pending, partial or unknown outcomes remain BLOCKED. The
[NTSTATUS catalog](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-erref/596a1078-e883-4972-9bbc-49e60bebca55)
distinguishes errors; it does not prove this absence rule. Retain raw typed status
internally; do not infer absence from `FileNotFoundError`/Win32 error translation.
The code implementing this distinction does not exist yet.

**A4 — bind the first missing name only.** Stop at the first missing component;
retain its verified parent, literal basename, untouched suffix and session epoch
in memory. Do not descend into nonexistent directories. Reconcile complete bounded
membership only within explicitly authorized listing scope, native lookup and
fresh source bindings. A DOS alias hit or differing long name is not missing.
`GetShortPathNameW` can return the original long name when no short name exists;
conversion success/failure is not an alias-absence proof.
[Short-path API](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getshortpathnamew).
CP2 rejects typical `~` aliases syntactically; that does not establish absence of
all possible short names, alternate spellings or native namespace collisions.

**A5 — prove the right disjointness relation.** Deny if the retained nearest parent
is a source root or below one. A shared ancestor is legitimate: `anchor/source`
and a missing `anchor/new-store` may be siblings. Do not reject merely because
`anchor` is also in the source's ancestry. Native absence plus fresh retained source
bindings must establish that the first missing child is not any existing source
ancestor. Unknown alias/ancestry/mapping behavior blocks.

**A6 — make validity temporal.** Recheck parent identity/name bindings, relevant
membership/case state and the exact negative lookup before any content and at
final completion. Parent replacement, new child/alias, volume change or uncertain
quiescence invalidates the whole session. Repeated checks cannot detect every
create/remove ABA or prevent insertion immediately after the last check. If
hostile concurrent namespace writers must be tolerated, this protocol is insufficient
and stays BLOCKED. Under an explicitly approved quiescent model it is only a
session-scoped observation, never a reservation, capability receipt or permission
to create. CP4 must separately solve creation-time authorization/atomicity; no CP4
mechanism is implemented or selected here.

## Native adapter security review

The following distinguishes observed CP3B code from required future proof. No
finding below was silently fixed in this planning checkpoint.

| Area | Observed / primary evidence | Qualification obligation or unresolved risk |
|---|---|---|
| NtCreateFile options | Literal relative names, existing-only, fixed rights, CASE_INSENSITIVE and OPEN_REPARSE_POINT; no OBJ_DONT_REPARSE reliance | Function's directory-compatible options omit OPEN_REPARSE_POINT despite separately documenting it. Resolve via authoritative contract/SDK review and native negative cases; never drop reparse refusal |
| Enumeration | 64 KiB buffers, 128 calls, 2,002 records including validated dots; hidden/system entries retained | Verify real restart/continuation/termination, layouts and driver behavior. [Extended record page](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_id_extd_dir_info) says no supported client while [query page](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getfileinformationbyhandleex) lists classes and warns of variation; Windows 11 applicability remains OPEN |
| Alias/ID joins | Extended records carry 128-bit IDs, no short names | A supplemental [short-name record](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_id_both_dir_info) has a different 64-bit ID layout; no truncation/equality assumption. Qualify native lookup instead of declaring long-name absence sufficient |
| ReadFile offsets | Fixed byte buffers and explicit OVERLAPPED offsets on synchronous handles | [ReadFile](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-readfile) documents this pattern. Actual multi-chunk offsets, EOF/rewind and completion still need native controls |
| ACLs and sharing | No READ_CONTROL/DACL inspection; directory share-all, files share-read | External trusted-writer/ACL policy is necessary. Sharing does not exclude all attributes or surviving mapped views. Exact leaf-data denial must permit metadata/SYNCHRONIZE so Q2R is genuinely tested. [Access rights](https://learn.microsoft.com/en-us/windows/win32/fileio/file-security-and-access-rights), [mapping lifetime](https://learn.microsoft.com/en-us/windows/win32/memory/closing-a-file-mapping-object) |
| Handle ownership | Explicit widths, noninheritance checks, one close attempt, cleanup on returned-handle failure/cancellation | Native acquisition/close/object trace required; uncertain close prevents success and cannot justify retry of a reused number. [CloseHandle](https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-closehandle) |
| Pending I/O and cancellation | Current adapter rejects unexpected statuses; unit exceptions test cleanup after control returns | A BLOCKED return/CloseHandle is not proof pending native I/O has completed. Stack/buffer/IO-status/OVERLAPPED lifetime must extend through actual completion; establish synchronous completion for approved calls or separately design safe completion/cancellation before activation. [CancelSynchronousIo](https://learn.microsoft.com/en-us/windows/win32/api/ioapiset/nf-ioapiset-cancelsynchronousio) does not wait for completion. Native deadline and cleanup guarantees remain BLOCKED |

No simulation resolves these native assumptions. Any future ABI, status handling,
lookup or lifetime change requires explicit implementation approval and new tests;
CP3C does not patch CP3B or expose a test-only bypass through the public API.

## Compatibility and stop boundary

Reuse CP2 logical scope/projection and CP3A policy/preflight concepts. Bootstrap
and absence observations are transient local session data outside graph hashes,
source IDs, evidence schemas and sealed artifacts. No second canonical model or
persistent authorization token is introduced. Preserve original byte handling,
all 596 tests, POSIX behavior, historical attempts and the Agent-mastery pin.
DRAFT, UNVERIFIABLE, independent semantic acceptance BLOCKED and benchmarks NOT_RUN
remain unchanged. Full Windows evidence commands remain BLOCKED/exit 2 even if a
future private reader qualifies; CP4 and any public-reader activation are separate
approvals. Stop after these planning documents for review.
