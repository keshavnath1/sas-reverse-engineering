# P2B-B1 execution approval checklist

**Decision: BLOCKED.** Baseline `fd9dc0194da9f15ff99805dd5ab6dea38815e684` is accepted
as **documentation only**. No implementation, provisioning or run is authorized. All B1
host tests are NOT_RUN. Use the [isolation design](P2B_B1_ISOLATION_DESIGN.md) and
[test plan](P2B_B1_TEST_PLAN.md) as the specifications for this checklist.

For each OPEN item, record the owner, decision, date and restricted evidence reference.
Keep sensitive details out of Git. Record actual grants in the [approval ledger](APPROVALS.md);
filling in a row does not authorize work.

| Execution prerequisite | Required decision or evidence | Status |
|---|---|---|
| Host and trust | Identify the dedicated Linux host or VM, approved location/tenant, owner, administrator and access roster. State who controls the kernel, hypervisor, snapshots and rollback. If those parties cannot be trusted, stop and redesign. | OPEN |
| People and separation | Name the independent human security reviewer, synthetic fixture custodian, evaluator operator and controller/observer operator. Record conflicts, service accounts, access groups and sanitized-release authority. Candidate C and reviewer R are distinct nonprivileged OS identities; R is not the human security reviewer. | OPEN |
| Runtime and isolation policy | Pin Linux distribution/image digest, exact kernel build/config, architecture, interpreter/runtime, offline dependencies and SHA-256 hashes. Pin launcher, broker, probes, recorder and policy revisions. Specify UID/GID/groups, capabilities, namespaces, private proc/mounts, syscall/exec policy, cgroup and resource limits. Reconcile the installed tuple to the manifest before a run. | OPEN |
| Storage and handoff | Identify filesystem/mounts, ownership/ACLs, quotas, key custodian, private evaluator store and append-only journal. Require durable nonreusable slots, all writers/descendants extinguished before bounded regular-file copying, and seal-last no-replace receipt. Independently reread the evaluator copy; bind its exact byte length/SHA-256, role, launch, slot and parent. Specify crash recovery and quarantine on ambiguous rollback; neither a digest nor a permission bit alone proves immutability. | OPEN |
| Data, network and credentials | Freeze a manifest of allowed public synthetic inputs, inert sentinel fixtures and per-role object grants. No private intake, gold, SAS, model calls or external egress. Approve default-deny network/DNS/socket rules, the per-launch offline broker channel, environment/descriptor allowlists and zero host/provider credentials or evaluator feedback in role views. | OPEN |
| Observation and retention | Name the independent observer and evidence custodian. Pin capture tools, clock, calibration, loss detection and raw-store ACLs. Witness target existence, actual role denial **and** backing permission denial, writer extinction, receipt equality and clean teardown. Approve finite retention for raw/audit data and backups, deletion evidence, expiring holds with a review owner, and sanitized release. | OPEN |
| Time and cost | Set monotonic deadlines, rate, currency, setup/storage costs and hard spending ceiling. Decline launch unless the full proof and safe cleanup fit. The [readiness proposal](P2B_READINESS.md) is at most two host-hours per proof attempt and three development attempts total (six host-hours); partial/failed attempts count. No cap, rate or retry is approved. | OPEN |
| Manifest freeze | Supply the exact IDs, fixture/tool/policy hashes, commands, limits, expected denial classes, positive controls, external witnesses and stop dispositions for every scheduled entry below. List every constituent operation and assertion, and freeze its finite total before launch. The atomic-operation count remains OPEN. | OPEN |

**Schedule to preregister — zero executions.** The accepted [test matrix](P2B_B1_TEST_PLAN.md#preregister-the-entire-proof)
defines the following denominators per complete proof attempt; keep them separate.

| Unit | Planned count |
|---|---:|
| Fresh launches: S01–S10, each with C1, C2, R1, R2 | **40** |
| Composite cases: 5, 6, 8, 7, 12, 5, 7, 11, 7, 7 variants respectively; 75 × 4 | **300** |
| BEGIN and END checkpoints: 2 × 40 | **80** |
| Positive-control outcomes: PC1–PC5 × 80 | **400** |
| Independent observation bundles: T01–T06 × 40 | **240** |

Stop immediately on **FAIL**: a confirmed breach, leak, unauthorized mutation, wrong
receipt accepted, or a positive control observed to give the wrong result. Missing authority
or witnesses, uncertain cleanup, or a time/cost limit means **BLOCKED**; known breaches
take precedence. Preserve each attempted outcome. Only after a proof stops, mark its
untouched entries NOT_RUN_STOPPED. No favorable skips, merged partial
runs or automatic retry. Stop after two repeated failures without new evidence. A repair
needs a new authorized attempt; a policy change requires a new freeze and the full matrix.

**Separate human decisions.** For each grant, record the approver, exact permitted
action, baseline/manifest reference, limits and expiry. No grant implies the next.

| Grant | What may be requested | Status |
|---|---|---|
| 1. Implementation | Develop the bounded offline harness against a reviewed target design. Identify the code/test scope and stop point. No host setup or sentinel launch. | OPEN |
| 2. Host provisioning | Configure only the named host, accounts, policy, recorder and storage under the approved change scope and budget. Return the as-built inventory, hashes and deviations for review. No sentinel execution. | OPEN |
| 3. Sentinel execution | After review of the built harness, actual host/policy tuple, complete frozen manifest, custody, budget and stop conditions, authorize the specified proof attempt. Stop for independent human security review of its restricted evidence. | OPEN |
| 4. Later semantic evaluation | B1 evidence cannot authorize gold or grading. B2 preparation needs its own decision after B1 review; B3 execution needs another for the frozen corpus, protocol, owners and budget (36 cases × two lanes × five repetitions = 360 case-attempts). | OPEN |

RMAP-02 and D09-B remain [OPEN](OPEN_DECISIONS.md). P3-A1 was accepted only for private
synthetic diagnostics. Native Windows access stays BLOCKED. Evidence statuses remain
DRAFT / UNVERIFIABLE / BLOCKED / NOT_RUN. Stop for human review.
