# Requirements formalisation report: draft 3

Blueprint `credit-risk-requirements`, id `006ff04c-d34c-4a9c-b230-ccd725b1be6f`.
Shared types from `credit-risk-foundation`, id `02011d57-8b15-43bb-8744-c6646fdfe9ae`.
Graph: https://platform-staging.logosresearch.ai/view/waad_AzureAd_b85254ea-5bb2-40b8-b836-c90bdf235fc9/006ff04c-d34c-4a9c-b230-ccd725b1be6f

Sources: `/Users/cristophersalvi/GitHub/credit-risk-migration/migration/requirements/requirements.md` (draft 3, rulings G1 to G22) and `/Users/cristophersalvi/GitHub/credit-risk-migration/migration/requirements/brief.md`.

## 1. Outcome

- The blueprint now states draft 3: the new interface (G11, G12), rulings G13 to G22, distinct row ids in section 3, and the new requirement Q27.
- All 58 statements are accepted by the compiler and the judge, and both theorems are proved.
- No contradiction between requirements was found.
- One requirement, Q27, cannot be stated as literally worded for a faulty test file (section 5); the reading taken needs the owner's confirmation.
- The reviewer raised five findings. Two led to corrected statements (Q22, Q25), two to added text (Q21, Q22), and one was kept as is (Q11).
- Five questions remain for the owner (section 8).
- The corrections to Q22 and Q25 were made after the review. Nothing in the record shows the independent reviewer re-checked those two corrected statements; they were re-accepted by the Logos judge only.

## 2. get_status counts

Read at report time.

| Field | Value |
|---|---|
| verification_approved | true |
| total_items | 58 |
| statements_formalized | 58 |
| statements_pinned | 0 |
| statements_to_write | none |
| proofs_to_write | none |
| waiting | none |
| trust layer | Judging |

This agrees with the facts handed over from the consistency step. `get_items` shows 56 definitions in state DefinitionFormalized and 2 theorems in state TheoremProved.

Compared with draft 2 (54 items): four were added (`def:TrainOK`, `def:TestOK`, `def:Fitted`, `def:Q27`) and none removed.

## 3. Items

All 56 definitions are in state DefinitionFormalized; both theorems are in state TheoremProved. "Change" is relative to the draft-2 blueprint.

### Interface and input conditions

| Item | Covers | Change |
|---|---|---|
| def:Pipeline | Interface (G11, G12, brief item 1): open type Model; features (raw train, seed), fit (training features), score (model, features), scoreTest (model, raw test, raw train), metrics. Each returns Option; none = error | restated |
| def:MetricsTables | The four metrics tables of section 5 | unchanged |
| def:TrainOK | Section 3 conditions on the raw training file, including at least one known income and distinct VAR1 (G14) | new |
| def:TestOK | Section 3 conditions on the raw test file, including distinct VAR1 (G14) | new |
| def:InputOK | TrainOK train and TestOK test | restated |
| def:Fitted | Model of a run (G12): features(train, seed) = some (F1, F2) and fit F1 = some m | new |

### Auxiliary notions

| Item | Covers | Change |
|---|---|---|
| def:num | Numeric cell reading; absent = missing | unchanged |
| def:str | Text cell reading | unchanged |
| def:ageGroup | Age groups (G5) | unchanged |
| def:median | Standard median | unchanged |
| def:q1Median | Training median of Q1 with the G4 fallback | unchanged |
| def:rowQ1, rowQ2, rowQ3, rowQ5, rowQ7 | Row rules of Q1, Q2, Q3, Q5, Q7 | unchanged |
| def:rowQ4 | Row rule of Q4 (G17): percent = 100 x raw, caps 200 and 500; also credit_utilization = 100u and debt_ratio = 100d | restated |
| def:rowQ6 | Row rule of Q6 (G22, G17, G6): each flag is 1 when its condition holds and 0 when not; thresholds against 100 x raw | restated |
| def:rowQ8 | Row rule of Q8 (G8) | unchanged |
| def:rowQ9 | Row rule of Q9 (G16, G17): natural log only when income > 0; uncapped percent values | text only |
| def:classProbs | Probabilities by class | unchanged |
| def:confCount | Confusion counts | unchanged |
| def:somersD | Standard Somers' D | unchanged |
| def:auc | Standard AUC | unchanged |
| def:ecdf | Empirical cumulative distribution | unchanged |
| def:ksStat | KS statistic | unchanged |
| def:decileCut | Nearest-rank decile cut, no interpolation (G9, G20) | text only |
| def:psiShare | PSI bin shares; a score equal to a cut goes in the lower bin (G20) | text only |
| def:outcomeRecorded | default_flag of a score table is the raw outcome, matched by row id (G14) | text only |

