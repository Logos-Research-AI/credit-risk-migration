# Translation Rulebook — SAS 9.4 → Python 3.13 (polars)

> **The meta-rule: if two agents could answer a question differently, the answer goes
> in this file.** Read by every implementer, reviewer and fixer before touching code.
> Read-only inside any loop: amendments are queued for the human and applied between
> batches.

**Status: v1.4, signed off 2026-11-05.** Items marked **[DECIDED]** were
policy calls made by the user at that gate (all five: the proposed defaults).
v1.1 = v1.0 + amendments A1–A8 (`migration/rulebook-amendments.md`), approved by the
user at the prompt 02 first-20-rows gate and applied on their authorization.
v1.2 = v1.1 + amendments A9, A11–A31 (A10 withdrawn, replaced by A20), approved by the
user at the prompt 02 final gate ("Ok" to the recommendations) and applied on their authorization.
v1.3 = v1.2 + stress-test round-1 amendments S1–S12 and experiment X05
(`migration/stress-test/amendment-queue.md`), applied by the orchestrator under the user's
standing instruction to decide every remaining gate (2026-11-05).
v1.4 = v1.3 + post-parity notes (prompt 06): ODDSRw.d, the complete-case rule, literal/column
division, fail-loud non-convergence. Experiment X06 verified the printing rules
(`migration/post-parity/classification.md`).

Read this whole document before writing any code. The judge (`judge/README.md`) is the
exit condition; this rulebook is how translations get there.

## 0. Scope and posture

- **Structure-preserving.** One `.sas` program → one Python module, same steps in the
  same order, same intermediate datasets (as polars DataFrames with the same names,
  lower-cased: `work.credit_features` → `credit_features`), same output files. You are
  translating, not improving. Two DATA steps with identical logic stay two code blocks at
  their own positions with literal names; a shared Python function exists only where SAS has
  a `%macro` (S9). The duplicated feature engineering in `predict.sas` stays
  duplicated (deduplication is a post-parity change, prompt 06).
- **One forced structural change:** SAS WORK-library state shared across programs
  becomes a file. The only instance is the item store `work.logit_model`
  (train.sas:90 `store`, predict.sas:208 `restore`) → `model.json` in the output folder
  (§2, "PROC LOGISTIC store / PROC PLM restore").
- **Cheap referee.** Python has no compile step; the referee is
  `ruff check` + `pyright --strict` on the package, seconds per run. Per README Step 4
  this dissolves Step 4 into Step 3: implementers run both inside their loop, and a
  draft that does not pass both is not done. **[DECIDED]** Yes — the human
  removes the lint/typecheck denies from `.claude/settings.json` at the Step 3 gate.
  Running the pipeline or the judge stays out of the loop until Step 5/6.
- **Fidelity over performance.** Mark known slow-but-faithful translations
  `PERF(port):` and move on.
- **The judge contract is the interface.** Every module must produce exactly the files,
  columns, column order and printed formats listed in `judge/README.md` "Contract".

## 1. Ecosystem adoption — what we use and what we ban

