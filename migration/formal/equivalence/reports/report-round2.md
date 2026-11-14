# Round 2: results under version 2 of the specification

Blueprint `py-credit-risk-port` (`b41b22d4-720d-4290-b593-39ceab961986`), `claude.ai Logos MCP
Staging`, trust layer Judging on. Specification: `informal-spec.md` version 2. Brief: `ROUND2.md`.
Round 1 results that version 2 marks "stands" are in `report.md` and were not touched. Findings
for the coding agent are in `findings-for-code.md`.

## Summary

Round 2 restated or settled 55 contracts: **29 proved, 25 disproved, 1 open.** All are at the
real numbers. No accepted proof uses `axiom`, `sorry`, `native_decide` or `unsafe`.

Of the 25 disproofs:

- 13 are the port differing from SAS on a well-formed input: the ROC tie rule (10 items, three of
  them stage files and one the helper H12), a missing `default_flag` in the confusion matrix
  (2), and a running sum over a missing value (1);
- 2 are properties the code fails: I7 on both sides, and I1 with `fix_psi_bins` on;
- 10 fail only on an input no pipeline produces or through a gap in a parameter link. They are
  listed under "Specification gaps"; the port is not at fault.

### Stage files

| Stage | Proved equal to SAS | Disproved, and by which finding | Open |
|---|---|---|---|
| ST1 feature engineering | `model_features_train.csv`, `model_features_validation.csv` | | |
| ST2 train | `risk_scores_train.csv` (conditional on `invLink`), `risk_scores_validation.csv`, `final_model_output.csv` (conditional on `invLink`) | `model_summary.csv`: ROC tie rule (step contracts S12, H12), in `Valid_AUC` | |
| ST3 metrics | `decile_analysis.csv`, `threshold_analysis.csv`, `calibration_plot.csv` | `validation_summary.csv`, `model_performance_metrics.csv`: ROC tie rule (step contract S14), in `AUC` | `ks_statistic.csv` |
| ST4 predict | `kaggle_submission.csv`, `test_predictions.csv` (under the `input_best32` hypothesis) | | |

Ten of fourteen files are proved equal to SAS, three are disproved by one finding, one is open.

### The three contracts to settle

| Contract | Result |
|---|---|
| ST2 | Settled per file: three proved, `model_summary.csv` disproved. One input is proved to meet the stage precondition (all 17 conjuncts, the out-of-scope steps included) |
| F1 on | Settled in two parts. Binning and the floored term of an empty bin: proved. "The validation shares sum to 1": disproved, but only with 10^9 validation rows of which one has a missing probability; proved true otherwise |
| I1 on | Disproved formally: with the fix on, PSI is exactly 0 while the shares differ in two bins, all at or below the 1e-4 floor. The general lemma about the floored terms that section 8 asks for is stated as its own item and proved |

## How round 2 was carried out

- **Text first, judged statements.** For every item the specification text was written first,
  then the Lean. The judge accepted every statement on its first submission. After each
  acceptance the service replaces the item's text with its own summary, and several summaries
  misstated the contract; the specification text was restored on every contract item.
- **Review.** A reviewer who had not written them checked every statement against the
  specification before its proof. Corrections made: S6(a) carried two domain hypotheses the
  specification does not sanction; part (b) of S14, S15 (KS) and S16 had dropped the stage
  conditions as well as the "never missing" ones; the F1 on term clause skipped a training bin
  with a missing probability.
- **Well-formedness** is stated once per shape, as 28 definition items (`def:wf_fe_*`,
  `def:wf_pr_*`, `def:wf_tr_*`, `def:wf_me_*`): stage inputs follow the four bullets of section 2;
  a step shape is the exact column list with kinds, equal column lengths, and at least one row.
- **Readings fixed during the round.**
  - A step frame is well formed by its columns only, as section 2 says, so its cells are
    otherwise unconstrained. Where a contract fails only on a cell no pipeline produces, it is
    disproved as written and classified as a specification gap.
  - A step that reads the imported stage table directly (metrics steps 01 to 03 and the PSI
    step) takes a stage input table: the four stage bullets apply in both parts.
  - `D_train` "no model variable is missing" includes `default_flag` present where the unit
    reads it, by the precedent of the standing S8(a).
  - The ST3 row lists "both text links", so each of its six files assumes both.
