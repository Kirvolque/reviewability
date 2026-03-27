"""Groups hunks that are logically connected (moves, rewrites, splits/merges)."""

from __future__ import annotations

from dataclasses import dataclass

from reviewability.diff.similarity_calculator import DiffSimilarityCalculator
from reviewability.domain.models import Hunk


@dataclass(frozen=True)
class HunkGrouper:
    """Assigns group IDs to hunks that are logically connected.

    Pairs deletion and insertion hunks by content similarity (threshold >= 0.3),
    regardless of flags. Uses union-find to merge pairs into connected components.
    Returns a dict mapping group_id -> list[Hunk], where singletons have group_id=None.
    """

    similarity_calculator: DiffSimilarityCalculator

    def group(self, hunks: list[Hunk]) -> dict[int | None, list[Hunk]]:
        """Group hunks by connectivity using removed-vs-added line similarity.

        For every pair of hunks, computes the similarity between one hunk's removed
        lines and the other's added lines (and vice versa). Pairs with similarity >= 0.3
        are candidates; greedy best-match selects the best non-overlapping pairs.

        Returns dict[group_id, list[Hunk]] where singletons have group_id=None.
        """
        if not hunks:
            return {}

        scored_pairs = self._score_all_pairs(hunks)
        pairs = self._greedy_match(scored_pairs)

        parent = self._initialize_union_find(len(hunks))
        parent = self._union_pairs(parent, pairs)

        root_to_group = self._assign_group_ids(parent, len(hunks))
        return self._build_result(hunks, parent, root_to_group)

    def _score_all_pairs(self, hunks: list[Hunk]) -> list[tuple[float, int, int]]:
        """Score all hunk pairs by removed-vs-added line similarity.

        For each pair (i, j) computes max(sim(i.removed, j.added), sim(j.removed, i.added)).
        Empty line lists produce 0.0, so two pure additions or two pure deletions never pair.
        Returns list of (similarity, i, j) with i < j, sorted descending by similarity.
        """
        scored: list[tuple[float, int, int]] = []

        for i in range(len(hunks)):
            for j in range(i + 1, len(hunks)):
                sim = self._pair_similarity(hunks[i], hunks[j])
                if sim >= 0.3:  # Low threshold: metric layer handles scoring nuance
                    scored.append((sim, i, j))

        scored.sort(reverse=True, key=lambda x: x[0])
        return scored

    def _pair_similarity(self, a: Hunk, b: Hunk) -> float:
        """Return the highest cross-similarity between a and b's removed/added lines.

        Checks both directions: a.removed vs b.added, and b.removed vs a.added.
        Guards against empty lists (which would score 1.0 via SequenceMatcher).
        """
        sim_ab = (
            self.similarity_calculator.pair_sequence_similarity(
                id(a), id(b), a.removed_lines, b.added_lines
            )
            if a.removed_lines and b.added_lines
            else 0.0
        )
        sim_ba = (
            self.similarity_calculator.pair_sequence_similarity(
                id(b), id(a), b.removed_lines, a.added_lines
            )
            if b.removed_lines and a.added_lines
            else 0.0
        )
        return max(sim_ab, sim_ba)

    def _greedy_match(
        self,
        scored_pairs: list[tuple[float, int, int]],
    ) -> list[tuple[int, int]]:
        """Greedily select best unmatched pairs.

        Each hunk index appears in at most one accepted pair.
        """
        matched: set[int] = set()
        pairs: list[tuple[int, int]] = []

        for _sim, i, j in scored_pairs:
            if i not in matched and j not in matched:
                pairs.append((i, j))
                matched.add(i)
                matched.add(j)

        return pairs

    def _initialize_union_find(self, size: int) -> dict[int, int]:
        """Initialize union-find parent map where each index is its own root."""
        return {i: i for i in range(size)}

    def _union_pairs(
        self, parent: dict[int, int], pairs: list[tuple[int, int]]
    ) -> dict[int, int]:
        """Union all pairs of hunk indices using union-find."""
        for i, j in pairs:
            parent = self._union(parent, i, j)
        return parent

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

    def _assign_group_ids(
        self, parent: dict[int, int], size: int
    ) -> dict[int, int]:
        """Assign unique group_id to each root."""
        root_to_group: dict[int, int] = {}
        next_group_id = 0

        for i in range(size):
            root = self._find(parent, i)
            if root not in root_to_group:
                root_to_group[root] = next_group_id
                next_group_id += 1

        return root_to_group

    def _build_result(
        self,
        hunks: list[Hunk],
        parent: dict[int, int],
        root_to_group: dict[int, int],
    ) -> dict[int | None, list[Hunk]]:
        """Build final result dict grouping hunks by their root.

        Singletons (group_size=1) map to None; multi-hunk groups get their group_id.
        """
        result: dict[int | None, list[Hunk]] = {}

        for i, hunk in enumerate(hunks):
            root = self._find(parent, i)
            group_id = root_to_group[root]
            group_size = self._count_group_size(parent, root, len(hunks))

            if group_size == 1:
                result.setdefault(None, []).append(hunk)
            else:
                result.setdefault(group_id, []).append(hunk)

        return result

    def _count_group_size(self, parent: dict[int, int], root: int, size: int) -> int:
        """Count the number of hunks in the group with the given root."""
        return sum(1 for j in range(size) if self._find(parent, j) == root)
