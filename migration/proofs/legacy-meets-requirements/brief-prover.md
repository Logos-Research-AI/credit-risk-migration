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

1. **The SAS program as a pipeline.** The SAS program was corrected on the findings of the first round (see `migration/legacy-to-lean/retranslation-report.md` and `manifest.tsv` for the units as they now are); every earlier verdict is void and every contract is decided again. One definition, `sasPipeline`, of type `CreditRisk.Pipeline`,
   assembled from the existing SAS units at the real numbers. It only wires existing units
   together: no logic of your own, nothing renamed, no unit skipped or reordered. The item, `SasLinks`, the contracts and their old negations exist from the first round without
   accepted Lean: restate them against the current units; remove an old `neg:` item rather than
   reuse it.
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
   - Errors: a step returns `none` exactly where the SAS Lean says the script stops. Since the
     SAS was corrected, each script has stop units (Booleans, true = stop): the input checks
     `credit_raw_stop` and `test_raw_stop`, and `train_inputs_stop`, `metrics_inputs_stop`,
     `predict_inputs_stop` for a missing input file. A step of the pipeline returns `none` when
     the stop unit of its script is true, and otherwise `some` of what the units compute. The
     later units are total and do not look at the Boolean themselves: the wiring must.
   - `income_medians.csv` is written by `feature_engineering.sas` and read by `predict.sas`:
     `scoreTest` gets the training medians by running the feature-engineering units that produce
     them on its raw training table argument.

   **Parameters and their links.** Everything the SAS units leave open is a parameter of
   `sasPipeline`. The contracts quantify over all parameter values that satisfy these links, and
   no other hypothesis may be added. Where the SAS has real freedom (the join order), the contract
   must hold for every choice. State the links once, as one definition `SasLinks` of the
   parameters, so every contract carries the same hypothesis.

   | Parameter | Stands for | Link |
   |---|---|---|
   | `importTrain`, `importTest` | PROC IMPORT of the two raw files (later pass) | defined on **every** table that meets `TrainOK` / `TestOK`: it keeps the rows, their order, the row ids and every column; a numeric field the requirements read with `CreditRisk.num` is delivered in the cell kind the first SAS unit reads, with the same value, and a missing value, however the table encodes it, as the one missing the first SAS unit reads (for `MonthlyIncome` and `NumberOfDependents`: text cells with `Sas.inputBest (Sas.chr row c) = CreditRisk.num row c`); within the first unit's own precondition |
   | `readFeatures`, `readScoresTrain`, `readScoresValid` | a CSV file written by one script and read by the next (later pass) | the identity |
   | `arrange` | row order of the PROC SQL joins, which SAS does not fix | a permutation of its argument, as the units' own preconditions say |
   | `split` | PROC SURVEYSELECT (outside the SAS Lean) | returns the rows of its argument in order, each with `Selected` added, 0 or 1; the number selected is 70 % of the rows rounded up (so a non-empty file never has an empty training part; evidence: the SAS runs on 1 to 3 rows and on the real data). Contracts that use the size clause are labelled *conditional on the draw* |
   | `fit` | the model fit (later pass) | every term of the model names one of the candidate variables of the MODEL statement in `train.sas` (so never `default_flag` or `row_id`), each a numeric column of every feature table the units produce from a valid input. Labelled *conditional on the fit* where used |
   | the read of `income_medians.csv` in `predict.sas` | a CSV file written by one script and read by the next | the identity on what `feature_engineering.sas` exports |
| the file-existence Booleans of the `*_inputs_stop` units | whether the previous script left its files | a file exists exactly when the step that writes it returned a result (ruling G36) |
| `best8` (the PSI floor passes through an 8-character text) | BEST8. formatting | `best8 x` is within 5·10⁻⁸ relative of `x` and positive when `x` is positive; where a contract needs more, say so |
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

## Round 3 (2026-11-15): what changed in the legacy Lean

The legacy code was corrected again (exact AUC, always ten decile rows, numeric row id, PSI floor
at full precision; rulings G40 to G43 in the requirements) and its Lean brought up to date. Before
anything else, revise `sasPipeline` and `SasLinks` to the units as they now are:

- `psi_floor` no longer takes a `best8` argument;
- `auc_summary` takes `auc_pairs` instead of `roc_stats` (`roc_stats` is read by no unit now);
- `decile_analysis` takes `decile_list` before `decile_data`;
- `test_raw_input_check` no longer depends on `credit_raw_input_check`;
- the two input checks count a row as bad when its id does not read as a number;
- on a table without the id column the check units return rows `bad_row, VAR1 (missing number)[, known_income]`;
- `Sas.sameValue` compares text cells with trailing blanks removed.

