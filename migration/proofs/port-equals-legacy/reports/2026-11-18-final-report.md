# Equality stage: final report (for the owner's sign-off)

2026-11-18. Port blueprint `py-credit-risk-port`
`5365851c-5549-44b7-9207-4bd4c422031d`; SAS blueprint `sas-credit-risk-spec` `3f5df696`;
requirements `credit-risk-requirements` `006ff04c`. This file holds no Lean.

Sources: `../informal-spec.md` (version 3; section 6 cut by the owner on 2026-11-18 except T0 to
T2), `../definitions-v3.md` (corrections C-a to C-f), `2026-11-17-equality-round-1.md` (the round
record: limits, owner's decisions, the lead's rulings), `../rounds/disproof-E4-2026-11-17.md`,
`../rounds/disproof-G1-2026-11-17.md`, and in `migration/legacy-to-port/`: `recycling-rule.md`,
`singular-information.md`, `global-wald-rule.md`, `separation-rule.md`. Commits from `git log` on
branch `initial`. The state at the close is in the table at the end.

## 1. The claim

The Python port equals the legacy SAS program on valid input. Each contract is an item of the port
blueprint and has the same form: at the real numbers, for all port parameters `py` and SAS
parameters `sas` with `PyLinks py` and `Paired py sas`, for every raw training table, raw test
table and seed that are valid input (`CreditRisk.InputOK`), the step of the port pipeline returns
what the same step of the SAS pipeline returns, stopping included. Write P for `pyPipeline py`, S
for `sasPipeline sas`.

Equality on the interface (spec section 2):

- E1. The training feature table: `P.features` and `S.features` both return or both stop, and the
  training tables are equal.
- E2. The validation feature table: when both return, the validation tables are equal.
- E3. The model: on the training feature table SAS returns, `P.fit` is `S.fit`.
- E4. The scores: for every model and every table of feature shape, `P.score` is `S.score`
  (feature shape narrowed by the lead, section 5).
- E5. The port's training scores: the `risk_scores_train.csv` its train stage writes is `P.score`
  of the training feature table.
- E6. The test predictions: `P.scoreTest` is `S.scoreTest` on the reached model and tables.
- E7. The column names and their order in `test_predictions.csv` and `kaggle_submission.csv`
  are those the SAS units give.
- E8 to E11. The validation summary, KS table, decile table and threshold table: on the reached
  score tables both metrics stages return or both stop, and each of the four tables is equal.

Files outside the interface, each against the composed SAS units (spec section 5):

- F1. `income_medians.csv`.
- F2. `kaggle_submission.csv`.
- F3. `final_model_output.csv`.
- F4. `model_summary.csv` (with the condition of section 5 below: training part with both
  outcomes, and a read-back hypothesis).
- F5. `calibration_plot.csv`.
- F6. `model_performance_metrics.csv`.

Faithfulness of the assembly (spec section 3), so that the contracts are about the port and not
about the wiring:

- A1. The two feature files `run` writes are the pair `P.features` returns.
- A2. The model the train stage returns is `P.fit`; its validation scores are `P.score`; its
  training scores are the table of E5.
- A3. The `test_predictions.csv` the predict stage writes is `P.scoreTest`, and the file is among
  those it returns.
- A4. The four files the metrics stage writes are the four tables of `P.metrics`.

Coverage of the port's stage preconditions (spec section 4). The port's Lean cannot say "the
Python raises"; a raise is excluded by a precondition. So the claim for a stage is its equality
contracts together with:

- G1. On valid input, the precondition of `run` holds where a valid run calls it.
- G2. Likewise for the train stage, for what `PyLinks` gives (steps 01 and 04; the rest is
  section 2 below), with two hypotheses ruled by the lead (section 5).
- G3. Likewise for the predict stage.
- G4. Likewise for the metrics stage, with the same two hypotheses as G2.

Kept from section 6 of the specification:

- T0. For every `py` meeting `PyLinks` there is a `sas` paired with it; when the port's read-backs
  are the identity, that `sas` meets `SasLinks`.
- T1. Some `py` meets `PyLinks` with identity read-backs (the hypotheses are not empty).
- T2. On valid input, the test feature table that requirements Q12 and Q13 score has the
  feature shape of E4.

Also on the blueprint and part of the record: the 20 SAS coverage lemmas `lem:sas_cov_<unit>`
(phase 1, all proved by the round record: the precondition of each SAS unit holds where the SAS
pipeline calls it on valid input), the 42 kept theorems of version 2.3 (phase 0), and contract C4
with its proved negation (the port's fit mask also drops a row with a missing outcome; not
reachable on valid input, which is proved on the SAS side only; the port side follows once E1 and
E2 are proved and may not be cited before).

