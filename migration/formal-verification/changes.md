# Changes made on the formal-verification findings

Work list: `sas-migration-formal/prover/findings-for-code.md` (read 2026-11-12), under the brief
`formal/prompts/python-fixes.md`. Base commit `143ddf2`; all commits are on branch `initial`.
Line numbers under "old" are those of `143ddf2`; under "new" those of the head of the branch.

## Summary

| Finding | Outcome | Commit |
|---|---|---|
| P1 ROC tie rule | Fixed. SAS was run to settle the two open points; one of them came out differently from the rule as written (see P1) | `b2e2a49` |
| P2 age group of a missing age, feature engineering | Fixed | `599606f` |
| P3 age group of a missing age, predict | Fixed | `751c6d9` |
| P4 missing values in step 05, feature engineering | Fixed | `eb33d7f` |
| P5 missing values in step 05, predict | Fixed | `c00bd76` |
| P6 PROC FREQ percent with a missing `default_flag` | Fixed | `3778ebc` |
| P7 running sum over a missing value | Fixed | `5f7415c` |
| P8 rounding helper outside the pipeline's range | Fixed | `32c4326` |
| P9 one-to-one merge with a shared variable | Fixed | `e7e4f2b` |
| R1 single-class ROC input | Record corrected | `f7d9622` |
| R2 fit mask and `default_flag` | Record corrected | `35173b8` |
| R3 `fix_psi_bins` and `status` | Record corrected | `9946676` |
| R4 two smaller statements | One corrected; the other is not in this repository | `ff1ea35` |
| D1 PSI exactly 0 with the fix on | Code not changed; three options below | none |
| N1, N2 | Already behind flags (`--fix-psi-bins`, `--fix-train-medians`); nothing to do | none |
| N3 to N9 | No flag yet; left as candidates, code not changed | none |

The parity contract passes all ten lines with all flags off (output at the end). One judged file
changes, inside its tolerance: `printed_association.csv`, `Percent Tied`, from P1. Every other
output file of the contract run is byte-identical to the run made before the first change.

`ruff check`, `ruff format --check` and `pyright` are clean on `credit_risk/`.

`migration/RULEBOOK.md` is untouched. The amendments it needs are queued in
`migration/rulebook-amendments.md`, batch 3, ids `FV-P1` to `FV-P9`, `FV-R2`, `FV-R4`. The
affected rows of `migration/inventory.tsv` are updated (classification `MISSING_NEVER` to
`MISSING_NULLABLE` where a comparison changed).

## For the Lean re-translation: every changed line

No function was added, removed, renamed or moved. Two files have lines that moved without
changing; their shifts are in the second table.

| File | Function | Old lines | New lines | Finding | What changed |
|---|---|---|---|---|---|
| `sas_compat.py` | `le` | 102 | 102 | P4 | docstring only |
| `sas_compat.py` | `eq` | 117 | 117 | R4 | docstring only |
| `sas_compat.py` | module constants | 178 | 178 | P8 | `_TWO52` removed, `_ROUND_FUZZ_CAP = 1e-6` added; `_ROUND_FUZZ` (179) unchanged |
| `sas_compat.py` | `sas_round` (182-191) | 183-185, 189-191 | 183-185, 189-191 | P8 | docstring; the three computing lines |
| `sas_compat.py` | `sas_round_scalar` (194-201) | 196, 199-201 | 196, 199-201 | P8 | the test for the unchanged case; the three computing lines |
| `sas_compat.py` | `merge_one_to_one` (240-253 → 240-259) | 243-244, 252 | 243-244, 252-258 | P9 | docstring; the line that pads and overwrites |
| `sas_compat.py` | `_TIE_EPS` | 833 | 839-842 | P1 | value, with a three-line comment above it |
| `sas_compat.py` | `_pairs` (847-862 → 856-882) | 851-852, 854-857 | 860-872, 874-877 | P1 | grouping loop added before `ev`, `ne`; `ev`, `ne` and the four `searchsorted` lines |
| `sas_compat.py` | `roc_association` (873-918 → 893-938) | 878, 882-883 | 898, 902-903 | P1, R1 | docstring only |
| `sas_compat.py` | `association_table` (935-957 → 955-977) | 936, 938-939 | 956, 958-959 | P1, R1 | docstring only |
| `feature_engineering.py` | `run` | 52-53, 55, 57, 59 | same | P2 | `age_group` chain of `income_medians` (52 is a comment) |
| `feature_engineering.py` | `run` | 77-78, 80, 82, 84 | same | P2 | `age_group` chain of `credit_cleaned` (77 is a comment) |
| `feature_engineering.py` | `run` | 139-140, 142, 144 | same | P4 | `credit_util_category` (139 is a comment) |
| `feature_engineering.py` | `run` | 148, 150, 152 | same | P4 | `debt_category` |
| `feature_engineering.py` | `run` | 162, 164, 166, 168 | same | P4 | `age_category` |
| `feature_engineering.py` | `run` | 179, 181 | same | P4 | `flag_low_income`, `flag_few_credit_lines` |
| `predict.py` | `run` | 46, 51, 53, 55, 57 | same | P3 | `age_group` chain of `test_income_medians` (46 is a comment) |
| `predict.py` | `run` | 80, 82, 84, 86 | same | P3 | `age_group` chain of `test_cleaned` |
| `predict.py` | `run` | 134-135, 137, 139 | same | P5 | `credit_util_category` (134 is a comment) |
| `predict.py` | `run` | 143, 145, 147 | same | P5 | `debt_category` |
| `predict.py` | `run` | 158, 160, 162, 164 | same | P5 | `age_category` |
| `predict.py` | `run` | 178 | same | P5 | `flag_few_credit_lines` |
| `train.py` | `run` | 436 | 436-446 | P6 | `PERCENT` of `confusion_matrix_train` |
| `train.py` | `run` | 503 | 513-523 | P6 | `PERCENT` of `confusion_matrix` |
| `metrics_calculation.py` | `run` | 231 | 231 | P7 | `cum_defaults` |

