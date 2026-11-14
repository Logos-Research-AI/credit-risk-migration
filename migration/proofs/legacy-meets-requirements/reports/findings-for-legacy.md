# Findings for the legacy SAS code

One entry per requirement not proved about the SAS. Paths are under `/Users/cristophersalvi/GitHub/credit-risk-migration/legacy/`. "Machine-checked" means the blueprint compiled the proof; the blueprint's trust layers are off. All inputs are raw CSV values; unlisted numeric columns are 0.

Proved, with no finding: Q8, Q16, Q19, Q20, Q21. For the training score file these rest on the proved theorem that the two scoring chains of `train.sas` agree, at the real numbers.

---

## Q1: income imputation has no fallback. `legacy-violates-requirement`

- **Requirement.** A missing `MonthlyIncome` becomes the median known income of the applicant's age group in training. If that group has no known income, it becomes the median of all known training incomes. Every applicant ends with an income.
- **Counterexample.** Two training rows, empty test file.
  - Row A: `VAR1`=1, `age`=25, `MonthlyIncome`=5000.
  - Row B: `VAR1`=2, `age`=45, `MonthlyIncome` missing.
- **Demanded.** Row B (group 40-49, no known income) gets income 5000.
- **SAS produces.** Row B keeps a missing `monthly_income` in the feature files.
- **Cause.** `feature_engineering.sas` 58-73: the `WHERE` on line 71 removes missing incomes before `GROUP BY`, so the group has no median row. Lines 96-120: the CASE on line 103 returns `b.median_income` from the left join (118-119), with no fallback.
- **Smallest change.** Compute the overall median of known training incomes once, and use `coalesce(b.median_income, <overall median>)` in line 103.
- **Status.** Machine-checked and independently confirmed. It occurs whenever an age group has a missing income and no known one.

## Q2, Q3, Q4, Q5, Q10: not decided, no SAS defect found. `needs-ruling` (Q2), `open` (Q3, Q4, Q5, Q10)

- **Requirements.**
  - Q2: missing dependents become 0.
  - Q3: missing-value indicators.
  - Q4: caps at 200 % and 500 %.
  - Q5: total late payments is the sum of the three counts.
  - Q10: the split covers every applicant once, at 70/30 within one.
- **Why undecided.** The formal contracts are false only on input tables that no CSV import can deliver to the first SAS step:
  - an income or dependents value that no decimal text of at most 32 characters denotes, such as 1/3;
  - a raw file that already has a column `MonthlyIncome_num` or `NumberOfDependents_num`.

  On those tables the model leaves PROC IMPORT unconstrained. No SAS line is at fault.
- **On every table that can be delivered.** Reading the SAS model, all five hold:
  - `feature_engineering.sas` 89-93 sets missing dependents to 0 and sets the indicators;
  - lines 200-201 cap with MIN;
  - line 130 sums the three counts;
  - the join yields one row per applicant, and the split only adds and drops `Selected`.

  For Q5 this is machine-checked in an unaccepted draft. For the others it is a hand argument.
- **What is missing.** A decision by the requirements owner: restrict the input conditions to deliverable tables, or accept the contracts as false for this modelling reason.
- **Notes for whoever changes the code.**
  - A raw file with a column named `MonthlyIncome_num` or `NumberOfDependents_num` would be overwritten by lines 44-56.
  - The 70/30 size clause of Q10 rests on an assumption about PROC SURVEYSELECT, not on SAS code.

## Q6: serious-delinquency flag tests `> 0`, not `>= 1`. `legacy-violates-requirement`

- **Requirement.** `flag_serious_delinquency` is 1 exactly when there is at least one 90-day delinquency, formally `1 <= n`.
- **Counterexample.** One training row: `VAR1`=1, `age`=25, `MonthlyIncome`=5000, `NumberOfTimes90DaysLate`=0.5.
- **Demanded.** Flag 0.
- **SAS produces.** Flag 1.
- **Cause.** `feature_engineering.sas` line 170: `flag_serious_delinquency = (num_late_90_plus > 0);`. `predict.sas` line 169 has the same test.
- **Smallest change.** Use `>= 1` on line 170.
- **Weight.** The two tests differ only for a count strictly between 0 and 1. The input conditions do not say counts are whole numbers. If the requirements owner adds that, the SAS meets Q6. The other seven flags match the requirement by reading.
- **Status.** Machine-checked and confirmed.

## Q7: total risk flags sums five flags, not eight. `legacy-violates-requirement`

