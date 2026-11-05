# Open decisions and compatibility risks

Status: PROPOSED — Step 1 only. Reviewed 2026-11-05.

Companion: [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md). No decision below is human-approved by virtue of appearing here. Recommendations distinguish proposed design from observed evidence. Resolve only decisions needed for the next phase; do not block P0 on future runtime or business choices.

## Decisions requiring human input

| ID / needed by | Decision | Recommendation | Consequence if unresolved |
|---|---|---|---|
| D01 / P0 | New repository name, local location, owner and eventual visibility | Local `sas-reverse-engineering/` under the current workspace; separate Git history; no remote publication in P0 | Cannot finalize bootstrap destination; current two documents remain in workspace `docs/` |
| D02 / P0 | Is the supplied v2 ZIP the intended `reference/` baseline, or is another pack missing? | Accept the exact archive hash recorded in the plan; preserve provenance and explicitly map the misencoded audit filename when copying it | A different pack may change requirements; do not silently substitute |
| D03 / P0 | Approve P0-only scope and initial toolchain | Python 3.12, package plus CLI, reproducible dependency pinning, local checks and GitHub Actions definition; no runtime libraries or agent framework yet | No implementation is authorized by this planning step |
| D04 / P1 | Canonical graph ownership across modules | One composed scoped-run source record with module-tagged operations and immutable module views; one reconciler/publisher | Per-module graphs can miss or disagree about cross-module edges |
| D05 / P1 | Source identity, stable IDs and hash canonicalization | Hash original bytes; version payload/envelope rules; IDs stable for identical source spans and operation kinds; explicit revision mapping after edits; declared encoding and newline policy | Citation and identity tests cannot be precise; decide whether logical identity survives line shifts |
| D06 / P1 | Scope authorization and log provenance | Explicit allowed roots, required dependencies and declared source/log run bindings; no implicit expansion or guessed matches; unresolved dynamic includes remain blocked | Inventory cannot establish completeness or log linkage; actual run provenance needs external evidence |
| D07 / before private intake | Evidence retention, permitted data, and seal trust model | Synthetic-only M1; private external read-only intake later; metadata-only reports; access-controlled immutable storage/trusted digest history for production | Local hashes alone do not provide authenticated or adversary-resistant history; PII handling cannot be inferred |
| D08 / P2 | Extraction execution environment and independent reviewer | Agent-assisted reconstruction using shared trace vocabulary; deterministic checks plus separately scoped checker; no full SAS parser guarantee | Need approved provider/tool access, data policy, context limits and supported SAS subset before real extraction |
| D09 / P2–P5 | Pilot corpus, semantic gold ownership and evaluation isolation | Domain-reviewed synthetic gold initially, then authorized representative workloads; gold accessible only to evaluator identity/process; freeze evaluator versions before runs | Cannot claim semantic precision/recall or independent agent performance; directory separation alone is insufficient |
| D10 / P4–P6 | Business intent, corrected legacy behavior, keys, oracle, tolerances and population | Leave unresolved in upstream drafts; domain owner chooses in downstream interview/specify/test gates | No parity or release claim, no convenient sample/population default |
| D11 / P4–P6 | Platform constraints and benchmark protocol | Assess Spark/Ray/Dask/native fairly; agree resources, data sizes, repetitions, cache conditions, objectives and training equivalence before measurement | No winner, cost ranking or speedup assertion; benchmark status stays NOT_RUN |
| D12 / P7 | Receiving-side owner and authorization | Separate Agent-mastery change proposal, isolated branch, independent reconciliation and existing human gates | Candidate handoff may be packaged in P6 but cannot be automatically imported or approved |

D01–D03 are the decisions for Step 2 approval. D04–D07 constrain evidence implementation or private intake. D08–D12 should be settled at the relevant later checkpoint rather than guessed now.

## Specification conflicts and proposed resolutions

| ID | Observed conflict or gap | Proposed resolution / remaining uncertainty |
|---|---|---|
| C01 | The reference audit proposes early discovery within Agent-mastery; normative 01/02 requires a separate upstream planner | Follow 01/02. Research proposals do not amend downstream workflow. P7 requires separate authorization |
| C02 | Build phase P3 precedes requirements in P4, while document 02's runtime flow drafts requirements before parallelism analysis | Treat phase numbers as development sequencing; enforce document 02 at runtime |
| C03 | README calls for one scoped graph; document 02 also describes per-module/run records | Proposed composed-run graph in D04; module views reference it. Avoid silently choosing incompatible authority models |
| C04 | Proposed source schema v0.1 is smaller than the narrative: no attempt identity, structured log observations/run links, column nodes, classification, or structured unknowns | Define a versioned expanded contract in P1; explicitly document migration from the supplied example |
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

No authorized real SAS workload, business schema, source/log run provenance, production reference output, runtime environment, data volume, retention rule, approver identity, or measured performance has been established in Step 1. The old audit's 43 passing smoke tests were not rerun. Neither the pack's expected verifier result nor these planning documents prove semantic reconstruction or safe parallelism.

## Approval boundary and recommended next action

Review the proposal and resolve D01–D03, then explicitly approve the exact P0-only Step 2 in IMPLEMENTATION_PLAN.md. This authorizes project scaffolding only. P1 evidence contracts/validators, later skills/agents, private intake, remote publication, and downstream changes are outside that Step 2 scope.

No implementation proceeds from this document without that approval.
