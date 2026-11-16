# Plan for the equality contracts: the port against the corrected SAS (2026-11-16)

A plan only. Nothing was stated, proved or changed on any blueprint; this file is the only thing
written. It holds no Lean (all Lean lives in the blueprints): definitions are described in words.

## 0. What was read, and what was not

- Read in full: `brief-prover.md`, `informal-spec.md` (v2.3), `reports/report-round5.md`,
  `migration/port-to-lean/update-after-verification.md`, RULEBOOK sections 2.6, 2.7, 2.8, 3, 6, 7.
  `changes.md`: headings and its last two sections only.
- SAS blueprint `3f5df696`: `def:sasPipeline`, `def:SasLinks`, `thm:sas_Q13`, `thm:sas_Q27`,
  `thm:score_chains_agree` (statements), and through them the requirement definitions
  `CreditRisk.Pipeline`, `MetricsTables`, `TrainOK`, `TestOK`, `InputOK`, `Fitted`, `decimal32`,
  `Q13`, `Q23`, `Q27`. The other 23 requirement definitions were not opened.
- Port blueprint `b41b22d4`: the four `run` items and their four preconditions,
  `def:fe_run_01_clean` (+precond), `def:fe_run_06_split`, `def:predict_run_02_medians`,
  `def:_into_float`; the texts of ten old theorems (two stage contracts, one step contract, one
  witness, three intent or closed-row contracts, the flagged C4 and its negation).
  The other step units were not opened: what this plan says about them comes from
  `update-after-verification.md` and from the signatures the `run` items show.
- `legacy/feature_engineering.sas` lines 125-163 and a search for `best12` in `legacy/`.
- Two things differ from the task as given. (1) The port blueprint lists **one** negation,
  `neg:train_run_01_fit_frame_C4_neg`, not 13; the other twelve are no longer in the item list.
  (2) `get_status` reports 319 items, 234 formalised, 84 statements to write, one flagged
  (`thm:train_run_01_fit_frame_C4`), `verification_approved` false.
- Nothing here was evaluated. Where a section says "expected", it is a reading, not a result.

### 0.1 Profile check after the re-base (2026-11-16, read-only)

The owner re-based the port blueprint. Its id is now `5365851c-5549-44b7-9207-4bd4c422031d`;
`b41b22d4` is a stale copy and is read here only for comparison. Everything this file says of
"the port blueprint" now means `5365851c`.

- **The blueprint.** Same item list as before: 319 items, 234 formalised, the same 84 statements
  to write, no proof to write, one negation, `thm:train_run_01_fit_frame_C4` flagged,
  `verification_approved` false. Two settings differ from the stale copy: the trust layers are
  **off** (the stale copy had Judging on) and the language reads "lean" (it read "python").
- **(1) Names resolve.** From `5365851c`: all 59 declarations of the requirements blueprint,
  among them `CreditRisk.Pipeline`, `MetricsTables`, `InputOK`, `TrainOK`, `TestOK`, `Fitted`,
  `decimal32` and the 26 definitions Q1 to Q16, Q18 to Q27; `Sas.Model`, `Sas.linpred`,
  `sasPipeline`, `SasLinks`, `sasLinks_witness`; the 26 `sas_Q` theorems, `score_chains_agree`
  and the lemmas `sas_feature_rows`, `sas_split_sat`, `sas_features_row_total`,
  `sas_Q27_clause1`, `sas_test_chain_agree`, `sas_links_sat`, `sas_test_feature_rows`,
  `sas_score_rows`, `sas_features_some`. Found by search over the profile; `sasPipeline`,
  `SasLinks`, `Sas.Model`, `sas_Q27`, `Q13`, `Q23`, `Q27`, `TrainOK` were also opened from a port
  item. Nothing the plan names is missing.
- **(2) Nothing stale.** `sasPipeline` and `SasLinks` as seen from `5365851c` are the same text
  as seen from `3f5df696` (17 parameters, with `importTestColumns`; links 1 to 8).
  `Q27`, `Q13`, `Q23` and `TrainOK` as seen from `5365851c` say what the statements of
  `def:Q27`, `def:Q13`, `def:Q23`, `def:TrainOK` in `006ff04c` say, clause by clause (the profile
  shows the elaborated form, the item the source form; names, constants, column lists and the
  order of clauses agree). Q27 is the reduced form of ruling G53.
