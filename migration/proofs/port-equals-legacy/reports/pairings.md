# Pairings: evaluation of both sides at Float

One section per group, written by the agent that ran the evaluations. Numbers were compared through `Float.toBits`. The temporary `zz_` carrier items used for these evaluations have been removed from the blueprint, so the evaluations cannot be re-run from it as it stands. Formal results (proved, disproved, not settled) are in `report.md`.

Evaluation limits: the edge scenarios were evaluated on prefixes or subsets only (metrics: the first 150 validation and 350 training rows of each of `edge_metrics_a/b/c`; predict: 33 of the 101,503 rows of `edge_predict`), because `eval_decl` takes inline terms.


---

# Group: Feature engineering (S1 to S6, ST1, F3, F4, I3, I4)

## Pairings by evaluation: feature engineering (S1 to S6, ST1, F3, F4, I3, I4)

Both sides evaluated at `Float` through the carrier `def:zz_fe` (blueprint `py-credit-risk-port`),
cells compared through `Float.toBits`. "agree" means bit-identical tables, including column names,
column order and row order. Python side: `Pl.toTable (python f)`. SAS side: `sas (Pl.toTable f)`.
Parameters: `input_best32` is the SAS conversion (`zz_fe_ib32`: `Sas.inputBest` of the text, all
missing on a non-text column); `arrange` is the identity; `credit_split` is the feature table with
`Selected = 1` exactly on the rows whose `row_id` is listed (`zz_fe_split`). "Domain" is `D_fe` of
section 2 of the specification. There is no edge scenario for this stage (`inputs/scenarios` and
`judge/scenarios` hold metrics and predict scenarios only).

Row notation below: S5 rows are `[age, monthly_income, num_dependents, late30, late60, late90,
credit_utilization, debt_ratio, num_credit_lines]`; raw rows are `[VAR1, SeriousDlqin2yrs,
utilization, age, late30, DebtRatio, lines, late90, real estate, late60], MonthlyIncome text,
NumberOfDependents text`.

### S1 `fe_run_01_clean` / `credit_raw_clean`

| Input | Outcome |
|---|---|
| text columns with `"5000"`, `"NA"`, `" 12.5 "`, missing, `""` | agree |
| `"-3"`, `"1e3"`, `"abc"`, `"."`, `"+.5"`, `"1."`, 32 digits, `"0.1"`, `"--1"`, `"1.5.2"`, blanks, `"007"`, with an extra integer column | agree |
| numeric (Float64) `MonthlyIncome` and `NumberOfDependents`, link as the SAS conversion | agree (both all missing) |
| columns `MonthlyIncome_num`, `NumberOfDependents_num` already present | agree |
| integer `NumberOfDependents` | agree |

No difference under the link. Outside the link: with an `input_best32` that keeps a numeric column
(what `sas_compat.input_best32` does), frame `MonthlyIncome = [5000, null]`,
`NumberOfDependents = [2, NaN]` (Float64): Python `5000, 2, NaN`, SAS missing, missing, missing.
This is a precondition pair, not a counterexample: the SAS precondition requires text columns.

### S2 `fe_run_02_income_medians` / `income_medians`

| Input (age, MonthlyIncome) | Outcome | Domain |
|---|---|---|
| (25,1000),(28,3000),(45,7),(45,9),(45,8),(65,5) | agree | on |
| **(45,1),(25,1)** | **differ: row order.** Python `[(3,1),(1,1)]` (first appearance), SAS `[(1,1),(3,1)]` (ascending). Equal up to row order | **on** |
| (25,1016.85),(26,7098.24),(27,0.1),(29,0.3) even count | agree | on |
| (25,1016.85)... through the pipeline: median 4057.545 = bits 4661141050889171107 on both sides | agree on the value | on |
| (missing,1) | differ: Python age_group 5, SAS 1 | outside (missing age) |
| (missing,1),(25,3) | differ: Python two rows (5,1),(1,3); SAS one row (1,2) | outside |
| (25,missing),(35,2),(36,missing); (25,missing) alone | agree (a group with no income has no row; empty table) | outside |
| (25,-1e308),(26,1e308) | differ: Python median `inf`, SAS missing (overflow of hi - lo) | on (Float only) |
| NaN income among 1, 2; NaN age | agree | - |
| (30,4),(29.999,2),(60,1),(1e308,1),(-5,8) | differ in row order only | on |
| (25,0.1),(26,0.7); subnormals 5e-324, 1.5e-323 | agree | on |

Smallest witness on the domain: ages 45, 25 with incomes 1, 1.

### S3 `fe_run_03_cleaned` / `credit_cleaned` (S3b is the pilot, already disproved)

| Input (age, MonthlyIncome, NumberOfDependents) | Outcome | Domain |
|---|---|---|
| ten rows: ages 25, 30, 39.5, 40, 50, 59, 60, 101, 0, -3, incomes and dependents present or missing | agree | on |
| (missing,1,0) | differ: Python age_group 5, SAS 1 | outside |
| NaN, +inf, -inf ages | agree | - |
| NaN income, NaN dependents, 1e308 income, dependents -1 | agree | - |
| output columns already present, in another order | agree | - |
| extra text, integer and Boolean columns | agree | - |

No difference on the domain.

### S4 `fe_run_04_imputed` / `credit_imputed` (arrange = identity)

| Input | Outcome | Domain |
|---|---|---|
| 3 rows, groups 1, 3, 1, two missing incomes, medians for 1 and 3 | agree, rows in the same order | on |
| the same with the medians table in the order 3, 1 | agree | on |
| a row of group 2 with missing income, medians for group 1 only; or an empty medians table | agree (monthly_income missing on both sides) | outside (group with no income) |
| utilization 1e308; DebtRatio -1e307; NaN; inf | differ: Python `inf` / `-inf` / NaN, SAS missing | on, Float only (overflow of `* 100`) |
| every cell missing, age_group null | agree | outside |
| age_group null on the left and a null key in the medians table | differ: Python monthly_income missing (null keys do not join), SAS 9 (missing equals missing) | outside |
| a duplicated key in the medians table | agree (same duplicated rows, same order) | - |
| **`credit_cleaned` has its own column `median_income` = 77; income missing, group 1, median 1000** | **differ: Python monthly_income 77, SAS 1000** | **on** (D_fe says nothing on extra columns) |
| flag 1 with a present income, flag 0 with a missing income, flag null, flag 2, extra columns on both sides | agree | - |

Smallest witness on the domain, real arithmetic too: one row, MonthlyIncome missing,
MonthlyIncome_missing = 1, age_group 1, an extra Float64 column `median_income = 77`, medians table
(1, 1000). After the polars join the right column is renamed `median_income_right`, so
`pl.col("median_income")` is the column of the left table; SAS reads `b.median_income`.

### S5 `fe_run_05_features` / `credit_features`

| Input | Outcome | Domain |
|---|---|---|
| 5 plain rows on every threshold, `full = true` and `full = false` | agree | on |
| late counts 0.1, 0.2, 0.3 | differ by one unit in the last place: total_late_payments Python 4603579539098121011 (a + (b + c)), SAS 4603579539098121012 ((a + b) + c) | on, Float only |
| late counts 1e308, 1e308, 0 | differ: total `inf` vs missing, then has_delinquency 1/0, flag_multiple_delinquencies 1/0, total_risk_flags 2/1, financial_health 65/85, log `inf`/missing | on, Float only |
| utilization 1e200, debt ratio 1e200 | agree (the product overflows to missing on both sides) | on |
| missing age | differ: age_category Python 5, SAS 1 | outside |
| missing monthly_income | differ: flag_low_income Python 0, SAS 1; total_risk_flags 0/1 | outside |
| missing num_dependents | agree | - |
| one missing late count; all three missing | agree | outside |
| missing credit_utilization | differ: credit_util_category Python 4, SAS 1. `credit_utilization_capped` is 200 on both sides (`min(., 200) = 200`) | outside |
| missing debt_ratio | differ: debt_category Python 4, SAS 1 | outside |
| missing num_credit_lines | differ: flag_few_credit_lines Python 0, SAS 1 | outside |
| every cell missing, `full = false` | differ in the six cells above | outside |
| NaN in each column in turn | differ in most (NaN compares greater in polars; SAS arithmetic gives missing; capped NaN: Python 200, SAS NaN) | Float only |
| negative values (income -1, lines -1; all negative) | agree | outside |
| age 1e308 with income 1.7e308 | differ: age_income_interaction `inf` vs missing | on, Float only |
| num_dependents 1e-320, income 1e308 | agree | on |

Smallest witness without the domain, real arithmetic too: one row with credit_utilization
missing (Python category 4, SAS 1), or monthly_income missing (flag_low_income 0 vs 1).

### S6 `fe_run_06_split` / `credit_train_validation`, the two exports

| Input | Outcome | Domain |
|---|---|---|
| ids 1, 3; rows 1..4 | agree (both files) | on |
| **ids 1; row_id missing in one row** | **differ: the row is in neither Python file; SAS puts it in validation** | **on** (D_fe says nothing on row_id) |
| a null among the ids; every row selected; duplicated ids; row_id NaN or 2.5 | agree | - |
| a column `selected` already in the feature frame | differ: Python drops it, SAS keeps it (the SAS variable is `Selected`; in SAS itself names are not case sensitive, so this is an artefact of the model) | - |

Smallest witness: feature frame `row_id = [missing, 1]`, ids `[1]`.

### ST1 `run` / the composition of the SAS units

Flags off. Both file names agree in every case.

| Input | Outcome | Domain |
|---|---|---|
| 6 raw rows (ages 45, 25, 28, 29, 47, 61; incomes "5000", "NA", "1016.85", "7098.24", "NA", "2400"; dependents with "NA"), ids 1, 3, 4, 6; `full = true` and `full = false` | agree, both files, rows in the same order (step by step: only S2 differs, by row order) | on |
| one row | agree | on |
| utilization 1e308 | differ: credit_utilization `inf` vs missing and five derived cells | on, Float only |
| late counts 0.1, 0.3, 0.2 | differ by one unit in the last place in total_late_payments | on, Float only |
| VAR1 missing in one row | differ: the row is in no Python file, in the SAS validation file | on |
| an extra numeric column `median_income` (77, 78) and a missing income | differ: monthly_income 78 vs 5000 and five derived cells | on |
| an age group with no present income | differ: flag_low_income 0 vs 1, total_risk_flags 2 vs 3 | outside |
| a missing age with a missing income | differ: age_group 5 vs 1, monthly_income 100 vs 9000, age_category, flag_low_income, ... | outside |
| every cell missing | S3, S5, S6 differ | outside |

### F3, F4 (`run` only)

`export_train_medians` on: file names `income_medians.csv`, `model_features_train.csv`,
`model_features_validation.csv`; the last two equal the result with the flag off; the medians are
sorted by age_group ((1, 4057.545), (3, 5000) on the 4-row input; empty when no income is present).
`fix_income_truncation` on or off: identical results, for both values of the other flag.

### I3, I4 (Python side only)

- Row (45, 2000, 3, 1, 2, 1, 120, 70, 2): all ten flags are 1, each variable is present and beyond
  its threshold.
- Row (25, missing, 2, 0, 0, 0, missing, missing, 4): every flag is 0 (flag_low_income 0 with a
  missing income); `credit_utilization_capped = 200` and `debt_ratio_capped = 500` while the
  originals are missing.
- At Float a NaN credit_utilization sets flag_high_utilization and flag_very_high_utilization.
- `fe_run_04_imputed` on a row of group 2 with a missing income and an empty medians table:
  `monthly_income` missing. With a median for group 2: 4000.

---

# Group: Train (S7 to S13, ST2, I5, C4)

## Pairings by evaluation: group TRAIN (S7 to S13, ST2; also I5, C4)

