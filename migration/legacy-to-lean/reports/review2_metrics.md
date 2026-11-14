# Review 2 (PROC SQL and MERGE semantics): metrics_calculation.sas 190-413

Reviewer angle: PROC SQL and MERGE, statement by statement. Read-only. Units: `decile_analysis`,
`total_defaults`, `cumulative_lift`, `train_bins`, `valid_bins`, `psi_calculation`, `psi_summary`,
`calibration_data`, `calibration_plot`, `validation_summary`, `model_performance_metrics`.
No `def:<unit>_precond` item exists for any of the eleven (all eleven lookups return "not found").

## Result

No WRONG and no OMITTED finding. 1 EXTRA, 4 UNSTATED-ASSUMPTION (all low), 0 STYLE.
Every statement, SELECT item, comparison, branch and output column was checked against the source,
and the Lean was run against SAS output (below). It agreed everywhere, to the bit except where
the `agg` parameter is involved.

## What was run

All Lean evaluations use `(α := Float)` and `agg` = left fold sum, sum / length.

| Check | Input | Outcome |
|---|---|---|
| `decile_analysis` vs `runs/m2` | the 62 real rows of the groups decile `.`, 0, 1 (ties at 0.5, one missing `default_flag`, three missing `pd_logistic`) plus 238 filler rows carrying the remaining 28 defaults, 209 non-defaults, 1 missing flag | rows `.`, 1, 2: `total_count`, `defaults`, `default_rate`, `min_pd`, `max_pd`, `capture_rate`, `lift` equal the DUMPX hex exactly; `avg_pd` of decile 1 is `3FE16FDC63B24636` against SAS `3FE16FDC63B24635` (1 ulp, the R17 accumulation, a parameter); column order equals the dump and `judge/reference/decile_analysis.csv` |
| `decile_analysis` edge cases | missing-decile group; group with all flags missing; all flags 0 (divisor 0); all flags missing (divisor missing); zero rows | missing group first with decile missing; `defaults`, `default_rate`, `capture_rate`, `lift` missing for the all-missing group (X13 `subq g=3`); `capture_rate` and `lift` missing on a zero or missing total (X13 `sqlarith`); `count(*)` counts rows with a missing flag (m2 decile 2: 28 rows, rate 16/27); zero rows give zero rows |
| `total_defaults` | flags 1, missing, 0, 0; one missing flag; zero rows | `(1, 0.333333)` with a 6-decimal `best8`; `(none, none)` for all-missing and for zero rows (X05 `sql_empty sum=[       .]`) |
| `cumulative_lift` vs `runs/m2` | first three rows of `decile_analysis`, totals `(59, 0.197987)` from DUMPM | `cum_defaults` 0, 15, 31; `cum_count` 3, 34, 62; `cum_capture_rate` and `cum_lift` equal the DUMPX hex exactly (`4001D3945937B988`, `4004340E873F279A`, `3FE0D0456C797DD5`) |
| `cumulative_lift` edge cases | the X13 `retain` data (missing `defaults` on row 1, missing `total_count` on row 2); two all-missing rows then a present one; zero and missing totals | `cd` = `.`, 3, 5 and `cc` = 5, 5, 9 as in X13 `retain`; divisions by a zero or missing total are missing; new columns in the order cum_defaults, cum_count, cum_capture_rate, cum_lift, as in the dump |
| `psi_calculation` vs `runs/m2` | train: 1 missing, 49 of bin 0, 44 of bin 7, 56 of bin 8, 350 of bin 3; valid: 28 of bin 8, 3 missing, 29 of bin 0, 30 of bin 7, 210 of bin 5 | rows `.`, 0, 7, 8 only (bins 3 and 5 are on one side and drop out, as in `runs/sb` and `runs/sc`); `train_pct`, `valid_pct`, `psi_component` equal the DUMPX hex exactly for all four rows; missing bin joins missing bin; empty train table gives zero rows |
| `psi_summary` | PSI 0.1, 0.25, 0.09999, zero rows, one missing component, 0.2 + missing + 0.04 | "Some change", "Significant change", "No significant change", missing PSI with "No significant change" (X13 `psisum_empty`), same, 0.24 "Some change"; always exactly one row |
| `validation_summary` | the X13 `merge` data (1, 2, 1 rows); AUC 0.7 / KS 0.3 / PSI missing; empty ks_statistic; AUC 0.65; empty auc_summary | row 1 "Production Ready", row 2 all of auc/psi missing and "Needs Improvement" (X13 `merge` lines); missing PSI passes `PSI < 0.25`; missing KS falls to "Requires Review"; 0.65 gives "Requires Review"; missing AUC gives "Needs Improvement"; columns as `judge/reference/validation_summary.csv` |
| `model_performance_metrics` | 0.5 row present with missing precision and f1; two ks rows; no 0.5 row; all inputs empty | 0.5 row selected, five metrics under their final names, `threshold` and `ROCModel` gone, column order equal to the header of `judge/reference/model_performance_metrics.csv`; second row has the threshold metrics missing; no 0.5 row leaves the five metrics missing on a one-row result (X13 `merge`: `threshold=. acc=.`); all empty gives zero rows |
| R24 on the four staged runs | every row of `decile_data`, `train_bins`, `valid_bins`, `calibration_data` in `runs/m2`, `sa`, `sb`, `sc` (5,880 rows, up to 294 tied values per table, missing values in m2), recomputed outside Lean with the formula of `Sas.rankGroups` | 0 mismatches; rows in input order; rank variable last |

