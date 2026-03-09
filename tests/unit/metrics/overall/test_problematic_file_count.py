from reviewability.domain.metric import MetricResults, MetricValueType
from reviewability.domain.models import FileDiff
from reviewability.domain.report import Analysis
from reviewability.metrics.overall.problematic_file_count import OverallProblematicFileCount


def make_file_analysis(score: float) -> Analysis:
    return Analysis(
        subject=FileDiff(path="a.py", old_path=None, is_new_file=False, is_deleted_file=False),
        metrics=MetricResults([]),
        score=score,
    )


def test_none_problematic():
    metric = OverallProblematicFileCount(score_threshold=0.5)
    result = metric.calculate([], [make_file_analysis(0.6), make_file_analysis(1.0)])
    assert result.name == "overall.problematic_file_count"
    assert result.value == 0
    assert result.value_type == MetricValueType.INTEGER
    assert result.causes == []


def test_some_problematic():
    metric = OverallProblematicFileCount(score_threshold=0.5)
    result = metric.calculate([], [make_file_analysis(0.2), make_file_analysis(0.8)])
    assert result.value == 1


def test_threshold_boundary_is_exclusive():
    metric = OverallProblematicFileCount(score_threshold=0.5)
    # score == threshold is NOT problematic
    result = metric.calculate([], [make_file_analysis(0.5)])
    assert result.value == 0


