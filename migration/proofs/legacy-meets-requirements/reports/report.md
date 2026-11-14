# Does the legacy SAS program meet the requirements? Report

## Outcome

The legacy SAS program does not meet the documented requirements: 13 of the 26 contracts are disproved with a counterexample that an independent check confirmed as a real failure of the SAS code.

| Result | Count | Requirements |
|---|---|---|
| Proved about the SAS | 5 | Q8, Q16, Q19, Q20, Q21 |
| Proved, by construction only | 1 | Q11 |
| Disproved, check confirmed | 13 | Q1, Q6, Q7, Q9, Q13, Q14, Q15, Q18, Q22, Q23, Q24, Q25, Q27 |
| Negation proved, but the check found the reason is an artefact | 2 | Q12, Q26 |
| Neither proved nor disproved | 5 | Q2, Q3, Q4, Q5, Q10 |
| `score_chains_agree` | proved | (not a requirement) |

- **Q12 and Q26 are flagged false in the blueprint, but should not go forward as SAS violations as they stand.** Q12 fails only because the formal statement demands that two differently laid out files be equal. The Q26 witness lies outside a unit's precondition.
- **The five open contracts share one cause.** The import link binds only raw tables that have a "delivery", and `InputOK` does not guarantee one. On tables that have a delivery, all five appear to hold; Q5 is machine-checked on that branch.
- **Nothing is fully machine-checked against the informal text.** Every trust layer of the blueprint is off, so "accepted" means the Lean compiles without `sorry`, `axiom`, `native_decide` or `unsafe`.

No file was written and no existing item was changed in this step. No hook blocked a call. The local `logos-mcp` server failed to connect, but it was not needed; all calls went through Logos MCP Staging. My standing instructions name the port-equals-legacy brief; I followed the brief the task named, `/Users/cristophersalvi/GitHub/credit-risk-migration/migration/proofs/legacy-meets-requirements/brief-prover.md`.

## get_status (called in this step)

| Field | Value |
|---|---|
| total_items | 126 |
| statements_formalized | 111 |
| statements_pinned | 0 |
| statements_to_write | none |
| proofs_to_write | 5: `thm:sas_Q2`, `sas_Q3`, `sas_Q4`, `sas_Q5`, `sas_Q10` |
| waiting | none |
| flagged | 15: `thm:sas_Q1`, `Q6`, `Q7`, `Q9`, `Q12`, `Q13`, `Q14`, `Q15`, `Q18`, `Q22`, `Q23`, `Q24`, `Q25`, `Q26`, `Q27` |
| verification_approved | false |

The 27 theorem items split as 7 proved (Q8, Q11, Q16, Q19, Q20, Q21, `score_chains_agree`), 15 flagged with a proved negation item, and 5 unproved.

Blueprint graph: https://platform-staging.logosresearch.ai/view/waad_AzureAd_b85254ea-5bb2-40b8-b836-c90bdf235fc9/3f5df696-7c80-45cc-809f-b2881714663d

## How sasPipeline is wired

`def:sasPipeline` has type `CreditRisk.Pipeline` with `Model := Sas.Model ℝ`. It only composes existing units; the reviewer found no unit skipped, reordered, renamed or applied to the wrong table. Every unit is total, so all five steps return `some` on every input.

