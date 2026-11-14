# Requirements: what the documentation says the pipeline must do

Draft 5, 2026-11-15. Draft 3 was signed off on 2026-11-14; drafts 4 and 5 add rulings G28 to G38,
made after the requirements were checked against the SAS program and the program was corrected. The contradiction and the silences found in draft 1, and the twelve points
the first formalisation raised, are ruled on (section 4).

Source: the documentation only, `MODEL_CARD.md` (MC) and `README.md` (RM), cited by line. No
requirement here is taken from the SAS or Python code. The documentation is the authority: where
the code disagrees with a requirement, the code is wrong.

This text is to be formalised into the Logos blueprint `credit-risk-requirements`, which is then
pinned as a profile to the SAS blueprint. The formalisation must end with a proof that the
requirements are **consistent**: that some behaviour satisfies all of them at once.

## 1. Requirements

Each is a property of the pipeline's inputs and outputs. "Missing" means a value absent from the
data.

### Data preparation

| # | Requirement | Source |
|---|---|---|
| Q1 | A missing `MonthlyIncome` is replaced by the median of the known incomes of the applicant's age group in the training data; when that group has no known income, by the median of all known training incomes. A present income is unchanged. After this step every applicant has an income. The age groups are: under 30, 30-39, 40-49, 50-59, 60 and over (rulings G4, G5) | MC 58, RM 85, RM 268 |
| Q2 | A missing `NumberOfDependents` is replaced by 0; a present value is unchanged | MC 59, RM 86 |
| Q3 | For income and for dependents there is an indicator that is 1 exactly when the original value was missing | MC 50 |
| Q4 | Credit utilization is capped at 200 % and debt ratio at 500 %: the capped value equals the original when the original is at most the cap, and equals the cap when it is above. The raw file holds both as fractions; the feature columns, the caps and all thresholds are in percent, that is raw value × 100 (ruling G17) | MC 60, MC 136, RM 196-197 |
| Q5 | Total late payments is the sum of the three late-payment counts | MC 40, RM 205 |
| Q6 | Each risk flag is 1 when its condition holds and 0 when it does not (ruling G22): utilization above 75 %; utilization above 100 %; debt ratio above 43 %; at least one 90-day delinquency; at least 3 late payments in total; income below 2,500; at least 3 dependents; at most 2 credit lines | RM 208-216 |
| Q7 | The total risk flags count is the number of the eight risk flags of Q6 that are set | RM 220 |
| Q8 | The financial health score lies between 0 and 100 | MC 47, RM 219 |
| Q9 | The interaction features are age × log(income) and utilization × debt ratio. The logarithm is the natural one; the first feature is required only when income is above 0 (ruling G16). Utilization and debt ratio are the uncapped percent values (ruling G17) | MC 49, RM 223-224 |
| Q10 | The training data is split into a training set and a validation set that together contain every applicant exactly once. Their sizes are within one applicant of 70 % and 30 % of the training data (ruling G15) | MC 20, RM 93 |
| Q11 | The same seed gives the same split | RM 274 |

### Scoring new applicants

| # | Requirement | Source |
|---|---|---|
| Q12 | The test set receives the same feature engineering as the training set. No test feature file is published, so this reads: there is a test feature table whose rows obey Q1 to Q9, and each row of the test predictions agrees with the score of that table's row for the same applicant on every column the test predictions file publishes (rulings G13, G30) | RM 163 |
| Q13 | Missing values in the test set are handled consistently with training: a missing test income is replaced by the training median of Q1 for the applicant's age group, and missing dependents by 0 (ruling G10). It is read through the same test feature table as Q12, compared on the published columns (ruling G30) | RM 164 |
| Q14 | Every applicant, in the training, validation and test sets, receives a probability in [0, 1], a score, a grade, a recommendation and a prediction. There is no unscored applicant (ruling G3) | RM 165-166, MC 157 |

### Score, grades and decisions

