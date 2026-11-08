"""Public synthetic intake review binds declared sources and refuses ambiguous or changed evidence."""

from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
import uuid

from workflow.test_review_workflow import ROOT, call, remove_destination


FIXTURE = ROOT / "tests/fixtures/source-reconstruction/intake-sources"
SCRIPT = ROOT / "scripts/review_intake.py"


@unittest.skipUnless(sys.platform in ("darwin", "linux"), "Existing POSIX evidence workflow")
class IntakeReviewTests(unittest.TestCase):
    def two_sources(self, root, *, consumer_input="stage"):
        declarations = []
        for name, mode, raw in (
            (
                "a_consumer.sas.txt",
                "sort",
                f"proc sort data=work.{consumer_input} out=work.ordered; by id; run;\n".encode(),
            ),
            (
                "z_producer.sas.txt",
                "data",
                b"data work.stage; set work.raw; if x < 0 then delete; keep id x; run;\r\n",
            ),
        ):
            (root / name).write_bytes(raw)
            declarations.append(
                {"path": name, "sha256": sha256(raw).hexdigest(), "ranges": [[1, 1]], "mode": mode}
            )
        scope = {"version": 2, "scope": "public-synthetic", "sources": declarations}
        (root / "scope.json").write_text(json.dumps(scope))
        return scope

    def invoke(self, intake, destination=None, *, extra=()):
        if destination is None:
            destination = Path("/tmp") / f"sas-re-int1-{uuid.uuid4().hex}"
            self.addCleanup(remove_destination, destination)
        return call(
            destination, script=SCRIPT, extra=("--intake", str(intake), *extra)
        ), destination

    def inventory(self, root):
        result = subprocess.run(
            [sys.executable, "-IB", str(SCRIPT), "--intake", str(root), "--inventory"],
            capture_output=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_p2a_opt_in_binds_profile_and_literal_include(self):
        with TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            raw = {
                "main.sas": b"%include 'settings.sas';\ndata work.out; set &source.; by id; retain n 0; n + id; run;\n",
                "settings.sas": b"%let source=work.raw;\n",
                "profile.json": json.dumps(
                    {
                        "schema_version": "2.0",
                        "profile_id": "sas94-synthetic-v1",
                        "entrypoints": ["synthetic:main.sas"],
                        "inputs": [
                            {
                                "name": "work.raw",
                                "module_id": "main",
                                "sorted_by": ["id"],
                                "columns": [{"name": "id", "type": "NUMERIC", "length": 8}],
                                "rows": [["1"]],
                            }
                        ],
                        "log_bindings": [],
                        "lst_bindings": [],
                        "numeric_missing_join_policy": "SAS_ORDINARY_MISSING_EQUALS_MISSING",
                    }
                ).encode(),
            }
            for name, data in raw.items():
                (root / name).write_bytes(data)
            hashes = {name: sha256(data).hexdigest() for name, data in raw.items()}
            scope = {
                "version": "p2a/1",
                "scope": "public-synthetic",
                "entrypoint": "main.sas",
                "sources": {name: hashes[name] for name in ("main.sas", "settings.sas")},
                "includes": [["main.sas", "settings.sas"]],
                "supporting": {},
                "profile_sha256": hashes["profile.json"],
            }
            scope_file = root / "scope.json"
            scope_file.write_text(json.dumps(scope))
            legacy, refused = self.invoke(root)
            self.assertEqual(legacy.returncode, 2)
            self.assertFalse(refused.exists())

            result, output = self.invoke(root, extra=("--p2a",))
            self.assertEqual(result.returncode, 0, result.stderr)
            graph = json.loads((output / "EVIDENCE.json").read_bytes())
            self.assertEqual(
                [op["kind"] for op in graph["operations"]], ["INCLUDE", "MACRO", "DATA_STEP"]
            )
            self.assertEqual(graph["profile_sha256"], hashes["profile.json"])
            self.assertEqual(
                graph["operations"][1]["span"]["citation"]["source_sha256"], hashes["settings.sas"]
            )
            self.assertEqual(graph["unknowns"], [])
            manifest = json.loads((output / "MANIFEST.json").read_bytes())
            self.assertEqual(manifest["reference_experiment"], "NOT_RUN")
            self.assertEqual(manifest["semantic_acceptance"], "BLOCKED")

            result, replay = self.invoke(root, extra=("--p2a",))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                {f.name: f.read_bytes() for f in output.iterdir()},
                {f.name: f.read_bytes() for f in replay.iterdir()},
            )

            result, drafts = self.invoke(root, extra=("--p2a", "--modernization-drafts"))
            self.assertEqual(result.returncode, 0, result.stderr)
            for artifact in output.iterdir():
                self.assertEqual(artifact.read_bytes(), (drafts / artifact.name).read_bytes())
            handoff = (drafts / "MODERNIZATION_REVIEW.md").read_text()
            for skill in (
                "sas-reconstruct",
                "sas-specify",
                "sas-analyze",
                "sas-validate",
                "sas-architect",
            ):
                self.assertIn(f"| {skill} |", handoff)
            self.assertIn("GATE-1 and candidate continuation are outside this route", handoff)
            self.assertNotIn("SOURCE_1.json", handoff)
            for label in (
                "SOURCE_DECLARED",
                "INFERRED",
                "PROFILE_ASSUMPTION",
                "PACKAGE_METADATA",
                "UNRESOLVED",
                "PROPOSED",
            ):
                self.assertIn(f"| {label} |", handoff)
            self.assertIn("An edge marked INFERENCE remains inferred", handoff)
            for name in ("migration-profile.yaml", "tie-out.yaml"):
                draft = json.loads((drafts / name).read_bytes())
                self.assertEqual(
                    draft["binding"]["manifest_sha256"],
                    sha256((output / "MANIFEST.json").read_bytes()).hexdigest(),
                )
                self.assertEqual(
                    set(draft["binding"]["evidence"]), {"INVENTORY.json", "EVIDENCE.json"}
                )
                self.assertEqual(
                    draft["binding"]["evidence"]["EVIDENCE.json"],
                    manifest["files"]["EVIDENCE.json"],
                )
            tie_out = json.loads((drafts / "tie-out.yaml").read_bytes())
            self.assertEqual(tie_out["reference"]["sas_execution"], "NOT_RUN")
            self.assertEqual(tie_out["reference"]["semantic_acceptance"], "BLOCKED")

            draft = drafts.parent / f"p2a-citations-{uuid.uuid4().hex}.md"
            self.addCleanup(draft.unlink, missing_ok=True)
            command = [
                sys.executable,
                "-IB",
                str(ROOT / "scripts/check_p2a_citations.py"),
                "--package",
                str(drafts.resolve()),
                "--intake",
                str(root),
                "--draft",
                str(draft.resolve()),
            ]
            valid = (
                "`EVIDENCE.json#/operations/0` `profile.json#/inputs/0/sorted_by`"
                " `scope.json#/profile_sha256`"
            )
            invalid = (
                "\n`INVENTORY.json#/binding/manifest_sha256`"
                "\n`INVENTORY.json#/approval/business_intent`"
                "\n`EVIDENCE.json#/statement_coverage/24`"
                "\nEVIDENCE.json#/operations/0"
            )
            for body, status, decision, count in (
                (valid, 0, "REVIEW_REQUIRED", 0),
                (valid + invalid, 2, "BLOCK", 4),
            ):
                draft.write_text(body)
                preflight = subprocess.run(command, capture_output=True, timeout=60)
                self.assertEqual(preflight.returncode, status, preflight.stdout + preflight.stderr)
                report = json.loads(preflight.stdout)
                self.assertEqual(report["decision"], decision)
                self.assertEqual(len(report["findings"]), count)
                self.assertEqual(report["draft"]["sha256"], sha256(draft.read_bytes()).hexdigest())
                self.assertEqual(report["semantic_acceptance"], "BLOCKED")
                self.assertEqual(report["reference_experiment"], "NOT_RUN")

            scope["includes"] = []
            scope_file.write_text(json.dumps(scope))
            result, partial = self.invoke(root, extra=("--p2a",))
            self.assertEqual(result.returncode, 0, result.stderr)
            partial_graph = json.loads((partial / "EVIDENCE.json").read_bytes())
            self.assertIn(
                "SOURCE_NOT_REACHED", {issue["code"] for issue in partial_graph["unknowns"]}
            )
            self.assertNotIn("MACRO", {op["kind"] for op in partial_graph["operations"]})

            (root / "profile.json").write_bytes(raw["profile.json"] + b"\n")
            result, refused = self.invoke(root, extra=("--p2a",))
            self.assertEqual(result.returncode, 2)
            self.assertIn(b"INTAKE_P2A_SHA256_MISMATCH", result.stderr)
            self.assertFalse(refused.exists())

    def test_inventory_proposes_scope_for_new_sources_and_support(self):
        with TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            self.two_sources(root)
            scope_path = root / "scope.json"
            scope_path.unlink()
            (root / "run.log").write_bytes(b"Unverified public log")
            (root / "run.lst").write_bytes(b"Unverified public listing")
            (root / "settings.json").write_bytes(b"{}")
            discovered = self.inventory(root)
            self.assertEqual(discovered, self.inventory(root))
            self.assertFalse(scope_path.exists())
            self.assertEqual(discovered["blockers"], [])
            self.assertEqual(discovered["inventory"][0]["syntax_recognition"], "SUPPORTED")
            scope_path.write_text(json.dumps(discovered["proposed_scope"]))
            run, destination = self.invoke(root, extra=("--modernization-drafts",))
            self.assertEqual(run.returncode, 0, run.stderr)
            manifest_raw = (destination / "MANIFEST.json").read_bytes()
            manifest = json.loads(manifest_raw)
            replay, replay_destination = self.invoke(root, extra=("--modernization-drafts",))
            self.assertEqual(replay.returncode, 0, replay.stderr)
            handoff = (destination / "MODERNIZATION_REVIEW.md").read_text()
            self.assertIn("`MANIFEST.json`, `SOURCE_1.json`, and", handoff)
            self.assertIn("exactly one of the two source JSON files", handoff)
            for name in ("migration-profile.yaml", "tie-out.yaml", "MODERNIZATION_REVIEW.md"):
                self.assertEqual(
                    (destination / name).read_bytes(), (replay_destination / name).read_bytes()
                )
            for name in ("migration-profile.yaml", "tie-out.yaml"):
                draft = json.loads((destination / name).read_bytes())
                self.assertEqual(draft["status"], "DRAFT")
                self.assertEqual(
                    draft["binding"]["manifest_sha256"], sha256(manifest_raw).hexdigest()
                )
                self.assertEqual(draft["binding"]["inputs"], manifest["inputs"])
                for evidence_name, digest in draft["binding"]["evidence"].items():
                    self.assertEqual(
                        digest["sha256"],
                        sha256((destination / evidence_name).read_bytes()).hexdigest(),
                    )
            for name, role in (
                ("run.log", "log"),
                ("run.lst", "listing"),
                ("settings.json", "configuration"),
            ):
                raw = (root / name).read_bytes()
                self.assertEqual(
                    manifest["inputs"][name],
                    {
                        "role": role,
                        "inspection": "IDENTITY_ONLY",
                        "bytes": len(raw),
                        "sha256": sha256(raw).hexdigest(),
                    },
                )
            self.assertEqual(manifest["cross_file_resolution"], "POTENTIAL")
            self.assertEqual(manifest["reference_experiment"], "NOT_RUN")
            self.assertEqual(manifest["semantic_acceptance"], "BLOCKED")

    def test_inventory_reports_unsupported_source_and_undeclared_file(self):
        with TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            (root / "unknown.sas").write_bytes(b"%include 'external.sas';")
            (root / "unknown.bin").write_bytes(b"arbitrary data")
            report = self.inventory(root)
            self.assertIsNone(report["proposed_scope"])
            self.assertEqual(report["inventory"][0]["inspection"], "NAME_ONLY")
            self.assertEqual(report["inventory"][1]["syntax_recognition"], "UNSUPPORTED")
            self.assertIn("MACRO_MARKER_OUTSIDE_SCOPE", report["inventory"][1]["reason_codes"])

    def test_public_intake_is_deterministic_and_traceable(self):
        with TemporaryDirectory() as temp:
            copied = Path(temp).resolve() / "INTAKE"
            shutil.copytree(FIXTURE, copied)
            runs = [self.invoke(root) for root in (FIXTURE, copied)]
        packages = []
        for run, destination in runs:
            self.assertEqual(run.returncode, 0, run.stderr)
            package = {p.name: p.read_bytes() for p in destination.iterdir()}
            self.assertEqual(
                set(package), {"README.md", "EVIDENCE.json", "MIGRATION_REVIEW.md", "MANIFEST.json"}
            )
            manifest = json.loads(package["MANIFEST.json"])
            self.assertEqual(
                sha256(package["MANIFEST.json"]).hexdigest(),
                "614ced69bb71885cc4e95687983b76de777f653913ebccf7163bb73b86718a5a",
            )
            self.assertEqual(
                json.loads(run.stdout)["manifest_sha256"],
                sha256(package["MANIFEST.json"]).hexdigest(),
            )
            for name, payload in package.items():
                if name != "MANIFEST.json":
                    self.assertEqual(
                        manifest["files"][name],
                        {"bytes": len(payload), "sha256": sha256(payload).hexdigest()},
                    )
            source = (FIXTURE / "pipeline.sas.txt").read_bytes()
            self.assertEqual(
                manifest["inputs"]["pipeline.sas.txt"]["sha256"], sha256(source).hexdigest()
            )
            evidence = json.loads(package["EVIDENCE.json"])
            self.assertEqual(evidence["source"], manifest["inputs"]["pipeline.sas.txt"])
            self.assertEqual(evidence["syntax_recognition"], "PARTIAL")
            self.assertEqual(
                evidence["connection"]["execution_verification"], "EXECUTION_UNVERIFIED"
            )
            self.assertEqual(evidence["interval_effects"]["sort_reachability"], "UNESTABLISHED")
            gaps = evidence["selections"][0]["declared_operation"]["unsupported_statements"]
            self.assertTrue(gaps)
            for gap in gaps:
                span = gap["span"]
                self.assertEqual(
                    sha256(source[span["start"] : span["end"]]).hexdigest(), span["sha256"]
                )
            report = package["MIGRATION_REVIEW.md"].decode()
            for marker in (
                "## TRACE",
                "## MAP",
                "Behavioral obligations",
                "Native Python",
                "distributed engine",
            ):
                self.assertIn(marker, report)
            self.assertEqual(manifest["behavioral_evidence"], "UNAVAILABLE")
            self.assertEqual(manifest["semantic_acceptance"], "BLOCKED")
            self.assertEqual(manifest["copilot_review"], "NOT_TESTED")
            packages.append(package)
        self.assertEqual(*packages)

    def test_refuses_unapproved_intake_and_existing_destination(self):
        with TemporaryDirectory() as temp:
            copied = Path(temp).resolve() / "INTAKE"
            shutil.copytree(FIXTURE, copied)
            for name, data, reason in (
                ("extra.txt", b"extra", b"INTAKE_FILE_SET_MISMATCH"),
                ("scope.json", b"{}", b"INTAKE_SCOPE_NOT_APPROVED"),
                ("pipeline.sas.txt", b"changed", b"SOURCE_SHA256_MISMATCH"),
            ):
                with self.subTest(name=name):
                    (copied / name).write_bytes(data)
                    run, dest = self.invoke(copied)
                    self.assertEqual(run.returncode, 2)
                    self.assertIn(reason, run.stderr)
                    self.assertFalse(dest.exists())
                    if (FIXTURE / name).exists():
                        shutil.copyfile(FIXTURE / name, copied / name)
                    else:
                        (copied / name).unlink()
        run, dest = self.invoke(FIXTURE)
        self.assertEqual(run.returncode, 0, run.stderr)
        before = (dest / "MANIFEST.json").read_bytes()
        run, _ = self.invoke(FIXTURE, dest)
        self.assertEqual(run.returncode, 2)
        self.assertEqual((dest / "MANIFEST.json").read_bytes(), before)

    def configurable_fixture(self, root):
        lines = [
            b"%outside_scope;",
            b"data work.staged; set work.incoming;",
            b"if score < 0 then delete;",
            b"keep id score; run;",
            b"proc sql; select count(*) into :total trimmed from work.staged; quit;",
            b"%if &total = 0 %then %abort_run(empty);",
            b"proc sort data=work.staged out=work.result; by id; run;",
            b"%outside_scope;",
        ]
        raw = b"\r\n".join(lines) + b"\r\n"
        note = b"Public synthetic scope description.\n"
        (root / "different.sas.txt").write_bytes(raw)
        (root / "context.md").write_bytes(note)
        scope = {
            "version": 1,
            "scope": "public-synthetic",
            "mode": "data-sort-sql",
            "sources": [
                {
                    "path": "different.sas.txt",
                    "sha256": sha256(raw).hexdigest(),
                    "ranges": [[2, 4], [7, 7]],
                }
            ],
            "supporting": [
                {"path": "context.md", "sha256": sha256(note).hexdigest(), "role": "note"}
            ],
        }
        (root / "scope.json").write_text(json.dumps(scope))
        return scope, raw, lines

    def test_configurable_pair_has_deterministic_coverage_and_verified_support(self):
        with TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            scope, raw, lines = self.configurable_fixture(root)
            packages = []
            for _ in range(2):
                run, dest = self.invoke(root)
                self.assertEqual(run.returncode, 0, run.stderr)
                packages.append({p.name: p.read_bytes() for p in dest.iterdir()})
            self.assertEqual(*packages)
            evidence = json.loads(packages[0]["EVIDENCE.json"])
            manifest = json.loads(packages[0]["MANIFEST.json"])
            self.assertEqual(evidence["source"]["sha256"], sha256(raw).hexdigest())
            self.assertEqual(evidence["syntax_recognition"], "PARTIAL")
            self.assertEqual(manifest["inputs"]["context.md"]["inspection"], "IDENTITY_ONLY")
            self.assertEqual(
                manifest["inputs"]["context.md"]["sha256"], scope["supporting"][0]["sha256"]
            )
            coverage = manifest["coverage"]
            self.assertEqual(
                [part["kind"] for part in coverage],
                [
                    "UNINSPECTED",
                    "SELECTED_SOURCE_REVIEW",
                    "BOUNDED_INTERVAL_INVENTORY",
                    "SELECTED_SOURCE_REVIEW",
                    "UNINSPECTED",
                ],
            )
            self.assertEqual(coverage[0]["end"], len(lines[0]) + 2)
            self.assertEqual(coverage[-1]["end"], len(raw))
            self.assertEqual([p["end"] for p in coverage[:-1]], [p["start"] for p in coverage[1:]])
            self.assertEqual(evidence["connection"]["classification"], "SOURCE_DECLARED")
            self.assertEqual(
                evidence["connection"]["execution_verification"], "EXECUTION_UNVERIFIED"
            )
            self.assertEqual(manifest["semantic_acceptance"], "BLOCKED")

    def test_configurable_refuses_invalid_scopes_and_file_changes(self):
        def set_source(scope, key, value):
            scope["sources"][0][key] = value

        cases = [
            (lambda s, _: s.update(version=3), b"INTAKE_MANIFEST_VERSION_UNSUPPORTED"),
            (lambda s, _: s.update(mode="execute"), b"INTAKE_REVIEW_MODE_UNSUPPORTED"),
            (lambda s, _: s.update(mode="sort"), b"INTAKE_RANGES_INVALID_FOR_MODE"),
            (
                lambda s, _: s["sources"].append(s["sources"][0]),
                b"INTAKE_MULTIPLE_SOURCES_UNSUPPORTED",
            ),
            (lambda s, _: set_source(s, "path", "../other.sas"), b"UNSAFE_PATH"),
            (
                lambda s, _: set_source(s, "ranges", [[2, 4], [99, 99]]),
                b"LINE_RANGE_OUTSIDE_SOURCE",
            ),
            (
                lambda s, p: (p / "different.sas.txt").write_bytes(b"changed"),
                b"SOURCE_SHA256_MISMATCH",
            ),
            (lambda s, p: (p / "context.md").write_bytes(b"changed"), b"SUPPORT_SHA256_MISMATCH"),
            (lambda s, p: (p / "context.md").unlink(), b"INTAKE_FILE_SET_MISMATCH"),
            (lambda s, p: (p / "extra.txt").write_bytes(b"extra"), b"INTAKE_FILE_SET_MISMATCH"),
        ]
        for change, reason in cases:
            with self.subTest(reason=reason), TemporaryDirectory() as temp:
                root = Path(temp).resolve()
                scope, _, _ = self.configurable_fixture(root)
                change(scope, root)
                (root / "scope.json").write_text(json.dumps(scope))
                run, dest = self.invoke(root)
                self.assertEqual(run.returncode, 2, run.stderr)
                self.assertIn(reason, run.stderr)
                self.assertFalse(dest.exists())

    def test_single_range_reuses_review_and_reports_unsupported_syntax(self):
        with TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            scope, _, _ = self.configurable_fixture(root)
            scope["mode"] = "sort"
            scope["sources"][0]["ranges"] = [[7, 7]]
            (root / "scope.json").write_text(json.dumps(scope))
            run, dest = self.invoke(root)
            self.assertEqual(run.returncode, 0, run.stderr)
            evidence = json.loads((dest / "EVIDENCE.json").read_bytes())
            self.assertEqual(evidence["declared_operation"]["ordering_keys"], ["id"])
            self.assertIn("Declared dependency map", (dest / "README.md").read_text())
            scope["sources"][0]["ranges"] = [[1, 1]]
            (root / "scope.json").write_text(json.dumps(scope))
            run, dest = self.invoke(root, extra=("--modernization-drafts",))
            self.assertEqual(run.returncode, 2)
            draft = json.loads((dest / "migration-profile.yaml").read_bytes())
            self.assertEqual(draft["source_review_status"], "BLOCKED")
            self.assertEqual(draft["target"]["runtime"], "PENDING")
            evidence = json.loads((dest / "EVIDENCE.json").read_bytes())
            self.assertEqual(evidence["syntax_recognition"], "UNSUPPORTED")
            self.assertIn("MACRO_MARKER_OUTSIDE_SCOPE", evidence["reason_codes"])

    def test_two_sources_link_declared_accesses_without_resolving_lineage(self):
        with TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            scope = self.two_sources(root)
            packages = []
            for _ in range(2):
                run, dest = self.invoke(root)
                self.assertEqual(run.returncode, 0, run.stderr)
                packages.append({p.name: p.read_bytes() for p in dest.iterdir()})
            self.assertEqual(*packages)
            files = packages[0]
            manifest = json.loads(files["MANIFEST.json"])
            for name in files.keys() - {"MANIFEST.json"}:
                self.assertEqual(manifest["files"][name]["sha256"], sha256(files[name]).hexdigest())
            self.assertEqual(manifest["package_revision"], "public-intake-review/3")
            self.assertEqual(manifest["copilot_review"], "NOT_TESTED")
            self.assertEqual(manifest["semantic_acceptance"], "BLOCKED")
            (match,) = manifest["cross_file_dependencies"]
            self.assertEqual(match["dataset"], "work.stage")
            self.assertEqual(match["classification"], "POTENTIAL")
            self.assertEqual(
                (match["execution_order"], match["dataset_version"]), ("UNRESOLVED", "UNRESOLVED")
            )
            for key, spec in zip(("reader", "writer"), scope["sources"]):
                ref = match[key]
                self.assertEqual(ref["path"], spec["path"])
                review = next(item for item in manifest["sources"] if item["path"] == ref["path"])
                self.assertEqual(review["coverage"][0]["start"], 0)
                evidence = json.loads(files[review["evidence"]])
                self.assertEqual(evidence["source"]["sha256"], spec["sha256"])
                op = evidence["declared_operation"]
                span = op["span"] if key == "reader" else op["declaration_spans"]["output"]
                raw = (root / spec["path"]).read_bytes()
                selected = evidence["source"]["selected_span"]
                self.assertEqual(
                    selected["sha256"], sha256(raw[selected["start"] : selected["end"]]).hexdigest()
                )
                self.assertLessEqual(selected["start"], span["start"])
                self.assertLessEqual(span["end"], selected["end"])
                if key == "writer":
                    self.assertEqual(
                        span["sha256"], sha256(raw[span["start"] : span["end"]]).hexdigest()
                    )
                self.assertEqual(ref["anchor"], f"bytes-{span['start']}-{span['end']}")
                self.assertIn(f'id="{ref["anchor"]}"', files[review["review"]].decode())
                self.assertIn(f"({review['review']}#{ref['anchor']})", files["README.md"].decode())
            self.assertEqual(json.loads(files["SOURCE_2.json"])["syntax_recognition"], "PARTIAL")

    def test_two_sources_with_unmatched_names_report_unresolved(self):
        with TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            self.two_sources(root, consumer_input="independent")
            run, dest = self.invoke(root)
            self.assertEqual(run.returncode, 0, run.stderr)
            manifest = json.loads((dest / "MANIFEST.json").read_bytes())
            self.assertEqual(manifest["cross_file_dependencies"], [])
            self.assertEqual(manifest["cross_file_resolution"], "UNRESOLVED")

    def test_two_source_refusals_leave_no_package(self):
        cases = [
            (lambda s, _: s["sources"].pop(), b"INTAKE_TWO_SOURCES_REQUIRED"),
            (lambda s, _: s["sources"].append(s["sources"][0]), b"INTAKE_TWO_SOURCES_REQUIRED"),
            (
                lambda s, _: s["sources"][1].update(path="A_CONSUMER.sas.txt"),
                b"INTAKE_FILE_NAME_UNSUPPORTED",
            ),
            (lambda s, _: s["sources"][1].update(path="../escape.sas"), b"UNSAFE_PATH"),
            (lambda s, _: s["sources"][1].update(mode="fit"), b"INTAKE_REVIEW_MODE_UNSUPPORTED"),
            (lambda s, _: s["sources"][1].update(ranges=[[2, 2]]), b"LINE_RANGE_OUTSIDE_SOURCE"),
            (
                lambda s, p: (p / s["sources"][1]["path"]).write_bytes(b"changed"),
                b"SOURCE_SHA256_MISMATCH",
            ),
        ]
        for change, reason in cases:
            with self.subTest(reason=reason), TemporaryDirectory() as temp:
                root = Path(temp).resolve()
                scope = self.two_sources(root)
                change(scope, root)
                (root / "scope.json").write_text(json.dumps(scope))
                run, dest = self.invoke(root)
                self.assertEqual(run.returncode, 2, run.stderr)
                self.assertIn(reason, run.stderr)
                self.assertFalse(dest.exists())
