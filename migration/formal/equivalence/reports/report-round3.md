# Round 3: results after the code changes

Blueprint `py-credit-risk-port` (`b41b22d4-720d-4290-b593-39ceab961986`), `claude.ai Logos MCP
Staging`, trust layer Judging on (never switched off). Specification: `informal-spec.md` version
2.1. Brief: `ROUND3.md`. Findings for the coding agent are in `findings-for-code.md`, rewritten
for the code as it now stands.

## Summary

Round 3 touched 85 contracts: **61 proved, 14 disproved, 10 open.** All are at the real numbers.
No accepted proof uses `axiom`, `sorry`, `native_decide` or `unsafe`.

- **No contract is disproved today by the port differing from SAS.** Every `port-differs-from-sas`
  finding of round 2 (P1 to P9) is either proved fixed or, for the ROC tie rule, not yet
  confirmed (next point).
- **The ROC tie rule (P1) is not confirmed.** The ten contracts that depend on it are open, not
  proved: the SAS definition pinned in the blueprint still carries the old tie constant, while the
  Python side and the rulebook carry the corrected one. See "Blocker".
- **The PSI fix (D1) is confirmed.** I1 with the fix on is proved: PSI is 0 exactly when the two
  sets have the same share in every training bin.
- Of the 14 disproofs, 8 are shared intent failures (SAS and Python agree), 1 is an inaccurate
  record, and 5 fail only through the form of a round 1 statement or a gap in the specification.
  Four of those five are contracts section 9 expected to hold: S2(b), S24(b), S25(b), S18(b), and
  H10 is the fifth.

### The fourteen stage files

| Stage | Proved equal to SAS | Disproved | Open |
|---|---|---|---|
| ST1 feature engineering | `model_features_train.csv`, `model_features_validation.csv` | | |
| ST2 train | `risk_scores_train.csv` (conditional on `invLink`), `risk_scores_validation.csv`, `final_model_output.csv` (conditional on `invLink`) | | `model_summary.csv`: stale SAS tie constant |
| ST3 metrics | `decile_analysis.csv`, `threshold_analysis.csv`, `calibration_plot.csv`, `ks_statistic.csv` (restated for version 2.1) | | `validation_summary.csv`, `model_performance_metrics.csv`: stale SAS tie constant, and a second obstacle (below) |
| ST4 predict | `kaggle_submission.csv`, `test_predictions.csv` (under the `input_best32` hypothesis) | | |

Eleven of fourteen files are proved equal to SAS, none is disproved, three are open.
`ks_statistic.csv` moved from open to proved.

### Counts from `get_status` (end of round)

| | |
|---|---|
| Items | 318 |
| Statements formalized | 300 |
| Statements to write | 0 |
| Proofs to write | 10 (the ten open contracts) |
| Waiting | 0 |
| Flagged false | 18 (the 14 disproved here, and 4 untouched: `thm:fe_run_04_imputed_I4`, `thm:metrics_run_02_ks_I7`, `thm:predict_run_04_imputed_S31`, `thm:train_run_01_fit_frame_C4`) |
| `verification_approved` | false |

## Blocker: the SAS tie constant in the blueprint is the old one

- `check_decl Sas.rocTops`, from each of the ten items, shows
  `if 10536712127723509e-24 < top - p`, the old decimal 1.0536712127723509e-8.
- Python `def:_TIE_EPS` is 3184525836262887 / 2^78 (about 1.05367121277235103e-8), as rulebook
  R25 now says. The two are different real numbers.
- A gap strictly between them separates the two sides. Witness against the definitions as they
  stand: `default_flag` = 1, 0 and `pd_logistic` = 3184525836262887 / 2^78, 0. The SAS definition
  gives Area 1 (not tied; evaluated at `Float`), the Python definition 0.5 (tied; by reading).
  Real SAS ties at this gap (experiment X08).
- A disproof on that witness would be an artefact of the stale item, so none was made. The ten
  contracts are stated with their round 2 Lean and left unproved, not negated: H12, S12(a),
  S12(b), S14(a) roc, S14(a) auc, S14(b) roc, S14(b) auc, ST2 `model_summary.csv`, ST3
  `validation_summary.csv`, ST3 `model_performance_metrics.csv`.
- Apart from the constant the two sides read the same: strict comparison of `top - p`, anchored
  at the group's top, scanning from the largest value down. This is by reading, not proved.

What correcting the constant would and would not settle (by reading):

