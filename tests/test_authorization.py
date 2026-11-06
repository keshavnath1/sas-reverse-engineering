"""Pure CP2 contract tests. Synthetic declarations never grant file access."""

from contextlib import ExitStack, redirect_stdout
from copy import deepcopy
from importlib.metadata import version
import io
import json
import sys
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator

from cp2_vectors import envelope
from sas_re.authorization import (authorization_scope_identity, load_authorization_schema,
                                  parse_authorization, project_logical_scope,
                                  validate_authorization, validate_logical_scope)
from sas_re.cli import main
from sas_re.contracts import load_schema, validate_contract
from sas_re.safeio import EvidenceError
import sas_re.semantic_runs  # Preload trusted code before external-I/O tripwires.


class AuthorizationTests(unittest.TestCase):
    def denied(self, value, code=None, gate="FAIL", **kwargs):
        with self.assertRaises(EvidenceError) as error:
            validate_authorization(value, **kwargs)
        self.assertEqual(error.exception.gate, gate)
        if code:
            self.assertEqual(error.exception.code, code)
        self.assertRegex(str(error.exception), r"^[A-Z_]+$")

    def test_public_contract_is_independent_self_contained_and_copy_safe(self):
        schema = load_authorization_schema()
        Draft202012Validator.check_schema(schema)
        def walk(value):
            if isinstance(value, dict):
                if "$ref" in value:
                    self.assertTrue(value["$ref"].startswith("#/$defs/"))
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)
        walk(schema)
        for platform in ("posix", "windows"):
            Draft202012Validator(schema).validate(envelope(platform))
            self.assertIsNone(validate_authorization(envelope(platform), expected_platform=platform))
        schema["properties"].clear()
        self.assertIn("logical_scope", load_authorization_schema()["properties"])
        self.assertIsNone(validate_authorization(envelope()))

    def test_projection_is_separately_shape_validated_but_not_an_io_scope(self):
        value = envelope()
        self.assertIsNone(validate_logical_scope(value["logical_scope"]))
        projection = project_logical_scope(value)
        schema = load_authorization_schema()
        Draft202012Validator({"$defs": schema["$defs"],
                              "$ref": "#/$defs/LegacyScopeIdentityInput"}).validate(projection)
        with self.assertRaises(EvidenceError):
            validate_contract("Scope", projection)
        with self.assertRaises(EvidenceError):
            validate_contract("Scope", value)

    def test_versions_never_fall_back_or_reuse_old_ids(self):
        for field, code in (("authorization_schema_version", "AUTHORIZATION_VERSION_UNSUPPORTED"),
                            ("identity_projection", "AUTHORIZATION_IDENTITY_UNSUPPORTED")):
            value = envelope()
            value[field] = "unreviewed-version-sensitive-input"
            self.denied(value, code, "BLOCKED")
            with self.assertRaises(EvidenceError):
                authorization_scope_identity(value)
            for invalid in (None, [], {}, 1):
                value[field] = invalid
                self.denied(value, "AUTHORIZATION_SCHEMA_INVALID")

    def test_closed_contract_required_fields_and_untrusted_authority(self):
        base = envelope()
        for field in base:
            value = deepcopy(base)
            del value[field]
            self.denied(value, "AUTHORIZATION_SCHEMA_INVALID")
        for field, invalid in (("status", "APPROVED"), ("human_approval", "VERIFIED"),
                               ("access", "WRITE"), ("declared_by", ""),
                               ("approval_reference", "secret\npath")):
            value = deepcopy(base)
            value["authorization"][field] = invalid
            self.denied(value, "AUTHORIZATION_SCHEMA_INVALID")
        for location in ((), ("logical_scope",), ("authorization",),
                         ("bindings", 0), ("logical_scope", "files", 0)):
            value = deepcopy(base)
            target = value
            for key in location:
                target = target[key]
            target["unapproved_extra"] = "private-value"
            self.denied(value, "AUTHORIZATION_SCHEMA_INVALID")

    def test_only_strict_finite_json_values_are_accepted(self):
        values = (None, [], True, "text", object(), {1: "bad"})
        for value in values:
            self.denied(value, "AUTHORIZATION_SCHEMA_INVALID")
        for bad in (float("nan"), float("inf"), ("tuple",), b"bytes", "\ud800"):
            value = envelope()
            value["authorization"]["approval_reference"] = bad
            self.denied(value, "AUTHORIZATION_SCHEMA_INVALID")
        recursive = envelope()
        recursive["loop"] = recursive
        self.denied(recursive, "AUTHORIZATION_SCHEMA_INVALID")

    def test_bytes_parser_is_strict_and_bounded(self):
        value = envelope("windows")
        raw = json.dumps(value).encode("utf-8")
        self.assertEqual(parse_authorization(raw), value)
        for invalid in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":1e999}',
                        b'"\xff"', b'"\\ud800"', b'\xef\xbb\xbf{}', b'{} trailing',
                        b'[' * 66 + b']' * 66, raw.decode(), bytearray(raw),
                        b' ' * (8 * 1024 * 1024 + 1)):
            with self.subTest(kind=type(invalid).__name__):
                with self.assertRaises(EvidenceError) as error:
                    parse_authorization(invalid)
                self.assertEqual(error.exception.code, "AUTHORIZATION_SCHEMA_INVALID")

    def test_binding_map_must_be_exact_and_explicit(self):
        for mode in ("missing", "extra", "duplicate", "wrong-id"):
            value = envelope()
            if mode == "missing":
                value["bindings"].pop()
            elif mode == "extra":
                value["bindings"].append({"root_id": "extra", "platform": "posix", "path": "/extra"})
            elif mode == "duplicate":
                value["bindings"].append(deepcopy(value["bindings"][0]))
            else:
                value["bindings"][0]["root_id"] = "wrong"
            self.denied(value, "AUTHORIZATION_BINDING_MISMATCH")

    def test_platform_is_explicit_data_not_implicitly_this_host(self):
        self.assertIsNone(validate_authorization(envelope("windows"), expected_platform="windows"))
        self.assertIsNone(validate_authorization(envelope("posix"), expected_platform="posix"))
        for expected in ("windows", "darwin", "linux", [], {}):
            self.denied(envelope(), "AUTHORIZATION_PLATFORM_MISMATCH", expected_platform=expected)
        value = envelope()
        value["bindings"][0]["platform"] = "windows"
        self.denied(value, "AUTHORIZATION_PLATFORM_MISMATCH")
        value = envelope("windows")
        value["bindings"][0]["path"] = "/synthetic/sources"
        self.denied(value, "AUTHORIZATION_PATH_INVALID")

    def test_duplicate_logical_identifiers_rejected(self):
        for field, code in (("roots", "AUTHORIZATION_DUPLICATE_ROOT"),
                            ("files", "AUTHORIZATION_DUPLICATE_FILE"),
                            ("dependencies", "AUTHORIZATION_DUPLICATE_DEPENDENCY"),
                            ("log_associations", "AUTHORIZATION_DUPLICATE_ASSOCIATION"),
                            ("module_ids", "AUTHORIZATION_SCHEMA_INVALID")):
            value = envelope()
            value["logical_scope"][field].append(deepcopy(value["logical_scope"][field][0]))
            self.denied(value, code)

    def test_ownership_and_file_key_are_explicit(self):
        for field in ("root_id", "module_id", "file_key"):
            value = envelope()
            value["logical_scope"]["files"][0][field] = "unknown" if field != "file_key" else "src:wrong.sas"
            self.denied(value, "AUTHORIZATION_FILE_KEY_MISMATCH" if field == "file_key"
                        else "AUTHORIZATION_OWNER_MISMATCH")
        value = envelope()
        value["logical_scope"]["synthetic"] = False
        self.denied(value, "AUTHORIZATION_SCHEMA_INVALID")

    def test_missing_and_dynamic_dependencies_must_remain_unresolved(self):
        for target in (None, "src:missing.sas", "absent:outside.sas"):
            value = envelope()
            dependency = value["logical_scope"]["dependencies"][0]
            dependency.update(to_file_key=target, status="UNRESOLVED")
            validate_authorization(value)
            projected = project_logical_scope(value)
            result = next(d for d in projected["dependencies"] if d["dependency_id"] == dependency["dependency_id"])
            self.assertEqual(result, dependency)
            dependency["status"] = "DECLARED"
            self.denied(value, "AUTHORIZATION_UNRESOLVED_REQUIRED")
        value = envelope()
        value["logical_scope"]["dependencies"][0]["from_file_key"] = "src:absent.sas"
        self.denied(value, "AUTHORIZATION_DEPENDENCY_SOURCE_MISSING")
        value = envelope()
        value["logical_scope"]["dependencies"][0]["to_file_key"] = "src:../outside.sas"
        self.denied(value, "AUTHORIZATION_PATH_INVALID")

    def test_log_declarations_not_filename_inference_or_approval(self):
        value = envelope()
        value["logical_scope"]["log_associations"] = []
        validate_authorization(value)
        self.assertEqual(project_logical_scope(value)["log_associations"], [])
        for field, replacement, code in (
            ("run_id", "different-run", "AUTHORIZATION_LOG_RUN_MISMATCH"),
            ("log_file_key", "src:main.sas", "AUTHORIZATION_LOG_FILE_MISMATCH"),
            ("source_file_keys", ["logs:run.log"], "AUTHORIZATION_LOG_SOURCE_MISSING"),
            ("source_file_keys", ["src:absent.sas"], "AUTHORIZATION_LOG_SOURCE_MISSING"),
        ):
            value = envelope()
            value["logical_scope"]["log_associations"][0][field] = replacement
            self.denied(value, code)
        value = envelope()
        duplicate = deepcopy(value["logical_scope"]["log_associations"][0])
        duplicate["association_id"] = "another"
        value["logical_scope"]["log_associations"].append(duplicate)
        self.denied(value, "AUTHORIZATION_LOG_AMBIGUOUS", "BLOCKED")

    def test_combined_path_limits_apply_before_any_access(self):
        value = envelope("windows")
        value["bindings"][0]["path"] = "C:\\" + "x" * 250
        self.denied(value, "AUTHORIZATION_PATH_INVALID")
        value = envelope()
        value["bindings"][0]["path"] = "/" + "/".join(["x" * 250] * 16) + "/" + "y" * 65
        self.denied(value, "AUTHORIZATION_PATH_INVALID")

    def test_pure_validation_does_not_touch_files_processes_or_network(self):
        # Import/trusted package resource reads are explicitly distinct from
        # user-controlled I/O. Warm only bundled schemas/validator instances.
        value = envelope("windows")
        expected = authorization_scope_identity(value)
        raw = json.dumps(value).encode()
        forbidden = AssertionError("CP2 attempted external access")
        with ExitStack() as stack:
            for target in ("builtins.open", "io.open", "os.open", "os.stat", "os.lstat",
                           "os.listdir", "os.scandir", "os.mkdir", "os.link", "os.rename",
                           "os.replace", "os.unlink", "os.getcwd", "os.getenv",
                           "pathlib.Path.resolve", "subprocess.Popen", "subprocess.run",
                           "socket.socket", "socket.create_connection", "socket.getaddrinfo"):
                stack.enter_context(patch(target, side_effect=forbidden))
            validate_authorization(value)
            validate_logical_scope(value["logical_scope"])
            self.assertEqual(authorization_scope_identity(parse_authorization(raw)), expected)
            self.assertTrue(load_authorization_schema())

    def test_valid_windows_envelope_does_not_enable_any_cli_evidence_io(self):
        validate_authorization(envelope("windows"))
        load_schema("1.0")
        load_schema("2.0")
        installed_version = version("sas-reverse-engineering")
        commands = ("discover", "seal-source", "verify-source", "reconstruct-source", "check-reconstruction")
        with ExitStack() as stack:
            stack.enter_context(patch.object(sys, "platform", "win32"))
            # argparse's gettext probes trusted stdlib locale files with stat.
            # Disable translation in this sentinel test, keeping all source and
            # store access tripwires active (including stat itself).
            stack.enter_context(patch("argparse._", side_effect=lambda text: text))
            stack.enter_context(patch("sas_re.cli.version", return_value=installed_version))
            for target in ("builtins.open", "io.open", "os.open", "os.mkdir", "os.stat",
                           "os.link", "os.rename", "os.replace", "pathlib.Path.resolve",
                           "subprocess.Popen", "socket.socket"):
                stack.enter_context(patch(target, side_effect=AssertionError("Blocked command did I/O")))
            for command in commands:
                argv = [command, "--scope", "C:\\Private\\scope.json", "--store", "C:\\Private\\store",
                        "--run", "run-1", "--attempt", "attempt-1"]
                if command == "seal-source":
                    argv += ["--record", "C:\\Private\\record.json"]
                if command in ("verify-source", "check-reconstruction"):
                    argv += ["--verification-attempt", "verify-1"]
                if command in commands[3:]:
                    argv += ["--profile-file", "src:profile.json"]
                if command == "reconstruct-source":
                    argv += ["--inventory-attempt", "inventory-1"]
                output = io.StringIO()
                with redirect_stdout(output):
                    self.assertEqual(main(argv), 2)
                report = json.loads(output.getvalue())
                self.assertEqual(report["stage_gate"], "BLOCKED")
                self.assertEqual(report["findings"], [{"code": "FILESYSTEM_CAPABILITY_UNAVAILABLE", "gate": "BLOCKED"}])
                self.assertEqual(report["artifact_authority"], "DRAFT")
                self.assertEqual(report["benchmark_execution"], "NOT_RUN")

    def test_fresh_import_and_validation_without_posix_backend_git_or_network(self):
        # Reuse the established fresh-process sentinel, not its test methods.
        from test_platform_io import FreshImportTests
        FreshImportTests().run_pure("\n".join([
            "from sas_re.authorization import validate_authorization, project_logical_scope",
            "value = " + repr(envelope("windows")),
            "assert validate_authorization(value) is None",
            "assert 'bindings' not in project_logical_scope(value)",
        ]))


if __name__ == "__main__":
    unittest.main()
