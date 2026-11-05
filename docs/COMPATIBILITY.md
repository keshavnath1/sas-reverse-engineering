# Pinned downstream boundary

Repository: `https://github.com/keshavnath1/Agent-mastery.git`.
Branch: `feature/governed-learning-memory`.
Commit: `bc754e0f1204a99020c864df2a5b25983005e09c`.

The sole machine-readable baseline is packaged at `src/sas_re/data/baseline.json`.
It contains SHA-256 digests computed from Git blobs at that exact commit, rather
than a potentially dirty worktree. Twenty files cover operating rules, workflow,
profile/tie-out templates, trace/map contracts, run state, relevant skills, helpers
and CI. The metadata is not a P1 evidence schema.

| Pinned observation | Compatibility implication |
|---|---|
| Workflow schema version 1.0, one-skill and human gates | Upstream status cannot advance downstream state |
| Profile version 2, `UNAPPROVED_TEMPLATE`, null runtime selection | No runtime or population inferred by this repository |
| Tie-out template-3 and draft/approval schema | Integrity cannot supply oracle, tolerances or human approval |
| Trace/map schemas and extraction instructions | Reusable vocabulary; no automatic SAS parser or verified graph |
| Pattern `import` skill | Not an architecture-bundle receiving adapter |
| Canonical singleton paths | No upstream direct writes or competing live graph |
| Public-template source/data exclusions | New upstream fixtures cannot be copied downstream indiscriminately |

Preserve `stage1_extraction/output/execution_trace.json`,
`policy/policy_registry.yaml`, `artifacts/semantic_ir/<module>.json`, and
`artifacts/evidence/runs/<run-id>/attempts/<attempt-id>/` in future integration.
P0 does not create or modify any of them.

`sas-re check-baseline --checkout PATH` requires HEAD equality, clean worktree and
all 20 actual file hashes to match. Missing/changed/symlink files and changed HEAD
fail. An inaccessible checkout is BLOCKED. `--remote` independently queries the
branch ref; an unreachable remote is BLOCKED, and a changed tip fails. Combining
checks retains each result; any drift fails overall, otherwise an unavailable
check blocks overall. No baseline is automatically updated.

On drift, inspect upstream changes and approve a new compatibility baseline
separately before changing the pinned metadata. Baseline PASS is not a downstream
schema integration test, evidence approval, or proof of source reconstruction.
