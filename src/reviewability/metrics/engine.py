from reviewability.domain.metric import MetricResults
from reviewability.domain.models import Diff, FileDiff, Hunk
from reviewability.domain.report import Analysis, AnalysisReport, OverallAnalysis
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
            self._build_hunk_analysis(hunk) for file in diff.files for hunk in file.hunks
        ]
        file_analyses = [self._build_file_analysis(file) for file in diff.files]

        overall_results = [
            m.calculate(hunk_analyses, file_analyses) for m in self._registry.overall_metrics()
        ]
        overall_metric_values = MetricResults(overall_results)
        overall_score = self._scorer.overall_score(overall_metric_values)

        overall = OverallAnalysis(
            metrics=overall_metric_values,
            score=overall_score,
        )

        return AnalysisReport(overall=overall, files=file_analyses, hunks=hunk_analyses)

    def _build_hunk_analysis(self, hunk: Hunk) -> Analysis:
        results = MetricResults([m.calculate(hunk) for m in self._registry.hunk_metrics()])
        score = self._scorer.hunk_score(results)
        return Analysis(subject=hunk, metrics=results, score=score)

    def _build_file_analysis(self, file: FileDiff) -> Analysis:
        results = MetricResults([m.calculate(file) for m in self._registry.file_metrics()])
        score = self._scorer.file_score(results)
        return Analysis(subject=file, metrics=results, score=score)
