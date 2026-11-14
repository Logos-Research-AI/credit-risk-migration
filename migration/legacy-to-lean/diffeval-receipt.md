# Differential evaluation receipt

Method. Each accepted Lean unit is run at `α = Float` through `eval_decl` and the result is read
back as IEEE bit patterns (`Float.toBits`), so the comparison is exact wherever SAS's exact
value is known. SAS's exact values come from staged runs of the **unmodified** scripts on SAS
OnDemand (`migration/run_stage.py`: only the two path macros are redirected; every work data
set is then dumped in HEX16.). Where only the reference CSVs exist, values are compared to
printed precision (BEST12., `8.4`, `percent8.2`); flags, counts, categories, text and
missing-ness are always compared exactly. Scripts: `migration/eval_fe.py`, `eval_scoring.py`,
`eval_metrics.py`, `eval_misc.py`. The comparator was validated on planted mismatches
(below) before its verdicts were used.

## Runs

| Chain / units | Input | SAS side | Rows | Cells | Differences |
|---|---|---|---|---|---|
| credit_raw_clean, credit_cleaned, credit_imputed, credit_features | 600 raw training rows (150 chosen for missing income, missing dependents, utilization above 100%, debt ratio above 500%, age under 22, zero income, 90-day lates; 450 random); medians of the full file | `judge/reference/model_features_*.csv` | 600 | 25,200 | 0 |
| same, the 40 rows of experiment X04 | raw rows | HEX16 of credit_utilization, debt_ratio, utilization_debt_interaction | 40 | 120 | 0 (bit-exact) |
| logit_scored_valid_temp, logit_scored_valid, risk_scores_validation, risk_scores_validation_clean | 300 reference validation rows (100 nearest a score half-point or pd 0.5) and the fitted model of staged run t1 (HEX16 coefficients) | `risk_scores_validation.csv` | 300 | 15,300 | 0 |
| logit_scored_train_output (invLink := 1/(1+exp(-x))), logit_scored_train, risk_scores_train, risk_scores_train_clean | 300 reference training rows, same model | `risk_scores_train.csv` | 300 | 15,300 | 0 |
| final_model_output | same | `final_model_output.csv` | 300 | 3,900 | 0 |
| test_raw_clean .. test_predictions_full (the ten units of predict.sas) | 300 raw test rows | `test_predictions.csv` | 300 | 4,500 | 0 |
| kaggle_submission | same | `kaggle_submission.csv` | 300 | 600 | 0 |
| the ten units of predict.sas, scenario `edge_predict` | 300 raw rows, 186 of them with no median for their age group | scenario reference | 300 | 4,500 | 0 |
| kaggle_submission, scenario `edge_predict` | same | scenario reference | 300 | 600 | 0 |
| training_metrics, validation_metrics | confusion matrices of staged run t1 | HEX16 dump | 2 | 8 | 0 (bit-exact) |
| model_summary | ROC areas and metrics of t1 | HEX16 dump (8 values), column order against `model_summary.csv` | 1 | 10 | 0 on the 8 values dumped in full; see note 2 |
| the 17 data sets of metrics_calculation.sas (roc_stats, auc_summary, sorted table, ks_calculation, ks_statistic, threshold_analysis, decile_data, decile_analysis, cumulative_lift, train_bins, valid_bins, psi_calculation, psi_summary, calibration_data, calibration_plot, validation_summary, model_performance_metrics) | staged run m2: 300 validation and 500 training reference rows with planted ties (5-way, 15-way at 0.5, 20-way), 4 missing pd_logistic, 3 missing default_flag | HEX16 dump | 2,765 | 9,831 | 0; 9,644 bit-exact, 187 through the SUM/MEAN parameter (note 3) |
| same 17 data sets | staged runs sa, sb, sc: 260 + 300 rows sampled from the three edge metrics scenarios (pd on coarse grids, heavy ties; PSI 0.0133, 1.6077, 0.3139; statuses Needs Improvement and Requires Review) | HEX16 dumps | about 2,200 each | 20,867 | 0 |
| same 17 data sets | staged run k1: 4 + 5 rows where the KS maximum is attained twice (two-row ks_statistic, two-row merges, second row "Needs Improvement") | HEX16 dump | 39 | 319 | 0 |
| logistic_lackfit | the 1,000 scored rows of experiment X15D (16 distinct probabilities) | `X15D hl` lines | 8 groups | 24 | 0 |
| logistic_association | same | `X15D assoc` lines (HEX16) | 4 | 8 | 0 (bit-exact) |
| Sas.rocArea | X15B sets r1, r2, r3, r4, r6 (near ties 5e-9 and 2e-8 apart, a chain, a reversed pair) | `X15B` lines | 5 | 5 | 0 |
| Sas.rankGroups | X12B, X12E (ties, missing, descending, k = 4 and 10, one row, all equal, all missing) | `X12` lines | 26 | 54 | 0 |
| Sas.freq2 | X13 `freq` (missing levels) | `X13 freq` lines | 7 | 28 | 0 |

