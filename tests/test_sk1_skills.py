"""Repository skill contracts and the fixed development workflow they reference.

These checks inspect on-disk guidance and exercise Python. Agent-side discovery
and model invocation require separate observations.
"""

from hashlib import sha256
import json
import os
from pathlib import Path
import re
import runpy
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import unquote, urlsplit

from test_review_workflow import FILES, STATUS, free_destination, remove_destination


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples/offline-review"
SKILLS = {
    "sas-reconstruct": {"MANIFEST.json", "EVIDENCE.md"},
    "sas-specify": {"EVIDENCE.md", "PRD.md", "MODULES.md"},
    "sas-architect": {"ARCHITECTURE.md", "ADR_NATIVE.md", "ADR_SPARK.md", "DECISION_REVIEW.md", "TIEOUT.json"},
    "sas-analyze": {"MANIFEST.json", "EVIDENCE.md", "ARCHITECTURE.md", "DECISION_REVIEW.md"},
    "sas-validate": {"MANIFEST.json", "EVIDENCE.md", "TIEOUT.json", "DECISION_REVIEW.md"},
}
COMMAND_PREFIX = ["python3.12", "-IB", "scripts/review_workflow.py", "--destination"]
SAMPLE_DIGEST = "da630e0225c7b2705bc22d37154560031c93ee675e1ca8c64fb312a0a1c179b6"


def skill(name):
    return ROOT / "skills" / name / "SKILL.md"


def commands(path):
    # Only the prescribed fixed argv will ever be executed. Do not run Markdown as shell code.
    blocks = re.findall(r"(?ms)^```(?:bash|sh|shell|console|powershell|cmd|python)\s*\n(.*?)^```", path.read_text())
    return [shlex.split(line) for block in blocks for line in block.splitlines() if line.strip()]


def instructed_argv():
    [argv] = commands(skill("sas-reconstruct"))
    if len(argv) != 5 or argv[:4] != COMMAND_PREFIX or not re.fullmatch(
            r"/tmp/sas-re-review(?:-[A-Za-z0-9_-]{1,64})?", argv[-1]):
        raise AssertionError(f"Unsupported skill command: {argv!r}")
    return argv


def package_digest(root):
    mapping = {p.name: sha256(p.read_bytes()).hexdigest() for p in root.iterdir()}
    return sha256((json.dumps(mapping, sort_keys=True, separators=(",", ":")) + "\n").encode()).hexdigest()