Lines that moved without changing:

| File | Old lines | New lines |
|---|---|---|
| `sas_compat.py` | 253-832 | 259-838 (+6) |
| `sas_compat.py` | 834-850 | 843-859 (+9) |
| `sas_compat.py` | 853 | 873 (+20) |
| `sas_compat.py` | 858-1127 | 878-1147 (+20) |
| `train.py` | 437-502 | 447-512 (+10) |
| `train.py` | 504-781 | 524-801 (+20) |

`feature_engineering.py`, `predict.py` and `metrics_calculation.py` keep every line number.

## Kind `port-differs-from-sas`

### P1. ROC tie rule: fixed, commit `b2e2a49`

`sas_compat._pairs` now groups the probabilities the way SAS does: rows with a missing response
or probability are dropped, the rest are taken from the largest down, a value joins the current
group while `top - value <= _TIE_EPS`, otherwise it opens a new group and becomes its top. A pair
is concordant, discordant or tied by the groups of its two members. `roc_association` and
`association_table` both use it. `Area` keeps its expression `(conc + 0.5 * tied) / (n1 * n0)`.

**What I ran on SAS.** The SAS rulebook leaves two points of R25 open (the boundary at exactly
ROCEPS, the operation order of the Area formula) and one of R28 (the tie tolerance of the
Association table). Two programs, submitted unmodified to SAS OnDemand (SAS 9.04.01M9) with the
`oda_eu` profile that `judge/run_sas.py` uses; every probability is given to SAS as the hex of a
binary64 value:

- `migration/experiments/x07_roc_ties.sas` (generator `x07_make.py`, log `x07_roc_ties.log`,
  analysis `x07_check.py`, check of the port `x07_port_check.py`):
  - part A, 92 small tables through `roc pred=`: pairs exactly ROCEPS apart and one ulp either
    side, pairs around ROCEPS at seven magnitudes, chains, and the two witnesses of the finding;
  - part B, 70 random tables with exact ties, for the operation order of `Area`;
  - part C, four fitted models whose predicted probabilities have near ties, for the Association
    table.
- `migration/experiments/x08_roceps_boundary.sas` (generator `x08_make.py`, log
  `x08_roceps_boundary.log`): 159 pairs whose distance is the double sqrt(2^-53) plus a whole
  number of ulps, at ten magnitudes from 0 to 0.86.

**What SAS does.**

- The finding's witnesses hold. Probabilities 0.5 and 0.5000000102: `Area` 0.5 in SAS. The
  train-stage witness (0.5 and 1 / (1 + exp(-4.1e-8))): `Area` 0.5.
- Grouping is from the largest value down, measured from the group's top. With 0.5 (event),
  0.500000009 and 0.500000018 (non-events), SAS gives `Area` 1/3: 0.5 is in a group of its own.
  Grouping from the smallest value gives 5/12 on this table, and so does a pairwise rule; each
  of those two rules misses SAS on at least 10 of the 92 tables of part A.