| Step | Wiring | SAS source |
|---|---|---|
| `features train seed` | `importTrain`, `credit_raw_clean`, then `income_medians` and `credit_cleaned` (both from the cleaned raw table), `credit_imputed arrange`, `credit_features`, `split seed`, `credit_train_validation`, the two export units. Returns the pair (train, validation). | `feature_engineering.sas`, all eight units in order |
| `fit F` | `some (fit F)`, the parameter | later pass |
| `score m F` | `logit_scored_valid_temp m (readFeatures F)`, `logit_scored_valid`, `risk_scores_validation`, `risk_scores_validation_clean`. The same validation chain is applied to F1 and F2. | `train.sas` 150-155, 157-168, 246-275, 331-335 |
| `scoreTest m test _` | `importTest`, `test_raw_clean`, `test_income_medians` and `test_cleaned`, `test_imputed arrange`, `test_features`, `test_scored_temp m`, `test_scored`, `test_predictions`, `test_predictions_full`. The training table is not read. | `predict.sas` |
| `metrics S1 S2` | `roc_stats` on the unsorted validation scores; everything else on the sorted table: `total_good_bad`, `ks_calculation`, `ks_statistic`, `train_bins`/`valid_bins`, `psi_calculation`, `psi_summary`, `validation_summary`, `decile_data`, `decile_analysis agg`, `threshold_analysis`. | `metrics_calculation.sas` |

Not wired, because they are on no path to an interface output:
- the training scoring chain of `train.sas` and its tables;
- `total_defaults`, `cumulative_lift`, the calibration units and `model_performance_metrics`;
- `kaggle_submission`.

So the open parameters `best8` and `today` do not appear. The training chain is tied in only through `score_chains_agree`.

### Parameters and links (`def:SasLinks`, one definition, nine parameters)

| Parameter | Link as stated in Lean |
|---|---|
| `importTrain`, `importTest` | For every raw table **that has a delivery**, the import returns one. A delivery has the same rows in order and the same cell for every column other than `MonthlyIncome` and `NumberOfDependents`. Those two are text cells that `Sas.inputBest` reads back to `CreditRisk.num`. It lies inside `credit_raw_clean_precond` or `test_raw_clean_precond`. |
| `readFeatures`, `readScoresTrain`, `readScoresValid` | the identity |
| `arrange` | a permutation of its argument; one `arrange` serves both joins |
| `split` | rows in order, each with `Selected` 0 or 1 added; the number selected is within 1 of 0.7 n (the size clause, "conditional on the draw") |
| `fit` | every term of `fit F` names a numeric column of every row of F ("conditional on the fit") |
| `agg` | real sum and mean |
| `invLink` | not a parameter; appears only in `score_chains_agree` |

Departures and weak points, all reported by the author and confirmed by the reviewer:
- **Import guard.** The brief's link has no "has a delivery" guard. Without it `SasLinks` is unsatisfiable and every contract is vacuous. With it, the imports are unconstrained on `InputOK` tables with no delivery: an income such as 1/3, or a column already named `MonthlyIncome_num` or `NumberOfDependents_num`. This is what blocks Q2, Q3, Q4, Q5 and Q10.
- **Fit link.** It is vacuous on an empty F1, and it admits `default_flag` and `row_id` as terms.
- **CSV round trip.** The identity read links hide `format _numeric_ best12.` at `feature_engineering.sas` 253-264. Every exact-value result holds modulo that round trip being exact.
- **Seed.** `feature_engineering.sas` line 212 hard-codes seed 42; `sasPipeline` passes the caller's seed.
- **Error outcome.** `roc_stats_precond` says SAS produces no table without both classes, but the Lean still returns one. Results about metrics on such score tables are outside the checked range.
- **Stale edges.** `def:SasLinks` still lists four statement dependencies it does not need. This is housekeeping only.
- **Satisfiability.** In the assembly step it was argued, not proved. The accepted negation proofs each prove `SasLinks` for concrete parameters, so it is satisfiable.

## Every requirement

"Check" is the independent disproof check. Links in the last column are those the result or the counterexample's parameters rely on.