- **Split and added items.** S14 stays split into its roc and auc parts. F1 on is split into
  `_bins` and `_sum`, because its third sentence fails for a reason unrelated to binning. One
  item is added that the list does not name: `thm:metrics_run_06_psi_I1_on_floor`, the lemma
  section 8 asks to state. S13 is one item (the round 1 `_S13a` and `_S13b` were the same
  statement).

## Results per contract touched

"Not needed" lists hypotheses the statement assumes and the proof does not use.

### Feature engineering

| Contract | Item | Result | Witness / note |
|---|---|---|---|
| S2(a) | `thm:fe_run_02_income_medians_S2a` | proved | As sets of rows. Not needed: "every age group has a present income" |
| S4(a), S4(b) | `thm:fe_run_04_imputed_S4a`, `_S4b` | disproved, specification gap | `age_group` missing in the cleaned row and in the medians row (median 20): `monthly_income` missing in Python, 20 in SAS, for every join order |
| S6(a), S6(b) | `thm:fe_run_06_split_S6a`, `_S6b` | disproved, specification gap | One feature row with `row_id` missing: 0 validation rows in Python, 1 in SAS. The two items have the same statement: `D_fe` says nothing about `row_id` |
| ST1, train file | `thm:run_ST1_model_features_train` | proved | Join order: identity. Not needed: `VAR1` distinct; `Selected` is 0 or 1 |
| ST1, validation file | `thm:run_ST1_model_features_validation` | proved | As above |

### Train

| Contract | Item | Result | Witness / note |
|---|---|---|---|
| S7(a), S7(b) | `thm:train_run_04_score_train_S7a`, `_S7b` | proved, conditional on `invLink` | All columns except `_LEVEL_`. (a) follows from (b) |
| S8(b) | `thm:train_run_09_confusion_train_S8b` | disproved | One row with `default_flag` missing: `PERCENT` 100 in Python, missing in SAS |
| S10(a) | `thm:train_run_11_confusion_valid_S10a` | disproved, specification gap | `pred_logistic` missing on both rows: `PERCENT` 50, 50 against missing |
| S10(b) | `_S10b` | disproved | One row with `default_flag` missing: `PERCENT` 100 against missing |
| S11(a), S11(b) | `thm:train_run_12_risk_scores_S11a`, `_S11b` | proved | Probability in [0, 1] or missing |
| S12(a), S12(b) | `thm:train_run_13_roc_S12a`, `_S12b` | disproved | `default_flag` 0, 1 with `pd_logistic` 0.5, 0.5000000102: Area 1 in Python, 0.5 in SAS |
| S13 | `thm:train_run_14_final_and_summary_S13` | proved | Not needed: the unit's precondition |
| H12 | `thm:roc_association_H12` | disproved | The same two rows as S12 |
| ST2 `risk_scores_train.csv` | `thm:run_py_py_py_ST2_risk_scores_train` | proved, conditional on `invLink` | Not needed: anything on the validation table |
| ST2 `risk_scores_validation.csv` | `_ST2_risk_scores_validation` | proved | Not conditional: this chain does not use `invLink`. Not needed: the domain |
| ST2 `final_model_output.csv` | `_ST2_final_model_output` | proved, conditional on `invLink` | From the `risk_scores_train` file |
| ST2 `model_summary.csv` | `_ST2_model_summary` | disproved | Two-row tables, flags 0 and 1, one validation cell `credit_utilization_capped` = 4.1e-8, model with that variable and coefficient 1: `Valid_AUC` 1 in Python, 0.5 in SAS. Differs only through S12 / H12 |

### Metrics