All evaluations at `Float` through the carrier `def:zz_tr` (`eval_decl`), both sides on the same
input, compared cell by cell through `Float.toBits` (missing prints `.`). Notation for inputs:
frames are lists of columns, `.` is a null, `NaN` is `0.0/0.0`. "On the domain" refers to
section 2, row `D_train`, as read for each unit (see "Reading of `D_train`" at the end).
At `Float`, overflow and NaN exist; at the reals they do not, so a difference that needs them is
marked "Float only".

Parameter links used: `model` = intercept and (name, coefficient) list of the Python side, same
order; `invLink e = Pl.ofInt 1 / (Pl.ofInt 1 + exp (-e))` (the Python expression of step 04);
`today` = the same number on both sides (`Tabular.Cell.num today` in Python).

### S7. `train_run_04_score_train` (5th component) vs `logit_scored_train_output`

Carrier `zz_tr_s7 candidates fit_mask final f`; model `names = [Intercept, x]`, `beta = [0.5, 1.0]`
unless said. Second comparison: the SAS table after removing the column `_LEVEL_`.

| Input | As written | Without `_LEVEL_` |
|---|---|---|
| plain, 3 rows, x = 1, -2, 0.25 (plus row_id, z, default_flag) | differ | agree |
| missing model variable: x = [1, .] | differ | agree (pd missing on both) |
| missing default_flag | differ | agree |
| two terms, columns in another order than the model (beta 0, 0.1, -0.3) | differ | agree |
| NaN: x = [1, NaN] | differ | differ |
| overflow: beta_x = 10, x = [1, 1e308] | differ | differ |
| overflow of exp (eta below -709.8) | not evaluated: excluded by the Python precondition (exp(-eta) finite) | |

- Difference 1 (every input, on the domain, also at the reals): the SAS table has the column
  `_LEVEL_ = 1` before `pd_logistic`; the Python frame has no such column. Smallest witness:
  one row `x = 1`. Python row: `x, pd_logistic`; SAS row: `x, _LEVEL_=1, pd_logistic`.
- Difference 2 (Float only, NaN): x = NaN. Python `pd_logistic = NaN`, SAS `pd_logistic = .`
  (`Sas.mul` gives missing for a non-finite product).
- Difference 3 (Float only, overflow, on the domain: no variable is missing): beta_x = 10,
  x = 1e308. The linear predictor is +inf. Python `pd_logistic = 1.0`; SAS `pd_logistic = .`.

### S8. `train_run_09_confusion_train` vs `logit_scored_train`, `confusion_matrix_train`, `training_metrics`

Carrier `zz_tr_s8 f`; three comparisons (scored table, confusion matrix, metrics).
Columns read: `pd_logistic`, `default_flag`.

| Input | scored | confusion matrix | metrics |
|---|---|---|---|
| plain: pd 0.9, 0.2, 0.6, 0.4, 0.5; flag 1, 0, 0, 1, 1 | agree | agree | agree |
| empty class: flag 0, 0 | agree | agree | agree |
| no predicted positive: pd 0.1, 0.2; flag 1, 0 | agree | agree | agree |
| missing pd: pd 0.9, ., 0.2 | agree | agree | agree |
| default_flag as an Int64 column | agree | agree | agree |
| default_flag = 2 on a row | agree | agree | agree |
| overflow values (pd 1e308, -1e308, inf; flag 1e308) | agree | agree | agree |
| input already has a column pred_logistic | agree | agree | agree |
| missing default_flag: pd 0.9, 0.2, 0.6, 0.1; flag 1, 0, ., 1 | agree | differ | agree |
| all default_flag missing (2 rows) | agree | differ | agree |
| NaN pd: pd 0.9, NaN, 0.2; flag 1, 1, 0 | differ | differ | differ |
| NaN default_flag | agree | differ | agree |
| empty frame (0 rows) | agree | agree | differ |

- Missing `default_flag` (outside the domain; also at the reals). PERCENT of the confusion matrix.
  Python divides every COUNT by the total number of rows; SAS (PROC FREQ) divides by the number
  of rows where both variables are present and gives a missing PERCENT on a row with a missing
  level. Witness of 4 rows above: Python PERCENT = 25, 25, 25, 25; SAS PERCENT = ., 33.33, 33.33,
  33.33. (One row suffices, see S10: Python 100, SAS missing.)
- NaN pd (Float only): polars `NaN >= 0.5` is true (total order), SAS false. Python
  `pred_logistic = 1`, SAS 0; recall 1.0 vs 0.5.
- NaN default_flag (Float only): Python keeps a NaN level row, the SAS Lean has two rows.
- Empty frame (outside the domain; also at the reals): Python `training_metrics` has one row of
  four missing values, SAS has no row.

### S9. `train_run_10_score_valid` vs `logit_scored_valid (logit_scored_valid_temp model ·)`

Carrier `zz_tr_s9 intercept coefficients f`.

| Input | Result |
|---|---|
| plain, two terms, 3 rows, a missing default_flag | agree |
| missing model variable: x = [1, .] | agree (pd missing, pred 0) |
| overflow of exp: x = -800 and 800 (intercept 0.5, coefficient 1) | agree (pd missing for -800) |
| NaN x | agree (both missing, pred 0) |
| linear predictor -inf: coefficient 10, x = -1e308 | agree (missing) |
| no coefficient | agree |
| empty frame | agree |
| input already has pd_logistic and predicted_logit columns | agree |
| signed zeros (intercept 0, x = -0.0) | agree |
| linear predictor +inf: intercept 0.5, coefficient 10, x = 1e308 | differ |
| +inf by the sum: coefficients x: 1, z: 1; x = z = 1e308 | differ |

- Difference (Float only, overflow of the linear predictor, on the domain): one row x = 1e308,
  coefficient 10. Python: `pd_logistic = 1.0`, `pred_logistic = 1`. SAS: `pd_logistic = .`,
  `pred_logistic = 0`. Python guards `exp` only (`sas_exp`); `exp(-inf) = 0` is finite. SAS makes
  the overflowing product (or sum) missing. The probe named by the specification, overflow of
  `exp`, agrees.

### S10. `train_run_11_confusion_valid` vs `confusion_matrix`, `validation_metrics`

Carrier `zz_tr_s10 f`; columns read: `default_flag`, `pred_logistic` (Int64 by the precondition).

| Input | confusion matrix | metrics |
|---|---|---|
| plain, all four cells | agree | agree |
| empty class (flag 0, 0) / (flag 1, 1 with pred 0, 0) | agree | agree |
| Int64 default_flag | agree | agree |
| other levels (flag 2, 1e308; pred 5) | agree | agree |
| missing default_flag, one row: flag ., pred 1 | differ | agree |
| missing default_flag among 4 rows | differ | agree |
| missing pred_logistic: flag 1, 0; pred ., 0 | differ | agree |
| NaN default_flag | differ | agree |
| empty frame | agree | differ |

- Missing `default_flag` (outside the domain; also at the reals), smallest witness one row
  `default_flag = ., pred_logistic = 1`: Python PERCENT = 100, SAS PERCENT = `.`.
- Missing `pred_logistic` (also at the reals): flag 1, 0; pred ., 0. Python PERCENT 50, 50; SAS
  100, `.`. `D_train` says nothing about `pred_logistic`, so this input is ON the domain as the
  specification states it (default_flag present, both outcomes occur); the pipeline never
  produces it (`flag` never returns null).
- Empty frame (outside the domain): Python metrics have one row of missing values, SAS no row.

### S11. `train_run_12_risk_scores` vs `risk_scores_train`, `risk_scores_validation`

Carrier `zz_tr_s11 ft fv`; column read: `pd_logistic`.

| Input | Result |
|---|---|
| pd 0, 0.1, 0.3, 0.5, 0.7, 0.9, 1 and band edges 0.398, 0.402, 0.598, 0.602, 0.798, 0.802 | agree |
| missing probability | agree (score missing, grade F, Decline, rate 0.05 + 0.15) |
| pd outside [0, 1]: 1.1, 1.2, 1.3, 2, 5, -0.5, -3 | agree |
| near-half scores, large pd (1e17, 4e13) | agree |
| input already has base_score, risk_grade, interest_rate, credit_risk_score columns | agree |
| empty frame | agree |
| NaN pd | differ |
| overflow: pd = 1e308, -1e308 | differ |
| score just below 0.5: pd = 3.3980000000000023 | differ |

- The probe named by the specification (a missing probability with plain comparisons) agrees.
- Rounding (on the domain as stated, pd present; also at the reals; pd is not a probability):
  pd = 3.3980000000000023 gives a raw score of about 0.5 - 6e-13. Python `sas_round` counts
  `|frac - 0.5| <= 1e-12 * max(1, |x|)` as a half and returns 1; SAS `round` uses
  `eps = min(1e-6, |x| * 1e-12)` and returns 0. Python `credit_risk_score = 1`, SAS 0. The two
  rules differ for |x| < 1 (and for |x| > 1e6); for 600 <= x <= 850 they are the same rule.
- NaN (Float only): Python score NaN, grade A, Approve, rate 0.05; SAS score missing, grade F.
- Overflow (Float only): pd = 1e308: Python score -inf (grade F on both sides), SAS missing.
  pd = -1e308: Python score +inf, grade A; SAS missing, grade F.

### S12. `train_run_13_roc` vs `roc_train`, `roc_valid`

Carrier `zz_tr_s12 ft fv`: as written, and with the Python table restricted to the two columns
the SAS unit gives (ROCModel, Area).

| Input | As written | ROCModel and Area only |
|---|---|---|
| plain, untied | differ | agree |
| exact ties (pd 0.5, 0.5, 0.7, 0.2; flag 1, 0, 1, 0) | differ | agree |
| missing default_flag, missing pd rows | differ | agree |
| empty class; empty frame | differ | agree (Area missing) |
| Int64 default_flag | differ | agree |
| overflow values in pd (1e308, -1e308, inf) | differ | agree |
| NaN pd on a non-event | differ | agree |
| near tie: flag 0, 1; pd 0.5, 0.5000000102 | differ | differ |
| chain: flag 1, 0, 0; pd 0.5, 0.500000006, 0.500000012 | differ | differ |
| default_flag = 2 on a row: flag 1, 0, 2; pd 0.5, 0.6, 0.1 | differ | differ |
| NaN default_flag | differ | differ |

- Difference 1 (every input, on the domain): the Python frame has eight columns (ROCModel, Area,
  StdErr, LowerArea, UpperArea, SomersD, Gamma, TauA); the SAS unit gives ROCModel and Area only
  (its comment: the other columns are never read by the pipeline).
- Difference 2, ties (on the domain, also at the reals). SAS groups probabilities within
  ROCEPS = 1.0536712127723509e-8 of the top of a group, scanning from the largest; Python counts
  a pair as tied when the two values differ by at most 1e-8.
  Witness A (tolerance): flag 0, 1; pd 0.5, 0.5000000102. Python Area = 1.0, SAS Area = 0.5.
  Witness B (grouping): flag 1, 0, 0; pd 0.5, 0.500000006, 0.500000012. Python Area = 0.25,
  SAS Area = 0.0.
- Difference 3 (default_flag not 0 or 1): flag 1, 0, 2; pd 0.5, 0.6, 0.1. Python Area = 0.0
  (the row with 2 is ignored), SAS Lean Area = 0.5 (every non-1 is a non-event). The SAS unit's
  precondition excludes this input: see precondition pairs.
- NaN default_flag (Float only): Python 1.0, SAS 0.5 (same cause as difference 3).

### S13. `train_run_14_final_and_summary` vs the two `_clean` units, `final_model_output`, `model_summary`

Carrier `zz_tr_s13 today tm vm rst rsv roct rocv` (the fifth output, model_coefficients.csv, has
no SAS unit in this group and is not compared).

| Input | risk_scores_train | risk_scores_validation | final_model_output | model_summary |
|---|---|---|---|---|
| plain; kept columns in another order with extra columns; missing cells | agree | agree | agree (order of the frame) | agree |
| today missing; 2-row validation metrics; no matching ROC label; 3-row ROC frame | - | - | agree | agree |
| 0-row training metrics; metrics frame with columns named model_name and Train_AUC | agree | agree | agree | agree |
| both ROC labels unmatched | agree | agree | agree | agree |
| risk_scores_train has columns `_LEVEL_`, `ip_1`; validation has `XP_0` | differ | differ | agree | agree |

