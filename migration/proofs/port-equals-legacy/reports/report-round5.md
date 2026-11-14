# Round 5: witnesses for the stage contracts, and three restatements

Blueprint `py-credit-risk-port` (`b41b22d4-720d-4290-b593-39ceab961986`), `claude.ai Logos MCP
Staging`, trust layer Judging on. Specification: `informal-spec.md` version 2.3. Brief:
`ROUND5.md`. `findings-for-code.md` is not changed: nothing is newly disproved.

## Summary

Round 5 touched seven contracts: **seven proved, none disproved, none open.** All are at the real
numbers. No accepted proof uses `axiom`, `sorry`, `native_decide`, `unsafe` or a `Float`
evaluation.

- **W1 to W4 are proved.** Each stage has one new contract on its `def:` item: an input and
  parameters exist that meet every hypothesis of that stage's contracts. So no stage contract is
  true only because its hypotheses cannot be met.
- **S12(a), S12(b) and S18(b) are proved** in their version 2.3 form. The three round 4 disproofs
  are gone; their negation items are removed.
- **All four witnesses are small and degenerate**, and say so in their proof texts. They show the
  hypotheses are consistent, nothing more (details per item below).
- `get_status` reports `verification_approved: true`. Validation and finalization are yours to
  run.

## Counts from `get_status`

| | End of round 4 | End of round 5 |
|---|---|---|
| Items | 316 | 317 |
| Statements formalized | 300 | 304 |
| Statements to write | 0 | 0 |
| Proofs to write | 0 | 0 |
| Waiting | 0 | 0 |
| Flagged false | 16 | 13 |
| `verification_approved` | true | true |

Four items were added (W1 to W4) and three removed (the negations of S12(a), S12(b), S18(b)).
The 13 flagged items are the disproofs of earlier rounds, unchanged:
`fe_run_04_imputed_I4`, `fe_run_05_features_I3`, `fe_run_05_features_I4`,
`metrics_run_02_ks_I7`, `metrics_run_06_psi_I1_off`, `predict_run_02_medians_I2_off`,
`predict_run_04_imputed_S31`, `predict_run_05_features_I3`, `predict_run_05_features_I8`,
`predict_run_07_predictions_I6`, `roc_association_C2`, `train_run_01_fit_frame_C4`,
`train_run_12_risk_scores_I5_bands`.

## Result per item

| Contract | Item | Result | Proof edges |
|---|---|---|---|
| W1 (ST1 feature engineering) | `thm:run_W1` | proved | none |
| W2 (ST2 train) | `thm:run_py_py_py_W2` | proved | none |
| W3 (ST3 metrics) | `thm:run_py_W3` | proved | none |
| W4 (ST4 predict) | `thm:run_py_py_W4` | proved | none |
| S12(a) | `thm:train_run_13_roc_S12a` | proved (was disproved) | `thm:train_run_13_roc_S12b` |
| S12(b) | `thm:train_run_13_roc_S12b` | proved (was disproved) | none |
| S18(b) | `thm:metrics_run_05_cumulative_lift_S18b` | proved (was disproved) | none |

Every statement was written text first, accepted by the judge, and checked by a separate reviewer
before its proof. No reviewer asked for a change to a W statement.

## The witness contracts

Each statement is an existence. The hypotheses are written out as the same Lean the stage
contracts have, conjoined. Parameters that stand for out-of-scope code are placeholders, as
section 3 of the specification allows.

### W1, feature engineering

- **Statement.** There are `input_best32`, `cs_training`, `split_ids` such that: the raw table is
  well formed; the stage precondition holds for both values of `full`; the three links hold; and
  for every `arrange` meeting its precondition there is a `credit_split` meeting the row, 0/1 and
  selection conditions.
- **Witness.** One row: `VAR1` 1, `SeriousDlqin2yrs` 0, utilization 0, age 45, the three late
  counts 0, `DebtRatio` 0, `MonthlyIncome` "5000", credit lines 5, real estate loans 1,
  `NumberOfDependents` "2". `split_ids` has `row_id` 1. `input_best32` is the SAS `BEST32.`
  informat applied to the text column. `credit_split` is the feature row with `Selected` 1.
- **What it does not exercise.** The validation file is empty on it. With one row every
  `arrange` is the identity.
- **Proof.** 651 lines. It uses `decide +kernel` on closed terms; this is kernel evaluation, not
  `native_decide`.

### W2, train

- **Statement.** The union of the ST2 hypothesis lists, five conjuncts: both feature tables well
  formed, the stage precondition, the `invLink` link, and the domain condition on the final
  coefficients.
- **Witness.** T = V, two rows with the 42 number columns: `row_id` 0 and 1, `default_flag` 0
  and 1, the other 40 columns 0. Stepwise result with no steps; final fit on
  [Intercept, `credit_utilization_capped`] with beta [0, 1] and identity covariance. `today` is
  24422. The formatters return the empty text, chi2 is 0, and the linear algebra parameters are
  placeholders. `invLink` is defined as the right-hand side of its link.
- **What it does not exercise.** T and V are the same table. The coefficient 1 sits on an
  all-zero column, so every probability is exactly 1/2 and all scores are tied.
- **Proof.** About 1,240 lines; all 17 conjuncts of the stage precondition, one lemma per step.
  Real-number facts used: exp 0 = 1, exp > 0, sqrt 1 = 1.
- **Difference from the plan.** The row ids are 0 and 1, not 1 and 2.

### W3, metrics

- **Statement.** The union of the six ST3 hypothesis lists, 16 conjuncts, the row bounds and both
  clauses of the count link included.
