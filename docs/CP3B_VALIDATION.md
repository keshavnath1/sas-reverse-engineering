# CP3B validation record

Approved baseline: `f841ca25d511230d77ab1c3eded3f59602a79f5d`.
Scope: [private Windows reader subset](CP3B_DESIGN.md), synthetic tests and honest
capability reporting. Public Windows source access and publication remain BLOCKED.
No CP4/CP5/P2B/P3, private intake, SAS execution, dependency/lock change or
Agent-mastery modification occurred. DRAFT authority, UNVERIFIABLE verification,
BLOCKED independent semantic acceptance and NOT_RUN benchmarks are preserved.

## Executed environment and classification

Local: macOS 26.6.2 build 25G83, Darwin 25.6.0, ARM64, CPython 3.12.5
(Clang 14.0.0), effective UID 501, existing APFS workspace. Reused approved
`.venv` and `/private/tmp/sas-re-p2a-wheel-env`; only the candidate package was
reinstalled offline with no dependency installation. Pip disabled its unwritable
user cache; this warning was not a dependency failure.

**No Windows host, NTFS volume, PowerShell, native DLL invocation, ACL test,
junction fixture, native trace or Windows dependency environment was executed.**
All new Windows test cases are simulated/unit-only. No skipped hostile fixture
counts as success. Native qualification is BLOCKED/NOT_RUN, not a passed matrix
cell. Development-agent review is not the OPEN independent human security review.

| Check | Observed result |
|---|---|
| Approved baseline checkout | 514 tests, exit 0, 16.738 s; no skips |
| Intermediate full development runs | 588 tests/17.212 s and 595 tests/16.737 s, both exit 0; test additions and final bound correction followed |
| Independent simulated protocol suite | 62 tests, exit 0, 0.734 s; no skips |
| Native adapter ABI/call/parser unit suite | 20 tests, exit 0, 0.006 s; no native execution or skips |
| Baseline/candidate synthetic P1 artifacts | 15 artifact files byte-identical; full demonstration JSON equal; wrappers/comparison exit 0 |
| Baseline/candidate synthetic P2A artifacts | 15 artifact files byte-identical; full demonstration JSON equal; wrappers/comparison exit 0 |
| Baseline protected-file comparison | 71 existing tracked files byte-identical, including all original tests, schemas, POSIX code, identity algorithms, scripts, dependency lock and reference archive; exit 0 |
| Dependency checks | Development and existing wheel environments: no broken requirements; exit 0 |
| Compile and pinned local downstream check | Exit 0; 20 pinned digests match, downstream clean at `bc754e0f1204a99020c864df2a5b25983005e09c` |
| Wheel build/install | Exit 0; package-only offline install, site-packages import confirmed |

Final complete-suite, fresh-checkout and staged checks are appended below after
execution. Timings are diagnostics, not SAS benchmarks or independent samples.
No hosted Linux result is claimed here before an actual completed run is observed.

## What the new tests actually demonstrate

`tests/windows_fake.py` was independently authored as a memory-only object tree,
with retained object references, separate metadata/data handles and a call ledger.
Its oracle requires all declared metadata/membership observations before any data
open, and all required data handles before any byte read; it does not trust a
candidate stage marker. It snapshots bytes, names, IDs, link counts and relevant
metadata independently of the reader. Tests prohibit real path/file opening,
process launch and network access during the protocol; the separate fresh-import
test intentionally launches only a local Python interpreter as its test harness.

Observed unit assertions cover root/ancestor/intermediate/leaf reparses, unknown
tags, offline/recall and nondisk objects; volume mismatch/ambiguous identity;
physical source/store equality and nesting; siblings; hardlinks and alias IDs;
exact membership including hidden/system entries and no unexpected-directory
descent; denied final metadata/data opens with zero earlier content reads;
replacement, mutation, second-pass byte changes; byte/count/depth/handle bounds;
cleanup on success, faults and cancellation; and public Windows denial before
native construction or path access. An existing synthetic sealed store remains
unchanged and unread. Absent store prefixes remain absent and block before reads.
No source/store mutation method exists in the protocol/native adapter.

