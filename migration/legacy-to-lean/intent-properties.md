# Intent properties (draft, not formalised)

What each part of the pipeline was meant to guarantee, with the source of the intent and
whether the SAS code as written (as translated in `sas-credit-risk-spec`) is expected to
satisfy it. "Fails" is a finding about the SAS code, not about the translation.

Sources: `MC` = MODEL_CARD.md, `RM` = README.md, `JR` = judge/README.md (findings section),
`fe` / `tr` / `me` / `pr` = feature_engineering.sas / train.sas / metrics_calculation.sas /
predict.sas, with line numbers.

## Feature engineering

| # | Property | Unit | Source of intent | Expected |
|---|---|---|---|---|
| I1 | `MonthlyIncome` after conversion is the number written in the raw file, and missing exactly when the raw field is `NA`. | credit_raw_clean | fe:48-49 "Convert to numeric" | Holds of the unit as a function of the imported table. **Fails end to end**: PROC IMPORT reads the column as `$5.`, so incomes of 100,000 or more are cut to five digits before this step (JR, 77 rows). Out of this pass's scope (import is a parameter), stated here because the intent is about the raw file. |
| I2 | Every applicant gets an age group in 1..5, and the groups partition the ages: below 30, 30-39, 40-49, 50-59, 60 and over. | credit_cleaned, income_medians | fe:78-83, 62-68 | Holds for present ages. A missing age is put in group 1 (missing compares low): the bands were not meant to include it. |
| I3 | The age group used to compute a median is the same as the age group used to look it up. | income_medians, credit_cleaned | fe:58, 96 "Merge and impute income" | Holds (the two CASE/IF chains agree on every input, missing age included). |
| I4 | After imputation, `monthly_income` is present for every applicant. | credit_imputed | MC "MonthlyIncome: Median by age group"; RM "automatically imputes missing values" | **Fails** when an age group has no present income at all: the group has no row in `income_medians`, the left join finds nothing, and the income stays missing. Reached by scenario `edge_predict` for the predict twin. |
| I5 | `monthly_income` equals the original income when it was present, and the median of the present incomes of the applicant's age group otherwise. | credit_imputed | fe:103-105 | Holds. |
| I6 | `MonthlyIncome_missing` is 1 exactly when the income was missing before imputation; `Dependents_missing` likewise; `num_dependents` is never missing. | credit_cleaned, credit_imputed | fe:85-93; MC "Missing value indicators" | Holds. |
| I7 | The imputation does not reorder or drop applicants: one output row per input row. | credit_imputed | fe:96-120 | One row per input row holds when age groups are unique in `income_medians` (they are). Order **fails**: the join order is not determined, and the 70/30 split depends on it (JR). |
| I8 | A risk flag is 1 only when its variable is present and beyond its threshold. | credit_features | fe:164-174; RM "Risk Flags" | Holds for the `>` and `>=` flags (a missing value fails them). **Fails** for `flag_low_income` (`monthly_income < 2500`) and `flag_few_credit_lines` (`num_credit_lines <= 2`): a missing value sets the flag. |
| I9 | Each category variable (`credit_util_category`, `debt_category`, `age_category`) takes a value in its range, and the bands neither overlap nor leave a gap. | credit_features | fe:138-162 | Holds for present values. A missing value falls in category 1 ("Low" / "Young"), which the bands were not meant to say. |
| I10 | `total_late_payments` is the sum of the three late-payment counts; `has_delinquency` is 1 exactly when it is positive. | credit_features | fe:129-133 | Holds; a missing count is treated as 0 by `SUM()`, and all three missing give a missing total and `has_delinquency = 0`. |
| I11 | `financial_health` is between 0 and 100. | credit_features | fe:181 "Financial health score (0-100)"; MC | Holds. The minimum reachable value is exactly 0 (100 - 15 - 15 - 20 - 20 - 30), so `max(0, ...)` never acts. |
| I12 | `total_risk_flags` counts the risk flags that are set. | credit_features | fe:176 "Total risk flags" | **Fails as named**: it sums five of the ten flags (high utilization, high debt ratio, serious delinquency, multiple delinquencies, low income). |
| I13 | "Income per dependent (handle division by zero)": `income_per_dependent` is defined for every applicant with a present income. | credit_features | fe:150-152 | Holds for `num_dependents >= 0`. The guard `num_dependents > 0` does not protect the next line, `credit_lines_per_person = num_credit_lines / (num_dependents + 1)`, which is missing for `num_dependents = -1`. |
| I14 | The log transforms are defined for every applicant ("add 1 to handle zeros"). | credit_features | fe:190-193 | Holds for values of at least 0; missing for a value of -1 or below, and for a missing income (I4). |
| I15 | The capped variables do not exceed their caps (200 and 500) and equal the original below the cap. | credit_features | fe:199-201; MC "Outlier capping" | Holds for present values. **A missing value becomes the cap** (`min(., 200)` is 200): a missing utilization is scored as the most extreme one. |
| I16 | Training and validation sets partition the applicants: every applicant is in exactly one. | credit_train_validation | fe:204-221; MC "70% / 30%" | Holds. The 70/30 proportion and its reproducibility ("Same seed = same split", RM) are properties of PROC SURVEYSELECT and of the join order, not of this unit; the second **fails** (JR). |
| I17 | The feature engineering applied to the test set is the same as that applied to the training set. | test_raw_clean .. test_features vs their twins | pr:122 "Same as Training"; RM "Handles missing values consistently" | The row-wise steps agree. **Fails** for imputation: test incomes are imputed with medians of the test set, not of the training set (JR), and test incomes are not truncated at import while training incomes are. |

