# The iteration at which SAS declares a separation, and what it keeps

Measured on 2026-11-16/17. Nothing under `port/` or `legacy/` was changed. Follows `small-inputs.md`
(case (c) and the later-step case, where the final model depends on a fit that does not exist).

Working files: `out/separation/` (git-ignored): `exp.py`, `exp_entry.py` (the SAS runs), `sas/*.log`
(tagged lines with 32-character numbers), `analyse.py`, `check_rule.py`, `entry_score.py`,
`scan_cuts.py` and their `.out` files.

## Result

**The rule.** PROC LOGISTIC, as `train.sas` calls it (`selection=stepwise`, default technique), fits
every step by Fisher scoring **from the intercept-only estimates** (intercept = log(events /
non-events), every other coefficient 0), whatever the step before left. After the update of
iteration k, **for k = 8 and every later iteration**, in this order:

1. **Complete separation** when no observation is on the wrong side: every observation has a
   fitted probability of its own response above 0.5.
2. Otherwise **quasi-complete separation** when some observation has a probability of its response
   of 0.95 or more and a diagonal element of the inverse information matrix, computed on the
   standardized columns (each variable minus its mean, divided by its standard deviation; intercept
   column left), exceeds 5000.

When either holds the iteration stops there. **The estimates kept are those of iteration k** (after
its update), with the inverse information at those estimates as their covariance. -2 Log L, the
Wald chi-squares of the removal test, the global tests and the probabilities are all computed from
them. The selection then goes on as after any step.

3. **The entry test after a separated step that stays.** The kept estimates are not at a maximum,
   so the score of the model's own parameters is not zero. SAS's score chi-square for a candidate
   is the full quadratic form U' I⁻¹ U over all parameters of the enlarged model at the kept
   estimates (the model's parameters and the candidate), not the candidate's part alone. At a
   converged fit the two are the same number.

**It predicts every run.** 38 SAS runs, 54 fitted steps with at least one variable: 31 declared
complete (29 stopped at iteration 8, 2 at iteration 9), 9 declared quasi-complete (iterations 9, 10,
10, 12, 12, 12, 12, 13, 15), 14 converged. The rule gives SAS's verdict, SAS's stop iteration and
SAS's estimates (to 1e-9 relative) on all 40 separated steps, and does not fire on any of the 14
converged ones. It also predicted, before the SAS run, the outcome of seven further inputs (below),
including which variable stays, which enters next and two stops at iteration 9.

**The port.**

- Commit `c1124e1` does not agree with it, in three places: it starts a separated fit from the
  estimates of the step before; it asks every probability to be 0.95 or more for a complete
  separation; and it applies the rule only when its own Newton fit has failed. Concrete input with
  another final model: the 400-row file of generator seed 1 with the outcome set to 1 exactly when
  age is above 55 (`out/separation/age_gt_55`, SAS run `judge/runs/sep_age_gt_55`). SAS ends with
  the model `age` (intercept -97.2666, age 1.7643) and 42 different probabilities on the training
  set; that port removes `age` and gives every applicant 0.4107.
- The port as it stands now (`f2791d1`, repository at `ee20d83`) has taken the first two parts of
  the rule and agrees on the stop iteration, the verdict and the estimates in all 38 runs. It does
  **not** have part 3. Concrete input with another final model: the same file with the outcome 1
  exactly when age is above 59. SAS: `age` enters, `utilization_debt_interaction` enters (score
  5.4160) and is removed, final model `age`. Port: `age` enters, `age_category` enters and stays,
  final model `age` and `age_category`.

## The experiment

`out/separation/exp.py`, from `judge/`: one SAS session, each data set fitted with

```sas
proc logistic data=... descending;
    model y = <candidates> / selection=stepwise slentry=0.05 slstay=0.05 itprint;
    ods output IterHistory=... ConvergenceStatus=... ParameterEstimates=... ModelBuildingSummary=... FitStatistics=... GlobalTests=...;
run;
```

and every table written to the log with 32-character numbers. Two groups:

- **Program files** (the 36 candidates of `train.sas`, in its order, on the
  `model_features_train.csv` of an earlier SAS run of the pipeline): the first-step separation
  (`small_sep60`), the quasi-complete one (`oneclass_n60_quasi`), the later-step one
  (`oneclass_n60_two_variables`), the six small generator seeds that separated (16, 17, 18, 20, 21,
  24), and seven files of 280 training rows in which age decides the outcome (thresholds 55, 59, 60,
  62, 64, 66, 71).
- **Designed data sets** of one to three variables, to vary the shape: a binary separator; a
  separator with the two classes one unit apart on 40, 400, 2,000 and 20,000 rows; the same
  rescaled; two unbalanced classes; a tie at the cut (quasi-complete); a binary quasi-complete on 30
  and 1,000 rows; two and three variables that separate only together; and data that overlap by one
  or three swapped neighbours on 40 to 2,000 rows, whose maximum likelihood estimate exists.

`out/separation/check_rule.py` replays every step from SAS's iteration 0 and applies the rule;
`out/separation/check_rule_final.out` has every step of every run.

### What the iteration histories show

Fisher scoring without step halving reproduces every SAS iterate (largest relative difference 2e-11
over all separated steps). Iteration 0 is the intercept-only estimate in all 54 steps, including the
steps after a removal and the steps after a separated step: the later-step run fixes this (its step
4 starts from -0.1911, 0, 0, not from the estimates step 3 kept).

Complete separation: stopped at iteration 8 although no observation was misclassified at iterations
6 and 7 already, so the check starts at 8. The probability of the observed response does not have to
be large:

| Run | Rows | Smallest probability of the observed response at iteration 8 | SAS |
|---|---|---|---|
| small_sep60 (program, binary separator) | 42 | 0.9999 | complete at 8 |
| later-step run, step 3 | 42 | 0.9779 | complete at 8 |
| D2, classes one unit apart | 40 | 0.8402 | complete at 8 |
| age above 59 (program) | 280 | 0.7522 | complete at 8 |
| D11, the same on 400 rows | 400 | 0.5389 | complete at 8 |
| D12, on 2,000 rows | 2,000 | 0.5078 | complete at 8 |
| D13, on 20,000 rows | 20,000 | 0.5008 | complete at 8 |
| age above 66 (program) | 280 | 0.4709 at 8 (2 misclassified), 0.6713 at 9 | complete at 9 |
| age above 71 (program) | 280 | misclassified at 8, none at 9 | complete at 9 |

Quasi-complete separation: the largest diagonal element of the standardized inverse information, at
the iteration before the stop and at the stop:

| Run | Before | At the stop | Stop |
|---|---|---|---|
| gen_s21 (program) | 2,903 | 7,700 | 9 |
| gen_s24 (program) | 2,447 | 6,652 | 10 |
| D4, tie at the cut | 2,479 | 6,792 | 10 |
| D5, binary, 30 rows | 4,615 | 12,540 | 12 |
| oneclass_n60_quasi (program) | 2,745 | 7,463 | 12 |
| D6b, one swap, 400 rows | 2,922 | 5,932 | 12 |
| D6c, one swap, 2,000 rows | 3,035 | 9,680 | 13 |
| D17, binary, 1,000 rows | 2,806 | 7,627 | 15 |

So the limit lies above 4,615 and at or below 5,932; 5000 is the documentation's figure. The
unstandardized matrix is ruled out (D4: 7,443 at iteration 9, not stopped; gen_s21: 2,574 at its
stop). When both conditions hold at iteration 8 SAS says complete (D8, gen_s16, gen_s18, gen_s20).

**SAS declares a quasi-complete separation on data that are not separated.** D6b, D6c and D21
overlap by one swapped pair, so their maximum likelihood estimate exists; the fit is slow, the
condition is met at iteration 12 or 13, and SAS stops there with its warning. With fewer rows (D6a,
40 rows; D19, 150 rows) or more overlap (D18) the fit converges first. A port that applies the rule
only to fits that fail to converge misses these.

### The Wald test and the removal

The Wald chi-square of each variable from the kept estimates and their inverse information is the
number in SAS's stepwise summary in every removal (e.g. the later-step run, step 5: computed
1.76651, SAS 1.7665; age above 66: 3.28014, SAS 3.2801). The removal decisions follow:

