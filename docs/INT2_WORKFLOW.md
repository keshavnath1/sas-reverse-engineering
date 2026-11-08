# INT-2 configurable public synthetic intake

Create a directory with one public synthetic SAS source, a `scope.json` manifest,
and up to four optional public notes. Declare only files you are authorized to
review. The manifest declares scope and expected identities. Authorization
and public-data classification are the caller's responsibility.

For example, put the following three lines in `sort.sas.txt`.

```sas
proc sort data=work.sample out=work.ordered;
  by id;
run;
```

Compute its original-byte digest with `shasum -a 256 sort.sas.txt` and put that
lowercase hexadecimal value in the manifest.

```json
{
  "version": 1,
  "scope": "public-synthetic",
  "mode": "sort",
  "sources": [
    {"path": "sort.sas.txt", "sha256": "<64 lowercase hexadecimal digits>", "ranges": [[1, 3]]}
  ]
}
```

From the repository root, run the existing entry point with the prepared
Python 3.12 environment.

```bash
.venv/bin/python -IB scripts/review_intake.py \
  --intake /absolute/path/to/INTAKE \
  --destination /tmp/sas-re-int1-configured
```

The destination uses the existing fresh system-scratch naming convention.
The workflow uses the existing POSIX evidence I/O gate, safe inventory and
reads, disjointness check, and exclusive writer.

| Mode | Inclusive line ranges | Existing review |
| --- | --- | --- |
| `data` | One | Bounded DATA declarations and unsupported-statement register |
| `sort` | One | Bounded PROC SORT declaration |
| `logistic` | One | Bounded ODS and PROC LOGISTIC fit-to-score review |
| `data-sort` | Two, ordered and disjoint | DATA then SORT and bounded intervening inventory |
| `data-sort-sql` | Two, ordered and disjoint | DATA then SORT with existing SQL-gate recovery |

Use flat filenames. The source must end in `.sas` or `.sas.txt` and fit the
64 KiB read limit. The manifest limit is 4 KiB. An optional `supporting` array
accepts entries such as
`{"path":"context.md","sha256":"<digest>","role":"note"}`. Each note must end
in `.md` or `.txt` and fit the 16 KiB limit. Notes are verified by identity
only. Their contents are outside source analysis and the output package.

The declared file set must match the inventory. Unsafe names, aliases,
symlinks, unsupported modes, invalid line ranges, multiple source declarations,
and digest mismatches are refused. The byte-identical INT-1 scope and fixture
continue through the original compatibility path.

## Read the package

- `MANIFEST.json` records all input and payload identities, review mode,
  review status, and coverage. Coverage partitions original source bytes into
  selected review ranges, bounded interval inventory when applicable, and
  uninspected ranges. Selection identifies review scope even when syntax is
  unsupported. Hashing covers the full input file.
- `EVIDENCE.json` is the existing source evidence, including unsupported
  statement records and original coordinates. A fully unsupported single
  range produces a blocked diagnostic package and exits 2. A two-range review
  requires recognizable DATA and SORT endpoints, and an invalid pairing is
  refused. A recognized DATA step can still contain unresolved statements.
- `README.md` is the existing source review. Two-range packages also include
  `MIGRATION_REVIEW.md` with TRACE/MAP, requirements, validation obligations,
  and conditional architecture considerations. The logistic single-range
  review includes TRACE/MAP in its README.

The declared relationships carry execution uncertainty. The manifest retains
DRAFT authority, unavailable behavioral evidence, unverifiable semantics,
blocked acceptance, reference and benchmark status NOT_RUN, and historical
provenance UNBOUND.

## Copilot handoff

Copilot review is `NOT_TESTED`. The workstation check found VS Code, but the
extension listing did not show Copilot and emitted a log-directory permission
error. No usable session was verified.

For an authorized, human-invoked review, supply the generated manifest and its
payload files, plus the approved public source and scope file. Verify hashes
against the command receipt and manifest first. Use the existing prompt and
check citations against EVIDENCE.json. Supporting notes are optional context
only if separately authorized for sharing. [INT-1 review prompt](INT1_WORKFLOW.md#copilot-handoff)
