"""Run the pinned public MIG-3 preparation and MIG-4 gates together."""

import argparse
from pathlib import Path
import sys

from sas_re.platform_io import require_evidence_io
from sas_re.safeio import EvidenceError, _parse_json, ensure_disjoint, secure_read

sys.path.insert(0, str(Path(__file__).resolve().parent))
from migrate_population import bind_plan, evaluate
from migrate_preparation import bind_rules, run_cases
from migration_candidate import AUTHORITY
from mvp1_demo import scratch_destination, write_bundle
from review_intake import identity, json_bytes


ROOT = Path(__file__).resolve().parents[1]
LIMIT = 262144
PINS = {
    "examples/mig3/preparation.sas.txt": "dccdf7b4b11eba5fd7369157c7b3e8ef002d3b8c7bf2c9a5547dc80e161b8cf8",
    "examples/mig4/population.sas.txt": "21e16d05e77999c9b2de565c7f1348d9d4b9aae27736024ca286062f8731d110",
    "examples/mig3/CASES.json": "4b8eb9867cc2a32c793f134fb28d684576ea486592822441e0a3d7ae8a4e0865",
    "examples/mig5/SCENARIOS.json": "945d503e01a88a45c50078d1eaa11c5d95237fb1eb98420797bbfe4aff088faf",
    "scripts/migrate_preparation.py": "91c632829174f1b9075a8b4bccaf8d67df13be30ea94cf86df053ed9a81f1bbe",
    "scripts/migrate_population.py": "12358fadc1f69da1019119d587c83072d6bb6d26f9875494ac817113a7bbb015",
    "scripts/preparation_candidate.py": "9f0c1f3e16d99be58299bd4c156783112aff43aaf41334082a9c3244d0df9547",
}
EVIDENCE_PINS = (
    "178671f6b7f0bfe7bcaa74abeeb2834c453b0ee1ac8cfadf9e7f40643d4ac2f5",
    "90af7c8eef586067a566cac9130f77609c4552190df2a0cb908ae367ca4f9b56",
)


def run_scenario(scenario, cases, preparation, population):
    selected = [cases[name] for name in scenario["cases"]]
    expected = scenario["expected"]
    result = {"scenario": scenario["id"], "sas_process_continuation": "UNOBSERVED"}
    try:
        rows, checks, summary = run_cases(selected, preparation["rules"])
    except ValueError as error:
        if "input_refused" not in expected:
            raise
        observed = {"input_refused": str(error)}
        result.update(input_cases=selected, preparation="REFUSED", population="NOT_RUN",
                      continuation="NOT_RUN")
        checks = []
    else:
        # This is a synthetic handoff of Python results. Retain order and
        # duplicates and keep isolated probes out even when they reach row end.
        ids = [row["candidate_output"]["id"] for row in rows
               if row["mode"] == "full" and row["candidate_row_end_reached"]]
        audit = evaluate(population, ids, scenario["flag"], scenario["expected_count"])
        result.update(preparation={"input_count": len(rows), "rows": rows, "summary": summary},
                      handoff_ids=ids, population=audit, continuation=audit["continuation"])
        observed = {
            "handoff_ids": ids,
            "continuation": audit["continuation"],
            "first_blocking_gate": audit["first_blocking_gate"],
            "guard_predicate": audit["optional_guard"].get("predicate"),
            "duplicate_groups": audit["duplicate_groups"],
        }
    passed = observed == expected and all(check["comparison"] == "PASS" for check in checks)
    return result, {"scenario": scenario["id"], "expected": expected, "observed": observed,
                    "preparation_checks": checks, "comparison": "PASS" if passed else "FAIL"}


