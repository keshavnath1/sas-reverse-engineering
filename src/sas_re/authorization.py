"""CP2 pure declaration validation and legacy identity projection; never I/O authority.

Only trusted bundled schemas are read. Local root strings are syntax-checked,
not opened or resolved. No evidence workflow accepts this envelope or projection.
"""

from copy import deepcopy
from functools import lru_cache
from importlib.resources import files
import json

from jsonschema import Draft202012Validator

from ._authorization_paths import validate_bindings, validate_file_paths
from ._io_common import EvidenceError, MAX_BYTES, _parse_json, canonical_bytes, safe_relative
from .contracts import _json_value
from .evidence import scope_identity


AUTHORIZATION_SCHEMA_VERSION = "1.0"
IDENTITY_PROJECTION = "sas-re-scope-v1"


@lru_cache(maxsize=1)
def _schema() -> dict:
    schema = json.loads(files("sas_re").joinpath(
        "contracts", "authorization", "v1", "local-authorization.schema.json"
    ).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


def load_authorization_schema() -> dict:
    """A defensive copy of the independently versioned, bundled input contract."""
    return deepcopy(_schema())


@lru_cache(maxsize=3)
def _validator(name: str = "Envelope") -> Draft202012Validator:
    schema = _schema()
    if name == "Envelope":
        return Draft202012Validator(schema)
    return Draft202012Validator({"$schema": schema["$schema"],
                                "$defs": schema["$defs"], "$ref": "#/$defs/" + name})


def _validate_structure(value: object, name: str) -> None:
    try:
        if not _json_value(value) or len(canonical_bytes(value)) > MAX_BYTES:
            raise EvidenceError("AUTHORIZATION_SCHEMA_INVALID")
    except (EvidenceError, RecursionError):
        raise EvidenceError("AUTHORIZATION_SCHEMA_INVALID") from None
    if not _validator(name).is_valid(value):
        raise EvidenceError("AUTHORIZATION_SCHEMA_INVALID")


def _unique(values: list, code: str) -> None:
    if len(values) != len(set(values)):
        raise EvidenceError(code)


def validate_logical_scope(value: object) -> None:
    """Validate logical declarations only. Missing facts are never inferred.

    This is not the historical Scope validator and cannot authorize any file.
    Missing/dynamic dependency targets must explicitly remain UNRESOLVED.
    Unassociated logs stay unassociated; no filename heuristic is applied.
    """
    _validate_structure(value, "LogicalScope")
    roots = [root["root_id"] for root in value["roots"]]
    _unique(roots, "AUTHORIZATION_DUPLICATE_ROOT")
    file_keys = [item["file_key"] for item in value["files"]]
    _unique(file_keys, "AUTHORIZATION_DUPLICATE_FILE")
    validate_file_paths(value["files"])
    for item in value["files"]:
        if item["root_id"] not in roots or item["module_id"] not in value["module_ids"]:
            raise EvidenceError("AUTHORIZATION_OWNER_MISMATCH")
        if item["file_key"] != item["root_id"] + ":" + item["path"]:
            raise EvidenceError("AUTHORIZATION_FILE_KEY_MISMATCH")
    declared = {item["file_key"]: item for item in value["files"]}
    _unique([dep["dependency_id"] for dep in value["dependencies"]],
            "AUTHORIZATION_DUPLICATE_DEPENDENCY")
    for dep in value["dependencies"]:
        if dep["from_file_key"] not in declared:
            raise EvidenceError("AUTHORIZATION_DEPENDENCY_SOURCE_MISSING")
        target = dep["to_file_key"]
        if target is not None:
            # Even unresolved references are literal logical keys, never paths
            # to search, glob, expand or implicitly add to authorized scope.
            try:
                safe_relative(target.split(":", 1)[1])
            except EvidenceError:
                raise EvidenceError("AUTHORIZATION_PATH_INVALID") from None
        if target not in declared and dep["status"] != "UNRESOLVED":
            raise EvidenceError("AUTHORIZATION_UNRESOLVED_REQUIRED")
    _unique([link["association_id"] for link in value["log_associations"]],
            "AUTHORIZATION_DUPLICATE_ASSOCIATION")
    linked = set()
    for link in value["log_associations"]:
        if link["run_id"] != value["run_id"]:
            raise EvidenceError("AUTHORIZATION_LOG_RUN_MISMATCH")
        key = link["log_file_key"]
        if key in linked:
            raise EvidenceError("AUTHORIZATION_LOG_AMBIGUOUS", "BLOCKED")
        if key not in declared or declared[key]["kind"] not in {"LOG", "LST"}:
            raise EvidenceError("AUTHORIZATION_LOG_FILE_MISMATCH")
        if any(source not in declared or declared[source]["kind"] not in {"SAS", "INCLUDE"}
               for source in link["source_file_keys"]):
            raise EvidenceError("AUTHORIZATION_LOG_SOURCE_MISSING")
        linked.add(key)


def validate_authorization(value: object, *, expected_platform: str | None = None) -> None:
    """Check declarations, not human approval, physical identity or permission.

    `expected_platform` is an optional explicit caller expectation, never host
    detection. Both syntaxes can be inspected on any host. No bindings are applied.
    Success returns None, not an access token, handle or evidence stage PASS.
    """
    if type(value) is dict:
        for field, supported, code in (
            ("authorization_schema_version", AUTHORIZATION_SCHEMA_VERSION,
             "AUTHORIZATION_VERSION_UNSUPPORTED"),
            ("identity_projection", IDENTITY_PROJECTION, "AUTHORIZATION_IDENTITY_UNSUPPORTED"),
        ):
            if type(value.get(field)) is str and value[field] != supported:
                raise EvidenceError(code, "BLOCKED")
    _validate_structure(value, "Envelope")
    if expected_platform is not None and (
        type(expected_platform) is not str or expected_platform not in {"posix", "windows"}
        or expected_platform != value["platform"]
    ):
        raise EvidenceError("AUTHORIZATION_PLATFORM_MISMATCH")
    validate_logical_scope(value["logical_scope"])
    root_ids = {root["root_id"] for root in value["logical_scope"]["roots"]}
    binding_ids = [binding["root_id"] for binding in value["bindings"]]
    if len(binding_ids) != len(set(binding_ids)) or set(binding_ids) != root_ids:
        raise EvidenceError("AUTHORIZATION_BINDING_MISMATCH")
    if any(binding["platform"] != value["platform"] for binding in value["bindings"]):
        raise EvidenceError("AUTHORIZATION_PLATFORM_MISMATCH")
    validate_bindings(value["platform"], value["bindings"])
    paths = {binding["root_id"]: binding["path"] for binding in value["bindings"]}
    for item in value["logical_scope"]["files"]:
        # Pure string bound only; never instantiate, resolve or open this path.
        full = paths[item["root_id"]] + "/" + item["path"]
        size = (len(full.encode("utf-16-le")) // 2 if value["platform"] == "windows"
                else len(full.encode("utf-8")))
        if size > (259 if value["platform"] == "windows" else 4096):
            raise EvidenceError("AUTHORIZATION_PATH_INVALID")


def parse_authorization(raw: bytes, *, expected_platform: str | None = None) -> dict:
    """Validate caller-supplied strict UTF-8 JSON bytes, without opening a path."""
    if type(raw) is not bytes or len(raw) > MAX_BYTES:
        raise EvidenceError("AUTHORIZATION_SCHEMA_INVALID")
    try:
        value = _parse_json(raw)
    except EvidenceError:
        raise EvidenceError("AUTHORIZATION_SCHEMA_INVALID") from None
    validate_authorization(value, expected_platform=expected_platform)
    return value


def project_logical_scope(value: object, *, expected_platform: str | None = None) -> dict:
    """Return deterministic legacy-v1 hash input, deliberately NOT an I/O Scope.

    The explicit projection version freezes this field selection and sorting.
    No native roots, declaration metadata or transient filesystem IDs are copied.
    Any future incompatible projection requires a new version and revision map.
    """
    validate_authorization(value, expected_platform=expected_platform)
    projected = {"schema_version": "1.0", **deepcopy(value["logical_scope"])}
    projected["roots"].sort(key=lambda item: item["root_id"])
    projected["module_ids"].sort()
    for field, key in (("files", "file_key"), ("dependencies", "dependency_id"),
                       ("log_associations", "association_id")):
        projected[field].sort(key=lambda item: item[key])
    for link in projected["log_associations"]:
        link["source_file_keys"].sort()
    _validate_structure(projected, "LegacyScopeIdentityInput")
    return projected


def authorization_scope_identity(value: object, *, expected_platform: str | None = None) -> str:
    """Use the unchanged P1 algorithm on the validated, explicit projection."""
    return scope_identity(project_logical_scope(value, expected_platform=expected_platform))
