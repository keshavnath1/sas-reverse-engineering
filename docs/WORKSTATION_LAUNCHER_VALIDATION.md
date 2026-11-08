# WS-1 validation and qualification limits

Baseline `a79b15fefd878f1ecc9c0e4969e1c6a211120a41` was clean before work. The
user authorized WS-1 only. See [design and bootstrap assumptions](https://github.com/keshavnath1/sas-reverse-engineering/blob/eb9794167339d1991800c290a2b24ac10a57edf8/docs/WS1_DESIGN.md).
The shipped launcher has **no release approval record/pin**, and **no target workstation
release is being certified**. Invalid argv → usage/2; a valid verb without trusted
approval → bootstrap BLOCKED/2 before interpreter discovery. Supplying an executable path
or caller-generated record cannot promote it. Only disposable copies bound to public test
inventories were used for successful dispatch. No real SAS input, Windows evidence
access/publication, setup, independent isolation or semantic evaluation ran.

## Checks and observations

| Subject | Actual local evidence |
|---|---|
| Baseline | Exact detached `a79b15f` clone, original **693 tests**, exit 0 in 18.195 s. macOS 26.6.2 build 25G83 ARM64, Bash 3.2.57(1)-release, native CPython 3.12.5. |
| W01 dispatch | All three allowed tokens via independently constructed test inventories and a real CPython process. The installed project wheel check (below) returned 0, same stdout **and** stderr bytes as each direct invocation. Checkouts and test records are not release trust anchors. |
| W02 bootstrap refusal | No pin, missing/mismatched selection, malformed record or file list, digest/tuple/origin mismatch, invalid wheel metadata, absent/altered resource, editable install or unexpected startup hook: no app dispatch. Calibrated atime witnesses covered unlisted directory, file alias and out-of-root metadata cases on this host. |
| W03 argv / conversion | Exact token counts and case; no suffix allowance or command interpretation. Exercised a path containing spaces, Unicode, apostrophe, glob and command-substitution characters. POSIX double checked argument list and scope of the MSYS setting; this is **not** Git Bash execution. |
| W04 offline / shadowing | Calibrated decoy PATH tools and CWD/PYTHONPATH packages, no trusted executable from PATH, the correct installed-site result; no decoy invocation by the launcher. No upstream endpoints or credentials. These are targeted controls, not a system-wide network sandbox. |
| W05 delivery / child process | External test delivery gate checked LF/UTF-8/no BOM and pinned launcher bytes before interpreting a candidate copy. Altered/CRLF copies refused by the delivery fixture. Synthetic child preserved binary stdout and stderr, exit 37, stdin, POSIX PTY behavior and SIGTERM. This is not native Windows Ctrl-C evidence. |
| W06 exclusions | Explicit refusals for all five evidence commands, placeholders, drift, setup/config/run/report, including a FIFO scope and nonexistent store. No store, report or attempt; existing direct CLI/platform denial regressions remained separate. |
| Focused methods | **29 passed, 0 skipped**, 12.518 s, exit 0. Methods may exercise several variants. This is one POSIX run, not 29 independently evaluated workloads. |
| Historical data | Both P1/P2A demos exit 0 at baseline and candidate. Each entire relative-path/file byte map matched the new baseline and both retained P3-A1 comparison sets: **15 + 15 files**. Complete parsed reports matched; complete stdout bytes also matched. |

Native Windows **W01, W02, W03, W04, W05 and W06 are all BLOCKED / NOT_RUN**. No approved
Windows interpreter, dependency closure, kit attestation or Git Bash test tuple was supplied.
An expected Windows denial covered by an existing simulation does not qualify the workstation.
Intel Mac and other OS/CPU tuples were not qualified. Source identity, semantic authority
and the platform I/O gates did not change.

Final local development suite: **722 tests (693 existing + 29 WS-1), exit 0, 30.264 s**.
No skipped tests.

## Interpreter and artifact identity

Development used the existing repository venv. Editable code was not accepted as an
installed release. The separate historical wheel environment in the following commands
has native CPython 3.12.5, package 0.3.0 in site-packages, and no checkout on its isolated
import path. Its local installation record describes wheel SHA-256
`1813c48e397952297ef0417db8c7f54a25d7fbce12af39431b3dc7d2d005292b`; the retained wheel
bytes matched. All 29 installed project Python/JSON files matched that wheel and the baseline.
Their compact sorted JSON + LF manifest digest is
`c72316485d3982660628273b0089d9d928d83f42c563c6e2d8957813da2e8e0d`; the invoked interpreter
bytes hashed to `f540e9c407a4af503ceaf37a075684fd36346eb114dfe497da31fddf003d0d20`.
A development comparison does not authenticate a host, administrator, offline distribution
or release grant.

For the actual historical-wheel smoke, a test-only copy of the launcher had its two
delivery slots bound to an audit-directory record. A separate stdlib harness
constructed the full inventory, ran the direct and wrapped commands outside the repo and
compared captured streams. **2,429** installed entries; inventory SHA-256
`402b7534f383e1cf8dd7d89807bad2b19e873df2d7b87f98f5e2c1ad8bf71c88`;
test record SHA-256 `eddac9c2766489b9d9c82ed7cb8f1254f99ae1a943ee1ed36564d5cf4b8c9f39`.
The shipped launcher did **not** trust those values. Temporary records, kit copies, wheels
and demo data remain outside Git.

| Historical replay | Artifact manifest SHA-256 | Complete stdout SHA-256 |
|---|---|---|
| P1 | `3b3a6b999ed496b995c2ae055448805a8fbfb746a03edac7192fe128403fa7c6` | `95bc99cfbcf5ff631de4a9e5f32c13da4d89afc7ae084fba8fd0249f9d2a7043` |
| P2A | `38259743e798bd3d9df6089c1576a31865aa575427710ff73bbc2befee3bb809` | `a3acd24fe13210d56b358f801ca7875fbc28fcf6e0877ef1b49246b00d1f5dc1` |

Manifest hashes cover sorted relative artifact paths and their original file contents
via the existing per-file SHA-256 policy; individual bytes were compared, not just totals.
The [eight frozen hashes](DEPENDENCY_ANALYSIS_VALIDATION.md#frozen-identities) and the three recorded
P3-A1 implementation/test hashes were recomputed and all matched. The compatibility
pin remains `bc754e0f1204a99020c864df2a5b25983005e09c`. No Agent-mastery changes.

## Failures, review and corrections

* Initially the W05 delivery regression still held an explicit pending digest while the
  launcher was being assembled. The first integrated run returned 1 (24 methods in
  9.974 s; 23 passed, one delivery-pin mismatch). The digest is test evidence only;
  it was frozen after review. An intermediate 26-method run passed in 11.016 s,
  then the final 29-method suite passed including the added adverse conditions.
* Bootstrap review found that hashing a whole directory tree against one digest could
  open unlisted content before detecting it. The pinned companion inventory now
  restricts membership **before** descent/reads. Pre-execution checks also distinguish
  the trusted base interpreter link from an unexpected executable, refuse a multiply
  linked cfg/manifest, constrain package-version spelling before constructing metadata
  paths, and defend Windows adjacent-file checks from inherited glob settings.
  These are engineering corrections, not reports of a real disclosure.
* No unsupported host, absent witness or simulated Windows branch is counted as a
  successful native Windows run. Trust in the base runtime and absence of concurrent
  untrusted writers must come from the independent release custodian, not this probe.

## Commands and changed files

Local paths used here: `P` is the repository root, `PY="$P/.venv/bin/python"`,
`T=/private/tmp/sas-re-ws1-preservation.U3UQvL7P`, and
`W=/private/tmp/sas-re-p2a-wheel-env/bin/python`. Audit-only scripts under T are
test harnesses; they are neither shipped nor runtime prerequisites.

```sh
# Exact baseline, from T/baseline; no code borrowed from the candidate via PYTHONPATH.
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$T/baseline/src" "$PY" -m unittest discover -s tests -v
# From T; these run the existing demo scripts into distinct synthetic destinations.
"$PY" preserve.py --source baseline --label baseline
"$PY" preserve.py --source "$P" --label candidate
"$W" -I -B -X utf8 "$T/wheel_smoke.py" "$P" "$T/historical-smoke"
# From P:
/bin/bash -n scripts/workstation.sh
/bin/bash scripts/workstation.sh status
.venv/bin/python -B -m unittest discover -s tests -p test_workstation.py -v
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -v
```

The unprovisioned status invocation returned **2 intentionally**; the positive tests used
separate fixture copies. Baseline/candidate replay commands/outputs and individual artifact
hashes are recorded locally in `$T/{baseline,candidate}-preservation.json`.

Added `scripts/workstation.sh`, `tests/test_workstation.py`, `docs/WS1_DESIGN.md` and
this report. Updated `README.md`, `AGENTS.md`, `docs/APPROVAL_HISTORY.md`,
`docs/OPEN_DECISIONS.md` and `docs/BEST_PRACTICES_ADOPTION.md`. Of 105 baseline tracked
files, the 100 outside those five documentation edits remained byte- and executable-mode
identical. No dependency, workflow, package source, frozen contract, parser, historical
artifact, downstream compatibility pin or existing test was edited.

## Final macOS modes

All three final runs used the same 722 methods, with **no failures or skips**. Fresh
checkout and the wheel are tied to implementation commit
`27ecad95a43d68c991d33c0b3aff44b94cf72696`. The launcher is a separately delivered
kit file; the test suite selects the script from that checkout and independently verifies
the installed Python package from the wheel environment.

| Mode | Package/launcher origin | Actual result |
|---|---|---|
| Development | Development source; W fixtures invoke disposable bound copies of the launcher | 722 in 30.264 s, exit 0 |
| Fresh local checkout | Explicit `fresh/src` on PYTHONPATH, verified import location; clean working tree after run | 722 in 31.488 s, exit 0 |
| Installed wheel outside checkout | Separate existing venv's `lib/python3.12/site-packages/sas_re/cli.py`; unset PYTHONPATH | 722 in 32.078 s, exit 0 |

```sh
# From P:
git clone --no-hardlinks --quiet . "$T/fresh"
git -C "$T/fresh" rev-parse HEAD
# From T/fresh:
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$T/fresh/src"
"$PY" -c 'from pathlib import Path; import sas_re.cli; print(sas_re.cli.__file__); assert Path(sas_re.cli.__file__).is_relative_to(Path.cwd()/"src")'
"$PY" -m unittest discover -s tests -v
"$PY" -m pip wheel --no-index --no-deps --no-build-isolation --no-cache-dir --wheel-dir "$T/wheels" .
"$W" -m pip install --no-index --no-deps --no-cache-dir --force-reinstall "$T/wheels/sas_reverse_engineering-0.3.0-py3-none-any.whl"
"$W" -m pip check
# From T:
unset PYTHONPATH
"$W" -I -B -c 'from pathlib import Path; import sas_re.cli,sysconfig; q=Path(sas_re.cli.__file__); assert q.is_relative_to(sysconfig.get_path("purelib")); print(q)'
"$W" -m unittest discover -s "$T/fresh/tests" -v
"$W" -I -B -X utf8 "$T/wheel_smoke.py" "$T/fresh" "$T/candidate-wheel-smoke"
# From P:
.venv/bin/python "$T/scope_check.py"
.venv/bin/python scripts/check_repository.py
.venv/bin/sas-re check-baseline --checkout /private/tmp/sas-re-downstream-bc754e0
git diff --cached --check
git -C "$T/fresh" status --short
```

Commands returned 0. The fresh directory is a clone of the implementation commit,
not a second editable installation. Packaging rebuilt and replaced only this project's
wheel in the disposable wheel environment; no dependency was added, altered or downloaded
by the launcher. `pip check` reported no broken requirements and a nonfatal cache
permission warning. Wheel size 113,647 bytes; SHA-256
`fba04db682b36e6d30f0d3a5a515e4aac7a03de4b793b6a5d5e78eeb0e2539e0`.
The rebuilt installation's test-only record SHA-256 was
`ae330887656cb48898e4a4f7f9faac7960e92c6843791459b28b2a971465f2c1`; its 2,429-entry
file inventory hashed to `080a6c7e9d7d7eae093f59964c61a68f8618bde1fc3a9f0f52faa031192e1ad8`.
All three direct/wrapped command pairs again returned 0 with identical stream bytes.
A different installed closure has a different inventory even with the same project version.

Launcher SHA-256: `83a32f061a69af598d62bb249fb98b87878641e6db7c51848146d0957cdddb7a`;
tests: `55b04651f29c0a8ef6cb64fd59a475a0c6c1569999123a1701573091bdc321ef`.
Scoped byte/mode, executable/LF/delivery-pin, Markdown target, whitespace and tracked-file
guard checks passed; the guard is not full DLP. The read-only downstream checkout check
passed for a clean pinned checkout, 20 files, none changed or missing.

## Hosted Linux CI

[Run 42307238880](https://github.com/keshavnath1/sas-reverse-engineering/actions/runs/42307238880)
completed successfully at implementation commit `27ecad95a43d68c991d33c0b3aff44b94cf72696`.
Ubuntu 24.04.5 x64, CPython 3.12.5: foundation job `128199551419` ran
`python -m unittest discover -s tests -v` in the CI checkout (**722 in 39.574 s**)
and `python -m unittest discover -s "$GITHUB_WORKSPACE/tests" -v` from the runner's
temporary directory after wheel installation (**722 in 39.387 s**). Both passed;
no skipped tests. The job used its native `/bin/bash` for the WS-1 tests; the exact
runner Bash patch version was not captured. Existing synthetic demos and guard passed.
The separate `sas-re check-baseline --remote` job `128199551255` passed. This validates
Linux development/CI behavior, not native Windows, B1 isolation or workstation release.

Stop here. A real independently approved kit, native Windows runtime/wheel closure and
Windows W01–W06 observations remain missing. No new dependency installation, setup
feature, source/workflow authority, semantic acceptance or later phase is implied.
