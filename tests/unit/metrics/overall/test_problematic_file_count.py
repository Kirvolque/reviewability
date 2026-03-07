from reviewability.domain.models import FileDiff
from reviewability.domain.report import FileAnalysis, MetricResults, MetricValue, MetricValueType
from reviewability.metrics.overall.problematic_file_count import OverallProblematicFileCount


def make_file_analysis(score: float) -> FileAnalysis:
    return FileAnalysis(
        file=FileDiff(path="a.py", old_path=None, is_new_file=False, is_deleted_file=False),
        metrics=MetricResults([]),
        score=score,
    )


def test_none_problematic():
    metric = OverallProblematicFileCount(score_threshold=0.5)
    result = metric.calculate([], [make_file_analysis(0.6), make_file_analysis(1.0)])
    assert result == MetricValue("overall.problematic_file_count", 0, MetricValueType.INTEGER)


def test_all_problematic():
    metric = OverallProblematicFileCount(score_threshold=0.5)
    result = metric.calculate([], [make_file_analysis(0.1), make_file_analysis(0.4)])
    assert result == MetricValue("overall.problematic_file_count", 2, MetricValueType.INTEGER)


def test_some_problematic():
    metric = OverallProblematicFileCount(score_threshold=0.5)
    result = metric.calculate([], [make_file_analysis(0.2), make_file_analysis(0.8)])
    assert result == MetricValue("overall.problematic_file_count", 1, MetricValueType.INTEGER)


def test_no_files():
    metric = OverallProblematicFileCount(score_threshold=0.5)
    result = metric.calculate([], [])
    assert result == MetricValue("overall.problematic_file_count", 0, MetricValueType.INTEGER)


def test_threshold_boundary_is_exclusive():
    metric = OverallProblematicFileCount(score_threshold=0.5)
    # score == threshold is NOT problematic
    result = metric.calculate([], [make_file_analysis(0.5)])
    assert result == MetricValue("overall.problematic_file_count", 0, MetricValueType.INTEGER)


def test_threshold_one_marks_all_problematic():
    metric = OverallProblematicFileCount(score_threshold=1.0)
    result = metric.calculate([], [make_file_analysis(0.0), make_file_analysis(0.99)])
    assert result == MetricValue("overall.problematic_file_count", 2, MetricValueType.INTEGER)
