from reviewability.diff.enrichment import DiffEnricher
from reviewability.domain.models import Diff, FileDiff, Hunk


# --- Spy detector ---


class SpyDetector:
    """Records every call to hunks_are_likely_moved / files_are_likely_moved.

    Call match_hunks / match_files to configure which pairs should return True.
    """

    def __init__(self) -> None:
        self.hunk_calls: list[tuple[Hunk, Hunk]] = []
        self.file_calls: list[tuple[FileDiff, FileDiff]] = []
        self._hunk_matches: set[tuple[int, int]] = set()
        self._file_matches: set[tuple[int, int]] = set()

    def match_hunks(self, deletion: Hunk, insertion: Hunk) -> None:
        self._hunk_matches.add((id(deletion), id(insertion)))

    def match_files(self, deleted: FileDiff, added: FileDiff) -> None:
        self._file_matches.add((id(deleted), id(added)))

    def hunks_are_likely_moved(self, deletion: Hunk, insertion: Hunk) -> bool:
        self.hunk_calls.append((deletion, insertion))
        return (id(deletion), id(insertion)) in self._hunk_matches

    def files_are_likely_moved(self, deleted: FileDiff, added: FileDiff) -> bool:
        self.file_calls.append((deleted, added))
        return (id(deleted), id(added)) in self._file_matches


# --- Helpers ---


def del_hunk(path: str = "del.py") -> Hunk:
    return Hunk(
        file_path=path,
        source_start=1, source_length=5, target_start=1, target_length=0,
        removed_lines=["line"] * 5,
    )


def ins_hunk(path: str = "ins.py") -> Hunk:
    return Hunk(
        file_path=path,
        source_start=1, source_length=0, target_start=1, target_length=5,
        added_lines=["line"] * 5,
    )


def file_with_hunk(hunk: Hunk, is_new: bool = False, is_deleted: bool = False) -> FileDiff:
    return FileDiff(
        path=hunk.file_path,
        old_path=None,
        is_new_file=is_new,
        is_deleted_file=is_deleted,
        hunks=[hunk],
    )


def del_file(path: str = "old.py") -> FileDiff:
    return FileDiff(
        path=path, old_path=None, is_new_file=False, is_deleted_file=True,
        hunks=[del_hunk(path)],
    )


def new_file(path: str = "new.py") -> FileDiff:
    return FileDiff(
        path=path, old_path=None, is_new_file=True, is_deleted_file=False,
        hunks=[ins_hunk(path)],
    )


def enricher(spy: SpyDetector) -> DiffEnricher:
    return DiffEnricher(detector=spy)  # type: ignore[arg-type]


# --- Hunk short-circuit: stop after first match for a deletion ---


def test_hunk_stops_checking_insertions_after_match():
    # 1 deletion, 2 insertions — deletion matches first insertion
    # detector should be called exactly once (breaks after match)
    spy = SpyDetector()
    d = del_hunk("d.py")
    i1 = ins_hunk("i1.py")
    i2 = ins_hunk("i2.py")
    spy.match_hunks(d, i1)

    diff = Diff(files=[
        file_with_hunk(d, is_deleted=True),
        file_with_hunk(i1, is_new=True),
        file_with_hunk(i2, is_new=True),
    ])
    enricher(spy).enrich(diff)

    assert len(spy.hunk_calls) == 1
    assert spy.hunk_calls[0] == (d, i1)


def test_hunk_skips_already_matched_insertion():
    # 2 deletions, 1 insertion — first deletion matches the insertion
    # second deletion should never check the already-matched insertion
    spy = SpyDetector()
    d1 = del_hunk("d1.py")
    d2 = del_hunk("d2.py")
    i = ins_hunk("i.py")
    spy.match_hunks(d1, i)

    diff = Diff(files=[
        file_with_hunk(d1, is_deleted=True),
        file_with_hunk(d2, is_deleted=True),
        file_with_hunk(i, is_new=True),
    ])
    enricher(spy).enrich(diff)

    # d1 checks i → match; d2 finds i already taken → 0 additional calls
    assert len(spy.hunk_calls) == 1
    assert spy.hunk_calls[0] == (d1, i)