### Requirements

| Item | Covers | Change |
|---|---|---|
| def:Q1, Q2, Q3, Q5, Q7, Q8 | Q1, Q2, Q3, Q5, Q7, Q8 on the feature tables the features step produces | adapted to interface |
| def:Q4 | Q4 (G17) via def:rowQ4 | restated |
| def:Q6 | Q6 (G22, G17) via def:rowQ6 | restated |
| def:Q9 | Q9 (G16, G17) via def:rowQ9 | restated |
| def:Q10 | Q10 (G15): row ids of F1 ++ F2 are a permutation of VAR1; sizes within one applicant (<= 1) of 0.7 n and 0.3 n | restated |
| def:Q11 | Q11: same seed, same outcome of the features step | adapted to interface |
| def:Q12 | Q12 (G13): test predictions equal score(m, Ft) for some Ft obeying the row rules of Q1 to Q9, with the fitted model of the run | restated |
| def:Q13 | Q13 (G10, G13): same existential table, training medians and 0 dependents | restated |
| def:Q14, Q15, Q16 | Q14 (G3), Q15, Q16 on the three score tables of the run | adapted to interface |
| def:Q18 | Q18 (G1, G2) | adapted to interface |
| def:Q19 | Q19 (G18): rates as fractions | text only |
| def:Q20 | Q20 | adapted to interface |
| def:Q21 | Q21: pred_logistic = 1 iff p >= 0.5; text now states that below 0.5 the value is only required not to be 1 | text added after review |
| def:Q22 | Q22 (G19), validation set: outcome recorded; counts sum to the row count at every threshold; threshold table non-empty and each row names its threshold; accuracy, precision, recall, F1 required only when both classes are present and the metric's own denominator is non-zero (F1: tp != 0) | restated, then corrected after review |
| def:Q23 | Q23 (G19): with both classes present AUC = standard AUC and Gini = 2 AUC - 1 = Somers' D; nothing required when a class is empty | restated |
| def:Q24 | Q24 (G19): with both classes present, ks and summary tables non-empty and every KS_Statistic = ksStat; nothing required when a class is empty | restated |
| def:Q25 | Q25 (G9, G20): (1) if both score tables have a score, the summary table is non-empty; (2) PSI present on every summary row, 0 iff equal shares in all ten bins, positive otherwise | restated, then corrected after review |
| def:Q26 | Q26 (G21): decile column a permutation of 1..10; lift and capture_rate present; capture sum = 1 when the validation set has a defaulter | restated |
| def:Q27 | Q27 (G3, G4, G11): (1) InputOK implies every step of the run produces its result; (2) training file not OK implies features = none for every seed; (3) training file OK and test file not OK implies scoreTest with the run's fitted model = none | new |
| def:Spec | Conjunction of Q1 to Q16 and Q18 to Q27 (26 conjuncts; Q17 withdrawn by G1) | restated |

### Theorems

| Item | Statement | State |
|---|---|---|
| thm:consistent | There is a pipeline P with Spec P | TheoremProved |
| thm:inputOK_satisfiable | There are train and test tables with InputOK train test | TheoremProved |

## 4. Readings still taken by the formaliser

These are not settled by a ruling. Each is stated in the text of its item.

1. **Q1 to Q10, Q12 to Q26.** A requirement constrains a step's result when the step produces one (hypothesis "step = some result"). That the result is produced on valid inputs is carried by Q27 alone.
2. **def:Pipeline.** An error is `none` and carries no message or code. The split is represented by the seed. Fitting takes only the training feature table.
3. **Q27, which step must fail.** The step that first reads the faulty raw file.
   - Training file at fault: features(train, seed) = none for every seed, so the run has no result at all.
   - Only the test file at fault: scoreTest = none for the fitted model of the run.
   - Nothing is required of scoreTest when the training file is at fault, nor of steps applied to tables that are not those of a run.
