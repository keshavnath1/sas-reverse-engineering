# CP3A validation record

Approved baseline: `07ddcda5a78a9a2f9f093a94e722532f44e3044b`.
Scope: [separate POSIX preflight](CP3A_DESIGN.md), synthetic fixtures only, no
publication integration or historical persistence change. No Windows access,
dependency/lock change, private intake, SAS execution, P2B/P3 or downstream write.
Authority DRAFT, verification UNVERIFIABLE, semantic acceptance BLOCKED and
benchmarks NOT_RUN remain unchanged.

## Actual environments and current results

Local execution: macOS 26.6.2 build 25G83, Darwin 25.6.0, ARM64, CPython 3.12.5
(Clang 14.0.0), effective UID 501, APFS. The already approved development and wheel
environments were reused; no dependency installed. Native NTFS/PowerShell execution
remains BLOCKED/NOT_RUN. Linux parser injections are distinct from native Linux
execution, which must be recorded separately when observed.

| Check | Observed result |
|---|---|
| Immutable baseline checkout | Exact baseline; 456 tests passed, 15.889 s, exit 0 |
| Final focused preflight suite | 40 tests passed, 0.653 s, exit 0, no skips |
| Final focused filesystem suite | 18 tests passed, 0.005 s, exit 0 |
| Final development suite | 514 tests passed (456 preserved + 58 new), 16.677 s, exit 0, no skips |
| Final installed wheel outside checkout | 514 tests passed, 16.702 s, exit 0, no skips; import path confirmed installed site-packages |
| Baseline/candidate P1 comparison | 15 artifact files byte-identical and complete JSON reports equal; wrappers/comparison exit 0 |
| Baseline/candidate P2A comparison | 15 artifact files byte-identical and complete JSON reports equal; wrappers/comparison exit 0 |
| Existing development/wheel dependency checks | `pip check` exit 0, no broken requirements; pip disabled its unwritable user cache |
| Compilation/status/local downstream check | Exit 0; unchanged statuses, pinned clean downstream and all 20 digests match; read-only |
| Initial staged preservation/docs/guard | Exit 0; 66 baseline files unchanged, 13 scoped files, 73 local links; guard PASS, whitespace clean |

Fresh-checkout and final staged checks are recorded below. Hosted results, if
observed, are reported separately. Test timings are diagnostic, not workload benchmarks,
productivity measures or independent semantic samples.

## Observable security evidence

The new [preflight tests](../tests/test_posix_preflight.py) use an independently
prepared synthetic byte/object inventory and observe actual `os.open`, `os.read`,
`os.close` and descriptor enumeration. They assert all expected regular-file
identities have retained read-only handles before the first source read. Every
open excludes create/truncate/append and uses noninheritable handles; mutation,
path-resolution, fallback file-opening, process and network tripwires remain active
except in explicitly attributed adversary hooks. Kernel procfs metadata has its
own fixed-path/proc-device classification and counter; unknown reads are not exempt.

Actual macOS observations:

- Successful sibling roots and absent/existing sibling stores; returned bytes
  equal independent fixtures, source bytes/mtime/ctime/modes/link counts/IDs unchanged.
- Case variants and NFC/NFD native root spellings identified the same APFS object;
  physical store-overlap denial passed. On case-sensitive systems the tests require
  distinct-sibling behavior instead of indiscriminate case folding.
- Missing/denied final source handles caused zero source-content reads. The native
  mode-000 denial ran under UID 501, not root; permission was restored by fixture
  cleanup, never by the reader.
- Unexpected files, hidden/empty directories and proposed stores inside source
  roots were denied without descending into unauthorized child directories.
- Root/intermediate/file/store-parent replacement, acquisition races, symlinks,
  hardlinks, FIFO, restored-mtime edits, earlier-file mutation and scope changes
  caused explicit denial; all tracked handles closed, including cancellation.
- Original LF/CRLF/BOM/edited-byte vectors retained exact frozen logical/file/source/
  operation identities through the independent existing oracle. Changed bytes
  changed applicable source-bound identities; logical scope hash stayed unchanged.
- A pre-existing sealed sibling store stayed byte-identical; absent stores were
  absent before/after, with no candidate creation/mutation calls observed.

