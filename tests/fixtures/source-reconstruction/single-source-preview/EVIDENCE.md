# Evidence and uncertainty

UNVERIFIED · public synthetic draft

```text
artifact_authority: DRAFT
semantic_verification: UNVERIFIABLE
semantic_acceptance: BLOCKED
benchmark_execution: NOT_RUN
```

Graph SHA-256 `385423530208b08635de832bed57698b7278490f2cb7a43f08fd754b80df9155` · preview `mvp1-draft-preview/1` · diagnostics `p3-a1-dependency-diagnostics/1`

## Subject and reading key

**OBSERVATION** Workspace `public-workspace`, run `public-run`, attempt `reconstruct-1`. Source fingerprint `c94ab61f4f4f84f885079f7d71aa71c98a4b7118d21c2eb92d4d26b3cbf4ccb4`. Scope manifest `d293f44991c5b8bab566167f892620e42f1d545d236fbe478e50d225460947e2`, profile SHA-256 `cbbfa402fc87e1c66467d8dd32e649ed92d3123c047c47b30cbceed0af27c7f6`. Diagnostic result SHA-256 `1324fd7c9c0f62178277928290887ed91d64db9c0a6ee40961b0725f732b678e`.

OBSERVATION reports what the supplied graph contains. INFERENCE interprets a represented relationship. ASSUMPTION needs outside confirmation. HYPOTHESIS is a proposal to test. MEASUREMENT requires observed execution evidence. No performance measurement is asserted.

O and E labels are local links. Persistent identities and zero-based fact indexes below resolve in the graph identified by the digest above. Spans use original byte offsets, exclusive end offsets and inclusive line numbers. A synthesized fact can point at one statement (for example a BY clause); use the enclosing operation span to locate the declaration and check the fact in context.

## Operation register

### O1

**OBSERVATION** `op_5a103e45a5799e048c110e798ffc94c9a7883c49b1dfb41c576d61d8c5a49967`, PROC_SORT, module `main`, canonical classification `INFERENCE`. `synthetic:main.sas` lines 2–4, bytes [48, 106). Source SHA-256 `8b29a37635780d63c87111c0856c380334cd6915c749865ef19e61ed058eeaf6`, span SHA-256 `7198058e49aaf58b3318f53d669d779a11c2b4f07dbd10edec68abe325f5f84a`, cited excerpt SHA-256 `bf17137bc5c29a91382a51375d408591d9540abff203d7a6d82ac16f0f3c8315`.

Read nodes: `col_18f501971aa7841dc2041d4b171795dcca11a94bb8860da19abcc195e4892f13`, `col_272814c17592785a19ed9cd576caa7ce2cf586f71163d192c64351e63109a521`, `col_cbcfc5bc700a2434cd8a9595d47028d69736cf698edae6f1eb425fa869dec0e6`, `ds_7184649b565a432853148f46efee450a106ea50e32e3f5bd8d03d584dab7c066`.
Write nodes: `col_22fa87668b97e7dea1c348c63ba60e83962cf1d8bc403be3fa493678f4d05d24`, `col_3a552c34a9955d7309eab42b09c61f6c2079bddd7baf5e52d331e4eafe369cfb`, `col_ad3eb6c6d645652d2a4efe16ec75b1c1c87a701f51840e2aa4cbf06b11c5fe59`, `ds_9af942e625f54a89c061b1d7aa131d517139604c36c5faf6ef699c42275edb9d`.

- **OBSERVATION** Fact 0 · `sort` · `synthetic:main.sas` lines 3–3, bytes [87, 101). Source SHA-256 `8b29a37635780d63c87111c0856c380334cd6915c749865ef19e61ed058eeaf6`, span SHA-256 `5fd557befb65777752300dd1858a24c6429b9a915458756358d710422fd41e84`, cited excerpt SHA-256 `06cdd8c83d8c62d531a83fe5acba78b78a46d3c73fdb4c2cc5ea4fd834e49ebb`.

### O2

**OBSERVATION** `op_9bf118c17f499bd241dec1876218ea338cc98514f2a5f4bf484b6e515c40f9bc`, DATA_STEP, module `main`, canonical classification `INFERENCE`. `synthetic:main.sas` lines 5–9, bytes [107, 171). Source SHA-256 `8b29a37635780d63c87111c0856c380334cd6915c749865ef19e61ed058eeaf6`, span SHA-256 `fb0b79a7811ea18eb927f9f0f096f32899017f1fdcc715f98786c1a43aceb4d7`, cited excerpt SHA-256 `468deb064b07889fe7cefbc9fba4b09d62fc638abc77655ec186f9bd5d1f1207`.

