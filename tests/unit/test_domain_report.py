from reviewability.domain.models import FileDiff, Hunk
from reviewability.domain.report import (
    Analysis,
    AnalysisReport,
    Cause,
    MetricResults,
    MetricValue,
    MetricValueType,
    OverallAnalysis,
    OverallMetricResult,
)


def make_metric_value(name: str = "m", value: int = 1) -> MetricValue:
    return MetricValue(name=name, value=value, value_type=MetricValueType.INTEGER)


def make_hunk() -> Hunk:
    return Hunk(
        file_path="a.py",
        source_start=1,
        source_length=1,
        target_start=1,
        target_length=1,
    )


def make_file() -> FileDiff:
    return FileDiff(path="a.py", old_path=None, is_new_file=False, is_deleted_file=False)


# --- MetricValue tests ---


def test_metric_value_fields():
    mv = MetricValue(name="foo", value=42, value_type=MetricValueType.INTEGER)
    assert mv.name == "foo"
    assert mv.value == 42
    assert mv.value_type == MetricValueType.INTEGER


def test_metric_value_equality():
    mv1 = MetricValue("a", 1, MetricValueType.INTEGER)
    mv2 = MetricValue("a", 1, MetricValueType.INTEGER)
    assert mv1 == mv2


def test_metric_value_inequality_name():
    mv1 = MetricValue("a", 1, MetricValueType.INTEGER)
    mv2 = MetricValue("b", 1, MetricValueType.INTEGER)
    assert mv1 != mv2


def test_metric_value_inequality_value():
    mv1 = MetricValue("a", 1, MetricValueType.INTEGER)
    mv2 = MetricValue("a", 2, MetricValueType.INTEGER)
    assert mv1 != mv2


def test_metric_value_frozen():
    mv = MetricValue("a", 1, MetricValueType.INTEGER)
    try:
        mv.value = 2  # type: ignore[misc]
        assert False, "Should have raised FrozenInstanceError"
    except Exception:
        pass


def test_metric_value_type_ratio():
    mv = MetricValue("ratio_metric", 0.75, MetricValueType.RATIO)
    assert mv.value_type == MetricValueType.RATIO


def test_metric_value_type_boolean():
    mv = MetricValue("bool_metric", True, MetricValueType.BOOLEAN)
    assert mv.value_type == MetricValueType.BOOLEAN


# --- MetricResults tests ---


def test_metric_results_get_existing():
    mv = make_metric_value("foo")
    mr = MetricResults([mv])
    assert mr.get("foo") == mv


def test_metric_results_get_missing():
    mr = MetricResults([])
    assert mr.get("nonexistent") is None


def test_metric_results_all():
    mv1 = make_metric_value("a")
    mv2 = make_metric_value("b")
    mr = MetricResults([mv1, mv2])
    assert mr.all() == [mv1, mv2]


def test_metric_results_all_empty():
    mr = MetricResults([])
    assert mr.all() == []


def test_metric_results_iter():
    mv1 = make_metric_value("a")
    mv2 = make_metric_value("b")
    mr = MetricResults([mv1, mv2])
    items = list(mr)
    assert items == [mv1, mv2]


def test_metric_results_len():
    mr = MetricResults([make_metric_value("a"), make_metric_value("b")])
    assert len(mr) == 2


def test_metric_results_len_empty():
    mr = MetricResults([])
    assert len(mr) == 0


def test_metric_results_equality():
    mv = make_metric_value("x")
    mr1 = MetricResults([mv])
    mr2 = MetricResults([mv])
    assert mr1 == mr2


def test_metric_results_inequality():
    mr1 = MetricResults([make_metric_value("a")])
    mr2 = MetricResults([make_metric_value("b")])
    assert mr1 != mr2


def test_metric_results_eq_non_metric_results():
    mr = MetricResults([])
    result = mr.__eq__("not a MetricResults")
    assert result is NotImplemented


def test_metric_results_repr():
    mv = MetricValue("foo", 1, MetricValueType.INTEGER)
    mr = MetricResults([mv])
    r = repr(mr)
    assert "MetricResults" in r


