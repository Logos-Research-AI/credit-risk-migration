# Requirements formalisation report: draft 5

Blueprint `credit-risk-requirements`, id `006ff04c-d34c-4a9c-b230-ccd725b1be6f`.
Shared types from `credit-risk-foundation`, id `02011d57-8b15-43bb-8744-c6646fdfe9ae`.
Graph: https://platform-staging.logosresearch.ai/view/waad_AzureAd_b85254ea-5bb2-40b8-b836-c90bdf235fc9/006ff04c-d34c-4a9c-b230-ccd725b1be6f

Sources: `/Users/cristophersalvi/GitHub/credit-risk-migration/migration/requirements/requirements.md` (draft 5, rulings G1 to G38) and `/Users/cristophersalvi/GitHub/credit-risk-migration/migration/requirements/brief.md`.

## 1. Outcome

- The blueprint states draft 5. G34 is in the input conditions: `def:TrainOK` and `def:TestOK` gain clause (1g), a present MonthlyIncome is zero or more, in both raw files.
- G35 to G38 change no statement. G35 leaves Q25 as it is; G36, G37 and G38 are about the SAS program and the printed files.
- All 59 statements are accepted by the compiler and the judge, and both theorems are proved against the current definitions. No item was added or removed.
- No contradiction was found, and nothing in draft 5 failed to be stated.
- The reviewer raised one finding, on the input conditions. It was accepted and corrected with a second new clause, (1h): no cell of a raw file is a text cell holding a string.
- **Clause (1h) is not a ruling and needs the owner's confirmation.** It reverses a reading of the draft-4 report, under which a text cell in MonthlyIncome or NumberOfDependents counted as missing. A raw file with any text value must now be refused under Q27.
- I was not given a second pass by the independent reviewer on the corrected `def:TrainOK` and `def:TestOK`. The judge re-accepted them and the list of open findings handed to me is empty.

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

This agrees with the facts handed over from the consistency step. Three points in the handed-over facts differ from the blueprint or from each other:

- **Update step's status.** It reported both proofs to write and verification_approved false. That was true at the time and has been superseded.
- **Update step's account of the input conditions.** It lists (1g) as the only new clause and says a text cell in MonthlyIncome is not constrained. The accepted statements also carry (1h), added after the review, and refuse such a cell.
- **Proof of `thm:inputOK_satisfiable`.** The answers record says it was rewritten for (1g) and (1h); the consistency step says it found the theorem already proved and did not resubmit it. The two are compatible if the rewrite happened in the review-answer step. The theorem is TheoremProved now.

## 3. Items

All 57 definitions are DefinitionFormalized; both theorems are TheoremProved. "Change" is relative to the draft-4 blueprint.

### Interface and input conditions

| Item | Covers | Change |
|---|---|---|
| def:Pipeline | Interface (G11, G12): open type Model; features, fit, score, scoreTest, metrics; each returns Option, none = error | unchanged |
| def:MetricsTables | The four metrics tables of section 5 | unchanged |
| def:TrainOK | Section 3 on the training file. Conditions of G14, G28 and G29 kept. New (1g), G34: if MonthlyIncome is present with value x then 0 <= x. New (1h), after review: no cell of a row is a text cell holding a string | restated, then corrected after review |
| def:TestOK | Section 3 on the test file, with the same (1g) and (1h). The outcome may be missing but its column must exist | restated, then corrected after review |
| def:InputOK | TrainOK train and TestOK test | text only (cites G34, both raw files) |
| def:Fitted | Model of a run (G12) | unchanged |

### Auxiliary notions

| Item | Covers | Change |
|---|---|---|
| def:decimal32 | G28: a plain decimal numeral of at most 32 characters | unchanged |
| def:num, def:str | Numeric and text cell reading. The text of def:num still calls a text cell "missing"; under (1h) no admissible raw file has one | unchanged |
| def:ageGroup, def:median, def:q1Median | Age groups, median, Q1 training median | unchanged |
| def:rowQ1 to def:rowQ9 | Row rules of Q1 to Q9. rowQ9: the first interaction is required only when income is above 0 (G16); income 0 stays admissible under G34 | unchanged |
| def:classProbs, def:confCount, def:somersD, def:auc, def:ecdf, def:ksStat | Standard notions behind Q22 to Q24 | unchanged |
| def:decileCut, def:psiShare | Nearest-rank decile cut (G20) and PSI bin shares | unchanged |
| def:outcomeRecorded | default_flag is the raw outcome, matched by row id | unchanged |

### Requirements

| Item | Covers | Change |
|---|---|---|
| def:Q1 to Q16, Q18 to Q24, Q26 | As in draft 4. Resubmitted with the same Lean (a blank line added) and re-accepted, because they depend on the input conditions. G38 changes nothing in Q15 and Q18: they are about the values computed | unchanged |
| def:Q25 | Q25 (G9, G20). G35 leaves it as it is: only 0 versus positive is fixed. The SAS program's empty-bin share rule is not stated | unchanged |
| def:Q27 | Q27. Same Lean. Its meaning follows the new input conditions: a training file with a known income below 0 or a text value must make feature engineering fail; such a test file must make test scoring fail (G23). G36 is not stated | unchanged |
| def:Spec | Conjunction of Q1 to Q16 and Q18 to Q27 (26 conjuncts) | unchanged |

