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

## Findings and things sent to the lead

(none yet)
