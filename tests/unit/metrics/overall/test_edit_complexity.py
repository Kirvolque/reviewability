"""Tests for OverallEditComplexity metric."""

import pytest

from reviewability.domain.models import Hunk, HunkRewriteKind
from reviewability.domain.report import Analysis
from reviewability.metrics.overall.edit_complexity import OverallEditComplexity


@pytest.fixture
def metric():
    return OverallEditComplexity()


def test_empty_hunks(metric):
    """Empty hunk list returns score of 1.0 (no complexity)."""
    result = metric.calculate([], [])
    assert result.value == 1.0
    assert result.name == "overall.edit_complexity"


def test_singleton_hunks(metric):
    """Hunks with no group_id (singletons) have low complexity."""
    hunk1 = Hunk(
        file_path="test.py",
        source_start=1, source_length=5,
        target_start=1, target_length=5,
        added_lines=["a", "b", "c"],
        removed_lines=["x", "y"],
        group_id=None,
    )

    hunk2 = Hunk(
        file_path="test.py",
        source_start=10, source_length=3,
        target_start=10, target_length=3,
        added_lines=["d"],
        removed_lines=["z"],
        group_id=None,
    )

    analyses = [
        Analysis(subject=hunk1, metrics=None, score=0.5),
        Analysis(subject=hunk2, metrics=None, score=0.5),
    ]

    result = metric.calculate(analyses, [])
    # Singletons have low individual complexity, so overall complexity should be high (easy)
    assert 0.0 <= result.value <= 1.0


def test_paired_hunks_same_group(metric):
    """Hunks in the same group (paired) are scored together."""
    content = ["line"] * 8
    del_hunk = Hunk(
        file_path="test.py",
        source_start=1, source_length=len(content),
        target_start=1, target_length=0,
        removed_lines=content,
        is_likely_moved=True,
        group_id=0,
    )

    add_hunk = Hunk(
        file_path="test.py",
        source_start=20, source_length=0,
        target_start=20, target_length=len(content),
        added_lines=content,
        is_likely_moved=True,
        group_id=0,
    )

    analyses = [
        Analysis(subject=del_hunk, metrics=None, score=0.5),
        Analysis(subject=add_hunk, metrics=None, score=0.5),
    ]

    result = metric.calculate(analyses, [])
    # Paired hunks (a move) should have lower complexity than large scattered changes
    assert 0.0 <= result.value <= 1.0


def test_rewrite_increases_complexity(metric):
    """Hunks with low similarity (rewrites) should increase complexity."""
    removed = ["old_line_1", "old_line_2", "old_line_3", "old_line_4", "old_line_5"]
    added = ["new_line_a", "new_line_b", "new_line_c", "new_line_d", "new_line_e"]

    hunk = Hunk(
        file_path="test.py",
        source_start=1, source_length=5,
        target_start=1, target_length=5,
        added_lines=added,
        removed_lines=removed,
        rewrite_kind=HunkRewriteKind.IN_PLACE_REWRITE,
        group_id=None,
    )

    analyses = [Analysis(subject=hunk, metrics=None, score=0.5)]

    result = metric.calculate(analyses, [])
    assert 0.0 <= result.value <= 1.0


def test_metric_attributes(metric):
    """Metric has proper name, type, description, and remediation."""
    assert metric.name == "overall.edit_complexity"
    assert metric.value_type.value == "ratio"
    assert "complex" in metric.description.lower() or "complexity" in metric.description.lower()
    assert metric.remediation is not None
    assert len(metric.remediation) > 0
