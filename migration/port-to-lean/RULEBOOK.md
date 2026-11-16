# Translation Rulebook — Python (polars 2.1.0, numpy 2.5.4) → Lean 4, blueprint `py-credit-risk-port`

**Version 5** (2026-11-16: batch 8 = H1–H7, what the readers deliver on valid input, §2.8; batch 7 = G1–G20 for the port as changed on 2026-11-16, §2.7; where §2.7 differs from an earlier section, §2.7 holds). Version 4 (2026-11-10: batch 3 = C1–C3 after the run reviews; batch 1 = A1–A14 after the stress test; batch 2 = B1–B14 after the first reviews; all listed in `migration/amendments.md`). **The preludes are frozen** (B13).

Blueprint id since the owner's re-base of 2026-11-16: `5365851c-5549-44b7-9207-4bd4c422031d`. The earlier id
`b41b22d4-720d-4290-b593-39ceab961986` is a stale copy: nothing is written to it.

> The meta-rule: if two agents could answer a question differently, the answer goes in this file.
> Read-only inside any loop. Implementers, reviewers and fixers cite it and never edit it.
> Amendments are queued in `migration/amendments.md` and applied by the orchestrator between batches.

Read this whole document before writing any Lean.

## 0. The shared foundation (read-only) and posture

- `foundation/foundation.pdf` fixes the types `Tabular.RealLike`, `Tabular.Cell`, `Tabular.Row`,
  `Tabular.Table`, `Row.get`, `Row.set`, `RealLike.abs`, `RealLike.eqb`. Never redefine or work
  around them. It decides no Python behaviour.
- The one job is **fidelity**: the Lean does what the Python does when it runs, including what
  looks wrong. Do not tidy, simplify, reorder, merge duplicated code or fix anything.
- **Never translate a comment or docstring.** They say what SAS does; they are the claims under
  test. Translate the code. Settle doubt by running the Python (`uv run python ...`).
- Isolation: never look for SAS code or its outputs anywhere; read only `port/`, `legacy/data/`,
  `judge/scenarios/`, `migration/port-to-lean/`, `migration/foundation/`; never open a Logos
  blueprint other than `py-credit-risk-port` and `credit-risk-foundation`. Inside
  `py-credit-risk-port`, never open, search or grep a `thm:`, `neg:` or `def:wf_*` item (they are
  another team's and mention the other side); restrict every `grep` / `search` to `def:` code items
  and their `_precond` items, with an exact or prefix query on the name you want.
- All Lean lives in the blueprint (`Logos MCP Staging` connector only, blueprint opened by id). No local Lean files.
- A unit is done when `write_statement` reports it accepted, not before. The in-loop referee is
  the server: it compiles and judges every statement (kit Step 4 dissolved into Step 3).
- Never change trust layers. Never edit an item you were not assigned. **Never edit
  `def:ExprOrNum` or `def:FloatArray_`** (the preludes): changing them clears every dependent.

## 1. What we use and what we ban

| Area | Decision | Why |
|---|---|---|
| Number type | Every definition is written once for `{α : Type} [Tabular.RealLike α]`. `ℝ`, `Real`, `Float` never appear in an item. | foundation §2 |
| polars | Only through the prelude `Pl` (in `def:ExprOrNum`). Never re-implement a polars behaviour locally. | one encoding per library rule, each with evidence |
| numpy | Only through the prelude `Np` (in `def:FloatArray_`) and plain list code that mirrors the Python line by line. | same |
| Mathlib | Core `List`/`Option`/`Nat`/`Int`/`String` functions only. No `Finset`, no `∑`, no real analysis. | definitions must evaluate with `eval_decl` |
| Bodies | A real body, never `sorry`, never `axiom`, never `partial`/`unsafe`/`opaque`. Recursion is structural or on explicit fuel. | must evaluate and be provable about |
| Doc comments | Never `/-- ... -/`. Plain `--` comments only. | server rule |
| Errors | Lean functions are total. Where Python raises, the Lean returns the value the code path would give if it continued, and the unit's precondition (`add_precond`) excludes the case. | §2 |

## 2. One canonical mapping per construct

### 2.1 Types

| Python | Lean | Notes |
|---|---|---|
| `float` | `α` | |
| `int` | `Int` (never `Nat` in signatures) | |
| `bool`, `str` | `Bool`, `String` | |
| `X \| None` | `Option X` | |
| `pl.Expr` | `Pl.Expr α` | |
| `ExprOrNum` | `ExprOrNum α` (`.expr e`, `.float x`, `.int n`) | at a call site a Python float literal is `.float (..)`, an int literal `.int ..`, an expression `.expr ..` |
| `pl.DataFrame` | `Pl.Frame α` | columns `Pl.Col α`: `.f64`, `.int`, `.bool`, `.str`, `.cell` |
| `pl.Series` | `Pl.Col α` | the Series name is dropped; `with_columns(s.alias(n))` is `fr.setCol n s` |
| 1-D float ndarray | `List α`; `List (Option α)` when it came from a nullable column (R-NULLNAN) | |
| 2-D float ndarray | `List (List α)` (rows) | |
| `FloatArray` annotation | `FloatArray_ α` only where the annotation is the declared type of a field or parameter of a class/def item | |
| `list[T]`, `tuple[A, B]`, `dict[str, T]` | `List T`, `A × B`, `List (String × T)` (insertion order) | |
| dataclass | `structure` with the same field names and order | |
| a frame read from or written to a CSV file | `Tabular.Table α`, converted with `Pl.ofTable` / `Pl.toTable` | §2.6 |

### 2.2 Numbers and literals

- Python `float` literal → the same decimal literal at type `α`: `100.0` → `(100.0 : α)`, `1e-12`
  → `(1e-12 : α)`, `0.5` → `(0.5 : α)`. Never `(0 : α)`/`(1 : α)` for a float literal `0.0`/`1.0`.
- A module-level constant defined by an expression (`_TWO52 = 2.0**52`) is the value Python computes, written as its decimal literal (`4503599627370496.0`); `pow2` (§3) is only for a run-time `x ** 2`.
- Python `int` literal or value used where a float is expected → `Pl.ofInt n` (a cast). In a
  polars expression the prelude does the cast: pass `.int n` / `Pl.litI n`.
- Integer arithmetic stays in `Int` (`+ - *`, comparisons, `len`, counts). `int / int` (true
  division) is `Pl.ofInt a / Pl.ofInt b`.
- Python float arithmetic: the same operations, the same order, the same grouping. `a / b * c`
  stays `a / b * c`. Never use `+ 0`, `* 1`, distributivity, commutativity or a common
  subexpression that the source does not have.
- Python `x == y`, `x < y`, `x <= y`, `x >= y`, `x > y` on floats: `RealLike.eqb x y`,
  `decide (x < y)`, `decide (x ≤ y)`, `decide (y ≤ x)`, `decide (y < x)`. `x != y`: `!(RealLike.eqb x y)`.
  (A NaN operand makes every Python comparison false and `!=` true; the `Float` instance agrees.)
- `abs(x)` → `RealLike.abs x`; `max(a, b)` Python builtin on floats → `if a < b then b else a`
  written out as Python evaluates it (`max(a, b)` returns `b` only if `b > a`); `min` dually.
- `math.sqrt`, `math.exp`, `math.log`, `np.exp`, `np.log` → `RealLike.sqrt/exp/log`.
  **Convention 1**: every `/`, `log`, `sqrt`, `exp` is guarded exactly as the code guards it, or
  covered by the unit's precondition. Where the code tests finiteness or NaN (`is_finite`,
  `np.isfinite`, `math.isfinite`, `np.isnan`), apply `RealLike.isFinite` / `RealLike.isNaN` to the
  same value at the same point.
