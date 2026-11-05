# Queued RULEBOOK amendments

Rulebook changes found while building the gap inventory (prompt 02). Queued for the
human; **not applied** to `migration/RULEBOOK.md` (the rulebook is read-only to agents;
CLAUDE.md standing rule 1). Each names the rule, the inventory row that exposed it, and
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
(0.0000415%). The judge's tolerance on that cell (0.1% relative) fails it. Options:
(a) judge change: compare `Percent Tied` with an absolute tolerance of 1e-5 percentage
points (it is a printed diagnostic; Concordant/Discordant still pass at 0.1%);
(b) require the port to reproduce SAS's exact optimizer stopping point (brittle; see judge
README tolerance evidence). Recommended: (a). This is a change to the signed-off judge.

## Already in RULEBOOK v1.0

- The rule delegating every gap decision to `migration/inventory.tsv` by path (§5) was
  part of the signed-off draft, so prompt 02's "queue a delegating rule" step is done.
