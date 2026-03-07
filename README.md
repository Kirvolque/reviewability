# reviewability

A tool for measuring the cognitive load of code reviews.

## The Idea

Not all diffs are equally hard to review. Research shows that what makes
a diff difficult is not just its size, but the **nature and mix of changes**
it contains. A large rename-only PR can be trivial to review, while a small
PR that mixes a logic change with a refactor can be surprisingly hard.

This tool analyzes code diffs and computes metrics that approximate review
difficulty — at the level of individual hunks, files, or an entire diff.
These metrics can then be compared against configurable thresholds to
produce warnings or fail a CI check.

## Key Concepts

- **Hunk** — a contiguous block of changes within a single file (the smallest unit of analysis)
- **Metric** — a calculated value attached to a hunk, a file, or the whole diff
- **Rule** — a threshold applied to a metric, producing a warning or error
