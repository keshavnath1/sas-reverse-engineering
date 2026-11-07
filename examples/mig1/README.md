# MIG-1 · Public DATA → SORT migration candidate

This contract is bound to INT-3 manifest SHA-256
`8bfc638d5c4db4f60001010ee7abbb3db175c29f44696b0403c621fed953227a`.
The pinned INT-5 public inputs are reused unchanged.

| Source evidence | Declared requirement | Candidate behavior |
| --- | --- | --- |
| `prepare.sas.txt`, line 1, `SOURCE_2.md#bytes-18-34` and `#bytes-0-17` | SET reads `work.sample`. DATA declares `work.staged`. | Read the public rows in their supplied order and stage one projected row per input row. |
| `prepare.sas.txt`, line 1, bytes `[35,50)`, `SOURCE_2.json` at `/declared_operation/declaration_spans/keep` | KEEP declares `id` and `amount`. | Carry those values and types unchanged and drop the synthetic `memo`. |
| `order.sas.txt`, line 1, `SOURCE_1.md#bytes-0-56` | SORT reads `work.staged` and writes `work.ordered`, with BY `id` at bytes `[45,51)`. | Order by ascending integer `id`. Preserve row multiplicity and stage order within ties. |
| INT-3 `MANIFEST.json`, `/cross_file_dependencies/0` | Matching declarations give a POTENTIAL handoff. Execution order and dataset version are UNRESOLVED. | Pass the projected rows directly to sorting in this candidate. This is a candidate design choice. |

Source SHA-256 values from the bound manifest:

- `prepare.sas.txt` · `b05324aeafa0067ad2cc95bf52ee36a29190ab420634301f80c7775518623454`
- `order.sas.txt` · `869452516bcbf0d823c27559855349814ed410605ef0e1eb937a5f52ec1bc5a6`

The public input rows contain exactly `id` (integer), `amount` (integer or
finite float), and `memo` (text). Missing fields and values, Boolean numeric
values, and unsupported types are refused. The output is an ordered list of
`id` and `amount` records. Stable ties, type restrictions and one output per
input row are engineering assumptions for this fixture. SAS descriptors,
missing-value rules, effective sort options and tie behavior require reference
evidence. To establish continuity, obtain a run tied to the exact submitted
sources and identify the produced dataset version consumed by SORT. Row counts
or timestamps alone are insufficient.

## Execute and review

Use the existing development installation on the supported POSIX path. From
the repository root, generate the deterministic evidence or reuse an existing
package with the pinned digest. Choose fresh destinations.

```bash
python3.12 -IB scripts/review_intake.py --intake examples/copilot-review/public-input \
  --destination /tmp/sas-re-int1-mig-demo
python3.12 -IB scripts/migration_candidate.py \
  --package /private/tmp/sas-re-int1-mig-demo \
  --destination /tmp/sas-re-mig1-demo
```

Use the physical package directory printed by the intake receipt. On Linux
that path starts with `/tmp`. The candidate runs only the public rows in
[CASES.json](CASES.json). No arbitrary row-file option is exposed.

Review the contract before running. If an operator has approved the INT-5 notes,
optionally pass their `COPILOT_REVIEW.json` via `--review-notes` using its
physical path. The candidate validates its binding and records its SHA-256 as
a separate reference. Keep the original sidecar with the evidence. Without it
the result records the notes as `NOT_SUPPLIED`. An operator approval applies
to those notes only.

Open `VALIDATION.json` for the expected and observed rows and the engineering
verdict. `MANIFEST.json` binds the input package, public cases, candidate code
and output files. Preserve the original INT-3 package for the cited TRACE and
MAP records. A mismatch produces a FAIL report and a nonzero exit code. A bad
package binding is refused before creating output.

```text
artifact_authority: DRAFT
behavioral_evidence: UNAVAILABLE
semantic_verification: UNVERIFIABLE
semantic_acceptance: BLOCKED
reference_experiment: NOT_RUN
benchmark_execution: NOT_RUN
historical_source_run_provenance: UNBOUND
```
