# WS-1: inspect a pinned installed environment

Reviewed baseline: `a79b15fefd878f1ecc9c0e4969e1c6a211120a41`. The user authorized only
the launcher in the [workstation plan](WORKSTATION_EXECUTION_PLAN.md) and its
[W01–W06 obligations](WORKSTATION_COMPATIBILITY_MATRIX.md#proposed-workstation-checks).
The launcher does not add a Python CLI or a public evidence operation.

**As shipped there is no authorized workstation installation.** Even if Python is
installed, `bash scripts/workstation.sh status` returns a bootstrap BLOCKED diagnostic
on stderr and exits 2. Supplying `SAS_RE_PYTHON`, owning a checkout, or finding a wheel
labeled 0.3.0 cannot change that result. See [actual validation](WS1_VALIDATION.md).

## Interface and authority

A user of a separately approved kit would invoke `bash /approved-kit/scripts/workstation.sh
status` from Terminal/Bash or Windows Git Bash. Exactly one argument is accepted:
`--help`, `--version`, or `status`. Missing/extra arguments, `-h`, `check-baseline`,
evidence commands, `eval` and every other verb return **wrapper usage/2** before any
interpreter or approval lookup. A recognized verb with missing/inconsistent trust
evidence returns **WS1 BLOCKED: bootstrap**, exit 2, with no child result on stdout.
A qualified call executes the selected interpreter with `-I -B -X utf8 -m sas_re` and
that one verb. The final process receives the original streams; the launcher does not parse,
rewrite, pipe or retry it, or turn process errors/signals into evidence findings.

The output is the existing engine's help/version text or status JSON. A status exit of 0
means status was reported; it does not imply available evidence I/O or semantic acceptance.
No config/source/record/store/report operands are accepted. No installation, activation,
SAS, network/provider request, Git, Docker, WSL, B1, report export or P3 analysis.

## Trust bootstrap

There is no release authority, verification key, approved interpreter digest or host-specific
release inventory supplied in this checkpoint. To avoid a caller approving its own runtime,
the launcher has two **non-environment** delivery slots: an absolute approval-record
location and its SHA-256. Both are empty in Git. Only an independent release custodian
could bind those constants in an authenticated kit copy. The custodian must authenticate
that **final launcher's bytes** by a trusted channel outside the kit before Bash sees it,
including its UTF-8/no-BOM/LF delivery. Changing the constants changes the launcher hash.
A checksum from beside the unchecked script is insufficient. No enrollment, signing,
installer, release manifest, runtime override or public “test mode” is shipped.
The synthetic copies used in tests substitute those two constants, not an authority
record for this repository or anyone's workstation.

The approved inventory is external to the project and to the interpreter tree. For this
version it has twelve nonempty, LF-terminated fields in the following exact order:

| Line | Binding |
|---|---|
| 1–2 | `WS1-APPROVAL-1`, then `darwin`, `win32` or `linux` (Linux x64 is a regression host only) |
| 3–4 | Exact absolute Bash spelling of the venv interpreter; native absolute invocation path as expected in Python |
| 5–7 | Resolved native base prefix, resolved native base executable, exact 3.12 patch version |
| 8–10 | Exact sysconfig platform tag; lowercase SHA-256 of the invoked executable bytes; SHA-256 of the root `pyvenv.cfg` |
| 11–12 | Exact application distribution version; SHA-256 of the separate closed file inventory |

Bounds: 64 KiB for the record and cfg, less than 4096 characters per record field, 8 MiB
and 65,536 entries for the file list, at most 32 path components, 128 MiB per installation
file and 512 MiB total regular-file bytes. Unlisted entries cause refusal, not a partial result.

A fixed companion at the approval location plus `.files` lists the venv contents. Its
preimage is UTF-8 relative POSIX names in sorted order, each followed by NUL, a marker,
and LF. A directory uses `-`; a regular file uses lowercase SHA-256 of its bytes; a
permitted link uses SHA-256 of `link` + NUL + its OS-encoded target spelling. It includes
empty directories, packages, resources, startup hooks, bytecode, dependencies, dist-info
and venv executables. This is a **workstation delivery inventory**, not a SAS evidence
schema, canonical graph, or authority token. It lives outside Git. The issuer must review
the installed closure against independently approved interpreter, project-wheel and
dependency artifacts, not bless whatever happens to be present. Every host/install path
or byte change requires renewed evidence. Picking a historical wheel or generating a
manifest from local state is not a production bootstrap.

If `SAS_RE_PYTHON` is set, its spelling must match line 3 exactly (even an explicitly
empty value blocks). Otherwise only line 3 can supply the selection. The launcher is a separate kit file used with an installed project wheel; it is not a new
console entry point or packaged installer. There is no PATH
search or Store launcher. Do not dereference caller-specified alternatives or search for
a manifest beside them. Native Windows uses one approved spelling in Git Bash and the
corresponding native path in Python; it is never a POSIX backend. The target scope is
Darwin ARM64 and proposed native Windows x64, with an x86_64 Linux branch for existing CI.
Host choice uses Bash's build triple; runtime, OS, bitness and native tag must also match.

## Verification before dispatch

1. Use a trusted Bash and parent environment (no unapproved imported functions/startup
   hooks, including `BASH_ENV`). A script cannot authenticate itself or undo code that
   ran before its first statement. Read bounded approval data; reject malformed framing,
   an incorrect hash, unsupported tuple, ambiguous selection or missing trusted tools.
   Only fixed host digest tools compute byte hashes: `/usr/bin/shasum -a 256` on macOS
   or `/usr/bin/sha256sum` from Git Bash/Linux. No record field is executable shell text.
2. Before invoking even a probe, compare the selected executable, its venv configuration
   and the file inventory to the pinned values. Require the exact `bin/python` or
   `Scripts/python.exe` in the approved venv. Preserve the invocation path when it is
   a legitimate POSIX venv link; executing its resolved target directly can select a
   different site. No adjacent overriding config. The Windows branch also rejects Store
   alias locations and adjacent path overrides/native loader files outside its narrow profile.
3. Run a fixed, noninteractive Python probe with `-I -B -S -X utf8`. It uses trusted base
   standard-library code; site processing is initially off. It checks native origins/tag,
   closed venv membership and file contents, installed package/resources and distribution
   origin, and the effective import path. Check directory membership before descending
   into unexpected directories or opening undeclared files. Refuse special files, unapproved
   links/aliases, editable origins, unexpected startup redirections and mismatched bytecode.
   Positive-origin checks use the approved venv, not an editable source checkout. Do not import
   the application until the checks succeed. Failure is sanitized and no final command runs.
4. Start the approved application directly via `exec` with isolated/no-bytecode/UTF-8 flags.
   The host tools and Python use a clean child environment; native Windows children alone
   receive `MSYS2_ARG_CONV_EXCL=*`. Paths and IDs are never interpreted as commands.
   Do not convert evidence paths or logical file keys. No caller input is read to provision
   or repair an environment. The preflight inventory stream is separate from final stdin.

These are **integrity checks inside an assumed trusted installation**, not a sandbox.
The approved OS, Bash, native tools, base interpreter including redirector/loader, DLLs,
stdlib and base startup hooks must already be independently authenticated, protected and
quiescent. The launcher and inventory location/ancestors and the venv must not admit
untrusted concurrent writers or rollback during verification/dispatch. A digest of a
venv redirector does not authenticate the base it loads, and two processes cannot prove
a hostile host safe. If these assumptions cannot be established, do not provision the
trust slots: the result is BLOCKED. No hostile-writer, administrator or Windows ACL proof
is claimed. The launcher inspects only an approved installation; its diagnostics never
authenticate human approval or authorize source access.

The existing CP1 gate, CP2 identity projection, P1/P2A publication, private P3-A1
diagnostics and downstream pin remain untouched. Windows source reading/publication and
B1 semantic evaluation are still BLOCKED. Statuses remain DRAFT / UNVERIFIABLE / BLOCKED /
NOT_RUN. Stop at WS-1; setup, configuration, source execution and reporting require separate
approval.
