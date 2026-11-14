# Review 1: train.sas units (adversarial, read-only)

Scope: `logit_scored_train_output`, `logistic_association`, `logistic_lackfit`, `logit_scored_train`,
`confusion_matrix_train`, `training_metrics`, `logit_scored_valid_temp`, `logit_scored_valid`,
`confusion_matrix`, `validation_metrics`, `risk_scores_train`, `risk_scores_validation`, `roc_train`,
`roc_valid`, `risk_scores_train_clean`, `risk_scores_validation_clean`, `final_model_output`,
`model_summary`, and the precondition items that exist for them (`training_metrics_precond`,
`validation_metrics_precond`, `roc_valid_precond`; no other `_precond` item exists for these units).

Counts: WRONG 1, OMITTED 2, UNSTATED-ASSUMPTION 3, EXTRA 0, UNSETTLED notes 3, STYLE 2.

How things were checked
- Lean read from `get_items`; SAS from `train.sas`.
- `eval_decl` on `Sas.round` (42 inputs), `Sas.rocArea` (X15B r1-r4, r6, plus boundary probes),
  `Sas.freq2` (X13 `freq` data), `training_metrics` (6 inputs), `model_summary` (6 inputs),
  `logistic_lackfit` and `logistic_lackfit.groups`, `logistic_association` (X15D input built from the
  log by script: 16 distinct probabilities, 1000 rows).
- An independent Python implementation of the rules (not the Lean) run on `judge/reference/
  risk_scores_train.csv` and `risk_scores_validation.csv` (150,000 rows) and compared with the
  reference tables. Caveat for everything derived from those CSVs: `pd_logistic` is printed with at
  most 10 significant digits.
- Limit: `Sas.Eval.apply` is not callable from `def:logistic_association` (`eval_decl` returns
  `success:false`), so association values from the Lean were compared at the 6 decimals `eval_decl`
  prints, not to the bit. My Python version of the same formulas is bit-exact on all 8 `X15D assoc`
  values, and the Lean's operation order is the same, read line by line.

---

## Findings

### F1. WRONG: tie tolerance `1e-8` in `Sas.rocTops` (R25), used by `logistic_association`, `roc_train`, `roc_valid`

- SAS: train.sas 48-96 (Association table), 293-306 (ROC statements). D10: ROCEPS default is "the
  square root of the machine epsilon, which is about 1E-8".
- Lean: `if (1e-8 : α) < top - p then p :: acc else acc`.
- Evidence against `1e-8`: `judge/reference/printed_association.csv` has Percent Tied 0.000040773 of
  686,727,936 pairs, which is 280 tied pairs (judge/README.md states the same SAS count, 280).
  The R25 rule with 1e-8 applied to the reference `pd_logistic` values gives 275 tied pairs
  (Percent Tied 0.000040045). The count as a function of the tolerance (top-anchored scan):
  1.00e-8 -> 275, 1.03e-8 -> 276, 1.0402e-8 -> 278, 1.05e-8 -> 279, 1.0502e-8 -> 280,
  1.0602e-8 -> 281, 1.49e-8 -> 310. `sqrt(2^-53) = 1.0536712e-8` gives exactly 280. The result is
  the same for a bottom-anchored scan, a chained scan and a pairwise test, so the scan direction is
  not what is off; the constant is. CSV rounding moves a difference by at most 1e-10, and the five
  pairs in question sit 3e-10 to 5e-10 above 1e-8, so rounding does not explain it.
- X15B does not contradict this: its near-tie cases only bound the tolerance to [0.6e-8, 1.2e-8).
- Concrete input: one event at p = 0.5 and one non-event at p = 0.5 + 1.03e-8.
  Lean (`eval_decl`, `Sas.rocArea`): `some 0.000000` (not tied, discordant).
  SAS with tolerance sqrt(2^-53): tied, Area 0.5, Percent Tied 100. The SAS side of this small input
  is inferred, not run: UNSETTLED for the ROC statement itself until an experiment with gaps of
  1.03e-8 and 1.08e-8 is run. For the Association table the reference data settles it (275 vs 280).
- Effect: `logistic_association` nValue1 (Tied, and Concordant/Discordant by the moved pairs), and c,
  Somers' D, Gamma, Tau-a in their last digits; `Area` of `roc_train`/`roc_valid` and hence
  `Train_AUC`/`Valid_AUC` in `model_summary` at bit level.

### F2. OMITTED: `_LEVEL_` in `logit_scored_train_output` (and so in `logit_scored_train`, `risk_scores_train`)

