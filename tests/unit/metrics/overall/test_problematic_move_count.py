from reviewability.domain.metric import MetricResults, MetricValueType
from reviewability.domain.models import Hunk, Move, MoveType
from reviewability.domain.report import Analysis
from reviewability.metrics.overall.problematic_move_count import OverallProblematicMoveCount


def make_move_analysis(score: float) -> Analysis:
    hunk = Hunk(file_path="a.py")
    move = Move(move_id=1, hunks=(hunk,), similarity=0.95, move_type=MoveType.PURE, length=5)
    return Analysis(subject=move, metrics=MetricResults([]), score=score)


def test_none_problematic():
    metric = OverallProblematicMoveCount(score_threshold=0.5)
    result = metric.calculate([], [], [make_move_analysis(0.8), make_move_analysis(0.9)])
    assert result.name == "overall.problematic_move_count"
    assert result.value == 0
    assert result.value_type == MetricValueType.INTEGER


def test_all_problematic():
    metric = OverallProblematicMoveCount(score_threshold=0.5)
    result = metric.calculate([], [], [make_move_analysis(0.1), make_move_analysis(0.3)])
    assert result.value == 2


def test_some_problematic():
    metric = OverallProblematicMoveCount(score_threshold=0.5)
    result = metric.calculate([], [], [make_move_analysis(0.2), make_move_analysis(0.7)])
    assert result.value == 1


def test_threshold_boundary_is_exclusive():
    metric = OverallProblematicMoveCount(score_threshold=0.5)
    result = metric.calculate([], [], [make_move_analysis(0.5)])
    assert result.value == 0


def test_no_moves():
    metric = OverallProblematicMoveCount(score_threshold=0.5)
    result = metric.calculate([], [], [])
    assert result.value == 0
