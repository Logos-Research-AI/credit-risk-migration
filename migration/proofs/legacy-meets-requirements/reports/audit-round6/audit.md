# Audit of round 6: the SAS blueprint after the second pass

Blueprint `sas-credit-risk-spec` (`3f5df696-7c80-45cc-809f-b2881714663d`), read on 2026-11-16
between 22:17 and 22:35 UTC, after the profile refresh for G57, the second revision of
`def:SasLinks`, the corrections of rule R46 and the second restating and proving of the 34
consumers. The auditor did none of that work and changed nothing on any blueprint.

This file holds no Lean. The changed Lean is in the blueprint; the changed lines were sent to the
team lead with the summary.

## Result

No finding. Every point passes; the limits are listed at the end.

| # | Point | Verdict |
|---|---|---|
| 1 | The 34 statements equal the round 5 snapshot; all proved; status | pass |
| 2 | Every definition against the snapshot; the five changed units against R46 and x27 | pass |
| 3 | Nothing in the chain of the 26 contracts depends on the changed bodies | pass |
| 4 | Proofs of the 34 and of the three uncleared lemmas; no flag, no negation | pass, within the limits |
| 5 | The input conditions seen from `def:SasLinks` are the signed-off ones | pass |

## 1. The 34 statements

For each of `thm:sas_Q1` to `thm:sas_Q16`, `thm:sas_Q18` to `thm:sas_Q27`,
`thm:score_chains_agree`, `lem:sasLinks_witness`, `lem:sas_links_sat`, `lem:sas_split_sat`,
`lem:sas_Q27_clause1`, `lem:sas_feature_rows`, `lem:sas_features_some`,
`lem:sas_test_feature_rows`:

- state `TheoremProved`: 34 of 34;
- SHA-256 of `statement_lean` equal to `snapshot-round5.json`: 34 of 34;
- byte count equal: 34 of 34.

`get_status`: 146 items, 146 statements formalised, nothing to write, nothing waiting, no flagged
item, `verification_approved` true.

Against the round 5 snapshot one item is gone: `neg:sas_Q27_neg` (not found on the blueprint).
`thm:sas_Q27` is proved, so its negation has no place; the removal predates this pass (it was
already gone at part 1 of this audit).

## 2. The definitions

109 definitions compared by SHA-256 with the round 5 snapshot.

| Item | Against round 5 | Bytes (round 5 to now) |
|---|---|---|
| `def:SasLinks` | two comment lines differ, nothing else | 9336 to 9438 |
| `def:roc_train` | changed (R46) | 4695 to 5298 |
| `def:roc_valid` | changed (R46) | 533 to 1147 |
| `def:model_summary` | changed (R46) | 3944 to 4866 |
| `def:roc_train_precond` | changed (R46) | 891 to 653 |
| `def:roc_valid_precond` | changed (R46) | 911 to 663 |
| the other 103, among them `def:sasPipeline` and the ten units resubmitted "unchanged" | identical | |

The ten resubmitted units (`def:logistic_association`, `def:logistic_lackfit`, `def:roc_stats`,
their three preconditions, `def:validation_summary`, `def:model_performance_metrics`,
`def:sasPipeline`, and `def:SasLinks` apart from its two comments) have the hash they had.

### `def:SasLinks`

A line diff against the full text in the round 5 snapshot gives two lines, both comments:

- link (3): the comment gained "(an idealisation, ruling G55)";
- link (5): the comment gained "(at least 4 rows since ruling G57, so the validation part is not
  empty)".

No line of code differs.

### The five units of rule R46

Baseline text: the statements read at part 1 of this audit (same day, before the second pass),
whose hashes equal the round 5 snapshot. The round 5 snapshot itself holds the full text only of
the two precondition items.

| Item | What changed in the code | Is it R46 and no more |
|---|---|---|
| `def:roc_train` | The one-row table is returned only when the observations used (response and probability both present) hold at least one event and one non-event; otherwise the table with no row. The row, its label and the Area expression are as before. The helpers above it (the grouping of rule R25, the Area, the observations used) are untouched | yes |
| `def:roc_valid` | The same change, label "Validation Set" | yes |
| `def:model_summary` | One guard in front of the body: no row when `roc_train` or `roc_valid` has no row. The merge, the constants and the kept columns are as before; the merge helper above it is untouched | yes |
| `def:roc_train_precond` | The two clauses "some event with a probability" and "some non-event with a probability" are removed; the column types and "the response is missing, 0 or 1" stay | yes |
| `def:roc_valid_precond` | The same | yes |

The comments of the three units were rewritten to state R46, its evidence and what is not
represented (the order of the header of a header-only `model_summary.csv`).

