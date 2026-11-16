# Empty validation set: what the SAS program and the port each do

Measured on 2026-11-16. No code was changed. Everything below was run; the working files are in
`out/empty_validation/` (git-ignored) and the SAS runs in `judge/runs/emptyval_*` (git-ignored).

## Result

1. **SAS's own split leaves the validation set empty exactly when the training file has 1, 2 or 3
   rows** (not only 1 or 2). The training set gets `ceil(0.7 n)` rows; from n = 4 on the validation
   set has `floor(0.3 n) >= 1` rows.
2. **On no such input does either program complete.** Feature engineering completes in both and the
   three files agree. After that:
   - SAS: `PROC IMPORT` cannot read the header-only `model_features_validation.csv`
     ("Unable to sample external file, no data in first 5 records. ERROR: Import unsuccessful").
     `train.sas` has no stop there, runs on to its end with ERRORs and writes part of its files.
   - Port: `train` raises an uncaught error and writes none of train's exports.
3. **There are valid inputs on which SAS writes results that the port does not write**: n = 2 or 3
   with both classes present. There SAS's fit converges, `train.sas` writes a right
   `risk_scores_train.csv`, `final_model_output.csv` and `model_coefficients.csv`, and `predict.sas`
   then runs with 0 ERRORs and writes `kaggle_submission.csv` and `test_predictions.csv`. The port
   writes none of the five. The reverse case (port completes, SAS does not) was not found.
   With one class only (every n = 1 input; n = 2, 3 with one class) neither fits: SAS says "All
   observations have the same response", the port "the fit at step 0 did not converge"; neither
   writes a model, and predict stops in both.
4. Neither program meets Q27 ("on an input that meets the conditions of section 3, every step
   produces its result") on these inputs: section 3 of `migration/requirements/requirements.md` asks
   no minimum number of rows, so a 2-row file with both classes is valid, and on it SAS's train
   writes a `risk_scores_validation.csv` with 9 of its 51 columns and a `model_summary.csv` with no
   row, and its metrics step writes no result.
5. **fix_Q7 and fix_Q9 complete and pass today** as feature-engineering scenarios, which is what they
   are (their README: "Run: feature_engineering.sas only"). `run_contract.sh` has no line for either.
   "Did not converge at step 0" is what `train` says when run on their output: fix_Q7 has one row and
   fix_Q9 two rows, all of outcome 0. That is the other agent's invocation, not a regression.

## 1. Which row counts give an empty validation set

`legacy/feature_engineering.sas` 322-335:

```sas
proc surveyselect data=work.credit_features out=work.credit_split samprate=0.7 seed=42 outall;
run;
data work.credit_train work.credit_validation;
    set work.credit_split;
    if selected = 1 then output work.credit_train;
    else output work.credit_validation;
```

No row is dropped before the split: the only statements that remove anything are the `abort cancel`
of lines 118-121 on an input that does not meet the conditions. So the split sees all n rows.

The same statement on data sets of n rows, in SAS (`out/empty_validation/split_counts.py`, run from
`judge/` with `uv run python ../out/empty_validation/split_counts.py`):

```
SPLIT n=1 train=1 validation=0
SPLIT n=2 train=2 validation=0
SPLIT n=3 train=3 validation=0
SPLIT n=4 train=3 validation=1
SPLIT n=5 train=4 validation=1
SPLIT n=6 train=5 validation=1
SPLIT n=7 train=5 validation=2
SPLIT n=10 train=7 validation=3
SPLIT n=20 train=14 validation=6
SPLIT n=40 train=28 validation=12
SPLIT n=100 train=70 validation=30
SPLIT n=1000 train=700 validation=300
SPLIT n=150000 train=105000 validation=45000
```

(every n from 1 to 40 was run; all 43 lines are in `out/empty_validation/split_counts.out`). Each
agrees with train = ceil(0.7 n): the sampling rate is rounded up to a whole number of rows, and an
exact product is not pushed up (n = 10 gives 7, n = 20 gives 14).

**Larger inputs.** The procedure selects a fixed number of rows, not each row with probability 0.7,
so the count does not depend on the seed or on the data. The validation set has n - ceil(0.7 n) =
floor(0.3 n) rows, which is 0 only for n <= 3. No input of 4 rows or more has an empty validation
set under SAS's own split. (Measured for n = 4 to 40, 100, 1000, 150000; for the other n it rests on
the rule.)

