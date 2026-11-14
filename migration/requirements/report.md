# Requirements formalisation report: draft 4

Blueprint `credit-risk-requirements`, id `006ff04c-d34c-4a9c-b230-ccd725b1be6f`.
Shared types from `credit-risk-foundation`, id `02011d57-8b15-43bb-8744-c6646fdfe9ae`.
Graph: https://platform-staging.logosresearch.ai/view/waad_AzureAd_b85254ea-5bb2-40b8-b836-c90bdf235fc9/006ff04c-d34c-4a9c-b230-ccd725b1be6f

Sources: `/Users/cristophersalvi/GitHub/credit-risk-migration/migration/requirements/requirements.md` (draft 4, rulings G1 to G33) and `/Users/cristophersalvi/GitHub/credit-risk-migration/migration/requirements/brief.md`.

## 1. Outcome

- The blueprint now states draft 4: G28 and G29 in the input conditions, G30 in Q12 and Q13, G31 in Q22. G32 leaves Q26 as it was, and G33 changes no requirement.
- All 59 statements are accepted by the compiler and the judge, and both theorems are proved against the current definitions.
- No contradiction was found, and nothing in draft 4 failed to be stated.
- The reviewer raised three findings (Q12, Q13, Q25). All three were accepted and the statements corrected. The reviewer's list of unanswered findings is empty.
- Two of those corrections go beyond the rulings and need the owner's attention:
  - Q25 now requires nothing when a set has no score, which is weaker than the accepted draft-3 statement.
  - Q12 and Q13 now bind every row of the test feature table and every score row with the applicant's id.
- One new reading may not be what the owner means: "decimal number" in G28 excludes exponent notation.
- I was not given the detail of any re-check of the three corrected statements by the independent reviewer. I only know that the judge re-accepted them and that the list of open findings handed to me is empty.

## 2. get_status counts

Read at report time.

| Field | Value |
|---|---|
| verification_approved | true |
| total_items | 59 |
| statements_formalized | 59 |
| statements_pinned | 0 |
| statements_to_write | none |
| proofs_to_write | none |
| waiting | none |
| trust layer | Judging |

`get_items` shows 57 definitions in state DefinitionFormalized and 2 theorems in state TheoremProved.

This agrees with the facts handed over from the consistency step. The update step's status (both proofs to write, verification_approved false) was true at that time and has since been superseded.

Compared with draft 3 (58 items): one item was added (`def:decimal32`) and none removed.

## 3. Items

All 57 definitions are DefinitionFormalized; both theorems are TheoremProved. "Change" is relative to the draft-3 blueprint.

### Interface and input conditions

| Item | Covers | Change |
|---|---|---|
| def:Pipeline | Interface (G11, G12): open type Model; features, fit, score, scoreTest, metrics; each returns Option, none = error | unchanged |
| def:MetricsTables | The four metrics tables of section 5 | unchanged |
| def:TrainOK | Section 3 on the training file. Earlier conditions kept. G28: each row's column names are a permutation of the twelve raw columns; every value def:num reads satisfies def:decimal32. G29: the three late-payment counts and NumberOfOpenCreditLinesAndLoans are natural numbers; NumberOfDependents is one where present | restated |
| def:TestOK | Section 3 on the test file, with the same G28 and G29 additions. The outcome may be missing but its column must exist | restated |
| def:InputOK | TrainOK train and TestOK test | text only (cites G28, G29) |
| def:Fitted | Model of a run (G12) | unchanged |

### Auxiliary notions

| Item | Covers | Change |
|---|---|---|
| def:decimal32 | G28: a real that is a plain decimal numeral (optional minus, at least one integer digit, optional point and k fractional digits) of at most 32 characters | new |
| def:num, def:str | Numeric and text cell reading | unchanged |
| def:ageGroup, def:median, def:q1Median | Age groups, median, Q1 training median | unchanged |
| def:rowQ1 to def:rowQ9 | Row rules of Q1 to Q9. G29 changes nothing in rowQ6: `1 <= n` already states "at least one" | unchanged |
| def:classProbs, def:confCount, def:somersD, def:auc, def:ecdf, def:ksStat | Standard notions behind Q22 to Q24 | unchanged |
| def:decileCut, def:psiShare | Nearest-rank decile cut and PSI bin shares | unchanged |
| def:outcomeRecorded | default_flag is the raw outcome, matched by row id | unchanged |

