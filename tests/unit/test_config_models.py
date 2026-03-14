from reviewability.config.models import ReviewabilityConfig


def test_default_values():
    config = ReviewabilityConfig()
    assert config.hunk_score_threshold == 0.5
    assert config.file_score_threshold == 0.5
    assert config.max_diff_lines == 500
    assert config.max_hunk_lines == 50
    # Optional rule thresholds default to None (disabled)
    assert config.min_overall_score is None
    assert config.max_problematic_hunks is None
    assert config.max_problematic_files is None
    assert config.max_file_hunk_count is None
    assert config.max_files_changed is None
    assert config.max_added_lines is None


def test_custom_values():
    config = ReviewabilityConfig(
        hunk_score_threshold=0.3,
        file_score_threshold=0.7,
        max_diff_lines=1000,
        max_problematic_hunks=5,
        max_problematic_files=4,
        max_hunk_lines=100,
        min_overall_score=0.6,
    )
    assert config.hunk_score_threshold == 0.3
    assert config.file_score_threshold == 0.7
    assert config.max_diff_lines == 1000
    assert config.max_problematic_hunks == 5
    assert config.max_problematic_files == 4
    assert config.max_hunk_lines == 100
    assert config.min_overall_score == 0.6


def test_frozen():
    config = ReviewabilityConfig()
    try:
        config.max_diff_lines = 999  # type: ignore[misc]
        assert False, "Should have raised FrozenInstanceError"
    except Exception:
        pass


def test_equality():
    c1 = ReviewabilityConfig()
    c2 = ReviewabilityConfig()
    assert c1 == c2


def test_inequality():
    c1 = ReviewabilityConfig()
    c2 = ReviewabilityConfig(max_diff_lines=999)
    assert c1 != c2


def test_partial_override():
    config = ReviewabilityConfig(max_diff_lines=200)
    assert config.max_diff_lines == 200
    assert config.hunk_score_threshold == 0.5
    assert config.min_overall_score is None


def test_zero_thresholds():
    config = ReviewabilityConfig(
        hunk_score_threshold=0.0,
        file_score_threshold=0.0,
        min_overall_score=0.0,
    )
    assert config.hunk_score_threshold == 0.0
    assert config.file_score_threshold == 0.0
    assert config.min_overall_score == 0.0


def test_max_thresholds():
    config = ReviewabilityConfig(
        hunk_score_threshold=1.0,
        file_score_threshold=1.0,
        min_overall_score=1.0,
    )
    assert config.hunk_score_threshold == 1.0
    assert config.file_score_threshold == 1.0
    assert config.min_overall_score == 1.0
