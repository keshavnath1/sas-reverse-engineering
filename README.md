# SAS Reverse Engineering and Computation Architecture Planner

Understand legacy SAS logic and dependencies before deciding what to
modernize. The repository turns authorized source into traceable evidence
and draft designs, with executable Python for explicitly supported workloads.

**Start here:** [Team reading path](#team-reading-path) ·
[Public INTAKE walkthrough](#run-the-public-walkthrough) ·
[Five Copilot skills](#use-the-five-skills) ·
[Scope and evidence](#scope-and-evidence) ·
[Engineering references](#engineering-references)

## Team reading path

For people learning or presenting this repository, read the following existing guides in order. This is a **human reading path**, not a new agent execution order; agents still follow `AGENTS.md` and the applicable skill and operator contracts.

1. **This README:** the core idea, current workflow, five skills and supported starting commands.
2. **[AGENTS.md](AGENTS.md) and [SECURITY.md](SECURITY.md):** operating rules, authorized input, human decisions and safety boundaries.
3. **[Architecture](docs/ARCHITECTURE.md):** how evidence becomes requirements and design, who owns each part, and how optimization choices are challenged.
4. **[Detailed INTAKE guide](docs/GOAL4B_P2A_INTAKE.md):** the existing operator steps, evidence handoff, citation preflight and script diagrams.
5. **Only the example you need:** [modernization](examples/modernization/README.md) for design review; [running-balance](examples/running-balance/README.md) for its exact supported draft engineering runner; or [projection/SORT](examples/intg1/README.md) for its separate approval-gated route.

For a design discussion, start with items 1–3. When running the walkthrough, also use the [installation instructions](#install-and-validate) and the relevant operator/example guide. You do not need to read every validation report or milestone plan first. Historical engineering records remain available [on demand](#engineering-history-and-qualification-plans).

## The core design, in plain language

**Recover what SAS does, identify what must be preserved, and design how the modern system should execute it.** Preserve business behavior, not every SAS block or incidental serial step.

**Python tools reconstruct supported source and bind its evidence. Copilot skills interpret that evidence and draft requirements/design. Humans confirm intent and review the decisions.** Execution is available only through the existing supported candidate contracts and their applicable approval routes.

```text
Authorized scope → existing Python reconstruction → evidence / TRACE / MAP
    → five existing skills → draft requirements, specifications and architecture
    → human review → supported candidate route, or stop with explicit gaps
```

The [architecture guide](docs/ARCHITECTURE.md#what-the-existing-design-is-trying-to-achieve) explains PRD, module specifications, HLD/LLD and ADRs, using an illustrative scenario example. It also separates preserved behavior from optimized execution and future correctness/performance proof. Those details are kept there rather than repeated across onboarding documents.

This branch preserves the scripts, package, five skills, tests and runtime contracts from `design/team-handoff`: no replacement engine, new orchestration workflow, renamed skills or new checkers. The handoff is human-invoked; it is not an autonomous intake-to-package driver. Nonessential historical documents and Copilot trial outputs are removed from this branch's current tree and retained in the original branch/history. Execution-dependent records remain for compatibility.

## Jim Thompson's practices: how to use the existing repo

We adapt selected practices recorded in the [attributed practice ledger](https://github.com/keshavnath1/sas-reverse-engineering/blob/eb9794167339d1991800c290a2b24ac10a57edf8/docs/BEST_PRACTICES_ADOPTION.md#sources-and-attribution). In everyday use:

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
records](https://github.com/keshavnath1/sas-reverse-engineering/blob/eb9794167339d1991800c290a2b24ac10a57edf8/docs/SK2_VALIDATION.md) describe observed discovery and use.
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
I/O remains blocked. See [platform validation](https://github.com/keshavnath1/sas-reverse-engineering/blob/eb9794167339d1991800c290a2b24ac10a57edf8/docs/CP1_VALIDATION.md) for
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

The team guides above explain today's workflow. The references below support a specific contract, restriction or engineering question; they are **not another onboarding sequence**.

| Repository area | What to look for |
| --- | --- |
| `scripts/` | The guides identify the operator commands. The same directory also holds internal helpers, candidate runners, CI utilities, and earlier replay commands. |
| `src/sas_re/` | Core Python implementation for inventory, reconstruction, evidence checks, and diagnostics. |
| `tests/` | Engineering expectations, compatibility checks, and reproducible replays. |
| `docs/` | Two main team guides plus the retained contract, boundary and compatibility-reference files listed below. |
| `examples/` | Existing public examples and supported continuation guides; their execution contracts are unchanged. |

### What remains in docs

The folder is reduced to **13 Markdown files**. `docs/goal4c/` and nonessential milestone/test reports are not shipped in this tree; their links below point to the immutable original version.

- **Team guides:** `ARCHITECTURE.md` and `GOAL4B_P2A_INTAKE.md`.
- **Contract and boundary references:** `COMPATIBILITY.md`, `P2A_DESIGN.md`, `P3_A1_DESIGN.md`, `APPROVALS.md`, `CP3_READINESS.md` and `WS1_VALIDATION.md`.
- **Engineering compatibility references:** `MVP3_VALIDATION.md`, `P2A_FIXTURE_REVIEW.md`, `P3_A1_VALIDATION.md`, `PY1_VALIDATION.md` and `SM3B_VALIDATION.md`. These support existing execution, fixture metadata, script documentation or the retained example—not new user stages. `MVP3_VALIDATION.md` remains byte-for-byte unchanged because an existing runner checks its hash.

### Active references and continuing limits

- **Source and dependency contracts:** [inventory design](https://github.com/keshavnath1/sas-reverse-engineering/blob/eb9794167339d1991800c290a2b24ac10a57edf8/docs/P1_DESIGN.md), [supported reconstruction forms](docs/P2A_DESIGN.md) and [dependency-diagnostic boundaries](docs/P3_A1_DESIGN.md). Consult them for the applicable skill or engineering question, not as extra user stages.
- **Compatibility and platform limits:** [downstream pin](docs/COMPATIBILITY.md), [platform validation](https://github.com/keshavnath1/sas-reverse-engineering/blob/eb9794167339d1991800c290a2b24ac10a57edf8/docs/CP1_VALIDATION.md), [platform readiness checkpoint](docs/CP3_READINESS.md) and [workstation validation](docs/WS1_VALIDATION.md). Read their dates, subjects and limits; native Windows evidence I/O remains blocked.
- **Authority:** [repository rules](AGENTS.md), [security](SECURITY.md) and the [chronological scope-approval ledger](docs/APPROVALS.md). Historical engineering authorization is not a new workload, architecture, runtime or release approval.

### Engineering history and qualification plans

Use these records when investigating an implementation decision, recorded check or open qualification question. They do not need to be loaded wholesale into a Copilot session.

- **How the implementation developed:** [historical implementation plan](https://github.com/keshavnath1/sas-reverse-engineering/blob/eb9794167339d1991800c290a2b24ac10a57edf8/docs/IMPLEMENTATION_PLAN.md) and dated P/CP/WS/MVP/SK/SM/TF records in the [original documentation tree](https://github.com/keshavnath1/sas-reverse-engineering/tree/eb9794167339d1991800c290a2b24ac10a57edf8/docs). These are not copied into the team branch unless an existing consumer needs them. Each record retains its own commit, platform, commands and proof boundaries.
- **Historical public demonstrations:** [original offline review](examples/offline-review/README.md), [public behavioral validation](docs/MVP3_VALIDATION.md), [recorded skill discovery/use](https://github.com/keshavnath1/sas-reverse-engineering/blob/eb9794167339d1991800c290a2b24ac10a57edf8/docs/SK2_VALIDATION.md) and [one corrected public design-review approval](https://github.com/keshavnath1/sas-reverse-engineering/blob/eb9794167339d1991800c290a2b24ac10a57edf8/docs/goal4c/README.md). These do not establish universal SAS equivalence or approval for another workload.
- **Plans and unresolved decisions:** [open decisions](https://github.com/keshavnath1/sas-reverse-engineering/blob/eb9794167339d1991800c290a2b24ac10a57edf8/docs/OPEN_DECISIONS.md), [independent-evaluation readiness](https://github.com/keshavnath1/sas-reverse-engineering/blob/eb9794167339d1991800c290a2b24ac10a57edf8/docs/P2B_READINESS.md), [workstation/offline-kit planning](https://github.com/keshavnath1/sas-reverse-engineering/blob/eb9794167339d1991800c290a2b24ac10a57edf8/docs/WS2A_OFFLINE_KIT_PLAN.md) and [SAS-reference/benchmark follow-up](https://github.com/keshavnath1/sas-reverse-engineering/blob/eb9794167339d1991800c290a2b24ac10a57edf8/docs/GOAL1_REFERENCE_AND_BENCHMARK_PLAN.md). A plan is not an executed result or a released capability.
- **Practice attribution and evidence:** [Jim Thompson practice ledger](https://github.com/keshavnath1/sas-reverse-engineering/blob/eb9794167339d1991800c290a2b24ac10a57edf8/docs/BEST_PRACTICES_ADOPTION.md). The team-facing usage explanation is in the [architecture guide](docs/ARCHITECTURE.md#using-jim-thompsons-practices-without-changing-the-workflow).

Historical links are pinned to `eb9794167339d1991800c290a2b24ac10a57edf8`, not a moving branch tip. The original branch and Git history are not deleted or rewritten. This cleanup removes documents only from the team's current tree; surviving historical-reference links point to their original bytes. It does not change test counts, approvals, schemas, operator commands or runtime behavior.