- **R-DIV0.** Where the code divides and then maps a non-finite quotient away (`sas_compat.div`: `q[~np.isfinite(q)] = nan`), IEEE division by zero is part of the behaviour (x/0 is ±inf or NaN) and must not be left to `α`'s `/`: write `if RealLike.eqb den 0.0 then <the code's result for a non-finite quotient> else (let q := num / den; if RealLike.isFinite q then … else …)` with the comment `-- R-DIV0`. A division with no such mapping (`a / b` on columns, Python `/`) is left as `/` and the unit's precondition states the divisor is not zero.
- **Python raises.** Python float `/` raises ZeroDivisionError on a zero divisor; `math.log` raises on an argument ≤ 0, `math.sqrt` on a negative one, `math.exp` and `**` on overflow. Each such site needs the precondition (non-zero, positive, non-negative, result finite), not only a domain remark.
- **`x ** 2` on a Python float** is libm `pow(x, 2.0)`, which is not `x * x` (differs in the last bit on about 0.14% of values): explicit parameter `pow2` (§3).
- **R-F2I (float → int).** The foundation has no map `α → Int`. A float converted to an integer
  (`int(x)`, `math.floor`, `math.ceil`, `.cast(pl.Int64)` of a float column, `astype(int)`) **stays
  the value in `α`** (`math.floor x` → `RealLike.floor x`, `math.ceil x` → `-(RealLike.floor (-x))`,
  `int(x)` → `x`); integers later combined with it are cast with `Pl.ofInt` and the arithmetic or
  comparison is done in `α`. The unit's precondition states that the value is integral wherever
  Python truncates (`int(x)`). A loop or range whose bounds are such values enumerates candidate
  integers over a bound stated in the precondition and filters by comparison in `α`. Mark every
  such site `-- TODO(port): F2I`. This is a recorded deviation (open item for the user).
- **R-NULLNAN.** `Series.to_numpy()` turns null into NaN and `pl.Series(..., nan_to_null=True)`
  turns NaN into null. `α` has no NaN constant. A numpy array obtained from a nullable column is
  `List (Option α)`; `none` stands for that NaN and propagates through numpy arithmetic
  (`Option.map` / `Pl.opt2`); `np.isnan(x)` on such an element is `x.isNone || isNaN`;
  `nan_to_null=True` maps `none` and every `some x` with `RealLike.isNaN x` to null.

### 2.3 polars expressions (prelude `Pl`, all evidence in §6)

| Python | Lean |
|---|---|
| `pl.col("x")` | `Pl.col "x"` |
| `pl.lit(1.5)`, `pl.lit(3)`, `pl.lit("A")`, `pl.lit(False)` | `Pl.litF 1.5`, `Pl.litI 3`, `Pl.litS "A"`, `Pl.litB false` |
| `pl.lit(v, pl.Float64)` with `v : float \| None` (a non-optional float `v` is `some v`) | `Pl.litOptF v` |
| `pl.lit(None)`, `.then(None)`, `.otherwise(None)` | `Pl.litNull` (dtype Null: takes the dtype of the other branch) |
| `pl.lit(<date>)` | `Pl.litCell today` (§3) |
| a bare Python number as operand of an `Expr` operator (`e * 100`, `1 - e`, `e > 0`, `e + 0.02`) | `Pl.litI 100` / `Pl.litF 0.02` on that side; a Python float variable `v` is `Pl.litF v`, an int variable `Pl.litI n` |
| `a + b`, `a - b`, `a * b`, `a / b`, `-a` | `a.add b`, `a.sub b`, `a.mul b`, `a.div b`, `a.neg` |
| `e + 0.0` | `e.add (Pl.litF 0.0)` like any other addition: the prelude's `add`/`sub` carry the scalar-zero rule (a length-1 zero added to a longer column leaves it unchanged; two length-1 operands are added) |
| `a < b`, `<=`, `>`, `>=`, `==`, `!=` | `a.lt b`, `a.le b`, `a.gt b`, `a.ge b`, `a.eq b`, `a.ne b` |
| `a & b`, `a \| b`, `~a` | `a.and b`, `a.or b`, `a.not` |
| `e.is_null()`, `e.is_not_null()`, `e.fill_null(v)` | `e.isNull`, `e.isNotNull`, `e.fillNull (Pl.litB v / Pl.litF v)` |
| `e.cast(pl.Float64)`, `e.cast(pl.Int64)` (Boolean/int input) | `e.castF64`, `e.castI64` |
| `pl.when(c).then(a).otherwise(b)` | `Pl.wto c a b` |
| `pl.when(c1).then(a1).when(c2).then(a2)…otherwise(b)` | `Pl.wto c1 a1 (Pl.wto c2 a2 … b)` |
| `pl.when(c).then(a)` (no otherwise) | `Pl.wto c a Pl.litNull` |
| `pl.all_horizontal([..])` | `Pl.allHorizontal [..]` |
| `pl.sum_horizontal(es)` | `Pl.sumHorizontal full es` (`full`: §3) |
| `pl.min_horizontal(es)`, `pl.max_horizontal(es)` | `Pl.minHorizontal full es`, `Pl.maxHorizontal full es` |
| a horizontal reduction with exactly 2 operands (or `sum_horizontal` with at most 4) | the shape does not depend on `full`: pass the literal `true`; the unit takes no `full` parameter for it |
| `e.log()`, `e.exp()`, `e.abs()`, `e.floor()`, `e.sign()`, `e.is_finite()` | `e.log`, `e.exp`, `e.abs`, `e.floor`, `e.sign`, `e.isFinite` |
| `e.count()`, `e.sum()`, `e.mean()`, `e.min()`, `e.max()`, `e.median()`, `pl.len()`, `e.cum_sum()` | `e.count`, `e.sum`, `e.mean`, `e.min`, `e.max`, `e.median`, `Pl.len`, `e.cumSum` |
| `pl.len().cast(pl.Int64)` | `Pl.len.castI64` |
| `e.filter(p)` | `e.filter p` |
| `e.is_in(series.implode())` (floats), `e.is_in(["A","B"])` | `e.isInF values`, `e.isInS ["A","B"]` |
| `e.alias("n")` | `e.alias "n"` |
| `pl.struct(a.alias("a"), b.alias("b")).map_batches(run, …)` | `Pl.mapBatches2 a b run` with `run` on the two `List (Option α)` |
| `e.meta.output_name(raise_if_undetermined=False)` | `e.name` |
| `json.loads(e.meta.serialize(format="json"))` | `e.ser` |

Frames:

| Python | Lean |
|---|---|
| `df.with_columns(name=e, …)` | `df.withColumns [("name", e), …]` (same order) |
| `df.with_columns(e)` positional | `df.withColumns [e.pos]` |
| `df.with_columns(series.alias("n"))` | `df.setCol "n" col` |
| `df.select(name=e, …)`, `df.select(e)`, `df.select("a", B=e)` | `df.select [("name", e), …]`, `df.select [e.pos]`, `df.select [(Pl.col "a").pos, ("B", e)]` |
| `df.select("a", "b")` / `df.select([c for c in df.columns if c in KEEP])` | `df.cols ["a","b"]` / `df.keep [...]` |
| `df.filter(p)` | `df.filter p` |
| `df.drop("a", "b")`, `df.rename({...})` | `df.drop ["a","b"]`, `df.rename [("old","new"), …]` |
| `df.sort(by, maintain_order=True)` | `df.sort ["k1", "k2"]` |
| `df.group_by(keys, maintain_order=True).agg(name=e, …)` | `df.groupByAgg ["k"] [("name", e), …]` |
| `a.join(b, on="k", how="left"\|"inner", maintain_order="left", nulls_equal=…)` | `a.join b "k" (inner := …) (nullsEqual := …)` positional: `a.join b "k" false false` for a plain left join |
| `pl.concat([..], how="vertical")` | `Pl.concat [..]` |
| `df.cast(pl.Float64)` | `df.castF64`; `df.cast(pl.Int64)` of integer columns is the identity |
| `df.height`, `df.get_column("x")`, `df.item(0, "x")` | `df.height` (a `Nat`; `(df.height : Int)` in integer arithmetic), `df.col "x"`, `df.itemF 0 "x"` (`itemI`, `itemS` for an Int64 / String column; `df.item(0, 0)` is `df.itemF 0 df.firstName`; `df.item()` on a 1×1 frame likewise) |
| `df.filter(pl.Series(mask))`, `arr[mask]` (Boolean mask) | `df.takeRows idx` / `List` filtering with the indices where the mask is true, in order |
| `df.sort(k)` / `df.group_by(k)` without `maintain_order=True` | the same `sort` / `groupByAgg`, only where the keys are provably distinct (sort) or the result is sorted right after (group_by); say so in a comment |
| `pl.all_horizontal(pl.col(*names).is_not_null())` | `Pl.allHorizontal (names.map fun n => (Pl.col n).isNotNull)` |
| `df.get_column("x").to_list()` / `.to_numpy()` of a Float64 column | `df.getF "x"` (`getI`, `getS` for Int64, String) |
| `x.rank("average", descending=d)` | `Pl.rankAverage x d` |
| `pl.DataFrame({"a": s1, "b": s2}).drop_nulls()` | keep the rows where no column is null (plain list code over the zipped columns) |
| `series.cast(pl.Float64)` | `col.asF64` |
| `x.len()`, `x.null_count()`, `x.drop_nulls()` on a float Series `x : List (Option α)` | `x.length`, `(x.filter Option.isNone).length`, `x.filterMap id` |
| `pl.DataFrame({...})` built from Python lists | a frame literal `[("name", Pl.Col.f64 …), …]` with the dtype the constructor produces |

The prelude states `abs`, `floor`, `sign`, `sumHorizontal`, `min`, `max` for Float64 inputs, and `filter` / `cumSum` for select context only: never use them on an Int64 input or inside `groupByAgg`.

Anything not in these tables: do not invent a mapping. Translate with plain list code that mirrors
the library behaviour you establish by running it, mark the site `-- TODO(port): <question>`, and
report it so that the rule is added here (UNKNOWN rule).

### 2.4 numpy (prelude `Np`)

| Python | Lean |
|---|---|
| `a.sum()`, `np.sum(a)` on floats | `Np.sum a` |
| `.sum()` on an integer array | `List.foldl (· + ·) 0` in `Int` |
| `np.var(a, ddof=1)` | `Np.var1 a` |
| `np.sort(a)`, `np.argsort(a, kind="stable")` | `Np.sort a`, `Np.argsortStable a` |
| `np.searchsorted(a, v, side="left"\|"right")`, `a.searchsorted(v, side=…)` | `Np.searchsortedLeft a v`, `Np.searchsortedRight a v` (results are `Nat`) |
| `np.cumsum` (ints) | `Np.cumsumInt` |
| `np.round(x, 3)` | `Np.round3 x` |
| element-wise `a op b`, `a op scalar`, `np.divide`, `np.floor`, `np.isfinite`, `np.where`, `np.clip`, boolean masks, slicing, `np.repeat`, `np.concatenate` | `List.map` / `List.zipWith` / `List.take` / `List.drop` / `List.replicate` code that mirrors the line |
| `a.mean()` on floats | `Np.sum a / Pl.ofInt n` (n = length; verified bit for bit) |
| `np.count_nonzero(mask)`, `a.min()`, `a.max()`, `np.column_stack`, `np.ones`, `.T`, slices | plain list code mirroring the line (`a.min()`: fold with `if x < acc then x else acc` from the first element; NaN excluded by precondition) |
| `np.linalg.inv`, `np.linalg.solve`, `@` (matrix product), `np.einsum`, `np.log1p`, `scipy` | explicit parameters (§3) |

### 2.5 Python control flow

- A `for` loop accumulating state → `List.foldl` over the same sequence in the same order, with
  the state as a tuple; `while` → recursion on explicit fuel with the fuel bound justified in a
  comment. Keep the statement order of the source inside the step function.
- Local helper functions (`def pct`, `def run`) → `let` functions or helper `def`s placed above the
  item's declaration, named `<item>_<helper>`.
- `print(...)` is not part of the result: omit, with one comment line.
- `raise` → precondition (§1 Errors). `try/except` in out-of-scope code only.

### 2.6 Stage boundaries and the `run` functions

- A `run` becomes a function from its inputs (§2.7 G1–G4: optional tables, explicit parameters
  §3) to `Option (List (String × Tabular.Table α))` (predict: §2.7 G4): `none` when the step
  stops and exports nothing, `some files` with the `(file name, table)` pairs
  in the order the code writes them. The file name is the last path component
  (`"model_features_train.csv"`). The `formats=` map is not part of the result.
- `sas_compat.proc_import_csv(path, …)` → the table parameter (the frame as imported: first
  column `VAR1`, names cut to 32 characters), turned into a frame by
  `Pl.ofTable` (numeric cells are Float64 columns, text cells String columns).
  `write_sas_csv(df, path, formats)` → the pair `(name, Pl.toTable df)`.
- A long `run` is split with `add_code` into consecutive line ranges, each an item named
  `def:<module>_run_<nn>_<what>` taking the frames/values the range reads and returning the ones
  later ranges use; the `run` item composes them in source order. Dependencies follow the calls.
- Column names are exactly the strings in the code. Column order is what the code produces.
- **Empty and malformed tables.** `Pl.ofTable [] = []` has no columns, so a zero-row input cannot be modelled: every `run` (and every step that receives an input table) requires in its precondition that each input table is non-empty, that all its rows have the same column names in the same order with the same cell kind per column, that the names are distinct, and that each column the code reads is present with the kind the code needs. Recorded limit.

### 2.7 Batch 7 (2026-11-16): stops, optional inputs, and the library calls new to the port

Decisions of the lead (2026-11-16) are marked DECISION. Evidence: `experiments/e07_batch7.py`,
output `experiments/e07_batch7.out.txt` (E07).

**G1. A stopped run (DECISION).** Each `run` returns `Option (…)`: `none` means the step stopped
and exported nothing, `some files` that it completed. The stop is inside the function, at the
point where the port prints its ERROR lines and raises `ValueError` (the "stop when the step
before did not produce its result" tests and the two input checks). It is no longer a precondition.
Any other raise (polars errors, the `RuntimeError` of train, the `ValueError` on `model.json`
variables) stays a precondition as before (§1 Errors).

**G2. Removal of earlier results.** The `unlink(missing_ok=True)` loop at the top of each `run`
has no value in the result. The `run` item states it in a comment that lists the file names in
source order and says what follows: when the result is `none`, none of those files exists after
the run. Files of the stage that are not in the loop (the `printed_*.csv`, `stepwise_summary.csv`,
`model.json`) are not removed; say so in the same comment.

**G3. Optional inputs (DECISION).** A file that may be absent, or an import that may fail, is an
`Option` parameter in the position of the Python path parameter (rule C2):

| Stage | Python | Parameter | `none` stands for |
|---|---|---|---|
| feature engineering | `proc_import_csv(data_dir / "cs-training.csv", guessingrows=None)` in `try` (:35-39) | `cs_training : Option (Tabular.Table α)` | the import raised `OSError`, `ValueError` or `PolarsError` (an absent file included) |
| train | `exists()` tests (:36-42), then the two imports | `model_features_train model_features_validation : Option (Tabular.Table α)` | the file does not exist. An existing file on which the import raises is outside the model: say so in the item text |
| metrics | `exists()` tests (:96-102), then the two imports | `risk_scores_validation risk_scores_train : Option (Tabular.Table α)` (order of the imports, :106-107) | the file does not exist; same remark |
| predict | `income_medians.exists()` (:31), import (:211) | `income_medians : Option (Tabular.Table α)` | the file does not exist |
| predict | `(input_dir / "model_coefficients.csv").exists()` (:31) | `model_coefficients_exists : Bool` | — (the file is only tested, never read; `model.json` stays `intercept`, `coefficients`) |
| predict | header probe and import (:42-79) | `cs_test : Option (List (String × Bool) × Tabular.Table α)` | `test_raw is None`: the import raised |

`some []` (an import that returned no row) is allowed where the code then stops by itself
(feature engineering: `known_incomes < 1`); elsewhere a zero-row table stays excluded by
precondition (§2.6), with the `-- narrowing:` comment. In metrics, empty score files are not valid
input (DECISION): keep the exclusion and say in the item text that empty training or validation
scores are excluded by precondition, not modelled.

**G4. The predict import parameter and a test file with a header and no applicant (DECISION).**
`cs_test = some (header, rows)` stands for everything lines 42-79 of `predict.py` produce:
`header` is the list of the columns of `test_raw` in order, each with `true` when polars typed the
column String and `false` when it typed it numeric (Float64); `rows` are the data rows. For a file
with one line (`test_lines == 1`) the frame is the import of the made-up copy, cleared: `header`
has the names and kinds of that import (text under the three names that hold `NA`, numeric under
the others) and `rows = []`. The unit builds `test_raw : Pl.Frame α` from the pair with a local
helper: one column per header entry, `.str` or `.f64` by its flag, values from `rows` by name
(`Pl.Frame` can hold columns of length 0; `Tabular.Table` cannot, which is why the header is its
own value). The precondition states that every row has exactly the header's names in order with
the header's kinds, and that the header names are distinct. The item text must say exactly this,
with the line range 42-79, so that the conditions on the parameter can be checked against real runs.
Consequence for the result (conservative choice of the orchestrator, DEV-013, to be confirmed by
the lead): predict writes files that can have a header and no row, so each file of `def:run_py_py`
is a triple `(file name, column names in order, table)`:
`Option (List (String × List String × Tabular.Table α))`. The other three stages keep pairs.

**G5. Input checks.** The checks (feature engineering :43-128, predict :82-182) are one unit each,
`def:fe_run_00_input_check` and `def:predict_run_00_input_check`, added with `add_code` on those
line ranges. They take the optional raw input and return what later lines use: the Boolean
"stop" (the test of :121 / :176) and the frame the steps continue with (`credit_raw` / `test_raw`
after the case-blind renaming; predict also `age_name`). The counters are plain `Int`.
Python `str.upper()` / `str.lower()` on column names and polars `str.to_uppercase()` on cells are
full Unicode case mappings (E07: `ß` → `SS`); Lean's `String.toUpper` / `toLower` change ASCII
letters only. Use them, and state in the precondition that the column names are ASCII
(`-- narrowing:` comment). (Corrected 2026-11-16 by G27 (a): the first wording also asked for
ASCII text cells in the checked columns; that is not needed, because the upper form is only tested
against `""`, `"."`, `"NA"`. G27 holds. `def:fe_run_00_input_check_precond` was accepted on the
first wording and keeps the stricter clause: §6.) `raw.schema[v] != pl.String` is a match on
the column kind (`.str` or not).

**G6. Strings in expressions.** Not in the prelude: write local `let` helpers (rule F1) that build
a `Pl.Expr α` with an explicit `eval`, the `name` of the input expression and `ser := Pl.node [e.ser]`.

| Python | Behaviour (E07) |
|---|---|
| `e.str.strip_chars(" ")` | removes U+0020 only, at both ends; a tab or U+00A0 stays; null stays null |
| `e.str.len_chars()` | number of Unicode scalar values (`String.length`), an integer column; null stays null; `<= 32` on it is null for null |
| `e.str.to_uppercase()` | G5 (ASCII by precondition); null stays null |
| `e.fill_null("")` | `e.fillNull (Pl.litS "")` (prelude) |
| `e.is_in(["", ".", "NA"])` | `e.isInS [...]` (prelude; null gives null) |
| `e.is_in([0.0, 1.0])` on a Float64 column | `e.isInF [some 0.0, some 1.0]` (prelude; `-0.0` matches, NaN does not, null gives null). On an Int64 column polars raises: the precondition states Float64 or String for the checked columns (what the import produces) |
| `sas_compat.input_best32(text)` on a String expression | the parameter `input_best32` applied to that expression |

**G7. `floor`, `ceil`.** `x.ceil()` on Float64 is `(x.neg.floor).neg` (bit-identical on the E07
values, signed zeros and infinities included; `RealLike` has no `ceil`).

**G8. `n_unique`, `drop_nulls`, `sum` of a Series.** `s.drop_nulls().n_unique()`: the number of
distinct non-null values, where all NaN are one value and `-0.0` equals `0.0` for floats
(`Pl.Val.keyEq`) and strings are compared exactly. Plain list code. `int(col.sum())` of an Int64
column: exact integer sum, 0 when empty.

**G9. `pl.coalesce(a, b)`** on two Float64 columns is `a.fillNull b` (E07: bit-identical, NaN is
not null, name of `a`).

**G10. Last row of a run of equal values** (`metrics_run_02_ks`). `e.shift(-1)`: the next row's
value, null on the last row. `a.ne_missing(b)`: never null; false when both are null or both
equal in the total order (NaN equals NaN, `-0.0` equals `0.0`), true otherwise.
`pl.int_range(pl.len()) == pl.len() - 1`: true on the last row only; an empty frame gives an empty
column. Local helper returning the Boolean column; it is only used as a `when` condition.

**G11. Frame helpers not in the prelude** (plain code on `Pl.Frame`, each a local `let`):
`df.head(k)` = `df.takeRows (List.range (min k df.height))`; `df.clear()` = `df.takeRows []`
(names and kinds kept, height 0); `df.item(i, 0)` with a negative `i` counts from the end
(`item(-1, 0)` is the last row); `frame.select([pl.col(n).alias(m), …])` = the listed columns
renamed, in list order; `pl.lit(None, dtype=pl.Float64).alias(c)` = `(Pl.litOptF none).alias c`;
`df.rename` to a name that already exists raises `DuplicateError` (precondition).
`fill_null(0)` keeps the column's dtype (Int64 stays Int64, Float64 gets `0.0`; NaN is not filled):
`e.fillNull (Pl.litI 0)` (the prelude casts for a Float64 column).

**G12. `pl.col(v).map_elements(sas_compat.sas_best12, return_dtype=pl.String)`.** A null is not
passed to the function and stays null; every other value, NaN included, is passed (E07). Local
helper: a `.str` column `v.map (fun o => o.map (fun x => sas_best12 (some x)))`, name of the input.
The parameter keeps the Python signature `Option α → String`. The branch is taken when the column
is not String (G5 kind test); the precondition states Float64 for that case.

**G13. Join with a key expression** (`predict_run_04_imputed`):
`l.join(r, left_on=pl.col("age_group").cast(pl.Float64), right_on="age_group", how="left", maintain_order="left")`.
Result columns: all left columns, then all the right columns in the order of the right frame, the
right key included at its own place as `age_group_right` (null on an unmatched row), with the
suffix `_right` on a clash. (Corrected 2026-11-16: the first wording said the key comes first
among the right columns; E07 only had a right frame whose key was its first column. The full
column and error rules are G23, which holds.) Rows as the prelude's
left join: left order, one row per matching right row in right order, null keys never match. A
String right key raises `SchemaError` (precondition: the imported `age_group` is numeric). Write a
local helper with the same list code as `Pl.Frame.join`, keeping the right key column.
The plain joins on an Int32 / Int64 key (`age_groups` with `income_medians`, `decile_list`,
`psi_bins`) are the prelude's `join`.

**G14. Integer arithmetic.** Python `//` is floor division: `Int.fdiv`. `-(-k * n // 10) - 1`
is written with the same operations in the same order. `0.5 / n` with an `int` n is
`(0.5 : α) / Pl.ofInt n`. `max(a, b)` / `min(a, b)` on `int` are plain `Int` max / min.

