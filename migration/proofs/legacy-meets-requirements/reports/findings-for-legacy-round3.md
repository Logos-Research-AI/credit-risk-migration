# Findings for the legacy code, round 3 (2026-11-15)

From the third proving round (workflow run wf_26e440d7-985 for 21 contracts, then an agent team
for the last six; `team-trial.md` has the full account). 24 contracts proved, Q11 by
construction, two disproved and checked. Both corrections were approved by the owner (rulings G44
and G45).

## Q27: the scoring script stops on a test file with no applicant (G44)

- **Input.** A valid training file and a test file with its header line and no data row.
- **Demanded.** On a valid input every step produces its result: here, prediction files with
  their header lines only.
- **Produced.** `PROC IMPORT` fails on a file with no data line, `WORK.TEST_RAW` is not created,
  `columns_ok` stays 0 and the script stops with `abort cancel`.
- **Evidence.** `migration/legacy-to-lean/experiments/x21_review_round2`, part C (log lines 262
  and 295).
- **Lines.** `legacy/predict.sas` 49-55 (the import), 71-86 (`columns_ok`), 123-130 (the stop).
- **Smallest change.** When `cs-test.csv` has the twelve header names and no data line, create an
  empty `WORK.TEST_RAW` with those columns instead of letting the import fail, so the check
  passes and `test_predictions.csv` and `kaggle_submission.csv` are written with header lines
  only. A file with a wrong header and no data line must still be rejected.

## Q26: capture rate and lift are missing when the validation set has no defaulter (G45)

- **Input.** A valid training file in which nobody defaulted (for example four rows, age 45,
  income 5000, other columns 0), any test file.
- **Demanded.** Every row of the decile table has capture rate and lift present; by G45 they are
  0 in this case.
- **Produced.** On each decile that holds an applicant, capture rate is 0/0 and lift is 0/0, so
  SAS writes missing. Empty deciles already show 0 (G41).
- **Evidence.** `judge/runs/ev5_fix_Q23_nodefaulter/decile_analysis.csv`.
- **Lines.** `legacy/metrics_calculation.sas` 272 (capture rate), 273 (lift); 260-261 pass them
  through.
- **Smallest change.** Return 0 where the value is missing (`coalesce(..., 0)`) at 260-261, or
  guard the divisions at 272-273. Check the cumulative lift table for the same division.
