# Parity judge (kit prompt 00b)

Decides mechanically whether the Python port reproduces the original SAS pipeline.
The original SAS code is the executable spec; the judge queries it on SAS OnDemand
for Academics (ODA) through saspy and compares output folders.

**Status:** validated (see `validation_report.md`): 18 of 19 deliberate breakages of the
SAS code caught, 1 provably undetectable (outputs byte-identical), 0 missed; a correct
port (fully converged refit) passes; 79/79 comparator self-test cases. Built and then
audited by three separate adversarial reviews; every confirmed finding is fixed and has
a self-test case.

## Pieces

| File | Role |
|---|---|
| `run_sas.py` | Runs the original `.sas` scripts in one ODA session; downloads every exported CSV to `runs/<run-id>/` |
| `compare.py` | Compares a candidate output folder against a reference (`--mode strict\|port`, `--stage`) |
| `mutations.py` | 19 deliberate breakages of the SAS code (12 judged end-to-end on real data, 2 staged on real risk scores, 5 on edge scenarios) |
| `make_scenarios.py` | Builds edge-case **inputs** in `scenarios/` (never code changes) |
| `make_converged_candidate.py` | Positive control: a correct port of the train stage (fully converged refit + SAS rules) |
| `run_validation_runs.sh` | Every SAS run the validation needs; resumable, two parallel queues |
| `validate_judge.py` | Judges each mutated run: CAUGHT / EQUIVALENT / MISSED / RERUN; writes `validation_report.md` |
| `test_compare.py` | Comparator self-test: injected faults with expected verdicts per column, plus the positive control |
| `reference/` | The reference: 31 CSVs from the unmodified SAS run, listings, `run_meta.json` |
| `reference/scenarios/` | References for the 4 edge-case scenarios |
| `known_warnings.txt` | WARNINGs the original code always emits (reviewed, benign); anything else is flagged |

## Commands (from `judge/`)

```sh
uv run python run_sas.py --run-id <id> [--mutation <m>] [--data-dir <dir>] \
    [--scripts metrics_calculation.sas --stage-inputs <dir>]   # ~5 min full, ~30 s metrics-only
uv run python compare.py reference <candidate_dir> --mode port --stage <stage>
uv run python make_scenarios.py && uv run python test_compare.py
bash run_validation_runs.sh A & bash run_validation_runs.sh B; uv run python validate_judge.py
```

ODA needs `~/.authinfo` (`oda user <id> password <pw>`, chmod 600) and the `oda_eu`
profile in `~/.config/saspy/sascfg_personal.py`. Run-ids are never reused.

## What `run_sas.py` changes in the SAS code, and nothing else

1. The `%let data_path` / `%let output_path` lines point at a fresh per-run folder on ODA.
2. Observation only: train.sas's own `ods output ParameterEstimates=...` statement inside
   PROC LOGISTIC also captures the printed tables in `CAPTURE_TABLES`, and work datasets
   the scripts already build (ROC tables, confusion matrices, cumulative lift, PSI table)
   are exported after each script. Verified: the 16 original outputs are byte-identical
   with and without this instrumentation.
3. Environment, not code: `ods listing gpath=` points at a writable folder. Without it,
   ODA's IOM sessions cannot write ROC images and PROC LOGISTIC then drops the
   ROCAssociation table (AUC). SAS Studio, where the goldens came from, has a writable path.

## Contract the Python port must meet (Step 6 runs exactly this)

The port has the same four stages, handing off through the same CSV files, and writes
the same files as SAS (names, columns, column order, printed formats). Each stage is
judged on the reference's inputs, so model-fit noise in one stage cannot flip exact
counts in the next (pd differences of ~1e-5 would otherwise swap rows across deciles).

| # | Port run | Inputs | Judge command |
|---|---|---|---|
| 1 | fe | `data/cs-training.csv`, split = reference training `row_id`s | `compare.py reference <out> --stage fe` |
| 2 | train | `reference/model_features_*.csv` | `compare.py reference <out> --stage train` |
| 3 | metrics | `reference/risk_scores_*.csv` | `compare.py reference <out> --stage metrics` |
| 4 | predict | `data/cs-test.csv` + the model artifact **written by run 2** | `compare.py reference <out> --stage predict` |
| 5 | predict | `scenarios/edge_predict/cs-test.csv` + the model from run 2 | `compare.py reference/scenarios/edge_predict <out> --stage predict` |
| 6–8 | metrics | `scenarios/edge_metrics_{a,b,c}/risk_scores_*.csv` | `compare.py reference/scenarios/edge_metrics_{a,b,c} <out> --stage metrics` |
| 9 | end-to-end smoke | `data/` only, split from the reference | `compare.py reference <out> --stage fe` and `--stage predict` (metrics may legitimately differ by a row at decile boundaries, so they are not judged end-to-end) |

