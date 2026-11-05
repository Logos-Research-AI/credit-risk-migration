# Translation Rulebook — SAS 9.4 → Python 3.13 (polars)

> **The meta-rule: if two agents could answer a question differently, the answer goes
> in this file.** Read by every implementer, reviewer and fixer before touching code.
> Read-only inside any loop: amendments are queued for the human and applied between
> batches.

**Status: v1.0, signed off by the user 2026-11-05.** Items marked **[DECIDED]** were
policy calls made by the user at that gate (all five: the proposed defaults).

Read this whole document before writing any code. The judge (`judge/README.md`) is the
exit condition; this rulebook is how translations get there.

## 0. Scope and posture

- **Structure-preserving.** One `.sas` program → one Python module, same steps in the
  same order, same intermediate datasets (as polars DataFrames with the same names,
  lower-cased: `work.credit_features` → `credit_features`), same output files. You are
  translating, not improving. The duplicated feature engineering in `predict.sas` stays
  duplicated (deduplication is a post-parity change, prompt 06).
- **One forced structural change:** SAS WORK-library state shared across programs
  becomes a file. The only instance is the item store `work.logit_model`
  (train.sas:93 `store`, predict.sas:208 `restore`) → `model.json` in the output folder
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
| CSV I/O | read raw inputs with `pl.read_csv(..., infer_schema=False)` (all text) and convert explicitly per §2 "PROC IMPORT"; write outputs with the shared writer `sas_compat.write_sas_csv` (§4) only | type guessing and number printing are SAS behaviors we must emulate, not delegate |
| Floating point | IEEE double (`pl.Float64`) everywhere, like SAS | |
| Row order | `maintain_order=True` on every `group_by`, `unique`, `join`; sorts are stable (`maintain_order=True`) | KS and ranks depend on order within ties (judge README findings) |

## 2. Constructs with no Python equivalent — one canonical mapping each

Helpers named `sas_compat.*` live in the shared module (§4). An implementer who invents a
second mapping for a listed construct is violating a rule; an unlisted construct is
flagged for this table and handled by the UNKNOWN rule.

### Values and expressions

| SAS construct | Canonical Python translation | Notes / evidence |
|---|---|---|
| numeric missing `.` | polars `null` (never NaN) | NaN is not SAS missing; `is_nan` never appears |
| comparison with a possibly-missing operand: `x < c`, `x <= c`, `x > c`, `x >= c`, `x = c` | `sas_compat.lt/le/gt/ge/eq(x, c)`: **missing is smaller than every number**, so `. < 2500` is **1**, `. > 30` is 0, `. = .` is 1. Result is Int8 0/1, never null | SAS rule; mutation `predict_null_compare_false` (judge) is exactly the polars default `null < 2500 → null → false`. Use the helpers on EVERY comparison whose operand can be missing (inventory says which) |
| boolean assignment `flag = (cond);` | `sas_compat.flag(cond)` → Int64 0/1 | SAS stores 0/1 numerics; exported as `0`/`1` |
| `if A then x=1; else if B then x=2; else x=3;` | one `pl.when(A).then(1).when(B).then(2).otherwise(3)` chain, conditions built with the comparison helpers | preserves first-match order and missing semantics |
| arithmetic `a + b`, `a * b`, `a / b` | plain polars arithmetic (null propagates, as SAS) | division by zero: SAS → missing + note; polars → inf. Use `sas_compat.div(a, b)` wherever the inventory says a divisor can be 0 |
| `sum(a, b, ...)` | `sas_compat.sas_sum(a, b, ...)`: ignores missing; all missing → missing | NOT `a + b` |
| `min(a, b)`, `max(a, b)` | `sas_compat.sas_min/sas_max`: ignore missing | NOT `pl.min_horizontal` without checking null handling (it also ignores nulls — allowed only via the helper) |
| `log(x)` | `sas_compat.sas_log(x)`: x ≤ 0 or missing → missing | |
| `exp(x)` | `pl.Expr.exp()`; missing → missing | |
| `round(x)` | `sas_compat.sas_round(x)`: **half away from zero** | Python `round` is half-to-even: BANNED for SAS `round` |
| `input(s, best32.)` | `sas_compat.input_best32(s)`: numeric text → float, anything else (`"NA"`, `""`) → missing | logs nothing |
| `missing(x)` | `x.is_null()` | |
| `today()` + `format date9.` | `datetime.date.today().strftime("%d%b%Y").upper()` | e.g. `05NOV2026` |
| macro variables `%let`, `&x` | module-level constants or function parameters | `&output_path` / `&data_path` become CLI arguments (§4) |
| `%macro name(a, b); ... %mend;` + calls | a Python function with the same name and parameters, called at the same points | metrics_calculation.sas:120 `%confusion_metrics` |
| `select ... into :mvar` | a Python scalar variable | |
| `%put NOTE: ...` | `print(...)` with the same text | |
| `title "...";` | dropped | listing-only |