What the claim rests on:

- `PyLinks py` (`definitions-v3.md` section 2, as corrected): what the port's out-of-scope code is
  taken to do: reading numbers from text, the 12-character round trip, the two importers, the
  split, the fit, the existence of files, the read-backs keeping their shape (clause 8), the model
  file, counts as text, and the date as a numeric cell. Each clause cites the observation it rests
  on (RULEBOOK 2.8 of `migration/port-to-lean/`).
- `Paired py sas` (section 3, as corrected): the SAS importers meet `SasLinks` (1) and (2); the
  SAS split selects the rows the port's split lists; the SAS fit returns the model the port's fit
  gives; the four read-backs are one function shared by both sides; the SAS flags meet `SasLinks`
  (8) on their own side; `agg` is the sum and the mean, `arrange` the identity; the same date.
- The model fit as a parameter (ruling G58): stepwise selection and the optimiser are outside the
  proofs on both sides. The equality is given the same fitted model. The two real fits agree only
  to the judge's tolerance (SAS stops at GCONV 1E-8).
- Judging is off on `5365851c` (decision D7): that each Lean statement says what its text says
  rests on the reviews recorded in the round record, not on the server.

## 2. Not covered

- Input that is not valid (G53). Nothing is claimed off `InputOK`.
- Raw files of 10^8 rows or more (G56). Counts are taken as exact on both sides (`PyLinks` 10);
  from 10^8 the real 8-character count round trip rounds. Same limit on the SAS side
  (`total_good_bad`, first clause of its precondition).
- Present `MonthlyIncome` and `NumberOfDependents` written in more than 12 characters (G54, a
  clause of `TrainOK` and `TestOK`).
- Hand-off precision (G55). The equality contracts hold both at full precision and when the
  hand-off files are read as the 12-character files the programs write (one shared, otherwise free
  read-back). The requirements were proved of SAS at full precision only, so what the
  12-character and 15-digit files lose is outside the inference of section 3.
- Fewer than 4 training rows (G57, a clause of `TrainOK`); with at least 4, neither split set is
  empty.
- The fit (G58): taken to return a result, the same on both sides; the claims hold for inputs
  whose training part has both outcomes (with one outcome the real SAS fits no model, experiment
  x27). Extension by the lead's ruling of 2026-11-17: the train stage completing after the fit
  (steps 03 and 05 to 08, before `model.json` is written) is not covered. `PyLinks` 6 gives only
  what steps 01 and 04 ask; a fit with zero covariance meets it and makes step 06 divide by zero
  (`train.py:347`). The real fit does not return this on a two-outcome training part. A raise there
  would stop `model.json` and every output after it, not only printed files (correction to spec
  section 4).
- Number forms in the input files (owner, 2026-11-17): the claim covers files written in plain
  digits with missing values blank, `.` or `NA`, as the real data are. The requirements also
  admit `+5000`, `5e3`, numbers padded with blanks and `na`, ` NA`, `NA ` as missing; on such a
  file the real importer does not meet `PyLinks`.
- A header-only test file for E7: E7 holds but says nothing there (the SAS table carries its
  column names in its rows and has none). Same class as the recorded limit on header-only files.
- Floating point: the contracts are at the reals; nothing is claimed about `Float` (overflow, NaN,
  summation order). One instance is on record: the last bit of `exp` differs between the Lean
  evaluator and CPython/polars on a few inputs (RULEBOOK of `migration/port-to-lean/`, section 6:
  `def:run_py_py` 3 of 2,314 fuzzed runs, `def:train_run_06_coefficients_odds` 5 of 3,400,
  `def:train_run_03_fit_global_rsquare` 1 of 2,280, where the Lean value is the correctly rounded
  one; the same for `log` in `def:metrics_run_06_psi`). This concerns the port's Lean against the
  port's Python under fuzzing, not the equality.
- CSV reading itself: importers and read-backs are parameters, described by `PyLinks` from
  observed runs. Also outside the model (prover-4's read): the split file as an input (missing or
  unreadable raises), a raise in train steps 02 to 08 before `model.json`, and predict testing
  `model_coefficients.csv` while it reads `model.json`.
- Files with no contract: `model_coefficients.csv`, `stepwise_summary.csv` (the fit is out of
  scope), the `printed_*` files (printed formats), the ROC tables beyond the area.
