# Round 4: the tie constant, and the restatements of version 2.2

Blueprint `py-credit-risk-port` (`b41b22d4-720d-4290-b593-39ceab961986`), `claude.ai Logos MCP
Staging`, trust layer Judging on. Specification: `informal-spec.md` version 2.2. Brief:
`ROUND4.md`. `findings-for-code.md` is updated: S12(a) and S12(b) are newly disproved.

## Summary

Round 4 touched 15 contracts: **12 proved, 3 disproved, none open.** All are at the real numbers.
No accepted proof uses `axiom`, `sorry`, `native_decide` or `unsafe`.

- **All fourteen stage files are proved equal to SAS.**
- **The ROC tie rule is confirmed.** H12 is proved: the Python area equals the SAS area, tie rule
  included. Round 2 finding P1 is fixed, and no `port-differs-from-sas` finding is left.
- **Three contracts are disproved against section 9's expectation: S12(a), S12(b), S18(b).** None
  is a port difference. Each fails on a step frame that no run produces and that version 2.2's
  well-formedness of step frames does not exclude. They need one clause each in the
  specification (below).
- `get_status` reports `verification_approved: true`: nothing is left to state or prove.
  Validation and finalization are yours to run.

### First check

`check_decl Sas.rocTops` from `def:roc_association` shows
`3184525836262887 / 302231454903657293676544`, the same number as Python `_TIE_EPS`. The refresh
of the profile cleared no proof: `get_status` was exactly as at the end of round 3 (ten proofs to
write, the same 18 flagged items). So step 1 of the brief had nothing to re-prove.

### The fourteen stage files

| Stage | Proved equal to SAS | Disproved | Open |
|---|---|---|---|
| ST1 feature engineering | `model_features_train.csv`, `model_features_validation.csv` | | |
| ST2 train | `risk_scores_train.csv`, `risk_scores_validation.csv`, `final_model_output.csv`, `model_summary.csv` (all but `risk_scores_validation.csv` conditional on `invLink`) | | |
| ST3 metrics | `decile_analysis.csv`, `threshold_analysis.csv`, `calibration_plot.csv`, `ks_statistic.csv`, `validation_summary.csv`, `model_performance_metrics.csv` (the last three for tables of fewer than 10^8 rows) | | |
| ST4 predict | `kaggle_submission.csv`, `test_predictions.csv` (under the `input_best32` hypothesis) | | |

Fourteen of fourteen proved. `model_summary.csv`, `validation_summary.csv` and
`model_performance_metrics.csv` moved from open to proved.

### Counts from `get_status` (end of round)

| | |
|---|---|
| Items | 316 |
| Statements formalized | 300 |
| Statements to write | 0 |
| Proofs to write | 0 |
| Waiting | 0 |
| Flagged false | 16 |
| `verification_approved` | true |

The 16 flagged contracts: the three disproved in this round, and 13 that stand from earlier
rounds (`fe_run_04_imputed_I4`, `fe_run_05_features_I3` and `_I4`, `metrics_run_02_ks_I7`,
`metrics_run_06_psi_I1_off`, `predict_run_02_medians_I2_off`, `predict_run_04_imputed_S31`,
`predict_run_05_features_I3` and `_I8`, `predict_run_07_predictions_I6`, `roc_association_C2`,
`train_run_01_fit_frame_C4`, `train_run_12_risk_scores_I5_bands`): eleven shared intent failures
and two inaccurate records.

## Every contract touched

### The ten that were open

| Contract | Item | Result | Notes |
|---|---|---|---|
| H12 | `thm:roc_association_H12` | **proved** | Statement unchanged. "Both outcomes present" is not needed: with one class empty both sides give a missing Area |
| S12(a) | `thm:train_run_13_roc_S12a` | **disproved** | Restated; see below |
| S12(b) | `thm:train_run_13_roc_S12b` | **disproved** | Restated; see below |
| S14(a) roc, auc; S14(b) roc, auc | `thm:metrics_run_01_roc_auc_S14a_roc`, `_S14a_auc`, `_S14b_roc`, `_S14b_auc` | **proved** | Statements unchanged. Part (b) holds with missing values and with a single outcome. Proved without H12: the tie-rule agreement is proved again inside the S14(b) roc file |
| ST2 `model_summary.csv` | `thm:run_py_py_py_ST2_model_summary` | **proved**, conditional on `invLink` | Statement unchanged. Uses H12 directly on the stage's frames, where well-formedness gives `default_flag` 0 or 1; does not use S12 or S13 |
| ST3 `validation_summary.csv` | `thm:run_py_ST3_validation_summary` | **proved** | Restated with the row bound |
| ST3 `model_performance_metrics.csv` | `thm:run_py_ST3_model_performance_metrics` | **proved** | Restated with the row bound |

