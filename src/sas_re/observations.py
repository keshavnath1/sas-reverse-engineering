"""Extract observations from the closed public synthetic LOG/LST profile.

Explicit bindings select evidence lines; filenames and apparent log names do not
establish provenance. Evidence is read but SAS is never executed, and observed
lexemes do not prove execution, numerical correctness, or semantic equivalence.
JSON schemas remain the authority for record shape; this module owns only the
bounded extraction and diagnostic rules below, not downstream gate decisions.
"""

import hashlib
import re

from sas_re.evidence import byte_lines, citation, validate_scope
from sas_re.safeio import EvidenceError, secure_read


NAME = r"[A-Za-z_][A-Za-z0-9_]{0,31}"
NUMBER = re.compile(r"[+-]?[0-9]+(?:\.[0-9]+)?\Z", re.ASCII)
READ = re.compile(
    rf"NOTE: There were ([0-9]+) observations read from the data set (WORK\.{NAME})\.", re.ASCII
)
OUTPUT = re.compile(
    rf"NOTE: The data set (WORK\.{NAME}) has ([0-9]+) observations and ([0-9]+) variables\.",
    re.ASCII,
)
TIME = re.compile(r"(real time|cpu time) ([0-9]+(?:\.[0-9]+)?) seconds", re.ASCII)
HEADERS = frozenset(
    {
        "NOTE: DATA statement used (Total process time):",
        "NOTE: PROCEDURE SORT used (Total process time):",
        "NOTE: PROCEDURE SQL used (Total process time):",
    }
)