### Theorems

| Item | Statement | State |
|---|---|---|
| thm:consistent | There is a pipeline P with Spec P | TheoremProved |
| thm:inputOK_satisfiable | There are train and test tables with InputOK train test | TheoremProved |

Both statements are unchanged from draft 4.

## 4. Readings still taken by the formaliser

These are not settled by a ruling. Each is stated in the text of its item unless noted.

New in draft 5:

1. **def:TrainOK / def:TestOK (G34), "a known MonthlyIncome".** It is one that def:num reads as a number. An income of exactly 0 is allowed. A missing income is not constrained.
2. **def:TestOK (G34), both files.** The condition is applied to the test file as well as the training file. Section 3 states it for the raw inputs without naming a file.
3. **def:TrainOK / def:TestOK, text cells (1h).** Section 1 says "missing" means absent from the data, and the foundation uses only the absent option of a cell for that. So a text cell holding a string is a present value that is not a decimal number, and the file is refused.
   - Every string is refused, including one that spells a number ("5", "-5") and the empty string. The requirements give no rule for reading a string as a number.
   - A cell holding the absent option, numeric or text, is still a missing value.
   - This replaces draft-4 reading 3.
4. **G35 to G38 are not stated in the blueprint.** G35's empty-bin share is a rule of the SAS program. G36 (scripts remove earlier output files) and G37 (import reads every row) are outside the interface. G38 (12 printed characters) is about printed files. This reading is in this report only, not in an item text.

Carried over from draft 4 and still not ruled (G34 to G38 touch none of them):

- def:decimal32 excludes exponent notation and a "+" sign;
- the columns are read row by row, as a permutation of the twelve raw names;
- "every numeric value" is every value def:num reads;
- the test file must have the SeriousDlqin2yrs column; its value may be missing;
- "the number of credit lines" is NumberOfOpenCreditLinesAndLoans; NumberOfDependents must be whole only where present;
- Q12, Q13: the published columns are the score columns without default_flag; agreement is equality of the values read by def:num or def:str; every row of Ft is a test applicant's and obeys the rules; every score row with the applicant's id agrees with the prediction;
- Q13's table is chosen by its own existential;
- Q22: "the validation set is empty" is read on F2;
- Q25 requires nothing when a set has no score;
- the draft-3 readings: a requirement binds a step only when it produces a result; an error is `none`; the outcome is required in training only; Q4 percent scaling; Q6 after imputation; Q10 inclusive; Q23 and Q24 require nothing with an empty class; Q26 lift and capture present on all ten rows; age-group boundaries; the median convention; grade and recommendation strings; KS on pd_logistic.

## 5. What could not be formalised as written, and known weaknesses

Nothing in draft 5 failed to be stated, and no two requirements contradict each other.

Known weaknesses:

1. **Q12, Q13 (G13, G30).** The test feature table is not an output. These requirements constrain test feature engineering only through the seven published columns.
2. **Q25, Q26 are weak where the documents define nothing.** PSI's value is only 0 versus positive, which G35 confirms. Lift and individual capture rates are unconstrained.
3. **Q25 with a set that has no score** requires nothing. G35 does not rule on this case.
4. **Q11** holds for every pipeline by the form of the interface (G24).
5. **Not stated by any requirement:** that the feature files' default_flag, age and num_late_* columns carry the raw values.
6. **Item texts not refreshed.** Items whose texts predate G23 to G27 (for example Q21, Q27, Q11) still describe as formaliser readings what those rulings confirmed. Q27's text names neither G34 nor G36. def:num's text still calls a text cell "missing". The Lean is unaffected.
7. **G36 against Q27.** "Produces no result" is stated as the step returning `none`. Whether earlier output files are removed cannot be said over this interface.

No hook block occurred. No Lean was saved locally. Only the Logos MCP Staging connector was used; a separate server named logos-mcp failed to connect and was not needed.

## 6. Review findings and answers

An independent reviewer checked the restated statements against `requirements.md`.

| # | Item | Kind | Finding | Answer |
|---|---|---|---|---|
| 1 | def:TrainOK, def:TestOK (cause in def:num) | weaker than text | def:num reads a text cell as absent, and the conditions reached MonthlyIncome, NumberOfDependents and the test outcome only through def:num. A row with MonthlyIncome held as the text "-5" or "abc" met TrainOK. The text makes that value present, so a negative income (G34) or a non-decimal (G28), and the file should be refused. In Lean, Q27 instead required a result, Q1 an imputed income and Q3 a missing flag of 1. The reading was declared in the item texts and predates draft 5. | Corrected, text and Lean, in both items: clause (1h), `∀ p ∈ r, ∀ s : String, p.2 ≠ Tabular.Cell.str (some s)`. The reviewer's case now fails TrainOK, so Q27 requires an error. The old reading is removed from the texts and reading 3 of section 4 written in its place. def:num is unchanged. |

