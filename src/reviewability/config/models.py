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
