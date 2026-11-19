# Equality stage: final report (for the owner's sign-off)

2026-11-19. Supersedes `2026-11-18-final-report.md`, and replaces the earlier text of this file
(written while E1, E2 and `lem:ex_port_train_outcomes` were open; they are now proved).
Port blueprint `py-credit-risk-port` `5365851c-5549-44b7-9207-4bd4c422031d`; SAS blueprint
`sas-credit-risk-spec` `3f5df696`; requirements `credit-risk-requirements` `006ff04c` (Draft 10).
This file holds no Lean.

**Result: every contract is stated and proved.** Two points need the owner's eye before sign-off:
the NaN row id (section 2) and one unexplained item count (section 7). Neither is a failed proof.

Sources read: `../informal-spec.md` (version 3, amendments 1 and 2), `../definitions-v3.md`
(corrections C-a to C-m), `2026-11-18-final-report.md`, `migration/port-to-lean/update-2026-11-18.md`
(sections 6 and 7), `migration/requirements/requirements.md` (Draft 10), the audit result of this
run, and `git log` (head 4a757fb). Where a record is not in these files, the report says so.

## 1. The claim in plain words

On every valid input, the Python port writes the same compared files as the corrected SAS program.
Valid input is `CreditRisk.InputOK` (requirements section 3, Draft 10). Each contract is stated on
what the pipeline reaches from a valid input, not on tables or argument combinations the code never
builds. No contract carries a precondition, a `wf_` domain, a limit or a "not covered" clause of
its own.

The contracts: equality on the interface (E1 to E11); equality of files outside it (F1 to F6);
faithfulness of the assembly (A1 to A4); coverage of the port's stage preconditions (G1 to G4);
predict on a run without a model (P0); and T0, T1, T2. The 26 requirements proved of the SAS
program are taken to hold of the port by inference from the equality (owner, 2026-11-18). They are
not proved again.

## 2. What the claim rests on: B1 to B6 of amendment 2

This is the claim's only boundary (owner, 2026-11-19; informal-spec, amendment 2).

- **B1. The claim.** End to end, on every valid input. A statement false only on an input no run
  reaches is restated to the reached input (text first, then Lean) and proved. That is not a
  narrowing. Step lemmas kept from version 2.3 may carry conditions on their arguments if every
  contract that uses them discharges those conditions.
- **B2. Valid input.** `InputOK`, Draft 10.
- **B3. Step requirements are proved.** A unit may require something of its argument only if G1
  to G4 and the section 4a lemmas prove the pipeline passes such an argument on every valid input.
  If one cannot be proved, the port is fixed. The first clause of `lem:sas_cov_total_good_bad`
  (fewer than 10^8 rows) follows from `InputOK` (G56 formal).
- **B4. The trusted base**, taken as given. (1) The model fit on a training part with both
  outcomes returns a model, the same on both sides, with the facts of `PyLinks` 6 and 6b. (2) numpy
  `solve`, `inv`, `matmul`, `matvec` behave as `PyLinks` 13 says. On what a valid run reaches,
  `solve` and `inv` raise no error, because selection leaves out every linearly dependent variable
  (X28). (3) CSV readers and writers are parameters, described by `PyLinks` from observed runs. A
  file not written and a header-only file both give the table with no row. (4) `Float` is the
  arithmetic of both programs, with the recorded last-bit difference of `exp` and the fuel 4096 of
  `_randbelow`.
- **B5. Outputs.** Exactly the files the parity judge compares. Printed reports, `printed_*`
  files, coefficient and stepwise printouts and printed formats are outside the claim.
- **B6. During a run** only a finding that would change B1 to B5 goes to the owner.

Also in force: `PyLinks` and `Paired` (corrections C-a to C-m). Judging is off on `5365851c`
(decision D7), so that each Lean statement says what its text says rests on the recorded reviews.

### The former narrowings and B3

The audit confirms that G1 to G4 and the 4a lemmas now cover the unit preconditions. It does not
list, narrowing by narrowing, the item that proves each. The table gives what the audit and the
records show. Where no single item is named, the report says so. It does not guess.