### Requirements

| Item | Covers | Change |
|---|---|---|
| def:Q1 to Q11, Q14 to Q16, Q18 to Q21, Q23, Q24 | As in draft 3. Lean identical, re-accepted after the input conditions changed | unchanged |
| def:Q12 | Q12 (G13, G30). There are Ft and S with score(m, Ft) = some S, and: (2a) every prediction row has a row of S with its row_id; (2b) every row of S with that row_id agrees with it on pd_logistic, pred_logistic, credit_risk_score, interest_rate (def:num) and risk_grade, recommendation (def:str); (3) every test row has a row in Ft with its id; (4) every row of Ft has a raw test row with its id for which the rules of Q1 to Q6 and Q9 hold, and obeys Q7 and Q8 | restated for G30, then corrected after review |
| def:Q13 | Q13 (G10, G13, G30). Same shape as Q12; (4) every row of Ft has a raw test row with its id for which a missing income gives the Q1 training median and missing dependents give 0 | restated for G30, then corrected after review |
| def:Q22 | Q22 (G19, G31). The threshold table must be non-empty only when the validation feature table F2 is non-empty. Everything else as before. The text now cites G26 and G27 for the two readings they confirmed | restated |
| def:Q25 | Q25 (G9, G20). If both score tables have a present credit_risk_score: the summary table is non-empty, and every summary row has a PSI value that is 0 on equal shares in all ten bins and positive otherwise. If either has none, nothing is required | corrected after review (no ruling) |
| def:Q26 | Q26 (G21; G32 leaves it unchanged) | unchanged |
| def:Q27 | Q27. Lean identical. Its meaning follows the new TrainOK and TestOK: a table that is not CSV-shaped (G28) or has non-whole counts (G29) must now be refused | unchanged |
| def:Spec | Conjunction of Q1 to Q16 and Q18 to Q27 (26 conjuncts) | unchanged |

### Theorems

| Item | Statement | State |
|---|---|---|
| thm:consistent | There is a pipeline P with Spec P | TheoremProved |
| thm:inputOK_satisfiable | There are train and test tables with InputOK train test | TheoremProved |

Both statements are unchanged from draft 3.

## 4. Readings still taken by the formaliser

These are not settled by a ruling. Each is stated in the text of its item.

New in draft 4:

1. **def:decimal32 (G28).** "A decimal number that can be written in at most 32 characters" is a plain positional numeral.
   - Characters counted: one for a minus sign, the integer digits (at least one), and, if there are k > 0 fractional digits, the point plus k.
   - No exponent notation: 1e-40 does not qualify. No "+" sign.
2. **def:TrainOK / def:TestOK (G28), columns.** "The columns of section 5 and no others" is read row by row: the row's column names are a permutation of the twelve raw names. Each appears exactly once; the order is free.
3. **def:TrainOK / def:TestOK (G28), values.** "Every numeric value" is every value def:num reads in the row. Nothing is required of a cell holding no number. A text cell in MonthlyIncome or NumberOfDependents is still allowed and counts as missing.
4. **def:TestOK (G28).** The test file must have the SeriousDlqin2yrs column, since section 5 lists it for both raw files. Its value may be missing.
5. **def:TrainOK / def:TestOK (G29).** "The number of credit lines" is NumberOfOpenCreditLinesAndLoans, not NumberRealEstateLoansOrLines. NumberOfDependents must be a whole number only where present.
6. **Q12, Q13 (G30), published columns.** They are row_id, pd_logistic, pred_logistic, credit_risk_score, risk_grade, recommendation, interest_rate: the score columns of section 5 without default_flag.
7. **Q12, Q13 (G30), agreement.** "Agrees on a column" is equality of the value read by def:num or def:str, not equality of the cells.
8. **Q12, Q13 (G30), "the score of that table's row for the same applicant".** The interface scores whole tables and does not pair rows of S with rows of Ft. So the applicant's score is any row of S with the applicant's row_id: at least one must exist, and all of them must agree with the prediction. Rows of S whose id is no prediction's are unconstrained.
9. **Q12, Q13, "whose rows obey Q1 to Q9".** Every row of Ft, without exception, is the feature row of some test applicant and obeys the rules against that raw row. Every test applicant has a row in Ft. Ft may hold two rows with one id if both obey the rules. This replaces draft-3 reading 9, under which Ft could have other rows.
10. **Q13, "the same test feature table as Q12".** Q13's table is still chosen by its own existential. Every witness of Q12 is a witness of Q13.
11. **Q22 (G31).** "The validation set is empty" is read on the validation feature table F2, as in Q26. Under Q14 this is equivalent to an empty validation score table. G31 removes only the obligation that a threshold row exists: a row reported anyway must still name its threshold. The outcome-record and count-sum conditions are kept.
12. **Q25, no score in a set.** When the training or the validation score table has no present credit_risk_score, nothing is required: no summary row, no PSI value, no rule on the value. This can only happen for training files of at most three applicants.

