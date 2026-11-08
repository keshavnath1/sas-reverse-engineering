# CP3D actual validation and remaining blockers

Approved baseline: `5453a2598bd6da4ee695602f539f3961e70556b7`.
Validation date: 2026-11-06 (America/New_York). The user accepted CP3C planning
and authorized only the bounded private implementation in [CP3D design](CP3D_DESIGN.md).
This report does not qualify native Windows or authorize further implementation.

## Observed environments and results

Local: macOS 26.6.2 build 25G83, ARM64, CPython 3.12.5, Clang 14.0.0,
existing `.venv`. No new dependency or lockfile change. Windows host, owner,
independent human security reviewer, observer, native execution grant and approved
offline Windows dependency closure remain OPEN. No Windows API was executed.

| Executed check | Actual result |
|---|---|
| Exact baseline checkout suite | Exit 0; 596 tests, OK, 17.453 seconds |
| New metadata protocol cases | Exit 0; 51 tests, OK, 0.706 seconds; memory-only simulation |
| New mapping/record/native-gate cases | Exit 0; 20 tests, OK, 0.004 seconds; pure or mocked callables |
| Complete development suite | Exit 0; 667 tests, OK, 18.111 seconds; all 596 existing tests plus 71 new tests |
| Historical baseline/candidate P1 replay | Exit 0; 15 artifact files byte-identical; complete parsed reports equal |
| Historical baseline/candidate P2A replay | Exit 0; 15 artifact files byte-identical; complete parsed reports equal |
| Retained CP3B artifact comparison | Both newly regenerated baseline sets match the retained historical files byte-for-byte |
| `pip check` | Exit 0; no broken requirements. Nonfatal unwritable-cache warning; no installation attempted |
| Staged repository guard | Exit 0; PASS, no errors; limited tracked-path/secret-pattern rules, not complete DLP |
| Preservation/documentation assertions | Exit 0; 82 existing baseline files byte-identical; exactly 12 authorized changed files; 96 valid local Markdown links |
| `git diff --check`; `git diff --cached --check` | Exit 0; no whitespace errors |

No test was removed, weakened or skipped to achieve these results. Test elapsed
times are not workload benchmarks. Existing POSIX tests/demos create disposable
synthetic fixtures; they are not CP3D Windows execution. CP3D's 71 new cases use
no real source/store fixtures. No private input or SAS execution occurred.

Existing frozen CP2 vectors and full regression tests preserve original-byte
hashes, logical scope/projection, source/operation identities, citations, graph
formats and append-only behavior. No historical evidence file was edited.

## Commands and evidence locations

Unless otherwise stated, commands ran from
`/Users/divyasreegundaram/Downloads/sas-migration-skill-enhancement-v2/sas-reverse-engineering`.
The development interpreter is that directory's `.venv/bin/python`.

```sh
git status --short
git rev-parse HEAD
sw_vers
.venv/bin/python -c 'import platform,sys; print(sys.version); print(platform.platform()); print(platform.machine())'
.venv/bin/python -m pip check
.venv/bin/python -m unittest discover -s tests -p test_windows_bootstrap_native.py -v
.venv/bin/python -m unittest discover -s tests -p test_windows_bootstrap.py
.venv/bin/python -m unittest discover -s tests -v > /private/tmp/sas-re-cp3d-tests.log 2>&1
rc=$?
tail -n 6 /private/tmp/sas-re-cp3d-tests.log
exit "$rc"
```

Initial checkout was clean at the exact approved baseline. All commands above
completed with exit 0. The full suite log is local and outside Git. Earlier
focused runs at 45 and 49 protocol tests also passed while tests were being added;
the final count is 51 protocol plus 20 primitive tests, not a sum of those runs.

Staging/guard commands actually executed:

```sh
git add AGENTS.md README.md SECURITY.md docs/APPROVALS.md docs/OPEN_DECISIONS.md docs/BEST_PRACTICES_ADOPTION.md docs/CP3D_DESIGN.md docs/CP3D_VALIDATION.md src/sas_re/_windows_bootstrap.py src/sas_re/_windows_bootstrap_native.py tests/test_windows_bootstrap.py tests/test_windows_bootstrap_native.py
.venv/bin/python scripts/check_repository.py
git diff --cached --check
```

