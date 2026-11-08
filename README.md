# SAS Reverse Engineering and Computation Architecture Planner

Start with an authorized SAS INTAKE. Recover the logic and dependencies the
source supports, review the modernization design, and run an existing Python
candidate when the evidence matches its contract.

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

Open the generated `MODERNIZATION_REVIEW.md`, evidence graph, migration
profile and tie-out drafts. Review the scope, unresolved obligations and
pending decisions with the team. The
[public candidate guide](examples/running-balance/README.md#run-from-a-fresh-intake-review)
shows how to run the exact supported draft candidate from that evidence.

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

Python 3.12 is required; local validation and CI pin 3.12.5. The complete runtime
and packaging dependency closure is SHA-256 locked. The lock currently supports
CPython 3.12 macOS arm64 and manylinux x86_64. Publication uses POSIX filesystem
APIs. CP1 keeps pure commands and bundled contract inspection independent of the
POSIX backend, and rejects Windows evidence I/O before reading inputs. Actual
native Windows qualification is BLOCKED: no approved Windows environment was
available, and the lock has not been extended. No model or runtime engine
dependency is included. Git is needed only for development/repository checks and
explicit downstream drift checks, not ordinary installed core operations.

See [CP1 design](docs/CP1_DESIGN.md) and [CP1 validation](docs/CP1_VALIDATION.md)
for exact tested environments and limitations. No new Windows installation is
authorized by the following existing POSIX installation recipe.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --require-hashes --only-binary=:all: -r requirements.lock
python -m pip install --no-deps --no-build-isolation -e .
python -m pip check
python -m unittest discover -s tests -v
python scripts/check_repository.py
sas-re status
```

For offline installation, add `--no-index --find-links /path/to/wheels` to the
hash-locked install. Keep hash checking enabled. Run the repository guard after
staging new files; it checks index and working-tree content, not arbitrary PII.
Synthetic test files are generated in temporary directories from labeled Python
strings. No raw SAS/log/LST exception was added to Git exclusions.

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

## Technical and historical references

- [Original offline review](examples/offline-review/README.md) and
  [behavioral validation](docs/MVP3_VALIDATION.md)
- [Evidence inventory](docs/P1_DESIGN.md), [bounded reconstruction](docs/P2A_DESIGN.md)
  and [dependency diagnostics](docs/P3_A1_DESIGN.md)
- [Platform readiness](docs/CP3_READINESS.md) and [workstation launcher](docs/WS1_VALIDATION.md)
- [Compatibility and downstream pin](docs/COMPATIBILITY.md)
- [Approved public design review](docs/goal4c/README.md) and
  [reference and benchmark plan](docs/GOAL1_REFERENCE_AND_BENCHMARK_PLAN.md)
