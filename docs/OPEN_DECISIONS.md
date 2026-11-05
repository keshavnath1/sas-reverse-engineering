# Open decisions and compatibility risks

Status: P2 readiness planning — recommendations awaiting approval. Updated 2026-11-05.

**P1 update, 2026-11-05:** the user approved D01–D03 for P0 and D04–D07 for
synthetic P1. The tables below retain the original recommendations for traceability;
their pending-approval language is historical. [APPROVALS.md](APPROVALS.md) records
the authorization. [P1_DESIGN.md](P1_DESIGN.md) records the implemented rationale
and conservative ID policy. D08–D12 remain open. Production data/provenance and
storage authorization remain unresolved; D07 permits synthetic P1 only. The later
local example authorized a read-only readiness check, not a synthetic label,
private-data ingestion feature, semantic extraction or publication of its files.

**P2 planning update:** the user reviewed and accepted P1 at
`5c8aea7588290925250b76c9cbd5091a3ea89f13`, including hosted CI verification,
and authorized only this planning checkpoint. [P2_READINESS.md](P2_READINESS.md)
and [P2_EVALUATION_DESIGN.md](P2_EVALUATION_DESIGN.md) specify D08/D09
recommendations. Neither their creation nor P1 acceptance approves P2 implementation.

Companion: [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md). Recommendations
distinguish observed implementation, proposed design and missing decisions.
No decision becomes human-approved merely by appearing in these documents.

## Current approval ledger

| Item | Status | Boundary |
|---|---|---|
| D01–D03 | APPROVED by the user for P0 | Repository/toolchain/baselines; subsequent remote publication was separately authorized |
| D04–D07 | APPROVED by the user for synthetic P1 | One canonical graph, byte identity, explicit scope/provenance and local safe publication |
| P1 result | ACCEPTED by the user's review | Structural scope at the exact commit above; not semantic correctness |
| P2 readiness documentation | APPROVED scope for this checkpoint | Only the two P2 design documents and this decision ledger |
| D08-A/B/C and D09-A/B/C below | RECOMMENDED, NOT APPROVED | No extraction, grader, isolation deployment, schema change or agent implementation yet |
| D10–D12 | OPEN | Business/oracle/runtime/downstream choices remain later human decisions |

## Decision register

D01–D07 retain their historical recommendations below; their approval status is
the ledger above. D08/D09 now have concrete proposals rather than implementation
authorization.

| ID / needed by | Decision | Recommendation | Consequence if unresolved |
|---|---|---|---|
| D01 / P0 | New repository name, local location, owner and eventual visibility | Local `sas-reverse-engineering/` under the current workspace; separate Git history; no remote publication in P0 | Cannot finalize bootstrap destination; current two documents remain in workspace `docs/` |
| D02 / P0 | Is the supplied v2 ZIP the intended `reference/` baseline, or is another pack missing? | Accept the exact archive hash recorded in the plan; preserve provenance and explicitly map the misencoded audit filename when copying it | A different pack may change requirements; do not silently substitute |
| D03 / P0 | Approve P0-only scope and initial toolchain | Python 3.12, package plus CLI, reproducible dependency pinning, local checks and GitHub Actions definition; no runtime libraries or agent framework yet | No implementation is authorized by this planning step |
| D04 / P1 | Canonical graph ownership across modules | One composed scoped-run source record with module-tagged operations and immutable module views; one reconciler/publisher | Per-module graphs can miss or disagree about cross-module edges |
| D05 / P1 | Source identity, stable IDs and hash canonicalization | Hash original bytes; version payload/envelope rules; IDs stable for identical source spans and operation kinds; explicit revision mapping after edits; declared encoding and newline policy | Citation and identity tests cannot be precise; decide whether logical identity survives line shifts |
| D06 / P1 | Scope authorization and log provenance | Explicit allowed roots, required dependencies and declared source/log run bindings; no implicit expansion or guessed matches; unresolved dynamic includes remain blocked | Inventory cannot establish completeness or log linkage; actual run provenance needs external evidence |
| D07 / before private intake | Evidence retention, permitted data, and seal trust model | Synthetic-only M1; private external read-only intake later; metadata-only reports; access-controlled immutable storage/trusted digest history for production | Local hashes alone do not provide authenticated or adversary-resistant history; PII handling cannot be inferred |
| D08 / P2 | Exact bounded semantic subset, canonical representation and reconstruction environment | Approve D08-A/B/C below and the closed synthetic subset in P2_READINESS.md; narrow canonical graph v2 using P1 identity primitives, no full interpreter | Missing schema/version or runtime decisions prevent defensible semantic reconstruction; no silent relaxation of v1 |
| D09 / P2–P5 | Independent gold, two-lane semantic evaluation and enforced isolation | Approve D09-A/B/C below and P2_EVALUATION_DESIGN.md; separate gold custodian/evaluator identity and fixed metrics/gates | No hidden-gold or independent semantic reliability claim until access-denial tests and frozen-corpus checks actually pass |
| D10 / P4–P6 | Business intent, corrected legacy behavior, keys, oracle, tolerances and population | Leave unresolved in upstream drafts; domain owner chooses in downstream interview/specify/test gates | No parity or release claim, no convenient sample/population default |
| D11 / P4–P6 | Platform constraints and benchmark protocol | Assess Spark/Ray/Dask/native fairly; agree resources, data sizes, repetitions, cache conditions, objectives and training equivalence before measurement | No winner, cost ranking or speedup assertion; benchmark status stays NOT_RUN |
| D12 / P7 | Receiving-side owner and authorization | Separate Agent-mastery change proposal, isolated branch, independent reconciliation and existing human gates | Candidate handoff may be packaged in P6 but cannot be automatically imported or approved |

