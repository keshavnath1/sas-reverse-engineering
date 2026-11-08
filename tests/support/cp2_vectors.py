"""Independent synthetic authorization and original-byte identity vectors use the frozen logical algorithm.

The oracle uses only hashlib/json, never candidate identity helpers or native path access; it does not establish SAS semantics."""

from copy import deepcopy
import hashlib
import json


MAIN = {"file_key": "src:main.sas", "root_id": "src", "path": "main.sas",
        "kind": "SAS", "module_id": "analyze", "encoding": "utf-8"}
INCLUDE = {"file_key": "src:includes/common.sas", "root_id": "src",
           "path": "includes/common.sas", "kind": "INCLUDE",
           "module_id": "prepare", "encoding": "ascii"}
LOG = {"file_key": "logs:run.log", "root_id": "logs", "path": "run.log",
       "kind": "LOG", "module_id": "analyze", "encoding": "utf-8"}
INCLUDE_DEPENDENCY = {"dependency_id": "include-common",
                      "from_file_key": "src:main.sas",
                      "to_file_key": "src:includes/common.sas",
                      "kind": "INCLUDE", "status": "DECLARED"}
MACRO_DEPENDENCY = {"dependency_id": "macro-unresolved",
                    "from_file_key": "src:main.sas", "to_file_key": None,
                    "kind": "MACRO", "status": "UNRESOLVED"}
ASSOCIATION = {"association_id": "log-run", "log_file_key": "logs:run.log",
               "source_file_keys": ["src:includes/common.sas", "src:main.sas"],
               "execution_id": "execution-1", "run_id": "run-1", "status": "DECLARED"}

# This is the exact legacy scope hash preimage, not an I/O authorization Scope:
# it deliberately has no physical root paths. Array order is literal/reviewable.
EXPECTED_PREIMAGE = {
    "schema_version": "1.0", "workspace_id": "synthetic-cp2", "run_id": "run-1",
    "module_ids": ["analyze", "prepare"], "synthetic": True,
    "roots": [{"root_id": "logs"}, {"root_id": "src"}],
    "files": [LOG, INCLUDE, MAIN],
    "dependencies": [INCLUDE_DEPENDENCY, MACRO_DEPENDENCY],
    "log_associations": [ASSOCIATION],
}


def envelope(platform="posix"):
    """Return deliberately unordered declarations and explicit native bindings."""
    logical = deepcopy(EXPECTED_PREIMAGE)
    del logical["schema_version"]
    for key in ("module_ids", "roots", "files", "dependencies"):
        logical[key].reverse()
    logical["log_associations"][0]["source_file_keys"].reverse()
    paths = ({"logs": "/synthetic/logs", "src": "/synthetic/sources"}
             if platform == "posix" else
             {"logs": "C:\\Synthetic\\Logs", "src": "C:\\Synthetic\\Sources"})
    return {
        "authorization_schema_version": "1.0", "identity_projection": "sas-re-scope-v1",
        "platform": platform, "logical_scope": logical,
        "bindings": [{"root_id": key, "platform": platform, "path": paths[key]}
                     for key in ("src", "logs")],
        "authorization": {"declaration_id": "declaration-1", "declared_by": "synthetic-author",
                          "approval_reference": None, "status": "DECLARED",
                          "human_approval": "NOT_VERIFIED", "access": "READ_ONLY"},
    }


def legacy_scope():
    """Shape-valid historical POSIX scope, constructed without filesystem use."""
    value = envelope()
    scope = {"schema_version": "1.0", **deepcopy(value["logical_scope"])}
    scope["roots"] = [{"root_id": binding["root_id"], "path": binding["path"]}
                      for binding in value["bindings"]]
    return scope


def oracle_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def oracle_hash(value):
    return hashlib.sha256(oracle_bytes(value)).hexdigest()


def oracle_id(prefix, fingerprint, payload):
    return prefix + "_" + oracle_hash({"source_fingerprint": fingerprint, "payload": payload})


