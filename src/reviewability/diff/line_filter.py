"""Public constants and utilities for filtering non-substantive lines from diffs.

Import/package declarations and blank lines inflate size metrics without adding
meaningful review burden. Use ``meaningful_lines`` to strip them before computing
any size-based metric.
"""

from __future__ import annotations

from pathlib import Path

IMPORT_PREFIXES_BY_EXT: dict[str, tuple[str, ...]] = {
    ".py": ("import ", "from "),
    ".go": ("import ", "package "),
    ".rs": ("use ", "extern crate ", "mod "),
    ".java": ("import ", "package "),
    ".kt": ("import ", "package "),
    ".scala": ("import ", "package "),
    ".cs": ("using ", "namespace "),
    ".js": ("import ", "from ", "require(", "require "),
    ".ts": ("import ", "from ", "require(", "require "),
    ".jsx": ("import ", "from ", "require(", "require "),
    ".tsx": ("import ", "from ", "require(", "require "),
    ".c": ("#include ",),
    ".h": ("#include ",),
    ".cpp": ("#include ", "using ", "namespace "),
    ".cc": ("#include ", "using ", "namespace "),
    ".hpp": ("#include ", "using ", "namespace "),
    ".rb": ("require ", "require_relative ", "load ", "include ", "prepend "),
    ".php": ("use ", "namespace ", "require ", "require_once ", "include ", "include_once "),
    ".fs": ("open ", "module ", "namespace "),
    ".fsx": ("open ", "module "),
    ".ml": ("open ", "module "),
    ".mli": ("open ", "module "),
    ".swift": ("import ",),
    ".hs": ("import ", "module "),
    ".ex": ("import ", "alias ", "use ", "require "),
    ".exs": ("import ", "alias ", "use ", "require "),
}

FALLBACK_IMPORT_PREFIXES: tuple[str, ...] = (
    "import ",
    "#include ",
    "extern crate ",
    "package ",
)


def import_prefixes(file_path: str) -> tuple[str, ...]:
    """Return the import/package prefixes for the given file extension."""
    ext = Path(file_path).suffix.lower()
    return IMPORT_PREFIXES_BY_EXT.get(ext, FALLBACK_IMPORT_PREFIXES)


def meaningful_lines(lines: list[str], file_path: str) -> list[str]:
    """Return lines with blank lines and import/package declarations removed.

    Whitespace is collapsed before matching so indented imports are also
    filtered. The returned lines are normalized (indentation stripped,
    internal whitespace collapsed).
    """
    prefixes = import_prefixes(file_path)
    return [
        normalized
        for line in lines
        if (normalized := " ".join(line.split()))
        if not normalized.startswith(prefixes)
    ]