| Req | Item | Outcome | Check | Conditional on / note |
|---|---|---|---|---|
| Q1 | `thm:sas_Q1` | disproved | confirmed | import, arrange, split. Failure independent of the choices. |
| Q2 | `thm:sas_Q2` | needs-ruling | n/a | False only on tables with no delivery. Informally holds with importTrain, arrange, split. |
| Q3 | `thm:sas_Q3` | open | n/a | Same gap. Hand trace uses importTrain, arrange, the row clause of split. |
| Q4 | `thm:sas_Q4` | open | n/a | Same gap. importTrain, arrange, split. |
| Q5 | `thm:sas_Q5` | open | n/a | Same gap. The delivery branch is machine-checked in an unaccepted draft; one `sorry` remains for the no-delivery case. |
| Q6 | `thm:sas_Q6` | disproved | confirmed | None. Needs a non-integer 90-day count between 0 and 1. |
| Q7 | `thm:sas_Q7` | disproved | confirmed | None; computed per row before the split. |
| Q8 | `thm:sas_Q8` | proved | n/a | Row clause of split only; not conditional on the draw. |
| Q9 | `thm:sas_Q9` | disproved | confirmed | None. A second violation (the log clause) is seen by reading only. |
| Q10 | `thm:sas_Q10` | open | n/a | Same gap. The size clause would be by-construction and conditional on the draw. |
| Q11 | `thm:sas_Q11` | by-construction | n/a | None; `SasLinks` unused. Says nothing about the SAS. |
| Q12 | `thm:sas_Q12` | negation proved; report as needs-ruling | artefact | Failure comes from exact table equality between two file layouts. |
| Q13 | `thm:sas_Q13` | disproved | confirmed | All links met by the witness; the violation holds for every model. |
| Q14 | `thm:sas_Q14` | disproved | confirmed | Conditional on the fit: the model must contain an income-derived term. The shipped model does. |
| Q15 | `thm:sas_Q15` | disproved | confirmed | Conditional on the fit (a constant model gives p = 0.25). The defect is generic. |
| Q16 | `thm:sas_Q16` | proved | n/a | None. Training score file only through `score_chains_agree`. |
| Q18 | `thm:sas_Q18` | disproved | confirmed | Conditional on the fit (constant model, p = 0.20). Wrong for every present p ≥ 10 %. |
| Q19 | `thm:sas_Q19` | proved | n/a | None. Training score file only through `score_chains_agree`. |
| Q20 | `thm:sas_Q20` | proved | n/a | None. Same scope note. |
| Q21 | `thm:sas_Q21` | proved | n/a | None. Same scope note. |
| Q22 | `thm:sas_Q22` | disproved | confirmed, with caveats | Conditional on the draw (empty validation set); fit with no terms. See below. |
| Q23 | `thm:sas_Q23` | disproved | confirmed | Draw (4 of 7 selected) and fit (intercept only). |
| Q24 | `thm:sas_Q24` | disproved | confirmed | Draw (2 of 4 selected) and fit (intercept only). |
| Q25 | `thm:sas_Q25` | disproved | confirmed | Draw and fit; S1 rests on `score_chains_agree` (proved). |
| Q26 | `thm:sas_Q26` | negation proved; report as open | artefact | Witness outside `roc_stats_precond`. |
| Q27 | `thm:sas_Q27` | disproved | confirmed | None. Counterexample is necessarily outside `InputOK`. |
| chains | `thm:score_chains_agree` | proved | n/a | invLink, readFeatures, arrange, row clause of split, fit. |

There is no Q17 contract, as the brief says. No requirement was reported as `interface-mismatch`.

## What the disproof checks found

All 15 negation items are exact negations of their contracts, in state TheoremProved, and their proof text has no `sorry`, `axiom`, `native_decide` or `unsafe`. The checks read `used_decls` at depth 1 only, so no transitive axiom listing was obtained.

**Confirmed as real SAS failures (13):** Q1, Q6, Q7, Q9, Q13, Q14, Q15, Q18, Q22, Q23, Q24, Q25, Q27.

**Not confirmed (2):**
- **Q12.** The proof is sound, but it shows only that the test predictions file (fifteen KEEP columns) can never equal the output of the validation scoring chain, which keeps `base_score` and every feature column. The documentation does not ask for equal layouts. The real deviation, medians taken from the test file, is the Q13 finding. The checker recommends `needs-ruling`.
- **Q26.** The witness has an empty validation score table, which violates `roc_stats_precond` in the same `metrics` step. By the brief's rule this is a failure of the model, not of the program. The defect looks real from the units: fewer than ten validation rows, or tied scores, give fewer than ten decile rows. A new witness is needed.