- **(3) The 47 uncleared theorems.** 46 are in state proved with no failure recorded; the 47th
  is `thm:train_run_01_fit_frame_C4`, stated and flagged false, with its negation proved. All 47
  statements were read. They name 26 SAS units: `income_medians`, `credit_cleaned`,
  `credit_train_validation`, `credit_train_export`, `credit_validation_export`;
  `logit_scored_train_output`, `logit_scored_train`, `confusion_matrix_train`,
  `training_metrics`, `logit_scored_valid_temp`, `logit_scored_valid`, `confusion_matrix`,
  `validation_metrics`, `confusion_metrics_macro`, `risk_scores_train_clean`,
  `risk_scores_validation_clean`, `final_model_output`, `model_summary`; `test_cleaned`,
  `test_scored_temp`, `test_scored`; `threshold_analysis`, `calibration_data`,
  `calibration_plot`, `validation_summary`, `model_performance_metrics`; and the `Sas.` helpers
  (comparisons, `div`, `sumFn`, `minFn`, `maxFn`, `log`, `exp`, `round`, the SQL aggregates,
  `merge11`, `rankGroups`, `ofBool`, `drop`, `num`).
  - None of these 26 is a unit the corrections changed. `migration/legacy-to-lean/manifest.tsv`
    marks 23 "unchanged by the corrections"; `income_medians`, `validation_summary` and
    `model_performance_metrics` were re-evaluated in rounds 2 and 3 but not rewritten. The units
    the corrections did change or add (the input checks, `credit_imputed`, `credit_features`,
    `risk_scores_train` and `_validation`, `auc_pairs`, `auc_summary`, the KS, decile, lift and
    PSI units, `test_imputed`, `test_features`, `test_predictions`) are named only by theorems
    among the 84 already cleared.
  - Checked directly for four of them: `income_medians` (and its age-group helper),
    `validation_summary`, `model_performance_metrics` and `test_cleaned` have the same body seen
    from the stale copy `b41b22d4` (whose profile is the old SAS copy: `sasPipeline` does not
    exist there) and from `5365851c`. The other 22 units and the `Sas.` helpers rest on the
    manifest, not on a comparison. `Sas.` helpers moved home in round 3 (to the unit of `%num`);
    the manifest records a move, not a change of meaning.
  - **Limit.** The state "proved" is what the blueprint records. Nothing read-only shows that
    the 46 proofs were recompiled against the re-based profile, and with the trust layers off no
    judge has looked at them since. If the lead wants certainty, the owner or a writer must
    trigger a recompilation; a prover in read-only mode cannot.
  - S21b and S22b take the tables of `auc_summary`, `ks_statistic` and `psi_summary` as
    arguments under their own shape conditions (`wf_me_...`). The theorems still hold as stated,
    but those conditions were written for the old one-row shapes; whether the corrected SAS
    tables (for example `auc_summary` with no row) meet them is a question for the faithfulness
    lemmas of group D, not a staleness of the theorems.

## 1. The shape of the claim

### 1.1 The target: the port as a `CreditRisk.Pipeline`

The 26 requirements are predicates on a `CreditRisk.Pipeline` over the reals: five steps
(`features`, `fit`, `score`, `scoreTest`, `metrics`), each returning an `Option`, chained through
raw tables (`TrainOK`, `TestOK`), a seed, and the tables each step returns. The SAS result is
"requirement Qn holds of `sasPipeline` at every parameter meeting `SasLinks`". So the right
target is the same interface. Three new definitions in the port blueprint, then the contracts:

1. **`pyPipeline`**: the port wired into `CreditRisk.Pipeline` at the reals, "wiring only", as
   `sasPipeline` is for the SAS units.
2. **`PyLinks`**: the conditions on the port's parameters (section 2), one hypothesis.
3. **`Paired`**: how the port's parameters relate to the SAS parameters (section 2, last column).

**The claim.** For all port parameters and SAS parameters that are paired, for every raw
training table, raw test table and seed with `CreditRisk.InputOK`: each step of `pyPipeline`
returns what the same step of `sasPipeline` returns, on the arguments a run reaches. One contract
per output (section 4). Valid input only, as ruling G53 has it for the SAS; nothing is claimed off
`InputOK`, so the old part (b) of every step contract is dropped.

### 1.2 How the four stage functions are put on that interface

The stage functions take the tables *as read* (optional), explicit parameters for out-of-scope
code, and return files. The interface takes raw tables and the tables the steps return. The gap
is closed by making each reader, and each parameter that depends on the data, a function of the
pipeline argument that stands for the file, exactly as `sasPipeline` does.

