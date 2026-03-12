import pytest

from reviewability.analysis.movement import MovementDetector
from reviewability.domain.models import FileDiff, Hunk


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


def deleted_file(lines: list[str], path: str = "old.py") -> FileDiff:
    return FileDiff(
        path=path,
        old_path=None,
        is_new_file=False,
        is_deleted_file=True,
        hunks=[deletion_hunk(lines, file_path=path)],
    )


def new_file(lines: list[str], path: str = "new.py") -> FileDiff:
    return FileDiff(
        path=path,
        old_path=None,
        is_new_file=True,
        is_deleted_file=False,
        hunks=[insertion_hunk(lines, file_path=path)],
    )


def code_lines(n: int, indent: str = "    ") -> list[str]:
    """Generate n distinct, realistic-looking code lines with the given indent."""
    return [f"{indent}result_{i} = compute_value(input_{i}, factor={i})" for i in range(n)]


DETECTOR = MovementDetector()


# --- Hunk: type checks ---


def test_hunk_mixed_deletion_not_eligible():
    # Deletion hunk that also has added lines is not a pure movement candidate
    hunk = Hunk(
        file_path="a.py",
        source_start=1, source_length=10, target_start=1, target_length=2,
        removed_lines=code_lines(10),
        added_lines=["    x = 1", "    y = 2"],
    )
    assert not DETECTOR.hunks_are_likely_moved(hunk, insertion_hunk(code_lines(10)))


def test_hunk_mixed_insertion_not_eligible():
    # Insertion hunk that also has removed lines is not a pure movement candidate
    hunk = Hunk(
        file_path="b.py",
        source_start=1, source_length=2, target_start=1, target_length=10,
        removed_lines=["    x = 1", "    y = 2"],
        added_lines=code_lines(10),
    )
    assert not DETECTOR.hunks_are_likely_moved(deletion_hunk(code_lines(10)), hunk)


# --- Hunk: size threshold ---


def test_hunk_below_min_lines_not_movement():
    lines = code_lines(5)  # below default min of 8
    assert not DETECTOR.hunks_are_likely_moved(deletion_hunk(lines), insertion_hunk(lines))


def test_hunk_exactly_at_min_lines_is_eligible():
    lines = code_lines(8)
    assert DETECTOR.hunks_are_likely_moved(deletion_hunk(lines), insertion_hunk(lines))


# --- Hunk: similarity ---


def test_hunk_identical_content_is_movement():
    lines = code_lines(10)
    assert DETECTOR.hunks_are_likely_moved(deletion_hunk(lines), insertion_hunk(lines))


def test_hunk_indentation_ignored():
    base = code_lines(10, indent="    ")
    reindented = code_lines(10, indent="        ")  # doubled indent
    assert DETECTOR.hunks_are_likely_moved(deletion_hunk(base), insertion_hunk(reindented))


def test_hunk_above_threshold_is_movement():
    # 19 of 20 lines match → ratio = 0.95 → passes default threshold of 0.95
    lines = code_lines(20)
    modified = lines[:-1] + ["    completely_different_line = True"]
    assert DETECTOR.hunks_are_likely_moved(deletion_hunk(lines), insertion_hunk(modified))


def test_hunk_below_threshold_is_not_movement():
    # 18 of 20 lines match → ratio ≈ 0.90 → below default threshold of 0.95
    lines = code_lines(20)
    modified = lines[:-2] + ["    different_a = 1", "    different_b = 2"]
    assert not DETECTOR.hunks_are_likely_moved(deletion_hunk(lines), insertion_hunk(modified))


def test_hunk_completely_different_is_not_movement():
    a = code_lines(10)
    b = [f"    foo_{i} = bar_{i}()" for i in range(100, 110)]
    assert not DETECTOR.hunks_are_likely_moved(deletion_hunk(a), insertion_hunk(b))


def test_hunk_custom_threshold_respected():
    lines = code_lines(20)
    modified = lines[:-3] + ["    x = 1", "    y = 2", "    z = 3"]
    # ratio ≈ 0.85 — fails at 0.95, passes at 0.80
    strict = MovementDetector(similarity_threshold=0.95)
    lenient = MovementDetector(similarity_threshold=0.80)
    assert not strict.hunks_are_likely_moved(deletion_hunk(lines), insertion_hunk(modified))
    assert lenient.hunks_are_likely_moved(deletion_hunk(lines), insertion_hunk(modified))


