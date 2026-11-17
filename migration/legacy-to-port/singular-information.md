# What SAS does when the information matrix is singular (2026-11-17)

Measured for the owner's decision of 2026-11-17 (the port follows SAS on every small input where SAS
completes). Nothing under `port/` or `legacy/` was changed for this file.

## When it happens

A fit starts from the intercept-only estimates. When the outcome is rare (fewer than about 1 row in
40.4 is an event, or fewer than 1 in 40.4 is not), the first iteration can move a row's linear
predictor beyond 36.74 in size, where its weight is exactly 0. If a parameter rests on such rows
alone (a flag that is 1 only for one event), its diagonal element of the information matrix is 0 and
the matrix is singular. The port solves with it and stops
(`neither converged nor separated`); SAS goes on.

## The rule

1. **Probabilities, weights, residuals.** With e = exp(−|η|): hi = 1 / (1 + e) is the probability of
   the likelier outcome and lo = e · hi that of the other; **lo is 0 when hi rounds to 1**, that is
   when |η| > 53 ln 2 = 36.7368. The weight is hi · lo and the residual y − p is taken from hi and lo.
   This is the same on both sides (a probability near 0 as one near 1), and below the limit the small
   values are exact: at η = 36.20 the weight is 1.893e-16, not the 2.2e-16 that p(1 − p) gives.
2. **The inverse.** Wherever the fit needs the inverse of the information matrix (the step, the
   ridged step, the convergence test, the 5000 test of quasi-complete separation, the covariance), SAS
   takes the parameters in order, intercept first, then the variables in the order of the model. A
   parameter whose pivot (its diagonal element after the earlier parameters are swept out) is **not
   above 1e-9 times its own diagonal element** is left out: its step is 0 and its row and column of
   the inverse are 0. The others are solved without it.
3. **The iteration is otherwise unchanged**: ridge, convergence test (GCONV, with the inverse of 2),
   separation tests from iteration 8. A parameter can be left out at some iterations and not at
   others. SAS writes "WARNING: The information matrix is singular and thus the convergence is
   questionable" when a parameter is left out at the last iteration, and only then.
4. **Tests on a step whose last iteration left a parameter out.**
   - That parameter has no standard error and no Wald test: DF 0, the cells empty.
   - The removal test removes it at the next step, whatever the other variables' tests are. The
     summary row has DF 0 and an empty Wald chi-square and probability
     (`2,,flag_very_high_utili,0,0,_,,`).
   - The Wald test of the global null hypothesis has no chi-square and no probability; its DF is the
     number of variables not left out (`1,Wald,,0,`). The likelihood ratio and score tests, the fit
     statistics and R-square are as on any step.
   - A parameter left out on the way but not at the last iteration has an ordinary, very large
     standard error and a Wald chi-square that prints 0.0000.

## Evidence

