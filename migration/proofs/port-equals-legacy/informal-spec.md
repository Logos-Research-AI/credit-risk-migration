# Informal specification, version 3: the port equals the corrected SAS

## Change note, 2026-11-19 (amendment 2 to version 3): the boundary of the claim

Owner's decisions of 2026-11-19, binding; they take precedence over any older text of this file.
One boundary, the same for every contract. No item carries a limit, hypothesis or "not covered"
of its own.

**B1. The claim.** End-to-end: on every valid input, the port writes the same compared files as
the corrected SAS program. Every contract (equality, coverage, unit lemma, example) is stated on
what the pipeline reaches from a valid input: the tables and argument values a run actually
passes to that step, never arbitrary tables or argument combinations the code never builds. A
statement that is false only on an input no run reaches is restated to the reached input (text
first, then Lean) and proved. That is not a narrowing.
Helper lemmas (the step lemmas kept from version 2.3) may carry conditions on their arguments
as long as every contract that uses them discharges those conditions in its proof; they add
nothing to the claim (owner, 2026-11-19: "Just finish", on the lead's recommendation).

**B2. Valid input.** `CreditRisk.InputOK`: section 3 of the requirements as signed off (Draft 10),
unchanged.

**B3. Step requirements are proved.** A unit may require something of its argument (its
precondition) only if the coverage contracts G1 to G4 and the lemmas of section 4a prove that the
pipeline passes such an argument on every valid input. In particular, these are proved facts, no
longer narrowings: `0 <= idx` of `train_run_06_coefficients_odds_precond`; the non-empty training
table of `run_py_precond`; `split_ids != []` and no NaN row id in `fe_run_06_split_precond`. If one
cannot be proved, the port is fixed. The first clause of `lem:sas_cov_total_good_bad` (fewer than
10^8 rows) follows from `InputOK` since G56 was made formal, and is proved.

**B4. The trusted base**, taken as given, stated once, the same for every contract:
1. *The model fit*: on a training part with both outcomes the fit returns a model, the same on
   both sides, with the value and shape facts of `PyLinks` 6, 6b and 14 (14: the final fit's first name is Intercept, C-k) (base (a) and (b) of section
   9). The classification table is part of the fit's output (base (d)).
2. *numpy linear algebra*: `solve`, `inv`, `matmul` and `matvec` behave as `PyLinks` 13 says, and
   on what a valid run reaches `solve` and `inv` raise no error for a singular matrix. Reason:
   selection leaves out every linearly dependent variable (X28), so the final model's matrix is
   invertible in exact arithmetic. This replaces the "not covered" sentence of G2: G2 has no
   limit of its own.
3. *Reading and writing files*: the CSV readers and writers are parameters described by `PyLinks`
   from observed runs (RULEBOOK 2.8), including conjunct 16 on the files a valid run reaches; a
   file not written and a header-only file are both the table with no row (base (c)).
4. *Floating point*: the Lean `Float` is taken as the arithmetic of both programs, including the
   recorded last-bit difference of `exp` and the fuel 4096 of `_randbelow`.

**B5. Outputs.** The claim covers exactly the files the parity judge compares. The printed
reports, the `printed_*` files, the coefficient and stepwise printouts and printed formats are
not part of the claim, listed once in section 9.

**B6. During a run** only a finding that would change B1 to B5 goes to the owner. Everything
inside the boundary is proved, or found to be a defect of the port and fixed.

**Note, 2026-11-20 (after amendment 2).** On valid input every row id the pipeline passes to the split is present and the split file fits (`lem:py_split_ids_finite`, `lem:py_split_fits`, both proved), so the draw on which Python's handling of NaN ids mattered is never reached. A NaN itself lies outside the real-number model (B4 item 4); the claim does not say NaN is proved impossible.

## Change note, 2026-11-18 (amendment 1 to version 3)

Entered for the lead as a records task (the lead commits); no blueprint item and no code was
changed with it. Source: `rounds/port-change-spec-2026-11-18.md` (C-g version 2) section 5, and
the decisions of 2026-11-18 listed here, which are binding. Where the amended text and older text
of this file differ, the amended text is in force. The statements are written from it only after
the steps of section 10, item 6.

Decisions applied:

- **Owner.** Every contract is proved; none keeps a hypothesis of its own. A training part with
  one outcome is covered on three levels: level 1 the fit (E3), level 2 the train-stage files
  (E5, A2, F3, F4), level 3 the metrics files (E8 to E11, F5, F6, A4, G4). Predict on a run
  without a model is stated: new contract P0. `SasLinks` (3) is weakened for the training score
  file (form W of `legacy-meets-requirements/reports/sas-change-spec-2026-11-18.md`, 4.8 c). The
  stated base of the claim is (a) to (d) of section 9.
- **Lead.** `PyLinks` 7 gains a second case for the training score flag (7b); the run of a
  contract is one definition item, `def:ScoreRun` (section 2a); `_kept`, `_inv_sas`, `_left_out`
  and `classification_is_made` become helper units, not parameters of `def:PyParams`; F5 in its
  strong form; the two sum bounds (`hosmer_lemeshow_precond` (5), `classification_table_precond`
  (9)) are dropped with the two row bounds; the shared lemma `lem:sas_reached_scores_read_shape`
  gains the hypothesis "every term of m names a candidate"; the examples are one pair per item
  (section 2b); Q27's "holds both outcomes" is read on the raw outcomes (ruling G59).

Changed by this amendment: E3 (a second case; text unchanged), E5, A2, F3, F4 (level 2); E8 to
E11, F5, F6, A4 (level 3); G2 (steps 03 and 05 to 08), G4; new P0; the run (section 2a); the
examples (section 2b); T0 and T1 (section 6, notes on the proof; statements unchanged); section
9 (the stated base); section 10, item 6. Unchanged in text: E1, E2, E4, E6, E7, F1, F2, A1, A3,
G1, G3, T2. The three definitions and the new `def:ScoreRun` are amended in `definitions-v3.md`
(correction C-g, version 2).

---

Version 3, in force from 2026-11-17 by the lead's instruction (it replaces version 2.3, kept as
`informal-spec-v2.3.md`). It is the text of record for every contract of the equality stage on
the port blueprint `5365851c-5549-44b7-9207-4bd4c422031d`. The three definitions all contracts
rest on are in `definitions-v3.md`. This file holds no Lean.

Why a version 3. Version 2.3 compared each Python unit with a SAS unit on "well-formed" frames,
with flags and with a part (b) off the domain. Since then: the SAS program was corrected and
verified against 26 documented requirements on valid input (signed off 2026-11-16); the port was
brought back in line with it; the flags are gone; ruling G53 limits every claim to valid input.
The claim is now stated on the interface the requirements use, `CreditRisk.Pipeline`, so that the
requirements can be carried over to the port (playbook stage 6).

