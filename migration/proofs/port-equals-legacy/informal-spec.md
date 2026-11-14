# Informal specification: what the Python port must satisfy

Version 2.3, 2026-11-13. Version 1 was the basis of proving round 1 and version 2 of round 2.
Version 2.1 followed the code changes made on round 2's findings and was the basis of round 3.
Version 2.2 closed the gaps round 3 found and was the basis of round 4. Version 2.3 follows the
audit; section 9 says what round 5 does.

Each contract is a statement about one item of the Logos blueprint `py-credit-risk-port`. It is a
postcondition on that item, with this text as its informal statement. The SAS definitions it
mentions come from `sas-credit-risk-spec`, pinned through the profile.

The contracts restate, as things that can be proved, what the migration committed to in writing:

| Source | What it fixed | Becomes |
|---|---|---|
| `judge/README.md`, "Contract" and "Comparison policy" | per stage: same files, columns, column order; rows matched by key | stage contracts (section 3) |
| `migration/RULEBOOK.md` §2 | one canonical Python form for each SAS construct | helper contracts (section 4) |
| `migration/inventory.tsv` (193 rows) | per site: the translation, and whether an operand can be missing | step contracts and input domains (sections 2 and 5) |
| RULEBOOK "BUG rule", `post-parity/classification.md`, `bugfix-1/3/4.md` | bugs reproduced by default; three fixes behind flags; rows closed as unreachable | flag and closed-row contracts (sections 6 and 7) |
| `MODEL_CARD.md`, judge README "Findings" | what the pipeline was meant to do | intent contracts (section 8) |

## What changed from version 1, and why

Round 1 stated 117 contracts: 53 proved, 61 disproved, 3 open. Many disproofs were caused by
version 1, not by the port: its domains admitted inputs no pipeline produces (an extra column
named `median_income`, a missing `row_id`, a probability of -3999999999, an empty frame, a format
function returning empty text). Version 2 changes five things.

1. **Contracts are over the real numbers.** That is the design of the shared number class:
   each Lean translation was checked against its source at `Float` when it was written, and the
   two translations are compared by proof at `ℝ`. Version 1 asked for "every number type" first;
   that aim is dropped.
2. **Domains are well-formed pipeline inputs** (section 2), so that a disproof is about the port.
3. **Stage contracts are stated per output file**, so one difference does not hide the rest.
4. **Two shape differences are stated away**: the `_LEVEL_` column, and ROC units of which the
   SAS side models two columns (section 5).
5. **Parameter links exclude degenerate parameters** (section 1).

Results of round 1 that version 2 does not restate stand as they are. Section 9 lists, contract by
contract, what round 2 must do.

## 1. Form of every contract

**Equivalence.** "At the real numbers, for every input in the stated domain, with all flags off,
the Python unit's result, as a table, equals the SAS unit's result on the same input":
`Pl.toTable (python f) = sas (Pl.toTable f)` with `α = ℝ`.

A contract that fails is disproved with a concrete input, which goes in the contract text. Nothing
is claimed about `Float`: overflow, NaN and summation order are outside these contracts.

**Parameters.** Each side left some behaviour as an explicit input. They may be linked only so:

| SAS side | Python side | Link |
|---|---|---|
| `arrange` (join order; the judge matches rows by key because SAS guarantees none) | the join keeps the left order | existential: there is an order for which they agree |
| `agg` (PROC SQL summation, unknown order) | polars summation, modelled | `agg.sum` and `agg.mean` are the sum and the mean of the list |
| `best8` | `sas_best`, `parse_float` | `parse_float (sas_best x 8) = best8 x` for every present `x`; the text is never empty for a present value, and is empty for a missing one |
| the SAS unit's own BEST8. rule for counts (`total_good_bad`) | `sas_best`, `parse_float` | for a whole number `n` with `0 ≤ n < 10^8`: `parse_float (sas_best n 8) = n`, and the text is never empty |
| `model` | `intercept`, `coefficients`; `stepwise.final` | same intercept, same (name, coefficient) list in the same order |
| `invLink` (PROC LOGISTIC's own probability, unknown) | the Python expression | hypothesis; the contract is labelled *conditional* |
| `today` | `today` | the same date |
| `credit_split` | `split_ids` | the selected rows are those whose `row_id` is listed; `Selected` is 0 or 1 on every row |
| none | `full` (thread-dependent order of polars horizontal sums) | must hold for both values |
| none | `input_best32` | hypothesis: equals the SAS unit's conversion; CSV parsing is a later pass |

No other hypothesis may be added. A contract that cannot be proved or disproved as written is left
open and reported.

## 2. Domains

### Well-formed inputs

Every contract assumes its input is well formed. For a stage, the input tables are well formed
when:

- each has at least one row and fewer than 10^8 rows;
- its columns are exactly those of the stage's input file, by name, order and kind (number or
  text); in particular none carries the name of a column the stage creates;