- H12, the four S14 items and ST2 `model_summary.csv`: the constant is the only obstacle seen.
- S12(a): H12 assumes `default_flag` is 0 or 1; S12(a) gives presence and both outcomes only.
  Whether the precondition supplies the rest was not checked.
- S12(b): it also covers missing values and a single outcome, which H12 does not address.
- ST3 `validation_summary.csv` and `model_performance_metrics.csv`: a second obstacle. Both
  contain the KS table, and their texts are version 2, with no bound on the number of rows.
  `ks_statistic.csv` needed that bound and was restated; section 9 does not list these two as
  restated. With the constant corrected they would still be unprovable as written, for tables of
  10^8 rows or more.

## Step 1: what changed

- **Changed `def:` items.** 21 original definitions changed: `_TIE_EPS`, `_pairs` and its
  precondition, `roc_association` and its precondition (comments only), `association_table` and
  its precondition, `sas_round`, `merge_one_to_one` and its precondition, `fe_run_02/03/05`,
  `predict_run_02/03/05`, `train_run_09/11`, `metrics_run_05_cumulative_lift`,
  `metrics_run_06_psi` and its precondition. Each has a section 9 reason (P1 to P9, the PSI
  floor). Read against the new Python source, each matches. `def:_TWO52` and the helper
  `metrics_run_06_psi_shares` no longer exist (the helper is inlined).
- **`merge_one_to_one_precond` changed in substance.** It no longer says a Null-kind column is
  never padded; it requires distinct column names per frame and excludes some kind pairs for
  same-named columns. The comments in the preconditions of metrics steps 08 and 09 still describe
  the old condition.
- **22 definitions were unformalized at the start of the round** (the four stage definitions and
  their preconditions, and steps that depend on changed helpers). They were formalized again
  during the round, not by me. Their Lean is identical to the pre-change Lean; they had lost it
  only through their dependencies.
- **Stale texts on translator items** (not fixed): the item texts of `def:run_py_py`,
  `def:metrics_run_06_psi`, `def:metrics_run_05_cumulative_lift`, `def:train_run_09_confusion_train`
  and `def:train_run_11_confusion_valid` still show the old Python source; some line-number
  comments are old. Their Lean follows the new code.
- **`eval_decl` fails on `def:run_py_py`** and on any carrier fixed at `Float`; it works on a
  carrier generic in the number type.
- **Contracts that lost their proof:** all 85 below, except the restated ones, which were
  rewritten on purpose.

## Verdicts section 9 expected to change

| Contracts | Expected | Result |
|---|---|---|
| S3(b) | holds | **proved** |
| S2(b) | holds | **still disproved**, by row order only (statement form) |
| S24(b) | holds | **still disproved**, by row order only (statement form) |
| S25(b) | holds | **still disproved**, on a text `MonthlyIncome` column (statement form) |
| S5(b), S27(b) | hold | **proved** |
| S31 step 05 | holds | **proved** |
| I8 | holds apart from `default_flag` and the medians | disproved, and `default_flag` is the only difference left: as expected |
| I3 on the feature-engineering step | fails | **disproved**, as expected |
| S8(b), S10(b) | hold | **proved** |
| S18(b) | holds | **still disproved**, through a gap in the `best8` link; the running-sum difference in `cum_defaults` is gone |
| H8 | holds | **proved** |
| H10 | holds | **still disproved**, on a same-named Int64 and String column; the round 2 witness now agrees |
| H12, S12, S14 | hold | **open** (blocker) |
| ST2 `model_summary.csv`, ST3 `validation_summary.csv`, ST3 `model_performance_metrics.csv` | hold | **open** (blocker) |

The five that were expected to hold and are still disproved:

- **S2(b) and S24(b).** The round 1 statement is an equality of tables as ordered lists. Python
  lists the medians in order of first appearance, SAS in ascending key order. Witness for S2(b):
  ages 45 then 25, incomes 1 and 1: Python rows (3, 1), (1, 1); SAS rows (1, 1), (3, 1). Section 5
  says S2 and S24 compare these tables as sets, and part (a), restated in round 2 as sets, is
  proved without using the age condition. So the contract as version 2.1 words it holds; the
  round 1 statement of part (b) is stronger than the contract. The order has no effect
  downstream: the table is only joined on its key.
- **S25(b).** The round 1 statement assumes only the precondition, which accepts a
  `MonthlyIncome` column of any kind. Witness: a String column holding "x": Python gives
  `MonthlyIncome_missing` = 0, SAS 1. Version 2.1 quantifies over well-formed frames, where the
  column is Float64; on those the equality is proved inside the S25(a) proof without the age
  condition. Again the statement is stronger than the contract.
