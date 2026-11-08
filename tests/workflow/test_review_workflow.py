"""Offline review workflow uses live stages and reproduces accepted synthetic package bytes."""

from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import unquote, urlsplit
import uuid

from mvp2_expectations import SOURCES
from mvp3_cases import CASES


from support.paths import REPOSITORY_ROOT as ROOT

SCRIPT = ROOT / "scripts/review_workflow.py"
PREVIEWS = {
    "PRD.md",
    "MODULES.md",
    "ARCHITECTURE.md",
    "EVIDENCE.md",
    "ADR_NATIVE.md",
    "ADR_SPARK.md",
}
FILES = PREVIEWS | {"TIEOUT.json", "DECISION_REVIEW.md", "README.md", "MANIFEST.json"}
STATUS = {
    "artifact_authority": "DRAFT",
    "semantic_verification": "UNVERIFIABLE",
    "semantic_acceptance": "BLOCKED",
    "benchmark_execution": "NOT_RUN",
}
TIEOUT_SHA = "aee7cbd480b1f6794888616af9c55e8896ecb13fa3dc1585d1b012f0a8508600"
GRAPH_SHA = "19f41dea50825469a89d8fc545fee1d87f09af946d130d62de8f946d90b78017"
LINK = re.compile(r"\[([^\]\n]+)\]\(([^)\n]+)\)")
STAGES = {
    "semantic.py:reconstruct",
    "_dependency_diagnostics.py:diagnose",
    "_draft_preview.py:generate_preview",
    "mvp3_tieout.py:build_report",
    "_decision_review.py:render_review",
}

# Observe actual calls so substituting a golden-file copy cannot pass a reproducibility check.
OFFLINE = """
import os, runpy, sys
names = {'reconstruct', 'diagnose', 'generate_preview', 'build_report', 'render_review'}
seen = set()
def observe(frame, event, arg):
    if event == 'call' and frame.f_code.co_name in names:
        seen.add(os.path.basename(frame.f_code.co_filename) + ':' + frame.f_code.co_name)
def deny(event, args):
    if event.startswith(('socket.', 'subprocess.', 'os.system', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork')):
        raise AssertionError(event)
sys.addaudithook(deny)
sys.setprofile(observe)
sys.argv = sys.argv[1:]
try:
    runpy.run_path(sys.argv[0], run_name='__main__')
finally:
    sys.setprofile(None)
    print('Observed stages: ' + ','.join(sorted(seen)), file=sys.stderr)
"""


def call(destination, *, script=SCRIPT, guard=None, extra=()):
    args = [sys.executable, "-IB"]
    if guard:
        args += ["-c", guard]
    with tempfile.TemporaryDirectory() as cwd:
        return subprocess.run(
            [*args, str(script), "--destination", str(destination), *extra],
            cwd=cwd,
            env={**os.environ, "PATH": ""},
            capture_output=True,
            timeout=60,
        )


def free_destination():
    dest = Path("/tmp") / ("sas-re-review-" + uuid.uuid4().hex)
    if os.path.lexists(dest):
        raise AssertionError("Synthetic destination already exists")
    return dest


def remove_destination(path):
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


