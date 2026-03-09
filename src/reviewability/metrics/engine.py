from reviewability.domain.models import Diff, FileDiff, Hunk
from reviewability.domain.report import (
    Analysis,
    AnalysisReport,
    Cause,
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

    When a score is below 1.0, the analysis object carries ``causes``:
    all metric values that participated in the score calculation, paired with
    their remediation hints.
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
            m.calculate(hunk_analyses, file_analyses)
            for m in self._registry.overall_metrics()
        ]
        overall_metric_values = MetricResults(overall_results)
        overall_score = self._scorer.overall_score(overall_metric_values)

        overall = OverallAnalysis(
            metrics=overall_metric_values,
            score=overall_score,
        )

        return AnalysisReport(overall=overall, files=file_analyses, hunks=hunk_analyses)

    def _build_hunk_analysis(self, hunk: Hunk) -> Analysis:
        metric_pairs = [(m, m.calculate(hunk)) for m in self._registry.hunk_metrics()]
        results = MetricResults([mv for _, mv in metric_pairs])
        score = self._scorer.hunk_score(results)
        causes = (
            [Cause(value=mv, remediation=m.remediation) for m, mv in metric_pairs]
            if score < 1.0
            else []
        )
        return Analysis(subject=hunk, metrics=results, score=score, causes=causes)

    def _build_file_analysis(self, file: FileDiff) -> Analysis:
        metric_pairs = [(m, m.calculate(file)) for m in self._registry.file_metrics()]
        results = MetricResults([mv for _, mv in metric_pairs])
        score = self._scorer.file_score(results)
        causes = (
            [Cause(value=mv, remediation=m.remediation) for m, mv in metric_pairs]
            if score < 1.0
            else []
        )
        return Analysis(subject=file, metrics=results, score=score, causes=causes)