**G15. `math.fsum`** is the correctly rounded sum; it is not a left fold (E07: three different
results for fsum, a left fold and `np.sum` on 1000 values). Explicit parameter `fsum : List α → α`
(§3). It raises on `inf + -inf`; not reachable from squared deviations of finite values.

**G16. `**` on a numpy array.** `(arr - c) ** 2` is `x * x` on every element (E07: 0 mismatches on
400,000 values, also after `.tolist()`); write `(v - c) * (v - c)`. `pow2` (§3) stays for `**` on a
Python float.

**G17. Builtin `max` / `min` with a float literal.** `max(x, 0.0)` returns `x` unless `0.0 > x`
(so `-0.0` and NaN are returned unchanged); `min(x, 1.0)` returns `x` unless `1.0 < x`. Written out
as in §2.2.

**G18. Constants.** `_SE_EPS = 1000 * 2.0**-53` is exactly 125 / 2^50: write it as that quotient of
casts (rule F2). `_SQRTBIG = 1.3407807929943e154` is a float literal: the same decimal literal.

**G19. The medians file.** `income_medians.csv` is the first file feature engineering writes, from
`income_medians_all`. In predict the imported table is the parameter `income_medians` (G3); the
renaming of :213-222 is plain code on the column names (G5 for `upper` / `lower`).