## Findings

### F1. `psi_calculation`: UNSTATED-ASSUMPTION (low). Join row order is fixed in the definition

- SAS: lines 272-278, an inner join with no ORDER BY.
- Lean: `(psi_calculation.view train_bins).filterMap ...`, so rows come out by ascending `score_bin`,
  missing first. The only trace of the question is a comment `-- OPEN(port): the row order of a join
  without ORDER BY is not guaranteed by SAS; key order observed`.
- Rule: R16 says join row order is not determined and "a unit that exposes join order takes the
  arrangement as a parameter"; the UNKNOWN rule asks for "a function argument with a comment
  `OPEN(port)`" or a precondition. Here there is a marker and no parameter. `inventory.tsv` line 275
  says "psi inner join: key order", status "open: row order", so the inventory and R16 disagree.
- Evidence for the order chosen: X13 `join` lines (`.`, 0, 2) and all four staged runs come out in
  key order; each side has one row per key, so the "scrambled inside a key" effect of X13 `leftjoin`
  cannot occur. D8(f) still says the order is not guaranteed.
- No input on which the Lean is known to differ from SAS. The order is visible in the printed
  listing (`judge/reference/printed_psi_calculation.csv`) and in the list handed to `agg` by
  `psi_summary`.

### F2. `decile_analysis`: UNSTATED-ASSUMPTION (low). `GROUP BY decile` is read as the input column, with no precondition on the values of `decile`

- SAS: `select decile + 1 as decile, ... group by decile order by decile` (194, 204, 205).
- Lean: groups on `Sas.num r "decile"` of the input and orders by it.
- X01b, cited for this site, cannot tell the two readings apart: on deciles 0, 0, 1, 2 grouping on the
  column and grouping on the alias `decile + 1` give the same three groups, because `+ 1` is
  one-to-one there.
- It can matter only when two distinct input values have the same `decile + 1` in binary64.
  Input: two rows with `decile` 0 and 1e-20. Lean: two output rows, both with `decile = 1` (run).
  SAS grouping on the alias would give one row with `total_count = 2`. Which SAS does: UNSETTLED.
- On the output of PROC RANK (`decile` in 0..9 or missing) the two readings coincide, so the pipeline
  is unaffected. The Lean takes any table and states no such domain.

### F3. `model_performance_metrics`: EXTRA. `evalApply` and six dependencies with no SAS counterpart

- Lean: `def model_performance_metrics.evalApply {β γ : Type} (f : β → γ) (x : β) : γ := f x`, with a
  comment saying it is an evaluation harness, and the item depends on `def:cumulative_lift`,
  `def:calibration_plot`, `def:validation_summary`, `def:final_model_output`,
  `def:logistic_association`, `def:logistic_lackfit`, none of which lines 390-413 read.
- SAS: nothing. The step reads `auc_summary`, `ks_statistic`, `psi_summary`, `threshold_analysis`.
- It does not change what `model_performance_metrics` computes. It does make the dependency graph
  claim data flow that does not exist (RULEBOOK section 3: `depends_on` is helper homes plus upstream units
  by data flow), and any change to those six units invalidates this item.

