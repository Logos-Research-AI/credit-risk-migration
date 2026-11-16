# Draft texts of `def:pyPipeline`, `def:PyLinks`, `def:Paired` (2026-11-16)

**Draft, in words only. Nothing here is on a blueprint.** These three items are to be added to the
port blueprint `5365851c` only after the requirements change of ruling G54 has gone through and the
owner has refreshed the profiles (SAS, then port); a refresh would clear anything stated before it.
Each text below is meant to become the informal statement of its item. This file holds no Lean.

Rulings built in: G53 (valid input only), G54 (a present `MonthlyIncome` or `NumberOfDependents`
is written in at most 12 characters; it reaches these texts through `TrainOK` and `TestOK`), G55
(the equality is stated for one read-back shared by both sides; the requirements are carried over
at the identity). Marks `[D3]` to `[D9]` show where a text follows my recommendation on a decision
not yet settled; `[R1]` to `[R6]` where a real run of the port is still owed before the clause
may be stated (plan, section 2.5).

Vocabulary. A *read-back* is a function from the table a script writes to the table the next
script gets from the file. The *port parameters* are one record `py`; the *SAS parameters* are the
17 parameters of `sasPipeline`, written `sas`. "The raw table" is the argument of the pipeline
step; "as read" is what a reader parameter returns on it.

---

## 1. `def:pyPipeline`

**Text.** `pyPipeline py` is the Python port assembled as a `CreditRisk.Pipeline` over the real
numbers. It is wiring only: every value is computed by the port's own units (the four stage
functions `run`, `run_py_py_py`, `run_py_py`, `run_py` and the step units of train), applied to
the parameters in `py`. It contains no arithmetic, comparison or default of its own.

The parameters `py` are:

- the constants and routines the stage functions already take: `full`, `input_best32`,
  `sas_best12`, the formatters, the numpy routines, `fsum`, `today`, `sas_best` and `parse_float`;
- the two importers, as functions of a raw table: `importTrain` (what `proc_import_csv` makes of
  the training file) and `importTest` (the header probe and import of the test file);
- the split, as a function of the seed and of the row ids of the training table as cleaned: the
  table of selected ids;
- the fit, as a function of the training feature table as read: the stepwise result;
- five read-backs: of the two feature files (one function for both), of the medians file, of the
  validation score file and of the training score file;
- five existence flags, each a function of the value the producing step returned: the two feature
  files, the medians file, the coefficients file, the two score files (one flag each for the
  score files, so six functions if counted singly);
- the model file: a function from the model train returns to the intercept and coefficient list
  predict parses from `model.json`. `[R4]`

The fields:

- **`Model`** is `Sas.Model` at the reals: an intercept and a list of (name, coefficient). The
  same type as on the SAS side, so that one model can be given to both pipelines.
- **`features train seed`**: `run` applied to `importTrain train`, to the split table at `seed`,
  and to `full`, `input_best32`, `sas_best12`. When `run` returns nothing, nothing. Otherwise the
  pair (table of `model_features_train.csv`, table of `model_features_validation.csv`) among the
  files `run` returns.
- **`fit F`**: nothing when the flag says the training feature file is absent for `F`. Otherwise
  the model that step 04 of train (`train_run_04_score_train`) extracts from the fit parameter
  applied to the read-back of `F`, after step 01 (`train_run_01_fit_frame`): its intercept and
  its (name, coefficient) list, in its order.
- **`score m F`**: the validation chain of train, steps 10, 12 and the clean export of step 14,
  applied to the read-back of `F` with the intercept and coefficients of `m`: the table of
  `risk_scores_validation.csv`. It never stops, as on the SAS side.
- **`scoreTest m test train`**: `run_py_py` applied to: the intercept and coefficients the model
  file gives for `m`; `importTest test`; the read-back of the medians table that the
  feature-engineering steps of `run` produce on `importTrain train`, or absent, as the medians
  flag says; the coefficients flag at `m`; and `full`, `input_best32`, `sas_best12`. When
  `run_py_py` returns nothing, nothing; otherwise the table of `test_predictions.csv`.
- **`metrics S1 S2`**: `run_py` applied to the read-back of `S2` (validation, its first argument)
  and the read-back of `S1` (training), each present or absent as its flag says, and to
  `sas_best`, `parse_float`, `sas_d8`, `today`, `fsum`. When it returns nothing, nothing;
  otherwise the four tables of `validation_summary.csv`, `ks_statistic.csv`,
  `decile_analysis.csv`, `threshold_analysis.csv`, as `MetricsTables`.

**For the reviewer** (wiring, against `sasPipeline` field by field): which argument of each stage
function each parameter feeds; that `fit` and `score` use only step units of train and nothing
written here in their place; that the medians table of `scoreTest` is the one of the training
table (not of the test table); the order of the two arguments of `run_py`.

---

## 2. `def:PyLinks`

**Text.** `PyLinks py` is the conjunction of what the port's out-of-scope code is taken to do.
Each clause names the observation it rests on (RULEBOOK section 2.8 of
`migration/port-to-lean/`, rules H1 to H7, or a run). Nothing is asked of the formatters, the
numpy routines, `fsum`, `today` or `full`.

1. **Reading a number from text.** `input_best32` returns, for a text column, a number column of
   the same height whose every cell is what `Sas.inputBest` reads from the text, and missing for
   a missing text. (Shape: G27 (c). Values: `[R1]`.)
