# Equality stage, round 1 (started 2026-11-17)

Port blueprint `5365851c-5549-44b7-9207-4bd4c422031d`. Coordinator prover-0; provers 1 to 10;
auditor prover-11. Specification: `../informal-spec.md` version 3 and `../definitions-v3.md`.
Brief and assignment tables: `../rounds/equality-stage.md`. This file holds no Lean.

## State at the start

- `get_status`: 235 items, 231 formalised; to write: `thm:train_run_01_fit_frame_C4`,
  `thm:train_run_04_score_train_S7a`, `_S7b`, `thm:train_run_14_final_and_summary_S13` (cleared
  by the change of the train stage); no proof to write; nothing flagged.
- Profile check repeated: pass (`plan-after-verification.md` section 0.2; `sasPipeline`,
  `SasLinks`, `TrainOK` re-read on 2026-11-17, unchanged).
- 43 kept theorems read "proved" from before the profile refresh.

## Phase 0: the kept theorems

Each stored proof resubmitted unchanged; the four cleared items restated and decided.
Assignment: the phase 0 table of the brief.

| Item | Owner | Result |
|---|---|---|
| (filled as reports come in) | | |

## Phase 1: coverage of the SAS unit preconditions

20 lemmas `lem:sas_cov_<unit>`. Assignment: the phase 1 table of the brief.

| Lemma | Owner | Statement reviewed by | Result |
|---|---|---|---|

## Phase 2: the three definitions

Stated by prover-1, reviewed by prover-2.

## Tool limits met

- An accepted proof over 30 KB cannot be read through the connector (`get_items` answers
  `response_too_large`; no stored draft on `5365851c`). Route, by the lead's instruction: the
  stored draft of the same item on the stale blueprint `b41b22d4` (read only), rebuilt on
  `5365851c` chunk by chunk as read, read back, compared, submitted. This class is kept apart
  below: identity with the accepted proof on `5365851c` is not shown and not claimed; the
  server's acceptance against the present profile is the evidence. Known so far: S2a, S2b, S8a,
  S8b, S10b, S20b, S21b, S22b.
- `lint` fails on every item with "Unknown constant Pl.Json.rec_1": no use as a recompile check.
- prover-9's session refuses `write_solution` on an existing item (permission check, "Destructive
  or Unwanted Actions"). Not worked round, not moved to another prover. Its six items (S8a, S8b,
  S9a, S9b, S10a, S10b) wait for the owner's answer.

## Contract texts changed with the lead's approval

- **S13** (`thm:train_run_14_final_and_summary_S13`), 2026-11-17. The port's step 14 has a new
  last argument `roc_valid_created` (from step 13); when false its `model_summary.csv` is the
  table with no row, while step 13 still returns a one-row validation ROC frame. Reading 1 (the
  old text for every value of the Boolean) is false, but only by feeding the SAS unit a ROC table
  the SAS never has. Reading 2 (the Boolean true only) adds a hypothesis and leaves the new
  branch unclaimed. Approved text (reading 3): "Contract S13, version 3 (step lemma): as S13 of
  version 2.3, for every value of roc_valid_created; in the model_summary.csv clause the SAS unit
  is given, for its validation ROC table, the table of the port's roc_valid frame when
  roc_valid_created is true and the table with no row when it is false." Conditions: contract F4
  must not take the Boolean as a free value, and its reviewer checks that the Boolean there is
  step 13's own output; a training-side Boolean, if any, gets its own wording from the lead.

## Findings about the SAS side (precondition stricter than the links, unit independent of it)

To be listed in the final report. Nothing is changed on the SAS blueprint.
1. `total_good_bad`: fewer than 10^8 rows (ruling G56, a stated limit).
2. `roc_valid` (before SAS round 6): both classes; since round 6 the unit returns no row instead.
3. `credit_raw_clean` and `test_raw_clean`, found 2026-11-17 by prover-7 and prover-6: the
   precondition asks each text of `MonthlyIncome` and `NumberOfDependents` to have at most 32
   characters as it is; `SasLinks` (1) and (2) bound the trimmed length only. Witness: a
   delivered cell of 33 blanks and "5". The Lean unit does not read the length. Behind the
   clause: the real BEST32. informat reads the first 32 characters of the unstripped value,
   while `Sas.inputBest` trims first; the real PROC IMPORT strips blanks, which the links do not
   say. No `sas_Q` theorem is affected. Lead's ruling: the two coverage lemmas are stated for the
   clauses that follow; no formal disproof now; no equality contract may use the full
   precondition of these units.