Carried over from draft 3 and still not ruled: readings 1, 2, 3 (as far as G23 does not cover it), 4, 5, 6, 7, 8, 12, 13, 15 and 16 of the draft-3 report. In short:

- a requirement constrains a step's result only when the step produces one; Q27 carries the obligation to produce it;
- an error is `none`, with no message;
- the outcome is required in the training file and optional in the test file;
- Q4 also requires credit_utilization = 100 x raw and debt_ratio = 100 x raw;
- Q6 reads income and dependents after Q1 and Q2; "late payments in total" is the sum of the three raw counts;
- Q10 "within one applicant" is inclusive;
- with an empty class, Q23 and Q24 require nothing at all, not even Gini = 2 AUC - 1 or a reported KS;
- Q26: lift and capture_rate are present on all ten rows even with no defaulter;
- age-group boundaries, the median convention, grade and recommendation strings, KS on pd_logistic.

Settled since draft 3 and no longer formaliser readings: Q27 with a faulty test file (G23), Q11 (G24), Q3 and Q21 below their case (G25), Q22 "or a class is empty" (G26), Q22 F1 (G27).

## 5. What could not be formalised as written, and known weaknesses

Nothing in draft 4 failed to be stated, and no two requirements contradict each other.

Known weaknesses:

1. **Q12, Q13 (G13).** The test feature table is not an output. These requirements constrain test feature engineering only as far as the scoring step distinguishes feature tables on the published columns. G30 narrows the comparison further, to seven columns.
2. **Q25, Q26 are weak where the documents define nothing.** PSI's value is only 0 versus positive. Lift and individual capture rates are unconstrained. No rule says which applicants fall in which decile. G32 confirms Q26 as written.
3. **Q25 with an empty set** now requires nothing (section 4, reading 12).
4. **Q11** holds for every pipeline by the form of the interface (ruled by G24).
5. **Not stated by any requirement:** that the feature files' default_flag, age and num_late_* columns carry the raw values.
6. **Item texts not refreshed.** Apart from def:Q22, items whose texts predate G23 to G27 (for example Q21, Q27, Q11) still describe as formaliser readings what those rulings have since confirmed. The Lean is unaffected.

No hook block occurred. No Lean was saved locally. Only the Logos MCP Staging connector was used; a separate server named logos-mcp failed to connect and was not needed.

## 6. Review findings and answers

An independent reviewer checked the changed statements against `requirements.md`.

| # | Item | Kind | Finding | Answer |
|---|---|---|---|---|
| 1 | def:Q12 | weaker than text | The G30 restatement asked only that some row of Ft per test applicant obey Q1 to Q6 and Q9, and that some row of S agree with each prediction. Ft could hold a second row with the same row_id that breaks the rules, and the prediction could be the score of that row. | Corrected, text and Lean. Every row of Ft must now obey the rules against a raw test row with its id; every row of S with the prediction's row_id must agree with it. The reviewer's case no longer satisfies Q12. The reviewer's permutation repair was not taken: it would forbid two rule-abiding rows with one id and impose a shape on S that the text does not state. |
| 2 | def:Q13 | weaker than text | Same gap as Q12, and no condition at all on the other rows of Ft. | Corrected in the same shape. Every row of Ft must have a raw test row with its id for which the median and 0 rules hold. The reviewer's case no longer satisfies Q13. |
| 3 | def:Q25 | stronger than text | A PSI number was required on every summary row even when a set has no score. A training file of 2 applicants split 2 and 0, with PSI missing, violated the Lean but not the text. | Corrected, text and Lean. The guard "both sets have a score" now stands in front of the whole conclusion. No reading was taken on whether a PSI should be reported in that case: the text is silent, so the statement is too. |

