"""Run the public MVP-3 fixed behavioral cases. Stdout only; no SAS or candidate code loader."""

import argparse
import ast
from collections import Counter, defaultdict
from decimal import Decimal
import hashlib
from itertools import groupby
import json
from pathlib import Path
import re
import sys


TESTS = Path(__file__).resolve().parents[1] / "tests"
SPEC_SHA256 = "7ca4c6b50cdc7f5b7ce2ee422f5adfe883dba82a39b064140fba2d7a70702342"
MVP2_FIXTURE_SHA256 = "dce463011111389bbd84901b2a94632305b287605af98493f3f88744e2f94716"
MVP2_GRAPH = "19f41dea50825469a89d8fc545fee1d87f09af946d130d62de8f946d90b78017"
STAGES = {"ordered": 3, "scaled": 4, "adjusted": 2}


class OutsideProfile(ValueError):
    """The public model has no agreed answer for this input."""


def _integer(cell):
    if cell == ".":
        return None
    if not isinstance(cell, str) or not re.fullmatch(r"[+-]?[0-9]+", cell):
        raise OutsideProfile(f"Outside the ordinary-missing and small-integer profile: {cell!r}")
    digits = cell.lstrip("+-").lstrip("0") or "0"
    if len(digits) > 7 or int(digits) > 1_000_000:
        raise OutsideProfile(f"Outside the exact input bound of 1,000,000: {cell}")
    return -int(digits) if cell.startswith("-") else int(digits)


def _ascending(value):
    # Ordinary SAS numeric missing precedes even negative finite values.
    return (value is not None, 0 if value is None else value)


def _half_units(twice_value):
    if twice_value is None:
        return "."
    units, half = divmod(abs(twice_value), 2)
    return ("-" if twice_value < 0 else "") + str(units) + (".5" if half else "")


def reference_rows(observations, offsets):
    """Exact half-unit arithmetic and all matching pairs. No candidate or graph calls."""
    left = [tuple(_integer(cell) for cell in row) for row in observations]
    right = [tuple(_integer(cell) for cell in row) for row in offsets]
    left.sort(key=lambda row: (_ascending(row[0]), _ascending(row[1])))
    ordered = [tuple("." if x is None else str(x) for x in row) for row in left]
    scaled = [row + (_half_units(value),) for row, (_, _, value) in zip(ordered, left, strict=True)]
    adjusted = []
    for batch, _, value in left:
        if value is None or value <= 0:  # value / 2 > 0 exactly when value > 0
            continue
        for key, offset in right:
            if batch == key:  # includes ordinary missing matching ordinary missing
                total = None if offset is None else value + 2 * offset
                adjusted.append(("." if batch is None else str(batch), _half_units(total)))
    # The join loop visits the already ordered left stream. Only batch order is required.
    return {"ordered": tuple(ordered), "scaled": tuple(scaled), "adjusted": tuple(adjusted)}


def _reverse_ties(rows, width):
    return [row for _, tied in groupby(rows, key=lambda row: row[:width]) for row in reversed(list(tied))]


def _scale_chunk(rows, divisor):
    return [row + ("." if row[2] == "." else str(Decimal(row[2]) / divisor),) for row in rows]


