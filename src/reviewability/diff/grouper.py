"""Groups hunks that are logically connected (moves, rewrites, splits/merges)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from reviewability.diff.similarity_calculator import DiffSimilarityCalculator
from reviewability.domain.models import Hunk, HunkRewriteKind


@dataclass(frozen=True)
class HunkGrouper:
    """Assigns group IDs to hunks that are likely connected.

    Groups hunks based on already-detected rewrite_kind and is_likely_moved flags,
    using union-find to merge pairs into connected components.
    Returns a dict mapping group_id -> list[Hunk], where singletons have group_id=None.
    """

    SIMILARITY_THRESHOLD: ClassVar[float] = 0.95

    similarity_calculator: DiffSimilarityCalculator

    def group(self, hunks: list[Hunk]) -> dict[int | None, list[Hunk]]:
        """Group hunks by connectivity. Returns dict keyed by group_id.

        All hunks are processed; each gets an implicit group_id (None for singletons,
        0..N-1 for groups of size > 1). Hunks with the same group_id form a logical unit.
        """
        if not hunks:
            return {}

        parent: dict[int, int] = self._initialize_union_find(len(hunks))
        pairs = self._find_hunk_pairs(hunks)
        parent = self._union_pairs(parent, pairs)
        root_to_group = self._assign_group_ids(parent, len(hunks))
        return self._build_result(hunks, parent, root_to_group)

    def _initialize_union_find(self, size: int) -> dict[int, int]:
        """Initialize union-find parent map where each index is its own root."""
        return {i: i for i in range(size)}

    def _find_hunk_pairs(self, hunks: list[Hunk]) -> list[tuple[int, int]]:
        """Find pairs of hunks that should be grouped together.

        Returns list of (i, j) tuples where i < j, based on rewrite/move annotations.
        """
        pairs: list[tuple[int, int]] = []

        for i, hunk in enumerate(hunks):
            if self._should_find_pair(hunk):
                pair_idx = self._find_pair(hunks, i)
                if pair_idx is not None and i < pair_idx:
                    pairs.append((i, pair_idx))

        return pairs

    def _should_find_pair(self, hunk: Hunk) -> bool:
        """Check if hunk should be examined for pairing with others."""
        return (
            hunk.rewrite_kind == HunkRewriteKind.MOVED_REWRITE
            or hunk.is_likely_moved
        )

    def _union_pairs(
        self, parent: dict[int, int], pairs: list[tuple[int, int]]
    ) -> dict[int, int]:
        """Union all pairs of hunk indices using union-find.

        Returns the modified parent dict with all pairs unioned.
        """
        for i, j in pairs:
            parent = self._union(parent, i, j)
        return parent

    def _find(self, parent: dict[int, int], x: int) -> int:
        """Find root of x with path compression."""
        if parent[x] != x:
            parent[x] = self._find(parent, parent[x])
        return parent[x]

    def _union(self, parent: dict[int, int], x: int, y: int) -> dict[int, int]:
        """Union two elements by their root.

        Returns the modified parent dict.
        """
        rx, ry = self._find(parent, x), self._find(parent, y)
        if rx != ry:
            parent[rx] = ry
        return parent

    def _assign_group_ids(
        self, parent: dict[int, int], size: int
    ) -> dict[int, int]:
        """Assign unique group_id to each root.

        Each connected component (union-find root) gets a sequential group_id.
        """
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

    def _find_pair(self, hunks: list[Hunk], hunk_idx: int) -> int | None:
        """Find the paired hunk for hunks[hunk_idx] by similarity.

        Returns the index of the pair, or None if no pair found.
        """
        hunk = hunks[hunk_idx]

        if hunk.is_pure_deletion:
            return self._find_addition_pair(hunks, hunk_idx, hunk)

        if hunk.is_pure_addition:
            return self._find_deletion_pair(hunks, hunk_idx, hunk)

        return None

    def _find_addition_pair(
        self, hunks: list[Hunk], hunk_idx: int, deletion_hunk: Hunk
    ) -> int | None:
        """Find a pure addition hunk matching the deletion hunk.

        Searches for an addition with similar content to the deletion.
        Uses SIMILARITY_THRESHOLD (matching MovementDetector).
        """
        for j, candidate in enumerate(hunks):
            if j == hunk_idx:
                continue
            if not candidate.is_pure_addition:
                continue

            sim = self.similarity_calculator.pair_sequence_similarity(
                id(deletion_hunk),
                id(candidate),
                deletion_hunk.removed_lines,
                candidate.added_lines,
            )
            if sim >= self.SIMILARITY_THRESHOLD:
                return j

        return None

    def _find_deletion_pair(
        self, hunks: list[Hunk], hunk_idx: int, addition_hunk: Hunk
    ) -> int | None:
        """Find a pure deletion hunk matching the addition hunk.

        Searches for a deletion with similar content to the addition.
        Uses SIMILARITY_THRESHOLD (matching MovementDetector).
        """
        for j, candidate in enumerate(hunks):
            if j == hunk_idx:
                continue
            if not candidate.is_pure_deletion:
                continue

            sim = self.similarity_calculator.pair_sequence_similarity(
                id(candidate),
                id(addition_hunk),
                candidate.removed_lines,
                addition_hunk.added_lines,
            )
            if sim >= self.SIMILARITY_THRESHOLD:
                return j

        return None
