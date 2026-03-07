# Suggested Metrics — Research-Backed

Metrics computable from a unified diff only. Excludes eye-tracking,
reviewer vote history, and other process data unavailable at diff time.
Already-implemented metrics (hunk.lines_changed, file.lines_changed, etc.) are omitted.

---

## Hunk-level

### `hunk.context_lines`
Lines of unchanged context included in the hunk (lines starting with ` ` in the diff).

**Calculation:** `count of context lines in the hunk`

**Rationale:** More context lines indicate the hunk is surrounded by a denser
code region, which increases cognitive load for the reviewer to locate the actual change.

**Suggested rule:** warn if `hunk.context_lines > 10`

> "Larger and more complex code changes are associated with lower defect detection
> effectiveness, and code change ordering according to the six derived principles
> positively influences review performance."
> — `emse2019a.pdf` (Baum et al., EMSE 2019)

---

### `hunk.churn_ratio`
Ratio of added lines to total changed lines within a hunk. Measures whether a hunk
is balanced (refactor) or one-sided (pure addition or deletion).

**Calculation:** `added_lines / (added_lines + removed_lines)`, or `0.0` if both are zero

**Value type:** RATIO (0.0–1.0)

**Rationale:** A ratio near 0.0 (pure deletion) or 1.0 (pure addition) may indicate
an unbalanced change that is harder to reason about than a balanced edit.

**Suggested rule:** warn if `hunk.churn_ratio > 0.9` (nearly all additions — no cleanup)

> "The size of the initial patch and the new lines of code added are statistically
> significant factors in predicting the number of review changes."
> — `10664_2022_Article_10205.pdf` (Fregnan et al., EMSE 2022)

---

## File-level

### `file.added_lines`
Total lines added across all hunks in a file.

**Calculation:** `sum of hunk.added_lines for all hunks in the file`

**Suggested rule:** warn if `file.added_lines > 300`

> "Size-based features (lines added, lines removed, file size, full patch size)
> are among the most predictive features for identifying files that will receive
> review comments."
> — `2404.10703v2.pdf` (Olewicki et al.)

---

### `file.removed_lines`
Total lines removed across all hunks in a file.

**Calculation:** `sum of hunk.removed_lines for all hunks in the file`

**Suggested rule:** warn if `file.removed_lines > 300`

> "Size-based features (lines added, lines removed, file size, full patch size)
> are among the most predictive features for identifying files that will receive
> review comments."
> — `2404.10703v2.pdf` (Olewicki et al.)

---

### `file.max_hunk_lines`
The size (lines changed) of the largest hunk in the file.

**Calculation:** `max(hunk.added_lines + hunk.removed_lines for all hunks in file)`

**Rationale:** Even if total file churn is acceptable, a single very large hunk is hard
to review in isolation. This metric identifies files with locally concentrated changes.

**Suggested rule:** warn if `file.max_hunk_lines > 50`

> "The inspection rate should be no greater than 200 LOC per hour... best practices
> suggest reviewing no more than 400 lines of code per session."
> — `IET Software - 2021 - Jureczko - Code review effectiveness...pdf` (Jureczko et al., citing Kemerer & Paulk)

---

## Overall-level

### `overall.added_lines`
Total lines added across the entire diff.

**Calculation:** `sum of hunk.added_lines for all hunks`

**Suggested rule:** error if `overall.added_lines > 400`

> "Best practices suggest reviewing no more than 400 lines of code per session
> to maintain reviewer effectiveness."
> — `1805.10978v2.pdf`, `TSE3158543.pdf`, `09733211.pdf` (Hijazi et al.)

---

### `overall.removed_lines`
Total lines removed across the entire diff.

**Calculation:** `sum of hunk.removed_lines for all hunks`

**Suggested rule:** warn if `overall.removed_lines > 200`

> "Patch Churn: the number of lines added and removed to the code during a review."
> — `UchoaCWPRAC20.pdf` (Uchôa et al.)

---

### `overall.change_entropy`
Shannon entropy of the distribution of changes across files. Measures how evenly
or unevenly the diff is spread. High entropy = changes scattered across many files.
Low entropy = changes concentrated in few files.

**Calculation:**
```
p_i = file_i.lines_changed / overall.lines_changed   (for each changed file)
H   = -sum(p_i * log2(p_i))                          (for all files where p_i > 0)
```

**Value type:** FLOAT (≥ 0.0; max = log2(number_of_files))

**Rationale:** Scattered changes across many files are harder to review coherently
than concentrated changes. High entropy diffs require the reviewer to maintain more
context simultaneously.

**Suggested rule:** warn if `overall.change_entropy > 3.0` (≈8+ files with equal spread)

> "Change entropy captures the degree of scattering of changes across the files
> in a component. Components with higher change entropy tend to have more
> post-release defects."
> — `EMSE2015_AnEmpiricalStudyOfTheImpactOfModernCodeReviewPracticesOnSoftwareQuality.pdf`,
>   `emse2016_mcintosh.pdf` (McIntosh et al.)

---

### `overall.largest_file_ratio`
Fraction of total diff lines concentrated in the single most-changed file.
A high ratio means one file dominates the diff; a low ratio means changes are spread.

**Calculation:**
```
max_file_lines = max(file.lines_changed for all files)
ratio          = max_file_lines / overall.lines_changed
```

**Value type:** RATIO (0.0–1.0)

**Rationale:** Complements change_entropy — a diff where one file holds 90% of
the changes may be easier to review than a scattered diff of the same size, but
also signals a monolithic change that may be difficult to decompose mentally.

**Suggested rule:** warn if `overall.largest_file_ratio < 0.2` (no dominant file
AND many files — combined with high entropy, this is the worst case)

> "Changesets affecting more than 10 files are connected with very low reviewing
> effectiveness, and both comment density and reviewers' decisions are
> disproportionately low."
> — `IET Software - 2021 - Jureczko - Code review effectiveness...pdf` (Jureczko et al.)

---

## Rules not tied to new metrics (thresholds on existing metrics)

| Rule | Metric | Operator | Threshold | Severity | Source |
|------|--------|----------|-----------|----------|--------|
| Too many files changed | `overall.files_changed` | `gt` | `10` | ERROR | Jureczko et al. |
| Diff exceeds session limit | `overall.lines_changed` | `gt` | `400` | ERROR | Hijazi et al. / SmartBear |
| Large single hunk | `hunk.lines_changed` | `gt` | `50` | WARNING | Jureczko et al. |
| High total additions | `overall.added_lines` | `gt` | `400` | ERROR | Hijazi et al. |
