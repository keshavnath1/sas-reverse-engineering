"""Read-only comparison to a frozen downstream source baseline, not integration."""

import hashlib
import json
import subprocess
from importlib.resources import files
from pathlib import Path


def metadata() -> dict:
    return json.loads(files("sas_re").joinpath("data/baseline.json").read_text())


def _git(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(
        ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", *args],
        cwd=cwd, capture_output=True, text=True, timeout=30, check=True,
    )
    return result.stdout.strip()


def check_checkout(checkout: Path, baseline: dict) -> dict:
    """Compare HEAD, worktree cleanliness and every pinned file's actual bytes."""
    expected = baseline["downstream"]
    try:
        root = checkout.resolve(strict=True)
        if Path(_git("rev-parse", "--show-toplevel", cwd=root)).resolve() != root:
            return {"check": "checkout", "stage_gate": "BLOCKED",
                    "reason": "Path must be the checkout root."}
        head = _git("rev-parse", "HEAD", cwd=root)
        dirty = bool(_git("status", "--porcelain", "--untracked-files=normal", cwd=root))
        changed = []
        for name, digest in expected["file_sha256"].items():
            path = root / name
            # Never follow a file or directory symlink while checking baseline files.
            if any(p.is_symlink() for p in [path, *path.parents] if p != root.parent):
                changed.append(name)
            elif not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                changed.append(name)
        drift = head != expected["commit"] or dirty or bool(changed)
        return {"check": "checkout", "stage_gate": "FAIL" if drift else "PASS",
                "expected_commit": expected["commit"], "observed_commit": head,
                "worktree_clean": not dirty, "changed_or_missing_files": changed,
                "files_checked": len(expected["file_sha256"])}
    except (OSError, subprocess.SubprocessError, UnicodeError):
        # Git stderr can contain credential-bearing URLs or private file content.
        return {"check": "checkout", "stage_gate": "BLOCKED",
                "reason": "Checkout unavailable, unreadable, or Git check failed."}


def check_remote(baseline: dict) -> dict:
    """Read one branch ref; never fetch, repin, pull, or mutate a checkout."""
    expected = baseline["downstream"]
    ref = "refs/heads/" + expected["branch"]
    try:
        output = _git("ls-remote", "--exit-code", expected["repository"], ref)
        rows = [line.split() for line in output.splitlines()]
        if len(rows) != 1 or len(rows[0]) != 2 or rows[0][1] != ref:
            raise ValueError("Missing or ambiguous branch")
        head = rows[0][0]
        if len(head) != 40 or any(c not in "0123456789abcdef" for c in head):
            raise ValueError("Invalid commit")
        return {"check": "remote", "stage_gate": "PASS" if head == expected["commit"] else "FAIL",
                "expected_commit": expected["commit"], "observed_commit": head,
                "branch": expected["branch"]}
    except (OSError, subprocess.SubprocessError, UnicodeError, ValueError):
        return {"check": "remote", "stage_gate": "BLOCKED",
                "reason": "Remote branch unavailable or response invalid; drift is unknown."}


def report(checkout: Path | None, remote: bool) -> tuple[dict, int]:
    baseline = metadata()
    checks = []
    if checkout is not None:
        checks.append(check_checkout(checkout, baseline))
    if remote:
        checks.append(check_remote(baseline))
    gates = {item["stage_gate"] for item in checks}
    gate = "FAIL" if "FAIL" in gates else "BLOCKED" if "BLOCKED" in gates or not checks else "PASS"
    return {"stage_gate": gate, "checks": checks,
            "proves": "Only baseline identity and explicitly requested drift checks.",
            "does_not_prove": ["downstream integration", "SAS semantics", "human approval"]}, {
                "PASS": 0, "FAIL": 1, "BLOCKED": 2}[gate]
