"""Coordinate P1 inventory, supplied-record, and fresh integrity-check attempts.

JSON schemas remain the record authority. Checks use original source bytes and
bounded evidence validation; SAS is never executed. A passing gate does not
establish semantic equivalence, and published artifacts remain draft evidence.
"""

from pathlib import Path

from sas_re.contracts import validate_contract
from sas_re.evidence import (
    build_inventory,
    digest,
    error_report,
    validate_record,
    validate_scope,
    validation_report,
)
from sas_re.safeio import AttemptStore, EvidenceError, read_json
from sas_re.platform_io import require_evidence_io


def _inventory_report(inventory: dict) -> dict:
    """Build an inventory gate report, blocking on unresolved unknowns."""
    findings = [{"code": "UNRESOLVED_UNKNOWNS", "gate": "BLOCKED"}] if inventory["unknowns"] else []
    return validation_report(findings)


def _publish(attempt, metadata: dict, artifacts: dict, report: dict) -> dict:
    """Validate and publish a draft seal, then return its digest with the report.

    Publication writes the reserved attempt's artifacts and seal. Completion is
    distinct from a passing gate and from semantic verification.
    """
    seal = {
        **metadata,
        "publication_state": "COMPLETE",
        "stage_gate": report["stage_gate"],
        "artifact_authority": "DRAFT",
        "semantic_verification": "UNVERIFIABLE",
    }
    # Check the complete contract before installing any artifact or seal.
    validate_contract(
        "Seal",
        {
            **seal,
            "artifacts": {
                "attempt.json": digest(metadata),
                **{k: digest(v) for k, v in artifacts.items()},
            },
        },
    )
    installed = attempt.publish(artifacts, seal)
    return {
        **report,
        **{k: metadata[k] for k in ("workspace_id", "run_id", "attempt_id")},
        "seal_sha256": digest(installed),
    }


def _verify_subject(
    store: AttemptStore, scope: dict, subject: str, artifacts: dict, seal: dict
) -> dict:
    """Recheck a passed inventory or record subject without modifying it.

    Rebuild the scoped inventory and validation report rather than trusting the
    stored gate alone. Ownership, stage, artifact, or freshness mismatches raise
    EvidenceError; passing these checks is not a semantic-equivalence proof.
    """
    validate_contract("Seal", seal)
    started = read_json(
        store.path / scope["workspace_id"] / scope["run_id"] / subject / "attempt.json"
    )
    validate_contract("Attempt", started)
    if seal["module_ids"] != sorted(scope["module_ids"]):
        raise EvidenceError("SEAL_OWNER_MISMATCH")
    # Each supported stage has an exact artifact set, not an extensible payload.
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
    actual = (
        validate_record(scope, inventory, artifacts["source_record.json"])
        if seal["stage"] == "RECORD"
        else _inventory_report(inventory)
    )
    if stored != actual or stored["stage_gate"] != seal["stage_gate"]:
        raise EvidenceError("REPORT_SEAL_MISMATCH")
    # Recheck bytes after citation validation; this is not a continuous snapshot.
    if inventory != build_inventory(scope, subject):
        raise EvidenceError("SOURCE_CHANGED_DURING_VERIFICATION")
    return actual


def execute(
    command: str,
    scope_path: Path,
    store_path: Path,
    run_id: str,
    attempt_id: str,
    record_path: Path | None = None,
    verification_attempt: str | None = None,
) -> tuple[dict, int]:
    """Run a bounded evidence stage and return its report and gate exit code.

    No subprocess, SAS execution, semantic inference, or implicit scope expansion
    occurs. Verification reads a subject but publishes into a separate attempt.
    Before reservation, refusals are returned without an attempt. Afterward,
    caught validation failures are included in publication; interrupted or failed
    publication can leave an incomplete, non-reusable attempt, not a successful
    seal. EvidenceError becomes a report; other exceptions propagate.

    Args:
        command: One of discover, seal-source, or verify-source.
        scope_path: Path to the authorized scope JSON record.
        store_path: Root of the attempt store to read and write.
        run_id: Run owner, which must match the scope.
        attempt_id: Output attempt for discovery or sealing; subject attempt for
            verification.
        record_path: Supplied record JSON, required for seal-source.
        verification_attempt: Separate output attempt ID for verify-source.

    Returns:
        A report and exit code: 0 for PASS, 1 for FAIL, or 2 for BLOCKED. A passing
        gate does not confer semantic verification or non-draft authority.
    """
    try:
        if command not in {"discover", "seal-source", "verify-source"}:
            raise EvidenceError("UNKNOWN_P1_COMMAND")
        require_evidence_io()
        scope = read_json(scope_path)
        roots = validate_scope(scope)
        if run_id != scope["run_id"]:
            raise EvidenceError("RUN_OWNER_MISMATCH")
        stage = {"discover": "INVENTORY", "seal-source": "RECORD", "verify-source": "VERIFICATION"}[
            command
        ]
        # Verification owns a new attempt; it never republishes its subject.
        output_attempt = verification_attempt if command == "verify-source" else attempt_id
        metadata = {
            "schema_version": "1.0",
            "workspace_id": scope["workspace_id"],
            "run_id": run_id,
            "attempt_id": output_attempt,
            "module_ids": sorted(scope["module_ids"]),
            "stage": stage,
            "publication_state": "STARTED",
        }
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
                subject_artifacts, subject_seal = store.read_attempt(
                    scope["workspace_id"], run_id, attempt_id
                )
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
            result = {
                **result,
                "subject_attempt_id": attempt_id,
                "subject_seal_sha256": subject_hash,
            }
            validate_contract("VerificationReport", result)
            artifacts["verification_report.json"] = result
        else:
            artifacts["validation_report.json"] = result
        result = _publish(attempt, metadata, artifacts, result)
    except EvidenceError as error:
        result = error_report(error)
    return result, {"PASS": 0, "FAIL": 1, "BLOCKED": 2}[result["stage_gate"]]