### DATA step and PROC SQL

| SAS construct | Canonical Python translation | Notes |
|---|---|---|
| `data out; set in; ... run;` | `out = in.with_columns(...)` in statement order; a later statement that reads a variable assigned earlier in the same step must see the new value → split into successive `with_columns` calls | SAS evaluates statements sequentially per row |
| `retain` + `end=eof` accumulation | an explicit aggregation over the frame producing the single output row | train.sas:132 training_metrics; behavior on missing cells as the source |
| `keep` / `drop` / `rename` | `select` / `drop` / `rename`, preserving SAS column order rules: new columns are appended in order of first assignment | column order is judged |
| `merge a b ...;` (no BY) | positional horizontal concat of single-row frames | train.sas:366 model_summary |
| PROC SQL `select ... from a left join b on ...` | `a.join(b, on=..., how="left", maintain_order="left")` | output row order is not guaranteed in SAS; the judge matches by key |
| PROC SQL `median(x)` with `group by` | `pl.col(x).median()` over non-missing values, `group_by(..., maintain_order=True)` | even counts average the two middle values, like SAS |
| PROC SQL `calculated name` | reuse the expression / column computed earlier in the same select | |
| PROC SQL `case when ... end` | `pl.when` chain with comparison helpers | |
| PROC SQL remerge (`select max(x), y from t where x = (select max(x) ...)`) | filter to the rows equal to the max, keep every such row | metrics_calculation.sas:107 KS can return several rows on ties |

### Procedures