- `row_id` (`VAR1` in a raw file) is present on every row and no two rows share it;
- where the table carries them: `pd_logistic`, when present, lies in [0, 1], and `default_flag`,
  when present, is 0 or 1.

For a step inside a stage, the input frame is well formed when it has exactly the columns, in
order and kind, that the preceding Python steps produce from a well-formed stage input, and at
least one row. It also has what those steps guarantee about its cells: `row_id` present on every
row; `age_group` present in the frames of step 04, and in the medians frame, which may have no
row at all; `pred_logistic` 0 or 1 wherever a step created it; `default_flag`, when present, 0 or 1 wherever a
frame carries it. Its rows are in the order the preceding step returns them: `decile_analysis`
is in ascending `decile` order. A table supplied from outside (the medians table of `fix_train_medians`) is well
formed when it has exactly the age groups 1 to 5, once each.

### The migration's "never missing" claims

The rulebook allows a plain polars comparison only where the inventory proves the operand is
never missing "for every input the program can receive" (amendment A2). 91 of the 193 inventory
rows make that claim, with the judged files as evidence. The domains state those claims as
conditions on an arbitrary well-formed input.

| Domain | Conditions beyond well-formedness | Inventory rows |
|---|---|---|
| `D_fe` (raw training table) | `age`, utilization, debt ratio, the three late-payment counts and the credit-line count are present; every age group has at least one present income | 8, 13 to 41 |
| `D_predict` (raw test table) | as `D_fe`, except that income may stay missing after imputation | 152 to 187 |
| `D_train` (feature tables) | no model variable is missing; both outcomes occur | 46, 58, 61 to 73, 82, 83 |
| `D_metrics` (score tables) | `pd_logistic` and `default_flag` present; both outcomes occur | 101, 110 to 121, 127 to 136 |

Round 1 showed that non-negativity of the counts, which version 1 also assumed, is never used. It
is removed.

Every step contract has two parts:

- **(a) on the domain**: the claim the migration made.
- **(b) on every well-formed input**, without the "never missing" conditions: either it still
  holds, or the witness shows what the port does on an input nobody tested.

## 3. Stage contracts

One contract **per output file**. Each says: the file's rows, column names and column order equal
those the composed SAS units give, rows matched by `row_id` where the file has one. Printed
formats, the `printed_*` files and the model fit are later passes.

| # | On | Files | Domain and links |
|---|---|---|---|
| ST1 | `run` (feature engineering) | `model_features_train.csv`, `model_features_validation.csv` | `D_fe`, split link, `input_best32` |
| ST2 | `run_py_py_py` (train) | `risk_scores_train.csv`, `risk_scores_validation.csv`, `final_model_output.csv`, `model_summary.csv` | `D_train`, model link, `invLink`, `today`. The stage's own precondition covers out-of-scope steps (classification table, Hosmer-Lemeshow); it is assumed, with one input shown to meet it |
| ST3 | `run_py` (metrics) | `validation_summary.csv`, `decile_analysis.csv`, `threshold_analysis.csv`, `ks_statistic.csv`, `calibration_plot.csv`, `model_performance_metrics.csv` | `D_metrics`, `agg`, both text links, `today` |
| ST4 | `run_py_py` (predict) | `kaggle_submission.csv`, `test_predictions.csv` | `D_predict`, model link, `input_best32` |

