# Audit of the existing `def:` items of `py-credit-risk-port`

Blueprint `b41b22d4-720d-4290-b593-39ceab961986`, read-only audit, 2026-11-11.
Reference: pre-pass dump `py-credit-risk-port_b41b22d4-720d-4290-b593-39ceab961986.lean` (12,666 lines).

## Counts

| prefix | count |
|---|---|
| `def:` | 145 |
| `thm:` | 117 |
| `neg:` | 61 |
| total | 323 (all unique, no other prefix) |

- `def:` ids containing `zz` (case-sensitive): none. No `def:zz_...` carrier is left. Case-insensitive, the only hit is `def:_ROUND_FUZZ`, an original item.
- `def:` ids in the blueprint with no counterpart in the dump: none.
- Items of the Python part of the dump (145 sections, lines 2635-12666) missing from the blueprint: none.
- Every `neg:X_neg` has its `thm:X`. No `thm:`/`neg:` name occurs in the dump.

## Result

All 145 `def:` items are in state `DefinitionFormalized` and their `statement_lean` occurs verbatim in the dump, exactly once, each filling its whole dump section (preceded by the `-- Comment:` line, followed by the blank line before `end`).

Method: each `statement_lean` was piped on stdin to a Python containment test against the dump; only trailing whitespace at line ends and the final newline were normalised.

## Items

