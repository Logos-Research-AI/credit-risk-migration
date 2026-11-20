# Texts of `def:pyPipeline`, `def:PyLinks`, `def:Paired` (version 3, 2026-11-17)

## Change note, 2026-11-20, latest (correction C-n; fidelity finding F1)

`PyLinks` clause 10 restated to counts below 10^8 (text and Lean, on `5365851c`), and the matching
hypothesis `hcount` of `lem:metrics_ks_table` bounded by `n ≤ V.length`. No contract gained a
hypothesis. Section **C-n** at the end of the corrections. This entry corrects the note below,
which was written before the restatement.

## Note, 2026-11-20, before C-n (records only; fidelity finding F4)

~~Not a correction: no text or Lean of `pyPipeline`, `PyLinks` or `Paired` changed.~~ *(superseded
2026-11-20 by C-n: the text and Lean of `PyLinks` clause 10 changed the same day; `pyPipeline` and
`Paired` did not.)* C-k recorded
`lem:py_split_ids_rowids` and `lem:py_split_fits` as "stated, not proved" and connected to no
consumer. Both are now `TheoremProved` on `5365851c` (read with `get_items` on 2026-11-20, as are
`lem:py_split_ids_finite` and `lem:fe_run_06_split_reached`, which cites the pipeline's split).
Where C-k says "stated, not proved", this note is in force. C-m is no longer the latest entry of
this file. Also of 2026-11-20: amendment 3 of `informal-spec.md` (B7, the training split as a
shared random draw) leaves `Paired` 2 as it is; the pairing it states holds on the real
150,000-row file and is not claimed elsewhere.

## Change note, 2026-11-19, before the note of 2026-11-20 (correction C-m)

Port-translator's fix of `def:train_run_08_ctable_precond` (accepted rev 00420db1): the null
clauses of train.py :482 and :486 are guarded (:482 by `final.isSome = true`, :486 by
`ctable_made = true`). No text of `pyPipeline`, `PyLinks` or `Paired` changed. The four items the
write cleared were restored unchanged by the prover. Section **C-m** at the end of the corrections.

## Change note, 2026-11-19, before C-m (correction C-l)

Owner's trusted base B4 item 2 (informal-spec amendment 2): made formal with no change. No
precondition of the blueprint asks `solve` or `inv` to return or a matrix to be invertible, and
the Lean routines are total functions of `def:PyParams`, so `PyLinks` needs no clause and no item
was changed. Section **C-l** at the end of the corrections.

## Change note, 2026-11-19, before C-l (correction C-k)

Owner's decisions of 2026-11-19 ("G2 fit": "Add the clause"; "S6 lemmas": "Restate for the
pipeline's split"). `PyLinks` gains clause 14 at the end (the final fit's first name is
`Intercept`, on every argument). New lemmas `lem:py_split_ids_rowids` and `lem:py_split_fits`,
stated, owed in C-j. Everything cleared was restored; four witness proofs got one added case each.
Section **C-k** at the end of the corrections.

## Change note, 2026-11-19, earlier (correction C-j)

Owner's decision of 2026-11-19 on the T0 disproof ("Port split": "Fix the port"). The port's split
now selects exactly (7n+9)/10 distinct ids among the input's (port commit 4a757fb). `PyLinks` 5 is
restated to say so (text, then Lean in place at position 5). `Paired` 2 and `SasLinks` (5) line up
again. Section **C-j** at the end of the corrections.

## Change note, 2026-11-19, later (correction C-i)

Lead's second task of 2026-11-19 (prover), on the review findings against C-h. `PyLinks` 7b gains the
guard of `SasLinks` (8) (both feature flags at F, the fit giving the result with no fit); conjunct
16 (`readScoresTrain`) takes the C-h form with the readability guard and the window of 20 rows;
8b and 8c gain the readability guard; the read-back of the table with no row and the raw test
table with no row are defined by the file they stand for; `ScoreRun` text no longer calls both
disjuncts reached-facts. Section **C-i** at the end of the corrections.

## Change note, 2026-11-19 (correction C-h)

Lead's task of 2026-11-19, with the owner's decisions: `Paired` 5 restates `SasLinks` (8) of the
refreshed profile; `Paired` 1 and `pyPipeline` text only; `PyLinks` head and citations; `PyLinks`
13 `matmul` only for a non-empty b; `PyLinks` 8 `keeps` restated so that it is true of the real
reader on every table; `PyLinks` 5 restated so that it is true of the real split; new
`lem:py_scores_valid_empty`. Section **C-h** at the end of the corrections.

## Change note, 2026-11-18 (correction C-g, version 2; new `def:ScoreRun`)

Entered for the lead as a records task (the lead commits); no blueprint item and no code was
changed with it. Source: `rounds/port-change-spec-2026-11-18.md` sections 3 and 4 (C-g version
2, which supersedes the uncompiled version 1 of `rounds/C-g-draft-2026-11-18.md`), observation
H15 (`rounds/observation-H15-2026-11-18.md`), and the decisions of 2026-11-18 recorded in the
change note of `informal-spec.md` (binding). New section at the end of the corrections:
**C-g**, which changes `PyLinks` 6 (in place), adds 6b, 7b (second case of the training score
flag, in place in clause 7), corrects conjunct 16 of clause 8 (H15), adds 8b and 8c (narrow),
12 (`fsum`) and 13 (`einsum_q`); changes `pyPipeline` (`fit`, `score`, `metrics`); changes
`Paired` 3 (filler form) and records `Paired` 1 unchanged; and gives the text of the new
definition item `def:ScoreRun`. Where C-g and an older text of this file differ, C-g is in force.
The definitions are entered on `5365851c` only after the port's units are updated (C-g, "Order").

---

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
- four read-backs: of the two feature files (one function for both), of the medians file, of the
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
10. **Counts as text.** ~~For every whole number n, zero or more,~~ *(superseded 2026-11-20 by
    C-n: "For every whole number n below 10^8,")* `parse_float` of `sas_best n 8`
    is n and the text is not empty; the text of a missing value is empty. ~~This is an
    idealisation, by ruling G56 (decision D4, owner, 2026-11-16), in the style of the hand-off
    links of G55: counts of good and bad applicants are taken as exact on both sides. Rule H14
    (experiment E17) supports it below 10^8; from 10^8 the real function rounds the count, so
    the claims hold for raw files of fewer than 10^8 rows, and every report says so. `InputOK`
    gets no row bound.~~ *(superseded 2026-11-20 by C-n: the clause is true of the real port
    (rule H14, experiment E17: exact below 10^8; from 10^8 the real function rounds, e.g.
    `sas_best(123456789, 8)` = `1.2346E8`, finding F1). Fewer than 10^8 raw rows is a clause of
    `InputOK` since G56 was made formal (B2, B3), and each proof that uses clause 10 discharges
    the bound from it.)*

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
~~Counts are taken as exact on both sides (clause 10), no bound is added to the input conditions,
and the claims are reported as holding for raw files of fewer than 10^8 rows.~~ *(superseded: G56
was made formal (informal-spec amendment 2, B2, B3), so fewer than 10^8 raw rows is a clause of
`InputOK`; and by C-n, 2026-11-20, clause 10 asks exactness only of counts below 10^8, which every
proof using it discharges from `InputOK`.)*

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

---

## Corrections before stating (2026-11-17)

Found by prover-1 on reading the texts against the present units, before anything was stated;
approved by the lead the same day. The texts above are left as drafted; where a correction
applies, the correction is the text in force. They are assumptions of the claim and are listed
for the owner at the final sign-off.

### C-a. `PyLinks` 5, the count

- **Before**: "the ids listed are distinct ids among those given, and their number is seven
  tenths of the number of ids, rounded up", for every seed and list of ids.
- **After**: for every seed and list of ids, the split table has the one numeric column
  `row_id`, and the ids listed are distinct and among those given. For a list of present,
  pairwise distinct ids, their number is seven tenths of the number of ids, rounded up.
- **Reason**: unsatisfiable as drafted. For the list (1, 1, 1, 1) three distinct ids among those
  given do not exist, so no `py` would meet `PyLinks` and every contract would hold emptily.
- **Conditions**: every clause of `PyLinks` and of `Paired` is covered by a witness: T0 exhibits
  a concrete `py` and `sas` meeting `PyLinks`, `Paired` and `SasLinks` together, and is stated
  and proved before any contract that takes them as hypotheses is proved. The reviewer of the
  definitions tries each clause by hand on a degenerate argument (empty list, repeated ids, one
  row, all missing).

### C-b. `Paired` 2, the tables it is asked of

- **Before**: "For every seed and table of feature-engineering rows, the rows the SAS `split`
  selects are exactly the rows whose `row_id` is in the port's split table for that seed and
  those ids."
- **After**: for every seed and every table whose `row_id` is a present number in every row,
  no two equal: `split seed t` is `t` with `Selected` set to 1 on the rows whose `row_id` is
  listed by the port's split for that seed and the ids of `t`, and 0 on the others. Nothing is
  asked for other tables.
- **Reason**: asked of every table, a table with a repeated `row_id` contradicts the count of
  clause (5) of `SasLinks`, which is asked of every table; T0 would be false.
- **Consequence, accepted**: clause (5) of `SasLinks` is not derived from `PyLinks` and `Paired`
  for every paired `sas`; it holds for the `sas` T0 exhibits, which is what section 6 of the
  specification uses. This replaces, for clause (5), the first half of the reviewer note of
  section 3 above. If a contract later needs clause (5) for every paired `sas`, it goes to the
  lead; it is not added as a hypothesis.
- **Condition**: a lemma that on valid input the table the split receives has `row_id` present
  in every row and pairwise distinct is stated and proved, so that E1 and the contracts after
  it carry no extra hypothesis.

### C-c. `Paired` 7, the date

- **Before**: "The same `today`."
- **After**: the SAS side of `Paired` is the 17 parameters of `sasPipeline` together with
  `today`, a SAS number (`def:SasParams`); clause 7 says the port's `today` cell is the numeric
  cell holding that number.
- **Reason**: `sasPipeline` has no date among its 17 parameters; the date belongs to SAS units
  outside it (`model_performance_metrics`; contracts F4, F6).
- **Condition**: F4 and F6 quantify `today` once, shared through `Paired`.

### C-d. The existence flags: `Paired` 5, `PyLinks` 7, `pyPipeline.fit`

Found by prover-1 while stating (the doubt on T0), checked by the coordinator on the Lean of
`def:SasLinks`, `def:sasPipeline`, `def:PyLinks`, `def:Paired`, `def:pyPipeline`; approved by
the lead 2026-11-17.

- **Before.** `Paired` 5: "Existence flags are shared. `featTrainExists`, `featValidExists`,
  `mediansExist`, `coefExists` and the two score-file flags of the SAS side are the port's."
  `PyLinks` 7: "Each existence flag is true exactly when the producing step returned a result:
  the feature flags on every table, the medians flag on every training table for which the
  feature-engineering steps return, the coefficients flag on every model, the score flags on
  every table." `pyPipeline.fit`: "nothing when the flag says the training feature file is
  absent for `F`".
