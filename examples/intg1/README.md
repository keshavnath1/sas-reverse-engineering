# INTG-1 public INTAKE-to-migration review

Run these steps from the repository root with the existing Python 3.12
development installation on macOS or Linux. Use public synthetic files
only. Choose unused scratch names for both destinations.

## Start with a new INTAKE folder

Put the authorized public synthetic programs and supporting files in
`INTAKE`. From the checkout, inventory the folder before declaring scope.

```bash
python3.12 -IB scripts/review_intake.py --intake ./INTAKE --inventory
```

The JSON report inventories file names and hashes bounded recognized files.
It probes whole SAS files with the existing DATA, SORT and logistic
recognizers and reports supported, partial or unsupported syntax.
For one or two flat sources with recognized operations, the report can
propose a scope with exact hashes, ranges and modes. Review the proposed
scope and save the `proposed_scope` object as `INTAKE/scope.json` to declare
the files you authorize for review. The inventory command leaves that
decision with the operator. For existing scopes, use the evidence command
below. For unrecognized programs, review the reported diagnostics and
declare bounded ranges explicitly when the existing modes fit.

The scope can bind up to four supporting files as notes, logs, listings
or configuration. The evidence package records their identity and role.
Treat their contents as supporting material during human review. A file
hash alone establishes neither runtime provenance nor SAS behavior.

## 1. Generate evidence and pause

```bash
intake=examples/mig2/public-input
rows=examples/mig2/CASES.json
rows_sha=f797f50799e89ee9e8d4de15e5ad718136606b1acc4e852d21f4abc86da7bb64
python3.12 -IB scripts/review_intake.py --intake "$intake" \
  --destination /tmp/sas-re-int1-intg1-example --modernization-drafts
```

Set `package` to the directory containing the review entry point shown in the
receipt. Use its physical path, typically under `/private/tmp` on macOS
and `/tmp` on Linux. A new public workload can replace the example if it
meets the [INT-3 and MIG-2 input contract](../mig2/README.md). Keep the
evidence package unchanged.

With `--modernization-drafts`, open `MODERNIZATION_REVIEW.md` for the
five-skill handoff. The two YAML drafts use JSON syntax, a subset of YAML
1.2, and carry the evidence manifest hash and input and evidence identities.
Compare these bindings against the current package before using the drafts.
Regenerate for a changed scope. The drafts record pending decisions and are
operator review inputs. The existing candidate uses the scoped evidence and
GATE-1 record as its execution inputs.

Stop here for the operator to open a real GitHub Copilot Agent session.
Supply `scope.json`, both declared SAS source files, and the package's
`MANIFEST.json`, `README.md`, `SOURCE_1.json`, `SOURCE_2.json` and their
matching Markdown reports, plus the modernization handoff and drafts when generated. Point the agent to the repository's
`sas-reconstruct`, `sas-specify`, `sas-analyze`, `sas-validate` and
`sas-architect` instructions under `.agents/skills/` and confirm which
instructions the session actually uses.

Ask for the five deliverables below using the actual INTAKE subject.

| Skill | Draft deliverable | Evidence to use |
| --- | --- | --- |
| `sas-reconstruct` | Reconstruction and TRACE | Selected declarations, source-qualified spans, unsupported constructs and uninspected ranges |
| `sas-specify` | PRD and specifications | Traced calculations and transformations, plus open questions about business intent |
| `sas-analyze` | Dependency and optimization analysis | MAP edges, state and ordering constraints, with unresolved execution order and dataset versions |
| `sas-validate` | Verification plan | Public engineering checks and separate obligations for independently authorized SAS reference comparison |
| `sas-architect` | Architecture, ADR and migration plan | Bounded candidate fit, unresolved assumptions, and conditions that would justify distributed alternatives |

Require file-qualified source locations and evidence references for material
claims. Keep individual declarations separate from potential cross-file
handoffs. Save drafts and review records outside the evidence package.
Python generates the evidence locally. The operator hands it to Copilot
and records the human decision before candidate publication.

## Check reviewed configuration

Run the planner against the same scoped INTAKE and review package.

```bash
python3.12 -IB scripts/plan_modernization.py --intake "$intake" --package "$package"
```

The planner prints JSON. A fresh draft returns `REVIEW_REQUIRED` with
the pending fields and supported choices. Copy the drafts outside the
package, review the choices, set each document's status to `REVIEWED`,
and supply the copies with `--profile` and `--tie-out`. Use the JSON syntax
emitted by the version 1 YAML drafts. Preserve their bindings and authority
fields. The planner rebuilds the selected evidence and checks the package
bytes and both bindings before proposing a plan. Regenerate the drafts if
the source, scope or supporting inputs change.

| Reviewed field | MIG-2 value |
| --- | --- |
| `target.runtime`, `target.distributed` | `"python"`, `false` |
| `execution.multiplicity_policy` | `"PRESERVE"` |
| `execution.ordering_policy` | `"ASCENDING_KEY_STABLE_TIES"` |
| `execution.category_policy` | `"NOT_APPLICABLE"` |
| `checks.source_coverage` | `"REVIEWED"` |
| `checks.population_and_multiplicity`, `checks.ordering_and_output`, `checks.numeric_tolerance` | `"EXACT"` for the public engineering comparison |

The profile expresses operator policy. The report links source declarations
separately and retains unresolved runtime obligations. `PLAN_PROPOSED`
exits 0 and returns a deterministic plan with the exact configuration file
identities. Pending choices exit 1. Stale inputs, contradictory choices and
unsupported candidate scopes exit 2 without a plan.

A pinned INTG-3 subject prepared by `review_mig5.py` has its own route.
Pass that package with `--package` and omit `--intake`. Use `--emit-drafts`
to print both version 1 drafts as a JSON mapping, then save each named
object in its own YAML file. MIG-5 uses `ORIGINAL_INPUT_ORDER`. The pinned
downstream route uses `EXPORT_ASCENDING_ID_SCORE_ORIGINAL_PRE_SORT`,
`PINNED_MOD2_MAPPING` and `PINNED_MOD2_TOLERANCE` for its existing fixed
scoring contract. Both routes replay the pinned subject before planning.

The planner reports the proposed route and leaves publication to the
existing continuation. Follow the separate GATE-1 and human approval steps
below for MIG-2 or the pinned INTG-3 operator workflow for MIG-5.

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
