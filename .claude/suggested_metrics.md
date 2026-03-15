# Suggested Metrics — Research-Backed

Metrics computable from a unified diff only. Excludes eye-tracking,
reviewer vote history, and other process data unavailable at diff time.

---

## Hunk-level

### `hunk.context_lines`

Lines of unchanged context included in the hunk (lines starting with ` ` in the diff).

**Calculation:** `count of context lines in the hunk`

**Rationale:** More context lines indicate the hunk is surrounded by a denser
code region, which increases cognitive load for the reviewer to locate the actual change.

**Suggested rule:** warn if `hunk.context_lines > 10`

| | |
|---|---|
| **Source** | Baum et al., *Associating Working Memory Capacity and Code Change Ordering with Code Review Performance* (EMSE 2019) — https://doi.org/10.1007/s10664-018-9657-6 |
| **Proof** | "effectiveness of reviews is significantly larger" |
| **Implemented** | Yes |

---

### `hunk.churn_ratio`

Ratio of added lines to total changed lines within a hunk. Measures whether a hunk
is directional (pure additions or pure deletions) or interleaved (mixed adds and removes).

**Calculation:** `added_lines / (added_lines + removed_lines)`, or `0.0` if both are zero

**Value type:** RATIO (0.0–1.0)

**Rationale:** A ratio near 0.0 (pure deletion) or 1.0 (pure addition) is easier to
review — the change moves clearly in one direction. A ratio near 0.5 means additions and
removals are interleaved, forcing the reviewer to track both simultaneously. Used as input
to `overall.churn_complexity`.

**Suggested rule:** warn if `hunk.churn_ratio` is near 0.5 and the hunk is large

| | |
|---|---|
| **Source** | Uchôa et al., *Predicting Design Impactful Changes in Modern Code Review* (MSR 2021) — https://doi.org/10.1145/3379597.3387480 |
| **Proof** | "CHURN presented statistically significant results" |
| **Implemented** | Yes |

---

### `hunk.move_distance`

For hunks identified as moved code, the distance (in lines) between the source
location and the destination within the same file.

**Calculation:** For intra-file moves: `|source_start_line - target_start_line|`.
For cross-file moves: not applicable.

**Value type:** INTEGER (≥ 0)

**Rationale:** A block moved a few lines away is trivial to verify. A block moved
hundreds of lines or across files requires more effort to confirm the content is unchanged.

**Suggested rule:** informational — no warning needed, but useful as scoring input

| | |
|---|---|
| **Source** | Hu & Pradel, *CodeMapper: Mapping and Analyzing Code Changes across Commits* (ICSE 2026) — https://arxiv.org/abs/2511.05205 |
| **Proof** | "cut-and-pasted to another location" |
| **Implemented** | No |

---

## File-level

### `file.added_lines`

Total lines added across all hunks in a file.

**Calculation:** `sum of hunk.added_lines for all hunks in the file`

**Suggested rule:** warn if `file.added_lines > 300`

| | |
|---|---|
| **Source** | Fregnan et al., *First Come First Served: The Impact of File Position on Code Review* (EMSE 2022) — https://doi.org/10.1007/s10664-021-10034-0 |
| **Proof** | "the lines added in a file" |
| **Implemented** | Yes |

---

### `file.removed_lines`

Total lines removed across all hunks in a file.

**Calculation:** `sum of hunk.removed_lines for all hunks in the file`

**Suggested rule:** warn if `file.removed_lines > 300`

| | |
|---|---|
| **Source** | Fregnan et al., *First Come First Served: The Impact of File Position on Code Review* (EMSE 2022) — https://doi.org/10.1007/s10664-021-10034-0 |
| **Proof** | "the lines added in a file" |
| **Implemented** | Yes |

---

### `file.max_hunk_lines`

The size (lines changed) of the largest hunk in the file.

**Calculation:** `max(hunk.added_lines + hunk.removed_lines for all hunks in file)`

**Rationale:** Even if total file churn is acceptable, a single very large hunk is hard
to review in isolation.

**Suggested rule:** warn if `file.max_hunk_lines > 50`

