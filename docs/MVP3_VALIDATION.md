# MVP-3 behavioral tie-out

On the original public inputs the model produces **five SQL rows**. The missing batch yields `13`. Batch `1` yields the multiset `{5, 6, 9, 10}`. Batch `2` has no matching offset. All 17 controls behaved as specified: **7 PASS, 8 deliberate FAIL, 2 UNVERIFIABLE**. These are observations of fixed Python candidates against hand-calculated expectations. The missing `postcheck.sas` keeps full-workflow acceptance **BLOCKED**.

```text
artifact_authority: DRAFT
semantic_verification: UNVERIFIABLE
semantic_acceptance: BLOCKED
benchmark_execution: NOT_RUN
```

## Reproduce and inspect

From this checkout, run with Python 3.12. The [development script](../scripts/mvp3_tieout.py) reads fixed public declarations and writes JSON to stdout. It needs only the standard library. The second command shows the missing duplicate in one candidate's output.

```bash
python3.12 -IBS scripts/mvp3_tieout.py
python3.12 -IBS scripts/mvp3_tieout.py --case B09-lost-duplicate-match
```

Each case gives the input ID, probe, expected and observed stage rows, verdict, and discrepancies. Exit 0 means the selected controls returned their predeclared verdicts, including expected failures. No user program or input path is accepted.

## Reference and comparison rules

