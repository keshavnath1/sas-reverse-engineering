"""Bounded source-rule recovery using the existing SAS statement/token framing.

This helper describes a contiguous filter and branch pair after SET, with
optional ordered missing-value exclusions.
It never evaluates observations or supplies canonical semantic facts.
"""

from sas_re.sas_subset import _Cursor, _Source, _Syntax, _frames, _literal


def character_literal(cursor):
    token = cursor.take()
    if token.kind != "string" or len(token.text) > 258:
        raise _Syntax()
    quote = token.text[0]
    if token.text[-1] != quote:
        raise _Syntax()
    return token.text[1:-1].replace(quote * 2, quote)


def assignment(cursor, linked):
    if linked:
        cursor.take("else")
    cursor.take("if")
    variable = cursor.name()
    cursor.take("=")
    value = character_literal(cursor)
    cursor.take("then")
    target = cursor.name()
    cursor.take("=")
    literal = _literal(cursor)
    if literal["lexeme"] == "." or target == variable:
        raise _Syntax()
    cursor.finish()
    return {
        "predicate": {"variable": variable, "operator": "=", "value": value},
        "action": {"kind": "ASSIGN_NUMERIC_LITERAL", "target": target,
                   "lexeme": literal["lexeme"]},
    }


def recover(span, include_missing=False):
    """Return transient records, or no recovery for unsupported/ambiguous syntax."""
    try:
        source = _Source(span, "source")
        framed = _frames(source)
        if not include_missing and any(frame["issues"] for frame in framed):
            return []
        # A malformed comment is a recovery barrier too.
        frames = [frame for frame in framed if not frame["comment"] or frame["issues"]]
        if any(frame["issues"] for frame in frames[:5]):
            return []
        # Requiring the first three statements after SET prevents an unknown
        # intervening statement from being treated as transparent control flow.
        if (len(frames) < 7 or frames[0]["tokens"][0].lower != "data"
                or frames[1]["tokens"][0].lower != "set"
                or (frames[5]["tokens"] and frames[5]["tokens"][0].lower == "else")):
            return []
        cursors = [_Cursor(frame["tokens"], source) for frame in frames[2:5]]
        exclusion, first, alternative = cursors
        exclusion.take("if")
        variable = exclusion.name()
        exclusion.take("not")
        exclusion.take("in")
        exclusion.take("(")
        values = [character_literal(exclusion)]
        while exclusion.accept(","):
            if len(values) == 16:
                raise _Syntax()
            values.append(character_literal(exclusion))
        exclusion.take(")")
        exclusion.take("then")
        exclusion.take("delete")
        exclusion.finish()
        first_rule = assignment(first, linked=False)
        last_rule = assignment(alternative, linked=True)
        if (first_rule["predicate"]["variable"] != variable
                or last_rule["predicate"]["variable"] != variable
                or first_rule["action"]["target"] != last_rule["action"]["target"]):
            return []
        rules = [
            {
                "predicate": {"variable": variable, "operator": "NOT IN", "values": values},
                "action": {"kind": "DELETE", "scope": "CURRENT_ROW_ITERATION",
                           "on_match": "SKIP_REMAINING_STATEMENTS_AND_SUPPRESS_OUTPUT"},
                "when": [],
            },
            {**first_rule, "when": [{"rule_index": 0, "predicate_result": False}]},
            {**last_rule, "when": [{"rule_index": 0, "predicate_result": False},
                                  {"rule_index": 1, "predicate_result": False}]},
        ]
        for rule, frame in zip(rules, frames[2:5], strict=True):
            rule["span"] = source.span(frame["start"], frame["end"])
        if include_missing:
            append_missing_exclusions(source, frames, rules)
        return rules
    except (UnicodeDecodeError, _Syntax):
        return []


def missing_predicate(cursor, function):
    cursor.take("if")
    cursor.take(function.lower())
    cursor.take("(")
    arguments = [cursor.name()]
    if function == "CMISS":
        while cursor.accept(","):
            if len(arguments) == 32:
                raise _Syntax()
            arguments.append(cursor.name())
    cursor.take(")")
    predicate = {"function": function, "arguments": arguments, "evaluation": "DIRECT"}
    if function == "CMISS":
        cursor.take(">")
        cursor.take("0")
        predicate.update(evaluation="COMPARISON", operator=">", value_lexeme="0")
    cursor.take("then")
    cursor.take("delete")
    cursor.finish()
    return predicate


def append_missing_exclusions(source, frames, rules):
    """Append a recognized prefix only, preserving barriers and original order."""
    for position, function in enumerate(("MISSING", "CMISS", "CMISS"), start=5):
        if position >= len(frames) or frames[position]["issues"]:
            break
        following = frames[position + 1]["tokens"] if position + 1 < len(frames) else []
        if following and following[0].lower == "else":
            break
        frame = frames[position]
        try:
            predicate = missing_predicate(_Cursor(frame["tokens"], source), function)
        except _Syntax:
            break
        # Assignment branch results must not gate these exclusions.
        prerequisites = [0, *range(3, len(rules))]
        rules.append({
            "span": source.span(frame["start"], frame["end"]),
            "predicate": predicate,
            "action": dict(rules[0]["action"]),
            "when": [{"rule_index": index, "predicate_result": False}
                     for index in prerequisites],
        })
