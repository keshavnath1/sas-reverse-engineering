"""Closed, deterministic synthetic SAS syntax profile; never executes source.

The result is transient parser data for the canonical graph builder, not a second
persisted graph. Byte offsets are half-open offsets into original UTF-8 bytes.
Parsing a construct is not semantic acceptance: callers retain UNVERIFIABLE.
"""

from __future__ import annotations

from bisect import bisect_right
from array import array
from dataclasses import dataclass
from fractions import Fraction
import re
from typing import Callable


PROFILE = "sas94-synthetic-v1"
MAX_LINES = 10_000
MAX_OPERATIONS = 100
MAX_FILES = 20
MAX_INCLUDE_DEPTH = 5
MAX_TOKENS = 100_000
MAX_EXPRESSION_DEPTH = 64
MAX_EXPRESSION_NODES = 1_024
MAX_STATEMENTS = 10_000
MAX_SOURCE_BYTES = 8 * 1024 * 1024
_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,31}\Z")
_DECIMAL = re.compile(r"[0-9]+(?:\.[0-9]+)?\Z")
IncludeLoader = Callable[[str, str], tuple[str, bytes]]


@dataclass(frozen=True)
class _Token:
    text: str
    start: int
    end: int
    kind: str

    @property
    def lower(self) -> str:
        return self.text.lower()


class _Syntax(Exception):
    def __init__(self, code: str = "UNSUPPORTED_SYNTAX", message: str = "Outside the closed pilot grammar"):
        self.code, self.message = code, message


class _Source:
    def __init__(self, data: bytes, file_key: str):
        self.data, self.file_key = data, file_key
        self.text = data.decode("utf-8", errors="strict")
        if data.isascii():
            self.offsets = range(len(data) + 1)
        else:
            self.offsets = array("I", [0])
            for char in self.text:
                self.offsets.append(self.offsets[-1] + len(char.encode("utf-8")))
        self.lines = [0]
        self.lines.extend(match.end() for match in re.finditer(rb"\r\n|\r|\n", data))

    def span(self, start: int, end: int) -> dict:
        a, b = self.offsets[start], self.offsets[end]
        return {"file_key": self.file_key, "start": a, "end": b,
                "line_start": bisect_right(self.lines, a),
                "line_end": bisect_right(self.lines, max(a, b - 1))}


def _issue(source: _Source, code: str, message: str, start: int, end: int) -> dict:
    return {"code": code, "message": message, "span": source.span(start, end)}


def _frames(source: _Source) -> list[dict]:
    """Account for every non-whitespace region, including malformed tails."""
    text = source.text
    result, i = [], 0
    while i < len(text):
        while i < len(text) and text[i] in " \t\r\n\f\v":
            i += 1
        if i == len(text):
            break
        if text.startswith("/*", i):
            # Leading standalone comments own their byte range. They must not
            # move the source anchor of the DATA/PROC header that follows.
            comment_start = i
            closing = text.find("*/", i + 2)
            end = len(text) if closing < 0 else closing + 2
            comment_issues = []
            if closing < 0:
                comment_issues.append(_issue(source, "UNCLOSED_COMMENT", "Unclosed block comment", i, end))
            if "/*" in text[i + 2:closing if closing >= 0 else len(text)]:
                comment_issues.append(_issue(source, "NESTED_COMMENT", "Nested block comments are unsupported", i, end))
            result.append({"start": comment_start, "end": end, "tokens": [],
                           "comment": True, "issues": comment_issues})
            i = end
            if len(result) > MAX_STATEMENTS:
                raise _Syntax("STATEMENT_LIMIT", "Statement count exceeds the bounded profile")
            continue
        start, quote, block, problems = i, None, False, []
        comment = text.startswith("%*", i) or text[i] == "*"
        macro_comment = text.startswith("%*", i)
        while i < len(text):
            ch = text[i]
            if block:
                if text.startswith("/*", i):
                    problems.append(("NESTED_COMMENT", "Nested block comments are unsupported"))
                    i += 2
                elif text.startswith("*/", i):
                    block, i = False, i + 2
                else:
                    i += 1
            elif quote:
                if comment and ch == ";":
                    problems.append(("AMBIGUOUS_COMMENT_BOUNDARY", "Semicolon inside a quoted comment is outside the frozen comment profile"))
                if ch == quote:
                    if i + 1 < len(text) and text[i + 1] == quote:
                        i += 2
                    else:
                        quote, i = None, i + 1
                else:
                    i += 1
            elif ch in "\"'":
                quote, i = ch, i + 1
            elif not comment and text.startswith("/*", i):
                block, i = True, i + 2
            elif ch == ";":
                i += 1
                break
            else:
                i += 1
        terminated = i > start and text[i - 1] == ";" and not quote and not block
        raw = text[start:i]
        if quote:
            problems.append(("UNCLOSED_QUOTE", "Unclosed quoted token or unbalanced comment quote"))
        if block:
            problems.append(("UNCLOSED_COMMENT", "Unclosed block comment"))
        if comment and not macro_comment and any(c in raw for c in "%&"):
            problems.append(("MACRO_BEARING_COMMENT", "Statement comments with macro triggers cannot be discarded"))
        tokens, token_errors = ([], []) if comment else _tokens(source, start, i)
        problems.extend(token_errors)
        if not terminated and tokens and not quote and not block:
            problems.append(("MISSING_SEMICOLON", "Nonempty statement is not semicolon terminated"))
        if comment and not terminated and not quote:
            problems.append(("MISSING_SEMICOLON", "Comment statement is not semicolon terminated"))
        result.append({"start": start, "end": i, "tokens": tokens,
                       "comment": comment or not tokens,
                       "issues": [_issue(source, code, message, start, i) for code, message in problems]})
        if len(result) > MAX_STATEMENTS:
            raise _Syntax("STATEMENT_LIMIT", "Statement count exceeds the bounded profile")
    return result


