# SK-1 validation

The three instruction-only skills are [sas-reconstruct](../skills/sas-reconstruct/SKILL.md), [sas-specify](../skills/sas-specify/SKILL.md) and [sas-architect](../skills/sas-architect/SKILL.md). They guide the existing fixed public workflow and evidence review. Python continues to own reconstruction, validation, hashes and diagnostics.

## Discovery and actual agent use

Official Codex guidance specifies repository-local `.agents/skills` roots and supports symlinked skill directories. This repository uses one relative link, `.agents/skills -> ../skills`, so each skill has one authoritative instruction file. The guard permits only that exact staged mode/target and working-tree link, with real in-tree parents. [Official discovery guidance](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)

| Executed check | Observed result |
|---|---|
| Installed ChatGPT-bundled `codex-cli 0.167.0-alpha.3.2`, macOS. App-server stdio `initialize`, then `skills/list` with the requested cwd and `forceReload: true` | `skills/` alone returned no repository skill in a scratch control. With the link, the actual repository returned all three enabled skills, canonical paths and zero errors. Discovery worked from the repo and `scripts/`. The parent workspace returned none. |
| `codex debug prompt-input` | Metadata for all three skills appeared in the live developer prompt. |
| Actual app-server `thread/start` and `turn/start` with each discovered typed skill selection | The exact final SKILL.md body appeared in each runtime input. These offline probes used an intentionally absent test credential. All three turns then failed with `Missing environment variable: SK1_DISABLED_TOKEN` before a provider request. Exact-load assertions exited 0. Model completion through those CLI turns was not tested. |
| Independent Codex agent, explicitly supplied the three file paths | Followed all three skills. Ran `.venv/bin/python3.12 -IB scripts/review_workflow.py --destination /tmp/sas-re-review-sk1-forward`, exit 0. Checked nine payload hashes and the receipt, traced the module handoff, identified the unsupported final-sequence requirement and open business intent, and kept Spark selection and BY splitting blocked. This tested file-guided use in the existing session. |
| Desktop skill picker, implicit model selection and native Windows | Untested. On a checkout that materializes the symlink as a regular file, use the canonical skill path explicitly. Native Windows evidence I/O remains BLOCKED. |

The independent forward test found ambiguity between sample links and a fresh output directory. The two review skills now explicitly direct fresh-run review to files from that same package. The reviewing agent reread and confirmed that clarification. Live exact-body loading was repeated after final prose edits.

The final skill files have these SHA-256 values.

```text
sas-reconstruct  d1f6b55071074c016d7de410d41f732d822d252f33fe85b0b4f098320910eb3c
sas-specify      3b65e951ffcce9e09abbf36c88504e49ebca9d9f55619688f6e089ef17bb8de0
sas-architect    e4d3802fb1ca3ac6ec0bc3172a029dc29f294e13bf45deb444225c858f257eaa
```

## Deterministic validation and preservation

- macOS 26.6.2 (25G83), ARM64, CPython 3.12.5. The clean baseline `51f1a735fd245ce40c1baad803d7401b93def4a6` passed 774/774. Candidate `.venv/bin/python -m unittest discover -s tests -v` passed **781/781**. The seven focused checks passed with `-p test_sk1_skills.py`.
- GitHub Actions on Ubuntu 24.04.5 x64 and CPython 3.12.5 passed at implementation commit `9d2fc6cab8f76c13aa4a737c2fbcf33061988bf0`. `python -m unittest discover -s tests -v` passed 781/781 in 41.233 seconds. After wheel installation, `python -m unittest discover -s "$GITHUB_WORKSPACE/tests" -v` passed 781/781 in 40.442 seconds. Repository guard, package build/install, demonstrations and remote downstream drift check passed. This run preceded the final prose-only edits and this validation update. [Executed CI run](https://github.com/keshavnath1/sas-reverse-engineering/actions/runs/42325205085)
- Metadata, real entry points and document links passed. The command extracted from the skill produced the same ten files and graph subject. Simulated Windows refused before creating the destination. Static and simulated checks confer no live-agent or Windows qualification.
- The guard positive control passed. Independent adversarial checks refused nine staged/working-tree target, mode, ancestor and unrelated-file substitutions. The initial focused guard test failed before its exact-link exception was implemented and passed afterward. Other private paths and symlinks remain excluded.
- The bundled skill-creator `quick_validate.py` was attempted for all three skills and exited 1 because its Python environment lacked PyYAML. No dependency was installed. The repository tests validate the deliberately simple frontmatter, and the actual Codex parser discovered all three final files without errors.
- All 30 P1/P2A historical files and both complete reports matched fresh and retained baselines. Eight frozen hashes, three P3-A1 hashes, the twelve earlier preview files and manifests, and all ten consolidated files matched. Consolidated MANIFEST SHA-256 remains `3efe4f68b923a2a59b37041cf30663c856891beb265ccad395fc2078e6970952`. The read-only Agent-mastery check passed for all 20 files at `bc754e0f1204a99020c864df2a5b25983005e09c`.

The skills retain DRAFT authority, UNVERIFIABLE semantics, BLOCKED independent acceptance and benchmarks NOT_RUN. SK-2 analysis/validation and SK-3 handoff work require separate approval.