- **After.**
  - `Paired` 5: the SAS existence flags meet clause (8) of `SasLinks`, restated word for word,
    with P the SAS pipeline at `sas`: for every table F, `featTrainExists F` is true exactly
    when F is one of the two feature tables of a result of the features step of P (for some raw
    training table and seed), and the same for `featValidExists`; for every table S,
    `scoresTrainExists S` is true exactly when the score step of P returned S for some model
    and feature table, and the same for `scoresValidExists`; for every raw training table,
    `mediansExist` of it is true exactly when the features step of P returned a result on it
    for some seed; for every model m, `coefExists m` is true exactly when the fit step of P
    returned m for some feature table. No clause relates the SAS flags to the port's.
  - `PyLinks` 7 (Lean as stated; text made unambiguous): the same six statements for the
    port's flags, with P the pipeline `pyPipeline py`: each flag is true of a value exactly
    when the producing step of P returned that value for some argument.
  - `pyPipeline.fit`: nothing when the flags say either feature file is absent for `F` (the
    conjunction of `featTrainExists F` and `featValidExists F`), as `sasPipeline` and the real
    train stage do (the reviewer confirms against `run_py_py_py` that the real stage stops when
    either file is absent). This reverses the addition below about `fit`.
- **Reason.** One function cannot be "returned by the SAS pipeline for some argument" and
  "returned by the port pipeline for some argument" for every value, unless the two pipelines
  return the same values over all inputs, invalid ones included, which nobody claims (G53). No
  `py` and `sas` could meet `PyLinks`, `Paired` and `SasLinks` together; T0 had no witness.
- **What each contract family uses of the flags** (from the two pipeline definitions):

  | Family | SAS side reads | Port side reads | Applied to | Port flag true by |
  |---|---|---|---|---|
  | features (E1, E2) | none | none | | |
  | fit (E3) | both feature flags of the one table | both feature flags (after C-d) | F1 returned by `S.features` on the valid run | E1 (F1 is a port feature table) |
  | score (E4, E5) | none | none | (so E4's free table of feature shape is untouched) | |
  | scoreTest (E6) | medians, coefficients | medians, coefficients | `train`; m returned by `S.fit F1` | E1, E3 |
  | metrics (E8 to E11) | the two score flags | the two score flags | S1, S2 returned by `S.score` | E4 and the feature-shape lemma |
  | F1 to F6, E7 | as the stage | as the stage | the same reached values | as above |
  | port coverage G1 to G4 | | the port's | reached values | `PyLinks` 7 |

  The SAS side always reads its flags on values its own pipeline returned, which clause (8)
  makes true at once.
- **Rejected forms.** (i) Shared flags (the draft): unsatisfiable with the two reachability
  clauses, as above. (ii) No clause at all on the SAS flags (the coordinator's first proposal):
  the contracts assume `PyLinks` and `Paired` only, so a `sas` whose flags are false everywhere
  would be paired with any `py`; `S.fit F1` is nothing while `P.fit F1` returns, and E3 is
  false. Also considered and withdrawn by prover-1: flags agreeing only on values a valid run
  reaches (T0 would need the equality), and a "valid runs only" reading of `PyLinks` 7 (the
  same).
- **Conditions and consequences.**
  1. Binding on every contract of phase 3: a flag appears only applied to a value named by a
     reached-equation on the valid input in question. A contract needing a flag on a free value
     goes to the lead; no hypothesis is added.
  2. Order of proof: E1 and E2, then E3, then E6; E4 before E8 to E11.
  3. `Paired` 5 and `SasLinks` (8) must be literally the same clause (a shared definition, or
     compared character against character by the reviewer), so that section 6 of the
     specification does not carry two versions.
  4. In the review of the fit contract it is shown that on a valid run every flag either side
     reads is true, each by its own clause; a valid input on which the two stops differ would
     be a finding.
  5. T0's witness: each side's flags are its own reachability, built stage by stage (features
     and score read no flag; fit reads the feature flags; scoreTest and metrics read flags of
     earlier stages only). prover-3's paper witness covers all clauses after C-a to C-d and is
     the plan of T0; T0 is stated and proved first in phase 3.
- **For the owner.** C-a to C-d change assumptions of the claim and are listed together in the
  final report under "definitions corrected before stating"; two of them (C-a, C-d) removed
  assumptions that could not be met.

### C-e. `PyLinks` 11, the date

Found by prover-3 while writing the witness of T0 on paper; approved by the lead 2026-11-17.

- **Before**: `PyLinks` asked nothing of `today` ("Nothing is asked of the formatters, the
  numpy routines, `fsum`, `today` or `full`").
- **After**: `PyLinks` gains a clause 11: the `today` cell is a numeric cell (there is a SAS
  number d, possibly the missing one, with `py.today` the numeric cell holding d). The sentence
  above no longer names `today`.
- **Reason**: `Paired` 7 says `py.today` is the numeric cell holding `sas.today`, so a `py`
  whose `today` is a text cell has no paired `sas`, while `PyLinks` admitted it. T0 in the form
  section 6 of the specification needs ("for every `py` with `PyLinks py` there is `sas` with
  `Paired py sas`") was false. The contracts were not affected (each has the fact through
  `Paired` 7).
- **Why it is an assumption of the right kind**: it says what the port's out-of-scope code hands
  the stages: the run date as a SAS date number. The reviewer points to the line of the port
  where `today` is computed.
- **Checked on the same occasion** (prover-3, clause by clause): no other parameter of `py` is
  constrained by `Paired` while free in `PyLinks`: clauses 1 and 6 speak of `sas` only; 2, 3, 4
  define `sas.split`, `sas.fit` and the SAS read-backs from the port's, for any port value; 5
  speaks of the SAS flags only.

### C-f. `PyLinks` 8, one kind of cell per column

Found in the review of G4 (`thm:G4_metrics_coverage`, "PyLinks 8 too loose"); form chosen and
approved by the lead 2026-11-17. Entered on `5365851c` the same day.

- **Before**: "Each read-back returns a table with the same number of rows in the same order, each row
  with the same column names in the same order; a numeric cell of a column listed here stays
  numeric, and a missing one missing: all 42 feature columns; the three medians columns;
  `row_id`, `default_flag`, `pd_logistic` and `credit_risk_score` of the score files. Nothing is
  asked of the values, nor of the other score columns." (Lean: `keeps R cols` is the row-by-row
  shape clause only.)
- **After**: the same, and each read-back also keeps one kind of cell per column, for every
  column, the other score columns included: for every table t in which each column holds one
  kind of cell in every row (for each column name, the cells under that name are numeric in
  every row that has it, or text in every row that has it), each column of the read-back of t
  does too. In the Lean, `keeps R cols` is the shape clause for every t, conjoined with
  `oneKind t -> oneKind (R t)`, where `oneKind t` says: for every name c, every cell `r.get c`
  of a row of t is numeric, or every one is text. It applies to all four read-backs.
- **Reason**: the clause constrained the kind of cell only for four columns of the score files,
  while the real reader (`proc_import_csv` in `port/credit_risk/sas_compat.py`) gives every
  column a single kind across all rows. A read-back that turns one cell of another score column
  into text while its neighbours stay numeric met `PyLinks` 8 but is no reader the port has, and
  G4 was false through this looseness alone. The lead's form keeps the identity read-back, which
  T1 and the carried requirements need: both the real reader and the identity meet it.
- **Consequence**: G4 then needs, as a fact proved about the port's score output and not
  assumed, that the score tables of a valid run have one kind of cell per column. This is noted
  in the item text. No hypothesis is added to G4.
- **Cleared by the edit** (`edit_text` on `def:PyLinks`; statements only, none of them had a
  proof): `thm:G1_run_coverage`, `thm:G3_predict_coverage`, `thm:G4_metrics_coverage`,
  `thm:E1_features_train`, `thm:E2_features_valid`, `thm:E6_score_test`,
  `thm:E7_predict_column_names`, `thm:E8_validation_summary`, `thm:E9_ks`, `thm:E10_decile`,
  `thm:E11_threshold`, `thm:F1_income_medians`, `thm:F2_kaggle_submission`,
  `thm:F5_calibration_plot`, `thm:F6_model_performance_metrics`, `lem:py_split_input_ids`,
  `lem:ex_reached_features_predict`, `lem:ex_metrics_run`, `lem:ex_G4_run` (19). Their statement
  drafts remain on the server (`read_scratch`) and are to be resubmitted and reviewed again.
  `def:PyLinks` itself was restated and accepted.
- **Note for the reviewer**: on the first submission the judge rejected the Lean over clause 4
  (unchanged since its acceptance): the Lean says the outcome column is text *only when* the
  table has no row or some cell is missing, not the converse the text might be read to say. The
  Lean of clause 4 was not changed; one comment line saying so was added above it, and the
  second submission was accepted. Whether the text of clause 4 overstates (a missing cell
  written empty leaves the column numeric in `proc_import_csv`) is left to the lead.

### C-g. The fit, the flags, the read-backs, the sum, one numpy routine; `pyPipeline`; `Paired` 1 and 3 (version 2, 2026-11-18)

Specified in `rounds/port-change-spec-2026-11-18.md` (sections 3, 4) after the owner's decisions
of 2026-11-18 (no contract keeps a hypothesis of its own; the port follows SAS on a training part
with one outcome, on three levels; G2 covers train steps 03 and 05 to 08; leverage near 1 and
variance 0 fixed in the port, not assumed; the stated base (a) to (d) of `informal-spec.md`
section 9) and the lead's (7b; `def:ScoreRun`; helper units; 8b, 8c narrow; conjunct 16 per
H15; `Paired` 3 filler; `Paired` 1 unchanged). Version 1 (`rounds/C-g-draft-2026-11-18.md`) is
superseded where they differ: its 6b (3) "a positive variance for every final parameter" and
6b (4) "no leverage equal to 1" are dropped, and its clause 6 gains the covariance shape. Like
C-a to C-f, these are assumptions of the claim, listed for the owner at the final sign-off.

**Vocabulary.** For a table T, *the outcomes of T* are the `default_flag` values of its complete
cases, as step 01 of train computes them (the rows where the 36 candidates and `default_flag`
are all present). T is *a training frame* when, as a frame, its column names are distinct, its
columns have one length, and the 36 candidates and `default_flag` are numeric columns (the
three table conditions of `train_run_01_fit_frame_precond`). T *has both outcomes* when every
outcome is 0 or 1 and both occur; T *has one outcome* when no two outcomes differ (this includes
no outcome at all).

**Shape.** New parts are appended after position 20 of the conjunction; `keeps` is not touched;
clauses 6, 7 (the training score flag, 7b) and conjunct 16 are changed in place. Positions after
the edit: 1 to 5; 6 (the fit, changed); 7 to 10; 11 (`scoresTrainExists`, changed: 7b); 12; 13
to 15; 16 (`readScoresTrain`, changed); 17 to 20; then 21 (clause 12, `fsum`), 22 to 24 (8b), 25
(8c), 26 (6b), 27 (clause 13, `einsum_q`); then 28 and 29 (clause 13, `matmul` and
`matvec`; owner, 2026-11-18). Every position and argument list is read again from the accepted
units before the Lean is entered.

**Head of `PyLinks`.** The sentence "Nothing is asked of the formatters, the numpy routines,
`fsum`, `today` or `full`" (as amended by C-e) becomes: "Nothing is asked of the formatters or
`full`; of `fsum` only clause 12; of the numpy routines only clause 13."

#### `PyLinks` 6, the fit (in place)

- **Before**: "For every table: the final effects of the stepwise result are distinct names
  among the 36 candidates, and the result has the shape steps 01 and 04 ask for. The fit is
  taken to return a result (decision D3 and ruling G58, ...)."
- **After**: For every table: the final effects are distinct names among the 36 candidates
  (unchanged). For every training frame:
  - with both outcomes, the stepwise result has a final fit and an intercept-only fit; the
    coefficient array of the final fit is one-dimensional with one entry per name of the fit
    and at least one entry; and its covariance is two-dimensional and square with one row per
    name;
  - with one outcome, the stepwise result is the result with no fit: no step, no final fit, no
    intercept-only fit.
  Nothing is asked of any other table. On a training frame with both outcomes the fit is taken
  to return a result (ruling G58, narrowed by the decision of 2026-11-18: base (a)).
- **Reason**: the port's fit returns `StepwiseResult()` when the rows used hold fewer than two
  response values, and train goes on without a model (commit 65430e4; SAS: x27, R46). The
  covariance shape is new because step 04 now reads `cov[i, i]` for every name of the final fit
  (`train.py:297`).
- **True of the port by**: `sas_compat.py:1067-1070` (no fit), `:1118`, `:1206` (the final fit),
  `:750`, `:950`, `:962` (coefficients; `_inv_sas(info)`, square, of the size of the design).
- **Lean, in words**: the final fit is read from the stepwise result (`(py.fit T).final`), no
  longer from an empty-fit default of step 01; the covariance conjunct (a list of rows c with
  `final.cov` the 2-D array c, as many rows as `final.names` has names, every row of that length)
  is added after the coefficient conjunct inside the both-outcomes branch.

#### `PyLinks` 6b, the fitted result on a training frame with both outcomes (appended, position 26)

For every training frame with both outcomes, with the values of steps 01 and 04 as
`run_py_py_py` computes them:

1. (step 03) For every step of the stepwise result whose fit has a variable: the names of the
   fit after the first are among the 36 candidates; its coefficient array is one-dimensional
   and its covariance two-dimensional and square with as many rows as there are coefficients;
   the fit has at most that many names.
2. (step 03) -2 Log L of the intercept-only fit is not 0.
3. (steps 03 and 08) The names of the final fit after the first are among the 36 candidates.
4. (step 06) For the intercept and for every final effect, the diagonal entry of the covariance
   is not negative.

Nothing more is asked. Parts 1 and 3 and the covariance shape of clause 6 are shape and naming
facts of the `LogisticFit` the port builds; parts 2 and 4 are facts about values of the fit,
true of it in exact arithmetic and not guaranteed by the code after it. Together they are base
(b) of `informal-spec.md` section 9. Dropped against version 1: a positive variance (the port
handles an entry exactly 0 since commit a9b1f41, `train.py:388-396`, X22) and all of the
leverage part (commit 88df42d, X21; "one leverage per complete case" is clause 13). What steps
05 and 07 ask is proved, not assumed: with the two sum bounds dropped from the preconditions
(lead, 2026-11-18) the group sums being whole numbers follows from outcomes 0 or 1.

#### `PyLinks` 7, the training score flag: a second case (7b, in place)

- **Before**: `scoresTrainExists S` is true exactly when the score step of P (`pyPipeline py`)
  returned S for some model and table.
- **After**: `scoresTrainExists S` is true exactly when the score step of P returned S for some
  model and table, **or** S is the training score table the train stage writes on some table
  with the result with no fit: the table of E5's chain (steps 01, 04, 09, 12, 14,
  `risk_scores_train.csv`) on the read-back of some F, at the stepwise result with no fit.
  `scoresValidExists` is unchanged: the validation score table of a run without a model is the
  table with no row, which the score step returns on the table with no row (to be proved once,
  for P and for S).