These are real descriptor operations with **in-process observation**, not a
privileged native kernel trace. The observer and reader share an interpreter.
Independent security-review ownership, comprehensive native trace coverage,
administrator/mount adversaries, ACL-writer isolation and arbitrary hostile-writer
snapshot guarantees remain OPEN/BLOCKED. Negative tests do not establish those
broader guarantees or human approval. Access-time effects are not hidden/restored.

## Commands executed

Working directory unless stated:
`/Users/divyasreegundaram/Downloads/sas-migration-skill-enhancement-v2/sas-reverse-engineering`.
Temporary public-synthetic fixtures/logs are outside Git at
`/private/tmp/sas-re-cp3a-validation.x41tAG`; they may expire.

```sh
git rev-parse HEAD
git status --short
.venv/bin/python -c 'import platform,sys,os; print(sys.version); print(platform.platform()); print(platform.uname()); print("euid",os.geteuid())'
sw_vers
.venv/bin/python -m pip check
/private/tmp/sas-re-p2a-wheel-env/bin/python -m pip check
.venv/bin/python -m unittest discover -s tests -p 'test_posix_filesystem.py' -v
.venv/bin/python -m unittest discover -s tests -p 'test_posix_preflight.py' -v > /private/tmp/sas-re-cp3a-validation.x41tAG/focused-preflight.txt 2>&1
.venv/bin/python -m unittest discover -s tests -v > /private/tmp/sas-re-cp3a-validation.x41tAG/development.txt 2>&1
git clone --no-hardlinks . /private/tmp/sas-re-cp3a-validation.x41tAG/baseline > /private/tmp/sas-re-cp3a-validation.x41tAG/baseline-clone.log 2>&1
git -C /private/tmp/sas-re-cp3a-validation.x41tAG/baseline rev-parse HEAD
PYTHONPATH=/private/tmp/sas-re-cp3a-validation.x41tAG/baseline/src .venv/bin/python -m unittest discover -s /private/tmp/sas-re-cp3a-validation.x41tAG/baseline/tests -v > /private/tmp/sas-re-cp3a-validation.x41tAG/baseline-tests.log 2>&1
PYTHONPATH=/private/tmp/sas-re-cp3a-validation.x41tAG/baseline/src .venv/bin/python /private/tmp/sas-re-cp3a-validation.x41tAG/baseline/scripts/p1_demo.py --destination /private/tmp/sas-re-cp3a-validation.x41tAG/p1-baseline > /private/tmp/sas-re-cp3a-validation.x41tAG/p1-baseline.json 2> /private/tmp/sas-re-cp3a-validation.x41tAG/p1-baseline.stderr
PYTHONPATH=/private/tmp/sas-re-cp3a-validation.x41tAG/baseline/src .venv/bin/python /private/tmp/sas-re-cp3a-validation.x41tAG/baseline/scripts/p2a_demo.py --destination /private/tmp/sas-re-cp3a-validation.x41tAG/p2a-baseline > /private/tmp/sas-re-cp3a-validation.x41tAG/p2a-baseline.json 2> /private/tmp/sas-re-cp3a-validation.x41tAG/p2a-baseline.stderr
.venv/bin/python scripts/p1_demo.py --destination /private/tmp/sas-re-cp3a-validation.x41tAG/p1-candidate > /private/tmp/sas-re-cp3a-validation.x41tAG/p1-candidate.json 2> /private/tmp/sas-re-cp3a-validation.x41tAG/p1-candidate.stderr
.venv/bin/python scripts/p2a_demo.py --destination /private/tmp/sas-re-cp3a-validation.x41tAG/p2a-candidate > /private/tmp/sas-re-cp3a-validation.x41tAG/p2a-candidate.json 2> /private/tmp/sas-re-cp3a-validation.x41tAG/p2a-candidate.stderr
```

All listed final commands exited 0. Initial focused failures/corrections are listed
below. Demo child BLOCKED and stale-source FAIL outcomes are expected assertions;
wrappers exit 0 when those outcomes occur. No SAS is executed.

After cleanup review, these final commands also exited 0:

