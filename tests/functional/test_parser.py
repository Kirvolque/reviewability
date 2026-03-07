from pathlib import Path

from reviewability.domain.models import Diff, FileDiff, Hunk
from reviewability.parser.git import parse_diff_text

FIXTURES = Path(__file__).parent.parent / "fixtures"


def load(name: str) -> str:
    return (FIXTURES / name).read_text()


def test_rename_only():
    diff = parse_diff_text(load("rename_only.diff"))
    assert diff == Diff(
        files=[
            FileDiff(
                path="src/greeter.py",
                old_path="a/src/old_name.py",
                is_new_file=False,
                is_deleted_file=False,
                hunks=[],
            )
        ]
    )


def test_logic_change():
    diff = parse_diff_text(load("logic_change.diff"))
    assert diff == Diff(
        files=[
            FileDiff(
                path="src/greeter.py",
                old_path=None,
                is_new_file=False,
                is_deleted_file=False,
                hunks=[
                    Hunk(
                        file_path="src/greeter.py",
                        source_start=1,
                        source_length=2,
                        target_start=1,
                        target_length=4,
                        added_lines=[
                            "    if not name:\n",
                            '        raise ValueError("name must not be empty")\n',
                        ],
                        removed_lines=[],
                        context_lines=[
                            "def greet(name: str) -> str:\n",
                            '    return f"Hello, {name}!"\n',
                        ],
                    )
                ],
            )
        ]
    )


def test_tangled_commit():
    diff = parse_diff_text(load("tangled_commit.diff"))
    assert diff == Diff(
        files=[
            FileDiff(
                path="src/farewell.py",
                old_path=None,
                is_new_file=True,
                is_deleted_file=False,
                hunks=[
                    Hunk(
                        file_path="src/farewell.py",
                        source_start=0,
                        source_length=0,
                        target_start=1,
                        target_length=4,
                        added_lines=[
                            "def say_goodbye(name: str) -> str:\n",
                            "    if not name:\n",
                            '        raise ValueError("name required")\n',
                            '    return f"Goodbye, {name}!"\n',
                        ],
                        removed_lines=[],
                        context_lines=[],
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
                        source_start=1,
                        source_length=2,
                        target_start=0,
                        target_length=0,
                        added_lines=[],
                        removed_lines=[
                            "def say_hello(name: str) -> str:\n",
                            '    return f"Hi, {name}!"\n',
                        ],
                        context_lines=[],
                    )
                ],
            ),
        ]
    )


def test_multi_file_change():
    diff = parse_diff_text(load("multi_file_change.diff"))
    assert diff == Diff(
        files=[
            FileDiff(
                path="src/farewell.py",
                old_path=None,
                is_new_file=False,
                is_deleted_file=False,
                hunks=[
                    Hunk(
                        file_path="src/farewell.py",
                        source_start=1,
                        source_length=4,
                        target_start=1,
                        target_length=6,
                        added_lines=[
                            'DEFAULT_FAREWELL = "Goodbye"\n',
                            "\n",
                            "def say_goodbye(name: str, farewell: str = DEFAULT_FAREWELL) -> str:\n",  # noqa: E501
                            '    return f"{farewell}, {name}!"\n',
                        ],
                        removed_lines=[
                            "def say_goodbye(name: str) -> str:\n",
                            '    return f"Goodbye, {name}!"\n',
                        ],
                        context_lines=[
                            "    if not name:\n",
                            '        raise ValueError("name required")\n',
                        ],
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
                        source_start=1,
                        source_length=4,
                        target_start=1,
                        target_length=6,
                        added_lines=[
                            'DEFAULT_GREETING = "Hello"\n',
                            "\n",
                            "def greet(name: str, greeting: str = DEFAULT_GREETING) -> str:\n",
                            '    return f"{greeting}, {name}!"\n',
                        ],
                        removed_lines=[
                            "def greet(name: str) -> str:\n",
                            '    return f"Hello, {name}!"\n',
                        ],
                        context_lines=[
                            "    if not name:\n",
                            '        raise ValueError("name must not be empty")\n',
                        ],
                    )
                ],
            ),
        ]
    )
