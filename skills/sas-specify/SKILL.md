---
name: sas-specify
description: Review the draft PRD and module specifications for the fixed synthetic SAS workflow. Use to trace requirements to source evidence, find unsupported business claims, and identify questions for an owner.
---

Work from one output of [review_workflow.py](../../scripts/review_workflow.py) or the [checked-in example](../../examples/offline-review/README.md). Use the [manifest](../../examples/offline-review/MANIFEST.json) to identify the subject and files. The engine's [generate_preview](../../src/sas_re/_draft_preview.py) already produces the drafts. Make review notes separately.

For a fresh run, read every named document from that output directory. Links below locate the checked-in example.

1. Read [EVIDENCE.md](../../examples/offline-review/EVIDENCE.md), then [PRD.md](../../examples/offline-review/PRD.md) and [MODULES.md](../../examples/offline-review/MODULES.md). Follow each material requirement back to its operation or edge, canonical ID, module owner, fact index where available, and original file/line/byte span. State what a candidate could be tested against.
2. Classify each claim. **OBSERVATION** describes what the supplied graph records. **INFERENCE** interprets a represented relationship and retains the record's original classification. **ASSUMPTION** names something an owner or independent reference must confirm. **HYPOTHESIS** proposes a requirement or design to test. Reserve **MEASUREMENT** for attributable execution evidence.
3. Challenge the draft at the handoff. The intermediate uses `batch, sequence`; O3 fact 1 projects only `batch, adjusted` with ORDER BY `batch`. A final acceptance test that requires `sequence` has lost its source basis. Ask the owner about the business purpose, accepted population, duplicate and tie policies, and numerical tolerance. Keep unanswered questions open.
4. Return findings with the disputed wording, classification, cited evidence, and proposed correction or owner question. For architecture review, identify the invariant both alternatives must preserve and the evidence still needed.

Stop on a mixed subject or missing evidence reference. Mark a claimed source behavior without a supporting span or record as unsupported. Keep proposed requirements labeled as hypotheses and owner questions open. O4's missing include leaves complete semantics UNVERIFIABLE and acceptance BLOCKED. Do not infer approved business intent, rewrite sealed evidence, run private inputs or send findings [downstream](../../docs/COMPATIBILITY.md). Native Windows evidence I/O remains BLOCKED. Document inspection uses the existing public package.

```text
artifact_authority: DRAFT
semantic_verification: UNVERIFIABLE
semantic_acceptance: BLOCKED
benchmark_execution: NOT_RUN
```
