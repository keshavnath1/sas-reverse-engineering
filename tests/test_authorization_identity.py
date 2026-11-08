"""Independent, in-memory CP2 identity proofs; no source filesystem access."""

from copy import deepcopy
import hashlib
import unittest
from unittest.mock import patch

from cp2_vectors import (EXPECTED_IDENTITIES, EXPECTED_PREIMAGE, EXPECTED_SCOPE_SHA256,
                         RAW_OTHER, RAW_VARIANTS, envelope, legacy_scope,
                         operation_payload, oracle_bytes, oracle_files, oracle_hash,
                         oracle_id)
from sas_re._io_common import EvidenceError, canonical_bytes
from sas_re.authorization import (authorization_scope_identity, project_logical_scope,
                                  validate_authorization, validate_logical_scope)
from sas_re.contracts import validate_contract
from sas_re.evidence import build_inventory, digest, identity, record_id, scope_identity


class AuthorizationIdentityTests(unittest.TestCase):
    def assert_changed_scope(self, value, expected):
        """Compare a literal transformed preimage with independent and frozen oracles."""
        self.assertEqual(project_logical_scope(value), expected)
        actual = authorization_scope_identity(value)
        self.assertEqual(actual, oracle_hash(expected))
        self.assertNotEqual(actual, EXPECTED_SCOPE_SHA256)
        old = {"schema_version": "1.0", **deepcopy(value["logical_scope"])}
        old["roots"] = [{"root_id": root["root_id"],
                         "path": "/synthetic/legacy/" + root["root_id"]}
                        for root in old["roots"]]
        validate_contract("Scope", old)
        self.assertEqual(scope_identity(old), actual)

    def test_literal_preimage_and_golden_hash_match_frozen_legacy_algorithm(self):
        old = legacy_scope()
        validate_contract("Scope", old)
        self.assertEqual(hashlib.sha256(oracle_bytes(EXPECTED_PREIMAGE)).hexdigest(),
                         EXPECTED_SCOPE_SHA256)
        self.assertEqual(canonical_bytes(EXPECTED_PREIMAGE), oracle_bytes(EXPECTED_PREIMAGE))
        self.assertEqual(scope_identity(old), EXPECTED_SCOPE_SHA256)
        self.assertEqual(project_logical_scope(envelope()), EXPECTED_PREIMAGE)
        self.assertEqual(authorization_scope_identity(envelope()), EXPECTED_SCOPE_SHA256)

    def test_windows_and_posix_bindings_share_exact_logical_identity(self):
        for platform in ("windows", "posix"):
            with self.subTest(platform=platform):
                value = envelope(platform)
                self.assertIsNone(validate_authorization(value, expected_platform=platform))
                self.assertEqual(project_logical_scope(value, expected_platform=platform),
                                 EXPECTED_PREIMAGE)
                self.assertEqual(authorization_scope_identity(value, expected_platform=platform),
                                 EXPECTED_SCOPE_SHA256)

    def test_declaration_array_order_does_not_change_identity(self):
        for platform in ("windows", "posix"):
            value = envelope(platform)
            for key in ("module_ids", "roots", "files", "dependencies", "log_associations"):
                value["logical_scope"][key].reverse()
            value["logical_scope"]["log_associations"][0]["source_file_keys"].reverse()
            value["bindings"].reverse()
            self.assertEqual(project_logical_scope(value), EXPECTED_PREIMAGE)
            self.assertEqual(authorization_scope_identity(value), EXPECTED_SCOPE_SHA256)

    def test_binding_and_unverified_authorization_metadata_do_not_enter_hash(self):
        for platform in ("windows", "posix"):
            value = envelope(platform)
            for binding in value["bindings"]:
                binding["path"] = ("D:\\Different Local Parent\\" + binding["root_id"]
                                   if platform == "windows" else
                                   "/different local parent/" + binding["root_id"])
            value["authorization"].update(declaration_id="another-declaration",
                                          declared_by="another-synthetic-author",
                                          approval_reference="unverified-reference-2")
            self.assertEqual(authorization_scope_identity(value), EXPECTED_SCOPE_SHA256)
            self.assertEqual(project_logical_scope(value), EXPECTED_PREIMAGE)
            text = oracle_bytes(project_logical_scope(value))
            self.assertNotIn(b"Different Local Parent", text)
            self.assertNotIn(b"approval_reference", text)
            self.assertNotIn(b"platform", text)

    def test_projection_is_detached_and_is_not_a_physical_authorization_scope(self):
        value = envelope()
        original = deepcopy(value)
        projected = project_logical_scope(value)
        self.assertIsNone(validate_logical_scope(value["logical_scope"]))
        with self.assertRaises(EvidenceError):
            validate_contract("Scope", projected)
        projected["files"][0]["module_id"] = "changed"
        projected["roots"][0]["root_id"] = "changed"
        projected["log_associations"][0]["source_file_keys"].clear()
        self.assertEqual(value, original)
        self.assertEqual(project_logical_scope(value), EXPECTED_PREIMAGE)

    def test_logical_declaration_changes_cannot_retain_scope_or_source_identity(self):
        variants = {}
        for name in ("workspace", "run", "modules", "owner", "dependency", "log", "encoding"):
            variants[name] = envelope()
        variants["workspace"]["logical_scope"]["workspace_id"] = "synthetic-other"
        variants["run"]["logical_scope"]["run_id"] = "run-2"
        variants["run"]["logical_scope"]["log_associations"][0]["run_id"] = "run-2"
        variants["modules"]["logical_scope"]["module_ids"].append("report")
        variants["owner"]["logical_scope"]["files"][0]["module_id"] = "prepare"
        variants["dependency"]["logical_scope"]["dependencies"][0]["kind"] = "OTHER"
        variants["log"]["logical_scope"]["log_associations"][0]["execution_id"] = "execution-2"
        variants["encoding"]["logical_scope"]["files"][0]["encoding"] = "latin-1"
        for name, value in variants.items():
            with self.subTest(change=name):
                projected = project_logical_scope(value)
                changed = authorization_scope_identity(value)
                self.assertEqual(changed, oracle_hash(projected))
                self.assertEqual(changed, scope_identity(projected))
                self.assertNotEqual(changed, EXPECTED_SCOPE_SHA256)
                fingerprint = digest({"scope_sha256": changed,
                                      "files": oracle_files(preimage=projected)})
                self.assertNotEqual(fingerprint, EXPECTED_IDENTITIES["lf"]["source_fingerprint"])
                self.assertNotEqual(identity("op", fingerprint, operation_payload()),
                                    EXPECTED_IDENTITIES["lf"]["operation_id"])

    def test_original_byte_vectors_have_pinned_independent_identities(self):
        for variant, expected in EXPECTED_IDENTITIES.items():
            with self.subTest(variant=variant):
                files = oracle_files(variant)
                main = next(item for item in files if item["file_key"] == "src:main.sas")
                self.assertEqual(main["sha256"], expected["main_sha256"])
                self.assertEqual(main["file_id"], expected["main_file_id"])
                for entry in files:
                    payload = {key: value for key, value in entry.items() if key != "file_id"}
                    self.assertEqual(identity("file", "", payload), entry["file_id"])
                fingerprint = digest({"scope_sha256": EXPECTED_SCOPE_SHA256, "files": files})
                self.assertEqual(fingerprint, expected["source_fingerprint"])
                self.assertEqual(oracle_hash({"scope_sha256": EXPECTED_SCOPE_SHA256, "files": files}),
                                 fingerprint)
                self.assertEqual(identity("op", fingerprint, operation_payload()),
                                 expected["operation_id"])
                self.assertEqual(oracle_id("op", fingerprint, operation_payload()),
                                 expected["operation_id"])
                self.assertEqual(record_id("op", fingerprint,
                                           {**operation_payload(), "operation_id": "ignored"},
                                           "operation_id"), expected["operation_id"])
        for field in ("main_sha256", "main_file_id", "source_fingerprint", "operation_id"):
            self.assertEqual(len({item[field] for item in EXPECTED_IDENTITIES.values()}), 4)
        self.assertEqual(authorization_scope_identity(envelope()), EXPECTED_SCOPE_SHA256)

    def test_frozen_inventory_byte_pipeline_matches_independent_vectors_without_io(self):
        # Stub only physical authorization/content transport, never hashing or identity.
        # This is a pure algorithm check, not a filesystem authorization claim.
        root_tokens = {"src": object(), "logs": object()}
        for variant, expected in EXPECTED_IDENTITIES.items():
            with self.subTest(variant=variant):
                def names(token):
                    return (["main.sas", "includes/common.sas"] if token is root_tokens["src"]
                            else ["run.log"])

                def raw(token, relative):
                    root_id = "src" if token is root_tokens["src"] else "logs"
                    key = root_id + ":" + relative
                    return RAW_VARIANTS[variant] if key == "src:main.sas" else RAW_OTHER[key]

                with patch("sas_re.evidence.validate_scope", return_value=root_tokens), \
                     patch("sas_re.evidence.enumerate_files", side_effect=names), \
                     patch("sas_re.evidence.secure_read", side_effect=raw):
                    inventory = build_inventory(legacy_scope(), "synthetic-attempt")
                self.assertEqual(inventory["scope_sha256"], EXPECTED_SCOPE_SHA256)
                self.assertEqual(inventory["files"], oracle_files(variant))
                self.assertEqual(inventory["source_fingerprint"], expected["source_fingerprint"])
                self.assertEqual(inventory["unknowns"][0]["kind"], "DYNAMIC_DEPENDENCY")
                self.assertEqual(inventory["unknowns"][0]["status"], "UNRESOLVED")

    def test_changed_supplied_operation_facts_never_reuse_operation_id(self):
        fingerprint = EXPECTED_IDENTITIES["lf"]["source_fingerprint"]
        payload = operation_payload()
        payload["module_id"] = "prepare"
        self.assertNotEqual(identity("op", fingerprint, payload),
                            EXPECTED_IDENTITIES["lf"]["operation_id"])
        self.assertEqual(identity("op", fingerprint, payload), oracle_id("op", fingerprint, payload))

    def test_equal_normalized_text_does_not_collapse_original_byte_identities(self):
        lf = RAW_VARIANTS["lf"].decode("utf-8")
        self.assertEqual(RAW_VARIANTS["crlf"].decode("utf-8").replace("\r\n", "\n"), lf)
        self.assertEqual(RAW_VARIANTS["bom"].decode("utf-8-sig"), lf)
        for variant in ("crlf", "bom"):
            self.assertNotEqual(EXPECTED_IDENTITIES[variant]["main_file_id"],
                                EXPECTED_IDENTITIES["lf"]["main_file_id"])
            self.assertNotEqual(EXPECTED_IDENTITIES[variant]["source_fingerprint"],
                                EXPECTED_IDENTITIES["lf"]["source_fingerprint"])

    def test_equal_unicode_text_under_different_encodings_changes_identity(self):
        encodings = {"utf-8": b"* caf\xc3\xa9;\n", "latin-1": b"* caf\xe9;\n"}
        results = []
        for encoding, raw in encodings.items():
            self.assertEqual(raw.decode(encoding), "* caf\u00e9;\n")
            value = envelope()
            main = next(item for item in value["logical_scope"]["files"]
                        if item["file_key"] == "src:main.sas")
            main["encoding"] = encoding
            scope_sha = authorization_scope_identity(value)
            payload = {**main, "sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw),
                       "line_count": 1, "newline": "LF"}
            file_id = identity("file", "", payload)
            self.assertEqual(file_id, oracle_id("file", "", payload))
            files = oracle_files()
            files[-1] = {**payload, "file_id": file_id}
            fingerprint = digest({"scope_sha256": scope_sha, "files": files})
            self.assertEqual(fingerprint, oracle_hash({"scope_sha256": scope_sha, "files": files}))
            results.append((scope_sha, file_id, fingerprint,
                            identity("op", fingerprint, operation_payload())))
        for left, right in zip(*results):
            self.assertNotEqual(left, right)

    def test_root_id_rename_updates_all_references_and_changes_identity(self):
        value = envelope()
        scope = value["logical_scope"]
        for root in scope["roots"]:
            if root["root_id"] == "src":
                root["root_id"] = "code"
        for binding in value["bindings"]:
            if binding["root_id"] == "src":
                binding["root_id"] = "code"
        for file in scope["files"]:
            if file["root_id"] == "src":
                file["root_id"] = "code"
                file["file_key"] = "code:" + file["path"]
        for dependency in scope["dependencies"]:
            dependency["from_file_key"] = "code:main.sas"
            if dependency["to_file_key"] is not None:
                dependency["to_file_key"] = "code:includes/common.sas"
        scope["log_associations"][0]["source_file_keys"] = ["code:main.sas", "code:includes/common.sas"]

        expected = deepcopy(EXPECTED_PREIMAGE)
        expected["roots"] = [{"root_id": "code"}, {"root_id": "logs"}]
        log, include, main = expected["files"]
        include.update(root_id="code", file_key="code:includes/common.sas")
        main.update(root_id="code", file_key="code:main.sas")
        expected["files"] = [include, main, log]
        expected["dependencies"][0].update(from_file_key="code:main.sas",
                                            to_file_key="code:includes/common.sas")
        expected["dependencies"][1]["from_file_key"] = "code:main.sas"
        expected["log_associations"][0]["source_file_keys"] = ["code:includes/common.sas", "code:main.sas"]
        self.assert_changed_scope(value, expected)

    def test_logical_filename_rename_updates_references_and_changes_identity(self):
        value = envelope()
        scope = value["logical_scope"]
        main = next(item for item in scope["files"] if item["file_key"] == "src:main.sas")
        main.update(path="entry.sas", file_key="src:entry.sas")
        for dependency in scope["dependencies"]:
            dependency["from_file_key"] = "src:entry.sas"
        scope["log_associations"][0]["source_file_keys"] = ["src:includes/common.sas", "src:entry.sas"]

        expected = deepcopy(EXPECTED_PREIMAGE)
        log, include, main = expected["files"]
        main.update(path="entry.sas", file_key="src:entry.sas")
        expected["files"] = [log, main, include]
        for dependency in expected["dependencies"]:
            dependency["from_file_key"] = "src:entry.sas"
        expected["log_associations"][0]["source_file_keys"] = ["src:entry.sas", "src:includes/common.sas"]
        self.assert_changed_scope(value, expected)

    def test_file_addition_and_valid_removal_change_scope_identity(self):
        added = envelope()
        extra = {"file_key": "src:extra.cfg", "root_id": "src", "path": "extra.cfg",
                 "kind": "CONFIG", "module_id": "prepare", "encoding": "ascii"}
        added["logical_scope"]["files"].append(deepcopy(extra))
        expected_added = deepcopy(EXPECTED_PREIMAGE)
        expected_added["files"].insert(1, extra)
        with self.subTest(change="addition"):
            self.assert_changed_scope(added, expected_added)

        removed = envelope()
        scope = removed["logical_scope"]
        scope["files"] = [item for item in scope["files"] if item["kind"] != "INCLUDE"]
        include_link = next(item for item in scope["dependencies"] if item["kind"] == "INCLUDE")
        include_link.update(to_file_key=None, status="UNRESOLVED")
        scope["log_associations"][0]["source_file_keys"] = ["src:main.sas"]
        expected_removed = deepcopy(EXPECTED_PREIMAGE)
        del expected_removed["files"][1]
        expected_removed["dependencies"][0].update(to_file_key=None, status="UNRESOLVED")
        expected_removed["log_associations"][0]["source_file_keys"] = ["src:main.sas"]
        with self.subTest(change="removal_with_unresolved_dependency"):
            self.assert_changed_scope(removed, expected_removed)

    def test_explicit_log_source_membership_changes_identity(self):
        value = envelope()
        value["logical_scope"]["log_associations"][0]["source_file_keys"] = ["src:main.sas"]
        expected = deepcopy(EXPECTED_PREIMAGE)
        expected["log_associations"][0]["source_file_keys"] = ["src:main.sas"]
        self.assert_changed_scope(value, expected)

    def test_two_log_associations_have_order_independent_identity(self):
        value = envelope()
        other_log = {"file_key": "logs:other.log", "root_id": "logs", "path": "other.log",
                     "kind": "LOG", "module_id": "analyze", "encoding": "utf-8"}
        other_link = {"association_id": "another-log", "log_file_key": "logs:other.log",
                      "source_file_keys": ["src:main.sas"], "execution_id": "execution-2",
                      "run_id": "run-1", "status": "DECLARED"}
        value["logical_scope"]["files"].append(deepcopy(other_log))
        value["logical_scope"]["log_associations"].append(deepcopy(other_link))
        expected = deepcopy(EXPECTED_PREIMAGE)
        expected["files"].insert(0, other_log)
        expected["log_associations"].insert(0, other_link)
        self.assert_changed_scope(value, expected)
        first_hash = authorization_scope_identity(value)
        value["logical_scope"]["log_associations"].reverse()
        value["logical_scope"]["files"].reverse()
        self.assert_changed_scope(value, expected)
        self.assertEqual(authorization_scope_identity(value), first_hash)

    def test_unsupported_identity_projection_fails_closed(self):
        for projection in ("sas-re-scope-v2", "unknown", ""):
            value = envelope()
            value["identity_projection"] = projection
            for action in (validate_authorization, project_logical_scope, authorization_scope_identity):
                with self.subTest(projection=projection, action=action.__name__):
                    with self.assertRaises(EvidenceError) as caught:
                        action(value)
                    self.assertEqual(caught.exception.code, "AUTHORIZATION_IDENTITY_UNSUPPORTED")
                    self.assertEqual(caught.exception.gate, "BLOCKED")


if __name__ == "__main__":
    unittest.main()
