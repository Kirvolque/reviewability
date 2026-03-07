from pathlib import Path

from reviewability.domain.report import (
    AnalysisReport,
    FileAnalysis,
    HunkAnalysis,
    MetricResults,
    MetricValue,
    MetricValueType,
    OverallAnalysis,
)
from reviewability.metrics.builtin import (
    FileHunkCount,
    FileLinesChanged,
    HunkAddedLines,
    HunkLinesChanged,
    HunkRemovedLines,
    OverallFilesChanged,
    OverallLinesChanged,
)
from reviewability.metrics.registry import MetricRegistry
from reviewability.parser.git import parse_diff_text
from reviewability.scoring.weighted import MetricWeight, WeightedReviewabilityScorer

FIXTURES = Path(__file__).parent.parent / "fixtures"


def load(name: str) -> str:
    return (FIXTURES / name).read_text()


def make_registry() -> MetricRegistry:
    registry = MetricRegistry()
    for metric in [
        HunkLinesChanged(),
        HunkAddedLines(),
        HunkRemovedLines(),
        FileHunkCount(),
        FileLinesChanged(),
        OverallFilesChanged(),
        OverallLinesChanged(),
    ]:
        registry.add(metric)
    return registry


def make_scorer() -> WeightedReviewabilityScorer:
    return WeightedReviewabilityScorer(
        hunk_weights=[MetricWeight("hunk.lines_changed", max_value=50.0)],
        file_weights=[MetricWeight("file.lines_changed", max_value=200.0)],
        overall_weights=[MetricWeight("overall.lines_changed", max_value=500.0)],
    )


def test_logic_change_report():
    diff = parse_diff_text(load("logic_change.diff"))
    scorer = make_scorer()
    report = make_registry().run(diff, scorer)

    overall_metrics = MetricResults(
        [
            MetricValue("overall.files_changed", 1, MetricValueType.INTEGER),
            MetricValue("overall.lines_changed", 2, MetricValueType.INTEGER),
        ]
    )
    file_metrics = MetricResults(
        [
            MetricValue("file.hunk_count", 1, MetricValueType.INTEGER),
            MetricValue("file.lines_changed", 2, MetricValueType.INTEGER),
        ]
    )
    hunk_metrics = MetricResults(
        [
            MetricValue("hunk.lines_changed", 2, MetricValueType.INTEGER),
            MetricValue("hunk.added_lines", 2, MetricValueType.INTEGER),
            MetricValue("hunk.removed_lines", 0, MetricValueType.INTEGER),
        ]
    )

    assert report == AnalysisReport(
        overall=OverallAnalysis(
            metrics=overall_metrics,
            score=scorer.overall_score(overall_metrics),
        ),
        files=[
            FileAnalysis(
                file=diff.files[0],
                metrics=file_metrics,
                score=scorer.file_score(file_metrics),
            )
        ],
        hunks=[
            HunkAnalysis(
                hunk=diff.files[0].hunks[0],
                metrics=hunk_metrics,
                score=scorer.hunk_score(hunk_metrics),
            )
        ],
    )


def test_multi_file_change_report():
    diff = parse_diff_text(load("multi_file_change.diff"))
    report = make_registry().run(diff, make_scorer())

    assert len(report.overall.metrics) == 2
    assert len(report.files) == 2
    assert len(report.hunks) == 2
    assert 0.0 <= report.overall.score <= 1.0

    for hunk_analysis in report.hunks:
        assert len(hunk_analysis.metrics) == 3
        assert 0.0 <= hunk_analysis.score <= 1.0
        metric_names = {m.name for m in hunk_analysis.metrics}
        assert metric_names == {"hunk.lines_changed", "hunk.added_lines", "hunk.removed_lines"}