- SAS: train.sas 86-87, `output out=work.logit_scored_train predicted=pd_logistic;`. D13 caveat:
  "the data set also contains a variable named _LEVEL_".
- Evidence that it exists here: `judge/reference/listings/train.sas.log`. After the DROP at source
  line 1529 (training set) there are four warnings: `IP_:`, `XP_:`, `_FROM_`, `_INTO_`. After the DROP
  at 1535 (validation set) there are five: the same four plus `_LEVEL_`. So `_LEVEL_` is a variable
  of `work.risk_scores_train` and is absent from `work.risk_scores_validation`.
- Lean: `Sas.setNum r "pd_logistic" ...` only. Output columns are the input columns plus
  `pd_logistic`.
- Difference on any non-empty input: SAS's `logit_scored_train` (both versions), and
  `risk_scores_train`, carry `_LEVEL_`; the Lean tables do not.
- Not visible in any exported file: `risk_scores_train_clean` drops it, `final_model_output` does not
  keep it, PROC FREQ and the ROC step do not read it.
- The comment in `risk_scores_train_clean` is false: "No such variable exists in risk_scores_train
  (the SAS log warns), so the table is unchanged". The log does not warn for `_LEVEL_` on the
  training set, and the SAS step does remove a column there. The Lean code of that unit is right
  (it would drop `_LEVEL_` if present); only its upstream and its comment are wrong.
- UNSETTLED: the type, value and position of `_LEVEL_` (expected: before `pd_logistic`, holding the
  event level). No experiment prints it; X15C's `fo` could be printed with PROC CONTENTS.

### F3. UNSTATED-ASSUMPTION: `logistic_lackfit` leaves `sameBlock` free, and the evidence fixes it

- SAS: train.sas 83 (`lackfit`). Lean: `sameBlock : α → α → Bool` is a parameter, with the comment
  "The documentation says identical; judge/README.md reports ... within about 1e-6. Both reproduce
  X15C and X15D."
- With exact equality (the instance suggested for testing), the rule does not reproduce SAS on the
  reference data. Reference `printed_hl_partition.csv` (Total / EventsObserved):
  10498/46, 10502/76, 10501/107, 10502/134, 10499/144, 10500/310, 10500/453, 10501/725,
  10500/1276, 10497/3737.
  Same algorithm, `sameBlock p q := p == q`, on reference `pd_logistic`: all ten Totals 10500, events
  46, 76, 107, 134, 144, 310, 453, 724, 1275, 3739. Eight of ten rows differ.
  `sameBlock p q := q - p <= 1e-6`, with p the first (smallest) probability of the block, which is
  what `logistic_lackfit.blocks` passes: all twenty numbers reproduced.
  Variants that fail: tolerance against the previous value instead of the block start (every
  tolerance tried from 1e-9 to 1e-4), 1e-9, 1e-8, 1e-7, 5e-7, 9e-7, 1.1e-6, 2e-6, 1e-5 against the
  block start, relative 1e-6, rounding to 5, 6 or 7 decimals.
- So this is not undetermined: the caller can pass a `sameBlock` that gives a table SAS does not
  produce, and nothing (no precondition, no fixed definition) prevents it. Only the boundary
  (`<=` or `<` at exactly 1e-6) remains open.
- Checked through the Lean: X15D (8 groups, Totals 130, 126, 123, 132, 118, 131, 119, 121, events
  15, 24, 32, 52, 67, 82, 94, 104) reproduced with exact equality. The 105,000-row check was done
  with my own implementation of the same algorithm, not through `eval_decl`.
- `groups` itself: no finding. `T = (F + 5) / 10`, the `j = 10` cap, `fj < T ∧ fj + f / 2 ≤ T`, and
  the fold of a last group with `20 * fl < F` match D12 on the probes run (F = 100, 104, 105, 23, 4,
  20, 40, 0).

### F4. OMITTED: `def:roc_train_precond` does not exist

- `roc_train`'s comment says "With no event or no non-event the Lean gives a missing Area; SAS then
  produces no table (precondition)". `def:roc_valid_precond` exists and states this;
  `def:roc_train_precond` is not in the blueprint (`get_items`: not found).
- Input: `risk_scores_train` with every `default_flag = 0`. Lean: one row, `ROCModel = "Training Set"`,
  `Area` missing. SAS: per the unit's own comment, no ROCAssociation table. Also unguarded:
  `default_flag = 2` is silently a non-event in `Sas.rocObs` (`RealLike.eqb y 1`), which
  `roc_valid_precond` excludes for the validation unit only.

