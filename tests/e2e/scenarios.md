# E2E Test Scenarios

Proposed scenarios for end-to-end tests.
"Expected" reflects whether the diff shape is easy to review, not whether the code is correct.

Score formula: `score = max(0, 1 − size_ratio × (1 + complexity))`
where `complexity = (churn_complexity + scatter_factor) / 2`

Defaults: `max_diff_lines=500`, `max_hunk_lines=50`, `hunk_score_threshold=0.5`, `min_overall_score=0.5`

| # | Shape of changes | Driving factors | Expected | Need test? |
|---|-----------------|-----------------|----------|------------|
| 1 | 40% of size limit, 1 file, all pure additions — no churn, no scatter | size=0.4, complexity=0 → score=0.60 | PASS | Y          |
| 2 | 70% of size limit, 1 file, all pure additions — large but clean | size=0.7, complexity=0 → score=0.30 | PASS | Y          |
| 3 | 40% of size limit, high churn (interleaved adds/removes), 1 file | size=0.4, churn≈1.0 → score=0.20 | PASS | Y          |
| 4 | 40% of size limit, directional, spread equally across 10 files (max scatter) | size=0.4, scatter=1.0 → score=0.20 | PASS | Y          |
| 5 | 2 files, file A deleted + file B added with identical content (file-level move) — directional, small real changes | movements excluded from size; effective size small | PASS | N          |
| 6 | Large diff (120%+ of limit), most changes are file-level moves, small real changes remain | effective size ~5–10% after exclusion → score≈0.90 | PASS | Y (exists) |
| 7 | 50% of size limit, all hunks maximally interleaved (churn=1.0), 1 file | size=0.5, complexity=1.0 → score=0.00 | FAIL | Y          |
| 8 | 50% of size limit, directional changes, spread equally across 10 files (max scatter) | size=0.5, scatter=1.0 → score=0.25 | FAIL | Y          |
| 9 | 30% of size limit, all hunks interleaved (churn=1.0) AND spread across 8 files (scatter≈1.0) | size=0.3, complexity=1.0 → score=0.40 | FAIL | Y          |
| 10 | 40% of size limit, moderate churn (0.5) across 5 files (scatter≈0.8) | size=0.4, complexity≈0.65 → score=0.34 | FAIL | Y          |
| 11 | Large diff (>limit), mostly movements — but real changes still have high churn and scatter | effective size small, but complexity on real changes still kills score | FAIL | Y          |
| 12 | Large diff with some movements (50% of lines moved), remaining 50% still exceeds limit | effective size still above limit after exclusion | FAIL |            |
| 13 | Many files (scatter≈1.0), but total change is tiny (5% of size limit) | size=0.05 → even with max complexity: 0.05×2=0.10 → score=0.90 | PASS |            |
| 14 | Two entangled concerns in one diff: new feature (pure additions) + refactor (interleaved) across same files | churn from refactor + scatter from both concerns → complexity amplified | FAIL |            |
| 15 | Large hunk (exceeds max_hunk_lines), but overall diff is small and directional | hunk score low, but overall score unaffected if total lines small | PASS |            |
| 16 | Large diff (80% of limit), half is movements, half is interleaved real changes (churn=1.0, scatter=1.0) | effective size=40%, complexity=1.0 → score=0.20 | FAIL |            |
