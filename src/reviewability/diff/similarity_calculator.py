from __future__ import annotations

import difflib
from dataclasses import dataclass, field

from reviewability.diff.line_filter import meaningful_lines


@dataclass(frozen=True)
class DiffSimilarityCalculator:
    """Shared normalization and similarity helpers for diff-structure detectors.

    This class exists to keep movement detection and deep-edit detection aligned:
    both should normalize whitespace consistently, ignore import/package noise,
    and use the same notion of sequence similarity.
    """

    pair_similarity_cache: dict[tuple[int, int], float] = field(
        default_factory=dict,
        init=False,
        repr=False,
        compare=False,
    )

    def content_lines(self, lines: list[str], file_path: str) -> list[str]:
        """Return lines with blank lines and import/package declarations removed."""
        return meaningful_lines(lines, file_path)

    def sequence_similarity(
        self, a: list[str] | tuple[str, ...], b: list[str] | tuple[str, ...]
    ) -> float:
        """Sequence similarity ratio in ``[0.0, 1.0]``."""
        return difflib.SequenceMatcher(None, a, b).ratio()

    def move_aware_similarity(self, deleted_lines: list[str], added_lines: list[str]) -> float:
        """Compute similarity by matching deleted lines to added lines individually.

        For every (deleted, added) line pair, computes a normalized character-level
        similarity score. Finds the best non-overlapping matches greedily (highest
        score first). Normalizes the total matched score by the larger of the two
        line counts.

        Score range: 0.0–1.0
          1.0 → identical lines (pure move)
          0.5–0.9 → modified lines
          0.0 → completely different or either side is empty
        """
        if not deleted_lines or not added_lines:
            return 0.0

        scored: list[tuple[float, int, int]] = []
        for i, del_line in enumerate(deleted_lines):
            for j, add_line in enumerate(added_lines):
                score = difflib.SequenceMatcher(None, del_line, add_line).ratio()
                scored.append((score, i, j))

        scored.sort(reverse=True, key=lambda x: x[0])

        used_del: set[int] = set()
        used_add: set[int] = set()
        total = 0.0
        for score, i, j in scored:
            if i not in used_del and j not in used_add:
                used_del.add(i)
                used_add.add(j)
                total += score

        return total / max(len(deleted_lines), len(added_lines))
