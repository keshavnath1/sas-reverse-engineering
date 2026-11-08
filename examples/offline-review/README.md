# Offline architecture review — ordered measurements and offsets

UNVERIFIED · fixed public synthetic development demonstration

```text
artifact_authority: DRAFT
semantic_verification: UNVERIFIABLE
semantic_acceptance: BLOCKED
benchmark_execution: NOT_RUN
```

The `prepare` module sorts observations by `batch, sequence`. The `enrich` module reads the ordered rows, divides each current value by two, and joins the result to batch offsets. The final SQL projection is ordered by `batch` alone. A literal include names `postcheck.sas`; its target and effects are unresolved.

## Review order

1. Open [DECISION_REVIEW.md](DECISION_REVIEW.md) for the decision, then [ARCHITECTURE.md](ARCHITECTURE.md) for the module handoff and dependency diagram.
2. Read the [draft PRD](PRD.md) and [module specifications](MODULES.md). Follow O, E and fact references into [EVIDENCE.md](EVIDENCE.md) for the original IDs, byte spans and hashes of the [synthetic source](#synthetic-source).
3. Compare the [native Python](ADR_NATIVE.md) and [conditional Spark](ADR_SPARK.md) proposals. Both need independent reference outputs and workload measurements before runtime selection.
4. Inspect the [fixed controls](#behavioral-controls) and [TIEOUT.json](TIEOUT.json) for the input rows, frozen expectations, observed probe outputs and individual discrepancies.
5. Use [MANIFEST.json](MANIFEST.json) to verify the bound subject, filenames, payload sizes and SHA-256 digests. The command prints the digest of the manifest itself separately.

## Scope

Source consistency passed. Reconstruction is PARTIAL because the include is unresolved. Production runtime selection and full-workflow acceptance are BLOCKED. No SAS or Spark job ran. The controls establish no general partition safety, semantic certification or performance result.

This developer command accepts one public synthetic fixture only. Real-source intake, broader SAS coverage, native Windows qualification and independent semantic evaluation require separate work.

## Reproduce the folder

From the development checkout with its prepared Python 3.12 environment active, run:

```bash
python3.12 -IB scripts/review_workflow.py --destination /tmp/sas-re-review
```

Use a fresh destination each time. If that directory exists, use a name such as `/tmp/sas-re-review-second`. The command prints the README path and the manifest digest.

## Synthetic source

These are the exact public source texts behind the graph. Evidence line numbers refer to these individual files, starting at line 1.

### prepare.sas

SHA-256 `1bc144d5ace53f06f765720a22d1ee2671cbcb13d5c1c2725cf34f8a8361e507`.

```sas
/* PUBLIC SYNTHETIC FIXTURE. Never executed. */
proc sort data=work.observations out=work.ordered;
by batch sequence;
run;
```

### enrich.sas

SHA-256 `09bae8bbb5c2b68e47801dbc865cd07b21f4953cec24ebcee043bcfea696ba91`.

```sas
/* PUBLIC SYNTHETIC FIXTURE. Never executed. */
data work.scaled;
set work.ordered;
by batch sequence;
scaled = value / 2;
run;
proc sql;
create table work.adjusted as
select s.batch as batch, s.scaled + r.offset as adjusted
from work.scaled as s inner join work.offsets as r on s.batch = r.batch
where s.scaled > 0
order by batch;
quit;
%include 'postcheck.sas';
```

## Behavioral controls

The 17 probes yielded 7 PASS, 8 deliberate FAIL and 2 UNVERIFIABLE outcomes. Every probe matched its frozen expectation. A deliberate FAIL means the checker caught an injected defect. The other synthetic input sets are behavioral challenges outside the original graph identity. See [TIEOUT.json](TIEOUT.json) for full rows and verdicts.

### B01

`B01-published-workflow` · input `mvp2` · probe `baseline`. Expected PASS. Observed PASS.

### B02

`B02-filter-and-fanout` · input `filters` · probe `baseline`. Expected PASS. Observed PASS.

### B03

`B03-sequence-coincidence` · input `sequence_witness` · probe `baseline`. Expected PASS. Observed PASS.

### B04

`B04-split-by-group` · input `mvp2` · probe `split`. Expected PASS. Observed PASS.

### B05

`B05-upstream-tie-permutation` · input `mvp2` · probe `reverse_sort_ties`. Expected PASS. Observed PASS.

### B06

`B06-final-tie-permutation` · input `sequence_witness` · probe `reverse_final_ties`. Expected PASS. Observed PASS.

### B07

`B07-wrong-sort-order` · input `mvp2` · probe `wrong_sort`. Expected FAIL. Observed deliberate FAIL.
Expected first discrepancy at `ordered`; observed `ordered` (key order differs from frozen sequence).

### B08

`B08-wrong-final-order` · input `sequence_witness` · probe `wrong_final_order`. Expected FAIL. Observed deliberate FAIL.
Expected first discrepancy at `adjusted`; observed `adjusted` (key order differs from frozen sequence).

### B09

`B09-lost-duplicate-match` · input `filters` · probe `drop_matches`. Expected FAIL. Observed deliberate FAIL.
Expected first discrepancy at `adjusted`; observed `adjusted` (row multiset differs).

### B10

`B10-wrong-arithmetic` · input `mvp2` · probe `wrong_scale`. Expected FAIL. Observed deliberate FAIL.
Expected first discrepancy at `scaled`; observed `scaled` (row multiset differs).

### B11

`B11-detached-data-ties` · input `mvp2` · probe `decouple_ties`. Expected FAIL. Observed deliberate FAIL.
Expected first discrepancy at `scaled`; observed `scaled` (SET did not retain the candidate SORT stream).

### B12

`B12-overstrict-sequence` · input `sequence_witness` · probe `strict_sequence`. Expected FAIL. Observed deliberate FAIL.
Expected first discrepancy at `final_order_policy`; observed `final_order_policy` (rejected a permitted within-batch permutation).

### B13

`B13-unfiltered-join` · input `filters` · probe `skip_where`. Expected FAIL. Observed deliberate FAIL.
Expected first discrepancy at `adjusted`; observed `adjusted` (row multiset differs).

### B14

`B14-missing-key-mismatch` · input `mvp2` · probe `ignore_missing_key`. Expected FAIL. Observed deliberate FAIL.
Expected first discrepancy at `adjusted`; observed `adjusted` (row multiset differs).

### B15

`B15-special-missing` · input `special_missing` · probe `baseline`. Expected UNVERIFIABLE. Observed UNVERIFIABLE.
Outside the frozen numeric profile. No candidate rows were assessed.

### B16

`B16-precision-boundary` · input `precision` · probe `baseline`. Expected UNVERIFIABLE. Observed UNVERIFIABLE.
Outside the frozen numeric profile. No candidate rows were assessed.

### B17

`B17-unresolved-include` · input `mvp2` · probe `unresolved_include`. Expected PASS. Observed PASS.
PASS covers O1–O3 only. The include at O4 remains UNVERIFIABLE.