| Contract | Item | Result | Witness / note |
|---|---|---|---|
| S14(a) roc, auc; S14(b) roc, auc | `thm:metrics_run_01_roc_auc_S14a_roc`, `_S14a_auc`, `_S14b_roc`, `_S14b_auc` | disproved | The two rows of S12, in a well-formed 51-column table in `D_metrics`: Area and AUC 1 against 0.5 |
| S15 KS (a), (b) | `thm:metrics_run_02_ks_S15a_ks`, `_S15b_ks` | disproved, specification gap | A `sas_best` that renders the count 1 as empty text, which the count link allows: two rows with missing `KS_Statistic` in Python, one row in SAS |
| S16(b) | `thm:metrics_run_03_thresholds_S16b` | proved | Needs only a non-empty table |
| S18(a) | `thm:metrics_run_05_cumulative_lift_S18a` | proved | Uses the never-empty clause of the `best8` link |
| S18(b) | `_S18b` | disproved | Deciles 4 and 7 with `defaults` 1 and missing: `cum_defaults` on row 2 missing in Python, 1 in SAS |
| S21(b) | `thm:metrics_run_08_validation_summary_S21b` | proved | |
| S22(b) | `thm:metrics_run_09_model_performance_S22b` | proved | |
| H13 | `thm:confusion_metrics_H13` | proved | On a frame with at least one row |
| I7 | `thm:metrics_run_02_ks_I7` | disproved (fails as expected) | Flags 0, 1, 0 with probabilities 0, 1/2, 1, with a sound format function: two rows, on both sides |
| ST3 `decile_analysis.csv` | `thm:run_py_ST3_decile_analysis` | proved | Not needed: the domain and the text links |
| ST3 `threshold_analysis.csv` | `_ST3_threshold_analysis` | proved | |
| ST3 `calibration_plot.csv` | `_ST3_calibration_plot` | proved | Not needed: the domain and the text links |
| ST3 `validation_summary.csv` | `_ST3_validation_summary` | disproved | Validation = training = the two rows of S14: `AUC` 1 against 0.5. Differs only through S14 |
| ST3 `model_performance_metrics.csv` | `_ST3_model_performance_metrics` | disproved | As above |
| ST3 `ks_statistic.csv` | `_ST3_ks_statistic` | **open** | See "Open" |

### Predict

| Contract | Item | Result | Witness / note |
|---|---|---|---|
| S24(a) | `thm:predict_run_02_medians_S24a` | proved | As sets of rows |
| S25(a) | `thm:predict_run_03_cleaned_S25a` | proved | |
| S26(a), S26(b) | `thm:predict_run_04_imputed_S26a`, `_S26b` | disproved, specification gap | As S4: `age_group` missing on both tables, median 20 |
| S29 | `thm:predict_run_07_predictions_S29` | proved | Probability in [0, 1] or missing; the bound is used only for the rounding |
| S30 | `thm:predict_run_08_outputs_S30` | proved | |
| ST4 `kaggle_submission.csv` | `thm:run_py_py_ST4_kaggle_submission` | proved | Join order: identity. Not needed: `VAR1` present or distinct |
| ST4 `test_predictions.csv` | `thm:run_py_py_ST4_test_predictions` | proved | As above |

### Flags and intents

| Contract | Item | Result | Witness / note |
|---|---|---|---|
| F1 frame | `thm:run_py_F1_frame` | proved | The version 2 wording. Uses no hypothesis. The round 1 disproof of the bugfix-4 wording stands as a finding against the record; its negation item was removed with the restatement |
| F1 on, binning | `thm:metrics_run_06_psi_F1_on_bins` | proved | Not needed: well-formedness |
| F1 on, shares sum to 1 | `thm:metrics_run_06_psi_F1_on_sum` | disproved, specification gap | Training one row at 0.5; validation 10^9 rows, 0.5 on all but one, which is missing: the shares sum to 1 - 1e-9 |
| F2 frame | `thm:run_py_py_F2_frame` | proved | Not needed: well-formedness of the raw table, and five of the seven step preconditions |
| I1 on | `thm:metrics_run_06_psi_I1_on` | disproved | Training 20,000 rows (0.1 once, 0.5 on 19,998, 0.9 once); validation 10,000 rows (0.5 on 9,999, 0.95 once): shares 0.00005, 0.9999, 0.00005 against 0, 0.9999, 0.0001, PSI = 0 |
| I1 on, floor lemma | `thm:metrics_run_06_psi_I1_on_floor` | proved | If every bin whose shares differ has both at or below 1e-4, PSI = 0 |