- Padded text on the SAS side (limit candidate, not yet ruled; section 5). A delivered text of
  31 blanks then "55" is admitted by `SasLinks` (1)/(2); the SAS Lean trims first and reads 55,
  the real BEST32. informat reads the first 32 characters, so 5. No real file reaches it (PROC
  IMPORT strips blanks). Port side checked by prover-1: the port links admit no padded number text
  and both Leans read the same number under `PyLinks` and `Paired`, so no equality contract needs
  an exclusion; it is a limit of the SAS-side claim only.
- Findings about the SAS side, nothing changed on the SAS blueprint: `total_good_bad` asks fewer
  than 10^8 rows (G56); `roc_valid` asked both classes before SAS round 6; `credit_raw_clean` and
  `test_raw_clean` ask each raw text to have at most 32 characters as delivered, while `SasLinks`
  bounds the trimmed length (the two coverage lemmas are stated for the clauses that follow; no
  equality contract may use the full precondition of these units).

## 3. The requirements

The 26 requirements proved of the SAS program (Q1 to Q16 and Q18 to Q27, signed off 2026-11-16
with limits G53 to G58) are taken to hold of the port as an inference from the equality, by the
owner's decision of 2026-11-18: "I don't want to reprove all the properties of the SAS blueprint
again for the python blueprint. If we proved equality I am happy to assume the other properties
translate over." They are not proved on the port blueprint: there is no `Agree` definition, no
transport lemma and no carried requirement (commit 03b92c8).

What the inference uses, so that the owner sees its premises: T0 (for a port with identity
read-backs there is a SAS instance meeting `SasLinks`, the setting of the SAS proofs), the
equality contracts on the interface, and T2 for Q12 and Q13. It holds at full hand-off precision
only (G55). One point the transports would have checked and nothing now checks by machine:
correction C-b gives `SasLinks` (5) for the `sas` T0 exhibits, not for every `sas` paired with a
port.

## 4. Differences found and fixed in the port during this stage

Each disproof was a proved negation with a concrete valid input. Under the owner's decision of
2026-11-17 the independent disproof check was dropped (commit fc69100), so each was taken as a
defect of the port and routed to the code side; the port's Lean then followed (fourth port diff,
recorded in `migration/port-to-lean/update-2026-11-17.md`).

- **E4: the score exports.** SAS's clean exports of the validation and training scores
  (`legacy/train.sas:350-359`) drop every column whose name starts with `IP_` or `XP_` and the
  columns `_FROM_`, `_INTO_`, `_LEVEL_`; the port wrote the frame unchanged. Witness: a one-row
  feature table with a column `IP_X`, the T1 parameters and the T0 pairing (`neg:E4_score_neg`,
  revision de4216b6). No real run has such a column. Recorded in 6856af9; fixed in b394838 (both
  score exports drop those columns, in any case of letters) and 8b74e6d (same class: a DATA step
  keeps its columns by upper-cased name, as SAS does, in `train.py` and `predict.py`); manifest
  and fourth diff in 7b09c31 and 89b4254.
- **G1: the split ids.** The port read the split file's `row_id` with a strict Int64 cast, which
  raises on an id that is not a whole number; `TrainOK` does not ask `VAR1` to be whole, and SAS keeps
  `row_id` as a double. Witness: four training rows with `VAR1` 1/2, 1/4, 3/4, 1/5, no test row,
  seed 0 (`neg:G1_run_coverage_neg`, revision f6a0bf0d). Recorded in 95c54db; fixed in 5784fc8
  (the ids are read as SAS numbers, no whole-number cast; the clause leaves step 06's
  precondition).
- **The fit, made to follow SAS (2026-11-17).** Under the owner's decision of 2026-11-17 that the
  port follows SAS on every small input where SAS completes, these were measured against SAS runs
  and fixed in `port/credit_risk/sas_compat.py` and `train.py`. The fit is a parameter of the
  proofs (G58), so the contracts neither found nor check them; the parity judge and the recorded
  experiments do.
  - A converged fit is SAS's: SAS's iteration and convergence test, with SAS's ridge (0ca3cdc,
    experiment X17); the ridge has no floor at 1e-4 (cf25ff5).
  - Quasi-complete separation: the intercept's element of the standardized inverse information
    is not counted (b798fe3; `separation-rule.md`, which builds on the separation fixes of
    2026-11-16, c1124e1 and f2791d1).
  - Recycling: stepwise selection ends rather than return to a model it has had (8fd4e0a,
    `recycling-rule.md`); the closing note moved to an inner function (45a5b78).
  - A singular information matrix: a parameter whose pivot is not above 1e-9 of its diagonal
    element is left out, as SAS does (e6a87f5, `singular-information.md`).
  - Global Wald test: a slope whose pivot is not above 1.5e-16 is left out of the chi-square, DF
    kept (measured in d6a7cb2, fixed in 524cd28; `global-wald-rule.md`).
  - Hosmer-Lemeshow: a group's average probability kept within [1e-6, 0.999999] (a8ab250); no
    table when the partition has fewer than 3 groups (e2b39ee).
  - The third port diff for the port translators: 5d2b519; manifest line ranges after the move:
    6efd36a.

