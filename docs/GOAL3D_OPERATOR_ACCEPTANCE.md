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
