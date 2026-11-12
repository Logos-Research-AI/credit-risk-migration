# Queued RULEBOOK amendments

Rulebook changes found while building the gap inventory (prompt 02). The rulebook is
read-only to agents (CLAUDE.md standing rule 1): every change waits in this queue for the human.

**Batch 1 (A1–A8): APPLIED 2026-11-05** as RULEBOOK v1.1. The user approved the batch at
the prompt 02 first-20-rows gate ("I approve") and authorized it to be applied. Q1 was
answered with option (a), and the judge was changed accordingly (judge/README.md, tolerance
evidence). New amendments from the fan-out and the joint audit are queued below as A9+. Each names the rule, the inventory row that exposed it, and
the translation that goes wrong without it.

| ID | Rule | Change | Exposed by | What goes wrong today |
|---|---|---|---|---|
| A1 | §2 comparison helpers / boolean assignment | Comparison helpers `sas_compat.lt/le/gt/ge/eq` return a **non-null Boolean**; `sas_compat.flag(cond)` turns any Boolean into Int64 0/1. (Today §2 says the helpers return Int8 0/1, and also defines `flag()`: two ways to produce a flag.) | batch 1 rows 9, 10 (review 1) | one agent writes `lt(...)` (Int8), another `flag(lt(...))` (Int64): the exported text is the same, but the dtypes differ and two mappings exist |
| A2 | §2 comparisons, `if/else` chains, `case when` | Helpers are mandatory where the inventory classifies the operand **MISSING_NULLABLE**; plain polars comparisons are required where it says **MISSING_NEVER** (and the inventory row must prove never-missing for every input the program can receive). | batch 1 rows 6, 9, 16 (review 1) | §2 says chains are "built with the comparison helpers" while the inventory says plain: two answers |
| A3 | §2 PROC IMPORT | A column whose first `guessingrows` values are **all empty** becomes text of width 1 (SAS: `SeriousDlqin2yrs $1.` in cs-test.csv). | batch 1 row 4 (review 1) | the §2 spec ("numeric if every value parses") makes an all-empty column numeric |
| A4 | §0 forced structural change | The item store is created at **train.sas:90** (`store`), not :93 (`:93` is `ods output ParameterEstimates`). | batch 1 row 12 (review 2) | wrong citation in the rulebook |
| A5 | §2 PROC LOGISTIC stepwise | Replace the stepwise row by inventory batch 1 row 14 verbatim: removal before entry each step; smallest Wald χ² removed if p > 0.05; entry skips candidates aliased with the CURRENT model (relative residual < 1e-8); enter the **largest score χ²** with strict >, so ties go to the **first in MODEL order**; never select by smallest p. Verified: `migration/experiments/x02_stepwise_reference.py` reproduces SAS's 24-step path exactly. | batch 1 row 14 (review 2, REFUTED twice, then verified) | at step 5 `np.linalg.solve` raises on aliased `flag_serious_delinquency`; a smallest-p rule enters `has_delinquency` at step 1 instead of `financial_health`; a last-wins tie-break enters `flag_serious_delinquency` at step 4 |
| A6 | §2 DATA step `merge` (no BY) | Replace "positional horizontal concat of single-row frames" by: one-to-one merge, rows = the longest input, values from a shorter input are **missing** on the extra rows (experiment X01a). | batch 1 row 20 | a multi-row KS result would be concatenated wrongly or raise |
| A7 | §2 (new row) proportions | Shares and rates (`count/n`, capture rate, lift) are Float64 divisions done **after** aggregation, never inside `group_by().agg(...)`. | batch 1 row 19 (review 2) | polars 2.1 gives `0.09999999999999999` inside the aggregation, so PSI prints `1.540744E-33` instead of `0` and fails the judge |
| A8 | §2 (new row) Association table | Tied pairs use SAS's tie fuzz `|Δpd| ≤ 1e-8`; c = (C + T/2)/pairs. Depends on the human's answer to Q1 below. | batch 1 row 15 (review 2, REFUTED → UNKNOWN) | exact comparison gives 226 tied pairs vs SAS's 280 |

## Questions for the human (UNKNOWN rows)

**Q1 — Association "Percent Tied" (batch 1 row 15).** SAS counts pairs whose predicted
probabilities differ by ≤ ~1e-8 as tied (280 pairs = 0.000040773%). A correct, fully
converged port has slightly different probabilities, so the same rule gives 285 tied pairs
(0.0000415%) [corrected at the gate: 283 tied pairs, 0.0000412%; SAS's 280 is reproduced by a
1.05e-8 fuzz on the exported pd, 1e-8 gives 275]. The judge's tolerance on that cell (0.1% relative) fails it. Options:
(a) judge change: compare `Percent Tied` with an absolute tolerance of 1e-5 percentage
points (it is a printed diagnostic; Concordant/Discordant still pass at 0.1%);
(b) require the port to reproduce SAS's exact optimizer stopping point (brittle; see judge
README tolerance evidence). Recommended: (a). This is a change to the signed-off judge.
**ANSWERED 2026-11-05: (a).** Applied in judge/compare.py `ABS_CELL_TOL`. A table built by
the rule from the converged refit (283 ties) passes, the self-test is 79/79 and validation
verdicts are unchanged.

