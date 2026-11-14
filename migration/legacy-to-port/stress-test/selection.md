# Stress-test file selection (prompt 03, round 1)

The criterion is mechanical. Each inventory row's classifications are scored by risk:
- MODEL_STAT, PROC_SEMANTICS, MISSING_NULLABLE: 3;
- BUG, ORDER, ROUNDING, TYPE_GUESS, SESSION_STATE: 2;
- FORMAT, MISSING_SOURCE: 1;
- MISSING_NEVER: 0.5;
- NO_GAP, LISTING_ONLY: 0.

A file's score is the sum over its inventory rows. Computed on migration/inventory.tsv at
commit 86aa338.

| File | Rows | Score | Risky sections exercised |
|---|---|---|---|
| train.sas | 53 | 141.5 | stepwise + model fitting (§2 A5, A17), ODS tables (A19/A20), PLM store (§0), confusion/summary, BEST12/D8/D12.3/PVALUE printing |
| metrics_calculation.sas | 47 | 102.0 | KS remerge + ORDER, PROC RANK, PSI division (A13), macro (A23), INTO (A9), one-to-one merge (A6), percent width (A14) |
| predict.sas | 49 | 80.0 | MISSING_NULLABLE helpers (A1/A2), PLM restore, TYPE_GUESS guessingrows=max, test-median imputation BUG |
| feature_engineering.sas | 44 | 44.0 | held back as the fresh file for a re-round |

Selected: **train.sas, metrics_calculation.sas, predict.sas**. The proof for each section is
in the inventory rows of each file (`grep -P '^train.sas\t' migration/inventory.tsv`, etc.).
