from reviewability.domain.models import FileDiff
from reviewability.domain.report import FileAnalysis, MetricResults, MetricValue, MetricValueType
from reviewability.metrics.overall.files_changed import OverallFilesChanged

metric = OverallFilesChanged()


def make_file_analysis(score: float = 1.0) -> FileAnalysis:
    return FileAnalysis(
        file=FileDiff(path="a.py", old_path=None, is_new_file=False, is_deleted_file=False),
        metrics=MetricResults([]),
        score=score,
    )


def test_no_files():
    result = metric.calculate([], [])
    assert result == MetricValue("overall.files_changed", 0, MetricValueType.INTEGER)


def test_single_file():
    result = metric.calculate([], [make_file_analysis()])
    assert result == MetricValue("overall.files_changed", 1, MetricValueType.INTEGER)


def test_multiple_files():
    result = metric.calculate(
        [], [make_file_analysis(), make_file_analysis(), make_file_analysis()]
    )
    assert result == MetricValue("overall.files_changed", 3, MetricValueType.INTEGER)
