from reviewability.config.models import ReviewabilityConfig
from reviewability.metrics.hunk.lines_changed import HunkLinesChanged
from reviewability.metrics.overall.added_lines import OverallAddedLines
from reviewability.metrics.overall.files_changed import OverallFilesChanged
from reviewability.metrics.overall.lines_changed import OverallLinesChanged
from reviewability.metrics.overall.problematic_file_count import OverallProblematicFileCount
from reviewability.metrics.overall.problematic_hunk_count import OverallProblematicHunkCount
from reviewability.metrics.overall.problematic_move_count import OverallProblematicMoveCount
from reviewability.rules.engine import Rule, Severity


def _compact(rules: list[Rule | None]) -> list[Rule]:
    return [r for r in rules if r is not None]


def hunk_rules(config: ReviewabilityConfig) -> list[Rule]:
    """Return the default set of hunk-level rules driven by the given config."""
    return [
        Rule(
            severity=Severity.WARNING,
            check=lambda s: (
                f"Hunk has {v.value} lines, exceeds limit of {config.max_hunk_lines}"
                if (v := s.metric(HunkLinesChanged.name)) is not None
                and v.value > config.max_hunk_lines
                else None
            ),
        ),
    ]


def overall_rules(config: ReviewabilityConfig) -> list[Rule]:
    """Return the default set of overall-level rules driven by the given config."""
    return _compact(
        [
            Rule(
                severity=Severity.ERROR,
                check=lambda s: (
                    f"Diff has {v.value} lines changed, exceeds limit of {config.max_diff_lines}"
                    if (v := s.metric(OverallLinesChanged.name)) is not None
                    and v.value > config.max_diff_lines
                    else None
                ),
            ),
            Rule(
                severity=Severity.ERROR,
                check=lambda s: (
                    f"Overall score {s.score:.2f} is below the minimum"
                    f" of {config.min_overall_score}"
                    if s.score < config.min_overall_score
                    else None
                ),
            )
            if config.min_overall_score is not None
            else None,
            Rule(
                severity=Severity.WARNING,
                check=lambda s: (
                    f"Diff has {v.value} problematic hunks,"
                    f" exceeds limit of {config.max_problematic_hunks}"
                    if (v := s.metric(OverallProblematicHunkCount.name)) is not None
                    and v.value > config.max_problematic_hunks
                    else None
                ),
            )
            if config.max_problematic_hunks is not None
            else None,
            Rule(
                severity=Severity.WARNING,
                check=lambda s: (
                    f"Diff has {v.value} problematic moves,"
                    f" exceeds limit of {config.max_problematic_moves}"
                    if (v := s.metric(OverallProblematicMoveCount.name)) is not None
                    and v.value > config.max_problematic_moves
                    else None
                ),
            )
            if config.max_problematic_moves is not None
            else None,
            Rule(
                severity=Severity.WARNING,
                check=lambda s: (
                    f"Diff has {v.value} problematic files,"
                    f" exceeds limit of {config.max_problematic_files}"
                    if (v := s.metric(OverallProblematicFileCount.name)) is not None
                    and v.value > config.max_problematic_files
                    else None
                ),
            )
            if config.max_problematic_files is not None
            else None,
            Rule(
                severity=Severity.ERROR,
                check=lambda s: (
                    f"Diff touches {v.value} files, exceeds limit of {config.max_files_changed}"
                    if (v := s.metric(OverallFilesChanged.name)) is not None
                    and v.value > config.max_files_changed
                    else None
                ),
            )
            if config.max_files_changed is not None
            else None,
            Rule(
                severity=Severity.ERROR,
                check=lambda s: (
                    f"Diff has {v.value} added lines, exceeds limit of {config.max_added_lines}"
                    if (v := s.metric(OverallAddedLines.name)) is not None
                    and v.value > config.max_added_lines
                    else None
                ),
            )
            if config.max_added_lines is not None
            else None,
        ]
    )