| | |
|---|---|
| **Source** | Jureczko et al., *Code review effectiveness: an empirical study on selected factors influence* (IET Software 2021) — https://doi.org/10.1049/iet-sen.2020.0134 |
| **Proof** | "A review rate of 200 LOC/h" |
| **Implemented** | Yes |

---

### `file.hunk_spread`

The span (in lines of the original file) between the first and last hunk in a file,
relative to the file's total changed lines. Measures how scattered changes are within
a single file.

**Calculation:**
```
span   = last_hunk.source_start - first_hunk.source_start + last_hunk.source_length
spread = span / file.lines_changed
```

**Value type:** FLOAT (≥ 1.0; higher = more scattered)

**Rationale:** Concentrated changes let the reviewer focus attention. Scattered changes
across a large file force the reviewer to jump between distant locations.

**Suggested rule:** warn if `file.hunk_spread > 20`

| | |
|---|---|
| **Source** | Fregnan et al., *First Come First Served: The Impact of File Position on Code Review* (EMSE 2022) — https://doi.org/10.1007/s10664-021-10034-0 |
| **Proof** | "the lines added in a file" |
| **Implemented** | No |

---

## Overall-level

### `overall.added_lines`

Total lines added across the entire diff.

**Calculation:** `sum of hunk.added_lines for all hunks`

**Suggested rule:** error if `overall.added_lines > 400`

| | |
|---|---|
| **Source** | Jureczko et al., *Code review effectiveness: an empirical study on selected factors influence* (IET Software 2021) — https://doi.org/10.1049/iet-sen.2020.0134 |
| **Proof** | "A review rate of 200 LOC/h" |
| **Implemented** | Yes |

---

### `overall.removed_lines`

Total lines removed across the entire diff.

**Calculation:** `sum of hunk.removed_lines for all hunks`

**Suggested rule:** warn if `overall.removed_lines > 200`

| | |
|---|---|
| **Source** | Uchôa et al., *Predicting Design Impactful Changes in Modern Code Review* (MSR 2021) — https://doi.org/10.1145/3379597.3387480 |
| **Proof** | "CHURN presented statistically significant results" |
| **Implemented** | Yes |

---

### `overall.change_entropy`

Shannon entropy of the distribution of changes across files. High entropy = changes
scattered across many files. Low entropy = changes concentrated in few files.

**Calculation:**
```
p_i = file_i.lines_changed / overall.lines_changed
H   = -sum(p_i * log2(p_i))
```

**Value type:** FLOAT (≥ 0.0; max = log2(number_of_files))

**Rationale:** Scattered changes across many files require the reviewer to maintain more
context simultaneously.

**Suggested rule:** warn if `overall.change_entropy > 3.0`

| | |
|---|---|
| **Source** | McIntosh et al., *An Empirical Study of the Impact of Modern Code Review Practices on Software Quality* (EMSE 2016) — https://doi.org/10.1007/s10664-015-9381-9 |
| **Proof** | "poorly-reviewed code has a negative impact" |
| **Implemented** | Yes |

---

### `overall.largest_file_ratio`

Fraction of total diff lines concentrated in the single most-changed file.

**Calculation:**
```
max_file_lines = max(file.lines_changed for all files)
ratio          = max_file_lines / overall.lines_changed
```

**Value type:** RATIO (0.0–1.0)

**Suggested rule:** warn if `overall.largest_file_ratio < 0.2`

| | |
|---|---|
| **Source** | Jureczko et al., *Code review effectiveness: an empirical study on selected factors influence* (IET Software 2021) — https://doi.org/10.1049/iet-sen.2020.0134 |
| **Proof** | "A review rate of 200 LOC/h" |
| **Implemented** | Yes |

---

### `overall.churn_complexity`

Average interleaving complexity across all hunks. Measures how much the diff mixes
additions and deletions rather than making directional changes.

**Calculation:**
```
mix_i = 1 − |2 × hunk.churn_ratio_i − 1|   (0.0 = directional, 1.0 = fully interleaved)
overall.churn_complexity = mean(mix_i)
```

**Value type:** RATIO (0.0–1.0)

**Suggested rule:** warn if `overall.churn_complexity > 0.7` combined with large diff size