- **Reason**: on a run without a model the training score table is written by the train stage
  and is not a value of `P.score` for any model: `P.score` gives a present probability on every
  feature row. Without 7b the port's metrics step would stop (flag false) where the real stage
  does not, and E8 to E11, F5, F6, G4 would fail on that run. 7b keeps the clause true of the
  port ("a file exists when written"); it adds no hypothesis to a contract. The other choice (a
  model with a term naming no column) was not taken: on the port it rests on what step 10 does
  outside its precondition. `Paired` 5 is not touched (it restates `SasLinks` (8)).

#### `PyLinks` 8, conjunct 16, `readScoresTrain` (in place; observation H15)

- **Before**: `keeps py.readScoresTrain` on `row_id`, `default_flag`, `pd_logistic`,
  `credit_risk_score`: in each of the four columns a numeric cell stays numeric, a missing one
  missing.
- **After**: the same for `row_id` and `default_flag`. For `pd_logistic` and
  `credit_risk_score`: a numeric cell is read back as a numeric cell, a missing one missing;
  **or**, when the column holds the missing number in every row of the table, as the text cell
  with the missing text. The rows, the names, and "one kind of cell per column" (C-f) are asked
  as before.
- **Reason**: H15. On `risk_scores_train.csv` of a one-outcome run the two columns are empty in
  every row, and the real reader (`guessingrows=20`) returns them as text columns of nulls. The
  conjunct as it stood was false of the real reader on a file a valid run reaches.
- **True of the port by**: `proc_import_csv` (`sas_compat.py:578-587`), H15. The identity meets
  it (first branch).
- **Lean, in words**: `keeps` is not edited (the other three read-backs use it). Conjunct 16 is
  written out at its position: the `Forall₂` of rows with equal names; for the first two columns
  the cell clause of `keeps`; for the other two the cell clause with the second disjunct "every
  row of t has `Cell.num none` under c, and the read-back cell is `Cell.str none`"; then
  `oneKind t → oneKind (R t)`. A proof that uses it for `pd_logistic` or `credit_risk_score`
  first shows the column is not missing in every row.
- **Limit**: true of the reader on the files a valid run reaches, not on every table (the reader
  decides on the first 20 rows). The SAS side's clause (3) is weakened the same way (form W).

#### `PyLinks` 8b and 8c, read-backs keep present numbers (appended, positions 22 to 25; narrow forms)

- **8b.** For the feature read-back and each of the 42 feature columns, and for each score
  read-back and each of `row_id`, `default_flag`, `pd_logistic`, `credit_risk_score`: for every
  table in which every row holds a present number in that column, every row of the read-back
  holds a present number in that column. True of `proc_import_csv` (`sas_compat.py:557-592`;
  H4, H5 (a), (d)); the identity meets it.
- **8c.** For every table in which every row holds a present number under `default_flag`: row
  against row at the same index, a `default_flag` cell holding 0 or 1 is read back as the same
  number. True of the same reader ("0" and "1" are read 0.0 and 1.0; H4); the identity meets it.
- **Why narrow**: the wide forms ("for every table, a present number stays present"; "every
  `default_flag` value is kept") are false of the real reader (a column with a text cell, or a
  score column whose first 20 rows are empty, is read as text; 1/3 is changed by 12 characters).

#### `PyLinks` 12, the sum (appended, position 21)

For every list of real numbers all at least 0, `fsum` of the list is at least 0. True of
`math.fsum` (`sas_compat.py:1317-1318`): correctly rounded, rounding is monotone.

#### `PyLinks` 13, one value per row (appended, position 27; new)

For every matrix x and every matrix v, `einsum_q x v` has as many entries as x has rows.
For every matrix a and every matrix b, `matmul a b` has as many rows as a has rows, each with as
many entries as the first row of b has (so the product X'X of a matrix X, formed as the units
form it, is square of the column count of X). For every matrix a and every vector v, `matvec a v`
has as many entries as a has rows. (`np.matmul`, `@`: the shape of the product, whenever it
returns.)

- **Shapes of `matmul` and `matvec`** (owner, 2026-11-18): the last two sentences above, as facts
  about numpy. They are what the accepted preconditions ask of the two routines: step 03
  (`train_run_03_fit_global_rsquare_precond`: `_kept_precond` of X'X, a square 2-D array;
  `_solve_sas_precond` of i0, the scaled X'X, and u0 = `matvec` of X' on the centred outcomes, a
  vector of i0's size) and `classification_table_precond` ((4') `_inv_sas_precond` of
  X'(x w), a square 2-D array; (5) p, `_expit` of `matvec x beta`, of the length of y). The
  accepted preconditions of `_kept`, `_inv_sas` and `_solve_sas` ask nothing of `inv` and
  `solve` ("the library routines play no part"), so clause 13 has no line for them.
- **Reason**: `classification_table_precond` (5) asks that the leverages have the length of y.
  Stated of the routine: true of `np.einsum("ij,jk,ik->i", x, v, x)` whenever it returns, met by
  T1's witness ("0 for each row").
- **Helper units** (lead, 2026-11-18): `_kept`, `_inv_sas`, `_left_out` and
  `classification_is_made` are new units of the port, with `inv`, `solve`, `matmul` as their
  parameters; `def:PyParams` gains no parameter for them. If the preconditions of `_kept` and
  `_inv_sas` ask the like of `inv` and `solve` (an n by n matrix in, an n by n matrix out; a
  vector of length n), each such condition is one more line of clause 13, fixed when the units
  are accepted.

#### Text only

Clause 11 cites `train.py:771` for the date; at HEAD (a9b1f41) the line is `train.py:883`
(`dt.date.today()`).

#### `def:pyPipeline` (from section 4.1 of the change specification)

Needed by E3 (level 1) and, for `metrics`, by base (c) of `informal-spec.md` section 9.

- **`fit`**: nothing when the flags say either feature file is absent, or when the fit returned
  no model (a training part of one outcome: step 04 extracts no intercept; the stage then writes
  no `model.json`); otherwise the model of step 04's intercept and coefficients, as before.
- **`score`**: the same wiring on the units as changed: step 10 with the intercept of m as a
  present value, step 12, step 14 with the fillers and `false` for both ROC flags.
  `lem:py_score_fillers_idle` is proved again on the new step 14.
- **`metrics`**: when `run_py` returns files, the KS and decile tables are the tables of their
  files, **or the table with no row when the file is not written**; the summary and threshold
  files are always written and are looked up as before. A file the stage does not write is given
  as the table with no row, as the SAS units give a table that was not created (RULEBOOK of
  `legacy-to-lean`, R39, R46). This is the first default written into `pyPipeline`: the
  sentence of section 1 "It contains no arithmetic, comparison or default of its own" gains
  "except this one".

