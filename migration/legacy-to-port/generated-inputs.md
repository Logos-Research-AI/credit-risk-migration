# The port against the corrected SAS on generated valid inputs

2026-11-16. Measurement only: nothing in `port/`, `legacy/`, `judge/compare.py` or `judge/reference/` was changed.

The parity contract judges the port on the real data and on four hand-made scenarios. This is the same contract run on fourteen generated pairs of raw files, each run through the corrected SAS and through the port.

**Result: no difference of the port was found.** Eleven of the fourteen seeds pass every line. The other three fail only in the train and predict stages, and in each the cause is that SAS stops its model fit before full convergence; the port's fit is the converged one. The two stages that do not depend on the fit (feature engineering and metrics) pass on all fourteen seeds. No generated row turned out to be invalid input, and no seed was rejected for a fit that did not converge.

## Method

1. **Generate.** `judge/generated_inputs.py make --seed N --out <folder>` writes `cs-training.csv` and `cs-test.csv`, deterministically in the seed.
2. **Run the corrected SAS.** `judge/run_sas.py --run-id gen_sNN --data-dir <folder>`: the four scripts in one session, as for the reference. Four runs at a time, about 70 seconds each, all with 0 ERROR and 0 new WARNING.
3. **Run and judge the port.** `judge/generated_inputs.py judge --seed N --data <folder> --sas runs/gen_sNN --out <folder>/port` runs the port as `run_contract.sh` does and judges each stage with `compare.py --mode port` against that seed's SAS run:
   - line 1, fe: the raw files, with the split taken from the SAS run;
   - line 2, train: the SAS feature files;
   - line 3, metrics: the SAS score files;
   - line 4, predict: the raw test file, the model of line 2, the SAS medians file;
   - line 9, end to end: the four steps chained in one folder, each stage judged.

   The port takes about 7 seconds per seed, the judge calls about 30.

Inputs and results are in `out/generated/sNN/` and the SAS runs in `judge/runs/gen_sNN/` (both git-ignored; the inputs are reproducible from the seed).

### What the generator draws

Every row is an applicant; every field is drawn either from a pool of edge values or from an ordinary distribution close to the real data (half and half by default), so the fit has ordinary rows to hold on to. The pools:

| Field | Edge values |
|---|---|
| Utilization (raw; the program multiplies by 100) | each band and flag threshold exactly and one ten-millionth either side: 0.3, 0.5, 0.75, 1, and the cap 2; 0; 0.000000001; 50708; values whose product with 100 is not exact in floating point (0.29, 0.57, 0.07) |
| Debt ratio (raw) | 0.3, 0.43, 0.6 and the cap 5, exactly and either side; 0; 3296; 329664; 0.07, 0.14, 0.28, 0.56 |
| Age | every edge of the five age groups and the five age categories, and the years either side: 24 to 26, 29 to 31, 34 to 36, 39 to 41, 49 to 51, 59 to 61, 64 to 66; 21, 80, 109 |
| Monthly income | 0, 0.01, 0.5, 1; 2499, 2499.99, 2500, 2500.01, 2501; 99999, 100000, 1000000, 3008750 |
| Dependents | 0 to 4, 10, 20 (the flag is at 3; above 0 the income is divided) |
| The three late-payment counts | 0 to 4, 13, 98 |
| Credit lines | 0 to 4, 20, 58 (the flag is at 2) |
| Real-estate loans | 0 to 3, 13, 54 |

Missing values: one income in five and one dependents value in twenty are missing, in every age group. The outcome is drawn from a logistic model of the row's own values (late payments, utilization, debt ratio, age, credit lines), so there are defaulters and non-defaulters at every edge and no rule separates them. About 29 % of applicants default.

Validity (section 3 of the requirements) is kept by construction: the twelve documented columns; only income and dependents ever missing; at least one known training income; outcome 0 or 1 (blank in the test file, as in the real one); distinct row ids; counts whole and zero or more; no negative income; every value a plain decimal number of at most 32 characters (asserted on every field).

Left out on purpose: exponent notation, quotes, signs and leading zeros. Whether those are numbers was the subject of rulings G48 and G50, which ruling G53 set aside.

### The seeds

| Seed | Training rows | Test rows | Defaulters | What is special |
|---|---|---|---|---|
| 1 | 400 | 150 | 111 | small |
| 2 | 1,200 | 400 | 353 | medium |
| 3 | 300 | 0 | 84 | smallest; the test file has its header and no applicant |
| 4 | 2,500 | 800 | 740 | the 30-to-39 age group has no known income in the training file |
| 5 | 800 | 300 | 248 | no dependents value missing in the training file (the column is numeric) |
| 6 | 5,000 | 1,000 | 1,501 | largest |
| 7 | 600 | 200 | 178 | three rows in ten repeat an earlier row: tied probabilities |
| 8 | 1,500 | 500 | 457 | values the requirements allow and the real data lacks: negative utilization and debt ratio, ages and real-estate loans with decimals, age 0 |
| 9 | 3,000 | 600 | 870 | one decimal field in four written with up to 32 characters |
| 10 | 500 | 2,000 | 134 | test file larger than the training file; every test income of the 60-and-over group missing |
| 11 | 2,000 | 500 | 573 | row ids shuffled and not contiguous; missing written as an empty field |
| 12 | 1,000 | 300 | 100 | few defaulters, one in ten |
| 13 | 700 | 250 | 302 | nine fields in ten from the edge pools |
| 14 | 4,000 | 900 | 1,180 | the under-30 age group has no known income; one row in ten repeats |

