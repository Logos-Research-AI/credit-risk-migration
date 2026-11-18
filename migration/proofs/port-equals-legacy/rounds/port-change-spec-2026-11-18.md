# Change specification for the port blueprint, one clearing (C-g version 2, 2026-11-18)

Status: for the lead's approval. Nothing was changed on any blueprint, no code was changed,
nothing is committed. Author: prover (specification step of the workflow).

This file holds no Lean (standing rule: Lean lives only in the blueprint). Every change is given
in words, with the names of the items, clauses and positions it touches. Where the uncompiled
Lean of `C-g-draft-2026-11-18.md` section 3 (version 1) still stands, this file says "as v1"
and names the lines that differ. Nothing here was compiled.

Blueprints: port `5365851c-5549-44b7-9207-4bd4c422031d` (322 items by `get_status` today; the
v1 draft says 323), SAS `3f5df696-7c80-45cc-809f-b2881714663d`. Both read only.

Decisions this file follows, not repeated in the sections: the owner's of 2026-11-18 (no
contract hypothesis; the port follows SAS on one outcome; three levels; G2 on steps 03 and 05 to
08 with the two row bounds dropped; leverage near 1 and variance 0 fixed in the port, not
assumed; padded text; Q27 restated) and the lead's (form U; `Paired` 3 filler; `Paired` 1
unchanged with a helper in T0; 8b, 8c narrow; conjunct 16 corrected per H15; one clearing per
blueprint).

## 0. What I read, and what I did not

Read in full: `C-g-draft-2026-11-18.md`, `observation-H15-2026-11-18.md`,
`sas-no-fit-draft-2026-11-18.md`, `sas-change-spec-2026-11-18.md`, `definitions-v3.md`,
`informal-spec.md`, `brief-prover.md`; the first 60 lines and the P1/P2 section of
`saslinks-padded-text-draft-2026-11-18.md`.

The port at HEAD `a9b1f41`: `git diff b9883c8 HEAD -- port/credit_risk` (the five commits
65430e4, 70c4d9c, 1a90814, 88df42d, a9b1f41: `train.py`, `sas_compat.py`,
`metrics_calculation.py`; `predict.py` and `feature_engineering.py` have no change), and
`sas_compat.py` 760-830 (`_kept`, `_solve_sas`, `_inv_sas`, `_left_out`). The working tree has no
uncommitted port change (`git status`): both fixes are committed, so R11 of v1 is closed.

On the port blueprint (accepted Lean): `def:Paired`, `def:pyPipeline`, `def:PyParams`,
`def:SasParams`, `def:StepwiseResult`, `def:StepwiseStep`, `def:LogisticFit`,
`def:train_run_01_fit_frame`, `_04_score_train`, `_08_ctable`, `_10_score_valid`,
`def:run_py_py_py`, the preconditions of `run_py_py_py`, of steps 01, 03, 04, 05, 06, 07, 08, of
`classification_table`, `hosmer_lemeshow`, `_hl_groups`, `_pairs`, `association_table`; the
statements of E3, E4, E5, E8, E9, E10, E11, A2, A4, F3, F5, F6, T0, T1, T2,
`lem:sas_fit_term_names`, `lem:metrics_flags_reached`, `lem:metrics_score_frames`,
`lem:sas_reached_scores_read_shape`, `lem:sas_cov_train_bins`, `lem:metrics_ks_table`;
`get_graph consumers_of` on 44 items; `get_status`.

Not read: any proof on the blueprint (for what the proofs open I rely on v1 section 2 and on the
proof dependencies `get_items` returns); `def:run_py`, `def:run_py_precond` and the ten metrics
step units (I specify their change from the Python diff and H15); the current statements of G2,
G4, F4 and of the example items (v1 section 4 read them); steps 02, 03, 05, 06, 07, 09, 11 to 15
as Lean (read as Python). The SAS items of the SAS specification are taken as that file gives
them (N1 to N3, C1 to C8); they do not exist yet. Where a statement below rests on something not
read it says "expected".

No hook blocked a call.

## 1. Summary

One clearing, in four layers that are entered together before any proof is resubmitted:

| Layer | Items | Who writes the Lean |
|---|---|---|
| (a) the port's units for the five commits, with the float-precision bounds dropped | 2 composition items, up to 15 train steps, 2 helpers of `sas_compat`, up to 4 new helper units, the metrics composition and up to 8 of its steps, and their preconditions (section 2) | port translators |
| (b) `def:pyPipeline` (fields `fit`, `score`, `metrics`) | 1 | prover, for the lead's review |
| (c) `def:PyLinks` (C-g version 2) and `def:Paired` (clause 3) | 2 | prover, for the lead's review |
| (d) contracts, lemmas and examples restated | 13 contracts, 9 examples, 1 lemma (section 5) | prover |

Of the 52 items the v1 draft and the no-fit draft count as cleared (47 statement consumers of
`def:PyLinks`, 5 more of `def:Paired`): 23 are restated, 29 keep their statement. Of the 29: 18
are expected to resubmit unchanged, 8 with a mechanical edit, 3 need new proof work. Table in
section 6. The units' update clears about 21 more items outside the 52 (step theorems and
shared lemmas of version 2.3; section 6.3), and the profile refresh reaches 24 more.

What changed against version 1 of C-g:

| v1 | v2 |
|---|---|
| R1 (row bounds of steps 07, 08) open | the bounds are dropped from the two preconditions (owner). Two companion bounds must go with them or G2 stays false: narrowing 5 |
| R2 (one outcome reaches E3, A2, E5, F3, metrics) open | settled by form U and the three levels: E3 proves "both nothing"; E5, A2, F3, F4 and the metrics contracts get the no-fit run (section 5) |
| 6b (3) a positive variance for every final parameter | dropped. What is left: no negative variance (narrowing 3) |
| 6b (4) no leverage equal to 1 | dropped. What is left is a fact about one numpy routine, moved to a clause of its own (13) |
| R6 conjunct 16 false on the one-outcome training score file | corrected (section 3.5) |
| clause 7 untouched | the training score flag needs a second case, or a lemma (section 3.6, question 2) |
| `pyPipeline.metrics` untouched | must treat a file that is not written as the table with no row, or E8 to E10 are false at level 3 (section 4.1, narrowing 1) |

## 2. (a) The port's Lean update, in words

For the port translators, who specify each change from the Python alone
(`port-lean-update-procedure`). Source: the diff `b9883c8..a9b1f41`. Line numbers are of HEAD.
The translators decide signatures; what is fixed here is the behaviour each unit must have and
which conditions leave or enter a precondition. Tuple positions and argument lists named in
sections 3 to 5 are read again from the accepted units before anything else is entered (R7 of
v1 stands).

### 2.1 Train stage (`train.py`), commits 65430e4, 1a90814, a9b1f41

