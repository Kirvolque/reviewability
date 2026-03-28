from reviewability.domain.metric import MetricResults, MetricValue, MetricValueType
from reviewability.domain.models import FileDiff, Hunk
from reviewability.domain.report import Analysis, AnalysisReport, OverallAnalysis


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


def test_metric_value_frozen():
    mv = MetricValue("a", 1, MetricValueType.INTEGER)
    try:
        mv.value = 2  # type: ignore[misc]
        assert False, "Should have raised FrozenInstanceError"
    except Exception:
        pass


def test_metric_value_remediation_defaults_none():
    mv = MetricValue("a", 1, MetricValueType.INTEGER)
    assert mv.remediation is None


def test_metric_value_remediation_set():
    mv = MetricValue("a", 1, MetricValueType.INTEGER, remediation="Fix it")
    assert mv.remediation == "Fix it"


# --- MetricResults tests ---


def test_metric_results_metric_existing():
    mv = make_metric_value("foo")
    mr = MetricResults([mv])
    assert mr.metric("foo") == mv


def test_metric_results_metric_missing():
    mr = MetricResults([])
    assert mr.metric("nonexistent") is None


def test_metric_results_iter():
    mv1 = make_metric_value("a")
    mv2 = make_metric_value("b")
    mr = MetricResults([mv1, mv2])
    items = list(mr)
    assert items == [mv1, mv2]


def test_metric_results_len():
    mr = MetricResults([make_metric_value("a"), make_metric_value("b")])
    assert len(mr) == 2


def test_metric_results_equality():
    mv = make_metric_value("x")
    mr1 = MetricResults([mv])
    mr2 = MetricResults([mv])
    assert mr1 == mr2


def test_metric_results_inequality():
    mr1 = MetricResults([make_metric_value("a")])
    mr2 = MetricResults([make_metric_value("b")])
    assert mr1 != mr2


def test_metric_results_deduplicates_by_name():
    mv1 = MetricValue("a", 1, MetricValueType.INTEGER)
    mv2 = MetricValue("a", 2, MetricValueType.INTEGER)
    mr = MetricResults([mv1, mv2])
    # Last one wins when same name
    assert len(mr) == 1
    assert mr.metric("a") == mv2


# --- Analysis (hunk) tests ---


def test_hunk_analysis_fields():
    hunk = make_hunk()
    metrics = MetricResults([make_metric_value("a")])
    ha = Analysis(subject=hunk, metrics=metrics, score=0.8)
    assert ha.subject == hunk
    assert ha.metrics == metrics
    assert ha.score == 0.8


def test_hunk_analysis_frozen():
    ha = Analysis(subject=make_hunk(), metrics=MetricResults([]), score=1.0)
    try:
        ha.score = 0.5  # type: ignore[misc]
        assert False, "Should have raised FrozenInstanceError"
    except Exception:
        pass


def test_analysis_metric():
    mv = make_metric_value("m")
    ha = Analysis(subject=make_hunk(), metrics=MetricResults([mv]), score=0.8)
    assert ha.metric("m") == mv


def test_analysis_metric_missing_returns_none():
    ha = Analysis(subject=make_hunk(), metrics=MetricResults([]), score=1.0)
    assert ha.metric("nonexistent") is None


# --- OverallAnalysis tests ---


def test_overall_analysis_fields():
    metrics = MetricResults([make_metric_value("overall.m")])
    oa = OverallAnalysis(metrics=metrics, score=0.9)
    assert oa.metrics == metrics
    assert oa.score == 0.9


def test_overall_analysis_frozen():
    oa = OverallAnalysis(metrics=MetricResults([]), score=1.0)
    try:
        oa.score = 0.0  # type: ignore[misc]
        assert False, "Should have raised FrozenInstanceError"
    except Exception:
        pass


def test_overall_analysis_metric():
    mv = make_metric_value("overall.m")
    oa = OverallAnalysis(metrics=MetricResults([mv]), score=0.5)
    assert oa.metric("overall.m") == mv


def test_overall_analysis_metric_missing_returns_none():
    oa = OverallAnalysis(metrics=MetricResults([]), score=1.0)
    assert oa.metric("nonexistent") is None


# --- AnalysisReport tests ---


def test_analysis_report_fields():
    oa = OverallAnalysis(metrics=MetricResults([]), score=1.0)
    ha = Analysis(subject=make_hunk(), metrics=MetricResults([]), score=0.8)
    fa = Analysis(subject=make_file(), metrics=MetricResults([]), score=0.9)
    report = AnalysisReport(overall=oa, files=[fa], moves=[], hunks=[ha])
    assert report.overall == oa
    assert report.files == [fa]
    assert report.hunks == [ha]


def test_analysis_report_empty_files_and_hunks():
    oa = OverallAnalysis(metrics=MetricResults([]), score=1.0)
    report = AnalysisReport(overall=oa, files=[], moves=[], hunks=[])
    assert report.files == []
    assert report.hunks == []


def test_analysis_report_frozen():
    oa = OverallAnalysis(metrics=MetricResults([]), score=1.0)
    report = AnalysisReport(overall=oa, files=[], moves=[], hunks=[])
    try:
        report.files = []  # type: ignore[misc]
        assert False, "Should have raised FrozenInstanceError"
    except Exception:
        pass