- **The boundary is inclusive, and the constant is one ulp above the one in the finding.** A
  pair is tied when its distance is at most `0x3E46A09E667F3BCE` (1.0536712127723511e-8), and
  not tied one ulp further. The double sqrt(2^-53) is `0x3E46A09E667F3BCD`
  (1.0536712127723509e-8). The same threshold holds at all ten magnitudes of X08. So R25's
  "ROCEPS = sqrt(2^-53) = 1.0536712127723509e-8" is one ulp low, and a pair at distance
  sqrt(2^-53) + 1 ulp is tied in SAS. I implemented what SAS does:
  `_TIE_EPS = math.nextafter(math.sqrt(2.0**-53), 1.0)`, test `top - v > _TIE_EPS` opens a
  group. The SAS-side Lean (`Sas.rocGroups`) needs the same constant.
- `Area = (nc + 0.5 * nt) / (n1 * n0)` in that operation order: bit-exact on all 162 tables of
  X07. Five other orders I tried each fail on 10 to 27 of them.
- The Association table of a fitted model uses the same grouping: on the four models of part C
  it gives SAS's concordant, discordant and tied counts exactly. A pairwise rule misses by
  hundreds of pairs, and so does grouping from the smallest value.

**Check of the port after the change.** `Area` is bit-exact against SAS on the 162 tables of X07
and the 159 of X08. On the four fitted models the Association percentages, `Pairs`, Gamma, Tau-a
and `c` are bit-exact. On `judge/reference/risk_scores_train.csv` the port now counts SAS's 280
tied pairs (275 before).