| Area | Decision | Why |
|---|---|---|
| Python | 3.13, managed by uv, `pyproject.toml` at repo root | user decision (feasibility gate) |
| DataFrames | **polars** only. `pandas` **BANNED** | user decision; one data model |
| Numerics | **numpy** for linear algebra (model fitting); **scipy** only for `scipy.stats.chi2.sf` (p-values) | stepwise needs score/Wald tests by hand |
| Model libraries | `statsmodels`, `scikit-learn` **BANNED** **[DECIDED]** | hidden defaults (sklearn's L2 penalty was caught by the judge in review C); SAS's stepwise rules must be explicit code (§2) |
| Plotting | none. PROC SGPLOT is not ported (§2) **[DECIDED]** | no judged output; no matplotlib dependency |
| Other third-party deps | NONE without a row here | |
| CSV I/O | read raw inputs with `pl.read_csv(..., infer_schema=False)` (all text) and convert explicitly per §2 "PROC IMPORT"; write outputs with the shared writer `sas_compat.write_sas_csv` (§4) only. The judge's `compare.sas_best12` is plain-notation only and is **never** copied as the port's printer (A15) | type guessing and number printing are SAS behaviors we must emulate, not delegate |
| Floating point | IEEE double (`pl.Float64`) for measured values, like SAS. Integer-literal category codes from `when` chains stay polars Int32 and are never cast; a join key is built by the same chain on both sides (A28) | `.then(1.0)` on one side → Int32 vs Float64 key → SchemaError |
| Row order | `maintain_order=True` on every `group_by`, `unique`, `join`; sorts are stable (`maintain_order=True`) | KS and ranks depend on order within ties (judge README findings) |

## 2. Constructs with no Python equivalent — one canonical mapping each

Helpers named `sas_compat.*` live in the shared module (§4). An implementer who invents a
second mapping for a listed construct is violating a rule; an unlisted construct is
flagged for this table and handled by the UNKNOWN rule.

### Values and expressions

| SAS construct | Canonical Python translation | Notes / evidence |
|---|---|---|
| numeric missing `.` | polars `null` (never NaN) | NaN is not SAS missing; `is_nan` never appears |
| comparison with a possibly-missing operand: `x < c`, `x <= c`, `x > c`, `x >= c`, `x = c` | `sas_compat.lt/le/gt/ge/eq(x, c)`: **missing is smaller than every number**, so `. < 2500` is **true**, `. > 30` is false, `. = .` is true. Result is a **non-null `pl.Boolean`** (A1) | SAS rule; mutation `predict_null_compare_false` (judge) is exactly the polars default `null < 2500 → null → false`. **Which form (A2):** the helpers are mandatory where the inventory classifies the operand `MISSING_NULLABLE`; a **plain polars comparison** is required where it says `MISSING_NEVER` (the row must prove never-missing for every input the program can receive) |
| boolean assignment `flag = (cond);` | `sas_compat.flag(cond)`: any Boolean expression (helper or plain comparison) → Int64 0/1. The only way to make a 0/1 numeric (A1) | SAS stores 0/1 numerics; exported as `0`/`1` |
| `if A then x=1; else if B then x=2; else x=3;` | one `pl.when(A).then(1).when(B).then(2).otherwise(3)` chain; each condition is a helper or a plain comparison per the inventory's `MISSING_NULLABLE` / `MISSING_NEVER` classification (A2) | preserves first-match order and missing semantics |
| arithmetic `a + b`, `a * b`, `a / b` | plain polars arithmetic (null propagates, as SAS), and plain `/` **only column by column**. Any division whose divisor is a scalar, a literal or an aggregate (`x / 100`, `x / n`, `x / x.sum()`) → `sas_compat.div(a, b)`: element-wise IEEE division (numpy `np.divide`), missing → missing, /0 → missing (A13). Also use it wherever the inventory says a divisor can be 0 | polars 2.1 computes `col / scalar` as `col * (1/scalar)` depending on chunk layout; SAS divides like IEEE (experiment X04, `migration/experiments/x04_findings.md`) |
| proportions: shares and rates (`count/n`, capture rate, lift, PSI shares) | aggregate counts/sums first, divide **after** the aggregation (A7), and with `sas_compat.div` when the divisor is a scalar (A13) | without A13, PSI prints `1.540744E-33` instead of `0` even after aggregation |
| `sum(a, b, ...)` | `sas_compat.sas_sum(a, b, ...)`: ignores missing; all missing → missing | NOT `a + b` |
| `min(a, b)`, `max(a, b)` | `sas_compat.sas_min/sas_max`: ignore missing | NOT `pl.min_horizontal` without checking null handling (it also ignores nulls — allowed only via the helper) |
| `log(x)` | `sas_compat.sas_log(x)`: x ≤ 0 or missing → missing | |
| `exp(x)` | `sas_compat.sas_exp(x)`: overflow → missing (S1; X05: `exp(1000)` is `.`) | polars gives inf → pd 0 → grade A where SAS gives grade F |
| numeric truthiness `if x then` | `pl.col(x) != 0` inside the `when` (missing and 0 are false) (A29) | |
| `round(x)` | `sas_compat.sas_round(x)`: **half away from zero with SAS's fuzz**: \|frac − 0.5\| ≤ 1e-12·max(1,\|x\|) counts as half; \|x\| ≥ 2^52 unchanged (X05) | Python `round` is half-to-even: BANNED for SAS `round`. X05: 2.49999999999999 → 3, 2.4999999999 → 2 |
| `input(s, best32.)` | `sas_compat.input_best32(s)`: numeric text → float, anything else (`"NA"`, `""`, overflow) → missing; a column already imported as numeric passes through (S2) | logs nothing |
| `missing(x)` | `x.is_null()` | |
| `today()` + `format date9.` | `f"{d.day:02d}{MONTHS[d.month - 1]}{d.year}"` with a fixed `MONTHS = ("JAN", ..., "DEC")`, never `strftime("%b")` (locale-dependent) (A16) | e.g. `05NOV2026` |
| macro variables `%let`, `&x` | module-level constants or function parameters | `&output_path` / `&data_path` become CLI arguments (§4) |
| `%macro name(a, b); ... %mend;` + calls | a Python function with the same name and macro parameters, plus the WORK datasets the body reads as DataFrame parameters; it returns the datasets it creates; called at the same points (A23) | metrics_calculation.sas:122 `%confusion_metrics` |
| `select ... into :mvar` | a Python scalar holding what SAS stores: numeric values without `format=` are **BEST8. text**, so `float(sas_compat.sas_best(x, 8))` (A9) | experiment X03: mean 0.0670666… → `0.066667`, and later arithmetic sees the rounded value |
| `%put NOTE: ...` | `print(...)` with the same text | |
| `title "...";` | dropped | listing-only |
| normal quantile in CIs | the single constant `sas_compat.Z975 = 1.959963984540054` (A25) | odds-ratio and ROC CIs |

### DATA step and PROC SQL

| SAS construct | Canonical Python translation | Notes |
|---|---|---|
| `data out; set in; ... run;` | `out = in.with_columns(...)` in statement order; a later statement that reads a variable assigned earlier in the same step must see the new value → split into successive `with_columns` calls. Repeated reassignment of ONE variable (e.g. `financial_health`) may instead be one nested expression that applies the statements in order (A30). A copy step that only attaches a format (`data x_export; set x; format _numeric_ best12.;`) may be elided: the writer's default is BEST12. (A31) | SAS evaluates statements sequentially per row |
| `retain` + `end=eof` accumulation | an explicit aggregation over the frame producing the single output row | train.sas:132 training_metrics; behavior on missing cells as the source |
| `keep` / `drop` / `rename` | `keep` keeps the **input** column order, not the order written in the statement: `select([c for c in df.columns if c in KEEP])` (A12); `drop` / `rename` as polars; new columns are appended in order of first assignment | column order is judged |
| `merge a b ...;` (no BY) | `sas_compat.merge_one_to_one(a, b, ...)`: rows = the longest input; values from a shorter input are **missing** on the extra rows (not repeated), written as empty fields (A6, S5). No translation writes its own merge | train.sas:366 model_summary; experiment X01a (`migration/experiments/x01_merge_and_alias.lst`) |
| PROC SQL `select ... from a left join b on ...` | `a.join(b, on=..., how="left", maintain_order="left")`, plus `nulls_equal=True` where a key can be missing (SAS SQL matches missing keys) (A11) | output row order is not guaranteed in SAS; the judge matches by key |
| PROC SQL inner join | `a.join(b, on=..., how="inner", maintain_order="left", nulls_equal=True)` (A26) | metrics PSI join |
| PROC SQL `median(x)` with `group by` | `pl.col(x).median()` over non-missing values, `group_by(..., maintain_order=True)` | even counts average the two middle values, like SAS |
| PROC SQL aggregates `sum/mean/min/max(x)` | `sas_compat.sql_sum/sql_mean/sql_min/sql_max(expr)`: **missing over zero rows or all-missing input** (S10; X05) — never bare polars `.sum()` (0 over zero rows) | an empty PSI join prints `0.0000` where SAS prints an empty field |
| PROC SQL `calculated name` | reuse the expression / column computed earlier in the same select | |
| PROC SQL `case when ... end` | `pl.when` chain; conditions as in the `if/else` row (A2) | |
| PROC SQL remerge (`select max(x), y from t where x = (select max(x) ...)`) | filter to the rows equal to the max, keep every such row | metrics_calculation.sas:107 KS can return several rows on ties |

### Procedures

| SAS construct | Canonical Python translation | Notes |
|---|---|---|
| PROC IMPORT (csv, `getnames=yes`) | `sas_compat.proc_import_csv(path, guessingrows=20 or None)`: column type = numeric if every one of the first `guessingrows` data values parses as a number, else character with length = longest of those values, **later values truncated to that length** (`BUG(port)`); a column whose first `guessingrows` values are **all empty** is character of length 1 (A3: `SeriousDlqin2yrs $1.` in cs-test.csv); character values that are not numbers stay text; empty header → `VAR1`; names truncated to 32 characters; hyphens kept | feature_engineering.sas:28 uses the default (20) → `MonthlyIncome` becomes `$5.` and 77 incomes ≥ 100,000 are truncated (judge README finding). predict.sas:27-33 uses `guessingrows=max` at :32 (None = all rows) (A31) |
| PROC SURVEYSELECT samprate=0.7 seed=42 | **not reproduced.** `feature_engineering.run(data_dir, output_dir, *, split_ids: Path)` reads the training `row_id`s from a CSV with a `row_id` column (from the reference) and marks `selected` from it (A27) | SAS's split depends on unguaranteed SQL row order (judge README); `BUG(port)` |
| PROC LOGISTIC `selection=stepwise slentry=0.05 slstay=0.05` (descending) | `sas_compat.stepwise_logistic(...)`, written once, over the candidates in MODEL statement order, modelling P(default_flag = 1) (A5): (1) intercept-only start; after every step test **removal first, then entry**. (2) Removal: Wald χ² for each effect in the model; remove the one with the **smallest χ²** if its p > slstay (ties: first in MODEL order), one per step. (3) Entry: for each candidate not in the model, in MODEL order, **skip it if aliased with the current model** (relative residual V/(z′Wz) < 1e-8, V = its residual variance after projecting on the model's columns in the information metric; decided per step, never by pre-excluding columns); else score χ² at the current fit: SAS's statistic over ALL parameters of the enlarged model, g′I⁻¹g for the model's own score g plus (U − v′I⁻¹g)²/V for the candidate (v = its information with the model's columns); g is not zero, since the fit stops at SAS's convergence test or at a separation (U²/V alone is not SAS's number: reference data step 13, 8.8017 against 8.7885); enter the **largest χ²** (DF = 1; strict >, so ties go to the **first in MODEL order**; never select by smallest p, which underflows) if its p < slentry. (4) Stop when nothing enters or the best entry is the effect just removed; if nothing ever enters, the intercept-only model is the final model and is fitted, stored and exported (S8). Every fit is SAS's iteration (next row); a step whose fit is separated (complete or quasi-complete) is **kept as SAS keeps it**: SAS warns and continues with the estimates of its last iteration (`sas_compat._fit_as_sas`: checked from the 8th iteration on), the step's tables are computed from them and the selection goes on to the removal test (owner's decision 2026-11-16; `small-inputs.md` (c)). A fit that neither converges nor separates in SAS's 25 iterations raises an error. Observations with a missing value in ANY MODEL variable are excluded from the fit (`TODO(port)`: unreachable here, FE outputs are never missing; diff D22) | the judge compares the 24-step path exactly (`stepwise_summary.csv`); `migration/experiments/x02_stepwise_reference.py` reproduces it; inventory row for train.sas stepwise |
| model fitting inside PROC LOGISTIC | **SAS's own iteration, stopped where SAS stops it** (`sas_compat._fit_as_sas`; owner's decision 2026-11-17, which replaces A17's Newton–Raphson from all-zero coefficients to full convergence): Fisher scoring on numpy float64 **from the intercept-only estimates** (intercept log(events / non-events), every other coefficient 0), at most 25 iterations. A step that would lower the log likelihood is retaken with SAS's ridge: the diagonal of the information matrix times 1 + 1e-4·4^j, j one up until the log likelihood is not lower; j is kept through the fit and goes one down after an iteration whose first ridge was accepted. After each iteration SAS's convergence test, GCONV: g′I⁻¹g / (\|log L\| + 1e-6) < 1e-8 at the new estimates; **the estimates of that iteration are the fit's**, and every table (Wald tests, entry score tests, covariance, probabilities, scores) is computed at them. Then, from the 8th iteration, the separation tests (post-parity note below). The intercept-only model is log(events / non-events). A fit that neither converges nor separates in 25 iterations raises an error | Experiment X17 (`experiments/x17_*`): ITPRINT on the reference feature file, 12 row subsets of it and 5 generated seeds, 211 steps, 393 ridged iterations, every iteration line and stop iteration reproduced; the 14 converged steps of `out/separation/sas`. With it the port's outputs on the reference data are SAS's text in every cell but the last printed digit of 25 cells (`DECISIONS.md`). Not settled: the first ridge (none below 0.0064 was needed), a step that leaves the log likelihood exactly equal, a ridge on a separated fit |
| ODS tables of PROC LOGISTIC (`ParameterEstimates`, `ModelBuildingSummary`, `FitStatistics`, `GlobalTests`, `RSquare`, `Association`, `OddsRatios`, `LackFitPartition`, `LackFitChiSq`, `Classification`) | computed explicitly as the inventory row for each judged file decides (`sas_compat.classification_table` for the ctable, `sas_compat.hosmer_lemeshow` for HL), written as **pre-rendered text columns**, every numeric column with the STORED format's width and decimals (e.g. chi-square 10.4, HL expected 8.2, ctable 5.3 / 5.1; S7). The procedure helpers' return conventions (column names, percent units, `names[0]='Intercept'`, `loglik`) are fixed by their `sas_compat` docstrings (S4). Printed text = the **stored formats of the ODS output dataset that PROC EXPORT applies** (export code in `judge/reference/listings/*.log`), never the listing's template format (A19, A20) | listing InterceptOnly `51477.521` vs exported `51478` |
| ODS variable names in coefficient tables | truncated to 20 characters (`credit_utilization_c`) | |
| `output out= predicted=` | pd for each training row from the final model | |
| PROC LOGISTIC `store` / PROC PLM `restore ... score predicted=` | train writes `model.json` = `{"intercept": b0, "coefficients": {full_variable_name: b}}`; predict reads it, computes the linear predictor η = b0 + Σ bᵢxᵢ (missing if any xᵢ missing), then pd = 1/(1+exp(−η)) as the SAS code does | the only cross-program session state (depmap) |
| PROC LOGISTIC `nofit` + `roc` (ROCAssociation) | `sas_compat.roc_association(y, score)`: Area = Mann–Whitney AUC with ties counted ½; StdErr and CI per SAS's DeLong method; Somers' D, Gamma, Tau-a | inventory row confirms SAS formulas |
| ODS `Association` table of the fitted model | over all event × non-event pairs on the final model's pd, no binning; a pair is **tied when \|pd_event − pd_nonevent\| ≤ 1e-8** (SAS tie fuzz); c = (C + T/2)/pairs, Somers' D = (C − D)/pairs, Gamma = (C − D)/(C + D), Tau-a = (C − D)/(n(n − 1)/2) (A8) | judge compares Percent Tied with an absolute 1e-5 percentage-point tolerance (Q1, signed off 2026-11-05): a converged port gets 283 ties vs SAS's 280 |
| PROC RANK `groups=k` (`descending`) | `sas_compat.proc_rank_groups(x, k, descending)`: rank with ties = mean, group = floor(rank·k/(n+1)) | reproduces SAS exactly on edge scenario a (judge README) |
| PROC FREQ `tables a*b / out=` | `group_by([a, b], maintain_order=True).len()` → `COUNT` (Int64), `PERCENT = sas_compat.div(100 * COUNT, N)` (A22), sorted by a, b | `printed_confusion_*` |
| PROC SORT `by x` | `sort(x, maintain_order=True)` (stable, missing first) | SAS's default EQUALS keeps ties in input order |
| PROC EXPORT dbms=csv | `sas_compat.write_sas_csv(df, path, formats={col: fmt})`. Unformatted numerics as BEST12. via `sas_compat.sas_best12`: plain notation, rounded **half up from the value's 15-significant-digit form** (A18), and **E-notation for 0 < \|x\| < 1e-5** (mantissa rounded to fill 12 characters, trailing zeros stripped, e.g. `9.670322E-6`) (A15). Formatted columns: `w.d` and `percentw.d` round half away from zero from the 15-significant-digit form (A24) and keep width w, so `percent8.2` prints `5.00%` but `100.0%` (A14); negatives keep their sign even when they round to zero (`-0.0000`), PERCENTw.d prints negatives in parentheses (`( 5.00%)`), and a value that cannot fit w.d falls back to BESTw. (`1.2346E8` at 8.4); BESTw. switches to E-notation when plain notation cannot show the value within w (`15E-6` at BEST6.) (X05); `date9.` per §2. Missing numeric → empty field. **str columns are written verbatim** (empty string → empty field): model-statistics files are pre-rendered with `sas_compat.sas_d8`, `sas_d12_3`, `sas_pvalue` (PVALUE6.4, `<.0001`), `sas_best(x, w)` and ODS's special missing `_` (A20) | X04: 39 of 149,987 cells still differ by 1 unit in the 12th character (within judge tolerance) |
| `format x best12.` / `format x 8.4` / `percent8.2` / `date9.` attached to a column | the `formats=` argument at export time; values stay full precision in memory | formats change printing only |
| PROC MEANS / PROC FREQ (printed) / PROC PRINT / PROC CONTENTS / PROC SGPLOT | **not ported**; replaced by a one-line comment `# listing-only: PROC X <what it showed>` **[DECIDED]** | not judged (judge README "Not judged") |
| datasets the judge exports although the SAS code only prints them (`judge/run_sas.py` EXPORT_AFTER: roc_train, roc_valid, confusion_matrix_train, confusion_matrix, roc_stats, cumulative_lift, psi_calculation) | `write_sas_csv` of the dataset's FINAL state to `printed_<name>.csv` (the judge contract's file name) with its stored formats (A21) | judged files: dropping them fails the judge |

