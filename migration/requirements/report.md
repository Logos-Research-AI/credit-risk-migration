# Report: formalisation of requirements.md into credit-risk-requirements

Date: 2026-11-14. Blueprint credit-risk-requirements, id 006ff04c-d34c-4a9c-b230-ccd725b1be6f (Logos MCP Staging, trust layer Judging). Shared types from credit-risk-foundation, id 02011d57-8b15-43bb-8744-c6646fdfe9ae.

## 1. Outcome
- All 25 live requirements (Q1 to Q16, Q18 to Q26; Q17 is withdrawn) have an accepted Lean statement.
- Consistency is proved: thm:consistent (∃ P : Pipeline, Spec P) and thm:inputOK_satisfiable (∃ train test, InputOK train test) are both TheoremProved.
- No contradiction between requirements was found.
- One sentence of the documentation is not formalised (section 3, 'must stop with an error').
- One review finding is still open (the text of def:Pipeline), and several readings need an owner ruling before the SAS program is judged against the specification (section 9).

## 2. get_status counts
total_items 54; statements_formalized 54; statements_pinned 0; statements_to_write none; proofs_to_write none; waiting none; verification_approved true. get_items: 52 definitions DefinitionFormalized, 2 theorems TheoremProved. get_status agrees with the earlier steps (50 items after formalisation, + def:outcomeRecorded and def:auc from the review answers, + 2 theorems).

## 3. Visibility check
Tabular.RealLike, Tabular.Row, Tabular.Table and Tabular.Row.get resolve from the blueprint, and a statement using Tabular.Table ℝ compiled with no explicit wiring to the foundation. The run-1 blocker is gone. Not tested: whether an instance Tabular.RealLike ℝ exists.

## 4. Items (all definitions DefinitionFormalized; both theorems TheoremProved)
Interface and inputs: def:Pipeline (features, score, scoreTest, metrics); def:MetricsTables (summary, ks, decile, threshold); def:InputOK (section 3).
Requirements: def:Q1 (Q1; clause added after review: every feature row has an income); def:Q2; def:Q3; def:Q4, def:Q5, def:Q6 (restated per applicant on the raw row after review); def:Q7; def:Q8; def:Q9 (restated on the raw row; nothing required when income <= 0); def:Q10 (tolerance is an unruled reading); def:Q11 (true of every pipeline); def:Q12, def:Q13 (existential reading: hidden test feature table); def:Q14 (permutation of row ids after review); def:Q15; def:Q16; def:Q18; def:Q19 (unit is a reading); def:Q20; def:Q21; def:Q22 (restructured after review); def:Q23 (AUC clause added); def:Q24; def:Q25 (guard added); def:Q26 (two clauses added); def:Spec (conjunction of Q1-Q16, Q18-Q26: 25 conjuncts, no Q17).
Shared vocabulary: def:num (numeric cell, absent = missing); def:str (text cell); def:ageGroup (G5); def:median; def:q1Median (G4 fallback); def:rowQ1 ... def:rowQ9 (row-level rules); def:classProbs; def:confCount; def:somersD; def:auc (added after review); def:ecdf; def:ksStat; def:decileCut (G9); def:psiShare; def:outcomeRecorded (default_flag of a score table is the raw outcome; added after review).
Theorems: thm:consistent; thm:inputOK_satisfiable.

