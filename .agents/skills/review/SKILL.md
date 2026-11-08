---
name: review
description: Independently challenge SAS evidence and draft requirements/architecture against original authorized intake in a genuinely fresh context. Use after design or one author correction; review readiness does not approve or repair drafts.
---

# Review, do not author

Follow repository `AGENTS.md`, `README.md`, `DESIGN.md` and `orchestrate` boundaries. Use a genuinely isolated fresh reviewer context where the host supports it, with original authorized input root and actual draft paths. Reread intake and drafts directly, not only the author's summary. Read [the shared SAS checklist](../understand/references/sas-reading.md).

Record actual reviewer/context identity, isolation mechanism, materials received and limitations. A named reviewer profile, role prompt or same-context self-check is not proof of independence. If a fresh context is unavailable, set `REVIEW_INDEPENDENCE: NOT_AVAILABLE`, identify any self-check as such, and cap document readiness at `PARTIAL`; never self-pass.

## Check

1. Before source rereads, check the existing manifest with `python3 scripts/input_snapshot.py check --input <root> --manifest <run>/SOURCE_MANIFEST.json` when available; check again after reads. Never regenerate it to mask mutation, invent hashes, follow symlinks, scan parents or fetch includes. Without the helper/checkable manifest record `SOURCE_INTEGRITY: NOT_CHECKED`. Changed input requires a new linked run, not review of mixed facts.
2. Read sealed `SOURCE_EVIDENCE.md`, `PRD.md`, `MODULES.md`, `ARCHITECTURE.md`, actual ADRs, `VALIDATION_PLAN.md` and progress. Check important original file/line citations and F/O/D/U links against intake; citation existence alone does not establish semantic support. State what was checked, sampled, unread or inaccessible and why.
3. Challenge source/log attribution and coverage; distinguish `SOURCE_DECLARED`, `LOG_OBSERVED`, `INFERRED`, `PROFILE_ASSUMPTION`, `PROPOSED`, `UNKNOWN` and `CONTRADICTED`. Logs need attributable source/run bindings and substantiate only observed paths. Missing evidence is `UNKNOWN`, not automatically contradiction or independence.
4. Examine includes/macros, producer-consumer continuity, shared mutable state, side effects, DATA MERGE versus JOIN, duplicates/output multiplicity, filters, BY/tie/global order, RETAIN/sum/LAG queues, missing/numeric semantics and model fitting/scoring invariants. Flag omitted operations, unsupported schema/intent, changed invariants and unproved parallel safety.
5. Check capability/module coverage and as-is/to-be diagrams, HLD/LLD/ADRs and optimization scenarios. Challenge runtime fit/exclusion and cost arguments for native Python/PySpark/Ray/Dask; workload sizes or absent edges alone do not justify parallel benefit. Confirm optional Cython is justified, not automatic.
6. Check separate correctness/performance obligations and future human oracle/input/keys/tolerance/coverage choices. Keep the parity population menu only in `VALIDATION_PLAN.md`. Proposals/plans or synthetic expectations are not semantic parity, benchmark results, human approvals or host-testing evidence.
7. Check exact expected files and consistent authority/statuses: requirements/architecture `DRAFT`; semantic/parity/performance `NOT_RUN`; human approvals `NOT_APPROVED`. No imported runner, approved downstream config, production code or automatic runtime selection may be implied.

## Write REVIEW.md only

Include actual context/independence; source-integrity check results; files and source coverage checked; supported/contradicted/unknown claims; findings with priority, affected artifact/claim, F/O/D/U and original citations, consequence and suggested author correction; open human decisions; document readiness and next action. Preserve first-pass findings and dispositions if reviewing the single corrected author draft. Do not alter source facts, drafts, expected results, keys or tolerance, and do not write PROGRESS; return results to orchestrate for its append.

Use `READY_FOR_HUMAN_REVIEW` only for coherent complete documents, checked integrity, actual independent review and no blocking findings; use `PARTIAL` for useful unresolved/unchecked/unavailable-review drafts and `BLOCKED` for unsafe or unusable drafts. These are document readiness only, not self-certification or human approval.

Return fixes to the author: allow one author correction and genuinely fresh re-review. Factual corrections or source mutation require a new linked run. If that context is unavailable or issues remain, expose `PARTIAL`/`BLOCKED`; never repair to pass, loop indefinitely or authorize downstream execution/release.
