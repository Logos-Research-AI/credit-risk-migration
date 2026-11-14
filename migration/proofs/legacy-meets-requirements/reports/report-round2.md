# Legacy SAS against the requirements, round 2: report

## Outcome

Of the 27 contracts in `sas-credit-risk-spec` (`3f5df696-7c80-45cc-809f-b2881714663d`), 19 are proved, 1 holds by construction only, 3 are disproved as failures of the SAS program, and 4 are not decided about the SAS.

- **Proved (19):** Q1 to Q10, Q15, Q16, Q18 to Q21, Q24, Q25 and `score_chains_agree`. The size clause of Q10 is by-construction and conditional on the draw.
- **By-construction (1):** Q11.
- **Disproved, the SAS is at fault (3):** Q23, Q26, Q27.
- **Needs a ruling (3):** Q12, Q13, Q22. Q13 has an accepted Lean disproof, but the check found it is an artefact of the import link and `TestOK`, not a defect in `predict.sas`.
- **Open (1):** Q14.

Nothing was written in this step. No hook blocked a call. The local server `logos-mcp` failed to connect (ECONNREFUSED) and was not needed; every call went through Logos MCP Staging.

## get_status (legacy blueprint, called in this step)

| Field | Value |
|---|---|
| total_items | 137 |
| statements_formalized | 133 |
| statements_pinned | 0 |
| statements_to_write | none |
| proofs_to_write | `thm:sas_Q12`, `thm:sas_Q14`, `thm:sas_Q22` |
| waiting | none |
| flagged | `thm:sas_Q13`, `thm:sas_Q23`, `thm:sas_Q26`, `thm:sas_Q27` |
| verification_approved | false |

The blueprint reports every trust layer off, so "accepted" means the Lean compiled against the accepted statement; no judge compared it with the informal text.

## How sasPipeline is wired

`def:sasPipeline` (type `CreditRisk.Pipeline`, 17 parameters) and `def:SasLinks` (the same 17 parameters, a Prop) are both accepted. Each `sas_Qk` is `CreditRisk.Qk (sasPipeline ...)` under `SasLinks` only. The wiring below is the one after the assembly review.

- **Model:** `Sas.Model ℝ`.
- **features train seed:** `raw := importTrain train`. Returns none when `credit_raw_stop (credit_raw_columns_ok raw) (credit_raw_check_totals (credit_raw_input_check raw))` is true. Otherwise `credit_raw_clean`, `income_medians`, `income_medians_all age_groups`, `credit_cleaned`, `credit_imputed arrange`, `credit_features`, `split seed`, `credit_train_validation`, then the two export units.
- **fit F:** none when `train_inputs_stop (featTrainExists F) (featValidExists F)` is true, otherwise `some (fit (readFeatures F))`. This is the only place the stop of `train.sas` is wired.
- **score m F:** `some (risk_scores_validation_clean (risk_scores_validation (logit_scored_valid (logit_scored_valid_temp m (readFeatures F)))))`, with no stop. The training chain is not wired in; it is tied to `score` by `score_chains_agree`.
- **scoreTest m test train:** none when `predict_inputs_stop (mediansExist train) (coefExists m)` is true; then none when `test_raw_stop` on `importTest test` is true. Otherwise `test_raw_clean`, `test_cleaned`, `test_imputed arrange`, `test_features`, `test_scored_temp m`, `test_scored`, `test_predictions`, `test_predictions_full`. The medians are recomputed from the raw training table through `importTrain`, `credit_raw_clean`, `income_medians`, `income_medians_all`, `income_medians_export`, `readMedians`.
- **metrics S1 S2:** none when `metrics_inputs_stop (scoresTrainExists S1) (scoresValidExists S2)` is true. Otherwise the summary is `validation_summary (auc_summary (roc_stats s)) ks (psi_summary agg (psi_calculation (psi_floor best8 tb vb) psi_bins tb vb))`, with `ks_statistic`, `decile_analysis agg (decile_data v)` and `threshold_analysis v` for the other three tables.
- **Not wired**, because no field of the interface receives their output: `logistic_association`, `logistic_lackfit`, `confusion_matrix_train`, `training_metrics`, `confusion_matrix`, `validation_metrics`, `roc_train`, `roc_valid`, `final_model_output`, `model_summary`, `total_defaults`, `cumulative_lift`, `calibration_data`, `calibration_plot`, `model_performance_metrics`, `kaggle_submission`.

