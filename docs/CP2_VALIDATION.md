# CP2 validation record

Approved baseline: `0061b7bf038f7b36add830912258232f174af197`.
Scope: [CP2 design](CP2_DESIGN.md) and [user approval](APPROVALS.md), independently
versioned input declarations, pure validators and exact legacy identity projection
only. Package version remains 0.3.0; identify this change by its Git commit.
Implementation commit: `bd566e37e33b0aec9fa14e899a0acaa0abc50e77`.
Subsequent validation-record updates are documentation only.
Native Windows qualification is **BLOCKED / NOT_RUN**. Semantic acceptance remains
**BLOCKED**, verification **UNVERIFIABLE**, authority **DRAFT**, benchmarks **NOT_RUN**.

## Actual platforms and qualifications

| Environment | Actual execution | Limits |
|---|---|---|
| Native macOS ARM64 | macOS 26.6.2, Darwin 25.6.0, CPython 3.12.5 / Clang 14.0.0; checkout and installed wheel | Existing approved environment; no new filesystem or physical-alias qualification |
| Windows syntax and selection simulation on macOS | Pure native-string vectors; fresh interpreter forbidding POSIX imports/process/network; `sys.platform="win32"` denial tests | Does not emulate Windows Python, NTFS, ACLs, path lookup or PowerShell |
| Native Windows 11 x64/NTFS/Python 3.12, PowerShell 7 preferred | BLOCKED / NOT_RUN; no approved native host/dependency environment available | No Windows dependencies installed or lock hashes extended |
| Hosted Linux x64 | Ubuntu 24.04.5, image `ubuntu-24.04` / `20261101.360.1`, CPython 3.12.5; checkout and installed wheel at implementation commit | Existing Ubuntu workflow only; no new matrix or P2B infrastructure |
| Other platforms/filesystems | NOT_RUN | No support extension claimed |

The local environment inventory found no `pwsh`, `powershell`, `wine`, `wine64`,
`wsl` or Windows `py` launcher. This is not a claim that no Windows machine exists
elsewhere. No actual approved Windows test environment was supplied or used.
No VM, Docker, WSL, provider, cloud service or Git runtime prerequisite was added.

## Checks actually executed

| Check | Result and exit |
|---|---|
| Immutable approved-baseline checkout | Exact baseline; original **411 tests passed**, 15.670 s, exit 0 |
| Final focused CP2 suite, separate review | **45 tests passed**, 0.552 s, exit 0 |
| Final development checkout | **456 tests passed** (411 original + 45 CP2), 16.043 s, exit 0; no skips |
| Installed wheel outside checkout | **456 tests passed**, 16.541 s, exit 0; no skips |
| Independent identity vectors | 17 tests passed, exit 0; literal preimage and pinned hashes unchanged after candidate execution |
| Path declarations | 12 tests passed, exit 0; no filesystem/process/environment/host lookup |
| Core envelope/contract/denial tests | 16 tests passed in the final focused/full runs; strict JSON, ownership, references, no-I/O sentinels and unchanged Windows CLI denial |
| Original source/test preservation | 61 baseline files checked; 55 unchanged, including all 15 existing production Python files and 13 old test/fixture files; only six scoped existing files changed; exit 0 |
| Frozen schema/ZIP/lock/pin/expectation bytes | All match baseline exactly; hashes below; exit 0 |
| P1 baseline/candidate artifact comparison | 15 artifact files byte-identical and full demo report JSON identical; exit 0 |
| P2A baseline/candidate artifact comparison | 15 artifact files byte-identical and full demo report JSON identical; exit 0 |
| Own-package wheel build/install | Exit 0; no dependency downloads/installation; existing approved wheel environment reused |
| `pip check`, both local environments | Exit 0, no broken requirements |
| Python compilation | Exit 0 |
| Local Agent-mastery baseline | PASS/0; clean pinned checkout and all 20 digests match; read-only |
| Status | Exit 0; existing DRAFT / UNVERIFIABLE / BLOCKED semantics and NOT_RUN benchmarks preserved |
| Final staged guard, docs and whitespace | PASS/0; no guard findings, 15 scoped files, 48 valid local Markdown links, balanced fences, working-tree and staged whitespace checks passed |
| Hosted Linux implementation CI | Both jobs PASS; 456 checkout tests (19.407 s) and 456 installed-wheel tests (18.011 s), both OK; downstream remote pin matched |

