# Judge validation report

## References

| Reference | Self-check | SAS errors | New warnings |
|---|---|---|---|
| reference (32 files) | PASS | 0 | 0 |
| reference/scenarios/edge_predict (32 files) | PASS | 0 | 0 |
| reference/scenarios/edge_metrics_a (9 files) | PASS | 0 | 0 |
| reference/scenarios/edge_metrics_b (9 files) | PASS | 0 | 0 |
| reference/scenarios/edge_metrics_c (9 files) | PASS | 0 | 0 |
| staged metrics run on reference risk scores vs reference (9 files, strict) | FAIL: validation_summary.csv[AUC,Gini,KS_Cutoff,KS_Statistic,PSI,raw]; ks_statistic.csv[KS_Cutoff,KS_Statistic,raw]; model_performance_metrics.csv[AUC,Gini,KS_Cutoff,KS_Statistic,PSI,accuracy_at_50,f1_score_at_50,precision_at_50,specificity_at_50]; decile_analysis.csv[avg_pd,capture_rate,default_rate,defaults,lift,max_pd,min_pd,raw]; threshold_analysis.csv[accuracy,f1_score,precision,raw,recall,specificity]; calibration_plot.csv[mean_actual,mean_predicted,raw]; printed_roc_metrics.csv[Area,Gamma,LowerArea,SomersD,StdErr,TauA,UpperArea,raw]; printed_cumulative_lift.csv[avg_pd,capture_rate,cum_capture_rate,cum_defaults,cum_lift,default_rate,defaults,lift,max_pd,min_pd,raw]; printed_psi_calculation.csv[psi_component,raw,train_pct,valid_pct] | | |

## Mutations (port mode)

| Mutation | Reference | Verdict | Failing files [columns] | SAS errors in run |
|---|---|---|---|---|
| `fe_health_penalty` | reference | **STALE** | run of 20261105T103309, before the reference run of 20261116T094856 | 0 |
| `fe_impute_mean` | reference | **STALE** | run of 20261105T103836, before the reference run of 20261116T094856 | 0 |
| `train_slentry` | reference | **STALE** | run of 20261105T104400, before the reference run of 20261116T094856 | 0 |
| `train_grade_cutoff` | reference | **STALE** | the mutation no longer finds its text in legacy/ | 0 |
| `train_round_floor` | reference | **STALE** | the mutation no longer finds its text in legacy/ | 0 |
| `train_rate_format` | reference | **STALE** | run of 20261105T102541, before the reference run of 20261116T094856 | 0 |
| `metrics_decile_groups` | reference | **STALE** | run of 20261105T110103, before the reference run of 20261116T094856 | 0 |
| `metrics_threshold` | reference | **STALE** | run of 20261105T110203, before the reference run of 20261116T094856 | 0 |
| `predict_no_dep_impute` | reference | **STALE** | run of 20261105T104140, before the reference run of 20261116T094856 | 0 |
| `train_slstay` | reference | **STALE** | run of 20261105T104932, before the reference run of 20261116T094856 | 0 |
| `fe_import_guessingrows` | reference | **STALE** | the mutation no longer finds its text in legacy/ | 0 |
| `fe_median_group_misaligned` | reference | **STALE** | run of 20261105T105311, before the reference run of 20261116T094856 | 0 |
| `fe_low_income_boundary` | reference | **STALE** | run of 20261105T105832, before the reference run of 20261116T094856 | 0 |
| `predict_grade_b_boundary` | reference | **STALE** | the mutation no longer finds its text in legacy/ | 0 |
| `predict_rate_f` | reference/scenarios/edge_predict | **STALE** | run of 20261105T102155, before the reference run of 20261115T103922 | 0 |
| `predict_null_compare_false` | reference/scenarios/edge_predict | **STALE** | run of 20261105T102721, before the reference run of 20261115T103922 | 0 |
| `metrics_rank_ties` | reference/scenarios/edge_metrics_a | **STALE** | run of 20261105T102050, before the reference run of 20261115T104510 | 0 |
| `metrics_psi_sign` | reference/scenarios/edge_metrics_b | **STALE** | the mutation no longer finds its text in legacy/ | 0 |
| `metrics_status_threshold` | reference/scenarios/edge_metrics_c | **STALE** | run of 20261105T105712, before the reference run of 20261115T104553 | 0 |
| `train_score_rounded` | reference | **CAUGHT** | risk_scores_train.csv[credit_risk_score]; risk_scores_validation.csv[credit_risk_score]; final_model_output.csv[credit_risk_score]; validation_summary.csv[PSI]; model_performance_metrics.csv[PSI]; printed_psi_calculation.csv[psi_component,train_pct,valid_pct] | 0 |
| `train_grade_cut_pd` | reference | **CAUGHT** | risk_scores_train.csv[interest_rate,risk_grade]; risk_scores_validation.csv[interest_rate,risk_grade]; final_model_output.csv[interest_rate,risk_grade] | 0 |
| `predict_grade_b_cut_pd` | reference | **CAUGHT** | test_predictions.csv[interest_rate,recommendation,risk_grade] | 0 |

Totals: CAUGHT 3, STALE 19
