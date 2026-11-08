# Running the planner from a workstation

**Planning baseline:** `13a82fdb48248215548a57463aafc075edeb7e41`. **Recommendation:**
deliver one Bash launcher over the installed Python package. On macOS, use Terminal with
Bash; on Windows, use the existing Git Bash shell and **native Windows CPython**. Git Bash
is the shell distribution, not a Git workflow. A user should need neither a checkout nor
a Git command, Linux host/VM, WSL, Docker, cloud account, editor, AI provider or SAS runtime.

Start with **WS-1: inspect an already installed environment**. It should accept just
`--help`, `--version` and `status`. This is a proposed checkpoint, not a script delivered
here. Installation, configuration checks, evidence execution and report views below
describe the intended workflow and require their own approval. The
[compatibility matrix](WORKSTATION_COMPATIBILITY_MATRIX.md) separates implemented behavior,
observed platforms, proposed tests and blocked cells. The Mac has an existing bounded synthetic
evidence path. Windows lacks an approved native wheel closure and its evidence commands
remain blocked even after a pure environment becomes available. With no evaluation host,
independent semantic certification remains blocked on both machines.

## What the installed package actually exposes

[Package metadata](../pyproject.toml) defines the console script `sas-re` (`sas_re.cli:main`).
[`python -m sas_re`](../src/sas_re/__main__.py) dispatches to the same [CLI](../src/sas_re/cli.py).
Prefer the latter with an absolute, approved interpreter: this binds the package and Python
environment together without activation, an entry-point shim on PATH or a repository root.

| Current surface | What an operator can infer |
|---|---|
| `--help`, `--version`, `status` | Help/version are text. Status is JSON with phase, implementation lists, pin and capability fields. Exit 0 means status was reported, even when evidence access is BLOCKED. Help lists the engine's commands, not a workstation entitlement. |
| `discover`, `seal-source`, `verify-source` | P1 inventory, validation of a supplied v1 record, and structural verification on an eligible POSIX filesystem. Require explicit scope, store, run and attempt. Verification uses a new verification-attempt ID. |
| `reconstruct-source`, `check-reconstruction` | Bounded synthetic P2A reconstruction from an exact sealed P1 predecessor, then a new check attempt. The authorized CONFIG **file key** is not a pathname. A consistent reconstruction still cannot pass independent semantic acceptance. |
| `check-baseline` | Optional maintainer drift check. Local checkout calls Git; remote comparison uses Git and the network. Neither belongs in workstation startup, installation, analysis or reporting. Reading the *packaged pin* in status needs neither. |
| `analyze-parallelism`, `draft-requirements`, `propose-adrs`, `verify-adrs`, `package-handoff`, `eval` | CLI placeholders: NOT_IMPLEMENTED, no input reads, exit 3. Do not dispatch alternatives for them. |
| Python only | [Bundled contracts](../src/sas_re/contracts.py), [CP2 declaration validation/projection](CP2_DESIGN.md), [separate CP3A physical preflight](CP3A_DESIGN.md) and [private P3-A1 diagnostics](P3_A1_DESIGN.md) have distinct trust boundaries. There is no public CLI for a CP2 envelope, a general report exporter or a semantic evaluator. Demo and repository-check scripts are development tools outside the installed entry points. |

## One interface, with explicit inputs

The following is the proposed operator vocabulary, **not commands available at this commit**.
`KIT` denotes an approved local distribution directory; it is not a Git checkout.

| Operator action through `bash "$KIT/workstation.sh" …` | Intended result / gate |
|---|---|
| `--help`, `--version`, `status` | WS-1 only. Select a trusted installed environment and delegate exactly one token. No project path, config, source, store, output file or installation. |
| `setup` (future) | Explicit, offline per-machine installation from approved local artifacts. Only install locations are writable. Normal startup never installs, updates or downloads anything. |
| `check-config` (future) | Validate supplied **declaration bytes**, not the existence of declared files. Keep bootstrap settings, a CP2 authorization envelope, and the P1 scope/P2A profile distinct. |
| `run <existing evidence command> …` (future) | Delegate a single explicitly named P1/P2A action and its exact arguments on a qualified synthetic scope. Windows must return the engine's denial before source/store access. No orchestration by latest attempt, silent retries or auto-advancement after exit 2. |
| `report` (future) | Produce a human-readable view of one selected, validated public result. The CLI's existing JSON on stdout already provides a report today; saved/displayed summaries confer no authority. |