#### `def:Paired` 3, the fit (filler form)

- **Before**: for every table T, `sas.fit T` is the model whose intercept and (name,
  coefficient) list, in order, are those step 04 of train extracts from the port's fit on T.
- **After**: for every table T, `sas.fit T` is the model step 04 extracts from the port's fit on
  T; and where step 04 extracts none, the model with intercept 0 and no term.
- **Reason**: step 04's intercept is optional after the update. The filler is never read by the
  SAS pipeline (its `fit` field returns nothing there, by `logistic_no_fit`); it keeps
  `lem:sas_fit_term_names` true for every table and the clause one equality at the same
  position. With a left-out parameter step 04 gives coefficient 0 for it (a9b1f41), which is what
  X22 shows of PROC LOGISTIC's parameter table.

#### `def:Paired` 1, and the rest of `Paired`

- Clause 1: unchanged in letters. After the profile refresh `SasLinks` (1), (2) carry one more
  conjunct each in `deliveredCell` (padded text); `Paired` 1 keeps its old local definition, and
  T0 gets the helper "the tightened delivery implies the old one".
- Clauses 2, 4, 5, 6, 7: unchanged in letters. Clause 5 changes in value through
  `sasPipelineOf` (the `fit` field of the SAS pipeline).
- The closing note of section 3 ("`Paired` deliberately does not include clause (3) of
  `SasLinks`") stands; clause (3) is now weakened for the training score file (form W), and the
  identity read-backs still meet it.
- `def:SasParams`, `def:SasLinksOf`, `def:sasPipelineOf`: Lean unchanged, resubmitted against the
  refreshed profile.

#### `def:ScoreRun` (new definition item; lead, 2026-11-18)

**Text.** `ScoreRun` says that two tables S1, S2 are the score tables of a run, fitted or
without a model, on the feature tables F1, F2 of that run. One definition, used on either side:
it takes the pipeline Q (the SAS pipeline `sasPipelineOf sas`, or the port's `pyPipeline py`)
and that side's training score table without a model, as a function of the feature table. It
holds when:

- **fitted**: there is a model m with `Q.fit F1` returning m, `Q.score m F1` returning S1 and
  `Q.score m F2` returning S2; or
- **without a model**: `Q.fit F1` returns nothing, S1 is the side's training score table without
  a model on F1, and S2 is the table with no row.

The training score table without a model is, on the SAS side, `logit_scored_train_output_nofit`
of `sas.readFeatures F1`, then `logit_scored_train`, `risk_scores_train`,
`risk_scores_train_clean`; on the port side, the table of E5's chain (steps 01, 04, 09, 12, 14,
`risk_scores_train.csv`) on `py.readFeatures F1` at the stepwise result with no fit. On the SAS
side the table with no row is what `logit_scored_valid_temp_nofit`, `logit_scored_valid`,
`risk_scores_validation`, `risk_scores_validation_clean` give. Both disjuncts are reached-facts,
so a contract that takes `ScoreRun` as its run hypothesis adds no hypothesis (`informal-spec.md`
sections 1 and 2a). Users: E8 to E11, F5, F6 (SAS side); A4, G4 and the port half of the examples
(port side). The stater fixes the exact signature; the reviewer checks it against this text and
against the two chains it names.

#### Order (from section 7 of the change specification)

The SAS clearing signed off and the port's profile refreshed; the port's units updated
(section 2 of the change specification, with the four helper units) and evaluated on the staged
data; then `def:pyPipeline`, `def:PyLinks`, `def:Paired`, `def:ScoreRun` in dependency order,
each reviewed by a prover who did not write it, clause against the port both ways, with the
degenerate arguments of C-a (empty table, one row, every outcome equal, no complete case); then
T1, T0, and the contracts.

#### Cleared by C-g

The 47 statement consumers of `def:PyLinks` and the 5 more of `def:Paired` (52; table in section
6.1 of the change specification): 23 restated (13 contracts, 9 examples,
`lem:sas_reached_scores_read_shape`), 29 resubmitted with the same statement. The update of the
units clears about 21 more (section 6.3 there); the profile refresh reaches 24 more (6.4).
Fetch `statement_lean` and `proof_lean` of all of them before clearing, and count the items
(322 by `get_status` on 2026-11-18).

### C-h, 2026-11-19

Lead's task of 2026-11-19 (prover), with the owner's decisions of 2026-11-18 and 2026-11-19. The
lead lifted the rule "change no existing item" for `def:Paired`, `def:PyLinks`, `def:pyPipeline`,
`def:ScoreRun` for this task only (`def:ScoreRun` was not changed). Order: this section, then the
text of each item, then its Lean. Where C-h and an older text of this file differ, C-h is in force.
The owner's rule of 2026-11-18 stands: no contract gets a hypothesis of its own; a narrowing is
the owner's, reported and never taken.

#### `Paired` 1, text only

Clause 1 keeps the delivery of `SasLinks` (1), (2), (2b) as it was before the tightening of C-g
(its own local `deliveredRow`, `textColumn`, `deliveredCell`, `deliveredTable`; Lean unchanged).
The refreshed `SasLinks` adds to `deliveredCell` one conjunct in each text branch (the delivered
text has no surrounding blanks: `Sas.trimBlanks` leaves it as it is). The tightened delivery
implies the old one (one conjunct more), a helper of T0, so every `sas` meeting the refreshed
`SasLinks` meets clause 1.

#### `Paired` 5, `SasLinks` (8) word for word (Lean changed in place)

- **Before**: the six SAS flags with one case each; the training score flag "true of S exactly
  when `score` returns S for some model and table".
- **After**: as the refreshed profile has it. The training score flag is true of S exactly when
  `score` of `sasPipelineOf sas` returns S for some model and table, **or** there is a table F with
  `train_inputs_stop (sas.featTrainExists F) (sas.featValidExists F) = false`,
  `logistic_no_fit (sas.readFeatures F) = true` and S =
  `risk_scores_train_clean (risk_scores_train (logit_scored_train
  (logit_scored_train_output_nofit (sas.readFeatures F))))` (the training score table written
  without a model). The other five flags as before. Same position, same order of the six as in
  `SasLinks` (8): feature train, feature validation, training score, validation score, medians,
  coefficients.
- **Reason**: C-d condition 3 (`Paired` 5 and `SasLinks` (8) literally the same clause). The
  profile refresh after the SAS clearing gave `SasLinks` (8) the second case; `Paired` 5 still had
  the old one, so a `sas` meeting `Paired` did not meet `SasLinks` (8) on a run without a model.

#### `pyPipeline`, text only

"five read-backs" becomes "four read-backs" (the record has four: `readFeatures` for both feature
files, `readMedians`, `readScoresValid`, `readScoresTrain`). Lean unchanged, resubmitted.

#### `PyLinks` head, text

"Nothing is asked of `full`, `chi2`, or of the formatters `fmt_wd`, `fmt_oddsr`, `sas_d8`,
`sas_d12_3`, `sas_pvalue`. Of the formatter `sas_best12` only clause 2, of the formatter `sas_best`
and of `parse_float` only clause 10, of `input_best32` only clauses 1 and 2, of `today` only clause
11, of `fsum` only clause 12, of the numpy routines only clause 13 (`einsum_q`, `matmul`,
`matvec`; nothing of `inv`, `solve`, `dot`, `log1p`, `pow2`)."

#### `PyLinks`, line citations (text; checked against `port/` at HEAD 3272e9d)

- Clause 6: `sas_compat.py` 1069-1072 (the result with no fit: `np.unique(y).size < 2`,
  `return StepwiseResult(), ""`), 1120, 1208 (the final fit), 952, 964 (`LogisticFit(..., b,
  _inv_sas(info), ...)`: coefficients and covariance).
- Clause 11: `metrics_calculation.py` 545 and `train.py` 888 (`dt.date.today()`), `sas_compat.py`
  275 (`today_date9`).
- Clause 12: `sas_compat.py` 1319-1320 (`math.fsum`).

#### `PyLinks` 13, `matmul` (owner, 2026-11-19; Lean changed in place, position 28)

- **Before**: for every a and b, `matmul a b` has as many rows as a, each as long as the first row
  of b.
- **After**: the same for every a and every b that is not the empty list. `matvec` unchanged.
- **Reason**: numpy gives a k by k matrix for X'X when X has no row (`a` = X' has k empty rows,
  `b` = X = []); as lists, the first row of [] has length 0, so the line was false there. Lists
  cannot say the column count of a matrix with no row.

#### `PyLinks` 8, `keeps` for `readFeatures`, `readMedians`, `readScoresValid` (owner, 2026-11-19; Lean changed in place, positions 13 to 15)

The read-back of a table t is what `proc_import_csv` (`sas_compat.py` 557-592) returns, as a table,
on the file `write_sas_csv` (`sas_compat.py` 597-657, with `_render_column`) writes from the frame of t
(`Pl.ofTable t`: the names and kinds of the first row). Guessing window: every row for the two
feature files (`train.py` 46-51, `guessingrows=None`); the first 20 rows for the medians file
(`predict.py` 211, the default) and the validation score file (`metrics_calculation.py` 107).
Formats of the writer: none for the feature files; `best32.` on `median_income` and
`overall_median_income` (`feature_engineering.py` 365-369); `percent8.2` on `interest_rate` of the
score files (`train.py` 846-853).

- **Before**: for every table t, the rows and names kept, a numeric cell of a listed column read
  back numeric (a missing one missing), and one kind per column kept (C-f).
- **After**: a table t is *readable*, for the list of formatted columns of its file, when
  1. every row has the column names of the first row, in the same order;
  2. those names are distinct, each of 1 to 32 characters, none contains a double quote, and the
     first does not begin with the byte-order mark U+FEFF;
  3. when t has a row, its first row has a column;
  4. each column holds one kind of cell in every row (C-f, `oneKind`);
  5. when t has a row, each formatted column is a numeric cell of the first row.

  On every readable table the read-back returns a table with the same number of rows in the same
  order, each row with the same column names in the same order, and one kind of cell per column;
  and in each listed column (all 42 feature columns; the three medians columns; `row_id`,
  `default_flag`, `pd_logistic`, `credit_risk_score` of the validation score file) a numeric cell
  is read back as a numeric cell, a missing one missing, **or**, when every row of the guessing
  window holds the missing number in that column, as a text cell. Nothing is asked of other tables
  or of the values.
- **True of the code** (probes of 2026-11-19 on the port at HEAD, polars 2.1.0, write then read):
  on a readable table the writer does not raise and the reader keeps every row and every name; a
  numeric column is written as number texts (`sas_best12`, `best32.`) and empty fields, so it is
  read as numbers when some cell of the window is present, and as text of width 1 when none is
  (H15; for the medians and validation score files a later present cell is then cut to its first
  character: `[None]*20 + [123.25]` reads `'1'` in row 21); a single-column file of empty fields
  keeps its rows; `Pl.toTable` gives every column one kind.