Read nodes: `col_22fa87668b97e7dea1c348c63ba60e83962cf1d8bc403be3fa493678f4d05d24`, `col_3a552c34a9955d7309eab42b09c61f6c2079bddd7baf5e52d331e4eafe369cfb`, `col_ad3eb6c6d645652d2a4efe16ec75b1c1c87a701f51840e2aa4cbf06b11c5fe59`, `ds_9af942e625f54a89c061b1d7aa131d517139604c36c5faf6ef699c42275edb9d`.
Write nodes: `col_930c3fb1c0ce33f8ff3ffa5bd41e6134ad08cc172936b27114aee341ebb5aa56`, `col_9c50784cc77b5f5ef1632a2d98c302124465f234bdc40703813028c2b0ec0ee0`, `col_dde4c3114f37cd8c3e19cde6ce31d57150e237dc94dd7beab9438d22ebcbb697`, `col_ed22b73a3cd4ac3038cff9a8db85705152f39e5d50c0a91b0bee9d7af0cbe139`, `ds_7852ec930d61e80d9a153f6e3f21ba6311d569be4f2cef7f1f06c823a91d599c`.

- **OBSERVATION** Fact 0 · `output` · `synthetic:main.sas` lines 5–5, bytes [107, 123). Source SHA-256 `8b29a37635780d63c87111c0856c380334cd6915c749865ef19e61ed058eeaf6`, span SHA-256 `7029eef8239a4e72d1ddef0cc6547d8f4230195d343923d6218e37772ae6eb56`, cited excerpt SHA-256 `2fcf0a26b956f81e5e9574c3ee248d203ced01018b71360f4c078c21cb02d375`.
- **OBSERVATION** Fact 1 · `input` · `synthetic:main.sas` lines 6–6, bytes [124, 139). Source SHA-256 `8b29a37635780d63c87111c0856c380334cd6915c749865ef19e61ed058eeaf6`, span SHA-256 `44df233bfd7738c5c19be54a218a42ce95720415bae87821a45dca723817aecf`, cited excerpt SHA-256 `32b07d9d3dd49489753e41da2cd2b0f523f0914b0477ce950d4bbf62debd0950`.
- **OBSERVATION** Fact 2 · `by` · `synthetic:main.sas` lines 7–7, bytes [141, 154). Source SHA-256 `8b29a37635780d63c87111c0856c380334cd6915c749865ef19e61ed058eeaf6`, span SHA-256 `bc885d5e3ef1c8516908b8b639c07d74c3a42f59399c5c1a75371ae7ba64c546`, cited excerpt SHA-256 `06cdd8c83d8c62d531a83fe5acba78b78a46d3c73fdb4c2cc5ea4fd834e49ebb`.
- **OBSERVATION** Fact 3 · `assignment` · `synthetic:main.sas` lines 8–8, bytes [156, 165). Source SHA-256 `8b29a37635780d63c87111c0856c380334cd6915c749865ef19e61ed058eeaf6`, span SHA-256 `b1eb894fdcfed9d2cfa04907b89bbea8326725b51769536193785a75d933d541`, cited excerpt SHA-256 `8cc2b07685511e415bef3977746908e10e0fee538ba67565f03aef306700b062`.

## Edge register

### E1

