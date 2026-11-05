"""Small, explicit foundation CLI. All future analysis commands fail closed."""

import argparse
import json
from importlib.metadata import version
from pathlib import Path

from sas_re.baseline import metadata, report

PLANNED = (
    "discover", "verify-source", "analyze-parallelism", "draft-requirements",
    "propose-adrs", "verify-adrs", "package-handoff", "eval",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SAS planner — P0 foundation only")
    parser.add_argument("--version", action="version", version=version("sas-reverse-engineering"))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="Report implemented and planned capabilities")
    drift = sub.add_parser("check-baseline", help="Read-only downstream identity/drift check")
    drift.add_argument("--checkout", type=Path, help="Explicit downstream checkout root")
    drift.add_argument("--remote", action="store_true", help="Query pinned public branch (network)")
    for command in PLANNED:
        sub.add_parser(command, help="NOT IMPLEMENTED; exits 3 without reading inputs")
    args, extra = parser.parse_known_args(argv)
    if args.command in PLANNED:
        result = {"command": args.command, "stage_gate": "BLOCKED", "status": "NOT_IMPLEMENTED",
                  "reason": "P0 foundation only. This command requires a later approved phase.",
                  "benchmark_execution": "NOT_RUN", "inputs_read": False}
        code = 3
    else:
        if extra:
            parser.error("unrecognized arguments: " + " ".join(extra))
        if args.command == "status":
            baseline = metadata()
            result = {"version": version("sas-reverse-engineering"), "phase": "P0",
                      "implemented": ["status", "check-baseline"], "planned": list(PLANNED),
                      "downstream_commit": baseline["downstream"]["commit"],
                      "specification_sha256": baseline["specification"]["sha256"],
                      "benchmark_execution": "NOT_RUN", "downstream_integration": "NOT_IMPLEMENTED",
                      "note": "Status does not execute validation or advance a workflow."}
            code = 0
        else:
            if args.checkout is None and not args.remote:
                drift.error("provide --checkout and/or --remote; no implicit checkout is selected")
            result, code = report(args.checkout, args.remote)
    print(json.dumps(result, indent=2))
    return code
