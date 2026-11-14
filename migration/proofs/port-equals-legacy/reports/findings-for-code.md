# Findings for the coding agent

Every contract of `informal-spec.md` (version 2.2) that is disproved today, one entry per finding,
for the code as it stands after the round 2 fixes. Updated after round 4. Paths are relative to the repository root:
Python under `python/credit_risk/`, SAS under `sas/`. "SAS rulebook" is
`sas/migration/RULEBOOK.md`. Python line numbers were read in the files on 2026-11-12; SAS line
numbers are those of round 2. "Missing" means a SAS missing value / a polars null.

Kinds:

- `port-differs-from-sas`: SAS and Python give different results on a well-formed input.
- `shared-intent-failure`: SAS and Python agree, and both fail what the pipeline was meant to do.
- `fix-defect`: a flag-on behaviour that does not do what its bug-fix record says.
- `record-inaccurate`: a statement in the migration's records that the code contradicts.

Files checked for "reach" (in round 2, not re-checked): the raw files `sas/data/cs-training.csv`
and `cs-test.csv`, the scenario inputs under `sas/judge/scenarios/`, and the SAS reference outputs
under `sas/judge/reference/`.

No Python pipeline code was run for this file: Python and SAS results come from the proved
witnesses and from reading the sources.

---

## Kind `port-differs-from-sas`

**No `port-differs-from-sas` entry is left.** No contract is disproved today by a difference
between the port and SAS on a well-formed input.

What happened to the round 2 entries:

| Round 2 finding | Today |
|---|---|
| P2, P3 age group of a missing age | Fixed: S2(b), S3(b), S24(b) and S25(b) are proved |
| P4, P5 missing values in the feature step | Fixed: S5(b), S27(b) and S31 step 05 are proved |
| P6 PROC FREQ percent with a missing level | Fixed: S8(b) and S10(b) are proved |
| P7 running sum over a missing value | Fixed for `cum_defaults`. S18(b) is still disproved, but not by this (see "Specification gaps") |
| P8 rounding helper | Fixed: H8 is proved for every value |
| P9 one-to-one merge with a shared variable | Fixed: H10 is proved for columns that share a name and have the same kind |
| P1 ROC tie rule | Fixed: H12, the four S14 contracts and the three stage files that depended on it are proved. S12(a) and S12(b) are disproved, but not by this (see "Specification gaps") |

---

## Kind `shared-intent-failure`

SAS and Python agree on each of these. Changing Python alone would make the port differ from SAS.

### N1. PSI is 0 although the score distributions differ (flag off)

- **Ids and what differs:** I1 off. With `fix_psi_bins` off each data set is ranked into its own
  ten groups, so on untied tables of equal size every bin has the same share on both sides and
  PSI is 0 whatever the shift.
- **Kind:** `shared-intent-failure`
- **Python:** `metrics_calculation.py`, `run`, lines 247-257 (the two rankings; the flag-off
  branch is line 256) and the join and terms that follow, to line 303. SAS:
  `sas/metrics_calculation.sas` lines 250-262 and 265-278.
- **Smallest input and results:** training `pd_logistic` = 0.1, 0.2; validation `pd_logistic` =
  0.8, 0.9. Both sides: groups 3 and 6 with shares 1/2 and 1/2 in both sets, every term 0,
  PSI = 0, although no validation score lies in the training range. Binned by the training
  groups the shares would be 1/2, 1/2 against 0, 1.
- **Reach:** reached by the judged data: the reference `validation_summary.csv` has PSI 0.0000.
- With the flag on this intent now holds: PSI is 0 exactly when the two sets have the same share
  in every training bin (I1 on, proved).

### N2. Test incomes are imputed from the test set (flag off)

- **Ids and what differs:** I2 off. With `fix_train_medians` off the medians used to impute test
  incomes are computed from the test file, not taken from training.
- **Kind:** `shared-intent-failure`
- **Python:** `predict.py`, `run`, lines 48-63 (medians of the test set; the `BUG(port)` comment
  is on lines 44-46). SAS: `sas/predict.sas` lines 59-73.
- **Smallest input and results:** supplied medians for age groups 1 to 5 of 3000, 4000, 5000,
  6000, 7000; test table of one row, `age` = 45, `MonthlyIncome` = 1. Both sides return the
  medians of the test set (one row), not the supplied table (five rows).
- **Reach:** every predict run with the flag off.

### N3. `flag_low_income` is set for a missing income (both copies now)

- **Ids and what differs:** I3 on the predict feature step, and now also I3 on the
  feature-engineering step. A missing `monthly_income` gives `flag_low_income` = 1 and adds 1 to
  `total_risk_flags`. The feature-engineering step failed this intent as soon as it was made to
  follow SAS (round 2 finding P4); round 2 said it would.
- **Kind:** `shared-intent-failure`
- **Python:** `feature_engineering.py`, `run`, line 179 (and `total_risk_flags`, lines 185-191);
  `predict.py`, `run`, line 176 (and lines 191-197). SAS: `sas/feature_engineering.sas` line 172,
  `sas/predict.sas` line 171 (`flag_low_income = (monthly_income < 2500)`; a missing value is
  smaller than every number, rulebook R3).
