# CP1 validation record

Baseline: `1c172fbb79a8ba07bf72f2f40ecf0f5db02b564a`.
Scope: import-safe shared code, capability reporting/denial and regression
preservation only. See [CP1 design](CP1_DESIGN.md) and [approval](APPROVALS.md).
Package version remains 0.3.0; identify this change by Git commit, not a new
semantic-engine or artifact version. Native Windows qualification is **BLOCKED**.
Implementation commit: `076f8c4559b9c916065e5e9ae8c2d7a99dd95bb2`.
Subsequent validation-report updates are documentation only.
Semantic acceptance stays **BLOCKED**, authority **DRAFT**, verification
**UNVERIFIABLE** and benchmarks **NOT_RUN**.

## Platforms actually exercised

| Environment | Observed version / execution | Qualification limit |
|---|---|---|
| Local native macOS ARM64 | macOS 26.6.2, Darwin 25.6.0, arm64; CPython 3.12.5, Clang 14.0.0; development and installed wheel | Existing local POSIX environment; no new filesystem/alias/power-loss qualification |
| Simulated Windows selection | Fresh processes on macOS with `sys.platform = "win32"`, forbidden POSIX imports and process/network sentinels; separate metadata-stub tests for `os.name == "nt"` | Tests Python selection/import/denial paths, not a Windows interpreter, paths, ACLs, NTFS or PowerShell |
| Native Windows 11 x64 / NTFS / PowerShell 7 | **BLOCKED / NOT_RUN**: no approved actual Windows interpreter/dependency host available | No dependency installation or lock extension authorized/performed; not a successful Windows acceptance run |
| Hosted Linux x64 | Ubuntu 24.04.5, runner image `ubuntu-24.04` / `20261101.360.1`, CPython 3.12.5 x64; checkout and installed wheel at implementation commit | Existing unchanged Ubuntu workflow; no new Windows/macOS CI matrix or filesystem qualification |
| macOS Intel, Windows ARM64, other OS/filesystem combinations | NOT_RUN | No support extension claimed |

Local environment inventory found no `pwsh`, `powershell`, `wine`, `wine64`,
`wsl` or Windows `py` launcher. Their absence alone is not a universal proof that
no Windows machine exists; no approved native test environment was supplied or
available for this checkpoint. No VM, Docker, emulator or cloud environment was
created. Ordinary core use does not require Git, editor, provider or network.

## Executed checks and results

| Check | Actual result / exit |
|---|---|
| Immutable baseline checkout, all original regressions | 389 tests, OK, exit 0; 14.621 s |
| Final focused CP1 suite | 22 tests, OK, exit 0; 0.914 s in focused run |
| Final development suite | 411 tests = original 389 + 22 CP1; OK, exit 0; 15.611 s; no skips |
| Installed wheel outside checkout | 411 tests, OK, exit 0; 16.362 s; no skips |
| Original versus moved safeio definitions | All 20 function/class ASTs identical, exit 0 |
| Evidence/identity/parser/contract source preservation | Five modules byte-identical to baseline, exit 0 |
| Existing adversarial test preservation | Only private import/patch targets relocated; original assertions/fixtures unchanged, exit 0 |
| Baseline versus candidate P1 demo | 15 sealed artifact files byte-identical; complete demo report JSON identical; expected wrapper exit 0 |
| Baseline versus candidate P2A demo | 15 sealed artifact files byte-identical; complete demo report JSON identical; expected wrapper exit 0 |
| Frozen files | Both schemas, compatibility metadata, ZIP, lock and reviewed expectations byte-identical; hashes below, exit 0 |
| Package build and local wheel install | Exit 0; own package only, no dependency download/install; existing approved wheel environment reused |
| Dependency consistency | `pip check`, development and wheel environments: exit 0, no broken requirements |
| Python compilation | Exit 0 |
| Local downstream baseline | PASS/0; exact pin, clean checkout and all 20 digests match; read-only |
| Staged repository guard and whitespace | PASS/0; no guard findings; both working-tree and staged whitespace checks passed |
| Scope and Markdown check | PASS/0; 18 scoped changed files, 43 other baseline files byte-identical, 38 local links exist, code fences balanced |
| Hosted Ubuntu implementation CI | Both jobs PASS; 411 checkout tests (26.673 s) and 411 installed-wheel tests (26.300 s), both OK; remote downstream pin matched |

