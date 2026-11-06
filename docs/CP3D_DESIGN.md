# CP3D private metadata bootstrap and absent-store design

Approved baseline: `5453a2598bd6da4ee695602f539f3961e70556b7`.
The user accepted CP3C planning and authorized a bounded implementation of the
defensible subset. This does not authorize native qualification, public Windows
source access, publication or deployment. [CP3C bootstrap design](CP3C_BOOTSTRAP_DESIGN.md),
[qualification plan](CP3C_QUALIFICATION_PLAN.md), [CP3B design](CP3B_DESIGN.md),
[security test plan](CP3_SECURITY_TEST_PLAN.md), [approvals](APPROVALS.md),
[security policy](../SECURITY.md) and [open decisions](OPEN_DECISIONS.md) remain
the governing context within that approved scope.

## Implemented subset and actual boundary

Two new private modules separate a pure metadata protocol from native primitives:

- [`_windows_bootstrap.py`](../src/sas_re/_windows_bootstrap.py) validates typed
  expectations, compares retained-object metadata, owns completed handles and
  produces transient candidate absence observations through a private adapter.
  Only simulated adapters currently implement this complete protocol.
- [`_windows_bootstrap_native.py`](../src/sas_re/_windows_bootstrap_native.py)
  provides strict wire decoders and a bounded `QueryDosDeviceW` binding. Import
  performs no DLL loading or filesystem access. The platform-specific constructor
  can bind only that named mapping function; it does not establish qualification.

OBSERVED implementation boundary: every native context, root-open, inspect,
volume, device, case-setting query, lookup and close entry unconditionally raises
`EvidenceError("CP3D_NATIVE_COMPLETION_UNQUALIFIED", "BLOCKED")` before evaluating
the supplied path/handle. There is no enabling flag, alternate opener or fallback.
The native adapter does not bind an Nt function, content reader, creator or closer.
The protocol calls `context()` first, so composing it with this native adapter
stops before a mapping query or root open.

The named `QueryDosDeviceW` binding is callable privately, but was **not executed
natively** and is **not qualified**. Direct use still requires independently
authorized named metadata inspection; availability is not permission. No public
entry point calls it. A pure decoder or passing simulation cannot confer native
bootstrap support. Current result and proof limits are recorded separately in
[CP3D validation](CP3D_VALIDATION.md).

## Expectations are comparison data

The frozen Python records are transient internal values, not a new public schema,
authorization envelope or evidence model:

| Record | Purpose | What it cannot establish |
|---|---|---|
| `HostContext` | Compare supplied host/token references with adapter observations | Authenticate the host, operating-system token or approving person |
| `HostVolumeExpectations` | Declare one metadata root locator, named DOS mapping, expected root object, volume/device fields and inspection/backing references | Issue an inspection grant, approve storage, establish provenance or defeat a cloned identity |
| `DirectoryExpectation` | Pair an exact component tuple with an expected retained directory identity | Grant access merely because a pathname or identity matches |
| `MetadataExpectations` | State the exact required directory-prefix set and nearest existing store parent | Grant arbitrary ancestor/sibling enumeration or creation rights |
| `AbsenceObservation` | Retain first-missing basename, parent identity and remaining suffix in memory | Reserve a namespace, survive session close or authorize publication |

Validation rejects missing/ill-typed references, malformed/duplicate identities,
unexpected directory declarations, missing prefixes, unsupported volume values
and inconsistent logical bindings before adapter access. CP2 validation, logical
scope identity and the existing CP3B invocation-policy checks are reused. Source
roots, anchor, workspace/run/scope and quiescent-source policy must agree. None of
those existing declarations becomes physical authorization.

Authentication, issuer, custody, freshness/revocation, approved code identity,
ordinary-user context and independently supplied physical storage inventory remain
OPEN. A matching string pair from a simulated adapter proves only comparison
behavior. The native context gate cannot be bypassed by populating these records.

## Bounded bootstrap protocol

