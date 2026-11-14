# Does the legacy SAS program meet the documented requirements?

## What this is for

The documentation of the SAS credit-risk pipeline has been turned into formal requirements, proved
consistent and signed off by its owner: blueprint `credit-risk-requirements`
(`006ff04c-d34c-4a9c-b230-ccd725b1be6f`), written up in `migration/requirements/requirements.md`.
The SAS program has been translated to Lean, unit by unit, and checked against real SAS runs:
blueprint `sas-credit-risk-spec` (`a490bc52-8080-49b4-a6f3-8d3c4d29754a`), record in
`migration/legacy-to-lean/` (start with `manifest.tsv`).

Your job is to decide, requirement by requirement, whether the SAS program meets it. The
documentation is the authority: where the SAS fails a requirement, the SAS is wrong and will be
corrected. So a disproof is a good result, and a weakened proof is worthless.

The requirements blueprint is pinned as a profile of the SAS blueprint, so its definitions
(`CreditRisk.Pipeline`, `CreditRisk.InputOK`, `CreditRisk.Q1` … `CreditRisk.Q27`, `CreditRisk.Spec`)
are visible from `sas-credit-risk-spec`. All your items go in `sas-credit-risk-spec`.

## What to build

1. **The SAS program as a pipeline.** One definition, `sasPipeline`, of type `CreditRisk.Pipeline`,
   assembled from the existing SAS units at the real numbers:
   - `features`: the units of `feature_engineering.sas`, from the raw training table to the two
     feature tables. The 70/30 draw is a parameter of the SAS Lean (`credit_split`); the seed
     selects it through a parameter `split : ℕ → …` of `sasPipeline`.
   - `fit`: the model fit is outside the SAS Lean (a later pass). It is a parameter of
     `sasPipeline`: an arbitrary function from the training feature table to a fitted model
     (intercept and named coefficients, as the scoring units take it).
   - `score`: the scoring units of `train.sas`, from the model and a feature table to the score
     table (`risk_scores_train.csv` / `risk_scores_validation.csv`).
   - `scoreTest`: the units of `predict.sas`, to `test_predictions.csv`.
   - `metrics`: the units of `metrics_calculation.sas`, to the four metrics tables the
     requirements name.
   - Errors: a step returns `none` exactly where the SAS Lean says the SAS stops. If the SAS units
     are total, every step returns `some`.
   Add no logic of your own: `sasPipeline` only wires existing units together and renames nothing.
   Every other parameter the SAS units leave open (`arrange`, `agg`, `best8`, `invLink`, `today`,
   the CSV conversion) is a parameter of `sasPipeline` too, constrained only by the links of
   section 1 of `migration/proofs/port-equals-legacy/informal-spec.md` that speak of the SAS side
   (`agg` is the real sum and mean; `best8` returns its argument for the values that occur;
   `invLink e = 1 / (1 + exp (-e))`, labelled conditional). No other hypothesis.
2. **One contract per requirement**: theorem items `sas_Q1` … `sas_Q27` (not Q17), each stating
   `CreditRisk.Qk (sasPipeline …)` for all parameters satisfying the links above. The informal
   text of each is the requirement's wording from `requirements.md`.
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

## Findings

One entry per requirement that is not proved, with a kind:

- `legacy-violates-requirement`: disproved. Counterexample, SAS lines, and the smallest change
  to the SAS that would meet the requirement (described, not made).
- `interface-mismatch`: the requirement cannot be stated on the SAS as it is.
- `needs-ruling`: the requirement is ambiguous on a case the SAS reaches; say which case.
- `open`: neither proved nor disproved; say what is missing.