- **S18(b).** The `best8` link speaks of present values only. Witness: a `sas_best` that returns
  "1" for a missing value, `default_flag` missing on the single row, `defaults` = 1 in
  `decile_analysis`: SAS totals missing, so `cum_capture_rate` missing; Python reads 1. The real
  `sas_best` returns an empty text for a missing value, so no run reaches it. A second difference
  remains by reading, not proved: `cum_count` is a plain running sum
  (`metrics_calculation.py` line 232) and is missing after a missing `total_count`, where SAS
  carries the total on; step 04 never produces a missing `total_count`.
- **H10.** Witness: first frame `v` = Int64 1, 2; second frame `v` = String "a". Python gives the
  text "2" on row 2, the SAS rule the number 2. Real SAS rejects a variable that is both
  character and numeric, and no pipeline call shares a name.

I did not reword or weaken any of the five. Restating S2(b), S24(b) and S25(b) in the version 2.1
form (well-formedness; sets for the medians) would make them provable from the existing proofs;
section 9 says their texts stay, so that is the specification owner's decision.

## Restated contracts (section 9)

Every restated statement was checked by a separate reviewer before its proof; no statement needed
a change. All hold.

| Contract | Items | Result | Notes |
|---|---|---|---|
| S4(a), S4(b) | `thm:fe_run_04_imputed_S4a`, `_S4b` | proved | `def:wf_fe_step04_cleaned` now has `age_group` and `VAR1` present; `def:wf_fe_step04_medians` has `age_group` present and may have no row. Distinct medians keys are not assumed: a repeated key repeats the row on both sides |
| S6(a), S6(b) | `thm:fe_run_06_split_S6a`, `_S6b` | proved | `def:wf_fe_step06` now has `row_id` present |
| S10(a) | `thm:train_run_11_confusion_valid_S10a` | proved | `def:wf_tr_scored` now has `row_id` present and `pred_logistic` 0 or 1; follows from S10(b) |
| S26(a), S26(b) | `thm:predict_run_04_imputed_S26a`, `_S26b` | proved | `def:wf_pr_cleaned`, `def:wf_pr_medians` changed as for S4. "`row_id` present" is read as "`VAR1` present": step 04 itself renames the column |
| S15 KS (a), (b) | `thm:metrics_run_02_ks_S15a_ks`, `_S15b_ks` | proved | Count link with both clauses; the row bound is a separate hypothesis, the shared definitions untouched. Holds with missing values, a class with no rows and ties at the maximum |
| ST3 `ks_statistic.csv` | `thm:run_py_ST3_ks_statistic` | proved | From S15(b) KS |
| F1 on, binning and floor | `thm:metrics_run_06_psi_F1_on_bins` | proved | New floor. No row bound needed, and none assumed |
| F1 on, shares sum to 1 | `thm:metrics_run_06_psi_F1_on_sum` | proved | Needs the validation row bound: the precondition tolerates a gap of 1e-9 |
| I1 on | `thm:metrics_run_06_psi_I1_on` | proved | No row bound needed. `thm:metrics_run_06_psi_I1_on_floor` removed |

Readings to confirm: the `VAR1` present conjunct in the step-04 shape of feature engineering
(the proof does not use it), and leaving the row bound out of `_F1_on_bins` and `_I1_on` (a
stronger statement than the contract).

## Every contract touched

"Same" means the verdict is that of round 2 (or round 1 where the contract stood).

### Feature engineering

| Contract | Item | Result | Change |
|---|---|---|---|
| S2(a) | `thm:fe_run_02_income_medians_S2a` | proved | same; the domain conditions are no longer used |
| S2(b) | `thm:fe_run_02_income_medians_S2b` | disproved | same verdict, new reason |
| S3(a) | `thm:fe_run_03_cleaned_S3a` | proved | same |
| S3(b) | `thm:fe_run_03_cleaned_S3b` | proved | was disproved |
| S4(a), S4(b) | `thm:fe_run_04_imputed_S4a`, `_S4b` | proved | restated; were disproved |
| S5(a) | `thm:fe_run_05_features_S5a` | proved | same |
| S5(b) | `thm:fe_run_05_features_S5b` | proved | was disproved |
| S6(a), S6(b) | `thm:fe_run_06_split_S6a`, `_S6b` | proved | restated; were disproved |
| I3 | `thm:fe_run_05_features_I3` | disproved | was proved; expected |
| I4, capping | `thm:fe_run_05_features_I4` | disproved | same |
| ST1, two files | `thm:run_ST1_model_features_train`, `_validation` | proved | same |
| F3 on, F3 off, F4 | `thm:run_F3_on`, `thm:run_F3_off`, `thm:run_F4` | proved | same |

