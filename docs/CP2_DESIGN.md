# CP2 — portable local authorization declarations and identity compatibility

Approved baseline: `0061b7bf038f7b36add830912258232f174af197`.
Scope approval is recorded in [APPROVALS.md](APPROVALS.md). This implements only
CP2's separately versioned input contract, pure validation and logical identity
projection. [Actual checks](CP2_VALIDATION.md) distinguish observed results from
design guarantees and unqualified platforms. Package version stays 0.3.0; the
Git commit identifies this additive API change.

No evidence command consumes the new envelope. It cannot authorize a source
read, create an artifact store or serve as a capability token. CP1's platform
selector, POSIX implementation, CLI exits, frozen contracts and evidence writers
are unchanged. Windows evidence I/O and native qualification remain **BLOCKED**.
Semantic acceptance remains **BLOCKED**, verification **UNVERIFIABLE**, artifact
authority **DRAFT** and benchmarks **NOT_RUN**.

## Contract and public API

The new bundled contract is
[`contracts/authorization/v1/local-authorization.schema.json`](../src/sas_re/contracts/authorization/v1/local-authorization.schema.json).
It has its own `authorization_schema_version: "1.0"`, schema ID
`urn:sas-re:local-authorization:1.0`, and named
`identity_projection: "sas-re-scope-v1"`. These do not modify or extend the frozen
evidence v1/v2 dispatch. All objects are closed; references resolve within the
bundled schema only. Shape validation alone is insufficient: the public validator
also enforces ownership, references, explicit binding coverage and path policy.

| Envelope field | Meaning and boundary |
|---|---|
| `logical_scope` | Workspace/run IDs, module IDs, `synthetic: true`, root IDs without paths, exact file declarations, dependencies and log associations |
| `platform` | Explicit `windows` or `posix` path-syntax profile, not a claim of OS or filesystem qualification |
| `bindings` | Exactly one `{root_id, platform, path}` per logical root; no extras, duplicates, guessed mappings or host defaults |
| `authorization` | Caller-supplied `declaration_id`, `declared_by`, nullable `approval_reference`; fixed `status: DECLARED`, `human_approval: NOT_VERIFIED`, `access: READ_ONLY` |
| Version fields | Select the independently validated envelope and the exact supported identity projection; no fallback or inferred conversion |

Authorization metadata records a declaration, not an authenticated person,
approval or permission. No caller identity, timestamp, signature or approval reference is
fabricated or filled in. An opaque reference can be recorded but is not followed
or verified. The separate project implementation approval in APPROVALS.md is not
a run-specific physical authorization. `synthetic` is not a private-data detector.

[`sas_re.authorization`](../src/sas_re/authorization.py) provides:

- `load_authorization_schema()` returns a defensive copy of the bundled contract.
- `validate_logical_scope(value)` validates the envelope's logical declarations,
  without a version field or physical bindings.
- `validate_authorization(value, expected_platform=None)` validates the full
  envelope. An optional explicit caller expectation must match; the host OS is
  never guessed. A Windows declaration can be inspected on macOS/Linux.
- `parse_authorization(raw, expected_platform=None)` accepts already supplied
  UTF-8 JSON **bytes**, never a filename. Duplicate keys, non-finite values, BOM,
  invalid encoding and excess depth/size are rejected.
- `project_logical_scope(value, expected_platform=None)` returns a detached,
  canonical legacy hash input, independently shape-checked against
  `LegacyScopeIdentityInput`. It deliberately lacks physical paths and fails the
  historical v1 `Scope` contract.
- `authorization_scope_identity(value, expected_platform=None)` applies the
  unchanged P1 `scope_identity()` to that projection.

Successful validators return `None`, not a filesystem authorization status or
access token. Errors are input-free `EvidenceError` codes. Unknown envelope or
identity versions produce `BLOCKED` with `AUTHORIZATION_VERSION_UNSUPPORTED` or
`AUTHORIZATION_IDENTITY_UNSUPPORTED`. Ambiguous repeated log association produces
`AUTHORIZATION_LOG_AMBIGUOUS/BLOCKED`. Invalid shape, mapping, ownership or syntax
produces `FAIL` with a fixed code. There is no new CLI/exit convention. Existing
evidence commands still report `FILESYSTEM_CAPABILITY_UNAVAILABLE`, exit 2, on
Windows before opening even their scope manifest.

