from __future__ import annotations

from dataclasses import dataclass

from reviewability.diff.similarity_calculator import DiffSimilarityCalculator
from reviewability.domain.models import Hunk, HunkRewriteKind


@dataclass(frozen=True)
class ComplexRewriteDetector:
    """Classify heavy rewrite patterns between one deletion hunk and one insertion hunk.

    The detector is intentionally conservative:

    - both sides must contain enough normalized changed lines
    - similarity must stay inside a middle band:
      too high -> simple replacement
      too low  -> unrelated delete/add
    - token overlap must stay above a minimum threshold

    If a qualifying rewrite stays in the same local area, it is classified as an
    in-place rewrite. Otherwise, it is treated as a moved rewrite.
    """

    min_changed_lines: int = 3
    min_similarity: float = 0.2
    max_similarity: float = 0.9
    min_token_overlap: float = 0.25
    max_in_place_anchor_distance: int = 5

    def classify_rewrite(
        self,
        deletion: Hunk,
        addition: Hunk,
        similarity_calculator: DiffSimilarityCalculator,
    ) -> HunkRewriteKind | None:
        """Return the rewrite classification for one deletion/addition hunk pair."""
        deletion_lines = similarity_calculator.changed_lines(deletion, prefer_removed=True)
        addition_lines = similarity_calculator.changed_lines(addition, prefer_removed=False)
        if len(deletion_lines) < self.min_changed_lines or len(addition_lines) < self.min_changed_lines:
            return None

        sequence_similarity = similarity_calculator.pair_sequence_similarity(
            id(deletion),
            id(addition),
            deletion_lines,
            addition_lines,
        )
        if sequence_similarity < self.min_similarity or sequence_similarity >= self.max_similarity:
            return None

        if (
            similarity_calculator.token_overlap(deletion_lines, addition_lines)
            < self.min_token_overlap
        ):
            return None

        if (
            deletion.file_path == addition.file_path
            and _anchor_distance(deletion, addition) <= self.max_in_place_anchor_distance
        ):
            return HunkRewriteKind.IN_PLACE_REWRITE

        return HunkRewriteKind.MOVED_REWRITE


def _hunk_anchor(hunk: Hunk) -> int:
    """Return a stable logical anchor for a hunk across small line-number drift."""
    starts = tuple(start for start in (hunk.source_start, hunk.target_start) if start > 0)
    return min(starts) if starts else 0


def _anchor_distance(deletion: Hunk, addition: Hunk) -> int:
    """Return logical anchor distance between a deletion hunk and an addition hunk."""
    return abs(_hunk_anchor(deletion) - _hunk_anchor(addition))
