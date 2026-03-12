from __future__ import annotations

import difflib
from dataclasses import dataclass
from pathlib import Path

from reviewability.domain.models import FileDiff, Hunk

# Import/package declaration prefixes per file extension.
# Only applied when the extension is known — avoids false positives from ambiguous
# keywords like `open`, `load`, `include` that are also common function names.
_PREFIXES_BY_EXT: dict[str, tuple[str, ...]] = {
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

# Conservative fallback for unknown extensions: only unambiguous prefixes.
_FALLBACK_PREFIXES: tuple[str, ...] = (
    "import ",
    "#include ",
    "extern crate ",
    "package ",
)


def _import_prefixes(file_path: str) -> tuple[str, ...]:
    ext = Path(file_path).suffix.lower()
    return _PREFIXES_BY_EXT.get(ext, _FALLBACK_PREFIXES)


def _normalize(line: str) -> str:
    """Strip indentation and collapse internal whitespace."""
    return " ".join(line.split())


def _content_lines(lines: list[str], file_path: str) -> list[str]:
    """Normalize lines, dropping blank lines and import/package declarations."""
    prefixes = _import_prefixes(file_path)
    result = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(prefixes):
            continue
        result.append(_normalize(line))
    return result


def _similarity(a: list[str], b: list[str]) -> float:
    """Sequence similarity ratio in [0.0, 1.0]."""
    return difflib.SequenceMatcher(None, a, b).ratio()


@dataclass(frozen=True)
class MovementDetector:
    """Detects whether two hunks or two files are likely a code movement.

    A movement is when code is deleted from one location and inserted at another,
    possibly with indentation or formatting changes, without meaningful logic changes.

    Ignores:
    - Indentation and whitespace formatting
    - Import/package/module declarations (which often change when files move)
    - Hunks with fewer than ``hunk_min_lines`` content lines
    - Files with fewer than ``file_min_lines`` content lines

    Returns False (not a movement) for inputs below the minimum line thresholds,
    treating small blocks as independent changes to avoid false positives.
    """

    hunk_min_lines: int = 8
    """Minimum content lines required to consider a hunk for movement detection."""

    file_min_lines: int = 15
    """Minimum content lines (excluding imports) to consider a file for movement detection."""

    similarity_threshold: float = 0.95
    """Fraction of lines that must match for two blocks to be considered a likely movement."""

    def hunks_are_likely_moved(self, deletion: Hunk, insertion: Hunk) -> bool:
        """Return True if ``insertion`` is likely a moved version of ``deletion``.

        ``deletion`` must be a pure-removal hunk (no added lines) and ``insertion`` must be a
        pure-addition hunk (no removed lines). Returns False if either condition is not met.
        """
        if deletion.added_count != 0 or insertion.removed_count != 0:
            return False

        a = _content_lines(deletion.removed_lines, deletion.file_path)
        b = _content_lines(insertion.added_lines, insertion.file_path)

        if len(a) < self.hunk_min_lines or len(b) < self.hunk_min_lines:
            return False

        return _similarity(a, b) >= self.similarity_threshold

    def files_are_likely_moved(self, deleted: FileDiff, added: FileDiff) -> bool:
        """Return True if ``added`` is likely a moved version of ``deleted``.

        ``deleted`` must be a deleted file and ``added`` must be a new file.
        Returns False if either condition is not met.

        Import and package declarations are excluded from comparison, as they commonly
        change when a file is relocated within a project.
        """
        if not deleted.is_deleted_file or not added.is_new_file:
            return False

        a = _content_lines([line for h in deleted.hunks for line in h.removed_lines], deleted.path)
        b = _content_lines([line for h in added.hunks for line in h.added_lines], added.path)

        if len(a) < self.file_min_lines or len(b) < self.file_min_lines:
            return False

        return _similarity(a, b) >= self.similarity_threshold
