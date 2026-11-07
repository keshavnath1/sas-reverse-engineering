"""Run the bounded public running-balance engineering candidate."""

import argparse
from collections import defaultdict
from fractions import Fraction
import json
from pathlib import Path
import re
import sys

from sas_re.safeio import EvidenceError, secure_read

sys.path.insert(0, str(Path(__file__).resolve().parent))
from review_intake import STATUS_FIELDS, identity, json_bytes

PACKAGE = Path(__file__).resolve().parents[1] / "examples/modernization"
PACKAGE_SHA256 = "cdf18e8c860931eef0e537986184c274a134811eb0909ac97393ec6774caef73"
MAX_VALUE = 2 ** 20
NUMBER = re.compile(r"[+-]?[0-9]{1,10}(?:\.[0-9]{1,10})?")


def numeric(value):
    """Admit ordinary missing and small, exact binary fractions."""
    if value == ".":
        return None
    if not isinstance(value, str) or not NUMBER.fullmatch(value):
        raise ValueError("UNSUPPORTED_NUMERIC_VALUE")
    number = Fraction(value)
    if abs(number) > MAX_VALUE or 1024 % number.denominator:
        raise ValueError("UNSUPPORTED_NUMERIC_VALUE")
    return number


def typed_rows(rows, width):
    if not isinstance(rows, list) or len(rows) > 1000:
        raise ValueError("UNSUPPORTED_ROW_COUNT")
    for row in rows:
        if not isinstance(row, list) or len(row) != width:
            raise ValueError("UNSUPPORTED_ROW_SHAPE")
        yield tuple(map(numeric, row))


def sort_key(row):
    return tuple((value is not None, value) for value in row[:2])


def run_pipeline(raw_rows, lookup_rows):
    """Evaluate the fixture's three operations under the draft engineering contract."""
    raw = list(typed_rows(raw_rows, 3))
    lookup = defaultdict(list)
    for group, weight in typed_rows(lookup_rows, 2):
        lookup[group].append(weight)
    if any(sort_key(a) > sort_key(b) for a, b in zip(raw, raw[1:])):
        raise ValueError("INPUT_ORDER_REQUIRED")
    if sum(len(lookup.get(row[0], ())) for row in raw) > 10000:
        raise ValueError("JOIN_CARDINALITY_LIMIT")

    running = []
    balance = Fraction(8)
    queued = None
    for index, (group, subkey, amount) in enumerate(raw):
        if index == 0 or raw[index - 1][0] != group:
            balance = Fraction(0)
        if amount is not None:
            balance += amount
        if abs(balance) > MAX_VALUE:
            raise ValueError("BALANCE_OUTSIDE_DOMAIN")
        previous = None
        if amount is not None and amount > 0:
            previous, queued = queued, amount
        last = index + 1 == len(raw) or raw[index + 1][:2] != (group, subkey)
        running.append((group, subkey, amount, balance, previous, Fraction(1) if last else None))

    ordered = sorted(running, key=sort_key)
    # Every unmatched left row has a missing right weight and fails the WHERE.
    enriched = [(group, balance, weight)
                for group, _, _, balance, _, _ in running
                for weight in lookup.get(group, ())
                if weight is not None and weight > 0]
    return running, ordered, enriched


def build_result(package):
    manifest_raw = secure_read(package, "MANIFEST.json", 65536)
    if identity(manifest_raw)["sha256"] != PACKAGE_SHA256:
        raise ValueError("UNSUPPORTED_PACKAGE_IDENTITY")
    manifest = json.loads(manifest_raw)
    payloads = {}
    for name, expected in manifest["files"].items():
        raw = secure_read(package, name)
        if identity(raw) != expected:
            raise ValueError("PACKAGE_PAYLOAD_IDENTITY_MISMATCH")
        payloads[name] = raw
    profile = json.loads(payloads["source/profile.json"])
    raw, lookup = profile["inputs"]
    running, ordered, enriched = run_pipeline(raw["rows"], lookup["rows"])

    def output(columns, rows):
        return {"columns": columns, "rows": [
            [None if v is None else int(v) if v.denominator == 1 else float(v) for v in row]
            for row in rows
        ]}

    fields = ["group", "subkey", "amount", "balance", "previous", "marker"]
    return {
        **{key: manifest[key] for key in STATUS_FIELDS},
        "candidate_status": "DRAFT_ENGINEERING_EXECUTION",
        "business_approval": "PENDING",
        "comparison": "NOT_RUN_BY_COMMAND",
        "package_manifest_sha256": PACKAGE_SHA256,
        "evidence": {
            "profile": manifest["files"]["source/profile.json"],
            "graph": manifest["files"]["evidence/EVIDENCE.json"],
            "operations": {"work.running": "/operations/2", "work.export_order": "/operations/3",
                           "work.enriched": "/operations/5"},
        },
        "outputs": {"work.running": output(fields, running),
                    "work.export_order": output(fields, ordered),
                    "work.enriched": output(["group", "balance", "weight"], enriched)},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--package", type=Path, default=PACKAGE)
    args = parser.parse_args()
    try:
        result = build_result(args.package.absolute())
    except (EvidenceError, OSError, ValueError) as error:
        parser.exit(2, f"REFUSED: {error}\n")
    sys.stdout.buffer.write(json_bytes(result))


if __name__ == "__main__":
    main()
