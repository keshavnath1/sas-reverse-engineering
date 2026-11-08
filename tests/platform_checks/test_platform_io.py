"""Backend capability boundaries fail closed; simulated Windows selection is not native qualification."""

import builtins
import contextlib
from importlib import import_module
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import textwrap
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from sas_re import platform_io, safeio
from sas_re.baseline import check_checkout
from sas_re.cli import main
from sas_re.contracts import load_schema
from sas_re.runs import execute as execute_p1
from sas_re.semantic_runs import execute as execute_p2a


DENIAL = "FILESYSTEM_CAPABILITY_UNAVAILABLE"
COMMANDS = (
    "discover",
    "seal-source",
    "verify-source",
    "reconstruct-source",
    "check-reconstruction",
)


class CapabilityTests(unittest.TestCase):
    def assert_blocked(self, result, reason):
        self.assertEqual(result["backend"], "blocked")
        self.assertEqual(result["evidence_io"], "BLOCKED")
        self.assertEqual(result["reason"], reason)
        self.assertTrue(result["capabilities"])
        self.assertEqual(set(result["capabilities"].values()), {"BLOCKED"})
        json.dumps(result, allow_nan=False)

    def test_simulated_windows_cannot_select_posix_backend(self):
        with patch.object(sys, "platform", "win32"):
            result = platform_io.filesystem_capabilities()
        self.assertEqual(result["platform"], "win32")
        self.assert_blocked(result, "WINDOWS_BACKEND_NOT_IMPLEMENTED")

    def test_unknown_platform_is_blocked(self):
        # Stub only selector metadata, never global os.name or Path behavior.
        with (
            patch.object(sys, "platform", "unsupported-test-platform"),
            patch.object(platform_io, "os", SimpleNamespace(name="posix")),
        ):
            self.assert_blocked(platform_io.filesystem_capabilities(), "PLATFORM_NOT_SUPPORTED")

    def test_windows_os_name_cannot_select_posix_backend(self):
        with (
            patch.object(sys, "platform", "linux"),
            patch.object(platform_io, "os", SimpleNamespace(name="nt")),
        ):
            self.assert_blocked(
                platform_io.filesystem_capabilities(), "WINDOWS_BACKEND_NOT_IMPLEMENTED"
            )

    @unittest.skipUnless(
        os.name == "posix" and sys.platform in {"darwin", "linux"},
        "POSIX prerequisite test; this skip does not qualify native evidence I/O",
    )
    def test_missing_nofollow_primitive_is_blocked(self):
        with patch.object(os, "O_NOFOLLOW"):
            del os.O_NOFOLLOW
            result = platform_io.filesystem_capabilities()
            self.assert_blocked(result, "POSIX_PRIMITIVES_UNAVAILABLE")
            self.assertTrue(
                any(item.endswith("O_NOFOLLOW") for item in result["missing_primitives"])
            )
            self.assert_denied(platform_io.require_evidence_io)

    @unittest.skipUnless(
        os.name == "posix" and sys.platform in {"darwin", "linux"},
        "POSIX prerequisite test; this skip does not qualify native evidence I/O",
    )
    def test_missing_descriptor_relative_support_is_blocked(self):
        with patch.object(os, "supports_dir_fd", set()):
            result = platform_io.filesystem_capabilities()
            self.assert_blocked(result, "POSIX_PRIMITIVES_UNAVAILABLE")
            self.assertTrue(result["missing_primitives"])
            self.assert_denied(platform_io.get_backend)

    def assert_denied(self, operation):
        with self.assertRaises(safeio.EvidenceError) as error:
            operation()
        self.assertEqual(error.exception.code, DENIAL)
        self.assertEqual(error.exception.gate, "BLOCKED")

    def test_requirement_and_dispatch_raise_the_same_bounded_error(self):
        with patch.object(sys, "platform", "win32"):
            self.assert_denied(platform_io.require_evidence_io)
            self.assert_denied(platform_io.get_backend)

    def test_broken_backend_import_never_falls_back_to_ordinary_io(self):
        for failure in (
            ImportError("synthetic missing module"),
            AttributeError("synthetic missing API"),
        ):

            def broken_backend(name):
                if name == "sas_re._filesystem._posix_io":
                    raise failure
                return import_module(name)

            with (
                self.subTest(failure=type(failure).__name__),
                patch.object(
                    platform_io,
                    "filesystem_capabilities",
                    return_value={"evidence_io": "AVAILABLE"},
                ),
                patch.object(platform_io, "import_module", side_effect=broken_backend),
                patch("builtins.open", side_effect=AssertionError("Fallback open")),
                patch("os.open", side_effect=AssertionError("Fallback OS open")),
            ):
                self.assert_denied(platform_io.get_backend)

    def assert_lock_unavailable(self, fake_fcntl, missing, *, import_failure=None):
        def guarded_import(name):
            if name == "fcntl":
                if import_failure is not None:
                    raise import_failure
                return fake_fcntl
            if name == "sas_re._filesystem._posix_io":
                self.fail("Missing locking primitive allowed backend import")
            return import_module(name)

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            source = root / "source"
            source.mkdir()
            store = root / "never-created-store"
            with patch.object(platform_io, "import_module", side_effect=guarded_import):
                result = platform_io.filesystem_capabilities()
                self.assert_blocked(result, "POSIX_PRIMITIVES_UNAVAILABLE")
                self.assertIn(missing, result["missing_primitives"])
                self.assert_denied(platform_io.get_backend)
                self.assert_denied(lambda: safeio.AttemptStore(store, [source]))
            self.assertEqual(list(root.iterdir()), [source])
            self.assertFalse(store.exists())

    @unittest.skipUnless(
        os.name == "posix" and sys.platform in {"darwin", "linux"},
        "POSIX prerequisite test; this skip does not qualify native evidence I/O",
    )
    def test_absent_flock_blocks_before_store_creation(self):
        fake = SimpleNamespace(LOCK_EX=2, LOCK_NB=4, LOCK_UN=8)
        self.assert_lock_unavailable(fake, "fcntl.flock")

    @unittest.skipUnless(
        os.name == "posix" and sys.platform in {"darwin", "linux"},
        "POSIX prerequisite test; this skip does not qualify native evidence I/O",
    )
    def test_noncallable_flock_blocks_before_store_creation(self):
        fake = SimpleNamespace(flock=None, LOCK_EX=2, LOCK_NB=4, LOCK_UN=8)
        self.assert_lock_unavailable(fake, "fcntl.flock")

    @unittest.skipUnless(
        os.name == "posix" and sys.platform in {"darwin", "linux"},
        "POSIX prerequisite test; this skip does not qualify native evidence I/O",
    )
    def test_missing_or_invalid_lock_flags_block_before_store_creation(self):
        absent = object()
        for name in ("LOCK_EX", "LOCK_NB", "LOCK_UN"):
            for value in (absent, None, 0):
                with self.subTest(flag=name, value="absent" if value is absent else value):
                    fake = SimpleNamespace(
                        flock=lambda *args: None, LOCK_EX=2, LOCK_NB=4, LOCK_UN=8
                    )
                    if value is absent:
                        delattr(fake, name)
                    else:
                        setattr(fake, name, value)
                    self.assert_lock_unavailable(fake, "fcntl." + name)

    @unittest.skipUnless(
        os.name == "posix" and sys.platform in {"darwin", "linux"},
        "POSIX prerequisite test; this skip does not qualify native evidence I/O",
    )
    def test_fcntl_import_failure_blocks_before_store_creation(self):
        for failure in (
            ImportError("synthetic missing extension"),
            OSError("synthetic failed extension load"),
        ):
            with self.subTest(failure=type(failure).__name__):
                self.assert_lock_unavailable(None, "fcntl", import_failure=failure)

    def test_mutating_a_report_cannot_authorize_io(self):
        with patch.object(sys, "platform", "win32"):
            result = platform_io.filesystem_capabilities()
            result["evidence_io"] = "AVAILABLE"
            result["backend"] = "posix"
            result["capabilities"]["source_read"] = "AVAILABLE"
            self.assert_blocked(
                platform_io.filesystem_capabilities(), "WINDOWS_BACKEND_NOT_IMPLEMENTED"
            )
            self.assert_denied(platform_io.get_backend)

    @unittest.skipUnless(
        os.name == "posix" and sys.platform in {"darwin", "linux"},
        "Native POSIX dispatch only; this skip does not qualify Windows evidence I/O",
    )
    def test_available_native_posix_dispatch_and_read(self):
        result = platform_io.filesystem_capabilities()
        self.assertEqual(result["evidence_io"], "AVAILABLE", result)
        self.assertEqual(result["backend"], "posix")
        self.assertIsNone(result["reason"])
        self.assertEqual(result["missing_primitives"], [])
        self.assertEqual(platform_io.get_backend().__name__, "sas_re._filesystem._posix_io")
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            raw = b"/* SYNTHETIC CP1 bytes */\r\ndata x;\nrun;\r\n"
            (root / "source.txt").write_bytes(raw)
            self.assertEqual(safeio.secure_read(root, "source.txt"), raw)
            self.assertEqual(safeio.enumerate_files(root), ["source.txt"])


