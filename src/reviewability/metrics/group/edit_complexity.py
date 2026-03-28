"""Group-level edit complexity metric."""

from __future__ import annotations

from reviewability.diff.similarity_calculator import DiffSimilarityCalculator
from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.models import Hunk, HunkGroup
from reviewability.domain.report import Analysis
from reviewability.metrics.base import GroupMetric


class GroupEditComplexity(GroupMetric):
    """Complexity score for a single hunk group [0.0, 1.0].

    Measures how hard the group is to review based on:
    - **Size**: total lines changed (larger = harder)
    - **Similarity**: how similar the removed and added content is
      (high similarity = easy, e.g. pure move; low = hard rewrite)
    - **Span**: how far apart hunks are within each file
      (span amplifies complexity for low-similarity groups)

    Formula for multi-hunk groups::

        complexity = size × (1 − similarity) × (1 + span × (1 − similarity))

    Singletons (single mixed hunk): ``complexity = size × (1 − similarity)``
    Pure additions/deletions with no counterpart: flat ``0.1`` penalty.

    Higher score = easier (less complex). Lower score = harder to review.
    """

    name = "group.edit_complexity"
    value_type = MetricValueType.RATIO
    description = (
        "Edit complexity score for a connected hunk group. "
        "Combines size, content similarity, and intra-file span. "
        "Higher = easier; lower = harder to review."
    )
    remediation = (
        "If score is low, consider splitting the change into focused commits: "
        "separate moves from logic changes, and rewrite large blocks incrementally."
    )

    def calculate(self, group: HunkGroup, hunk_analyses: list[Analysis]) -> MetricValue:
        """Compute edit complexity for the given hunk group."""
        hunks = list(group.hunks)
        complexity = self._compute_complexity(hunks)
        score = max(0.0, 1.0 - complexity)
        return MetricValue(
            name=self.name,
            value=score,
            value_type=self.value_type,
            remediation=self.remediation,
        )

    def _compute_complexity(self, hunks: list[Hunk]) -> float:
        """Compute raw complexity [0.0, 1.0] for a list of hunks."""
        if not hunks:
            return 0.0

        total_size = sum(h.added_count + h.removed_count for h in hunks)
        size_factor = min(total_size / 50.0, 1.0)

        if len(hunks) == 1:
            hunk = hunks[0]
            if hunk.removed_lines and hunk.added_lines:
                similarity = DiffSimilarityCalculator().sequence_similarity(
                    hunk.removed_lines, hunk.added_lines
                )
                return min(size_factor * (1.0 - similarity), 1.0)
            return 0.1  # pure addition or deletion alone

        all_removed = [line for h in hunks for line in h.removed_lines]
        all_added = [line for h in hunks for line in h.added_lines]

        if all_removed and all_added:
            similarity = DiffSimilarityCalculator().sequence_similarity(all_removed, all_added)
        else:
            similarity = 1.0  # assume clean if nothing to compare

        span = self._span_factor(hunks)
        complexity = size_factor * (1.0 - similarity) * (1.0 + span * (1.0 - similarity))
        return min(complexity, 1.0)

    def _span_factor(self, hunks: list[Hunk]) -> float:
        """Average per-file span of the hunks, normalised to [0.0, 1.0]."""
        by_file: dict[str, list[Hunk]] = {}
        for hunk in hunks:
            by_file.setdefault(hunk.file_path, []).append(hunk)

        spans = []
        for file_hunks in by_file.values():
            if len(file_hunks) <= 1:
                spans.append(0.0)
            else:
                min_start = min(h.source_start for h in file_hunks)
                max_start = max(h.source_start for h in file_hunks)
                spans.append(min((max_start - min_start) / 500.0, 1.0))

        return sum(spans) / len(spans) if spans else 0.0