Test durations are diagnostics, not SAS workload benchmarks or productivity/cost
measurements. Counts are cumulative and repeat the same suite across environments;
they are not independent semantic samples. The guard checks tracked-file rules
and selected credential formats, not complete DLP. Hosted results below bind the
exact implementation commit; they are distinct from local runs and later commits.

The new tests cover help/version/status and both bundled schemas without POSIX
imports; no Git/process/network on pure paths; explicit Windows/unknown-platform
denial; absent OS and locking primitives; backend load failure; mutable reports
not granting authority; all five direct/CLI evidence workflows; direct low-level
I/O and retained attempt/store objects; local baseline denial before path/Git.
Sentinel inputs remain byte-identical and no output store is created. POSIX-only
prerequisite tests are labeled as such; skipping them on a future Windows host
would not qualify Windows evidence I/O. Original POSIX security tests were not
skipped or weakened.

## Commands executed

Unless stated otherwise, working directory was the repository root:
`/Users/divyasreegundaram/Downloads/sas-migration-skill-enhancement-v2/sas-reverse-engineering`.
Temporary transcripts and synthetic artifacts live outside Git and may expire.

Baseline isolation and regression commands:

```bash
git clone --no-hardlinks . /private/tmp/sas-re-cp1-baseline
git -C /private/tmp/sas-re-cp1-baseline rev-parse HEAD
PYTHONPATH=/private/tmp/sas-re-cp1-baseline/src .venv/bin/python -m unittest discover -s /private/tmp/sas-re-cp1-baseline/tests -v > /private/tmp/sas-re-cp1-baseline-tests.txt 2>&1
.venv/bin/python -m unittest discover -s tests -v > /private/tmp/sas-re-cp1-development-tests.txt 2>&1
.venv/bin/python -m unittest discover -s tests -v > /private/tmp/sas-re-cp1-development-final-tests.txt 2>&1
.venv/bin/python -m unittest discover -s tests -p test_platform_io.py -v
.venv/bin/python -m unittest discover -s tests -v > /private/tmp/sas-re-cp1-development-accepted-tests.txt 2>&1
```

The baseline clone resolved to the exact approved commit. Explicit PYTHONPATH
selected its immutable package source and propagated to demo subprocesses;
existing interpreter/dependencies were reused. The two intermediate development
commands failed as described below; the final `accepted` transcript passed.
Focused test development also retained the initial failed expectation before its
correction. No claim of an additional fresh dependency installation is made.

Synthetic artifact comparison inputs (all four commands exited 0):

```bash
PYTHONPATH=/private/tmp/sas-re-cp1-baseline/src .venv/bin/python /private/tmp/sas-re-cp1-baseline/scripts/p1_demo.py --destination /private/tmp/sas-re-cp1-p1-before > /private/tmp/sas-re-cp1-p1-before.json
PYTHONPATH=/private/tmp/sas-re-cp1-baseline/src .venv/bin/python /private/tmp/sas-re-cp1-baseline/scripts/p2a_demo.py --destination /private/tmp/sas-re-cp1-p2a-before > /private/tmp/sas-re-cp1-p2a-before.json
.venv/bin/python scripts/p1_demo.py --destination /private/tmp/sas-re-cp1-p1-after > /private/tmp/sas-re-cp1-p1-after.json
.venv/bin/python scripts/p2a_demo.py --destination /private/tmp/sas-re-cp1-p2a-after > /private/tmp/sas-re-cp1-p2a-after.json
```

Executed comparison body (`python3 - <<'PY'`), exit 0:

```python
from pathlib import Path
import hashlib,json
for phase in ('p1','p2a'):
    before=Path('/private/tmp/sas-re-cp1-'+phase+'-before')
    after=Path('/private/tmp/sas-re-cp1-'+phase+'-after')
    def snapshot(p): return {str(x.relative_to(p)):x.read_bytes() for x in p.rglob('*') if x.is_file()}
    a,b=snapshot(before/'artifacts'),snapshot(after/'artifacts')
    assert a==b,(phase,set(a)^set(b))
    left=json.loads(before.with_suffix('.json').read_bytes())
    right=json.loads(after.with_suffix('.json').read_bytes())
    assert left==right,phase
    manifest={name:hashlib.sha256(data).hexdigest() for name,data in sorted(a.items())}
    digest=hashlib.sha256((json.dumps(manifest,sort_keys=True,separators=(',',':'))+'\n').encode()).hexdigest()
    print(phase,len(a),'artifact files byte-identical; full demo JSON identical; digest manifest',digest)
    if phase=='p2a': print('source_fingerprint',right['source_fingerprint'],'graph_sha256',right['graph_sha256'])
```

