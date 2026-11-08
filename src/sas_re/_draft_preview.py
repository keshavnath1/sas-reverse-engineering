"""Private rendering of a small, supplied public synthetic v2 subject. No source/store I/O."""

import hashlib
import re

from ._dependency_diagnostics import _bounded_copy, diagnose
from ._io_common import EvidenceError, canonical_bytes
from .evidence import digest


class PreviewError(EvidenceError):
    """Fixed diagnostic only; a rejected subject produces no draft."""


_STATUS = """artifact_authority: DRAFT
semantic_verification: UNVERIFIABLE
semantic_acceptance: BLOCKED
benchmark_execution: NOT_RUN"""
_VERSION = "mvp1-draft-preview/1"
_NAMES = re.compile(r"[a-zA-Z0-9_][a-zA-Z0-9_.-]{0,127}")
_FILE_KEY = re.compile(r"[a-zA-Z0-9_.-]+:[a-zA-Z0-9_./-]{1,160}")
_NUMBER = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?|\.", re.ASCII)


def _subject(graph, supplied):
    # Detach exact JSON types before indexing or comparing either untrusted argument.
    try:
        graph = _bounded_copy(graph)
        supplied = _bounded_copy(supplied)
        if type(supplied) is not dict or type(graph) is not dict:
            raise PreviewError("PREVIEW_SUBJECT_INVALID")
        if len(canonical_bytes(graph)) > 256 * 1024 or len(canonical_bytes(supplied)) > 512 * 1024:
            raise PreviewError("PREVIEW_SUBJECT_LIMIT")
        checked = diagnose(graph, supplied.get("parent_graph_sha256"))
        if digest(supplied) != digest(checked):
            raise PreviewError("PREVIEW_DIAGNOSTIC_MISMATCH")
    except EvidenceError as error:
        raise PreviewError(error.code) from None
    if (len(graph["operations"]) > 8 or len(graph["edges"]) > 24
            or len(graph["datasets"]) + len(graph["columns"]) > 80
            or sum(len(op["facts"]) for op in graph["operations"]) > 64
            or len(graph["unknowns"]) + len(graph["contradictions"]) > 32):
        raise PreviewError("PREVIEW_SUBJECT_LIMIT")
    return graph, checked


def _name(value):
    # No comments, token lexemes, issue prose, paths or arbitrary Markdown as copy.
    return value if _NAMES.fullmatch(value) else "[identifier withheld]"


def _names(values):
    return ", ".join(f"`{_name(name)}`" for name in values) or "none listed"


def _display_file_key(key):
    if not _FILE_KEY.fullmatch(key) or any(p in ("", ".", "..") for p in key.split(":", 1)[1].split("/")):
        return "withheld-" + hashlib.sha256(key.encode()).hexdigest()
    return key


def _location(span):
    return (f"`{_display_file_key(span['file_key'])}` lines {span['line_start']}–{span['line_end']}, "
            f"bytes [{span['start']}, {span['end']})")


def _span_entry(span):
    cite = span["citation"]
    return (f"{_location(span)}. Source SHA-256 `{cite['source_sha256']}`, "
            f"span SHA-256 `{span['byte_sha256']}`, cited excerpt SHA-256 `{cite['excerpt_sha256']}`.")


def _expression(expr):
    kind = expr["kind"]
    if kind == "name":
        return _name(expr["name"])
    if kind == "literal":
        value = expr["lexeme"]
        return value if len(value) <= 40 and _NUMBER.fullmatch(value) else "[literal withheld]"
    if kind == "binary":
        return f"({_expression(expr['left'])} {expr['operator']} {_expression(expr['right'])})"
    if kind == "group":
        return f"({_expression(expr['expression'])})"
    if kind == "unary":
        return f"({expr['operator']}{_expression(expr['operand'])})"
    return "[expression detail withheld]"


