# The port against the corrected SAS: where parity stands

2026-11-16. Measurement only; no code was changed.

The Python port (`port/credit_risk/`) was written to reproduce the SAS program before its verification. The SAS program has since been corrected (rounds 1 to 4, `git log -- legacy/`), and `judge/reference/` holds the outputs of the corrected program (scripts as at 697eed5). This is the port, unchanged, judged against that reference.

**Result: every line of the contract fails.** 15 of the 31 judged files differ on the real data. Nearly all differences trace to a named SAS correction that the port does not have yet; one (a single count in `printed_classification.csv`) does not and needs a diagnosis.

## How it was measured

`bash migration/legacy-to-port/parity/run_contract.sh out/parity_after_verification` at HEAD 74f9a9d: the nine contract lines of `judge/README.md`, each judged with `compare.py <reference> <candidate> --mode port --stage <stage>`. The outputs and the judge's full text are in `out/parity_after_verification/` (git-ignored): `r1_fe`, `r2_train`, `r3_metrics`, `r4_predict`, `r5_predict_edge`, `r6_metrics_a`, `r7_metrics_b`, `r8_metrics_c`, `r9_e2e`, each with `judge_<stage>.txt`.

| Line | Stage | Input | Files passing |
|---|---|---|---|
| 1 | fe | real data, reference split | 0 of 2 |
| 2 | train | reference feature files | 14 of 18 |
| 3 | metrics | reference score files | 6 of 9 |
| 4 | predict | real test file, model of line 2 | 0 of 2 |
| 5 | predict | `edge_predict` test file, model of line 2 | 0 of 2 |
| 6 | metrics | `edge_metrics_a` | 5 of 9 |
| 7 | metrics | `edge_metrics_b` | 5 of 9 |
| 8 | metrics | `edge_metrics_c` | 5 of 9 |
| 9 | end to end, fe | real data | 0 of 2 |
| 9 | end to end, predict | real data | 0 of 2 |

## Time

The whole contract (twelve port runs and ten judge calls) took **46 seconds** of wall clock.

| Port run | Seconds |
|---|---|
| fe | 10 (4 on the second run, in line 9) |
| train | 7 to 8 |
| metrics, real data | 1 |
| metrics, each edge scenario | under 1 |
| predict | 2 to 3 |

The port runs add up to about 37 seconds; the ten judge calls take the remaining 9 or so. One stage and its judge call can be rerun alone in 3 to 12 seconds (`run_contract.sh <outdir> fe`, and so on).

## Differences, stage by stage

Row counts are for the real data unless a scenario is named. "Train" and "validation" are the two files of a pair.

### Stage fe: `model_features_train.csv`, `model_features_validation.csv`

Both fail, on the same six columns. Line 9 (end to end) shows exactly the same differences.

| Column | Rows differing (train / validation) | Example (row id: reference, port) | SAS correction | Port place |
|---|---|---|---|---|
| `monthly_income` | 57 / 20 | 267: `208333`, `20833` | Q1 (726048a): the training file is imported with `guessingrows=max`, so an income of six digits is no longer cut to five | `feature_engineering.py` `run`, line 32, the `proc_import_csv` call |
| `income_per_dependent` | 57 / 20 | 267: `104166.5`, `10416.5` | follows from `monthly_income` | same |
| `log_monthly_income` | 57 / 20 | 267: `12.24689784`, `9.9443415465` | follows from `monthly_income` | same |
| `total_risk_flags` | 19,672 / 8,433 | 20: `2`, `1` | Q7 (7b55ef1): the total counts the eight risk flags | `feature_engineering.py` `run`, lines 185-191 |
| `age_income_interaction` | 103,866 / 44,499 | 1: `410.32012874`, `410.32506268` | Q9 (10f447e): age × log(income) when income is above 0, not age × log(income + 1) | `feature_engineering.py` `run`, line 205 |
| `utilization_debt_interaction` | 95,856 / 41,013 | 1: `6151.8597558`, `61.518597558` | Q9 (10f447e): utilization × debt ratio, no division by 100 | `feature_engineering.py` `run`, lines 207-209 |

The same rows also show as "not printed as SAS prints them", which is the same wrong value seen through the print format, not a second defect.

### Stage train: 14 of 18 pass

Passing: `model_coefficients.csv`, `stepwise_summary.csv`, `model_summary.csv`, the nine printed fit tables except one, both ROC files and both confusion files. So on the reference features the port fits the same model.

