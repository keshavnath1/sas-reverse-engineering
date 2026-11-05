"""Explicit P1 integrity CLI. All future semantic commands fail closed."""

import argparse
import json
from importlib.metadata import version
from pathlib import Path

from sas_re.baseline import metadata, report
from sas_re.runs import execute

PLANNED = (
    "analyze-parallelism", "draft-requirements",
    "propose-adrs", "verify-adrs", "package-handoff", "eval",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SAS planner — P1 source integrity only")
    parser.add_argument("--version", action="version", version=version("sas-reverse-engineering"))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="Report implemented and planned capabilities")
    drift = sub.add_parser("check-baseline", help="Read-only downstream identity/drift check")
    drift.add_argument("--checkout", type=Path, help="Explicit downstream checkout root")
    drift.add_argument("--remote", action="store_true", help="Query pinned public branch (network)")
    for command in ("discover", "seal-source", "verify-source"):
        p1 = sub.add_parser(command, help="Explicit synthetic scope; structural integrity only")
        p1.add_argument("--scope", type=Path, required=True, help="Authorized JSON scope manifest")
        p1.add_argument("--store", type=Path, required=True, help="Absolute artifact store outside source roots")
        p1.add_argument("--run", required=True)
        p1.add_argument("--attempt", required=True, help="Explicit attempt ID (subject for verify-source)")
        if command == "seal-source":
            p1.add_argument("--record", type=Path, required=True, help="Supplied canonical graph JSON")
        if command == "verify-source":
            p1.add_argument("--verification-attempt", required=True, help="New append-only verification attempt")
    for command in PLANNED:
        sub.add_parser(command, help="NOT IMPLEMENTED; exits 3 without reading inputs")
    args, extra = parser.parse_known_args(argv)
    if args.command in PLANNED:
        result = {"command": args.command, "stage_gate": "BLOCKED", "status": "NOT_IMPLEMENTED",
                  "reason": "P1 source integrity only. This command requires a later approved phase.",
                  "benchmark_execution": "NOT_RUN", "inputs_read": False}
        code = 3
    else:
        if extra:
            parser.error("unrecognized arguments")
        if args.command == "status":
            baseline = metadata()
            result = {"version": version("sas-reverse-engineering"), "phase": "P1",
                      "implemented": ["status", "check-baseline", "discover", "seal-source", "verify-source"], "planned": list(PLANNED),
                      "downstream_commit": baseline["downstream"]["commit"],
                      "specification_sha256": baseline["specification"]["sha256"],
                      "benchmark_execution": "NOT_RUN", "downstream_integration": "NOT_IMPLEMENTED",
                      "semantic_verification": "UNVERIFIABLE", "artifact_authority": "DRAFT",
                      "note": "Status does not execute validation or advance a workflow."}
            code = 0
        elif args.command == "check-baseline":
            if args.checkout is None and not args.remote:
                drift.error("provide --checkout and/or --remote; no implicit checkout is selected")
            result, code = report(args.checkout, args.remote)
        else:
            result, code = execute(args.command, args.scope, args.store, args.run, args.attempt,
                                   getattr(args, "record", None), getattr(args, "verification_attempt", None))
    print(json.dumps(result, indent=2))
    return code
