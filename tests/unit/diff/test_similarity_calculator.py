"""Tests for DiffSimilarityCalculator.move_aware_similarity."""

from reviewability.diff.similarity_calculator import DiffSimilarityCalculator


def calc() -> DiffSimilarityCalculator:
    return DiffSimilarityCalculator()


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_both_empty_returns_zero():
    assert calc().move_aware_similarity([], []) == 0.0


def test_deleted_empty_returns_zero():
    assert calc().move_aware_similarity([], ["a line\n"]) == 0.0


def test_added_empty_returns_zero():
    assert calc().move_aware_similarity(["a line\n"], []) == 0.0


# ---------------------------------------------------------------------------
# Exact matches
# ---------------------------------------------------------------------------


def test_identical_single_line_returns_one():
    line = "    def compute(x: int) -> int:\n"
    result = calc().move_aware_similarity([line], [line])
    assert result == 1.0


def test_identical_multiple_lines_returns_one():
    lines = [
        "def foo(x):\n",
        "    return x + 1\n",
        "    pass\n",
    ]
    result = calc().move_aware_similarity(lines, lines[:])
    assert result == 1.0


# ---------------------------------------------------------------------------
# Completely different lines
# ---------------------------------------------------------------------------


def test_completely_different_lines_returns_low_score():
    deleted = ["aaaaaaaaaaaaaaa\n", "bbbbbbbbbbbbbbb\n"]
    added = ["zzzzzzzzzzzzzzz\n", "yyyyyyyyyyyyyyy\n"]
    result = calc().move_aware_similarity(deleted, added)
    assert result < 0.2


# ---------------------------------------------------------------------------
# Normalization by max count
# ---------------------------------------------------------------------------


def test_normalized_by_larger_side_when_deleted_is_larger():
    # 3 deleted, 1 added — best match is the identical line; 2 unmatched
    line = "    return value\n"
    deleted = [line, "unrelated_a\n", "unrelated_b\n"]
    added = [line]
    result = calc().move_aware_similarity(deleted, added)
    # Matched: 1 identical (score 1.0), denominator = 3
    assert abs(result - 1.0 / 3) < 0.05


def test_normalized_by_larger_side_when_added_is_larger():
    line = "    return value\n"
    deleted = [line]
    added = [line, "unrelated_a\n", "unrelated_b\n"]
    result = calc().move_aware_similarity(deleted, added)
    # Matched: 1 identical (score 1.0), denominator = 3
    assert abs(result - 1.0 / 3) < 0.05


# ---------------------------------------------------------------------------
# Partial match
# ---------------------------------------------------------------------------


def test_partial_match_scores_between_zero_and_one():
    deleted = ["def greet(name):\n", "    return 'hello'\n"]
    added = ["def greet(name):\n", "    return 'goodbye'\n"]
    result = calc().move_aware_similarity(deleted, added)
    assert 0.5 < result < 1.0


def test_greedy_picks_best_match():
    # Two deleted lines, two added lines — best pairing should be diagonal
    deleted = ["aaaa\n", "bbbb\n"]
    added = ["aaaa\n", "cccc\n"]
    result = calc().move_aware_similarity(deleted, added)
    # "aaaa" pairs with "aaaa" (score 1.0), "bbbb" pairs with "cccc" (low)
    # total / 2 should be > 0.5
    assert result > 0.4
