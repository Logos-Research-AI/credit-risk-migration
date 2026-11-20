# Update 2026-11-20: `def:model_coefficients_written` added

Blueprint `sas-credit-risk-spec` (`3f5df696-7c80-45cc-809f-b2881714663d`), by the SAS translator.
Authority: the owner's request of 2026-11-20 that P0 (predict on a run without a model) take its
SAS half from the SAS Lean. One item added; no existing item changed, cleared or resubmitted.

The Lean is in the blueprint, not in this file (this role keeps no Lean locally).

## The item

- Id `def:model_coefficients_written`, code item, state DefinitionFormalized (compiled and accepted
  on first submission; trust layers all off on this blueprint, so not judged or fuzzed).
- Code field: train.sas 419-424 (the PROC EXPORT of `work.model_coefficients`). The text and the
  Lean comment also cite 34-42 (input-file check, the script's only ABORT) and 116
  (`ods output ParameterEstimates=work.model_coefficients`). The requested citation 420-424 was
  widened to 419 to take in the comment line `/* Export model coefficients */`.
- Statement dependencies: `def:train_inputs_stop`, `def:logistic_no_fit`.
- Lean name `model_coefficients_written`; signature
  `{α : Type} [RealLike α] (features_train_exists features_validation_exists : Bool) (model_features_train : Table α) : Bool`;
  body `!(train_inputs_stop features_train_exists features_validation_exists) && !(logistic_no_fit model_features_train)`.

## Reading of the SAS

- 34-42: when either feature file is absent the script stops (ABORT CANCEL); nothing after runs.
- 71-119 / 116: the parameter table `work.model_coefficients` exists exactly when the fit fits
  something; on a training part whose present default_flag values are all equal (or none present)
  PROC LOGISTIC fits nothing and makes no parameter table (R46, `def:logistic_no_fit`).
- No step between 119 and 419 creates, replaces or deletes `work.model_coefficients`, and there is
  no other ABORT; so PROC EXPORT at 419-424 either writes the file or fails with
  "File WORK.MODEL_COEFFICIENTS.DATA does not exist" / "Export unsuccessful" and writes nothing.
  The copy of an earlier run was removed at 21-32.
- Conditions: the one-session-per-script condition (no `work.model_coefficients` left by an earlier
  script in the session), and for the fit the tables on which `def:logistic_no_fit` is stated
  (the 36 candidates and default_flag present in every row, default_flag 0 or 1). Outside them
  nothing is claimed; no precondition item added, as for `def:logistic_no_fit`.
- An intercept-only fit (no variable entered) still writes the file (A4, emptyval_n3_both: one
  Intercept row): the item does not depend on what the stepwise selection keeps.

## Evaluation (eval_decl, Float), against staged SAS runs

Input tables built from the staged `model_features_train.csv` with `eval_nofit.py` (printed, not
saved as Lean).

| Case | Flags (train, validation) | Training table | Lean | SAS |
|---|---|---|---|---|
| `staged-2026-11-18/emptyval_n3_both` | true, true | 3 rows, outcomes 1, 0, 0 | true | train.sas.log 1154: "1 records created in .../model_coefficients.csv"; file in the folder |
| same table, feature file absent | false, true | as above | false | by reading (34-42; x16, x17, x19 for ABORT CANCEL) |
| `staged-2026-11-18/x27_C60_full` | true, true | 42 rows, all default_flag 0 | false | train.sas.log 424 (fit ERROR), 1269-1270 (export ERRORs); no model_coefficients.csv |

Also consistent, not evaluated again: `x27_E60_full`, `oneclass_n60_all1` (same log lines 424,
1269-1270, no file; `logistic_no_fit` true on them per its record of 2026-11-18);
`experiments/x27_one_class_roc.log`: A4, B60, D60 (training part of both outcomes) write the file,
C60, E60 do not (`X27 ... FILE model_coefficients.csv DOES NOT EXIST`); x22_A/B/C write it
(train.sas.log 1416, 1404, 1408).

## Blocks met

`ls` of `migration/legacy-to-port/experiments/` was refused by the hook; the x27 runs were found in
this folder (`experiments/x27_one_class_roc.*`, `experiments/staged-2026-11-18/`), so the block did
not stop the work.
