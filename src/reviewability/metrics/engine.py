from reviewability.domain.metric import MetricResults
from reviewability.domain.models import Diff, FileDiff, Hunk, HunkGroup
from reviewability.domain.report import Analysis, AnalysisReport, OverallAnalysis
from reviewability.metrics.registry import MetricRegistry
from reviewability.scoring.base import ReviewabilityScorer


class MetricEngine:
    """Runs metric calculation against a diff in the correct order.

    Construction is strictly bottom-up: hunk metrics are computed first,
    then file metrics, then group metrics, then overall metrics. Scores are
    computed before each analysis object is constructed.

    """

    def __init__(self, registry: MetricRegistry, scorer: ReviewabilityScorer) -> None:
        self._registry = registry
        self._scorer = scorer

    def run(self, diff: Diff) -> AnalysisReport:
        """Run all registered metrics against the diff and return a fully computed report."""
        hunk_analyses = [self._build_hunk_analysis(hunk) for hunk in diff.singleton_hunks]
        file_analyses = [self._build_file_analysis(file) for file in diff.files]
        group_analyses = [self._build_group_analysis(g, hunk_analyses) for g in diff.groups]

        overall_results = [
            m.calculate(hunk_analyses, file_analyses, group_analyses)
            for m in self._registry.overall_metrics()
        ]
        overall_metric_values = MetricResults(overall_results)
        overall_score = self._scorer.overall_score(overall_metric_values)

        overall = OverallAnalysis(
            metrics=overall_metric_values,
            score=overall_score,
        )

        return AnalysisReport(
            overall=overall,
            files=file_analyses,
            groups=group_analyses,
            hunks=hunk_analyses,
        )

    def _build_group_analysis(self, group: HunkGroup, hunk_analyses: list[Analysis]) -> Analysis:
        """Compute group metrics and score for a single ``HunkGroup``."""
        hunk_id_set = {id(h) for h in group.hunks}
        relevant = [a for a in hunk_analyses if id(a.subject) in hunk_id_set]

        results = MetricResults(
            [m.calculate(group, relevant) for m in self._registry.group_metrics()]
        )
        score = self._scorer.group_score(results)
        return Analysis(subject=group, metrics=results, score=score)

    def _build_hunk_analysis(self, hunk: Hunk) -> Analysis:
        results = MetricResults([m.calculate(hunk) for m in self._registry.hunk_metrics()])
        score = self._scorer.hunk_score(results)
        return Analysis(subject=hunk, metrics=results, score=score)

    def _build_file_analysis(self, file: FileDiff) -> Analysis:
        results = MetricResults([m.calculate(file) for m in self._registry.file_metrics()])
        score = self._scorer.file_score(results)
        return Analysis(subject=file, metrics=results, score=score)
