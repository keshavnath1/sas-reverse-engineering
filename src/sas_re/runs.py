"""Explicit P1 attempts: inventory, supplied records and fresh integrity checks."""

from pathlib import Path

from sas_re.contracts import validate_contract
from sas_re.evidence import (build_inventory, digest, error_report, validate_record,
                             validate_scope, validation_report)
from sas_re.safeio import AttemptStore, EvidenceError, read_json


def _inventory_report(inventory: dict) -> dict:
    findings = ([{"code": "UNRESOLVED_UNKNOWNS", "gate": "BLOCKED"}]
                if inventory["unknowns"] else [])
    return validation_report(findings)


def _publish(attempt, metadata: dict, artifacts: dict, report: dict) -> dict:
    seal = {**metadata, "publication_state": "COMPLETE",
            "stage_gate": report["stage_gate"], "artifact_authority": "DRAFT",
            "semantic_verification": "UNVERIFIABLE"}
    # Check the complete contract before installing any artifact or seal.
    validate_contract("Seal", {**seal, "artifacts": {
        "attempt.json": digest(metadata), **{k: digest(v) for k, v in artifacts.items()}}})
    installed = attempt.publish(artifacts, seal)
    return {**report, **{k: metadata[k] for k in ("workspace_id", "run_id", "attempt_id")},
            "seal_sha256": digest(installed)}


def _verify_subject(store: AttemptStore, scope: dict, subject: str,
                    artifacts: dict, seal: dict) -> dict:
    validate_contract("Seal", seal)
    started = read_json(store.path / scope["workspace_id"] / scope["run_id"] / subject / "attempt.json")
    validate_contract("Attempt", started)
    if seal["module_ids"] != sorted(scope["module_ids"]):
        raise EvidenceError("SEAL_OWNER_MISMATCH")
    expected = {"source_inventory.json", "validation_report.json"}
    if seal["stage"] == "RECORD":
        expected.add("source_record.json")
    elif seal["stage"] != "INVENTORY":
        raise EvidenceError("UNSUPPORTED_SUBJECT_STAGE", "BLOCKED")
    if seal["stage_gate"] != "PASS":
        raise EvidenceError("SUBJECT_NOT_PASSED", "BLOCKED")
    if set(artifacts) != expected:
        raise EvidenceError("STAGE_ARTIFACT_MISMATCH")
    inventory = artifacts["source_inventory.json"]
    validate_contract("Inventory", inventory)
    if inventory != build_inventory(scope, subject):
        raise EvidenceError("STALE_SOURCE")
    stored = artifacts["validation_report.json"]
    validate_contract("Report", stored)
    actual = (validate_record(scope, inventory, artifacts["source_record.json"])
              if seal["stage"] == "RECORD" else _inventory_report(inventory))
    if stored != actual or stored["stage_gate"] != seal["stage_gate"]:
        raise EvidenceError("REPORT_SEAL_MISMATCH")
    # Recheck bytes at the end as well as during individual citation validation.
    if inventory != build_inventory(scope, subject):
        raise EvidenceError("SOURCE_CHANGED_DURING_VERIFICATION")
    return actual


def execute(command: str, scope_path: Path, store_path: Path, run_id: str,
            attempt_id: str, record_path: Path | None = None,
            verification_attempt: str | None = None) -> tuple[dict, int]:
    """No subprocess, SAS execution, semantic inference or implicit scope expansion.

    Before a valid scope/store reservation, failures are returned only. Afterwards
    validation failures are sealed as failures; an I/O interruption leaves an
    incomplete, non-reusable attempt, never a successful seal.
    """
    try:
        if command not in {"discover", "seal-source", "verify-source"}:
            raise EvidenceError("UNKNOWN_P1_COMMAND")
        scope = read_json(scope_path)
        roots = validate_scope(scope)
        if run_id != scope["run_id"]:
            raise EvidenceError("RUN_OWNER_MISMATCH")
        stage = {"discover": "INVENTORY", "seal-source": "RECORD", "verify-source": "VERIFICATION"}[command]
        output_attempt = verification_attempt if command == "verify-source" else attempt_id
        metadata = {"schema_version": "1.0", "workspace_id": scope["workspace_id"],
                    "run_id": run_id, "attempt_id": output_attempt,
                    "module_ids": sorted(scope["module_ids"]), "stage": stage,
                    "publication_state": "STARTED"}
        validate_contract("Attempt", metadata)
        if command == "verify-source":
            validate_contract("Attempt", {**metadata, "attempt_id": attempt_id})
            if attempt_id == output_attempt:
                raise EvidenceError("VERIFICATION_ATTEMPT_REUSED", "BLOCKED")
        store = AttemptStore(store_path, list(roots.values()))
        attempt = store.begin(scope["workspace_id"], run_id, output_attempt, metadata)
        artifacts = {}
        subject_hash = None
        try:
            if command == "verify-source":
                subject_artifacts, subject_seal = store.read_attempt(scope["workspace_id"], run_id, attempt_id)
                subject_hash = digest(subject_seal)
                result = _verify_subject(store, scope, attempt_id, subject_artifacts, subject_seal)
            else:
                inventory = build_inventory(scope, output_attempt)
                artifacts["source_inventory.json"] = inventory
                if command == "seal-source":
                    if record_path is None:
                        raise EvidenceError("RECORD_REQUIRED")
                    graph = read_json(record_path)
                    result = validate_record(scope, inventory, graph)
                    artifacts["source_record.json"] = graph
                else:
                    result = _inventory_report(inventory)
                if inventory != build_inventory(scope, output_attempt):
                    raise EvidenceError("SOURCE_CHANGED_DURING_VERIFICATION")
        except EvidenceError as error:
            result = error_report(error)
            # An invalid supplied record must not masquerade as accepted evidence.
            artifacts.pop("source_record.json", None)
        if command == "verify-source":
            result = {**result, "subject_attempt_id": attempt_id,
                      "subject_seal_sha256": subject_hash}
            validate_contract("VerificationReport", result)
            artifacts["verification_report.json"] = result
        else:
            artifacts["validation_report.json"] = result
        result = _publish(attempt, metadata, artifacts, result)
    except EvidenceError as error:
        result = error_report(error)
    return result, {"PASS": 0, "FAIL": 1, "BLOCKED": 2}[result["stage_gate"]]