| Run | Kept at | Wald of the separating variable | SAS |
|---|---|---|---|
| small_sep60 | 8 | 0.3510 | removed, intercept only |
| D2, 40 rows | 8 | 1.1131 | removed |
| D11, 400 rows | 8 | 10.557 | **stays**: final model x1 = 0.3116 |
| D12, D13 | 8 | 52.8, 528 | stays |
| D6b, one swap, 400 rows | 12 | 2.9000 | removed |
| D6c, one swap, 2,000 rows | 13 | 7.1978 | stays, with the stopped estimates |
| age above 55, 59, 60, 62, 64 | 8 | 6.96 to 11.2 | stays |
| age above 66, 71 | 9 | 3.2801, 1.6944 | removed |
| later-step run, step 4 (age, credit lines) | 8 | age 1.7665 | age removed, final model credit lines |

On few rows the separating variable is thrown out; with more rows near the boundary its Wald test at
iteration 8 is significant and SAS keeps it, with coefficients that are those of iteration 8 and
nothing else.

### The entry test after a separated step that stays (part 3)

`out/separation/exp_entry.py` adds `details`, which prints the score chi-square of every candidate
at every step. After step 1 of "age above 55" (age stays, separated) SAS's 35 numbers lie between
1.65 and 2.60: none enters, and the selection ends after one step. `out/separation/entry_score.py`:

```
age > 55: Complete at iteration 8; 35 candidates; largest relative difference from SAS's score chi-square:
          U' I^-1 U over all parameters 2.7e-12; candidate's score alone 3.5e+02
   candidates that would enter on the candidate's score alone: [('age_category', 581.278, 1.6569)]
age > 62: ... U' I^-1 U over all parameters 3.5e-12 ...  [('age_category', 10.459, 1.533)]
```