Durations are diagnostic test timings, not SAS workload benchmarks, productivity
measurements or independent semantic samples. Repeated suites exercise the same
public tests on different package/platform installations.

## Commands executed

Unless noted, working directory was
`/Users/divyasreegundaram/Downloads/sas-migration-skill-enhancement-v2/sas-reverse-engineering`.
Temporary transcripts, synthetic sources and artifacts are outside Git and may expire.

Baseline and candidate tests:

```bash
git clone --no-hardlinks . /private/tmp/sas-re-cp2-baseline
PYTHONPATH=/private/tmp/sas-re-cp2-baseline/src .venv/bin/python -m unittest discover -s /private/tmp/sas-re-cp2-baseline/tests -v > /private/tmp/sas-re-cp2-baseline-tests.txt 2>&1
.venv/bin/python -m unittest discover -s tests -p test_authorization_paths.py -v
.venv/bin/python -m py_compile tests/cp2_vectors.py tests/test_authorization_identity.py
.venv/bin/python -m unittest discover -s tests -p test_authorization_identity.py -v
.venv/bin/python -m unittest discover -s tests -p test_authorization.py -v > /private/tmp/sas-re-cp2-authorization-tests.txt 2>&1
.venv/bin/python -m unittest discover -s tests -p 'test_authorization*.py' -v > /private/tmp/sas-re-cp2-focused-tests.txt 2>&1
.venv/bin/python -m unittest discover -s tests -p 'test_authorization*.py' -v > /private/tmp/sas-re-cp2-focused-final-tests.txt 2>&1
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -p 'test_authorization*.py' -v
.venv/bin/python -m unittest discover -s tests -v > /private/tmp/sas-re-cp2-development-tests.txt 2>&1
```

The initial core-only run had 16 tests, one failure, exit 1; the initial combined
run had 40 tests, one failure, exit 1. The next combined run passed 40/0; five
additional independent identity cases brought the final focused count to 45.
Failures/corrections are retained below. The baseline checkout used explicit
PYTHONPATH and existing interpreter/dependencies, not a new dependency install.

Synthetic artifact comparison commands, each exit 0:

```bash
PYTHONPATH=/private/tmp/sas-re-cp2-baseline/src .venv/bin/python /private/tmp/sas-re-cp2-baseline/scripts/p1_demo.py --destination /private/tmp/sas-re-cp2-p1-before > /private/tmp/sas-re-cp2-p1-before.json
PYTHONPATH=/private/tmp/sas-re-cp2-baseline/src .venv/bin/python /private/tmp/sas-re-cp2-baseline/scripts/p2a_demo.py --destination /private/tmp/sas-re-cp2-p2a-before > /private/tmp/sas-re-cp2-p2a-before.json
.venv/bin/python scripts/p1_demo.py --destination /private/tmp/sas-re-cp2-p1-after > /private/tmp/sas-re-cp2-p1-after.json
.venv/bin/python scripts/p2a_demo.py --destination /private/tmp/sas-re-cp2-p2a-after > /private/tmp/sas-re-cp2-p2a-after.json
```

These demos include append-only stale-source failures. P2A reconstruction/check
retain expected child exit 2/BLOCKED; stale-source checks exit 1. The demo wrappers
exit 0 when those expected outcomes occur. No SAS or private workload was executed.
No new envelope is passed into an evidence workflow.

Preservation/comparison body executed via `.venv/bin/python - <<'PY'`, exit 0:

