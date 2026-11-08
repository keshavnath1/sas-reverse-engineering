"""Build an offline review for either of two approved public synthetic workflows."""

import argparse
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory

try:
    from sas_re._decision_review import MVP2_GRAPH_SHA256, render_review
    from sas_re._draft_preview import _STATUS
    from sas_re.evidence import digest
    from sas_re.platform_io import require_evidence_io
    from sas_re.safeio import EvidenceError
except ModuleNotFoundError as err:
    raise SystemExit(f"Missing {err.name}. Run with the project's prepared Python 3.12 environment "
                     "(for example .venv/bin/python3.12).") from None


ROOT = Path(__file__).resolve().parents[1]
# Isolated Python omits the script directory. Only fixed development helpers are imported.
sys.path.insert(0, str(ROOT / "scripts"))
from mvp1_demo import FILES, render_case, scratch_destination, write_bundle
from mvp3_tieout import _load_cases, build_report
from mvp4_review import verify_references

PREVIEW_MAP_SHA256 = "218a0111e99f64d4869570e46e7fa951ff8dfe1db617e9d0d72f9dc06624658c"
ORIGINAL_REVIEW_SHA256 = "9aa03933aa24121b786f3939e4e4bec3555302b43c117e3dda9333de9fa04afe"
AUTHORITY_FIELDS = ("artifact_authority", "semantic_verification", "semantic_acceptance", "benchmark_execution")
STATE_GRAPH_SHA256 = "6ec1a62ae2180e05c54c69f6f15a02ecd4678ee925fb37f29796ba7d2842c965"
STATE_EXPECTATIONS_SHA256 = "f42549738a041db87d3547adec59ddfd0f9b15aa2621f1cf0b7ea7fa9f7ffd93"


def content_hash(data):
    return sha256(data).hexdigest()


def portable_review(raw, case_ids):
    """Only relocate the reviewed links; an unfamiliar target needs a new review."""
    def relocate(match):
        label, target = match.groups()
        if target.startswith("../mvp2/") and target.removeprefix("../mvp2/").split("#")[0] in FILES:
            local = target.removeprefix("../mvp2/")
        elif label in case_ids and target.startswith("../../tests/mvp3_cases.py#L"):
            local = "README.md#" + label.lower()
        elif target == "../../tests/mvp2_expectations.py#L9-L31":
            local = "README.md#synthetic-source"
        elif target == "../../tests/mvp3_cases.py#L84-L102":
            local = "README.md#behavioral-controls"
        elif target == "../../docs/MVP3_VALIDATION.md#case-results":
            local = "TIEOUT.json"
        else:
            raise ValueError("Unexpected link in the fixed decision review")
        return f"[{label}]({local})"

    return re.sub(r"\[([^]\n]+)\]\(([^)\n]+)\)", relocate, raw.decode("utf-8")).encode("utf-8")


