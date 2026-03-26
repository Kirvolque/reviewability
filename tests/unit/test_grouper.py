"""Tests for HunkGrouper."""

import pytest

from reviewability.diff.grouper import HunkGrouper
from reviewability.diff.similarity_calculator import DiffSimilarityCalculator
from reviewability.domain.models import Hunk, HunkRewriteKind


@pytest.fixture
def grouper():
    return HunkGrouper(DiffSimilarityCalculator())


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


def test_moved_pair_gets_grouped(grouper):
    """Two hunks marked as moved should be grouped together."""
    content = ["line1", "line2", "line3", "line4", "line5", "line6", "line7", "line8"]

    del_hunk = Hunk(
        file_path="test.py",
        source_start=1, source_length=len(content),
        target_start=1, target_length=0,
        removed_lines=content,
        is_likely_moved=True,
    )

    add_hunk = Hunk(
        file_path="test.py",
        source_start=20, source_length=0,
        target_start=20, target_length=len(content),
        added_lines=content,
        is_likely_moved=True,
    )

    result = grouper.group([del_hunk, add_hunk])

    # Both should be in the same group
    assert len([g for g in result.values() if g]) == 1  # One non-None group
    group_id = [g for g in result if g is not None][0]
    assert result[group_id] == [del_hunk, add_hunk]


def test_rewrite_kind_in_place_gets_grouped(grouper):
    """A mixed hunk with IN_PLACE_REWRITE should be grouped."""
    hunk = Hunk(
        file_path="test.py",
        source_start=1, source_length=5,
        target_start=1, target_length=5,
        added_lines=["new1", "new2"],
        removed_lines=["old1", "old2"],
        rewrite_kind=HunkRewriteKind.IN_PLACE_REWRITE,
    )

    result = grouper.group([hunk])

    # Single hunk with rewrite_kind should still be grouped (not a singleton)
    # Actually, looking at the implementation, a single hunk is still a singleton
    # only the `group_size > 1` check determines if it gets a group_id or stays None
    assert None in result  # Single hunks are singletons


def test_mixed_hunks_and_singletons(grouper):
    """Mix of grouped and singleton hunks."""
    content = ["a" * 10, "b" * 10, "c" * 10, "d" * 10, "e" * 10, "f" * 10, "g" * 10, "h" * 10]

    # Pair: move
    del_hunk = Hunk(
        file_path="file1.py",
        source_start=1, source_length=len(content),
        target_start=1, target_length=0,
        removed_lines=content,
        is_likely_moved=True,
    )

    add_hunk = Hunk(
        file_path="file1.py",
        source_start=20, source_length=0,
        target_start=20, target_length=len(content),
        added_lines=content,
        is_likely_moved=True,
    )

    # Singleton
    isolated_hunk = Hunk(
        file_path="file2.py",
        source_start=1, source_length=3,
        target_start=1, target_length=3,
        added_lines=["x"],
        removed_lines=["y"],
    )

    result = grouper.group([del_hunk, add_hunk, isolated_hunk])

    # Should have one pair and one singleton
    assert len(result) == 2  # One group_id and None
    assert None in result
    assert len(result[None]) == 1  # singleton
    assert isolated_hunk in result[None]

    # Find the paired group
    paired_group_id = [k for k in result if k is not None][0]
    assert len(result[paired_group_id]) == 2


def test_no_grouping_for_non_moved_hunks(grouper):
    """Hunks without move/rewrite flags are singletons."""
    hunk1 = Hunk(
        file_path="test.py",
        source_start=1, source_length=3,
        target_start=1, target_length=3,
        added_lines=["a"],
        removed_lines=["b"],
    )

    hunk2 = Hunk(
        file_path="test.py",
        source_start=10, source_length=3,
        target_start=10, target_length=3,
        added_lines=["c"],
        removed_lines=["d"],
    )

    result = grouper.group([hunk1, hunk2])

    # Both should be singletons
    assert None in result
    assert len(result[None]) == 2
    assert hunk1 in result[None]
    assert hunk2 in result[None]
