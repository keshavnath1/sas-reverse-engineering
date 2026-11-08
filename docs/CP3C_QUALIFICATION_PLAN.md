# CP3C Windows native qualification plan

Reviewed baseline: `a29af0ec024945b15d31435e7041d45e92278c68`.
This is **planning and security review only**. CP3B is accepted within its limited
simulated-test scope. The [bootstrap design](CP3C_BOOTSTRAP_DESIGN.md) is a proposed
conditional protocol, not a deployed control. No Windows source-content read,
bootstrap, dependency installation, publication or output-store creation is
performed or enabled by this checkpoint. Native qualification remains BLOCKED.

## Actual environment versus proposed target

**Actual Windows environment: NOT SUPPLIED.** No Windows host owner, independent
human security reviewer, runtime bundle, physical volume, fixture custodian or
native observer was supplied. Do not infer them from a GitHub account, macOS user,
development assistant or successful CI run. The exact values below must be
supplied and approved before any native execution; OPEN is not a default approval.

| Manifest field | Required qualification target / actual status |
|---|---|
| Host | Native Windows 11 client, AMD64/x64; actual edition, full build/update revision, host identity and owner OPEN. ARM emulation/Server/WSL/VM results cannot substitute |
| Python | CPython 3.12 x64, approved distribution, exact patch, executable/installer hashes and runtime/CRT versions OPEN. Existing macOS/Linux baseline is 3.12.5; it is not an approved Windows installation |
| Shell | PowerShell 7 x64 preferred; exact patch, binary identity and enterprise policy OPEN. Record actual shell and argument/exit behavior; no policy changes to make tests run |
| Filesystem/backing | One independently approved local fixed NTFS volume with dedicated synthetic anchor; actual root/volume/backing observations, storage inventory/custody, driver/filter versions and owner OPEN |
| NTFS configuration | Record case-sensitive-directory state, 8.3 policy and actual aliases, reparse/provider state, relevant encryption/compression and mount configuration. Initial allowed tuple and evidence OPEN |
| Application token | Ordinary unelevated token, user/group SIDs, integrity level and enabled privileges; actual values OPEN. No backup/restore privilege activation or administrator execution |
| Scope | Exact CP2 declaration hash, metadata inspection grant, root-only candidate, authorized ancestor/name queries, source membership and existing/absent-store cases; all real paths OPEN and kept outside Git |
| Writers | Named custody of effective file/namespace/ACL/storage writers, quiescent interval, revocation/expiry policy and residual threat exclusions OPEN |
| Candidate | Exact approved code/package hashes, offline dependency manifest, Windows native-harness identity and finite expected case list OPEN. CP3B's private fake entry is not a native harness |
| Observation | Named operator, tool/version/hash, privileges, configuration, process/object attribution, timestamp ordering and dropped-event detection OPEN |
| Review/retention | Independent human reviewer, approver, fixture custodian and retention owner/location/access/duration OPEN |

Initially exclude UNC/SMB/network shares, SUBST, cloud/offline/redirected roots,
removable/virtual/ambiguous backing, mounted-folder crossings and unsupported
filesystems. A local-looking NTFS device is not proof of physically attached
storage. Unknown backing or clone identity remains BLOCKED. Broader support needs
separate evidence and authorization. No cloud service, AI provider, Git, Docker,
WSL or administrator token is an ordinary-workstation runtime prerequisite.

## Offline runtime and dependency approval

OBSERVED repository pins (not approved Windows artifacts):

| Role | Pinned versions at the baseline |
|---|---|
| Core validation closure | jsonschema 4.26.0; attrs 26.1.0; jsonschema-specifications 2025.9.1; referencing 0.37.0; rpds-py 2026.9.1; typing-extensions 4.16.0 |
| Existing installer/build tools | pip 25.3; setuptools 80.9.0; wheel 0.45.1 |
| Planner package | sas-reverse-engineering 0.3.0; candidate wheel hash must bind the reviewed code |

