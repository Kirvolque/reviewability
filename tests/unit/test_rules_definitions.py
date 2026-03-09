from reviewability.config.models import ReviewabilityConfig
from reviewability.domain.report import MetricResults, MetricValue, MetricValueType, Statistics
from reviewability.rules.definitions import hunk_rules, overall_rules
from reviewability.rules.engine import RuleEngine, Severity


def make_stats(score: float = 1.0, **kwargs: int) -> Statistics:
    metrics = MetricResults(
        [MetricValue(name, value, MetricValueType.INTEGER) for name, value in kwargs.items()]
    )
    return Statistics(metrics, score)


config = ReviewabilityConfig(
    max_hunk_lines=50,
    max_diff_lines=500,
    max_problematic_hunks=3,
    max_problematic_files=2,
    min_overall_score=0.5,
)


# --- hunk_rules ---


def test_hunk_rules_returns_list():
    rules = hunk_rules(config)
    assert isinstance(rules, list)
    assert len(rules) >= 1


def test_hunk_rule_passes_when_below_limit():
    engine = RuleEngine(hunk_rules(config))
    violations = engine.evaluate(make_stats(**{"hunk.lines_changed": 30}))
    assert violations == []


def test_hunk_rule_passes_when_at_limit():
    engine = RuleEngine(hunk_rules(config))
    violations = engine.evaluate(make_stats(**{"hunk.lines_changed": 50}))
    assert violations == []


def test_hunk_rule_fails_when_above_limit():
    engine = RuleEngine(hunk_rules(config))
    violations = engine.evaluate(make_stats(**{"hunk.lines_changed": 51}))
    assert len(violations) == 1
    assert violations[0].rule.severity == Severity.WARNING
    assert "51" in violations[0].message
    assert "50" in violations[0].message


def test_hunk_rule_fails_when_well_above_limit():
    engine = RuleEngine(hunk_rules(config))
    violations = engine.evaluate(make_stats(**{"hunk.lines_changed": 200}))
    assert len(violations) == 1


def test_hunk_rule_passes_when_metric_missing():
    engine = RuleEngine(hunk_rules(config))
    violations = engine.evaluate(make_stats())
    assert violations == []


def test_hunk_rule_uses_config_limit():
    custom = ReviewabilityConfig(max_hunk_lines=10)
    engine = RuleEngine(hunk_rules(custom))
    violations = engine.evaluate(make_stats(**{"hunk.lines_changed": 11}))
    assert len(violations) == 1
    assert "10" in violations[0].message


# --- overall_rules: score ---


def test_overall_score_passes_when_above_threshold():
    engine = RuleEngine(overall_rules(config))
    violations = engine.evaluate(make_stats(score=0.8))
    score_violations = [v for v in violations if "score" in v.message.lower()]
    assert score_violations == []


def test_overall_score_passes_when_at_threshold():
    engine = RuleEngine(overall_rules(config))
    violations = engine.evaluate(make_stats(score=0.5))
    score_violations = [v for v in violations if "score" in v.message.lower()]
    assert score_violations == []


def test_overall_score_fails_when_below_threshold():
    engine = RuleEngine(overall_rules(config))
    violations = engine.evaluate(make_stats(score=0.3))
    score_violations = [v for v in violations if "score" in v.message.lower()]
    assert len(score_violations) == 1
    assert score_violations[0].rule.severity == Severity.ERROR
    assert "0.3" in score_violations[0].message


# --- overall_rules: lines changed ---


def test_overall_lines_changed_passes_when_at_limit():
    engine = RuleEngine(overall_rules(config))
    violations = engine.evaluate(make_stats(**{"overall.lines_changed": 500}))
    lines_violations = [v for v in violations if "lines changed" in v.message.lower()]
    assert lines_violations == []


def test_overall_lines_changed_fails_when_above_limit():
    engine = RuleEngine(overall_rules(config))
    violations = engine.evaluate(make_stats(**{"overall.lines_changed": 501}))
    lines_violations = [v for v in violations if "lines changed" in v.message.lower()]
    assert len(lines_violations) == 1
    assert lines_violations[0].rule.severity == Severity.ERROR
    assert "501" in lines_violations[0].message


def test_overall_lines_changed_passes_when_below_limit():
    engine = RuleEngine(overall_rules(config))
    violations = engine.evaluate(make_stats(**{"overall.lines_changed": 100}))
    lines_violations = [v for v in violations if "lines changed" in v.message.lower()]
    assert lines_violations == []


# --- overall_rules: problematic counts ---


def test_overall_problematic_hunks_fails_when_above_limit():
    engine = RuleEngine(overall_rules(config))
    violations = engine.evaluate(make_stats(**{"overall.problematic_hunk_count": 4}))
    hunk_violations = [v for v in violations if "problematic hunks" in v.message.lower()]
    assert len(hunk_violations) == 1
    assert hunk_violations[0].rule.severity == Severity.WARNING
    assert "4" in hunk_violations[0].message


def test_overall_problematic_hunks_passes_when_at_limit():
    engine = RuleEngine(overall_rules(config))
    violations = engine.evaluate(make_stats(**{"overall.problematic_hunk_count": 3}))
    hunk_violations = [v for v in violations if "problematic hunks" in v.message.lower()]
    assert hunk_violations == []


def test_overall_problematic_files_fails_when_above_limit():
    engine = RuleEngine(overall_rules(config))
    violations = engine.evaluate(make_stats(**{"overall.problematic_file_count": 3}))
    file_violations = [v for v in violations if "problematic files" in v.message.lower()]
    assert len(file_violations) == 1
    assert file_violations[0].rule.severity == Severity.WARNING


def test_overall_problematic_files_passes_when_at_limit():
    engine = RuleEngine(overall_rules(config))
    violations = engine.evaluate(make_stats(**{"overall.problematic_file_count": 2}))
    file_violations = [v for v in violations if "problematic files" in v.message.lower()]
    assert file_violations == []


def test_overall_rules_no_violations_when_metrics_missing():
    engine = RuleEngine(overall_rules(config))
    violations = engine.evaluate(make_stats(score=1.0))
    assert violations == []


def test_overall_rules_multiple_violations():
    engine = RuleEngine(overall_rules(config))
    violations = engine.evaluate(
        make_stats(
            score=0.3,
            **{
                "overall.lines_changed": 600,
                "overall.problematic_hunk_count": 5,
                "overall.problematic_file_count": 4,
            },
        )
    )
    assert len(violations) == 4  # score + lines + hunks + files
