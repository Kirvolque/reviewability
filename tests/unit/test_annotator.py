from reviewability.diff.annotator import DiffAnnotator
from reviewability.diff.similarity_calculator import DiffSimilarityCalculator
from reviewability.domain.models import Diff, FileDiff, Hunk, HunkRewriteKind

# --- Spy detector ---


class SpyDetector:
    """Records every call to the movement detector's hunk pair checks.

    Call match_hunks to configure which pairs should return True.
    """

    def __init__(self) -> None:
        self.hunk_calls: list[tuple[Hunk, Hunk]] = []
        self._hunk_matches: set[tuple[int, int]] = set()

    def match_hunks(self, deletion: Hunk, insertion: Hunk) -> None:
        self._hunk_matches.add((id(deletion), id(insertion)))

    def hunks_are_likely_moved(
        self,
        deletion: Hunk,
        insertion: Hunk,
        *,
        similarity: float,
        deletion_line_count: int,
        insertion_line_count: int,
    ) -> bool:
        self.hunk_calls.append((deletion, insertion))
        return (id(deletion), id(insertion)) in self._hunk_matches


class SpyRewriteDetector:
    def __init__(self) -> None:
        self.calls: list[tuple[Hunk, Hunk]] = []
        self._matches: dict[tuple[int, int], HunkRewriteKind] = {}

    def classify_rewrite(
        self,
        deletion: Hunk,
        insertion: Hunk,
        similarity_calculator: DiffSimilarityCalculator,
    ) -> HunkRewriteKind | None:
        self.calls.append((deletion, insertion))
        return self._matches.get((id(deletion), id(insertion)))

    def match(
        self,
        deletion: Hunk,
        insertion: Hunk,
        kind: HunkRewriteKind,
    ) -> None:
        self._matches[(id(deletion), id(insertion))] = kind


class CountingSimilarityCalculator(DiffSimilarityCalculator):
    def __init__(self) -> None:
        super().__init__()
        self.content_calls: dict[tuple[str, tuple[str, ...]], int] = {}
        self.sequence_calls: dict[tuple[tuple[str, ...], tuple[str, ...]], int] = {}

    def content_lines(self, lines: list[str], file_path: str) -> list[str]:
        key = (file_path, tuple(lines))
        self.content_calls[key] = self.content_calls.get(key, 0) + 1
        return super().content_lines(lines, file_path)

    def sequence_similarity(self, a: list[str] | tuple[str, ...], b: list[str] | tuple[str, ...]) -> float:
        key = (tuple(a), tuple(b))
        self.sequence_calls[key] = self.sequence_calls.get(key, 0) + 1
        return super().sequence_similarity(a, b)


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


def enricher(
    movement_detector: SpyDetector,
    complex_rewrite_detector: SpyRewriteDetector | None = None,
) -> DiffAnnotator:
    return DiffAnnotator(
        movement_detector=movement_detector,  # type: ignore[arg-type]
        complex_rewrite_detector=complex_rewrite_detector or SpyRewriteDetector(),  # type: ignore[arg-type]
    )


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


def test_hunk_pair_similarity_is_calculated_at_most_once():
    detector = SpyDetector()
    similarity_calculator = CountingSimilarityCalculator()
    d1 = del_hunk("d1.py")
    i1 = ins_hunk("i1.py")
    enricher = DiffAnnotator(
        movement_detector=detector,
        similarity_calculator=similarity_calculator,
    )  # type: ignore[arg-type]
    hunk_lines_by_id = {
        id(d1): tuple(
            similarity_calculator.content_lines(d1.removed_lines, d1.file_path)
        ),
        id(i1): tuple(
            similarity_calculator.content_lines(i1.added_lines, i1.file_path)
        ),
    }

    assert not enricher._is_hunk_pair_likely_moved(  # noqa: SLF001
        d1,
        i1,
        hunk_lines_by_id=hunk_lines_by_id,
    )
    assert not enricher._is_hunk_pair_likely_moved(  # noqa: SLF001
        d1,
        i1,
        hunk_lines_by_id=hunk_lines_by_id,
    )

    assert sum(similarity_calculator.sequence_calls.values()) == 1
    assert all(count == 1 for count in similarity_calculator.sequence_calls.values())
    assert similarity_calculator.pair_similarity_cache == {(id(d1), id(i1)): 1.0}

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

    assert result is diff
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

    assert result is diff
    all_hunks = [h for f in result.files for h in f.hunks]
    assert not any(h.is_likely_moved for h in all_hunks)


def test_complex_rewrite_detector_runs_after_movement_and_marks_hunks():
    movement_detector = SpyDetector()
    complex_rewrite_detector = SpyRewriteDetector()
    moved_deletion = del_hunk("moved_del.py")
    moved_insertion = ins_hunk("moved_ins.py")
    rewritten_deletion = del_hunk("rewrite_del.py")
    rewritten_insertion = ins_hunk("rewrite_ins.py")
    movement_detector.match_hunks(moved_deletion, moved_insertion)
    complex_rewrite_detector.match(
        rewritten_deletion,
        rewritten_insertion,
        HunkRewriteKind.MOVED_REWRITE,
    )

    diff = Diff(files=[
        file_with_hunk(moved_deletion, is_deleted=True),
        file_with_hunk(moved_insertion, is_new=True),
        file_with_hunk(rewritten_deletion, is_deleted=True),
        file_with_hunk(rewritten_insertion, is_new=True),
    ])
    result = enricher(movement_detector, complex_rewrite_detector).enrich(diff)

    assert result is diff
    moved_hunks = [h for f in result.files for h in f.hunks if h.file_path.startswith("moved_")]
    rewritten_hunks = [
        h for f in result.files for h in f.hunks if h.file_path.startswith("rewrite_")
    ]

    assert all(h.is_likely_moved for h in moved_hunks)
    assert all(h.rewrite_kind is None for h in moved_hunks)
    assert all(not h.is_likely_moved for h in rewritten_hunks)
    assert all(h.rewrite_kind is HunkRewriteKind.MOVED_REWRITE for h in rewritten_hunks)
    assert (moved_deletion, moved_insertion) not in complex_rewrite_detector.calls

def test_no_movement_returns_same_diff_object():
    # Short-circuit: if nothing is moved, the original Diff is returned as-is
    spy = SpyDetector()
    diff = Diff(
        files=[
            file_with_hunk(del_hunk("del.py"), is_deleted=True),
            file_with_hunk(ins_hunk("ins.py"), is_new=True),
        ]
    )

    result = enricher(spy).enrich(diff)

    assert result is diff