| Unit | Change |
|---|---|
| `def:train_run_01_fit_frame` | The raise on a result without a final fit is gone (`train.py:106-107`). `final` and `intercept_only` are passed on as they are, present or absent (today the empty fit stands for an absent one). `m2ll0` exists only with an intercept-only fit (Python: NaN otherwise; it is read only by step 03, on steps, of which a result with no fit has none) |
| `def:train_run_01_fit_frame_precond` | loses `stepwise.final.isSome` and `stepwise.intercept_only.isSome`. The rest stays, `n_obs ≠ 0` included |
| `def:train_run_02_stepwise_summary` | `stepwise_summary.csv` is written only with a final fit (`:156`) |
| `def:train_run_03_fit_global_rsquare` | `printed_fit_statistics.csv` is written only with a final fit (`:265`). Its precondition is unchanged (it speaks of steps) |
| `def:train_run_04_score_train` | With no final fit: no effect, no index, no intercept, no coefficient, and `pd_logistic` missing on every row (the linear predictor is the null literal, `:290-307`). With a fit: a new value `left_out`, the positions i of `final.names` whose `cov[i, i]` is exactly 0; the intercept is 0 when position 0 is left out, a coefficient is 0 when its position is (`:297-306`, X22). The intercept becomes optional |
| `def:train_run_04_score_train_precond` | gains, with a fit: `cov` is two-dimensional and `cov[i, i]` exists for every position of `final.names` (IndexError otherwise, `:297`). With no fit only the frame conditions and the mask length remain |
| `def:train_run_05_association` | The table is computed on the probabilities of the last iteration's estimates: with a left-out parameter, from `final.beta` as it is (`eta_iteration`, `assoc_scored`, `:325-331`); otherwise on `fit_scored` as today. New inputs: `final` (or its `beta`), `final_effects`, `final_index`, `left_out` |
| `def:train_run_06_coefficients_odds` | No fit: no row at all (`:374`, `:386`). A left-out parameter: DF 0, estimate 0, empty standard error, Wald and p-value, no odds ratio (`:388-396`); the others DF 1 as before. New column source `mc_df` |
| `def:train_run_06_coefficients_odds_precond` | No fit: nothing. A left-out position: nothing. The other positions: as today (`cov[i, i]` not negative, its square root not 0, the overflow conditions). The clause "square root not 0" now follows from "not left out and not negative" |
| `def:train_run_07_hl` | no change in the Python. Its precondition changes through `hosmer_lemeshow_precond` |
| `def:hosmer_lemeshow_precond` | **drops `yy.length ≤ 2^52`** (owner). See narrowing 5 for the companion clause (5), `|o1| ≤ 2^52` |
| `def:classification_table` | `v` is `_inv_sas` of the weighted cross-product, not `np.linalg.inv` (`sas_compat.py:1558`, X22 B). New rule (X21): an observation with `1 - h ≤ 1e-8` keeps its probability; the others get the one-step adjustment, and the division is by `1 - h` only for them (`:1563-1564`) |
| `def:classification_table_precond` | **drops clause (6) "1 - h_i is not 0"** (the code no longer divides there) and **drops `y.length ≤ 2^51`** (owner). See narrowing 5 for `|n1| ≤ 2^52` |
| new: `_kept`, `_inv_sas`, `_left_out`, `classification_is_made` (`sas_compat.py:772-787`, `:801-811`, `:814-817`, `:1651-1663`) | `classification_table` and step 08 now call them, and they are inside `sas_compat`. Either new units (with `inv`, `solve`, `matmul` as their parameters) or new explicit parameters. **Translators' and lead's choice, question 5.** As units they need no `PyLinks` clause beyond 13; as parameters each needs one |
| `def:train_run_08_ctable` | `ctable_made` is "there is a final fit and `classification_is_made`" (`:485`). When false the table is the empty table of twelve columns, nothing is computed, and `printed_classification.csv` is not written (`:527`). The design matrix is built from the names of the fit, none when there is no fit |
| `def:train_run_08_ctable_precond` | asks the precondition of `classification_table` only when `ctable_made`; otherwise only what building `x_final`, `pd_train` and the test itself ask |
| `def:train_run_09_confusion_train`, `def:train_run_12_risk_scores` | no change in the Python. To be evaluated on the no-fit inputs (a probability missing on every row; a validation frame with no row and two columns) |
| `def:train_run_10_score_valid` | No fit: the PLM table does not exist; the scored validation frame has no row and the two columns `pd_logistic`, `pred_logistic` (`:609-628`). With a fit: as today |
| `def:train_run_11_confusion_valid` | A scored frame without `default_flag`: the confusion matrix is the frame with no column; `validation_metrics` has no row (`:634-694`). `validation_metrics` has at most as many rows as the confusion matrix has, at most one |
| `def:train_run_13_roc` | A validation table without `default_flag` is read as one with no usable row. New result `roc_train_created`, computed as `roc_valid_created` is (`:803-824`) |
| `def:train_run_14_final_and_summary` | takes `roc_train_created`. `model_summary` has no row unless both ROC tables were created (`:904`). `model_coefficients.csv` is written only with a final fit (`:935`) |
| `def:train_run_15_printed_roc` | `printed_roc_train.csv` only when `roc_train_created`; `printed_confusion_validation.csv` only when the confusion matrix has a column (`:947`, `:960`) |
| `def:run_py_py_py` | the composition of the above. `model.json` is written only with a final fit (`:533`): the second component of the result becomes optional. Its header comment lists the files not always written; it gains `stepwise_summary.csv`, `printed_fit_statistics.csv`, `printed_classification.csv`, `model_coefficients.csv`, `printed_roc_train.csv`, `printed_confusion_validation.csv` |
| `def:run_py_py_py_precond` | the conjunction of the step preconditions as changed. Its header gains "a training part with one outcome (a stepwise result with no fit)" among the cases inside the precondition |

`StepwiseResult`, `StepwiseStep`, `LogisticFit` do not change (the dataclasses did not), so
`def:PyParams` keeps its Lean unless question 5 adds parameters.

### 2.2 Metrics stage (`metrics_calculation.py`), commit 70c4d9c and observation H15