| | |
|---|---|
| **Source** | Uchôa et al., *Predicting Design Impactful Changes in Modern Code Review* (MSR 2021) — https://doi.org/10.1145/3379597.3387480 |
| **Proof** | "CHURN presented statistically significant results" |
| **Implemented** | Yes |

---

### `overall.independent_partition_count`

Number of logically independent groups of changes within a single diff. Higher counts
suggest the changeset mixes multiple unrelated concerns.

**Calculation:** Build a dependency graph between changed regions. Count connected
components. A diff with one connected component is cohesive; multiple components
indicate tangled changes.

**Value type:** INTEGER (≥ 1)

**Rationale:** At Microsoft, 40% of changesets could be automatically decomposed into
independent partitions, and reviewers strongly preferred the decomposed versions.

**Suggested rule:** warn if `overall.independent_partition_count > 2`

**Implementation note:** Requires static analysis beyond a unified diff. Could be
approximated by clustering hunks that share modified identifiers.

| | |
|---|---|
| **Source** | Barnett et al., *Helping Developers Help Themselves: Automatic Decomposition of Code Review Changesets* (ICSE 2015) — https://doi.org/10.1109/ICSE.2015.35 |
| **Proof** | "over 40% of changes submitted for review" |
| **Implemented** | No |

---

### `overall.tangled_change_ratio`

Fraction of changed hunks that belong to more than one logical concern.

**Calculation:**
```
tangled_hunks = count of hunks that appear in more than one independent partition
ratio = tangled_hunks / total_hunks
```

**Value type:** RATIO (0.0–1.0)

**Suggested rule:** warn if `overall.tangled_change_ratio > 0.3`

**Implementation note:** Same dependency as `overall.independent_partition_count`.

| | |
|---|---|
| **Source** | Barnett et al., *Helping Developers Help Themselves: Automatic Decomposition of Code Review Changesets* (ICSE 2015) — https://doi.org/10.1109/ICSE.2015.35 |
| **Proof** | "over 40% of changes submitted for review" |
| **Implemented** | No |

---

### `overall.diff_code_churn`

Fraction of changed lines attributable to mechanical refactorings (moves, renames,
extract method) rather than behavioral changes.

**Calculation:**
```
refactoring_lines = sum of lines attributable to detected refactoring operations
diff_code_churn   = refactoring_lines / overall.lines_changed
```

**Value type:** RATIO (0.0–1.0)

**Rationale:** A simple move-method refactoring that changes 0 lines of logic can
produce hundreds of diff lines. Reviewers waste effort on mechanical changes.

**Suggested rule:** informational — report the ratio so reviewers know how much is mechanical

**Implementation note:** Our `MovementDetector` already handles move detection.
This metric would generalize it to other refactoring types.

| | |
|---|---|
| **Source** | Brito & Valente, *RAID — Refactoring-Aware and Intelligent Diffs* (ICPC 2021) — https://arxiv.org/abs/2103.11453 |
| **Proof** | "decreases from 14.5 to 2 lines" |
| **Implemented** | No |

---

### `overall.cross_file_move_count`

Number of code blocks deleted from one file and inserted into a different file.

**Calculation:** `count of (source_hunk, target_hunk) pairs where source and target
are in different files and content similarity > threshold`

**Value type:** INTEGER (≥ 0)

**Suggested rule:** informational if `overall.cross_file_move_count > 0`

| | |
|---|---|
| **Source** | Hu & Pradel, *CodeMapper: Mapping and Analyzing Code Changes across Commits* (ICSE 2026) — https://arxiv.org/abs/2511.05205 |
| **Proof** | "Lines are moved inside or outside a structural unit" |
| **Implemented** | No |

---

## Rules not tied to new metrics

| Rule | Metric | Operator | Threshold | Severity | Source |
|---|---|---|---|---|---|
| Too many files changed | `overall.files_changed` | `gt` | `10` | ERROR | Jureczko et al. |
| Diff exceeds session limit | `overall.lines_changed` | `gt` | `400` | ERROR | Jureczko et al. |
| Large single hunk | `hunk.lines_changed` | `gt` | `50` | WARNING | Jureczko et al. |
| High total additions | `overall.added_lines` | `gt` | `400` | ERROR | Jureczko et al. |
