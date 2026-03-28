"""Tests for GroupEditComplexity metric."""

import pytest

from reviewability.domain.models import Hunk, HunkGroup
from reviewability.metrics.group.edit_complexity import GroupEditComplexity


@pytest.fixture
def metric():
    return GroupEditComplexity()


def _make_group(hunks: list[Hunk], group_id: int | None = 0) -> HunkGroup:
    return HunkGroup(group_id=group_id, hunks=tuple(hunks))


# ---------------------------------------------------------------------------
# Metric attributes
# ---------------------------------------------------------------------------

def test_metric_attributes(metric):
    assert metric.name == "group.edit_complexity"
    assert metric.value_type.value == "ratio"
    assert "complex" in metric.description.lower() or "complexity" in metric.description.lower()
    assert metric.remediation


# ---------------------------------------------------------------------------
# Empty group
# ---------------------------------------------------------------------------

def test_empty_group_returns_max_score(metric):
    """Empty group (no hunks) → score 1.0 (no complexity)."""
    group = HunkGroup(group_id=None, hunks=())
    result = metric.calculate(group, [])
    assert result.value == 1.0


# ---------------------------------------------------------------------------
# Singleton groups
# ---------------------------------------------------------------------------

def test_singleton_pure_addition(metric):
    """Pure addition alone has a small fixed penalty."""
    hunk = Hunk(
        file_path="a.py",
        source_start=1, source_length=0,
        target_start=1, target_length=5,
        added_lines=["a", "b", "c", "d", "e"],
    )
    result = metric.calculate(_make_group([hunk], group_id=None), [])
    assert 0.0 <= result.value <= 1.0
    # pure addition penalty is 0.1 complexity → score ≈ 0.9
    assert result.value == pytest.approx(0.9)


def test_singleton_pure_deletion(metric):
    """Pure deletion alone has the same small fixed penalty as pure addition."""
    hunk = Hunk(
        file_path="a.py",
        source_start=1, source_length=5,
        target_start=1, target_length=0,
        removed_lines=["a", "b", "c", "d", "e"],
    )
    result = metric.calculate(_make_group([hunk], group_id=None), [])
    assert result.value == pytest.approx(0.9)


def test_singleton_mixed_high_similarity(metric):
    """Mixed hunk with nearly identical content has low complexity (high score)."""
    lines = ["def foo():", "    return 1", "    x = 2", "    y = 3"]
    hunk = Hunk(
        file_path="a.py",
        source_start=1, source_length=4,
        target_start=1, target_length=4,
        removed_lines=lines,
        added_lines=lines[:3] + ["    y = 4"],  # one line changed
    )
    result = metric.calculate(_make_group([hunk], group_id=None), [])
    assert result.value > 0.5  # high similarity → high score


def test_singleton_mixed_low_similarity(metric):
    """Mixed hunk with very different content has higher complexity (lower score)."""
    removed = ["old_a", "old_b", "old_c", "old_d", "old_e"]
    added = ["new_x", "new_y", "new_z", "new_w", "new_v"]
    hunk = Hunk(
        file_path="a.py",
        source_start=1, source_length=5,
        target_start=1, target_length=5,
        removed_lines=removed,
        added_lines=added,
    )
    result = metric.calculate(_make_group([hunk], group_id=None), [])
    assert 0.0 <= result.value <= 1.0


# ---------------------------------------------------------------------------
# Multi-hunk groups
# ---------------------------------------------------------------------------

def test_identical_move_scores_near_max(metric):
    """A pure move (deletion + identical insertion) has very low complexity."""
    content = ["def foo():", "    return 1", "    x = 2", "    y = 3", "    z = 5"]
    del_hunk = Hunk(
        file_path="a.py",
        source_start=10, source_length=len(content),
        target_start=10, target_length=0,
        removed_lines=list(content),
    )
    add_hunk = Hunk(
        file_path="a.py",
        source_start=80, source_length=0,
        target_start=80, target_length=len(content),
        added_lines=list(content),
    )
    result = metric.calculate(_make_group([del_hunk, add_hunk]), [])
    # similarity ≈ 1.0 → complexity ≈ 0 → score ≈ 1.0
    assert result.value > 0.9


def test_rewrite_group_scores_lower_than_move(metric):
    """A cross-hunk rewrite (low similarity) scores lower than a clean move."""
    content = ["def foo():", "    return 1", "    x = 2", "    y = 3", "    z = 5"]
    moved_del = Hunk(
        file_path="a.py",
        source_start=10, source_length=len(content),
        target_start=10, target_length=0,
        removed_lines=list(content),
    )
    moved_add = Hunk(
        file_path="a.py",
        source_start=80, source_length=0,
        target_start=80, target_length=len(content),
        added_lines=list(content),
    )
    move_result = metric.calculate(_make_group([moved_del, moved_add]), [])

    rewrite_del = Hunk(
        file_path="a.py",
        source_start=10, source_length=len(content),
        target_start=10, target_length=0,
        removed_lines=["old_a", "old_b", "old_c", "old_d", "old_e"],
    )
    rewrite_add = Hunk(
        file_path="a.py",
        source_start=80, source_length=0,
        target_start=80, target_length=len(content),
        added_lines=["new_x", "new_y", "new_z", "new_w", "new_v"],
    )
    rewrite_result = metric.calculate(_make_group([rewrite_del, rewrite_add]), [])

    assert move_result.value > rewrite_result.value


def test_far_apart_low_similarity_scores_lowest(metric):
    """Low similarity + large span gives the lowest score."""
    near_del = Hunk(
        file_path="a.py",
        source_start=10, source_length=5,
        target_start=10, target_length=0,
        removed_lines=["old_a", "old_b", "old_c", "old_d", "old_e"],
    )
    near_add = Hunk(
        file_path="a.py",
        source_start=15, source_length=0,  # close
        target_start=15, target_length=5,
        added_lines=["new_x", "new_y", "new_z", "new_w", "new_v"],
    )
    near_result = metric.calculate(_make_group([near_del, near_add]), [])

    far_del = Hunk(
        file_path="a.py",
        source_start=10, source_length=5,
        target_start=10, target_length=0,
        removed_lines=["old_a", "old_b", "old_c", "old_d", "old_e"],
    )
    far_add = Hunk(
        file_path="a.py",
        source_start=600, source_length=0,  # far away
        target_start=600, target_length=5,
        added_lines=["new_x", "new_y", "new_z", "new_w", "new_v"],
    )
    far_result = metric.calculate(_make_group([far_del, far_add]), [])

    assert near_result.value > far_result.value
