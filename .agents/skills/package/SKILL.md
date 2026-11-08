---
name: package
description: Assemble reviewed SAS draft artifacts into a one-page reading guide and explicit human handoff. Use after review or documented review unavailability, not downstream import, implementation, approval, or release.
---

# Package for human review

Follow repository `AGENTS.md`, `README.md`, `DESIGN.md` and `orchestrate` boundaries. Read actual current-run artifacts, `REVIEW.md` and `PROGRESS.md`; do not rely on promised outputs. Packaging creates readable documents, not an archive, parser graph, execution config or runner.

## Reconcile and check

1. Reconcile optional `SOURCE_MANIFEST.json`, `SOURCE_EVIDENCE.md`, `PRD.md` with capability map, `MODULES.md`, `ARCHITECTURE.md` with as-is/to-be Mermaid and HLD/LLD, actual `adrs/<decision>.md`, `VALIDATION_PLAN.md`, `REVIEW.md` and progress. Link actual paths; never invent absent files, checks, review or approvals. Keep reviewer findings visible; do not repair drafts while packaging.
2. Before package, check existing source identity using `python3 scripts/input_snapshot.py check --input <root> --manifest <run>/SOURCE_MANIFEST.json` if available. Record actual result, not an invented hash. On mutation preserve the old run and return to orchestrate for a new linked run; do not declare ready on stale evidence. Unavailable helper/manifest means `SOURCE_INTEGRITY: NOT_CHECKED` and at best `PARTIAL`.
3. Reconcile readiness across review/progress/handoff. Require complete coherent documents, checked source, actual independent fresh review and no blocking findings for `READY_FOR_HUMAN_REVIEW`. Use `PARTIAL` for useful unresolved drafts, unavailable independent review (`NOT_AVAILABLE`) or unchecked integrity; use `BLOCKED` when safe/meaningful use cannot proceed. These statuses concern documents only.

## Write START_HERE.md (one page)

Explain in plain language the workload, inspected coverage and limits, source behavior/invariants, proposed modules and optimization-led architecture choices, recommendation versus unselected decisions, and top unknowns/review findings. Give a short relative-link reading order through evidence, PRD/modules, architecture/ADRs, validation and review. State actual readiness, integrity, review context, what was not executed and the human next action. Keep it one page; refer detail to linked artifacts.

## Write HANDOFF.md

Record request, authorized input root, run ID and prior-run link/reason if any; actual source manifest/check result or `NOT_CHECKED`; evidence/requirements/architecture/ADR/validation/review links; author correction/re-review history and unresolved findings; conditional recommendations; human decision owners and next steps. Reference the validation plan for its future choices without duplicating its parity population menu. Preserve source F/O/D/U provenance; do not create a competing factual record.

State explicitly: requirements and architecture `DRAFT`; runtime `NOT_SELECTED`; semantic/parity/performance `NOT_RUN`; human approvals `NOT_APPROVED`. Attributed supplied log/measurement evidence is scoped historical evidence, not workflow execution or a parity pass. No workflow host-testing, migration success, imported runner, approved downstream config or production implementation is established by this package.

Explain the downstream obligations without performing them: human scope/architecture/tolerance decisions, fresh source verification, independently governed oracle/inputs/keys/coverage, implementation authorization, correctness checks, representative performance measurements, and execution/release approval. Human owners retain final scope, architecture, tolerance, execution and release. A recommendation or `READY_FOR_HUMAN_REVIEW` does not authorize any of these.

## Deliver and stop

Write only `START_HERE.md` and `HANDOFF.md` in this current fresh run. Return actual paths, readiness, integrity/review limits, open decisions and a copy-ready human-review request to orchestrate; it appends the final progress entry. Never change prior runs/input, auto-commit/push private files, select a runtime or invoke downstream migration/execution.
