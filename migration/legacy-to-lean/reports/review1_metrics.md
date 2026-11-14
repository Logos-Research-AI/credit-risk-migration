# Review 1, metrics_calculation.sas 47-188: built-in rules and stateful steps

Reviewer: adversarial, read-only. Units: `roc_stats`, `auc_summary`, `logit_scored_valid_sorted`,
`total_good_bad` (+ `Sas.SqlAgg`, `sqlSum`, `sqlMean`, `sqlMin`, `sqlMax`, `sqlCountTrue`),
`ks_calculation`, `ks_statistic`, `confusion_metrics`, `threshold_analysis`, `decile_data`
(+ `Sas.rankGroups`, `Sas.addRanks`), and their precondition items.

Result: **no WRONG finding**. 0 WRONG, 1 OMITTED, 0 EXTRA, 4 UNSTATED-ASSUMPTION, 2 STYLE.
Every case I could check against a SAS result agrees, most of them to the bit. What is left are
behaviours fixed in the Lean without evidence or without a precondition.

## What was run

All Lean results come from `eval_decl` on the accepted statements (`α := Float`), either directly
on the unit's item or through `model_performance_metrics.evalApply` to print exact bits.

| Check | SAS side | Result |
|---|---|---|
| Unmodified script on `eval_inputs/m1` (300 rows, ties up to 15 rows, 3 missing pd, 2 missing default_flag) | `runs/m2/dump.txt`, `DUMPX` bits | `logit_scored_valid` sort order (300 rows), `ks_calculation` (300 rows x 5 new columns), `ks_statistic`, `metrics_03`, `threshold_analysis` (5 x 6), `decile_data` (300 deciles), `roc_stats` Area, `auc_summary`: **0 mismatches, bit-exact**; column order equal |
| `ks_calculation` on prefixes of the sorted dump (1, 2, 7, 40, 120 rows) with totals 239 / 59 (`DUMPM`) | first rows of the dump | bit-exact |
| `total_good_bad` | `DUMPM` 239 / 59; X13 `into` n0=4 n1=4; X13 `sqlgrp` g=3 (all missing: 0, 0); X05 (zero rows: `.`) | equal (ks_calculation bit-exact with these totals; 4, 4; 0, 0; none, none) |
| `Sas.rankGroups` | X12A g10, g20, gd10 (22 ids each, n=244 boundary ranks 24.5, 49, 73.5, 98, 147, 171.5, 196); X12C (10 ids, n=153, k=20); X12B g10, gd10, g4 (ties, 2 missing, unsorted); X12E1, E2, E3 | all equal |
| `ks_statistic` | X13 `remerge` (3 rows, input order), `remerge_allmiss` (2 rows, KS missing) | equal |
| Tie-heavy scenarios `judge/scenarios/edge_metrics_a/b/c` (3000 rows, pd with 2 or 3 decimals) | `judge/reference/scenarios/*/ks_statistic.csv`, `threshold_analysis.csv`, `decile_analysis.csv` (total_count per decile) | equal at printed precision; decile counts equal (ties across decile boundaries, DESCENDING) |

Answers to the specific attacks:

- First row of `ks_calculation`: both counters are set to 0 on `_N_ = 1`, the initial missing value
  is never observable. Agrees with the dump rows 1-3.
- Missing `default_flag`: takes the ELSE, so `cum_bad + 1`. Dump rows 223 and 251 (sorted index
  222, 250): `cum_bad` goes 23 to 24 and 34 to 35 on a missing flag. Last row: `cum_bad=61` with
  `total_bad_count=59`, `cum_pct_bad=1.0339`. Lean identical.
- Denominator 0 (all flags 1, or all 0) or missing: `Sas.div` gives missing, every `ks_value`
  missing, and `ks_statistic` then returns **every** row with a missing KS (X13
  `remerge_allmiss`). Lean does this (evaluated: 2 rows in, 2 rows out).
- KS maximum is taken after every row, also inside a group of tied probabilities. SAS confirms:
  `edge_metrics_a` reference KS is 0.1309 at cutoff 0.08, which is the per-row maximum
  (0.130944...); the maximum over group ends would be 0.1168 at 0.07. Same for `edge_metrics_c`
  (0.2959 against 0.2876). Lean gives 0.13094460205095354 and 0.29586436513194153.
- `BEST8.` round trip: the identity exactly for integer counts below 10^8 (X03: 123456789 gives
  `1.2346E8`), and `.` for a missing sum (X05). The condition is stated in
  `def:total_good_bad_precond`, in text only (see F5).
- Threshold literal: `(0.3 : α)` is 3FD3333333333333, the value SAS has for the macro text `0.3`
  (`DUMPX metrics_03 threshold=3FD3333333333333`; 0.4, 0.6, 0.7 likewise). `pd = 0.3` gives
  predicted 1, `0.29999999999999993` gives 0.
