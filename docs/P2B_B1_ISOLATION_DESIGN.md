# P2B-B1 isolation readiness: who can see which bytes?

**Decision requested later:** approve a specific native evaluation host, isolation policy,
owners, storage and budget for sentinel testing. **Current decision:** planning only.
Baseline: `5e62727b9b8e463cf6c7dd1bc68172801a7868f6`. Host qualification is
**BLOCKED**; B1 denial tests, launches, controls and handoffs are **NOT_RUN**.

The smallest useful boundary is one dedicated Linux host or VM with a trusted administrator
and independently observable OS policy. Two untrusted role identities run deterministic
probes there. A trusted handoff exposes only the frozen submission intended for its recipient.
A deployment claim would cover that host, image, policy and interface only. Different prompts,
chats, directories, same-user subprocesses and GitHub CI cannot establish this boundary.

This refines [P2B readiness](P2B_READINESS.md) and the [two-lane design](P2_EVALUATION_DESIGN.md).
The [roadmap](POST_CP3D_ROADMAP.md), [approval](APPROVALS.md), [open decisions](OPEN_DECISIONS.md)
and [security boundary](../SECURITY.md) still apply. The [P3-A1 design](P3_A1_DESIGN.md) and
[validation](P3_A1_VALIDATION.md) concern private graph diagnostics: neither those results,
public fixtures nor a candidate's own reconstruction checker are semantic gold. Do not use
them to score dependencies. Artifact authority stays DRAFT, verification UNVERIFIABLE,
semantic acceptance BLOCKED, benchmarks NOT_RUN.

## Principals and permitted transfers

The **two identities under test** are distinct nonprivileged host UIDs/GIDs C and R.
They are distinct from the trusted services below. Each launch gets a new isolated context,
even if it reuses its role's UID; no prior launch's storage or channels are attached.
The matrix schedules **40 distinct launches**: S01–S10 × C/R × two fresh launches per
family/role, with BEGIN and END controls in each. No reuse across families; the proposed
two-host-hour ceiling has not been demonstrated. Trusted services have distinct duties and least-privilege accounts. They may live on the
same trusted host. C/R may behave as arbitrary hostile code with their effective OS rights;
do not credit the probe's cooperation.

| Principal | Allowed inputs and outputs | Forbidden route |
|---|---|---|
| Candidate (C) | Frozen, public synthetic input/profile and read-only runtime; its current staging slots; bounded submissions/requests to its own stub channel | No R staging/verdict, evaluator receipt, scores, gold, previous attempts or host credentials |
| Source-aware reviewer (R) | Its assigned frozen input and, only where explicitly granted, an exact **read-only copy** of C's frozen synthetic graph; its own fresh staging slots | No access to C's live workspace or other candidate submissions. Cannot modify the graph, see protected answers/results or approve a claim |
| Trusted broker (offline stub) | A private, per-launch endpoint, controller-assigned actor/attempt and finite object/verb allowlist; returns only a bounded public object or fixed neutral refusal | No filesystem paths/URLs, role-selectable identity, provider keys, general shell, gold, scores or evaluator lookup. Never relay raw internal errors |
| Custodian | Owns version/visibility manifests and restricted release decisions; provisions harmless canaries through the trusted controller in B1. Would control independently authored gold **only after a separate grant** | Cannot turn public cases into hidden gold, disclose answer material to C/R, or change a frozen subject in place |
| Independent evaluator | In B1, an offline verifier under a separate identity reads sentinel/control material and its own custody copy; reopens it, recomputes the digest and compares the trusted receipt. Keeps results private | No grader or semantic judgment in B1; no candidate routines supply expected answers. Cannot fetch a submitted pathname, run the submitted bytes or send a score back |
| Trusted controller/importer; independent security reviewer | Controller reserves attempts, launches/tears down roles, grants explicit transfers, installs the evaluator-owned copy and private receipt. Independent human reviewer has read-only restricted observations, reconciles the matrix and accepts or rejects the security evidence | Neither role self-reports its effective policy or controls its validator, audit or release. Controller cannot mint human sign-off. Implementer/admin self-attestation is insufficient |

Gold, evaluator results, the other role's private data and prior-launch residue are
represented **only by unrelated random sentinels** in B1. Future gold would be a
custodian-controlled read-only input for the evaluator, outside Git; results would remain
evaluator-owned. C/R can receive only preassigned public material, including the explicitly
released C artifact for R. Give neither an evaluator credential, detailed rejection, score,
canary bytes, shared cache, or retry selected with private feedback. Keep public status
responses independent of private data; an unreleased case must not become an interactive
oracle. A later release of hidden detail would require the custodian's decision and retirement
of affected hidden cases. No hidden cases exist in this plan.

## Effective native controls and independent observations

