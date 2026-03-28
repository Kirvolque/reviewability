from reviewability.domain.metric import MetricResults, MetricValueType
from reviewability.domain.models import FileDiff
from reviewability.domain.report import Analysis
from reviewability.metrics.overall.files_changed import OverallFilesChanged

metric = OverallFilesChanged()


def make_file_analysis(score: float = 1.0) -> Analysis:
    return Analysis(
        subject=FileDiff(path="a.py", old_path=None, is_new_file=False, is_deleted_file=False),
        metrics=MetricResults([]),
        score=score,
    )


def test_no_files():
    result = metric.calculate([], [], [])
    assert result.name == "overall.files_changed"
    assert result.value == 0
    assert result.value_type == MetricValueType.INTEGER


def test_single_file():
    result = metric.calculate([], [make_file_analysis()], [])
    assert result.value == 1


def test_multiple_files():
    result = metric.calculate(
        [], [make_file_analysis(), make_file_analysis(), make_file_analysis()], []
    )
    assert result.value == 3
