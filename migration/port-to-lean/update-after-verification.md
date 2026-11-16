# Bringing `py-credit-risk-port` in line with the port (scoping, 2026-11-16)

Scoping only. Nothing was changed on the blueprint or in the repository apart from this file.

## 0. How the comparison was made, and its limits

- This role may not run git, so `git log 2ac4039..HEAD -- port/` was not run. The baseline is the
  Python source stored in each blueprint item (`get_items`, field `code`), which is what the
  accepted Lean translates (state of the re-translation after 7927af7). It was compared by reading
  with `port/credit_risk/*.py` as on disk at 15:11 on 2026-11-16.
- `sas_compat.py` was still being committed. `sas_best` and `roc_association` are treated as
  changed whatever their final text (as instructed); line numbers of `sas_compat.py` below may move.
- Old source was read for every code item except `def:run_py_py_py` as a whole (too large; its 15
  steps were read one by one) and steps whose text is contained in the `run` item read. Lean was
  read only for `def:run`, `def:run_precond`, `def:fe_run_01_clean` (+precond),
  `def:predict_run_02_medians_precond`, `def:metrics_run_10_printed_roc`. Precondition changes
  below are therefore estimates from the Python, to be confirmed by the translator of each unit.
- No theorem (`thm:`/`neg:`) or `wf_` item was opened on purpose. One regex `grep` meant for prelude
  names returned the signatures of four theorems (`thm:roc_association_C2`, `_H12`,
  `thm:metrics_run_06_psi_I1_off`, `_I1_on`); see section 5.

## 1. Changed port code and the items that translate it

Status words: CHANGE (statement must be rewritten), RESTORE (Lean unchanged, but a dependency
changes, so the item is cleared and must be resubmitted), RANGE (only the source line range or a
docstring moved), NEW (no item yet), REMOVE (source no longer exists).

### 1.1 `sas_compat.py`

| Port (current lines) | Item | Status | Why |
|---|---|---|---|
| `_SE_EPS` :874 | none | NEW | second tie tolerance, `1000 * 2.0**-53`, used for the standard-error components |
| `_SQRTBIG` :878 | none | NEW | divisor for a class of one observation |
| `_groups` :892-903 | none | NEW | the grouping loop was inline in `_pairs`; now a function called twice |
| `_pairs` :906-930 | `def:_pairs` | CHANGE | conc/tied from the `_TIE_EPS` groups (as before); `v10`, `v01` now from a second grouping with `_SE_EPS` |
| `_pairs` | `def:_pairs_precond` | review | probably unchanged |
| `roc_association` :937-993 | `def:roc_association` | CHANGE | standard error: `math.fsum` of squared deviations around the Area, divided by `n-1` or `_SQRTBIG`, then by `n`; computed whenever the Area exists (was: only with two or more in each class, `np.var(ddof=1)`); limits clamped with `max(…, 0.0)` / `min(…, 1.0)` |
| `roc_association` | `def:roc_association_precond` | CHANGE | follows the new formula (`fsum`, no `np.var`) |
| `association_table` :1010-1032 | `def:association_table` | RESTORE | text unchanged; depends on `def:_pairs` |
| `proc_rank_apply_groups` | `def:proc_rank_apply_groups`, `def:proc_rank_apply_groups_precond` | REMOVE | function deleted from the port (only caller was the `fix_psi_bins` branch) |
| `sas_round` :186-195 | `def:sas_round` | RANGE | text unchanged; no caller left in the package (item stays, loses its four consumers among the code items) |
| `le`, `ge`, `eq` | `def:le`, `def:ge`, `def:eq` | RANGE | docstring only |
| `sas_best` :391, `sas_best12` :426, `input_best32` :235, `proc_import_csv` :557 | none (out of scope, explicit parameters) | parameter | `sas_best` stays the parameter of `def:_into_float` (item text unchanged; the lookup tables of the harness must be regenerated). `sas_best12` becomes a NEW explicit parameter of the two step-01 units (1.2, 1.3). `sas_best` at width 32 is reached only through the CSV writer's `best32.` format, which is not part of any result |
| `sas_round_scalar` :198 | none | not in scope | new function, no caller |
| all other in-scope helpers | their items | RANGE | text identical; every line number after :46 moved |