Require both **absent visibility** and **underlying host permission denial** for protected
objects. A read-only mount of gold still leaks gold. An acceptable implementation must freeze
the exact control values and recorder before launch, and demonstrate them from outside the
role. These are proposed controls, not a selected distribution, deployed policy or new
dependency of this repository.

| Surface | Required enforcement | Independent evidence / reason to stop |
|---|---|---|
| Files, devices and aliases | Fresh mount namespace with private propagation; read-only verified runtime and assigned input only. Role-private home/tmp/cache and bounded staging. Omit host root/home, evaluator drives, runtime/SSH sockets, host devices, package caches and past attempts. Host ownership, ACLs and non-writable ancestor directories must also enforce separation. No other bind mount, hardlink or writable alias into privileged data | Controller records mount IDs/options/propagation, UID/GID/ACL and allowed object identities; confirms the target exists outside the role and authorized siblings really work. An absent or incorrectly seeded target is not a successful denial |
| Process and privilege | Distinct host accounts, no shared privileged groups/capabilities, non-root, no new privileges; nondelegated cgroup per launch, fresh PID, mount, IPC and network namespaces and private proc view. Constrain exec/syscalls and devices with an observed OS policy; deny mount/setns, ptrace/process-memory access, privilege-changing exec, namespace creation/escape, runtime/daemon APIs and unapproved tools | Inspect actual process tree, namespaces, proc mount, credentials, all capability sets, limits, syscall/exec profile and denied actions. Paths omitted from an application allowlist alone are not enforcement |
| Credentials and descriptors | Start from an allowlisted environment and descriptor table: approved standard streams plus one role-specific bounded message channel; no inherited host directory, secret, agent socket, keyring, writable audit fd or metadata service. No ancillary file-descriptor transfer; broker trusts control-plane launch binding, not actor-supplied claims | Inventory actual environment **names**/fd targets outside the process, test access to planted non-secret markers and cross-role descriptors. No real credential in a fixture, log or receipt |
| Network and feedback | No external network for C, R, broker or evaluator. Separate network views; enforce default-deny address families/routes, DNS, loopback listeners, filesystem/abstract UNIX sockets and alternate namespaces. Only the prebound broker IPC is permitted; no provider endpoint. Broker grammar uses opaque assigned object IDs, fixed actions/replies, length limits and launch identity | Trusted policy/deny counters and controlled local witness/sinks corroborate attempted routes. No packets to the internet as a “test”. Empty logs/timeouts without attribution give no credit. No score, grader output, privileged failure reason or previous-role state via API/stdout/retry |
| Lifetime, resources and audit | Launch admission pins image/kernel/runtime/policy, monotonic deadline, CPU/memory/PID limits, staging bytes/inodes, and bounded streams. Controller outside the role owns process creation/termination; no ability for descendants to migrate or modify the cgroup or observation services | Inspect cgroup membership and limits, quiescence including descendants, endpoint revocation, unmount and cleanup. Lost capture, exhausted budget, unverifiable control or unavailable hostile fixture prevents PASS |