def _tokens(source: _Source, start: int, end: int) -> tuple[list[_Token], list[tuple[str, str]]]:
    text, out, issues, i = source.text, [], [], start
    while i < end:
        ch = text[i]
        if ch in " \t\r\n\f\v" or ch == ";":
            i += 1
            continue
        if text.startswith("/*", i):
            closing = text.find("*/", i + 2, end)
            i = end if closing < 0 else closing + 2
            continue
        a = i
        if ch in "\"'":
            quote, i = ch, i + 1
            while i < end:
                if text[i] == quote:
                    if i + 1 < end and text[i + 1] == quote:
                        i += 2
                        continue
                    i += 1
                    break
                i += 1
            kind = "string"
        elif ch.isascii() and (ch.isalpha() or ch == "_"):
            i += 1
            while i < end and text[i].isascii() and (text[i].isalnum() or text[i] == "_"):
                i += 1
            kind = "name"
            if not _NAME.fullmatch(text[a:i]):
                issues.append(("INVALID_NAME", "Names must be ordinary ASCII identifiers of at most 32 characters"))
        elif ch.isascii() and ch.isdigit():
            i += 1
            while i < end and text[i].isascii() and text[i].isdigit():
                i += 1
            if i + 1 < end and text[i] == "." and text[i + 1].isascii() and text[i + 1].isdigit():
                i += 1
                while i < end and text[i].isascii() and text[i].isdigit():
                    i += 1
            kind = "number"
            if i - a > 128:
                issues.append(("NUMERIC_TOKEN_LIMIT", "Numeric literal exceeds the bounded spelling length"))
        elif text[i:i + 2] in ("<=", ">=", "^="):
            i += 2
            kind = "symbol"
        else:
            i += 1
            kind = "symbol"
            if ch not in ".,()=+-*/<>^%&":
                issues.append(("UNSUPPORTED_TOKEN", "Token outside the lexical profile"))
        out.append(_Token(text[a:i], a, i, kind))
        if len(out) > MAX_TOKENS:
            raise _Syntax("TOKEN_LIMIT", "Token limit exceeded")
    return out, issues


class _Cursor:
    def __init__(self, tokens: list[_Token], source: _Source):
        self.tokens, self.source, self.i = tokens, source, 0
        self.expression_nodes = 0

    def peek(self, text: str | None = None) -> bool:
        return self.i < len(self.tokens) and (text is None or self.tokens[self.i].lower == text)

    def take(self, text: str | None = None) -> _Token:
        if not self.peek(text):
            raise _Syntax()
        token = self.tokens[self.i]
        self.i += 1
        return token

    def accept(self, text: str) -> bool:
        if self.peek(text):
            self.i += 1
            return True
        return False

    def name(self) -> str:
        token = self.take()
        if token.kind != "name" or not _NAME.fullmatch(token.text):
            raise _Syntax("INVALID_NAME", "Expected an ordinary identifier")
        return token.lower

    def finish(self) -> None:
        if self.peek():
            raise _Syntax()

    def span(self, a: int, b: int | None = None) -> dict:
        b = self.i if b is None else b
        return self.source.span(self.tokens[a].start, self.tokens[b - 1].end)


def _literal(cursor: _Cursor) -> dict:
    start = cursor.i
    sign = cursor.take().text if cursor.peek("+") or cursor.peek("-") else ""
    token = cursor.take()
    if token.text != "." and not _DECIMAL.fullmatch(token.text):
        raise _Syntax("UNSUPPORTED_NUMERIC_LITERAL", "Expected a decimal literal or ordinary numeric missing")
    if sign and token.text == ".":
        raise _Syntax("UNSUPPORTED_NUMERIC_LITERAL", "Signed missing markers are outside the profile")
    return {"kind": "literal", "lexeme": sign + token.text, "span": cursor.span(start)}


