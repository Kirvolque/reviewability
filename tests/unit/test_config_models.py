from reviewability.config.models import ReviewabilityConfig
from reviewability.config.parser import parse_config

# All required fields — used to construct configs in tests.
_REQUIRED = {
    "hunk_score_threshold": 0.5,
    "file_score_threshold": 0.5,
    "max_diff_lines": 500,
    "max_hunk_lines": 50,
    "rewrite_in_place_line_cost": 3.0,
    "rewrite_moved_line_cost": 4.0,
    "movement_hunk_min_lines": 8,
    "movement_file_min_lines": 15,
    "movement_similarity_threshold": 0.95,
}


def test_defaults_match_defaults_toml():
    from_toml = parse_config()
    from_constructor = ReviewabilityConfig(
        **_REQUIRED,
        min_overall_score=0.7,
        max_problematic_hunks=3,
        max_problematic_files=2,
        max_file_hunk_count=5,
        max_files_changed=10,
        max_added_lines=400,
    )
    assert from_toml == from_constructor


def test_custom_values():
    config = ReviewabilityConfig(
        hunk_score_threshold=0.3,
        file_score_threshold=0.7,
        max_diff_lines=1000,
        max_hunk_lines=100,
        rewrite_in_place_line_cost=2.5,
        rewrite_moved_line_cost=3.5,
        movement_hunk_min_lines=5,
        movement_file_min_lines=10,
        movement_similarity_threshold=0.9,
        max_problematic_hunks=5,
        max_problematic_files=4,
        min_overall_score=0.6,
    )
    assert config.hunk_score_threshold == 0.3
    assert config.file_score_threshold == 0.7
    assert config.max_diff_lines == 1000
    assert config.max_problematic_hunks == 5
    assert config.max_problematic_files == 4
    assert config.max_hunk_lines == 100
    assert config.rewrite_in_place_line_cost == 2.5
    assert config.rewrite_moved_line_cost == 3.5
    assert config.min_overall_score == 0.6


def test_frozen():
    config = ReviewabilityConfig(**_REQUIRED)
    try:
        config.max_diff_lines = 999  # type: ignore[misc]
        assert False, "Should have raised FrozenInstanceError"
    except Exception:
        pass


def test_equality():
    c1 = ReviewabilityConfig(**_REQUIRED)
    c2 = ReviewabilityConfig(**_REQUIRED)
    assert c1 == c2


def test_inequality():
    c1 = ReviewabilityConfig(**_REQUIRED)
    c2 = ReviewabilityConfig(**{**_REQUIRED, "max_diff_lines": 999})
    assert c1 != c2


def test_optional_fields_default_to_none():
    config = ReviewabilityConfig(**_REQUIRED)
    assert config.min_overall_score is None
    assert config.max_problematic_hunks is None
    assert config.max_problematic_files is None
    assert config.max_file_hunk_count is None
    assert config.max_files_changed is None
    assert config.max_added_lines is None


def test_zero_thresholds():
    config = ReviewabilityConfig(
        **{**_REQUIRED, "hunk_score_threshold": 0.0, "file_score_threshold": 0.0},
        min_overall_score=0.0,
    )
    assert config.hunk_score_threshold == 0.0
    assert config.file_score_threshold == 0.0
    assert config.min_overall_score == 0.0


def test_max_thresholds():
    config = ReviewabilityConfig(
        **{**_REQUIRED, "hunk_score_threshold": 1.0, "file_score_threshold": 1.0},
        min_overall_score=1.0,
    )
    assert config.hunk_score_threshold == 1.0
    assert config.file_score_threshold == 1.0
    assert config.min_overall_score == 1.0
