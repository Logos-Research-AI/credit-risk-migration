# Defects ledger by finder (2026-11-20)

Classification of the ~~110 entries of `defects-ledger.md` (52 PORT, 22 LEGACY, 17 LEAN, 19 SPEC)~~
112 entries of `defects-ledger.md` (52 PORT, 22 LEGACY, 18 LEAN, 20 SPEC; T18 and S20 added
2026-11-20) by
who or what found each one, for the public post "the AI-native legacy-to-Python port made mistakes
that the Logos verified layer caught". Read-only: built from the ledger, the records it cites and
`git log` / `git show`. No blueprint was opened. Where the records do not settle a field it says
**unclear**.

## Codes

**Finder (one primary per entry).**

| Code | Meaning |
|---|---|
| 1 | Logos proof attempt or disproof. **1d**: a negation proved or the contract disproved with a witness. **1o**: an obligation the prover could not discharge while stating or proving, so the prover traced it to the code (no negation proved) |
| 2 | Logos judge (statement or code judging). **No entry was found this way.** |
| 3 | Differential evaluation or fuzzing of the Lean against Python or SAS on the same inputs |
| 4 | SAS or Python runs, measurement experiments (including port-vs-SAS runs on new generated inputs, and reviewers' own SAS runs) |
| 5 | Human or agent review reading code, records or a proof (including the porting agent's own BUG/TODO markers) |
| 6 | Other (noticed during Lean translation work, not by a proof) |
| U | Unclear: the records do not say what found it |

**Severity.** *silent*: wrong output, no error, on an input that meets section 3 of
`migration/requirements/requirements.md` (valid input), default flags. *crash*: the program stops or
refuses on valid input. *edge*: only on input outside section 3 (for example a missing age: section
3 lets only income and dependents be missing), only with a non-default flag, only on a designed input
whose reach from a valid raw file is not recorded, or on a state no pipeline run reaches. *records*:
printing, an extra file, or a record or model text. *model*: a defect of a Lean model, no program
output involved. *unclear*: the reach on valid input is not recorded.

**Parity.** Would the parity tests (judge `judge/compare.py` under
`migration/legacy-to-port/parity/run_contract.sh`: the real data plus the hand-made edge scenarios)
have caught it? The script hands the port SAS's split read from the SAS reference features (lines
8-15) and runs only the reference inputs, so anything needing other inputs is out of its reach.

## Summary

### Counts, kind x finder

| Kind | 1 Logos proof (1d / 1o) | 2 Logos judge | 3 Diff-eval / fuzz | 4 Runs / measurement | 5 Review | 6 Other | U Unclear | Total |
|---|---|---|---|---|---|---|---|---|
| PORT | 13 (11 / 2) | 0 | 0 | 26 | 11 | 1 | 1 | 52 |
| LEGACY | 15 (15 / 0) | 0 | 0 | 1 | 6 | 0 | 0 | 22 |
| ~~LEAN~~ | ~~0~~ | ~~0~~ | ~~4~~ | ~~1~~ | ~~11~~ | ~~0~~ | ~~1~~ | ~~17~~ |
| LEAN (2026-11-20) | 0 | 0 | 5 | 1 | 11 | 0 | 1 | 18 |
| ~~SPEC~~ | ~~14 (10 / 4)~~ | ~~0~~ | ~~0~~ | ~~1~~ | ~~3~~ | ~~0~~ | ~~1~~ | ~~19~~ |
| SPEC (2026-11-20) | 14 (10 / 4) | 0 | 0 | 1 | 4 | 0 | 1 | 20 |
| ~~**Total**~~ | ~~**42**~~ | ~~**0**~~ | ~~**4**~~ | ~~**29**~~ | ~~**31**~~ | ~~**1**~~ | ~~**3**~~ | ~~**110**~~ |
| **Total (2026-11-20)** | **42** | **0** | **5** | **29** | **32** | **1** | **3** | **112** |

*Updated 2026-11-20: T18 (LEAN, code 3, differential fuzzing) and S20 (SPEC, code 5, non-author
review of the glue) added.*

SPEC 1o are S6, S7, S8, S11 (provers finding a definition or contract unsatisfiable or false while
stating or writing a witness, without a proved negation). S11 also had per-contract hypotheses; it is
counted 1o.

### Counts, PORT by severity and finder

| Severity | 1 Logos | 4 Runs | 5 Review | 6 Other | U | Total |
|---|---|---|---|---|---|---|
| silent | **3** (P1, P2, P23) | 14 | 0 | 0 | 0 | 17 |
| crash | 1 (P5) | 5 | 0 | 0 | 0 | 6 |
| edge | 9 (P3, P10, P32-P38) | 3 | 7 | 1 | 1 | 21 |
| records | 0 | 1 | 2 | 0 | 0 | 3 |
| unclear | 0 | 3 | 2 | 0 | 0 | 5 |
| **Total** | **13** | **26** | **11** | **1** | **1** | **52** |

(Runs, silent: P12-P14, P17, P19, P22, P24-P31. Runs, crash: P6, P7, P8, P20, P21. Runs, edge: P4,
P46, P51. Runs, unclear: P15, P16, P18. Review, edge: P9, P11, P39, P42, P48-P50. Review, unclear:
P40, P41.)

### The headline numbers for the post

- **PORT defects found by Logos: 13 of 52** (11 by a disproof, 2 by an obligation a prover could not
  discharge).
- **Of those, silent wrong output on valid input that the parity tests passed: 3** (P1, P2, P23).
  One more is silent with the non-default `--fix-psi-bins` flag on (P38), one is a crash on valid
  input (P5), and 8 need input outside section 3 or are unreachable from the pipeline (P3, P10,
  P32-P37).
- **The parity tests caught none of the 52 PORT defects** at the moment of discovery (50 "no", 2
  "unknown": P45, P47). Where a judge run failed, it was on new inputs made for the search, not on
  the parity sample.
- **Most PORT defects (26) were found by running SAS and the port on new small or generated
  inputs**, not by Logos. The post should not imply otherwise. Several of those runs were made
  because a Logos round asked for SAS's behaviour (for example X21, X22, x27), but the difference
  itself showed up in the runs.
- **LEGACY: 15 of 22 by a Logos disproof** of a requirement contract on the SAS blueprint. Three of
  the six "review" entries (L2, L4, L6) had been flagged by the porting agent as `BUG(port)` on
  2026-11-05 (`migration/legacy-to-port/post-parity/classification.md` rows 1, 3, 4) before Logos
  confirmed L2 and L4 against the requirements.
- **The Logos judge (code 2) found nothing in the records.** The ledger never names it.

## Showcase candidates

Port defects found by a Logos proof, silent, missed by the parity tests. Four candidates; the first
is the strongest. P5 is a runner-up (Logos disproof on valid input, but a crash, not silent).

### 1. P2: two probabilities 1e-8 apart, counted as a tie (ROC area)

**In plain words.** The AUC counts pairs of one defaulter and one non-defaulter. When the two
predicted probabilities are "equal", SAS counts half a pair. The AI port decided "equal" as "within
1e-8 of each other, pair by pair". SAS groups the probabilities from the top down and uses a
different constant (one ulp above sqrt(2^-53), about 1.0537e-8). The Logos prover disproved the
equality contracts with two rows, flags 0 and 1, probabilities 0.5 and 0.5000000102: the port says
AUC 1, SAS says 0.5.

**Python before the fix** (`credit_risk/sas_compat.py` at 143ddf2, lines 833 and 846-857):

```python
_TIE_EPS = 1e-8  # A8: SAS tie fuzz
...
    lo_ne = np.searchsorted(ne, ev - _TIE_EPS, side="left")
    le_ne = np.searchsorted(ne, ev + _TIE_EPS, side="right")
    ...
    tied = int((le_ne - lo_ne).sum())
```

**Why the parity tests passed.** The real data reaches it. On the reference training scores 280
pairs are tied under SAS's rule and 275 under the port's; the area differs by 2.2e-9, and `Train_AUC`
is printed with four decimals (0.8592 either way). The printed Association table's Percent Tied also
differed. On 2026-11-05 the judge was given a tolerance on that very cell after the difference could
not be explained (f6ba921, "Association Percent Tied is judged with an absolute 1e-5
percentage-point tolerance").

**Evidence.** Disproofs `thm:train_run_13_roc_S12a` and `_S14a_auc`:
`reports/report.md:89`, `:97`, and finding 1 at `:191-196`. Reach on real data:
`reports/report-round2.md:147-153`. Judge tolerance: commit f6ba921. Fix: b2e2a49 (constant measured
on SAS in x07/x08). Record note: b2e2a49's message gives the port's printed Percent Tied as 283 pairs
before the fix and 286 after (SAS 280), while report-round2 gives 275 under the port's rule on the
reference scores; the two counts are of different tables at different estimates and are not
reconciled in the records.

### 2. P1: the port's training sample was a fixed file

**In plain words.** SAS draws a 70% training sample (PROC SURVEYSELECT, seed 42) from whatever file
it is given. The AI port did not draw: it read the list of ids SAS had drawn on the 150,000 real
rows. On the real data that is exactly right, so every parity test passed. On any other valid file
the training set is whichever rows happen to carry one of those 105,000 ids: anything from none
(train then stops) to all of them, and in general not 7 in 10. The Logos prover could not pair the
port with any SAS run on such inputs: contract T0 (a SAS instance paired with the port exists) was
disproved on 2026-11-19, and the owner ordered "Fix the port".

**Python before the fix** (`port/credit_risk/feature_engineering.py` at 5b3f0d5, lines 343-348; the
judge and the CLI pass `--split-ids`, i.e. SAS's draw):

```python
    train_ids = (
        pl.read_csv(split_ids, columns=["row_id"], infer_schema=False)  # R§1 CSV I/O: all text
        .select(sas_compat.input_best32(pl.col("row_id")))
        .get_column("row_id")
    )
    credit_split = credit_features.with_columns(selected=pl.col("row_id").is_in(train_ids.implode()))
```

**Why the parity tests passed.** `run_contract.sh` lines 8-15 write the port's split file from SAS's
reference training features, and the only full-pipeline input is the real data.

**Evidence.** The fixed-file behaviour written into `PyLinks` 5 (C-h): `definitions-v3.md:864-890`.
Disproof and owner's decision: `reports/2026-11-19-final-report.md:275-281`, `:300`. Fix: 4a757fb.

**Caveats for the post.** (a) The negation item's id and witness are not in the files read; the
records call it "the T0 disproof" only. (b) It was a deliberate choice of the porting agents on
2026-11-05, to remove a row-order nondeterminism (`post-parity/classification.md` row 2), not an
oversight; the defect is that the choice made the port wrong on every input but one. (c) The C-h
author found the fixed file by reading the code while making the link true; the disproof is what
made it a defect. (d) After the fix the port draws its own seeded sample (`random.Random(42)`); that
it is SAS's PROC SURVEYSELECT sample is an assumption of the claim (`Paired` 2), not a proved fact.

### 3. P23: leverage near 1 in the classification table

**In plain words.** The printed classification table uses each applicant's leave-one-out
probability, computed as one step `p - (y - p) h / (1 - h)`. When one row alone carries a direction
of the model, its leverage h is 1 (or 1 up to rounding). The port divided by `1 - h` as it came: an
infinite step, a probability of exactly 0 or 1, the opposite of the observed outcome. SAS makes no
adjustment there. A Logos prover, writing the link clauses for contract G2, could not show that a
final model never has such a row and traced it to this line (C-g draft, R3). Experiment X21 then
measured SAS's rule.

**Python before the fix** (`port/credit_risk/sas_compat.py` at ee51891, lines 1549-1553):

```python
    w = p * (1.0 - p)
    v = np.linalg.inv(x.T @ (x * w[:, None]))
    q = np.einsum("ij,jk,ik->i", x, v, x)
    h = w * q
    ps = _expit(eta - (y - p) * q / (1.0 - h))
```

**Why the parity tests passed.** The reference data has no such row.

**Evidence.** `rounds/C-g-draft-2026-11-18.md:820-828` (R3); X21 results in the docstring of
`migration/legacy-to-port/experiments/x21_leverage_one.py` (commit bf8eb49): on the valid raw input
R3 (generated seed 3, four training defaulters) row 276 has leverage 1 within 1e-13; the port's
classification table differs from SAS's on 10 of 18 designed fits. Fix: 88df42d.

**Caveats for the post.** (a) Found by an undischarged obligation (1o), not a proved negation.
(b) On R3 the port happened to match SAS because its `1 - h` came out -3.2e-14; with the same
probabilities summed in another order it is +5.4e-15 and 49 of the 51 rows of
`printed_classification.csv` differ. The 10 of 18 are fits without selection. (c) The file is a
printed PROC LOGISTIC table, not a score or a grade.

### 4. P38: the AI's own PSI fix could still report "no shift"

**In plain words.** The SAS program's PSI was always 0 (L2). The AI port offered an optional fix
(`--fix-psi-bins`). In it, both shares of a bin were floored at 1e-4 before the logarithm, so bins
whose shares differ but are both at or below 1e-4 cancel, and PSI can be exactly 0 while the two
distributions differ. Logos first flagged it by evaluation (round 1) and then disproved the intent
contract formally (round 2) with 20,000 training and 10,000 validation rows.

**Python before the fix** (`credit_risk/metrics_calculation.py` at 885cd87, lines 266-271):

```python
    if fix_psi_bins:
        # ... enters the log term with both shares
        # floored at PSI_EPS = 1e-4 (ln(train/0) is undefined), so the shift is not silently dropped
        eps = 1e-4
```

**Why the parity tests passed.** The flag was off by default and never judged.

**Evidence.** `reports/report.md:172` (round 1, false by Float evaluation),
`reports/report-round2.md:141` (`thm:metrics_run_06_psi_I1_on` disproved with the witness). Fix:
04b4d78. **Caveat:** it is silent only with a non-default flag (classed *edge* above), and it is a
defect of the AI's added fix, not of its translation of SAS.

### Runner-up: P5, a fractional row id stopped the port

`neg:G1_run_coverage_neg` (revision f6a0bf0d): four valid training rows with VAR1 = 1/2, 1/4, 3/4,
1/5; the port's strict Int64 cast of the split ids raised where SAS splits. Crash, not silent.
Evidence: `rounds/disproof-G1-2026-11-17.md:7-28`; fix 5784fc8.

## Per-entry table

"Judge" = would the parity tests have caught it. Evidence paths are relative to
`migration/proofs/port-equals-legacy/` unless they start with `migration/`, `port/` or a commit.

### PORT

| ID | Kind | Finder | How, exactly | Judge | Severity | Evidence |
|---|---|---|---|---|---|---|
| P1 | PORT | 1d | T0 disproved 2026-11-19 after C-h wrote the fixed split file into `PyLinks` 5; neg item id not in the records | no: judge hands the port SAS's split, real data only | silent (crash when no id matches) | `definitions-v3.md:864-890`; `reports/2026-11-19-final-report.md:275,300`; 4a757fb |
| P2 | PORT | 1d | S12, S14(a) auc, H12 disproved, first Logos pass 2026-11-12 | no: reached, hidden by 4-decimal AUC and the Percent Tied tolerance (f6ba921) | silent | `reports/report.md:89,97,191-196`; `reports/report-round2.md:147-153`; b2e2a49 |
| P3 | PORT | 1o | Prover drafting `PyLinks` 6b could not show a final model has no variance-0 parameter (C-g R4); X22 confirmed | no: not reached | edge (crash; no recorded run reaches it, X22 forces the final model) | `rounds/C-g-draft-2026-11-18.md:830-839`; a9b1f41 |
| P4 | PORT | 4 | Experiment X22 design B, run while measuring P3 | no: not reached | edge (crash on a designed singular X'X; reach from a valid raw file not recorded) | c61e586, 3272e9d |
| P5 | PORT | 1d | `neg:G1_run_coverage_neg` (rev f6a0bf0d) | no: no judged id is fractional | crash | `rounds/disproof-G1-2026-11-17.md:7-28`; 5784fc8 |
| P6 | PORT | 4 | Port and SAS on small generated files, case (c) | no: contract passed | crash (6 of 11 seeds of 4-30 rows); a deliberate porting choice | `migration/legacy-to-port/small-inputs.md:17-22`; c1124e1 |
| P7 | PORT | 4 | One-class runs of 2026-11-16, case (f); made a defect when F4's prover needed a two-outcome condition (1o, secondary) | no: not reached | crash | `migration/legacy-to-port/small-inputs.md:300-340`; `reports/2026-11-18-final-report.md:241-245,356`; 65430e4 |
| P8 | PORT | 4 | SAS and port runs x27 C60/E60 metrics after the P7 fix | no | crash | 70c4d9c |
| P9 | PORT | 5 | Review of 65430e4 / 70c4d9c, confirmed on runs `emptyval_n1_*` | no | edge (1-row training part needs a file below G57's 4 rows) | 1a90814 |
| P10 | PORT | 1d | `neg:E4_score_neg` (rev de4216b6): a feature column `IP_X` | no: no real column has such a name | edge (no valid raw input produces such a column) | `rounds/disproof-E4-2026-11-17.md:7-34`; b394838 |
| P11 | PORT | 5 | Reviewer of the E4 fix ("same class") | no | edge (header `AGE` is outside the exact names) | 8b74e6d |
| P12 | PORT | 4 | Port vs SAS on generated seeds 2, 6, 8 failed the fit tolerance; first read as SAS stopping early | no: real data passed within tolerance with 814,511 text cells different | silent (small numeric differences in every downstream number) | 0ca3cdc; `migration/legacy-to-port/generated-inputs.md` |
| P13 | PORT | 4 | Reviewer's SAS run `sep_monthly_income_0p5_n2000_s0_sw0` (review of 2461757) | no | silent (estimates 1.9% off) | cf25ff5 |
| P14 | PORT | 4 | SAS run `oneclass_n60_two_variables` | no | silent | 428b5c9 |
| P15 | PORT | 4 | Reviewer's SAS ITPRINT runs D11-D13 (review of c1124e1 / 428b5c9) | no | unclear (designed separation inputs) | 099d6ce |
| P16 | PORT | 4 | Reviewer's SAS runs D6b, D6c | no | unclear (designed inputs) | 3f7c1d5 |
| P17 | PORT | 4 | Reviewer's ITPRINT runs; raw inputs `small12_43`, `small90_15` | no | silent | b798fe3 |
| P18 | PORT | 4 | Reviewer's SAS run D10 (three equal columns) | no | unclear (designed input) | f2791d1 |
| P19 | PORT | 4 | Separation measurement, 280 rows of seed 1 with a derived outcome | no | silent (final model differs) | `migration/legacy-to-port/separation-rule.md` part 3; 232e21d |
| P20 | PORT | 4 | 13 raw inputs measured for the owner's decision of 2026-11-17 | no | crash (500-step cap) | `migration/legacy-to-port/recycling-rule.md`; 8fd4e0a |
| P21 | PORT | 4 | Measurement, rare outcome; 40 X19 designs | no | crash | `migration/legacy-to-port/singular-information.md:8-13`; e6a87f5 |
| P22 | PORT | 4 | Generated seed 6 | no: contract passed, seed 6 failed one cell | silent (printed global Wald) | `migration/legacy-to-port/global-wald-rule.md`; 0ca3cdc, 524cd28 |
| P23 | PORT | 1o | Prover drafting `PyLinks` 6b could not exclude leverage 1 (C-g R3); X21, X23 measured SAS | no: not reached | silent (printed classification table; valid raw input R3) | `rounds/C-g-draft-2026-11-18.md:820-828`; bf8eb49 (x21 docstring); 88df42d |
| P24 | PORT | 4 | Measurement on 38 SAS runs | no | silent (printed Hosmer-Lemeshow) | a8ab250 |
| P25 | PORT | 4 | SAS runs with 2 groups | no | silent (tables SAS does not write) | e2b39ee |
| P26 | PORT | 4 | Small inputs, case (a) | no: contract passed | silent (`model_summary.csv` row) | `migration/legacy-to-port/small-inputs.md:17`; c336d8e |
| P27 | PORT | 4 | Small inputs, case (b), then X16 | no | silent (printed table) | 414f381, d4f25d2 |
| P28 | PORT | 4 | Separation runs `sep_age_gt_55`, `sep_age_gt_62` | no | silent (printed table) | 3e29b3f |
| P29 | PORT | 4 | Small inputs, case (d) | no | silent (extra printed tables) | 78adeef |
| P30 | PORT | 4 | Small inputs, case (e) | no | silent (printed tables) | f3922ac |
| P31 | PORT | 4 | Recorded SAS runs ev5, ev6 | no | silent (extra printed file) | c850e3a |
| P32 | PORT | 1d | S2(b), S3(b), S24(b), S25(b) disproved, 2026-11-12 | no: every fix left judged files byte-identical | edge (missing age is outside section 3) | `reports/report.md:69`; 599606f, 751c6d9 |
| P33 | PORT | 1d | S5(b), S27(b), S31 step 05, I8 disproved | no | edge (missing inputs before imputation, or outside section 3) | `reports/report.md:75,133`; eb33d7f, c00bd76 |
| P34 | PORT | 1d | S8(b), S10(b) disproved | no | edge (missing `default_flag`) | `reports/report-round2.md:155-157`; 3778ebc |
| P35 | PORT | 1d | S18(b) disproved | no | edge (missing defaults count) | `reports/report.md:106`; 5f7415c |
| P36 | PORT | 1d | `thm:sas_round_H8` disproved (500000000000) | no: pipeline rounds only 600..850 | edge (unreachable range) | `reports/report.md:147`; 32c4326 |
| P37 | PORT | 1d | `thm:merge_one_to_one_H10` disproved | no: no call site shares a column | edge (latent helper) | `reports/report.md:150`; e7e4f2b |
| P38 | PORT | 1d | I1 on: false by evaluation (round 1), disproved formally (round 2) | no: flag never judged | edge (silent with non-default `--fix-psi-bins`) | `reports/report.md:172`; `reports/report-round2.md:141`; 04b4d78 |
| P39 | PORT | 5 | Post-parity reviewer | no: flag not judged | edge (flag on) | `migration/legacy-to-port/post-parity/review.bugfixes.tsv`; 03f099b |
| P40 | PORT | 5 | Porting agent's own TODO #11, post-parity burndown | no: no judged input has a missing feature | unclear (whether a valid file gives a missing MODEL variable is not recorded) | `migration/legacy-to-port/post-parity/classification.md` row 11; eaef530 |
| P41 | PORT | 5 | Post-parity reviewer | no | unclear (as P40) | 19b6f55 |
| P42 | PORT | 5 | Post-parity reviewer | no | edge (crash on an empty frame) | a265259 |
| P43 | PORT | 5 | Post-parity reviewer (with a differential fuzz of the formatter) | no: BEST6/7 unused | records (print width) | be7713e |
| P44 | PORT | 5 | Post-parity reviewer | no: file not judged | records (extra file) | 334e62b |
| P45 | PORT | U | Experiment X09; who or what prompted it not recorded | unknown | edge (values over 12 characters are outside section 3 since G54) | f799a80, 2ca060a |
| P46 | PORT | 4 | Experiments X10, X10b, then review of 68db49f and X12 (what prompted X10 not recorded) | no: printed ROC not in contract | edge (one observation per class) | 68db49f, 993436c |
| P47 | PORT | 4 | Experiments X11, X13-X15, review of e2dc541 | unknown: `income_medians.csv` judged byte for byte from 2b9dbdf; whether a real median was affected is not recorded | records (last printed digit) | e2dc541, 0f7fc64 |
| P48 | PORT | 5 | Reviewers of the Q27 port changes | no | edge (header case outside the exact names) | 29511e2 |
| P49 | PORT | 5 | Same | no | edge | b1aa814 |
| P50 | PORT | 5 | Same | no | edge | 55eee8c |
| P51 | PORT | 4 | Measurement 2026-11-16 | no | edge (2-3 rows, outside section 3 since G57); not fixed | `migration/legacy-to-port/empty-validation.md` |
| P52 | PORT | 6 | Port translator, Lean update of 2026-11-19 | no | edge (NaN id; unreachable on valid input); open | `reports/2026-11-19-final-report.md:40-50` |

### LEGACY

For every entry the port reproduced SAS, so the parity judge (port vs SAS) could not catch it:
"no, by construction".

| ID | Kind | Finder | How, exactly | Judge | Severity | Evidence |
|---|---|---|---|---|---|---|
| L1 | LEGACY | 1d | `sas_Q18` disproved (also round-1 intent I5) | no, by construction | silent (grade wrong for every p >= 10%) | `migration/proofs/legacy-meets-requirements/reports/findings-for-legacy.md:135-147`; e1df983 |
| L2 | LEGACY | 5 | Porting agent's BUG(port) #4 (2026-11-05); Logos `sas_Q25`, I1 off confirmed | no, by construction | silent (PSI 0 on the real data) | `migration/legacy-to-port/post-parity/classification.md` row 4; `findings-for-legacy.md:183`; 766937c |
| L3 | LEGACY | 1d | `sas_Q15` | no, by construction | silent | `findings-for-legacy.md:125`; b7b1cd4 |
| L4 | LEGACY | 5 | Porting agent's BUG(port) #3; Logos `sas_Q13`, I2 off confirmed | no, by construction | silent | `classification.md` row 3; `findings-for-legacy.md:95`; 2d4fdef |
| L5 | LEGACY | 1d | `sas_Q1` | no, by construction | silent (age group with no known income) | `findings-for-legacy.md:9-19`; 167dc38 |
| L6 | LEGACY | 5 | Porting agent's BUG(port) #1; reviewer of the Q1/Q13 corrections | no, by construction | silent (77 real incomes cut) | `classification.md` row 1; 726048a |
| L7 | LEGACY | 1d | `sas_Q14` | no, by construction | silent (applicant declined) | `findings-for-legacy.md:107`; 12a28e4 |
| L8 | LEGACY | 1d | `sas_Q7` | no, by construction | silent | `findings-for-legacy.md:57`; 7b55ef1 |
| L9 | LEGACY | 1d | `sas_Q9` | no, by construction | silent | `findings-for-legacy.md:67`; 10f447e |
| L10 | LEGACY | 1d | `sas_Q23` | no, by construction | silent (KS tie) | `findings-for-legacy.md:163`; e8f879f |
| L11 | LEGACY | 1d | `sas_Q23` round 2 | no, by construction | silent (near-tied probabilities) | `findings-for-legacy-round2.md:9`; 3428731 |
| L12 | LEGACY | 1d | `sas_Q24` | no, by construction | silent | `findings-for-legacy.md:173`; 607dd5e |
| L13 | LEGACY | 1d | `sas_Q26` round 2 | no, by construction | silent (small validation sets) | `findings-for-legacy-round2.md:35`; ad9c945 |
| L14 | LEGACY | 1d | `sas_Q26` round 3 | no, by construction | silent (no defaulter in validation) | `findings-for-legacy-round3.md:23`; a9acbf5 |
| L15 | LEGACY | 1d | `sas_Q27` | no, by construction | edge (invalid input accepted) | `findings-for-legacy.md:205-230`; 9b8dc37 |
| L16 | LEGACY | 5 | Reviewer of the Q27 correction (inferred from the commit text only) | no | edge | 73bfde0 |
| L17 | LEGACY | 5 | Same (inferred) | no | edge (stale files after a stop on invalid input) | b40a55d |
| L18 | LEGACY | 1d | `sas_Q27` round 2; SAS run x21 E agrees | no | edge (text id) | `findings-for-legacy-round2.md:58`; a6c0b02 |
| L19 | LEGACY | 1d | `sas_Q27` round 3; reviewers found the two wrong corrections | no | crash (valid header-only test file refused) | `findings-for-legacy-round3.md:8`; 5913e11, 56e52f7, 697eed5 |
| L20 | LEGACY | 5 | Review of the Q25 proof: it rested on a `best8` link the real BEST8. does not meet | no, by construction | silent (PSI floor precision) | `migration/proofs/legacy-meets-requirements/reports/report-round2.md` item 3; 3e6dfa6 |
| L21 | LEGACY | 1d | `neg:sas_Q27_neg` (round 4), SAS run x24 | no | edge; not fixed (G53) | `migration/proofs/legacy-meets-requirements/reports/q27-old-disproof.md`; 5096f00 |
| L22 | LEGACY | 4 | Measurement 2026-11-16 | no | edge (1-3 rows, ruled out by G57) | `migration/legacy-to-port/empty-validation.md` |

### LEAN

The parity judge never runs the Lean: "no (out of reach)" for all ~~17~~ 18 (2026-11-20). Severity is *model* for all.

| ID | Kind | Finder | How, exactly | Judge | Severity | Evidence |
|---|---|---|---|---|---|---|
| T1 | LEAN | 3 | Fuzz, seed 700248 (279 of 2,699 targeted seeds) | no (out of reach) | model | `migration/port-to-lean/diffeval/receipts/fuzz_2026-11-18.tsv` |
| T2 | LEAN | 3 | Prelude differential attack, class D2 | no | model | prelude attack records (A1, A2) |
| T3 | LEAN | 3 | Prelude attack, D3 | no | model | (A3) |
| T4 | LEAN | 3 | Prelude attack, D10 | no | model | (A4) |
| T5 | LEAN | 5 | Both B3 reviewers independently | no | model | `migration/port-to-lean/reviews/verdicts.md:16,25` |
| T6 | LEAN | 5 | B5 reviewer, with reproducers | no | model | `verdicts.md:47-48` |
| T7 | LEAN | 5 | Review (port-translator-7); the magnitude clause from fuzz | no | model | `migration/port-to-lean/update-2026-11-17.md:313,417` |
| T8 | LEAN | U | Port translator during C-m; what showed the gap not recorded | no | model | `migration/port-to-lean/update-2026-11-18.md:246-258` |
| T9 | LEAN | 5 | B3 implementer (B5) | no | model | `verdicts.md` (B5) |
| T10 | LEAN | 5 | SAS-side reviewer (A4) | no | model | `migration/legacy-to-lean/amendments.md:8` |
| T11 | LEAN | 5 | SAS-side reviewer (A5) | no | model | `migration/legacy-to-lean/amendments.md` |
| T12 | LEAN | 5 | SAS-side reviewer (A6) | no | model | same |
| T13 | LEAN | 5 | Reviewer, confirmed by SAS run x21 | no | model | `migration/legacy-to-lean/corrections-account.md` |
| T14 | LEAN | 5 | Reviewer, x21 | no | model | same |
| T15 | LEAN | 5 | Three reviewers, x23 | no | model | same |
| T16 | LEAN | 5 | Reviewers, x23 H | no | model | same |
| T17 | LEAN | 4 | SAS experiment x27, prompted by the port's small-input runs | no | model | `migration/legacy-to-lean/corrections-round7.md:1-39` |
| T18 | LEAN | 3 | Differential fuzzing of the fidelity pass, 2026-11-20: `m2ll0` placeholder (0.0 vs NaN when no fit), 461 of 2,473 kept cases; reaches no compared output | no (out of reach) | model | `migration/port-to-lean/diffeval/receipts/fuzz_2026-11-20c-train-a.tsv`; `migration/port-to-lean/RULEBOOK.md` (known limits) |

### SPEC

Not program defects: "no (n/a)" for the judge, severity *records* for all ~~19~~ 20 (2026-11-20).

| ID | Kind | Finder | How, exactly | Evidence |
|---|---|---|---|---|
| S1 | SPEC | 1d | `thm:train_run_01_fit_frame_C4` disproved 2026-11-12 and 2026-11-17 | `rounds/disproof-C4-2026-11-17.md` |
| S2 | SPEC | 1d | `thm:roc_association_C2` disproved | `reports/findings-for-code.md:181-185` |
| S3 | SPEC | 1d | `thm:run_py_F1_frame` disproved | `reports/report.md:197-200` |
| S4 | SPEC | 1d | Logos round 1 | `reports/report.md`; ff1ea35 |
| S5 | SPEC | 1d | Logos rounds 1-4 (several disproofs) | `reports/report.md`, `report-round2.md`, `findings-for-code.md:208-211` |
| S6 | SPEC | 1o | Prover-1 while stating | ledger only; `reports/2026-11-18-final-report.md` (C-a to C-c) |
| S7 | SPEC | 1o | Prover-3 writing T0's witness | `reports/2026-11-18-final-report.md:225-226` |
| S8 | SPEC | 1o | C-g draft R6; observation H15 confirmed it | `rounds/C-g-draft-2026-11-18.md:847-857`; `rounds/observation-H15-2026-11-18.md` |
| S9 | SPEC | 5 | Definitions author reading the code while writing C-h | `definitions-v3.md:864-890` |
| S10 | SPEC | 1d | E4's prover (the E4 disproof's input) | `rounds/disproof-E4-2026-11-17.md`; f88bd93 |
| S11 | SPEC | 1o | Provers of G2, G4, F4 | `reports/2026-11-18-final-report.md:236-245`; 45e0363, 639a134, 4399051, c4a0cd0 |
| S12 | SPEC | 1d | S13's prover | ledger only (not re-checked) |
| S13 | SPEC | 1d | Prover-6 (padded text) | `migration/proofs/legacy-meets-requirements/reports/saslinks-padded-text-draft-2026-11-18.md` |
| S14 | SPEC | 4 | Port-side planning and runs on small generated files, confirmed by SAS runs x25, x26 | `migration/proofs/legacy-meets-requirements/reports/round-6-2026-11-16.md:33-45` |
| S15 | SPEC | 5 | Review of the Q25 proof | `migration/proofs/legacy-meets-requirements/reports/report-round2.md` item 3 |
| S16 | SPEC | U | "Round-4 notes", not read in full by the ledger's author or here | `migration/proofs/legacy-meets-requirements/reports/round4-notes.md` (not read) |
| S17 | SPEC | 1d | Requirement contracts on the SAS blueprint | `migration/requirements/requirements.md` rulings G28-G31, G39, G53 |
| S18 | SPEC | 1d | Provers, 2026-11-19 | `reports/2026-11-19-final-report.md:282-286` |
| S19 | SPEC | 5 | Audit of 2026-11-19 | `reports/2026-11-19-final-report.md` |
| S20 | SPEC | 5 | Non-author review of the glue, fidelity pass 2026-11-20 (fidelity finding F1: `PyLinks` clause 10 unbounded; fixed by restating to n < 10^8, C-n) | `definitions-v3.md` (C-n); `informal-spec.md` (change note of 2026-11-20) |

S12 and S18 are counted 1d as the ledger states them; the negation items are not named in the
records read here, so a reader may prefer 1o. Moving them would not change any PORT count.

## Points that need a decision before publishing

- **Finder code 1o versus 1d.** P3 and P23 were found because a prover could not discharge an
  obligation and read the code to see why, not by a proved negation. If the post says "a proof
  failed", both qualify; if it says "Logos produced a counterexample", only P1, P2, P5, P10, P32-P38
  do, and the silent valid-input count drops from 3 to 2 (P1, P2).
- **P1's witness is not in the records.** If the post cites P1 as a disproof, the negation item
  should be named from the blueprint first.
- **"Found by Logos" is 13 of 52 PORT entries.** 26 came from runs on new inputs and 11 from review.
  An honest framing: Logos found the defects the parity tests structurally could not see (P1, P2),
  and its rounds drove the SAS measurements that found most of the others.