def candidate_rows(observations, offsets, probe, *, split_after=None, chunks=None):
    """Fixed development candidates: decimal scaling and a batch-indexed join on admitted inputs."""
    allowed = {"baseline", "split", "reverse_sort_ties", "reverse_final_ties", "wrong_sort",
               "wrong_final_order", "drop_matches", "wrong_scale", "decouple_ties", "strict_sequence",
               "skip_where", "ignore_missing_key", "unresolved_include"}
    if probe not in allowed:
        raise ValueError("Unknown fixed candidate")

    def sort_cell(cell):
        return Decimal("-Infinity") if cell == "." else Decimal(cell)

    ordered = sorted(observations, key=lambda row: (sort_cell(row[0]), sort_cell(row[1])),
                     reverse=probe == "wrong_sort")
    if probe == "reverse_sort_ties":
        ordered = _reverse_ties(ordered, 2)
    data_stream = _reverse_ties(ordered, 2) if probe == "decouple_ties" else ordered
    blocks = [data_stream]
    if probe == "split":
        if split_after is None or not 0 < split_after < len(data_stream):
            raise ValueError("A split probe needs an interior cut")
        blocks = [data_stream[:split_after], data_stream[split_after:]]
    scaled = []
    for block in blocks:
        if chunks is not None:
            chunks.append(len(block))
        scaled.extend(_scale_chunk(block, 1 if probe == "wrong_scale" else 2))

    lookup = defaultdict(list)
    for key, offset in offsets:
        lookup[sort_cell(key)].append(offset)
    joined = []
    for batch, sequence, _, value in scaled:
        if probe != "skip_where" and (value == "." or Decimal(value) <= 0):
            continue
        if probe == "ignore_missing_key" and batch == ".":
            continue
        matches = lookup[sort_cell(batch)]
        for offset in (dict.fromkeys(matches) if probe == "drop_matches" else matches):
            adjusted = "." if "." in (value, offset) else str(Decimal(value) + Decimal(offset))
            joined.append((batch, sequence, adjusted))
    if probe == "strict_sequence":
        joined.sort(key=lambda row: (sort_cell(row[0]), sort_cell(row[1])))
    else:
        joined.sort(key=lambda row: sort_cell(row[0]), reverse=probe == "wrong_final_order")
    projected = [(batch, value) for batch, _, value in joined]
    if probe == "reverse_final_ties":
        projected = _reverse_ties(projected, 1)
    return {"ordered": tuple(ordered), "scaled": tuple(scaled), "adjusted": tuple(projected)}


def _number(cell):
    if cell == ".":
        return None
    if not isinstance(cell, str) or not re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)", cell):
        raise ValueError("Expected a finite decimal string or ordinary missing '.'")
    return Decimal(cell)


def _bag_difference(delta):
    return [{"row": ["." if x is None else str(x) for x in row], "count": n} for row, n in delta.items()]


def discrepancies(expected, observed):
    """Check the observable contract rather than demanding the reference's choice among ties."""
    differences = []
    previous = None
    for stage, width in STAGES.items():
        source = observed.get(stage)
        if not isinstance(source, (list, tuple)) or any(
                not isinstance(row, (list, tuple)) or len(row) != width for row in source):
            differences.append({"stage": stage, "reason": "missing stage or wrong row shape",
                                "expected_columns": width, "observed": source})
            continue
        try:
            actual = [tuple(_number(x) for x in row) for row in source]
        except ValueError as err:
            differences.append({"stage": stage, "reason": str(err), "observed": source})
            continue
        wanted = [tuple(_number(x) for x in row) for row in expected[stage]]
        keys = 1 if stage == "adjusted" else 2
        # Frozen key sequences are independent of the reference sorter. Tied payloads stay free.
        want_keys = [row[:keys] for row in wanted]
        got_keys = [row[:keys] for row in actual]
        if Counter(got_keys) == Counter(want_keys) and got_keys != want_keys:
            i = next(i for i, value in enumerate(got_keys) if value != want_keys[i])
            differences.append({"stage": stage, "reason": "key order differs from frozen sequence",
                                "at_row": i + 1, "expected": expected[stage][i][:keys], "observed": source[i][:keys]})
        # Each full row contains its key. Bag equality therefore checks multiplicity *per key*.
        needed, got = Counter(wanted), Counter(actual)
        if needed != got:
            differences.append({"stage": stage, "reason": "row multiset differs",
                                "missing": _bag_difference(needed - got), "extra": _bag_difference(got - needed)})
        if stage == "ordered":
            previous = actual
        elif stage == "scaled" and previous is not None and [row[:3] for row in actual] != previous:
            differences.append({"stage": stage, "reason": "SET did not retain the candidate SORT stream",
                                "expected": observed["ordered"], "observed": [row[:3] for row in source]})
    return differences


def _literals(filename, pin, names):
    """Read the named literal assignments from these exact bytes; execute no fixture code."""
    raw = (TESTS / filename).read_bytes()
    if hashlib.sha256(raw).hexdigest() != pin:
        raise RuntimeError(f"Frozen input digest mismatch: {filename}")
    values = {}
    for node in ast.parse(raw).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in names:
                values[name] = ast.literal_eval(node.value)
    if values.keys() != names:
        raise RuntimeError(f"Missing frozen declaration: {filename}")
    return values


def _load_cases():
    cases = _literals("mvp3_cases.py", SPEC_SHA256, {"FIXTURES", "CASES", "FINAL_TIE_WITNESS"})
    original = _literals("mvp2_expectations.py", MVP2_FIXTURE_SHA256, {"CASE", "INPUTS", "SOURCES", "MISSING_INCLUDE"})
    baseline = cases["FIXTURES"]["mvp2"]
    if (baseline["observations"], baseline["offsets"]) != tuple(rows for _, _, _, rows in original["INPUTS"]):
        raise RuntimeError("The behavioral fixture and original declarations differ")
    return cases, original