def _fact_text(fact, revision="legacy"):
    kind = fact["kind"]
    if revision == "tf1" and kind == "retain":
        return f"RETAIN `{_name(fact['target'])}` with initialization `{_expression(fact['initial'])}`."
    if revision == "tf1" and kind == "sum":
        return (f"Sum statement `{_name(fact['target'])} + {_expression(fact['expression'])}`. "
                "The represented SUM state persists across rows and treats a missing addend as zero.")
    if kind == "sort":
        return (f"Sort `{_name(fact['input'])}` into `{_name(fact['output'])}` "
                f"by {_names(fact['keys'])}.")
    if kind == "output":
        return f"Output dataset `{_name(fact['dataset'])}`."
    if kind == "input":
        return f"{fact['mode']} reads {_names(fact['datasets'])}."
    if kind == "by":
        direction = "ascending" if fact["ascending"] else "non-ascending"
        return f"BY keys in declared order: {_names(fact['keys'])} ({direction})."
    if kind == "assignment":
        if revision == "tf1" and fact["guard"] is not None and fact["guard"]["kind"] == "by_flag":
            guard = fact["guard"]
            return (f"IF `{guard['flag'].upper()}.{_name(guard['key'])}` THEN "
                    f"`{_name(fact['target'])} = {_expression(fact['expression'])}`.")
        guard = " under a represented condition" if fact["guard"] is not None else ""
        return f"Assignment{guard}: `{_name(fact['target'])} = {_expression(fact['expression'])}`."
    if kind == "sql":
        inputs = ", ".join(f"`{_name(x['dataset'])}` as `{_name(x['alias'])}`" for x in fact["inputs"])
        parts = [f"FROM {inputs}."]
        join = fact["join"]
        if join:
            parts.append(f"{join['kind']} JOIN on `{_expression(join['left'])} = {_expression(join['right'])}`.")
        where = fact["where"]
        if where:
            condition = (f"{_expression(where['left'])} {where['operator']} {_expression(where['right'])}"
                         if where["kind"] == "comparison" else f"{where['flag']}.{_name(where['key'])}")
            parts.append(f"WHERE `{condition}`.")
        selections = [f"`{_name(x['output'])} = {_expression(x['expression'])}`" for x in fact["select"]]
        parts.append("Project " + ", ".join(selections) + ".")
        if fact["order_by"]:
            parts.append(f"ORDER BY {_names(fact['order_by'])}.")
        return " ".join(parts)
    if kind == "include":
        target = "Target unresolved; effects UNKNOWN." if fact["target_file_key"] is None else "Target recorded."
        return f"INCLUDE literal `{_name(fact['path'])}`. {target}"
    return f"Fact kind `{kind}`. Its semantics require separate review."


def _review_test(op, revision="legacy"):
    kinds = {fact["kind"] for fact in op["facts"]}
    if revision == "tf1" and "sort" in kinds:
        return ("Preserve input/output row multisets and counts. Check the output composite-key sequence "
                "against the order contract, allowing only its declared tie freedom.")
    if revision == "tf1" and any(f["kind"] == "input" and f["mode"] == "SET" for f in op["facts"]):
        return ("Preserve the actual input stream, including its producer's chosen tie order. "
                "Compare initialization, FIRST/LAST key-prefix flags, explicit resets and accumulation "
                "at each row and partition boundary against an independent reference.")
    if "sort" in kinds:
        return ("Compare the input/output row multiset, counts and the full composite key sequence. "
                "Challenge equal keys and ordinary numeric missing keys separately.")
    if "by" in kinds and "assignment" in kinds:
        return ("Trace first and last rows of each key prefix, equal keys and a group split at a chunk boundary. "
                "Compare derived values for finite and missing inputs with a separately justified tolerance.")
    if "sql" in kinds:
        return ("Compare the projected values, qualifying row multiset and requested order. Challenge duplicate "
                "and missing keys, tied output rows and the effect of predicate placement.")
    if "include" in kinds:
        return "Obtain authorized evidence for the target and its effects before accepting workflow completeness."
    return ("Compare declared input and output schemas, row multiplicities, state transitions and values "
            "against an independently reviewed reference for this operation.")