The pure API reads trusted package resources when first loading schemas. It does
not open supplied paths, inspect directories, resolve symlinks/reparse points,
expand environment variables, use the working directory, invoke Git/processes,
or contact a network/provider. It requires only the existing installed package
and locked dependencies. No dependency, lock extension or CI matrix is added.

## Logical integrity and bounded inputs

File keys must be exactly `root_id:path`; each file belongs to one declared root
and module. Root, file, dependency and association IDs must be unique. Module IDs
are unique. Logical identifiers remain case-sensitive; there is no casefolding
or normalization of canonical fields. Each source key in a dependency must exist.
Missing/null targets must explicitly be `UNRESOLVED`; even a declared target with
`UNRESOLVED` stays unresolved. No file search or include expansion occurs.

LOG/LST associations must explicitly name declared SAS/INCLUDE files, one log
per association and the declared run. Missing associations are permitted and
remain missing, never inferred from names. These declarations do not establish
actual execution provenance or upgrade `DECLARED` to observed/verified facts.

Bounds: strict built-in JSON values, 8 MiB serialized envelope, depth 64, up to
1,000 roots/modules/files/associations and 10,000 dependencies. File paths retain
the historical ASCII relative syntax, at most 32 components of 128 characters,
with additional conservative portability exclusions below. Oversized or unknown
formats are rejected rather than silently trimmed.

## Native path declaration profile

[`_authorization_paths.py`](../src/sas_re/_authorization_paths.py) uses string
operations and Unicode comparison only. No `Path` object is resolved or opened.
These are conservative lexical screens, not proofs of physical disjointness.

| Property | Windows declaration | POSIX declaration |
|---|---|---|
| Absolute root syntax | Uppercase drive plus backslash, e.g. `C:\Synthetic\Sources` | Single leading slash, e.g. `/synthetic/sources` |
| Root breadth | Whole-volume `C:\` rejected | Whole-filesystem `/` rejected |
| Namespace exclusions | UNC, device/extended prefixes, drive-relative/root-relative, forward/mixed separators, ADS/extra colon, wildcard characters | `//`, backslashes, empty components, relative roots |
| Common exclusions | Empty/dot/dotdot components, repeated/trailing separator, controls/format controls/surrogates, expansion-like `$`, `%`, `~` | Same common exclusions |
| Components | At most 255 UTF-16 units; no trailing space/dot or reserved device basename, including extensions and COM/LPT superscript variants | At most 255 UTF-8 bytes |
| Root and complete declared file path | At most 259 UTF-16 units, no implicit extended prefix | At most 4096 UTF-8 bytes |
| Unicode native parents | Accepted without rewriting when no screened collision; relative evidence paths remain ASCII | Same |

The length bounds are declarations-profile limits, not proof that an OS will
open the path. Lowercase drive letters and several otherwise legal native names
are deliberately outside this profile. New relative file paths also reject
Windows-reserved basenames and trailing dots/spaces on every declared platform.
Legacy v1 readers retain their existing rules; CP2 does not rename historical
files or widen their accepted namespace.

NFC plus casefold is used **only for rejection**. Duplicate/nested bindings,
case/normalization aliases and differing spellings of a shared intermediate
directory are rejected. Per-root file tries reject duplicate/aliased names,
file-versus-directory collisions and directory spelling aliases. Exact original
spellings remain in canonical declarations. Unicode filenames outside the legacy
ASCII relative subset require a later versioned design; no transliteration or
normalization is allowed to make old IDs match.

Strings cannot reveal symlink/reparse destinations, hardlinks, volume identity,
mounts, SUBST/mapped drives, 8.3 aliases, actual case tables, permissions or NTFS.
Tilde spellings are rejected, but this cannot prove the absence of hidden aliases.
Even syntactically distinct drives may refer to the same physical volume. Physical
authorization is **not established**. Any future binding consumer must remain
BLOCKED until a separately approved backend verifies required capabilities and
physical identity. CP2 implements no such consumer, handle, receipt or cache.

