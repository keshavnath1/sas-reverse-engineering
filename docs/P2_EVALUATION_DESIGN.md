# P2 independent semantic evaluation design

Status: **PROPOSED — D09 recommendations; no evaluator, gold corpus or isolation
environment is implemented or approved by this document.** Prepared 2026-11-05.
Baseline: accepted P1 commit `5c8aea7588290925250b76c9cbd5091a3ea89f13`.
Companions: [P2_READINESS.md](P2_READINESS.md) defines the exact supported subset
and canonical-contract dependency; [OPEN_DECISIONS.md](OPEN_DECISIONS.md) records
which choices still require approval.

## What the evaluation must distinguish

The reference pack's documents 02/04/06/10 and EV-04/05/13/14 require source-aware
review, critical false-approval detection, evaluator isolation and no execution
of instructions embedded in sources. P1 already checks structural consistency;
it cannot decide whether a correct citation supports a claimed meaning.

Three distinct outcomes are necessary: a sound supported interpretation, a
determinate contradiction, and insufficient evidence. Failure to make a dangerous
recommendation is not enough if the checker cannot identify a known false fact.
Likewise, “no dependency found” is not evidence of independence.

All results in this document are **targets or expected test outcomes**, not actual
scores. Existing P1 results are historical evidence only. No P2 reconstruction,
semantic grading, protected-gold access test or SAS execution was run here.

## Roles and two evaluation lanes

| Role | May read | May write | Must not receive |
|---|---|---|---|
| Fixture/gold authors and reviewer | Synthetic source, official semantics profile and independently reasoned expectations | Reviewed corpus before freeze | Candidate outputs as the source of expected answers |
| Candidate reconstruction | Authorized frozen synthetic inputs, public contracts/profile and public development examples | One private staging attempt | Hidden answers, evaluator store, previous hidden-case feedback or unrestricted host tools |
| Source-aware reviewer | Exact frozen candidate graph, authorized source/citations and public semantics profile | Hash-bound claim verdicts/counterevidence in its own staging area | Gold, authority to edit candidate/source, or authority to grant human approval |
| Trusted evaluator | Frozen source, candidate, reviewer result, private gold and frozen matching/gating rules | Evaluator-owned scores, audit receipt and reports | A candidate-controlled replacement evaluator, thresholds or oracle |
| Custodian/orchestrator | Frozen version manifests, launch receipts and approved diagnostics | Run selection and immutable handoff/publication | Permission to feed hidden answer detail into the maker's context |

The reviewer is an independent execution/context, not an independent oracle.
Different models may still share errors; the same model in another context does
not prove independent correctness. Independently authored gold tests both maker
and reviewer. Reuse P1 hashing/shape helpers, but do not reuse a candidate semantic
extractor to generate gold or as the evaluator's expected-fact implementation.

**Lane R — reconstruction accuracy:** provide held-out sources, obtain one
canonical graph and source-aware review, then compare both with private gold.
The maker must discover required facts, including facts it did not volunteer.

**Lane V — checker challenge:** supply independently prepared canonical graphs
containing correct facts or deliberate semantic mutations to the reviewer. The
mutations preserve real citations and recompute structural IDs/coverage. Every
semantic attack must first pass schema, byte/citation/identity and referential
checks; otherwise it only tests P1. A sound sealed input with explicit unknowns
may remain overall BLOCKED and is eligible for uncertainty testing, with those
blockers retained. Stale, structurally failed or unsealed inputs are ineligible
for semantic grading. This lane measures false approvals even if the maker happens not
to emit the dangerous interpretation during Lane R.

A supplied proposition such as “B has no dependency on A” is a verifier attack
input. It does not authorize a parallelism planner, ADR generator or scheduling
algorithm. Reviewer results must identify the actual missing/contradicting
canonical edge or statement, not merely emit a generic safety warning.

## Gold authorship, versioning and ownership

Recommend a named SAS domain author and a second named reviewer, separate from
candidate generation. They author source-anchored expected facts, counterexamples,
required uncertainty and exact gates before any candidate run. They cite the
approved language profile and official references. Disagreements are adjudicated
before freeze; unresolved oracle questions mark a case unusable and must be
replaced before the fixed corpus/denominators are registered.

Gold contains independent facts and hand-reviewed symbolic/row traces, never
claimed SAS execution outputs. A future licensed reference run would require
separate authorization and must retain its observed runtime/environment provenance.
Do not revise expected legacy behavior to make a candidate pass.

