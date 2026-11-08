# SM-2 local validation

Baseline `ce65288ddea3d0c237e1e1a5aaa7ff9cba5b9c22`.
Local checks ran on macOS 26.6.2 ARM64 with CPython 3.12.5.

## Implemented boundary

The developer command accepts `--recover-status-rules`. This is an opt-in
compatibility choice. Without it, earlier single-span and combined package
bytes remain reproducible. Opted-in DATA and dependency reviews use
`source-only-data/2` and `source-only-dependency/2`, respectively.
The canonical v2 evidence contract remains frozen.

`scripts/source_rules.py` reuses the existing SAS statement framing, tokens,
cursor and numeric literal reader. It recognizes one contiguous three-statement
unit immediately after SET, allowing intervening standalone comments. It requires
a character-literal NOT IN exclusion, then two equality-guarded numeric-literal
assignments to one target with an immediate ELSE IF link. Both assignment guards
use the filter variable. Broader or ambiguous forms remain unresolved as a unit.

Each recovered record owns its original span, hash, parser reason codes,
predicate and action. List-index references to earlier predicates preserve
execution prerequisites without new persistent IDs. DELETE terminates the
current row iteration and suppresses its output. A matched first assignment
skips the alternative. The branch pair explicitly records no assignment on
fallthrough. Subsequent unresolved statements can still exclude or change a row.

The membership set may include a value unmatched by either assignment guard.
Recognition therefore never assumes that membership proves a binary label.
Schema, character comparison behavior and actual output values remain unknown.
MISSING and CMISS continue to have separate unresolved records.

TRACE renders recovered facts once. MAP and behavioral obligations reference
those records through existing byte-coordinate anchors. The source-only
recognizer neither evaluates input rows nor changes canonical reconstruction.

## Executed checks

All commands exited 0 unless noted below.

- `.venv/bin/python -m unittest discover -s tests -p test_review_source.py -v`
  passed 13 tests in 7.272 seconds.
- `.venv/bin/python -m unittest discover -s tests -v` passed 801 tests in
  53.042 seconds, preserving all 798 regressions and adding three focused tests.
- `.venv/bin/python scripts/check_repository.py` passed. This guard inspects
  tracked files and selected credential patterns. The new helper, test literals
  and this report were also reviewed directly.
- `git diff --check` passed.
- `git diff --exit-code ce65288 -- examples src requirements.lock skills reference`
  passed. Accepted examples, engine/parser implementation, canonical contracts,
  dependency lock and downstream compatibility metadata remained byte-identical.
- `.venv/bin/python /private/tmp/sas-re-sk1-proof.q6kb2j8q/preserve_tf1.py --label sm2-local --source .`
  replayed and compared all 30 historical P1/P2A artifacts, both complete
  reports, eight frozen hashes and three diagnostic hashes successfully.

The three new tests cover exact predicates and literal actions for both
assignment branches, exclusion polarity, precedence, unmatched-member
fallthrough, original CRLF/UTF-8 byte spans, all three remaining gaps,
deterministic output, escaped literal presentation, TRACE links, unchanged SORT
output, and eleven unsupported/ambiguous forms. They inspect source records
and command output. No row interpreter or behavioral oracle was introduced.

No product test failed. An editing helper initially had an unterminated Python
string and exited before writing a file. It was corrected before focused tests.

## Package preservation and authorized source check

A read-only baseline archive was obtained with
`git archive ce65288ddea3d0c237e1e1a5aaa7ff9cba5b9c22 scripts`.
Baseline and candidate commands processed the same public synthetic file in
DATA-only, SORT-only and combined modes. Complete output-file maps compared
byte-identically without the recovery flag, including MIGRATION_REVIEW.md in
combined mode.

The approved private DATA/SORT spans were also inspected locally using the
existing source path and caller-supplied expected digest. The invocation was

```bash
.venv/bin/python -IB scripts/review_source.py \
  --source "$AUTHORIZED_SAS_PATH" --source-sha256 "$EXPECTED_SHA256" \
  --lines 314:335 --lines 391:393 --recover-status-rules \
  --destination /tmp/sas-re-source-sm2-recovered
```

The private package contains three recovered source rules and the three
original unresolved exclusions, with 19 declared KEEP selections. Assertions
compared source identity, all six statement spans, remaining gap records,
interval inventory and SORT selection to the earlier authorized RS-5B package.
All matched. The input remained read-only. No private source excerpts or
generated private review packages are included in the repository.

The command was also run without the flag for each approved single span.
`diff -rq` against the existing private DATA and SORT packages passed for both.
The caller's expected source hash was verified by each invocation.

## Qualification limits

This is local source-recognition validation. Character schema, SAS comparison
semantics, input rows, execution reachability and actual labels need attributable
reference evidence. Native Windows, Linux CI and an installed-wheel test run
were not executed in this checkpoint.

```text
artifact_authority: DRAFT
behavioral_evidence: UNAVAILABLE
semantic_verification: UNVERIFIABLE
semantic_acceptance: BLOCKED
benchmark_execution: NOT_RUN
```