### 1.2 `feature_engineering.py` (`run` is :19-380)

| Port (current lines) | Item | Status | Why |
|---|---|---|---|
| signature :19-24 | `def:run`, `def:run_precond` | CHANGE | `fix_income_truncation`, `export_train_medians` removed |
| removal of earlier results :28-30 | none | NEW | three file names unlinked first |
| import may fail :35-39 | (in `def:run`) | CHANGE | `credit_raw` is `None` on a failed import; always `guessingrows=None` |
| input check and stop :43-128 | none | NEW | `columns_ok`, `bad_rows`, `duplicate_ids`, `known_incomes`; case-blind renaming of the 12 columns; text columns read through `input_best32` after `strip_chars`/`len_chars <= 32`; `ValueError` and nothing exported |
| step 01 :138-152 | `def:fe_run_01_clean`, `_precond` | CHANGE | BEST12 round trip: a column imported as numeric goes through `map_elements(sas_best12)` before `input_best32` |
| step 02 :157-173 | `def:fe_run_02_income_medians` (+precond) | RANGE | text unchanged |
| medians of all groups :179-186 | none | NEW | five-row frame left-joined with the medians, plus `overall_median_income` on every row |
| step 03 :189-204 | `def:fe_run_03_cleaned` (+precond) | RANGE | unchanged |
| step 04 :208-229 | `def:fe_run_04_imputed`, `_precond` | CHANGE | joins `income_medians_all`; `coalesce(median_income, overall_median_income)` |
| step 05 :234-336 | `def:fe_run_05_features`, `_precond` | CHANGE | `total_risk_flags` over eight flags, no `.alias`; `age_income_interaction` now a `when`; `utilization_debt_interaction` a plain product (no `div`). `full` now concerns an 8-operand `sum_horizontal` (the recorded limit is "1 to 8 operands match") |
| step 06 :342-350 | `def:fe_run_06_split` (+precond) | RANGE | unchanged |
| writes :360-373 | (in `def:run`) | CHANGE | `income_medians.csv` always written, first, from `income_medians_all` (was: optional, sorted `income_medians`) |

### 1.3 `predict.py` (`run` is :17-491)

| Port (current lines) | Item | Status | Why |
|---|---|---|---|
| signature :17-23 | `def:run_py_py`, `def:run_py_py_precond` | CHANGE | `fix_train_medians`, `medians` removed; `income_medians` required |
| removal :27-28, stop when a result of the step before is absent :31-37 | none | NEW | |
| header probe and import :42-79 | (parameter of `def:run_py_py`) | CHANGE | a header-only test file is imported from a made-up copy and `.clear()`ed: a frame with columns and no row; failed import gives `None` |
| input check and stop :82-182 | none | NEW | as 1.2 but: duplicate names become `VARn`; `select` of the first column of each name; outcome checked only when stated; no known-income count; records `age_name` |
| step 01 :192-206 | `def:predict_run_01_clean`, `_precond` | CHANGE | BEST12 round trip |
| step 02 :211-222 | `def:predict_run_02_medians`, `_precond` | CHANGE (rewrite) | old source gone (test-set medians, the `fix_train_medians` branch and its two raises). New: the imported medians table with a case-blind rename of three columns |
| step 03 :228-241 | `def:predict_run_03_cleaned` (+precond) | RANGE | unchanged |
| step 04 :247-271 | `def:predict_run_04_imputed`, `_precond` | CHANGE | join on `age_group` cast to Float64 against the imported key; `coalesce` |
| step 05 :277-372 | `def:predict_run_05_features`, `_precond` | CHANGE | same three changes as 1.2 step 05 |
| step 06 :376-394 | `def:predict_run_06_score` (+precond) | RANGE | unchanged |
| step 07 :398-443 | `def:predict_run_07_predictions`, `_precond` | CHANGE | score not rounded (`sas_round` gone); grade cut on `pd_logistic` with `lt`/`le`, null graded F first |
| step 08 :446-478 | `def:predict_run_08_outputs` | CHANGE | `test_predictions_full` renames `age` to `age_name` |