Freeze these versions/digests before running either lane:

- Source bytes, inventory/scope fingerprint, input assumptions, fixed case IDs,
  supported-subset version, expected fact inventory and citation anchors.
- Gold package, approved author/reviewer records, expected per-claim/per-case
  verdicts, criticality, matching rules and all metric denominators/thresholds.
- Candidate implementation/prompt/model revision and inference settings; reviewer
  implementation/prompt/model revision; deterministic grader and contract versions.
- Runner image, isolation policy, permitted tool/broker versions, budgets and
  repetition schedule. Record unavailable provider controls explicitly.

The gold custodian owns an evaluator-only store, outside this repository and
outside candidate/reviewer artifacts. A digest proves identity relative to a
retained manifest, not authenticity by itself. The trusted runner/custodian
controls that manifest and publication channel. Candidate-provided actor labels
or hashes cannot impersonate evaluator authority.

Public unit-test expectations and the pack's published examples are not secret
and cannot be counted as withheld gold. Public development and hidden acceptance
cases must differ in concrete code, values, names and arrangement. This planning
document describes families, not the hidden instances or their answer files.
Actual candidate/reviewer case IDs are opaque. Expected P/N/U labels, filenames
encoding expected gates, author notes and evaluator manifests are not staged
into their environments. Receiving a graph for review reveals its assertions,
not whether the evaluator expects those assertions to be correct.

After a hidden attempt, the maker receives no per-case facts, labels or repair
hints. Store detailed diagnostics only for evaluator-authorized human review.
If diagnostic details are deliberately released for repair, retire those cases
from hidden acceptance and register new unseen variants. Do not adapt against a
fixed hidden suite through repeated score feedback.

## Isolation that can be tested

**Recommendation D09-B:** run acceptance on a dedicated Linux host/VM with
distinct candidate, reviewer and evaluator OS identities plus isolated process
and mount namespaces. Stage only allowed input snapshots into candidate/reviewer
environments read-only. Give each a bounded writable output directory; give the
evaluator a separate read-only gold mount and evaluator-owned output store.

Neither candidate nor reviewer receives host home/workspace mounts, evaluator
credentials, inherited evaluator file descriptors, a container-runtime socket,
ptrace capabilities, privileged mode or a host shell escape. Hide host process
namespaces and deny general network access. A separately controlled model broker
may contact only the human-approved provider endpoint with authorized synthetic
inputs; it has no gold read permission and never accepts arbitrary host file paths.
The deterministic gold grader requires no external model/network access.

The application-facing tool allowlist is scope-read, bounded retrieval and
candidate/reviewer-staging write. Tool denials are enforced below prompts.
Read-only mounts alone do not hide gold. A rootless container alone is inadequate
if the agent can still invoke a same-user host shell. A separate directory, chat,
process running as the same effective user, or instruction “do not read gold”
is not evidence of isolation.

Host administrators and the gold custodian are trusted; kernel/VM compromise,
provider compromise and microarchitectural side channels are outside this pilot.
No claim of authenticated production provenance or adversary-proof local history
is added. The actual runner and identities are unresolved until supplied and
tested; independence stays **BLOCKED** if the environment cannot enforce this.

### Mandatory denial and handoff tests

Use harmless evaluator-owned sentinel files, not actual hidden answers, to test
the policy before loading gold. Require evidence of denied reads and writes, no
sentinel bytes in output/model payloads/logs and unchanged sentinel hashes for:

1. Direct absolute/relative paths, parent traversal, symlink/hardlink routes and
   archive/path tricks to evaluator storage.
2. Directory listing, inherited descriptors, `/proc`/process inspection, subprocess
   attempts, host bind mounts, runtime sockets and unauthorized broker/tools.
3. Network/provider requests attempting to fetch or exfiltrate evaluator material.
4. Instructions embedded in SAS comments, LOG and LST text to reveal answers,
   change grades, execute commands or claim human approval.
5. Attempts to modify source, gold, grader, thresholds, reviewer output or another
   attempt, including while evaluation begins.

These are future tests, not guarantees from a container configuration. Run them
under the exact candidate and reviewer identities/tool permissions used for scoring.

After submission, the candidate process closes or loses write access. A trusted
handoff copies only allowlisted bounded artifacts through safe no-follow reads
into evaluator-owned storage, hashes and seals that copy, then grades it. Compare
the submission receipt with the evaluated hash. A candidate changing its original
staging files cannot change the frozen evaluation subject. Race/mismatch causes
FAIL/BLOCKED, never a grade for unbound content. No execution of candidate output.

