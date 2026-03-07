# Cognitive Load in Code Review and Diff Analysis

## Goal

Understand which characteristics of code diffs (e.g., Git pull requests)
influence the **cognitive load during code review**, and identify
**metrics that can approximate review difficulty**.

------------------------------------------------------------------------

# 1. Research Areas Related to Diff Cognitive Load

## Patch Size

Commonly studied metric in code review research.

Key metrics: - Lines Added - Lines Deleted - Lines Modified - Total
churn

Example:

PatchSize = added_lines + deleted_lines

Also used: - Files changed - Number of diff hunks

Finding: larger patches reduce review effectiveness.

Key references: - McIntosh et al. (2014) - Bacchelli & Bird (2013)

------------------------------------------------------------------------

## Change Decomposition (Tangled Commits)

Research shows that mixing multiple concerns increases review
difficulty.

Example concerns: - Logic change - Rename - Refactor - Move

Metric:

ConcernCount(commit)

Example:

  PR                      ConcernCount   Review difficulty
  ----------------------- -------------- -------------------
  rename + move           1              low
  logic + rename + move   3              high

Reference: - di Biase et al., *The Effects of Change Decomposition on
Code Review*

------------------------------------------------------------------------

## Change Entropy

Measures how scattered the changes are across files.

Formula:

Entropy = - Σ(p_i \* log2(p_i))

Where:

p_i = proportion of changes in file i

Interpretation:

-   Low entropy → localized changes
-   High entropy → scattered changes

Reference: - Hassan (2009)

------------------------------------------------------------------------

## Structural Change Metrics (AST)

Measures structural edits instead of textual edits.

Examples:

-   AST edit distance
-   Number of AST nodes modified
-   Control flow changes
-   Method signature changes

Observation:

  Change Type    AST Impact
  -------------- ------------
  rename         very low
  move           very low
  logic change   high

Thus logic changes increase cognitive load more than simple refactors.

------------------------------------------------------------------------

## Semantic Change Metrics

Some metrics try to capture **behavioral changes**.

Examples:

-   changed conditions
-   changed return values
-   changed method calls
-   changed control flow

These are typically associated with higher review difficulty.

------------------------------------------------------------------------

## Change Coupling / Dependency Impact

Measures how system dependencies change.

Examples:

-   DependencyEdgesChanged
-   CallGraphImpact
-   FanInDelta
-   FanOutDelta

Logic changes often affect dependency structure.

------------------------------------------------------------------------

## Diff Hunk Metrics

Metrics describing the structure of diff segments.

Examples:

-   NumberOfHunks
-   AverageHunkSize
-   MaxHunkSize

Observation: - Many small hunks often increase review difficulty.

------------------------------------------------------------------------

# 2. Cognitive Effort Metrics

## NRevisit Metric

Proposed as a proxy for cognitive load.

Definition:

NRevisit = number of times a developer revisits a code region

Measured via: - eye tracking - navigation logs

Higher revisit counts correlate with higher cognitive load.

------------------------------------------------------------------------

# 3. Important Observations from Research

### Size Alone Is Not Enough

Example comparison:

PR A: - rename - move - very large

PR B: - logic change - rename - move - smaller

PR B is usually harder to review because multiple concerns are mixed.

------------------------------------------------------------------------

### Refactoring + Logic Change Is Problematic

Research repeatedly observes:

Review difficulty increases when **behavioral changes are mixed with
refactoring changes**.

This is known as:

Tangled commits

------------------------------------------------------------------------

# 4. Metrics That Best Capture Review Difficulty

A useful minimal metric set:

-   ConcernCount
-   ASTEditDistance
-   ChangeEntropy
-   DependencyImpact

Example comparison:

## PR1 (rename + move)

ConcernCount = 1\
ASTEditDistance = low\
Entropy = low\
DependencyImpact = low

Review difficulty: low

## PR2 (logic + rename + move)

ConcernCount = 3\
ASTEditDistance = high\
Entropy = medium/high\
DependencyImpact = medium

Review difficulty: high

------------------------------------------------------------------------

# 5. Practical Insight

The most important factors affecting review cognitive load are:

1.  Number of concerns in a change
2.  Structural complexity of the edits
3.  Change distribution across files
4.  Dependency impact
5.  Patch size

However, **edit heterogeneity (mixing change types)** is often more
important than diff size.

------------------------------------------------------------------------

# 6. Key Search Keywords

Useful queries for literature:

-   code review cognitive load
-   modern code review empirical study
-   tangled commits code review
-   patch size code review effectiveness
-   delocalized changes code review
-   program comprehension cognitive load developers

------------------------------------------------------------------------