- Column order after `keep` (the probe named by the specification): agrees; both keep the
  order of the input.
- Difference (no domain condition applies; also at the reals): a column named `_LEVEL_`,
  `_FROM_`, `_INTO_` or starting with `IP_` / `XP_` (any case). SAS drops it
  (`drop IP_: XP_: _FROM_ _INTO_ _LEVEL_`), Python exports the frame unchanged. Smallest
  witness: risk_scores_train = one column `_LEVEL_ = [1.0]`: Python row `_LEVEL_=1`, SAS row
  empty. The Python pipeline never creates such a column; the SAS pipeline does (`_LEVEL_`).

### ST2. `run_py_py_py` vs the composition of the SAS units

Carrier `zz_tr_st2 today beta T V`. T and V are built by `zz_tr_mk` from rows
(row_id, default_flag, age, monthly_income); the other 34 candidates are 0.0. The fitted model is
Intercept, age, monthly_income with the given beta; the out-of-scope parameters (formatters,
chi2, linear algebra) are dummies. SAS side: `logit_scored_train_output` (model = the Python
model.json, `invLink` as above), `logit_scored_train`, `confusion_matrix_train`,
`training_metrics`, `logit_scored_valid_temp`, `logit_scored_valid`, `confusion_matrix`,
`validation_metrics`, `risk_scores_train`, `risk_scores_validation`, `roc_train`, `roc_valid`,
the two `_clean` units, `final_model_output`, `model_summary`.

| Input | risk_scores_train.csv | risk_scores_validation.csv | final_model_output.csv | model_summary.csv (AUCs, metrics) |
|---|---|---|---|---|
| plain: beta -2, 0.05, -0.0002; 6 training rows, 4 validation rows | agree | agree | agree | agree |
| a missing model variable (age in T, income in V) | agree | agree | agree | agree |
| a missing default_flag in T and V | agree | agree | agree | agree |
| one class only in T | agree | agree | agree | agree (AUC missing) |
| overflow: beta_age = 10, age = 1e308 | differ | differ | differ | differ |
| near tie: beta 0, 1, 0; ages 0 and 4.08e-8, flags 0 and 1 | agree | agree | agree | differ |

- The `_LEVEL_` column of S7 does not reach the exported files: `risk_scores_train_clean` drops
  it and `final_model_output` does not keep it.
- Near tie (on the domain; a real-number difference): pd = 0.5 and about 0.5 + 1.02e-8.
  Python Train_AUC = Valid_AUC = 1.0; SAS 0.5. Every other cell agrees. Cause: S12 difference 2.
- Overflow (Float only, on the domain): Python pd = 1, score 600, grade D, rate 0.12; SAS pd
  missing, grade F, rate 0.20; the metrics and AUCs differ too. Cause: S7 difference 3 and S9.
- Not checked: that these inputs meet the sub-preconditions of the out-of-scope steps 03, 05,
  06, 07, 08, 15 inside `run_py_py_py_precond` (they involve the dummy parameters).

### I5. `train_run_12_risk_scores` (carrier `zz_tr_i5`)

pd -> (score, grade): 0 -> 850 A; 0.05 -> 838 A; 0.12 -> 820 A; 0.2 -> 800 A; 0.3 -> 775 A;
0.398 -> 751 A; 0.402 -> 750 A; 0.45 -> 738 B; 0.598 -> 701 B; 0.6 -> 700 B; 0.602 -> 700 B;
0.798 -> 651 C; 0.802 -> 650 C; 1.0 -> 600 D; missing -> missing, F.
Outside [0, 1]: 1.1 -> 575 E; 1.3 -> 525 F; 3.0 -> 100 F; -1.0 -> 1100 A.
So: for a probability in [0, 1] the score is in 600..850 (inside 300..850), the grades are A to D
only, and F arises from a missing probability; the model-card bands fail (pd = 0.2 is grade A,
band A is below 10%).

### C4. `train_run_01_fit_frame` (carrier `zz_tr_c4`)

Rows (row_id, default_flag, age, monthly_income): (1, 1, 60, 1000), (2, 0, ., 5000),
(3, ., 45, 3000), (., 1, 25, .), (5, 0, NaN, 8000).
Mask: true, false, false, false, true.
"No missing candidate" (the 36 candidates): true, false, TRUE, false, true.
"No missing candidate and no missing default_flag": true, false, false, false, true.
The mask also excludes a row whose `default_flag` is missing (row 3): it tests the 36
candidates and `default_flag` (train.py:79). As written, "exactly the rows with no missing
candidate" does not describe the mask; with `default_flag` added it does. A NaN is not missing.

### Reading of `D_train` used for the units of this group

`D_train` (feature tables): "no model variable is missing; both outcomes occur". Per unit, only
what the unit reads:

