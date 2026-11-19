# eval_decl errors, 2026-11-18 (for a report to Logos)

Server: Logos MCP Staging. Blueprint `5365851c-5549-44b7-9207-4bd4c422031d` (py-credit-risk-port).
Calls made by the coordinator of carriers, 2026-11-18 (about 21:00 to 21:47 UTC).
Trust layers of the blueprint: all off (as `open_blueprint` reports).

## 1. The error

Every failing call returns, in place of a result:

```
Structured content does not match the tool's output schema: data must have required property
'item_id', data must have required property 'decl', data must have required property 'cases',
data must have required property 'elapsed_ms', data/success must be equal to constant
```

Reading: the server answered with a payload whose `success` is not `true` and which has no
`item_id`, `decl`, `cases`, `elapsed_ms`; the MCP output schema of `eval_decl` allows only
`success: true`, so the client rejects the payload and **the server's own error message is lost**.
The error is per call, not per case: it does not depend on the input.

Evidence that it is the server's refusal path, made unreadable: the same error comes back for
calls that must be refused (rows 9 and 10 below: an item that is not formalized, a `decl` that
does not exist), while a case that does not elaborate (wrong argument type, no `Repr`) comes back
normally as `"kind": "notRun"` inside a successful payload (rows 11 to 17).

**Request 1 to Logos:** declare the failure shape in the output schema of `eval_decl` (or return
the refusal as a tool error with its text), so that the reason reaches the client.

**Request 2 to Logos:** say why `eval_decl` refuses the formalized code items of rows 1 to 6.
They are `DefinitionFormalized`, `kind` definition, and their accepted Lean compiles: the same
declarations run when called from `def:zz_carrier_e`, which depends on them (section 3).

## 2. Calls made

`eval_decl(blueprint_id=5365851c-…, item_id=…, decl=…, inputs=[…])`

| # | item_id | decl | inputs | state of the item | result |
|---|---|---|---|---|---|
| 1 | `def:train_run_06_coefficients_odds` | (omitted) | `["(fun (_ : Option Float) (_ _ : Int) => \"\") (fun (_ : Option Float) (_ _ : Int) => \"\") (fun (_ : Option Float) => \"\") (fun (_ : Option Float) => \"\") (fun (_ : Float) (_ : Int) => (0.0 : Float)) (fun (x : Float) => x * x) none [] [] none []"]` | DefinitionFormalized | schema error |
| 2 | `def:train_run_12_risk_scores` | (omitted) | `["(α := Float) [] []"]`, and `["1"]` | DefinitionFormalized | schema error (both) |
| 3 | `def:train_run_12_risk_scores` | `train_run_12_risk_scores` | `["1"]` | DefinitionFormalized | schema error |
| 4 | `def:association_table`, `def:classification_table`, `def:_pairs`, `def:roc_association` | (omitted) | `["1"]` | DefinitionFormalized | schema error (each) |
| 5 | `def:train_run_02_stepwise_summary`, `def:train_run_05_association` | (omitted) | `["1"]` | DefinitionFormalized | schema error (each) |
| 6 | `def:metrics_run_01_roc_auc`, `def:metrics_run_02_ks`, `def:metrics_run_04_deciles`, `def:metrics_run_06_psi` | (omitted) | `["1"]` | DefinitionFormalized | schema error (each) |
| 7 | `def:_hl_groups_precond` | (omitted) | `["[3, 4] 7 2"]` | DefinitionFormalized, precondition (no `code`) | schema error |
| 8 | `def:metrics_run_02_ks_precond` | (omitted) | `["1"]` | DefinitionFormalized, precondition | schema error |
| 9 | `def:hosmer_lemeshow` | (omitted) | `["1"]` | DefinitionUnformalized | schema error (a refusal is expected) |
| 10 | `def:zz_carrier_e` | `no_such_decl` | `["1"]` | DefinitionFormalized | schema error (a refusal is expected) |
| 11 | `def:_hl_groups` | (omitted) | `["(α := Float) [3, 4, 5, 6] 18 2", "(α := Float) [] 0 0"]` | DefinitionFormalized | success: `[12, 6]`, `[0]` |
| 12 | `def:_hl_groups` | (omitted) | `["(α := Float) [1] \"x\" 2"]`, `["1"]` | DefinitionFormalized | success, case `notRun` (does not elaborate) |
| 13 | `def:flag` | (omitted) | `["(Pl.col (α := Float) \"x\")"]` | DefinitionFormalized | success, case `notRun` (no `Repr`) |
| 14 | `def:lt` | (omitted) | `["(.float (1.0 : Float)) (.float (2.0 : Float))"]` | DefinitionFormalized | success, case `notRun` |
| 15 | `def:le`, `def:_ratio`, `def:proc_rank_groups` | (omitted) | `["1"]` | DefinitionFormalized | success, case `notRun` |
| 16 | `def:metrics_run_07_calibration` | (omitted) | `["1"]` | DefinitionFormalized | success, case `notRun` |
| 17 | `def:zz_carrier_e` | `pr_prop_d` | `["((1 : Int) = 1) (by infer_instance)"]` | DefinitionFormalized | success, case `notRun` (see section 4) |

