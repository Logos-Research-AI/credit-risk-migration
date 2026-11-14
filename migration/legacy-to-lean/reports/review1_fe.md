# Adversarial review 1: feature_engineering.sas units

Reviewer: read-only. Blueprint `sas-credit-risk-spec`. Date 2026-11-10.
Units: `credit_raw_clean` (with runtime R1-R12), `income_medians` (R13-R15), `credit_cleaned`,
`credit_imputed` (R16, `arrange`), `credit_features`, `credit_train_validation`,
`credit_train_export`, `credit_validation_export`, `credit_features_precond`.

## Counts

| Severity | Count |
|---|---|
| WRONG | 1 |
| OMITTED | 2 |
| EXTRA | 1 |
| UNSTATED-ASSUMPTION | 4 |
| STYLE (hides meaning) | 1 |

Units with no fidelity finding of their own: `credit_cleaned`, `credit_features`,
`credit_train_export`, `credit_validation_export`, `credit_features_precond`, and the bodies of
`income_medians`, `credit_imputed`, `credit_train_validation` (their findings are missing
preconditions, not wrong logic).

## What was run

- Real rows through the Lean chain `credit_features (credit_imputed id (credit_cleaned
  (credit_raw_clean RAW)) MED)`, `α := Float`, on 235 rows of `data/cs-training.csv`
  (MonthlyIncome cut to 5 characters, NumberOfDependents to 2, as the reference log's `$5.` / `$2.`
  informats do), joined to `judge/reference/model_features_{train,validation}.csv` by `row_id`.
  `MED` is SAS's own five medians, read off the reference rows with `MonthlyIncome_missing = 1`
  (2557, 4666, 6000, 6333, 5313). The 235 rows are 85 chosen for oddity plus 150 random:
  row 65696 (age 0); six incomes of 100000 or more (208333 becomes text `20833`); the five largest
  utilizations (up to 50708) and debt ratios (up to 329664); zero income; `NA` dependents;
  dependents 10, 13, 20; late counts of 98; `NA` income with debt ratio above 3000; raw values in
  exponent notation; ages on every CASE boundary; income 2499/2500; credit lines 0, 2, 3.
  Result: all 42 columns in the reference order on every row; 9870 cells, 0 real mismatches.
  One cell (row 139388, `utilization_debt_interaction`, 23327.389407 against 23327.389408) is
  the evaluator's 6-decimal print falling on a rounding boundary; the bit-level check below
  passes on that row.
- Limit of that check: `eval_decl` prints a Float with 6 decimals and the result of
  `credit_features` cannot be post-processed (`Sas.Eval.apply` is not visible from that item), so
  1604 of the 9870 cells were compared more coarsely than BEST12. prints. To close the gap, the
  eleven fractional columns of the same 235 rows were recomputed from the `Sas` primitives, with
  the expression of the corresponding `credit_features` line, and read back as bits: 2438 cells,
  0 mismatches at the full printed precision. `Sas.inputBest` on the 235 income and dependents
  texts: 0 mismatches.
- `Sas.inputBest`, `Sas.mul`, `Sas.div` against the 40 rows of `x04_division_by_constant.log`:
  240 values equal bit for bit.
- `income_medians` on six random real subsets (300, 700, 1200 rows; groups of even and odd size,
  many duplicates): all medians equal the expected ones. On 2000 rows the evaluator stops with
  "maximum recursion depth has been reached", so the full 150000-row table was not evaluated in
  Lean; the five full-data medians were recomputed outside Lean and equal SAS's.
- Hand-built inputs: zero rows through every unit; an all-missing row, boundary values and
  overflow through `credit_features`; missing keys and duplicate right keys through
  `credit_imputed`; ten `Selected` variants through `credit_train_validation`; about 110 calls of
  the `Sas` helpers.

## Findings

### F1. WRONG: `Sas.inputBest` ignores the informat width (R9), `def:credit_raw_clean`

- SAS line: 49-50, `input(MonthlyIncome, best32.)`.
- Lean: `let cs := trimBlanks s.toList` reads the whole string.
- Input: `"1234567890123456789012345678901234567"` (37 digits).
- SAS: `12345678901234566802609541218304`, about 1.23e31: only the first 32 characters are read
  (`experiments/x06_printing.log` line 22, `X06 input32`).
