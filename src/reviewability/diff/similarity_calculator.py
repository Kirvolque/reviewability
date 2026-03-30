from __future__ import annotations

import difflib
from dataclasses import dataclass, field

from rapidfuzz import fuzz


@dataclass(frozen=True)
class DiffSimilarityCalculator:
    """Shared similarity helpers for diff-structure detectors."""

    pair_similarity_cache: dict[tuple[int, int], float] = field(
        default_factory=dict,
        init=False,
        repr=False,
        compare=False,
    )

    def sequence_similarity(
        self, a: list[str] | tuple[str, ...], b: list[str] | tuple[str, ...]
    ) -> float:
        """Sequence similarity ratio in ``[0.0, 1.0]``."""
        return difflib.SequenceMatcher(None, a, b).ratio()

    def move_aware_similarity(self, deleted_lines: list[str], added_lines: list[str]) -> float:
        """Compute similarity by matching deleted lines to added lines individually.

        Phase 1 matches identical lines via dict lookup (O(D+A), score=1.0).
        Phase 2 matches remaining lines via rapidfuzz.fuzz.ratio (O(D'×A'×L)).
        Greedy best-match selection, normalized by the larger line count.

        Score range: 0.0–1.0
          1.0 → identical lines (pure move)
          0.5–0.9 → modified lines
          0.0 → completely different or either side is empty
        """
        if not deleted_lines or not added_lines:
            return 0.0

        used_del, used_add, total = self._match_exact(deleted_lines, added_lines)

        remaining_del = [(i, deleted_lines[i]) for i in range(len(deleted_lines)) if i not in used_del]
        remaining_add = [(j, added_lines[j]) for j in range(len(added_lines)) if j not in used_add]
        total += self._match_approximate(remaining_del, remaining_add, used_del, used_add)

        return total / max(len(deleted_lines), len(added_lines))

    def _match_exact(
        self,
        deleted_lines: list[str],
        added_lines: list[str],
    ) -> tuple[set[int], set[int], float]:
        """Phase 1: match identical lines via dict lookup — O(D + A).

        Returns (used_del, used_add, total_score). Exact matches score 1.0
        and are excluded from the approximate phase.
        """
        add_index: dict[str, list[int]] = {}
        for j, line in enumerate(added_lines):
            add_index.setdefault(line, []).append(j)

        used_del: set[int] = set()
        used_add: set[int] = set()
        total = 0.0
        for i, del_line in enumerate(deleted_lines):
            if del_line in add_index:
                candidates = [j for j in add_index[del_line] if j not in used_add]
                if candidates:
                    used_del.add(i)
                    used_add.add(candidates[0])
                    total += 1.0
        return used_del, used_add, total

    def _match_approximate(
        self,
        remaining_del: list[tuple[int, str]],
        remaining_add: list[tuple[int, str]],
        used_del: set[int],
        used_add: set[int],
    ) -> float:
        """Phase 2: match remaining lines via rapidfuzz.fuzz.ratio — O(D' × A' × L).

        Uses the same LCS-based similarity as difflib.SequenceMatcher but implemented
        in C via rapidfuzz. Scores all pairs >= 0.3, greedily selects best
        non-overlapping matches, and returns the total score contribution.
        """
        if not remaining_del or not remaining_add:
            return 0.0

        scored: list[tuple[float, int, int]] = []
        for i, del_line in remaining_del:
            for j, add_line in remaining_add:
                score = fuzz.ratio(del_line, add_line) / 100
                if score >= 0.3:
                    scored.append((score, i, j))

        scored.sort(reverse=True, key=lambda x: x[0])
        total = 0.0
        for score, i, j in scored:
            if i not in used_del and j not in used_add:
                used_del.add(i)
                used_add.add(j)
                total += score
        return total
