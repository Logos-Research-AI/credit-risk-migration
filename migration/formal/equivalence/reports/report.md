# Equivalence pass: does the Python port behave as the SAS original?

Blueprint `py-credit-risk-port` (`b41b22d4-720d-4290-b593-39ceab961986`), worked through the
`claude.ai Logos MCP Staging` connector. Specification: `informal-spec.md` (approved version, H13
against `confusion_metrics_macro`). Float evaluation evidence: `pairings.md`.

## Summary

117 contract items were stated. 53 are proved, 61 are disproved with an accepted proof of the
negation, and 3 are left stated and not settled. No accepted proof uses `axiom`, `sorry`,
`native_decide` or `unsafe`.

| Kind | Stated | Proved | Disproved | Not settled |
|---|---|---|---|---|
| Stage (ST1 to ST4) | 4 | 0 | 3 | 1 (ST2) |
| Step (S1 to S31) | 68 | 29 | 39 | 0 |
| Helper (H1 to H13) | 21 | 17 | 4 | 0 |
| Flag (F1 to F4) | 7 | 4 | 2 | 1 (F1 on) |
| Closed rows (C2 to C4) | 3 | 1 | 2 | 0 |
| Intent (I1 to I8) | 14 | 5 | 8 | 1 (I1 on) |

The port agrees with SAS, as real-number mathematics, on every step whose contract was expected
to hold on its domain: all of those are proved. The stage contracts ST1, ST3 and ST4 are false as
written, each through an input the stated domain does not exclude. The differences that matter
are listed under Findings.

## How to read the results

- **Strength.** Almost every contract is proved or disproved **at the real numbers**, not for
  every number type. `Tabular.RealLike` carries no laws, and the two sides use different
  operations: polars comparisons consult `isNaN` (`Pl.fLt`, `Pl.fLe`, `Pl.fEq`), SAS arithmetic
  wraps results in `Sas.fin` (`isFinite`), and integer columns reach the table through a
  `NatCast` (`Pl.ofInt`) where SAS writes literals. Each item's text names which of these
  applies. Items stated and proved **for every number type** are marked "every type".
- **Float.** Nothing about `Float` can be proved without `native_decide`. Differences that exist
  only in floating point (overflow, NaN, summation order) are therefore findings from
  evaluation, recorded in `pairings.md`, not formal results.
- **Hypotheses.** Every contract assumes the Python unit's own `_precond` item, its domain (part
  (a) only) and the parameter links of section 1. The SAS preconditions are never assumed.
- **Contracts are stated as written.** Where the as-written statement fails for a structural
  reason it is disproved, not narrowed. A contract over several units or helpers is split into
  one item per conjunct; the contract holds only if all its parts do.
- **Disproofs.** Every negation proves, inside the proof, that its witness meets every
  hypothesis of the contract. The witness and what differs are in the negation item's text.
- **Review.** A separate agent that had not written them checked every statement against the
  specification before any proof. All trust layers of the blueprint are off, so the service
  accepted statements on compilation only; the review was the only check of meaning.

## Results per contract

"Assumptions" lists parameter links and what the proof actually used. A domain condition marked
"unused" was assumed by the statement but not needed by the proof.

### Stage contracts

| Contract | Item | Result | Assumptions | Witness / note |
|---|---|---|---|---|
| ST1 | `thm:run_ST1` | disproved (on `D_fe`) | `arrange` existential, `full`, split link, `input_best32` hypothesis | One raw row with `VAR1` missing: the row is in neither Python file, SAS writes it to validation, for every join order |
| ST2 | `thm:run_py_py_py_ST2` | **not settled** | model link, `invLink` conditional, `today` | Expected false through the ROC tie rule in `model_summary.csv` (Float: Python AUC 1.0, SAS 0.5). The `exp` bound for the tie gap compiled; the stage precondition (classification-table and Hosmer-Lemeshow steps, 37-column frames) was not discharged. Rule 4 is not claimed |
| ST3 | `thm:run_py_ST3` | disproved, by a degenerate parameter | `agg` at the reals, `today` | `sas_best` returning the empty text: `KS_Statistic` missing in Python, present in SAS. A gap in the specification's links, not a port defect |
| ST4 | `thm:run_py_py_ST4` | disproved (on `D_predict`) | `arrange` existential, model link, `input_best32` hypothesis, `full` | One raw row with income "NA" and an extra numeric column `median_income` = 99: `monthly_income` is 99 in Python, missing in SAS |

