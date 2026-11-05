"""Append-only P2A attempts. Deterministic consistency is not semantic acceptance."""

from pathlib import Path

from sas_re.contracts import validate_contract
from sas_re.evidence import build_inventory, digest, validate_record, validate_scope
from sas_re.runs import _inventory_report
from sas_re.safeio import AttemptStore, EvidenceError, read_json


def error_report(error: EvidenceError) -> dict:
    failed = error.gate == "FAIL"
    result = {"schema_version": "2.0", "stage_gate": error.gate,
              "structural_verification": "FAILED" if failed else "BLOCKED",
              "source_consistency": "FAILED" if failed else "BLOCKED",
              "reconstruction_status": "NOT_RUN", "semantic_verification": "UNVERIFIABLE",
              "semantic_acceptance": "BLOCKED", "benchmark_execution": "NOT_RUN",
              "artifact_authority": "DRAFT", "findings": [{"code": error.code, "gate": error.gate}],
              "coverage": None}
    validate_contract("Report", result, version="2.0")
    return result


def load_profile(scope: dict, profile_file_key: str) -> dict:
    """Read only an explicitly declared CONFIG identity, never a caller path."""
    roots = validate_scope(scope)
    item = next((f for f in scope["files"] if f["file_key"] == profile_file_key), None)
    if item is None or item["kind"] != "CONFIG" or item["encoding"] not in {"utf-8", "ascii"}:
        raise EvidenceError("PROFILE_NOT_AUTHORIZED")
    profile = read_json(roots[item["root_id"]] / item["path"])
    validate_contract("Profile", profile, version="2.0")
    return profile


def _subject(store, scope, subject, version, stage):
    artifacts, seal = store.read_attempt(scope["workspace_id"], scope["run_id"], subject)
    validate_contract("Seal", seal, version=version)
    started = read_json(store.path / scope["workspace_id"] / scope["run_id"] / subject / "attempt.json")
    validate_contract("Attempt", started, version=version)
    if seal["module_ids"] != sorted(scope["module_ids"]):
        raise EvidenceError("SEAL_OWNER_MISMATCH")
    if seal["stage"] not in stage or seal["stage_gate"] == "FAIL":
        raise EvidenceError("INELIGIBLE_RECONSTRUCTION_SUBJECT", "BLOCKED")
    required = {"source_inventory.json", "validation_report.json"}
    if seal["stage"] != "INVENTORY":
        required.add("source_record.json")
    if set(artifacts) != required:
        raise EvidenceError("STAGE_ARTIFACT_MISMATCH")
    inventory = artifacts["source_inventory.json"]
    validate_contract("Inventory", inventory)
    if inventory != build_inventory(scope, subject):
        raise EvidenceError("STALE_SOURCE")
    return artifacts, seal


