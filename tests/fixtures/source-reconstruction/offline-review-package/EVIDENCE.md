# Evidence and uncertainty

UNVERIFIED · public synthetic draft

```text
artifact_authority: DRAFT
semantic_verification: UNVERIFIABLE
semantic_acceptance: BLOCKED
benchmark_execution: NOT_RUN
```

Graph SHA-256 `19f41dea50825469a89d8fc545fee1d87f09af946d130d62de8f946d90b78017` · preview `mvp2-multimodule-preview/1` · diagnostics `p3-a1-dependency-diagnostics/1`

## Subject and reading key

**OBSERVATION** Workspace `mvp2-public-workspace`, run `ordered-measurements`, attempt `preview-2`. Source fingerprint `7517a3f1d064af2c15eb4bb0f3671659b4ea9b5acb9c39125dd9fb973a0a5d46`. Scope manifest `3bad52035b88cb4e827027f80cb0d7617dfb0e04414c91f111faf91bfe7354d0`, profile SHA-256 `5f70d3ecd6903e29ef8abc861c2d75f78b4a620f506db30e2aab14d2d53b0b50`. Diagnostic result SHA-256 `cdfdd753bdfbc2f9a6fd24e3eee2b3270d157db754203c8f89e976617a87f3dd`.

OBSERVATION reports what the supplied graph contains. INFERENCE interprets a represented relationship. ASSUMPTION needs outside confirmation. HYPOTHESIS is a proposal to test. MEASUREMENT requires observed execution evidence. No performance measurement is asserted.

O and E labels are local links. Persistent identities and zero-based fact indexes below resolve in the graph identified by the digest above. Spans use original byte offsets, exclusive end offsets and inclusive line numbers. A synthesized fact can point at one statement (for example a BY clause); use the enclosing operation span to locate the declaration and check the fact in context.

## Operation register

### O1

**OBSERVATION** `op_07c37f6f9837d33a0732a2833016eae57a3df1a36951b81dd31d6f44882d312b`, PROC_SORT, module `prepare`, canonical classification `INFERENCE`. `synthetic:prepare.sas` lines 2–4, bytes [48, 122). Source SHA-256 `1bc144d5ace53f06f765720a22d1ee2671cbcb13d5c1c2725cf34f8a8361e507`, span SHA-256 `62abf14ebc80e0a8828141cb31bd92358c1765a3046fd87f1f40b4f82fb30224`, cited excerpt SHA-256 `d82cbfc9a9bab6d325678608df8b282a2d559ef5f38d39313df4508bf349fc2a`.

Read nodes: `col_73abad849885c65a8a5045e739e417dab76cd72083b6d3e98754a067317a963f`, `col_7fdfb68c55c97a593688de1f04874967621429b9452ec3913827ba672776a96b`, `col_ddc94290372cb75523f6ec283c24b2042f06510508cad299abfbf287d5664875`, `ds_b8093cf48fba188be7368a104284b37c48705efe6f4ae52b529aa114e59dd505`.
Write nodes: `col_0a8275f0568073887c5934a876e4571449a5afe6bdc09e8f7890b0a99eabfe23`, `col_1c68c1a9a27d85d503335d4102e38567fbb832450b3712d5dd962fb0b0f953b5`, `col_59d578b12fb78c1533e356b66f8ee6dbb0926f8309165547a6f5382e48947c1a`, `ds_ef1c9b98adbe650219aed22c32ef2d874388ae1ec5260c21914591a9c072a2b9`.

#### O1 fact 0

