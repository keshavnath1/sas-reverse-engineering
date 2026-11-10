# Read the actual migration profile and tie-out drafts

Open [migration-profile.yaml](../tests/fixtures/running-balance-workload/evidence/migration-profile.yaml)
and [tie-out.yaml](../tests/fixtures/running-balance-workload/evidence/tie-out.yaml).
Python generates these drafts when the operator requests modernization
drafts. Both bind the exact source identities and evidence manifest. The
typed [input profile](../tests/fixtures/running-balance-workload/source/profile.json)
is a different file. It supplies synthetic assumptions for reconstruction.

| Actual draft field | Current value | How to use it in review |
| --- | --- | --- |
| Migration profile `target.runtime` and `target.distributed` | `PENDING` | Discuss the native baseline and the evidence that would justify distribution. |
| Migration profile `execution.ordering_policy` and `execution.multiplicity_policy` | `PENDING` | Review SORT ties and SQL duplicate handling. |
| Migration profile `approval.architecture` and `approval.business_intent` | `REQUIRED` | A person decides and records approval separately where applicable. |
| Tie-out `checks.source_coverage` | `REVIEW_REQUIRED` | Inspect supported and unresolved scope. |
| Tie-out ordering, population, and numeric tolerance checks | `PENDING` | Specify expected outputs, comparisons, and tolerances. |
| Tie-out `reference.sas_execution` | `NOT_RUN` | Independent verification remains `UNVERIFIABLE`; semantic acceptance is `BLOCKED`. |

Copilot can propose values or questions for review. These checked-in YAML
drafts retain their pending fields.

## One concrete engineering check

The [public Python candidate](../scripts/run_running_balance.py) produces
three enrichment rows with columns `group, balance, weight`:

~~~text
[1, 2, 3]
[1, 2, 3]
[2, 4, 5]
~~~

The [engineering expectations](../tests/workflow/test_running_balance.py)
check those values. Compare enrichment as a multiset, so both copies of
the first row count. Check SORT separately for ascending keys and preserved
rows. A stable tie order is an engineering choice for the candidate.

In the REA analogy, follow-up checks test the claim a tool finding motivates.
Here the tie-out draft records the proposed checks and what evidence they
need. The Python comparison covers the public fixture. A SAS comparison
would need attributable typed inputs, execution and outputs, and a
performance claim would need a separate representative benchmark.

**Try it:** Would a set comparison catch a missing duplicate?
**Output:** One multiset check and one separate ordering check.

[Next: apply the method to your own INTAKE](07-apply-to-your-intake.md)
