# WS-2A: offline kit and installed-inventory handoff

**Planning only; neither target has a released kit.** Baseline
`767b2c3154de7fb451c4278e22f25633d9a025d0` is accepted for WS-1 engineering.
The repository [launcher](../scripts/workstation.sh) still has two empty approval
slots. An installed Python, a passing test or a wheel with the expected version
cannot fill them. No custodian, signer, trust root, release ID or target machine
has been designated. All installation trials in the [test plan](WS2A_INSTALLATION_TEST_PLAN.md)
are proposals, **NOT_RUN**.

The recommendation is **one closed set of inputs per target, one fresh environment
per installation, and a separate human decision to activate it**. Ordinary use is
local, from Terminal/Bash on macOS ARM64 or Git Bash with native CPython 3.12 on
Windows 11 x64. It needs no checkout, Git command, WSL, Docker, Linux host/VM,
cloud account, model provider or network. The [WS-1 design](WS1_DESIGN.md),
[validation](WS1_VALIDATION.md), [workstation workflow](WORKSTATION_EXECUTION_PLAN.md)
and [matrix](WORKSTATION_COMPATIBILITY_MATRIX.md) remain the basis for this plan.

## Exactly what goes into a wheelhouse

Each target needs **ten wheels** in a flat, read-only wheelhouse: eight shared
universal wheels, **one** compatible native wheel, and **one** separately approved
project wheel. Keep the interpreter distribution, bootstrap tools, manifests and
launcher outside this directory. Do not put both OS wheels, an alternative build,
an sdist, a second project wheel or a “just in case” dependency in it.

The shared candidates below have tag `py3-none-any`. The expected SHA-256 for
each is the single value on that package's line in the frozen
[requirements.lock](../requirements.lock), itself SHA-256
`4676c7fe0a41ce2fdb35c2fb10cc014a8b352a8ca71029eb28b7373c0053e19b`.
The links are primary publisher metadata, not instructions for an offline workstation.