For example, the WS-1 invocation would be `bash "$KIT/workstation.sh" status` in **both**
shells. On a qualified Mac, the later `run` path would forward `discover --scope
"$scope" --store "$store" --run R1 --attempt inv1`, then, on an explicit operator request,
`reconstruct-source` with `--inventory-attempt inv1 --attempt rec1 --profile-file
synthetic:profile.json` and the same scope/store/run. `check-reconstruction` selects
`--attempt rec1` and a new `--verification-attempt check1`. These are independent calls:
inspect each JSON result and its seal/subject IDs. Preserve documented predecessor
eligibility and failure timing: an error before reservation and a sealed failure after
reservation are different outcomes. An interrupted
or failed attempt is never reused or “fixed” by deleting files. There is no equivalent
Windows evidence sequence at this baseline.

### Bash and interpreter boundary

* Target Bash 3.2-compatible syntax on macOS and Git Bash on Windows. Invoke using
  `bash`, not the login shell, `sh`, PowerShell or a second Windows-specific dispatcher.
  Use Bash arrays / one argv element per value and quoted expansion. No command strings,
  `eval`, sourced configuration, `bash -c` interpolation, word splitting or glob expansion
  of user input. Spaces, apostrophes, wildcard and dollar characters are data; a leading
  dash must not become an option through token reconstruction. Trust the parent shell and
  kit: noninteractive Bash can read `BASH_ENV` before the script runs. Exclude unapproved
  startup hooks **at invocation**, not inside the script. This is not confinement.
