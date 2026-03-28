"""Tests for OverallEditComplexity metric."""

import pytest

from reviewability.domain.models import HunkGroup
from reviewability.domain.report import Analysis
from reviewability.metrics.overall.edit_complexity import OverallEditComplexity


@pytest.fixture
def metric():
    return OverallEditComplexity()


def _make_group_analysis(score: float) -> Analysis:
    return Analysis(subject=HunkGroup(group_id=None, hunks=()), metrics=None, score=score)


def test_metric_attributes(metric):
    """Metric has proper name, type, description, and remediation."""
    assert metric.name == "overall.edit_complexity"
    assert metric.value_type.value == "ratio"
    assert "complex" in metric.description.lower() or "complexity" in metric.description.lower()
    assert metric.remediation is not None
    assert len(metric.remediation) > 0


def test_empty_groups(metric):
    """No groups returns score of 1.0 (no complexity)."""
    result = metric.calculate([], [], [])
    assert result.value == 1.0
    assert result.name == "overall.edit_complexity"


def test_single_group_score_propagates(metric):
    """Single group: overall score equals the group score."""
    group_analysis = _make_group_analysis(score=0.7)
    result = metric.calculate([], [], [group_analysis])
    assert result.value == pytest.approx(0.7)


def test_averages_multiple_group_scores(metric):
    """Multiple groups: overall is their average (rounded to 2 dp by MetricValue)."""
    groups = [_make_group_analysis(s) for s in [0.4, 0.8, 1.0]]
    result = metric.calculate([], [], groups)
    assert result.value == round((0.4 + 0.8 + 1.0) / 3, 2)


def test_all_high_scores_give_high_result(metric):
    """All groups scoring near 1.0 → overall near 1.0."""
    groups = [_make_group_analysis(s) for s in [0.95, 0.98, 1.0]]
    result = metric.calculate([], [], groups)
    assert result.value > 0.9


def test_all_low_scores_give_low_result(metric):
    """All groups scoring low → overall is low."""
    groups = [_make_group_analysis(s) for s in [0.1, 0.2, 0.15]]
    result = metric.calculate([], [], groups)
    assert result.value < 0.3
