"""Detects hunks that are logically connected (moves, rewrites, splits/merges)."""

from __future__ import annotations

from dataclasses import dataclass

from reviewability.diff.similarity_calculator import DiffSimilarityCalculator
from reviewability.domain.models import Hunk, Move, MoveType

_PURE_SIMILARITY_THRESHOLD = 0.9
# Filtered lines for a single hunk: (removed, added) after blank/import stripping.
_HunkContent = tuple[list[str], list[str]]


@dataclass(frozen=True)
class MoveDetector:
    """Detects hunks that are logically connected by move-aware diff similarity.

    Pairs deletion and insertion hunks using move_aware_similarity (threshold >= 0.3).
    Uses union-find to merge pairs into connected components.
    Returns only multi-hunk moves; ungrouped (singleton) hunks are omitted.
    """

    similarity_calculator: DiffSimilarityCalculator

    def detect(self, hunks: list[Hunk]) -> list[Move]:
        """Detect moves by move-aware diff similarity.

        For every pair of hunks, computes move_aware_similarity between one hunk's
        removed lines and the other's added lines (and vice versa). Pairs with
        similarity >= 0.3 are candidates; greedy best-match selects the best
        non-overlapping pairs.

        Returns list[Move] containing only multi-hunk moves; singletons are omitted.
        """
        if not hunks:
            return []

        # Pre-compute content tuples for all hunk pairs.
        hunk_content = self._precompute_content(hunks)

        scored_pairs = self._score_all_pairs(hunk_content)
        accepted_pairs = self._greedy_match(scored_pairs)

        parent = self._initialize_union_find(len(hunks))
        match_by_root: dict[int, tuple[int, int, float]] = {}
        for source_index, target_index, similarity in accepted_pairs:
            parent = self._union(parent, source_index, target_index)
            root = self._find(parent, source_index)
            match_by_root[root] = (source_index, target_index, similarity)

        root_to_move = self._assign_move_ids(parent, len(hunks))
        return self._build_result(hunks, hunk_content, parent, root_to_move, match_by_root)

    def _precompute_content(self, hunks: list[Hunk]) -> list[_HunkContent]:
        """Return pre-filtered lines for each hunk (filtering already done at parse time)."""
        return [(h.removed_lines, h.added_lines) for h in hunks]

    def _score_all_pairs(
        self, hunk_content: list[_HunkContent]
    ) -> list[tuple[float, int, int]]:
        """Score all hunk pairs using pre-filtered lines.

        For each pair, computes both deleted-to-added directions and preserves the
        higher-scoring source/target orientation.
        Empty line lists produce 0.0, so two pure additions or two pure deletions never pair.
        Returns list of (similarity, i, j) with i < j, sorted descending by similarity.
        """
        calc = self.similarity_calculator
        scored: list[tuple[float, int, int]] = []

        for i in range(len(hunk_content)):
            i_removed, i_added = hunk_content[i]
            for j in range(i + 1, len(hunk_content)):
                j_removed, j_added = hunk_content[j]
                sim_ij = calc.move_aware_similarity(i_removed, j_added)
                sim_ji = calc.move_aware_similarity(j_removed, i_added)
                sim, source_index, target_index = (
                    (sim_ij, i, j) if sim_ij >= sim_ji else (sim_ji, j, i)
                )
                if sim >= 0.3:  # Low threshold: metric layer handles scoring nuance
                    scored.append((sim, source_index, target_index))

        scored.sort(reverse=True, key=lambda x: x[0])
        return scored

    def _greedy_match(
        self,
        scored_pairs: list[tuple[float, int, int]],
    ) -> list[tuple[int, int, float]]:
        """Greedily select best unmatched pairs, preserving the similarity score.

        Each hunk index appears in at most one accepted pair.
        Returns list of (source_index, target_index, similarity).
        """
        matched: set[int] = set()
        pairs: list[tuple[int, int, float]] = []

        for similarity, source_index, target_index in scored_pairs:
            if source_index not in matched and target_index not in matched:
                pairs.append((source_index, target_index, similarity))
                matched.add(source_index)
                matched.add(target_index)

        return pairs

    def _initialize_union_find(self, size: int) -> dict[int, int]:
        """Initialize union-find parent map where each index is its own root."""
        return {i: i for i in range(size)}

    def _find(self, parent: dict[int, int], x: int) -> int:
        """Find root of x with path compression."""
        if parent[x] != x:
            parent[x] = self._find(parent, parent[x])
        return parent[x]

    def _union(self, parent: dict[int, int], x: int, y: int) -> dict[int, int]:
        """Union two elements by their root. Returns the modified parent dict."""
        rx, ry = self._find(parent, x), self._find(parent, y)
        if rx != ry:
            parent[rx] = ry
        return parent

    def _assign_move_ids(self, parent: dict[int, int], size: int) -> dict[int, int]:
        """Assign unique move_id to each root."""
        root_to_move: dict[int, int] = {}
        next_move_id = 0

        for i in range(size):
            root = self._find(parent, i)
            if root not in root_to_move:
                root_to_move[root] = next_move_id
                next_move_id += 1

        return root_to_move

    def _build_result(
        self,
        hunks: list[Hunk],
        hunk_content: list[_HunkContent],
        parent: dict[int, int],
        root_to_move: dict[int, int],
        match_by_root: dict[int, tuple[int, int, float]],
    ) -> list[Move]:
        """Build Move list from union-find result.

        Only multi-hunk moves are returned; singletons (ungrouped hunks) are omitted.
        Multi-hunk moves retain their source/target hunks and residual lines not
        explained by exact correspondence. A move is pure only when it has high
        similarity and no residual edits; a fuzzy match must not hide a rewrite.
        """
        buckets: dict[int, list[int]] = {}
        for i in range(len(hunks)):
            root = self._find(parent, i)
            buckets.setdefault(root, []).append(i)

        hunk_changed_line_counts = [
            len(removed_lines) + len(added_lines)
            for removed_lines, added_lines in hunk_content
        ]
        result: list[Move] = []
        for root, indices in buckets.items():
            if len(indices) <= 1:
                continue

            source_index, target_index, similarity = match_by_root[root]
            source_removed_lines, _ = hunk_content[source_index]
            _, target_added_lines = hunk_content[target_index]
            residual_removed_lines, residual_added_lines = (
                self.similarity_calculator.exact_residual_lines(
                    source_removed_lines, target_added_lines
                )
            )
            result.append(
                Move(
                    move_id=root_to_move[root],
                    hunks=tuple(hunks[index] for index in indices),
                    similarity=similarity,
                    move_type=(
                        MoveType.PURE
                        if (
                            similarity >= _PURE_SIMILARITY_THRESHOLD
                            and not residual_removed_lines
                            and not residual_added_lines
                        )
                        else MoveType.MODIFIED
                    ),
                    length=max(hunk_changed_line_counts[index] for index in indices),
                    source_hunk=hunks[source_index],
                    target_hunk=hunks[target_index],
                    residual_removed_lines=residual_removed_lines,
                    residual_added_lines=residual_added_lines,
                )
            )
        return result