Independent LF/CRLF/BOM/edited-byte vectors retain the frozen CP2 scope and
applicable file/source/operation identities across Windows/POSIX logical bindings.
Changed original bytes change applicable source-bound IDs, while an unchanged
logical scope retains its scope hash. No native path or transient handle/volume
identity is added to portable evidence. Historical artifact comparisons below
exercise the unchanged actual POSIX P1/P2A workflows, not a Windows publisher.

ABI/parser unit tests check fixed-width layouts, malformed UTF-16/length/offset
records, finite progress, aggregate counts including structural dots, exact
existing-only relative-open rights, metadata refusal, ReadFile offsets/bytes,
failed/informational opens, cancellation after returned handles, reused handle
numbers, no weaker retry and ambiguous close. Every fake handle receives one
close attempt; uncertainty prevents a successful source mapping. This does not
prove actual Windows handles close or kernel calls terminate under every failure.

## Commands and reproducible comparisons

Unless stated, cwd is
`/Users/divyasreegundaram/Downloads/sas-migration-skill-enhancement-v2/sas-reverse-engineering`.
Logs, fixtures and comparison scripts are outside Git at
`/private/tmp/sas-re-cp3b-validation.nUVriN`; this temporary evidence may expire.
Commands below were actually executed; all completed checks exited 0 unless
explicitly described in the failure record.

```sh
git rev-parse HEAD
git status --short
.venv/bin/python -c 'import platform,sys,os; print(sys.version); print(platform.platform()); print(platform.uname()); print("euid",os.geteuid())'
sw_vers
.venv/bin/python -m pip check
/private/tmp/sas-re-p2a-wheel-env/bin/python -m pip check
git clone --no-hardlinks . /private/tmp/sas-re-cp3b-validation.nUVriN/baseline
PYTHONPATH=/private/tmp/sas-re-cp3b-validation.nUVriN/baseline/src .venv/bin/python -m unittest discover -s /private/tmp/sas-re-cp3b-validation.nUVriN/baseline/tests -v > /private/tmp/sas-re-cp3b-validation.nUVriN/baseline-tests.log 2>&1
.venv/bin/python -m unittest discover -s tests -p 'test_windows_native.py' -v
.venv/bin/python -m unittest discover -s tests -p 'test_windows_preflight.py' -v > /private/tmp/sas-re-cp3b-validation.nUVriN/windows-protocol-tests.log 2>&1
.venv/bin/python -m unittest discover -s tests -v > /private/tmp/sas-re-cp3b-validation.nUVriN/development-first.log 2>&1
.venv/bin/python -m unittest discover -s tests -v > /private/tmp/sas-re-cp3b-validation.nUVriN/development-final.log 2>&1
.venv/bin/python -m unittest discover -s tests -v > /private/tmp/sas-re-cp3b-validation.nUVriN/development-complete.log 2>&1
.venv/bin/python -m compileall -q src tests scripts
.venv/bin/sas-re check-baseline --checkout /private/tmp/sas-re-downstream-bc754e0
.venv/bin/python /private/tmp/sas-re-cp3b-validation.nUVriN/preservation.py
.venv/bin/python /private/tmp/sas-re-cp3b-validation.nUVriN/check_preserved.py
SOURCE_DATE_EPOCH=1793926179 .venv/bin/python -m pip wheel --no-deps --no-build-isolation --wheel-dir /private/tmp/sas-re-cp3b-validation.nUVriN/wheel .
```

The preservation script executed these four argument-vector commands, with the
indicated checkout's `/src` as `PYTHONPATH` and the development Python above:

```sh
PYTHONPATH=/private/tmp/sas-re-cp3b-validation.nUVriN/baseline/src .venv/bin/python /private/tmp/sas-re-cp3b-validation.nUVriN/baseline/scripts/p1_demo.py --destination /private/tmp/sas-re-cp3b-validation.nUVriN/p1-baseline
PYTHONPATH=/Users/divyasreegundaram/Downloads/sas-migration-skill-enhancement-v2/sas-reverse-engineering/src .venv/bin/python scripts/p1_demo.py --destination /private/tmp/sas-re-cp3b-validation.nUVriN/p1-candidate
PYTHONPATH=/private/tmp/sas-re-cp3b-validation.nUVriN/baseline/src .venv/bin/python /private/tmp/sas-re-cp3b-validation.nUVriN/baseline/scripts/p2a_demo.py --destination /private/tmp/sas-re-cp3b-validation.nUVriN/p2a-baseline
PYTHONPATH=/Users/divyasreegundaram/Downloads/sas-migration-skill-enhancement-v2/sas-reverse-engineering/src .venv/bin/python scripts/p2a_demo.py --destination /private/tmp/sas-re-cp3b-validation.nUVriN/p2a-candidate
```

