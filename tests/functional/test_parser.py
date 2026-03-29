from pathlib import Path

from reviewability.config.parser import parse_config
from reviewability.diff_reader import parse_diff_text
from reviewability.domain.models import ChangeType, FileDiff, Hunk, HunkType

A = ChangeType.ADDED
R = ChangeType.REMOVED

FIXTURES = Path(__file__).parent.parent / "fixtures"

_DEFAULT_CONFIG = parse_config()


def load(name: str) -> str:
    return (FIXTURES / name).read_text()


def test_rename_only():
    diff = parse_diff_text(load("rename_only.diff"), _DEFAULT_CONFIG)
    assert diff.files == [
        FileDiff(
            path="src/greeter.py",
            old_path="src/old_name.py",
            is_new_file=False,
            is_deleted_file=False,
            hunks=[],
        )
    ]


def test_logic_change():
    diff = parse_diff_text(load("logic_change.diff"), _DEFAULT_CONFIG)
    assert diff.files == [
        FileDiff(
            path="src/greeter.py",
            old_path=None,
            is_new_file=False,
            is_deleted_file=False,
            hunks=[
                Hunk(
                    file_path="src/greeter.py",
                    added_lines=[
                        "if not name:",
                        'raise ValueError("name must not be empty")',
                    ],
                    removed_lines=[],
                    context_lines=[
                        "def greet(name: str) -> str:\n",
                        '    return f"Hello, {name}!"\n',
                    ],
                    change_order=(A, A),
                    hunk_type=HunkType.PURE_ADDITION,
                )
            ],
        )
    ]


def test_tangled_commit():
    diff = parse_diff_text(load("tangled_commit.diff"), _DEFAULT_CONFIG)
    assert diff.files == [
        FileDiff(
            path="src/farewell.py",
            old_path=None,
            is_new_file=True,
            is_deleted_file=False,
            hunks=[
                Hunk(
                    file_path="src/farewell.py",
                    added_lines=[
                        "def say_goodbye(name: str) -> str:",
                        "if not name:",
                        'raise ValueError("name required")',
                        'return f"Goodbye, {name}!"',
                    ],
                    removed_lines=[],
                    context_lines=[],
                    change_order=(A, A, A, A),
                    hunk_type=HunkType.MIXED,
                )
            ],
        ),
        FileDiff(
            path="src/hello.py",
            old_path=None,
            is_new_file=False,
            is_deleted_file=True,
            hunks=[
                Hunk(
                    file_path="src/hello.py",
                    added_lines=[],
                    removed_lines=[
                        "def say_hello(name: str) -> str:",
                        'return f"Hi, {name}!"',
                    ],
                    context_lines=[],
                    change_order=(R, R),
                    hunk_type=HunkType.MIXED,
                )
            ],
        ),
    ]


def test_multi_file_change():
    diff = parse_diff_text(load("multi_file_change.diff"), _DEFAULT_CONFIG)
    assert diff.files == [
        FileDiff(
            path="src/farewell.py",
            old_path=None,
            is_new_file=False,
            is_deleted_file=False,
            hunks=[
                Hunk(
                    file_path="src/farewell.py",
                    added_lines=[
                        'DEFAULT_FAREWELL = "Goodbye"',
                        "def say_goodbye(name: str, farewell: str = DEFAULT_FAREWELL) -> str:",
                        'return f"{farewell}, {name}!"',
                    ],
                    removed_lines=[
                        "def say_goodbye(name: str) -> str:",
                        'return f"Goodbye, {name}!"',
                    ],
                    context_lines=[
                        "    if not name:\n",
                        '        raise ValueError("name required")\n',
                    ],
                    change_order=(R, A, A, R, A),
                    hunk_type=HunkType.MIXED,
                )
            ],
        ),
        FileDiff(
            path="src/greeter.py",
            old_path=None,
            is_new_file=False,
            is_deleted_file=False,
            hunks=[
                Hunk(
                    file_path="src/greeter.py",
                    added_lines=[
                        'DEFAULT_GREETING = "Hello"',
                        "def greet(name: str, greeting: str = DEFAULT_GREETING) -> str:",
                        'return f"{greeting}, {name}!"',
                    ],
                    removed_lines=[
                        "def greet(name: str) -> str:",
                        'return f"Hello, {name}!"',
                    ],
                    context_lines=[
                        "    if not name:\n",
                        '        raise ValueError("name must not be empty")\n',
                    ],
                    change_order=(R, A, A, R, A),
                    hunk_type=HunkType.MIXED,
                )
            ],
        ),
    ]
