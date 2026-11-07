"""Bounded, declaration-only inventory between selected source operations."""

from hashlib import sha256
import re

from sas_re.sas_subset import _Source, _Syntax, _frames


_DATASET = r"(work) \. ([a-z_][a-z0-9_]{0,31})(?= |$)"


def dataset_refs(pattern, text):
    return [".".join(match.groups()) for match in re.finditer(pattern + _DATASET, text)]


def inventory(raw, start, end, first_line, shared, max_bytes):
    span = raw[start:end]
    findings = []
    status = "INSPECTED"

    def record(location, **effects):
        a, b = location["start"], location["end"]
        findings.append({
            "span": {
                "start": start + a, "end": start + b,
                "line_start": first_line + location["line_start"] - 1,
                "line_end": first_line + location["line_end"] - 1,
                "sha256": sha256(span[a:b]).hexdigest(),
            },
            **effects,
        })

    try:
        if len(span) > max_bytes:
            raise _Syntax("INTERVAL_SIZE_LIMIT")
        source = _Source(span, "interval")
        frames = _frames(source)
    except (UnicodeDecodeError, _Syntax) as error:
        status = "UNAVAILABLE"
        if span:
            # Count original newline sequences without decoding or parsing the interval.
            line_count = sum(1 for _ in re.finditer(rb"\r\n|\r|\n", span))
            record({"start": 0, "end": len(span), "line_start": 1,
                    "line_end": line_count + (not span.endswith((b"\r", b"\n")))},
                   unknown_effects=[getattr(error, "code", "INTERVAL_NOT_UTF8")])
    else:
        procedure = None
        for frame in frames:
            location = source.span(frame["start"], frame["end"])
            codes = {issue["code"] for issue in frame["issues"]}
            # SELECT INTO uses colons outside the expression lexer's profile.
            sql_into = (procedure == "sql" and codes == {"UNSUPPORTED_TOKEN"}
                        and any(token.text == ":" for token in frame["tokens"])
                        and all(token.kind != "symbol" or token.text in ". , ( ) = + - * / < > ^ % & <= >= ^= :".split()
                                for token in frame["tokens"]))
            if codes and not sql_into:
                procedure = None
                record(location, unknown_effects=sorted(codes))
                continue
            if frame["comment"]:
                continue
            tokens = frame["tokens"]
            words = [token.lower if token.kind != "string" else "<literal>" for token in tokens]
            text = " ".join(words)
            # Quoted text can contain macro triggers in SAS. Keep it unresolved.
            macro = any(token.text in {"%", "&"} or
                        (token.kind == "string" and token.text.startswith('"')
                         and any(marker in token.text for marker in "%&"))
                        for token in tokens)
            if macro:
                calls = sorted({words[i + 1] for i, word in enumerate(words[:-1])
                                if word == "%" and tokens[i + 1].kind == "name"
                                and words[i + 1] not in {"if", "then", "do", "end", "else"}})
                gates = []
                if any(a == "%" and b in {"if", "else", "then", "do", "end"}
                       for a, b in zip(words, words[1:])):
                    gates.append("CONDITIONAL_MACRO_CONTROL")
                if any(name in {"abort", "abort_run"} for name in calls):
                    gates.append("POTENTIAL_ABORT")
                record(location, macro_invocations=calls, control_gates=gates,
                       unknown_effects=["MACRO_DEPENDENT_EFFECTS"])
                procedure = None
                continue

            reads, writes, ods_outputs = [], [], []
            unknown = sorted(codes)
            if words[0] == "proc":
                procedure = words[1] if len(words) > 1 else None
                if procedure in {"print", "means", "freq", "sort"}:
                    reads = dataset_refs(r"\bdata = ", text)
                    writes = dataset_refs(r"\bout = ", text)
                    if not reads:
                        unknown.append("PROCEDURE_INPUT_UNRESOLVED")
                    if procedure == "sort" and not writes and reads:
                        if "out" in words:
                            unknown.append("SORT_OUTPUT_UNRESOLVED")
                        else:
                            writes = reads.copy()
                elif text not in {"proc sql", "proc sql noprint"}:
                    unknown.append("PROCEDURE_EFFECTS_UNRESOLVED")
            elif words[0] == "data":
                procedure = None
                writes = dataset_refs(r"^data ", text)
                if not re.fullmatch(r"data " + _DATASET, text):
                    unknown.append("DATA_OUTPUTS_UNRESOLVED")
            elif words[0] == "set":
                reads = dataset_refs(r"(?:^set | )", text)
                if not re.fullmatch(r"set " + _DATASET, text):
                    unknown.append("SET_INPUTS_UNRESOLVED")
            elif words[:2] == ["ods", "output"]:
                ods_outputs = dataset_refs(r" = ", text)
                if not ods_outputs and text != "ods output close":
                    unknown.append("ODS_OUTPUTS_UNRESOLVED")
                elif ods_outputs and not re.fullmatch(
                        r"ods output(?: [a-z_][a-z0-9_]* = " + _DATASET + r")+", text):
                    unknown.append("ODS_OUTPUTS_UNRESOLVED")
            elif procedure == "sql" and (words[0] == "select" or words[:2] == ["create", "table"]):
                reads = dataset_refs(r"\b(?:from|join) ", text)
                writes = dataset_refs(r"^create table ", text)
                # These references alone do not account for SQL expressions,
                # INTO assignments, views or other effects of the statement.
                unknown.append("SQL_EFFECTS_NOT_FULLY_CLASSIFIED")
            elif text in {"run", "quit"}:
                procedure = None
            elif not (words[0] == "title" or (procedure, words[0]) in
                      {("means", "var"), ("freq", "tables"), ("sort", "by")}):
                unknown.append("STATEMENT_EFFECTS_UNRESOLVED")
            if reads or writes or ods_outputs or unknown:
                record(location, reads=reads, writes=writes, ods_outputs=ods_outputs, unknown_effects=unknown)

    reads = {name for item in findings for name in item.get("reads", [])}
    outputs = {name for item in findings for field in ("writes", "ods_outputs") for name in item.get(field, [])}
    return {
        "status": status,
        "sha256": sha256(span).hexdigest(),
        "shared_dataset": shared,
        "direct_reads": sorted(reads),
        "other_outputs": sorted(outputs - {shared}),
        "shared_writer_identified": shared in outputs if shared and status == "INSPECTED" else None,
        "sort_reachability": "UNESTABLISHED",
        "findings": findings,
    }