Rulings built in: G53, G54, G55, G56, G57, G58 (narrowed 2026-11-18, section 9), G59. Decisions D1 to D9 of `plan-after-verification.md` are all
decided (2026-11-16): D1 and D2 by the owner's rulings G55 and G54; D3 to D9 by the lead as
recommended, D7 with the owner's answer (the 84 cleared theorems may be removed; Judging stays
off on `5365851c`, so the match of Lean and text rests on the reviews). The marks `[D3]` to
`[D9]` now show where each decision is applied.

## 1. Form of every contract

The contracts are items of the port blueprint `py-credit-risk-port` (`5365851c`). The SAS and
requirement declarations they name come through the profile from `sas-credit-risk-spec`
(`3f5df696`) and `credit-risk-requirements` (`006ff04c`).

**The three definitions** all contracts rest on (`definitions-v3.md`): `pyPipeline py`, the
port as a pipeline; `PyLinks py`, what the port's out-of-scope code is taken to do; `Paired py
sas`, how the port's parameters relate to the SAS parameters.

**The form.** "At the real numbers: for all port parameters `py` and SAS parameters `sas` with
`PyLinks py` and `Paired py sas`, for every raw training table, raw test table and seed that are
valid input (`CreditRisk.InputOK`), this step of `pyPipeline py` returns what the same step of
`sasPipeline sas` returns, on the arguments named." "Returns what" includes returning nothing:
if the SAS step stops, so does the port's, and conversely.

**Hypotheses.** `PyLinks py`, `Paired py sas`, `InputOK`, and, where a contract names arguments
that a run reaches, the equations saying they were reached. No other hypothesis may be added. In
particular no precondition of a port unit, no `wf_` domain, and no clause of `SasLinks` beyond
those `Paired` restates. A contract that cannot be proved or disproved as written is left open
and reported. (2026-11-18) The run hypothesis of section 2a, `def:ScoreRun`, is such a
reached-equation: a disjunction of two reached-facts, which widens a contract and adds no
hypothesis.

**Read-backs (ruling G55).** The files passed between scripts are read by one function shared by
both sides and otherwise free (`Paired` 4, `PyLinks` 8). Every equality contract therefore holds
both when hand-off files are taken at full precision and when they are read as the 12-character
files the programs write.

**Number type.** The reals. Nothing is claimed about `Float`: overflow, NaN, summation order.

**Disproof.** A contract that fails is disproved by its negation, proved with a concrete valid
input and concrete parameters meeting `PyLinks` and `Paired`; the input and one sentence on what
differs go in the negation's text. A checked disproof is a difference: the port changes.

## 2. Equality contracts on the interface

Write P for `pyPipeline py` and S for `sasPipeline sas`.

| # | Output | Statement, under the form of section 1 |
|---|---|---|
| E1 | training feature table | `P.features train seed` and `S.features train seed` both return a pair or both return nothing; when they return pairs, the first tables are equal |
| E2 | validation feature table | when both return pairs, the second tables are equal |
| E3 | the model | for the tables F1, F2 that `S.features train seed` returns: `P.fit F1` is `S.fit F1`. (Level 1, 2026-11-18: text unchanged; it has two cases, both proved. With one outcome in the training feature table as read, both return nothing; with both outcomes, both return the same model) |
| E4 | scores | (restated 2026-11-19 under B1, amendment 2) for F the training or validation feature table a run reaches on valid input (F1 or F2 with `S.features train seed = some (F1, F2)`) and every model m whose terms name candidates of step 01: `P.score m F` is `S.score m F` |
| E5 | the training scores of the port | (amended 2026-11-18, level 2) for F1 as in E3: the table of `risk_scores_train.csv` that the training chain of the train stage produces (step 04 onward) is `P.score m F1` when `P.fit F1` returns m; and when `P.fit F1` returns nothing it is the SAS training score table without a model (section 2a) on the feature table as read |
| E6 | test predictions | for F1 as in E3 and m with `S.fit F1` returning m: `P.scoreTest m test train` is `S.scoreTest m test train` |
| E8 | validation summary | (amended 2026-11-18, level 3) for F1, F2 and S1, S2 the score tables of the run (section 2a), fitted or without a model: `P.metrics S1 S2` and `S.metrics S1 S2` both return tables or both return nothing; when they return tables, the summary tables are equal |
| E9 | KS table | as E8: the KS tables are equal |
| E10 | decile table | as E8: the decile tables are equal |
| E11 | threshold table | as E8: the threshold tables are equal |
| R | the port returns (new 2026-11-20, `thm:R_port_returns`) | on every valid input and seed (`InputOK`), under `PyLinks`, the port pipeline returns: `P.features train seed` returns a pair F1, F2; then either the fitted run (a model m with `P.fit F1` returning m; `P.score m F1`, `P.score m F2`, `P.scoreTest m test train` and `P.metrics S1 S2` each return some table) or the run without a model (`P.fit F1` returns nothing; the training score table without a model on F1 is some table S1, the validation table has no row, `P.metrics S1` returns tables). Hypotheses `PyLinks`, `InputOK` only; no reached-equation |

(2026-11-20: row R moved into this table; it stood in a separate table after it.)

(E7 is in section 5.)

Amended statements, in words (2026-11-18). Write P for `pyPipeline py`, S for `sasPipelineOf
sas`.

- **E3.** Statement unchanged. Its second case: on a valid run the read-back of F1 is a training
  frame whose outcomes are 0 or 1; with one outcome `PyLinks` 6 gives the result with no fit,
  step 04 extracts no model and P returns nothing, and `logistic_no_fit` is true of the same
  table (`Paired` 4) so S returns nothing; with both outcomes `PyLinks` 6 gives a final fit,
  `logistic_no_fit` is false, and `Paired` 3 gives the same model.
- **E5.** The statement as before, with the chain on the units as changed (the idle arguments of
  steps 12 and 14 stay quantified, the new ROC flag among them), and a second conjunct for
  `P.fit F1` returning nothing, whose right side is the SAS training score table without a model
  (section 2a) on `sas.readFeatures F1`. The first conjunct is the former statement.
- **E8 to E11.** The conclusion letter for letter as before; the three hypotheses (m with
  `S.fit F1` returning m, `S.score m F1` returning S1, `S.score m F2` returning S2) become the one
  run hypothesis `ScoreRun` on the SAS side. On the run without a model both sides return four
  tables with no row: S by the SAS units as changed (`ks_statistic`, `decile_analysis`,
  `validation_summary`; `threshold_analysis` on no row), P by `valid_exists` false and the
  metrics field of `pyPipeline` as amended (a file not written is the table with no row).
- **E6.** Unchanged: it names a model through `S.fit F1` returning m. Predict on the run without
  a model is contract P0 (section 5).

**Shared lemma restated (lead, 2026-11-18).** `lem:sas_reached_scores_read_shape` is stated for
every model m and concludes that `pd_logistic` and `credit_risk_score` are numeric in every row
of either score read-back of `S.score m F`. With conjunct 16 of `PyLinks` corrected (H15) this is
false for a model with a term naming no column of F. It gains the hypothesis: every term of m
names one of the 36 candidates (which `lem:sas_fit_term_names` gives for a fitted m). It is a
lemma, not a contract; its users (E10, F5) use it with a fitted m.

## 2a. The run of a contract (2026-11-18)

Two runs, named once.

- **The fitted run** (as before): F1, F2 with `S.features train seed` returning them; m with
  `S.fit F1` returning m; S1, S2 with `S.score m F1` and `S.score m F2` returning them.
- **The run without a model**: F1, F2 as above; `S.fit F1` returns nothing; S1 is the SAS
  training score table without a model, that is `logit_scored_train_output_nofit` of the feature
  table as read (`sas.readFeatures F1`), then `logit_scored_train`, `risk_scores_train`,
  `risk_scores_train_clean`; S2 is the SAS validation score table without a model, that is
  `logit_scored_valid_temp_nofit`, then `logit_scored_valid`, `risk_scores_validation`,
  `risk_scores_validation_clean`: the table with no row.

**`def:ScoreRun`** (one definition item, lead's decision; its text is in `definitions-v3.md`):
the score tables of the run, fitted or without a model. In a statement "the run" is this one
hypothesis: there is m with the three fitted equations, or the fit returns nothing and S1, S2
are the two tables above. Both disjuncts are reached-facts, so it adds no hypothesis; it widens
each contract. On the port's own run (G2, G4, A2, and the port side of the examples) the same
definition is taken with P for S: the fit is `P.fit`, the score step `P.score`, S1 without a
model is the table of E5's chain at the stepwise result with no fit on `py.readFeatures F1`, and
S2 is the table with no row.

**Levels** (owner). Level 1: E3. Level 2: E5, A2, F3, F4. Level 3: E8 to E11, F5, F6, A4, G4.
G2 covers both outcomes and one outcome. Each is proved on both runs.

## 2b. Examples (rule 4 of the brief; lead, 2026-11-18)

Every contract's hypotheses must be shown satisfiable. Each restated contract with a new case
shows that case inhabited, in the same example item: each of `lem:ex_E3_fit`,
`lem:ex_E5_train_scores`, `lem:ex_F3_final_model_output`, `lem:ex_F4_model_summary`,
`lem:ex_A2_train`, `lem:ex_A4_metrics`, `lem:ex_G2_run`, `lem:ex_G4_run`, `lem:ex_metrics_run`
becomes a pair: the fitted run it shows today, and a run without a model on one small valid
input (four training rows, every outcome 0; the T1 parameters). P0, a new contract, is shown
inhabited by a run without a model of the same kind (the item is named when P0 is stated).
`lem:ex_G2_run`, `lem:ex_G4_run`, `lem:ex_F4_model_summary` lose the conjuncts
that repeated hypotheses now dropped. The fitted half of each must have both outcomes in its
training part under the witness split; if one cannot be rebuilt so, its contract's fitted case
is reported vacuous, not proved.

~~*Feature shape* (E4): every row of F has the same column names in the same order, no name twice;
every name of a term of m is among them; every cell is numeric. It is wider than "reached by a
run" on purpose: requirements Q12 and Q13 score a test feature table that no step returns
(section 6). The reviewer of E4 fixes the exact wording against the port's scoring units and the
SAS shape lemma of section 6 before it is stated.~~ *(superseded 2026-11-20: E4 was restated on
2026-11-19 under B1 on the feature table a run reaches (F1 or F2) and every model whose terms
name candidates of step 01; see E4 in section 2. E4 no longer uses feature shape. T2 (section 6)
keeps its own wording, which names the shape described in the struck text.)*

Tables are compared as tables: same rows in the same order, same column names in the same order,
same cells. `[D6]`: no contract is "up to the order of rows"; `Paired` 6 takes the SAS join order
as the identity.

## 3. Faithfulness of the assembly

`pyPipeline` wires `fit` and `score` from step units, because the train stage does the fit and
both scorings in one call. So that the contracts are about the port and not about a paraphrase:

| # | On | Statement |
|---|---|---|
| A1 | `run` | on valid input, under `PyLinks`: when `run` returns files on the imported training table and the split, the tables of its two feature files are the pair `P.features` returns |
| A2 | `run_py_py_py` | (amended 2026-11-18, level 2) on the port's own run, when the train stage returns (files, the optional content of `model.json`) on the two feature tables as read back: (1) `P.fit F1` is that optional model, as an equality of options; (2) with a model m, its `risk_scores_validation.csv` is `P.score m F2`; with none, it is the table with no row; (3) its `risk_scores_train.csv` is the table of E5's chain, written as E5 writes it, with the other arguments those the stage gives |
| A3 | `run_py_py` | when the predict stage returns on the arguments `P.scoreTest` gives it: its `test_predictions.csv` is `P.scoreTest m test train` |
| A4 | `run_py` | (amended 2026-11-18, level 3) when the metrics stage returns files on the arguments `P.metrics S1 S2` gives it, for S1, S2 the score tables of the port's own run (section 2a, fitted or without a model): there is T with `P.metrics S1 S2` returning T; `validation_summary.csv` and `threshold_analysis.csv` are among the files and are T's summary and threshold tables; and each of `ks_statistic.csv`, `decile_analysis.csv` is among the files and is T's table, or is not among them and T's table has no row |

A1, A3 and A4 hold by the way `pyPipeline` is written and are expected to be short; A2 is the
real one. A2's hypotheses are unchanged: `PyLinks`, `InputOK`, the reached-equation of F1, F2.
A4 says which of "written" and "not written" happened for the KS and decile files; E9 and E10
do not (section 9 (c)).

## 4. Coverage of the stage preconditions

The Lean of the port has no way to say "the Python raises": its units are total, and a case
where the program raises is excluded by the unit's precondition (RULEBOOK of the port, section
1). A contract of section 2 assumes no precondition, so by itself it does not say the real
stage completes. **The claim for a stage is therefore the pair**: its equality contracts and its
coverage contract. One contract per stage says the port's own stated precondition holds where a
valid run takes it:

| # | On | Statement |
|---|---|---|
| G1 | `run` | on valid input, under `PyLinks`, the precondition of `run` holds of the arguments `P.features` gives it |
| G2 | `run_py_py_py` | likewise for the train stage on the feature tables a valid run returns, read back (amended 2026-11-18: the whole precondition, steps 03 and 05 to 08 included, on both outcomes and on one outcome; below) |
| G3 | `run_py_py` | likewise for the predict stage |
| G4 | `run_py` | likewise for the metrics stage (amended 2026-11-18: on the port's own run, fitted or without a model; below) |

**G2, amended 2026-11-18** (owner's decision, steps 03 and 05 to 08). At the real numbers, for
all `py` with `PyLinks py`, for every valid input (`CreditRisk.InputOK`) and seed, with F1, F2
returned by `P.features train seed`: the whole precondition of `run_py_py_py`
(`run_py_py_py_precond`) holds of the real arguments of `run_py_py_py` on that run (not of the
filler frames of `P.score`): the stepwise result `py.fit` on the read-back of F1 (as `P.fit F1`
takes it), the routines of `py`, and the two feature tables as read back, each present or absent
as its existence flag at F1, resp. F2, says. Statement dependencies `def:PyParams`,
`def:PyLinks`, `def:pyPipeline`, `def:run_py_py_py_precond`; the precondition is named, not
copied. What steps 03 and 05 to 08 ask of the fit result on a training part with both outcomes
comes from clauses 6, 6b and 13 of `PyLinks` (correction C-g); the rest is proved. On a training
part with one outcome the fit result is the one with no fit (`PyLinks` 6) and the precondition
is that of the port as changed. The two row bounds and the two sum bounds were dropped from the
preconditions (owner and lead, 2026-11-18: `hosmer_lemeshow_precond` loses `yy.length ≤ 2^52`
and its clause (5), the group's sum of outcomes at most 2^52 in absolute value;
`classification_table_precond` loses `y.length ≤ 2^51` and its clause (9), the sum of outcomes
at most 2^52). The proof has two cases: both outcomes (steps 03, 05 to 08 from 6, 6b, 13 and
valid input) and one outcome (the precondition of each step on the result with no fit).
Hypotheses: `PyLinks py`, `InputOK`, the reached-equation of F1, F2; no other. ~~Not covered, and
stated in the precondition itself: an error of `np.linalg.solve` or `np.linalg.inv` on a
singular matrix (`LinAlgError`, `train.py:229`, inside `_kept` and `_inv_sas`): "covered" is
the stated precondition, not "the train stage cannot raise after the fit"~~ *(superseded 2026-11-19/20 by B4.2, C-l: the LinAlgError case is inside the claim)*; and that the fit
returns a result on a training part with both outcomes is the base (a) of section 9.

**G4, amended 2026-11-18.** On the port's own run, fitted or without a model (`ScoreRun` with P
for S, section 2a): the precondition of `run_py` holds of the arguments `P.metrics S1 S2` gives
it, spelled as `def:pyPipeline` writes them. On the run without a model: the validation argument
is the read-back of the table with no row (no row, by `PyLinks` 8); the training argument is the
read-back of the port's no-fit training score table, whose `credit_risk_score` is, by conjunct
16 of `PyLinks` as corrected, a numeric column of missing values or a text column of nulls, both
inside the precondition of the metrics stage as changed (observation H15). Hypotheses:
`PyLinks`, `InputOK` and the run; no other (the hypotheses of 2026-11-18 on `fsum` and on the
read-backs are now clauses 12 and 8b of `PyLinks`). G4 needs, proved and not assumed, that the
score tables of the run have one kind of cell per column (C-f) and, on the fitted run, that
`row_id`, `default_flag`, `pd_logistic`, `credit_risk_score` are present in every row of S1, S2
(8b).

`[D3]`: no exception is written into these. Where a valid input falls outside a precondition,
the coverage contract is disproved with that input: a difference, fixed in the port.

The empty validation set (rule H13 of the port's RULEBOOK 2.8) is closed by ruling G57: the
training data has at least 4 rows, a clause of `TrainOK`. With the split count held by link
(`PyLinks` 5) the validation set then has at least one row on every valid input, so **G2 is no
longer expected to fail** on that account; the real SAS fails on one to three rows as the port
does. G2 uses one shared lemma: from `TrainOK` and `PyLinks` 5, neither set of the split is
empty. A header-only test file is still valid input: the port completes (H13 (d)), so G3 is
expected to hold there.

The precondition of the train stage also carries conditions on the printed steps
(Hosmer-Lemeshow, classification table) that depend on the numpy parameters: G2 is stated for
the part that concerns the compared files, and the rest is reported as not covered.
**Superseded 2026-11-18** (owner): G2 covers the whole precondition, steps 03 and 05 to 08
included (the amended G2 above); what it asks of the numpy routines is clause 13 of `PyLinks`.

## 4a. Coverage of the SAS unit preconditions (stated first)

The SAS units are total too: where SAS would fail or do something the Lean does not model, the
case is in the unit's precondition. `sasPipeline` applies the units without their preconditions,
and the 26 `thm:sas_Q` do not assume them. Twice already a precondition turned out not to hold on
valid input (`total_good_bad` below 10^8 rows: ruling G56; `roc_valid` with both classes: the
one-class validation set, corrected in SAS round 6). So before any equality contract, one lemma
per unit of `sasPipeline` that has a precondition: on valid input, under `SasLinks`, the
precondition holds of the argument the pipeline gives the unit. They are stated in the port
blueprint, through the profile, about SAS units only (`lem:sas_cov_<unit>`). A lemma that fails
is a finding about the SAS verification, reported to the lead, not patched.

**Text of each lemma** (`lem:sas_cov_<unit>`): "At the real numbers. For all SAS parameters
meeting `SasLinks`, for every raw training table, raw test table and seed that are valid input
(`CreditRisk.InputOK`), the precondition of `<unit>` holds of the argument that `sasPipeline`
gives `<unit>` in the step named. Where the argument depends on a model or on tables the earlier
steps return, it is stated for the values a run reaches: F1, F2 with `features train seed`
returning them; m with `fit F1` returning m; for a scoring unit, F one of F1, F2; S1, S2 with
`score m F1` and `score m F2` returning them. No other hypothesis." For `total_good_bad` the
lemma ~~states the second clause only (`default_flag` numeric in every row); the first clause
(fewer than 10^8 rows)~~ states and proves both clauses (fewer than 10^8 rows; `default_flag`
numeric in every row) *(corrected 2026-11-20 against `lem:sas_cov_total_good_bad` as proved)*;
the first clause ~~is the stated limit of ruling G56~~ follows from `InputOK` since G56 was made formal, and is proved (B3; note of 2026-11-20). For `train_bins` there are two
statements in one lemma: the training use and the validation use (`valid_bins`).

The 20 units of `sasPipeline` with a precondition item, read from `3f5df696` on 2026-11-16
and re-read on 2026-11-17 after the round 6 revision and the owner's refresh of the port
profile (all 20 unchanged, word for word), and what each asks:

| Unit | Its precondition asks | Expected |
|---|---|---|
| `credit_raw_input_check` | each of the 12 raw columns is, in the whole table, numeric, or absent, or text with no exponent notation; no two column names equal up to capitalisation; `bad_row`, `known_income` not already columns | holds, from `SasLinks` (1) |
| `credit_raw_clean` | `MonthlyIncome`, `NumberOfDependents` are text cells of at most 32 characters with no letter e, E, d, D; the two `_num` names not already columns | holds, from `SasLinks` (1) c |
| `income_medians` | `age`, `MonthlyIncome` numeric cells in every row | holds |
| `income_medians_all` | `age_group`, `median_income` numeric in the medians table; no age group twice; `MonthlyIncome` numeric in the cleaned table | holds |
| `credit_cleaned` | `age`, `MonthlyIncome`, `NumberOfDependents` numeric; the three new names not already columns | holds |
| `credit_imputed` | `arrange` returns a permutation; `VAR1` a numeric cell in every row | holds, `SasLinks` (4) |
| `credit_features` | the nine input columns numeric; the 27 new names not already columns | holds |
| `credit_train_validation` | `Selected` a numeric cell in every row of the split | holds, from `SasLinks` (5): each row of the split is the row with `Selected` set to 0 or 1 |
| `logit_scored_valid_temp` | every model variable a numeric cell in every row of the table scored | needs `SasLinks` (6) and what the read-back keeps (`PyLinks` 8 under G55) |
| `test_raw_input_check` | as the training check, on the test table; a table with no row meets it | holds, `SasLinks` (2) |
| `test_raw_clean` | as `credit_raw_clean` | holds |
| `test_cleaned` | as `credit_cleaned`; no row meets it | holds |
| `test_imputed` | `arrange` returns a permutation | holds |
| `test_features` | as `credit_features` | holds |
| `test_scored_temp` | every model variable numeric in the test feature table | needs `SasLinks` (6) |
| `test_scored` | `predicted_logit` numeric in every row | holds |
| `test_predictions` | `pd_logistic` numeric in every row | holds |
| `total_good_bad` | fewer than 10^8 rows; `default_flag` a numeric cell in every row | ~~**first clause does not follow from valid input**: the stated limit of G56.~~ Both clauses proved (B3, 2026-11-20). ~~The lemma is stated for the second clause, and the first is reported~~ *(superseded 2026-11-20: the lemma states and proves both clauses)* |
| `train_bins` (also used for `valid_bins`) | `credit_risk_score` numeric; the names the step creates not already columns; the cuts table has at most one row with numeric cuts | holds; depends on the read-back keeping `credit_risk_score` numeric |
| `decile_data` | `pd_logistic` numeric; `decile` not already a column | holds; depends on the read-back |

The other units of `sasPipeline` have no precondition item. Units outside it with one
(`logit_scored_train_output`, `training_metrics`, `validation_metrics`, `roc_train`, `roc_valid`,
`roc_stats`, `kaggle_submission`, and the two printed-table units; since round 6 the two ROC
preconditions no longer ask for both classes: a one-class set is inside the unit, which returns
no row) matter only for the per-file
contracts of section 5 and get the same lemma there if those contracts are kept.

Under ruling G55 three of these depend on the read-back: with the identity (the SAS
verification's setting) they follow from the SAS shape lemmas; with the shared free read-back
of the equality contracts they follow from `PyLinks` 8. Both forms are stated.

(2026-11-18) The SAS clearing widens `train_bins_precond` (C6 of the SAS change specification:
`credit_risk_score` a numeric cell, or a text cell whose text is missing or blank) and weakens
`SasLinks` (3) for the training score file (form W). The 20 lemmas keep their statements in
letters. The three metrics coverage lemmas (`train_bins`, `total_good_bad`, `decile_data`) are
also stated and proved on the run without a model (lead, 2026-11-18, question 6 of the change
specification).

## 5. Outputs outside the interface `[D5]`

The playbook asks for one contract per output of the program. Six compared files are not carried
by the interface. Each gets a contract of the old per-file form: on valid input, under `PyLinks`
and `Paired`, the table of the file equals what the composed SAS units give on the same run.

| # | File | SAS units |
|---|---|---|
| F1 | `income_medians.csv` (restated 2026-11-20: the features stage returns files, and the table of the file among them equals what the SAS units give) | `income_medians_all`, `income_medians_export` |
| F2 | `kaggle_submission.csv` (restated 2026-11-20: the port stage returns files, and the table of the file among them equals what the SAS unit gives) | `kaggle_submission` |
| F3 | `final_model_output.csv` | `final_model_output` |
| F4 | `model_summary.csv` | `model_summary` |
| F5 | `calibration_plot.csv` | `calibration_data`, `calibration_plot` |
| F6 | `model_performance_metrics.csv` | `model_performance_metrics` |
| E7 | column names of `test_predictions.csv` and `kaggle_submission.csv` (restated 2026-11-20: the port stage returns files, and the column names of each file among them equal the names, in order, the SAS units give) | the names and order the SAS units give |
| P0 | (2026-11-18, owner) predict on a run without a model: no file | the stop of predict.sas (`predict_inputs_stop`) |

**Amended 2026-11-18.** F3 and F4 are at level 2, F5 and F6 at level 3. Port and SAS are
compared as written, no read-back, as before.

- **F3** (`final_model_output.csv`). The hypothesis "m with `S.fit F1` returning m" goes. Port
  side unchanged (the file among those `run_py_py_py` returns, on its new result type). SAS side:
  the stop of the SAS train stage; then `final_model_output` of `risk_scores_train` of
  `logit_scored_train` of the OUTPUT table, which is `logit_scored_train_output` at m with the
  logistic link when `S.fit F1` returns m, and `logit_scored_train_output_nofit` when it returns
  nothing. One equality whose SAS side branches on `S.fit F1`.
- **F4** (`model_summary.csv`). No condition on the outcomes of the training part, and the
  hypothesis "m with `S.fit F1` returning m" goes; the two read-back hypotheses of 2026-11-18 go
  too (they are clauses 8b and 8c of `PyLinks`). The SAS side takes the model as `S.fit F1`
  returns it, present or absent: the training chain as in F3, the validation chain from
  `logit_scored_valid_temp` at m, or from `logit_scored_valid_temp_nofit`; then `model_summary`
  at the date `sas.today` (`Paired` 7) as before. One equality whose SAS side branches on
  `S.fit F1`. On one outcome both sides are the table with no row (the port: `train.py:904`;
  SAS: `roc_train` of a one-class table has no row and `model_summary` then has none, R46).
- **F5** (`calibration_plot.csv`), strong form (lead). On the run of section 2a, fitted or
  without a model. Port side: the file among those `run_py` returns, on the arguments of
  `P.metrics S1 S2`. SAS side: the stop, then T, the table of `calibration_plot` of
  `calibration_data`. The equality: the port writes no file when T has no row, and writes T
  otherwise. This states when the port omits the file; on the fitted run it needs that T has a
  row (the validation table has one, G57).
- **F6** (`model_performance_metrics.csv`). The statement as before, with the run hypothesis of
  section 2a in place of the three reached-equations. On the run without a model both sides are
  the table with no row (the port: `metrics_calculation.py:536-542`; SAS: the changed
  `model_performance_metrics`). The file is written on both sides, as a header only.
- **P0** (new, owner). On the run without a model (section 2a: F1, F2 returned by
  `S.features train seed`, `S.fit F1` returning nothing): both predict stages return no result.
  Port side: `run_py_py` on the arguments the predict stage receives on that run, in which the
  train stage wrote no `model.json` (A2 (1): its optional model is absent), so the model-file
  argument says the file is absent; the predict stage returns nothing. ~~SAS side: the stop of
  predict.sas, `predict_inputs_stop`, is true because `model_coefficients.csv` does not exist
  (the train stage of a run without a model writes none; SAS change specification, 2.2).~~
  *(superseded 2026-11-20: the SAS half was restated by the lead at the owner's request and is
  proved in that form; see the note after this list.)* The
  statement does not go through `P.scoreTest` and `S.scoreTest`, which take a model; it is of
  the per-file form of this section. Hypotheses: `PyLinks`, `Paired`, `InputOK`, the run; no
  other. The exact spelling of the "file absent" arguments on each side is fixed by the stater
  against `def:run_py_py`, `def:pyPipeline` and `def:sasPipeline` and checked by the reviewer
  against this text; it must be what the real stages receive, not a free value.

**P0, SAS half restated (2026-11-20; as proved in `thm:P0_predict_no_model` on 5365851c).** The
SAS side no longer says the stop holds "because `model_coefficients.csv` does not exist"; the flag
is derived from the SAS run. Item statement text, SAS part, word for word: "SAS side, derived from
the SAS run and not from a literal: whether the SAS train stage writes `model_coefficients.csv` is
`def:model_coefficients_written` (train.sas 34-42, 116, 419-424) at the inputs of the SAS train
stage on that run, that is the two input-file flags and the training feature table as read,
exactly as `S.fit` receives them in `def:sasPipeline` (`featTrainExists F1`, `featValidExists
F1`, `readFeatures F1`); (1) on the run without a model this flag is false, and (2) the stop of
predict.sas, `predict_inputs_stop`, at the medians flag of `S.scoreTest` and at this flag as its
model-coefficients-file argument, is true." In symbols: `coefWritten :=
model_coefficients_written (sas.featTrainExists F1) (sas.featValidExists F1) (sas.readFeatures
F1) = false`, and `predict_inputs_stop (sas.mediansExist train) coefWritten = true`. The
validation flag is taken at F1 because that is how `sasPipeline`'s fit receives its inputs; it
equals the flag at F2 by `Paired` 5. Hypotheses unchanged: `PyLinks`, `Paired`, `InputOK`, the run.

**Restated 2026-11-20 (B1, lead; items proved on blueprint 5365851c).** F1, F2 and E7 change
from the conditional form to existence and equality, as F3 to F6 state equality of options.
F1: on valid input, under `PyLinks` and `Paired`, the run of the features stage returns files,
and the table of `income_medians.csv` among them is `income_medians_export` of
`income_medians_all age_groups (income_medians C) C` (C the cleaned SAS training import), as
`sasPipeline` composes them; no hypothesis beyond `PyLinks`, `Paired`, `InputOK`. F2: "the port
stage returns files and the table of `kaggle_submission.csv` among them equals `kaggle_submission
T`"; E7: "the port stage returns files and the column names of `test_predictions.csv` and
`kaggle_submission.csv` equal the SAS names, in order"; both for F1, F2, m as in E6 and the
call `(pyPipeline py).scoreTest m test train`. The port returning files is now part of the
conclusion, not a hypothesis; each statement is stronger than the earlier conditional form and
implies it. The only hypotheses left beyond `PyLinks`, `Paired` and valid input are the
reached-equations of F2 and E7 (shown inhabited by example items), which contract R below
concludes to exist.

**Contract R (new, 2026-11-20, `thm:R_port_returns`).** Stated in the table of section 2: the
port pipeline returns on every valid input. Test scoring is stated on the fitted run only; on the
run without a model the predict stage returns no result (P0).

~~E7, F1, F2 unchanged.~~ *(superseded 2026-11-20 by the note above.)* E6, E7, F2, A3, G3 name a model through a fit that returned one and say
nothing of the run without a model; that run is P0's.

Not given a contract, with the reason: `model_coefficients.csv` and `stepwise_summary.csv` (the
fit is out of scope on both sides and no SAS unit models them); the `printed_*` files (printed
formats); the ROC tables beyond the area.

## 6. Requirements carried over (stage 6)

**Owner, 2026-11-18: only T0, T1 and T2 of this section are kept.** The transports and the 26
carried requirements are dropped; the requirements are taken to hold of the port by the equality
(round record, owner's decision of 2026-11-18).

Stated only after every contract of section 2 is proved.

- **T0, parameters exist.** For every `py` with `PyLinks py` there is `sas` with `Paired py sas`;
  and when the read-backs of `py` are the identity, that `sas` meets `SasLinks`.
- **T1, not empty.** There is a `py` meeting `PyLinks` whose read-backs are the identity.
- **T0 and T1 after correction C-g (2026-11-18).** Statements unchanged. T1's witness: the fit
  depends on the table (the result with no fit on a training frame with one outcome, a constant
  intercept-only fit elsewhere); the constant fit's covariance is one row of one entry, any number
  not negative (1 is taken, so that the intercept is not read as left out); `einsum_q` gives 0
  for each row (clause 13); `fsum` constant 0; identity read-backs (conjunct 16 by its first
  branch); each flag is its side's reachability, the training score flag with the second case
  of 7b. T0: the date is the first part of position 20 of `PyLinks`; the witness of `sas.fit` is
  `Paired` 3 with its filler; `SasLinks` (6) from `PyLinks` 6 (first part) and the filler's empty
  term list; (8) by construction, through the SAS pipeline with its no-fit branch; `Paired` 1
  through a helper ("the tightened delivery of `SasLinks` (1), (2) implies the old one"); and
  `SasLinks` (3) as weakened (form W) at the identity read-backs, which meet it. T1, then T0, are
  proved before any contract.
- **T2, the test feature table has feature shape.** For the SAS pipeline on valid input, the
  feature table that requirements Q12 and Q13 score meets the feature shape of E4. `[D8]`: an
  item of the port blueprint, about SAS units seen through the profile; the signed-off SAS
  blueprint is not touched.
- **Transport, one per requirement.** For each of Q1 to Q16 and Q18 to Q27: if two pipelines
  with the same model type agree as the contracts E1 to E4, E6 and E8 to E11 say, and the
  requirement holds of the second, it holds of the first. These name only `CreditRisk`
  definitions and neither program.
- **The 26 carried requirements.** For each: "For every `py` with `PyLinks py` whose read-backs
  are the identity, requirement Qn holds of `pyPipeline py`. The hand-off files are taken at
  full precision (ruling G55), as in the verification of the SAS program; what the 12-character
  files lose between scripts is outside this statement." Proved from `thm:sas_Qn`, the equality
  contracts, T0 and the transport lemma, and from nothing about the code. If a proof needs an
  argument about the port, the contracts or the conditions do not line up: that is a finding.

## 7. What stands from version 2.3, and what is withdrawn

- **Stand, as proved** (46 items, checked after the re-base, plan section 0.1): the helper
  contracts H1 to H11 and H13, and the step contracts S2, S3, S6, S7, S8, S9, S10, S13, S16,
  S20, S21b, S22b, S25, S28, with `predict_run_03_cleaned_S31` and C3. They are lemmas for the
  proofs of section 2 where their hypotheses can be met on a valid run; they are no longer the
  claim.
- ~~**Stands, as a recorded fact about the port**: C4 and its proved negation (the fit mask also
  drops a row with a missing outcome). No effect on valid input.~~ *(superseded 2026-11-19/20: C4 is restated and proved; the negation no longer stands)*
- **Withdrawn** (the 84 items the update cleared; their removal was allowed by the owner on 2026-11-16, `[D7]`; record in `reports/removed-2026-11-16.md`):
  the stage contracts ST1 to ST4 and witnesses W1 to W4 (replaced by sections 2 to 5); the flag
  contracts F1 to F4 of version 2.3 (the flags are gone); every part (b) and the `wf_` domains
  (G53); the intent contracts I1 to I8 (intent is now the 26 requirements); S31 and I8 (now
  requirement Q12); the cleared step contracts, which return only as lemmas inside the proofs or
  as `lem:` items shared by a group; H12 returns as a lemma if F4 is kept; C2 is dropped (a
  printed column).

**Note, 2026-11-20 (the `wf_` domains that remain).** "The `wf_` domains withdrawn" means
withdrawn from the claim, not from the blueprint. `wf_` hypotheses remain on step and helper
lemmas: `thm:train_run_04_score_train_S7a`, `S7b`, `thm:train_run_09_confusion_train_S8b`,
`thm:train_run_11_confusion_valid_S10b`, `thm:train_run_14_final_and_summary_S13`,
`thm:predict_run_03_cleaned_S25a`, `S25b` and `lem:train_run_04_score_train_S7_nofit` (also on
`S2a`, `S2b`, `S10a`, `S16b`, `S21b`, `S22b`), and 28 `def:wf_*` items remain in the blueprint.
No contract carries one (section 1). Under B1 they add nothing to the claim: S7a, S13, S25a and
S7_nofit are used by no contract; where a contract's proof uses one (S7b, S8b, S10b in F4;
S25b in E6 and F2; S21b in E8), the contract states no `wf_` hypothesis, so its proof
discharges the condition on the reached argument.

**What the claim counts (2026-11-20).** The claim is the contracts E1 to E11, F1 to F6, G1 to
G4, A1 to A4, T0 to T2, P0 and R (one item each on 5365851c, 30 items), each assuming only
`PyLinks`, `Paired`, `InputOK` and reached-equations (several assume fewer: R and G1 to G4 have no
`Paired`, T0 and T1 no input). The step and helper lemmas whose statements carry a unit precondition (`hpre`), a
`wf_` domain or a domain hypothesis and that nothing in the blueprint uses (roots of the
dependency graph, read 2026-11-20) are proved as stated but are not part of the claim, since no
contract uses them and their conditions are not discharged on reached input:
`thm:train_run_01_fit_frame_C4`, `thm:fe_run_02_income_medians_S2a`,
`thm:fe_run_02_income_medians_S2b`, `thm:fe_run_03_cleaned_S3a`,
`thm:train_run_04_score_train_S7a`, `lem:train_run_04_score_train_S7_nofit`,
`thm:train_run_10_score_valid_S9a`, `lem:train_run_10_score_valid_S9_nofit`,
`thm:train_run_11_confusion_valid_S10a`, `thm:train_run_14_final_and_summary_S13`,
`thm:metrics_run_03_thresholds_S16a`, `thm:metrics_run_03_thresholds_S16b`,
`thm:metrics_run_07_calibration_S20a`, `thm:metrics_run_09_model_performance_S22b`,
`thm:predict_run_03_cleaned_S25a`, `thm:predict_run_03_cleaned_S31`,
`thm:predict_run_06_score_C3`, `thm:confusion_metrics_H13`, `thm:proc_rank_groups_H11`,
`thm:sas_sum_H4`, `thm:sas_min_H5_min` (21 items). The unconditional helper roots
(`thm:eq_H1_eq`, `thm:ge_H1_ge`, `thm:gt_H1_gt`, `thm:flag_H2`, `thm:sas_exp_H7`,
`thm:sql_max_H9_max`, `thm:sql_mean_H9_mean`, `thm:sql_min_H9_min`; `sql_mean` with a hypothesis
on the aggregate only) are proved facts about the port's helpers and likewise not part of the
claim. Step lemmas with such hypotheses that a contract's proof does use (for example S3b in E1,
S7b, S8a, S8b, S9b, S10b in F4, S20b in F5, S21b in E8, S25b and S28 in E6 and F2, H10 in F6)
add nothing to the claim either: each contract proves their conditions on the reached argument.

## 8. How the work is divided

Stating order: the SAS coverage lemmas of section 4a first; then the three definitions; then
the contracts. Groups A (E1, E2, A1, G1; R from 2026-11-20), B (E3, E4, E5, A2, G2), C (E6, E7, A3, G3; P0 from 2026-11-18), D (E8 to E11, A4, G4) in
parallel; E (section 6) stated after A to D are stated; F (section 5) last. Every statement is
checked against this text by a teammate who did not write it before its proof is started. Shared
lemmas are `lem:` items (plan section 4.3).

## 9. Not covered

- The fit: stepwise selection and the optimiser, on both sides a parameter, assumed to return a
  model and the same model for both programs (ruling G58, a stated limit). Every report says:
  the equality is given the same fitted model; the claims hold for inputs whose training part
  has both outcomes (with one outcome the real SAS fits no model, experiment x27); and the two
  real fits agree only to the judge's tolerance (SAS stops at GCONV 1E-8).
  **Replaced 2026-11-18** by the stated base below.

**The stated base of the claim (owner, 2026-11-18).** On a training part with one outcome both
programs fit no model, and the train and metrics files are equal (levels 1 to 3, section 2a);
predict returns no result on either side (P0). The claim rests on:

- (a) **The fit, with both outcomes** (ruling G58 narrowed): on a training part with both
  outcomes the fit is taken to return a model, the same model on both sides (`PyLinks` 6,
  `Paired` 3). "No model" is exactly "one outcome"; a fit that stops in another way with both
  outcomes (no convergence, two left-out parameters, 500 steps on the port; a PROC LOGISTIC
  failure on the SAS side) is not modelled. Reports keep saying that the two real fits agree
  only to the judge's tolerance.
- (b) **The value and shape facts of `PyLinks` 6b and 6**: -2 Log L of the intercept-only fit is
  not 0; no diagonal entry of the final covariance is negative; the names, coefficient array and
  covariance shape of what the fit builds. True of the port's fit in exact arithmetic, not
  guaranteed by the code after the fit.
- (c) **A file not written and a header-only file are both the table with no row.** Which files
  exist, and the header line of a header-only file, are not represented; that the two programs
  write and omit the same files is judge evidence (x27, commits 70c4d9c, 1a90814). A4 and F5
  state, for the port, when the KS, decile and calibration files are omitted.
- (d) **The classification table is outside the SAS Lean** (it is part of the fit's output in
  `out-of-scope.tsv`). That the port does what SAS does on a leverage near 1 is evidence
  (experiments X21, X23), not a theorem; the port's rule is in its Lean (`classification_table`,
  an observation with `1 - h ≤ 1e-8` keeps its probability).

Ruling G59 (2026-11-18): requirement Q27's "the training part holds both outcomes" is read
on the applicants' raw outcomes (`SeriousDlqin2yrs` 0 and 1 among the training part's row ids),
not on the `default_flag` the pipeline writes. The contracts of this file name no requirement;
in them "one outcome" and "both outcomes" are tested on the training feature table as read, by
`PyLinks` 6 on the port side and `logistic_no_fit` on the SAS side.

Also recorded with the amendment (from section 8 of the change specification; listed for the
owner, not separately ruled): `PyLinks` 13 asks of a numpy routine that it returns one value per
row; conjunct 16 as corrected is true of the real reader on the files a valid run reaches, not
on every table (the reader decides on the first 20 rows); the run without a model is stated on
SAS's tables (`logit_scored_train_output_nofit`, `logit_scored_valid_temp_nofit` and the units
after them) and so inherits the SAS side's limits there (no row for "not created";
`logistic_no_fit` stated for complete tables with outcomes 0 or 1; one SAS session per script).
- CSV reading itself: the importers and read-backs are parameters, described by `PyLinks` from
  observed runs (RULEBOOK 2.8), not modelled.
- What the 12-character and 15-digit hand-off files lose, for the carried requirements (G55).
  The equality contracts do cover it.
- Printed formats, the `printed_*` files, the coefficient and stepwise files.
- Any input that is not valid (G53).
- ~~Raw files of 10^8 rows or more (ruling G56): the 8-character count round trip is taken as
  exact on both sides (`PyLinks` 10); beyond that size neither program counts exactly. Every
  report states this limit.~~ *(reworded 2026-11-20 under B3)* Raw files of 10^8 rows or more
  (ruling G56): not a limit of the claim. Since G56 was made formal, fewer than 10^8 rows is a
  clause of valid input (`CreditRisk.InputOK`, B2), so such a file is not valid input and falls
  under "any input that is not valid" above; on valid input the 8-character count round trip is
  exact on both sides (`PyLinks` 10) and the row bound of `total_good_bad` is proved (B3).
- Floating-point behaviour.

## 10. Owed before anything is stated

1. The requirements change of G54 formalised, and the owner's refresh of both profiles; then the
   profile check again, including the state of the 46 kept theorems.
2. (Done 2026-11-16: decisions D3 to D9 are settled.)
3. (Done 2026-11-16: the runs are rules H8 to H14 of the port's RULEBOOK 2.8; each clause of
   `PyLinks` cites its rule.) D4 is closed by ruling G56 (owner, 2026-11-16): counts are taken as exact on
   both sides and the claims hold for raw files of fewer than 10^8 rows. The empty validation set (H13) is closed by ruling G57 (at least 4 training
   rows; neither program changes).
5. The five differences on small valid inputs (`migration/legacy-to-port/small-inputs.md`),
   decided by the owner on 2026-11-16: the port follows SAS on separation (c) and is fixed for
   (a), (b), (d), (e) as parity fixes, its Lean following; the SAS translator corrects
   `def:roc_train`, `def:roc_valid` and `def:model_summary` (no row when the set has one
   class) in the round 6 revision. Contract F4 is to be read against the corrected units.
4. Review of the three definitions: wiring, and each condition against the port in both
   directions.
6. (2026-11-18, amendment 1) Before the amended contracts are stated: the requirements
   blueprint carries the restated Q27; the SAS clearing (its new items `logistic_no_fit`,
   `logit_scored_train_output_nofit`, `logit_scored_valid_temp_nofit`, the changed metrics units,
   `train_bins_precond`, `sasPipeline`, and `SasLinks` with (3) in form W) is done and signed
   off; the port's profile is refreshed to both; observation H15 is a rule of the port's RULEBOOK
   2.8 (port-side facts only) and X21, X22 the evidence of the two fixes; the port's units are
   updated (`rounds/port-change-spec-2026-11-18.md` section 2, with the four helper units);
   then `def:pyPipeline`, `def:PyLinks`, `def:Paired`, and the new `def:ScoreRun` are entered
   from `definitions-v3.md` (correction C-g) and reviewed by a prover who did not write them;
   then T1, T0, and the contracts in the order of section 7 of that file.
