# Small valid inputs: where the port and the SAS program differ

Measured on 2026-11-16, after ruling G57 (a training file has at least 4 rows). Nothing in `port/` or
`legacy/` was changed. `judge/generated_inputs.py` was extended (seeds 15 to 29 and a file-by-file
judging mode). Follows `empty-validation.md`, whose 4-row control showed the first two differences.

Working files: `out/small_inputs/`, `out/generated/s15` to `s29` (git-ignored, reproducible from the
seed); SAS runs: `judge/runs/gen_s15` to `gen_s29`, `gen_s29_split`, `small_sep60` (git-ignored).

## Result

Five differences on valid input, all in the train stage, all in files the contract judges. Feature
engineering passed on every input (3/3), and metrics and predict passed wherever train completed.

| | Difference | Needs | Seen on 50 rows or more |
|---|---|---|---|
| (a) | `model_summary.csv`: SAS writes the header and no row, the port one row | a validation set of one class, at any size | yes: 60 rows (seed 29) |
| (b) | `printed_classification.csv`: other rows and counts | a final model with the intercept only and few training rows | no: equal at 42 training rows (seed 29); on fits with a variable the port is exact from 35 to 700 training rows |
| (c) | SAS completes, the port stops ("did not converge") and writes nothing of train or predict | a variable that separates the two classes when it enters | yes: 60 rows (constructed, `small_sep60`); 6 of the 11 seeds of 4 to 30 rows |
| (d) | six printed tables that SAS does not make and the port writes | a final model with the intercept only | yes: 60 rows (seed 29) |
| (e) | `printed_fit_statistics.csv`, `printed_global_tests.csv`, `printed_rsquare.csv`: the port writes rows for a step SAS prints one line for | a step that removes the last variable | not seen above 30 rows (seeds 22, 25); nothing in the rule ties it to size |

(c), (d) and (e) were not asked for; the small files showed them.

None of the five files is named by a requirement. (a) carries the validation precision, recall, F1,
accuracy and AUC of Q22 and Q23, which rulings G19 and G26 leave unconstrained when a class is empty;
what is left is Q27 ("every step produces its result"), which SAS's empty `model_summary.csv` does
not meet and which is the owner's to read. (b), (d), (e) are printed tables of the fit that the
requirements do not speak of. (c) touches Q14 and Q27: SAS scores every applicant and the port
scores none.

**Why the generator did not meet them.** Its smallest training file had 300 rows, about 29 % of
applicants default and the outcome is drawn from a model of the row. So every validation set (90
rows or more) had both classes, every fit kept at least one variable, and no variable separated the
classes. All five need a small file or an outcome that carries no signal or a perfect one.

## The runs

```
cd judge
uv run python generated_inputs.py make --seed N --out ../out/generated/sN                 # N = 15 .. 29
uv run python run_sas.py --run-id gen_sN --data-dir ../out/generated/sN                   # four at a time
uv run python generated_inputs.py judge --seed N --data ../out/generated/sN --sas runs/gen_sN \
    --out ../out/generated/sN/port --with-errors --accept-warnings
```

`--with-errors` is new. `compare.py` refuses a reference run that has ERROR lines, and on these
files most SAS runs have them: the program's own (case (a)) and those of `run_sas.py`'s added
exports of printed tables that the fit did not make (case (d)). With the flag the port is judged
file by file, through `compare.compare_dir` in port mode, on the files SAS wrote; a file only one
side wrote is reported and fails the line. Seeds 1 to 14 are unchanged (seed 1 regenerated and
compared byte for byte).

Seed 29 is made in two passes: SAS's validation set for the file was read from a
feature-engineering-only run (`gen_s29_split`), then the outcome of those 18 ids was set to 0 (the
ids are in the generator). The full run made the same split.

