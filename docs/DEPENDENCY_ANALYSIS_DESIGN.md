# P3-A1: what a supplied dependency graph can tell us

A missing edge is an open proof obligation. For example, if an earlier operation
writes a dataset and a later operation reads it, an omitted DATA edge is useful
to report. The declared sequence identifies which access is earlier. It does not
prove runtime order, authorize inserting an edge, or make either operation safe
to move.

The user approved this private development experiment at
`dba5b3aa5a60ef384bfc57a90b46ca72ea4f27dc`. [The roadmap](https://github.com/keshavnath1/sas-reverse-engineering/blob/eb9794167339d1991800c290a2b24ac10a57edf8/docs/POST_CP3D_ROADMAP.md)
specifies A01–A26. The workflow still requires independently accepted source
semantics and draft requirements before operational parallelism analysis.
[P2A](SOURCE_RECONSTRUCTION_DESIGN.md) reconstructs the graph; [P2B readiness](https://github.com/keshavnath1/sas-reverse-engineering/blob/eb9794167339d1991800c290a2b24ac10a57edf8/docs/P2B_READINESS.md)
and [evaluation design](https://github.com/keshavnath1/sas-reverse-engineering/blob/eb9794167339d1991800c290a2b24ac10a57edf8/docs/P2_EVALUATION_DESIGN.md) describe a separate, unrun gate.

## Subject and trust boundary

`diagnose(graph, expected_graph_sha256)` takes two in-memory arguments. Supply a
public synthetic canonical v2 Graph and its exact lowercase SHA-256 (sorted compact
UTF-8 JSON with the final LF). There is no path loader, authorization flag, store,
CLI, or persistent report. A path-looking string inside a fact stays inert. The
caller must supply a stable object during the call; results share no mutable state
with it. This is not a security sandbox for arbitrary code in the calling process.

Check the frozen v2 shape with the trusted package schema. Use the original record
identity function for datasets, columns, operations, edges and log observations.
Check local counts, owners and references: columns belong to their dataset's module;
reads can cross modules; definition/use indexes bind earlier facts in the same
operation. Check the declared sequence as a permutation, independent of the order
of records in the array. Keep array and expression order intact when hashing the
graph. An observation is bound to the supplied run/attempt, not authenticated as a
measurement. An inventory issue can keep its original ID after graph enrichment;
check uniqueness and references, never fabricate its missing hash preimage.

A matching digest identifies exactly the supplied graph. It cannot prove the
claimed file hashes, source fingerprint, scope, LOG association, freshness, seal,
semantic reconstruction, or completeness of effects. An author can rehash a false
graph. Neither a positive public fixture nor a successful integrity check can
promote any of these claims. Structural refusal yields a diagnostic error, never
a partial result. A valid graph containing a contradiction still yields the
rejecting finding alongside all unknowns.

## Reading the result

The result binds the algorithm, exact parent digest and workspace/run/attempt/
source fingerprint to a detached analysis. The only evidence authority is `DRAFT`;
verification is `UNVERIFIABLE`, semantic acceptance `BLOCKED`, and benchmarks
`NOT_RUN`. No eligibility value can authorize execution.

| Question | Diagnostic interpretation |
|---|---|
| What directed relationships are represented? | DATA, STATE, ORDER, SIDE_EFFECT and UNKNOWN retain their original edge IDs. Reachability through UNKNOWN is a represented constraint, not established causality. RESOURCE stays separate, even if it connects the same endpoints. |
| Why is a destination reachable? | One predecessor and original edge per reachable ordered pair. Follow predecessors to recover one deterministic shortest edge witness. Self-reach requires a positive-length cycle. |
| Which cycles exist? | Strongly connected components retain members and internal edges; self-edges remain in the source. No cycle deletion or scheduler DAG. |
| Do read/write declarations overlap? | In declared sequence, compare writes→reads (RAW), reads→writes (WAR) and writes→writes (WAW). Include parent dataset/column aliases. Distinct columns in an unversioned dataset do not prove independent writes. Findings are annotations, never new graph edges. |
| What else is missing? | Preserve the referenced operation's state effects, control/lineage fact indexes, order/tie requirements, cardinality and numeric obligations. Local issues name their operations; an unbound issue stays global. Contradictions reject eligibility. |
| What if there is no path? | For distinct operations: **no represented dependency path; independence unproved.** Effect completeness, storage versions, semantic equivalence and independent verification remain outstanding. |

No target runtime, schedule, worker wave, performance estimate, parallel-execution
approval or semantic verdict follows from this result. [Validation](DEPENDENCY_ANALYSIS_VALIDATION.md)
records actual execution separately from design. Windows evidence access/publication
remains blocked before caller I/O; `analyze-parallelism` remains a placeholder.

## Finite work and witness storage

| Input guard | Inclusive maximum |
|---|---:|
| Operations / modules / edges | 100 / 8 / 10,000 |
| Datasets and columns combined / facts across operations | 2,000 / 5,000 |
| JSON occurrences (every scalar/container and every object key) | 200,000 |
| Nesting (root depth 0) | 64 |
| Exact canonical bytes, including JSON escaping, UTF-8 and final LF | 8 MiB |

Reject over-limit, cyclic, non-JSON and nonfinite input. The input guards apply
before potentially expensive shape checks or whole-graph serialization. Bundled
schema loading is the only permitted file access. Input bounds govern occurrences,
so two references to a shared subtree count twice; caller-defined container or
scalar subclasses cannot supply serialization hooks.

BFS visits each operation once per source and scans at most `N × E` outgoing edge
instances across searches. It keeps at most `N²` predecessor rows. Tie-break first
by target sequence, then canonical target ID, edge type and original edge ID.
`witness(result, start, end)` follows at most `N` edges from the chosen table. A
layered graph with exponentially many possible routes still stores one predecessor
per reachable pair. SCC membership reuses mutual reachability; internal edge IDs
are grouped in one additional scan. No all-path recursion or graph dependency.

Each ordered-in-sequence operation pair contributes at most three conflict rows.
Each row reports the exact count of shared logical dataset groups and one canonical
access witness for that kind. For RAW, it counts groups for which no direct DATA
edge names **any** node of the group, prioritizing an uncovered group as the
witness. Partial DATA coverage within one dataset is not proof of a complete
producer binding. Full access sets remain addressable through operation IDs. This
avoids repeating every column combination across pairs; nothing is inferred from
an absent witness for another column. Dataset names here refer to supplied logical
identities, never physical aliases or versioned storage. Fingerprints and IDs stay
outside any scheduling or optimization decision.

## Independence of the public expectations

Before creating the candidate module, a separate fixture author wrote 23 literal
positive graph digests, canonical JSON/record preimages and topology/conflict
expectations, with the A01–A26 obligation manifest. A read-only reviewer matched
all 23 graph hashes and 101 reconstructible records to the frozen rules and
checked the literal answers. Git commit `0e1b80fe60c412ddbf19a0c93c4291f4fe3bfd95`
contains just the vectors; SHA-256 of the file is
`7e8e5f6d3c37bf3ef7553abb3511446c23a22562f460398cb7e5344b95b6a90b`.
This was independent development authorship and review in one workspace, not
isolated evaluation, human domain adjudication or a P2B result.

Case-insensitive duplicate dataset names or sibling column names under distinct
canonical IDs are ambiguous in this unversioned name model; reject them rather
than picking a writer. File-count and covered-source-file claims are not validated
against an unavailable inventory. The 8 MiB limit applies to input; the derived
result can be larger. At most `3 × N × (N−1)/2` conflict rows and `N × (N−1)`
no-path rows are possible. The private witness helper consumes the returned
analysis table; an edited result has no authentication or authority.

An issue's free-text `missing_proof` and caller-chosen `code` can themselves
assert false authority or give instructions. Diagnostic codes and proof wording
therefore come from the closed issue **kind**, not those strings. To inspect the
original claim, follow `parent_graph_sha256` → `source_collection` → `issue_id`.
Operation/file references keep their original meaning. The parent is unchanged;
its issue text is source material, never a diagnostic verdict.