The inline Python preservation check compared each baseline `git ls-tree` file
outside the six documented Markdown edits to `git show <baseline>:<path>` bytes.
It asserted the exact twelve-file diff and no untracked extras, UTF-8/LF/final
newlines, balanced Markdown fences and existence of all 96 local link targets.
It recomputed all eight SHA-256 values below and checked the downstream commit.
No existing implementation, test, workflow or contract byte differed.

Independent baseline preparation used these commands, both exit 0:

```sh
git clone --no-hardlinks /Users/divyasreegundaram/Downloads/sas-migration-skill-enhancement-v2/sas-reverse-engineering /private/tmp/sas-re-cp3d-preservation.rvgjikm7/baseline
git -C /private/tmp/sas-re-cp3d-preservation.rvgjikm7/baseline checkout --detach 5453a2598bd6da4ee695602f539f3961e70556b7
```

Baseline suite was invoked by a Python subprocess, not a separate shell command:

```python
argv = [
    '/Users/divyasreegundaram/Downloads/sas-migration-skill-enhancement-v2/sas-reverse-engineering/.venv/bin/python',
    '-m', 'unittest', 'discover', '-s',
    '/private/tmp/sas-re-cp3d-preservation.rvgjikm7/baseline/tests', '-v',
]
cwd = '/private/tmp/sas-re-cp3d-preservation.rvgjikm7/baseline'
# Inherited environment plus:
PYTHONPATH = '/private/tmp/sas-re-cp3d-preservation.rvgjikm7/baseline/src'
PYTHONDONTWRITEBYTECODE = '1'
```

The subprocess stdout/stderr was captured in
`/private/tmp/sas-re-cp3d-preservation.rvgjikm7/baseline-tests.log`.
Baseline demos used the same interpreter/environment with argv
`[interpreter, audit + '/baseline/scripts/' + phase + '_demo.py', '--destination',
audit + '/' + phase + '-baseline']`, for `phase` equal to `p1` and `p2a`;
`audit` is `/private/tmp/sas-re-cp3d-preservation.rvgjikm7` and cwd was the development
repository. Exact invocations, exit codes and captured outputs are in that
directory's `commands.json`, `p1-baseline.json` and `p2a-baseline.json`.

Candidate comparison actually executed, exit 0:

```sh
.venv/bin/python /private/tmp/sas-re-cp3d-preservation.rvgjikm7/compare_candidate.py
```

That audit-only script invokes the existing candidate `scripts/p1_demo.py` and
`scripts/p2a_demo.py` with `--destination` ending in `p1-candidate` / `p2a-candidate`
under the same audit directory, using the existing interpreter, candidate `src`
on `PYTHONPATH` and `PYTHONDONTWRITEBYTECODE=1`. It compares full relative-path-to-
original-bytes mappings, not just summaries, and complete parsed stdout reports.
`candidate-preservation.json` records exact commands/results. These local audit
scripts and generated artifacts are not packaged, committed or runtime dependencies.
Existing demo revision scenarios intentionally change their own disposable source
fixtures; they do not modify historical sealed evidence or exercise CP3D I/O.

| Historical artifact set | File count | Unchanged manifest SHA-256 |
|---|---|---|
| P1 | 15 | `3b3a6b999ed496b995c2ae055448805a8fbfb746a03edac7192fe128403fa7c6` |
| P2A | 15 | `38259743e798bd3d9df6089c1576a31865aa575427710ff73bbc2befee3bb809` |

Manifest preimage: compact sorted JSON mapping relative paths (including
`artifacts/`) to SHA-256 of original bytes, followed by LF. Both manifest hashes
agree with the historical record; all individual bytes were also compared.

## Frozen hashes

All values below are unchanged from the approved baseline. The downstream commit
remains `bc754e0f1204a99020c864df2a5b25983005e09c`. Agent-mastery was not modified.

| File / boundary | SHA-256 |
|---|---|
| v1 evidence schema | `15e3265fac9af300b40967580998ef4ac90eb1d830a10ce201855fc4ec2738a2` |
| v2 evidence schema | `093216d16bb02e91a3997c97175420bf2257982f5a5fe3a4374ef92f7637a90b` |
| CP2 authorization schema | `427ce869b05e75227653e6f3dcf99466cfaf5111e2be95242a9da5ee157a08f6` |
| requirements.lock | `4676c7fe0a41ce2fdb35c2fb10cc014a8b352a8ca71029eb28b7373c0053e19b` |
| downstream baseline.json | `d22af8651c77a0569e9de7ca473e2274c108de14896b23089421100d6aa2e040` |
| tests/cp2_vectors.py | `02b4bd89c0bb0e9550c0fb8665738f5db411b2f858b9f261975f50a117da7509` |
| tests/p2a_expectations.py | `f42549738a041db87d3547adec59ddfd0f9b15aa2621f1cf0b7ea7fa9f7ffd93` |
| specification ZIP | `e3cbf3d9df6cc20c594261556c5e3ea1dfc292c9c1a30672c2d7b1a736b9718e` |