### 1.4 `metrics_calculation.py` (`run` is :81-539)

| Port (current lines) | Item | Status | Why |
|---|---|---|---|
| signature :81 | `def:run_py`, `def:run_py_precond` | CHANGE | `fix_psi_bins` removed |
| removal :85-93, stop :96-102 | none | NEW | |
| step 01 :114-152 | `def:metrics_run_01_roc_auc`, `_precond` | CHANGE | `auc_summary` no longer derived from `roc_stats`: exact pairwise AUC from `auc_pairs` (group by probability, running sums), `head(min(height, 1))` |
| step 02 :157-196 | `def:metrics_run_02_ks`, `_precond` | CHANGE | `ks_value` only on the last row of each run of equal probabilities (`shift(-1)`, `ne_missing`, `int_range`); `ks_statistic` is one row (`sql_max`, `sql_min`) |
| step 03 :201-210 | `def:metrics_run_03_thresholds` (+precond) | RANGE | unchanged |
| step 04 :216-283 | `def:metrics_run_04_deciles`, `_precond` | CHANGE | `decile_list` (1..10) left-joined with the grouped data; four `fill_null` |
| step 05 :290-321 | `def:metrics_run_05_cumulative_lift`, `_precond` | CHANGE | `gt` guards, 0.0 with no defaulter, `cum_lift` missing while `cum_count` is 0 |
| step 06 :328-401 | `def:metrics_run_06_psi`, `_precond` | CHANGE (rewrite) | bins from nine nearest-rank cuts of the training `credit_risk_score` (was PROC RANK of `pd_logistic`); both sets in the training bins; ten bins always; floor `0.5 / psi_rows`; `sas_max`, `div`; the flag and both old branches are gone |
| steps 07, 08, 09 :407-485 | their items | RANGE | unchanged (format maps changed, not part of the result) |
| step 10 :508-520 | `def:metrics_run_10_printed_roc` (+precond) | RANGE | frame construction unchanged |
| conditional write :522-523 | (in `def:run_py`) | CHANGE | `printed_roc_metrics.csv` written only when the Area is present |
| `_into_float`, `confusion_metrics` | their items | RANGE | unchanged |

### 1.5 `train.py` (`run` is :20-814)

| Port (current lines) | Item | Status | Why |
|---|---|---|---|
| removal :26-33, stop :36-42 | none | NEW | |
| step 12 :584-673 | `def:train_run_12_risk_scores`, `_precond` | CHANGE | score not rounded; grade on `pd_logistic` (as predict step 07), twice |
| step 13 :681-690 | `def:train_run_13_roc`, `_precond` | RESTORE | depends on `def:roc_association` |
| step 05 :279-312 | `def:train_run_05_association` (+precond) | RESTORE | depends on `def:association_table` |
| `run` | `def:run_py_py_py`, `def:run_py_py_py_precond` | CHANGE | removal and stop; dependencies `def:sas_round` dropped |
| steps 01-04, 06-11, 14, 15 | their items | RANGE | text identical |

### 1.6 Totals

- CHANGE: 40 items (3 in `sas_compat`, 8 feature engineering, 13 predict, 12 metrics, 4 train).
- NEW: 9 items if kept as separate units: `_SE_EPS`, `_SQRTBIG`, `_groups`; feature-engineering
  input check (+precond) and medians-of-all-groups (+precond); predict input check (+precond).
  Removal of earlier files, the stop on a missing input and the conditional write live in the four
  `run` items.