**G20. Harness.** One carrier per group of units, each an identity on `List Int` depending on both
preludes: `def:zz_carrier_s` (sas_compat), `def:zz_carrier_f` (feature engineering),
`def:zz_carrier_p` (predict), `def:zz_carrier_m` (metrics), `def:zz_carrier_t` (train). `connect`
your carrier to your unit before evaluating; use no other carrier. Lookup tables for `sas_best`
(width 8) and `sas_best12` are regenerated from the port as it stands on the day of the evaluation.

Rules G21 to G25 were added by translators during the run. Numbers were made unique on 2026-11-16:
G21 (forward fill, T14), G22 (division under a guard, T14) and G23 (join completed, T8) keep their
numbers; the rule T4 wrote as "G21" (median of a Series) is G24; the rule T15 wrote as "G22" (score
against a Float64 literal) is G25. A comment in an accepted unit that cites the old number of G24
or G25 means these rules. A new rule takes the next free number (G26); its author adds it at the
end of this section and names its evidence file in full.

**G21. `e.forward_fill()`** (no limit; `metrics_run_05_cumulative_lift`, added by T14 on 2026-11-16).
Each null takes the last non-null value before it in the column; the nulls before the first
non-null value stay null; a NaN is a value (it is kept, and it fills the nulls after it); the dtype
is kept. Select / with_columns context only. Not in the prelude: a local `let` helper (rule F1) that
maps the values of the `.f64`, `.int`, `.bool` or `.str` column with one left fold carrying the last
non-null value, with the `name` of the input and `ser := Pl.node [e.ser]`; copy the helper of
`def:metrics_run_05_cumulative_lift`. Evidence: the differential suites `r3_lift` and `t14_lift`
(`diffeval/units/t14_gen.py`, hand-made cases "unsorted deciles, null defaults first / middle /
last", "all defaults null", "NaN defaults is kept, not filled"): 60 of 60 cases equal.

**G22. A column / column division under a `when` guard** (T14, reading of §2.2 Convention 1 and
R-DIV0). `pl.when(gt(d, 0)).then(… n / d …)`: polars evaluates `n / d` on every row and selects it
only where the guard holds. The Lean writes the same `Pl.wto` with `n.div d` inside; the unit's
precondition states nothing about `d` being non-zero, because the quotient on a row where the guard
fails is never selected. This is the one exception to the last sentence of R-DIV0 (§2.2), and it
holds only when the guard is in the same expression as the division; accepted by the reviewer and
by the lead (2026-11-16). Evidence: suite `t14_lift` (`diffeval/units/t14_gen.py`), cases with
`cum_count` 0, null and negative, and the real run on `judge/scenarios/fix_G43` (first deciles empty).

**G24. Median of a Series; the Int32 key of `age_groups`** (T4, 2026-11-16; first written as "G21"; evidence
`experiments/e08_series_median.py`, output `experiments/e08_series_median.out.txt`).
`s.drop_nulls().median()` on a Float64 Series `s : List (Option α)` is
`Pl.median ((s.filterMap id).map some)`: the same value, bit for bit, as the select-context
`pl.col(..).median()` (4000 cases, 0 differences: NaN is a value and the greatest, `[-inf, inf]`
gives NaN, an even count gives `0.5 * (b - a) + a`); a Python float, or `None` when no value is
left. `pl.lit(m, dtype=pl.Float64)` of that result is `Pl.litOptF m` (null for `None`, the same
bits otherwise, on every row). On a String column the median is `None` without an error, on an
Int64 or Boolean column it is a float: the unit states Float64 with a `-- narrowing:` comment.
`pl.DataFrame({"age_group": [1, 2, 3, 4, 5]}, schema={"age_group": pl.Int32})` is the frame literal
`[("age_group", Pl.Col.int [some 1, …, some 5])]`; joining its Int32 key with an Int32 or Int64 key
works, with a Float64 or String key polars raises `SchemaError` (precondition: integer key).
`pl.coalesce(a, b)` with a String operand does not raise (the result is a String column); with an
Int64 or Null-dtype operand next to a Float64 one the result is Float64. G9 stays stated for two
Float64 columns: the unit's precondition requires them, with a `-- narrowing:` comment.

**G25. A score column compared with a Float64 literal; an Int64 counter built from flags** (T15,
2026-11-16; first written as "G22"; evidence `experiments/t15_psi_dtypes.py`, output `t15_psi_dtypes.out.txt`, and the 108
cases of `diffeval/units/t15_gen.py`). `sas_compat.gt(pl.col(c), pl.lit(x, pl.Float64))` on a String
column `c` raises `ComputeError` ("cannot compare string with numeric type (f64)"): precondition
Float64, with a `-- narrowing:` comment for Int64, which does not raise. `pl.lit(0, pl.Int64)` plus
`flag(..)` terms is an Int64 column: `(Pl.litI 0).add ..`, kept `.int` (no R-F2I cast to Float64); on
a frame emptied with `.clear()` it is an empty Int64 column. `df.item(i, 0)` on a null cell is
`None`; `pl.lit(None, pl.Float64)` as the second argument of `gt` makes every non-null value
greater (missing is smallest) and no null value greater.

**G23. The join of G13, completed; `map_elements` on an empty or all-null column; one declaration
per statement** (T8, 2026-11-16; evidence `experiments/e08_t8_predict_steps.py`, output
`e08_t8_predict_steps.out.txt`, and the 55 cases of `diffeval/units/t8_gen.py`, `t8_edges_gen.py`).
This replaces the column rule of G13. `l.join(r, left_on=<expr named k>, right_on="k", how="left",
maintain_order="left")` returns the left columns, then ALL the right columns in the order of `r`,
the key at its own place (not first); a right column whose name is a left column's gets the suffix
`_right`, so the key is `k_right` because `l` has `k`. When `<name>_right` is already a column of
`l` or of `r`, polars raises `DuplicateError` (precondition, key included). An integer right key
against the Float64 left key raises `SchemaError` like a String one; an absent right key raises
`ColumnNotFoundError`. Keys match as in the prelude's join (`Val.keyEq` on the Float64 values:
`-0.0` equals `0.0`; a NaN right key matches no integer; a null on either side matches nothing).
An empty left frame gives all the columns with no row; an empty right frame gives nulls.
`pl.when(c).then(pl.coalesce(a, b)).otherwise(d)` with a String `a`, `b` or `d` does not raise: the
result is a String column (stated as a narrowing in the unit's precondition).
`map_elements(f, return_dtype=pl.String)` on a column with no row or with nulls only gives a String
column (length 0 / all null); `sas_compat.input_best32` of it is Float64.
The case-blind rename of `predict.py:213-222` never targets a taken name (no `DuplicateError`).
On a re-written (`changed`) item the server refused a statement with helper declarations above the
unit ("only one is allowed", T8): there a helper is a `let` inside the unit, and a precondition that
needs it restates it as a `let` (same text). A new `add_code` item was accepted with helper
declarations (T7).

**G26. `a + b * c` on Float64 columns is two rounded operations** (review of T10 / T17 by
port-translator-10, 2026-11-16; evidence `experiments/rv_t10_fma.py`). polars does not fuse
`pl.col("base_score") + pl.col("score_range") * (1 - pl.col("pd_logistic"))` into a multiply-add: on
200,007 values the column equals Python's `600.0 + 250.0 * (1 - p)` bit for bit (0 differences; 16,533
differences from `math.fma`). So it is `a.add (b.mul c)` with the prelude's `add` / `mul`, as written.