**Designed data, PROC LOGISTIC with ITPRINT, DETAILS and COVB: 40 cases, 44 fits**
(`experiments/x19_singular_cases.py`; SAS's results in `experiments/x19_sas_singular_results.json`).
The rule was fitted on the first 25 cases and then **predicted the 17 fits of the last 15 cases, run
after the predictions were written: iterations, estimates of every iteration, stop, the parameters
left out, standard errors and tests, all as predicted.**

| What was tested | Cases | Result |
|---|---|---|
| A flag on one event, 45 to 283 rows, 1 to 7 events | G1 to G5 | The flag's step is 0 while its row has weight 0; it moves again when the weight is not 0 (G1 iteration 7; G3, G4a iteration 2) |
| The limit 36.7368 | G4a (η = 36.726: weight not 0), G4b (η = 36.754: weight 0), mirrored G9d, G9e | As the rule says, on both sides |
| The same with outcomes exchanged | G9a to G9e | Identical to the fifteenth digit (Wald 4.3665171590004E-13 against 4.3665171590002E-13) |
| Which parameter is left out | G7a, G7b: two columns that become collinear once a row has weight 0, in both orders | The later one in the order of the model |
| The tolerance and what it is relative to | G8 series: the second column off collinearity by 1e-7 to 1e-2; H1: the first column times 1000; G8e: the second times 1000 | Left out up to a relative pivot of about 8.6e-10, kept from about 1.18e-9; unchanged by either scaling. A tolerance relative to the largest diagonal element, or to the diagonal corrected for the intercept, or 1e-12 (the value SAS documents for SINGULAR=), each fails on several cases |
| A singular parameter beside a regular variable, in a stepwise run | J5 (and J5n, J6n without selection) | Removed at the next step with DF 0; global Wald test empty with DF 1 |

**The three ITPRINT histories in hand before the rule** (`out/review_fit/sas`: small45_19, small60_16,
small120_7): reproduced, including which of them has the warning.

**Raw inputs through the whole SAS program.** The outcome column of raw files already run was
searched (the split and the features do not depend on it): of 2,500 columns with at most 1 event in
41 rows, 53 gave a singular fit (35 with a parameter left out on the way only, 18 at the last
iteration). Eight inputs were made, the steps predicted with a scratch copy of the port carrying the
rule (`out/review_fit/sim2`), and SAS run: **steps, the DF 0 rows and the warning as predicted on all
eight.** With the two inputs of the review, ten raw inputs:

| Input | Raw rows (training) | Shape | SAS |
|---|---|---|---|
| `single45`, `Ca` | 64 (45) | one event, flagged; left out on the way, not at the end | complete separation at 8, removed with Wald 0.0000 |
| `single60`, `Cb` | 85 (60) | one event, flagged; left out at the end | complete separation at 8, warning, removed with DF 0 |
| `Ce` | 171 (120) | the same | the same |
| `Cc` | 128 (90) | two events, one flagged | converged with the warning, removed with DF 0 |
| `Cd` | 171 (120) | the same | the same |
| `Cm1` | 64 (45) | mirrored: one row that is not an event, flagged; on the way only | complete separation, removed with Wald 0.0000 |
| `Cm2` | 85 (60) | mirrored; left out at the end | warning, removed with DF 0 |
| `Cm3` | 128 (90) | mirrored; converged | warning, removed with DF 0 |

The scratch copy equals SAS on every file SAS wrote, through the whole contract, on all ten. Its
`_fit_as_sas` reproduces all 44 designed fits (iterations, estimates, standard errors, parameters left
out) and the 110 fits of the earlier ITPRINT runs (109 to 1e-7 relative, one separated step to 2e-7). On the reference data its files are the branch's
(the same 6 cells differ from SAS's text), and on the 70 small feature files with a SAS model it
differs from SAS only where the branch does for another reason.

## Failing inputs for the port as it stands

Branch `entry-score` with the ridge floor, the 5000 test and the recycling rule corrected
(`out/review_fit/sim`):

- `single45`, `single60`, `Ca`, `Cb`, `Cc`, `Cd`, `Ce`: the train step stops
  (`RuntimeError: ... neither converged nor separated`) where SAS completes. Smallest: `single45`,
  64 rows.
- `Cm2`, `Cm3`: the port does not stop and is wrong: summary row `2, DF 1, Wald 0.0000, 1.0000` for
  SAS's `2, DF 0, empty`, and the global Wald test `0.0000, DF 1` for SAS's empty cell with DF 0.
  The port's p(1 − p) is not 0 for a probability near 0.
- `Cm1` passes: the difference there is beyond the printed digits.

```
cd judge && uv run python ../migration/legacy-to-port/experiments/x18_small_raw_inputs.py judge <dir> single45 single60 Ca Cb Cc Cd Ce Cm1 Cm2 Cm3 --port <folder holding credit_risk>
```

## Smallest fix

`experiments/x19_singular_fix.patch` (against the branch with the recycling rule; about 65 lines in
`sas_compat.py`, 12 in `train.py`):

- `sas_compat._p_w_r(eta, y)`: probability, weight and residual as in rule 1.
- `sas_compat._ginv(a)`: the inverse of rule 2 and the parameters left out.
- `_fit_as_sas`: uses the two in place of `_expit`, `p * (1 - p)`, `np.linalg.solve` and
  `np.linalg.inv`; returns the parameters left out at the last iteration in a new field
  `LogisticFit.singular`.
- `stepwise_logistic`, removal test: a variable whose parameter is in `singular` is removed first, as a
  step with DF 0 and no Wald chi-square.
- `train.py`: the summary row of such a step has empty Wald and probability cells; the global Wald row
  of a step with singular parameters has empty chi-square and probability and DF = variables not left
  out.

## Not measured

- Two parameters left out on the same step (which is removed first), and a singular parameter
  together with another variable whose Wald test would also remove it.
- A candidate's score test for entry when the model has a parameter left out: it cannot arise while
  such a parameter is always removed at the next step.
- The port leaves a candidate out of the entry test when its residual information is below 1e-8 of
  its own; SAS's tolerance in the fit is 1e-9. Whether SAS's entry test uses 1e-9 too was not run.
- The final model's scores when a weight is 0: no final model in hand has one.
