# The equality stage: brief for provers 1 to 10 (from 2026-11-17)

Coordinator: `prover-0`. Auditor: `prover-11` (proves nothing; takes the snapshot before proving).
The lead decides what goes to the owner. This file holds no Lean.

## What is being shown

The Python port produces what the corrected SAS program produces, on every valid input, for
parameters related as `Paired` says. Text of record: `../informal-spec.md` (version 3) and
`../definitions-v3.md`. Read both in full before your first item. Background, if you need it:
`../plan-after-verification.md`.

Port blueprint (you work here): `5365851c-5549-44b7-9207-4bd4c422031d`. Never write to
`b41b22d4-...` (a stale copy). The SAS blueprint `3f5df696-7c80-45cc-809f-b2881714663d` and the
requirements blueprint `006ff04c-d34c-4a9c-b230-ccd725b1be6f` are read only; their declarations
are in scope through the profile.

## Rules

1. `Logos MCP Staging` connector only. Open blueprints by id. All Lean lives on the blueprint:
   never save Lean to a local file, not even as scratch.
2. One owner per item, assigned by the coordinator. Do not take an item that is not yours. If you
   finish, tell the coordinator; you will get the next one.
3. Never change a definition or any item that is not assigned to you. Never reword a contract:
   the item's informal text is the text of the specification; the Lean says exactly that, with no
   extra hypothesis and no weaker conclusion. If a text cannot be stated as written, stop and
   tell the coordinator.
4. A disproof is a good result; a weakened proof is worthless. No `axiom`, `sorry`,
   `native_decide`, `unsafe` in an accepted proof.
5. Every statement is checked against its text by the reviewer named in the table, who did not
   write it, **before** its proof is started. Trust layers are off on this blueprint: the review
   is the only check that Lean and text agree. The reviewer answers "agrees" or lists each
   difference.
6. Helper lemmas private to one proof go in its proof file. A lemma two provers need is an item
   (`lem:`), asked of the coordinator, who assigns it.
7. A disproof: negate the item, prove the negation with a concrete valid input, put the input and
   one sentence in the negation's text, and tell the coordinator at once. It is checked by a
   prover who neither wrote it nor supplied its input, and its text is saved under this folder
   before anything else is touched. You do not message the coding agents or the translators.
8. Do not depend on `def:zz_carrier_*` items. Remove any `zz_` item you add before you finish.
9. Do not wait idle on a compile: draft the next item meanwhile. Keep proofs in small pieces
   (drafts on the server: `write_solution_draft`, `edit_solution_draft`, `submit_solution`).
10. Report to the coordinator by message: per item, the result (proved; disproved with the
    input; statement reviewed; stuck, with the goal), nothing else.

## Phase 0: the kept theorems (now)

43 theorems still read "proved" from before the profile was refreshed. Each stored proof must be
compiled against the present profile. For each of yours: read the accepted proof
(`get_items` with `proof_lean`), and resubmit **that same text, unchanged**, with
`write_solution` (or, if a stored draft exists, `read_scratch` then `submit_solution`). Do not
change the statement. Result per item: accepted, or the compile error. **If it does not compile,
do not repair it: report the error first.** A kept theorem that no longer compiles is a finding.

