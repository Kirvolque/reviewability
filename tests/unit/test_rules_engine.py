from reviewability.domain.metric import MetricResults, MetricValue, MetricValueType
from reviewability.domain.report import OverallAnalysis
from reviewability.rules.engine import Rule, RuleEngine, RuleViolation, Severity


def make_context(metrics: list[MetricValue] | None = None, score: float = 1.0) -> OverallAnalysis:
    return OverallAnalysis(MetricResults(metrics or []), score)


def passing_rule() -> Rule:
    return Rule(severity=Severity.WARNING, check=lambda s: None)


def failing_rule(msg: str = "failure") -> Rule:
    return Rule(severity=Severity.ERROR, check=lambda s: msg)


# --- Rule tests ---


def test_rule_fields():
    def check(s: OverallAnalysis) -> str | None:
        return None

    rule = Rule(severity=Severity.WARNING, check=check)
    assert rule.severity == Severity.WARNING
    assert rule.check is check


def test_rule_frozen():
    rule = passing_rule()
    try:
        rule.severity = Severity.ERROR  # type: ignore[misc]
        assert False, "Should have raised FrozenInstanceError"
    except Exception:
        pass


def test_rule_severity_warning():
    rule = Rule(severity=Severity.WARNING, check=lambda s: None)
    assert rule.severity == Severity.WARNING


def test_rule_severity_error():
    rule = Rule(severity=Severity.ERROR, check=lambda s: None)
    assert rule.severity == Severity.ERROR


# --- RuleViolation tests ---


def test_rule_violation_fields():
    rule = failing_rule("oops")
    violation = RuleViolation(rule=rule, message="oops")
    assert violation.rule == rule
    assert violation.message == "oops"


def test_rule_violation_str_warning():
    rule = Rule(severity=Severity.WARNING, check=lambda s: "too big")
    violation = RuleViolation(rule=rule, message="too big")
    assert str(violation) == "[WARNING] too big"


def test_rule_violation_str_error():
    rule = Rule(severity=Severity.ERROR, check=lambda s: "way too big")
    violation = RuleViolation(rule=rule, message="way too big")
    assert str(violation) == "[ERROR] way too big"


def test_rule_violation_frozen():
    rule = failing_rule()
    violation = RuleViolation(rule=rule, message="msg")
    try:
        violation.message = "other"  # type: ignore[misc]
        assert False, "Should have raised FrozenInstanceError"
    except Exception:
        pass


# --- RuleEngine tests ---


def test_rule_engine_no_rules():
    engine = RuleEngine([])
    violations = engine.evaluate(make_context())
    assert violations == []


def test_rule_engine_all_pass():
    engine = RuleEngine([passing_rule(), passing_rule()])
    violations = engine.evaluate(make_context())
    assert violations == []


def test_rule_engine_one_failing():
    rule = failing_rule("bad thing")
    engine = RuleEngine([rule])
    violations = engine.evaluate(make_context())
    assert len(violations) == 1
    assert violations[0].rule == rule
    assert violations[0].message == "bad thing"


def test_rule_engine_mixed_rules():
    r_pass = passing_rule()
    r_fail1 = failing_rule("fail1")
    r_fail2 = failing_rule("fail2")
    engine = RuleEngine([r_pass, r_fail1, r_pass, r_fail2])
    violations = engine.evaluate(make_context())
    assert len(violations) == 2
    assert violations[0].message == "fail1"
    assert violations[1].message == "fail2"


def test_rule_engine_rule_receives_context():
    received = []

    def capture_check(context: OverallAnalysis) -> str | None:
        received.append(context)
        return None

    rule = Rule(severity=Severity.WARNING, check=capture_check)
    engine = RuleEngine([rule])
    context = make_context([MetricValue("x", 5, MetricValueType.INTEGER)])
    engine.evaluate(context)
    assert len(received) == 1
    assert received[0] is context


def test_rule_engine_rule_uses_metric_value():
    mv = MetricValue("hunk.lines_changed", 100, MetricValueType.INTEGER)
    context = make_context([mv])

    def check_too_many(s: OverallAnalysis) -> str | None:
        v = s.get("hunk.lines_changed")
        if v is not None and v.value > 50:
            return f"Too many: {v.value}"
        return None

    rule = Rule(severity=Severity.WARNING, check=check_too_many)
    engine = RuleEngine([rule])
    violations = engine.evaluate(context)
    assert len(violations) == 1
    assert "Too many: 100" in violations[0].message


def test_rule_engine_rule_uses_score():
    context = make_context(score=0.3)

    def check_low_score(s: OverallAnalysis) -> str | None:
        if s.score < 0.5:
            return f"Score too low: {s.score}"
        return None

    rule = Rule(severity=Severity.ERROR, check=check_low_score)
    violations = RuleEngine([rule]).evaluate(context)
    assert len(violations) == 1
    assert "0.3" in violations[0].message


def test_rule_engine_returns_list_of_violations_not_nones():
    rules = [passing_rule(), failing_rule("x"), passing_rule()]
    engine = RuleEngine(rules)
    violations = engine.evaluate(make_context())
    assert all(isinstance(v, RuleViolation) for v in violations)


# --- Severity enum ---


def test_severity_values():
    assert Severity.WARNING.value == "warning"
    assert Severity.ERROR.value == "error"
