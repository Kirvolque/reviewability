from reviewability.domain.models import Diff, FileDiff, Hunk
from reviewability.domain.report import (
    AnalysisReport,
    FileAnalysis,
    HunkAnalysis,
    MetricResults,
    OverallAnalysis,
)
from reviewability.metrics.registry import MetricRegistry
from reviewability.scoring.base import ReviewabilityScorer


class MetricEngine:
    """Runs metric calculation against a diff in the correct order.

    Construction is strictly bottom-up: hunk metrics are computed first,
    then file metrics, then overall metrics. Scores are computed before
    each analysis object is constructed.
    """

    def __init__(self, registry: MetricRegistry, scorer: ReviewabilityScorer) -> None:
        self._registry = registry
        self._scorer = scorer

    def run(self, diff: Diff) -> AnalysisReport:
        """Run all registered metrics against the diff and return a fully computed report."""
        hunk_analyses = [
            self._build_hunk_analysis(hunk)
            for file in diff.files
            for hunk in file.hunks
        ]
        file_analyses = [self._build_file_analysis(file) for file in diff.files]

        overall_metrics = MetricResults(
            [
                m.calculate(hunk_analyses, file_analyses)
                for m in self._registry.overall_metrics()
            ]
        )
        overall = OverallAnalysis(
            metrics=overall_metrics,
            score=self._scorer.overall_score(overall_metrics),
        )

        return AnalysisReport(overall=overall, files=file_analyses, hunks=hunk_analyses)

    def _build_hunk_analysis(self, hunk: Hunk) -> HunkAnalysis:
        results = MetricResults([m.calculate(hunk) for m in self._registry.hunk_metrics()])
        return HunkAnalysis(hunk=hunk, metrics=results, score=self._scorer.hunk_score(results))

    def _build_file_analysis(self, file: FileDiff) -> FileAnalysis:
        results = MetricResults([m.calculate(file) for m in self._registry.file_metrics()])
        return FileAnalysis(file=file, metrics=results, score=self._scorer.file_score(results))