### Train and helpers

| Contract | Item | Result | Change |
|---|---|---|---|
| H8 | `thm:sas_round_H8` | proved | was disproved |
| H10 | `thm:merge_one_to_one_H10` | disproved | same verdict, new witness |
| H12 | `thm:roc_association_H12` | open | was disproved |
| C2 | `thm:roc_association_C2` | disproved | same |
| S8(a) | `thm:train_run_09_confusion_train_S8a` | proved | same |
| S8(b) | `thm:train_run_09_confusion_train_S8b` | proved | was disproved |
| S10(a) | `thm:train_run_11_confusion_valid_S10a` | proved | restated; was disproved |
| S10(b) | `thm:train_run_11_confusion_valid_S10b` | proved | was disproved |
| S11(a), S11(b) | `thm:train_run_12_risk_scores_S11a`, `_S11b` | proved | same; the probability range is no longer used |
| I5 bands | `thm:train_run_12_risk_scores_I5_bands` | disproved | same |
| I5 grades, range, sharp range | `_I5_grades`, `_I5_range`, `_I5_range_sharp` | proved | same |
| S12(a), S12(b) | `thm:train_run_13_roc_S12a`, `_S12b` | open | were disproved |
| S13 | `thm:train_run_14_final_and_summary_S13` | proved | same |
| ST2, three files | `thm:run_py_py_py_ST2_risk_scores_train`, `_risk_scores_validation`, `_final_model_output` | proved | same |
| ST2 `model_summary.csv` | `thm:run_py_py_py_ST2_model_summary` | open | was disproved |

### Metrics

| Contract | Item | Result | Change |
|---|---|---|---|
| S14, four items | `thm:metrics_run_01_roc_auc_S14a_roc`, `_S14a_auc`, `_S14b_roc`, `_S14b_auc` | open | were disproved |
| S15 KS (a), (b) | `thm:metrics_run_02_ks_S15a_ks`, `_S15b_ks` | proved | restated; were disproved |
| S18(a) | `thm:metrics_run_05_cumulative_lift_S18a` | proved | same |
| S18(b) | `thm:metrics_run_05_cumulative_lift_S18b` | disproved | same verdict, new reason |
| S19(a), S19(b) | `thm:metrics_run_06_psi_S19a`, `_S19b` | proved | same |
| I1 off | `thm:metrics_run_06_psi_I1_off` | disproved | same |
| I1 on | `thm:metrics_run_06_psi_I1_on` | proved | restated; was disproved |
| F1 on, two parts | `thm:metrics_run_06_psi_F1_on_bins`, `_F1_on_sum` | proved | restated; `_sum` was disproved |
| S21(a), S21(b) | `thm:metrics_run_08_validation_summary_S21a`, `_S21b` | proved | same |
| S22(a), S22(b) | `thm:metrics_run_09_model_performance_S22a`, `_S22b` | proved | same |
| F1 frame | `thm:run_py_F1_frame` | proved | same |
| ST3, three files | `thm:run_py_ST3_decile_analysis`, `_threshold_analysis`, `_calibration_plot` | proved | same |
| ST3 `ks_statistic.csv` | `thm:run_py_ST3_ks_statistic` | proved | restated; was open |
| ST3, two summary files | `thm:run_py_ST3_validation_summary`, `_model_performance_metrics` | open | were disproved |

### Predict

| Contract | Item | Result | Change |
|---|---|---|---|
| S24(a) | `thm:predict_run_02_medians_S24a` | proved | same; the age condition is no longer used |
| S24(b) | `thm:predict_run_02_medians_S24b` | disproved | same verdict, new reason |
| S25(a) | `thm:predict_run_03_cleaned_S25a` | proved | same |
| S25(b) | `thm:predict_run_03_cleaned_S25b` | disproved | same verdict, new reason |
| S26(a), S26(b) | `thm:predict_run_04_imputed_S26a`, `_S26b` | proved | restated; were disproved |
| S27(a) | `thm:predict_run_05_features_S27a` | proved | same |
| S27(b) | `thm:predict_run_05_features_S27b` | proved | was disproved |
| S29 | `thm:predict_run_07_predictions_S29` | proved | same |
| S31 steps 02, 03 | `thm:predict_run_02_medians_S31`, `thm:predict_run_03_cleaned_S31` | proved | same |
| S31 step 05, two items | `thm:predict_run_05_features_S31`, `_S31_rest` | proved | `_S31` was disproved |
| F2 on, I2 on | `thm:predict_run_02_medians_F2_on`, `_I2_on` | proved | same |
| I2 off | `thm:predict_run_02_medians_I2_off` | disproved | same; the witness no longer has a missing age |
| I3 | `thm:predict_run_05_features_I3` | disproved | same |
| I6 | `thm:predict_run_07_predictions_I6` | disproved | same |
| I8 | `thm:predict_run_05_features_I8` | disproved | same verdict; only `default_flag` differs now |
| ST4, two files | `thm:run_py_py_ST4_kaggle_submission`, `_test_predictions` | proved | same |
| F2 frame | `thm:run_py_py_F2_frame` | proved | same |

