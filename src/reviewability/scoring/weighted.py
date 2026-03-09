from typing import override

from reviewability.domain.report import MetricResults
from reviewability.metrics.hunk.lines_changed import HunkLinesChanged
from reviewability.metrics.file.lines_changed import FileLinesChanged
from reviewability.metrics.overall.churn_complexity import OverallChurnComplexity
from reviewability.metrics.overall.lines_changed import OverallLinesChanged
from reviewability.scoring.base import ReviewabilityScorer


class DefaultScorer(ReviewabilityScorer):
    """Concrete reviewability scorer used by the default analysis pipeline.

    Hunk score:    max(0, 1 − lines_changed / max_hunk_lines)
    File score:    max(0, 1 − lines_changed / max_diff_lines)
    Overall score: max(0, 1 − size_ratio × (1 + churn_complexity))

    The overall formula penalises interleaved changes progressively more
    as the diff grows toward the configured size limit.
    """

    def __init__(self, max_hunk_lines: float, max_diff_lines: float) -> None:
        self._max_hunk_lines = max_hunk_lines
        self._max_diff_lines = max_diff_lines

    @override
    def hunk_score(self, metrics: MetricResults) -> float:
        v = metrics.get(HunkLinesChanged.name)
        return max(0.0, 1.0 - v.value / self._max_hunk_lines) if v else 1.0

    @override
    def file_score(self, metrics: MetricResults) -> float:
        v = metrics.get(FileLinesChanged.name)
        return max(0.0, 1.0 - v.value / self._max_diff_lines) if v else 1.0

    @override
    def overall_score(self, metrics: MetricResults) -> float:
        lines = metrics.get(OverallLinesChanged.name)
        if lines is None:
            return 1.0
        size_ratio = min(lines.value / self._max_diff_lines, 1.0)
        churn_mv = metrics.get(OverallChurnComplexity.name)
        churn = churn_mv.value if churn_mv is not None else 0.0
        return max(0.0, 1.0 - size_ratio * (1.0 + churn))

    @override
    def overall_score_inputs(self) -> set[str]:
        return {OverallLinesChanged.name, OverallChurnComplexity.name}
