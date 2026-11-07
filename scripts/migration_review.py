"""Render the existing two-range source evidence for migration planning."""


import html
import json


def location(span):
    return (f"lines {span['line_start']}–{span['line_end']}, "
            f"bytes [{span['start']}, {span['end']})")


def anchor(span):
    return f"bytes-{span['start']}-{span['end']}"


def cite(label, span):
    return f"[{label}](#{anchor(span)})"


def names(values):
    return ", ".join(f"`{value}`" for value in values)


def rule_description(rule):
    predicate, action = rule["predicate"], rule["action"]
    if "function" in predicate:
        condition = f"{predicate['function']}({names(predicate['arguments'])})"
        if predicate["evaluation"] == "COMPARISON":
            condition += f" {predicate['operator']} {predicate['value_lexeme']}"
    else:
        values = predicate.get("values", [predicate.get("value")])
        # Literal spelling is data. Escape Markdown/HTML without interpreting it.
        quoted = ", ".join("`" + html.escape(json.dumps(value, ensure_ascii=True))
                           .replace("`", "&#96;").replace("|", "&#124;") + "`" for value in values)
        condition = f"`{predicate['variable']}` {predicate['operator']} {quoted}"
    if action["kind"] == "DELETE":
        effect = "terminate the current row iteration and suppress its output"
    else:
        effect = f"assign numeric literal `{action['lexeme']}` to `{action['target']}`"
    return f"SOURCE_RECOGNIZED · If {condition}, {effect}. Execution UNVERIFIED."


def missing_rule_relationships(rules):
    lines = []
    for index, rule in enumerate(rules[3:], start=3):
        prerequisites = ", ".join(
            cite("earlier predicate", rules[item["rule_index"]]["span"])
            for item in rule["when"]
        )
        lines.append(f"- {cite('Exclusion', rule['span'])} follows "
                     f"{cite('preceding statement', rules[index - 1]['span'])} in source order. "
                     f"It requires false results from {prerequisites}. A true result ends this row "
                     "and skips the remaining statements.")
    if lines:
        lines += [
            "- Either label branch or no-assignment fallthrough can reach the missing-value checks "
            "after the branch pair. The first exclusion has no label-branch predicate prerequisite.",
            "- Argument types, evaluated missing counts and actual row survival remain unknown. "
            "The evidence establishes statement order without establishing lazy evaluation inside CMISS.",
        ]
    return lines


def interval_declarations(item):
    sql = item.get("sql_declaration")
    if sql:
        if sql["kind"] == "DUPLICATE_GROUP_SIZES":
            return (f" Group by {names([sql['group_by']])}, retain `{sql['having']}`, "
                    f"and project {names(sql['projection'])}. Counts are per group.")
        bindings = ", ".join(f"`{b['expression']}` → `:{b['target']} TRIMMED`"
                             for b in sql["bindings"])
        purpose = " Counts retained groups." if sql["kind"] == "DUPLICATE_GROUP_COUNT" else ""
        return f" Positional INTO bindings {bindings}.{purpose}"
    gate = item.get("gate_declaration")
    if gate:
        operand = gate["operand"]
        right = "&" + operand["variable"] if "variable" in operand else operand["literal"]
        left = "&" + gate["variable"]
        if gate["action"] == "GUARD":
            return f" Optional guard `%UPCASE({left}) {gate['operator']} {right}`."
        return f" Condition `{left} {gate['operator']} {right}` requests `%abort_run`."
    return ""


def sql_gate_relationships(findings):
    spans = {item["span"]["start"]: item["span"] for item in findings}
    lines = []
    for item in findings:
        sql = item.get("sql_declaration", {})
        if "group_query_start" in sql:
            group = cite("grouped query", spans[sql["group_query_start"]])
            count = cite("scalar count", item["span"])
            lines.append(f"- **SOURCE_DECLARED** · {group} → {count}.")
        gate = item.get("gate_declaration", {})
        if gate.get("action") != "ABORT_REQUEST":
            continue
        condition = cite("condition and potential abort request", item["span"])
        refs = [cite(f"INTO binding for {name}", spans[start])
                for name, start in gate["into_sources"].items()]
        links = " → ".join([", ".join(refs), condition]) if refs else condition
        if "guard_start" in gate:
            links += f". Requires {cite('optional guard', spans[gate['guard_start']])}."
        else:
            links += "."
        referenced = {gate["variable"], gate["operand"].get("variable")} - {None}
        unresolved = referenced - gate["into_sources"].keys()
        if unresolved:
            links += f" Producer unresolved for {names(sorted(unresolved))}."
        lines.append(f"- **SOURCE_DECLARED / EXECUTION_UNVERIFIED** · {links}")
    return lines


