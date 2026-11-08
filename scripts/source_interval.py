"""Bounded, declaration-only inventory between selected source operations."""

from hashlib import sha256
import re

from sas_re.sas_subset import _Cursor, _Source, _Syntax, _frames
from source_rules import character_literal


_DATASET = r"(work) \. ([a-z_][a-z0-9_]{0,31})(?= |$)"


def dataset_refs(pattern, text):
    return [".".join(match.groups()) for match in re.finditer(pattern + _DATASET, text)]


_NAME = r"[a-z_][a-z0-9_]{0,31}"
_TABLE = r"work \. " + _NAME
_GROUPED = re.compile(
    rf"create table ({_TABLE}) as select id , count \( \* \) as duplicate_count "
    rf"from ({_TABLE}) group by id having count \( \* \) > 1"
)
_SCALAR = re.compile(rf"select (.+) into (.+) from ({_TABLE})")
_AGGREGATES = {
    "count ( * )": "COUNT(*)",
    "count ( distinct id )": "COUNT(DISTINCT id)",
    "sum ( case when missing ( id ) then 1 else 0 end )":
        "SUM(CASE WHEN MISSING(id) THEN 1 ELSE 0 END)",
}
_GATE = re.compile(rf"% if & ({_NAME}) (=|ne) (0|& {_NAME}) % then "
                   rf"% abort_run \( (.+) \)")
_FLAG = re.compile(rf"% if % upcase \( & ({_NAME}) \) = y % then % do")


