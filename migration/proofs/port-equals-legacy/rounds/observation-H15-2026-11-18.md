# Observation H15: the real reader on the score files of a one-outcome run (2026-11-18)

Written by the coding agent of crm-w7 (review of 65430e4, 70c4d9c); saved here by the lead because it cites SAS logs (not for the port translators: they get only the port-side facts, through the lead).

Observations of the port, 2026-11-18, rule H15 (asked for in rounds/C-g-draft-2026-11-18.md, R6). Port at commit 1a90814, polars 2.1.0. I called sas_compat.proc_import_csv(path, guessingrows=20) as metrics_calculation.run does (metrics_calculation.py:107 for risk_scores_validation.csv, :117 for risk_scores_train.csv), on SAS's score files from judge/runs/x27_C60_full, x27_E60_full, oneclass_n4_all1, oneclass_n60_all1 and emptyval_n1_class0. All five give the same picture.

risk_scores_train.csv (C60 and E60: 42 rows, 51 columns; 3 rows for n4_all1, 1 for n1_class0):
- Rows: all of them, one per row of the training part.
- pd_logistic and credit_risk_score: text (pl.String, width 1, because the column is empty in every row of the guessing window); every cell is null.
- risk_grade, recommendation, interest_rate: text ('F', 'Decline', '20.00%' in every row).
- The other 46 columns (row_id, default_flag, the 40 features, pred_logistic, base_score, score_range, base_rate): numbers (Float64); pred_logistic is 0 in every row.
- SAS reads the file the same way: the x27_C60_full metrics log shows informats pd_logistic $1., credit_risk_score $1., risk_grade $1., recommendation $7., interest_rate $6., and best32. for the other 46.
- So conjunct 16 ('a numeric cell stays numeric' for pd_logistic and credit_risk_score) is false of the real reader on this file.

risk_scores_validation.csv (header only):
- The reader returns 0 rows and 9 text columns (pd_logistic, pred_logistic, base_score, score_range, credit_risk_score, risk_grade, recommendation, base_rate, interest_rate). There is no default_flag column.
- SAS does not import it at all ('Unable to sample external file, no data in first 5 records', 'ERROR: Import unsuccessful', metrics log lines 62-63), so WORK.LOGIT_SCORED_VALID does not exist.

What the metrics stage then does:
(1) Validation table. valid_exists = height > 0 (:112) is False, and the text table is replaced at once by a 0-row table of default_flag, pd_logistic and credit_risk_score, all Float64 (:113-116). No later step reads the reader's text columns. The steps follow valid_exists: decile_analysis.csv, ks_statistic.csv, calibration_plot.csv and printed_roc_metrics.csv are not written; validation_summary.csv, model_performance_metrics.csv, threshold_analysis.csv and printed_cumulative_lift.csv are written as a header only.
(2) Training table. Only credit_risk_score is read, in the PSI steps (:357-380); pd_logistic and the other columns are never read.
- The nine cuts (sorted row ceil(k*n/10)) are all None.
- score_bin adds flag(gt(text cell, lit(cut, Float64))) over the cuts. gt(x,c) = lt(c,x) answers on its null branch (c is null, so the result is x.is_not_null(), which is False). Every row lands in bin 0.
- The branch that compares text with a number never decides a row here. On a non-null text cell against a non-null cut, polars 2.1.0 raises 'ComputeError: cannot compare string with numeric type (f64)' (probe). That needs a score file whose first 20 rows are unscored and some later rows scored, which a one-outcome training part never gives.
- train_bins has n rows, all in bin 0; valid_bins has 0 rows; psi_floor = 0.5/n.
- Bin 0: train_pct 1, valid_pct 0, component (1-0.5/n)*log(2n), which is 4.3780689798 for n=42. Bins 1 to 9: 0.
- printed_psi_calculation.csv is written in full and matches SAS byte for byte in every one-outcome run. PSI goes only into validation_summary and model_performance_metrics, whose merges have no row.
(3) Every file the metrics stage writes matches SAS byte for byte, on SAS's score files (line 3) and on the port's own (line 9).

For the Lean: the stage writes the same files as if pd_logistic and credit_risk_score were numeric columns with every cell missing.