### The restated contracts

Every restated statement was checked by a separate reviewer before its proof.

| Contract | Item | Result | Notes |
|---|---|---|---|
| S2(b) | `thm:fe_run_02_income_medians_S2b` | **proved** | On `def:wf_fe_step02`, as sets of rows. Part (a) without its domain hypotheses |
| S24(b) | `thm:predict_run_02_medians_S24b` | **proved** | On `def:wf_pr_raw_clean`, as sets of rows |
| S25(b) | `thm:predict_run_03_cleaned_S25b` | **proved** | On `def:wf_pr_raw_clean` |
| H10 | `thm:merge_one_to_one_H10` | **proved** | Same-kind condition as its own hypothesis; the precondition item untouched. Every hypothesis is used |
| S12(a), S12(b) | as above | **disproved** | |
| S18(b) | `thm:metrics_run_05_cumulative_lift_S18b` | **disproved** | New reason; the link gap is closed |
| ST3, two summary files | as above | **proved** | |

The concrete inputs of S2(b), S24(b) and S25(b) have a missing age, so the case part (b) adds is
exercised. H10's has a shared name and a shorter later frame of another numeric kind.

## The three disproofs

### S12(a) and S12(b): a `default_flag` that is neither 0 nor 1

- **Statement.** As section 9 words it: well-formedness `def:wf_tr_risk` (shape only), the
  precondition, and for (a) both columns present on every row with both outcomes; for (b) both
  outcomes among the rows where both are present.
- **Witness** (the same 51-column frame for training and validation, three rows):
  `default_flag` = 1, 0, 2 and `pd_logistic` = 0.5, 0.3, 0.9. It is proved to meet every
  hypothesis of part (a), and so of part (b).
- **Python:** Area 1. Events are the rows with flag 1, non-events the rows with flag 0; the 2 is
  in neither class (`sas_compat.py`, `_pairs`, lines 856-882).
- **SAS:** Area 1/2. Everything that is not 1 is a non-event (rule R25, `Sas.rocObs`).
- **Kind:** specification gap, not a port difference. **Reach:** none. A stage input has flags 0
  or 1, the steps pass the column through, and `model_summary.csv` is proved at stage level.
- **A hypothesis I removed.** The first restatement carried "`default_flag`, when present, is 0
  or 1" as part of well-formedness. The reviewer ruled it out: section 2 gives that condition for
  stage inputs, and its list of what a step frame guarantees about its cells (`row_id`,
  `age_group`, `pred_logistic`) does not include it. So the contracts are stated without it, and
  are false.