## 5. Decisions for the owner at sign-off

**Definitions corrected before stating** (`definitions-v3.md`; each approved by the lead, each an
assumption of the claim). C-a and C-d removed assumptions that could not be met together.

- C-a, `PyLinks` 5 (commit 9640913): the count of the split (seven tenths, rounded up) is asked
  only for a list of present, pairwise distinct ids. As drafted it was unsatisfiable.
- C-b, `Paired` 2 (9640913): the split pairing is asked only of tables whose `row_id` is present
  and distinct. Consequence: `SasLinks` (5) holds for T0's `sas`, not for every paired one.
- C-c, `Paired` 7 (9640913): the SAS side carries `today` beside the 17 parameters; the port's
  `today` is the numeric cell holding it.
- C-d, the existence flags (604b534): no sharing of flags; `Paired` 5 restates `SasLinks` (8) for
  the SAS flags; `PyLinks` 7 its text clarified; `pyPipeline.fit` tests both feature flags, as the
  real train stage does. Shared flags made T0 false.
- C-e, `PyLinks` 11 (3538f74): `today` is a numeric cell. Without it T0 was false.
- C-f, `PyLinks` 8 (19967a0): each read-back also keeps one kind of cell per column, for every
  column. The real reader and the identity both meet it; G4 then needs, as a proved fact, that the
  score tables of a valid run have one kind per column.

**Contract texts changed or read with the lead's approval** (round record):

- E4 feature shape narrowed (f88bd93): the table has at least one column, and every term of the
  model names one of the 42 feature columns of `PyLinks` 8. Reached models meet both (T2,
  `lem:sas_fit_term_names`).
- G2 and G4 assume that `fsum` of a list of reals all at least 0 is at least 0, true of
  `math.fsum` (45e0363). Without it they fail on the ROC unit's precondition alone.
- G2 and G4 assume that their read-backs (G2 `readFeatures`; G4 `readScoresValid`,
  `readScoresTrain`) keep a present number present in the columns `PyLinks` 8 lists (639a134).
  Without it a read-back may empty the fit frame.