**G27. Input checks: three facts settled by T7** (2026-11-16) (E08: `experiments/e08_t7_input_check.py`, output
`e08_t7_input_check.out.txt`). They hold for both input checks (same expressions).
(a) *Upper case on cells needs no narrowing.* `….str.to_uppercase().is_in(["", ".", "NA"])` with
`String.toUpper` (ASCII letters only) is exact for every text: over all Unicode scalar values, the
only characters whose polars upper form holds `N`, `A` or `.` are `n N a A .` and U+0149, U+1E9A,
whose upper forms (`ʼN`, `Aʾ`) keep a non-ASCII character; the upper form is the concatenation of
the characters' upper forms. So a text with a non-ASCII character never has the upper form `""`,
`"."` or `"NA"`, on either side. The precondition states ASCII for the **column names** only
(Python `upper()` maps U+017F to `S`, U+0131 to `I`, so a non-ASCII name can match an expected one);
this replaces the "text cells of the checked columns are ASCII" clause of G5.
(b) *A frame with no column.* `frame.select([])` has shape (0, 0), and `with_columns` of literal
columns on it gives the columns with **no row** (shape (0, k), not (1, k)): the prelude's
`withColumns` agrees, no special case. The check then counts `bad_rows = 0`, `duplicate_ids = 0`.
(c) *`input_best32` in the check.* The parameter is applied to the stripped text expression; the
precondition states that it returns a Float64 column of the frame's height on each text column the
check reads, and only for the inputs on which the result depends on it (predict: `columns_ok = 1`).

**G28. The join of G23 when the right frame repeats a key: right order at any size** (review of T8
by port-translator-9, 2026-11-16; evidence `experiments/rv_t8_join_dups.py`, output
`rv_t8_join_dups.out.txt`, and the 10 cases of `diffeval/units/rv_t8_gen.py`). With
`how="left", maintain_order="left"` and a key expression, a left row with several matching right
rows gets them in the order of the right frame, also on large frames (200,000 left rows against
2,000 right rows, 27,350,686 result rows; 3 against 100,000): equal to the list model of G23 row
for row. No change to G23; this is the evidence for its "in right order" on repeated keys.
`select` after the join reads a name the left frame also has from the LEFT column (the right one
is `<name>_right`): a `test_cleaned` with its own `median_income` is imputed from that column.

### 2.8 Batch 8 (2026-11-16): what the port's readers deliver on VALID input

Observed on real runs; no Lean. These are the facts the conditions on the input parameters of the
four `run` items may rest on. Scope: valid files only (documented columns, numeric fields, blank or
NA where a missing value is allowed, unique ids, at least one training row; the test file may be a
header with no applicant). Quoted fields, other headers, blank lines and short rows are not covered.
Evidence: `experiments/e08_inputs.py` (E08), `e09_readback.py` (E09), `e10_valid_stops.py` (E10),
`e11_medians_readback.py` (E11), each with its `.out.txt`. Meant to be blueprint items
`rule:<name>`; the server refuses the prefix `rule` (only def / thm / lem / neg), so they are here.

**H1 `rule:import_raw_names_rows`.** Reader: `sas_compat.proc_import_csv(path, guessingrows=None)`
(feature engineering on `cs-training.csv`; predict on a `cs-test.csv` with at least one data line).
The frame has (1) the columns, in header order: `VAR1`, `SeriousDlqin2yrs`,
`RevolvingUtilizationOfUnsecuredL`, `age`, `NumberOfTime30-59DaysPastDueNotW`, `DebtRatio`,
`MonthlyIncome`, `NumberOfOpenCreditLinesAndLoans`, `NumberOfTimes90DaysLate`,
`NumberRealEstateLoansOrLines`, `NumberOfTime60-89DaysPastDueNotW`, `NumberOfDependents` (the empty
first header field becomes `VAR1`; every name is the header field cut to 32 characters, which cuts
three names); (2) one row per data line; (3) rows in file order, cell (i, j) from field j of data
line i. E08 Part 1: compared field by field with the file text on 34 files (legacy/data, 150000 and
101503 data lines; the training and test files of 16 valid scenario folders) and 6 variants made of
verbatim legacy lines, one of them a single data line. All hold.

**H2 `rule:import_raw_kinds_cells`.** Same reader. Each column is Float64 or String, decided per
column over ALL data lines: Float64 when at least one field is not blank and every non-blank field
is a number; String otherwise. So one `NA` (or `.`, `na`) anywhere makes the column String, and a
column whose fields are all blank is String. Integers and decimals give the same kind: `5700` and
`5700.0` are both Float64 and the same value; `4.5e1` is Float64 45.0.
Cells: a blank field is null in either kind. In a Float64 column a non-blank field is
`float(field)`, bit for bit. In a String column a non-blank field is its text unchanged: `NA` is
the text "NA", not null, and `5700` is the text "5700".
What the real files give (E08 Part 1): training legacy/data: `MonthlyIncome` String (29731 NA),
`NumberOfDependents` String (3924 NA), the other ten Float64, no null anywhere. Test legacy/data:
`SeriousDlqin2yrs` String with every cell null (the column is blank on every line),
`MonthlyIncome` and `NumberOfDependents` String with NA texts, the other nine Float64.
Variants of legacy lines: no NA in any line: all twelve Float64; NA only in `MonthlyIncome`: that
column String, `NumberOfDependents` Float64; NA replaced by a blank field: both Float64 with nulls
(391 and 58 of 2000); every `NumberOfDependents` blank: String, all null.
So a valid training frame has `MonthlyIncome` and `NumberOfDependents` each String or Float64 and
the other ten Float64; a valid test frame the same, with `SeriousDlqin2yrs` String (all null) when
the column is blank throughout (every test file run: observed). A test file whose outcome column
holds NA or 0 / 1 was not among the valid files; the kind rule gives String and Float64 for them.

**H3 `rule:import_test_header_only`.** A `cs-test.csv` that is its header line and nothing else:
`test_raw` of the real `predict.run` has height 0 and the twelve columns of H1 in header order with
kinds `VAR1` Float64, `SeriousDlqin2yrs` String, `MonthlyIncome` String, `NumberOfDependents`
String, the other eight Float64. Same for LF, CR LF and no line end after the header
(`fix_Q27_emptytest/header_only`, `crlf_header_only`, `header_only_noterminator`), and with the
legacy training file. predict completes and writes `kaggle_submission.csv` (columns `row_id`,
`pd_logistic`) and `test_predictions.csv` (15 columns) with height 0. In the terms of G4:
`cs_test = some (header, [])` with `true` (String) exactly under those three names. E08 Parts 2-4.

**H4 `rule:readback_model_features`.** `model_features_train.csv` and
`model_features_validation.csv`, written by feature engineering and read by train with
`guessingrows=None`. Same 42 names in the same order, same number of rows in the same order, no
null written or read. Every column is read Float64 (written: 24 Float64, 14 Int64, 4 Int32), so in
table terms every cell is numeric on both sides. Cell law, which held on every cell of every run:
read = float(text printed by the writer), bit for bit; the text is `sas_best12(x)` for a Float64
column and `str(int)` for an integer column. The table read back is therefore NOT the table
written: in 11 Float64 columns the value changes because BEST12 keeps at most 12 characters:
`credit_utilization`, `debt_ratio`, `income_per_dependent`, `credit_lines_per_person`,
`log_monthly_income`, `log_num_credit_lines`, `log_total_late_payments`, `age_income_interaction`,
`utilization_debt_interaction`, `credit_utilization_capped`, `debt_ratio_capped` (legacy training
set: between 8901 and 103867 of 105000 cells per column; largest relative change 2.7e-7, in
`utilization_debt_interaction`; e.g. 9.118334726180159 is read 9.1183347262). The other 31 columns
were read equal to what was written, cell for cell, in every run. E08 Part 3, E09 A (legacy,
fix2/good, fix_G34/income_zero, fix2/q13_median_width, legacy reordered).
A validation set with no row (`fix_Q1`: two training lines, both in the split): the file is the
header alone and is read as 42 String columns with height 0 (E09 A). Train did not complete on
that file (RuntimeError, the fit did not converge), so nothing is known beyond the read.