def extract_observations(
    scope: dict, inventory: dict, profile: dict, operation_anchors: dict
) -> tuple[list[dict], list[dict]]:
    """Return cited observation facts and diagnostic locations for the composer.

    Reads authorized evidence and checks its inventoried hashes without writing
    files or executing SAS. The caller supplies schema-conforming records and
    owns fact IDs and downstream gate decisions. Every nonblank LOG/LST line
    must have exactly one binding; missing or overlapping coverage yields issues.

    Args:
        scope: Authorized evidence roots and scope used for reads and citations.
        inventory: File identities and explicit log/source associations.
        profile: LOG/LST bindings with one-based inclusive line ranges and,
            for listings, fixed-width column layouts.
        operation_anchors: Operations keyed by (file key, original source byte
            start), never decoded-text offsets or guessed filenames.

    Returns:
        A pair of lists: facts without IDs, carrying citations and uninterpreted
        value lexemes, and issues carrying file/line locations and contradiction
        flags. Returned observations remain semantically unverified.

    Raises:
        EvidenceError: If scope or evidence access, identity, encoding,
            provenance, operation binding, or listing layout is refused.
            Unsupported content and incomplete coverage instead produce issues.
        UnicodeDecodeError: If bytes do not decode using the inventoried encoding.
    """
    roots = validate_scope(scope)
    files = {item["file_key"]: item for item in inventory["files"]}
    associations = {a["association_id"]: a for a in inventory["log_associations"]}
    facts, issues = [], []
    loaded, covered = {}, {}

    def issue(code, key, start, end=None, contradiction=False):
        issues.append(
            {
                "code": code,
                "file_key": key,
                "line_start": start,
                "line_end": end if end is not None else start,
                "contradiction": contradiction,
            }
        )

    def lines_for(key):
        if key not in loaded:
            item = files[key]
            if item["encoding"] not in {"utf-8", "ascii"}:
                raise EvidenceError("OBSERVATION_ENCODING_UNSUPPORTED", "BLOCKED")
            raw = secure_read(roots[item["root_id"]], item["path"])
            # Check original bytes before decoding or normalizing line endings.
            if hashlib.sha256(raw).hexdigest() != item["sha256"]:
                raise EvidenceError("STALE_SOURCE")
            loaded[key] = [line.decode(item["encoding"]).rstrip("\r\n") for line in byte_lines(raw)]
            covered[key] = set()
        return loaded[key]

    for kind, bindings in (("LOG", profile["log_bindings"]), ("LST", profile["lst_bindings"])):
        for binding in bindings:
            association = associations.get(binding["association_id"])
            if association is None:
                raise EvidenceError("MISSING_LOG_PROVENANCE", "BLOCKED")
            key = association["log_file_key"]
            if key not in files or files[key]["kind"] != kind:
                raise EvidenceError("OBSERVATION_KIND_MISMATCH")
            # An association must also cover the explicitly anchored operation.
            operation = operation_anchors.get(
                (binding["operation_file_key"], binding["operation_start"])
            )
            if (
                operation is None
                or binding["operation_file_key"] not in association["source_file_keys"]
            ):
                raise EvidenceError("OBSERVATION_STEP_MISMATCH", "BLOCKED")
            lines = lines_for(key)
            start, end = binding["start_line"], binding["end_line"]
            if not 1 <= start <= end <= len(lines):
                raise EvidenceError("OBSERVATION_RANGE_INVALID")
            segment = set(range(start, end + 1))
            if segment & covered[key]:
                issue("OVERLAPPING_OBSERVATION_BINDING", key, start, end)
            covered[key].update(segment)
            base = {
                "module_id": files[key]["module_id"],
                "run_id": inventory["run_id"],
                "attempt_id": inventory["attempt_id"],
                "association_id": binding["association_id"],
                "execution_id": association["execution_id"],
                "source_operation_ids": [operation["operation_id"]],
                "classification": "OBSERVATION",
                "semantic_verification": "UNVERIFIABLE",
            }

            def add(
                line, metric, lexeme, unit, dataset=None, row=None, column=None, cell_kind=None
            ):
                facts.append(
                    {
                        **base,
                        "log_citation": citation(scope, inventory, key, line, line),
                        "metric": metric,
                        "value_lexeme": lexeme,
                        "unit": unit,
                        "dataset": dataset,
                        "row": row,
                        "column": column,
                        "cell_kind": cell_kind,
                    }
                )

            if not binding["complete"]:
                issue("INCOMPLETE_OBSERVATION_SEGMENT", key, start, end)
            if kind == "LOG":
                seen = {}
                headers = []
                expected_header = {
                    "DATA_STEP": "NOTE: DATA statement used (Total process time):",
                    "PROC_SORT": "NOTE: PROCEDURE SORT used (Total process time):",
                    "PROC_SQL": "NOTE: PROCEDURE SQL used (Total process time):",
                }.get(operation["kind"])
                for line_no in range(start, end + 1):
                    line = lines[line_no - 1].strip()
                    if not line:
                        continue
                    if line in HEADERS:
                        headers.append(line_no)
                        if line != expected_header:
                            issue("LOG_STEP_HEADER_CONTRADICTION", key, line_no, contradiction=True)
                        continue
                    read, output, time = (
                        READ.fullmatch(line),
                        OUTPUT.fullmatch(line),
                        TIME.fullmatch(line),
                    )
                    # Bound lexical measurements without converting their values.
                    numeric_tokens = (
                        [read[1]]
                        if read
                        else [output[2], output[3]]
                        if output
                        else [time[2]]
                        if time
                        else []
                    )
                    if any(len(token) > 128 for token in numeric_tokens):
                        issue("OBSERVATION_NUMERIC_LIMIT", key, line_no)
                        continue
                    if read:
                        add(line_no, "READ_ROWS", read[1], "rows", read[2].lower())
                        token = ("READ_ROWS", read[2].lower())
                    elif output:
                        add(line_no, "OUTPUT_ROWS", output[2], "rows", output[1].lower())
                        add(line_no, "OUTPUT_COLUMNS", output[3], "columns", output[1].lower())
                        token = ("OUTPUT_ROWS", output[1].lower())
                    elif time:
                        metric = "ELAPSED_SECONDS" if time[1] == "real time" else "CPU_SECONDS"
                        add(line_no, metric, time[2], "seconds")
                        token = (metric, None)
                    elif line.startswith("WARNING:"):
                        add(line_no, "WARNING_COUNT", "1", "count")
                        continue
                    elif line.startswith("ERROR:"):
                        issue("LOG_ERROR", key, line_no, contradiction=True)
                        continue
                    else:
                        issue("UNSUPPORTED_LOG_LINE", key, line_no)
                        continue
                    if token in seen:
                        issue("AMBIGUOUS_LOG_METRIC", key, seen[token], line_no)
                    seen[token] = line_no
                if not ({"OUTPUT_ROWS", "ELAPSED_SECONDS", "CPU_SECONDS"} <= {t[0] for t in seen}):
                    issue("INCOMPLETE_LOG_METRICS", key, start, end)
                if len(headers) > 1:
                    issue("AMBIGUOUS_LOG_STEP_HEADERS", key, headers[0], headers[-1])
            else:
                header = binding["header_line"]
                first, last = binding["data_start_line"], binding["data_end_line"]
                if not start < header < first <= last <= end:
                    raise EvidenceError("LST_LAYOUT_INVALID")
                columns = binding["columns"]
                if len({column["name"].lower() for column in columns}) != len(columns):
                    raise EvidenceError("LST_COLUMN_NAME_AMBIGUOUS")
                occupied = set()
                for column in columns:
                    lo, hi = column["start"], column["end"]
                    if not 1 <= lo <= hi <= 4096 or set(range(lo, hi + 1)) & occupied:
                        raise EvidenceError("LST_LAYOUT_INVALID")
                    occupied.update(range(lo, hi + 1))
                if lines[start - 1] != binding["title"]:
                    issue("LST_TITLE_MISMATCH", key, start)
                for column in columns:
                    lo, hi = column["start"], column["end"]
                    if lines[header - 1][lo - 1 : hi].strip() != column["name"]:
                        issue("LST_HEADER_MISMATCH", key, header)
                for line_no in range(start + 1, end + 1):
                    line = lines[line_no - 1]
                    if line_no != header and not first <= line_no <= last:
                        if line.strip():
                            issue("UNSUPPORTED_LST_LAYOUT", key, line_no)
                        continue
                    if any(char != " " and idx not in occupied for idx, char in enumerate(line, 1)):
                        issue("UNSUPPORTED_LST_LAYOUT", key, line_no)
                    if line_no == header:
                        continue
                    for column in columns:
                        lo, hi = column["start"], column["end"]
                        if len(line) < hi:
                            issue("TRUNCATED_LST_ROW", key, line_no)
                            continue
                        # Retain fixed-width spaces in facts, including blank cells.
                        raw = line[lo - 1 : hi]
                        value = raw.strip()
                        cell_kind = (
                            "BLANK"
                            if raw == " " * len(raw)
                            else "MISSING"
                            if value == "."
                            else "NUMBER"
                        )
                        if cell_kind == "NUMBER" and not NUMBER.fullmatch(value):
                            issue("UNSUPPORTED_LST_CELL", key, line_no)
                            continue
                        add(
                            line_no,
                            "LST_CELL",
                            raw,
                            "none",
                            row=line_no - first + 1,
                            column=column["name"],
                            cell_kind=cell_kind,
                        )

    # An explicit source association is necessary but is not a step binding.
    # Include files with no bindings so their nonblank evidence cannot be skipped.
    for key, item in files.items():
        if item["kind"] not in {"LOG", "LST"}:
            continue
        lines = lines_for(key)
        for line_no, line in enumerate(lines, 1):
            if line.strip() and line_no not in covered[key]:
                issue("UNBOUND_OBSERVATION_LINE", key, line_no)
        if not lines:
            # A locationless empty file is still a concrete identity-level blocker.
            issue("EMPTY_OBSERVATION_FILE", key, 0, 0)
    return facts, issues
