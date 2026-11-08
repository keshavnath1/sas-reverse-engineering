# P1 validation record

Result: **PASS for the approved synthetic P1 structural scope**. Semantic
verification remains **UNVERIFIABLE**; artifact authority **DRAFT**; benchmarks
**NOT_RUN**. No P2 implementation, SAS execution or downstream modification.

Validated on 2026-11-05 against implementation commit
`0e1f6822871d3aa6956695a776672b63454c7958` (package `0.2.0`). This report is a
subsequent documentation-only commit; obtain its final SHA with `git rev-parse HEAD`.
The implementation commit was pushed to the authorized `origin/main` successfully.

## Environment and outcomes

Local: macOS 26.6.2 (25G83), arm64, Python 3.12.5,
Git 2.50.1 (Apple Git-155). Dependency/tool versions and wheel hashes are in
`requirements.lock`; no unpinned build isolation was used. Fresh and wheel
virtual environments installed the complete lock offline with hash checking.

| Environment | Tests | Exit | Observed result |
|---|---:|---:|---|
| Original development checkout | 138 | 0 | PASS, 4.783 seconds |
| Fresh Git checkout and fresh virtual environment | 138 | 0 | PASS, 5.360 seconds |
| Installed wheel, working directory `/private/tmp` | 138 | 0 | PASS, 5.139 seconds |
| Independent agent review, development checkout | 138 | 0 | PASS, 4.860 seconds; no remaining blocking code findings |

Times above are test-suite durations, not workload performance measurements.
Every suite includes 25 P0 regression tests, 19 contract tests, 43 evidence tests,
22 workflow/CLI tests and 29 safe-filesystem/publication tests. The P0 status test
was updated to expect the now-implemented P1 phase while retaining its no-semantic
claim checks. Remaining future commands still reject inputs without reading them.

`pip check`, repository guard, syntax compilation, staged whitespace check,
workflow YAML parse, local downstream baseline and network-enabled remote drift
check all exited 0. Local baseline checked 20 digests, exact pinned HEAD and clean
worktree. The remote branch still resolved to the same pinned commit.

Hosted CI status is recorded below separately from local results.

## Exact local commands

Commands below are grouped by working directory; environment variables are only
readability aliases for the actual absolute paths. All commands exited 0 unless
explicitly recorded otherwise. Redirection retained the full test transcripts
outside Git. These temporary paths may disappear; the tests and fixture generator
are committed for reproduction. Use new empty destinations on repetition.

Development directory:
`/Users/divyasreegundaram/Downloads/sas-migration-skill-enhancement-v2/sas-reverse-engineering`

```bash
.venv/bin/python -m pip install --no-index --find-links /tmp/sas-re-p1-wheels --require-hashes --only-binary=:all: -r requirements.lock
.venv/bin/python -m pip install --no-deps --no-build-isolation -e .
.venv/bin/python -m pip check
.venv/bin/python -m unittest discover -s tests -v > /private/tmp/sas-re-p1-development-tests.txt 2>&1
.venv/bin/python scripts/p1_demo.py --destination /private/tmp/sas-re-p1-demo-final > /private/tmp/sas-re-p1-demo-output.json
.venv/bin/sas-re check-baseline --checkout /private/tmp/sas-re-downstream-bc754e0
.venv/bin/sas-re check-baseline --remote
.venv/bin/python -m compileall -q src scripts tests
.venv/bin/python scripts/check_repository.py
git diff --cached --check
ruby -e 'require "yaml"; YAML.load_file(".github/workflows/foundation.yml"); puts "workflow YAML parsed"'
SOURCE_DATE_EPOCH=1793906985 .venv/bin/python -m pip wheel --no-deps --no-build-isolation --wheel-dir dist .
shasum -a 256 dist/sas_reverse_engineering-0.2.0-py3-none-any.whl
```

The guard was run after staging all 23 implementation files. The remote command's
first restricted-network invocation returned BLOCKED/exit 2; the identical
network-authorized retry returned PASS/exit 0. No compatibility pin was changed.

Fresh checkout setup, from `/private/tmp`:

```bash
git clone --no-hardlinks /Users/divyasreegundaram/Downloads/sas-migration-skill-enhancement-v2/sas-reverse-engineering /private/tmp/sas-re-p1-fresh
/opt/homebrew/bin/python3.12 -m venv /private/tmp/sas-re-p1-fresh-env
/private/tmp/sas-re-p1-fresh-env/bin/python -m pip install --no-index --find-links /private/tmp/sas-re-p1-wheels --require-hashes --only-binary=:all: -r /private/tmp/sas-re-p1-fresh/requirements.lock
/private/tmp/sas-re-p1-fresh-env/bin/python -m pip install --no-deps --no-build-isolation -e /private/tmp/sas-re-p1-fresh
cd /private/tmp/sas-re-p1-fresh
/private/tmp/sas-re-p1-fresh-env/bin/python -m pip check
/private/tmp/sas-re-p1-fresh-env/bin/python -m unittest discover -s tests -v > /private/tmp/sas-re-p1-fresh-tests.txt 2>&1
/private/tmp/sas-re-p1-fresh-env/bin/python scripts/check_repository.py
/private/tmp/sas-re-p1-fresh-env/bin/python scripts/p1_demo.py --destination /private/tmp/sas-re-p1-demo-fresh > /private/tmp/sas-re-p1-demo-fresh-output.json
git status --porcelain
```

The fresh clone selected `0e1f6822871d3aa6956695a776672b63454c7958`; final porcelain
output was empty. Git objects were copied without hardlinks.

Installed wheel setup/checks, from `/private/tmp`:

```bash
P1_CHECKOUT=/Users/divyasreegundaram/Downloads/sas-migration-skill-enhancement-v2/sas-reverse-engineering
/opt/homebrew/bin/python3.12 -m venv /private/tmp/sas-re-p1-wheel-env
/private/tmp/sas-re-p1-wheel-env/bin/python -m pip install --no-index --find-links /private/tmp/sas-re-p1-wheels --require-hashes --only-binary=:all: -r "$P1_CHECKOUT/requirements.lock"
/private/tmp/sas-re-p1-wheel-env/bin/python -m pip install --no-deps "$P1_CHECKOUT/dist/sas_reverse_engineering-0.2.0-py3-none-any.whl"
/private/tmp/sas-re-p1-wheel-env/bin/python -m pip check
/private/tmp/sas-re-p1-wheel-env/bin/python -c 'import sas_re; print(sas_re.__file__); assert "/site-packages/" in sas_re.__file__'
/private/tmp/sas-re-p1-wheel-env/bin/python -m unittest discover -s /private/tmp/sas-re-p1-fresh/tests -v > /private/tmp/sas-re-p1-wheel-tests.txt 2>&1
/private/tmp/sas-re-p1-wheel-env/bin/python /private/tmp/sas-re-p1-fresh/scripts/p1_demo.py --destination /private/tmp/sas-re-p1-demo-wheel > /private/tmp/sas-re-p1-demo-wheel-output.json
/private/tmp/sas-re-p1-wheel-env/bin/sas-re status
/private/tmp/sas-re-p1-wheel-env/bin/python -m sas_re --version
```

Observed import:
`/private/tmp/sas-re-p1-wheel-env/lib/python3.12/site-packages/sas_re/__init__.py`.
The tests remain in the fresh checkout so their P0 Git/reference tests can run;
application code and schema/baseline resources came from the installed wheel.
CLI version was `0.2.0`, phase `P1`, semantics `UNVERIFIABLE`.

The demonstration report equality check was executed from the development checkout:

```bash
.venv/bin/python - <<'CHECK'
import json
from pathlib import Path
runs = [json.loads(Path(p).read_text()) for p in (
    '/private/tmp/sas-re-p1-demo-output.json',
    '/private/tmp/sas-re-p1-demo-fresh-output.json',
    '/private/tmp/sas-re-p1-demo-wheel-output.json')]
assert runs[0] == runs[1] == runs[2]
print('All three complete synthetic demo reports are identical.')
CHECK
```

Observed identical complete JSON results, including seal hashes, across all three.
Each demo invokes the installed CLI four times: discover `PASS/0`, seal-source
`PASS/0`, verify-source `PASS/0`, then verify-source after changing an include
`FAIL/1`. The demo wrapper exits 0 because the expected stale failure occurred.
All original sealed attempt files remained byte-identical.

## Hash evidence

| Artifact | SHA-256 |
|---|---|
| v2 specification ZIP | `e3cbf3d9df6cc20c594261556c5e3ea1dfc292c9c1a30672c2d7b1a736b9718e` |
| v1 schema bundle | `15e3265fac9af300b40967580998ef4ac90eb1d830a10ce201855fc4ec2738a2` |
| requirements.lock | `4676c7fe0a41ce2fdb35c2fb10cc014a8b352a8ca71029eb28b7373c0053e19b` |
| Built 0.2.0 wheel | `846e35c9bca861ed5348d49c34eb8f7ec48ae562edf3c95bb49fbea45b83482f` |
| Synthetic source fingerprint | `ee1048733c26c4db2cb3bd7c11b2a48a4f45976a5adeadcedb95d5c2945fd4a6` |
| Synthetic record (`record-1`) | `3850f89def63ae3008b7b2b70b4c08e294279006a1f63f0cab17b9f9e8768a31` |

