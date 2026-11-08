"""Private decision review of the fixed public MVP-2 graph and MVP-3 controls."""

from collections import Counter
import hashlib
import json

from ._dependency_diagnostics import _bounded_copy
from ._draft_preview import _STATUS
from .._io_common import EvidenceError
from ..evidence import digest


# Published in MVP2_VALIDATION.md and MVP3_VALIDATION.md. The report pin is the
# full stdout byte digest, including its final newline, not a canonical JSON hash.
MVP2_GRAPH_SHA256 = "19f41dea50825469a89d8fc545fee1d87f09af946d130d62de8f946d90b78017"
MVP2_FIXTURE_SHA256 = "dce463011111389bbd84901b2a94632305b287605af98493f3f88744e2f94716"
MVP3_CASES_SHA256 = "7ca4c6b50cdc7f5b7ce2ee422f5adfe883dba82a39b064140fba2d7a70702342"
MVP3_REPORT_SHA256 = "aee7cbd480b1f6794888616af9c55e8896ecb13fa3dc1585d1b012f0a8508600"


class ReviewBindingError(EvidenceError):
    """A changed or unsupported input cannot produce a decision review."""


def bind_review(graph, report_bytes):
    """Return detached, fixed graph and report data. No source, store or caller-path I/O."""
    if (
        type(report_bytes) is not bytes
        or len(report_bytes) != 15_660
        or hashlib.sha256(report_bytes).hexdigest() != MVP3_REPORT_SHA256
    ):
        raise ReviewBindingError("MVP3_REPORT_MISMATCH")
    report = json.loads(report_bytes)
    try:
        graph = _bounded_copy(graph)
        if digest(graph) != MVP2_GRAPH_SHA256:
            raise ReviewBindingError("MVP2_GRAPH_MISMATCH")
    except EvidenceError as error:
        raise ReviewBindingError(error.code) from None

    reference = report["reference"]
    graph_sources = {
        (op["span"]["file_key"], op["span"]["citation"]["source_sha256"])
        for op in graph["operations"]
    }
    report_sources = {
        ("synthetic:" + name, sha) for name, sha in reference["source_sha256"].items()
    }
    if (
        reference["original_mvp2_graph_sha256"] != MVP2_GRAPH_SHA256
        or reference["original_fixture_sha256"] != MVP2_FIXTURE_SHA256
        or reference["specification_sha256"] != MVP3_CASES_SHA256
        or graph_sources != report_sources
    ):
        raise ReviewBindingError("REVIEW_REFERENCE_MISMATCH")
    authority = {
        "artifact_authority": "DRAFT",
        "semantic_verification": "UNVERIFIABLE",
        "semantic_acceptance": "BLOCKED",
        "benchmark_execution": "NOT_RUN",
    }
    if (
        any(report[key] != status or graph[key] != status for key, status in authority.items())
        or report["full_workflow_gate"] != "BLOCKED"
    ):
        raise ReviewBindingError("REVIEW_AUTHORITY_MISMATCH")
    for case in report["cases"]:
        if (
            case["matches_specification"] is not True
            or case["verdict"] != case["expected_verdict"]
            or case["full_workflow_gate"] != "BLOCKED"
        ):
            raise ReviewBindingError("REVIEW_CONTROL_MISMATCH")
    return graph, report


