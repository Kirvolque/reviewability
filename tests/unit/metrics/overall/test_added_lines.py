from reviewability.domain.metric import MetricResults, MetricValue, MetricValueType
from reviewability.domain.models import Hunk
from reviewability.domain.report import Analysis
from reviewability.metrics.overall.added_lines import OverallAddedLines

metric = OverallAddedLines()


def make_hunk_analysis(added: int) -> Analysis:
    return Analysis(
        subject=Hunk(
            file_path="a.py"
        ),
        metrics=MetricResults([MetricValue("hunk.added_lines", added, MetricValueType.INTEGER)]),
        score=1.0,
    )


def test_no_hunks():
    result = metric.calculate([], [], [])
    assert result.name == "overall.added_lines"
    assert result.value == 0
    assert result.value_type == MetricValueType.INTEGER


def test_single_hunk():
    result = metric.calculate([make_hunk_analysis(4)], [], [])
    assert result.name == "overall.added_lines"
    assert result.value == 4


def test_multiple_hunks():
    result = metric.calculate([make_hunk_analysis(2), make_hunk_analysis(6)], [], [])
    assert result.value == 8


def test_hunk_missing_metric_is_skipped():
    hunk_without_metric = Analysis(
        subject=Hunk(
            file_path="a.py"
        ),
        metrics=MetricResults([]),
        score=1.0,
    )
    result = metric.calculate([hunk_without_metric, make_hunk_analysis(3)], [], [])
    assert result.value == 3
