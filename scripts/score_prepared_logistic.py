"""Build a public reference-coded design and score it with fixed coefficients."""

import argparse
import math
from pathlib import Path
import sys

from sas_re.platform_io import require_evidence_io
from sas_re.safeio import EvidenceError, _parse_json, ensure_disjoint, secure_read

sys.path.insert(0, str(Path(__file__).resolve().parent))
from migrate_preparation import CHARACTER_FIELDS, NUMERIC_FIELDS
from migrate_preparation_gates import LIMIT, ROOT, build_package
from migrate_sort_export import SCENARIOS
from migration_candidate import AUTHORITY
from migration_review import anchor
from mvp1_demo import scratch_destination, write_bundle
from review_intake import identity, json_bytes
from review_source import single_review


EXAMPLE = ROOT / "examples/mod2"
SOURCE_PROFILES = {
    "fe1bbbd9e531d53103aad52caafbd616a8365e9bcc81241ffa466aaa1c218f85": (417, 441),
    "0f6741a10b6fc29de02fdd9a4500c95f2cc948814d109c1643cfd893a7e58a4c": (1, 10),
}
FIXTURE_PINS = {
    "MAPPING.json": "707f4c7d8c5afb2ccd8073d5dea34ff754c9af8487ae56b95881240e9f53e2a5",
    "COEFFICIENTS.json": "b41d066a5302f7908c97eebe133809a5445fc658b2393d6e8e5e6e78c0a70a64",
}
STATISTICS = {"fitting": "NOT_RUN", "convergence": "NOT_RUN", "ods_production": "NOT_RUN"}
EVENT = "Default=1"
PROBABILITY_TOLERANCE = 1e-15


def recover_model(raw, digest):
    if digest not in SOURCE_PROFILES or identity(raw)["sha256"] != digest:
        raise ValueError("MODEL_SOURCE_IDENTITY_REFUSED")
    evidence, _ = single_review(raw, SOURCE_PROFILES[digest], digest, recover_logistic=True)
    model = evidence["declared_operation"]
    if (not model or model["kind"] != "PROC_LOGISTIC" or model["input"] != "work.prepared_data"
            or model["model"]["response"] != "default" or model["header"]["options"] != ["DESCENDING"]
            or model["class"]["parameterization"] != "REF"
            or len(model["model"]["non_class_predictors"]) != 12 or len(model["class"]["levels"]) != 5
            or (model["score_columns"]["xbeta"], model["score_columns"]["predicted"]) != ("sas_eta", "sas_phat")
            or len(model["ods_output"]["datasets"]) != 5
            or {"id", "case_id", "intercept"} & set(model["model"]["predictors"])):
        raise ValueError("MODEL_DECLARATIONS_UNSUPPORTED")
    return evidence, model


def design_contract(model, mapping):
    if (type(mapping.get("version")) is not int or mapping["version"] != 1
            or mapping.get("numeric_slots_in_non_class_order") != NUMERIC_FIELDS
            or mapping.get("class_slots_in_class_order") != CHARACTER_FIELDS
            or set(mapping["levels"]) != set(CHARACTER_FIELDS)):
        raise ValueError("MODEL_FIELD_MAPPING_INVALID")
    numeric = dict(zip(model["model"]["non_class_predictors"], NUMERIC_FIELDS, strict=True))
    classes = {}
    for term, slot in zip(model["class"]["levels"], CHARACTER_FIELDS, strict=True):
        levels = mapping["levels"][slot]
        if (not isinstance(levels, list) or len(levels) < 2
                or any(not isinstance(pair, list) or len(pair) != 2
                       or any(not isinstance(value, str) for value in pair)
                       or len(pair[0]) != 4 or not pair[0].strip()
                       or any(not 32 <= ord(char) <= 126 for char in pair[0])
                       or not pair[1].isascii() or not pair[1].isidentifier() for pair in levels)
                or len({pair[0] for pair in levels}) != len(levels)
                or len({pair[1] for pair in levels}) != len(levels)
                or sum(pair[1] == "REFERENCE" for pair in levels) != 1):
            raise ValueError("MODEL_CLASS_MAPPING_INVALID")
        classes[term["variable"]] = {"slot": slot, "source_reference": term["reference"],
                                      "alias_levels_in_order": levels}
    columns = ["intercept"]
    for term in model["model"]["predictors"]:
        if term in numeric:
            columns.append(numeric[term])
        else:
            spec = classes[term]
            columns.extend(f"{spec['slot']}:{level}" for _, level in spec["alias_levels_in_order"]
                           if level != "REFERENCE")
    return {"columns": columns, "numeric_source_to_public_slot": numeric,
            "class_source_to_public_levels": classes}