Native design references: the Linux man-pages describe [mount views and propagation](https://man7.org/linux/man-pages/man7/mount_namespaces.7.html),
[PID visibility](https://man7.org/linux/man-pages/man7/pid_namespaces.7.html) and
[network namespaces](https://man7.org/linux/man-pages/man7/network_namespaces.7.html).
[No new privileges](https://man7.org/linux/man-pages/man2/PR_SET_NO_NEW_PRIVS.2const.html)
limits gains on exec; it does not grant isolation by itself. The kernel's
[cgroup v2 documentation](https://docs.kernel.org/admin-guide/cgroup-v2.html) describes
hierarchical resource/lifecycle controls. Inspect these on the eventual tuple; no control
has been observed on an approved B1 Linux host.

For each launch, the independent observer must record *two different facts*: what C/R
can reach through its actual mount/proc view, and why its effective credentials cannot
traverse a protected backing directory even if the path is known. For the latter, anchor
each gold-surrogate, peer-private, result and prior-state specimen below a protected
parent. Record the trusted parent/object ID, permissions, ACLs, effective groups, labels
and capabilities. A fixed, noninteractive host-side check using the corresponding
nonprivileged credentials must encounter the registered permission denial on that
backing route; independently confirm the same specimen exists using a permitted
principal. Do not pass the protected parent fd or a broader view to C/R. This
sideband observation is not a role probe or a substitute for one. An unproved
credential match, unavailable observer or inactive fixture leaves that case BLOCKED.

## Immutable handoff on that host

“Immutable” here means a role, including its descendants, cannot replace, amend or delete the
bytes or select an alternative for the evaluator. The trusted kernel/admin, custodian and
controller are in the trust base. This is not cryptographic protection against a malicious
administrator, rollback by a hypervisor, hardware/covert-channel certification or a production
WORM claim. If this trust assumption is unacceptable, stop and redesign on independently
controlled infrastructure. Never transfer by passing an actor-supplied path or by choosing
the latest file.

1. **Reserve.** Before exposing an ID, durably reserve it with a no-clobber insert and
   sync its trusted journal. Give each positive, negative and crash subject its own
   controller-anchored slot directory; PC2 scratch cannot pollute a valid PC5 slot.
   Bind the nonreusable attempt and slot to the proof revision, C/R identity, launch, assignment, input manifest
   and policy/image/probe digests. Grant one fixed flat filename per slot and one artifact
   type: public canonical v2 graph for a candidate or inert public test submission for a
   reviewer. Proposal: one nonempty regular UTF-8 JSON file of at most 8 MiB per slot.
   Freeze allowed shape, filename, expected control-byte hashes and negative fixtures before
   testing. These are B1 transport constraints, not changes to any v1/v2 schema.
2. **Stage and request.** The actor can write only its current inbox and declare completion
   with the slot, length and claimed byte digest. Content, embedded instructions, filenames
   and actor labels cannot select tools or authority. The broker can acknowledge a request;
   acknowledgement freezes nothing. BEGIN and END controls use separate disposable slots.
   Neither becomes a successful handoff until trusted processing after writer extinction.
3. **Close the writer boundary.** Cut off new requests, terminate and reap the entire role
   cgroup and descendants; verify it is empty/non-repopulatable and that no other permitted
   process or mount can write that staging. Revoke channels and account for inherited fds,
   writable maps and out-of-band aliases. A chmod, cooperative close, read-only remount
   alone or a metadata recheck is not a revocation proof. If extinction or exclusivity cannot
   be observed, mark the slot incomplete and BLOCK. For cgroup v2 require externally
   observed extinction of the whole subtree (`populated=0`) and admission closed, not
   just a signal sent or a paused task. No trusted copy while writes may continue.
4. **Copy by object handle.** Trusted importer retains a handle to the controller-provisioned
   stage anchor, verifies expected filesystem/parent and exact membership, rejects links
   (including multiply linked regular files), mount crossings, devices, FIFOs, sockets,
   subdirectories, extra files and archives. Inspect metadata without activating special
   files; only read a verified regular object tied to that identity under the quiescent
   boundary. On Linux, design the relative lookup with the bounds in
   [openat2](https://man7.org/linux/man-pages/man2/openat2.2.html) (`RESOLVE_BENEATH`,
   `RESOLVE_NO_SYMLINKS`, `RESOLVE_NO_XDEV`). No ordinary pathname reopen, following paths
   in JSON, unpacking, SAS execution or weaker fallback. Bound actual bytes while copying,
   not just the stated length. Check exact declared length/hash, UTF-8/structure and trusted
   assignment. Strictly refuse duplicate keys, malformed/over-limit input and ambiguous names.
5. **Seal last, in evaluator-owned custody.** Hash the *original transferred bytes* with
   SHA-256 as copied; independently reread the new private object. Publish the bounded
   object and a no-replace, evaluator-side receipt through the trusted controller, with
   file and directory durability verified on the qualified filesystem. The receipt binds
   identity from the launcher, attempt/slot, role, input and policy digests, artifact type,
   exact byte length and SHA-256, plus parent receipt/digest for a reviewer. If a canonical
   graph digest is also recorded, name it separately and compute with the frozen algorithm:
   differing JSON whitespace may change transport bytes. Never reserialize to hide a
   mismatch. A bare hash, caller-supplied receipt or mode bit is not authority.
6. **Release exactly once.** An assigned reviewer can see a read-only snapshot of the frozen
   bytes with its approved digest, not private receipt contents. The evaluator selects only
   the committed receipt by exact ID through its trusted namespace, recomputes length and
   digest from its stored copy and confirms actor, assignment and parent. Results/audit
   stay outside both role views. In B1 this is a byte comparison only. A crash before durable
   commit permanently tombstones that slot; recovery reconciles by exact receipt and digest,
   never “newest”, overwriting or completing a partial attempt. A duplicate/replay or
   forged submission is an expected negative only when refused without a new success.
   Accepting a wrong, unstable, unavailable or substituted subject is a security failure.
   A crash after durable commit but before acknowledgement returns the original private
   receipt to trusted recovery only, never a second commit. If journal rollback or durable
   state is ambiguous, quarantine the attempt/storage epoch; do not reuse its IDs.

End-of-launch cleanup and retention are separate. Before admitting another role, require
external evidence of zero surviving writers/channels, detached private mounts and revoked
scratch. At entry to the next scheduled context, check exclusion there against the prior
launch record; do not count a future denial before it happens. The final launch requires
observed terminal cleanup and receipt checks; no extra successor is launched or certified.
Keep the restricted ledger, failed
receipts and raw observations out of Git. At trusted close time record deletion deadlines
as close time plus each **approved finite retention period**, including snapshots/backups
and keys; require a custodian deletion record or dated incident hold with an expiry and
review owner. Missing periods, unaccounted copies or a failed cleanup block reuse and
release. Retain non-content nonreuse reservations, or retire the entire epoch permanently,
when content expires. No silent reopening of failed IDs after purge.

No existing P1/P2A publisher or evidence store is being repurposed. These are requirements
for a future evaluator-private importer; its receipts are not new canonical artifacts,
verification statuses, approvals or edits to sealed history.

## Decision record required before implementation or execution

| Missing accountable input | Status and admission criterion |
|---|---|
| Dedicated physical host or VM, location, owner and trust base | **OPEN**. Identify exact host/tenant, isolation from other users, administrator, kernel/image and hypervisor trust; authorize sentinel-only use |
| Independent human security reviewer, custodian and evaluator operator | **OPEN**. Name people, conflicts/separation, access groups and who may release sanitized evidence. The semantic reviewer role R is not this security reviewer |
| Runtime and effective OS policy | **OPEN**. Freeze interpreter, installed offline artifacts/hashes, kernel build, launcher, syscall/LSM profiles, recorder version, resource limits and network/IPC policy. No native probing here |
| Storage, rollback, incident and retention policy | **OPEN**. Specify local filesystems/ACLs, encryption/key owner, quota, durability, restricted raw audit store, backup/deletion scope and release authority. Define finite raw/audit retention durations and handling of security holds |
| Time and spending | **OPEN**. Prior proposal: zero external model calls, at most two host-hours per complete proof attempt, at most three development attempts; stop after two repeated failures without new evidence. No actual rate, approved charge limit or setup/storage allowance. No retries without a separate authorized attempt and frozen schedule |
| Authorization and invalidation | **OPEN**. Require explicit scope for implementing the offline harness and for exercising it on the named tuple; no deployment implicit in document acceptance. New host, kernel/runtime/policy, mounts, broker routes, custody or observer changes invalidate the old isolation result until separately requalified |

The [test plan](P2B_B1_TEST_PLAN.md) fixes the two-role denial schedule, controls, leakage,
cleanup, evidence and stop rules. Only a complete, independently reviewed real-host report
could support an isolation claim for the tested tuple. Missing prerequisites remain BLOCKED;
nothing here starts B2/B3 or the later **36 cases × 2 lanes × 5 repetitions = 360
case-attempts**. The evaluation host is optional specialized infrastructure for evaluation,
never a Git, Docker, WSL, VM, cloud or AI-provider requirement for the offline workstation
engine. Native Windows source access/publication stays BLOCKED; Agent-mastery stays unchanged.

## What was actually checked at this planning checkpoint

The checkout began clean at the stated baseline. The following are documentation
and preservation checks on the development workstation, **not B1 tests**:

- Staged scope: exactly two new plans and three ledger edits (`APPROVALS.md`,
  `OPEN_DECISIONS.md`, `BEST_PRACTICES_ADOPTION.md`). All other **97 baseline
  files** matched the baseline tree byte for byte and in executable mode. The eight
  frozen hashes and three P3-A1 implementation/test hashes matched the recorded
  [P3-A1 validation values](P3_A1_VALIDATION.md). Downstream metadata still pins
  `bc754e0f1204a99020c864df2a5b25983005e09c`; Agent-mastery was not changed.
- Read-only comparison of the retained public P3-A1 baseline and final sets:
  15 P1 files and 15 P2A files matched exactly, including their two recorded
  manifest hashes. The demos were not replayed locally.
- Checked changed Markdown's encoding, line endings, fenced blocks, local links
  and matrix arithmetic. Ten S01–S10 rows have four NOT_RUN cells each; the 75
  named case variants expand to 300 case executions, separately from 400 control
  outcomes and 240 trusted observation bundles. This verifies the written schedule
  only. There were **zero B1 launches, probes, receipts, scores or security passes**.

Local check commands: `git rev-parse HEAD`, `git status --short --branch`,
`git diff --check`, `git diff --cached --check`, `.venv/bin/python scripts/check_repository.py`
and a read-only Python comparison of the staged scope to `git ls-tree -r` /
`git show <baseline>:<path>` and the retained artifact sets. Whitespace, guard and
comparison checks returned 0; the guard checks only selected tracked paths and
credential formats. The 693 regression methods and 133 P3-A1 subtests are
**historical P3-A1 engineering evidence**. No local regression suite, host
provisioning, sentinel run, isolated evaluation or model/SAS call was performed here.
Any ordinary CI on publication is repository regression evidence only. Stop for
human review before implementing or running B1.
