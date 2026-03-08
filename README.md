# reviewability

A tool that scores the reviewability of code changes.

## The Idea

Not all diffs are equally hard to review. Research shows that what makes
a diff difficult is not just its size, but the **nature and mix of changes**
it contains. A large rename-only PR can be trivial to review, while a small
PR that mixes a logic change with a refactor can be surprisingly hard.

This tool analyzes code diffs and computes metrics that approximate review
difficulty — at the level of individual hunks, files, or an entire diff.
These metrics feed into **Reviewability Scores** (0.0 = hardest, 1.0 = easiest)
with configurable thresholds for what counts as problematic.

## Key Concepts

- **Hunk** — a contiguous block of changes within a single file (the smallest unit of analysis)
- **Metric** — a calculated value attached to a hunk, a file, or the whole diff
- **Score** — a float [0.0, 1.0] representing reviewability at hunk, file, or diff level

## Extensibility

The metric system is designed to be extended:

- **Add a metric** — subclass `HunkMetric`, `FileMetric`, or `OverallMetric`, implement `calculate()`, register via `registry.add()`
- **Adjust scoring** — provide a custom `ReviewabilityScorer` implementation, or tune the weights in `WeightedReviewabilityScorer`
- **Adjust thresholds** — edit `reviewability.toml` to change what score counts as problematic and what limits trigger violations

## Usage

```bash
# Analyze a range of commits
reviewability HEAD~1 HEAD

# Analyze from stdin
git diff HEAD~1 | reviewability --from-stdin

# Use a custom config
reviewability --config path/to/reviewability.toml HEAD~1 HEAD
```

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
