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
