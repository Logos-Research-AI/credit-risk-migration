# Change specification for the SAS blueprint, one clearing (2026-11-18)

Status: for the lead's approval. Nothing was changed on any blueprint, no code was changed,
nothing is committed. Author: prover (specification step of the workflow).

This file holds no Lean. Every change is given in words, with the names of the items and of the
declarations it touches; the Lean is written on the server by the SAS translators when the lead
approves. Nothing here was compiled.

Blueprints: SAS `3f5df696-7c80-45cc-809f-b2881714663d` (signed off), port
`5365851c-5549-44b7-9207-4bd4c422031d`. Both read only.

Decisions this file follows (not repeated in the sections): the owner's of 2026-11-18 (no
contract hypothesis; three levels on a one-outcome training part; G2; leverage and variance 0
not assumed; padded text; Q27 restated) and the lead's (form U; Paired 3 filler; Paired 1
unchanged with a helper in T0; C-g 8b, 8c narrow; conjunct 16 of `PyLinks` corrected; one
clearing per blueprint).

## 0. What I read, and what I did not

Read in full: the two drafts (`sas-no-fit-draft-2026-11-18.md`,
`saslinks-padded-text-draft-2026-11-18.md`), observation H15, RULEBOOK of `legacy-to-lean` R39 to
R46 and sections 3, 4, 7, `out-of-scope.tsv` and `open-items.md` where they name the fit,
`legacy/metrics_calculation.sas` (all), `legacy/train.sas` 40-200, the x27 runner and its
`X27 C60` and `X27 E60` lines, the files and the error lines of the logs of
`judge/runs/x27_C60_full` and `x27_E60_full`, the files of `oneclass_n4_all0`, `oneclass_n4_all1`,
`oneclass_n10_all1`, `oneclass_n60_all1`, `emptyval_n1_class0`, `emptyval_n2_both`,
`emptyval_n3_both`, the header of `x21_leverage_one.py` and `x21_sas_results.json` (cases S1,
L1, L3, T 1E-6, 7E-7, 4E-7, 3E-7, 1E-8).

Read on the SAS blueprint (accepted Lean): `def:sasPipeline`, `def:logit_scored_train_output`
(with `Sas.Model`, `Sas.linpred`) and its precondition, `def:logit_scored_valid_temp` and its
precondition, `def:logit_scored_train`, `def:logit_scored_valid`, `def:risk_scores_train`,
`def:risk_scores_train_clean`, `def:train_inputs_stop`, `def:metrics_inputs_stop`,
`def:logistic_lackfit`, `def:logistic_association` and their preconditions, `def:roc_stats`,
`def:auc_pairs`, `def:auc_summary`, `def:logit_scored_valid_sorted`, `def:total_good_bad`,
`def:ks_calculation`, `def:ks_statistic`, `def:confusion_metrics_macro`,
`def:threshold_analysis`, `def:decile_data`, `def:decile_list`, `def:decile_analysis`,
`def:total_defaults`, `def:cumulative_lift`, `def:train_scores_sorted`, `def:psi_cuts`,
`def:train_bins` and its precondition, `def:valid_bins`, `def:psi_floor`, `def:psi_calculation`,
`def:psi_summary`, `def:calibration_data`, `def:calibration_plot`, `def:validation_summary`,
`def:model_performance_metrics`, the runtime helpers of `def:credit_raw_clean` (`Sas.num`,
comparisons), the statement of `thm:score_chains_agree`; `get_graph consumers_of` on 16 items.

Read on the port blueprint: `def:Paired`, `def:SasParams`, `def:PyLinks`, `def:SasLinksOf`, the
statements of `thm:T0`, `thm:E5_train_scores`, `thm:E8_validation_summary`,
`thm:F4_model_summary`, `thm:F6_model_performance_metrics`, `thm:A4_metrics`,
`thm:metrics_run_08_validation_summary_S21b`, `thm:metrics_run_09_model_performance_S22b`;
`get_graph consumers_of` on 4 items; one regex search for the SAS units this file changes.

Not read: any proof on either blueprint (I rely on the tables of the two drafts for what the 34
SAS proofs open); `def:risk_scores_validation`, `def:risk_scores_validation_clean`,
`def:confusion_matrix`, `def:validation_metrics`, `def:roc_train`, `def:roc_valid`,
`def:model_summary`, `def:final_model_output`, `def:confusion_matrix_train`,
`def:training_metrics` (for these I rely on section 2.2 of the no-fit draft, which read them);
`Sas.freq2`, `Sas.merge11`, `Sas.groupKeys`, `Sas.rocObs`. Where a statement below rests on an
item I did not read, it says "by the draft" or "expected".

Two corrections to the record, found while reading:

1. **x27 C60 and E60 are the same training part.** E60 is "60 rows, no defaulter at all" (runner
   docstring); C60 moves the defaulters to the validation part. In both the 42 training rows all
   have `default_flag` 0 (`X27 E60 risk_scores_train ... default_flag=0` on the 42 lines;
   `model_features_train.csv` of the two full runs is the same file). The no-fit draft says "E60
   (every outcome 1)": it is not. A training part with every outcome 1 was run only by the judge:
   `judge/runs/oneclass_n4_all1`, `oneclass_n10_all1`, `oneclass_n60_all1` (same error, same
   files, `printed_confusion_train.csv` is `1,0,n,100`). R46 of the RULEBOOK cites C60 and E60
   only. See section 9, evidence to stage.
2. **The classification table is not in the SAS Lean.** `out-of-scope.tsv` line 10: "PROC
   LOGISTIC fit (stepwise, optimiser), model_coefficients, CTABLE, RSQUARE, fit statistics: model
   fit out of scope; CTABLE uses leave-one-out quantities of the fit". There is no unit for it,
   and `Sas.Model` holds an intercept and coefficients, no covariance. Section 5.

## 1. Summary

| # | Item | New or changed | For | Clears |
|---|---|---|---|---|
| N1 | `def:logistic_no_fit` | new | level 1 | nothing |
| N2 | `def:logit_scored_train_output_nofit` | new | level 2 | nothing |
| N3 | `def:logit_scored_valid_temp_nofit` | new | level 2 | nothing |
| C1 | `def:ks_statistic` | changed (one branch) | level 3 | its dependents (below) |
| C2 | `def:decile_analysis` | changed (one branch) | level 3 | its dependents |
| C3 | `def:validation_summary` | changed (one branch) | level 3 | its dependents |
| C4 | `def:cumulative_lift` | comment only | level 3 | `def:model_performance_metrics` |
| C5 | `def:model_performance_metrics` | changed (one branch) | level 3 (F6) | nothing (a root) |
| C6 | `def:train_bins_precond` | changed (one clause wider) | level 3, H15 | nothing (a root) |
| C7 | `def:sasPipeline` | changed (`fit` field, one branch; text) | level 1 | `def:SasLinks` and the 34 |
| C8 | `def:SasLinks` | changed: (1), (2) padded text; text of (6), (8); (3) for the training score file, see 4.8 | padded text, H15 | the 34 |
| O1 | `def:roc_stats`, `def:logistic_association`, `def:logistic_lackfit` and three preconditions | changed, optional (same pattern as R46) | "what SAS does" on one class | `def:model_performance_metrics` only |
| O2 | `def:logistic_ctable_xp` | new, optional | leverage near 1 | nothing |

