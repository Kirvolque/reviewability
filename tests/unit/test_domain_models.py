from reviewability.domain.models import Diff, FileDiff, Hunk


def make_hunk(
    file_path: str = "a.py",
    added: list[str] | None = None,
    removed: list[str] | None = None,
    context: list[str] | None = None,
    source_start: int = 1,
) -> Hunk:
    added = added or []
    removed = removed or []
    context = context or []
    return Hunk(
        file_path=file_path,
        source_start=source_start,
        source_length=len(removed),
        target_start=source_start,
        target_length=len(added),
        added_lines=added,
        removed_lines=removed,
        context_lines=context,
    )


def make_file(
    path: str = "a.py",
    hunks: list[Hunk] | None = None,
    old_path: str | None = None,
    is_new_file: bool = False,
    is_deleted_file: bool = False,
) -> FileDiff:
    return FileDiff(
        path=path,
        old_path=old_path,
        is_new_file=is_new_file,
        is_deleted_file=is_deleted_file,
        hunks=hunks or [],
    )


# --- Hunk tests ---


def test_hunk_added_count():
    hunk = make_hunk(added=["a", "b", "c"])
    assert hunk.added_count == 3


def test_hunk_removed_count():
    hunk = make_hunk(removed=["x", "y"])
    assert hunk.removed_count == 2


def test_hunk_added_and_removed_count():
    hunk = make_hunk(added=["a"], removed=["x", "y"])
    assert hunk.added_count == 1
    assert hunk.removed_count == 2


def test_hunk_fields():
    hunk = Hunk(
        file_path="foo.py",
        source_start=10,
        source_length=3,
        target_start=12,
        target_length=2,
        added_lines=["x"],
        removed_lines=["y", "z"],
        context_lines=["ctx"],
    )
    assert hunk.file_path == "foo.py"
    assert hunk.source_start == 10
    assert hunk.source_length == 3
    assert hunk.target_start == 12
    assert hunk.target_length == 2
    assert hunk.added_lines == ["x"]
    assert hunk.removed_lines == ["y", "z"]
    assert hunk.context_lines == ["ctx"]


def test_hunk_default_empty_lists():
    hunk = Hunk(
        file_path="a.py",
        source_start=1,
        source_length=0,
        target_start=1,
        target_length=0,
    )
    assert hunk.added_lines == []
    assert hunk.removed_lines == []
    assert hunk.context_lines == []


def test_hunk_equality():
    h1 = make_hunk(added=["a"])
    h2 = make_hunk(added=["a"])
    assert h1 == h2


def test_hunk_inequality():
    h1 = make_hunk(added=["a"])
    h2 = make_hunk(added=["b"])
    assert h1 != h2


# --- FileDiff tests ---


def test_file_diff_fields():
    f = FileDiff(
        path="src/foo.py",
        old_path="src/bar.py",
        is_new_file=False,
        is_deleted_file=False,
    )
    assert f.path == "src/foo.py"
    assert f.old_path == "src/bar.py"
    assert f.is_new_file is False
    assert f.is_deleted_file is False


def test_file_diff_new_file():
    f = make_file(is_new_file=True)
    assert f.is_new_file is True


def test_file_diff_deleted_file():
    f = make_file(is_deleted_file=True)
    assert f.is_deleted_file is True


def test_file_diff_old_path_none():
    f = make_file(old_path=None)
    assert f.old_path is None


def test_file_diff_renamed():
    f = FileDiff(path="new.py", old_path="old.py", is_new_file=False, is_deleted_file=False)
    assert f.old_path == "old.py"


def test_file_diff_default_empty_hunks():
    f = FileDiff(path="a.py", old_path=None, is_new_file=False, is_deleted_file=False)
    assert f.hunks == []


def test_file_diff_is_mutable():
    f = make_file()
    f.path = "b.py"
    assert f.path == "b.py"


# --- Diff tests ---


def test_diff_all_hunks():
    h1 = make_hunk()
    h2 = make_hunk()
    h3 = make_hunk()
    d = Diff(files=[make_file("a.py", hunks=[h1, h2]), make_file("b.py", hunks=[h3])])
    assert d.all_hunks == [h1, h2, h3]


def test_diff_all_hunks_empty():
    d = Diff(files=[])
    assert d.all_hunks == []


def test_diff_default_empty_files():
    d = Diff()
    assert d.files == []


def test_diff_is_mutable():
    d = Diff()
    d.files = [make_file("a.py")]
    assert len(d.files) == 1