| # | Requirement | Source |
|---|---|---|
| Q15 | Score = 600 + 250 × (1 − probability) | MC 118, RM 191 |
| Q16 | The score lies in 300..850 | MC 116 |
| Q17 | (withdrawn by ruling G1) The documentation's score ranges per grade are not a requirement. The score of Q15 is a displayed value; the grade is defined by Q18 | MC 122-129, RM 182-189 |
| Q18 | The grade is determined by the probability p: A when p < 10 %; B when 10 % ≤ p < 15 %; C when 15 % ≤ p < 25 %; D when 25 % ≤ p < 35 %; E when 35 % ≤ p ≤ 50 %; F when p > 50 % (rulings G1, G2) | MC 122-129, RM 182-189 |
| Q19 | Interest rate by grade: A 5 %, B 7 %, C 9 %, D 12 %, E 15 %, F 20 %, held as fractions: 5 % is 0.05 (ruling G18) | same |
| Q20 | Recommendation by grade: A and B Approve; C Review; D, E and F Decline | same |
| Q21 | An applicant is predicted to default exactly when the probability is at least 0.5 | MC 72, MC 85 |

### Validation metrics

| # | Requirement | Source |
|---|---|---|
| Q22 | Accuracy, precision, recall and F1 are the standard functions of the confusion counts, and the four counts sum to the number of scored applicants. These, and the AUC, Gini and KS of Q23 and Q24, are computed on the validation set; where a denominator is zero or a class is empty, nothing is required of the value (ruling G19). When the validation set is empty, no threshold row is required either (ruling G31) | MC 72-76, MC 91-98 |
| Q23 | Gini = 2 × AUC − 1, and Somers' D equals Gini | RM 136, MC 69-70 |
| Q24 | KS is the maximum separation between the cumulative distributions of defaulters and non-defaulters: one number per run | RM 137 |
| Q25 | PSI measures the shift between the training and validation score distributions. Ten bins are cut from the training scores and the validation scores are placed in the same bins. PSI is 0 when the two sets have the same share in every bin and positive otherwise. The cuts are the nearest-rank deciles of the training scores, without interpolation, and a score equal to a cut belongs to the lower bin (rulings G9, G20) | RM 141, MC 100-102 |
| Q26 | Decile analysis reports lift and capture rate by risk decile: exactly ten rows, deciles 1 to 10, each once. The capture rates sum to 1 when the validation set has at least one defaulter (ruling G21) | RM 140 |

### Inputs and errors

| # | Requirement | Source |
|---|---|---|
| Q27 | On an input that meets the conditions of section 3, every step produces its result. On an input that does not, the pipeline stops with an error and produces no result (rulings G3, G4, G11) | section 3 |

## 2. Reported figures, not requirements

The model card reports numbers from one run: AUC 0.8592 and 0.8564, the confusion matrix, PSI
0.0013, default rate about 6.7 %. They are observations, not properties to prove. One of them is
already known not to be reproducible: the SAS program gives PSI 0.0000 on that data.

## 3. Inputs the requirements assume

The documentation speaks of missing values in income and dependents only (MC 57-59, MC 135). So
the requirements are stated for raw inputs in which:

- only `MonthlyIncome` and `NumberOfDependents` may be missing; every other field is present;
- the training data has at least one known income;
- the outcome, where present, is 0 or 1;
- the row ids (`VAR1`) are distinct within each raw file (ruling G14);
- the raw files are tables a CSV file can hold: they have the columns of section 5 and no others,
  and every numeric value is a decimal number that can be written in at most 32 characters
  (ruling G28);
- the three late-payment counts, the number of dependents and the number of credit lines are
  whole numbers, zero or more (ruling G29);
- a known `MonthlyIncome` is zero or more (ruling G34).

On such inputs Q1 and Q2 leave no missing value, so no later requirement has to say what a
missing value does. A pipeline that meets an input outside these conditions must stop with an
error, not produce a result.

