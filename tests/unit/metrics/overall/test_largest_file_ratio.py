import pytest

from reviewability.domain.metric import MetricResults, MetricValue, MetricValueType
from reviewability.domain.models import FileDiff
from reviewability.domain.report import Analysis
from reviewability.metrics.overall.largest_file_ratio import OverallLargestFileRatio

metric = OverallLargestFileRatio()


def make_file_analysis(lines_changed: int) -> Analysis:
    return Analysis(
        subject=FileDiff(path="a.py", old_path=None, is_new_file=False, is_deleted_file=False),
        metrics=MetricResults(
            [MetricValue("file.lines_changed", lines_changed, MetricValueType.INTEGER)]
        ),
        score=1.0,
    )


def test_no_files():
    result = metric.calculate([], [], [])
    assert result.name == "overall.largest_file_ratio"
    assert result.value == 0.0
    assert result.value_type == MetricValueType.RATIO


def test_single_file():
    result = metric.calculate([], [make_file_analysis(20)], [])
    assert result.value == 1.0


def test_two_equal_files():
    result = metric.calculate([], [make_file_analysis(10), make_file_analysis(10)], [])
    assert result.value == 0.5


def test_dominant_file():
    # 80 of 100 lines in one file → ratio = 0.8
    result = metric.calculate([], [make_file_analysis(80), make_file_analysis(20)], [])
    assert result.value == pytest.approx(0.8)


def test_picks_max():
    result = metric.calculate(
        [],
        [make_file_analysis(10), make_file_analysis(40), make_file_analysis(10)],
        [],
    )
    assert result.value == round(40 / 60, 2)


def test_all_files_zero_lines():
    # total = 0 → ratio = 0.0, must not divide by zero
    result = metric.calculate([], [make_file_analysis(0), make_file_analysis(0)], [])
    assert result.value == 0.0


def test_file_missing_metric_is_treated_as_zero():
    # Analysis without file.lines_changed is excluded from values list.
    # Only the file with the metric contributes → ratio = 1.0
    file_without_metric = Analysis(
        subject=FileDiff(path="b.py", old_path=None, is_new_file=False, is_deleted_file=False),
        metrics=MetricResults([]),
        score=1.0,
    )
    result = metric.calculate([], [file_without_metric, make_file_analysis(10)], [])
    assert result.value == 1.0
