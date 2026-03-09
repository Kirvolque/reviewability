import pytest

from reviewability.domain.metric import MetricResults, MetricValue, MetricValueType
from reviewability.scoring.weighted import DefaultScorer


def make_mr(**kwargs: float) -> MetricResults:
    return MetricResults(
        [MetricValue(name, value, MetricValueType.INTEGER) for name, value in kwargs.items()]
    )


def make_scorer(max_hunk_lines: float = 50.0, max_diff_lines: float = 100.0) -> DefaultScorer:
    return DefaultScorer(max_hunk_lines=max_hunk_lines, max_diff_lines=max_diff_lines)


# --- hunk_score ---


def test_hunk_score_at_zero():
    assert make_scorer().hunk_score(make_mr(**{"hunk.lines_changed": 0})) == 1.0


def test_hunk_score_at_max():
    assert make_scorer().hunk_score(make_mr(**{"hunk.lines_changed": 50})) == 0.0


def test_hunk_score_half():
    assert make_scorer().hunk_score(make_mr(**{"hunk.lines_changed": 25})) == 0.5


def test_hunk_score_above_max_clamped():
    assert make_scorer().hunk_score(make_mr(**{"hunk.lines_changed": 200})) == 0.0


def test_hunk_score_metric_missing():
    assert make_scorer().hunk_score(MetricResults([])) == 1.0


# --- file_score ---


def test_file_score_at_zero():
    assert make_scorer().file_score(make_mr(**{"file.lines_changed": 0})) == 1.0


def test_file_score_at_max():
    assert make_scorer().file_score(make_mr(**{"file.lines_changed": 100})) == 0.0


def test_file_score_half():
    assert make_scorer().file_score(make_mr(**{"file.lines_changed": 50})) == 0.5


def test_file_score_metric_missing():
    assert make_scorer().file_score(MetricResults([])) == 1.0


# --- overall_score ---


def test_overall_score_no_lines_metric():
    assert make_scorer().overall_score(MetricResults([])) == 1.0


def test_overall_score_full_size_no_churn():
    # size_ratio=1.0, churn=0.0 → 1 - 1.0 * 1.0 = 0.0
    mr = make_mr(**{"overall.lines_changed": 100, "overall.churn_complexity": 0})
    assert make_scorer().overall_score(mr) == 0.0


def test_overall_score_half_size_no_churn():
    # size_ratio=0.5, churn=0.0 → 1 - 0.5 * 1.0 = 0.5
    mr = make_mr(**{"overall.lines_changed": 50, "overall.churn_complexity": 0})
    assert make_scorer().overall_score(mr) == 0.5


def test_overall_score_half_size_full_churn():
    # size_ratio=0.5, churn=1.0 → 1 - 0.5 * 2.0 = 0.0
    mr = make_mr(**{"overall.lines_changed": 50, "overall.churn_complexity": 1})
    assert make_scorer().overall_score(mr) == 0.0


def test_overall_score_small_size_full_churn():
    # size_ratio=0.1, churn=1.0 → 1 - 0.1 * 2.0 = 0.8
    mr = make_mr(**{"overall.lines_changed": 10, "overall.churn_complexity": 1})
    assert make_scorer().overall_score(mr) == pytest.approx(0.8)


def test_overall_score_never_below_zero():
    mr = make_mr(**{"overall.lines_changed": 1000, "overall.churn_complexity": 1})
    assert make_scorer().overall_score(mr) == 0.0


def test_overall_score_churn_missing_treated_as_zero():
    # churn=0.0 implied → 1 - 0.5 * 1.0 = 0.5
    mr = make_mr(**{"overall.lines_changed": 50})
    assert make_scorer().overall_score(mr) == 0.5
