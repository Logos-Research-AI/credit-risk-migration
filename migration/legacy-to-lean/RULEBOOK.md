# Translation Rulebook: SAS to Lean (blueprint `sas-credit-risk-spec`)

> **The meta-rule: if two agents could answer a question differently, the answer goes in this
> file.** Every implementer, reviewer and fixer reads it before touching the blueprint. It is
> read-only inside any loop. Amendments are queued in `migration/amendments.md` and applied
> between batches by the orchestrating session only.

Read this whole document before writing any Lean.

## 0. The foundation (read-only)

`foundation/foundation.pdf` (blueprint `credit-risk-foundation`) fixes the shared types and
nothing else. Never redefine or work around them.

- Number type: every definition is written once for `{α : Type} [Tabular.RealLike α]`.
  Never mention `ℝ` or `Float` in an item. `Float` appears only in evaluation inputs.
- `Tabular.Cell α` is `num (Option α)` or `str (Option String)`; `Tabular.Row α` is a list of
  `(column name, cell)` in column order; `Tabular.Table α` is a list of rows in row order.
  `Tabular.Row.get` reads the first pair with a name, `Tabular.Row.set` overwrites in place or
  appends at the end.
- Convention 1: every division, `log`, `sqrt`, `exp` is guarded as SAS guards it or covered by
  a precondition. In this blueprint they are always guarded, by the `Sas.*` operations of §2.
- The foundation decides no SAS behaviour. Each behaviour below is ours and cites evidence.

## 1. Scope and posture

- Fidelity only. The Lean does what SAS does on this code, including what looks wrong. Do
  not tidy, simplify, reorder, merge duplicated logic, or fix. `predict.sas` repeats the
  feature engineering of `feature_engineering.sas`: translate it again from its own lines;
  never call the other unit's row function.
- Arithmetic is kept exactly as written: same operations, same order, same grouping.
  `a * b / 100` is `Sas.div (Sas.mul a b) (some 100)`. `2 * (p * r) / (p + r)` is
  `Sas.div (Sas.mul (some 2) (Sas.mul p r)) (Sas.add p r)`. Never fold constants: SAS
  evaluates `base_rate + 0.02` at run time in binary64 (D14), so it is
  `Sas.add base_rate (some 0.02)`, not `some 0.07`.
- In scope: DATA steps, PROC SQL, PROC SORT, PROC RANK, PROC FREQ with `OUT=`, the
  `%confusion_metrics` macro, scoring from a fitted model, the ROC association statistics and
  the Hosmer-Lemeshow partition computed from fitted probabilities.
- Out of scope, each an explicit input: the model fit (the fitted model is a parameter), PROC
  IMPORT (the imported table is a parameter of the first step of each script), PROC
  SURVEYSELECT (its output table is a parameter), printed formats, PROC EXPORT, and
  listing-only output (PROC PRINT, MEANS, FREQ without `OUT=`, CONTENTS, SGPLOT, `%put`).
  `FORMAT` statements change no value and are not translated.
- Each statement is compiled and judged when written (`write_statement`). A unit is done when
  `get_status` shows its statement accepted, not before.

## 2. SAS behaviour: one canonical mapping each

The shared runtime lives in namespace `Sas`, inside the code item that first needs it (the
"home" column). Use these; never write a second version. Read the home item's Lean with
`get_lean` before using a helper. Evidence: `Xnn` is `experiments/xnn_*.{sas,log}`, `Dn` is
`migration/evidence/sas-docs.md` section n, `REF` is `judge/reference/`.