Totals: 45 of 56 units evaluated directly against SAS output with zero unexplained differences; about
101,000 cells. Not evaluated against SAS directly, and why: `credit_train_validation` (the split
is a parameter; its body is a filter, reviewed twice), `credit_train_export`,
`credit_validation_export` (identity), `income_medians` and `test_income_medians` (the evaluator
cannot take the 150,000-row table; the median rule is bit-exact on X13/X14, the two units were
run on subsets of up to 1,200 rows against an independent computation by reviewer 1, and the
medians of the full files, computed outside Lean by the same rule, reproduce every imputed
income in the 900 evaluated rows), `confusion_matrix_train`, `confusion_matrix` (their rule
`Sas.freq2` is evaluated, and is exercised bit-exactly inside `confusion_metrics`), `roc_train`,
`roc_valid` (same rule as `roc_stats`, which is bit-exact on five staged runs; the 105,000-row
tables exceed the evaluator), `total_good_bad`, `total_defaults` (macro variables: evaluated
inside ks_calculation and cumulative_lift, which are bit-exact).

## Differences found and how each was resolved

1. **Five cells of `utilization_debt_interaction`** (first run, 400 rows): the Lean value
   printed, for example, 67434.8416225 where the reference has `67434.841623`. Explained, not a
   Lean defect: the double is a decimal half-way case and BEST12. rounds it up. Experiment X04
   had dumped exactly such rows in HEX16; the Lean bits equal SAS's on all 40. Rule recorded:
   R6 evidence; comparator tolerance widened by 4 ulp for decimal ties. No Lean change.
2. **`model_summary`, `valid_recall` and `valid_f1_score`**: the t1 dump line was cut at 256
   characters by the first version of the runner, so only the printed `0.2008` and `0.2968`
   were available for these two. The Lean values (0.2007952286..., 0.2968405584...) pass through
   unchanged from `validation_metrics`, which is bit-exact. Runner fixed (dumps now written to
   files); no Lean change.
3. **Aggregates through the parameter `agg`** (187 cells in m2): with a left-fold sum and
   sum / count passed for `agg`, 167 cells equal SAS to the bit and 20 differ in the last bits
   (all within 1e-9 relative). This is the open parameter P2 doing its job, not a difference
   in the units: the units agree with SAS exactly wherever no SUM or MEAN is involved.

No Lean definition was changed to make an evaluation pass. The three Lean changes made after the
first evaluation came from review findings with their own evidence (amendments A4, A5, A6), and
all runs above were made after them.

## Coverage of the inventory classes

| Class | Reached by |
|---|---|
| MISSING (comparisons, Boolean assignment, SUM/MIN/MAX, truthiness) | edge_predict rows (missing income: `. < 2500`, categories, caps, log of missing), m2 rows with missing pd_logistic and default_flag |
| DOMAIN (division by zero or missing, LOG, EXP) | threshold 0.7 in m2 (precision and F1 missing), income 0 and missing; EXP overflow only by hand evaluation (logit -800) |
| ROUNDING | 200 rows chosen nearest a half-point of the score; X11 thresholds through `Sas.round` (reviewer 1) |
| TIES | m2, sa, sb, sc, k1 |
| AGGREGATE, ALIAS, ROW_ORDER | m2, sa, sb, sc (missing group first, counts vs means, subqueries) |
| FORMAT_ROUNDTRIP | m2 (`overall_default_rate` 0.197987), sb (0.092308), sc (0.119231) |
| ROW_ALIGN (MERGE) | k1 (two KS rows), t1, m2 |
| CHAR_LENGTH, COLUMN_ORDER | every run (column order is part of each comparison) |
| STATE (RETAIN, sum statements) | ks_calculation, cumulative_lift, the metrics steps |
| CLOCK | not compared (parameter P7) |

