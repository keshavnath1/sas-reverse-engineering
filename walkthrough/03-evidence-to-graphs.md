# Two graphs, two different jobs

Give Copilot the [evidence graph](../tests/fixtures/running-balance-workload/evidence/EVIDENCE.json)
and [review handoff](../tests/fixtures/running-balance-workload/evidence/MODERNIZATION_REVIEW.md).
Ask it to draw the current dependencies before proposing any changes.
These diagrams show example skill deliverables. Python generates the
evidence records, and the skill can render a view of them in Mermaid.

## As-is view

~~~mermaid
flowchart LR
    raw["WORK.RAW"] --> data["DATA: ordered BY, RETAIN, SUM and guarded LAG"]
    data --> running["WORK.RUNNING"]
    running --> sort["SORT by group and subkey"]
    running --> join["SQL: LEFT JOIN and post-join filter"]
    lookup["WORK.LOOKUP"] --> join
    sort --> ordered["WORK.EXPORT_ORDER"]
    join --> enriched["WORK.ENRICHED"]
~~~

The two outgoing relationships from preparation correspond to `/edges/2`
and `/edges/3`. The input names come from the operation records. The SQL
operation does not declare a read of the sorted output. The graph describes
logical dependencies and leaves runtime order and dataset versions unverified.

## Proposed optimization view

~~~mermaid
flowchart TD
    waste["Hypothetical target: prepare, then SORT"] --> wrong["Send sorted rows to both outputs"]
    keep["Proposed target: prepare once"] --> version["Identify the prepared dataset version"]
    version --> a["SORT only the ordered export branch"]
    version --> b["Join and filter directly for enrichment"]
    a --> checks["Check order, state and multiplicity"]
    b --> checks
~~~

**Design implication:** Preserve the source's separate branches and avoid
introducing a sort prerequisite for enrichment. The inefficient target above
is a teaching contrast. The source already separates the two consumers.
Parallel scheduling remains conditional on state ownership, output isolation,
dataset-version continuity, and measured workload cost.

**REA comparison:** An agent-led investigation can ask for another probe
when it cannot justify a relationship. In this workflow, have Copilot cite
the exact evidence records first. If those records cannot establish
independence, keep it unresolved and ask for the specific missing evidence.

**Try it:** Which source read would justify making SQL wait for SORT?
**Output:** An as-is graph and one proposed graph with the difference labeled.

[Next: write the skills that produce these views](04-how-to-write-the-skills.md)
