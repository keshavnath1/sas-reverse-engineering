"""Synthetic CP2 lexical policy tests; these do not qualify native I/O."""

from contextlib import ExitStack
from copy import deepcopy
import os
import unittest
from unittest.mock import patch

from sas_re._authorization_paths import validate_bindings, validate_file_paths
from sas_re._io_common import EvidenceError


def binding(path, *, platform="posix", root_id="synthetic"):
    return {"root_id": root_id, "platform": platform, "path": path}


def file_path(path, *, root_id="synthetic"):
    return {"root_id": root_id, "path": path}


class NativeBindingSyntaxTests(unittest.TestCase):
    def assert_invalid(self, path, *, platform="posix"):
        with self.assertRaises(EvidenceError) as error:
            validate_bindings(platform, [binding(path, platform=platform)])
        self.assertEqual(error.exception.code, "AUTHORIZATION_PATH_INVALID")
        self.assertEqual(str(error.exception), "AUTHORIZATION_PATH_INVALID")
        self.assertEqual(error.exception.gate, "FAIL")

    def assert_alias(self, paths, *, platform="posix"):
        values = [binding(path, platform=platform, root_id="synthetic-" + str(index))
                  for index, path in enumerate(paths)]
        for ordered in (values, list(reversed(values))):
            with self.assertRaises(EvidenceError) as error:
                validate_bindings(platform, ordered)
            self.assertEqual(error.exception.code, "AUTHORIZATION_PATH_ALIAS")

    def test_explicit_native_roots_preserve_original_spelling(self):
        examples = (
            ("posix", ["/synthetic/évidence one", "/synthetic/other"]),
            ("windows", ["C:\\Synthetic\\évidence one", "D:\\Synthetic\\Other"]),
        )
        for platform, paths in examples:
            values = [binding(path, platform=platform, root_id="synthetic-" + str(index))
                      for index, path in enumerate(paths)]
            before = deepcopy(values)
            self.assertIsNone(validate_bindings(platform, values))
            self.assertEqual(values, before)

    def test_posix_unsafe_or_implicit_spelling_is_rejected(self):
        for path in ("", "/", "//synthetic", "relative", "./relative", "/a/",
                     "/a//b", "/a/./b", "/a/../b", "/a\\b", "/$ROOT/a",
                     "/%ROOT%/a", "/~user/a", "/a\0b", "/a\nb", "/a\x7fb",
                     "/a\x85b", "/a\ud800b", "/a\u202eb", "/a\u2028b", None, 12):
            with self.subTest(path=repr(path)):
                self.assert_invalid(path)

    def test_windows_unsafe_or_implicit_spelling_is_rejected(self):
        for path in ("", "C:\\", "c:\\synthetic", "C:synthetic", "\\synthetic",
                     "C:/synthetic", "C:\\a\\", "C:\\a\\\\b", "C:\\a\\.\\b",
                     "C:\\a\\..\\b", "\\\\server\\share", "\\\\?\\C:\\a",
                     "\\\\.\\C:\\a", "C:\\a:stream", "C:\\bad*name", "C:\\bad?name",
                     "C:\\a<b", "C:\\a>b", 'C:\\a"b', "C:\\a|b", "C:\\a/b",
                     "C:\\a.", "C:\\a ", "C:\\a\t", "C:\\a\udfff", "C:\\%ROOT%",
                     "C:\\$ROOT", "C:\\SYNTH~1", "C:\\a\u200db"):
            with self.subTest(path=repr(path)):
                self.assert_invalid(path, platform="windows")

    def test_windows_reserved_device_names_and_extensions_are_rejected(self):
        for name in ("CON", "prn", "AUX.txt", "NuL.any", "COM1", "lpt9.txt",
                     "COM¹", "lpt².txt", "COM³.txt", "CON .txt", "CONIN$", "CONOUT$"):
            with self.subTest(name=name):
                self.assert_invalid("C:\\synthetic\\" + name, platform="windows")
        validate_bindings("windows", [binding("C:\\synthetic\\COM0.txt", platform="windows")])

    def test_native_length_limits_are_measured_in_native_units(self):
        validate_bindings("posix", [binding("/" + "a" * 255)])
        self.assert_invalid("/" + "a" * 256)
        self.assert_invalid("/" + "é" * 128)
        validate_bindings("windows", [binding("C:\\" + "a" * 255, platform="windows")])
        self.assert_invalid("C:\\" + "a" * 256, platform="windows")
        self.assert_invalid("C:\\" + "😀" * 128, platform="windows")
        validate_bindings("windows", [binding("C:\\" + "a" * 127 + "\\" + "b" * 128,
                                              platform="windows")])
        self.assert_invalid("C:\\" + "a" * 128 + "\\" + "b" * 128, platform="windows")
        self.assert_invalid("/" + "/".join(["a" * 255] * 17))

    def test_duplicate_nested_and_shared_component_aliases_are_rejected(self):
        for paths in (("/synthetic/a", "/synthetic/a"),
                      ("/synthetic/a", "/synthetic/a/b"),
                      ("/synthetic/a/b", "/SYNTHETIC/a/c"),
                      ("/synthetic/é/a", "/synthetic/e\u0301/b"),
                      ("/synthetic/Straße/a", "/synthetic/STRASSE/b")):
            with self.subTest(paths=paths):
                self.assert_alias(paths)
        self.assert_alias(("C:\\synthetic\\one", "C:\\Synthetic\\two"), platform="windows")
        self.assert_alias(("C:\\synthetic\\one", "C:\\synthetic\\one\\two"), platform="windows")

    def test_duplicate_root_ids_platform_mismatch_and_invalid_shapes_are_rejected(self):
        with self.assertRaises(EvidenceError) as error:
            validate_bindings("posix", [binding("/synthetic/a"), binding("/synthetic/b")])
        self.assertEqual(error.exception.code, "AUTHORIZATION_PATH_ALIAS")
        for platform, values in (("posix", [binding("C:\\synthetic", platform="windows")]),
                                 ("windows", [binding("/synthetic")]), ("macos", []),
                                 ("posix", []), ("posix", None), ("posix", [{}]),
                                 ("posix", [None]), (None, []), ([], [])):
            with self.subTest(platform=platform, values=values), self.assertRaises(EvidenceError) as error:
                validate_bindings(platform, values)
            self.assertEqual(error.exception.code, "AUTHORIZATION_PATH_INVALID")