class SkillDefinitionTests(unittest.TestCase):
    def test_metadata_and_authoritative_sources(self):
        descriptions = set()
        self.assertEqual({p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md")}, set(SKILLS))
        for name in SKILLS:
            with self.subTest(skill=name):
                path = skill(name)
                text = path.read_text(encoding="utf-8")
                self.assertTrue(path.is_file() and not path.is_symlink())
                front = re.match(r"\A---\n(.*?)\n---\n(.+)", text, re.S)
                self.assertIsNotNone(front)
                # These skills use one plain string per field; no optional YAML parser is needed.
                fields = [re.fullmatch(r"(name|description): (.+)", line) for line in front[1].splitlines()]
                self.assertTrue(all(fields))
                self.assertCountEqual([field[1] for field in fields], ["name", "description"])
                metadata = {field[1]: field[2] for field in fields}
                self.assertEqual(metadata["name"], name)
                self.assertGreater(len(metadata["description"].split()), 4)
                descriptions.add(metadata["description"])
                self.assertTrue(front[2].strip())
        self.assertEqual(len(descriptions), len(SKILLS))

    def test_discovery_alias_resolves_to_the_same_definitions(self):
        link = ROOT / ".agents" / "skills"
        self.assertTrue(link.is_symlink())
        self.assertEqual(os.readlink(link), "../skills")
        for name in SKILLS:
            with self.subTest(skill=name):
                self.assertTrue((link / name / "SKILL.md").samefile(skill(name)))

    def test_evidence_references_commands_and_statuses(self):
        for name, artifacts in SKILLS.items():
            with self.subTest(skill=name):
                path = skill(name)
                text = path.read_text()
                for artifact in artifacts:
                    self.assertIn(artifact, text)
                    self.assertTrue((SAMPLE / artifact).is_file())
                for status in STATUS.values():
                    self.assertIn(status, text)
                for target in re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", text):
                    url = urlsplit(target)
                    self.assertFalse(url.scheme or url.netloc, target)
                    resolved = (path.parent / unquote(url.path)).resolve()
                    self.assertTrue(resolved.is_relative_to(ROOT) and resolved.is_file(), target)
                    if url.fragment and resolved.suffix == ".md":
                        headings = [h.lower().replace(" ", "-") for h in re.findall(
                            r"^#{1,6} (.+)$", resolved.read_text(), re.M)]
                        self.assertIn(unquote(url.fragment), headings, target)
                self.assertNotRegex(text, r"`(?:sas-re\s+|python(?:3(?:\.12)?)?\s+-m\s+sas_re|(?:bash\s+)?scripts/workstation\.sh)")
                if name != "sas-reconstruct":
                    self.assertFalse(commands(path))
        instructed_argv()
        self.assertRegex(skill("sas-reconstruct").read_text(), r"(?is)Windows.{0,130}BLOCKED|BLOCKED.{0,130}Windows")

    def test_analysis_and_validation_links_bind_the_existing_subject(self):
        references = {
            "sas-analyze": ("src/sas_re/_dependency_diagnostics.py", "docs/P3_A1_DESIGN.md"),
            "sas-validate": ("tests/mvp3_cases.py", "scripts/mvp3_tieout.py", "docs/MVP3_VALIDATION.md"),
        }
        for name, sources in references.items():
            with self.subTest(skill=name):
                path = skill(name)
                linked = {}
                for target in re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", path.read_text()):
                    resolved = (path.parent / unquote(urlsplit(target).path)).resolve()
                    linked[resolved.name] = resolved
                for source in sources:
                    self.assertEqual(linked[Path(source).name], ROOT / source)
                for artifact in SKILLS[name]:
                    self.assertEqual(linked[artifact], SAMPLE / artifact)
                subject = json.loads(linked["MANIFEST.json"].read_bytes())["subject"]
                for artifact in {"EVIDENCE.md", "ARCHITECTURE.md"} & SKILLS[name]:
                    graph = re.search(r"Graph SHA-256 `([0-9a-f]{64})`", linked[artifact].read_text())
                    self.assertIsNotNone(graph, artifact)
                    self.assertEqual(graph[1], subject["graph_sha256"])
                if name == "sas-validate":
                    reference = json.loads(linked["TIEOUT.json"].read_bytes())["reference"]
                    self.assertEqual(reference["original_mvp2_graph_sha256"], subject["graph_sha256"])
                    case_digest = sha256(linked["mvp3_cases.py"].read_bytes()).hexdigest()
                    self.assertEqual(case_digest, subject["case_table_sha256"])
                    self.assertEqual(case_digest, reference["specification_sha256"])

    def test_original_consolidated_sample_hash(self):
        self.assertEqual({p.name for p in SAMPLE.iterdir()}, FILES)
        self.assertEqual(package_digest(SAMPLE), SAMPLE_DIGEST)


@unittest.skipUnless(sys.platform in ("darwin", "linux"), "Development fixture I/O requires qualified POSIX")
class SkillCommandTests(unittest.TestCase):
    def test_instruction_produces_the_bound_ten_file_package(self):
        argv = instructed_argv()
        dest = free_destination()
        self.addCleanup(remove_destination, dest)
        # Use the test's prepared interpreter and only substitute a fresh destination.
        run = subprocess.run([sys.executable, *argv[1:-1], str(dest)], cwd=ROOT,
                             env={**os.environ, "PATH": ""}, capture_output=True, timeout=60)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual({p.name for p in dest.iterdir()}, FILES)
        self.assertEqual(package_digest(dest), SAMPLE_DIGEST)
        manifest = json.loads((dest / "MANIFEST.json").read_bytes())
        self.assertEqual(json.loads(run.stdout)["manifest_sha256"], sha256((dest / "MANIFEST.json").read_bytes()).hexdigest())
        self.assertEqual(manifest["subject"]["graph_sha256"], "19f41dea50825469a89d8fc545fee1d87f09af946d130d62de8f946d90b78017")
        self.assertEqual((manifest["reconstruction_status"], manifest["stage_gate"]), ("PARTIAL", "BLOCKED"))
        for key, value in STATUS.items():
            self.assertEqual(manifest[key], value)

    def test_instruction_blocks_before_destination_access_on_simulated_windows(self):
        argv = instructed_argv()
        dest = free_destination()
        self.addCleanup(remove_destination, dest)
        guard = """
import runpy, sys
sys.argv = sys.argv[1:]
entry = runpy.run_path(sys.argv[0])["main"]
sys.platform = "win32"
entry()
"""
        run = subprocess.run([sys.executable, argv[1], "-c", guard, *argv[2:-1], str(dest)],
                             cwd=ROOT, capture_output=True, timeout=30)
        self.assertEqual(run.returncode, 2, run.stderr)
        self.assertIn(b"FILESYSTEM_CAPABILITY_UNAVAILABLE", run.stderr)
        self.assertFalse(run.stdout or dest.exists())


@unittest.skipUnless(os.name == "posix", "POSIX Git checkout of a symlink")
class SkillAliasGuardTests(unittest.TestCase):
    def test_only_the_exact_staged_and_worktree_alias_is_allowed(self):
        guard = runpy.run_path(str(ROOT / "scripts/check_repository.py"))["check"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            baseline = json.loads((ROOT / "src/sas_re/data/baseline.json").read_text())
            for name in ("src/sas_re/data/baseline.json", baseline["specification"]["path"]):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
            shutil.copytree(ROOT / "skills", root / "skills")
            alias = root / ".agents/skills"
            alias.parent.mkdir()
            alias.symlink_to("../skills", target_is_directory=True)
            subprocess.run(["git", "add", "-f", "."], cwd=root, check=True)
            self.assertEqual(guard(root), [])

            for staged, as_file in ((False, False), (True, False), (False, True), (True, True)):
                with self.subTest(staged=staged, regular=as_file):
                    alias.unlink()
                    if as_file:
                        alias.write_text("../skills")
                    else:
                        alias.symlink_to("../other", target_is_directory=True)
                    if staged:
                        subprocess.run(["git", "add", "-f", ".agents/skills"], cwd=root, check=True)
                        alias.unlink()
                        alias.symlink_to("../skills", target_is_directory=True)
                    self.assertTrue(guard(root))
                    alias.unlink()
                    alias.symlink_to("../skills", target_is_directory=True)
                    subprocess.run(["git", "add", "-f", ".agents/skills"], cwd=root, check=True)

            # The one link grants no permission for another layer of aliasing.
            for directory in ("skills", ".agents"):
                with self.subTest(aliased_directory=directory):
                    original = root / directory
                    relocated = root / (directory + "-saved")
                    original.rename(relocated)
                    original.symlink_to(relocated.name, target_is_directory=True)
                    try:
                        self.assertTrue(guard(root))
                    finally:
                        original.unlink()
                        relocated.rename(original)

            (root / ".agents/local.md").write_text("synthetic unintended local file\n")
            subprocess.run(["git", "add", "-f", ".agents/local.md"], cwd=root, check=True)
            self.assertTrue(guard(root))
