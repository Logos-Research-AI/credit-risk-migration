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