## Comparator validation (planted mismatches)

Bit-exact comparator: one ulp in a value, a missing replaced by 0, a value replaced by missing,
two rows swapped, a row dropped, two columns reordered: 6 of 6 caught. Printed-value comparator:
truncated value, flag 1 vs 0, missing vs 0, 0 vs blank, 12th digit off by one are rejected; an
exact value and a decimal half-way tie are accepted: 7 of 7 as expected (`migration/eval_misc.py`).

---

# Round 2 (2026-11-14): the corrected SAS, rulings G33-G38

Method this round. The local server the round 1 scripts used refused connections, so every
evaluation went through `eval_decl` of the staging connector on the two sink items
(`test_predictions_full.evalApply`, `model_performance_metrics.evalApply`, `α = Float`), with the
input rows written into the call and the comparison either done inside Lean or read off the
returned values. Consequences, stated plainly: samples are smaller than in round 1; comparison
is to the printed precision of the SAS CSVs and listings (no HEX16 dumps, so nothing in this
round is bit-exact evidence); the full 105,000 / 45,000-row KS and PSI of the real run were not
evaluated in Lean (the three 7,000 / 3,000-row edge scenarios were, two of them in Lean). SAS
side: `judge/reference/` (corrected outputs), `judge/scenarios/`, and the run folders
`judge/runs/{final_*, ev_fix_*, ev2_fix_*, ev3_fix_G34_sequence, dbg3_fix_Q27_sequence}`.

## Runs

