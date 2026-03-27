"""Tests for HunkGrouper."""

import pytest

from reviewability.diff.grouper import HunkGrouper
from reviewability.diff.similarity_calculator import DiffSimilarityCalculator
from reviewability.domain.models import Hunk, HunkRewriteKind


@pytest.fixture
def grouper():
    return HunkGrouper(DiffSimilarityCalculator())


# ---------------------------------------------------------------------------
# Basic structure
# ---------------------------------------------------------------------------

def test_empty_hunks(grouper):
    """Empty list returns empty groups."""
    result = grouper.group([])
    assert result == {}


def test_single_hunk_is_singleton(grouper):
    """Single isolated hunk has group_id=None."""
    hunk = Hunk(
        file_path="test.py",
        source_start=1, source_length=5,
        target_start=1, target_length=5,
        added_lines=["a", "b"],
        removed_lines=["c"],
    )
    result = grouper.group([hunk])
    assert None in result
    assert result[None] == [hunk]


# ---------------------------------------------------------------------------
# Core grouping cases (the four required scenarios)
# ---------------------------------------------------------------------------

def test_identical_additions_are_not_grouped(grouper):
    """Two pure-addition hunks with identical content must NOT be grouped.

    Both have only added_lines; neither has removed_lines to compare against
    the other's added_lines, so cross-similarity is 0.
    """
    content = ["def foo():", "    pass", "    return 1", "    x = 2"]

    add1 = Hunk(
        file_path="a.py",
        source_start=1, source_length=0,
        target_start=1, target_length=len(content),
        added_lines=list(content),
    )
    add2 = Hunk(
        file_path="b.py",
        source_start=50, source_length=0,
        target_start=50, target_length=len(content),
        added_lines=list(content),
    )

    result = grouper.group([add1, add2])

    assert None in result
    assert len(result[None]) == 2
    assert add1 in result[None]
    assert add2 in result[None]


def test_identical_deletions_are_not_grouped(grouper):
    """Two pure-deletion hunks with identical content must NOT be grouped.

    Both have only removed_lines; neither has added_lines that the other's
    removed_lines could be compared against.
    """
    content = ["def foo():", "    pass", "    return 1", "    x = 2"]

    del1 = Hunk(
        file_path="a.py",
        source_start=1, source_length=len(content),
        target_start=1, target_length=0,
        removed_lines=list(content),
    )
    del2 = Hunk(
        file_path="b.py",
        source_start=50, source_length=len(content),
        target_start=50, target_length=0,
        removed_lines=list(content),
    )

    result = grouper.group([del1, del2])

    assert None in result
    assert len(result[None]) == 2
    assert del1 in result[None]
    assert del2 in result[None]


def test_deletion_identical_to_addition_is_grouped(grouper):
    """A pure-deletion hunk identical to a pure-insertion hunk must be grouped.

    This is the classic "move" scenario.
    """
    content = [
        "def compute_risk(route):",
        "    points = 0",
        "    if route.hub_handoff:",
        "        points += 3",
        "    return points",
    ]

    del_hunk = Hunk(
        file_path="risk.py",
        source_start=10, source_length=len(content),
        target_start=10, target_length=0,
        removed_lines=list(content),
    )
    add_hunk = Hunk(
        file_path="risk.py",
        source_start=80, source_length=0,
        target_start=80, target_length=len(content),
        added_lines=list(content),
    )

    result = grouper.group([del_hunk, add_hunk])

    group_ids = [k for k in result if k is not None]
    assert len(group_ids) == 1
    grouped = result[group_ids[0]]
    assert len(grouped) == 2
    assert del_hunk in grouped
    assert add_hunk in grouped


def test_mixed_hunk_groups_with_similar_counterpart(grouper):
    """A mixed hunk whose removed_lines closely match another hunk's added_lines
    (or vice versa) must be grouped with that counterpart.

    Scenario: a mixed hunk renames a function in-place (old body removed,
    new body added), and a separate pure-insertion hunk introduces the same
    old body elsewhere — they should be grouped because the removed content of
    the mixed hunk matches the added content of the insertion hunk.
    """
    old_body = [
        "    points = 0",
        "    if route.hub_handoff:",
        "        points += 3",
        "    return points",
    ]
    new_body = [
        "    score = 0",
        "    if route.remote_coverage:",
        "        score += 2",
        "    return score",
    ]

    # Mixed hunk: removes old_body, adds new_body
    mixed_hunk = Hunk(
        file_path="risk.py",
        source_start=10, source_length=len(old_body),
        target_start=10, target_length=len(new_body),
        removed_lines=list(old_body),
        added_lines=list(new_body),
    )

    # Pure insertion elsewhere that duplicates the old body
    add_hunk = Hunk(
        file_path="risk.py",
        source_start=80, source_length=0,
        target_start=80, target_length=len(old_body),
        added_lines=list(old_body),
    )

    result = grouper.group([mixed_hunk, add_hunk])

    group_ids = [k for k in result if k is not None]
    assert len(group_ids) == 1
    grouped = result[group_ids[0]]
    assert len(grouped) == 2
    assert mixed_hunk in grouped
    assert add_hunk in grouped


# ---------------------------------------------------------------------------
# Combined and edge cases
# ---------------------------------------------------------------------------

def test_mixed_hunks_and_singletons(grouper):
    """Mix of grouped and singleton hunks."""
    content = ["a" * 10, "b" * 10, "c" * 10, "d" * 10, "e" * 10, "f" * 10, "g" * 10, "h" * 10]

    del_hunk = Hunk(
        file_path="file1.py",
        source_start=1, source_length=len(content),
        target_start=1, target_length=0,
        removed_lines=content,
    )
    add_hunk = Hunk(
        file_path="file1.py",
        source_start=20, source_length=0,
        target_start=20, target_length=len(content),
        added_lines=content,
    )
    isolated_hunk = Hunk(
        file_path="file2.py",
        source_start=1, source_length=3,
        target_start=1, target_length=3,
        added_lines=["x"],
        removed_lines=["y"],
    )

    result = grouper.group([del_hunk, add_hunk, isolated_hunk])

    assert None in result
    assert len(result[None]) == 1
    assert isolated_hunk in result[None]

    paired_group_id = [k for k in result if k is not None][0]
    grouped = result[paired_group_id]
    assert len(grouped) == 2
    assert del_hunk in grouped
    assert add_hunk in grouped


def test_rewrite_kind_flag_does_not_affect_grouping(grouper):
    """Grouper is flag-agnostic: a single hunk with rewrite_kind is still a singleton."""
    hunk = Hunk(
        file_path="test.py",
        source_start=1, source_length=5,
        target_start=1, target_length=5,
        added_lines=["new1", "new2"],
        removed_lines=["old1", "old2"],
        rewrite_kind=HunkRewriteKind.IN_PLACE_REWRITE,
    )

    result = grouper.group([hunk])

    assert None in result


def test_unrelated_hunks_are_singletons(grouper):
    """Hunks with dissimilar content on both sides are never grouped."""
    hunk1 = Hunk(
        file_path="test.py",
        source_start=1, source_length=3,
        target_start=1, target_length=3,
        added_lines=["foo_alpha"],
        removed_lines=["bar_beta"],
    )
    hunk2 = Hunk(
        file_path="test.py",
        source_start=10, source_length=3,
        target_start=10, target_length=3,
        added_lines=["xyz_gamma"],
        removed_lines=["qrs_delta"],
    )

    result = grouper.group([hunk1, hunk2])

    assert None in result
    assert len(result[None]) == 2
