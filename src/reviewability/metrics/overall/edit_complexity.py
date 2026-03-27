"""Edit complexity metric: measures difficulty of logically-connected hunk groups."""

from __future__ import annotations

from reviewability.diff.similarity_calculator import DiffSimilarityCalculator
from reviewability.domain.metric import MetricValue, MetricValueType
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

        Scoring: complexity = size * (1 - similarity) * (1 + span * (1 - similarity))
        - High similarity → low complexity (e.g., clean move)
        - Low similarity → high complexity (significant rewrite)
        - Far apart with low similarity → even higher complexity
        """
        if not group_hunks:
            return 0.0

        # Singleton groups: score based on hunk characteristics
        if len(group_hunks) == 1:
            hunk = group_hunks[0]
            total_size = hunk.added_count + hunk.removed_count
            size_factor = min(total_size / 50.0, 1.0)

            # For mixed hunks, compute self-similarity (removed vs added)
            if hunk.removed_lines and hunk.added_lines:
                similarity = DiffSimilarityCalculator().sequence_similarity(
                    hunk.removed_lines, hunk.added_lines
                )
                complexity = size_factor * (1.0 - similarity)
            else:
                # Pure addition or pure deletion alone: small penalty
                complexity = 0.1

            return min(complexity, 1.0)

        # Multi-hunk groups: pair-based scoring
        total_size = sum(h.added_count + h.removed_count for h in group_hunks)
        size_factor = min(total_size / 50.0, 1.0)

        # Compute overall similarity: all removed lines vs all added lines in the group
        all_removed = [line for h in group_hunks for line in h.removed_lines]
        all_added = [line for h in group_hunks for line in h.added_lines]

        if all_removed and all_added:
            similarity = DiffSimilarityCalculator().sequence_similarity(
                all_removed, all_added
            )
        else:
            similarity = 1.0  # Assume clean if no content to compare

        # Compute span: how spread out are the hunks?
        span = self._compute_span_factor(group_hunks)

        # Formula: size * (1 - similarity) * (1 + span * (1 - similarity))
        complexity = size_factor * (1.0 - similarity) * (1.0 + span * (1.0 - similarity))

        return min(complexity, 1.0)

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