### Limit candidate for the owner (SAS-side claim, same kind as G55 to G58)

Found by prover-6; to be put to the owner by the lead with the final report. Nothing is changed
on the SAS blueprint or in `SasLinks` now.
- Input: a delivered text of 31 blanks then "55" (33 characters; trimmed length 2, admitted by
  link (1)/(2)).
- The Lean: `Sas.inputBest` trims first and reads 55.
- The real BEST32. informat reads the first 32 characters of the unstripped value: 31 blanks
  and "5", so 5.
- Why no real file reaches it: the real PROC IMPORT strips blanks (SAS round 4 notes, defect
  D1); `SasLinks` does not say so.
- Proposed limit: "delivered texts carry no blank at either end; not formal". Alternative:
  tighten link (1) and (2).
- Port side: whether `PyLinks`, the port's read-back or its reader behave the same on a padded
  text is being checked by prover-1 with the statement of `def:PyLinks`; a difference there
  would be one F3/F4 must exclude.

- Port side, checked by prover-1 (read, not evaluated): (a) `PyLinks` 1 to 4 speak only of
  number texts with no blank and of the missing forms, so the port links admit no padded
  number text; (b) the Python reader cuts to 32 characters and then trims
  (`port/credit_risk/sas_compat.py:241`), as the real informat; in the port Lean
  `input_best32` is a parameter with no body, applied to the unstripped column; (c) a padded
  text can be delivered on the SAS side only; within 32 characters both orders read the same
  number, beyond 32 the port links admit nothing. So under `PyLinks` and `Paired` no input
  makes the two Leans read different numbers, and F3/F4 need no exclusion on this account. The
  limit stays one of the SAS-side claim (SAS Lean against the real SAS).

### Results received (to be merged into the phase tables at the end of each phase)

- Phase 0, typed resubmissions by prover-6 ("resubmitted from the accepted text, identity not
  shown, accepted"): S6a 451e6a4e80114117b2b99cdf961eaa92, S6b 1188042d9a804e0399ce369cf716dd57,
  S25a f3491567840e42ff8baf59fe5f1c2166, S25b 6833c26e36ff4331bf6ef79b14e7c7fe.
- Phase 0, texts of S7a, S7b, C4 restored by prover-10 with `edit_text`: S7b first, state and
  Lean unchanged, nothing cleared downstream (S7a, which depends on S7b, kept its Lean); then
  S7a and C4. Not tested: whether a later `write_statement` replaces the text again (assume so).
- Phase 1: `lem:sas_cov_test_predictions` proved by prover-9, revision
  b173ba882e5346f9848b0b80e73c74b8, reviewed "agrees" by prover-10 before the proof.
  `lem:sas_cov_total_good_bad` (second clause only) proved by prover-9, revision
  385bdc92f3ab4f229452633ac08faade, reviewed "agrees" by prover-10; uses `lem:sas_feature_rows`,
  `lem:sas_score_rows`, links (3) and `TrainOK`; no carrier.
- Phase 1 reviews "agrees": prover-9 on prover-8's test_features and test_scored; prover-6 on
  prover-5's logit_scored_valid_temp and test_scored_temp (owed: the second form under
  PyLinks 8, after `def:PyLinks`).
- Phase 2, prover-1's points before stating (sent to the lead 2026-11-17 for approval of the
  wording): PyLinks 5 unsatisfiable as drafted (count only for present, pairwise distinct ids);
  Paired 2 only for tables with present, pairwise distinct row_id (SasLinks (5) then holds for
  the `sas` T0 exhibits, not for every paired one); Paired 7 needs `today` beside the 17
  parameters. `pyPipeline.score` calls steps 12 and 14 with fillers in idle slots, with a lemma
  of independence.

