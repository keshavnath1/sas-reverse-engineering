# SM-3B local validation

Baseline `98f25e7727a5f39d6d1e7145086312309a93f370`.
Local environment was macOS 26.6.2 ARM64 with CPython 3.12.5.

## Implemented scope

The existing developer command accepts the separate
`--recover-missing-exclusions` flag together with `--recover-status-rules`.
It uses source-only review format version 3. Default mode and the SM-2 flag
alone retain their existing formats and package bytes.

The extension reuses the existing statement frames, tokens and cursor in
`scripts/source_rules.py`. It appends only a contiguous MISSING, CMISS, CMISS
prefix after the status and linked-label unit. MISSING preserves direct
predicate evaluation. CMISS preserves the explicit greater-than comparison and
zero literal. Arguments are explicit ordinary identifiers normalized by the
existing cursor, in source order, with a limit of 32 per CMISS call.
Original spelling remains bound through the original source spans.

The existing ordered records retain hashes, parser reasons and
SOURCE_RECOGNIZED classification. The added rules reuse the current-row DELETE
action. Their false-predicate prerequisites reference existing list positions.

| Rule | Required false predicates |
| --- | --- |
| 0 | None |
| 1 | 0 |
| 2 | 0, 1 |
| 3 | 0 |
| 4 | 0, 3 |
| 5 | 0, 3, 4 |

List order places rule 3 after the branch pair. Neither assignment predicate
gates rule 3. Both branches and no-assignment fallthrough therefore remain
eligible for the subsequent checks. This is a recovered source relationship.
No observation is evaluated.

The first unsupported or ambiguous exclusion ends recovery. The statement and
later exclusions retain separate gap records. A recognized prefix remains
available with recovery PARTIAL. Attached ELSE clauses, malformed comments,
nested expressions, OF lists, ranges, compound guards, alternate thresholds and
unsupported action blocks do not become recognized exclusions.

TRACE displays each recovered fact once. MAP and behavioral obligations link
to the same original byte-coordinate anchors. Input/output schemas, actual
labels and row survival remain UNKNOWN. The review explicitly leaves lazy
evaluation inside CMISS unestablished.

## Focused validation

Three tests were added to the existing source-review test file. All inputs
are public synthetic text.

- Exact six-rule prerequisites, function/argument records, direct and comparison
  predicates, first-exclusion precedence, CRLF/UTF-8 original spans, source/span
  hashes, retained parser reasons, deterministic output and resolved TRACE links.
- Twelve unsupported or ambiguous variants at different positions. Each verifies
  the recognized prefix and preservation of every remaining gap, including a
  malformed-comment barrier and a lexical error in a later exclusion.
- Frozen SM-2 DATA and combined package hashes captured independently from the
  approved baseline, plus refusal when the new flag lacks its SM-2 prerequisite.

These checks inspect records and rendered output. They supply no behavioral
oracle, reference rows, inferred argument types or SAS evaluation results.

The first new focused run had one test assertion error because subprocess
stderr is bytes. The assertion was corrected. Review also identified and
guarded an empty-token access at a malformed-comment barrier, and that case
passed in the focused run. The final focused command was

```bash
.venv/bin/python -m unittest discover -s tests -p test_review_source.py -v
```

It exited 0 with 16 tests passing in 12.271 seconds.

The full regression command was

```bash
.venv/bin/python -m unittest discover -s tests -v
```

It exited 0 with 804 tests passing in 61.345 seconds, preserving all 801 existing
tests and adding the three focused tests above.

## Preservation checks

All completed commands below exited 0.

```bash
git diff --check
git diff --exit-code 98f25e7 -- examples src requirements.lock skills reference
.venv/bin/python scripts/check_repository.py
.venv/bin/python /private/tmp/sas-re-sk1-proof.q6kb2j8q/preserve_tf1.py --label sm3b-local --source .
```

The replay compared 30 historical P1/P2A artifacts, two complete historical
reports, eight frozen hashes and three diagnostic hashes successfully.
Accepted examples, canonical contracts, parser implementation, identities,
skills, dependency lock and downstream pin remained byte-identical.

Scripts from the approved baseline were extracted with
`git archive 98f25e7727a5f39d6d1e7145086312309a93f370 scripts`.
Baseline and candidate commands processed the same external synthetic file in
six combinations of DATA, SORT or combined ranges and legacy or SM-2 mode.
Every package filename and byte hash matched. The first baseline invocation
correctly refused a synthetic source placed inside its extracted checkout.
The source was moved outside that checkout before collecting comparisons.

The repository guard passed its tracked-file and limited credential-pattern
checks. The diff and new report were reviewed directly. Validation used public
synthetic sources only. No real-source review packages or proprietary inputs
are included in this change.

## Limits

Native Windows, Linux CI and installed-wheel verification were not run during
this local implementation checkpoint. Source recognition supplies no claim of
successful SAS execution, row survival, variable types or semantic equivalence.

```text
artifact_authority: DRAFT
behavioral_evidence: UNAVAILABLE
semantic_verification: UNVERIFIABLE
semantic_acceptance: BLOCKED
benchmark_execution: NOT_RUN
```
