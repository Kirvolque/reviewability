import pytest

from reviewability.domain.metric import MetricResults, MetricValue, MetricValueType
from reviewability.scoring.weighted import DefaultScorer


def make_mr(**kwargs: float) -> MetricResults:
    return MetricResults(
        [MetricValue(name, value, MetricValueType.INTEGER) for name, value in kwargs.items()]
    )


def make_scorer(max_hunk_lines: float = 50.0, max_diff_lines: float = 100.0) -> DefaultScorer:
    return DefaultScorer(
        max_hunk_lines=max_hunk_lines,
        max_diff_lines=max_diff_lines,
        rewrite_in_place_line_cost=3.0,
        rewrite_moved_line_cost=4.0,
    )


# --- hunk_score ---


def test_hunk_score_at_zero():
    assert make_scorer().hunk_score(make_mr(**{"hunk.lines_changed": 0})) == 1.0


def test_hunk_score_at_max():
    assert make_scorer().hunk_score(make_mr(**{"hunk.lines_changed": 50})) == 0.0


def test_hunk_score_half():
    assert make_scorer().hunk_score(make_mr(**{"hunk.lines_changed": 25})) == 0.5


def test_hunk_score_metric_missing():
    assert make_scorer().hunk_score(MetricResults([])) == 1.0


def test_hunk_score_moved_hunk_stays_easy():
    assert make_scorer().hunk_score(make_mr(**{"hunk.lines_changed": 50, "hunk.is_likely_moved": 1})) == 1.0


def test_hunk_score_in_place_rewrite_uses_weighted_line_cost():
    mr = make_mr(**{"hunk.lines_changed": 10, "hunk.in_place_rewrite_lines": 5})
    assert make_scorer().hunk_score(mr) == 0.6


def test_hunk_score_moved_rewrite_uses_higher_weighted_line_cost():
    mr = make_mr(**{"hunk.lines_changed": 10, "hunk.moved_rewrite_lines": 5})
    assert make_scorer().hunk_score(mr) == pytest.approx(0.5)


# --- file_score ---


def test_file_score_uses_weighted_rewrite_lines():
    mr = make_mr(**{"file.lines_changed": 20, "file.in_place_rewrite_lines": 10})
    assert make_scorer().file_score(mr) == pytest.approx(0.6)


def test_file_score_with_moved_rewrite_lines():
    mr = make_mr(**{"file.lines_changed": 20, "file.moved_rewrite_lines": 10})
    assert make_scorer().file_score(mr) == pytest.approx(0.5)


def test_file_score_moved_lines_discount_both_sides_of_pair():
    mr = make_mr(**{"file.lines_changed": 20, "file.moved_lines": 10})
    assert make_scorer().file_score(mr) == 1.0


# --- overall_score ---


def test_overall_score_no_lines_metric():
    assert make_scorer().overall_score(MetricResults([])) == 1.0


def test_overall_score_full_size_no_scatter():
    # size_ratio=1.0, scatter=0.0 → 1 - 1.0 * 1.0 = 0.0
    mr = make_mr(**{"overall.lines_changed": 100})
    assert make_scorer().overall_score(mr) == 0.0


def test_overall_score_half_size_no_scatter():
    # size_ratio=0.5, scatter=0.0 → 1 - 0.5 * 1.0 = 0.5
    mr = make_mr(**{"overall.lines_changed": 50})
    assert make_scorer().overall_score(mr) == 0.5


def test_overall_score_half_size_full_scatter():
    # size_ratio=0.5, scatter=1.0 → 1 - 0.5 * 2.0 = 0.0
    mr = make_mr(**{"overall.lines_changed": 50, "overall.scatter_factor": 1})
    assert make_scorer().overall_score(mr) == 0.0


def test_overall_score_half_size_half_scatter():
    # size_ratio=0.5, scatter=0.5 → 1 - 0.5 * 1.5 = 0.25
    mr = make_mr(**{"overall.lines_changed": 50, "overall.scatter_factor": 0.5})
    assert make_scorer().overall_score(mr) == 0.25


def test_overall_score_scatter_missing_treated_as_zero():
    # scatter absent → scatter=0.0 → 1 - 0.5 * 1.0 = 0.5
    mr = make_mr(**{"overall.lines_changed": 50})
    assert make_scorer().overall_score(mr) == 0.5


def test_overall_score_rewrite_lines_increase_effective_size():
    mr = make_mr(
        **{
            "overall.lines_changed": 50,
            "overall.in_place_rewrite_lines": 10,
            "overall.scatter_factor": 0.0,
        }
    )
    assert make_scorer().overall_score(mr) == pytest.approx(0.3)


def test_overall_score_moved_rewrite_lines_increase_effective_size_more():
    mr = make_mr(
        **{
            "overall.lines_changed": 50,
            "overall.moved_rewrite_lines": 10,
            "overall.scatter_factor": 0.0,
        }
    )
    assert make_scorer().overall_score(mr) == pytest.approx(0.2)


def test_overall_score_moved_lines_remain_cheap_even_with_rewrite_penalties():
    mr = make_mr(
        **{
            "overall.lines_changed": 60,
            "overall.moved_lines": 10,
            "overall.in_place_rewrite_lines": 10,
        }
    )
    assert make_scorer().overall_score(mr) == 0.4