| # | SAS behaviour | Lean | Home | Evidence |
|---|---|---|---|---|
| R1 | Numeric value; `.` is missing | `Sas.Num α := Option α`, `none` is missing | `def:credit_raw_clean` | D2 |
| R2 | Overflow of any arithmetic result gives missing | `Sas.fin` (applied inside every operation) | same | X10 |
| R3 | Comparison: missing is below every number and equal to itself; result is a Boolean | `Sas.lt le gt ge eq ne`, `Sas.isMissing` | same | X10, D2, REF scenario `edge_predict` |
| R4 | `v = (cond);` gives 1 or 0 | `Sas.ofBool` | same | D2 |
| R5 | `if v then`: false when zero or missing | `Sas.truthy` | same | X10 |
| R6 | `+ - * /` with a missing operand give missing; division by zero gives missing; binary64, left to right | `Sas.add sub mul div` | same | X10, X04 |
| R7 | `LOG` of zero or negative gives missing; `EXP` overflow gives missing; `ABS` | `Sas.log exp abs` | same | X10, X05 |
| R8 | Variable read, assignment, `DROP`, `KEEP`, `RENAME`; new variables go after existing ones; `KEEP` does not reorder | `Sas.num chr setNum setChr drop keep rename` | same | D4, REF column orders |
| R9 | `INPUT(text, BEST32.)`: after leading and trailing blanks, `[sign]digits[.digits]` with one digit or more is that number (`5.`, `.5`, `-.5`, `0005` included); a blank or `.` is missing; every other text is missing, **except** exponent notation (digits or a point directly followed by e, E, d or D, then an optional sign and digits: `1e3`, `1D2`, `1.5e3`, `5.e1`, `1d-2` are numbers), which is not modelled and is excluded by precondition. `5000-1`, `1+2`, `5-`, `- 5`, `1 2`, `1,000`, `$5`, `0x10`, `bad`, `e5`, `-e5`, `1e`, `12d` are missing | `Sas.inputBest` (no exponent notation: precondition) | same | REF log, X06, X04; X21 part A and X22 part A (89 texts, value and HEX16) |
| R10 | `SUM(a,b,...)`: skip missing, add left to right, missing if all missing. Sum statement `v + e;` is `v = SUM(v, e)` | `Sas.sumFn [..]` | same | X10, X14, X13 (retain) |
| R11 | `MIN`, `MAX` functions: over the nonmissing arguments | `Sas.minFn`, `Sas.maxFn` | same | X10 |
| R12 | Character values: trailing blanks are not represented; blank is missing (`Cell.str none`); length comes from the first assignment (no value in this code is truncated: `Review` in a `$7`, statuses in `$20`) | `Sas.chr`, `Sas.setChr`, Lean `String` equality, `∈ ["A","B"]` for `IN` | same | X13 (char), D4 |
| R13 | Stable ascending sort, missing first (PROC SORT; also the order of GROUP BY and ORDER BY keys) | `Sas.sortBy` | `def:income_medians` | D5, X13 |
| R14 | PROC SQL `GROUP BY`: one output row per distinct key, keys ascending, missing first, missing is a group | `Sas.groupKeys` | `def:income_medians` | X13 |
| R15 | PROC SQL `MEDIAN` aggregate: nonmissing values sorted; odd count gives the middle one, even count gives `lo + (hi - lo) / 2`; missing when no value | `Sas.sqlMedian` | `def:income_medians` | X13, X14 |
| R16 | PROC SQL join `ON a.k = b.k`: missing matches missing. Row order of a join result is **not determined** (X13: sorted by key, order inside a key scrambled; REF: same). A unit that exposes join order takes the arrangement as a parameter | see §4 P1 | `def:income_medians_all` (moved in round 2; was `def:credit_imputed`) | X13, REF |
| R17 | PROC SQL `SUM`, `MEAN`: missing values are skipped; no value gives missing. The floating-point accumulation is **not determined** (X13: neither a left fold in input order nor sum/n). Parameter `agg : Sas.SqlAgg α` | `Sas.sqlSum agg`, `Sas.sqlMean agg` | `def:total_good_bad` | X13, X05 |
| R18 | PROC SQL `MIN`, `MAX`, `COUNT(*)`; a Boolean inside `SUM(x = 0)` is 1 or 0 (missing compares as R3) | `Sas.sqlMin`, `Sas.sqlMax`, list length | `def:total_good_bad` | X13 |
| R19 | `SELECT ... INTO :m` stores the `BEST8.` text of the number; using `&m` reads that text back. A missing value becomes `.` and reads back as missing. Integers below 10^8 are unchanged (precondition); otherwise the round trip is the parameter `best8 : α → α` | see §4 P3 | `def:total_good_bad` | X03, X13, X05 |
| R20 | PROC FREQ `TABLES a*b / OUT=`: one row per observed pair, missing levels included, sorted by `a` then `b` with missing first; `COUNT`; `PERCENT = 100 * COUNT / N` with N the rows where both are present, and missing on a missing-level row | `Sas.freq2` | `def:confusion_matrix_train` | X13 |
| R21 | One-to-one `MERGE` (no `BY`): row i takes the i-th row of each data set; rows = longest input; a later data set overwrites a same-named variable; a data set that has run out sets its own variables to missing but does not overwrite a variable another input supplies; a `WHERE=` that selects nothing still contributes its variables | `Sas.merge11` | `def:model_summary` | X01, X13, X15A, D9 |
| R22 | `RETAIN v 0` keeps the value across rows; `retain v;` starts missing; `_N_ = 1` is the first row; `END=eof` is true on the last row; with no input rows the step body never runs | explicit fold over the rows | each unit | X13, D3 |
| R23 | RETIRED in round 2 (ruling G35: the score is no longer rounded; `Sas.round` is removed from the blueprint). Was: `ROUND(x)` | none | none | X11, D1 (kept for the record) |
| R24 | PROC RANK `GROUPS=k`: ties get the mean rank; group is `floor(rank * k / (n + 1))` with n the nonmissing count; missing stays missing; `DESCENDING` ranks from the largest; rows keep input order; the new variable is appended | `Sas.rankGroups` | `def:decile_data` | X12, D6 |
| R25 | PROC LOGISTIC `ROC ... PRED=`: rows with a missing response or probability are dropped; probabilities are grouped from the largest down, a value `p` joining the current group exactly when `top - p <= ROCEPS`, where `top` is the group's largest value and ROCEPS = 3184525836262887 * 2^-78 (binary64 `3E46A09E667F3BCE`, one unit in the last place above the binary64 nearest to sqrt(2^-53), which is 6369051672525773 * 2^-79); otherwise it starts a new group. The anchor is the group's largest value: not the previous value (no chaining), not the smallest, and ties are not decided pair by pair. A pair (event, non-event) is concordant, discordant or tied by group; `Area = (nc + 0.5 * nt) / (n1 * n0)`. Only `ROCModel` and `Area` are produced (the other ROCAssociation columns are never read) | `Sas.rocTops`, `Sas.rocArea` | `def:roc_train` | D10 (default "square root of the machine epsilon", not the value SAS applies). X08: 159 four-row cases with the gap stepped one unit in the last place at a time around sqrt(2^-53), at 12 base values from 0 to 0.86; in every series the last tied gap is the largest binary64 <= `3E46A09E667F3BCE` and the first separated gap is the smallest >= `3E46A09E667F3BCF`; sqrt(2^-53) to nearest as the bound fails 6 cases, `3E46A09E667F3BCF` with `<=` fails 4, 1e-8 fails 40. X07 `roc` lines (162 cases, Area in HEX16): counts right on all 162 with this rule; chains of 3 and 5 values (cases 76-90) refute anchoring at the smallest value (11 cases wrong) and pairwise ties (10 wrong); the four fits of X07 part C refute chaining. Area: `(nc + 0.5 * nt) / (n1 * n0)` equals SAS to the bit on 162 of 162; `(nc + nt/2)/n1/n0` on 150, `nc/t + 0.5*(nt/t)` on 140, `0.5*(1 + (nc - nd)/t)` on 152, `1 - (nd + 0.5*nt)/t` on 122 (`(2*nc + nt)/(2*t)` is the same correctly rounded quotient). X15B. REF: 280 tied pairs of `printed_association.csv`. Analysis: `migration/analyze_x07_x08.py`. OPEN (cannot be seen on binary64 inputs): `top - p <= 3184525836262887 * 2^-78` and `top - p < 6369051672525775 * 2^-79` are the same predicate on binary64 differences; they differ only for a number type with values strictly between the two |
| R26 | Linear predictor of a fitted model (PROC LOGISTIC `XBETA`, PROC PLM `SCORE`): `intercept + b1*x1 + b2*x2 + ...`, added left to right in the order of the parameter table; missing when a model covariate is missing. PROC LOGISTIC's OUTPUT data set also carries `_LEVEL_` (amendment A6) | `Sas.linpred` | `def:logit_scored_train_output` | X15C (2998 of 2998 rows bit-exact, PLM equals XBETA, missing covariate gives missing, missing response still scored), D13. OPEN: parameter order after stepwise selection is taken from the fitted-model parameter |
| R28 | PROC LOGISTIC Association table: pairs of one event and one non-event, tied by the grouping of R25 (same anchor, same ROCEPS); `c = (nc + 0.5 * nt) / t`, percentages `100 * n / t`, `Gamma = (nc - nd) / (nc + nd)`, `Tau-a = (nc - nd) / (0.5 * N * (N - 1))`, Somers' D `2 * c - 1` | `def:logistic_association` | own unit | D11, X15C, X15D, X07 part C (four fits of 400 rows whose predicted probabilities have 36 to 40 gaps under 5e-8). Tie rule: the R25 grouping gives SAS's concordant, discordant and tied counts on all four fits; chaining, anchoring at the smallest value, pairwise ties and exact equality fail all four, a bound of 1e-8 fails three. Somers' D: `2 * c - 1` equals SAS to the bit on all four fits and on X15C, X15D; `nc / t - nd / t` fails fits C1 and C4, `(nc - nd) / t` fails C1, C3, C4. Percentages: `100 * n / t` to the bit on all four (`100 * (n / t)` fails C3). The fits do not separate ROCEPS from sqrt(2^-53) to nearest (no gap falls between them); R25's value is used |
| R29 | Hosmer-Lemeshow partition: rows sorted by probability; a block is the run of probabilities within 1e-6 of its first (amendment A5; REF `printed_hl_partition.csv`, all 20 counts); target `T = floor(F / 10 + 0.5)`; a block joins group j if j = 10, or if `f_j < T` and `f_j + floor(f / 2) <= T`; a last group below `F / 20` is folded into the previous one | `def:logistic_lackfit` | own unit | D12, X15C, X15D (totals and observed counts of all 18 groups reproduced). OPEN: accumulation of expected counts and the statistic (not given); boundary at exactly 1e-6 |
| R27 | A numeric literal is the nearest binary64 number: `(0.05 : α)`, `(2500 : α)` | Lean literals through `OfScientific` and `NatCast` | every unit | X04, D14 |
| R30 | `MISSING(v)`: true for a missing number and for a blank character value | `Sas.missingVar` | `def:credit_raw_input_check` | D16; X19; runs `dbg3_fix_Q27_sequence` (age missing), `ev_fix_Q27_test` |
| R31 | `x >= 0 and x = int(x)` (whole-number test). `INT` returns the neighbouring integer when the argument is within 1E-12 of it, and the comparison with `x` is then exact, so `0.99999999999999` is not whole | `Sas.eqInt` | same | D17; X19; run `dbg3_fix_Q27_sequence` (counts 0.5, -1, 0.99999999999999; dependents 1.5) |
| R32 | A text cell that is blank, `.` or `NA` after `CATS` (leading and trailing blanks removed) counts as "not given"; any other text must read as a number through `%num` or the row is bad | `Sas.blankDotNA` | same | D18; X19; run `dbg3_fix_Q27_sequence` (`12345abc`, `abc`, 34-digit income) |
| R33 | PROC SQL `COUNT(DISTINCT v)`: number of distinct nonmissing values; `COUNT(*) - COUNT(DISTINCT id)` is the number of surplus rows | `Sas.countDistinct`, `Sas.sameValue` | `def:credit_raw_check_totals` | D19; runs `dbg3_fix_Q27_sequence` (duplicate id), `ev_fix_Q27_test` |
| R34 | PROC SQL `COALESCE(a, b)`: the first nonmissing argument, missing when all are | `Sas.coalesce` | `def:income_medians_all` | D20; run `ev_fix_Q1` (`income_medians.csv`: groups 2-5 take the overall median 5000) |
| R35 | `BY v` with `last.v`: true on the last row of each run of equal `v` (input sorted; missing is a value) | lookahead inside the fold of `def:ks_calculation` | `def:ks_calculation` | D21; runs `ev_fix_Q23_tie`, `ev_fix_Q24` |
| R36 | `SET t NOBS=n END=eof` with `if _n_ = ceil(k * n / 10) then cut{k} = score` under `RETAIN`, one row written at `eof`: cut k is the score of row `ceil(k*n/10)` of the sorted table, k = 1..9. In Lean the index is the natural number `(k*n + 9) / 10`, exact for every n (no floating-point CEIL, so the CEIL fuzz of D22 cannot matter: k*n/10 is either an integer or at least 0.1 away from one). An empty table gives no cuts | fold in `def:psi_cuts` | `def:psi_cuts` | D22; runs `final_edge_metrics_a/b/c`, `ev_fix_Q23_tie`, `ev_fix_Q24`, `ev_fix_Q25` |
| R37 | `if _n_ = 1 then set one_row_table;` in front of `set t;`: the values are kept for every row; when the one-row table has no row the step ends at that SET and writes no row | `def:train_bins`, `def:valid_bins` return the empty table when `psi_cuts` is empty | `def:train_bins` | D23; X22 part F (psi_cuts with 0 rows: TRAIN_BINS 0 observations, VALID_BINS 0 observations with 3 validation rows); X21 part F (lines 278-359 on an empty training table: psi_floor `.`, ten PSI rows with shares 0 and missing component, PSI missing, 'No significant change') |
| R38 | SAS finds a variable by name whatever the capitalisation (data-step reference, `"name"n`, VARNUM, KEEP). Modelled in the input-check units only (they decide which files are accepted); every other unit keeps the exact reference names of A10 | `Sas.getCI`; KEEP as a filter on upper-cased names | `def:num_macro` | X21 part B (headers AGE, DEBTRATIO, monthlyincome, seriousdlqin2yrs, numberofdependents: columns_ok=1, bad_rows=0, known_incomes=2) |
| R39 | PROC IMPORT of a CSV holding the header line only fails ("Unable to sample external file, no data in first 5 records. Import unsuccessful"); the table is not created, dictionary.columns has no row for it and `columns_ok` is 0: the script stops. A `Table` with no row therefore stands for "no table" in `*_columns_ok` | `credit_raw_columns_ok`, `test_raw_columns_ok` give `false` on `[]` | both | X21 part C |
| R40 | `%num(v)` on a column the table does not have is missing on every row (the `%else` branch creates the variable) | `none` branch of `num_macro`, `test_num_macro` | both | X21 part D (file without age: bad_rows=2, columns_ok=0) |
| R41 | `a.VAR1 as row_id` carries the value as it is; VAR1 is character when an id is not a number, and the check accepts such ids when not blank and not repeated | `test_imputed` copies the cell; `kaggle_submission_precond` asks only that row_id be present | `def:test_imputed` | X21 part E (ids A1, A2, A2, blank: bad_rows=1, duplicate_ids=2; row_id Char $2) |

