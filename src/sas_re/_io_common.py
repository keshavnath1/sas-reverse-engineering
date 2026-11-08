"""Import-safe evidence primitives; moved without changing byte or error rules."""

import json
import re


MAX_BYTES = 8 * 1024 * 1024


MAX_FILES = 1000


MAX_DEPTH = 32


MAX_DIRECTORIES = 1000


ARTIFACT_NAMES = frozenset(
    {
        "source_inventory.json",
        "source_record.json",
        "validation_report.json",
        "verification_report.json",
    }
)


_COMPONENT = re.compile(r"[A-Za-z0-9_.-]{1,128}\Z", re.ASCII)


_CODE = re.compile(r"[A-Z][A-Z0-9_]{0,79}\Z", re.ASCII)


class EvidenceError(Exception):
    """Public errors contain a fixed diagnostic code, never input contents."""

    def __init__(self, code: str, gate: str = "FAIL") -> None:
        self.code = (
            code if isinstance(code, str) and _CODE.fullmatch(code) else "INVALID_ERROR_CODE"
        )
        self.gate = gate if gate in {"FAIL", "BLOCKED"} else "FAIL"
        super().__init__(self.code)


def safe_relative(relative: str) -> str:
    """Validate a portable, unambiguous, POSIX-relative file or directory name."""
    if not isinstance(relative, str) or not relative or len(relative) > 4096:
        raise EvidenceError("UNSAFE_PATH")
    parts = relative.split("/")
    if any(part in {".", ".."} or not _COMPONENT.fullmatch(part) for part in parts):
        raise EvidenceError("UNSAFE_PATH")
    if len(parts) > MAX_DEPTH:
        raise EvidenceError("PATH_DEPTH_LIMIT")
    return relative


def _identifier(value: str) -> str:
    if safe_relative(value) != value or "/" in value:
        raise EvidenceError("UNSAFE_ID")
    return value


def _json_depth(value: object, depth: int = 0) -> None:
    if depth > 64:
        raise EvidenceError("JSON_DEPTH_LIMIT")
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise EvidenceError("JSON_INVALID")
            _json_depth(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            _json_depth(child, depth + 1)


def canonical_bytes(obj: object) -> bytes:
    """Canonical local JSON policy: sorted compact UTF-8, finite numbers, final LF."""
    try:
        _json_depth(obj)
        return (
            json.dumps(
                obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise EvidenceError("JSON_INVALID") from None


def _parse_json(raw: bytes) -> object:
    def pairs(items: list[tuple[str, object]]) -> dict:
        result = {}
        for key, value in items:
            if key in result:
                raise EvidenceError("JSON_DUPLICATE_KEY")
            result[key] = value
        return result

    def nonfinite(_: str) -> None:
        raise EvidenceError("JSON_NONFINITE")

    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=nonfinite)
        _json_depth(value)
        # JSON's exponent syntax can overflow Python floats without parse_constant.
        canonical_bytes(value)
        return value
    except (ValueError, UnicodeError, RecursionError):
        raise EvidenceError("JSON_INVALID") from None
