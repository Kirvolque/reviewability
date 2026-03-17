# Overall Scoring — Formula Explanation

```
score = max(0, 1 − effective_size_ratio × (1 + scatter_factor))
```

## Components

**`effective_size_ratio`** = `min((lines_changed − moved_lines) / max_diff_lines, 1.0)`

Normalizes effective diff size to [0.0, 1.0]. Lines identified as code movements are
subtracted — relocations are easy to review and should not penalize the score. At zero
effective lines it's 0.0 (no penalty); at the configured size limit it's 1.0 (full penalty).
`min(..., 1.0)` clamps the value so an oversized diff doesn't push the score below zero.

**`scatter_factor`** = normalized Shannon entropy of change distribution across files

Measures how evenly changes are spread across files. `0.0` means all changes are in a
single file — the reviewer has one focused location to examine. `1.0` means changes are
evenly distributed across many files, forcing the reviewer to context-switch between
unrelated areas.

## Why each part

**Why `(1 + scatter_factor)`**

The `1` is the baseline: even a perfectly focused diff (scatter = 0) still incurs a size
penalty proportional to `effective_size_ratio`. Adding `scatter_factor` scales that penalty
up when changes are spread across many files. At scatter = 0 the multiplier is 1.0;
at scatter = 1 it is 2.0.

**Why multiply `effective_size_ratio × (1 + scatter_factor)`**

Neither factor alone is sufficient. A large but focused diff (e.g. a single large file
change) is tolerable. A scattered but small diff is also tolerable. The product penalizes
only when *both* are true — large *and* scattered — which is when review becomes
genuinely hard.

**Why `1 − ...`**

Flips the penalty into a score: zero penalty → 1.0 (easiest to review), maximum
penalty → 0.0 (hardest to review).
