---
name: design
description: Draft optimization-led SAS modernization architecture, candidate ADRs, and separate correctness/performance plans. Use after specify to compare native Python, PySpark, Ray, and Dask without selecting or implementing a runtime.
---

# Design better implementation, preserving behavior

Follow repository `AGENTS.md`, `README.md`, `DESIGN.md` and `orchestrate` boundaries. Read sealed `SOURCE_EVIDENCE.md`, `PRD.md`, `MODULES.md`, progress and supplied constraints. Use [the short ADR template](templates/candidate-adr.md). Keep requirements/architecture `DRAFT`, runtime `NOT_SELECTED`, approvals `NOT_APPROVED`, and semantic/parity/performance checks `NOT_RUN`.

## Compare optimization scenarios

1. Recover source behavior/invariants first; propose better algorithms and execution structure, not line-by-line SAS translation. Consider shared scans/preparation, projections/filtering, materialization, joins/aggregation, group/state processing, modeling versus scoring and export coordination where evidence supports them.
2. Separate source-supported opportunities from inferred bottlenecks, profile assumptions and unmeasured performance hypotheses. Cite O/D/U IDs and preserve unknowns/contradictions. Do not fabricate cardinalities, measured costs, runtime results or speedups.
3. Compare native Python, PySpark, Ray and Dask explicitly in a compact table: candidate strategy, fit/conditional fit or reasoned exclusion, semantic risks, data locality/transfer, memory/materialization, scheduling/startup/shuffle overhead, failure/recovery and operational complexity, constraints, missing evidence and needed measurements. Use a sensible native baseline; do not mandate distributed execution. Consider optional Cython only for a justified CPU-hotspot hypothesis and acceptable complexity; never add it automatically.
4. For each proposed parallel scenario assess dependency completeness, producer-consumer versions, shared mutable state/resources, order/group continuity, side effects and output reconciliation. Explain isolation/partition strategy and correctness obligations, then coordination, serialization, memory, skew, I/O and recovery costs. Missing edges, large workloads or separate diagram branches are not proof of independence or net benefit. Keep unproved scenarios conditional.

## Write ARCHITECTURE.md and adrs/<decision>.md

Include a team-readable as-is workload and to-be proposal using valid Mermaid diagrams; annotate nodes/edges or adjacent mapping with O/D/U IDs and unresolved links. Retain dependency/state/order constraints; represent unresolved includes/macros honestly. Do not imply to-be choices are deployed.

Put HLD components, ownership, data flow and runtime comparison in `ARCHITECTURE.md`, plus concise LLD: operation/algorithm changes, partition/group/keys, ordering/ties, state resets, missing/multiplicity semantics, materialization, scheduling, failures and output contracts. Document preserved invariants, design limits and conditional recommendations. Write one or more short candidate `adrs/<decision>.md` using the template for material choices; reference the architecture rather than duplicate it. Recommendations remain unselected drafts.

## Write VALIDATION_PLAN.md

Keep correctness and performance proof obligations in separate sections; writing plans performs neither.

- **Correctness:** propose an independently attributable SAS oracle and input/version binding, comparison keys, numeric/character/date/missing semantics, order and multiplicity handling, tolerance rationale and coverage (branches, includes/macros, state boundaries, joins/models/outputs). Record every oracle/input/keys/tolerance/coverage choice as awaiting human approval; define evidence needed and unresolved blockers. Supplied observations are scoped evidence, not a parity pass.
- **Future parity population decision:** present `50 governed`, `FULL`, `PHASED50THENFULL`, or `custom` as human choices, only here. A governed sample needs selection rationale and coverage limits; no sample proves full-population parity. Make a conditional recommendation if supported, but leave selection `OPEN` for the user; do not run or configure it.
- **Performance:** propose a comparable baseline and candidates, representative workload/scale, resource/environment bindings, end-to-end and stage metrics, transfer/materialization costs, repeat strategy, warm/cold/cache treatment, skew/failure cases and acceptance hypotheses. Require correctness first; keep measurements `NOT_RUN` and any supplied historical measurements separately attributable. Workload size alone is not evidence of speedup.

## Deliver

Write `ARCHITECTURE.md`, `adrs/<decision>.md`, and `VALIDATION_PLAN.md` only in the current run; return paths, constraints and human decisions to orchestrate. Do not select a runtime, import a runner, generate scorers/jobs/production code, approved tie-out/deployment configs, cluster resources or downstream approvals. Human owners choose final scope, architecture, tolerance, execution and release; proceed to fresh review, not implementation.