class FreshImportTests(unittest.TestCase):
    """Fresh interpreters deny POSIX imports and process/network activity.

    Setting sys.platform exercises selection only. It does not emulate Windows
    path, ACL, filesystem, interpreter or dependency behavior.
    """

    def run_pure(self, body):
        script = (
            textwrap.dedent("""
            import contextlib
            import importlib.abc
            import io
            import json
            import pathlib
            import socket
            import subprocess
            import sys

            # Some host stdlib imports load fcntl. Remove that cached module so
            # a product import cannot bypass the finder in this fresh process.
            sys.modules.pop("fcntl", None)
            class NoPosixImport(importlib.abc.MetaPathFinder):
                def find_spec(self, fullname, path=None, target=None):
                    if fullname in {"fcntl", "sas_re._filesystem._posix_io"}:
                        raise AssertionError("Forbidden POSIX import: " + fullname)
                    return None
            sys.meta_path.insert(0, NoPosixImport())
            sys.platform = "win32"  # Selection simulation, never qualification.
            def forbidden(*args, **kwargs):
                raise AssertionError("Pure command attempted process/network access")
            subprocess.Popen = forbidden
            subprocess.run = forbidden
            subprocess.check_call = forbidden
            subprocess.check_output = forbidden
            socket.socket = forbidden
            socket.create_connection = forbidden
            socket.getaddrinfo = forbidden
            from sas_re.cli import main
        """)
            + "\n"
            + textwrap.dedent(body)
            + textwrap.dedent("""
            assert "fcntl" not in sys.modules
            assert "sas_re._filesystem._posix_io" not in sys.modules
        """)
        )
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run(
                [sys.executable, "-c", script],
                cwd=folder,
                capture_output=True,
                text=True,
                timeout=30,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_help_without_posix_import_git_or_network(self):
        self.run_pure("""
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                try:
                    main(["--help"])
                except SystemExit as error:
                    assert error.code == 0
                else:
                    raise AssertionError("argparse help did not exit")
            assert "reconstruct-source" in output.getvalue()
        """)

    def test_version_without_posix_import_git_or_network(self):
        self.run_pure("""
            from importlib.metadata import version
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                try:
                    main(["--version"])
                except SystemExit as error:
                    assert error.code == 0
                else:
                    raise AssertionError("argparse version did not exit")
            assert output.getvalue().strip() == version("sas-reverse-engineering")
        """)

    def test_status_reports_blocked_io_and_unchanged_authority(self):
        self.run_pure("""
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                assert main(["status"]) == 0
            result = json.loads(output.getvalue())
            assert result["phase"] == "P2A"
            assert result["artifact_authority"] == "DRAFT"
            assert result["semantic_acceptance"] == "BLOCKED"
            assert result["semantic_verification"] == "UNVERIFIABLE"
            assert result["benchmark_execution"] == "NOT_RUN"
            assert result["filesystem_capabilities"]["evidence_io"] == "BLOCKED"
            assert result["filesystem_capabilities"]["reason"] == "WINDOWS_BACKEND_NOT_IMPLEMENTED"
        """)

    def test_both_contract_versions_and_shared_identity_code_import(self):
        self.run_pure("""
            import hashlib
            from importlib.resources import files
            from sas_re.contracts import load_schema, validate_contract
            from sas_re.evidence import digest
            from sas_re.safeio import canonical_bytes
            from sas_re.semantic import revision_map
            expected = {
                "1": "15e3265fac9af300b40967580998ef4ac90eb1d830a10ce201855fc4ec2738a2",
                "2": "093216d16bb02e91a3997c97175420bf2257982f5a5fe3a4374ef92f7637a90b",
            }
            for major, checksum in expected.items():
                schema = load_schema(major + ".0")
                assert "Report" in schema["$defs"]
                raw = files("sas_re").joinpath("contracts", "v" + major,
                                               "evidence.schema.json").read_bytes()
                assert hashlib.sha256(raw).hexdigest() == checksum
            value = {"z": "synthetic", "a": [1, True, None]}
            raw = b'{"a":[1,true,null],"z":"synthetic"}\\n'
            assert canonical_bytes(value) == raw
            assert digest(value) == hashlib.sha256(raw).hexdigest()
        """)


class BlockedIOTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.scope = self.root / "scope.json"
        self.record = self.root / "record.json"
        self.store = self.root / "new-store"
        self.source = self.root / "source.txt"
        self.scope.write_bytes(b"SYNTHETIC scope must never be opened")
        self.record.write_bytes(b"SYNTHETIC record must never be opened")
        self.source.write_bytes(b"SYNTHETIC source must never be opened")
        self.before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        # Error-report validation may read trusted bundled schemas, not intake.
        load_schema("1.0")
        load_schema("2.0")

    @contextlib.contextmanager
    def denied_environment(self):
        def guarded_open(original):
            def guarded(file, *args, **kwargs):
                if not isinstance(file, int):
                    path = os.fsdecode(file)
                    if path == str(self.root) or path.startswith(str(self.root) + os.sep):
                        self.fail("Capability denial attempted scoped read or write")
                return original(file, *args, **kwargs)

            return guarded

        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(sys, "platform", "win32"))
            stack.enter_context(patch("builtins.open", side_effect=guarded_open(builtins.open)))
            stack.enter_context(patch("io.open", side_effect=guarded_open(io.open)))
            for name in ("open", "mkdir", "link", "unlink", "remove", "rename", "replace"):
                stack.enter_context(
                    patch.object(os, name, side_effect=AssertionError("Unexpected OS I/O: " + name))
                )
            stack.enter_context(
                patch("subprocess.run", side_effect=AssertionError("Unexpected subprocess"))
            )
            stack.enter_context(
                patch("subprocess.Popen", side_effect=AssertionError("Unexpected subprocess"))
            )
            stack.enter_context(
                patch("socket.socket", side_effect=AssertionError("Unexpected network"))
            )
            yield
        self.assertFalse(self.store.exists())
        self.assertEqual(self.before, {p.name: p.read_bytes() for p in self.root.iterdir()})

    def assert_blocked_report(self, result, code, *, p2a=False):
        self.assertEqual(code, 2)
        self.assertEqual(result["stage_gate"], "BLOCKED")
        self.assertEqual(result["artifact_authority"], "DRAFT")
        self.assertEqual(result["semantic_verification"], "UNVERIFIABLE")
        self.assertEqual(result["benchmark_execution"], "NOT_RUN")
        self.assertEqual(result["findings"], [{"code": DENIAL, "gate": "BLOCKED"}])
        self.assertNotIn(str(self.root), json.dumps(result))
        if p2a:
            self.assertEqual(result["semantic_acceptance"], "BLOCKED")
            self.assertEqual(result["reconstruction_status"], "NOT_RUN")

    def test_all_five_direct_workflows_deny_before_inputs_or_store(self):
        for command in COMMANDS:
            with self.subTest(command=command), self.denied_environment():
                if command in COMMANDS[:3]:
                    result, code = execute_p1(
                        command, self.scope, self.store, "run1", "attempt1", self.record, "verify1"
                    )
                else:
                    result, code = execute_p2a(
                        command,
                        self.scope,
                        self.store,
                        "run1",
                        "attempt1",
                        "profile1",
                        "inventory1",
                        "verify1",
                    )
                self.assert_blocked_report(result, code, p2a=command in COMMANDS[3:])

    def test_all_five_cli_workflows_deny_before_inputs_or_store(self):
        for command in COMMANDS:
            argv = [
                command,
                "--scope",
                str(self.scope),
                "--store",
                str(self.store),
                "--run",
                "run1",
                "--attempt",
                "attempt1",
            ]
            if command == "seal-source":
                argv += ["--record", str(self.record)]
            if command in {"verify-source", "check-reconstruction"}:
                argv += ["--verification-attempt", "verify1"]
            if command in COMMANDS[3:]:
                argv += ["--profile-file", "profile1"]
            if command == "reconstruct-source":
                argv += ["--inventory-attempt", "inventory1"]
            with self.subTest(command=command), self.denied_environment():
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    code = main(argv)
                self.assert_blocked_report(
                    json.loads(output.getvalue()), code, p2a=command in COMMANDS[3:]
                )

    def test_direct_safeio_entrypoints_deny_without_access(self):
        operations = {
            "require_safe_root": lambda: safeio.require_safe_root(self.root),
            "ensure_disjoint": lambda: safeio.ensure_disjoint(self.store, [self.root]),
            "secure_read": lambda: safeio.secure_read(self.root, "source.txt"),
            "enumerate_files": lambda: safeio.enumerate_files(self.root),
            "read_json": lambda: safeio.read_json(self.scope),
            "AttemptStore": lambda: safeio.AttemptStore(self.store, [self.root]),
        }
        for name, operation in operations.items():
            with self.subTest(entrypoint=name), self.denied_environment():
                with self.assertRaises(safeio.EvidenceError) as error:
                    operation()
                self.assertEqual((error.exception.code, error.exception.gate), (DENIAL, "BLOCKED"))

    def test_attempt_methods_recheck_capability_before_using_objects(self):
        # A retained object must not bypass selection when its platform is denied.
        # Deliberately missing internals prove denial precedes any backend access.
        store = object.__new__(safeio.AttemptStore)
        attempt = safeio.Attempt(self.store / "attempt1", "workspace1", "run1", "attempt1", (1, 1))
        operations = (
            lambda: store.begin("workspace1", "run1", "attempt1", {}),
            lambda: store.read_attempt("workspace1", "run1", "attempt1"),
            lambda: attempt.publish({}, {}),
        )
        for operation in operations:
            with self.subTest(operation=operation), self.denied_environment():
                with self.assertRaises(safeio.EvidenceError) as error:
                    operation()
                self.assertEqual((error.exception.code, error.exception.gate), (DENIAL, "BLOCKED"))

    def test_local_baseline_denies_before_resolving_or_running_git(self):
        baseline = {"downstream": {"commit": "a" * 40, "file_sha256": {}}}
        with (
            self.denied_environment(),
            patch.object(Path, "resolve", side_effect=AssertionError("Path resolution")),
        ):
            result = check_checkout(self.root, baseline)
        self.assertEqual(result["stage_gate"], "BLOCKED")
        self.assertTrue(result["reason"])
        self.assertNotIn(str(self.root), json.dumps(result))


if __name__ == "__main__":
    unittest.main()
