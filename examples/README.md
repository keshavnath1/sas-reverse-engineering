# Team walkthroughs

These are the three examples to use when explaining or operating the project. They are not development milestone folders or a new automatic agent workflow.

| Walkthrough | What the team learns | Start here |
| --- | --- | --- |
| **SAS modernization** | Understand a SAS workload, reconstruct its evidence, and draft requirements and architecture with the five skills | [sas-modernization](sas-modernization/README.md) |
| **Running balance** | Run the exact supported draft Python candidate for the same public workload | [running-balance](running-balance/README.md) |
| **Governed continuation** | Review and approve a separate supported subject before its candidate publication | [governed-continuation](governed-continuation/README.md) |

Start with SAS modernization. Running balance is an optional execution demonstration, not independent SAS parity proof. Governed continuation is an advanced, separately scoped route; its approval is not interchangeable with another workload.

The required synthetic source, expected results and frozen replay packages live under [tests/fixtures](../tests/fixtures/README.md), organized by purpose. They are engineering support material, not more starting points. Nonessential trial snapshots are removed from this team tree and preserved in Git history. No private intake or newly generated run evidence is shipped here.

All examples retain draft authority and explicit proof limits. SAS reference and benchmark execution remain `NOT_RUN`; independent semantic verification remains `UNVERIFIABLE`, and semantic acceptance remains `BLOCKED`.
