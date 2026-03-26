"""Groups hunks that are logically connected (moves, rewrites, splits/merges)."""

from __future__ import annotations

from dataclasses import dataclass

from reviewability.diff.similarity_calculator import DiffSimilarityCalculator
from reviewability.domain.models import Hunk, HunkRewriteKind


@dataclass(frozen=True)
class HunkGrouper:
    """Assigns group IDs to hunks that are likely connected.

    Groups hunks based on already-detected rewrite_kind and is_likely_moved flags,
    using union-find to merge pairs into connected components.
    Returns a dict mapping group_id -> list[Hunk], where singletons have group_id=None.
    """

    similarity_calculator: DiffSimilarityCalculator

    def group(self, hunks: list[Hunk]) -> dict[int | None, list[Hunk]]:
        """Group hunks by connectivity. Returns dict keyed by group_id.

        All hunks are processed; each gets an implicit group_id (None for singletons,
        0..N-1 for groups of size > 1). Hunks with the same group_id form a logical unit.
        """
        if not hunks:
            return {}

        # Union-find structure: maps hunk index to its root
        parent: dict[int, int] = {i: i for i in range(len(hunks))}

        def find(x: int) -> int:
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x: int, y: int) -> None:
            rx, ry = find(x), find(y)
            if rx != ry:
                parent[rx] = ry

        # Build pairs from already-detected rewrite/move annotations
        pairs: list[tuple[int, int]] = []

        for i, hunk in enumerate(hunks):
            if hunk.rewrite_kind == HunkRewriteKind.IN_PLACE_REWRITE:
                # Mixed hunk with both additions and removals marked as rewrite.
                # The hunk itself is a logical unit; no pairing needed.
                # But if we later detect it paired with another hunk, union them.
                pass

            elif hunk.rewrite_kind == HunkRewriteKind.MOVED_REWRITE or hunk.is_likely_moved:
                # This hunk is part of a move or moved rewrite.
                # Try to find its pair by re-running similarity against candidate hunks.
                # A deletion should pair with an insertion of similar content.
                pair_idx = self._find_pair(hunks, i)
                if pair_idx is not None and i < pair_idx:
                    # Only record pair once (i < pair_idx to avoid duplicates)
                    pairs.append((i, pair_idx))

        # Union all pairs
        for i, j in pairs:
            union(i, j)

        # Assign group_id: each root gets a unique group_id; non-roots are None initially
        root_to_group: dict[int, int] = {}
        next_group_id = 0

        for i in range(len(hunks)):
            root = find(i)
            if root not in root_to_group:
                root_to_group[root] = next_group_id
                next_group_id += 1

        # Build result: group_id -> list[Hunk]
        result: dict[int | None, list[Hunk]] = {}
        for i, hunk in enumerate(hunks):
            root = find(i)
            group_id = root_to_group[root]

            # Only assign group_id if the group has more than one hunk
            group_size = sum(1 for j in range(len(hunks)) if find(j) == root)
            if group_size == 1:
                # Singleton
                result.setdefault(None, []).append(hunk)
            else:
                # Multi-hunk group
                result.setdefault(group_id, []).append(hunk)

        return result

    def _find_pair(self, hunks: list[Hunk], hunk_idx: int) -> int | None:
        """Find the paired hunk for hunks[hunk_idx] by similarity.

        Returns the index of the pair, or None if no pair found.
        """
        hunk = hunks[hunk_idx]

        # If this is a pure deletion, look for a pure addition pair
        if hunk.removed_count > 0 and hunk.added_count == 0:
            for j, candidate in enumerate(hunks):
                if j == hunk_idx:
                    continue
                if candidate.added_count > 0 and candidate.removed_count == 0:
                    # Check similarity
                    sim = self.similarity_calculator.pair_sequence_similarity(
                        id(hunk), id(candidate),
                        hunk.removed_lines, candidate.added_lines
                    )
                    if sim >= 0.95:  # Use same threshold as MovementDetector
                        return j

        # If this is a pure addition, look for a pure deletion pair
        elif hunk.added_count > 0 and hunk.removed_count == 0:
            for j, candidate in enumerate(hunks):
                if j == hunk_idx:
                    continue
                if candidate.removed_count > 0 and candidate.added_count == 0:
                    # Check similarity
                    sim = self.similarity_calculator.pair_sequence_similarity(
                        id(candidate), id(hunk),
                        candidate.removed_lines, hunk.added_lines
                    )
                    if sim >= 0.95:
                        return j

        return None
