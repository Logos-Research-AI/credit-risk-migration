# Round 4: working notes (2026-11-15)

Run from the orchestrator's session with ordinary background agents (team mode did not come on
after the restart). Follows the verification kit's playbook, stages 5 to 7.

## Profile check: passed

Seven names of the requirements blueprint resolve from the legacy blueprint and equal its current
statements (`TrainOK`, `TestOK`, `Q12`, `Q13`, `Q26`, `Q27`, `Spec`).

## Pipeline revised (prover), accepted

- `def:sasPipeline`: new parameter `importTestColumns : Table ℝ → List String` after `importTest`
  (17 parameters). `score` carries no stop. `fit` is unchanged and is now the only place
  `train_inputs_stop` sits. `scoreTest` passes `importTestColumns test` to `test_raw_columns_ok`.
- `def:SasLinks`: one link added, (2b): on a test table meeting `TestOK`, `importTestColumns raw`
  is a permutation of the twelve names, and `test_raw_columns_ok_precond` holds of it. Links (1)
  to (8) textually unchanged.
- The informal text of both items was rewritten to the round 4 wiring: the judge is active on
  these two items and rejected the new Lean against the round 3 text.
- Stops: `features` credit_raw_stop; `fit` train_inputs_stop; `score` none; `scoreTest`
  predict_inputs_stop then test_raw_stop; `metrics` metrics_inputs_stop.

Noted by the author:
- `[]` is the only row-less table and meets `TestOK`, so link (2b) asserts the twelve names for
  the empty test table. A header-only file with a wrong header, or no table, is the same raw
  table `[]` at the interface: the third clause of Q27 is never tested on a bad header.
- With `score` total, link (8) makes `scoresTrainExists S` / `scoresValidExists S` true exactly
  when S is the scoring chain applied to some model and some table.
- The second conjunct of (2b) is redundant (the twelve names stay distinct when upper-cased) but
  that is not machine-checked.

Blueprint after the revision: 143 items; to restate: 26 contracts, `thm:score_chains_agree`, five
lemmas (`lem:sasLinks_witness`, `lem:sas_feature_rows`, `lem:sas_features_some`,
`lem:sas_links_sat`, `lem:sas_split_sat`). `lem:sas_features_row_total` and `lem:sas_score_rows`
remain proved.
