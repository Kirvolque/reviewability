from typing import override

from reviewability.domain.metric import MetricResults
from reviewability.metrics.file.lines_changed import FileLinesChanged
from reviewability.metrics.hunk.interleaving import HunkInterleaving
from reviewability.metrics.hunk.lines_changed import HunkLinesChanged
from reviewability.metrics.overall.lines_changed import OverallLinesChanged
from reviewability.metrics.overall.mean_interleaving import OverallMeanInterleaving
from reviewability.scoring.base import ReviewabilityScorer


class DefaultScorer(ReviewabilityScorer):
    """Concrete reviewability scorer used by the default analysis pipeline.

    Hunk score:    max(0, 1 − (lines / max_hunk_lines) × (1 + interleaving))
    File score:    max(0, 1 − lines / max_diff_lines)
    Overall score: max(0, 1 − size_ratio × (1 + mean_interleaving))
    """

    def __init__(
        self,
        max_hunk_lines: float,
        max_diff_lines: float,
    ) -> None:
        self._max_hunk_lines = max_hunk_lines
        self._max_diff_lines = max_diff_lines

    @override
    def hunk_score(self, metrics: MetricResults) -> float:
        mv = metrics.metric(HunkLinesChanged.name)
        if mv is None:
            return 1.0
        size_ratio = mv.value / self._max_hunk_lines
        interleaving_mv = metrics.metric(HunkInterleaving.name)
        interleaving = interleaving_mv.value if interleaving_mv is not None else 0.0
        return max(0.0, 1.0 - size_ratio * (1.0 + interleaving))

    @override
    def file_score(self, metrics: MetricResults) -> float:
        mv = metrics.metric(FileLinesChanged.name)
        if mv is None:
            return 1.0
        return max(0.0, 1.0 - mv.value / self._max_diff_lines)

    @override
    def move_score(self, metrics: MetricResults) -> float:
        """Move score is the move.edit_complexity metric value if present, else 1.0."""
        mv = metrics.metric("move.edit_complexity")
        return float(mv.value) if mv is not None else 1.0

    @override
    def overall_score(self, metrics: MetricResults) -> float:
        mv = metrics.metric(OverallLinesChanged.name)
        if mv is None:
            return 1.0
        size_ratio = min(mv.value / self._max_diff_lines, 1.0)
        interleaving_mv = metrics.metric(OverallMeanInterleaving.name)
        mean_interleaving = interleaving_mv.value if interleaving_mv is not None else 0.0
        return max(0.0, 1.0 - size_ratio * (1.0 + mean_interleaving))
