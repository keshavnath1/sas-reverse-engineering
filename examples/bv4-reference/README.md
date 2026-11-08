# BV-4 public synthetic SAS reference experiment

```text
artifact_authority: DRAFT
reference_experiment: NOT_RUN
semantic_verification: UNVERIFIABLE
semantic_acceptance: BLOCKED
benchmark_execution: NOT_RUN
```

Prepared against repository baseline
`de4d9ac4c7e63be6f42920d5d94794e8b907be92`. No authorized SAS runtime is
available for this checkpoint. The program has not been compiled or executed.
Historical source/run provenance remains UNBOUND. This fixture does not reproduce
the historical prepared-output descriptor or verify a real workload.

[reference_experiment.sas.txt](reference_experiment.sas.txt) is the complete public
synthetic program. Its text suffix preserves the repository's exclusion of raw
`.sas` files. An authorized custodian can copy its exact bytes to a `.sas` file
outside the checkout; verify identical SHA-256 after copying. Do not edit accepted
artifacts, weaken the repository guard, or commit execution results.

## Frozen case design

The explicit synthetic schema is `case_id` character length 3, `status` character
length 8, `id` and `n1` through `n12` numeric length 8, and `c1` through `c5`
character length 4. `Default` is numeric length 8. The full input has no Default
column; the probe input supplies the sentinel 9. Output datasets keep `case_id`
plus the 19 synthetic business fields (`id`, twelve numeric fields, five character
fields and Default). Column-count coincidence is not historical schema evidence.

`case_id` is audit-only and never a business predicate. Each input dataset uses
its own positive input ordinal as the default `id`; all `n` fields start at 1 and
all `c` fields at `X`. These are constants assigned afresh per input record, not
inferred input types. Blank assignments fill fixed-length character fields with
blanks. Numeric missing literals are assigned directly, avoiding import guessing.

All outcomes in this table are **hypotheses, NOT_RUN**. They are not reference
answers, verdicts, or expected-output records consumed by the program.

| Case | Status | Changes from defaults | Hypothesis to challenge |
| --- | --- | --- | --- |
| C01 | A | None | Survive with Default 1 |
| C02 | B | id=0, n1=0, c1 is character period | Survive with Default 0 |
| C03 | C | None | Rule 0 terminates before assignment |
| C04 | C | id ordinary missing, n1 ordinary missing, c1 blank | Rule 0 terminates despite other possible exclusions |
| C05 | A | id ordinary missing | Assign 1, then rule 3 terminates |
| C06 | B | id special missing .A | Assign 0, then rule 3 terminates |
| C07 | A | n1 ordinary missing | Rule 4 terminates |
| C08 | B | n12 special missing ._ | Rule 4 terminates |
| C09 | A | c1 blank | Rule 5 terminates |
| C10 | B | c5 blank | Rule 5 terminates |
| C11 | A | id ordinary missing, n1 ordinary missing, c1 blank | Rule 3 is first exclusion; no rules 4/5 reached |
| C12 | B | n1 ordinary missing, c1 blank | Rule 4 is first exclusion; no rule 5 reached |
| P01 | C | Isolated pair; input Default=9 | No assignment; sentinel retained; subsequent checks reached |
| P02 | C | Isolated pair; input Default=9; id ordinary missing | No assignment; rule 3 terminates |

The program contains the twelve C records once in `BV4.FULL_INPUT` and the two
P records once in `BV4.PROBE_INPUT`. Three arms use them:

1. `BV4.FULL_PLAIN`: uninstrumented six-rule step, reading FULL_INPUT.
2. `BV4.FULL_TRACED`: instrumented six-rule step, reading that same FULL_INPUT.
3. `BV4.PAIR_PROBE`: instrumented rules 1-5, reading PROBE_INPUT; rule 0 is absent.

There are 14 distinct case designs and 26 planned business-row evaluations.
Diagnostic row dumps are collection, not additional behavioral trials. Full-run
fallthrough is structurally unreachable when the two allowed status values are
exactly the two branch values. P01/P02 test the isolated pair and rejoin only.

