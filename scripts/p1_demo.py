"""Reproducible synthetic P1 CLI exercise. Does not execute SAS or parse sources."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

# Test support generates labeled synthetic bytes; the application remains installed.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
from fixture_support import make_graph, make_scope  # noqa: E402
from sas_re.evidence import digest  # noqa: E402
from sas_re.safeio import canonical_bytes, require_safe_root  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, required=True)
    target = parser.parse_args().destination
    require_safe_root(target.parent)
    target.mkdir(mode=0o700)  # Exclusive: never overwrite an existing demo directory.
    scope = make_scope(target)
    inventory, graph = make_graph(scope, "record-1")
    (target / "scope.json").write_bytes(canonical_bytes(scope))
    (target / "record.json").write_bytes(canonical_bytes(graph))
    common = ["--scope", str(target / "scope.json"), "--store", str(target / "artifacts"),
              "--run", scope["run_id"]]
    results = []

    def invoke(command, expected, *args):
        completed = subprocess.run([sys.executable, "-m", "sas_re", command, *common, *args],
                                   capture_output=True, text=True, check=False)
        result = json.loads(completed.stdout)
        if completed.returncode != expected:
            raise RuntimeError("Unexpected synthetic demo exit code")
        results.append({"command": command, "exit_code": completed.returncode, "result": result})

    invoke("discover", 0, "--attempt", "inventory-1")
    invoke("seal-source", 0, "--attempt", "record-1", "--record", str(target / "record.json"))
    invoke("verify-source", 0, "--attempt", "record-1", "--verification-attempt", "check-1")
    record_dir = target / "artifacts" / scope["workspace_id"] / scope["run_id"] / "record-1"
    historical = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in record_dir.iterdir()}
    changed = target / "sources" / "includes" / "constants.sas"
    changed.write_bytes(changed.read_bytes() + b"/* SYNTHETIC REVISION; not executed. */\n")
    invoke("verify-source", 1, "--attempt", "record-1", "--verification-attempt", "check-stale")
    unchanged = historical == {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in record_dir.iterdir()}
    if not unchanged:
        raise RuntimeError("Historical synthetic attempt changed")
    report = {"synthetic_only": True, "source_hashes": {f["file_key"]: f["sha256"] for f in inventory["files"]},
              "initial_source_fingerprint": inventory["source_fingerprint"],
              "source_record_sha256": digest(graph), "historical_attempt_unchanged": unchanged,
              "results": results}
    (target / "demo-report.json").write_bytes(canonical_bytes(report))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