Each stdout/stderr was captured as `<phase>-<version>.json/.stderr`. Child
BLOCKED and stale-source FAIL outcomes are expected demo assertions; wrappers
exit 0. Comparison constructs relative-path-to-original-bytes dictionaries for
all files beneath `/artifacts/`, asserts exact dictionary equality, and compares
complete parsed stdout JSON. No SAS runs. Manifest hashes below use the SHA-256
of compact sorted JSON `{relative_path: sha256(bytes)}` plus LF; this explicit
preimage differs from earlier reports' manifest formatting, not artifact bytes.

From `/private/tmp`:

```sh
/private/tmp/sas-re-p2a-wheel-env/bin/python -m pip install --no-index --no-deps --force-reinstall /private/tmp/sas-re-cp3b-validation.nUVriN/wheel/sas_reverse_engineering-0.3.0-py3-none-any.whl
/private/tmp/sas-re-p2a-wheel-env/bin/python -c 'import sas_re; print(sas_re.__file__); assert "site-packages" in sas_re.__file__'
/private/tmp/sas-re-p2a-wheel-env/bin/python -m unittest discover -s /Users/divyasreegundaram/Downloads/sas-migration-skill-enhancement-v2/sas-reverse-engineering/tests -v > /private/tmp/sas-re-cp3b-validation.nUVriN/wheel-tests.log 2>&1
```

Observed import:
`/private/tmp/sas-re-p2a-wheel-env/lib/python3.12/site-packages/sas_re/__init__.py`.

## Frozen hashes and artifact preservation

| Item | SHA-256 |
|---|---|
| Frozen v1 schema | `15e3265fac9af300b40967580998ef4ac90eb1d830a10ce201855fc4ec2738a2` |
| Frozen v2 schema | `093216d16bb02e91a3997c97175420bf2257982f5a5fe3a4374ef92f7637a90b` |
| CP2 authorization schema | `427ce869b05e75227653e6f3dcf99466cfaf5111e2be95242a9da5ee157a08f6` |
| Dependency lock | `4676c7fe0a41ce2fdb35c2fb10cc014a8b352a8ca71029eb28b7373c0053e19b` |
| Downstream metadata | `d22af8651c77a0569e9de7ca473e2274c108de14896b23089421100d6aa2e040` |
| CP2 vectors | `02b4bd89c0bb0e9550c0fb8665738f5db411b2f858b9f261975f50a117da7509` |
| P2A expectations | `f42549738a041db87d3547adec59ddfd0f9b15aa2621f1cf0b7ea7fa9f7ffd93` |
| P1 15-file manifest under stated preimage | `3b3a6b999ed496b995c2ae055448805a8fbfb746a03edac7192fe128403fa7c6` |
| P2A 15-file manifest under stated preimage | `38259743e798bd3d9df6089c1576a31865aa575427710ff73bbc2befee3bb809` |
| Candidate wheel | `ba0350487c5bb7f408d6c276cd8cfd8c56eb4fdc17bb738e5a3ef2e160d8d0ad` |

The protected-file script compares every baseline tracked file except the eight
explicitly edited existing files listed below, using original `git show` bytes.
All 71 protected files match. This includes the unchanged original-byte identity
algorithms, all 514-test source files, source graph algorithms, frozen contracts,
reference ZIP and POSIX persistence implementation. Generated synthetic artifacts
match actual baseline outputs; no historical artifacts were rewritten.

## Failures, review findings and corrections

- Initial 44-test protocol run: 43 passed, one failed because a test mutation hook
  changed another file before its first read. The independently authored hook was
  corrected to fire after that same handle had been read. All 44 then passed.
- Security review rejected enumeration of unrelated bootstrap-ancestor siblings.
  Replaced it with retained-parent single-component metadata probes; added a
  sentinel proving unrelated volume entries are never enumerated.