| File | Column | Rows differing | Example (row id: reference, port) | SAS correction | Port place |
|---|---|---|---|---|---|
| `risk_scores_train.csv`, `final_model_output.csv` | `credit_risk_score` | 105,000 (all) | 85073: `845.08018882`, `845` | Q15 (b7b1cd4): the score is not rounded | `train.py` `run`, lines 569 and 613 (two scoring blocks) |
| same | `risk_grade` | 15,450 | 93713: `E`, `B` | Q18 (e1df983): the grade is cut on the probability, not on the score | `train.py` `run`, lines 574-585 and 618-629 |
| same | `recommendation` | 11,286 | 93713: `Decline`, `Approve` | follows from the grade | same |
| same | `interest_rate` | 15,450 | 93713: `15.00%`, `7.00%` | follows from the grade | same |
| `risk_scores_validation.csv` | `credit_risk_score` | 45,000 (all) | 70959: `844.25865194`, `844` | Q15 | as above |
| same | `risk_grade`, `interest_rate` | 6,779 | 93492: `C`, `A` | Q18 | as above |
| same | `recommendation` | 4,932 | 93492: `Review`, `Approve` | follows from the grade | as above |
| `printed_classification.csv` | `CorrectEvents` | 1 | level 0.680: `308`, `309` | **none identified** | `sas_compat.py` `classification_table`, or the judge's rule for this table |

The classification count is one applicant at one probability level. No correction touched that table; the reference model is now fitted on the corrected features, so this is most likely an applicant whose adjusted probability sits on the 0.68 boundary and falls on different sides in SAS and in the port. It needs to be diagnosed before deciding whether the port or the judge's tolerance is to change.

### Stage metrics, real data: 6 of 9 pass

Passing: `ks_statistic.csv`, `decile_analysis.csv`, `threshold_analysis.csv`, `calibration_plot.csv`, `printed_roc_metrics.csv`, `printed_cumulative_lift.csv`.

| File | Column | Rows differing | Example (reference, port) | SAS correction | Port place |
|---|---|---|---|---|---|
| `validation_summary.csv`, `model_performance_metrics.csv` | `PSI` | 1 | `0.0004404097`, `0.0000` | Q25 (766937c, 723ddaa): both sets are binned on the training score deciles, and PSI is published unrounded | `metrics_calculation.py` `run`, lines 246-300 |
| `printed_psi_calculation.csv` | `train_pct` | 8 of 10 | bin 1: `0.1`, `0.1000285714` | Q25: the bins come from training cut points | same |
| same | `valid_pct` | 10 of 10 | bin 0: `0.1018888889`, `0.1` | Q25 | same |
| same | `psi_component` | 10 of 10 | bin 0: `0.0000353462`, `0` | Q25 | same |

### Stage metrics, edge scenarios a, b, c: 5 of 9 pass each

Passing in all three: `decile_analysis.csv`, `threshold_analysis.csv`, `calibration_plot.csv`, `printed_roc_metrics.csv`, `printed_cumulative_lift.csv`.

| File | Column | Scenario: reference, port | SAS correction | Port place |
|---|---|---|---|---|
| `ks_statistic.csv`, `validation_summary.csv`, `model_performance_metrics.csv` | `KS_Statistic` | a: `0.1168`, `0.1309`; b: `0.1839`, `0.1884`; c: `0.2876`, `0.2959` | Q24 (607dd5e): KS compares the distributions only between distinct probabilities; e8f879f: one KS row, the lowest cutoff | `metrics_calculation.py` `run`, lines 118-138 |
| same | `KS_Cutoff` | a: `0.0700`, `0.0800`; b: `0.0750`, `0.0760` | Q24 | same |
| `validation_summary.csv`, `model_performance_metrics.csv` | `PSI` | a: `0.0027901142`, `0.0906`; b: `6.8081601761`, `1.5743`; c: `0.3075776761`, `0.1790` | Q25, with the share of an empty bin floored (G35, G43, 3e6dfa6) | `metrics_calculation.py` `run`, lines 246-300 |
| same | `PSI_interpretation` | c: `Significant change`, `Some change` | follows from PSI | same |
| `printed_psi_calculation.csv` | rows | b: 10 rows in the reference, 3 in the port; c: 10 and 8 | Q25: all ten bins are listed, an empty one with share 0 | same |
| same | `train_pct`, `valid_pct`, `psi_component` | every row present differs | Q25 | same |

### Stage predict: `kaggle_submission.csv`, `test_predictions.csv`

Both fail on the real test file (101,503 rows) and on `edge_predict`.

