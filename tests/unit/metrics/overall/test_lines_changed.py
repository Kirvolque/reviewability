from reviewability.domain.metric import MetricResults, MetricValue, MetricValueType
from reviewability.domain.models import Hunk, Move, MoveType
from reviewability.domain.report import Analysis
from reviewability.metrics.overall.lines_changed import OverallLinesChanged

metric = OverallLinesChanged()


def make_hunk_analysis(lines_changed: int) -> Analysis:
    return Analysis(
        subject=Hunk(file_path="a.py"),
        metrics=MetricResults(
            [MetricValue("hunk.lines_changed", lines_changed, MetricValueType.INTEGER)]
        ),
        score=1.0,
    )


def make_move_analysis(*hunks: Hunk) -> Analysis:
    return Analysis(
        subject=Move(
            move_id=1,
            hunks=hunks,
            similarity=1.0,
            move_type=MoveType.PURE,
            length=0,
        ),
        metrics=MetricResults([]),
        score=1.0,
    )


def test_no_hunks():
    result = metric.calculate([], [], [])
    assert result.name == "overall.lines_changed"
    assert result.value == 0
    assert result.value_type == MetricValueType.INTEGER


def test_single_hunk():
    result = metric.calculate([make_hunk_analysis(5)], [], [])
    assert result.value == 5


def test_multiple_hunks():
    result = metric.calculate([make_hunk_analysis(3), make_hunk_analysis(7)], [], [])
    assert result.value == 10


def test_hunk_missing_metric_is_skipped():
    # An Analysis without hunk.lines_changed must not crash — it is simply ignored.
    hunk_without_metric = Analysis(
        subject=Hunk(file_path="a.py"),
        metrics=MetricResults([]),
        score=1.0,
    )
    result = metric.calculate([hunk_without_metric, make_hunk_analysis(4)], [], [])
    assert result.value == 4


def test_move_hunks_are_included_in_raw_size():
    moved_hunk = Hunk(
        file_path="a.py",
        added_lines=["new one", "new two", "new three"],
        removed_lines=["old one", "old two"],
    )

    result = metric.calculate([], [], [make_move_analysis(moved_hunk)])

    assert result.value == 5


def test_singleton_and_move_hunks_are_combined():
    moved_hunk = Hunk(file_path="a.py", added_lines=["new"], removed_lines=["old"])

    result = metric.calculate([make_hunk_analysis(3)], [], [make_move_analysis(moved_hunk)])

    assert result.value == 5