- **What the code does on other tables** (why each condition is there): a name of more than 32
  characters is cut (two names equal after the cut: `ValueError`); an empty name becomes `VARn`; a
  name with a double quote is read with the quote doubled (`a"b` reads `a""b`); a leading U+FEFF
  is dropped; a frame with no column gives an empty file (`NoDataError`); a row whose names differ
  from the first row's is written under the first row's names; a cell of another kind than its
  column's first cell is written empty; the writer raises on a formatted column that is absent or
  text. The numeric window case is no longer outside the clause: it is its second disjunct.
- **The table with no row**: readable (every condition holds of it), so the read-back of [] is []:
  the real file of a table with no row is the header of the script's frame, which the reader
  returns with no row (H13 (a), H15).
- **Unchanged by C-h**: conjunct 16 (`readScoresTrain`, H15) and its recorded limit (true on the
  files a valid run reaches, not on every table); 8b and 8c. The owner's task named the three
  read-backs only. 8b, 8c and conjunct 16 are not true of the real reader on every table either
  (a name with a double quote, rows with other names, a column of two kinds): reported, not
  changed.
- **Lean, in words**: a local `readable fmt t` (the five conditions; 4 is `oneKind t`); `keeps R win
  fmt cols` is: for every readable t, the `Forall₂` of rows (equal names; for c listed, from a
  numeric cell v, either a numeric cell w with v none implying w none, or every row of `win t`
  holds `Cell.num none` under c and the read-back cell is a text cell), and `oneKind (R t)`. Window
  `fun t => t` for the features, `List.take 20` for the medians and validation score files.

#### `PyLinks` 5, the split (owner, 2026-11-19; Lean changed in place, position 5)

- **Before** (C-a): the split table has the one numeric column `row_id`; the ids listed are
  distinct and among those given; for present, pairwise distinct ids, their number is
  (7n + 9) / 10.
- **The code** (`feature_engineering.py` 343-350): `pl.read_csv(split_ids, columns=["row_id"],
  infer_schema=False)` of a fixed file (`inputs/split_ids.csv`, SAS's draw on the 150,000 real
  rows), then `input_best32`: a Float64 column, a cell missing where the text is blank or not a
  number. The file depends on neither the seed nor the ids of the input. Its ids may repeat, be
  missing, or not be among the ids given. Then (`def:fe_run_06_split`): a feature row is a
  training row exactly when its `row_id` equals, by value, a present id of the table; a row whose
  `row_id` is present and not listed is a validation row; a row with a missing `row_id` is in
  neither set; a repeated id, an id of no row and a missing id have no effect; both sets keep the
  order of the rows. The number of training rows is the number of rows whose id is listed:
  anything from 0 to every row. The code guarantees no count, no distinctness and no membership.
- **After**: for every seed and list of ids, the split table is a table with the one numeric
  column `row_id`, one row per entry, each cell a number or missing. Nothing more.
- **SAS side, through the profile**: `SasLinks` (5) asks, for every seed and table, that every row
  gets `Selected` 0 or 1 and that the number selected is (7n + 9) / 10 (PROC SURVEYSELECT
  `samprate=0.7 seed=42 outall`, `feature_engineering.sas` 323-335). `Paired` 2 (C-b) defines
  the SAS split from the port's table and asks no count, so it is unchanged and still satisfiable.
  **The pair no longer matches in the count**: a paired `sas` meets `SasLinks` (5) on a table t
  exactly when the port's table lists exactly (7n + 9) / 10 of the ids of t, which no clause now
  gives (C-b had already accepted that (5) is not derived for every paired `sas`; it was still
  derivable on the ids of a valid run, and is no longer). For the real file it holds on the
  150,000 real rows, and not in general.
- **Reason**: the old clause was false of the real code (the file is fixed; on any input other
  than the real data its ids need not be among those given, and the count fails).

#### `lem:py_scores_valid_empty` (new item, stated, not proved)

Under `PyLinks py`, `py.scoresValidExists [] = true`: the fact C-g says is "to be proved once"
(the validation score table of a run without a model is the table with no row, which the score
step returns on the table with no row), needed for the run without a model of E8 to E11, F5, F6.
The contracts run proves it.

#### Consumers that need new proof work

- From 8 (C-h): every proof that uses `keeps` on `readFeatures`, `readMedians` or
  `readScoresValid` must first show the table readable (names: rectangular, distinct, 1 to 32
  characters, no double quote, no leading U+FEFF; one kind per column; `interest_rate` and the two
  medians numeric in the first row) and then exclude the second disjunct for each listed column
  it uses (some row of the window holds a present number there), or carry the text case.
  Directly: `lem:sas_reached_feature_shape`, `lem:sas_reached_scores_read_shape`,
  `lem:metrics_score_frames`, `lem:metrics_flags_reached`, E1, E2, E3, E4, E6, E8 to E11, F1, F5,
  F6, A2, A4, G2, G4, T0 and T1 (the identity read-back: readable gives `oneKind t`, so it meets
  the new form), the examples on reached tables, and the new `lem:py_scores_valid_empty` (the
  table with no row is readable: the read-back of [] is []). Expected hardest: a feature column
  missing in every row of a valid run (the port then reads it as text, the fit frame's numeric
  condition fails); for the medians file, a median missing in the first 20 rows.
