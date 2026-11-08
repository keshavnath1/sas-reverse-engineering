"""Foundation repository guard; not a SAS evidence validator or full DLP system."""

import hashlib
import json
import os
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
SKILL_DISCOVERY_LINK = ".agents/skills"


def valid_skill_link(root: Path) -> bool:
    """Allow only the exact, tracked directory link used for repository skill discovery."""
    path = root / SKILL_DISCOVERY_LINK
    # Check parents and the literal pointer before following any link.
    if any(part.is_symlink() or not part.is_dir() for part in (root / ".agents", root / "skills")):
        return False
    if not path.is_symlink() or os.readlink(path) != "../skills":
        return False
    entry = subprocess.check_output(
        ["git", "ls-files", "--stage", "--", SKILL_DISCOVERY_LINK], cwd=root, text=True).split()
    if len(entry) != 4 or entry[0] != "120000" or entry[2:] != ["0", SKILL_DISCOVERY_LINK]:
        return False
    return subprocess.check_output(["git", "show", ":" + SKILL_DISCOVERY_LINK], cwd=root) == b"../skills"


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
        if name == SKILL_DISCOVERY_LINK:
            if not valid_skill_link(root):
                errors.append("Invalid repository skill discovery link")
            continue
        if name.startswith("skills/") and any(
                root.joinpath(*Path(name).parts[:i]).is_symlink() for i in range(1, len(Path(name).parts))):
            errors.append(f"Symlink in skill definition path: {name}")
            continue
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