- Missing `pd_logistic`: `predicted = 0` (R3). Missing `default_flag`: the PROC FREQ row exists
  (missing level) and matches no branch, so it is in none of TP, TN, FP, FN.
- Last-row logic, guards, f1 grouping, `precision + recall = 0`, `TP + FP = 0`: equal to SAS on
  m2 (threshold 0.7: precision missing, recall 0, f1 missing) and on `edge_metrics_a`
  (threshold 0.5: precision 0, recall 0, f1 missing).
- `threshold_analysis`: order 0.3, 0.4, 0.5, 0.6, 0.7, concatenation in SET order. Equal.
- `decile_data`: DESCENDING, group 0 = largest probabilities, missing stays missing, input order
  kept, `decile` appended last. Equal on m2 and X12.
- Sortedness: no unit needs its input sorted to be faithful (the SAS steps do not either).

## Findings

### F1. `ks_statistic`: UNSTATED-ASSUMPTION (row order of the remerge)

- SAS, lines 105-111: `select max(ks_value) ..., pd_logistic ... where ks_value = (select max ...)`,
  no ORDER BY.
- Lean: `(ks_calculation.filter ...).map ...`, i.e. input order, with the comment
  `-- OPEN(port): row order of a remerge without ORDER BY is not guaranteed by SAS; input order observed (X13)`.
- The UNKNOWN rule asks for an explicit parameter or a precondition, as R16/P1 does for the join.
  Here the order is fixed in the definition and the marker is only a comment. Evidence for input
  order is one 6-row table (X13 `remerge`); D8(d) and D8(e) say the order is not guaranteed and
  that the remerge takes two passes.
- Input on which it matters: any table where the maximum is attained on two rows with different
  `pd_logistic`, e.g. ks_value 0.5 at pd 0.4 and at pd 0.2. Lean: rows (0.5, 0.4), (0.5, 0.2).
  SAS: UNSETTLED beyond X13. The first row is the one that `validation_summary` pairs with AUC.
- Fix direction: either a precondition "the maximum ks_value is attained on exactly one row", or
  an `arrange` parameter as in P1.

### F2. `ks_calculation`: UNSTATED-ASSUMPTION (no precondition item; input column named like a retained variable)

- SAS, lines 88-89: `set work.logit_scored_valid; retain cum_good cum_bad;`. A variable read by SET
  is reloaded from the input on every iteration (D3: naming it in RETAIN is redundant).
- Lean `ks_calculation.step`: `let r := Sas.setNum r "cum_good" s.1`, which replaces the input's
  value with the retained one.
- Input: rows (default_flag=0, pd=0.1, cum_good=7), (default_flag=1, pd=0.2, cum_good=9), totals
  (1, 1). Lean (evaluated): row 2 has cum_good=1, cum_pct_good=1. SAS by D3: row 2 reads
  cum_good=9 from the input and leaves it, cum_pct_good=9. Not run in SAS.
- `def:decile_data_precond` excludes the analogous case ("no column is named decile"); this unit
  has no precondition item at all. It should state: `default_flag` and `pd_logistic` numeric
  cells, no input column named `cum_good`, `cum_bad`, `cum_pct_good`, `cum_pct_bad`, `ks_value`.

### F3. Six units have no precondition item: UNSTATED-ASSUMPTION

- `def:ks_calculation_precond`, `def:ks_statistic_precond`, `def:confusion_metrics_precond`,
  `def:threshold_analysis_precond`, `def:auc_summary_precond`,
  `def:logit_scored_valid_sorted_precond` do not exist. Rulebook section 3 asks for column
  presence and type.
- What the Lean silently assumes: `Sas.num` reads a character or absent column as missing.
  Evaluated: `total_good_bad` on a row with `default_flag = Cell.str "1"` gives (0, 0), and
  `ks_calculation` would count that row as bad. SAS would convert or raise an error. The
  existing `total_good_bad_precond` covers this for its own unit only.
- `confusion_metrics` and `sorted` need: `default_flag`, `pd_logistic` numeric. `auc_summary`
  needs: `ROCModel` character, `Area` numeric. No 0/1 assumption is needed by `ks_calculation`,
  `total_good_bad` or `confusion_metrics`: a flag of 2 is treated as SAS treats it (evaluated).

### F4. Zero rows and all-missing levels: UNSTATED-ASSUMPTION, SAS side UNSETTLED

No experiment or document in the evidence settles these, and no precondition excludes them:

- `ks_statistic` on an empty `ks_calculation`: Lean gives no row. Whether a remerged query over
  zero rows gives zero rows or one row of missing values is not in X13 (`psisum_empty` is an
  aggregate-only query, which gives one row) nor in D8.