**Caveats on confirmed disproofs:**
- **Q22 uses the same input as Q26.** Its checker accepted it because the failing clause (threshold table non-empty) does not pass through `roc_stats`. The Q26 checker asked for Q22 to be re-checked. The failing clause can only fail on an empty validation set, where `roc_stats_precond` always fails. The two checks disagree on whether that disqualifies the witness.
- **Unrealistic fits.** The witness models for Q15, Q18, Q22, Q23, Q24 and Q25 are allowed by the fit link but are not what PROC LOGISTIC would return; several training parts have a single outcome level. The defects do not depend on the model chosen.
- **Split rounding.** The witnesses for Q23 and Q24 select floor(0.7 n) rows. The checkers recall that real PROC SURVEYSELECT rounds up; this was not verified. Replaying them on real SAS needs larger tables (about ten rows).
- **Q27.** The counterexample cannot meet `InputOK`, because the violated clause speaks only of inputs outside it. Only the training-table clause is proved; the test-table clause is claimed, not proved.
- **Q6.** The contract would hold if the count columns were whole numbers.
- **Preconditions.** In most disproofs the downstream unit preconditions were checked by reading, not proved in Lean. Only the import and `arrange` preconditions are machine-checked.

**Line corrections from the checks:**
- Q15: the ROUND is at `train.sas` 251-253 (validation) and 217-219 (training), and `predict.sas` 235-237.
- Q18: the training ladder is at `train.sas` 222-227, in addition to 255-260 and `predict.sas` 240-245.
- Q14: the CASE in `predict.sas` is at 102-104.
- Q9: the log is at `feature_engineering.sas` 191 and `predict.sas` 190.
- Q27: PROC IMPORT is at `feature_engineering.sas` 28-33.

## What is open

1. **Ruling on the import link (blocks Q2, Q3, Q4, Q5, Q10).** Either restrict `InputOK` or the link to raw tables that have a delivery, or accept disproofs on undeliverable tables as findings about the model. The first option means income and dependents are missing or a decimal of at most 32 characters without exponent, and no `_num` columns exist. With it, Q5's draft becomes a proof once the `sorry` branch is removed, and the others should follow the same route.
2. **Ruling on Q12.** Which columns of the test predictions must agree with the scored table. If Q12 is restated, a disproof on its Q1 clause is still needed.
3. **Q26 needs a new witness.** It should have a non-empty validation set with both classes: for example 10 training rows, 7 selected, an intercept-only fit, with every metrics precondition checked.
4. **Q22 needs a decision.** Is an empty validation set an admissible witness, and should ruling G19 excuse missing threshold rows there?
5. **Fit link.** A ruling is needed on excluding `default_flag` and `row_id` and on the empty-F1 case.
6. **Q6.** Should `InputOK` require whole-number counts? That is a question for the requirements owner.
7. **Stale flags.** `thm:sas_Q12` and `thm:sas_Q26` remain flagged false in the blueprint; I did not unflag them.
8. **Not established:**
   - bit-level agreement of the two scoring chains in binary64;
   - exactness of the best12. CSV round trip;
   - the unexamined clauses of Q23 and Q24 (first summary row, summary-table KS, `outcomeRecorded`);
   - the missing-dependents clause of Q13;
   - whether a missing `pd_logistic` row breaks the count clause of Q22.

Files referred to: `/Users/cristophersalvi/GitHub/credit-risk-migration/migration/proofs/legacy-meets-requirements/brief-prover.md`, `/Users/cristophersalvi/GitHub/credit-risk-migration/migration/requirements/requirements.md`, and the four scripts under `/Users/cristophersalvi/GitHub/credit-risk-migration/legacy/`.