RAW_MAIN = b"data work.example;\n  value=1;\nrun;\n"
RAW_VARIANTS = {
    "lf": RAW_MAIN,
    "crlf": RAW_MAIN.replace(b"\n", b"\r\n"),
    "bom": b"\xef\xbb\xbf" + RAW_MAIN,
    "changed": RAW_MAIN.replace(b"value=1", b"value=2"),
}
RAW_OTHER = {"logs:run.log": b"NOTE: synthetic execution declaration only.\n",
             "src:includes/common.sas": b"%let synthetic_constant=1;\n"}


def oracle_files(variant="lf", preimage=None):
    """Independent v1 file preimages for the explicit three-line byte vectors."""
    preimage = EXPECTED_PREIMAGE if preimage is None else preimage
    files = []
    for declaration in sorted(preimage["files"], key=lambda item: item["file_key"]):
        main = declaration["file_key"] == "src:main.sas"
        raw = RAW_VARIANTS[variant] if main else RAW_OTHER[declaration["file_key"]]
        entry = {**declaration, "sha256": hashlib.sha256(raw).hexdigest(),
                 "size_bytes": len(raw), "line_count": 3 if main else 1,
                 "newline": "CRLF" if main and variant == "crlf" else "LF"}
        entry["file_id"] = oracle_id("file", "", entry)
        files.append(entry)
    return files


def operation_payload():
    """Fixed supplied facts isolate source-fingerprint binding, not semantics."""
    return {"module_id": "analyze", "kind": "DATA_STEP", "citations": [],
            "reads": [], "writes": [], "stateful_constructs": [],
            "classification": "OBSERVATION", "semantic_verification": "UNVERIFIABLE"}


# Pinned independently before inspecting or executing candidate authorization code.
EXPECTED_SCOPE_SHA256 = "ef0f163ba588eeaf5da718a772f9bed73e5180623bbed575011490df43849e65"
EXPECTED_IDENTITIES = {
    "lf": {
        "main_sha256": "62767855c799df942b4e65966a164565c41c7d580f0105673007b90eb6a34969",
        "main_file_id": "file_c3047b974ba8bcb5f4e892bb15daa8d4be5bbb87a4176a923a3b07bdd17d1efb",
        "source_fingerprint": "1f19783d572d34df0711b6548fb9db9779779390f56fecaef04937aff5fa88e5",
        "operation_id": "op_26432c0b6e4df56acaf0f699c2e36fab87a85f7324ce7f447c71a3b9cd5b5d0b",
    },
    "crlf": {
        "main_sha256": "01e0bc965ac302373fbc4640c879618656ada97772967514867558da866cb1f4",
        "main_file_id": "file_a5371fedb4347dba274ee07e56952fb778b319bff35db90efe75414a85008810",
        "source_fingerprint": "a4060c59299c92bfde5b39b084074bb15cbc145ab35a9070baf4ac842379f57e",
        "operation_id": "op_07a482efae96a2539fecbd4150a4ec981abdd983a8da1bc79253cec2bc80b893",
    },
    "bom": {
        "main_sha256": "bff16ae759750993841627fcce2618d58f50033d3281700a70cf38b027af0db2",
        "main_file_id": "file_e2ba0611a430b1d488b597eb3bd5508ddb7f785da19de8b76ff86e4be68b6ba9",
        "source_fingerprint": "dce8b6466cdb043300cbdbdfe040eff72de5ea38532e54cb539fe266fdbc14d6",
        "operation_id": "op_7a82ee90114d193ee7bd5116d0dc9eb4a250f10d74679187f9d40f18e42bb583",
    },
    "changed": {
        "main_sha256": "97b71236acb199815e8cd8c28c52395be569a77d89498e04dbdefe5d11f9027f",
        "main_file_id": "file_ca945c4fb20d322cce558f807fdb4da99d50b11d7baae851acb67486566b033c",
        "source_fingerprint": "45b176eadcccdfc48f23a2ce75dc123f73314f329081a1b314aed793b2452a6b",
        "operation_id": "op_30b5de466404bb9acda2dafd22d0dba45fabe3818c1205ab9b8b2e06443f2621",
    },
}
