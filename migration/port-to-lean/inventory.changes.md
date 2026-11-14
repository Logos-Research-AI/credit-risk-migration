# inventory.tsv — change log (2026-11-10, bookkeeping pass after 146/146 items formalized)

`migration/inventory.tsv` was aligned with the ACCEPTED Lean of the blueprint `py-credit-risk-port` (read with `get_items`, field `statement_lean`, for every unit, step and precondition item except the polars prelude `def:ExprOrNum`, which exceeds the response limit of `get_items`) and with `migration/RULEBOOK.md` version 3. Only the columns `target_translation` and `status` were edited; the notes line, the header, the row order and the columns `file`, `symbol`, `source_construct`, `classification`, `evidence` are unchanged. Row numbers below are line numbers of the file (the first data row is line 3).

## Totals

- data rows: 1383; rows changed: **296** (all 296 have a new `target_translation`; 11 of them also changed `status` from `unknown` to `confirmed`); rows untouched: 1087 (their text was checked against the accepted Lean and kept).
- status after the pass: `confirmed` 1383, `unknown` **0**.
- rows changed per file: feature_engineering.py 17, metrics_calculation.py 56, predict.py 29, sas_compat.py 110, train.py 84.

## Rows changed per reason

A row is counted under every reason that applied to it, so the counts add up to more than the number of rows changed.

| Reason | Rows | Line numbers |
|---|---|---|
| text aligned with the accepted Lean (names, shapes, int literal as `Pl.ofInt`, helper names, where the precondition is stated and what it states) | 121 | 6-7, 42, 81, 146, 154, 219, 261, 348, 362, 373-374, 380-381, 403, 405-406, 423, 451, 515, 563, 569, 574-575, 607, 611, 615, 625, 628-630, 638-641, 645-646, 673, 696, 699-700, 702, 705-707, 715-716, 724, 726, 732, 734, 736, 742, 744, 749-751, 760-761, 763-764, 780-782, 822, 833-835, 837-838, 849-850, 864-865, 872-873, 883, 906, 910-914, 921, 929-930, 932, 935, 939-940, 942-943, 945-951, 955, 957-958, 966, 981, 983, 998, 1022, 1026, 1064, 1097, 1099, 1121, 1124, 1127, 1133, 1151, 1162, 1165, 1168, 1171, 1352 |
| precondition moved from the `run` precondition to the step precondition `def:<step>_precond` (RULEBOOK §2.6 split, §4, B12) | 85 | 5, 8, 10, 27, 43, 61, 83, 125, 196-197, 204, 215, 236, 245-246, 252, 269, 284, 288-291, 293, 318, 320, 323, 325, 330, 339, 341, 349, 361, 366, 379, 382, 386, 400, 402, 404, 407-408, 424, 431, 453, 502, 516, 518, 521, 962, 972, 975, 1000, 1007, 1013, 1032-1035, 1051, 1053, 1058, 1061, 1065-1066, 1088, 1090-1091, 1093, 1095, 1101, 1103, 1105, 1115-1117, 1148, 1153, 1155, 1207, 1243, 1261, 1340-1341, 1343-1344 |
| A3 litNull: `.then(None)` / `.otherwise(None)` / missing otherwise is `Pl.litNull`, not `Pl.litOptF none` | 32 | 175-176, 178-179, 181-182, 184-185, 190, 634, 636, 653-654, 659, 677, 682, 687, 692, 1226-1227, 1229-1230, 1232-1233, 1238, 1280-1281, 1283-1284, 1286-1287, 1292 |
| A12 / B11 rule now in RULEBOOK §2.3-§2.4 (itemI / itemS / firstName, takeRows, ndarray.mean, column_stack, .T, pl.col(*names), drop_nulls, Series cast) | 15 | 212, 214, 235, 317, 369, 915, 963, 967, 978, 997, 1015-1018, 1062 |
| A13 / §2.3 `full` only for the 5-operand sum; 2-operand reductions pass the literal `true` | 13 | 59, 117, 127, 129, 322, 324, 429, 493, 504, 506, 533, 667-668 |
| A11 LinAlgError (total parameter, OPEN) / union-typed `fit` and return sum type / unused flag | 12 | 4, 195, 805, 902-905, 916, 1021, 1025, 1339, 1342 |
| row was `unknown`, now `confirmed` with its resolution | 11 | 4, 401, 561, 619, 875, 877, 902, 916, 1021, 1025, 1094 |
| A7 R-DIV0: zero divisor handled inside `div` (`div_run`), no call-site precondition | 8 | 224, 226, 263, 265, 281, 283, 619-620 |
| claim that was false or is now a recorded limit corrected (B5, B10, B13, review notes) | 5 | 697, 701, 745, 788, 919 |
| A8 `** 2` is the explicit parameter `pow2` | 3 | 875, 877, 1094 |
| A10 `medians : Option (Pl.Frame α)` | 1 | 401 |

