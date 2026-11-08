# Conditional sorting and CSV export

Run from the checkout root with the existing Python 3.12 development
installation on the supported POSIX path. Generate the pinned public source
reviews with the current paths below, or reuse exact matching reviews from
this revision. Choose fresh destinations and use canonical physical paths.

## Prepare the two source reviews

The original fixture contracts remain frozen engineering reference material,
not current command instructions. These commands use their unchanged source
bytes and the original bounded-review flags; SAS itself is not executed.

```bash
work=$(mktemp -d /tmp/sas-export-prerequisites-XXXXXX)
work=$(cd "$work" && pwd -P)
cp tests/fixtures/candidate-execution/preparation-rules/preparation.sas.txt "$work/preparation.sas"
cp tests/fixtures/candidate-execution/population-gates/population.sas.txt "$work/population.sas"
prep_sha=dccdf7b4b11eba5fd7369157c7b3e8ef002d3b8c7bf2c9a5547dc80e161b8cf8
pop_sha=21e16d05e77999c9b2de565c7f1348d9d4b9aae27736024ca286062f8731d110
prep_review="/tmp/sas-re-source-preparation-${work##*/}"
pop_review="/tmp/sas-re-source-population-${work##*/}"
python3.12 -IB scripts/review_source.py \
  --source "$work/preparation.sas" --source-sha256 "$prep_sha" --lines 1:12 \
  --recover-status-rules --recover-missing-exclusions --destination "$prep_review"
python3.12 -IB scripts/review_source.py \
  --source "$work/population.sas" --source-sha256 "$pop_sha" \
  --lines 1:1 --lines 14:14 --recover-sql-gates --destination "$pop_review"
prep_review=$(cd "$prep_review" && pwd -P)
pop_review=$(cd "$pop_review" && pwd -P)
```

## Run the standalone public engineering probe

This standalone probe is not the approval-gated publication route. For that
route use the [governed preparation and population continuation](../preparation-and-population/README.md)
with a fresh subject, claim record and required human approval.

```bash
python3.12 -IB scripts/migrate_sort_export.py \
  --preparation-evidence "$prep_review/EVIDENCE.json" \
  --population-evidence "$pop_review/EVIDENCE.json" \
  --scenario passes --destination "/tmp/sas-re-mig6-${work##*/}"
```

Choose any pinned MIG-5 scenario
with `--scenario`. Each invocation publishes one scenario's package.
`PLAN.json` preserves the original source-evidence pointers and anchors.
`SCENARIO_RESULT.json` retains preparation rows, the ID handoff, and gate
decisions. `VALIDATION.json` reports engineering comparison results.
A successful comparison can include an expected block or refusal.

`PROCEED` publishes `SORTED_ROWS.json` and `PREPARED_EXPORT.csv` from the
full-mode row-end records only. The adapter flattens all 19 business fields.
The review retains `case_id`. Ascending integer sorting preserves full
records and input order within ties. The duplicate gate normally prevents
ties from reaching the adapter, so stable ties are checked separately.

CSV uses a header with `id`, `n1`–`n12`, `c1`–`c5`, and `Default` in that
order. It uses comma delimiters, minimal double quoting with doubled embedded
quotes, LF including the final line ending, and UTF-8 without a BOM. Integers
use decimal text and finite floats use Python's float representation.
Stored four-character values retain padding and whitespace. Missing or
unsupported cells are refused. The candidate publishes only into a fresh
directory. On `BLOCK` no sort or serialization runs and no sorted-row or
CSV file appears in the manifest. Invalid preparation input also produces
no downstream files.

The public SQL-2 fixture declares ascending SORT by `id`. The EX-1
historical boundary supplies a source-cited migration assumption for
`PROC EXPORT DATA=WORK.PREPARED_EXPORT DBMS=CSV REPLACE` and its following
status check. The public fragments do not establish a link to that historical
export. Actual SAS writes, ordering and tie behavior, serialization, status
checks and execution remain unobserved. The package keeps the existing DRAFT,
UNAVAILABLE, UNVERIFIABLE, BLOCKED, NOT_RUN and UNBOUND authority statuses.
