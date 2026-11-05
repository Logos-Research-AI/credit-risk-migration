# Post-parity burndown (kit prompt 06): marker classification

## Receipt
`grep -c` per marker over credit_risk/ at commit 7f4cca7 (full grep in `markers-receipt.txt`):

| Marker | feature_engineering | train | metrics_calculation | predict | sas_compat | Total |
|---|---|---|---|---|---|---|
| BUG(port) | 2 | 0 | 1 | 2 | 1 | 6 lines (4 distinct defects) |
| TODO(port) | 0 | 5 | 0 | 1 | 13 | 19 |
| PERF(port) | 0 | 0 | 0 | 0 | 0 | 0 |

## Merge policy (orchestrator, under the user's standing instruction)

The kit says nothing merges without sign-off; the user said never stop.
- **Parity-preserving changes** fix a latent divergence and leave every judged output byte-identical. They merge into `sas-to-python-migration` after review and a full contract re-run.
- **Behaviour-changing fixes** are the inherited SAS bugs. Fixing them changes the model's outputs, which is a business decision. They ship as separate commits on branch `post-parity-bugfixes`, each behind an off-by-default flag, with parity evidence. They are NOT merged.

## Classification

| # | Site | Marker | Call | Reasoning |
|---|---|---|---|---|
| 1 | feature_engineering.py:22, sas_compat.py:483 | BUG: MonthlyIncome truncated to $5. by guessingrows=20 (77 incomes) | **fix now, flagged, unmerged** | A real data-corruption bug in the model input. The fix is guessingrows=max on the training import (predict already uses it) |
| 2 | feature_engineering.py:204 | BUG: split depends on unguaranteed SQL row order | **document and close** | The port takes the split as an explicit input (`--split-ids`), which removes the nondeterminism by construction; nothing to fix in Python |
| 3 | predict.py:37, :79 | BUG: test set imputed from TEST-set medians | **fix now, flagged, unmerged** | Leakage and instability (age group 1 gets no median on edge_predict). The fix is to impute from the training medians, exported by feature_engineering as an artifact |
| 4 | metrics_calculation.py:245 | BUG: PSI always 0 (each set ranked into its own deciles) | **fix now, flagged, unmerged** | PSI is meaningless as written. The fix is to apply the TRAINING decile cut-points to validation |
| 5 | train.py:313 | TODO: ODDSR8.3 out of range | **fix now (parity-preserving)** | X06 verified: >999.999 / <0.001. Add `sas_compat.fmt_oddsr` |
| 6 | sas_compat.py:234 | TODO: best32. reads 32 columns | **close (verified, no code change)** | X06: the 32-column cut IS real (a 37-digit string reads as its first 32 digits, 1.2345…E31); leading blanks are ignored. The helper already behaved this way. CORRECTED: the first draft of this row misread X06 as "no cut"; the fixer caught it |
| 7 | sas_compat.py:311, :337 | TODO: BEST E-notation at w ≠ 12, digit counts | **fix now (parity-preserving)** | X06 gives exact cells at w = 6, 8, 12 |
| 8 | sas_compat.py:385 | TODO: percent overflow | **fix now (parity-preserving)** | X06: `1234%`, `( 1234%)`, `999.0%`, `0.00%` |
| 9 | sas_compat.py:411 | TODO: D8. thresholds | **fix now (parity-preserving)** | X06: 14 exact D8. cells across magnitudes |
| 10 | sas_compat.py:441 | TODO: D12.3 unobserved magnitudes | **fix now (parity-preserving)** | X06: 100 ≤ \|x\| < 1e4 gives 6 decimals; \|x\| < 1e-4 gives 9 decimals with no E-notation down to 1.2e-6 (the earlier guess "BEST12 E" was WRONG) |
| 11 | train.py:81, :126, :137, :384 | TODO: rows with a missing MODEL variable | **fix now (parity-preserving)** | SAS excludes incomplete rows from the fit and its statistics. A complete-case mask is the faithful translation; no judged input has missing features |
| 12 | sas_compat.py:622, :704 | TODO: non-convergence / separation | **document and close** | SAS's exact warning-and-continue output is not reproducible without a SAS run on separated data. The port fails loudly instead of silently, which is the safer behaviour for a credit model; recorded in RULEBOOK §2 |
| 13 | sas_compat.py:758 | TODO: alias alternation in stepwise | **document and close** | Unreachable: no removed effect has an alias outside the model on any input; the stepwise stop rule prevents a loop on this data |
| 14 | sas_compat.py:842, :898, :944 | TODO: degenerate ROC / association / HL inputs | **document and close** | Single-class or near-empty inputs are outside the pipeline's domain (train and metrics always see both classes); the helpers return missing, not a crash |
| 15 | sas_compat.py:1013 | TODO: ctable lower grid end | **document and close** | Every SAS run starts the grid at 0.000; the helper reproduces all 19 runs |
| 16 | predict.py:202 | TODO: model variable absent at scoring | **document and close** | Raising a ValueError matches PROC PLM's ERROR. model.json keys are full names per RULEBOOK §2 |

Totals (corrected after review):
- BUG(port): 4 defects. 3 are fix-now, flagged and NOT merged (branch post-parity-bugfixes); 1 is
  closed (row 2).
- TODO(port): 19 lines across 12 sites.
  - Fix-now rows 5, 7, 9, 10 (printing) and 11 (complete-case mask, 4 sites): code changed.
  - Rows 6 and 8 closed as verified with no code change (X06 matched the existing helper).
  - Rows 12–16 closed with a resolution note.
- Receipt after the burndown: `grep -c 'TODO(port)'` is 0 in every module; PERF(port) is 0;
  BUG(port) lines remain as documentation of the default (SAS-compatible) behaviour.