### F4. `total_defaults`: UNSTATED-ASSUMPTION (low). `best8` is applied to the integer sum with nothing constraining it

- SAS: line 215, `into :total_defaults, :overall_default_rate`.
- Lean: `(Sas.sqlSum agg ...).map best8` and `(Sas.sqlMean agg ...).map best8`.
- R19 and `inventory.tsv` line 215 say an integer below 10^8 reads back unchanged "(precondition)"
  and only otherwise is the round trip the parameter. The Lean routes the sum through the parameter
  too, and no precondition item says `best8 x = x` on such integers or that `default_flag` is 0 or 1.
  With flags 1, 0, 0 and a `best8` that is not the identity on 1, the Lean's `&total_defaults` is
  not 1, while SAS stores `       1` (X03 `s1=[       1]`).
- The missing case is right: `.map` leaves a missing value missing, matching X05 `[       .]`.

### F5. All eleven units: UNSTATED-ASSUMPTION (low). No precondition items

- RULEBOOK section 3 asks for `def:<name>_precond` covering column presence and type, value domains and
  "anything the Lean needs to be faithful". None exists for these units.
- What the Lean relies on silently: a column that is absent or character reads as missing through
  `Sas.num` where SAS would stop with an error; `merge11` is given fixed variable lists
  (`ROCModel, AUC, Gini`; `KS_Statistic, KS_Cutoff`; `PSI, PSI_interpretation`;
  `threshold` + five metrics) that must be the real variables, in order, of the inputs; F2 and F4.

## Units with no finding

- `cumulative_lift`: first-row assignment, sum statements, both divisions with their grouping, column
  order, zero rows: all as SAS.
- `train_bins`, `valid_bins`, `calibration_data`: `GROUPS=10`, 10, 20, ascending, rank variable
  appended: as SAS on every row of four runs.
- `psi_summary`: one row always, missing branch, thresholds, strings: as SAS.
- `calibration_plot`: SELECT order `pred_bin, mean_predicted, mean_actual, bin_count`, group and
  order on `pred_bin`, missing bin first, `count(*)` over all rows: as SAS (m2 dump, reference
  header).
- `validation_summary`: MERGE rows, variables after LENGTH, AND with missing operands, ELSE IF order,
  the three status strings: as SAS.
- `model_performance_metrics`, apart from F3: `WHERE=` against the stored 0.5 (`3FE0000000000000` in
  the dump, an exact literal), RENAME= then RENAME statement, DROP, column order, no-0.5-row case: as
  SAS. Filtering before renaming is equivalent here because `threshold` is not renamed.

## Points checked and left as the rulebook has them

- The values handed to `agg` are the present values in table row order, and one `agg` serves every
  query. That is R17/P2 as written; the 1-ulp `avg_pd` difference above is the reason it is a
  parameter.
- The divisors of `capture_rate` and `lift` are computed over every row of `decile_data`, including
  the rows of the missing-decile group, skipping missing flags. Confirmed by m2: 59 and 59/298.

## Amendments proposed

1. R16 / section 4 P1 against `inventory.tsv` line 275: decide whether the psi inner join takes an
   `arrange` parameter or whether key order is the rule for a join whose two sides have unique keys.
   At present the unit follows the inventory and contradicts the wording of R16.
2. Section 4 P3 lists `best8` under `cumulative_lift`; the Lean takes it in `total_defaults`
   (lines 212-217), and `cumulative_lift` takes the resulting pair `totals`.
3. R19: either add the precondition it mentions (`best8` is the identity on integers below 10^8,
   or the sum bypasses `best8`) or drop the word "precondition".
4. `inventory.tsv` line 204: add the alias-or-column question for `GROUP BY decile`, with a note
   that X01b does not discriminate and that it is immaterial for integer deciles.
5. Section 3: say whether an evaluation-only helper and evaluation-only dependencies are allowed in
   a code item (F3).

## Note on the workspace rules

`CLAUDE.md` in this folder lists `/Users/cristophersalvi/GitHub/sas-migration-formal/sas` (this
workspace) among the paths never to read; `migration/prompts/common.md` gives the intended path,
`.../sas-migration-formal/python`. I followed `common.md`. Nothing outside this workspace and the
blueprint `sas-credit-risk-spec` was read.