def reading_guide(declarations, cases, report):
    lines = [
        "# Offline architecture review — ordered measurements and offsets", "",
        "UNVERIFIED · fixed public synthetic development demonstration", "", "```text", _STATUS, "```", "",
        "The `prepare` module sorts observations by `batch, sequence`. The `enrich` module reads the "
        "ordered rows, divides each current value by two, and joins the result to batch offsets. "
        "The final SQL projection is ordered by `batch` alone. A literal include names `postcheck.sas`; "
        "its target and effects are unresolved.", "",
        "## Review order", "",
        "1. Open [DECISION_REVIEW.md](DECISION_REVIEW.md) for the decision, then [ARCHITECTURE.md](ARCHITECTURE.md) "
        "for the module handoff and dependency diagram.",
        "2. Read the [draft PRD](PRD.md) and [module specifications](MODULES.md). Follow O, E and fact references "
        "into [EVIDENCE.md](EVIDENCE.md) for the original IDs, byte spans and hashes of the "
        "[synthetic source](#synthetic-source).",
        "3. Compare the [native Python](ADR_NATIVE.md) and [conditional Spark](ADR_SPARK.md) proposals. "
        "Both need independent reference outputs and workload measurements before runtime selection.",
        "4. Inspect the [fixed controls](#behavioral-controls) and [TIEOUT.json](TIEOUT.json) for the input rows, "
        "frozen expectations, observed probe outputs and individual discrepancies.",
        "5. Use [MANIFEST.json](MANIFEST.json) to verify the bound subject, filenames, payload sizes and SHA-256 "
        "digests. The command prints the digest of the manifest itself separately.", "",
        "## Scope", "",
        "Source consistency passed. Reconstruction is PARTIAL because the include is unresolved. "
        "Production runtime selection and full-workflow acceptance are BLOCKED. No SAS or Spark job ran. "
        "The controls establish no general partition safety, semantic certification or performance result.", "",
        "This developer command accepts one public synthetic fixture only. Real-source intake, broader SAS coverage, "
        "native Windows qualification and independent semantic evaluation require separate work.", "",
        "## Reproduce the folder", "",
        "From the development checkout with its prepared Python 3.12 environment active, run:", "",
        "```bash", "python3.12 -IB scripts/review_workflow.py --destination /tmp/sas-re-review", "```", "",
        "Use a fresh destination each time. If that directory exists, use a name such as "
        "`/tmp/sas-re-review-second`. The command prints the README path and the manifest digest.", "",
        "## Synthetic source", "",
        "These are the exact public source texts behind the graph. Evidence line numbers refer to these "
        "individual files, starting at line 1.", "",
    ]
    for name, source in declarations["SOURCES"].items():
        lines.extend([f"### {name}", "", f"SHA-256 `{content_hash(source)}`.", "", "```sas",
                      source.decode("ascii").removesuffix("\n"), "```", ""])
    lines.extend(["## Behavioral controls", "",
                  "The 17 probes yielded 7 PASS, 8 deliberate FAIL and 2 UNVERIFIABLE outcomes. "
                  "Every probe matched its frozen expectation. A deliberate FAIL means the checker caught an "
                  "injected defect. The other synthetic input sets are behavioral challenges outside the original "
                  "graph identity. See [TIEOUT.json](TIEOUT.json) for full rows and verdicts.", ""])
    for case in report["cases"]:
        case_id = case["case_id"]
        input_id, probe, expected, first = cases["CASES"][case_id]
        observed = "deliberate FAIL" if case["verdict"] == "FAIL" else case["verdict"]
        lines.extend([f"### {case_id.split('-', 1)[0]}", "",
                      f"`{case_id}` · input `{input_id}` · probe `{probe}`. "
                      f"Expected {expected}. Observed {observed}."])
        if first:
            error = case["discrepancies"][0]
            lines.append(f"Expected first discrepancy at `{first}`; observed `{error['stage']}` ({error['reason']}).")
        elif case["verdict"] == "UNVERIFIABLE":
            lines.append("Outside the frozen numeric profile. No candidate rows were assessed.")
        elif probe == "unresolved_include":
            lines.append("PASS covers O1–O3 only. The include at O4 remains UNVERIFIABLE.")
        lines.append("")
    return ("\n".join(lines).rstrip() + "\n").encode("utf-8")


