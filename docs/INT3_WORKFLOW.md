# INT-3 two-source public synthetic intake

Use version 2 of `scope.json` for exactly two authorized public synthetic
sources. Version 1 continues to select one source. The original INT-1 fixture
still uses its pinned scope.

For a small example, put the following single line in `prepare.sas.txt`.

```sas
data work.staged; set work.sample; keep id amount; run;
```

Put this single line in `order.sas.txt`.

```sas
proc sort data=work.staged out=work.ordered; by id; run;
```

Compute each source's SHA-256 over its exact stored bytes and use the lowercase
digests in `scope.json`.

```json
{
  "version": 2,
  "scope": "public-synthetic",
  "sources": [
    {"path": "prepare.sas.txt", "sha256": "<first SHA-256>", "ranges": [[1, 1]], "mode": "data"},
    {"path": "order.sas.txt", "sha256": "<second SHA-256>", "ranges": [[1, 1]], "mode": "sort"}
  ]
}
```

The per-source mode uses the same supported values and range requirements as
INT-2. Flat filenames, size limits, optional supporting notes, verified
identities, and scratch destination rules also apply. A version 2 manifest puts
`mode` on each source entry. [INT-2 manifest and filesystem rules](INT2_WORKFLOW.md)

```bash
.venv/bin/python -IB scripts/review_intake.py \
  --intake /absolute/path/to/INTAKE \
  --destination /tmp/sas-re-int1-two-source
```

The package contains a README index and cross-file MAP, two source evidence JSON
files, their existing review reports, and a manifest. The manifest maps each
original filename to its evidence, report, and coverage. Report numbering is
alphabetical for navigation. Each citation resolves within its own file.

Cross-file MAP compares the existing selected operation declarations. A named
dataset written in one source and read in the other yields a **potential**
handoff with citations to both declarations. Execution order and dataset version
remain unresolved, including whether two WORK references refer to the same
session. An empty match list is unresolved. The comparison scope is the selected
DATA, SORT, or LOGISTIC operation accesses and declared LOGISTIC ODS targets.
Interval effects remain in the per-source reviews. Includes and macro expansion
remain outside this slice.

Keep the human-invoked Copilot handoff. Supply the manifest and its payloads,
the two approved public sources, and their scope file. Verify the hashes against
the receipt first. Ask for notes with file-qualified source citations and a
distinction between declared accesses and potential handoffs. Copilot remains
`NOT_TESTED` because no usable session was verified. [Review handoff](INT1_WORKFLOW.md#copilot-handoff)
