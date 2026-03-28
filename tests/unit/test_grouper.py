"""Tests for HunkGrouper."""

import pytest

from reviewability.diff.grouper import HunkGrouper
from reviewability.diff.similarity_calculator import DiffSimilarityCalculator
from reviewability.domain.models import GroupType, Hunk, HunkGroup


@pytest.fixture
def grouper():
    return HunkGrouper(DiffSimilarityCalculator())


def paired(groups: list[HunkGroup]) -> list[HunkGroup]:
    return [g for g in groups if g.group_id is not None]


# ---------------------------------------------------------------------------
# Basic structure
# ---------------------------------------------------------------------------


def test_empty_hunks(grouper):
    """Empty list returns empty groups."""
    result = grouper.group([])
    assert result == []


def test_single_hunk_produces_no_groups(grouper):
    """Single isolated hunk produces no groups (singletons are omitted)."""
    hunk = Hunk(
        file_path="test.py",
        source_start=1,
        source_length=5,
        target_start=1,
        target_length=5,
        added_lines=["a", "b"],
        removed_lines=["c"],
    )
    result = grouper.group([hunk])
    assert result == []


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
        source_start=1,
        source_length=0,
        target_start=1,
        target_length=len(content),
        added_lines=list(content),
    )
    add2 = Hunk(
        file_path="b.py",
        source_start=50,
        source_length=0,
        target_start=50,
        target_length=len(content),
        added_lines=list(content),
    )

    result = grouper.group([add1, add2])

    assert result == []


def test_identical_deletions_are_not_grouped(grouper):
    """Two pure-deletion hunks with identical content must NOT be grouped.

    Both have only removed_lines; neither has added_lines that the other's
    removed_lines could be compared against.
    """
    content = ["def foo():", "    pass", "    return 1", "    x = 2"]

    del1 = Hunk(
        file_path="a.py",
        source_start=1,
        source_length=len(content),
        target_start=1,
        target_length=0,
        removed_lines=list(content),
    )
    del2 = Hunk(
        file_path="b.py",
        source_start=50,
        source_length=len(content),
        target_start=50,
        target_length=0,
        removed_lines=list(content),
    )

    result = grouper.group([del1, del2])

    assert result == []


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
        source_start=10,
        source_length=len(content),
        target_start=10,
        target_length=0,
        removed_lines=list(content),
    )
    add_hunk = Hunk(
        file_path="risk.py",
        source_start=80,
        source_length=0,
        target_start=80,
        target_length=len(content),
        added_lines=list(content),
    )

    result = grouper.group([del_hunk, add_hunk])

    assert len(paired(result)) == 1
    group = paired(result)[0]
    assert len(group.hunks) == 2
    assert del_hunk in group.hunks
    assert add_hunk in group.hunks


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
        source_start=10,
        source_length=len(old_body),
        target_start=10,
        target_length=len(new_body),
        removed_lines=list(old_body),
        added_lines=list(new_body),
    )

    # Pure insertion elsewhere that duplicates the old body
    add_hunk = Hunk(
        file_path="risk.py",
        source_start=80,
        source_length=0,
        target_start=80,
        target_length=len(old_body),
        added_lines=list(old_body),
    )

    result = grouper.group([mixed_hunk, add_hunk])

    assert len(paired(result)) == 1
    group = paired(result)[0]
    assert len(group.hunks) == 2
    assert mixed_hunk in group.hunks
    assert add_hunk in group.hunks


# ---------------------------------------------------------------------------
# Combined and edge cases
# ---------------------------------------------------------------------------


def test_mixed_hunks_and_singletons(grouper):
    """Mix of grouped and singleton hunks — only the group is returned."""
    content = ["a" * 10, "b" * 10, "c" * 10, "d" * 10, "e" * 10, "f" * 10, "g" * 10, "h" * 10]

    del_hunk = Hunk(
        file_path="file1.py",
        source_start=1,
        source_length=len(content),
        target_start=1,
        target_length=0,
        removed_lines=content,
    )
    add_hunk = Hunk(
        file_path="file1.py",
        source_start=20,
        source_length=0,
        target_start=20,
        target_length=len(content),
        added_lines=content,
    )
    isolated_hunk = Hunk(
        file_path="file2.py",
        source_start=1,
        source_length=3,
        target_start=1,
        target_length=3,
        added_lines=["x"],
        removed_lines=["y"],
    )

    result = grouper.group([del_hunk, add_hunk, isolated_hunk])

    assert len(result) == 1
    group = result[0]
    assert len(group.hunks) == 2
    assert del_hunk in group.hunks
    assert add_hunk in group.hunks


def test_unrelated_hunks_produce_no_groups(grouper):
    """Hunks with completely different content on both sides are never grouped."""
    hunk1 = Hunk(
        file_path="test.py",
        source_start=1,
        source_length=3,
        target_start=1,
        target_length=3,
        added_lines=["x" * 20],
        removed_lines=["x" * 20],
    )
    hunk2 = Hunk(
        file_path="test.py",
        source_start=10,
        source_length=3,
        target_start=10,
        target_length=3,
        added_lines=["y" * 20],
        removed_lines=["y" * 20],
    )

    result = grouper.group([hunk1, hunk2])

    assert result == []


# ---------------------------------------------------------------------------
# Similarity score on HunkGroup
# ---------------------------------------------------------------------------


def test_paired_group_has_high_similarity_for_identical_content(grouper):
    """Identical del/add lines should produce similarity near 1.0 and GroupType.MOVED."""
    content = [
        "def compute(x):\n",
        "    return x * 2\n",
        "    pass\n",
    ]
    del_hunk = Hunk(
        file_path="a.py",
        source_start=1,
        source_length=len(content),
        target_start=1,
        target_length=0,
        removed_lines=list(content),
    )
    add_hunk = Hunk(
        file_path="b.py",
        source_start=50,
        source_length=0,
        target_start=50,
        target_length=len(content),
        added_lines=list(content),
    )

    result = grouper.group([del_hunk, add_hunk])

    assert len(paired(result)) == 1
    group = paired(result)[0]
    assert group.similarity > 0.9
    assert group.group_type == GroupType.MOVED


def test_low_similarity_pair_has_moved_modified_type(grouper):
    """A grouped pair with similarity below MOVED threshold gets GroupType.MOVED_MODIFIED."""
    content_del = ["def compute(x):\n", "    return x * 2\n", "    pass\n"]
    content_add = ["def transform(z):\n", "    result = z + 99\n", "    return result\n"]
    del_hunk = Hunk(
        file_path="a.py",
        source_start=1,
        source_length=len(content_del),
        target_start=1,
        target_length=0,
        removed_lines=content_del,
    )
    add_hunk = Hunk(
        file_path="b.py",
        source_start=50,
        source_length=0,
        target_start=50,
        target_length=len(content_add),
        added_lines=content_add,
    )

    result = grouper.group([del_hunk, add_hunk])

    if paired(result):
        assert paired(result)[0].group_type == GroupType.MOVED_MODIFIED