- `confusion_metrics` on an empty table: Lean gives no row, with the comment "an empty PROC FREQ
  output gives no row". Whether PROC FREQ creates the `OUT=` data set at all for an input with
  no observations is not in X13 or D7.
- `confusion_metrics` when every `default_flag` is missing: Lean gives one row
  (threshold, then five missing values; evaluated). X13 `freq` shows missing levels in `OUT=`
  only next to complete rows; whether `OUT=` has rows when no observation is complete is not
  shown.
- `roc_stats_precond` (one event and one non-event) implies a nonempty table for `roc_stats`
  only. A nonemptiness precondition on the imported table, shared by these units, or three
  short experiments, would close this.

### F5. Preconditions exist as text only: OMITTED

- `def:roc_stats_precond`, `def:total_good_bad_precond`, `def:decile_data_precond` are in state
  `DefinitionUnformalized` (`statement_lean` is null; `get_status` lists them under
  `statements_to_write`). Rulebook section 3: a precondition is a `def ... : Prop`.
- The texts themselves are adequate: fewer than 100000000 rows is sufficient for R19 on both
  counts; `decile` not already a column; flags missing, 0 or 1 with both classes present.
- The Lean comment of `total_good_bad` relies on "(precondition)", which today is not Lean.

### F6. Missing `BUG(port):` markers: STYLE (hides meaning)

The Lean reproduces these, correctly, but the BUG rule asks for a marker on the line and none of
the units carries one:

- `ks_calculation`, line 96-97: a missing `default_flag` is counted in `cum_bad` while
  `&total_bad_count` excludes it, so `cum_pct_bad` exceeds 1 (m2: 61 / 59 = 1.0339).
- `ks_calculation` / `ks_statistic`: `ks_value` is computed after every row, so inside a group of
  equal probabilities the KS depends on the input order of the tied rows (stable sort). Same
  multiset, two input orders, evaluated: KS 0.3333 and KS 1.0. SAS reference `edge_metrics_a`:
  0.1309 reported, 0.1168 at group ends.
- `ks_calculation`: rows with a missing `pd_logistic` sort first and are accumulated.
- `ks_statistic`: several rows when the maximum is attained several times, and one row per input
  row when every `ks_value` is missing (the marker is on `validation_summary` only).

### F7. Dependencies do not follow the data flow: STYLE

- `def:decile_data` depends on `def:credit_raw_clean` only, and `def:total_good_bad` on
  `def:credit_raw_clean`, `def:income_medians`. Both read the table PROC SORT rewrote
  (manifest upstream: `logit_scored_valid_sorted`; the Lean comment of `decile_data` and the text
  of `decile_data_precond` say "sorted"). Rulebook section 3: `depends_on` includes upstream
  units by data flow. For `decile_data` the row order of the output is the sorted order, so the
  missing edge is not cosmetic.

## Units with no finding on the Lean itself

- `roc_stats`: no finding (Area bit-exact on m2 with missing rows: 3FEA5DFC9DF7E90E; one row).
- `auc_summary`: no finding (AUC, Gini bit-exact; column order ROCModel, AUC, Gini).
- `logit_scored_valid_sorted`: no finding (300 rows in SAS's order; stable; missing first).
- `total_good_bad`, `Sas.sqlCountTrue`, `Sas.sqlMin`, `Sas.sqlMax`, `Sas.sqlSum`, `Sas.sqlMean`,
  `Sas.SqlAgg`: no finding against X13, X05, X03. `sqlSum` / `sqlMean` are not used by the units
  reviewed here.
- `confusion_metrics`, `threshold_analysis`: no finding on the Lean (bit-exact on m2).
- `decile_data`, `Sas.rankGroups`, `Sas.addRanks`: no finding (X12 and m2 equal).

## Amendments proposed

- R-new (remerge): state the row order and the zero-row result of a PROC SQL remerge, or say it
  is a parameter / precondition, as R16 does for joins (F1, F4).
- R20: add the PROC FREQ `OUT=` result for an input with no observations and for an input where
  no observation is complete (F4).
- R22: add that a variable named in RETAIN and also read by SET takes the SET value on every
  iteration, or require the precondition of F2.
- Inventory: no row is classified as a bug site, although the BUG rule says known sites are
  listed there; lines 96-97 and 105-110 are candidates (F6).
- Workspace `CLAUDE.md` forbids reading `/Users/cristophersalvi/GitHub/sas-migration-formal/sas`,
  which is this workspace; `migration/prompts/common.md` names
  `/Users/cristophersalvi/GitHub/sas-migration-formal/python` instead. I followed `common.md`.
  The line in `CLAUDE.md` needs correcting.