These demos include append-only stale-source failures and preserve historical
seals. P2A reconstruction/check still exit 2 with semantic acceptance BLOCKED;
the wrapper exits 0 because that is the expected outcome. Source mutation tests
use synthetic bytes only. Absolute authorization roots differ between before/
after demo destinations; they do not enter the existing logical identity hash.

Packaging and checks (exit 0):

```bash
.venv/bin/python -m pip check
.venv/bin/python -m compileall -q src tests scripts
.venv/bin/sas-re check-baseline --checkout /private/tmp/sas-re-downstream-bc754e0
.venv/bin/python -m sas_re status
SOURCE_DATE_EPOCH=1793926179 .venv/bin/python -m pip wheel --no-deps --no-build-isolation --wheel-dir /private/tmp/sas-re-cp1-wheel .
/private/tmp/sas-re-p2a-wheel-env/bin/python -m pip install --no-index --no-deps --force-reinstall /private/tmp/sas-re-cp1-wheel/sas_reverse_engineering-0.3.0-py3-none-any.whl
```

From `/private/tmp`, using the existing approved macOS wheel environment:

```bash
/private/tmp/sas-re-p2a-wheel-env/bin/python -c 'import sas_re; print(sas_re.__file__); assert "/site-packages/" in sas_re.__file__'
/private/tmp/sas-re-p2a-wheel-env/bin/python -m unittest discover -s /Users/divyasreegundaram/Downloads/sas-migration-skill-enhancement-v2/sas-reverse-engineering/tests -v > /private/tmp/sas-re-cp1-wheel-tests.txt 2>&1
/private/tmp/sas-re-p2a-wheel-env/bin/python -m pip check
/private/tmp/sas-re-p2a-wheel-env/bin/python -m sas_re status
```

Observed import path:
`/private/tmp/sas-re-p2a-wheel-env/lib/python3.12/site-packages/sas_re/__init__.py`.
Pip warned that the user cache was unwritable and disabled caching; it succeeded
without changing constraints or installing dependencies. No workflow, Python pin,
lockfile, packaging version, downstream pin or demo script was changed.

Preservation script executed with `python3 - <<'PY'`, exit 0:

```python
import ast, hashlib, json, subprocess
from pathlib import Path
base='1c172fbb79a8ba07bf72f2f40ecf0f5db02b564a'
old=ast.parse(subprocess.check_output(['git','show',base+':src/sas_re/safeio.py']))
olddefs={n.name:ast.dump(n,include_attributes=False) for n in old.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
newdefs={}
for name in ('_io_common.py','_posix_io.py'):
    for n in ast.parse(Path('src/sas_re',name).read_text()).body:
        if isinstance(n,(ast.FunctionDef,ast.ClassDef)): newdefs[n.name]=ast.dump(n,include_attributes=False)
assert all(newdefs.get(k)==v for k,v in olddefs.items())
print('PASS:',len(olddefs),'original function/class ASTs unchanged after relocation')
for name in ('evidence.py','semantic.py','sas_subset.py','observations.py','contracts.py'):
    p='src/sas_re/'+name
    assert Path(p).read_bytes()==subprocess.check_output(['git','show',base+':'+p])
print('PASS: five evidence/identity/parser/contract modules byte-identical')
for name in ('tests/test_safeio.py','tests/test_runs.py'):
    current=Path(name).read_text().replace('import sas_re._posix_io as safeio','import sas_re.safeio as safeio').replace('from sas_re import _posix_io as safeio','from sas_re import safeio').replace('patch("sas_re._posix_io.','patch("sas_re.safeio.')
    assert current.encode()==subprocess.check_output(['git','show',base+':'+name])
print('PASS: existing adversarial test changes only relocate private patch targets')
for name in ('src/sas_re/contracts/v1/evidence.schema.json','src/sas_re/contracts/v2/evidence.schema.json','requirements.lock','src/sas_re/data/baseline.json','tests/p2a_expectations.py','reference/Codex_SAS_Architecture_Pack_v2.zip'):
    raw=Path(name).read_bytes(); assert raw==subprocess.check_output(['git','show',base+':'+name])
    print(hashlib.sha256(raw).hexdigest(),name)
```

## Hash evidence

