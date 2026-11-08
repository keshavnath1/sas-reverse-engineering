# P2A validation record

P2A is deterministic, public-synthetic reconstruction only. Semantic acceptance
remains **BLOCKED**, semantic verification **UNVERIFIABLE**, authority **DRAFT**,
and benchmarks **NOT_RUN**. P2B isolation, protected gold and the 360-attempt
campaign have not been implemented or run. No SAS or private workload was executed.

Baseline: planning commit `e13705c67c5984b2cb6bc8d4c797a188fd6421e2`; package 0.3.0,
Python 3.12.5, macOS arm64. The v1 schema and dependency lock remain byte-identical.
No dependency was added. Implementation commit:
`e5f5eb2fde973acf2dd059b4522247aa6fd2283c`. Subsequent changes to this report are
documentation only. Pending hosted checks are not passes.

## Checks and results

| Check | Result |
|---|---|
| Original P0/P1 baseline before implementation | 138 tests PASS |
| Final development suite | 389 tests PASS, exit 0 |
| Fresh Git checkout and fresh hash-locked virtual environment | 389 tests PASS, exit 0 |
| Installed 0.3.0 wheel outside the checkout | 389 tests PASS, exit 0 |
| Public P2A fixture suite | 187 tests PASS |
| Repository guard after staging | PASS, no findings |
| Python compilation and diff whitespace | PASS |
| Workflow YAML parse | PASS |
| Dependency consistency | PASS: no broken requirements |
| Local Agent-mastery compatibility | PASS: exact pinned HEAD, clean tree, 20 matching digests |
| Remote Agent-mastery drift | PASS: branch resolves to the frozen pin |
| Public synthetic CLI demo | PASS for expected outcomes; independent acceptance BLOCKED |
| Hosted CI | PASS: [run 42104309091](https://github.com/keshavnath1/sas-reverse-engineering/actions/runs/42104309091), both jobs successful |

The status test now expects phase P2A and adds blocked-acceptance checks; existing
P0/P1 behavioral, contract and security assertions were retained. The public suite
comprises 12 complete-but-blocked cases, 61 reviewed fact assertions, 26 false-claim
mutations, 70 syntax boundaries, 16 contextual boundaries, review-digest validation
and explicit missing-join-policy refusal. Of the 26 mutations, 22 pass schema and
fail deterministic source consistency; four violate the closed schema and are
rejected there. All retain valid citations; accepted-shape mutations recompute
operation/edge references and IDs so stale hashes are not the reason for refusal.

The 389-test suite contains the 138 P0/P1 regressions, 187 public fixture tests,
20 parser mechanics tests, 22 graph review regressions and 22 workflow/observation
tests. Additional parser, graph and workflow tests cover original spans, bounded syntax,
compile-time projection, numeric/state proof gaps, changed ordering keys, control
lineage, cross-module ownership, immutable v1 history, explicit revision maps,
stale source/profile, append-only attempts and unchanged source bytes. No score is
reported as independent semantic precision/recall or a P2B acceptance result.

## Exact commands

Development working directory:
`/Users/divyasreegundaram/Downloads/sas-migration-skill-enhancement-v2/sas-reverse-engineering`.

```bash
.venv/bin/python -m pip install --no-deps --no-build-isolation -e .
.venv/bin/python -m pip check
.venv/bin/python -m unittest discover -s tests -v > /private/tmp/sas-re-p2a-development-tests.txt 2>&1
.venv/bin/python -m unittest discover -s tests -p test_p2a_public.py -v
.venv/bin/python -m unittest discover -s tests -p test_p2a_runs.py -v
.venv/bin/python -m unittest discover -s tests -p test_p2a_graph.py -v
.venv/bin/python -m unittest discover -s tests -p test_sas_subset.py -v
.venv/bin/python -m compileall -q src scripts tests
git diff --check
.venv/bin/sas-re check-baseline --checkout /private/tmp/sas-re-downstream-bc754e0
.venv/bin/sas-re check-baseline --remote
ruby -e 'require "yaml"; YAML.load_file(".github/workflows/foundation.yml"); puts "workflow YAML parsed"'
.venv/bin/python scripts/p2a_demo.py --destination /private/tmp/sas-re-p2a-demo-final > /private/tmp/sas-re-p2a-demo-final.json
SOURCE_DATE_EPOCH=1793906985 .venv/bin/python -m pip wheel --no-deps --no-build-isolation --wheel-dir dist .
shasum -a 256 dist/sas_reverse_engineering-0.3.0-py3-none-any.whl
```

The baseline commands are read-only; downstream pin remains
`bc754e0f1204a99020c864df2a5b25983005e09c`. No fetch, pull, repin, or downstream
write was used. Pip reported an unwritable cache and disabled caching; installs
succeeded without bypassing hash checks or dependency constraints.

Fresh environments were created and installed offline from the existing locked
wheelhouse using these commands from the development directory:

```bash
/opt/homebrew/bin/python3.12 -m venv /private/tmp/sas-re-p2a-fresh-env
/opt/homebrew/bin/python3.12 -m venv /private/tmp/sas-re-p2a-wheel-env
/private/tmp/sas-re-p2a-fresh-env/bin/python -m pip install --no-index --find-links /private/tmp/sas-re-p1-wheels --require-hashes --only-binary=:all: -r requirements.lock
/private/tmp/sas-re-p2a-wheel-env/bin/python -m pip install --no-index --find-links /private/tmp/sas-re-p1-wheels --require-hashes --only-binary=:all: -r requirements.lock
```

Fresh checkout selected exactly `e5f5eb2fde973acf2dd059b4522247aa6fd2283c`, without
Git object hardlinks. Fresh and installed-wheel commands below all exited 0.
From `/private/tmp`, except the fresh-checkout test/guard/demo commands which ran
in `/private/tmp/sas-re-p2a-fresh`:

```bash
git clone --no-hardlinks /Users/divyasreegundaram/Downloads/sas-migration-skill-enhancement-v2/sas-reverse-engineering /private/tmp/sas-re-p2a-fresh
/private/tmp/sas-re-p2a-fresh-env/bin/python -m pip install --no-deps --no-build-isolation -e /private/tmp/sas-re-p2a-fresh
/private/tmp/sas-re-p2a-fresh-env/bin/python -m unittest discover -s tests -v > /private/tmp/sas-re-p2a-fresh-tests.txt 2>&1
/private/tmp/sas-re-p2a-fresh-env/bin/python scripts/check_repository.py
/private/tmp/sas-re-p2a-fresh-env/bin/python scripts/p2a_demo.py --destination /private/tmp/sas-re-p2a-demo-fresh > /private/tmp/sas-re-p2a-demo-fresh.json
/private/tmp/sas-re-p2a-fresh-env/bin/python -m pip check
git status --porcelain
/private/tmp/sas-re-p2a-wheel-env/bin/python -m pip install --no-deps /Users/divyasreegundaram/Downloads/sas-migration-skill-enhancement-v2/sas-reverse-engineering/dist/sas_reverse_engineering-0.3.0-py3-none-any.whl
/private/tmp/sas-re-p2a-wheel-env/bin/python -c 'import sas_re; print(sas_re.__file__); assert "/site-packages/" in sas_re.__file__'
/private/tmp/sas-re-p2a-wheel-env/bin/python -m unittest discover -s /private/tmp/sas-re-p2a-fresh/tests -v > /private/tmp/sas-re-p2a-wheel-tests.txt 2>&1
/private/tmp/sas-re-p2a-wheel-env/bin/python /private/tmp/sas-re-p2a-fresh/scripts/p2a_demo.py --destination /private/tmp/sas-re-p2a-demo-wheel > /private/tmp/sas-re-p2a-demo-wheel.json
/private/tmp/sas-re-p2a-wheel-env/bin/python -m pip check
```

Observed wheel import:
`/private/tmp/sas-re-p2a-wheel-env/lib/python3.12/site-packages/sas_re/__init__.py`.
Fresh checkout porcelain was empty. Suite durations were 13.649 seconds in the
development checkout, 15.140 fresh, and 15.053 installed wheel; these are test
durations, not workload benchmarks. Complete demo JSON equality was checked from
the development checkout with this executed Python body:

```python
import json
from pathlib import Path
reports = [json.loads(Path(p).read_bytes()) for p in (
    '/private/tmp/sas-re-p2a-demo-final.json',
    '/private/tmp/sas-re-p2a-demo-fresh.json',
    '/private/tmp/sas-re-p2a-demo-wheel.json')]
assert reports[0] == reports[1] == reports[2]
```

All three reports, including graph/seal hashes, were identical. Final staged
guard and whitespace commands were `.venv/bin/python scripts/check_repository.py`
and `git diff --cached --check`, both exit 0. Local documentation links were also
checked for existence. Temporary transcripts/artifacts are outside Git and may
disappear. Tests and
fixture generators are committed for reproduction with new empty destinations.

Publication used `git push origin main`, exit 0, advancing the remote from
`e13705c` to `7da79ab4b72f894d473948ce198436a5abe1f6cd`. GitHub Actions run
`42104309091` completed successfully at that exact commit; both `foundation`
and `downstream-drift` passed. The foundation job log independently records
389 checkout tests (15.866 seconds) and 389 installed-wheel tests (15.725 seconds),
both `OK`, plus successful public CLI demonstrations with semantic acceptance
still BLOCKED and historical bytes unchanged. These are CI test durations,
not workload benchmarks. This report's subsequent documentation-only update
does not alter the tested implementation.

Hosted results were read through the GitHub connector using these exact GET
resources and decoded job-log request:

```text
https://api.github.com/repos/keshavnath1/sas-reverse-engineering/actions/runs?head_sha=7da79ab4b72f894d473948ce198436a5abe1f6cd&per_page=5
https://api.github.com/repos/keshavnath1/sas-reverse-engineering/actions/runs/42104309091
https://api.github.com/repos/keshavnath1/sas-reverse-engineering/actions/runs/42104309091/jobs
fetch_workflow_job_logs(repo_full_name="keshavnath1/sas-reverse-engineering", job_id=127514966739)
```

## Hash evidence

| Artifact | SHA-256 |
|---|---|
| Specification v2 ZIP | `e3cbf3d9df6cc20c594261556c5e3ea1dfc292c9c1a30672c2d7b1a736b9718e` |
| Preserved v1 schema | `15e3265fac9af300b40967580998ef4ac90eb1d830a10ce201855fc4ec2738a2` |
| Canonical v2 schema | `093216d16bb02e91a3997c97175420bf2257982f5a5fe3a4374ef92f7637a90b` |
| Unchanged requirements.lock | `4676c7fe0a41ce2fdb35c2fb10cc014a8b352a8ca71029eb28b7373c0053e19b` |
| Reviewed public expectations | `f42549738a041db87d3547adec59ddfd0f9b15aa2621f1cf0b7ea7fa9f7ffd93` |
| Built 0.3.0 wheel | `b7b81cd90b2060a16f36a5a597ca4f8cc15c5a1d178fa0141cfecc42c4e0c968` |
| Public SORT/DATA demo source fingerprint | `c94ab61f4f4f84f885079f7d71aa71c98a4b7118d21c2eb92d4d26b3cbf4ccb4` |
| Public demo canonical graph | `385423530208b08635de832bed57698b7278490f2cb7a43f08fd754b80df9155` |

The demo observed inventory PASS/0, reconstruction and check BLOCKED/2 with
COMPLETE/PASSED deterministic status, then stale-source FAIL/1 after a synthetic
edit. Historical attempt bytes stayed unchanged. The wrapper returned 0 because
these were the expected gates; it did not convert semantic acceptance to PASS.

## Failures found and fixes

- The first workflow test run had 10 failures and three errors because the new
  profile loader rejected valid ASCII CONFIG files. Accepting the approved ASCII
  encoding fixed the common cause; all 17 tests then passed.
- The first public fixture run had eight errors because operation anchors began
  at preceding block comments. Separating comments and anchoring operations at
  their syntax tokens fixed LOG/LST bindings and macro definition citations;
  reviewed expected meanings were not changed to fit output.
- Source review found conditional/state range underestimation, input RETAIN
  incorrectly overriding SET values, SUM recurrence treated as constant delta,
  pre-SET current-row assumptions, uncertainty leaking from producers, and changed
  sort keys retaining downstream order claims. Explicit state/context blockers,
  conservative bounds, correct phase/lineage facts and uncertainty propagation
  address the concrete counterexamples. They do not constitute full SAS proof.
- Review corrected a test citation-key typo and a mutation that rehashed an
  operation without updating coverage references. Final negative tests assert
  nonempty preserved citations and repair references before challenging meaning.
- Review found mismatched/duplicate LOG step headers and ambiguous duplicate LST
  column names. New checks preserve contradictions/blockers. Oversized count
  lexemes are bounded before integer conversion. BY-before-input is refused
  against the documented SAS statement-order rule.

No assertion or acceptance threshold was weakened to hide a failure. Direct
retrieval of several official SAS pages timed out; official search excerpts and
alternate official pages supported the public expectation review. This is not
runtime verification. The parser agent also ran 3,000 seeded lexical fuzz inputs
plus long/deep-expression probes without crashes; that exploratory exercise is
not counted as independent semantic evaluation or as unit tests.

The first `git push origin main` was denied by automatic approval review before
execution. Its reason was that it did not recognize P2A approval in the user's
pasted attachment and considered default-branch publication unauthorized. The
original request was reread to establish the explicit D08-A/B P2A approval;
the same push was then approved and succeeded. No alternate publication route
or approval bypass was used. Hosted results are recorded above.

## Files and proof boundary

Created: `docs/P2A_DESIGN.md`, this report, `docs/P2A_FIXTURE_REVIEW.md`,
`scripts/p2a_demo.py`, v2 schema, `sas_subset.py`, `semantic.py`, `observations.py`,
`semantic_runs.py`, public expectations/support and the P2A/parser test modules.
Updated: README, SECURITY, AGENTS, approval/decision records, historical P2 planning
status, CLI, explicit contract dispatch, package metadata, phase status test and CI.
No raw intake, protected answers, credentials, translated SAS, downstream code,
new model/runtime dependency or private artifacts are included.

The deterministic checker shares reconstruction logic and can share defects.
Separate development review is not hidden-gold isolation or a human SAS expert
sign-off. Supported syntax can remain PARTIAL when numeric, state, provenance or
ordering preconditions cannot be proved. Hashes demonstrate integrity against
retained evidence, not authenticated production origin. Public synthetic rows,
LOG metrics and hand traces are not execution measurements.

Stop after P2A. Recommended P2B readiness: separately approve D08-C/D09, name the
gold author/reviewer/custodian, select provider/tool/egress policies, provision
and test evaluator isolation and immutable handoff, then freeze and authorize the
two-track 360-attempt campaign. No P2B, P3 or downstream human gate is advanced here.