- **Smallest input and results:** one row of the step-05 input with `monthly_income` missing
  (the predict witness: `age` 45, `num_dependents` 0, the late counts 0, `credit_utilization` 10,
  `debt_ratio` 10, `num_credit_lines` 5): `flag_low_income` = 1 on both sides, in both copies.
- **Reach:** predict: reached by `edge_predict` (5,881 rows with a missing income). Feature
  engineering: not reached; every age group of `cs-training.csv` has incomes, so no income stays
  missing after imputation.

### N4. A missing ratio is capped at the cap

- **Ids and what differs:** I4, capping. A missing `debt_ratio` gives `debt_ratio_capped` = 500
  (and a missing `credit_utilization` gives `credit_utilization_capped` = 200).
- **Kind:** `shared-intent-failure`
- **Python:** `feature_engineering.py`, `run`, lines 211-216; `predict.py`, `run`, lines 211-212.
  SAS: `sas/feature_engineering.sas` lines 200-201, `sas/predict.sas` lines 199-200 (`min(x, cap)`
  skips a missing argument, rulebook R11).
- **Smallest input and results:** one row with `debt_ratio` missing: `debt_ratio_capped` = 500 on
  both sides.
- **Reach:** not reached. Utilization and debt ratio are never missing in the judged files.

### N5. An age group with no income leaves the income missing

- **Ids and what differs:** I4, imputation (the round 2 disproof stands; this contract kept its
  proof and was not touched in round 3).
- **Kind:** `shared-intent-failure`
- **Python:** `feature_engineering.py`, `run`, the left join and imputation expression of step 04
  (lines 94-103 in round 2); `predict.py`, `run`, lines 99-119. SAS:
  `sas/feature_engineering.sas` lines 97-119, `sas/predict.sas` lines 97-118.
- **Smallest input and results:** a cleaned row with `MonthlyIncome` missing and an age group
  that has no medians row: `monthly_income` missing on both sides.
- **Reach:** training side not reached; the predict copy is reached by `edge_predict`.

### N6. Grades do not follow the model card's probability bands

- **Ids and what differs:** I5, bands. A probability of 0.4 scores 750 and is graded A; the
  model card (`sas/MODEL_CARD.md`) says A is below 10 %. 0.4 lies in none of the card's bands for
  A to D.
- **Kind:** `shared-intent-failure`
- **Python:** `train.py`, `run`, lines 569-585 and 613-629 (score and grade chain); `predict.py`,
  `run`, lines 246-263. SAS: `sas/train.sas` lines 219-227 and 253-260, `sas/predict.sas` lines
  237-245.
- **Smallest input and results:** one row with `pd_logistic` = 0.4: `credit_risk_score` =
  600 + 250 * 0.6 = 750, `risk_grade` = A on both sides. (0.2 gives 800 and A, as in round 2.)
- **Reach:** reached by the judged data (round 2: 11,510 training rows and 5,047 validation rows
  graded A with a probability of 0.10 or more).

### N7. A missing probability is predicted "no default"

- **Ids and what differs:** I6. A row with a missing `pd_logistic` gets `pred_logistic` = 0.
- **Kind:** `shared-intent-failure`
- **Python:** `predict.py`, `run`, line 240. SAS: `sas/predict.sas` line 232.
- **Smallest input and results:** one row with `pd_logistic` missing: `pred_logistic` = 0 on both
  sides.
- **Reach:** reached by `edge_predict` (5,881 rows).

### N8. `ks_statistic` can have more than one row

- **Ids and what differs:** I7 (the round 2 disproof stands; not touched in round 3). Every row
  whose `ks_value` equals the maximum is kept. The restated S15 KS contract, now proved, confirms
  that both sides keep the same rows.
- **Kind:** `shared-intent-failure`
- **Python:** `metrics_calculation.py`, `run`, lines 135-138. SAS:
  `sas/metrics_calculation.sas` lines 105-111.
- **Smallest input and results:** three rows, `default_flag` = 0, 1, 0 and `pd_logistic` = 0,
  0.5, 1: two rows in `ks_statistic` on both sides.
- **Reach:** not reached.

### N9. The predict copy of step 04 has no `default_flag`

- **Ids and what differs:** S31 step 04 (stands from round 2), and I8. The training copy of the
  imputation step outputs 15 columns, the predict copy 14. For I8 this is now the only
  difference between the two copies: `flag_low_income` agrees since the round 2 fix.
- **Kind:** `shared-intent-failure`
- **Python:** `feature_engineering.py`, `run`, line 98 (present); `predict.py`, `run`, lines
  101-119 (absent). SAS: `sas/feature_engineering.sas` line 101 against `sas/predict.sas` lines
  99-115.
- **Smallest input and results:** any input. The I8 witness is one raw row with `VAR1` 1, `age`
  45, `MonthlyIncome` and `NumberOfDependents` missing, the other numbers 0 except 5 credit
  lines: the feature-engineering result has the column `default_flag`, the predict result has
  none.