## Already in RULEBOOK v1.0

- The rule delegating every gap decision to `migration/inventory.tsv` by path (§5) was
  part of the signed-off draft, so prompt 02's "queue a delegating rule" step is done.

## Batch 2 (fan-out, A9–A31): APPLIED 2026-11-05 as RULEBOOK v1.2

The user approved the gate's recommendations ("Ok"). A10 is withdrawn and replaced by A20.

| ID | Rule | Change | Exposed by | What goes wrong today |
|---|---|---|---|---|
| A9 | §2 `select ... into :mvar` | A numeric value stored by INTO without `format=` is **BEST8. text**; the port stores `float(sas_compat.sas_best(x, 8))`. New helper `sas_compat.sas_best(x, w)` = the BEST<w>. rule (`sas_best12` = `sas_best(x, 12)`). | dstep row S297; experiment X03 | "a Python scalar variable" keeps full precision: `&overall_default_rate` is 0.0670666… instead of 0.067067 (no judged cell changes on current inputs) |
| A10 | §2 PROC EXPORT / `write_sas_csv` | The writer must also take the ODS formats the model-statistics files use (D8., PVALUE6.4 → `<.0001`, fixed 3/4/6 decimals, integer), or accept columns already formatted as text. | modelstat-fit rows | an implementer following §2 prints BEST12. (`0.0025` instead of `0.00250`; `51477.52075` where SAS exports `51478`) |
| A11 | §2 PROC SQL join | SAS SQL matches missing keys to each other; polars needs `join(..., nulls_equal=True)` where a key can be missing. | cmp-fe-predict report | unreachable today (age_group never missing); a join on a nullable key silently drops rows |
| A12 | §2 `keep` / `drop` | `keep` keeps the INPUT column order, not the order written in the statement: translate as `select([c for c in df.columns if c in KEEP])`. | dstep rows (final_model_output, test_predictions, model_summary) | `select(KEEP_LIST)` fails the judge's column-order check |
| A13 | §2 arithmetic + A7 (correction of an APPLIED amendment) | Any division whose divisor is a scalar, a literal or an aggregate (`x / 105000`, `x / pl.lit(n)`, `x / x.sum()`) must go through `sas_compat.div(a, b)`, implemented as element-wise IEEE division (numpy `np.divide` via `map_batches`, missing → missing, /0 → missing). Plain polars `/` is allowed only column-by-column. A7 ("divide after aggregation") stays, but on its own it does not prevent the trap. | arith report; orchestrator check `scratchpad/divcheck.py` | polars 2.1 computes `col / scalar` as `col * (1/scalar)` depending on chunk layout: `10500/105000` gives `0.09999999999999999` on a one-chunk frame and on a rechunked `group_by` output, so PSI prints `1.5e-33` instead of `0` even when A7 is followed; column / column gives IEEE `0.1` |
| A14 | §2 PROC EXPORT `percent8.2` | `percent8.2` keeps width 8: values ≥ 100% lose a decimal (`100.0%`), SAS's w.d shrinking rule | arith report; `judge/reference/printed_cumulative_lift.csv` and 4 scenario copies print `100.0%` | the §2 example `percent8.2 → 5.00%` suggests a fixed 2 decimals, giving `100.00%` |
| A15 | §1 CSV I/O + §2 PROC EXPORT (`sas_best12`) | `sas_compat.sas_best12` prints **E-notation for 0 < \|x\| < 1e-5**: mantissa rounded to fill 12 characters, trailing zeros stripped (`9.670322E-6`, `8.406611E-51`, `2.01153E-23`); plain notation otherwise as today. The judge's `compare.sas_best12` is plain-only and must not be copied as the port's helper. | proc shard rows (model_features_train, kaggle_submission, test_predictions, printed_psi_calculation); `scratchpad/fan/proc/best12e.py` reproduces all 31.9M BEST12 cells of the references | following §2, pd `8.406611E-51` prints `0` and `9.670322E-6` prints `0.0000096703`: the judge's format check fails kaggle_submission / test_predictions (6 cells each), model_features_*, risk_scores_*, edge_a printed_psi_calculation |
| A16 | §2 `today()` + date9. | Month names in English upper case regardless of locale: `f"{d.day:02d}{MONTHS[d.month-1]}{d.year}"` with a fixed `MONTHS` tuple, not `strftime("%b")` | proc report | under a non-English locale `strftime("%b")` gives e.g. `05NOV.2026` / `05NOVEMBRE`; the judge requires DATE9. |
| A17 | §2 model fitting inside PROC LOGISTIC | Name the Newton starting point and safeguard: start every fit from all-zero coefficients, and halve the step while -2 Log L increases (SAS's own safeguard is step-halving). Convergence stays max\|step\| < 1e-10. | review train-A | plain Newton started from the intercept-only fit (intercept = logit(ȳ), slopes 0) diverges at stepwise step 2; an implementer following §2 as written can pick that start |
| A18 | §2 PROC EXPORT (`sas_best12` rounding) | BEST12. rounds **half up from the value's 15-significant-digit form** (`Decimal(f"{x:.15g}")` quantized ROUND_HALF_UP), not from the exact binary value. Byte identity cannot be guaranteed: 39 of 149,987 cells of utilization_debt_interaction still differ by 1 unit in the 12th character (judge tolerance covers it) | experiment X04 (`migration/experiments/x04_findings.md`) | Python formatting of the exact value prints 424 cells 1 unit low (`174544.68751` vs SAS `174544.68752`) |
| A19 | §2 ODS tables of PROC LOGISTIC (TM-01) | Replace "UNKNOWN until the inventory settles each one" + "ODS's printed formats" by: each table's content and text come from its inventory row; printed text = the **stored formats of the ODS output dataset that PROC EXPORT applies** (export code in `judge/reference/listings/*.log`), never the listing's template format. Open: LackFitPartition (Q2) only. | audit TM-01 | "printed formats" read as the listing gives InterceptOnly `51477.521`; SAS exports `51478`; printed_fit_statistics.csv fails on 73 cells |
| A20 | §2 PROC EXPORT, replaces A10 (TM-03, TM-04) | One mechanism: model-statistic files are **pre-rendered text columns** built by named helpers `sas_compat.sas_d8`, `sas_d12_3`, `sas_pvalue` (PVALUE6.4, `<.0001`), `sas_best(x, w)`, plus ODS's special missing `_`; `write_sas_csv` writes str cells verbatim (empty string → empty field). New §2 rows for `sas_compat.classification_table` and `sas_compat.hosmer_lemeshow`. A10 is withdrawn. | audits TM-03, TM-04 | A10 leaves two mechanisms, calls D12.3 fixed-decimal, and misses the `_` cells of stepwise_summary.csv (writing them empty fails the judge) |
| A21 | §2 (new row) judge-instrumented exports (TM-05) | Datasets the judge exports (`run_sas.py` EXPORT_AFTER: roc_train, roc_valid, confusion_matrix_train, confusion_matrix, roc_stats, cumulative_lift, psi_calculation) → `write_sas_csv` of the dataset's FINAL state to `printed_<name>.csv` with its stored formats, even though the SAS code only PROC PRINTs them. | audit TM-05 | §2 "PROC PRINT not ported" + no export rule: an implementer drops judged files |
| A22 | §2 PROC FREQ (TM-06) | `PERCENT = sas_compat.div(100 * COUNT, N)` (A13), COUNT Int64. | audit TM-06 | the §2 formula `100·COUNT/N` in polars drifts by 1 ulp in 3 of 8 reference cells |
| A23 | §2 `%macro` (TM-10) | Same name and macro parameters, plus the WORK datasets the body reads as DataFrame parameters; returns the datasets it creates. Citation: metrics_calculation.sas:122 (not :120). | audit TM-10 | the §2 row and the macro inventory row give different signatures |
| A24 | §2 w.d / percentw.d rounding (TM-13) | `w.d` and `percentw.d` round **half away from zero from the 15-significant-digit form** (as A18 for BEST12), keeping width (A14). Rows cite `write_sas_csv`, not restated formulas. | audit TM-13 | rows restate `f'{100*x:.2f}%'` (half-even on the exact binary value) |
| A25 | §2 (new row) constants (TM-14) | `sas_compat.Z975 = 1.959963984540054` is the only normal quantile used (odds-ratio CIs, ROC CIs). | audit TM-14 | two rows write the quantile differently |
| A26 | §2 PROC SQL inner join (TM-15) | `a.join(b, on=..., how="inner", maintain_order="left", nulls_equal=True)` (A11). | audit TM-15 | no §2 row for inner join; the PSI rows invent their own |
| A27 | §4 stage signatures (FP-04) | List each stage's exact signature. FE: `run(data_dir: Path, output_dir: Path, *, split_ids: Path)`, split_ids = CSV with a `row_id` column (also in §2 SURVEYSELECT). train/metrics/predict: `run(input_dir, output_dir, *, data_dir=...)` as their rows state. | audit FP-04 | §2 says a set of row_ids, §4 a CSV path; a driver written to §4 gets a TypeError on FE |
| A28 | §1 Floating point / §2 if-else chain (FP-07) | Integer-literal `when` chains stay polars Int32 and are never cast; join keys built by the same chain on both sides. ("Float64 everywhere" applies to measured values, not category codes.) | audit FP-07 | following §1, `.then(1.0)` on one side → Int32 vs Float64 join key → SchemaError (demonstrated) |
| A29 | §2 (new row) numeric truthiness (FP-08) | `if x then` → `pl.col(x) != 0` inside `when` (missing and 0 are false). | audit FP-08 | unlisted construct; the rows invented it |
| A30 | §2 DATA step sequential statements (FP-09) | Sanction the nested-expression form for repeated reassignment of one variable (financial_health) as equivalent to successive `with_columns`. | audit FP-09 | the rule says successive `with_columns`; the rows use a nested chain |
| A31 | §0 structure / §2 helpers (FP-10, FP-11, FP-12, FP-13) | (a) format-only copy steps (`data x_export; set x; format _numeric_ best12.;`) may be elided (writer default); (b) `sas_compat.le` / `eq` have no site: keep them, marked "no site; unverified"; (c) helper branches unreachable on judged inputs (`sum(.,1)=1`, `sum(.,.)=.`, `min(.,200)=200`, `log(0)=.`, `input('')=.`) get explicit cases in the Step 2 sas_compat review; (d) PROC IMPORT note: predict.sas:27-33 (guessingrows=max at :32). | audits FP-10..FP-13 | dead or untested rules and a wrong citation |

## Questions for the human (fan-out)

**Q2 — Hosmer–Lemeshow group Totals (row `printed_hl_partition.csv`, modelstat-classify).**
SAS forms the HL groups from blocks of rows whose pd agree to within 1e-6, with the documented
group-size rule. That rule reproduces all 18 SAS HL tables exactly (reference plus 17 mutation
runs). On the fully converged fit that RULEBOOK §2 requires, rows near group boundaries move,
so 6 of the 10 group Totals differ by 1 (e.g. 10502 → 10503). The judge requires Totals to be
exact (`ABS_COL_TOL` 0, with the comment "groups are formed by count: exact", which is wrong:
grouping depends on pd). The chi-square file passes, and the observed counts are already
allowed ±2. Verified by the orchestrator: the table from SAS's pd passes, the table from the
converged pd fails only on Total. Options:
(a) judge change: Total absolute tolerance 2, the same as the observed counts;
(b) the port stops Fisher scoring where SAS does (GCONV=1e-8), which the judge README calls
brittle.
Recommended: (a). This is a change to the signed-off judge.
**ANSWERED 2026-11-05: (a).** judge/compare.py ABS_COL_TOL Total 2.0. The converged HL table passes;
self-test 81/81; validation verdicts unchanged.

## Batch 3 (formal verification, FV-*): QUEUED 2026-11-12, not applied

Queued by the coding pass on the formal-verification findings
(`sas-migration-formal/prover/findings-for-code.md`; report in
`migration/formal-verification/changes.md`). The code and the inventory already follow these;
RULEBOOK.md is unchanged until the human applies them. Ids are `FV-<finding id>`.

| ID | Rule | Change | Exposed by | What goes wrong today |
|---|---|---|---|---|
| FV-P1 | §2 ODS `Association` table (A8) and §2 PROC LOGISTIC `nofit` + `roc` | Replace "tied when \|pd_event − pd_nonevent\| ≤ 1e-8" by SAS's ROCEPS grouping, for both tables: drop rows with a missing response or probability; take the probabilities from the largest down; the first opens a group and is its top; a value joins the current group while `top − value ≤ ROCEPS`, else it opens a new group and becomes its top; a pair is concordant / discordant / tied by the groups of its two members. ROCEPS is the double `0x3E46A09E667F3BCE` = 1.0536712127723511e-8, **one ulp above** the double sqrt(2^-53) (`math.nextafter(math.sqrt(2.0**-53), 1.0)`). Area = (C + T/2)/pairs, in that operation order. | finding P1; SAS experiments `migration/experiments/x07_roc_ties.*` and `x08_roceps_boundary.*` | pairwise 1e-8: two probabilities 1.02e-8 apart are concordant in the port and tied in SAS (AUC 1 against 0.5); 0.5, 0.500000009, 0.500000018 are tied pairwise where SAS separates 0.5 from the other two; 275 tied pairs against SAS's 280 on the reference training scores |