class _View:
    """Document-local references into the canonical graph; no new factual identities."""

    def __init__(self, graph, diagnostic, revision="legacy"):
        self.graph = graph
        self.revision = revision
        self.diagnostic = diagnostic
        self.ops = sorted(graph["operations"], key=lambda op: op["sequence"])
        self.edges = sorted(graph["edges"], key=lambda edge: edge["edge_id"])
        self.labels = {op["operation_id"]: f"O{i}" for i, op in enumerate(self.ops, 1)}
        self.labels.update({e["edge_id"]: f"E{i}" for i, e in enumerate(self.edges, 1)})
        self.nodes = {d["dataset_id"]: d["name"] for d in graph["datasets"]}
        self.datasets = self.nodes.copy()
        for col in graph["columns"]:
            self.nodes[col["column_id"]] = self.datasets[col["dataset_id"]] + "." + col["name"]
        self.analysis = diagnostic["analysis"]
        # TF-1 uses the detailed layout for single-module subjects as well.
        self.multi = len(graph["module_ids"]) > 1 or revision == "tf1"
        self.owner = {op["operation_id"]: op["module_id"] for op in self.ops}

    def ref(self, identifier):
        label = self.labels[identifier]
        return f"[{label}](EVIDENCE.md#{label.lower()})"

    def refs(self, identifiers):
        return ", ".join(self.ref(identifier) for identifier in identifiers) or "graph-wide"

    def fact_ref(self, op, index):
        label = self.labels[op["operation_id"]]
        return f"[{label} fact {index}](EVIDENCE.md#{label.lower()}-fact-{index})"

    def module_handoffs(self):
        lines = []
        for edge in self.edges:
            first, second = edge["from_operation_id"], edge["to_operation_id"]
            if edge["type"] == "DATA" and self.owner[first] != self.owner[second]:
                lines.extend([f"**OBSERVATION** `{self.owner[first]}` {self.ref(first)} produces "
                              f"{self.dataset_names(edge['node_ids'])} for `{self.owner[second]}` "
                              f"{self.ref(second)} on {self.ref(edge['edge_id'])}.", ""])
        return lines

    def include_gaps(self):
        lines = []
        for op in self.ops:
            for i, fact in enumerate(op["facts"]):
                if fact["kind"] == "include" and fact["target_file_key"] is None:
                    lines.extend([f"**OBSERVATION** {self.fact_ref(op, i)} names `{_name(fact['path'])}` "
                                  "without a bound target. Its reads, writes and downstream effects are UNKNOWN.",
                                  "", "**ASSUMPTION** Obtain separately authorized target evidence before "
                                  "treating the represented outputs as the complete workflow.", ""])
        return lines

    def dataset_names(self, identifiers):
        direct = set(identifiers) & self.datasets.keys()
        parents = self.analysis["column_parents"]
        touched = direct | {parents[i] for i in identifiers if i in parents}
        labels = []
        for parent in sorted(touched, key=self.datasets.__getitem__):
            label = f"`{_name(self.datasets[parent])}`"
            if parent not in direct:
                cols = sorted(self.nodes[i] for i in identifiers if parents.get(i) == parent)
                label += f" (column references only: {_names(cols)})"
            labels.append(label)
        return ", ".join(labels) or "none listed"

    def workflow(self):
        lines = []
        for op in self.ops:
            kinds = {"sort", "input", "by", "assignment", "sql", "include"}
            if self.revision == "tf1":
                kinds.update({"retain", "sum"})
            facts = [f"{_fact_text(f, self.revision)} ({self.fact_ref(op, i) if self.multi else f'fact {i}'})"
                     for i, f in enumerate(op["facts"]) if f["kind"] in kinds]
            owner = f", module `{op['module_id']}`" if self.multi else ""
            outputs = f"writes {self.dataset_names(op['writes'])}."
            if self.multi and not op["writes"]:
                outputs = "has no listed output node."
            lines.append(f"**OBSERVATION** {self.ref(op['operation_id'])} ({op['kind']}{owner}) "
                         + outputs + " " + " ".join(facts))
            lines.append("")
        return lines

    def document(self, title, lines):
        version = "mvp2-multimodule-preview/1" if self.multi else _VERSION
        if self.revision == "tf1":
            version = "two-fixture-preview/1"
        header = [f"# {title}", "", "UNVERIFIED · public synthetic draft", "", "```text", _STATUS,
                  "```", "", f"Graph SHA-256 `{self.diagnostic['parent_graph_sha256']}` · "
                  f"preview `{version}` · diagnostics `{self.diagnostic['algorithm']}`", ""]
        return ("\n".join(header + lines).rstrip() + "\n").encode("utf-8")


def _prd(v):
    lines = ["## Scope and proposed objective", "",
             "**HYPOTHESIS** Use this workflow to define a reproducible transformation and a shared "
             "correctness test for candidate replacements. The business purpose and consumers need an owner.",
             "", "## What the supplied workflow represents", "", *v.workflow(),
             "## Functional requirements for review", ""]
    if v.multi:
        lines.extend(v.module_handoffs())
        lines.extend(v.include_gaps())
    for op in v.ops:
        ref = v.ref(op["operation_id"])
        reads_writes = f"reads {v.dataset_names(op['reads'])} and writes {v.dataset_names(op['writes'])} at the dataset level."
        if v.multi and not op["reads"] and not op["writes"]:
            reads_writes = "has no represented dataset accesses. Its effects require further evidence."
        lines.extend([f"### {v.labels[op['operation_id']]} · {op['kind']}", "",
                      f"**OBSERVATION** {ref} {reads_writes}",
                      "", f"**HYPOTHESIS** Require a candidate to reproduce this boundary. {_review_test(op, v.revision)}", ""])
    for edge in v.edges:
        if edge["type"] == "DATA":
            lines.append(f"**INFERENCE** Treat {v.dataset_names(edge['node_ids'])} on {v.ref(edge['edge_id'])} "
                         f"as a producer/consumer interface. Confirm the exact dataset version at that handoff.")
    lines.extend(["", "## Proposed nonfunctional requirements and open questions", "",
                  "**HYPOTHESIS** Make a run reproducible from fixed input bytes, versions and policy choices. "
                  "Keep peak memory and elapsed time within budgets a workload owner must supply.",
                  "", "**ASSUMPTION** Who consumes the output? Which population, row key, duplicate policy, "
                  "tie order and absolute/relative tolerance would they accept? What hardware, data volume "
                  "and completion window should the alternatives be tested against?",
                  "", "**HYPOTHESIS** Before migration, agree on those answers and an independent reference. "
                  "Require complete row/key coverage and a discrepancy report against the same acceptance "
                  "criteria for both candidates."])
    return v.document("Draft product requirements", lines)


