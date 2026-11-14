# Findings for the legacy SAS code

Eight requirements are not proved about the SAS program. Three call for a change to the SAS (Q23, Q26, Q27). Four call for a decision on the requirements or the model before the SAS can be judged, and no code change (Q12, Q13, Q14, Q22). One holds only by the form of the model (Q11).

All file paths are under `/Users/cristophersalvi/GitHub/credit-risk-migration/legacy/`.

---

## Q23: the published AUC is not the exact pairwise AUC

**Kind:** `legacy-violates-requirement`. Machine-checked and confirmed by an independent check.

**Requirement.** Gini = 2 x AUC - 1, Somers' D equals Gini, and the AUC in the validation summary is the exact pairwise AUC of the validation probabilities: a defaulter/non-defaulter pair counts as tied only when the two probabilities are equal.

**What the SAS does.** `metrics_calculation.sas` takes the AUC from PROC LOGISTIC's ROC statement. That statement groups probabilities lying within about 1.05e-8 of each other and counts a pair inside one group as tied, even when the values differ.

**Counterexample.**
- Training file of 4 applicants: ids 1 to 4, outcomes 0, 1, 1, 0, ages 30, 31, 31, 30, income 1, dependents missing, the other seven fields 0. Empty test file.
- The split puts applicants 3 and 4 in the validation set. The model is -60 + age.
- Validation probabilities: applicant 3 (defaulter) about 2.5e-13, applicant 4 (non-defaulter) about 9.4e-14. They are different numbers, also in double precision.
- Required: the defaulter scores strictly higher, so AUC = 1 and Gini = 1.
- Produced: the two values fall in one group, the pair is tied, AUC = 0.5 and Gini = 0.

**Lines responsible.** `metrics_calculation.sas` 70-77 (`roc 'Logistic Model' pred=pd_logistic` with `ods output ROCAssociation=work.roc_stats`). Lines 79-87 (`AUC = Area; Gini = 2 * Area - 1`) and 401-416 only carry the value into the summary.

**Smallest change (described, not made).** Compute the AUC from exact comparisons of `pd_logistic` instead of reading `Area` from ROCAssociation. For example, count over all defaulter/non-defaulter pairs the concordant pairs and the exactly tied pairs, and set AUC = (concordant + ties/2) / (defaulters x non-defaulters). The Mann-Whitney form from PROC RANK with `ties=mean` gives the same number. Alternatively the owner may rule that probabilities this close count as tied, and the requirement is restated.

**Limits.**
- The witness model is allowed by the model of the fit but is not what PROC LOGISTIC would return on two rows. The defect does not depend on the model: the translation record shows 36 to 40 such near-ties on each of four real 400-row fits.
- The witness was not replayed on real SAS. A replay needs a larger file, because the real split of 4 rows probably selects 3.
- Only the AUC-value clause was refuted. The other clauses were not examined.

---

## Q26: the decile table has fewer than ten rows on a small validation set

**Kind:** `legacy-violates-requirement`. Machine-checked and confirmed by an independent check.

**Requirement.** The decile analysis has exactly ten rows, deciles 1 to 10, each once, with lift and capture rate present. There is no minimum size for the validation set (ruling G21).

**What the SAS does.** PROC RANK assigns each validation row a decile, and the table is built with `group by decile`. A decile that no row received gets no row in the table.

**Counterexample.**
- The same 4-applicant training file as in Q23, with 2 rows in the validation set.
- Required: ten rows.
- Produced: at most two. The machine-checked fact is that the table never has more rows than the validation set. By hand, the two rows are deciles 4 and 7.

**Lines responsible.** `metrics_calculation.sas` 208-213 (`proc rank ... groups=10 descending`) and 216-231 (`create table work.decile_analysis ... group by decile order by decile`).

**Smallest change (described, not made).** Build the table from a fixed list of deciles 1 to 10, left-joined to the grouped data, so an unassigned decile still gets a row. An empty decile then needs defined values: count 0 and capture rate 0, which keeps the capture rates summing to 1. What its lift should be is a question for the requirements owner. The owner may instead prefer a ruling that sets a minimum validation size.

**Limits.**
- The failure is confined to validation sets of fewer than ten rows, or to heavily tied probabilities (tied values share one group; this second case is by reading only).
- Real PROC SURVEYSELECT on 4 rows probably selects 3, leaving one validation row, where the ROC step produces nothing. A replay should use about 10 rows with 7 selected. That larger case is argued, not machine-checked.

---

## Q27: a test file with a non-numeric row id is scored instead of rejected

**Kind:** `legacy-violates-requirement`. Machine-checked and confirmed by an independent check.

**Requirement.** On an input that does not meet the input conditions, the pipeline stops with an error and produces no result. The conditions require the row id `VAR1` to be a number; no field may hold a text value (ruling G39).

**What the SAS does.** The input check of `predict.sas` tests the id only for being non-blank. Every other required field goes through the `%num` macro; `VAR1` does not.

**Counterexample.**
- Training file: one valid row (id 1, outcome 0, age 1, income 1, dependents missing, the other fields 0).
- Test file: one row with `VAR1` = the text `A1`, outcome 0, age 1, income and dependents missing, the other fields 0.
- Required: test scoring stops and writes no predictions.
- Produced: `bad_row` = 0, no duplicate ids, the script does not stop, and `test_predictions` is written with `row_id` = `A1`.
- A real SAS run of the check agrees (`x21_review_round2` part E: `VAR1=A1 bad_row=0`, `row_id` of type Char).

**Lines responsible.** `predict.sas` line 93, `bad_row = (missing(VAR1) ...`. Line 118 (`count(*) - count(distinct VAR1)`) and the stop test at 123-130 then pass, and line 188 (`a.VAR1 as row_id`) carries the text on.