The floor of about 1.65 is the score left in the intercept and in `age` by a fit stopped before its
maximum; every candidate inherits it.

### Predictions made before the SAS run

From the rule alone (`out/separation/scan_cuts.py` on the feature file, then SAS):

| Input (seed 1's file, outcome 1 when age is above) | Predicted | SAS |
|---|---|---|
| 55 (whole pipeline, `sep_age_gt_55`) | complete at 8; Wald of age 6.9641, stays; coefficients -97.2666, 1.76434; nothing enters (best candidate 2.597) | the same: one step, `age,1,1.7643,0.6686,6.9641,0.0083` |
| 62 (whole pipeline, `sep_age_gt_62`) | complete at 8; Wald 11.0326, stays; 2.46489; nothing enters | the same: `age,1,2.4649,0.7421,11.0326,0.0009` |
| 59 | stays; `utilization_debt_interaction` enters next with 5.416 | enters with 5.4160, then removed (Wald 0.6605); final model age |
| 60 | stays; `has_delinquency` enters next with 5.155 | enters, then removed; final model age |
| 64 | stays; `age_category` enters next with 4.065 | enters; then age is removed; final model age_category |
| 66 | complete at 9, not 8; Wald 3.280, removed | complete at 9; removed on 3.2801 |
| 71 | complete at 9; Wald 1.694, removed | complete at 9; removed |

The two whole-pipeline runs had 0 ERROR lines in `train.sas` itself beyond the runner's exports, and
every file was written; in both the validation and test probabilities come from the iteration-8
coefficients.

## The port against the rule

`check_rule.py` runs `sas_compat.stepwise_logistic` of a `git archive` copy of the port on every
data set and compares the steps, the final model and its coefficients with SAS.

**`c1124e1`** (38 runs: 24 the same; 8 with another sequence of steps or another final model; 1 stopped
with "did not converge" (age above 64, step 3); 4 with the same model and other coefficients; the
non-stepwise run does not apply). Two of the 8 are the tied Wald chi-squares of D7 and D10, see the
end; the others:

| Where its rule differs | Run | SAS | `c1124e1` |
|---|---|---|---|
| Complete separation needs every probability at 0.95 or more | D11 | complete at 8, x1 stays | quasi-complete at 12, x1 removed: **another final model** |
| | age above 55, age above 62 (whole pipeline) | age stays | quasi-complete / complete at 11, age removed: **another final model** |
| | D2, D3 | complete at 8 | complete at 10: same model, other printed step |
| | D12, D13 | x1 = 0.0623, 0.00623 | quasi-complete at 13, 15: x1 = 0.474, 0.106 |
| The rule only runs when its own fit failed | D6c | quasi-complete at 13, x1 stays | fit converges, x1 removed on the converged Wald: **another final model** |
| Start from the step before (corrected in `428b5c9`) | later-step run | start from the intercept-only estimates | reproduced it only by the choice of start |

**The port now (`f2791d1`)**: the same stop iteration, verdict and estimates as SAS on every
separated step of the 38 runs. Different in four runs, all through part 3 (the entry test after a
separated step that stays):

| Run | SAS's steps | Port's steps | Final model |
|---|---|---|---|
| age above 59 | age; + utilization_debt_interaction; − utilization_debt_interaction | age; + age_category | SAS: age. Port: age, age_category. **Different** |
| age above 55 | age | age; + age_category; − age_category | the same (age), other steps and printed tables |
| age above 62 | age | age; + age_category; − age_category | the same |
| age above 60 | age; + has_delinquency; − has_delinquency | age; + age_category; − age_category | the same |

(On age above 64 the two agree: there `age_category` is also SAS's next entry. On four designed runs the final fit converges and the port's coefficients differ from SAS's in the
fifth digit: SAS stops at GCONV = 1E-8, the difference already recorded in `generated-inputs.md`.)

**Smallest fix, not made:** in `stepwise_logistic`, where the score chi-square of a candidate is
computed, use U' I⁻¹ U over all the parameters of the enlarged model at the current estimates. After
a converged step the model's own scores are zero and the number is the one computed today, so
nothing else changes.

## What is not settled

- **The 0.95 of the quasi-complete condition.** In every quasi-complete run some observation was
  above 0.999 well before the stop, so 0.95 is the documentation's figure, not a measured one.
- **The limit of 5000** is bracketed between 4,615 and 5,932; the divisor of the standard deviation
  (n or n − 1) and whether the intercept's element counts do not change any of the nine verdicts.
- **A probability of exactly 0.5** at iteration 8 (the smallest seen is 0.5008).
- **The quasi-complete check before iteration 8**: no quasi-complete run met the condition before
  iteration 9, so "from iteration 8" is measured for the complete check and taken for the other.
- **The iteration limit** (25 by default): no run reached it.
- **Equal Wald chi-squares.** In the two symmetric designed sets (D7, D10) the variables tie exactly
  and SAS removed the first in model order; the port's commit `f2791d1` now does the same.
- One designed run (one swap on 20,000 rows) hung the SAS session and was dropped.