| item id | state | verbatim match | note |
|---|---|---|---|
| `def:ExprOrNum` | DefinitionFormalized | yes | dump line 2638; statement too large for get_items (39 KB response, 30 KB cap); text read with get_lean (item_statement_lean), state with get_items; 807 lines / 36,461 bytes matched |
| `def:train_run_15_printed_roc_precond` | DefinitionFormalized | yes | dump line 3456 |
| `def:train_run_15_printed_roc` | DefinitionFormalized | yes | dump line 3498 |
| `def:merge_one_to_one_precond` | DefinitionFormalized | yes | dump line 3539 |
| `def:train_run_14_final_and_summary_precond` | DefinitionFormalized | yes | dump line 3558 |
| `def:merge_one_to_one` | DefinitionFormalized | yes | dump line 3598 |
| `def:train_run_14_final_and_summary` | DefinitionFormalized | yes | dump line 3718 |
| `def:_pairs_precond` | DefinitionFormalized | yes | dump line 3807 |
| `def:FloatArray_` | DefinitionFormalized | yes | dump line 3829 |
| `def:_Pairs` | DefinitionFormalized | yes | dump line 3921 |
| `def:_TIE_EPS` | DefinitionFormalized | yes | dump line 3940 |
| `def:_pairs` | DefinitionFormalized | yes | dump line 3967 |
| `def:roc_association_precond` | DefinitionFormalized | yes | dump line 4027 |
| `def:train_run_13_roc_precond` | DefinitionFormalized | yes | dump line 4053 |
| `def:RocAssociation` | DefinitionFormalized | yes | dump line 4083 |
| `def:_ratio` | DefinitionFormalized | yes | dump line 4102 |
| `def:Z975` | DefinitionFormalized | yes | dump line 4117 |
| `def:roc_association` | DefinitionFormalized | yes | dump line 4178 |
| `def:train_run_13_roc` | DefinitionFormalized | yes | dump line 4259 |
| `def:train_run_12_risk_scores_precond` | DefinitionFormalized | yes | dump line 4292 |
| `def:_ROUND_FUZZ` | DefinitionFormalized | yes | dump line 4309; id contains ZZ only through FUZZ (case-insensitive hit); original item, not a zz_ carrier |
| `def:_TWO52` | DefinitionFormalized | yes | dump line 4320 |
| `def:_e` | DefinitionFormalized | yes | dump line 4333 |
| `def:_named` | DefinitionFormalized | yes | dump line 4353 |
| `def:sas_round` | DefinitionFormalized | yes | dump line 4378 |
| `def:train_run_12_risk_scores` | DefinitionFormalized | yes | dump line 4492 |
| `def:train_run_11_confusion_valid_precond` | DefinitionFormalized | yes | dump line 4580 |
| `def:_has_bare_column` | DefinitionFormalized | yes | dump line 4609 |
| `def:_is_scalar` | DefinitionFormalized | yes | dump line 4651 |
| `def:div` | DefinitionFormalized | yes | dump line 4682 |
| `def:lt` | DefinitionFormalized | yes | dump line 4742 |
| `def:gt` | DefinitionFormalized | yes | dump line 4765 |
| `def:train_run_11_confusion_valid` | DefinitionFormalized | yes | dump line 4819 |
| `def:train_run_10_score_valid_precond` | DefinitionFormalized | yes | dump line 4879 |
| `def:flag` | DefinitionFormalized | yes | dump line 4899 |
| `def:ge` | DefinitionFormalized | yes | dump line 4915 |
| `def:sas_exp` | DefinitionFormalized | yes | dump line 4931 |
| `def:train_run_10_score_valid` | DefinitionFormalized | yes | dump line 4961 |
| `def:train_run_09_confusion_train_precond` | DefinitionFormalized | yes | dump line 4997 |
| `def:train_run_09_confusion_train` | DefinitionFormalized | yes | dump line 5066 |
| `def:LogisticFit` | DefinitionFormalized | yes | dump line 5139 |
| `def:_expit` | DefinitionFormalized | yes | dump line 5160 |
| `def:classification_table` | DefinitionFormalized | yes | dump line 5261 |
| `def:_expit_precond` | DefinitionFormalized | yes | dump line 5437 |
| `def:classification_table_precond` | DefinitionFormalized | yes | dump line 5463 |
| `def:train_run_08_ctable_precond` | DefinitionFormalized | yes | dump line 5543 |
| `def:train_run_08_ctable` | DefinitionFormalized | yes | dump line 5624 |
| `def:_hl_groups` | DefinitionFormalized | yes | dump line 5713 |
| `def:chi2_sf` | DefinitionFormalized | yes | dump line 5768 |
| `def:hosmer_lemeshow` | DefinitionFormalized | yes | dump line 5857 |
| `def:hosmer_lemeshow_precond` | DefinitionFormalized | yes | dump line 6000 |
| `def:train_run_07_hl_precond` | DefinitionFormalized | yes | dump line 6056 |
| `def:train_run_07_hl` | DefinitionFormalized | yes | dump line 6107 |
| `def:train_run_06_coefficients_odds_precond` | DefinitionFormalized | yes | dump line 6166 |
| `def:train_run_06_coefficients_odds` | DefinitionFormalized | yes | dump line 6243 |
| `def:association_table_precond` | DefinitionFormalized | yes | dump line 6332 |
| `def:train_run_05_association_precond` | DefinitionFormalized | yes | dump line 6347 |
| `def:AssociationTable` | DefinitionFormalized | yes | dump line 6375 |
| `def:association_table` | DefinitionFormalized | yes | dump line 6418 |
| `def:train_run_05_association` | DefinitionFormalized | yes | dump line 6487 |
| `def:train_run_04_score_train` | DefinitionFormalized | yes | dump line 6554 |
| `def:train_run_04_score_train_precond` | DefinitionFormalized | yes | dump line 6604 |
| `def:StepwiseStep` | DefinitionFormalized | yes | dump line 6651 |
| `def:StepwiseResult` | DefinitionFormalized | yes | dump line 6677 |
| `def:train_run_03_fit_global_rsquare_precond` | DefinitionFormalized | yes | dump line 6698 |
| `def:train_run_03_fit_global_rsquare` | DefinitionFormalized | yes | dump line 6849 |
| `def:train_run_02_stepwise_summary` | DefinitionFormalized | yes | dump line 7044 |
| `def:train_run_01_fit_frame` | DefinitionFormalized | yes | dump line 7158 |
| `def:train_run_01_fit_frame_precond` | DefinitionFormalized | yes | dump line 7255 |
| `def:sql_sum` | DefinitionFormalized | yes | dump line 7283 |
| `def:sql_min` | DefinitionFormalized | yes | dump line 7301 |
| `def:sql_mean` | DefinitionFormalized | yes | dump line 7321 |
| `def:sql_max` | DefinitionFormalized | yes | dump line 7339 |
| `def:sas_sum_precond` | DefinitionFormalized | yes | dump line 7358 |
| `def:sas_sum` | DefinitionFormalized | yes | dump line 7379 |
| `def:sas_min_precond` | DefinitionFormalized | yes | dump line 7403 |
| `def:sas_min` | DefinitionFormalized | yes | dump line 7417 |
| `def:sas_max_precond` | DefinitionFormalized | yes | dump line 7440 |
| `def:sas_max` | DefinitionFormalized | yes | dump line 7454 |
| `def:sas_log` | DefinitionFormalized | yes | dump line 7479 |
| `def:run_py_py_py_precond` | DefinitionFormalized | yes | dump line 7501 |
| `def:run_py_py_py` | DefinitionFormalized | yes | dump line 8356 |
| `def:predict_run_01_clean` | DefinitionFormalized | yes | dump line 8475 |
| `def:predict_run_02_medians` | DefinitionFormalized | yes | dump line 8527 |
| `def:predict_run_03_cleaned` | DefinitionFormalized | yes | dump line 8581 |
| `def:predict_run_04_imputed` | DefinitionFormalized | yes | dump line 8630 |
| `def:predict_run_05_features` | DefinitionFormalized | yes | dump line 8765 |
| `def:predict_run_06_score` | DefinitionFormalized | yes | dump line 8894 |
| `def:predict_run_01_clean_precond` | DefinitionFormalized | yes | dump line 8935 |
| `def:predict_run_02_medians_precond` | DefinitionFormalized | yes | dump line 8962 |
| `def:predict_run_03_cleaned_precond` | DefinitionFormalized | yes | dump line 8999 |
| `def:predict_run_04_imputed_precond` | DefinitionFormalized | yes | dump line 9031 |
| `def:predict_run_05_features_precond` | DefinitionFormalized | yes | dump line 9082 |
| `def:predict_run_06_score_precond` | DefinitionFormalized | yes | dump line 9112 |
| `def:predict_run_07_predictions_precond` | DefinitionFormalized | yes | dump line 9136 |
| `def:run_py_py_precond` | DefinitionFormalized | yes | dump line 9159 |
| `def:predict_run_07_predictions` | DefinitionFormalized | yes | dump line 9255 |
| `def:predict_run_08_outputs` | DefinitionFormalized | yes | dump line 9332 |
| `def:run_py_py` | DefinitionFormalized | yes | dump line 9679 |
| `def:metrics_run_01_roc_auc` | DefinitionFormalized | yes | dump line 9745 |
| `def:_into_float` | DefinitionFormalized | yes | dump line 9779 |
| `def:eq` | DefinitionFormalized | yes | dump line 9802 |
| `def:metrics_run_02_ks` | DefinitionFormalized | yes | dump line 9855 |
| `def:confusion_metrics` | DefinitionFormalized | yes | dump line 9961 |
| `def:metrics_run_03_thresholds` | DefinitionFormalized | yes | dump line 10046 |
| `def:proc_rank_groups` | DefinitionFormalized | yes | dump line 10075 |
| `def:metrics_run_04_deciles` | DefinitionFormalized | yes | dump line 10161 |
| `def:proc_rank_apply_groups` | DefinitionFormalized | yes | dump line 10230 |
| `def:metrics_run_06_psi` | DefinitionFormalized | yes | dump line 10342 |
| `def:metrics_run_01_roc_auc_precond` | DefinitionFormalized | yes | dump line 10436 |
| `def:metrics_run_02_ks_precond` | DefinitionFormalized | yes | dump line 10466 |
| `def:confusion_metrics_precond` | DefinitionFormalized | yes | dump line 10497 |
| `def:metrics_run_03_thresholds_precond` | DefinitionFormalized | yes | dump line 10523 |
| `def:proc_rank_groups_precond` | DefinitionFormalized | yes | dump line 10543 |
| `def:metrics_run_04_deciles_precond` | DefinitionFormalized | yes | dump line 10568 |
| `def:metrics_run_05_cumulative_lift_precond` | DefinitionFormalized | yes | dump line 10602 |
| `def:proc_rank_apply_groups_precond` | DefinitionFormalized | yes | dump line 10641 |
| `def:metrics_run_06_psi_precond` | DefinitionFormalized | yes | dump line 10666 |
| `def:metrics_run_07_calibration_precond` | DefinitionFormalized | yes | dump line 10735 |
| `def:metrics_run_08_validation_summary_precond` | DefinitionFormalized | yes | dump line 10765 |
| `def:metrics_run_09_model_performance_precond` | DefinitionFormalized | yes | dump line 10796 |
| `def:metrics_run_10_printed_roc_precond` | DefinitionFormalized | yes | dump line 10841 |
| `def:run_py_precond` | DefinitionFormalized | yes | dump line 10870 |
| `def:metrics_run_05_cumulative_lift` | DefinitionFormalized | yes | dump line 10946 |
| `def:metrics_run_07_calibration` | DefinitionFormalized | yes | dump line 10998 |
| `def:metrics_run_08_validation_summary` | DefinitionFormalized | yes | dump line 11039 |
| `def:metrics_run_09_model_performance` | DefinitionFormalized | yes | dump line 11088 |
| `def:metrics_run_10_printed_roc` | DefinitionFormalized | yes | dump line 11139 |
| `def:run_py` | DefinitionFormalized | yes | dump line 11538 |
| `def:fe_run_01_clean` | DefinitionFormalized | yes | dump line 11608 |
| `def:fe_run_02_income_medians` | DefinitionFormalized | yes | dump line 11650 |
| `def:fe_run_03_cleaned` | DefinitionFormalized | yes | dump line 11695 |
| `def:fe_run_04_imputed` | DefinitionFormalized | yes | dump line 11747 |
| `def:fe_run_05_features` | DefinitionFormalized | yes | dump line 11884 |
| `def:fe_run_01_clean_precond` | DefinitionFormalized | yes | dump line 11995 |
| `def:fe_run_02_income_medians_precond` | DefinitionFormalized | yes | dump line 12026 |
| `def:fe_run_03_cleaned_precond` | DefinitionFormalized | yes | dump line 12054 |
| `def:fe_run_04_imputed_precond` | DefinitionFormalized | yes | dump line 12088 |
| `def:fe_run_05_features_precond` | DefinitionFormalized | yes | dump line 12153 |
| `def:fe_run_06_split_precond` | DefinitionFormalized | yes | dump line 12195 |
| `def:run_precond` | DefinitionFormalized | yes | dump line 12239 |
| `def:fe_run_06_split` | DefinitionFormalized | yes | dump line 12301 |
| `def:run` | DefinitionFormalized | yes | dump line 12577 |
| `def:le` | DefinitionFormalized | yes | dump line 12637 |
| `def:_hl_groups_precond` | DefinitionFormalized | yes | dump line 12653 |