def _modules(v):
    lines = []
    # Read modules in first represented operation order, including any declared empty modules.
    for module in dict.fromkeys([*v.owner.values(), *v.graph["module_ids"]]):
        lines.extend([f"## Module `{_name(module)}`", ""])
        for op in v.ops:
            if op["module_id"] != module:
                continue
            oid = op["operation_id"]
            incident = [e["edge_id"] for e in v.edges if oid in (e["from_operation_id"], e["to_operation_id"])]
            order = op["order_contract"]
            policy = op["numeric_policy"]
            lines.extend([f"### {v.labels[oid]} · {op['kind']}", "",
                          f"**OBSERVATION** {v.ref(oid)} reads {v.dataset_names(op['reads'])} and writes "
                          f"{v.dataset_names(op['writes'])}. Incident edge references: {v.refs(incident) if incident else 'none listed'}.",
                          "", "**OBSERVATION** The graph records the following facts, in fact-index order.", ""])
            for i, fact in enumerate(op["facts"]):
                ref = v.fact_ref(op, i) if v.multi else f"Fact {i}"
                lines.append(f"- {ref} · {_fact_text(fact, v.revision)} ({_location(fact['span'])})")
            source = v.ref(oid) + " · " if v.multi else ""
            lines.extend(["", f"**OBSERVATION** {source}Order `{order['kind']}`, keys {_names(order['keys'])}, "
                          f"input precondition `{order['precondition']}`, tie order `{order['tie_order']}`. "
                          f"Cardinality rule `{op['cardinality']}`.", "",
                          f"**OBSERVATION** {source}Numeric representation `{policy['storage']}`, missing order "
                          f"`{policy['missing_order']}`, arithmetic `{policy['missing_arithmetic']}`, "
                          f"expression order `{policy['expression_order']}`. Runtime equivalence "
                          f"`{policy['runtime_equivalence']}`."])
            for effect in op["state_effects"]:
                ref = v.fact_ref(op, effect["fact_index"]) if v.multi else f"Fact {effect['fact_index']}"
                lines.extend(["", f"**OBSERVATION** {ref} records {effect['kind']} state, "
                              f"initialization `{effect['initialization']}`, persistence `{effect['persistence']}` "
                              f"and reset `{effect['reset']}`."])
            if v.multi:
                lines.extend(_lineage_rows(v, op))
            if v.revision == "tf1":
                for index, fact in enumerate(op["facts"]):
                    if fact["kind"] == "sum":
                        lines.extend(["", f"**INFERENCE** {v.fact_ref(op, index)} accumulates from prior retained "
                                      "state unless an earlier explicit assignment resets it. Review fact order "
                                      "and group guards together. Independent behavioral evidence and safe "
                                      "partition boundaries remain unproved."])
            lines.extend(["", f"**HYPOTHESIS** Candidate validation: {_review_test(op, v.revision)}", ""])
        issues = [i for i in v.graph["unknowns"] + v.graph["contradictions"]
                  if not i["operation_ids"] or any(op["module_id"] == module and op["operation_id"] in
                                                   i["operation_ids"] for op in v.ops)]
        lines.append(f"**OBSERVATION** {len(issues)} unresolved issue record(s) apply here or globally. "
                     "The [evidence summary](EVIDENCE.md#proof-obligations) identifies the bindings.")
        lines.extend(["", "**ASSUMPTION** Effects outside represented facts, unsupported constructs, "
                      "physical dataset versions and behavior across partitions still need source-aware review.", ""])
    return v.document("Draft module specifications", lines)


def _lineage_rows(v, op):
    if not op["lineage"] and not op["control_lineage"]:
        return []
    detail = ""
    if op["kind"] == "PROC_SQL":
        detail = (f" Value rows may include ON and WHERE inputs. The SELECT expression identifies the "
                  f"arithmetic operands. The numeric missing-key policy is `{op['numeric_policy']['missing_join']}`.")
    lines = ["", f"**OBSERVATION** {v.ref(op['operation_id'])} records these value and control inputs." + detail, "",
             "| Output or control | Input columns | Earlier facts | Input phase | Source fact |",
             "|---|---|---|---|---|"]
    for item in [*op["lineage"], *op["control_lineage"]]:
        target = v.nodes[item["output_column_id"]] if "output_column_id" in item else item["role"]
        prior = ", ".join(v.fact_ref(op, i) for i in item["input_fact_indices"]) or "none listed"
        inputs = _names(v.nodes[i] for i in item["input_column_ids"])
        lines.append(f"| `{_name(target)}` | {inputs} | {prior} | `{item['input_phase']}` | "
                     f"{v.fact_ref(op, item['fact_index'])} |")
    if any(effect["kind"] == "BY" for effect in op["state_effects"]):
        lines.extend(["", f"**INFERENCE** The BY annotation at {v.ref(op['operation_id'])} models group flags. "
                      "It does not establish that an assigned value depends on a previous row. Review the "
                      "assignment's value lineage separately before proposing any partition boundary."])
    for index, fact in enumerate(op["facts"]):
        if fact["kind"] == "sql" and fact["join"]:
            lines.extend(["", f"**INFERENCE** At {v.fact_ref(op, index)}, multiple rows matching a join key "
                          "may yield multiple result rows before the WHERE filter, if present. Confirm "
                          "multiplicity with duplicate and missing keys; no runtime count is available here."])
            if fact["order_by"] and op["order_contract"]["tie_order"] == "UNSPECIFIED":
                lines.append(f"**INFERENCE** {v.fact_ref(op, index)} orders by {_names(fact['order_by'])}. "
                             "Relative order within a tied key remains unspecified.")
    return lines


