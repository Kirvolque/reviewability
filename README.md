# reviewability

**A CI/CD quality gate that scores pull requests by how hard they are to review.**

Catch diffs that are too large, too tangled, or too scattered to review safely — before they merge.

![code review bottleneck](img/code-review-bottleneck.png)

*It doesn't matter how fast AI generates code — the bottleneck is the human reviewer.*

## Installation

```bash
pip install reviewability
```

Requires Python 3.12+.

## The Idea

A pull request can be hard to review not because the code is poorly written, but because of
how the changes are combined. Mixing renames, movements, and logic changes in one PR
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
- **Adjust thresholds** — edit the [default config](src/reviewability/config/reviewability.toml) or provide your own `reviewability.toml`

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

## Configuration

All thresholds and limits are configured via a single `reviewability.toml` file.
The tool looks for it in the current directory, or you can specify a path explicitly:

```bash
reviewability -c path/to/reviewability.toml HEAD~1 HEAD
```

If no config file is found, the
[built-in default](src/reviewability/config/reviewability.toml) is used. You can
edit that file directly to change the defaults, or copy it into your project root.
The config must contain all mandatory fields — there is no merging with defaults.

```toml
# Scores below these thresholds mark hunks/files as problematic
hunk_score_threshold = 0.5
file_score_threshold = 0.5

# Size limits (used for score normalisation)
max_diff_lines = 500
max_hunk_lines = 50

# Gate: fail if overall score drops below this (provisional, based on calibration)
min_overall_score = 0.7

# Optional limits (remove a line to disable that check)
max_problematic_hunks = 3
max_problematic_files = 2
max_file_hunk_count = 5
max_files_changed = 10
max_added_lines = 400

[movement_detection]
hunk_min_lines = 8
file_min_lines = 15
similarity_threshold = 0.95
```

## Movement Detection

Moved code is easy to review — the logic hasn't changed, only the location. The tool detects
when a block of code is deleted from one place and inserted elsewhere (accounting for
reindentation and package/import changes), and treats those hunks and files as relocations.

Relocations receive a perfect score and are excluded from the size calculations
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
| `hunk.change_balance` | Ratio of added lines to total changed lines (0.0 = pure deletion, 1.0 = pure addition) |
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
| `overall.scatter_factor` | Normalized entropy of how changes are distributed across files (0.0 = all in one file, 1.0 = evenly spread) |
| `overall.problematic_hunk_count` | Hunks with a score below the configured threshold |
| `overall.problematic_file_count` | Files with a score below the configured threshold |

## Overall Scoring

```
score = max(0, 1 − effective_size_ratio × (1 + scatter_factor))

effective_size_ratio = (lines_changed − moved_lines) / max_diff_lines   [capped at 1.0]
```

The score is driven by **effective diff size** and **scatter**. Moved lines are excluded
from the size count — relocations are easy to review and should not penalize the score.

`scatter_factor` measures how evenly changes are spread across files (normalized entropy,
0.0 = all in one file, 1.0 = evenly spread). It amplifies the size penalty: a large diff
that touches many files evenly scores worse than an equally large diff concentrated in
a few files.

A large but focused diff (e.g. a bulk rename in one file) or a scattered but small diff
each score better than a diff that is both large *and* scattered.

## Validation

The scoring formula was calibrated against ~2,000 pull requests from 15 permissively
licensed open-source repositories. Ground truth labels were derived from review outcomes
(change requests, revision cycles, comment density). Metrics that did not improve
prediction over a naive size baseline were removed from the formula.

## Research

Metrics are informed by peer-reviewed research on code review effectiveness. Most are heuristics derived from research concepts rather than direct paper-defined variables:

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