The [source-recovered prerequisite structure](../../docs/MISSING_VALUE_RULES_VALIDATION.md) is
unchanged in the full arms: rule 0 has none; rule 1 requires 0 false; rule 2
requires 0 and 1 false; rule 3 requires only 0 false; rule 4 requires 0 and 3
false; rule 5 requires 0, 3 and 4 false. Both label branches rejoin before rule 3.
The probe intentionally omits the rule-0 prerequisite and makes no full-sequence
reachability claim.

## Actual observations, not generated answers

The event macro only increments a row-local counter and writes values with PUTLOG.
It does not evaluate predicates. The shared traced rules retain an immediately
linked IF/ELSE IF and add a logging-only ELSE body for actual fallthrough. No
predicate is evaluated just to produce a trace. Rule-2 events identify a reached
body; they are not a separate probe before its predicate. No CMISS argument
evaluation order or laziness is asserted.

`BV4|TRACE` lines carry arm, case, event sequence, rule index and actual Default.
Only actual message lines starting with `BV4|` are observations. SOURCE/MPRINT
echoes containing those strings are program text, not additional events or rows.
`BEFORE_DELETE` means the marker before DELETE was reached; `ROW_END_REACHED`
means the final control point was reached. Neither marker by itself proves an
output row was written. Check the real output datasets and complete diagnostics.
There are no explicit OUTPUT statements: business rows retain implicit DATA-step
output. Trace writes do not create or route business rows.

The collection helper prints PROC CONTENTS descriptors to the listing and emits
`BV4|DUMP_BEGIN`, NUM/CHAR and DUMP_END lines to the LOG for all five datasets.
These are actual SET-read values, with no comparison to hypotheses. Character hex
retains padding; numeric BEST32 text retains missing tags and HEX16 adds host
representation. Interpret hex with the recorded encoding/platform and descriptor;
do not compare numeric host hex across architectures as a portable identity.
The collection helper has no business-rule predicates. An empty actual dataset
has no row dump entries; descriptor and log review must distinguish this from a
missing or failed dump.

## Custodian execution and collection checklist

Execution authorization, named custodian, SAS host and independent reviewer are
**OPEN**. This preparation grants no execution approval and provides no runtime.

- Obtain separate authorization for the exact public program and case design.
  Have an independent reviewer inspect the declarations, case constructors,
  six-rule order, branch linkage, trace wrappers and isolated probe distinction.
  The target is conventional Base SAS 9.4; actual compatibility is untested.
- Create a fresh external run directory. Copy the program byte-for-byte and hash
  both copies with an approved host SHA-256 utility. Record the README/case-design
  hash too. Use a fresh SAS session with that directory as its actual working
  directory: `LIBNAME BV4 '.'` places the five permanent datasets there. Verify
  the assigned physical library in the LOG. Do not use the repository or reuse
  results. NOREPLACE is supplementary and has not been runtime-tested here.
- Assign a unique execution ID in an externally retained receipt. Record the
  operator, approval reference, exact invocation/submission mechanism, submitted
  path and digest, UTC start/end times, and exit status. Bind the actual submitted
  bytes, not merely a filename or a self-reported digest inside SAS. Retain the
  submitted program and verify its digest after execution.
- Capture complete LOG and LST from the start of the submission; do not redirect
  logging halfway through the program. Record SAS version/maintenance level, OS,
  host identity, timezone, encoding, locale and relevant options. The program
  prints version/options and local timestamps, but these do not supply UTC,
  custodian identity, an authenticated run ID or submission provenance.
- Retain `full_input.sas7bdat`, `probe_input.sas7bdat`, `full_plain.sas7bdat`,
  `full_traced.sas7bdat` and `pair_probe.sas7bdat` after the session closes. Compute
  each exact file SHA-256. Preserve both input descriptors and actual typed rows
  as well as all three output descriptors and typed rows. Check the constructed
  inputs against this case design before interpreting any output. Do not treat
  program bytes alone as proof of the materialized input fixture.
