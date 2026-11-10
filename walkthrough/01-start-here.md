# From SAS code to an execution plan

A loan team needs two outputs from the same prepared rows: an ordered
running-balance export and an enriched view with lookup weights. The
[public synthetic example](../tests/fixtures/running-balance-workload/source/main.sas.txt)
models that shape with small numeric rows. It contains no loan records.

**Opening question:** Does SQL enrichment need to wait for SORT?

~~~mermaid
flowchart LR
    A["Authorized SAS and input profile"] --> B["Python reconstructs supported operations"]
    B --> C["Evidence and unresolved findings"]
    C --> D["Human starts Copilot with the evidence"]
    D --> E["Skills draft requirements, graphs and design choices"]
    E --> F["People review decisions and validation obligations"]
~~~

## Explain it by comparison with REA

Reverse Engineer Anything (REA, by morluto) documents an agent-led
investigation. An agent calls inspection tools through MCP, receives
evidence, and can ask follow-up questions. Here, the operator first runs a
scoped Python reconstruction, then provides its evidence to Copilot. REA
is a comparison for the audience. The SAS example does not call REA.

| Audience question | REA-style investigation | This SAS example |
| --- | --- | --- |
| Who starts the inspection? | The agent chooses tool calls based on the question. | The operator selects the inputs and runs Python. |
| What anchors an answer? | Findings and limitations returned by the inspection tools. | Original source spans, declared dataset access, inferred edges, and coverage in the generated evidence. |
| What does the assistant do? | Explains findings and can drive further investigation. | The skills interpret the supplied evidence and propose a modernization design for human review. |

If a teammate asks whether enrichment must wait, the REA analogy is to ask
which tool finding supports that relationship. Here we can point directly
to the SQL input declaration and trace its inferred producer.

## Reading path

1. [SAS to Python evidence](02-sas-to-evidence.md)
2. [Evidence to as-is and proposed graphs](03-evidence-to-graphs.md)
3. [Write the five skills](04-how-to-write-the-skills.md)
4. [PRD, module design, and three ADRs](05-prd-and-architecture-decisions.md)
5. [Migration profile and tie-out drafts](06-profile-and-tie-out.md)
6. [Apply it to your INTAKE](07-apply-to-your-intake.md)

**Takeaway:** Keep the evidence, the design interpretation, and the approval
decision distinct. This example demonstrates bounded Python behavior on
synthetic inputs. Independent SAS verification and benchmarking remain unrun.