- Sas-name sweep (prover-3, read only): statements of the kept theorems, S7a, S7b, C4 and the
  17 coverage lemmas then present. Only `Sas.round` (H8) failed to resolve. 45 names through
  `check_decl` (23 of the `Sas` namespace, 22 SAS units); 31 more occur only in statements
  accepted by `write_statement` on 2026-11-17. Cautions: a name can resolve with a changed
  signature, so only the phase 0 resubmission settles a kept item; names inside proofs were not
  swept.
- S7a, S7b, C4: prover-9's review against the restored texts, on a fresh read at 05:06 CET:
  agrees, all three; its first review (against the generated summaries) is void. C4 agrees with
  its text and is false against the unit; to be negated by prover-10.
- Phase 1: `lem:sas_cov_income_medians` and `lem:sas_cov_income_medians_all` stated and proved
  by prover-2 (only link (1) and `TrainOK` used); proved before prover-3's review answered,
  allowed on condition that a change asked by the review means restating and proving again.
- Phase 2: the server takes one declaration per item, so two record items are added beyond the
  three definitions, allowed by the coordinator and told to the lead: `def:PyParams`,
  `def:SasParams` (author prover-1, reviewer prover-9).
- Text comparison of every kept `thm:` item across the two ids: prover-9 (moved from prover-3).

- Phase 0, typed resubmissions by prover-2 (flag_H2, div_H3, sas_sum_H4, sas_min_H5_min,
  sas_max_H5_max): no stored draft existed, `get_items` then `write_solution` with the text
  copied; each accepted first time; "resubmitted from the accepted text, identity not shown,
  accepted".
- Phase 1 review "agrees": prover-2 on prover-10's train_bins and decile_data (owed: the forms
  under the free read-back, after `def:PyLinks`).
- Phase 2: the lead approved C-a, C-b, C-c (entered in `definitions-v3.md`) and the two record
  items (fields only, no default, no proposition; `today` last in `def:SasParams`).

- Text comparison across the two ids (prover-9, read only, fetched about 05:08 CET): the 42
  kept `thm:` items plus S7a, S7b, C4, S13: 46 compared, all 46 identical character for
  character (string equality and SHA-256 of each text, by script over its session record).
  `thm:sas_round_H8` exists on b41b22d4 only. S13 still carried its old text (version 3 text
  not yet written by prover-8). S7a, S7b, C4 equal again to the old texts. So the text
  replacement hit only the three restated items, and `write_solution` touched no text.

- Phase 1: `lem:sas_cov_credit_cleaned` and `lem:sas_cov_credit_imputed` proved by prover-3
  (statements reviewed "agrees" by prover-4); use link (1) first clause, link (4) and the
  column-names clause of `TrainOK`; no carrier.

- Phase 1: prover-3's review of prover-2's income_medians and income_medians_all: agrees, both.
  For the audit: the review came after the proofs (rule 5's order not kept for these two; the
  lead accepted it once); no consequence, the statements agree with their texts.

