"""Private, in-memory diagnostics for a supplied public synthetic canonical v2 graph."""

import json
import math
import re

from ._io_common import EvidenceError
from .contracts import validate_contract
from .evidence import digest, record_id


class DiagnosticError(EvidenceError):
    """Refusal with a fixed reason code; no partial analysis or caller data."""


_MAX_VALUES = 200_000
_MAX_DEPTH = 64
_MAX_BYTES = 8 * 1024 * 1024
_TABLES = (
    ("datasets", "dataset_id", "ds"),
    ("columns", "column_id", "col"),
    ("operations", "operation_id", "op"),
    ("edges", "edge_id", "edge"),
    ("log_observations", "observation_id", "log"),
)


def _bounded_copy(value: object) -> object:
    """Detach native JSON with exact compact UTF-8 size accounting before hashing."""
    size = 1  # The frozen canonical representation ends with LF.
    values = 0
    ancestors = set()

    def charge(amount):
        nonlocal size
        size += amount
        if size > _MAX_BYTES:
            raise DiagnosticError("LIMIT_CANONICAL_BYTES")

    def string_size(string):
        # One code point is at least one encoded byte. Count escaping and UTF-8
        # in fixed-size chunks; never encode an oversized caller string at once.
        if len(string) + 2 > _MAX_BYTES - size:
            raise DiagnosticError("LIMIT_CANONICAL_BYTES")
        charge(2)
        for offset in range(0, len(string), 4096):
            encoded = json.encoder.encode_basestring(string[offset:offset + 4096])
            try:
                charge(len(encoded.encode("utf-8")) - 2)
            except UnicodeEncodeError:
                raise DiagnosticError("JSON_INVALID") from None

    def visit(item, depth):
        nonlocal values
        if depth > _MAX_DEPTH:
            raise DiagnosticError("LIMIT_DEPTH")
        values += 1
        if values > _MAX_VALUES:
            raise DiagnosticError("LIMIT_JSON_VALUES")
        kind = type(item)
        if kind is str:
            string_size(item)
        elif item is None or kind is bool:
            charge(5 if item is False else 4)
        elif kind is int:
            # Reject huge integers before decimal conversion. 3.322 exceeds
            # log2(10), so this lower bound cannot reject a number that fits.
            if item.bit_length() > ((_MAX_BYTES - size) * 3322 // 1000) + 1:
                raise DiagnosticError("LIMIT_CANONICAL_BYTES")
            try:
                charge(len(str(item)))
            except ValueError:  # Same interpreter integer limit as canonical_bytes.
                raise DiagnosticError("JSON_INVALID") from None
        elif kind is float:
            if not math.isfinite(item):
                raise DiagnosticError("JSON_INVALID")
            charge(len(json.dumps(item, allow_nan=False)))
        elif kind is dict or kind is list:
            marker = id(item)
            if marker in ancestors:
                raise DiagnosticError("JSON_CYCLE")
            # Charge punctuation and refuse oversized immediate fan-out without
            # copying it. Only active ancestors occupy the recursion stack.
            children = len(item)
            immediate = children * 2 if kind is dict else children
            if values + immediate > _MAX_VALUES:
                raise DiagnosticError("LIMIT_JSON_VALUES")
            charge(2 + max(0, children - 1) + (children if kind is dict else 0))
            ancestors.add(marker)
            if kind is dict:
                result = {}
                for key, child in item.items():
                    if type(key) is not str:
                        raise DiagnosticError("JSON_INVALID")
                    visit(key, depth + 1)
                    result[key] = visit(child, depth + 1)
            else:
                result = [visit(child, depth + 1) for child in item]
            ancestors.remove(marker)
            return result
        else:
            # Exact type tests above do not invoke subclass/metaclass methods.
            raise DiagnosticError("JSON_INVALID")
        return item

    return visit(value, 0)


def _check_counts(graph: dict) -> None:
    """Check graph fan-out on detached input before invoking the schema validator."""
    def array_length(record, key):
        items = record.get(key)
        return len(items) if type(items) is list else 0

    for key, maximum in (("operations", 100), ("module_ids", 8), ("edges", 10_000)):
        if array_length(graph, key) > maximum:
            code = "MODULES" if key == "module_ids" else key.upper()
            raise DiagnosticError("LIMIT_" + code)
    if array_length(graph, "datasets") + array_length(graph, "columns") > 2_000:
        raise DiagnosticError("LIMIT_NODES")
    if type(graph.get("operations")) is list:
        facts = sum(array_length(op, "facts") for op in graph["operations"] if type(op) is dict)
        if facts > 5_000:
            raise DiagnosticError("LIMIT_FACTS")


def _index_records(graph):
    tables = {}
    modules = set(graph["module_ids"])
    for table, field, prefix in _TABLES:
        index = {}
        for record in graph[table]:
            identifier = record[field]
            if identifier in index:
                raise DiagnosticError("DUPLICATE_RECORD_ID")
            if "module_id" in record and record["module_id"] not in modules:
                raise DiagnosticError("MODULE_OWNER_MISMATCH")
            if identifier != record_id(prefix, graph["source_fingerprint"], record, field):
                raise DiagnosticError("RECORD_ID_MISMATCH")
            index[identifier] = record
        tables[table] = index
    return tables


def _check_nodes(datasets, columns):
    names = set()
    for dataset in datasets.values():
        name = dataset["name"].lower()
        if name in names:
            raise DiagnosticError("AMBIGUOUS_DATASET_NAME")
        names.add(name)
    column_names = set()
    for column in columns.values():
        parent = datasets.get(column["dataset_id"])
        if parent is None:
            raise DiagnosticError("DANGLING_COLUMN_DATASET")
        if column["module_id"] != parent["module_id"]:
            raise DiagnosticError("COLUMN_OWNER_MISMATCH")
        key = (column["dataset_id"], column["name"].lower())
        if key in column_names:
            raise DiagnosticError("AMBIGUOUS_COLUMN_NAME")
        column_names.add(key)


def _check_operations(operations, nodes, columns):
    sequences = [op["sequence"] for op in operations.values()]
    if any(type(seq) is not int for seq in sequences) or set(sequences) != set(range(len(sequences))):
        raise DiagnosticError("INVALID_OPERATION_SEQUENCE")
    reads, writes = {}, {}
    for identifier, op in operations.items():
        reads[identifier] = set(op["reads"])
        writes[identifier] = set(op["writes"])
        if not reads[identifier] <= nodes or not writes[identifier] <= nodes:
            raise DiagnosticError("DANGLING_OPERATION_NODE")
        for group in ("state_effects", "lineage", "control_lineage"):
            for item in op[group]:
                index = item["fact_index"]
                if type(index) is not int or not 0 <= index < len(op["facts"]):
                    raise DiagnosticError("INVALID_FACT_INDEX")
                for prior in item.get("input_fact_indices", ()):
                    if type(prior) is not int or not 0 <= prior < index:
                        raise DiagnosticError("INVALID_PRIOR_FACT_INDEX")
                for column in item.get("input_column_ids", ()):
                    if column not in columns or column not in reads[identifier]:
                        raise DiagnosticError("INVALID_LINEAGE_INPUT")
                if "output_column_id" in item:
                    column = item["output_column_id"]
                    if column not in columns or column not in writes[identifier]:
                        raise DiagnosticError("INVALID_LINEAGE_OUTPUT")
    return reads, writes


def _check_issues(graph, operations):
    """Preserve opaque IDs and index only the supplied co-scoped unknown bindings."""
    ids = set()
    related = {identifier: set() for identifier in operations}
    for table in ("unknowns", "contradictions"):
        for issue in graph[table]:
            if issue["issue_id"] in ids:
                raise DiagnosticError("DUPLICATE_ISSUE")
            ids.add(issue["issue_id"])
            if (issue["kind"] == "CONTRADICTION") != (table == "contradictions"):
                raise DiagnosticError("MISPLACED_CONTRADICTION")
            binding = issue["operation_ids"]
            if any(identifier not in operations for identifier in binding):
                raise DiagnosticError("DANGLING_ISSUE_REFERENCE")
            if table == "unknowns":
                for identifier in binding:
                    related[identifier].update(binding)
    return related


def _check_edges(graph, reads, writes, nodes, related):
    for edge in graph["edges"]:
        source, target = edge["from_operation_id"], edge["to_operation_id"]
        if source not in reads or target not in reads or any(
            item not in reads for item in edge["evidence_operation_ids"]
        ):
            raise DiagnosticError("DANGLING_EDGE_OPERATION")
        shared = edge["node_ids"]
        if any(item not in nodes for item in shared):
            raise DiagnosticError("DANGLING_EDGE_NODE")
        if edge["type"] == "DATA":
            if not shared or any(item not in writes[source] or item not in reads[target] for item in shared):
                raise DiagnosticError("PRODUCER_CONSUMER_MISMATCH")
        if edge["type"] == "UNKNOWN" and target not in related[source]:
            raise DiagnosticError("UNKNOWN_EDGE_NOT_RECORDED")


def _check_locations(item):
    """Only internal interval consistency; no source bytes or physical file lookup."""
    if type(item) is list:
        for child in item:
            _check_locations(child)
    if type(item) is dict:
        if "line_start" in item and item["line_start"] > item["line_end"]:
            raise DiagnosticError("INVALID_LINE_INTERVAL")
        if "byte_sha256" in item:
            if item["start"] >= item["end"] or any(
                item[key] != item["citation"][key] for key in ("file_key", "line_start", "line_end")
            ):
                raise DiagnosticError("INVALID_SPAN")
        for child in item.values():
            _check_locations(child)


def _check_references(graph, tables):
    operations = tables["operations"]
    datasets, columns = tables["datasets"], tables["columns"]
    nodes = datasets.keys() | columns.keys()
    _check_nodes(datasets, columns)
    reads, writes = _check_operations(operations, nodes, columns)
    related = _check_issues(graph, operations)
    _check_edges(graph, reads, writes, nodes, related)
    for item in graph["log_observations"]:
        if item["run_id"] != graph["run_id"] or item["attempt_id"] != graph["attempt_id"]:
            raise DiagnosticError("LOG_OWNER_MISMATCH")
        if any(identifier not in operations for identifier in item["source_operation_ids"]):
            raise DiagnosticError("DANGLING_LOG_OPERATION")
    for statement in graph["statement_coverage"]:
        owner = statement["operation_id"]
        if owner is not None and owner not in operations:
            raise DiagnosticError("DANGLING_STATEMENT_OPERATION")
    for field in ("operation", "dataset", "column", "edge", "log_observation", "unknown", "contradiction"):
        if graph["coverage"][field + "_count"] != len(graph[field + "s"]):
            raise DiagnosticError("COVERAGE_MISMATCH")
    _check_locations(graph)


def _subject(graph: object, expected_graph_sha256: str) -> dict:
    """Bind and check the exact in-memory subject without reconstructing evidence."""
    if type(expected_graph_sha256) is not str or not re.fullmatch("[0-9a-f]{64}", expected_graph_sha256):
        raise DiagnosticError("INVALID_EXPECTED_DIGEST")
    detached = _bounded_copy(graph)
    if type(detached) is not dict or detached.get("schema_version") != "2.0":
        raise DiagnosticError("UNSUPPORTED_GRAPH_VERSION")
    _check_counts(detached)
    try:
        validate_contract("Graph", detached, version="2.0")
        if digest(detached) != expected_graph_sha256:
            raise DiagnosticError("GRAPH_DIGEST_MISMATCH")
        _check_references(detached, _index_records(detached))
    except DiagnosticError:
        raise
    except EvidenceError as error:
        raise DiagnosticError(error.code) from None
    except RecursionError:
        raise DiagnosticError("SCHEMA_INVALID") from None
    return detached


# All analysis below operates on the detached, structurally validated subject.
_NO_PATH = "no represented dependency path; independence unproved."


def _topology(operations, edges):
    """One shortest predecessor per positive-length reachable ordered pair."""
    by_id = {op['operation_id']: op['sequence'] for op in operations}
    outgoing = {i: [] for i in by_id}
    for edge in edges:
        outgoing[edge['from_operation_id']].append(edge)
    for neighbors in outgoing.values():
        neighbors.sort(key=lambda e: (by_id[e['to_operation_id']], e['to_operation_id'],
                                      e['type'], e['edge_id']))

    routes, pairs, absent = {}, [], []
    for start in by_id:
        predecessors = routes[start] = {}
        queue = [start]
        # Appending to this FIFO while iterating visits each operation at most once.
        for current in queue:
            for edge in outgoing[current]:
                end = edge['to_operation_id']
                if end in predecessors:
                    continue
                predecessors[end] = (current, edge['edge_id'])
                if end != start:
                    queue.append(end)
        for end in by_id:
            if end in predecessors:
                parent, edge_id = predecessors[end]
                pairs.append(dict(from_operation_id=start, to_operation_id=end,
                                  predecessor_operation_id=parent, edge_id=edge_id))
            elif start != end:
                absent.append(dict(from_operation_id=start, to_operation_id=end, reason=_NO_PATH))

    # Mutual positive-length reachability partitions the graph; isolated vertices
    # are singleton components, not cycles. Never substitute a DAG for the input.
    components, ownership = [], {}
    for start in by_id:
        if start in ownership:
            continue
        members = [end for end in by_id if end == start or
                   (end in routes[start] and start in routes[end])]
        component = dict(operation_ids=members, edge_ids=[], cyclic=start in routes[start])
        components.append(component)
        ownership.update((i, component) for i in members)
    for edge in edges:
        component = ownership[edge['from_operation_id']]
        if component is ownership[edge['to_operation_id']]:
            component['edge_ids'].append(edge['edge_id'])
    return pairs, absent, components


def witness(result, from_operation_id, to_operation_id):
    """Recover one path from a diagnose() result. [] means no represented path.

    The table belongs to that result, not a new attestation of the caller's copy.
    Never expand all possible paths, including when the requested pair is a cycle.
    """
    analysis = result['analysis']
    ops = analysis['operation_constraints']
    if len(ops) > 100 or len(analysis['reachability']) > len(ops) ** 2:
        raise DiagnosticError('INVALID_WITNESS_TABLE')
    known = {op['operation_id'] for op in ops}
    if from_operation_id not in known or to_operation_id not in known:
        raise DiagnosticError('UNKNOWN_WITNESS_ENDPOINT')
    parents = {r['to_operation_id']: r for r in analysis['reachability']
               if r['from_operation_id'] == from_operation_id}
    if to_operation_id not in parents:
        return []
    path = []
    current = to_operation_id
    for _ in range(len(ops)):
        if current not in parents:
            break
        step = parents[current]
        path.append(step['edge_id'])
        current = step['predecessor_operation_id']
        if current == from_operation_id:
            return path[::-1]
    raise DiagnosticError('INVALID_WITNESS_TABLE')


def _accesses(operations, dataset_for, names):
    """Logical name intersection is a conservative hazard, never physical identity."""
    access = {}
    for op in operations:
        modes = {}
        for mode in ('reads', 'writes'):
            groups = {}
            for node in sorted(op[mode]):
                parent = dataset_for[node]
                # One representative per group suffices for a pair witness.
                groups.setdefault(names[parent], node)
            modes[mode] = groups
        access[op['operation_id']] = modes
    return access


def _conflicts(operations, dependencies, dataset_for, names):
    access = _accesses(operations, dataset_for, names)
    data = {}
    for edge in dependencies:
        if edge['type'] == 'DATA':
            groups = data.setdefault((edge['from_operation_id'], edge['to_operation_id']), set())
            groups.update(names[dataset_for[n]] for n in edge['node_ids'])
    explanations = {
        'RAW': 'Establish which dataset version the reader consumes and verify the producer binding.',
        'WAR': 'Show the earlier read completes against its intended version before the later write.',
        'WAW': 'Establish overwrite order, versions and physical write isolation, including column writes.',
    }
    results = []
    for index, earlier in enumerate(operations):
        first = earlier['operation_id']
        for later in operations[index + 1:]:
            second = later['operation_id']
            for kind, left, right in (('RAW', 'writes', 'reads'), ('WAR', 'reads', 'writes'),
                                      ('WAW', 'writes', 'writes')):
                a, b = access[first][left], access[second][right]
                shared = a.keys() & b.keys()
                if not shared:
                    continue
                unrepresented = shared - data.get((first, second), set()) if kind == 'RAW' else set()
                group = min(unrepresented or shared)
                nodes = sorted({a[group], b[group]})
                proof = explanations[kind]
                if unrepresented:
                    proof = 'No direct DATA edge covers all shared datasets. ' + proof
                results.append(dict(kind=kind, earlier_operation_id=first, later_operation_id=second,
                                    node_ids=nodes, dataset_ids=sorted({dataset_for[n] for n in nodes}),
                                    shared_dataset_count=len(shared), missing_data_group_count=len(unrepresented),
                                    uncertainty='UNVERSIONED_DATASET', missing_proof=proof))
    return results


def _blockers(graph, operations, edges):
    findings = []

    def add(code, ops, proof, category='CONSTRAINT', **references):
        findings.append(dict(code=code, operation_ids=ops, missing_proof=proof, category=category,
                             scope='LOCAL' if ops else 'GLOBAL', **references))

    add('EFFECT_COMPLETENESS_UNPROVED', [], 'Independently establish source semantics and completeness '
        'of reads, writes, external effects and unresolved dependencies for this scope.')
    for op in operations:
        ids = [op['operation_id']]
        if op['stateful_constructs'] or op['state_effects']:
            add('STATE_CONTINUITY', ids, 'Prove initialization, reset, call order and state carried across rows/groups.')
        order = op['order_contract']
        if order['requires_sorted_inputs'] or order['kind'] != 'UNSPECIFIED' or order['precondition'] == 'UNRESOLVED':
            add('ORDER_PRECONDITION', ids, 'Establish the declared input/order/key requirements for every affected row.')
        if order['keys'] and order['tie_order'] == 'UNSPECIFIED':
            add('TIE_ORDER_UNSPECIFIED', ids, 'Prove equal-key ordering is immaterial or supply the required tie order.')
        if op['cardinality'] != 'NOT_APPLICABLE':
            add('CARDINALITY', ids, 'Prove row multiplicity and selection under the declared cardinality rule.')
        add('NUMERIC_EQUIVALENCE_UNPROVED', ids, 'Preserve expression order, missing-value and numeric policies; '
            'runtime equivalence and numerical invariants have not been demonstrated.')
        if op['kind'] == 'UNKNOWN':
            add('UNKNOWN_OPERATION', ids, 'Resolve the operation and its effects against independently reviewed source.')
    edge_proof = {'UNKNOWN': 'Resolve the declared unknown dependency and its original evidence.',
                  'SIDE_EFFECT': 'Establish the external effect, isolation, and required observation order.',
                  'RESOURCE': 'Establish shared-resource behavior separately from semantic precedence.'}
    for edge in edges:
        kind = edge['type']
        if kind in edge_proof:
            add(kind + '_EDGE', sorted({edge['from_operation_id'], edge['to_operation_id']}),
                edge_proof[kind], edge_id=edge['edge_id'])
    # code and missing_proof in a supplied Issue are untrusted source material.
    # Keep a precise reference to them; never promote them to our own verdict.
    issue_proofs = {
        'MISSING_DEPENDENCY': 'Identify the absent dependency and establish its operation and effect bindings.',
        'DYNAMIC_DEPENDENCY': 'Resolve the dynamic target and its effects for the bound scope.',
        'MISSING_LOG_PROVENANCE': 'Establish an independent program, run and log association for this issue.',
        'OTHER': 'Resolve the cited issue against independent source evidence and establish affected effects.',
        'CONTRADICTION': 'Reconcile the conflicting evidence identified by the cited issue before eligibility review.',
    }
    for collection, category in (('unknowns', 'UNKNOWN'), ('contradictions', 'CONTRADICTION')):
        for issue in sorted(graph[collection], key=lambda i: i['issue_id']):
            kind = issue['kind']
            add('DECLARED_' + kind, sorted(issue['operation_ids']), issue_proofs[kind], category,
                source_collection=collection, issue_id=issue['issue_id'], file_keys=sorted(issue['file_keys']))
    return findings


def diagnose(graph, expected_graph_sha256):
    """Bound, inspect and return detached private diagnostics; perform no caller I/O."""
    g = _subject(graph, expected_graph_sha256)
    ops = sorted(g['operations'], key=lambda op: op['sequence'])
    edge_fields = ('edge_id', 'type', 'from_operation_id', 'to_operation_id', 'node_ids', 'evidence_operation_ids')
    edges = [{field: e[field] for field in edge_fields} for e in sorted(g['edges'], key=lambda e: e['edge_id'])]
    dependencies = [e for e in edges if e['type'] != 'RESOURCE']
    reachability, absent, components = _topology(ops, dependencies)
    names = {d['dataset_id']: d['name'].casefold() for d in g['datasets']}
    parents = {**{i: i for i in names}, **{c['column_id']: c['dataset_id'] for c in g['columns']}}
    constraints = [{field: op[field] for field in ('operation_id', 'module_id', 'sequence', 'kind', 'reads', 'writes',
                    'lineage', 'control_lineage', 'stateful_constructs', 'state_effects', 'order_contract',
                    'cardinality', 'numeric_policy', 'interpretation_rules')} |
                   {'fact_kinds': [f['kind'] for f in op['facts']]} for op in ops]
    return dict(algorithm='p3-a1-dependency-diagnostics/1', parent_graph_sha256=expected_graph_sha256,
                subject={k: g[k] for k in ('workspace_id', 'run_id', 'attempt_id', 'source_fingerprint')},
                artifact_authority='DRAFT', semantic_verification='UNVERIFIABLE',
                semantic_acceptance='BLOCKED', benchmark_execution='NOT_RUN',
                limitations=['Digest and record checks bind supplied claims only. Source bytes, inventory, log '
                             'associations, seal, freshness and semantic correctness are not verified.',
                             'Reachability includes unresolved constraints. Absence of a path does not prove independence.',
                             'Conflict witnesses use logical dataset names/parents and declared sequence, not physical '
                             'storage identity, runtime order or versioned instances.'],
                analysis=dict(operation_constraints=constraints, dependencies=dependencies,
                              resource_annotations=[e for e in edges if e['type'] == 'RESOURCE'],
                              node_owners={**{d['dataset_id']: d['module_id'] for d in g['datasets']},
                                           **{c['column_id']: c['module_id'] for c in g['columns']}},
                              column_parents={c['column_id']: c['dataset_id'] for c in g['columns']},
                              statement_coverage=g['statement_coverage'], reachability=reachability,
                              no_path_pairs=absent, components=components,
                              conflicts=_conflicts(ops, dependencies, parents, names), blockers=_blockers(g, ops, edges),
                              eligibility='REJECTED' if g['contradictions'] else 'BLOCKED'))
