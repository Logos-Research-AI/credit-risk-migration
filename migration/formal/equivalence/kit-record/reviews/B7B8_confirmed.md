# B7 / B8 — confirmed findings for the fixer (reviewer 1, each with a reproducer in reviews/B7B8_r1.md)

Only PRECONDITION items are to be edited. Do not edit any unit (`def:fe_run_*`, `def:predict_run_*`,
`def:run`, `def:run_py_py`): they are being evaluated by a reviewer right now.

1. Join suffix clash (feature_engineering.py:94-96, predict.py:99-101): polars raises
   DuplicateError when a right column renamed to `<name>_right` meets an existing name; the Lean
   returns tables. Fix `def:fe_run_04_imputed_precond` and `def:predict_run_04_imputed_precond`:
   add that for every non-key column `c` of the right frame (`income_medians` /
   `test_income_medians`) whose name is already a column of the left frame, `c ++ "_right"` is
   neither a column of the left frame nor produced twice. Check `def:run_precond` and
   `def:run_py_py_precond` inherit it (they include the step preconditions on the computed
   frames); if they restate conditions instead, fix them too. For predict with
   `fix_train_medians = true` the right frame is `medians`, whose other columns are unconstrained.
2. `def:fe_run_04_imputed_precond`: state that `median_income` of the JOINED frame is Float64 (as
   `def:predict_run_04_imputed_precond` already does), so that a text column `median_income` of
   cs-training is excluded (Python raises InvalidOperationError at feature_engineering.py:157; on
   the step alone Python returns a String column where the Lean returns Float64).
3. Narrowing comments (RULEBOOK §4): add `-- narrowing: …` to the conjuncts that exclude inputs on
   which Python runs: `MonthlyIncome` (predict 02), `NumberOfDependents` (predict 03),
   `MonthlyIncome_missing` (predict 04), `pd_logistic` (predict 07), `MonthlyIncome_missing` /
   `Dependents_missing` (feature engineering 04) — only if you can do so without changing the
   Prop; a comment-only edit that the server rejects is to be reported, not forced.
After the edits: every precondition that depends on an edited one may be cleared: re-submit it
unchanged (`read_scratch` then `write_statement`) and confirm with `get_status` that nothing
accepted before is left unformalized. Reproduce findings 1 and 2 by evaluating the precondition's
new conjunct on the reviewer's input where practical (a Prop cannot be evaluated; evaluate the
Boolean expression it states), or argue from the text.