- Review found exact-name absence could conceal a case/DOS alias. Missing store
  prefixes now explicitly BLOCKED; positive fixtures use a preexisting disjoint
  store. An intermediate 53-test run during this change had 22 errors/3 failures
  due to the old absent-store fixture. Tests now assert both stronger denial and
  existing-store success; no gate was weakened.
- Native close reports EvidenceError, so OSError-only cleanup could abandon
  remaining handles. Cleanup now exhausts all handles even on wrapper failures or
  cancellation, with no retry; uncertainty blocks success. Native returned-handle
  cancellation and handle-number reuse are covered separately.
- Structural dot entries are validated and excluded, while hidden/system names
  remain. Undefined nonreparse tag bytes are handled according to the API contract.
- Final review corrected aggregate enumeration accounting to include structural
  entries, and added exact-limit/overflow tests across multiple query batches.
  Documentation now describes the actual kernel-version screen rather than
  incorrectly treating it as Windows client-edition qualification.
- One editing helper failed with a Python SyntaxError before changing any file;
  the correction used an explicit patch. One read command used nonexistent
  `.github/workflows/ci.yml` (exit 1); the actual unchanged workflow is
  `.github/workflows/foundation.yml`. These were tooling failures, not ignored tests.

## Exact changed files

New:
`src/sas_re/_windows_native.py`, `src/sas_re/_windows_preflight.py`,
`tests/windows_fake.py`, `tests/test_windows_native.py`,
`tests/test_windows_preflight.py`, `docs/CP3B_DESIGN.md`,
`docs/CP3B_VALIDATION.md`.

Updated:
`src/sas_re/platform_io.py`, `src/sas_re/cli.py`, `AGENTS.md`, `README.md`,
`SECURITY.md`, `docs/APPROVALS.md`, `docs/OPEN_DECISIONS.md`,
`docs/BEST_PRACTICES_ADOPTION.md`.

No original test, schema, identity module, preflight entry point, POSIX backend,
lockfile, CI workflow, reference archive or downstream pin changed.

## Native obligations that remain unexecuted

The [CP3 security matrix](CP3_SECURITY_TEST_PLAN.md) is not replaced by unit tests.
T01/T02/T20/T22/T23/T24 have pure/simulated coverage; T03–T14/T16–T21 have relevant
reader simulations and still require actual approved NTFS fixtures. T15's POSIX
regressions run on the existing supported environment. T25 preservation comparisons
are executed. T26 has installed macOS package coverage, not native Windows coverage.
No row is declared fully native-qualified by this mapping.

Still BLOCKED: approved local-volume bootstrap and ambiguity handling; root/ancestor
reparse/no-hydration behavior; actual junction/mounted-folder/unknown-tag fixtures;
Windows ACL and denied-last-file rights; real sharing conflicts and mapped views;
case/Unicode/DOS aliases; drive/SUBST/duplicate-volume identities; real replacement
races; noninheritance, cleanup and kernel-call cancellation; observed zero writes
and no early output across failures. Privileged fixture/observer setup is separate
from ordinary unelevated execution and has not been authorized or performed.

Host owner, independent human security reviewer, fixture custodian, approved offline
Python/dependency bundle, observer/retention plan and writer/ACL policy remain OPEN.
No simulation, successful skip, copied hash or development review closes them.
The private protocol also blocks absent store paths pending a reviewed absence
proof. Full Windows evidence remains BLOCKED until separate publication work and
qualification. Stop after CP3B; no automatic CP4/CP5/P2B/P3 progression.

## Final local results before fresh checkout

- Complete development suite: **596 tests**, exit 0, 17.301 s, no skips
  (514 preserved + 62 simulated protocol/capability + 20 native-adapter unit tests).
- Installed wheel suite outside the checkout: **596 tests**, exit 0, 17.405 s,
  no skips; the import path above confirms installed site-packages.
- `git diff --check`: exit 0, no whitespace errors.
- `.venv/bin/python -m sas_re status`: exit 0; unchanged DRAFT/UNVERIFIABLE/
  BLOCKED/NOT_RUN statuses and pin, with additive read-only preflight capability.

No native Windows result is implied. Fresh-checkout and final repository checks
follow in the record below.
