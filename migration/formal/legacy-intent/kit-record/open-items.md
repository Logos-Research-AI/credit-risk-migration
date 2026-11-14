# Open parameters and UNKNOWN rows

Each row is a place where the Lean does not decide a SAS behaviour, and the question that would
close it. "Parameter" means the behaviour is an explicit argument of the unit; "marker" means the
Lean makes a stated choice and carries `OPEN(port):`; "precondition" means the case is excluded.

## Parameters

| # | Parameter | Units | Why it is not a definition | Question that closes it |
|---|---|---|---|---|
| P1 | `arrange : Table → Table` (a permutation) | credit_imputed, test_imputed | PROC SQL returns a join without ORDER BY in an order nothing in the code fixes. In the reference run rows are ordered by age_group and scrambled inside it (X13 shows the same on 40 rows) | Is the join order a deterministic function of the inputs on a given SAS release (for instance the order of an unstable sort on the key)? If the port is judged on the reference split, this stays a parameter by design |
| P2 | `agg : Sas.SqlAgg α` (`sum`, `mean` of a list of present values) | decile_analysis, total_defaults, psi_summary, calibration_plot | X13: PROC SQL's SUM is not a left fold in input order and MEAN is not SUM / COUNT. On the staged run m2, a left fold agrees with SAS to the bit on 167 of 187 aggregate cells and within 1e-9 on all | Which accumulation does PROC SQL use (order after its internal grouping sort; extended precision or a compensated sum; how MEAN is formed)? |
| P3 | `best8 : α → α` | total_defaults (feeds cumulative_lift) | `INTO :m` stores the BEST8. text of the number; a generic number type cannot express "print to 8 characters and read back" | None about SAS (X03 settles it). An executable BEST8. for binary64 would turn the parameter into a definition at `α = Float` only |
| P4 | `model : Sas.Model α` | logit_scored_train_output, logit_scored_valid_temp, test_scored_temp | The fit is out of scope for this pass | Later pass |
| P5 | `invLink : α → α` | logit_scored_train_output | X15C: none of `1/(1+exp(-x))`, `exp(x)/(1+exp(x))`, `1-1/(1+exp(x))` gives PROC LOGISTIC's predicted probability to the bit on more than half of 2,998 rows (all agree within 1 ulp on about 93%) | Which expression does PROC LOGISTIC's OUTPUT PREDICTED= evaluate? |
| P6 | imported tables; `credit_split` | first unit of each script; credit_train_validation | PROC IMPORT and PROC SURVEYSELECT are out of scope | Later pass |
| P7 | `today : Sas.Num α` | model_summary, model_performance_metrics | Clock | None |

## Markers (`OPEN(port):` in the Lean)

| # | Unit | Choice made | Evidence for it | Question that closes it |
|---|---|---|---|---|
| O1 | roc_train (R25; used by roc_valid, roc_stats, logistic_association) | CLOSED on binary64 by X08. A probability joins the group exactly when `top - p <= 3184525836262887 * 2^-78`; a gap of exactly sqrt(2^-53) to nearest joins, and so does the next binary64 above it | X08 (159 cases), X07 `roc` lines (162 cases) | Remaining, not observable with binary64 inputs: whether SAS tests `<=` against `3E46A09E667F3BCE` or `<` against `3E46A09E667F3BCF`. The Lean writes the first |
| O2 | roc_train (R25) | CLOSED by X07. `Area = (nc + 0.5 * nt) / (n1 * n0)` | bit-exact on 162 of 162 X07 cases; the other orders of operations fail 10 to 40 of them | none |
| O3 | logistic_association | CLOSED by X07 part C, and the Lean changed: Somers' D is `2 * c - 1` | bit-exact on the four X07 fits and on X15C, X15D; `nc / t - nd / t` (the previous choice) fails fits C1 and C4 | none |
| O4 | logistic_association | CLOSED by X07 part C. Ties are decided by the ROC grouping (R25) | SAS's concordant, discordant and tied counts reproduced on four fits with 36 to 40 near-tied gaps each; five other tie rules refuted | The fits have no gap between sqrt(2^-53) to nearest and ROCEPS, so the bound itself is taken from R25 (X08), not observed on this table |
| O5 | logistic_lackfit | A probability at exactly 1e-6 from the first of its block joins the block | none either way | Boundary test |
| O6 | logistic_lackfit | Expected counts, chi-square and p-value are not given | X15C: the printed expected counts are not left-to-right sums of the probabilities | Accumulation used for the expected counts |
| O7 | logit_scored_train_output (R26) | Terms are added in the order of the parameter table of the fitted model | X15C is not a stepwise fit | Order of accumulation after stepwise selection (table order or entry order); the reference chain passes with table order to printed precision, which cannot separate the two |
| O8 | logit_scored_train_output | `_LEVEL_` is numeric and placed before pd_logistic | existence only (reference log) | Type and position of `_LEVEL_` (never exported, never read) |
| O9 | ks_statistic | Rows of the remerged result are in input order | X13 `remerge` lines; SAS does not guarantee it | Only matters when the KS maximum is attained on several rows |
| O10 | psi_calculation | Rows of the inner join are in ascending key order | X13 `join` lines, staged runs m2, sa, sb, sc; SAS does not guarantee it | Only affects the order of the printed PSI table |
| O11 | income_medians (R15) | Even-count median is `lo + (hi - lo) / 2` | one discriminating pair (X14) | A second pair, to rule out a coincidence; incomes are integers, where every candidate agrees |

