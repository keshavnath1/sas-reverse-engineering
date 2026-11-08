"""Bundled v1/v2 structural contracts, including authorization record schemas.

Packaged JSON schemas remain the authority for record structure. Passing these
checks grants no publication permission or semantic authority, and does not
execute SAS or establish SAS equivalence.
"""

from copy import deepcopy
from functools import lru_cache
from importlib.resources import files
import json
import math
from typing import Any

from jsonschema import Draft202012Validator

from .safeio import EvidenceError


@lru_cache(maxsize=2)
def _schema(version: str = "1.0") -> dict[str, Any]:
    """Read and cache a package schema, never an input-supplied schema or URI."""
    if version not in {"1.0", "2.0"}:
        raise EvidenceError("SCHEMA_INVALID")
    schema = json.loads(
        files("sas_re")
        .joinpath("contracts", "v" + version[0], "evidence.schema.json")
        .read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    return schema


# Keep the exported names tied to the default v1 schema, not a union of versions.
CONTRACT_NAMES = tuple(_schema()["$defs"])


def load_schema(version: str = "1.0") -> dict[str, Any]:
    """Return a caller-owned copy of a bundled schema.

    Reads the package resource on a cache miss; modifying the returned nested
    objects cannot change the cached schema used by trusted validators.

    Args:
        version: Bundled schema version, either "1.0" or "2.0".

    Returns:
        A deep copy of the selected JSON schema.

    Raises:
        EvidenceError: If the requested version is unsupported.
    """
    return deepcopy(_schema(version))


def _json_value(value: Any) -> bool:
    """Accept only JSON-shaped built-in values, with finite floating-point numbers."""
    # Exact types exclude custom subclasses and their overridden behavior.
    if value is None or type(value) in (str, bool, int):
        return True
    if type(value) is float:
        return math.isfinite(value)
    if type(value) is list:
        return all(_json_value(item) for item in value)
    if type(value) is dict:
        return all(type(key) is str and _json_value(item) for key, item in value.items())
    return False


@lru_cache(maxsize=None)
def _validator(name: str, version: str = "1.0") -> Draft202012Validator:
    """Cache a validator for a definition in the selected bundled schema."""
    schema = _schema(version)
    if name not in schema["$defs"]:
        raise EvidenceError("SCHEMA_INVALID")
    return Draft202012Validator(
        {
            "$schema": schema["$schema"],
            "$defs": schema["$defs"],
            "$ref": f"#/$defs/{name}",
        }
    )


def validate_contract(name: str, value: Any, *, version: str = "1.0") -> None:
    """Reject malformed structure without disclosing supplied values or paths.

    Does not mutate the supplied record. Citation integrity, referential
    integrity, ownership, freshness and lexical path safety require the
    deterministic verifier in addition to this check. P1 semantic_verification
    is always UNVERIFIABLE, even for a valid contract. Authorization record
    structure alone does not confer approval or permission to publish.

    Args:
        name: Definition name in the selected bundled schema.
        value: Record to check for JSON-compatible values and schema structure.
        version: Bundled schema version; defaults to the v1 boundary.

    Returns:
        None if the value satisfies the selected structural contract.

    Raises:
        EvidenceError: With SCHEMA_INVALID for invalid selectors, non-JSON
            values, excessive recursion, or a schema mismatch.
    """
    if not isinstance(name, str) or not isinstance(version, str):
        raise EvidenceError("SCHEMA_INVALID")
    try:
        json_value = _json_value(value)
    except RecursionError:
        # Cycles and excessive nesting share the same non-disclosing refusal.
        raise EvidenceError("SCHEMA_INVALID") from None
    if not json_value:
        raise EvidenceError("SCHEMA_INVALID")
    if not _validator(name, version).is_valid(value):
        raise EvidenceError("SCHEMA_INVALID")


def validate_versioned_contract(name: str, value: Any) -> None:
    """Opt into record-selected validation without changing P1's v1 boundary.

    Does not mutate the record or infer a missing version. Dispatch selects only
    a bundled schema; a record cannot supply a schema document or location.

    Args:
        name: Definition name to validate in the record's schema version.
        value: Built-in dict with a built-in string schema_version field.

    Returns:
        None if the record satisfies the selected structural contract.

    Raises:
        EvidenceError: With SCHEMA_INVALID if dispatch fields are malformed or
            the delegated structural validation refuses the record.
    """
    if type(value) is not dict or type(value.get("schema_version")) is not str:
        raise EvidenceError("SCHEMA_INVALID")
    validate_contract(name, value, version=value["schema_version"])
