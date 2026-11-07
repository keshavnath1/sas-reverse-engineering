# SAS Reverse Engineering and Computation Architecture Planner

## Use the agent skills

Open this repository as the agent's working directory. Use
[`$sas-reconstruct`](skills/sas-reconstruct/SKILL.md) for the fixed synthetic
trace, [`$sas-specify`](skills/sas-specify/SKILL.md) for requirements review,
or [`$sas-architect`](skills/sas-architect/SKILL.md) to compare the existing
Python and Spark proposals. Keep review notes separate from generated evidence.
For explicit file-based use, ask the agent to read the linked `SKILL.md`.

The three authoritative definitions live in `skills/`. The repository-local
`.agents/skills -> ../skills` link exposes them to Codex without copying
instructions or changing user configuration. Live discovery was observed on the
installed macOS Codex CLI from this repository and its `scripts/` directory.
The parent workspace does not discover this nested repository automatically.
Hosts that do not materialize the link can still read the canonical files
explicitly. [Observed validation and remaining qualification limits](docs/SK1_VALIDATION.md).

Skills guide evidence review and bounded reasoning. The deterministic Python
engine owns reconstruction, validation, hashing and diagnostics. Developers
can continue to invoke it directly with the command below, offline and without
an AI provider. These skills cover the fixed public fixture and preserve the
DRAFT / UNVERIFIABLE / BLOCKED / NOT_RUN statuses.

## Run the offline review

Open the [sample review folder](examples/offline-review/README.md) to read the
workflow, compare the native Python and Spark proposals, and trace each decision
to synthetic source and behavioral controls.

To regenerate all ten files, run this from the development checkout with its
prepared Python 3.12 environment active:

```bash
python3.12 -IB scripts/review_workflow.py --destination /tmp/sas-re-review
```

The command prints the path to the generated README and the SHA-256 of
`MANIFEST.json`. Choose a new direct child of system scratch for each run,
named `sas-re-review` or `sas-re-review-<label>`. If your shell selects a
different interpreter, substitute `.venv/bin/python3.12` from the prepared
environment. No network, runtime Git command, model provider or SAS execution
is needed. [Validation and preservation checks](docs/REVIEW_WORKFLOW_VALIDATION.md).

This developer demonstration runs only the fixed public fixture. Reconstruction
is partial because the include is unresolved. Real-source intake, broader SAS
syntax, native Windows qualification and independent semantic evaluation need
separate authorization. Review this package's usability before choosing the
next capability.

## Review the architecture decision

The [MVP-4 decision review](examples/mvp4/DECISION_REVIEW.md) connects all 17
public behavioral controls to the original operations and to separate obligations
for native Python and Spark. The matrix identifies which errors the checker
caught, what remains unknown, and which tests or human decisions each proposal
still needs. Production runtime selection is BLOCKED.
[Reproduce the review and inspect its validation](docs/MVP4_VALIDATION.md).

## Check the synthetic workflow's behavior

The [MVP-3 tie-out report](docs/MVP3_VALIDATION.md) compares fixed Python
candidates with independently frozen expected rows at the SORT, DATA and SQL
boundaries. Its 17 cases show which changes lose duplicates, break input order
or incorrectly reject a legal SQL tie permutation. Inspect one discrepancy
offline with `python3.12 -IBS scripts/mvp3_tieout.py --case B09-lost-duplicate-match`.
The missing include keeps full-workflow acceptance BLOCKED.

## Follow a dataset across two SAS modules

The [MVP-2 architecture preview](examples/mvp2/ARCHITECTURE.md) follows
`work.ordered` from a sort in `prepare` through a BY-group DATA step and an
SQL join in `enrich`. The [module specifications](examples/mvp2/MODULES.md)
trace individual columns to original source spans. A missing include leaves the
reconstruction partial. The [native Python](examples/mvp2/ADR_NATIVE.md) and
[conditional Spark](examples/mvp2/ADR_SPARK.md) proposals compare both
candidates against the same per-dataset tie-out obligations. See the
[draft PRD](examples/mvp2/PRD.md), [evidence index](examples/mvp2/EVIDENCE.md)
and [validation report and offline run command](docs/MVP2_VALIDATION.md).