def _expression(cursor: _Cursor, qualified: bool = False, minimum: int = 0, depth: int = 0) -> dict:
    if depth == 0:
        cursor.expression_nodes = 0
    cursor.expression_nodes += 1
    if cursor.expression_nodes > MAX_EXPRESSION_NODES:
        raise _Syntax("EXPRESSION_LIMIT", "Expression node limit exceeded")
    if depth > MAX_EXPRESSION_DEPTH:
        raise _Syntax("EXPRESSION_LIMIT", "Expression nesting limit exceeded")
    start = cursor.i
    token = cursor.take()
    if token.text in ("+", "-"):
        left = {"kind": "unary", "operator": token.text,
                "operand": _expression(cursor, qualified, 30, depth + 1), "span": cursor.span(start)}
    elif token.text == "(":
        inside = _expression(cursor, qualified, depth=depth + 1)
        cursor.take(")")
        left = {"kind": "group", "expression": inside, "span": cursor.span(start)}
    elif token.kind == "number" or token.text == ".":
        left = {"kind": "literal", "lexeme": token.text, "span": cursor.span(start)}
    elif token.kind == "name":
        if not _NAME.fullmatch(token.text):
            raise _Syntax("INVALID_NAME", "Expression name exceeds the identifier profile")
        name = token.lower
        if qualified:
            cursor.take(".")
            name += "." + cursor.name()
        left = {"kind": "name", "name": name,
                "lexeme": cursor.source.text[token.start:cursor.tokens[cursor.i - 1].end],
                "span": cursor.span(start)}
    else:
        raise _Syntax("UNSUPPORTED_EXPRESSION", "Expression outside the numeric arithmetic grammar")
    while cursor.peek() and cursor.tokens[cursor.i].text in ("+", "-", "*", "/"):
        op = cursor.tokens[cursor.i].text
        priority = 10 if op in ("+", "-") else 20
        if priority < minimum:
            break
        cursor.take()
        right = _expression(cursor, qualified, priority + 1, depth + 1)
        cursor.expression_nodes += 1
        if cursor.expression_nodes > MAX_EXPRESSION_NODES:
            raise _Syntax("EXPRESSION_LIMIT", "Expression node limit exceeded")
        left = {"kind": "binary", "operator": op, "left": left, "right": right,
                "span": cursor.span(start)}
    if depth == 0:
        # Left-associative chains are shallow parser recursion but deep trees.
        # Bound the emitted tree too, before schema or graph traversal sees it.
        pending = [(left, 1)]
        while pending:
            node, level = pending.pop()
            if level > MAX_EXPRESSION_DEPTH:
                raise _Syntax("EXPRESSION_LIMIT", "Expression tree depth limit exceeded")
            for field in ("operand", "left", "right", "expression"):
                if field in node:
                    pending.append((node[field], level + 1))
    return left


def _condition(cursor: _Cursor, qualified: bool = False) -> dict:
    start = cursor.i
    if not qualified and (cursor.peek("first") or cursor.peek("last")):
        flag = cursor.take().lower
        cursor.take(".")
        key = cursor.name()
        return {"kind": "by_flag", "flag": flag, "key": key, "span": cursor.span(start)}
    token = cursor.take()
    if token.kind != "name" or not _NAME.fullmatch(token.text):
        raise _Syntax("UNSUPPORTED_CONDITION", "Condition must compare one numeric variable with a literal")
    name = token.lower
    if qualified:
        cursor.take(".")
        name += "." + cursor.name()
    left = {"kind": "name", "name": name,
            "lexeme": cursor.source.text[token.start:cursor.tokens[cursor.i - 1].end],
            "span": cursor.span(start)}
    operator = cursor.take().text
    if operator not in ("=", "^=", "<", "<=", ">", ">="):
        raise _Syntax("UNSUPPORTED_CONDITION", "Unsupported comparison operator")
    right = _literal(cursor)
    return {"kind": "comparison", "left": left, "operator": operator,
            "right": right, "span": cursor.span(start)}


def _numeric_issues(value: object) -> list[tuple[str, str, dict]]:
    """Conservative literal/divisor checks; input/intermediate proof stays unresolved."""
    found = []
    if isinstance(value, list):
        for item in value:
            found.extend(_numeric_issues(item))
    elif isinstance(value, dict):
        if value.get("kind") == "literal" and value["lexeme"] != ".":
            number = Fraction(value["lexeme"])
            if abs(number) > 2 ** 20 or number.denominator > 1024 or number.denominator & (number.denominator - 1):
                found.append(("NUMERIC_PROFILE", "Literal needs a numerical policy outside the exact dyadic profile", value["span"]))
        if value.get("kind") == "binary" and value.get("operator") == "/":
            denominator = value["right"]
            while denominator.get("kind") in ("group", "unary"):
                denominator = denominator.get("expression", denominator.get("operand"))
            if denominator.get("kind") != "literal" or denominator["lexeme"] == ".":
                valid = False
            else:
                number = abs(Fraction(denominator["lexeme"]))
                valid = bool(number) and not (number.numerator & (number.numerator - 1)) and not (number.denominator & (number.denominator - 1))
            if not valid:
                found.append(("NUMERIC_DIVISION_PROFILE", "Division requires a nonzero literal power-of-two divisor", value["span"]))
        for key, item in value.items():
            if key != "span":
                found.extend(_numeric_issues(item))
    return found