Level 1 needs N1 and C7. Level 2 adds N2 and N3. Level 3 adds C1 to C6. The padded text is C8.
Nothing is needed on the SAS side for leverage near 1 or for a final parameter with variance 0
as far as any contract goes (sections 5 and 6); O2 is what to add if the SAS Lean is to state
SAS's rule, and section 6 gives the measurement (X22, read uncommitted) the clearing waits for.

Item count: 146 today; 149 with N1 to N3; 150 with O2.

Proof work on the SAS blueprint after the clearing: 2 proofs with new substance (`thm:sas_Q27`,
`lem:sas_Q27_clause1`), 2 with the mechanical edit of the padded-text draft
(`lem:sasLinks_witness`, `lem:sas_links_sat`), up to 5 with one new non-emptiness step (Q22 to
Q26, for C1 to C3), up to 14 with one more branch to discard where `Fitted` is opened, the rest
unchanged. Table in section 7.

## 2. What SAS does, file by file

### 2.1 Train stage on a one-outcome training part

Source: `x27_one_class_roc.log` (C60, E60), `judge/runs/x27_C60_full/train.sas.log`.

| Table or file | Observed |
|---|---|
| PROC LOGISTIC | "ERROR: All observations have the same response. No statistics are computed." (log line 424). None of the ten ODS tables is created (ParameterEstimates, Classification, LackFitChiSq, LackFitPartition, OddsRatios, Association, RSquare, GlobalTests, FitStatistics, ModelBuildingSummary: lines 427-454) |
| `logit_scored_train` after OUTPUT | 42 observations, 44 variables (line 425): the 42 features, `_LEVEL_`, `pd_logistic`; then 45 with `pred_logistic`. `pd_logistic` missing on the 42 rows, `pred_logistic` 0 |
| `work.logit_model`, `model_coefficients` | not created; `model_coefficients.csv` not written |
| `confusion_matrix_train`, `training_metrics` | one row each (`0,0,42,100`; precision, recall, F1 missing, accuracy 1). With every outcome 1 (`oneclass_n60_all1`): `1,0,42,100` |
| `logit_scored_valid_temp` | not created (PROC PLM: the item store does not exist) |
| `logit_scored_valid`, `confusion_matrix`, `validation_metrics` | 0 rows (2, 0 and 4 variables) |
| `risk_scores_train`, `_clean` | 42 rows; score missing, grade F, Decline, 0.20 |
| `risk_scores_validation`, `_clean` | 0 rows, 9 variables; the CSV is one header line of 9 names |
| `roc_train`, `roc_valid` | not created |
| `final_model_output` | 42 rows (`9,0,27,2231,11.6950644,4600,2,0,,,F,Decline,20.00%`) |
| `model_summary` | 0 rows, 14 variables; the CSV is a header only |

### 2.2 Predict stage

Stops at its input check: `model_coefficients.csv` is absent (predict log lines 47-49). No file.

### 2.3 Metrics stage on the header-only validation score file

Source: `judge/runs/x27_C60_full/metrics_calculation.sas.log` (line numbers below), the files
of that run, of `x27_E60_full` (same bytes), of the three `oneclass_n*_all1` runs, and of
`emptyval_n2_both`, `emptyval_n3_both` (a model was fitted there and the validation part is
empty: the same pattern, so the behaviour does not depend on the fit).

| Step (source lines) | Observed | The Lean today, on the validation table with no row |
|---|---|---|
| input check (36-44) | does not stop: both files exist | see 4.9 |
| PROC IMPORT of `risk_scores_validation.csv` (50-56) | "Unable to sample external file, no data in first 5 records", "ERROR: Import unsuccessful" (62-63). `work.logit_scored_valid` does not exist. The script runs on | table with no row (convention of R39) |
| PROC IMPORT of `risk_scores_train.csv` (58-64) | 42 rows; `pd_logistic` and `credit_risk_score` are read as character `$1.` (lines 128, 132), every value blank | link (3): the same table, numeric missing cells. See 4.8 |
| `roc_stats` (70-77) | not created (254, 277) | one row, Area missing. Not in the pipeline. O1 |
| `auc_pairs`, `auc_summary` (79-113) | `auc_pairs` not created; `auc_summary` 0 observations, 3 variables (284, 303) | no row, no row: agree |
| sort, `total_good_bad` (123-133) | fail; the two macro variables do not resolve (345, 349) | not written to a file |
| `ks_calculation` (135-153) | 0 observations (356) | no row: agrees |
| `ks_statistic` (155-162) | **not created**: "The following columns were not found in the contributing tables: pd_logistic" (366, 370). `ks_statistic.csv` is not written (919-920) | **one row, both values missing**. C1 |
| `confusion_metrics`, `threshold_analysis` (172-222) | every `metrics_xx` 0 rows; `threshold_analysis.csv` is a header of 6 names | no row: agrees |
| `decile_data` (233-239) | 0 observations, 0 variables (467) | no row: agrees |
| `decile_analysis` (248-279) | **not created**: "Table WORK.DECILE_DATA doesn't have any columns" (507-524). `decile_analysis.csv` is not written (846-847) | **ten rows**. C2 |
| `cumulative_lift` (291-314) | 0 observations, 8 variables (583); `printed_cumulative_lift.csv` header only | ten rows today; no row once C2 is made (it folds over `decile_analysis`). C4 |
| `train_scores_sorted`, `psi_cuts`, `train_bins` (332-358) | run on the character column: every cut missing, every row in bin 0 | every cut missing, every row in bin 0: agrees |
| `valid_bins` (360-369) | 0 observations, 2 variables (641) | no row: agrees |
| `psi_calculation`, `psi_summary` (381-416) | bin 0: `0,1,0,4.3780689798`; bins 1 to 9: `k,0,0,0`; PSI 4.3780689798, "Significant change" | the same: bin 0 has shares 1 and 0, floor 0.5/n, component (1 - 0.5/n) * log(2n), which is 4.37807 for n = 42 and 1.49313 for n = 3 (`oneclass_n4_*`: 1.493132891). Computed by hand from the Lean read, not by `eval_decl` |
| `calibration_data`, `calibration_plot` (427-444) | 0 observations and 0 variables; `calibration_plot` not created; the file is not written (930-931) | no row, no row: agree |
| `validation_summary` (459-473) | "File WORK.KS_STATISTIC.DATA does not exist" (745): the step stops at compile time, **0 observations**, 8 variables (757). The CSV is the header `ROCModel,AUC,Gini,PSI,PSI_interpretation,model,status,KS_Statistic` | **one row** (the merge of no row, the KS row and the PSI row). C3 |
| `model_performance_metrics` (519-541) | the same error (940), **0 observations** (959); the CSV is a header of 12 names | **one row**. C5 |