## Exact legacy identity compatibility

For accepted declarations, projection copies only `logical_scope`, inserts
`schema_version: "1.0"` as part of the named legacy algorithm, sorts root IDs and
module IDs, sorts files/dependencies/associations by their existing identity keys,
and sorts each association's source-file keys. This is the exact canonical input
already hashed by frozen `scope_identity()`. It is a hash preimage, **not** a
pretend v1 filesystem Scope; no `/C:/` conversion or guessed path is created.

The new envelope version, binding paths/platform and declaration metadata are
excluded only by this explicit versioned field selection. No existing artifact's
schema version is dropped. Transient device/inode/handle identities have no field
in the new logical contract. No envelope is published in a frozen artifact set.

| Change | Required identity effect |
|---|---|
| Different native root location/platform, caller declaration metadata, or ordering of set-like declarations | Same projected bytes and scope hash for identical logical declarations |
| Workspace/run/module, logical root/name, ownership, encoding, dependency or log association change | Changed scope hash and resulting source fingerprint; no silent semantic-ID reuse |
| Original source bytes change (including LF/CRLF/BOM/recoding) with identical declarations | Scope hash unchanged; affected file ID, source fingerprint and source-bound operation IDs change |
| Supplied operation facts change with the same source fingerprint | Operation ID changes via unchanged record identity rules |

The scope hash does not hash source contents. Existing file IDs bind their
declaration and original-byte metrics; unrelated scope changes can legitimately
retain an unchanged file ID, while the composed source fingerprint changes.
Existing source identity and citation rules never normalize raw bytes or encodings.

Public [vectors](../tests/cp2_vectors.py) were authored against the frozen v1
algorithm before reading candidate authorization code. Literal preimage and
golden hashes are checked with an independent `hashlib`/JSON oracle and the
unchanged inventory pipeline (physical transport mocked only in pure tests).
Both native declaration profiles yield scope hash
`ef0f163ba588eeaf5da718a772f9bed73e5180623bbed575011490df43849e65`.
Actual historical P1/P2A sealed artifacts are compared separately in validation.
This proves bounded identity compatibility, not independent SAS semantics.

Exact compatibility is claimed only for the supported legacy logical subset.
Unsupported versions fail BLOCKED; incompatible declarations fail validation.
There is no speculative alternative identity algorithm or auto-migration. A future
extension that cannot reproduce this exact preimage requires a separately
versioned identity and explicit old/new revision mappings under separate approval.
The existing revision-map contracts/helpers remain unchanged and are not invoked
to fabricate compatibility. Neither matching names nor textual similarity permits
retaining operation IDs after a source/fact change.

## Security, qualification and stopping boundary

Keep actual local envelopes outside Git, preferably in the already ignored
`local/` directory or entirely outside the checkout. Native paths and declarations
may be sensitive. CP2 fixtures are synthetic Python literals, not private intake;
ignore rules and the repository guard are not a complete DLP mechanism.

| Target | CP2 boundary |
|---|---|
| Existing macOS/Linux | Pure validation plus unchanged qualified POSIX behavior; actual test executions are listed in validation |
| Native Windows 11 x64/NTFS, Python 3.12, PowerShell 7 preferred | Proposed qualification target only; no approved host/dependency environment supplied, native execution BLOCKED |
| Windows I/O on any target | BLOCKED by unchanged CP1 before source/store access; syntax tests are not native execution |
| Other platforms/filesystems | No new qualification or support claim |

No CP3–CP5, native traversal/publication, authorization receipt, new runtime
dependency, AI adapter, P2B evaluator, P3 architecture work or downstream integration
is introduced. Agent-mastery stays pinned to
`bc754e0f1204a99020c864df2a5b25983005e09c` and read-only. Stop after CP2 for human
review. Any CP3 proposal must resolve the unavailable native test environment and
physical authorization/alias controls without treating these declarations as
permission or weakening existing POSIX safeguards.
