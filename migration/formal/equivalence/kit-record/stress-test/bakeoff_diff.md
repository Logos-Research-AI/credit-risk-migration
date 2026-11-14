# Bakeoff diff — rulebook translation (A) against native translation (B)

Diff inspector report, 2026-11-10. The rulebook is the defendant.

- Sources: `credit_risk/sas_compat.py` `lt` / `gt` / `flag` (87-124), `sas_round` (182-191);
  `credit_risk/metrics_calculation.py` `confusion_metrics` (24-78).
- A: the drafts of `def:_e`, `def:_named`, `def:lt`, `def:gt`, `def:flag`, `def:_TWO52`,
  `def:_ROUND_FUZZ`, `def:sas_round`, `def:confusion_metrics` (+ `def:confusion_metrics_precond`),
  written under RULEBOOK version 1. Five of them (`lt`, `gt`, `flag`, `sas_round`,
  `confusion_metrics`) are currently unformalized: the prelude change of amendment batch 1 cleared them.
- B: the native translation (row-wise, `Option α` values, `Table α` frames), never compiled.
- Python evidence: `uv run python migration/stress-test/bakeoff_probe.py` (P1–P7) and
  `bakeoff_probe2.py` (Q1–Q6), polars 2.1.0. Every Python value quoted below is from those runs.
- Lean evidence: one `eval_decl` run (L1, below) for `sas_round`. Everything else on the Lean side
  is **read from the text** of A, B and the prelude, not evaluated: two attempts to evaluate A's
  `confusion_metrics` inlined on the prelude did not elaborate, and B has no item to evaluate.

## Verdict counts

| Verdict | Rows | Count |
|---|---|---|
| rulebook right | D1, D3, D5, D6, D9, D11 | 6 |
| native right | — | 0 |
| both defensible | D4, D7, D8, D12, D13, D14, D15 | 7 |
| both wrong | D2, D10 | 2 |