def _architecture(v):
    lines = ["## As-is computational flow", "", *v.workflow(),
             "**OBSERVATION** Each box is an original operation ID. Edge labels identify original "
             "graph records in the [evidence index](EVIDENCE.md#edge-register). RESOURCE annotations, "
             "when present, are dotted. Arrows describe the supplied model.", "", "```mermaid", "flowchart LR"]
    for op in v.ops:
        oid = op["operation_id"]
        owner = f" · {op['module_id']}" if v.multi else ""
        lines.append(f'    {oid}["{v.labels[oid]} {op["kind"]}{owner}"]')
    for e in v.edges:
        arrow = "-.->" if e["type"] == "RESOURCE" else "-->"
        lines.append(f"    {e['from_operation_id']} {arrow}|{v.labels[e['edge_id']]} {e['type']}| {e['to_operation_id']}")
    lines.extend(["```", "", "## Dependencies and missing proof", ""])
    if v.multi:
        lines.extend(v.module_handoffs())
        lines.extend(v.include_gaps())
    for e in v.edges:
        first, second = e["from_operation_id"], e["to_operation_id"]
        lines.append(f"**OBSERVATION** {v.ref(e['edge_id'])} records {e['type']} from {v.ref(first)} "
                     f"to {v.ref(second)}. Dataset nodes: {v.dataset_names(e['node_ids'])}.")
        lines.append("")
    for c in v.analysis["components"]:
        if c["cyclic"]:
            state = any(e["type"] == "STATE" and e["edge_id"] in c["edge_ids"] for e in v.edges)
            proof = ("Test state continuity across successive rows and group boundaries."
                     if state else "Resolve the feedback before considering an acyclic execution plan.")
            if state and v.multi:
                proof = ("Treat the STATE annotation as conservative. No independently demonstrated cross-row "
                         "value dependence follows from this edge; test the specific grouping and value lineage.")
            if state and v.revision == "tf1":
                sums = [v.fact_ref(op, i) for op in v.ops if op['operation_id'] in c['operation_ids']
                        for i, fact in enumerate(op['facts']) if fact['kind'] == 'sum']
                if sums:
                    proof = (f"Source facts {', '.join(sums)} represent retained accumulation across rows. "
                             "Review initialization and explicit resets with those facts. Independently verified "
                             "state continuity and safe partition boundaries remain unproved.")
            lines.extend([f"**INFERENCE** Represented cycle at {v.refs(c['operation_ids'])} via {v.refs(c['edge_ids'])}. "
                          + proof, ""])
    for c in v.analysis["conflicts"]:
        coverage = (f"{c['missing_data_group_count']} shared dataset group(s) lack a direct DATA edge. "
                    if c["kind"] == "RAW" else "")
        lines.extend([f"**INFERENCE** {c['kind']} conflict between {v.ref(c['earlier_operation_id'])} and "
                      f"{v.ref(c['later_operation_id'])}, including {v.dataset_names(c['dataset_ids'])}. "
                      + coverage + "Physical versions and access isolation require evidence.", ""])
    pairs = v.analysis["no_path_pairs"]
    if v.multi and pairs:
        lines.extend(["**INFERENCE** For the pairs below there is no represented dependency path; "
                      "independence unproved.", "", "| From | To |", "|---|---|"])
        absent = {}
        for pair in pairs:
            absent.setdefault(pair["from_operation_id"], []).append(pair["to_operation_id"])
        lines.extend(f"| {v.ref(first)} | {v.refs(targets)} |" for first, targets in absent.items())
        lines.append("")
    else:
        for p in pairs:
            lines.extend([f"**INFERENCE** {v.ref(p['from_operation_id'])} → {v.ref(p['to_operation_id'])}: "
                          "no represented dependency path; independence unproved.", ""])
    lines.extend(["## To-be alternatives", "",
                  "**HYPOTHESIS** The [native Python candidate](ADR_NATIVE.md) keeps a local intermediate so "
                  "order and per-row state can be inspected. The [Spark candidate](ADR_SPARK.md) would need "
                  "a proven exchange and group-boundary contract. Compare both on the same behavior tests.",
                  "", "**ASSUMPTION** Capacity, skew, retry behavior, partition boundaries and admissible "
                  "tie order require external confirmation. No execution schedule has been established."])
    return v.document("Architecture overview", lines)