### Step contracts, feature engineering

| Contract | Item | Result | Assumptions | Witness / note |
|---|---|---|---|---|
| S1(a), S1(b) | `thm:fe_run_01_clean_S1a`, `_S1b` | proved, every type | `input_best32` hypothesis; dependents condition unused | |
| S2(a) | `thm:fe_run_02_income_medians_S2a` | disproved (on domain) | | Ages 45 then 25: rows in order of first appearance in Python, ascending in SAS |
| S2(b) | `_S2b` | disproved | | Missing age: group 5 against 1 |
| S3(a) | `thm:fe_run_03_cleaned_S3a` | proved at the reals | age present (needed); dependents and income conditions unused | |
| S3(b) | `thm:fe_run_03_cleaned_S3b` | disproved | | Missing age: group 5 against 1 (the known case) |
| S4(a) | `thm:fe_run_04_imputed_S4a` | disproved (on domain) | `arrange` existential | Input column named `median_income` = 77: imputed income 77 against 1000 |
| S4(b) | `_S4b` | disproved | `arrange` existential | Missing join key on both tables: income stays missing in Python, SAS imputes |
| S5(a) | `thm:fe_run_05_features_S5a` | proved at the reals, both `full` | presence of age, utilization, debt ratio, income, credit lines, late counts; non-negativity unused | |
| S5(b) | `_S5b` | disproved | | All inputs missing: `credit_util_category` 4 against 1 |
| S6(a), S6(b) | `thm:fe_run_06_split_S6a`, `_S6b` | disproved (S6a on domain) | split link | Missing `row_id`: row in neither Python file, SAS validation |

### Step contracts, train

| Contract | Item | Result | Assumptions | Witness / note |
|---|---|---|---|---|
| S7(a), S7(b) | `thm:train_run_04_score_train_S7a`, `_S7b` | disproved, structural | model link, `invLink` conditional | The SAS scored table carries `_LEVEL_`; Python has no such column |
| S8(a) | `thm:train_run_09_confusion_train_S8a` | proved at the reals | `default_flag` present (needed for `PERCENT`); probability condition and both-outcomes unused beyond non-emptiness | |
| S8(b) | `_S8b` | disproved | | Frame with no row: one row of missing metrics against none |
| S9(a), S9(b) | `thm:train_run_10_score_valid_S9a`, `_S9b` | proved at the reals | model link; domain unused | |
| S10(a) | `thm:train_run_11_confusion_valid_S10a` | disproved (on domain) | | Missing `pred_logistic`: `PERCENT` 50 against missing |
| S10(b) | `_S10b` | disproved | | Frame with no row |
| S11(a), S11(b) | `thm:train_run_12_risk_scores_S11a`, `_S11b` | disproved | | `pd_logistic` = 3.398000000000002 (present, but not a probability): score 1 against 0 (rounding rule) |
| S12(a), S12(b) | `thm:train_run_13_roc_S12a`, `_S12b` | disproved (S12a on domain) | | Flags 0, 1 with probabilities 0.5 and 0.5000000102: area 1 against 0.5 (tie rule). The Python frame also has six columns the SAS unit does not model |
| S13(a), S13(b) | `thm:train_run_14_final_and_summary_S13a`, `_S13b` | disproved, structural | `today` | An input table with a `_LEVEL_` column: Python exports it, SAS drops it. The two items are the same statement: no `D_train` condition concerns this unit |

### Step contracts, metrics