- REMOVE: 2 items (`def:proc_rank_apply_groups`, its precondition), and inside changed items the
  parameters `fix_income_truncation`, `export_train_medians`, `fix_train_medians`, `medians`,
  `fix_psi_bins`.
- RESTORE: 5 items (`def:association_table`, `def:train_run_05_association`,
  `def:train_run_13_roc` and the preconditions that follow them).
- RANGE: every other code item (source ranges in four files and in `sas_compat.py` moved).

## 2. What each change clears (`get_graph`, consumers)

No item has a proof consumer among the changed definitions; all edges below are statement edges.
Theorem states: 118 `TheoremProved`, 13 `TheoremStated` (the 13 flagged); 13 `neg:` all proved.

| Changed item | Consumers (theorems and negations) |
|---|---|
| `def:_pairs` | `def:association_table`, `def:roc_association`, `def:roc_association_precond` |
| `def:roc_association` (+precond) | `def:metrics_run_01_roc_auc` (+precond), `def:train_run_13_roc` (+precond), `def:run_py_py_py`; `thm:roc_association_C2`, `thm:roc_association_H12`, `neg:roc_association_C2_neg` |
| `def:train_run_13_roc` | `thm:train_run_13_roc_S12a`, `_S12b` |
| `def:run` (+precond) | `thm:run_F3_off`, `run_F3_on`, `run_F4`, `run_ST1_model_features_train`, `run_ST1_model_features_validation`, `run_W1` |
| `def:fe_run_01_clean` (+precond) | `thm:fe_run_01_clean_S1a`, `_S1b`, `thm:predict_run_01_clean_S31`, `thm:predict_run_05_features_I8` (+neg), `thm:run_F3_on` |
| `def:fe_run_04_imputed` (+precond) | `thm:fe_run_04_imputed_I4` (+neg), `_S4a`, `_S4b`, `thm:predict_run_04_imputed_S31` (+neg), `thm:predict_run_05_features_I8` (+neg) |
| `def:fe_run_05_features` (+precond) | `thm:fe_run_05_features_I3` (+neg), `_I4` (+neg), `_S5a`, `_S5b`, `thm:predict_run_05_features_I8` (+neg), `_S31`, `_S31_rest` |
| `def:run_py_py` (+precond) | `thm:run_py_py_F2_frame`, `run_py_py_ST4_kaggle_submission`, `run_py_py_ST4_test_predictions`, `run_py_py_W4` |
| `def:predict_run_01_clean` (+precond) | `thm:predict_run_01_clean_S23`, `_S23a`, `_S31`, `thm:predict_run_05_features_I8` (+neg), `thm:run_py_py_F2_frame` |
| `def:predict_run_02_medians` (+precond) | `thm:predict_run_02_medians_F2_on`, `_I2_off` (+neg), `_I2_on`, `_S24a`, `_S24b`, `_S31`, `thm:predict_run_05_features_I8` (+neg) |
| `def:predict_run_04_imputed` (+precond) | `thm:predict_run_04_imputed_S26a`, `_S26b`, `_S31` (+neg), `thm:predict_run_05_features_I8` (+neg) |
| `def:predict_run_05_features` (+precond) | `thm:predict_run_05_features_I3` (+neg), `_I8` (+neg), `_S27a`, `_S27b`, `_S31`, `_S31_rest` |
| `def:predict_run_07_predictions` (+precond) | `thm:predict_run_07_predictions_I6` (+neg), `_S29` |
| `def:predict_run_08_outputs` | `thm:predict_run_08_outputs_S30` |
| `def:run_py` (+precond) | `thm:run_py_F1_frame`, `run_py_ST3_calibration_plot`, `_decile_analysis`, `_ks_statistic`, `_model_performance_metrics`, `_threshold_analysis`, `_validation_summary`, `run_py_W3` |
| `def:metrics_run_01_roc_auc` (+precond) | `thm:metrics_run_01_roc_auc_S14a_auc`, `_S14a_roc`, `_S14b_auc`, `_S14b_roc`, `thm:metrics_run_08_validation_summary_S21a`, `thm:metrics_run_09_model_performance_S22a` |
| `def:metrics_run_02_ks` (+precond) | `thm:metrics_run_02_ks_I7` (+neg), `_S15a_ks`, `_S15a_sorted`, `_S15b_ks`, `_S15b_sorted`, `_S21a`, `_S22a` |
| `def:metrics_run_04_deciles` (+precond) | `thm:metrics_run_04_deciles_S17a`, `_S17b`, `thm:metrics_run_05_cumulative_lift_S18a` |
| `def:metrics_run_05_cumulative_lift` (+precond) | `thm:metrics_run_05_cumulative_lift_S18a`, `_S18b` |
| `def:metrics_run_06_psi` (+precond) | `thm:metrics_run_06_psi_F1_on_bins`, `_F1_on_sum`, `_I1_off` (+neg), `_I1_on`, `_S19a`, `_S19b`, `_S21a`, `_S22a` |
| `def:run_py_py_py` (+precond) | `thm:run_py_py_py_ST2_final_model_output`, `_ST2_model_summary`, `_ST2_risk_scores_train`, `_ST2_risk_scores_validation`, `run_py_py_py_W2` |
| `def:train_run_12_risk_scores` (+precond) | `thm:train_run_12_risk_scores_I5_bands` (+neg), `_I5_grades`, `_I5_range`, `_I5_range_sharp`, `_S11a`, `_S11b` |