### Parameters and links

| Parameter | Stands for | Link in SasLinks |
|---|---|---|
| `importTrain`, `importTest` | PROC IMPORT of the raw files | For every raw table that has a delivery within the check and clean preconditions, the import is one: same column names and order, every cell kept except numeric `MonthlyIncome` and `NumberOfDependents`, which become text read back by `Sas.inputBest` as the same value (missing as blank, period or NA) |
| `readFeatures`, `readScoresTrain`, `readScoresValid`, `readMedians` | CSV written by one script, read by the next | Identity |
| `arrange` | Row order of the PROC SQL joins | A permutation of its argument |
| `split` | PROC SURVEYSELECT | Rows in order, each with `Selected` 0 or 1; number selected within 1 of 70 % |
| `fit` | The model fit | Every term names a column that is a numeric cell in every row of the table fitted on |
| `agg` | PROC SQL SUM and MEAN | Real sum and mean |
| `best8` | BEST8. round trip in `psi_floor` | Within 5·10⁻⁸ relative of x, and positive when x is positive |
| `featTrainExists`, `featValidExists` | Feature files exist | True exactly when the table is F1 or F2 of some result of `features` |
| `scoresTrainExists`, `scoresValidExists` | Score files exist | True exactly when `score` returned that table for some model and feature table |
| `mediansExist` | `income_medians.csv` exists | True exactly when `features` returned a result on that table for some seed |
| `coefExists` | Coefficient file exists | True exactly when `fit` returned that model for some feature table |

`invLink` is not a parameter of `sasPipeline`; it appears only in `score_chains_agree`.

## Every requirement

"split (rows)" means only the row clause of the split link is used, so the result is not conditional on the draw.

| Contract | Outcome | Conditional on |
|---|---|---|
| Q1 | proved | importTrain, arrange, split (rows) |
| Q2 | proved | importTrain, arrange, split (rows) |
| Q3 | proved | importTrain, arrange, split (rows) |
| Q4 | proved | importTrain, arrange, split (rows) |
| Q5 | proved | importTrain, arrange, split (rows) |
| Q6 | proved | importTrain, arrange, split (rows) |
| Q7 | proved | split (rows) |
| Q8 | proved | split (rows) |
| Q9 | proved | importTrain, arrange, split (rows) |
| Q10 | proved; size clause by-construction | importTrain, arrange, split (rows); size clause conditional on the draw |
| Q11 | by-construction | none (uses no link and no SAS unit) |
| Q12 | needs-ruling | fails at the importTest guard; nothing machine-checked |
| Q13 | needs-ruling (Lean disproof accepted, judged an artefact) | importTest guard |
| Q14 | open | blocked by the fit link; nothing machine-checked |
| Q15 | proved | none |
| Q16 | proved | none |
| Q18 | proved | none |
| Q19 | proved | none |
| Q20 | proved | none |
| Q21 | proved | none |
| Q22 | needs-ruling | blocked by the fit link; nothing machine-checked |
| Q23 | disproved, `legacy-violates-requirement` | witness uses fit and split (2 of 4 rows); the defect depends on neither |
| Q24 | proved | importTrain, readFeatures, readScoresValid, arrange, split (rows) |
| Q25 | proved | importTrain, the three reads, arrange, split (rows), fit (conditional on the fit), agg, best8 |
| Q26 | disproved, `legacy-violates-requirement` | conditional on the draw (fewer than ten validation rows); independent of the fit |
| Q27 | disproved, `legacy-violates-requirement` (third clause) | importTest, importTrain, file-existence links |
| score_chains_agree | proved | invLink, readFeatures, arrange, split (rows), fit (conditional on the fit) |

All proofs are over the real numbers, where no arithmetic overflows or rounds. They say nothing about binary64 behaviour, including the exp overflow of `train.sas` 185 and `predict.sas` 305-313.

## What the disproof checks found