| Subject | SHA-256 |
|---|---|
| Frozen v1 schema | `15e3265fac9af300b40967580998ef4ac90eb1d830a10ce201855fc4ec2738a2` |
| Frozen v2 schema | `093216d16bb02e91a3997c97175420bf2257982f5a5fe3a4374ef92f7637a90b` |
| Dependency lock | `4676c7fe0a41ce2fdb35c2fb10cc014a8b352a8ca71029eb28b7373c0053e19b` |
| Compatibility metadata | `d22af8651c77a0569e9de7ca473e2274c108de14896b23089421100d6aa2e040` |
| Reviewed public expectations | `f42549738a041db87d3547adec59ddfd0f9b15aa2621f1cf0b7ea7fa9f7ffd93` |
| v2 specification ZIP | `e3cbf3d9df6cc20c594261556c5e3ea1dfc292c9c1a30672c2d7b1a736b9718e` |
| CP1 local wheel | `1d6f4976b6b30eccf6db243d1bf68fb381ec2fac97d4e16263419381db8d0859` |
| P1 demo artifact digest manifest, before = after | `947f26a2d6314ef8345046d1d78cd3b0f51561b52e9547bf5051845db6dc612f` |
| P2A demo artifact digest manifest, before = after | `51c40e32e1df0657494f12891bc0277d5b2c4f9daa7b8821bd3adef364e62755` |
| P2A demo original source fingerprint | `c94ab61f4f4f84f885079f7d71aa71c98a4b7118d21c2eb92d4d26b3cbf4ccb4` |
| P2A demo canonical graph | `385423530208b08635de832bed57698b7278490f2cb7a43f08fd754b80df9155` |

The compatibility metadata still pins Agent-mastery
`bc754e0f1204a99020c864df2a5b25983005e09c`. Digest-manifest computation is a local
comparison check shown above, not a new product artifact/contract format.

## Observed hosted validation