| Column | Rows differing (real / edge) | Example (row id: reference, port) | SAS correction | Port place |
|---|---|---|---|---|
| `monthly_income` | 16,613 / 21,513 | 9: `5313`, `5395`; edge 5: `2557`, empty | Q13 (2d4fdef): test incomes are imputed from the training medians; Q14 (12a28e4) and Q1 (167dc38): an age group with no median falls back to the overall training median | `predict.py` `run`, lines 43-105 |
| `total_risk_flags` | 19,209 / 20,632 | 7: `3`, `2` | Q7 | `predict.py` `run`, lines 191-200 |
| `pd_logistic` (both files) | 19,209 / 20,632 beyond tolerance; mean difference 1.73e-3 | 7: `0.0452521749`, `0.0409676377` | follows from Q7, Q9 and Q13 through the features | `predict.py` `run`, lines 191-210 |
| `pred_logistic` | 167 / 180 | 70: `1`, `0` | follows from the probability | same |
| `credit_risk_score` | 101,503 (all) | 1: `836.21551796`, `836` | Q15 | `predict.py` `run`, line 246 |
| `risk_grade`, `interest_rate` | 15,293 / 15,248 | 10: `F`, `C` | Q18 | `predict.py` `run`, lines 252-284 |
| `recommendation` | 11,158 / 11,120 | 10: `Decline`, `Review` | follows from the grade | same |

`predict.py` holds the Q9 lines too (208-210); they do not show as a column because the test file does not publish the interaction features, only through the probability.

## What the judge does not show

- **`income_medians.csv` is not judged.** It is in the reference (the corrected `feature_engineering.sas` exports it, Q13) and in no stage of `judge/compare.py`. The port writes it only under `--export-train-medians`, and then without the `overall_median_income` column the reference has.
- **The contract script does not hand the medians to predict.** `run_contract.sh` gives `predict` the model folder and the data folder; the corrected `predict.sas` reads `income_medians.csv` from the output folder.
- **Corrections the real data and the four scenarios do not reach.** They change no reference file here, so no line of the contract can show whether the port has them:
  - Q27: the input checks, the removal of earlier results, the stop when the step before produced none, and the header-only test file (G44).
  - Q26: ten decile rows always, and capture rate and lift 0 with no defaulter (G41, G45).
  - Q23: the exact pairwise AUC (G40); the published AUC agrees to four decimals on every scenario here.
  - Q1 and Q14: the fallback to the overall median, reached only by `edge_predict`.
- **The port's own fix flags do not match the corrected SAS.** The port carries four optional flags from an earlier stage. Tried as they are:
  - `--fix-income-truncation` (fe) removes the three income-driven differences; `total_risk_flags` and the two interactions remain.
  - `--fix-psi-bins` (metrics) does not reproduce the reference: PSI comes out as `0.0004` (rounded) on the real data and as `0.0560` where the reference has `6.8081601761` on scenario b. The SAS correction builds its bins differently and floors empty shares.
  - `--export-train-medians` and `--fix-train-medians` use a medians file without the overall median.

## Work sets that touch disjoint port files

Each set can go to a different agent at the same time. Every stage is judged on the reference's inputs, so no set has to wait for another to see its own stage pass; only line 9 (end to end) needs sets A, B and C together.

| Set | Port file | Corrections | Contract lines it should turn green |
|---|---|---|---|
| A | `port/credit_risk/feature_engineering.py` | Q1 (import, fallback median), Q7, Q9, export of `income_medians.csv` with the overall median, Q27 checks for the training file | 1 |
| B | `port/credit_risk/predict.py` | Q13 and Q14 (training medians, fallback), Q7, Q9, Q15, Q18, Q27 checks for the test file and the header-only file | 4, 5 |
| C | `port/credit_risk/train.py` | Q15, Q18, in both scoring blocks and `final_model_output.csv` | 2, except the classification count |
| D | `port/credit_risk/metrics_calculation.py` | Q24 (KS), Q25 (PSI bins, floor, unrounded), Q23 (exact AUC), Q26 (ten deciles) | 3, 6, 7, 8 |
| E | `port/credit_risk/sas_compat.py` | the one classification count at level 0.680: diagnosis first | the last file of line 2 |
| F | `migration/legacy-to-port/parity/run_contract.sh`, and `judge/compare.py` if the owner allows | pass the medians to predict; drop or keep the fix flags; decide whether `income_medians.csv` is judged | 4, 5, 9 run as the corrected SAS runs |

Two cautions for the split:

- `sas_compat.py` is shared by all four stage modules. To keep the sets disjoint, only set E writes to it; sets A to D put any new helper in their own module, or ask E for it.
- Sets A and B hold the same feature engineering twice (as the SAS does), and sets B and C the same scoring. The three agents should agree the Q7, Q9, Q15 and Q18 expressions once, so the copies do not drift.
