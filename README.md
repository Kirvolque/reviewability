# reviewability

A tool that scores the reviewability of code changes.

![code review bottleneck](img/code-review-bottleneck.png)

*It doesn't matter how fast AI generates code — the bottleneck is the human reviewer.*

## The Idea

A diff can be hard to review not because the code is poorly written, but because of
how the changes are combined. Mixing renames, movements, and logic changes in one diff
makes each harder to verify. This is especially common with AI-generated code. Unlike
linters, Reviewability does not analyze the code — only how the changes are structured.

When a diff scores low, the typical remedies are splitting it into focused pull
requests or deferring non-essential changes.

Reviewability computes metrics at the level of individual hunks, files, and the whole diff,
feeding into **Reviewability Scores** (0.0 = hardest, 1.0 = easiest) with
configurable thresholds for what counts as problematic.

## Key Concepts

- **Hunk** — a contiguous block of changes within a single file (the smallest unit of analysis)
- **Metric** — a calculated value attached to a hunk, a file, or the whole diff
- **Score** — a float [0.0, 1.0] representing reviewability at hunk, file, or diff level

## Extensibility

The metric system is designed to be extended:

- **Add a metric** — subclass `HunkMetric`, `FileMetric`, or `OverallMetric`, implement `calculate()`, register via `registry.add()`
- **Adjust scoring** — provide a custom `ReviewabilityScorer` implementation
- **Adjust thresholds** — edit `reviewability.toml` to change what score counts as problematic and what limits trigger violations

## Usage

```bash
# Analyze a range of commits
reviewability HEAD~1 HEAD

# Analyze from stdin
git diff HEAD~1 | reviewability --from-stdin

# Use a custom config
reviewability --config path/to/reviewability.toml HEAD~1 HEAD

# Include per-file and per-hunk breakdowns
reviewability --detailed HEAD~1 HEAD
```

Output is JSON. Exit code is `0` if the gate passes, `1` if it fails.

## Claude Code Skill

If you use [Claude Code](https://claude.ai/code), a `/reviewability` skill is included.
It runs the tool on the current diff, summarizes the results, and attempts to address
any recommendations directly.

## Movement Detection

Moved code is easy to review — the logic hasn't changed, only the location. The tool detects
when a block of code is deleted from one place and inserted elsewhere (accounting for
reindentation and package/import changes), and treats those hunks and files as relocations.

Relocations receive a perfect score and are excluded from the size and churn calculations
that drive the overall score. A diff that is large only because of relocations is not penalized.

## Metrics

Metrics are calculated at three levels: hunk, file, and overall diff.

### Hunk-level

| Metric | Description |
|--------|-------------|
| `hunk.lines_changed` | Total lines added and removed in a hunk |
| `hunk.added_lines` | Lines added in a hunk |
| `hunk.removed_lines` | Lines removed in a hunk |
| `hunk.context_lines` | Unchanged context lines surrounding the change |
| `hunk.churn_ratio` | Ratio of added lines to total changed lines (0.0 = pure deletion, 1.0 = pure addition) |
| `hunk.is_likely_moved` | Whether this hunk is a movement of code from another location |

### File-level

| Metric | Description |
|--------|-------------|
| `file.lines_changed` | Total lines added and removed across all hunks in a file |
| `file.added_lines` | Total lines added in a file |
| `file.removed_lines` | Total lines removed in a file |
| `file.hunk_count` | Number of separate change regions in a file |
| `file.max_hunk_lines` | Lines changed in the largest single hunk within a file |
| `file.is_likely_moved` | Whether this file is a movement from another path |

### Overall-level

| Metric | Description |
|--------|-------------|
| `overall.lines_changed` | Total lines changed across the entire diff |
| `overall.added_lines` | Total lines added across the entire diff |
| `overall.removed_lines` | Total lines removed across the entire diff |
| `overall.files_changed` | Number of files changed |
| `overall.moved_lines` | Total lines in hunks identified as code movements |
| `overall.change_entropy` | Shannon entropy of the distribution of changes across files |
| `overall.largest_file_ratio` | Fraction of total diff lines in the most-changed file |
| `overall.churn_complexity` | Average interleaving of adds and removes across hunks |
| `overall.problematic_hunk_count` | Hunks with a score below the configured threshold |
| `overall.problematic_file_count` | Files with a score below the configured threshold |

## Overall Scoring

The overall score is driven by two factors: **diff size** and **churn complexity**.

A larger diff is harder to review. A diff where adds and removes are interleaved within the
same hunks is harder to review than one where they are separated. The score penalizes both —
but only when they occur together. A large but directional diff (e.g. a bulk rename) scores
well. A small but tangled diff also scores well. The worst score comes from a diff that is
both large *and* internally mixed.

## Research

Metrics are grounded in peer-reviewed research on code review effectiveness:

- Jureczko et al. — *Code review effectiveness: an empirical study on selected factors influence* (IET Software, 2021)
  https://doi.org/10.1049/iet-sen.2020.0134

- McIntosh et al. — *An Empirical Study of the Impact of Modern Code Review Practices on Software Quality* (EMSE, 2015)
  https://doi.org/10.1007/s10664-015-9381-9

- Fregnan et al. — *First Come First Served: The Impact of File Position on Code Review* (EMSE, 2022)
  https://doi.org/10.1007/s10664-021-10034-0

- Uchôa et al. — *Predicting Design Impactful Changes in Modern Code Review* (MSR, 2020)
  https://doi.org/10.1145/3379597.3387480

- Baum et al. — *The Choice of Code Review Process: A Survey on the State of the Practice* (EMSE, 2019)
  https://doi.org/10.1007/s10664-018-9657-6

- Hijazi et al. — *Using Biometric Data to Measure Code Review Quality* (TSE, 2021)
  https://doi.org/10.1109/TSE.2020.2992169

- Olewicki et al. — *Towards Better Code Reviews: Using Mutation Testing to Prioritise Code Changes* (2024)
  https://arxiv.org/abs/2402.01860

- Barnett et al. — *Helping Developers Help Themselves: Automatic Decomposition of Code Review Changesets* (ICSE, 2015)
  https://doi.org/10.1109/ICSE.2015.35

- Brito & Valente — *RAID — Refactoring-Aware and Intelligent Diffs* (2021)
  https://doi.org/10.1109/ICSME52107.2021.00037

- Hu & Pradel — *CodeMapper: Mapping and Analyzing Code Changes across Commits* (ICSE, 2026)
