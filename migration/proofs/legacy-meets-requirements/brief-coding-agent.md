# Correct the legacy SAS program on the proved findings

## What this is for

The documentation of the SAS pipeline in `legacy/` was turned into formal requirements
(`migration/requirements/requirements.md`), and the SAS program was checked against them by
proof. Eleven requirements were disproved: the SAS does not do what its documentation says. The
owner has ruled that the documentation is right and approved correcting the SAS (ruling G33).

Your work list is `migration/proofs/legacy-meets-requirements/reports/findings-for-legacy.md`.
Act on the entries for **Q1, Q7, Q9, Q13, Q14, Q15, Q18, Q23, Q24, Q25, Q27** only. Each gives a
small input, what the requirement demands, what the SAS produces, the lines responsible and the
smallest change. The other entries are not yours: Q2 to Q6, Q10, Q12 and Q22 were settled by
rulings without a code change, Q11 needs none, and Q26 is still being decided.

## Rules

- **Smallest change that meets the requirement**, in the style of the surrounding SAS. Read the
  requirement itself in `requirements.md` (with its rulings) before each fix; the finding's
  suggested change is a suggestion, the requirement is the target. Change nothing else: no
  tidying, no renaming, no other behaviour.
- The same defect often sits in more than one place (`feature_engineering.sas` and `predict.sas`
  duplicate the feature engineering; `train.sas` has two scoring blocks). Fix every copy, and say
  which.
- Q13 needs the training medians in `predict.sas`: have `feature_engineering.sas` export them as a
  file in the output folder (per age group, plus the overall median) and `predict.sas` read it.
  Q14 is fixed by the Q1 fallback on both sides.
- Q27: after each PROC IMPORT, check the input conditions of section 3 of `requirements.md` and
  stop with an error before anything is exported. A faulty test file stops `predict.sas` only
  (ruling G23).
- One commit per finding, message starting with its number (`Q7: ...`). Do not touch `port/`,
  `judge/compare.py` or anything under `migration/` except where this brief says.
- You do not open any Logos blueprint.

## Evidence: run the real SAS

SAS runs on SAS OnDemand through `judge/run_sas.py` (from `judge/`, with `uv run`; see
`judge/README.md`; about five minutes for a full run; run ids are never reused). The session
profile is `oda_eu`.

1. For each finding, show the fix on the finding's own small input where a run can show it: write
   the input as a scenario under `judge/scenarios/` (name it `fix_<Qk>`), run the corrected SAS on
   it, and record what came out. If the defect cannot be shown by a run of the whole script (the
   model fit will not converge on two rows, for example), show it with a short SAS experiment
   under `migration/legacy-to-lean/experiments/` that runs the corrected statements on that input.
2. When all fixes are in, run the corrected program on the real data and on the four existing
   edge scenarios. Check the logs for errors and for warnings not in `judge/known_warnings.txt`.
3. Do **not** replace `judge/reference/` yet: put the new outputs in `judge/runs/` and name the
   run ids in your report. The orchestrator replaces the reference after reading your report.

The Python port will no longer match the corrected SAS, so `run_contract.sh` will fail against
the new outputs. That is expected and is the next step, not yours.

## Report

Return as text (do not write a report file): per finding, what was wrong in one line, the
change with file and lines, every copy fixed, the evidence run and what it showed, and the
commit. Then: the run ids of the full runs, what changed in the real-data outputs compared with
`judge/reference/` (which files, roughly how much: the model coefficients, the grade
distribution, AUC, KS, PSI), any new warning, anything you could not fix or could not show, and
anything in the findings you found to be wrong.

## Round 2 (2026-11-15): after the owner's rulings on your report

Your account of round 1 is in `migration/proofs/legacy-meets-requirements/changes.md`. The owner
accepted the empty-bin share of PSI (G35), the removal of earlier outputs (G36), the wider import
(G37) and the printing tolerance (G38). One thing changes, under the finding name **G34**:

1. **Income is zero or more (ruling G34).** Add to the input check of `feature_engineering.sas` and
   `predict.sas`: a known `MonthlyIncome` below 0 makes the file faulty. Then remove the branch
   you added for an income of -1 or less (commit 7c3aada: `log_monthly_income` and, through it,
   the else branch's effect): restore `log_monthly_income = log(monthly_income + 1)` as it was in
   both scripts. Keep everything else. Show both on a small input (a file with income -1 is
   rejected; income 0 still runs).
2. **Final runs.** Run the corrected program on the real data and the edge scenarios again
   (new run ids). If an existing edge scenario input is now rejected by the input check, say so
   and adjust the scenario's input minimally so that it still reaches the branch it was built for.
3. **Replace the reference.** The owner has read the report: replace `judge/reference/` (and
   `judge/reference/scenarios/`) with the final runs, in the same layout as now (CSVs, listings,
   `run_meta.json`), so the judge compares against the corrected SAS. Commit it separately
   (`Reference: outputs of the corrected SAS`). Do not change `judge/compare.py`, `port/` or the
   documents; those belong to the next stage.

## Round 3 (2026-11-15): after the second proving round

The corrected SAS was re-translated and all requirements decided again
(`migration/proofs/legacy-meets-requirements/reports/findings-for-legacy-round2.md`). Nineteen
are proved. The owner approved four more corrections (rulings G40 to G43). Act on these only:

1. **Q23 (G40).** The validation summary's AUC must be the exact pairwise AUC of the validation
   probabilities: (concordant pairs + half the exactly tied pairs) / (defaulters x
   non-defaulters), with Gini = 2 x AUC - 1. Compute it from exact comparisons of `pd_logistic`
   in `metrics_calculation.sas`; do not read `Area` from PROC LOGISTIC's ROCAssociation for the
   summary. Leave the PROC LOGISTIC ROC step itself in place where its printed output is used.
   Show it on an input with probabilities closer than 1e-8 but different.
2. **Q26 (G41).** `decile_analysis` always has ten rows, deciles 1 to 10; a decile that receives
   no applicant reports count 0, capture rate 0 and lift 0 (and whatever other columns the table
   has, 0 or missing as fits; say which). Show it on a validation set of fewer than ten rows and
   on one with heavily tied probabilities.
3. **Q27 (G42).** The row id must be a number: `missing(%num(VAR1))` in the input check of both
   `predict.sas` and `feature_engineering.sas`. Show a text id rejected in each.
4. **PSI floor (G43).** The floor for an empty bin reaches the PSI calculation as an 8-character
   text (it is 4.762E-6 for 105,000 rows, not 0.5/105000). Carry it at full precision.
5. **Seed evidence for Q11.** No code change: run `feature_engineering.sas` twice on the same
   file in separate sessions and record whether the split is identical (row ids and order).
6. **Final runs and reference**, as in round 2: real data and the edge scenarios under new run
   ids, logs checked, then replace `judge/reference/` (separate commit) and say what changed in
   the outputs.

Same rules as before: smallest change, every copy, one commit per finding, no change to `port/`,
`judge/compare.py` or the documents.

## Round 4 (2026-11-15): after the third proving round

Two contracts were disproved and checked; the owner approved both corrections (rulings G44 and
G45). The findings are in
`migration/proofs/legacy-meets-requirements/reports/findings-for-legacy-round3.md`. Act on these
only:

1. **Q27 (G44).** `predict.sas` scores a test file that has its header and no applicant: the
   prediction files are written with header lines only. A file with a wrong header and no data
   line is still rejected. Show both on real SAS.
2. **Q26 (G45).** In `metrics_calculation.sas`, capture rate and lift are 0 on every decile when
   the validation set has no defaulter. Look for the same division in the cumulative lift table
   and say what you did there. Show it on a validation set with no defaulter.
3. **Final runs and reference**, as in rounds 2 and 3: real data and the edge scenarios under new
   run ids, logs checked, then replace `judge/reference/` (separate commit) and say what changed
   in the outputs. In this round the corrections are made by one agent per finding and this step
   is done once, afterwards, by the integration step.

Same rules as before: smallest change, every copy, one commit per finding, no change to `port/`,
`judge/compare.py` or the documents.
