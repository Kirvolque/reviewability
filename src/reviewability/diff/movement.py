from __future__ import annotations

from dataclasses import dataclass

from reviewability.domain.models import Hunk


@dataclass(frozen=True)
class MovementDetector:
    """Apply movement thresholds to one prepared deletion/addition hunk pair.

    The caller is responsible for normalizing lines and calculating similarity.
    This detector only applies structural rules:
    - pair type must be deletion/addition
    - normalized line counts must meet the configured minimum
    - similarity must meet the configured threshold
    """

    hunk_min_lines: int = 8
    """Minimum content lines required to consider a hunk for movement detection."""

    similarity_threshold: float = 0.95
    """Fraction of lines that must match for two blocks to be considered a likely movement."""

    def hunks_are_likely_moved(
        self,
        deletion: Hunk,
        insertion: Hunk,
        *,
        similarity: float,
        deletion_line_count: int,
        insertion_line_count: int,
    ) -> bool:
        """Return True if ``insertion`` is likely a moved version of ``deletion``.

        ``deletion`` must be a pure-removal hunk (no added lines) and ``insertion`` must be a
        pure-addition hunk (no removed lines). The similarity score and normalized
        content line counts are computed by the caller. Returns False if either type
        check or the line thresholds are not met.
        """
        if deletion.added_count != 0 or insertion.removed_count != 0:
            return False

        if deletion_line_count < self.hunk_min_lines or insertion_line_count < self.hunk_min_lines:
            return False

        return similarity >= self.similarity_threshold