**Effect on judged files.** `printed_association.csv`, `Percent Tied`: 0.000041210 before,
0.000041647 now (283 and 286 pairs on the port's own probabilities; SAS has 280 on its own).
The judge's tolerance on that cell covers both. No other file changes; `model_summary.csv` is
byte-identical.

**How far the change reaches.** `_pairs` returns the pair counts and the two vectors the
standard error is built from, so every column of both tables now follows the grouping. The SAS
runs support that for `Area`, Gamma, Tau-a and the Association table. They do not support it for
three other things, which I left as they were because no finding covers them:

- `StdErr` (and the confidence limits built from it) when probabilities are tied through ROCEPS
  without being equal: the port matches SAS on 47 of the 90 such tables of X07, up to 25 % off on
  the rest. With exact ties only, it matches to the last bit or two on all 70. Before the change
  the port matched 34 of the 90. SAS's rule for this case is not known.
- `LowerArea` and `UpperArea`: SAS clips them to [0, 1]; the port does not.
- `SomersD` of the ROC table: SAS gives `2 * Area - 1` (bit-exact on 160 of 162 tables); the
  port computes `(nc - nd) / (n1 * n0)`, which differs in the last bit on 68.
- On a two-row table SAS prints `StdErr` 6.1e-78 and limits equal to `Area`; the port returns
  missing.

None of these shows in a judged file.

Functions and lines: `_TIE_EPS` 833 → 839-842; `_pairs` 851-852 → 860-872 and 854-857 → 874-877;
docstrings `roc_association` 878 → 898, `association_table` 936 → 956.

### P2. Age group of a missing age, feature engineering: fixed, commit `599606f`

Both `age_group` chains of `feature_engineering.run` use `sas_compat.lt(pl.col("age"), k)` in
every branch, so a missing age gives 1. Lines 53, 55, 57, 59 (`income_medians`) and 78, 80, 82,
84 (`credit_cleaned`); comments on 52 and 77. Line numbers unchanged.

### P3. Age group of a missing age, predict: fixed, commit `751c6d9`

The same in `predict.run`: lines 51, 53, 55, 57 (`test_income_medians`) and 80, 82, 84, 86
(`test_cleaned`); comment on 46. Line numbers unchanged.

### P4. Missing values in step 05, feature engineering: fixed, commit `eb33d7f`

`feature_engineering.run`: `credit_util_category` (140, 142, 144), `debt_category` (148, 150,
152) and `age_category` (162, 164, 166, 168) use `sas_compat.lt`; `flag_low_income` (179) uses
`sas_compat.lt`; `flag_few_credit_lines` (181) uses `sas_compat.le`. `total_risk_flags` follows
through `flag_low_income`, with no line of its own changed. Comment on 139. Line numbers
unchanged. The `>` and `>=` flags are untouched.

As the finding warns, this step now sets `flag_low_income` for a missing income, as SAS does
(N3).

### P5. Missing values in step 05, predict: fixed, commit `c00bd76`

`predict.run`: `credit_util_category` (135, 137, 139), `debt_category` (143, 145, 147),
`age_category` (158, 160, 162, 164) use `sas_compat.lt`; `flag_few_credit_lines` (178) uses
`sas_compat.le`. Comment on 134. Line numbers unchanged.

### P6. PROC FREQ percent with a missing `default_flag`: fixed, commit `3778ebc`

In `train.run`, the `PERCENT` of `confusion_matrix_train` and of `confusion_matrix` is now
`100 * COUNT / N` with N the sum of `COUNT` over the rows where `default_flag` and
`pred_logistic` are both present, and it is missing on a row where either is missing. Old line
436 → new 436-446; old line 503 → new 513-523.

Checked against the SAS-side experiment X13 (a table with missing levels in both variables):
same rows, same order, same `PERCENT` values, missing where SAS has missing.

### P7. Running sum over a missing value: fixed, commit `5f7415c`

`metrics_calculation.run`, line 231: `cum_defaults` is `pl.col("defaults").cum_sum().forward_fill()`.
The running total keeps its last value across a missing `defaults` and is missing only until
the first present value. `cum_capture_rate` and `cum_lift` follow. `cum_count` is unchanged
(`total_count` is a row count and cannot be missing). Line number unchanged.

### P8. Rounding helper: fixed, commit `32c4326`

`sas_round` and `sas_round_scalar` follow R23: with `a = |x|` and `eps = min(1e-6, a * 1e-12)`,
the result is `floor((a + 0.5) + eps)` with the sign of `x`; an integer is returned unchanged;
missing stays missing. Lines 178 (constant), 183-185 and 189-191 (`sas_round`), 196 and 199-201
(`sas_round_scalar`). Line numbers unchanged.

Checked against the SAS-side experiment X11: both forms reproduce its nine half-way thresholds
to the bit (the smallest double that rounds up, and the double just below it). The three
witnesses now give 500000000000, 0 and 2000000. On 600..850 the old and new rules agree on
401,501 values, including every half-way point and its neighbours.

One thing I noticed and did not change: for x in (-0.5, 0] the expression form returns -0.0,
before and after this change (the scalar form returns 0.0). The pipeline never rounds such a
value.

### P9. One-to-one merge with a shared variable: fixed, commit `e7e4f2b`

`merge_one_to_one`: a later frame overwrites a same-named column only on the rows it has; on the
rows after its end the earlier value is kept. Old line 252 → new 252-258; docstring 243-244.

Checked against the SAS-side experiment X15A (`merge a b` and `merge b a` with a shared `x`):
same rows. The two witnesses give `v` = 0 and `v` = 9, 2. No call site shares a variable, so no
output changes.

### End-to-end check of P2 to P7

Besides the parity contract I ran the four stages, before and after, on inputs with missing
values (400-row raw files with one blank `age`, utilization, debt ratio and credit-line count
and an age group without incomes; the reference features with five blank `default_flag`; the
reference validation scores with one whole decile of blank `default_flag`). The outputs changed
only in the cells the findings name, to the SAS values: `age_group` 5 → 1, the three categories
4, 4, 5 → 1, `flag_few_credit_lines` 0 → 1, `flag_low_income` 0 → 1 on a missing income, a
missing `PERCENT` on the missing-level row with the other rows divided by the present rows only,
and `cum_defaults` carried over the missing decile.

## Kind `fix-defect`

### D1. With `fix_psi_bins` on, PSI can be exactly 0 while the shares differ: code not changed

The defect: both shares are raised to 1e-4 inside the logarithms, so a bin whose two shares are
both at or below 1e-4 contributes 0 even when they differ.

On the finding's input (training shares 0.00005, 0.9999, 0.00005 in bins 0, 5, 9; validation
shares 0, 0.9999, 0.0001) PSI is 0 today. Three ways to fix it:

1. **Make the floor smaller than any non-zero share**:
   `eps = min(1e-4, 0.5 / n_train, 0.5 / n_valid)`. Only a share of exactly 0 is then raised, so
   every term is 0 exactly when the two shares are equal, and positive otherwise. On the
   finding's input eps is 2.5e-5, the terms are 3.47e-5, 0 and 3.47e-5, and PSI is 6.93e-5
   ("No significant change", but not 0). A run whose two tables have at most 5,000 rows keeps
   eps = 1e-4 and does not move. A larger run moves only in a bin where one share is 0 or below
   1e-4. This is the one I would pick: it is the smallest change and it restores "PSI is 0 only
   if the shares are equal".
2. **Smooth the counts instead of flooring the shares**: share = (count + 0.5) / (n + 0.5 k)
   with k the number of training bins, on both sides. No share is 0, so no floor is needed. On
   the finding's input PSI is 6.21e-5. It changes every PSI the flag produces, slightly, and two
   tables with different shares can still smooth to the same shares (training counts 4, 1 against
   validation counts 1, 0 both become 0.75, 0.25), so it does not remove the defect, only moves
   it.