def _adr(v, spark):
    runtime = "Spark" if spark else "Native Python"
    lines = ["## Decision under review", ""]
    if spark:
        lines += ["**HYPOTHESIS** Consider Spark only if measured input and intermediate sizes exceed an "
                  "approved single-workstation resource budget. A partitioned representation might accommodate "
                  "larger inputs but adds shuffle, spill, serialization and key-skew costs.",
                  "", "**HYPOTHESIS** Evaluate a keyed exchange, explicit sort and row transformation. Check "
                  "global key sequence on output and continuity of every affected group at exchange boundaries. "
                  "Local partition sorting alone cannot establish the required end-to-end order."]
    else:
        lines += ["**HYPOTHESIS** Use native Python as the comparison baseline. Model named datasets as "
                  "local row sequences, order with an explicit composite-key comparator, and carry BY state "
                  "through a single ordered scan where required. Expose intermediate rows for inspection.",
                  "", "**HYPOTHESIS** A local representation may simplify tie-out and avoid transfer costs. "
                  "Row objects, sorting scratch space and the intermediate may exceed workstation memory. "
                  "Bound input plus sort workspace before any trial."]
    if v.multi:
        lines.extend(_decision_matrix(v))
    lines.extend(["", "## Source-to-candidate mapping", ""])
    for op in v.ops:
        kind = op["kind"]
        if kind == "PROC_SORT":
            design = ("Test an explicit distribution and sort policy for the full key." if spark else
                      "Test a local sort with an explicit missing-key comparator and tie policy.")
        elif kind == "DATA_STEP":
            design = ("Test row expressions and ordered state across partition boundaries." if spark else
                      "Test a row-by-row reference with explicit missing values and group reset rules.")
        elif kind == "PROC_SQL":
            design = ("Test key redistribution, predicate placement and the output ordering contract." if spark else
                      "Test a local keyed join retaining every matching row before applying the filter.")
            if not any(f["kind"] == "sql" and f["join"] for f in op["facts"]):
                design = "Test the projection and each represented predicate on the same input rows."
        elif kind == "INCLUDE":
            design = "Keep effects outside the supplied graph open for source review."
        else:
            design = "Defer this operation until its effects have a reviewed translation and tie-out test."
        lines.extend([f"**HYPOTHESIS** {v.ref(op['operation_id'])} ({kind}). {design} {_review_test(op, v.revision)}", ""])
    ops = {op["operation_id"]: op for op in v.ops}
    for e in v.edges:
        target = ops[e["to_operation_id"]]
        if e["type"] == "ORDER":
            proof = "Challenge tied rows and confirm the candidate satisfies the declared ordering requirement."
        elif e["type"] == "STATE":
            proof = "Compare the state immediately before and after an input chunk boundary."
            if "BY" in target["stateful_constructs"] and len(target["order_contract"]["keys"]) == 2:
                proof += (" Change the leading key while the trailing key repeats. Split a group across two "
                          "chunks and compare its boundary rows to a single uninterrupted reference scan.")
        elif e["type"] == "DATA":
            proof = "Compare the intermediate row multiset at the handoff before comparing the final values."
        else:
            continue
        lines.extend([f"**HYPOTHESIS** For {v.ref(e['edge_id'])} ({e['type']}): {proof}", ""])
    tie_out = ("Use the same hashed cases for both candidates. Compare row counts, "
               "multisets per composite key, missing-value placement, order across groups and arithmetic "
               "at rounding boundaries. Report discrepancy rows and maximum absolute/relative error. "
               "Review unresolved ties separately; avoid manufacturing a tie-breaker.")
    if v.multi:
        tie_out = ("Use the same hashed cases for both candidates. Use only keys and columns present at "
                   "each boundary. Report missing rows, unexpected duplicates, discrepancies in tied "
                   "groups and maximum absolute/relative error at rounding boundaries.")
        for op in v.ops:
            keys = op["order_contract"]["keys"]
            if not keys:
                continue
            comparison = "Check the multiset of projected rows within each tied group and the order between groups."
            if v.revision == "tf1":
                if op["order_contract"]["kind"] == "INPUT_ORDER":
                    comparison = "Preserve the actual producer stream, including its chosen order within ties."
                elif op["kind"] == "PROC_SORT":
                    comparison = "Preserve rows and apply only the tie freedom established by the SORT contract."
                elif op["kind"] == "PROC_SQL":
                    comparison = "Follow this SQL ORDER BY contract with per-key multisets and no invented secondary order."
            lines.extend([f"**HYPOTHESIS** At {v.ref(op['operation_id'])} compare {v.dataset_names(op['writes'])} "
                          f"by {_names(keys)}. {comparison}", ""])
    lines.extend(["## Common tie-out and benchmark proposal", "",
                  "**ASSUMPTION** An owner must supply the input population, versioned output reference, "
                  "key/duplicate policy, treatment of tied rows and numerical tolerance. P2B semantic "
                  "review and human selection are outstanding.",
                  "", "**HYPOTHESIS** " + tie_out,
                  "", "**HYPOTHESIS** After correctness review and separate benchmark approval, pin versions "
                  "and hardware; record input bytes, skew, memory budget and cache state. Run one cold and "
                  "five warm trials per agreed size. Collect end-to-end elapsed time, CPU time and peak "
                  "memory including sort and I/O; record spill and transferred bytes where applicable.", ""])
    reason = ("Defer unless resource evidence justifies distribution and group-boundary tests pass under "
              "different partition counts, skew and retries." if spark else
              "Defer if the largest approved case exceeds the memory budget or the comparator cannot "
              "preserve missing-key and group behavior.")
    lines.append(f"**HYPOTHESIS** {reason} On a tie-out failure, retain the existing boundary and its "
                 "reference output; reopen the disputed operation. Neither candidate has a measured result.")
    return v.document(f"Candidate ADR · {runtime}", lines)