| Unit | Change |
|---|---|
| `def:confusion_metrics` | the metrics frame has at most as many rows as the confusion matrix, at most one (`:78`): no row when the table read has none |
| `def:run_py` and the step units it composes | `valid_exists` is "the validation table as read has a row" (`:112`). When false the validation frame is the frame of three Float64 columns `default_flag`, `pd_logistic`, `credit_risk_score` with no row, whatever the reader returned (`:113-116`) |
| the steps of `cumulative_lift`, `validation_summary`, `model_performance_metrics` (05, 08, 09) | when `valid_exists` is false: no row each (`:332-350`, `:459-483`, `:536-542`). The column order of these header-only files is outside what the Lean states (RULEBOOK section 6) |
| the writes of `decile_analysis.csv`, `ks_statistic.csv`, `calibration_plot.csv` (steps 04, 02, 07, or the composition) | only when `valid_exists` (`:507-520`). Whether `printed_roc_metrics.csv` is already conditional in the Lean is for the translators to check against `:568-590` (not in the diff I read as changed; H15 lists the file as not written) |
| `def:metrics_run_06_psi` and its precondition | **H15.** On the training score table of a no-fit run the real reader gives `credit_risk_score` as a text column whose every cell is null. The unit must return on such a column what it returns on a Float64 column of nulls: every cut missing, every row in bin 0. Its precondition admits, for `credit_risk_score` of the training table, a Float64 column or a text column of nulls only. A text cell that is not null stays outside (polars raises `ComputeError` there: a true exclusion, not a narrowing) |
| `def:run_py_precond` | the validation table may have no row; with a row, as today. The training table: as today, with the clause above for `credit_risk_score`. `pd_logistic` of the training table is not read by any step (H15 (2)): if a clause asks it to be numeric, the clause goes |

### 2.3 Predict and feature engineering

No change. On a no-fit run `predict.run` stops at its input check (no `model.json`); the Lean
says this through `coefExists`.

### 2.4 Differential evaluation the translators owe (before layer (b))

