from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from pathlib import Path

from reviewability.domain.models import Hunk


@dataclass(frozen=True)
class DiffSimilarityCalculator:
    """Shared normalization and similarity helpers for diff-structure detectors.

    This class exists to keep movement detection and deep-edit detection aligned:
    both should normalize whitespace consistently, ignore import/package noise,
    and use the same notion of sequence similarity.
    """

    prefixes_by_ext: dict[str, tuple[str, ...]] | None = None
    fallback_prefixes: tuple[str, ...] = (
        "import ",
        "#include ",
        "extern crate ",
        "package ",
    )
    pair_similarity_cache: dict[tuple[int, int], float] = field(
        default_factory=dict,
        init=False,
        repr=False,
        compare=False,
    )

    def import_prefixes(self, file_path: str) -> tuple[str, ...]:
        ext = Path(file_path).suffix.lower()
        prefixes = self.prefixes_by_ext or _DEFAULT_PREFIXES_BY_EXT
        return prefixes.get(ext, self.fallback_prefixes)

    def normalize_line(self, line: str) -> str:
        """Strip indentation and collapse internal whitespace."""
        return " ".join(line.split())

    def content_lines(self, lines: list[str], file_path: str) -> list[str]:
        """Normalize lines, dropping blanks and import/package declarations."""
        prefixes = self.import_prefixes(file_path)
        return [
            normalized
            for line in lines
            if (normalized := self.normalize_line(line))
            if not normalized.startswith(prefixes)
        ]

    def changed_lines(self, hunk: Hunk, *, prefer_removed: bool) -> tuple[str, ...]:
        """Return normalized changed lines from one side of a hunk.

        If the preferred side is empty, the opposite side is used as a fallback.
        This makes the helper usable for standalone hunk-to-hunk comparisons where
        one side may be mostly additions and the other mostly removals.
        """
        primary = hunk.removed_lines if prefer_removed else hunk.added_lines
        fallback = hunk.added_lines if prefer_removed else hunk.removed_lines
        return tuple(self.content_lines(primary or fallback, hunk.file_path))

    def sequence_similarity(self, a: list[str] | tuple[str, ...], b: list[str] | tuple[str, ...]) -> float:
        """Sequence similarity ratio in ``[0.0, 1.0]``."""
        return difflib.SequenceMatcher(None, a, b).ratio()

    def pair_sequence_similarity(
        self,
        deletion_id: int,
        addition_id: int,
        deletion_lines: list[str] | tuple[str, ...],
        addition_lines: list[str] | tuple[str, ...],
    ) -> float:
        """Return cached sequence similarity for one ordered deletion/addition pair."""
        pair_key = (deletion_id, addition_id)
        similarity = self.pair_similarity_cache.get(pair_key)
        if similarity is not None:
            return similarity

        similarity = self.sequence_similarity(deletion_lines, addition_lines)
        self.pair_similarity_cache[pair_key] = similarity
        return similarity

    def token_overlap(self, a: tuple[str, ...], b: tuple[str, ...]) -> float:
        """Return a simple overlap score over identifier-like tokens."""
        left = frozenset(self._tokenize_lines(a))
        right = frozenset(self._tokenize_lines(b))
        if not left or not right:
            return 0.0
        return len(left & right) / min(len(left), len(right))

    def _tokenize_lines(self, lines: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(
            token.lower()
            for line in lines
            for token in self._split_identifierish_tokens(line)
            if len(token) >= 2
        )

    def _split_identifierish_tokens(self, line: str) -> tuple[str, ...]:
        return tuple("".join(ch if ch.isalnum() or ch == "_" else " " for ch in line).split())


_DEFAULT_PREFIXES_BY_EXT: dict[str, tuple[str, ...]] = {
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
