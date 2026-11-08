"""Synthetic contract-shape tests; these do not establish source semantics."""

from copy import deepcopy
import json
import unittest

from jsonschema import Draft202012Validator

from sas_re.contracts import CONTRACT_NAMES, load_schema, validate_contract
from sas_re.safeio import EvidenceError


HASH = "a" * 64
OP = "op_" + HASH
DS = "ds_" + HASH
COL = "col_" + HASH
EDGE = "edge_" + HASH
LOG = "log_" + HASH


def examples():
    """Small shape-valid examples, deliberately not a sealed evidence bundle."""
    base = {"schema_version": "1.0", "workspace_id": "synthetic", "run_id": "run-1"}
    ownership = {**base, "attempt_id": "attempt-1", "module_ids": ["module-1"]}
    unverified = {"semantic_verification": "UNVERIFIABLE"}
    authority = {"artifact_authority": "DRAFT", **unverified}
    root = {"root_id": "src", "path": "/synthetic/source"}
    scoped = {"file_key": "src:program.sas", "root_id": "src", "path": "program.sas",
              "kind": "SAS", "module_id": "module-1", "encoding": "utf-8"}
    file = {**scoped, "sha256": HASH, "size_bytes": 1, "line_count": 1,
            "newline": "LF", "file_id": "file_" + HASH}
    citation = {"file_key": "src:program.sas", "source_sha256": HASH,
                "line_start": 1, "line_end": 1, "excerpt_sha256": HASH}
    dependency = {"dependency_id": "dependency-1", "from_file_key": "src:program.sas",
                  "to_file_key": None, "kind": "MACRO", "status": "UNRESOLVED"}
    association = {"association_id": "association-1", "log_file_key": "src:run.log",
                   "source_file_keys": ["src:program.sas"], "execution_id": "execution-1",
                   "run_id": "run-1", "status": "DECLARED"}
    issue = {"issue_id": "unknown-1", "kind": "DYNAMIC_DEPENDENCY",
             "file_keys": ["src:program.sas"], "operation_ids": [], "status": "UNRESOLVED"}
    scope = {**base, "module_ids": ["module-1"], "synthetic": True, "roots": [root],
             "files": [scoped], "dependencies": [dependency], "log_associations": []}
    inventory = {**ownership, "scope_sha256": HASH, "source_fingerprint": HASH,
                 "files": [file], "dependencies": [dependency],
                 "log_associations": [], "unknowns": [issue]}
    dataset = {"dataset_id": DS, "module_id": "module-1", "name": "work.example", **unverified}
    column = {"column_id": COL, "module_id": "module-1", "dataset_id": DS,
              "name": "value", **unverified}
    operation = {"operation_id": OP, "module_id": "module-1", "kind": "DATA_STEP",
                 "citations": [citation], "reads": [], "writes": [DS, COL],
                 "stateful_constructs": [], "classification": "OBSERVATION", **unverified}
    edge = {"edge_id": EDGE, "from_operation_id": OP, "to_operation_id": "op_" + "b" * 64,
            "type": "DATA", "node_ids": [DS], "evidence_operation_ids": [OP],
            "classification": "INFERENCE", **unverified}
    log = {"observation_id": LOG, "module_id": "module-1", "run_id": "run-1",
           "attempt_id": "attempt-1", "association_id": "association-1",
           "execution_id": "execution-1", "log_citation": {**citation, "file_key": "src:run.log"},
           "source_operation_ids": [OP], "metric": "ROW_COUNT", "value": 12,
           "classification": "OBSERVATION", **unverified}
    coverage = {"file_count": 1, "operation_count": 1, "dataset_count": 1,
                "column_count": 1, "edge_count": 0, "log_observation_count": 0,
                "unknown_count": 1, "contradiction_count": 0, "covered_source_file_count": 1}
    graph = {**ownership, "scope_manifest_sha256": HASH, "source_fingerprint": HASH,
             **authority, "datasets": [dataset], "columns": [column], "operations": [operation],
             "edges": [], "log_observations": [], "unknowns": [issue],
             "contradictions": [], "coverage": coverage}
    seal = {**ownership, "stage": "RECORD", "stage_gate": "BLOCKED", **authority,
            "publication_state": "COMPLETE", "artifacts": {"source_record.json": HASH}}
    view = {**base, "attempt_id": "attempt-1", "module_id": "module-1",
            "source_record_sha256": HASH, "operation_ids": [OP], "dataset_ids": [DS],
            "column_ids": [COL], "edge_ids": [], "log_observation_ids": [], **authority}
    revision = {"schema_version": "1.0", "previous_record_sha256": HASH,
                "current_record_sha256": "b" * 64, "retained_operation_ids": [],
                "removed_operation_ids": [OP], "added_operation_ids": ["op_" + "b" * 64],
                "semantic_equivalence": "NOT_ASSERTED"}
    attempt = {**ownership, "stage": "RECORD", "publication_state": "STARTED"}
    finding = {"code": "MISSING_DEPENDENCY", "gate": "BLOCKED"}
    report = {"schema_version": "1.0", "stage_gate": "BLOCKED",
              "structural_verification": "BLOCKED", "benchmark_execution": "NOT_RUN",
              **authority, "findings": [finding], "coverage": coverage}
    verification = {**report, "subject_attempt_id": "attempt-0", "subject_seal_sha256": HASH}
    return {"Root": root, "ScopedFile": scoped, "File": file, "Citation": citation,
            "Dependency": dependency, "LogAssociation": association, "Issue": issue,
            "Scope": scope, "Inventory": inventory, "Dataset": dataset, "Column": column,
            "Operation": operation, "Edge": edge, "LogObservation": log, "Coverage": coverage,
            "Graph": graph, "Seal": seal, "ModuleView": view, "RevisionMap": revision,
            "Attempt": attempt, "Finding": finding, "Report": report,
            "VerificationReport": verification}