- **What would close it:** one clause, either in section 2 ("`default_flag`, when present, is 0
  or 1 in every step frame that carries it") or on the S12 row. With it both parts are expected
  to hold: the lemma `h12_general` in the H12 proof file proves the area equality when the flag
  is missing, 0 or 1 on every row with a present probability. The two small bridges from that
  lemma to the step were not proved.

### S18(b): `decile_analysis` not sorted by decile

- **Statement.** With the three-clause `best8` link and `total_count` present on every row, as
  section 9 says. The shared shape definition was not edited (the proved S18(a) uses it);
  `total_count` present is its own hypothesis.
- **Witness:** `decile_analysis` of two rows in the order `decile` 2, 1; `total_count` 1, 1;
  `defaults` 0, 1. Proved to meet every hypothesis.
- **Python:** rows in the order decile 1, 2. Step 05 sorts the frame first
  (`metrics_calculation.py` line 229).
- **SAS:** rows in the order decile 2, 1. The unit folds the rows in the order given
  (`metrics_calculation.sas` lines 220-235); in the SAS program the order comes from
  `order by decile` in the step before (lines 191-206).
- The proved difference is the `decile` cell of the first row. By `Float` evaluation only, on a
  two-row `decile_data`: `cum_defaults` 1, 1 in Python against 0, 1 in SAS.
- **Kind:** specification gap: the row order of a step's input is not part of well-formedness.
  Not a port difference: the port follows the SAS program as a whole. **Reach:** none; step 04
  always returns the frame sorted (line 192), and S18(a) is proved.
- **What would close it:** state that `decile_analysis` is in ascending `decile` order as step
  04 returns it, or state S18(b) on step 04's outputs as S18(a) is. On sorted input the two sides
  agreed in three `Float` evaluations (missing decile, tied deciles, missing `defaults`, every
  flag missing); that is not proved.
- I did not add a sortedness hypothesis.

## Readings for you to confirm

- **H10, "same kind".** Kind is number or text: a String column is text; Float64, Int64,
  Boolean, Date and an all-missing untyped (Null) column are numbers. Null as number is forced by
  the table model, which gives it numeric missing cells.
- **S14(b) and a single outcome.** The pinned SAS definition `roc_stats` always returns one row,
  with a missing Area on a single class, and Python does the same, so S14(b) holds as stated.
  Section 9 says of S12(b) that "SAS produces no table otherwise"; if real SAS produces no table,
  the pinned definition does not model that case. Not checked against real SAS.
- **Stage contracts not restated for the third `best8` clause.** The two restated ST3 files do
  not assume "the text is empty for a missing value": they do not need it, and their texts say
  so. S18(a) and the other proved contracts keep their earlier texts.

## Hypotheses can be met (rule 4)

| Contracts | How one input meeting all hypotheses is shown |
|---|---|
| H12, H10, S2(b), S24(b), S25(b), the four S14 items | A lemma at the reals in the proof file (for S14, in the S14(b) roc file) |
| ST2 `model_summary.csv` | By reference to the round 3 `Float` evaluation of the ST2 hypotheses (same hypothesis block). The conclusion of this file was not evaluated on that input |
| ST3 `validation_summary.csv`, `model_performance_metrics.csv` | By reference to the round 3 `Float` evaluation of the ST3 hypotheses (same block as `ks_statistic.csv`). Not re-run |

The limits of those evaluations are as stated in `report-round3.md`.

## Clean-up asked for in the brief

| Item | Done |
|---|---|
| H8 text | Done. The remarks about `Float` evaluation of the old code are removed; the item stayed proved with the same Lean |
| H10 text | Done with the restatement |
| S25(b) text | Done with the restatement ("expected to fail" is gone) |
| Stale proof edge ST1 train to S5(a) | Removed. The disconnect cleared the proof; the stored solution was re-submitted unchanged and accepted. Nothing else was affected |
| Commented-out lemmas, ST1 train and validation | Removed: 4,025 lines to 2,921 in each; accepted |
| Commented-out lemmas, S29 | Removed: 1,648 lines to 1,561; accepted. The two ST4 proofs that depend on S29 were not cleared |
| Commented-out lemmas, S13, S11(b), I5 sharp range, I5 grades | **Not done.** The clean-up agent's `submit_solution` calls were denied by the permission system, and I did not submit in its place |

State of the four files not done (their accepted proofs are unchanged, and they and their
dependants are proved):

- S13: the stored draft has no commented-out block left. Whether the accepted proof is that
  draft or the older file with one 13-line block is not confirmed: two earlier submissions timed
  out on the client.
- S11(b): one 57-line dead block is removed from the stored draft, not submitted; the rest of
  the file was not scanned.
- I5 sharp range: a dead block is located (ending at line 485), not removed.
- I5 grades: partly scanned, nothing found.

## Other notes

- **Items.** Removed: the old negations of S2(b), S24(b), S25(b), H10 and S18(b). Added: the
  negations of S12(a), S12(b) and S18(b). No `zz` item remains. No `def:` item was touched, and
  no well-formedness definition was edited.
- **Proof edges added.** S14(a) roc and S14(b) auc to S14(b) roc; S14(a) auc to S14(b) auc. ST2
  `model_summary.csv` to S7(b), S8(a), S9(b), S10(b), H12 and the two ST2 risk-score files. ST3
  `validation_summary.csv` to S21(a), S14(a) auc, S15(b) KS, S19(b), S15(a) sorted; ST3
  `model_performance_metrics.csv` to S22(a), the same four, and ST3 `threshold_analysis.csv`.
  The S12(b) negation to the S12(a) negation.
- **Stale texts on translator items** (not fixed): the item texts of `def:_pairs` and
  `def:roc_association` still show the old source and docstring; those of the step 02 and 03
  definitions still show the plain comparisons. Their Lean follows the new code.
- **Service behaviour.** A helper lemma placed before the main theorem that contains a `match`
  of the same shape as the statement's makes the submission fail the challenge check although it
  compiles. Re-submitting a proof whose statement is unchanged does not clear the proofs that
  depend on it.
- **One file to delete.** A failed submission returned a large goal dump that the harness saved
  to
  `~/.claude/projects/-Users-cristophersalvi-GitHub-sas-migration-formal-prover/2a2ffe4a-6b04-4f5e-b827-557979ca4e66/tool-results/toolu_0187oY2WXDbePVseBwRCLCmo.txt`.
  It holds Lean goal text. The agent's attempt to delete it was denied by the permission system,
  and I did not delete it in its place. No other Lean is saved locally.
- **Process.** At most four subagents worked against the blueprint at once.