def test_hunk_two_independent_pairs_each_checked_once():
    # 2 deletions, 2 insertions — each deletion matches its own insertion
    spy = SpyDetector()
    d1 = del_hunk("d1.py")
    d2 = del_hunk("d2.py")
    i1 = ins_hunk("i1.py")
    i2 = ins_hunk("i2.py")
    spy.match_hunks(d1, i1)
    spy.match_hunks(d2, i2)

    diff = Diff(files=[
        file_with_hunk(d1, is_deleted=True),
        file_with_hunk(d2, is_deleted=True),
        file_with_hunk(i1, is_new=True),
        file_with_hunk(i2, is_new=True),
    ])
    enricher(spy).enrich(diff)

    # d1 → i1 (1 call, match), d2 skips i1, checks i2 (1 call, match) = 2 total
    assert len(spy.hunk_calls) == 2


def test_hunk_no_match_checks_all_pairs():
    # No matches — every combination must be checked
    spy = SpyDetector()
    d1 = del_hunk("d1.py")
    d2 = del_hunk("d2.py")
    i1 = ins_hunk("i1.py")
    i2 = ins_hunk("i2.py")

    diff = Diff(files=[
        file_with_hunk(d1, is_deleted=True),
        file_with_hunk(d2, is_deleted=True),
        file_with_hunk(i1, is_new=True),
        file_with_hunk(i2, is_new=True),
    ])
    enricher(spy).enrich(diff)

    assert len(spy.hunk_calls) == 4  # full 2×2 search


# --- File short-circuit: same logic for files ---


def test_file_stops_checking_after_match():
    spy = SpyDetector()
    d = del_file("old.py")
    n1 = new_file("new1.py")
    n2 = new_file("new2.py")
    spy.match_files(d, n1)

    diff = Diff(files=[d, n1, n2])
    enricher(spy).enrich(diff)

    assert len(spy.file_calls) == 1
    assert spy.file_calls[0] == (d, n1)


def test_file_skips_already_matched_new_file():
    spy = SpyDetector()
    d1 = del_file("old1.py")
    d2 = del_file("old2.py")
    n = new_file("new.py")
    spy.match_files(d1, n)

    diff = Diff(files=[d1, d2, n])
    enricher(spy).enrich(diff)

    assert len(spy.file_calls) == 1
    assert spy.file_calls[0] == (d1, n)


def test_file_no_match_checks_all_pairs():
    spy = SpyDetector()
    d1 = del_file("old1.py")
    d2 = del_file("old2.py")
    n1 = new_file("new1.py")
    n2 = new_file("new2.py")

    diff = Diff(files=[d1, d2, n1, n2])
    enricher(spy).enrich(diff)

    assert len(spy.file_calls) == 4  # full 2×2 search


# --- Flags are set correctly ---


def test_matched_hunks_get_flag_set():
    spy = SpyDetector()
    d = del_hunk("d.py")
    i = ins_hunk("i.py")
    spy.match_hunks(d, i)

    diff = Diff(files=[
        file_with_hunk(d, is_deleted=True),
        file_with_hunk(i, is_new=True),
    ])
    result = enricher(spy).enrich(diff)

    all_hunks = [h for f in result.files for h in f.hunks]
    assert all(h.is_likely_moved for h in all_hunks)


def test_unmatched_hunks_flag_not_set():
    spy = SpyDetector()  # no matches configured
    d = del_hunk("d.py")
    i = ins_hunk("i.py")

    diff = Diff(files=[
        file_with_hunk(d, is_deleted=True),
        file_with_hunk(i, is_new=True),
    ])
    result = enricher(spy).enrich(diff)

    all_hunks = [h for f in result.files for h in f.hunks]
    assert not any(h.is_likely_moved for h in all_hunks)


def test_matched_files_get_flag_set():
    spy = SpyDetector()
    d = del_file("old.py")
    n = new_file("new.py")
    spy.match_files(d, n)

    result = enricher(spy).enrich(Diff(files=[d, n]))

    assert all(f.is_likely_moved for f in result.files)


def test_no_movement_returns_same_diff_object():
    # Short-circuit: if nothing is moved, the original Diff is returned as-is
    spy = SpyDetector()
    diff = Diff(files=[del_file(), new_file()])

    result = enricher(spy).enrich(diff)

    assert result is diff
