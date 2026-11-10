# From dependency findings to a PRD and three ADRs

The following drafts illustrate what the team can ask the skills to produce
from the [actual evidence](../tests/fixtures/running-balance-workload/evidence/EVIDENCE.json).
The [public authored review](../tests/fixtures/running-balance-workload/REVIEW.md)
is the longer companion example. Business approval remains pending.

## Mini-PRD

**Goal.** Deliver an ordered running-balance output and an enriched lookup
output from the same prepared population. Ask the business owner to confirm
both consumers, the intended meaning of balance and marker, and how ties and
duplicate matches should be treated.

| Draft requirement | Evidence and acceptance question |
| --- | --- |
| R1. Preserve the ordered preparation rules. | `/operations/2` records BY groups, retained balance, first-group reset, sum and guarded LAG. Do synthetic tests distinguish skipped calls from group resets? |
| R2. Preserve the sorted output. | `/operations/3` declares two keys. Does the output preserve row multiplicity, and does the consumer need a tie policy? |
| R3. Preserve enrichment and its multiplicity. | `/operations/5` declares the LEFT JOIN, selected fields and filter. Do duplicate, unmatched, and filtered cases produce the agreed row multiset? |

**HLD.** A preparation module writes an identified prepared population.
Separate export-ordering and enrichment modules consume that population.

**LLD.** Preparation needs ordered group keys, retained balance, and a
guarded queue. Export sorts full records by `group, subkey`. Enrichment
preserves lookup matches and applies the filter after joining. Each module
gets an explicit input and output contract and separate engineering checks.

## Draft architecture decisions

| ADR | Proposed choice | Alternative and evidence needed |
| --- | --- | --- |
| ADR-1 — Branch handoff | Keep SORT and SQL as separate consumers of preparation. | Routing enrichment through SORT adds work with no declared dependency in `/edges/2` or `/edges/3`. Confirm both consumers get the intended prepared version before changing scheduling. |
| ADR-2 — Order and state | Keep preparation ordered, preserve the group reset and guarded LAG, and document the stable tie choice of the Python candidate. | Partitioning preparation needs proof that group state and the queue survive boundaries correctly. SAS equal-key order still requires separate evidence if it matters. |
| ADR-3 — Runtime baseline | Use native Python as the initial engineering comparison on the bounded example. Keep runtime selection pending. | Spark or Dask may suit measured partition or shuffle workloads, and Ray may suit demonstrably independent tasks. Require correctness evidence and representative cost measurements before choosing. |

An REA-style follow-up asks what evidence would settle an open technical
question. Here the ADR makes that question durable. For example, ADR-2
records what must be demonstrated before changing state ownership.

**Try it:** Pick one ADR and name the evidence that would change its proposed
choice. **Output:** One conditional decision a reviewer can accept, revise, or defer.

[Next: read the actual profile and tie-out drafts](06-profile-and-tie-out.md)