No row came out "native right". The two places where the native version came closest: D2 (B is
right on a literal and on a 1-row frame, where version 1 of the rulebook was wrong) and D12 (B
reports a raise in-band, which can be tested by evaluation; the rulebook's precondition cannot).
Version 2 already fixes D2 and the `full` silence of D9. It does not address the silences behind
D8, D11 and D12 (proposals R1–R3).

## Differences

| # | Topic | A (rulebook) | B (native) | Rule indicted / silence | Verdict and evidence | Fixed in v2? |
|---|---|---|---|---|---|---|
| D1 | What an expression is | `def lt … (x : ExprOrNum α) (c : ExprOrNum α) : Pl.Expr α` (evaluation on a frame) | `def lt (x c : Option α) : Bool`; "a polars expression is modelled row-wise as its value on one row" | §2.1 `pl.Expr` → `Pl.Expr α` | **rulebook right.** Q6: `sas_round(pl.col("x"))` at x = -0.3 is `0.0` on a 1-row frame and `-0.0` on a 2- or 3-row frame; in a 3-row frame a group of size 1 still gives `-0.0`. The value depends on the column, so no function of one row's value can return it. | already right in v1 |
| D2 | `+ 0.0` at the end of `sas_round` | `_named x (Pl.wto (a.ge (Pl.litF _TWO52)) xf r)` with `-- + 0.0: polars returns the operand (E05)` | `(if geTot a two52 then xf else r) + 0` | §2.3 v1 row "`e + 0.0` = operand" | **both wrong.** P5/Q6 at x = -0.3: multi-row column `-0.0` (8000…), 1-row column `0.0`, literal `0.0`, literal broadcast to 3 rows `0.0`. A gives `-0.0` on the 1-row column and on the literal (L1: bits 9223372036854775808 for both). B gives `+0.0` everywhere under IEEE (`-0.0 + 0 = +0.0`), so it is wrong on every column of 2 or more rows. | yes (A1, A2): L1 `v2_rule` gives `-0.0` on the 5-row column and `0` on the 1-row column and the literal |
| D3 | Output name (`_named`, `alias`) | `match n with \| some s => if s.isEmpty then out else out.alias s \| none => out` | "`_named`/`alias` only affects the output column name, so it has no counterpart at the value level" | §2.3 `e.alias`, `e.name` | **rulebook right.** P1: `select(lt(col a, col b)).columns` = `['a']`, the same chain without `_named` = `['b']`, `lt(1.0, col b)` = `['literal']`; `with_columns(sas_round(col a + 0.6))` replaces column `a`. The name decides which column a positional call writes. Not observable inside `confusion_metrics` (`predicted=` overrides it), so B's three outputs are unaffected. | already right |
| D4 | Result of `lt` | a Boolean column: `(Pl.wto xe.isNull ce.isNotNull (Pl.wto ce.isNull (Pl.litB false) (xe.lt ce))).fillNull (Pl.litB false)` | `\| none, c => c.isSome \| some _, none => false \| some a, some b => ltTot a b`, type `Bool`, `fill_null` dropped as dead | none (fidelity §0 says do not simplify) | **both defensible.** P2: 64-pair table over null, NaN, ±inf, ±0.0, ±1: `lt`/`gt` null count 0; `lt(null, null)` False, `lt(null, NaN)` True, `lt(NaN, null)` False, `lt(1, NaN)` True, `lt(NaN, 1)` False, `lt(-0.0, 0.0)` False. Both texts give these values. | n/a |
| D5 | Integer operands (`ExprOrNum` int, Int64 columns) | `\| .int n => Pl.litI n`; prelude `cmpBin` compares two integer columns in `Int` | everything is `Option α`: "An integer input is assumed to be already embedded in `α`" | §2.1 `int` → `Int`, §2.2 integer arithmetic stays in `Int` | **rulebook right.** P3: `lt(Int64 col [2^53+1, 2^53], 2^53+1)` = `[False, True]`: polars compares Int64 with Int64 exactly. With `α := Float` B embeds both sides as 2^53 and returns `[False, False]`. (Mixed Int64/Float64 is cast to Float64 in polars: `2^53 as f64 < 2^53+1 as i64` is False; A and B agree there on `Float`, and both differ on ℝ: recorded limit "integers beyond 2^53".) | already right |
| D6 | dtype of `flag`, `predicted`, `COUNT` | `(cond.fillNull (Pl.litB false)).castI64` (Int64 column); `("COUNT", Pl.len.castI64)` | `def flag (cond : Option Bool) : α := if cond.getD false then 1 else 0`; `Cell.num (some (Nat.cast g.2 : α))`, because "`Cell` has no integer case" | §2.1 frame columns `.int`, §2.3 `castI64` | **rulebook right.** P4: `flag(col p)` schema `{'p': Int64}`, values `[1, 0, 0]`. P7: `confusion` schema `predicted: Int64`, `conf_matrix` `COUNT: Int64`. Q3: the frame writes `0.9,1.0,1` (not `1.0`). The foundation fixes `Cell` only at the stage boundary; inside a stage the dtype is part of what the Python produces. At the boundary the two agree: `Pl.toTable` casts an Int64 value with `ofInt`. | already right |
| D7 | Form of numeric literals | `Pl.litF (0.5 : α)`, `Pl.litF (1.0 : α)`, `Pl.litI 2`, `Pl.litI 0`, `up.castF64` | `(0.5 : α)`, `maxH 1 a`, `if ltTot 0 x then 1 … else -1`, `(if up then (1 : α) else 0)`, `Nat.cast (2 : Nat)`, `+ 0` | §2.2 "Never `(0 : α)`/`(1 : α)` for a float literal `0.0`/`1.0`" | **both defensible.** Q5: `max_horizontal(pl.lit(1.0), a)` and `max_horizontal(pl.lit(1), a)` both give `[1.0, 3.0]`; P6: `sign` returns `1.0` / `-1.0` (3ff0…, bff0…), the values of B's `1` / `-1`. No input separates the two forms; the rule buys one spelling, not a different value. B's forms need `OfNat α 0/1`, which B flags itself. | n/a |
| D8 | `_TWO52 = 2.0**52` | `def _TWO52 … : α := (4503599627370496.0 : α)` | `def two52 : α := (Nat.cast (4503599627370496 : Nat) : α)` | **silence**: §2.2 covers float literals, not a constant expression; v2's "`x ** 2` is `pow2`" now reads as if it applied | **both defensible.** Q1: `2.0**52 == 4503599627370496.0` True, `== float(2**52)` True, `sc._TWO52` = `4503599627370496.0`. Both forms denote that value. | no (R1) |
| D9 | `pl.max_horizontal(pl.lit(1.0), a)` | `Pl.maxHorizontal false [Pl.litF (1.0 : α), a]` with `-- TODO(port): … this unit has none; false passed` (prelude: nulls skipped, NaN ignored) | `def maxH (a b : α) : α := if ltTot a b then b else a` | §2.3 `max_horizontal`; v1 silence on `full` for 2 operands | **rulebook right.** P6: `max_horizontal(1.0, NaN)` = `1.0`; B's `maxH 1 NaN` is NaN (`ltTot 1 NaN` is true). B's helper is wrong on its own; inside `sas_round` it is masked: for a NaN input `up` is True in polars and in B, and the result is NaN either way (P5). | `full`: yes (A13, literal `true`) |
| D10 | `abs` | `xf.abs` = `mapF RealLike.abs` | `RealLike.abs xf` | foundation `RealLike.abs` (`-x` if `x < 0`, else `x`) | **both wrong, same way** (no A/B difference). P6: polars `abs(-0.0)` = `0.0` (0000…); `RealLike.abs (-0.0)` on `Float` is `-0.0`. Forced by the foundation. Not observable in `sas_round`: for x = -0.0 on a multi-row column Python gives `-0.0` and L1 gives 9223372036854775808. | recorded limit (A5), not fixable here |
| D11 | Frame model, empty frames | `(logit_scored_valid : Pl.Frame α)`: named typed columns, a zero-row frame keeps its columns | `(logitScoredValid : Table α)`: "A zero-row frame is `[]`, so its schema is lost … the function succeeds even where polars would raise" | §2.1 `pl.DataFrame` → `Pl.Frame α` | **rulebook right.** P7: zero rows with schema `{pd_logistic: Float64, default_flag: Float64}` returns `conf_matrix` with 0 rows and 3 columns and one `metrics` row `(0.5, null, null, null, null, null)`; zero rows and zero columns raises `ColumnNotFoundError`; zero rows with a String `default_flag` raises `ComputeError`. B maps all three inputs to `[]` and returns the first answer for each. Silence exposed on the rulebook side: `Pl.ofTable [] = []`, so a zero-row table at a boundary has no columns in A either (R2). | frame model already right; boundary case: no (R2) |
| D12 | Where Python raises | total function, plus `confusion_metrics_precond`: `Nodup` names ∧ equal column lengths ∧ `numeric "pd_logistic" ∧ numeric "default_flag"` (`.f64` or `.int`) | result `Option (Table α × Table α × Table α)`, "`none` where polars would raise", via `getNum … \| some (Cell.num v) => some v \| _ => none` | §1 Errors, §4 Preconditions | **both defensible.** P7: `pd_logistic` missing → `ColumnNotFoundError`; `default_flag` missing → `ColumnNotFoundError`; `pd_logistic` String → `ComputeError`; `default_flag` String → `ComputeError`. B returns `none` on all four when the table has a row; A's precondition excludes all four and the zero-column frame. A's precondition is stricter than Python: Boolean `default_flag` is excluded, yet P7 shows Python returns `conf_matrix [(False, 0, 1), (True, 1, 1)]` and every metric 1.0 (R3). | no (R3) |
| D13 | `group_by` and `sort` | `(confusion.groupByAgg ["default_flag", "predicted"] [("COUNT", Pl.len.castI64)]).sort ["default_flag", "predicted"]` | local `keyEq`, `keyLt`, `bump`, `groupCounts`, `pairLt`, `insertSorted`, `sortGroups` | §1 "Never re-implement a polars behaviour locally" | **both defensible.** P7 keys `[-0.0, 0.0, NaN, 2.0, NaN, 1.0]`: `conf_matrix` = `[(-0.0, 0, 2), (1.0, 1, 1), (2.0, 0, 1), (NaN, 0, 2)]`; with a null key: the null group first. B's code gives this (one group for ±0.0 keeping the first row's `-0.0`, one NaN group, nulls first, NaN last), and so does the prelude text (`Val.keyEq`, `Val.lt`). The rule buys one encoding with evidence; B's copy happens to be right. | n/a |
| D14 | Counts and ratios | Int64 columns: `((Pl.col "TP").add (Pl.col "TN")).div (…)`, guard `.gt (Pl.litI 0)` | `Nat` counts: `if den > 0 then some ((Nat.cast num : α) / (Nat.cast den : α)) else none` | §2.1 "`int` → `Int` (never `Nat` …)", §2.2 `int / int` | **both defensible.** P7 (3 TP, 1 FP, 2 FN, 1 TN): accuracy 3fe2492492492492, precision 0.75, recall 0.6, specificity 0.5: one division of two exactly represented integers in both. Empty selection sums to 0 and the guard gives null (P7 "only negatives predicted": precision null). | n/a |
| D15 | `.otherwise(None)` | `(Pl.litOptF none)` (a Float64 null) | `else none` | §2.3 v1 had no rule for a Null-dtype branch | **both defensible in this unit.** P7: all six `metrics` columns are Float64 on every input because of the final `.cast(pl.Float64)`, so the dtype of the null branch cannot be seen here. | yes in general (A3, `Pl.litNull`) |