Done = runs 1–8 all PASS and run 9 PASSes for fe and predict. Runs 5–8 are not optional:
the real data never reaches missing-value semantics, grade F, PROC RANK ties, a
non-zero PSI or the lower status branches, so only the scenarios judge them.

**The 70/30 split is an input, not something to reproduce.** PROC SURVEYSELECT (seed=42)
samples rows in the order PROC SQL's join left them, and a join without `ORDER BY` has
no guaranteed order. Observed on ODA: 16 of 17 runs with an unchanged
feature_engineering.sas reproduced the reference split; one
(`runs/x_split_drift_m_metrics_threshold`) drew a different one, with identical log
NOTEs. Even SAS cannot promise this split, and Python cannot reproduce SAS's RNG at all.
`validate_judge.py` refuses (RERUN) any SAS run whose split drifted.

Verified: metrics_calculation.sas run alone on the reference `risk_scores_*.csv`
reproduces the reference metrics byte-for-byte (`runs/ref_real_metrics`), so staged
judging matches the full pipeline.

## Comparison policy (port mode)

Default is **exact**. Each tolerance below is deliberate and is a place a defect could hide.

| Rule | Why |
|---|---|
| Rows matched by key; key text also compared exactly | SAS's row order comes from its SQL join engine, not business logic |
| Columns must match in name and order | Downstream CSV consumers may depend on it |
| Text exact (no trimming), including `<.0001`, `_`, `5.00%` | Printed formats are part of the output |
| **Format:** integers stay integers (`28`, not `28.0`); E-notation only where SAS used it; fixed-format columns keep their decimals; BEST12. cells must be exactly what BEST12. prints for the candidate's own value | Printed formats are part of the output. `sas_best12()` reproduces the 2,942,611 distinct plain-notation BEST12 cells of the reference. It does NOT print E-notation (SAS uses it below 1e-5, e.g. `2.01153E-23`; 15 reference files), so it is not by itself a rule for the port (RULEBOOK amendment A15) |
| **Value**, fixed-format columns (`8.4`, `percent8.2`, ...): 1 display unit | SAS printed a rounded value |
| **Value**, other numbers (BEST12.): 1 unit in the 12th character | Integers and flags are effectively exact |
| `pd_logistic`: per row within `PD_TOL = 1e-4`, and per file mean \|Δ\| within `PD_MEAN_TOL = 1e-5` | Tolerance evidence; the mean bound catches systematic bias |
| Model-fit tables: 2 display units + 0.1% relative; -2 Log L, AIC, SC, LR test 1e-6 relative; Estimate/StdErr 2 display units; integers relative only; HL group Totals exact, HL observed counts ±2; Association `Percent Tied` absolute 1e-5 percentage points (added 2026-11-05, Q1) | Tolerance evidence |
| Score ±1 only where the reference pd is within `PD_TOL` of round()'s .5 boundary **and** the candidate score is SAS round() of the candidate's own pd **and** grade/recommendation/rate are the tuple SAS assigns to that score; 0/1 prediction may flip only within `PD_TOL` of 0.5 and only to (candidate pd ≥ 0.5) | A legitimate pd difference can cross a boundary; the port must be self-consistent. Every excusal is counted and reported |
| Each such 0.5 flip widens `model_summary` and `printed_confusion_*` by exactly one flip's worth per metric (accuracy 1/N, recall 1/P, ...), computed from the files independent of `--only` | |
| `training_date`, `validation_date`: a real DATE9. date within 2 days of the candidate file | Stamped with `today()` |

`strict` mode (byte-identical text and raw lines) is used for SAS-vs-SAS validation.

### Tolerance evidence

A fully converged Newton refit of the selected model on the reference features
(`make_converged_candidate.py`, after reviews B and C) reproduces SAS's -2 Log L
(37961.2327 vs printed 37961.233). SAS stops at GCONV=1E-8, which is not the exact MLE.
Against it:
- pd differs by up to **3.64e-5**, mean 1.6e-6, median 9.0e-7. → `PD_TOL = 1e-4`,
  `PD_MEAN_TOL = 1e-5`. The positive control passes with 42 / 29 legitimate score
  excusals (train / validation); a uniform +5e-5 bias fails.
- Wald χ² differs by up to 0.0285 (`has_delinquency` 306.3717 vs 306.4002), about
  1e-4 relative; the Intercept prints -4.1669 vs -4.1668. → 0.1% relative, 2 display units.
- The log-likelihood gap is 4.5e-6 absolute. → likelihood statistics at 1e-6 relative.