Dependants of the correction:

- **def:InputOK, def:Q1 to def:Q27, def:Spec** were resubmitted with the same Lean and re-accepted.
- **thm:inputOK_satisfiable**: statement unchanged. The proof was rewritten for (1g) and (1h) with the same witness tables.
- **thm:consistent**: statement unchanged. The stored proof was accepted again without change.

**Still open.** The reviewer's list of unanswered findings is empty. I was not given a second pass by the independent reviewer on the corrected statements, so (1h) has been checked by the judge only.

## 7. Consistency

Both theorems are proved against the current draft-5 definitions, including (1g) and (1h). The proofs contain no axiom, sorry, native_decide or unsafe; the consistency proof opens Classical. No separate axiom audit was run beyond the server's acceptance. No obstacle was met.

### The witness for thm:consistent

The same artificial pipeline as in draft 4, with Model = Unit.

- **features.** Error unless TrainOK holds. Otherwise one feature row per raw row as the documents prescribe: imputed income and dependents, missing flags, percent scaling and caps, late-payment total, eight flags and their sum, interactions, financial_health fixed at 50. The split is by position, the first floor(7n/10) rows to training; the seed is ignored.
- **fit.** Always succeeds.
- **score.** Probability = total_risk_flags / 8 clamped to [0, 1]; prediction = 1 exactly when p >= 0.5; score = 600 + 250 x (1 - p); grade, rate and recommendation by the documented bands.
- **scoreTest.** Error unless TestOK holds. Otherwise the same feature engineering with training medians, then the same scoring.
- **metrics.** Never fails. One summary row with AUC, Gini = 2 AUC - 1, KS, and a PSI that is 0 when the ten bin shares agree and 1 otherwise. One KS row, one threshold row at 0.5, ten decile rows with capture rate 1/10 and lift 1.

The witness tests TrainOK and TestOK themselves, so it refuses a known income below 0 and a text cell without any change to the proof.

### The witness for thm:inputOK_satisfiable

- Training table: three applicants, ids 1 to 3, outcomes 0, 1, 0; incomes 5000, missing, 0.235; dependents 2, missing, 0; fractional utilisation and debt ratio.
- Test table: two applicants, ids 1 and 2, outcome not recorded; incomes 4200 and missing.
- Every cell is numeric. Every known income is shown to be zero or more, every value a decimal within 32 characters and every count a natural number.

### What the witnesses do not show

- Nothing about the SAS program or a realistic model: nothing is fitted and the model carries no information.
- The split is positional and ignores the seed.
- financial_health, the decile rows and PSI are constants or a 0/1 indicator. The proof shows that those requirements can be met together, not that a realistic model meets them.
- The pipeline always emits a threshold row, so the G31 excuse for an empty validation set is not exercised.
- Q27's error clauses are met by testing TrainOK and TestOK classically. Nothing is shown about how a real program detects a negative income, a text cell, a non-CSV table or a non-whole count.
- The input witness is a small hand-made table, not real data. It has no income of exactly 0, so the boundary case of G34 is not exhibited there.
- The witness's first interaction is age x log(income), which matches Q9 as worded in draft 5. I did not re-read the Lean of def:rowQ9 for this report.

## 8. Open points for the owner

New in draft 5:

1. **Text values in a raw file, clause (1h).** Confirm that a raw file holding any text value must be refused, including a string that spells a number and the empty string. The alternative, in force up to draft 4, treats a text cell in MonthlyIncome or NumberOfDependents as missing. This also decides whether a negative income held as text is caught by G34.
2. **G34 on the test file.** Confirm that a known income below 0 in cs-test.csv makes the test file faulty, so that the test predictions are withheld (G23).

Standing from draft 4; I read G34 to G38 and none of them rules on these:

3. **G28, "decimal number".** Confirm that a plain positional numeral is meant. As stated, a file holding a value written only with an exponent, such as 1e-40, must be refused.
4. **Q25, a set with no score.** Nothing is required when the training or validation set has no score (training files of at most three applicants). G35 confirms the 0-versus-positive form but not this case. Rule whether a PSI must be reported there.
5. **Q12, Q13, reading of G30.** Confirm that every row of the test feature table must be a test applicant's and obey the rules, and that every score row with an applicant's id must agree with the prediction.
6. **G28, columns of the test file.** Confirm that cs-test.csv must contain the SeriousDlqin2yrs column, even if empty.
7. **G29, "the number of credit lines".** Confirm that NumberOfOpenCreditLinesAndLoans is meant and that NumberRealEstateLoansOrLines need not be a whole number.

One remark on the source: the sign-off line of `requirements.md` still refers to the draft-3 blueprint (58 items, signed 2026-11-14). The blueprint now has 59 items and states draft 5.

For the orchestrator: `/Users/cristophersalvi/GitHub/credit-risk-migration/migration/requirements/report.md` still holds the draft-4 report until this text is saved over it.