**Large proofs (accepted proof over the 30 KB response limit, no stored draft on `5365851c`).**
The stale blueprint `b41b22d4-720d-4290-b593-39ceab961986` still holds the stored solution
drafts, readable in line ranges. It is read only: nothing is ever written to that id. Procedure
(lead's instruction, 2026-11-17):
1. On `b41b22d4`: confirm the item is in state proved and its `statement_lean` equals the one on
   `5365851c`. If it differs, stop and report.
2. `read_scratch` (part "solution") on `b41b22d4` in line ranges; note its revision and
   `total_lines`.
3. On `5365851c`: build the draft with `write_solution_draft` then `edit_solution_draft`
   (append), each chunk passed exactly as read, never retyped.
4. `read_scratch` the new draft back in ranges; check `total_lines` and each range against the
   old one.
5. `submit_solution`. If it does not compile, stop and report; no repair.
Report for each such item: "proof text from the stored draft of the same item on b41b22d4,
revision ..., N lines; accepted on 5365851c at revision ...". Identity with the accepted proof
on `5365851c` cannot be shown for this class and is not claimed. An item with no draft on either
id: report it; it goes to the owner.

The linter (`lint`) fails on every item with "Unknown constant Pl.Json.rec_1": a tool limit, not
a result; do not use it as a check.

Four items were cleared when the train stage changed and are to be restated and decided again:
`thm:train_run_04_score_train_S7a`, `_S7b`, `thm:train_run_14_final_and_summary_S13`,
`thm:train_run_01_fit_frame_C4`. Their texts are on the items (contracts S7, S13, C4 of
`../informal-spec-v2.3.md`). Read `migration/port-to-lean/update-2026-11-17.md` for what changed
in the units. Restate exactly the text against the present units; if the text no longer fits the
unit, report before stating. C4 was a recorded difference (its negation item is gone): decide it
again.

| Prover | Phase 0 items |
|---|---|
| prover-1 | `lt_H1_lt`, `le_H1_le`, `gt_H1_gt`, `ge_H1_ge`, `eq_H1_eq` |
| prover-2 | `flag_H2`, `div_H3`, `sas_sum_H4`, `sas_min_H5_min`, `sas_max_H5_max` |
| prover-3 | `sas_log_H6`, `sas_exp_H7`, `sas_round_H8`, `sql_sum_H9_sum`, `sql_min_H9_min` |
| prover-4 | `sql_mean_H9_mean`, `sql_max_H9_max`, `merge_one_to_one_H10`, `proc_rank_groups_H11`, `confusion_metrics_H13` |
| prover-5 | `fe_run_02_income_medians_S2a`, `_S2b`, `fe_run_03_cleaned_S3a`, `_S3b` |
| prover-6 | `fe_run_06_split_S6a`, `_S6b`, `predict_run_03_cleaned_S25a`, `_S25b` |
| prover-7 | `predict_run_03_cleaned_S31`, `predict_run_06_score_S28`, `predict_run_06_score_C3`, `metrics_run_03_thresholds_S16a`, `_S16b` |
| prover-8 | `metrics_run_07_calibration_S20a`, `_S20b`, `metrics_run_08_validation_summary_S21b`, `metrics_run_09_model_performance_S22b`; restate and decide `train_run_14_final_and_summary_S13` |
| (was prover-9; owners set by the lead 2026-11-17) | `train_run_10_score_valid_S9a`, `_S9b`, `train_run_11_confusion_valid_S10a`: prover-3. `train_run_09_confusion_train_S8a`, `_S8b`, `train_run_11_confusion_valid_S10b`: prover-7 and its helpers (live drafts found; the lead, 2026-11-17: a live writer keeps the item; provers 4, 5, 6 are free of them). |
| prover-10 | restate and decide `train_run_04_score_train_S7a`, `_S7b`, `train_run_01_fit_frame_C4` |

All ids carry the prefix `thm:`. Reviewer of a restated statement: prover-9 for prover-10's,
prover-10 for prover-8's.

**Proof before review (lead, 2026-11-17).** For the phase 1 coverage lemmas and the small
supporting lemmas of phase 2 only, a proof may be built and submitted while the statement
review is pending: if the review asks a change, the item is restated and proved again, and the
order is reported for the record. Strict as before, reviewed before any proof or any use: the
three definitions and two records, T0, and every contract of phase 3. Reviewers answer review
requests before continuing their own proofs.

**Seams when appending a draft.** Found by prover-5: an append with `edit_solution_draft` drops
a leading blank line of the chunk and adds no line break after a chunk that ends without one
(two lines are joined). After every append read the seam back and compare it and the line count
with the old draft; repair whitespace only, and report each repair.

**Restating an old `thm:` item replaces its text.** `write_statement` on an existing `thm:` item
replaces its `statement_text` (the contract) with a generated summary. Remedy, for every old
item restated: save `statement_text` first; `write_statement`; then `edit_text` with the saved
text (this keeps the Lean); read `statement_text` back and compare. New items made with
`add_item` keep their text, but read it back after `write_statement` all the same.

## Phase 1: coverage of the SAS unit preconditions (start when your phase 0 items are reported)

Section 4a of the specification: one lemma per unit, `lem:sas_cov_<unit>`, with the text given
there. Add the item (`add_item`, kind lemma, the text from section 4a with the unit's name and
the step filled in, depending on `def:` nothing of the port: the SAS names come through the
profile), state it, get it reviewed, then prove it. The shared SAS lemmas (`sas_features_some`,
`sas_feature_rows`, `sas_score_rows`, `sas_split_sat`, `sas_test_feature_rows`, ...) are in
scope and are the intended tools. A lemma that fails is a finding about the SAS verification:
report it with the input, do not patch.

| Prover | Lemmas (units) | Reviewer of the statements |
|---|---|---|
| prover-2 | `income_medians`, `income_medians_all` | prover-3 |
| prover-3 | `credit_cleaned`, `credit_imputed` | prover-4 |
| prover-4 | `credit_features`, `credit_train_validation` | prover-5 |
| prover-5 | `logit_scored_valid_temp`, `test_scored_temp` | prover-6 |
| prover-6 | `test_raw_input_check`, `test_raw_clean`, `credit_raw_input_check` | prover-7 |
| prover-7 | `test_cleaned`, `test_imputed`, `credit_raw_clean` | prover-8 |
| prover-8 | `test_features`, `test_scored` | prover-9 |
| prover-9 | `test_predictions`, `total_good_bad` | prover-10 |
| prover-10 | `train_bins` (training and validation use), `decile_data` | prover-2 |

## Phase 2: the three definitions (prover-1 states, prover-2 reviews)

prover-1, after its phase 0 items: `def:pyPipeline`, `def:PyLinks`, `def:Paired`, from
`../definitions-v3.md`, in that order. prover-2 reviews (this has priority over its phase 1
lemmas): `pyPipeline` as pure wiring against `sasPipeline` field by field and against the four
stage functions; `PyLinks` clause by clause against rules H1 to H14 and G29, G30 of
`migration/port-to-lean/RULEBOOK.md` section 2.8, in both directions (too strong makes proofs
unsound; too loose lets a disproof rest on something the port never does); `Paired` against the
notes "for the reviewer" in the definitions file. Nothing depends on these until both say so.

For whoever gives `pow2` a value in a witness: Python's `x ** 2` differs from `x * x` in the last
place on about 0.13 % of floats (RULEBOOK section 6): take Python's.

## Phases 3 to 5 (assigned later)

3. The contracts E1 to E11, the coverage contract of each stage, the per-file contracts, in
   groups A to D and F; then the snapshot by prover-11, before any proving.
4. Prove or disprove: a prover and a refuter on each contract, hunters on edge inputs.
5. The 26 transport theorems; the audit.
