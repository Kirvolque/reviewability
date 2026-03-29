from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewabilityConfig:
    """Parsed reviewability configuration.

    All numeric values come from the config file (defaults.toml or user override).
    This is a pure data structure with no hardcoded defaults.
    Optional fields default to None (disabled).
    """

    hunk_score_threshold: float
    """Hunks with a reviewability score below this are considered problematic."""

    file_score_threshold: float
    """Files with a reviewability score below this are considered problematic."""

    max_diff_lines: int
    """Maximum total lines changed across the diff (used for score normalisation)."""

    max_hunk_lines: int
    """Maximum lines changed in a single hunk (used for score normalisation)."""

    max_move_lines: int
    """Maximum meaningful lines in the largest hunk of a move (for move score normalisation)."""

    move_similarity_penalty: float
    """Multiplier controlling how much low similarity raises the per-line penalty for moves."""

    min_overall_score: float | None = None
    """Overall diff score below this causes the gate to fail. Range [0.0, 1.0]."""

    max_problematic_hunks: int | None = None
    """Maximum number of problematic hunks allowed."""

    max_problematic_moves: int | None = None
    """Maximum number of problematic moves allowed."""

    max_problematic_files: int | None = None
    """Maximum number of problematic files allowed."""

    max_files_changed: int | None = None
    """Maximum number of files changed in the diff."""

    max_added_lines: int | None = None
    """Maximum total added lines across the diff."""

    import_prefixes: dict[str, list[str]] | None = None
    """Per-extension import/package prefixes to strip from lines before analysis.
    Use ``"*"`` as the key for a fallback applied to unknown extensions.
    If None, built-in defaults are used."""