`git push origin main` exited 0, advancing `1c172fb` to implementation commit
`076f8c4559b9c916065e5e9ae8c2d7a99dd95bb2`. The existing workflow completed
successfully in [run 42141440804](https://github.com/keshavnath1/sas-reverse-engineering/actions/runs/42141440804).
Both `foundation` and `downstream-drift` passed. The foundation log records the
two 411-test runs above, successful P1/P2A synthetic demos, installed site-packages
validation and status. Expected P2A BLOCKED and stale-source FAIL results remained
unchanged; demo history checks were true. The remote drift log confirms the exact
frozen downstream commit. This is Linux regression evidence, not Windows or
independent semantic qualification.

The unchanged workflow ran its locked binary dependency installation, editable
package install, `python -m pip check`, `python scripts/check_repository.py`,
`python -m unittest discover -s tests -v`, both public demos, then wheel build/
reinstall and the full test suite from outside the checkout. It also ran
`sas-re status`, `python -m sas_re --version` and the separate
`sas-re check-baseline --remote` job. All successful commands/steps exited 0;
demo wrappers explicitly checked expected child exits 0/2/1. Hosted installation
used the existing approved lock, not a dependency update or Windows setup.

Read-only GitHub verification requests:

```text
https://api.github.com/repos/keshavnath1/sas-reverse-engineering/actions/runs?head_sha=076f8c4559b9c916065e5e9ae8c2d7a99dd95bb2&per_page=3
https://api.github.com/repos/keshavnath1/sas-reverse-engineering/actions/runs/42141440804
https://api.github.com/repos/keshavnath1/sas-reverse-engineering/actions/runs/42141440804/jobs
fetch_workflow_job_logs(repo_full_name="keshavnath1/sas-reverse-engineering", job_id=127642440409)
fetch_workflow_job_logs(repo_full_name="keshavnath1/sas-reverse-engineering", job_id=127642439979)
```

This report update does not change the tested implementation. Its subsequent
publication may trigger another unchanged hosted run; that later result is
reported separately rather than assumed from the implementation run.

## Failures, corrections and review

- First original-regression run after moving code: **389 tests, 27 errors,
  exit 1**. `_posix_io.read_attempt` still needed `re` for seal hash validation.
  Restored that import; no function/algorithm or expected artifact was changed.
- First focused run: **16 tests, one failure, exit 1**. The new baseline-denial
  test incorrectly demanded an evidence finding code in the existing baseline
  report shape. It already observed BLOCKED before resolve/Git. Corrected this
  new assertion to require the established baseline BLOCKED/nonempty-reason
  shape; input/mutation sentinels remain. A concurrent full run captured the same
  issue: **405 tests, one failure, exit 1**. All original 389 then passed.
- Read-only review found that checking only fcntl module availability could
  incorrectly report locking available when `flock` or constants were missing.
  Added actual callable/constant checks and four focused absence/import-failure
  tests. An intermediate 18-test focused run passed; final 22-test focused and
  411-test development/wheel runs passed.
- Two patch applications were rejected before application (duplicate target
  operation; unmatched documentation context). Corrected patch structure/context;
  neither changed product behavior or acceptance assertions.
- A read-only audit initially looked for `ci.yml`, then inspected the actual
  `foundation.yml`; no workflow was modified. Final separate boundary review
  found no remaining material CP1 issue. These reviewers share the development
  environment; they are not a protected independent semantic evaluator.

No private intake, SAS execution, new dependencies, Windows installation, provider
calls, isolation deployment or benchmark occurred. No safety control was disabled
to obtain a pass. Actual native Windows qualification is the remaining blocked
acceptance item, explicitly permitted to be reported BLOCKED by the CP1 request.

Final staged checks (exit 0):

```bash
git add AGENTS.md README.md SECURITY.md docs/APPROVALS.md docs/BEST_PRACTICES_ADOPTION.md docs/CP1_DESIGN.md docs/CP1_VALIDATION.md src/sas_re/_io_common.py src/sas_re/_posix_io.py src/sas_re/platform_io.py src/sas_re/safeio.py src/sas_re/baseline.py src/sas_re/cli.py src/sas_re/runs.py src/sas_re/semantic_runs.py tests/test_platform_io.py tests/test_runs.py tests/test_safeio.py
.venv/bin/python scripts/check_repository.py
git diff --check
git diff --cached --check
git diff --cached --stat
```

The scope/link check used the following body with `python3 - <<'PY'`, exit 0:

```python
from pathlib import Path
import re,subprocess
base='1c172fbb79a8ba07bf72f2f40ecf0f5db02b564a'
allowed=set('AGENTS.md README.md SECURITY.md docs/APPROVALS.md docs/BEST_PRACTICES_ADOPTION.md docs/CP1_DESIGN.md docs/CP1_VALIDATION.md src/sas_re/_io_common.py src/sas_re/_posix_io.py src/sas_re/platform_io.py src/sas_re/safeio.py src/sas_re/baseline.py src/sas_re/cli.py src/sas_re/runs.py src/sas_re/semantic_runs.py tests/test_platform_io.py tests/test_runs.py tests/test_safeio.py'.split())
def git(*args): return subprocess.check_output(['git',*args])
changed=set(git('diff','--name-only',base).decode().splitlines())
changed.update(git('ls-files','--others','--exclude-standard').decode().splitlines())
assert changed==allowed,changed^allowed
protected=0
for name in git('ls-tree','-r','--name-only',base).decode().splitlines():
    if name not in allowed:
        assert Path(name).read_bytes()==git('show',base+':'+name),name
        protected+=1
links=0
for name in sorted(allowed):
    if not name.endswith('.md'): continue
    p=Path(name); body=p.read_text(encoding='utf-8')
    assert len(re.findall(r'^```',body,re.M))%2==0,name
    for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)',body):
        if target.startswith(('https://','http://','#','mailto:')): continue
        assert (p.parent/target.split('#',1)[0]).exists(),(name,target)
        links+=1
print(f'PASS: {len(allowed)} scoped files; {protected} other baseline files byte-identical; {links} local links; balanced fences')
```

## Changed files and stop boundary

Created: this report, `docs/CP1_DESIGN.md`, `src/sas_re/_io_common.py`,
`src/sas_re/_posix_io.py`, `src/sas_re/platform_io.py`, `tests/test_platform_io.py`.
Updated: `src/sas_re/safeio.py`, `runs.py`, `semantic_runs.py`, `cli.py`,
`baseline.py`; private patch targets in `tests/test_safeio.py` and `test_runs.py`;
README, SECURITY, AGENTS, approval record and the bounded practice-ledger update.

The actual macOS results establish CP1 regression/denial behavior within the
existing trust model. Native Windows support is not declared; runtime availability
is not a platform/security or semantic approval. CP2–CP5 and P2B/P3 remain
unimplemented and unapproved. Stop after CP1 for human review.
