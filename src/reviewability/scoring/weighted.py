from typing import override

from reviewability.domain.metric import MetricResults
from reviewability.metrics.file.is_likely_moved import FileIsLikelyMoved
from reviewability.metrics.file.lines_changed import FileLinesChanged
from reviewability.metrics.hunk.is_likely_moved import HunkIsLikelyMoved
from reviewability.metrics.hunk.lines_changed import HunkLinesChanged
from reviewability.metrics.overall.churn_complexity import OverallChurnComplexity
from reviewability.metrics.overall.lines_changed import OverallLinesChanged
from reviewability.metrics.overall.moved_lines import OverallMovedLines
from reviewability.scoring.base import ReviewabilityScorer


class DefaultScorer(ReviewabilityScorer):
    """Concrete reviewability scorer used by the default analysis pipeline.

    Hunk score:    1.0 if likely moved; otherwise max(0, 1 − lines_changed / max_hunk_lines)
    File score:    1.0 if likely moved; otherwise max(0, 1 − lines_changed / max_diff_lines)
    Overall score: max(0, 1 − effective_size_ratio × (1 + churn_complexity))
                   where effective_size_ratio excludes moved lines and churn excludes moved hunks.

    Movements are easy to review and should not penalise the overall score.
    """

    def __init__(self, max_hunk_lines: float, max_diff_lines: float) -> None:
        self._max_hunk_lines = max_hunk_lines
        self._max_diff_lines = max_diff_lines

    @override
    def hunk_score(self, metrics: MetricResults) -> float:
        moved = metrics.metric(HunkIsLikelyMoved.name)
        if moved is not None and moved.value:
            return 1.0
        v = metrics.metric(HunkLinesChanged.name)
        return max(0.0, 1.0 - v.value / self._max_hunk_lines) if v else 1.0

    @override
    def file_score(self, metrics: MetricResults) -> float:
        moved = metrics.metric(FileIsLikelyMoved.name)
        if moved is not None and moved.value:
            return 1.0
        v = metrics.metric(FileLinesChanged.name)
        return max(0.0, 1.0 - v.value / self._max_diff_lines) if v else 1.0

    @override
    def overall_score(self, metrics: MetricResults) -> float:
        lines = metrics.metric(OverallLinesChanged.name)
        if lines is None:
            return 1.0
        moved = metrics.metric(OverallMovedLines.name)
        moved_count = moved.value if moved is not None else 0
        effective_lines = max(0, lines.value - moved_count)
        size_ratio = min(effective_lines / self._max_diff_lines, 1.0)
        churn_mv = metrics.metric(OverallChurnComplexity.name)
        churn = churn_mv.value if churn_mv is not None else 0.0
        return max(0.0, 1.0 - size_ratio * (1.0 + churn))
