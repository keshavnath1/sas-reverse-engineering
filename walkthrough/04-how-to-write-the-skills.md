# Write skills that work from evidence

A skill gives Copilot a repeatable review job. The operator starts the
session and supplies the [generated handoff](../tests/fixtures/running-balance-workload/evidence/MODERNIZATION_REVIEW.md),
the selected graph and inventory, and the YAML drafts. A skill-file read
only shows that the instructions were opened. Review the produced draft to
see whether the instructions were applied.

## Worked Analyze skill for this example

| Section | Instruction to write |
| --- | --- |
| Trigger | Use when a proposed architecture changes an execution dependency. |
| Required inputs | Read the bound graph and source citations for DATA, SORT, and SQL. |
| Workflow | Identify the declared writer and readers of `WORK.RUNNING`. Check whether SQL reads `WORK.EXPORT_ORDER`. Check the order and state obligations separately. |
| Output | Return an as-is Mermaid graph, one proposed design graph, and a finding that names the evidence and remaining proof. |
| Verification | Resolve `/operations/2`, `/operations/3`, `/operations/5`, `/edges/2`, and `/edges/3`. Label reads and writes as declarations and graph edges as inferences. |
| Boundaries and stops | Keep runtime order and version continuity unresolved. If a required citation or input is missing, report the affected finding as unresolved. Keep speedup and parallel execution conditional. |

## Use the same structure for the five responsibilities

| Skill | Question it answers | Deliverable |
| --- | --- | --- |
| [Reconstruct](../skills/sas-reconstruct/SKILL.md) | What does the source declare and where does coverage end? | Cited TRACE/MAP and gaps |
| [Specify](../skills/sas-specify/SKILL.md) | What must the new system preserve, and what needs a business decision? | PRD and module contracts |
| [Analyze](../skills/sas-analyze/SKILL.md) | Which data, order, and state constraints shape the design? | Dependencies and optimization hypotheses |
| [Architect](../skills/sas-architect/SKILL.md) | Which component boundaries and runtime options are justified? | HLD, LLD, and ADRs |
| [Validate](../skills/sas-validate/SKILL.md) | What would establish correct behavior and performance? | Engineering checks and independent reference obligations |

The REA analogy is useful here: tell the assistant what question to
investigate and what tool findings can support its answer. Our skills use a
supplied Python evidence package. The team can change the questions for its
own INTAKE while keeping the evidence and stop rules explicit.

**Try it:** Rewrite the Analyze trigger for your own business output.
**Output:** One skill instruction with a clear input, output, and stop condition.

[Next: carry the findings into the PRD and ADRs](05-prd-and-architecture-decisions.md)
