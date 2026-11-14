# Does the legacy SAS program meet the documented requirements?

## What this is for

The documentation of the SAS credit-risk pipeline has been turned into formal requirements, proved
consistent and signed off by its owner: blueprint `credit-risk-requirements`
(`006ff04c-d34c-4a9c-b230-ccd725b1be6f`), written up in `migration/requirements/requirements.md`.
The SAS program has been translated to Lean, unit by unit, and checked against real SAS runs:
blueprint `sas-credit-risk-spec` (`3f5df696-7c80-45cc-809f-b2881714663d`), record in
`migration/legacy-to-lean/` (start with `manifest.tsv`).

Your job is to decide, requirement by requirement, whether the SAS program meets it. The
documentation is the authority: where the SAS fails a requirement, the SAS is wrong and will be
corrected. So a disproof is a good result, and a weakened proof is worthless.

The requirements blueprint is pinned as a profile of the SAS blueprint, so its definitions
(`CreditRisk.Pipeline`, `CreditRisk.InputOK`, `CreditRisk.Q1` … `CreditRisk.Q27`, `CreditRisk.Spec`)
are visible from `sas-credit-risk-spec`. All your items go in `sas-credit-risk-spec`.

## What to build

1. **The SAS program as a pipeline.** One definition, `sasPipeline`, of type `CreditRisk.Pipeline`,
   assembled from the existing SAS units at the real numbers. It only wires existing units
   together: no logic of your own, nothing renamed, no unit skipped or reordered. If the item
   already exists, revise it to match this brief.
   - `features`: the units of `feature_engineering.sas`, from the raw training table to the two
     feature tables (the data sets handed to PROC EXPORT).
   - `fit`: a parameter (the model fit is a later pass).
   - `score`: the **validation** scoring chain of `train.sas` (PROC PLM and the explicit formula:
     `logit_scored_valid_temp`, `logit_scored_valid`, `risk_scores_validation`,
     `risk_scores_validation_clean`). `train.sas` scores the training table with a second chain
     (PROC LOGISTIC OUTPUT, which uses the unknown `invLink`). The interface has one scoring
     function, so the second chain is tied to the first by a separate theorem, `score_chains_agree`
     (part 2b), and is not wired into `sasPipeline`.
   - `scoreTest`: the units of `predict.sas`, to `test_predictions.csv`.
   - `metrics`: the units of `metrics_calculation.sas`, to the four metrics tables the
     requirements name.
   - Errors: a step returns `none` exactly where the SAS Lean says the SAS stops. If the units are
     total, every step returns `some`.

   **Parameters and their links.** Everything the SAS units leave open is a parameter of
   `sasPipeline`. The contracts quantify over all parameter values that satisfy these links, and
   no other hypothesis may be added. Where the SAS has real freedom (the join order), the contract
   must hold for every choice. State the links once, as one definition `SasLinks` of the
   parameters, so every contract carries the same hypothesis.

   | Parameter | Stands for | Link |
   |---|---|---|
   | `importTrain`, `importTest` | PROC IMPORT of the two raw files (later pass) | keeps the rows, their order and every column; a numeric field the requirements read with `CreditRisk.num` is delivered in the cell kind the first SAS unit reads, with the same value, and missing as missing (for `MonthlyIncome` and `NumberOfDependents`: text cells with `Sas.inputBest (Sas.chr row c) = CreditRisk.num row c`); within the first unit's own precondition |
   | `readFeatures`, `readScoresTrain`, `readScoresValid` | a CSV file written by one script and read by the next (later pass) | the identity |
   | `arrange` | row order of the PROC SQL joins, which SAS does not fix | a permutation of its argument, as the units' own preconditions say |
   | `split` | PROC SURVEYSELECT (outside the SAS Lean) | returns the rows of its argument in order, each with `Selected` added, 0 or 1; the number selected is within one of 70 % of the rows. Contracts that use the size clause are labelled *conditional on the draw* |
   | `fit` | the model fit (later pass) | every term of the model names a numeric column of the feature table. Labelled *conditional on the fit* where used |
   | `agg` | PROC SQL SUM and MEAN | the real sum and mean of the list |
   | `invLink` | PROC LOGISTIC's own probability | not a parameter of `sasPipeline`; appears only in `score_chains_agree`, as `invLink e = 1 / (1 + exp (-e))` |

2. **One contract per requirement**: theorem items `sas_Q1` … `sas_Q27` (not Q17), each stating
   `CreditRisk.Qk (sasPipeline …)` for all parameters satisfying the links above. The informal
   text of each is the requirement's wording from `requirements.md`.
2b. **The two scoring chains agree**: one theorem, `score_chains_agree`: under the `invLink` link,
   the training chain of `train.sas` gives, on the training feature table of a run, the same score
   table as `score`. Prove or disprove it like a contract. Every result about
   `risk_scores_train.csv` rests on it.
3. **Prove or disprove each contract.** To disprove: negate, prove the negation with a concrete
   input that meets `CreditRisk.InputOK`, and flag the contract false. Give the smallest input you
   can, what the requirement demands on it, what the SAS produces, and the SAS file and lines
   responsible.

## Rules

- Never change an existing item, in either blueprint. Never restate a requirement: the contract is
  `Qk` applied to `sasPipeline`, nothing else.
- Never add a hypothesis beyond the parameter links. If a contract is true only under a further
  assumption, it is false as stated: disprove it and say which assumption would rescue it.
- If a requirement cannot be connected to the SAS at all (a file or column the requirement names
  does not exist in the SAS output, or exists under another name), do not bridge it yourself:
  report it as `interface-mismatch`, with the two names.
- No `axiom`, `sorry`, `native_decide` or `unsafe` in an accepted proof.
- All Lean lives in the blueprint. Do not write files; return your report as text.

- A counterexample must lie inside the SAS units' own preconditions (the `*_precond` items):
  outside them the Lean was not checked against SAS, so a failure there is about the model, not
  the program. Say for each disproof which preconditions you checked.
- A contract that holds only by the form of `sasPipeline` or of a link (Q11 through `split`, the
  size clause of Q10) is reported as `by-construction`, not as proved about the SAS.

## Findings

One entry per requirement that is not proved, with a kind:

- `legacy-violates-requirement`: disproved. Counterexample, SAS lines, and the smallest change
  to the SAS that would meet the requirement (described, not made).
- `interface-mismatch`: the requirement cannot be stated on the SAS as it is.
- `needs-ruling`: the requirement is ambiguous on a case the SAS reaches; say which case.
- `open`: neither proved nor disproved; say what is missing.
