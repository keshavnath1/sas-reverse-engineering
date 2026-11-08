# Public engineering fixtures

These files support existing commands and regression checks. They are not team onboarding instructions; use the [three walkthroughs](../../examples/README.md) instead.

| Group | Purpose |
| --- | --- |
| `source-reconstruction/` | Synthetic intake and agent-review sources, single-source and dependency-aware previews, and original offline/decision-review packages |
| `candidate-execution/` | Projection, projection-and-sort, preparation rules, population gates, combined scenarios, and fixed logistic-scoring inputs |
| `running-balance-workload/` | The original complete source/evidence/review package used by the bounded running-balance candidate |

Directory names describe their use. The retained source, expected-case, coefficient, evidence and frozen-package files are moved byte-for-byte, including internal names and original checkpoint identifiers. They must not be regenerated from candidate output to repair a mismatch. Some frozen Markdown links and status text describe the old checkpoint; inspect the [original tree](https://github.com/keshavnath1/sas-reverse-engineering/tree/36d9103746f8b12578125910dde67015e2347dd1/examples) for those original relative links. Current walkthroughs and skill references use the new locations. Do not treat fixture READMEs as the current team route.

The relocation changes explicit caller paths and implementation bytes. Only the two existing implementation pins for `scripts/migrate_preparation.py` and `scripts/migrate_population.py` are rebound to the reviewed path-only changes. `scripts/preparation_candidate.py`, source/evidence/package hashes, expected values, tolerance rules and refusal checks remain unchanged.

The projection replay test also binds a newly generated manifest whose bytes include the candidate script digest. Its historical manifest hash remains associated with the old revision, while the current test fixes the reviewed new manifest digest and adds separate assertions for the unchanged input-package and case-file hashes. This is an explicit provenance update, not a regenerated expected row or broadened acceptance criterion.

Fresh generated packages record the new path and code identities. Pre-relocation packages and their approvals retain their old identities and revision; they are not edited, promoted or transplanted to the new subject. Obtain fresh exact-byte approvals wherever the existing continuation requires them.

These are public synthetic engineering fixtures, not private business data, attributable SAS reference outputs, benchmark proof or production approvals. Unperformed SAS reference and benchmark execution remain `NOT_RUN`.
