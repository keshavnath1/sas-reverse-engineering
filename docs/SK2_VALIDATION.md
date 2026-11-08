# SK-2 validation

Baseline `cf6588733a32a7bbc8ac952c26321a6024adfc6d`. The new [sas-analyze](../skills/sas-analyze/SKILL.md) and [sas-validate](../skills/sas-validate/SKILL.md) instructions use the existing fixed public package, diagnostics, frozen cases and decision matrix. Both permit existing-package inspection and notes in chat. The existing discovery link exposes all five canonical skill files.

## Observed skill use

| Check | Observed result |
|---|---|
| Native parsing and discovery | macOS, `codex-cli 0.167.0-alpha.3.2`. Existing app-server probe called `skills/list` with repository cwd and `forceReload: true`. All five skills were enabled with canonical paths and zero errors, exit 0. |
| File-guided analysis trial | An independent agent followed sas-analyze to answer which boundaries might support parallelism. It checked the nine payload hashes, traced E4/E2 across modules and E1 into SQL, distinguished E3 BY state from O2 current-row arithmetic, and kept O2/O3 optimization proposals conditional. It found no proven independent operation, no RESOURCE edge and no LOG/LST measurement. Ray/Dask remained unevaluated hypotheses. |
| File-guided validation trial | A second agent followed sas-validate to explain the eight FAIL outcomes. Read-only hashes and literal inspection reconciled all 17 case identities, inputs, probes, expected rows, verdicts and first-discrepancy stages. All matched, with 7 PASS, 8 deliberate FAIL and 2 UNVERIFIABLE. It preserved B04's limited split, B12's validator defect and B17's O1–O3 scope. |
| Loading and completion limits | Both agents completed explicitly file-guided reviews. Native discovery was checked separately. Typed loading and completed model execution through native skill selection were untested. Desktop picker, implicit selection and native Windows discovery were untested. |

The validation trial flagged existing O2 wording that could allow within-tie multiset comparison alone. B11 requires SET to retain the chosen SORT stream. The skill-linked comparison rules and decision matrix supply that stronger condition. This finding is recorded for review under the accepted-artifact preservation boundary. [Native ADR](../examples/offline-review/ADR_NATIVE.md), [Spark ADR](../examples/offline-review/ADR_SPARK.md).

## Checks executed

- `.venv/bin/python -m unittest discover -s tests -v` exited 0 with **782/782** passing in 42.115 seconds on macOS 26.6.2 (25G83), ARM64, CPython 3.12.5. The 781 existing regressions were retained. Existing skill structure, metadata, paths, alias and authority checks now cover five skills. One added integration test follows actual skill links and binds the diagnostic source, graph subject and frozen case-table digest to the existing package.
- Compared all 160 baseline tracked files as original bytes. Only README and the skill test file differ among those baseline files. All 23 accepted example files matched, including the twelve previews, original decision review and ten-file consolidated package. The consolidated manifest SHA-256 is `3efe4f68b923a2a59b37041cf30663c856891beb265ccad395fc2078e6970952`.
- Existing preservation audit, `.venv/bin/python /private/tmp/sas-re-sk1-proof.q6kb2j8q/preserve.py --label sk2 --source /Users/divyasreegundaram/Downloads/sas-migration-skill-enhancement-v2/sas-reverse-engineering`, exited 0. All 30 regenerated historical artifacts, both complete reports, eight frozen hashes and three diagnostic hashes matched retained references. Downstream metadata matched baseline commit pin `bc754e0f1204a99020c864df2a5b25983005e09c`.
- The optional skill-creator `quick_validate.py` exited 1 for both skills because its environment lacks PyYAML. Existing repository checks and the native Codex parser passed. No dependency was installed. The first discovery probe stopped because its temporary home directory was absent. Creating that scratch directory allowed the existing probe to pass. A read-only validation inspection initially encountered an unrelated nonliteral declaration and then successfully restricted inspection to the named literal definitions.

New instruction-file SHA-256 values follow.

```text
sas-analyze   f2ffe8a04623381d77cb6aa42800c4e50917007874f4f0324eef63b2af9964b7
sas-validate  10d37d44a08c3a9d487c6e16c4f8a486c9811c445cb686e6576ecf5d8af100f5
```

All reviews retain DRAFT authority, UNVERIFIABLE semantic verification, BLOCKED semantic acceptance and benchmarks NOT_RUN. Production selection, operational parallelism, independent evaluation and SK-3 require separate approval.