* Select the interpreter deterministically: an explicit **trusted absolute executable**
  (proposed setting `SAS_RE_PYTHON`, one filename, never a command with flags), otherwise
  only the exact environment location in the approved kit (`bin/python` vs
  `Scripts/python.exe`). Invalid explicit settings stop; do not try another.
  Bootstrap may locate an already installed interpreter through a separately approved
  enterprise inventory. No PATH scan, arbitrary `python`/`python3`, `.bat`/`.cmd`, Store
  alias, automatic `py -3.12` download, `conda`, or activation from the caller's directory.
  [Python's Windows launcher](https://docs.python.org/3.12/using/windows.html#install-on-demand)
  can install on demand under specific settings.
* Verify the approved executable **before** launching it. Pin exact patch/build and CPU/ABI
  to the trusted inventory; require CPython 3.12, expected `sys.platform`, `os.name` and
  `sysconfig.get_platform()` in a trusted fixed metadata check. macOS must be Darwin/posix;
  the initial Windows x64 proposal requires win32/nt and native `win-amd64`, not an
  [MSYS2/MinGW Python](https://www.msys2.org/docs/python/), Cygwin Python or WSL.
  The shell may veto a mismatch; it cannot select the engine backend. An existing Windows
  workstation is not evidence that its architecture, interpreter, filesystem or wheels
  meet that tuple. Rosetta/Intel and ARM Windows require their own approval and evidence.
* Invoke the selected interpreter with `-I -B -X utf8 -m sas_re` from any working
  directory. Use the same flags for interpreter checks. Isolated mode omits CWD/user site and ignores Python environment settings;
  it is **not** OS isolation. Use a non-editable installation in a trusted environment;
  validate package version, installed origin, bundled resources and release manifest,
  not version alone. See [Python 3.12 invocation rules](https://docs.python.org/3.12/using/cmdline.html#cmdoption-I).
* [Git Bash](https://gitforwindows.org/) can transform path-looking arguments when
  invoking native programs; quoting preserves token boundaries but does **not** disable
  that conversion. Environment values have a separate conversion policy. Use
  `MSYS2_ARG_CONV_EXCL='*'` **for the native child only**, pass already-native path
  operands when a later approved mode requires them, and scope `MSYS2_ENV_CONV_EXCL`
  to explicitly carried native environment fields if needed. Verify the exact installed
  Git Bash behavior; see [MSYS2 path conversion](https://www.msys2.org/docs/filesystem-paths/).
  WS-1 accepts no path operands; the executable itself is addressed in Bash-compatible
  spelling. For a later installer, convert only a declared *installation* path such as
  `/c/Approved Kit` to a single native argument (e.g. `C:/Approved Kit`), once, using a
  trusted `cygpath` if available. If ambiguous or unavailable, require explicit native
  spelling or stop. Never convert file keys, `root:file`, ID lists, arbitrary values or
  paths embedded in JSON. Do not resolve, stat or convert evidence paths to “help” a
  blocked Windows command.
* Preserve spelling and bytes: no case folding, Unicode normalization, BOM stripping,
  newline conversion, shell variables carrying binary source, or text pipelines for
  evidence. CP2 uses its own native-root syntax (including backslashes in a Windows
  declaration) and screens aliases; relative evidence names retain their current limits.
  Unicode native parent directories, NFC/NFD pairs and spaces are test cases, not an
  extension of the evidence namespace. Ship the launcher UTF-8 without BOM and with LF,
  verifying distribution bytes **before** Bash reads it. CRLF can break parsing even
  with explicit `bash`. A future narrowly scoped LF attribute for the script is a
  development convenience only ([Git attributes](https://git-scm.com/docs/gitattributes));
  never normalize frozen inputs, contracts or seals. Native text-mode stdout line endings
  are presentation, not canonical JSON bytes for hashing.

### Exit status, streams and reports

WS-1 checks the entire argv before interpreter discovery and accepts exactly one of its
three tokens. Unsupported usage exits 2 with a launcher
usage diagnostic on stderr; an unavailable approved environment exits 2 with a distinct
bootstrap BLOCKED diagnostic. Neither masquerades as an engine JSON evidence report.
For a delegated call, preserve stdout, stderr and the child exit status (prefer final
`exec`); no pipeline, `tee`, unconditional success or trap that masks failure. CLI
0 means success **for that command**; 1 is a failed stage or process error; 2 can mean
a JSON BLOCKED stage **or** argparse usage on stderr; 3 is a future CLI placeholder.
A shell start/exec error or signal is not a workflow finding. Record actual interruption
behavior on each shell; do not retry or synthesize a seal.

For later reporting, display the original structured result, preserving gate, findings,
verification/authority fields and, when present, exact workspace/run/attempt/subject
and seal hashes. Do not infer a successful seal from stdout or from exit code alone.
A Markdown view could consume bounded, caller-supplied synthetic result bytes and write
only to stdout. Label unverified data as data, escape free text, and link any sealed result
by exact identity; do not auto-open a store, select “latest”, derive new canonical hashes
from console text, overwrite a seal or infer a stage PASS. Optional persisted export would
need independently approved destination controls; no redirection/log file that creates
output **before** a Windows denial. No HTML/PDF/Mermaid runtime, provider or downstream write
is needed for terminal reporting.

## Offline setup and configuration (later design, not WS-1)

1. **Receive a kit, not a checkout.** An administrator supplies the launcher, pinned
   application wheel, frozen lock, all matching dependency wheels (including native
   `rpds-py`), tuple-specific Python/bootstrap tools if needed, and an independently
   approved manifest of filenames, versions, tags, sizes and SHA-256 values. Authenticate
   the manifest through a trusted release channel outside the kit. Hash equality with a
   manifest supplied by the same untrusted party is insufficient. Verify before executing
   the launcher/interpreter or creating an environment. Do not use a historical wheel
   merely because its name contains `0.3.0`.
2. **Check the whole closure first.** The [existing lock](../requirements.lock) pins
   Python packaging and runtime dependencies and admits native wheels for macOS ARM64
   and manylinux x86_64. It has no approved Windows x64 or Intel Mac native hash.
   A system Python or a pure-Python application wheel does not fill that gap. Missing,
   extra/unapproved, damaged or wrong-ABI artifacts, an unusable interpreter bootstrap,
   or insufficient permission/space means installation BLOCKED. On Windows no dependency
   may be installed and no lock hash added on the strength of this plan.
3. **Install only from verified local bytes.** In a separately approved setup, create a fresh
   per-user venv at its final dedicated installation path, outside source/store, without
   system site packages. Use the verified `bin/python` or `Scripts/python.exe` directly.
   Never move/copy a dev venv or replace a working environment in place
   ([Python venv guidance](https://docs.python.org/3.12/library/venv.html#how-venvs-work)).
   Use a trusted, reviewed local wheelhouse with pip options `--no-index --find-links
   <local-dir> --require-hashes --only-binary=:all: --no-cache-dir` and the exact lock;
   install the separately verified project wheel by its exact name with `--no-index
   --no-deps`. Allow only local regular wheel files and pinned requirements; no nested
   URLs, VCS, editable installs, source builds, upgrades or wildcard wheel selection.
   Clear ambient pip/proxy options; disable configuration-file loading with the native
   `os.devnull` for `PIP_CONFIG_FILE` and disable update checks. Validate behavior with the
   **pinned pip**, because `--no-index` alone does not rule out a remote find-links URL.
   See [pip secure installs](https://pip.pypa.io/en/stable/topics/secure-installs/),
   [install options](https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-no-index)
   and [configuration precedence](https://pip.pypa.io/en/stable/topics/configuration/#pip-config-file).
   Run `pip check`, verify installed files/resources and inspect `status` outside the source
   tree. Only then select this environment for use. An incomplete install remains unusable;
   retain the previous approved environment. No release kit or offline installation was
   built, delivered or qualified here.
4. **Validate the right configuration.** Runtime selection is trusted kit metadata, never
   a sourced shell file. For the proposed standalone `check-config`, accept only bounded
   caller-supplied CP2 declaration bytes (e.g. binary stdin); cap the read at the existing
   limit plus one before calling `parse_authorization(raw, expected_platform=...)`.
   Use the selected target `posix` or `windows` explicitly. Return declaration validity,
   projection version and logical scope hash or the fixed error/gate. Do not echo absolute
   roots or private payloads. A valid Windows declaration on a Mac is a syntax/identity
   check, not a Windows trial. Do not search for configs, open arbitrary files by extension
   or follow a binding. A CP2 projection is **not** the v1 Scope accepted by the CLI;
   do not convert it into evidence authorization. P2A's profile is a separately authorized
   CONFIG file addressed by file key. Nothing automatically executes after validation.

## Filesystem gates and local evaluation

The native interpreter's [capability gate](../src/sas_re/platform_io.py), not the shell,
decides availability. On macOS, AVAILABLE means primitives exist. The engine still checks
authorized synthetic scope, physical filesystem constraints, permissions, links, disjoint
store and exact append-only attempts. [CP3A preflight](CP3A_DESIGN.md) is a separate
read-only API with an independent local policy; do not silently add it to the older
commands or alter their failure timing. On native Windows all five evidence operations
remain BLOCKED/exit 2 on well-formed invocations **before** reading the scope/record,
enumerating sources or creating/reserving a store. The private CP3B/CP3D code is not
a public reader or publisher. No path rewriting, capability override or POSIX emulation
fallback can grant access.

| Local question | Useful workstation evidence | Limit |
|---|---|---|
| Is the environment correctly installed? | Interpreter/ABI, manifest and installed resource checks; help/version/status without Git or network | Does not qualify the filesystem or certify SAS semantics |
| Are supplied declarations/records consistent? | Pure schema validation, CP2 identity vectors, frozen synthetic byte/hash comparisons and private graph-math regressions in a development harness | No physical authority, real source provenance, gold, or proof that absent dependencies imply independence |
| Does the tested reconstruction match its public input? | On a qualified Mac, P1/P2A synthetic fixtures, exact attempt replay and deterministic report comparisons | P2A shares reconstruction logic with its checker. Its result is local regression evidence, not independent acceptance. On Windows, source-backed checks remain unavailable |
| Are C/R/evaluator roles independently isolated? | **No workstation result here.** The design accepted as documentation in the [B1 checklist](P2B_B1_APPROVAL_CHECKLIST.md) needs a separately authorized evaluation host and OS-enforced role boundaries | With no dedicated Linux host or VM, that B1 proof cannot run. Same-user processes, venvs, Bash sessions, synthetic fixtures, prompts and CI are not substitutes. Any alternative isolation architecture needs a separate design, approval and native proof |

For example, a local harness can check that a public A→B→C fixture returns its two
original edge IDs in order, that changing its bytes invalidates the expected digest,
and that matched logical declarations project to the same CP2 identity. Those are
repeatable tests with visible answers; none tests hidden semantics or cross-role secrecy.

No role isolation is required to use the ordinary workstation engine. Keep
`artifact_authority: DRAFT`, `semantic_verification: UNVERIFIABLE`,
`semantic_acceptance: BLOCKED` and `benchmark_execution: NOT_RUN` wherever those
fields belong to the existing contract. P3-A1 remains private. The shell choice supersedes
the older [portability plan's](CROSS_PLATFORM_PORTABILITY_PLAN.md) PowerShell preference
for ordinary Windows use only; it changes no qualification result or evidence contract.

## Smallest next approval: WS-1

**Propose one launcher file plus focused launcher tests and usage/validation documentation.**
Require an already approved environment. Accept exactly `--help`, `--version`, or `status`;
reject missing/extra tokens and every other operation before any caller-path access.
No setup/config/run/report verb is part of this first increment. No installers, new CLI
or API, shell writes, locks, report export, dependency changes, host provisioning or
platform override. Any later modes require a separate review of the specific file and
authority boundaries they introduce.

The six [WS-1 test families and expected observations](WORKSTATION_COMPATIBILITY_MATRIX.md#proposed-workstation-checks)
cover dispatch/streams, bootstrap refusal, argv, offline execution/shadowing, delivery and
interruption, and gate preservation. Keep the 693 existing regressions on the environments
where they apply; the full POSIX development suite is not a Windows workstation prerequisite.
For Windows, credit only native cases actually run. Record simulated denials separately.

Acceptance is per tuple. Record Bash/Git Bash build, OS, CPU, native Python, provenance,
wheel hashes, commands, exits and failures. Test on an actual approved Git Bash + native
Python installation or mark Windows **BLOCKED / NOT_RUN**; Linux CI, a simulated
`sys.platform` and macOS alone are insufficient. If either an approved Windows wheel
closure or equivalent security controls are missing, stop—do not extend the lock, skip
hostile cases or make workstation use depend on Linux. WS-1 success does not release
a platform or authorize CP4, CP5, native Windows access, B1, operational P3 or real intake.

Before a real-host WS-1 trial, identify each workstation's OS/CPU, Bash build, approved
interpreter and package origin; supply the trusted kit/manifest location and the person
authorized to approve its bytes. These details are OPEN. Advance only WS-1 if separately
approved; decide offline setup or a first authorized synthetic macOS run after its review.

## Evidence for this planning checkpoint

Observed directly on macOS 26.6.2 (25G83), ARM64, Bash 3.2.57 and CPython 3.12.5:
from outside the checkout with an empty PATH, the previously installed wheel environment's
absolute interpreter ran `-I -B -X utf8 -m sas_re` with `--help`, `--version` and `status`
(exit 0 for each). Version was 0.3.0; status reported POSIX primitives AVAILABLE, P2A
and semantic acceptance BLOCKED. All 29 `.py`/`.json` package files in the baseline
matched the installed copies, including the P3-A1 module. An empty PATH is not a network-isolation test. These were direct existing
commands: **no launcher, setup, evidence workflow, report exporter, Windows qualification
or B1 test was run**. The prior 693-test results in the project records are historical.
The staged change covers only two plans and three ledger updates. Read-only comparisons
found all 100 other baseline files byte- and mode-identical, eight frozen hashes and
three P3-A1 hashes unchanged, and the downstream pin unchanged. Markdown/table checks,
CLI inventory comparison, whitespace checks and the tracked-file repository guard passed.
No scripts, contracts, lock, workflows or tests changed. See the [matrix](WORKSTATION_COMPATIBILITY_MATRIX.md)
and [decisions](OPEN_DECISIONS.md) for the unexecuted obligations. Stop for human review.