| SAS construct | Canonical Python translation | Notes |
|---|---|---|
| PROC IMPORT (csv, `getnames=yes`) | `sas_compat.proc_import_csv(path, guessingrows=20 or None)`: column type = numeric if every one of the first `guessingrows` data values parses as a number, else character with length = longest of those values, **later values truncated to that length** (`BUG(port)`); character values that are not numbers stay text; empty header → `VAR1`; names truncated to 32 characters; hyphens kept | feature_engineering.sas:28 uses the default (20) → `MonthlyIncome` becomes `$5.` and 77 incomes ≥ 100,000 are truncated (judge README finding). predict.sas:28 uses `guessingrows=max` (None = all rows) |
| PROC SURVEYSELECT samprate=0.7 seed=42 | **not reproduced.** `feature_engineering.run(..., split_ids=...)` takes the set of training `row_id`s (from the reference) and marks `selected` from it | SAS's split depends on unguaranteed SQL row order (judge README); `BUG(port)` |
| PROC LOGISTIC `selection=stepwise slentry=0.05 slstay=0.05` (descending) | `sas_compat.stepwise_logistic(...)`, written once, implementing SAS's rules exactly: (1) start with intercept only; (2) entry: for each candidate not in the model compute the **score χ²** at the current fit; enter the largest if its p < slentry; (3) removal: compute **Wald χ²** for effects in the model; remove the one with the largest p if p > slstay, one at a time; (4) stop when nothing enters, or when the effect to enter is the one just removed ("recycles previous steps"); (5) model P(default_flag = 1) | the judge compares the 24-step path exactly (`stepwise_summary.csv`) |
| model fitting inside PROC LOGISTIC | Newton–Raphson (= Fisher scoring for the logit link) on numpy float64 to full convergence (max abs step < 1e-10) | SAS stops at GCONV=1E-8; the judge accepts a fully converged fit (PD_TOL evidence) |
| ODS tables of PROC LOGISTIC (`ParameterEstimates`, `ModelBuildingSummary`, `FitStatistics`, `GlobalTests`, `RSquare`, `Association`, `OddsRatios`, `LackFitPartition`, `LackFitChiSq`, `Classification`) | computed explicitly and written as the `printed_*.csv` / coefficient / stepwise files of the judge contract, with ODS's column names, row labels and printed formats | **UNKNOWN until the inventory settles each one**: the exact SAS definitions (HL grouping, `ctable` jackknife classification, R-square, odds-ratio CI method) are inventory rows |
| ODS variable names in coefficient tables | truncated to 20 characters (`credit_utilization_c`) | |
| `output out= predicted=` | pd for each training row from the final model | |
| PROC LOGISTIC `store` / PROC PLM `restore ... score predicted=` | train writes `model.json` = `{"intercept": b0, "coefficients": {full_variable_name: b}}`; predict reads it, computes the linear predictor η = b0 + Σ bᵢxᵢ (missing if any xᵢ missing), then pd = 1/(1+exp(−η)) as the SAS code does | the only cross-program session state (depmap) |
| PROC LOGISTIC `nofit` + `roc` (ROCAssociation) | `sas_compat.roc_association(y, score)`: Area = Mann–Whitney AUC with ties counted ½; StdErr and CI per SAS's DeLong method; Somers' D, Gamma, Tau-a | inventory row confirms SAS formulas |
| PROC RANK `groups=k` (`descending`) | `sas_compat.proc_rank_groups(x, k, descending)`: rank with ties = mean, group = floor(rank·k/(n+1)) | reproduces SAS exactly on edge scenario a (judge README) |
| PROC FREQ `tables a*b / out=` | `group_by([a, b], maintain_order=True).len()` → `COUNT`, `PERCENT` = 100·COUNT/N, sorted by a, b | `printed_confusion_*` |
| PROC SORT `by x` | `sort(x, maintain_order=True)` (stable, missing first) | SAS's default EQUALS keeps ties in input order |
| PROC EXPORT dbms=csv | `sas_compat.write_sas_csv(df, path, formats={col: fmt})`: unformatted numerics as BEST12. (`sas_compat.sas_best12`), formatted columns with their format (`percent8.2` → `5.00%`, `8.4` → `0.8592`, `8.2`, `date9.`), missing numeric → empty field, header = column names | `sas_best12` reproduces all 2.9M reference cells |
| `format x best12.` / `format x 8.4` / `percent8.2` / `date9.` attached to a column | the `formats=` argument at export time; values stay full precision in memory | formats change printing only |
| PROC MEANS / PROC FREQ (printed) / PROC PRINT / PROC CONTENTS / PROC SGPLOT | **not ported**; replaced by a one-line comment `# listing-only: PROC X <what it showed>` **[DECIDED]** | not judged (judge README "Not judged") |

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
- **Stage entry points:** each module exposes `run(input_dir: Path, output_dir: Path, ...) -> None`
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
# PORT STATUS: confidence=[high|medium|low] todos=[N]
```

Reviewers check the trailer against the file's actual `TODO(port)` count.

## 7. Deviation log

| ID | Date | Deviation | Sanctioned by |
|---|---|---|---|
| DEV-001 | 2026-11-05 | 00b steps 1–2 (categorize/rewrite tests) not applicable: 0 tests in repo; replaced by real-world and edge-case scenarios | user (judge sign-off) |
| DEV-002 | 2026-11-05 | 00b reviewers A and B reviewed code edited during their review; mitigated by review C on the final state | user (judge sign-off) |
| DEV-003 | 2026-11-05 | 00b review C's fixes verified by self-test + full re-validation, not by a fourth reviewer | user (judge sign-off) |
| DEV-004 | 2026-11-05 | Prompt 01 skeptic samples: the codebase has 4 files, so each reviewer takes 2 (all files covered) instead of 20 | user, 2026-11-05 |
