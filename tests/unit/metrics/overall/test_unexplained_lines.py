from reviewability.domain.metric import MetricResults, MetricValue, MetricValueType
from reviewability.domain.models import Hunk, Move, MoveType
from reviewability.domain.report import Analysis
from reviewability.metrics.overall.unexplained_lines import OverallUnexplainedLines

metric = OverallUnexplainedLines()


def make_hunk_analysis(lines_changed: int) -> Analysis:
    return Analysis(
        subject=Hunk(file_path="a.py"),
        metrics=MetricResults(
            [MetricValue("hunk.lines_changed", lines_changed, MetricValueType.INTEGER)]
        ),
        score=1.0,
    )


def make_move_analysis(
    residual_removed_lines: tuple[str, ...] = (),
    residual_added_lines: tuple[str, ...] = (),
) -> Analysis:
    return Analysis(
        subject=Move(
            move_id=1,
            hunks=(),
            similarity=1.0,
            move_type=MoveType.PURE,
            length=0,
            residual_removed_lines=residual_removed_lines,
            residual_added_lines=residual_added_lines,
        ),
        metrics=MetricResults([]),
        score=1.0,
    )


def test_no_hunks_or_moves_has_no_unexplained_lines():
    result = metric.calculate([], [], [])

    assert result.name == "overall.unexplained_lines"
    assert result.value == 0
    assert result.value_type == MetricValueType.INTEGER


def test_singleton_hunk_lines_are_unexplained():
    result = metric.calculate([make_hunk_analysis(5)], [], [])

    assert result.value == 5


def test_pure_move_has_no_unexplained_lines():
    result = metric.calculate([], [], [make_move_analysis()])

    assert result.value == 0


def test_modified_move_counts_only_exact_residual_lines():
    result = metric.calculate(
        [],
        [],
        [make_move_analysis(("old condition",), ("new condition", "new branch"))],
    )

    assert result.value == 3


def test_singleton_and_move_residual_lines_are_combined():
    result = metric.calculate(
        [make_hunk_analysis(4)],
        [],
        [make_move_analysis(("old",), ("new",))],
    )

    assert result.value == 6
