# RUNS — reviewer 2: end-to-end differential evaluation of the three `run` units on real data

Units: `def:run` (feature_engineering.run), `def:run_py_py` (predict.run), `def:run_py`
(metrics_calculation.run), all accepted (`get_status`: 131 / 131 formalized). Rulebook version 3.
Read-only review: nothing in the blueprint was changed; `def:zz_carrier` was found accepted and
depending on the three units, so it was not re-submitted. `B6_r1.md` / `B7B8_r1.md` were not read.

## Result

**No DEFECT, no PRECOND finding.** 40 whole-run evaluations in Lean (12 + 12 + 16), 198 output
tables compared exactly with the real Python: 190 identical, 8 differ, and those 8 are **one**
last-bit difference of `exp` between the Lean runtime and polars on **one** row (recorded
separately below, fully accounted for). Every input table and both `input_best32` doubles were
checked bit for bit before the comparison.

| run | sample | rows | cases | differences |
|---|---|---|---|---|
| `run` (feature_engineering) | `mid`: 150 seeded random rows of 50001..100000 + 48 edge rows | 198 (137 train / 61 validation) | 13 | 0 |
| `run` | `end`: 150 seeded random rows of 100001..150000 + 55 edge rows (incl. row 150000) | 205 (148 / 57) | 13 | 0 |
| `run` | `extremes`: edge rows only, `fix_income_truncation=True` | 168 (123 / 45) | 13 | 0 |
| `run_py_py` (predict) | `test_last`: last 200 lines of data/cs-test.csv | 200 | 10 | 0 |
| `run_py_py` | `test_rand`: 200 seeded random lines of data/cs-test.csv | 200 | 10 | 8 (one `exp` value, 1 ulp, row 34475; see below) |
| `run_py_py` | `edge_mix`: edge_predict/cs-test.csv, last 100 + 100 seeded random (60 among the lines that differ from cs-test) | 200 | 10 | 0 |
| `run_py` (metrics) | edge_metrics_a, last 300 validation / 700 training | 300 / 700 | 20 | 0 |
| `run_py` | edge_metrics_b, last 300 / 700 | 300 / 700 | 20 | 0 |
| `run_py` | edge_metrics_c, last 300 / 700 | 300 / 700 | 20 | 0 |
| `run_py` | edge_metrics_a, seeded random 300 / 700 of the middle rows | 300 / 700 | 20 | 0 |
| `run_py` | edge_metrics_b, seeded random 300 / 700 | 300 / 700 | 20 | 0 |
| `run_py` | edge_metrics_c, seeded random 300 / 700 | 300 / 700 | 20 | 0 |
| `run_py` | REAL risk_scores files, all 51 columns, last 20 / 30 lines | 20 / 30 | 20 | 0 |
| `run_py` | REAL risk_scores files, columns row_id / default_flag / pd_logistic, seeded random 150 / 350 | 150 / 350 | 20 | 0 |
| total | | | 229 | 8 (all the same 1-ulp `exp` value) |

Cases per sample: `run` = 2 input tables + 1 check of the `input_best32` double + 10 output tables
(full × export_train_medians: 2 + 2 + 3 + 3 files); `run_py_py` = 1 input table + 1 check of the
double + 8 output tables ((fix_train_medians false | true with the real medians) × full, 2 files
each); `run_py` = 2 input tables + 18 output tables (fix_psi_bins false / true, 9 files each).
An output-table case is one 64-bit digest of the file name and the whole table (row count, column
names in order, cell kind, value bits; an Int64 column is compared as the numeric value, as
`Pl.toTable` gives it). Evaluation time: 0.7 – 1.8 s per input.

Receipts (`migration/diffeval/receipts/units.tsv`, generator `migration/diffeval/units/runs_r2_gen.py`):
`run` 39 cases PASS, `run_py` 160 cases PASS, `run_py_py` 30 cases KNOWN-DIFF (8 expected, the
`exp` value).

## Method

