# Corrections, round 7: one-class ROC tables (rule R46) and the G57 text of the links

Applied to the blueprint `sas-credit-risk-spec` (`3f5df696-7c80-45cc-809f-b2881714663d`) on
2026-11-16 by the SAS translator.

This file describes the changes in words. It does not hold the old and new Lean: this role may
not save Lean to a local file. The Lean is in the blueprint (item ids below); the changed lines
are in the message sent to the team lead with this report.

## 1. Why

Experiment x27 (`experiments/x27_one_class_roc.*`): the real feature_engineering.sas then the
real train.sas, a new session per case.

| Case | Training part | Validation part | `work.roc_train` | `work.roc_valid` | `work.model_summary` | `model_summary.csv` |
|---|---|---|---|---|---|---|
| A4 (4 rows) | 3 rows, both classes | 1 row | 1 row, Area 0.5 | not created | 0 rows, 14 variables | header only |
| B60 | 42, both classes | 18, no defaulter | 1 row, Area 0.76392961876832 | not created | 0 rows, 14 variables | header only |
| D60 | 42, both classes | 18, all defaulters | 1 row, same Area | not created | 0 rows, 14 variables | header only |
| C60 | 42, no defaulter | 18, both classes | not created | not created | 0 rows, 14 variables | header only |
| E60 | no defaulter anywhere | no defaulter | not created | not created | 0 rows, 14 variables | header only |

Before this round the Lean returned one row with a missing Area for a one-class table and one
row of `model_summary`, and excluded the case by precondition. A validation part of one class
is valid input.

## 2. Items changed

| Item | Change |
|---|---|
| `def:roc_train` | Returns the one-row table (ROCModel, Area) when the rows used (response and probability both present) hold at least one event and one non-event; otherwise the table with no row, which stands for "no table" (the convention of rule R39). The Area computation and the helpers of rule R25 are untouched |
| `def:roc_valid` | The same, for the validation table |
| `def:model_summary` | Returns the table with no row when `roc_train` or `roc_valid` has no row; otherwise as before. The case of rule R21 (a table that exists and whose WHERE= selects no row) is kept |
| `def:roc_train_precond`, `def:roc_valid_precond` | The two clauses "at least one event" and "at least one non-event" are removed; the column types and "default_flag is missing, 0 or 1" stay. Their texts say so |
| `def:SasLinks` | Text: one sentence after link (5) for ruling G57. Lean: one comment on link (5). Nothing else |

Not represented: the header-only `model_summary.csv` lists `Valid_AUC` last when `roc_valid` is
the missing table; a table with no row carries no column in the model. Stated in the Lean
comment of `def:model_summary` and in rule R46.

## 3. Items resubmitted with the Lean they had

Each was cleared by the changes above and resubmitted unchanged. Method: one string of a comment
was replaced on the stored draft and then put back, so the accepted Lean is the stored draft as
it was.

- `def:logistic_association`, `def:logistic_association_precond`
- `def:logistic_lackfit`, `def:logistic_lackfit_precond`
- `def:roc_stats`, `def:roc_stats_precond`
- `def:validation_summary`
- `def:model_performance_metrics`
- `def:sasPipeline`
- `def:SasLinks` (after its G57 revision)

## 4. Evaluation (eval_decl, Float)

| Unit | Rows | Lean | SAS |
|---|---|---|---|
| `roc_train` | A4 training (3 rows) | one row, Area 0.5 | one row, Area 0.5 |
| `roc_train` | B60 training (42 rows of the real file) | one row, Area 0.763930 | one row, 0.76392961876832 |
| `roc_train` | C60 / E60 training (42 rows, every probability missing) | no row | not created |
| `roc_valid` | A4 validation (1 row) | no row | not created |
| `roc_valid` | B60 validation (18 rows, no defaulter) | no row | not created |
| `roc_valid` | D60 validation (18 rows, all defaulters) | no row | not created |
| `roc_valid` | the B60 training rows (two classes) | one row, Area 0.763930 | (same rows as above) |
| `model_summary` | A4: `roc_train` one row, `roc_valid` none | no row | 0 rows |
| `model_summary` | C60: neither ROC table | no row | 0 rows |
| `model_summary` | both ROC tables with one row, B60's metrics | one row, 14 columns | not run in x27 |
| `model_summary` | a ROC table that exists with another label (rule R21) | one row, Train_AUC missing | x13, x15 (earlier) |

The evaluation prints six decimals, so the two-class Areas are compared to that precision, not
to the bit. I did not re-run the earlier differential evaluation on the reference data.

## 5. State of the blueprint afterwards

146 items, 112 formalised, every definition formalised. Statements to write, 34: the 26
contracts (`thm:sas_Q1` to `thm:sas_Q16`, `thm:sas_Q18` to `thm:sas_Q27`),
`thm:score_chains_agree`, and `lem:sasLinks_witness`, `lem:sas_links_sat`, `lem:sas_split_sat`,
`lem:sas_Q27_clause1`, `lem:sas_feature_rows`, `lem:sas_features_some`,
`lem:sas_test_feature_rows`. No lemma outside these 34 was cleared.

## 6. Left as it is

- `def:roc_stats`, `def:logistic_association`, `def:logistic_lackfit` and their preconditions
  have the same pattern (a missing value, one class excluded by precondition). No run was made
  for them, so they were not changed.
- Training part of one class (C60, E60): the fit itself fails; no model, no
  `model_coefficients.csv`, training scores with a missing probability, validation scores with a
  header only. The Lean takes the fit as a total parameter. With the owner for a ruling.