| Contract | Item | Result | Assumptions | Witness / note |
|---|---|---|---|---|
| S14(a) roc | `thm:metrics_run_01_roc_auc_S14a_roc` | disproved, structural | | Eight Python columns against the two the SAS unit models (a gap in the SAS translation) |
| S14(a) auc | `_S14a_auc` | disproved (on domain) | | Flags 0, 1 with probabilities 0.5 and 0.5000000102: AUC 1 against 0.5 |
| S14(b) roc | `_S14b_roc` | disproved, structural | | As S14(a) roc |
| S14(b) auc | `_S14b_auc` | disproved | | Flags 1 and 2: AUC missing in Python, present in SAS |
| S15 sorted, (a) and (b) | `thm:metrics_run_02_ks_S15a_sorted`, `_S15b_sorted` | proved at the reals | | |
| S15 ks, (a) and (b) | `_S15a_ks`, `_S15b_ks` | disproved, by a degenerate parameter | no link exists for these counts | `sas_best` returning the empty text |
| S16(a) | `thm:metrics_run_03_thresholds_S16a` | proved at the reals | only non-emptiness from the domain | |
| S16(b) | `_S16b` | disproved | | Frame with no row: 5 rows against 0 |
| S17(a), S17(b) | `thm:metrics_run_04_deciles_S17a`, `_S17b` | proved at the reals | `agg` link (sum and mean); domain unused | |
| S18(a) | `thm:metrics_run_05_cumulative_lift_S18a` | disproved, by a degenerate parameter | `best8` link, `agg` | `sas_best` returning the empty text: `cum_capture_rate` missing against 1 |
| S18(b) | `_S18b` | disproved | `best8` link, `agg` | A decile whose `defaults` is missing: running sum missing in Python, carried on in SAS |
| S19(a), S19(b) | `thm:metrics_run_06_psi_S19a`, `_S19b` | proved at the reals | `agg` link (sum); domain unused | Flag off: this is also F1 "off" |
| S20(a), S20(b) | `thm:metrics_run_07_calibration_S20a`, `_S20b` | proved at the reals | `agg` link (mean); domain unused | |
| S21(a) | `thm:metrics_run_08_validation_summary_S21a` | proved at the reals | inputs are those the earlier Python steps produce; one row with a present probability | Covers any number of KS rows |
| S21(b) | `_S21b` | disproved | | Hand-made frames with two KS rows: row 2 has different columns |
| S22(a) | `thm:metrics_run_09_model_performance_S22a` | proved at the reals | as S21(a), `today` | |
| S22(b) | `_S22b` | disproved | `today` | As S21(b) |

### Step contracts, predict and the twins

| Contract | Item | Result | Assumptions | Witness / note |
|---|---|---|---|---|
| S23(a), S23(b) | `thm:predict_run_01_clean_S23a`, `_S23` | proved, every type | `input_best32` hypothesis; dependents condition unused | |
| S24(a) | `thm:predict_run_02_medians_S24a` | disproved (on domain) | | Ages 45 then 35: row order |
| S24(b) | `_S24b` | disproved | | Missing age |
| S25(a) | `thm:predict_run_03_cleaned_S25a` | disproved (on domain) | | A text `MonthlyIncome` column: `MonthlyIncome_missing` 0 against 1 |
| S25(b) | `_S25b` | disproved | | Missing age |
| S26(a), S26(b) | `thm:predict_run_04_imputed_S26a`, `_S26b` | disproved (S26a on domain) | `arrange` existential | Missing join key on both tables |
| S27(a) | `thm:predict_run_05_features_S27a` | proved at the reals, both `full` | presence conditions; non-negativity unused; income may be missing | |
| S27(b) | `_S27b` | disproved | | All inputs missing: `age_category` 5 against 1 |
| S28 | `thm:predict_run_06_score_S28` | proved at the reals | model link | No `D_predict` condition concerns the unit: one item |
| S29 | `thm:predict_run_07_predictions_S29` | disproved | | `pd_logistic` = -3999999999 (not a probability): score 1000000000601 against 1000000000600 |
| S30 | `thm:predict_run_08_outputs_S30` | disproved | no precondition item exists | A frame with none of the kept columns: 0 rows against 1 |
| S31 step 01 | `thm:predict_run_01_clean_S31` | proved, every type | | |
| S31 step 02 | `thm:predict_run_02_medians_S31` | proved, every type | | |
| S31 step 03 | `thm:predict_run_03_cleaned_S31` | proved, every type | | |
| S31 step 04 | `thm:predict_run_04_imputed_S31` | disproved | | Every input: 15 columns against 14 (`default_flag`) |
| S31 step 05 | `thm:predict_run_05_features_S31` | disproved | | Missing income: `flag_low_income` 0 against 1 |
| S31 step 05, rest | `thm:predict_run_05_features_S31_rest` | proved at the reals | | Equal apart from `flag_low_income` and `total_risk_flags` |

