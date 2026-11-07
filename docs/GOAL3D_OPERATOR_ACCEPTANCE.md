# GOAL-3D operator acceptance record

The configured MIG-2 operator run passed on a fresh public synthetic INTAKE at implementation commit `3baca6c1f9d9962bdac19652d0e36b80c2245dae`. The record covers discovery, scoped evidence, reviewed configuration, human approval, engineering publication and replay. [Operator guide](../examples/intg1/README.md)

| Step | Observed result |
| --- | --- |
| Inventory and scope | Discovered `01_project.sas` and `02_order.sas` and selected the proposed DATA and SORT scope. The synthetic `context.log` and `context.lst` were bound by identity as supporting context. |
| Evidence and plan | Generated the scoped review and both YAML drafts. The reviewed YAML selected local Python with exact public engineering comparisons. The planner returned `PLAN_PROPOSED` for MIG-2. |
| Before human approval | GATE-1 returned `REVIEW_REQUIRED` with zero blockers and `BOUND_HUMAN_APPROVAL_REQUIRED` as its sole pending item. The candidate destination was absent. |
| Approved continuation | Keshav explicitly approved the exact version 2 claim record below. A separate approval file bound that digest. GATE-1 returned `PASS` with zero blockers and zero pending items, then the continuation published the MIG-2 package. |
| Engineering tie-out | All four projected rows matched the public expectations. IDs were ordered `3, 3, 3, 9` with measurements `8.5, 6, 8.5, 2`. Equal-key input order and duplicate multiplicity were preserved. |
| Fresh replay | GATE-1 and the engineering comparison both returned `PASS`. All seven filenames and file bytes matched the first publication, including the manifest. The manifest matched the recorded hashes and sizes of all six payload files. |

The five review sections were authored directly for this operator run. The SAS reference obligation remains separate from the public engineering expectations.

| Artifact | SHA-256 |
| --- | --- |
| Scoped evidence manifest | `b594e77aa7a12ef91f765a668d2fc372812e2cc0ddfa4cf39310bbda302f19c1` |
| Reviewed migration profile | `774be387e28c08ba34f390a9c4fd1aeb4e8caee46b8486ce0520c17917a9bc99` |
| Reviewed tie-out | `ff4303cbd2fb858fbc04bb54b7fbc0159d73ecbf8975bef69bea67ddb075d4ed` |
| Proposed plan | `7eaf1bf7a062d8e37916dc95bfe56b17297334b44d053fec2c566a48292679eb` |
| Exact approved claim record | `5f9771129709ab9cd2b68dae446d685ed0f17093250a23b6b72ed2044ae7b049` |
| Separate approval file | `b8bc97a05501304f5fc79cc2e43cf7c497af26598fda69e8b65f1933d41155f0` |
| Public input and expected rows | `c135ac9d58d5222e45044c59d62ab4f68c18780ea88e6d3816afa1c9e4a602ca` |
| Publication and replay manifest | `e289cbff2f7651c682d3f58be1f58980bb7ff204a9b671dba201b5c262f6a00d` |

Both publications contained `MANIFEST.json`, `GATE.json`, `PLAN.json`, `MODERNIZATION_PLAN.json`, `ROWS.json`, `VALIDATION.json` and `ENGINEERING_TIE_OUT.json`. The run artifacts were retained in local scratch. This repository record preserves their identities and observed outcomes.

| Evidence status | Value |
| --- | --- |
| Artifact authority | DRAFT |
| Behavioral evidence | UNAVAILABLE |
| SAS reference execution | NOT_RUN |
| Semantic verification | UNVERIFIABLE |
| Semantic acceptance | BLOCKED |
| Benchmark execution | NOT_RUN |
| Historical SAS run provenance | UNBOUND |

## Pinned INTG-3 operator runs

Both pinned subjects used the configured MIG-5/MIG-6/MOD-2 route at implementation commit `3baca6c1f9d9962bdac19652d0e36b80c2245dae`. Each reviewed YAML pair produced `PLAN_PROPOSED`. Before approval, both GATE-1 receipts showed `REVIEW_REQUIRED` with zero blockers and `BOUND_HUMAN_APPROVAL_REQUIRED` as the sole pending item. Keshav then approved each exact version 2 claim record, and separate approval files bound the two digests. [Pinned operator guide](../examples/intg3a/README.md)