**H5 `rule:readback_risk_scores`.** `risk_scores_validation.csv` and `risk_scores_train.csv`,
written by train and read by metrics with `guessingrows=20`: the kind of a column and the width of
a text column are decided on the first 20 data rows only. Same 51 names and order, same rows and
order, no null. Differences from the table written, all with runs (E08 Part 3, E09 A-C):
(a) `pd_logistic` and `credit_risk_score`: read = float(`sas_best12`(written)); every cell changes
(legacy: 45000 of 45000 and 105000 of 105000; relative change up to 8.8e-9 and 7.7e-12).
(b) `interest_rate`: written Float64 with format `percent8.2`, read as String: 0.09 is read "9.00%".
When the first 20 rows hold only 5-character texts, the longer ones are cut: "12.00%" is read
"12.00" (legacy and fix2/good validation sets).
(c) `recommendation` (String: Approve, Decline, Review): equal in the legacy and fix2/good runs.
With the legacy lines reordered so that the first 20 scored rows are all "Review" (a valid file),
"Approve" is read "Approv" and "Decline" "Declin" (43036 of 45000 and 100721 of 105000 cells).
(d) `risk_grade` (String, one character) and the other 46 columns: read equal to what was written,
cell for cell (the columns train took from the feature files already hold the values read
through BEST12, so printing them again changes nothing; `pred_logistic` is Int64 written, Float64
read, same values).
No run had a numeric column whose first 20 rows are all blank; by H2's rule on the 20-row window
such a column would be read String. Not observed on valid input.

**H6 `rule:readback_income_medians`.** `income_medians.csv`, written by feature engineering
(format `best32.` on the two medians) and read by predict with the default `guessingrows=20`:
5 rows, columns `age_group`, `median_income`, `overall_median_income`, all read Float64
(`age_group` written Int32). Read equal to written, cell for cell and null for null, on 11 training
files (E11; E09 A): legacy, fix2/good, q13_median_width, fix_G34/income_zero, fix_round5/good,
fix_Q27_textid/good, fix_Q13, and the files with an age group that has no known income (fix_Q1,
fix_Q14, fix_Q7, fix_Q9), where `median_income` is null for that group on both sides and
`overall_median_income` is never null.

**H7 `rule:inputs_present_in_sequence`.** The four stages run in order on valid input (feature
engineering, train, metrics, predict; one output folder): every "absent" parameter is present.
`credit_raw` is a frame; `model_features_train.csv` and `model_features_validation.csv` exist
before train; `risk_scores_validation.csv` and `risk_scores_train.csv` exist before metrics;
`income_medians.csv`, `model_coefficients.csv` and `model.json` exist before predict; `test_raw`
is a frame; no stage stops. Shown on 10 sequences (E08 Part 4): legacy/data, fix2/good,
fix_G34/income_zero, fix2/q13_median_width, fix_round5/good, fix_Q27_emptytest/good, the three
header-only test files, and legacy training with the header-only test file.
No exception (DECISION of the lead, 2026-11-16): a negative income is not valid input by the
requirements as they now stand, so fix2/valid_unusual and fix2/q14_negative_real, whose README
still says "Valid files", are not valid files. Feature engineering stops on them, and then every
later stage stops on its absent input, because rows 34 and 35 have `MonthlyIncome` -1 and -7.5
(bad_rows = 2; E10). Their rows with a blank, `.` or
`na` income and a blank `NumberOfDependents` are not counted bad. A training file of two lines
(fix_Q1) passes feature engineering and train raises RuntimeError (no convergence): not a stop of
the "absent input" kind, and outside the model.

**Not observed (batch 8).** No condition may rest on these without a new run.
1. A completed run with an empty validation set. The only case (fix_Q1) is read as 42 String
   columns of height 0 and train then raised RuntimeError (no convergence).
2. A valid test file whose `SeriousDlqin2yrs` holds NA or 0 / 1: none among the valid files; the
   kinds given in H2 for it follow from the kind rule, not from a run on such a file.
3. A numeric score column that is blank in its first 20 rows: no run had one; its reading as
   String (H5) is not observed.
4. Whether metrics uses `interest_rate` or `recommendation`: not established by a run (a text
   search of `metrics_calculation.py` finds neither name).

## 3. Explicit parameters (out-of-scope or non-deterministic behaviour)

Out-of-scope code is never translated. It is an explicit parameter of the unit that uses it, with
the canonical name and type below, placed **before** the Python parameters, in the order listed.
Every unit that receives one lists it in its trailer `-- OPEN(port): <name>`.

| Python | Parameter | Type |
|---|---|---|
| reduction shape of `sum_horizontal` etc. for N ≥ 3 operands (thread-pool dependent, E06) | `full` | `Bool` |
| `sas_compat.input_best32` | `input_best32` | `Pl.Expr α → Pl.Expr α` |
| `sas_compat.sas_best` | `sas_best` | `Option α → Int → String` |
| `float(text)` on rendered text | `parse_float` | `String → α` |
| `sas_compat.fmt_wd` | `fmt_wd` | `Option α → Int → Int → String` |
| `sas_compat.fmt_oddsr` | `fmt_oddsr` | `Option α → Int → Int → String` |
| `sas_compat.sas_d8`, `sas_d12_3`, `sas_pvalue` | `sas_d8`, `sas_d12_3`, `sas_pvalue` | `Option α → String` |
| `str(int)` | `Pl`-free: `toString` on `Int` (in scope: plain Python) | |
| `str(v)` / f-string of a float-valued quantity kept in `α` by R-F2I | `str_int` | `α → String` |
| `scipy.stats.chi2.sf` | `chi2` | `α → Int → α` |
| `dt.date.today()` | `today` | `Tabular.Cell α` (the cell that stands for the date) |
| `stepwise_logistic(...)` result | `stepwise` | `StepwiseResult α` |
| `model.json` content (predict) | `intercept`, `coefficients` | `α`, `List (String × α)` |
| `pl.read_csv(split_ids)` row_id column, after its casts | `split_ids` | `Tabular.Table α` (numeric column `row_id`) |
| `sas_compat.proc_import_csv(income_medians)` (predict; replaces the removed `medians`) | `income_medians` | `Option (Tabular.Table α)` (§2.7 G3) |
| `sas_compat.sas_best12` | `sas_best12` | `Option α → String` (called only on non-null values, §2.7 G12) |
| `math.fsum` | `fsum` | `List α → α` (§2.7 G15) |
| `np.linalg.inv` | `inv` | `List (List α) → List (List α)` |
| `np.linalg.solve(A, b)` | `solve` | `List (List α) → List α → List α` |
| matrix product `A @ B`, `A @ v`, `u @ v` | `matmul`, `matvec`, `dot` | `List (List α) → List (List α) → List (List α)`, `List (List α) → List α → List α`, `List α → List α → α` |
| `np.einsum("ij,jk,ik->i", x, v, x)` | `einsum_q` | `List (List α) → List (List α) → List α` |
| `np.log1p` | `log1p` | `α → α` |
| `x ** 2` on a Python float | `pow2` | `α → α` |

A parameter that stands for a library routine is total; the inputs on which the routine raises (a singular matrix: `LinAlgError`) are outside the model and are listed as OPEN in the unit's trailer.
The flags `fix_income_truncation`, `export_train_medians`, `fix_train_medians`, `fix_psi_bins` and the parameter `medians` no longer exist in the port (2026-11-16): no unit carries them.
A function whose return type depends on an argument (`roc_association` with/without `label`) returns a sum type `A ⊕ B`. A union-typed parameter (`fit: LogisticFit | FloatArray | None`) is `Option (A ⊕ B)`; `isinstance` tests are matches.
A table, frame or parsed-file parameter that stands for a Python path parameter takes that parameter's position (`input_dir` → what is read from it; `output_dir` is dropped); routine and format parameters come first, in the order of the table. (`def:run_py_py` was accepted with `medians` before `cs_test`; left as accepted, DEV-011.)
A unit that calls a blueprint item which has such parameters passes them through unchanged.
`train.run` also returns the content of `model.json` (see its item).

## 4. Naming, statement shape, done-ness

- Item ids are those of `index_codebase` (`def:lt`, `def:run` = feature_engineering,
  `def:run_py` = metrics_calculation, `def:run_py_py` = predict, `def:run_py_py_py` = train).
  The Lean name is the id without `def:`. A Python name that clashes with Lean gets a trailing
  `_` (`FloatArray_`).
- Statement shape: `def <name> {α : Type} [Tabular.RealLike α] (<explicit params §3>) (<Python
  params in order>) : <type> := <body>`. A constant is a `def` of its type. Helpers above it.
- Open the preludes by qualified name (`Pl.col`, `Np.sum`); do not `open Pl`.
- Every statement starts with `-- credit_risk/<file>:<line range>` and ends with the trailer
  `-- PORT STATUS: confidence=high todos=0` (confidence one of high / medium / low, no brackets; todos = number of `TODO(port)` lines) then one `-- OPEN(port): …` line per
  explicit parameter and one `-- TODO(port): …` line per unresolved site.
