# B5 — confirmed findings for the fixer (reviewer 1, reproducers in reviews/B5_r1.md; reviewer 2 found no further defect)

Only PRECONDITION items are to be edited.
1. `def:classification_table_precond`: the sum of y kept in α (R-F2I, `n1`) is unbounded. With
   y = [2^54, 1.0, 0.0], x = [[1.0]]*3, pd = [0.3, 0.5, 0.7] the precondition holds, Python runs,
   and 6 of 12 columns differ (Python's exact ints vs Float rounding of `3 - 2^54`); with
   y = [1e19, 1, 0] Python raises TypeError (Int64 overflow). Fix: add a bound on `n1`
   (`Np.sum y`) and on the number of rows: `|n1| ≤ 2^52` stated in α (as `_hl_groups_precond`
   does), with a `-- narrowing:` comment.
2. `def:hosmer_lemeshow_precond`: same gap per group: y = [1e19, 0.0, 1.0], pd = [0.3, 0.4, 0.5]
   raises TypeError in Python while the precondition holds; y = [2^53 + 2] gives a
   NoneventsObserved that differs as an integer. Fix: `|o1| ≤ 2^52` for every group, narrowing
   comment.
3. Narrowing comments (RULEBOOK §4) on the exclusions on which Python runs:
   `hosmer_lemeshow_precond` excludes String Series; `classification_table_precond` requires pd of
   the length of y (numpy broadcasts a length-1 pd) and `1 - h ≠ 0` — only if the edit keeps the
   Prop unchanged.
After the edits re-submit unchanged every precondition that was cleared because it depends on an
edited one (the train run's step preconditions may include these), and confirm with `get_status`.