Original synthetic source-byte hashes, generated from `tests/fixture_support.py`:

| File key | SHA-256 |
|---|---|
| `synthetic:consumer.sas` | `455b199ea170040211371064b7d5e6081b6411cfac472775d2289f2348fd3e81` |
| `synthetic:includes/constants.sas` | `d43d96a9dbd97dac3f72da81a93b5f7291a5aac9bf8acad374fb9676964ca42b` |
| `synthetic:producer.log` | `5b6a8bea98c6bc6616bc82bb51428f3b3751b72ad1439feac0e04f730404b5b6` |
| `synthetic:producer.lst` | `6545188d4a6bbd9cc3822fcb244c57c701cf6c9a0fccc894585718bbe70440ac` |
| `synthetic:producer.sas` | `dec7863931b58c0a4d66c12fd0393bbe43ced0d1506765993e8d893ae87f6aed` |
| `synthetic:settings.cfg` | `4cb44dee6aae27a69000f644450a2fc979769e4599df7840becc1f6b805f3d86` |

The synthetic LOG/LST contents explicitly state that no SAS execution occurred.
Their numeric values are supplied fixtures, not measured rows or timings.

## Adversarial acceptance evidence

All cases below are present in the committed tests and passed in all three local
installation modes. A negative case passing means its expected FAIL/BLOCKED or
fixed-code rejection occurred; it does not mean invalid evidence was accepted.

| Obligation | Test evidence and observed behavior |
|---|---|
| Complete authorized inventory | Missing/removal/addition cases block; added-file contents are never read; modification and inter-file mutation invalidate prior inventory |
| Original bytes/citations | UTF-8/BOM/Latin-1/binary and LF/CRLF/CR/mixed tests; fabricated file/excerpt hashes, invalid spans and forged undeclared citation paths rejected |
| IDs and graph references | Duplicate/changed operation IDs, dangling datasets/columns/edges/issues, invalid producer-consumer nodes rejected; stable unchanged IDs and explicit include revision maps verified |
| Ownership | Wrong workspace/run/module/attempt/source owner rejected; exact subject attempt selected, never latest-by-mtime |
| Provenance | Matching filenames never create links; missing links remain unknown/BLOCKED; conflicting execution/run links and ambiguous multi-execution log associations fail/block |
| Coverage and unknowns | Counts recomputed; omitted unknowns, invalid UNKNOWN edges and misplaced contradictions rejected; explicit contradiction produces retained FAIL |
| Append-only history | Duplicate reservation/publication blocked; artifact tampering detected; failed attempts preserved; changed-source verification leaves historical bytes untouched |
| Concurrent processes | Two real spawned writers contend for reservation and publication: exactly one succeeds, the other blocks |
| Interrupted writes | Simulated short writes and a real child process `os._exit(71)` before seal preserve partial artifacts, produce no successful seal, and prevent attempt reuse |
| Path boundaries | Traversal, symlink root/file/directory/store, hardlink, FIFO, overlapping output root and malformed NUL/control/surrogate paths rejected |
| Execution/leakage | Prompt-like source/log text never executed; raw marker/source contents and absolute intake paths absent from artifacts/CLI; code-only errors; no real data imported |
| Authority | Unknown approval fields/HUMAN_APPROVED/semantic VERIFIED rejected; shape-only validity never yields semantic verification |
| P0 regression | All 25 existing foundation behavior/baseline/security tests pass with P1 status expectation updated |

## Review findings, failures and fixes

Independent review and adversarial construction found and fixed these issues
before final acceptance: earlier-file mutation while later files were read;
forged inventory citation bypassing explicit file authorization; foreign column
views omitting their parent dataset; NUL root paths raising an uncaught exception;
contradictions misplaced as unknowns; ambiguous log associations; and loss of an
available subject seal hash on failed verification. Dedicated regression cases
now pass. No acceptance threshold was weakened. No remaining critical failed case
was suppressed or converted into success.

A reviewer probe initially demonstrated the citation bypass. After the freshness
fix, a temporary unhandled mutation probe exited 1 by raising the now-correct
`SOURCE_CHANGED_DURING_READ`; the committed test asserts that rejection explicitly.
These exploratory probes are not included in the 138 test count.

Dependency acquisition included this initial restricted-network failure (exit 1,
DNS unavailable), followed by the identical network-authorized retry (exit 0):