| Former narrowing | Proved by | State |
|---|---|---|
| `classification_table` clause 7 | G2, G4 (B3) | covered; the audit names no separate item |
| `hosmer_lemeshow` String Series | G4 (B3) | covered; the audit names no separate item |
| train step 06 `0 <= idx` (`train_run_06_coefficients_odds_precond`) | G2, resting on the Intercept-first clause (`PyLinks` 14, C-k) | covered; the audit names no separate item |
| train step 06 `exp` NaN and infinity clauses | G2 (B3) | covered; the audit names no separate item |
| `split_ids != []` of `fe_run_06_split_precond` | G1 and `lem:py_split_ids_rowids`, `lem:py_split_fits` (C-k) | covered; both lemmas are `lem:` items and the audit finds every `lem:` item proved |
| non-empty training table of `run_py_precond` | G2, G4 | covered, same reading |
| fewer than 10^8 rows | `lem:sas_cov_total_good_bad`, both clauses | proved |
| no NaN row id in `fe_run_06_split_precond` | none | **not a proved fact; see below** |

**NaN row id.** B3 calls "no NaN row id in `fe_run_06_split_precond`" a proved fact. The
precondition does not say that. It has an `isFinite` clause on the split ids. Its comment says a
NaN `row_id` when the split file does not fit is "Not excluded (no clause; reported to the owner,
2026-11-19)". The reason: Python's `set` keeps each NaN as a distinct object, so which ids are
drawn is not a function of the input. The Lean sorts in first-occurrence order. On `InputOK` rows
with present ids this case is not reached, and at the real numbers it does not arise. Still, this
is a recorded behaviour of the port that the Lean does not model. By B3 the options are to prove it
cannot happen on valid input, or to fix the port. The owner decides (section 8).

Several unit preconditions (`fe_run_01/02/03/06_split_precond` and others) keep comments marked
"narrowing", such as `0 < height` and Float64-only columns. They sit on unit items, not on
contracts. G1 to G4 prove them on what a valid run passes, so they are within B3.

## 3. Contracts and their states

Read from the port blueprint `5365851c` by the audit (read only, Logos MCP Staging).

- 368 items; 367 statements formalized; statements to write: none; proofs to write: none; waiting:
  none.
- All 75 `thm:` items and all 92 `lem:` items are `TheoremProved`, failure count 0 on every
  contract.
- Every `def:` item is `DefinitionFormalized`.
- No auxiliary item, no `neg:` item, nothing flagged false. No `zz_` item (the grep hits only
  `_ROUND_FUZZ_CAP` and `sas_round`).
- Contracts run summary: resubmitted none, needed proving none.