Contracts that still had their proof were not touched.

## Hypotheses can be met (rule 4)

| Contracts | How one input meeting all hypotheses is shown |
|---|---|
| The step contracts and helpers proved in round 3, except those below | A lemma at the reals in the proof file (or in the file of the (b) part, or of a negation of the same unit, named in the proof text) |
| S15 KS (a), (b) | A lemma at the reals, with concrete `sas_best` and `parse_float` meeting the count link |
| S21(a), S22(a) | Domain conditions by a lemma at the reals; the precondition by evaluation at `Float` |
| F2 on, I2 on | By description only: the frames of the I2 off witness, flag on. Not evaluated |
| S19(a) | "`pd_logistic` present" is true of the named frames but not proved as a lemma |
| ST1, F3, F4; ST2 (three files); ST3 (four files), F1 frame, S18(a); ST4 (two files), F2 frame | Evaluation at `Float` of every hypothesis conjunct, and of the conclusions, on one concrete input per stage |

Limits of the `Float` evaluations:

- They are evaluations, not proofs at the reals.
- Each check is a Boolean transcription of the hypothesis written by hand, because the
  definitions are propositions and cannot be evaluated directly. The transcriptions were checked
  by reading.
- Links that quantify over every number were checked on samples (metrics), or hold by
  construction of the input (`invLink`, the model link, `today`, `agg`).
- The train stage input uses placeholder linear-algebra and format parameters, and no negative
  control was run on its encoding. The metrics checker was run on bad inputs for the table shape
  only.

## Other notes

- **Definitions of mine that changed:** `def:wf_fe_step04_cleaned`, `def:wf_fe_step04_medians`,
  `def:wf_fe_step06`, `def:wf_tr_scored`, `def:wf_tr_scored_train`, `def:wf_pr_cleaned`,
  `def:wf_pr_medians` (the cell guarantees of version 2.1). The texts of the two `wf_tr`
  definitions are the service's summaries, accurate but short; they were left so as not to clear
  proved contracts. The shared definitions `def:wf_me_score_table` and `def:wf_me_score_frame`
  were not touched.
- **Items added:** the negations of the 14 disproved contracts (re-created by `negate`). **Items
  removed:** `thm:metrics_run_06_psi_I1_on_floor` (as section 9 asks) and the old negations of the
  restated S15 KS and S26 contracts. No `zz` item remains in the blueprint, mine or the
  translator's.
- **Proof edges added:** (a) to (b) for S4, S6, S10, S26, S15 KS; ST1 to S3(b) and S5(b);
  `_S31_rest` to `_S31`; I5 range to I5 sharp range; the I5 bands negation to I5 grades; ST3
  `ks_statistic.csv` to S15(b) KS. One stale edge is left: ST1 train to S5(a).
- **Texts.** The service again replaced contract texts with summaries after acceptance; the
  specification text was restored on every contract. The statement texts of negation items are
  the service's and cannot be edited; the witnesses are in their proof texts. The texts of H8 and
  H10 (round 2 wording, not reworded) end with remarks about `Float` evaluation of the old code,
  and the text of S25(b) says "expected to fail"; these are now out of date.
- **Leftovers in proofs.** Commented-out round 2 lemmas remain in the proof files of ST1, S11(b),
  S13, S29 and two I5 items.
- **Rule breaches and near-breaches.** One subagent wrote a slice of the old Lean dump to
  `/tmp/claude-501/tf.txt` by mistake and deleted it at once. The harness saved several oversized
  tool results holding Lean under the session's `tool-results` folder; they were deleted. Two
  subagents read their own session transcripts with small scripts to recover item texts and
  lemmas; nothing was written to disk. No Lean is saved locally now, and the working tree holds
  only the two report files.
- **Process.** At most four subagents worked against the blueprint at once. A network outage
  stopped three of them once; the server state was checked before they went on, and nothing was
  lost.
