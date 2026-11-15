# Team trial: the six open stage 2 contracts

Run on 2026-11-15 by an agent team: one lead and ten teammates, `prover-1` to `prover-10`, all of
the sub-agent type `prover`. Legacy blueprint `sas-credit-risk-spec`
(`3f5df696-7c80-45cc-809f-b2881714663d`), Logos MCP Staging.

All six contracts are settled on the blueprint: four proved, two disproved and checked. The states
below were read from the blueprint by the lead at the end (`get_status`, `get_items`), not taken
from the teammates' messages. `get_status` lists `thm:sas_Q26` and `thm:sas_Q27` as flagged, and
`thm:sas_Q12` and `thm:sas_Q13` as the only proofs still to write; nobody touched those two.

## 1. Outcomes

| Requirement | Outcome on the blueprint | Proved or refuted by | Links used | Lemmas used |
|---|---|---|---|---|
| Q14 | proved | `prover-1` | (1), (2) imports; (3) `readFeatures`, `readMedians`; (4) arrange; (5) split, row clause, through the lemma; (6) fit | `lem:sas_features_row_total`, `lem:sas_feature_rows` |
| Q22 | proved | `prover-3` | (1), (4), (5) row clause, through the lemma; (3) `readFeatures`, `readScoresValid`; (6) fit | `lem:sas_feature_rows` |
| Q23 | proved | `prover-5` | (1); (3) `readFeatures`, `readScoresValid`; (4); (5) row clause | none |
| Q24 | proved | `prover-7` | (1), (4), (5) row clause, through the lemma; (3) `readFeatures`, `readScoresValid`; (6) fit | `lem:sas_feature_rows`, `lem:sas_score_rows` |
| Q26 | disproved and checked | refuted by `prover-10`; checked by `prover-5` | failure proved for every parameter choice meeting the links; inside it (3), (6), (7) agg, (8) file existence, and (1) through the lemmas | `lem:sasLinks_witness`, `lem:sas_feature_rows`, `lem:sas_features_some`, and the contract `thm:sas_Q10` (proved) |
| Q27 | disproved and checked | refuted by `prover-9`; checked by `prover-2`, `prover-4` and `prover-8` | (2) `importTest` for the failure; all links for existence of parameters | `lem:sas_links_sat`, `lem:sas_split_sat` |

Notes on the proved ones:

- Q14, Q22 and Q24 are conditional on the fit (link 6: the model's terms are among the 36
  candidates of the MODEL statement). Round 2 had listed Q24 without the fit link; it enters
  because the proof needs a non-missing probability on every validation row.
- None of the four uses the size clause of the split, so none is conditional on the draw.
- All four are over the reals. In floating point a very negative logit (below about -709) makes
  `exp` overflow and SAS gives a missing probability (`train.sas` 185, `predict.sas` 305-313,
  experiment x19). The contracts cannot see this; the proofs do not cover it.
- The refute side found nothing against Q14 (`prover-2`), Q22 (`prover-4`), Q23 (`prover-6`) and
  Q24 (`prover-8`), each after evaluating the legacy Lean on edge inputs.

## 2. Contracts not proved

### Q27: the scoring script stops on a test file with no applicant

- **Input.** A valid training file (the witness has one row: id 1, no default, age 1, monthly
  income 1, every other field 0) and a test file with no data row. Seed 0. The requirements as
  signed off accept this input: section 3 does not ask the test file to hold an applicant (it
  does ask the training file for at least one known income).
- **What the requirement demands.** Q27, clause 1: on a valid input every step produces its
  result. Here the scoring step should produce an empty predictions table.
- **What the legacy code produces.** Nothing. `PROC IMPORT` fails on a file with a header and no
  data line, `WORK.TEST_RAW` is not created, `columns_ok` stays 0 and the script stops with
  `abort cancel`. This happens whatever the training data, the seed, the split or the model.