def build_package(preparation_path, population_path):
    inputs = {}
    for name, digest in PINS.items():
        path = ROOT / name
        raw = secure_read(path.parent, path.name, LIMIT)
        if identity(raw)["sha256"] != digest:
            raise ValueError("MIGRATION_PINNED_INPUT_MISMATCH")
        inputs[name] = raw
    prep_evidence = secure_read(preparation_path.parent, preparation_path.name, LIMIT)
    pop_evidence = secure_read(population_path.parent, population_path.name, LIMIT)
    if tuple(identity(raw)["sha256"] for raw in (prep_evidence, pop_evidence)) != EVIDENCE_PINS:
        raise ValueError("MIGRATION_EVIDENCE_MISMATCH")

    prep_source, pop_source = "examples/mig3/preparation.sas.txt", "examples/mig4/population.sas.txt"
    preparation = bind_rules(inputs[prep_source], PINS[prep_source], prep_evidence)
    population = bind_plan(inputs[pop_source], PINS[pop_source], pop_evidence)
    scenario_spec = _parse_json(inputs["examples/mig5/SCENARIOS.json"])
    cases = {row["id"]: row for row in (*_parse_json(inputs["examples/mig3/CASES.json"]),
                                        *scenario_spec["additional_cases"])}
    runs, checks = zip(*(run_scenario(scenario, cases, preparation, population)
                         for scenario in scenario_spec["scenarios"]), strict=True)
    passed = all(check["comparison"] == "PASS" for check in checks)
    files = {
        "PREPARATION_EVIDENCE.json": prep_evidence,
        "POPULATION_EVIDENCE.json": pop_evidence,
        "PLAN.json": json_bytes({
            "preparation": {**preparation, "source_path": prep_source,
                            "evidence_file": "PREPARATION_EVIDENCE.json"},
            "population": {**population, "source_path": pop_source,
                           "evidence_file": "POPULATION_EVIDENCE.json"},
            "handoff": "FULL_MODE_PYTHON_ROW_END_IDS_IN_ORIGINAL_ORDER",
            "sas_dataset_continuity": "UNESTABLISHED",
            "reference_obligations": [
                "Obtain attributable SAS prepared output and descriptors for the six-rule cases.",
                "Establish that the population queries consumed that dataset version.",
                "Observe macro values, abort effects and whether SAS continued.",
            ],
            **AUTHORITY,
        }),
        "SCENARIO_RESULTS.json": json_bytes(runs),
        "VALIDATION.json": json_bytes({
            "basis": "PUBLIC_PYTHON_ENGINEERING_EXPECTATIONS",
            "comparison": "PASS" if passed else "FAIL", "scenarios": checks, **AUTHORITY,
        }),
    }
    runner = Path(__file__).resolve()
    files["MANIFEST.json"] = json_bytes({
        "inputs": {name: identity(raw) for name, raw in inputs.items()},
        "runner": {f"scripts/{runner.name}": identity(secure_read(runner.parent, runner.name, LIMIT))},
        "files": {name: identity(raw) for name, raw in files.items()},
        **AUTHORITY,
    })
    return files, passed


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--preparation-evidence", type=Path, required=True)
    parser.add_argument("--population-evidence", type=Path, required=True)
    parser.add_argument("--destination", required=True, help="fresh /tmp/sas-re-mig5-<label> directory")
    args = parser.parse_args()
    try:
        require_evidence_io()
        scratch, leaf = scratch_destination(args.destination, "mig5")
        prep, pop = args.preparation_evidence.absolute(), args.population_evidence.absolute()
        ensure_disjoint(scratch / leaf, [prep.parent, pop.parent])
        files, passed = build_package(prep, pop)
        write_bundle(scratch, leaf, files, names=tuple(files))
    except FileExistsError:
        parser.exit(2, "BLOCKED: destination exists\n")
    except EvidenceError as error:
        parser.exit(2, f"{error.gate}: {error.code}\n")
    except ValueError as error:
        parser.exit(2, f"REFUSED: {error}\n")
    except OSError:
        parser.exit(2, "REFUSED: FILE_IO_REFUSED\n")
    print(json_bytes({"open": str(scratch / leaf / "PLAN.json"),
                      "manifest_sha256": identity(files["MANIFEST.json"])["sha256"],
                      "comparison": "PASS" if passed else "FAIL"}).decode(), end="")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
