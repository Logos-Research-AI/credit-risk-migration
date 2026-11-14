# Review 2 (adversarial, statement-by-statement): train.sas units

Reviewer angle: tick every SAS statement against the accepted Lean; edge inputs through
`eval_decl` with `(α := Float)`. Read-only. Blueprint `sas-credit-risk-spec`, state read on
2026-11-10. Other reviewers' reports were not read.

Note on the standing rules: the workspace `CLAUDE.md` lists this very folder as a path never to
read; `migration/prompts/common.md` gives the intended path (`.../sas-migration-formal/python`).
I followed `common.md`. Nothing outside the allowed list was opened.

## Result

| Severity | Count |
|---|---|
| WRONG | 0 |
| OMITTED | 0 |
| EXTRA | 0 |
| UNSTATED-ASSUMPTION | 5 |
| STYLE (hides meaning) | 2 |
| UNSETTLED points (no evidence either way) | 3 (inside U3, U4, U5) |

No input inside the stated or evident domain was found on which a unit's Lean and the SAS
differ. All findings concern inputs that no precondition excludes.

Preconditions that exist for these units (read): `training_metrics_precond`,
`validation_metrics_precond`, `roc_train_precond`, `roc_valid_precond`,
`logit_scored_train_output_precond`, `logit_scored_valid_temp_precond`. The other ten units
have none. (Preconditions were being added while I worked: `logit_scored_train_output_precond`
went from unformalized to formalized during the review.)

## Findings

### U1. `training_metrics`, `validation_metrics`: input columns named TP/TN/FP/FN not excluded
- Severity: UNSTATED-ASSUMPTION.
- SAS: `set work.confusion_matrix_train end=eof; retain TP TN FP FN 0;` (119-120; 181-182). A
  variable that the SET data set supplies is read on every iteration and overrides the RETAIN
  initial value.
- Lean: `foldl training_metrics.step (some 0, some 0, some 0, some 0)`; the state never reads
  the row's own `TP`/`TN`/`FP`/`FN`.
- Input: one row `default_flag=0, pred_logistic=0, COUNT=10, PERCENT=100, TP=50`.
  Lean (eval_decl): precision `.`, recall `.`, f1 `.`, accuracy 1.
  SAS: TP=50 from the data set, TN=10, so precision 1, recall 1, f1 1, accuracy 1.
- Evidence: D3 (RETAIN); the "SET overrides" part is standard PDV behaviour but has no
  experiment here. The precondition requires three columns and says nothing about these four.
  Cannot occur with the output of `Sas.freq2`. Fix: add "no column TP, TN, FP, FN" to both
  preconditions.

### U2. Ten units have no precondition for the columns and types they read
- Severity: UNSTATED-ASSUMPTION (RULEBOOK section 3: "column presence and type").
- Units: `logit_scored_train` (pd_logistic numeric), `confusion_matrix_train`,
  `confusion_matrix` (default_flag, pred_logistic numeric), `logit_scored_valid`
  (predicted_logit numeric), `risk_scores_train`, `risk_scores_validation` (pd_logistic
  numeric; no existing shorter character `risk_grade`/`recommendation`), `final_model_output`,
  `model_summary` (ROCModel character, Area and the eight metrics numeric and present in every
  row), and the two `_clean` units (nothing needed).
- Example: `confusion_matrix_train` on `[default_flag = Cell.str "1", pred_logistic = 1]`:
  Lean gives the level `default_flag = .` with COUNT 1 (eval_decl); SAS tabulates the character
  level `'1'`.
- Example (names): Lean matches names by exact case, SAS ignores case. `logit_scored_valid` on
  a column `Predicted_Logit = 2`: Lean gives pd_logistic `.`, pred_logistic 0 and keeps the
  column (eval_decl); SAS gives 0.8808, 1 and drops it. Only the `_clean` units upper-case.
  Inside the pipeline the upstream Lean always writes the expected spelling, so this needs only
  a stated convention or preconditions.

### U3. `confusion_matrix_train`, `confusion_matrix`: PROC FREQ levels are formatted values
- Severity: UNSTATED-ASSUMPTION, SAS side UNSETTLED in this workspace.
- SAS: `tables default_flag * pred_logistic / out=...` (110, 172). PROC FREQ forms levels from
  formatted values (BEST12. here), so two numbers that print alike are one level.
- Lean: `Sas.freq2` groups by exact value (`Sas.eq`).
- Input: default_flag values `0.1+0.2` and `0.3` with the same pred_logistic: Lean two rows,
  SAS (by the general PROC FREQ rule) one row. D7 only covers ORDER=INTERNAL for ordering; X13
  uses integers. Harmless for 0/1 flags; needs a precondition "default_flag is missing, 0 or 1"
  (as the roc preconditions already state) or an experiment.