4. **def:TrainOK / def:TestOK.** The outcome is required (0 or 1) in the training file and may be missing only in the test file. "At least one known income" is a condition on the training file.
5. **def:rowQ4 (Q4, G17).** "The feature columns are in percent" is read as also requiring credit_utilization = 100 x raw and debt_ratio = 100 x raw, not only as fixing the unit of the capped columns. This is stronger than the draft-2 Lean.
6. **def:rowQ6.** Income and dependents are read in the feature row after Q1 and Q2 (G6). If such a value is absent, nothing is required of the flag. "Late payments in total" is the sum of the three raw counts.
7. **def:rowQ9.** "Income" is monthly_income of the feature row after Q1; age is the raw age.
8. **Q10 (G15).** "Within one applicant" is inclusive: |size - share| <= 1.
9. **Q12.** "Whose rows obey Q1 to Q9" means: every test applicant has a row in Ft, matched by row id, obeying the rules of Q1 to Q6 and Q9 against its raw test row, and every row of Ft obeys Q7 and Q8. Ft may have other rows. Q13's table is chosen independently of Q12's.
10. **Q21.** "Predicted to default" is pred_logistic = 1. Below 0.5 the value is only required not to be 1.
11. **Q22.**
    - Confusion counts are computed from the validation score table, with default_flag equal to the raw outcome.
    - The count sum holds at every threshold and is not subject to the G19 exemption.
    - The threshold table is non-empty and each row names its threshold; no particular threshold is required.
    - "Or a class is empty" is applied to all four metrics: with an empty class nothing is required of accuracy, precision, recall or F1.
    - F1 is the harmonic mean of precision and recall, required only when tp != 0.
12. **Q23 (G19).** With an empty class nothing is required, including the relation Gini = 2 AUC - 1 between the reported values. Draft 2 required that relation unconditionally.
13. **Q24 (G19).** With an empty class nothing is required, including that a KS value is reported and that the two files agree. Draft 2 required both unconditionally.
14. **Q25.** "Scores" are credit_risk_score. A summary row is required whenever both sets have at least one score, regardless of the classes. The 0/positive rule and the obligation to report apply only when both sets have a score.
15. **Q26.** Lift and capture_rate are present on all ten rows even with no defaulter (G21 makes only the sum conditional). "The validation set has a defaulter" is read on the validation feature table, matched by row id to a raw training row with outcome 1. Deciles are the real numbers 1 to 10 in a numeric cell.
16. **Carried over from draft 2.** Age-group boundaries (30 <= a < 40 and so on); the median convention; the Q3 indicator constrained only to be 1 iff missing; grades and recommendations as the strings A to F and Approve, Review, Decline; KS on pd_logistic.

## 5. What could not be formalised as written, and known weaknesses

1. **Q27, faulty test file.** Feature engineering, fitting, scoring and metrics do not receive the test file. By Q27's first sentence, applied to the same training file with a valid test file, they must produce their results. So "produces no result" can only mean "no test predictions" there; the feature, score and metrics tables are still produced. This is what def:Q27 states.
2. **Q12, Q13 (G13).** The test feature table is not an output. These requirements constrain test feature engineering only as far as the scoring step distinguishes feature tables. The limitation is unchanged from draft 2, now under a ruling.
3. **Q25, Q26 are weak where the documents define nothing.**
   - PSI's value is only 0 versus positive.
   - Lift and individual capture rates are unconstrained.
   - No rule says which applicants fall in which decile.
   - PSI, capture_rate and lift must be present even where they are mathematically undefined (no defaulter).
4. **Q11** holds for every pipeline by construction of the interface (section 6, finding 1).
5. **Not stated by any requirement:** that the feature files' default_flag, age and num_late_* columns carry the raw values.

No hook block occurred. No Lean was saved locally.

## 6. Review findings and answers

An independent reviewer checked the statements against `requirements.md` before the consistency proof was started.

| # | Item | Kind | Finding | Answer |
|---|---|---|---|---|
| 1 | def:Q11 | vacuous | The Lean holds for every Pipeline value, because features is a function of (train, seed). A program whose split depends on the clock breaks Q11 as worded but cannot break def:Q11. | Kept. It cannot be made non-vacuous without changing the interface the brief prescribes. The obligation falls on whoever shows the real program is a function of (train, seed). Open for the owner. |
| 2 | def:Q21 | unstated reading | Below 0.5 the prediction is only required not to be 1; a row with p = 0.2 and pred_logistic = 7 passes. | Text added: the limitation and the reviewer's row are now in the item. Lean unchanged, since no ruling names the value for "not predicted to default". Open for the owner. |
| 3 | def:Q22 | unstated reading | The text had dropped "or a class is empty"; the Lean exempted each metric only through its own denominator. | Corrected. The four value conditions are now required only when both classes are present, in addition to the denominator guards. The count sum, the outcome record and the non-empty threshold table stay unconditional. The alternative, stronger reading is named in the text. Open for the owner. |
| 4 | def:Q22 | unstated reading | F1 is in harmonic-mean form with guard tp != 0; the count form 2tp / (2tp + fp + fn) would require F1 = 0 when tp = 0 and fp + fn > 0. | Text added: the reading and the limitation, with the reviewer's case. Lean unchanged. Open for the owner. |
| 5 | def:Q25 | vacuous | With an empty summary table no PSI was required; only Q24 forced a summary row, and only with both classes present. | Corrected. New first condition: if both score tables have a score, the summary table is non-empty. The reviewer's case now violates Q25. Remaining limitation, stated in the text: when one set has no score, nothing is required. |