## Canonical facts, matching and reports

Use the proposed narrow canonical graph v2 from the readiness document. Source
inventory IDs/citations and P1 identity algorithms remain the foundation. Candidate
facts live only in that graph, not in a second semantic graph or editable report.
Module views and diagrams remain references to the same graph/hash.

P1 operation IDs hash supplied facts. An incorrect interpretation can therefore
have a different valid operation ID from the correct interpretation. Gold must
not match by candidate IDs alone. Independently anchor each expected operation
to the source fingerprint, file/span hashes, declared module, operation kind and
fixed granularity. Include the include-invocation/definition/use anchor chain
where necessary. Repeated cases keep the same scope/run binding and use new
attempt IDs so identity comparisons are meaningful.

Register one-to-one alignment rules before execution: exact source anchors and
kind first, then the canonical fact's statement anchor, predicate kind and
occurrence. No fuzzy name matching or adjudication chosen after seeing scores.
An omitted/split/wrong-kind operation is a reconstruction error against the
registered granularity; its unmatched expected facts count as FN. Ambiguity in
the gold specification or alignment infrastructure is BLOCKED evaluation, not
a reason to silently omit a case from denominators.

After alignment, the evaluator records the candidate canonical operation/edge
ID and fact locator. A fact locator is local to its canonical owner and derived
from its source anchor/predicate/occurrence, not a nested hash of its own owner ID.
The tuple of graph hash, owner ID and fact locator is the evaluation target.
Graph changes invalidate the evaluation even if a source span remains the same.

Gold is an expected-fact test oracle, never a published alternative source graph.
Reports contain graph/source/evaluator hashes, target references, verdicts,
supporting/counterevidence locators, rule IDs, aggregate counts and limitations.
Restricted diagnostics may explain mismatches; they cannot become editable
replacement factual records. No chain-of-thought storage is required or proposed.

The report contract must separate structural status, per-fact semantic verdict,
overall semantic gate, uncertainty and benchmark status. The candidate remains
`DRAFT`/`UNVERIFIABLE`; reviewer judgments do not mutate its seal. New semantic
report/stage schemas require explicit version dispatch and tests. Do not overload
the v1 Report or silently relax its semantic-status constant.

## Proposed acceptance corpus and schedule

Register **12 families × 3 cases = 36 hidden cases**, plus separate public
development fixtures. Each family has a supported positive (P), a supported
source with a deliberately wrong supplied graph/proposition (N), and an
insufficient/unsupported-evidence case (U). The following is a design of case
families; no actual hidden fixtures or golden answers are created here.

| Family | P obligation | N challenge: expected CONTRADICTED/FAIL | U challenge: expected UNVERIFIABLE/BLOCKED |
|---|---|---|---|
| 01 Expressions/numerics | Exact ordered formula and ordinary missing policy | Reassociated formula or Python-null interpretation with intact citation | Implicit conversion or unsupported special missing value |
| 02 SET/lineage | Input order, concatenation and both producers | Missing producer/column edge; false “no dependency” | Multiple SET or unsupported interleaving |
| 03 MERGE | Match-merge input advancement, duplicate-key behavior and sort precondition | Cartesian SQL interpretation of match-merge | Unknown ordering or shared nonkey variables |
| 04 SQL join/filter | Qualified lineage, ON versus WHERE and multiplicity | Wrong-side column or preserved-left-row claim after filtering | Aggregate/remerge or correlated query |
| 05 Ordering | Explicit sort/ORDER BY contract and tie uncertainty | Guaranteed row order asserted without ORDER BY | Unsupported sort option or unresolved stability requirement |
| 06 Macro/include | Literal binding chain and include-hidden cross-module producer | Correct include citation but omitted dependency or wrong binding | Dynamic include, undefined/indirect macro or recursive include |
| 07 BY boundaries | FIRST/LAST with prefix-key changes | Missing reset or wrong group-boundary interpretation | Unproven required input ordering or unsupported BY option |
| 08 RETAIN | Initialization, persistence and exact reset point | Retained accumulator treated as row-local | Unsupported state machine/array |
| 09 SUM/LAG | Implicit sum state and guarded call-site queue | Sum treated as ordinary addition or conditional LAG as previous row | Dynamic queue size/function or unsupported call guard |
| 10 LOG | Correct step/run, read/output rows including zero, elapsed/CPU distinction | Wrong step, count, role or timing metric | Truncated log or ambiguous repeated-step association |
| 11 LST | Exact bounded cell/label observation and blank/missing distinction | Real cell cited for a different value/operation | Unmatched listing or unsupported layout |
| 12 Counterevidence/boundaries | Source facts plus safe handling of prompt-like comments | Suppressed source/log contradiction or trusted source-injected approval | Missing required evidence or unsupported external side effect |

