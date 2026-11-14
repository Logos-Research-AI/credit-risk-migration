# Stress test (kit step 2): bakeoff and pilot

Units: `credit_features` (feature_engineering.sas 126-202), `risk_scores_train` (train.sas 212-244),
`decile_analysis` (metrics_calculation.sas 190-206). Together they reach the inventory classes
MISSING, DOMAIN, ROUNDING, CHAR_LENGTH, AGGREGATE, ROW_ORDER, ALIAS.

## Bakeoff

Translator A follows the rulebook (the accepted blueprint items). Translator B (separate
context, smaller model) saw only the SAS source and the foundation, never `migration/`. B's
text is disposable and was not kept. Each difference is a verdict on a rule.

| # | Difference | A (rulebook) | B (no rules) | SAS evidence | Verdict |
|---|---|---|---|---|---|
| 1 | Overflow of `+ - * /` | missing (R2) | the infinite value is kept | X10: `1e308*10` is `.` | R2 is load-bearing. Keep. |
| 2 | `ROUND` half-way tolerance | documented fuzz (R23) | exact comparison of the fraction with 0.5 | X05: 2.4999999999999996 rounds to 3; X11 thresholds | R23 is load-bearing. Keep. |
| 3 | PROC SQL `SUM`/`MEAN` | parameter `agg` (R17) | left fold in input order; mean = sum / count | X13: neither holds | R17 is load-bearing. Keep; B's choice is exactly the convenient Lean the brief warns about. |
| 4 | Column absent / text where a number is expected | reads as missing, excluded by precondition | reads as missing, noted as a decision | SAS would not compile | Same Lean; rule R8 plus precondition confirmed. |
| 5 | Everything else (missing comparisons, Boolean assignment, `SUM()`/`MIN()`/`MAX()` functions, truthiness, division by zero, `LOG`, grade F on missing score, unfolded `base_rate + 0.02`, column order by `Row.set`, GROUP BY order with the missing group first) | same | same | X10, X12, X13 | Rules agree with an independent reading. No change. |

No rule was found wrong. Rules 1 to 3 are the ones an unguided translator gets wrong; they are
the places where the two independent translations could otherwise have agreed on a wrong
answer.

## Pilot

The production pipeline (implementer in a separate context on a smaller model, then two
adversarial reviewers, then a fixer) ran first on `credit_features`. Graded on obedience:

- Used only `Sas.*` helpers in scope; no helper copied or re-invented. PASS.
- One `let r := Sas.setNum ...` per SAS assignment, in source order; output column order equals
  the reference CSV header. PASS.
- Looked rows up in the inventory and listed them. PASS.
- Added a precondition item; found that the server allows one declaration per precondition
  and rejects unused parameters. Recorded as amendment A1 (process note, not a SAS rule).
- Evaluated two reference rows and one missing-value row. PASS.

Amendments queued from the stress test: A1 (precondition shape), A2 (a unit can only be
evaluated through `Sas.Eval.apply` from an item whose own Lean declares the helper: evaluation
of bit patterns is run from sink items), A3 (unary minus has no shared helper; it is defined
locally by the two units that need it).
