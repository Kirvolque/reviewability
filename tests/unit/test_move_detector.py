"""Tests for MoveDetector."""

import pytest

from reviewability.diff.move_detector import MoveDetector
from reviewability.diff.similarity_calculator import DiffSimilarityCalculator
from reviewability.domain.models import Hunk, Move, MoveType


@pytest.fixture
def detector():
    return MoveDetector(DiffSimilarityCalculator())


def paired(moves: list[Move]) -> list[Move]:
    return [m for m in moves if m.move_id is not None]


# ---------------------------------------------------------------------------
# Basic structure
# ---------------------------------------------------------------------------


def test_empty_hunks(detector):
    """Empty list returns empty moves."""
    result = detector.detect([])
    assert result == []


def test_single_hunk_produces_no_moves(detector):
    """Single isolated hunk produces no moves (singletons are omitted)."""
    hunk = Hunk(
        file_path="test.py",
        source_start=1,
        source_length=5,
        target_start=1,
        target_length=5,
        added_lines=["a", "b"],
        removed_lines=["c"],
    )
    result = detector.detect([hunk])
    assert result == []


# ---------------------------------------------------------------------------
# Core detection cases (the four required scenarios)
# ---------------------------------------------------------------------------


def test_identical_additions_are_not_detected(detector):
    """Two pure-addition hunks with identical content must NOT be detected as a move.

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

    result = detector.detect([add1, add2])

    assert result == []


def test_identical_deletions_are_not_detected(detector):
    """Two pure-deletion hunks with identical content must NOT be detected as a move.

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

    result = detector.detect([del1, del2])

    assert result == []


def test_deletion_identical_to_addition_is_detected(detector):
    """A pure-deletion hunk identical to a pure-insertion hunk must be detected as a move.

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

    result = detector.detect([del_hunk, add_hunk])

    assert len(paired(result)) == 1
    move = paired(result)[0]
    assert len(move.hunks) == 2
    assert del_hunk in move.hunks
    assert add_hunk in move.hunks


def test_mixed_hunk_detected_with_similar_counterpart(detector):
    """A mixed hunk whose removed_lines closely match another hunk's added_lines
    (or vice versa) must be detected as a move with that counterpart.

    Scenario: a mixed hunk renames a function in-place (old body removed,
    new body added), and a separate pure-insertion hunk introduces the same
    old body elsewhere — they should be detected because the removed content of
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

    result = detector.detect([mixed_hunk, add_hunk])

    assert len(paired(result)) == 1
    move = paired(result)[0]
    assert len(move.hunks) == 2
    assert mixed_hunk in move.hunks
    assert add_hunk in move.hunks


# ---------------------------------------------------------------------------
# Combined and edge cases
# ---------------------------------------------------------------------------


def test_mixed_hunks_and_singletons(detector):
    """Mix of detected and singleton hunks — only the move is returned."""
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

    result = detector.detect([del_hunk, add_hunk, isolated_hunk])

    assert len(result) == 1
    move = result[0]
    assert len(move.hunks) == 2
    assert del_hunk in move.hunks
    assert add_hunk in move.hunks


def test_unrelated_hunks_produce_no_moves(detector):
    """Hunks with completely different content on both sides are never detected as moves."""
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

    result = detector.detect([hunk1, hunk2])

    assert result == []


# ---------------------------------------------------------------------------
# Similarity score on Move
# ---------------------------------------------------------------------------


def test_detected_move_has_high_similarity_for_identical_content(detector):
    """Identical del/add lines should produce similarity near 1.0 and MoveType.PURE."""
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

    result = detector.detect([del_hunk, add_hunk])

    assert len(paired(result)) == 1
    move = paired(result)[0]
    assert move.similarity > 0.9
    assert move.move_type == MoveType.PURE


def test_low_similarity_pair_has_modified_type(detector):
    """A detected pair with similarity below PURE threshold gets MoveType.MODIFIED."""
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

    result = detector.detect([del_hunk, add_hunk])

    if paired(result):
        assert paired(result)[0].move_type == MoveType.MODIFIED