2. **The 12-character round trip.** For every number that can be written in at most 12
   characters, `input_best32` of the `sas_best12` text of the number is the number; a missing
   value gives a missing value. (Ruling G54; SAS half shown by experiment x25; port half `[R2]`.)
3. **The training import.** On a table meeting `TrainOK`, `importTrain` returns a frame: one row
   per raw row, in order; the twelve column names of the requirements in one order for all rows;
   the ten columns other than `MonthlyIncome` and `NumberOfDependents` numeric, holding the value
   of the raw cell; each of those two columns, as a whole, either numeric (missing for a missing
   value) or text (the text reads, by `Sas.inputBest`, as the value of the raw cell; a missing
   value is a missing text or a text SAS takes for missing). (H1, H2, H7.)
4. **The test import.** On a table meeting `TestOK`, `importTest` returns a header and a frame
   with the same properties, `SeriousDlqin2yrs` being text and missing throughout when no outcome
   is stated; on a table with no row, the twelve names, text exactly under `SeriousDlqin2yrs`,
   `MonthlyIncome`, `NumberOfDependents`, and no row. (H1, H2, H3, H7. A test file whose outcome
   column mixes `NA` with 0 or 1: `[R5]`.)
5. **The split.** For every seed and list of ids: the split table has one numeric column
   `row_id`; its ids are distinct and are among the ids given; their number is seven tenths of
   the number of ids, rounded up. (`[R3]` for the file of the reference run; the count is held by
   link, `[D9]`.)
6. **The fit.** For every table: the final effects of the stepwise result are distinct names
   among the 36 candidates, and the result has the shape steps 01 and 04 ask for. The fit is
   taken to return a result (a fit that does not converge is outside this model, `[D3]`).
7. **Files exist when written.** Each existence flag is true exactly when the producing step
   returned a result: the feature flags on every table, the medians flag on every training table
   for which the feature-engineering steps return, the coefficients flag on every model, the
   score flags on every table. (H7.)
8. **Read-backs keep the shape.** Each read-back returns a table with the same number of rows in
   the same order, each row with the same column names in the same order; a numeric cell of a
   column listed here stays numeric, and a missing one missing: all 42 feature columns; the
   three medians columns; `row_id`, `default_flag`, `pd_logistic` and `credit_risk_score` of the
   score files. Nothing is asked of the values, nor of the other score columns. (H4, H5, H6: the
   real readers keep this shape and change values to 12 characters; ruling G55 leaves the values
   free.)
9. **The model file.** The intercept and coefficients predict parses are those of the model
   train returned. (`[R4]`.)
10. **Counts as text.** For every whole number n, zero or more, that a count of rows of a valid
    run can be: `parse_float` of `sas_best n 8` is what the SAS unit `total_good_bad` makes of n
    by its own BEST8. rule, and the text is not empty; the text of a missing value is empty.
    (`[D4]`: stated against the SAS rule, with no bound of 10^8, if a run confirms the two rules
    agree at and beyond 10^8; otherwise the bound returns and the decision goes to the owner.)

**For the reviewer** (each clause against the port, both ways): too strong makes the proofs
unsound, too loose lets a disproof rest on something the port never does. In particular clause 8:
is "shape kept, values free" enough for the port's units to reach the same result as the SAS
units on the read table, or must a column's kind in the frame (`Pl.ofTable`) be fixed further;
and clause 3: the requirements allow each raw row its own column order, the port's frame has one.

---

## 3. `def:Paired`

**Text.** `Paired py sas` says how the port parameters and the SAS parameters are related, and
nothing about either side alone beyond what the relation needs.

1. **Imports.** The SAS importers meet clauses (1) and (2) of `SasLinks`: on a valid raw table
   they deliver that table, `MonthlyIncome` and `NumberOfDependents` as text, and the test
   columns as `importTestColumns` gives them. (No clause ties `py`'s importers to them directly:
   by `PyLinks` 3 and 4 both sides deliver the same raw values.)
2. **Split.** For every seed and table of feature-engineering rows, the rows the SAS `split`
   selects are exactly the rows whose `row_id` is in the port's split table for that seed and
   those ids.
3. **Fit.** For every table, the SAS `fit` returns the model whose intercept and (name,
   coefficient) list, in order, are those step 04 of train extracts from the port's fit on the
   same table.
4. **Read-backs are shared.** `readFeatures`, `readMedians`, `readScoresValid`,
   `readScoresTrain` of the SAS side are the port's four read-backs, as functions. (Ruling G55:
   one function for both sides, otherwise free within `PyLinks` 8. The identity is one such
   function; so is reading 12-character files.)
5. **Existence flags are shared.** `featTrainExists`, `featValidExists`, `mediansExist`,
   `coefExists` and the two score-file flags of the SAS side are the port's.
6. **Sums and order.** The SAS `agg` is the sum and the mean of the list (clause (7) of
   `SasLinks`); the SAS `arrange` is the identity (`[D6]`: the port's joins keep the left order,
   and the identity is a permutation, so clause (4) of `SasLinks` is met).
7. **The date.** The same `today`.

`Paired` deliberately does not include clause (3) of `SasLinks` (read-backs are the identity). It
is added, on both sides at once, only where the requirements are carried over (informal
specification v3, section 6).

**For the reviewer**: that under `PyLinks py`, `Paired py sas` and identity read-backs, every
clause of `SasLinks sas` follows (needed to use the 26 `thm:sas_Q`); and that for every `py`
meeting `PyLinks` some `sas` is paired with it (needed so that the SAS parameters disappear from
the carried-over requirements).