## Findings of round 2

`findings-for-code.md` has each one with the Python lines, the SAS rule and the reach. In short:

1. **ROC tie rule** (S12, H12, S14, three stage files). Python ties two probabilities within
   1e-8 of each other; SAS groups from the largest value down, within 1.0536712127723509e-8 of
   the group's top. **This corrects round 1**, which said the judged runs did not reach it: on
   the reference training scores 280 pairs are tied under the SAS rule and 275 under Python's
   (the rulebook's own evidence note for R25, reproduced on the reference file). The area
   differs by 2.2e-9 and `Train_AUC`, written with four decimals, is 0.8592 either way. The
   reference validation table and the edge scenarios give identical counts.
2. **I1 with the fix on.** PSI can be exactly 0 while the distributions differ, when every
   differing bin is at or below the floor. Needs more than 10,000 training rows.
3. **Missing `default_flag` in the confusion matrix** (S8(b), S10(b)). `PERCENT` 100 in Python,
   missing in SAS. Touches only the `printed_confusion_*` files; no judged table has a missing
   flag.
4. **Running sum over a missing value** (S18(b)). `cum_defaults` goes missing in Python and
   carries on in SAS. Touches only `printed_cumulative_lift.csv`; needs a decile whose flags are
   all missing.
5. **I7.** `ks_statistic` has two rows when the maximum is attained twice, on both sides.

One correction to round 1's classification, from checking the SAS scripts: the two SAS copies of
the feature step agree on `flag_low_income`; only the Python copies differ (plain `<` in feature
engineering, the SAS comparison in predict). So that part of S31 / I8 is a port difference, in
the feature-engineering copy. The `default_flag` difference between the copies is shared with
SAS.

## Specification gaps

Contracts disproved only on an input no pipeline produces, or through a missing link.

- **S4, S26:** a missing `age_group` join key. Steps 02 and 03 never produce one. On the frames
  the pipeline does produce, the join is proved equal to SAS inside the ST1 and ST4 proofs.
- **S6:** a missing `row_id` in the step-06 frame. The `row_id` condition is stated for stage
  inputs only.
- **S10(a):** a missing `pred_logistic`. The step shape fixes the column's kind, not its cells.
- **S15 KS:** the count link lacks "the text is never empty". It is also silent for 10^8 rows or
  more, which is why ST3 `ks_statistic.csv` is open. The `best8` link says nothing about a
  missing value.
- **F1 on, shares sum to 1:** fails only from 10^9 validation rows.
- **"At least one row" on a medians frame** excludes the zero-row medians frame the pipeline
  produces when every income is missing. Both sides agree there, by evaluation.
- **Edge scenarios of metrics** have 3 columns, not the 51 of the stage's input file, so no
  restated metrics contract covers them literally.
- **Standing items that still carry version 1 hypotheses.** S1(a), S3(a), S5(a) and S27(a) keep
  non-negativity hypotheses that version 2 removed. They stand untouched, as section 9 says; the
  stage proofs re-prove those steps without them.

## Open

- **`thm:run_py_ST3_ks_statistic`.** Not proved, not disproved. With both text links the empty
  text is excluded, but the count link says nothing for 10^8 rows or more of one class, where
  the SAS unit uses the exact count. A formal witness would need a table that size. Below that
  size the two sides are expected to agree; the evidence is one lemma on a three-row table and
  round 1's evaluations, not a general proof.

## Hypotheses can be met (rule 4)

| Contracts | How shown |
|---|---|
| Every disproved contract | The negation proves its witness meets every hypothesis |
| ST2, four files | The `model_summary` negation proves one input meets well-formedness, `D_train`, the `invLink` hypothesis and all 17 conjuncts of the stage precondition. Its linear-algebra and format parameters are not honest implementations (the contract quantifies over them), so it says nothing about the model fit |
| ST3, six files | The `validation_summary` negation proves one input meets every hypothesis, the stage precondition included |
| The four PSI flag-on items | The I1 on negation proves its witness meets well-formedness and the precondition |
| S2(a), S7, S11, S13, S16(b), S21(b), S22(b), S24(a), S25(a), S29, S30, H13 | A lemma at the reals inside the proof file |
| ST1, S18(a), ST4 | Evaluation at `Float` of every conjunct on a concrete input, and of the conclusion; not a proof at the reals |
| **F2 frame** | **Not machine-checked.** `run_py_py` was evaluated with the flag on and off on a two-row table and behaves as the contract says, but the hypotheses on that input were checked by reading only. A carrier item to evaluate them was refused by the session's permission settings |

## Counts and housekeeping

- `get_status` (final): 346 items, `statements_formalized` 301, `statements_to_write` empty,
  nothing waiting, one proof to write (`thm:run_py_ST3_ks_statistic`), 45 contracts flagged
  false. `verification_approved` is false, as expected.
- By prefix: 173 `def:` (the 145 originals and 28 well-formedness definitions), 128 `thm:`,
  45 `neg:`. Across both rounds: 82 contracts proved, 45 disproved, 1 open.
- No `zz` item remains: the item list contains none.
- Original `def:` items: see "Audit" below.
- **Rule breaches to report.**
  - Lean was copied to a local scratch file twice, by two different agents, when a tool result
    was too large to read (`st4_lean_view.txt`, `psi-deps.txt`). Both files were deleted at
    once and nothing remains on disk, but PROMPT.md forbids any local copy.
  - Two agents delegated part of their work to sub-agents of their own, so more than four
    agents may have worked on the blueprint at the same time for a while.
- **Proof-dependency edges added** (all between contract items):
  - S7(a) on S7(b); S11(a) on S11(b);
  - ST1 train on S1(b), S2(a) and S5(a); ST1 validation on S1(b), S2(a). The S5(a) edge is not
    used by the proof; removing it would clear the item, so it is left;
  - ST2 `risk_scores_validation` on S9(b), S11(b); `risk_scores_train` on S7(b), S8(a), S11(b);
    `final_model_output` on the `risk_scores_train` file;
  - ST3 `decile_analysis` on S17(b) and S15(b) sorted; `calibration_plot` on S20(b) and S15(b)
    sorted; `threshold_analysis` on S16(a) and S15(b) sorted;
  - the two ST3 negations on S19(a), and `model_performance_metrics` also on S16(a);
  - each ST4 file on S23, S24(a), S25(a), S28, S29.
- **`decide +kernel`** is used once, in the ST4 proofs, for a closed fact about 43 column names.
  It is kernel evaluation, not `native_decide`.
- **Editing a proof text resets an accepted theorem.** It happened on S24(a), S29, the two ST4
  items and the F2 frame; each was re-submitted unchanged and is `TheoremProved` again.
- **A leftover draft** with `sorry` placeholders is stored on `thm:run_py_py_py_ST2_model_summary`.
  It is not an accepted proof; the accepted result is the negation.
- **Item texts.** The specification text was restored on the contract items. The 28 definition
  items carry the service's own summaries where those were accurate.
- The bug-fix and classification records are not in the two source folders; their wording is
  taken from the specification.

## Audit of the original items

A read-only agent repeated the round 1 audit at the end of round 2, against the Lean dump taken
before any proving work.

- All 145 original `def:` items have a Lean statement identical to their section of the dump
  (only trailing whitespace normalised), at the same dump lines as in `audit-existing-items.md`,
  and all are in state `DefinitionFormalized`.
- 346 ids, all unique: 173 `def:`, 128 `thm:`, 45 `neg:`. Every negation has its contract item.
  The 28 `def:` ids that are not original are exactly the well-formedness definitions.
- No id contains `zz`.
- Not compared: the informal texts and dependencies of the original items; the content of the
  28 new definitions and of the contract items (those were read by the reviewers, not by this
  audit).