| Contract | State |
|---|---|
| E1 to E11 (E7 included) | proved |
| F1 to F6 | proved |
| G1 to G4 | proved |
| A1 to A4 | proved |
| T0, T1, T2 | proved |
| P0 (`thm:P0_predict_no_model`) | proved (see the audit note on its SAS half) |
| `thm:train_run_01_fit_frame_C4` | proved, restated: the mask is true exactly when the 36 candidates and `default_flag` are non-null |
| example items (witnesses that each contract's hypotheses can be met) | proved; inhabitation shown in every case |

Each statement assumes only `PyLinks` and `Paired` (or `SasLinks` for T2 and the 4a lemmas),
`InputOK`, the reached equations and `ScoreRun`. A3 assumes neither `PyLinks` nor `InputOK`. The
46 step and helper lemmas kept from version 2.3 keep `hpre` and `wf_` hypotheses, which B1 allows
because their users discharge them. There was no `sorry` or axiom scan (Logos refuses both; the
check is `TheoremProved`).

## 4. Changes since the 2026-11-18 report

- **C-g bundle** (owner, 2026-11-18). `PyLinks` 6 strengthened; 6b, 7b, 8b, 8c, 12, 13 added;
  `def:ScoreRun`; one-outcome training covered on three levels; new contract P0. `SasLinks` (3)
  weakened for the training score file. Corrections C-h and C-i followed: restated `Paired` 5,
  `PyLinks` 8 `keeps`, conjunct 16, `matmul`, new `lem:py_scores_valid_empty`.
- **SasLinks tightening** (owner, 2026-11-18). (1) and (2) tightened on the SAS blueprint for the
  padded-text limit. The SAS dependents were proved again.
- **One-outcome training** in the port (65430e4, 70c4d9c, 1a90814). With one outcome the port fits
  no model and runs on, and the metrics files are written on header-only validation scores, as SAS
  (x27 C60/E60). F4 loses its two-outcome condition.
- **X21, X22, X28 port fixes.** Leverage near 1 in the classification table (88df42d, X21). A
  parameter left out of a singular information matrix has variance 0 (a9b1f41, X22/R4). A step
  with X'X singular leaves its dependent variable out of the global tests and fit statistics
  (3272e9d, X28). X28 is what makes B4.2 true on reached runs.
- **G56 formal** (Draft 10, 2026-11-18). Each raw file has fewer than 10^8 rows, a clause of
  `TrainOK` and `TestOK`. 60 requirement items re-proved with the same witnesses. The first clause
  of `lem:sas_cov_total_good_bad` now follows from it.
- **`_hl_groups` exact division** (2026-11-18, lead, no narrowing). `n / g` is one correctly
  rounded division. The precondition is generic, overflow clauses added, the 2^52 bounds dropped.
- **PSI.** Recorded in `update-2026-11-18.md` section 6 (A): the clause `0 < logit_scored_train.height`
  of `def:metrics_run_06_psi_precond` is lifted (owner). Python returns on an empty training frame
  (fuzz: Lean equal to Python on all 77 such inputs). The statement text was edited first, then
  the Lean. **The "one-row text fix" named in the task has no record in the files read.** It is
  not described here.
- **C4** restated to the true statement and proved (owner, 2026-11-18). It keeps
  `hpre : train_run_01_fit_frame_precond`, allowed by B1. The negation item is gone.

### Split fix C-j, C-k, C-l (2026-11-19)

- **C-j.** Owner's decision on the T0 disproof: "Fix the port". The port's split selects exactly
  (7n+9)/10 distinct ids among the input's (commit 4a757fb; `feature_engineering.py` 20-25 and
  352-366). The split file is used only when it names exactly that many pairwise distinct ids, all
  among the input's. Otherwise the port draws `random.Random(42).sample` of the sorted present
  ids. `PyLinks` 5 restated (text, then Lean). `Paired` 2 and `SasLinks` (5) line up again. The
  Lean unit was written and fuzzed: 800 inputs compared against the real port, 0 differences.
  54 items were cleared by the write and resubmitted from stored drafts.
- **C-k.** Owner's decisions "G2 fit": "Add the clause", and "S6 lemmas": "Restate for the
  pipeline's split". `PyLinks` gains clause 14: the final fit's first name is `Intercept`, on every
  argument (the Intercept-first clause). New split lemmas `lem:py_split_ids_rowids` and
  `lem:py_split_fits`: the ids passed to `py.split` have the feature frame's present row ids, and
  the table the split returns fits, so the unit takes the file branch with no drawing. Both are
  proved.
- **C-l.** B4.2 made formal with no change: no precondition asks `solve` or `inv` to return, the
  Lean routines are total functions of `def:PyParams`, and `PyLinks` needs no clause. G2 now says
  "no limit of its own" and rests on B4.2 and C-l.
- **C-m.** `def:train_run_08_ctable_precond`: null clauses of train.py :482 and :486 guarded. The
  four items the write cleared were restored unchanged.

## 5. The owner's and the lead's answers of 2026-11-19

- Owner, T0 disproof ("Port split"): "Fix the port" (C-j).
- Owner, "G2 fit": "Add the clause" (C-k, `PyLinks` 14).
- Owner, "S6 lemmas": "Restate for the pipeline's split" (C-k).
- Owner, on step lemmas with conditions: "Just finish", on the lead's recommendation (B1).
- Owner, amendment 2: B1 to B6, binding over any older text.
- Owner, `PyLinks` 8 `keeps` and 13 `matmul` changes (C-h).
- Lead: lifted "change no existing item" for `def:PyLinks` only, for the C-j and C-k tasks; took
  the `_hl_groups` division as no narrowing; approved C-m.

No further answer of 2026-11-19 is in the files read. The lead should add any that exist.

## 6. The Logos 503 outage during the run

The task names a Logos 503 outage during this run. **No record of it is in the files read.** What
is on record: `migration/audit/logos-requests-2026-11-19.md` section 6 measures that compiling
calls queue on the server (about four at a time). The audit of this run read the blueprint without
trouble and reports that every item is proved, so the outage left no item unproved. It did not
change what is claimed. How long it lasted and which calls it cost are not known to the writer;
the lead should state them.

## 7. Audit results

Read-only audit of `5365851c`: gates pass.