def execute(command: str, scope_path: Path, store_path: Path, run_id: str,
            attempt_id: str, profile_file_key: str, inventory_attempt: str | None = None,
            verification_attempt: str | None = None) -> tuple[dict, int]:
    # Import lazily: installed v1 commands retain their original dependency path.
    from sas_re.semantic import reconstruct, revision_map, validate_v2

    try:
        if command not in {"reconstruct-source", "check-reconstruction"}:
            raise EvidenceError("UNKNOWN_P2A_COMMAND")
        scope = read_json(scope_path)
        roots = validate_scope(scope)
        if scope["run_id"] != run_id:
            raise EvidenceError("RUN_OWNER_MISMATCH")
        is_check = command == "check-reconstruction"
        subject = attempt_id if is_check else inventory_attempt
        output = verification_attempt if is_check else attempt_id
        stage = "RECONSTRUCTION_CHECK" if is_check else "RECONSTRUCTION"
        metadata = {"schema_version": "2.0", "workspace_id": scope["workspace_id"],
                    "run_id": run_id, "attempt_id": output, "module_ids": sorted(scope["module_ids"]),
                    "stage": stage, "publication_state": "STARTED"}
        validate_contract("Attempt", metadata, version="2.0")
        validate_contract("Attempt", {**metadata, "attempt_id": subject}, version="2.0")
        if subject == output:
            raise EvidenceError("VERIFICATION_ATTEMPT_REUSED", "BLOCKED")
        store = AttemptStore(store_path, list(roots.values()))
        attempt = store.begin(scope["workspace_id"], run_id, output, metadata)
        artifacts, subject_hash, lineage = {}, None, None
        try:
            profile = load_profile(scope, profile_file_key)
            prior, prior_seal = _subject(store, scope, subject, "2.0" if is_check else "1.0",
                                        {"RECONSTRUCTION"} if is_check else {"INVENTORY", "RECORD"})
            subject_hash = digest(prior_seal)
            previous_inventory = prior["source_inventory.json"]
            if is_check:
                prior_report = prior["validation_report.json"]
                validate_contract("ReconstructionReport", prior_report, version="2.0")
                result = validate_v2(scope, previous_inventory, prior["source_record.json"], profile,
                                     profile_file_key=profile_file_key)
                base = {k: v for k, v in prior_report.items()
                        if k not in {"subject_attempt_id", "subject_seal_sha256", "lineage"}}
                if base != result or result["stage_gate"] != prior_seal["stage_gate"]:
                    raise EvidenceError("REPORT_SEAL_MISMATCH")
                lineage = prior_report["lineage"]
                # Validate the predecessor binding as well; never trust claimed lineage.
                old, old_seal = _subject(store, scope, prior_report["subject_attempt_id"],
                                        "1.0", {"INVENTORY", "RECORD"})
                if digest(old_seal) != prior_report["subject_seal_sha256"]:
                    raise EvidenceError("PREDECESSOR_SEAL_MISMATCH")
                old_result = (validate_record(scope, old["source_inventory.json"], old["source_record.json"])
                              if old_seal["stage"] == "RECORD" else _inventory_report(old["source_inventory.json"]))
                if old_result != old["validation_report.json"] or old_result["stage_gate"] != old_seal["stage_gate"]:
                    raise EvidenceError("REPORT_SEAL_MISMATCH")
                expected_lineage = (revision_map(old["source_record.json"], prior["source_record.json"])
                                    if old_seal["stage"] == "RECORD" else None)
                if lineage != expected_lineage:
                    raise EvidenceError("REVISION_LINEAGE_MISMATCH")
            else:
                stored = prior["validation_report.json"]
                validate_contract("Report", stored)
                expected = (validate_record(scope, previous_inventory, prior["source_record.json"])
                            if prior_seal["stage"] == "RECORD" else _inventory_report(previous_inventory))
                if expected != stored or stored["stage_gate"] != prior_seal["stage_gate"]:
                    raise EvidenceError("REPORT_SEAL_MISMATCH")
                inventory = build_inventory(scope, output)
                artifacts["source_inventory.json"] = inventory
                graph = reconstruct(scope, inventory, profile, profile_file_key=profile_file_key)
                result = validate_v2(scope, inventory, graph, profile, profile_file_key=profile_file_key)
                artifacts["source_record.json"] = graph
                if prior_seal["stage"] == "RECORD":
                    lineage = revision_map(prior["source_record.json"], graph)
            # No mutation of prior inventory/graph/seal, even for unchanged bytes.
            if previous_inventory != build_inventory(scope, subject):
                raise EvidenceError("SOURCE_CHANGED_DURING_VERIFICATION")
        except EvidenceError as error:
            result = error_report(error)
            artifacts.pop("source_record.json", None)
        result = {**result, "subject_attempt_id": subject,
                  "subject_seal_sha256": subject_hash, "lineage": lineage}
        validate_contract("VerificationReport" if is_check else "ReconstructionReport", result, version="2.0")
        artifacts["verification_report.json" if is_check else "validation_report.json"] = result
        seal = {**metadata, "publication_state": "COMPLETE", "stage_gate": result["stage_gate"],
                "artifact_authority": "DRAFT", "semantic_verification": "UNVERIFIABLE",
                "semantic_acceptance": "BLOCKED"}
        validate_contract("Seal", {**seal, "artifacts": {
            "attempt.json": digest(metadata), **{k: digest(v) for k, v in artifacts.items()}}}, version="2.0")
        installed = attempt.publish(artifacts, seal)
        result = {**result, **{k: metadata[k] for k in ("workspace_id", "run_id", "attempt_id")},
                  "seal_sha256": digest(installed)}
    except EvidenceError as error:
        result = error_report(error)
    return result, {"PASS": 0, "FAIL": 1, "BLOCKED": 2}[result["stage_gate"]]
