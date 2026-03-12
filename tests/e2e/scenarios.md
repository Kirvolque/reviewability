# E2E Test Scenarios

Proposed scenarios for end-to-end tests.
"Expected" reflects whether the diff shape is easy to review, not whether the code is correct.

Defaults: `max_diff_lines=500`, `max_hunk_lines=50`, `hunk_score_threshold=0.5`, `max_problematic_hunks=3`

| # | Shape of changes | Expected | Need test? |
|---|-----------------|----------|-----------|
| 1 | 1 file, 1 hunk, 1 line changed, churn ratio 0% (pure fix) | PASS | N         |
| 2 | 1 file, 1 hunk, 30 lines added, 0 removed (new function) | PASS | N         |
| 3 | 1 file, 1 hunk, 0 lines added, 25 removed (dead code removal) | PASS | N         |
| 4 | 1 new file, 80 lines added, 0 removed | PASS | N         |
| 5 | 2 files, 4 hunks, ~60 lines added, ~5 lines context adjusted, churn ratio <10% | PASS | Y         |
| 6 | 1 file deleted, 120 lines removed, 0 added | PASS |           |
| 7 | 1 file, 6 hunks, 200 lines changed — all indentation/formatting, churn ratio 0% | PASS |           |
| 8 | 2 files, file A: 40 lines removed / file B: 40 lines added, churn ratio 0% per hunk | PASS |           |
| 9 | 1 file, 3 hunks, 15 lines added (docstrings only), churn ratio 0% | PASS |           |
| 10 | 3 files, 1 old file deleted (60 lines), 2 new files added (30 lines each), churn ratio 0% | PASS |           |
| 11 | 8 files, 420 lines changed (84% of limit), all hunks directional, churn ratio 0% | FAIL (size) | Y         |
| 12 | 1 file, 2 hunks, 40 lines each, churn ratio 80% — function split with heavy interleaving | FAIL | Y         |
| 13 | 1 file, 1 hunk, 30 lines — block moved within file, 50% adds / 50% removes interleaved | FAIL | TBD       |
| 14 | 5 files, 150 lines changed, 4+ hunks each with churn ratio >70% | FAIL | Y         |
| 15 | 2 files, 60 lines added (new interface) + 40 lines modified (existing class), 4 mixed hunks | FAIL |           |
| 16 | 6 files, 310 lines changed (62% of limit), churn ratio 60% average across hunks | FAIL | YO        |
| 17 | 3 files, 2 unrelated concerns, 5 hunks with churn ratio >50%, 180 lines total | FAIL |           |
| 18 | 7 files, 250 lines changed, every hunk has interleaved field renames, churn ratio ~75% | FAIL |           |
| 19 | 1 file, 1 hunk, 90 lines changed (80% adds / 20% removes interleaved, exceeds max_hunk_lines) | FAIL |           |
| 20 | 4 files, 480 lines changed (96% of limit), churn ratio 55%, 5 problematic hunks (exceeds max) | FAIL |           |
