# reviewability

A tool that scores the reviewability of code changes.

![code review bottleneck](img/code-review-bottleneck.png)

*It doesn't matter how fast AI generates code — the bottleneck is the human reviewer.*

## The Idea

A diff can be hard to review not because the code is poorly written, but because the
*intent* of the change is unclear from the diff itself. A block moved and
reindented looks like a wall of red and green even if nothing changed logically.
Unlike linters, it does not analyze the code — only the diff as a whole.

It computes metrics at the level of individual hunks, files, and the whole diff,
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

- McIntosh et al. — *The Impact of Code Review Coverage and Code Review Participation on Software Quality* (MSR, 2014)  
  https://doi.org/10.1145/2597073.2597076

- Fregnan et al. — First Come First Served: The Impact of File Position on Code Review (EMSE, 2022)
  https://doi.org/10.1007/s10664-021-10034-0

- Uchôa et al. — *Predicting Design Impactful Changes in Modern Code Review* (MSR, 2020)  
  https://doi.org/10.1145/3379597.3387480

- Baum et al. — *The Choice of Code Review Process: A Survey on the State of the Practice* (EMSE, 2019)  
  https://doi.org/10.1007/s10664-018-9657-6

- Hijazi et al. — *Using Biometric Data to Measure Code Review Quality* (TSE, 2021)  
  https://doi.org/10.1109/TSE.2020.2992169

- Olewicki et al. — *Towards Better Code Reviews: Using Mutation Testing to Prioritise Code Changes* (2024)  
  https://arxiv.org/abs/2402.01860