## Review the synthetic architecture preview

Start with the [draft PRD](examples/mvp1/PRD.md). The public workflow sorts
`work.a` into `work.sorted` on `key, subkey`. A DATA step reads the intermediate
in BY order, assigns `y = x / 2` and writes `work.final`. The [module specification](examples/mvp1/MODULES.md)
points to the original file, lines and byte ranges. The [architecture diagram](examples/mvp1/ARCHITECTURE.md)
shows the DATA and ORDER edges and the DATA step's STATE self-edge. Tied rows,
missing values and BY groups crossing a partition boundary need different tests.

Compare the [native Python baseline](examples/mvp1/ADR_NATIVE.md) with the
[conditional Spark alternative](examples/mvp1/ADR_SPARK.md). Both use the same proposed
row, order and numeric checks. Spark also needs evidence that distribution is worthwhile
and that a partition boundary preserves group state. Follow an O or E link to its
[canonical ID and evidence](examples/mvp1/EVIDENCE.md). OBSERVATION means the graph
contains a record. Operations and edges for this fixture carry the original
INFERENCE classification. There are no execution measurements or selected runtime.

From this development checkout and its existing Python 3.12 environment:

```bash
.venv/bin/python -IB scripts/mvp1_demo.py --destination /tmp/sas-re-mvp1-review
```

Choose a fresh `/tmp/sas-re-mvp1-<label>` for each run. The POSIX demonstration
accepts only a new direct child of system scratch reserved for disposable development
output. It reads the fixed [public fixture](tests/p2a_expectations.py) named
`sort_and_producer_consumer`, recreates the scope in a private temporary directory,
and uses the existing P1 inventory, P2A reconstruction and source-consistency check.
It pins the historical graph SHA-256, runs P3-A1 diagnostics and prints an
`UNVERIFIED` manifest with the size and SHA-256 of each Markdown file. The demo
needs no Git command, network, model provider or SAS runtime. It has no intake
path or evidence store parameter. Its only persistent outputs are the six new files.

The private renderer accepts two in-memory objects, an exact graph and its
diagnostic. It revalidates the graph and recomputes the entire diagnostic. In
addition to P3-A1's JSON guards, it limits the graph/diagnostic to 256/512 KiB,
8 operations, 24 edges, 80 nodes, 64 facts and 32 issues. It projects selected
sort/input/BY/assignment facts and keeps other fact kinds as review references.
The fixed example has no SQL step. Each file records DRAFT authority, UNVERIFIABLE
semantics, BLOCKED independent acceptance and benchmarks NOT_RUN.

### MVP-1 validation

- The [source expectations](tests/preview_expectations.py) were frozen before
  rendering (SHA-256 `37e9650c48eb76610d957995d533b50c2662847f8167895094590813053efc56`).
  These and the golden preview are public development checks. The independent
  semantic evaluation gate remains open for separate authorization.
- The demo reproduced the historical graph SHA-256
  `385423530208b08635de832bed57698b7278490f2cb7a43f08fd754b80df9155`
  on macOS 26.6.2 ARM64, CPython 3.12.5. Two fresh destinations produced
  byte-identical output. A run with an empty executable search path and monitored
  Python socket/process events also completed. Native Windows evidence I/O remains BLOCKED.
- Review exposed three presentation errors. The renderer now distinguishes a
  DATA-only cycle from state feedback, reports missing DATA coverage only for RAW
  conflicts, and names individual columns when only column IDs are present.
  The first golden comparison ran before the samples existed and failed on
  missing files. The committed samples are generated by the same demo.
- Preservation replays compared 15 P1 files, 15 P2A files and both complete
  reports against the approved baseline and the retained WS-1 sets. All bytes
  matched. The eight frozen hashes, P3-A1 module/test/vector hashes and downstream
  pin matched. An auxiliary replay check initially expected a nonexistent phase
  field in a retained manifest. A span check initially used the scratch copy that
  the historical stale-source demo intentionally edits. Reading the manifest in its
  recorded order and the original public fixture resolved both checks. All seven
  operation/fact spans and their source, span and excerpt hashes matched.
