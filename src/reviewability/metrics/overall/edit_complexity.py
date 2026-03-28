"""Edit complexity metric: measures difficulty of logically-connected hunk groups."""

from __future__ import annotations

from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.report import Analysis
from reviewability.metrics.base import OverallMetric


class OverallEditComplexity(OverallMetric):
    """Complexity score for hunk groups that are logically connected.

    Aggregates group-level complexity scores (from ``GroupEditComplexity``) into
    a single RATIO score [0.0, 1.0] representing how hard the changes are to review.

    Higher score = easier changes (low complexity).
    Lower score = harder changes (high complexity).
    """

    name = "overall.edit_complexity"
    value_type = MetricValueType.RATIO
    description = (
        "Composite complexity score for hunk groups. "
        "Measures size, rewrite similarity, and connectivity of logically-related hunks. "
        "Higher = easier; lower = harder to review."
    )
    remediation = (
        "If score is low, consider splitting the change into focused commits: "
        "separate moves from logic changes, and rewrite large blocks incrementally."
    )

    def calculate(
        self, hunks: list[Analysis], files: list[Analysis], groups: list[Analysis]
    ) -> MetricValue:
        """Calculate edit complexity as the average of all group scores."""
        if not groups:
            return MetricValue(
                name=self.name,
                value=1.0,
                value_type=self.value_type,
                remediation=self.remediation,
            )

        avg_group_score = sum(g.score for g in groups) / len(groups)

        return MetricValue(
            name=self.name,
            value=avg_group_score,
            value_type=self.value_type,
            remediation=self.remediation,
        )