## 4. Rulings

| # | Ruling | Date |
|---|---|---|
| G1 | The probability bands are authoritative (Q18). The formula stays as the displayed score (Q15). The score-range column of the grade table is withdrawn (Q17): under the formula the bands correspond to scores above 825, 812.5 to 825, 787.5 to 812.5, 762.5 to 787.5, 725 to 762.5 and below 725, which the documentation should show instead | 2026-11-13 |
| G2 | Band edges: the lower edge is included, and 50 % belongs to E (see Q18) | 2026-11-13 |
| G3 | "Every applicant receives a probability" stands as written. An unscored applicant cannot occur; the pipeline must always be able to compute a probability (see Q14 and section 3) | 2026-11-13 |
| G4 | An age group with no known income uses the median of all known training incomes; no known income at all is an error (see Q1) | 2026-11-13 |
| G5 | The five age groups the code uses are adopted, and the documentation should state them. Age must be present (see Q1, section 3) | 2026-11-13 |
| G6 | No ruling needed: under section 3 and Q1, Q2 no variable in a risk-flag condition is missing | 2026-11-13 |
| G7 | Q16 stands as written (300..850). It follows from Q15, which gives 600..850; the documentation could say so | 2026-11-13 |
| G8 | The financial health score is required only to lie in 0..100; its definition is left to the code | 2026-11-13 |
| G9 | PSI bins are the training deciles, applied to both sets (see Q25) | 2026-11-13 |
| G10 | "Consistently" in the README means training medians for the test set (see Q13) | 2026-11-13 |

| G11 | "Must stop with an error" is a requirement (Q27). The pipeline's steps can end in an error, and the interface must be able to say so | 2026-11-14 |
| G12 | The interface names the fitted model: the model is fitted on the training feature set, and scoring (of the training, validation and test sets) takes that model. What a model is, is left open | 2026-11-14 |
| G13 | Q12 and Q13 are read through a test feature table that is not published (see Q12) | 2026-11-14 |
| G14 | Row ids are distinct within each raw file (section 3) | 2026-11-14 |
| G15 | "About 70 % and 30 %" means within one applicant (see Q10) | 2026-11-14 |
| G16 | log(income) is the natural logarithm and is required only when income is above 0 (see Q9) | 2026-11-14 |
| G17 | Utilization and debt ratio are fractions in the raw file and percent (raw × 100) in the feature files; caps and thresholds are in percent (see Q4, Q6, Q9) | 2026-11-14 |
| G18 | Interest rates are held as fractions (see Q19) | 2026-11-14 |
| G19 | The metrics are computed on the validation set; undefined cases are not constrained (see Q22) | 2026-11-14 |
| G20 | PSI cuts are nearest-rank deciles; a score equal to a cut goes to the lower bin (see Q25) | 2026-11-14 |
| G21 | The decile table has ten rows, deciles 1 to 10; the capture sum is required when there is a defaulter (see Q26) | 2026-11-14 |
| G22 | A risk flag is 0 when its condition does not hold (see Q6) | 2026-11-14 |

| G23 | Q27 with a faulty test file: only the test predictions are withheld; the feature, score and metrics tables of the training file are still produced | 2026-11-14 |
| G24 | Q11 holds by the form of the interface; whoever presents a program as a pipeline must show its split depends only on the training file and the seed | 2026-11-14 |
| G25 | Q3 and Q21: the indicator and the prediction are 1 exactly in their case; their value otherwise is only required not to be 1 | 2026-11-14 |
| G26 | Q22: with an empty class nothing is required of accuracy, precision, recall or F1 either | 2026-11-14 |
| G27 | Q22: F1 is required only when there is at least one true positive | 2026-11-14 |

