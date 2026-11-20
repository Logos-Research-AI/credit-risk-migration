# Equality stage: final report (for the owner's sign-off)

2026-11-20. Supersedes `2026-11-18-final-report.md`. It keeps the 2026-11-19 text of this file,
with the 2026-11-20 results in section 0 and changes in the sections they touch.
Port blueprint `py-credit-risk-port` `5365851c-5549-44b7-9207-4bd4c422031d`; SAS blueprint
`sas-credit-risk-spec` `3f5df696`; requirements `credit-risk-requirements` `006ff04c` (Draft 10).
This file holds no Lean. No git call was made to write it.

Sources read: `../informal-spec.md` (version 3, amendments 1 and 2, notes and restatements of
2026-11-20, uncommitted working copy), `../definitions-v3.md` (corrections C-a to C-m),
`2026-11-18-final-report.md`, `migration/port-to-lean/update-2026-11-18.md`,
`migration/requirements/requirements.md` (Draft 10), `defects-ledger.md`,
`migration/legacy-to-lean/update-2026-11-20-model-coefficients-written.md`, and the read-only audit
of 2026-11-20 (second pass). Where a record is not in these files, the report says so.

## 0. Section 2026-11-20: what changed today and what the audit found

**Result: every contract is stated and proved, and every gate of the audit passes.** Contracts
are now E1 to E11, F1 to F6, G1 to G4, A1 to A4, T0 to T2, P0 and the new R. Points for the owner's
eye: what the NaN wording may say (0.2), what P0's SAS half now rests on (0.3), the contract count
(0.5), and records that still need a text edit (0.6).

### 0.1 State of the blueprint (read only)

- `get_status`: 370 items, 369 statements formalized, nothing to state, nothing to prove, nothing
  waiting, `verification_approved` true. This morning: 369 and 368.
- The audit read the state of all 370 items. 200 definitions are `DefinitionFormalized`. All 170
  theorem and lemma items are `TheoremProved`: 76 `thm:` and 94 `lem:` (37 are `lem:ex_*` examples).
  The one new item is `thm:R_port_returns`.
- No `neg:` item, no `zz_` item (a search for `zz_` finds only `def:_ROUND_FUZZ_CAP` and
  `def:sas_round`), nothing flagged false. Contracts run summary: resubmitted `thm:E6_score_test`
  and `thm:G3_predict_coverage`; needed proving: none.
- **The count gap.** `get_status` says 369 of 370 formalized, yet all 370 items read are formalized
  or proved. The audit could not find the item the server leaves out. The gap was already there
  (369 against 368) and moved with the new item. Do not quote "369 of 370" in public until the
  Logos side explains the counter.

### 0.2 NaN row id: the honest wording

`lem:py_split_ids_finite` is `TheoremProved`. The spec note of 2026-11-20 (now in the working
copy) says the NaN row id is unreachable on valid input and adds that NaN itself lies outside the
real-number model (B4.4). The record is consistent with this report: what is proved is below.

- At the real numbers the finiteness half says nothing. `Tabular.real_ops` proves `isFinite x = true`
  and `isNaN x = false` for every real `x`. The real content is that every id is present.
- The case that mattered (the id drawn, not read from the split file, where Python's NaN set order
  counts) is ruled out by `lem:py_split_fits`, not by this lemma.
- The lemma is a root. No contract uses it.

**Wording for public text:** "On valid input the row ids are present and the split file fits." Do
not write that NaN is proved impossible. NaN is outside the real-number model (B4.4). Ledger entry
P52 can close with this wording.

### 0.3 The 2026-11-20 restatements and what the audit makes of them