### Helper contracts

| Contract | Item | Result | Assumptions | Witness / note |
|---|---|---|---|---|
| H1 | `thm:lt_H1_lt`, `thm:le_H1_le`, `thm:gt_H1_gt`, `thm:ge_H1_ge`, `thm:eq_H1_eq` | proved at the reals | | `eq` includes a possibly missing scalar |
| H2 | `thm:flag_H2` | proved at the reals | | Includes a null condition (counts as 0) |
| H3 | `thm:div_H3` | proved at the reals | | Includes divisor 0, integer columns, a missing scalar divisor |
| H4 | `thm:sas_sum_H4` | proved at the reals, both `full` | `sas_sum_precond` | Includes integer columns |
| H5 | `thm:sas_min_H5_min`, `thm:sas_max_H5_max` | proved at the reals, both `full` | their preconditions | |
| H6 | `thm:sas_log_H6` | proved at the reals | | |
| H7 | `thm:sas_exp_H7` | proved, every type | | |
| H8 | `thm:sas_round_H8` | disproved | | The literal 500000000000: Python 500000000001, SAS unchanged |
| H9 | `thm:sql_sum_H9_sum`, `thm:sql_mean_H9_mean` | proved at the reals | `agg` link | Select and group contexts, empty group |
| H9 | `thm:sql_min_H9_min`, `thm:sql_max_H9_max` | proved at the reals | | |
| H10 | `thm:merge_one_to_one_H10` | disproved | `merge_one_to_one_precond` | `v = [0]` merged with an empty `v`: missing against 0 |
| H11 | `thm:proc_rank_groups_H11` | proved at the reals | column is Float64 | Ties and missing values covered |
| H12 | `thm:roc_association_H12` | disproved | `roc_association_precond` | Responses 1 and 2: area missing against 1. The tie tolerance is disproved in S12 and S14(a) |
| H13 | `thm:confusion_metrics_H13` | disproved | | Frame with no row: 1 row against 0. On a non-empty frame it holds (S16(a)) |

### Flag, closed-row and intent contracts

| Contract | Item | Result | Witness / note |
|---|---|---|---|
| F1 off | covered by S19 and ST3 | S19 proved; ST3 fails by a degenerate parameter | |
| F1 on | `thm:metrics_run_06_psi_F1_on` | **not settled** | Not attempted. Its "validation shares sum to 1" clause probably fails only beyond 10^9 validation rows with a missing probability (the precondition allows a deviation of 1e-9); not evaluated |
| F1 frame | `thm:run_py_F1_frame` | disproved | Validation probabilities 4/5 and 9/10, training 1/10 and 1/5: `status` in `validation_summary.csv` goes from "Production Ready" to "Requires Review" |
| F2 off | covered by S24 and ST4 | both disproved, see above | |
| F2 on | `thm:predict_run_02_medians_F2_on` | proved, every type | Stated on step 02: the step returns the supplied table, whose age groups are exactly 1 to 5 as a set |
| F2 frame | `thm:run_py_py_F2_frame` | disproved | Supplied medians listing age group 1 twice: 2 output rows against 1, for a row whose income was present |
| F3 off, F3 on | `thm:run_F3_off`, `thm:run_F3_on` | proved, every type | |
| F4 | `thm:run_F4` | proved, every type | The Lean keeps `fix_income_truncation` and ignores it |
| C1 | covered by the split link of ST1 | | |
| C2 | `thm:roc_association_C2` | disproved | Two rows of class 1: `TauA` is 0, not missing. The other six statistics are missing |
| C3 | `thm:predict_run_06_score_C3` | proved, every type | |
| C4 | `thm:train_run_01_fit_frame_C4` | disproved | A row with a missing `default_flag` and no missing candidate is also dropped by the mask |
| I1 off | `thm:metrics_run_06_psi_I1_off` | disproved (fails as expected) | Training 1/10, 1/5; validation 4/5, 9/10: PSI 0 with completely shifted distributions |
| I1 on | `thm:metrics_run_06_psi_I1_on` | **not settled**; false by Float evaluation | Expected to hold, but PSI is 0 with differing shares when the differing bins sit at or below the 1e-4 floor. The witness needs 20,000 training rows, too large to evaluate formally |
| I2 off | `thm:predict_run_02_medians_I2_off` | disproved (fails as expected) | The step returns the test set's own medians |
| I2 on | `thm:predict_run_02_medians_I2_on` | proved, every type | |
| I3, fe | `thm:fe_run_05_features_I3` | proved at the reals | All ten flags |
| I3, predict | `thm:predict_run_05_features_I3` | disproved (fails as expected) | Missing income with `flag_low_income` = 1 |
| I4, capping | `thm:fe_run_05_features_I4` | disproved (fails as expected) | Missing debt ratio: capped value 500 |
| I4, imputation | `thm:fe_run_04_imputed_I4` | disproved (fails as expected) | An age group with no median: income stays missing |
| I5, range | `thm:train_run_12_risk_scores_I5_range`, `_I5_range_sharp` | proved at the reals | For a probability in [0, 1] the score is in 300..850, and in fact 600..850 |
| I5, grades | `_I5_grades` | proved at the reals | Grades A to D only; F exactly from a missing probability; E unreachable |
| I5, bands | `_I5_bands` | disproved (fails as expected) | Probability 0.2 is graded A |
| I6 | `thm:predict_run_07_predictions_I6` | disproved (fails as expected) | A missing probability is predicted 0 |
| I7 | `thm:metrics_run_02_ks_I7` | disproved (fails as expected) | Formal witness is degenerate (all missing, two rows). The maximum attained twice on domain data is Float evidence only |
| I8 | `thm:predict_run_05_features_I8` | disproved | `flag_low_income` 0 in the fe pipeline, 1 in predict; `default_flag` also differs |