def recover_sql_gates(frames, findings, start):
    """Annotate existing records with declaration facts, never resolved values."""
    by_start = {item["span"]["start"] - start: item for item in findings}
    producers = {}
    grouped = {}
    in_sql = False
    depth = 0
    pending_guard = None
    pending_gate = None
    for frame in frames:
        if frame["comment"] and not frame["issues"]:
            continue
        item = by_start.get(frame["start"])
        tokens = frame["tokens"]
        words = [t.lower if t.kind != "string" else "<literal>" for t in tokens]
        text = " ".join(words)
        codes = {issue["code"] for issue in frame["issues"]}
        if words[:2] == ["proc", "sql"]:
            producers.clear()
            grouped.clear()
            in_sql = not codes and text in {"proc sql", "proc sql noprint"} and not depth
            continue
        if not codes and text == "quit":
            in_sql = False
            continue
        if in_sql:
            group = _GROUPED.fullmatch(text) if not codes else None
            scalar = _SCALAR.fullmatch(text) if codes <= {"UNSUPPORTED_TOKEN"} else None
            if group and item:
                output, _ = group.groups()
                item["sql_declaration"] = {
                    "kind": "DUPLICATE_GROUP_SIZES",
                    "projection": ["id", "COUNT(*) AS duplicate_count"],
                    "group_by": "id", "having": "COUNT(*) > 1",
                }
                grouped[output] = None if output in grouped else item["span"]["start"]
                continue
            if scalar and item:
                expressions, targets, table = scalar.groups()
                expressions = expressions.split(" , ")
                targets = [re.fullmatch(rf": ({_NAME}) trimmed", target)
                           for target in targets.split(" , ")]
                if (len(expressions) == len(targets) and all(targets)
                        and all(expr in _AGGREGATES for expr in expressions)):
                    names = [target[1] for target in targets]
                    if len(set(names)) == len(names):
                        declaration = {
                            "kind": "SCALAR_INTO",
                            "bindings": [{"expression": _AGGREGATES[expr], "target": name,
                                          "trimmed": True}
                                         for expr, name in zip(expressions, names)],
                        }
                        if grouped.get(table) is not None and expressions == ["count ( * )"]:
                            declaration["kind"] = "DUPLICATE_GROUP_COUNT"
                            declaration["group_query_start"] = grouped[table]
                        item["sql_declaration"] = declaration
                        for name in names:
                            # Repeated producers leave the reference ambiguous.
                            producers[name] = (None if name in producers
                                               else item["span"]["start"])
                        continue
            # An unsupported SQL statement may write a target or replace a table.
            producers.clear()
            grouped.clear()
            if words[:1] in (["proc"], ["%"], ["run"]):
                in_sql = False
            else:
                continue

        adjacent_macros = all(
            i + 1 < len(tokens) and token.end == tokens[i + 1].start
            for i, token in enumerate(tokens) if token.text in {"%", "&"}
        )
        if not codes and adjacent_macros and text == "% end" and depth:
            depth -= 1
            if depth == 0 and pending_guard and pending_gate:
                guard_item, guard_declaration = pending_guard
                gate_item, gate_declaration = pending_gate
                guard_item["gate_declaration"] = guard_declaration
                gate_declaration["guard_start"] = guard_item["span"]["start"]
                gate_item["gate_declaration"] = gate_declaration
            pending_guard = pending_gate = None
            continue

        if any(pair == ("%", "do") for pair in zip(words, words[1:])):
            flag = _FLAG.fullmatch(text) if not codes and adjacent_macros and not depth else None
            # Keyword normalization must not change the case-sensitive operand.
            if flag and tokens[words.index("=") + 1].text != "Y":
                flag = None
            depth += 1
            pending_guard = (item, {
                "variable": flag[1], "transform": "UPCASE", "operator": "=",
                "operand": {"literal": "Y"}, "action": "GUARD",
            }) if flag and item else None
            pending_gate = None
            continue

        gate = _GATE.fullmatch(text) if not codes and adjacent_macros else None
        if gate and item and re.fullmatch(
            r"(?:[a-z0-9_=.<>+/-]+|& [a-z_][a-z0-9_]*)(?: (?:[a-z0-9_=.<>+/-]+|& [a-z_][a-z0-9_]*))*",
            gate[4],
        ):
            variable, operator, operand, _ = gate.groups()
            reference = operand[2:] if operand.startswith("& ") else None
            declaration = {
                "variable": variable, "operator": operator.upper(),
                "operand": {"variable": reference} if reference else {"literal": operand},
                "action": "ABORT_REQUEST",
                "into_sources": {name: producers[name] for name in (variable, reference)
                                 if producers.get(name) is not None},
            }
            if not depth:
                item["gate_declaration"] = declaration
            elif depth == 1 and pending_guard and not pending_gate:
                pending_gate = (item, declaration)
            else:
                pending_guard = pending_gate = None
        else:
            if depth:
                pending_guard = pending_gate = None
            if words[:1] == ["%"] and words[:2] != ["%", "assert_step"]:
                producers.clear()