Checked and found identical in A and B (no row):

- NaN in comparisons: both use the polars total order (P2).
- `sign`: P6 `[NaN, -0.0, 0.0, -1.0, 1.0, null, 1.0, -1.0]` for `[NaN, -0.0, 0.0, -3, 3, null, inf, -inf]`; both return the value for a zero or a NaN.
- Null in `sas_round`: null in, null out (P5). ±inf and `|x| >= 2^52` returned unchanged (P5).
- Arithmetic grouping: `(a - fl) >= (0.5 - max(1, a) * fuzz)`, `sign * (fl + up)`, `(2 * (p * r)) / (p + r)` in both.
- `predicted`: null `pd_logistic` → 0, NaN → 1, NaN threshold flags only NaN rows (P7).
- `with_columns` replaces an existing `predicted` in place (P7).
- The f1 guard: p + r = 0 → null, p or r null → null (P7 "f1 guard", "only negatives predicted").
- Column order of `conf_matrix` and `metrics`; `suffix` unused.

Not behavioural, not counted: B uses camelCase names (`sasRound`, `confusionMetrics`), `/-- -/` doc
comments and its own `setCol` / `List.lookup` where the foundation has `Row.set` / `Row.get`. §4,
§1 and §0 forbid each of these. Q2: polars refuses duplicate column names (`DuplicateError`), so
B's `setCol` and `Row.set` cannot differ on a real frame.

