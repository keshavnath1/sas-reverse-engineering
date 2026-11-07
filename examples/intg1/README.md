# INTG-1 public INTAKE-to-migration review

Run these steps from the repository root with the existing Python 3.12
development installation on macOS or Linux. Use public synthetic files
only. Choose unused scratch names for both destinations.

## 1. Generate evidence and pause

```bash
intake=examples/mig2/public-input
rows=examples/mig2/CASES.json
rows_sha=f797f50799e89ee9e8d4de15e5ad718136606b1acc4e852d21f4abc86da7bb64
python3.12 -IB scripts/review_intake.py --intake "$intake" \
  --destination /tmp/sas-re-int1-intg1-example
```

Set `package` to the directory containing the `README.md` shown in the
receipt. Use its physical path, typically under `/private/tmp` on macOS
and `/tmp` on Linux. A new public workload can replace the example if it
meets the [INT-3 and MIG-2 input contract](../mig2/README.md). Keep the
evidence package unchanged.

Stop here for the operator to open a real GitHub Copilot Agent session.
Supply `scope.json`, both declared SAS source files, and the package's
`MANIFEST.json`, `README.md`, `SOURCE_1.json`, `SOURCE_2.json` and their
matching Markdown reports. Point the agent to the repository's
`sas-reconstruct`, `sas-specify`, `sas-analyze`, `sas-validate` and
`sas-architect` instructions under `.agents/skills/` and confirm which
instructions the session actually uses.

Ask for five deliverables: reconstruction, PRD, dependency analysis,
verification plan and ADR. Require file-qualified source locations and
evidence references for material claims. Ask the agent to keep individual
DATA and SORT declarations separate from their potential cross-file
handoff, leave runtime order and dataset version unresolved, and distinguish
the bounded MIG-2 engineering choice from independently observed behavior.
Request notes outside the evidence package. This workflow uses a manual
handoff. Python does not contact Copilot.

## 2. Review the claims and approve the exact record

Save a `claims.json` outside the evidence package using the
[GATE-1 record contract](../gate1/README.md). Ask Copilot to propose the record
or assemble it manually. Include the full text of the five deliverables
and the exact package manifest digest. Use the GATE-1 deliverable keys,
literal claim text from each section, stable claim IDs and resolvable
file/JSON-pointer references. Initially leave dispositions `UNREVIEWED`.

The human reviewer checks the original deliverables against the supplied
sections, checks coverage and each claim against the evidence, and sets
dispositions. Correct unsupported claims and update both the prose and
claim entries before approving. Create a separate `approval.json` with
`decision: APPROVED`, a `reviewer` label and `record_sha256` from
`shasum -a 256 "$record"` on the final claim record. Any edit to the record,
even whitespace, requires a new review and approval. The label is an
operator assertion.

## 3. Continue through GATE-1 to MIG-2

Set `record` and `approval` to the physical paths of the saved JSON files.

```bash
python3.12 -IB scripts/review_to_migration.py --intake "$intake" \
  --package "$package" --record "$record" --approval "$approval" \
  --rows "$rows" --rows-sha256 "$rows_sha" \
  --destination /tmp/sas-re-intg1-example
```

The JSON receipt reports the gate decision and any pending or blocking codes.
Omit both review arguments while waiting for Copilot to get
`REVIEW_REQUIRED` with `COPILOT_CLAIM_RECORD_REQUIRED`. Supply just the
record to run the bounded claim checks while waiting for human approval.

| Receipt | Operator action |
| --- | --- |
| `REVIEW_REQUIRED` | Supply the missing claim record, complete pending dispositions or coverage, or obtain approval of the current record bytes. |
| `BLOCK` | Resolve the listed citation, classification or binding defect and submit a reviewed correction. For an input refusal, check the record path, JSON structure and package manifest digest. |
| `PASS`, migration `REFUSED` | Correct the reported candidate input, scope, identity or destination problem. Approval covers the review; MIG-2 still validates the source and rows independently. |
| `PASS`, migration `PUBLISHED` | Inspect the plan, rows and validation. A candidate comparison `FAIL` exits 1 and retains the engineering discrepancy. With no expected rows, comparison is `NOT_RUN`. |

The first two cases create no migration directory. Keep the JSON receipt as
the review diagnostic. The continuation replays deterministic intake
validation, verifies the approved record and approval again, and selects
only MIG-2's DATA projection and ascending SORT. It writes a fresh bundle
with `PLAN.json`, `ROWS.json`, `VALIDATION.json`, `GATE.json` and a manifest
binding the source evidence, review, approval, input rows, code and output
bytes. Keep the original record and approval separately for replay.
The existing standalone MIG-2 demo remains a separate engineering command.

GATE-1 PASS permits this engineering continuation. The bundle retains
DRAFT authority, UNAVAILABLE behavioral evidence, UNVERIFIABLE semantic
verification, BLOCKED semantic acceptance, NOT_RUN reference and benchmark
execution, and UNBOUND historical source/run provenance.

For the opt-in pinned public preparation and population gate suite, see the
[INTG-3A MIG-5 operator workflow](../intg3a/README.md).