The staged data of the commits: `port/tests/data/x27_one_class/C60` and `E60` (both are a
training part of zeros: correction 1 of the SAS specification), `one_row_training/n1_class0` and
`n1_class1` (the second is the only all-ones case in the port's tests),
`sas_x21_leverage.json`, `x21_r3_s03`, `x22_A`, `x22_B`, `x22_C`; and one fitted scenario already
in the receipts, to show nothing moved there.

## 3. (b), (c) `def:PyLinks`, C-g version 2

### 3.1 Shape

As v1 section 2: new parts are appended after position 20; `keeps` is not touched; clause 6 is
changed in place. New in v2: conjunct 16 and conjunct 11 are changed in place (3.5, 3.6); one
more appended part (clause 13).

Positions after the edit: 1 to 5; 6 (the fit, changed); 7 to 10; 11 (`scoresTrainExists`,
changed if question 2 is answered "second case"); 12; 13 to 15; 16 (`readScoresTrain`, changed);
17 to 20; then appended 21 (clause 12, `fsum`), 22 to 24 (8b), 25 (8c), 26 (6b), 27 (clause 13).

The local definitions `outcomes`, `trainFrame`, `bothOutcomes`, `oneOutcome`, `keepsPresent` are
as v1 section 3, on the tuple of step 01 as the translators leave it.

### 3.2 Clause 6, the fit (in place)

Text, replacing the last three parts of clause 6:

> For every table: the final effects are distinct names among the 36 candidates (unchanged). For
> every training frame:
> - with both outcomes, the stepwise result has a final fit and an intercept-only fit; the
>   coefficient array of the final fit is one-dimensional with one entry per name of the fit and
>   at least one entry; and its covariance is two-dimensional and square with one row per name;
> - with one outcome, the stepwise result is the result with no fit: no step, no final fit, no
>   intercept-only fit.
> Nothing is asked of any other table. On a training frame with both outcomes the fit is taken
> to return a result (ruling G58, narrowed by the decision of 2026-11-18).

Against v1: the covariance shape is new. Reason: step 04 now reads `cov[i, i]` for every name of
the final fit (`train.py:297`). It is within the old wording of clause 6 ("the shape steps 01
and 04 ask for"); the Lean of the clause grows by one conjunct inside the both-outcomes branch.
True of the port by `sas_compat.py:950`, `:962` (`_inv_sas(info)`, square, of the size of the
design).

Lean, in words: as v1 lines 352-365, with the conjunct "there is a list of rows c with
`final.cov` the 2-D array c, c has as many rows as `final.names` has names, and every row has
that length" added after the coefficient conjunct. `final` is read from the stepwise result
(`(py.fit T).final`), no longer from an empty-fit default of step 01.

### 3.3 Clause 6b, what is still asked of the fitted result (appended, position 26)

For every training frame with both outcomes, with the values of steps 01 and 04 as
`run_py_py_py` computes them:

1. (step 03) For every step of the stepwise result whose fit has a variable: the names of the
   fit after the first are among the 36 candidates; its coefficient array is one-dimensional and
   its covariance two-dimensional and square with as many rows as there are coefficients; the
   fit has at most that many names. Unchanged from v1.
2. (step 03) -2 Log L of the intercept-only fit is not 0. Unchanged from v1 (it was inside (1)).
3. (steps 03 and 08) The names of the final fit after the first are among the 36 candidates.
   Unchanged from v1.
4. (step 06) For the intercept and for every final effect, the diagonal entry of the covariance
   is not negative. **Replaces v1 (3)** ("exists and is greater than 0"): existence is now in
   clause 6; "greater than 0" is no longer needed because `train.py:388-396` handles the entry
   that is exactly 0.

**Dropped against v1**: (3) the positive variance (commit a9b1f41), and all of (4), the
leverages (commit 88df42d for "none equals 1"; "one leverage per complete case" moves to clause
13, where it is a statement about the routine and not about the fit).

Parts 1 and 3 are shape and naming facts of a `LogisticFit` the port builds (v1 "True of the
port by" (1), (2)). Parts 2 and 4 are facts about values of the out-of-scope fit and are
**still assumed**: narrowing 3.

What steps 05 and 07 ask is proved, not assumed, as v1 says; with the two companion bounds of
narrowing 5 gone, the "group sums are whole numbers" clauses follow from outcomes 0 or 1.

### 3.4 Clauses 8b, 8c, 12 (appended, positions 21 to 25)

As v1, narrow forms, text and Lean unchanged: 12 (`fsum` of numbers all at least 0 is at least
0); 8b (`keepsPresent` for the 42 feature columns and for the four listed columns of each score
read-back); 8c (the feature read-back keeps a `default_flag` of 0 or 1, on a table whose
`default_flag` is present in every row).

The sentence at the head of the definition becomes: "Nothing is asked of the formatters or
`full`; of `fsum` only clause 12; of the numpy routines only clause 13."

### 3.5 Conjunct 16, `readScoresTrain` (in place; observation H15)

- **Before**: `keeps py.readScoresTrain` on `row_id`, `default_flag`, `pd_logistic`,
  `credit_risk_score`: in each of the four columns a numeric cell stays numeric, a missing one
  missing.
- **After**: the same for `row_id` and `default_flag`. For `pd_logistic` and
  `credit_risk_score`: a numeric cell is read back as a numeric cell, a missing one missing;
  **or**, when the column holds the missing number in every row of the table, as the text cell
  with the missing text. The rows, the names, and "one kind of cell per column" (C-f) are asked
  as before.
- **Reason**: H15. On `risk_scores_train.csv` of a one-outcome run the two columns are empty in
  every row, and the reader (`guessingrows=20`) returns them as text columns of nulls. The
  conjunct as it stands is false of the real reader on a file a valid run reaches.
- **True of the port by**: `proc_import_csv` (`sas_compat.py:578-587`), H15 lines 9 to 13. The
  identity meets it (first branch).
- **Lean, in words**: `keeps` is not edited (the other three read-backs use it). Conjunct 16 is
  written out in its place: the `Forall₂` of rows with equal names; for the two first columns
  the cell clause of `keeps`; for the two others the cell clause with the second disjunct "every
  row of t has `Cell.num none` under c, and the read-back cell is `Cell.str none`"; then
  `oneKind t → oneKind (R t)`. One conjunct at the same position, so proofs that discard it are
  untouched; a proof that uses it for `pd_logistic` or `credit_risk_score` must first show the
  column is not missing in every row (section 6).
- **Residue**: narrowing 6.
- The SAS specification's question 1 (W or K for `SasLinks` (3) on the same file) is the mirror
  of this. Under W the two sides read the same; under K the SAS link stays the identity. The
  equality contracts do not use `SasLinks` (3); only T0's second half does, at the identity,
  which meets both.

### 3.6 Clause 7, the training score flag (in place; **new, not among the decisions**)

`PyLinks` 7 says `scoresTrainExists S` is true exactly when `P.score m F` returned S for some
model and table. On a no-fit run the training score table is written by the train stage and is
not a value of `P.score` for any model I can name: `P.score` is the validation chain with a
model, and with every feature present it gives a present probability. So at level 3 the port's
metrics step would stop (flag false) where the real stage does not, and E8 to E11, F5, F6, G4
would fail on the no-fit run.

Two ways (question 2):

- **7b, a second case (specified here).** `scoresTrainExists S` is true exactly when the score
  step of P returned S for some model and table, **or** S is the training score table the train
  stage writes on some table with the result with no fit: the table of E5's chain (steps 01, 04,
  09, 12, 14, `risk_scores_train.csv`) on the read-back of some F, at the stepwise result with
  no fit. `scoresValidExists` needs nothing: the validation score table of a no-fit run is the
  table with no row, which the score step returns on the table with no row (expected; to be
  proved once, for P and for S).
- **Junk model, no change.** The SAS specification (4.9) gets the SAS flag from link (8) as it
  is, through a model with a term naming no column. On the port that would rest on what the Lean
  of step 10 does outside its precondition (a column that does not exist). I do not recommend
  it: the flag would be true through a value the unit's own precondition excludes.

7b is a correction of an assumption so that it stays true of the port ("a file exists when
written"); it is not a hypothesis on a contract. `Paired` 5 is not touched (it restates
`SasLinks` (8), which the SAS specification leaves as it is).

### 3.7 Clause 13, one value per row (appended, position 27; new)

For every matrix x and every matrix v, `einsum_q x v` has as many entries as x has rows.

- **Reason**: `classification_table_precond` (5) asks that the leverages have the length of y.
  v1 carried this inside 6b (4) on the reached arguments. Stated of the routine it is simpler,
  true of `np.einsum("ij,jk,ik->i", x, v, x)` whenever it returns, and met by T1's witness once
  that is "0 for each row".
- If question 5 is answered "new units", the preconditions of `_kept` and `_inv_sas` may ask the
  like of `inv` and `solve` (an n by n matrix in, an n by n matrix out; a vector of length n).
  Each such condition is one more line of clause 13. To be fixed when the units are accepted.
- Narrowing 4.

### 3.8 Text only

Clause 11 cites `train.py:771` for the date; at HEAD the line is `train.py:883`
(`dt.date.today()`; v1 says 843, which was before 1a90814 and a9b1f41). To be read again at the
edit.

## 4. (b), (c) The equality definitions

### 4.1 `def:pyPipeline`

- **`fit`**: nothing when either feature flag is false (unchanged); nothing when step 04
  extracts no intercept (the stage writes no `model.json`); otherwise the model of step 04's
  intercept and coefficients. Text: "nothing when the flags say either feature file is absent,
  or when the fit returned no model (a training part of one outcome; the stage then writes no
  `model.json`)".
- **`score`**: the same wiring on the units as changed: step 10 with the intercept of m as a
  present value, step 12, step 14 with the fillers and `false` for both ROC flags.
  `lem:py_score_fillers_idle` is proved again on the new step 14.
- **`metrics`** (**needed for level 3**): today the field returns nothing unless all four files
  are in the result of `run_py`. On a no-fit run `ks_statistic.csv` and `decile_analysis.csv`
  are not written, so P would return nothing where S (after C1 to C3 of the SAS specification)
  returns four tables with no row, and E8 to E11 would be false. Change: when `run_py` returns
  files, the KS and decile tables are the tables of their files, **or the table with no row when
  the file is not written**; the summary and threshold files are always written and are looked
  up as today. Text: "a file the stage does not write is given as the table with no row, as the
  SAS units give a table that was not created (RULEBOOK of `legacy-to-lean`, R39, R46)". This is
  the first default written into `pyPipeline`; the sentence "It contains no arithmetic,
  comparison or default of its own" gains "except this one". Narrowing 1.

### 4.2 `def:Paired` 3, filler form

- **Before**: for every table T, `sas.fit T` is the model whose intercept and terms are those
  step 04 extracts from the port's fit on T.
- **After**: for every table T, `sas.fit T` is the model step 04 extracts from the port's fit on
  T; and where step 04 extracts none, the model with intercept 0 and no term.
- **Reason**: step 04's intercept is optional after the update, so the clause must change
  whatever else is decided. The second half is never read by the SAS pipeline (form U: its `fit`
  field returns nothing there, by `logistic_no_fit`). It keeps `lem:sas_fit_term_names` true for
  every table and the clause one equality at the same position.
- Note for the text: with a left-out parameter step 04 gives coefficient 0 for it (a9b1f41), so
  the model `Paired` 3 hands SAS has that term at 0, which is what X22 shows of PROC LOGISTIC's
  parameter table.

### 4.3 The rest of `def:Paired`

- Clause 1: unchanged (P1). After the profile refresh `SasLinks` (1), (2) carry one more
  conjunct in `deliveredCell`; `Paired` 1 keeps the old local definition. T0 gets the helper
  "the tightened delivery implies the old one".
- Clauses 2, 4, 5, 6, 7: unchanged in letters. Clause 5 changes in value through
  `sasPipelineOf` (the `fit` field of the SAS pipeline).

### 4.4 `def:SasParams`, `def:SasLinksOf`, `def:sasPipelineOf`

Lean unchanged (form U: no parameter changes type). Resubmitted against the refreshed profile.

## 5. (d) Contracts: new texts and statements, in words

Write P for `pyPipeline py`, S for `sasPipelineOf sas`. Hypotheses of every contract:
`PyLinks py`, `Paired py sas` where the form has it, `InputOK`, reached-equations. No other.

The informal specification is the text of record and these texts differ from it (E5, E8 to E11,
A2, A4, section 4 on G2, section 9 on the fit). **The lead enters them as an amendment of
`informal-spec.md` before any statement is written** (question 1). I do not reword a contract on
my own; what follows is the proposal.

### 5.1 Two runs, named once

- **The fitted run** (as today): F1, F2 with `S.features train seed` returning them; m with
  `S.fit F1` returning m; S1, S2 with `S.score m F1` and `S.score m F2` returning them.
- **The run without a model**: F1, F2 as above; `S.fit F1` returns nothing; S1 is the SAS
  training score table without a model, that is `logit_scored_train_output_nofit` (N2) of the
  feature table as read, then `logit_scored_train`, `risk_scores_train`,
  `risk_scores_train_clean`; S2 is the SAS validation score table without a model, that is
  `logit_scored_valid_temp_nofit` (N3), then `logit_scored_valid`, `risk_scores_validation`,
  `risk_scores_validation_clean`: the table with no row.

In a statement "the run" is the disjunction of the two, as one hypothesis: "there is m with the
three fitted equations, or `S.fit F1` returns nothing and S1, S2 are these two tables". Both
disjuncts are reached-facts, so this adds no hypothesis; it widens each contract. Whether the
disjunction is written out in each statement or is one new definition item (`def:ScoreRun`, with
its text in the definitions file) is question 3. On the port's own run (G2, G4, A2) the same
with P for S, the port's chain of E5 at the result with no fit for S1, and the table with no row
for S2.

### 5.2 Level 1

**E3 (`thm:E3_fit`).** Text and Lean unchanged. It now has a second case, proved: on a valid
run the read-back of F1 is a training frame whose outcomes are 0 or 1 (`TrainOK`, E1, 8b, 8c);
with one outcome `PyLinks` 6 gives the result with no fit, step 04 extracts no model and P
returns nothing, and `logistic_no_fit` is true of the same table (`Paired` 4) so S returns
nothing; with both outcomes `PyLinks` 6 gives a final fit, `logistic_no_fit` is false, and
`Paired` 3 gives the same model.

### 5.3 Level 2: the train-stage files

**E5 (`thm:E5_train_scores`).** Text: "For F1 as in E3: the table of `risk_scores_train.csv`
that the training chain of the train stage produces (step 04 onward) is `P.score m F1` when
`P.fit F1` returns m; and when `P.fit F1` returns nothing it is the SAS training score table
without a model (5.1)." Statement: the present one, with the chain on the units as changed (the
idle arguments of steps 12 and 14 stay quantified, the new ROC flag among them), and a second
conjunct for `P.fit F1 = none` whose right side is `some` of the SAS table of 5.1 on
`sas.readFeatures F1`. The first conjunct is today's statement.

**A2 (`thm:A2_train`).** On the port's own run, when the train stage returns (files, the
optional content of `model.json`): (1) `P.fit F1` is that optional model, as an equality of
options; (2) with a model m, `risk_scores_validation.csv` is `P.score m F2`; with none, it is
the table with no row; (3) `risk_scores_train.csv` is the table of E5's chain, written as E5
writes it, with the other arguments those the stage gives. Hypotheses unchanged (`PyLinks`,
`InputOK`, the reached-equation of F1, F2).