### F5. UNSTATED-ASSUMPTION: `logistic_association` and `logistic_lackfit` have no precondition

- Both read `default_flag` through `Sas.rocObs`, where anything present and not equal to 1 is a
  non-event, and both return a table for inputs on which PROC LOGISTIC fits nothing.
- `eval_decl`, `logistic_association` on `[]`: four rows, `Pairs = 0`, every other value missing.
  On rows `(1, 0.7), (0, 0.7), (., 0.9), (2, 0.1)`: Pairs 2, Percent Concordant 50, c 0.75, i.e. the
  row with `default_flag = 2` is counted as a non-event.
- `logistic_lackfit` on one row: one group. SAS needs at least three groups for the test (D12) and a
  binary response with both levels for the fit.
- Needed: `default_flag` in {missing, 0, 1}, at least one event and one non-event with a present
  probability (as in `roc_valid_precond`).

### F6. UNSTATED-ASSUMPTION: which missing covariates blank `pd_logistic` in `logit_scored_train_output`

- SAS: train.sas 49-83, 34 candidate covariates with `selection=stepwise`. D13 (Missing Values):
  the fitted probabilities "are not computed for any observation with missing offset or explanatory
  variable values".
- Lean: `Sas.linpred model r` is missing only when a covariate in `model.terms` (the selected
  ones) is missing.
- Input: a row with every selected covariate present and a missing value in a candidate that
  stepwise did not select (for example `age`, absent from the reference parameter table).
  Lean: `pd_logistic` is a number. SAS: UNSETTLED. By the quoted sentence the MODEL statement's
  explanatory variables are the 34 candidates, which would give a missing value; X15C has no
  selection and cannot tell. PROC PLM (`logit_scored_valid_temp`) may behave differently from the
  OUTPUT statement here, since it sees only the stored model.
- Neither unit has a precondition. One is needed (all 34 MODEL covariates present in every row), or
  an experiment. Related and also unstated: the names in `model.terms` must be columns of the
  table. With a name that is not a column, `Sas.num` reads missing and every `pd_logistic` is
  missing; the reference `model_coefficients.csv` shows names cut to 20 characters
  (`credit_utilization_c`), so a model built from that table would hit this.

### UNSETTLED notes (no evidence either way)

- U1. PROC FREQ on a table with zero rows (`confusion_matrix_train`, `confusion_matrix`): Lean gives
  `[]`. Whether SAS creates an empty `OUT=` data set or none is in neither X13 nor D7. Downstream,
  `training_metrics` gives `[]` and `model_summary` still gives one row with missing metrics, which
  matches SAS only if the empty data set exists.
- U2. `Sas.round` on a negative value that rounds to zero: `eval_decl` gives `-0.0` for `-0.3` and
  for `-1e-320`. SAS's sign of zero there is not in X05 or X11. Unreachable in this pipeline unless
  `pd_logistic > 3.4`.
- U3. ROC tolerance boundary and Area operation order: already marked OPEN in the Lean. Probes:
  gap `+1e-8` above an event gives 0.0, gap `-1e-8` gives 0.5 (binary64 rounding of the
  subtraction), so the boundary behaviour is asymmetric as written.

### STYLE (only where it hides meaning)

- S1. `roc_train` / `roc_valid` give `ROCModel` and `Area` only. SAS's tables have eight columns
  (`printed_roc_train.csv`: ROCModel, Area, StdErr, LowerArea, UpperArea, SomersD, Gamma, TauA).
  Sanctioned by R25. The claim that nothing else is read holds: `proc print` uses `var Area`, and in
  `model_summary` the six shared columns are overwritten by `roc_valid`'s and then dropped by KEEP.
  X15B prints SomersD, Gamma and TauA in hex, so they could be translated and checked.
- S2. `ROCModel` in `model_summary`: the reference log has "WARNING: Multiple lengths were specified
  for the variable ROCModel", so in SAS's PDV the value from `roc_valid` is cut to the length set by
  `roc_train`. `Sas.merge11` keeps `"Validation Set"` whole. `WHERE=` is applied to the data set
  before the PDV, and KEEP drops `ROCModel`, so no output differs (reference `Valid_AUC` is present).
  The KEEP does hide this, and it is harmless.

---

## Units with no finding

- `logit_scored_train` (102-106): `pred_logistic = (pd_logistic >= 0.5)`, missing gives 0, appended.
  Reference: 0 mismatches in 150,000 rows.