## Lean evidence L1

`eval_decl(item_id="def:ExprOrNum", decl="Pl.zipB")` on A's `sas_round` body inlined over the
current prelude, once as A wrote it and once with `.add (Pl.litF 0.0)` (the v2 rule), `α := Float`:

| Input | A as written | v2 rule | Python |
|---|---|---|---|
| 5-row column `[-0.3, -0.0, 2.5, null, NaN]` | `-0.0, -0.0, 3.0, null, NaN` | the same | `-0.0, -0.0, 3.0, null, NaN` |
| 1-row column `[-0.3]` | `-0.0` (9223372036854775808) | `0.0` (0) | `0.0` |
| literal `-0.3` on a 1-row frame | `-0.0` | `0.0` | `0.0` |

## Proposed rule changes not in `amendments.md`

| # | Section | Change | Evidence |
|---|---|---|---|
| R1 | §2.2 | A module-level constant defined by an expression (`_TWO52 = 2.0**52`) is the value Python computes, written as its decimal literal with the source expression in a comment. Say that the `pow2` rule (A8) is for a run-time `x ** 2` only. | D8, Q1: `2.0**52 == 4503599627370496.0` is True. A chose the literal on its own judgment; under v2 a second agent could reach for `pow2`. |
| R2 | §2.6 (or §6 limits) | State what a zero-row table means at a stage boundary. `Pl.ofTable [] = []` has no columns, so every unit that reads a column is outside its precondition, while Python on a zero-row Float64 frame succeeds. Either each `run` precondition states that its input tables are non-empty, or the case is recorded as a limit. | D11, P7 and Q4: zero rows with a Float64 schema gives the `metrics` row `(0.5, null × 5)`; zero columns raises `ColumnNotFoundError`; a header-only CSV read by `pl.read_csv` has String columns and raises `ComputeError`. |
| R3 | §4 Preconditions | Give the frame part of a precondition one fixed wording (distinct names, equal column lengths, then per column: present and of the listed kinds), and require a comment for every input the precondition excludes although Python does not raise. | D12, P7: A's `numeric "default_flag"` excludes a Boolean column, on which Python returns every metric 1.0. A wrote the two well-formedness conjuncts by hand; nothing makes the next unit write the same ones. |
| R4 | §2.3 `e + 0.0` row, diffeval suites | A unit that contains `+ 0.0` or `- 0.0` is tested on a 1-row frame, a frame of 2 or more rows and a literal argument. No change to the rule itself. | D2, Q6, L1: the three inputs give `0.0`, `-0.0`, `0.0`; version 1 passed on multi-row columns only. |

## Deletion

`/private/tmp/claude-501/-Users-cristophersalvi-GitHub-sas-migration-formal-python/aa9ba63a-dfbb-4dbd-bc0a-805359ea00aa/scratchpad/bakeoff_B.md`
was deleted after this report was written (checked with `ls`: no such file). The inspector's own
scratch files there (`bakeoff_gen.py`, `bakeoff_gen2.py`, `bakeoff_input.txt`, `bakeoff_exp.json`,
and the scratch copies of the two probes) were deleted too. The blueprint and `RULEBOOK.md` were
not modified.