Rows 1 to 6 are deterministic (row 2 was repeated, same result). No pattern found among the
dependencies: `def:train_run_12_risk_scores` (refused) depends on `def:ExprOrNum`, `def:lt`,
`def:le`; `def:metrics_run_07_calibration` (runs) on `def:proc_rank_groups`, `def:sql_mean`,
`def:ExprOrNum`; `def:le` (runs) depends on `def:lt`. Rows 7 and 8 may be the documented
restriction ("only a `code_migration` item … can be evaluated": a precondition has no `code`);
the restriction is then right and only its message is lost.

## 3. Workaround that works: the carrier

`def:zz_carrier_e` (added 2026-11-18 with `add_code`, source `diffeval/carrier_e.py:13-14`,
accepted revision `5769b0b7…`) depends on the units, declares printers from each result type (at
Float) to `List Int`, and runs every unit of rows 1 to 6 (`decl` = a printer, input = the unit
call). Calls made, all `success`, each case `returned`:

| decl | unit called in the input |
|---|---|
| `pr_frame_files` | `train_run_06_coefficients_odds` with `final = none`, and with a fit of two coefficients |
| `pr_assoc` | `association_table` on three rows |
| `pr_files` | `train_run_05_association` with a fit, one effect |
| `pr_frame2` | `train_run_12_risk_scores` (a null probability; an empty validation frame) |
| `dg_frame2` | `metrics_run_01_roc_auc`, `metrics_run_02_ks`, `metrics_run_04_deciles`, `metrics_run_06_psi` |
| `dg_frame` | `metrics_run_07_calibration`, `classification_table` (pd path, intercept only) |
| `zz_carrier_e` | `_hl_groups (α := Float) [3, 4, 5, 6] 18 2` → `[12, 6]` |

## 4. Preconditions at Float

`pr_prop (p : Prop) [Decidable p]` and `pr_prop_d (p : Prop) (d : Decidable p)` in the carrier.

- `pr_prop` on a precondition applied to its arguments does not elaborate (`notRun`) for
  `_hl_groups_precond`, `train_run_06_coefficients_odds_precond`, `metrics_run_02_ks_precond`,
  `train_run_12_risk_scores_precond`: instance search does not unfold the definition.
- `pr_prop_d P (inferInstanceAs (Decidable <body of P>))` works: `_hl_groups_precond [3, 4] 7 0`
  → `[0]`, `… 7 2` → `[1]` (body `g ≠ 0`).
- **A tactic block in an input never elaborates**, also on a trivial goal:
  `pr_prop_d ((1 : Int) = 1) (by infer_instance)` is `notRun` while
  `pr_prop_d ((1 : Int) = 1) inferInstance` returns `[1]`. Worth reporting to Logos as well
  (not documented in the tool description).
- Not decidable by any instance, whatever the input: the preconditions of the metrics steps 01,
  02, 04, 06, 07 and of train step 12 contain `match … with | some (.f64 _) => True | _ => False`
  or `∃ v, lookup … = some (.f64 v)`; the step 06 precondition contains `∃ (b : List α) (c : …)`;
  the step 05 and `association_table` preconditions go through `_pairs_precond`. Evaluating them
  needs a Bool decider per precondition, a second translation; not written.