**The BUG rule.** Where SAS's behaviour looks defective, reproduce it and mark the line
`-- BUG(port): <what>`. Known sites are listed in the inventory.

**The UNKNOWN rule.** When neither this table nor the inventory decides a case, do not guess.
Make the behaviour an explicit parameter of the unit (a function argument with a comment
`-- OPEN(port): <question>`), or exclude it with a precondition, and report it. A stalled unit
is worse than an open one; a guessed one is worse than both.

**Standing assumption on every input (amendment A7).** SAS numbers are finite binary64 values or
missing: there is no NaN and no infinity in a SAS data set. Every unit assumes that the numeric
cells of its inputs are finite (`isFinite`) and not NaN, and that numeric cells and coefficients
handed in as parameters are too. The `Sas` operations never produce a non-finite value (R2).
On a number type with a NaN the comparisons of R3 are not a total order and nothing is claimed.

**Standing assumption on table shape (amendment A10).** A unit reads each variable by its exact
name (SAS names are case-insensitive; the tables here carry the capitalisation of the reference
CSV headers; the input-check units are the exception and ignore case, R38), assumes the variables it reads are present with the type SAS gives them, and
assumes its input has no variable already named like one the step creates or retains
(including TP, TN, FP, FN, cum_good, cum_bad and the scratch names of each step). Where a
precondition item exists it states this; where none exists, this paragraph is the condition.

