"""Groups hunks that are logically connected (moves, rewrites, splits/merges)."""

from __future__ import annotations

from dataclasses import dataclass

from reviewability.diff.similarity_calculator import DiffSimilarityCalculator
from reviewability.domain.models import GroupType, Hunk, HunkGroup

_MOVED_SIMILARITY_THRESHOLD = 0.9


@dataclass(frozen=True)
class HunkGrouper:
    """Groups hunks that are logically connected by move-aware diff similarity.

    Pairs deletion and insertion hunks using move_aware_similarity (threshold >= 0.3).
    Uses union-find to merge pairs into connected components.
    Returns only multi-hunk groups; ungrouped (singleton) hunks are omitted.
    """

    similarity_calculator: DiffSimilarityCalculator

    def group(self, hunks: list[Hunk]) -> list[HunkGroup]:
        """Group hunks by move-aware diff similarity.

        For every pair of hunks, computes move_aware_similarity between one hunk's
        removed lines and the other's added lines (and vice versa). Pairs with
        similarity >= 0.3 are candidates; greedy best-match selects the best
        non-overlapping pairs.

        Returns list[HunkGroup] containing only multi-hunk groups; singletons are omitted.
        """
        if not hunks:
            return []

        scored_pairs = self._score_all_pairs(hunks)
        accepted_pairs = self._greedy_match(scored_pairs)

        parent = self._initialize_union_find(len(hunks))
        similarity_by_root: dict[int, float] = {}
        for i, j, sim in accepted_pairs:
            parent = self._union(parent, i, j)
            root = self._find(parent, i)
            similarity_by_root[root] = sim

        root_to_group = self._assign_group_ids(parent, len(hunks))
        return self._build_result(hunks, parent, root_to_group, similarity_by_root)

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
        """Return the highest move-aware similarity between a and b's removed/added lines.

        Lines are filtered through content_lines before comparison: blank lines and
        import/package declarations are dropped, and indentation is stripped.
        Checks both directions: a.removed vs b.added, and b.removed vs a.added.
        """
        calc = self.similarity_calculator
        a_removed = calc.content_lines(a.removed_lines, a.file_path)
        a_added = calc.content_lines(a.added_lines, a.file_path)
        b_removed = calc.content_lines(b.removed_lines, b.file_path)
        b_added = calc.content_lines(b.added_lines, b.file_path)
        sim_ab = calc.move_aware_similarity(a_removed, b_added)
        sim_ba = calc.move_aware_similarity(b_removed, a_added)
        return max(sim_ab, sim_ba)

    def _greedy_match(
        self,
        scored_pairs: list[tuple[float, int, int]],
    ) -> list[tuple[int, int, float]]:
        """Greedily select best unmatched pairs, preserving the similarity score.

        Each hunk index appears in at most one accepted pair.
        Returns list of (i, j, similarity).
        """
        matched: set[int] = set()
        pairs: list[tuple[int, int, float]] = []

        for sim, i, j in scored_pairs:
            if i not in matched and j not in matched:
                pairs.append((i, j, sim))
                matched.add(i)
                matched.add(j)

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
        similarity_by_root: dict[int, float],
    ) -> list[HunkGroup]:
        """Build HunkGroup list from union-find result.

        Only multi-hunk groups are returned; singletons (ungrouped hunks) are omitted.
        Multi-hunk groups get their group_id and the stored similarity score.
        """
        buckets: dict[int, list[Hunk]] = {}
        for i, hunk in enumerate(hunks):
            root = self._find(parent, i)
            buckets.setdefault(root, []).append(hunk)

        return [
            HunkGroup(
                group_id=root_to_group[root],
                hunks=tuple(members),
                similarity=(sim := similarity_by_root.get(root, 0.0)),
                group_type=(
                    GroupType.MOVED
                    if sim >= _MOVED_SIMILARITY_THRESHOLD
                    else GroupType.MOVED_MODIFIED
                ),
            )
            for root, members in buckets.items()
            if len(members) > 1
        ]