**F3 (`thm:F3_final_model_output`).** The hypothesis `hm` goes. SAS side: the stop of the SAS
train stage; then `final_model_output` of `risk_scores_train` of `logit_scored_train` of the
OUTPUT table, which is `logit_scored_train_output` at m with the logistic link when `S.fit F1`
returns m, and `logit_scored_train_output_nofit` when it returns nothing. Port side unchanged
(the file among those `run_py_py_py` returns, on the new result type).

**F4 (`thm:F4_model_summary`).** The two-outcome condition is already gone in v1; `hm` goes
too. SAS side as today with the training chain as in F3 and the validation chain from
`logit_scored_valid_temp` at m, or from `logit_scored_valid_temp_nofit`. Text as v1 section 4,
with "the SAS side takes the model as `S.fit F1` returns it, present or absent" in place of "m
with `S.fit F1` returning m". On one outcome both sides are the table with no row (the port:
`train.py:904`; SAS: `roc_train` of a one-class table, R46).

Both F3 and F4 are written as one equality whose SAS side branches on `S.fit F1`. Port and SAS
are compared as written, no read-back, as today.

### 5.4 Level 3: the metrics files

**E8, E9, E10, E11.** Text: "for F1, F2 and S1, S2 the score tables of the run (5.1), fitted or
without a model: `P.metrics S1 S2` and `S.metrics S1 S2` both return tables or both return
nothing; when they return tables, the summary (KS, decile, threshold) tables are equal."
Statement: today's conclusion, letter for letter; the three hypotheses `hm`, `hS1`, `hS2`
become the one run hypothesis. On the run without a model both sides return four tables with no
row: S by C1 to C3 of the SAS specification and `threshold_analysis` on no row; P by
`valid_exists` false and 4.1.

**F5 (`thm:F5_calibration_plot`).** Port side: the file among those `run_py` returns. SAS side:
the stop, then T, the table of `calibration_plot` of `calibration_data`. The equality: the port
writes no file when T has no row, and writes T otherwise. This says more than "equal up to the
convention": it states when the port omits the file. It needs, on the fitted run, that T has a
row (the validation table has one, G57): small new proof work. The weaker form (the port's file,
or the table with no row when it is not written, equals T) is available if the lead prefers one
shape for all files; it is the weaker statement and so a narrowing (narrowing 1).

**F6 (`thm:F6_model_performance_metrics`).** Statement as today with the run hypothesis. On the
run without a model both sides are the table with no row (the port: `:536-542`; SAS: C5). The
file is written on both sides, as a header only.

**A4 (`thm:A4_metrics`).** When `run_py` returns files on the arguments `P.metrics S1 S2` gives
it, on the run of 5.1: there is T with `P.metrics S1 S2` returning T; `validation_summary.csv`
and `threshold_analysis.csv` are among the files and are T's summary and threshold; and each of
`ks_statistic.csv`, `decile_analysis.csv` is among the files and is T's table, or is not among
them and T's table has no row.

