# Draft for the lead: the SAS side models "no fit" on a one-outcome training part (2026-11-18)

Status: draft, for approval. Nothing was changed on any blueprint, no code was changed, nothing
is committed. Author: prover (drafting step of the workflow).

This file holds no Lean. The standing rule of the prover role is that Lean lives only in the
blueprint, so every change below is given in words, with the names of the items and fields it
touches. The Lean is to be written on the server (as statement drafts) when the lead approves a
form. Nothing here was compiled.

Read for this draft:

- `C-g-draft-2026-11-18.md` (all, section 7 R2 in particular), `saslinks-padded-text-draft-2026-11-18.md`,
  `definitions-v3.md`, `requirements.md` (Q1 to Q27, section 3, rulings G53 to G58), RULEBOOK
  of `legacy-to-lean` R46.
- Experiment x27: `migration/legacy-to-lean/experiments/x27_one_class_roc.log` (the `X27 C60
  TABLE` and `FILE` lines), and the full SAS runs `judge/runs/x27_C60_full` (`run_meta.json`,
  the four logs, the files written).
- SAS blueprint `3f5df696`: `def:sasPipeline`, the three `*_inputs_stop` units,
  `def:logit_scored_train_output` (with `Sas.Model`), its precondition,
  `def:logit_scored_valid_temp`, `def:logit_scored_train`, `def:logit_scored_valid`,
  `def:risk_scores_train`, `def:risk_scores_validation`, the two `_clean` units,
  `def:confusion_matrix_train`, `def:training_metrics`, `def:confusion_matrix`,
  `def:validation_metrics`, `def:roc_train`, `def:roc_valid`, `def:model_summary`,
  `def:final_model_output`, `def:ks_statistic`, `def:decile_analysis`, `def:threshold_analysis`,
  `def:validation_summary`, `def:auc_summary`, `def:logit_scored_valid_sorted`; the statements
  of `thm:sas_Q14`, `thm:sas_Q27`, `thm:score_chains_agree`, `lem:sas_Q27_clause1`,
  `lem:sas_feature_rows`; the proof of `thm:sas_Q15`; `get_graph consumers_of` on 25 items.
- Requirements blueprint `006ff04c`: `def:Pipeline`, `def:Fitted`, `def:Q12`, `def:Q13`,
  `def:Q14`, `def:Q27`, and their consumers.
- Port blueprint `5365851c`: `def:SasParams`, `def:sasPipelineOf`, `def:SasLinksOf`,
  `def:Paired`, `def:pyPipeline`, the statements of `thm:E3_fit`, `thm:E5_train_scores`,
  `thm:A2_train`, `thm:F3_final_model_output`, `thm:T0`, `thm:T2`, `lem:sas_fit_term_names`;
  `get_graph consumers_of` on 11 items.

Not read: the proofs of the 34 SAS dependents other than `thm:sas_Q15` (the padded-text draft
read 12 of them where they open `hLinks`; I rely on its table), and the proofs on the port.

## 0. Summary for the lead

