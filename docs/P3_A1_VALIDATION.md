# P3-A1 validation record

Scope: private diagnostics over caller-supplied public synthetic graph values.
Baseline `dba5b3aa5a60ef384bfc57a90b46ca72ea4f27dc`; see the [design](P3_A1_DESIGN.md)
and [approved obligations](POST_CP3D_ROADMAP.md#proposed-exact-tests-and-acceptance).
All 693 tests passed in the final macOS development, fresh-clone and installed-wheel
runs and in both hosted Linux installation modes. The 26 new methods exercised
133 explicit subtests. All 30 historical artifacts and eight frozen hashes matched.

The results below describe engineering behavior only. Each positive result is
DRAFT / UNVERIFIABLE / BLOCKED / NOT_RUN. The P2B gate was not run.

## Baseline and independent freeze

The starting checkout was clean at the approved commit. On macOS 26.6.2 arm64,
CPython 3.12.5, an exact detached baseline clone ran **667 tests, OK, 17.399 s**.
Its P1 and P2A demos each returned 0; all 15 artifact files in each matched the
retained CP3D set byte for byte. The complete parsed reports also matched. The
baseline checkout remained clean. Disposable synthetic replay was outside Git.

The fixture author used only stdlib JSON/SHA-256, hand-declared graph inputs and
literal mathematical expectations. Before the candidate module existed, another
developer review checked:

- 23 literal graph hashes and 23 frozen v2 shape validations; all matched.
- 101 reproducible ID preimages: 44 operations, 23 datasets, 14 columns, 19 edges,
  one log observation. Four unknowns and one contradiction were treated as opaque.
- A01–A26 labels; topology, edge witness, scoped issue and conflict expectations.
  The largest observed dimensions among the 23 positives: 4 operations, 2 modules,
  4 edges, 4 nodes, 4 facts, 659 values, depth 9, 10,693 canonical bytes.

`test ! -e src/sas_re/_dependency_diagnostics.py` succeeded before the freeze.
`shasum -a 256 tests/dependency_vectors.py` returned
`7e8e5f6d3c37bf3ef7553abb3511446c23a22562f460398cb7e5344b95b6a90b`.
Only that file was committed at `0e1b80fe60c412ddbf19a0c93c4291f4fe3bfd95`.
These are public regression oracles, not hidden answers, observed SAS executions
or independently adjudicated semantics.

## Commands and artifacts

Shell commands below use `P` for the repository root, `T` for the disposable
workspace `/private/tmp/sas-re-p3a1-preservation.gj3qly8u`, and `PY` for the
existing `"$P/.venv/bin/python"`. All paths below are synthetic development paths.
Baseline execution (with `PYTHONDONTWRITEBYTECODE=1`, in the detached clone):

```sh
git clone --no-hardlinks "$P" "$T/baseline"
git -C "$T/baseline" checkout --detach dba5b3aa5a60ef384bfc57a90b46ca72ea4f27dc
PYTHONPATH="$T/baseline/src" "$PY" -m unittest discover -s "$T/baseline/tests" -v
PYTHONPATH="$T/baseline/src" "$PY" "$T/baseline/scripts/p1_demo.py" --destination "$T/p1-baseline"
PYTHONPATH="$T/baseline/src" "$PY" "$T/baseline/scripts/p2a_demo.py" --destination "$T/p2a-baseline"
```

For the hash review, `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests:src .venv/bin/python -`
iterated `fixture_catalog()`, compared `digest` and each reconstructible `record_id`
to the authored values, and ran the frozen v2 shape validator. No candidate
routine supplied any expected answer. For the historical comparisons the byte
manifest is SHA-256 of compact sorted JSON mapping relative `artifacts/...` paths
to per-file SHA-256, followed by LF. The manifests are:

| Scope | Manifest SHA-256 |
|---|---|
| P1 (15 files) | `3b3a6b999ed496b995c2ae055448805a8fbfb746a03edac7192fe128403fa7c6` |
| P2A (15 files) | `38259743e798bd3d9df6089c1576a31865aa575427710ff73bbc2befee3bb809` |

## Frozen identities

| File | SHA-256 |
|---|---|
| `src/sas_re/contracts/v1/evidence.schema.json` | `15e3265fac9af300b40967580998ef4ac90eb1d830a10ce201855fc4ec2738a2` |
| `src/sas_re/contracts/v2/evidence.schema.json` | `093216d16bb02e91a3997c97175420bf2257982f5a5fe3a4374ef92f7637a90b` |
| `src/sas_re/contracts/authorization/v1/local-authorization.schema.json` | `427ce869b05e75227653e6f3dcf99466cfaf5111e2be95242a9da5ee157a08f6` |
| `requirements.lock` | `4676c7fe0a41ce2fdb35c2fb10cc014a8b352a8ca71029eb28b7373c0053e19b` |
| `src/sas_re/data/baseline.json` | `d22af8651c77a0569e9de7ca473e2274c108de14896b23089421100d6aa2e040` |
| `tests/cp2_vectors.py` | `02b4bd89c0bb0e9550c0fb8665738f5db411b2f858b9f261975f50a117da7509` |
| `tests/p2a_expectations.py` | `f42549738a041db87d3547adec59ddfd0f9b15aa2621f1cf0b7ea7fa9f7ffd93` |
| `reference/Codex_SAS_Architecture_Pack_v2.zip` | `e3cbf3d9df6cc20c594261556c5e3ea1dfc292c9c1a30672c2d7b1a736b9718e` |

No baseline or downstream bytes are updated to make a comparison succeed.

## What was exercised

One `unittest` method per named roadmap obligation; subtests are parameter
variants within the method, **not** extra discovered tests, semantic samples or
additional runs. The table names the methods without their `test_` prefix.

| ID | Method | Checked result | Explicit subtests |
|---|---|---|---:|
| A01 | single_operation | Original op, no paths or cycles; no approval | 0 |
| A02 | data_chain_witness | A→C reconstructs the two original DATA edges in order | 0 |
| A03 | diamond | Four edges retained; A→B→D is the deterministic witness | 0 |
| A04 | disconnected_branches | All missing directed pairs say independence is unproved | 0 |
| A05 | missing_raw_edge | Shared canonical access and missing proof; edges stay empty | 0 |
| A06 | waw_conflict | Two writes, unversioned overwrite obligation | 0 |
| A07 | war_conflict | Earlier read/later write, no added dependency | 0 |
| A08 | dataset_column_alias | Both parent/column directions and distinct columns | 3 |
| A09 | state_self_cycle | RETAIN and LAG effects, original self-edge and cycle witness | 2 |
| A10 | multi_operation_cycle | Both operations and internal edge IDs in one cyclic component | 0 |
| A11 | cross_module_macro_control | Macro STATE, local prior fact and cross-module column ownership | 0 |
| A12 | order_preconditions | Three preconditions, tie uncertainty, numeric and cardinality constraints | 3 |
| A13 | resource_not_precedence | RESOURCE annotation alone produces no directed reachability | 0 |
| A14 | side_effect_and_unknown_edges | Both typed IDs retained and specific proof obligations surfaced | 0 |
| A15 | unknown_scope | Local attribution and global empty binding | 2 |
| A16 | contradiction_precedence | Rejecting contradiction plus unknowns; five issue kinds cannot inject verdicts/advice | 5 |
| A17 | identity_integrity | Duplicate/forged IDs for five record families; enriched opaque issue accepted | 10 |
| A18 | reference_integrity | Dangling edges, nodes, modules, statement, issue, log and local fact refs | 21 |
| A19 | version_sequence_ownership | Version, sequence, column and log ownership violations | 6 |
| A20 | rehashed_false_graph_not_verified | Internally coherent false and omitted dependencies remain unverified | 2 |
| A21 | no_input_mutation | Input bytes/deep content preserved; output edits do not alias input | 3 |
| A22 | determinism_and_order | Set-like permutations change subject hash only; statement and fact order retained | 2 |
| A23 | subject_binding | Old hash rejects changed operation/edge/workspace/run/attempt; rebind is distinct | 5 |
| A24 | finite_bounds | Below/at/above all eight limits, encoding/invalid inputs and bounded layered graph | 40 |
| A25 | pure_offline_operation | Trap caller opens, I/O, reconstruction, store, processes/network and provider paths | 0 |
| A26 | authority_and_gate_preservation | Four fixed statuses across 23 positives; placeholder exit 3; five Windows command denials exit 2 | 29 |

Count after the attribution fix below: **26 methods; 133 explicit subtest executions; no skips**. A24's 24-layer
graph has 50 operations, 96 edges and 1,201 reachable ordered pairs despite
16,777,216 start-to-end routes. Only one predecessor row per reachable pair was
stored. Collection guards were isolated where full shape validation would prevent
testing a single limit. These are engineering thresholds, not measured capacity.
A25 uses an ordinary synthetic sentinel outside the call, patches relevant opens,
process/network and evidence APIs during it, then compares the sentinel bytes and
directory contents. It is a regression trap, not OS-enforced evaluation isolation.

## Failures and corrections

`.venv/bin/python -m unittest discover -s tests -p test_dependency_diagnostics.py -v`
(first run, exit 1): 26 methods in 0.760 s, one failure and two errors. A19
incorrectly expected a log observation's module to equal the source operation's
module. It now tests the actual run-owner mismatch and permits a legitimate
cross-module association. A20's invented DATA edge and A24's layered DATA edges
lacked producer/consumer node bindings and correctly refused with
`PRODUCER_CONSUMER_MISMATCH`. The synthetic challenges were corrected to provide
coherent bindings; the implementation gate and frozen oracle were not relaxed.
The second run returned 0 (26 in 0.797 s). Review found that A17 also needed a
valid positive control to isolate each failure. Its base now succeeds and its
duplicate/forged mutations require the specific identity diagnostic. A19 isolates
the invalid sequence; A22 permutes the operations array; A24 traps hostile
subclasses. The third run returned 0 (26 in 0.817 s). A counting runner then
independently observed 26 methods in 0.821 s with 128 subtests.

Read-only discovery initially used nonexistent `ci.yml`, `scaffold.yml` and
`verify.py` names; lookup failed (exit 1, `rg` exit 2 in one exploratory search).
Listing the tree located `.github/workflows/foundation.yml` and `evidence.py`.
`pip check` returned 0 with no broken requirements; it disabled an unwritable
cache. Neither issue changed the lock or runtime dependencies.

## Executed candidate checks

| Check | Actual result |
|---|---|
| Local macOS development suite before attribution fix | Exit 0, **693** tests in 17.795 s (667 preserved + 26 new); no skips |
| Focused counter | Exit 0; final 26 methods / 133 explicit subtests, no skips |
| All 23 frozen inputs, plus a preserved P2A example | 23 accepted; every witness finite and nonempty for represented pairs. Preserved synthetic `source_record.json` accepted by the pure input checks, exact digest `385423530208b08635de832bed57698b7278490f2cb7a43f08fd754b80df9155` |
| P1/P2A replay | Both demos exit 0. All 30 artifact files byte-identical and both complete parsed reports equal to the baseline; baseline also matched retained CP3D replay |
| Freeze and scope | Eight hashes above unchanged; all 90 baseline files outside the five permitted Markdown edits byte-identical. No changes to reconstruction, CLI, publication, tests from the baseline, workflow, dependencies or downstream pins |
| Local read-only downstream check | PASS, exit 0; clean checkout at `bc754e0f1204a99020c864df2a5b25983005e09c`, 20 files checked, no changes/missing files. This checks compatibility inputs only |

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python "$T/review_tests.py"
.venv/bin/python "$T/compare_candidate.py"
.venv/bin/sas-re check-baseline --checkout /private/tmp/sas-re-downstream-bc754e0
.venv/bin/python -m pip check
```

The audit-only `review_tests.py` records `addSubTest` events on discovery of the
single new test file. `compare_candidate.py` runs both demos into `$T/p1-candidate`
and `$T/p2a-candidate`, compares full relative-path/original-byte maps and parsed
reports and recomputes the eight hashes; invocations, results and manifests are in
`$T/candidate-preservation.json`. Neither audit script is a runtime dependency.

A separate read-only `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:tests .venv/bin/python -`
review compared graph math to enumeration of positive walks of length 1–3 under
all 512 directed ORDER masks on three vertices; missing ORDER arcs had RESOURCE
annotations. All 4,608 pair/witness outcomes matched (3,072 reachable; 1,152
missing distinct pairs), as did 1,080 SCCs, cycle flags and original internal
edge IDs. This is a small topology oracle, not a SAS oracle. A second review
checked 400 two-operation access graphs (52 each of RAW/WAR/WAW), plus 32 DATA
coverage subsets over two logical dataset groups. A 100-operation shared-dataset
case produced the expected finite maxima of 14,850 conflicts and 9,900 no-path
rows with no mutable input/output aliases. Its result exceeded 8 MiB; the limit
is on the canonical input, not a promise that output fits the same size.

## Changed files and proof limits

New: `src/sas_re/_dependency_diagnostics.py`, `tests/dependency_vectors.py`,
`tests/test_dependency_diagnostics.py`, `docs/P3_A1_DESIGN.md` and this report.
Updated: `README.md`, `AGENTS.md`, `docs/APPROVALS.md`, `docs/OPEN_DECISIONS.md`,
`docs/BEST_PRACTICES_ADOPTION.md`. No other repository changes are part of P3-A1.

No private inputs, SAS execution, provider calls, gold, Windows qualification,
performance measurements or downstream integration. The Windows denial checks
are simulations: native Windows remains **BLOCKED / NOT_RUN**. Original-byte
identities and append-only evidence are exercised only in the historical public
fixtures. Graph hash equality is not evidence of true SAS dependencies, authentic
inventory, freshness, sealed origin, physical aliasing or safe execution.
P3-A1 ends at engineering review; P2B, operational P3, P3-A2, P4, CP4 and CP5
have not started.

## Review correction: issue text is not diagnostic authority

After the initial development pass, a reviewer supplied an unknown with code
`VERIFIED` and an instruction recommending concurrent execution on Spark. Its
top-level semantic acceptance stayed BLOCKED, but the finding had repeated the
caller's code and proof text. That was an attribution defect. The final code
generates both fields from the closed issue kind, retains the canonical issue
and operation/file refs and identifies the original collection in the bound
parent. The graph's untrusted strings remain inspectable there. A regression
challenges all five kinds with injected verdicts/advice and checks that changing
only caller text changes the parent digest but cannot change the finding. No
frozen expectations changed. The final focused run returned 0 (26 methods in
0.895 s); the final root counting replay returned 0 (26 methods in 0.782 s,
133 explicit subtests, no skips). The final preservation rerun
`"$PY" "$T/compare_candidate.py" --label final` returned 0 with unchanged
artifacts, reports, all 90 protected files and the eight hashes above.

| Final file | SHA-256 |
|---|---|
| Private diagnostic implementation | `d6e7ea9d70b1ae4aa10ad2fcf5488dda5a30a6b17c256ad3ab393b8d365041a7` |
| A01–A26 tests | `1800fbb734a0bc0b7f5248d6d782ce88b594b06ff14a237897bff8f41d0f3251` |
| Pre-candidate vectors | `7e8e5f6d3c37bf3ef7553abb3511446c23a22562f460398cb7e5344b95b6a90b` |

## Final local installation matrix

All three modes ran the **same 693 methods**, with no failures or skips. Local
environment: macOS 26.6.2 build 25G83, arm64, CPython 3.12.5. The isolated fresh
clone and wheel bind implementation commit `927410103a8b458ea690f6b5dfcac4e070814c0c`.

| Mode | Verified package origin | Test result |
|---|---|---|
| Development, final attribution fix | Existing development checkout | Exit 0, 693 in 18.078 s |
| Fresh local clone | `fresh/src/sas_re/_dependency_diagnostics.py` | Exit 0, 693 in 17.506 s |
| Installed wheel, outside the checkout | Existing separate environment's `lib/python3.12/site-packages/sas_re/_dependency_diagnostics.py`, contents hash checked | Exit 0, 693 in 17.556 s |

```sh
# From P; T and PY are as defined above. No new dependency downloaded.
git clone --no-hardlinks --quiet . "$T/fresh"
git -C "$T/fresh" rev-parse HEAD
# From T/fresh:
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$T/fresh/src"
"$PY" -c 'from pathlib import Path; import sas_re._dependency_diagnostics as d; assert Path(d.__file__).resolve().is_relative_to(Path.cwd() / "src"); print(d.__file__)'
"$PY" -m unittest discover -s tests -v
"$PY" -m pip wheel --no-index --no-deps --no-build-isolation --no-cache-dir --wheel-dir "$T/wheels" .
W=/private/tmp/sas-re-p2a-wheel-env/bin/python
"$W" -m pip install --no-index --no-deps --no-cache-dir --force-reinstall "$T"/wheels/*.whl
"$W" -m pip check
# From T:
unset PYTHONPATH
"$W" -I -c 'from pathlib import Path; import hashlib, sysconfig, sas_re._dependency_diagnostics as d; p=Path(d.__file__); assert p.is_relative_to(sysconfig.get_path("purelib")); assert hashlib.sha256(p.read_bytes()).hexdigest()=="d6e7ea9d70b1ae4aa10ad2fcf5488dda5a30a6b17c256ad3ab393b8d365041a7"; print(p)'
"$W" -m unittest discover -s "$T/fresh/tests" -v
PYTHONPATH="$P/tests" "$PY" -c 'import json, dependency_vectors as v; print(json.dumps([v.topology("chain"),v.FROZEN_GRAPH_SHA256["chain"]]))' | PATH='' "$W" -I -c 'import json,sys; from sas_re._dependency_diagnostics import diagnose,witness; g,h=json.load(sys.stdin); r=diagnose(g,h); path=witness(r,g["operations"][0]["operation_id"],g["operations"][2]["operation_id"]); assert path==[e["edge_id"] for e in g["edges"]]; print(r["parent_graph_sha256"],len(path),r["semantic_acceptance"])'
```

All commands above returned 0. The final pipeline used stdin only in the caller's
harness: the private function takes the decoded in-memory graph and digest. It
returned the exact frozen chain digest, two original edge IDs and acceptance
BLOCKED without an executable on PATH. The wheel
`sas_reverse_engineering-0.3.0-py3-none-any.whl` weighed 113,117 bytes, SHA-256
`1813c48e397952297ef0417db8c7f54a25d7fbce12af39431b3dc7d2d005292b` for this
build. Only this project wheel was replaced in the existing disposable wheel
environment. `pip check` found no broken requirements. The dependency lock and
packaging version were not changed; no Windows installation was attempted.

```sh
git add -- AGENTS.md README.md docs/APPROVALS.md docs/BEST_PRACTICES_ADOPTION.md docs/OPEN_DECISIONS.md docs/P3_A1_DESIGN.md docs/P3_A1_VALIDATION.md src/sas_re/_dependency_diagnostics.py tests/test_dependency_diagnostics.py
git diff --cached --check
.venv/bin/python scripts/check_repository.py
.venv/bin/python "$T/check_docs.py"
git -C "$T/fresh" status --porcelain
```

Staged guard PASS (exit 0, no errors); scope/fence/link/method check passed, with
10 authorized paths and all 26 roadmap methods in code and report. The guard
checks selected tracked-path and credential patterns only, not complete DLP.
Whitespace and clean-clone checks returned 0; no tracked or untracked changes in
the fresh clone. Test times describe suite executions, not SAS benchmarks.

## Hosted Linux verification

[GitHub Actions run 42299912385](https://github.com/keshavnath1/sas-reverse-engineering/actions/runs/42299912385)
completed **success** at implementation commit `927410103a8b458ea690f6b5dfcac4e070814c0c`.
The foundation job used Ubuntu 24.04.5 x64 and CPython 3.12.5. In that clean CI
checkout, `python -m unittest discover -s tests -v` ran **693 tests in 24.047 s**;
after wheel installation, from `$RUNNER_TEMP`, `python -m unittest discover -s
"$GITHUB_WORKSPACE/tests" -v` ran **693 tests in 25.668 s**. Both passed. The
repository guard, dependency check, synthetic demos, packaging and installed
commands also succeeded in the unchanged [workflow](../.github/workflows/foundation.yml).
The separate downstream-drift job's `sas-re check-baseline --remote` returned
PASS at exactly `bc754e0f1204a99020c864df2a5b25983005e09c`. CI logs were read via
`GET /repos/keshavnath1/sas-reverse-engineering/actions/runs/42299912385/jobs` and
job logs for foundation `128174703856` and drift `128174704215`. This is hosted
Linux regression evidence, not Windows qualification, workstation release
qualification or independent SAS semantic evaluation.
