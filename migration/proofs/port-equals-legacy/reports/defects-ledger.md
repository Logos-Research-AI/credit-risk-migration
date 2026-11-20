# Defects ledger of the credit-risk migration (SAS to Python, verified with Logos)

2026-11-20. Written for a public post. Records only: no git commit, no blueprint read or write.
Every entry rests on `git log` / `git show` of `port/` (earlier `credit_risk/`), `legacy/`,
`judge/` and `migration/`, and on the records named under "Sources". Anything not stated in
those is marked **(inferred)**; anything the records do not say is marked **not known**.

## How to read it

- **Class.** `PORT` a defect of the AI-written Python port; `LEGACY` a defect of the SAS program
  found by verifying it against its requirements (or of an AI-written SAS correction); `LEAN` a
  defect of a Lean translation (of the port or of the SAS), caught by evaluation or review;
  `SPEC` a wording or specification error (a contract, link, definition, requirement or record
  that said something false).
- **Where.** `file:line` at the commit *before* the fix, then `before -> fix` commit. Paths
  before 2026-11-14 are `credit_risk/...` (the port before the restructure 16ab0d3), after it
  `port/credit_risk/...`. SAS lines are those cited by the finding.
- **Judge then.** Whether the parity judge (`judge/compare.py`, contract
  `migration/legacy-to-port/parity/run_contract.sh`: real data plus four hand-made scenarios)
  passed at that moment, and whether its inputs reach the defect. The judge never runs the
  port's own split: line 1 gives the port the split read from the SAS reference features
  (`run_contract.sh` lines 8-26).
- **Phases.** (1) 2026-11-05 port written, judge 10/10 (7f4cca7), post-parity review. (2)
  2026-11-12 first Logos equivalence pass (blueprint `b41b22d4`, stale since 2026-11-16).
  (3) 2026-11-14..16 Logos verification of the SAS against the requirements (`3f5df696`),
  SAS corrected, port made to follow. (4) 2026-11-16..17 small and generated inputs run
  through SAS and the port. (5) 2026-11-17..19 equality proof (`5365851c`).

## Counts

| Class | Entries | Fixed in code / Lean | Closed by a ruling or restatement | Open |
|---|---|---|---|---|
| PORT | 52 | 50 | 1 (P51, by ruling G57) | 1 (P52, NaN row id, see note) |
| LEGACY | 22 | 20 | 2 (L21 by G53, L22 by G57) | 0 |
| LEAN | 17 | 17 | 0 | 0 |
| SPEC | 19 | 18 restated or ruled | | 1 (S19, audit points of 2026-11-19 for the owner) |

Of the 52 port entries, the parity judge passed at the moment of discovery on every one for
which the records say; for none of them did the judge's own inputs fail before the defect was
found by other means (where the judge failed, it was on new inputs added for the search, e.g.
generated seeds). Of the 22 legacy entries the port reproduced the SAS behaviour, so the judge
passed on all of them by construction (it compares the port with SAS).

## The ledger

Ordered most striking first within each class; classes in the order PORT, LEGACY, LEAN, SPEC.

### PORT: the AI-written port