## Excluded by precondition (not modelled)

| # | Unit | Excluded case | Question |
|---|---|---|---|
| U1 | credit_raw_clean, test_raw_clean (R9) | Exponent notation, text longer than 32 characters, and a numeric (not text) MonthlyIncome / NumberOfDependents column | What `INPUT(numeric, BEST32.)` returns (numeric-to-character conversion under BEST12., then read back) |
| U2 | logit_scored_train_output | A missing value in a MODEL candidate that was not selected | Does PROC LOGISTIC leave PREDICTED= missing for it? (D13 suggests yes; no experiment with selection) |
| U3 | total_good_bad (R19) | 10^8 rows or more (BEST8. then prints `1.2346E8`) | none |
| U4 | roc_train, roc_valid, roc_stats, logistic_association, logistic_lackfit | No event or no non-event; a response other than 0 / 1 | SAS produces no table |
| U5 | every unit (A7) | NaN or infinite cells | cannot occur in a SAS data set |

| U6 | confusion_matrix_train, confusion_matrix, confusion_metrics (R20) | An empty input table, or one where every default_flag is missing (the Lean returns an empty OUT= table, hence zero metric rows) | Does PROC FREQ create the OUT= data set at all in that case? |
| U7 | confusion_matrix_train, confusion_matrix (R20) | Flag values that differ only beyond BEST12. precision | PROC FREQ groups by formatted value; the Lean by exact value. Flags are 0 / 1 here |
| U8 | decile_analysis | Two input deciles that collide after `+ 1` (for instance 0 and 1e-20) | Does `GROUP BY decile` use the input column or the SELECT alias? X01b cannot tell; PROC RANK groups are integers, where it cannot matter |
| U9 | every unit (A10) | A variable with a different capitalisation, a wrong type, or a pre-existing variable named like one the step creates | Standing assumption of the RULEBOOK; stated as a precondition item for 26 units |

## Review record

Six adversarial reviews (two per script; `migration/reports/review*.md`). Findings that changed
the Lean: tie tolerance of the ROC grouping (A4), Hosmer-Lemeshow block rule (A5), `_LEVEL_`
(A6). Findings that became precondition items or standing assumptions: A7, A8, A10. Findings
left as recorded open points: O1-O11, U1-U9. No review found, inside the stated input domain, an
input on which a unit differs from an observed SAS result.

## Not translated, and why (listed in `migration/out-of-scope.tsv`)

The ROCAssociation columns StdErr, LowerArea, UpperArea, SomersD, Gamma, TauA (never read; printed
only); the CTABLE classification table, RSQUARE and fit statistics (functions of the fit); the
PERCENT column of PROC FREQ is translated (bit-exact) although never read.