- Lean: `some 1234567890123456841093504014485553152.0`, about 1.23e36 (`eval_decl`).
- The comment does not admit it and no precondition bounds the text length. It cannot occur
  when the column is `$5.` or `$2.` as in the reference run, but the imported table is a
  parameter and nothing states its width. The evidence the comment cites for this rule (X06) is
  the evidence against it.

### F2. OMITTED: the precondition of `credit_raw_clean` does not exist

- The Lean comment on `inputBest` says "Exponent notation is not modelled: the precondition of
  each unit using this excludes it". RULEBOOK R9 and inventory rows 49 and 50 say "precondition:
  text column, no exponent notation". There is no item `def:credit_raw_clean_precond`.
- Inputs on which nothing protects the Lean:
  - `"1E3"` (fits in `$5.`): Lean `none`. SAS: UNSETTLED in the workspace evidence (no
    experiment reads exponent text through `INPUT`); the inventory itself assumes SAS reads it
    as a number, which is why it asks for the precondition.
  - A numeric cell, `("MonthlyIncome", Cell.num (some 5000))`: `Sas.chr` returns `""`, Lean gives
    `MonthlyIncome = none`, and the row is later imputed with `MonthlyIncome_missing = 1`. SAS:
    UNSETTLED in the evidence (no experiment passes a numeric to `INPUT`). The source comments on
    lines 44, 48 and 52 ("if needed", "if they exist") show the author expected the column to be
    numeric sometimes.

### F3. OMITTED: the precondition of `credit_imputed` does not exist

- The Lean comment says "`arrange` is that rearrangement; the precondition states it is a
  permutation". There is no item `def:credit_imputed_precond`, so `arrange` is any function.
- Input: `arrange := fun _ => []` with four left rows. Lean: `[]`. SAS: one row per left row
  (`x13_freq_sql_merge.log`, `leftjoin` lines: 40 rows in, 40 out).
- A function that edits cells is equally allowed.

### F4. EXTRA: `Sas.Eval.apply` in `def:credit_raw_clean`

- `def Eval.apply {β γ : Type} (f : β → γ) (x : β) : γ := f x` has no SAS counterpart. The
  comment says so ("Evaluation harness only"). It is part of the accepted statement that the
  equivalence team will read, and RULEBOOK section 3 allows helpers only when they state a SAS
  rule or serve the unit.

### F5. UNSTATED-ASSUMPTION: every numeric cell is a finite number (all units; attack 4)

- `Tabular.RealLike` carries no laws (foundation Definition 1). `Sas.lt` uses `<`, `Sas.le` uses
  `≤`, `Sas.eq` and `Sas.truthy` and the zero test of `Sas.div` use `eqb` (`x ≤ y ∧ y ≤ x`),
  `Sas.minFn`/`maxFn` use `<`, `Sas.sortBy` uses `≤`. SAS has one total order with missing
  lowest, so in SAS `a <= b` is `not (b < a)` and `a = a` always holds. In the Lean these hold
  only when the order on α is total and consistent.
- On `ℝ` and on finite `Float` values they do hold; I found no misbehaviour there (signed zero:
  `Sas.eq (some 0.0) (some (-0.0))` is true, division by `-0.0` gives missing).
- Input where they fail: a cell `some NaN`. `eval_decl`: `Sas.eq NaN NaN = false`,
  `Sas.lt NaN 1 = false`, `Sas.le NaN 1 = false`, `Sas.ge NaN 1 = false`, `Sas.truthy NaN = true`.
  So `credit_utilization = some NaN` gives `credit_util_category = 4`, and
  `credit_utilization_capped = NaN`. SAS has no such value; the nearest thing it can hold is
  missing, which gives category 1 and cap 200.
- `Sas.fin` keeps NaN and infinity out of every computed result, so the only way in is an input
  cell. No comment admits this and no precondition (including `credit_features_precond`) says
  the input cells are finite.

### F6. UNSTATED-ASSUMPTION: column presence, type and name for five units

Only `credit_features` has a precondition. The other units assume the same things silently.

- `credit_train_validation` (attack 5). On a numeric `Selected` the Lean equals SAS for every
  value tried: 1 goes to train; 0, 2, -1, 1.0000000001 and missing go to validation; order kept;
  `Selected` dropped; zero rows give `([], [])`. But:
  - `("selected", Cell.num (some 1))` (lower case): Lean sends the row to validation and keeps the
    column `selected`. SAS names are case-insensitive: train, column dropped.
  - `("Selected", Cell.str (some "1"))`: Lean sends it to validation. SAS: UNSETTLED in the
    evidence (character-to-numeric conversion in a comparison is not probed).
  - Column absent: Lean validation. SAS: `selected` uninitialized, missing, validation. Same.