Files of the metrics stage on such a run: `validation_summary.csv`, `threshold_analysis.csv`,
`model_performance_metrics.csv` a header only; `ks_statistic.csv`, `decile_analysis.csv`,
`calibration_plot.csv` not written.

## 3. New items

### N1. `def:logistic_no_fit` (new; level 1; form U of the no-fit draft, section 3.1)

- **Source text**: the PROC LOGISTIC step, train.sas 71-119 (the registered text of
  `def:logit_scored_train_output`).
- **Behaviour**: a Boolean of the training feature table as read. True exactly when the
  `default_flag` values present in the table are all equal; this includes the table in which no
  `default_flag` is present. True means: PROC LOGISTIC stops and fits no model. The script does
  not stop.
- **Lean in words**: one definition, generic in the number type like the other units. Take the
  list of the present `default_flag` values of the rows, in order (`Sas.num r "default_flag"`,
  missing values left out). The result is true for the empty list, and for a non-empty list when
  every element is equal to the first under `RealLike.eqb` (the comparison `Sas.eq` uses). No
  parameter.
- **Condition, in its text** (amendment A10: no precondition item, the paragraph is the
  condition): stated for tables in which the 36 candidates of the MODEL statement and
  `default_flag` are present in every row and `default_flag` is 0 or 1. On a valid run every such
  cell is present and 0 or 1 (`lem:sas_feature_rows`, `TrainOK`).
- **Comments to carry**: OPEN: which rows PROC LOGISTIC uses when a candidate is missing was not
  run (the open point of `logit_scored_train_output_precond`). OPEN: a table with no usable row
  ("There are no valid observations" is observed for the ROC step, R46, not for this step).
  OPEN: a response with three values or more (PROC LOGISTIC then fits another model; not run).
- **SAS evidence**: x27 C60 and E60 (42 training rows, all 0: the error above); x27 A4, B60, D60
  (both outcomes: the fit runs, `model_coefficients` exists). Every outcome 1: the judge runs
  `oneclass_n4_all1`, `oneclass_n10_all1`, `oneclass_n60_all1` (same error); to be staged for
  the translators, section 9.
- **RULEBOOK**: R46 gains "In the Lean since ...: `logistic_no_fit`; the `fit` field of
  `sasPipeline` returns nothing there", and its evidence cell is corrected: C60 and E60 are both
  a training part of zeros; the all-ones case is cited from the staged runs.
- **Clears**: nothing (new item).

### N2. `def:logit_scored_train_output_nofit` (new; level 2)

- **Source text**: the OUTPUT statement of the same step (train.sas 109-111).
- **Behaviour**: the OUTPUT data set when PROC LOGISTIC fitted nothing. Every input row, in
  input order, with `_LEVEL_` and then `pd_logistic` added after the existing variables;
  `pd_logistic` is missing on every row.
- **Lean in words**: one definition taking the training feature table only (no model, no
  `invLink`). Each row is mapped as `def:logit_scored_train_output` maps it, with the
  `pd_logistic` cell the numeric missing value: `_LEVEL_` set to the number 1, then
  `pd_logistic` set to missing.
- **Comment to carry**: OPEN: the value of `_LEVEL_` on this path was not printed. The variable
  is dropped by `risk_scores_train_clean`, is not kept by `final_model_output`, and no unit reads
  it; the unit writes the cell the fitted unit writes, and says so.
- **SAS evidence**: x27 C60: train log line 425 (42 observations, 44 variables after the step),
  `logit_scored_train exists rows=42 vars=45`, the 42 lines `pd hex=. pd_logistic=.`,
  `risk_scores_train.csv` lines 2 and 3 (probability and score empty, `pred_logistic` 0, F,
  Decline, 20.00%).
- **What it gives downstream, with no edit** (by the draft, section 2.2; I read
  `logit_scored_train`, `risk_scores_train`, `risk_scores_train_clean`): `pred_logistic` 0;
  score missing; grade F by the first test; Decline; rate 0.05 + 0.15; `roc_train` no row;
  `model_summary` no row; `final_model_output` every row.
- **Clears**: nothing.

### N3. `def:logit_scored_valid_temp_nofit` (new; level 2)

- **Source text**: train.sas 173-178 (the registered text of `def:logit_scored_valid_temp`).
- **Behaviour**: PROC PLM when no item store exists: "ERROR: The file WORK.LOGIT_MODEL does not
  exist or it is not a valid item store"; `work.logit_scored_valid_temp` is not created. By the
  convention of R39 and R46 a table with no row stands for a table that was not created.
- **Lean in words**: a constant, the table with no row, generic in the number type. No argument.
- **Why an item and not a remark**: section 5 of the informal specification compares a file with
  "what the composed SAS units give on the same run". With this item the SAS side of E5, A2, F3,
  F4 on one outcome is a composition of SAS units only; without it the port contract would write
  the empty table itself and the SAS Lean would not say it.
- **SAS evidence**: x27 C60: train log lines 512, 522, 532, 540; `logit_scored_valid_temp DOES
  NOT EXIST`, `logit_scored_valid exists rows=0 vars=2`, `confusion_matrix rows=0 vars=0`,
  `validation_metrics rows=0 vars=4`, `risk_scores_validation rows=0 vars=9`,
  `risk_scores_validation.csv line 1 len=116` and no line 2.
- **What it gives downstream, with no edit**: `logit_scored_valid`, `risk_scores_validation`,
  `risk_scores_validation_clean` are maps, so no row; `confusion_matrix`, `validation_metrics`,
  `roc_valid` no row (by the draft).
- **Not represented**: the header of the header-only file (9 names, not the feature columns).
- **Clears**: nothing.

## 4. Changed items

### C1. `def:ks_statistic` (level 3)

- **Behaviour**: when `ks_calculation` has no row, the table with no row; otherwise as today (one
  row, also when every `ks_value` is missing).
- **Lean in words**: one test in front of the present body: `ks_calculation` empty gives the
  empty table. The rest is not touched. The comment "the query gives exactly one row, also when
  no row passes the WHERE" stays for a table with rows and gains: a `ks_calculation` with no row
  arises only when `work.logit_scored_valid` was not created (PROC IMPORT of the header-only
  file, R39 and the new rule of section 8); it then has no `pd_logistic` variable, the query
  fails, `work.ks_statistic` is not created and `ks_statistic.csv` is not written; the table
  with no row stands for that.
- **Why the test is on "no row"**: `ks_calculation` gives one row per row of the sorted
  validation table, and inside metrics_calculation.sas that table comes from PROC IMPORT only,
  which never yields a table with a header and no row (R39). So "no row" and "not created" are
  the same case for this script.
- **SAS evidence**: x27 C60 metrics log 356, 365-370, 919-920; no `ks_statistic.csv` in
  `x27_C60_full`, `x27_E60_full`, `oneclass_n*_all1`, `emptyval_n2_both`, `emptyval_n3_both`.
- **Clears** (statement consumers): `def:validation_summary`, `def:model_performance_metrics`,
  `def:sasPipeline`, and through it `def:SasLinks` and the 34.