- **Requirement.** `total_risk_flags` is the number of the eight Q6 flags that are set.
- **Counterexample.** One training row: `VAR1`=1, `age`=40, `MonthlyIncome`=5000, `NumberOfOpenCreditLinesAndLoans`=0.
- **Demanded.** 1, because `flag_few_credit_lines` is 1.
- **SAS produces.** 0.
- **Cause.** `feature_engineering.sas` 177-179: the SUM omits `flag_very_high_utilization`, `flag_many_dependents` and `flag_few_credit_lines`.
- **Smallest change.** Add those three flags to the SUM.
- **Status.** Machine-checked and confirmed. It fails for any applicant with one of the three omitted flags set.

## Q9: both interaction features differ from the requirement. `legacy-violates-requirement`

- **Requirement.** `utilization_debt_interaction` is utilization % × debt ratio %, uncapped. `age_income_interaction` is age × ln(income) when income is above 0.
- **Counterexample.** One training row: `age`=25, `RevolvingUtilizationOfUnsecuredL`=1, `DebtRatio`=1, `MonthlyIncome`=5000.
- **Demanded.** Utilization interaction 100 × 100 = 10000; age interaction 25 × ln(5000).
- **SAS produces.** 100, and 25 × ln(5001).
- **Cause.**
  - `feature_engineering.sas` line 197 divides the product by 100.
  - Line 196 uses `log_monthly_income`, which line 191 sets to `log(monthly_income + 1)`.
  - The same statements are in `predict.sas` 196, 195 and 190.
- **Smallest change.** Drop `/ 100` on line 197, and use `age * log(monthly_income)` on line 196. Fixing one line only leaves Q9 false.
- **Status.** The utilization clause is machine-checked and confirmed. The log clause is by reading only.

## Q11: same seed, same split. `by-construction`, not a result about the SAS

- The formal statement holds for any pipeline, because the split is modelled as a function of seed and table. It says nothing about PROC SURVEYSELECT.
- `feature_engineering.sas` line 212 hard-codes `seed=42` and takes no seed from outside.
- **What is missing.** Evidence that PROC SURVEYSELECT is deterministic for a given seed and table.

## Q12: test set gets the same feature engineering. `needs-ruling`

- **What is machine-checked.** The formal Q12 demands that the test predictions table equal the scoring function's output on some feature table. That can never hold for a non-empty test file:
  - `predict.sas` 275-281 KEEPs fifteen columns;
  - the validation score file keeps every feature column plus `base_score` (`train.sas` 251), `score_range` and `base_rate`; the DROP at 331-335 does not remove them.
- **Why this is not a code finding.** The independent check found that the documentation does not ask for the two files to share a layout. Changing the KEEP would alter a published file and would not make Q12 true.
- **Case needing a ruling.** Which columns of `test_predictions.csv` must agree with the scored feature table.
- **The real deviation** is the Q13 finding below. Q6, Q7 and Q9 are likely mirrored in `predict.sas`; this was not examined.

## Q13: test incomes are imputed from the test file. `legacy-violates-requirement`

- **Requirement.** A missing test income is replaced by the **training** median for the applicant's age group.
- **Counterexample.**
  - Training: one row, `age`=25, `MonthlyIncome`=5000.
  - Test: (`VAR1`=1, `age`=25, `MonthlyIncome`=7000) and (`VAR1`=2, `age`=25, income missing).
- **Demanded.** Test applicant 2 gets income 5000.
- **SAS produces.** 7000, the median of the test file's own under-30 incomes.
- **Cause.** `predict.sas` 58-73 builds `work.test_income_medians` from `work.test_raw_clean`. Lines 96-119 impute from it (expression at line 102, join at 117-118). `predict.sas` never reads the training data. The training medians (`feature_engineering.sas` 58-73) are a WORK table that is not persisted.
- **Smallest change.** Persist or recompute the training medians and join `work.test_cleaned` against them, with the Q1 fallback to the overall training median.
- **Status.** Machine-checked and confirmed, for every model. The missing-dependents clause was not exercised; `predict.sas` 89-93 does set 0. The formal contract will stay false until the Q12 layout question is settled.

## Q14: an applicant can be left without a probability. `legacy-violates-requirement`

- **Requirement.** Every applicant in the training, validation and test sets receives a probability in [0, 1], a score, a grade, a recommendation and a prediction.
- **Counterexample.**
  - Test: one row, `VAR1`=2, `age`=45, `MonthlyIncome` missing.
  - Training: two rows, (`age`=25, income 5000) and (`age`=45, income missing).
  - Model: any model containing an income-derived term. The shipped `output/model_coefficients.csv` contains `log_monthly_income`, `income_per_dependent` and `age_income_interaction`.