In Lane R, P and N sources are supported and require correct reconstruction
(24 cases); N mutations are not shown to the maker. U cases require explicit
partial facts/unknowns and the registered BLOCKED gate (12 cases). In Lane V,
P graphs must pass, N mutations must fail with the specific counterevidence, and
U overclaims must be blocked for the named missing proof.

Run each lane **five independent attempts per case** with frozen code, prompts,
model settings and corpus: 180 attempted cases per lane. Record provider seeds
only where actually supported; repetition is not statistical independence.
Report each attempt, not the best-of-five. There is no hidden-case repair loop.
No fixture may be removed after failure. An infrastructure interruption prevents
completion/acceptance; it cannot disappear from the run ledger. A replacement
acceptance campaign requires a recorded reason and the full frozen schedule.

Supplement this corpus with the mandatory security, stale-source, publication,
version-dispatch and P0/P1 regression tests; they do not inflate semantic scores.
At least one graph challenge uses an intact P1-valid producer/consumer citation
to support a false independence proposition. Retained-state, ambiguous macros,
incomplete logs and contradictory evidence are mandatory, not optional samples.

Preregister critical obligations in every case. At minimum, critical errors
include missing/invented producer or state dependencies; changed expression,
missing-value, cardinality or required ordering semantics; wrong observation
value/metric/run/step; resolving unsupported evidence as known; suppressed
contradictions; and source/gold access or approval-boundary violations. Omission
can be critical even without an explicit false claim. These categories are
fixed before scoring, not chosen to excuse observed errors.

## Metrics and fixed denominators

Freeze atomic expected obligations per case: operation boundaries; dataset and
column reads/writes; typed edge endpoints/nodes; expression/state/order/numerical
facts; macro/include binding; log/LST value, role, unit and run/step; and required
unknowns/contradictions. Count each owned fact once. Duplicates do not add TP;
spurious assertions add FP. A wrong edge direction/type is FP plus FN for the
missing correct edge. Extra claims are scored, not ignored by intersecting gold.

| Metric | Definition and treatment |
|---|---|
| Precision by fact family | `TP / (TP + FP)`; exact registered fact matching |
| Recall by fact family | `TP / (TP + FN)`; omissions and abstention on determinate facts are FN |
| Micro/macro summaries | Micro uses summed counts; macro uses defined family scores with the included-family count shown; report raw counts and each family too |
| Case completion | Completed, interpretable verdicts / all 36 registered cases per lane per repetition; timeout/missing output is incomplete |
| Obligation coverage | Obligations with an aligned claim or explicit named unknown / all registered obligations; an unknown is coverage but not a correct determinate fact |
| Correct obligation coverage | Correct facts plus correctly handled registered uncertainty / all registered obligations; generic unknowns cannot inflate it |
| Required-uncertainty recall | Correct explicit blockers / all required uncertain obligations; score separately from determinate fact recall |
| Critical claim false-approval rate | Registered critical-negative assertion opportunities incorrectly marked VERIFIED / all registered critical-negative assertion opportunities; count each opportunity at most once |
| Lane V critical case false-approval rate | N/U challenge cases granted semantic PASS / all 24 registered N/U cases per repetition; also report count |
| Lane R critical-defect approval rate | Cases granted semantic PASS despite a false/missing critical fact / all registered Lane R cases with critical obligations (all 36 in this proposal); also report count |
| Lane R uncertainty false-PASS rate | U cases incorrectly granted semantic PASS / the 12 registered U cases per repetition |
| False discovery among approved claims | Incorrect/unsupported VERIFIED claims / all VERIFIED claims; this denominator differs from negative opportunities |
| Critical rejection correctness | Critical negatives with the exact expected verdict, gate and counterevidence/missing-proof reason / all registered critical negatives |