A file that differs only through a finding already established at step level is disproved with
that finding's witness, and the text names the step contract.

### Witness contracts

A stage contract assumes the Python stage's own precondition, well-formedness, a domain and
parameter links. If no input met all of them at once the contract would be true and empty. So
each stage has one more contract:

| # | On | Statement |
|---|---|---|
| W1 | `run` | There are a raw training table, a split and parameters that meet every hypothesis of the ST1 contracts |
| W2 | `run_py_py_py` | There are two feature tables and parameters that meet every hypothesis of the ST2 contracts, `model_summary.csv` included |
| W3 | `run_py` | There are two score tables and parameters that meet every hypothesis of the ST3 contracts, the row bounds included |
| W4 | `run_py_py` | There are a raw test table, a model and parameters that meet every hypothesis of the ST4 contracts |

Each is proved at the real numbers, on a concrete small input. Parameters that stand for
out-of-scope code (linear algebra, format functions) may be any functions that meet the
hypotheses; the contract says nothing about the real ones.

## 4. Helper contracts

One per row of RULEBOOK §2 that is in scope: the `sas_compat` helper computes the SAS rule the SAS
side established from evidence.

| # | On | Statement (RULEBOOK §2 row) | Round 1 |
|---|---|---|---|
| H1 | `lt`, `le`, `gt`, `ge`, `eq` | A missing value is smaller than every number and equal to itself; the result is never missing | proved |
| H2 | `flag` | A Boolean becomes the number 0 or 1 | proved |
| H3 | `div` | Element-wise division; a missing operand or a zero divisor gives missing | proved |
| H4 | `sas_sum` | Missing arguments are ignored; all missing gives missing; both values of `full` | proved |
| H5 | `sas_min`, `sas_max` | Missing arguments are ignored | proved |
| H6 | `sas_log` | Zero, negative or missing gives missing | proved |
| H7 | `sas_exp` | Overflow gives missing | proved |
| H8 | `sas_round` | Half away from zero, with SAS's tolerance; unchanged at or above 2^52 | disproved: a finding |
| H9 | `sql_sum`, `sql_mean`, `sql_min`, `sql_max` | Missing over zero rows or an all-missing input | proved |
| H10 | `merge_one_to_one` | Rows as the longest input; shorter inputs give missing on the extra rows. Columns that share a name across inputs have the same kind (SAS rejects a variable that is both character and numeric) | disproved: a finding |
| H11 | `proc_rank_groups` | Ties get the mean rank; group is floor(rank × k / (n + 1)) | proved |
| H12 | `roc_association` | For a response that is 0 or 1 on every row and both outcomes present: Area is the SAS area, SAS's tie rule included | restate |
| H13 | `confusion_metrics` | On a frame with at least one row: equals the SAS unit `confusion_metrics_macro` for one threshold | restate |

## 5. Step contracts

One per Python step, against the SAS units it covers, in the two parts of section 2. Three
conventions apply:

- **Row order of the medians tables.** `income_medians` and `test_income_medians` are only ever
  joined on their key, and SAS fixes no order for them. S2 and S24 compare them as sets of rows.
  That Python lists groups in order of first appearance and the SAS translation in ascending
  order is recorded once, as a note on S2.
- **`_LEVEL_`.** The SAS scored training table carries a `_LEVEL_` column that PROC LOGISTIC
  creates and the export drops; the port never creates it. S7 compares all columns except
  `_LEVEL_`. A well-formed Python frame has no such column (section 2), which settles S13.
- **ROC columns.** The SAS ROC units model two of the eight columns the Python frames carry. S12
  and S14 compare those two columns.

