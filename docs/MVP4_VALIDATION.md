# MVP-4 validation

The [decision review](../examples/mvp4/DECISION_REVIEW.md) covers nine obligations for the existing native Python and Spark proposals. It distinguishes what the checker detected from what either proposed migration still needs to demonstrate. The 17 frozen controls matched their expected outcomes: 7 PASS, 8 deliberate FAIL, 2 UNVERIFIABLE. B12 rejected a validator that demanded a hidden secondary order. B17 passed for O1–O3 while the include and complete workflow stayed BLOCKED.

Reproduce from this development checkout using its Python 3.12 environment:

```bash
.venv/bin/python -IB scripts/mvp4_review.py
```

The [script](../scripts/mvp4_review.py) prints Markdown to stdout. It accepts no paths or source input. It checks POSIX evidence capabilities and the linked review documents, uses MVP-3's literal-only reader to verify the source fixture and case table before importing the fixture adapter, and reconstructs only the fixed public subject in disposable scratch. The [private renderer](../src/sas_re/_decision_review.py) consumes the supplied graph and the exact complete report. A filtered, reformatted, missing or changed report is refused even if some rows still match.

| What was bound | SHA-256 |
|---|---|
| Original MVP-2 graph | `19f41dea50825469a89d8fc545fee1d87f09af946d130d62de8f946d90b78017` |
| Public source fixture / frozen case table | `dce463011111389bbd84901b2a94632305b287605af98493f3f88744e2f94716` / `7ca4c6b50cdc7f5b7ce2ee422f5adfe883dba82a39b064140fba2d7a70702342` |
| Full MVP-3 stdout, 15,660 bytes | `aee7cbd480b1f6794888616af9c55e8896ecb13fa3dc1585d1b012f0a8508600` |
| Generated Markdown, 8,516 bytes | `9aa03933aa24121b786f3939e4e4bec3555302b43c117e3dda9333de9fa04afe` |

## Executed checks

- **macOS 26.6.2 (25G83), ARM64, CPython 3.12.5.** Fresh baseline `8e9c0484a21c1fa8211f7a5418bac62a4bc1bd48` passed 758/758. The candidate passed 766/766 with `.venv/bin/python -m unittest discover -s tests -v`. The eight new tests also passed with `-p test_mvp4_review.py`.
- Two fresh demo runs matched the sample byte for byte. One ran with an empty executable search path and calibrated Python socket/child-process probes. No attempts were observed. All 54 local links resolved, including case line references and original graph evidence anchors.
- Tests refused changed graph/source bindings, a missing case, same-length report corruption, suppressed discrepancies, an unexpected FAIL, an invalid promotion and an edited ADR. A scratch fixture initially executed its altered declarations before the expected digest refusal. The script now verifies the data first. The regression confirmed exit 2, empty stdout and no execution of the injected statement.
- Fresh P1/P2A replays matched all 30 historical files and both complete stdout reports. Regenerating MVP-1 and MVP-2 matched all 12 documents and both complete demo manifests. Eight frozen hashes and three P3-A1 hashes matched. The downstream checkout check passed for all 20 files at `bc754e0f1204a99020c864df2a5b25983005e09c`.

The review retains DRAFT authority, UNVERIFIABLE semantic verification, BLOCKED semantic acceptance and benchmarks NOT_RUN. Only fixed public development evidence was assessed. Native Windows qualification, SAS execution, distributed runtime trials and independent semantic evaluation were outside this increment.