def _decision_matrix(v):
    """Contrast hypotheses against the relevant canonical subjects, without ranking engines."""
    def edge_refs(kind):
        ids = [e["edge_id"] for e in v.edges if e["type"] == kind]
        return v.refs(ids) if ids else "no such edge recorded"

    ops = v.refs(op["operation_id"] for op in v.ops)
    sql = [v.fact_ref(op, i) for op in v.ops for i, f in enumerate(op["facts"]) if f["kind"] == "sql"]
    sql_orders = [f"{v.fact_ref(op, i)} by {_names(f['order_by'])}" for op in v.ops
                  for i, f in enumerate(op["facts"]) if f["kind"] == "sql" and f["order_by"]]
    output_order = " SQL output: " + ", ".join(sql_orders) + "." if sql_orders else ""
    local_memory = "Budget input, sort scratch and join multiplicity."
    validation = "Trace duplicates, missing keys and filtering against an independent reference."
    if v.revision == "tf1" and not sql:
        output_order = " Input order and preconditions are recorded in the module specifications."
        local_memory = "Budget input, retained state and output buffers."
        validation = "Trace initialization, resets, accumulation, missing addends and the actual input stream."
    rows = [
        ("Workload size", f"{ops}. Production rows, bytes and skew: UNKNOWN.",
         "Size a single-host trial including the intermediate.", "Consider distribution only if measured scale warrants it."),
        ("Ordering", f"ORDER: {edge_refs('ORDER')}.{output_order} Acceptable order among ties: UNKNOWN.",
         "Check the full key comparator and missing-key placement.", "Check ordering after exchanges and at consumption."),
        ("Partition boundaries", f"STATE: {edge_refs('STATE')}. Safe split keys: UNKNOWN.",
         "Compare chunk boundaries with one continuous scan.", "Vary partition count and split a tied group; compare boundary rows."),
        ("Memory", f"DATA: {edge_refs('DATA')}. Peak bytes, headroom and spill: UNKNOWN.",
         local_memory, "Budget per-worker skew, shuffle buffers and spill."),
        ("Data movement", f"Logical handoffs: {edge_refs('DATA')}. Physical transfers: UNKNOWN.",
         "Measure local intermediate materialization.", "Measure repartition and serialization bytes before proposing reuse."),
        ("Operations", f"Workflow: {ops}. Operator capacity, recovery budget and supported deployment: UNKNOWN.",
         "Test local restart at the intermediate.", "Test retry and duplicate-output handling; identify a runtime owner."),
        ("Validation obligations", f"Review {', '.join(sql) or ops} and the [proof obligations](EVIDENCE.md#proof-obligations). "
         "Independent reference and tolerances: UNKNOWN.",
         validation,
         "Use the same reference across partitions and retries; reconcile row multisets before timing."),
    ]
    lines = ["", "## Decision matrix", "", "**HYPOTHESIS** Both candidates require the same correctness "
             "reference. UNKNOWN marks evidence still needed to compare them.", "",
             "| Criterion | Evidence and open question | Native Python hypothesis | Spark hypothesis |",
             "|---|---|---|---|"]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    lines.extend(["", *v.include_gaps()])
    return lines