1. Every contract of version 3 (amendments 1 and 2) has an item and is `TheoremProved`: E1 to E11,
   F1 to F6, G1 to G4, A1 to A4, T0 to T2, P0, and the example items. No contract carries a
   precondition, `wf_` domain, limit or "not covered" of its own.
2. Every proof item is `TheoremProved`.
3. No `zz_` item, nothing flagged false, nothing left to state or prove.
4. C4 is restated and proved; its negation is gone.

Findings for the owner to weigh. None is a failed contract.

- **Count gap, unexplained.** `get_status` reports 368 items but 367 statements formalized, with
  nothing left to write. Every listed item is formalized or proved, so one item is counted but not
  listed. It may be a hidden item or a server miscount. A read-only audit cannot tell. Ask the
  Logos side, or recount.
- **P0, SAS half is weak.** It states `predict_inputs_stop (sas.mediansExist train) false = true`
  with the coefficients flag written as the literal `false`. It uses nothing from the run, so it is
  very likely true by the definition alone. The spec lets the stater fix the spelling, and no SAS
  unit writes `model_coefficients.csv`. The half proves nothing about the SAS run.
- **One-directional file contracts.** F1, F2 and E7 are "when the port stage returns files". They
  hold vacuously if the stage returns nothing. F3 to F6 and P0 state an equality of options. That
  the port returns on a valid run follows only indirectly, from E1, E6 and the wiring. A reviewer
  should confirm this reading. A1, A3 and A4 say "when" in the spec text itself.
- **Hypotheses beyond B.** All come from the spec text. E4 and `lem:sas_reached_scores_read_shape`
  assume every term of the model names one of the 36 candidates (a property, not a reached
  equation). T2 assumes `CreditRisk.Fitted` and the defining equation of the fit. C4 keeps `hpre`.
  The 46 kept lemmas keep `hpre` and `wf_` hypotheses, so the `wf_` defs remain in the blueprint
  although spec section 7 lists the `wf_` domains as withdrawn.
- **Three spellings of the no-fit training score table.** `PyLinks` 7b, A4 and `ex_A4_metrics` use
  the `pyPipeline.score` fillers. G4 and `ex_G4_run` use empty fillers. All start from the empty
  `StepwiseResult`. On the reached no-fit run they agree (`PyLinks` 6 forces `py.fit = {}`, and E5
  shows the file does not depend on the fillers). Cosmetic.
- **Examples.** For the no-model half, spec 2b asks for four training rows, every outcome 0, the T1
  parameters. `ex_E3_fit`, `ex_E5_train_scores` and `ex_F3_final_model_output` state it. The others
  (`ex_F4_model_summary`, `ex_A2_train`, `ex_A4_metrics`, `ex_G2_run`, `ex_G4_run`,
  `ex_metrics_run`, `ex_P0_predict_no_model`) state bare existence. Inhabitation is shown in every
  case.
- **Stale records, no blueprint change needed.** (a) `informal-spec.md` section 7 still says "C4
  and its proved negation". (b) `reports/report.md` still lists C4 as disproved. (c) The Lean
  comment of `thm:T2` says the feature-shape wording is "not yet fixed by E4's reviewer". (d) Spec
  section 4 still carries G2's old "Not covered" sentence on LinAlgError, superseded by B4.2 but not
  struck through.
- **NaN row id** next to the B3 wording: see section 2.

## 8. What the owner must still do

1. Decide the NaN row id. Either fix the port so the split cannot meet it, or have B3 and the spec
   say it is a recorded behaviour outside the model. B3 as written says to fix the port.
2. Have the count gap checked: 368 items, 367 formalized, one not listed.
3. Confirm the one-directional reading of F1, F2 and E7, and accept or strengthen the SAS half of P0.
4. Ask the lead for the missing records: the PSI one-row text fix, any other answer of 2026-11-19,
   and the 503 outage (how long, which calls).
5. Have the stale records of section 7 struck through.
6. Sign off. `verification_approved` on `5365851c` is set by the owner, not by this report.
7. Push. Branch `initial` has commits from 2026-11-18 and 2026-11-19 not on origin (89c15e6 was the
   last push on record) and an uncommitted working tree (`definitions-v3.md`, `informal-spec.md`,
   `requirements.md`, `manifest.tsv`, `update-2026-11-17.md`, fuzz files). The owner decides what
   is committed and pushed. This role made no git call.