**OBSERVATION** `edge_1328f3e60d6e3fd8b52f05b1aad12d7bd371fcca3eb8b816d7d5118be3fc9115`, STATE, [O2](EVIDENCE.md#o2) → [O2](EVIDENCE.md#o2). Canonical classification `INFERENCE`. Original evidence operations: [O2](EVIDENCE.md#o2).

Linked nodes: `col_930c3fb1c0ce33f8ff3ffa5bd41e6134ad08cc172936b27114aee341ebb5aa56`, `col_9c50784cc77b5f5ef1632a2d98c302124465f234bdc40703813028c2b0ec0ee0`, `col_dde4c3114f37cd8c3e19cde6ce31d57150e237dc94dd7beab9438d22ebcbb697`, `col_ed22b73a3cd4ac3038cff9a8db85705152f39e5d50c0a91b0bee9d7af0cbe139`, `ds_7852ec930d61e80d9a153f6e3f21ba6311d569be4f2cef7f1f06c823a91d599c`.

### E2

**OBSERVATION** `edge_293748bf8ef10ff7144cac2b18068a2ef8ca407faab6da2d151172d9b3643653`, ORDER, [O1](EVIDENCE.md#o1) → [O2](EVIDENCE.md#o2). Canonical classification `INFERENCE`. Original evidence operations: [O1](EVIDENCE.md#o1), [O2](EVIDENCE.md#o2).

Linked nodes: `col_22fa87668b97e7dea1c348c63ba60e83962cf1d8bc403be3fa493678f4d05d24`, `col_3a552c34a9955d7309eab42b09c61f6c2079bddd7baf5e52d331e4eafe369cfb`, `col_ad3eb6c6d645652d2a4efe16ec75b1c1c87a701f51840e2aa4cbf06b11c5fe59`, `ds_9af942e625f54a89c061b1d7aa131d517139604c36c5faf6ef699c42275edb9d`.

### E3

**OBSERVATION** `edge_7c1804b6f4da231e354b05eb3db39c843911dd82c99583e3499e862e983ffdd2`, DATA, [O1](EVIDENCE.md#o1) → [O2](EVIDENCE.md#o2). Canonical classification `INFERENCE`. Original evidence operations: [O1](EVIDENCE.md#o1), [O2](EVIDENCE.md#o2).

Linked nodes: `col_22fa87668b97e7dea1c348c63ba60e83962cf1d8bc403be3fa493678f4d05d24`, `col_3a552c34a9955d7309eab42b09c61f6c2079bddd7baf5e52d331e4eafe369cfb`, `col_ad3eb6c6d645652d2a4efe16ec75b1c1c87a701f51840e2aa4cbf06b11c5fe59`, `ds_9af942e625f54a89c061b1d7aa131d517139604c36c5faf6ef699c42275edb9d`.

## Node register

**OBSERVATION** Original graph identifiers, logical names and owners.

| Logical node | Owner | Canonical ID |
|---|---|---|
| `work.a` | `main` | `ds_7184649b565a432853148f46efee450a106ea50e32e3f5bd8d03d584dab7c066` |
| `work.sorted` | `main` | `ds_9af942e625f54a89c061b1d7aa131d517139604c36c5faf6ef699c42275edb9d` |
| `work.final` | `main` | `ds_7852ec930d61e80d9a153f6e3f21ba6311d569be4f2cef7f1f06c823a91d599c` |
| `work.a.key` | `main` | `col_18f501971aa7841dc2041d4b171795dcca11a94bb8860da19abcc195e4892f13` |
| `work.a.subkey` | `main` | `col_272814c17592785a19ed9cd576caa7ce2cf586f71163d192c64351e63109a521` |
| `work.a.x` | `main` | `col_cbcfc5bc700a2434cd8a9595d47028d69736cf698edae6f1eb425fa869dec0e6` |
| `work.sorted.key` | `main` | `col_3a552c34a9955d7309eab42b09c61f6c2079bddd7baf5e52d331e4eafe369cfb` |
| `work.sorted.subkey` | `main` | `col_ad3eb6c6d645652d2a4efe16ec75b1c1c87a701f51840e2aa4cbf06b11c5fe59` |
| `work.sorted.x` | `main` | `col_22fa87668b97e7dea1c348c63ba60e83962cf1d8bc403be3fa493678f4d05d24` |
| `work.final.key` | `main` | `col_dde4c3114f37cd8c3e19cde6ce31d57150e237dc94dd7beab9438d22ebcbb697` |
| `work.final.subkey` | `main` | `col_ed22b73a3cd4ac3038cff9a8db85705152f39e5d50c0a91b0bee9d7af0cbe139` |
| `work.final.x` | `main` | `col_9c50784cc77b5f5ef1632a2d98c302124465f234bdc40703813028c2b0ec0ee0` |
| `work.final.y` | `main` | `col_930c3fb1c0ce33f8ff3ffa5bd41e6134ad08cc172936b27114aee341ebb5aa56` |

## Proof obligations

**OBSERVATION** 0 LOG/LST observation record(s) in the supplied graph. Diagnostic eligibility `BLOCKED`.

**INFERENCE** The following obligations come from the recomputed P3-A1 diagnostic.

- `EFFECT_COMPLETENESS_UNPROVED` (graph-wide): Independently establish source semantics and completeness of reads, writes, external effects and unresolved dependencies for this scope.
- `ORDER_PRECONDITION` ([O1](EVIDENCE.md#o1)): Establish the declared input/order/key requirements for every affected row.
- `TIE_ORDER_UNSPECIFIED` ([O1](EVIDENCE.md#o1)): Prove equal-key ordering is immaterial or supply the required tie order.
- `CARDINALITY` ([O1](EVIDENCE.md#o1)): Prove row multiplicity and selection under the declared cardinality rule.
- `NUMERIC_EQUIVALENCE_UNPROVED` ([O1](EVIDENCE.md#o1)): Preserve expression order, missing-value and numeric policies; runtime equivalence and numerical invariants have not been demonstrated.
- `STATE_CONTINUITY` ([O2](EVIDENCE.md#o2)): Prove initialization, reset, call order and state carried across rows/groups.
- `ORDER_PRECONDITION` ([O2](EVIDENCE.md#o2)): Establish the declared input/order/key requirements for every affected row.
- `TIE_ORDER_UNSPECIFIED` ([O2](EVIDENCE.md#o2)): Prove equal-key ordering is immaterial or supply the required tie order.
- `CARDINALITY` ([O2](EVIDENCE.md#o2)): Prove row multiplicity and selection under the declared cardinality rule.
- `NUMERIC_EQUIVALENCE_UNPROVED` ([O2](EVIDENCE.md#o2)): Preserve expression order, missing-value and numeric policies; runtime equivalence and numerical invariants have not been demonstrated.

**ASSUMPTION** Independent review must establish original scope, effects and source semantics. Dataset identities alone do not establish physical versions or safe partitioning. Caller-supplied comments and issue prose have no decision authority.