- Local macOS passed all 722 prior tests and 13 focused tests
  (735 total). Use `python -m unittest discover -s tests -v` for all regressions,
  or `python -m unittest discover -s tests -p test_draft_preview.py -v` for
  the focused tests. Mermaid checks cover the generated flowchart grammar and
  graph references; native Windows execution and runtime benchmarks were not attempted.

## Evidence foundation

**P2A deterministic reconstruction foundation.** Python 3.12 package for explicitly
authorized synthetic SAS evidence, canonical graph v2 and append-only attempts.
CP1 adds import-safe platform selection and explicit filesystem capabilities;
native Windows evidence I/O remains BLOCKED.
CP2 adds pure validation of separately versioned local authorization declarations
and an exact legacy identity projection; it grants no filesystem access.
CP3A adds a separate POSIX read-only preflight API for explicitly scoped synthetic
sources, with retained handles and physical disjointness inside a dedicated
inspection anchor. Existing evidence CLI/persistence behavior is unchanged.
CP3B adds a private Windows retained-handle protocol and native API adapter with
unit-only synthetic coverage. Public Windows read-only access remains BLOCKED:
approved physical-volume bootstrap and actual native qualification are missing.
See [CP3B design](docs/CP3B_DESIGN.md) and [validation](docs/CP3B_VALIDATION.md).
CP3C documented native qualification requirements. CP3D added a private
metadata protocol and bounded DOS-mapping primitives tested with synthetic
in-memory fixtures. Native bootstrap, public Windows source access and Windows
publication are still BLOCKED. See [CP3D design](docs/CP3D_DESIGN.md) and
[validation](docs/CP3D_VALIDATION.md).
The closed subset is described in [P2A design](docs/P2A_DESIGN.md). Public regression
tests demonstrate bounded behavior; independent semantic acceptance remains
`BLOCKED`, verification `UNVERIFIABLE`, authority `DRAFT`, and benchmarks `NOT_RUN`.

| Implemented | Planned; requires later approval |
|---|---|
| Three fixed-fixture reconstruction, specification and architecture skills | Analysis, validation and handoff skills |
| P0 package, status, frozen baseline and drift checks | Model/provider adapters |
| Preserved P1 contracts, authorized inventory and byte hashes | P2B protected-gold independent semantic evaluation |
| Citation, ID, ownership, reference and coverage checks; private synthetic MVP-1 preview | Operational PRD/SPEC, parallelism, ADR/HLD/LLD generation |
| Explicit log declarations and unresolved dependencies | Runtime comparisons and workload benchmarks |
| Local append-only attempts and fresh-source verification | Downstream handoff/integration and release approval |
| Derived module views and explicit ID revision maps (Python API) | Production provenance and immutable storage |
| Canonical v2 with bounded DATA/SQL/macro/state/order facts | Full SAS language coverage and runtime parity |
| Fixed synthetic LOG/LST observations and deterministic source checks | Workload execution and measured performance |

See [P1 design](docs/P1_DESIGN.md), [P1 validation](docs/P1_VALIDATION.md),
[approval scope](docs/APPROVALS.md), [plan](docs/IMPLEMENTATION_PLAN.md),
[open decisions](docs/OPEN_DECISIONS.md), and [compatibility](docs/COMPATIBILITY.md).
D01–D07 and D08-A/B are approved for their bounded phases. CP1 is separately
approved for its capability boundary. CP2 is separately approved for pure local
declarations and identity compatibility only. CP3A is separately approved for
bounded POSIX preflight. CP3B and CP3D have separate, limited approvals for
private Windows work. The user accepted the [post-CP3D roadmap](docs/POST_CP3D_ROADMAP.md)
at `dba5b3aa5a60ef384bfc57a90b46ca72ea4f27dc` and approved P3-A1 alone as a
private engineering experiment before P2B.
D08-C and D09 remain open for P2B. See [P2A validation](docs/P2A_VALIDATION.md)
and [public fixture review](docs/P2A_FIXTURE_REVIEW.md).

## Inspect an installed workstation package (WS-1)

The launcher accepts one argument on macOS Terminal/Bash or Windows Git Bash.
`KIT` denotes the absolute directory containing the externally authenticated
`workstation.sh`. Start it with a trusted Bash and parent environment with
`BASH_ENV` unset. Verify the launcher's original bytes through the trusted
delivery channel before Bash reads it.