Dependants of the three corrections:

- **def:Spec** and the statement of **thm:consistent** were resubmitted unchanged and re-accepted.
- **thm:consistent**: the proof was accepted again with the same witness pipeline. Its Q12 and Q13 parts now use the distinctness of the test row ids; its Q25 part follows the moved guard.
- **thm:inputOK_satisfiable** was not affected by the findings. Its proof was missing at that point because of G28 and G29, and was written in the consistency step. The answers record labels it "cannot-state"; that label is wrong, the statement was accepted throughout.

**Still open.** The reviewer's list of unanswered findings is empty. I was not given the detail of a second pass by the independent reviewer on the corrected Q12, Q13 and Q25.

## 7. Consistency

Both theorems are proved against the current draft-4 definitions, after the three corrections. The proofs contain no axiom, sorry, native_decide or unsafe; the consistency proof opens Classical. No separate axiom audit was run beyond the server's acceptance. No obstacle was met.

### The witness for thm:consistent

The same artificial pipeline as in draft 3, with Model = Unit.

- **features.** Error unless TrainOK holds. Otherwise one feature row per raw row as the documents prescribe: imputed income and dependents, missing flags, percent scaling and caps, late-payment total, eight flags and their sum, interactions, financial_health fixed at 50. The split is by position, the first floor(7n/10) rows to training; the seed is ignored.
- **fit.** Always succeeds.
- **score.** Probability = total_risk_flags / 8 clamped to [0, 1]; prediction = 1 exactly when p >= 0.5; score = 600 + 250 x (1 - p); grade, rate and recommendation by the documented bands.
- **scoreTest.** Error unless TestOK holds. Otherwise the same feature engineering with training medians, then the same scoring.
- **metrics.** Never fails. One summary row with AUC, Gini = 2 AUC - 1, KS, and a PSI that is 0 when the ten bin shares agree and 1 otherwise. One threshold row at 0.5. Ten decile rows with capture rate 1/10 and lift 1.

### The witness for thm:inputOK_satisfiable

Proved anew for G28 and G29.

- Training table: three applicants, ids 1 to 3, outcomes 0, 1, 0. One has income and dependents missing. Utilisation and debt ratio are fractional (such as 0.35 and 0.125); one income is 0.235.
- Test table: two applicants, outcome not recorded, one with income missing, one with utilisation 0.12.
- Every value is shown to be a decimal within 32 characters and every count a natural number.

### What the witnesses do not show

- Nothing about the SAS program or a realistic model: nothing is fitted and the model carries no information.
- The split is positional and ignores the seed.
- financial_health, the decile rows and PSI are constants or a 0/1 indicator. The proof shows that those requirements can be met together, not that a realistic model meets them.
- The pipeline always emits a threshold row, so the G31 excuse for an empty validation set is not exercised.
- Q27's error clauses are met by testing TrainOK and TestOK classically. Nothing is shown about how a real program would detect a non-CSV table or a non-whole count.
- The input witness is a small hand-made table, not real data.

## 8. Open points for the owner

1. **G28, "decimal number".** Confirm that a plain positional numeral is meant. If a value such as 1e-40, written with an exponent, should count as an admissible input, def:decimal32 must be widened; as stated, a file holding it must be refused under Q27.
2. **Q25, a set with no score.** The accepted draft-3 statement required a PSI value on every summary row regardless. After the review it requires nothing when the training or validation set has no score (training files of at most three applicants). Rule whether a PSI must be reported there, or confirm that nothing is required, as G31 does for the threshold rows.
3. **Q12, Q13, reading of G30.** Confirm that every row of the test feature table must be a test applicant's and obey the rules, and that every score row with an applicant's id must agree with the prediction. The alternative the reviewer proposed is stricter: the row ids of the test feature table are exactly the test ids, each once.
4. **G28, columns of the test file.** Confirm that cs-test.csv must contain the SeriousDlqin2yrs column, even if empty. As stated, a test file without that column must be refused.
5. **G29, "the number of credit lines".** Confirm that NumberOfOpenCreditLinesAndLoans is meant and that NumberRealEstateLoansOrLines is not required to be a whole number.

For the orchestrator: `/Users/cristophersalvi/GitHub/credit-risk-migration/migration/requirements/report.md` still holds the draft-3 report until this text is saved over it.
