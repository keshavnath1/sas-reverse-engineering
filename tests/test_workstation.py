"""WS-1 public synthetic fixtures. Native Windows qualification requires its own kit."""

import errno
import hashlib
import json
import os
from pathlib import Path
import selectors
import shlex
import signal
import subprocess
import sys
import sysconfig
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts" / "workstation.sh"
BASH = "/bin/bash"
FLAGS = ["-I", "-B", "-X", "utf8", "-m", "sas_re"]
ALLOWED = ("--help", "--version", "status")
# Regression byte pin for the unprovisioned distribution only.
LAUNCHER_SHA256 = "83a32f061a69af598d62bb249fb98b87878641e6db7c51848146d0957cdddb7a"
APP_MAIN = b"""# Public synthetic installed-package double
import json
import os
import signal
import sys

mode = ''
if mode == 'interrupt':
    print('ready', flush=True)
    signal.pause()
elif mode == 'binary':
    os.write(1, b'out\\0\\xff\\n')
    os.write(2, b'err\\0\\xfe\\n')
    raise SystemExit(37)
elif mode == 'stdin':
    sys.stdout.buffer.write(sys.stdin.buffer.read())
else:
    print(json.dumps([[sys.executable, *sys.orig_argv[1:]], sys.flags.isolated, sys.flags.dont_write_bytecode,
                      sys.flags.utf8_mode, os.environ.get('MSYS2_ARG_CONV_EXCL')]))
"""


def executable(path, data):
    path.write_bytes(data)
    path.chmod(0o700)
    return path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fixture_file_list(root):
    entries = []
    for path in root.rglob("*"):
        name = path.relative_to(root).as_posix()
        if path.is_symlink():
            content = b"link\x00" + os.fsencode(os.readlink(path))
        elif path.is_file():
            content = path.read_bytes()
        elif path.is_dir():
            entries.append((name, "-"))
            continue
        else:
            continue
        entries.append((name, digest(content)))
    return b"".join(name.encode() + b"\x00" + checksum.encode() + b"\n"
                    for name, checksum in sorted(entries))


def fixture_tree_hash(root):
    return digest(fixture_file_list(root))


def run_with_terminals(argv, cwd, env):
    # The fixture writes only a few bytes on each stream, below PTY capacity.
    # Use separate terminals so mixing stderr into stdout remains observable.
    out_master, out_slave = os.openpty()
    err_master, err_slave = os.openpty()
    try:
        try:
            child = subprocess.run(argv, stdout=out_slave, stderr=err_slave,
                                   cwd=cwd, env=env, timeout=10)
        finally:
            os.close(out_slave)
            os.close(err_slave)
        streams = []
        for master in (out_master, err_master):
            data = bytearray()
            while True:
                try:
                    chunk = os.read(master, 4096)
                except OSError as exc:
                    if exc.errno != errno.EIO:
                        raise
                    break
                if not chunk:
                    break
                data.extend(chunk)
            streams.append(bytes(data))
        return (child.returncode, *streams)
    finally:
        os.close(out_master)
        os.close(err_master)


@unittest.skipUnless(os.name == "posix" and Path(BASH).is_file()
                     and (sys.platform, os.uname().machine) in (("darwin", "arm64"), ("linux", "x86_64")),
                     "requires a supported POSIX fixture tuple; Windows needs native qualification")
class WorkstationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.caller = self.root / "caller"
        self.caller.mkdir()
        self.traps = self.root / "shadow-bin"
        self.traps.mkdir()
        self.log = self.root / "trapped"
        trap = b'#!/bin/bash\nprintf "%s\\n" "$0" >> "$WS_TRAP_LOG"\nexit 101\n'
        for name in ("python", "python3", "python3.12", "python.exe", "py", "py.exe",
                     "git", "curl", "wget", "pip", "pip3", "conda", "docker", "wsl",
                     "aws", "az", "openai"):
            executable(self.traps / name, trap)
        self.env = {"PATH": str(self.traps), "HOME": str(self.caller),
                    "WS_TRAP_LOG": str(self.log), "LC_ALL": "C",
                    "HTTP_PROXY": "http://127.0.0.1:1", "HTTPS_PROXY": "http://127.0.0.1:1"}

    def runtime_fixture(self, mode=""):
        # A real CPython executes the verifier and the test-only package. No
        # environment installation, site activation, release wheel or
        # operational approval record is used.
        self.runtime = self.root / "München's $(printf injected) [*]; kit"
        self.python = self.runtime / "bin" / "python"
        self.python.parent.mkdir(parents=True)
        base_exe = Path(sys._base_executable).resolve()
        self.python.symlink_to(base_exe)
        self.cfg = self.runtime / "pyvenv.cfg"
        patch = ".".join(map(str, sys.version_info[:3]))
        self.cfg.write_text(f"home = {base_exe.parent}\ninclude-system-site-packages = false\n"
                            f"version = {patch}\nexecutable = {base_exe}\n")
        self.site = self.runtime / "lib/python3.12/site-packages"
        self.package = self.site / "sas_re"
        files = ("__init__.py", "__main__.py", "cli.py", "platform_io.py", "data/baseline.json",
                 "contracts/v1/evidence.schema.json", "contracts/v2/evidence.schema.json",
                 "contracts/authorization/v1/local-authorization.schema.json")
        for name in files:
            path = self.package / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"{}\n" if path.suffix == ".json" else b"# Synthetic fixture\n")
        (self.package / "__main__.py").write_bytes(APP_MAIN.replace(
            b"mode = ''", b"mode = " + repr(mode).encode()))
        dist = self.site / "sas_reverse_engineering-0.3.0.dist-info"
        dist.mkdir()
        (dist / "METADATA").write_bytes(b"Metadata-Version: 2.1\nName: sas-reverse-engineering\n"
                                       b"Version: 0.3.0\n")
        (dist / "WHEEL").write_bytes(b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\n"
                                    b"Tag: py3-none-any\n")
        self.fields = ["WS1-APPROVAL-1", sys.platform, str(self.python), str(self.python),
                       str(Path(sys.base_prefix).resolve()), str(base_exe), patch,
                       sysconfig.get_platform(), digest(base_exe.read_bytes()),
                       digest(self.cfg.read_bytes()), "0.3.0", fixture_tree_hash(self.runtime)]
        self.record = self.root / "fixture approval.txt"
        self.bound = self.root / "synthetic launcher.sh"
        self.provision()

    def provision(self, raw=None, listing=None):
        # Replace two literal release slots in a disposable private fixture.
        # The distributed launcher accepts neither slot from the environment.
        record = ("\n".join(self.fields) + "\n").encode() if raw is None else raw
        self.record.write_bytes(record)
        if listing is None:
            listing = fixture_file_list(self.runtime)
        Path(str(self.record) + ".files").write_bytes(listing)
        code = LAUNCHER.read_text(encoding="utf-8")
        for name, value in (("approval_pin", digest(record)), ("approval_file", str(self.record))):
            slot = f"readonly {name}=''"
            self.assertEqual(code.count(slot), 1)
            code = code.replace(slot, f"readonly {name}={shlex.quote(value)}")
        self.bound.write_text(code, encoding="utf-8")

    def invoke(self, *args, script=LAUNCHER, **settings):
        return subprocess.run([BASH, str(script), *args], cwd=self.caller,
                              env={**self.env, **settings}, capture_output=True, timeout=10)

    def assert_usage(self, result):
        self.assertEqual(result.returncode, 2, result)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"usage", result.stderr.lower())
        self.assertNotIn(b"bootstrap", result.stderr.lower())

    def assert_bootstrap_blocked(self, result):
        self.assertEqual(result.returncode, 2, result)
        self.assertEqual(result.stdout, b"")
        self.assertTrue(result.stderr.startswith(b"WS1 BLOCKED:"), result.stderr)

    def assert_no_trap(self):
        self.assertFalse(self.log.exists(), self.log.read_bytes() if self.log.exists() else b"")

    def test_w01_all_modes_match_direct_isolated_child_bytes(self):
        self.runtime_fixture()
        for verb in ALLOWED:
            direct_argv = [str(self.python), *FLAGS, verb]
            direct = subprocess.run(direct_argv, env=self.env, cwd=self.caller,
                                    capture_output=True, timeout=10)
            self.assertEqual(direct.returncode, 0, direct.stderr)
            self.assertEqual(json.loads(direct.stdout), [direct_argv, 1, 1, 1, None])
            for selection in ({}, {"SAS_RE_PYTHON": str(self.python)}):
                with self.subTest(verb=verb, explicit=bool(selection)):
                    child = self.invoke(verb, script=self.bound, **selection)
                    self.assertEqual((child.returncode, child.stdout, child.stderr),
                                     (0, direct.stdout, direct.stderr))
        self.assertEqual(self.fields[-1], fixture_tree_hash(self.runtime))
        self.assertEqual(list(self.caller.iterdir()), [])
        self.assert_no_trap()

    def test_w02_wrong_or_ambiguous_explicit_selection_never_falls_back(self):
        self.runtime_fixture()
        for value in ("", "python", "./python", str(self.python) + " -I",
                      str(self.traps / "python"), str(self.root / "missing"),
                      "C:/Users/user/AppData/Local/Microsoft/WindowsApps/python.exe"):
            with self.subTest(value=value):
                self.assert_bootstrap_blocked(self.invoke("status", script=self.bound,
                                                         SAS_RE_PYTHON=value))
        self.python.unlink()
        self.assert_bootstrap_blocked(self.invoke("status", script=self.bound))
        self.assert_no_trap()

    def test_w02_pinned_record_cannot_change_after_delivery(self):
        self.runtime_fixture()
        self.record.write_bytes(self.record.read_bytes().replace(b"0.3.0", b"9.9.9"))
        self.assert_bootstrap_blocked(self.invoke("status", script=self.bound))
        self.record.unlink()
        self.assert_bootstrap_blocked(self.invoke("status", script=self.bound))

    def test_w02_replaced_executable_never_runs_even_as_a_probe(self):
        self.runtime_fixture()
        self.python.unlink()
        marker = self.root / "unapproved interpreter executed"
        decoy = f"#!/bin/bash\nprintf '%s' invoked > {shlex.quote(str(marker))}\nexit 2\n"
        executable(self.python, decoy.encode())
        self.assert_bootstrap_blocked(self.invoke("status", script=self.bound))
        self.assertFalse(marker.exists())

    def test_w02_bootstrap_links_never_redirect_hashing_to_outside_content(self):
        self.runtime_fixture()
        outside = self.caller / "public synthetic decoy"
        for path in (self.cfg, self.record, Path(str(self.record) + ".files")):
            with self.subTest(path=path.name):
                os.link(path, outside)
                self.check_access_witness(outside, outside.read_bytes)
                self.assert_bootstrap_blocked(self.invoke("status", script=self.bound))
                self.assertEqual(outside.stat().st_atime_ns, 1_000_000_000)
                outside.unlink()
        self.python.unlink()
        executable(outside, b"#!/bin/bash\nexit 2\n")
        self.python.symlink_to(outside)
        self.check_access_witness(outside, outside.read_bytes)
        self.assert_bootstrap_blocked(self.invoke("status", script=self.bound))
        self.assertEqual(outside.stat().st_atime_ns, 1_000_000_000)

    def test_w02_missing_or_tampered_approved_file_list_blocks(self):
        self.runtime_fixture()
        listing = Path(str(self.record) + ".files")
        listing.write_bytes(listing.read_bytes() + b"unapproved\x00-\n")
        self.assert_bootstrap_blocked(self.invoke("status", script=self.bound))
        listing.unlink()
        self.assert_bootstrap_blocked(self.invoke("status", script=self.bound))

    def test_w02_even_pinned_unusable_file_lists_block(self):
        self.runtime_fixture()
        valid = fixture_file_list(self.runtime)
        first = valid.splitlines(keepends=True)[0]
        for raw in (b"", valid[:-1], first + valid, b"../escape\0-\n" + valid,
                    b"/absolute\0-\n" + valid, b"bad\0not-a-digest\n" + valid):
            with self.subTest(prefix=raw[:12], length=len(raw)):
                self.fields[-1] = digest(raw)
                self.provision(listing=raw)
                self.assert_bootstrap_blocked(self.invoke("status", script=self.bound))

    def test_w02_unlisted_directory_is_never_opened(self):
        self.runtime_fixture()
        unknown = self.runtime / "unexpected directory"
        unknown.mkdir()
        os.mkfifo(unknown / "do not read")
        self.check_access_witness(unknown, lambda: list(unknown.iterdir()))
        self.assert_bootstrap_blocked(self.invoke("status", script=self.bound))
        self.assertEqual(unknown.stat().st_atime_ns, 1_000_000_000)

    def test_w02_hardlinked_approved_name_is_denied_before_content_read(self):
        self.runtime_fixture()
        resource = self.package / "data/baseline.json"
        outside = self.caller / "public synthetic bytes"
        os.link(resource, outside)
        self.check_access_witness(outside, outside.read_bytes)
        self.assert_bootstrap_blocked(self.invoke("status", script=self.bound))
        self.assertEqual(outside.stat().st_atime_ns, 1_000_000_000)

    def check_access_witness(self, path, read):
        # Calibrate an on-filesystem read witness before asserting no read.
        times = (1_000_000_000, 2_000_000_000)
        os.utime(path, ns=times)
        read()
        if path.stat().st_atime_ns == times[0]:
            self.skipTest("filesystem supplies no atime witness for this operation")
        os.utime(path, ns=times)

    def test_w02_even_pinned_malformed_records_block(self):
        self.runtime_fixture()
        raw = self.record.read_bytes()
        malformed = [b"", raw[:-1], raw + b"extra\n", raw + b"\n",
                     raw.replace(b"\n", b"\r\n"), raw.replace(b"WS1-", b"WS\x001-"),
                     raw.replace(b"WS1-APPROVAL-1", b"WS1-APPROVAL-2"),
                     raw.replace(self.fields[8].encode(), b"bad digest"),
                     raw.replace(self.fields[8].encode(), b"A" * 64),
                     raw.replace(self.fields[2].encode(), b"relative", 1)]
        for data in malformed:
            with self.subTest(prefix=data[:32], size=len(data)):
                self.provision(raw=data)
                self.assert_bootstrap_blocked(self.invoke("status", script=self.bound))
        self.assert_no_trap()

    def test_w02_invalid_installation_tuple_and_digests_block(self):
        self.runtime_fixture()
        original = self.fields.copy()
        for index, value in ((1, "win32"), (3, str(self.traps / "python")),
                             (4, str(self.root / "wrong-base")), (5, str(self.traps / "python")),
                             (6, "3.12.9999"), (7, "wrong-architecture"),
                             (8, "a" * 64), (9, "a" * 64), (10, "9.9"), (11, "a" * 64)):
            with self.subTest(field=index):
                self.fields = original.copy()
                self.fields[index] = value
                self.provision()
                self.assert_bootstrap_blocked(self.invoke("status", script=self.bound))
        self.assert_no_trap()

    def test_w02_same_version_altered_resource_and_missing_resource_block(self):
        self.runtime_fixture()
        resource = self.package / "data/baseline.json"
        resource.write_bytes(b'{"synthetic":true}\n')
        self.assert_bootstrap_blocked(self.invoke("status", script=self.bound))
        resource.unlink()
        # A tree digest that agrees with an incomplete fixture is insufficient.
        self.fields[-1] = fixture_tree_hash(self.runtime)
        self.provision()
        self.assert_bootstrap_blocked(self.invoke("status", script=self.bound))

    def test_w02_preflight_rejects_startup_hook_before_execution(self):
        self.runtime_fixture()
        hook = self.site / "unexpected.pth"
        marker = self.root / "startup-marker"
        hook.write_text(f"import pathlib; pathlib.Path({str(marker)!r}).touch()\n")
        control = subprocess.run([str(self.python), "-I", "-B", "-c", "pass"],
                                 env=self.env, cwd=self.caller, capture_output=True)
        self.assertEqual(control.returncode, 0, control.stderr)
        self.assertTrue(marker.is_file())
        marker.unlink()
        self.fields[-1] = fixture_tree_hash(self.runtime)
        self.provision()
        self.assert_bootstrap_blocked(self.invoke("status", script=self.bound))
        self.assertFalse(marker.exists())
        self.assertEqual(list(self.caller.iterdir()), [])

    def test_w02_pinned_resource_link_cannot_redirect_to_caller(self):
        self.runtime_fixture()
        outside = self.caller / "unreadable fifo"
        os.mkfifo(outside)
        resource = self.package / "data/baseline.json"
        resource.unlink()
        resource.symlink_to(outside)
        self.fields[-1] = fixture_tree_hash(self.runtime)
        self.provision()
        self.assert_bootstrap_blocked(self.invoke("status", script=self.bound))
        self.assertEqual(list(self.caller.iterdir()), [outside])

    def test_w02_pinned_editable_distribution_is_refused(self):
        self.runtime_fixture()
        dist = self.site / "sas_reverse_engineering-0.3.0.dist-info"
        (dist / "direct_url.json").write_text(json.dumps(
            {"url": "file:///synthetic/checkout", "dir_info": {"editable": True}}))
        self.fields[-1] = fixture_tree_hash(self.runtime)
        self.provision()
        self.assert_bootstrap_blocked(self.invoke("status", script=self.bound))

    def test_w02_wheel_origin_must_identify_valid_local_archive_metadata(self):
        self.runtime_fixture()
        origin = self.site / "sas_reverse_engineering-0.3.0.dist-info" / "direct_url.json"
        local = "file:///supplied/sas_reverse_engineering-0.3.0-py3-none-any.whl"
        valid = {"url": local, "archive_info": {"hashes": {"sha256": "1" * 64}}}
        origin.write_text(json.dumps(valid))
        self.fields[-1] = fixture_tree_hash(self.runtime)
        self.provision()
        child = self.invoke("status", script=self.bound)
        self.assertEqual(child.returncode, 0, child.stderr)
        for raw in (json.dumps({**valid, "url": local.replace("file:///", "https://example.invalid/")}),
                    json.dumps(valid).replace("1" * 64, "bad"),
                    json.dumps(valid).replace('"url":', '"url":"wrong","url":')):
            with self.subTest(raw=raw):
                origin.write_text(raw)
                self.fields[-1] = fixture_tree_hash(self.runtime)
                self.provision()
                self.assert_bootstrap_blocked(self.invoke("status", script=self.bound))

    def test_w02_pinned_package_metadata_must_describe_one_matching_wheel(self):
        self.runtime_fixture()
        dist = self.site / "sas_reverse_engineering-0.3.0.dist-info"
        wheel = dist / "WHEEL"
        metadata = dist / "METADATA"
        good_wheel = wheel.read_bytes()
        good_metadata = metadata.read_bytes()
        changes = [(wheel, good_wheel.replace(b"py3-none-any", b"cp311-cp311-win32")),
                   (metadata, good_metadata.replace(b"sas-reverse-engineering", b"other")),
                   (metadata, good_metadata + b"Version: 0.3.0\n")]
        for path, damaged in changes:
            with self.subTest(path=path.name, damaged=damaged):
                path.write_bytes(damaged)
                self.fields[-1] = fixture_tree_hash(self.runtime)
                self.provision()
                self.assert_bootstrap_blocked(self.invoke("status", script=self.bound))
                wheel.write_bytes(good_wheel)
                metadata.write_bytes(good_metadata)

    def test_w02_package_version_cannot_redirect_wheel_read_outside_installation(self):
        self.runtime_fixture()
        dist = self.site / "sas_reverse_engineering-0.3.0.dist-info"
        outside = self.caller / "outside.dist-info"
        outside.mkdir()
        escape = os.path.relpath(self.caller / "outside", dist)
        bad_version = "0.3.0.dist-info/" + escape
        metadata = dist / "METADATA"
        metadata.write_bytes(metadata.read_bytes().replace(b"Version: 0.3.0",
                                                           b"Version: " + bad_version.encode()))
        (outside / "METADATA").write_bytes(metadata.read_bytes())
        wheel = outside / "WHEEL"
        wheel.write_bytes((dist / "WHEEL").read_bytes())
        self.fields[10] = bad_version
        self.fields[-1] = fixture_tree_hash(self.runtime)
        self.provision()
        self.check_access_witness(wheel, wheel.read_bytes)
        self.assert_bootstrap_blocked(self.invoke("status", script=self.bound))
        self.assertEqual(wheel.stat().st_atime_ns, 1_000_000_000)

    def test_w03_native_child_conversion_scope_simulated_on_posix(self):
        # Exercise the two child command lines, with a POSIX double for the
        # Windows executable, machine triple, drive mount and hashing tool.
        # This cannot qualify MSYS argument conversion or Windows execution.
        self.runtime_fixture()
        self.python = self.runtime / "Scripts/python.exe"
        self.python.parent.mkdir()
        probe_log = self.root / "probe argv"
        app_log = self.root / "app argv"
        hasher_log = self.root / "hasher env"
        double = ("#!/bin/bash\n"
                  f"if [[ $3 == -S ]]; then log={shlex.quote(str(probe_log))}; "
                  f"else log={shlex.quote(str(app_log))}; fi\n"
                  'printf "%s\\0" "${MSYS2_ARG_CONV_EXCL-unset}" "$@" >> "$log"\n')
        executable(self.python, double.encode())
        native = "C:/Synthetic user's München [ok] $kit/Scripts/python.exe"
        self.fields[1:6] = ["win32", str(self.python), native,
                            "C:/Native Python", "C:/Native Python/python.exe"]
        self.fields[7:9] = ["win-amd64", digest(self.python.read_bytes())]
        self.fields[-1] = fixture_tree_hash(self.runtime)
        self.provision()
        hasher = self.root / "hash tool"
        backend = "/usr/bin/shasum -a 256" if sys.platform == "darwin" else "/usr/bin/sha256sum"
        executable(hasher, ("#!/bin/bash\n" + 'printf "%s\\n" "${MSYS2_ARG_CONV_EXCL-unset}" >> '
                            + shlex.quote(str(hasher_log)) + "\nexec " + backend + "\n").encode())
        code = self.bound.read_text()
        for old, new in (("${BASH_VERSINFO[5]}", "x86_64-pc-msys"),
                         ("win32:/[a-zA-Z]/*/Scripts/python.exe", "win32:/*/Scripts/python.exe"),
                         ("(/usr/bin/sha256sum)", f"({shlex.quote(str(hasher))})")):
            self.assertIn(old, code)
            code = code.replace(old, new)
        if sys.platform == "darwin":
            code = code.replace("stat_fmt=(-c %s)", "stat_fmt=(-f %z)")
            code = code.replace("link_fmt=(-c %h)", "link_fmt=(-f %l)")
        self.bound.write_text(code)
        child = self.invoke("status", script=self.bound, MSYS2_ARG_CONV_EXCL="caller",
                            SAS_RE_PYTHON=str(self.python))
        self.assertEqual((child.returncode, child.stdout, child.stderr), (0, b"", b""))
        self.assertEqual(app_log.read_bytes().split(b"\0"),
                         [s.encode() for s in ["*", *FLAGS, "status", ""]])
        probe = probe_log.read_bytes().split(b"\0")
        self.assertEqual(probe[:7], [b"*", b"-I", b"-B", b"-S", b"-X", b"utf8", b"-c"])
        expected_tail = self.fields[3:8] + self.fields[10:12] + ["win32", ""]
        self.assertEqual(probe[8:], [s.encode() for s in expected_tail])
        self.assertEqual(set(hasher_log.read_text().splitlines()), {"unset"})

    def test_w04_calibrated_shadow_commands_packages_and_pythonpath(self):
        self.runtime_fixture()
        pythonpath = self.root / "other pythonpath"
        for directory in (self.caller, pythonpath):
            shadow = directory / "sas_re"
            shadow.mkdir(parents=True)
            (shadow / "__init__.py").write_text("raise SystemExit(93)\n")
        for cwd in (self.caller, self.root):
            decoy = subprocess.run([str(self.python), "-B", "-m", "sas_re", "status"], cwd=cwd,
                                   env={**self.env, "PYTHONPATH": str(pythonpath)})
            self.assertEqual(decoy.returncode, 93)
        result = subprocess.run(["git"], env=self.env, cwd=self.caller)
        self.assertEqual(result.returncode, 101)
        self.assertEqual(self.log.read_text().strip(), str(self.traps / "git"))
        self.log.unlink()
        child = self.invoke("status", script=self.bound, PYTHONPATH=str(pythonpath),
                            PYTHONHOME=str(self.traps), PYTHONSTARTUP=str(self.log))
        self.assertEqual(child.returncode, 0, child.stderr)
        self.assertEqual(json.loads(child.stdout)[0], [str(self.python), *FLAGS, "status"])
        self.assertEqual(child.stderr, b"")
        self.assertEqual(list(self.caller.iterdir()), [self.caller / "sas_re"])
        self.assert_no_trap()

    def test_w05_binary_streams_distinct_exit_and_terminal_delivery(self):
        self.runtime_fixture("binary")
        child = self.invoke("status", script=self.bound)
        self.assertEqual((child.returncode, child.stdout, child.stderr),
                         (37, b"out\0\xff\n", b"err\0\xfe\n"))
        direct = run_with_terminals([str(self.python), *FLAGS, "status"], self.caller, self.env)
        wrapped = run_with_terminals([BASH, str(self.bound), "status"], self.caller,
                                     self.env)
        self.assertEqual(wrapped, direct)
        self.assertEqual(list(self.caller.iterdir()), [])

    def test_w05_external_signal_reaches_delegated_child_without_retry(self):
        self.runtime_fixture("interrupt")
        cmd = [BASH, str(self.bound), "status"]
        with subprocess.Popen(cmd, cwd=self.caller, start_new_session=True, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, env=self.env) as proc:
            try:
                with selectors.DefaultSelector() as selector:
                    selector.register(proc.stdout, selectors.EVENT_READ)
                    self.assertTrue(selector.select(10), "child never became ready")
                    self.assertEqual(proc.stdout.readline(), b"ready\n")
                proc.send_signal(signal.SIGTERM)
                self.assertEqual(proc.communicate(timeout=5), (b"", b""))
                self.assertEqual(proc.returncode, -signal.SIGTERM)
            finally:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        self.assertEqual(fixture_tree_hash(self.runtime), self.fields[-1])
        self.assertEqual(list(self.caller.iterdir()), [])

    def test_w05_external_delivery_byte_check_precedes_bash(self):
        data = LAUNCHER.read_bytes()
        self.assertEqual(data.decode("utf-8").encode("utf-8"), data)
        self.assertFalse(data.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\r", data)
        self.assertEqual(digest(data), LAUNCHER_SHA256)
        candidate = self.root / "delivered.sh"
        marker = self.caller / "executed"
        def checked_handoff(content):
            candidate.write_bytes(content)
            if digest(candidate.read_bytes()) == LAUNCHER_SHA256:
                return self.invoke("status", script=candidate)
            return None

        self.assert_bootstrap_blocked(checked_handoff(data))
        tampered = b"printf '%s' tampered > " + shlex.quote(str(marker)).encode() + b"\n" + data
        for damaged in (data.replace(b"\n", b"\r\n"), b"\xef\xbb\xbf" + data, tampered):
            with self.subTest(prefix=damaged[:12]):
                self.assertIsNone(checked_handoff(damaged))
                self.assertFalse(marker.exists())

    def test_w05_approval_verification_preserves_final_child_stdin(self):
        self.runtime_fixture("stdin")
        supplied = b"public\x00fixture\r\n\xff"
        child = subprocess.run([BASH, str(self.bound), "status"], cwd=self.caller, env=self.env,
                               input=supplied, capture_output=True, timeout=10)
        self.assertEqual((child.returncode, child.stdout, child.stderr), (0, supplied, b""))

    def test_w03_reject_entire_argv_before_discovery_or_expansion(self):
        decoy = self.traps / "python"
        before = list(self.caller.iterdir())
        rejected = (
            (), ("",), ("--",), ("-h",), ("--vers",), ("--HELP",), ("STATUS",),
            (" status",), ("status ",), ("--help=status",), ("*",),
            ("$(printf executed > marker)",), ("`printf executed > marker`",),
            ("status; printf executed > marker",), ("--help\nstatus",),
            ("status", ""), ("--help", "status"), ("--version", "--help"),
            ("status", str(self.caller)), ("--help", "$(printf executed > marker)"),
        )
        for args in rejected:
            with self.subTest(args=args):
                self.assert_usage(self.invoke(*args, SAS_RE_PYTHON=str(decoy)))
        self.assert_no_trap()
        self.assertEqual(list(self.caller.iterdir()), before)

    def test_w03_reject_extra_arg_before_reading_real_fixture_approval(self):
        self.runtime_fixture()
        self.check_access_witness(self.record, self.record.read_bytes)
        for args in ((), ("status", "/synthetic"), ("--version", "*")):
            with self.subTest(args=args):
                self.assert_usage(self.invoke(*args, script=self.bound,
                                              SAS_RE_PYTHON=str(self.python)))
        self.assertEqual(self.record.stat().st_atime_ns, 1_000_000_000)
        self.assertEqual(list(self.caller.iterdir()), [])

    def test_w02_explicit_candidate_and_caller_metadata_cannot_grant_trust(self):
        # Even if a proposed runtime is executable and the caller supplies a
        # plausible manifest, a released launcher needs independent approval.
        decoy = self.traps / "python3.12"
        manifest = self.caller / "release.json"
        manifest.write_text(json.dumps({"interpreter": str(decoy),
                                        "sha256": hashlib.sha256(decoy.read_bytes()).hexdigest()}))
        for command in ALLOWED:
            with self.subTest(command=command):
                self.assert_bootstrap_blocked(self.invoke(command, SAS_RE_PYTHON=str(decoy),
                                              SAS_RE_MANIFEST=str(manifest)))
        self.assert_no_trap()
        self.assertEqual(list(self.caller.iterdir()), [manifest])

    def test_w02_missing_selection_does_not_search_path(self):
        self.assert_bootstrap_blocked(self.invoke("status"))
        self.assert_no_trap()
        self.assertEqual(list(self.caller.iterdir()), [])

    def test_w06_deny_evidence_placeholders_remote_and_future_modes(self):
        # An actual blocking reader on this synthetic scope would hang until
        # the subprocess timeout. The output destination must stay absent.
        scope = self.caller / "synthetic scope"
        os.mkfifo(scope)
        store = self.caller / "uncreated store"
        args = ["--scope", str(scope), "--store", str(store), "--run", "R", "--attempt", "A"]
        extra = {
            "discover": [], "seal-source": ["--record", str(scope)],
            "verify-source": ["--verification-attempt", "V"],
            "reconstruct-source": ["--profile-file", "public:p", "--inventory-attempt", "P"],
            "check-reconstruction": ["--profile-file", "public:p", "--verification-attempt", "V"],
        }
        denied = [(command, *args, *tail) for command, tail in extra.items()]
        denied.extend((command,) for command in (
            *extra, "analyze-parallelism", "draft-requirements", "propose-adrs", "verify-adrs",
            "package-handoff", "eval", "setup", "check-config", "run", "report",
        ))
        denied.extend([("check-baseline", "--remote"), ("check-baseline", "--checkout", str(scope))])
        for command in denied:
            with self.subTest(command=command):
                self.assert_usage(self.invoke(*command, SAS_RE_PYTHON=str(self.traps / "python")))
        self.assert_no_trap()
        self.assertTrue(scope.is_fifo())
        self.assertEqual(list(self.caller.iterdir()), [scope])