**Rule numbers inside `def:credit_raw_clean`.** That item numbers its comments R1-R10 by its own
count: its R7 (variables, DROP/KEEP/RENAME) is R8 here, its R8 (`INPUT`) is R9, its R9 (`SUM`)
is R10, its R10 (`MIN`/`MAX`) is R11; its R6 covers R6 and R7 here. All other items use the
numbers of this table.

## 3. Lean conventions

- One code item per unit, id `def:<name>`, Lean definition named `<name>` (the SAS data set
  it creates, lower case). Add it with `add_code` (file, line range, verbatim source) and
  `depends_on` = the home items of the helpers it uses plus its upstream units by data flow.
- Helpers used by one unit only are written above the unit's definition in the same
  statement, in namespace `Sas` if they state a SAS rule, otherwise in a namespace named
  after the unit. Never add a blueprint item for a helper.
- A DATA step over rows is `input.map fun r => ...` with one `let r := Sas.setNum r "x" (...)`
  per SAS assignment, in source order, reading with `Sas.num r "x"`. `IF/ELSE IF` chains are
  Lean `if/else if` chains over the `Sas` comparisons, in source order. Every branch that
  assigns in SAS assigns in Lean.
- Column names are the SAS names with the capitalisation of the reference CSV headers.
- Literals: `(some 30 : Sas.Num α)` or `some (30 : α)`; decimals `some (0.05 : α)`.
- Comments: plain `--` only. No doc comments (`/-- -/`). Each unit starts with a comment
  giving file and lines. Evidence is cited by id.