- **Dependent proofs**: `thm:sas_Q24` and any other that unfolds the KS table of the pipeline:
  **new proof work, small** (expected; proofs not read): show the sorted validation table has a
  row on a fitted valid run (validation part not empty, ruling G57; `lem:sas_score_rows` or the
  row count the proof already has), so the new test is false, then as before.

### C2. `def:decile_analysis` (level 3)

- **Behaviour**: when `decile_data` has no row, the table with no row; otherwise as today (ten
  rows).
- **Lean in words**: one test in front of the present body, on `decile_data` empty. Comment:
  PROC RANK on a table that does not exist leaves `work.decile_data` with no row and no variable;
  PROC SQL then fails ("doesn't have any columns"), `work.decile_analysis` is not created and
  `decile_analysis.csv` is not written. "Always ten rows" (rulings G41, G45) holds when the
  validation table exists.
- **SAS evidence**: x27 C60 metrics log 462, 467, 507-524, 846-847; the file is absent in the
  same runs as for C1.
- **Clears**: `def:cumulative_lift`, `def:sasPipeline` (and on).
- **Dependent proofs**: `thm:sas_Q26`: **new proof work, small** (expected): `decile_data` has a
  row on a fitted valid run, then as before.

### C3. `def:validation_summary` (level 3)

- **Behaviour**: when `ks_statistic` has no row, the table with no row; otherwise as today.
- **Lean in words**: one test in front of the present body, on the `ks_statistic` argument
  empty. Comment: a DATA step whose MERGE names a table that does not exist stops at compile time
  and leaves its output with 0 rows (R46, the case of `model_summary`); PROC EXPORT writes the
  header only. The sentence "ks_statistic and psi_summary have one row each" becomes "when the
  validation table exists".
- **Not represented**: the header of the header-only file (8 names, `KS_Statistic` last,
  `KS_Cutoff` absent), as R46 says of `model_summary.csv`.
- **SAS evidence**: x27 C60 metrics log 745, 757; `validation_summary.csv` is that header line in
  all the runs named under C1.
- **Clears**: `def:model_performance_metrics`, `def:sasPipeline` (and on).
- **Dependent proofs**: those that read the summary table of the pipeline (Q22, Q23, Q24, Q25 by
  their subjects; not read): **new proof work, small**, the same non-emptiness fact as C1.

### C4. `def:cumulative_lift` (comment only)

- **Behaviour**: unchanged in value. It folds over `decile_analysis`, so after C2 it has no row
  when the validation table was not created, which is what SAS shows (0 observations, 8
  variables; `printed_cumulative_lift.csv` a header only).
- **Lean in words**: the comment line "work.decile_analysis always has ten rows" becomes "has ten
  rows when the validation table exists, and no row otherwise (C2)". It is cleared by C2 in any
  case and is restated with this comment.
- **SAS evidence**: x27 C60 metrics log 557-587.
- **Clears**: `def:model_performance_metrics` (which names it only for the evaluation harness,
  DEV-006).

### C5. `def:model_performance_metrics` (level 3, contract F6)

- **Behaviour**: when `ks_statistic` has no row, the table with no row; otherwise as today.
- **Lean in words**: one test in front of the merge, on the `ks_statistic` argument empty. The
  helper `evalApply` of the item stays. Comment as C3.
- **SAS evidence**: x27 C60 metrics log 940, 959; `model_performance_metrics.csv` is a header of
  12 names in all the runs named under C1.
- **Clears**: nothing (no consumer).

### C6. `def:train_bins_precond` (level 3; observation H15)

- **Behaviour**: the clause "`credit_risk_score` is a numeric cell in every row" becomes "a
  numeric cell, or a text cell whose text is missing or blank". The other clauses stay.
- **Why**: on the training score file of a one-outcome run PROC IMPORT reads `credit_risk_score`
  (and `pd_logistic`) as character `$1.`, every value blank. In a numeric context SAS converts a
  blank character value to a missing number, so every cut is missing and every row is in bin 0.
  `Sas.num` already reads a text cell as missing, so `def:train_scores_sorted`, `def:psi_cuts`,
  `def:train_bins`, `def:valid_bins` give SAS's result on such a table with no edit (2.3). Only
  the precondition excludes it today.
- **Not covered by the unit, and to be said in its comment**: a text cell holding a number text.
  SAS would convert it to the number; `Sas.num` gives missing. It needs a score file whose first
  20 rows have no score and a later row has one, which no run gives (H15).
- **SAS evidence**: x27 C60 metrics log 128, 132 (the two informats `$1.`);
  `printed_psi_calculation.csv` of `x27_C60_full` (4.3780689798) and of `oneclass_n4_all1`
  (1.493132891). New rule in the RULEBOOK, section 8.
- **Clears**: nothing (a root).
- Whether the port's coverage lemma `lem:sas_cov_train_bins` is then restated to cover the
  one-outcome run is the port side's choice (section 9).

### C7. `def:sasPipeline` (level 1; form U)

- **Behaviour**: field `fit` only. After the test of `train_inputs_stop`, a second test: when
  `logistic_no_fit` of `readFeatures F` is true, nothing; otherwise, as today, the parameter
  `fit` applied to `readFeatures F`. The 17 parameters keep their names, order and types. The
  fields `features`, `score`, `scoreTest`, `metrics` keep their Lean letter for letter (the
  `metrics` field changes in value through C1 to C3 only).
- **Text**: sentence (2) gains "and it returns no model when PROC LOGISTIC fits nothing
  (`logistic_no_fit`, R46, x27): the script does not stop there, it runs on without a model; the
  value of the parameter `fit` on such a table is not read". The comment "A step returns `none`
  when the stop unit of its script is true" gains "or, for `fit`, when the procedure fits no
  model". Sentence (5) gains "on a validation score table with no row (a header-only file, which
  PROC IMPORT cannot read) the four tables have no row: two of the files are then a header only
  and two are not written, which the tables do not distinguish".
- **One statement dependency added**: `def:logistic_no_fit`.
- **SAS evidence**: as N1; `model_coefficients.csv` absent and predict.sas stopped (2.2), which
  is what `coefExists` now says through link (8).
- **Clears**: `def:SasLinks` and 33 of its 34 dependents directly; the 34th
  (`lem:sas_split_sat`) through `def:SasLinks`.
- **Dependent proofs**: section 7.

### C8. `def:SasLinks`

Three parts. Only the first two are decided; the third needs the owner or the lead (4.8).

**4.8 a. Clauses (1) and (2), padded text.** Exactly the change of
`saslinks-padded-text-draft-2026-11-18.md`, sections 2 to 4, with nothing added: inside the
local definition `deliveredCell`, one conjunct appended at the end of clause (ii) and one at the
end of clause (iii), each saying that removing the blanks at the two ends of the delivered text
changes nothing (`Sas.trimBlanks` of the characters is the characters). Clause (i),
`deliveredRow`, `textColumn`, `deliveredTable` and clauses (2b), (4), (5), (6), (7) are not
touched. Text: the five replacements of section 3 of that draft. Evidence: x23 part I (` 7`,
`7 `, `" 7"`, `"7 "` stored as `7`), on the id column of the training file only (risk 2 of that
draft: not run on `MonthlyIncome` or on the test file).

