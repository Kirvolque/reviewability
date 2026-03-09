from reviewability.domain.models import FileDiff
from reviewability.domain.report import (
    Analysis,
    Cause,
    MetricResults,
    MetricValueType,
)
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


def test_all_problematic():
    metric = OverallProblematicFileCount(score_threshold=0.5)
    f1 = make_file_analysis(0.1)
    f2 = make_file_analysis(0.4)
    result = metric.calculate([], [f1, f2])
    assert result.value == 2
    assert result.causes == [Cause(value=f1), Cause(value=f2)]


def test_some_problematic():
    metric = OverallProblematicFileCount(score_threshold=0.5)
    f1 = make_file_analysis(0.2)
    f2 = make_file_analysis(0.8)
    result = metric.calculate([], [f1, f2])
    assert result.value == 1
    assert result.causes == [Cause(value=f1)]


def test_no_files():
    metric = OverallProblematicFileCount(score_threshold=0.5)
    result = metric.calculate([], [])
    assert result.value == 0
    assert result.causes == []


def test_threshold_boundary_is_exclusive():
    metric = OverallProblematicFileCount(score_threshold=0.5)
    # score == threshold is NOT problematic
    result = metric.calculate([], [make_file_analysis(0.5)])
    assert result.value == 0
    assert result.causes == []


def test_threshold_one_marks_all_problematic():
    metric = OverallProblematicFileCount(score_threshold=1.0)
    f1 = make_file_analysis(0.0)
    f2 = make_file_analysis(0.99)
    result = metric.calculate([], [f1, f2])
    assert result.value == 2
    assert len(result.causes) == 2
