from reviewability.domain.report import MetricResults, MetricValue, MetricValueType
from reviewability.scoring.weighted import MetricWeight, WeightedReviewabilityScorer


def make_mr(*pairs: tuple[str, float]) -> MetricResults:
    return MetricResults(
        [MetricValue(name, value, MetricValueType.INTEGER) for name, value in pairs]
    )


def make_scorer(
    hunk_weights: list[MetricWeight] | None = None,
    file_weights: list[MetricWeight] | None = None,
    overall_weights: list[MetricWeight] | None = None,
) -> WeightedReviewabilityScorer:
    return WeightedReviewabilityScorer(
        hunk_weights=hunk_weights or [],
        file_weights=file_weights or [],
        overall_weights=overall_weights or [],
    )


# --- MetricWeight tests ---


def test_metric_weight_fields():
    w = MetricWeight(metric_name="hunk.lines_changed", max_value=50.0, weight=2.0)
    assert w.metric_name == "hunk.lines_changed"
    assert w.max_value == 50.0
    assert w.weight == 2.0


def test_metric_weight_default_weight():
    w = MetricWeight(metric_name="m", max_value=100.0)
    assert w.weight == 1.0


def test_metric_weight_frozen():
    w = MetricWeight(metric_name="m", max_value=10.0)
    try:
        w.weight = 5.0  # type: ignore[misc]
        assert False, "Should have raised FrozenInstanceError"
    except Exception:
        pass


# --- WeightedReviewabilityScorer: empty weights ---


def test_hunk_score_no_weights_returns_one():
    scorer = make_scorer()
    assert scorer.hunk_score(make_mr()) == 1.0


def test_file_score_no_weights_returns_one():
    scorer = make_scorer()
    assert scorer.file_score(make_mr()) == 1.0


def test_overall_score_no_weights_returns_one():
    scorer = make_scorer()
    assert scorer.overall_score(make_mr()) == 1.0


# --- hunk_score ---


def test_hunk_score_at_max_value():
    scorer = make_scorer(hunk_weights=[MetricWeight("hunk.lines_changed", max_value=50.0)])
    mr = make_mr(("hunk.lines_changed", 50))
    assert scorer.hunk_score(mr) == 0.0


def test_hunk_score_at_zero():
    scorer = make_scorer(hunk_weights=[MetricWeight("hunk.lines_changed", max_value=50.0)])
    mr = make_mr(("hunk.lines_changed", 0))
    assert scorer.hunk_score(mr) == 1.0


def test_hunk_score_half():
    scorer = make_scorer(hunk_weights=[MetricWeight("hunk.lines_changed", max_value=50.0)])
    mr = make_mr(("hunk.lines_changed", 25))
    assert scorer.hunk_score(mr) == 0.5


def test_hunk_score_above_max_clamped():
    scorer = make_scorer(hunk_weights=[MetricWeight("hunk.lines_changed", max_value=50.0)])
    mr = make_mr(("hunk.lines_changed", 200))
    # value / max = 4.0, clamped to 1.0 → score = 0.0
    assert scorer.hunk_score(mr) == 0.0


def test_hunk_score_metric_missing_ignored():
    scorer = make_scorer(hunk_weights=[MetricWeight("hunk.lines_changed", max_value=50.0)])
    mr = MetricResults([])
    # No metric present → weighted_load = 0 → score = 1.0
    assert scorer.hunk_score(mr) == 1.0


# --- file_score ---


def test_file_score_at_max_value():
    scorer = make_scorer(file_weights=[MetricWeight("file.lines_changed", max_value=100.0)])
    mr = make_mr(("file.lines_changed", 100))
    assert scorer.file_score(mr) == 0.0


def test_file_score_half():
    scorer = make_scorer(file_weights=[MetricWeight("file.lines_changed", max_value=100.0)])
    mr = make_mr(("file.lines_changed", 50))
    assert scorer.file_score(mr) == 0.5


# --- overall_score ---