```bash
.venv/bin/python -m pip download --only-binary=:all: --no-deps --platform manylinux_2_17_x86_64 --python-version 3.12 --implementation cp --abi cp312 --dest /tmp/sas-re-p1-wheels rpds-py==2026.9.1
```

The Linux wheel's recorded hash is in the lock. That download used pip's configured
index, whose URL was not printed. The later explicitly selected public index
command succeeded (exit 0), downloading the P0 wheels and reusing the runtime
wheelhouse; it did not independently re-download the Linux wheel:

```bash
.venv/bin/python -m pip download --no-cache-dir --index-url https://pypi.org/simple --require-hashes --only-binary=:all: --dest /tmp/sas-re-p1-wheels -r requirements.lock
```

Initial jsonschema resolution used:

```bash
.venv/bin/python -m pip download --disable-pip-version-check --no-cache-dir --only-binary=:all: --dest /tmp/sas-re-p1-wheels jsonschema==4.26.0
```

It succeeded with network authorization. Pip emitted an unwritable-user-cache
warning during several installs and disabled its cache; the installs completed
successfully. No hash check or dependency pin was bypassed.

The first remote drift check was BLOCKED/2 by restricted network access; its
network-enabled retry was PASS/0. `gh run list --repo keshavnath1/sas-reverse-engineering
--commit 0e1f6822871d3aa6956695a776672b63454c7958 --json databaseId,headSha,status,conclusion,url
--limit 5` exited 4 because GitHub CLI was unauthenticated. Hosted status was then
read through the connected GitHub tool; no credentials were requested or changed.

## Hosted CI

Observed [GitHub Actions run 42094717277](https://github.com/keshavnath1/sas-reverse-engineering/actions/runs/42094717277)
for exact implementation commit `0e1f6822871d3aa6956695a776672b63454c7958`:
**completed / success**. Both `foundation` (job 127481624948) and
`downstream-drift` (job 127481625098) succeeded. The foundation job log contains
138 tests OK in 5.480 seconds for checkout validation and 138 tests OK in 5.489
seconds after wheel installation outside the checkout. Hash-locked install,
repository guard, synthetic demo and site-packages assertion all succeeded.
Runner: ubuntu-latest, configured Python 3.12.5 x86_64.

Status and logs were read with connected GitHub tools using these exact inputs:

```json
{"url":"https://api.github.com/repos/keshavnath1/sas-reverse-engineering/actions/runs/42094717277"}
{"repo_full_name":"keshavnath1/sas-reverse-engineering","run_id":42094717277}
{"repo_full_name":"keshavnath1/sas-reverse-engineering","job_id":127481624948}
```

Tools respectively: `github.fetch`, `github.fetch_workflow_run_jobs`,
`github.fetch_workflow_job_logs`. The report does not attribute this run to a
later documentation-only commit. No hosted tests were skipped or weakened.

## Files changed

Created: `docs/P1_DESIGN.md`, this `docs/P1_VALIDATION.md`, `scripts/p1_demo.py`,
`src/sas_re/contracts.py`, `src/sas_re/contracts/v1/evidence.schema.json`,
`src/sas_re/evidence.py`, `src/sas_re/runs.py`, `src/sas_re/safeio.py`,
`tests/fixture_support.py`, `tests/test_contracts.py`, `tests/test_evidence.py`,
`tests/test_runs.py`, `tests/test_safeio.py`.

Modified: `.github/workflows/foundation.yml`, `AGENTS.md`, `README.md`,
`SECURITY.md`, `docs/APPROVALS.md`, `docs/OPEN_DECISIONS.md`, `pyproject.toml`,
`requirements.lock`, `src/sas_re/__init__.py`, `src/sas_re/cli.py`,
`tests/test_foundation.py`. The reference ZIP, compatibility pin and downstream
repository were not modified. Raw fixtures/artifacts remain outside Git.

## Proof boundaries and next decision

The tests demonstrate synthetic local structural integrity, safe path handling,
explicit declarations and append-only API behavior. They do not establish SAS
meaning, absent-but-undeclared dependencies, trustworthy log-to-execution origin,
true numeric metrics, safe parallelism, migration parity or architecture quality.
Local hashes are not signatures; filesystem owners can rewrite everything. A
multi-file atomic source snapshot, production immutability, real-data redaction,
retention policy and independently protected evaluator environment remain open.

Recommended Step 4/P2: first approve D08/D09 (supported synthetic SAS subset,
extraction environment, independent checker and isolated gold), then implement
bounded semantic reconstruction/evaluation against canonical P1 IDs, including
valid-citation/false-conclusion negatives. Preserve downstream human gates and
keep architecture selection, real workloads and execution outside that scope.
**P1 stops here; P2 requires explicit review and approval.**