def render_review(graph, report_bytes):
    """Return one UTF-8 Markdown review, or refuse the input before rendering."""
    graph, report = bind_review(graph, report_bytes)
    cases = {c["case_id"].split("-", 1)[0]: c for c in report["cases"]}
    counts = Counter(c["verdict"] for c in cases.values())
    lines = [
        "# Architecture decision review — ordered measurements and offsets",
        "",
        "UNVERIFIED · public synthetic development evidence",
        "",
        "```text",
        _STATUS,
        "```",
        "",
        "**Production runtime selection is BLOCKED.** The `prepare` module sorts observations into `work.ordered`. "
        "The `enrich` module scales the rows and joins offsets to produce `work.adjusted`. The effects of "
        "`postcheck.sas` are unknown. Independent SAS outputs and measurements on the target workload are still needed. "
        "[SORT](../mvp2/EVIDENCE.md#o1) · [DATA step](../mvp2/EVIDENCE.md#o2) · [SQL](../mvp2/EVIDENCE.md#o3) · "
        "[Include](../mvp2/EVIDENCE.md#o4-fact-0)",
        "",
        "Keep [native Python](../mvp2/ADR_NATIVE.md) as a local comparison baseline if the sort and join "
        "fit the workstation budget. Consider [Spark](../mvp2/ADR_SPARK.md) if measured scale warrants "
        "distribution and the same row-level checks hold across exchanges and retries.",
        "",
        "## Behavioral evidence and candidate obligations",
        "",
        f"**OBSERVATION** The fixed Python probes returned {counts['PASS']} PASS, {counts['FAIL']} deliberate FAIL "
        f"and {counts['UNVERIFIABLE']} UNVERIFIABLE outcomes. All matched their frozen expectations. "
        "A deliberate FAIL means the checker caught an injected defect. An unexpected result blocks review generation. "
        "Neither proposed migration has run against an independently verified SAS output.",
        "",
        "| Requirement and original evidence | Public controls and limit | Native Python | Spark | Next test or human decision |",
        "|---|---|---|---|---|",
    ]

    def row(requirement, refs, probes, observation, native, spark, next_step):
        links = ", ".join(
            f"[{ref}](../mvp2/EVIDENCE.md#{ref.lower().replace(' ', '-')})" for ref in refs
        )
        results = []
        for code in probes:
            case = cases[code]
            # CASES starts at line 85 in the pinned table. A comment precedes B17.
            number = int(code[1:])
            source_line = 102 if code == "B17" else 84 + number
            verdict = "deliberate FAIL" if case["verdict"] == "FAIL" else case["verdict"]
            results.append(f"[{code}](../../tests/mvp3_cases.py#L{source_line}) {verdict}")
        cells = [
            f"**{requirement}**. {links}",
            ". ".join(filter(None, [", ".join(results), observation])),
            native,
            spark,
            next_step,
        ]
        lines.append("| " + " | ".join(cells) + " |")

    row(
        "SORT and SET order",
        ["O1 fact 0", "E2", "E4", "O2 fact 1"],
        ["B05", "B07", "B11"],
        "One full-key tie permutation passed when SET kept it. Reversing composite-key order or reordering ties only at SET failed.",
        "Sort missing keys first on `batch, sequence` and pass the chosen stream to SET.",
        "Verify order where the consumer reads the exchanged rows. A partition-local sort alone is insufficient.",
        "Obtain the site's sort settings and tie policy. Compare keys and complete rows at `work.ordered` and `work.scaled`.",
    )

    scaled_error = cases["B10"]["discrepancies"][0]
    row(
        "Current-row arithmetic and BY state",
        ["O2 fact 2", "O2 fact 3", "E3"],
        ["B01", "B10"],
        f"The BY annotation concerns group flags. For input 6 the faulty division produced "
        f"{scaled_error['extra'][0]['row'][-1]} instead of {scaled_error['missing'][0]['row'][-1]}. "
        "Cross-row dependence of the arithmetic remains unproved.",
        "Compute `scaled = value / 2` on the current row. Track group flags separately if consumed.",
        "Test an equivalent row expression. Retain the grouping constraint pending a boundary test.",
        "Compare the assignment and any actually used group flags at the first and last rows of each key prefix.",
    )

    lost = cases["B09"]["discrepancies"][0]["missing"][0]
    row(
        "Join multiplicity and filtering",
        ["E1", "O3 fact 1"],
        ["B01", "B02", "B09", "B13"],
        f"Deduplicating offsets lost {lost['count']} copy of `({', '.join(lost['row'])})`. Omitting WHERE "
        f"produced {len(cases['B13']['observed']['adjusted'])} rows instead of {len(cases['B13']['expected']['adjusted'])}.",
        "Index a list of offsets per batch. Retain each matching pair and apply `scaled > 0`.",
        "Preserve duplicate matches and predicate semantics through the join. Treat key uniqueness as an open question.",
        "Tie out qualifying row multisets per batch on duplicate, unmatched and skewed keys.",
    )

    row(
        "Ordinary and special missing values",
        ["O1 fact 0", "O2 fact 3", "O3 fact 1"],
        ["B01", "B02", "B14", "B15"],
        "The ordinary missing batch matched and yielded 13. Skipping it lost that row. A missing offset "
        "propagated to the sum. Special missing `.A` was outside the profile.",
        "Represent ordinary missing explicitly in sort, equality, addition and filtering.",
        "Test null and NaN representations separately. Check ordinary-missing matches, order and propagation.",
        "Ask which missing classes occur and obtain reference rows for each before choosing their mapping.",
    )

    row(
        "Final SQL order",
        ["O3 fact 1"],
        ["B03", "B06", "B08", "B12"],
        "Both batch-1 orders `2,5` and `5,2` satisfied the model. B08 reversed batches. B12's validator "
        "rejected a valid permutation even though its own rows were valid.",
        "Compare the `work.adjusted` row multiset within each ascending batch. The projection drops `sequence`.",
        "Require batch order at collection or handoff. Preserve multiplicity across partitions without a hidden secondary key.",
        "Confirm the consumer accepts ties in either order. Any stronger order needs separate evidence.",
    )

    row(
        "Numeric precision",
        ["O2 fact 3", "O3 fact 1"],
        ["B02", "B10", "B16"],
        "The model admits integer inputs of magnitude up to 1,000,000 and uses exact half-units. The precision-boundary input "
        "`9007199254740993` was refused. The numeric tolerance is UNKNOWN.",
        "Check the proposed dtype, rounding, range and missing arithmetic against reference values.",
        "Check casts and expression order in the proposed distributed representation on the same values.",
        "Have the owner specify admissible ranges and tolerances, then test cancellation, overflow and rounding boundaries.",
    )

    blocks = cases["B04"]["chunks"]
    row(
        "Partition boundary",
        ["O2 fact 2", "O2 fact 3", "E3"],
        ["B04"],
        f"Two chunks of {blocks[0]} and {blocks[1]} rows split one equal-key group and preserved this scalar result. "
        "General partition safety and BY-state continuity remain unproved.",
        "Compare chunked output with a continuous ordered scan, including group-boundary rows.",
        "Vary partition counts, skew, exchanges and retry points. Check state and multiplicity across each boundary.",
        "Repeat with key-prefix changes and an independently specified state witness before permitting a split.",
    )

    gap = report["unresolved_include"]
    row(
        "Unresolved include",
        ["O4 fact 0"],
        ["B17"],
        f"PASS covers O1–O3 only. O4 (`{gap['target']}`) is {gap['verdict']}. Its reads, writes and "
        "effect on the final result are UNKNOWN.",
        "Keep local output provisional until the target's effects are known.",
        "Keep distributed stage and retry boundaries open around O4.",
        "Obtain separately authorized target evidence or an attributable scope decision. Keep full-workflow acceptance BLOCKED.",
    )

    row(
        "Workload size, hardware, cost and runtime",
        ["E4", "E1"],
        [],
        "No control measures production rows, bytes, skew, memory, hardware, elapsed time or cost. All are UNKNOWN. "
        "[Graph observation inventory](../mvp2/EVIDENCE.md#proof-obligations).",
        "Size input, sort scratch, join fan-out and peak workstation memory.",
        "Size exchange volume, skew, spill, worker memory and recovery overhead.",
        "Name the workload, hardware and budgets. After correctness review and separate approval, measure both candidates on the same inputs.",
    )

    lines.extend(
        [
            "",
            "## Trace and scope",
            "",
            f"- [Original SAS declarations](../../tests/mvp2_expectations.py#L9-L31) · workspace `{graph['workspace_id']}`, "
            f"run `{graph['run_id']}`, attempt `{graph['attempt_id']}`. [Canonical evidence](../mvp2/EVIDENCE.md) "
            f"has graph SHA-256 `{MVP2_GRAPH_SHA256}`.",
            f"- [Frozen cases](../../tests/mvp3_cases.py#L84-L102) · SHA-256 `{MVP3_CASES_SHA256}`. "
            f"[Observed case results](../../docs/MVP3_VALIDATION.md#case-results) · full JSON report SHA-256 `{MVP3_REPORT_SHA256}`.",
            "- The graph identifies the original synthetic run. The extra input vectors belong to the public case table. "
            "The fixed controls establish development behavior only. Independent semantic acceptance remains BLOCKED.",
        ]
    )
    return ("\n".join(lines) + "\n").encode("utf-8")
