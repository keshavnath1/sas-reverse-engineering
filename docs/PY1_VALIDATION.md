# PY-1 development preparation candidate

Baseline: `81b30a11af82ff1e6beee1420d3e596eb1a5c4ba`.
This is a Python candidate implementing documented engineering assumptions.
It is neither an independent behavioral oracle nor an accepted SAS replacement.
Historical source/run provenance remains UNBOUND; BV-4 remains NOT_RUN.

```text
artifact_authority: DRAFT
behavioral_evidence: UNAVAILABLE
semantic_verification: UNVERIFIABLE
semantic_acceptance: BLOCKED
reference_experiment: NOT_RUN
benchmark_execution: NOT_RUN
```

## Direct developer call

From the repository root in Python 3.12, import the development module directly.
It is not part of the installed CLI or package API and has no file/network I/O.

```python
from scripts.preparation_candidate import Character, NumericMissing, SyntheticRecord, prepare

record = SyntheticRecord(
    case_id="D01",
    status=Character("B       "),
    id=0,
    numeric_group=(1,) * 12,
    character_group=(Character(".   "),) * 5,
)
result = prepare(record)
# Inspect result.output, first_exclusion_rule, label_assignment_branch and trace.
# A surviving output is a Python candidate result, not a SAS reference answer.

probe = SyntheticRecord(
    case_id="D02", status=Character("C       "), id=NumericMissing(".A"),
    numeric_group=(1,) * 12, character_group=(Character("X   "),) * 5,
    initial_default=9,
)
probe_result = prepare(probe, mode="isolated_pair")
```

The result is an immutable `CandidateResult`. `SURVIVED` carries an immutable
`CandidateOutput`; `EXCLUDED` carries no output and identifies the first exclusion
rule. The label branch is 1, 2 or absent independently of survival. All results
carry the six fixed authority/evidence statuses above. `None` appears only in
result metadata for an absent output/decision, never as an accepted missing cell.

## Explicit development contract and assumptions

- One immutable `SyntheticRecord`, not a dictionary or dataframe. Audit-only
  `case_id` is three ASCII letters/digits; a one-record API cannot establish
  uniqueness across a workload. Numeric arguments are an ordered tuple of twelve
  values (aliases n1 through n12); character arguments are an ordered tuple of
  five (c1 through c5). The output preserves their order and stored values.
- Numeric cells accept built-in finite floats, built-in integers within inclusive
  `[-2**53, 2**53]`, or `NumericMissing`. Numeric missing tags are exactly `.`,
  `._`, and `.A` through `.Z`; their spelling is preserved. All these tags are
  assumed missing. Zero, negative numbers and negative zero are nonmissing.
  Booleans, NaN, infinity, Decimal, strings and `None` are unsupported. No numeric
  conversion, arithmetic model, rounding or tolerance is introduced.
- `Character` contains already-stored printable ASCII. Status must have exactly
  eight characters and each character-group field exactly four. The caller must
  supply storage padding. The function neither pads nor truncates, strips,
  case-folds or coerces. Admission and assignment compare exact padded aliases
  `A` and `B`. Leading spaces and lowercase variants do not become admitted.
  A character-group value is assumed missing only when all four characters are
  ASCII spaces; character period remains nonmissing. Tabs, newlines, Unicode,
  empty strings and different widths are unsupported, not normalized.
- The entire typed contract is checked before rule execution. Unsupported forms
  raise `ValueError`, even in fields that a valid row might never reach. Input
  validation is not a recorded rule evaluation or an exclusion decision.
- Full mode preserves NOT IN exclusion, the first assignment and linked
  alternative, followed by MISSING, numeric CMISS and character CMISS. Rule 2 is
  evaluated only if rule 1 is false. Rule 3 is outside both assignment branches.
  Its only full-mode predecessor condition is rule 0 false; rule 4 also requires
  3 false, and rule 5 additionally requires 4 false. Returning on exclusion stops
  the current call; no later predicate is evaluated for diagnostics.
- Each CMISS-like candidate check counts the entire ordered argument tuple before
  comparing with zero. This is a chosen Python evaluation strategy, not a claim
  about SAS CMISS argument laziness. No generic expression evaluator is present.
- `initial_default` defaults to ordinary numeric missing. The isolated-pair mode
  explicitly omits rule 0, preserves that value when neither branch matches, and
  still reaches later exclusions. Full-mode fallthrough is structurally
  unreachable with the two admitted aliases. No row-retained PDV state is modeled.

