# The global Wald test when a slope's variance is tiny (2026-11-17)

Measured from SAS's output. Nothing under `port/` or `legacy/` was changed for this file.

## The case

Seed 6 (`judge/runs/gen_s06`), step 7, model of 7 variables. All 7 fit the same in SAS and the port:
-2 Log L, likelihood ratio and score tests, and step 8's Wald test of 1.5569 for the removed variable.
The global Wald test differs: **SAS 406.4827, port 407.3550**, both with DF 7. The port's figure is
exact for its estimates: 407.355047 at 60 digits, and SAS prints 407.355047318151 when it keeps the
slope (runs A5 and T2 below).

`utilization_debt_interaction` reaches 1.67e14, its estimate is 9.9e-13 and its variance 6.3e-25.
The Wald quadratic form over the **other 6 slopes**, with the 7-variable fit's estimates and
covariance, is 406.48270947. SAS prints 406.482709472169.

## The rule

For the Wald test of the global null hypothesis, SAS inverts the slopes' block of the covariance
matrix (intercept left out) by sweeping it in the order of the MODEL statement. A slope whose pivot
(its variance given the slopes swept before it) is **not above an absolute tolerance between 1e-16
and 2e-16** is left out: its row and column of the inverse are 0. The chi-square is
b' G b with that generalized inverse G. **The DF stays the number of slopes** (7 here, not 6), and so
does the probability's DF.

The other statistics are unaffected. The slope's own Wald test (estimate squared over its variance)
is printed as usual. This is not the singular-information rule (`singular-information.md`): there the
parameter is left out of the information matrix during the fit, with a tolerance of 1e-9 relative to
its own diagonal element, and the global Wald chi-square is empty. Here the information matrix is
regular: the slope's relative pivot in it is about 0.99.

## Evidence

**The runs in hand** (all 216 steps with a printed global Wald test: reference, 31 generated seeds,
35 raw inputs; `out/rv/wald_scan2.txt`, script `out/rv/wald_scan2.py`, git-ignored). Every step
equals SAS with all slopes kept except seed 6 step 7. The smallest kept pivot is 2.589e-15
(rawfit_Dn6 step 2). Cm2 and Cm3 step 1 have an empty Wald, which is the singular-information rule.

**X20** (`experiments/x20_global_wald.py`, SAS results in `experiments/x20_sas_results.json`): the
step-7 model fitted alone (PROC LOGISTIC, no selection, COVB) on seed 6's feature file with columns
rescaled. Rescaling a column rescales its estimate and its (co)variances and leaves everything else
alone, so each run prints either 406.4827 (left out) or 407.3550 (kept). The predictions were written
before each round (`out/x20/predictions*.txt`).

| Run | Change | Interaction's pivot | Relative to largest slope variance | SAS |
|---|---|---|---|---|
| A0 | none (control, no selection) | 6.29e-25 | 5.2e-23 | left out |
| A1 to A4 | interaction × 10^-1 to 10^-4 | 6.29e-23 to 6.29e-17 | 5.2e-21 to 5.2e-15 | left out |
| A5 | interaction × 10^-5 | 6.29e-15 | 5.2e-13 | kept |
| B1 to B5 | the other six × 10^1 to 10^5 | 6.29e-25 | 5.2e-21 to 5.2e-13 | left out |
| T1 | interaction scaled to pivot 1e-16 | 1.0e-16 | 8.3e-15 | left out |
| T2 to T5 | pivot 2e-16, 5e-16, 1e-15, 2e-15 | 2e-16 to 2e-15 | 1.7e-14 to 1.7e-13 | kept |
| S1 | A5 with log_num_credit_lines + 1000 (intercept variance × 2.5e4, slopes' block unchanged) | 6.29e-15 | 5.2e-13 | kept |

These runs rule out three alternative tolerances:
- **Relative to the largest variance in the block:** A4 is left out at 5.2e-15 while Dn6 is kept at
  1.9e-15, and B4 and B5 are left out at 5.2e-15 and 5.2e-13.
- **Relative to the intercept's variance:** S1 is kept at 4e-18 of it.
- **Relative to the slope's own variance:** that ratio is about 0.99 in every run.

An absolute tolerance fits every run and every step in hand: left out at 1.0e-16, kept from 2.0e-16.

## Not settled

- The tolerance inside (1e-16, 2e-16]. One candidate is machine epsilon 2.2e-16, but that would leave
  out T2 (2.0e-16), so it is not epsilon on the pivot itself. The slope's diagonal element in T2 is
  2.01e-16.
- Whether the pivot or the diagonal element is tested. They differ by 0.7% here.
- The order of sweeping when two slopes are near the tolerance. Only one slope was ever below it.