@unittest.skipUnless(
    sys.platform in ("darwin", "linux"), "Existing synthetic source I/O needs qualified POSIX"
)
class ReviewWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.destination = free_destination()
        cls.addClassCleanup(remove_destination, cls.destination)
        run = call(cls.destination)
        if run.returncode:
            raise AssertionError(run.stderr.decode())
        cls.stdout = run.stdout
        cls.files = {p.name: p.read_bytes() for p in cls.destination.iterdir()}

    def test_repetition_uses_live_stages_offline_and_matches_sample(self):
        dest = free_destination()
        self.addCleanup(remove_destination, dest)
        second = call(dest, guard=OFFLINE)
        self.assertEqual(second.returncode, 0, second.stderr)
        observed = re.search(rb"Observed stages: (.*)", second.stderr)
        self.assertIsNotNone(observed, second.stderr)
        self.assertTrue(STAGES <= set(observed[1].decode().split(",")), second.stderr)
        self.assertEqual({p.name: p.read_bytes() for p in dest.iterdir()}, self.files)
        self.assertEqual(set(self.files), FILES)
        sample = ROOT / "tests/fixtures/source-reconstruction/offline-review-package"
        self.assertEqual({p.name: p.read_bytes() for p in sample.iterdir()}, self.files)

    def test_original_preview_bytes_tieout_and_review_content(self):
        for name in PREVIEWS:
            with self.subTest(name=name):
                self.assertEqual(
                    self.files[name],
                    (
                        ROOT
                        / "tests/fixtures/source-reconstruction/dependency-aware-preview"
                        / name
                    ).read_bytes(),
                )
        raw = self.files["TIEOUT.json"]
        self.assertEqual(hashlib.sha256(raw).hexdigest(), TIEOUT_SHA)
        tieout = json.loads(raw)
        self.assertEqual(tieout["reference"]["original_mvp2_graph_sha256"], GRAPH_SHA)
        self.assertEqual(
            Counter(c["verdict"] for c in tieout["cases"]),
            Counter({"PASS": 7, "FAIL": 8, "UNVERIFIABLE": 2}),
        )
        self.assertTrue(
            all(
                c["matches_specification"] and c["full_workflow_gate"] == "BLOCKED"
                for c in tieout["cases"]
            )
        )
        self.assertEqual(
            tieout["unresolved_include"],
            {"operation": "O4", "target": "postcheck.sas", "verdict": "UNVERIFIABLE"},
        )
        # All decisions, evidence labels and prose survive relocation; only link destinations may change.
        historical = (
            ROOT / "tests/fixtures/source-reconstruction/decision-review/DECISION_REVIEW.md"
        ).read_text()
        localized = self.files["DECISION_REVIEW.md"].decode()
        self.assertEqual(LINK.sub(r"[\1](dest)", historical), LINK.sub(r"[\1](dest)", localized))

    def test_manifest_subject_bytes_and_authority(self):
        manifest = json.loads(self.files["MANIFEST.json"])
        self.assertEqual(manifest["subject"]["graph_sha256"], GRAPH_SHA)
        source_hashes = {name: hashlib.sha256(raw).hexdigest() for name, raw in SOURCES.items()}
        self.assertEqual(manifest["subject"]["source_sha256"], source_hashes)
        reference = json.loads(self.files["TIEOUT.json"])["reference"]
        self.assertEqual(
            manifest["subject"]["case_table_sha256"], reference["specification_sha256"]
        )
        self.assertEqual(
            manifest["subject"]["fixture_sha256"], reference["original_fixture_sha256"]
        )
        self.assertEqual(
            tuple(
                manifest[k]
                for k in (
                    "source_consistency",
                    "reconstruction_status",
                    "stage_gate",
                    "full_workflow_gate",
                )
            ),
            ("PASSED", "PARTIAL", "BLOCKED", "BLOCKED"),
        )
        for key, value in {
            "workspace_id": "mvp2-public-workspace",
            "run_id": "ordered-measurements",
            "attempt_id": "preview-2",
            "source_fingerprint": "7517a3f1d064af2c15eb4bb0f3671659b4ea9b5acb9c39125dd9fb973a0a5d46",
        }.items():
            self.assertEqual(manifest["subject"][key], value)
        self.assertEqual(
            manifest["tieout_counts"], {"PASS": 7, "deliberate FAIL": 8, "UNVERIFIABLE": 2}
        )
        self.assertEqual(set(manifest["files"]), FILES - {"MANIFEST.json"})
        self.assertEqual(manifest["manifest_file"], "MANIFEST.json")
        for name, entry in manifest["files"].items():
            payload = self.files[name]
            self.assertEqual(
                (entry["bytes"], entry["sha256"]),
                (len(payload), hashlib.sha256(payload).hexdigest()),
            )
        receipt = json.loads(self.stdout)
        self.assertEqual(
            receipt["manifest_sha256"], hashlib.sha256(self.files["MANIFEST.json"]).hexdigest()
        )
        self.assertEqual(receipt["open"], str((self.destination / "README.md").resolve()))
        self.assertEqual({field: receipt[field] for field in STATUS}, STATUS)
        for name, payload in self.files.items():
            for field, value in STATUS.items():
                with self.subTest(file=name, field=field):
                    if name.endswith(".json"):
                        self.assertEqual(json.loads(payload)[field], value)
                    else:
                        self.assertIn(f"{field}: {value}", payload.decode())

    def test_links_resolve_to_self_contained_sources_cases_and_results(self):
        docs = {
            name: payload.decode() for name, payload in self.files.items() if name.endswith(".md")
        }
        readme = docs["README.md"]
        for source in SOURCES.values():
            self.assertIn(source.decode(), readme)
        navigation = {urlsplit(dest).path for _, dest in LINK.findall(readme)}
        self.assertTrue(PREVIEWS | {"TIEOUT.json", "DECISION_REVIEW.md"} <= navigation)
        self.assertIn("postcheck.sas", readme)
        anchors = {
            name: {
                re.sub(r"[^\w-]", "", h.lower().replace(" ", "-"))
                for h in re.findall(r"(?m)^#{1,6} (.+)$", contents)
            }
            for name, contents in docs.items()
        }
        for owner, contents in docs.items():
            for _, link in LINK.findall(contents):
                dest = urlsplit(link)
                self.assertFalse(dest.scheme or dest.netloc or dest.query, link)
                path = unquote(dest.path) or owner
                self.assertIn(path, FILES, link)
                if dest.fragment:
                    self.assertIn(unquote(dest.fragment), anchors.get(path, set()), link)

        # Check that localization points to the *right* local witness, not just a valid heading.
        historical = LINK.findall(
            (
                ROOT / "tests/fixtures/source-reconstruction/decision-review/DECISION_REVIEW.md"
            ).read_text()
        )
        actual = LINK.findall(docs["DECISION_REVIEW.md"])
        self.assertEqual(len(actual), len(historical))
        for (label, old), (_, new) in zip(historical, actual):
            if old.startswith("../mvp2/"):
                self.assertEqual(new, old.removeprefix("../mvp2/"))
            elif re.fullmatch(r"B\d\d", label):
                self.assertEqual(new, f"README.md#{label.lower()}")
                target = re.search(rf"(?ms)^### {label}\s*\n(.*?)(?=^#|\Z)", readme)
                self.assertIsNotNone(target, label)
                case_id = next(case_id for case_id in CASES if case_id.startswith(label + "-"))
                self.assertIn(case_id, target.group(1))
                self.assertIn(CASES[case_id][2], target.group(1))
            elif "mvp2_expectations.py" in old:
                self.assertEqual(new, "README.md#synthetic-source")
            elif "mvp3_cases.py" in old:
                self.assertEqual(new, "README.md#behavioral-controls")
            elif "MVP3_VALIDATION.md" in old:
                self.assertEqual(new, "TIEOUT.json")
            else:
                self.fail(f"Unaccounted decision-review reference: {old}")

    def test_existing_locations_refuse_overwrite(self):
        dest = free_destination()
        self.addCleanup(remove_destination, dest)
        dest.mkdir()
        marker = dest / "operator.txt"
        marker.write_bytes(b"retain me")
        refused = call(dest)
        self.assertEqual(refused.returncode, 2, refused.stderr)
        self.assertFalse(refused.stdout)
        self.assertEqual(set(dest.iterdir()), {marker})
        self.assertEqual(marker.read_bytes(), b"retain me")
        existing_file = free_destination()
        self.addCleanup(remove_destination, existing_file)
        existing_file.write_bytes(b"existing single file")
        refused = call(existing_file)
        self.assertEqual(refused.returncode, 2, refused.stderr)
        self.assertFalse(refused.stdout)
        self.assertEqual(existing_file.read_bytes(), b"existing single file")
        with tempfile.TemporaryDirectory() as folder:
            alias = free_destination()
            self.addCleanup(remove_destination, alias)
            alias.symlink_to(Path(folder), target_is_directory=True)
            refused = call(alias)
            self.assertEqual(refused.returncode, 2, refused.stderr)
            self.assertFalse(refused.stdout)
            self.assertTrue(alias.is_symlink())
            self.assertEqual(list(Path(folder).iterdir()), [])
        invalid = free_destination()
        self.addCleanup(remove_destination, invalid)
        refused = call(invalid, extra=("--source", "elsewhere.sas"))
        self.assertEqual(refused.returncode, 2, refused.stderr)
        self.assertFalse(invalid.exists())

    def test_corrupt_or_missing_evidence_never_creates_a_bundle(self):
        with tempfile.TemporaryDirectory() as folder:
            clone = Path(folder)
            shutil.copytree(
                ROOT / "scripts", clone / "scripts", ignore=shutil.ignore_patterns("__pycache__")
            )
            shutil.copytree(
                ROOT / "tests/fixtures/source-reconstruction/dependency-aware-preview",
                clone / "tests/fixtures/source-reconstruction/dependency-aware-preview",
            )
            shutil.copytree(
                ROOT / "tests/fixtures/source-reconstruction/decision-review",
                clone / "tests/fixtures/source-reconstruction/decision-review",
            )
            (clone / "docs").mkdir()
            shutil.copyfile(
                ROOT / "docs/SYNTHETIC_TIEOUT_VALIDATION.md",
                clone / "docs/SYNTHETIC_TIEOUT_VALIDATION.md",
            )
            (clone / "tests").mkdir(exist_ok=True)
            for name in (
                "mvp2_expectations.py",
                "mvp2_fixture.py",
                "mvp3_cases.py",
                "p2a_support.py",
            ):
                shutil.copyfile(ROOT / "tests" / name, clone / "tests" / name)
            script = clone / "scripts/review_workflow.py"
            control = free_destination()
            self.addCleanup(remove_destination, control)
            ready = call(control, script=script)
            self.assertEqual(ready.returncode, 0, ready.stderr)
            for name, added in (
                (
                    "tests/fixtures/source-reconstruction/dependency-aware-preview/ADR_SPARK.md",
                    None,
                ),
                ("tests/mvp3_cases.py", b"\n# altered\n"),
                (
                    "tests/mvp2_expectations.py",
                    b'\nraise RuntimeError("UNVERIFIED_DECLARATION_EXECUTED")\n',
                ),
            ):
                with self.subTest(name=name):
                    target = clone / name
                    original = target.read_bytes()
                    if added is None:
                        target.unlink()
                    else:
                        target.write_bytes(original + added)
                    refused_path = free_destination()
                    self.addCleanup(remove_destination, refused_path)
                    refused = call(refused_path, script=script)
                    self.assertEqual(refused.returncode, 2, refused.stderr)
                    self.assertFalse(refused.stdout)
                    self.assertNotIn(b"UNVERIFIED_DECLARATION_EXECUTED", refused.stderr)
                    self.assertFalse(refused_path.exists())
                    target.write_bytes(original)

    def test_partial_write_is_cleaned_up(self):
        dest = free_destination()
        self.addCleanup(remove_destination, dest)
        fault = """
import os, runpy, sys
def disk_fault(event, args):
    if event == 'open' and isinstance(args[0], str) and args[0].split('/')[-1] == 'MODULES.md':
        if args[2] & (os.O_WRONLY | os.O_RDWR):
            print('injected output refusal', file=sys.stderr)
            raise OSError('simulated write fault')
sys.addaudithook(disk_fault)
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name='__main__')
"""
        refused = call(dest, guard=fault)
        self.assertEqual(refused.returncode, 2, refused.stderr)
        self.assertIn(b"injected output refusal", refused.stderr)
        self.assertFalse(refused.stdout)
        self.assertFalse(dest.exists())

    def test_promoted_stage_authority_refuses_output(self):
        guard = """
from pathlib import Path
import runpy, sys
sys.argv = sys.argv[1:]
sys.path.insert(0, str(Path(sys.argv[0]).parent))
import mvp1_demo
original = mvp1_demo.render_case
def promoted(*args, **kwargs):
    files, status = original(*args, **kwargs)
    print('changed reconstruction authority', file=sys.stderr)
    return files, {**status, 'semantic_acceptance': 'PASS'}
mvp1_demo.render_case = promoted
runpy.run_path(sys.argv[0], run_name='__main__')
"""
        dest = free_destination()
        self.addCleanup(remove_destination, dest)
        refused = call(dest, guard=guard)
        self.assertEqual(refused.returncode, 2, refused.stderr)
        self.assertIn(b"changed reconstruction authority", refused.stderr)
        self.assertFalse(refused.stdout)
        self.assertFalse(dest.exists())