- Preconditions: `add_precond` item `def:<unit>_precond` for each unit that needs one: a
  `def … : Prop` over the unit's inputs stating domains (non-zero divisors, positive `log`
  arguments, no overflow), column presence and kind, integrality (R-F2I), and the cases where
  Python would raise. No postconditions. A precondition item is exactly one declaration, no
  trailer, no unused binder (name an unused parameter `_x`). Fixed wording for a frame: distinct
  column names; every column has the frame's height; each column read is present and of the
  listed kinds. Every input that is excluded although Python does not raise carries a comment
  saying so (`-- narrowing: …`). An expression helper (`lt`, `flag`, `sas_round`, …) cannot see
  dtypes: the dtype it needs (a Boolean condition for `flag`, numeric operands for comparisons,
  Float64 for abs / floor / sign / min / max) is stated in the precondition of the unit that
  evaluates the expression. A unit taking a `pl.Series` states the column kind it needs.
  String operands are excluded explicitly (polars parses numeric text in a cast instead of
  raising). A step with a join states that no right column renamed `<name>_right` clashes with
  an existing name (polars raises DuplicateError); a step with `rename` / `drop` states that the
  columns exist (the prelude's `rename` / `drop` are lenient, polars raises).
- Queue: `migration/manifest.tsv`. A unit is done when `get_status` no longer lists it under
  `statements_to_write` / `waiting`.

## 5. The gap inventory

`migration/inventory.tsv`: one row per site where Python or polars leaves implicit something Lean
must state (null vs NaN, int vs float column, row order after joins and group-bys, ties,
out-of-domain arguments, exceptions). Look your sites up there before translating. A site that is
not in the inventory is an inventory bug: apply the UNKNOWN rule, flag it, keep moving.

## 6. Evidence for every library rule

Experiments are in `migration/port-to-lean/experiments/` (run from `migration/port-to-lean` with `PYTHONPATH=../../port uv run --project ../../port python experiments/<file>`). Source = polars
tag `py-2.1.0`, numpy tag `v2.5.4`.

| Rule (prelude name) | Behaviour | Evidence |
|---|---|---|
| comparisons (`fLt`, `fLe`, `fEq`, `Expr.lt…`) | null if either side null; NaN = NaN, NaN greater than every number, `-0.0 == 0.0` | E01 tables |
| arithmetic (`numBin`, `Expr.div`) | null propagates; Int op Int stays Int; `/` is Float64 true division, `x/0` = ±inf/NaN not null | E01 `add`, `div`, dtype schema |
| scalar zero in `+`/`-` (`addCol`, `subCol`) | a length-1 zero operand against a longer column: no addition (`-0.0 + 0.0` stays `-0.0`; `0 - col` negates); two length-1 operands: IEEE (`sas_round(-0.3)` on a literal gives `+0.0`, on a column `-0.0`) | E05 "optimizer" block; pilot report; diffeval D2 |
| `litNull`, `Col.ite` | a Null-dtype branch takes the dtype of the other branch | diffeval D3 |
| Boolean logic (`kAnd`, `kOr`, `Expr.not`), `fill_null`, Boolean→Int64 cast | Kleene logic; `~null` = null; cast keeps null | E01 Boolean table |
| `wto` | null condition takes the next branch; `then(1)` is an integer column; missing otherwise = null | E01 Boolean table, schema |
| `minIgnoreNan`/`maxIgnoreNan`, `minHorizontal`/`maxHorizontal` | nulls skipped, all null = null; NaN ignored unless all NaN; zeros of opposite sign: min gives -0.0, max +0.0 (not expressible, documented) | E01 `min_h`/`max_h`; `horizontal.rs` `min_binary` |
| `sumHorizontal` | null operand = 0.0 (all null = 0.0); 2 operands a+b; N ≥ 3 rayon `try_reduce_with`: split at N/2, parts fully bisected with ≥ 2 threads, left-folded with 1 thread | E01 `sum_h`, E06 (threads 1–4, 12); `horizontal.rs` |
| `Expr.log/exp/abs/floor/sign/isFinite` | null stays null; `sign(±0.0)` and `sign(NaN)` return the value; polars `abs(-0.0)` is `0.0` but `RealLike.abs` cannot clear the sign of a zero (recorded limit) | E01 unary table |
| `floatSum` (select-context `sum`) | 128-blocks × 16 stripes, pairwise blocks, first `len mod 128` values sequential from 0.0, `main + rest`; null = 0.0 in place; empty = 0.0 | E02 (195/195 cases, with and without nulls); `polars-compute/float_sum.rs` |
| select-context `mean` | `floatSum / count(non-null)`; none when count = 0 | E02 |
| `kahan`, `groupSum`, `groupMean` (group_by().agg) | Kahan fold over the group's rows in frame order; 1-row group returns the value; all-null group: sum 0.0, mean null; mean divides by `len` (no nulls in column) or `len - nulls` | E04 (all groups, 4 modes); `aggregations/mod.rs` `agg_sum`/`agg_mean`, `kahan_sum.rs` |
| `aggMin`/`aggMax`, `count`, `len` | nulls skipped; count = non-null; len = rows | E02, E04 |
| `median` | total-order sort; odd: middle; even: `a` if `a == b` else `0.5*(b-a)+a` | E04 (345/345 even groups; `(a+b)/2` fails 85); `quantile.rs` `linear_interpol` |
| `cumSumF/I` | sequential from first non-null; null stays null | E02 |
| `Frame.sort` | stable; nulls first; NaN last; `-0.0`/`0.0` keep input order; result is one chunk | E05 sort block |
| `Frame.groups`, `groupByAgg` | groups in first-appearance order; null key is a group; NaN keys one group; `-0.0`/`0.0` one group | E04, E05 group block |
| `Frame.join` | left order kept; unmatched left row → nulls; null keys match only with `nulls_equal=True`; clash suffix `_right` | E05 join block |
| `withColumns`, `select`, `filter`, `concat` | all expressions read the input frame; replace in place / append; scalars broadcast; null predicate drops the row | E05 |
| `isInF`, `isInS` | null → null; NaN matches NaN | E05 |
| `rankAverage` | nulls → null; NaN greatest; ties `0.5*(first+last)`; descending reverses the order | E05; `rank.rs` |
| `Np.pairwise`, `Np.sum`, `Np.var1` | see prelude comments | E02 (195/195, 55/55); `loops_utils.h.src`; E05 (9 × -0.0 sums to +0.0) |
| `Np.sort`, `argsortStable`, `searchsorted*` | NaN last; stable; counts in NaN-last order | E05 numpy block |
| `Np.round3` | `rint(x*1000)/1000` on the grid | E05 |
| `Series.to_numpy` null → NaN, `nan_to_null` | R-NULLNAN | E05 |
| batch 7 calls (§2.7 G6–G17) | `str.strip_chars(" ")`, `len_chars`, `to_uppercase`, `is_in`, `ceil`, `n_unique`, `coalesce`, `shift`, `ne_missing`, `int_range`, `head`, `clear`, negative `item`, join with a `left_on` expression, `fill_null(0)`, `map_elements`, numpy `** 2`, `math.fsum`, builtin `max`/`min` | E07 (`experiments/e07_batch7.py`, `e07_batch7.out.txt`) |
| G21 `forward_fill`, G22 division under a guard | see §2.7 | `diffeval/units/t14_gen.py` (suites `r3_lift`, `t14_lift`) |
| G23 join with a key expression, `map_elements` on empty / all-null | see §2.7 | `experiments/e08_t8_predict_steps.py`, `experiments/e08_t8_predict_steps.out.txt`; `diffeval/units/t8_gen.py`, `t8_edges_gen.py` |
| G24 Series median, Int32 key, coalesce dtypes | see §2.7 | `experiments/e08_series_median.py`, `experiments/e08_series_median.out.txt` |
| G25 String score against a Float64 literal, Int64 counter | see §2.7 | `experiments/t15_psi_dtypes.py`, `experiments/t15_psi_dtypes.out.txt`; `diffeval/units/t15_gen.py` |
| predict input check on frames with no row or no column (supports G4, G5, G8; no rule of its own) | `select([])` gives a 0 × 0 frame, `with_columns` of null literals on it gives 0 rows; the check expressions on a frame with no row give 0 bad rows and 0 distinct ids | `experiments/e08_t7_input_check.py`, `experiments/e08_t7_input_check.out.txt` |
| chunking | every float `sum`/`mean` in scope runs on a frame that is one chunk (after `sort`, `group_by`, or a frame built in memory) | E05 (`n_chunks` after sort = 1) |

Known limits of the model (recorded, not worked around): the sign of a zero in `abs`, in min/max
of zeros of opposite sign, in the median and in `np.sort` when zeros of both signs are present;
a frame column that polars keeps internally as a scalar; a literal zero or null-literal operand of `sum_horizontal` (polars leaves the column unchanged, the model adds 0.0); padding a Null-dtype column in `merge_one_to_one` (`Col.append` on two Null columns); a literal, an aggregate or a non-aggregated column passed to `sql_*`, `div`, `sas_log` inside `group_by().agg`; a Boolean input of `sql_sum`; a null in a Date (`.cell`) column; a Null-dtype column (`Pl.litNull`) anywhere but as a branch of `Pl.wto` or next to Float64 operands (`fill_null`, `+`/`*` with Int64, comparison with String, `&`/`|`, `cast(pl.Int64)`, `sum`, `mean` of a Null column: dtype, and for `sum` the value 0.0 instead of null); zero-width frames with a height; two points of form on `def:metrics_run_06_psi_precond`, found by the review of T15 and left as they are (DECISION of the lead, 2026-11-16; neither changes behaviour): it ends with a `-- PORT STATUS: confidence=high todos=0` trailer although §4 says a precondition item carries none, and its statement dependencies include `def:metrics_run_06_psi` although its Lean does not mention the unit, so a later re-submission of the unit clears the precondition; a narrowing stricter than needed in `def:fe_run_00_input_check_precond`, which requires ASCII text in the cells of `MonthlyIncome` and `NumberOfDependents`: by G27 (a) the check is exact for every text (evidence `experiments/e08_t7_input_check.py` and, over all Unicode characters in Python and in polars, `experiments/e09_upper_cells.py`), so non-ASCII cells are excluded there without need; the clause is kept because re-submitting the precondition would clear `def:run` (DECISION of the lead, 2026-11-16); `def:predict_run_00_input_check_precond` has no such clause; zero-row tables; a file written with a header and no data row by feature engineering, train or metrics, whose result is the pair `(file name, [])` with the column names lost (DECISION of the lead, 2026-11-16: these three stages keep pairs; only predict returns triples, §2.7 G4. Example: `judge/scenarios/fix_Q7`, where the validation set has no applicant, so `model_features_validation.csv` is the table `[]`; stated in the comment of `def:run_precond`); multi-chunk columns; integers beyond
2^53; R-F2I; a `group_by` whose key column carries polars' sorted flag (the frame was sorted by the key: polars then sums each group with the select-context kernel, the model always with the Kahan fold; not reachable in the package, whose float group aggregates use keys built by `proc_rank_groups`, which carry no flag; `reviews/B2_r2.md` F1); `sum_horizontal` with 9 or more operands (bracketing outside both values of `full`, and not deterministic). Outside the model altogether: the last bit of `exp` and `log`, which differs between the Lean evaluator's `Float` and polars on a few values per thousand (`RealLike.exp` / `RealLike.log` are abstract in the statements; `reviews/B2_r2.md` F2). The full differential receipt of the preludes is `migration/diffeval/receipts/prelude.tsv`.

Signed zeros and the last bit of `log` and `exp`, as measured by the fuzz pass of 2026-11-16 (ruling of the lead,
2026-11-16: each is a recorded limit of the prelude; nothing is re-submitted and no precondition is
narrowed, because the equality contracts are stated at the reals, where there is no signed zero; receipts
`diffeval/receipts/fuzz_2026-11-16.tsv`):
- min / max of zeros of opposite sign (prelude: the first of the equal values; polars: -0.0 for min, 0.0
  for max). Smallest case: `pd_logistic` [-0.0, 0.0] in one decile gives `min_pd` -0.0, `max_pd` 0.0 in
  polars and (-0.0, -0.0) in the prelude. Reaches `def:metrics_run_04_deciles` (`min_pd`, `max_pd`) and
  through it `def:metrics_run_05_cumulative_lift` and `def:run_py` (`decile_analysis.csv`,
  `printed_cumulative_lift.csv`): 30 of 2,092 fuzzed runs. Not reached through `def:metrics_run_02_ks`
  (154 fuzzed frames with both zeros: equal).
- the median when the middle of the sorted values falls on zeros of both signs: see the first bullet of
  "Known points on the T4 units" below (callers `def:fe_run_02_income_medians`,
  `def:fe_run_02b_medians_all`; seen from 17 values up).
- the running sum (new, found by port-translator-12): polars `cum_sum` starts from 0.0, so a running sum
  whose first non-null values are -0.0 is +0.0; `Pl.cumSumF` starts from the first value and gives -0.0.
  Smallest case: `cum_sum` of [null, -0.0, -0.0, 1.0] is [null, 0.0, 0.0, 1.0] in polars 2.1.0 and
  [null, -0.0, -0.0, 1.0] in the prelude (`experiments/fz_t14_cumsum_zero.py`). Reaches
  `def:metrics_run_05_cumulative_lift` (`cum_defaults`, and from it `cum_capture_rate`, `cum_lift`) when a
  `defaults` is -0.0, that is a decile whose `default_flag` sum is -0.0; the other `cum_sum` calls of the
  package are on integer columns (steps 01 and 02 of metrics), where there is no signed zero.
- the last bit of `log`: the Lean evaluator's `Float.log 0.3783783783783784` ends in ...871, polars and
  `math.log` in ...870. Seen in `def:metrics_run_06_psi` (shares 7/37 and 1/2 in one bin: 1 of 2,200
  fuzzed inputs). Outside the model, as recorded for `log` above.
- the last bit of `exp` (the same recorded sentence as `log`): the Lean evaluator's `Float.exp` differs
  from polars / `math.exp` by one unit in the last place on 5.272105834777667, 123.18413696076126 and
  25.386958717439118. Seen in `def:run_py_py` through `pd_logistic` and `credit_risk_score` (3 of 2,314
  fuzzed runs, seeds 30930, 31316, 31393; the port's frames recomputed from the Lean's `exp` value give
  the Lean digest, `experiments/fz_run_py_py_exp_last_bit.py`). Smallest case: one row, one coefficient
  (MonthlyIncome_missing, -0.0), intercept -25.386958717439118.

Known points on the T4 units (2026-11-16, from the review by port-translator-6; the items stay as
accepted, decision of the lead):

- **Signed zeros in `MonthlyIncome` and the overall median** (`def:fe_run_02b_medians_all`). The
  overall median is the prelude's `Pl.median`, whose recorded limit above is the sign of the result
  when zeros of both signs are present. Such incomes are reachable: the text `-0` passes the input
  check and `input_best32` returns `-0.0`. On 14 lists holding zeros of both signs the Lean
  returned the same sign as the port (e.g. `[0.0, -0.0]` gives `0.0` and `[-0.0, 0.0]` gives `-0.0`
  on both sides); those lists all had 5 values or fewer. **The fuzz pass then found a difference
  inside the precondition** (port-translator-6, seeds 11164 and 11214 of
  `diffeval/units/fz_t4_gen.py`): `MonthlyIncome = [0.0, -1.0 ×7, 1.0, -0.0, 1.0 ×7]` (17 known
  incomes, any `income_medians`) gives an overall median of `0.0` in Python and `-0.0` in the Lean.
  The fuzzer's reading: the prelude keeps input order among equal zeros, polars does so on short
  lists and not at 17 values; it is the recorded limit above, not a fault of the unit's statement.
  The precondition of the unit does not exclude these inputs and its comment does not mention
  them. Probes: `experiments/rev_t4_zero_median.py`, `experiments/fz_t4_zero_median_min.py`.
  **Decision of the lead (2026-11-16), for every caller of the prelude's median at once:** nothing
  is re-submitted and no precondition is narrowed. The equality contracts are stated on the port's
  pipeline at the real numbers, where there is no signed zero, so no theorem covers this case at
  floats; it is a limit of how far the float evaluation mirrors the port. Callers: the port has two
  median calls (`grep "median()" port/credit_risk/*.py`): `feature_engineering.py:172`, the group
  medians of `def:fe_run_02_income_medians` (`Expr.median` in `group_by().agg`), and `:184`, the
  overall median of `def:fe_run_02b_medians_all`. The failing case was measured on the second
  only; the first has the same limit by the same prelude function and is to get its own fuzz run.
  Every later step that reads `median_income` or `overall_median_income` (`def:fe_run_04_imputed`,
  `income_medians.csv`, and through that file the predict stage) carries the sign of that zero.
- **A narrowing the Lean does not need** (`def:fe_run_04_imputed_precond`). The clause
  `0 < credit_cleaned.height` excludes a `credit_cleaned` with no row, on which Python does not
  raise. On a frame with the 15 columns and no row the Lean result equals the port's (same digest
  on both sides), so the clause is stricter than fidelity requires. `run` never reaches step 04
  with no row (the input check stops first). The step 05 precondition has no such clause. Probe:
  `experiments/rev_t4_empty.py`.

