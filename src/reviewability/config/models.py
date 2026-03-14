from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewabilityConfig:
    """Configuration for reviewability analysis thresholds and limits.

    Score thresholds are in the range [0.0, 1.0].
    A hunk or file is considered problematic if its reviewability score falls below
    the corresponding threshold.
    """

    hunk_score_threshold: float = 0.5
    """Hunks with a reviewability score below this are considered problematic."""

    file_score_threshold: float = 0.5
    """Files with a reviewability score below this are considered problematic."""

    max_diff_lines: int = 500
    """Maximum total lines changed across the diff."""

    max_problematic_hunks: int = 3
    """Maximum number of problematic hunks allowed in a diff."""

    max_problematic_files: int = 2
    """Maximum number of problematic files allowed in a diff."""

    max_hunk_lines: int = 50
    """Maximum lines changed in a single hunk."""

    min_overall_score: float = 0.5
    """Overall diff score below this causes the gate to fail. Range [0.0, 1.0]."""

    movement_hunk_min_lines: int = 8
    """Minimum content lines in a hunk to be considered for movement detection."""

    movement_file_min_lines: int = 15
    """Minimum content lines in a file to be considered for movement detection."""

    movement_similarity_threshold: float = 0.95
    """Fraction of lines that must match for two blocks to be classified as a movement."""
