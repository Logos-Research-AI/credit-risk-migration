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