## Scoring and grades

| # | Property | Unit | Source of intent | Expected |
|---|---|---|---|---|
| S1 | Every eligible applicant receives a probability. | logit_scored_train_output, logit_scored_valid, test_scored | tr:85-87, 157-168; pr:207-222 | **Fails** when a covariate of the fitted model is missing (I4): the probability is missing. Also missing when `exp(-logit)` overflows (logit below about -709.8): the intended probability there is 0, and SAS gives a missing value. |
| S2 | A present probability lies in [0, 1]. | logit_scored_valid, test_scored | MC "probability" | Holds for the DATA-step formula `1 / (1 + exp(-x))`. For the training set it is a property of the parameter `invLink`. |
| S3 | `pred_logistic` is 1 exactly when the probability is at least 0.5, and is never missing. | logit_scored_train, logit_scored_valid, test_predictions | tr:105, 165; pr:232 | Holds; a missing probability gives 0 ("no default"), which is a prediction nobody made. |
| S4 | The credit risk score lies in 300..850. | risk_scores_*, test_predictions | tr:216 "300-850 scale like FICO"; MC | Holds trivially and **the stated range is wrong**: with a probability in [0, 1] the score lies in 600..850. |
| S5 | The score decreases (weakly) as the probability increases. | risk_scores_*, test_predictions | MC score formula | Expected to hold (rounding is monotone). |
| S6 | Every scored row with a present probability gets a grade in A..F. | risk_scores_*, test_predictions | tr:221-227 | Holds; in fact only A..D occur. |
| S7 | The grade bands neither overlap nor leave gaps: A 750+, B 700-749, C 650-699, D 600-649, E 550-599, F below 550. | risk_scores_*, test_predictions | MC and RM grade tables | Holds as a partition of the scores. |
| S8 | Each grade corresponds to the default-probability band of the model card (A below 10%, B 10-15%, C 15-25%, D 25-35%, E 35-50%, F above 50%). | risk_scores_*, test_predictions | MC and RM grade tables | **Fails.** From score = round(600 + 250 (1 - pd)): A is pd up to about 40%, B about 40-60%, C about 60-80%, D about 80-100%. Grade E is unreachable and F occurs only for a missing probability (JR). |
| S9 | The recommendation and interest rate are functions of the grade: A and B Approve, C Review, others Decline; rates 5, 7, 9, 12, 15, 20%. | risk_scores_*, test_predictions | tr:229-241; MC table | Holds, up to binary rounding of `0.05 + 0.02` and the like (the sums are not the decimal 0.07, 0.09, 0.12, 0.15, 0.20). |
| S10 | An applicant whose probability cannot be computed is not silently approved. | risk_scores_*, test_predictions | implied by the grade table | Holds: a missing probability gives grade F, Decline, 20%. But see S3: the same row is predicted "no default". |
| S11 | Training and validation scores are produced by "the same scoring logic". | risk_scores_train vs risk_scores_validation vs test_predictions | tr:250 "Same scoring logic as training" | The three DATA steps agree. The probabilities do not come from the same computation: training uses PROC LOGISTIC's own predicted probability, validation and test use `1 / (1 + exp(-x))` on PROC PLM's linear predictor; they can differ in the last bits. |
| S12 | The exported score files contain no PROC LOGISTIC working columns. | risk_scores_*_clean | tr:325-335 | Holds vacuously: none of the dropped names exists. |

## Training-stage metrics

