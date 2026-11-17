# Texts of `def:pyPipeline`, `def:PyLinks`, `def:Paired` (version 3, 2026-11-17)

The informal statements of the three definitions, in words. In force from 2026-11-17 with
`informal-spec.md` version 3. Each text is the informal statement of its item on the port
blueprint `5365851c`. This file holds no Lean. Since it was drafted the train stage changed
(`migration/port-to-lean/update-2026-11-17.md`: rules G29, G30; a final model with no effect is
inside the precondition; `LogisticFit` has a field `separation`): the author of the definitions
reads that record first and reports to the coordinator any clause it makes wrong.

Rulings built in: G53 (valid input only), G58 (the fit assumed, clause 6 and `Paired` 3), G56 (counts exact, clause 10), G57 (at least 4
training rows, through `TrainOK`), G54 (a present `MonthlyIncome` or `NumberOfDependents`
is written in at most 12 characters; it reaches these texts through `TrainOK` and `TestOK`), G55
(the equality is stated for one read-back shared by both sides; the requirements are carried over
at the identity). Marks `[D3]` to `[D9]` show where a decision is applied (all settled on
2026-11-16 as recommended); the runs R1 to R6 the plan asked for (section 2.5) are now recorded as rules H8 to H14 of
RULEBOOK 2.8 (`migration/port-to-lean/`, version 5), cited clause by clause.

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
  predict parses from `model.json` (the identity by rule H11; kept as a parameter so that the
  condition is visible).

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
   the same height. For a text of at most 32 characters made of digits with at most one point,
   the cell is the number written. For a missing text, an empty or blank text, `.` and `NA`, the
   cell is missing. Nothing is asked for any other text. (Rule H8, experiment E12; shape: G27
   (c). That `Sas.inputBest` reads the same on these texts is then a lemma about the SAS helper,
   not a condition here.)
2. **The 12-character round trip.** For every number, zero or more, that is written in at most
   12 characters in the sense of the requirements (`CreditRisk.decimal12`), `input_best32` of
   the `sas_best12` text of the number is the number; a missing value gives a missing value.
   (Rule H9, experiments E12 and E12b; ruling G54; SAS half: experiment x25.) See the note on
   G54 below.
3. **The training import.** On a table meeting `TrainOK`, `importTrain` returns a frame: one row
   per raw row, in order; the twelve column names of the requirements in one order for all rows;
   the ten columns other than `MonthlyIncome` and `NumberOfDependents` numeric, holding the value
   of the raw cell; each of those two columns, as a whole, either numeric (missing for a missing
   value) or text (a text of clause 1 that reads as the value of the raw cell; a missing value
   is one of the missing forms of clause 1). (Rules H1, H2, H7.)
4. **The test import.** On a table meeting `TestOK`, `importTest` returns a header and a frame
   with the same properties. `SeriousDlqin2yrs` is, as a whole column, numeric (when every
   stated cell is 0 or 1) or text (when all are missing, or one is written `NA`); the predict
   units are to be shown, by a lemma on the units, not to read it. On a table with no row: the
   twelve names, text exactly under `SeriousDlqin2yrs`, `MonthlyIncome`, `NumberOfDependents`,
   and no row. (Rules H1, H2, H3, H7; the outcome column: H12; the header-only file: H13 (d).)
5. **The split.** For every seed and list of ids, the split table has one numeric column
   `row_id` (rule H10: only that column of the file is read; a row is a training row exactly
   when its id is listed, both sets keep the order of the file, and together they are every row
   once; an id listed twice or the id of no row has no effect). Held by link, not by a run
   (decision D9): the ids listed are distinct ids among those given, and their number is seven
   tenths of the number of ids, rounded up. (The real file `inputs/split_ids.csv` is the SAS
   draw for the 150,000 real rows; on a shorter file it does not have that count: H10 gives
   2 and 1 for the first three rows.)