- **Witness.** `va` = `tr`, two rows with the 51 columns: `row_id` 1 and 2, `default_flag` 0
  and 1, every other number column 1 (so `pd_logistic` is 1 on both rows), the four text columns
  "A". `sas_best` of a present x is the letter a followed by floor(x) letters b, and the empty
  text for a missing value. `parse_float` is the length minus 1. `best8` is their composition.
  `agg` is (sum, sum divided by length). `sas_d8` is constantly the empty text. `today` is 23000.
- **What it does not exercise.** The scores are tied, so there is one rank group in every step.
  The two tables are the same. The format functions are not the SAS formats.
- **Proof.** About 1,200 lines; the 15 conjuncts of the stage precondition, one group of lemmas
  per step. At every threshold from 0.3 to 0.7 the counts are TP 1, TN 0, FP 1, FN 0.
- **Proof text.** It says the five table conditions go through the lemma `ztab`. Two of the five
  are in fact evaluated inside the precondition lemma by the same computation. I left the text,
  because changing it resets the accepted proof.
- **Left in the proof file.** One block of commented-out lemmas from an earlier attempt, a small
  unused lemma (`zprobe1`), and two `first | … | fail` wrappers. They do not affect the proof.

### W4, predict

- **Statement.** There are `input_best32`, `intercept`, `coefficients`, `medians`, `cs_test` such
  that for every `full`: the raw test table is well formed, the stage precondition holds, and the
  `input_best32` link and the domain condition hold.
- **Witness.** One row: `VAR1` 1, age 45, credit lines 5, the other numbers 0;
  `SeriousDlqin2yrs`, `MonthlyIncome` and `NumberOfDependents` hold missing text. Intercept 0, no
  coefficients, no medians. `input_best32` returns a missing number whatever the text.
- **What it does not exercise.** An empty medians frame, dependents filled with 0, a constant
  `input_best32`, and no coefficients. A richer witness was not attempted.

## The three restatements

Each was restated with the guarantee of section 2 that it lacked in round 4, and nothing else.

| Contract | Hypothesis added (version 2.3) | Used in the proof | Not needed |
|---|---|---|---|
| S12(a), S12(b) | `default_flag`, when present, is 0 or 1 on both score frames | the added guarantee; part of the step precondition | "both outcomes occur"; well-formedness of the two tables |
| S18(b) | `decile_analysis` is in ascending `decile` order | the ordering; all three clauses of the `best8` link; `total_count` present; non-zero running sums from the precondition | the shape of `decile_data`; any condition on `default_flag` |

- **S12(b)** is the main proof, 1,036 lines. **S12(a)** follows from it by a proof edge.
- **Hypotheses can be met.** S12: a lemma over the reals on three rows, flags 1, 0, 0 and
  probabilities 0.5, 0.3, 0.9. S18(b): a lemma over the reals on a two-row `decile_analysis`
  in decile order 1, 2 and a one-row `decile_data`.

## Readings to confirm

1. **Conditions kept from version 2.2.** The texts of the three restated items attribute the
   S12(a) domain, the S12(b) "no never-missing condition" and "`total_count` present" to
   section 9 of version 2.2, as kept by version 2.3.
2. **The ordering in S18(b)** is stated as a fixed point: sorting `decile_analysis` by `decile`
   returns it unchanged.
3. **`full` in W1 and W4** is universally quantified inside the existence: one witness serves
   both values.
4. **`arrange` in W1** is universally quantified, with `credit_split` chosen after it.
5. **Degenerate witnesses.** The brief asks for "a concrete small input". If you want witnesses
   with untied scores or distinct training and validation tables, W2 and W3 would need new
   proofs of the rank, Hosmer-Lemeshow and classification steps.

## `findings-for-code.md`

Not changed, as the brief asks. Its section "Specification gaps" still lists S12(a), S12(b) and
S18(b) as round 4 left them. Version 2.3 closed those gaps and the three contracts are now
proved, so that section is out of date.

## What went wrong

- **W3 took three attempts.** The first agent ran out of room with the proof four-fifths done.
  Its `submit_solution` calls timed out on the client at 60 seconds 88 times out of 115, each
  leaving a compile running on the server. The second agent met an unreachable server and
  changed nothing. I finished the proof directly, compiling each open lemma on its own in a
  temporary item (`thm:zz_w3_scratch`, statement `True`), which is now removed.
- **Oversized tool results with Lean were saved to disk by the harness.** The first W3 agent
  reports four, all deleted by it, one of which it caused on purpose to read a truncated result;
  it stopped after that. Four files of compile output with Lean goals are still under
  `~/.claude/projects/-Users-cristophersalvi-GitHub-sas-migration-formal-prover/2a2ffe4a-6b04-4f5e-b827-557979ca4e66/tool-results/`:
  `toolu_017W8Ycw4U8ZyeJGHKMZZeLi.txt`, `toolu_018HGWeLEhshxqXgyygvu65N.txt`,
  `toolu_01HVq6MVAgkG4Jbt9XQWkTWn.txt` and `toolu_01VVLg6rKaGYYj2bi1TVuB6f.txt`. I have not
  deleted them: an agent's attempt to delete one was denied by the permission system.
- **Round 4 clean-up is still undone.** The proof files of S13, S11(b) and the two I5 items may
  still hold commented-out blocks; the submissions that would have cleaned them were denied in
  round 4 and I did not retry them ("touch nothing else").
- No `zz` item of mine remains in the blueprint. No original `def:` item was changed.