- S7, S9 (read the model variables): every variable of the fitted model is present in every row.
- S8 (reads pd_logistic, default_flag): pd_logistic present (the image of "no model variable
  is missing" on a scored table), default_flag present (the response of the MODEL statement),
  default_flag = 1 on some row and = 0 on some row.
- S10 (reads default_flag, pred_logistic): default_flag present, both outcomes. Nothing on
  pred_logistic.
- S11 (reads pd_logistic): pd_logistic present, in both frames.
- S12 (reads default_flag, pd_logistic): as S8, in both frames.
- S13: reads no value: no condition, so parts (a) and (b) are the same statement.
- ST2: both feature tables: every variable of the model present, default_flag present, both
  outcomes.

If "model variable" is read as excluding the response, S8(a), S10(a), S12(a) lose the condition
"default_flag present" and S8(a), S10(a) then fail by the missing-default_flag witness above.

### Agreement apart from the structural difference (evaluation only, not a contract)

The seven supplementary items that held this evidence in the blueprint were removed in phase 3.
What they recorded is evaluation at `Float` only; none of it is a contract and none of it is
proved. The carrier `def:zz_tr` was removed at the end of phase 3, so the evaluations of this
file can no longer be re-run from the blueprint as they stand.

- S7 without `_LEVEL_` (parts a and b): with the SAS column `_LEVEL_` left out, the scored
  training table agrees on every other column on the inputs of section S7, including a row with
  a missing model variable (pd_logistic missing on both sides).
- S10 with pred_logistic present: on inputs whose pred_logistic is never missing and whose
  default_flag is present, the confusion matrix and the metrics agree (section S10).
- S11 for probabilities: for pd_logistic in [0, 1] (raw score in [600, 850]) the two rounding
  rules give the same score, grade, recommendation and rate on the inputs of section S11.
- S12, ROCModel and Area only (parts a and b): with the Python table restricted to the two
  columns the SAS unit models, the two sides agree on the inputs of section S12 without near
  ties; they differ on the near tie below.
- C4 with default_flag: the mask is true exactly on the rows where no candidate and not
  default_flag is missing, on the inputs of section C4.

### Phase 3: formal results (blueprint `py-credit-risk-port`)

Disproved at the reals (negation item proved; witness in the proof text of each `neg:` item):

| Contract | Witness | What differs |
|---|---|---|
| S7a, S7b | no candidate, intercept-only model (beta = [0]), frame x = [0] | SAS first row has `_LEVEL_` = 1, Python has no such cell (structural; the exported files agree) |
| S8b | frame with columns pd_logistic, default_flag and no row | Python training_metrics has 1 row, SAS 0 rows |
| S10a | default_flag = [0, 1], pred_logistic = [0, null] (on the domain) | PERCENT of row 2: Python 50, SAS missing |
| S10b | frame with columns default_flag, pred_logistic and no row | Python validation_metrics has 1 row, SAS 0 rows |
| S11a, S11b | one row, pd_logistic = 3.398000000000002 (raw score exactly 0.4999999999995) | credit_risk_score: Python 1, SAS 0 (rounding fuzz absolute vs relative below 1) |
| S12a, S12b | default_flag = [0, 1], pd_logistic = [0.5, 0.5000000102] | Area: Python 1, SAS 0.5 (tie rule); also six Python columns the SAS unit does not model |
| S13a, S13b | risk_scores_train with the single column `_LEVEL_` = 0 | risk_scores_train.csv: Python keeps `_LEVEL_`, SAS drops it |
| I5_bands | pd_logistic = 0.2 | score 800, grade A, but 0.2 is not below 0.10 |
| C4 | 36 candidates = [0, 0], default_flag = [0, missing] | row 2: no candidate missing, mask false |

The missing-default_flag PERCENT difference of S8b and S10b stays `Float` evidence only (the
formal witness is the empty frame).

Proved at the reals, for every input meeting the precondition: I5_range (score in [300, 850]
for a probability), I5_range_sharp (score in [600, 850] for a probability) and I5_grades (a
probability gets grade A, B, C or D; a missing probability gets grade F).

Stated, not settled: S8a, S9a, S9b, ST2 (see the phase 3 report). The product
overflow difference of S9 (coefficient 10, x = 1e308) is a `Float`-only finding on the domain
and does not arise at the reals.

---

# Group: Metrics (S14 to S22, ST3, H13, F1, I1, I7)

## Pairings by evaluation: METRICS group (tag `me`)

Phase 1. Both sides evaluated at `Float` on the same inputs through the carrier `def:zz_me`
(blueprint `py-credit-risk-port`), compared bit for bit through `Float.toBits`.
"Domain" is `D_metrics` of informal-spec.md section 2: `pd_logistic` present, `default_flag` 0 or 1,
both outcomes occur.

### How the comparison was made

- Score frames are built by `zz_me_fr flags pds` (columns `row_id` = 1..n, `default_flag`,
  `pd_logistic`, all Float64). Below a frame is written `F[flags | pds]`, `.` is a null, `NaN` is `0.0/0.0`.
- Python parameters: `sas_best := zz_me_sb` (the bits of the number as text, empty text for a null),
  `parse_float := zz_me_pf` (reads the bits back and rounds to 6 decimals, a stand-in for the BEST8.
  round trip), SAS `best8 := zz_me_b8 = fun x => zz_me_pf (zz_me_sb (some x) 8)`, so the link
  `best8 x = parse_float (sas_best x 8)` holds by construction and is not the identity.
- SAS `agg` (`zz_me_agg k`): k = 0 the polars group algorithm (`Pl.kahan`, mean = kahan / n), k = 1 the
  polars select algorithm (`Pl.floatSum`, mean = floatSum / n), k = 2 a left fold from 0.0.
  With the algorithm polars uses in that context, agreement is bit for bit; with k = 2 the only
  differences are summation order (see S17, S20).
- `today`: Python `Cell.num (some 24000.0)`, SAS `some 24000.0`.
- SAS compositions: S14 `roc_stats T`, `auc_summary (roc_stats T)`; S15 `S := logit_scored_valid_sorted T`,
  `ks_statistic (ks_calculation (total_good_bad S) S)`; H13 `confusion_metrics_macro th T`; S16
  `threshold_analysis T`; S17 `decile_data T`, `decile_analysis agg (decile_data T)`; S18
  `cumulative_lift (total_defaults agg best8 DD) DA`; S19 `psi_calculation (train_bins Ttr) (valid_bins Tva)`,
  `psi_summary agg (..)`; S20 `calibration_plot agg (calibration_data T)`; S21 `validation_summary A K P`;
  S22 `model_performance_metrics today A K P THR`; ST3 the composition of all of these in the order of
  metrics_calculation.sas (roc on the table as imported, everything after line 75 on the sorted table,
  `train_bins` on the training table as imported).
- Edge scenarios: `eval_decl` takes inline Lean terms only, so the full files (3,000 + 7,000 rows per
  scenario) could not be passed. The FIRST 150 validation rows and FIRST 350 training rows of each of
  `edge_metrics_a/b/c` were used (same files on both sides: `diff -rq` of the two scenario folders is
  empty). The transcription was checked: row counts and the bits of the left-fold sums of `default_flag`
  and `pd_logistic` computed in Lean (`zz_me_chk`) equal those computed from the CSV prefixes in Python
  (a: 150/4622945017495814144/4623676852435261845, 350/4630826316843712512/4629765156181513336;
  b: 150/4621819117588971520/4623219174123130324, 350/4629418941960159232/4631332971801791726;
  c: 150/4625478292286210048/4623147679479045811, 350/4631248529308778496/4629447089457830267).
  The full-size scenarios were NOT evaluated.

### Outcome per pairing

#### S14 `metrics_run_01_roc_auc` vs `roc_stats`, `auc_summary`

| Input | roc_stats | auc_summary |
|---|---|---|
| plain F[0,1,0,1,0,0,1,0 \| .1,.7,.35,.2,.05,.6,.9,.45] | differ (columns) | agree |
| ties F[0,1,0,1 \| .2,.2,.2,.5]; near-ties F[0,1,0,1 \| .2,.200000001,.20000002,.5] | differ (columns) | agree |
| missing flag and missing pd F[0,1,.,1,0 \| .2,.,.3,.5,.1] | differ (columns) | agree |
| single class F[0,0 \| .2,.5] | differ (columns) | agree (AUC, Gini missing on both) |
| NaN pd F[0,1,1 \| .2,NaN,.9] | differ (columns) | agree |
| flag 2: F[0,1,2 \| .2,.5,.9] | differ | DIFFER |
| NaN flag: F[0,1,NaN \| .2,.4,.9] | differ | DIFFER |
| scenario prefixes a, b, c | differ (columns) | agree |

- roc_stats differs on EVERY input: the Python frame has 8 columns (ROCModel, Area, StdErr, LowerArea,
  UpperArea, SomersD, Gamma, TauA), the SAS Lean gives 2 (ROCModel, Area: "the other columns are never
  read"). Smallest witness F[0,0 | .2,.5]: py `[ROCModel='Logistic Model', Area=., StdErr=., LowerArea=.,
  UpperArea=., SomersD=., Gamma=., TauA=0]`, sas `[ROCModel='Logistic Model', Area=.]`. On the domain.
  This is the scope of the SAS specification, not a behaviour difference: the `Area` cell agreed in every
  case where auc_summary agreed.
- auc_summary: witness F[0,1,2 | .2,.5,.9]: py AUC = 1.0 (4607182418800017408), Gini = 1.0; sas AUC = 0.5
  (4602678819172646912), Gini = 0. SAS counts a `default_flag` that is not 1 as a non-event, Python
  leaves the row out. Outside the domain (flag not 0 or 1). Same with a NaN flag.

#### S15 `metrics_run_02_ks` vs `logit_scored_valid_sorted`, `total_good_bad`, `ks_calculation`, `ks_statistic`

Agree (sorted table and ks_statistic) on: plain; tied pd F[0,1,0,1 | .2,.2,.2,.5] and F[1,0,0,1 | same]
(the order inside the tie is kept on both sides; 2 rows each); maximum attained twice
F[0,1,0,1 | .1,.2,.3,.4] (2 rows on both sides: KS = 0.5 at cut-offs 0.1 and 0.3); missing pd; missing
flag; NaN flag; flag 2; single class F[0,0,0 | ..] and F[1,1,1 | ..] (KS missing, every row kept, on
both sides); all flags missing; all pd missing; 1e308; scenario prefixes a, b, c (1 KS row each).

Differ: NaN pd. Witness F[0,1,0,1 | .1,NaN,.3,.4]: py sorted puts NaN last and gives
`[[KS_Statistic=1.0, KS_Cutoff=0.3]]`; sas sorted starts with row 3 and gives two rows
`[[KS=0.5, cutoff 0.3], [KS=0.5, cutoff NaN]]`. A NaN is a present value, so at `Float` this input is
on the domain as literally stated; it does not exist at the reals.

Note for the statement: the Python unit takes `sas_best`, `parse_float` for the two counts; the SAS unit
`total_good_bad` has no `best8` parameter (it fixed the round trip to the identity under its own
precondition, fewer than 10^8 rows). The agreement above is for a round trip that is the identity on
the counts.

#### H13 `confusion_metrics` (third component) vs `confusion_metrics_macro`

Agree: plain at 0.5; missing pd F[0,1,1 | .1,.,.7] at 0.5, 0.2 and -1.0 (a missing probability is
predicted 0 on both sides); NaN threshold; 1e308; Int64 columns with nulls; missing flag.

Differ: the frame with no row. Witness `zz_me_fr [] []`, threshold 0.5: py one row
`[threshold=0.5, accuracy=., precision=., recall=., f1_score=., specificity=.]`, sas no row. The Python
precondition accepts it (no "at least one row" condition); outside the domain (no outcome occurs).
(NaN pd also differs, see S16.)

#### S16 `metrics_run_03_thresholds` vs `threshold_analysis`

Agree: plain; pd equal to the thresholds F[0,1,0,1 | .3,.5,.7,.4]; missing pd; missing flag; NaN flag;
flag 2; single class (both ways); all flags missing; all pd missing; 1e308; flags 2 and 3 only;
scenario prefixes.

Differ: NaN pd, witness F[0,1,0,1 | .1,NaN,.35,.65]: at 0.3 py accuracy 0.75, sas 0.5 (polars: NaN >=
threshold is true; SAS: false). Float only. And the frame with no row (5 rows against 0, as H13).

#### S17 `metrics_run_04_deciles` vs `decile_data`, `decile_analysis`

Agree with agg = kahan AND with agg = left fold: plain (8 distinct pd); ties across decile boundaries
F[12 rows | .1 x3, .2 x4, .3 x5]. Agree with agg = kahan: missing pd (a missing decile group, first);
missing flag; flag 2; single class (capture_rate and lift missing: division by 0); all flags missing; all
pd missing; scenario prefixes a, b, c.

With agg = left fold on the scenario prefixes, decile_data agrees and decile_analysis differs in
`avg_pd` only, by 1 or 2 units in the last place (a: row 0 py 4598007085159187918 sas ..916; b: row 3
py 4591087840474545933 sas ..931; c: row 1 py 4594061931885611363 sas ..364): summation order.

Differ (Float only): NaN pd F[0,1,0,1 | .1,.2,.3,NaN] (py ranks NaN as the greatest value, decile 4 for
row 1 against 3 in sas; avg_pd NaN against missing); NaN flag (defaults NaN against missing); overflow
of the mean F[0,1,1 | .1,1e308,1e308] (avg_pd = inf in py, missing in sas): on the domain as literally
stated; overflow of the flag sum F[1e308,1e308,1 | ..] (outside).

#### S18 `metrics_run_05_cumulative_lift` vs `total_defaults`, `cumulative_lift`

On the frames step 04 produces (agg = floatSum, and left fold on the first): agree on plain, ties,
missing pd, NaN pd, flag 2, single class, all flags missing, all pd missing, 1/7 default rate (the
rounded `best8` value is used in the same place on both sides), scenario prefixes.

Differ:
- a decile whose flags are all missing. Witness F[0,.,0,1 | .1,.2,.3,.4], row 2: py `cum_defaults=.`,
  `cum_capture_rate=.`, `cum_lift=.`; sas `cum_defaults=1`, `cum_capture_rate=1.0`, `cum_lift=4607182423303621539`.
  The SAS sum statement skips a missing `defaults`, polars `cum_sum` gives null on that row. Outside the
  domain (missing flag).
- hand-made `decile_analysis` not sorted by decile: dd `[default_flag=[0,1]]`, da `[decile=[2,1],
  total_count=[1,1], defaults=[1,0]]`: py sorts first (row 0 is decile 1), sas keeps the input order
  (row 0 is decile 2). Meets the Python precondition; never produced by step 04.
- overflow: defaults `[1e308, 1e308]`: py cum_defaults = inf, sas missing. Float only.
- NaN flag (Float only).

#### S19 `metrics_run_06_psi` (flag off) vs `train_bins`, `valid_bins`, `psi_calculation`, `psi_summary`

Agree (agg = floatSum; also left fold where tried): untied train 3 rows / valid 4 rows (one joined bin,
PSI = 4582567114071330666 on both sides); tied data; EMPTY JOIN train 1 row / valid 2 rows and train all
pd missing (psi_calculation has no row, PSI missing, "No significant change" on both sides); missing pd
on both sides (the missing bin joins the missing bin); missing pd in validation only; unsorted inputs;
12 / 7 rows with ties; scenario prefixes a (10 bins), b (3 bins), c (8 bins).

Differ: NaN pd in training F[.. | .1,NaN,.3] (py 3 rows, sas 2). Float only.

#### S20 `metrics_run_07_calibration` vs `calibration_data`, `calibration_plot`

Agree (agg = kahan; also left fold on the small cases): plain, ties, missing pd, missing flag, flag 2,
single class, all flags missing, all pd missing, unsorted with a missing pd, scenario prefixes.
With agg = left fold on the scenario prefixes: `mean_predicted` differs by 1 unit in the last place
(a row 1: py 4581421828931458171 sas ..170). Differ (Float only): NaN pd, NaN flag, overflow of the mean
(1e308 twice: inf against missing; on the domain as literally stated).

#### S21 `metrics_run_08_validation_summary` vs `validation_summary`

On the frames the earlier Python steps produce: agree on plain; SEVERAL KS ROWS (valid
F[0,1,0,1 | .1,.2,.3,.4]: 2 rows on both sides, second row AUC, Gini, PSI missing and status
'Needs Improvement'); single class (3 rows); empty join (PSI missing); missing and flag-2 values;
scenario prefixes. Hand-made frames: agree on 1 AUC row / 2 KS rows / 1 PSI row, on an empty
PSI_interpretation text, on a column `model` already present and an `AUC` column in two inputs.

Differ:
- hand-made frames that lack a column of the SAS template and have fewer rows than the longest input:
  a `[AUC=[0.8]]`, k `[KS_Statistic=[0.4,0.4]]`, p `[PSI=[0.1]]`. py row 1
  `[AUC=., KS_Statistic=0.4, PSI=., model, status]`; sas row 1 adds `ROCModel=''`, `Gini=.`,
  `PSI_interpretation=''`. Meets the Python precondition; never produced by the earlier steps.
- NaN AUC (Float only): py status 'Production Ready', sas 'Needs Improvement'.

#### S22 `metrics_run_09_model_performance` vs `model_performance_metrics`

On the frames the earlier Python steps produce: agree on the same inputs as S21 (1, 2 and 3 rows),
scenario prefixes. Not evaluated on hand-made frames (same merge as S21: the same template difference is
expected).

#### ST3 `run_py` (flag off) vs the composition of the SAS units

Six files compared (validation_summary, decile_analysis, threshold_analysis, ks_statistic,
calibration_plot, model_performance_metrics). Agree, with agg = kahan for the grouped units and floatSum
for PSI: plain 4 / 4 rows; ties 12 / 7 rows (also with left fold everywhere); missing flag, missing pd and
flag 2 together; single class (3 KS rows, 3 summary rows); scenario prefixes a, b, c. With a left fold
everywhere on the scenario prefixes only `avg_pd` (decile_analysis.csv) and `mean_predicted`
(calibration_plot.csv) differ, in the last place. Differ: NaN pd (all six files; Float only).

#### Flag `fix_psi_bins` (for F1, I1)

- Flag off, train F[.. | .1,.2], valid F[.. | .8,.9]: PSI = 0, both bins 0.5 / 0.5.
  Flag on, same input: shares 0.5 / 0 and 0.5 / 1, PSI = 4616870979110786325, 'Significant change'.
  So with the flag off PSI is 0 although the distributions differ on the training bins (I1 off fails).
- Flag on: valid .15 goes to the group starting at .1; valid .05 (below every start) goes to the lowest
  group; a training bin with no validation row has `valid_pct=0`.
- Frame, valid F[0,0,1,1 | .1,.2,.8,.9], train F[0,1,0,0 | .1,.2,.3,.4], flag off against on:
  decile_analysis, threshold_analysis, ks_statistic, calibration_plot, printed_roc_metrics,
  printed_cumulative_lift identical; printed_psi_calculation differs; in validation_summary.csv not only
  `PSI` (0 against 4611977172310405494) and `PSI_interpretation` change but also
  `status`: 'Production Ready' against 'Requires Review'. On the domain.
- I7: valid F[0,1,0,1 | .1,.2,.3,.4] gives 2 rows in ks_statistic (on the domain). The three scenario
  prefixes give 1 row.

#### Added in phase 3: the 1e-4 floor of the flag-on PSI (I1 flag on)

Train 20,000 rows: pd = 0.1 once, 0.5 x 19,998, 0.9 once; validation 10,000 rows: pd = 0.5 x 9,999,
0.95 once; flag on. Three training bins (0, 5, 9). Shares: bin 0 train 0.00005 (4542503522391573293)
against validation 0; bin 5 0.9999 on both sides; bin 9 train 0.00005 against validation 0.0001
(4547007122018943789). Every psi_component is exactly 0 and PSI = 0, 'No significant change', although
the shares differ in two bins: both shares of those bins are at or below the floor 1e-4, so their
logarithms cancel. The validation shares sum to 1, so the input is inside the flag-on precondition.
I1 with the flag on therefore FAILS by evaluation (expected "holds" in the specification). Not
reachable with fewer than 20,000 training rows; no formal disproof (the witness is too large to
evaluate in the kernel at the reals).

#### Formal results of phase 3 (blueprint items)

Disproved with a proof of the negation: S14a_roc, S14b_roc (8 columns against 2), H13 and S16b (frame
with no row), S18b (missing `defaults`), S21b and S22b (frames lacking template columns), I7 (degenerate
all-missing witness), S15a_ks and S15b_ks (degenerate `sas_best`). Proved at the reals: S15a_sorted,
S15b_sorted. Everything else is stated and not settled.

### Summary

| Pairing | On the domain (reals) | Outside the domain | Float only |
|---|---|---|---|
| S14 roc_stats | differs always: 8 columns against 2 (scope of the SAS Lean) | same | |
| S14 auc_summary | agree | differs: flag not 0/1 | NaN flag |
| S15 | agree (given an identity round trip on the counts) | agree | NaN pd |
| H13, S16 | agree | differs: frame with no row | NaN pd |
| S17 | agree up to summation order of `avg_pd` | agree | NaN, overflow |
| S18 | agree on step-04 frames | differs: all-missing decile; unsorted hand-made input | NaN, overflow |
| S19 | agree | agree (empty join included) | NaN pd |
| S20 | agree up to summation order of `mean_predicted` | agree | NaN, overflow |
| S21, S22 | agree on produced frames | differs: hand-made frames lacking template columns | NaN AUC |
| ST3 | agree up to summation order | agree | NaN pd |

---

# Group: Predict (S23 to S31, ST4, F2, I2, I3, I6, I8, C3)

## Pairings by evaluation: group PREDICT (S23 to S31, ST4, F2, I2, I3, I6, I8)

Blueprint `py-credit-risk-port`, carrier item `def:zz_pr` (removed at the end of phase 3), everything evaluated with `eval_decl` at
`Float`. Both sides receive the same input; cells are compared through `Float.toBits` (printed
below as the decimal value of the bits; `.` is the SAS missing value / a polars null).
Useful bit values: 0 = 0.0, 4607182418800017408 = 1.0, 4611686018427387904 = 2.0,
4613937818241073152 = 3.0, 4616189618054758400 = 4.0, 4617315517961601024 = 5.0,
9218868437227405312 = +inf, 18442240474082181120 = -inf, 9221120237041090560 = NaN.

Conventions of the evaluation:

- `input_best32` is `zz_pr_ib`: on a text column `Sas.inputBest` of each value (blank for a null),
  on any other column all nulls (what `Sas.chr` then `Sas.inputBest` gives). This is the
  `input_best32` link of section 1.
- `arrange` is the identity (existential link). `model` is `{intercept, terms := coefficients}`.
- "Edge" is `zz_pr_edge`: rows 1 to 32 and row 47 of `inputs/scenarios/edge_predict/cs-test.csv`
  (the whole file has 101,503 rows and cannot be passed to `eval_decl`). It keeps the features of
  the scenario: all five rows under 30 (rows 5, 10, 16, 19 and none other) have income `NA`, so
  age group 1 has no present income; row 10 has 98 late payments; row 47 has dependents `NA`.
  `MonthlyIncome` and `NumberOfDependents` are text, the other columns numeric, names cut to 32
  characters, `SeriousDlqin2yrs` all missing.
- The model is the one of `python/migration/diffeval/work/runs_r2_pipe/model.json` (18 terms).
- "Domain" is `D_predict` of section 2, restricted to the columns the unit reads.

### Summary

| Pairing | Edge | Other inputs | Differences found | On the domain? |
|---|---|---|---|---|
| S23 `predict_run_01_clean` / `test_raw_clean` | agree | agree on all | none | |
| S24 `predict_run_02_medians` (flag off) / `test_income_medians` | DIFFER | differ | row order; missing age; NaN income; overflow of the median | row order, NaN, overflow: on. Missing age: outside |
| S25 `predict_run_03_cleaned` / `test_cleaned` | agree | differ | missing age; text `MonthlyIncome` column | text column: on (the domain says nothing about it). Missing age: outside |
| S26 `predict_run_04_imputed` / `test_imputed` | agree | differ | overflow and NaN of `* 100`; null join key; a `median_income` column in the left frame | all on (the domain only asks utilization and debt ratio present) |
| S27 `predict_run_05_features` / `test_features` | agree (both `full`) | differ | missing age, utilization, debt ratio, credit lines; NaN; overflow | missing values: outside. NaN, overflow: on |
| S28 `predict_run_06_score` / `test_scored_temp` + `test_scored` | agree | differ | overflow of the linear predictor | on (no domain condition applies) |
| S29 `predict_run_07_predictions` / `test_predictions` | agree | differ | NaN probability; overflow; integer score at or above 5e11 (rounding) | on (no domain condition applies); none of them is a probability in [0, 1] |
| S30 `predict_run_08_outputs` / `kaggle_submission`, `test_predictions_full` | agree | differ | frame with no kept column; ragged frame (the step has no precondition item) | on (no domain condition applies) |
| ST4 `run_py_py` / composition of the ten SAS units | agree (both `full`) | differ | missing age with a missing income; missing utilization; overflow; NaN; overflow at scoring; a raw column named `median_income` | missing values: outside. Overflow, NaN, `median_income` column: on |
| S31 step 01 fe / predict | equal | equal | none | |
| S31 step 02 fe / predict (flag off) | equal | equal | none (flag on with a supplied table: differ, as intended) | |
| S31 step 03 fe / predict | equal | equal | none | |
| S31 step 04 fe / predict | equal after dropping `default_flag` | equal | fe has the extra column `default_flag` | |
| S31 step 05 fe / predict | DIFFER | differ | `flag_low_income` and `total_risk_flags`, only on rows with a missing income | on (`D_predict` allows a missing income) |

### S23: `predict_run_01_clean` against `test_raw_clean`

`zz_pr_s23 f` = differences between `Pl.toTable (predict_run_01_clean zz_pr_ib f)` and
`test_raw_clean (Pl.toTable f)`.

| Input | Result |
|---|---|
| Edge (raw frame, 33 rows) | agree |
| `MonthlyIncome` text `["5700", " 12.5 ", "NA", null, "", ".", "-3", "+.5", "1e400"]`, `x` Float64 with null, NaN, 1e308, `NumberOfDependents` text with null and `"NA"` | agree |
| `MonthlyIncome` Float64 `[5700, null]`, `NumberOfDependents` Int64 `[1, null]` (not text) | agree (both give missing) |
| frame that already has `NumberOfDependents_num` and `MonthlyIncome_num` columns | agree |
| zero rows | agree |

No difference found. (A `cell` column gives a difference only because `zz_pr_ib` is then not the
SAS conversion: excluded by the `input_best32` hypothesis, not a finding.)

### S24: `predict_run_02_medians` (flag off, `medians = none`) against `test_income_medians`

| Input (`age`, `MonthlyIncome`) | Result |
|---|---|
| Edge (frame after step 01) | DIFFER: 6 cells, the same rows in another order. Python `[3, 4, 2, 5]` (first appearance), SAS `[2, 3, 4, 5]` (ascending) |
| `[45, 35]`, `[1, 2]` | DIFFER. Python rows `(3, 1.0), (2, 2.0)`; SAS rows `(2, 2.0), (3, 1.0)`. **Smallest witness, on the domain** |
| ages already ascending by group `[25, 29, 35, 45, 55, 65, 30, 60, 25]`, incomes with nulls, even count `1016.85, 7098.24` | agree (the even-count median is bit-identical: `0.5 * (b - a) + a` and `lo + (hi - lo) / 2`) |
| `[null]`, `[5]` | DIFFER: Python `age_group` 5.0, SAS 1.0. Outside the domain (missing age) |
| `[NaN]`, `[5]` | agree (group 5 on both sides) |
| `[25, 25, 25]`, `[1, NaN, 3]` | DIFFER: Python median 3.0 (NaN sorts last), SAS NaN. On the domain |
| `[25, 25]`, `[1e308, -1e308]` | DIFFER: Python `+inf`, SAS missing (`hi - lo` overflows). On the domain |
| all incomes null | agree (no row) |
| ties `[3, 3, 1, 3]`; `[0.1, 0.3]` | agree |
| `[1e308, -1e308, 30, 29.999999999999996]` | DIFFER by row order only |
| flag ON with a supplied table with groups 1 to 5 | DIFFER as intended: Python returns the supplied 5 rows, SAS the test medians (1 row) |

### S25: `predict_run_03_cleaned` against `test_cleaned`

| Input (`age`, `MonthlyIncome`, `NumberOfDependents`) | Result |
|---|---|
| Edge (frame after step 01) | agree |
| 9 rows: ages at every boundary, 1e308, -1e308; incomes null, NaN, 1e308; dependents null, NaN, 1e308 | agree |
| `[null]`, `[1]`, `[0]` | DIFFER: Python `age_group` 5.0, SAS 1.0. Outside the domain. **Smallest witness** (the one of the pilot S3b) |
| `[NaN]`, `[1]`, `[0]` | agree |
| `[25]`, text `["x"]`, `[0]` | DIFFER: Python `MonthlyIncome_missing` 0, SAS 1.0. The Python precondition accepts a text `MonthlyIncome`; SAS reads a text cell as a missing number. On the domain (age present) |
| `[25]`, text `[null]`, `[0]` | agree |
| frame that already has `Dependents_missing`, `age_group` columns | agree |
| zero rows | agree |

### S26: `predict_run_04_imputed` against `test_imputed` (arrange = identity)

`zz_pr_c ag mm inc util dr` is a cleaned frame (other columns constant 1); `zz_pr_m ag med` a medians frame.

| Input | Result |
|---|---|
| Edge (cleaned frame, Python medians) | agree |
| 4 rows, groups `[1, 2, 5, 2]`, flags `[1, 0, 1, 1]`, null utilization / debt ratio, medians for groups 2 and 5 (group 1 has none: income stays missing) | agree |
| utilization `1e308` | DIFFER: Python `credit_utilization` `+inf`, SAS missing. On the domain. **Smallest witness (overflow)** |
| utilization and debt ratio NaN | DIFFER: Python NaN, SAS missing. On the domain |
| left `age_group` null, right `age_group` null with median 20, flag 1 | DIFFER: Python `monthly_income` missing (null keys do not match), SAS 20.0 (missing = missing). On the domain as written (not reachable from step 03) |
| medians with a duplicated group `[2, 1, 2]` | agree (row repeated on both sides, same order) |
| `MonthlyIncome_missing` null | agree |
| empty medians | agree |
| left frame with its own column `median_income` = 99, flag 1, median 20 | DIFFER: Python `monthly_income` 99.0 (the left column; the right one is renamed `median_income_right`), SAS 20.0. On the domain as written |
| medians frame with an extra column `age` | agree |
| `-0.0`, `1e-320` | agree |
| zero rows | agree |

### S27: `predict_run_05_features` against `test_features`

`zz_pr_i1 age inc dep l30 l60 l90 util dr ncl` is a one-row imputed frame; base row
`45, 5000, 2, 1, 0, 1, 80, 50, 4`.

| Input | Result |
|---|---|
| Edge (imputed frame), `full` true and false | agree |
| base row | agree |
| income missing (allowed by the domain), both `full`; also with utilization 250, debt ratio 600 | agree (`flag_low_income` is 1 on both sides) |
| age missing | DIFFER: `age_category` Python 5.0, SAS 1.0. Outside. **Smallest witness for part (b)** |
| dependents missing; each late-payment count missing; all three missing | agree |
| utilization missing | DIFFER: `credit_util_category` Python 4.0, SAS 1.0. Outside. `credit_utilization_capped` agrees: `min(., 200) = 200` on both sides |
| debt ratio missing | DIFFER: `debt_category` Python 4.0, SAS 1.0. Outside |
| credit lines missing | DIFFER: `flag_few_credit_lines` Python 0, SAS 1.0. Outside |
| NaN in one column at a time | DIFFER in each case (Python keeps NaN and treats it as greater than every number, SAS gives missing / false), e.g. utilization NaN: `flag_high_utilization` Python 1.0, SAS 0; `credit_utilization_capped` Python 200.0, SAS NaN. On the domain |
| age 1e308 and income 1e308 | DIFFER: `age_income_interaction` Python `+inf`, SAS missing. On the domain |
| dependents and two late counts 1e308 | DIFFER: `total_late_payments` Python `+inf`, SAS missing, then 5 derived cells. On the domain |
| utilization, debt ratio, credit lines 1e308 | agree |
| negative values; `1e16, 1, -1e16` late counts (both `full`); thresholds exactly at 2500, 30, 43, 75, 60 | agree |
| 7 rows at every category boundary, both `full` | agree |
| frame with stray columns `financial_health` (text), `has_delinquency`, `log_monthly_income`, `total_late_payments`, `flag_low_income` | agree |
| zero rows | agree |

### S28: `predict_run_06_score` against `test_scored (test_scored_temp model ·)`

| Input | Result |
|---|---|
| Edge (features frame), the 18-term model | agree |
| `x` Float64 with null, `y` Int64 with null, a text column, coefficients `0.1`, `-0.3` | agree (a missing model variable gives a missing probability on both sides) |
| `exp` overflow: coefficient `-1`, `x = 710, 709, 745, -745, 1e308, -1e308` | agree (missing where `exp` overflows) |
| coefficient `10`, `x = 1e308` | DIFFER: Python `pd_logistic` 1.0 (logit `+inf`, `exp(-inf) = 0`), SAS missing (the product overflows). **Smallest witness** |
| coefficient `10`, `x = -1e308`; `x = NaN` | agree (missing) |
| intercept 1e308, `x = 1e308` | DIFFER as above |
| intercept NaN | agree |
| no coefficient; coefficient 0 | agree |
| `0`, `-0.0` | agree |
| coefficients named `predicted_logit` and `pd_logistic`, both already columns | agree |
| zero rows; `1e16 + 1 - 1e16` in model order | agree |

### S29: `predict_run_07_predictions` against `test_predictions`

| Input (`pd_logistic`) | Result |
|---|---|
| Edge (scored frame) | agree |
| 20 values in [0, 1] including every grade boundary and `0.49999999999999994` | agree |
| `[null]` | agree: `pred_logistic` 0, score missing, grade F, Decline (I6) |
| `[NaN]` | DIFFER: Python `pred_logistic` 1.0, score NaN, grade A, Approve; SAS 0, missing, F, Decline |
| `[1e308]` | DIFFER: Python score `-inf`, SAS missing (both grade F) |
| `[-1e308]` | DIFFER: Python score `+inf`, grade A; SAS missing, F |
| values outside [0, 1]: `1.1, 1.2, 1.3, 2, 3.4, -0.5, -3, 3.398, 3.399`; `-4e15, -4e16, -1e300` | agree |
| `[-3999999997.6]` (score exactly 1000000000250) | DIFFER: Python `credit_risk_score` 1000000000251, SAS 1000000000250. `sas_round` rounds an integer up as soon as `1e-12 * a >= 0.5`, that is at or above 5e11; SAS returns an integer unchanged. A difference of the mathematics (not of floating point). Not a probability |
| 11 values around the grade boundaries | agree |
| frame with stray columns `base_rate` (text), `risk_grade`, `score_range` | agree |
| zero rows | agree |

### S30: `predict_run_08_outputs` against `kaggle_submission` and `test_predictions_full`

| Input | Result |
|---|---|
| Edge (predictions frame) | agree, both files |
| `[("x", [1])]` (no kept column) | DIFFER, both files: Python 0 rows, SAS 1 row with no column. **Smallest witness, for every number type** |
| `[("age", [1])]` | first file DIFFER (0 rows / 1 empty row), second agree |
| ragged frame `zz` 2 rows, `row_id` 1 row, `age` 2 rows | DIFFER: Python 1 row, SAS 2 rows |
| 2 rows, null / NaN / 1e308, text and Int64 columns | agree |
| zero rows; duplicated column name | agree |

The step has no precondition item, so nothing excludes these frames.

### ST4: `run_py_py` (flag off) against the composition of the SAS units

`zz_pr_st4 full intercept coefficients medians flag cs` compares the two files.

| Input | Result |
|---|---|
| Edge, `full` true and false | agree, both files |
| 4 rows, ages `45, 35, 36, 38`, one income `NA`, even-count median | agree |
| one row, age missing | agree (`age_category` is not an output) |
| 2 rows: age missing with income `NA`; age 25 with income 3000 | DIFFER: `monthly_income` Python missing (group 5 has no median), SAS 3000.0; `total_risk_flags` 1.0 / 0. Outside the domain |
| utilization missing | DIFFER: `pd_logistic` (through `credit_util_category`). Outside |
| debt ratio missing; each late count missing; credit lines missing; real-estate loans missing; `VAR1`, income and dependents missing | agree |
| utilization 1e308; debt ratio 1e308; two late counts 1e308 | DIFFER (5 cells in `test_predictions.csv`, `pd_logistic` in both files). On the domain |
| credit lines 1e308; real-estate loans 1e308; income `"9999...9"` (32 digits) | agree |
| age NaN; real-estate loans NaN | agree |
| utilization NaN | DIFFER. On the domain |
| model `[("age", 1e308)]` (overflow at scoring) | DIFFER: Python `pd_logistic` 1.0, `pred_logistic` 1.0, grade D; SAS missing, 0, F |
| model `[("monthly_income", 1.0)]`, income missing (a missing model variable) | agree (missing probability, predicted 0, grade F on both sides) |
| raw table with an extra numeric column `median_income` (99, 98), one income `NA` | DIFFER: `monthly_income` Python 99.0, SAS 5000.0 (the test median), then `pd_logistic`, the score, `total_risk_flags`. On the domain as written; a real cs-test.csv has no such column |
| raw table with extra columns `age_group`, `pd_logistic`, `row_id`, `monthly_income` | agree |
| two rows with 98 late payments, `full` false | agree |
| flag ON with a supplied table (groups 1 to 5) | DIFFER as intended (rows with a missing income only) |

### S31: the twins of feature engineering and predict, on the same input (frames compared with their column types)

| Pair | Inputs | Result |
|---|---|---|
| `fe_run_01_clean` / `predict_run_01_clean` | Edge raw frame; non-text columns; pre-existing `_num` columns | equal |
| `fe_run_02_income_medians` / `predict_run_02_medians none · false` | Edge; 7 rows with null, NaN, 1e308, -1e308 in both columns; a frame with a stray text column `age_group`; zero rows; all incomes null; flag on with `medians = none` | equal (the two copies filter and add `age_group` in opposite orders: no effect) |
| same, flag on with a supplied table | | DIFFER as intended |
| `fe_run_03_cleaned` / `predict_run_03_cleaned` | Edge; null, NaN, 1e308 in every column; stray columns | equal |
| `fe_run_04_imputed` / `predict_run_04_imputed` | one row | DIFFER by the column `default_flag` only (15 columns against 14) |
| same, after dropping `default_flag` from the fe result | Edge; 4 rows with null keys, null flag, 1e308, NaN, duplicated groups; stray `median_income`; stray `default_flag` | equal. Without the column `SeriousDlqin2yrs` (excluded by the fe precondition) the fe result has empty columns |
| `fe_run_05_features` / `predict_run_05_features` | Edge, `full` true and false | DIFFER: `flag_low_income` and `total_risk_flags` on the 5 rows whose income stayed missing (fe 0, predict 1) |
| same | base row, `full` true/true, false/false, true/false | equal |
| same | income missing | DIFFER: `flag_low_income` fe 0, predict 1; `total_risk_flags` fe 3.0, predict 4.0. **Smallest witness** |
| same | age present or not with every other column missing; all NaN; all 1e308; `1e16, 1, -1e16`; stray columns; zero rows | equal |

The other textual differences of the two copies have no effect at `Float`: `fh - 15` with an
integer literal (fe) against the Float64 literal `15.0` (predict), `sas_sum` / `sas_max` /
`sas_min` called with `full` (fe) against `true` (predict) on 2 or 3 operands, three against four
`with_columns` blocks.

### F2, I2, I3, I6 (evaluated properties)

- F2 frame, `zz_pr_onoff` (stage with the flag on against off, same supplied table):
  Edge with medians `1..5 -> 10..50`: the files differ on rows 4, 8, 9, 15, 18, 19, 25, 27, 29,
  31, 32 (0-based), exactly the 11 rows whose income is `NA`. Supplied table with a null median for
  group 4: only the `NA` row changes (to missing). Supplied table with extra columns: no change on
  a row with an income. **Supplied table with a duplicated group `[1, 2, 3, 4, 5, 3]` and one test
  row of age 45 with income 5000: flag on gives 2 rows, flag off 1 row.** The precondition accepts
  it (the Python test is on the set of values), so a row whose income was present changes.
- I2: flag off with a supplied table: the unit returns the test medians (1 row `(3, 7.0)`), not
  the supplied 5 rows. Flag on: returns the supplied table.
- I3 (predict): one row with income, dependents, utilization and credit lines missing gives
  `flag_low_income` 1.0 with `monthly_income` missing; `flag_high_utilization`,
  `flag_many_dependents`, `flag_few_credit_lines` are 0. The fe twin gives `flag_low_income` 0.
- I6: `pd_logistic = [null, 0.7]` gives `pred_logistic` 0, score missing, grade F, Decline on the
  first row; 1.0, 675, C, Review on the second.
- Imputation: 3 rows (age 25 `NA`; age 45 `NA`; age 46 income 7), flag off: incomes
  `missing, 7.0, 7.0`; flag on with medians `10..50`: `10.0, 30.0, 7.0`.

### Precondition pairs seen

- Step 03: the Python precondition accepts `MonthlyIncome` of any type; the SAS one requires a
  numeric cell. On a text column the two results differ.
- Step 04: the Python precondition accepts a `median_income` column in the left frame and null
  join keys; the SAS unit reads the right table's `median_income` and matches missing keys.
- Step 05: the SAS precondition requires the 27 output columns absent; the Python one does not
  (results agree on the inputs tried).
- Step 06, 07: the SAS preconditions ask only numeric cells; the Python ones also ask distinct
  names and equal lengths.
- Step 08: no Python precondition; the SAS `kaggle_submission_precond` exists.
- Step 02 with the flag: the Python precondition accepts duplicated age groups in the supplied
  table.

### Phase 3: statements corrected and results (at the real numbers unless said otherwise)

Changes to the statements since the evaluation above:

- S23 is now two items: `..._S23` is part (b); `..._S23a` adds the D_predict condition that
  NumberOfDependents (read with the SAS conversion) is at least 0.
- S25a also carries "NumberOfDependents at least 0"; the text-`MonthlyIncome` witness
  (age 25, dependents 0) satisfies it.
- S26a carries the whole of D_predict on the cleaned table (age, utilization, debt ratio, the three
  late counts and the credit-line count present; the four counts and NumberOfDependents at least
  0). The null-key witness was adjusted: every such column equals 1.
- S26a, S26b, ST4 write the constraint on `arrange` as `test_imputed_precond arrange`.
- S31 step 04 and I8 are stated as written (full equality, no column dropped). Both are false:
  the feature-engineering twin has the extra column `default_flag`. This is a second place where
  the copies differ, not named by the row; apart from that column the frames agreed on every
  input evaluated.

Formal results:

| Contract | Result | Witness / note |
|---|---|---|
| S23(b), S23(a) | stated, not settled | no difference found by evaluation |
| S24(a) | stated, not settled | Float witness: ages 45, 35 (row order). A proof of the negation needs real comparisons and the SAS sort evaluated symbolically on both sides |
| S24(b) | disproved | age missing, income 5: age_group 5 / 1 |
| S25(a) | disproved | age 25, text MonthlyIncome "x", dependents 0: MonthlyIncome_missing 0 / 1 |
| S25(b) | disproved | age missing: age_group 5 / 1 |
| S26(a), S26(b) | disproved | null age_group on both sides, median 20, flag 1: monthly_income missing / 20 |
| S27(a) | stated, not settled | on the domain the only differences found at Float are NaN and overflow, which do not exist at the reals |
| S27(b) | disproved | the nine input columns null: age_category 5 / 1 |
| S28 | stated, not settled | differences at Float only (overflow) |
| S29 | stated, not settled | Float witness pd = -3999999997.6 (score 1000000000250, Python adds 1); not negated |
| S30 | disproved (every number type) | frame with the single column x: 0 rows / 1 row |
| ST4 | stated, not settled | Float witness: raw column `median_income`; not negated |
| S31 step 01, 03 | proved for every number type | by definition |
| S31 step 02 | stated, not settled | equal on every input evaluated |
| S31 step 04 | disproved | 15 columns against 14 (`default_flag`) |
| S31 step 05 | disproved | the nine input columns null: flag_low_income 0 / 1 |
| S31 step 05 `_rest` | stated, not settled | equal on every input evaluated |
| F2 on | proved for every number type | |
| F2 frame | stated, not settled | Float witness: duplicated age group, 2 rows / 1 row; negation withdrawn |
| I2 off | disproved | age missing, income 7, supplied groups 1 to 5: returned age_group [5] |
| I2 on | proved for every number type | |
| I3 | disproved | nine input columns null: flag_low_income 1 with monthly_income missing |
| I6 | disproved | pd_logistic null: pred_logistic 0 |
| I8 | disproved | one raw row, all twelve columns null, input_best32 the identity: flag_low_income 0 / 1 (and `default_flag`) |
| C3 | proved for every number type | |

Obstacle met for ST4 and F2 frame: at the reals the output of step 05 cannot be evaluated by
definitional reduction, because the shape of several columns goes through
`Pl.scalarZero [some c]`, a comparison of real literals (`RealLike.eqb c 0.0`) that the kernel
cannot decide. The preconditions of steps 06 and 07 (all columns of the step-05 output have the
frame's length; `pd_logistic` is Float64) therefore need a symbolic evaluation of step 05.

---

# Group: Helpers (H1 to H12, C2)

## Pairings by evaluation: helpers (H1 to H12, C2)

Carrier `def:zz_he` of blueprint `py-credit-risk-port`, evaluated at `Float` with `eval_decl`.
Numbers are compared through `Float.toBits`; `.` is a polars null on the Python side and the
missing value on the SAS side. "Float only" means the two sides agree at the real numbers and
differ on machine numbers; "at the reals" means the difference does not depend on rounding.

How each helper is evaluated. The Python helper is an expression. Its operands are Float64
columns of a frame built from the listed values (`Pl.col`), or literals (`ExprOrNum.float`,
`ExprOrNum.int`, `pl.lit`), and it is evaluated in select context (`eval none`), or in group
context for the SQL aggregates (`eval (some gs)`). The SAS rule is applied row by row (group by
group) to the same values.

Shorthand: NaN = `0.0/0.0`, inf = `1.0/0.0`.

### H1 `lt`, `le`, `gt`, `ge`, `eq` against `Sas.lt/le/gt/ge/eq`

Inputs tried, column against column (16 rows): (1,2) (2,1) (2,2) (.,1) (1,.) (.,.) (NaN,1)
(1,NaN) (NaN,NaN) (.,NaN) (NaN,.) (inf,1) (-inf,1) (inf,inf) (-0.0,0.0) (0.0,-0.0).
Column against a float literal 2500.0 and against NaN; column against an integer literal
(2500, 0, 750, 1, -3); float literal 2.0 on the left; Int64 against Int64, Int64 against
Float64, Boolean against Float64, Null-dtype against Float64 columns; 0 rows, 1 row.

| Helper | Outcome | Smallest witness of a difference (Python / SAS) | Where |
|---|---|---|---|
| `lt` | agree on every input without NaN, the result is never null | x = 1, c = NaN: true / false | Float only (`Pl.fLt` orders NaN above every number, `Sas.lt` uses `decide (x < y)`) |
| `le` | same | x = 1, c = NaN: true / false; x = NaN, c = NaN: true / false | Float only |
| `gt` | same | x = NaN, c = 1: true / false | Float only |
| `ge` | same | x = NaN, c = 1: true / false; x = NaN, c = NaN: true / false | Float only |
| `eq` | same | x = NaN, c = NaN: true / false | Float only (`Pl.fEq`: NaN equals NaN) |

Covered and equal on both sides: `le` and `eq` (the two "unverified" helpers), missing against a
number (missing is smaller), missing against missing (`lt` false, `le` true, `eq` true,
`ge` true, `gt` false), infinities, zeros of both signs (equal), integer and Boolean columns,
literals on either side, the empty frame. A string column is compared as text by the Python
helper; the SAS rule is numeric, so that case has no SAS value.

### H2 `flag` against `Sas.ofBool`

Inputs: [true, false, true], [true], [false], [], and with a null condition [true, false, null].
Outcome: agree. The Python column is Int64 (1, 0); cast with `Pl.ofInt` it is 1.0 and 0.0, the
bits of `Sas.ofBool`. A null condition gives 0 in Python; SAS has no missing Boolean, so there is
no SAS value to compare (recorded, not a difference).

### H3 `div` against `Sas.div`

Inputs (24 rows, column against column): the 16 rows of H1, then (1,0) (0,0) (.,0) (1,-0.0)
(1e308, 1e-10) (1,3) (-7, 1e-320) (5e-324, 2). Column against the float literals 100.0, 0.0,
-0.0, 1e-10; against the integer literals 100, 0, -4; float literal 2.0 and 1e308 on the left;
Int64 columns; 0 rows, 1 row.
Outcome: agree on every input, bit for bit. Divisor 0 and -0.0 give missing on both sides; a
missing operand gives missing; overflow (1e308 / 1e-10, -7 / 1e-320) gives missing on both sides
(the Python helper tests `isfinite` itself); NaN and infinite operands give missing on both sides.
No difference found, at Float or at the reals.

### H4 `sas_sum` against `Sas.sumFn`, both values of `full`

Inputs: 1, 2, 3, 5 and 8 operand columns, each with `full = true` and `full = false`; a column
and a literal in either order; 0 rows, 1 row.

| Input | Python | SAS | Where |
|---|---|---|---|
| sum(., 1) | 1 | 1 | agree |
| sum(., .) and all missing with 3, 5, 8 operands | . | . | agree |
| sum(1, ., 2), sum(., 1, .), sum(., ., ., ., 7) | 3, 1, 7 | same | agree |
| sum(-0.0, .), sum(., -0.0) | +0.0 (bits 0) | -0.0 (bits 9223372036854775808) | Float only: polars counts a null as 0.0 and adds it |
| sum(1e308, 1e308) | inf | . | Float only: `Sas.fin`; polars keeps inf |
| sum(NaN, 1), sum(inf, 1), sum(inf) with one operand | NaN, inf, inf | . | Float only |
| sum(1e16, 1, 1), both `full` | 10000000000000002 (…201) | 1e16 (…200) | Float only: polars adds a + (b + c), SAS (a + b) + c |
| sum(1, 1, 1e16), both `full` | 1e16 | 10000000000000002 | Float only |
| sum(0.1, 0.2, 0.3) | 4603579539098121011 | 4603579539098121012 | Float only, one unit in the last place |
| sum(1e308, 1e308, -1e308) | 1e308 | . | Float only: the SAS left fold overflows first |
| sum(1e16, 1, -1e16, 1, 1), `full = true` | 2 | 2 | agree |
| sum(1e16, 1, -1e16, 1, 1), `full = false` | 0 | 2 | Float only; the two values of `full` give different Python results |
| sum(1, 1, 1e16, 1, 1), `full = false` | 10000000000000002 | 10000000000000004 | Float only |
| sum(0.1, …, 0.8), 8 operands, both `full` | 4615288898129284301 | 4615288898129284300 | Float only |

No difference at the reals: every difference above is an order of additions, the sign of a
zero, or a non-finite result.

### H5 `sas_min`, `sas_max` against `Sas.minFn`, `Sas.maxFn`

Inputs: 1, 2, 3, 5, 9 operand columns with both values of `full`; a column and `pl.lit(200.0)`
or `pl.lit(0.0)` in either order (the two forms the port uses); 0 rows, 1 row.
Outcome: `min(., 200) = 200`, `max(0, .)`, all missing gives missing, zeros of both signs,
infinities: agree. Difference only with NaN:

| Input | Python | SAS | Where |
|---|---|---|---|
| min(NaN, 1), max(NaN, 1) | 1 | NaN | Float only: polars ignores NaN, the SAS fold keeps a NaN it starts from |
| min(NaN, 2, 3) | 2 | NaN | Float only |
| min(x, 200.0) with x = NaN | 200 | NaN | Float only |

No difference at the reals.

### H6 `sas_log` against `Sas.log`

Inputs: 1, e, 0, -0.0, -1, ., 5e-324, 1.7976931348623157e308, NaN, inf, -inf; float literals
2.0, 0.0, -3.0; integer literals 2, 0, -3; 0 rows, 1 row.
Outcome: `log(0) = .`, negative and missing give missing, positive values agree bit for bit.

| Input | Python | SAS | Where |
|---|---|---|---|
| NaN | NaN (bits 9221120237041090560) | . | Float only: `NaN > 0` is true in the polars order |
| inf | inf | . | Float only: `Sas.fin` |

### H7 `sas_exp` against `Sas.exp`

Inputs: 0, 1, -1000, 709, 709.782712893384, 709.7827128933841, 710, 1000, ., -0.0, -745.2, NaN,
inf, -inf; literals 1.0, 710.0, 1, 710; 0 rows, 1 row.
Outcome: agree on every input. Overflow (709.7827128933841, 710, 1000, inf) gives missing on
both sides, NaN gives missing on both sides, underflow gives 0. No difference found; both sides
apply the same finiteness test to the same `exp`.

### H8 `sas_round` against `Sas.round`

Inputs: exact halves 0.5, 1.5, 2.5, 3.5, 849.5 and negative halves -0.5, -1.5, -2.5; integers;
0.4, 0.6; 2.4999999999999996; values at and above 2^52 (4503599627370496, …497, 9007199254740992,
1e300, negatives); values just below 2^52; the tolerance edges below; NaN, inf, -inf; -0.0;
literals.
Agree: every exact half (away from zero), negative halves, integers below 5e11, everything at or
above 2^52 (unchanged), 2.4999999999999996 (3 on both sides), inf, -0.0, missing.

| Input | Python | SAS | Where |
|---|---|---|---|
| 0.4999999999994 (bits 4602678819172636104) | 1 | 0 | at the reals: Python treats a fraction within 1e-12 * max(1, abs x) of one half as a half, SAS adds min(1e-6, abs x * 1e-12), which is below 1e-12 when abs x < 1 |
| 0.499999999999 (0.5 - 1e-12) | 1 | 0 | at the reals |
| 500000000000 (integer) | 500000000001 | 500000000000 | at the reals: the Python tolerance reaches one half at 5e11, so every integer in [5e11, 2^52) gets 1 added; SAS returns an integer unchanged |
| 1000000000250, 1e12, 1e15, 4503599627370495 | x + 1 | x | at the reals |
| -1000000000250 | -1000000000251 | -1000000000250 | at the reals |
| 600000000000.25 | 600000000001 | 600000000000 | at the reals |
| 4500000000000.499 | 4500000000001 | 4500000000000 | at the reals |
| 2000000.4999985 | 2000001 | 2000000 | at the reals: above 1e6 the SAS tolerance is capped at 1e-6, the Python one is not |
| 999999.499999 | 999999 | 1000000 | Float only: the SAS sum `(a + 0.5) + eps` rounds up to 1000000 |
| 1000000.499999 | 1000000 | 1000001 | Float only, same reason |
| NaN | NaN | . | Float only: `Sas.fin` |

Not a difference at Float although it is one at the reals: 0.4999999999995 (both give 1 at Float
because the SAS sum rounds to 1.0; at the reals the SAS sum is below 1).

### H9 `sql_sum`, `sql_mean`, `sql_min`, `sql_max` against `Sas.sqlSum/sqlMean/sqlMin/sqlMax`

The SAS parameter `agg` is unknown at Float; the carrier uses a left fold from the first value
(sum) and that sum divided by the count (mean). Differences of one unit in the last place
therefore say nothing; missing values, non-finite results and NaN do.
Inputs: column [1, 2, ., 4, ., .] with groups {0,1} {2,3} {4,5} {} {0..5} {3}; the empty frame
(select context: zero rows) and zero groups; an all-missing column with groups {0,1} {0} {};
[1e308, 1e308, -0.0, NaN, 1, 0.1, 0.2, 0.3] with several groups; one row; group indices outside
the column.

| Case | Python | SAS | Where |
|---|---|---|---|
| zero rows (select context), all four | . | . | agree |
| empty group, all four | . | . | agree |
| all-missing group or column, all four | . | . | agree |
| mixed groups (missing skipped) | equal bits | | agree |
| sum, mean over {1e308, 1e308} | inf | . | Float only: `Sas.fin` |
| sum, mean over a group with NaN | NaN | . | Float only |
| sum over {0.1, 0.2, 0.3} | …011 | …012 | Float only, and depends on `agg` |
| min, max over {NaN, 1} | 1 | NaN | Float only: polars ignores NaN |
| min, max over {1, NaN} | 1 | 1 | agree |

No difference at the reals with `agg` the real sum and mean.

Artifact of the evaluation, not a finding: a group index outside the column is not a group of a
frame. With such an index and a column without nulls, `Pl.groupMean` counts the absent row as a
value 0 (`mean` of column [2] with indices {0, 5}: Python 1, SAS 2). The statements therefore take
the groups as lists of `Fin xs.length`, valid by construction; with valid indices (repeated or
not) the two sides agree ([2, 4, ., 6] with groups {0,0} {1,3,3} {2,2} {3,2,1}: equal bits).

### H10 `merge_one_to_one` against `Sas.merge11`

Each frame is given to `Sas.merge11` as (its variables with a missing cell of their type, its
rows `Pl.toTable f`). All inputs meet `merge_one_to_one_precond`.
Inputs: different lengths (2 and 1; 1, 3 and 2 with a text and an integer column); an input with
no row, first and last; no input; an input with no column; all inputs empty; a Null-dtype column
in a frame of the greatest height; a name twice in one frame; the four frames of the model
summary; the same variable in two inputs.

| Input | Python | SAS | Where |
|---|---|---|---|
| a = [1, 2]; b = [5] | rows (1, 5), (2, .) | same | agree |
| three inputs of lengths 1, 3, 2 | 3 rows, missing on the extra rows | same | agree |
| an input with no row, either position | its variables missing | same | agree |
| v = [1, 2]; then v = [9] | v = 9, . | v = 9, 2 | at the reals (no arithmetic): Python overwrites with the padding null, SAS keeps the value the other input set once the later input has run out (x15 `X15A`) |
| v = [1, 2]; then v = [] | v = ., . | v = 1, 2 | at the reals |
| v = [9]; then v = [1, 2] | v = 1, 2 | same | agree |
| (v, w) = [(1, 3), (2, 4)]; then (w, z) = [(9, 0)] | row 2: w = . | row 2: w = 4 | at the reals |

### H11 `proc_rank_groups` against `Sas.rankGroups`

All inputs meet `proc_rank_groups_precond`. Inputs: ten distinct values with k = 10, ascending
and descending; all values equal; ties across a group boundary ([0.1, 0.5, 0.5, 0.9] with k = 2,
[0.1, 0.5, 0.5, 0.5, 0.9, 0.95] with k = 3, nine values with ties and k = 10 descending and
k = 4); missing values ([0.3, ., 0.1, ., 0.2]); all missing; no row; one row; k = 0 and k = 1;
infinities and zeros of both signs; NaN.
Outcome: agree bit for bit on every input without NaN (tied values share a group, a missing
value has a missing group, n counts present values only).

| Input | Python | SAS | Where |
|---|---|---|---|
| [1, NaN, 2], k = 2 | 0, 1, 1 | 0, 0, 1 | Float only: polars ranks NaN greatest, the SAS count gives it rank 0.5 |
| [NaN, NaN, 2], k = 3, descending | 1, 1, 2 | 0, 0, 0 | Float only |

### H12 `roc_association` (Area) against `Sas.rocArea (Sas.rocObs …)`

The SAS observations are read from the table with the two columns `default_flag`, `pd_logistic`.
All inputs meet `roc_association_precond`. With and without a label the seven statistics are the
same.

| Input (default_flag; pd_logistic) | Python Area | SAS Area | Where |
|---|---|---|---|
| [0,1,0,1,1,0]; [0.1,0.9,0.4,0.35,0.8,0.2] | bits 4606181618882823964 | same | agree |
| [1,0,1,0]; [0.3,0.3,0.6,0.1] (exact tie) | 0.875 | same | agree |
| [0,1]; [0.5,0.5] | 0.5 | 0.5 | agree |
| [0,1]; [0.5, 0.500000005] (gap 5e-9) | 0.5 | 0.5 | agree |
| [0,1]; [0.5, 0.50000002] (gap 2e-8) | 1 | 1 | agree |
| [0,1]; [0.5, 0.5000000102] (gap 1.02e-8) | 1 | 0.5 | at the reals: Python ties within 1e-8, SAS within 1.0536712127723509e-8 |
| [1,0,0]; [0.5, 0.500000006, 0.500000012] | 0.25 | 0 | at the reals: Python ties pair by pair, SAS groups from the largest value of a group |
| [0,1,1]; same scores | 0.75 | 1 | at the reals |
| [1,2]; [0.9,0.1] | . | 1 | at the reals: Python drops a response that is neither 0 nor 1, SAS counts it as a non-event |
| [1,2,0]; [0.5,0.9,0.1] | 1 | 0.5 | at the reals |
| [1,0,0]; [NaN,0.9,0.1] | 1 | 0.5 | Float only |
| Int64 response with missing values, Boolean response, Int64 score | equal | | agree |

### C2 `roc_association` on a single-class input

"Single class" is evaluated as: among the rows with a present `pd_logistic`, no row has
`default_flag = 1`, or no row has `default_flag = 0` (the two-class clauses of the SAS
preconditions `roc_stats_precond`, `roc_train_precond`, `roc_valid_precond` fail).

| Input (default_flag; pd_logistic) | Python [Area, StdErr, LowerArea, UpperArea, SomersD, Gamma, TauA] | SAS Area |
|---|---|---|
| [1,1]; [0.3,0.7], with and without label | ., ., ., ., ., ., 0 | . |
| [0,0,0]; [0.3,0.7,0.1] | ., ., ., ., ., ., 0 | . |
| [1]; [0.3] | all . | . |
| no row | all . | . |
| [1, ., 0]; [0.3, 0.2, .] (one usable row) | all . | . |
| Null-dtype response | all . | . |
| [1,2]; [0.9,0.1] | all . | 1 |

Outcome: Area, StdErr, LowerArea, UpperArea, SomersD and Gamma are missing on every single-class
input. TauA is 0, not missing, as soon as two rows are usable (its denominator n(n-1)/2 is then
not zero); it is missing with fewer than two usable rows. Exists at the reals.
Precondition pair: [1,1]; [0.3,0.7] meets `roc_association_precond` and does not meet the SAS
preconditions (no non-event).

### Phase 3 additions

#### Evaluations of the widened forms (Float, before the statements were widened)

| Helper | New operand form | Result |
|---|---|---|
| `eq` | column against `pl.lit(o, Float64)` with `o` present or missing (`Pl.litOptF o`) | agree with `Sas.eq` |
| `div` | column against `Pl.litOptF o`, both orders; Int64 column over Int64 column | agree with `Sas.div` |
| `flag` | Boolean column with nulls | agree with `Sas.ofBool (o.getD false)`: a null condition gives 0 |
| `sas_sum` | k Int64 operand columns | agree with `Sas.sumFn` on the values cast to numbers |
| `sql_sum` | Int64 column, select context (result read through `Pl.Col.asF64`) | agree with `Sas.sqlSum` |

#### Witnesses used in the accepted disproofs (all at the reals)

| Contract | Witness | Python | SAS |
|---|---|---|---|
| H8 `sas_round` | no row; literal operand 500000000000 | 500000000001 | 500000000000 (unchanged) |
| H10 `merge_one_to_one` | frames `[("v", [0])]` and `[("v", [])]` | v missing | v = 0 |
| H12 `roc_association` | default_flag [1,2]; pd_logistic [1,0]; no label | Area missing | Area 1 |
| C2 `roc_association` | default_flag [1,1]; pd_logistic [0,0]; no label | TauA = 0 | all seven statistics missing is required |

#### Results

| Contract | Item | Result |
|---|---|---|
| H1 | `thm:lt_H1_lt`, `thm:le_H1_le`, `thm:gt_H1_gt`, `thm:ge_H1_ge`, `thm:eq_H1_eq` | proved at the reals |
| H2 | `thm:flag_H2` | proved at the reals |
| H3 | `thm:div_H3` | proved at the reals |
| H4 | `thm:sas_sum_H4` | proved at the reals (any bracketing of the horizontal sum equals the left fold) |
| H5 | `thm:sas_min_H5_min`, `thm:sas_max_H5_max` | proved at the reals |
| H6 | `thm:sas_log_H6` | proved at the reals |
| H7 | `thm:sas_exp_H7` | proved for every number type |
| H8 | `neg:sas_round_H8_neg` | disproved |
| H9 | `thm:sql_min_H9_min`, `thm:sql_max_H9_max` | proved at the reals |
| H9 | `thm:sql_sum_H9_sum`, `thm:sql_mean_H9_mean` | proved at the reals, under the parameter links `agg.sum l = l.sum` and `agg.mean l = l.sum / l.length` |
| H10 | `neg:merge_one_to_one_H10_neg` | disproved |
| H11 | `thm:proc_rank_groups_H11` | not settled (stated; every evaluation above agrees) |
| H12 | `neg:roc_association_H12_neg` | disproved |
| C2 | `neg:roc_association_C2_neg` | disproved |

Operations that differ in floating point and coincide at the reals: the polars select-context
sum (128-element blocks in 16 stripes, combined pairwise), the Kahan sum of the group context,
the bracketing of `pl.sum_horizontal` / `pl.min_horizontal` / `pl.max_horizontal`, the NaN
branches of the polars comparisons and of min/max, and the finiteness guards of the SAS rules.