def test_metric_results_deduplicates_by_name():
    mv1 = MetricValue("a", 1, MetricValueType.INTEGER)
    mv2 = MetricValue("a", 2, MetricValueType.INTEGER)
    mr = MetricResults([mv1, mv2])
    # Last one wins when same name
    assert len(mr) == 1
    assert mr.get("a") == mv2


# --- Cause tests ---


def test_cause_with_metric_value():
    mv = make_metric_value("m")
    cause = Cause(value=mv, remediation="Fix it")
    assert cause.value == mv
    assert cause.remediation == "Fix it"


def test_cause_remediation_defaults_empty():
    mv = make_metric_value("m")
    cause = Cause(value=mv)
    assert cause.remediation == ""


def test_cause_with_hunk_analysis():
    ha = Analysis(subject=make_hunk(), metrics=MetricResults([]), score=0.3)
    cause = Cause(value=ha)
    assert cause.value == ha
    assert cause.remediation == ""


def test_cause_with_file_analysis():
    fa = Analysis(subject=make_file(), metrics=MetricResults([]), score=0.4)
    cause = Cause(value=fa)
    assert cause.value == fa


def test_cause_frozen():
    mv = make_metric_value("m")
    cause = Cause(value=mv)
    try:
        cause.remediation = "new"  # type: ignore[misc]
        assert False, "Should have raised FrozenInstanceError"
    except Exception:
        pass


def test_cause_equality():
    mv = make_metric_value("m")
    c1 = Cause(value=mv, remediation="r")
    c2 = Cause(value=mv, remediation="r")
    assert c1 == c2


# --- Analysis (hunk) tests ---


def test_hunk_analysis_fields():
    hunk = make_hunk()
    metrics = MetricResults([make_metric_value("a")])
    ha = Analysis(subject=hunk, metrics=metrics, score=0.8)
    assert ha.subject == hunk
    assert ha.metrics == metrics
    assert ha.score == 0.8
    assert ha.causes == []


def test_hunk_analysis_with_causes():
    hunk = make_hunk()
    mv = make_metric_value("m")
    cause = Cause(value=mv, remediation="fix")
    ha = Analysis(subject=hunk, metrics=MetricResults([mv]), score=0.5, causes=[cause])
    assert ha.causes == [cause]


def test_hunk_analysis_frozen():
    ha = Analysis(subject=make_hunk(), metrics=MetricResults([]), score=1.0)
    try:
        ha.score = 0.5  # type: ignore[misc]
        assert False, "Should have raised FrozenInstanceError"
    except Exception:
        pass


def test_hunk_analysis_perfect_score():
    ha = Analysis(subject=make_hunk(), metrics=MetricResults([]), score=1.0)
    assert ha.score == 1.0


def test_hunk_analysis_zero_score():
    ha = Analysis(subject=make_hunk(), metrics=MetricResults([]), score=0.0)
    assert ha.score == 0.0


# --- Analysis (file) tests ---


def test_file_analysis_fields():
    f = make_file()
    metrics = MetricResults([make_metric_value("b")])
    fa = Analysis(subject=f, metrics=metrics, score=0.7)
    assert fa.subject == f
    assert fa.metrics == metrics
    assert fa.score == 0.7
    assert fa.causes == []


def test_file_analysis_with_causes():
    mv = make_metric_value("m")
    cause = Cause(value=mv, remediation="hint")
    fa = Analysis(subject=make_file(), metrics=MetricResults([mv]), score=0.3, causes=[cause])
    assert fa.causes == [cause]


def test_file_analysis_frozen():
    fa = Analysis(subject=make_file(), metrics=MetricResults([]), score=1.0)
    try:
        fa.score = 0.0  # type: ignore[misc]
        assert False, "Should have raised FrozenInstanceError"
    except Exception:
        pass