**Smallest change (described, not made).** In `predict.sas` line 93, replace `missing(VAR1)` by `missing(%num(VAR1))`. A text id then gives `bad_row` = 1 and the script stops at line 128.

**Same defect on the training side.** `feature_engineering.sas` line 86 has the same `missing(VAR1)` test and needs the same one-token change. This was found by reading; it could not be used as a formal counterexample because a text training id is outside what the Lean model covers.

**Limits.**
- Only the faulty-test-file clause was refuted. The clause "a valid input makes every step produce its result" was not attempted.
- There is no end-to-end SAS run of `predict.sas` with a text id; the evidence covers the check and the SELECT.
- A separate point needs a ruling and is not a code defect: the SAS check accepts the texts blank, `.` and `NA` in `MonthlyIncome` and `NumberOfDependents` as missing, while G39 rejects any text value. In the model, a raw text `1` and the number 1 reach the check as the same table, so no program could tell them apart.

---

## Q13: missing values in the test set handled as in training

**Kind:** `needs-ruling`. No defect was found in `predict.sas`. No code change is called for.

**State.** A formal disproof exists and the contract is flagged false, but the independent check found it is an artefact and should not count against the SAS.

**The case.** The input conditions for the test file allow the outcome field to be missing, and allow two encodings of "missing" in one column: a missing number in one row and a missing text in another. For such a table the model of PROC IMPORT says nothing, so the disproof lets the import return a row with an id that no applicant has. Real PROC IMPORT keeps rows and ids, and a CSV file has only one way to write an empty field.

**Ruling needed.** Either the input conditions fix one encoding of a missing field (in line with G39, "missing means absent"), or the model of the import delivers a missing outcome as a numeric missing.

**After the ruling.** Q13 must be decided again. By reading only, it is expected to hold: `predict.sas` joins the test rows to the training medians of `income_medians.csv` with the overall-median fallback, and sets missing dependents to 0.

---

## Q12: the test set receives the same feature engineering

**Kind:** `needs-ruling`. No defect was found in `predict.sas`. No code change is called for. Nothing here is machine-checked.

**The case.** The same as Q13: a test table whose outcome column mixes a missing number and a missing text meets the input conditions but leaves the model of the import unconstrained, so the contract is false as stated for a reason that is not the program's.

**Ruling needed.** The same as Q13.

**After the ruling.** By reading only, the contract looks true on every test file the import model covers: the test units mirror the training units that Q1 to Q9 were proved on, and the scoring uses the same expressions as the validation chain. The proof would be a test-side copy of the Q1 to Q9 proofs and was not written.

---

## Q22: confusion counts and threshold metrics

**Kind:** `needs-ruling`. No defect was found in the SAS. No code change is called for. Nothing here is machine-checked.

**Clause at issue.** The four confusion counts sum to the number of scored applicants. The counts include only rows that have a probability.

**The case.** A training file of one applicant. The split may select none of it for training (0 is within one of 70 % of 1), so the training part is empty and the validation part has one row. The model of the fit only says the model's variables are numeric columns of the table fitted on, which says nothing for an empty table. A model naming a column that does not exist then gives a missing probability: the counts sum to 0 where 1 is required.

**Why it is not a finding against the SAS.** PROC LOGISTIC does not fit on an empty table, and the case lies outside the conditions under which the scoring step was checked against SAS. No counterexample was found inside those conditions.

**Ruling needed.** Either the model of the fit also covers the tables the model is applied to (or the fit step returns no model on an empty training table), or Q22 is not required when the training part is empty.

**After the ruling.** Q22 is expected to be provable. The other clauses (five threshold rows, the standard formulas with their zero-denominator guards) look correct by reading `metrics_calculation.sas` 146-183.

---

## Q14: every applicant receives a probability, score, grade, recommendation and prediction

**Kind:** `open`. No defect was found in the SAS. No code change is called for. Nothing here is machine-checked.

**What is missing.** A stronger statement about the fit. As it stands, the model of the fit allows two things PROC LOGISTIC never does:
- a model that uses the outcome `default_flag` as a variable. The test features have no such column, so every test probability would be missing;
- a model fitted on an empty training part (the one-applicant case of Q22), naming a column the validation table lacks.

Both lie outside the conditions under which the scoring steps were checked against SAS, so neither is a disproof.

**What would close it.** One of:
- the model's variables come from the fixed list of the MODEL statement in `train.sas`, which excludes `default_flag` and `row_id`;
- every variable of the model is a numeric column of every table the model scores.

With either, Q14 is expected to be provable, conditional on the fit. By reading, every feature column is present under valid input and the probability formula lies in (0, 1). Q14 on the test set also waits on the ruling of Q12 and Q13.

**Related gap.** The proofs are over the real numbers. The exp overflow at `train.sas` 185 and `predict.sas` 305-313 (a very negative logit) cannot be seen there, so no contract in this round decides it.

---

## Q11: the same seed gives the same split

**Kind:** `open` as a statement about the SAS; the formal result is by-construction. No defect was found.

**What was shown.** In the model, the split is a function of the seed, so equal seeds give equal output by substitution. This uses no SAS unit.

**What is missing.** PROC SURVEYSELECT is outside the translated SAS. That it is deterministic in its seed is assumed by the form of the model, not proved. `feature_engineering.sas` line 326 passes a fixed `seed=42`, which is consistent with the requirement. Closing this needs a check against real runs: the same file twice, the same split.

**Same standing.** The size clause of Q10 (training and validation within one applicant of 70 % and 30 %) also follows only from the assumed behaviour of PROC SURVEYSELECT. The other clause of Q10, every applicant exactly once, is proved about the SAS.
