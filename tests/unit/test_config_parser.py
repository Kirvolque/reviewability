import tempfile
from pathlib import Path

from reviewability.config.models import ReviewabilityConfig
from reviewability.config.parser import parse_config


def write_toml(content: str) -> Path:
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False)
    tmp.write(content)
    tmp.flush()
    tmp.close()
    return Path(tmp.name)


def test_parse_top_level_keys():
    path = write_toml("""
max_diff_lines = 300
max_hunk_lines = 80
hunk_score_threshold = 0.4
file_score_threshold = 0.6
max_problematic_hunks = 5
max_problematic_files = 3
min_overall_score = 0.7
""")
    config = parse_config(path)
    assert config == ReviewabilityConfig(
        max_diff_lines=300,
        max_hunk_lines=80,
        hunk_score_threshold=0.4,
        file_score_threshold=0.6,
        max_problematic_hunks=5,
        max_problematic_files=3,
        min_overall_score=0.7,
    )


def test_parse_movement_detection_section():
    path = write_toml("""
[movement_detection]
hunk_min_lines = 5
file_min_lines = 10
similarity_threshold = 0.9
""")
    config = parse_config(path)
    assert config.movement_hunk_min_lines == 5
    assert config.movement_file_min_lines == 10
    assert config.movement_similarity_threshold == 0.9


def test_parse_mixed_top_level_and_section():
    path = write_toml("""
max_diff_lines = 200
min_overall_score = 0.6

[movement_detection]
similarity_threshold = 0.8
""")
    config = parse_config(path)
    assert config.max_diff_lines == 200
    assert config.min_overall_score == 0.6
    assert config.movement_similarity_threshold == 0.8
    assert config.movement_hunk_min_lines == 8  # default


def test_parse_empty_file_uses_defaults():
    path = write_toml("")
    config = parse_config(path)
    assert config == ReviewabilityConfig()


def test_parse_unknown_keys_are_ignored():
    path = write_toml("""
max_diff_lines = 100
unknown_key = "hello"

[movement_detection]
similarity_threshold = 0.9
unknown_movement_key = 42
""")
    config = parse_config(path)
    assert config.max_diff_lines == 100
    assert config.movement_similarity_threshold == 0.9


def test_parse_partial_config_uses_defaults_for_rest():
    path = write_toml("""
min_overall_score = 0.8
""")
    config = parse_config(path)
    assert config.min_overall_score == 0.8
    assert config.max_diff_lines == 500
    assert config.max_hunk_lines == 50
    assert config.movement_hunk_min_lines == 8


def test_parse_unknown_section_is_ignored():
    path = write_toml("""
max_diff_lines = 100

[some_future_section]
some_key = 42
""")
    config = parse_config(path)
    assert config.max_diff_lines == 100
    assert config == ReviewabilityConfig(max_diff_lines=100)