| ID | What was wrong | Smallest input | Where (before -> fix) | Found by | Judge then | Fix |
|---|---|---|---|---|---|---|
| P1 | The split was a fixed file (SAS's draw on the 150,000 real rows); on any other valid input the training set is not 7/10 of the rows and can be empty | **(inferred from C-h text)** any valid 4-row training file whose ids are not in `inputs/split_ids.csv`: no training row, train stage raises | `feature_engineering.py:343-350`, 5b3f0d5 -> 4a757fb | Logos: disproof of `thm:T0` (2026-11-19); neg item id not in the records read | Passed; judge cannot see it (it feeds SAS's split) | Use the file only when it names exactly (7n+9)/10 distinct ids of the input, else a seeded draw |
| P2 | ROC tie rule: two probabilities within 1e-8 counted as tied pairwise; SAS groups from the top within ROCEPS (sqrt(2^-53), one ulp up) | flags 0, 1 with pd 0.5 and 0.5000000102: AUC 1 (port) vs 0.5 (SAS) | `credit_risk/sas_compat.py:833-857` (`_pairs`), 143ddf2 -> b2e2a49 | Logos: `thm:train_run_13_roc_S12a`, `thm:roc_association_H12`, `thm:metrics_run_01_roc_auc_S14a_auc` disproved | Passed: reached on real data (280 SAS vs 275 port tied pairs, area off by 2.2e-9), hidden by four-decimal AUC and by a Percent Tied tolerance added to the judge on 2026-11-05 (f6ba921) | SAS's ROCEPS grouping, boundary measured (x07, x08) |
| P3 | A final model with a parameter left out of a singular information matrix crashed train (`ZeroDivisionError` in `(b / se) ** 2`) | X22 designs A, C (weight 0 at the last iteration); no recorded real run | `train.py:374` (cited by C-g draft R4), 88df42d -> a9b1f41 | Logos prover drafting `PyLinks` 6b (C-g draft, R4), then SAS experiment X22 | Passed; not reached | Follow SAS: DF 0, estimate 0, empty Wald cells, no odds ratio (X22) |
| P4 | A step with a linearly dependent column raised `LinAlgError` in the score test, and counted the dependent variable in DF and AIC/SC | X22 design B (a column that is a linear combination of others) | `train.py:229` (`np.linalg.solve`), `sas_compat.py:827-839`, 0919741 -> 3272e9d | SAS experiment X22 B, run while measuring P3; named in C-g draft R5/R10 | Passed (10/10) | `_solve_sas`; dependent variables left out of DF and the global tests, as SAS |
| P5 | A non-integer row id stopped feature engineering (strict Int64 cast of split ids); SAS keeps a double | 4 training rows, VAR1 = 1/2, 1/4, 3/4, 1/5; no test row | `feature_engineering.py:342-347`, 95c54db -> 5784fc8 | Logos: `neg:G1_run_coverage_neg` (rev f6a0bf0d) | Passed; no judged id is fractional | Read ids with `input_best32`, match by value |
| P6 | On a separated step the port stopped ("did not converge") and wrote nothing; SAS warns, keeps the step, goes on. A deliberate choice recorded by the porting agent (classification row 12, "fails loudly") | 5-row file, seed 16 (6 of 11 seeds of 4-30 rows); constructed 60 rows `small_sep60` | `sas_compat.py:674-745`, 378c8e1 -> c1124e1 | Differential runs of SAS and port on small generated inputs (`small-inputs.md`, case c) | Passed on the contract; the same judge failed these generated inputs | Follow SAS's separation rule (owner, 2026-11-16) |
| P7 | A training part with one outcome: port stopped ("fit at step 0 did not converge"); SAS fits no model and runs on | x27 C60/E60 (60 rows, no defaulter in training) | `sas_compat.py:1045-1070`, `train.py:106-110`, b9883c8 -> 65430e4 | SAS experiment x27; made a contract issue by F4's prover (F4 needed a two-outcome condition); owner ordered the port fix 2026-11-18 | Passed; not reached | Return no fit; train writes what SAS writes |
| P8 | After such a training, metrics stopped (`default_flag not found`) on the header-only validation scores; SAS writes five files | as P7 | `metrics_calculation.py:77-116`, 65430e4 -> 70c4d9c | SAS runs x27_C60_metrics, x27_E60_metrics | Passed; not reached | Read as a table with no row; follow SAS step by step |
| P9 | One-row training part: train crashed (`cannot convert float NaN to integer`) computing a classification table of a fit not made (leave-one-out divides by 0) | 1 training row (`emptyval_n1_class0`) | `train.py:455`, cfee417 -> 1a90814 | Review of 65430e4 / 70c4d9c | Passed; not reached | Table not computed when no fit |
| P10 | Score exports kept columns SAS drops (`IP_*`, `XP_*`, `_FROM_`, `_INTO_`, `_LEVEL_`) | one-row feature table with a column `IP_X` | `train.py:725-726` (export), 6856af9 -> b394838 | Logos: `neg:E4_score_neg` (rev de4216b6) | Passed; no real column has such a name | `drop_sas_names` on both score exports |
| P11 | DATA-step KEEPs compared names exactly; SAS names are case-insensitive | test file header `AGE` (run 14_test_header_age_upper) | `predict.py:445-467`, `train.py` keeps, b394838 -> 8b74e6d | Reviewer of the E4 fix ("same class") | Passed; not reached | `keep_sas_names` |
| P12 | The port's fit iterated to the optimum; SAS stops at GCONV 1E-8 with its ridge, so every downstream number differed slightly | generated seeds 2, 8, 26, 27 (35-70 training rows); real data: 814,511 text cells differed from SAS | `sas_compat.py:675-762`, 5a04084 -> 0ca3cdc | Differential runs on generated inputs (`generated-inputs.md`); initially read as "no difference of the port" | Passed on real data within tolerance; failed on seeds 2, 6, 8 on the fit tolerance | SAS's iteration and stop rule, ridge measured (X17) |
| P13 | Ridge floored at 1e-4; SAS goes lower | SAS run `sep_monthly_income_0p5_n2000_s0_sw0`, step 3: estimates 1.9% off | `sas_compat.py:768`, 0ca3cdc -> cf25ff5 | Review of the fit change | Not run on that input | No floor |
| P14 | A separated fit started from the previous step's estimates; SAS starts from intercept-only | `oneclass_n60_two_variables` | `sas_compat.py:749-765`, 0ac2fce -> 428b5c9 | SAS run comparison | Not run on that input | Start from intercept-only estimates |
| P15 | Complete separation declared only when all probabilities reached 0.95; SAS: no observation on the wrong side of 0.5 | SAS ITPRINT runs D11 (x1 removed where SAS keeps it) | `sas_compat.py:755-784`, 414f381 -> 099d6ce | Review of c1124e1 / 428b5c9 | Not run on that input | SAS's test |
| P16 | Separation tested only when the port's own fit failed; SAS tests every fit still iterating at iteration 8 | D6c: x1 stays in SAS (Wald 7.198), removed by the port (2.511) | `sas_compat.py:750-781`, 099d6ce -> 3f7c1d5 | Review of c1124e1 / 428b5c9 | Not run on that input | Follow SAS's iteration on every step |
| P17 | Quasi-complete separation counted the intercept's element of the inverse information; SAS does not | raw inputs `small12_43`, `small90_15` | `sas_compat.py:771-845`, cf25ff5 -> b798fe3 | Review of 2461757 (ITPRINT runs) | Not run on that input | Leave the intercept out |
| P18 | Removal test: Wald chi-squares equal up to rounding were not a tie; port removed another variable | D10: three equal columns, SAS removes x1, port x2 | `sas_compat.py:889`, 3f7c1d5 -> f2791d1 | Review of c1124e1 / 428b5c9 | Not run on that input | 1e-9 relative tie, first in MODEL order (tolerance a port choice) |
| P19 | After a separated step the entry score was over the candidate's part only; SAS uses all parameters | 280 rows of seed 1, outcome age > 59: final model differs | `sas_compat.py:826-910`, fc09a2f -> 232e21d | `separation-rule.md` part 3 | Not run on that input | Full U' I^-1 U |
| P20 | Stepwise selection ran to its 500-step cap (`RuntimeError`) where SAS stops on a model it has had | 13 raw inputs (`recycling-rule.md`) | `sas_compat.py:877-1003`, b798fe3 -> 8fd4e0a | Measurement for the owner's decision of 2026-11-17 | Not run on those inputs | SAS's recycling rule |
| P21 | Singular information matrix: port solved with it and stopped; SAS leaves the parameter out | rare outcome (fewer than 1 in 40.4 events), 40 X19 designs | `sas_compat.py:752-819`, d6a7cb2 -> e6a87f5 | Measurement, `singular-information.md` | Not run on those inputs | Pivot test 1e-9, weights 0 beyond abs(eta) 36.7368 |
| P22 | Global Wald test kept a slope SAS leaves out | seed 6, step 7: SAS 406.4827, port 407.3550 | `sas_compat.py:819`, `train.py:229-240`, 012ab5a -> 524cd28 | Generated seed 6 (`global-wald-rule.md`) | Failed on seed 6 only (one cell); contract passed | Absolute pivot 1.5e-16, DF kept |
| P23 | Classification table divided by 1 - h for leverage within 1e-8 of 1 (infinite, probability 0 or 1); SAS keeps the probability | raw input R3 (`judge/runs/x21_r3_s03`) | `sas_compat.py:1536-1553`, ee51891 -> 88df42d | Logos prover drafting `PyLinks` 6b (C-g draft, R3), then X21, X23 | Passed; not reached | No adjustment where 1 - h <= 1e-8 |
| P24 | Hosmer-Lemeshow limited each probability, not the group average, to [1e-6, 0.999999] | 5 runs with SAS's note (floorB 0.3644 vs 0.3656) | `sas_compat.py:1256-1289`, 8fd4e0a -> a8ab250 | Measurement on 38 SAS runs | Not run on those inputs | Limit the group average |
| P25 | Hosmer-Lemeshow tables written with fewer than 3 groups; SAS writes none | `rawfit_Dd`, `Dn2`, `Dn6`, `small60_16` | `sas_compat.py:1265,1331`, `train.py:401-411`, a8ab250 -> e2b39ee | Measurement on SAS runs | Not run on those inputs | No table below 3 groups |
| P26 | Validation set of one class: port wrote a `model_summary.csv` row and a `printed_roc_validation.csv`; SAS writes a header only and no ROC file | any 4-row file with both outcomes in training (seed 15) | `train.py:690-803`, 428b5c9 -> c336d8e | Small inputs vs SAS (`small-inputs.md`, case a) | Passed on contract; failed on the small inputs | Follow SAS |
| P27 | Classification table of an intercept-only fit: not the exact leave-one-out mean, levels not SAS's | seed 15 (4 rows) | `sas_compat.py:1208-1269`, 75a75d8 -> 414f381, ee20d83 -> d4f25d2 | Small inputs (case b), then X16 | As P26 | Exact (events - y)/(n - 1), SAS's level values |
| P28 | At level 1.000 the port counted predicted events on fits with a variable; SAS counts none | separated fits `sep_age_gt_55`, `sep_age_gt_62` | `sas_compat.py:1265-1295`, 232e21d -> 3e29b3f | Separation runs | Not run on those inputs | Last level 1 + 1e-12 on every fit |
| P29 | Intercept-only final model: six printed tables SAS does not make were written | seed 29 (60 rows) | `train.py:243-358`, c336d8e -> 78adeef | Small inputs (case d) | As P26 | Guard the writes |
| P30 | A step that removes the last variable printed full rows; SAS prints one -2 Log L line | seeds 22, 25 (15, 30 rows) | `train.py:179`, 78adeef -> f3922ac | Small inputs (case e) | As P26 | Step-0 form |
| P31 | One-class validation set: port wrote `printed_roc_metrics.csv` (`Logistic Model,,,,,,,0`); SAS writes none | `fix_Q26_nodefaulter`, `fix_Q23_alldefaulters` | `metrics_calculation.py:90,499`, 01e0f5f -> c850e3a | Recorded SAS runs ev5/ev6 | Not in contract | Not written |
| P32 | Missing age went to age group 5; in SAS a missing value is below every number, group 1 (both copies) | one row with age missing | `credit_risk/feature_engineering.py:52-82`, b2e2a49 -> 599606f; `credit_risk/predict.py:46-82`, 599606f -> 751c6d9 | Logos: S2(b), S3(b), S24(b), S25(b) disproved | Passed (byte-identical after fix); not reached | `sas_compat.lt` |
| P33 | Missing inputs in the feature step: category chains fell to the last category, `flag_low_income` / `flag_few_credit_lines` 0 (SAS: first category, flag 1). The two port copies also disagreed with each other | one row with every input missing: `credit_util_category` 4 vs 1 | `credit_risk/feature_engineering.py:139-162`, 751c6d9 -> eb33d7f; `credit_risk/predict.py:134-158`, eb33d7f -> c00bd76 | Logos: S5(b), S27(b), S31 step 05, I8 disproved | Passed; `edge_predict` reached the predict copy's flag, where the port already agreed | `lt` / `le` helpers |
| P34 | PROC FREQ percent with a missing `default_flag`: port divided by all rows (100); SAS gives missing | one row, flag missing | `credit_risk/train.py:436,503`, c00bd76 -> 3778ebc | Logos: S8(b), S10(b) | Passed; not reached (printed files only) | PERCENT over rows with both levels present |
| P35 | Running sum over a missing value went missing; SAS carries the total | deciles 4, 7 with defaults 1, missing: row 2 missing vs 1 | `credit_risk/metrics_calculation.py:231`, 3778ebc -> 5f7415c | Logos: S18(b) | Passed; not reached | `cum_sum().forward_fill()` |
| P36 | `sas_round` half tolerance 1e-12 * max(1, abs(x)) made large integers gain 1 | 500000000000 -> 500000000001 | `credit_risk/sas_compat.py:183-199`, 5f7415c -> 32c4326 | Logos: `thm:sas_round_H8` (also S11, S29) | Passed; pipeline rounds only 600..850 | SAS's documented ROUND rule (X11) |
| P37 | `merge_one_to_one` overwrote a shared column with missing after a shorter input ended | v = [0] merged with empty v: missing vs 0 | `credit_risk/sas_compat.py:243-252`, 32c4326 -> e7e4f2b | Logos: `thm:merge_one_to_one_H10` | Passed; no call site shares a name | Overwrite only rows the later frame has |
| P38 | PSI with the `--fix-psi-bins` flag: both shares floored at 1e-4, so PSI could be 0 with differing shares | training 20,000 rows (0.1 once, 0.5 x 19,998, 0.9 once), validation 10,000 (0.5 x 9,999, 0.95 once): PSI 0 | `credit_risk/metrics_calculation.py:269-271`, 885cd87 -> 04b4d78 | Logos: `thm:metrics_run_06_psi_I1_on` | Flag off by default; judge did not run it | Floor min(1e-4, 0.5/n_train, 0.5/n_valid) |
| P39 | The same flag sent validation values below the training minimum to bin 0, which training lacks; the inner join dropped them | `edge_metrics_b` with the flag: 1,988 of 3,000 validation rows dropped, PSI 0.7552 vs 0.0560 | `credit_risk/sas_compat.py:595,603`, `metrics_calculation.py:250-271`, 0edbf0e -> 03f099b | Post-parity reviewer (`review.bugfixes.tsv`) | Flag not judged | Lowest training bin open below; keep empty bins |
| P40 | The fit used every row; SAS fits complete cases only. Flagged by the porting agents themselves (TODO #11) | a row missing one MODEL variable **(inferred)** | `credit_risk/train.py:81,126,137,384`, 4dac42b -> eaef530 .. d434e9a | Porting agent's own TODO marker, burndown 2026-11-05 | Passed; no judged input has a missing feature | Complete-case mask |
| P41 | Association and Hosmer-Lemeshow still used every scored row after P40 | a row missing only a non-selected candidate (reviewer) | `credit_risk/train.py:253-341`, be7713e -> 19b6f55 | Post-parity reviewer | Passed; not reached | Complete-case rows |
| P42 | `hosmer_lemeshow` raised `IndexError` on an empty frame (records claimed "missing, not a crash") | empty frame | `credit_risk/sas_compat.py:962`, 19b6f55 -> a265259 | Post-parity reviewer | Not reached | Guard |
| P43 | `_best_e` printed wider than w for negative exponents (introduced by 06674b5) | BEST6. of 1.005e-9 gives `101E-11` | `credit_risk/sas_compat.py:303-321`, 742d4d5 -> be7713e | Post-parity reviewer, differential fuzz | Not reached (BEST6/7 unused) | Recompute digit count from the printed exponent |
| P44 | `income_medians.csv` written on the default path, outside the flag the commit claimed | any run | `credit_risk/feature_engineering.py:61-66`, 03f099b -> 334e62b | Post-parity reviewer | Passed (file not judged) | Behind `--export-train-medians` (later the corrected SAS writes it, 922c837) |
| P45 | `input(best32.)` of a numeric income or dependents column treated as identity; SAS goes through BEST12. text | a numeric `MonthlyIncome` column, 2499.9999999999 used as 2500 (x25) | `feature_engineering.py:34-37`, 38f17fd -> f799a80; `predict.py:188-191`, b1aa814 -> 2ca060a | Experiment X09 (finder not recorded) | Not known | BEST12. text first |
| P46 | ROC standard error and limits not as PROC LOGISTIC; a class of one observation gave 0, SAS 6.11E-78 | one observation per class, tied for the area | `sas_compat.py:842-870`, 0f87857 -> 68db49f; `sas_compat.py:859-942`, 6935545 -> 993436c | X10, X10b; review of 68db49f, X12 | Not in contract (printed ROC) | SAS's grouping and SQRTBIG |
| P47 | BEST32. printing rounded to 15 digits; SAS cuts | 2/3 prints 0.66666666666666 | `sas_compat.py:32-365`, 68db49f -> e2dc541; 122e6ef -> 0f7fc64 | X11, X13-X15; review of e2dc541 | Not known; `income_medians.csv` is judged byte for byte from 2b9dbdf | SAS's rule, 1,926 of 1,951 measured values |
| P48 | Two test-file names differing only in case crashed predict | header with `age` and `AGE` | `predict.py:100-108`, f5b7601 -> 29511e2 | Port-follows-legacy review (Q27 runs) | Not in contract | SAS's VARn naming, stop with SAS's error |
| P49 | `test_predictions.csv` named the age column `age`; SAS writes the imported name (`AGE`) | test header `AGE` | `predict.py:98-441`, 29511e2 -> b1aa814 | Same | Not in contract | Imported name |
| P50 | Medians file column names read case-sensitively; SAS's join is case-blind | medians header in other case | `predict.py:211`, 2ca060a -> 55eee8c | Same | Not in contract | Case-blind |
| P51 | Training file of 2 or 3 rows with both outcomes: SAS completes train and predict, the port raises and writes nothing | 2-row file, both outcomes (`empty-validation.md`) | `train.py` (split leaves validation empty) | Measurement 2026-11-16 | Not in contract | **Not fixed.** Ruling G57: valid input has at least 4 rows |
| P52 | A NaN row id when the split file does not fit: Python's `set` keeps each NaN as a distinct object, so the draw is not a function of the input; the Lean does not model it | a NaN `row_id` reaching `fe_run_06_split` | `feature_engineering.py:352-370` at 4a757fb | Port translator, update of 2026-11-19 | Not reached | **Open / recorded.** Spec note of 2026-11-20: unreachable on valid input, `lem:py_split_ids_finite` "being proved" |

### LEGACY: the SAS program, found by verifying it against its requirements

The port reproduced every one of these before the SAS was corrected, so the parity judge passed on
all of them. After each SAS correction the port was made to follow (2026-11-16, commits
`98699fd..` of `port/`).

| ID | What was wrong | Smallest input | Where (before -> fix) | Found by | Fix (SAS; port follow-up) |
|---|---|---|---|---|---|
| L1 | Risk grade cut on the score, not the probability: A up to p about 40%, E unreachable | any row with p = 0.20: grade A, required C | `predict.sas` 240-245, `train.sas` 222-227, 255-260; b7b1cd4 -> e1df983 | Logos: `sas_Q18` disproved (also round-1 intent I5 bands, 2026-11-12) | Cut on p; port 48486da, 67562b8 |
| L2 | PSI ranked each set into its own deciles: 0 whatever the shift (also flagged as BUG(port) #4 on 2026-11-05) | training scores 725, 725; validation 800, 800: PSI 0 | `metrics_calculation.sas` 249-288; 607dd5e -> 766937c, 723ddaa | Logos: `sas_Q25`; round-1 I1 off | Training-decile cuts, ten bins, floor, unrounded; port 6712406 |
| L3 | Score rounded | p = 0.25: 788, required 787.5 | `predict.sas` 235-237, `train.sas` 217-219, 251-253; 12a28e4 -> b7b1cd4 | Logos: `sas_Q15` | ROUND removed; port 81820ab, 357c984 |
| L4 | Test incomes imputed from the test file's medians (also BUG(port) #3) | train: age 25, income 5000; test: age 25 income 7000, age 25 missing: 7000, required 5000 | `predict.sas` 58-119; 10f447e -> 2d4fdef | Logos: `sas_Q13`; round-1 I2 off | Export training medians, join them; port c34f68c |
| L5 | No fallback median: an age group with no known income left the income missing | rows (age 25, 5000), (age 45, missing) | `feature_engineering.sas` 58-120; 15b0b2e -> 167dc38 | Logos: `sas_Q1`; round-1 I4 imputation | coalesce with the overall median; port 922c837 |
| L6 | PROC IMPORT guessed `MonthlyIncome` as $5. from 20 rows and cut 6-digit incomes (77 real rows); the exported medians were medians of cut incomes | real row 267: 208333 read as 20833 | `feature_engineering.sas` 46; b5c20eb -> 726048a | BUG(port) #1 by the porting agent (2026-11-05); reviewer of the Q1/Q13 corrections | `guessingrows=max`; port fc07298 |
| L7 | An applicant could be left without a probability (missing income through an income-derived term), then silently declined | test: age 45, income missing; training group 40-49 without income | `predict.sas` 58-222; 2d4fdef -> 12a28e4 | Logos: `sas_Q14`; round-1 N3, N7 | Q1 fallback in predict. A follow-up branch for income <= -1 (7c3aada) was removed when ruling G34 made negative incomes invalid (6d9a855) |
| L8 | `total_risk_flags` summed 5 of the 8 flags | age 40, income 5000, 0 credit lines: 0, required 1 | `feature_engineering.sas` 177-179 (and predict); 167dc38 -> 7b55ef1 | Logos: `sas_Q7` | All eight; port 7fba59f, 5b15d9b |
| L9 | Interaction features: utilization x debt divided by 100; age x log(income + 1) | utilization 1, debt 1, age 25, income 5000: 100 and 25 ln 5001 | `feature_engineering.sas` 191-197 (and predict); 7b55ef1 -> 10f447e | Logos: `sas_Q9` | As required; port 2edf837, d23ee98 |
| L10 | A KS maximum attained twice gave two KS rows; MERGE without BY added a summary row with AUC, Gini, PSI missing | 3 validation rows, equal p, outcomes 1, 0, 1 | `metrics_calculation.sas` 104-111, 330-345; e1df983 -> e8f879f | Logos: `sas_Q23`; round-1 I7 | One row, lowest cutoff; port 2d3d5fd |
| L11 | Published AUC from PROC LOGISTIC, which ties probabilities within about 1.05e-8 | 4-row file, validation p 2.5e-13 (defaulter) and 9.4e-14: AUC 0.5, required 1 | `metrics_calculation.sas` 70-87; 19ff28b -> 3428731 | Logos: `sas_Q23` round 2 | Exact pairwise AUC (G40); port 7aef17c |
| L12 | KS computed between rows of equal probability: overstated | one defaulter, one non-defaulter, same p: KS 1, required 0 | `metrics_calculation.sas` 86-111; e8f879f -> 607dd5e | Logos: `sas_Q24` | At the last row of each p; port 2d3d5fd |
| L13 | Decile table had fewer than ten rows on small or tied validation sets | 4-row file, 2 validation rows | `metrics_calculation.sas` 208-231; 3428731 -> ad9c945 | Logos: `sas_Q26` round 2 | Fixed list 1..10 (G41); port b243236 |
| L14 | No defaulter in validation: capture rate and lift 0/0, written missing | 4 training rows, nobody defaulted | `metrics_calculation.sas` 260-273; f355dfb -> a9acbf5 | Logos: `sas_Q26` round 3 | 0 (G45); port b243236 |
| L15 | No input validation: an invalid file went through | one row with `SeriousDlqin2yrs` = 2 | `feature_engineering.sas` 28-278, `predict.sas` 27-56; 766937c -> 9b8dc37 | Logos: `sas_Q27` | Checks and ABORT; port ffad121, eda078f |
| L16 | The check passed 0.99999999999999 as a whole count (CATS at 12 characters) and read only 32 characters of a long text | a count 0.99999999999999 | both checks; 723ddaa -> 73bfde0 | Reviewer of the Q27 correction **(inferred: commit text only)** | Test the numeric value; reject long text |
| L17 | After a stop, later scripts ran on files an earlier run left in the folder | a faulty training file after a good run | all four scripts; 73bfde0 -> b40a55d | Same **(inferred)** | Remove own outputs first, stop on missing input; port 0f87857, d66019b, eda078f, ffad121 |
| L18 | A text row id passed the check and was scored | test `VAR1` = `A1` | `predict.sas` 93, `feature_engineering.sas` 86; ad9c945 -> a6c0b02 | Logos: `sas_Q27` round 2 (SAS run x21 E agrees) | `missing(%num(VAR1))` (G42) |
| L19 | A header-only test file (valid, G44) stopped predict; two AI-written corrections of it were themselves wrong (a hand-written header parser more lenient than PROC IMPORT; types taken by column position) | header line only; same with columns in another order | `predict.sas` 49-130; a9acbf5 -> 5913e11 -> 56e52f7; d1cbb67 -> 697eed5 | Logos: `sas_Q27` round 3; reviewers of the corrections | PROC IMPORT on the header plus a made-up applicant chosen by name |
| L20 | PSI floor carried through an 8-character text (0.0000714285 stored as 0.000071) | `fix_G43` | `metrics_calculation.sas` psi floor; a6c0b02 -> 3e6dfa6 | Logos review: the Q25 proof rested on a `best8` link the real BEST8. does not meet (`report-round2.md` item 3) | Full precision (G43). Also counted as S15 |
| L21 | Training header `AGE` for `age` was not rejected | one valid row with header `AGE` | `feature_engineering.sas` 52-79 | Logos: `neg:sas_Q27_neg` (round 4), SAS run x24 | **Not fixed**: G53 reduced Q27 to valid input; corrections 0d339b7 reverted by 5096f00 |
| L22 | Training file of 1 to 3 rows: SAS cannot read its own header-only validation file and train fails | 2 rows (`empty-validation.md`) | `train.sas` import | Measurement 2026-11-16 | **Not fixed**: ruling G57 (at least 4 rows) |

### LEAN: defects of the Lean translations

| ID | What was wrong | Smallest input | Item (before -> fix) | Found by | Fix |
|---|---|---|---|---|---|
| T1 | Port Lean `_hl_groups` divided two floats; Python's `n / g` on ints is one correctly rounded division | n = 100000000000000000019, g = 5 (seed 700248) | `def:_hl_groups` -> rev 2864ca0a | Fuzz receipt `diffeval/receipts/fuzz_2026-11-18.tsv` (DIFF-FIXED; 279 of 2,699 targeted seeds wrong under the old quotient) | Exact integer quotient, one rounding |
| T2 | Prelude: `0.0 + col`, `col - (-0.0)` modelled as the column; polars adds (sign of zero) | `sas_round(-0.3)` on a 1-row column | prelude `addCol`/`numBin` | Prelude differential attack, class D2 (A1, A2) | Scalar-zero rule |
| T3 | Prelude: `when(..).then(None)` typed wrong; String branch lost | `when(..).then(1)` with a None branch | prelude `Col.ite` | Prelude attack, D3 (A3) | `Col.null` dtype |
| T4 | Prelude: `np.round(-0.0004, 3)` is -0.0, Lean gave +0.0 | -0.0004 | prelude `Np.rint` | Prelude attack, D10 (A4) | `rint` odd |
| T5 | Port Lean `proc_rank_apply_groups` wrong for k < 0 (group minima not sorted) | k < 0 | `def:proc_rank_apply_groups_precond` | Both B3 reviewers independently | Precondition `0 <= k` |
| T6 | `classification_table`, `hosmer_lemeshow`: sums of y beyond 2^53 inside the precondition (Int64 overflow in Python) | reviewer's reproducers | preconditions | B5 reviewer | Preconditions bound the sums |
| T7 | Step 14 precondition admitted frames on which `write_sas_csv` raises; step 15 admitted all-null ROC labels; magnitudes >= 9.999999999999996e75 in a percent column | `t14p_formats` (Python raises on 27 of 42); fuzz seeds | `def:train_run_14_..._precond`, `def:train_run_15_printed_roc_precond` | Review (port-translator-7) and fuzz after the fourth diff | Clauses added |
| T8 | `def:train_run_08_ctable_precond`: null clauses of train.py :482, :486 unguarded | not recorded | rev 00420db1 (C-m) | Port translator, 2026-11-19 | Guards added |
| T9 | Prelude `Col.append` of two Null columns kept the first length | 1-row Null column merged with a 3-row frame | `merge_one_to_one_precond` | B3 implementer (B5) | Precondition clause (prelude frozen) |
| T10 | SAS Lean ROC used ROCEPS 1e-8; SAS uses sqrt(2^-53) | reference Association table: 280 tied pairs, 1e-8 gives 275 | `def:roc_train` | SAS-side reviewer (A4) | Corrected; dependents re-accepted |
| T11 | SAS Lean Hosmer-Lemeshow block rule a free parameter; SAS: a run within 1e-6 of its first | reference partition | `def:logistic_lackfit` | SAS-side reviewer (A5) | Rewritten |
| T12 | SAS Lean omitted `_LEVEL_` that PROC LOGISTIC OUTPUT writes | reference log | `def:logit_scored_train_output` | SAS-side reviewer (A6) | Edited |
| T13 | SAS Lean check units matched column names by case; SAS ignores case | headers `AGE`, `DEBTRATIO` (x21 B) | `def:credit_raw_input_check`, `def:num_macro` | Reviewer, confirmed by SAS run x21 | `Sas.getCI` |
| T14 | SAS Lean read a character `VAR1` as a number in `test_imputed`; SAS writes it as text | ids `A1`, `A2` (x21 E) | `def:test_imputed` | Reviewer, x21 | Copy the cell |
| T15 | SAS Lean input checks: an absent `VAR1` column; SAS's `%num(VAR1)` creates it as missing (training and test) | file without `VAR1` (x23 G) | `def:credit_raw_input_check`, `def:test_raw_input_check` | Three reviewers, confirmed by x23 | `VAR1 = .` after `bad_row` |
| T16 | SAS Lean `COUNT(DISTINCT)` compared ids with trailing blanks; SAS ignores them (training and test) | ids `7` and `7 ` | `def:credit_raw_check_totals`, `def:test_raw_check_totals` | Reviewers, x23 H | Trim before comparing |
| T17 | SAS Lean returned one `model_summary` row with a missing Area for a one-class ROC table; SAS writes none | x27 A4, B60, D60 | `def:roc_train`, `def:roc_valid`, `def:model_summary` | SAS experiment x27, found by the port's small-input runs (round 6) | Rule R46 |

### SPEC: wording and specification errors

| ID | What was false | Witness | Found by | Resolution |
|---|---|---|---|---|
| S1 | Contract C4 / record: "rows with a missing model variable are excluded"; the mask also drops a missing `default_flag` | 2 rows, candidates 0, flag 0 and missing: mask true, false | Logos: `thm:train_run_01_fit_frame_C4` disproved 2026-11-12 and again 2026-11-17 | Record 35173b8; C4 restated and proved 2026-11-18 |
| S2 | Record: single-class ROC gives all statistics missing; `TauA` is 0 | flags 1, 1, pd 0, 0 | Logos: `thm:roc_association_C2` | f7d9622 |
| S3 | Record (bugfix-4): only PSI cells change with the flag; `status` changes too | validation 4/5, 9/10, training 1/10, 1/5 | Logos: `thm:run_py_F1_frame` | 9946676 |
| S4 | Records: `sas_compat.eq` unused; judge README tie rule "<= ~1e-8" | `metrics_calculation.py:137` | Logos round 1 | ff1ea35 |
| S5 | Contracts of spec v1/v2 false only on inputs no run produces: missing join key (S4, S26), missing `row_id` (S6), missing `pred_logistic` (S10a), `default_flag` 2 in a step frame (S12), empty `sas_best` text (S15, S18a), 10^9 validation rows (F1 on), unsorted deciles (S18b) | each in `report.md`, `report-round2.md`, `findings-for-code.md` | Logos rounds 1-4 | Spec v2.1, v2.2 restated; later B1 |
| S6 | `PyLinks` 5 unsatisfiable as drafted (C-a); `Paired` 2 (C-b); `Paired` 7 lacked `today` (C-c) | not recorded beyond the text | Prover-1 while stating (2026-11-17) | Corrected before stating |
| S7 | Shared existence flags made T0 false (C-d); `today` not a numeric cell made T0 false (C-e); one kind per column (C-f) | T0 witness on paper | Prover-3 writing T0's witness | C-d, C-e, C-f |
| S8 | `PyLinks` 8 conjunct 16 ("a numeric cell stays numeric") false of the real reader on a one-outcome score file (all-empty column read as text) | C60/E60 score files | C-g draft R6, observation H15 | C-g / C-h, C-i |
| S9 | `PyLinks` 5 (C-a) false of the real code: the split file is fixed | any non-real input | Definitions author (C-h) | Weakened, then the port fixed (P1, C-j) |
| S10 | E4's feature shape admitted a table with no column (SAS two rows, port none) and terms naming non-features | rows with no column | E4's prover | Shape narrowed (f88bd93); later B1 |
| S11 | G2, G4 failed on an arbitrary `fsum` and on read-backs that empty the fit frame; F4 needed a two-outcome condition | arbitrary `fsum` | Provers of G2, G4, F4 | Per-contract hypotheses (45e0363, 639a134, 4399051, c4a0cd0), then C-g and the port change P7 removed them |
| S12 | S13 false for `roc_valid_created` false with step 13's one-row table | SAS unit fed a ROC table SAS never has | S13's prover | "Reading 3" restatement |
| S13 | `SasLinks` (1)/(2) admitted a padded text the SAS Lean reads differently from BEST32. | 31 blanks then "55": Lean 55, SAS 5 | Prover-6 | Links tightened on the SAS blueprint (owner, 2026-11-18) |
| S14 | SAS Lean signed off in round 5 said things the real program does not: numeric income through 12-character text, exact hand-offs, exact counts, 1-3 rows, one-outcome fit | 2499.9999999999 used as 2500 (x25) | Port-side planning and fuzzing (round 6) | Rulings G54-G58 |
| S15 | `best8` link false of real BEST8. (relative error about 6e-3) | 0.0000714285 stored as 0.000071 | Logos round-2 review of the Q25 proof | Restated; SAS fixed (L20) |
| S16 | SAS import links D1-D5 (blanks kept, mixed kinds, non-rectangular tables, renamed names, empty column) | faulty tables | Round-4 notes | Out of scope after G53 |
| S17 | Requirements false only for undeliverable tables or needing a reading: Q2-Q5, Q10 (G28); Q6 counts not whole (`> 0` vs `>= 1`, 0.5 late payments) (G29); Q12, Q13 mixed missing encodings (G30, G39); Q22 empty validation (G31); Q27 on invalid input (G53) | Q6: `NumberOfTimes90DaysLate` = 0.5 | Logos: requirement contracts | Rulings |
| S18 | `thm:fe_run_06_split_S6a`, `S6b` false after the split change; G2 needed the final fit's first name to be `Intercept` | not recorded | Provers, 2026-11-19 | C-k: restated for the pipeline's split; `PyLinks` 14 |
| S19 | Audit points left for the owner (2026-11-19): P0's SAS half proves nothing about the SAS run; F1, F2, E7 one-directional; 368 items vs 367 formalised | | Audit | **Open** for the owner |

## One paragraph per entry

### PORT

**P1. The split.** The port never drew its own sample: it read `inputs/split_ids.csv`, which is
SAS's PROC SURVEYSELECT draw on the 150,000 real rows. On the real data that is exactly right; on
any other valid file the ids need not be among the input's, so the training set can be anything
from empty to every row. The porting agents chose this on 2026-11-05 to remove SQL row-order
nondeterminism (classification row 2). The parity judge could not see it, because its line 1
hands the port SAS's split. Logos disproved T0 (the existence of a SAS instance paired with the
port) on 2026-11-19; the owner chose "Fix the port" (4a757fb). The negation item's id and witness
are not in the files read; the smallest input above is inferred from the C-h text. Note for the
post: after the fix the port draws its own seeded 70% sample; that it picks the same rows as
SAS's PROC SURVEYSELECT is an assumption of the claim (`Paired` 2), not a proved fact.

**P2. ROC ties.** The port treated two probabilities within 1e-8 as tied, pairwise; SAS groups
values from the largest down within ROCEPS. This is a real-number difference on valid data, and
the reference data reach it (280 vs 275 tied pairs). The judge passed because the AUC is printed
to four decimals and because, on 2026-11-05, the judge had been given an absolute tolerance on
Association Percent Tied after this very table could not be explained (f6ba921). Found by the
first Logos pass (2026-11-12); fixed with the boundary measured on SAS (b2e2a49).

**P3. Variance 0 crash.** A parameter left out of a singular information matrix has variance
exactly 0, and step 06 divided by it. The Logos prover writing `PyLinks` 6b could not show that a
selection ending by recycling never ends on such a model (C-g draft, R4); experiment X22 showed
what SAS prints, and a9b1f41 follows it. No recorded real run reached it.

**P4. LinAlgError.** With a linearly dependent column, `np.linalg.solve` in the score test raised,
and SAS also leaves such a variable out of DF and AIC/SC. Found in X22 design B while measuring
P3; fixed in 3272e9d. This is what makes trusted-base item B4.2 ("solve and inv raise no error on
what a valid run reaches") true.

**P5. Fractional row ids.** The requirements allow VAR1 = 0.5; SAS keeps it as a double; the port
cast split ids to Int64 and raised. Logos disproof `neg:G1_run_coverage_neg`; fixed 5784fc8.

**P6. Separation.** On a variable that separates the classes the port raised; SAS warns and goes
on. This was a documented decision of the porting agents ("fails loudly", RULEBOOK v1.4), not an
oversight. It came to light when SAS and the port were run on small generated files (6 of 11
seeds of 4 to 30 rows, and a constructed 60-row file); the owner withdrew the decision on
2026-11-16 (c1124e1). P13 to P19 are the further differences found while matching SAS's
separation and iteration rules, each by a reviewer of the previous fix or a SAS measurement.

**P7, P8, P9. One outcome in training.** SAS fits no model and runs on; the port stopped in train
(P7), then in metrics (P8), and on a one-row training part crashed computing a classification
table of a fit it had not made (P9). P7 surfaced as an extra condition F4's prover needed; the
owner chose a port change (2026-11-18) so the contract could drop the condition.

**P10, P11. Column names.** SAS drops `IP_*`, `XP_*`, `_FROM_`, `_INTO_`, `_LEVEL_` from the score
exports and keeps columns case-insensitively; the port did neither. Logos disproof of E4 with a
one-row table holding a column `IP_X` (P10); the reviewer of the fix found the same class in three
KEEPs (P11). No real file has such names.

**P12. The fit stop rule.** The port iterated to the optimum; SAS stops at GCONV 1E-8, with its
own ridge. On the real data this left 814,511 text cells different from SAS, all within the
judge's fit tolerance. On generated seeds 2, 6, 8 the judge failed; the generated-inputs report
first attributed this to SAS stopping early and said no port difference was found. The owner
decided on 2026-11-17 that the port follows SAS's iteration (0ca3cdc). The one unexplained
`printed_classification.csv` count of `parity-after-verification.md` is not separately closed in
the records; 0ca3cdc reports 0 differing cells in every printed table afterwards **(inferred to
be the same cause)**.

**P13 to P19. Separation and iteration details.** Ridge floor (P13), start of a separated fit
(P14), the 0.5 test of complete separation (P15), testing every fit at iteration 8 (P16), the
intercept's element in the quasi-complete test (P17), ties in the removal Wald test (P18; the
1e-9 tolerance is the port's choice, SAS's is not known), and the entry score after a separated
step (P19). Each changed the final model or printed statistics on a recorded SAS run.

**P20. Recycling.** The port had two special cases of SAS's "model already seen" rule; on 13 raw
inputs it went round to its 500-step cap and raised. Fixed 8fd4e0a.

**P21. Singular information.** With a rare outcome a weight becomes exactly 0 and a parameter
rests on it; the port stopped, SAS leaves it out. Fixed e6a87f5.

**P22. Global Wald.** SAS leaves a slope with a tiny pivot out of the global Wald chi-square; on
seed 6 the port printed 407.3550 against SAS's 406.4827. Fixed 524cd28.

**P23. Leverage near 1.** The port divided by 1 - h where SAS keeps the probability. Raised by the
same C-g draft (R3) as an idealisation in the Lean precondition; X21 and X23 measured SAS's rule
(1 - h <= 1e-8 within (9.496e-9, 1.2e-8]). Fixed 88df42d.

**P24, P25. Hosmer-Lemeshow.** Limit applied to observations instead of the group average, and
tables written with fewer than 3 groups. Measured on SAS runs; fixed a8ab250, e2b39ee.

**P26 to P30. Small inputs.** A one-class validation set (P26), the intercept-only
classification table (P27, P28), printed tables SAS does not make (P29), and a step removing the
last variable (P30). All found on 2026-11-16 by running SAS and the port on 4 to 200-row
generated files; none on the contract's inputs.

**P31.** `printed_roc_metrics.csv` written for a one-class validation set. Found against
recorded SAS runs. Printed file, outside the final claim.

**P32 to P37. The first Logos pass (2026-11-12).** Missing values compared with plain polars
operators instead of SAS's "missing is below every number" (P32, P33; the two port copies of the
feature step also disagreed on `flag_low_income`), PROC FREQ percent (P34), running sum over a
missing value (P35), `sas_round` (P36), one-to-one merge (P37). Every fix left all judged files
byte-identical: the judge's inputs never had these values.

