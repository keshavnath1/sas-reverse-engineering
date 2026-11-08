# P2A INTAKE modernization review

Review manifest SHA-256 `c8e63ee5a954918bdbed5adda43f759412122e94bb106a86f780b333076441e4`.
In a human-invoked Agent session, supply [MANIFEST.json](MANIFEST.json),
[INVENTORY.json](INVENTORY.json), [EVIDENCE.json](EVIDENCE.json), this handoff,
[migration-profile.yaml](migration-profile.yaml), and [tie-out.yaml](tie-out.yaml).
Verify the manifest-listed payload digests and the P2A graph's inventory and
profile bindings before review. Stop on a missing or mismatched identity.

Use the five existing skills in order. For this subject, use the P2A graph in
place of the fixture-specific reports in their instructions. Carry findings
from each draft into the next. Save the drafts separately from this package.

| Skill | Draft and evidence to use |
| --- | --- |
| sas-reconstruct | TRACE reconstruction. Use inventory file hashes and graph operations, facts and statement coverage. Cite the original file, lines and half-open byte span. Record unknowns, contradictions and any source the graph did not reach. |
| sas-specify | PRD and testable requirements. Trace each requirement to a recovered fact or label it as a proposed requirement needing owner confirmation. Keep typed input descriptors and declared input order as synthetic profile assumptions. |
| sas-analyze | MAP and dependency review. Cite graph edges by ID and trace their evidence operations. Distinguish declared reads and writes from inferred edges. Assess represented order and state constraints, including across BY groups and guarded LAG calls when present. Missing edges leave independence unproved. |
| sas-validate | Verification plan. Separate structural checks, proposed public engineering cases and attributable SAS reference evidence. Address join multiplicity and missing values, BY input order, retained state and conditional queue advancement where represented. Unbound LOG/LST provides no run evidence. |
| sas-architect | ADR with conditional native and distributed designs. Tie each option to the actual dependencies, ordering and state, and state what must be proved before partitioning or benchmarking. Leave runtime selection pending. |

For each material claim, put every JSON citation in its own inline code
span using the exact form `FILENAME#/pointer`. Use bare filenames
and one complete pointer per span. Cite only paths you opened and verified;
never infer list indices from line numbers or use pointer ranges. The
inventory has no approval or binding fields. The YAML drafts carry those
fields. Before human review, the operator runs `scripts/check_p2a_citations.py`
on the draft and returns any unresolved pointers for correction. A clean
preflight still requires human review of coverage, meaning and classification.
Add canonical operation or edge IDs and original spans where applicable. Apply
these classifications consistently in every section:

| Classification | Use and citation |
| --- | --- |
| SOURCE_DECLARED | An individual source-backed declaration or statement. Cite its operation fact and original span. A graph summary, inferred dependency, or profile value cannot establish a source declaration. |
| INFERRED | A derived relationship or interpretation. Cite the specific edge or interpretation record and preserve its original graph classification. An edge marked INFERENCE remains inferred even when both endpoints have source citations. |
| PROFILE_ASSUMPTION | A declared synthetic input descriptor, input sort order, row sample, or missing-value join policy. Cite the specific profile.json field. Describe its use by the graph separately from any source-declared BY or JOIN. |
| PACKAGE_METADATA | Manifest statuses, counts, recorded identities, or YAML draft settings and approvals. Cite the exact status, count, digest, or setting. |
| UNRESOLVED | Missing runtime, provenance, behavioral, or partitioning proof. Cite the relevant finding or boundary. |
| PROPOSED | A draft requirement, test, or architecture decision. Cite the evidence that motivates it and state what would validate it. |

Split claims that combine different evidence classes. Keep graph labels
intact when describing what the graph records. Scope validation to the
operations actually present. Request reference outputs for the cited
operations and do not introduce scoring or other absent stages. Report checks
actually performed separately from pending checks. Comparing recorded hashes
is an identity consistency check. Report byte-level verification only if
hashes were recomputed.

The YAML files are drafts for operator review. This P2A package supports a
design review only. GATE-1 and candidate continuation are outside this route.
Behavioral evidence is UNAVAILABLE, SAS reference and benchmark execution are
NOT_RUN, semantic verification is UNVERIFIABLE, and semantic acceptance is
BLOCKED.