Generator: `migration/diffeval/units/runs_r2_gen.py` (suites `work/runs_r2_fe`, `runs_r2_pred`,
`runs_r2_met`; statistics `work/runs_r2_stats.json`; `... runs_r2_gen.py explain` reproduces the
account of the `exp` difference). Technique of b6 / b7 / b8, own rows, only the whole runs:

- The REAL `run` is called on a temporary directory; `sas_compat.write_sas_csv` is replaced by a
  recorder, the frames it receives in call order are the expected tables. The imported frames
  (`proc_import_csv`, real) are read from the locals of the run.
- Lean: `run full IB T S fix export`, `run_py_py full IB intercept coefficients medians T fix`,
  `run_py sas_best parse_float sas_d8 today V T fix` through `def:zz_carrier`. Tables are built
  inside Lean from one string literal (decimal text parsed with `Float.ofScientific`; a value
  within 2^-9 ulp of a rounding boundary is sent by its bits: 7 cells); the digest of every input
  table is compared first (14 / 14 samples: identical to what Python imported).
- `input_best32`: the test double of b7 (text: null / "NA" → null, digits → value; Float64:
  identity, non-finite → null). Checked in each of the 6 samples against the real function:
  `fe_run_01_clean IB (Pl.ofTable T)` / `predict_run_01_clean IB (Pl.ofTable T)` equals the local
  `credit_raw_clean` / `test_raw_clean` of the real run (6 / 6).
- `sas_best` / `parse_float` / `sas_d8`: lookups in the (argument bits → text), (text →
  `float(text)` bits) pairs the real functions produced during the run; `today`: the String cell
  of the run's date.
- predict: `model.json` and `income_medians.csv` come from really running the pipeline once
  (`feature_engineering.run` on the full data with `export_train_medians=True`, then `train.run`):
  intercept -4.166900901967611, 18 coefficients (Int column `credit_util_category` among them),
  medians {1: 2557, 2: 4666, 3: 6000, 4: 6333, 5: 5313} read with `pl.read_csv(...,
  schema_overrides=...)` as predict.py does. The real `risk_scores_*.csv` of that run feed the two
  real metrics samples.

Disjointness from the implementers' rows: feature_engineering rows are all > 50000 (b7: 1–20,
2551–2778, four rows < 7200); predict rows exclude everything `b8_gen.pick` selects (asserted);
metrics rows are the last 300 / 700 and a sample of rows 300..2699 / 700..6299 (b6: the first
300 / 700).

What the samples reach (from `runs_r2_stats.json`):

- feature_engineering: 571 rows. Edge rows included: age < 22: 46, age > 100: 9 (all there are above
  row 50000; ages 101–109) and one row with age 0, utilization > 10: 41 (up to 13930), DebtRatio >
  5000: 46 (up to 18062), 90-days-late ≥ 90: 46 (96 and 98), dependents ≥ 8: 21 (all there are above
  row 50000; up to 13), income 0: 46, income ≥ 100000: 40. Import variants: MonthlyIncome text in
  all three (cut to 5 characters by the default import in `end`: 6 incomes; not cut in `mid`, whose
  first 20 rows hold a 7-digit income; `guessingrows=None` in `extremes`), NumberOfDependents
  numeric in `mid` / `end` and text in `extremes`. Medians of even and odd groups, with ties
  (`extremes`: 852.5, 9826.5, 23866.5, 53793.5). 157 imputed incomes, 34 missing dependents.
  financial_health 0 … 100, total_risk_flags 0 … 5 (the 5-operand `sum_horizontal`, `full` true
  and false both equal to Python).
- predict: 600 rows; `edge_mix` without the fix has no median for age group 1: 75 null incomes →
  75 null pd, grade F; with the real training medians no null. NumberOfDependents text with NA,
  SeriousDlqin2yrs an all-null text column.
- metrics: PSI tables of 2, 3, 8 and 10 rows, calibration tables of 15, 16 and 20 bins, null
  precision / f1 in threshold_analysis (0 – 8 nulls), all three `status` values, `sas_best` texts
  that change the value (`0.133333`, `0.123333`, `0.113333`, `0.093333`), a negative D8 statistic
  (`-0.2381`), 51-column frames with text columns carried through the sort.

