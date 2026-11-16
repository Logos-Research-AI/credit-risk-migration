# Translation Rulebook — Python (polars 2.1.0, numpy 2.5.4) → Lean 4, blueprint `py-credit-risk-port`

**Version 5** (2026-11-16: batch 7 = G1–G20 for the port as changed on 2026-11-16, §2.7; where §2.7 differs from an earlier section, §2.7 holds). Version 4 (2026-11-10: batch 3 = C1–C3 after the run reviews; batch 1 = A1–A14 after the stress test; batch 2 = B1–B14 after the first reviews; all listed in `migration/amendments.md`). **The preludes are frozen** (B13).

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
letters only. Use them, and state in the precondition that the column names and the text cells of
the checked columns are ASCII (`-- narrowing:` comment). `raw.schema[v] != pl.String` is a match on
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
Result columns (E07): all left columns, then the right key as `age_group_right` (null on an
unmatched row), then the other right columns (suffix `_right` on a clash). Rows as the prelude's
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
| chunking | every float `sum`/`mean` in scope runs on a frame that is one chunk (after `sort`, `group_by`, or a frame built in memory) | E05 (`n_chunks` after sort = 1) |

Known limits of the model (recorded, not worked around): the sign of a zero in `abs`, in min/max
of zeros of opposite sign, in the median and in `np.sort` when zeros of both signs are present;
a frame column that polars keeps internally as a scalar; a literal zero or null-literal operand of `sum_horizontal` (polars leaves the column unchanged, the model adds 0.0); padding a Null-dtype column in `merge_one_to_one` (`Col.append` on two Null columns); a literal, an aggregate or a non-aggregated column passed to `sql_*`, `div`, `sas_log` inside `group_by().agg`; a Boolean input of `sql_sum`; a null in a Date (`.cell`) column; a Null-dtype column (`Pl.litNull`) anywhere but as a branch of `Pl.wto` or next to Float64 operands (`fill_null`, `+`/`*` with Int64, comparison with String, `&`/`|`, `cast(pl.Int64)`, `sum`, `mean` of a Null column: dtype, and for `sum` the value 0.0 instead of null); zero-width frames with a height; zero-row tables; multi-chunk columns; integers beyond
2^53; R-F2I; a `group_by` whose key column carries polars' sorted flag (the frame was sorted by the key: polars then sums each group with the select-context kernel, the model always with the Kahan fold; not reachable in the package, whose float group aggregates use keys built by `proc_rank_groups`, which carry no flag; `reviews/B2_r2.md` F1); `sum_horizontal` with 9 or more operands (bracketing outside both values of `full`, and not deterministic). Outside the model altogether: the last bit of `exp` and `log`, which differs between the Lean evaluator's `Float` and polars on a few values per thousand (`RealLike.exp` / `RealLike.log` are abstract in the statements; `reviews/B2_r2.md` F2). The full differential receipt of the preludes is `migration/diffeval/receipts/prelude.tsv`.

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
| DEV-013 | 2026-11-16 | `def:run_py_py` returns triples `(file, column names, table)` so that a result with a header and no row is representable (§2.7 G4); the other stages return pairs | orchestrator; to be confirmed by the lead |
