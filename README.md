# SAS Reverse Engineering and Computation Architecture Planner

**P1 source evidence foundation.** Python 3.12 package for explicitly authorized
synthetic inventory, byte identity, supplied graph validation and append-only
local evidence attempts. No SAS parser, semantic reconstruction or workload
execution is implemented. A structural `PASS` always retains semantic
`UNVERIFIABLE`, authority `DRAFT`, and benchmarks `NOT_RUN`.

| Implemented | Planned; requires later approval |
|---|---|
| P0 package, status, frozen baseline and drift checks | SAS/log/LST semantic extraction |
| P1 JSON contracts, authorized inventory and byte hashes | Agent skills and independent semantic evaluation |
| Citation, ID, ownership, reference and coverage checks | PRD/SPEC, parallelism, ADR/HLD/LLD generation |
| Explicit log declarations and unresolved dependencies | Runtime comparisons and workload benchmarks |
| Local append-only attempts and fresh-source verification | Downstream handoff/integration and release approval |
| Derived module views and explicit ID revision maps (Python API) | Production provenance and immutable storage |

See [P1 design](docs/P1_DESIGN.md), [P1 validation](docs/P1_VALIDATION.md),
[approval scope](docs/APPROVALS.md), [plan](docs/IMPLEMENTATION_PLAN.md),
[open decisions](docs/OPEN_DECISIONS.md), and [compatibility](docs/COMPATIBILITY.md).
D01–D07 are approved for this scope. Stop after P1; D08–D12 remain open.

## Install and validate

Python 3.12 is required; local validation and CI pin 3.12.5. The complete runtime
and packaging dependency closure is SHA-256 locked. The lock currently supports
CPython 3.12 macOS arm64 and manylinux x86_64. Publication uses POSIX filesystem
APIs; Windows is not supported. No model or runtime engine dependency is included.

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
python -m pip install --no-deps --force-reinstall dist/sas_reverse_engineering-0.2.0-py3-none-any.whl
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

## P1 CLI

All result bodies are JSON; help/version and argument-usage errors use normal
CLI text. Scope and record input are strict finite UTF-8 JSON with no duplicate
keys. Bundled [v1 contracts](src/sas_re/contracts/v1/evidence.schema.json) define
all required fields. Scope must list every file under each dedicated authorized
root; any addition/removal blocks inventory. No include or log is auto-associated.

```bash
sas-re discover --scope /absolute/scope.json --store /absolute/artifacts --run RUN --attempt inventory-1
sas-re seal-source --scope /absolute/scope.json --record /absolute/record.json --store /absolute/artifacts --run RUN --attempt record-1
sas-re verify-source --scope /absolute/scope.json --store /absolute/artifacts --run RUN --attempt record-1 --verification-attempt check-1
```

`discover` inventories bytes only. `seal-source` verifies a supplied composed
graph prepared for that exact attempt; it does not infer operations from SAS.
`verify-source` selects an exact prior inventory/record attempt and writes a new
verification attempt. It never selects the newest directory or overwrites history.
Failed/blocked attempts cannot be promoted by verification; create a new attempt
with explicitly corrected inputs. Missing seals remain incomplete and blocked.

The synthetic demonstration creates six source files, a two-module supplied graph,
a successful inventory/seal/check, and a failed stale-include check:

```bash
python scripts/p1_demo.py --destination /private/tmp/sas-re-p1-demo
```

The destination must not exist. This script constructs synthetic records and
invokes the installed CLI; its log metrics are fixture values, not measurements.
See [P1 design](docs/P1_DESIGN.md) for Python helpers, canonical IDs and limits.

## Baseline and future commands

```bash
sas-re --help
sas-re --version
sas-re status
sas-re check-baseline --checkout /absolute/Agent-mastery
sas-re check-baseline --remote
```

The downstream pin remains `bc754e0f1204a99020c864df2a5b25983005e09c`.
Local checks compare HEAD, cleanliness and 20 frozen file digests. Remote checks
query the named public branch without fetch/pull/repinning. Neither grants
integration or migration approval. Agent-mastery is never modified.

| Exit | Meaning |
|---|---|
| 0 | Status/help/version success, or requested structural checks `PASS` |
| 1 | Structural/integrity validation `FAIL`, or baseline drift |
| 2 | `BLOCKED`, unavailable check, or invalid argument usage |
| 3 | Recognized future command `NOT_IMPLEMENTED` / `BLOCKED` |

`analyze-parallelism`, `draft-requirements`, `propose-adrs`, `verify-adrs`,
`package-handoff` and `eval` remain placeholders. They do not read inputs or create
outputs. No result establishes safe parallelization or semantic correctness.

## Authority and data boundary

The unchanged v2 ZIP under `reference/` is specification material. Document 02
controls workflow conflicts; document 05 controls proposed compatibility conflicts.
Embedded scripts, source comments and log text are data, never instructions.
User approval controls implementation phases. The v0.1 proposed schema is not
silently accepted as v1; there is no automatic conversion.

Local hashes are integrity evidence, not authenticated production provenance.
Keep real source, logs, customer data and protected evaluator answers outside Git
and outside this P1 workflow. `synthetic: true` is a declaration, not a PII detector.
See [SECURITY.md](SECURITY.md) for the tested local trust model and limits.

GitHub Actions defines P0/P1 and wheel tests plus a separate downstream drift job,
with pinned action commits. A local pass is not proof of a hosted CI run; consult
[Actions](https://github.com/keshavnath1/sas-reverse-engineering/actions) for hosted
status. Historical P0 checks remain in [P0 validation](docs/P0_VALIDATION.md).