```sh
.venv/bin/python -m unittest discover -s tests -p 'test_posix_preflight.py' -v > /private/tmp/sas-re-cp3a-validation.x41tAG/focused-preflight-final.txt 2>&1
.venv/bin/python -m unittest discover -s tests -p 'test_posix_filesystem.py' -v > /private/tmp/sas-re-cp3a-validation.x41tAG/focused-filesystem-final.txt 2>&1
.venv/bin/python -m unittest discover -s tests -v > /private/tmp/sas-re-cp3a-validation.x41tAG/development-final.txt 2>&1
.venv/bin/python -m compileall -q src tests scripts
.venv/bin/sas-re check-baseline --checkout /private/tmp/sas-re-downstream-bc754e0
.venv/bin/python -m sas_re status
SOURCE_DATE_EPOCH=1793926179 .venv/bin/python -m pip wheel --no-deps --no-build-isolation --wheel-dir /private/tmp/sas-re-cp3a-validation.x41tAG/wheel-final .
```

From `/private/tmp`, reusing the existing approved wheel environment:

```sh
/private/tmp/sas-re-p2a-wheel-env/bin/python -m pip install --no-index --no-deps --force-reinstall /private/tmp/sas-re-cp3a-validation.x41tAG/wheel-final/sas_reverse_engineering-0.3.0-py3-none-any.whl
/private/tmp/sas-re-p2a-wheel-env/bin/python -c 'import sas_re.preflight; print(sas_re.preflight.__file__); assert "/site-packages/" in sas_re.preflight.__file__'
/private/tmp/sas-re-p2a-wheel-env/bin/python -m pip check
/private/tmp/sas-re-p2a-wheel-env/bin/python -m unittest discover -s /Users/divyasreegundaram/Downloads/sas-migration-skill-enhancement-v2/sas-reverse-engineering/tests -v > /private/tmp/sas-re-cp3a-validation.x41tAG/installed-wheel-final.txt 2>&1
```

Only this repository's own package was rebuilt/reinstalled, with no index or
dependency install. The observed path was
`/private/tmp/sas-re-p2a-wheel-env/lib/python3.12/site-packages/sas_re/preflight.py`.
An earlier wheel build used `wheel/` instead of `wheel-final/`; its install and
512-test run also exited 0 (16.696 s). The final rebuild/rerun was necessary after
the cleanup correction; its 514-test count includes the two new cleanup tests.

## Preservation and hash evidence

A separate development agent compared the exact baseline checkout with candidate code
and ran both demos. At that audit instant all 72 baseline tracked files were
unchanged; subsequent edits are scoped documentation only. All existing production
modules, tests, schemas, vectors, workflow and lock remain byte-identical. Native
implementation is three new modules; no identity code was relocated or rewritten.

| Subject | SHA-256 |
|---|---|
| v1 schema | `15e3265fac9af300b40967580998ef4ac90eb1d830a10ce201855fc4ec2738a2` |
| v2 schema | `093216d16bb02e91a3997c97175420bf2257982f5a5fe3a4374ef92f7637a90b` |
| CP2 authorization schema | `427ce869b05e75227653e6f3dcf99466cfaf5111e2be95242a9da5ee157a08f6` |
| requirements.lock | `4676c7fe0a41ce2fdb35c2fb10cc014a8b352a8ca71029eb28b7373c0053e19b` |
| baseline.json | `d22af8651c77a0569e9de7ca473e2274c108de14896b23089421100d6aa2e040` |
| p2a_expectations.py | `f42549738a041db87d3547adec59ddfd0f9b15aa2621f1cf0b7ea7fa9f7ffd93` |
| cp2_vectors.py | `02b4bd89c0bb0e9550c0fb8665738f5db411b2f858b9f261975f50a117da7509` |
| v2 specification ZIP | `e3cbf3d9df6cc20c594261556c5e3ea1dfc292c9c1a30672c2d7b1a736b9718e` |
| P1 artifact digest manifest, before = after | `947f26a2d6314ef8345046d1d78cd3b0f51561b52e9547bf5051845db6dc612f` |
| P2A artifact digest manifest, before = after | `51c40e32e1df0657494f12891bc0277d5b2c4f9daa7b8821bd3adef364e62755` |
| P2A source fingerprint, unchanged | `c94ab61f4f4f84f885079f7d71aa71c98a4b7118d21c2eb92d4d26b3cbf4ccb4` |
| P2A graph hash, unchanged | `385423530208b08635de832bed57698b7278490f2cb7a43f08fd754b80df9155` |
| Final tested local wheel | `bb1fdb2ca6ba41243fce63439f9971e47ccdd7e50192eff9efe7b62d5ba1e430` |

