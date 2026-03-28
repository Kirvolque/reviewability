"""Group-level edit complexity metric."""

from __future__ import annotations

from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.models import HunkGroup
from reviewability.domain.report import Analysis
from reviewability.metrics.base import GroupMetric


class GroupEditComplexity(GroupMetric):
    """Reviewability score for a single hunk group [0.0, 1.0].

    Computed as a per-line penalty scaled by how dissimilar the group's content is::

        penalty_per_line = (1 + similarity_penalty × (1 − similarity)) / max_group_lines
        score = max(0, 1 − length × penalty_per_line)

    ``length`` is the meaningful-line size of the largest hunk in the group
    (blank lines and import/package declarations excluded).

    - High similarity (pure move) → small per-line penalty → score close to hunk score
    - Low similarity (rewrite) → large per-line penalty → score drops faster with size
    - Larger group → lower score for the same similarity level

    Higher score = easier to review. Lower score = harder to review.
    """

    name = "group.edit_complexity"
    value_type = MetricValueType.RATIO
    description = (
        "Reviewability score for a connected hunk group. "
        "Combines the size of the largest hunk with move similarity: "
        "pure moves score high, rewrites score low. Higher = easier to review."
    )
    remediation = (
        "If score is low, consider splitting the change into focused commits: "
        "separate moves from logic changes, and rewrite large blocks incrementally."
    )

    def __init__(self, max_group_lines: int, similarity_penalty: float) -> None:
        self._max_group_lines = max_group_lines
        self._similarity_penalty = similarity_penalty

    def calculate(self, group: HunkGroup, hunk_analyses: list[Analysis]) -> MetricValue:
        """Compute reviewability score for the given hunk group."""
        if not group.hunks:
            return MetricValue(name=self.name, value=1.0, value_type=self.value_type)

        penalty = (
            1.0 + self._similarity_penalty * (1.0 - group.similarity)
        ) / self._max_group_lines
        score = max(0.0, 1.0 - group.length * penalty)

        return MetricValue(
            name=self.name,
            value=score,
            value_type=self.value_type,
            remediation=self.remediation,
        )
