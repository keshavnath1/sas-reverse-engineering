# MIG-4 · Public population audit and gate candidate

This example reuses SQL-2 source recovery. It runs a small Python population
audit and records gate decisions. The public SAS source is input to static
review only. Its DATA and SORT statements frame the SQL interval.

## Run with Python 3.12

Use the development installation on the supported POSIX path. Run from the
checkout root with fresh destinations. On Linux use `/tmp` for physical paths.

```bash
work=$(mktemp -d /private/tmp/mig4-public.XXXXXX)
cp examples/mig4/population.sas.txt "$work/population.sas"
digest=$(shasum -a 256 "$work/population.sas" | cut -d ' ' -f1)
python3.12 -IB scripts/review_source.py \
  --source "$work/population.sas" --source-sha256 "$digest" \
  --lines 1:1 --lines 14:14 --recover-sql-gates \
  --destination /tmp/sas-re-source-mig4-demo
python3.12 -IB scripts/migrate_population.py \
  --source "$work/population.sas" --source-sha256 "$digest" \
  --evidence /private/tmp/sas-re-source-mig4-demo/EVIDENCE.json \
  --destination /tmp/sas-re-mig4-demo
```

The runner replays the existing SQL-2 review and checks the exact evidence bytes.
It accepts the bounded three-query, five-gate sequence with linked INTO
bindings and the nested flag guard. It rejects partial or mismatched gate
evidence. Keep the original source review to resolve the TRACE anchors and
record pointers. Other interval effects and SAS SORT reachability remain
unresolved.

## Candidate policies

- A public ID is an exact-range integer (inclusive ±2⁵³) or a PY-1 numeric
  missing tag object, such as `{"tag":".A"}`. Floats, booleans, strings and
  null IDs are refused. The candidate counts missing rows, excludes them from
  distinct IDs, and groups missing IDs by exact tag for the duplicate audit.
  The empty missing count is zero. These are engineering choices.
- Each repeated group's `duplicate_count` is its size. `duplicate_ids` is
  the number of repeated groups. The audit lists integers in ascending order
  followed by missing tags in lexicographic order.
- The first true gate requests a candidate block. Subsequent gates are marked
  unevaluated. The optional guard accepts only Y/y or N/n and requires a
  nonnegative integer expected count when enabled. A normal block is an
  expected business outcome. Exit 1 means the engineering comparison failed.
- Gate 4 is present in the plan. With this population policy it cannot be
  the first blocker after the missing and duplicate checks pass.

The default run executes the eight bundled public cases. To also audit
the two full-mode row-end outputs from the public MIG-3 demonstration, pass
`--mig3-package` with its physical directory and `--mig3-manifest-sha256`
with the digest from its receipt. Only IDs from full-mode candidate row ends
are carried forward, preserving multiplicity. Isolated-pair probes and
excluded rows stay out. This extra run uses flag N, and its comparison is
`NOT_RUN`. It neither establishes runtime dataset continuity nor observes
SAS output. Supply only a trusted public MIG-3 package.

Open `PLAN.json` for declaration anchors and proof obligations,
`POPULATION.json` for statistics and ordered Python decisions, and
`VALIDATION.json` for the engineering comparisons. Each case's expected
array gives total rows, distinct nonmissing IDs, missing rows, duplicate
groups and first blocking gate (1-based, or null). The manifest binds inputs,
candidate implementation and output bytes.

SAS aggregate behavior for empty and missing populations, actual macro
variables and execution of abort effects need attributable SAS reference
evidence. Authority remains `DRAFT`, behavioral evidence `UNAVAILABLE`,
semantic verification `UNVERIFIABLE`, semantic acceptance `BLOCKED`,
reference and benchmark execution `NOT_RUN`, and provenance `UNBOUND`.
