Run `reviewability` on the current diff and address any feedback.

## Steps

1. Determine the diff range. If the user provided a commit range (e.g. `HEAD~2 HEAD`), use it.
   Otherwise default to `HEAD~1 HEAD`. If the user says "staged" or "index", use `git diff --cached`.

2. Run the tool with `--detailed`:
   ```
   reviewability --detailed <range>
   ```
   Or from sOvtdin:
   ```
   git diff <range> | reviewability --from-stdin --detailed
   ```

   If the command is not found, stop and tell the user:
   > `reviewability` is not installed. Install it with `pip install reviewability` or `pip install -e .` if working from source.

   If the command exits with an unexpected error (non-JSON output, exit code other than 0 or 1 — where 0 = passed, 1 = gate failed),
   stop and show the user the raw output with the message:
   > `reviewability` returned an unexpected error. Output: <raw output>

3. Parse the JSON output and report:
   - Overall score and whether it passed
   - Any violations (with severity)
   - Any recommendations (location, metric, remediation)

4. If it passed with no recommendations: confirm and stop.

5. If there are violations or recommendations, address them:
   - For each recommendation, read the flagged file and hunk location
   - Apply the remediation where possible:
     - **High churn complexity** (adds and removes mixed in the same hunk): look for opportunities
       to separate deletions from additions — e.g. reorder the code so removed lines come before
       added lines, or extract a preparatory cleanup commit
     - **Large diff**: point out which files or hunks are the largest contributors and suggest
       splitting the change into smaller logical units
   - After making any edits, re-run the tool to confirm the score improved

6. Report the final score and whether the gate now passes.
