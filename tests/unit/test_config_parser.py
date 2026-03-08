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


def test_parse_with_reviewability_section():
    path = write_toml("""
[reviewability]
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


def test_parse_without_reviewability_section_uses_top_level():
    path = write_toml("""
max_diff_lines = 200
max_hunk_lines = 25
""")
    config = parse_config(path)
    assert config.max_diff_lines == 200
    assert config.max_hunk_lines == 25
    # Remaining fields are defaults
    assert config.hunk_score_threshold == 0.5


def test_parse_missing_section_uses_defaults():
    path = write_toml("")
    config = parse_config(path)
    assert config == ReviewabilityConfig()


def test_parse_unknown_keys_are_ignored():
    path = write_toml("""
[reviewability]
max_diff_lines = 100
unknown_key = "hello"
another_unknown = 42
""")
    config = parse_config(path)
    assert config.max_diff_lines == 100
    # Should not raise, and defaults used for other known fields
    assert config.hunk_score_threshold == 0.5


def test_parse_partial_section():
    path = write_toml("""
[reviewability]
min_overall_score = 0.8
""")
    config = parse_config(path)
    assert config.min_overall_score == 0.8
    # Everything else at defaults
    assert config.max_diff_lines == 500
    assert config.max_hunk_lines == 50


def test_parse_section_preferred_over_top_level():
    # When [reviewability] section is present, it takes precedence over top-level keys
    path = write_toml("""
max_diff_lines = 999

[reviewability]
max_diff_lines = 100
""")
    config = parse_config(path)
    assert config.max_diff_lines == 100


def test_parse_all_defaults_when_empty_section():
    path = write_toml("""
[reviewability]
""")
    config = parse_config(path)
    assert config == ReviewabilityConfig()