**4.8 b. Clauses (6) and (8), text only.** Lean unchanged. Text of (6) gains: "On a table where
PROC LOGISTIC fits nothing the value of `fit` is not read by the pipeline; clause (6) is still
asked of it." Text of (8) gains: "`coefExists` is true exactly of a model a fit that happened
returned: on a one-outcome training part no coefficient file exists (x27). The score flags are
true of the score tables of a run without a model as well: that training score table is what
the scoring chain gives for a model with a term naming no column (every probability missing),
and the table with no row is what it gives on no row; so the metrics step does not stop there,
as SAS does not." This last sentence is a fact to be proved, not assumed: see 4.9.

**4.8 c. Clause (3), the read-back of the training score file.** Today: `readScoresTrain t = t`
for every table. Of the real PROC IMPORT this is false in letter on the training score file of a
one-outcome run: the two all-empty columns come back as character columns with blank values
(metrics log 128, 132; H15), where the identity gives numeric cells holding the missing value.
The lead corrected the port's clause for the same file (conjunct 16 of `PyLinks`). Two ways:

- **W (specified here, no new limit).** Clause (3) for `readScoresTrain` becomes: for every
  table, the read-back has the rows in order and in each row the cells in order with the same
  names; each cell is the cell of the table, except that in a column whose cell is the numeric
  missing value in every row of the table the cell may instead be the text cell with the missing
  text. The other three read-backs stay the identity. The clause keeps its position in the
  conjunction. The identity meets it, so the witness of `lem:sasLinks_witness` and
  `lem:sas_links_sat` stands (one more case per cell: mechanical). Cost: every proof that uses
  the identity of `readScoresTrain` on the reached training score table must first show that no
  column of that table is missing in every row (on a fitted valid run: the features are present,
  `lem:sas_feature_rows`; probability and score are present; the table has a row), and then gets
  the identity back. That is new proof work in the metrics theorems that read the training
  scores (Q25 by its subject; possibly others; not read), and in `thm:T2` on the port.
- **K (no Lean change, needs the owner).** Keep the identity and extend ruling G55 by a
  sentence: "a column that is empty in every row is read by PROC IMPORT as a character column
  of blanks, which the PSI steps treat as missing numbers; the read-back is taken to carry the
  missing values". No proof changes. It is a stated idealisation that is false in letter of the
  real reader on a reachable valid file, so it is the owner's to take: narrowing 4.

Either way the SAS units give SAS's result on the table as really read (C6), and the equality
contracts do not use clause (3) at all (they take the read-backs from `Paired` 4).

### 4.9 The metrics step does not stop on a run without a model: a lemma, not a link

`def:metrics_inputs_stop` reads the two score flags, and link (8) says a score flag is true of a
table exactly when the `score` field returned it for some model and some table. Read from the
Lean: `score` takes any model, not only a fitted one. For the model with intercept 0 and one
term naming a column the table does not have, `Sas.linpred` is missing on every row, so the
validation chain on the training feature table gives every row with `pd_logistic` missing,
`pred_logistic` 0, score missing, F, Decline, which is the table N2 leads to (the column order
is the same: `thm:score_chains_agree` shows it for a fitted model; `_LEVEL_` and
`predicted_logit` are both dropped). And `score` on the table with no row returns the table with
no row. So under link (8) as it stands both flags are true of the two score tables of a no-fit
run, and `metrics` returns four tables there. Nothing in `def:SasLinks` needs to change for it.