### U4. `logit_scored_valid_temp_precond` allows what `logit_scored_train_output_precond` excludes
- Severity: UNSTATED-ASSUMPTION, SAS side UNSETTLED.
- SAS: `proc plm restore=work.logit_model; score data=... predicted=predicted_logit;` (151-155).
- Lean: `Sas.linpred model r` reads only the selected terms. Row `a=2, b=1, c=.` with model
  terms a, b gives predicted_logit -2 (eval_decl) although `c` is missing.
- The train precondition demands every numeric cell present, with the comment that a missing
  MODEL candidate that was not selected is "not settled by the evidence". The same question is
  open for PROC PLM after a stepwise fit (D13 caveat: PLM with a missing covariate is not
  documented; X15C had no unselected candidate), but the validation precondition only asks for
  numeric cells on the model terms. Either both exclude it or the PLM case gets an experiment.
  The reference features have no missing cell (checked: 0 of 105000 and 0 of 45000 rows).

### U5. `logit_scored_train_output`: `_LEVEL_ = 1` assumes the event level is the number 1
- Severity: UNSTATED-ASSUMPTION, partly UNSETTLED (already marked OPEN for type and position).
- SAS: `proc logistic ... descending; model default_flag = ...; output out= predicted=` (48-87).
  `_LEVEL_` holds the modelled level, the highest value of default_flag (D13).
- Lean: `Sas.setNum r "_LEVEL_" (some 1)` for every row; the precondition does not require
  default_flag to be 0/1. With levels {0, 2} SAS writes 2. Not visible in any export
  (`_LEVEL_` is dropped at 328 and not kept at 354); visible only in this unit's own table.
- Also: the header comment says pd_logistic is computed "also when default_flag is missing",
  while the precondition now forbids any missing numeric cell. Not a difference, but the two
  texts disagree about the domain.

### S1. `roc_train`: tolerance constant differs from RULEBOOK R25, and a stale OPEN comment
- Severity: STYLE (hides meaning).
- R25 says "within 1e-8". Lean `rocTops` uses `1.0536712127723509e-8` (sqrt of 2^-53) and
  justifies it by 280 tied pairs in `printed_association.csv`. I reproduced that from
  `risk_scores_train.csv`: 280 tied pairs with sqrt(2^-53), 275 with 1e-8; Area 0.859221 and
  0.856422, matching the printed 0.8592 / 0.8564 and c = 0.859221. The CSV probabilities carry
  10 digits, so this is strong but not bit-level evidence, and the 280 comes from the fit step's
  Association table, not from a ROC statement.
- The comment still reads "OPEN(port): whether a gap of exactly 1e-8 joins the group", which no
  longer describes the code (the boundary is now at the new constant, join on `<=`, as D10
  "does not exceed").
- See Amendments.

### S2. `model_summary`: ROCModel is truncated in SAS, not in Lean (never visible)
- Severity: STYLE / note.
- SAS log line 1255: "Multiple lengths were specified for the variable ROCModel". The PDV length
  is 12 (from roc_train), so the merged value is `Validation S`; Lean carries `Validation Set`.
  WHERE= is applied before the read and KEEP drops ROCModel, so no output differs. Worth one
  comment line in the unit, since R12 claims "no value in this code is truncated".

## Statement checklists (all ticked unless noted)

`logit_scored_train_output` (85-87): one row per input row, input order; `_LEVEL_` then
`pd_logistic` appended (log evidence: no "never been referenced" warning for `_LEVEL_` at 328,
warning at 334: confirmed in `train.sas.log` lines 636-650); `linpred` left to right; missing
covariate gives missing; `invLink` parameter (P5); overflow through `Sas.fin`. See U5.

`logit_scored_train` (103-105): `pred_logistic = (pd_logistic >= 0.5)` is
`ofBool (ge pd 0.5)`. eval: 0.5 gives 1; 0.49999999999999994 gives 0; missing gives 0; existing
pred_logistic overwritten in place. No finding beyond U2.

`confusion_matrix_train` (109-111), `confusion_matrix` (171-173): columns default_flag,
pred_logistic, COUNT, PERCENT (header of `printed_confusion_*.csv`); rows sorted, missing first;
missing-level row kept with PERCENT missing and excluded from N (X13 `freq` lines);
`100 * c / N` (X13 freq3/freq4); zero rows give zero rows. eval on 8 rows with one missing
default_flag: PERCENT 71.43/14.29/14.29 over N = 7. Reference: 100*1418/105000 = 1.3504761905.
Findings U2, U3.

`training_metrics` (118-139), `validation_metrics` (180-201):
- SET ... END=eof: fold plus `getLast?`. Zero rows give `[]` (R22).
- RETAIN TP TN FP FN 0: initial state four zeros; an absent cell stays 0.
- IF chain order (1,1) TP, (0,0) TN, (0,1) FP, (1,0) FN: same order in Lean, each assigns
  COUNT. A row with missing default_flag or pred_logistic = 2 changes nothing (eval).