class PortableFileSyntaxTests(unittest.TestCase):
    def assert_error(self, paths, code="AUTHORIZATION_PATH_INVALID"):
        with self.assertRaises(EvidenceError) as error:
            validate_file_paths([file_path(path) for path in paths])
        self.assertEqual(error.exception.code, code)

    def test_portable_ascii_names_and_distinct_roots_preserve_values(self):
        values = [file_path("includes/input_1.sas"), file_path("includes/input-2.sas"),
                  file_path("includes/input_1.sas", root_id="other")]
        before = deepcopy(values)
        self.assertIsNone(validate_file_paths(values))
        self.assertEqual(values, before)

    def test_relative_subset_and_windows_portability_restrictions(self):
        for path in ("", "/a.sas", "../a.sas", "a/./b.sas", "a//b.sas", "a\\b.sas",
                     "a/", "é.sas", "a. ", "a.", "NUL.sas", "AUX/config.json",
                     "dir/COM3.txt", "a:b.sas", "a\0b.sas", "a" * 129, None, 23):
            with self.subTest(path=repr(path)):
                self.assert_error([path])
        self.assert_error(["/".join(["a"] * 33)])

    def test_duplicates_case_aliases_and_directory_conflicts_fail_in_both_orders(self):
        for paths in (("a.sas", "a.sas"), ("a.sas", "A.sas"), ("a", "a/b.sas"),
                      ("includes/a.sas", "INCLUDES/b.sas"),
                      ("a/b.sas", "a/B.sas/c.sas")):
            for order in (paths, tuple(reversed(paths))):
                with self.subTest(paths=order):
                    self.assert_error(order, "AUTHORIZATION_PATH_ALIAS")

    def test_invalid_file_declaration_shapes_are_redacted(self):
        for values in (None, [], [None], [{}], [{"root_id": None, "path": "a.sas"}]):
            with self.subTest(values=values), self.assertRaises(EvidenceError) as error:
                validate_file_paths(values)
            self.assertEqual(error.exception.code, "AUTHORIZATION_PATH_INVALID")

    def test_pure_validation_never_uses_filesystem_process_environment_or_host(self):
        forbidden = AssertionError("CP2 syntax validation attempted external access")
        with ExitStack() as stack:
            for name in ("builtins.open", "io.open", "os.open", "os.stat", "os.lstat",
                         "os.scandir", "os.getcwd", "os.getenv", "os.mkdir", "os.readlink",
                         "pathlib.Path.resolve", "pathlib.Path.absolute", "pathlib.Path.open",
                         "subprocess.run", "subprocess.Popen", "socket.socket"):
                stack.enter_context(patch(name, side_effect=forbidden))
            stack.enter_context(patch.dict(os.environ, {}, clear=True))
            validate_bindings("posix", [binding("/synthetic/intake")])
            validate_bindings("windows", [binding("C:\\Synthetic\\Intake", platform="windows")])
            validate_file_paths([file_path("synthetic/program.sas")])


if __name__ == "__main__":
    unittest.main()