**Still open.** The reviewer's list of unanswered findings is empty. Findings 1 to 4 each end in a question only the owner can settle (section 8). The corrected statements of Q22 and Q25 were re-accepted by the judge, along with def:Spec and the statement of thm:consistent; the record shows no second pass by the independent reviewer on them.

## 7. Consistency

Both theorems are proved against the current draft-3 definitions, after the Q22 and Q25 corrections. The proofs use `open Classical` and no axiom, sorry, native_decide or unsafe. No obstacle was met.

### The witness for thm:consistent

An artificial pipeline defined inside the proof, with Model = Unit.

- **features.** If the training table meets TrainOK: one feature row per raw row, split at floor(7n/10) in file order, seed ignored. Otherwise error. Each row has:
  - row_id and default_flag copied;
  - income imputed with the Q1 median (age group, falling back to all known incomes) and dependents imputed with 0;
  - the two missing indicators;
  - credit_utilization and debt_ratio as raw x 100, with their caps at 200 and 500;
  - the late-payment sum, the eight flags as 1/0 and their count;
  - financial_health = 50 (constant) and the two interactions.
- **fit.** Always succeeds and returns the trivial model.
- **score.** Always succeeds.
  - Probability = total_risk_flags / 8, clamped to [0, 1].
  - Score = 600 + 250 x (1 - p).
  - Grade by the Q18 bands; recommendation and interest rate by grade.
  - Prediction = 1 exactly when p >= 0.5.
- **scoreTest.** If the test table meets TestOK: the same feature map (with training medians) followed by the same scoring. Otherwise error.
- **metrics.** Always succeeds.
  - One summary row: AUC = auc, Gini = 2 AUC - 1, KS = ksStat, PSI = 0 if the ten bin shares agree and 1 otherwise.
  - One ks row.
  - Ten decile rows: deciles 1 to 10, each with capture_rate 1/10 and lift 1.
  - One threshold row at 1/2 with the standard formulas.

Proved on the way, for any score table: Somers' D = 2 AUC - 1 when both classes are present; the four confusion counts sum to the row count when every row has an outcome in {0, 1} and a probability.

### The witness for thm:inputOK_satisfiable

One training row (all fields present, outcome 0, income known) and one test row (outcome, income and dependents missing, everything else present).

### What the witness does not show

- Nothing about the SAS program or a realistic fitted model: the model is trivial and fitting ignores its input.
- Q11 holds only because the seed is ignored.
- Q8 holds by a constant (50).
- Grade C, Review and rate 0.09 are never produced by this pipeline (p takes values k/8, none in [0.15, 0.25)). Those clauses are proved for arbitrary p but not exercised.
- PSI = 1 when shares differ, capture_rate 1/10 and lift 1 are arbitrary permitted choices. They show how little Q25 and Q26 fix.
- The feature rows carry only the columns the requirements mention formally. Age, age_group, the raw late counts, num_credit_lines and log_monthly_income are not written.
- Q27's error clauses are met by testing TrainOK and TestOK classically (non-computably); fit, score and metrics never fail. Nothing is shown about how a real program would detect bad input.
- The InputOK witness is two single-row tables and says nothing about realistic data.

## 8. Open points for the owner

1. **Q27, faulty test file.** Confirm that "produces no result" means only that no test predictions are produced, while the feature, score and metrics tables still are.
2. **Q11.** Confirm that the obligation is handed to whoever shows the real program is a function of the raw training table and the seed. The alternative is a ruling that changes the interface, for example making the features step a relation.
3. **Q21.** Rule whether pred_logistic must be 0 when p < 0.5. As stated, it must only differ from 1.
4. **Q22, "or a class is empty".** Rule whether the clause exempts accuracy, precision, recall and F1 (the reading taken, which follows the sentence literally) or concerns AUC, Gini and KS only (stronger).
5. **Q22, F1.** Rule whether F1 = 0 is required when tp = 0 and fp + fn > 0 (count form) or nothing is required there (harmonic-mean form, the reading taken).

Also for the owner's attention, without a specific question: the Q4 reading in section 4 item 5 is stronger than draft 2, and Q25 and Q26 remain weak (section 5 item 3).

For the orchestrator: `/Users/cristophersalvi/GitHub/credit-risk-migration/migration/requirements/report.md` still holds the draft-2 report until this text is saved over it.

## Orchestrator's note (2026-11-14)

The report above was returned by the reporting agent and saved by the orchestrator. One correction
to its section 6: the corrected statements of Q22 and Q25 were re-checked by a second independent
reviewer (the workflow's re-check step), who found both resolved and no new defect. The reporting
agent was not given that step's detail.
