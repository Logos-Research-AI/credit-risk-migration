# Rulebook amendments (queued inside loops, applied between batches by the orchestrator)

| # | Source | Amendment | Applied |
|---|---|---|---|
| A1 | pilot (credit_features) | A precondition item holds exactly one declaration and may not have an unused parameter | process note in the implementer brief |
| A2 | first differential run | `eval_decl` calls only declarations of the evaluated item; bit-exact evaluation runs from sink items carrying a helper | RULEBOOK DEV-006 |
| A3 | train batch | Unary minus has no shared helper; the two units that need it define it locally | none needed |
| A4 | review 1 of train.sas, F1 | R25: ROCEPS is sqrt(2^-53), not 1e-8. Evidence: the reference Association table has 280 tied pairs; 1e-8 gives 275 | `def:roc_train` edited, dependents re-accepted |
| A5 | review 1 of train.sas, F3 | R29: a Hosmer-Lemeshow block is the run of probabilities within 1e-6 of its first; the free parameter `sameBlock` is removed. Evidence: reference partition | `def:logistic_lackfit` rewritten |
| A6 | review 1 of train.sas, F2 | PROC LOGISTIC OUTPUT writes `_LEVEL_`. Evidence: the reference log warns "never been referenced" for `_LEVEL_` only in the validation DROP | `def:logit_scored_train_output` edited; comment of `def:risk_scores_train_clean` corrected |
| A7 | review 1 of feature engineering, F5 | Standing assumption: numeric cells are finite and not NaN | RULEBOOK section 2 |
| A8 | reviews 1 and 2 of feature engineering | Every unit whose Lean relies on column types, text syntax, a permutation or a count bound has a precondition item, as its predict.sas twin has; `INPUT(..., BEST32.)` reads at most 32 characters (excluded by precondition, not modelled) | precondition items added by the fixer |
| A9 | review 1 of feature engineering, F9 | Rule numbers in `def:credit_raw_clean` comments differ from the RULEBOOK table | mapping note in RULEBOOK section 2 (the item was not edited: an edit of the root clears every other item) |
| A10 | reviews 2 of train.sas and 1, 2 of metrics_calculation.sas | Standing assumption on table shape: exact names, expected types, no pre-existing variable with the name of one the step creates or retains | RULEBOOK section 2 |

Recurring-failure rule (kit rule 6): the missing-precondition finding appeared in three reviews
(feature engineering twice, train once). It was moved upstream as A8 rather than fixed one unit
at a time.