def render(evidence):
    data_selection, sort_selection = evidence["selections"]
    data = data_selection["declared_operation"]
    sort = sort_selection["declared_operation"]
    declarations = data["declaration_spans"]
    gaps = data["unsupported_statements"]
    interval = evidence["interval_effects"]
    findings = interval["findings"]
    recovery = data.get("status_rule_recovery")
    rules = recovery["rules"] if recovery else []
    connection = evidence["connection"]
    middle = evidence["intervening_span"]

    lines = [
        "# Migration review", "",
        "Source-only partial analysis based on [EVIDENCE.json](EVIDENCE.json). "
        "All locations refer to the original bytes.", "",
        "```text",
        *(f"{key}: {evidence[key]}" for key in (
            "artifact_authority", "behavioral_evidence", "semantic_verification",
            "semantic_acceptance", "benchmark_execution", "supported_profile_reconstruction",
        )),
        "```", "",
        "## TRACE", "",
        f"Source identity **{evidence['source_identity']}**. SHA-256 `{evidence['source']['sha256']}`.",
        "",
    ]
    emitted_anchors = set()

    def trace(label, span, detail=""):
        target = anchor(span)
        marker = ""
        if target not in emitted_anchors:
            emitted_anchors.add(target)
            marker = f'<a id="{target}"></a>'
        digest = f" SHA-256 `{span['sha256']}`." if "sha256" in span and marker else ""
        lines.append(f"- {marker}**{label}** · {location(span)}.{digest}"
                     + (f" {detail}" if detail else ""))

    trace("Selected DATA range", data_selection["selected_span"])
    trace("DATA output", declarations["output"], names([data["output"]]))
    trace("SET input", declarations["input"], names([data["input"]]))
    trace("KEEP", declarations["keep"],
          f"{len(data['selected_columns'])} declared output selections ({names(data['selected_columns'])}). "
          "Column values and types remain unknown.")
    if recovery:
        lines.extend(["", f"Ordered source-rule recovery **{recovery['status']}**.", ""])
    for rule in rules:
        trace("Ordered source rule", rule["span"], rule_description(rule))
    for gap in gaps:
        trace("Unsupported transformation", gap["span"],
              f"{names(gap['reason_codes'])}. `{gap['effect']}`.")
    trace("Selected SORT range", sort_selection["selected_span"])
    trace("SORT datasets", sort["span"],
          f"Input {names([sort['input']])}. Output {names([sort['output']])}.")
    trace("SORT BY", sort["ordering_span"],
          f"{names(sort['ordering_keys'])} · {sort['declared_direction']}.")

    lines.extend([
        "", "### Intervening source findings", "",
        f"Bytes [{middle['start']}, {middle['end']}). Inventory **{interval['status']}**. "
        f"SHA-256 `{interval['sha256']}`.", "",
    ])
    for item in findings:
        trace("Interval finding", item["span"], " ".join(
            f"{field.replace('_', ' ').capitalize()} · {names(values)}."
            for field, values in item.items()
            if field not in {"span", "sql_declaration", "gate_declaration"} and values
        ) + interval_declarations(item))
    if not findings:
        lines.append("The bounded inventory contains no finding records.")

    handoff = f"{cite('DATA output', declarations['output'])} → {cite('SORT input', sort['span'])}"
    lines.extend([
        "", "## MAP", "",
        f"- **{connection['classification']} / {connection['execution_verification']}** · {handoff}. "
        "Runtime dataset identity and version remain unknown.",
        f"- **UNKNOWN** · Upstream and downstream boundaries remain "
        f"{evidence['boundaries']['upstream']} and {evidence['boundaries']['downstream']}, respectively. "
        f"See {cite('SET input', declarations['input'])} and {cite('SORT output', sort['span'])}.",
    ])
    if rules:
        exclusion, first, alternative = [cite("source rule", rule["span"]) for rule in rules[:3]]
        lines.extend([
            f"- **SOURCE_RECOGNIZED / UNVERIFIED** · {exclusion} precedes {first} and {alternative}. "
            "A true exclusion guard ends this row before either assignment.",
            f"- {alternative} is reached only if {first}'s guard is false. "
            "A true first guard skips the linked alternative.",
            f"- If both guards are false, the pair makes no assignment "
            f"({recovery['fallthrough']}). Later unresolved effects may still exclude or change an assigned row.",
        ])
    lines.extend(missing_rule_relationships(rules))
    interval_refs = {}
    for label, fields in (
        ("Source-declared reads", ("reads",)),
        ("Source-declared outputs", ("writes", "ods_outputs")),
        ("Potential control gates and macro-dependent effects", ("control_gates", "macro_invocations")),
        ("Unresolved interval effects", ("unknown_effects",)),
    ):
        refs = [cite(f"lines {item['span']['line_start']}–{item['span']['line_end']}", item["span"])
                for item in findings if any(item.get(field) for field in fields)]
        interval_refs[label] = ", ".join(refs)
        if refs:
            lines.append(f"- **{label}** · {interval_refs[label]}.")
    lines.extend(sql_gate_relationships(findings))
    outputs = interval_refs["Source-declared outputs"]
    if interval["shared_writer_identified"] is True:
        lines.append(f"- **INFERRED** · An explicit interval output may replace the shared dataset in the {handoff} handoff. See {outputs}.")
    elif interval["shared_writer_identified"] is False:
        lines.append("- No direct writer identified within the inspected supported source forms; unresolved effects remain.")
    lines.append(f"- **UNKNOWN** · SORT reachability is {interval['sort_reachability']} "
                 f"at the {cite('SORT range', sort_selection['selected_span'])}.")

    keep = cite("KEEP selection", declarations["keep"])
    ordering = cite("SORT BY", sort["ordering_span"])
    gap_refs = ", ".join(cite(f"gap at line {gap['span']['line_start']}", gap["span"]) for gap in gaps)
    row_evidence = cite("SET input", declarations["input"])
    if rules:
        row_evidence += ", " + ", ".join(cite("recovered rule", rule["span"]) for rule in rules)
    if gap_refs:
        row_evidence += f", {gap_refs}"
    interval_ref = "[bounded interval findings](#intervening-source-findings)"
    control_refs = interval_refs["Potential control gates and macro-dependent effects"] or interval_ref
    derivation_refs = gap_refs
    if rules:
        derivation_refs = ", ".join(cite("recovered rule", rule["span"]) for rule in rules)
        if gap_refs:
            derivation_refs += ", " + gap_refs
    label = "`Default` derivation" if "default" in data["selected_columns"] else "Selected value derivation"
    lines.extend([
        "", "## Behavioral obligations and validation plan", "",
        "Each obligation is **HYPOTHETICAL**. Obtain reference evidence attributable to the verified "
        "source and a specific execution before evaluating a replacement.", "",
        "| Obligation | Evidence | Required validation |",
        "| --- | --- | --- |",
        f"| Row eligibility and filter order | {row_evidence} | Compare input and prepared rows, including "
        "surviving and excluded identities and cases where more than one rule could apply. |",
        f"| {label} | {keep}" + (f", {derivation_refs}" if derivation_refs else "") +
        " | Obtain prepared output values and reference rows for each applicable branch, including fallthrough. |",
        f"| Missing-value handling | {row_evidence}, {ordering} | Obtain descriptors and reference rows "
        "for applicable character and numeric missing cases, including missing sort keys. |",
        f"| Key uniqueness checks | {ordering}, {interval_ref}, [MAP](#map) | Confirm whether uniqueness is required, "
        "which keys are checked and how duplicates are reported or handled. Obtain attributable duplicate-case outputs. |",
        f"| Abort reachability | {control_refs}, [MAP](#map), {cite('SORT range', sort_selection['selected_span'])} "
        "| Obtain run records showing which checks fired and whether SORT was reached on both continuation and abort paths. |",
        f"| Dataset-version continuity | {handoff}, {interval_ref}, [MAP](#map) | Bind DATA output and SORT input to "
        "execution snapshots or equivalent version evidence and account for intervening writers and unknown effects. |",
        f"| SORT ordering and downstream handoff | {ordering}, {cite('SORT output', sort['span'])} "
        "| Obtain input/output descriptors and attributable sorted reference rows. Confirm key types, "
        "missing and equal-key order, row multiplicity and the downstream consumer’s contract. |",
        "", "## Conditional architecture implications", "",
        f"- **Native Python** · Consider a local implementation after confirming the ordered row rules "
        f"({row_evidence}) and comparison semantics ({ordering}). Check available memory against workload size.",
        f"- **Spark or another distributed engine** · Consider partitioned preparation after proving row-local "
        f"rules ({row_evidence}). Validate global uniqueness if required, control-gate behavior and global ordering "
        f"across partitions ({ordering} and [MAP](#map)). Require attributable version and output evidence before partitioning the handoff.",
        "", "Runtime selection remains open. Workload size, resource needs and performance are unmeasured.",
    ])
    return ("\n".join(lines) + "\n").encode("utf-8")
