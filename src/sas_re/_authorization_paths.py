"""Pure CP2 path declarations; successful syntax checks never authorize I/O.

Native paths are opaque local binding data. Comparisons reject a conservative
set of lexical aliases without rewriting caller values. They cannot establish
physical identity, permissions, filesystem type or absence of reparse points.
"""

import re
import unicodedata

from ._io_common import EvidenceError, MAX_FILES, safe_relative


_DRIVE = re.compile(r"[A-Z]:\\", re.ASCII)
_WINDOWS_FORBIDDEN = frozenset('<>:"/\\|?*')
_EXPANSIONS = frozenset("$%~")
_DEVICES = frozenset({
    "con", "prn", "aux", "nul", "conin$", "conout$",
    *("com" + digit for digit in "123456789¹²³"),
    *("lpt" + digit for digit in "123456789¹²³"),
})


def _invalid() -> None:
    raise EvidenceError("AUTHORIZATION_PATH_INVALID")


def _alias() -> None:
    raise EvidenceError("AUTHORIZATION_PATH_ALIAS")


def _text(value: object) -> str:
    if type(value) is not str or not value:
        _invalid()
    if any(unicodedata.category(char) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
           for char in value):
        _invalid()
    return value


def _comparison(value: str) -> str:
    # Comparison-only screening, not a claim about any native collation table.
    return unicodedata.normalize("NFC", unicodedata.normalize("NFC", value).casefold())


def _portable_component(part: str) -> None:
    if (part in {".", ".."} or not part or part.endswith((".", " "))
            or any(char in _WINDOWS_FORBIDDEN | _EXPANSIONS for char in part)
            or part.split(".", 1)[0].rstrip(" .").casefold() in _DEVICES):
        _invalid()


def _native_parts(platform: str, path: object) -> tuple[str, ...]:
    value = _text(path)
    if any(char in _EXPANSIONS for char in value):
        _invalid()
    if platform == "windows":
        # Non-extended Win32 spelling only. UTF-16 units include surrogate pairs;
        # unpaired surrogates were rejected above. The NUL is not in this string.
        if len(value.encode("utf-16-le")) // 2 > 259 or not _DRIVE.match(value):
            _invalid()
        parts = value[3:].split("\\")
        for part in parts:
            _portable_component(part)
            if len(part.encode("utf-16-le")) // 2 > 255:
                _invalid()
        return (value[:2], *parts)
    if platform == "posix":
        if (len(value.encode("utf-8")) > 4096 or not value.startswith("/")
                or value.startswith("//") or "\\" in value):
            _invalid()
        parts = value[1:].split("/")
        if any(not part or part in {".", ".."} or len(part.encode("utf-8")) > 255
               for part in parts):
            _invalid()
        return tuple(parts)
    _invalid()


class _Node:
    """A bounded, iterative comparison trie; no path object is constructed."""

    def __init__(self) -> None:
        self.children: dict[str, tuple[str, _Node]] = {}
        self.terminal = False

    def insert(self, parts: tuple[str, ...]) -> None:
        node = self
        for part in parts:
            if node.terminal:
                _alias()
            key = _comparison(part)
            if key in node.children:
                spelling, child = node.children[key]
                if spelling != part:
                    _alias()
            else:
                child = _Node()
                node.children[key] = (part, child)
            node = child
        if node.terminal or node.children:
            _alias()
        node.terminal = True


def validate_bindings(platform: str, bindings: list[dict]) -> None:
    """Validate explicit native root syntax and detectable lexical aliases only.

    The platform is declaration data, never inferred from this host. Even a
    successful return leaves physical filesystem authorization unestablished.
    """
    if type(platform) is not str or platform not in {"windows", "posix"} or type(bindings) is not list:
        _invalid()
    if not 1 <= len(bindings) <= MAX_FILES:
        _invalid()
    tree = _Node()
    root_ids = set()
    for binding in bindings:
        if type(binding) is not dict or binding.get("platform") != platform:
            _invalid()
        root_id = _text(binding.get("root_id"))
        if root_id in root_ids:
            _alias()
        root_ids.add(root_id)
        tree.insert(_native_parts(platform, binding.get("path")))


def validate_file_paths(files: list[dict]) -> None:
    """Check the portable ASCII relative subset, without changing legacy rules.

    Only this new envelope uses the stricter Windows-compatible component and
    alias policy. The frozen evidence reader's safe_relative is unchanged.
    """
    if type(files) is not list or not 1 <= len(files) <= MAX_FILES:
        _invalid()
    trees: dict[str, _Node] = {}
    for declaration in files:
        if type(declaration) is not dict:
            _invalid()
        root_id = _text(declaration.get("root_id"))
        path = _text(declaration.get("path"))
        try:
            safe_relative(path)
        except EvidenceError:
            _invalid()
        parts = tuple(path.split("/"))
        for part in parts:
            _portable_component(part)
        trees.setdefault(root_id, _Node()).insert(parts)