- **Reach:** every run.

---

## Kind `fix-defect`

None. The round 2 entry D1 is fixed: with the floor
`min(1e-4, 0.5 / n_train, 0.5 / n_valid)` (`metrics_calculation.py` line 271) only a share of
exactly 0 is raised, and I1 with the fix on is proved. F1 on is proved in both parts.

---

## Kind `record-inaccurate`

### R1. A single-class ROC input does not give all-missing statistics

- **Ids and what differs:** C2. The record says degenerate ROC inputs return missing statistics;
  on a single-class input `TauA` is 0, not missing (the other six statistics are missing).
- **Kind:** `record-inaccurate`
- **Python:** `sas_compat.py`, `roc_association`, lines 889-938. The docstring of
  `association_table` (line 958) now states the behaviour ("tau_a is 0 on a single-class
  response"), so only the external record is inaccurate.
- **Smallest input and results:** `default_flag` = 1, 1 and `pd_logistic` = 0, 0: `TauA` = 0; the
  other six statistics missing. SAS: the SAS side defines no result for a single-class input.
- **Reach:** not reached.

### R2. The fit mask also drops rows with a missing `default_flag`

- **Ids and what differs:** C4 (the round 2 disproof stands; not touched in round 3). The record
  says rows with a missing model variable are excluded from the fit; the mask also excludes a row
  whose `default_flag` is missing.
- **Kind:** `record-inaccurate`
- **Python:** `train.py`, `run`, lines 78-83 (`fit_mask`).
- **Smallest input and results:** two rows, the candidate columns all 0, `default_flag` = 0,
  missing: the mask is true, false.
- **Reach:** not reached.

---

## Specification gaps

For the specification's author. Each contract below is disproved, but the port is not at fault
and no code change is asked.

- **S12(a), S12(b): a `default_flag` that is neither 0 nor 1 in a step frame** (newly disproved
  in round 4). Witness, the same frame for training and validation: `default_flag` = 1, 0, 2 and
  `pd_logistic` = 0.5, 0.3, 0.9. Python gives Area 1: events are the rows with flag 1, non-events
  the rows with flag 0, and the 2 is in neither class (`sas_compat.py`, `_pairs`, lines 856-882).
  SAS gives Area 1/2: everything that is not 1 is a non-event (rulebook R25). Version 2.2 gives
  "`default_flag`, when present, is 0 or 1" for stage inputs but not for step frames. No run
  reaches it: the stage input has flags 0 or 1, the steps pass the column through, and
  `model_summary.csv` is proved at stage level. Closing the gap: say in section 2 that a step
  frame that carries `default_flag` has it 0 or 1 when present, or say so on the S12 row.
- **S18(b): `decile_analysis` not sorted by decile.** Witness: `decile_analysis` of two rows in
  the order `decile` 2, 1; `total_count` 1, 1; `defaults` 0, 1. Python sorts the frame by decile
  first (`metrics_calculation.py` line 229) and returns the rows as decile 1, 2; the SAS unit
  folds the rows in the order given (`sas/metrics_calculation.sas` lines 220-235) and returns
  them as decile 2, 1. In the SAS program the order comes from `order by decile` in the step
  before (lines 191-206), and Python step 04 returns the frame sorted (line 192), so the port
  follows the SAS program and no run reaches the witness. Closing the gap: state that the step's
  input is in ascending `decile` order, or state S18(b) on step 04's outputs as S18(a) is. The
  round 3 gap in the `best8` link is closed by version 2.2.

The gaps of earlier rounds are closed: S4, S6, S10(a), S26, S15 KS, F1 on and the medians frame
by version 2.1; S2(b), S24(b), S25(b), H10 and the two ST3 summary files by version 2.2. Those
contracts are restated and proved.

---

## Proved equal to SAS (no action)

- ST1: `model_features_train.csv`, `model_features_validation.csv`.
- ST2: `risk_scores_train.csv`, `risk_scores_validation.csv`, `final_model_output.csv`,
  `model_summary.csv` (all but `risk_scores_validation.csv` conditional on `invLink`).
- ST3: `decile_analysis.csv`, `threshold_analysis.csv`, `calibration_plot.csv`,
  `ks_statistic.csv`, `validation_summary.csv`, `model_performance_metrics.csv` (the last three
  for tables of fewer than 10^8 rows).
- ST4: `kaggle_submission.csv`, `test_predictions.csv` (under the `input_best32` hypothesis).

Also proved, about the helpers and the two fixes: H8, H10, H12; F1 frame, F1 on (binning, floor, shares sum to 1), I1 on, F2
frame, F2 on, I2 on.

## Open

Nothing. All fourteen stage files are proved equal to SAS, and the ROC tie rule is confirmed: the
Python rule (`sas_compat.py` line 842, `_pairs` lines 856-882) is proved equal to the SAS rule
with the corrected constant 3184525836262887 * 2^-78 (H12).