- **F1, F2, E7 as existence and equality.** They were conditional ("when the port stage returns
  files"). They now say that the features stage (F1) or the port stage (F2, E7) returns files, and
  that the table or the column names among them equal what the SAS units give. The port returning
  is part of the conclusion. Each is stronger than the old form and implies it. Their only
  hypotheses beyond `PyLinks`, `Paired` and `InputOK` are the reached equations of F2 and E7 (the
  returned F1, F2 and m), shown inhabited by examples. All three are `TheoremProved`.
- **Contract R (new, `thm:R_port_returns`): the port returns on every valid input.** Hypotheses
  `PyLinks` and `InputOK` only, no reached equation. The features stage returns F1, F2. Then either
  the fitted run (a model m; scores on F1, F2, the test scores and the metrics each return a table)
  or the run without a model (the fit returns nothing; the training score table is some table, the
  validation table has no row, and the metrics return tables). Test scoring is stated on the fitted
  run only; on the run without a model predict returns no result (P0). R closes the earlier gap that
  "both pipelines return on every valid input" was carried by G1 to G4 and the examples. It is one
  theorem now. Proved.
- **E4 kept in its strongest form.** E4 (and `lem:sas_reached_scores_read_shape`) assume that every
  term of the model names one of the 36 candidates. That is every model on the candidates, not only
  the fitted one. Restricting E4 to the fitted model would have weakened it. The spec text of E4
  says so, and T2 shows the reached model meets the condition. Proved.
- **P0 with its SAS half from the SAS Lean.** Before, the SAS half was `predict_inputs_stop ... false
  = true`, true by definition. At the owner's request (2026-11-20) the SAS blueprint gained
  `def:model_coefficients_written` (train.sas 419-424, depends on `def:train_inputs_stop` and
  `def:logistic_no_fit`). P0's SAS half now uses it:
  `model_coefficients_written (sas.featTrainExists F1) (sas.featValidExists F1) ...`. It is
  true when the script stops or the fit fits nothing, so the flag now comes from the SAS run. The
  port half still derives its flag from `run_py_py_py`. P0 proved. The record
  `migration/legacy-to-lean/update-2026-11-20-model-coefficients-written.md` evaluates the item
  against three staged SAS runs, all matching the log. Three points remain:
  - The validation flag is applied to F1, not F2. It copies how `sasPipeline`'s fit receives its
    inputs. By `Paired` 5 the two flags are the same predicate, so on a reached run the value is
    the same.
  - The item carries conditions of its own, stated in the record: one SAS session per script
    (no `work.model_coefficients` left by an earlier script), and the tables on which
    `def:logistic_no_fit` is stated.
  - `informal-spec.md` section 5 still describes the old SAS half. The spec of record is not
    updated. `def:model_coefficients_written` is in the uncommitted `manifest.tsv` and the update
    note only.
- **Hypotheses (gate 1 passes).** Every contract assumes only `PyLinks`, `Paired`, `InputOK` and the
  reached equations (`ScoreRun` counts as one). A3 assumes nothing, which is stronger than the spec.
  E5 and A2 quantify the idle arguments of steps 12 and 14 over every value, as the spec allows.
  No contract carries a precondition, `wf_` domain, limit or "not covered" clause of its own.
- **Extra hypothesis, minor.** `thm:A4_metrics` takes `sas` and `Paired py sas`, but its conclusion
  never mentions `sas`. A4 is about the port alone. It costs nothing, because T0 gives a paired
  `sas` for every `py` with `PyLinks`. A4 is the only port-only contract with it.
- **C4.** `thm:train_run_01_fit_frame_C4` is restated and proved; its negation is gone. It keeps
  `hpre : train_run_01_fit_frame_precond`, is a root, and nothing discharges that condition. B1
  allows this; it is not part of the claim.

### 0.4 Boundary text: PyLinks clause 14 in B4.1

The working copy of `informal-spec.md` now names clauses 6, 6b and 14 in B4.1 (14: the final fit's
first name is `Intercept`, C-k). That settles what the earlier audit asked. The edit is uncommitted.

### 0.5 Contract count: 30 listed, 33 reported

The audit's counts line says 33 contracts, but its own list (E1-E11, F1-F6, G1-G4, A1-A4, T0-T2, P0,
R) adds up to 30, and 30 matches the theorem count: 76 `thm:` items are 30 contracts and 46 kept
v2.3 helpers (75 earlier: 29 and 46). **This report says 30.** Do not quote 33 until the lead has
reconciled it.

### 0.6 Other audit findings (none is a failed contract)

