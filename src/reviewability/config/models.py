from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewabilityConfig:
    """Configuration for reviewability analysis thresholds and limits.

    Score thresholds are in the range [0.0, 1.0].
    A hunk or file is considered problematic if its reviewability score falls below
    the corresponding threshold.

    Rule thresholds default to ``None``, meaning the corresponding rule is disabled.
    Set a value to enable the rule.
    """

    hunk_score_threshold: float = 0.5
    """Hunks with a reviewability score below this are considered problematic."""

    file_score_threshold: float = 0.5
    """Files with a reviewability score below this are considered problematic."""

    max_diff_lines: int = 500
    """Maximum total lines changed across the diff (used for score normalisation)."""

    max_hunk_lines: int = 50
    """Maximum lines changed in a single hunk (used for score normalisation)."""

    min_overall_score: float | None = None
    """Overall diff score below this causes the gate to fail. Range [0.0, 1.0].
    Disabled by default — set a value to enable."""

    max_problematic_hunks: int | None = None
    """Maximum number of problematic hunks allowed. Disabled by default."""

    max_problematic_files: int | None = None
    """Maximum number of problematic files allowed. Disabled by default."""

    max_file_hunk_count: int | None = None
    """Maximum number of hunks in a single file. Disabled by default."""

    max_files_changed: int | None = None
    """Maximum number of files changed in the diff. Disabled by default."""

    max_added_lines: int | None = None
    """Maximum total added lines across the diff. Disabled by default."""

    movement_hunk_min_lines: int = 8
    """Minimum content lines in a hunk to be considered for movement detection."""

    movement_file_min_lines: int = 15
    """Minimum content lines in a file to be considered for movement detection."""

    movement_similarity_threshold: float = 0.95
    """Fraction of lines that must match for two blocks to be classified as a movement."""