## Observable simulated security evidence

- The independently authored metadata fixture has no source reader, creator,
  writer, publisher or process/network method. I/O spies reject external file,
  process and network access during protocol runs. Original synthetic bytes and
  namespace snapshots remain equal for positive/no-adversary cases.
- Missing expectations, unsafe components, wrong scope, duplicate identities and
  out-of-bound inventories fail before any adapter event. No drive scan or default
  root is selected. Host/mapping mismatch stops before root acquisition.
- Retained root/parent identity and fresh relative-lookup comparisons detect
  replacement, metadata mutation and mapping changes injected at protocol barriers.
  An independent alias table makes native-style case/short-name collisions PRESENT,
  even when the requested long spelling is absent. Existing file/reparse collisions
  never become absence. True absent sibling and multi-suffix cases pass simulation.
- Only exact candidate NAME_NOT_FOUND passes status classification. Access/share/
  path/type/pending/unknown failures block. Definite case-insensitive state is
  required; boolean/integer equality cannot conceal malformed native records.
- Ownership/event assertions show completed handles close once on success,
  denial and cancellation. Close uncertainty prevents success while attempting
  all other owned releases. Inconsistent pending/failed resources stay adapter-
  owned and are never falsely claimed closed by the protocol.
- Import/constructor spies establish that imports load no DLL, the mocked Windows
  constructor binds only QueryDosDeviceW, and every new native filesystem/context
  entry denies without using supplied values. The public Windows gates and all
  original POSIX/CP2/CP3B behavior are covered by the unchanged regression suite.

These are in-process/memory observations, not native OS traces or independent
human certification. Pending-buffer lifetime is protected by not issuing native
filesystem calls; no native cancellation or completion solution is implemented.

## Failures and corrections

The first independently authored protocol-test file failed import with a
SyntaxError caused by raw strings ending in a backslash. The literals were fixed;
subsequent focused and full runs passed. No test was skipped or weakened.

Read-only security review identified a potentially premature ownership transfer
for a contradictory PRESENT result carrying STATUS_PENDING. The implementation now
validates status before accepting ownership; dedicated fault tests preserve adapter
ownership. Review also led to strict observed-field widths/types, bounded mapping
tuples and typed BLOCKED conversion for metadata OSError after cleanup. These were
review findings, not observed native failures. Two documentation patch attempts
had context mismatches, made no changes, and were reapplied with correct context.

No full-regression or artifact-comparison failure occurred. No actual Windows
success/failure result exists. The missing native prerequisites remain BLOCKED.

## Complete changed-file scope and stop

New files: `src/sas_re/_windows_bootstrap.py`,
`src/sas_re/_windows_bootstrap_native.py`, `tests/test_windows_bootstrap.py`,
`tests/test_windows_bootstrap_native.py`, `docs/CP3D_DESIGN.md`,
`docs/CP3D_VALIDATION.md`.

Updated documentation only: `AGENTS.md`, `README.md`, `SECURITY.md`,
`docs/APPROVALS.md`, `docs/OPEN_DECISIONS.md`, `docs/BEST_PRACTICES_ADOPTION.md`.
No existing implementation/test/schema/workflow/lock bytes change. No public CLI,
capability activation, CP3B reader connection, new provider/dependency or runtime
Git/cloud requirement. DRAFT, UNVERIFIABLE, semantic BLOCKED and benchmark NOT_RUN
statuses remain unchanged.

Native host/runtime/provisioning approval, authentic metadata authority, physical
backing and namespace trust, exact root/reparse/name/case query behavior, completion
and independent hostile-fixture observation are unresolved. All CP3C native
obligations remain NOT_RUN; no passing skips stand in for them. The constant native
gate means CP3D does **not** yet provide a working native bootstrap or absent-store
proof. Stop here for explicit review; no CP4, CP5, P2B or P3.
