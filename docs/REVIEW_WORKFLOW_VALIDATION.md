# Offline review workflow validation

Start at the [sample README](../examples/offline-review/README.md). From the development checkout with its prepared Python 3.12 environment active, the exact command exercised was:

```bash
python3.12 -IB scripts/review_workflow.py --destination /tmp/sas-re-review
```

The [entry script](../scripts/review_workflow.py) checks the fixed fixture and case table against their accepted hashes before importing the fixture adapter. It uses the existing P2A reconstruction and source-consistency check, P3-A1 diagnostics, MVP-2 preview generator, MVP-3 behavioral tie-out and MVP-4 review generator. The preview and decision review consume the same in-memory graph. The demo neither accepts an intake path nor writes to an evidence store.

## Package and byte comparisons

| Output | Executed comparison |
|---|---|
| Six MVP-2 Markdown files | All six matched the accepted files byte for byte. The SHA-256 of their canonical filename-to-digest mapping is `218a0111e99f64d4869570e46e7fa951ff8dfe1db617e9d0d72f9dc06624658c`. |
| TIEOUT.json | Exact 15,660-byte MVP-3 stdout, SHA-256 `aee7cbd480b1f6794888616af9c55e8896ecb13fa3dc1585d1b012f0a8508600`. All 17 cases matched expectations: 7 PASS, 8 deliberate FAIL and 2 UNVERIFIABLE. |
| DECISION_REVIEW.md | Regeneration matched the original SHA-256 `9aa03933aa24121b786f3939e4e4bec3555302b43c117e3dda9333de9fa04afe`. Only link targets were localized. Packaged SHA-256 is `0c333a998546beffacade3cb7c54b420de31139651c9f543954bb28880276e3d`. |
| README.md | Gives the reading order, rerun command, scope and limitations. Its two source excerpts match the original bytes. All 17 case anchors retain their case IDs, input/probe, expected and observed verdicts. |
| MANIFEST.json | Names all ten files, binds the synthetic subject and hashes the nine payloads. Its own whole-file digest is printed separately in the command receipt: `3efe4f68b923a2a59b37041cf30663c856891beb265ccad395fc2078e6970952`. This is an integrity check, not a release signature. |

The subject is `mvp2-public-workspace / ordered-measurements / preview-2`, graph SHA-256 `19f41dea50825469a89d8fc545fee1d87f09af946d130d62de8f946d90b78017`. Source consistency passed. Reconstruction stayed PARTIAL. The unresolved include keeps full-workflow acceptance BLOCKED.

## Checks executed

- **macOS 26.6.2 (25G83), ARM64, CPython 3.12.5.** The accepted baseline `4a19ea1242e8aba685bef3dd53c222f6fde8d6b8` passed all 766 existing tests. The candidate passed 774/774 with `.venv/bin/python -m unittest discover -s tests -v`. All eight new integration tests passed separately with `-p test_review_workflow.py`.
- Two fresh runs and the checked-in sample matched across all ten files. All 280 local Markdown links resolved, including the original source and every case reference. An empty-PATH run monitored for socket/child-process attempts observed none. Function-call tracing observed reconstruction, dependency diagnostics, preview generation, tie-out and decision review.
- Existing destinations and symlinks were refused. Concurrent writers to one fresh destination produced one complete package and one refusal. Tests rejected an intake argument, missing and altered evidence, and a promoted reconstruction status. An injected write fault removed the incomplete destination. The manifest is installed last. These checks cover normal completion and handled failures, not crash durability.
- Fresh P1/P2A replays matched all 30 artifact files and both complete reports. Regeneration preserved all 12 earlier preview documents, both preview stdout manifests, the original decision review and full tie-out report. Eight frozen hashes and three P3-A1 hashes matched. The read-only downstream check matched all 20 pinned files at `bc754e0f1204a99020c864df2a5b25983005e09c`.
- The first focused run reached the comparison before the sample existed. A comparison during README revision also saw different intermediate bytes. Both checks were repeated against the final sample. The unactivated system Python lacked the installed project package; the documented command was verified with the existing development environment active.

This is a fixed synthetic developer demonstration. Each packaged artifact retains DRAFT authority, UNVERIFIABLE semantic verification, BLOCKED semantic acceptance and benchmarks NOT_RUN. No real-source intake, SAS or Spark execution, native Windows qualification, or independent semantic evaluation ran. The next capability is a separate decision after usability review.