- From 5: everything that used the count, distinctness or membership of the split ids.
  `lem:py_split_input_ids`, `lem:sas_split_input_ids`; the "validation set is not empty" lemma of
  G57 (no longer derivable: with the fixed file the validation set can be empty, or the training
  set, on a valid input of at least 4 rows; then the train stage raises, H13 (a)); G1, G2 and
  every contract whose run reaches train (E3, E5, A2, F3, F4, the metrics level, G4); T0's second
  half (`SasLinks` (5) for the paired `sas`); the precondition `fe_run_06_split_precond` asks
  `split_ids ≠ []`, which the clause no longer gives (it is that precondition's own narrowing).
  Where a contract needs a count or a non-empty set, it goes to the owner as a narrowing; nothing
  is added here.

#### Cleared by C-h

No formalized consumer: every statement consumer of `def:pyPipeline`, `def:PyLinks` and `def:Paired`
was already unformalized (334 items, 263 formalized at the start). The edits cleared and restored
`def:pyPipeline` (same Lean), `def:PyLinks` and `def:Paired` (new Lean). `lem:py_score_fillers_idle`
does not depend on them and is untouched (state TheoremProved).
Accepted revisions: `def:pyPipeline` f3d96a77d2c0465bbd3b25d2db113e36 (Lean as before),
`def:PyLinks` 2fbfb39e1c8e496aa90427fdfd1d6a41, `def:Paired` daf7228889fa4fe085d2d32b8d6825f2,
`lem:py_scores_valid_empty` 1a6bd86cb93242a9b5b44531c8aa17f2 (statement; proof to write).
`get_status` at the end: 335 items (one new), 264 statements formalized. `def:ScoreRun` unchanged.

### C-i, 2026-11-19 (later)

Lead's task of 2026-11-19 (prover), on the review of C-h; owner's rule of 2026-11-18/19 (no
contract keeps a hypothesis of its own; a narrowing is the owner's, reported, never taken). The lead
lifted "change no existing item" for `def:Paired`, `def:PyLinks`, `def:pyPipeline`, `def:ScoreRun`
for this task. Changed: `def:PyLinks` (text and Lean), `def:ScoreRun` (text only). `def:Paired` and
`def:pyPipeline`: no finding against them; not touched. Where C-i and an older text of this file
differ, C-i is in force.

#### `PyLinks` 7b, the guard (Lean in place, position 11)

- **Before**: the training score flag is true of S exactly when `score` returns S for some model
  and table, or `noFitTrain F = some S` for some table F (no condition on F).
- **After**: ... or there is a table F with `(py.featTrainExists F && py.featValidExists F) = true`,
  `py.fit (py.readFeatures F) = {}` (the stepwise result with no fit) and `noFitTrain F = some S`.
  The same three parts, in the same order, as the second case of `SasLinks` (8) / `Paired` 5
  (`train_inputs_stop ... = false`, `logistic_no_fit (sas.readFeatures F) = true`, S the chain).
- **Reason**: review witness. For a reached F with both outcomes, `noFitTrain F` (every
  `pd_logistic` and `credit_risk_score` missing) is written by no run, yet the old clause made the
  flag true of it. The code writes the no-fit training score file only when both feature files
  exist (`train.py` 35-41) and `stepwise_logistic` returns `StepwiseResult()` (`sas_compat.py`
  1069-1072, `np.unique(y).size < 2`; the only path with `final` None: line 1120 builds every
  other result with a final fit). The guard is on the fit parameter itself, so the chain
  `noFitTrain` (built at `{}`) is the chain the stage runs on that F.

#### `PyLinks` conjunct 16, `readScoresTrain` (Lean in place, position 16)

- **Before** (C-g, H15): for every table, rows and names kept; `row_id`, `default_flag` numeric
  kept; `pd_logistic`, `credit_risk_score` numeric kept or, when missing in every row of the table,
  the text cell with the missing text; `oneKind t -> oneKind (R t)`.
- **After**: the form of conjuncts 13 to 15 (C-h), with window the first 20 rows
  (`metrics_calculation.py` 117, `guessingrows=20`) and formatted column `interest_rate`
  (`percent8.2`, `train.py` 846-847): on every readable table, rows and names kept; in each of
  `row_id`, `default_flag`, `pd_logistic`, `credit_risk_score` a numeric cell is read back numeric
  (missing stays missing), or, when every row of the window holds the missing number there, as a
  text cell, which is the missing text when the cell was missing; one kind per column in the
  read-back. Written out at its position (not through `keeps`), because of that last part.
- **Reason**: review (a) 21 rows, `pd_logistic` missing in rows 1-20 and 0.5 in row 21: the real
  reader gives text and row 21 reads `'0'`; the old second disjunct needed the column missing in
  every row. (b) rows with other names: excluded by readability. `row_id` or `default_flag` missing
  in the window is read as text too, so the two columns get the same either-or. H15 stays covered:
  a missing cell is written as an empty field, which the text column reads as null.
- **The limit of C-g** ("true on the files a valid run reaches, not on every table") is withdrawn:
  the clause is now stated where it is true of the reader.

#### `PyLinks` 8b and 8c (Lean in place, positions 22 to 25)

`keepsPresent R fmt cols` and 8c now hold on every readable table (formatted columns: none for
the features; `interest_rate` for the two score read-backs). On a readable table in which a column
holds a present number in every row, the window has a present cell, so the reader reads the column
as numbers and every cell present. Reason: review; the writer raises on a table with no
`interest_rate` (`format given for unknown column`) and the reader on two names equal after 32
characters or an empty name beside a `VARn` name, where the clauses asserted a value.

#### The table with no row (text of clauses 4 and 8)

- **Clause 8, the read-back of []**: the read-back of a table t with a row is what
  `proc_import_csv` returns on the file `write_sas_csv` writes from the frame of t. A table with no
  row records no header; it stands for the header-only file the script writes from its own frame,
  which always has its columns (every frame the four files come from is built with its columns),
  and its read-back is what the reader returns on that file: no row (H13 (a), H15). The C-h text
  defined it through `Pl.ofTable []`, a frame with no column, whose file is empty (`NoDataError`).
  Lean unchanged (it already said R [] = [] for readable []).
- **Clause 4, the raw test table []**: stands for the test file of the header line alone (G44),
  with the names of section 5 of the requirements (G46: a header with other names is not valid
  input). The requirements' own reading of a raw table, so no condition is added. Lean unchanged.

#### `ScoreRun`, text only (Lean unchanged, resubmitted)

"Both disjuncts are reached-facts" becomes: the definition alone does not say F1, F2 are reached;
the second disjunct holds whenever `Q.fit F1` returns nothing, also when a feature flag is false at
F1 (then no run writes S1), on both sides alike. A contract applies it with F1, F2 returned by the
features step on its valid input; there each disjunct is a reached fact, and the hypothesis adds
nothing beyond the run.

#### Checked, not changed

- `PyLinks` 7, validation score flag, at []: in the Lean, `Pl.Frame.withColumns` broadcasts each
  column to the frame's height (`Pl.Col.bcast c fr.height`), so step 10 on `Pl.ofTable []` (height
  0) gives height 0, not the one row polars gives a frame with no column; the real file of a
  header-only feature file has its columns and also gives no row. So a model m and F with
  `py.readFeatures F = []` are expected to give `P.score m F = some []` (steps 12 and 14 not
  inspected; `lem:py_score_fillers_idle` gives step 14's output as the cleaned frame).
  `eval_decl` on step 10 failed again on the tool's output schema. Left to the proof of
  `lem:py_scores_valid_empty`; if it fails, clause 7 needs the no-model case of 7b for the
  validation flag, which goes to the lead.
- `PyLinks` 13: the `matmul` line keeps `b != []` (C-h, owner 2026-11-19), which supersedes
  "unconditional" (owner 2026-11-18).

#### Cleared by C-i

`get_status` at the start and at the end: 335 items, 264 statements formalized (the same 71
statements and 1 proof to write). `edit_text` on `def:PyLinks` cleared `def:PyLinks` and its one
formalized consumer `lem:py_scores_valid_empty` (statement only; no proof existed); both restored:
`def:PyLinks` with the new Lean (revision f20bd80e95cb4e8fa5626feeba9fffe5),
`lem:py_scores_valid_empty` with its accepted Lean resent unchanged (2b77fa1ab6614c2e85717b0978902fb5).
`edit_text` on `def:ScoreRun` cleared only itself; Lean resent unchanged
(73d67ded9b5847adb7e4b88c472bebcc). Every other consumer of the two items was already
unformalized. `def:Paired`, `def:pyPipeline`, `lem:py_score_fillers_idle`: untouched. Trust layers
are off on `5365851c` (Lean accepted on compiling), so the match of text and Lean rests on review.

### C-j, 2026-11-19 (earlier)

Lead's task of 2026-11-19 (prover), carrying the owner's decision of 2026-11-19 on the T0 disproof
("Port split": "Fix the port"; stated consequence: the port's split selects exactly (7n+9)/10 ids,
`PyLinks` 5 is restated to say so, T0 and its consumers are re-proved). The lead lifted "change no
existing item" for `def:PyLinks` only, for this task. Changed: `def:PyLinks` (text and Lean, clause
5 only, plus two Lean header comments naming C-j). `def:Paired`, `def:pyPipeline`, `def:PyParams`,
`def:ScoreRun`: not touched. Where C-j and an older text of this file differ, C-j is in force.

#### `PyLinks` 5, the split (Lean in place, position 5)

- **Before** (C-h): for every seed and list of ids, the split table is the one numeric column
  `row_id`, one row per entry, each a number or missing. Nothing more (the file was fixed, so no
  count, distinctness or membership held).
- **The code** (port commit 4a757fb, `feature_engineering.py` 20-25 and 352-366; diff
  `migration/port-to-lean/port-changes-2026-11-19-split.diff`): `file_ids` is the `row_id` column of
  the fixed `split_ids` file, read as text, then `input_best32`. `input_ids` is the set of present
  `row_id` values of the feature frame; `n_train = (7 * height + 9) // 10`. The file is used when it
  names exactly `n_train` ids, pairwise distinct, all in `input_ids`; otherwise
  `random.Random(42).sample(sorted(input_ids), min(n_train, len(input_ids)))`. In both branches the
  ids used are pairwise distinct, all present ids of the input, and their number is
  `min(n_train, number of distinct present ids)` (in the file branch, `n_train` distinct ids among
  `input_ids` exist, so the minimum is `n_train`). For present, pairwise distinct ids that minimum is
  `n_train`, since (7n+9)/10 <= n for every n >= 0.
- **After** (text, clause 5): for every seed and list of ids, of length n (missing entries counted),
  the split table has the one numeric column `row_id`, one row per id listed, each a present
  number; the ids listed are pairwise distinct, each a present id of the list given, and their
  number is the smaller of (7n+9)/10 and the number of distinct present ids of the list. In
  particular, for present, pairwise distinct ids (as `TrainOK` gives through the input check):
  exactly (7n+9)/10 distinct ids, all among those given. With missing or repeated ids: still
  exactly (7n+9)/10 when there are at least that many distinct present ids, otherwise every
  distinct present id once. Nothing is asked of which ids, nor of the seed. No limit.
- **Lean**:

  ```
  (∀ (seed : ℕ) (ids : List (Option ℝ)),
    ∃ l : List ℝ,
      py.split seed ids = l.map (fun x => [("row_id", Tabular.Cell.num (some x))]) ∧
      l.Nodup ∧ (∀ x ∈ l, some x ∈ ids) ∧
      l.length = min ((7 * ids.length + 9) / 10) (ids.filterMap id).toFinset.card)
  ```
- **What `py.split` now stands for.** Under C-h it was the fixed file. Under C-j it is the table of
  the ids the port's split selects: the file's when it fits, otherwise the seeded draw. This is
  what the `PyParams` comment already says ("the table of selected ids"). It is not a narrowing, on
  one condition (below): the unit `fe_run_06_split`, given that table in place of the real file,
  selects the same rows. Either the table fits (it has `n_train` distinct ids among the input's)
  and is used as it is, or, when the input has fewer distinct present ids than `n_train`, it does
  not fit and the unit makes the same draw again (the same pool, the same seed 42). The real file
  therefore disappears from the claim. So the real port is the `py` whose split is that function,
  and that `py` meets clause 5.
- **The condition, owed and not stated** (for the lead): this rests on the list `pyPipeline` passes
  to `py.split` (`VAR1` of the cleaned frame) having the same length and the same present values
  as the `row_id` column of the feature frame that `fe_run_06_split` receives (steps 02 to 05 keep
  the rows; `row_id` is `VAR1`, `feature_engineering.py` 220). It also rests on the idempotence above
  ("`fe_run_06_split` on the table of its own selection selects the same rows as on the file"),
  which is a lemma about the unit. I add neither as an item (no helper nodes). The first is
  needed by any proof that ties `py.split` to the unit's own count; the second only by an argument
  that the real port is covered, not by any contract's proof.
- **`Paired` 2 (C-b), checked; it lines up.** On a table t whose `row_id` is present in every row and
  pairwise distinct, `Paired` 2 gives `Selected` 1 exactly on the rows whose `row_id` the port's
  split lists for the ids of t (`t.map (Sas.num · "row_id")`, so n = |t| and every id is present
  and distinct). By clause 5 the split lists exactly (7|t|+9)/10 distinct ids, each the id of a row
  of t, and each row's id is listed at most once and matched by exactly one row (distinct ids). So
  exactly (7|t|+9)/10 rows get `Selected` 1, the others 0, and the SAS selection is the port's.
- **`SasLinks` (5) (profile), checked; it lines up for the T0 witness.** (5) asks of `sas.split`, for
  every seed and every table, `Selected` 0 or 1 on every row and (7|t|+9)/10 rows with `Selected`
  1. On tables with present, pairwise distinct `row_id` this now follows from `Paired` 2 and
  clause 5 (above). On other tables `Paired` 2 asks nothing, so the `sas` that T0 exhibits takes
  the split of `lem:sas_split_sat` there (the first (7|t|+9)/10 rows get 1). As accepted in C-b,
  (5) is still not derived for every paired `sas` on every table. It is derived on every table
  a valid run gives the split, which was lost under C-h and is restored now.
- **Consumers.** Everything that used the count, distinctness or membership of the split ids, as
  listed under C-h ("From 5"): `lem:py_split_input_ids`, `lem:sas_split_input_ids`, the G57
  "validation set is not empty" lemma (derivable again: from `TrainOK`, n >= 4, so 1 <= n -
  (7n+9)/10, and the training set has at least 3 rows), G1, G2, E3, E5, A2, F3, F4, the metrics
  level, G4, T0. `fe_run_06_split_precond` asks `split_ids ≠ []`, which clause 5 now gives for
  n >= 1 with a present id ((7n+9)/10 >= 1); it is no longer that precondition's own narrowing
  on valid input.
- **Narrowing**: none. Clause 5 is true of the code (under the reading above) on every argument,
  with no limit.

#### Cleared by C-j

`get_status` before and after: 350 items, 290 statements formalized (the same 57 statements and 14
proofs to write). All 50 statement consumers of `def:PyLinks` were already unformalized (`get_items`:
`lem:ex_G2_run`, `thm:F4_model_summary`, `thm:G2_train_coverage` are `TheoremUnformalized` with no
Lean, though `get_status` does not list them among the statements to write). So `edit_text` cleared
`def:PyLinks` only, and nothing else needed resubmitting. `def:PyLinks` was restored through
`edit_statement` on its stored draft: clause 5 replaced in place, then two header comments
(revisions 7722428b0cf340908afb8869d301515a, c4798c3d91644e5d94f772f3776ac28a, final
b29d74d04dc949cd82fb13df38994f0d). Trust layers are off on `5365851c` (accepted when it compiles),
so whether the text and the Lean match rests on review.

### C-k, 2026-11-19 (before C-l)

Lead's task of 2026-11-19 (prover), carrying two owner decisions of 2026-11-19 given in the main
session: "G2 fit" answered "Add the clause"; "S6 lemmas" answered "Restate for the pipeline's
split". The lead lifted "change no existing item" for `def:PyLinks` only, for this task. Changed:
`def:PyLinks` (text: new clause 14 at the end; Lean: new last conjunct, position 30, plus header
comments naming C-k and position 30). New items: `lem:py_split_ids_rowids`, `lem:py_split_fits`
(stated, not proved). `def:Paired`, `def:pyPipeline`, `def:PyParams`, `def:ScoreRun`: not touched.
Where C-k and an older text of this file differ, C-k is in force.

#### `PyLinks` 14, the final fit's first name (new last conjunct, position 30)

- **Text** (clause 14): for every table, whenever the fit parameter returns a final fit, the first
  name of that final fit is `Intercept`. Stated of the fit parameter itself, on every argument,
  as `sas_compat.stepwise_logistic` returns its result; nothing else is asked.
- **Lean** (in words): for every table T and every `LogisticFit` f, if `(py.fit T).final = some f`
  then `f.names.head? = some "Intercept"`.
- **The code** (`port/credit_risk/sas_compat.py`): line 16 and line 672 (`names[0]` is
  "Intercept"); line 1043 (every fit of the selection has `names[0] = "Intercept"`); line 1084 (the
  intercept-only fit is built with `["Intercept"]`); line 1090 (every fit with a variable is built
  with `["Intercept", *cols]`); `fit_logistic` (750) and `_fit_as_sas` (952, 964) return
  `LogisticFit(list(names), ...)`, so the names are those given; the final fit is `cur`, always the
  result of the local `fit` (1120 `final=cur`, 1208 `res.final = cur`; checked every assignment of
  `cur` in 1120-1208); the result with no fit (1069-1072, `StepwiseResult()`) has no final fit; a
  call that raises (`RuntimeError`) returns no result. So the clause is true of the code on every
  argument, with no limit.
- **Narrowing**: none.

#### `lem:py_split_ids_rowids` and `lem:py_split_fits` (new, stated, owed in C-j)

Both at the real numbers, for every `py` with `PyLinks py` and every raw training table meeting
`TrainOK` (so on every valid input; `TrainOK` is what the feature stage reads of the input, as in
`lem:py_split_input_ids`). The cleaned frame is `fe_run_01_clean` on the input check's frame of the
import, as `pyPipeline` and `run` compose them; the feature frame is steps 02, 02b, 03, 04, 05 on it,
as `run` composes them (the frame `fe_run_06_split` receives).

- **`lem:py_split_ids_rowids`**: the list the pipeline passes to `py.split` (`VAR1` of the cleaned
  frame) has the length of the feature frame's `row_id` column, and a real number is a present entry
  of the one exactly when it is a present entry of the other. This is the first condition C-j left
  owed ("the list `pyPipeline` passes to `py.split` ... has the same length and the same present
  values as the `row_id` column of the feature frame that `fe_run_06_split` receives").
- **`lem:py_split_fits`**: for every seed, the `row_id` column of the table `py.split` returns for
  those ids, read as the unit reads it (`(Pl.ofTable table).getF "row_id"`, the `file_ids` of the
  unit), is a list of present numbers, pairwise distinct, each a present `row_id` of the feature
  frame, exactly (7n+9)/10 of them with n the feature frame's height. These are the three parts of
  the unit's test `fits` (`feature_engineering.py` 365: `len(file_ids) == n_train`,
  `len(set(file_ids)) == n_train`, `set(file_ids) <= input_ids`); at the real numbers, Python's `==`
  on floats is equality, so `Nodup` is "distinct" and membership is `input_ids.any eqb`. So
  `fe_run_06_split` uses the table as given, without drawing. Expected proof: `PyLinks` 5, the
  previous lemma, and the input check on `TrainOK` (present, pairwise distinct ids, so the minimum in
  clause 5 is (7n+9)/10).
- **Not done here**: neither lemma is proved, and no S6 contract or other consumer is connected to
  them (the task asked to state them). *(2026-11-20: both are now `TheoremProved`; see the note of
  2026-11-20 at the top of this file.)* The second condition of C-j (the unit on the table of its own
  selection selects the same rows as on the file) is not stated: with `py_split_fits` the unit takes
  the fitting branch on the pipeline's table, which is what a proof about the pipeline needs.

#### Restoring what the `PyLinks` edit cleared

`get_status` before: 358 items, 344 statements formalized, 19 proofs to write; after the edit and
the two new items: 360 items, 350 statements formalized, 23 proofs to write (the two new lemmas;
`thm:F4_model_summary` and `thm:G2_train_coverage`, `TheoremStated` before and after, are now listed
too, which they were not before: a listing difference of `get_status`, as noted in C-j; the count
344 against 348 on the same states is the same difference). No `neg:` item vanished (358 before the
two additions). `edit_text` on `def:PyLinks` cleared all 44 formalized statement consumers (50
consumers, 6 already unformalized: `lem:ex_E3_fit`, `lem:ex_F3_final_model_output`,
`lem:ex_G2_run`, `thm:E9_ks`, `thm:E10_decile`, `thm:F3_final_model_output`). `def:PyLinks` was
restored by `edit_statement` on its stored draft (revisions e4ca1d9f302a4e41bfa7c69b74a0432b,
1c9de65ba4bc48d98c5058d5f70b3878, final 20e0426a5a5c4ff795911dcf7661ba2b). Every one of the 44
statements was resubmitted from its stored draft with `submit_statement` (same revision as before);
their accepted Lean before and after the edit, compared from this session's record by SHA-256, is
identical for all 44. Every state is as before: 27 `TheoremProved`, 17 `TheoremStated`.

Of the 27 proofs, 23 were resubmitted unchanged from their stored drafts and accepted. Four could
not be: each builds a `py` and proves `PyLinks` of it conjunct by conjunct, so the new conjunct has
to be proved too. Each got the smallest addition that proves clause 14 for its own witness, and
nothing else in it changed:

- `thm:T1` (revision e595b2474f8e4b1d8b1a05d8e5fa6693): `?c14` added to the `refine` and a
  `case c14`: the witness's only final fit is `fit1` (`T1W.fitR_final`), whose names are
  `["Intercept"]`, so `rfl`. T1's witness meets the new `PyLinks`.
- `lem:ex_reached_features_predict` (d873c481a701482cae54071f3f586143) and `lem:ex_G4_run`
  (36eb1d4799f440c0ba22e9de7069e3dc): the last bullet of `links` (matvec) now splits the last goal
  in two, matvec as before and clause 14: the fit is `sw0` (final fit `f0`, names `["Intercept"]`)
  or the result with no fit (`fitC_cases`).
- `lem:ex_A4_metrics` (600a3ff93cb04bab9a5c491a5289b75c): `modPy py` changes only the fit to
  `fitM py`, which keeps the final fits of `py.fit` (`fitM_final`); the last component `h29` became
  `h29.1` and clause 14 for `modPy py` is clause 14 of `py` through `fitM_final`.

These four proofs are changes of existing items beyond "resubmit unchanged"; they were made because
the stored proofs could not compile against the new conjunction, and they only add the case for the
new clause. The lead may want them reviewed. Trust layers are off on `5365851c` (accepted when it
compiles).

### C-l, 2026-11-19 (before C-m)

Lead's task of 2026-11-19 (prover), carrying the owner's trusted base B4 item 2 of amendment 2 of
`informal-spec.md` ("on what a valid run reaches `solve` and `inv` raise no error for a singular
matrix"; "G2 has no limit of its own"). Task: add one clause at the end of `def:PyLinks` stating
that fact in the form the preconditions need, unless it is already given. **Result: already given;
nothing changed.** No item of any blueprint was edited, cleared or resubmitted; `def:PyLinks` keeps
30 positions; T1 and every other consumer are untouched (T1's witness meets `PyLinks` as before,
since `PyLinks` is unchanged).

#### What the preconditions ask of `solve` and `inv`

Nothing. Every accepted precondition that reaches the two routines leaves singularity out, in its
Lean, with "the LinAlgError ... is outside the model (§3: OPEN) ... no clause on singularity
(lead)":

- `def:_kept_precond`: a square 2-D array, nothing more ("Singularity is not constrained").
- `def:_inv_sas_precond`: a square 2-D array ("singularity is not constrained").
- `def:_solve_sas_precond`: a square 2-D array and a vector of its size.
- `def:classification_is_made_precond` (2): `_kept_precond` of the product `matmul xT rows`.
- `def:train_run_03_fit_global_rsquare_precond`: `_kept_precond` of `matmul xT x_k` and
  `_solve_sas_precond` of i0, u0 (shapes, from `PyLinks` 13 and 6b).
- `def:classification_table_precond` (4'): `_inv_sas_precond` of `matmul xT xw` (shape).
- `def:_left_out_precond`: reads `fit.cov` only; no routine.

`run_py_py_py_precond` asks these at its calls and adds nothing on the routines' success.

#### Why that is the formal B4.2

In `def:PyParams`, `inv : List (List ℝ) → List (List ℝ)` and `solve : List (List ℝ) → List ℝ →
List ℝ` are total: every call in `_kept`, `_inv_sas`, `_solve_sas`, `classification_is_made`,
`classification_table` and the train units returns a value. A raise of `LinAlgError` has no
counterpart in the model, so "returns its result, no singular-matrix error" holds by the type on
every argument, and no precondition, hence no coverage contract, depends on it. A clause "solve
and inv return their result" has nothing to say in Lean (it would be `True`). Any clause with
content (for instance `inv a` is an inverse of `a`, or `solve a g` solves `a x = g`) would assert
values of the routines, which B4.2 does not trust, and is wider than the trusted fact. So the
fact B4.2 trusts is given by the types of `def:PyParams` together with the preconditions above;
what B4.2 also trusts of numpy (`matmul`, `matvec` shapes) is `PyLinks` 13, positions 28 and 29,
unchanged. G2's Lean (`thm:G2_train_coverage`) already has no hypothesis but `PyLinks py`,
`InputOK` and the reached-equation: no limit of its own in the formal statement.

#### Left to the lead (not changed: a contract is not reworded here)

- The statement text of `thm:G2_train_coverage` still carries amendment 1's sentence "Not
  covered, and stated in the precondition itself: an error of `np.linalg.solve` or
  `np.linalg.inv` on a singular matrix ...". Amendment 2 B4.2 says it is replaced; the Lean does
  not reflect it (it has no such limit). Restating that text is a contract rewording, for the
  lead; editing it clears the G2 statement, which is `TheoremStated` (not proved).
- The OPEN notes in the Lean comments of `_kept`, `_inv_sas`, `_solve_sas` and their
  preconditions ("outside the model (§3: OPEN)") now read as B4.2; they are comments of existing
  items and were left as they are.

#### Narrowing

None beyond B4.2. One remark for the record: the model takes `solve` and `inv` as total on every
argument, not only on what a valid run reaches; since no clause constrains their values, this
adds no fact the claims could use beyond "a value is returned".

### C-m, 2026-11-19 (~~latest~~ before C-n)

Port-translator's correction of `def:train_run_08_ctable_precond` (accepted rev 00420db1), under
the owner's boundary B1 to B6 (amendment 2 of `informal-spec.md`). Restoration and the clause check
by the prover, on the lead's task of 2026-11-19 (the lead authorised restoring cleared items to their
accepted content, nothing else).

#### What changed

Only the Lean of `def:train_run_08_ctable_precond` (statement and signature unchanged; two clauses
guarded):

- :482, no null in the columns `final_names[1:]` of the fit frame: now asked only when there is a
  final fit (`final.isSome = true`). Reason given by the translator: the unit drops nulls where
  Python gets NaN, so guarding by `ctable_made` instead would admit an input on which Python raises.
- :486/:492, no null `pd_logistic` on a complete case: now asked only when the table is made
  (`ctable_made = true`).
- Unchanged: `0 <= n_obs`; each column of `final_names[1:]` a Float64 column of `n_obs` values (on
  every run); `pd_logistic` a Float64 column of the mask's length; `classification_is_made_precond`
  when there is a final fit; `classification_table_precond` when the table is made.

#### Items cleared by the write, restored (prover, 2026-11-19)

All by resubmitting the stored draft unchanged; all accepted:

| item | how | revision | result |
|---|---|---|---|
| `def:run_py_py_py_precond` | `submit_statement` | e914fe13 | accepted |
| `def:zz_carrier_e` | `submit_statement` | 7b33ec2a | accepted |
| `thm:G2_train_coverage` (statement) | `submit_statement` | dba73446 | accepted, judge approved; proof still owed, as before |
| `thm:F4_model_summary` (proof) | `submit_solution` | 819c80cf (5309 lines) | accepted, 0 errors; nothing fixed |

The prover did not hold the Lean the translator fetched before the change; the restored text is the
stored draft, which the write did not touch (only the accepted state was cleared). The F4 proof
compiled with no edit, so C-m broke nothing in it.

#### Clause check (B3: a precondition asks only what the pipeline is proved to pass)

Python: train.py:477-535, `sas_compat.classification_is_made` (:1653-1665), `classification_table`
(:1502-1618). On the run: `fit_frame` is the complete cases of every candidate and `default_flag`
(train.py:99-103); `final_names` is `[]` with no fit and `final.names` with one; `pd_logistic` is
`1/(1+exp(-eta))` on every row of the training features, null on every row with no fit.

Clauses that ask more than the Python needs:

1. **:482 null clause** (`final.isSome = true -> no null`). Python needs it only when the table is
   made and the model has an effect (a NaN in `x_final` makes `ps` NaN and `math.floor` raises);
   with a fit and no table Python runs on, as the clause's own narrowing note says. **Not reachable**:
   `final_names[1:]` are candidates (with a fit, `PyLinks` 8b gives every candidate column present
   with present numbers), and the fit frame keeps complete cases only, so no row of the fit frame
   has a null in a candidate column. The clause holds of every reached argument.
2. **:482 Float64 kind**. `np.asarray(..., dtype=float64)` also takes an Int64 or Boolean column.
   **Not reachable**: with a fit, `PyLinks` 8b makes every candidate column of the read-back hold a
   present number in every row, which `Pl.ofTable` gives as a Float64 column. With no fit the
   clause is about `[].drop 1` and is empty.
3. **:486 null clause** (`ctable_made = true -> no null pd on a complete case`). Asked also for an
   intercept-only final model, where Python replaces `ps` by the leave-one-out mean and runs on (the
   clause's narrowing note). **Not reachable**: `ctable_made` implies a fit, so the intercept is
   present and every effect column is present on a complete case; `pd_logistic` is non-null there.
4. **Inherited through `classification_table_precond`**, on the call `(y_train, x_final, pd_train)`:
   (3) `0 < pd < 1` with more than one column (numpy runs at 0 and 1 with a warning); (7)
   `0 <= klo`, `khi <= 50`; (8) the sum of `y` integral (Python truncates). **Not reachable at ℝ**:
   `pd = 1/(1+exp(-eta))` with `exp > 0` lies strictly in (0, 1), so does `_expit`, so `ps` lies in
   [0, 1] and the bounds hold; `y_train` is `default_flag` on complete cases, 0 or 1 under `InputOK`
   and `PyLinks` 8c, so its sum is integral. Remark (not a defect of the clause at ℝ, where the
   contracts are stated): at Float `pd` is exactly 1.0 for `eta` above about 36.7, which a separated
   fit with a table can reach (judge/runs/sep_age_gt_55 has leave-one-out probabilities of 1; `pd`
   itself was not checked); there clause (3) would be false although Python runs on.

Clauses the Python needs (kept by B3; each met on the run): `0 <= n_obs` (`np.ones`; `n_obs` is the
fit frame's height); each column of `final_names[1:]` present with `n_obs` values (`get_column`
raises `ColumnNotFoundError`, `np.column_stack` on different lengths; built on every run, a fit or
not, before the test of :490); `pd_logistic` present with the mask's length (boolean index);
`classification_is_made_precond` (shapes; `_left_out` reads `fit.cov[i, i]`); the shape clauses
(1), (2), (4'), (5), (6), (6') and `ps` non-empty with no NaN of `classification_table_precond`.

**Result**: no clause of the C-m precondition can be violated by an argument a run on valid input
reaches at ℝ; four ask more than the Python needs (items 1 to 4 above) and are met on every reached
argument, so they are proved facts under B3, not narrowings of the claim. Owed: their proof is part
of `thm:G2_train_coverage` (still `TheoremStated`).

#### Observed, not touched

`get_status` after the restore: 360 of 366 statements formalized; `lem:zz_G2s1415_s14_merge_check`
and `lem:zz_G2s_step06_check` have no accepted statement, and `lem:ex_sas_cov_train_bins`,
`lem:metrics_flags_reached`, `thm:G2_train_coverage` have no accepted proof. They were not in the
list of items C-m cleared and were left as they are.

### C-n, 2026-11-20 (latest; fidelity finding F1)

Recorded from `reports/port-lean-fidelity-2026-11-20.md` (sections "PyLinks clause 10 restated
(finding F1)", "The re-proofs" and "The audit"). The records were written after the restatement;
the restatement itself was made on `5365851c` on 2026-11-20.

#### Why

Finding F1 (high) of the fidelity review: clause 10 as stated, "for every whole number n",
`parse_float (sas_best (some n) 8) = n`, is false of the real port. `sas_compat.sas_best`
(`port/credit_risk/sas_compat.py:391-423`) switches to E-notation when the integer part does not
fit in 8 characters, and `metrics_calculation._into_float` (`metrics_calculation.py:18-21`) parses
that text: `sas_best(123456789, 8)` = `1.2346E8`, read back as 123460000; `sas_best(1e8, 8)` =
`1E8`. So the real port's parameters did not meet `PyLinks`, and a contract of the form "for all
py with `PyLinks` py" did not formally cover the real port, only ports whose formatter is exact on
every count. The spec (B3 rewording of G56, `informal-spec.md` section 9) already said valid input
bounds the counts below 10^8 and the round trip is exact there; the clause had not been restricted
to that range.

#### What changed

- `def:PyLinks` clause 10, text (`edit_text`) then Lean (`edit_statement`), both compiled and
  accepted by the judge:
  `∀ n : Nat, n < 10 ^ 8 → parse_float (sas_best (some n) 8) = n ∧ sas_best (some n) 8 ≠ ""`;
  `sas_best none 8 = ""` unchanged. The text cites F1 and the example above. No other clause, and
  neither the number nor the order of the clauses, changed. The clause is weaker than before and
  no stronger than the code.
- `lem:metrics_ks_table` (a lemma, not a contract): its hypothesis `hcount` of the same shape is
  restated as `∀ n : Nat, n ≤ V.length → ...` and moved after `f` and `V`; the number of
  hypotheses is unchanged. This bound, `n ≤ V.length` rather than `n < 10^8` with a new
  `V.length < 10^8` hypothesis, is the one place that goes beyond the literal wording "n < 10^8";
  left for review.
- No contract gained a hypothesis. `pyPipeline`, `Paired` and `SasLinks` are unchanged (`SasLinks`
  has no count clause; the SAS bound is the first clause of `total_good_bad_precond`).
- Not changed (records only, no Logos write): the Lean header comment of `def:PyLinks` still lists
  corrections up to C-k only.

#### Where the bound is discharged

Clause 10 is used only through `lem:metrics_ks_table`, whose consumers are
`thm:E8_validation_summary`, `thm:E9_ks` and `thm:G4_metrics_coverage` (the counts `total_good`,
`total_bad` of `metrics_run_02_ks`). In each, the call passes
`fun n hn => hCnt n (lt_of_le_of_lt hn hVlt)`, where `hVlt` is the lemma that the sorted
validation score table has fewer than 10^8 rows on valid input. It is proved inside each proof
file, not as a blueprint item: `E8R.read_len` in `thm:E8_validation_summary`, `e9_valid_len` in
`thm:E9_ks`, `g4_valid_len` (with `g4_F2_len`; `g4_fit_core` takes the new clause and
`xv.length < 10^8`) in `thm:G4_metrics_coverage`. The argument: read-backs keep the number of rows
(`PyLinks` 8), the SAS score chain keeps rows, `Paired` 2 with `lem:sas_split_input_ids` makes the
validation export a filter of the split of the raw training table, and `InputOK` bounds the raw
rows below 10^8 (G56, `hOK.1.2.2.2.2`). So n ≤ V.length < 10^8. Edges added with `connect`:
E8 to `lem:sas_reached_feature_shape` and `lem:sas_split_input_ids`; G4 to
`lem:sas_split_input_ids`. In `thm:T1`, `lem:ex_G4_run` and `lem:ex_reached_features_predict` the
witness round-trips every n, so the bound is taken and not used (`intro n _`). Step 05
(`total_defaults`, `overall_default_rate`) feeds only the printed cumulative lift file; no
contract uses clause 10 for it.

#### State after the restatement (from the audit, not re-read here)

The edit cleared 62 items; they were restored from their stored drafts. At the audit, 30 of 30
contracts were `TheoremProved` by state, but 18 rested transitively on `thm:fe_run_06_split_S6a`,
then `TheoremStated`, and seven `lem:ex_*` items and `lem:ex_port_train_outcomes` were not
re-proved. See the report for the list; this correction records the restatement, not a close.

### Additions that are not changes of wording

- **Two record items.** The server takes one declaration per item, so the parameters are two
  items of their own: `def:PyParams` (the port parameters of section 1, fields only, no
  condition) and `def:SasParams` (the 17 parameters of `sasPipeline` in its order and types,
  then `today`). Author prover-1; reviewer prover-9.
- **`pyPipeline.score` and the changed train stage.** Step 12 takes two frames and step 14 eight
  frames and a Boolean; the validation output depends on none of the others. `score` calls the
  units themselves with the risk-scored validation frame in the idle slots and `false`, and
  looks up `risk_scores_validation.csv` in the result. The independence of the validation
  output from the idle slots is a required lemma, proved before any F-contract cites
  `pyPipeline`.
- **`pyPipeline.fit`**: superseded by C-d (it tests both feature flags). The first form of
  this addition read: it stops on the training feature flag only, as the text says; under
  `PyLinks` 7 the two flags agree, so E3 is not affected.
- **Importers** are optional-valued (`importTrain`, `importTest`); `PyLinks` 3 and 4 say a valid
  table gives a value and say nothing of other tables.