def _case_result(case_id, definition, fixtures, witness):
    input_id, probe, expected_verdict, first_stage = definition
    fixture = fixtures[input_id]
    expected = fixture["expected"]
    result = {"case_id": case_id, "input_id": input_id, "probe": probe, "expected": expected,
              "expected_verdict": expected_verdict, "observed": None, "discrepancies": [],
              "full_workflow_gate": "BLOCKED"}
    inputs = (fixture["observations"], fixture["offsets"])
    try:
        reference = reference_rows(*inputs)
    except OutsideProfile as err:
        if expected is not None:
            raise RuntimeError(f"Reference refused an admitted case: {case_id}") from err
        result.update(verdict="UNVERIFIABLE", reason=str(err))
    else:
        if expected is None or discrepancies(expected, reference):
            raise RuntimeError(f"Reference disagrees with frozen specification: {case_id}")
        blocks = []
        observed = candidate_rows(*inputs, probe, split_after=fixture.get("split_after"), chunks=blocks)
        errors = discrepancies(expected, observed)
        if probe == "split":
            result["chunks"] = blocks
        if probe == "strict_sequence":
            # Challenge an overstrict candidate verifier. Its own emitted rows may be perfectly legal.
            if discrepancies(expected, {**reference, "adjusted": witness}):
                raise RuntimeError("Frozen final tie witness is not a legal projection")
            sequence_order = observed["adjusted"]

            def accepts(projection):
                return sequence_order == tuple(projection)

            result["policy"] = {"offered_final_rows": witness, "expected_acceptance": True,
                                "observed_acceptance": accepts(witness), "accepts_own_order": accepts(sequence_order)}
            if not accepts(witness):
                errors.append({"stage": "final_order_policy", "reason": "rejected a permitted within-batch permutation",
                               "expected": "accept", "observed": "reject", "offered": witness})
        result.update(observed=observed, discrepancies=errors, verdict="FAIL" if errors else "PASS")
    actual_stage = result["discrepancies"][0]["stage"] if result["discrepancies"] else None
    result["matches_specification"] = result["verdict"] == expected_verdict and actual_stage == first_stage
    return result


def build_report():
    cases, original = _load_cases()
    return {"artifact_authority": "DRAFT", "semantic_verification": "UNVERIFIABLE",
            "semantic_acceptance": "BLOCKED", "benchmark_execution": "NOT_RUN",
            "full_workflow_gate": "BLOCKED",
            "unresolved_include": {"operation": "O4", "target": original["MISSING_INCLUDE"], "verdict": "UNVERIFIABLE"},
            "reference": {"scope": "Public development checks of O1–O3. Graph digest identifies only the original MVP-2 subject.",
                          "fixture": original["CASE"], "original_mvp2_graph_sha256": MVP2_GRAPH,
                          "original_fixture_sha256": MVP2_FIXTURE_SHA256, "specification_sha256": SPEC_SHA256,
                          "source_sha256": {file: hashlib.sha256(data).hexdigest() for file, data in original["SOURCES"].items()}},
            "columns": {"ordered": ["batch", "sequence", "value"], "scaled": ["batch", "sequence", "value", "scaled"],
                        "adjusted": ["batch", "adjusted"]},
            "inputs": {name: {k: v for k, v in f.items() if k != "expected"} for name, f in cases["FIXTURES"].items()},
            "cases": [_case_result(name, definition, cases["FIXTURES"], cases["FINAL_TIE_WITNESS"])
                      for name, definition in cases["CASES"].items()]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", help="show one fixed case ID in detail")
    args = parser.parse_args()
    try:
        report = build_report()
    except RuntimeError as err:
        parser.exit(2, f"BLOCKED: {err}\n")
    if args.case:
        selected = [row for row in report["cases"] if row["case_id"] == args.case]
        if not selected:
            parser.error("unknown frozen case ID")
        report["cases"] = selected
        name = selected[0]["input_id"]
        report["inputs"] = {name: report["inputs"][name]}
    print(json.dumps(report, indent=2 if args.case else None, allow_nan=False))
    return 0 if all(row["matches_specification"] for row in report["cases"]) else 1


if __name__ == "__main__":
    sys.exit(main())
