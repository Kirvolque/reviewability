"""Move-level edit complexity metric."""

from __future__ import annotations

from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.models import Move, MoveType
from reviewability.domain.report import Analysis
from reviewability.metrics.base import MoveMetric


class MoveEditComplexity(MoveMetric):
    """Reviewability score for a single code move [0.0, 1.0].

    Computed as a per-line penalty scaled by how dissimilar the move's content is::

        penalty_per_line = (1 + similarity_penalty × (1 − similarity)) / max_move_lines
        score = max(0, 1 − length × penalty_per_line)

    ``length`` is the meaningful-line size of the largest hunk in the move
    (blank lines and import/package declarations excluded).

    - High similarity (pure move) → small per-line penalty → score close to hunk score
    - Low similarity (rewrite) → large per-line penalty → score drops faster with size
    - Larger move → lower score for the same similarity level

    Higher score = easier to review. Lower score = harder to review.
    """

    name = "move.edit_complexity"
    value_type = MetricValueType.RATIO
    description = (
        "Edit complexity score for a connected code move. "
        "Combines the size of the largest hunk with move similarity: "
        "pure moves score high, rewrites score low. Higher = easier to review."
    )
    remediation = None

    def __init__(self, max_move_lines: int, similarity_penalty: float) -> None:
        self._max_move_lines = max_move_lines
        self._similarity_penalty = similarity_penalty

    def calculate(self, move: Move, hunk_analyses: list[Analysis]) -> MetricValue:
        """Compute reviewability score for the given code move."""
        if not move.hunks:
            return MetricValue(name=self.name, value=1.0, value_type=self.value_type)

        penalty = (1.0 + self._similarity_penalty * (1.0 - move.similarity)) / self._max_move_lines
        score = max(0.0, 1.0 - move.length * penalty)

        return MetricValue(
            name=self.name,
            value=score,
            value_type=self.value_type,
            remediation=self.remediation,
            causes=self._causes(move),
        )

    @staticmethod
    def _causes(move: Move) -> tuple[MetricValue, ...]:
        """Explain why a modified move is costly without treating pure moves as rewrites."""
        if move.move_type is not MoveType.MODIFIED:
            return ()

        return (
            MetricValue(
                name="move.modified_relocation",
                value=move.similarity,
                value_type=MetricValueType.RATIO,
                remediation=(
                    "This relocation also changes code. Review the behavioural edits "
                    "separately from the movement."
                ),
            ),
            MetricValue(
                name="move.rewrite_length",
                value=move.length,
                value_type=MetricValueType.INTEGER,
                remediation=(
                    "This moved rewrite spans a large block. Verify the rewritten "
                    "behaviour incrementally instead of treating it as mechanical movement."
                ),
            ),
        )