| G28 | The input conditions cover only tables a CSV file can hold (section 3) | 2026-11-15 |
| G29 | Counts are whole numbers, zero or more (section 3). "At least one 90-day delinquency" and "more than none" then say the same | 2026-11-15 |
| G30 | Q12 and Q13 compare the test predictions with the scores of the test feature table on the published columns only, applicant by applicant | 2026-11-15 |
| G31 | Q22 requires no threshold row when the validation set is empty | 2026-11-15 |
| G32 | Q26 stands as written, including with tied scores and small validation sets | 2026-11-15 |
| G33 | The SAS program is to be corrected where it was proved to violate Q1, Q7, Q9, Q13, Q14, Q15, Q18, Q23, Q24, Q25 and Q27, by the smallest change that meets the requirement. For Q15 the rounding of the score is removed | 2026-11-15 |

| G34 | A known income is zero or more (section 3); a file with a negative income is rejected | 2026-11-15 |
| G35 | PSI with an empty bin: the SAS program's rule stands (an empty bin is given the share 0.5 divided by the size of the larger set). Q25 itself is unchanged: it fixes only whether PSI is 0 or positive | 2026-11-15 |
| G36 | "Produces no result" (Q27) is met by each script removing its own earlier output files when it starts | 2026-11-15 |
| G37 | The raw files are imported reading every row to size the columns, so no present value is cut | 2026-11-15 |
| G38 | The published files hold 12 characters per number. Requirements that relate two published columns (Q15, Q18) are about the values computed, and hold between printed values only to that precision; printed formats are a later pass | 2026-11-15 |

**Signed off by the owner on 2026-11-14** as formalised in the blueprint `credit-risk-requirements`
(58 items, consistency proved; report in `report.md`, audit in `../audit/requirements-audit.md`).

## 5. Names

The requirements speak of these files and columns. They are the interface of the pipeline (the
files it reads and writes), not its logic.

- Raw input (`cs-training.csv`, `cs-test.csv`): `VAR1` (row id), `SeriousDlqin2yrs` (outcome),
  `age`, `MonthlyIncome`, `NumberOfDependents`, `RevolvingUtilizationOfUnsecuredL`, `DebtRatio`,
  `NumberOfTime30-59DaysPastDueNotW`, `NumberOfTime60-89DaysPastDueNotW`,
  `NumberOfTimes90DaysLate`, `NumberOfOpenCreditLinesAndLoans`, `NumberRealEstateLoansOrLines`.
- Feature files (`model_features_train.csv`, `model_features_validation.csv`): `row_id`,
  `default_flag`, `age`, `age_group`, `monthly_income`, `MonthlyIncome_missing`, `num_dependents`,
  `Dependents_missing`, `credit_utilization`, `debt_ratio` (both in percent),
  `credit_utilization_capped`, `debt_ratio_capped`, `num_late_30_59`, `num_late_60_89`,
  `num_late_90_plus`, `num_credit_lines`, `total_late_payments`, the eight flags
  `flag_high_utilization`, `flag_very_high_utilization`, `flag_high_debt_ratio`,
  `flag_serious_delinquency`, `flag_multiple_delinquencies`, `flag_low_income`,
  `flag_many_dependents`, `flag_few_credit_lines`, `total_risk_flags`, `financial_health`,
  `log_monthly_income`, `age_income_interaction`, `utilization_debt_interaction`.
- Score files (`risk_scores_train.csv`, `risk_scores_validation.csv`, `test_predictions.csv`):
  `row_id`, `default_flag` (not in the test file), `pd_logistic` (the probability),
  `pred_logistic` (the prediction), `credit_risk_score`, `risk_grade`, `recommendation`,
  `interest_rate`.
- Metrics files: `validation_summary.csv` (`AUC`, `Gini`, `KS_Statistic`, `PSI`),
  `ks_statistic.csv` (`KS_Statistic`), `decile_analysis.csv` (`decile`, `capture_rate`, `lift`),
  `threshold_analysis.csv` (`threshold`, `accuracy`, `precision`, `recall`, `f1_score`).
