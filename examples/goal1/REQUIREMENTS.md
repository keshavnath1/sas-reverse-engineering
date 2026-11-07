# Draft PRD and module specifications

Deliver a reviewable replacement design for the pinned public preparation, population, export and scoring workflow. Operators need to see which rows reached candidate row end, why gates blocked, and which branches produced artifacts. Business owners need traceability to the source before accepting the replacement. Independent SAS validation is a separate release criterion.

| Requirement | Module contract and engineering acceptance | Basis |
| --- | --- | --- |
| R1 Prepare | Typed public case in, ordered decisions and eligible full-mode row-end records out. Apply the six guards in source order. Preserve first exclusion, assignments and isolated branch fallthrough diagnostics. Exclude probes and terminated rows from the handoff. | [TRACE rules](TRACE_MAP.md#rules), [MIG-5](../mig5/README.md). |
| R2 Audit | Eligible records in, population counts and repeated-ID groups out. Preserve multiplicity. Report group size separately from group count. Verify the pinned cases against public expected statistics. | [TRACE SQL](TRACE_MAP.md#queries), [MIG-4](../mig4/README.md). |
| R3 Gate | Counts and explicit guard inputs in, ordered gate decisions out. Record skipped tests and first blocker. Both downstream branches use the same candidate gate result. Verify a duplicate block publishes diagnostics only. | [TRACE gates](TRACE_MAP.md#gates), [INTG-3](../intg3a/README.md#include-sort-csv-and-fixed-coefficient-scoring). |
| R4 Export | On PROCEED, serialize 19 business fields from full sorted records using the documented UTF-8 CSV policy. Verify ascending IDs, row multiplicity, column order and serialized bytes. Stable equal-key order is a candidate policy. | [TRACE SORT](TRACE_MAP.md#sort), [MIG-6](../mig6/README.md). |
| R5 Score | On PROCEED, use original pre-sort eligible rows and bound public mapping and coefficients. Produce design, eta and probability in candidate input order. Verify encoding, event label, numeric tolerance and case alignment. | [TRACE model](TRACE_MAP.md#model), [MOD-2](../mod2/README.md). |
| R6 Publish | Check the exact subject and final record digests. GATE-1 refusal creates no migration package. Engineering replay must preserve filenames and bytes. | [GATE-1](../gate1/README.md), [INTG-3](../intg3a/README.md). |

R1–R6 are draft requirements. Source declarations motivate them. Engineering acceptance criteria are candidate checks. Fitting, ODS production, performance qualification and SAS acceptance are outside this public slice.

## Business decisions required

- Who owns the status allowlist and Default event definition? Should blanks, case variants and unmatched values be rejected, mapped or investigated?
- Is the duplicate gate intentionally fail-fast? Who supplies and approves the expected population, and when should the optional flag be enabled?
- Is ascending ID order consumer-visible? Which schema, padding and overwrite policy must downstream consumers contractually rely on?
- Is fixed scoring useful as a separate deliverable? Who owns coefficient provenance, category drift policy and future fitting or recalibration?
- Which decisions require business sign-off, and which release decisions require a custodian's attributable SAS results?