**OBSERVATION** [O1](EVIDENCE.md#o1) · `sort` · `synthetic:prepare.sas` lines 3–3, bytes [99, 117). Source SHA-256 `1bc144d5ace53f06f765720a22d1ee2671cbcb13d5c1c2725cf34f8a8361e507`, span SHA-256 `d1b35d429409e9dd00a30e11744c89e3652cbfefb527fbec062fc1076d785788`, cited excerpt SHA-256 `4bd6a9bbef87718b423692988abed3436ef08b845901f980cbcab8559037c8e8`.


### O2

**OBSERVATION** `op_fb9dc21671be26fbd10babe8f2597c4afa6d9b4b44368e392cd4bf2f8052241b`, DATA_STEP, module `enrich`, canonical classification `INFERENCE`. `synthetic:enrich.sas` lines 2–6, bytes [48, 127). Source SHA-256 `09bae8bbb5c2b68e47801dbc865cd07b21f4953cec24ebcee043bcfea696ba91`, span SHA-256 `701eba38f5c0477f838b0be081504e5dbaebd9c3ca919bb40f3923fd50b11ad9`, cited excerpt SHA-256 `9debe9f76f181d53db36e3c69898362a86129b677def10dc7e3b140f6dceed07`.

Read nodes: `col_0a8275f0568073887c5934a876e4571449a5afe6bdc09e8f7890b0a99eabfe23`, `col_1c68c1a9a27d85d503335d4102e38567fbb832450b3712d5dd962fb0b0f953b5`, `col_59d578b12fb78c1533e356b66f8ee6dbb0926f8309165547a6f5382e48947c1a`, `ds_ef1c9b98adbe650219aed22c32ef2d874388ae1ec5260c21914591a9c072a2b9`.
Write nodes: `col_431505728a66f48397d2c9583dc5814f953a078278c50d2546bc4aea6a4de4d9`, `col_63ea1d340efaaa7f6a1a50a023936cc583fc69436d7f1bfa79ee3c9918d1e842`, `col_ba2b3bc2eb40c414fd001eb90a4407affaa70b9efee164da12a928332e3b165d`, `col_bedc24b3e81e8b81df467ab1622105a1777be189867e2c289fdbaa7fd30b1522`, `ds_18f6ab02a0b63d4495c97179d3a9864e1e27e71d02a1caaa820986301782f13f`.

#### O2 fact 0

**OBSERVATION** [O2](EVIDENCE.md#o2) · `output` · `synthetic:enrich.sas` lines 2–2, bytes [48, 65). Source SHA-256 `09bae8bbb5c2b68e47801dbc865cd07b21f4953cec24ebcee043bcfea696ba91`, span SHA-256 `b2c79a8d25099af333ddf13c646e15f168f848e90ec7e8087530651a051e3095`, cited excerpt SHA-256 `30c49a75b9fe09c6693571b0550eed82424da9530c99912f2b7593318c9d404f`.

#### O2 fact 1

**OBSERVATION** [O2](EVIDENCE.md#o2) · `input` · `synthetic:enrich.sas` lines 3–3, bytes [66, 82). Source SHA-256 `09bae8bbb5c2b68e47801dbc865cd07b21f4953cec24ebcee043bcfea696ba91`, span SHA-256 `6a4a9fbee6a27e2c152b5b7ab492613dbb20781f0327f933b5f96be1f8e88d59`, cited excerpt SHA-256 `31c77c850dd630999e3293c2ebb25baaa964acd9d016e7dff4a7553e2c347cbb`.

#### O2 fact 2

**OBSERVATION** [O2](EVIDENCE.md#o2) · `by` · `synthetic:enrich.sas` lines 4–4, bytes [84, 101). Source SHA-256 `09bae8bbb5c2b68e47801dbc865cd07b21f4953cec24ebcee043bcfea696ba91`, span SHA-256 `9e8dfc560f67468bfa10e17091a1b06640abb261724b6c5ab82a697080bc9de3`, cited excerpt SHA-256 `4bd6a9bbef87718b423692988abed3436ef08b845901f980cbcab8559037c8e8`.

#### O2 fact 3

**OBSERVATION** [O2](EVIDENCE.md#o2) · `assignment` · `synthetic:enrich.sas` lines 5–5, bytes [103, 121). Source SHA-256 `09bae8bbb5c2b68e47801dbc865cd07b21f4953cec24ebcee043bcfea696ba91`, span SHA-256 `e4bbaf14c3f892ecd2f6de5b4791f76124449f4607107b815c8285945ed00855`, cited excerpt SHA-256 `843bcd2efa81b374caac2764dcd5ba8fa3dd329cebfb0dcaa98f086e65c2742e`.


### O3

**OBSERVATION** `op_01e89ebcb947f473544c71da20e7656cf1334a60916b3d988947e6e62a2eb4c0`, PROC_SQL, module `enrich`, canonical classification `INFERENCE`. `synthetic:enrich.sas` lines 7–13, bytes [128, 337). Source SHA-256 `09bae8bbb5c2b68e47801dbc865cd07b21f4953cec24ebcee043bcfea696ba91`, span SHA-256 `b0540007cf2c78c4299d2228c30618a29645d95832eefa65be90592d9d2804b1`, cited excerpt SHA-256 `7b44fb2be61df8e347cb1758e5e03c0ca52cb9926479c2d3ea7f76384db94fa1`.

Read nodes: `col_431505728a66f48397d2c9583dc5814f953a078278c50d2546bc4aea6a4de4d9`, `col_53ce6d65bb65f98fa7839cd9f46f62953b2324f224ed617960d1f672bf510aab`, `col_63ea1d340efaaa7f6a1a50a023936cc583fc69436d7f1bfa79ee3c9918d1e842`, `col_ba2b3bc2eb40c414fd001eb90a4407affaa70b9efee164da12a928332e3b165d`, `col_bedc24b3e81e8b81df467ab1622105a1777be189867e2c289fdbaa7fd30b1522`, `col_e0d7af860d928e7202679e8c363b0766a644c17bd9dffc2930bbccfeb132b115`, `ds_18f6ab02a0b63d4495c97179d3a9864e1e27e71d02a1caaa820986301782f13f`, `ds_7cade8c245955293331351748d52fd74adbb8a510d9df056dd80096c19962730`.
Write nodes: `col_00abfae1f0f6c2da47f52de9cfcbc95a8a9e923f0cbc88edb6355f469ea8d5b0`, `col_dfde016fe5c0b703a41b57d1b5042d8b183b2740a481659f6027ce106a1bf81a`, `ds_409d5a037b977693af1ad803ca7cbf6f5ec25794de7a6868d35882ed67ab4800`.

#### O3 fact 0

**OBSERVATION** [O3](EVIDENCE.md#o3) · `output` · `synthetic:enrich.sas` lines 8–12, bytes [138, 330). Source SHA-256 `09bae8bbb5c2b68e47801dbc865cd07b21f4953cec24ebcee043bcfea696ba91`, span SHA-256 `1d6ea000a505996ac68d4c9b357665b71d088f0569e427bcf7b7b5362511204e`, cited excerpt SHA-256 `7a94cadd56a5b7486fb3cb90d6a6563ef4c9ad0366c6395afe011df6b4312544`.

#### O3 fact 1

**OBSERVATION** [O3](EVIDENCE.md#o3) · `sql` · `synthetic:enrich.sas` lines 8–12, bytes [138, 330). Source SHA-256 `09bae8bbb5c2b68e47801dbc865cd07b21f4953cec24ebcee043bcfea696ba91`, span SHA-256 `1d6ea000a505996ac68d4c9b357665b71d088f0569e427bcf7b7b5362511204e`, cited excerpt SHA-256 `7a94cadd56a5b7486fb3cb90d6a6563ef4c9ad0366c6395afe011df6b4312544`.


### O4

**OBSERVATION** `op_ef3d074f8fd0f8f92c4c280b0ff9ca79ba42cc99a6513d4a191c634a28ab9c57`, INCLUDE, module `enrich`, canonical classification `INFERENCE`. `synthetic:enrich.sas` lines 14–14, bytes [338, 363). Source SHA-256 `09bae8bbb5c2b68e47801dbc865cd07b21f4953cec24ebcee043bcfea696ba91`, span SHA-256 `36aaf6b81c2698d495fc1ff9f8663c7a57260dcb7061e488b1dac33fadf48de0`, cited excerpt SHA-256 `c4b4e8dc98993557cb288ac997d0d02fcb7e8397d48564260c0c32797ebe1474`.

Read nodes: none listed.
Write nodes: none listed.

#### O4 fact 0

**OBSERVATION** [O4](EVIDENCE.md#o4) · `include` · `synthetic:enrich.sas` lines 14–14, bytes [338, 363). Source SHA-256 `09bae8bbb5c2b68e47801dbc865cd07b21f4953cec24ebcee043bcfea696ba91`, span SHA-256 `36aaf6b81c2698d495fc1ff9f8663c7a57260dcb7061e488b1dac33fadf48de0`, cited excerpt SHA-256 `c4b4e8dc98993557cb288ac997d0d02fcb7e8397d48564260c0c32797ebe1474`.


## Edge register

### E1

**OBSERVATION** `edge_2a479e2228a6699322404618564ecb9080cb5d3dfce78ec4d2686fc4f47d0b9c`, DATA, [O2](EVIDENCE.md#o2) → [O3](EVIDENCE.md#o3). Canonical classification `INFERENCE`. Original evidence operations: [O3](EVIDENCE.md#o3), [O2](EVIDENCE.md#o2).

Linked nodes: `col_431505728a66f48397d2c9583dc5814f953a078278c50d2546bc4aea6a4de4d9`, `col_63ea1d340efaaa7f6a1a50a023936cc583fc69436d7f1bfa79ee3c9918d1e842`, `col_ba2b3bc2eb40c414fd001eb90a4407affaa70b9efee164da12a928332e3b165d`, `col_bedc24b3e81e8b81df467ab1622105a1777be189867e2c289fdbaa7fd30b1522`, `ds_18f6ab02a0b63d4495c97179d3a9864e1e27e71d02a1caaa820986301782f13f`.

### E2

**OBSERVATION** `edge_95d539e493b79759f154a9233716b3bf0a3eb5be30cb58c4c11f37c5040ac1b1`, ORDER, [O1](EVIDENCE.md#o1) → [O2](EVIDENCE.md#o2). Canonical classification `INFERENCE`. Original evidence operations: [O1](EVIDENCE.md#o1), [O2](EVIDENCE.md#o2).

Linked nodes: `col_0a8275f0568073887c5934a876e4571449a5afe6bdc09e8f7890b0a99eabfe23`, `col_1c68c1a9a27d85d503335d4102e38567fbb832450b3712d5dd962fb0b0f953b5`, `col_59d578b12fb78c1533e356b66f8ee6dbb0926f8309165547a6f5382e48947c1a`, `ds_ef1c9b98adbe650219aed22c32ef2d874388ae1ec5260c21914591a9c072a2b9`.

### E3

**OBSERVATION** `edge_9dd53b855a4cc38ff35ed31ef57d8b269c2977d87bf413714227d4a8c6bd2197`, STATE, [O2](EVIDENCE.md#o2) → [O2](EVIDENCE.md#o2). Canonical classification `INFERENCE`. Original evidence operations: [O2](EVIDENCE.md#o2).

Linked nodes: `col_431505728a66f48397d2c9583dc5814f953a078278c50d2546bc4aea6a4de4d9`, `col_63ea1d340efaaa7f6a1a50a023936cc583fc69436d7f1bfa79ee3c9918d1e842`, `col_ba2b3bc2eb40c414fd001eb90a4407affaa70b9efee164da12a928332e3b165d`, `col_bedc24b3e81e8b81df467ab1622105a1777be189867e2c289fdbaa7fd30b1522`, `ds_18f6ab02a0b63d4495c97179d3a9864e1e27e71d02a1caaa820986301782f13f`.

### E4

**OBSERVATION** `edge_c340985016b3e6d628142db43cc532025e244a4dee18e5b4b0e49b3148a7b0cf`, DATA, [O1](EVIDENCE.md#o1) → [O2](EVIDENCE.md#o2). Canonical classification `INFERENCE`. Original evidence operations: [O1](EVIDENCE.md#o1), [O2](EVIDENCE.md#o2).

Linked nodes: `col_0a8275f0568073887c5934a876e4571449a5afe6bdc09e8f7890b0a99eabfe23`, `col_1c68c1a9a27d85d503335d4102e38567fbb832450b3712d5dd962fb0b0f953b5`, `col_59d578b12fb78c1533e356b66f8ee6dbb0926f8309165547a6f5382e48947c1a`, `ds_ef1c9b98adbe650219aed22c32ef2d874388ae1ec5260c21914591a9c072a2b9`.

## Node register

**OBSERVATION** Original graph identifiers, logical names and owners.

| Logical node | Owner | Canonical ID |
|---|---|---|
| `work.observations` | `prepare` | `ds_b8093cf48fba188be7368a104284b37c48705efe6f4ae52b529aa114e59dd505` |
| `work.offsets` | `enrich` | `ds_7cade8c245955293331351748d52fd74adbb8a510d9df056dd80096c19962730` |
| `work.ordered` | `prepare` | `ds_ef1c9b98adbe650219aed22c32ef2d874388ae1ec5260c21914591a9c072a2b9` |
| `work.scaled` | `enrich` | `ds_18f6ab02a0b63d4495c97179d3a9864e1e27e71d02a1caaa820986301782f13f` |
| `work.adjusted` | `enrich` | `ds_409d5a037b977693af1ad803ca7cbf6f5ec25794de7a6868d35882ed67ab4800` |
| `work.observations.batch` | `prepare` | `col_7fdfb68c55c97a593688de1f04874967621429b9452ec3913827ba672776a96b` |
| `work.observations.sequence` | `prepare` | `col_73abad849885c65a8a5045e739e417dab76cd72083b6d3e98754a067317a963f` |
| `work.observations.value` | `prepare` | `col_ddc94290372cb75523f6ec283c24b2042f06510508cad299abfbf287d5664875` |
| `work.offsets.batch` | `enrich` | `col_53ce6d65bb65f98fa7839cd9f46f62953b2324f224ed617960d1f672bf510aab` |
| `work.offsets.offset` | `enrich` | `col_e0d7af860d928e7202679e8c363b0766a644c17bd9dffc2930bbccfeb132b115` |
| `work.ordered.batch` | `prepare` | `col_59d578b12fb78c1533e356b66f8ee6dbb0926f8309165547a6f5382e48947c1a` |
| `work.ordered.sequence` | `prepare` | `col_0a8275f0568073887c5934a876e4571449a5afe6bdc09e8f7890b0a99eabfe23` |
| `work.ordered.value` | `prepare` | `col_1c68c1a9a27d85d503335d4102e38567fbb832450b3712d5dd962fb0b0f953b5` |
| `work.scaled.batch` | `enrich` | `col_ba2b3bc2eb40c414fd001eb90a4407affaa70b9efee164da12a928332e3b165d` |
| `work.scaled.sequence` | `enrich` | `col_431505728a66f48397d2c9583dc5814f953a078278c50d2546bc4aea6a4de4d9` |
| `work.scaled.value` | `enrich` | `col_63ea1d340efaaa7f6a1a50a023936cc583fc69436d7f1bfa79ee3c9918d1e842` |
| `work.scaled.scaled` | `enrich` | `col_bedc24b3e81e8b81df467ab1622105a1777be189867e2c289fdbaa7fd30b1522` |
| `work.adjusted.batch` | `enrich` | `col_00abfae1f0f6c2da47f52de9cfcbc95a8a9e923f0cbc88edb6355f469ea8d5b0` |
| `work.adjusted.adjusted` | `enrich` | `col_dfde016fe5c0b703a41b57d1b5042d8b183b2740a481659f6027ce106a1bf81a` |

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
- `ORDER_PRECONDITION` ([O3](EVIDENCE.md#o3)): Establish the declared input/order/key requirements for every affected row.
- `TIE_ORDER_UNSPECIFIED` ([O3](EVIDENCE.md#o3)): Prove equal-key ordering is immaterial or supply the required tie order.
- `CARDINALITY` ([O3](EVIDENCE.md#o3)): Prove row multiplicity and selection under the declared cardinality rule.
- `NUMERIC_EQUIVALENCE_UNPROVED` ([O3](EVIDENCE.md#o3)): Preserve expression order, missing-value and numeric policies; runtime equivalence and numerical invariants have not been demonstrated.
- `NUMERIC_EQUIVALENCE_UNPROVED` ([O4](EVIDENCE.md#o4)): Preserve expression order, missing-value and numeric policies; runtime equivalence and numerical invariants have not been demonstrated.
- `DECLARED_OTHER` ([O4](EVIDENCE.md#o4), issue `issue_172180d89b056ce0a220fe2f`): Resolve the cited issue against independent source evidence and establish affected effects.
- `DECLARED_MISSING_DEPENDENCY` (graph-wide, issue `issue_238238051cbda64095adc363`): Identify the absent dependency and establish its operation and effect bindings.
- `DECLARED_OTHER` (graph-wide, issue `issue_35c1728f11449dbaa3e84499`): Resolve the cited issue against independent source evidence and establish affected effects.

### Unresolved records and bindings

**OBSERVATION** [O4 fact 0](EVIDENCE.md#o4-fact-0) names `postcheck.sas` without a bound target. Its reads, writes and downstream effects are UNKNOWN.

**ASSUMPTION** Obtain separately authorized target evidence before treating the represented outputs as the complete workflow.

**OBSERVATION** `issue_238238051cbda64095adc363` · MISSING_DEPENDENCY · no bound operation. Declared file keys: `synthetic:enrich.sas`.

**OBSERVATION** `issue_35c1728f11449dbaa3e84499` · OTHER · no bound operation. Declared file keys: `synthetic:enrich.sas`.

`synthetic:enrich.sas` lines 14–14, bytes [338, 363). Source SHA-256 `09bae8bbb5c2b68e47801dbc865cd07b21f4953cec24ebcee043bcfea696ba91`, span SHA-256 `36aaf6b81c2698d495fc1ff9f8663c7a57260dcb7061e488b1dac33fadf48de0`, cited excerpt SHA-256 `c4b4e8dc98993557cb288ac997d0d02fcb7e8397d48564260c0c32797ebe1474`.

**OBSERVATION** `issue_172180d89b056ce0a220fe2f` · OTHER · [O4](EVIDENCE.md#o4). Declared file keys: `synthetic:enrich.sas`.

`synthetic:enrich.sas` lines 14–14, bytes [338, 363). Source SHA-256 `09bae8bbb5c2b68e47801dbc865cd07b21f4953cec24ebcee043bcfea696ba91`, span SHA-256 `36aaf6b81c2698d495fc1ff9f8663c7a57260dcb7061e488b1dac33fadf48de0`, cited excerpt SHA-256 `c4b4e8dc98993557cb288ac997d0d02fcb7e8397d48564260c0c32797ebe1474`.


**ASSUMPTION** Independent review must establish original scope, effects and source semantics. Dataset identities alone do not establish physical versions or safe partitioning. Caller-supplied comments and issue prose have no decision authority.