```python
from pathlib import Path
import hashlib, json, subprocess
base = '0061b7bf038f7b36add830912258232f174af197'
assert subprocess.check_output(['git', '-C', '/private/tmp/sas-re-cp2-baseline',
                                'rev-parse', 'HEAD'], text=True).strip() == base
names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', base], text=True).splitlines()
allowed = {'AGENTS.md', 'README.md', 'SECURITY.md', 'docs/APPROVALS.md',
           'docs/BEST_PRACTICES_ADOPTION.md', 'pyproject.toml'}
for name in names:
    if name not in allowed:
        assert Path(name).read_bytes() == subprocess.check_output(['git', 'show', base + ':' + name]), name
print('Unchanged baseline files:', len(set(names) - allowed))
for name in ('src/sas_re/contracts/v1/evidence.schema.json',
             'src/sas_re/contracts/v2/evidence.schema.json', 'requirements.lock',
             'src/sas_re/data/baseline.json', 'tests/p2a_expectations.py',
             'reference/Codex_SAS_Architecture_Pack_v2.zip',
             'src/sas_re/contracts/authorization/v1/local-authorization.schema.json',
             'tests/cp2_vectors.py'):
    print(hashlib.sha256(Path(name).read_bytes()).hexdigest(), name)
for phase in ('p1', 'p2a'):
    before = Path('/private/tmp/sas-re-cp2-' + phase + '-before')
    after = Path('/private/tmp/sas-re-cp2-' + phase + '-after')
    def snapshot(p):
        return {str(x.relative_to(p)): x.read_bytes() for x in p.rglob('*') if x.is_file()}
    a, b = snapshot(before / 'artifacts'), snapshot(after / 'artifacts')
    assert a == b, phase
    left = json.loads(before.with_suffix('.json').read_bytes())
    right = json.loads(after.with_suffix('.json').read_bytes())
    assert left == right, phase
    manifest = {name: hashlib.sha256(raw).hexdigest() for name, raw in sorted(a.items())}
    checksum = hashlib.sha256((json.dumps(manifest, sort_keys=True, separators=(',', ':')) + '\n').encode()).hexdigest()
    print(phase, len(a), 'sealed artifact files byte-identical; report identical;', checksum)
    if phase == 'p2a':
        print('P2A source/graph:', right['source_fingerprint'], right['graph_sha256'])
```

A separate read-only reviewer ran
`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python /private/tmp/sas-re-cp2-review-audit.py`
against the same baseline and confirmed the source/frozen-file counts above.
This temporary helper is not a shipped product validator; the reproducible
preservation assertions are included above. The reviewer also exercised 30
malformed-object API calls, eight invalid JSON inputs, both native identity
vectors and rejection of both projections as historical filesystem Scope.

Packaging and local checks, exit 0:

```bash
.venv/bin/python -m pip check
.venv/bin/python -m compileall -q src tests scripts
.venv/bin/sas-re check-baseline --checkout /private/tmp/sas-re-downstream-bc754e0
.venv/bin/python -m sas_re status
.venv/bin/python -c 'import platform, sys; print(platform.platform()); print(platform.mac_ver()); print(sys.version)'
SOURCE_DATE_EPOCH=1793926179 .venv/bin/python -m pip wheel --no-deps --no-build-isolation --wheel-dir /private/tmp/sas-re-cp2-wheel .
```

From `/private/tmp`, using the existing approved macOS environment:

```bash
/private/tmp/sas-re-p2a-wheel-env/bin/python -m pip install --no-index --no-deps --force-reinstall /private/tmp/sas-re-cp2-wheel/sas_reverse_engineering-0.3.0-py3-none-any.whl
/private/tmp/sas-re-p2a-wheel-env/bin/python -c 'import sas_re; print(sas_re.__file__); assert "/site-packages/" in sas_re.__file__'
/private/tmp/sas-re-p2a-wheel-env/bin/python -m unittest discover -s /Users/divyasreegundaram/Downloads/sas-migration-skill-enhancement-v2/sas-reverse-engineering/tests -v > /private/tmp/sas-re-cp2-wheel-tests.txt 2>&1
/private/tmp/sas-re-p2a-wheel-env/bin/python -m pip check
```

Observed package path:
`/private/tmp/sas-re-p2a-wheel-env/lib/python3.12/site-packages/sas_re/__init__.py`.
Pip disabled its unwritable user cache and succeeded without changing constraints
or dependencies. Only this repository's package was reinstalled.

Staged guard and whitespace commands, exit 0:

```bash
git add AGENTS.md README.md SECURITY.md docs/APPROVALS.md docs/BEST_PRACTICES_ADOPTION.md docs/CP2_DESIGN.md docs/CP2_VALIDATION.md pyproject.toml src/sas_re/authorization.py src/sas_re/_authorization_paths.py src/sas_re/contracts/authorization/v1/local-authorization.schema.json tests/cp2_vectors.py tests/test_authorization.py tests/test_authorization_identity.py tests/test_authorization_paths.py
.venv/bin/python scripts/check_repository.py
git diff --cached --check
git diff --check
git diff --cached --stat
```

A Python check over staged Markdown verified all 48 relative link targets exist,
code fences are balanced and the staged scope contains exactly 15 files. The
guard checks tracked private paths/extensions and selected credential formats,
not arbitrary PII or all local untracked data. Environment inspection used
`platform.uname()` and `shutil.which()` for the six Windows-related commands
listed above, without installing or launching them.

## Identity and hash evidence

| Subject | SHA-256 |
|---|---|
| Frozen v1 evidence schema | `15e3265fac9af300b40967580998ef4ac90eb1d830a10ce201855fc4ec2738a2` |
| Frozen v2 evidence schema | `093216d16bb02e91a3997c97175420bf2257982f5a5fe3a4374ef92f7637a90b` |
| Unchanged dependency lock | `4676c7fe0a41ce2fdb35c2fb10cc014a8b352a8ca71029eb28b7373c0053e19b` |
| Unchanged compatibility metadata | `d22af8651c77a0569e9de7ca473e2274c108de14896b23089421100d6aa2e040` |
| Unchanged P2A reviewed expectations | `f42549738a041db87d3547adec59ddfd0f9b15aa2621f1cf0b7ea7fa9f7ffd93` |
| Unchanged specification ZIP | `e3cbf3d9df6cc20c594261556c5e3ea1dfc292c9c1a30672c2d7b1a736b9718e` |
| New authorization schema | `427ce869b05e75227653e6f3dcf99466cfaf5111e2be95242a9da5ee157a08f6` |
| Independent synthetic vector file | `02b4bd89c0bb0e9550c0fb8665738f5db411b2f858b9f261975f50a117da7509` |
| Local CP2 wheel | `d7aedb1fc04b4ce8a072b3b772bef56a0e29aa0147fbeec144570476d9bb9953` |
| P1 artifact digest manifest, before = after | `947f26a2d6314ef8345046d1d78cd3b0f51561b52e9547bf5051845db6dc612f` |
| P2A artifact digest manifest, before = after | `51c40e32e1df0657494f12891bc0277d5b2c4f9daa7b8821bd3adef364e62755` |
| P2A source fingerprint, unchanged | `c94ab61f4f4f84f885079f7d71aa71c98a4b7118d21c2eb92d4d26b3cbf4ccb4` |
| P2A graph hash, unchanged | `385423530208b08635de832bed57698b7278490f2cb7a43f08fd754b80df9155` |

The downstream pin remains `bc754e0f1204a99020c864df2a5b25983005e09c`.
Digest manifests are local comparison evidence, not a new sealed artifact format.

Independent public vector anchor:

- Scope hash, Windows = POSIX = historical v1:
  `ef0f163ba588eeaf5da718a772f9bed73e5180623bbed575011490df43849e65`.
- LF source fingerprint:
  `1f19783d572d34df0711b6548fb9db9779779390f56fecaef04937aff5fa88e5`.
- LF operation ID:
  `op_26432c0b6e4df56acaf0f699c2e36fab87a85f7324ce7f447c71a3b9cd5b5d0b`.

The vector author used frozen algorithms plus an independent hashlib/JSON oracle
before reading candidate code. Parent review kept pinned expectations unchanged;
one API call was corrected to pass the logical declaration rather than the
projected hash input. Pure tests also invoke unchanged `build_inventory`, mocking
only physical authorization and byte transport. They prove four pinned LF/CRLF/
BOM/edited-byte identities, not physical-source authorization.

Source-byte edits leave scope identity unchanged but change the affected file ID,
source fingerprint and source-bound operation IDs. Encoding declarations, ownership,
root/file names, file membership, dependencies and explicit log links affect scope
identity. Metadata/native relocation and set-like order do not. Same decoded
Unicode text under UTF-8/Latin-1 does not collapse byte identities. Unsupported
identity versions fail BLOCKED; there is no unreviewed alternate algorithm or
implicit migration. Future incompatible identities require a new version and
explicit revision mapping under separate approval.

