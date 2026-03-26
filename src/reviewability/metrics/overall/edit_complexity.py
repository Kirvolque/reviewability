"""Edit complexity metric: measures difficulty of logically-connected hunk groups."""

from __future__ import annotations

from reviewability.diff.similarity_calculator import DiffSimilarityCalculator
from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.models import HunkRewriteKind
from reviewability.domain.report import Analysis
from reviewability.metrics.base import OverallMetric


class OverallEditComplexity(OverallMetric):
    """Complexity score for hunk groups that are logically connected.

    Groups hunks by their group_id (assigned by HunkGrouper during annotation).
    For each group, computes: size, type, similarity, span. Aggregates into a
    single RATIO score [0.0, 1.0] representing how hard the changes are to review.

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

    def calculate(self, hunks: list[Analysis], files: list[Analysis]) -> MetricValue:
        """Calculate edit complexity for all hunk groups in the diff."""
        if not hunks:
            return MetricValue(
                name=self.name,
                value=1.0,
                value_type=self.value_type,
                remediation=self.remediation,
            )

        # Extract raw Hunk objects from Analysis
        raw_hunks = [h.subject for h in hunks]

        # Group hunks by group_id
        groups_by_id: dict[int | None, list] = {}
        for hunk in raw_hunks:
            gid = hunk.group_id
            if gid not in groups_by_id:
                groups_by_id[gid] = []
            groups_by_id[gid].append(hunk)

        if not groups_by_id:
            return MetricValue(
                name=self.name,
                value=1.0,
                value_type=self.value_type,
                remediation=self.remediation,
            )

        # Compute complexity for each group
        group_complexities = []
        for group_id, group_hunks in groups_by_id.items():
            complexity = self._compute_group_complexity(group_hunks)
            group_complexities.append(complexity)

        # Aggregate: average complexity (invert: high complexity = low score)
        avg_group_complexity = sum(group_complexities) / len(group_complexities)
        edit_complexity = max(0.0, 1.0 - avg_group_complexity)

        return MetricValue(
            name=self.name,
            value=edit_complexity,
            value_type=self.value_type,
            remediation=self.remediation,
        )

    def _compute_group_complexity(self, group_hunks: list) -> float:
        """Compute complexity score for a single hunk group [0.0, 1.0].

        Higher = more complex (harder to review).
        """
        if not group_hunks:
            return 0.0

        # Singleton groups have low complexity
        if len(group_hunks) == 1:
            return 0.1  # Small penalty for being present at all

        # Multi-hunk groups: compute size, type, similarity factors
        total_size = sum(h.added_count + h.removed_count for h in group_hunks)
        size_factor = min(total_size / 50.0, 1.0)  # Normalize by typical hunk size

        # Type factor: what kind of changes in this group?
        type_multiplier = self._compute_type_multiplier(group_hunks)

        # Similarity factor: how different are removed vs added sides?
        similarity_factor = self._compute_similarity_factor(group_hunks)

        # Span factor: how spread out are the hunks?
        span_factor = self._compute_span_factor(group_hunks)

        # Combine factors: high complexity when size is large, changes are different, hunks are spread out
        complexity = size_factor * (0.5 + 0.5 * similarity_factor) * (0.8 + 0.2 * span_factor) * type_multiplier

        return min(complexity, 1.0)

    def _compute_type_multiplier(self, group_hunks: list) -> float:
        """Return type multiplier based on the kind of changes in the group.

        Move = 1.2 (easy to verify, but still requires attention)
        InPlaceRewrite = 1.0 (moderate difficulty)
        Mixed = 1.1 (default, moderate)
        """
        types = set()
        for hunk in group_hunks:
            if hunk.is_likely_moved:
                types.add("move")
            if hunk.rewrite_kind == HunkRewriteKind.MOVED_REWRITE:
                types.add("moved_rewrite")
            elif hunk.rewrite_kind == HunkRewriteKind.IN_PLACE_REWRITE:
                types.add("in_place_rewrite")

        if "moved_rewrite" in types:
            return 1.2  # Moved rewrites are slightly more complex
        elif "in_place_rewrite" in types:
            return 1.0
        elif "move" in types:
            return 0.9  # Pure moves are easy to review
        else:
            return 1.1  # Default: mixed or unknown

    def _compute_similarity_factor(self, group_hunks: list) -> float:
        """Compute how different removed vs added content is [0.0, 1.0].

        High similarity (0.0) = easy to verify it's a clean move or rename
        Low similarity (1.0) = hard to verify because content changed
        """
        similarity_calc = DiffSimilarityCalculator()
        similarities = []

        for hunk in group_hunks:
            if hunk.removed_lines and hunk.added_lines:
                sim = similarity_calc.sequence_similarity(
                    hunk.removed_lines, hunk.added_lines
                )
                # Invert: high similarity = low complexity
                similarities.append(1.0 - sim)

        if not similarities:
            return 0.0  # No content to compare; assume clean move

        return sum(similarities) / len(similarities)

    def _compute_span_factor(self, group_hunks: list) -> float:
        """Compute how spread out hunks are within their files [0.0, 1.0].

        0.0 = all in same region, 1.0 = spread far apart (forces reviewer to jump around)
        """
        # Group by file path to compute intra-file span
        by_file: dict[str, list] = {}
        for hunk in group_hunks:
            if hunk.file_path not in by_file:
                by_file[hunk.file_path] = []
            by_file[hunk.file_path].append(hunk)

        spans = []
        for file_path, hunks_in_file in by_file.items():
            if len(hunks_in_file) <= 1:
                spans.append(0.0)  # No span for single hunks
            else:
                min_start = min(h.source_start for h in hunks_in_file)
                max_start = max(h.source_start for h in hunks_in_file)
                file_span = (max_start - min_start) / max(1, 500)  # Normalize by typical file size
                spans.append(min(file_span, 1.0))

        if not spans:
            return 0.0

        return sum(spans) / len(spans)