- `credit_cleaned`: a row without `age`. Lean adds no `age` column. SAS creates `age` at its
  first reference on line 79, before `age_group`, so the column order differs.
- `income_medians`, `credit_imputed`: read every column with `Sas.num`, which turns a text cell
  or an absent column into missing.

### F7. UNSTATED-ASSUMPTION: overflow inside `SUM` and inside the SQL median (R10, R15)

- `Sas.sumFn [some 1e308, some 1e308, some (-1e308)]` is `none` in Lean: the fold reaches
  infinity and `fin` is applied once at the end. `Sas.sumFn [some 1e308, some 1e308]` is `none`.
- `Sas.sqlMedian [some 1e308, some (-1e308)]` is `none` in Lean, because `hi - lo` overflows.
- SAS: UNSETTLED. X10 shows overflow of `+ - * /` and `EXP` giving missing, not of the `SUM`
  function nor of the SQL aggregate. X14 has no overflow case.
- Not reachable from this script's data (counts and flags; incomes below 100000).

### F8. UNSTATED-ASSUMPTION: texts on which `INPUT(…, BEST32.)` is unverified (attack 1)

Evidence covers four behaviours only: `NA` gives missing (reference log), leading blanks are
skipped and 32 characters are read (X06), decimal text is the nearest binary64 (X04; reproduced
bit for bit on 80 texts). The Lean also decides the following, with no evidence either way.
Each fits in a `$5.` field.

| Text | Lean | SAS |
|---|---|---|
| `-`, `+` | missing | UNSETTLED |
| `-0` | `some -0.0` (negative zero) | UNSETTLED |
| `1-3`, `1+3`, `1D3`, `1E3` | missing | UNSETTLED (exponent forms) |
| `.A`, `._` | missing | UNSETTLED (special missing values; R1 has only one missing) |
| `1,000`, `1 2`, `- 5`, `0x1F`, tab then `5` | missing | UNSETTLED |

Settled and equal: `""`, `"."`, `" . "`, `"NA"`, `"5."`, `".5"`, `"-.5"`, `"+7"`, `"00012"`,
`"   12.5"`.

### F9. STYLE (hides meaning): rule numbers in `def:credit_raw_clean` do not match the RULEBOOK

- The Lean comments number the rules R1-R6, then "R7" for variable access (RULEBOOK R8), "R8"
  for `INPUT` (R9), "R9" for `SUM` (R10), "R10" for `MIN`/`MAX` (R11). `LOG`/`EXP`/`ABS`
  (RULEBOOK R7) sit under the R6 heading and R12 has no label.
