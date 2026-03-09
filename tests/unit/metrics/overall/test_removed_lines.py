from reviewability.domain.metric import MetricResults, MetricValue, MetricValueType
from reviewability.domain.models import Hunk
from reviewability.domain.report import Analysis
from reviewability.metrics.overall.removed_lines import OverallRemovedLines

metric = OverallRemovedLines()


def make_hunk_analysis(removed: int) -> Analysis:
    return Analysis(
        subject=Hunk(
            file_path="a.py", source_start=1, source_length=1, target_start=1, target_length=1
        ),
        metrics=MetricResults(
            [MetricValue("hunk.removed_lines", removed, MetricValueType.INTEGER)]
        ),
        score=1.0,
    )


def test_no_hunks():
    result = metric.calculate([], [])
    assert result.name == "overall.removed_lines"
    assert result.value == 0
    assert result.value_type == MetricValueType.INTEGER


def test_single_hunk():
    result = metric.calculate([make_hunk_analysis(3)], [])
    assert result.value == 3


def test_multiple_hunks():
    result = metric.calculate([make_hunk_analysis(1), make_hunk_analysis(4)], [])
    assert result.value == 5


def test_hunk_missing_metric_is_skipped():
    hunk_without_metric = Analysis(
        subject=Hunk(
            file_path="a.py", source_start=1, source_length=1, target_start=1, target_length=1
        ),
        metrics=MetricResults([]),
        score=1.0,
    )
    result = metric.calculate([hunk_without_metric, make_hunk_analysis(2)], [])
    assert result.value == 2
