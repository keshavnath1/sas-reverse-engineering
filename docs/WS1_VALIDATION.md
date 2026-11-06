# WS-1 validation and qualification limits

Baseline `a79b15fefd878f1ecc9c0e4969e1c6a211120a41` was clean before work. The
user authorized WS-1 only. See [design and bootstrap assumptions](WS1_DESIGN.md).
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
The [eight frozen hashes](P3_A1_VALIDATION.md#frozen-identities) and the three recorded
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
this report. Updated `README.md`, `AGENTS.md`, `docs/APPROVALS.md`,
`docs/OPEN_DECISIONS.md` and `docs/BEST_PRACTICES_ADOPTION.md`. Of 105 baseline tracked
files, the 100 outside those five documentation edits remained byte- and executable-mode
identical. No dependency, workflow, package source, frozen contract, parser, historical
artifact, downstream compatibility pin or existing test was edited.