def _assemble(scratch):
    require_evidence_io()
    verify_references()
    # Validate both literal files before importing the fixture adapter's declarations.
    cases, declarations = _load_cases()
    sys.path.insert(0, str(ROOT / "tests"))
    try:
        from mvp2_fixture import make_multi_module_case
        from p2a_support import PROFILE_KEY
    finally:
        sys.path.pop(0)

    with TemporaryDirectory(prefix="sas-re-review-fixture-", dir=scratch) as temporary:
        case = make_multi_module_case(temporary)
        *_, graph = case
        files, status = render_case(case, declarations["CASE"], MVP2_GRAPH_SHA256, PROFILE_KEY,
                                    additional_status=("source_consistency", "reconstruction_status", "stage_gate"))
    if (status["source_consistency"], status["reconstruction_status"], status["stage_gate"]) != ("PASSED", "PARTIAL", "BLOCKED"):
        raise ValueError("Unexpected reconstruction status")
    hashes = {name: content_hash(data) for name, data in files.items()}
    if set(files) != set(FILES) or digest(hashes) != PREVIEW_MAP_SHA256:
        raise ValueError("Generated preview differs from the accepted six-file digest")
    for name in FILES:
        if files[name] != (ROOT / "tests/fixtures/source-reconstruction/dependency-aware-preview" / name).read_bytes():
            raise ValueError(f"Accepted preview differs: {name}")

    report = build_report()
    if any(status[field] != report[field] for field in AUTHORITY_FIELDS):
        raise ValueError("Reconstruction and tie-out authority disagree")
    files["TIEOUT.json"] = (json.dumps(report, allow_nan=False) + "\n").encode("utf-8")
    review = render_review(graph, files["TIEOUT.json"])
    if content_hash(review) != ORIGINAL_REVIEW_SHA256 or review != (ROOT / "tests/fixtures/source-reconstruction/decision-review/DECISION_REVIEW.md").read_bytes():
        raise ValueError("Original decision review mismatch")
    short_ids = {case_id.split("-", 1)[0] for case_id in cases["CASES"]}
    files["DECISION_REVIEW.md"] = portable_review(review, short_ids)
    files["README.md"] = reading_guide(declarations, cases, report)

    counts = Counter(c["verdict"] for c in report["cases"])
    if counts != {"PASS": 7, "FAIL": 8, "UNVERIFIABLE": 2}:
        raise ValueError("Unexpected tie-out counts")
    reference = report["reference"]
    subject = {key: graph[key] for key in ("workspace_id", "run_id", "attempt_id", "source_fingerprint", "scope_manifest_sha256")}
    subject.update(fixture=declarations["CASE"], graph_sha256=status["graph_sha256"], source_sha256=reference["source_sha256"],
                   fixture_sha256=reference["original_fixture_sha256"], case_table_sha256=reference["specification_sha256"])
    manifest = {
        **{key: report[key] for key in AUTHORITY_FIELDS}, "subject": subject,
        "source_consistency": status["source_consistency"], "reconstruction_status": status["reconstruction_status"],
        "stage_gate": status["stage_gate"], "full_workflow_gate": report["full_workflow_gate"],
        "tieout_counts": {"PASS": counts["PASS"], "deliberate FAIL": counts["FAIL"], "UNVERIFIABLE": counts["UNVERIFIABLE"]},
        "accepted_preview_map_sha256": PREVIEW_MAP_SHA256, "original_decision_review_sha256": ORIGINAL_REVIEW_SHA256,
        "files": {name: {"bytes": len(data), "sha256": content_hash(data)} for name, data in files.items()},
        "manifest_file": "MANIFEST.json", "manifest_hash_location": "Exact file digest in the command's stdout receipt.",
    }
    files["MANIFEST.json"] = (json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")
    return files


def _assemble_state(scratch):
    """Reuse the approved P2A case; missing behavioral evidence remains explicit."""
    require_evidence_io()
    expectations = ROOT / "tests/p2a_expectations.py"
    if content_hash(expectations.read_bytes()) != STATE_EXPECTATIONS_SHA256:
        raise ValueError("Stateful public expectations mismatch")
    sys.path.insert(0, str(ROOT / "tests"))
    try:
        from p2a_expectations import PUBLIC_CASES
        from p2a_support import PROFILE_KEY, make_case
    finally:
        sys.path.pop(0)
    declarations = PUBLIC_CASES["by_retain_and_sum"]
    with TemporaryDirectory(prefix="sas-re-review-state-", dir=scratch) as temporary:
        case = make_case(temporary, declarations, attempt="reconstruct1")
        graph = case[3]
        files, status = render_case(case, "by_retain_and_sum", STATE_GRAPH_SHA256, PROFILE_KEY,
                                    additional_status=("source_consistency", "reconstruction_status", "stage_gate"),
                                    revision="tf1")
    if (status["source_consistency"], status["reconstruction_status"], status["stage_gate"]) != ("PASSED", "COMPLETE", "BLOCKED"):
        raise ValueError("Unexpected stateful reconstruction status")
    authority = dict(line.split(": ", 1) for line in _STATUS.splitlines())
    if any(status[key] != value for key, value in authority.items()):
        raise ValueError("Stateful reconstruction authority mismatch")
    lines = ["# Offline architecture review — retained accumulation", "",
             "UNVERIFIED · approved public synthetic development fixture", "", "```text", _STATUS,
             "behavioral_evidence: UNAVAILABLE", "```", "",
             "## Missing behavioral evidence", "",
             "No approved behavioral oracle or executed tie-out report is available for this fixture. "
             "TIEOUT.json and DECISION_REVIEW.md are omitted. The hand-authored expectations below are "
             "public development reference material. They establish no independently verified SAS result.", "",
             "## Review order", "",
             "Read [PRD.md](PRD.md), [MODULES.md](MODULES.md) and [ARCHITECTURE.md](ARCHITECTURE.md). "
             "Trace original IDs, spans, state and value lineage in [EVIDENCE.md](EVIDENCE.md). "
             "Compare [ADR_NATIVE.md](ADR_NATIVE.md) and [ADR_SPARK.md](ADR_SPARK.md) as conditional proposals. "
             "Verify payload hashes and the selected subject in [MANIFEST.json](MANIFEST.json).", "",
             "## Reconstruction and limits", "",
             f"Source consistency `{status['source_consistency']}`. Reconstruction `{status['reconstruction_status']}` "
             "within the supported profile. Stage gate and full-workflow semantic acceptance remain BLOCKED. "
             "The declared input is ordered by group, subkey. RETAIN initializes balance to 8; FIRST.group "
             "resets it to 0 before accumulation. The sum statement uses retained state across rows, "
             "and LAST.subkey guards marker assignment. Review the source interpretations and partition "
             "obligations against the cited facts. No execution or safe partition boundary is certified.", "",
             "## Synthetic source", ""]
    for name, source in declarations["files"].items():
        lines.extend([f"### {name}", "", f"SHA-256 `{content_hash(source)}`.", "", "```sas",
                      source.decode("ascii").removesuffix("\n"), "```", ""])
    lines.extend(["## Declared synthetic input", "", "```json",
                  json.dumps(declarations["inputs"], indent=2), "```", "",
                  "## Hand-authored expectations", "",
                  f"Original declaration file SHA-256 `{STATE_EXPECTATIONS_SHA256}`; case `by_retain_and_sum`. "
                  "These rows and flags were specified in the existing public P2A case. They were not "
                  "computed or assessed by a behavioral oracle in this command.", "", "```json",
                  json.dumps(declarations["hand_trace"], indent=2), "```", "",
                  "## Reproduce", "", "```bash",
                  "python3.12 -IB scripts/review_workflow.py --fixture by-retain-and-sum --destination /tmp/review-state",
                  "```", "", "Choose a fresh destination for each run. The receipt supplies the manifest digest."])
    files["README.md"] = ("\n".join(lines).rstrip() + "\n").encode("utf-8")
    subject = {key: graph[key] for key in ("workspace_id", "run_id", "attempt_id", "source_fingerprint", "scope_manifest_sha256")}
    subject.update(fixture="by_retain_and_sum", graph_sha256=STATE_GRAPH_SHA256,
                   fixture_sha256=STATE_EXPECTATIONS_SHA256,
                   source_sha256={name: content_hash(raw) for name, raw in declarations["files"].items()})
    manifest = {**authority, "package_revision": "two-fixture-review/1", "preview_revision": "two-fixture-preview/1",
                "fixture_selection": "by-retain-and-sum", "subject": subject,
                "behavioral_evidence": "UNAVAILABLE", "behavioral_evidence_reason": "No approved behavioral oracle or tie-out report",
                "hand_authored_expectations": {"declaration_sha256": STATE_EXPECTATIONS_SHA256, "case": "by_retain_and_sum"},
                "source_consistency": status["source_consistency"], "reconstruction_status": status["reconstruction_status"],
                "stage_gate": status["stage_gate"], "full_workflow_gate": "BLOCKED",
                "files": {name: {"bytes": len(raw), "sha256": content_hash(raw)} for name, raw in files.items()},
                "manifest_file": "MANIFEST.json", "manifest_hash_location": "Exact file digest in the command's stdout receipt."}
    files["MANIFEST.json"] = (json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--destination", action="append", required=True,
                        help="fresh system-scratch review directory")
    parser.add_argument("--fixture", choices=("mvp2", "by-retain-and-sum"), action="append",
                        help="approved public example; omission preserves the legacy MVP-2 package")
    args = parser.parse_args()
    if len(args.destination) != 1:
        parser.error("supply --destination exactly once")
    if args.fixture is not None and len(args.fixture) != 1:
        parser.error("supply --fixture at most once")
    try:
        require_evidence_io()
        prefix = "review-" if args.fixture and os.path.basename(args.destination[0]).startswith("review-") else None
        scratch, leaf = scratch_destination(args.destination[0], "review", allow_plain_name=True, name_prefix=prefix)
        if os.path.lexists(scratch / leaf):
            raise FileExistsError
        files = _assemble_state(scratch) if args.fixture == ["by-retain-and-sum"] else _assemble(scratch)
        # The shared writer exclusively reserves the destination. Install the manifest last.
        names = (*FILES, *(name for name in ("TIEOUT.json", "DECISION_REVIEW.md") if name in files), "README.md", "MANIFEST.json")
        write_bundle(scratch, leaf, files, names=names)
    except FileExistsError:
        parser.exit(2, "BLOCKED: destination exists; choose a new review directory\n")
    except (EvidenceError, RuntimeError, ValueError, OSError) as err:
        parser.exit(2, f"BLOCKED: {err}\n")
    manifest = json.loads(files["MANIFEST.json"])
    print(json.dumps({"open": str(scratch / leaf / "README.md"), "manifest_sha256": content_hash(files["MANIFEST.json"]),
                      **{field: manifest[field] for field in AUTHORITY_FIELDS}}, indent=2))


if __name__ == "__main__":
    main()