| Seed | Rows | SAS training / validation | Defaulters training / validation | SAS's final model | SAS ERROR lines train / metrics | Port train | Differences |
|---|---|---|---|---|---|---|---|
| 15 | 4 | 3 / 1 | 2 / 0 | intercept | 17 / 3 | completes | a, b, d |
| 16 | 5 | 4 / 1 | 1 / 0 | intercept, after separation | 13 / 3 | stops | c |
| 17 | 6 | 5 / 1 | 2 / 0 | intercept, after separation | 13 / 3 | stops | c |
| 18 | 7 | 5 / 2 | 1 / 0 | intercept, after separation | 13 / 3 | stops | c |
| 19 | 8 | 6 / 2 | 2 / 2 | intercept | 17 / 3 | completes | a, b, d |
| 20 | 10 | 7 / 3 | 1 / 2 | intercept, after separation | 8 / 0 | stops | c |
| 21 | 12 | 9 / 3 | 3 / 0 | intercept, after separation | 13 / 3 | stops | c |
| 22 | 15 | 11 / 4 | 3 / 2 | intercept, after a removal | 8 / 0 | completes | b, d, e |
| 23 | 20 | 14 / 6 | 2 / 0 | intercept | 17 / 3 | completes | a, b, d |
| 24 | 25 | 18 / 7 | 5 / 3 | intercept, after separation | 8 / 0 | stops | c |
| 25 | 30 | 21 / 9 | 8 / 3 | intercept, after a removal | 8 / 0 | completes | b, d, e |
| 26 | 50 | 35 / 15 | 14 / 2 | 1 variable | 0 / 0 | completes | none of the five (see below) |
| 27 | 100 | 70 / 30 | 24 / 6 | 1 variable | 0 / 0 | completes | none of the five (see below) |
| 28 | 200 | 140 / 60 | 43 / 14 | 2 variables | 0 / 0 | completes | none: every line passes |
| 29 | 60 | 42 / 18 | 6 / 0 | intercept | 17 / 3 | completes | a, d |

Seeds 26 and 27 fail the train and predict lines on the probability only
(`pd_logistic(mean): mean |dpd| = 1.18e-05 > PD_MEAN_TOL 1e-05`, 1.88e-05 for seed 27, whose intercept
is 3.4591 in SAS and 3.4595 in the port). That is the difference already recorded in
`generated-inputs.md` for seeds 2, 6 and 8: SAS stops its fit at GCONV = 1E-8 and the port's is the
converged one. On 35 and 70 training rows the gap is larger than the judge's tolerance. Not one of
the five and not looked into further here.

Where the metrics line says 8/8, neither side wrote `printed_roc_metrics.csv` (a validation set of
one class has no ROC); the two agree.

## (a) `model_summary.csv` has no row in SAS when the validation set has one class

**Smallest input:** any 4-row file with both classes in the training set: the validation set is one
row (n = 4, 5, 6 give one validation row), so it always has one class. Seed 15; also `n4_both` of
`empty-validation.md`.

**SAS** (seed 29, `judge/runs/gen_s29/model_summary.csv`): the header, with `Valid_AUC` moved to the
end, and no row:

```
Train_AUC,train_precision,train_recall,train_f1_score,train_accuracy,valid_precision,valid_recall,valid_f1_score,valid_accuracy,model_name,training_date,training_records,validation_records,Valid_AUC
```

**Port** (`out/generated/s29/port/r2_train/model_summary.csv`): one row, the validation AUC missing:

```
Train_AUC,Valid_AUC,train_precision,train_recall,train_f1_score,train_accuracy,valid_precision,valid_recall,valid_f1_score,valid_accuracy,model_name,training_date,training_records,validation_records
0.5000,,,0.0000,,0.8571,,,,1.0000,Logistic Regression,16NOV2026,105000,45000
```

The port also writes `printed_roc_validation.csv` with one row of missing values
(`Validation Set,,,,,,,0`); SAS writes no such file.

**Where it comes from.** `legacy/train.sas` 325-331 runs `proc logistic data=work.risk_scores_validation;
model default_flag(event='1') = pd_logistic / nofit; roc ...; ods output ROCAssociation=work.roc_valid;`.
With one response level the procedure stops:

```
ERROR: All observations have the same response.  No statistics are computed.
WARNING: Output 'ROCAssociation' was not created.
```