**P38, P39. The PSI fix flag.** The AI's optional fix for the inherited PSI bug was itself wrong
twice: a reviewer found validation values dropped into a bin training lacks (P39, 2026-11-05),
and Logos found the 1e-4 floor could make PSI exactly 0 with differing shares (P38, 2026-11-12).
The flag was off by default and never judged; it was removed on 2026-11-16 when the SAS was
corrected (L2).

**P40 to P44. Post-parity review (2026-11-05).** The complete-case mask the porting agents had
left as a TODO (P40), Association and Hosmer-Lemeshow still on all rows (P41), an `IndexError`
on an empty Hosmer-Lemeshow input contradicting its record (P42), a print width regression
introduced by a fix (P43), and an output written outside its flag (P44). Found by reviewers after
the judge passed 10/10.

**P45 to P47. SAS number reading and printing.** `input(best32.)` of a numeric column, ROC
standard errors, BEST32. printing. Measured in experiments X09 to X15 during the port's update of
2026-11-16; the finder of P45 and of the first parts of P46, P47 is not recorded (the later
parts cite "Review of ...").

**P48 to P50. Header case.** Crashes or naming differences on headers in another case. Found by
the reviewers of the Q27 port changes. Such headers fail `TrainOK`/`TestOK` (exact names), so
these inputs are outside the final claim (G53).