```bash
bash "$KIT/workstation.sh" --help
bash "$KIT/workstation.sh" --version
bash "$KIT/workstation.sh" status
```

The [repository launcher](scripts/workstation.sh) ships with empty approval fields.
A valid argument therefore exits 2 with a bootstrap `BLOCKED` diagnostic on
stderr. Dispatch requires an independently authenticated kit that pins the
installation inventory and binds the exact native interpreter and installed package.
`SAS_RE_PYTHON` may match the approved executable. Setting it cannot approve
an installation. Extra arguments, paths and unsupported commands produce a
usage diagnostic on stderr and exit 2 before interpreter selection.

After a successful bootstrap, the installed module supplies the output and exit
status. Help and version are text. Status reports capabilities as JSON. The
historical macOS wheel supplies development comparison data. Workstation release
approval is open, and native Windows qualification is `BLOCKED / NOT_RUN`. See
the [WS-1 design](docs/WS1_DESIGN.md) and [validation record](docs/WS1_VALIDATION.md).

## P3-A1 private dependency and blocker diagnostics

P3-A1 binds a supplied public synthetic canonical v2 graph to its expected digest
and reports represented dependency paths, cycles, conservative read/write
conflicts and missing proof. A missing path leaves independence unproved.
Diagnostics operate in memory. The public `analyze-parallelism` command stays a
placeholder (exit 3). See the [private design](docs/P3_A1_DESIGN.md) and
[validation of the roadmap's A01–A26 obligations](docs/P3_A1_VALIDATION.md).

The result carries DRAFT authority, UNVERIFIABLE verification, BLOCKED semantic
acceptance and NOT_RUN benchmarks. Operational P3 requires independent source
and graph acceptance followed by draft PRD/module specifications and separate
approval. Scheduling, P3-A2, P4, P2B execution, CP4/CP5, private SAS intake
and downstream changes are outside P3-A1. Stop after validation for user review.

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

## CP2 pure authorization declarations

The additive [CP2 contract and API](docs/CP2_DESIGN.md) separate logical declarations
from native local root strings. They preserve the existing logical scope hash
through the explicit `sas-re-scope-v1` projection. See [actual validation and
qualification limits](docs/CP2_VALIDATION.md) and [public synthetic vectors](tests/cp2_vectors.py).

```python
from sas_re.authorization import (
    validate_authorization, project_logical_scope, authorization_scope_identity,
)

# envelope is an already supplied dictionary; this API does not open a path.
validate_authorization(envelope, expected_platform="windows")
logical_hash_input = project_logical_scope(envelope)
scope_sha256 = authorization_scope_identity(envelope)
```

`parse_authorization(raw_bytes)` also validates strict UTF-8 JSON bytes supplied
by the caller. `load_authorization_schema()` returns the new bundled input schema.
No filesystem bindings are applied and no existing evidence CLI accepts this
envelope. Success validates declarations only: human approval is NOT_VERIFIED,
physical authorization is not established, and Windows evidence I/O stays BLOCKED.
Store actual envelopes outside Git, for example under the already ignored `local/`.
The API works without Git, Docker, cloud services or any AI provider; native Windows
execution remains unqualified until an approved actual environment is tested.

## CP3A read-only POSIX preflight

See [CP3A design](docs/CP3A_DESIGN.md) for the `LocalInspectionPolicy` and
`open_preflight(envelope, policy=...)` API, and [actual validation](docs/CP3A_VALIDATION.md)
for qualified environments and limits. A trusted caller supplies the independent
exact inspection policy; validated CP2 strings never become human approval.

The new path retains directory/file handles, checks physical root/store
disjointness on a qualified filesystem beneath an explicit owned anchor, rejects
undeclared directories before descent, and acquires every read handle before
reading any source byte. It returns original bytes only; no output store is
created, even on success. Unsupported mounts, missing rights or uncertain bindings
are BLOCKED. Quiescent synthetic fixtures and trusted effective writers are
required; mode checks are not an ACL audit or hostile-writer snapshot guarantee.

This additive Python API is not integrated into the legacy commands below.
Their existing append-only failure timing remains unchanged. Future publication
integration needs separate review; a completed preflight is not a reusable create
permission. CP3B adds only a private Windows protocol: `sas-re status` reports
`read_only_preflight_capabilities` separately from full evidence capabilities.
Windows has no public preflight factory or override. Even the private subset
blocks absent store prefixes because a missing long name is not proof of physical
absence. No dependency, native support or broader filesystem claim is added.

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

## P2A CLI

Declare the synthetic input schemas/rows, ordered entrypoints, missing-join policy
and exact observation bindings in an authorized CONFIG JSON file using the
[v2 Profile contract](src/sas_re/contracts/v2/evidence.schema.json). Its original
bytes become part of the P1 inventory. Profile arguments are scoped file keys,
not arbitrary filesystem paths. All real/private intake remains excluded.

```bash
sas-re discover --scope /absolute/scope.json --store /absolute/artifacts --run RUN --attempt inventory-1
sas-re reconstruct-source --scope /absolute/scope.json --store /absolute/artifacts --run RUN --attempt reconstruct-1 --inventory-attempt inventory-1 --profile-file synthetic:profile.json
sas-re check-reconstruction --scope /absolute/scope.json --store /absolute/artifacts --run RUN --attempt reconstruct-1 --verification-attempt check-1 --profile-file synthetic:profile.json
```

The last two commands deliberately exit **2/BLOCKED**, even for a supported
complete reconstruction with `source_consistency: PASSED`: independent semantic
acceptance requires P2B. Unsupported evidence yields explicit unknowns/PARTIAL;
contradictions or invalid claims yield FAIL. The deterministic checker shares
reconstruction logic and is not an independent evaluator. V1-to-v2 lineage is
recorded when `--inventory-attempt` selects a sealed P1 RECORD instead of inventory.

Run the reviewed public synthetic demo in a new directory:

```bash
python scripts/p2a_demo.py --destination /private/tmp/sas-re-p2a-demo
```

It checks inventory, reconstruction, fresh-source validation, and an expected
stale-source failure after a synthetic edit; old seals stay unchanged. The wrapper
exits 0 when these expected outcomes occur. No SAS or generated program is run.

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
Local checkout checks are BLOCKED on Windows before path resolution or Git;
remote checks remain separately opt-in and require Git/network availability.

`status` includes `filesystem_capabilities`: backend, platform, required primitive
availability and denial reason. `AVAILABLE` means implementation prerequisites
exist; it is not a filesystem qualification or stage PASS. Windows reports
`WINDOWS_BACKEND_NOT_IMPLEMENTED`. All five evidence commands return their existing
P1/P2A report shape, fixed `FILESYSTEM_CAPABILITY_UNAVAILABLE` finding and exit 2
before opening the scope, record, profile or source, or creating a store.
Missing POSIX primitives and unknown platforms also fail closed; there is no
force-backend option or ordinary-file-operation fallback.

With an already approved installed Python environment, pure module commands are
`python -m sas_re --help`, `python -m sas_re --version` and
`python -m sas_re status`. Bundled schemas can be inspected through
`sas_re.contracts.load_schema("1.0")` / `load_schema("2.0")`; this reads trusted
package resources only and grants no semantic authority. No new schema-inspection
CLI, model, editor, Docker, WSL or cloud requirement is introduced by CP1.

| Exit | Meaning |
|---|---|
| 0 | Status/help/version success, or requested structural checks `PASS` |
| 1 | Structural/integrity validation `FAIL`, or baseline drift |
| 2 | `BLOCKED`, unavailable check, or invalid argument usage |
| 3 | Recognized future command `NOT_IMPLEMENTED` / `BLOCKED` |

`analyze-parallelism`, `draft-requirements`, `propose-adrs`, `verify-adrs`,
`package-handoff` and `eval` remain placeholders. They do not read inputs or create
outputs. No result establishes safe parallelization or independently verified
semantic reliability.

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

GitHub Actions defines P0/P1/P2A and wheel tests plus a separate downstream drift job,
with pinned action commits. A local pass is not proof of a hosted CI run; consult
[Actions](https://github.com/keshavnath1/sas-reverse-engineering/actions) for hosted
status. Historical P0 checks remain in [P0 validation](docs/P0_VALIDATION.md).