## Findings, most serious first

"Reachable by differential testing" asks whether comparing SAS and Python outputs on the real
data could have shown the difference.

1. **ROC tie rule: a real-number difference on the domain** (S12, S14(a) auc; expected in ST2).
   Python treats two probabilities within 1e-8 as tied; SAS groups values within about
   1.0537e-8 of the top of a group. Two opposite-class probabilities 1.02e-8 apart give AUC 1 in
   Python and 0.5 in SAS. It reaches `Train_AUC` and `Valid_AUC` in the model summary and the
   AUC and Gini in `validation_summary.csv` and `model_performance_metrics.csv`. Reachable only
   if the real data has such a pair; the judged runs did not.
2. **`fix_psi_bins` changes more than the PSI cells** (F1 frame). `status` in
   `validation_summary.csv` is computed from AUC, KS and PSI together, so it moves when PSI does.
   The frame claim of bugfix-4 is false on ordinary data. Not a SAS comparison: reachable by
   comparing flag on against flag off whenever PSI crosses 0.25.
3. **With `fix_psi_bins` on, PSI can still be 0 while the distributions differ** (I1 on; Float
   evidence only). Both shares are floored at 1e-4, so bins at or below the floor cancel. Needs
   at least 10,000 training rows with very small bins.
4. **The two copies of the feature engineering differ in two places, not one** (S31, I8).
   `flag_low_income` is 0 in feature engineering and 1 in predict on a missing income (with
   `total_risk_flags`), which the edge scenario reaches. And the feature-engineering step 04
   carries `default_flag`, which the predict copy does not, on every input.
5. **A row with a missing `row_id` vanishes from both Python files** (S6, ST1). SAS writes it to
   validation. `D_fe` says nothing about `VAR1`. Not reachable: the real `VAR1` is never missing.
6. **A raw column named `median_income` is read in place of the medians table** (S4(a), ST4).
   Not reachable: no judged CSV has such a column.
7. **Missing values outside the domain go to the last branch in Python and the first in SAS**
   (S2(b), S3(b), S5(b), S24(b), S25(b), S27(b)): age group and age category 5 against 1,
   utilization and debt categories 4 against 1, `flag_few_credit_lines` 0 against 1. The proofs
   of S3(a), S5(a) and S27(a) show that "present" is exactly what is needed; non-negativity is
   never used. Reachable only by a CSV with a missing age, utilization, debt ratio or credit
   line count.
