# MVP-2 validation

The [architecture overview](../examples/mvp2/ARCHITECTURE.md) follows one dataset across two modules. `prepare` sorts observations into `work.ordered` by `batch, sequence`. In `enrich`, a DATA step reads that intermediate and assigns `scaled = value / 2`. SQL joins the scaled rows to offsets on `batch`, filters on `s.scaled > 0`, and projects `batch` and `adjusted`. The final include names `postcheck.sas`; the target is outside the declared file scope. Reconstruction is **PARTIAL** with source consistency **PASSED** and stage gate **BLOCKED**.

From the development checkout with its existing Python 3.12 environment, choose a new destination for each run:

```bash
.venv/bin/python -IB scripts/mvp2_demo.py --destination /tmp/sas-re-mvp2-review
```

The script reconstructs the fixed public example in disposable scratch, checks the graph against its pinned digest and prints an UNVERIFIED six-file SHA-256 manifest. It shares the MVP-1 destination and no-clobber checks. It accepts no source or store path.

## Expected and observed

The [fixture and expectations](../tests/mvp2_expectations.py) were frozen at baseline `022c672d244a522e25a5aded7f29513f51875b69` before reconstruction or renderer edits (SHA-256 `dce463011111389bbd84901b2a94632305b287605af98493f3f88744e2f94716`). The [scope adapter](../tests/mvp2_fixture.py) declares ownership and entrypoints. The graph derives the DATA and ORDER edges from the represented accesses and sort contract. The file dependency declaration alone cannot establish either edge.

| Review question | Observed in the generated package |
|---|---|
| Which module supplies the intermediate? | O1 in `prepare` writes `work.ordered`. O2 in `enrich` consumes it on E4 (DATA) with E2 (ORDER). E1 carries `work.scaled` from O2 to SQL O3. [Architecture](../examples/mvp2/ARCHITECTURE.md) |
| Does the division depend on a previous row? | E3 is a conservative STATE self-edge. BY controls group flags. The assignment's listed input is `work.ordered.value` in the current iteration. Neither recurrence of the calculated value nor safe partitioning has been independently established. [Module specifications](../examples/mvp2/MODULES.md) |
| How should the SQL result be checked? | The scalar addends are `s.scaled` and `r.offset`. ON and WHERE contribute control inputs. Matches may multiply rows. Compare the two intermediates by `batch, sequence`, then compare qualifying projected rows per `batch` in `work.adjusted`. The matrix marks unavailable size, cost and capacity evidence UNKNOWN. [Native Python](../examples/mvp2/ADR_NATIVE.md) · [Spark](../examples/mvp2/ADR_SPARK.md) |
| What remains unknown? | The missing target has no invented edge or output. Of three unresolved records, two have no bound operation and one binds to O4. No contradiction or log observation is recorded. [Evidence](../examples/mvp2/EVIDENCE.md) · [PRD](../examples/mvp2/PRD.md) |

The graph has four operations, four edges, five datasets and fourteen columns. Graph SHA-256 is `19f41dea50825469a89d8fc545fee1d87f09af946d130d62de8f946d90b78017`; P3-A1 diagnostic SHA-256 is `cdfdd753bdfbc2f9a6fd24e3eee2b3270d157db754203c8f89e976617a87f3dd`.

## Checks executed

| Check | Result |
|---|---|
| macOS 26.6.2 (25G83), ARM64, CPython 3.12.5. `.venv/bin/python -m unittest discover -s tests -v` | Baseline **735/735**; candidate **745/745**, including 10 new tests. The focused command was `.venv/bin/python -m unittest discover -s tests -p test_mvp2_preview.py -v`. |
| Hosted Linux, CPython 3.12.5, implementation commit `0bd86edc23b71af8eab6c10ab559afca127a88d5` | **745/745** passed with the editable installation (45.591 s), then **745/745** with the installed wheel (44.722 s). Foundation and downstream drift both passed. [GitHub Actions run](https://github.com/keshavnath1/sas-reverse-engineering/actions/runs/42313417323) |
| Repeated offline demo and document review | Two fresh directories matched the six sample files and each other's stdout. An empty-PATH run with calibrated Python socket/process-event probes observed no attempts. All 12 operation/fact spans matched the original source, byte-slice and excerpt digests. All 214 package-local links resolved. |
| Subject and uncertainty challenges | Removing the cross-module DATA edge left a missing-edge obligation. Pairing the changed graph with the previous diagnostic was rejected. Suppressing include blockers in an otherwise matching diagnostic was also rejected. |
| Historical synthetic replay | Ran `scripts/p1_demo.py` and `scripts/p2a_demo.py` with separate fresh `--destination` directories at baseline and candidate. All 30 artifact files and both complete reports matched byte for byte, including the retained WS-1 sets. |
| Frozen identities and downstream compatibility | Eight frozen hashes and three P3-A1 hashes matched. `.venv/bin/python -B -m sas_re check-baseline --checkout /private/tmp/sas-re-downstream-bc754e0` passed, 20/20 pinned downstream files, clean worktree. |
| Prior and new sample bytes | Original MVP-1 demo stdout and all six files matched the accepted commit. SHA-256 of sorted compact filename-to-SHA-256 JSON plus LF: MVP-1 `39297fadabb084a3d0cd46abdb130b73de95de71cdf3c4cdb040e68bfc66b232`; MVP-2 `218a0111e99f64d4869570e46e7fa951ff8dfe1db617e9d0d72f9dc06624658c`. |

During development, the first focused run had six failed assertions and one missing-sample error while the renderer lacked fact-anchor targets, the matrix and golden files. Review also found an inherited proposal to use the intermediate's composite key for the final SQL output. Both ADRs and the tests now distinguish those boundaries. An auxiliary audit initially assumed declared module order; comparing membership preserved the canonical module IDs and fixed the check.

Native Windows execution was not attempted. DRAFT authority, UNVERIFIABLE semantic verification, BLOCKED independent semantic acceptance and NOT_RUN benchmarks apply throughout. The checks exercise public synthetic reconstruction and rendering; no SAS, candidate runtime, private workload or independent evaluation was executed.
