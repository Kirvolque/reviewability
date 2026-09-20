from reviewability.domain.models import Hunk, Move, MoveType
from reviewability.formatter import _move_alignment


def test_move_alignment_keeps_exact_matches_and_residual_edits_separate():
    source = Hunk(
        file_path="src/legacy.py",
        source_start=10,
        removed_lines=["def old_name():", "prepare()", "return result"],
    )
    target = Hunk(
        file_path="src/current.py",
        target_start=30,
        added_lines=["def new_name():", "prepare()", "return result", "publish()"],
    )
    move = Move(
        move_id=1,
        hunks=(source, target),
        similarity=0.8,
        move_type=MoveType.MODIFIED,
        length=4,
        source_hunk=source,
        target_hunk=target,
    )

    assert _move_alignment(move) == [
        {
            "kind": "removed",
            "source": {"file": "src/legacy.py", "line": 10, "content": "def old_name():"},
        },
        {
            "kind": "exact_match",
            "source": {"file": "src/legacy.py", "line": 11, "content": "prepare()"},
            "target": {"file": "src/current.py", "line": 31, "content": "prepare()"},
        },
        {
            "kind": "exact_match",
            "source": {"file": "src/legacy.py", "line": 12, "content": "return result"},
            "target": {"file": "src/current.py", "line": 32, "content": "return result"},
        },
        {
            "kind": "added",
            "target": {"file": "src/current.py", "line": 30, "content": "def new_name():"},
        },
        {
            "kind": "added",
            "target": {"file": "src/current.py", "line": 33, "content": "publish()"},
        },
    ]