6. **The fit.** For every table: the final effects of the stepwise result are distinct names
   among the 36 candidates, and the result has the shape steps 01 and 04 ask for. The fit is
   taken to return a result (decision D3 and ruling G58, a stated limit: the fit is outside
   both proofs; the claims hold for inputs whose training part has both outcomes, and every
   report says so. On separation the port is being changed to follow SAS, which ends with the
   intercept alone, so a final model with no effect must be within the stage's precondition).
7. **Files exist when written.** Each existence flag is true exactly when the producing step
   returned a result: the feature flags on every table, the medians flag on every training table
   for which the feature-engineering steps return, the coefficients flag on every model, the
   score flags on every table. (Rule H7; H10: feature engineering writes its three files for
   every size of file from one row.)
8. **Read-backs keep the shape.** Each read-back returns a table with the same number of rows in
   the same order, each row with the same column names in the same order; a numeric cell of a
   column listed here stays numeric, and a missing one missing: all 42 feature columns; the
   three medians columns; `row_id`, `default_flag`, `pd_logistic` and `credit_risk_score` of the
   score files. Nothing is asked of the values, nor of the other score columns. (Rules H4, H5,
   H6: the real readers keep this shape and change values to 12 characters; ruling G55 leaves
   the values free. A file with no row is read as text columns, H13 (a): the clause says nothing
   there, since a table with no row has no cell.)
9. **The model file.** The intercept and the (name, coefficient) list predict parses are those
   of the model train returned, in the same order. (Rule H11, experiment E14: bit for bit.)
10. **Counts as text.** For every whole number n, zero or more, `parse_float` of `sas_best n 8`
    is n and the text is not empty; the text of a missing value is empty. This is an
    idealisation, by ruling G56 (decision D4, owner, 2026-11-16), in the style of the hand-off
    links of G55: counts of good and bad applicants are taken as exact on both sides. Rule H14
    (experiment E17) supports it below 10^8; from 10^8 the real function rounds the count, so
    the claims hold for raw files of fewer than 10^8 rows, and every report says so. `InputOK`
    gets no row bound.

**Note on G54 and H9.** H9 finds one shape of 12 characters that the round trip changes: a point
first, then 11 digits, the 11th not 0. The requirements count the 0 before the point
(`CreditRisk.decimal12`, as `decimal32`: "at least one digit is written before the decimal
point"), so such a value needs 13 characters, has no shorter writing, and is not valid input.
Every non-negative `decimal12` value has a writing with a digit first and at most 12 characters,
and H9 reports no change on any such text (integers of every length to 12, every position of the
point, `0.` and up to 10 digits, leading and trailing zeros, values below 1e-5). So G54 as
formalised is enough on the port side, and its boundary is tight: the first shape outside it
does change. Two limits. H9 is a finding on samples of doubles; clause 2 states it for every
such real number, as a link. H9 tested no negative number; clause 2 asks none (incomes are zero
or more, dependents whole numbers).

**Note on D4 and H14 (closed by ruling G56).** The SAS Lean unit `total_good_bad` counts
exactly and puts "fewer than 10^8 rows" in its precondition (SAS rule R19); the port's real
function rounds a count from 10^8 to five significant digits (H14); the SAS program does the
same 8-character round trip. The owner's ruling G56: a stated limit with no formal change.
Counts are taken as exact on both sides (clause 10), no bound is added to the input conditions,
and the claims are reported as holding for raw files of fewer than 10^8 rows.

**Note on an empty validation set (H13; closed by ruling G57).** With at most three training
rows, seven tenths rounded up is every row and the validation set has no row; the port's train
stage raises there (H13 (a)) and the real SAS fails there too
(`migration/legacy-to-port/empty-validation.md`). The owner's ruling G57 (requirements draft 8,
2026-11-16): the training data has at least 4 rows, a formal clause of `TrainOK`. Neither
program changes. Consequence here: on valid input, with the count of clause 5 (seven tenths of n
rounded up, held by link), the validation set has n minus that count rows, which is at least 1
from n = 4 (4 gives 3 and 1). So the validation feature table, the validation score table and
the tables metrics reads from it have at least one row on every valid input. This rests on the
link of clause 5: the lemma "the validation set is not empty" is to be stated once, from
`TrainOK` and clause 5, and used by the coverage contract of the train stage. The training set
is never empty either (at least 3 rows). A test file with no row stays valid (H13 (d): the port
completes).

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
   same table. (An assumption, not a finding: ruling G58. Reports word it as "the equality is
   given the same fitted model"; the real fits agree to the judge's tolerance only.)
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