| Pipeline step | Built from | How |
|---|---|---|
| `Model` | `Sas.Model ℝ` (intercept, terms) | the content of `model.json`, the second component of `def:run_py_py_py`. The same type on both sides, so that models can be compared and passed across |
| `features train seed` | `def:run` | `cs_training` is the port's import applied to `train`; `split_ids` is the split parameter applied to the seed and the ids of `train`; `full`, `input_best32`, `sas_best12` as they are. Result: the tables of `model_features_train.csv` and `model_features_validation.csv`; `none` when `run` is `none` |
| `fit F` | steps 01 and 04 of train (`def:train_run_01_fit_frame`, `def:train_run_04_score_train`) | stops when a feature file is absent (existence as a function of `F`, as on the SAS side); otherwise the model step 04 extracts from the fit parameter on `F` as read back |
| `score m F` | steps 10, 12, 14 of train (the validation chain) | on `F` as read back; the table of `risk_scores_validation.csv`. No stop, as on the SAS side |
| `scoreTest m test train` | `def:run_py_py` | `intercept`, `coefficients` from `m`; `cs_test` the port's test import applied to `test`; `income_medians` the medians file of the feature-engineering steps on `train`, read back, present or absent as a function of `train`; `model_coefficients_exists` a function of `m`. Result: the table of `test_predictions.csv` |
| `metrics S1 S2` | `def:run_py` | the two score tables read back, present or absent as functions of `S1`, `S2` (note `run_py` takes the validation table first). Result: the tables of `validation_summary.csv`, `ks_statistic.csv`, `decile_analysis.csv`, `threshold_analysis.csv` |

Two steps (`fit`, `score`) cannot be the stage function itself: `train.run` takes both feature
tables and does the fit and both scorings in one call, where the interface has one table per
call. They are wired from the stage's step units. So that `pyPipeline` is provably the port and
not a paraphrase, four **faithfulness lemmas** say: when the stage function returns `some files`
on the tables a run in sequence gives it, each compared file is the corresponding pipeline value.
For train this includes the port's counterpart of `thm:score_chains_agree`: the table of
`risk_scores_train.csv` (the training chain, step 04) is `score m F1`.

The number type: every port unit is generic; the contracts instantiate it at the reals, as
informal-spec v2 already decided. Nothing is claimed about `Float`.

### 1.3 Why not the other shapes

- *Per output file against inlined SAS units, as in v2.3.* That is how the 14 old stage contracts
  read. It does not give stage 6: the requirements are stated on a `Pipeline`, not on files.
  It stays the right form only for the files the interface does not carry (section 4, group F).
- *Equality of the two pipelines as functions.* False off valid input, and not demanded (G53).

### 1.4 How stage 6 follows

For each requirement Qn, one **transport lemma** that mentions only `CreditRisk` definitions:
if two pipelines agree on valid input (the conjunction of the equality contracts) and Qn holds of
the second, Qn holds of the first. 26 short proofs by rewriting; none looks at the port or at the
SAS. Then `Qn (pyPipeline …)` under `PyLinks` is: the equality contracts, `thm:sas_Qn`, the
transport lemma, and one lemma that for every port parameters meeting `PyLinks` there are SAS
parameters meeting `SasLinks` and paired with them (so that the SAS parameters disappear from the
final statement).