## 5. Readings taken (as they stand after the review; each is in its item's text except the def:Pipeline limitation of section 7)
1. The brief's 'a split' is the seed (a natural number), because Q11 speaks of the seed. scoreTest takes (raw test, raw training) and no seed.
2. Missing = def:num returns none (no column, empty numeric cell, or text cell).
3. Input conditions: outcome present (0 or 1) in training, may be missing in test only; nine other raw columns incl. VAR1 and age present in both tables; seed unconstrained.
4. Applicants matched by row id (VAR1 / row_id). Q1-Q6, Q9, Q12, Q13 say 'for every applicant there is a row with its id satisfying the rule'. Ids are not assumed distinct (section 3 does not say so); with duplicates each requirement chooses its row independently.
5. Metrics with no named set are computed on the validation score table.
6. Q1/Q13 'the training data' = whole raw training table before the split.
7. Age groups: '30-39' is 30 <= age < 40, etc.
8. Median: middle element or mean of the two middle; 0 on the empty list, never used.
9. Q3: indicator = 1 iff original missing; otherwise unconstrained.
10. Q4: original is the raw field; raw fields are ratios (MC 31-32), percent = 100 x raw; capped columns in percent; caps 200 and 500. Uncapped feature columns unconstrained.
11. Q5: the three counts are the raw fields.
12. Q6: utilization, debt ratio, 90-day delinquencies, total late payments, credit lines read on the raw row; income and dependents are the feature columns after Q1/Q2 (G6). A flag whose condition fails is only required not to be 1.
13. Q7: a flag is set when it is 1.
14. Q9: natural log of monthly_income after Q1; age, utilization, debt ratio from the raw row; product is (100u)(100d); nothing required when income <= 0.
15. Q10: row_id list of train ++ validation features is a permutation of the raw VAR1 list; sizes within less than 1 of 0.7 n and 0.3 n.
16. Q11: stated as worded; holds for every pipeline because features is a function of (table, seed).
17. Q12/Q13: there exists a test feature table Ft with scoreTest test train = score Ft obeying the rules against the raw test row. Constrains test feature engineering only as far as score distinguishes feature tables.
18. Q14: row_id list of each score table is a permutation of that of its feature table (VAR1 list for test); every score row complete; grade and recommendation text, the rest numeric.
19. Q15, Q16, Q18-Q21 apply to every row of all three score tables.
20. Q18: grades are strings A..F; 10 % = 0.10.
21. Q19: 5 % read as 0.05.
22. Q20: strings Approve, Review, Decline.
23. Q21: pred_logistic = 1 iff p >= 0.5; otherwise unconstrained.
24. default_flag of the validation score table is the raw outcome, matched by row id.
25. Q22: counts computed from the validation score table (positive iff p >= t); sum to the row count for every t; threshold table non-empty, each row has a numeric threshold; no particular threshold required; each ratio required only where its denominator is non-zero.
26. Q23: AUC and Gini are the summary columns; Somers' D is the standard one of the validation score table; with both classes present Gini = 2 AUC - 1 = Somers' D and AUC = standard AUC; with one class only Gini = 2 AUC - 1.
27. Q24: ks and summary tables non-empty, all KS_Statistic values equal one k; k = KS of the validation score table over pd_logistic when both classes are present.
28. Q25: scores are credit_risk_score; nine nearest-rank training decile cuts without interpolation, right-closed bins (not settled by G9); PSI rule required only when both sets have a score; a PSI value must be present.
29. Q26: decile, lift, capture_rate present on each row; capture rates sum to 1; decile values distinct; at most ten rows.

## 6. Documentation that could not be formalised as written
1. Section 3 'must stop with an error' (and G4 'no known income at all is an error'): not formalised; total functions have no error outcome; every requirement is guarded by InputOK.
2. Q12, Q13: no test feature table in section 5; stated existentially.
3. Q10 'about': no tolerance; the Lean's 'less than one applicant' rejects independent 0.7 sampling (e.g. 104,950/45,050).
4. Q9 at income <= 0: log undefined, documentation silent; also unclear whether log(income) is ln(monthly_income) or the undocumented log_monthly_income column.
5. Q11 is carried by the interface, not the item.
6. Q19: unit of interest_rate undocumented.
7. Q22-Q24: set not named; no value when a denominator is zero or a class empty.
8. Q25: decile convention and ties not given; shares of a set without scores undefined.
9. Q26: lift, capture rate, decile numbering undefined; sum-to-1 unguarded as written, unmeetable by a standard capture rate when there is no defaulter.
10. Row ids not said to be distinct.
11. No requirement says the uncapped feature columns or the feature files' default_flag carry the raw values.

