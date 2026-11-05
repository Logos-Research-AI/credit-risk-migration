# Bugfix row 1: MonthlyIncome truncation (flag `--fix-income-truncation`, off by default)

Site: `feature_engineering.py` PROC IMPORT of cs-training.csv. Marked `FIXED(post-parity, flag --fix-income-truncation)`; the BUG(port) marker stays.

## Flag off
`rm -rf out/off && migration/parity/run_contract.sh out/off`: all 10 lines PASS (fe 2/2, train 18/18, metrics 9/9 x4, predict 2/2 x2, e2e fe+predict 2/2).
Referee: `ruff format`, `ruff check`, `pyright` clean.

## Flag on
```
SPLIT=out/off/split_ids.csv   # same split as the contract
python -m credit_risk.feature_engineering --data-dir data --output-dir out/on/fe --split-ids $SPLIT --fix-income-truncation
python -m credit_risk.train --input-dir out/on/fe --output-dir out/on/train
python -m credit_risk.metrics_calculation --input-dir out/on/train --output-dir out/on/metrics
python -m credit_risk.predict --input-dir out/on/train --data-dir data --output-dir out/on/pred
```
Diff against flag-off outputs (CSV cell diffs):
- FE: only `model_features_train.csv` (57 rows) and `model_features_validation.csv` (20 rows) = the 77 incomes; columns `monthly_income`, `income_per_dependent`, `log_monthly_income`, `age_income_interaction` only. Medians unchanged (`income_medians.csv` identical).
  Example row_id 267: monthly_income 20833 -> 208333, log_monthly_income 9.944342 -> 12.246898. Changed values range 100000..3008750 (all >= 100,000).
- Downstream (expected, model refit): train (coefficients/stepwise change: 19 vs 18 rows), risk_scores, metrics (KS, Gini, deciles), predict (all 101,503 scores shift) all change. Row 4's PSI is not touched here.
