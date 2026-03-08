from reviewability.domain.models import Hunk
from reviewability.domain.report import HunkAnalysis, MetricResults, MetricValue, MetricValueType
from reviewability.metrics.overall.added_lines import OverallAddedLines

metric = OverallAddedLines()


def make_hunk_analysis(added: int) -> HunkAnalysis:
    return HunkAnalysis(
        hunk=Hunk(
            file_path="a.py", source_start=1, source_length=1, target_start=1, target_length=1
        ),
        metrics=MetricResults([MetricValue("hunk.added_lines", added, MetricValueType.INTEGER)]),
        score=1.0,
    )


def test_no_hunks():
    result = metric.calculate([], [])
    assert result.value == MetricValue("overall.added_lines", 0, MetricValueType.INTEGER)


def test_single_hunk():
    result = metric.calculate([make_hunk_analysis(4)], [])
    assert result.value == MetricValue("overall.added_lines", 4, MetricValueType.INTEGER)


def test_multiple_hunks():
    result = metric.calculate([make_hunk_analysis(2), make_hunk_analysis(6)], [])
    assert result.value == MetricValue("overall.added_lines", 8, MetricValueType.INTEGER)


def test_hunk_missing_metric_is_skipped():
    hunk_without_metric = HunkAnalysis(
        hunk=Hunk(
            file_path="a.py", source_start=1, source_length=1, target_start=1, target_length=1
        ),
        metrics=MetricResults([]),
        score=1.0,
    )
    result = metric.calculate([hunk_without_metric, make_hunk_analysis(3)], [])
    assert result.value == MetricValue("overall.added_lines", 3, MetricValueType.INTEGER)