def inspect_logistic(raw, first_line, start, max_bytes):
    """Recognize only the bounded ODS / LOGISTIC / status-check sequence."""
    if len(raw) > max_bytes:
        return None, ["SPAN_SIZE_LIMIT"]

    try:
        source = _Source(raw, "logistic")
        frames = [frame for frame in _frames(source) if not frame["comment"] or frame["issues"]]
        if len(frames) != 8 or any(frame["issues"] for frame in frames):
            raise _Syntax("LOGISTIC_SEQUENCE_UNSUPPORTED")
        ods, proc, classes, model, output, run, check, close = frames

        def cursor(frame, *prefix):
            c = _Cursor(frame["tokens"], source)
            for token in prefix:
                c.take(token)
            return c

        def work_table(c):
            c.take("work")
            c.take(".")
            return "work." + c.name()

        def span(frame, last=None, include_newline=False):
            end = (last or frame)["end"]
            if include_newline:
                newline = re.match(r"[ \t]*(?:\r\n|\r|\n)", source.text[end:])
                if newline:
                    end += newline.end()
            location = source.span(frame["start"], end)
            a, b = location["start"], location["end"]
            return {
                "start": start + a, "end": start + b,
                "line_start": first_line + location["line_start"] - 1,
                "line_end": first_line + location["line_end"] - 1,
                "sha256": sha256(raw[a:b]).hexdigest(),
            }

        c = cursor(ods, "ods", "output")
        destinations = {}
        while c.peek():
            table = c.name()
            if table in destinations:
                raise _Syntax("LOGISTIC_ODS_TARGETS_UNSUPPORTED")
            c.take("=")
            destinations[table] = work_table(c)
        if set(destinations) != {"parameterestimates", "fitstatistics", "association",
                                 "classlevelinfo", "convergencestatus"}:
            raise _Syntax("LOGISTIC_ODS_TARGETS_UNSUPPORTED")

        c = cursor(proc, "proc", "logistic", "data", "=")
        input_table = work_table(c)
        c.take("descending")
        c.finish()

        c = cursor(classes, "class")
        levels = []
        while not c.accept("/"):
            variable = c.name()
            c.take("(")
            c.take("ref")
            c.take("=")
            reference = character_literal(c)
            if any(mark in reference for mark in "%&"):
                raise _Syntax("LOGISTIC_DYNAMIC_REFERENCE_UNSUPPORTED")
            c.take(")")
            levels.append({"variable": variable, "reference": reference})
        c.take("param")
        c.take("=")
        c.take("ref")
        c.finish()

        c = cursor(model, "model")
        response = c.name()
        c.take("=")
        predictors = []
        while c.peek():
            predictors.append(c.name())
        class_names = {level["variable"] for level in levels}
        if (len(levels) != 5 or len(class_names) != 5 or len(predictors) != 17
                or len(set(predictors)) != 17 or not class_names <= set(predictors)
                or response in predictors):
            raise _Syntax("LOGISTIC_TERMS_UNSUPPORTED")

        c = cursor(output, "output", "out", "=")
        output_table = work_table(c)
        c.take("xbeta")
        c.take("=")
        eta = c.name()
        c.take("predicted")
        c.take("=")
        probability = c.name()
        c.finish()
        if len({eta, probability, response, *predictors}) != 20:
            raise _Syntax("LOGISTIC_OUTPUT_COLUMNS_AMBIGUOUS")
        if len({input_table, output_table, *destinations.values()}) != 7:
            raise _Syntax("LOGISTIC_DATASETS_AMBIGUOUS")

        cursor(run, "run").finish()
        cursor(close, "ods", "output", "close").finish()
        c = cursor(check, "%", "assert_step", "(", "step_name", "=")
        if check["tokens"][0].end != check["tokens"][1].start:
            raise _Syntax("LOGISTIC_STEP_CHECK_UNSUPPORTED")
        label_start = c.i
        while c.peek() and not c.peek(")"):
            c.name()
        if c.i == label_start:
            raise _Syntax("LOGISTIC_STEP_CHECK_UNSUPPORTED")
        c.take(")")
        c.finish()
    except UnicodeDecodeError:
        return None, ["SPAN_NOT_UTF8"]
    except _Syntax as error:
        return None, [error.code if error.code != "UNSUPPORTED_SYNTAX" else "LOGISTIC_SYNTAX_UNSUPPORTED"]

    return {
        "kind": "PROC_LOGISTIC",
        "span": span(proc, run, include_newline=True),
        "input": input_table,
        "header": {"span": span(proc), "options": ["DESCENDING"]},
        "class": {"span": span(classes), "parameterization": "REF", "levels": levels},
        "model": {"span": span(model), "response": response, "predictors": predictors,
                  "non_class_predictors": [name for name in predictors if name not in class_names],
                  "options": []},
        "output": output_table,
        "score_columns": {"span": span(output), "xbeta": eta, "predicted": probability},
        "ods_output": {"span": span(ods), "datasets": destinations, "close_span": span(close)},
        "step_check": {"span": span(check), "macro": "assert_step", "effects": "UNRESOLVED"},
        "execution_verification": "EXECUTION_UNVERIFIED",
    }, []


def inventory(raw, start, end, first_line, shared, max_bytes, recover_sql=False):
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

        if recover_sql:
            recover_sql_gates(frames, findings, start)

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