**G4 (`thm:G4_metrics_coverage`).** On the port's own run, fitted or without a model (5.1 with P
for S): the precondition of `run_py` holds of the arguments `P.metrics S1 S2` gives it. On the
run without a model: the validation argument is the read-back of the table with no row (no row,
by `PyLinks` 8); the training argument is the read-back of the port's no-fit training score
table, whose `credit_risk_score` is, by conjunct 16 as corrected, a numeric column of missing
values or a text column of nulls, both inside the precondition as changed (2.2). No hypothesis
beyond `PyLinks`, `InputOK` and the run.

### 5.5 Coverage of the train stage

**G2 (`thm:G2_train_coverage`).** Text and statement as v1 section 4 (the whole of
`run_py_py_py_precond` on the real arguments; statement dependencies `def:PyParams`,
`def:PyLinks`, `def:pyPipeline`, `def:run_py_py_py_precond`), with two changes of text: the
sentence on steps 03 and 05 to 08 cites clauses 6, 6b and 13 of `PyLinks` (not "6b (4)"), and
the paragraph "As stated this is false for a valid input with more than 2^51 complete training
rows" is replaced by "the two row bounds were dropped from the preconditions (owner,
2026-11-18)", subject to narrowing 5. "Not covered" keeps its two items (narrowings 2 and 7).
The proof has two cases: both outcomes (steps 03, 05 to 08 from 6, 6b, 13 and valid input) and
one outcome (the precondition of each step on the result with no fit).

### 5.6 T0 and T1

**T1.** Statement unchanged. Witness, against v1 section 6: the fit depends on the table (the
result with no fit on a training frame with one outcome, a constant intercept-only fit
elsewhere); the constant fit's covariance is one row of one entry, any number not negative (1,
so that the intercept is not read as left out); `einsum_q` gives 0 for each row of x (clause
13); `fsum` constant 0; identity read-backs (16 by its first branch); the flags are each side's
reachability, with the second case of 7b if it is taken. Seven more goals than today (positions
21 to 27) and clause 6, 11 and 16 again.

**T0.** Statement unchanged. Proof: the date is the first part of position 20 (v1); the witness
of `sas.fit` is `Paired` 3 with the filler; `SasLinks` (6) from `PyLinks` 6 first part and the
filler's empty term list; (8) by construction, now through the SAS pipeline with the no-fit
branch; the helper of P1 for `Paired` 1; `SasLinks` (3) at the identity under either W or K.

### 5.7 The examples (rule 4 of the brief: every contract's hypotheses can be met)

Each restated contract with a new case needs that case shown inhabited. Proposal: each of
`lem:ex_E3_fit`, `ex_E5_train_scores`, `ex_F3_final_model_output`, `ex_F4_model_summary`,
`ex_A2_train`, `ex_A4_metrics`, `ex_G2_run`, `ex_G4_run`, `ex_metrics_run` becomes a pair: the
fitted run it shows today, and a run without a model on one small valid input (four training
rows, every outcome 0; the T1 parameters). `ex_G2_run`, `ex_G4_run`, `ex_F4_model_summary` also
lose the conjuncts that repeated dropped hypotheses (v1 section 4). The fitted half of each must
have both outcomes in its training part under the witness split: to be checked on each (not
checked here).

### 5.8 Contracts whose text does not change