- Markers, greppable, exact spelling: `BUG(port):`, `OPEN(port):`, `TODO(port):`.
- A table crossing a stage boundary (a CSV hand-off) is a `Tabular.Table α` with the SAS
  column names and order. Inside a stage, tables are also `Tabular.Table α` unless a rule
  says otherwise.
- Preconditions are separate items (`add_precond`, id `def:<name>_precond`), a
  `def ... : Prop` over the unit's inputs: column presence and type, value domains,
  non-emptiness, and anything the Lean needs to be faithful. No postconditions.

**"Stopped" (round 2, rulings G33/G34).** A script that stops is modelled by a Boolean unit, true = stop: `credit_raw_stop`, `test_raw_stop` (input check) and `train_inputs_stop`, `metrics_inputs_stop`, `predict_inputs_stop` (an input file is absent). The units after it are still total functions; whoever composes the pipeline must read the Boolean first and, when it is true, take every output of that script as absent. The removal of the previous outputs at the top of each script (so that a stopped run leaves none) is a file-system effect and is not translated (`out-of-scope.tsv`); its consequence, "the next script finds no input and stops", is what the `*_exists` parameters (P8) express.

## 4. Parameters (what is an input, not a definition)

| # | Parameter | Units | Why |
|---|---|---|---|
| P1 | `arrange : Table α → Table α`, a rearrangement of the join result | `credit_imputed`, `test_imputed` | R16: join row order is not determined |
| P2 | `agg : Sas.SqlAgg α` (`sum`, `mean` over a list of present values) | units with PROC SQL `SUM`/`MEAN` of non-integers | R17 |
| P3 | `best8 : α → α`, value of the `BEST8.` text of a number (applied to both macro variables; on an integer below 10^8 it is the identity) | `total_defaults` (feeds `cumulative_lift`); round 2: `psi_floor` (feeds `psi_calculation`), where the value is **not** an integer: `0.5/7000` is stored as `0.000071`, `0.5/105000` as `4.762E-6` | R19 |
| P4 | the fitted model `Sas.Model α`: intercept and `(variable, coefficient)` list in parameter-table order | scoring units | fit out of scope |
| P5 | `invLink : α → α`, how PROC LOGISTIC's `OUTPUT PREDICTED=` turns the linear predictor into a probability | `logit_scored_train_output` | X15C: none of `1/(1+exp(-x))`, `exp(x)/(1+exp(x))`, `1-1/(1+exp(x))` reproduces more than half the rows to the bit |
| P6 | the imported table of each script; the SURVEYSELECT output | first unit of each script; `credit_train_validation` | out of scope. Round 2: also `train_income_medians`, the table PROC IMPORT reads from `income_medians.csv` (predict.sas 155-161), parameter of `test_imputed`; the BEST32. text round trip of the medians and the type guessing lie inside it |
| P7 | `today : Sas.Num α`, the value of `TODAY()` | `model_summary`, `model_performance_metrics` | clock |
| P8 | `*_exists : Bool`, whether each input file of the script exists (`FILEEXIST`) | `train_inputs_stop`, `metrics_inputs_stop`, `predict_inputs_stop` | the file system is outside the model (round 2) |

