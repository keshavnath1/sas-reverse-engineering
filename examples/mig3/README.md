# MIG-3 · Evidence-bound public preparation candidate

This example binds the six ordered rules from the existing SM-3B source review
to the unchanged PY-1 candidate. The public SAS text is the business-rule
portion of the BV-4 plain arm adapted to the bounded source reviewer. The
typed rows follow the BV-4 case designs. The declarations in the supplied
source establish rule structure and KEEP selections. The PY-1 input widths,
numeric tags and character padding are engineering assumptions.

## Run with Python 3.12

Use the existing development installation on the supported POSIX path. From
the checkout root, copy the public source to a new physical scratch directory.
On Linux replace `/private/tmp` with `/tmp`. Choose fresh destinations.

```bash
work=$(mktemp -d /private/tmp/mig3-public.XXXXXX)
cp examples/mig3/preparation.sas.txt "$work/preparation.sas"
digest=$(shasum -a 256 examples/mig3/preparation.sas.txt | cut -d ' ' -f1)
python3.12 -IB scripts/review_source.py \
  --source "$work/preparation.sas" --source-sha256 "$digest" --lines 1:12 \
  --recover-status-rules --recover-missing-exclusions \
  --destination /tmp/sas-re-source-mig3-demo
python3.12 -IB scripts/migrate_preparation.py \
  --source "$work/preparation.sas" --source-sha256 "$digest" \
  --evidence /private/tmp/sas-re-source-mig3-demo/EVIDENCE.json \
  --destination /tmp/sas-re-mig3-demo
```

The command requires an operator-authorized public source containing one
complete DATA step. It reruns the existing source review with both flags and
checks the exact evidence bytes, six-rule sequence, prerequisites, arguments,
assignments and byte-span hashes. It refuses other rule variants and extra or
uninspected effects. It uses the existing protected readers and fresh-output
writer. The case set is bundled. No caller data-file input is exposed.

- `PLAN.json` links each PY-1 rule index to a pointer in the supplied
  `EVIDENCE.json` and its byte anchor in the source review README.
- `ROWS.json` contains the typed public inputs, Python candidate outputs and
  ordered diagnostics. Missing numerics retain their tags. Reaching Python
  candidate row end leaves SAS dataset output `UNOBSERVED`.
- `VALIDATION.json` compares first exclusion, assignment branch and surviving
  Default against explicit public engineering expectations. The three
  positions of each case's `expected` array follow that order. Assignments
  made before an exclusion are counted in the summary. P01 and P02 use PY-1's
  isolated-pair probe, which omits rule 0 and still runs later exclusions.
- `MANIFEST.json` binds source, source evidence, case definitions, candidate
  code and output bytes. A failed engineering comparison exits 1. A refusal
  exits 2 before publication.

Keep any human-reviewed Copilot notes alongside the original evidence as
separate optional review material. The INT-5 sidecar binds a two-source
package. This single-source runner neither rebinds that sidecar nor uses it
to authorize behavior.

SAS input/output descriptors, comparison and missing-value behavior, actual
row production and exact run attribution require independent evidence.
BV-4 reference execution remains `NOT_RUN`. Output authority remains
`DRAFT`, behavioral evidence `UNAVAILABLE`, semantic verification
`UNVERIFIABLE`, semantic acceptance `BLOCKED`, benchmark execution
`NOT_RUN` and historical source/run provenance `UNBOUND`.
