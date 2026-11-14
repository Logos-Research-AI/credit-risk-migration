# Review 2: feature_engineering.sas and predict.sas unit bodies, line against line

Reviewer angle: unit bodies and preconditions (runtime helpers are the other reviewer's).
Read-only. Blueprint `sas-credit-risk-spec`. All 18 units are `DefinitionFormalized`.

Method: SAS source (`get_items.code` and the `.sas` files) ticked statement by statement against
the accepted Lean; `eval_decl` with `(α := Float)` on real rows of `data/cs-training.csv`,
`judge/scenarios/edge_predict/cs-test.csv`, and on synthetic boundary rows; results compared with
`judge/reference/` and `judge/reference/scenarios/edge_predict/`.

## Counts

| Severity | Count |
|---|---|
| WRONG | 1 |
| OMITTED | 0 |
| EXTRA | 1 |
| UNSTATED-ASSUMPTION | 5 |
| STYLE (hides meaning) | 1 |
| UNSETTLED | 1 |

No unit body differs from its SAS statements on any threshold, comparison direction, branch
order, argument order, arithmetic grouping, or column order. All findings are about the domain
(preconditions) or about material outside the unit bodies.

## Findings

### F1. WRONG: `test_raw_clean`, `credit_raw_clean` (via `Sas.inputBest`): the informat width 32 is ignored

- SAS: `MonthlyIncome_num = input(MonthlyIncome, best32.);` (predict.sas 49-50, feature_engineering.sas 49-50).
  `BEST32.` reads the first 32 characters only.
- Lean: `Sas.inputBest (Sas.chr r "MonthlyIncome")` parses the whole string.
- Input: `MonthlyIncome = "1234567890123456789012345678901234567"` (37 digits). It satisfies
  `test_raw_clean_precond` (text cell, none of e/E/d/D).
  - SAS: `12345678901234566802609541218304` (experiments/x06_printing.log line 22, `X06 input32`).
  - Lean (`eval_decl` on `Sas.inputBest`): `1234567890123456841093504014485553152`. On the first 32
    characters Lean gives exactly SAS's value `12345678901234566802609541218304`.
- Real data are not affected (longest value is 7 characters). Fix is either truncation to 32
  characters in the helper or a length bound in the two preconditions.
- Evidence: X06. Rule R9 says nothing about the width.

### F2. UNSTATED-ASSUMPTION: `credit_raw_clean` has no precondition item

- `def:credit_raw_clean_precond` does not exist; `def:test_raw_clean_precond` does. The helper's
  own comment says "the precondition of each unit using this excludes it" (exponent notation), and
  inventory rows feature_engineering.sas 49 and 50 say "precondition: text column, no exponent notation".
- Inputs on which the Lean is not faithful and nothing excludes them:
  - `MonthlyIncome = "1e3"`: Lean `none`; SAS reads exponent notation (acknowledged in the helper comment).
  - `MonthlyIncome` a numeric cell `Cell.num (some 5000)` (what PROC IMPORT yields for a file with
    no `NA`): Lean gives missing (`eval_decl`, chain on `def:credit_features`, row 4: monthly_income
    `none`, MonthlyIncome_missing 1). SAS converts the number to text and reads it back; the exact
    result is UNSETTLED in `experiments/`, but it is not missing.

### F3. UNSTATED-ASSUMPTION: `credit_imputed` has no precondition item for `arrange`

- Lean comment: "`arrange` is that rearrangement; the precondition states it is a permutation."
  No `def:credit_imputed_precond` exists (`def:test_imputed_precond` does, with `∀ t, List.Perm (arrange t) t`).
- Input: `arrange := fun _ => []`. Lean: empty table. SAS: one row per left row.
- Rule: RULEBOOK section 4 P1, section 3 (preconditions).

### F4. UNSTATED-ASSUMPTION: `credit_imputed`, `test_imputed`: source columns assumed numeric

- SAS: `a.VAR1 as row_id, a.SeriousDlqin2yrs as default_flag, ..., a.NumberOfTimes90DaysLate as num_late_90_plus, ...`
- Lean: every select item is `Cell.num (Sas.num a "...")`, which turns a text cell or an absent
  column into numeric missing.
- Input: `NumberOfTimes90DaysLate = Cell.str (some "3")` (what PROC IMPORT gives if the column
  contains `NA`). Lean: `num_late_90_plus` numeric missing. SAS: a character column holding `3`.
- `test_imputed_precond` constrains `arrange` only; nothing states that VAR1, the three
  delinquency counts, RevolvingUtilizationOfUnsecuredL, DebtRatio, NumberOfOpenCreditLinesAndLoans,
  NumberRealEstateLoansOrLines (and SeriousDlqin2yrs for training) are numeric cells, nor that
  `income_medians` has numeric `age_group` and `median_income`.
- Real data satisfy the assumption (reference logs: all `best32.`; training `SeriousDlqin2yrs best32.`).
  `test_imputed` does not read `SeriousDlqin2yrs`, so the all-blank `$1.` column in the test
  data is harmless.

### F5. UNSTATED-ASSUMPTION: `credit_train_validation`: the variable is read as `"Selected"`, no precondition

- SAS: `if selected = 1 then output work.credit_train; ... drop selected;` (names are case-insensitive).
- Lean: `Sas.num r "Selected"`, `Sas.drop ["Selected"]`.
- Input: a row `[("selected", num 1), ("row_id", num 5)]`. Lean (`eval_decl`): the row goes to
  credit_validation and keeps the column `selected`. SAS: credit_train, column dropped.
- No `def:credit_train_validation_precond` states that `credit_split` carries a numeric column
  spelled `Selected`. Evidence for the spelling itself: only the reference CSV header (the column
  is absent after the drop), so the stored case is not shown anywhere in `experiments/`.

### F6. UNSTATED-ASSUMPTION: `income_medians`, `credit_cleaned` lack the preconditions their predict twins have

- `def:test_income_medians_precond` (age, MonthlyIncome numeric cells) and
  `def:test_cleaned_precond` (age, MonthlyIncome, NumberOfDependents numeric cells) exist; the
  feature_engineering twins have none, with identical Lean bodies.
- Input: `age = Cell.str (some "45")`. Lean: `Sas.num` gives missing, so age_group 1. SAS:
  character-to-numeric conversion gives 45, age_group 3.

### F7. EXTRA: evaluation-harness definitions inside unit items

- `Sas.Eval.apply` at the end of namespace `Sas` in `def:credit_raw_clean`, and
  `test_predictions_full.evalApply` in `def:test_predictions_full`. Both are `f x`, are commented
  "Evaluation harness only (no SAS meaning)", and correspond to no SAS statement.
- They change no result. RULEBOOK section 3 allows helpers that "state a SAS rule" or belong to the unit; these do neither.

### F8. STYLE (hides meaning): `kaggle_submission_precond` text contradicts its Lean

- Text: "each holding an actual numeric value rather than a missing or text entry."
- Lean: `∃ v, r.get "pd_logistic" = some (Cell.num v)` with `v : Option α`, so a missing value is allowed.
- The Lean is the right one: in `judge/reference/scenarios/edge_predict/kaggle_submission.csv`
  pd_logistic is blank for the under-30 rows. Read literally, the text would exclude the real edge data.
- Milder version of the same wording in `test_features_precond` ("present with a numeric value").

### F9. UNSETTLED: `test_raw_clean_precond` excludes only the letters e, E, d, D

- Whether `BEST32.` reads a text such as `"1-2"` or `"1+2"` as exponent notation without a letter
  is not settled by `experiments/` or `sas-docs.md`. Lean gives `none` for `"1-2"` (`eval_decl`).
  Not present in the real data.

## Per-unit checklist

Legend: each SAS statement, then the Lean fragment that carries it. All ticked unless a finding is cited.

### credit_raw_clean (feature_engineering.sas 44-56) and test_raw_clean (predict.sas 44-56)

| SAS | Lean | |
|---|---|---|
| `set` | `.map fun r` | ok |
| `MonthlyIncome_num = input(MonthlyIncome, best32.)` | `setNum r "MonthlyIncome_num" (inputBest (chr r "MonthlyIncome"))` | ok, F1 |
| `NumberOfDependents_num = input(NumberOfDependents, best32.)` | same pattern | ok, F1 |
| `drop MonthlyIncome NumberOfDependents` | `Sas.drop [...]` before the renames | ok |
| `rename ..._num = ...` (two) | two `Sas.rename` | ok |

Column order: the two numeric columns end up last, as in SAS. The twin is written out again, not
called. Preconditions: F2 (training side missing). `test_raw_clean_precond` holds on both real
test files (MonthlyIncome `$7.`, NumberOfDependents `$2.`, only non-numeric text is `NA`); it does
not mention `SeriousDlqin2yrs`.

### income_medians (58-73) and test_income_medians (58-73)

| SAS | Lean | |
|---|---|---|
| `where MonthlyIncome is not missing` | `filter (!isMissing (num r "MonthlyIncome"))`, applied before grouping | ok |
| `case when age < 30 then 1 / < 40 then 2 / < 50 then 3 / < 60 then 4 / else 5` | `ageGroup`: `lt` 30, 40, 50, 60, else 5, same order | ok |
| `group by calculated age_group` | `groupKeys (rows.map ageGroup)` | ok |
| `median(MonthlyIncome)` | `sqlMedian` over the group's rows | ok |

Columns `age_group`, `median_income` in that order. Zero rows give zero rows. `eval_decl`: group
{9120, 2600} gives 5860 = lo + (hi - lo) / 2. Twin has its own `test_income_medians.ageGroup`. F6.

### credit_cleaned (75-94) and test_cleaned (75-94)

| SAS | Lean | |
|---|---|---|
| `if age < 30 ... 1; < 40 ... 2; < 50 ... 3; < 60 ... 4; else 5` | same chain, every branch assigns | ok |
| `if missing(MonthlyIncome) then MonthlyIncome_missing = 1; else ... = 0` | ok | ok |
| `if missing(NumberOfDependents) then do; NumberOfDependents = 0; Dependents_missing = 1; end; else Dependents_missing = 0` | in-place set then flag; else flag 0 | ok |

New-variable order age_group, MonthlyIncome_missing, Dependents_missing. `eval_decl`: missing age
gives age_group 1; `NA` dependents give 0 and flag 1. F6 (training side).

### credit_imputed (96-120) and test_imputed (96-119)

SELECT list, name by name and in order:

| # | SAS | Lean | |
|---|---|---|---|
| 1 | `a.VAR1 as row_id` | `("row_id", num a "VAR1")` | ok |
| 2 | `a.SeriousDlqin2yrs as default_flag` (training only) | present in `credit_imputed`, absent in `test_imputed` | ok |
| 3 | `a.age` | `"age"` | ok |
| 4 | `case when a.MonthlyIncome_missing = 1 then b.median_income else a.MonthlyIncome end as monthly_income` | `if eq (num a "MonthlyIncome_missing") (some 1) then num b "median_income" else num a "MonthlyIncome"` | ok |
| 5 | `a.MonthlyIncome_missing` | ok | ok |
| 6 | `a.NumberOfDependents as num_dependents` | ok | ok |
| 7 | `a.Dependents_missing` | ok | ok |
| 8 | `a.age_group` | ok | ok |
| 9 | `a."NumberOfTime30-59DaysPastDueNotW"n as num_late_30_59` | exact 32-character name | ok |
| 10 | `a."NumberOfTime60-89DaysPastDueNotW"n as num_late_60_89` | exact 32-character name | ok |
| 11 | `a.NumberOfTimes90DaysLate as num_late_90_plus` | ok | ok |
| 12 | `a.RevolvingUtilizationOfUnsecuredL * 100 as credit_utilization` | `mul (num a "RevolvingUtilizationOfUnsecuredL") (some 100)` | ok |
| 13 | `a.DebtRatio * 100 as debt_ratio` | `mul (num a "DebtRatio") (some 100)` | ok |
| 14 | `a.NumberOfOpenCreditLinesAndLoans as num_credit_lines` | ok | ok |
| 15 | `a.NumberRealEstateLoansOrLines as num_real_estate_loans` | ok | ok |

`left join ... on a.age_group = b.age_group`: `Sas.leftJoin` with `Sas.eq`; an unmatched left row
gets `b = []`, so `median_income` reads missing. Order matches the first 15 header fields of
`judge/reference/model_features_train.csv`. Row order is the parameter `arrange` (P1). F3, F4.

Edge pattern (`eval_decl`, chain from raw rows 5 and 10 of the edge `cs-test.csv`, age 27 and 23,
MonthlyIncome `NA`, no income present in age group 1): monthly_income missing, as in the reference.

### credit_features (126-202) and test_features (125-201)

Both Lean bodies were ticked separately against their own lines; they agree with each other and with the SAS.

| SAS line (fe / predict) | Statement | Lean | |
|---|---|---|---|
| 130 / 129 | `sum(num_late_30_59, num_late_60_89, num_late_90_plus)` | `sumFn [30_59, 60_89, 90_plus]` | ok |
| 133 / 132 | `(total_late_payments > 0)` | `ofBool (gt . (some 0))` | ok |
| 136 / 135 | `(num_late_90_plus > 0)` | ok | ok |
| 139-142 / 138-141 | credit_utilization `< 30`, `< 50`, `< 75`, else: 1, 2, 3, 4 | `lt` 30, 50, 75 | ok |
| 145-148 / 144-147 | debt_ratio `< 30`, `< 43`, `< 60`, else: 1, 2, 3, 4 | `lt` 30, 43, 60 | ok |
| 151-152 / 150-151 | `if num_dependents > 0 then monthly_income / (num_dependents + 1); else monthly_income` | `gt . 0`; `div mi (add nd (some 1))`; else `mi` | ok |
| 155 / 154 | `num_credit_lines / (num_dependents + 1)` | `div ncl (add nd (some 1))` | ok |
| 158-162 / 157-161 | age `< 25`, `< 35`, `< 50`, `< 65`, else: 1..5 | `lt` 25, 35, 50, 65 | ok |
| 165 / 164 | `(credit_utilization > 75)` | `gt . 75` | ok |
| 166 / 165 | `(credit_utilization > 100)` | `gt . 100` | ok |
| 167 / 166 | `(debt_ratio > 43)` | `gt . 43` | ok |
| 168 / 167 | `(debt_ratio > 60)` | `gt . 60` | ok |
| 169 / 168 | `(num_late_30_59 > 0)` | `gt . 0` | ok |
| 170 / 169 | `(num_late_90_plus > 0)` | `gt . 0` | ok |
| 171 / 170 | `(total_late_payments >= 3)` | `ge . 3` | ok |
| 172 / 171 | `(monthly_income < 2500)` | `lt . 2500` | ok |
| 173 / 172 | `(num_dependents >= 3)` | `ge . 3` | ok |
| 174 / 173 | `(num_credit_lines <= 2)` | `le . 2` | ok |
| 177-179 / 176-178 | `sum(flag_high_utilization, flag_high_debt_ratio, flag_serious_delinquency, flag_multiple_delinquencies, flag_low_income)` | same five, same order | ok |
| 182 / 181 | `financial_health = 100` | ok | ok |
| 183 / 182 | `if credit_utilization > 30 then ... - 15` | 1st update, `gt . 30`, `sub fh 15` | ok |
| 184 / 183 | `if credit_utilization > 75 then ... - 15` | 2nd, `gt . 75`, 15 | ok |
| 185 / 184 | `if debt_ratio > 43 then ... - 20` | 3rd, `gt . 43`, 20 | ok |
| 186 / 185 | `if has_delinquency then ... - 20` | 4th, `truthy`, 20 | ok |
| 187 / 186 | `if num_late_90_plus > 0 then ... - 30` | 5th, `gt . 0`, 30 | ok |
| 188 / 187 | `max(0, financial_health)` | `maxFn [some 0, fh]` | ok |
| 191 / 190 | `log(monthly_income + 1)` | `log (add mi (some 1))` | ok |
| 192 / 191 | `log(num_credit_lines + 1)` | ok | ok |
| 193 / 192 | `log(total_late_payments + 1)` | ok | ok |
| 196 / 195 | `age * log_monthly_income` | `mul age lmi` | ok |
| 197 / 196 | `credit_utilization * debt_ratio / 100` | `div (mul cu dr) (some 100)` | ok |
| 200 / 199 | `min(credit_utilization, 200)` | `minFn [cu, some 200]` | ok |
| 201 / 200 | `min(debt_ratio, 500)` | `minFn [dr, some 500]` | ok |

The 27 new columns come out in the order of header fields 16-42 of `model_features_train.csv`.

`eval_decl` checks:
- Training rows 1 and 2 through the whole chain: every one of the 42 values agrees with the
  reference rows (`1,1,45,9120,...,30,9.1183347262,...,61.518597558,...` and row 2) to the printed digits.
- Boundary row (age 25, income 2500, dependents 3, cu 75, dr 43, lines 2, late 1/1/1): categories 4, 3, 2;
  flags high_util 0, high_debt 0, multiple 1, low_income 0, many_dep 1, few_lines 1; health 35. As SAS.
- All-missing row: categories 1, 1, 1; flag_low_income 1; flag_few_credit_lines 1; total_risk_flags 1;
  health 100; caps 200 and 500 (min skips missing, X10); logs missing. As SAS per R3, R10, R11.
- Negative dependents (-1): credit_lines_per_person missing (division by zero), income_per_dependent = income.
- Zero rows give zero rows.

Preconditions: `credit_features_precond` and `test_features_precond` allow a missing value in each
input column (`v : Option α`), so the edge data are inside the domain. The second conjunct (the 27
output names absent) is stronger than needed (SAS also keeps an existing variable in place, and so
does `Row.set`) but holds on the real data; no finding.

### credit_train_validation (216-221)

| SAS | Lean | |
|---|---|---|
| `if selected = 1 then output work.credit_train` | `filter (eq (num r "Selected") (some 1))` | ok, F5 |
| `else output work.credit_validation` | `filter (!eq ...)` | ok |
| `drop selected` | `Sas.drop ["Selected"]` on both | ok |

`eval_decl`: Selected 1 to train; 0, missing and 2 to validation; order kept; empty input gives `([], [])`.

### credit_train_export, credit_validation_export

`set` plus `format _numeric_ best12.`: identity. No finding. Header of `model_features_train.csv`
equals the column order produced by the chain.

### test_scored_temp (207-212)

`score data=... out=... predicted=predicted_logit`: `setNum r "predicted_logit" (Sas.linpred model r)`,
appended last, every row kept. Precondition states exactly what `linpred` reads (model terms are
numeric cells, possibly missing). No finding on the unit body.

### test_scored (214-222)

| SAS | Lean | |
|---|---|---|
| `pd_logistic = 1 / (1 + exp(-predicted_logit))` | `div (some 1) (add (some 1) (exp (neg (num r "predicted_logit"))))` | ok |
| `drop predicted_logit` | `Sas.drop ["predicted_logit"]` | ok |

No finding.

### test_predictions (228-262)

| SAS line | Statement | Lean | |
|---|---|---|---|
| 232 | `(pd_logistic >= 0.5)` | `ofBool (ge pd (some 0.5))` | ok |
| 235-236 | `base_score = 600; score_range = 250` | ok | ok |
| 237 | `round(base_score + score_range * (1 - pd_logistic))` | `round (add base (mul range (sub (some 1) pd)))` | ok |
| 240-245 | `>= 750 A, >= 700 B, >= 650 C, >= 600 D, >= 550 E, else F` | same order and constants | ok |
| 248-250 | `in ('A','B')` Approve; `= 'C'` Review; else Decline | ok | ok |
| 253 | `base_rate = 0.05` | ok | ok |
| 254-259 | A: base; B: + 0.02; C: + 0.04; D: + 0.07; E: + 0.10; else + 0.15 | `add base_rate (some ...)`, not folded | ok |

`eval_decl`: pd 0.4 gives 750 A 0.05; 0.5 gives pred 1, 725 B; 0.6 gives 700 B; 0.8 and 0.802 give
650 C Review 0.09; 1.3 gives 525 F; missing gives pred 0, score missing, F, Decline, 0.2;
0.4741467589 gives 731 B 0.07 (reference row 10: `731,B,Approve,7.00%`). No finding.

### kaggle_submission (268-272)

`keep row_id pd_logistic`: `Sas.keep`, order row_id, pd_logistic as in `kaggle_submission.csv`. F8 (text of the precondition).

### test_predictions_full (274-281)

The 15 KEEP names are all present in the Lean list; resulting order (from `eval_decl`) is
row_id, age, monthly_income, credit_utilization, debt_ratio, num_credit_lines, total_late_payments,
total_risk_flags, financial_health, pd_logistic, pred_logistic, credit_risk_score, risk_grade,
recommendation, interest_rate: identical to the header of `judge/reference/test_predictions.csv`. F7.

Edge scenario, whole chain from raw rows (model chosen by me, containing `log_monthly_income`):
- row 5 (age 27, income `NA`): monthly_income missing, total_risk_flags 2, financial_health 70,
  pd missing, pred 0, score missing, F, Decline, 0.2. Reference: `5,27,,99.99999,1.9917227,4,0,2,70,,0,,F,Decline,20.00%`.
- row 10 (age 23): total_late_payments 294, total_risk_flags 4, financial_health 20, pd missing, F.
  Reference: `10,23,,99.99999,0,0,294,4,20,,0,,F,Decline,20.00%`.
- rows 1, 2, 7, 22: every non-model column equals the reference row.

## Amendments proposed

- R9: state that `BEST32.` reads at most 32 characters (X06), and either truncate in `Sas.inputBest`
  or add the bound to the preconditions.
- Section 3: say whether evaluation-harness definitions may live in unit items (F7).
- Section 3: a precondition item should exist for every unit whose twin has one (F2, F3, F6).

## Note on the workspace instructions

`CLAUDE.md` lists `/Users/cristophersalvi/GitHub/sas-migration-formal/sas` (this workspace) among the
paths never to read; `migration/prompts/common.md` gives `.../sas-migration-formal/python` there.
I followed `common.md` and read nothing outside this workspace.
