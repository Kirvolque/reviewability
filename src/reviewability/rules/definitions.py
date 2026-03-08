from reviewability.config.models import ReviewabilityConfig
from reviewability.rules.engine import Rule, Severity


def hunk_rules(config: ReviewabilityConfig) -> list[Rule]:
    """Return the default set of hunk-level rules driven by the given config."""
    return [
        Rule(
            severity=Severity.WARNING,
            check=lambda m: (
                f"Hunk has {v.value} lines, exceeds limit of {config.max_hunk_lines}"
                if (v := m.get("hunk.lines_changed")) is not None
                and v.value > config.max_hunk_lines
                else None
            ),
        ),
    ]


def overall_rules(config: ReviewabilityConfig) -> list[Rule]:
    """Return the default set of overall-level rules driven by the given config."""
    return [
        Rule(
            severity=Severity.ERROR,
            check=lambda m: (
                f"Diff has {v.value} lines changed, exceeds limit of {config.max_diff_lines}"
                if (v := m.get("overall.lines_changed")) is not None
                and v.value > config.max_diff_lines
                else None
            ),
        ),
        Rule(
            severity=Severity.WARNING,
            check=lambda m: (
                f"Diff has {v.value} problematic hunks, exceeds limit of {config.max_problematic_hunks}"  # noqa: E501
                if (v := m.get("overall.problematic_hunk_count")) is not None
                and v.value > config.max_problematic_hunks
                else None
            ),
        ),
        Rule(
            severity=Severity.WARNING,
            check=lambda m: (
                f"Diff has {v.value} problematic files, exceeds limit of {config.max_problematic_files}"  # noqa: E501
                if (v := m.get("overall.problematic_file_count")) is not None
                and v.value > config.max_problematic_files
                else None
            ),
        ),
    ]
