from reviewability.config.models import ReviewabilityConfig
from reviewability.domain.report import MetricResults, MetricValue, MetricValueType
from reviewability.rules.definitions import hunk_rules, overall_rules
from reviewability.rules.engine import RuleEngine, Severity


def make_mr(**kwargs: int) -> MetricResults:
    return MetricResults(
        [MetricValue(name, value, MetricValueType.INTEGER) for name, value in kwargs.items()]
    )


config = ReviewabilityConfig(
    max_hunk_lines=50,
    max_diff_lines=500,
    max_problematic_hunks=3,
    max_problematic_files=2,
)


# --- hunk_rules ---


def test_hunk_rules_returns_list():
    rules = hunk_rules(config)
    assert isinstance(rules, list)
    assert len(rules) >= 1


def test_hunk_rule_passes_when_below_limit():
    engine = RuleEngine(hunk_rules(config))
    mr = make_mr(**{"hunk.lines_changed": 30})
    violations = engine.evaluate(mr)
    assert violations == []


def test_hunk_rule_passes_when_at_limit():
    engine = RuleEngine(hunk_rules(config))
    mr = make_mr(**{"hunk.lines_changed": 50})
    violations = engine.evaluate(mr)
    assert violations == []


def test_hunk_rule_fails_when_above_limit():
    engine = RuleEngine(hunk_rules(config))
    mr = make_mr(**{"hunk.lines_changed": 51})
    violations = engine.evaluate(mr)
    assert len(violations) == 1
    assert violations[0].rule.severity == Severity.WARNING
    assert "51" in violations[0].message
    assert "50" in violations[0].message


def test_hunk_rule_fails_when_well_above_limit():
    engine = RuleEngine(hunk_rules(config))
    mr = make_mr(**{"hunk.lines_changed": 200})
    violations = engine.evaluate(mr)
    assert len(violations) == 1


def test_hunk_rule_passes_when_metric_missing():
    engine = RuleEngine(hunk_rules(config))
    mr = MetricResults([])
    violations = engine.evaluate(mr)
    assert violations == []


def test_hunk_rule_uses_config_limit():
    custom = ReviewabilityConfig(max_hunk_lines=10)
    engine = RuleEngine(hunk_rules(custom))
    mr = make_mr(**{"hunk.lines_changed": 11})
    violations = engine.evaluate(mr)
    assert len(violations) == 1
    assert "10" in violations[0].message


# --- overall_rules ---


def test_overall_rules_returns_list():
    rules = overall_rules(config)
    assert isinstance(rules, list)
    assert len(rules) >= 1


def test_overall_lines_changed_passes_when_at_limit():
    engine = RuleEngine(overall_rules(config))
    mr = make_mr(**{"overall.lines_changed": 500})
    violations = engine.evaluate(mr)
    # Only lines_changed rule can fire; at 500 == limit it should NOT fire
    assert all(
        "lines changed" not in v.message.lower() or v.message.find("500") == -1 for v in violations
    )


def test_overall_lines_changed_fails_when_above_limit():
    engine = RuleEngine(overall_rules(config))
    mr = MetricResults(
        [
            MetricValue("overall.lines_changed", 501, MetricValueType.INTEGER),
        ]
    )
    violations = engine.evaluate(mr)
    lines_violations = [v for v in violations if "lines changed" in v.message.lower()]
    assert len(lines_violations) == 1
    assert lines_violations[0].rule.severity == Severity.ERROR
    assert "501" in lines_violations[0].message


def test_overall_lines_changed_passes_when_below_limit():
    engine = RuleEngine(overall_rules(config))
    mr = MetricResults(
        [
            MetricValue("overall.lines_changed", 100, MetricValueType.INTEGER),
        ]
    )
    violations = engine.evaluate(mr)
    lines_violations = [v for v in violations if "lines changed" in v.message.lower()]
    assert lines_violations == []


def test_overall_problematic_hunks_fails_when_above_limit():
    engine = RuleEngine(overall_rules(config))
    mr = MetricResults(
        [
            MetricValue("overall.problematic_hunk_count", 4, MetricValueType.INTEGER),
        ]
    )
    violations = engine.evaluate(mr)
    hunk_violations = [v for v in violations if "problematic hunks" in v.message.lower()]
    assert len(hunk_violations) == 1
    assert hunk_violations[0].rule.severity == Severity.WARNING
    assert "4" in hunk_violations[0].message


def test_overall_problematic_hunks_passes_when_at_limit():
    engine = RuleEngine(overall_rules(config))
    mr = MetricResults(
        [
            MetricValue("overall.problematic_hunk_count", 3, MetricValueType.INTEGER),
        ]
    )
    violations = engine.evaluate(mr)
    hunk_violations = [v for v in violations if "problematic hunks" in v.message.lower()]
    assert hunk_violations == []


def test_overall_problematic_files_fails_when_above_limit():
    engine = RuleEngine(overall_rules(config))
    mr = MetricResults(
        [
            MetricValue("overall.problematic_file_count", 3, MetricValueType.INTEGER),
        ]
    )
    violations = engine.evaluate(mr)
    file_violations = [v for v in violations if "problematic files" in v.message.lower()]
    assert len(file_violations) == 1
    assert file_violations[0].rule.severity == Severity.WARNING


def test_overall_problematic_files_passes_when_at_limit():
    engine = RuleEngine(overall_rules(config))
    mr = MetricResults(
        [
            MetricValue("overall.problematic_file_count", 2, MetricValueType.INTEGER),
        ]
    )
    violations = engine.evaluate(mr)
    file_violations = [v for v in violations if "problematic files" in v.message.lower()]
    assert file_violations == []


def test_overall_rules_no_violations_when_metrics_missing():
    engine = RuleEngine(overall_rules(config))
    mr = MetricResults([])
    violations = engine.evaluate(mr)
    assert violations == []


def test_overall_rules_multiple_violations():
    engine = RuleEngine(overall_rules(config))
    mr = MetricResults(
        [
            MetricValue("overall.lines_changed", 600, MetricValueType.INTEGER),
            MetricValue("overall.problematic_hunk_count", 5, MetricValueType.INTEGER),
            MetricValue("overall.problematic_file_count", 4, MetricValueType.INTEGER),
        ]
    )
    violations = engine.evaluate(mr)
    assert len(violations) == 3
