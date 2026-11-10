# How Python turns SAS into evidence

Open the public [source scope](../tests/fixtures/running-balance-workload/source/scope.json)
and [typed input profile](../tests/fixtures/running-balance-workload/source/profile.json).
The scope identifies the entry point, literal include edges, and expected
file hashes. The profile supplies column types, small public input rows,
and an input-order assumption for the DATA step. The profile is a declared
input contract.

~~~mermaid
flowchart TD
    A["SAS bytes, declared scope and typed profile"] --> B["review_intake.py: verify file set and hashes"]
    B --> C["evidence.py: build_inventory"]
    C --> D["semantic.py: reconstruct"]
    D --> E["sas_subset.py: parse_source"]
    E --> F["Supported facts and unresolved findings"]
    F --> G["semantic.py: assemble operations and inferred edges"]
    G --> H["INVENTORY.json, EVIDENCE.json and MANIFEST.json"]
~~~

Follow the [operator entry point](../scripts/review_intake.py), then the
[engine code map](../src/sas_re/README.md). The parser uses implemented
grammar rules. For example, it can recognize the input after `DATA=`, the
output after `OUT=`, and the keys in `BY`. The reconstruction combines
those declarations with source citations, input contracts, and related
operations. Unsupported forms or missing preconditions remain visible.

## Follow two statements into the graph

The source contains these excerpts:

~~~sas
proc sort data=work.running out=work.export_order;
by group subkey;
run;
~~~

~~~sas
from work.running as a left join work.lookup as b on a.group = b.group
where b.weight > 0;
~~~

| Original source | What the actual evidence records |
| --- | --- |
| [main.sas.txt](../tests/fixtures/running-balance-workload/source/main.sas.txt), lines 12–14, bytes [278,350) | Operation 3 reads `WORK.RUNNING`, writes `WORK.EXPORT_ORDER`, and sorts by `group, subkey`. |
| [enrich.sas.txt](../tests/fixtures/running-balance-workload/source/enrich.sas.txt), lines 1–6, bytes [0,202) | Operation 5 reads `WORK.RUNNING` and `WORK.LOOKUP`, left joins on group, applies the weight filter, and writes `WORK.ENRICHED`. |

Open the [actual graph](../tests/fixtures/running-balance-workload/evidence/EVIDENCE.json).
Compare `/operations/3` and `/operations/5` with `/edges/2` and `/edges/3`.
The operations carry source declarations. Both edges are `INFERENCE` records
from operation 2, the DATA step. The public package contains six operations
and four inferred edges. See the [bound inventory](../tests/fixtures/running-balance-workload/evidence/INVENTORY.json)
and [evidence manifest](../tests/fixtures/running-balance-workload/evidence/MANIFEST.json)
for the identities.

**Deterministic** means the same verified bytes, profile, and engine version
reproduce the evidence. The reconstruction does not execute the SAS program.
As in the REA analogy, ask what the tool actually observed and where the
assistant is interpreting a finding.

**Try it:** Point to the source span that declares each consumer's input.
**Output:** Two cited source facts and two separately labeled inferred edges.

[Next: turn the evidence into graphs](03-evidence-to-graphs.md)