| Scenario | GATE-1 and engineering comparison | Candidate outcome | Replay |
| --- | --- | --- | --- |
| `passes` | Both PASS on publication and replay. | `PROCEED`. CSV IDs were `[0, 1]`. Fixed scoring retained pre-sort ID order `[1, 0]` and passed its numeric comparison. | All 18 filenames and file bytes matched, including the manifest. |
| `duplicates` | Both PASS on publication and replay. | Expected candidate `BLOCK` at gate 3. The publication contained diagnostics and their bindings. Export, sorted rows, design and scores were absent. | All 10 filenames and file bytes matched, including the manifest. |

| Bound artifact | `passes` SHA-256 | `duplicates` SHA-256 |
| --- | --- | --- |
| Pinned subject manifest | `f1159f3f397c640d867401d1be4e3eb2bd232dd2fdcf068247088847fb48f864` | `57fb8c0a4b2dec668f5363a48f120ebb5bb405c3ec9ecd39c8d6eefde2fbd477` |
| Exact approved claim record | `99b43c30cfde23007210467bda9c69ab42a2bf552ecc76275c0bcaa16765a851` | `85d12742a6580ff27a2ff7ea404ce5ec340d0aaa99f5bda04de2924f2cddcf95` |
| Publication and replay manifest | `d9fd82381568e6a261f181af390ad639a5752ab9289fd56b0a275b74d609373b` | `0849473180bf13953c6f80baeb613c339326aa4ed06cdfcbdb502e36a95a7c98` |

The publications and receipts were retained in local scratch. Both runs recorded SAS reference execution as `NOT_RUN`, semantic verification as `UNVERIFIABLE` and semantic acceptance as `BLOCKED`.

## Live GitHub Copilot Agent run

A fresh public synthetic INTAKE produced a configured MIG-2 proposal. The
VS Code Copilot Agent session showed reads of all five local skills and
wrote one draft with five deliverables and 16 proposed claims. The source
and evidence copies, plan, reviewed YAML and public row fixture matched
the operator inputs byte for byte. [Operator guide](../examples/intg1/README.md)

| Skill | Captured deliverable |
| --- | --- |
| `sas-reconstruct` | DATA input, output and projection, SORT input, output and ascending key, and unresolved runtime order and dataset version. |
| `sas-specify` | Local Python MIG-2 requirements for projection, ascending order, stable ties and duplicate multiplicity, with the four expected public rows. |
| `sas-analyze` | A potential handoff through `work.live_stage`, with runtime execution order and dataset continuity unresolved. |
| `sas-validate` | Source declaration checks, exact public row comparison, and independent SAS reference obligations. |
| `sas-architect` | A bounded local Python ADR, with distributed alternatives deferred pending workload and benchmark evidence. |

The version 2 record assembled from the raw Copilot draft returned
`BLOCK`. GATE-1 reported 45 unresolved evidence references and seven
classification conflicts. The draft used workspace prefixes, cited
plan, YAML and row files outside the gate's evidence set, and grouped
declarations across source files.

The operator preserved the raw draft and prepared a separate corrected
record. It uses package-relative citations, separates declarations by
source, and retains candidate policy and public expectations in review
prose. The corrected record returned `REVIEW_REQUIRED` with zero
blockers and only `BOUND_HUMAN_APPROVAL_REQUIRED` pending. Keshav then
approved its exact SHA-256 in a separate approval record.

GATE-1 returned `PASS` on publication and replay. MIG-2 matched all four
public expected rows, including duplicate multiplicity and stable ties.
The fresh replay matched all seven filenames and file bytes, including
the manifest. SAS reference execution was `NOT_RUN`, semantic
verification was `UNVERIFIABLE` and semantic acceptance was `BLOCKED`.

| Retained artifact | SHA-256 |
| --- | --- |
| Raw Copilot draft | `fd484db2f755072a2cc14edd7fdda256673b1926c24ec7457dfbe72c6c096054` |
| Claim record blocked by GATE-1 | `4c37fe563b8d922a513956ce4e7fae0a0739a0f7605cf9458b1616887732a6bf` |
| Corrected and approved claim record | `9df69114e53cb23ef7a56ba1b2961f1221d4858bc04b01c15f7de75cb7c76aee` |
| Separate approval | `8dd3d4f3a3b41c22be374706eb972045a356b15d46dda4a29078587e660b08f6` |
| Proposed modernization plan | `bfd2e86ec8953ff9e4fd9b68815718b0bb5fd01670985d26bf4e2e143b745ed1` |
| Publication and replay manifest | `9adfcf573f0d7991bb83290f4baa70f97a270de409f98cba1cb112a2dc72f703` |

The exact drafts, approval, gate receipts and publications were retained in local scratch.