1. **What SAS does (x27, C60 and E60, and the full runs).** PROC LOGISTIC stops ("All
   observations have the same response"). train.sas runs on: `logit_scored_train` has every row
   with `pd_logistic` missing; no coefficient table, no item store; PROC PLM fails, so the
   validation chain has no row; neither ROC table; `model_summary` no row. It writes
   `risk_scores_train.csv` (every row, probability and score empty, grade F, Decline),
   `final_model_output.csv`, and `risk_scores_validation.csv` and `model_summary.csv` as a
   header only. It does not write `model_coefficients.csv`. predict.sas then stops at its input
   check (no coefficient file). metrics_calculation.sas does not stop, fails to import the
   header-only validation file, and writes three header-only files and no `ks_statistic.csv`,
   `decile_analysis.csv` or `calibration_plot.csv`.
2. **Where the SAS Lean is wrong today.** One place: `sasPipeline.fit` returns a model
   whenever the two feature files exist. Everything after it on the train side is already right
   once it is given "no model" (section 2): the units read a missing probability and a table
   with no row the way x27 shows.
3. **Smallest change (recommended, form U).** One new unit that says when PROC LOGISTIC fits
   nothing, and one more branch in the `fit` field of `def:sasPipeline`. The `fit` parameter
   keeps its type; `def:SasLinks` gets no new clause; no theorem signature changes. Section 3.
   The form the task names (the parameter returns an option, a link pins "none") is form O,
   section 3.4: same content, but it changes one binder in all 34 SAS statements and in `T2`.
4. **One requirement changes in statement: Q27.** With "no fit" modelled, Q27 as signed off is
   false of the SAS program on a valid input whose training part has one outcome. Either the
   owner restates Q27 (proposal in section 5) or `thm:sas_Q27` is disproved. Fourteen
   requirements (Q12 to Q16, Q18 to Q26) keep their statement and become silent on such
   inputs.
5. **Clearing.** On the SAS blueprint the edit of `def:sasPipeline` clears exactly the items the
   padded-text edit of `def:SasLinks` clears (the 34 dependents, and `def:SasLinks` restated):
   one clearing carries both. On the port blueprint it joins the clearing of C-g: 52 items.
6. **Not covered by the smallest change, and said so:** the metrics units of the SAS Lean do not
   say what SAS does on a validation score file with a header only (section 2.3). Under the
   recommended form no valid run reaches them there, so nothing false is claimed; the equality
   contracts of the metrics stage are then silent on a one-outcome training part.

## 1. What SAS does on a one-outcome training part

Source: `x27_one_class_roc.log`, block `X27 SUBMISSION C60_OBSERVE` (42 training rows, all
`default_flag` 0; 18 validation rows), and `judge/runs/x27_C60_full`. E60 (every outcome 1) is
reported the same by R46; I read the C60 lines.

| Table or file | Observed | Lean unit today, given what it would receive |
|---|---|---|
| PROC LOGISTIC | "ERROR: All observations have the same response. No statistics are computed." None of the ten ODS tables | the `fit` parameter returns a model (wrong) |
| `logit_scored_train` (OUTPUT, then `pred_logistic`) | 42 rows, 45 variables (42 features, `_LEVEL_`, `pd_logistic`, `pred_logistic`); `pd_logistic` missing, `pred_logistic` 0 | `logit_scored_train_output` needs a model: no way to say "missing in every row" |
| `model_coefficients`, `work.logit_model` | not created; `model_coefficients.csv` not written | no unit; the flag `coefExists` |
| `confusion_matrix_train`, `training_metrics` | 1 row each | `freq2`, `training_metrics`: agree |
| `logit_scored_valid_temp` (PROC PLM) | not created | `logit_scored_valid_temp` needs a model |
| `logit_scored_valid` | 0 rows (2 variables) | map of the empty table: agrees |
| `confusion_matrix`, `validation_metrics` | 0 rows | agree (`freq2` of nothing; `getLast?` none) |
| `risk_scores_train`, `_clean` | 42 rows; score missing, grade F, Decline, 20 % | `risk_scores_train` grades a missing probability F first: agrees |
| `risk_scores_validation`, `_clean` | 0 rows; the CSV is a header of 9 names | map of the empty table: agrees (the header is not represented, as R46 says) |
| `roc_train`, `roc_valid` | not created | no row (R46, in the Lean since 2026-11-16): agree |
| `final_model_output` | 42 rows | agrees |
| `model_summary` | 0 rows, 14 variables | no row (R46): agrees |
| predict.sas | stops: "The training medians or the model are not in the output folder" | `predict_inputs_stop` with `coefExists` false: agrees once no model exists |
| metrics_calculation.sas | does not stop; "Import unsuccessful" on the header-only file; `validation_summary.csv`, `threshold_analysis.csv`, `model_performance_metrics.csv` a header only; no `ks_statistic.csv`, `decile_analysis.csv`, `calibration_plot.csv` | see 2.3: the units disagree |

## 2. Where the fit enters, item by item

### 2.1 SAS blueprint

- **`def:sasPipeline`, parameter `fit`**: a total function from a table to `Sas.Model ℝ`. Field
  `fit` of the pipeline: nothing when `train_inputs_stop` of the two feature flags is true,
  otherwise the parameter applied to `readFeatures F`. This is the only place the parameter is
  called. Fields `score` and `scoreTest` take a model as argument (the interface gives it to
  them); `metrics` takes two score tables and no model.
- **`def:SasLinks`**: clause (6), for every table, every term of `fit F` names one of the 36
  candidates. Clause (8), last line: `coefExists m` is true exactly when the `fit` field of the
  pipeline returned m for some table. No other clause speaks of the fit. The text and comments
  of the 26 `thm:sas_Q` say "conditional on the fit" where they rest on (6).
- **`Sas.Model`** is declared inside `def:logit_scored_train_output`. Every item that names the
  type depends on that item: `def:SasLinks`, `def:sasPipeline` (through
  `def:logit_scored_valid_temp`), and through them everything. **Any edit of
  `def:logit_scored_train_output` clears the definitions downstream of it** (the scoring, ROC,
  summary and predict units), not only theorems. This is why the proposal does not touch it.
- **Units after PROC LOGISTIC** that take a model: `logit_scored_train_output` (with `invLink`),
  `logit_scored_valid_temp`, `test_scored_temp`, and the two printed-table units
  `logistic_association`, `logistic_lackfit` (not in the pipeline; R46 notes they still exclude
  one class by precondition). All the others take tables.
- **`thm:score_chains_agree`** is the only theorem that names the training chain. It is stated
  under `CreditRisk.Fitted`, so with a model.

### 2.2 The train units already follow x27

Given the two facts "the OUTPUT table has `pd_logistic` missing in every row" and "the PLM table
does not exist (no row)", every later train unit returns what x27 shows (table of section 1). I
checked each against its Lean by reading, not by evaluation. So only the two entry points lack a
"no model" form: `logit_scored_train_output` and `logit_scored_valid_temp`.

### 2.3 The metrics units do not follow x27 on a header-only validation file

On a validation score table with no row (which is how a file that cannot be imported would be
given to them):

| Unit | Lean on the table with no row | SAS (x27 C60 full run) |
|---|---|---|
| `ks_statistic` | always one row, both values missing | table not created, file not written |
| `decile_analysis` | always ten rows (rulings G41, G45) | table without columns, file not written |
| `validation_summary` | one row (the merge of `ks_statistic` and `psi_summary`) | header only |
| `threshold_analysis` | no row, as far as `confusion_metrics_macro` gives none on no row (not read) | header only |

This was outside valid input before (ruling G57: the validation part is not empty), and no rule
of the RULEBOOK covers "PROC IMPORT of a header-only file fails and the script runs on". The
interface cannot say it either: `MetricsTables` always holds four tables.

Consequence for this draft: the SAS Lean must not be made to reach the metrics units with such a
table on a valid input. Under both forms of section 3 it does not: the requirements and the
contracts reach `metrics S1 S2` only for S1, S2 returned by `score m F1`, `score m F2` with a
fitted m, and then S2 has a row.

### 2.4 Port blueprint

- **`def:SasParams`**: the record of the 17 parameters "in its order and with its types", then
  `today`. Field `fit : Table → Sas.Model ℝ`.
- **`def:sasPipelineOf`, `def:SasLinksOf`**: `sasPipeline` and `SasLinks` of the profile at the
  record. Their Lean names no type of a field.
- **`def:Paired`, clause 3**: for every table T, `sas.fit T` is the model whose intercept and
  terms are the third and fourth components of step 04 on step 01 of the port's fit on T.
  Clause 5, last line, is `SasLinks` (8) for `coefExists`, with P the SAS pipeline.
- **`def:pyPipeline`**: field `fit` returns a model whenever both feature flags are true (never
  nothing otherwise); field `score` takes the model. The port's Lean has not yet been updated
  for commits 65430e4 and 70c4d9c (read today: step 04's intercept is still a number).
- **Contracts that name the run through the SAS fit** (`S.fit F1 = some m` as a hypothesis, or m
  through it): E4, E6, E7, E8 to E11, F2 to F6, A4, G4 (through `P.fit`), and the lemmas
  `metrics_flags_reached`, `metrics_score_frames`, `sas_reached_scores_read_shape`. E5 and A2
  name it through the port's fit. E3 states `P.fit F1 = S.fit F1` as an equality of options.
- **`lem:sas_fit_term_names`**: for every paired `sas` and every table, the terms of `sas.fit F`
  are candidates. Used by nine proofs.
- **`thm:T2`** restates the 17 binders of `sasPipeline` and takes `SasLinks` and `Fitted`.

## 3. The smallest change

### 3.1 Form U (recommended): the test is a SAS unit, the parameter keeps its type

**New item `def:logistic_no_fit`** (SAS blueprint; a new item clears nothing). In words:

- Source text: the PROC LOGISTIC step of train.sas (lines 71 to 119), as for
  `def:logit_scored_train_output`.
- A Boolean of the training feature table as read. True when the `default_flag` values that are
  present in the table are all equal, which includes the table with no such value. In that case
  PROC LOGISTIC stops ("All observations have the same response", or "There are no valid
  observations") and fits nothing. Written with the comparison already used by `Sas.rocObs`
  (`RealLike.eqb`), over the list of present `default_flag` values: true for the empty list, and
  for a list whose every element equals its first.
- Comment to carry: R46 and x27 (C60: 42 rows all 0; E60: all 1; both classes in A4, B60, D60:
  the fit runs). OPEN: which rows PROC LOGISTIC uses when a candidate of the MODEL statement is
  missing was not run (the same open point as in `logit_scored_train_output_precond`); the unit
  is stated for tables in which the 36 candidates and `default_flag` are present in every row,
  and that condition goes into its text (amendment A10: where no precondition item exists, the
  paragraph is the condition). On a valid run every such cell is present
  (`lem:sas_feature_rows`).
- RULEBOOK: one sentence added to R46 ("In the Lean since ...: `logistic_no_fit`; the `fit`
  field of `sasPipeline` returns nothing there"). No new rule number is needed; x27 is the
  evidence already cited.

**Edit of `def:sasPipeline`, field `fit` only.** After the test of `train_inputs_stop`, a second
test: when `logistic_no_fit (readFeatures F)` is true, nothing; otherwise, as today, the
parameter applied to `readFeatures F`. Text: sentence (2) gains "and it returns no model when
PROC LOGISTIC fits nothing (`logistic_no_fit`, R46, x27): the script does not stop there, it
runs on without a model; the value of the parameter `fit` on such a table is not read". The
comment line "A step returns `none` when the stop unit of its script is true" gains "or, for
`fit`, when the procedure fits no model". One statement dependency added.

**`def:SasLinks`: no change for the fit.** Clause (6) stays as it is, for every table. Clause
(8) keeps its words; through P it now says that the coefficient file exists exactly for a model
of a fit that happened, which is what x27 shows (no `model_coefficients.csv`). One sentence of
text: "On a table where PROC LOGISTIC fits nothing the value of `fit` is not read by the
pipeline; clause (6) is still asked of it." The only Lean change to `def:SasLinks` is the
padded-text one.

**Why this is the smallest.**

- The 17 parameters keep their types, so the 34 SAS statements, `T2`, `def:SasParams`,
  `def:SasLinksOf` and `def:sasPipelineOf` keep their Lean, and the audit of round 6 (statements
  equal to `snapshot-round6.json` by hash) still applies to 32 of the 34 (all but the two about
  Q27).
- No existing unit is edited, so no definition is cleared.
- The behaviour is measured (x27), so by the RULEBOOK it belongs in a unit, like the one-class
  case of `roc_train`; it is not an open behaviour to be left to a parameter.
- What stays assumed is unchanged and said in one place: on a training part with both outcomes
  the fit returns a model (ruling G58, narrowed as in C-g R5: PROC LOGISTIC can also fail to
  converge; not measured).

### 3.2 The units after it

Under form U the pipeline needs nothing more: with no model, `score`, `scoreTest` and `metrics`
are not reached by any requirement.

For the port's contracts on the files of the train stage to say something on one outcome (they
are the reason for commits 65430e4), one more new item is enough, and no existing unit changes:

- **New item `def:logit_scored_train_output_nofit`** (level 2, optional; see 3.3). The OUTPUT
  table when the fit failed: every input row, in order, with `_LEVEL_` and then `pd_logistic`
  added, `pd_logistic` missing. Evidence: x27 C60, `logit_scored_train` 42 rows and 45
  variables; `risk_scores_train.csv` lines 2 and 3 (probability and score empty,
  `pred_logistic` 0, F, Decline). OPEN: the value of `_LEVEL_` was not printed; it is dropped by
  `risk_scores_train_clean`, not kept by `final_model_output` and read by no unit, so the unit
  writes the same cell as the fitted one and says so.
- **The validation chain with no model** is the table with no row, written as such where a
  contract composes the chain (the convention of R39 and R46: a table with no row stands for a
  table that was not created). `logit_scored_valid`, `risk_scores_validation`, the clean unit,
  `confusion_matrix`, `validation_metrics`, `roc_valid`, `model_summary` then give what x27
  shows, with no edit.
- `test_scored_temp`: not reached (predict stops on the coefficient flag). No change.
- `logistic_association`, `logistic_lackfit`: printed tables, not in the pipeline, no change;
  R46 already records them as not corrected.
- The metrics units: no change (section 2.3); see level 3 below.

### 3.3 Three levels, for the lead to choose

| Level | What the Lean says on a valid input with a one-outcome training part | SAS items | Port contracts |
|---|---|---|---|
| 1 | Both programs fit no model (E3: both sides nothing). Every contract that names the run through a fitted model is silent there, by its own reached-equation, with no hypothesis added | `def:logistic_no_fit` new; `def:sasPipeline` edited | no statement changes beyond those of C-g and of the port's Lean update |
| 2 | Level 1, and the train-stage files are equal: `risk_scores_train.csv` (E5, A2), `final_model_output.csv` (F3), `model_summary.csv` (F4), `risk_scores_validation.csv` with no row | level 1 and `def:logit_scored_train_output_nofit` new | E5, A2, F3, F4 restated: the SAS side takes the model as the option `S.fit F1` returns and uses the no-fit unit and the table with no row when it is nothing; `hm` is dropped from F3 and F4 |
| 3 | Level 2, and the metrics files on the header-only validation file | new rule and new evidence reading for "import of a header-only file fails"; `ks_statistic`, `decile_analysis`, `validation_summary`, the calibration and performance units change in substance; the interface cannot express a file that is not written | E8 to E11, F5, F6, A4, G4 restated on tables not named through `score` |

Recommendation: level 1 in the clearing, with level 2 added in the same clearing if the lead
wants F4's text of C-g section 4 ("on a one-outcome training part both sides give the table
with no row") to be a proved statement and not a remark. Under level 1 that sentence of F4 is
true but is not what F4 proves, because F4 keeps `hm`; C-g's F4 text must then be reworded to
"with one outcome `S.fit F1` returns nothing and the contract says nothing". Level 3 is a
separate piece of work and needs the owner: it changes units of the signed-off metrics chain
for a case no requirement reaches.

### 3.4 Form O (the form the task names): the parameter returns an option

- `fit : Table → Option (Sas.Model ℝ)`; the `fit` field is: nothing on `train_inputs_stop`,
  otherwise the parameter on `readFeatures F`.
- `SasLinks` (6) becomes "for every table and every model the parameter returns on it, every
  term names a candidate". New clause (6c): on a table in which the 36 candidates and
  `default_flag` are present in every row and `default_flag` is 0 or 1, the parameter returns
  nothing exactly when the `default_flag` values are all equal. It cannot be asked of every
  table: `PyLinks` 6 (C-g) pins the port's fit only on a training frame, and T0 must derive
  (6c) for the paired `sas`.
- Costs beyond form U: one binder changes in the 34 SAS statements and in `T2` (none is equal to
  the round 6 snapshot any more; the audit must compare modulo that binder);
  `lem:sasLinks_witness` and `lem:sas_links_sat` need a fit that depends on the table (a
  classical choice) in place of a constant; `def:SasParams` changes a field type, which clears
  its 39 statement consumers on the port by itself.
- Gain: `Paired` 3 can be an equality of options, and E3 stays a rewriting. Under form U the
  same fact (the SAS test and the port's test agree on the reached table) is proved in E3;
  under form O it is proved in T0. The mathematical content is the same.
- Both forms give the same pipeline on every table where (6c) speaks.

## 4. What it clears on the SAS blueprint, and which proofs change

`get_graph consumers_of def:sasPipeline` (2026-11-18): 34 statement consumers, no proof
consumer: `def:SasLinks` and 33 of the 34 dependents of `def:SasLinks`. The 34th,
`lem:sas_split_sat`, consumes `def:SasLinks` only and is cleared through it. So the edit of
`def:sasPipeline` clears `def:SasLinks` and the same 34 items as the padded-text edit. Not
cleared: `lem:sas_score_rows`, `lem:sas_features_row_total`, `lem:sas_test_chain_agree`, every
unit definition.

| Item | Statement | Proof after the change | Basis |
|---|---|---|---|
| `thm:sas_Q27` | Lean unchanged in letters (`CreditRisk.Q27` of the pipeline); **meaning and text change with `def:Q27`** | **substance**: the case of one outcome; with both outcomes, as before | statement read |
| `lem:sas_Q27_clause1` | **restated**: its conclusion copies Q27's clause | **substance**: must show that on a valid run every `default_flag` of F1 is present and 0 or 1 (`lem:sas_feature_rows` (a) and `TrainOK`), so that "both outcomes" is the negation of `logistic_no_fit`; then as before | statement read |
| `lem:sasLinks_witness`, `lem:sas_links_sat` | unchanged | mechanical: the padded-text edit; and clause (8) for `coefExists` if the proof opens the `fit` field (the witness flags are reachability, so expected by definition) | not read at that line |
| `thm:sas_Q12`, `Q13`, `Q14`, `Q16`, `Q18` to `Q26`, `thm:score_chains_agree` (those that get m's terms from link (6)) | unchanged | mechanical: where `Fitted` is opened to get m as the parameter's value, one more branch to discard (`split_ifs` already handles it if that is how it is written) | `thm:sas_Q14` depends on (6); proofs not read |
| `thm:sas_Q15` | unchanged | unchanged | proof read: it opens `score` and `scoreTest` only |
| `thm:sas_Q1` to `Q11`, `lem:sas_features_some`, `lem:sas_feature_rows`, `lem:sas_test_feature_rows`, `lem:sas_split_sat` | unchanged | unchanged (expected): the features step and the links only | padded-text draft, section 5 |

So: two proofs change in substance (`thm:sas_Q27`, `lem:sas_Q27_clause1`), two take the
mechanical edit of the padded-text draft, up to 14 may need one more branch, the rest resubmit
as they are. 32 statements should hash equal to `snapshot-round6.json`.

If Q27 is not restated (section 5, question 1): `thm:sas_Q27` and `lem:sas_Q27_clause1` cannot
be proved again; the result is a disproof (a valid training file with every outcome 0 and four
rows), to be recorded as such.

## 5. The requirements

`def:Fitted` is "features returned (F1, F2) and fit F1 returned m". Its statement consumers:
`def:Q12` to `def:Q16`, `def:Q18` to `def:Q26` (14).

| Requirement | Statement | Meaning |
|---|---|---|
| Q1 to Q11 | unchanged | unchanged: they do not speak of the model |
| Q12 to Q16, Q18 to Q26 | unchanged | **narrower**: each is asked of a run with a fitted model. Today the SAS Lean claims them for a model that the real SAS does not have on a one-outcome training part (the limit of G58). After the change no such model exists in the Lean, and these 14 say nothing there. That is ruling G58 made formal |
| Q12, Q13, Q14 (text only) | Lean unchanged | their texts say "that every step does produce its result on such inputs, so that no applicant is left unscored by an error, is Q27". After Q27 is restated this holds only with both outcomes: on one outcome the real SAS leaves every training applicant with a missing probability and scores nobody in validation or test. The sentence needs the words "when the training set holds both outcomes". I read these three texts; the same sentence may stand in others of the 14 |
| **Q27** | **changes** | see below |
| Q17 | withdrawn | |

**Q27 as signed off** asks, on every valid input, for F1, F2, a model m, S1, S2, S3 and M with
every step returning. `InputOK` does not ask for both outcomes in the training part (G58: "The
condition depends on the split, so it is not written on the raw files"). A training file of
four rows with every outcome 0 is valid. With "no fit" modelled, the SAS pipeline returns no
model on it, and Q27 is false of the SAS program.

**Proposed Q27** (for the owner; it is ruling G58 written into the requirement): on an input
that meets the conditions of section 3, feature engineering produces its result; and when the
training set it produces holds both outcomes (some row with `default_flag` 0 and some row with
`default_flag` 1), every later step produces its result. When the training set holds one
outcome nothing is required after feature engineering. Formally: for every valid train, test
and seed there are F1, F2 with `features train seed` returning (F1, F2), and if some row of F1
has `default_flag` 0 and some row has `default_flag` 1 then there are m, S1, S2, S3, M with the
five other equations of today's Q27.

- Cleared on the requirements blueprint: `def:Q27`, `def:Spec`, `thm:consistent` (its witness
  still meets the weaker Q27). The 26 count is unchanged.
- The SAS and the port blueprints read the requirements through the profile: the profile is
  refreshed before the SAS clearing.
- Alternatives. (a) A clause in `InputOK`: not possible as a condition on the raw files alone.
  (b) Keep Q27 and record that the SAS program does not meet it on a one-outcome training part:
  an honest result, but then "every requirement holds of SAS on valid input" is no longer the
  claim, and the port side has no Q27 to carry over. (c) Do not model "no fit" on the SAS side:
  against the decision of 2026-11-18.

## 6. The port blueprint

Everything here comes after the SAS blueprint is signed off again and the profile is refreshed,
and together with the port's Lean update for commits 65430e4 and 70c4d9c and with C-g.

**Definitions (form U).**

- `def:SasParams`, `def:SasLinksOf`, `def:sasPipelineOf`: Lean unchanged.
- `def:pyPipeline`, field `fit`: nothing also when step 04 extracts no model (the port's stage
  writes no `model.json`). This is the rewiring C-g R2 asks about; the exact words depend on the
  new signature of step 04 and belong to the port's Lean update.
- `def:Paired` 3: today an equality for every table with a model step 04 always gives. After
  the port update step 04 gives no intercept on a result with no fit, so the clause must change
  whatever the SAS side does. Smallest form that keeps it one equality at the same position:
  for every table T, `sas.fit T` is the model step 04 extracts from the port's fit on T, and,
  where it extracts none, the model with intercept 0 and no term. The second half is a filler
  that the SAS pipeline never reads (form U); it keeps `lem:sas_fit_term_names` true for every
  table and T0's witness of the same shape. Alternative: guard clause 3 ("where step 04
  extracts a model") and add `SasLinks` (6) to `Paired` word for word, as clause 5 does for
  (8); cleaner to read, but it shifts the positions every proof takes `Paired` apart by.
- `def:Paired` 1: since `Paired` is restated in any case, take **P2** of the padded-text draft
  (clause 1 tightened like `SasLinks` (1) and (2)); T0 then compiles against the new
  `sas_links_sat` without the weakening helper.

**Items cleared.** `consumers_of def:PyLinks`: 47 (C-g section 5). `consumers_of def:Paired`:
36, of which five are not among the 47: `lem:sas_features_present_paired`,
`lem:sas_features_shape`, `lem:sas_features_some_paired`, `lem:sas_fit_term_names`,
`lem:sas_split_input_ids`. Union: **52**, in one clearing. To be resubmitted against the new
profile without being cleared by these edits (whether a profile refresh clears them is the
question the padded-text draft left open): `thm:T2`, `lem:ex_T2_sas_run`, the 20
`lem:sas_cov_*`, `def:SasLinksOf`, `def:sasPipelineOf`.

**Proofs: what changes in substance.**

- `thm:E3_fit`: statement unchanged. New case: the read-back of F1 is a training frame whose
  outcomes are 0 or 1 (C-g R8); with one outcome the port's fit is the result with no fit
  (`PyLinks` 6), so P returns nothing, and `logistic_no_fit` is true of the same table (shared
  read-back, `Paired` 4), so S returns nothing; with both outcomes as today. The step "the SAS
  test and the port's test agree on this table" is new: `default_flag` of the rows on one side,
  `y_train` of step 01 on the frame on the other.
- Every proof that used the last three parts of `PyLinks` 6 (C-g section 2: G2, A2, E5, F3, F4,
  T1 and others found on resubmission): the fact "both outcomes" that C-g's clause 6 asks for
  now comes from the reached-equation `S.fit F1 = some m` (or `P.fit F1 = some m` and E3),
  through `logistic_no_fit`. This is how R2 of C-g is settled without a hypothesis and without
  a place in `Paired` or `InputOK` for the limit of G58.
- `thm:T0`: witness of `sas.fit` from the new `Paired` 3; `SasLinks` (6) from `PyLinks` 6
  (second part, for every table) and the filler; (8) by construction. Mechanical under P2.
- `thm:T2`: statement unchanged; proof mechanical where it opens `Fitted`.
- `thm:G2_train_coverage`, `thm:A2_train` (stated on the port's own run, no SAS fit in the
  hypotheses): they must cover the one-outcome run of the port as changed. That is C-g and the
  port update, not this draft.
- The example items (`lem:ex_E3_fit`, `ex_E4`, `ex_E5`, `ex_F3`, `ex_F4`, `ex_A4`,
  `ex_metrics_run`, `ex_T2_sas_run`, `ex_G4_run`): each shows a run with a fitted model
  exists. After the change that needs a training part with both outcomes under the witness
  split. If an example's data has one outcome in its training part, it must be rebuilt. Not
  checked here.
- Under level 2 only: E5, A2 (3), F3, F4 restated as in the table of 3.3; their one-outcome
  case is new proof work (the port's units on a result with no fit against
  `logit_scored_train_output_nofit` and the table with no row).

**Mechanical only:** the 41 other consumers of `def:PyLinks` as C-g lists them, with one more
place or projection where `Paired` is taken apart if the alternative form of clause 3 is chosen
(none with the recommended form).

## 7. One clearing per blueprint

**Requirements blueprint** (first; owner's sign-off): restate `def:Q27`; `def:Spec` and
`thm:consistent` again. Texts of Q12, Q13, Q14 corrected by `edit_text` only if that does not
clear their Lean (to be checked; otherwise leave the texts and record the reading in
`requirements.md`).

**SAS blueprint**, one pass:

1. Refresh the profile (new Q27). Fetch `statement_lean` and `proof_lean` of the 34 and of
   `def:SasLinks`, `def:sasPipeline` (procedure of 2026-11-17). Count the items: 146.
2. Add `def:logistic_no_fit` (and, at level 2, `def:logit_scored_train_output_nofit`). 147 or
   148 items. Nothing is cleared.
3. Restate `def:sasPipeline` (the `fit` field). This clears `def:SasLinks` and the 34.
4. Restate `def:SasLinks` once, with the padded-text Lean of
   `saslinks-padded-text-draft-2026-11-18.md` section 4 as it is (the fit adds nothing to it),
   and the text sentences of both drafts.
5. Resubmit: `lem:sasLinks_witness` and `lem:sas_links_sat` (the `SLS` edits of the
   padded-text draft); `lem:sas_features_some`, `lem:sas_feature_rows`,
   `lem:sas_test_feature_rows`, `lem:sas_split_sat`; `lem:sas_Q27_clause1` (restated) and
   `thm:sas_Q27`; the other 25 `thm:sas_Q` and `thm:score_chains_agree`.
6. Audit as in round 6: 32 statements against the snapshot by hash; the two Q27 items and the
   three changed definitions (`def:SasLinks`, `def:sasPipeline`, the new unit) reviewed by a
   second agent against x27; no `sorry` or `axiom` in 37 proofs. RULEBOOK R46 and
   `changes.md` amended. Sign-off again.

**Port blueprint**, one pass, after the SAS sign-off: profile refresh; the port's Lean update
for 65430e4 and 70c4d9c; `def:pyPipeline` (`fit`); `def:Paired` (1 by P2, 3); `def:PyLinks`
(C-g); then the 52, in C-g's order with `lem:sas_fit_term_names` and the four `lem:sas_*`
before E1.

## 8. Risks

1. **Nothing compiled, and no Lean written.** The new unit is three lines; the pipeline edit is
   one branch. The first submission will tell whether `RealLike.eqb` is the right comparison at
   that place and whether the 14 proofs that open `Fitted` survive the extra branch.
2. **Q27 is a signed-off requirement.** The whole proposal rests on the owner accepting a
   condition on the training set inside Q27. Without it the SAS blueprint ends with one
   disproved requirement.
3. **Vacuity.** Under level 1 every contract and requirement that goes through a fitted model
   says nothing on a one-outcome training part. That is a formal limit in place of the stated
   limit G58, not a proof that the port follows SAS there; the evidence for that remains the
   judge runs of 65430e4 and 70c4d9c (byte-identical files on C60 and E60). Level 2 turns the
   train-stage part into theorems; the metrics part stays evidence only.
4. **The metrics units on a header-only validation file are not what SAS does** (2.3). No valid
   run reaches them after the change, but the pipeline's `metrics` field is still defined on
   every pair of tables and would return four tables where SAS writes two files fewer. If a
   later contract names the one-outcome score files directly, this must be corrected first.
5. **Rows PROC LOGISTIC uses.** x27 ran complete tables only. The unit is stated for tables
   with the 37 variables present in every row. A table with a missing candidate is outside
   valid input (`lem:sas_feature_rows`), so nothing depends on it, but the port's test is on
   complete cases and the two tests are shown equal only on such tables.
6. **Other ways the real fit fails with both outcomes** (no convergence, C-g R5) stay assumed:
   "the fit returns a model exactly when the training part has both outcomes" is true of SAS
   only as far as x27 and the reference runs show. Reports must keep the sentence of G58 in its
   narrowed form.
7. **`PyLinks` 8 on the training score file of a one-outcome run** (C-g R6) is untouched by
   this draft: the real reader reads an all-empty `pd_logistic` column as text. No contract
   names that file under levels 1 and 2, but the clause is asked of every table.
8. **The filler in `Paired` 3** asks something of the SAS fit on tables where SAS fits nothing.
   It is never read, but a reviewer may prefer the guarded form.
9. **Header-only files.** A table with no row carries no column in the Lean. The header of
   `risk_scores_validation.csv` on a one-outcome run (9 names, not the feature columns) and of
   `model_summary.csv` are outside what any contract compares (R46: "not represented").
10. **Order between blueprints.** Three sign-offs in sequence (requirements, SAS, port). The
    port clearing cannot start before the first two are in.

## 9. Questions for the lead

1. Q27: take the restated form to the owner (section 5), or record a disproof of `thm:sas_Q27`?
2. Form U (a unit, no signature change) or form O (the parameter returns an option, a link
   clause pins "none")?
3. Level 1 or level 2 (section 3.3)? At level 1, C-g's text of F4 needs rewording.
4. `Paired` 3: the filler form, or the guarded form with `SasLinks` (6) restated in `Paired`?
5. P2 for `Paired` 1, now that `Paired` is restated anyway?
6. Is the difference of section 2.3 (metrics units on a header-only validation file) to be
   recorded as a stated limit, or opened as work for the SAS translators?
7. Does a profile refresh clear the port items that use `sasPipeline` and `SasLinks` only
   through the profile (`T2`, the 20 `lem:sas_cov_*`)?