def finite_number(value):
    if not (type(value) is int and abs(value) <= 2**53
            or type(value) is float and math.isfinite(value)):
        raise ValueError("MODEL_FINITE_BINARY64_NUMBER_REQUIRED")
    return float(value)


def coefficients_for(columns, spec):
    entries = spec.get("coefficients")
    if (type(spec.get("version")) is not int or spec["version"] != 1 or spec.get("event") != EVENT
            or not isinstance(entries, list)
            or any(not isinstance(item, list) or len(item) != 2 for item in entries)
            or [item[0] for item in entries] != columns):
        raise ValueError("MODEL_COEFFICIENT_COLUMNS_MISMATCH")
    return [finite_number(value) for _, value in entries]


def encode_row(row, contract):
    if (type(row) is not dict or row.keys() != {"id", "case_id", "default", "numeric_group", "character_group"}
            or type(row["id"]) is not int or abs(row["id"]) > 2**53
            or not isinstance(row["case_id"], str) or len(row["case_id"]) != 3
            or not row["case_id"].isascii() or not row["case_id"].isalnum()
            or type(row["default"]) is not int or row["default"] not in (0, 1)
            or not isinstance(row["numeric_group"], list) or len(row["numeric_group"]) != len(NUMERIC_FIELDS)
            or not isinstance(row["character_group"], list) or len(row["character_group"]) != len(CHARACTER_FIELDS)):
        raise ValueError("MODEL_PREPARED_RECORD_UNSUPPORTED")
    features = {"intercept": 1.0}
    features.update(zip(NUMERIC_FIELDS, map(finite_number, row["numeric_group"]), strict=True))
    characters = dict(zip(CHARACTER_FIELDS, row["character_group"], strict=True))
    for spec in contract["class_source_to_public_levels"].values():
        slot = spec["slot"]
        item = characters[slot]
        levels = dict(spec["alias_levels_in_order"])
        if (type(item) is not dict or item.keys() != {"text"} or not isinstance(item["text"], str)
                or item["text"] not in levels):
            raise ValueError("MODEL_UNKNOWN_CLASS_ALIAS")
        for level in levels.values():
            if level != "REFERENCE":
                features[f"{slot}:{level}"] = float(levels[item["text"]] == level)
    return {"case_id": row["case_id"], "id": row["id"], "default": row["default"],
            "values": [features[name] for name in contract["columns"]]}


def score(values, coefficients):
    try:
        eta = math.fsum(value * coefficient for value, coefficient in zip(values, coefficients, strict=True))
    except OverflowError:
        raise ValueError("MODEL_NONFINITE_LOGIT") from None
    if not math.isfinite(eta):
        raise ValueError("MODEL_NONFINITE_LOGIT")
    exp = math.exp(-abs(eta))
    return eta, 1 / (1 + exp) if eta >= 0 else exp / (1 + exp)