### The evidence

`migration/legacy-to-lean/experiments/x27_one_class_roc.log` and the five
`x27_one_class_roc_*_model_summary.csv` files, read by the auditor:

| Case | `roc_train` | `roc_valid` | `model_summary` | `model_summary.csv` |
|---|---|---|---|---|
| A4 | 1 row | does not exist | 0 rows, 14 variables | header line only |
| B60 | 1 row | does not exist | 0 rows, 14 variables | header line only |
| D60 | 1 row | does not exist | 0 rows, 14 variables | header line only |
| C60 | does not exist | does not exist | 0 rows, 14 variables | header line only |
| E60 | does not exist | does not exist | 0 rows, 14 variables | header line only |

The log carries "ERROR: All observations have the same response. No statistics are computed."
and "ERROR: File WORK.ROC_VALID.DATA does not exist." This is the table of
`migration/legacy-to-lean/corrections-round7.md`, section 1.

### Cases tried by the auditor (`eval_decl`, Float)

`def:roc_train`:

| Input | Result | Expected by R46 |
|---|---|---|
| one event (0.8), two non-events (0.3, 0.9) | one row, "Training Set", Area 0.5 | one row; one pair concordant, one discordant |
| two events, no non-event | no row | no row |
| two non-events, no event | no row | no row |
| one event and one non-event, both probabilities missing | no row | no row |
| the table with no row | no row | no row |
| an event whose probability is missing, two non-events with a probability | no row | no row: the event is not used |
| a row with the response missing, one event (0.7), one non-event (0.2) | one row, Area 1 | one row: the first row is not used |
| one row | no row | no row |

`def:roc_valid`: two classes, one row "Validation Set" with Area 0.5; events only, non-events
only, all probabilities missing, no row, one row: each gives no row.

`def:model_summary`:

| ROC tables | Result |
|---|---|
| both with their row | one row, 14 columns, both AUC present |
| `roc_valid` with no row | no row |
| `roc_train` with no row | no row |
| neither | no row |
| `roc_train` exists with another label (rule R21) | one row, Train_AUC missing, Valid_AUC present |
| `roc_valid` exists with another label (rule R21) | one row, Valid_AUC missing, Train_AUC present |

All as R46 and the x27 table describe.

One remark, not a defect: `def:model_summary` takes any ROC table with no row as "not created".
A table that exists with no row is not told apart. The two ROC units return either no row or one
row, so the case does not arise in the program.

## 3. Does a contract depend on the changed bodies

- The code of `def:sasPipeline` and of `def:SasLinks` names none of `roc_train`, `roc_valid`,
  `model_summary` or the two preconditions (comments stripped, scripted). No item other than the
  five names them in its code.
- `def:sasPipeline` reaches `def:model_summary` through one dependency only:
  `def:validation_summary`, which lists `def:model_summary` as a dependency because the
  one-to-one merge helper is declared in that item. The code of `def:validation_summary` calls
  that helper and nothing else from the item.
- The diff of `def:model_summary` starts below the helper: the helper is textually unchanged.
  The same holds for the helpers declared in `def:roc_train` (the diff starts below them).
- `def:roc_stats`, `def:logistic_association`, `def:logistic_lackfit`,
  `def:model_performance_metrics` and their preconditions depend on the changed items but are not
  dependencies of `def:sasPipeline` or `def:SasLinks`.

So the results of the pipeline cannot have changed: no changed body is in the chain of a
contract.

## 4. The proofs

37 items: the 34 and `lem:sas_score_rows`, `lem:sas_features_row_total`,
`lem:sas_test_chain_agree`.

Method per item:

- accepted proof read with `get_items proof_lean` (23): Q2, Q3, Q4, Q5, Q7, Q8, Q9, Q10, Q11,
  Q12, Q15, Q16, Q18, Q19, Q20, Q21, Q27, `thm:score_chains_agree`, `lem:sas_split_sat`,
  `lem:sas_features_some`, `lem:sas_score_rows`, `lem:sas_features_row_total`,
  `lem:sas_test_chain_agree`;
- stored draft read with `read_scratch` because the accepted proof is over the response limit
  (14): Q1, Q6, Q13, Q14, Q22, Q23, Q24, Q25, Q26, `lem:sasLinks_witness`, `lem:sas_links_sat`,
  `lem:sas_Q27_clause1`, `lem:sas_feature_rows`, `lem:sas_test_feature_rows`. Each draft is
  complete (every line, one revision) and its size equals the size the server reported for the
  accepted proof, with a constant offset of 6 bytes. That is equality of length, not of content.

