"""Bundled v1 structural contracts; schema success grants no semantic authority."""

from copy import deepcopy
from functools import lru_cache
from importlib.resources import files
import json
import math
from typing import Any

from jsonschema import Draft202012Validator

from .safeio import EvidenceError


@lru_cache(maxsize=1)
def _schema() -> dict[str, Any]:
    """Read only the package resource, never an input-supplied schema or URI."""
    schema = json.loads(
        files("sas_re").joinpath("contracts", "v1", "evidence.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator.check_schema(schema)
    return schema


CONTRACT_NAMES = tuple(_schema()["$defs"])


def load_schema() -> dict[str, Any]:
    """Return a copy so callers cannot modify the process's trusted validators."""
    return deepcopy(_schema())


def _json_value(value: Any) -> bool:
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
def _validator(name: str) -> Draft202012Validator:
    if name not in CONTRACT_NAMES:
        raise EvidenceError("SCHEMA_INVALID")
    schema = _schema()
    return Draft202012Validator(
        {
            "$schema": schema["$schema"],
            "$defs": schema["$defs"],
            "$ref": f"#/$defs/{name}",
        }
    )


def validate_contract(name: str, value: Any) -> None:
    """Reject malformed structure without disclosing supplied values or paths.

    Citation integrity, referential integrity, ownership, freshness and lexical
    path safety require the deterministic verifier in addition to this check.
    P1 semantic_verification is always UNVERIFIABLE, even for a valid contract.
    """
    if not isinstance(name, str) or name not in CONTRACT_NAMES:
        raise EvidenceError("SCHEMA_INVALID")
    try:
        json_value = _json_value(value)
    except RecursionError:
        raise EvidenceError("SCHEMA_INVALID") from None
    if not json_value:
        raise EvidenceError("SCHEMA_INVALID")
    if not _validator(name).is_valid(value):
        raise EvidenceError("SCHEMA_INVALID")