| Units | Input | SAS side | Cases / rows | Unexplained differences |
|---|---|---|---|---|
| credit_raw_columns_ok, num_macro, credit_raw_input_check, credit_raw_check_totals, credit_raw_stop | the faulty row(s) of each fix scenario with context rows: good file, outcome 2, age missing, duplicate id, count 0.5, count -1, count 0.99999999999999, dependents 1.5, `12345abc`, `abc`, 34-digit income, no known income, extra column, missing column, valid_unusual, income 0, income -0.5 | log messages of `dbg3_fix_Q27_sequence` and `ev3_fix_G34_sequence` (columns_ok, bad_rows, duplicate_ids, stopped or not) | 17 | 0 (one explained, below) |
| test_raw_columns_ok, test_num_macro, test_raw_input_check, test_raw_check_totals, test_raw_stop | good file, duplicate id, age missing, outcome 2, count 0.5, `abc`, extra column, income -1; outcome 1 / NA by reading | `ev_fix_Q27_test`, `dbg2_fix_Q27_test` | 9 | 0 |
| income_medians, age_groups, income_medians_all, credit_imputed, credit_features (chain from credit_raw_clean) | scenario fix_Q1 (income known in one age group only) | `ev_fix_Q1`: income_medians.csv (1: 5000, 5000; 2-5: blank, 5000), imputed income 5000 with MonthlyIncome_missing = 1, `25*log(5000)` = 212.92983 | all rows of the scenario | 0 |
| credit_features | 33 rows of `reference/model_features_*.csv` chosen for: income 0, income 1, utilization above 100, 3 or more dependents, 2 or fewer credit lines, 6 or more flags, imputed income, very large debt ratio; rest random | same files: total_risk_flags, age_income_interaction, utilization_debt_interaction, financial_health, log_monthly_income | 33 x 5 | 0 (relative 2e-6) |
| test_raw_clean, test_cleaned, test_imputed (train_income_medians := reference income_medians.csv), test_features | 20 raw test rows (10 with missing income over the five age groups, 2 with missing dependents) | `reference/test_predictions.csv`: monthly_income, total_risk_flags, financial_health | 20 | 0 |
| risk_scores_train | 25 reference rows nearest each grade boundary + 3 rows exactly on a boundary (0.10, 0.25, 0.50; by reading and X18) | `reference/risk_scores_train.csv`: score (1e-7), grade, recommendation, rate | 28 | 0 |
| risk_scores_validation | 25 reference rows | `reference/risk_scores_validation.csv` | 25 | 0 |
| test_predictions | 25 reference rows incl. pred_logistic; missing probability gives missing score, F, Decline, 0.20, pred 0 (scenario edge_predict) | `reference/test_predictions.csv`, `final_edge_predict` | 25 | 0 |
| logit_scored_valid_sorted, total_good_bad, ks_calculation, ks_statistic, train_scores_sorted, psi_cuts, train_bins, valid_bins, psi_bins, psi_floor, psi_calculation, psi_summary | fix_Q23_tie | `ev_fix_Q23_tie`: KS 0.5000 at 0.1000; PSI 0.3884, components 0.0495097873 (bins 0-2), 0.0599588344 (bins 4, 5, 7, 8), 0 (3, 6, 9) | whole scenario | 0 |
| same | fix_Q24 (two rows, same probability, one of each outcome) | `ev_fix_Q24`: one KS row, 0.0000 at 0.4000; PSI 1.9650 | whole | 0 |
| same | fix_Q25 (tiny) | `ev_fix_Q25`: KS 0 at 0.2; PSI 2.0794 = 2 x 1.0397207708 | whole | 0 |
| same | edge_metrics_a (7,000 training, 3,000 validation scores) | `final_edge_metrics_a`: KS 0.1168 at 0.0700; PSI 0.0027901142, ten printed bin rows | whole | 0 (Lean 0.116806, 0.002790114228) |
| same | edge_metrics_c | `final_edge_metrics_c`: KS 0.2876 at 0.0800; PSI 0.3078608702 (bin 9: training share 0, component 0.3023176) | whole | 0 (Lean 0.287562, 0.307860870240) |
| same | edge_metrics_b | `final_edge_metrics_b`: PSI 6.8121516398 | whole | not run in Lean (input too long for one call); a Python transcription of the same definitions gives 6.81215163984 |
| train_inputs_stop, metrics_inputs_stop, predict_inputs_stop, income_medians_export, psi_bins, age_groups | none | none | 0 | by reading only |

`best8` (parameter P3) was given the value SAS prints: 0.000071 for the 7,000-row scenarios,
0.071429 for 7 training rows, 0.25 for 2.

## Differences found and how each was resolved

1. **PSI with an empty bin, first model wrong.** With the exact floor `0.5 / N` the model gave
   6.80816 on edge_metrics_b where SAS gives 6.8121516398. Cause: `psi_floor` goes through a
   macro variable, so SAS uses the BEST8. text of it (0.000071, not 0.0000714285...). Modelled
   with the existing parameter `best8` (R19, P3); a, b and c then agree to all printed digits.
   Marked `BUG(port)` in `def:psi_floor`. This was a model correction before acceptance, on
   evidence, not a change made to pass.
2. **valid_unusual (incomes -1 and -7.5).** `dbg3_fix_Q27_sequence` accepts the file; the Lean
   reports 2 bad rows and stops. Explained: that run predates ruling G34 (negative income is
   now rejected); `ev3_fix_G34_sequence`, run on the final SAS, rejects -1 and -0.5, as the Lean
   does.

## Not covered

- An empty raw file (header only): SAS accepts a test file with no rows; the Lean `columns_ok`
  reads the column names from the first row, so it answers false. OPEN.
- Numeric cells in a column PROC IMPORT typed as character with exponent notation (R9
  precondition), and a MonthlyIncome / NumberOfDependents column typed numeric by PROC IMPORT
  reaching `credit_raw_clean` (round 1 precondition; the check units handle both types).
- `logistic_lackfit`: evidence is the pre-correction reference partition; not repeated.
- Comparator validation was not repeated; comparisons this round were made by reading values or
  by equality tests written in the call.

# Round 2 review (2026-11-14): defects raised by the reviewers