## Rows that were `unknown` (11 rows, 7 questions): all `confirmed`

| Line | Site | Resolution | Amendment |
|---|---|---|---|
| 4 | feature_engineering.py L31:28#1 | unused `fix_income_truncation : Bool` kept in `def:run` | A11 |
| 401 | predict.py L69:33#1 | `medians : Option (Pl.Frame α)`, the frame as read (`age_group` `.int`, `median_income` `.f64`) | A10 |
| 561 | sas_compat.py L41:0#1 | `FloatArray_ α` is an alias of `Np.NDArray α` (`.d1` / `.d2`), one type for both ranks | no amendment row names it; settled by RULEBOOK §2.1 and the accepted prelude (nearest: A12) |
| 619 | sas_compat.py L138:30#1 | zero divisor: rule R-DIV0 inside `div_run`, no precondition | A7 |
| 875 | sas_compat.py L1022:69#1 | `pow2 (o1 - e1)`, explicit parameter `pow2`; overflow in `def:hosmer_lemeshow_precond` | A8 |
| 877 | sas_compat.py L1022:91#1 | `pow2 (o0 - e0)`, same | A8 |
| 902 | sas_compat.py L1067:7#1 | dispatch translated literally (`classification_table_dispatch`, `fit : Option (LogisticFit α ⊕ FloatArray_ α)`) | A11 |
| 916 | sas_compat.py L1080:22#1 | `inv` total; LinAlgError outside the model, listed `OPEN(port)` in the trailer | A11 |
| 1021 | train.py L191:37#1 | `solve` total; LinAlgError outside the model, listed `OPEN(port)` in the trailer | A11 |
| 1025 | train.py L193:41#1 | same (`solve` on `cov[1:, 1:]`) | A11 |
| 1094 | train.py L312:17#1 | `wald_b := pow2 (b / se)`; overflow in `def:train_run_06_coefficients_odds_precond` | A8 |

## Rows still `unknown`

None. For lines 916, 1021 and 1025 the inventory question (how the `LinAlgError` raise is excluded) is answered by A11: it is not excluded, the parameter is total and the raise is outside the model. The matter itself remains an open item for the user, carried by the `-- OPEN(port): LinAlgError …` trailer lines of `def:classification_table`, `def:train_run_03_fit_global_rsquare` and `def:run_py_py_py`, not by an `unknown` inventory row.

## What was not verified

- The polars prelude `def:ExprOrNum` could not be read (39 kB, above the 30 kB limit of `get_items`; no other read tool was allowed). Rows that describe prelude behaviour (`Pl.wto`, `floatSum`, `groupMean`, `Frame.join`, `getF` on an integer column, …) were checked against RULEBOOK §2.3 / §6 and against the comments of the units that use them, not against the prelude text. The seven `[TO_LIST]` rows of train.py (lines 1124, 1127, 1133, 1162, 1165, 1168, 1171) say so explicitly ("per the unit's comment").
- The numpy prelude `def:FloatArray_` was read.
- No Python was run and no Lean was evaluated in this pass: it is a text alignment only.