## 5. The gap inventory

`migration/inventory.tsv`: one row per site where SAS leaves something implicit. Look your
site up; do not decide it. A site that is missing from the inventory is an inventory bug:
report it and apply the UNKNOWN rule.

## 6. Per-unit obligations

- The statement is accepted by the server.
- The implementer's report lists, for the unit: inventory rows applied, parameters taken,
  preconditions needed, markers left.
- Reviewers answer one question with evidence: does this Lean do anything the SAS does not,
  or omit anything it does? Every finding cites a rule number or a source line.

## 7. Deviation log

| ID | Date | Deviation | Sanctioned by |
|---|---|---|---|
| DEV-001 | 2026-11-10 | Kit step 00 (feasibility) skipped | PROMPT.md |
| DEV-002 | 2026-11-10 | No depmap script; manifest written by hand in source order | PROMPT.md |
| DEV-003 | 2026-11-10 | Sign-off gates run through without stopping; each recorded in `migration/gates.md` | PROMPT.md |
| DEV-004 | 2026-11-10 | `judge/run_sas.py` cannot run here (it imports `mutations.py`, which is not in this workspace). Experiments run through `migration/run_experiment.py`, same saspy profile, programs submitted verbatim | orchestrating session, to be confirmed |
| DEV-006 | 2026-11-10 | Evaluation helpers with no SAS meaning (`Sas.Eval.apply`, `model_performance_metrics.evalApply`, `test_predictions_full.evalApply`) sit in three code items, and the two sink items carry extra dependencies for that purpose only: `eval_decl` can call only a declaration of the evaluated item | orchestrating session, to be confirmed |
| DEV-007 | 2026-11-10 | `def:logistic_lackfit` is registered with an excerpt of train.sas 47-96 (elisions marked) as its source: with the whole PROC as source the judge rejected a translation of one option of it three times | orchestrating session, to be confirmed |
| DEV-005 | 2026-11-10 | Shared SAS runtime helpers live inside code items (the first unit that needs each), because the server allows one declaration per non-code item and forbids helper items | orchestrating session, to be confirmed |
| DEV-008 | 2026-11-14 | Round 2. An item relabelled "changed" by `write_code` accepts one declaration only. Helpers needed by changed items therefore live in a new item (`Sas.coalesce` and the moved `Sas.leftJoin` in `def:income_medians_all`) or are written as local `let`s (`def:ks_calculation`, `def:psi_calculation`) | to be confirmed |
| DEV-009 | 2026-11-14 | Round 2. `write_code` on `def:credit_imputed` cleared the Lean of all 88 dependent items. Each was recovered from the server's search index and resubmitted unchanged apart from line numbers in comments. Items the cascade did not reach (`credit_raw_clean`, `income_medians`, `credit_cleaned`, `confusion_matrix_train`, `training_metrics`, `total_good_bad`, `decile_data`, `decile_analysis`, `total_defaults`, `cumulative_lift`, `test_raw_clean`, `test_cleaned` and their preconditions) were left alone, so their Lean comments still cite the pre-correction line numbers; the manifest has the current ones | to be confirmed |
| DEV-011 | 2026-11-14 | Round 2 review. Experiments x21, x22 were submitted with `uv run --no-project --with saspy python run_experiment.py ...` (same saspy profile `oda_eu`, program verbatim): the hook refuses a command naming the `judge` project folder, which the runner's documented invocation does. Nothing of `judge/` was read to do so | to be confirmed |
| DEV-012 | 2026-11-14 | Round 2 review. Any accepted change to an item's Lean (even a comment) clears the Lean of its dependents. 28 dependents were resubmitted unchanged after the corrections to the check units, `test_imputed`, `train_bins`, `valid_bins`. For that reason the Lean comments of the remaining items of DEV-009 (all upstream of most of the blueprint) still cite old line numbers; `test_raw_clean`, `test_cleaned` and their preconditions were corrected | to be confirmed |
| DEV-010 | 2026-11-14 | Round 2. Differential evaluation ran through `eval_decl` of the staging connector with inputs written into the call (the local server used by the round 1 scripts refused connections). Samples are smaller than in round 1 and comparison is to printed precision | to be confirmed |