| Filename used by both targets | Why it is present |
|---|---|
| [pip-25.3-py3-none-any.whl](https://pypi.org/pypi/pip/25.3/json) | Pinned installer tooling |
| [setuptools-80.9.0-py3-none-any.whl](https://pypi.org/pypi/setuptools/80.9.0/json) | Pinned packaging tooling and reviewed startup hook |
| [wheel-0.45.1-py3-none-any.whl](https://pypi.org/pypi/wheel/0.45.1/json) | Pinned packaging closure; no wheel build on the workstation |
| [attrs-26.1.0-py3-none-any.whl](https://pypi.org/pypi/attrs/26.1.0/json) | Runtime dependency |
| [jsonschema-4.26.0-py3-none-any.whl](https://pypi.org/pypi/jsonschema/4.26.0/json) | Project dependency and validator |
| [jsonschema_specifications-2025.9.1-py3-none-any.whl](https://pypi.org/pypi/jsonschema-specifications/2025.9.1/json) | Schema resources for the validator |
| [referencing-0.37.0-py3-none-any.whl](https://pypi.org/pypi/referencing/0.37.0/json) | Reference handling; also depends on the native `rpds-py` package |
| [typing_extensions-4.16.0-py3-none-any.whl](https://pypi.org/pypi/typing-extensions/4.16.0/json) | In the Python 3.12 runtime closure |

| Target | Native wheel | Published size / SHA-256 | Lock decision |
|---|---|---|---|
| macOS ARM64 | `rpds_py-2026.9.1-cp312-cp312-macosx_11_0_arm64.whl` | 341,380 bytes; `e21c1429e205828ea886a2293a4a2c8e01f4c25d9893ca330e97a6cf73f52e7b` | Already in lock. The wheel's minimum macOS tag is not an OS qualification. |
| Windows 11 x64 | `rpds_py-2026.9.1-cp312-cp312-win_amd64.whl` | 222,923 bytes; `5ce8943f79c2210f7abcc28e86367b03b28d95027fd01c46d2472373ae70c86f` | **Absent; Windows install BLOCKED.** Separate review and explicit lock-change authorization required. |

These filenames, tags and digests were checked against [PyPI release metadata](https://pypi.org/pypi/rpds-py/2026.9.1/json)
and its [file-specific checksums and provenance](https://pypi.org/project/rpds-py/2026.9.1/#files).
Only metadata was reviewed; neither native wheel was fetched or hashed here. The other
locked `rpds-py` digest (`addeda51556dac7c1a2f14cda62db8b621cd12afba3091d03a96c72932387eab`)
is for manylinux x86_64 CI, not Windows. Never borrow that digest, substitute win32/ARM64,
build from Rust/source, pass an unlocked requirement or add a private overlay lock
to get past this gate. A future review must acquire the exact artifact outside the offline
installation, verify its bytes, upstream provenance, internal metadata and target ABI,
review the exact proposed lock diff, and freeze the **new** reviewed lock digest.

The tenth filename is `sas_reverse_engineering-0.3.0-py3-none-any.whl`.
Its **release hash is OPEN**. WS-1 recorded two different historical wheel hashes
for that version; neither is a production pin. Select one reviewed build against
the approved project source revision and toolchain, or accept an independently
authenticated prebuilt wheel with that provenance. Verify package code, bundled
schemas, baseline metadata, console entry point, wheel tags and exact archive bytes.
The same universal wheel may serve both wheelhouses only if those bytes match.
Prebuilding/acquisition is a separate custodial activity. Nothing is built,
resolved online or fetched at workstation install time.

## Two manifests answer different questions

| Record | Produced and checked by | What it binds |
|---|---|---|
| **Release inputs:** “What may be installed?” | Proposed: custodian freezes an input bill of materials; an independent reviewer reconciles it to upstream publications, the approved lock/project revision and the actual staged bytes. A human with release authority authorizes installation for a specified tuple. | Unique generation, allowed purpose/target, OS/build/architecture, exact native CPython patch/build and installer or existing base image, bootstrap/verifier and Bash/tool identities, project revision, reviewed lock digest, exact wheel filenames/sizes/tags/hashes, expected installed layout, path/ACL and retention policy. No executable or unsigned directives in the manifest. |
| **Installed inventory:** “What exact installation did we get?” | A trusted observer independently measures the quiescent candidate after installation at its final path. Reviewer compares to the approved inputs and a previously frozen expected installation. | Actual executable/config hash, base prefix and base executable, native vs shell path, package and distribution origin, all permitted venv members, including generated files and empty directories. A matching local inventory alone is not approval. |
| **Activation handoff:** “Which launcher may run against it?” | Separate human activation decision after review and native qualification. Custodian authenticates the exact **final bound kit copy** of WS-1, its record, companion and generation; operator verifies it out of band before Bash interprets it. | Whole-install identity, permitted target/inspection verbs, exact final launcher size/hash, validity/revocation policy and prior-generation disposition. The Git copy remains unchanged and BLOCKED. |

**Trust must start outside the kit.** Proposed mechanism: detached signature over the exact,
unambiguously encoded release manifest bytes, verified offline by an already authenticated
tool/key in a protected enterprise store; alternatively an independently administered,
read-only delivery channel pinned to those bytes. A public key or checksum first obtained
from the same untrusted media is not a trust root. Pin verifier/version, roles, scope,
key rotation, revocation, offline validity horizon, trusted clock or monotonic generation
and anti-rollback policy. Record human identity/date and restricted evidence references;
reject unknown, stale, revoked, replayed or out-of-scope decisions. These people, keys,
channels and budgets are **OPEN**. Stop if current authorization cannot be established
offline. No signature format, trust identity or signed artifact was created here.

Before any supplied executable runs, independently confirm the protected base image:
vendor interpreter package/build and bytes, actual approved base prefix/executable,
native loader, libraries/stdlib, startup hooks, trusted shell and fixed utility binaries.
On macOS bind native ARM64 and the actual OS/build, not a Rosetta/Intel fallback. On
Windows bind native 64-bit CPython (`win32`, `nt`, `win-amd64` platform tag),
the base executable/Python DLLs as well as the venv redirector, actual Windows build,
Git Bash/MSYS build and its utilities. Choose and attest the exact 3.12 patch; the
historical 3.12.5 tuple is not a release choice. An existing interpreter must pass the
same identity check as an approved offline interpreter payload. An embeddable/minimal
distribution that cannot satisfy the venv/WS-1 checks is ineligible. See
[Python 3.12 on Windows](https://docs.python.org/3.12/using/windows.html).

## Future offline installation sequence

No step below was executed. Only a separately authorized installer or operator procedure
could carry it out.

1. **Admit the inputs, before candidate creation.** Read and authenticate the external
   release decision. Verify complete directory membership, lengths and SHA-256 of all
   kit objects before import, unzip, venv creation or pip. Reject missing/extra entries,
   duplicate normalized names, symlink/reparse/hardlink or mount aliases, special objects
   and uncertain parents. Use a controlled local volume with trusted effective writers,
   enough space for the complete install **and cleanup**, separate from source/store.
   Inspect bounded wheel ZIP members without execution: no traversal, duplicate/case or
   Unicode collisions, unsafe links, overlapping output paths or unapproved startup code.
   Reconcile filenames with internal WHEEL/METADATA, Python/ABI/OS tags, Requires-Python
   and the complete Requires-Dist closure evaluated for 3.12, no extras. Refuse an
   unexpected dependency or remote reference before pip. Check applicable publisher advisories and approve the
   toolchain for this use; a matching hash does not make a vulnerable tool safe. Never
   execute a wheel's unpack command to inspect untrusted members. Pin this inspected input set
   read-only through install. On Windows the absent lock authorization stops here.
2. **Reserve a new final path.** Record the current approved generation read-only.
   Exclusively reserve a fresh, private, uniquely named candidate environment at its
   intended **final physical path**. Do not copy a dev venv, move a staged venv, follow
   a mutable “current” symlink, inherit site packages, clear an existing directory, or
   install into the active environment. [Venvs are not portable directories](https://docs.python.org/3.12/library/venv.html).
   Pin the absolute paths to the base, wheelhouse, controlled scratch and record locations.
3. **Use one authenticated bootstrap route.** Proposed: create a pip-less venv with
   the verified native base (`venv --without-pip`, system site disabled). Use a
   **separate preverified local pip 25.3 tool environment** and pip's
   [explicit target-interpreter option](https://pip.pypa.io/en/stable/topics/python-option/)
   `--python <absolute candidate interpreter>`. Custodian must attest the bootstrap
   tool and its entire base/closure before use. Do not run pip found on PATH or prefer
   an unverified bundled seed. If that tool is unavailable, BLOCKED; no implicit ensurepip,
   upgrade, Store download, source build or alternate bootstrap.
   Before the first target execution, independently check the newly created venv against
   the expected empty-venv layout, cfg, redirector/base and startup controls. In particular,
   [pip 25.3's dispatch](https://github.com/pypa/pip/blob/25.3/src/pip/_internal/cli/main_parser.py#L74-L95)
   starts the target with its external runner; parent Python flags do **not** automatically
   follow. Clear inbound `_PIP_RUNNING_IN_SUBPROCESS`, Python/loader and pip settings;
   use a reviewed child environment with user-site off and bytecode writes suppressed.
   Bound and observe both processes. If that clean startup cannot be established, stop.
4. **Install exact files, in one target invocation.** Give the verified pip the approved
   lock unchanged plus a separately authenticated, single-entry local project requirement:
   the exact local wheel file URI (properly escaped) and its approved SHA-256. It adds
   **no** dependency pins or Windows override. Use `--require-hashes --only-binary=:all:
   --no-index --no-deps --no-cache-dir --no-compile`, one `--find-links` verified local
   flat directory, `--no-input` and `--disable-pip-version-check`. The complete prechecked closure is eight
   universal plus one native dependency and the project wheel. `--no-deps` does not
   excuse a missing member. One invocation avoids starting a second target interpreter
   against partly installed site hooks. No glob, editable, sdist, VCS, remote URL, HTML
   link source, build backend or dependency repair. For the pinned tool explicitly disable
   config-file loading by setting `PIP_CONFIG_FILE` to the target's actual null device
   (the exact native `os.devnull` string, not a Bash pathname), scrub all other inherited pip/proxy
   settings, and check the effective settings. Use a protected CWD/temp area and denied,
   independently observable egress. `--no-compile` suppresses installer compilation; it
   is **not** a guarantee that ordinary imports write no pyc files. Cache flags alone
   do not enforce offline operation. See [pip secure installs](https://pip.pypa.io/en/stable/topics/secure-installs/)
   and [configuration precedence](https://pip.pypa.io/en/stable/topics/configuration/#pip-config-file).
5. **Reconcile prior to activation.** Compare the target closure to an independently
   approved reference of permitted wheel payloads and install derivations, not to an
   expected list generated by the installer under test. Reconcile every installed
   distribution/version, package code/resources and native extension to the measured
   wheel bytes. Use [wheel RECORD](https://packaging.python.org/en/latest/specifications/recording-installed-packages/)
   as an index, not an authority. Account separately for pip-generated RECORDs, entry
   points/shebangs, `pyvenv.cfg`, `direct_url.json`, hooks and any bytecode. The specified direct-file install must produce
   [project direct URL metadata](https://packaging.python.org/en/latest/specifications/direct-url/)
   naming the exact authorized local wheel URI with its approved SHA-256; missing,
   malformed or divergent origin blocks handoff. This is stronger than WS-1's generic
   check, which allows that metadata to be absent. Compare paths, owner, ACL and backing object.
   Do not execute site hooks or import a candidate package to decide whether its files
   were trustworthy. Once provenance is reconciled, run bounded `pip check`, import-origin,
   resources and native-extension checks from outside the checkout on the **candidate**
   under a trial grant. Ensure those checks cannot write bytecode or alter the frozen view.
   Freeze/re-measure after all writes stop; a mismatch is not repaired by rehashing it.
6. **Rebuild comparison.** Freeze recipe, seed, bytecode policy, local wheelhouse URI,
   controlled absolute install path, file modes and all tool versions. In particular, pin a
   valid ZIP-range UTC `SOURCE_DATE_EPOCH` in both installer processes: [pip 25.3 generates
   Windows entry-point executables with embedded ZIP timestamps](https://github.com/pypa/pip/blob/25.3/src/pip/_vendor/distlib/scripts.py#L245-L255).
   Rebuild at different wall-clock times; identical inputs should not silently change
   `Scripts/sas-re.exe` or its RECORD hash. On each separately
   approved native tuple, use two independent clean fixture runs (serial resets are sufficient) with
   the same final path spelling and inputs; compare membership and per-file bytes. Resolve
   every difference in generated artifacts against a preregistered derivation (or stop
   and revise the recipe). Do not omit varying files from the WS-1 inventory. Different
   host paths, cfg, interpreter patch, local wheel URL, timestamps in generated pyc or
   image mean a new binding. Reproducibility here means repeatable inputs and a checkable
   result **on a declared tuple**; macOS and Windows trees need not hash identically.

## Terminal/Bash and Git Bash handoff

Use the **same three WS-1 verbs** and an absolute authenticated launcher on both machines.
For illustration only, a custodian might specify the Bash spelling
`C:/Approved Kit/<generation>/Scripts/python.exe`; the native invocation spelling
would be the exact `C:\…\Scripts\python.exe` reported by the approved interpreter.
These are examples, not selections. The authority record must bind one exact pair.
A macOS selection ends in `/bin/python`. An explicit `SAS_RE_PYTHON` must be that
same Bash spelling; omitted selects the fixed approved path. Never search PATH, use
`py`/Store aliases, activate an arbitrary venv, or use MSYS/Cygwin/WSL Python.

Pass one quoted argv token per value, including spaces, Unicode, apostrophes and
metacharacters. Never construct a command string or source a manifest. Git Bash
can rewrite argv **after** Bash quoting. The unchanged launcher sets
`MSYS2_ARG_CONV_EXCL=*` only for its native Python children; it probes with
`-I -B -S -X utf8`, then executes `-I -B -X utf8 -m sas_re` plus exactly one
allowed verb. For a future installer convert *only declared installation operands*
once using authenticated tools, supply native spellings to native Python/pip,
and scope any `MSYS2_ENV_CONV_EXCL` to the explicitly carried environment fields.
Do not apply conversion to file keys or evidence paths. Verify the actual Windows
build/argv and trusted SystemRoot/WINDIR, native base executable/DLL identities,
absence of adjacent overrides, path aliases and reparse points; simulation is
insufficient. See [MSYS2's separate argument and environment rules](https://www.msys2.org/docs/filesystem-paths/).

Reject an unauthenticated script **before invoking Bash**, in a trusted parent with
no unapproved shell startup hooks. For an authenticated launcher, wrong/missing/extra
arguments give usage/2 before discovery. Recognized verb without valid bootstrap gives
BLOCKED/2 on stderr with no child stdout. On success preserve child stdout, stderr and
exit separately; record the exit immediately, not that of a formatter or later command.
Illustrative invocation **only after a future grant**, with a separately authenticated
absolute launcher path in `kit_launcher`:
`SAS_RE_PYTHON='C:/Approved Kit/<generation>/Scripts/python.exe' /usr/bin/bash "$kit_launcher" status`.
No activation, unquoted expansion or Git call is needed. Record the immediate child
status (in Bash, `$?` before any other command), not the outcome of a pipeline.
Status/0 can report Windows evidence I/O BLOCKED. An adjacent checksum, matching
`SAS_RE_PYTHON`, or successfully invoking Python directly does not release a kit.

## How an inactive environment could become eligible

1. **Measure under custody.** Quiesce and protect the candidate, ancestors, base and
   approval store against concurrent untrusted writers. Confirm native local backing,
   permissions and no ambiguous aliases. Compute the exact WS-1 companion from the
   independently reconciled environment. Follow [WS-1 framing and limits](WS1_DESIGN.md#trust-bootstrap):
   strict sorted UTF-8 relative POSIX names, NUL, directory marker or lowercase byte/link
   digest, LF. Include empty directories; reject multiply linked regular files, unexpected
   objects, reparses and escaping links. Accept only the precise WS-1 exceptions for POSIX
   interpreter links to the approved base and local `lib64` link. Respect 8 MiB / 65,536
   list entries / 32 components, 128 MiB per regular file and 512 MiB total regular bytes.
   No ad hoc exclusion for a pyc, absolute-path entry point, startup hook or native DLL.
   Check the one permitted setuptools hook against WS-1's pinned digest; reject all other
   `.pth`/editable/startup shadows. If a legitimate installation cannot fit, BLOCK.
2. **Bind without changing the repository.** In a future restricted generation, create the
   separate single-link regular approval record and its sibling `.files` at fixed, external,
   protected paths. The twelve LF-terminated fields bind format/host, exact Bash/native
   executable spellings, resolved base prefix/executable, patch and platform tag,
   executable bytes, root cfg bytes, project version and SHA-256 of the companion. Enforce
   the 64 KiB record/cfg bound and less than 4,096 characters per field. Compare the
   resulting length/hash of **both** files to independent expectations. The native base,
   loader/DLLs, shell and verifier require external authentication before WS-1's first probe;
   hashing a redirector does not authenticate the base image.
3. **Authenticate the last changed byte.** For a *separately authorized* candidate kit,
   take the authenticated unbound WS-1 template. Verify the only differences in its
   kit copy are the two literal delivery slots: approved absolute record path and its
   SHA-256. Require safe literal encoding of the path and pin; ambiguous or executable
   substitutions refuse issuance. Recheck UTF-8, LF/no BOM, complete bytes, size and
   hash **after** binding. The signed outer manifest binds this final hash, the record,
   companion, target/root, generation and release inputs. The record does not hash the
   outer signature or its own final launcher; there is no circular hash. Repository
   slots remain empty. Nothing in WS-2A writes any of these objects.
4. **Authorize trial and release separately.** A custodian/reviewer can request a
   limited trial grant for a frozen challenge generation; it cannot authorize ordinary
   use. Review original native evidence and the exact candidate byte identities before
   requesting release. The accountable human records the allowed target, paths, generation,
   purpose, scope, validity, revocation/rollback rules and restricted evidence reference.
   The offline recipient verifies the independent decision, detached authenticity proof,
   freshness, all manifest digests and protected delivery **before** invoking the bound
   launcher. No automatic promotion of trial fixtures. If final bytes or paths differ from
   the qualified subject, rebind, reauthenticate and requalify before release.
5. **Select only a complete generation.** Keep base, venv, record, companion, launcher and
   outer decision under immutable, versioned locations; never replace their contents in
   place. A protected local administrative selection record identifies the exact authorized
   launcher path/generation. WS-1 does not follow a new selector or implement switching.
   Advance the administrative selection only after the whole generation and its receipt
   are durable and verified. Serialize competing selections; on interruption reconcile
   the previous or new complete decision, never a mixed set or the “newest” directory.
   If the native storage cannot prove these properties, leave selection unchanged or
   unavailable. This concerns kit management only, not CP4 evidence publication.

**Failure and retention.** A failed preflight creates no candidate. A failure after
reservation terminates/waits for installer descendants, freezes a failure receipt
(phase, tuple, inputs, exit, byte mismatches, cleanup), and leaves that candidate
ineligible. Preserve the previous approved base and environment untouched. Remove only
a provably owned inactive generation under a protected parent, after roots/identities
are rechecked; never recursively delete a caller path, symlink, junction, active release
or source/store. If safe cleanup or quiescence cannot be shown, quarantine, record
residue and stop. Keep the prior generation for the human-approved retention period;
rollback requires a **still-current** explicit grant for its entire base/launcher/record,
not just its version string. If no valid prior exists, run nothing. Hash/ACL drift, a
revoked generation, base patch, path move or uncertain crash state invalidates dispatch.

## Decisions and stopping point

| Future decision | Required evidence | Now |
|---|---|---|
| Custody and input authorization | Named custodian, independent reviewer and release approver; offline trust anchor/verifier, protected paths, expiry, revocation and recovery policy | OPEN |
| Tuple and artifact selection | Actual Mac ARM64 / Windows 11 x64 OS/builds, CPython patch/distribution and tool hashes, target path/file system, immutable input and reference wheel/inventory records, capacity and retention | OPEN |
| Windows dependency | Independent acquisition/byte review of the named x64 wheel and separate human approval for the lock change | OPEN; current install BLOCKED |
| Implementation and trials | Separate authorization for any installer implementation; separate approved native lab/workstation, test identities/fixtures, capture, budget and cleanup for each tuple | OPEN; proposed tests NOT_RUN |
| Issuance and activation | Review of all required native controls, signed final handoff and protected generation selection. No production provisioning from a test report | OPEN on both platforms |

A passing install qualifies only that exact kit and tuple for **inspection**. It conveys
no permission to read SAS, LOG/LST, scope or store paths, no Windows publication,
no B1 evaluator isolation, no semantic acceptance and no P4/CP4/CP5 work. Existing
DRAFT / UNVERIFIABLE / BLOCKED / NOT_RUN statuses, canonical identities and downstream
pin remain unchanged. Stop at planning for explicit human review.

## Evidence actually obtained in WS-2A

These were **planning and preservation checks**, not installations. The starting checkout
was clean at the stated baseline. Read-only review covered the four required plans/reports,
actual launcher, package metadata, lock and approval history. PyPI metadata identified
the candidate Windows filename/hash; no Windows wheel bytes or publisher credentials were
obtained. Review of pinned pip source exposed the child-startup and Windows timestamp
requirements above; neither is a demonstrated native result.

| Executed local check | Result |
|---|---|
| Staged path and Git-tree byte/mode comparison against the baseline | Exactly five Markdown files: two new plans; only the approvals, decisions and practice ledgers edited. All **106 other baseline files** matched. No untracked extras. |
| SHA-256 comparisons | Eight frozen hashes, three P3-A1 implementation/oracle/test hashes and both WS-1 launcher/test hashes matched. Both repository launcher slots remain empty; downstream pin unchanged at `bc754e0f1204a99020c864df2a5b25983005e09c`. |
| Read-only comparison of retained WS-1 synthetic replay sets | All 15 P1 + 15 P2A files and both full stdout reports matched byte for byte. Manifest SHA-256: P1 `3b3a6b999ed496b995c2ae055448805a8fbfb746a03edac7192fe128403fa7c6`; P2A `38259743e798bd3d9df6089c1576a31865aa575427710ff73bbc2befee3bb809`. No replay performed locally. |
| Documentation and scope | Local Markdown link/heading targets, UTF-8/LF, table widths, fences, nine locked versions, native lock gap and contiguous I01–I24 tested against the documents. The register has 22 + 24 = 46 proposed native cells; **zero attempted**. |
| `git diff --cached --check`; `.venv/bin/python scripts/check_repository.py` | Both exit 0. The repository guard reports PASS under its tracked-path and selected-secret rules only. |

The accepted WS-1 record reports 722 regression tests in its final macOS and Linux
modes. Those are historical, not new WS-2A workstation results. No local installer,
wheel download/build, native trial, release record, provisioned kit or activated launcher
was produced. Normal publication CI, if run, exercises repository regressions only.