- **Q13: artefact.** `neg:sas_Q13_neg` is the exact negation and is proved. The counterexample is a test table whose outcome column holds a missing number in one row and a missing text in another. `TestOK` allows that, but no import delivery exists for it, so `importTest` is unconstrained and the witness returns a made-up row with an id no applicant has. PROC IMPORT has no such freedom, and a CSV file cannot express the two encodings. The checker read about 60 % of the solution and relied on the server for the rest. `thm:sas_Q13` is still flagged false in the blueprint; I did not change it.
- **Q23: stands.** Exact negation, fully read, no axiom or sorry. The checker corrected one point: `credit_features_precond` and `credit_train_validation_precond` are on the path and were checked by reading, not skipped legitimately. `total_good_bad_precond`, `decile_data_precond` and `train_bins_precond` were not checked by anyone; the proof reads only the AUC cell. Lines 70-77, 79-87 and 401-416 of `metrics_calculation.sas` are confirmed.
- **Q26: stands.** Exact negation, fully read. The checker added a caveat: real PROC SURVEYSELECT on the 4-row witness probably selects 3, leaving one validation row, which is outside `roc_stats_precond`. The finding does not depend on it; any validation set of 2 to 9 rows with both classes gives the same bound, but that larger case is argued, not machine-checked. The correct lines are 208-213 and 216-231; the Lean comments cite stale numbers.
- **Q27: stands.** Exact negation, fully read. The raw test table has a delivery and the link fixes it fully, so this is not the Q13 hole. Real SAS evidence (`x21_review_round2` part E) shows `VAR1=A1 bad_row=0`. Later `predict.sas` preconditions were checked by reading only. There is no end-to-end SAS run of `predict.sas` with a text id.

In all four checks the accepted proof text was too large to fetch, so the checkers read the stored draft and could not compare it byte for byte with the accepted one.

## What is open

Decisions needed:

1. **Missing cells in the test file (Q12, Q13, test part of Q14).** Either `TestOK` fixes one encoding of a missing cell, or the test import link delivers a missing outcome as a numeric missing. Then Q12 and Q13 are to be decided again by proof, and the flag on `thm:sas_Q13` reconsidered.
2. **Fit link (Q14, Q22).** As stated it covers only the table fitted on, and is vacuous when that table is empty. Either it also covers the tables the model scores (or the terms come from the fixed MODEL list of `train.sas`), or the two requirements are not demanded when the training part is empty.
3. **`best8` link and Q25.** Real BEST8. does not satisfy the 5·10⁻⁸ bound: the translator's evidence has 0.0000714285 stored as 0.000071, a relative error near 6·10⁻³. The Q25 proof uses the closeness clause to get the floor below 1/max(nT, nV). So Q25 is proved under a link the program does not meet. The observed values still satisfy the weaker fact the proof needs, but that was not established. The link needs restating and Q25 re-proving.
4. **`score` without a stop.** The corrected wiring departs from the brief's sentence "a step returns none when the stop unit of its script is true" when `score` is called with a model no fit returned. No contract depends on it. It needs confirming, or the alternative (two more existence parameters) chosen.
5. **Text cells in the raw file (Q27, second clause).** Under the import link a raw text `1` in `MonthlyIncome` and the number 1 give the same imported table, so no program could reject one and accept the other. The SAS check also accepts blank, `.` and `NA` texts that G39 rejects.
6. **Import link readings to confirm or strike:** missing delivered as blank, period or NA; non-numeric cells kept as they are; same column names in order; the clean precondition required only when the check does not stop.

Not settled by this round:

- Q27's first clause (a valid input makes every step return a result) and the rest of its second clause were not attempted.
- Q23's other clauses (outcome recorded, Gini, Somers' D) were not examined.
- Raw tables with no delivery leave the import unconstrained; some fail `TrainOK`, so an adversarial import could let `features` return a result on them.
- Contracts that quantify over the seed are about the parameter `split`; `feature_engineering.sas` line 326 fixes seed 42.
- `roc_stats` is total in Lean, but SAS produces no table when the validation set lacks a class; AUC results there are outside the unit's precondition.
- `SasLinks` was not proved satisfiable as a separate item. The three accepted disproofs of Q23, Q26 and Q27 each prove it for one parameter choice.
- A training file with a text id passes the real check (`feature_engineering.sas` line 86) but is outside the Lean model (`credit_imputed_precond`).
- `neg:sas_Q13_neg` carries an unused dependency on `thm:sas_Q1`.
- No witness was replayed on real SAS.

Files read: `/Users/cristophersalvi/GitHub/credit-risk-migration/migration/proofs/legacy-meets-requirements/brief-prover.md`.