Cleared in all: 84 of the 131 theorems and 12 of the 13 negations (all but
`neg:train_run_01_fit_frame_C4_neg`). Two more (`thm:fe_run_02_income_medians_S2a`, `_S2b`) clear
only if `def:fe_run_02_income_medians` is touched; the plan leaves it alone and adds the new block
as its own item. Proofs that cite a cleared theorem clear too (seen: `thm:run_ST1_model_features_train`
cites `S1b`, `S2a`, `S3b`, `S5b`).

Not cleared: the helper theorems except the two on `roc_association`; `fe_run_03` (`S3a`, `S3b`),
`fe_run_06` (`S6a`, `S6b`), `predict_run_03` (`S25a`, `S25b`, `S31`), `predict_run_06` (`C3`, `S28`),
`metrics_run_03` (`S16a`, `S16b`), `metrics_run_07` (`S20a`, `S20b`), `S21b`, `S22b`, and train
steps 01, 04, 09, 10, 11, 14.

Third-team items whose subject no longer exists in the port (theirs to remove or restate; judged
from the item ids and the removed parameters, not from their text): `thm:run_F3_on`, `run_F3_off`,
`run_F4`; `thm:predict_run_02_medians_F2_on`, `_I2_on`, `_I2_off` (+neg); `thm:run_py_py_F2_frame`;
`thm:run_py_F1_frame`; `thm:metrics_run_06_psi_F1_on_bins`, `_F1_on_sum`, `_I1_on`, `_I1_off` (+neg);
`def:wf_pr_medians_supplied`. The 28 `def:wf_*` items depend only on `def:ExprOrNum` and are not
cleared, but several describe frames whose columns change (`wf_pr_medians`, `wf_me_psi_summary`,
`wf_me_ks_statistic`, `wf_me_decile_analysis`, `wf_tr_risk`, `wf_pr_predictions`).

`def:ExprOrNum` (the polars prelude) must not be edited: every item depends on it. New polars
operations go in as local helpers of the unit that needs them (rulebook amendment F1/F3).

## 3. Tasks