One point is not generic. `Q13` (and, by its text, `Q12`) asserts that *there is* a feature table
`Ft` with `score m Ft = some S`; `Ft` is the test feature table, which no step returns. Transport
then needs the two `score` steps to agree at that `Ft`, of which the bare statement of Q13 says
nothing. Two ways: (a) prove `score` equal on every table of feature shape (rows of one shape,
the model's columns numeric) and add a SAS-side lemma that the `Ft` of Q12 and Q13 has that shape;
(b) prove `score` equal on every table whatever its shape. (b) is unlikely to hold for tables
whose rows differ in their columns (`Pl.ofTable`). Plan on (a); the extra lemma is about SAS units
and can live in the port blueprint through the profile.

## 2. The port's parameters, their conditions, and their SAS partners

"Basis" names the rule of RULEBOOK 2.8 or the run a condition rests on. **No basis yet** means a
real run is needed before the condition may be stated; the runs are collected in 2.5.

### 2.1 Feature engineering, `def:run`

| Parameter | Stands for | Condition (`PyLinks`) | Basis | SAS partner and pairing |
|---|---|---|---|---|
| `full` | bracketing of the 8-operand horizontal sum | none: stated for both values (at the reals the sum does not depend on it) | E06; recorded limit "1 to 8 operands" | none |
| `input_best32` | `sas_compat.input_best32` on a text column | cell by cell the value `Sas.inputBest` reads from the text, null for null; a Float64 column of the frame's height (the unit preconditions ask the last part) | **no basis yet** for the values (run R1). The shape half is G27 (c), E08 | the SAS units call `Sas.inputBest` directly; this condition *is* the pairing |
| `sas_best12` | `sas_compat.sas_best12`, reached only when the import typed `MonthlyIncome` or `NumberOfDependents` numeric | reading back the BEST12. text gives the number again, for the numbers a valid file can hold in those columns | **no basis yet** (run R2). False as written for a number that needs more than 12 characters: decision D2 | none in the SAS Lean, which takes both columns as text always (`SasLinks` (1), clause c). The SAS program does the same conversion: `input(MonthlyIncome, best32.)` on a numeric column |
| `cs_training`, as a function of the raw table | `proc_import_csv(cs-training.csv, guessingrows=None)` | on a `TrainOK` table: a frame is returned (H7); one row per raw row, in order (H1); every row with the same twelve names in one order (H1; the requirements allow each raw row its own column order, the port's units do not); the ten other columns numeric cells with the value the requirements read (H2); `MonthlyIncome` and `NumberOfDependents` each, for the whole column, either numeric with null for a missing value, or text whose content reads as the value, a missing value being null or a text SAS takes for missing (H2); within `def:fe_run_00_input_check_precond` | H1, H2, H7 (E08 parts 1 and 4) | `importTrain`. No direct pairing: each side delivers the same raw table, the SAS always with two text columns. The proofs meet at the raw values |
| `split_ids`, as a function of the seed and the row ids | the split file after its casts | a table with a numeric `row_id` column and at least one row (the unit's narrowing); the ids listed are distinct ids of the training table; their number is 70 % of the rows rounded up | **no basis yet** as a rule (run R3). The file `inputs/split_ids.csv` is the SAS draw of the reference run; the port has no sampler and no seed | `split`: the rows `split seed t` selects are those whose `row_id` is listed. The count clause is what `SasLinks` (5) needs of the paired `split` |

### 2.2 Train, `def:run_py_py_py`

| Parameter | Stands for | Condition | Basis | SAS partner and pairing |
|---|---|---|---|---|
| `fmt_wd`, `fmt_oddsr`, `sas_d8`, `sas_d12_3`, `sas_pvalue`, `chi2` | formatters and the chi-square tail, used for `stepwise_summary.csv` and the `printed_*` files | none. To be confirmed by a lemma that no compared file depends on them | signatures of the step units | none |
| `inv`, `solve`, `matmul`, `matvec`, `dot`, `einsum_q`, `log1p`, `pow2` | numpy routines of steps 03, 06, 07, 08 (printed tables) | none, same remark. They do enter `def:run_py_py_py_precond`: see 4.3, coverage | signatures | none |
| `fsum` | `math.fsum`, inside `roc_association` (standard error) | none for the compared outputs (Area does not use it). Were a printed ROC table ever compared: `fsum` is the sum | G15, E07 | none |
| `today` | `dt.date.today()` | none for the interface. For `model_summary.csv`: the same date cell | P7 on the SAS side | `today` of `model_summary` |
| `stepwise`, as a function of the training feature table as read | the result of the out-of-scope fit | the final effects are distinct names among the 36 candidates; what the preconditions of steps 01 and 04 ask of its shape. The fit itself is assumed to return (the Python can raise `RuntimeError` when it does not converge: outside the model, H7) | the real run of T18; no rule of 2.8 covers the fit | `fit`: the SAS model at a table is the (intercept, coefficients) step 04 extracts. `SasLinks` (6) then follows from the first condition |
| `model_features_train`, `model_features_validation`, as functions of the table written | the two feature files read by `proc_import_csv(…, guessingrows=None)`; `none` = file absent | present exactly when feature engineering returned a result (H7); same 42 names and order, same rows and order, every cell numeric (H4); cell law: the value read is the BEST12. text of the value written, read as a number, **not** the value written, in 11 columns (H4) | H4 (E08 part 3, E09 A), H7 | `readFeatures`, `featTrainExists`, `featValidExists`. `SasLinks` (3) says the read-back is the identity; H4 says the port's is not. Decision D1 |

### 2.3 Predict, `def:run_py_py`

| Parameter | Stands for | Condition | Basis | SAS partner and pairing |
|---|---|---|---|---|
| `full`, `input_best32`, `sas_best12` | as in 2.1 | the same conditions; the same parameter values in both stages | as in 2.1 | as in 2.1 |
| `intercept`, `coefficients` | the parsed `model.json` | the model the train stage returned, unchanged by writing and reading the file | **no basis yet** (run R4); H7 only says the file exists | the model argument `m` of `scoreTest` |
| `model_coefficients_exists`, as a function of the model | whether `model_coefficients.csv` exists | true exactly when train returned a result | H7 | `coefExists`, `SasLinks` (8) |
| `cs_test`, as a function of the raw test table | header probe and import, lines 42-79 | on a `TestOK` table: `some (header, rows)` (H7); names, order, rows and kinds as for the training import (H1, H2), with `SeriousDlqin2yrs` text and null throughout when no outcome is stated (H2); a table with no row gives the twelve names with text exactly under `SeriousDlqin2yrs`, `MonthlyIncome`, `NumberOfDependents` and no row (H3); within `def:predict_run_00_input_check_precond` | H1, H2, H3, H7. A valid test file whose outcome column holds NA, 0 or 1 was **not observed** (2.8, point 2): run R5 | `importTest`, `importTestColumns`. As for training: no direct pairing |
| `income_medians`, as a function of the raw training table | `income_medians.csv` read with the default `guessingrows`; `none` = absent | present exactly when feature engineering returned a result (H7); five rows, the three columns numeric, read equal to written, null for null (H6) | H6 (E11, E09 A), H7 | `readMedians` (identity: agrees with H6), `mediansExist` |

### 2.4 Metrics, `def:run_py`

| Parameter | Stands for | Condition | Basis | SAS partner and pairing |
|---|---|---|---|---|
| `sas_best` (width 8), `parse_float` | `_into_float`: the BEST8. text of a count, read back | for a whole number n with 0 ≤ n < 10^8 the text is not empty and reads back as n; the text of a missing value is empty | the lookup tables of the harness (T20). Not a rule of 2.8, and bounded at 10^8: decision D4 | none: `total_good_bad` on the SAS side counts directly. The other use (`cumulative_lift`) feeds a printed file only |
| `sas_d8` | format of the printed ROC table | none | signature | none |
| `today` | the run date | none for the interface; for `model_performance_metrics.csv` the same date cell | P7 | `today` |
| `fsum` | as in 2.2 | none for the compared outputs | G15 | none |
| `risk_scores_validation`, `risk_scores_train`, as functions of the table written | the two score files read with `guessingrows=20`; `none` = absent | present exactly when train returned a result (H7); same 51 names, rows and order (H5); `default_flag` read as written; `pd_logistic` and `credit_risk_score` read through BEST12., every cell changed (H5 a); `interest_rate` read as text, `recommendation` possibly cut (H5 b, c): the metrics units must be shown not to read them, by a Lean lemma on the units, which settles "not observed" point 4 of 2.8 without a run | H5 (E08 part 3, E09 A-C), H7 | `readScoresValid`, `readScoresTrain` (identity in `SasLinks` (3)): decision D1. The pairing needs agreement on three columns only |

There is no port parameter for the SAS `agg` (PROC SQL sum and mean) or `arrange` (join order):
the port's sums and joins are modelled. Pairing: `agg` is the real sum and mean (that is
`SasLinks` (7)); `arrange` is the identity, because the port's joins keep the left order
(decision D6: v2.3 had this link as "there is an order").

### 2.5 Real runs needed before conditions are stated

| Run | For | What to run |
|---|---|---|
| R1 | `input_best32` | `sas_compat.input_best32` on the 89 texts of the SAS experiment x22 part A and on every `MonthlyIncome` and `NumberOfDependents` text of the valid files; compare with what SAS reads |
| R2 | `sas_best12` then `input_best32` | a valid training file with no NA in `MonthlyIncome`, holding incomes of 12, 13 and more significant characters, on the port and on SAS: what each exports |
| R3 | `split_ids` | check of `inputs/split_ids.csv` against the ids of `legacy/data/cs-training.csv`: distinct, all present, 105000 |
| R4 | `model.json` | the model read by predict against the model train returned, bit for bit, on the real run |
| R5 | test import | a valid test file whose `SeriousDlqin2yrs` holds NA on some lines and 0 or 1 on others: kinds and cells of `test_raw` |
| R6 | empty validation set | a completed sequence (train converging) whose validation set has no row: what train reads and writes, and what metrics does (2.8 "not observed", point 1). Bears on decision D3 |

Point 3 of "not observed" (a numeric score column blank in its first 20 rows) needs no run for
valid input if `pd_logistic` is never missing there, which the SAS lemma `lem:sas_score_rows`
gives on the SAS side and the equality contract carries to the port.

## 3. The old items

### 3.1 The 84 cleared theorems

Their texts cite informal-spec v2.x, the removed flags, the `wf_*` domains and "part (b) on every
well-formed input". None can be restated as it reads. By group (the counts add to 84):

| Group | Items | Recommendation |
|---|---|---|
| Stage contracts and witnesses | 18: the 14 file contracts `ST1` to `ST4`, and `W1` to `W4` | **replace** by the contracts of section 4; remove the old items |
| Flag contracts | 12: `run_F3_off`, `run_F3_on`, `run_F4`, `run_py_F1_frame`, `run_py_py_F2_frame`, `predict_run_02_medians_F2_on`, `_I2_on`, `_I2_off`, `metrics_run_06_psi_F1_on_bins`, `_F1_on_sum`, `_I1_on`, `_I1_off` | **remove**: the flags and both branches are gone from the port |
| Step contracts, parts (a) and (b) | 36: S1, S4, S5, S11, S12, S14, S15, S17, S18, S19, S21a, S22a, S23, S24, S26, S27, S29, S30 | **replace** by step lemmas on the frames a valid run produces (4.2), one per step, no part (b). Remove the old items |
| Predict against its training twin | 6: the five `S31` items and `predict_run_05_features_I8` | **remove**: this is requirement Q12, carried over in stage 6 |
| Intent contracts | 10: `I3` (two), `I4` (two), `I5` (four), `I6`, `I7` | **remove**: intent is now the 26 requirements |
| ROC helper | 2: `roc_association_H12`, `_C2` | H12: **restate** as a step lemma if `model_summary.csv` gets a contract (D5). C2: remove (3.2) |

The 47 theorems the update did not clear were re-read after the re-base: see 0.1 (3). 46 stand
as proved and name no SAS unit the corrections changed; the 47th is the flagged C4.

Removing an item is against the standing rule of this role ("never change an existing item").
It needs the lead's explicit instruction, per item list: decision D7.

### 3.2 The thirteen recorded differences

Twelve of the thirteen theorems are cleared (unformalised, text kept) and their negation items
are gone. The verdicts below are read from the texts and from `update-after-verification.md`;
none was evaluated.

| Item | What it recorded | Still applies? |
|---|---|---|
| `predict_run_02_medians_I2_off` | test incomes imputed from test-set medians | No. Step 02 is now the imported training medians table; the flag is gone. Covered by Q13 |
| `metrics_run_06_psi_I1_off` | PSI is 0 on untied tables whatever the shift | No. The PSI step is rewritten (training cuts, ten bins, floor 0.5 / rows). Covered by Q25 |
| `metrics_run_02_ks_I7` | `ks_statistic` can have more than one row | No. The step now returns one row. Covered by the KS requirement |
| `fe_run_04_imputed_I4` | an applicant can be left without an income | No on valid input: step 04 falls back on the overall median, and a valid training file has a known income. Covered by Q1 |
| `fe_run_05_features_I4` | the capped variable below the cap | To be re-checked: step 05 was rewritten in three places, none of them the caps. On valid input the two ratios are present; the witness probably used a missing value, which valid input excludes |
| `fe_run_05_features_I3`, `predict_run_05_features_I3` | a risk flag set while its variable is missing | Not on valid input (the variables are present after imputation). Off valid input it is shared with the SAS and no longer demanded (G53) |
| `predict_run_04_imputed_S31`, `predict_run_05_features_I8` | the predict copy of feature engineering differs from the training copy | To be re-checked by evaluation: both copies changed today. The claim is Q12 and is settled by the carry-over, not by a restated twin contract |
| `predict_run_07_predictions_I6` | a missing probability is predicted "no default" | The port still gives 0 for a missing probability, as the SAS does; it now grades it F first. On valid input no probability is missing. Not a difference between port and SAS |
| `train_run_12_risk_scores_I5_bands` | the grade bands against the model card | Probably not: the grade is now cut on `pd_logistic`, as in the corrected SAS. Covered by the grade requirement |
| `roc_association_C2` | `TauA` is 0, not missing, on a single-class input | Unknown: `roc_association` is rewritten. It concerns a printed column of the ROC table, which no contract covers. Remove |
| `thm:train_run_01_fit_frame_C4` (stated, flagged; negation proved) | the fit mask also drops a row with a missing `default_flag` | Yes, as a fact about the port: step 01 is unchanged and nothing cleared the item. No effect on valid input (`TrainOK` has the outcome on every row). Leave both items as they are |

## 4. The contracts, grouped for a team

### 4.1 Before anyone states a contract (one author, one reviewer, in order)

1. `def:pyPipeline` (1.2). 2. `def:PyLinks` (section 2). 3. `def:Paired` (section 2, last
columns). All contracts depend on these three; a change to any of them clears everything stated
on it, so they are reviewed against RULEBOOK 2.8 clause by clause and frozen first.
4. A new informal specification (v3) holding the text of each contract below: the prover brief
forbids wording a contract oneself.

### 4.2 Contracts and lemmas, by group (groups A to D can run in parallel)

| Group | Contracts (each on valid input, under `Paired`) | Step lemmas the group owns |
|---|---|---|
| A. Feature engineering | E1 training feature table; E2 validation feature table; faithfulness of `features` | the check does not stop and what frame it leaves; step 01 (both kinds of the two columns); medians of all groups; steps 03 to 06 |
| B. Train | E3 `fit` (by the pairing of the fit, plus file existence); E4 `score` on a table of feature shape; E5 the training chain equals `score m F1`; faithfulness of `fit` and `score` | steps 04, 09 to 14; S7, S9, S13 if they survive the re-base |
| C. Predict | E6 `scoreTest` table; E7 the column names of the two files (see D5); faithfulness of `scoreTest` | the test check; steps 01 to 08; the medians table of predict equals the SAS one |
| D. Metrics | E8 summary; E9 KS; E10 deciles; E11 thresholds; faithfulness of `metrics` | AUC pairs; KS; thresholds (S16 if it survives); deciles; PSI; validation summary; the lemma that metrics reads three columns only |
| E. Transfer (after A to D are stated, before they are proved) | SAS parameters exist for every port parameters under `PyLinks`; `PyLinks` and `Paired` can be met (witness); the 26 transport lemmas; the shape lemma for the `Ft` of Q12 and Q13 | none |
| F. Files outside the interface, if wanted (D5) | `income_medians.csv`, `kaggle_submission.csv`, `final_model_output.csv`, `model_summary.csv`, `calibration_plot.csv`, `model_performance_metrics.csv`, each against the SAS units inlined | H12 (ROC area), calibration (S20 if it survives) |
| G. Coverage | per stage: on valid input and under `PyLinks` the stage precondition holds, with the exceptions listed | none |

Each contract gets a reviewer who did not write it, before any proof, as in the brief.

### 4.3 Lemmas likely to be shared (state them as `lem:` items, as the SAS side did)

- From a frame to a table: `Pl.toTable` of a row-wise `withColumns`, `filter`, `drop`, `rename`,
  `select` is the SAS row operation on the table. The old proofs hold these inside their proof
  files; they must be lifted out once.
- At the reals: the port's Kahan, pairwise and striped sums are the list sum; the mean is the
  sum over the count; the port's median (`0.5 * (b - a) + a`) is the SAS median
  (`lo + (hi - lo) / 2`); no value is NaN or infinite.
- Order: the port's stable sort with nulls first is `Sas.sortBy`; the left join keeps the left
  order; groups in order of first appearance against ascending keys (harmless where a join on the
  key follows).
- The shape of every frame of a valid run (columns, kinds, which cells are present): one lemma per
  stage. It replaces the 28 `def:wf_*` items.
- Independence: a compared file does not depend on a formatter, on a numpy routine, on `fsum`, or
  on a column the stage does not read.
- From the SAS side, through the profile: `lem:sas_features_some`, `lem:sas_feature_rows`,
  `lem:sas_score_rows`, `lem:sas_Q27_clause1` and the other shared lemmas give what a valid input
  yields on the SAS side.

### 4.4 What I expect to be hard

1. **The two input checks and step 01.** The port strips, measures, upper-cases, renames
   case-blind and counts distinct ids with polars expressions; the SAS check is a row function.
   Only "does not stop on valid input, and leaves this frame" is needed, but the two possible
   kinds of each of two columns double every case.
2. **PSI, AUC pairs, deciles, KS.** All four port steps were rewritten today; the SAS-side proofs
   on the same units were the longest of that verification (Q25: 3237 lines of draft).
3. **Empty tables.** A valid training file of three rows or fewer puts every row in the training
   set (70 % rounded up), so the validation table is empty; a valid test file may have no row.
   `Pl.ofTable []` has no column, and three stage preconditions exclude an empty table.
4. **Coverage of the train precondition.** It carries the preconditions of the printed steps
   (Hosmer-Lemeshow, classification table), which depend on the numpy parameters. It cannot
   follow from valid input alone; v2.3 assumed it and showed one input meeting it.
5. **Size.** Round 5 lost a proof to client timeouts at 60 seconds. Keep each lemma small and its
   own item.

## 5. Decisions needed before contracts are stated

**Ruled by the owner on 2026-11-16** (requirements draft 7; SAS experiment x25). D1 is ruling
G55: the equality contracts are stated for one read-back shared by both sides and otherwise
free; the 26 requirements are carried over at the identity, said so in their text. D2 is ruling
G54: a present `MonthlyIncome` or `NumberOfDependents` is written in at most 12 characters;
valid input is narrowed (`TrainOK`, `TestOK`), the SAS is not changed. Nothing is stated on the
blueprint until that change is formalised and the owner has refreshed the profiles. The drafts
written meanwhile: `informal-spec-v3-draft.md` and `definitions-v3-draft.md`, next to this file.
D3 to D9 remain open.

**All nine decided, 2026-11-16.** D1 = ruling G55 and D2 = ruling G54 (owner). D3 to D9 settled
by the lead as recommended, two of them with the owner's answer:
- D3: no exception is written into the contracts; equality is stated on all valid input and
  decides each case; a coverage contract that fails is disproved and reported; the fit stays a
  parameter taken to return.
- D4: no bound of 10^8; the port's count round trip is linked to the SAS unit's own BEST8. rule,
  on the evidence of a run (being made by a port translator).
- D5: the interface outputs first, then one per-file contract for the six compared files the
  interface does not carry and the column names of predict's files; none for the coefficient,
  stepwise and printed files.
- D6: the SAS `arrange` is paired with the identity; tables are compared in order.
- D7 (owner): the 84 cleared theorems may be removed from `5365851c`; the 46 kept theorems,
  `thm:train_run_01_fit_frame_C4` and its negation stay. Judging stays off on `5365851c`
  (owner's choice): the match of Lean and text rests on the reviews. Record of the 84:
  `reports/removed-2026-11-16.md`.
- D8: the shape lemma for Q12 and Q13 lives in the port blueprint.
- D9: the size of the split is held by link, as a condition on the port's split parameter.

**D4 reopened the same day by rule H14** (port RULEBOOK 2.8): the port's count round trip
rounds from 10^8, the SAS Lean counts exactly under a precondition of fewer than 10^8 rows, so
the two do not agree beyond the bound and the decision goes to the owner, as D4 provided.
Recommended: a ruling that a raw file has fewer than 10^8 rows. See `definitions-v3-draft.md`,
notes after `PyLinks`.

The list below is kept as written before the decisions.

- **D1. Files read back.** `SasLinks` (3) takes every read-back as the identity. The port's is
  not (H4, H5: BEST12. changes 11 feature columns and both score columns), and the SAS program
  exports its feature files with `format _numeric_ best12.` too. Under identity on both sides the
  equality contracts say nothing about the real port. Recommendation: state the equality
  contracts for one read-back function shared by both sides and otherwise free, which covers the
  real one; carry the 26 requirements over at the identity, as the SAS verification has them, and
  say so in their text.
- **D2. An income column imported as numbers.** Port and SAS both pass it through BEST12.; the
  SAS Lean reads it exactly. Either valid incomes are limited to what BEST12. keeps, or the round
  trip is taken as a link known to fail beyond 12 characters. Run R2 first.
- **D3. Valid inputs the port's preconditions exclude**: an empty validation or score table, a
  final model with no effect, and a fit that does not converge (the Python raises; Q27 asks every
  step to produce its result). Are these valid inputs for the port's contracts, exceptions named
  in the coverage contracts, or a matter for the requirements?
- **D4. 10^8 rows.** The count link holds below 10^8; `InputOK` has no bound.
- **D5. Which outputs get a contract**: the interface outputs only (what stage 6 needs), or also
  the files of group F. `model_coefficients.csv` has no SAS unit to compare with. The column names
  of predict's files (E7) can only be compared with the documented list of names, not with a SAS
  Lean object.
- **D6. Join order.** Pairing `arrange` with the identity, in place of v2.3's "there is an order".
- **D7. The old items.** Leave to remove the 84 cleared theorems, in the groups of 3.1, and to
  supersede informal-spec v2.3 by a v3. Until they are removed or restated, `get_status` keeps
  84 statements to write and the blueprint cannot close. After the re-base (0.1) the count is
  unchanged on `5365851c`: the same 84 are without a statement. The 46 kept theorems need no
  action on the evidence of 0.1; the flagged `thm:train_run_01_fit_frame_C4` and its proved
  negation stay as the record of that difference unless the lead rules otherwise. Two further
  points for the lead: the trust layers of `5365851c` are off (should Judging be on before
  contracts are stated, as it was on the stale copy and is on `006ff04c`?), and whether a
  recompilation of the 46 kept proofs against the new profile is wanted before anything is
  built on them.
- **D8. Where things live.** `pyPipeline` uses `Sas.Model` and the requirement definitions. The
  re-base is done and checked (0.1): every name the plan uses resolves from `5365851c` and
  matches the current statements of `3f5df696` and `006ff04c`, so this no longer blocks stating
  the definitions; the other decisions of this section do (D1 and D2 are with the SAS translator). All new items go in `5365851c`, never in `b41b22d4`.
  Still open: the shape lemma for Q12 and Q13 is about SAS units: in the port blueprint, or
  added to the signed-off SAS blueprint?
- **D9. The split.** The port has no sampler: the seed reaches it only through the split file.
  Is the size clause of Q10 for the port then held "by link", as it is for the SAS draw?