def _dataset(cursor: _Cursor, macros: dict, macro_facts: list) -> str:
    start = cursor.i

    def contiguous():
        if any(left.end != right.start for left, right in zip(cursor.tokens[start:cursor.i], cursor.tokens[start + 1:cursor.i])):
            raise _Syntax("UNSUPPORTED_DATASET_TOKEN", "Dataset names and macro substitutions must be contiguous tokens")

    prefix = ""
    if cursor.peek("work"):
        cursor.take("work")
        cursor.take(".")
        prefix = "work."
    if cursor.accept("&"):
        name = cursor.name()
        cursor.accept(".")
        binding = macros.get(name)
        if binding is None or binding.get("unresolved"):
            raise _Syntax("UNRESOLVED_MACRO", "Dataset token references an undefined literal macro binding")
        value = prefix + binding["value"].lower()
        if not re.fullmatch(r"work\.[A-Za-z_][A-Za-z0-9_]{0,31}", value):
            raise _Syntax("UNSUPPORTED_MACRO_SUBSTITUTION", "Macro binding does not produce one explicit WORK dataset")
        contiguous()
        macro_facts.append({"kind": "macro_use", "span": cursor.span(start),
                            "name": name, "value": binding["value"], "definition_span": binding["span"]})
        return value
    if not prefix:
        raise _Syntax("IMPLICIT_OR_EXTERNAL_DATASET", "Dataset must be an explicit WORK name")
    name = prefix + cursor.name()
    contiguous()
    return name


def _action(cursor: _Cursor, guard: dict | None = None) -> dict:
    start = cursor.i
    target = cursor.name()
    if cursor.accept("+"):
        expression = _expression(cursor)
        return {"kind": "sum", "span": cursor.span(start), "target": target,
                "expression": expression, "guard": guard}
    cursor.take("=")
    if cursor.peek("lag") or cursor.peek("lag2"):
        pos, name = cursor.i, cursor.take().lower
        cursor.take("(")
        arg_start = cursor.i
        argument = cursor.name()
        arg = {"kind": "name", "name": argument, "lexeme": cursor.tokens[arg_start].text,
               "span": cursor.span(arg_start)}
        cursor.take(")")
        expression = {"kind": "lag", "name": name, "argument": arg,
                      "queue_size": 1 if name == "lag" else 2, "span": cursor.span(pos)}
    else:
        expression = _expression(cursor)
    return {"kind": "assignment", "span": cursor.span(start), "target": target,
            "expression": expression, "guard": guard}


def _data_statement(cursor: _Cursor, macros: dict, macro_facts: list) -> dict:
    start = cursor.i
    if cursor.peek("set") or cursor.peek("merge"):
        mode = cursor.take().text.upper()
        inputs = []
        while cursor.peek():
            inputs.append(_dataset(cursor, macros, macro_facts))
        if len(inputs) not in ((1, 2) if mode == "SET" else (2,)):
            raise _Syntax("UNSUPPORTED_INPUT_COUNT", "SET accepts one or two inputs; MERGE exactly two")
        return {"kind": "input", "span": cursor.span(start), "mode": mode, "datasets": inputs}
    if cursor.accept("by"):
        keys = []
        while cursor.peek():
            keys.append(cursor.name())
        if (len(keys) not in (1, 2) or len(set(keys)) != len(keys)
                or set(keys) & {"descending", "notsorted", "groupformat"}):
            raise _Syntax("UNSUPPORTED_BY", "BY requires one or two distinct ascending numeric keys")
        return {"kind": "by", "span": cursor.span(start), "keys": keys, "ascending": True}
    if cursor.accept("retain"):
        target = cursor.name()
        initial = _literal(cursor)
        return {"kind": "retain", "span": cursor.span(start), "target": target, "initial": initial}
    if cursor.peek("keep") or cursor.peek("drop"):
        kind, names = cursor.take().lower, []
        while cursor.peek():
            names.append(cursor.name())
        if not names or len(set(names)) != len(names):
            raise _Syntax("UNSUPPORTED_COLUMN_LIST", "KEEP/DROP requires explicit distinct names")
        return {"kind": kind, "span": cursor.span(start), "names": names}
    if cursor.accept("if"):
        condition = _condition(cursor)
        if cursor.accept("then"):
            action = _action(cursor, condition)
            action["span"] = cursor.span(start)
            return action
        return {"kind": "subset_if", "span": cursor.span(start), "condition": condition}
    return _action(cursor)


