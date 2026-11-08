---
name: specify
description: Draft an evidence-linked PRD capability map and module contracts from recovered SAS behavior. Use after understand to separate source invariants, proposed improvements, and open human scope decisions.
---

# Specify capabilities and module boundaries

Follow repository `AGENTS.md`, `README.md`, `DESIGN.md` and `orchestrate` boundaries. Read current `SOURCE_EVIDENCE.md`, `PROGRESS.md` and authorized supplied business context. Cite F/O/D/U IDs and their original coordinates; never reconstruct a second factual graph or edit completed source facts.

## Draft PRD.md

1. State `DRAFT` requirements, document readiness, `NOT_APPROVED` human approvals, and semantic/parity/performance `NOT_RUN`. Explain the workload and intended outcome in team-readable language.
2. Separate user-supplied goals from inferred legacy capabilities. If intent is missing, label a candidate goal `INFERRED` and ask the human owner; source behavior is not approved business intent. Keep useful draft work moving without pretending scope is final.
3. Include scope/non-goals, stakeholders/ownership, candidate success criteria, constraints, assumptions, risks and open decisions. Label proposed changes `PROPOSED` and supplied planning assumptions `PROFILE_ASSUMPTION`; carry unknowns/contradictions without hiding them.
4. Include a capability map table: capability ID/name, source O/D references, current behavior/invariants, proposed improvement, affected U IDs, and candidate acceptance/proof obligation. Cover preparation, computation/modeling, dependencies and outputs as actually present; explain excluded/unread scope.
5. Separate preservation requirements from requested behavior changes. Do not silently change formulas, filters, event/category definitions, keys, duplicates, missing values, order/state or output contracts for optimization. Send material business-change questions to the human scope owner.

## Draft MODULES.md

Propose boundaries by capabilities and dependencies, not automatically one module per source file. For each proposed module record purpose, source capability/O/D/U references, inputs/outputs and known schemas/keys, invariants, algorithms at contract level, mutable state, ordering, side effects, error/unknown handling and inter-module dependencies. Mark unknown types/contracts explicitly rather than manufacturing schemas.

Identify reusable preparation, semantic boundaries and candidate parallel scenarios only conditionally. Preserve producer-consumer continuity and state/order/multiplicity constraints. An absent dependency edge or large dataset alone does not establish independence or benefit. Distinguish source facts from proposed boundaries; pass unresolved safety and cost questions to design.

## Deliver and continue

Write `PRD.md` (with capability map) and `MODULES.md` only in the current run. Return paths, readiness, open human scope decisions and design constraints for orchestrate's progress entry; auto-continue to design within host permissions. Do not approve requirements, choose a runtime, execute data, generate production code, or materialize downstream configs.

Keep oracle/input/keys/tolerance/coverage decisions for the future human-approved validation plan. Put the parity population choice menu only in `VALIDATION_PLAN.md`, not in these specifications. Recommendations never substitute for human selection; final scope, architecture, tolerance, execution and release remain human-owned.