E1, E2, E4, E6, E7, F1, F2, A1, A3, G1, G3. E6, E7, F2, A3, G3 name a model through
`S.fit F1 = some m` (or P's) and say nothing on the run without a model: narrowing 8.

Section 9 of the informal specification ("the claims hold for inputs whose training part has
both outcomes") is to be replaced by: on a training part with one outcome both programs fit no
model and the train and metrics files are equal (levels 1 to 3); with both outcomes the fit is
taken to return a model, the same for both (G58 as narrowed).

## 6. (e) The cleared items

### 6.1 The 52

Statement "same" means the Lean statement is resubmitted character for character (shown with
`unchanged_check.py`), on the new definitions.

| Item | Statement | Proof | Why |
|---|---|---|---|
| `thm:T1` | same | **new work** | witness and seven more goals (5.6) |
| `thm:T0` | same | mechanical | date projection, filler, helper of P1 |
| `lem:py_clean_frame`, `lem:pr01_clean_frame`, `lem:py_input_check_no_stop`, `lem:py_split_input_ids` | same | unchanged | clauses 1 to 5 only |
| `lem:sas_split_input_ids`, `lem:sas_features_present_paired`, `lem:sas_features_shape`, `lem:sas_features_some_paired` | same | unchanged | `Paired` 1, 2; features step |
| `lem:sas_fit_term_names` | same | mechanical | `Paired` 3 has two cases; step 04's new result |
| `thm:G1_run_coverage`, `thm:A1_run`, `thm:E1_features_train`, `thm:E2_features_valid`, `thm:F1_income_medians` | same | unchanged | features stage |
| `lem:sas_reached_feature_shape` | same | unchanged | `keeps py.readFeatures` untouched |
| `thm:E3_fit` | same | **new work** | the no-fit case (5.2) |
| `thm:E4_score` | same | mechanical | `score` on the new steps 10, 12, 14 |
| `thm:E5_train_scores` | **restated** | new work | 5.3 |
| `thm:A2_train` | **restated** | new work | 5.3 |
| `thm:G2_train_coverage` | **restated** | new work, the largest | 5.5 |
| `thm:F3_final_model_output`, `thm:F4_model_summary` | **restated** | new work | 5.3 |
| `thm:E6_score_test`, `thm:E7_predict_column_names`, `thm:F2_kaggle_submission` | same | mechanical | they get m's terms through `Paired` 3 (one `match`); predict unchanged |
| `thm:G3_predict_coverage` | same | mechanical | its proof opens steps 01 and 04 |
| `lem:metrics_flags_reached` | same | mechanical | clause 7 for the training flag: first case |
| `lem:metrics_score_frames` | same | **new work, small** | conjunct 16: first show `pd_logistic` and `credit_risk_score` are not missing in every row of S1 (present on a fitted valid run) |
| `lem:sas_reached_scores_read_shape` | **restated** | new work, small | see below |
| `thm:E8_validation_summary`, `thm:E9_ks`, `thm:E10_decile`, `thm:E11_threshold` | **restated** | new work | 5.4: the fitted case as today on the new units; the no-fit case |
| `thm:F5_calibration_plot`, `thm:F6_model_performance_metrics` | **restated** | new work | 5.4 |
| `thm:A4_metrics` | **restated** | new work, small | 5.4 |
| `thm:G4_metrics_coverage` | **restated** | new work | 5.4 |
| `lem:ex_A1_run`, `lem:ex_A3_predict`, `lem:ex_E4_score`, `lem:ex_reached_features_predict` | same | unchanged, or mechanical if the proof spells the T1 witness | expected; proofs not read |
| `lem:ex_E3_fit`, `ex_E5_train_scores`, `ex_F3_final_model_output`, `ex_F4_model_summary`, `ex_A2_train`, `ex_A4_metrics`, `ex_G2_run`, `ex_G4_run`, `ex_metrics_run` | **restated** | new work | 5.7 |

Counts: restated 23 (13 contracts, 9 examples, 1 lemma). Same statement 29: unchanged 18,
mechanical 8, new work 3 (T1, E3, `lem:metrics_score_frames`); if their proofs spell the T1
witness, up to four examples move from unchanged to mechanical.

**`lem:sas_reached_scores_read_shape` must be restated.** It is stated for every model m and
concludes that `pd_logistic` and `credit_risk_score` are numeric in every row of either score
read-back of `S.score m F`. With conjunct 16 corrected this is false for a model with a term
naming no column of F (every probability missing, so the training read-back may return text).
New hypothesis: every term of m names one of the 36 candidates (which `lem:sas_fit_term_names`
gives for a fitted m). It is a shared lemma, not a contract; its two users (E10, F5) have a
fitted m in the case where they use it. Lead to approve.

### 6.2 Proof work that is new, by size

1. G2: steps 03, 05, 06, 07, 08 on both outcomes; every step on the result with no fit.
2. T1: the witness.
3. E5, A2, F3, F4 on the run without a model: the port's units on the result with no fit
   against N2, N3 and the unchanged SAS train units, cell by cell (grade F, Decline, the rate,
   `pred_logistic` 0, the column order).
4. G4 and E8 to E11, F5, F6, A4 on the run without a model: the flags (3.6), `valid_exists`
   false, PSI on a column of missing scores read as numbers or as text (H15), the four SAS
   tables with no row.
5. E3: the two tests agree on the reached table.
6. The example pairs.

### 6.3 Cleared by the units' update, outside the 52

Read from `get_graph` (statement and proof consumers of the units of section 2). Each is a
theorem or lemma of version 2.3 that stands as a lemma for the equality proofs; each must be
resubmitted, and proved again where its unit changed in the case it speaks of.

- Train: `thm:train_run_01_fit_frame_C4` (if it has a negation item it goes with it: count the
  items), `thm:train_run_04_score_train_S7a`, `_S7b`, `thm:train_run_10_score_valid_S9a`,
  `_S9b`, `thm:train_run_11_confusion_valid_S10a`, `_S10b`,
  `thm:train_run_14_final_and_summary_S13`, `lem:ex_train_run_14_final_and_summary_S13`,
  `lem:py_score_fillers_idle`. `thm:train_run_09_confusion_train_S8a`, `_S8b` only if step 09's
  Lean is touched (its Python is not).
- Metrics: `thm:confusion_metrics_H13`, `thm:metrics_run_03_thresholds_S16a`, `_S16b`,
  `lem:py_thresholds_table`, `lem:metrics_ks_table`, `lem:pl_sort_pd_logistic_table`,
  `lem:metrics_auc_table`, `lem:metrics_psi_table`, `thm:metrics_run_07_calibration_S20a`,
  `_S20b`, `thm:metrics_run_08_validation_summary_S21b`,
  `thm:metrics_run_09_model_performance_S22b`. S21b, S22b and `lem:metrics_ks_table` also name
  SAS units that change (C1, C3, C5): their hypothesis that the KS table has a row decides
  whether the edit is mechanical (SAS specification, section 9).
- Statements: unchanged in letters where the unit's signature is; a step whose argument list
  changed (04, 10, 14) takes the new arguments. For the lead: these are not contracts of
  version 3; a changed statement here is a lemma's, to be reviewed as such.

### 6.4 Reached by the profile refresh only

`thm:T2`, `lem:ex_T2_sas_run`, the 20 `lem:sas_cov_*`, `def:SasLinksOf`, `def:sasPipelineOf`.
Statements unchanged in letters. `lem:sas_cov_train_bins` changes in meaning with C6 (a wider
precondition is proved, the proof stands or shortens). `lem:sas_cov_credit_raw_clean` and
`lem:sas_cov_test_raw_clean`: the padded-text draft's note on their texts. Whether the three
metrics coverage lemmas (`train_bins`, `total_good_bad`, `decile_data`) are also stated on the
run without a model is question 6. Whether a refresh clears these items by itself is still not
known (question 7 of the SAS specification).

## 7. (f) Order

**Step 0, before anything is cleared.**

1. The requirements blueprint carries the restated Q27; the SAS clearing is done and signed off
   (its N1 to N3, C1 to C8, with W or K decided); the port's profile is refreshed to both.
2. The lead has amended `informal-spec.md` and `definitions-v3.md` (the texts of sections 3 to
   5), and has answered questions 1 to 6.
3. H15 is entered as a rule of the port's RULEBOOK 2.8 (port-side facts only), and X21, X22 as
   the evidence of the two fixes.
4. Fetch and keep `statement_lean` and `proof_lean` of the 52, of the items of 6.3 and 6.4, and
   the Lean of every definition to be edited. Count the items: 322.

**Step 1, the units (port translators), upstream first, each restated once:** the new helper
units if any; `def:classification_table` and its precondition; `def:hosmer_lemeshow_precond`;
steps 01 to 08 and 10, 11, 13, 14, 15 with their preconditions; `def:run_py_py_py` and its
precondition; `def:confusion_metrics`; the metrics steps and preconditions; `def:run_py` and its
precondition. Then the differential evaluation of 2.4.

**Step 2, the three definitions, in dependency order:** `def:pyPipeline`; `def:PyLinks` (it
depends on `pyPipeline` and on steps 01, 04); `def:Paired`. Each compiled against the accepted
units; reviewed by a prover who did not write it, clause against the port both ways, with the
degenerate arguments of C-a (empty table, one row, every outcome equal, no complete case).

**Step 3, the witnesses first:** T1, then T0. No contract is proved before both are.

**Step 4, lemmas of 6.3** (they are cited by the contracts), train then metrics.

**Step 5, the 52, in this order:** the four `lem:py_*`, `lem:pr01_*`; the five `lem:sas_*` of
`Paired`; G1, A1, E1, E2, F1; `lem:sas_reached_feature_shape`; E3; E4; E5; A2; G2; F3, F4; E6,
E7, F2, G3; `lem:metrics_flags_reached`, `lem:metrics_score_frames`,
`lem:sas_reached_scores_read_shape`; E8 to E11; F5, F6; A4; G4; the examples.

**Step 6:** the items of 6.4 against the new profile. Then the audit: every unchanged statement
character for character against the fetch of step 0; every restated statement against the
amended text by a reviewer who did not write it; no `sorry`, `axiom`, `native_decide`, `unsafe`;
item count accounted for; the final report rewritten (limits: the narrowings below as the owner
rules them).

## 8. Narrowings (the owner decides; none is taken here)

1. **A file that is not written and a header-only file are the same table.** `pyPipeline.metrics`
   gives the table with no row for `ks_statistic.csv` and `decile_analysis.csv` when they are
   not written (4.1); A4 says which of the two happened, E9 and E10 do not. Which header a
   header-only file carries (`validation_summary.csv`, `model_performance_metrics.csv`,
   `threshold_analysis.csv`, `risk_scores_validation.csv`, `model_summary.csv`) is not stated on
   either side. For F5 the stronger form is specified; its weaker form would add
   `calibration_plot.csv` to this narrowing. That the two programs write and omit the same
   files beyond this stays judge evidence (70c4d9c, 1a90814).
2. **With both outcomes the fit is still taken to return a result, and the same model on both
   sides** (`PyLinks` 6, `Paired` 3; G58 narrowed). The port's fit can stop there with an error
   (no convergence, two left-out parameters, 500 steps: v1 R5).
3. **Two facts about values of the fitted result stay assumed in `PyLinks` 6b**: -2 Log L of
   the intercept-only fit is not 0 (step 03 divides by 1 - exp(-m2ll0 / n)); no diagonal entry
   of the final covariance is negative (step 06 takes its square root). Both are true of the
   port's fit in exact arithmetic; neither is guaranteed by the code after the fit. Also asked,
   as shape and naming of what the fit builds: 6b (1), (3) and the covariance shape of clause 6.
4. **Clause 13**: `einsum_q` returns one value per row; with new helper units, possibly the
   like for `inv` and `solve`. The first thing `PyLinks` asks of a numpy routine.
5. **The owner's decision names two row bounds; two more bounds of the same kind stand next to
   them** and follow from nothing on valid input once the row bounds are gone:
   `hosmer_lemeshow_precond` (5), the group's sum of outcomes at most 2^52 in absolute value,
   and `classification_table_precond` (9), the sum of outcomes at most 2^52. If they stay, G2 is
   false on a valid input with enough rows, exactly as R1 of v1. I specify nothing for them:
   question 4. (`def:_hl_groups_precond` has the same bounds but no item consumes it.)
6. **Conjunct 16 as corrected is true of the reader on the files a valid run reaches, not on
   every table.** The text branch is allowed when the column is missing in every row; the real
   reader decides on the first 20 rows, so a table whose first 20 scores are missing and a later
   one present is read as text with a number text, which the clause does not allow. H15: no
   one-outcome run gives such a file. The same kind of residue was already in conjuncts 13 to
   16 (a `row_id` column missing in every row is read as text too); and 8b, 8c are the narrow
   forms the lead chose.
7. **`LinAlgError` stays outside the precondition G2 covers** (`np.linalg.solve` at
   `train.py:229` and inside `_kept`, `np.linalg.inv` inside `_inv_sas`): "covered" is the stated
   precondition, not "the stage cannot raise after the fit" (v1 R10).
8. **Predict on a run without a model is not a theorem.** E6, E7, F2, A3, G3 name a model
   through a fit that returned one. That both predict stages stop on a one-outcome training
   part is what the coefficient flags say on each side (`PyLinks` 7, `Paired` 5) and what the
   judge shows; no contract compares the two stops, because the interface gives `scoreTest` a
   model. The owner's three levels do not name predict.
9. **The run without a model is stated on SAS's tables** (N2, N3 and the units after them). On
   the SAS side that inherits its narrowings 1, 2 and 5 (no row for "not created";
   `logistic_no_fit` stated for complete tables with outcomes 0 or 1; one session per script).
10. **The examples of the fitted run** need a training part with both outcomes under the
    witness split. If an example cannot be rebuilt so, its contract's fitted case is reported
    vacuous, not proved (rule 4).

## 9. Questions for the lead

1. The informal specification is the text of record and E5, A2, A4, E8 to E11, F3 to F6, G2, G4
   change in text (section 5). Will the lead amend `informal-spec.md` and `definitions-v3.md`
   from this file before statements are written? I do not reword a contract myself.
2. 3.6: the second case in `PyLinks` 7 for the training score flag (7b, recommended), or the
   junk-model lemma on the port too?
3. 5.1: the run written out as a disjunction in each of the eight metrics statements, or one
   new definition item for it?
4. Narrowing 5: are the two sum bounds dropped with the two row bounds?
5. 2.1: `_kept`, `_inv_sas`, `_left_out`, `classification_is_made` as new units or as new
   parameters of `def:PyParams`? (As parameters each needs a clause of `PyLinks`, and
   `def:PyParams` changes.)
6. 6.4: the three metrics coverage lemmas of section 4a on the run without a model as well?
7. F5: the strong form (the port omits the file exactly when the SAS table has no row) or the
   weak one?
8. 6.1: approve the added hypothesis of `lem:sas_reached_scores_read_shape` (term names are
   candidates).
9. 5.7: one pair per example item, or separate items for the runs without a model?
10. Narrowing 8: is a statement about predict on a run without a model wanted, and in what
    form?

## 10. Risks

1. **Nothing compiled and no Lean written.** Every position, tuple component and argument list
   above is to be read again from the accepted units (v1 R7). Clause 6, 6b and the E5 and A2
   chains are the most exposed.
2. **Level 3 rests on three things outside this blueprint**: the SAS changes C1 to C3, C5, C6
   as specified; the SAS specification's 4.9 (the SAS score flags on a run without a model,
   "expected, not verified"); and W or K. If 4.9 fails, `SasLinks` (8) and with it `Paired` 5
   change, in this same clearing.
3. **The no-fit training score table must be the same table on both sides, cell for cell and in
   column order.** The port's is step 14's clean export of 51 columns; SAS's is N2 followed by
   four units. `_LEVEL_` (N2's open point) is dropped on the SAS side before the comparison. If
   they differ in a column the Lean keeps, E5's second half is a disproof, which is a result.
4. **H15 in the Lean.** The Lean's frame of a column of `Cell.str none` is a text column; that
   `metrics_run_06_psi` then gives bin 0 on every row depends on how `gt` of a text column
   against a null cut is translated. If the translators cannot make the unit return there,
   G4's no-fit case needs the identity branch only and conjunct 16's text branch is a disproof
   of G4 for the real reader: to be known at step 1, before `PyLinks` is entered.
5. **Size.** 23 restated statements, about 75 items to resubmit in all, G2 alone covering five
   more steps in two cases. The fitted halves of the metrics contracts are today's proofs on
   changed units; "as today" is an expectation.
6. **The two fixes are measured on fixed models.** X21 and X22 give SAS's behaviour on designs
   fitted without selection; whether the stepwise selection can end on such a model is not
   known (SAS specification, narrowing 7). The port follows SAS if it does; `PyLinks` assumes
   nothing either way after this change.
7. **Order between blueprints.** Requirements, then SAS, then the port; the port clearing
   cannot start before the SAS sign-off and the refresh.
