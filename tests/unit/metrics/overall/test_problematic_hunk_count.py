from reviewability.domain.models import Hunk
from reviewability.domain.report import HunkAnalysis, MetricResults, MetricValue, MetricValueType
from reviewability.metrics.overall.problematic_hunk_count import OverallProblematicHunkCount


def make_hunk_analysis(score: float) -> HunkAnalysis:
    return HunkAnalysis(
        hunk=Hunk(
            file_path="a.py", source_start=1, source_length=1, target_start=1, target_length=1
        ),
        metrics=MetricResults([]),
        score=score,
    )


def test_none_problematic():
    metric = OverallProblematicHunkCount(score_threshold=0.5)
    result = metric.calculate([make_hunk_analysis(0.8), make_hunk_analysis(0.9)], [])
    assert result == MetricValue("overall.problematic_hunk_count", 0, MetricValueType.INTEGER)


def test_all_problematic():
    metric = OverallProblematicHunkCount(score_threshold=0.5)
    result = metric.calculate([make_hunk_analysis(0.1), make_hunk_analysis(0.3)], [])
    assert result == MetricValue("overall.problematic_hunk_count", 2, MetricValueType.INTEGER)


def test_some_problematic():
    metric = OverallProblematicHunkCount(score_threshold=0.5)
    result = metric.calculate([make_hunk_analysis(0.2), make_hunk_analysis(0.7)], [])
    assert result == MetricValue("overall.problematic_hunk_count", 1, MetricValueType.INTEGER)


def test_threshold_boundary_is_exclusive():
    metric = OverallProblematicHunkCount(score_threshold=0.5)
    # score == threshold is NOT problematic (requires strictly less than)
    result = metric.calculate([make_hunk_analysis(0.5)], [])
    assert result == MetricValue("overall.problematic_hunk_count", 0, MetricValueType.INTEGER)


def test_no_hunks():
    metric = OverallProblematicHunkCount(score_threshold=0.5)
    result = metric.calculate([], [])
    assert result == MetricValue("overall.problematic_hunk_count", 0, MetricValueType.INTEGER)


def test_threshold_zero_marks_nothing_problematic():
    # score is always >= 0.0, so threshold=0.0 → nothing is strictly less than 0
    metric = OverallProblematicHunkCount(score_threshold=0.0)
    result = metric.calculate([make_hunk_analysis(0.0), make_hunk_analysis(0.5)], [])
    assert result == MetricValue("overall.problematic_hunk_count", 0, MetricValueType.INTEGER)


def test_threshold_one_marks_all_problematic():
    # Every score is strictly less than 1.0 (unless perfect)
    metric = OverallProblematicHunkCount(score_threshold=1.0)
    result = metric.calculate([make_hunk_analysis(0.0), make_hunk_analysis(0.99)], [])
    assert result == MetricValue("overall.problematic_hunk_count", 2, MetricValueType.INTEGER)


def test_perfect_score_not_problematic_at_threshold_one():
    metric = OverallProblematicHunkCount(score_threshold=1.0)
    result = metric.calculate([make_hunk_analysis(1.0)], [])
    assert result == MetricValue("overall.problematic_hunk_count", 0, MetricValueType.INTEGER)