- `confusion_matrix_train`, `confusion_matrix`, `Sas.freq2` (R20): X13 `freq` data reproduced through
  `eval_decl` (7 rows, order, missing levels, PERCENT missing on them, 50 / 12.5 / 12.5 / 25);
  1 of 7 gives 14.285714. Reference counts and percents reproduced (`100 * c / N`). See U1.
- `training_metrics`, `validation_metrics` and their preconditions: line by line identical to the
  SAS, including branch order, `retain ... 0` for all four, the guards and the F1 grouping.
  `eval_decl`: zero rows gives `[]`; one cell (1,1) gives 1, 1, 1, 1; one cell (0,0) gives precision,
  recall, F1 missing and accuracy 1; only `default_flag = 0` rows gives precision 0, recall missing,
  F1 missing (`. > 0` is false), accuracy 0.5; a missing COUNT on the (1,1) row gives four missing
  values; a row with a missing level changes nothing. Reference counts give 0.578068, 0.202340,
  0.299757, 0.936905 against 0.5781, 0.2023, 0.2998, 0.9369. Column order matches
  `model_summary.csv`.
- `logit_scored_valid_temp`: `Sas.linpred` is intercept then terms left to right. My recomputation
  of X15C: 2998 of 2998 complete rows bit-exact against `xb`, `pl` equal to `xb`, rows 2999 and 3000
  missing, row 2998 (missing response) scored. See F6 for the missing-candidate question.
- `logit_scored_valid`: `1 / (1 + exp(-predicted_logit))` grouped as written, overflow and missing
  give missing then `pred_logistic = 0`, DROP after the assignments.
- `risk_scores_train`, `risk_scores_validation`, `Sas.round` (R23): all nine X11 thresholds and their
  predecessors reproduced through `eval_decl` (18 of 18), plus the X11 negative, below-half and X05
  cases (0.4999999999999 -> 1, 0.499999999999 -> 0, 2.4999999999999996 -> 3, 2.4999999999 -> 2,
  -2.5 -> -3, -712.49999999999989 -> -713, 4503599627370497 unchanged, missing -> missing). Constants
  750 / 700 / 650 / 600 / 550, `'A','B'`, `'C'`, 0.05, 0.02, 0.04, 0.07, 0.10, 0.15, branch order and
  variable order all match the source. Reference: score, grade, recommendation, rate, base_score,
  score_range, base_rate recomputed for 150,000 rows, 0 mismatches. See U2.
- `Sas.rocArea` on X15B: r1 0.666667, r2 0.625, r3 0.75, r4 0.125, r6 0.587912, matching the log to
  the printed precision; r5 is r1 plus rows `Sas.rocObs` drops. See F1 for the constant.
- `roc_valid`, `roc_valid_precond`: nothing beyond F1 and S1.
- `risk_scores_train_clean`, `risk_scores_validation_clean`: code correct (prefix match, case
  folding, order kept). Comment of the first is wrong, see F2.
- `final_model_output`: KEEP list and resulting order match `final_model_output.csv`.
- `model_summary`, `Sas.merge11` (R21): X15A and X13 `merge` behaviour as modelled. `eval_decl`: four
  one-row inputs give the reference column order (Train_AUC, Valid_AUC, train_*, valid_*,
  model_name, training_date, training_records, validation_records); empty metrics tables give one row
  with missing metrics; both WHERE= selecting nothing and empty metrics give no row; WHERE= selecting
  nothing on `roc_train` only gives a missing `Train_AUC` and the other values kept.

---

## Amendments proposed

1. R25: the tie tolerance is not 1e-8. The reference Association table needs a value in
   [1.0502e-8, 1.0602e-8) at CSV resolution; `sqrt(2^-53)` fits. Run an experiment on the ROC
   statement with gaps 1.03e-8 and 1.08e-8 to confirm for `PRED=`, then change `Sas.rocTops`.
2. R29: fix the block rule instead of a parameter: a probability joins the block while it is within
   1e-6 of the block's first probability. "Identical" is refuted by `printed_hl_partition.csv`.
   Boundary at exactly 1e-6 stays OPEN.
3. R26 / inventory: add `_LEVEL_` to the OUTPUT data set (train.sas 86); inventory has no row for
   it. Print `_LEVEL_` (type, value, position) from X15C's `fo`.
4. Add `def:roc_train_precond`, and preconditions for `logistic_association`, `logistic_lackfit`
   and `logit_scored_train_output` (F4, F5, F6).
5. Inventory: no row for PROC FREQ on an empty input (U1) or for the missing-candidate question
   under stepwise selection (F6).