- F4 assumes a training part with both outcomes, under G58 (4399051). With one outcome in
  training and two in validation, SAS's `model_summary` has no row and the port's Lean has one;
  the real programs never reach it (the port's fit raises, SAS fits no model). A port change was
  not taken. The owner may overrule.
- F4 also assumes that the feature read-back keeps a present number present in the 42 columns and
  keeps the value of `default_flag` (c4a0cd0). Otherwise a relabelled outcome (2) splits the sides.
- `lem:py_score_fillers_idle` clause (2) restated with the cleaned frame after the E4 fix
  (b394838).
- Example items: `lem:ex_A3_predict` keeps its extra `PyLinks` and `InputOK` conjuncts;
  `lem:ex_E5_train_scores` rests on E1.
- A3, E7 and F2 also assert that the file is among those the stage returns, a stronger
  conclusion than the one line of the specification, with no added hypothesis (19967a0).
- S13 (kept step lemma) restated for both values of the new Boolean `roc_valid_created`
  ("reading 3"); F4 must take the Boolean from step 13, not as a free value.
- The coverage lemmas of `credit_raw_clean` and `test_raw_clean` stated without the length
  clause the links do not give (section 2).
- The train stage after the fit reported as not covered rather than a change to `PyLinks` 6
  (section 2).

**The `PyLinks` 8 question.** Three contracts now carry a read-back hypothesis of their own (G2,
G4: present numbers stay present; F4: the same, and `default_flag` keeps its value), and G2 and G4
carry the `fsum` hypothesis. The lead chose per-contract hypotheses over one correction C-g to
`PyLinks` because a correction to `def:PyLinks` clears every statement that depends on it again
(as C-f cleared 19). The assumption is the same either way and is true of the real reader and of
the identity. The owner decides: keep the per-contract hypotheses, or ask for C-g (clause 8: a
present number stays present and `default_flag` keeps its value; and `fsum` non-negative on
non-negative lists) and accept the restating and re-review of every dependent.

**The padded-text limit** (SAS-side claim, section 2). Proposed: "delivered texts carry no blank
at either end; not formal", listed with G53 to G58. Alternative: tighten links (1) and (2) of
`SasLinks` on the signed-off SAS blueprint. No equality contract depends on the choice.

**Push and merge.** Branch `initial` tracks `origin/initial` and is one commit ahead (f7d7b43);
the working tree also has uncommitted port-to-lean fuzz work (`manifest.tsv` modified, `fz3_*`,
`fz4_*` files untracked). The owner decides whether to push, and what is merged where (see the
points left open in the covering note).

## 6. Not done

- Source references on the blueprint. After the fourth port diff the items' source line ranges
  should have moved (for example `def:fe_run_06_split` to `feature_engineering.py:343-350`). The
  server's `update_item_source` rejects `file_path`, `line_start` and `line_end` as unexpected
  keyword arguments, and `get_items` does not return the stored references, so the stale items
  cannot even be listed. The ranges in `migration/port-to-lean/manifest.tsv` are current; those on
  the blueprint are not (`update-2026-11-17.md`, records step after the fourth diff).
- Stored code of the compositions, checked at the close (2026-11-18): `def:run` and `def:run_py_py`
  carry the port's current code (read through, not byte-compared). `def:run_py_py_py` was set
  again from `train.py:20-873` at HEAD; it is over the server's 30 KB read cap, so the result could
  not be read back (the sizes before and after agree).
- Evidence limits of phase 0, for the audit: proofs over 30 KB were rebuilt from the stale
  blueprint `b41b22d4` chunk by chunk; their identity with the accepted proofs is not shown, the
  server's acceptance against the present profile is the evidence. `lint` fails on every item and
  was not used as a recompile check.

## State at close

Read from the port blueprint `5365851c` on 2026-11-18 (`get_status`, `get_items`) after the
evaluation carriers were removed. The server does not return accepted solution revisions through
`get_items`, so the table gives states only.

| Contract | State |
|---|---|
| `thm:T0` | proved |
| `thm:T1` | proved |
| `thm:T2` | proved |
| `thm:G1_run_coverage` | proved (proved after the port fix (5784fc8)) |
| `thm:E1_features_train` | proved |
| `thm:E2_features_valid` | proved |
| `thm:E3_fit` | proved |
| `thm:E4_score` | proved (proved after the port fix (b394838, 8b74e6d) and the narrowed feature shape) |
| `thm:E5_train_scores` | proved |
| `thm:E6_score_test` | proved |
| `thm:E7_predict_column_names` | proved |
| `thm:E8_validation_summary` | proved |
| `thm:E9_ks` | proved |
| `thm:E10_decile` | proved |
| `thm:E11_threshold` | proved |
| `thm:F1_income_medians` | proved |
| `thm:F2_kaggle_submission` | proved |
| `thm:F3_final_model_output` | proved |
| `thm:F4_model_summary` | proved (proved, with the two-outcome condition (G58) and the read-back hypotheses) |
| `thm:F5_calibration_plot` | proved |
| `thm:F6_model_performance_metrics` | proved |
| `thm:G2_train_coverage` | proved (proved, with the fsum and read-back hypotheses) |
| `thm:G3_predict_coverage` | proved |
| `thm:G4_metrics_coverage` | proved (proved, with the fsum and read-back hypotheses) |
| `thm:A1_run` | proved |
| `thm:A2_train` | proved |
| `thm:A3_predict` | proved |
| `thm:A4_metrics` | proved |

- **Totals:** 317 items after the carriers were removed, 134 theorem, lemma and negation items:
  133 proved, the one that is not is C4 (below). Every equality contract and every example item
  (which shows a contract's hypotheses can be met together) is proved.
- The last three examples (`lem:ex_A2_train`, `lem:ex_G2_run`, `lem:ex_G4_run`), restated with
  their contracts, were proved at the close. `lem:ex_A2_train` and `lem:ex_G2_run` still declare
  `lem:ex_G4_run` as a proof dependency their proofs no longer use (the server only warns; a
  disconnect would clear the item's Lean).
- **C4:** `thm:train_run_01_fit_frame_C4` stays flagged false, with
  `neg:train_run_01_fit_frame_C4_neg` proved: a recorded fact about the port (the fit mask also
  drops a row with a missing outcome; no effect on valid input).
- **The negations of E4 and G1** (`neg:E4_score_neg`, `neg:G1_run_coverage_neg`) are gone from
  the blueprint: the port Lean update for the two fixes removed them.
- **Helper lemmas:** every `lem:` item a prover added during proving was reviewed afterwards by a
  second agent against its text (19 of 19 agree).
- **Evaluation carriers** (`def:zz_carrier_*`, six items) removed; nothing depended on them.