- Association `Percent Tied` (added after sign-off, human decision Q1 at the prompt 02
  gate, 2026-11-05): SAS counts event/non-event pairs whose pd differ by ≤ ~1e-8 as tied
  (280 of 686,727,936 pairs = 4.0773e-5 %). The same rule on the converged refit gives 283
  (4.12e-5 %), 1% relative off, outside the 0.1% model rule. The cell is judged with an
  absolute 1e-5 percentage points (≈ 69 pairs). Concordant/Discordant keep the model rule.
  Effect on validation: verdicts unchanged (18 CAUGHT, 1 EQUIVALENT); three mutations
  (`fe_impute_mean`, `fe_import_guessingrows`, `fe_median_group_misaligned`) no longer
  fail on that one cell and remain caught in about 20 other files each.

Reproducing SAS's exact Fisher-scoring stopping point would allow tighter bounds, but
is brittle. Tightening is a rulebook choice, not a judge choice.

## Edge-case scenarios (inputs only)

| Scenario | Inputs | Reaches |
|---|---|---|
| `edge_predict` | `cs-test.csv` with MonthlyIncome = NA for all applicants under 30 | missing test-median → missing income → SAS missing-value semantics (`. < 2500` is true), missing pd → grade F, Decline, 20% (5,881 rows) |
| `edge_metrics_a` | synthetic risk scores, weak signal, pd at 2 decimals | PROC RANK ties across boundaries, PSI 0.0906 "No significant change", "Needs Improvement" |
| `edge_metrics_b` | synthetic, train pd at 1 decimal vs validation at 3 | PSI 1.5743 "Significant change" |
| `edge_metrics_c` | synthetic, pd on 0.02 vs 0.01 grids | PSI 0.1790 "Some change", AUC 0.6973 "Requires Review" |

With the real data ("Production Ready"), every status and PSI-interpretation branch is
covered. Scenario c was tuned offline with an emulation of PROC RANK
(`floor(rank·groups/(n+1))`, ties = mean rank) that reproduces SAS's PSI and AUC on
scenario a exactly: a ready rule for the port.

Not reachable by any input, so covered by the rulebook instead of the judge:
- **Grade E is dead code.** Score = 600 + 250·(1−pd) ≥ 600 whenever pd is present, so
  E (550–599) never occurs. F occurs only when pd is missing.
- **round() half-ties** need pd = 1 − (k+0.5)/250 exactly; SAS rounds half away from
  zero, Python's `round` to even (`compare.sas_round` is the SAS rule).

Not judged at all (listing-only output): PROC MEANS / FREQ / PRINT tables in the
listings and log NOTEs. They restate judged data; the rulebook decides whether the port
reproduces them.

## Findings about the original code (for the rulebook / gap inventory)

- **Training incomes ≥ 100,000 are truncated to 5 digits.** PROC IMPORT with the
  default `guessingrows` reads `MonthlyIncome` as `$5.`
  ([feature_engineering.sas:28-33](../feature_engineering.sas#L28-L33)): 77 incomes
  are cut (159,791 → 15,979). predict.sas uses `guessingrows=max`, so test incomes are
  **not** truncated. Reproduce bug-for-bug, mark `BUG(port)`.
- **The 70/30 split depends on unguaranteed SQL row order** (above). `BUG(port)`.
- **PSI is always 0.0000** ([metrics_calculation.sas:250-262](../metrics_calculation.sas#L250-L262)):
  each set is ranked into its own deciles, so every bin holds 10% on both sides.
  `MODEL_CARD.md` claims 0.0013. `BUG(port)`.
- **Grade E is unreachable** and F only arises from a missing pd (above).
- **Test-set income imputation uses test-set medians**
  ([predict.sas:59-73](../predict.sas#L59-L73)), not training medians. `BUG(port)`.
- **The model fails Hosmer-Lemeshow** (χ² = 121.913, 8 DF, p < .0001), printed but
  never acted on.
- **KS depends on row order within pd ties** (cumulative sum after a stable sort).
  The port must sort stably in reference-CSV order. Today's maximum is not on a tie.
- `input(MonthlyIncome, best32.)` on `"NA"` logs invalid-data notes and yields missing;
  that is the intended conversion.
- Column names are truncated: 32 characters by PROC IMPORT, 20 in ODS tables
  (`credit_utilization_c`). The port must emit the truncated names.

## Review history

| Review | Scope | Confirmed findings | Effect |
|---|---|---|---|
| A (Opus 5.5) | comparator mechanics | 11 (3 critical): ±1 accepted on integers/flags, excusals accepting any value, keys not compared as text | rewrite; all reproduced first, all fixed, all in the self-test |
| B (Opus 5.5) | harness, policy, coverage | 12 (1 critical): untested branches; PD_TOL too tight for a correct port; printed results unjudged; BEST12 rounding; equivalent mutant | edge scenarios, printed tables, evidence-based tolerances, 5 new mutations |
| C (Opus 5.5, resample) | final judge | 9 (1 critical): excusals ignored the candidate's own pd; formats not enforced; scenarios missing from the contract | self-consistent excusals, format checks, contract table, positive control |
