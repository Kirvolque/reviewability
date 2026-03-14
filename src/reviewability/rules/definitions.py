from reviewability.config.models import ReviewabilityConfig
from reviewability.rules.engine import Rule, Severity


def hunk_rules(config: ReviewabilityConfig) -> list[Rule]:
    """Return the default set of hunk-level rules driven by the given config."""
    rules: list[Rule] = [
        Rule(
            severity=Severity.WARNING,
            check=lambda s: (
                f"Hunk has {v.value} lines, exceeds limit of {config.max_hunk_lines}"
                if (v := s.metric("hunk.lines_changed")) is not None
                and v.value > config.max_hunk_lines
                else None
            ),
        ),
    ]
    return rules


def file_rules(config: ReviewabilityConfig) -> list[Rule]:
    """Return the default set of file-level rules driven by the given config."""
    rules: list[Rule] = []
    if config.max_file_hunk_count is not None:
        rules.append(
            Rule(
                severity=Severity.WARNING,
                check=lambda s: (
                    f"File has {v.value} hunks, exceeds limit of {config.max_file_hunk_count}"
                    if (v := s.metric("file.hunk_count")) is not None
                    and v.value > config.max_file_hunk_count
                    else None
                ),
            )
        )
    return rules


def overall_rules(config: ReviewabilityConfig) -> list[Rule]:
    """Return the default set of overall-level rules driven by the given config."""
    rules: list[Rule] = [
        Rule(
            severity=Severity.ERROR,
            check=lambda s: (
                f"Diff has {v.value} lines changed, exceeds limit of {config.max_diff_lines}"
                if (v := s.metric("overall.lines_changed")) is not None
                and v.value > config.max_diff_lines
                else None
            ),
        ),
    ]
    if config.min_overall_score is not None:
        rules.append(
            Rule(
                severity=Severity.ERROR,
                check=lambda s: (
                    f"Overall score {s.score:.2f} is below the minimum of {config.min_overall_score}"
                    if s.score < config.min_overall_score
                    else None
                ),
            )
        )
    if config.max_problematic_hunks is not None:
        rules.append(
            Rule(
                severity=Severity.WARNING,
                check=lambda s: (
                    f"Diff has {v.value} problematic hunks, exceeds limit of {config.max_problematic_hunks}"  # noqa: E501
                    if (v := s.metric("overall.problematic_hunk_count")) is not None
                    and v.value > config.max_problematic_hunks
                    else None
                ),
            )
        )
    if config.max_problematic_files is not None:
        rules.append(
            Rule(
                severity=Severity.WARNING,
                check=lambda s: (
                    f"Diff has {v.value} problematic files, exceeds limit of {config.max_problematic_files}"  # noqa: E501
                    if (v := s.metric("overall.problematic_file_count")) is not None
                    and v.value > config.max_problematic_files
                    else None
                ),
            )
        )
    if config.max_files_changed is not None:
        rules.append(
            Rule(
                severity=Severity.ERROR,
                check=lambda s: (
                    f"Diff touches {v.value} files, exceeds limit of {config.max_files_changed}"
                    if (v := s.metric("overall.files_changed")) is not None
                    and v.value > config.max_files_changed
                    else None
                ),
            )
        )
    if config.max_added_lines is not None:
        rules.append(
            Rule(
                severity=Severity.ERROR,
                check=lambda s: (
                    f"Diff has {v.value} added lines, exceeds limit of {config.max_added_lines}"
                    if (v := s.metric("overall.added_lines")) is not None
                    and v.value > config.max_added_lines
                    else None
                ),
            )
        )
    return rules
