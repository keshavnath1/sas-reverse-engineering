# SAS Reverse Engineering and Computation Architecture Planner

**P0 foundation only.** This local repository contains an installable Python 3.12
package, an honest status CLI, a read-only downstream baseline check, and scaffold
tests. It does not read or execute SAS workloads.

| Implemented in P0 | Planned, not implemented |
|---|---|
| Package and console entry point | Evidence inventory, sealing, schemas and validation |
| JSON status and explicit future-command rejection | SAS/log/LST reconstruction and dependency graphs |
| Frozen specification and downstream source metadata | Requirements, specifications, parallelism analysis |
| Local checkout and remote branch drift checks | Spark/Ray/Dask/native ADRs and HLD/LLD generation |
| Hash-locked packaging tools, local tests, CI definition | Agent skills, independent semantic evaluation, handoff integration |
| Git exclusions and tracked-file guard | SAS parity, workload benchmarks or release approval |

See [approval scope](docs/APPROVALS.md), [implementation plan](docs/IMPLEMENTATION_PLAN.md),
[open decisions](docs/OPEN_DECISIONS.md), and [compatibility boundary](docs/COMPATIBILITY.md).
The plan and open-decisions copies preserve the Step 1 record; APPROVALS.md records
the subsequent D01–D03 approval. P1 remains unapproved.

## Install and check

Python 3.12 is required; the tested patch version and CI baseline are 3.12.5.
The package permits 3.12.x only. No third-party runtime or test dependencies are
needed. `requirements.lock` pins pip, setuptools and wheel with SHA-256 wheel
hashes. Do not use an unpinned build-isolation environment for the acceptance run.

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

The repository guard inspects tracked/staged files; run it after staging newly
created files. It is an additional control, not a complete secret/PII detector.
The approved specification archive is the only permitted tracked ZIP, and its
exact hash is checked. No synthetic SAS fixtures are needed or allowed in P0;
future synthetic-source exceptions require a narrow policy change at P1.

Build and smoke-test the installed wheel separately:

```bash
python -m pip wheel --no-deps --no-build-isolation --wheel-dir dist .
python -m pip install --no-deps --force-reinstall dist/*.whl
cd /tmp
sas-re status
python -m sas_re --version
```

For an offline setup, obtain the three universal wheels using the locked versions,
then add `--no-index --find-links /path/to/wheels` to the hash-locked install. Hash
checking is still required. These pins reproduce the toolchain; OS, Git and Python
patch versions must also be recorded for any stronger reproducibility claim.

## CLI behavior

All result bodies are JSON; help/version use normal CLI text. The CLI works
outside the repository directory because baseline metadata is bundled in the
installed package. It neither creates run state nor advances a migration.

```bash
sas-re --help
sas-re --version
sas-re status
sas-re check-baseline --checkout /path/to/Agent-mastery
sas-re check-baseline --remote
sas-re check-baseline --checkout /path/to/Agent-mastery --remote
```

Local checks require the explicit checkout root. They compare HEAD, worktree
cleanliness and 20 frozen file digests. Remote checks query only the named public
branch ref; they never fetch, pull, change a checkout or repin metadata. A remote
match does not check local files. An offline failure is BLOCKED, not a match.

| Exit code | Meaning |
|---|---|
| 0 | Status/help/version success, or requested baseline checks passed |
| 1 | Baseline drift or repository guard failure |
| 2 | Invalid CLI usage or unavailable baseline check |
| 3 | Recognized future command is not implemented |

`discover`, `verify-source`, `analyze-parallelism`, `draft-requirements`,
`propose-adrs`, `verify-adrs`, `package-handoff` and `eval` return
`NOT_IMPLEMENTED` / `BLOCKED` with exit 3. Arguments to these placeholders are
not acted upon. They do not inspect the supplied paths, create outputs or report
successful evidence validation. Benchmarks remain `NOT_RUN`.

## Authority and data boundaries

The unchanged v2 ZIP is under `reference/`. It is specification material, including
proposed schemas and synthetic expected results, not installed executable features.
Never execute its embedded scripts as part of intake. Document 02 governs planned
workflow; document 05 governs proposed downstream compatibility. User approval
controls which phase can be implemented.

Agent-mastery remains pinned to `bc754e0f1204a99020c864df2a5b25983005e09c`.
Its approvals, canonical artifacts and pattern import remain downstream-owned.
A baseline PASS proves identity only, not compatibility of a future bundle or
authorization to implement a migration. P0 does not write to Agent-mastery.

Keep real intake and protected evaluator answers outside this repository. See
[SECURITY.md](SECURITY.md) for exclusions, limitations and reporting. No remote
repository is configured or published by this foundation step.

## Validation and next checkpoint

GitHub Actions defines separate foundation and remote-drift jobs using pinned
action commits. Remote drift is deliberately a failing check if the branch moves
or cannot be reached; it does not silently update the baseline. Hosted Actions
has not run until this local repository is published and a workflow executes.

See [P0 validation report](docs/P0_VALIDATION.md) for actual commands and results.
Stop at P0. Review D04–D07 and explicitly authorize P1 before implementing source
identity contracts or evidence validators.
