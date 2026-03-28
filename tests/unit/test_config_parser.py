import tempfile
from pathlib import Path

import pytest

from reviewability.config.parser import parse_config

_FULL_CONFIG = """\
hunk_score_threshold = 0.5
file_score_threshold = 0.5
max_diff_lines = 500
max_hunk_lines = 50
min_overall_score = 0.7
"""


def write_toml(content: str) -> Path:
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False)
    tmp.write(content)
    tmp.flush()
    tmp.close()
    return Path(tmp.name)


def test_parse_complete_config():
    path = write_toml(_FULL_CONFIG)
    config = parse_config(path)
    assert config.hunk_score_threshold == 0.5
    assert config.file_score_threshold == 0.5
    assert config.max_diff_lines == 500
    assert config.max_hunk_lines == 50
    assert config.min_overall_score == 0.7


def test_parse_custom_values():
    path = write_toml("""\
hunk_score_threshold = 0.3
file_score_threshold = 0.7
max_diff_lines = 300
max_hunk_lines = 80
min_overall_score = 0.6
max_problematic_hunks = 5
max_problematic_files = 3
""")
    config = parse_config(path)
    assert config.hunk_score_threshold == 0.3
    assert config.file_score_threshold == 0.7
    assert config.max_diff_lines == 300
    assert config.max_hunk_lines == 80
    assert config.min_overall_score == 0.6
    assert config.max_problematic_hunks == 5
    assert config.max_problematic_files == 3


def test_parse_no_path_returns_bundled_defaults():
    config = parse_config()
    assert config.max_diff_lines == 500
    assert config.max_hunk_lines == 50
    assert config.hunk_score_threshold == 0.5
    assert config.min_overall_score == 0.7


def test_parse_nonexistent_path_returns_bundled_defaults():
    config = parse_config(Path("/nonexistent/reviewability.toml"))
    assert config.max_diff_lines == 500
    assert config.min_overall_score == 0.7


def test_parse_unknown_keys_are_ignored():
    path = write_toml("""\
hunk_score_threshold = 0.5
file_score_threshold = 0.5
max_diff_lines = 100
max_hunk_lines = 50
unknown_key = "hello"
""")
    config = parse_config(path)
    assert config.max_diff_lines == 100


def test_parse_unknown_section_is_ignored():
    path = write_toml("""\
hunk_score_threshold = 0.5
file_score_threshold = 0.5
max_diff_lines = 100
max_hunk_lines = 50

[some_future_section]
some_key = 42
""")
    config = parse_config(path)
    assert config.max_diff_lines == 100


def test_missing_mandatory_field_raises_error():
    path = write_toml("""\
max_diff_lines = 100
""")
    with pytest.raises(TypeError, match="required"):
        parse_config(path)


def test_optional_fields_can_be_omitted():
    path = write_toml(_FULL_CONFIG)
    config = parse_config(path)
    assert config.max_problematic_hunks is None
    assert config.max_problematic_files is None
    assert config.max_files_changed is None
    assert config.max_added_lines is None
