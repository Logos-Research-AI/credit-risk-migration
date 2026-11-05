# Step 6 done-gate (README Step 6) — 2026-11-05

Both counts are documented.

## 1. Parity tests, Python port vs SAS reference (judge contract, port mode)

Receipts are in `contract-results.txt` (per-run judge output); the runner is
`run_contract.sh`.

| Run | Stage | Inputs | Result |
|---|---|---|---|
| 1 | fe | data/cs-training.csv + reference split | 2/2 PASS |
| 2 | train | reference model_features_* | 18/18 PASS |
| 3 | metrics | reference risk_scores_* | 9/9 PASS |
| 4 | predict | data/cs-test.csv + run-2 model.json | 2/2 PASS |
| 5 | predict | edge_predict | 2/2 PASS |
| 6–8 | metrics | edge_metrics a, b, c | 9/9 PASS each |
| 9 | e2e | data only | fe 2/2 PASS, predict 2/2 PASS |

**10/10 judged runs pass (66/66 files).**

Python runtime is about 16 s for the whole contract (`timings.txt`). SAS takes 315 s for the
pipeline on ODA.

## 2. The original suite re-run on the original code

The repo has 0 tests. The equivalent is the judge's strict SAS-vs-SAS check.

A fresh unmodified SAS run on ODA (`judge/runs/baseline_v3`, 2026-11-05) gave:
- 0 ERROR, 0 new WARNING;
- byte-identical to `judge/reference` on **31/31 files** (`compare.py --mode strict`).

Judge validation is unchanged: 18/19 mutations CAUGHT, 1 EQUIVALENT
(`judge/validation_report.md`).