The [public case table](../tests/mvp3_cases.py) was frozen from source before implementing the reference, at SHA-256 `7ca4c6b50cdc7f5b7ce2ee422f5adfe883dba82a39b064140fba2d7a70702342`. The script checks this digest and the accepted [MVP-2 fixture](../tests/mvp2_expectations.py) digest before reading literal assignments. Historical graph `19f41dea50825469a89d8fc545fee1d87f09af946d130d62de8f946d90b78017` identifies the original workload only. The new vectors are identified by the case-table digest and input ID. [Original operations and source spans](../examples/mvp2/EVIDENCE.md#operation-register)

- **O1, SORT.** Require the frozen `(batch, sequence)` key sequence and the complete row multiset. The represented contract leaves full-key ties unspecified. A SAS site's EQUALS setting can impose a stronger constraint on an actual run. This oracle does not guess that setting. [SAS PROC SORT options](https://support.sas.com/documentation/cdl/en/proc/61895/HTML/default/a000146878.htm)
- **O2, DATA.** Require the actual O1 stream, including the order its producer chose among ties. Compare every original field and the current row's `scaled = value / 2`. Splitting the test input inside a tied group exercises only this calculation. [SAS SET statement](https://support.sas.com/documentation/cdl/en/lestmtsref/63323/HTML/default/p00hxg3x8lwivcn1f0e9axziw57y.htm)
- **O3, SQL.** Join every matching pair, retain only positive scaled values and project `(batch, adjusted)`. Require ascending batches and exact row multiplicity within each batch. The final projection omits `sequence`. A candidate may happen to emit sequence order, but a validator must accept other legal tie permutations. [SAS PROC SQL joins](https://support.sas.com/documentation/cdl/en/sqlproc/62086/HTML/default/a001361784.htm) · [SQL ordering](https://support.sas.com/documentation/cdl/en/sqlproc/63043/HTML/default/p1jr2es0aus2qtn11peo724tt8f4.htm)
- **Numeric scope.** Inputs are ordinary `.` or signed integer strings with magnitude at most 1,000,000. Integer half-units give an exact reference for the selected divisions and sums. Ordinary numeric missing sorts below finite values, matches ordinary missing on this SQL join, propagates in arithmetic and fails `scaled > 0`. Python `None` cannot directly participate in these comparisons or arithmetic. NaN does not equal itself. Special missing codes and host-sensitive precision are outside the modeled profile. [SAS missing-value order](https://support.sas.com/documentation/cdl/en/lrcon/62955/HTML/default/a000989180.htm) · [SAS missing arithmetic](https://support.sas.com/documentation/cdl/en/lrcon/65287/HTML/default/p17j9efnrdlz0gn1d19ete4ik8sb.htm)

The reference enumerates matching pairs. The built-in candidates use decimal arithmetic and a batch-indexed lookup. The checker compares both against the explicit frozen rows. A correct tie permutation is allowed only when the stage's order contract allows it. P2A, P3 diagnostics, preview rendering, SAS execution and protected evaluator answers play no part in computing the expected rows.

## Case results

IDs below are the prefixes of the full IDs in the [frozen table](../tests/mvp3_cases.py). The input ID selects the original rows and their expected outputs at all three boundaries.

| Case / input | Expected behavior | Observed candidate behavior | Verdict |
|---|---|---|---|
| B01 / mvp2 | Four SORT/DATA rows, five SQL rows | Returned the two per-batch results above | PASS |
| B02 / filters | Drop missing, zero and negative scaled values. Preserve duplicate matches and missing addition | Batch 1 returned `3.5, 3.5, .` | PASS |
| B03 / sequence_witness | Sequence-compatible final tie order is allowable | Batch 1 emitted `2, 5`, then batch 2 emitted `5` | PASS |
| B04 / mvp2 | Two chunks split the equal `(1,1)` group without changing values | Chunk sizes `[2,2]`. All stage rows matched | PASS |
| B05 / mvp2 | Allow a different full-key SORT tie order carried through DATA | Tied values `4,2` stayed in that order at both stages | PASS |
| B06 / sequence_witness | Allow the reverse final tie permutation | Batch 1 emitted `5,2`, then batch 2 emitted `5` | PASS |
| B07 / mvp2 | First SORT key must be `(.,2)` | Wrong sort put `(2,1)` first | FAIL |
| B08 / sequence_witness | Final batch order must start at 1 | Batch 2 came first | FAIL |
| B09 / filters | Two copies of `(1,3.5)` required | Candidate discarded a duplicate offset and returned one copy | FAIL |
| B10 / mvp2 | Input value 6 must scale to 3 | Dividing by one produced 6 and changed the SQL result | FAIL |
| B11 / mvp2 | SET must follow the candidate's concrete SORT stream | SORT chose values `2,4`. DATA processed `4,2` instead | FAIL |
| B12 / sequence_witness | Accept batch 1 values `5,2` in the frozen legal witness | The overstrict validator accepted its own `2,5` order and rejected the witness. Its emitted rows alone were valid | FAIL |
| B13 / filters | WHERE leaves three qualifying projected rows | Omitting WHERE returned twelve rows, nine extra | FAIL |
| B14 / mvp2 | Ordinary missing keys must match here | Skipping the missing key lost `(.,13)` | FAIL |
| B15 / special_missing | `.A` needs a separate numeric profile | Reference refused the input. No candidate rows computed | UNVERIFIABLE |
| B16 / precision | `9007199254740993` exceeds the admitted bound | Reference refused the input. Conversion to binary64 can collapse it to its predecessor | UNVERIFIABLE |
| B17 / mvp2 | Assess O1–O3 and leave O4 unresolved | Subset matched. O4 has no assessed output, full gate BLOCKED | PASS (O1–O3) |

## Verification and limits

- macOS 26.6.2 (25G83), ARM64, CPython 3.12.5. The baseline passed **745/745**. The focused command `python -m unittest discover -s tests -p test_mvp3_tieout.py -v` passed **13/13**. Full discovery passed **758/758**.
- Two isolated runs produced identical 15,660-byte reports (SHA-256 `aee7cbd480b1f6794888616af9c55e8896ecb13fa3dc1585d1b012f0a8508600`). A calibrated Python audit with an empty executable path observed no socket or child-process attempts. An additional permutation check accepted exactly 24/120, 3/3 and 2/6 distinct final-row permutations for the three supported inputs, as required by batch order.
- Fresh baseline and candidate replays matched all 30 P1/P2A artifacts and both complete reports. All eight frozen hashes, three P3-A1 hashes, both six-document previews and their original stdout manifests matched. The local downstream drift check passed for all 20 files at `bc754e0f1204a99020c864df2a5b25983005e09c`.
- Review exposed three reproducible faults. A shared sort-key function could approve missing-last output, a modified source fixture could carry the historical graph reference, and a returned expected-row object could alter a subsequent report. The checker now uses frozen key sequences, verifies both literal files before use, and reads fresh data for each report. The targeted tests first reproduced all three faults and now pass.
- This is a public synthetic development oracle. There is no observed SAS run, independently isolated evaluator, complete-workflow equivalence verdict or native Windows qualification.