## 2. The runs

Inputs (`out/empty_validation/inputs/<case>/`), all valid as section 3 defines it (no missing value,
whole-number counts, distinct ids, outcome 0 or 1). The test file is the first two rows of
`legacy/data/cs-test.csv` in every case.

| Case | Rows | Outcomes |
|---|---|---|
| n1_class0 | 1 | 0 |
| n1_class1 | 1 | 1 |
| n2_both | 2 | 0, 1 |
| n2_class0 | 2 | 0, 0 |
| n3_both | 3 | 0, 1, 0 |
| n3_class0 | 3 | 0, 0, 0 |
| n4_both | 4 | 0, 1, 0, 1 (control: validation has 1 row) |

SAS, from `judge/`, all four scripts in one session:

```
uv run python run_sas.py --run-id emptyval_<case> --data-dir ../out/empty_validation/inputs/<case>
```

Port, with the split SAS made (the row_ids of SAS's `model_features_train.csv`), the modules and
arguments of the contract's e2e line, every step run and its exit code recorded:

```
bash out/empty_validation/port_run.sh <case> out/empty_validation/inputs/<case> judge/runs/emptyval_<case>
```

### SAS

ERROR lines per script (`out/empty_validation/sas_runs.out`). The train count includes the ERRORs of
the runner's own added exports of printed tables (`run_sas.py` instrumentation), which are not the
program's: on n2_both, 7 of the 22 are the program's.

| Case | fe | train | metrics | predict | Fit |
|---|---|---|---|---|---|
| n1_class0 | 0 | 37 | 64 | 3 | "All observations have the same response. No statistics are computed." |
| n1_class1 | 0 | 37 | 64 | 3 | same |
| n2_both | 0 | 22 | 64 | 0 | "Convergence criterion (GCONV=1E-8) satisfied", intercept only |
| n2_class0 | 0 | 37 | 64 | 3 | same response |
| n3_both | 0 | 22 | 64 | 0 | converged, intercept only |
| n3_class0 | 0 | 37 | 64 | 3 | same response |
| n4_both | 0 | 17 | 3 | 0 | converged, intercept only |

The program's own ERRORs in `train.sas` on n2_both (`judge/runs/emptyval_n2_both/train.sas.log`):

```
proc import datafile="&output_path/model_features_validation.csv" ...
Unable to sample external file, no data in first 5 records.
ERROR: Import unsuccessful.  See SAS Log for details.
proc plm restore=work.logit_model; score data=work.model_features_validation ...
ERROR: File WORK.MODEL_FEATURES_VALIDATION.DATA does not exist.
proc freq data=work.logit_scored_valid noprint;        ERROR: Variable DEFAULT_FLAG not found.
proc freq data=work.risk_scores_validation;            ERROR: Variable DEFAULT_FLAG not found.
/* ROC analysis for validation set */                  ERROR: Variable DEFAULT_FLAG not found.
proc print data=work.roc_valid;                        ERROR: File WORK.ROC_VALID.DATA does not exist.
data work.model_summary;                               ERROR: File WORK.ROC_VALID.DATA does not exist.
```

`metrics_calculation.sas` fails the same way on the header-only `risk_scores_validation.csv`
("Import unsuccessful", then "File WORK.LOGIT_SCORED_VALID.DATA does not exist" down the script).

With one class, predict stops by its own check: "ERROR: The training medians or the model are not in
the output folder: the training steps did not complete."

Files SAS wrote (file:lines, the header counted):

```
n1_class0  final_model_output.csv:2 income_medians.csv:6 model_features_train.csv:2 model_features_validation.csv:1
           model_performance_metrics.csv:1 model_summary.csv:1 printed_confusion_train.csv:2 printed_cumulative_lift.csv:1
           printed_psi_calculation.csv:11 risk_scores_train.csv:2 risk_scores_validation.csv:1 threshold_analysis.csv:1
           validation_summary.csv:1
n2_both    final_model_output.csv:3 income_medians.csv:6 kaggle_submission.csv:3 model_coefficients.csv:2
           model_features_train.csv:3 model_features_validation.csv:1 model_performance_metrics.csv:1 model_summary.csv:1
           printed_classification.csv:52 printed_confusion_train.csv:3 printed_cumulative_lift.csv:1
           printed_fit_statistics.csv:2 printed_psi_calculation.csv:11 printed_roc_train.csv:2 risk_scores_train.csv:3
           risk_scores_validation.csv:1 stepwise_summary.csv:1 test_predictions.csv:3 threshold_analysis.csv:1
           validation_summary.csv:1
```

n1_class1, n2_class0 and n3_class0 wrote the same files as n1_class0; n3_both the same as n2_both
(the full lists are in `out/empty_validation/port_runs.out`). In n2_both:

- `risk_scores_train.csv`, `final_model_output.csv`: both rows, pd 0.5, score 725, grade E.
- `model_coefficients.csv`: `Intercept,1,0,1.4142,0.0000,1.0000,MLE`.
- `risk_scores_validation.csv`: a header of 9 columns
  (`pd_logistic,pred_logistic,base_score,score_range,credit_risk_score,risk_grade,recommendation,base_rate,interest_rate`),
  not the 51 of the file, and no row.
- `model_summary.csv`: its header with `Valid_AUC` moved to the end, and no row.
- `kaggle_submission.csv`, `test_predictions.csv`: both test rows, pd 0.5.
- the metrics files: header only (`printed_psi_calculation.csv` has its ten bins).

With one class, SAS still writes `risk_scores_train.csv` and `final_model_output.csv`, with the rows
and no probability: files of a step that did not produce its result.

### Port

`out/empty_validation/port_runs.out`:

| Case | fe | train | metrics | predict |
|---|---|---|---|---|
| n1_class0, n1_class1, n2_class0, n3_class0 | exit 0 | exit 1: `RuntimeError: stepwise_logistic: the fit at step 0 ([]) did not converge` (sas_compat.py:795) | exit 1: "Model validation stopped. Nothing is exported." | exit 1: "Test set scoring stopped. Nothing is exported." |
| n2_both, n3_both | exit 0 | exit 1: `polars.exceptions.ComputeError: cannot compare string with numeric type (i32)` (train.py:549) | exit 1, same message | exit 1, same message |
| n4_both | exit 0 | exit 0 | exit 0 | exit 0 |

Files the port wrote:

```
one class  income_medians.csv:6 model_features_train.csv model_features_validation.csv:1
n2_both    income_medians.csv:6 model.json model_features_train.csv:3 model_features_validation.csv:1
           printed_association.csv:5 printed_classification.csv:42 printed_fit_statistics.csv:2
           printed_global_tests.csv:1 printed_hl_partition.csv:2 printed_hosmer_lemeshow.csv:2
           printed_odds_ratios.csv:1 printed_rsquare.csv:1 stepwise_summary.csv:1
```

On n2_both and n3_both the port fits (it writes `model.json` and the printed tables of the fit) and
then fails scoring the validation frame: the header-only file is read with every column as text, and
`train.py` 549 compares `default_flag` with a number. No `risk_scores_*.csv`, `final_model_output.csv`,
`model_coefficients.csv` or `model_summary.csv`; predict then stops because train's exports are missing.

### Port against SAS, on the files both wrote (port mode)

| Case | fe | train | metrics | predict |
|---|---|---|---|---|
| all six empty-validation cases | 3/3 pass | n2_both, n3_both: `stepwise_summary.csv` and `printed_fit_statistics.csv` pass, `printed_classification.csv` fails (SAS 51 rows, port 41; n3: 26 against 22); others: nothing in common | nothing in common | nothing in common |
| n4_both (control) | 3/3 pass | 9/11: `model_summary.csv` fails (SAS no row, port one row), `printed_classification.csv` fails (26 rows against 22) | 8/8 pass | 2/2 pass |

The two failures of n4_both are not about an empty validation set: its one validation row has one
class, so SAS's ROC step for the validation set fails ("All observations have the same response")
and SAS's `model_summary.csv` has no row; and the classification table of a 3-row fit differs in its
rows. They are recorded here because the control showed them; they were not looked into.

## 3. fix_Q7 and fix_Q9

`migration/legacy-to-port/parity/run_contract.sh` has no line for either scenario: it runs the real
data, `edge_metrics_a/b/c` and `edge_predict` only. Run as it runs a feature-engineering line (its
`fe` command and its `judge` function), on the scenario's data, against a SAS run of the scenario
made today:

```
cd judge && uv run python run_sas.py --run-id emptyval_fix_Q7_fe --data-dir scenarios/fix_Q7 --scripts feature_engineering.sas
            uv run python run_sas.py --run-id emptyval_fix_Q9_fe --data-dir scenarios/fix_Q9 --scripts feature_engineering.sas
feature_engineering.sas: 1s, 0 ERROR, 0 new WARNING     (both)

bash out/empty_validation/fix_lines.sh
fix_Q7 fe exit=0
fix_Q7  fe       3/3 files pass (port mode)  PASS
fix_Q7 train exit=1 (not a contract line: the scenario is for feature engineering only)
RuntimeError: stepwise_logistic: the fit at step 0 ([]) did not converge
fix_Q9 fe exit=0
fix_Q9  fe       3/3 files pass (port mode)  PASS
fix_Q9 train exit=1 (not a contract line: the scenario is for feature engineering only)
RuntimeError: stepwise_logistic: the fit at step 0 ([]) did not converge
```

fix_Q7 is one row of outcome 0 and fix_Q9 two rows of outcome 0: a fit on them cannot converge, and
SAS refuses it too ("All observations have the same response", cases n1_class0 and n2_class0 above).
Against the SAS runs of 2026-11-14 (`ev_fix_Q7`, `ev_fix_Q9`) the result is the same, 3/3.

## 4. The smallest fix, not made

SAS does not complete on these inputs, so there is no completed SAS result for the port to follow;
what differs is how far each gets. Two questions are the owner's before any change:

- Is a training file of 1 to 3 rows a valid input? Section 3 does not exclude it. If it is, the SAS
  program violates Q27 there and is the first to correct (as it was for the empty test file, G44),
  and the port follows the corrected SAS.
- If it is not (a condition "at least 4 rows", or "the validation set is not empty", added to
  section 3), nothing is required of either program and nothing needs to change.

If the port is to get as far as SAS does today, the smallest change is two lines in
`port/credit_risk/train.py` after the two imports (line 51):

```python
    if model_features_validation.height == 0 and model_features_validation.columns == model_features_train.columns:
        model_features_validation = model_features_train.clear()  # a header and no row: the columns keep their types
```

Tried on a copy of the port (`out/empty_validation/trial_173646/`, `bash out/empty_validation/trial.sh`),
`port/` untouched:

```
n2_both trial train exit=0
n2_both trial metrics exit=1
  metrics_calculation.py, line 125: polars.exceptions.ComputeError: cannot compare string with numeric type (i32)
n2_both trial predict exit=0
```

(n3_both: the same.) Against the SAS runs, file by file: `risk_scores_train.csv`,
`final_model_output.csv`, `model_coefficients.csv`, `stepwise_summary.csv`,
`printed_fit_statistics.csv`, `printed_roc_train.csv`, `printed_confusion_train.csv`,
`kaggle_submission.csv`, `test_predictions.csv` pass. Three do not, and cannot while SAS is as it is:
`risk_scores_validation.csv` (the port writes the 51-column header, SAS its 9-column one),
`model_summary.csv` (the port writes one row with the validation figures missing, SAS no row) and
`printed_classification.csv` (the row difference above, not caused by the change). The metrics step
would need the same treatment of the header-only `risk_scores_validation.csv` at its own import
(`metrics_calculation.py` 106); SAS's metrics step produces nothing there to compare with.

## What was not checked

- n = 1, 2, 3 with a header-only test file (fix_Q7 and fix_Q9 have one): only their feature step was run.
- One input per class pattern and row count, not several; the split sizes for n above 40 other than
  100, 1000 and 150000 rest on the rule, not on a run.
- The two differences the n = 4 control showed (`model_summary.csv` with a one-class validation set,
  the classification table's rows on a 3-row fit).