def _sql_statement(cursor: _Cursor, macros: dict, macro_facts: list) -> tuple[str, dict]:
    start = cursor.i
    cursor.take("create")
    cursor.take("table")
    output = _dataset(cursor, macros, macro_facts)
    cursor.take("as")
    cursor.take("select")
    selected = []
    while True:
        expr = _expression(cursor, qualified=True)
        cursor.take("as")
        selected.append({"output": cursor.name(), "expression": expr})
        if not cursor.accept(","):
            break
    if len({item["output"] for item in selected}) != len(selected):
        raise _Syntax("DUPLICATE_OUTPUT_COLUMN", "SQL output aliases must be unique")
    cursor.take("from")
    dataset = _dataset(cursor, macros, macro_facts)
    cursor.take("as")
    inputs = [{"dataset": dataset, "alias": cursor.name()}]
    join = None
    if cursor.peek("inner") or cursor.peek("left"):
        kind = cursor.take().text.upper()
        cursor.take("join")
        dataset = _dataset(cursor, macros, macro_facts)
        cursor.take("as")
        inputs.append({"dataset": dataset, "alias": cursor.name()})
        if inputs[0]["alias"] == inputs[1]["alias"]:
            raise _Syntax("DUPLICATE_SQL_ALIAS", "SQL inputs require distinct aliases")
        cursor.take("on")
        left = _expression(cursor, qualified=True)
        cursor.take("=")
        right = _expression(cursor, qualified=True)
        if (left["kind"] != "name" or right["kind"] != "name"
                or {left["name"].split(".")[0], right["name"].split(".")[0]} != {x["alias"] for x in inputs}):
            raise _Syntax("UNSUPPORTED_JOIN_CONDITION", "ON requires one equality between the two input key columns")
        join = {"kind": kind, "left": left, "right": right}
    where = _condition(cursor, qualified=True) if cursor.accept("where") else None
    order = []
    if cursor.accept("order"):
        cursor.take("by")
        order.append(cursor.name())
        cursor.accept("asc")
        if cursor.accept(","):
            order.append(cursor.name())
            cursor.accept("asc")
        if len(set(order)) != len(order) or not set(order) <= {x["output"] for x in selected}:
            raise _Syntax("UNSUPPORTED_SQL_ORDER", "ORDER BY requires distinct selected output names")
    cursor.finish()
    aliases = {x["alias"] for x in inputs}

    def check_alias(value):
        if isinstance(value, dict):
            if value.get("kind") == "name" and value["name"].split(".")[0] not in aliases:
                raise _Syntax("UNKNOWN_SQL_ALIAS", "Expression references an undeclared SQL input alias")
            for item in value.values():
                check_alias(item)
        elif isinstance(value, list):
            for item in value:
                check_alias(item)

    check_alias(selected)
    check_alias(where)
    return output, {"kind": "sql", "span": cursor.span(start), "inputs": inputs,
                    "select": selected, "join": join, "where": where, "order_by": order}