**P51. Two or three training rows.** SAS completes, the port raises. Not fixed: ruling G57 made
4 rows a condition of valid input, because SAS itself fails on 1 to 3 rows (L22).

**P52. NaN row id.** Recorded by the port translator on 2026-11-19: not a function of the input
in Python, not modelled in Lean. The 2026-11-19 final report left it for the owner; the spec's
note of 2026-11-20 says it is unreachable on valid input, proved by `lem:py_split_ids_finite`,
"being proved now; not yet recorded as proved". Open in the records.

### LEGACY

**L1. Grades.** The SAS graded on the score with cuts 750/700/650/600/550, so a 40% default
probability was graded A and grade E could not occur. The port reproduced it and the judge
passed. Found by Logos against requirement Q18 (and, earlier, as intent I5 on 2026-11-12).

**L2. PSI.** Each data set ranked into its own deciles: PSI is 0 whatever the shift. Known to the
porting agent as BUG(port) #4 on 2026-11-05 and confirmed by Logos (Q25, I1).

**L3. Score rounding.** The documented bands (812.5, 787.5, 762.5) cannot be hit by an integer
score. Logos, Q15.

**L4. Test medians.** Test incomes imputed from the test file itself (leakage, and empty groups).
Known as BUG(port) #3; Logos Q13.