Agent-mastery stays pinned to `bc754e0f1204a99020c864df2a5b25983005e09c` and
unmodified. Digest manifests are local comparisons, not new artifact formats.
The comparison records and exact commands are retained in temporary
`preservation-summary.json` and `preservation-commands.json`.

## Failures, corrections and limits

1. The first preflight test run had 33 tests, 10 failures, exit 1. Seven failures
   came from test spies replacing `os.open`/`scandir`/mutation callables without
   preserving Python capability-set membership. The observer now preserves only
   those actual feature memberships while retaining I/O tripwires. Production
   capability checks were not weakened.
2. Three assertions expected a later mutation diagnostic. Earlier complete
   membership/named-fingerprint checks already denied safely. Tests now require
   the applicable earlier fixed code and retain zero-read/no-store/cleanup checks.
   The corrected 33-test run passed; no historical test or golden vector changed.
3. Expanded 39-test coverage initially had one failure: unavailable writer policy
   returned generic FAIL. Implementation now distinguishes the missing assurance
   as `CP3A_WRITER_POLICY_UNAVAILABLE/BLOCKED`; final 39 passed. A separate reviewer
   observed the same pre-correction 38/39 result, not an additional distinct defect.
4. Review corrected the observer's initial classification of Linux procfs reads
   as source reads. It now verifies fixed metadata-path/descriptor provenance;
   unknown reads still fail. Actual native Linux execution must validate that path.
5. Native API research encountered unavailable Gitiles/guessed-header URLs, then
   used installed SDK and official upstream Linux/glibc definitions. No failed
   source retrieval is treated as implementation evidence.
6. Final review identified suppressed source-close errors and a metadata-close
   loop that could stop before trying remaining handles. Both now attempt every
   close once and report BLOCKED if any result is uncertain; neither retries a
   possibly reused FD. One source test performs real closes then injects EINTR;
   one metadata test injects a three-handle close sequence. They demonstrate the
   failure protocol, not an observed kernel close failure. Hidden-file/directory
   fixture subcases were also added and passed. Final development/wheel reruns
   passed 514; earlier 512-test passes are retained as pre-correction evidence.
7. One validation-document patch used a mismatched lowercase context and failed
   before applying; corrected context applied successfully. This was a tooling
   failure, not a product-test result.

Separate agents reviewed scope/security, implemented filesystem metadata and
authored adversarial tests; the parent integrated the session and policy API.
They share the development environment and are not the still-OPEN named independent
security reviewer. No ACL isolation, privileged trace, Intel macOS, aarch64 Linux,
alternate-volume/mount or hostile-writer snapshot qualification is inferred.

## Changed files and stopping boundary

New: `src/sas_re/preflight.py`, `_posix_preflight.py`, `_posix_filesystem.py`;
`tests/test_posix_preflight.py`, `test_posix_filesystem.py`;
`docs/CP3A_DESIGN.md`, `docs/CP3A_VALIDATION.md`.
Documentation updates: AGENTS.md, README.md, SECURITY.md, APPROVALS.md,
OPEN_DECISIONS.md and BEST_PRACTICES_ADOPTION.md.

No legacy persistence/timing change is introduced. Stop after CP3A and await
explicit further approval. Windows access, CP3B, publication/CP4, CP5, P2B/P3 and
downstream integration remain outside this implementation.

## Fresh checkout and final local preservation

Implementation commit: `05cd886120e86ca37f16caecbdd89fa311053f74`.
Subsequent validation-record updates are documentation only.
A new clean local clone at that exact commit passed **514 tests in 16.035 s**,
exit 0, no skips. Its repository guard passed. Explicit import-path assertions
proved use of the fresh checkout, rather than the development tree or wheel.

Commands (clone from development root; remaining commands from the fresh root):