To be proved where level 3 is stated (on the port blueprint, from `Paired` 5, which is link (8)
word for word; or as a new lemma of the SAS blueprint if the lead wants it there): for every
feature table F, the no-fit training score table of F (N2, then `logit_scored_train`,
`risk_scores_train`, `risk_scores_train_clean`) is `score m F` for that model m, provided
`readFeatures` is the identity on F or the statement is written on `readFeatures F`. I checked
this by reading `logit_scored_valid`, `risk_scores_train` and `risk_scores_train_clean`; I did
not read `risk_scores_validation` and `risk_scores_validation_clean` (the theorem
`score_chains_agree` says they agree with the training units on a fitted run). **Expected, not
verified.** If it fails, link (8) needs a second disjunct for the two score flags ("or the table
is the score table of a run in which `fit` returned nothing"), which is a change of the Lean of
`def:SasLinks` beyond 4.8 a: question 3.

### O1. Optional: the three printed-table units R46 lists as "not corrected"

- `def:roc_stats`: the table with no row when the rows used hold no event or no non-event
  (which includes the table that was not created); its precondition loses the two-class clause.
  Evidence: x27 C60 metrics log 254-277, 1061-1062.
- `def:logistic_association`, `def:logistic_lackfit`: the table with no row when the rows used
  hold one class; their preconditions lose the two-class clause. Evidence: x27 C60 train log
  433-442 (`LackFitPartition`, `Association` not created).
- Same pattern and same Lean shape as `roc_train` since 2026-11-16. None is in the pipeline;
  consumers: `def:model_performance_metrics` (harness dependency only), which C5 restates
  anyway. No proof depends on them on the SAS blueprint.
- Not needed by any contract I read. Lead's choice (question 6).

## 5. Leverage near 1

**Does the SAS Lean's classification table model SAS's no-adjustment rule? There is no
classification table in the SAS Lean.** CTABLE has been out of scope since the first gate
(`out-of-scope.tsv` line 10), the fit is a parameter, and `Sas.Model` carries no covariance, so
no unit can compute a leverage. Consequences:

- Nothing in the SAS Lean is false on a fit with a leverage near 1, and nothing needs to change
  for any contract: on the port blueprint the classification table (train step 08) appears only
  in the coverage contract G2, which is about the port's own precondition; no theorem compares
  it with a SAS unit (the unit theorems against SAS units are for train steps 01, 04, 09, 10,
  11, 14).
- So after the port's fix "the port does what SAS does" on leverage near 1 rests on experiment
  X21 and the judge, not on a theorem. If that is to be a theorem, the SAS Lean needs a unit.

**O2. `def:logistic_ctable_xp` (new, optional): the cross-validated probability CTABLE counts.**

- **Source text**: the CTABLE option of the MODEL statement (train.sas 106), registered as an
  excerpt like `def:logistic_lackfit` (DEV-007).
- **Inputs**: for one observation used by the fit: the response y (0 or 1), the linear predictor
  eta, the predicted probability p, and the quadratic form q of its covariates in the estimated
  covariance of the parameters. The fit is out of scope, so eta, p and q are given: q is a new
  parameter of the kind of P4, and the unit says so. The leverage is h = p (1 - p) q.
- **Behaviour (X21)**: the probability the classification table counts for the observation is
  - p itself, with no adjustment, when 1 - h is at most the bound tau;
  - otherwise the one-step leave-one-out probability: the inverse logit of
    eta - (y - p) q / (1 - h).
- **The bound**: SAS adjusts at 1 - h = 1.489e-8 (case T 4E-7: leverage 0.99999998511292, XP_1 is
  0 where p is 0.99999798) and does not at 8.56e-9 (case T 3E-7: leverage 0.99999999143809, XP_1
  equals p), nor at leverage printed 1 (L1 to L5). So tau lies in [8.56e-9, 1.489e-8). The value
  is not located: 1e-8 and the square root of 2^-53 (1.0537e-8, the bound of R25) both fit.
  **To be measured before the unit is written** (cases between T 3E-7 and T 4E-7), or the unit
  carries the interval as an OPEN marker and a precondition that 1 - h is outside it, which is a
  narrowing (narrowing 6).
- **The inverse logit** of the second branch is a parameter as in `logit_scored_train_output`
  (P5).
- **Not in this unit**: the levels 0.000, 0.020, ..., the level printed 1.000, the counts and
  the eight percentages, the intercept-only fit (an exact leave-one-out mean and other level
  values, the port's X16), and the case with no table at all (section 6). A full
  `logistic_classification` unit is a translation of its own, with its own evidence.
- **SAS evidence**: `x21_sas_results.json`, the OUT rows (y, xb, p, lev, XP_1) of the 18 fits
  with a table. It lies under `migration/legacy-to-port/experiments/`; the SAS translators need
  the SAS half staged under `legacy-to-lean` (section 9).
- **Clears**: nothing. No item depends on it.
- New rule for the RULEBOOK (section 8). Question 5.

## 6. A final parameter with variance 0 (a parameter left out at the last iteration)

What X21 S1 shows of PROC LOGISTIC (one event in 60, flagged; fitted without selection):

- ParameterEstimates has the row of the parameter: DF 0, Estimate 0, standard error, Wald
  chi-square and p-value missing.
- OUTPUT predicts with 0 for it: on the row with x1 = 1 the linear predictor is the intercept
  (-12.1041508908181), as on the rows with x1 = 0.
- No Classification table ("Output 'Classification' was not created"); H= and the
  cross-validated probabilities are missing on every row.

**What the SAS Lean's units after the fit must do, and whether they do:**

| Unit | Must do | Today |
|---|---|---|
| the parameter `fit`, `Sas.Model` (P4) | the model is the parameter table: the left-out parameter is a term with coefficient 0 | no change: it is what the parameter returns. One sentence for P4 and R26: "a parameter the fit left out (DF 0) is in the parameter table with estimate 0 and is a term of the model with coefficient 0" |
| `logit_scored_train_output` (`Sas.linpred`) | add 0 times the covariate | does: the sum is unchanged at the real numbers. Agrees with S1 |
| the same, when that covariate is missing | not measured | missing (R26: missing as soon as a covariate of the model is missing). Outside valid input (`lem:sas_feature_rows`) |
| `logit_scored_valid_temp`, `test_scored_temp` (PROC PLM on the stored model) | S1 did not run PROC PLM. X22 (below): the linear predictor with 0 for the parameter | the linear predictor with coefficient 0, as OUTPUT: agrees with X22 as read |
| `logistic_association` | X22: the table is made on the three designs | computed from the probabilities as on any fit |
| `logistic_lackfit` | X22: made on B and C, **not made on A** | a partition whatever the probabilities. See the note on A below |
| the coefficient file | not a unit (`coefExists` only) | no change |
| the classification table | S1, X22 A and C: none. X22 B: **made** (48 rows) | not in the Lean (section 5) |

**The measurement on the staged train.sas: experiment X22, in the working tree, not committed.**
While this file was being written, `migration/legacy-to-port/experiments/x22_left_out_final.py`
and `x22_sas_results.json` appeared in the working tree (untracked; the docstring says its
summary is "filled after the runs"). I read the SAS facts of the JSON as it stood; they must be
read again at the commit. train.sas runs as it is except that the MODEL statement names the
design's variables without the selection options; metrics and predict follow.

| Design | Parameter left out | ParameterEstimates | Classification | LackFit | Association | PROC PLM (validation, 40 rows; the flag is 1 on every 8th) | metrics, predict |
|---|---|---|---|---|---|---|---|
| A (X21 S1: 60 rows, one event, flagged) | at the last iteration; complete separation; "information matrix is singular" | DF 0, Estimate 0, no standard error | not created | not created | created | no missing value; two values, 5.5364534854088E-6 and ...89E-6: the flagged rows are scored with 0 for the flag | no error |
| B (120 rows; the flag collinear from the start) | at every iteration; converged; no warning | DF 0, Estimate 0 | **created**, 48 rows | created | created | no missing value | no error |
| C (200 rows, three events, one flagged alone) | at the last iteration; converged; "information matrix is singular" | DF 0, Estimate 0 | not created | created | created | no missing value | no error |

What it settles, as read:

The three points to measure were: M1, whether the stepwise selection of train.sas can end with
such a parameter in the final model; M2, what PROC PLM gives with the stored model; M3, whether
the LackFit, Association and Classification tables are made.

- M1 (can the stepwise selection of train.sas end with such a parameter): **not settled**. The
  X22 docstring: "The selection path of train.sas is not known to reach such a final model (a
  parameter left out at a step is removed at the next one, singular-information.md), so the
  model is fixed". X22 measures the units after the fit on a model given without selection.
- M2 (PROC PLM): scores with 0 for the parameter, as OUTPUT. So **no change of `Sas.Model` and
  no branch in `logit_scored_valid_temp` or `test_scored_temp`**: the model is the parameter
  table with the term at coefficient 0, and the existing units give SAS's values. Read from the
  40 validation probabilities of each design only; the test predictions I did not compare.
- M3: Association is made. LackFit is made on B and C. The classification table is absent on A
  and C and present on B: the dividing line is the warning "the information matrix is singular"
  (a parameter left out at the last iteration by the fit), not DF 0 as such. A full
  classification unit (question 5) must take that as its case split.
- Note on A and `logistic_lackfit`: on A the 60 training probabilities are one value to 13
  digits and no LackFit table is made. C has DF 0 and a table, so the variance is not the
  reason; a partition with fewer than three groups is the likely one (not separated by these
  designs). `def:logistic_lackfit` returns a partition there. It is a printed table outside the
  pipeline; if O1 is taken this case belongs to it and needs its own run.

**What depends on it.** `Sas.Model` is declared inside `def:logit_scored_train_output`; editing
that item clears the scoring, ROC, summary and predict definitions downstream of it, not only
theorems. By X22 as read no such edit is needed. **The clearing should still not start before
X22 is committed with its summary and the lead has read it** (step 0 of section 8): if the
committed result differs from the above, a change of the model belongs to this same clearing.

## 7. What is cleared on the SAS blueprint, and the proofs

Cleared: `def:validation_summary`, `def:cumulative_lift`, `def:model_performance_metrics`,
`def:sasPipeline`, `def:SasLinks` (all restated with a change), and the 34 dependents of
`def:SasLinks`: `lem:sasLinks_witness`, `lem:sas_links_sat`, `lem:sas_features_some`,
`lem:sas_feature_rows`, `lem:sas_test_feature_rows`, `lem:sas_split_sat`,
`lem:sas_Q27_clause1`, `thm:sas_Q1` to `thm:sas_Q16`, `thm:sas_Q18` to `thm:sas_Q27`,
`thm:score_chains_agree`. Not cleared: `lem:sas_score_rows`, `lem:sas_features_row_total`,
`lem:sas_test_chain_agree`, every other definition. (A change to an item's Lean, even a comment,
clears the Lean of its dependents: DEV-012.)

| Item | Statement | Proof after the change | Basis |
|---|---|---|---|
| `lem:sasLinks_witness`, `lem:sas_links_sat` | unchanged | **mechanical**: the six `SLS` edits of the padded-text draft, section 5; with W of 4.8 c one more case per cell of the training score read-back | padded-text draft read the first in full |
| `lem:sas_features_some`, `lem:sas_feature_rows`, `lem:sas_test_feature_rows`, `lem:sas_split_sat` | unchanged | **unchanged** (the features step and links (1) first half, (2b), (3) for features and medians, (4), (5)) | padded-text draft |
| `thm:sas_Q1` to `thm:sas_Q11` | unchanged | **unchanged** (expected for Q4, Q5, Q6, Q8, Q9) | padded-text draft |
| `lem:sas_Q27_clause1` | **restated** (it copies the clause of `def:Q27`, which the owner restated) | **new proof work**: on a valid run every `default_flag` of the training feature table is present and 0 or 1, so "both outcomes" is `logistic_no_fit` false; then as before | no-fit draft |
| `thm:sas_Q27` | Lean unchanged in letters; its meaning follows `def:Q27` | **new proof work**: the case split on the outcomes | no-fit draft |
| `thm:sas_Q12`, `Q13`, `Q14`, `Q16`, `Q18` to `Q21`, `thm:score_chains_agree` | unchanged | **mechanical** where `Fitted` is opened: one more branch of the `fit` field to discard | no-fit draft; proofs not read |
| `thm:sas_Q15` | unchanged | **unchanged** | no-fit draft read the proof |
| `thm:sas_Q22` to `thm:sas_Q26` | unchanged | the `Fitted` branch (mechanical), and **new proof work, small**, where the proof unfolds `ks_statistic`, `decile_analysis` or `validation_summary`: the validation score table has a row, so the new test is false. With W of 4.8 c, also the step for `readScoresTrain` | by the subjects of the requirements; proofs not read |

Statements: 33 of the 34 should hash equal to `snapshot-round6.json` (all but
`lem:sas_Q27_clause1`); `thm:sas_Q27` is equal in letters and changes in meaning.

## 8. Order

**Step 0, before anything is cleared.**

- The requirements blueprint carries the restated `def:Q27` (and the texts of Q12 to Q14); the
  SAS profile is refreshed to it.
- Experiment X22 (section 6) is committed with its summary and read; the lead confirms that no
  change of `Sas.Model` is needed, or adds it to this clearing.
- The evidence of section 9 is staged for the translators.
- The lead has decided W or K (4.8 c), O1, O2.
- Fetch and keep `statement_lean` and `proof_lean` of the 34, and the Lean of every definition
  to be edited (procedure of 2026-11-17). Count the items: 146.

**Step 1, RULEBOOK and records** (`migration/legacy-to-lean`; the translators' files):

- R46 amended (N1; the evidence cell corrected; "not corrected" list shortened if O1).
- New rule (next free number): PROC IMPORT of the header-only `risk_scores_validation.csv`
  fails and metrics_calculation.sas runs on; each later step that names the missing table
  fails; consequences step by step as in the table of 2.3; a table with no row stands for the
  table that was not created; a file that is not written and a header-only file are both the
  table with no row. Evidence: the runs of 2.3.
- New rule: a blank character value used as a number is the missing number (the two `$1.`
  columns of the training score file; C6).
- P4 and R26: the sentence of section 6 on a parameter with DF 0 (after X22 is committed).
- If O2: the rule of section 5, with the interval for tau.
- `changes.md` of the verification and the amendments file.

**Step 2, new items** (nothing is cleared): N1, N2, N3 (and O2). 149 or 150 items.

**Step 3, the definitions, upstream first** so that each is restated once:

1. `def:ks_statistic` (C1), `def:decile_analysis` (C2).
2. `def:validation_summary` (C3), `def:cumulative_lift` (C4).
3. If O1: `def:roc_stats`, `def:logistic_association`, `def:logistic_lackfit` and their
   preconditions.
4. `def:model_performance_metrics` (C5), `def:train_bins_precond` (C6).
5. `def:sasPipeline` (C7), with the new dependency.
6. `def:SasLinks` (C8), once, with the padded-text Lean of the draft as it is and, if W, the
   new clause (3) for the training score file.

**Step 4, differential evaluation of the new and changed units** (`eval_decl`, as in rounds 2
and 3), on the rows of x27 C60: N2 then the train units against `risk_scores_train.csv` and
`final_model_output.csv`; the metrics field on that table and the table with no row against the
four tables with no row and `printed_psi_calculation.csv` (4.3780689798; with 3 training rows
1.493132891). A fitted scenario already in the receipts, to show C1 to C3 and C5 changed
nothing there.

**Step 5, the 34**: `lem:sasLinks_witness`, `lem:sas_links_sat`; the four feature lemmas;
`lem:sas_Q27_clause1` (restated) and `thm:sas_Q27`; Q1 to Q11; Q12 to Q16, Q18 to Q21,
`thm:score_chains_agree`; Q22 to Q26.

**Step 6, audit as in round 6**: 33 statements against the snapshot by hash; the changed and new
definitions reviewed by a second agent against the evidence; no `sorry` or `axiom`; sign-off.

**Then the port blueprint** (section 9), after the SAS sign-off.

## 9. The port blueprint

**Evidence to stage for the SAS translators** (they cannot read `judge/` or
`migration/legacy-to-port/`): under `migration/legacy-to-lean/experiments/`, the logs and files
of `x27_C60_full` (train, metrics, predict logs; the written files), one all-ones run
(`oneclass_n60_all1`), one fitted run with an empty validation part (`emptyval_n3_both`), and the
SAS half of X21 (`x21_sas_results.json` and the SAS program text, without the port comparison).
Or a new SAS-only experiment that repeats them. Question 2.

**Profile refresh.** After the SAS sign-off the port's profile is refreshed to the new SAS
blueprint (and to the requirements blueprint with the restated Q27). The port statements will
name, new: `logistic_no_fit`, `logit_scored_train_output_nofit`,
`logit_scored_valid_temp_nofit`; changed in value: `ks_statistic`, `decile_analysis`,
`validation_summary`, `cumulative_lift`, `model_performance_metrics`, `train_bins_precond`,
`sasPipeline`, `SasLinks`. Unchanged in type: every parameter of `sasPipeline`, so
`def:SasParams`, `def:SasLinksOf`, `def:sasPipelineOf` keep their Lean.

**Port items the SAS changes reach** (from `get_graph` and one search; whether a profile refresh
clears them by itself is still not known, question 7):

- Through `def:sasPipelineOf` (32 statement consumers, 1 proof consumer): `def:Paired`; E1 to
  E11, F2 to F6, A4; `lem:metrics_flags_reached`, `lem:metrics_score_frames`,
  `lem:sas_features_present_paired`, `lem:sas_features_shape`, `lem:sas_features_some_paired`,
  `lem:sas_reached_feature_shape`, `lem:sas_reached_scores_read_shape`; the examples
  `lem:ex_A4_metrics`, `ex_E3_fit`, `ex_E5_train_scores`, `ex_F3_final_model_output`,
  `ex_F4_model_summary`, `ex_metrics_run`, `ex_reached_features_predict`; in its proof,
  `thm:G4_metrics_coverage`.
- Through `SasLinks`: `def:SasLinksOf`, `thm:T0` (proof: the weakening helper of P1),
  `lem:ex_F4_model_summary` (proof), `lem:sas_fit_term_names`, the 20 `lem:sas_cov_*`, `thm:T2`,
  `lem:ex_T2_sas_run`.
- Naming a changed SAS unit directly: `thm:metrics_run_08_validation_summary_S21b`,
  `thm:metrics_run_09_model_performance_S22b`, `lem:metrics_ks_table`, `thm:E8_validation_summary`
  and `thm:F6_model_performance_metrics` (they spell the units), `lem:sas_cov_train_bins`.
  The search was one regex and its result was cut by size: not exhaustive.

**What the port side then has to do with the SAS items** (for the port's own specification, not
decided here):

- Level 1: E3 proves "both sides nothing" from `logistic_no_fit` and `PyLinks` 6.
- Level 2: E5, A2, F3, F4 restated; the SAS side on one outcome is N2 and N3 followed by the
  existing units.
- Level 3: E8 to E11, F5, F6, A4, G4 restated on the two score tables of a no-fit run; they need
  the lemma of 4.9 so that the SAS metrics step does not stop; S21b and S22b meet the new branch
  of C3 and C5 (their hypothesis on the KS frame decides whether the edit is mechanical).
- `lem:sas_cov_credit_raw_clean`, `lem:sas_cov_test_raw_clean`: the padded-text draft's point
  (their text says `SasLinks` does not imply the length clause; after C8 it does).

## 10. Narrowings found (the owner decides; none is taken here)

1. **A file that is not written and a header-only file are the same table.** At level 3 the
   SAS Lean says "no row" for `ks_statistic.csv`, `decile_analysis.csv`, `calibration_plot.csv`
   (not written) and for `validation_summary.csv`, `threshold_analysis.csv`,
   `model_performance_metrics.csv`, `risk_scores_validation.csv`, `model_summary.csv` (header
   only). Which files exist, and the header lines, are not represented (the convention of R39
   and R46, now carrying more). The equality proved at level 3 is of tables; that the port
   writes and omits the same files stays judge evidence. The interface (`MetricsTables`: four
   tables) cannot say more.
2. **`logistic_no_fit` is stated for complete tables with outcomes 0 or 1.** Which rows PROC
   LOGISTIC uses when a candidate is missing was not run. True on every valid run, so no
   contract gets a hypothesis; it is a stated domain of the unit.
3. **With both outcomes the fit is still taken to return a model.** After the change "no model"
   is exactly "one outcome". PROC LOGISTIC failing in another way on a two-outcome training part
   is not measured and not modelled: the rest of ruling G58, to be kept in the reports in that
   narrowed form.
4. **Clause (3) on the training score file, if K is chosen (4.8 c).** The identity read-back is
   false in letter of PROC IMPORT on the one-outcome training score file; keeping it needs
   ruling G55 extended. W avoids the narrowing at the cost of proof work.
5. **Each script in its own SAS session.** What metrics_calculation.sas does after the failed
   import depends on WORK holding no table of an earlier script: with the tables of train.sas
   still in WORK the steps would read `work.logit_scored_valid` of train.sas. All the runs cited
   are one session per script. Not stated anywhere in the SAS Lean or the rulings that I read.
6. **The leverage bound, if O2 is taken before it is located**: a precondition excluding
   1 - h between 8.56e-9 and 1.489e-8.
7. **A final parameter with variance 0**: what the units after the fit do is measured (X22, not
   yet committed) on a model given without selection. Whether the stepwise selection of
   train.sas can end there is not known. So the SAS Lean is right on such a model if the fit
   returns one, and says nothing about whether it does: the fit stays a parameter (ruling G58).
   No hypothesis is needed for it on the SAS side.

## 11. Questions for the lead

1. 4.8 c: W (weaken clause (3) for the training score file; proof work in the metrics theorems
   and T2) or K (the owner extends G55)?
2. Evidence for the translators: stage the judge runs and the SAS half of X21 under
   `legacy-to-lean/experiments`, or run them again as a SAS-only experiment (it would also give
   an all-ones training part in the kit's own record)?
3. 4.9: the lemma that the score flags hold on a no-fit run, on the port blueprint (from
   `Paired` 5) or as a new lemma of the SAS blueprint? And if it fails on the two units I did
   not read: a second disjunct in link (8)?
4. N3: an item for the validation chain without a model (recommended), or the empty table
   written in the port contracts?
5. O2: is the classification table to enter the SAS Lean (the rule only, or the whole table)?
   If not, "the port does what SAS does on leverage near 1" is evidence (X21) and no theorem.
   If yes: measure the bound first.
6. O1: correct `roc_stats`, `logistic_association`, `logistic_lackfit` in this clearing?
7. Does a profile refresh clear the port items that use the SAS declarations only through the
   profile? (Open since the padded-text draft.)
8. Narrowing 5 (one session per script): record it as a stated condition of the SAS Lean?
9. The padded-text draft's question 3 stands: run x23 part I on `MonthlyIncome` and on the test
   file before sign-off?

## 12. Risks

1. **Nothing compiled.** The changes are five one-line tests, one branch, two conjuncts and
   three small new definitions; the first submission will tell.
2. **Proofs not read.** "Mechanical" and "small" for Q12 to Q26 are expectations from the
   statements and the two drafts. A proof that unfolds `ks_statistic` or `decile_analysis` by
   `simp` with the definition name may need more than one line.
3. **The convention "no row is no table" now decides values**, not only stop flags: C1 to C3
   and C5 return no row where the same units returned rows. On a valid fitted run the validation
   table has a row, so no signed-off requirement changes; a later contract on an empty
   validation part with a model (outside valid input, G57) would meet the new values, which
   `emptyval_n2_both` and `emptyval_n3_both` support.
4. **4.9 rests on a junk model.** The score flags are true on a no-fit run through a model no
   fit returns. It is sound and matches SAS (the files exist), but a reader of link (8) will not
   expect it; the text of (8) says it (4.8 b).
5. **The clearing waits on a measurement** (section 6). X22 was read from an uncommitted
   working tree while its runs were being written up; starting before it is committed risks a
   second clearing of the definitions downstream of `Sas.Model`.
6. **Sign-off.** `def:SasLinks` gets its third revision after sign-off and five signed-off
   metrics units change in value on a case no requirement reaches.
