"""Tests for MoveEditComplexity metric."""

import pytest

from reviewability.domain.models import Hunk, Move, MoveType
from reviewability.metrics.move.edit_complexity import MoveEditComplexity


@pytest.fixture
def metric():
    return MoveEditComplexity(max_move_lines=100, similarity_penalty=2.0)


def _make_move(hunks: list[Hunk], move_id: int | None = 0) -> Move:
    return Move(
        move_id=move_id,
        hunks=tuple(hunks),
        similarity=0.0,
        move_type=MoveType.MODIFIED,
        length=max((len(h.removed_lines) + len(h.added_lines)) for h in hunks) if hunks else 0,
    )


# ---------------------------------------------------------------------------
# Metric attributes
# ---------------------------------------------------------------------------


def test_metric_attributes(metric):
    assert metric.name == "move.edit_complexity"
    assert metric.value_type.value == "ratio"
    assert "complex" in metric.description.lower() or "complexity" in metric.description.lower()
    assert metric.remediation


# ---------------------------------------------------------------------------
# Empty move
# ---------------------------------------------------------------------------


def test_empty_move_returns_max_score(metric):
    """Empty move (no hunks) → score 1.0 (no complexity)."""
    move = Move(move_id=None, hunks=(), similarity=0.0, move_type=MoveType.MODIFIED, length=0)
    result = metric.calculate(move, [])
    assert result.value == 1.0


# ---------------------------------------------------------------------------
# Singleton moves
# ---------------------------------------------------------------------------


def test_singleton_pure_addition(metric):
    """Pure addition alone has a small fixed penalty."""
    hunk = Hunk(
        file_path="a.py",
        added_lines=["a", "b", "c", "d", "e"],
    )
    move = Move(move_id=None, hunks=(hunk,), similarity=0.0, move_type=MoveType.MODIFIED, length=5)
    result = metric.calculate(move, [])
    assert 0.0 <= result.value <= 1.0
    # pure addition penalty = (1 + 2.0 * 1.0) / 100 = 0.03; length=5 → score = 1 - 5*0.03 = 0.85
    assert result.value == pytest.approx(0.85)


def test_singleton_pure_deletion(metric):
    """Pure deletion alone has the same small fixed penalty as pure addition."""
    hunk = Hunk(
        file_path="a.py",
        removed_lines=["a", "b", "c", "d", "e"],
    )
    move = Move(move_id=None, hunks=(hunk,), similarity=0.0, move_type=MoveType.MODIFIED, length=5)
    result = metric.calculate(move, [])
    assert result.value == pytest.approx(0.85)


def test_high_similarity_scores_higher_than_low(metric):
    """A move with high similarity scores higher than one with low similarity."""
    hunk = Hunk(
        file_path="a.py",
        removed_lines=["a", "b", "c", "d", "e"],
        added_lines=["a", "b", "c", "d", "e"],
    )
    high_sim_move = Move(
        move_id=0, hunks=(hunk,), similarity=0.95, move_type=MoveType.PURE, length=10
    )
    low_sim_move = Move(
        move_id=0, hunks=(hunk,), similarity=0.3, move_type=MoveType.MODIFIED, length=10
    )
    high_result = metric.calculate(high_sim_move, [])
    low_result = metric.calculate(low_sim_move, [])
    assert high_result.value > low_result.value


# ---------------------------------------------------------------------------
# Multi-hunk moves
# ---------------------------------------------------------------------------


def test_identical_move_scores_near_max(metric):
    """A pure move (deletion + identical insertion) has very low complexity."""
    content = ["def foo():", "    return 1", "    x = 2", "    y = 3", "    z = 5"]
    del_hunk = Hunk(
        file_path="a.py",
        removed_lines=list(content),
    )
    add_hunk = Hunk(
        file_path="a.py",
        added_lines=list(content),
    )
    move = Move(
        move_id=0,
        hunks=(del_hunk, add_hunk),
        similarity=1.0,
        move_type=MoveType.PURE,
        length=len(content),
    )
    result = metric.calculate(move, [])
    # similarity=1.0 → penalty = 1/100 = 0.01; length=5 → score = 1 - 0.05 = 0.95
    assert result.value > 0.9


def test_rewrite_move_scores_lower_than_pure_move(metric):
    """A cross-hunk rewrite (low similarity) scores lower than a clean move."""
    content = ["def foo():", "    return 1", "    x = 2", "    y = 3", "    z = 5"]
    moved_del = Hunk(
        file_path="a.py",
        removed_lines=list(content),
    )
    moved_add = Hunk(
        file_path="a.py",
        added_lines=list(content),
    )
    pure_move = Move(
        move_id=0,
        hunks=(moved_del, moved_add),
        similarity=1.0,
        move_type=MoveType.PURE,
        length=len(content),
    )
    move_result = metric.calculate(pure_move, [])

    rewrite_del = Hunk(
        file_path="a.py",
        removed_lines=["old_a", "old_b", "old_c", "old_d", "old_e"],
    )
    rewrite_add = Hunk(
        file_path="a.py",
        added_lines=["new_x", "new_y", "new_z", "new_w", "new_v"],
    )
    rewrite_move = Move(
        move_id=0,
        hunks=(rewrite_del, rewrite_add),
        similarity=0.0,
        move_type=MoveType.MODIFIED,
        length=len(content),
    )
    rewrite_result = metric.calculate(rewrite_move, [])

    assert move_result.value > rewrite_result.value