# --- Hunk: import filtering ---


def test_hunk_python_imports_ignored():
    content = code_lines(10)
    with_imports = ["import os", "from pathlib import Path"] + content
    without_imports = content
    d = deletion_hunk(with_imports, file_path="module.py")
    i = insertion_hunk(without_imports, file_path="other.py")
    assert DETECTOR.hunks_are_likely_moved(d, i)


def test_hunk_rust_use_statements_ignored():
    content = code_lines(10)
    with_use = ["use std::collections::HashMap;", "use std::io::Read;"] + content
    d = deletion_hunk(with_use, file_path="lib.rs")
    i = insertion_hunk(content, file_path="other.rs")
    assert DETECTOR.hunks_are_likely_moved(d, i)


def test_hunk_open_not_filtered_for_unknown_extension():
    # `open` is only filtered for F#/OCaml files; for unknown extensions it stays
    content = code_lines(8)
    with_open = ["open some_module"] + content
    d = deletion_hunk(with_open, file_path="script.xyz")
    i = insertion_hunk(content, file_path="other.xyz")
    # `open` line is NOT filtered → lines differ → similarity drops → not a movement
    assert not DETECTOR.hunks_are_likely_moved(d, i)


def test_hunk_open_filtered_for_fsharp():
    content = code_lines(9)
    with_open = ["open MyModule"] + content
    d = deletion_hunk(with_open, file_path="Program.fs")
    i = insertion_hunk(content, file_path="Other.fs")
    assert DETECTOR.hunks_are_likely_moved(d, i)


# --- File: type checks ---


def test_file_not_deleted_returns_false():
    not_deleted = FileDiff(path="a.py", old_path=None, is_new_file=False, is_deleted_file=False)
    assert not DETECTOR.files_are_likely_moved(not_deleted, new_file(code_lines(20)))


def test_file_not_new_returns_false():
    not_new = FileDiff(path="b.py", old_path=None, is_new_file=False, is_deleted_file=False)
    assert not DETECTOR.files_are_likely_moved(deleted_file(code_lines(20)), not_new)


# --- File: size threshold ---


def test_file_below_min_lines_not_movement():
    lines = code_lines(10)  # below default min of 15
    assert not DETECTOR.files_are_likely_moved(deleted_file(lines), new_file(lines))


def test_file_exactly_at_min_lines_is_eligible():
    lines = code_lines(15)
    assert DETECTOR.files_are_likely_moved(deleted_file(lines), new_file(lines))


# --- File: similarity ---


def test_file_identical_content_is_movement():
    lines = code_lines(20)
    assert DETECTOR.files_are_likely_moved(deleted_file(lines), new_file(lines))


def test_file_indentation_ignored():
    base = code_lines(20, indent="  ")
    reindented = code_lines(20, indent="    ")
    assert DETECTOR.files_are_likely_moved(deleted_file(base), new_file(reindented))


def test_file_below_threshold_is_not_movement():
    lines = code_lines(20)
    different = [f"    totally_different_{i}()" for i in range(20)]
    assert not DETECTOR.files_are_likely_moved(deleted_file(lines), new_file(different))


# --- File: import filtering ---


def test_file_python_package_imports_ignored():
    content = code_lines(20)
    old_lines = ["import old.package.utils", "from old.models import Foo"] + content
    new_lines = ["import new.package.utils", "from new.models import Foo"] + content
    assert DETECTOR.files_are_likely_moved(
        deleted_file(old_lines, path="src/old/service.py"),
        new_file(new_lines, path="src/new/service.py"),
    )


def test_file_java_package_declaration_ignored():
    content = code_lines(20)
    old_lines = ["package com.example.old;", "import com.example.old.Util;"] + content
    new_lines = ["package com.example.new;", "import com.example.new.Util;"] + content
    assert DETECTOR.files_are_likely_moved(
        deleted_file(old_lines, path="OldService.java"),
        new_file(new_lines, path="NewService.java"),
    )