- **Conditions kept on helpers (allowed by B1).** C4 and 29 other kept step or helper lemmas carry
  `hpre`, `wf_` or domain hypotheses and are roots of `get_graph`: S7a, S9a, S10a, S13 (six `wf_`
  hypotheses plus `hpre`), S25a, S31, C3, S16a, S16b, S20a, S22b, S2a, S2b, S3a, H13, H1 (`eq`,
  `ge`, `gt`), H2, H11, H7, H5, H4, H9 (`max`, `mean`, `min`), `lem:train_run_04_score_train_S7_nofit`
  and `lem:train_run_10_score_valid_S9_nofit`. No contract's proof uses them. They are not proved
  contracts and must not be counted as such. Spec section 7 lists the `wf_` domains as withdrawn,
  yet `wf_` hypotheses remain on S7a, S7b, S8b, S10b, S13, S25a, S25b and the `S7_nofit` lemma, and
  the 28 `def:wf_*` items stay in the blueprint.
- **Three spellings of the no-fit training score table.** `PyLinks` 7b and A4 put the risk frame in
  the free places of steps 12 and 14. G4 and R put empty tables and none. All three use the empty
  `StepwiseResult`. They agree on a one-outcome table by `PyLinks` 6, and E5 shows the free places
  do not affect the result. No item states that the three forms are equal. Cosmetic.
- **Examples (section 2b).** Every example comes as a fitted and a no-model half, all proved. The
  fitted halves show the fit returning a model. None states outright that the training part has
  both outcomes, as section 2b asks. That follows from `PyLinks` 6 and `logistic_no_fit`. Low
  severity.
- **Stale comments in the blueprint** (changing them would clear consumers, so leave them). In
  `def:fe_run_06_split_precond`: the "Not excluded ... NaN row_id" comment predates
  `py_split_ids_finite` and `py_split_fits`. In `thm:T2`: "wording not yet fixed by E4's reviewer";
  E4 no longer uses feature shape, so no contract uses that wording. In `_kept`, `_inv_sas`,
  `_solve_sas`: the "OPEN" comments now mean B4.2.
- **Stale records in the spec working copy** (text only, no blueprint change). (a) Section 4a's
  paragraph still says "for `total_good_bad` the lemma states the second clause only", and the
  table cell for `total_good_bad` says both "Both clauses proved" and "the lemma is stated for the
  second clause, and the first is reported". `lem:sas_cov_total_good_bad` states and proves both.
  (b) Section 9 still lists "raw files of 10^8 rows or more (ruling G56)" as a limit. Under B3 it
  is a clause of valid input (B2). (c) The R row is a separate table after the E table. (d) Section 2b's
  "feature shape (E4)" is stale. (e) Section 5 P0 text is the old SAS half (0.3).
- **Ledger.** `reports/defects-ledger.md` is untracked and lists P52 (NaN row id) and S19 as open.
  P52 can close with 0.2. S19 (P0 SAS half, F1/F2/E7 one-directional, the count) is answered by 0.3
  and 0.5 and needs the owner's reading.
- **Trust layers.** `open_blueprint` reports every trust layer off for `5365851c`: the Lean written
  for code is accepted once it compiles, neither judged nor fuzzed against the source (decision D7).
  That the port's Lean (`def:*_run_*`, `pyPipeline`, `PyLinks`, `Paired`) matches the Python rests
  on the recorded reviews. Say this in public, with the B4 trusted base: the fit, the numpy
  routines, the CSV reading and writing, and `Float` taken as the reals.
- **No block.** No hook stopped any read the audit needed. The audit wrote nothing.

## 1. The claim in plain words

On every valid input, the Python port returns, and writes the same compared files as the corrected
SAS program. Valid input is `CreditRisk.InputOK` (requirements section 3, Draft 10). Each contract
is stated on what the pipeline reaches from a valid input, not on tables or argument combinations
the code never builds. No contract carries a precondition, a `wf_` domain, a limit or a "not
covered" clause of its own.