def test_file_analysis_multiple_causes():
    mv1 = make_metric_value("a")
    mv2 = make_metric_value("b")
    c1 = Cause(value=mv1)
    c2 = Cause(value=mv2)
    fa = Analysis(
        subject=make_file(), metrics=MetricResults([mv1, mv2]), score=0.2, causes=[c1, c2]
    )
    assert len(fa.causes) == 2


# --- OverallMetricResult tests ---


def test_overall_metric_result_fields():
    mv = make_metric_value("overall.m")
    omr = OverallMetricResult(value=mv)
    assert omr.value == mv
    assert omr.causes == []
    assert omr.remediation == ""


def test_overall_metric_result_with_causes():
    mv = make_metric_value("overall.m")
    ha = Analysis(subject=make_hunk(), metrics=MetricResults([]), score=0.1)
    cause = Cause(value=ha)
    omr = OverallMetricResult(value=mv, causes=[cause])
    assert omr.causes == [cause]


def test_overall_metric_result_with_remediation():
    mv = make_metric_value("overall.m")
    omr = OverallMetricResult(value=mv, remediation="Fix it")
    assert omr.remediation == "Fix it"


def test_overall_metric_result_frozen():
    mv = make_metric_value("overall.m")
    omr = OverallMetricResult(value=mv)
    try:
        omr.value = make_metric_value("other")  # type: ignore[misc]
        assert False, "Should have raised FrozenInstanceError"
    except Exception:
        pass


# --- OverallAnalysis tests ---


def test_overall_analysis_fields():
    metrics = MetricResults([make_metric_value("overall.m")])
    oa = OverallAnalysis(metrics=metrics, score=0.9)
    assert oa.metrics == metrics
    assert oa.score == 0.9
    assert oa.metric_results == []


def test_overall_analysis_with_results():
    mv = make_metric_value("overall.m")
    omr = OverallMetricResult(value=mv)
    oa = OverallAnalysis(
        metrics=MetricResults([mv]),
        score=0.5,
        metric_results=[omr],
    )
    assert oa.metric_results == [omr]


def test_overall_analysis_frozen():
    oa = OverallAnalysis(metrics=MetricResults([]), score=1.0)
    try:
        oa.score = 0.0  # type: ignore[misc]
        assert False, "Should have raised FrozenInstanceError"
    except Exception:
        pass


# --- AnalysisReport tests ---


def test_analysis_report_fields():
    oa = OverallAnalysis(metrics=MetricResults([]), score=1.0)
    ha = Analysis(subject=make_hunk(), metrics=MetricResults([]), score=0.8)
    fa = Analysis(subject=make_file(), metrics=MetricResults([]), score=0.9)
    report = AnalysisReport(overall=oa, files=[fa], hunks=[ha])
    assert report.overall == oa
    assert report.files == [fa]
    assert report.hunks == [ha]


def test_analysis_report_empty_files_and_hunks():
    oa = OverallAnalysis(metrics=MetricResults([]), score=1.0)
    report = AnalysisReport(overall=oa, files=[], hunks=[])
    assert report.files == []
    assert report.hunks == []


def test_analysis_report_frozen():
    oa = OverallAnalysis(metrics=MetricResults([]), score=1.0)
    report = AnalysisReport(overall=oa, files=[], hunks=[])
    try:
        report.files = []  # type: ignore[misc]
        assert False, "Should have raised FrozenInstanceError"
    except Exception:
        pass


def test_analysis_report_multiple_hunks_and_files():
    oa = OverallAnalysis(metrics=MetricResults([]), score=0.7)
    ha1 = Analysis(subject=make_hunk(), metrics=MetricResults([]), score=0.5)
    ha2 = Analysis(subject=make_hunk(), metrics=MetricResults([]), score=0.9)
    fa1 = Analysis(subject=make_file(), metrics=MetricResults([]), score=0.6)
    fa2 = Analysis(subject=make_file(), metrics=MetricResults([]), score=0.8)
    report = AnalysisReport(overall=oa, files=[fa1, fa2], hunks=[ha1, ha2])
    assert len(report.hunks) == 2
    assert len(report.files) == 2