def build_scoring(source, digest, prep, population, scenario):
    evidence, model = recover_model(secure_read(source.parent, source.name, LIMIT), digest)
    fixtures = {}
    for name, expected in FIXTURE_PINS.items():
        raw = secure_read(EXAMPLE, name, LIMIT)
        if identity(raw)["sha256"] != expected:
            raise ValueError("MODEL_PUBLIC_FIXTURE_IDENTITY_MISMATCH")
        fixtures[name] = raw
    contract = design_contract(model, _parse_json(fixtures["MAPPING.json"]))
    coefficients = coefficients_for(contract["columns"], _parse_json(fixtures["COEFFICIENTS.json"]))
    upstream, passed = build_package(prep, population)
    if not passed:
        raise ValueError("MODEL_UPSTREAM_ENGINEERING_COMPARISON_FAILED")
    run = next(row for row in _parse_json(upstream["SCENARIO_RESULTS.json"]) if row["scenario"] == scenario)
    decision = run["continuation"]
    files = {}
    validation = {"candidate_gate": decision, "scoring": "NOT_RUN", "comparison": "NOT_RUN"}
    if decision == "PROCEED":
        eligible = [row["candidate_output"] for row in run["preparation"]["rows"]
                    if row["mode"] == "full" and row["candidate_row_end_reached"]]
        if [row["id"] for row in eligible] != run["handoff_ids"]:
            raise ValueError("MODEL_PREPARED_HANDOFF_MISMATCH")
        design = [encode_row(row, contract) for row in eligible]
        scores = []
        for row in design:
            eta, phat = score(row["values"], coefficients)
            scores.append({"case_id": row["case_id"], "id": row["id"], "eta": eta, "phat": phat})
        expected = [
            {"case_id": "C01", "id": 1, "eta": 1.5, "phat": 0.8175744761936437},
            {"case_id": "C02", "id": 0, "eta": 0.5, "phat": 0.6224593312018546},
        ]
        passed = len(scores) == len(expected) and all(
            all(actual[key] == target[key] for key in ("case_id", "id", "eta"))
            and math.isclose(actual["phat"], target["phat"], rel_tol=0, abs_tol=PROBABILITY_TOLERANCE)
            for actual, target in zip(scores, expected, strict=True)
        )
        validation.update(scoring="EXECUTED", comparison="PASS" if passed else "FAIL", expected=expected,
                          probability_absolute_tolerance=PROBABILITY_TOLERANCE)
        files["DESIGN.json"] = json_bytes({"columns": contract["columns"], "rows": design})
        files["SCORES.json"] = json_bytes({"event": EVENT, "rows": scores})
    model_trace = {key: {**model[key], "anchor": anchor(model[key]["span"])}
                   for key in ("header", "class", "model", "score_columns", "ods_output", "step_check")}
    files["PLAN.json"] = json_bytes({
        "source": evidence["source"], "source_review": identity(json_bytes(evidence)),
        "trace": model_trace, "source_input": model["input"], "source_output": model["output"],
        "design": contract, "fixture_identities": {name: identity(raw) for name, raw in fixtures.items()},
        "candidate_event": EVENT, "historical_event_orientation": "UNVERIFIED",
        "historical_class_encoding": "UNVERIFIED", "historical_dataset_continuity": "UNESTABLISHED",
        "candidate_policy": "PRE_SORT_FULL_MODE_ROW_ENDS_ON_PROCEED_ONLY",
        "candidate_precision": "FINITE_BINARY64_WITH_FSUM_AND_STABLE_SIGMOID",
        **STATISTICS, **AUTHORITY,
    })
    files["VALIDATION.json"] = json_bytes({
        "basis": "PUBLIC_PYTHON_ENGINEERING_EXPECTATIONS", "scenario": scenario,
        **validation, **STATISTICS, **AUTHORITY,
    })
    parent = _parse_json(upstream["MANIFEST.json"])
    script = Path(__file__).resolve()
    files["MANIFEST.json"] = json_bytes({
        "scenario": scenario, "source": evidence["source"], "source_review": identity(json_bytes(evidence)),
        "upstream_manifest": identity(upstream["MANIFEST.json"]), "upstream_inputs": parent["inputs"],
        "fixtures": {name: identity(raw) for name, raw in fixtures.items()},
        "runner": identity(secure_read(script.parent, script.name, LIMIT)),
        "files": {name: identity(raw) for name, raw in files.items()}, **STATISTICS, **AUTHORITY,
    })
    return files, passed


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--model-source", type=Path, required=True)
    parser.add_argument("--model-source-sha256", required=True)
    parser.add_argument("--preparation-evidence", type=Path, required=True)
    parser.add_argument("--population-evidence", type=Path, required=True)
    parser.add_argument("--scenario", choices=SCENARIOS, default="passes")
    parser.add_argument("--destination", required=True, help="fresh /tmp/sas-re-mod2-<label> directory")
    args = parser.parse_args()
    try:
        require_evidence_io()
        scratch, leaf = scratch_destination(args.destination, "mod2")
        model, prep, pop = (path.absolute() for path in
                            (args.model_source, args.preparation_evidence, args.population_evidence))
        ensure_disjoint(scratch / leaf, [model.parent, prep.parent, pop.parent])
        files, passed = build_scoring(model, args.model_source_sha256, prep, pop, args.scenario)
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
                      "manifest_sha256": identity(files["MANIFEST.json"])["sha256"]}).decode(), end="")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