D01–D07 have been decided for their approved phases. D08/D09 are the present
approval checkpoint. D10–D12 remain future decisions and must not be guessed.

## D08/D09 proposed resolutions requiring human input

| Item | Recommendation | Still needed before implementation |
|---|---|---|
| D08-A: semantics and granularity | Static synthetic SAS 9.4-profile subset: constrained DATA/SET/MERGE, SQL, literal macros/includes, BY, RETAIN/SUM/LAG, sort and fixed LOG/LST layouts; top-level operations with ordered internal facts; unsupported constructs explicitly BLOCKED | Approval of the exact allowlist/exclusions in P2_READINESS.md and symbolic-proof limits; no SAS execution or private pilot |
| D08-B: canonical contract | Version the existing composed graph to narrow v2 for numerical/order/state/step facts; reuse P1 inventory/citations/ID derivation; immutable v1 remains supported; explicit new IDs and predecessor mapping | Approval for future versioned schema/validator/envelope evolution, including graph-owned semantic facts and hash-bound verifier judgments |
| D08-C: environment and budgets | Pinned configurable candidate/reviewer adapters, bounded source retrieval, scope-read/staging-write tools, synthetic-only provider broker; three calls/32k input/8k output/five minutes per role/case maximum | Name actual model/provider revision, permitted endpoint/data policy, implementation runner and budget settings; none is assumed available |
| D09-A: gold ownership | SAS domain author plus second reviewer; separate custodian freezes source, source-anchored facts, exact expected gates, evaluator and denominator versions before runs | Named author/reviewer/custodian and private gold store; no maker-generated expected answers or copying public examples into “hidden” gold |
| D09-B: isolation | Dedicated Linux host/VM, separate OS identities and process/mount boundaries, gold absent from candidate/reviewer views, trusted immutable submission handoff; real denial tests before scoring | Provisioned runner/security policy and evaluator-owned storage; shared-user folders/chats are not an acceptable fallback |
| D09-C: corpus, metrics and feedback | 12 families × P/N/U = 36 hidden cases; reconstruction and checker-challenge lanes; five fixed attempts per case/lane; all required positive facts correct, exact negative gates, 100% obligation coverage and zero critical false approvals | Approval of strict finite-pilot thresholds, repetition/transport-failure policy and restricted diagnostic release; actual gold-derived assertion denominators frozen before running |

No particular person, model, evaluator host, hidden corpus or semantic test result
has been supplied/verified by this checkpoint. If those dependencies are absent,
future implementation/evaluation must report BLOCKED rather than invent them.

### Canonical-model compatibility decision

Observed: P1 v1 cannot serialize exact expressions, state reset, row ordering or
detailed LOG/LST semantics, and its semantic status is constant UNVERIFIABLE.
Recommendation D08-B is an explicit evolution of that same factual graph,
not a second graph/IR. Facts remain in canonical nodes/operations/edges; verifier
reports contain judgments and references only. Adding semantic payload changes
operation IDs under D05, so v1-to-v2 lineage must be explicit. Golden test anchors
cannot depend solely on candidate operation IDs because a wrong interpretation
also changes the ID. No v1 contract or artifact changes in this planning step.

The pack's P2 “DAG” is a derived canonical-ID visualization preserving state
cycles/unknowns. It does not authorize P3 scheduling or independence analysis.
Its P5 evaluation roadmap does not defer the independent semantic and security
checks explicitly required for this P2 pilot.

## Specification conflicts and proposed resolutions

