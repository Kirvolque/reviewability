from reviewability.config.models import ReviewabilityConfig
from reviewability.domain.report import (
    AnalysisReport,
    MetricResults,
    OverallAnalysis,
)
from reviewability.gate import GateResult, QualityGate
from reviewability.rules.engine import Rule, RuleViolation, Severity


def make_report(overall_score: float) -> AnalysisReport:
    oa = OverallAnalysis(metrics=MetricResults([]), score=overall_score)
    return AnalysisReport(overall=oa, files=[], hunks=[])


def make_violation(severity: Severity, message: str = "msg") -> RuleViolation:
    rule = Rule(severity=severity, check=lambda m: message)
    return RuleViolation(rule=rule, message=message)


config = ReviewabilityConfig(min_overall_score=0.5)


# --- GateResult tests ---


def test_gate_result_fields():
    result = GateResult(passed=True, recommendations=["hint"])
    assert result.passed is True
    assert result.recommendations == ["hint"]


def test_gate_result_frozen():
    result = GateResult(passed=True, recommendations=[])
    try:
        result.passed = False  # type: ignore[misc]
        assert False, "Should have raised FrozenInstanceError"
    except Exception:
        pass


def test_gate_result_empty_recommendations():
    result = GateResult(passed=False, recommendations=[])
    assert result.recommendations == []


# --- QualityGate tests ---


def test_gate_passes_when_score_above_threshold_no_violations():
    gate = QualityGate(config)
    report = make_report(overall_score=0.8)
    result = gate.evaluate(report, [])
    assert result.passed is True


def test_gate_passes_when_score_exactly_at_threshold():
    gate = QualityGate(config)
    report = make_report(overall_score=0.5)
    result = gate.evaluate(report, [])
    assert result.passed is True


def test_gate_fails_when_score_below_threshold():
    gate = QualityGate(config)
    report = make_report(overall_score=0.4)
    result = gate.evaluate(report, [])
    assert result.passed is False


def test_gate_fails_when_score_zero():
    gate = QualityGate(config)
    report = make_report(overall_score=0.0)
    result = gate.evaluate(report, [])
    assert result.passed is False


def test_gate_passes_with_only_warning_violations():
    gate = QualityGate(config)
    report = make_report(overall_score=0.8)
    violations = [make_violation(Severity.WARNING)]
    result = gate.evaluate(report, violations)
    assert result.passed is True


def test_gate_fails_with_error_violation():
    gate = QualityGate(config)
    report = make_report(overall_score=0.8)
    violations = [make_violation(Severity.ERROR)]
    result = gate.evaluate(report, violations)
    assert result.passed is False


def test_gate_fails_with_error_and_good_score():
    gate = QualityGate(config)
    report = make_report(overall_score=1.0)
    violations = [make_violation(Severity.ERROR)]
    result = gate.evaluate(report, violations)
    assert result.passed is False


def test_gate_fails_when_both_score_low_and_error_violation():
    gate = QualityGate(config)
    report = make_report(overall_score=0.1)
    violations = [make_violation(Severity.ERROR)]
    result = gate.evaluate(report, violations)
    assert result.passed is False


def test_gate_fails_score_low_with_only_warning_violation():
    gate = QualityGate(config)
    report = make_report(overall_score=0.3)
    violations = [make_violation(Severity.WARNING)]
    result = gate.evaluate(report, violations)
    assert result.passed is False


def test_gate_passes_with_multiple_warnings():
    gate = QualityGate(config)
    report = make_report(overall_score=0.9)
    violations = [make_violation(Severity.WARNING), make_violation(Severity.WARNING)]
    result = gate.evaluate(report, violations)
    assert result.passed is True


def test_gate_fails_with_mixed_violations_includes_error():
    gate = QualityGate(config)
    report = make_report(overall_score=0.9)
    violations = [make_violation(Severity.WARNING), make_violation(Severity.ERROR)]
    result = gate.evaluate(report, violations)
    assert result.passed is False


def test_gate_recommendations_always_empty():
    gate = QualityGate(config)
    report = make_report(overall_score=0.0)
    result = gate.evaluate(report, [make_violation(Severity.ERROR)])
    assert result.recommendations == []


def test_gate_uses_config_threshold():
    strict_config = ReviewabilityConfig(min_overall_score=0.9)
    gate = QualityGate(strict_config)
    report = make_report(overall_score=0.8)
    result = gate.evaluate(report, [])
    assert result.passed is False


def test_gate_uses_config_threshold_passes():
    lenient_config = ReviewabilityConfig(min_overall_score=0.1)
    gate = QualityGate(lenient_config)
    report = make_report(overall_score=0.2)
    result = gate.evaluate(report, [])
    assert result.passed is True