`work.roc_valid` does not exist, and the data step of lines 392-411 that merges
`work.roc_train`, `work.roc_valid`, `work.training_metrics` and `work.validation_metrics` fails
("ERROR: File WORK.ROC_VALID.DATA does not exist", "The data set WORK.MODEL_SUMMARY may be
incomplete ... 0 observations and 14 variables"). The export then writes the 14 columns in the
order the failed step left them, and no row. `train.sas` runs on; every other file of the step is
written.

**Reach.** It needs a validation set of one class and nothing else: seeds 15, 19 (two validation
rows, both defaulters), 23 and 29 show it; seeds 20, 22, 24, 25 with both classes in the validation
set have their row. It does not depend on the fit. It occurs at any size at which all the defaulters
fall in the training set: at the real data's default rate (6.7 %) a validation set of 15 rows
(50-row file) has no defaulter about one time in three, of 30 rows one time in eight, of 150 rows
(500-row file) about 3 in 100,000.

The metrics step handles the same case (scenario `fix_Q23_nodefaulter`, rulings G19, G45): AUC and
Gini are left missing and its files are written. The training script was not given the same care.

**Smallest fix to the port, if it is to follow SAS as it is:** in `train.py`, where the validation
ROC is computed (around line 680) and the summary is assembled (734-768), when the validation set
has fewer than two outcome values write `model_summary.csv` with SAS's column order and no row, and
do not write `printed_roc_validation.csv`. About six lines. The other reading is that SAS is wrong
here (Q27: the step's summary is not produced, and the training figures it would hold are defined):
then `train.sas` is corrected to keep the row with a missing validation AUC, which is what the port
already writes, and the port does not change.

## (b) The classification table on an intercept-only fit of few rows

**Smallest input:** 4 rows (seed 15: three training rows, two of them defaulters).

SAS (`gen_s15`), 26 rows from 0.500 to 1.000; the port, 22 rows from 0.480 to 0.900 (first and last
rows, the four counts):

```
SAS   0.500,2,0,1,0   0.520,0,0,1,2   ...   0.980,0,0,1,2   1.000,0,1,0,2
port  0.480,2,0,1,0   0.500,0,0,1,2   ...   0.880,0,0,1,2   0.900,0,1,0,2
```

**Where it comes from.** The `ctable` option of the MODEL statement (`train.sas` 105): the table
counts, at each level from the smallest to the largest in steps of 0.02, the applicants whose
probability *with the applicant left out of the fit* is at or above the level.
`sas_compat.classification_table` computes that probability by one Newton step on the logit scale,
`p* = expit(eta - (y - p) q / (1 - h))`. Against SAS:

- on fits with at least one variable the port's formula reproduces every count of every level:
  seeds 26, 27, 28, 1, 3, 7, 12 (35 to 700 training rows), 0 levels differ
  (`out/small_inputs/ctable_formula.py`);
- on fits with the intercept only SAS's numbers are those of the exact leave-one-out mean,
  `p* = (defaulters - y) / (n - 1)`, which is `p - (y - p) h / (1 - h)`: for seed 15 that is 0.5
  for the two defaulters and 1.0 for the other row, SAS's range; the port's formula gives 0.486 and
  0.900. The two formulas differ by a term of the order of 1/n squared, so the port's table is
  wrong on small intercept-only fits and right again as n grows.

| Run | Training rows | SAS levels | Port levels | Leave-one-out mean |
|---|---|---|---|---|
| n2_both (below 4 rows) | 2 | 0.000 to 1.000 | 0.100 to 0.900 | 0.000 to 1.000 |
| seed 15 | 3 | 0.500 to 1.000 | 0.480 to 0.900 | 0.500 to 1.000 |
| seed 19 | 6 | 0.200 to 0.400 | 0.200 to 0.420 | 0.200 to 0.400 |
| seed 22 | 11 | 0.200 to 0.300 | 0.200 to 0.320 | 0.200 to 0.300 |
| seed 23 | 14 | 0.060 to 0.160 | 0.080 to 0.160 | 0.060 to 0.160 |
| seed 25 | 21 | 0.340 to 0.400 | 0.340 to 0.420 | 0.340 to 0.400 |
| seed 29 | 42 | 0.120 to 0.160 | 0.120 to 0.160 (equal) | 0.120 to 0.160 |

With the leave-one-out mean the range is SAS's in every run. One thing is not settled: when a
probability equals a level to the last digit (0.5, 0.3, 0.4, 1.0: common on tiny fits, where the
probabilities are small fractions) SAS counts it at that level in some runs and not in others, which
is its own floating-point arithmetic on the levels. Building the levels by repeated addition of 0.02
reproduces six of the nine runs exactly and building them as k times 0.02 the other three
(`out/small_inputs/ctable_intercept_only.py`); neither reproduces all nine.

**Reach.** It needs a final model with the intercept only *and* few training rows. From 42 training
rows the two tables were equal (seed 29, the only larger intercept-only run). It does not need a
validation set of one class (seeds 22 and 25 have both). On inputs of 50 rows or more it was not
seen; it can still occur there on an intercept-only fit when a probability falls within the
1/n-squared gap of a level.

**Smallest fix to the port:** in `sas_compat.classification_table`, when `x` has the intercept
column only, take `ps = p - (y - p) * h / (1 - h)` instead of the logit step (two lines), and take
the floor and ceiling of the range with a tolerance so that a probability of exactly 0.2 starts the
table at 0.200. That gives SAS's rows in all nine runs and SAS's counts except at a level a
probability equals exactly, which needs SAS's level arithmetic and one more experiment to pin down.

## (c) A variable that separates the classes: SAS completes, the port stops

**Smallest input seen:** 5 rows (seed 16). Constructed at 60 rows (`out/small_inputs/sep60`: seed
29's file with the outcome set to 1 exactly where `NumberOfTimes90DaysLate` is above 0; 27 defaulters).

**SAS** (`judge/runs/small_sep60`): the stepwise selection enters the separating variable on its
score test, the fit does not exist, SAS goes on, and the next step removes the variable because its
Wald test, on a fit that ran away, is not significant. The final model is the intercept alone:

```
Step  1. Effect has_serious_delinque entered:     Complete separation of data points detected.
WARNING: There is a complete separation of data points in Step 1. The maximum likelihood estimate does not exist.
WARNING: The LOGISTIC procedure continues in spite of the above warning. Results shown are based on the last maximum likelihood iteration.
Step  2. Effect has_serious_delinque is removed:  Convergence criterion (GCONV=1E-8) satisfied.

stepwise_summary.csv
1,has_serious_delinque,,1,1,42.0000,_,<.0001
2,,has_serious_delinque,1,0,_,0.3510,0.5536
```

Every applicant, training, validation and test, gets the probability 0.4523809524 and grade E,
although one variable predicts the outcome exactly. All of train's, metrics' and predict's files
are written; metrics passes against the port run on SAS's score files (9/9).

**Port:** `RuntimeError: stepwise_logistic: the fit at step 1 (['has_serious_delinquency']) did not
converge`. Nothing of train is written, and predict stops ("Test set scoring stopped").

**Where it comes from.** `train.sas` 71-119: PROC LOGISTIC with `selection=stepwise` and no option
that stops on separation. The port's stop is a recorded choice (`sas_compat.stepwise_logistic`:
"RESOLVED (post-parity): the port stops with an error on separation/non-convergence (RULEBOOK §2)"),
made when no input in hand separated.

**Reach.** Six of the eleven seeds of 4 to 30 rows (16, 17, 18, 20, 21, 24): on few rows some
candidate among 36 separates by chance. On larger files it needs an outcome that one candidate
variable determines; none of seeds 1 to 14 and 26 to 28 has it. The 60-row file shows it is not
bounded by size.

**Smallest fix to the port, if it is to follow SAS:** in `stepwise_logistic`, do not raise when the
fit of a step is separated: keep the estimates of the iteration at which the separation is found,
compute that step's tables from them, and go on to the removal test. To print SAS's numbers for the
separated step (-2 Log L 0.008, Wald 0.3510 in the 60-row run) the port must stop at the iteration
SAS stops at; SAS's detection rule was not established here and needs its own experiment. The final
model, and so every score and prediction file, does not depend on that: it is the intercept-only
fit. Whether a pipeline that answers a perfectly predictable outcome with one probability for
everyone meets the requirements is the owner's question before either program changes.

## (d) Printed tables SAS does not make on an intercept-only model

When no variable is in the final model SAS's PROC LOGISTIC makes no Association, Odds Ratios,
Hosmer-Lemeshow partition or Hosmer-Lemeshow test table, and, when no variable ever entered, no
Global Tests or R-Square table either. `run_sas.py` exports those tables for the judge; the export
fails ("File WORK._J_ASSOCIATION.DATA does not exist") and the file is not written. These are the
runner's ERROR lines, not the program's. The port writes all six, with values SAS never prints
(seed 29):

```
printed_association.csv      Percent Concordant 0.0, Percent Tied 100.0, Pairs 216, c 0.500
printed_hl_partition.csv     1,42,6,6.00,36,36.00
printed_hosmer_lemeshow.csv  0.0000,-1,,1          (-1 degrees of freedom)
printed_global_tests.csv, printed_rsquare.csv, printed_odds_ratios.csv   header only
```

**Smallest input:** 4 rows (seed 15). **Reach:** any intercept-only final model: seeds 15, 19, 22,
23, 25, 29 (60 rows). All six are judged files of the train stage; none is a file `train.sas`
itself exports. **Smallest fix:** in `train.py`, write the four tables of the final model only when
it has a variable, and the two of the steps only when a step entered one (guards around lines
240-255 and 277-393).

## (e) A step that removes the last variable

Seeds 22 and 25: a variable enters at step 1 and is removed at step 2, leaving the intercept. SAS
prints for step 2 what it prints for step 0, one line; the port prints a full step (seed 22):

```
SAS   printed_fit_statistics.csv   2,M2LOGL0,-2 Log L,=,12.890958,12.891
port  printed_fit_statistics.csv   2,AIC,AIC,,14.890958,14.891
                                   2,SBC,SC,,15.288853,15.289
                                   2,M2LOGL,-2 Log L,,12.890958,12.891
port  printed_global_tests.csv     2,Likelihood Ratio,0.0000,0,     (and Score, Wald: SAS has no step-2 rows)
port  printed_rsquare.csv          2,R-Square,0.0000,0,Max-rescaled R-Square,0.0000,0   (SAS: no step-2 row)
```

**Smallest fix:** in `train.py` where the three step tables are built (150-255), give a step whose
model has no variable the step-0 form: the single `M2LOGL0` line, and no global-tests or R-square row.

## What was not checked

- One file per size; the frequencies above are of these seeds, not estimates.
- (b): SAS's rule for a probability equal to a level, and whether an intercept-only fit of 50 rows or
  more can still differ.
- (c): the iteration at which SAS declares separation. (Quasi-complete separation, separation at a
  later step and a training set of one class were measured afterwards: next section.)
- (e) on files above 30 rows.

## A training set of one class, and more on separation (added 2026-11-16)

Measured after the five differences above. The port is the one of commit 748f4db, run from a copy
(`git archive 748f4db port/credit_risk`, in `out/oneclass/port748`), because `port/` is being changed.
Inputs `out/oneclass/inputs/`, SAS runs `judge/runs/oneclass_*`, port runs `out/oneclass/port/`
(`bash out/oneclass/port_run.sh <case>`; all output in `out/oneclass/port_runs.out`).

### (f) The training set has one class: SAS produces no model, and neither does the port

**There are valid inputs on which the SAS program produces no model.** Section 3 does not ask for
both outcomes, so a file of non-defaulters only is valid; and a file with both outcomes is valid and
still gives a one-class training set when SAS's split puts every defaulter in the validation set.

Nine inputs: 4, 10 and 60 rows (the files of seeds 15, 20 and 29), each three ways: every outcome 0;
every outcome 1; outcome 1 exactly on the rows of SAS's validation set of that file (1 of 4, 3 of 10,
18 of 60 defaulters; the split was the same as before, so the training set has no defaulter).

SAS, the same in all nine (ERROR lines: fe 0, train 36, metrics 64, predict 3):

```
proc logistic data=work.model_features_train descending; model default_flag = ... / selection=stepwise ...
ERROR: All observations have the same response.  No statistics are computed.
WARNING: The data set WORK.LOGIT_SCORED_TRAIN may be incomplete.  When this step was stopped there were 42 observations and 44 variables.
proc plm restore=work.logit_model; ...
ERROR: The file WORK.LOGIT_MODEL does not exist or it is not a valid item store.
...
NOTE: Model training completed successfully          (the script's own last %put, printed regardless)
```

- No model: no item store, no `model_coefficients.csv`.
- `train.sas` has no stop there. It runs to its end and writes `risk_scores_train.csv` and
  `final_model_output.csv` with every training row, **the probability and the score empty, grade F,
  Decline, 20.00 %**, and a prediction of 0:
  `5,0,29,2499.99,100,26.2022649,0,0,,,F,Decline,20.00%`. It writes `risk_scores_validation.csv`
  and `model_summary.csv` with a header and no row.
- `metrics_calculation.sas` cannot import the header-only validation scores and writes headers only.
- `predict.sas` stops by its own check: "ERROR: The training medians or the model are not in the
  output folder: the training steps did not complete. Test set scoring stopped. Nothing is exported."
  No prediction file.

Port (748f4db), the same in all nine: feature engineering exit 0 and its three files equal to SAS's
(3/3); train exit 1, `RuntimeError: stepwise_logistic: the fit at step 0 ([]) did not converge`,
nothing written; metrics exit 1 ("Model validation stopped. Nothing is exported."); predict exit 1
("Test set scoring stopped. Nothing is exported.").

| | SAS | Port (748f4db) |
|---|---|---|
| Model | none | none |
| Train's files | 4 written: two score files with no probability and grade F for everyone, two with a header only | none |
| Metrics' files | headers only | none |
| Prediction files | none (predict stops) | none (predict stops) |

So on these inputs neither produces a model or a prediction, and they agree on that. They differ in
what train leaves behind: SAS leaves score files that grade every applicant F without a probability
(against Q14: no unscored applicant), the port leaves nothing. A proof that assumes the SAS fit
always returns a model does not hold on valid input as section 3 stands: it needs the condition
"the training set has both outcomes", which is a condition on the split's result, not on the raw
file (the 60-row file with 18 defaulters has both outcomes and still fails).

### Quasi-complete separation: SAS completes, the port (748f4db) stops

`n60_quasi`: seed 29's file, outcome 1 for every applicant with a 90-day delinquency and for every
fourth of the others (35 defaulters). SAS: train 8 ERROR lines (all the runner's exports of tables an
intercept-only model does not make, case (d)), metrics 0, predict 0; every file written.

```
Step 1. Effect has_serious_delinque entered:   Quasi-complete separation of data points detected.
WARNING: There is possibly a quasicomplete separation of data points in step 1. The maximum likelihood estimate may not exist.
WARNING: The LOGISTIC procedure continues in spite of the above warning. Results shown are based on the last maximum likelihood iteration.
Step 2. Effect has_serious_delinque is removed:   Convergence criterion (GCONV=1E-8) satisfied.

1,has_serious_delinque,,1,1,26.0217,_,<.0001
2,,has_serious_delinque,1,0,_,0.0072,0.9325
```

As with complete separation the variable is removed on its Wald test and the final model is the
intercept: every applicant gets 0.5714285714. Port: `the fit at step 1 (['has_serious_delinquency'])
did not converge`, nothing written after feature engineering.

### Separation at a later step: SAS completes, and its final model depends on the separated fits

`n60_two_variables`: seed 29's file, outcome 1 exactly when age + 3 × credit lines is above its
median (29 defaulters): neither variable alone decides it, the two together do. SAS: 0 ERROR lines
in every script, every file written.

```
Step 1. Effect age entered:                     Convergence criterion (GCONV=1E-8) satisfied.
Step 2. Effect log_num_credit_lines entered:    Convergence criterion (GCONV=1E-8) satisfied.
Step 3. Effect num_credit_lines entered:        Complete separation of data points detected.
Step 4. Effect log_num_credit_lines is removed: Complete separation of data points detected.
Step 5. Effect age is removed:                  Convergence criterion (GCONV=1E-8) satisfied.

3,num_credit_lines,,1,3,9.7158,_,0.0018
4,,log_num_credit_lines,1,2,_,0.0000,0.9955
5,,age,1,1,_,1.7665,0.1838
final model: Intercept -2.3474, num_credit_lines 0.2448
```

The model of step 4 (age and credit lines) is still separated (-2 Log L 0.181), and SAS removes
`age` from it because the Wald test of the separated fit gives 0.1838. So here the choice of the
final model is made on estimates taken from "the last maximum likelihood iteration" of a fit that
does not exist: **a port that follows SAS on separation must stop each separated fit at the
iteration SAS stops at, or it may remove another variable and end with another model.** In the
first-step cases above the final model did not depend on that; here it does. Port (748f4db):
`the fit at step 3 (['age', 'log_num_credit_lines', 'num_credit_lines']) did not converge`.

### Not checked

- SAS's rule for the iteration at which it declares a separation and stops (it decides the Wald
  values above; PROC LOGISTIC prints an iteration history with the `itprint` option, which would
  show it).
- A one-class training set on more than 60 rows; the result does not depend on the size in the
  three sizes run.