| # | On | SAS unit(s) | Rows | Round 2 |
|---|---|---|---|---|
| S1 | `fe_run_01_clean` | `credit_raw_clean` | 4, 5 | stands |
| S2 | `fe_run_02_income_medians` | `income_medians` | 6, 7 | restate (a) as sets of rows; (b) stands |
| S3 | `fe_run_03_cleaned` | `credit_cleaned` | 8 to 10 | stands |
| S4 | `fe_run_04_imputed` | `credit_imputed` | 11, 12 | restate (a) and (b) on well-formed frames |
| S5 | `fe_run_05_features` | `credit_features` | 13 to 41 | stands |
| S6 | `fe_run_06_split` | `credit_train_validation`, the two exports | 42 to 44 | restate (a) and (b) |
| S7 | `train_run_04_score_train` | `logit_scored_train_output` | 57 | restate, without `_LEVEL_` |
| S8 | `train_run_09_confusion_train` | `logit_scored_train`, `confusion_matrix_train`, `training_metrics` | 59 to 70 | (a) stands; restate (b) |
| S9 | `train_run_10_score_valid` | `logit_scored_valid_temp`, `logit_scored_valid` | 72 to 74 | stands |
| S10 | `train_run_11_confusion_valid` | `confusion_matrix`, `validation_metrics` | 75 to 80 | restate (a) and (b) |
| S11 | `train_run_12_risk_scores` | `risk_scores_train`, `risk_scores_validation` | 58, 82 to 84 | restate (a) and (b): the probability is in [0, 1] or missing |
| S12 | `train_run_13_roc` | `roc_train`, `roc_valid` | 88, 89 | restate on the two columns |
| S13 | `train_run_14_final_and_summary` | the two `_clean` units, `final_model_output`, `model_summary` | 85, 86, 91 to 96 | restate |
| S14 | `metrics_run_01_roc_auc` | `roc_stats`, `auc_summary` | 100 to 104 | restate on the two columns |
| S15 | `metrics_run_02_ks` | `logit_scored_valid_sorted`, `total_good_bad`, `ks_calculation`, `ks_statistic` | 106 | sorted part stands; restate the KS part with the count link |
| S16 | `metrics_run_03_thresholds` | `threshold_analysis` | 107 to 123 | (a) stands; restate (b) |
| S17 | `metrics_run_04_deciles` | `decile_data`, `decile_analysis` | 124, 125 | stands |
| S18 | `metrics_run_05_cumulative_lift` | `total_defaults`, `cumulative_lift` | 126 to 132 | restate (a) and (b) |
| S19 | `metrics_run_06_psi` | `train_bins`, `valid_bins`, `psi_calculation`, `psi_summary` | 133, 134 | stands |
| S20 | `metrics_run_07_calibration` | `calibration_data`, `calibration_plot` | 135 to 137 | stands |
| S21 | `metrics_run_08_validation_summary` | `validation_summary` | 138, 139 | (a) stands; restate (b) |
| S22 | `metrics_run_09_model_performance` | `model_performance_metrics` | 142 to 144 | (a) stands; restate (b) |
| S23 | `predict_run_01_clean` | `test_raw_clean` | 148 to 150 | stands |
| S24 | `predict_run_02_medians` | `test_income_medians` | 151 to 154 | restate (a) as sets of rows; (b) stands |
| S25 | `predict_run_03_cleaned` | `test_cleaned` | 155 to 157 | restate (a); (b) stands |
| S26 | `predict_run_04_imputed` | `test_imputed` | 158 to 161 | restate (a) and (b) |
| S27 | `predict_run_05_features` | `test_features` | 162 to 187 | stands |
| S28 | `predict_run_06_score` | `test_scored_temp`, `test_scored` | 188 | stands |
| S29 | `predict_run_07_predictions` | `test_predictions` | 189 | restate: the probability is in [0, 1] or missing |
| S30 | `predict_run_08_outputs` | `kaggle_submission`, `test_predictions_full` | 190 to 193 | restate on well-formed frames |
| S31 | the predict steps against their feature-engineering twins | | | stands. The copies differ in `flag_low_income` (with `total_risk_flags`), and in `default_flag`, which only the training copy carries |

## 6. Flag contracts

