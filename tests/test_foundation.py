import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from sas_re.baseline import check_checkout, check_remote, metadata, report
from sas_re.cli import PLANNED, main

ROOT = Path(__file__).resolve().parents[1]


class CLITests(unittest.TestCase):
    def invoke(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(list(args))
        return code, json.loads(out.getvalue())

    def test_status_is_implemented_phase_only(self):
        code, data = self.invoke("status")
        self.assertEqual(code, 0)
        self.assertEqual(data["phase"], "P2A")
        self.assertEqual(data["semantic_acceptance"], "BLOCKED")
        self.assertEqual(data["independent_evaluation"], "NOT_IMPLEMENTED")
        self.assertEqual(data["semantic_verification"], "UNVERIFIABLE")
        self.assertEqual(data["benchmark_execution"], "NOT_RUN")
        self.assertEqual(data["downstream_integration"], "NOT_IMPLEMENTED")
        self.assertNotIn("stage_gate", data)

    def test_planned_commands_never_read_inputs_or_create_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            before = set(Path(folder).iterdir())
            for command in PLANNED:
                with self.subTest(command=command), patch("pathlib.Path.read_bytes", side_effect=AssertionError("read")):
                    code, data = self.invoke(command, "--scope", folder, "--run", "RUN-1")
                    self.assertEqual(code, 3)
                    self.assertEqual(data["stage_gate"], "BLOCKED")
                    self.assertFalse(data["inputs_read"])
            self.assertEqual(before, set(Path(folder).iterdir()))

    def test_installed_entrypoint_and_resources_outside_checkout(self):
        with tempfile.TemporaryDirectory() as folder:
            exe = Path(os.sys.executable).parent / "sas-re"
            for args in (["status"], ["--version"], ["--help"]):
                result = subprocess.run([str(exe), *args], cwd=folder, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run([str(exe), "status"], cwd=folder, capture_output=True, text=True)
            self.assertEqual(json.loads(result.stdout)["downstream_commit"], metadata()["downstream"]["commit"])

    def test_check_requires_explicit_target(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            main(["check-baseline"])
        self.assertEqual(error.exception.code, 2)

    def test_unknown_command_rejected(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            main(["generate"])
        self.assertEqual(error.exception.code, 2)

    def test_unknown_status_option_rejected(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            main(["status", "--approve"])


class CheckoutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.git("init", "-q")
        self.git("config", "user.name", "Synthetic Test")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        (self.root / "contract.txt").write_text("Synthetic baseline only\n")
        self.git("add", "contract.txt")
        self.git("commit", "-qm", "synthetic baseline")
        self.baseline = {"downstream": {
            "commit": self.git("rev-parse", "HEAD"),
            "file_sha256": {"contract.txt": hashlib.sha256((self.root / "contract.txt").read_bytes()).hexdigest()}}}

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, stderr=subprocess.PIPE, text=True).strip()

    def test_clean_matching_checkout(self):
        self.assertEqual(check_checkout(self.root, self.baseline)["stage_gate"], "PASS")

    def test_modified_pinned_file_fails(self):
        (self.root / "contract.txt").write_text("modified")
        result = check_checkout(self.root, self.baseline)
        self.assertEqual(result["stage_gate"], "FAIL")
        self.assertEqual(result["changed_or_missing_files"], ["contract.txt"])

    def test_missing_pinned_file_fails(self):
        (self.root / "contract.txt").unlink()
        self.assertEqual(check_checkout(self.root, self.baseline)["stage_gate"], "FAIL")

    def test_wrong_head_fails_even_if_pinned_file_unchanged(self):
        self.git("commit", "--allow-empty", "-qm", "new commit")
        self.assertEqual(check_checkout(self.root, self.baseline)["stage_gate"], "FAIL")

    def test_untracked_files_prevent_clean_match(self):
        (self.root / "unrelated.txt").write_text("new")
        self.assertEqual(check_checkout(self.root, self.baseline)["stage_gate"], "FAIL")

    def test_symlink_is_not_followed(self):
        target = self.root / "contract.txt"
        target.unlink()
        target.symlink_to(self.root / "absent")
        self.assertEqual(check_checkout(self.root, self.baseline)["stage_gate"], "FAIL")

    def test_subdirectory_not_implicitly_promoted_to_repo(self):
        child = self.root / "subdir"
        child.mkdir()
        self.assertEqual(check_checkout(child, self.baseline)["stage_gate"], "BLOCKED")

    def test_missing_checkout_is_blocked(self):
        self.assertEqual(check_checkout(self.root / "absent", self.baseline)["stage_gate"], "BLOCKED")


class RemoteTests(unittest.TestCase):
    def setUp(self):
        self.baseline = metadata()
        self.ref = "refs/heads/" + self.baseline["downstream"]["branch"]

    def test_matching_remote(self):
        with patch("sas_re.baseline._git", return_value=self.baseline["downstream"]["commit"] + "\t" + self.ref):
            self.assertEqual(check_remote(self.baseline)["stage_gate"], "PASS")

    def test_remote_drift(self):
        with patch("sas_re.baseline._git", return_value="f" * 40 + "\t" + self.ref):
            self.assertEqual(check_remote(self.baseline)["stage_gate"], "FAIL")

    def test_network_failure_is_blocked_not_pass(self):
        with patch("sas_re.baseline._git", side_effect=OSError("private diagnostics")):
            result = check_remote(self.baseline)
            self.assertEqual(result["stage_gate"], "BLOCKED")
            self.assertNotIn("private diagnostics", json.dumps(result))

    def test_missing_ambiguous_or_malformed_response(self):
        for output in ["", "bad\t" + self.ref, "f" * 40 + "\trefs/heads/wrong", "x\ny"]:
            with self.subTest(output=output), patch("sas_re.baseline._git", return_value=output):
                self.assertEqual(check_remote(self.baseline)["stage_gate"], "BLOCKED")

    def test_remote_timeout(self):
        with patch("sas_re.baseline._git", side_effect=subprocess.TimeoutExpired("git", 30)):
            self.assertEqual(check_remote(self.baseline)["stage_gate"], "BLOCKED")

    def test_report_exit_codes(self):
        for gate, code in [("PASS", 0), ("FAIL", 1), ("BLOCKED", 2)]:
            with self.subTest(gate=gate), patch("sas_re.baseline.check_remote", return_value={"stage_gate": gate}):
                self.assertEqual(report(None, True)[1], code)

    def test_no_requested_check_is_blocked(self):
        self.assertEqual(report(None, False)[1], 2)


class RepositoryTests(unittest.TestCase):
    def test_approved_reference_hash(self):
        spec = metadata()["specification"]
        self.assertEqual(hashlib.sha256((ROOT / spec["path"]).read_bytes()).hexdigest(), spec["sha256"])

    def test_private_paths_ignored(self):
        paths = ["intake/data.txt", "private/note.md", "artifacts/result.json", "gold/answers.json",
                 "work.sas", "run.log", "report.lst", "data.csv", ".env", ".env.prod",
                 ".aws/config", "secret.key", "credentials.json", "private.zip", "UPPER.SAS", "RUN.LOG"]
        for path in paths:
            with self.subTest(path=path):
                result = subprocess.run(["git", "check-ignore", "--no-index", "-q", path], cwd=ROOT)
                self.assertEqual(result.returncode, 0)
        result = subprocess.run(["git", "check-ignore", "--no-index", "-q", metadata()["specification"]["path"]], cwd=ROOT)
        self.assertEqual(result.returncode, 1)

    def test_guard_rejects_forced_private_paths_and_credentials(self):
        spec = importlib.util.spec_from_file_location("guard", ROOT / "scripts/check_repository.py")
        guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guard)
        for path in ["DATA.SAS", "gold/expected.json", ".env.prod", "x.PEM", "nested/intake/input.txt"]:
            self.assertTrue(guard.prohibited_path(path))
        self.assertFalse(guard.prohibited_path("src/sas_re/cli.py"))
        self.assertTrue(any(p.search(b"AKIA" + b"A" * 16) for p in guard.SECRET_PATTERNS))

    def test_guard_checks_index_even_if_worktree_was_cleaned(self):
        spec = importlib.util.spec_from_file_location("guard", ROOT / "scripts/check_repository.py")
        guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guard)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            subprocess.run(["git", "init", "-q", folder], check=True)
            (root / "src/sas_re/data").mkdir(parents=True)
            (root / "reference").mkdir()
            (root / "reference/spec.zip").write_bytes(b"synthetic test archive placeholder")
            baseline = {"specification": {"path": "reference/spec.zip", "sha256":
                        hashlib.sha256((root / "reference/spec.zip").read_bytes()).hexdigest()}}
            (root / "src/sas_re/data/baseline.json").write_text(json.dumps(baseline))
            (root / "note.txt").write_bytes(b"AKIA" + b"A" * 16)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            (root / "note.txt").write_text("cleaned after staging")
            self.assertIn("Possible credential material: note.txt", guard.check(root))


if __name__ == "__main__":
    unittest.main()
