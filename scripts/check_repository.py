"""Foundation repository guard; not a SAS evidence validator or full DLP system."""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

PRIVATE_PARTS = {"intake", "private", "artifacts", "outputs", "local", "gold",
                 ".env", ".aws", ".ssh", ".azure", ".gcloud", ".agents", ".codex"}
PRIVATE_SUFFIXES = {".sas", ".log", ".lst", ".csv", ".tsv", ".parquet", ".sas7bdat",
                    ".sas7bcat", ".xpt", ".xlsx", ".xls", ".db", ".sqlite", ".sqlite3",
                    ".pem", ".key", ".p12", ".pfx", ".zip"}
SECRET_PATTERNS = [re.compile(rb"AKIA[0-9A-Z]{16}"),
                   re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
                   re.compile(rb"gh[pousr]_[A-Za-z0-9]{36,}"),
                   re.compile(rb"sk-proj-[A-Za-z0-9_-]{20,}")]


def prohibited_path(name: str) -> bool:
    path = Path(name.lower())
    return (bool(set(path.parts) & PRIVATE_PARTS)
            or path.suffix in PRIVATE_SUFFIXES
            or path.name.startswith((".env.", "credentials", "secrets")))


def check(root: Path) -> list[str]:
    """Inspect staged/tracked files; report paths, never matched secret contents."""
    names = subprocess.check_output(
        ["git", "ls-files", "-z"], cwd=root).decode().split("\0")
    baseline = json.loads((root / "src/sas_re/data/baseline.json").read_text())
    spec = baseline["specification"]
    errors = []
    for name in filter(None, names):
        path = root / name
        if path.is_symlink() or not path.is_file():
            errors.append(f"Non-regular or missing tracked file: {name}")
            continue
        worktree_data = path.read_bytes()
        index_data = subprocess.check_output(["git", "show", ":" + name], cwd=root)
        versions = (worktree_data, index_data)
        if name == spec["path"]:
            if any(hashlib.sha256(data).hexdigest() != spec["sha256"] for data in versions):
                errors.append("Specification archive hash mismatch")
            continue  # The one approved, hash-pinned reference archive.
        if prohibited_path(name):
            errors.append(f"Private/source/data path tracked: {name}")
        if any(pattern.search(data) for pattern in SECRET_PATTERNS for data in versions):
            errors.append(f"Possible credential material: {name}")
    if spec["path"] not in names:
        errors.append("Approved specification archive is not tracked")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = check(root)
    print(json.dumps({"stage_gate": "FAIL" if errors else "PASS", "errors": errors,
                      "limitation": "Tracked-file rules and selected secret formats only; not complete DLP."}, indent=2))
    return int(bool(errors))


if __name__ == "__main__":
    sys.exit(main())
