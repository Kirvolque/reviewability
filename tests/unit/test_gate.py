from reviewability.domain.metric import MetricResults
from reviewability.domain.report import AnalysisReport, OverallAnalysis
from reviewability.gate import QualityGate
from reviewability.rules.engine import Rule, RuleViolation, Severity


def make_report(overall_score: float = 1.0) -> AnalysisReport:
    oa = OverallAnalysis(metrics=MetricResults([]), score=overall_score)
    return AnalysisReport(overall=oa, files=[], hunks=[])


def make_violation(severity: Severity, message: str = "msg") -> RuleViolation:
    rule = Rule(severity=severity, check=lambda s: message)
    return RuleViolation(rule=rule, message=message)


gate = QualityGate()


# --- QualityGate tests ---


def test_gate_passes_with_no_violations():
    result = gate.evaluate(make_report(), [])
    assert result.passed is True


def test_gate_passes_with_only_warning_violations():
    violations = [make_violation(Severity.WARNING)]
    result = gate.evaluate(make_report(), violations)
    assert result.passed is True


def test_gate_fails_with_error_violation():
    violations = [make_violation(Severity.ERROR)]
    result = gate.evaluate(make_report(), violations)
    assert result.passed is False


def test_gate_fails_with_error_and_warning():
    violations = [make_violation(Severity.WARNING), make_violation(Severity.ERROR)]
    result = gate.evaluate(make_report(), violations)
    assert result.passed is False


def test_gate_recommendations_empty_when_passed():
    result = gate.evaluate(make_report(), [])
    assert result.recommendations == []


def test_gate_recommendations_empty_when_no_metric_results():
    # Gate produces recommendations from metric_results causes; empty report = empty recs
    result = gate.evaluate(make_report(), [make_violation(Severity.ERROR)])
    assert result.recommendations == []
