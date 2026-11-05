# Bugfix row 3: test-set median imputation (flag `--fix-train-medians`, off by default)

Sites: `predict.py` (test_income_medians) and `feature_engineering.py` (new extra file `income_medians.csv`, written always, not judged). Marked `FIXED(post-parity, flag --fix-train-medians)`.
CLI: `predict --fix-train-medians --medians <income_medians.csv>`; `--medians` is required only with the flag (argparse error otherwise; `run()` raises ValueError).

## Flag off
`rm -rf out/off && migration/parity/run_contract.sh out/off`: all 10 lines PASS (the extra income_medians.csv does not affect judged files). Referee clean.

## Flag on
Training medians (flag-off FE run): `1:2557, 2:4666, 3:6000, 4:6333, 5:5313` (cs-test medians were 2516, 4667, 6000, 6260.5, 5395).
```
python -m credit_risk.predict --input-dir out/off/r2_train --data-dir data --output-dir out/on/pred_med --fix-train-medians --medians out/off/r1_fe/income_medians.csv
(same with --data-dir out/off/edge_data -> out/on/pred_edge_med)
```
- cs-test: 16,613 of the 101,503 rows change (the rows with imputed income). `test_predictions.csv`: `monthly_income`, `pd_logistic`, `credit_risk_score`; `kaggle_submission.csv`: `pd_logistic`. Max |delta pd| = 0.00076.
- edge_predict: null monthly_income 5,881 -> 0. 21,513 rows change (under-30 rows go from null score to scored): monthly_income, total_risk_flags, pd_logistic, pred_logistic, credit_risk_score, risk_grade, recommendation, interest_rate. Example row 5 (age 27): monthly_income null -> 2557, pd null -> 0.075679; row 10: pd null -> 0.626506.