def _evidence(v):
    g, diagnostic = v.graph, v.diagnostic
    lines = ["## Subject and reading key", "",
             f"**OBSERVATION** Workspace `{g['workspace_id']}`, run `{g['run_id']}`, attempt "
             f"`{g['attempt_id']}`. Source fingerprint `{g['source_fingerprint']}`. Scope manifest "
             f"`{g['scope_manifest_sha256']}`, profile SHA-256 `{g['profile_sha256']}`. "
             f"Diagnostic result SHA-256 `{digest(diagnostic)}`.", "",
             "OBSERVATION reports what the supplied graph contains. INFERENCE interprets a represented "
             "relationship. ASSUMPTION needs outside confirmation. HYPOTHESIS is a proposal to test. "
             "MEASUREMENT requires observed execution evidence. No performance measurement is asserted.",
             "", "O and E labels are local links. Persistent identities and zero-based fact indexes below "
             "resolve in the graph identified by the digest above. Spans use original byte offsets, "
             "exclusive end offsets and inclusive line numbers. A synthesized fact can point at one statement "
             "(for example a BY clause); use the enclosing operation span to locate the declaration "
             "and check the fact in context.", "", "## Operation register", ""]
    for op in v.ops:
        oid = op["operation_id"]
        lines.extend([f"### {v.labels[oid]}", "", f"**OBSERVATION** `{oid}`, {op['kind']}, "
                      f"module `{op['module_id']}`, canonical classification `{op['classification']}`. "
                      + _span_entry(op["span"]), "",
                      "Read nodes: " + _names(op["reads"]) + ".",
                      "Write nodes: " + _names(op["writes"]) + ".", ""])
        for index, fact in enumerate(op["facts"]):
            if v.multi:
                lines.extend([f"#### {v.labels[oid]} fact {index}", "",
                              f"**OBSERVATION** {v.ref(oid)} · `{fact['kind']}` · {_span_entry(fact['span'])}", ""])
            else:
                lines.append(f"- **OBSERVATION** Fact {index} · `{fact['kind']}` · {_span_entry(fact['span'])}")
        lines.append("")
    lines.extend(["## Edge register", ""])
    for e in v.edges:
        lines.extend([f"### {v.labels[e['edge_id']]}", "",
                      f"**OBSERVATION** `{e['edge_id']}`, {e['type']}, {v.ref(e['from_operation_id'])} → "
                      f"{v.ref(e['to_operation_id'])}. Canonical classification `{e['classification']}`. "
                      f"Original evidence operations: {v.refs(e['evidence_operation_ids'])}.", "",
                      "Linked nodes: " + _names(e["node_ids"]) + ".", ""])
    lines.extend(["## Node register", "", "**OBSERVATION** Original graph identifiers, logical names and owners.", "",
                  "| Logical node | Owner | Canonical ID |", "|---|---|---|"])
    for key, name in v.nodes.items():
        lines.append(f"| `{_name(name)}` | `{v.analysis['node_owners'][key]}` | `{key}` |")
    lines.extend(["", "## Proof obligations", "",
                  f"**OBSERVATION** {len(g['log_observations'])} LOG/LST observation record(s) in the "
                  f"supplied graph. Diagnostic eligibility `{v.analysis['eligibility']}`.",
                  "", "**INFERENCE** The following obligations come from the recomputed P3-A1 diagnostic.", ""])
    for block in v.analysis["blockers"]:
        refs = v.refs(block["operation_ids"])
        extra = []
        if "issue_id" in block:
            extra.append(f"issue `{block['issue_id']}`")
        if "edge_id" in block:
            extra.append(v.ref(block["edge_id"]))
        lines.append(f"- `{block['code']}` ({', '.join([refs, *extra])}): {block['missing_proof']}")
    if v.multi:
        lines.extend(["", "### Unresolved records and bindings", "", *v.include_gaps()])
        for issue in g["unknowns"] + g["contradictions"]:
            binding = v.refs(issue["operation_ids"]) if issue["operation_ids"] else "no bound operation"
            keys = ", ".join(f"`{_display_file_key(key)}`" for key in issue["file_keys"]) or "none listed"
            lines.extend([f"**OBSERVATION** `{issue['issue_id']}` · {issue['kind']} · {binding}. "
                          f"Declared file keys: {keys}.", ""])
            for span in issue["spans"]:
                lines.extend([_span_entry(span), ""])
    lines.extend(["", "**ASSUMPTION** Independent review must establish original scope, effects and "
                  "source semantics. Dataset identities alone do not establish physical versions or "
                  "safe partitioning. Caller-supplied comments and issue prose have no decision authority."])
    return v.document("Evidence and uncertainty", lines)


def generate_preview(graph, diagnostic, *, revision="legacy"):
    """Return six deterministic Markdown files for a supplied, small in-memory subject.

    The caller supplies stable public synthetic objects. Matching them binds the documents
    to a representation, without authenticating source provenance or semantic truth.
    """
    if revision not in {"legacy", "tf1"}:
        raise PreviewError("PREVIEW_REVISION_UNSUPPORTED")
    graph, checked = _subject(graph, diagnostic)
    view = _View(graph, checked, revision)
    return {"PRD.md": _prd(view), "MODULES.md": _modules(view),
            "ARCHITECTURE.md": _architecture(view), "ADR_NATIVE.md": _adr(view, False),
            "ADR_SPARK.md": _adr(view, True), "EVIDENCE.md": _evidence(view)}