| # | Property | Unit | Source of intent | Expected |
|---|---|---|---|---|
| T1 | The confusion counts TP, TN, FP, FN sum to the number of scored rows. | confusion_matrix_train, training_metrics (and validation twins) | tr:108-139 | Holds when `default_flag` is 0 or 1 on every row. A row with a missing `default_flag` appears in the PROC FREQ output with its own level and is counted in none of the four. |
| T2 | Precision, recall, F1 and accuracy are the standard functions of the counts, and are missing rather than an error when undefined. | training_metrics, validation_metrics, confusion_metrics | tr:127-136; me:142-153 | Holds. F1 is missing when precision or recall is missing or when both are 0. |
| T3 | Each metric lies in [0, 1] when present. | same | implied | Expected to hold. |
| T4 | AUC is the probability that a random defaulter has a higher predicted probability than a random non-defaulter, ties counting one half. | roc_train, roc_valid, roc_stats | tr:288-306; MC "AUC-ROC" | Holds up to SAS's tie rule, which is a grouping and not a pairwise tolerance: probabilities are grouped from the largest down, a value joining a group when it is at most 3184525836262887 * 2^-78 (about 1.0537e-8) below the group's largest value, and a pair counts one half exactly when both probabilities are in one group. So "higher" means "in a higher group", and the property as written holds exactly when no two distinct probabilities share a group (X07, X08). |
| T5 | `model_summary` reports the sizes of the training and validation sets. | model_summary | tr:375-376 | **Fails**: the two counts are the constants 105000 and 45000 ("Approximate"). |

## Validation metrics

| # | Property | Unit | Source of intent | Expected |
|---|---|---|---|---|
| V1 | Gini = 2 AUC - 1. | auc_summary | me:61; MC "Gini" | Holds. |
| V2 | KS is the maximum over cut-offs of the absolute difference between the cumulative share of non-defaulters and of defaulters, and lies in [0, 1]. | ks_calculation, ks_statistic | me:71-111; RM "KS Statistic" | Holds on untied probabilities. **Depends on row order inside ties** (JR): the running difference is evaluated after every row, not after every distinct probability, so with tied probabilities it can exceed the true KS, and it depends on the stable-sort order. A row with a missing `default_flag` is counted as a defaulter in the running count but not in the total, so `cum_pct_bad` can exceed 1. |
| V3 | `ks_statistic` has exactly one row. | ks_statistic | me:104-111, and the MERGE at 331-334 | **Fails** when the maximum is attained on several rows: one row each, and the extra rows carry missing AUC and PSI into `validation_summary` with status "Needs Improvement". |
| V4 | The five threshold rows are the confusion metrics of the validation set at 0.3, 0.4, 0.5, 0.6, 0.7. | confusion_metrics, threshold_analysis | me:117-171 | Holds. The 0.5 row equals `validation_metrics` of train.sas when the validation scores are the same. |
| V5 | The ten deciles have (nearly) equal size, decile 1 holding the highest probabilities. | decile_data | me:182-188; RM "Decile Analysis" | Holds on untied data. With ties, groups are unequal and some decile numbers can be absent. Rows with a missing probability form an eleventh group with a missing decile. |
| V6 | Capture rates sum to 1 over the deciles, and cumulative capture reaches 100% at the last decile. | decile_analysis, cumulative_lift | me:201, 232 | Holds up to rounding when the defaults total is present and positive. |
| V7 | Lift of a decile is its default rate divided by the overall default rate; cumulative lift ends at 1. | decile_analysis, cumulative_lift | me:202, 233 | Lift holds. **Cumulative lift fails to end at exactly 1**: it divides by the overall rate after it has been rounded to the 8 characters of `BEST8.` in a macro variable (0.066667 for 0.0666...), and `cum_count` includes rows with a missing `default_flag` that the rate excludes. |
| V8 | PSI measures the shift between the training and validation score distributions: zero exactly when the two distributions agree on the bins, positive otherwise. | train_bins, valid_bins, psi_calculation, psi_summary | me:246-288; MC "PSI 0.0013" | **Fails.** Each data set is ranked into its own deciles, so on untied data every bin holds 10% on both sides and PSI is 0 whatever the shift (JR; the model card's 0.0013 is not what the code computes). It is non-zero only through ties and missing values. Bins present on one side only are dropped by the inner join. |
| V9 | The PSI interpretation bands partition the PSI values: below 0.1, 0.1 to below 0.25, 0.25 and above. | psi_summary | me:282-286 | Holds; a missing PSI is reported as "No significant change". |
| V10 | Calibration bins compare the mean predicted probability with the observed default rate, over 20 bins of equal size. | calibration_data, calibration_plot | me:295-316 | Holds on untied data; same caveats as V5. |
| V11 | The model status is "Production Ready" only when AUC >= 0.7, KS >= 0.3 and PSI < 0.25; otherwise "Requires Review" when AUC >= 0.65; otherwise "Needs Improvement". Exactly one status per run. | validation_summary | me:338-344 | The rule holds per row. The PSI condition is vacuous on untied data (V8), and is passed by a missing PSI. Exactly one row fails with V3. |
| V12 | `model_performance_metrics` carries the 0.5-threshold metrics of the validation set. | model_performance_metrics | me:390-413 | Holds, on the first row; with several KS rows (V3) the later rows carry missing values. |
| V13 | The Hosmer-Lemeshow test is acted on. | logistic_lackfit | tr:83 `lackfit` | **Fails**: printed (chi-square 121.9 on 8 df, p < .0001 in the reference run) and never read (JR). |