- **Evidence on real SAS.** `experiments/x21_review_round2` part C: log line 262 ("Unable to
  sample external file, no data in first 5 records", import unsuccessful) and line 295
  (`C_header_only_test … columns_ok=0`). Not rerun during the trial.
- **Lines.** `legacy/predict.sas` 49-55 (the `PROC IMPORT`), 71-86 (`columns_ok`), 123-130 (the
  stop; `abort cancel` at 128).
- **Smallest change.** When `cs-test.csv` has the twelve header names and no data line, create an
  empty `WORK.TEST_RAW` with those columns instead of letting the import fail, so that the check
  passes and `test_predictions.csv` and `kaggle_submission.csv` are written with their header
  lines only.
- **Check.** Three teammates checked it independently (see section 4) and agree on all four
  points: exact negation, proved, no sorry or axiom in it or in its two lemmas; input valid;
  failure independent of every parameter; lines right.
- **Depends on a ruling.** See section 5, point 1.

Two further inputs were raised from the prove side by `prover-6` and are **not** part of the
disproof. Clauses 2 and 3 of Q27 ask the code to stop on invalid tables, but the import links say
what the imports do on valid tables only, so those clauses cannot be decided about the legacy
code as the links stand. One of the inputs may be a real gap: a training file with a column name
in another case (`AGE` for `age`) is invalid under the requirement's exact names, while the
legacy check is case-insensitive (`feature_engineering.sas` 63-79 and 81-107) and does not stop.
See section 5, points 3 and 4.

### Q26: lift and capture rate are missing when the validation set has no defaulter

- **Input.** A valid training file in which nobody defaulted (the witness has four rows, ids 1 to
  4, age 45, monthly income 5000, the other columns 0), any test file, seed 0. The split leaves a
  non-empty validation part (three rows selected, one not) with no defaulter.
- **What the requirement demands.** Q26, clause 2, as formalised and listed among the signed-off
  readings ("lift and capture present on all ten rows"): every row of the decile table has lift
  and capture rate non-missing.
- **What the legacy code produces.** On each decile that holds a validation applicant, capture
  rate is the decile's defaults divided by the total defaults, 0/0, and lift is the decile's
  default rate divided by the overall default rate, 0/0. SAS gives missing for both. Deciles with
  no applicant get 0, as ruling G41 fixed.
- **Evidence on real SAS.** `judge/runs/ev5_fix_Q23_nodefaulter/decile_analysis.csv`: the filled
  deciles 3, 6 and 9 have `capture_rate` and `lift` empty; the empty deciles have 0.00% and 0.00.
- **Lines.** `legacy/metrics_calculation.sas` 272 (capture rate) and 273 (lift) compute the two
  divisions; 260-261 pass them through unchanged (`else d.capture_rate`, `else d.lift`).
- **Smallest change.** At 260-261 return 0 when the inner value is missing
  (`coalesce(d.capture_rate, 0)`, `coalesce(d.lift, 0)`), or guard the divisions at 272-273 the
  same way. Whether 0 is the right value is the owner's (section 5, point 2).
- **Scope of the Lean.** The failure is proved for every choice of parameters meeting the links,
  so it does not come from a chosen split, join order or fit. The negation as proved covers
  capture rate (line 272); lift fails in the same way at line 273 and is shown by the SAS run,
  not by the Lean.
- **Check.** `prover-5`: all four points pass, with two caveats.
  - *Caveat A.* The precondition of the unit `credit_raw_clean` (the income and dependents texts
    are at most 32 characters, with no e/E/d/D) is not implied by the links, and the import of
    the witness is not exhibited, so the Lean does not show its own witness inside that
    precondition. The checker judges this does not weaken the verdict: the failure holds for
    every choice meeting the links, and an import delivering "5000" and "0", which is what
    `PROC IMPORT` gives, meets it. The missing fact, if wanted: some `importTrain` meets link (1)
    and `credit_raw_clean_precond` on every valid training table. The other unit preconditions on
    the path were checked by reading, not proved in Lean.
  - *Caveat B.* Section 5, point 2.
  - The checker read the negation's proof in full, but not the proofs of its four dependencies;
    for those it relies on the server refusing sorry and axioms.

## 3. Lemma items added

All seven are in state proved on the blueprint; no sub-goal is left unproved.

| Item | Added by | What it says | Used by |
|---|---|---|---|
| `lem:sas_feature_rows` | `prover-3` | Under the links and a valid training table, every row of the two feature tables traces to a raw training row (id and outcome kept) and has all 36 model candidates numeric and non-missing. Links (1), (4), (5) row clause. | Q14, Q22, Q24, Q26 negation |
| `lem:sas_score_rows` | `prover-7` | The validation scoring chain pairs score rows with feature rows in order, keeps id and outcome, sets the probability to 1/(1+exp(-linear predictor)), and the linear predictor is present when every term's column is. No hypothesis. | Q24 |
| `lem:sas_features_row_total` | `prover-1` | One row with income, dependents and credit lines present and zero or more, and the other base columns present, gets all 36 candidates present from `credit_features`. Posted as a sub-goal of Q14. | Q14 |
| `lem:sas_features_some` | `prover-6` | On a valid training table the features step returns a result for every seed (the input check of `feature_engineering.sas` 63-123 does not stop). Link (1). Posted as a sub-goal by `prover-10`. It is also the first half of clause 1 of Q27. | Q26 negation |
| `lem:sas_links_sat` | `prover-9` | The links can be satisfied: for every arrange, split and fit meeting links (4), (5), (6), the other parameters exist, with the four reads the identity. | Q27 negation |
| `lem:sasLinks_witness` | `prover-10` | The same statement as `lem:sas_links_sat` (reads written `fun t => t`). | Q26 negation |
| `lem:sas_split_sat` | `prover-9` | An explicit split meeting link (5): the first (7n+9)/10 rows selected. | Q27 negation |

`lem:sas_links_sat` and `lem:sasLinks_witness` are duplicates (section 4). Each negation depends
on a different one, so neither can be removed without clearing an accepted proof.

## 4. How the team worked

- **Claims.** The twelve first tasks were claimed without collision, the first ten by ten
  different teammates within the first minutes. The two Q27 tasks were taken later by teammates
  whose first task was done or waiting.
- **A task claimed three times.** `check the disproof of thm:sas_Q27` was worked in full by
  `prover-2`, `prover-4` and `prover-8`. The lead notified the three at once; each re-read the
  task, saw it unowned, and claimed it. The list ended with `prover-2` as owner. The result is
  three independent checks that agree, at three times the cost. For the Q26 check the lead
  offered the task to one teammate only, and it had one owner.
- **A lemma proved twice.** `prover-9` and `prover-10` each announced the fact that the links
  can be satisfied, under two names, within moments of each other. The lead told both to settle
  on one, and each told the other, but both proofs were accepted before the messages arrived.
- **Messages arrive late.** Teammates read their inbox between tool rounds, so relays often
  reached them after the result they concerned was already accepted. Several teammates said so.
  This is the cause of the two duplications above.
- **Messages that changed the course of a proof.**
  - `prover-9`, holding prove Q26, concluded the contract was false and passed the input to
    `prover-10` instead of disproving it itself, as rule 3 asks; that input became the disproof.
  - `prover-3` announced `lem:sas_feature_rows` early; Q14, Q24 and the Q26 negation were then
    built on it instead of reproving it.
  - `prover-6`, holding prove Q27, stopped on the refute side's candidate (empty test table),
    confirmed it by reading, and did not attempt the proof.
  - `prover-10` posted the fact it lacked as a sub-goal task; the idle `prover-6` proved it.
  - `prover-2` gave `prover-8` a working `eval_decl` call (below).
- **Where the lead stepped in.**
  - `prover-8` closed refute Q24 having evaluated nothing, because `eval_decl` failed on every
    call. The lead sent it to `prover-2` and `prover-4`, who had working calls; it then evaluated
    five candidates and the outcome did not change.
  - `prover-9` asked whether it could check the Q26 disproof. The rule bars only the author; the
    lead said no because `prover-9` had supplied the input, and others were free.
  - `prover-9` held three tasks at one time (prove Q26 waiting on the other side, refute Q27, and
    its own lemma). The lead let this stand.
  - Relays of lemmas and candidates between teammates who could not address each other.
- **Hook blocks.** One: a grep by `prover-2` that included the project's `.claude` folder was
  refused by the isolation hook. It reran the search on `migration/` only. No call of the lead's
  was blocked. The other teammates who mentioned it reported none.
- **Teammates stalled or lost.** None. The first spawn of `prover-6` failed with "Lock file is
  already being held" when the ten were started at once, and succeeded on retry.
- **Tools.**
  - `eval_decl` returns an output-schema error, not a message, when the term does not elaborate
    or the unit is called directly without a printable view. `prover-2`, `prover-6` and
    `prover-8` all hit it. The working shape is the item's `evalApply` declaration with a
    string-printing view at `Float`.
  - The proof sandbox refuses `macro` and `set_option`; the earlier draft on `thm:sas_Q14` had
    never compiled for that reason. The earlier draft on `thm:sas_Q23` called helpers it did not
    define.
  - `prover-9` replaced an earlier prover's unfinished draft on `neg:sas_Q27_neg` with its own
    proof.
- **Lead's part.** The lead created the tasks and teammates, relayed messages, and read the
  blueprint (`get_items`, `get_status`). It stated, proved and edited nothing.
- **Unexplained.** `get_items` shows a failure count of 1 on `thm:sas_Q26` and on `thm:sas_Q27`.
  Both prove-side teammates say they submitted no proof of those contracts; the lead did not
  establish whether the count comes from the flagging or from an earlier round.

## 5. For the owner to decide

1. **Is a test file with no applicant a valid input?** The Q27 disproof stands only because
   section 3 does not ask the test file to hold a row. If such a file is valid, `predict.sas`
   must change as in section 2. If it is not, `TestOK` needs a clause, the witness goes away and
   Q27 is open again. In the Lean an empty table stands for every test file without a data row:
   header only, wrong header, or wholly empty.
2. **What should lift and capture rate be when the validation set has no defaulter?** The formal
   Q26 demands them present in every case, so formally the legacy code violates it. But the
   requirement's text is silent on that case: G21 makes only the sum of capture rates conditional
   on a defaulter, G41 covers only empty deciles, and G19 leaves undefined metrics unconstrained
   for Q22. The owner may rule that they must be present (then fix the code, and say whether the
   value is 0) or that they may be missing (then Q26 changes and is open again).
3. **Should the import links say what the imports do on invalid tables?** Without that, clauses 2
   and 3 of Q27 (the code stops on invalid input) cannot be decided about the legacy code.
4. **Are the column names of section 3 case-exact?** The legacy check is case-insensitive.
5. **Floating-point overflow.** The missing probability for a very negative logit is outside
   every contract, because they are over the reals. Whether it needs a requirement is the
   owner's.
6. **`KS_Cutoff` on ties.** Seen by `prover-8` in evaluation: when the KS maximum is attained at
   two probabilities, the floating-point run reported the higher (0.9), not the lowest (0.1),
   through a last-bit difference. Q24 does not read the cutoff; this matters only if another
   requirement does.
7. **The duplicate lemma.** Whether to keep both `lem:sas_links_sat` and `lem:sasLinks_witness`
   or reconnect one negation and remove the other.
8. **Caveat A on Q26.** Whether to ask for the missing fact about `credit_raw_clean_precond`.
9. `thm:sas_Q12` and `thm:sas_Q13` still wait for the owner, as before the trial.