How often the edges were reached, over the fourteen feature files: utilization exactly 30, 75, 100 and 200 percent in 539, 532, 521 and 508 rows; debt ratio exactly 43 and 500 percent in 620 and 634; income exactly 2,500 and 0 in 634 and 646; age exactly 30 in 638. Every grade from A to F occurs in twelve seeds (seed 12 has no F, seed 13 no A). In seeds 4 and 14 the medians file has an empty median for the empty age group and the overall median is used.

## Results

| Seed | 1 fe | 2 train | 3 metrics | 4 predict | 9 end to end |
|---|---|---|---|---|---|
| 1 | pass | pass | pass | pass | pass |
| 2 | pass | **14 of 18** | pass | **0 of 2** | train and predict fail as in lines 2 and 4 |
| 3 | pass | pass | pass | pass (header lines only) | pass |
| 4 | pass | pass | pass | pass | pass |
| 5 | pass | pass | pass | pass | pass |
| 6 | pass | **17 of 18** | pass | pass | train fails as in line 2 |
| 7 | pass | pass | pass | pass | pass |
| 8 | pass | **15 of 18** | pass | **0 of 2** | train and predict fail as in lines 2 and 4 |
| 9 | pass | pass | pass | pass | pass |
| 10 | pass | pass | pass | pass | pass |
| 11 | pass | pass | pass | pass | pass |
| 12 | pass | pass | pass | pass | pass |
| 13 | pass | pass | pass | pass | pass |
| 14 | pass | pass | pass | pass | pass |

The judge excused nothing on any seed: no grade flip at a cut, no 0.5 prediction flip.

### The three failures

All three are tolerance effects of the fit. In each, SAS and the port select the same variables and print the same -2 Log L. To tell which side is off, the selected model was refitted on the SAS feature file to full convergence, independently of both.

| Seed | What fails | First rows (reference, port) | Distance from the converged fit |
|---|---|---|---|
| 2 | `pd_logistic` mean difference 2.07e-5 (score files) and 2.29e-5 (prediction files), limit 1e-5; no single row beyond the row limit. `model_coefficients.csv` `Estimate`, 1 cell | `flag_multiple_delinq`: `0.7563`, `0.7566` | SAS: mean 2.07e-5, largest 6.4e-5. Port: largest 5e-11 |
| 8 | `pd_logistic` beyond 1e-4 on 2 training rows and 4 test rows, with their scores. `Estimate`, 2 cells | row 323: `0.2125572542`, `0.2124331499`; `Intercept`: `-2.7726`, `-2.7734`; `has_delinquency`: `1.2535`, `1.2542` | SAS: mean 6.0e-6, largest 1.24e-4. Port: largest 5e-11 |
| 6 | `printed_global_tests.csv`, the Wald test of step 7, 1 cell | `406.4827`, `407.3551` (0.21 %; 0.1 % allowed) | the final model agrees to 2e-8. At step 7 the converged value, computed independently, is 407.3551: the port's |

- **Seeds 2 and 8.** SAS stops when its convergence measure falls below 1E-8, which on these small samples leaves it further from the optimum than on the real data (there about 1e-6). The port iterates to the optimum. The tolerances `PD_TOL` and `PD_MEAN_TOL` were set on the 105,000-row training file. In seed 8 the selected model also holds `income_per_dependent` with a coefficient of 4.681E-7 beside incomes of three million, which makes the fit badly scaled.
- **Seed 6.** The model of step 7 holds `utilization_debt_interaction`, which reaches 1.7e14 in this seed (utilization 50708 times debt ratio 329664, each times 100). The variable is removed at step 8 and the final model agrees. The one cell that differs is the Wald test SAS printed for the intermediate model.

None of the three is a real difference of the port, and none is an invalid row. Whether the judge's fit tolerances should depend on the sample size is a question for the owner; nothing was changed.

## What this does and does not show

- **Shown.** On valid inputs built around every threshold of the feature rules, with missing values in every age group, empty age groups, ties, a header-only test file, long decimals, shuffled ids and blank missing values, the port's feature files, medians file and metrics files agree with SAS on every seed, and its model and predictions agree wherever SAS's own fit has converged to within the judge's tolerances.
- **Not targeted.** The grade cuts (10, 15, 25, 35, 50 %) and the 0.5 prediction cut lie on the fitted probability, which a generator of raw rows cannot place. Every grade is populated, but no probability was steered onto a cut.
- **Not covered.** Ways of writing a number other than plain decimals; inputs outside section 3 (ruling G53: not required).
- **Sample.** Fourteen seeds. The generator takes further seeds by adding a line to its table.