T0 is done (2026-11-16). The four questions below were decided by the lead: (1) `Option`, `none` =
stopped; (2) yes, `Option` parameters; (3) foundation unchanged, the predict import parameter
delivers column names and rows separately, empty metrics scores stay excluded by precondition;
(4) yes. The rules are RULEBOOK v5 §2.7 (G1-G20), with evidence in `experiments/e07_batch7.py`;
carriers `def:zz_carrier_s/_f/_p/_m/_t` are in the blueprint; the brief for translators is
`prompts/common.md` (last block). New unit names: `def:fe_run_00_input_check`,
`def:predict_run_00_input_check`, `def:_groups`, `def:_SE_EPS`, `def:_SQRTBIG`; the medians of all
groups block is `def:fe_run_02b_medians_all`. One point awaits confirmation: DEV-013, the predict
result as triples `(file, column names, table)`.

Questions as put before T0:

1. Shape of a `run` result when the run stops. Now `List (String × Tabular.Table α)`. Proposal:
   keep the type, a stopped run returns `[]`, and each `run` item states in its text the names it
   removes first. Alternative: `Option (List …)`. The choice changes every `run` theorem's statement.
2. Missing inputs: a failed import and an absent file become `Option` parameters
   (`cs_training : Option (Table α)`, etc.) so that the stop is inside the function, not excluded
   by the precondition.
3. Frames with columns and no row. The port now defines them (header-only test file, empty
   training scores, `auc_pairs` with no row). `Tabular.Table α` cannot carry one (`Pl.ofTable [] = []`,
   recorded limit B2). Either they stay excluded by precondition, or the foundation changes; the
   foundation is not this role's to change.
4. Whether the header probe of predict (:42-63, raw bytes) is part of the import parameter
   (proposal: yes, it is CSV reading) or a unit.