3. **Keep the floor and refuse the case**: raise `ValueError` (or write a missing PSI) when a
   non-zero share is below the floor. On the finding's input the run stops with a message
   instead of reporting 0. Nothing else changes, but a large training table with one sparse bin
   then has no PSI at all.

## Kind `record-inaccurate`

### R1: record corrected, commit `f7d9622`

`migration/post-parity/classification.md` row 14, and the docstrings of `roc_association`
(902-903) and `association_table` (958-959): on a single-class input `TauA` is 0, the other
statistics are missing; `TauA` is missing only with at most one usable row. No code change.

### R2: record corrected, commit `35173b8`

`classification.md` row 11 now says the mask also drops a row with a missing `default_flag`.
The rulebook's stepwise row has the same wording; amendment `FV-R2` is queued. No code change.

### R3: record corrected, commit `9946676`

`migration/post-parity/bugfix-4.md`: "only PSI cells change" is now stated for the four judged
inputs only, with the general statement (PSI cells, `PSI_interpretation` and `status` can
change, every other cell is identical) and the finding's example. No code change.

### R4: one statement corrected, commit `ff1ea35`; one not in this repository

- `eq` has a call site. The inventory row already said so; the wrong statements were the
  docstring of `sas_compat.eq` (117, corrected) and the rulebook's "Helper verification (A31)"
  sentence (amendment `FV-R4` queued; it also covers `le`, which has two sites since P4 and P5).
- `intent-properties.md`, T4 ("within 1e-8"), exists only in `sas-migration-formal/sas/migration/`,
  outside this repository and outside what the brief lets me open. It is not corrected. When it
  is, it should state the rule and the constant given under P1, not R25's.
- Also corrected, same subject: `judge/README.md` described SAS's tie rule as "differ by
  ≤ ~1e-8". A dated note now gives the grouping rule and the pair counts (280 in SAS, 286 in the
  port after P1). The judge's tolerance is unchanged.

## Kind `shared-intent-failure`: code not changed

N1 and N2 already have flags (`--fix-psi-bins`, `--fix-train-medians`). The others have none.
Each is a candidate for a new off-by-default flag; whether to add it is a business decision.

| Finding | Candidate flag would | Reached by judged data |
|---|---|---|
| N3 | not set `flag_low_income` (nor count it in `total_risk_flags`) for a missing income. Since P4 this applies to both copies of the step | `edge_predict` only |
| N4 | leave a capped ratio missing when the ratio is missing, instead of the cap | no |
| N5 | impute from another source (overall median, or the training medians of N2) when an age group has no income | `edge_predict` only |
| N6 | grade by the model card's probability bands instead of the score thresholds | yes: 11,510 training and 5,047 validation rows |
| N7 | leave `pred_logistic` (and the grade) missing when the probability is missing | `edge_predict` only |
| N8 | keep one row in `ks_statistic` when several rows attain the maximum | no |
| N9 | carry `default_flag` in the predict copy of step 04 | every run (the column is empty in the test file) |

## For the specification's author

Found while doing the above; not acted on.

- R25's constant: SAS's ROCEPS is `0x3E46A09E667F3BCE`, not the double sqrt(2^-53). The two open
  points of R25 and the one of R28 are settled by X07 and X08 as described under P1.
- The ROC table's `StdErr` under near ties, the clipping of the confidence limits, and
  `SomersD = 2 * Area - 1` are three places where SAS and the port differ and no contract
  exists (P1, "How far the change reaches").
- PROC FREQ `PERCENT`: on one cell of the SAS-side experiment X13 (6 of 7) SAS has
  `0x40556DB6DB6DB6DC` and `100 * COUNT / N` gives `...DB`, one ulp less. `COUNT / N * 100`
  gives the same as the port; neither order explains SAS's value. The port's expression is
  unchanged.

## Parity contract

`migration/parity/run_contract.sh <outdir>` at the head of the branch, all flags off:

```
1    fe       2/2 files pass (port mode)  PASS
2    train    18/18 files pass (port mode)  PASS
3    metrics  9/9 files pass (port mode)  PASS
6    metrics  9/9 files pass (port mode)  PASS
7    metrics  9/9 files pass (port mode)  PASS
8    metrics  9/9 files pass (port mode)  PASS
4    predict  2/2 files pass (port mode)  PASS
5    predict  2/2 files pass (port mode)  PASS
9    fe       2/2 files pass (port mode)  PASS
9    predict  2/2 files pass (port mode)  PASS
```

The run before the first change printed the same ten lines.