def test_overall_score_at_max():
    scorer = make_scorer(overall_weights=[MetricWeight("overall.lines_changed", max_value=500.0)])
    mr = make_mr(("overall.lines_changed", 500))
    assert scorer.overall_score(mr) == 0.0


def test_overall_score_zero():
    scorer = make_scorer(overall_weights=[MetricWeight("overall.lines_changed", max_value=500.0)])
    mr = make_mr(("overall.lines_changed", 0))
    assert scorer.overall_score(mr) == 1.0


# --- multiple weights ---


def test_multiple_weights_equal():
    scorer = make_scorer(
        hunk_weights=[
            MetricWeight("hunk.a", max_value=10.0, weight=1.0),
            MetricWeight("hunk.b", max_value=10.0, weight=1.0),
        ]
    )
    # both at max → each contributes 1.0 * 1.0 / 2.0 = 0.5 → total load = 1.0 → score = 0.0
    mr = MetricResults(
        [
            MetricValue("hunk.a", 10, MetricValueType.INTEGER),
            MetricValue("hunk.b", 10, MetricValueType.INTEGER),
        ]
    )
    assert scorer.hunk_score(mr) == 0.0


def test_multiple_weights_one_missing():
    scorer = make_scorer(
        hunk_weights=[
            MetricWeight("hunk.a", max_value=10.0, weight=1.0),
            MetricWeight("hunk.b", max_value=10.0, weight=1.0),
        ]
    )
    # Only hunk.a present at max; hunk.b missing
    # weighted_load = 1.0 * 1.0 = 1.0; total_weight = 2.0 → score = 1.0 - 0.5 = 0.5
    mr = MetricResults([MetricValue("hunk.a", 10, MetricValueType.INTEGER)])
    assert scorer.hunk_score(mr) == 0.5


def test_weighted_sum_unequal_weights():
    scorer = make_scorer(
        hunk_weights=[
            MetricWeight("hunk.a", max_value=10.0, weight=3.0),
            MetricWeight("hunk.b", max_value=10.0, weight=1.0),
        ]
    )
    # hunk.a at max (1.0) with weight 3.0, hunk.b at max (1.0) with weight 1.0
    # load = (3.0 * 1.0 + 1.0 * 1.0) / 4.0 = 1.0 → score = 0.0
    mr = MetricResults(
        [
            MetricValue("hunk.a", 10, MetricValueType.INTEGER),
            MetricValue("hunk.b", 10, MetricValueType.INTEGER),
        ]
    )
    assert scorer.hunk_score(mr) == 0.0


def test_weighted_sum_partial_unequal_weights():
    import pytest

    scorer = make_scorer(
        hunk_weights=[
            MetricWeight("hunk.a", max_value=10.0, weight=3.0),
            MetricWeight("hunk.b", max_value=10.0, weight=1.0),
        ]
    )
    # hunk.a at half (0.5) with weight 3.0, hunk.b at max (1.0) with weight 1.0
    # load = (3.0 * 0.5 + 1.0 * 1.0) / 4.0 = 2.5 / 4.0 = 0.625 → score = 0.375
    mr = MetricResults(
        [
            MetricValue("hunk.a", 5, MetricValueType.INTEGER),
            MetricValue("hunk.b", 10, MetricValueType.INTEGER),
        ]
    )
    assert scorer.hunk_score(mr) == pytest.approx(0.375)


def test_zero_total_weight_returns_one():
    scorer = WeightedReviewabilityScorer(
        hunk_weights=[MetricWeight("hunk.a", max_value=10.0, weight=0.0)],
        file_weights=[],
        overall_weights=[],
    )
    mr = MetricResults([MetricValue("hunk.a", 5, MetricValueType.INTEGER)])
    assert scorer.hunk_score(mr) == 1.0


def test_score_never_below_zero():
    # Extreme value way beyond max_value
    scorer = make_scorer(hunk_weights=[MetricWeight("hunk.lines_changed", max_value=1.0)])
    mr = make_mr(("hunk.lines_changed", 1000))
    assert scorer.hunk_score(mr) == 0.0
