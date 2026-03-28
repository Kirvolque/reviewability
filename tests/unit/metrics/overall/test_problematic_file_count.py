from reviewability.domain.metric import MetricResults, MetricValueType
from reviewability.domain.models import FileDiff, Hunk
from reviewability.domain.report import Analysis
from reviewability.metrics.overall.problematic_file_count import OverallProblematicFileCount


def make_hunk() -> Hunk:
    return Hunk(
        file_path="a.py",
        source_start=1,
        source_length=1,
        target_start=1,
        target_length=1,
    )


def make_file_analysis(score: float, hunk_count: int = 2) -> Analysis:
    return Analysis(
        subject=FileDiff(
            path="a.py",
            old_path=None,
            is_new_file=False,
            is_deleted_file=False,
            hunks=[make_hunk() for _ in range(hunk_count)],
        ),
        metrics=MetricResults([]),
        score=score,
    )


def test_none_problematic():
    metric = OverallProblematicFileCount(score_threshold=0.5)
    result = metric.calculate([], [make_file_analysis(0.6), make_file_analysis(1.0)], [])
    assert result.name == "overall.problematic_file_count"
    assert result.value == 0
    assert result.value_type == MetricValueType.INTEGER


def test_some_problematic():
    metric = OverallProblematicFileCount(score_threshold=0.5)
    result = metric.calculate([], [make_file_analysis(0.2), make_file_analysis(0.8)], [])
    assert result.value == 1


def test_threshold_boundary_is_exclusive():
    metric = OverallProblematicFileCount(score_threshold=0.5)
    result = metric.calculate([], [make_file_analysis(0.5)], [])
    assert result.value == 0


def test_single_hunk_files_are_ignored():
    """Files with only one hunk are excluded even if their score is low."""
    metric = OverallProblematicFileCount(score_threshold=0.5)
    single_hunk = make_file_analysis(score=0.1, hunk_count=1)
    multi_hunk = make_file_analysis(score=0.1, hunk_count=2)
    result = metric.calculate([], [single_hunk, multi_hunk], [])
    assert result.value == 1


def test_zero_hunk_files_are_ignored():
    """Files with no hunks are excluded regardless of score."""
    metric = OverallProblematicFileCount(score_threshold=0.5)
    result = metric.calculate([], [make_file_analysis(score=0.0, hunk_count=0)], [])
    assert result.value == 0
