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

## Batch 2 (fan-out): queued, NOT applied

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