**Post-parity notes (v1.4, prompt 06).**
- ODDSRw.d → `sas_compat.fmt_oddsr` (`>999.999` / `<0.001` outside range; X06).
- Rows with a missing value in ANY MODEL variable are excluded from the fit AND from every statistic of the fitted model: fit statistics, global tests, Association, HL, ctable. The ROC `nofit` analyses use the scored dataset.
- `literal / column` (e.g. `1 / (1 + sas_exp(-eta))`) is column-wise division and may stay plain `/` (A13 applies to scalar or aggregate DIVISORS).
- A logistic fit that is separated follows SAS (owner's decision 2026-11-16, which withdraws the deliberate stop recorded here in v1.4): the port warns, keeps the estimates of the iteration at which SAS declares the separation, and continues; the variable is removed at the next step if its Wald test is not significant. SAS declares complete separation at the 8th iteration when no observation is on the wrong side of 0.5 (not when every probability is 0.95 or above), and quasi-complete separation from the 8th iteration on by the 0.95 and 5000 tests of `sas_compat._fit_as_sas`; the tests apply to every fit that SAS's own iteration (GCONV = 1E-8) has not converged by then, also one whose maximum likelihood estimate exists. Evidence: `small-inputs.md` (c), SAS runs `judge/runs/gen_s16`, `s17`, `s18`, `s20`, `s21`, `s24`, `small_sep60`, and the ITPRINT runs of `out/separation/sas`. A fit that does not converge for another reason still raises an error.
- Unverified, unreachable on every judged input: the training pd of a row missing only a NON-selected candidate (SAS's OUTPUT scores it if every selected effect is present; FE outputs are never missing), and `fmt_oddsr` at widths other than 8.3.
- BEST, D8., D12.3 and PERCENT printing is verified against X06 cells. BESTw. never exceeds w.

**Helper verification (A31).** `sas_compat.le` and `sas_compat.eq` have no site in the inventory: keep them, marked "no site; unverified". Helper branches that no judged input reaches get explicit cases in the Step 2 `sas_compat` review: `sum(., 1) = 1`, `sum(., .) = .`, `min(., 200) = 200`, `log(0) = .`, `input('') = .`, and the D12.3 magnitudes never observed (100 ≤ \|x\| < 1e4, \|x\| < 1e-5).

**The BUG rule:** when the source's behavior is itself defective, reproduce it
bug-for-bug and mark the site `BUG(port):` with a one-line repro. Known instances:
MonthlyIncome truncation (PROC IMPORT guessing), PSI always 0 (per-set deciles),
test-set median imputation, unguaranteed split. Fixes ship only after parity (prompt 06).

**The UNKNOWN rule:** when neither this table nor the inventory decides a case,
translate to the most conservative representation, mark `TODO(port):` with the open
question, and keep moving.

There is no allocation-guard / precondition-guard distinction in this codebase (no
shared error sentinels); SAS's invalid-argument notes become missing values per the
helpers above.

## 3. The sanctioned escape hatch

- There is no `unsafe`. The pressure valve is `# type: ignore[<code>]  # TODO(port): <why>`
  for a pyright error the translation cannot express; nothing else silences the referee.
- Greppable markers, exact format: `TODO(port):`, `PERF(port):`, `BUG(port):`.

## 4. Naming and output paths

- Source `<name>.sas` → target `credit_risk/<name>.py`. One source, one target:
  `feature_engineering.sas` → `credit_risk/feature_engineering.py`, `train.sas` →
  `credit_risk/train.py`, `metrics_calculation.sas` → `credit_risk/metrics_calculation.py`,
  `predict.sas` → `credit_risk/predict.py`.
- **Shared home module:** `credit_risk/sas_compat.py` owns every `sas_compat.*` helper in
  §2. It has no SAS source; it is written once before the fan-out (Step 2 pilot) and
  reviewed like a translation. Translations import it as `from credit_risk import sas_compat`.
  No translation defines its own copy of a helper.
- **Stage entry points (A27):** `feature_engineering.run(data_dir: Path, output_dir: Path, *, split_ids: Path)`;
  `train.run(input_dir: Path, output_dir: Path)`; `metrics_calculation.run(input_dir: Path, output_dir: Path)`;
  `predict.run(input_dir: Path, output_dir: Path, *, data_dir: Path)`. `input_dir` is the folder holding the previous
  stage's outputs. `run()` creates `output_dir` (`mkdir(parents=True, exist_ok=True)`) before writing (S12). Each module exposes its `run(...) -> None`
  and `if __name__ == "__main__":` argparse with `--data-dir`, `--input-dir`,
  `--output-dir` replacing `&data_path` / `&output_path`; feature_engineering also
  takes `--split-ids <csv of row_id>`. Paths like `/home/u64352077` never appear.
- Package: `credit_risk/__init__.py` (empty). Tests: none in the package; the judge is
  the test suite.

## 5. The gap inventory

Decisions about **SAS semantics Python does not share** — missing-value comparisons,
SAS function behavior on missing/invalid input, type guessing, printed formats, PROC
defaults and output order — are **not made by implementers**. They are looked up:
`migration/inventory.tsv`, one row per site. If your site isn't in the inventory, that's
an inventory bug — flag it, apply the UNKNOWN rule, keep moving.

## 6. Per-file obligations

Every translated file ends with a status trailer:

```
# PORT STATUS: confidence=high todos=0
```

Literally that format, no brackets: `confidence` is one of high, medium, low; `todos` is the
`grep -c 'TODO(port)'` count (S3).

Reviewers check the trailer against the file's actual `TODO(port)` count.

## 7. Deviation log

| ID | Date | Deviation | Sanctioned by |
|---|---|---|---|
| DEV-001 | 2026-11-05 | 00b steps 1–2 (categorize/rewrite tests) not applicable: 0 tests in repo; replaced by real-world and edge-case scenarios | user (judge sign-off) |
| DEV-002 | 2026-11-05 | 00b reviewers A and B reviewed code edited during their review; mitigated by review C on the final state | user (judge sign-off) |
| DEV-003 | 2026-11-05 | 00b review C's fixes verified by self-test + full re-validation, not by a fourth reviewer | user (judge sign-off) |
| DEV-004 | 2026-11-05 | Prompt 01 skeptic samples: the codebase has 4 files, so each reviewer takes 2 (all files covered) instead of 20 | user, 2026-11-05 |
| DEV-005 | 2026-11-05 | Prompt 02: inventory row 14 (stepwise) was revised a second time instead of being marked UNKNOWN after its one resubmission, because the reviewer named the single missing sentence (tie-break by MODEL order) and `migration/experiments/x02_stepwise_reference.py` (re-run independently by the orchestrator) reproduces SAS's 24-step path exactly | user, 2026-11-05 (prompt 02 first-20 gate) |
| DEV-006 | 2026-11-05 | Prompt 02 batch 1: the two skeptic reviewers took disjoint halves, so each of the first 20 rows had ONE reviewer, not two. Mitigation: the fan-out used two independent reviewers per row, and the joint audit re-read the batch-1 rows (6 defects fixed, none changing computed values in the FE/predict half) | user, 2026-11-05 (prompt 02 final gate) |
| DEV-007 | 2026-11-05 | `.claude/settings.json` (kit guardrails) is NOT installed. The kit forbids the agent from installing it; the user waived the stop with a standing instruction to run every remaining step without asking. Consequence: no deny rules; the orchestrator keeps the expensive commands (judge, SAS, pipeline runs) out of every implementer and reviewer loop by brief | user's standing instruction, 2026-11-05 |
| DEV-008 | 2026-11-05 | Prompt 03: 'translator A' (follows the rulebook, cites rules) is the pilot implementer's first draft, not a separate fourth translation of the same 3 files; the diff inspector compares that draft (before review fixes) with native translator B | auto-approved under the user's standing instruction |
| DEV-009 | 2026-11-05 | Prompt 03 re-round (a fresh-file bakeoff plus a pilot against the amended rules) folded into Step 3: only one fresh file remains (feature_engineering.sas), and Step 3 runs the full production pipeline on all 4 files under v1.3 with the judge as exit condition. The round-1 pilot already passes every staged judge run | auto-approved under the user's standing instruction |