class ContractTests(unittest.TestCase):
    def assert_invalid(self, name, value):
        with self.assertRaises(EvidenceError) as caught:
            validate_contract(name, value)
        self.assertEqual(str(caught.exception), "SCHEMA_INVALID")

    def test_bundle_is_valid_draft_2020_12_with_internal_refs_only(self):
        bundle = load_schema()
        self.assertEqual(bundle["$schema"], "https://json-schema.org/draft/2020-12/schema")
        Draft202012Validator.check_schema(bundle)
        self.assertEqual(set(CONTRACT_NAMES), set(bundle["$defs"]))

        def inspect(value):
            if isinstance(value, dict):
                if "$ref" in value:
                    self.assertTrue(value["$ref"].startswith("#/$defs/"))
                    self.assertIn(value["$ref"].removeprefix("#/$defs/"), CONTRACT_NAMES)
                for child in value.values():
                    inspect(child)
            elif isinstance(value, list):
                for child in value:
                    inspect(child)
        inspect(bundle)

    def test_all_document_contracts_validate(self):
        for name, example in examples().items():
            with self.subTest(contract=name):
                self.assertIsNone(validate_contract(name, example))

    def test_returned_schema_cannot_change_trusted_validation(self):
        bundle = load_schema()
        bundle["$defs"]["Graph"]["additionalProperties"] = True
        self.assert_invalid("Graph", {**examples()["Graph"], "human_approved": True})
        self.assertFalse(load_schema()["$defs"]["Graph"]["additionalProperties"])

    def test_every_document_contract_rejects_unknown_properties(self):
        for name, example in examples().items():
            with self.subTest(contract=name):
                self.assert_invalid(name, {**example, "private_source_excerpt": "SYNTHETIC PRIVATE MARKER"})

    def test_every_declared_property_is_required(self):
        for name, example in examples().items():
            for key in example:
                with self.subTest(contract=name, missing=key):
                    changed = deepcopy(example)
                    del changed[key]
                    self.assert_invalid(name, changed)

    def test_nested_unknown_properties_are_rejected(self):
        graph = deepcopy(examples()["Graph"])
        graph["operations"][0]["citations"][0]["source_excerpt"] = "SYNTHETIC PRIVATE MARKER"
        self.assert_invalid("Graph", graph)

    def test_p1_cannot_claim_semantic_verification_or_human_approval(self):
        for name, example in examples().items():
            if "semantic_verification" in example:
                for status in ["VERIFIED", "PARTIAL", "UNSUPPORTED", "CONTRADICTED", "HUMAN_APPROVED"]:
                    with self.subTest(contract=name, status=status):
                        self.assert_invalid(name, {**example, "semantic_verification": status})
            if "artifact_authority" in example:
                with self.subTest(contract=name, field="artifact_authority"):
                    self.assert_invalid(name, {**example, "artifact_authority": "HUMAN_APPROVED"})
        self.assert_invalid("RevisionMap", {**examples()["RevisionMap"], "semantic_equivalence": "VERIFIED"})

    def test_verification_status_vocabulary_is_separate_from_stage_gates(self):
        for status in ["VERIFIED", "PARTIAL", "UNSUPPORTED", "CONTRADICTED", "UNVERIFIABLE"]:
            validate_contract("VerificationStatus", status)
            self.assert_invalid("StageGate", status)
        for gate in ["PASS", "FAIL", "BLOCKED"]:
            validate_contract("StageGate", gate)
            self.assert_invalid("VerificationStatus", gate)

    def test_classifications_remain_distinct(self):
        for classification in ["OBSERVATION", "INFERENCE", "ASSUMPTION", "HYPOTHESIS", "MEASUREMENT"]:
            validate_contract("Operation", {**examples()["Operation"], "classification": classification})
        self.assert_invalid("LogObservation", {**examples()["LogObservation"], "classification": "MEASUREMENT"})

    def test_boolean_and_nonfinite_numbers_are_not_measurements_or_counts(self):
        for name, field in [("Citation", "line_start"), ("Citation", "line_end"),
                            ("File", "size_bytes"), ("File", "line_count"),
                            ("Coverage", "operation_count"), ("LogObservation", "value")]:
            for invalid in [True, False, -1, float("nan"), float("inf"), float("-inf")]:
                with self.subTest(contract=name, field=field, invalid=repr(invalid)):
                    self.assert_invalid(name, {**examples()[name], field: invalid})

    def test_safe_ids_hashes_and_node_ids_reject_wrong_syntax(self):
        for name, values in {
            "SafeId": ["", "../run", "a/b", "a:b", "run\n", "x" * 65],
            "Sha256": ["a" * 63, "g" * 64, HASH + "\n", "A" * 64],
            "FileKey": ["program.sas", "../root:program.sas", "src:", "src:program.sas\n"],
            "OperationId": [HASH, "ds_" + HASH, OP + "\n"],
            "NodeId": [OP, "column_" + HASH, "dataset"],
            "SasName": ["1name", "bad name", "valid\n"],
        }.items():
            for value in values:
                with self.subTest(contract=name, value=repr(value)):
                    self.assert_invalid(name, value)

    def test_scope_requires_explicit_synthetic_opt_in_and_nonempty_scope(self):
        scope = examples()["Scope"]
        for value in [False, 1, "true", None]:
            self.assert_invalid("Scope", {**scope, "synthetic": value})
        for key in ["module_ids", "roots", "files"]:
            self.assert_invalid("Scope", {**scope, key: []})
        self.assert_invalid("Root", {"root_id": "src", "path": "relative/source"})

    def test_unique_reference_lists_reject_duplicates(self):
        for name, key in [("Scope", "module_ids"), ("Operation", "writes"),
                          ("Edge", "evidence_operation_ids"), ("ModuleView", "operation_ids"),
                          ("LogAssociation", "source_file_keys")]:
            example = examples()[name]
            self.assert_invalid(name, {**example, key: [example[key][0], example[key][0]]})

    def test_module_views_accept_references_without_editable_facts(self):
        view = examples()["ModuleView"]
        self.assert_invalid("ModuleView", {**view, "operations": [examples()["Operation"]]})
        self.assert_invalid("ModuleView", {**view, "operation_ids": [examples()["Operation"]]})

    def test_seals_require_complete_state_and_known_artifact_filenames(self):
        seal = examples()["Seal"]
        self.assert_invalid("Seal", {**seal, "publication_state": "STARTED"})
        self.assert_invalid("Seal", {**seal, "artifacts": {}})
        for filename in ["../source_record.json", "/tmp/source_record.json", "seal.json", "private.txt"]:
            self.assert_invalid("Seal", {**seal, "artifacts": {filename: HASH}})

    def test_log_associations_require_explicit_identity_and_declared_status(self):
        association = examples()["LogAssociation"]
        self.assert_invalid("LogAssociation", {**association, "source_file_keys": []})
        self.assert_invalid("LogAssociation", {**association, "status": "INFERRED_FROM_FILENAME"})
        self.assert_invalid("LogObservation", {**examples()["LogObservation"], "source_operation_ids": []})

    def test_verification_report_can_record_unreadable_target_without_inventing_hash(self):
        report = examples()["VerificationReport"]
        validate_contract("VerificationReport", {**report, "subject_seal_sha256": None})
        self.assert_invalid("VerificationReport", {**report, "subject_seal_sha256": "UNKNOWN"})

    def test_non_json_inputs_unknown_contracts_and_cycles_are_redacted(self):
        for name in ["https://example.invalid/private", "../../schema", "", None, []]:
            with self.subTest(contract=name):
                self.assert_invalid(name, {"private": "SYNTHETIC PRIVATE MARKER"})
        for value in [b"bytes", {1: "not a JSON key"}, {"set"}, ("tuple",)]:
            self.assert_invalid("Scope", value)
        cycle = []
        cycle.append(cycle)
        self.assert_invalid("Scope", cycle)

    def test_schema_only_does_not_claim_cross_reference_or_source_truth(self):
        graph = examples()["Graph"]
        graph["operations"][0]["reads"] = ["ds_" + "b" * 64]
        validate_contract("Graph", graph)
        self.assertEqual(graph["semantic_verification"], "UNVERIFIABLE")
        self.assertEqual(graph["artifact_authority"], "DRAFT")
        self.assertNotIn("stage_gate", graph)
        # The full deterministic verifier must reject this dangling reference.
        self.assertIn("ds_" + "b" * 64, json.dumps(graph))


if __name__ == "__main__":
    unittest.main()