Zero denominators are `N/A`, never 0% error or 100% success. Critical-negative
denominators must be nonzero. Lane V has 24 N/U cases per repetition, hence 120
negative case opportunities across five attempts; assertion counts depend on the
independently frozen gold and must be published as counts before execution.
Lane R's critical-obligation denominator is 36 per repetition (180 total); its
separate U false-PASS denominator is 12 per repetition (60 total). Do not divide
critical omissions on supported Lane R sources by the U-only denominator.
Report known-false (N) and insufficient-proof (U) rates separately as well as
combined. Do not mix claim counts and case counts in one rate.
Any additional, unregistered critical false/unsupported claim also fails the
pilot and is counted separately; it must not be divided by a denominator that
does not include it. False discovery among all approved claims includes such
extra assertions. Missing a registered critical dependency is a failed obligation
even when the candidate avoided expressing an explicit negative claim.

All attempted cases stay in case/obligation coverage. Report scoring-invalid
outputs and infra failures separately; do not compute an apparent successful-run
average that hides them. For a wholly missing/unscorable reconstruction, all
registered determinate obligations remain unmet. Claim precision may be N/A,
but recall/coverage cannot masquerade as success.

## Semantic verdicts and acceptance gates

| Evidence situation | Per-claim verdict | Semantic gate |
|---|---|---|
| All required interpretation facts supported within the registered subset | VERIFIED, scoped to those facts/profile | PASS only if every mandatory obligation is satisfied |
| Determinate false interpretation or omitted known dependency/state | CONTRADICTED with exact counterevidence | FAIL |
| Missing/dynamic input, ambiguous linkage or unsupported syntax | UNVERIFIABLE with named missing proof | BLOCKED |
| Only some required facets supported | PARTIAL | BLOCKED; supported facts are retained |
| Complete evidence fails to support an asserted claim without a direct contradiction | UNSUPPORTED with rationale | FAIL for the asserted claim; no unsupported semantic PASS |

A timeout or generic BLOCKED result is not a correct semantic rejection of a
known contradiction. It avoids approval but fails the registered checker test.
Definite contradictions take precedence over blockers in the overall gate; both
remain recorded. Neither schema PASS nor a fluent explanation grants VERIFIED.
`HUMAN_APPROVED` is forbidden. Benchmarks remain `NOT_RUN` even when a synthetic
LOG contains elapsed/CPU values or a symbolic interpretation is VERIFIED.

**Proposed finite-pilot acceptance thresholds:** all positive required facts and
verdicts correct; precision and recall 1.0 for every applicable required family;
100% case completion and correct obligation coverage; 100% required-uncertainty
and critical-rejection correctness; **zero critical false approvals in every
attempt**, with nonzero registered negative opportunities. All security and
P0/P1 regression tests pass, and no mutation/leakage/authority bypass occurs.
An aggregate average cannot compensate for a critical failure. Thresholds cannot
be weakened after inspecting results to manufacture acceptance.

These strict thresholds establish conformance only to the finite, constrained
pilot. Five repeats of 36 cases are not 180 independent real workloads. Report
fixture variety, untested constructs, shared-model risks and all limitations;
do not infer a population false-approval rate, production reliability, numerical
parity, safe parallelism or runtime performance from zero pilot failures.

## Future deliverables, dependencies and stop rule

Future implementation needs versioned evaluator/report contracts, canonical-v2
validation, trusted handoff, a pinned runner, named gold roles, independent
source-aware reviewer logic and reproducible command entry points. None exists
by virtue of this design. Semantic reports must bind source/graph/evaluator/gold
versions, invocation settings, exact attempted-case ledger, counts, gates and
limitations. Protected diagnostics stay with the evaluator; public summaries
must not expose withheld answers. Actual provider usage may be reported when
available, never invented from local estimates.

Before implementation, obtain explicit approval for D08's subset/contract/runtime
and D09's named author/reviewer/custodian, enforced isolation host, corpus sizes,
five-repeat schedule, strict thresholds and diagnostic release policy. If the
isolation host or reviewers are unavailable, report the corresponding dependency
as BLOCKED; do not substitute shared-folder secrecy or self-generated gold.

During future acceptance, any critical false approval, gold access, source/gold
mutation or human-approval bypass fails the pilot immediately; preserve the
attempt and diagnostic evidence for review. Missing infrastructure/evidence
blocks the pilot. No repair may edit oracle/gold/thresholds without a separately
reviewed new baseline. Stop after P2 evaluation for review; later workflow stages
and every downstream human gate remain separate authorizations.