The contracts: the port returns on valid input (R); equality on the interface (E1 to E11, with E4 on
every model of the 36 candidates); existence and equality of files outside it (F1 to F6, F1, F2 and
E7 in the stronger form); faithfulness of the assembly (A1 to A4); coverage of the port's stage
preconditions (G1 to G4); predict on a run without a model (P0, SAS half taken from
`def:model_coefficients_written`); and T0, T1, T2. The 26 requirements proved of the SAS program
are taken to hold of the port by inference from the equality (owner, 2026-11-18). They are not
proved again.

On NaN: on valid input the row ids are present and the split file fits. NaN is outside the
real-number model (B4.4); the claim does not say it is proved impossible.

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
  outcomes returns a model, the same on both sides, with the facts of `PyLinks` 6 and 6b, and
  clause 14 (`Intercept` first, named in B4.1 since 2026-11-20, 0.4). (2) numpy `solve`, `inv`, `matmul`,
  `matvec` behave as `PyLinks` 13 says. On what a valid run reaches, `solve` and `inv` raise no
  error, because selection leaves out every linearly dependent variable (X28). (3) CSV readers and
  writers are parameters, described by `PyLinks` from observed runs. A file not written and a
  header-only file both give the table with no row. (4) `Float` is the arithmetic of both programs,
  with the recorded last-bit difference of `exp` and the fuel 4096 of `_randbelow`.
- **B5. Outputs.** Exactly the files the parity judge compares. Printed reports, `printed_*`
  files, coefficient and stepwise printouts and printed formats are outside the claim.
- **B6. During a run** only a finding that would change B1 to B5 goes to the owner.

Also in force: `PyLinks` and `Paired` (corrections C-a to C-m). Judging is off on `5365851c`
(decision D7), so that each Lean statement says what its text says rests on the recorded reviews.

