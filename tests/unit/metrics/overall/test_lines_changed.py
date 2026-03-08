from reviewability.domain.models import Hunk
from reviewability.domain.report import HunkAnalysis, MetricResults, MetricValue, MetricValueType
from reviewability.metrics.overall.lines_changed import OverallLinesChanged

metric = OverallLinesChanged()


def make_hunk_analysis(lines_changed: int) -> HunkAnalysis:
    return HunkAnalysis(
        hunk=Hunk(
            file_path="a.py", source_start=1, source_length=1, target_start=1, target_length=1
        ),
        metrics=MetricResults(
            [MetricValue("hunk.lines_changed", lines_changed, MetricValueType.INTEGER)]
        ),
        score=1.0,
    )


def test_no_hunks():
    result = metric.calculate([], [])
    assert result.value == MetricValue("overall.lines_changed", 0, MetricValueType.INTEGER)


def test_single_hunk():
    result = metric.calculate([make_hunk_analysis(5)], [])
    assert result.value == MetricValue("overall.lines_changed", 5, MetricValueType.INTEGER)


def test_multiple_hunks():
    result = metric.calculate([make_hunk_analysis(3), make_hunk_analysis(7)], [])
    assert result.value == MetricValue("overall.lines_changed", 10, MetricValueType.INTEGER)


def test_hunk_missing_metric_is_skipped():
    # A HunkAnalysis without hunk.lines_changed must not crash — it is simply ignored.
    hunk_without_metric = HunkAnalysis(
        hunk=Hunk(
            file_path="a.py", source_start=1, source_length=1, target_start=1, target_length=1
        ),
        metrics=MetricResults([]),
        score=1.0,
    )
    result = metric.calculate([hunk_without_metric, make_hunk_analysis(4)], [])
    assert result.value == MetricValue("overall.lines_changed", 4, MetricValueType.INTEGER)