- Preserve the complete instrumented trace and typed dumps in the original LOG.
  Optional extracted copies must cite LOG digest and line ranges. Preserve raw
  missing tags and character padding; a lossy CSV or generic null is insufficient.
  Bind all filenames, hashes, descriptors and receipt to the same execution ID.
- Review all diagnostics, missing artifacts, truncation and row-dump completeness.
  Stop interpretation on errors, unexplained warnings, invalid-data/uninitialized
  notes, missing traces or input mismatches. END_REACHED is not success. Never
  repair an output to fit the hypothesis. Retain failed attempts separately;
  any changed program or rerun requires a new digest and execution ID.
- Independently inspect actual survivors, labels, values, multiplicity and order.
  Compare FULL_PLAIN and FULL_TRACED business outputs before using the trace to
  explain control flow. Output agreement alone does not prove instrumentation
  transparency. Trace completeness and the reviewed control structure are also
  required. Record discrepancies and reviewer confirmation without promoting
  synthetic results to historical SAS equivalence, B1 acceptance or certification.

No expected-output dataset, behavioral comparator, automatic verdict or benchmark
is supplied. This checkpoint only prepares a reference experiment. Later SAS
observations must remain separate from this document's hypotheses.

## Static preparation checks

Only static inspection is permitted at this checkpoint. No SAS compilation,
execution, row evaluation, reference generation or regression suite is involved.

On 2026-11-07, a one-off `.venv/bin/python -IB` text inspection exited 0. It
checked the two DATALINES blocks (12 + 2 records), all approved overrides, five
explicit dataset declarations, three business arms, shared full input, IF/ELSE
linkage, rejoin before MISSING, ordered CMISS calls, predicate-free event logging,
five dump targets, explicit schema declarations and local documentation links.
It found no explicit OUTPUT statement or executable expected-verdict generation.
This was text inspection, not SAS parsing, compilation or a behavioral test.

The existing `.venv/bin/python -IB scripts/check_repository.py` exited 0 with
no findings for tracked files. The two new files were also checked directly with
its existing path and limited credential-pattern rules because they are not
staged. `git diff --check`, `git diff --exit-code` against the baseline and
`git diff --cached --exit-code` exited 0: existing tracked files and the index
were unchanged. No new test, parser, comparator or infrastructure was added.
Independent custodian review and every native SAS check remain NOT_RUN.

Prepared program SHA-256:
`cabe1cc6226599e2dea59a73082d89f508bd8c5e05267aa4ecbd076db8d994a0`.
This identifies the prepared text, not an approved submission or observed run.

## Documentation used for the design

- [SAS PUTLOG](https://support.sas.com/documentation/cdl/en/lestmtsref/63323/HTML/default/n05jha8tsrpanyn19m05ss7ltv6e.htm): logging without changing the current file destination.
- [SAS IF/THEN/ELSE](https://support.sas.com/documentation/cdl/en/lestmtsref/63323/HTML/default/n1j60arf27ll4nn1ejavv3nby4pa.htm): linked alternatives and DO bodies.
- [SAS DELETE](https://support.sas.com/documentation/cdl/en/lestmtsref/63323/HTML/default/p068vr83ld69mrn1fpvs67k5l5as.htm): current-iteration termination.
- [SAS OUTPUT](https://support.sas.com/documentation/cdl/en/lrdict/64316/HTML/default/a000194540.htm): explicit OUTPUT changes implicit output behavior.
- [SAS numeric HEX](https://support.sas.com/documentation/cdl/en/leforinforref/63324/HTML/default/n0ueabv26pr2fwn19uxk2f4bf10y.htm) and [character HEX](https://support.sas.com/documentation/cdl/en/leforinforref/64790/HTML/default/p1h8xtl50tpzthn1u8kp0sji8f60.htm): typed dump representations and platform limits.

Documentation informs the design; it is not observed execution evidence.