| # | Flag | On | Frame | Round 2 |
|---|---|---|---|---|
| F1 | `fix_psi_bins` (bugfix-4) | Validation rows are binned by the training groups: a value goes to the highest training group whose start is at most the value, and below all of them to the lowest group present. A training bin with no validation rows keeps a share of 0 and its term uses both shares floored at 1e-4. The validation shares sum to 1 | The cells that change are the PSI cells and the cells computed from PSI (`PSI_interpretation`, `status`); every other cell of every output is identical with the flag on and off | settle "on"; restate the frame. Round 1 disproved the frame as bugfix-4 states it ("only PSI cells"): that result stands as a finding against the record |
| F2 | `fix_train_medians` (bugfix-3) | Test incomes are imputed from the medians supplied, not from the test set | With a well-formed medians table, only rows whose income was missing change | "on" stands; restate the frame |
| F3 | `export_train_medians` | One more file, the medians, first; the two judged files unchanged | | stands |
| F4 | `fix_income_truncation` | The Python Lean keeps the flag and ignores it: it changes only the CSV import, out of scope | | stands |

## 7. Closed rows

| # | Row | Closed as | Contract | Round 2 |
|---|---|---|---|---|
| C2 | 14 | degenerate ROC inputs "return missing, not a crash" | on a single-class input every statistic of `roc_association` is missing | disproved (`TauA` is 0): stands, a finding against the record |
| C3 | 16 | a model variable absent at scoring raises an error | precondition of `predict_run_06_score`: every coefficient name is a column | stands |
| C4 | 11 | rows with a missing model variable are excluded from the fit | the mask keeps exactly the rows with no missing candidate | disproved (a missing `default_flag` also drops the row): stands, a finding against the record |

## 8. Intent contracts

Stated on the Python item. "Fails" is proved as the negation, with a witness.

| # | Property | On | Round 2 |
|---|---|---|---|
| I1 | PSI is zero exactly when the two score distributions agree on the bins | `metrics_run_06_psi` | "off" stands, with its text corrected: PSI is 0 on untied tables of equal size whatever the shift. Settle "on": round 1 suspects it false when the differing bins sit at or below the 1e-4 floor. State that as a general lemma about the floored terms, which needs no large table |
| I2 | Test incomes are imputed with the training medians | `predict_run_02_medians` | stands |
| I3 | A risk flag is set only when its variable is present and beyond its threshold | both feature steps | stands |
| I4 | A capped variable equals the original below the cap; after imputation every applicant has an income | `fe_run_05_features`, `fe_run_04_imputed` | stands |
| I5 | The score lies in 300..850 and each grade is its model-card probability band | `train_run_12_risk_scores` | stands |
| I6 | A row whose probability is missing is not predicted "no default" | `predict_run_07_predictions` | stands |
| I7 | `ks_statistic` has exactly one row | `metrics_run_02_ks` | restate on `D_metrics`: the witness must be a well-formed table on which the maximum is attained twice |
| I8 | The feature engineering applied to the test set is the one applied to the training set | S31 | stands |

## 9. What round 5 does

After round 4 all fourteen stage files are proved and no difference between the port and SAS is
left. Round 5 is small.

- **State and prove W1 to W4** (section 3). Rounds 2 to 4 showed that the stage hypotheses can be
  met by evaluating hand-written checks at `Float`; these four replace that with proofs.
- **Restate S12(a), S12(b) and S18(b)** with the two step-frame guarantees section 2 now gives
  (`default_flag` 0 or 1; `decile_analysis` in ascending order). All three are expected to hold.
- **Leave alone** everything else.

## 10. Not covered in this pass

- CSV import and type guessing (`proc_import_csv`, `input_best32`): the income truncation lives here.
- Printed formats and the `printed_*` files.
- The model fit: stepwise selection, the optimiser, and the PROC LOGISTIC tables.
- The Hosmer-Lemeshow and association tables: the SAS side leaves their arithmetic open.
- The other six columns of the ROC table (standard error, confidence limits, Somers' D, Gamma,
  Tau-a): SAS and the port differ there under near ties, and the SAS side has no rule for them.
- The edge scenarios' score files have three columns, not the stage's 51, so the metrics stage
  contracts do not cover them literally.
- Floating-point behaviour: overflow, NaN and summation order. Each translation was checked
  against its source at `Float`; the judge's tolerance covers last-place differences.