Other SAS character comparison rules, implicit conversions, mixed-type CMISS
groups, arbitrary schemas/widths, collations, encodings, full DATA-step behavior,
SORT, CSV import and real-workload execution remain outside this contract.

## Trace ownership and comparison with BV-4

Diagnostics are observations of the Python call. Each reached predicate is logged
once, followed where applicable by an assignment, no-assignment or row-exclusion
action. The function does not invent events for skipped rules. The existing rule
indices and original inclusive line / half-open byte coordinates are navigation
references to existing TRACE/MAP records. They are not new persistent identities,
source extraction, or verification of a source file/version. No proprietary text,
status literal, source-specific hash or generated real-source package is embedded
or loaded. Source recovery remains owned by the existing engine.

The candidate uses the same public aliases, group arities and width choices as
the BV-4 design. It does **not** run or read the SAS program or consume BV-4's
hypothesized outputs. The focused tests use separate T-series public records and
expectations describing this candidate contract; they are not SAS gold.

Material differences requiring future review:

| Candidate contract | BV-4 SAS experiment |
| --- | --- |
| Caller supplies already-padded typed values | SAS constructs typed datasets and storage padding |
| Explicit numeric missing objects and bounded Python numbers | Native SAS numeric storage and missing values |
| Explicit `initial_default` and independent one-row calls | PDV initialization in full arms and sentinel column in probe input |
| In-memory tuples preserve group position | Named dataset columns and SAS descriptors |
| Predicate/assignment/exclusion events with source coordinates | PUTLOG control-point events, including BEFORE_DELETE and ROW_END_REACHED |
| Up-front rejection of unsupported records | No corresponding Python validation layer in the SAS fixture |

No claim of divergence or agreement has been measured against SAS outputs. Raw
trace streams intentionally have different formats and must not be compared as
identical records. Future comparison needs an attributable custodian bundle and
an explicit correspondence of business values and reached control points. The
19 synthetic business values plus case_id do not verify a historical descriptor.

## Local validation

Environment observed: macOS 26.6.2 ARM64, CPython 3.12.5. No dependency was added.

```bash
.venv/bin/python -IB -m unittest discover -s tests -p test_preparation_candidate.py -v
.venv/bin/python -B -m unittest discover -s tests -v
```

The focused run exited 0: **7 tests**, 0.008 seconds. Coverage includes both
branches, all 28 accepted missing tags, both CMISS groups, zero/character-period
controls, overlapping exclusions, rejoin/fallthrough, ordered source-referenced
diagnostics, deterministic immutable results and rejection without coercion.
The full run exited 0: **811 tests in 57.835 seconds**, preserving the existing
804 and adding the seven focused tests. No test failures occurred; no existing
test was changed. These counts are engineering checks, not SAS observations.

A direct `.venv/bin/python -IBS` smoke call loaded only this module with `runpy`,
constructed a public record and called `prepare`; it exited 0 with site packages
disabled. This establishes a stdlib-only call path, not SAS correctness. No
behavioral expectation was obtained from historical LOG/LST counts or BV-4.

## Preservation and limits

Both BV-4 files were checked byte-for-byte by their accepted SHA-256 values:

- SAS text: `cabe1cc6226599e2dea59a73082d89f508bd8c5e05267aa4ecbd076db8d994a0`.
- README: `408084a47e21fcf45c6f17afe9ba4887b4ac197c5bb3b7d35a09511473804cf8`.

All preexisting tracked files match the baseline. No accepted report, historical
artifact, frozen contract, skill, lockfile or downstream compatibility pin changed.
Only the development module, focused test file and this report are new.

The existing `.venv/bin/python -IB scripts/check_repository.py` exited 0. Its
tracked-file guard was supplemented by applying the existing path and credential
patterns directly to the three untracked additions. Python AST parsing, local
file/reference inspection and whitespace checks also succeeded. A byte comparison
of every preexisting regular tracked file against the baseline succeeded, and
the downstream pin remains `bc754e0f1204a99020c864df2a5b25983005e09c`.

```bash
git diff --check
git diff --exit-code 81b30a11af82ff1e6beee1420d3e596eb1a5c4ba
git status --short --untracked-files=all
```

These commands exited 0; status showed only the three new files. The all-file
byte comparison is preservation of existing artifacts, not a new replay of
historical SAS behavior or an independently certified evidence reconstruction.

SAS execution, native Windows qualification, Linux CI, installed-wheel validation,
independent behavioral verification and benchmarks are NOT_RUN in PY-1. No new
CLI, parser, graph contract, oracle or provider was introduced. No commit or push
is part of this checkpoint; stop after local validation.