`requirements.lock` explicitly contains macOS arm64/manylinux x86_64 `rpds-py`
artifacts, not an approved Windows closure. Compatible win_amd64 artifacts, tags,
hashes, provenance and installation authority are **OPEN**. Do not assert their
availability from a version string, silently add hashes, fetch packages during a
native test, build from source or relax binary/hash checks. No lock or dependency
is changed in CP3C.

Prefer a separately preprovisioned, approved Python environment. If provisioning
is later authorized, the owner must provide an independently verified offline
bundle containing the interpreter/runtime prerequisites, the complete pinned
binary-wheel closure, candidate package, pure contracts/tests and reviewed native
harness. Packaging tools are provisioning/development tools, not runtime Git/build
requirements. Verify every file against the approved manifest before installation;
network access remains unnecessary. A newer 3.12 patch or dependency change needs
its own explicit version/hash decision and regression evidence.

Future approved installation must retain local-only, hash-required, binary-only
restrictions (`--no-index`, approved `--find-links`, `--require-hashes`,
`--only-binary=:all:`), without fallback to an index or compiler. This is a policy
requirement, not an executable install instruction or permission. Python's
[Windows installation guide](https://docs.python.org/3.12/using/windows.html)
describes normal/offline installation and the distinct embeddable distribution;
do not assume the latter is an interchangeable pip-capable environment.
[pip secure installation](https://pip.pypa.io/en/stable/topics/secure-installs/)
and [install options](https://pip.pypa.io/en/stable/cli/pip_install/) describe the
candidate restrictions, not repository-specific approval.

## Execution lanes and authority

| Lane | Ordinary application/test activity after future approval | Separately provisioned activity / boundary |
|---|---|---|
| Pure checks | Help/version/status, bundled-contract/CP2 validation, import safety and logical identity vectors | Approved offline runtime first; no supplied-path I/O. Pure success is not volume authorization |
| Bootstrap/metadata | Root-only candidate, qualified locality/identity checks, retained ancestors, exact membership and absence probes | Explicit metadata inspection grant and storage inventory. No source-content access in this lane |
| Synthetic reader | All metadata checks, all data handles before bytes, bounded original-byte reads and rechecks | Separate explicit synthetic-content qualification scope; current CP3C grants none |
| Owned ordinary fixtures | Execute reader unelevated against prearranged sibling/alias/hardlink/hidden/system/denied-file/race cases where policy permits | Fixture custodian authorizes and records setup/cleanup separately; reader never edits fixtures or repairs permissions |
| Special fixtures | Execute the same unelevated reader | Symlink privilege/Developer Mode, mounted folders, second accounts, 8.3 settings, duplicate/virtual volumes, unknown tags/providers or storage remaps need disposable separately approved setup; never alter production/system drives |
| Observation | Application stays unelevated | Observer may need privileged provisioning; exact method/custody approved separately. Do not install drivers or enable policy ad hoc |
| Positive observer controls | Observe independently generated known events | Separate disposable control directory, never source roots or proposed output store; any create/write/delete control needs explicit future fixture authorization |

Setup privilege does not authorize elevated application execution. A fixture that
cannot be supplied safely remains BLOCKED/NOT_RUN; do not replace it with a passing
skip or rename a fake as native. Standard-user ability to create a junction,
hardlink or ACL varies with policy; record actual requirements rather than assuming
all such setup needs elevation. [Symbolic-link API](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-createsymboliclinkw)
documents the Developer Mode dependency of its unprivileged option; no such setting
is enabled by this plan.

## Positive controls and native adversarial obligations

All rows below are **PROPOSED / native NOT_RUN**. Before future execution, the
custodian/reviewer must freeze the finite individual case manifest, expected exact
diagnostic/exit code, fixture hash, phase boundary and observation assertions.
Rows are test families, not an invented test count or completed denominator.
They refine [CP3 T01–T26](CP3_SECURITY_TEST_PLAN.md); historical test counts in that
plan stay historical. The current preserved regression suite has 596 tests.

| ID / prior family | Required positive and negative native cases | Evidence required before that obligation can pass |
|---|---|---|
| C01 / T01,T23,T26 | Approved pure declarations/imports; missing/forged/stale local grant, wrong host/token/scope and replayed handle/receipt | Pure checks touch no supplied path; invalid authority prevents even candidate metadata lookup; no public handle override |
| C02 / T02,T03,T08,T14 | One approved NTFS root and genuine siblings; wrong root ID, duplicate serial/clone, unsupported/unknown/denied locality query | Same retained handle verified against independent inventory; ambiguous backing stays BLOCKED, not inferred local from errors |
| C03 / T07,T14 | Stable approved drive mapping; per-logon shadow, SUBST, GUID aliases, remap before/during/after bootstrap and ABA | No unapproved-root descent/content; retained relative access cannot redirect; limits of repeated observations recorded under quiescent policy |
| C04 / T04,T05 | Ordinary root/ancestors; root, ancestor, intermediate and leaf symlink/junction/mounted folder/unknown reparse/recall placeholder | Refusal before target descent/content/hydration; outside sentinel and actual namespace trace, no weakened flags |
| C05 / T03,T12 | Exact single/multiple-root scopes; hidden/system files, unexpected empty/deep directories and missing entries | Complete bounded membership before descendants or data rights; unexpected-directory sentinel unread/unentered |
| C06 / T13 | All metadata/data permissions available; denied last metadata file, denied last data file and denied directory listing | Distinct metadata/data-right observations; zero source reads for every incomplete Q2R; no ACL repair or privilege escalation |
| C07 / T06,T19 | Ordinary single-link file; inside/outside hardlinks, new link, nondisk/device/deleted/unsupported object | Relevant type/link/volume checks before bytes and after mutation. Dangerous raw devices are not probed as fixtures |
| C08 / T07,T08,T09 | Existing disjoint sibling store; equal/inside/ancestor store, physical case/Unicode/DOS aliases | Correct two-direction physical ancestry, no store-content read or mutation; shared distant ancestor is allowed |
| C09 / T09 | Truly missing sibling leaf and several missing suffix components; nearest parent equal to/inside source | Native first-component absence and fresh source bindings, correct common-ancestor positive control; zero mkdir/create |
| C10 / T07,T09,T20 | Existing directory/file/reparse under queried spelling, case alias, actual DOS alias, Unicode collision, case-sensitive/unknown parent mode | Every successful native lookup is PRESENT/collision; wrong-type flags cannot fake absence. No Python normalization proof |
| C11 / T09,T13 | Genuine qualified NAME_NOT_FOUND; PATH_NOT_FOUND, NO_SUCH_FILE, access/share/type errors, malformed/partial/pending outcomes | Raw typed status and exact single-component call. Only reviewed absence status eligible; all unknown results BLOCKED |
| C12 / T09,T10,T18 | Stable retained parent; rename/replacement, unexpected parent, insertion/alias creation/removal after negative probe | Whole-session invalidation on observed change; explicitly expose final-check/ABA limits. Absence never reserves a name |
| C13 / T10,T11,T16 | Stable root/file handles; replacements before/during metadata and data acquisition, append/truncate/same-length edit/restored mtime | New/replacement sentinel never read before identity checks; relevant mutation denies result; no silent rebind |
| C14 / T03,T20,T22 | 0,1,65535,65536,65537-byte and multi-chunk binary/CRLF/BOM data; EOF/rewind; size limits and short final reads | Exact independent original bytes/hashes and offset trace. No normalization; unchanged logical vectors agree across bindings |
| C15 / T17,T18 | Quiescent positive control; conflicting ordinary write/delete handles and surviving writable mapped views | Real share behavior and residual writer limits recorded; no atomic snapshot claim or weaker sharing retry |
| C16 / T02,T12,T20 | Real empty/multi-batch enumeration, hidden/system names, dots, alias/case flags and exact boundaries | SDK/runtime layout and restart/termination proof; malformed record injections separately labeled unit-only, never native-driver qualification |
| C17 / T20,T21 | Repeated successful sessions, failures at acquisition/read/recheck, cancellation after return, handle reuse and child process | Per-object ownership/rights/inheritance/close trace; every resource accounted for, uncertainty blocks success, no double-close |
| C18 / T02,T21 | Expected synchronous completion; safe reviewed blocking, unexpected completion and cancellation cases | Buffers/status/handles remain live until actual completion. Native pending/cancellation/deadline assumptions resolved or BLOCKED |
| C19 / T24,T25,T26 | Pure installed commands offline; every full Windows evidence command; existing regressions in available POSIX environments | Windows workflows BLOCKED/2 before input/store access; all 596 tests (including Windows unit/simulated cases) and frozen bytes preserved; no runtime Git/cloud/provider |
| C20 / observation controls | Independent known metadata/read and separately authorized control-directory write/create/delete events | Observer correctly attributes process/children, object types, masks, ordering and losses; failed observer control blocks all affected security conclusions |

Case/DOS aliases must exist in the independently inventoried fixture. A machine
where 8.3 generation is disabled cannot count an uncreated alias case as passed.
At least one end-to-end native alias case must use a spelling admitted by frozen
CP2. A `~` name rejected by CP2 tests pure validation only; separately identify
private native-lookup cases and any custodian-provisioned admissible alternate name.
Do not enable 8.3, change case settings, attach volumes or manipulate mappings on
an unapproved host just to complete the matrix. Negative fixtures and native
runtime results must be distinguishable from parser/status injections.

## Independent evidence and acceptance criteria

Before each run, a custodian freezes a source/namespace oracle independent of the
candidate: original bytes and hashes, exact long/short names, object/volume IDs,
link counts, lengths, relevant times, ACL/token context, parent relationships,
outside sentinels and absent-store expectation. The oracle's own reads/setup are
attributed separately. Raw host paths/IDs/traces remain outside Git and portable
canonical artifacts, under the approved retention policy.

An independently reviewed observer must show native operation, object type,
requested rights, handle/acquisition identity, result and ordering for candidate
and children. Directory LIST_DIRECTORY and file READ_DATA share a bit value;
classification must use object type. A candidate READY marker or Python mock is
not the ordering oracle. A metadata handle is not read readiness.
[Process Monitor](https://learn.microsoft.com/en-us/sysinternals/downloads/procmon)
is one possible provisioned observer, not an approved dependency or proof that
all required events are visible. Tool choice and coverage remain OPEN.

Acceptance requires all of the following for the exact approved tuple:

- Named owner/reviewer, authenticated local inspection scope and independently
  accepted physical-volume inventory. Every required API assumption and result
  layout reviewed; no unsupported mapping/volume fallback.
- Positive controls succeed and every scheduled native adversarial case yields its
  frozen result. Report scheduled/executed/passed/failed/blocked counts separately;
  any missing required fixture/observer/approval keeps qualification BLOCKED.
- Independent call order proves all Q2 metadata/membership obligations before data
  opens and every Q2R read handle before the first source byte, including denied
  final-file cases. Exact ACLs should deny READ_DATA while preserving required
  metadata/SYNCHRONIZE; a broad generic deny may test the wrong stage.
- No reader create/write/delete/ACL-change request or output-store creation on
  any path. Compare source bytes/names/IDs/relevant security metadata before/after
  **and** inspect full event traces: matching final bytes/absence alone misses
  write-and-restore/create-and-delete. Separate adversary mutations and OS-managed
  access-time effects; never restore timestamps or permissions to hide changes.
- Every acquired handle/buffer accounted for on success/failure/cancellation.
  Aggregate process handle counts alone are insufficient. An uncertain close is
  a blocked outcome, not a proven leak-free close. Unit cancellation after return,
  native completion and OS process-termination cleanup are distinct claims.
- No cross-platform source/graph identity drift, frozen-schema change, historical
  seal mutation, human-approval claim or legacy POSIX persistence change. Native
  values never enter graph hashes or portable sealed artifacts.
- Independent human review binds the exact code, host, fixture manifest, native
  traces, failures/corrections/reruns and exclusions. Development-agent reviews
  and API documentation cannot sign off native security or SAS semantics.

Repeated observations do not create a snapshot or reserve absent names. Any
required hostile-writer, cancellation deadline, ambiguous-volume or namespace
assurance that cannot be established must remain BLOCKED. Independent semantic
acceptance is still BLOCKED, artifact authority DRAFT, verification UNVERIFIABLE
and benchmarks NOT_RUN irrespective of filesystem test results.

## Proposed gated sequence and native instructions

1. Review the CP3C documents and resolve CP3C-D01–D08 as applicable. Accepting a
   plan does not authorize implementation, provisioning or execution.
2. Supply named owners/reviewer and the exact host/runtime/storage/authority
   manifest. Separately approve offline provisioning, any hash extensions,
   special fixtures/observer and finite test obligations. No such approval exists.
3. Separately authorize only the reviewed bootstrap/absence/completion-lifetime
   implementation and its private native qualification harness. Keep public
   Windows access and publication blocked. No harness command is invented here.
4. In the approved actual Windows environment, run pure installed-package controls
   first. Then qualify the observer and metadata-only bootstrap/absence cases.
   Stop on missing/failed prerequisites; do not bypass gates to reach reader tests.
5. Only with separate explicit synthetic source-content qualification authority,
   run Q2/Q2R/read cases and all remaining native obligations. Preserve full POSIX
   regressions on the already supported environments. Do not prune a failing
   POSIX suite on Windows and call the remainder a platform pass.
6. Freeze complete evidence and independent reviewer disposition; stop for human
   acceptance of the bounded tuple. Public reader activation, CP4 publication,
   CP5 release qualification, P2B and P3 remain separate approvals.

After approval/provisioning, these **existing pure commands** can be used from
PowerShell with independently supplied approved paths; they are NOT_RUN here:

```powershell
# $Cp3cPython and $Cp3cTests must come from the approved bundle manifest.
$PSVersionTable.PSVersion
& $Cp3cPython -c "import platform,sys; print(sys.version); print(platform.platform()); print(platform.machine())"
$LASTEXITCODE
& $Cp3cPython -m sas_re --help
$LASTEXITCODE
& $Cp3cPython -m sas_re --version
$LASTEXITCODE
& $Cp3cPython -m sas_re status
$LASTEXITCODE
& $Cp3cPython -m unittest discover -s $Cp3cTests -p 'test_authorization*.py' -v
$LASTEXITCODE
```

Stop after any unexpected exit; capture `$LASTEXITCODE` immediately, not after
another native command. Existing pure authorization tests comprise 45 cases;
freeze the approved bundle count before execution. Status must continue reporting
Windows reader/publication BLOCKED and unchanged authority. Do not call the
private fake adapter with real handles or invent a `--force-windows` flag. Exact
native harness/provisioning commands, native case count and owner names are OPEN.

## Actual checks for this planning checkpoint

The following section records executed documentation/preservation checks, separate
from every proposed Windows command/case above. No Windows API, source-content
read, output store, new fixture or dependency is created by the local planning
checks. Existing hosted regression CI, if observed, is reported as POSIX synthetic
validation, not Windows qualification. Detailed results are appended after checks
complete; no result is inferred from the plan or previous test counts.

### Observed local results

Local review/check environment: macOS 26.6.2 build 25G83, ARM64, CPython 3.12.5
(Clang 14.0.0), using the existing `.venv`. No dependency installed. All commands
below ran from
`/Users/divyasreegundaram/Downloads/sas-migration-skill-enhancement-v2/sas-reverse-engineering`.

| Executed check | Actual result |
|---|---|
| `git rev-parse HEAD`; initial `git status --short` | Exit 0; exact accepted baseline, clean checkout before edits |
| `.venv/bin/python -c 'import platform,sys; print(sys.version); print(platform.platform()); print(platform.machine())'`; `sw_vers` | Exit 0; environment above, no Windows host |
| Required-document/native-code/lock/workflow review and primary API retrieval | Read-only; three focused development reviews. API contradictions and missing proof are recorded, not represented as qualification |
| Static AST method inspection | 411 direct `test_` definitions; not the suite count because existing tests generate additional methods |
| Discovery-only command below | Exit 0; 596 tests discovered, no tests executed and no fixtures run |
| Preservation/documentation command below | Exit 0; 82 existing baseline files byte-identical, exactly six Markdown changes, 57 valid local links; UTF-8/LF and balanced fences |
| `git diff --check`; `git diff --cached --check` | Exit 0, no whitespace errors |
| Staged `scripts/check_repository.py` | Exit 0, PASS with no errors; tracked paths/selected secret patterns only, not complete DLP |

No full suite, demo, native Windows API, new security fixture, source intake,
artifact-store creation, wheel build/install or external historical-store scan was
run locally in this planning checkpoint. Source/test/schema/workflow/lock bytes
are preserved; CP3B's earlier sealed-artifact comparisons remain historical results,
not new replay evidence. Hosted existing POSIX regression CI is classified
separately below if observed; it uses its existing disposable synthetic fixtures.

Discovery-only command actually executed:

```sh
.venv/bin/python - <<'PY'
import unittest
suite = unittest.defaultTestLoader.discover('tests')
assert not unittest.defaultTestLoader.errors, unittest.defaultTestLoader.errors
assert suite.countTestCases() == 596, suite.countTestCases()
print('596 tests discovered; no tests executed, no fixtures run')
PY
```

Preservation/documentation command actually executed:

```sh
.venv/bin/python - <<'PY'
import hashlib, json, re, subprocess
from pathlib import Path
baseline = 'a29af0ec024945b15d31435e7041d45e92278c68'
edited = {'AGENTS.md', 'docs/APPROVALS.md', 'docs/OPEN_DECISIONS.md', 'docs/BEST_PRACTICES_ADOPTION.md'}
added = {'docs/CP3C_BOOTSTRAP_DESIGN.md', 'docs/CP3C_QUALIFICATION_PLAN.md'}
paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', baseline], text=True).splitlines()
protected = 0
for name in paths:
    if name not in edited:
        assert Path(name).read_bytes() == subprocess.check_output(['git', 'show', baseline + ':' + name]), name
        protected += 1
changed = set(subprocess.check_output(['git', 'diff', baseline, '--name-only'], text=True).splitlines())
assert changed == edited | added, changed
assert not subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], text=True).strip()
links = 0
for name in sorted(edited | added):
    data = Path(name).read_bytes()
    text = data.decode('utf-8')
    assert b'\r' not in data and data.endswith(b'\n'), name
    assert sum(line.lstrip().startswith('```') for line in text.splitlines()) % 2 == 0, name
    for target in re.findall(r'\]\(([^)]+)\)', text):
        if '://' not in target and not target.startswith('#'):
            assert (Path(name).parent / target.split('#')[0]).exists(), (name, target)
            links += 1
print('PASS:', protected, 'baseline files byte-identical;', len(changed), 'Markdown-only changes;', links, 'local links')
for name in ['src/sas_re/contracts/v1/evidence.schema.json', 'src/sas_re/contracts/v2/evidence.schema.json', 'src/sas_re/contracts/authorization/v1/local-authorization.schema.json', 'requirements.lock', 'src/sas_re/data/baseline.json', 'tests/cp2_vectors.py', 'tests/p2a_expectations.py', 'reference/Codex_SAS_Architecture_Pack_v2.zip']:
    print(hashlib.sha256(Path(name).read_bytes()).hexdigest(), name)
assert json.loads(Path('src/sas_re/data/baseline.json').read_text())['downstream']['commit'] == 'bc754e0f1204a99020c864df2a5b25983005e09c'
PY
```

Staging/guard commands actually executed:

```sh
git add AGENTS.md docs/APPROVALS.md docs/OPEN_DECISIONS.md docs/BEST_PRACTICES_ADOPTION.md docs/CP3C_BOOTSTRAP_DESIGN.md docs/CP3C_QUALIFICATION_PLAN.md
.venv/bin/python scripts/check_repository.py
git diff --cached --check
```

| Preserved item | Observed SHA-256 |
|---|---|
| v1 schema | `15e3265fac9af300b40967580998ef4ac90eb1d830a10ce201855fc4ec2738a2` |
| v2 schema | `093216d16bb02e91a3997c97175420bf2257982f5a5fe3a4374ef92f7637a90b` |
| CP2 authorization schema | `427ce869b05e75227653e6f3dcf99466cfaf5111e2be95242a9da5ee157a08f6` |
| requirements.lock | `4676c7fe0a41ce2fdb35c2fb10cc014a8b352a8ca71029eb28b7373c0053e19b` |
| downstream metadata | `d22af8651c77a0569e9de7ca473e2274c108de14896b23089421100d6aa2e040` |
| CP2 vectors | `02b4bd89c0bb0e9550c0fb8665738f5db411b2f858b9f261975f50a117da7509` |
| P2A expectations | `f42549738a041db87d3547adec59ddfd0f9b15aa2621f1cf0b7ea7fa9f7ffd93` |
| v2 specification ZIP | `e3cbf3d9df6cc20c594261556c5e3ea1dfc292c9c1a30672c2d7b1a736b9718e` |

Review corrections: clarified that a directory type does not establish a volume
root; valid zero-valued bitmasks need field-specific interpretation; native alias
cases must reach native lookup rather than only CP2's `~` rejection; test discovery
is distinct from AST counts and test execution; completion/buffer lifetime is a
separate security gate. No code or test expectation was changed. No executed local
validation check failed; the reported API documentation conflicts remain unresolved.

Changed files: new `docs/CP3C_BOOTSTRAP_DESIGN.md` and
`docs/CP3C_QUALIFICATION_PLAN.md`; updates only to `AGENTS.md`,
`docs/APPROVALS.md`, `docs/OPEN_DECISIONS.md` and
`docs/BEST_PRACTICES_ADOPTION.md`. No implementation or dependency changes.
Stop after planning for explicit approval; the Windows reader stays BLOCKED.

### Observed hosted regression CI

The unchanged workflow passed for planning commit
`6343cce966b66b7424d526ef50b93a5d49c10b87` in
[run 42163128965](https://github.com/keshavnath1/sas-reverse-engineering/actions/runs/42163128965)
on 2026-11-06 UTC. Both `foundation` and `downstream-drift` completed successfully.
Observed runner: Ubuntu 24.04.5 x64, image `20261101.360.1`, CPython 3.12.5.
This is Linux regression evidence, not native Windows qualification.

The following existing workflow commands completed with exit 0:

```sh
python -m pip install --require-hashes --only-binary=:all: -r requirements.lock
python -m pip install --no-deps --no-build-isolation -e .
python -m pip check
python scripts/check_repository.py
python -m unittest discover -s tests -v
python scripts/p1_demo.py --destination "$RUNNER_TEMP/synthetic-p1"
python scripts/p2a_demo.py --destination "$RUNNER_TEMP/synthetic-p2a"
python -m pip wheel --no-deps --no-build-isolation --wheel-dir dist .
python -m pip install --no-deps --force-reinstall dist/*.whl
cd "$RUNNER_TEMP"
python -c 'import sas_re; assert "site-packages" in sas_re.__file__, sas_re.__file__'
python -m unittest discover -s "$GITHUB_WORKSPACE/tests" -v
python "$GITHUB_WORKSPACE/scripts/p2a_demo.py" --destination "$RUNNER_TEMP/synthetic-p2a-wheel"
sas-re status
python -m sas_re --version
```

Development: **596 tests, OK**, 31.658 seconds. Installed wheel: **596 tests,
OK**, 32.555 seconds. These elapsed test times are not workload benchmarks.
Existing synthetic POSIX demos also passed. They create disposable synthetic
artifacts on the hosted Linux runner; no Windows content, publication or store
operation was enabled or executed. No dependencies or workflow configuration
were changed; CI installed the existing locked dependencies as it already does.

The separate drift job ran the same locked-dependency install, then
`python -m pip install --no-deps --no-build-isolation .` and
`sas-re check-baseline --remote`, all exit 0. Its reported expected and observed
downstream commit both equal `bc754e0f1204a99020c864df2a5b25983005e09c`,
with `stage_gate: PASS`. This is a read-only compatibility check, not downstream
integration or approval. There were no failed CI jobs or test failures in this run.

This section is a documentation-only result record added after that run; the
referenced run qualifies the exact commit above, not a future revision. All
proposed CP3C native cases remain NOT_RUN and native qualification remains BLOCKED.