The private protocol admits one exact root-only native locator of the form
`\Device\HarddiskVolumeN\`, without a source suffix. It requires an uppercase
drive mapping matching the declared anchor and exactly one unambiguous expected
mapping target equal to that root device name. The wire parser preserves current
and prior mappings, but this deliberately narrow protocol rejects additional or
different mappings. It never searches drives or chooses the first matching volume.

Within a simulation, the protocol performs these operations:

1. Validate all declarations and expectations without native access.
2. Compare host/token context and the one explicitly named mapping.
3. Acquire the one root through the adapter and retain it. Compare its actual
   object identity, directory metadata, volume fields and device observations.
4. Walk only the declared source-root and nearest-store-parent prefixes in parent
   order, one literal component relative to each retained parent. Require the
   adapter's exact returned long name and expected object identity at each step.
5. Recheck context, mapping, retained metadata and fresh parent-relative bindings.
   Replacement, mutation, unexpected case behavior or any uncertainty blocks.

There is no unrelated-sibling listing, source-file enumeration or content access.
Exact lookup names do not prove native long-name identity by themselves. A future
handle-bound long-name/parent observation API and its collision semantics remain
OPEN; copying the requested name into a native result would not satisfy the seam.

Directory identities contain a nonzero 64-bit volume serial and nonzero 128-bit
file ID. The formatted-volume 32-bit serial is checked separately; no truncation
or equality assumption joins the two. Each required directory must have a distinct
identity on the expected volume. Reparse, device, offline, virtual and recall
attributes, delete-pending state, unexpected links/type and inconsistent metadata
are rejected. The initial profile admits NTFS, 255-character components and
persistent ACL capability. Device type must be disk (`7`) and characteristics
exactly `0` or mounted (`0x20`). Other bits remain unsupported; a zero bitmask is
not independent proof of locality, fixed hardware or approved backing.

The case query must return exactly `False`; unknown or enabled case sensitivity
blocks. No query failure is interpreted as local storage or ordinary case behavior,
and no setting or privilege is changed.

| Bound | Implemented limit |
|---|---|
| Candidate root | One, no alternate candidate or retry |
| Named mapping observations | Eight per adapter/protocol session; failed native attempts consume the budget |
| Mapping buffer | Fixed 64 KiB / 32,768 UTF-16 code units; no growth or retry |
| Parsed mapping entries | 128 maximum; complete termination must be within the reported count |
| Declared directory prefixes | 128 maximum; every required prefix, no extras |
| Component tuple | 64 maximum; existing CP3B anchor/depth bounds also apply |
| Retained protocol handles | At most 130, including root and temporary recheck |

The primitive accepts only an explicitly named uppercase drive or syntactically
valid `Volume{GUID}` query. GUID-query parsing does not expand the narrower
bootstrap protocol's supported locator policy. Finite call counts do not establish
a wall-clock timeout, native cancellation or safe pending-I/O completion.

## Typed lookup and absent-store inspection

`classify_lookup` is a pure signed/unsigned NTSTATUS classifier. Status zero is
PRESENT; only `STATUS_OBJECT_NAME_NOT_FOUND` (`0xC0000034`) is candidate
NAME_NOT_FOUND. Other statuses, booleans and out-of-range values are BLOCKED.
This classification establishes neither actual completion nor namespace absence.

A future native lookup must use one literal component relative to a retained
parent, existing-only disposition, qualified case/reparse semantics and no
directory/non-directory result constraint. Any existing object, including a file
or short-name/case alias, must be PRESENT or BLOCKED, never absence. Pending,
access denial, sharing denial, wrong-type, path-not-found, generic no-such-file
and unknown statuses cannot be translated into NAME_NOT_FOUND.

The implemented protocol requires an independently declared nearest existing
store parent. All its prefixes must bind to expected identities and exact returned
long names. It then issues a typed lookup of the first missing component, rechecks
all bindings and issues a second lookup of that same component. Both must report
candidate NAME_NOT_FOUND with no transferred handle/name. It stops there and
retains the remaining suffix without descending or creating anything. A later
`recheck_absence()` repeats the binding and negative-lookup checks within budget.

Any PRESENT result collides, regardless of object type or returned spelling. A
source root equal to or containing the nearest store parent is rejected, including
physical identity aliases. A genuine shared ancestor is allowed for sibling source
and missing-store paths. Changed parents, mappings, identities, metadata, case
state or later insertion invalidate the session and initiate cleanup.

The result is a temporal observation under the declared quiescent-writer model.
Repeated checks do not defeat create/remove ABA races, hostile administrators,
mapped writers or insertion after the final check. There is no namespace
reservation, portable receipt or artifact-store authorization. CP4 creation-time
proof and publication remain separate and unimplemented. Native alias, long-name,
case and negative-status behavior remain BLOCKED until independently observed.

## Ownership and pending-I/O safeguards

The private seam transfers ownership only for a **completed successful** root
acquisition or a consistent PRESENT lookup with a valid unique handle. The session
retains those handles until release/close. Temporary successful binding probes are
closed once. Failure/cancellation attempts cleanup of every previously transferred
handle; an uncertain close blocks success and is never retried against a potentially
reused handle number. Closing clears the session observation and prevents reuse.

Failed, pending, malformed or otherwise unproven acquisitions remain adapter-owned.
A result carrying a handle without a consistent completed-success status is
rejected without treating that number as a safe-to-close resource. The protocol
cannot complete native I/O or free its buffers. This is an adapter obligation,
not a leak-free claim about a defective future implementation.

Microsoft's [IO_STATUS_BLOCK contract](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/ns-wdm-_io_status_block)
requires waiting for pending completion and distinguishes it from immediate return
status. The pure classifier uses the nonpending routine status rather than requiring
an error-path status block to duplicate it. [CancelSynchronousIo](https://learn.microsoft.com/en-us/windows/win32/api/ioapiset/nf-ioapiset-cancelsynchronousio)
requests cancellation without waiting for completion. Returning BLOCKED, closing a
handle or requesting cancellation does not establish safe buffer reclamation.

CP3D therefore introduces no callable Nt acquisition/query and no pending-request
resource allocation. All native filesystem operations stop before those risks
arise. No existing CP3B native reader behavior is silently patched or promoted;
its previously documented completion questions remain qualification blockers.

## Reviewed APIs and unsupported assumptions

| Primary contract | Defensible implementation/use | Still BLOCKED or OPEN |
|---|---|---|
| [QueryDosDeviceW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-querydosdevicew) | Fixed named query; returned UTF-16 count; first current then prior MULTI_SZ entries | Actual native call behavior, local/global shadow changes, approval and backing inference |
| [NtCreateFile](https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntcreatefile) | Reviewed existing-only/relative semantics inform the private seam; no new binding | Root bootstrap authority, namespace resolution, completion and directory/reparse flag compatibility; no weaker flags substituted |
| [NtQueryVolumeInformationFile](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntqueryvolumeinformationfile) | Reviewed handle-bound result length and unsupported-field semantics; no callable query | Native user-mode ABI/export, exact successful completion, capability/support and physical-backing evidence |
| [File-system classes](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-fscc/ee12042a-9352-46e3-9f67-c094b75fe6c3), [device record](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/ns-wdm-_file_fs_device_information), [characteristics](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-fscc/616b66d5-b335-4e1c-8f87-b4a55e8d3e4a) | Pure eight-byte/two-DWORD decoder; independent expectations compare exact values | Decoding is not a query or a locality/backing certificate; remote, virtual, removable and unknown arrangements unsupported |
| [Win32 information classes](https://learn.microsoft.com/en-us/windows/win32/api/minwinbase/ne-minwinbase-file_info_by_handle_class), [case-sensitive information](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/ns-ntifs-_file_case_sensitive_information) | Private seam requires a definite ordinary case-insensitive observation | No case query is bound; Win32 and NT class values cannot be interchanged; native availability/behavior and handle-bound exact-name proof unqualified |

Named Windows host owner, ordinary-user qualification host, independent reviewer,
provisioned hostile fixtures, observer coverage, authentic inspection authority and
approved offline runtime remain OPEN. No simulation supplies those approvals or
native evidence. All native obligations in the CP3C qualification plan remain
NOT_RUN/BLOCKED unless a later separately authorized record establishes otherwise.

## Compatibility and stopping point

No public CLI, capability activation, evidence schema, CP2 projection, identity
algorithm, artifact format or persistence behavior changes. Native paths, transient
IDs and observations remain outside canonical hashes and sealed artifacts. There
is no adapter connection to the CP3B reader, source-content operation, source/store
creation, lock, publisher or downstream integration. Existing CP1/CP2/CP3A/CP3B
gates and POSIX behavior remain intact. No runtime Git, Docker, WSL, cloud, AI
provider or new dependency is introduced; the Agent-mastery pin is unchanged.

DRAFT authority, UNVERIFIABLE verification, BLOCKED independent semantic acceptance
and NOT_RUN benchmarks are preserved. Public Windows evidence commands retain
their prior BLOCKED diagnostics and exit code 2. Stop after CP3D; qualification,
public activation, CP4, CP5, P2B and P3 require separate authorization.
