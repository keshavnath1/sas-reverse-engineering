# SAS modernization: understand first, design next

Start here to see the core project design on one public synthetic workload. SAS builds a running balance, creates a sorted output, and enriches the prepared rows with a lookup. The goal is to recover those behaviors and propose a modern execution design—not translate every SAS statement literally.

## The story

1. **Read the authorized SAS inputs.** The entry program includes two supporting files; scope and typed input profiles make the subject explicit.
2. **Generate source evidence.** The existing Python tools reconstruct supported operations, source coordinates, dependencies and coverage gaps.
3. **Ask the five skills to interpret it.** Copilot drafts requirements, module specifications, optimization hypotheses, a validation plan, architecture and ADRs.
4. **Make the human decisions.** Business intent, ordering, duplicate policy, runtime and acceptance criteria remain review decisions.
5. **Optionally run the exact supported candidate.** The [running-balance walkthrough](../running-balance/README.md) demonstrates draft Python execution for this same public workload. It does not establish independent SAS equivalence.

## Run source reconstruction

Use the repository's [Python 3.12 development environment](../../README.md#install-and-validate) on qualified macOS or Linux. Run from the repository root and choose a fresh destination:

```sh
scratch=$(mktemp -d /tmp/sas-modernization-XXXXXX)
scratch=$(cd "$scratch" && pwd -P)
mkdir "$scratch/INTAKE"
cp tests/fixtures/running-balance-workload/source/* "$scratch/INTAKE/"
evidence="/tmp/sas-re-int1-${scratch##*/}"
python3.12 -IB scripts/review_intake.py --intake "$scratch/INTAKE" --inventory
python3.12 -IB scripts/review_intake.py --p2a --modernization-drafts \
  --intake "$scratch/INTAKE" --destination "$evidence"
```

Open the generated `MODERNIZATION_REVIEW.md`, evidence and configuration drafts. Supply the selected package to a real Copilot Agent session, following [AGENTS.md](../../AGENTS.md) and the [five existing skills](../../README.md#use-the-five-skills). This handoff is human-invoked, not an automatic script that launches AI skills.

## What to show the team

| Question | Read or show |
| --- | --- |
| What did SAS do? | Generated TRACE/MAP, source-qualified spans and coverage gaps |
| What must be preserved? | Draft PRD, functional requirements and module contracts |
| What can change? | Dependency analysis, architecture alternatives and candidate ADRs |
| What still needs proof? | Validation plan, reference provenance and benchmark obligations |
| What can run now? | The separate bounded running-balance draft candidate |

The [recorded requirements and architecture review](../../tests/fixtures/running-balance-workload/REVIEW.md) is a frozen example, not approval for a new workload. Original package material remains byte-identical under `tests/fixtures/running-balance-workload/`; some embedded legacy links and status statements describe its original design-review checkpoint. Use this current guide and the running-balance guide for today's navigation and optional execution.

For a different supported projection-and-sort subject, the [governed continuation](../governed-continuation/README.md) describes its separate exact-byte review and approval route. Do not transfer its approval or applicability to the running-balance route.

**Proof boundary:** all input is public and synthetic. Business approval and runtime decisions remain pending; SAS reference execution and benchmarks remain `NOT_RUN`, semantic verification `UNVERIFIABLE`, and semantic acceptance `BLOCKED`. The two provisional parallel output branches are not measured performance evidence.
