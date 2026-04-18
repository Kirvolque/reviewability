"""Public constants and utilities for filtering non-substantive lines from diffs."""

from __future__ import annotations

from pathlib import Path

EXCLUDED_PREFIXES_BY_EXT: dict[str, tuple[str, ...]] = {
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

FALLBACK_EXCLUDED_PREFIXES: tuple[str, ...] = (
    "import ",
    "#include ",
    "extern crate ",
    "package ",
)


def excluded_prefixes_for(
    file_path: str, prefixes_by_ext: dict[str, list[str]] | None
) -> tuple[str, ...]:
    """Return the line-exclusion prefixes for the given file path.

    Uses ``prefixes_by_ext`` when provided (from config); falls back to the
    built-in ``EXCLUDED_PREFIXES_BY_EXT`` and ``FALLBACK_EXCLUDED_PREFIXES`` otherwise.
    The special key ``"*"`` in ``prefixes_by_ext`` acts as the fallback for unknown extensions.
    """
    ext = Path(file_path).suffix.lower()
    if prefixes_by_ext is not None:
        prefixes = prefixes_by_ext.get(ext) or prefixes_by_ext.get("*") or []
        return tuple(prefixes)
    return EXCLUDED_PREFIXES_BY_EXT.get(ext, FALLBACK_EXCLUDED_PREFIXES)


def meaningful_lines(lines: list[str], prefixes: tuple[str, ...]) -> list[str]:
    """Return lines with blank lines and import/package declarations removed.

    Whitespace is collapsed before matching so indented imports are also
    filtered. The returned lines are normalized (indentation stripped,
    internal whitespace collapsed).
    """
    return [
        normalized
        for line in lines
        if (normalized := " ".join(line.split()))
        if not normalized.startswith(prefixes)
    ]
