import math

from reviewability.domain.models import FileDiff
from reviewability.domain.report import FileAnalysis, MetricResults, MetricValue, MetricValueType
from reviewability.metrics.overall.change_entropy import OverallChangeEntropy

metric = OverallChangeEntropy()


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
    assert result.value == MetricValue("overall.change_entropy", 0.0, MetricValueType.FLOAT)


def test_single_file():
    # All changes in one file → entropy = 0
    result = metric.calculate([], [make_file_analysis(10)])
    assert result.value == MetricValue("overall.change_entropy", 0.0, MetricValueType.FLOAT)


def test_two_equal_files():
    # Equal split → entropy = log2(2) = 1.0
    result = metric.calculate([], [make_file_analysis(5), make_file_analysis(5)])
    assert result.value.value == pytest_approx(1.0)


def test_two_unequal_files():
    # Unequal split → entropy < 1.0
    result = metric.calculate([], [make_file_analysis(9), make_file_analysis(1)])
    expected = -(0.9 * math.log2(0.9) + 0.1 * math.log2(0.1))
    assert abs(result.value.value - expected) < 1e-9


def test_three_equal_files():
    # Equal 3-way split → entropy = log2(3) ≈ 1.585
    result = metric.calculate(
        [], [make_file_analysis(4), make_file_analysis(4), make_file_analysis(4)]
    )
    assert abs(result.value.value - math.log2(3)) < 1e-9


def test_file_with_zero_lines_is_excluded():
    # A file with 0 lines_changed contributes nothing and must not cause log2(0).
    result = metric.calculate([], [make_file_analysis(0), make_file_analysis(10)])
    # Only one file with actual changes → entropy = 0
    assert result.value == MetricValue("overall.change_entropy", 0.0, MetricValueType.FLOAT)


def test_all_files_zero_lines():
    # All files have 0 lines changed → total = 0 → entropy = 0
    result = metric.calculate([], [make_file_analysis(0), make_file_analysis(0)])
    assert result.value == MetricValue("overall.change_entropy", 0.0, MetricValueType.FLOAT)


def test_file_missing_metric_is_excluded():
    # A FileAnalysis without file.lines_changed must be silently ignored.
    file_without_metric = FileAnalysis(
        file=FileDiff(path="b.py", old_path=None, is_new_file=False, is_deleted_file=False),
        metrics=MetricResults([]),
        score=1.0,
    )
    result = metric.calculate([], [file_without_metric, make_file_analysis(10)])
    # Only one file contributes → entropy = 0
    assert result.value == MetricValue("overall.change_entropy", 0.0, MetricValueType.FLOAT)


# pytest.approx helper used inline
def pytest_approx(val: float, rel: float = 1e-6):
    import pytest

    return pytest.approx(val, rel=rel)