class _Session:
    def __init__(self, macros: dict, loader: IncludeLoader | None):
        self.macros, self.loader = macros, loader
        self.operations, self.statements, self.issues = [], [], []
        self.visited: set[str] = set()
        self.line_count = 0
        self.token_count = 0
        self.outputs: set[str] = set()

    def add_issue(self, operation: dict, issue: dict):
        operation["issues"].append(issue)
        self.issues.append(issue)

    def poison_macros(self):
        # Unsupported macro processing or unread include content can change the
        # environment. Never keep using earlier bindings as if still resolved.
        for name, binding in list(self.macros.items()):
            self.macros[name] = {**binding, "unresolved": True}

    def operation(self, kind: str, source: _Source, frame: dict) -> dict:
        return {"kind": kind, "span": source.span(frame["start"], frame["end"]),
                "statements": [], "facts": [], "reads": [], "writes": [], "issues": []}

    def finish(self, operation: dict, source: _Source, start: int, end: int):
        operation["span"] = source.span(start, end)
        if operation["kind"] == "DATA_STEP":
            inputs = [f for f in operation["facts"] if f["kind"] == "input"]
            bys = [f for f in operation["facts"] if f["kind"] == "by"]
            if len(inputs) != 1:
                self.add_issue(operation, _issue(source, "INPUT_STATEMENT_COUNT", "DATA step requires exactly one SET or MERGE statement", start, end))
            if len(bys) > 1:
                self.add_issue(operation, _issue(source, "BY_STATEMENT_COUNT", "Only one BY declaration is supported", start, end))
            if len(inputs) == 1:
                inp = inputs[0]
                if any(operation["facts"].index(by) < operation["facts"].index(inp) for by in bys):
                    for by in bys:
                        if operation["facts"].index(by) < operation["facts"].index(inp):
                            self.add_issue(operation, {"code": "BY_PRECEDES_INPUT",
                                                       "message": "DATA-step BY must follow its SET or MERGE statement",
                                                       "span": by["span"]})
                if inp["mode"] == "MERGE" and (len(bys) != 1 or len(bys[0]["keys"]) != 1):
                    self.add_issue(operation, _issue(source, "MERGE_REQUIRES_BY", "MERGE requires one ascending numeric BY key", start, end))
                if inp["mode"] == "SET" and len(inp["datasets"]) == 2 and bys:
                    self.add_issue(operation, _issue(source, "INTERLEAVING_SET_UNSUPPORTED", "Multi-input SET with BY is outside the profile", start, end))
            keys = set(bys[0]["keys"]) if len(bys) == 1 else set()
            for fact in operation["facts"]:
                guard = fact.get("guard") or fact.get("condition")
                if guard and guard["kind"] == "by_flag" and guard["key"] not in keys:
                    self.add_issue(operation, {"code": "UNBOUND_BY_FLAG", "message": "FIRST/LAST flag has no supported BY key", "span": guard["span"]})
        for fact in operation["facts"]:
            for code, message, span in _numeric_issues(fact):
                self.add_issue(operation, {"code": code, "message": message, "span": span})
        for dataset in operation["writes"]:
            if dataset in self.outputs:
                self.add_issue(operation, _issue(source, "DATASET_OVERWRITE", "Dataset output names must be written once per scoped case", start, end))
            self.outputs.add(dataset)
        self.operations.append(operation)

    def include(self, source: _Source, frame: dict, cursor: _Cursor, stack: tuple[str, ...], statement: dict) -> tuple[str | None, bytes | None]:
        """Resolve one explicit literal include without gaining file authority."""
        token = cursor.take()
        cursor.finish()
        if token.kind != "string" or len(token.text) < 2 or token.text[-1] != token.text[0]:
            raise _Syntax("DYNAMIC_INCLUDE", "INCLUDE requires one quoted literal path")
        path = token.text[1:-1].replace(token.text[0] * 2, token.text[0])
        if (not path or len(path) > 4096 or len(path.split("/")) > 32
                or any(part in ("", ".", "..") or not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", part)
                       for part in path.split("/"))):
            raise _Syntax("UNSAFE_INCLUDE", "INCLUDE path is outside the safe relative-path profile")
        op = self.operation("INCLUDE", source, frame)
        op["statements"] = [statement]
        fact = {"kind": "include", "span": statement["span"], "path": path, "target_file_key": None}
        op["facts"] = [fact]
        statement["classification"] = "FACT"
        target, included = None, None
        try:
            if self.loader is None:
                raise _Syntax("UNRESOLVED_INCLUDE", "No authorized include mapping was supplied")
            if len(stack) >= MAX_INCLUDE_DEPTH:
                raise _Syntax("INCLUDE_DEPTH", "Include depth exceeds the profile")
            if len(self.visited) >= MAX_FILES:
                raise _Syntax("SOURCE_LIMIT", "Included file count exceeds the profile")
            target, included = self.loader(source.file_key, path)
            if not isinstance(target, str) or not isinstance(included, bytes):
                raise ValueError("invalid include response")
            if target in (*stack, source.file_key):
                raise _Syntax("INCLUDE_CYCLE", "Include cycle is unsupported")
            if target in self.visited:
                raise _Syntax("REPEATED_INCLUDE", "Repeated inclusion of a file is unsupported")
            fact["target_file_key"] = target
        except _Syntax as exc:
            self.add_issue(op, _issue(source, exc.code, exc.message, frame["start"], frame["end"]))
            self.poison_macros()
            included = None
        except (KeyError, ValueError, OSError):
            self.add_issue(op, _issue(source, "UNRESOLVED_INCLUDE", "Literal include has no readable authorized mapping", frame["start"], frame["end"]))
            self.poison_macros()
            included = None
        self.finish(op, source, frame["start"], frame["end"])
        return target, included

    def parse(self, data: bytes, file_key: str, stack: tuple[str, ...] = (), context: dict | None = None):
        state = context or {"active": None, "block_start": None, "owner_source": None, "owner_end": None,
                            "sort_input": None, "sort_output": None, "sort_keys": [], "sort_span": None}
        if len(data) > MAX_SOURCE_BYTES:
            span = {"file_key": file_key, "start": 0, "end": len(data), "line_start": 1,
                    "line_end": 1 + sum(m.end() < len(data) for m in re.finditer(rb"\r\n|\r|\n", data))}
            issue = {"code": "SOURCE_BYTE_LIMIT", "message": "Source exceeds the P1 per-file byte limit", "span": span}
            self.issues.append(issue)
            statement = {"span": span, "classification": "UNKNOWN"}
            self.statements.append(statement)
            self.operations.append({"kind": "UNKNOWN", "span": span, "statements": [statement],
                                    "facts": [], "reads": [], "writes": [], "issues": [issue]})
            return state
        try:
            source = _Source(data, file_key)
        except UnicodeDecodeError:
            span = {"file_key": file_key, "start": 0, "end": len(data), "line_start": 1,
                    "line_end": 1 + sum(m.end() < len(data) for m in re.finditer(rb"\r\n|\r|\n", data))}
            issue = {"code": "UNSUPPORTED_ENCODING", "message": "Only strict UTF-8/ASCII is supported", "span": span}
            self.issues.append(issue)
            self.operations.append({"kind": "UNKNOWN", "span": span, "statements": [{"span": span, "classification": "UNKNOWN"}], "facts": [], "reads": [], "writes": [], "issues": [issue]})
            self.statements.append({"span": span, "classification": "UNKNOWN"})
            return state
        self.visited.add(file_key)
        self.line_count += len(source.lines) - (bool(data) and data.endswith((b"\n", b"\r")))
        if self.line_count > MAX_LINES or len(self.visited) > MAX_FILES:
            frame = {"start": 0, "end": len(source.text)}
            op = self.operation("UNKNOWN", source, frame)
            self.add_issue(op, _issue(source, "SOURCE_LIMIT", "Source line or file count exceeds the bounded profile", 0, len(source.text)))
            statement = {"span": op["span"], "classification": "UNKNOWN"}
            op["statements"].append(statement)
            self.statements.append(statement)
            self.operations.append(op)
            return state
        try:
            frames = _frames(source)
        except _Syntax as exc:
            frame = {"start": 0, "end": len(source.text)}
            op = self.operation("UNKNOWN", source, frame)
            self.add_issue(op, _issue(source, exc.code, exc.message, 0, len(source.text)))
            statement = {"span": op["span"], "classification": "UNKNOWN"}
            op["statements"].append(statement)
            self.statements.append(statement)
            self.operations.append(op)
            return state
        active, block_start = state["active"], state["block_start"]
        owner_source, owner_end = state["owner_source"], state["owner_end"]
        sort_input, sort_output, sort_keys, sort_span = state["sort_input"], state["sort_output"], state["sort_keys"], state["sort_span"]
        for frame in frames:
            if active and owner_source.file_key == file_key:
                owner_end = frame["end"]
            tokens = frame["tokens"]
            self.token_count += len(tokens)
            statement = {"span": source.span(frame["start"], frame["end"]),
                         "classification": "COMMENT" if frame["comment"] and not frame["issues"] else "UNKNOWN"}
            self.statements.append(statement)
            if frame["comment"] and not frame["issues"]:
                if active:
                    active["statements"].append(statement)
                continue
            if len(self.operations) >= MAX_OPERATIONS or self.token_count > MAX_TOKENS:
                # Account for the entire remaining region once; never silently
                # truncate it or continue allocating operations past the budget.
                statement["span"] = source.span(frame["start"], len(source.text))
                statement["classification"] = "UNKNOWN"
                op = active or self.operation("UNKNOWN", source, frame)
                op["statements"].append(statement)
                self.add_issue(op, _issue(source, "PARSER_LIMIT", "Operation or token budget exceeded; remaining source is unresolved", frame["start"], len(source.text)))
                self.finish(op, owner_source if active else source,
                            block_start if active else frame["start"],
                            owner_end if active else len(source.text))
                active = None
                break
            op = active or self.operation("UNKNOWN", source, frame)
            op["statements"].append(statement)
            if frame["issues"]:
                if any(x["code"] in {"MACRO_BEARING_COMMENT", "UNCLOSED_QUOTE", "UNCLOSED_COMMENT"} for x in frame["issues"]):
                    self.poison_macros()
                for issue in frame["issues"]:
                    self.add_issue(op, issue)
                if not active:
                    self.finish(op, source, frame["start"], frame["end"])
                continue
            cursor = _Cursor(tokens, source)
            macro_facts = []
            try:
                if cursor.peek("%") and len(tokens) > 1 and tokens[1].lower == "include":
                    cursor.take("%")
                    cursor.take("include")
                    target, included = self.include(source, frame, cursor, stack, statement)
                    if included is not None:
                        state = self.parse(included, target, (*stack, file_key),
                                           {"active": active, "block_start": block_start, "owner_source": owner_source,
                                            "owner_end": owner_end, "sort_input": sort_input, "sort_output": sort_output,
                                            "sort_keys": sort_keys, "sort_span": sort_span})
                        active, block_start = state["active"], state["block_start"]
                        owner_source, owner_end = state["owner_source"], state["owner_end"]
                        sort_input, sort_output, sort_keys, sort_span = state["sort_input"], state["sort_output"], state["sort_keys"], state["sort_span"]
                    continue
                if active:
                    if cursor.peek("run") or cursor.peek("quit"):
                        terminator = cursor.take().lower
                        cursor.finish()
                        if (active["kind"] == "PROC_SQL") != (terminator == "quit"):
                            raise _Syntax("WRONG_TERMINATOR", "DATA/SORT require RUN; SQL requires QUIT")
                        if active["kind"] == "PROC_SORT":
                            if not sort_keys:
                                raise _Syntax("SORT_REQUIRES_BY", "SORT requires one BY statement")
                            active["facts"].append({"kind": "sort", "span": sort_span,
                                                    "input": sort_input, "output": sort_output, "keys": sort_keys})
                        if active["kind"] == "PROC_SQL" and sum(f["kind"] == "sql" for f in active["facts"]) != 1:
                            self.add_issue(active, _issue(owner_source, "SQL_STATEMENT_COUNT", "PROC SQL requires exactly one CREATE TABLE", block_start, owner_end))
                        statement["classification"] = "TERMINATOR"
                        self.finish(active, owner_source, block_start, owner_end)
                        active = None
                        continue
                    if active["kind"] == "DATA_STEP":
                        fact = _data_statement(cursor, self.macros, macro_facts)
                        cursor.finish()
                        if fact["kind"] == "input":
                            active["reads"].extend(fact["datasets"])
                        active["facts"].extend(macro_facts + [fact])
                    elif active["kind"] == "PROC_SORT":
                        cursor.take("by")
                        if sort_keys:
                            raise _Syntax("SORT_BY_COUNT", "Only one SORT BY statement is supported")
                        while cursor.peek():
                            sort_keys.append(cursor.name())
                        if (len(sort_keys) not in (1, 2) or len(set(sort_keys)) != len(sort_keys)
                                or set(sort_keys) & {"descending", "notsorted", "groupformat"}):
                            raise _Syntax("UNSUPPORTED_BY", "SORT requires one or two distinct ascending keys")
                        sort_span = statement["span"]
                    else:
                        if any(f["kind"] == "sql" for f in active["facts"]):
                            raise _Syntax("SQL_STATEMENT_COUNT", "Only one CREATE TABLE per PROC SQL is supported")
                        output, fact = _sql_statement(cursor, self.macros, macro_facts)
                        active["facts"].extend(macro_facts + [{"kind": "output", "span": fact["span"], "dataset": output}, fact])
                        active["reads"] = [x["dataset"] for x in fact["inputs"]]
                        active["writes"] = [output]
                    statement["classification"] = "FACT"
                elif cursor.accept("data"):
                    output = _dataset(cursor, self.macros, macro_facts)
                    cursor.finish()
                    op["kind"] = "DATA_STEP"
                    op["facts"] = macro_facts + [{"kind": "output", "span": statement["span"], "dataset": output}]
                    op["writes"] = [output]
                    active, block_start = op, frame["start"]
                    owner_source, owner_end = source, frame["end"]
                    statement["classification"] = "HEADER"
                elif cursor.accept("proc"):
                    proc = cursor.name()
                    if proc == "sort":
                        cursor.take("data")
                        cursor.take("=")
                        sort_input = _dataset(cursor, self.macros, macro_facts)
                        cursor.take("out")
                        cursor.take("=")
                        sort_output = _dataset(cursor, self.macros, macro_facts)
                        cursor.finish()
                        if sort_input == sort_output:
                            raise _Syntax("IN_PLACE_SORT", "PROC SORT requires a distinct output dataset")
                        sort_keys = []
                        sort_span = None
                        op["kind"], op["reads"], op["writes"] = "PROC_SORT", [sort_input], [sort_output]
                        op["facts"] = macro_facts
                    elif proc == "sql":
                        cursor.finish()
                        op["kind"] = "PROC_SQL"
                    else:
                        raise _Syntax("UNSUPPORTED_PROCEDURE", "Only PROC SORT and bounded PROC SQL are supported")
                    active, block_start = op, frame["start"]
                    owner_source, owner_end = source, frame["end"]
                    statement["classification"] = "HEADER"
                elif cursor.accept("%"):
                    directive = cursor.name()
                    if directive == "let":
                        name = cursor.name()
                        cursor.take("=")
                        value_start = cursor.i
                        value = cursor.name()
                        if cursor.accept("."):
                            if value != "work":
                                raise _Syntax("UNSUPPORTED_MACRO_VALUE", "Literal macro values are a name or complete WORK name")
                            value += "." + cursor.name()
                        cursor.finish()
                        raw = source.text[tokens[value_start].start:tokens[-1].end]
                        if any(c.isspace() for c in raw) or "/*" in raw:
                            raise _Syntax("UNSUPPORTED_MACRO_VALUE", "Macro literal cannot contain whitespace or comments")
                        if name in self.macros:
                            # The old value is no longer sound after an unsupported
                            # reassignment. Keep a tombstone instead of using it.
                            self.macros[name] = {"value": raw, "span": statement["span"], "unresolved": True}
                            raise _Syntax("MACRO_REASSIGNMENT", "Macro names may only be defined once")
                        self.macros[name] = {"value": raw, "span": statement["span"]}
                        op["kind"] = "MACRO"
                        op["facts"] = [{"kind": "macro_binding", "span": statement["span"], "name": name, "value": raw}]
                    else:
                        raise _Syntax("UNSUPPORTED_MACRO", "Only open-code literal LET and INCLUDE are supported")
                    statement["classification"] = "FACT"
                    self.finish(op, source, frame["start"], frame["end"])
                else:
                    raise _Syntax()
            except _Syntax as exc:
                if tokens and tokens[0].text == "%":
                    self.poison_macros()
                self.add_issue(op, _issue(source, exc.code, exc.message, frame["start"], frame["end"]))
                if not active:
                    self.finish(op, source, frame["start"], frame["end"])
        if active and context is None:
            self.add_issue(active, _issue(owner_source, "UNTERMINATED_BLOCK", "DATA/PROC block lacks its supported explicit terminator", block_start, owner_end))
            self.finish(active, owner_source, block_start, owner_end)
        return {"active": active, "block_start": block_start, "owner_source": owner_source, "owner_end": owner_end,
                "sort_input": sort_input, "sort_output": sort_output, "sort_keys": sort_keys, "sort_span": sort_span}


def parse_source(data: bytes, *, file_key: str, macros: dict | None = None,
                 include_loader: IncludeLoader | None = None) -> dict:
    """Parse only supplied bytes; includes resolve solely through the caller.

    ``macros`` is updated in encounter order, including included definitions.
    The loader must return bytes from an already validated authorized scope; this
    module never opens paths, performs network access, runs SAS or invokes a model.
    Caller must apply global budgets across distinct entry points and preserve
    returned issues. No successful parse is a semantic verification result.
    """
    if not isinstance(data, bytes) or not isinstance(file_key, str) or not file_key:
        raise TypeError("parse_source requires bytes and a nonempty file key")
    session = _Session(macros if macros is not None else {}, include_loader)
    session.parse(data, file_key)
    return {"profile": PROFILE, "operations": session.operations, "statements": session.statements,
            "issues": session.issues, "macros": session.macros,
            "files": sorted(session.visited), "semantic_verification": "UNVERIFIABLE",
            "semantic_acceptance": "BLOCKED"}