**L5, L7. Missing income.** No fallback when an age group has no known income; through an
income-derived term the applicant then has no probability and is declined with grade F. Logos Q1,
Q14. The AI's first follow-up for negative incomes (7c3aada) was undone by ruling G34.

**L6. Truncated incomes.** PROC IMPORT guessed a 5-character column from 20 rows and cut 77 real
incomes. Flagged by the porting agent on 2026-11-05 (BUG(port) #1); entered the SAS corrections
as a reviewer's defect.

**L8, L9. Feature formulas.** Five of eight flags summed; both interaction features off the
requirement. Logos Q7, Q9.

**L10 to L12. KS and AUC.** Two KS rows on a tie (and a second summary row with AUC missing);
AUC with near-ties counted as ties; KS evaluated inside ties. Logos Q23, Q24.

**L13, L14. Deciles.** Fewer than ten rows; missing capture rate and lift with no defaulter.
Logos Q26, rulings G41, G45.

**L15 to L19. Input validation and stops.** No check at all (L15), then defects in the AI-written
checks found by reviewers or by Logos: whole-number test through 12-character text (L16), stale
files used after a stop (L17), text ids accepted (L18), header-only test file rejected and two
wrong attempts to accept it (L19).

**L20. PSI floor precision.** The floor went through an 8-character text. Found because a Logos
reviewer noticed the Q25 proof rested on a link the real BEST8. does not meet.

**L21. `AGE` header.** Logos disproved Q27 clause 2 with a valid row under header `AGE`; the
owner reduced Q27 to valid input (G53) instead of changing the SAS.

**L22. 1 to 3 rows.** SAS cannot read its own header-only validation file. Ruled out of valid
input (G57).

### LEAN

**T1.** The only translation defect of a port unit found by fuzzing inside a precondition: the
Lean divided two floats where Python divides two integers exactly. Seed 700248 of the 2026-11-18
fuzz; 279 of 2,699 division-targeted seeds were wrong under the old Lean.

**T2 to T4.** Defects of the shared Lean preludes (signed zero of scalar-zero addition, the dtype of
a None branch, `np.round` of a small negative), found by the differential attack on the preludes
before translation (2026-11-10).

**T5 to T9.** Port-Lean preconditions that admitted inputs on which the Python raises or the Lean
differs, found by the adversarial reviewers and fuzzers of the translation; each closed by a
precondition clause (the unit bodies were faithful).

**T10 to T16.** SAS-Lean units corrected after reviewers' findings, each confirmed by a SAS run
(ROCEPS, Hosmer-Lemeshow blocks, `_LEVEL_`, name case, character ids, absent `VAR1`, trailing
blanks). The SAS-side differential evaluation then found 0 unexplained differences in about
101,000 cells.

**T17.** The SAS Lean gave one `model_summary` row for a one-class ROC table; SAS writes none.
Found because the port's small-input runs (P26) showed SAS's behaviour; corrected as rule R46.

### SPEC

**S1 to S4.** Statements in the migration records that the code contradicted, found by the first
Logos pass. C4 was disproved twice (2026-11-12 and 2026-11-17) before it was restated.

**S5.** Contracts of the early specification that failed only on inputs no run produces; each
disproof was correct and the contract was restated. Under amendment 2 (B1) this is no longer a
narrowing.

**S6 to S12.** Definitions and contract texts of the equality proof that were unsatisfiable,
false of the real code, or too weak to prove, found by provers while stating or proving; S9 led
to the port fix P1, S11 to P7.

**S13 to S16.** SAS-side links and model idealisations that were false of the real SAS, found by
provers, by the port's planning and fuzzing, or by a review of a proof.

**S17.** Requirements that needed a ruling; Q6 is the clearest: the SAS flagged 0.5 late
payments as a serious delinquency, which the requirement as worded forbade; ruling G29 (counts
are whole numbers) made the two say the same.

**S18, S19.** Restatements of 2026-11-19 and the audit points still open for the owner.

## Sources

`git log` and `git show` of `port/`, `credit_risk/`, `legacy/`, `judge/`, `migration/` (head
4a757fb); `migration/legacy-to-port/`: `post-parity/classification.md`, `review.bugfixes.tsv`,
`review.parity-fixes.tsv`, `parity-after-verification.md`, `small-inputs.md`,
`generated-inputs.md`, `empty-validation.md`, `separation-rule.md`, `recycling-rule.md`,
`singular-information.md`, `global-wald-rule.md`, `parity/run_contract.sh`;
`migration/proofs/port-equals-legacy/`: `reports/report.md`, `report-round2.md`,
`findings-for-code.md`, `2026-11-17-equality-round-1.md`, `2026-11-18-final-report.md`,
`2026-11-19-final-report.md`, `rounds/disproof-C4-2026-11-17.md`, `disproof-E4-2026-11-17.md`,
`disproof-G1-2026-11-17.md`, `observation-H15-2026-11-18.md`, `C-g-draft-2026-11-18.md`,
`port-change-spec-2026-11-18.md`, `definitions-v3.md`, `informal-spec.md`;
`migration/port-to-lean/`: `update-2026-11-17.md`, `update-2026-11-18.md`, `gates.md`,
`amendments.md`, `RULEBOOK.md`, `reviews/verdicts.md`, `diffeval/receipts/fuzz_2026-11-18.tsv`;
`migration/legacy-to-lean/`: `corrections-account.md`, `retranslation-report.md`,
`diffeval-receipt.md`, `amendments.md`, `corrections-round7.md`;
`migration/proofs/legacy-meets-requirements/reports/`: `findings-for-legacy.md`,
`findings-for-legacy-round2.md`, `findings-for-legacy-round3.md`, `2026-11-15-round-4.md`,
`2026-11-16-round-5.md`, `round-6-2026-11-16.md`, `corrections-round4.md`, `q27-old-disproof.md`,
`report-round2.md`; `migration/requirements/requirements.md`.

Not read in full: the per-round prover logs of the SAS stage (`team-trial.md`, round-4 notes),
the `update-after-verification.md` plan, and the review files under `port-to-lean/reviews/` beyond
`verdicts.md`. An entry could be missing from those; the ones above are what the read records
and git show.
