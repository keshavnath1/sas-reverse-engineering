# SAS Reverse Engineering and Computation Architecture Planner

Understand legacy SAS logic and dependencies before deciding what to
modernize. The repository turns authorized source into traceable evidence
and draft designs, with executable Python for explicitly supported workloads.

**Start here:** [Architecture](docs/ARCHITECTURE.md) ·
[Public INTAKE walkthrough](#run-the-public-walkthrough) ·
[Five Copilot skills](#use-the-five-skills) ·
[Scope and evidence](#scope-and-evidence)

## The core design, in plain language

**Recover what SAS does, identify what must be preserved, and design how the modern system should execute it.** Preserve business behavior, not every SAS block or incidental serial step.

The existing Python tools first reconstruct the supported source subset into evidence, TRACE/MAP, dependencies and explicit gaps. The five existing skills use that evidence to draft requirements, analyze constraints, propose validation and compare architectures. Humans confirm intent and review design/configuration. Execution is available only through the existing supported candidate contracts and their applicable approval routes.

```text
Authorized scope → existing Python reconstruction → evidence / TRACE / MAP
    → five existing skills → draft requirements, specifications and architecture
    → human review → supported candidate route, or stop with explicit gaps
```

For example, an optimization proposal may share preparation or split scenarios, but only if ordering, state, multiplicity and producer-consumer constraints are preserved. Distributed designs remain proposals, not measured improvements. Read [the design explanation](docs/ARCHITECTURE.md#what-the-existing-design-is-trying-to-achieve) before the implementation details.

This branch preserves the functional `design/team-handoff` baseline. Its changes are explanation and navigation only: no replacement engine, new orchestration workflow, renamed skills or new checkers. The handoff is human-invoked; it is not an autonomous intake-to-package driver. Historical records and validation assets remain for compatibility, but are not the team's starting reading list.

## Jim Thompson's practices: how to use the existing repo

We adapt selected practices recorded in the [attributed practice ledger](docs/BEST_PRACTICES_ADOPTION.md#sources-and-attribution). In everyday use:

- **Inspect before planning:** follow `AGENTS.md`, declare the authorized scope and generate source evidence before asking the skills for a design.
- **Give the agent focused context:** supply the exact generated handoff and bound evidence to the five existing skills, rather than the whole historical archive.
- **Use feedback without weakening checks:** run the existing citation preflight and applicable engineering checks; correct the draft or candidate, not the acceptance rules.
- **Keep human decisions separate:** resolving citations, passing a test or receiving an AI review is not architecture approval or independent SAS equivalence.

See [practical usage and limitations](docs/ARCHITECTURE.md#using-jim-thompsons-practices-without-changing-the-workflow). This is guidance for using the current system, not a claim of complete adoption or an added agent/runtime feature.

## From INTAKE to modernization

1. **Scope the input.** Identify the entry point, authorized source files or
   spans, and any descriptors or run artifacts. Keep private material outside
   Git. The [multi-file operator example](examples/modernization/README.md)
   shows how to inventory and scope public synthetic inputs.
2. **Generate evidence.** Run the existing Python source-review tools to bind
   original bytes and produce TRACE/MAP, coverage and unresolved findings.
   The [multi-file INTAKE guide](docs/GOAL4B_P2A_INTAKE.md) covers literal
   includes, typed synthetic inputs, and draft configuration. For an authorized
   private source, use only the [bounded source-review tool](scripts/review_source.py)
   and its explicit source hash and selected spans.
3. **Review the design.** Use the skills below with the selected evidence to
   draft requirements, specifications, architecture, optimization hypotheses
   and validation obligations. Review the migration profile and tie-out drafts.
   Record business decisions and human approval separately from the evidence.
4. **Check candidate fit.** The [running-balance example](examples/running-balance/README.md)
   runs an exact supported public workload from fresh verified INTAKE evidence.
   The [projection and SORT guide](examples/intg1/README.md) shows a separate
   approval-gated route. Use the existing gate and exact-byte human approval
   where publication is gated. Unsupported workflows stop at review.

Python tools perform deterministic reconstruction, identity checks, diagnostics
and supported execution. Agent skills interpret the evidence and prepare drafts.
Human reviewers decide business intent, configuration and approval.

See the [architecture guide](docs/ARCHITECTURE.md) for component boundaries,
the evidence flow, and runtime decision criteria.

## Run the public walkthrough

After [installing the development environment](#install-and-validate), run
from the repository root on a supported POSIX host:

```sh
scratch=$(mktemp -d /tmp/sas-team-handoff-XXXXXX)
scratch=$(cd "$scratch" && pwd -P)

mkdir "$scratch/INTAKE"
cp examples/modernization/source/* "$scratch/INTAKE/"
evidence="/tmp/sas-re-int1-${scratch##*/}"
python3.12 -IB scripts/review_intake.py --p2a --modernization-drafts --intake "$scratch/INTAKE" --destination "$evidence"
```

The command generates `INVENTORY.json`, `EVIDENCE.json`, `MANIFEST.json`,
`MODERNIZATION_REVIEW.md`, and the migration profile and tie-out YAML drafts.
The example's [PRD and architecture review](examples/modernization/REVIEW.md)
is authored draft prose. To draft or revise it with Copilot, open a session
and supply the generated evidence and handoff yourself. Review the resulting
claims and configuration choices with the team.

The [source-review guide](examples/modernization/README.md) stops at design
review. The [running-balance guide](examples/running-balance/README.md)
covers a separate draft engineering runner for the same exact public inputs.
After generating evidence above, run it from the same shell:

```sh
evidence=$(cd "$evidence" && pwd -P)
python3.12 -IB scripts/run_running_balance.py --package "$evidence" --intake "$scratch/INTAKE"
```

Use these walkthrough commands on macOS. They resolve scratch paths before
passing them to commands that require canonical paths. The runner verifies
the source and evidence identities and emits JSON for preparation, SORT, and
enrichment. The approval-gated publication route described earlier has its
own supported contracts.

## Use the five skills

Open this repository as the agent's working directory and provide the selected
evidence package. Ask the agent to read the applicable skill files explicitly
if the host does not discover them.

| Skill | Deliverable |
| --- | --- |
| [sas-reconstruct](skills/sas-reconstruct/SKILL.md) | Source trace, dependency map and coverage gaps |
| [sas-specify](skills/sas-specify/SKILL.md) | PRD, functional requirements and module contracts |
| [sas-analyze](skills/sas-analyze/SKILL.md) | Dependency constraints and optimization hypotheses |
| [sas-validate](skills/sas-validate/SKILL.md) | Engineering checks, tie-out plan and independent reference obligations |
| [sas-architect](skills/sas-architect/SKILL.md) | HLD, LLD, ADRs and conditional runtime choices |

The canonical definitions live under `skills/`. The repository-local
`.agents/skills` link points to those same files. The [skill validation
records](docs/SK2_VALIDATION.md) describe observed discovery and use.
A generated handoff supports a human-invoked Copilot session. Record live
session activity only when observed.

## Scope and evidence

Separate source declarations, graph inferences, profile assumptions,
package metadata, proposed behavior and unknowns. Cite exact source locations
and use the selected package's manifest and evidence records. Public engineering
comparisons do not establish SAS equivalence or authorize production use.

Draft authority is `DRAFT`, independent semantic verification is
`UNVERIFIABLE`, and semantic acceptance is `BLOCKED` until independently
supported. Record unperformed SAS reference and benchmark execution as
`NOT_RUN`. See [repository rules](AGENTS.md), [security](SECURITY.md) and
[approval boundaries](docs/APPROVALS.md).

## Install and validate

Use Python 3.12 on a supported POSIX host. The dependency lock covers
CPython 3.12 on macOS arm64 and manylinux x86_64. Native Windows evidence
I/O remains blocked. See [platform validation](docs/CP1_VALIDATION.md) for
tested environments and limits.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --require-hashes --only-binary=:all: -r requirements.lock
python -m pip install --no-deps --no-build-isolation -e .
sas-re status
```

For offline installation, add `--no-index --find-links /path/to/wheels`
to the hash-locked dependency install.

For repository validation, run the following checks. The repository guard
checks tracked and staged content. Keep private SAS inputs outside Git.

```sh
python -m pip check
python -m unittest discover -s tests -v
python scripts/check_repository.py
```

Build and test the installed wheel from another directory:

```bash
python -m pip wheel --no-deps --no-build-isolation --wheel-dir dist .
python -m pip install --no-deps --force-reinstall dist/sas_reverse_engineering-0.3.0-py3-none-any.whl
# Set CHECKOUT to this checkout's absolute path before changing directories.
CHECKOUT="$PWD"
cd /private/tmp  # Linux: /tmp; avoid symlink aliases for authorized source roots.
python -m unittest discover -s "$CHECKOUT/tests" -v
sas-re status
python -c 'import sas_re; print(sas_re.__file__)'
```

The last path must identify installed site-packages for a wheel validation run.
The test files retain their checkout location for the P0 Git/reference tests;
the installed application must not import source code from that checkout.

## Engineering references

| Repository area | What to look for |
| --- | --- |
| `scripts/` | The guides identify the operator commands. The same directory also holds internal helpers, candidate runners, CI utilities, and earlier replay commands. |
| `src/sas_re/` | Core Python implementation for inventory, reconstruction, evidence checks, and diagnostics. |
| `tests/` | Engineering expectations, compatibility checks, and reproducible replays. |
| `docs/` and `examples/` | Current operator guides alongside preserved design, validation, approval, and demonstration records. |

Earlier implementation plans and milestone records describe their original
scope. Use the current [architecture guide](docs/ARCHITECTURE.md) and
operator walkthrough for today’s workflow.

- [Inventory design](docs/P1_DESIGN.md), [reconstruction coverage](docs/P2A_DESIGN.md)
  and [dependency diagnostics](docs/P3_A1_DESIGN.md)
- [Historical implementation plan](docs/IMPLEMENTATION_PLAN.md),
  [original offline example](examples/offline-review/README.md) and
  [public behavioral validation](docs/MVP3_VALIDATION.md)
- [Platform readiness](docs/CP3_READINESS.md), [workstation validation](docs/WS1_VALIDATION.md)
  and [compatibility and downstream pin](docs/COMPATIBILITY.md)
- [Recorded design approval](docs/goal4c/README.md) and
  [reference and benchmark plan](docs/GOAL1_REFERENCE_AND_BENCHMARK_PLAN.md)
