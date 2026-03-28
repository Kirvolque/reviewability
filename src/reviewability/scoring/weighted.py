from typing import override

from reviewability.domain.metric import MetricResults
from reviewability.metrics.file.in_place_rewrite_lines import FileInPlaceRewriteLines
from reviewability.metrics.file.lines_changed import FileLinesChanged
from reviewability.metrics.file.moved_lines import FileMovedLines
from reviewability.metrics.file.moved_rewrite_lines import FileMovedRewriteLines
from reviewability.metrics.hunk.in_place_rewrite_lines import HunkInPlaceRewriteLines
from reviewability.metrics.hunk.is_likely_moved import HunkIsLikelyMoved
from reviewability.metrics.hunk.lines_changed import HunkLinesChanged
from reviewability.metrics.hunk.moved_rewrite_lines import HunkMovedRewriteLines
from reviewability.metrics.overall.in_place_rewrite_lines import OverallInPlaceRewriteLines
from reviewability.metrics.overall.lines_changed import OverallLinesChanged
from reviewability.metrics.overall.moved_lines import OverallMovedLines
from reviewability.metrics.overall.moved_rewrite_lines import OverallMovedRewriteLines
from reviewability.metrics.overall.scatter_factor import OverallScatterFactor
from reviewability.scoring.base import ReviewabilityScorer


class DefaultScorer(ReviewabilityScorer):
    """Concrete reviewability scorer used by the default analysis pipeline.

    Hunk score:    1.0 if likely moved; otherwise max(0, 1 − effective_lines / max_hunk_lines)
    File score:    max(0, 1 − effective_lines / max_diff_lines)
    Overall score: max(0, 1 − effective_size_ratio × (1 + scatter_factor))
                   where effective_size_ratio excludes both sides of moved pairs and
                   inflates rewrite-heavy lines by configured line costs.

    Movements are easy to review and should not penalise the overall score.
    """

    def __init__(
        self,
        max_hunk_lines: float,
        max_diff_lines: float,
        rewrite_in_place_line_cost: float,
        rewrite_moved_line_cost: float,
    ) -> None:
        self._max_hunk_lines = max_hunk_lines
        self._max_diff_lines = max_diff_lines
        self._rewrite_in_place_line_cost = rewrite_in_place_line_cost
        self._rewrite_moved_line_cost = rewrite_moved_line_cost

    @override
    def hunk_score(self, metrics: MetricResults) -> float:
        moved = metrics.metric(HunkIsLikelyMoved.name)
        if moved is not None and moved.value:
            return 1.0
        effective_lines = self._effective_lines(
            metrics=metrics,
            lines_metric_name=HunkLinesChanged.name,
            in_place_metric_name=HunkInPlaceRewriteLines.name,
            moved_metric_name=HunkMovedRewriteLines.name,
        )
        return max(0.0, 1.0 - effective_lines / self._max_hunk_lines)

    @override
    def file_score(self, metrics: MetricResults) -> float:
        effective_lines = max(
            0.0,
            self._effective_lines(
                metrics=metrics,
                lines_metric_name=FileLinesChanged.name,
                in_place_metric_name=FileInPlaceRewriteLines.name,
                moved_metric_name=FileMovedRewriteLines.name,
            )
            - 2.0 * self._metric_value(metrics, FileMovedLines.name),
        )
        return max(0.0, 1.0 - effective_lines / self._max_diff_lines)

    @override
    def group_score(self, metrics: MetricResults) -> float:
        """Group score is the group.edit_complexity metric value if present, else 1.0."""
        mv = metrics.metric("group.edit_complexity")
        return float(mv.value) if mv is not None else 1.0

    @override
    def overall_score(self, metrics: MetricResults) -> float:
        moved = metrics.metric(OverallMovedLines.name)
        moved_count = moved.value if moved is not None else 0
        effective_lines = max(
            0.0,
            self._effective_lines(
                metrics=metrics,
                lines_metric_name=OverallLinesChanged.name,
                in_place_metric_name=OverallInPlaceRewriteLines.name,
                moved_metric_name=OverallMovedRewriteLines.name,
            )
            - 2.0 * moved_count,
        )
        size_ratio = min(effective_lines / self._max_diff_lines, 1.0)
        scatter_mv = metrics.metric(OverallScatterFactor.name)
        scatter = scatter_mv.value if scatter_mv is not None else 0.0
        return max(0.0, 1.0 - size_ratio * (1.0 + scatter))

    def _effective_lines(
        self,
        metrics: MetricResults,
        lines_metric_name: str,
        in_place_metric_name: str,
        moved_metric_name: str,
    ) -> float:
        lines_metric = metrics.metric(lines_metric_name)
        if lines_metric is None:
            return 0.0
        in_place_lines = self._metric_value(metrics, in_place_metric_name)
        moved_lines = self._metric_value(metrics, moved_metric_name)
        return (
            lines_metric.value
            + in_place_lines * (self._rewrite_in_place_line_cost - 1.0)
            + moved_lines * (self._rewrite_moved_line_cost - 1.0)
        )

    @staticmethod
    def _metric_value(metrics: MetricResults, name: str) -> float:
        metric = metrics.metric(name)
        return float(metric.value) if metric is not None else 0.0