Every contract is to be proved or disproved on the Lean as it now stands. A proof or disproof kept
from an earlier round counts only if the blueprint still accepts it. The negation items of earlier
rounds are gone; state a negation afresh where a contract is false.

## Round 4 (2026-11-15): the scoring step carries no file check; two more corrections

**Wiring of `score` (corrects part 1).** Round 3 left Q12 and Q13 undecided because `score` was
wired with the input-file stop of `train.sas` (`train_inputs_stop`), so `score m F` returned
`none` on any table `F` that is not a feature file of some run. That is an artefact of the
wiring: the requirements apply `score` to tables that are no file of a run (the test feature
table of Q12 and Q13). From now on:

- `score m F` is the validation scoring chain alone, applied to `F`. It carries no stop.
- The input-file stop of `train.sas` belongs to `fit`, the step that reads the files: the
  pipeline's `fit` returns `none` when `train_inputs_stop` is true on the file-existence Booleans
  of its feature table, and `some` of the `fit` parameter otherwise. Link (8) is unchanged.
- Nothing else in the wiring changes. Revise `def:sasPipeline` to this, have it accepted, and say
  in your result exactly which lines changed.

**The legacy code was corrected again** on the two disproofs of round 3 (rulings G44 and G45 in
the requirements): `predict.sas` now scores a test file that has its header and no applicant,
writing the prediction files with header lines only; `metrics_calculation.sas` now reports
capture rate 0 and lift 0 on every decile when the validation set has no defaulter. The Lean of
the changed units was brought up to date (see `manifest.tsv`).

Every contract is decided again on the Lean as it now stands. A proof kept from round 3 counts
only if the blueprint still accepts it; where it was cleared, its draft and the shared `lem:`
items of round 3 are the place to start, not a blank page.

**Changes in the Lean units for round 4** (third update; details in
`migration/legacy-to-lean/retranslation-report.md`, section "Third update"):

- `test_raw_columns_ok` has a new first argument `test_raw_columns : List String`, the column
  names PROC IMPORT gave the test table; it is read only when the table has no row, and `[]`
  means there is no table. It has a precondition, `test_raw_columns_ok_precond` (names distinct
  up to capitalisation). `sasPipeline` therefore needs one more parameter beside `importTest`,
  for those names, and `SasLinks` one more link: on a test table meeting `TestOK` the names are
  the twelve column names of section 5 of the requirements, distinct, in any order. Like the
  other import links it says nothing outside `TestOK`.
- With the check passing on an empty test table, `scoreTest` returns `some []`.
- `decile_analysis`: `capture_rate` and `lift` are never missing. `cumulative_lift`:
  `cum_capture_rate` is 0 when the total of defaults is not above 0; `cum_lift` is missing
  exactly when `cum_count` is not above 0. No signature changed there.
- A table with no row carries no column names in this foundation. If a requirement speaks of the
  columns of an empty output, say so in your result as an interface mismatch: do not work
  around it.
- When there is no test table at all (the import failed), do not rely on the totals of the input
  check being `(0, 0)`: the stop is true there because the column check fails, and that is all
  the SAS evidence supports.

**The import links cover every table (owner's decision, 2026-11-15; replaces the "only on tables
that meet `TrainOK` / `TestOK`" wording of links (1) and (2)).** With the imports free on faulty
tables, clauses 2 and 3 of Q27 (the pipeline stops on an invalid input) were false by
construction: an import that turns a faulty file into a valid one satisfied the links. The imports
are to be constrained on every table, by what PROC IMPORT does: it delivers the file as it is.

- On **every** raw table, `importTrain` / `importTest` keep the rows, their order, the column
  names and every cell's content: a number is delivered as the same number, in the cell kind the
  first SAS unit reads (a number, or for the columns SAS reads as text a text that reads back to
  it with `Sas.inputBest`); a text is delivered as the same text; a missing value as the one
  missing the first SAS unit reads. The clauses (a) to (c) of the round 3 links, which say this
  for valid tables, are the model: generalise them, do not replace them, and keep what they give
  on valid tables exactly as it is, so that the round 3 proofs still go through.
- A column that holds a text anywhere is a character column in SAS, so the numbers of that
  column may be delivered as texts that read back to them. Allow that; do not allow anything
  else to change.
- **Do not assume the conclusion.** The link says what the import delivers. It must not say that
  the checks fail on a faulty table: that is for the SAS units to do and for the contract to
  prove.
- **Preconditions.** On valid tables the links assert the first unit's precondition, as before.
  On faulty tables assert a unit precondition only where it is a fact about what PROC IMPORT
  delivers from any file, and say which and on what evidence; never assert one that restricts
  the raw input. If clause 2 or 3 of Q27 then cannot be decided inside the units' preconditions
  for some kind of faulty table, say so precisely: which kind, which precondition.
- `importTestColumns` (link 2b) is unchanged.