## Failures, corrections and review limits

1. The first core test run blocked all `os.stat` calls, including argparse's trusted
   gettext locale lookup. The second reached trusted installed-package metadata
   lookup and tripped the same overly broad harness. The final test disables
   translation and supplies the already-read package version, preloads trusted
   code/schemas, and keeps all source/store I/O tripwires active. No production
   capability check was relaxed. Existing CP1 all-command sentinel tests also pass.
2. Review identified root-only length checking would miss an overlong joined
   root/file declaration. Added pure full-path length refusal and adversarial
   tests before final regressions; this did not enable path construction/access.
3. Independent test API interpretation was clarified: `validate_logical_scope`
   accepts the logical declaration without `schema_version`; the projection has
   its own schema definition. Only the test call changed, not golden expectations.
4. Documentation patches failed to match existing SECURITY.md/validation sentences
   and were reapplied with correct context; no partial implementation change resulted.
   An inspection tried nonexistent `.github/workflows/ci.yml`; the actual unchanged
   file is `foundation.yml`. The reviewer audit initially used an incorrect
   expectations filename and exited 1, then corrected it and passed. No source
   evidence or test assertion was weakened to hide these tooling failures.

Separate agents reviewed contracts/purity, implemented path checks and authored
independent public vectors; the parent reconciled results. They share the same
development environment. This is not an isolated evaluator or human SAS semantic
certification. No real intake or protected answers were read.

## Observed publication and hosted validation

`git commit -m 'Add CP2 pure local authorization and legacy identity projection'`
and `git push origin main` both exited 0. The push advanced `0061b7b` to
`bd566e37e33b0aec9fa14e899a0acaa0abc50e77` under the user's standing publication
authorization. Hosted [run 42145810724](https://github.com/keshavnath1/sas-reverse-engineering/actions/runs/42145810724)
completed successfully at that exact implementation commit.

Both `foundation` (job `127656877414`) and `downstream-drift`
(job `127656877046`) passed. GitHub API run/job metadata and decoded logs were
inspected through the GitHub connector. The foundation logs record the two
456-test runs above, successful public demos, unchanged history, installed
site-packages assertion and status. Expected stale-source reports contain FAIL;
those are checked negative outcomes, not CI failures. The drift job observed
the exact frozen `bc754e0f1204a99020c864df2a5b25983005e09c` pin.

The existing unchanged workflow executed these checks, all steps exiting 0:

```bash
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

The separate drift job installed the same locked requirements and own package
(`python -m pip install --no-deps --no-build-isolation .`), then ran
`sas-re check-baseline --remote`, exit 0. Hosted Linux dependency installation
used the existing approved lock; it was not a dependency change or Windows setup.
This is actual Linux regression evidence, distinct from local macOS tests,
simulated Windows selection and unavailable native Windows qualification.

## Changed files and stopping boundary

New files:

- `docs/CP2_DESIGN.md`, `docs/CP2_VALIDATION.md`
- `src/sas_re/authorization.py`, `src/sas_re/_authorization_paths.py`
- `src/sas_re/contracts/authorization/v1/local-authorization.schema.json`
- `tests/cp2_vectors.py`, `tests/test_authorization.py`,
  `tests/test_authorization_identity.py`, `tests/test_authorization_paths.py`

Updated files: `AGENTS.md`, `README.md`, `SECURITY.md`, `docs/APPROVALS.md`,
`docs/BEST_PRACTICES_ADOPTION.md`, `pyproject.toml` (bundled schema data only).
No existing production/test Python, historical schema/evidence, workflow, lock,
compatibility pin or Agent-mastery file changed.

Physical alias/permission/volume checks cannot be inferred from strings. Neither
validated declarations nor caller approval references authorize content reads.
The new envelope has no consumer in existing workflows; Windows I/O remains
BLOCKED before source access or store creation. No native Windows qualification,
CP3–CP5, P2B/P3, downstream integration or provider work is introduced. Stop after
CP2 and await human review/approval before any further implementation.