- **Demanded.** A probability in [0, 1] for the test applicant.
- **SAS produces.** `pd_logistic` missing. The row is still written with prediction 0, a missing score, grade F and Decline, so the applicant is silently declined.
- **Cause.**
  - `predict.sas` 58-73 (WHERE at 71): the age group has no median row.
  - Lines 96-119: the CASE at 102-104 leaves the income missing.
  - Lines 190 and 195: the log and the interaction are missing.
  - Lines 207-212 and 214-222: the logit and probability are missing.
  - The same defect exists on the training side through `feature_engineering.sas` 58-73 and 96-120.
- **Smallest change.** The Q1 fallback in both scripts, so `monthly_income` can never stay missing. For `predict.sas`, fall back to the training medians.
- **Status.** Machine-checked and confirmed. It is conditional on the model containing an income-derived term.

## Q15: the score is rounded. `legacy-violates-requirement`

- **Requirement.** Score = 600 + 250 × (1 − probability), unrounded. Ruling G1 quotes bands at 812.5, 787.5 and 762.5.
- **Counterexample.** Any scored row with probability 0.25.
- **Demanded.** 787.5.
- **SAS produces.** An integer; 788 under SAS rounding.
- **Cause.** `round(...)` around the score in `predict.sas` 235-237 (ROUND on 237), `train.sas` 251-253 (validation) and `train.sas` 217-219 (training).
- **Smallest change.** Remove ROUND in all three places.
- **Status.** Machine-checked on the test path and confirmed. The two `train.sas` places are the same code, by reading. The witness model is a constant one that the fit assumption allows; the defect holds for any probability where 250 × (1 − p) is not an integer.

## Q18: the grade is cut on the score, not on the probability. `legacy-violates-requirement`

- **Requirement.** A when p < 10 %; B when p < 15 %; C when p < 25 %; D when p < 35 %; E when p ≤ 50 %; F when p > 50 %.
- **Counterexample.** Any scored row with probability 0.20.
- **Demanded.** Grade C.
- **SAS produces.** Score 800, which is ≥ 750, so grade A.
- **Cause.** The ladders test `credit_risk_score` at 750 / 700 / 650 / 600 / 550: `predict.sas` 240-245, `train.sas` 255-260 (validation) and `train.sas` 222-227 (training).
  - The SAS gives A up to p ≈ 40 %, B to ≈ 60 %, C to ≈ 80 % and D to 100 %.
  - E is unreachable, and F arises only from a missing probability.
  - The grade is wrong for every present p ≥ 10 %.
- **Smallest change.** In all three ladders, test `pd_logistic` at 0.10 / 0.15 / 0.25 / 0.35 / 0.50, with an explicit branch for a missing probability.
- **Status.** Machine-checked on the test path and confirmed.

## Q22: no threshold rows when the validation set is empty. `legacy-violates-requirement`, with a caveat

- **Requirement.** The threshold metrics are reported for at least one threshold. The exemption for empty classes covers the values, not the existence of the rows.
- **Counterexample.** A training file of one applicant. A 70 % sample of 1 to 3 rows selects all of them, so the validation set is empty.
- **Demanded.** A non-empty threshold table.
- **SAS produces.** No rows.
- **Cause.** `metrics_calculation.sas` 122-158: the row is written inside `if eof then do; ... output; end;` (line 142) after `set ... end=eof` (line 134). A DATA step stops at SET on an empty input. The calls are at 161-165 and the concatenation at 168-171. The empty validation set comes from `feature_engineering.sas` 209-221.
- **Smallest change.** Write one row per threshold even when the confusion table is empty, with the metrics missing. For example, compute the four counts with a PROC SQL aggregate.
- **Caveat.** This occurs only with an empty validation set (at most 3 applicants).
  - On that run the ROC step is outside the range where the SAS model was checked.
  - The real program would probably fail earlier, at the model fit.
  - Two independent checks disagree on whether the witness is admissible.
  - The owner may prefer to rule that the requirement excuses this case.
- **Not examined.** Whether a validation row with a missing probability breaks the "counts sum to the number scored" clause.

## Q23: a KS tie adds a summary row with AUC and Gini missing. `legacy-violates-requirement`