| ID | Observed conflict or gap | Proposed resolution / remaining uncertainty |
|---|---|---|
| C01 | The reference audit proposes early discovery within Agent-mastery; normative 01/02 requires a separate upstream planner | Follow 01/02. Research proposals do not amend downstream workflow. P7 requires separate authorization |
| C02 | Build phase P3 precedes requirements in P4, while document 02's runtime flow drafts requirements before parallelism analysis | Treat phase numbers as development sequencing; enforce document 02 at runtime |
| C03 | README calls for one scoped graph; document 02 also describes per-module/run records | Proposed composed-run graph in D04; module views reference it. Avoid silently choosing incompatible authority models |
| C04 | Proposed source schema v0.1 was smaller than the narrative; P1 v1 now covers structural identities but not detailed semantic facts | P1 implemented the structural expansion. D08-B proposes narrow canonical v2 semantics and explicit version migration; not implemented or approved yet |
| C05 | Claim and handoff schemas omit several required narrative fields; enum field names differ across files | One versioned serialization specification with required provenance, counterevidence, preconditions and explicit field-name mapping |
| C06 | Document 10 says generated drafts remain CANDIDATE, while document 02's authority enum uses DRAFT/EVIDENCE_CHECKED | Use document 02's authority enum; candidate is descriptive, not a new authority value |
| C07 | Final checklist asks for three ADRs; requirements call for evaluating four runtime families with justified exclusions | Evaluate all four families; generate full designs for every viable candidate. Do not invent three viable options when evidence excludes them; report the unmet showcase condition |
| C08 | Append-only/immutable evidence is specified without storage, authentication, atomicity, retry or canonicalization details | M1 demonstrates local atomic publication and overwrite prevention under a stated trust model; production immutability is D07 |
| C09 | Hash-valid citations do not establish true dependencies; source/log association and dynamic macros may remain uncertain | Separate integrity and semantic gates; unknown is not independent; source-aware checks cannot be replaced by JSON Schema |
| C10 | ZIP entry spelling of the audit differs from the manifest's Unicode name | Explicit encoding mapping reproduced the content hash. Preserve original archive; do not regenerate a manifest to hide a discrepancy |

## Risk register

| Risk | Evidence classification | Mitigation and proof obligation |
|---|---|---|
| Downstream compatibility mistaken for acceptance | OBSERVED: existing import handles reusable patterns; trace requires approved SPEC/ADRs | P6 reports compatibility only; P7 must demonstrate approval-chain non-bypass |
| Valid structure mistaken for valid semantics | OBSERVED: loose trace/map schema fields; INFERENCE: malicious or erroneous claims can fit those shapes | Test valid-citation/false-independence cases with independent source-aware review; zero critical false approvals on pilot cases |
| Duplicate source authority | OBSERVED: trace and map both describe dependency reconstruction | Handoff must preserve IDs; contradictions reopen source evidence instead of map silently changing it |
| Run contamination | OBSERVED: downstream helper chooses newest state by mtime | Explicit workspace/module/run/attempt selection; concurrency, crash and stale-source tests |
| Unknown macro/state behavior | ASSUMPTION: real workloads may use dynamic includes, external state or proprietary formats; no real workload inspected | Supported-subset declaration, scope omissions and unknown records; never execute SAS to resolve uncertainty automatically |
| Invalid optimization or numerical drift | PROPOSED risk from reordering/state/reductions/training | Shared invariants and tie-out obligations; downstream human approval for changed behavior; measured runtime tests later |
| Evaluator leakage | PROPOSED risk: candidate tools could read local gold | Enforced process/account access boundary and denied-access tests; no independence claim until demonstrated |
| Private source or values exposed in Git/reports | PROPOSED risk for future intake | External intake, local ignored artifacts, synthetic public fixtures, metadata-only reports and leakage tests |
| Unsupported research or performance claims | OBSERVED: pack labels REA cases unreplicated and example verdicts expected | No REA integration claim, no default runtime winner, no measured speedup without actual benchmark evidence |

## What remains unknown

The Step 1 review established no production business schema, authentic source/log
run provenance, reference-output correctness, runtime environment, retention rule,
approver identity or measured performance. The subsequent private example was
only checked locally for readiness; it is outside this synthetic planning scope.
P1 structural tests and the user's CI review do not answer those production
questions. The old audit's smoke tests were not rerun at this checkpoint.
Neither the pack's expected outcomes nor these designs prove semantic reconstruction,
gold isolation or safe parallelism.

## Approval boundary and recommended next action

Review the two P2 design documents; approve or amend D08-A/B/C and D09-A/B/C,
and supply the named owners, model/tool policy and isolation environment. Then
issue an explicit P2-only implementation instruction using their acceptance
criteria. Approval of documentation alone does not start extraction, skills,
agents, semantic graders or contract implementation.

Stop after this checkpoint. No PRD/ADR generation, parallelization analysis,
private-data feature, SAS execution or downstream integration is authorized.
