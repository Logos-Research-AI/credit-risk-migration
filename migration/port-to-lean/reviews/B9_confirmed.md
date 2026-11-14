# B9 — confirmed findings for the fixer (reviewer 1, reproducers in reviews/B9_r1.md)

Only PRECONDITION items are to be edited (no unit).
1. `def:train_run_03_fit_global_rsquare_precond` (inherited by `def:run_py_py_py_precond`): the
   shapes of each step's fit are unconstrained beyond "beta 1-D, cov 2-D", but at train.py:193
   `np.linalg.solve(st.fit.cov[1:, 1:], b_slope)` raises ValueError / LinAlgError when `cov` is
   not square with as many rows as `beta` has entries (beta of length 3 with a 2x2 cov; beta of
   length 2 with a 3x3 cov; a 2x3 cov). Fix: for every step's fit, `cov` is square
   (every row has the length of the number of rows) with as many rows as `beta` has entries.
   Check whether the same shape condition is needed for the FINAL fit where it is used
   (train.py:311 `final.cov[idx, idx]`, step 06; classification_table's x_final vs final.names,
   step 08) and add it where a mismatch makes Python raise (IndexError) while the Lean returns a
   value; say what you verified.
2. Narrowing comments (RULEBOOK §4), comment-only: steps 03 and 06 `isFinite (exp …)` (also
   excludes NaN / +inf arguments on which `math.exp` does not raise); steps 03 and 08 "no null in
   every column a fit names"; step 04 `b.length = final.names.length`.
3. Frame wording (RULEBOOK §4): the preconditions of steps 05, 07, 13, 15 do not state distinct
   names and common height of the frames they take: add the fixed wording.
After the edits re-submit unchanged every precondition that was cleared because it depends on an
edited one, and confirm with `get_status` (146 formalized before you start).
