"""Adapter for one fixed public two-module example in private disposable storage."""

from mvp2_expectations import INPUTS, MISSING_INCLUDE, MODULES, SOURCES
from p2a_support import make_case


def make_multi_module_case(root):
    """Build the existing P1 inventory and P2A graph without an evidence store."""
    inputs = [
        {"name": name, "module_id": module, "sorted_by": [],
         "columns": [{"name": col, "type": "NUMERIC", "length": 8} for col in columns],
         "rows": [list(row) for row in rows]}
        for name, module, columns, rows in INPUTS
    ]

    def profile_edit(profile):
        profile["entrypoints"] = ["synthetic:prepare.sas", "synthetic:enrich.sas"]

    def scope_edit(scope):
        scope.update(workspace_id="mvp2-public-workspace", run_id="ordered-measurements",
                     module_ids=list(MODULES))
        owners = {"prepare.sas": "prepare", "enrich.sas": "enrich", "profile.json": "prepare"}
        for entry in scope["files"]:
            entry["module_id"] = owners[entry["path"]]
            if entry["path"] in SOURCES:
                entry["kind"] = "SAS"
        scope["dependencies"] = [
            {"dependency_id": "ordered-input", "from_file_key": "synthetic:enrich.sas",
             "to_file_key": "synthetic:prepare.sas", "kind": "OTHER", "status": "DECLARED"},
            {"dependency_id": "unresolved-postcheck", "from_file_key": "synthetic:enrich.sas",
             "to_file_key": "synthetic:" + MISSING_INCLUDE, "kind": "INCLUDE", "status": "UNRESOLVED"},
        ]

    return make_case(root, {"files": SOURCES, "inputs": inputs}, attempt="preview-2",
                     profile_edit=profile_edit, scope_edit=scope_edit)