## 7. Review (separate reviewer, before the consistency proof): 19 findings; 1 open after recheck
1. def:rowQ4 (Q4, weaker) - corrected: reads raw fields.
2. def:rowQ5 (Q5, weaker) - corrected: reads raw counts.
3. def:rowQ9 (Q9, weaker) - corrected in part: raw-row reading fixed; income = 0 case open (owner).
4. def:Q1 (Q1-Q3 matching, weaker) - corrected in part: income required on every feature row; duplicate-id crosswise case still passes (needs distinct VAR1 or a joint matching; owner).
5. def:InputOK (section 3 error sentence, missing requirement) - cannot state (owner).
6. def:Pipeline (interface, other) - kept; statement and text unchanged; STILL OPEN.
7. def:rowQ6 (Q6, unstated reading) - corrected: (a) raw row; (b) 'not 1' kept as literal wording, now stated.
8. def:Q11 (vacuous) - kept; text now says the interface carries it.
9. def:Q10 (stronger) - cannot state; tolerance kept and declared unruled (owner).
10. def:Q14 (weaker) - corrected: permutation of row ids.
11. def:Q12 (weaker) - corrected: rules applied to raw test row and one row of Ft.
12. def:Q12/Q13 (unstated reading) - kept; limit of the existential reading now stated (owner).
13. def:Q22 (vacuous) - corrected: non-empty threshold table, numeric thresholds, count-sum always checked.
14. def:classProbs (weaker) - added def:outcomeRecorded as a conjunct of Q22, Q23, Q24.
15. def:Q26 (weaker) - corrected in part: distinct deciles, at most ten rows; single row {decile 7, lift -5, capture 1} still passes (owner).
16. def:decileCut (unstated reading) - kept; convention now declared as a reading (owner).
17. def:Q25 (unstated reading) - corrected: PSI rule guarded.
18. def:Q23 (other) - added def:auc; Q23 requires AUC column = standard AUC with both classes present.
19. def:Spec (missing requirement) - cannot state; text now states the omission (owner).

Still open: def:Pipeline. score sees only the feature table it scores and scoreTest takes no seed, while the documents say the scores come from a model trained on the training set of the split (RM 165, RM 274). With seeds 42 and 43 a fitted model gives different test predictions but scoreTest test train must be one table; equal validation features with different training features must get equal scores. A real fitted-model program may not be presentable as a Pipeline; Q12-Q14 depend on this. The interface follows the brief. The formaliser did not edit the item (an edit clears the dependants); get_items confirms the item text states only the seed reading. Needs a text edit with re-acceptance of dependants and proofs, or an owner decision on the interface.

## 8. Consistency
Witness (thm:consistent), an artificial pipeline defined in the proof only. Features: one feature row per raw row; row_id and default_flag copied; income imputed with the Q1 median, dependents with 0; indicators, caps, late sum, eight flags and count, interactions per Q3-Q7, Q9; financial_health = 50; split at floor(7n/10); seed ignored. Scoring: probability 0, score 850, grade A, Approve, rate 0.05, prediction 0; test scoring is the same feature map then the same scoring. Metrics from the validation score table: summary AUC = auc, Gini = 2 auc - 1, KS = ksStat, PSI 0 if the ten shares agree else 1; one ks row; one decile row (1, lift 1, capture 1); one threshold row at 1/2 with the standard formulas. Proved on the way for any score table: Somers' D = 2 AUC - 1 with both classes present; the four counts sum to the row count when every row has an outcome in {0,1} and a probability. thm:inputOK_satisfiable: one-row training table (all fields present, outcome 0, income known), empty test table. Proofs use open Classical; no axiom, sorry, native_decide or unsafe; no existing statement edited.
Not shown: anything about the SAS program or a realistic model; bands B-F, Review/Decline, other rates and prediction = 1 are met vacuously (probability constant 0); Q11 holds because the seed is ignored; Q8 by a constant; PSI 1 and the single decile row are arbitrary permitted choices, showing how little Q25 and Q26 fix; the InputOK witness has an empty test table; nothing about inputs outside InputOK.

## 9. Open points for the owner
1. Section 3 error sentence: error outcome in the interface or not. 2. def:Pipeline: give score the training features/model and scoreTest the seed, or state the limitation. 3. Q12/Q13: confirm existential reading or add a test feature file. 4. Distinct VAR1. 5. Q10 tolerance. 6. Q9 at income <= 0 and which log column. 7. Q4/Q6/Q9: raw ratios, thresholds in percent. 8. Q19 unit. 9. Q22-Q24 set and undefined cases. 10. Q25 decile convention. 11. Q26 definitions, ten deciles, no-defaulter case. 12. Q6: must a flag whose condition fails be 0.

## 10. Process notes
No role-hook block in any earlier step; in this step the harness refused the write of report.md. No Lean saved locally. report-run1.md is the report of the earlier blocked run and would be superseded by this file.