8. **The medians table is in order of first appearance in Python, ascending in SAS** (S2(a),
   S24(a)). On the domain, and on the edge scenario. The stage outputs agree, and the judge
   matches rows by key, so it is invisible to differential testing.
9. **Rounding rule** (H8, S11, S29). `sas_round` and the SAS rule differ below 1 in absolute
   value near one half, for values from 5e11 up to 2^52, and for non-integers above 1e6.
   Unreachable for a probability, whose score lies in 600..850. S11 and S29 fail only because
   the domain says the probability is present, not that it lies in [0, 1].
10. **Inaccurate claims in the migration records.**
    - C2: a single-class ROC input gives `TauA` = 0, not missing (the record says "None
      statistics"). The Lean matches the Python source.
    - C4: the fit mask also drops rows with a missing `default_flag`.
    - `eq` has a call site in the port (`metrics_calculation.py:137`), contrary to "no site".
11. **Intent failures shared by SAS and Python** (I2 off, I4, I5 bands, I6, I7, I1 off), all as
    the specification expected. I1 off needs one correction: PSI is not "always 0 on untied
    data"; with tables of different sizes it is non-zero on both sides.
12. **Helper differences not reached by the port.** `merge_one_to_one` overwrites a shared
    variable with missing where SAS keeps the earlier value (H10); the port's one call shares no
    name. `roc_association` drops a response that is neither 0 nor 1 where SAS counts it as a
    non-event (H12, S14(b)).
13. **Inputs the Python precondition accepts and the domain does not exclude.** A frame with no
    row (H13, S16(b), S8(b), S10(b)); a missing `pred_logistic` (S10(a)); a text `MonthlyIncome`
    at step 03 (S25(a)); a missing join key (S4(b), S26); a frame with no kept column at step 08,
    which has no precondition item (S30); a supplied medians table with a repeated age group
    (F2 frame); a decile with all flags missing (S18(b)); hand-made summary frames (S21(b),
    S22(b)). None is produced by the pipeline on the judged data.
14. **Gaps in the SAS translation, not port defects.** The SAS scored training table carries
    `_LEVEL_` (S7, S13); the SAS ROC units model two of the eight columns (S12, S14 roc).
15. **Gaps in the specification.**
    - No link exists for the KS counts: the SAS unit has no `best8` parameter, so S15 (ks) and
      ST3 fail for a degenerate `sas_best`.
    - The `best8` link says nothing about an empty text, so S18(a) fails the same way.
    - `D_train` and `D_metrics` do not say a probability lies in [0, 1].
    - `D_fe` does not mention `VAR1`.
    - "The two copies differ in one place only" omits `default_flag`.
16. **Float only, on the domain as literally written** (evaluation, `pairings.md`).
    - Overflow: Python keeps `inf` where SAS gives missing (the `* 100` products, sums, the
      linear predictor: Python probability 1 and grade D, SAS missing and grade F).
    - NaN: polars orders NaN above every number; a NaN probability is predicted 1 and graded A in
      Python, 0 and F in SAS.
    - Summation order: non-integer late-payment counts differ by one unit in the last place; a
      left-fold `agg` differs from polars by 1 to 2 units in the last place on `avg_pd` and
      `mean_predicted`. At the reals all of these are proved equal (H4, H9, S17, S20).
    None is reachable from a finite CSV of realistic magnitudes, except the last-place
    differences, which the judge's tolerance already covers.

## Suspected translation errors

None. Every difference that looked like one was checked against the `.sas` and `.py` sources and
found faithful: the medians group order, the join column, the null `row_id`, `sas_round`, the
medians flag test, and `TauA` on a single class (run on the Python source).

One modelling artefact: a feature column named `selected` is dropped by Python and kept by the
SAS Lean, because Lean strings are case sensitive and SAS names are not.

## Precondition pairs: one side accepts an input the other rejects

| Units | Python accepts, SAS rejects | SAS accepts, Python rejects |
|---|---|---|
| All step units | | An empty table (every Python precondition of feature engineering requires a row; predict's do not) |
| `fe_run_01_clean` / `credit_raw_clean` (and predict twin) | Numeric `MonthlyIncome` / `NumberOfDependents` columns; text with exponent notation or over 32 characters; pre-existing `_num` columns | |
| `fe_run_03_cleaned` / `credit_cleaned`, `fe_run_05_features` / `credit_features` (and predict twins) | Pre-existing output columns (results agree) | `num_dependents` = -1 (Python requires a non-zero divisor; SAS gives missing) |
| `predict_run_03_cleaned` / `test_cleaned` | `MonthlyIncome` of any type | |
| `fe_run_04_imputed`, `predict_run_04_imputed` / the SAS joins | A `median_income` column in the left frame; missing keys; repeated groups | |
| `predict_run_02_medians` with the flag | A supplied table with a repeated age group | |
| `predict_run_08_outputs` / `kaggle_submission` | Any frame (no Python precondition exists) | |
| `train_run_04_score_train` / `logit_scored_train_output` | Missing cells; existing `_LEVEL_` or `pd_logistic` columns | Inputs where `exp(-eta)` is not finite |
| `train_run_11_confusion_valid` | A missing `pred_logistic` | |
| `train_run_13_roc`, `metrics_run_01_roc_auc`, `roc_association` / `roc_train`, `roc_valid`, `roc_stats` | A single class; an empty frame; a `default_flag` other than missing, 0 or 1 | |
| `confusion_metrics`, `metrics_run_03_thresholds` | A frame with no row | |
| `metrics_run_04_deciles` / `decile_data` | An input that already has a `decile` column | |
| `metrics_run_02_ks` / `total_good_bad` | 10^8 rows or more | |
| `fe_run_06_split` / `credit_train_validation` | | The SAS side requires a numeric `Selected`; the link does not assume it |

## Counts and housekeeping

- `get_status` (final run): 323 items, `statements_formalized` 262 (a flagged item leaves that
  count), `statements_to_write` empty, nothing waiting. 145 are the original `def:` items; 117 are contract items (`thm:`);
  61 are negation items (`neg:`), all `TheoremProved`. 61 contract items are flagged false. The
  status lists three proofs to write: `thm:run_py_py_py_ST2`, `thm:metrics_run_06_psi_F1_on`,
  `thm:metrics_run_06_psi_I1_on`. `verification_approved` is false, as expected with flagged
  and unproved items.
- No `zz_` item remains in `py-credit-risk-port`: the item list contains none.
- Existing items: see "Audit of the existing items" below.
- Three proof-dependency edges were added between contract items of this pass: S20(a) on S20(b),
  S17(a) on S17(b), S19(a) on S19(b).
- The accepted proof of S20(b) still carries stale "DRAFT / Still to do" header comments; they
  are cosmetic.
- The S7 and S13 negation texts say the exported files agree despite `_LEVEL_`. That is from
  reading the units, not from a proved statement (ST2 would have covered it).
- Seven weakened "supplement" items that one agent had added were removed before any proof.
- Row numbers of the 193-row inventory are copied from the specification: that inventory is not
  in the two source folders this pass may read.
- Left over from the earlier connector problem: an empty blueprint `zz-profile-probe`
  (`91128f70-f729-4fae-887d-d22873aefff0`) created through the local `logos-mcp` server. It has
  no items; no tool here can delete a blueprint.

## Audit of the existing items

A separate read-only agent compared the blueprint with the Lean dump of the profile taken before
this pass (`py-credit-risk-port_b41b22d4-….lean`, 12,666 lines). Details are in
`audit-existing-items.md`.

- All 145 original `def:` items have a Lean statement identical to the dump (only trailing
  whitespace normalised), each filling its whole section of the dump. All are in state
  `DefinitionFormalized`.
- The 145 ids in the blueprint and the 145 item sections of the Python part of the dump are the
  same set. No `thm:` or `neg:` name occurs in the dump.
- 323 ids, all unique: 145 `def:`, 117 `thm:`, 61 `neg:`; each negation has its contract item.
- No id contains `zz`.
- Not compared: the informal texts, dependencies and other fields of the `def:` items. Only the
  Lean statement and the state were checked.
- `def:ExprOrNum` is too large for `get_items`; its statement was read with `get_lean` and
  matched.
