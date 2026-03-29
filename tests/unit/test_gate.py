from reviewability.config.models import ReviewabilityConfig
from reviewability.domain.metric import MetricResults, MetricValue, MetricValueType
from reviewability.domain.models import ChangeType, Hunk, Move, MoveType
from reviewability.domain.report import Analysis, AnalysisReport, OverallAnalysis
from reviewability.gate import QualityGate
from reviewability.rules.engine import Rule, RuleViolation, Severity


def make_config() -> ReviewabilityConfig:
    return ReviewabilityConfig(
        hunk_score_threshold=0.5,
        file_score_threshold=0.5,
        max_diff_lines=500,
        max_hunk_lines=50,
        max_move_lines=100,
        move_similarity_penalty=1.0,
    )


def make_report(overall_score: float = 1.0) -> AnalysisReport:
    oa = OverallAnalysis(metrics=MetricResults([]), score=overall_score)
    return AnalysisReport(overall=oa, files=[], moves=[], hunks=[])


def make_violation(severity: Severity, message: str = "msg") -> RuleViolation:
    rule = Rule(severity=severity, check=lambda s: message)
    return RuleViolation(rule=rule, message=message)


def make_hunk_analysis(score: float, remediation: str | None = None) -> Analysis:
    mv = MetricValue(
        name="hunk.test",
        value=0.8,
        value_type=MetricValueType.RATIO,
        remediation=remediation,
    )
    hunk = Hunk(file_path="src/foo.py")
    return Analysis(subject=hunk, metrics=MetricResults([mv]), score=score)


def make_move_analysis(score: float, remediation: str | None = None) -> Analysis:
    mv = MetricValue(
        name="move.test",
        value=0.5,
        value_type=MetricValueType.RATIO,
        remediation=remediation,
    )
    hunk = Hunk(file_path="src/foo.py", change_order=(ChangeType.ADDED,))
    move = Move(move_id=1, hunks=(hunk,), similarity=0.95, move_type=MoveType.PURE, length=10)
    return Analysis(subject=move, metrics=MetricResults([mv]), score=score)


gate = QualityGate()


# --- QualityGate tests ---


def test_gate_passes_with_no_violations():
    result = gate.evaluate(make_report(), [], make_config())
    assert result.passed is True


def test_gate_passes_with_only_warning_violations():
    violations = [make_violation(Severity.WARNING)]
    result = gate.evaluate(make_report(), violations, make_config())
    assert result.passed is True


def test_gate_fails_with_error_violation():
    violations = [make_violation(Severity.ERROR)]
    result = gate.evaluate(make_report(), violations, make_config())
    assert result.passed is False


def test_gate_fails_with_error_and_warning():
    violations = [make_violation(Severity.WARNING), make_violation(Severity.ERROR)]
    result = gate.evaluate(make_report(), violations, make_config())
    assert result.passed is False


def test_gate_recommendations_empty_when_passed():
    result = gate.evaluate(make_report(), [], make_config())
    assert result.recommendations == []


def test_gate_recommendations_empty_when_no_metric_results():
    # Gate produces no recommendations when report has no remediations
    result = gate.evaluate(make_report(), [make_violation(Severity.ERROR)], make_config())
    assert result.recommendations == []


def test_gate_recommendations_from_low_scoring_hunk():
    hunk_analysis = make_hunk_analysis(score=0.2, remediation="Fix this hunk.")
    report = AnalysisReport(
        overall=OverallAnalysis(metrics=MetricResults([]), score=0.5),
        files=[],
        moves=[],
        hunks=[hunk_analysis],
    )
    result = gate.evaluate(report, [make_violation(Severity.ERROR)], make_config())
    assert len(result.recommendations) == 1
    assert result.recommendations[0].location == "src/foo.py"
    assert result.recommendations[0].metric == "hunk.test"
    assert result.recommendations[0].remediation == "Fix this hunk."


def test_gate_no_recommendations_from_passing_hunk():
    hunk_analysis = make_hunk_analysis(score=0.8, remediation="Fix this hunk.")
    report = AnalysisReport(
        overall=OverallAnalysis(metrics=MetricResults([]), score=0.5),
        files=[],
        moves=[],
        hunks=[hunk_analysis],
    )
    result = gate.evaluate(report, [make_violation(Severity.ERROR)], make_config())
    assert result.recommendations == []


def test_gate_recommendations_from_low_scoring_move():
    move_analysis = make_move_analysis(score=0.1, remediation="Simplify this move.")
    report = AnalysisReport(
        overall=OverallAnalysis(metrics=MetricResults([]), score=0.5),
        files=[],
        moves=[move_analysis],
        hunks=[],
    )
    result = gate.evaluate(report, [make_violation(Severity.ERROR)], make_config())
    assert len(result.recommendations) == 1
    assert result.recommendations[0].location == "move:1"
    assert result.recommendations[0].remediation == "Simplify this move."


def test_gate_recommendations_from_overall_metrics():
    mv = MetricValue(
        name="overall.scatter_factor",
        value=0.9,
        value_type=MetricValueType.RATIO,
        remediation="Split into focused PRs.",
    )
    report = AnalysisReport(
        overall=OverallAnalysis(metrics=MetricResults([mv]), score=0.5),
        files=[],
        moves=[],
        hunks=[],
    )
    result = gate.evaluate(report, [make_violation(Severity.ERROR)], make_config())
    assert len(result.recommendations) == 1
    assert result.recommendations[0].location == "overall"
    assert result.recommendations[0].metric == "overall.scatter_factor"
