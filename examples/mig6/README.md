# MIG-6 · Conditional full-record SORT and CSV

Run from the checkout root with the existing Python 3.12 development
installation on the supported POSIX path. Generate or reuse the pinned
public source reviews described in the [MIG-5 instructions](../mig5/README.md).
Use their physical paths and a fresh destination.

```bash
python3.12 -IB scripts/migrate_sort_export.py \
  --preparation-evidence /private/tmp/sas-re-source-mig3-demo/EVIDENCE.json \
  --population-evidence /private/tmp/sas-re-source-mig4-demo/EVIDENCE.json \
  --scenario passes --destination /tmp/sas-re-mig6-demo
```

On Linux use `/tmp` for the input paths. Choose any pinned MIG-5 scenario
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