| Task | Unit(s) | Depends on | Evaluate against (real port run) |
|---|---|---|---|
| T0 | Decisions above; rulebook batch 7 with evidence for the library calls new to the Lean (`str.strip_chars`, `len_chars`, `to_uppercase`, `is_in`, `n_unique`, `drop_nulls`, `floor`/`ceil`, `coalesce`, `shift`, `ne_missing`, `int_range`, `head`, `clear`, join with a cast `left_on`, `fill_null` on Int64, `map_elements`, `Series.item` with a negative index, `math.fsum`); check which the prelude already has; re-add the carrier item | none | experiments only |
| T1 | `_SE_EPS`, `_SQRTBIG`, `_groups` (new); `def:_pairs`, `def:roc_association` (+preconds); restore `def:association_table` | T0 | `sas_compat.roc_association` on `(default_flag, pd_logistic)` of `judge/scenarios/fix_Q26_small`, `fix_Q26_ties`, `fix_Q26_nodefaulter`, `fix_Q23_alldefaulters`, `fix_Q23_tie`, `real_metrics`, `edge_metrics_a/b/c` |
| T2 | feature-engineering input check (new, :28-128) | T0 | `feature_engineering.run` on `legacy/data/cs-training.csv` and on `fix2/train_*`, `fix_G34/train_*`, `fix_Q27`, `fix_Q27_textid/train_text_id`, `fix_round5/train_*` |
| T3 | `def:fe_run_01_clean` (+precond) | T0 | `feature_engineering.run`, step slice, on real data and `fix2/train_income_long`, `fix2/q13_median_width`, `fix_round5/train_age_exponent` |
| T4 | medians of all groups (new, :179-186); `def:fe_run_04_imputed` (+precond) | T0 | same run on real data, `fix_Q1`, `fix_Q14`, `fix2/train_no_known_income`, `edge_predict/cs-training.csv` |
| T5 | `def:fe_run_05_features` (+precond) | T0 | same run on real data, `fix_Q7`, `fix_Q9`, `fix_G34/income_zero` |
| T6 | `def:run`, `def:run_precond` | T2, T3, T4, T5 | whole stage: `legacy/data/cs-training.csv` with `inputs/split_ids.csv`; one stopping scenario per counter |
| T7 | predict input check (new unit `def:predict_run_00_input_check`, :82-182; the removal :27-28, the stop :31-37 and the probe and import :42-79 are in `def:run_py_py`, T11) | T0 | `predict.run` on `fix_Q27_emptytest/*`, `fix_Q27_emptytest_badheader/*`, `fix_Q27_column_order/*`, `fix_round5/test_*`, `fix2/test_*`, `fix_G34/test_*`, `fix_Q27_test` |
| T8 | `def:predict_run_01_clean`, `def:predict_run_02_medians`, `def:predict_run_04_imputed` (+preconds) | T0 | `predict.run` on `legacy/data/cs-test.csv` with `income_medians.csv` and `model.json` from real runs of the two stages before; `fix_Q13`, `fix_Q14`, `fix_Q1`, `fix2/q13_median_width`, `edge_predict` |
| T9 | `def:predict_run_05_features` (+precond) | T0 (same text as T5: one translator can take both) | `predict.run` on real data, `fix_Q7`, `fix_Q9`, `fix2/q14_negative_real` |
| T10 | `def:predict_run_07_predictions` (+precond), `def:predict_run_08_outputs` | T0 | `predict.run` on real data, `fix_round5/test_header_age_upper`, `test_header_all_upper` |
| T11 | `def:run_py_py`, `def:run_py_py_precond` | T7, T8, T9, T10 | whole stage on real data; stop with `income_medians.csv` or `model_coefficients.csv` absent |
| T12 | `def:metrics_run_01_roc_auc` (+precond) | T1 | `metrics_calculation.run` on `real_metrics`, `fix_Q26_*`, `fix_Q23_nodefaulter`, `fix_Q23_alldefaulters` |
| T13 | `def:metrics_run_02_ks` (+precond) | T0 | same stage on `real_metrics`, `fix_Q23_tie`, `fix_Q23_near`, `fix_Q24`, `edge_metrics_a/b/c` |
| T14 | `def:metrics_run_04_deciles`, `def:metrics_run_05_cumulative_lift` (+preconds) | T0 | same stage on `real_metrics`, `fix_Q23_nodefaulter`, `fix_G43`, `edge_metrics_a/b/c` |
| T15 | `def:metrics_run_06_psi` (+precond); then remove `def:proc_rank_apply_groups` (+precond) | T0 | same stage on `real_metrics`, `fix_Q25`, `fix2/q25_tiny_psi`, `fix_G43`, `edge_metrics_a/b/c` |
| T16 | `def:run_py`, `def:run_py_precond` | T12-T15 | whole stage on `real_metrics` and each scenario above; stop with a score file absent; no `printed_roc_metrics.csv` with one response level |
| T17 | `def:train_run_12_risk_scores` (+precond) | T0 (same text as T10's grade chain) | `train.run` on the feature files of a real feature-engineering run, slice of step 12; a null `pd_logistic` row |
| T18 | `def:run_py_py_py`, `def:run_py_py_py_precond`; restore `def:train_run_13_roc`, `def:train_run_05_association` (+preconds) | T1, T17 | whole stage on the real feature files; stop with a feature file absent |
| T19 | Source ranges of all code items, manifest, docstrings of `le`/`ge`/`eq` | none (any time) | none |
| T20 | Harness: scripts of section 4, lookup tables for `sas_best` (width 8) and `sas_best12`, receipts, end-to-end run of the four stages | all | all four stages on `legacy/data` |

Tasks that can run at once after T0: T1, T2, T3, T4, T5, T7, T8, T9, T10, T13, T14, T15, T17, T19
(the server limit in the brief is four agents at a time). Then T12; then T6, T11, T16, T18; then T20.

## 4. Scripts under `migration/port-to-lean/` that call removed keywords

| File | Line | Removed keyword or function |
|---|---|---|
| `experiments/inv02_stage_edges.py` | 25 | `export_train_medians=True` |
| `experiments/inv02_stage_edges.py` | 34, 35, 36 | `fix_train_medians=True` (36 also `medians=`) |
| `experiments/inv02_stage_edges.py` | 41, 55 | `fix_psi_bins=fix` |
| `experiments/inv01_unit_edges.py` | 37, 39 | `sc.proc_rank_apply_groups` |
| `experiments/e05_frames_numpy.py` | 68 | `sc.proc_rank_apply_groups` |
| `diffeval/units/b3_gen.py` | 103, 112, 127, 132 | `proc_rank_apply_groups` (Python calls and generated Lean terms) |
| `diffeval/units/b6_gen.py` | 107 | `mc.run(…, fix_psi_bins=fix)` |
| `diffeval/units/b7_gen.py` | 94 | `fix_income_truncation=fix, export_train_medians=export` |
| `diffeval/units/b8_gen.py` | 106 | `fix_train_medians=fix, medians=…` |
| `diffeval/units/c7927_gen.py` | 226 | `fix_train_medians=fix, medians=…` |
| `diffeval/units/r3_gen.py` | 479 | `"fix_psi_bins": fix` in the environment of the step slice (and 484-505 the branch on it) |
| `diffeval/units/runs_r2_gen.py` | 215 | `export_train_medians=True` |
| `diffeval/units/runs_r2_gen.py` | 271 | `fix_income_truncation=fix, export_train_medians=ex` |
| `diffeval/units/runs_r2_gen.py` | 363-364, 432 | `fix_train_medians=fx, medians=…` |
| `diffeval/units/runs_r2_gen.py` | 502 | `mc.run(…, fix_psi_bins=fix)` |

`sas_round` is still in `sas_compat.py`, so the scripts that call it still run. `brief.md:88` and
`RULEBOOK.md:240` describe the removed flags and need an amendment.

## 5. State of the blueprint

`get_status` (2026-11-16): 317 items; 304 statements formalised; nothing to write, nothing waiting;
`verification_approved` true; 13 flagged:
`thm:fe_run_04_imputed_I4`, `thm:fe_run_05_features_I3`, `thm:fe_run_05_features_I4`,
`thm:metrics_run_02_ks_I7`, `thm:metrics_run_06_psi_I1_off`, `thm:predict_run_02_medians_I2_off`,
`thm:predict_run_04_imputed_S31`, `thm:predict_run_05_features_I3`, `thm:predict_run_05_features_I8`,
`thm:predict_run_07_predictions_I6`, `thm:roc_association_C2`, `thm:train_run_01_fit_frame_C4`,
`thm:train_run_12_risk_scores_I5_bands`.

By kind (from the item list and `get_items` states): 90 code items and 55 preconditions, all
formalised; 28 `def:wf_*`; 131 theorems, 118 proved and 13 stated (the flagged ones); 13 negations,
all proved. Trust layers: Judging.

Profile: the foundation is visible (`grep` finds `Tabular.RealLike`). `grep` results carry no
origin, and `get_status` / `open_blueprint` do not list the profile, so which other blueprints are
in it cannot be read off directly. The four theorem signatures returned by accident use
`Sas.num`, `Sas.rocArea`, `Sas.rocObs` and name `roc_stats_precond`, `roc_train_precond`,
`roc_valid_precond`: declarations that are not items of this blueprint. So the profile shows at
least one blueprint with a `Sas` namespace. Whether that is 3f5df696-7c80-45cc-809f-b2881714663d
was not checked, since checking means opening its items.

## 6. Not determined

- The commit list itself (no git in this role); see section 0.
- Whether `update_item_source` on an unchanged item clears its dependents (the 7927af7 record
  suggests not).
- Which of the new polars calls the prelude in `def:ExprOrNum` already models.
- The exact new preconditions; and whether `def:_pairs_precond` changes.
- Why `get_status` counts 304 of 317 formalised (the difference equals the 13 flagged theorems or
  the 13 negations; the states do not say which).
- The final text of `sas_best` and `roc_association`.