```sh
git clone --no-hardlinks . /private/tmp/sas-re-cp3a-validation.x41tAG/fresh
git rev-parse HEAD
git status --short
PYTHONPATH=/private/tmp/sas-re-cp3a-validation.x41tAG/fresh/src /Users/divyasreegundaram/Downloads/sas-migration-skill-enhancement-v2/sas-reverse-engineering/.venv/bin/python -c 'import sas_re.preflight; print(sas_re.preflight.__file__); assert sas_re.preflight.__file__.startswith("/private/tmp/sas-re-cp3a-validation.x41tAG/fresh/src/")'
PYTHONPATH=/private/tmp/sas-re-cp3a-validation.x41tAG/fresh/src /Users/divyasreegundaram/Downloads/sas-migration-skill-enhancement-v2/sas-reverse-engineering/.venv/bin/python -m unittest discover -s tests -v > /private/tmp/sas-re-cp3a-validation.x41tAG/fresh-tests.txt 2>&1
/Users/divyasreegundaram/Downloads/sas-migration-skill-enhancement-v2/sas-reverse-engineering/.venv/bin/python scripts/check_repository.py
```

Final local comparison command below exited 0: 66 baseline files unchanged,
13 scoped changed/new files, 73 existing local Markdown links, UTF-8/LF and
balanced fences, both 15-file artifact/report comparisons equal, final wheel hash
matching the table. It reads public development fixtures only; no new artifact
format or source-workload validator is shipped.

```sh
.venv/bin/python - <<'PY'
from pathlib import Path
import hashlib, json, re, subprocess
base = '07ddcda5a78a9a2f9f093a94e722532f44e3044b'
allowed = {'AGENTS.md', 'README.md', 'SECURITY.md', 'docs/APPROVALS.md',
           'docs/OPEN_DECISIONS.md', 'docs/BEST_PRACTICES_ADOPTION.md'}
names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', base], text=True).splitlines()
for name in set(names) - allowed:
    assert Path(name).read_bytes() == subprocess.check_output(['git', 'show', base + ':' + name]), name
changed = subprocess.check_output(['git', 'diff', base, '--name-only'], text=True).splitlines()
assert len(changed) == 13, changed
links = 0
for name in changed:
    if name.endswith('.md'):
        raw = Path(name).read_bytes()
        value = raw.decode('utf-8')
        assert b'\r' not in raw
        assert sum(line.lstrip().startswith('```') for line in value.splitlines()) % 2 == 0
        for target in re.findall(r'\]\(([^)]+)\)', value):
            if '://' not in target and not target.startswith('#'):
                assert (Path(name).parent / target.split('#')[0]).exists(), (name, target)
                links += 1
print('unchanged baseline files', len(set(names) - allowed), 'scoped files', len(changed), 'links', links)
root = Path('/private/tmp/sas-re-cp3a-validation.x41tAG')
for phase in ('p1', 'p2a'):
    def snapshot(folder):
        return {str(p.relative_to(folder)): p.read_bytes() for p in folder.rglob('*') if p.is_file()}
    before = snapshot(root / (phase + '-baseline') / 'artifacts')
    after = snapshot(root / (phase + '-candidate') / 'artifacts')
    assert before == after
    assert json.loads((root / (phase + '-baseline.json')).read_bytes()) == json.loads((root / (phase + '-candidate.json')).read_bytes())
    manifest = {name: hashlib.sha256(raw).hexdigest() for name, raw in sorted(before.items())}
    checksum = hashlib.sha256((json.dumps(manifest, sort_keys=True, separators=(',', ':')) + '\n').encode()).hexdigest()
    print(phase, len(before), 'artifact files and reports identical', checksum)
print('final wheel', hashlib.sha256((root / 'wheel-final/sas_reverse_engineering-0.3.0-py3-none-any.whl').read_bytes()).hexdigest())
PY
```

Repository staging/guard/whitespace commands, exit 0 before implementation commit:

```sh
git add AGENTS.md README.md SECURITY.md docs/APPROVALS.md docs/OPEN_DECISIONS.md docs/BEST_PRACTICES_ADOPTION.md docs/CP3A_DESIGN.md docs/CP3A_VALIDATION.md src/sas_re/preflight.py src/sas_re/_posix_preflight.py src/sas_re/_posix_filesystem.py tests/test_posix_preflight.py tests/test_posix_filesystem.py
.venv/bin/python scripts/check_repository.py
git diff --cached --check
git diff --check
git commit -m 'Add CP3A retained POSIX read-only preflight with explicit policy'
```

These checks are separate from any hosted CI result. A local APFS pass does not
qualify Linux or Windows, and a repository guard is not comprehensive DLP.