## 7. Deviation log

| ID | Date | Deviation | Sanctioned by |
|---|---|---|---|
| DEV-001 | 2026-11-10 | Kit step 00 (feasibility) skipped | PROMPT.md |
| DEV-002 | 2026-11-10 | Kit steps 4–5 (survey build) dissolved into step 3: the server compiles and judges each statement | PROMPT.md |
| DEV-003 | 2026-11-10 | Sign-off gates run through without stopping; evidence recorded in `migration/gates.md` | PROMPT.md |
| DEV-004 | 2026-11-10 | R-F2I: floats converted to integers stay in `α` (the foundation has no `α → Int`) | orchestrator, conservative choice; open item for the user |
| DEV-005 | 2026-11-10 | The polars and numpy preludes live inside `def:ExprOrNum` and `def:FloatArray_` (the server has no item kind for library semantics) | orchestrator; open item for the user |
| DEV-006 | 2026-11-10 | Inventory skeptic round (two reviewers per batch) not run; the inventory was cross-checked only by the joint audit in its own report | orchestrator (budget) |
| DEV-007 | 2026-11-10 | Stress-test re-round folded into the production run of bundle B1 under rulebook v2 | orchestrator |
| DEV-008 | 2026-11-10 | Amendment batches applied by the orchestrator at gates (no human in the loop) | PROMPT.md (gates run through) |
| DEV-009 | 2026-11-10 | Bundle B2 reviewed by one reviewer covering both foci instead of two. CLOSED 2026-11-11: second reviewer run at the user's request (`reviews/B2_r2.md`) | orchestrator (budget) |
| DEV-010 | 2026-11-10 | Form findings on accepted items (missing trailer on `def:Z975`, bracketed trailers) waived: re-submitting a dependency clears its dependents | orchestrator |
| DEV-011 | 2026-11-10 | `def:run_py_py` keeps `medians` before `cs_test` (rule C2 was written after it was accepted and differentially tested; reordering would invalidate its receipts) | orchestrator |
| DEV-012 | 2026-11-10 | B6 (metrics run) and B7/B8 had one line-by-line reviewer each plus one shared end-to-end reviewer on real data, instead of two reviewers per bundle | orchestrator (budget) |
| DEV-013 | 2026-11-16 | `def:run_py_py` returns triples `(file, column names, table)` so that a result with a header and no row is representable (§2.7 G4); the other stages return pairs | lead, confirmed 2026-11-16 |
| DEV-014 | 2026-11-16 | Units whose Python text is unchanged keep their accepted Lean and stored source as they are: only the item's source reference (file, line span) was updated (`update_item_source`, metadata only). So the `-- credit_risk/<file>:<lines>` header inside their Lean, and the stored docstrings of `le`, `ge`, `eq`, are those of the earlier port. Rewriting them would clear every dependent item for no change in meaning. The manifest has the current ranges | orchestrator |
