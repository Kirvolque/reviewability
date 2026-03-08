import pytest

from reviewability.domain.models import FileDiff
from reviewability.domain.report import FileAnalysis, MetricResults, MetricValue, MetricValueType
from reviewability.metrics.overall.largest_file_ratio import OverallLargestFileRatio

metric = OverallLargestFileRatio()


def make_file_analysis(lines_changed: int) -> FileAnalysis:
    return FileAnalysis(
        file=FileDiff(path="a.py", old_path=None, is_new_file=False, is_deleted_file=False),
        metrics=MetricResults(
            [MetricValue("file.lines_changed", lines_changed, MetricValueType.INTEGER)]
        ),
        score=1.0,
    )


def test_no_files():
    result = metric.calculate([], [])
    assert result.value == MetricValue("overall.largest_file_ratio", 0.0, MetricValueType.RATIO)


def test_single_file():
    result = metric.calculate([], [make_file_analysis(20)])
    assert result.value == MetricValue("overall.largest_file_ratio", 1.0, MetricValueType.RATIO)


def test_two_equal_files():
    result = metric.calculate([], [make_file_analysis(10), make_file_analysis(10)])
    assert result.value == MetricValue("overall.largest_file_ratio", 0.5, MetricValueType.RATIO)


def test_dominant_file():
    # 80 of 100 lines in one file → ratio = 0.8
    result = metric.calculate([], [make_file_analysis(80), make_file_analysis(20)])
    assert result.value.value == pytest.approx(0.8)


def test_picks_max():
    result = metric.calculate(
        [],
        [make_file_analysis(10), make_file_analysis(40), make_file_analysis(10)],
    )
    assert result.value.value == pytest.approx(40 / 60)


def test_all_files_zero_lines():
    # total = 0 → ratio = 0.0, must not divide by zero
    result = metric.calculate([], [make_file_analysis(0), make_file_analysis(0)])
    assert result.value == MetricValue("overall.largest_file_ratio", 0.0, MetricValueType.RATIO)


def test_file_missing_metric_is_treated_as_zero():
    # FileAnalysis without file.lines_changed is excluded from values list.
    # Only the file with the metric contributes → ratio = 1.0
    file_without_metric = FileAnalysis(
        file=FileDiff(path="b.py", old_path=None, is_new_file=False, is_deleted_file=False),
        metrics=MetricResults([]),
        score=1.0,
    )
    result = metric.calculate([], [file_without_metric, make_file_analysis(10)])
    assert result.value == MetricValue("overall.largest_file_ratio", 1.0, MetricValueType.RATIO)