Float sums, means and medians are order-sensitive (select-context `sum` in blocks of 128, Kahan
group means, median interpolation, `sum_horizontal` shapes, the PSI sum): none differs on any
sample.

## The one difference: `exp`, last bit (recorded, not a finding against the unit)

- Where: `def:predict_run_06_score`, predict.py:234 `1 / (1 + sas_compat.sas_exp(-pl.col("predicted_logit")))`
  (`sas_exp` → `Expr.exp` → `RealLike.exp`).
- Which value: sample `test_rand`, row id 34475 (`34475,,0.180394012,45,0,0.515924602,6153,15,0,3,0,0`),
  predicted_logit = -3.5785111395443048. `exp(3.5785111395443048)` (argument bits
  4615240509517313858) is bits **4630238058052490439** in polars and Python `math.exp` on this
  machine and **4630238058052490438** in Lean's runtime (`Float.exp (Float.ofBits 4615240509517313858)`
  through `eval_decl`). The exact value lies 0.50026 ulp from the Python result: Lean's is the
  correctly rounded one. Consequence: pd_logistic 0.027159027319719514 (Python) vs
  0.027159027319719517 (Lean), 1 ulp, that row only; credit_risk_score (843), grade and every other
  column are equal. It appears in both files and in all four runs of the sample (the row's income
  is not imputed): 8 table digests.
- Complete account: the real `predict.run` rerun with that single `exp` result replaced by Lean's
  value gives exactly the digests Lean returned, for both values of `fix_train_medians`
  (`runs_r2_gen.py explain`: `equal: True` twice; the only cells that change are
  `pd_logistic` of row 34475 in the two files).
- Minimal input: the one-line cs-test.csv above with the real model.json.
- Other values checked directly in Lean: the 4 further `exp` arguments and the 4 `log` arguments
  where polars is furthest from the exact value (0.492 – 0.5004 ulp) are bit-identical.
- Elsewhere no last-bit difference shows: the 600 predict rows hold one differing `exp` result;
  the three `log` columns of the 571 feature_engineering rows are written to the output tables
  and are identical, and the `log` of metrics step 06 (PSI) is identical on the 8 samples.

## Preconditions: inputs of the samples outside a unit's precondition although Python runs

None, 0 times.

- Zero divisor `num_dependents + 1 = 0` (`fe_run_05_features_precond`,
  `predict_run_05_features_precond`): 0 of 571 and 0 of 600 rows. In the whole files there is no
  NumberOfDependents of -1 and no negative one (cs-training 150000 rows: 0 … 20; cs-test and
  edge_predict 101503 rows: 0 … 43), so the narrowing excludes no row of the delivered data.
- Zero-row tables: every input table has rows; no output table of the 40 runs is empty (smallest:
  ks_statistic 1 row, printed_psi_calculation 2 rows, income_medians 4 rows in `edge_mix`). The
  recorded limit of §2.6 is not reached. An age group without median (`edge_mix`, flag off) is
  inside the precondition and equal to Python.
- `fix_psi_bins=True`: the ValueError of metrics_calculation.py:277 is raised on none of the 8
  metrics samples, nor on the full scenario files or the full real files (the pd columns have no
  null).
- Column kinds: every column the preconditions require numeric was imported numeric;
  MonthlyIncome / NumberOfDependents occur as text and as numeric, both allowed.

## Notes

- NOTE (harness, not the units): `eval_decl` echoes the input, and a 200-row table is 12 – 23 k
  characters; the string-literal encoding of `runs_r2_gen.py` keeps one sample in one call.
- NOTE: `fix_income_truncation` is an unused Bool in `def:run` (RULEBOOK §3); the sample
  `extremes` passes `true` together with the frame imported with `guessingrows=None`, so both
  values of the flag are covered with the import Python really did.
- Not covered here (by assignment: whole runs on real data only): hand-made nulls / NaN, inputs
  where Python raises, the step items individually, `train.run`.