- Phase 0, typed resubmissions by prover-1 ("resubmitted from the accepted text, identity not
  shown, accepted"): lt 0b0762bd135046afa6e4a6a6eb3ca25a, le 6f343f58039648d1ae35ba8bc8f8ff04,
  gt aa43428270444c1bb0d4742b99c65346, ge 661dc530d0874dad86b588954f787702,
  eq 9950f7cf075a40b1969a7bae744c2475.
- Phase 2: `lem:sas_feature_rows` gives no distinctness of `row_id`, so the lemma of C-b is
  needed: `lem:sas_split_input_ids`, stated by prover-1 under `Paired` after `def:Paired`.

- Phase 0, the restated three (prover-10; statements reviewed "agrees" by prover-9; contract
  texts read back after the proofs):
  - S7b: proved with the proof it had on b41b22d4, unchanged; accepted first time.
  - S7a: proved with the old proof and one token added (`none` for the new separation field of
    `LogisticFit`, built positionally in the witness); rests on S7b. Recorded as changed, not as
    unchanged.
  - C4: disproved, flagged false; `neg:train_run_01_fit_frame_C4_neg` proved with the old proof
    unchanged. The difference of round 2 (report.md, row C4): the mask of
    `train_run_01_fit_frame` also drops a row whose `default_flag` is missing (train.py 78-82);
    no effect on valid input. Input: two rows, the 36 candidates each [0, 0], `default_flag`
    [0, missing], a stepwise result with no step and empty fits; mask [true, false]. Check by a
    prover who neither wrote it nor supplied its input: prover-9 (verdict pending).
  - Revisions: S7b 0d3121a1ef6e4f54a0e27827f5dced7d, S7a 0ef7d36fa0ce4ad18bed1c3521730966,
    negation of C4 a7a601a3fbd74becb13a4983f3f44c66. Disproof text:
    `rounds/disproof-C4-2026-11-17.md`. Order, for the audit: S7b was submitted on prover-9's
    first "agrees" on the restored texts, before the fresh review made at the lead's request;
    the Lean was not changed in between, so the fresh review covers what was proved.
  - Checker's disclosure (prover-9, before starting): it did not write the negation and
    supplied no input in an earlier round; today, in its reviews, it told prover-10 that C4
    looked false because the mask also tests `default_flag`, and advised a witness "with every
    candidate a plain present number and default_flag null". The coordinator's judgement: not
    "supplied its input" (the input is the two-row input of round 2, fixed before; the advice
    repeats the contract text); the check goes on, the disclosure goes to the lead with the
    verdict, and a second checker is named if the lead judges otherwise.

- Phase 0, large-proof route (stored draft on b41b22d4 read in ranges, written as a draft on
  5365851c, submitted), prover-5; nothing written to b41b22d4; statements on the two ids
  compared first, equal:
  - S2a: from revision 67e9690ed988415dac495a7cba5cdd16 (796 lines); accepted at
    4b8e927502594fdca92cd92d2477c7f0 (796 lines).
  - S2b: from revision cb3c2347c45242bab2ffbab0f9385c3b (777 lines); accepted at
    229feffdeb2a4cd9a2afbe020564770b (777 lines).
  - Identity evidence: line counts after each chunk and at the end, every chunk seam and the
    last lines read back and compared; the body of each chunk not re-read in full. Whitespace
    repairs at seams before submitting (the append drops a leading blank line and adds no line
    break after a chunk ending without one): S2a blank line 200; S2b blank line 200, lines
    600/601 split again, final newline. No other character changed.
  - Tool behaviour for the other large-proof items: `edit_solution_draft` append drops a
    leading blank line and joins lines at a seam; read every seam back.

- C4 disproof check by prover-9: **confirmed**, without reading prover-10's proof.
  (1) the `neg:` statement is exactly the negation of C4, nothing weaker, no extra hypothesis;
  (2) input built by the checker and run once with `eval_decl` at Float (`def:zz_carrier_t` as
  evaluation carrier only): output `[1, 36, 2, 2, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1]`: mask
  [true, false], no candidate missing in either row, `default_flag` missing in row 1, the six
  clauses of the precondition true (evaluated as Boolean tests written by the checker; the
  precondition item itself did not return under `eval_decl`); (3) Python: the test is at
  `port/credit_risk/train.py` lines 97 to 102 today (the earlier record says 78-82), the
  response is in `all_horizontal(... is_not_null())`; run first-hand with polars on a two-row
  frame: mask [True, False]; the Lean unit is faithful; (4) not reachable on valid input
  (`TrainOK` makes the outcome 0 or 1; `default_flag` is that value: proved on the SAS side by
  `lem:sas_feature_rows`, read from the code on the port side, not a proved item).
  Accepted by the lead, with the checker's disclosure as judged. Line reference: the mask is at
  `port/credit_risk/train.py` line 98 at commit 9640913; "78 to 82" is the earlier revision
  (prover-10 corrects the negation's proof text and the disproof file). Nothing goes to the
  code side: the difference is on record since round 2. **For the final report**: "the witness
  is not reachable on valid input" is proved on the SAS side alone; the port-side fact follows
  only once the E-contracts of the feature stage are proved, and may not be cited before then.
- Phase 0, prover-4. Large-proof route (nothing written to b41b22d4; statements equal on both):
  H10 from 83c5fb06ad614f8da5e13253f0538ab1 (774 lines), accepted at
  a7a04e9592e74c31b9b3183def81b51a (774 lines, 31275 characters), both drafts read back whole
  and compared by eye; H13 from 24a126639d5148d9a064d1d16a5bbc9d (1402 lines), accepted at
  5a40a0f6cbfe4e6ea966fd2f8af1d49a (1402 lines, 61044 characters), read back: total lines and
  the 8 chunk boundaries only. No repair. Typed ("resubmitted from the accepted text, identity
  not shown, accepted"): sql_mean 4b6ea7401e404ba6b911fc4916825bc4, sql_max
  0aeb9410c3a74fe3b6c8d578f0b08855, proc_rank_groups_H11 ff00e3f0fba648b09ae68a1462871139.

- Phase 1, prover-6, all proved: `lem:sas_cov_credit_raw_input_check` (second conjunct of link
  (1), `TrainOK`) and `lem:sas_cov_test_raw_input_check` (second conjunct of link (2),
  `TestOK`), each reviewed "agrees" by prover-7 before the proof. `lem:sas_cov_test_raw_clean`
  restated as ruled (the precondition with the one conjunct `t.length ≤ 32` removed; the text
  quotes `def:test_raw_clean` in full to show the length is not read), proved at
  e71270ba8fd3449abf81dd0a9c2a3a1a; order: proved before prover-7's review of the restated
  statement (review pending; restate and prove again if it asks a change).
- Phase 0, prover-4, seams of H10 and H13: all read back after the last append and equal to the
  old drafts; no repair (H13: 8 chunks, 7 seams and the tail; H10: 5 chunks, whole draft
  compared).

- Phase 1, prover-4, both proved, reviewed "agrees" by prover-5 before the proofs:
  `lem:sas_cov_credit_features` b6fe165921d54037a869562cf584060b (link (4) only; `InputOK` not
  used); `lem:sas_cov_credit_train_validation` 9cd8f9fb05b84af38f1875a93626dd5f (link (5) only;
  `InputOK` not used). No carrier.

- Phase 1, prover-5, both proved, reviewed "agrees" by prover-6 before the proofs:
  `lem:sas_cov_logit_scored_valid_temp` (links (3) readFeatures, (6), `lem:sas_feature_rows`);
  `lem:sas_cov_test_scored_temp` (links (4), (6) only; `InputOK` not needed; holds on an empty
  test table). SasLinks form only; the second form is owed after `def:PyLinks` (for
  test_scored_temp it needs nothing of the read-back).

- Phase 0, prover-8, large-proof route (nothing written to b41b22d4; no repair):
  - S20b: from fca6ebb82c11453381e018588530045b (1226 lines); accepted at
    8f2c981effc74cdab2bf62cf8c1cf5aa (1226 lines); read back before submit: total and four
    seams. The stored text opens with old comments "DRAFT ... Open: the main theorem" and
    "PLAN (not done)"; the theorem is complete and compiled with no sorry; comments left.
  - S21b: from 38695223dd704a23b89c1ca9dc4a50dd (842 lines); accepted at
    ce48168d560240d1b194a2ec2dd98244 (842 lines). Deviation: submitted before the read-back;
    afterwards the line count and two seams matched.
  - S22b: from 3095068f46de40c6b1a29e8d886ce461 (798 lines); accepted at
    e0f62bab31744248b2a7e4bbdea2b87e (798 lines); read back: total, one seam, the tail.
- Phase 1 reassignment by the coordinator: proofs of `lem:sas_cov_test_features` and
  `lem:sas_cov_test_scored` (stated by prover-8, reviewed "agrees" by prover-9, not started)
  moved to prover-5, so that prover-8 states S13.

- Phase 0, prover-3 (the three reassigned by the lead; no call refused; no repair; statements
  equal on the two ids):
  - S10a: small (14 lines); `proof_lean` on 5365851c and the stored draft on b41b22d4
    (2b99ea79abc645c1be728602929b9043) read identical; accepted at
    85907e52d1b34d8f91398dab6a487eef; read back the same. Rests on S10b.
  - S9a: large-proof route, from d15a3e54e6ae401682fa19d80ff395ba (582 lines); accepted at
    bd44a04ff0134e88b9436b3f7b76b4a0 (582 lines, 24547 characters).
  - S9b: large-proof route, from 77ecb0171a674ad4a53e4d8565b4ee43 (574 lines); accepted at
    d0d68de98d3d4b5d985fd4b673cc26f0 (574 lines, 24081 characters).
  - Evidence for S9a, S9b: four ranges, line counts matching at each step, the whole new draft
    read back and compared before submitting; the two share their first 450 lines and the two
    copies have equal character counts at each boundary. Limit stated by prover-3 and true of
    every large-proof item: text passes from one call to the next only through the prover, so
    "passed exactly as read" is the prover's copying, not a tool's.
- Owners changed by the lead directly (2026-11-17): S8a to prover-4, S8b to prover-5, S10b to
  prover-6 (from prover-7, which keeps S16a, S16b and its coverage lemmas).

- Phase 0, S13 stated by prover-8 (statement revision 862fba02fff644bc9bec99ff502d389a): the
  2.3 statement with `roc_valid_created : Bool` universally quantified, given to the
  precondition and the unit; the SAS `model_summary` receives the port's `roc_valid` table when
  it is true and no row when false. **Open**: the item's `statement_text` still reads version 2
  (prover-8 held on the role rule against rewording an existing contract; the approved sentence
  is a comment at the head of the Lean); put to the lead 2026-11-17. Review by prover-10; no
  proof before the review agrees and the text question is closed.
- Phase 0, prover-3, seams of S9a and S9b: intact, no repair.
- Phase 1, prover-10, both proved (statements reviewed "agrees" by prover-2):
  `lem:sas_cov_decile_data` 4e69ffd59de84d589a9c2187d37eeac3; `lem:sas_cov_train_bins` (both
  uses) 6519b73a9ecd402480c60e519a978ac4. Rest on links (3), (4), first clause of (5); no
  clause of `InputOK`. Two facts proved inside, candidates for shared items if a second proof
  needs them: (a) no row of F1 or F2 has a column `score_bin`, `k`, `cut1` to `cut9` or
  `decile`; (b) every row of a score table has `pd_logistic` and `credit_risk_score` as numeric
  cells and has a name of that list exactly when its feature row has it.

- Phase 1, prover-5: `lem:sas_cov_test_features` proved 5e9bf3fb296b4d69affac2d0bd0a64b0 (link
  (4) only); `lem:sas_cov_test_scored` proved 826def1076364bb3b1ccef17f1a569d7 (no link). Both
  stated by prover-8, reviewed "agrees" by prover-9. The coordinator's move of test_scored to
  prover-3 came after prover-5 had proved it; prover-3 touched nothing; owner prover-5.
- Phase 2 stated by prover-1 (statements only): `def:PyParams`, `def:SasParams`,
  `def:sasPipelineOf`, `def:SasLinksOf`, `def:pyPipeline`, `lem:py_score_fillers_idle`,
  `def:PyLinks`, `def:Paired`, `lem:sas_split_input_ids`. Reviewers: prover-9 (records and the
  two applications), prover-2 (the three definitions).
- **Finding on the draft definitions (prover-1, checked by the coordinator; sent to the lead
  for decision)**: `Paired` 5 (flags shared) with `PyLinks` 7 and `SasLinks` (8) (each flag true
  exactly when its own pipeline returns the value for some argument, valid or not) can be met
  together only if the two pipelines have the same reachable outputs over all inputs; T0 would
  have no witness. Recommendation: drop the sharing (each side's flags governed by its own
  link; every contract applies a flag only to what its own side produced on the valid run).
  prover-3 searches, on paper, for any other joint clash of the three sets of clauses.

- The flags and T0, as sent to the lead (2026-11-17, proposal C-d, awaiting decision). Read
  first-hand from `def:SasLinks`, `def:sasPipeline`, `def:PyLinks`, `def:Paired`,
  `def:pyPipeline`: features and score read no flag on either side; fit reads the feature
  flags of the one table given (SAS both, the port definition the training one); scoreTest the
  medians and coefficients flags; metrics the two score flags. In every contract a flag is
  applied only to a value reached by the valid run and named by an equation. Proposal: `Paired`
  5 restates clause (8) of `SasLinks` on `sas` (no sharing); `PyLinks` 7 keeps its Lean, its
  text is made unambiguous; `pyPipeline.fit` tests both feature flags, as `sasPipeline` and
  the real stage do. The coordinator's first proposal ("no clause at all") was incomplete (the
  SAS flags would be free and E3 false) and is withdrawn. Order of proof that follows: E3 uses
  E1; E6 uses E1 and E3; E8 to E11 use E4 and the feature-shape lemma.
- S13 text, sequence: `write_statement` replaced the item's text with a generated summary; the
  lead and prover-8 each restored it with `edit_text`, prover-8 last (after being told to hold,
  on the ground that its own write had lost the text). Text at the coordinator's fetch: the
  version 2.3 contract followed by the approved version 3 sentence; state TheoremStated, Lean
  unchanged. prover-10 reviewed the Lean against that text: agrees. Whether the lead's order
  (sentence first) is to be restored is with the lead; no proof before the lead closes it.
- C4 reference corrected by prover-10 in the negation's proof text and the disproof file:
  "train.py line 98, in the assignment of fit_mask at lines 97 to 101, applied by the filter of
  line 102 (commit 9640913)"; states, Leans and C4's contract text read back untouched.
- Draft collision: partial drafts by another writer were found on S8a, S10b (lead) and S8b
  (prover-5: 900 then 1050 lines); rule from the lead: a live writer keeps the item; owners to
  be entered when prover-7 answers. prover-5 wrote nothing to S8b.
- Second, independent reads of the phase 2 items by free provers (read only): prover-4
  (`def:pyPipeline` against the Python), prover-5 (`PyLinks` 1 to 4, 9, 10 against the rules and
  the real functions), prover-6 (`PyLinks` 8 names; `Paired` 1, 2, 6 against `SasLinks`),
  prover-3 (joint clashes blocking T0).

- C-d approved by the lead in full (2026-11-17) and entered in `definitions-v3.md`: `Paired` 5
  restates `SasLinks` (8) on `sas`; `PyLinks` 7 Lean unchanged, text clarified;
  `pyPipeline.fit` tests both feature flags. prover-1 restates.
- S13 text closed by the lead as it stands (the 2.3 text followed by the version 3 sentence,
  prover-8's edit; the lead's own edit, sentence first, made within the same minutes, is
  superseded). prover-8's edit after being told to hold: recorded, no consequence (the text
  had been lost by its own write and the content is the approved one). No third review; the
  proof is released.
- Owners, final: S8a, S8b, S10b stay with prover-7 and its helpers (live drafts); provers 4, 5,
  6 are free of them and wrote nothing to them.
- Phase 2 review: prover-9 on `def:PyParams`, `def:SasParams`, `def:sasPipelineOf`,
  `def:SasLinksOf`: agrees, all four (fields only, no default, no proposition; the 17 binders
  one by one against `sasPipeline`, `today` last; the 36 field types of `PyParams` against the
  stage functions). Remark: the text of `def:PyParams` does not spell out the types of the
  eight numpy routines.

## Blueprint behaviour met

- `write_statement` on an old `thm:` item replaces its contract text with a generated summary
  (S7a, S7b, C4, found by prover-10). Restored with `edit_text` from the texts saved before the
  write (the Lean is kept); read back and compared. Remedy now in the brief.
- `thm:sas_round_H8`: statement no longer elaborated (`Sas.round` removed under G35) although the
  state read proved; found on resubmission by prover-3; removed by the lead on the owner's
  decision of 2026-11-17 (record: `removed-2026-11-16.md`). After removal: 254 items, 250
  formalised, 42 kept theorems. The coordinator's two profile checks had missed it: they compared
  SAS units and took the `Sas` helpers from the manifest. A sweep of every SAS name in every
  statement is assigned to prover-3.
- prover-9's six phase 0 items were assigned by the lead directly: S9a, S9b, S10a to prover-3
  (owner's decision; the coordinator's own message carrying it was refused by its session,
  "Undermining Oversight", and was not worked round); S8a, S8b, S10b to prover-7 (the lead's
  reassignment; no call made or refused).

## Findings and things sent to the lead

- The three points above (tool limit, permission block, S13 text).