- eof block order: precision, recall, f1, accuracy; guards `(TP+FP) > 0`, `(TP+FN) > 0`,
  `(p+r) > 0`, `(TP+TN+FP+FN) > 0` with `((TP+TN)+FP)+FN`; else-branches assign missing;
  `2 * (p * r) / (p + r)` grouped as written.
- KEEP: four names in PDV order; matches `model_summary.csv` columns 3-6 and 7-10.
- The two SAS steps differ only in the input name and the `train_`/`valid_` prefixes; the two
  Lean bodies likewise (each written out, no shared helper).
- eval: reference cells give 0.578068 / 0.202340 / 0.299757 / 0.936905 and 0.569014 / 0.200795
  / 0.296841 / 0.936200 (reference 0.5781 0.2023 0.2998 0.9369; 0.5690 0.2008 0.2968 0.9362).
  Only TN: precision, recall, f1 missing, accuracy 1. Only FN: precision missing, recall 0, f1
  missing, accuracy 0. Only FP: precision 0, recall missing, f1 missing. COUNT missing in the TP
  cell: all four missing.
- Finding U1.

`logit_scored_valid_temp` (151-155): predicted_logit appended, linear predictor, no `_LEVEL_`
(log warning at 334 agrees). Finding U4.

`logit_scored_valid` (158-168): `1 / (1 + exp(-predicted_logit))` is
`div 1 (add 1 (exp (neg x)))`, no reassociation; then pred_logistic; DROP applied last, to the
output row only. eval: 0 gives 0.5 and 1; missing gives missing and 0; -710 (EXP overflow)
gives missing and 0; 800 gives 1 and 1; +-1e-17 gives 0.5 and 1. No finding beyond U2.

`risk_scores_train` (213-244), `risk_scores_validation` (247-275): constants 600, 250, `1 -
pd`, ROUND; 750/700/650/600/550 all `>=`, A to F; IN ('A','B') Approve, 'C' Review, else
Decline; 0.05; A base_rate, B +0.02, C +0.04, D +0.07, E +0.10, else +0.15, each added at run
time (not folded). New variables in order base_score, score_range, credit_risk_score,
risk_grade, recommendation, base_rate, interest_rate: equal to the CSV headers. The SAS steps
differ only in comments and the input name; the Lean bodies are separate and identical apart
from comments. eval, both units, 18 probabilities: thresholds exact at pd 0.4/0.6/0.8/1.0/1.2
(750 A, 700 B, 650 C, 600 D, 550 E); half-way cases 0.402, 0.602, 0.802, 1.002, 1.202 round up
to the threshold; missing gives score missing, F, Decline, 0.20; reference rows 0.0215012376
gives 845 and 0.0537071796 gives 837. Whole reference files re-derived from their own
pd_logistic with the SAS rule: 0 inconsistent rows of 105000 and 45000. No finding beyond U2.

`roc_train` (293-298), `roc_valid` (301-306): label text, columns ROCModel and Area only
(documented omission; `printed_roc_*.csv` has one row each, so no extra "Model" row with
NOFIT); rows with a missing response or probability dropped; X15B r6 replayed gives 0.587912
(log: 0.58791208791208). No event or zero rows give a row with Area missing where SAS gives no
table: excluded by both preconditions. Finding S1.

`risk_scores_train_clean` (326-329), `risk_scores_validation_clean` (332-335): eval with
columns `_LEVEL_, ip_1, IP_0, Xp_1, _from_, _Into_, IP_` dropped and `IP, XIP_1, _LEVEL,
_FROM_X` kept, order of the rest unchanged. Exactly the DROP list, case-insensitive. No finding.

`final_model_output` (352-358): 13 names equal to lines 354-357; KEEP does not reorder; eval
output order equals the header of `final_model_output.csv`. No finding beyond U2.

`model_summary` (367-386): WHERE= on the original name before RENAME=; Area renamed per input;
four assignments in source order; KEEP list has the 14 names of lines 382-385; eval output
order Train_AUC, Valid_AUC, 4 training, 4 validation, model_name, training_date,
training_records, validation_records equals the header of `model_summary.csv`. Zero rows:
training_metrics empty gives one row with the four train metrics missing; a WHERE= that selects
nothing gives a missing Train_AUC; all four empty (or roc_train non-matching and the rest
empty) gives no row (X13 `merge`, `merge_empty`; X15A). Finding S2.

## Amendments proposed

- R25: replace "within 1e-8" by the constant actually used (sqrt(2^-53) =
  1.0536712127723509e-8) with its evidence, or revert the Lean to 1e-8; update the OPEN note to
  the real open point (boundary at exactly the constant; evidence is 10-digit CSV data).
- R12: the claim "no value in this code is truncated" has one exception, ROCModel in the
  `model_summary` merge (never output).
- Section 3: say whether column-name case is a convention of every table or a precondition per
  unit (U2), and whether "numeric flag columns are 0/1" is assumed by the PROC FREQ units (U3).
- R26 / D13: add an experiment for a missing unselected MODEL candidate, for PROC LOGISTIC
  OUTPUT and for PROC PLM SCORE (U4).