Searched in each proof, comments stripped: `sorry`, `axiom`, `native_decide`, `unsafe`,
`set_option`, `sorryAx`, `implemented_by`, `extern`, `opaque`, `ofReduceBool`, `reduceBool`,
`trustCompiler`, `admit`, `partial`, `csimp`, `macro`, `syntax`, `elab`, `run_cmd`, `#eval`,
`instance`, `bv_decide`.

| Check | Result |
|---|---|
| Forbidden word | none in 37 proofs |
| Other hits | `local notation` for two abbreviations in Q1, Q13, Q14, `lem:sas_test_feature_rows` |
| The proof restates its accepted statement | 37 of 37 (the name of the hypothesis apart) |
| `used_decls` names `sorryAx`, `Lean.ofReduceBool` or `Lean.trustCompiler` | none in 37 |
| `decide +kernel` (kernel evaluation, not `native_decide`) | Q13, Q14, Q15, Q18, Q19, Q21, Q22, Q23, `thm:score_chains_agree`, `lem:sasLinks_witness`, `lem:sas_links_sat`, `lem:sas_Q27_clause1`, `lem:sas_features_some`, `lem:sas_score_rows`, `lem:sas_test_chain_agree` |
| Classical reasoning (standard axiom) | Q6, Q24, `lem:sasLinks_witness`, `lem:sas_links_sat` |
| Lemmas called equal the declared proof dependencies | yes, except Q13 (below) |
| Every proof dependency proved | yes |
| Flagged or negated item on the blueprint | none |

Dependencies as called in the proof text: Q12 on `lem:sas_test_chain_agree` and
`lem:sas_test_feature_rows`; Q14 on `lem:sas_feature_rows` and `lem:sas_features_row_total`; Q22
on `lem:sas_feature_rows`; Q24 and Q26 on `lem:sas_feature_rows` and `lem:sas_score_rows`; Q27 on
`lem:sas_Q27_clause1`; `lem:sas_Q27_clause1` on `lem:sas_features_some`.

`thm:sas_Q13` still declares a proof dependency on `thm:sas_Q1` that its proof does not call
(known since round 4; harmless).

The three uncleared lemmas: their statements equal the round 5 snapshot, and neither statement
nor proof names `TrainOK`, `TestOK`, `InputOK`, `Fitted`, `SasLinks`, `sasPipeline` or a
requirement. `lem:sas_test_chain_agree` uses the two cell readers of the requirements only, which
do not depend on the input conditions. None of the three needs proving again.

## 5. The input conditions seen from `def:SasLinks`

`check_decl` on 58 names of the requirements from `def:SasLinks` in this blueprint and from
`thm:consistent` in the requirements blueprint `006ff04c-d34c-4a9c-b230-ccd725b1be6f`, compared
character for character by script: 58 of 58 identical. Among them `TrainOK` (with the last
conjunct "at least 4 rows"), `TestOK`, `InputOK`, `decimal12`, `decimal32`, `Pipeline`,
`MetricsTables`, `Fitted`, `Spec`, Q1 to Q16, Q18 to Q27 and the 23 helpers.

The requirements blueprint itself was audited against the previous signed-off state on the same
day (G54, then G57): only the expected conjuncts were added.

## Method

- Read-only fetches were made by three `prover` sub-agents through the Logos MCP Staging
  connector; the auditor parsed their raw tool results by script. The `eval_decl` cases and the
  reading of the x27 files were done by the auditor.
- Scripts, in this folder: `r6.py` (points 1, 2 and the uncleared lemmas), `defdiff.py` (diff of
  the five units), `deps.py` (point 3), `proofs6.py` (point 4), `reqcmp.py` (point 5),
  `snap6.py` (the snapshot). Each takes the transcript of a fetch; the paths inside are those of
  this session.
- Snapshot: `../snapshot-round6.json`, 146 items, hashes and byte counts, no Lean.

## Limits

- No tool lists the axioms a proof depends on transitively; `used_decls` gives direct
  dependencies only. "No axiom beyond the standard ones" rests on the text search and on the
  server's acceptance.
- For the 14 oversized proofs the stored draft was read, equal to the accepted proof in length
  only.
- `check_decl` prints the elaborated form, which hides implicit arguments; both sides use the
  same printer.
- `eval_decl` runs on Float and prints six decimals. The auditor used small tables of its own,
  not the 42 and 18 rows of the x27 cases; the translator's evaluation on those rows was not
  repeated.
- The sub-agent fetches rest on their transcripts being a faithful record of the tool results.
- Not looked at: the informal texts of the changed items against their Lean, and the units left
  as they are by the translator (`def:roc_stats`, `def:logistic_association`,
  `def:logistic_lackfit`: one class still excluded by precondition, no SAS run made).