- `def:credit_features` cites the RULEBOOK numbering ("SUM/MIN/MAX R10/R11, LOG and division
  R6/R7"). A reader following "R10" from `credit_features` into the home item lands on the
  wrong rule.

## Attacks requested: results

1. `Sas.inputBest` on odd strings: F1 (WRONG), F2, F8.
2. `Sas.sqlMedian`: no finding on even counts or duplicates. `[7,5]` gives 6, `[5,5]` gives 5,
   `[5,5,7,7]` gives 6, `[1,2,2,2,9,9]` gives 2, `[3,1,.,8,5]` gives 4, `[]` and `[.,.]` give
   missing. `{1016.85, 7098.24}` gives `40AFB3170A3D70A3`, equal to X14 bit for bit. I checked
   the other candidate formulas (`(lo+hi)/2`, `lo/2+hi/2`, `hi-(hi-lo)/2`): all give
   `…70A4`, so X14 does single out `lo + (hi - lo) / 2`. That is one data point. Overflow: F7.
3. `minFn`/`maxFn`/`sumFn` with missing in every position: no finding. `min(.,200)`,
   `min(200,.)`, `max(0,.)`, `max(.,0)`, `max(.,-5)` and all-missing behave as D3 states
   ("only if all arguments are missing"); `sum` with the missing argument first, middle and last
   gives the same value; left-to-right order equals X14 on its three cases. X10 probes only
   one position for each of `MIN` and `MAX`; the other position rests on D3. Signed zero:
   `maxFn [-0.0, 0.0]` returns `-0.0` (the first argument); SAS UNSETTLED, no effect here.
4. `Sas.eq`/`lt` on a generic number type: F5.
5. `credit_train_validation` on other `Selected` values: no finding for numeric values; F6 for
   name and type.
6. Missing inputs: no difference found. An all-missing row through `credit_features` gives
   `total_late_payments` missing, both category variables 1, `age_category` 1,
   `flag_low_income` 1, `flag_few_credit_lines` 1, `total_risk_flags` 1, `financial_health` 100,
   the logs and interactions missing, caps 200 and 500: each as R3, R10, R11 and X10 predict.
   A missing `age` gets `age_group` 1 in both `income_medians` and `credit_cleaned`. A missing
   `age_group` key matches a missing key in the right table (R16, X13 `join` lines). A missing
   `MonthlyIncome_missing` takes the ELSE branch.

## Line-by-line result per unit

- `credit_raw_clean` (44-56): two assignments in order, appended; drop; two renames; output
  order equals the reference-derived order. Findings F1, F2, F4, F9.
- R1-R12 against evidence: R2 (X10 `o1 o2 o3 o7 o8` missing, `o6` missing: reproduced), R3 (X10
  `cmp` line: reproduced, including `. > .` false), R4, R5 (X10 `truth_*`: reproduced), R6 (X10
  `arith`, X04: reproduced), R7 (X10 `log`, `overflow`, `abs`: reproduced), R10 (X10, X14:
  reproduced), R11 (X10, D3). R8 and R12 by reading. R9: F1, F8.
- `income_medians` (58-73): WHERE before grouping, CASE constants 30/40/50/60 in order, one row
  per key ascending, columns `age_group`, `median_income`; zero rows give zero rows. R13-R15
  agree with X13 (`sqlgrp` lines) and X14. No finding beyond F6, F7.
- `credit_cleaned` (75-94): chain constants and order, both flags, the DO block's two
  assignments in order, new columns in order of appearance. No finding beyond F6.
- `credit_imputed` (96-120): 15 columns in SELECT order, CASE on `MonthlyIncome_missing = 1`,
  `* 100` as written, unmatched left rows kept with a missing median, duplicate right keys
  duplicate the left row. Findings F3, F6.
- `credit_features` (126-202): every assignment present and in source order; every comparison
  direction and constant checked against the source (30/50/75; 30/43/60; 25/35/50/65; 75, 100,
  43, 60, 0, 0, 3, 2500, 3, 2; 15, 15, 20, 20, 30); `sum` argument order; `max(0, …)`;
  `min(…, 200)`, `min(…, 500)`; grouping of `credit_utilization * debt_ratio / 100`. No finding.
- `credit_features_precond`: nine input columns and 27 output columns, both lists complete. It
  does not state finiteness (F5). No other finding.
- `credit_train_validation` (216-221): F6 only.
- `credit_train_export`, `credit_validation_export` (253-264): identity; FORMAT changes no
  value. No finding.

## Amendments proposed (RULEBOOK is read-only)

1. R9: state that only the first 32 characters are read (X06), or require a precondition on the
   text length; list which texts are evidenced and which are not (F8).
2. Section 3: a precondition that a Lean comment or an inventory row refers to must exist as an
   item. Today two comments point at preconditions that were never added (F2, F3).
3. Section 3 or R3: a standing precondition that input numeric cells are finite, with the
   reason (F5).
4. R11: cite D3 as well as X10. The header of `x14_sum_median.sas` announces MIN/MAX but the
   program contains none.
5. One further experiment would settle F7 and F8: `INPUT` of the texts in the F8 table and of a
   numeric argument; `SUM(1e308, 1e308, -1e308)`; SQL `MEDIAN` of `{1e308, -1e308}`;
   `selected = 1` with a character `selected`.
6. Tooling, not a rule: `eval_decl` fails on `income_medians` at 2000 rows (recursion depth)
   and prints Floats with 6 decimals; a bit-exact view of a unit's result is only possible from
   `def:credit_raw_clean`.

## Note on instructions

The project `CLAUDE.md` lists this workspace's own path among the folders never to read;
`migration/prompts/common.md` gives `.../sas-migration-formal/python` instead. I followed
`common.md`. I read nothing outside this workspace and opened no other blueprint.