- **Requirement.** Every row of the validation summary carries the AUC, Gini = 2 × AUC − 1 and Somers' D = Gini.
- **Counterexample.** Three validation rows with equal probabilities and outcomes 1, 0, 1 in sorted order. The proof uses 7 training rows with an intercept-only model.
- **Demanded.** AUC and Gini present on every summary row.
- **SAS produces.** The KS maximum (1/2) is attained on two rows, so `ks_statistic` has two rows and the summary has two rows. The second has AUC, Gini and PSI missing.
- **Cause.** `metrics_calculation.sas` 104-111 selects every row whose `ks_value` equals the maximum. Lines 330-345 MERGE without BY, which propagates the extra rows. Lines 390-413 have the same defect. This matches a real SAS run, `experiments/x13_freq_sql_merge.log`.
- **Smallest change.** Make `ks_statistic` a single row. For example, take `max(ks_value)` with `min(pd_logistic)` over the rows attaining it, or keep the first observation.
- **Status.** Machine-checked and confirmed. Whether the first summary row meets Q23 once this is fixed was not examined. A replay on real SAS needs about 10 training rows.

## Q24: KS is overstated when probabilities tie. `legacy-violates-requirement`

- **Requirement.** KS is the maximum separation between the cumulative distributions of defaulters and non-defaulters.
- **Counterexample.** Two validation rows, one defaulter and one non-defaulter, with the same probability. This happens for any two applicants with identical features and opposite outcomes.
- **Demanded.** KS = 0, because the distributions coincide.
- **SAS produces.** KS = 1.
- **Cause.** `metrics_calculation.sas` 86-102 computes `ks_value` after every observation, including between rows that share a probability. Lines 104-111 take the maximum over all rows. The sort at 74-77 is by `pd_logistic` only.
- **Smallest change.** Evaluate `ks_value` only at the last observation of each distinct probability: `by pd_logistic;` and `if last.pd_logistic`.
- **Status.** Machine-checked and confirmed, whatever the order inside the tie. The summary table carries the same value; that clause was not examined.

## Q25: PSI ranks each data set separately. `legacy-violates-requirement`

- **Requirement.** Ten bins are cut from the training scores at nearest-rank deciles. Validation scores are placed in the same bins, and a score equal to a cut goes to the lower bin. PSI is 0 only when the shares agree in every bin.
- **Counterexample.** Training scores 725 and 725; validation scores 800 and 800. The proof uses 4 training rows and a one-term model.
- **Demanded.** PSI > 0: all training scores are in the lowest bin and all validation scores in the highest.
- **SAS produces.** PSI = 0, "No significant change".
- **Cause.** `metrics_calculation.sas` 249-255 and 257-262 run PROC RANK GROUPS=10 on each data set independently, so each side fills its own deciles. Lines 264-278 and 280-288 carry the result through. On large untied data this gives PSI = 0 whatever the scores are; that is the checker's arithmetic, not a Lean result.
- **Smallest change.**
  - Compute the nine nearest-rank decile cuts of the training scores, and assign both data sets with `score > cut`.
  - Bin `credit_risk_score`; the SAS ranks `pd_logistic`.
  - Keep all ten bins in the join; the inner join drops bins that are empty on one side.
  - Define a positive contribution when one share is 0.
- **Status.** Machine-checked and confirmed.

## Q26: decile table can have fewer than ten rows. `open`

- **Requirement.** Exactly ten rows, deciles 1 to 10, each once.
- **What exists.** A machine-checked counterexample with an empty validation set (0 rows against 10). The independent check rejected it: the same run is outside the range where the ROC step of the SAS model was checked.
- **What the code does, by reading.** `metrics_calculation.sas` 182-188 (`proc rank ... groups=10 descending`) and 190-206 (`group by decile`) produce one row per decile that PROC RANK actually assigns. Fewer than ten validation rows, or tied scores, give fewer than ten rows.
- **What is missing.** A counterexample with a non-empty validation set containing both outcomes, for example 3 validation rows with tied scores.
- **Likely change.** Build the table from a fixed list of deciles 1 to 10 left-joined to the grouped data. What an empty decile should report needs a ruling.

## Q27: no input validation. `legacy-violates-requirement`

- **Requirement.** On an input that does not meet the input conditions, the pipeline stops with an error and produces no result.
- **Counterexample.** One training row with `SeriousDlqin2yrs`=2.
- **Demanded.** No feature files.
- **SAS produces.** Both feature files, with the invalid target carried through.
- **Cause.** `feature_engineering.sas` has no check between PROC IMPORT (28-33) and the exports (267-278). None of the four scripts contains an abort or a condition test. `predict.sas` 27-56 is the same for the test file.
- **Smallest change.** After the import in `feature_engineering.sas`, test the conditions and abort before any export:
  - required fields non-missing;
  - target in {0, 1};
  - at least one known income;
  - `VAR1` unique.

  Do the same for the test file in `predict.sas`. By ruling G23, a faulty test file withholds only the test predictions.
- **Status.** The training-file clause is machine-checked and confirmed. The test-file clause is false for the same reason but not separately proved.
