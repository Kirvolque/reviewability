
from reviewability.diff.movement import MovementDetector
from reviewability.diff.similarity_calculator import DiffSimilarityCalculator
from reviewability.domain.models import Hunk

# --- Helpers ---


def deletion_hunk(lines: list[str], file_path: str = "a.py") -> Hunk:
    return Hunk(
        file_path=file_path,
        source_start=1,
        source_length=len(lines),
        target_start=1,
        target_length=0,
        removed_lines=lines,
        added_lines=[],
    )


def insertion_hunk(lines: list[str], file_path: str = "b.py") -> Hunk:
    return Hunk(
        file_path=file_path,
        source_start=1,
        source_length=0,
        target_start=1,
        target_length=len(lines),
        removed_lines=[],
        added_lines=lines,
    )

def code_lines(n: int, indent: str = "    ") -> list[str]:
    """Generate n distinct, realistic-looking code lines with the given indent."""
    return [f"{indent}result_{i} = compute_value(input_{i}, factor={i})" for i in range(n)]


DETECTOR = MovementDetector()
SIMILARITY_CALCULATOR = DiffSimilarityCalculator()


def hunk_move_similarity(deletion: Hunk, insertion: Hunk) -> tuple[float, int, int]:
    deletion_lines = SIMILARITY_CALCULATOR.content_lines(deletion.removed_lines, deletion.file_path)
    insertion_lines = SIMILARITY_CALCULATOR.content_lines(insertion.added_lines, insertion.file_path)
    return (
        SIMILARITY_CALCULATOR.sequence_similarity(deletion_lines, insertion_lines),
        len(deletion_lines),
        len(insertion_lines),
    )
def hunks_are_likely_moved(detector: MovementDetector, deletion: Hunk, insertion: Hunk) -> bool:
    similarity, deletion_line_count, insertion_line_count = hunk_move_similarity(deletion, insertion)
    return detector.hunks_are_likely_moved(
        deletion,
        insertion,
        similarity=similarity,
        deletion_line_count=deletion_line_count,
        insertion_line_count=insertion_line_count,
    )


# --- Hunk: type checks ---


def test_hunk_mixed_deletion_not_eligible():
    # Deletion hunk that also has added lines is not a pure movement candidate
    hunk = Hunk(
        file_path="a.py",
        source_start=1, source_length=10, target_start=1, target_length=2,
        removed_lines=code_lines(10),
        added_lines=["    x = 1", "    y = 2"],
    )
    assert not hunks_are_likely_moved(DETECTOR, hunk, insertion_hunk(code_lines(10)))


def test_hunk_mixed_insertion_not_eligible():
    # Insertion hunk that also has removed lines is not a pure movement candidate
    hunk = Hunk(
        file_path="b.py",
        source_start=1, source_length=2, target_start=1, target_length=10,
        removed_lines=["    x = 1", "    y = 2"],
        added_lines=code_lines(10),
    )
    assert not hunks_are_likely_moved(DETECTOR, deletion_hunk(code_lines(10)), hunk)


# --- Hunk: size threshold ---


def test_hunk_below_min_lines_not_movement():
    lines = code_lines(5)  # below default min of 8
    assert not hunks_are_likely_moved(DETECTOR, deletion_hunk(lines), insertion_hunk(lines))


def test_hunk_exactly_at_min_lines_is_eligible():
    lines = code_lines(8)
    assert hunks_are_likely_moved(DETECTOR, deletion_hunk(lines), insertion_hunk(lines))


# --- Hunk: similarity ---


def test_hunk_identical_content_is_movement():
    lines = code_lines(10)
    assert hunks_are_likely_moved(DETECTOR, deletion_hunk(lines), insertion_hunk(lines))


def test_hunk_indentation_ignored():
    base = code_lines(10, indent="    ")
    reindented = code_lines(10, indent="        ")  # doubled indent
    assert hunks_are_likely_moved(DETECTOR, deletion_hunk(base), insertion_hunk(reindented))


def test_hunk_above_threshold_is_movement():
    # 19 of 20 lines match → ratio = 0.95 → passes default threshold of 0.95
    lines = code_lines(20)
    modified = lines[:-1] + ["    completely_different_line = True"]
    assert hunks_are_likely_moved(DETECTOR, deletion_hunk(lines), insertion_hunk(modified))


def test_hunk_below_threshold_is_not_movement():
    # 18 of 20 lines match → ratio ≈ 0.90 → below default threshold of 0.95
    lines = code_lines(20)
    modified = lines[:-2] + ["    different_a = 1", "    different_b = 2"]
    assert not hunks_are_likely_moved(DETECTOR, deletion_hunk(lines), insertion_hunk(modified))


def test_hunk_completely_different_is_not_movement():
    a = code_lines(10)
    b = [f"    foo_{i} = bar_{i}()" for i in range(100, 110)]
    assert not hunks_are_likely_moved(DETECTOR, deletion_hunk(a), insertion_hunk(b))


def test_hunk_custom_threshold_respected():
    lines = code_lines(20)
    modified = lines[:-3] + ["    x = 1", "    y = 2", "    z = 3"]
    # ratio ≈ 0.85 — fails at 0.95, passes at 0.80
    strict = MovementDetector(similarity_threshold=0.95)
    lenient = MovementDetector(similarity_threshold=0.80)
    assert not hunks_are_likely_moved(strict, deletion_hunk(lines), insertion_hunk(modified))
    assert hunks_are_likely_moved(lenient, deletion_hunk(lines), insertion_hunk(modified))


# --- Hunk: import filtering ---


def test_hunk_python_imports_ignored():
    content = code_lines(10)
    with_imports = ["import os", "from pathlib import Path"] + content
    without_imports = content
    d = deletion_hunk(with_imports, file_path="module.py")
    i = insertion_hunk(without_imports, file_path="other.py")
    assert hunks_are_likely_moved(DETECTOR, d, i)


def test_hunk_rust_use_statements_ignored():
    content = code_lines(10)
    with_use = ["use std::collections::HashMap;", "use std::io::Read;"] + content
    d = deletion_hunk(with_use, file_path="lib.rs")
    i = insertion_hunk(content, file_path="other.rs")
    assert hunks_are_likely_moved(DETECTOR, d, i)


def test_hunk_open_not_filtered_for_unknown_extension():
    # `open` is only filtered for F#/OCaml files; for unknown extensions it stays
    content = code_lines(8)
    with_open = ["open some_module"] + content
    d = deletion_hunk(with_open, file_path="script.xyz")
    i = insertion_hunk(content, file_path="other.xyz")
    # `open` line is NOT filtered → lines differ → similarity drops → not a movement
    assert not hunks_are_likely_moved(DETECTOR, d, i)


def test_hunk_open_filtered_for_fsharp():
    content = code_lines(9)
    with_open = ["open MyModule"] + content
    d = deletion_hunk(with_open, file_path="Program.fs")
    i = insertion_hunk(content, file_path="Other.fs")
    assert hunks_are_likely_moved(DETECTOR, d, i)
