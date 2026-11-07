# MIG-2 · Configurable public DATA projection → SORT

Use the existing Python 3.12 development installation on the supported POSIX
path. From the checkout root, choose fresh system-scratch destinations.

```bash
python3.12 -IB scripts/review_intake.py --intake examples/mig2/public-input \
  --destination /tmp/sas-re-int1-mig2-example
python3.12 -IB scripts/migrate_projection_sort.py \
  --intake examples/mig2/public-input \
  --package /private/tmp/sas-re-int1-mig2-example \
  --rows examples/mig2/CASES.json \
  --rows-sha256 f797f50799e89ee9e8d4de15e5ad718136606b1acc4e852d21f4abc86da7bb64 \
  --destination /tmp/sas-re-mig2-example
```

Use the physical package path from the intake receipt. On Linux it starts
with `/tmp`. Keep the package, intake and row file available for replay.

To use a new public synthetic workload, declare exactly two sources in the
existing v2 scope manifest and generate a new INT-3 package. Select the entire
contents of each file as a single range. The bounded candidate accepts a
single DATA/SET/KEEP operation, a single ascending PROC SORT with one BY key,
exactly two distinct projected columns including the key, and an unambiguous
handoff between distinct input, intermediate and output datasets. Additional
transformations, uninspected bytes and ambiguous handoffs are refused.
The command reruns the existing analyzer and compares every expected package
artifact byte-for-byte before using its SOURCE and MAP records.

Supply a separate JSON row file of at most 256 KiB. Set `scope` to
`public-synthetic` and declare the discarded text field in `text_column`.
Each `input` row contains exactly the source-declared integer key, the other
projected column as an integer or finite float, and the text field as a
string. An optional `expected` array contains projected rows only, in
expected order. Supply the exact row-file SHA-256 from an authorized copy
(`shasum -a 256 path/to/rows.json`). Scope labels are caller declarations.
Use public synthetic inputs only.

Open `PLAN.json` for the source paths, TRACE record references, potential
handoff and candidate assumptions. `ROWS.json` contains candidate rows.
`VALIDATION.json` records execution and the comparison result. A mismatch
writes a FAIL report and exits 1. Omitting `expected` records comparison
`NOT_RUN` with successful execution. Refusals exit 2. The manifest binds
the evidence, row file, candidate code and output bytes.

Projecting before sorting and keeping ties in input order are Python
candidate choices. SAS descriptors, sort behavior, execution order and
runtime dataset-version continuity still require attributable evidence.
Public expected rows provide engineering checks. The outputs retain DRAFT
authority, UNAVAILABLE behavioral evidence, UNVERIFIABLE semantic
verification, BLOCKED acceptance, NOT_RUN reference and benchmark execution,
and UNBOUND historical provenance.

The pinned MIG-1 command and its package bytes remain compatible.