SAS side: two new experiments, `experiments/x21_review_round2.{sas,log,lst}` and
`experiments/x22_input_texts_r37.{sas,log}`, run on SAS OnDemand (DEV-011), plus
`judge/reference/scenarios/edge_metrics_b` and its inputs `judge/scenarios/edge_metrics_b`.
Lean side: `eval_decl` of the staging connector on `test_predictions_full.evalApply` and
`model_performance_metrics.evalApply`, `α = Float`, after the corrected items were accepted.

| Units | Input | SAS side | Lean result | Differences |
|---|---|---|---|---|
| credit_raw_columns_ok, num_macro, credit_raw_input_check, credit_raw_check_totals, credit_raw_stop | 3 training rows of X21 part B with headers `AGE`, `DEBTRATIO`, `monthlyincome`, `seriousdlqin2yrs`, `numberofdependents` | X21 B: columns_ok=1 bad_rows=0 duplicate_ids=0 known_incomes=2 | (true, (0, 0, 2), stop false) | 0 |
| same | same rows, reference headers | same | (true, (0, 0, 2), false) | 0 |
| same | income of row 1 = `5000-1`, `1+2`, `bad`, `undefined`, `.A` (five tables) | X21 A: each text reads as missing (`.A` as a special missing), so line 100 makes the row bad | (true, (1, 0, 1), true) each | 0 |
| same | income of row 1 = ` 5. ` | X21 A: `5.` is 5 | (true, (0, 0, 2), false) | 0 |
| same | table with no row | X21 C: import fails, columns_ok=0, script stops | (false, (0, 0, 0), true) | 0 on the stop decision (SAS leaves bad_rows=1, duplicate_ids=1 from lines 64-65) |
| test_raw_columns_ok, test_num_macro, test_raw_input_check, test_raw_check_totals, test_raw_stop | X21 part D: two rows, no age column | columns_ok=0 bad_rows=2 duplicate_ids=0 | (false, (2, 0), true), bad_row 1, 1 | 0 |
| same | X21 part E: ids A1, A2, A2, blank | columns_ok=1 bad_rows=1 duplicate_ids=2; bad_row 0, 0, 0, 1 | (true, (1, 2), true), bad_row 0, 0, 0, 1 | 0 |
| same | ids A1, A2, valid rows | by X21 E rows 1, 2: bad_row=0 | (true, (0, 0), false) | 0 |
| same | table with no row | X21 C: columns_ok=0, stops | (false, (0, 0), true) | 0 |
| test_raw_clean, test_cleaned, test_imputed, test_features, test_predictions, kaggle_submission | the two valid rows with ids A1, A2 | X21 E: row_id is Char holding A1, A2 | row_id "A1", "A2" in test_imputed and in kaggle_submission; incomes 9120 and the group median | 0 |
| train_scores_sorted, psi_cuts, train_bins, valid_bins, psi_floor (best8 := 0.000071), psi_calculation | edge_metrics_b: all 7,000 training and 3,000 validation scores (given to Lean as value x count, 8 and 333 distinct values) | `printed_psi_calculation.csv`: 0.1647142857 / 0.0873333333 / 0.0490966787; 0.8352857143 / 0.25 / 0.7060377198; bins 2-8 zero; bin 9: 0 / 0.6626666667 / 6.0570172413; PSI 6.8121516398 | the same ten rows to all ten printed digits; left-fold sum 6.8121516398 | 0 |
| same chain | empty training table, 3 validation rows | X22 F: train_bins 0 rows, valid_bins 0 rows; X21 F: psi_floor `.`, ten rows with shares 0 and component `.`, PSI `.`, 'No significant change' | psi_cuts [], bins empty, floor none, ten rows (0, 0, none) | 0 (psi_summary itself not re-run: its Lean is unchanged and a missing sum reads 'No significant change' by its first test) |

This replaces the round 2 entry "edge_metrics_b: not run in Lean". The earlier "Not covered"
entry on the header-only file is superseded by X21 part C.

Not evaluated: a full SAS run of the four scripts on a file with `5000-1` or with other
capitalisation (the experiments run the check code of lines 52-123 / 60-130 copied verbatim
into a macro, on small files, not the scripts themselves).
