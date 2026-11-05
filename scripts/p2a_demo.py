"""Public synthetic CLI demonstration; no SAS execution or semantic acceptance."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    target = args.destination
    if not target.is_absolute() or target.exists():
        parser.error("destination must be an absolute new directory")
    target.mkdir(mode=0o700)
    target = target.resolve()
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
    from p2a_expectations import EXPECTATION_REVIEW, PUBLIC_CASES
    from p2a_support import prepare_case
    from sas_re.evidence import digest
    from sas_re.safeio import canonical_bytes

    assert EXPECTATION_REVIEW["status"] == "REVIEWED_FOR_PUBLIC_DEVELOPMENT"
    scope, _ = prepare_case(target, PUBLIC_CASES["sort_and_producer_consumer"])
    scope_path, store = target / "scope.json", target / "artifacts"
    scope_path.write_bytes(canonical_bytes(scope))
    base = [str(Path(sys.executable).parent / "sas-re")]
    common = ["--scope", str(scope_path), "--store", str(store), "--run", scope["run_id"]]

    def invoke(command, arguments, code):
        result = subprocess.run(base + [command] + common + arguments, capture_output=True, text=True, check=False)
        assert result.returncode == code, (command, result.returncode, result.stdout, result.stderr)
        report = json.loads(result.stdout)
        assert report["semantic_verification"] == "UNVERIFIABLE"
        assert report["benchmark_execution"] == "NOT_RUN"
        return report

    discovered = invoke("discover", ["--attempt", "inventory-1"], 0)
    reconstructed = invoke("reconstruct-source", ["--attempt", "reconstruct-1", "--inventory-attempt", "inventory-1",
                                                  "--profile-file", "synthetic:profile.json"], 2)
    assert reconstructed["reconstruction_status"] == "COMPLETE", reconstructed
    assert reconstructed["source_consistency"] == "PASSED"
    checked = invoke("check-reconstruction", ["--attempt", "reconstruct-1", "--verification-attempt", "check-1",
                                             "--profile-file", "synthetic:profile.json"], 2)
    assert checked["source_consistency"] == "PASSED", checked
    subject = store / scope["workspace_id"] / scope["run_id"] / "reconstruct-1"
    original = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in subject.iterdir()}
    graph = json.loads((subject / "source_record.json").read_bytes())
    source = target / "sources" / "main.sas"
    source.write_bytes(source.read_bytes().replace(b"x / 2", b"x / 4"))
    stale = invoke("check-reconstruction", ["--attempt", "reconstruct-1", "--verification-attempt", "stale-1",
                                           "--profile-file", "synthetic:profile.json"], 1)
    assert stale["findings"][0]["code"] == "STALE_SOURCE", stale
    assert original == {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in subject.iterdir()}
    print(json.dumps({"fixture": "PUBLIC_SYNTHETIC_SORT_AND_DATA", "discover": discovered,
                      "reconstruct": reconstructed, "check": checked, "stale": stale,
                      "source_fingerprint": graph["source_fingerprint"], "graph_sha256": digest(graph),
                      "semantic_acceptance": "BLOCKED", "sas_execution": "NOT_RUN",
                      "history_unchanged": True}, indent=2))


if __name__ == "__main__":
    main()