**B7, amendment 3 (owner, 2026-11-20): the training split.** Added after the fidelity review's
finding F2 (`port-lean-fidelity-2026-11-20.md`, w29). The training split is a shared random draw:
SAS draws it with `PROC SURVEYSELECT` (its own generator, seed 42); the port reads that draw from
a file and otherwise draws with Python's `random`. The two generators do not draw the same ids, so
the claim is equality given that both sides train on the same ids. That is `Paired` clause 2,
which stays as it is; no item and no proof changed. The pairing holds on the real 150,000-row file
(`inputs/split_ids.csv` is SAS's own draw) and is not claimed elsewhere. B7 is part of the
boundary, like the trusted base B4, and public text must say it: "on every valid input, given both
sides train on the same ids". With it, the NaN wording of 0.2 and section 1 ("the split file fits")
is to be read as reworded in the spec note of 2026-11-20 (finding F3): the row ids are present
(`lem:py_split_ids_finite`, `InputOK`), and the port's own draw is reached on any input other than
the real file, so it is not dead code.

### The former narrowings and B3

The audit confirms that G1 to G4 and the 4a lemmas cover the unit preconditions. It does not list,
narrowing by narrowing, the item that proves each. The table gives what the audit and the records
show. Where no single item is named, the report says so. It does not guess.

| Former narrowing | Proved by | State |
|---|---|---|
| `classification_table` clause 7 | G2, G4 (B3) | covered; the audit names no separate item |
| `hosmer_lemeshow` String Series | G4 (B3) | covered; the audit names no separate item |
| train step 06 `0 <= idx` (`train_run_06_coefficients_odds_precond`) | G2, resting on the Intercept-first clause (`PyLinks` 14, C-k) | covered; the audit names no separate item |
| train step 06 `exp` NaN and infinity clauses | G2 (B3) | covered; the audit names no separate item |
| `split_ids != []` of `fe_run_06_split_precond` | G1 and `lem:py_split_ids_rowids`, `lem:py_split_fits` (C-k) | covered; both are proved `lem:` items |
| non-empty training table of `run_py_precond` | G2, G4 | covered, same reading |
| fewer than 10^8 rows | `lem:sas_cov_total_good_bad`, both clauses | proved |
| no NaN row id in `fe_run_06_split_precond` | `lem:py_split_fits` (file branch, no draw) and `lem:py_split_ids_rowids`; `lem:py_split_ids_finite` adds only that every id is present | **proved unreachable on valid input; see 0.2 for what the proof does and does not say** |

Several unit preconditions (`fe_run_01/02/03/06_split_precond` and others) keep comments marked
"narrowing", such as `0 < height` and Float64-only columns. They sit on unit items, not on
contracts. G1 to G4 prove them on what a valid run passes, so they are within B3.

## 3. Contracts and their states

Read from the port blueprint `5365851c` by the audit of 2026-11-20 (read only, Logos MCP Staging).
Totals are in section 0.1.

| Contract | State |
|---|---|
| R (`thm:R_port_returns`, new): the port returns on every valid input | proved |
| E1 to E11 (E4 on every model of the 36 candidates; E7 in the new form) | proved |
| F1, F2 (existence and equality), F3 to F6 | proved |
| G1 to G4 | proved |
| A1 to A4 | proved (A4 carries an unused `Paired`, 0.3) |
| T0, T1, T2 | proved |
| P0 (`thm:P0_predict_no_model`) | proved; SAS half from `def:model_coefficients_written` (0.3) |
| `thm:train_run_01_fit_frame_C4` | proved, restated: the mask is true exactly when the 36 candidates and `default_flag` are non-null; keeps `hpre`, not part of the claim |
| example items (37; witnesses that each contract's hypotheses can be met) | proved; inhabitation shown in every case |

30 contracts, 46 kept helpers (some with conditions, 0.6). Contracts run summary: resubmitted
`thm:E6_score_test` and `thm:G3_predict_coverage`; needed proving: none. There was no `sorry` or
axiom scan (Logos refuses both; the check is `TheoremProved`).

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
- **C-k (Intercept-first clause, split lemmas).** Owner's decisions "G2 fit": "Add the clause", and
  "S6 lemmas": "Restate for the pipeline's split". `PyLinks` gains clause 14: the final fit's first
  name is `Intercept`, on every argument. New split lemmas `lem:py_split_ids_rowids` and
  `lem:py_split_fits`: the ids passed to `py.split` have the feature frame's present row ids, and
  the table the split returns fits, so the unit takes the file branch with no drawing. Both are
  proved.
- **C-l.** B4.2 made formal with no change: no precondition asks `solve` or `inv` to return, the
  Lean routines are total functions of `def:PyParams`, and `PyLinks` needs no clause. G2 now says
  "no limit of its own" and rests on B4.2 and C-l.
- **C-m.** `def:train_run_08_ctable_precond`: null clauses of train.py :482 and :486 guarded. The
  four items the write cleared were restored unchanged.
- **2026-11-20.** `lem:py_split_ids_finite` proved (0.2). F1, F2 and E7 restated as existence and
  equality; contract R added and proved; P0's SAS half taken from the new SAS unit
  `def:model_coefficients_written` (0.3); clause 14 named in B4.1. The G2 LinAlgError "Not covered"
  sentence and the C4 negation are struck through in the spec and `report.md` (uncommitted).

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
- Owner, 2026-11-20: P0's SAS half is to come from the SAS Lean (result: `def:model_coefficients_written`).
- Lead, 2026-11-20 (B1): F1, F2, E7 restated to existence and equality; contract R added; E4 kept on
  every model of the 36 candidates.


## 6. The Logos 503 outage during the run

**No record of the outage of this run is in the files read.** A search of `migration/` finds a
503 note only for an earlier round (`legacy-meets-requirements/reports/round-6-2026-11-16.md`: 503
errors on about one call in ten, retries went through). On the compile queue,
`migration/audit/logos-requests-2026-11-19.md` section 6 measures that compiling calls queue on
the server (about four at a time). The audits of 2026-11-19 and 2026-11-20 read the blueprint
without trouble and report every item proved, so the outage left no item unproved and does not
change what is claimed. How long it lasted and which calls it cost are not known to the writer. The
lead should state them.

## 7. Audit results

Read-only audits of `5365851c`, 2026-11-19 and 2026-11-20. Gates 1 to 4 pass.

1. Every contract has an item and is `TheoremProved`. Each Lean statement was compared with the spec
   text. Notes: A4's unused `Paired`; three spellings of the no-fit score table; P0's SAS half now
   from `def:model_coefficients_written`, with the validation flag on F1.
2. All 170 proof items (76 `thm:`, 94 `lem:`) are `TheoremProved`, with 37 examples.
3. No `zz_` item, no `neg:` item, nothing flagged false, nothing left to state or prove. The counter
   says 369 of 370 formalized; every item read is formalized (0.1).
4. C4 is restated and proved; its negation is gone; it keeps `hpre`.

Contracts run summary: resubmitted `thm:E6_score_test` and `thm:G3_predict_coverage`; needed proving: none.

## 8. What the owner must still do

1. Sign off. `verification_approved` on `5365851c` reads true in `get_status`; this report does not set
   it, and the sign-off is the owner's.
2. Accept the P0 reading of 0.3: SAS half from `def:model_coefficients_written`, validation flag on
   F1 (equal to F2 by `Paired` 5), and its two stated conditions.
3. Have the spec working copy fixed (0.6): section 5 P0 text, section 4a `total_good_bad`, section 9
   G56 limit, the R row, the stale "feature shape" text. These are text edits only.
4. Have the Logos side explain the counter (369 of 370 formalized) and the lead reconcile the
   contract count (30 listed, 33 reported) before any number is quoted.
5. Choose the public wording of the NaN row id (0.2) and say in public that trust layers are off
   (0.6).
6. Ask the lead for the missing records: the PSI one-row text fix, any other answer of 2026-11-19,
   and the 503 outage (how long, which calls).
7. Settle the ledger entries P52 and S19, then commit.
8. Push. Branch `initial` has commits from 2026-11-18 and 2026-11-19 not on origin (89c15e6 was the
   last push on record) and an uncommitted working tree (`informal-spec.md`, `reports/report.md`,
   `reports/defects-ledger.md`, `legacy-to-lean/manifest.tsv`, the update note of 2026-11-20, and
   earlier files). The owner decides what is committed and pushed. This role made no git call.

**Addendum, 2026-11-20, after fidelity pass w30 (records only; this supersedes the "every contract
proved" and `verification_approved: true` statements of sections 0.1, 7 and 8 until re-checked).**
Details are in `reports/port-lean-fidelity-2026-11-20.md`, section "Fidelity pass, second attempt
(w30)". *Tests:* w30 compared 0 Lean cases with Python and wrote no receipt. An evaluation carrier,
`def:zz_carrier_fid_1`, was added and `eval_decl` returned through it on every target unit, but the
blueprint was cleared under the carrier step and no comparison followed; 17 of 100 code units and
the glue's Lean remain without a unit-level receipt on their current Lean, and `def:run`'s stored
Python text is still the version before `4a757fb`. *F1:* `def:PyLinks` clause 10 now reads
`∀ n : Nat, n < 10 ^ 8 → parse_float (sas_best (some n) 8) = n ∧ sas_best (some n) 8 ≠ ""`
(the port's `sas_best` switches to E-notation above 8 digits); `lem:metrics_ks_table`'s `hcount`
is bounded by `n ≤ V.length` (a reviewer choice: no added hypothesis), and E8, E9 and G4 discharge
the bound from `InputOK` (G56) through new in-file helpers, with edges E8 → `lem:sas_reached_feature_shape`,
E8 → `lem:sas_split_input_ids`, G4 → `lem:sas_split_input_ids` added. No contract got a new
hypothesis. *Re-proofs:* the restatement cleared 62 statements and proofs; all 30 contracts are
again `TheoremProved` by state, but at the audit 18 of them (E1-E3, E5-E11, F2-F4, F6, G2, G4, P0,
R) rest on `thm:fe_run_06_split_S6a`, which is only `TheoremStated`, and seven `ex_` lemmas are
unproved, so the claim does not hold until S6a and those lemmas are proved and the states re-read.
*Amendment 3 (B7)* is recorded in section 2; F3 and F4 are fixed in the spec and in
`definitions-v3.md`. *Audit (`ok: false`):* 372 items, 371 formalized, `verification_approved`
false; both `zz_carrier_fid_*` items are on the blueprint with no consumer and must be removed;
`definitions-v3.md:215`, `:239`, its 2026-11-20 top note and the `PyLinks` Lean header comment
are stale against the restated clause 10; T2 assumes `SasLinks`, not `PyLinks`/`Paired`, so the
public sentence on hypotheses must allow for it. The owner's sign-off (section 8, item 1) waits on
these.

**Addendum, 2026-11-20, after fidelity pass w31 (third attempt and close; records only).** Details
are in `reports/port-lean-fidelity-2026-11-20.md`, section "Fidelity pass, third attempt and close
(w31)". *Re-proofs:* `thm:fe_run_06_split_S6a` and the seven `ex_` lemmas were resubmitted from
their stored drafts unchanged and accepted with 0 errors, and `def:zz_carrier_fid_1` is formalized
again; no statement, Lean or hypothesis changed. *Audit (`ok: true`):* 372 items, 372 formalized
(203 `DefinitionFormalized`, 169 `TheoremProved`, read item by item), `verification_approved`
true, all 30 contracts `TheoremProved` with no unproved item in their closure inside 5365851c; the
SAS-side blueprints 3f5df696 and 006ff04c were not checked. So the "every contract proved"
statement of sections 0.1, 7 and 8 holds again for this blueprint. *Tests:* through
`def:zz_carrier_fid_2`, 46,359 cases compared against the port at HEAD `4a757fb`, including every
unit left without a receipt in w30 and, for the first time, the glue end to end (4,342 cases, all
bit-exact). 557 differences: 96 wholly explained by RULEBOOK section 6 limits (last bit of exp,
signed zeros, running sum from -0.0), plus 3 such cases in `train_run_03`, and **461 unexplained,
all in `def:train_run_01_fit_frame`**: on the no-fit case its m2ll0 is 0.0 where the port gives NaN
(the Lean comment calls it a "placeholder, lead's decision"; no RULEBOOK rule covers it; nothing was
fixed). Full-size real data is still reached only for `train_run_11` and `metrics_run_05`; other
units ran on real windows or slices. *Records:* C-n is now recorded in `definitions-v3.md` and
`informal-spec.md`. *Still open for sign-off:* the `train_run_01` finding; the audit's finding that
the no-model training score table is spelled three ways (PyLinks 7b / A4, G4 / R, E5 / A2 / F3) with
no item proving them equal; removal or disclosure of both `zz_carrier_fid_*` items; the stale
`def:PyLinks` header comment and `def:run` stored text; trust layers off (fidelity rests on reviews
and the diffeval receipts); boundary B1-B7, with B7 conditioning the claim on shared split ids; the
`t16_run` work files regenerated as a side effect; and committing the working tree.

**Addendum, 2026-11-20, w31 restart (records only).** The w31 workflow was restarted after an
interruption. The re-proofs, tests and records returned the same results as in the addendum above.
The audit ran again (read-only, `ok: true`) and is recorded verbatim in
`reports/port-lean-fidelity-2026-11-20.md`, section "w31 restart: second audit". It confirms 372 of
372 items formalized and all 30 contracts `TheoremProved`, and this time also read the SAS-side
blueprints as complete (SAS spec 3f5df696 151/151, requirements 006ff04c 60/60, foundation 02011d57
17/17); T2's closure rests on whole-blueprint completeness, not an item-by-item trace. New findings
for a public text: T2 assumes `SasLinks`, `InputOK`, `CreditRisk.Fitted` and `hFt`, and A3 assumes
nothing, which the summary sentence and exception list of informal-spec section 7 do not say; T2's
Lean comment still cites the superseded "Feature shape of E4" wording; and both `zz_carrier_fid_*`
items are still present although brief-prover.md says to remove every `zz_` item. On the no-model
training score table the two audits disagree: the first counts three spellings with no item proving
them equal, the second counts two and takes E5 as showing they are the same table. Both are on
record; the point stays open for the lead. The rest of the open list in the addendum above stands.
