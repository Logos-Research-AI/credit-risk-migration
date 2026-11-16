# Rulebook amendment queue (applied between batches by the orchestrator)

## Batch 1 — after the stress test (applied 2026-11-10, RULEBOOK v2, prelude revisions)
| # | Source | Rule / prelude line indicted | Evidence | Change |
|---|---|---|---|---|
| A1 | pilot implementer | §2.3 `e + 0.0` = operand | on a 1-row column polars adds (`sas_round(-0.3)` literal gives +0.0) | prelude `addCol`/`subCol` scalar-zero rule; `e + 0.0` translated as an ordinary `add` |
| A2 | diffeval D2 | `numBin` in add/sub | `0.0 + col`, `col + 0`, `0.0 - col`, `col - (-0.0)`, `col + agg(=0)` keep/negate the column | same as A1 |
| A3 | diffeval D3 | `Col.ite` + `litOptF none` for None | `when(..).then(1)` is Int, String branch lost | `Col.null` dtype, `Pl.litNull`, ite takes the other branch's dtype |
| A4 | diffeval D10 | `Np.rint` | `np.round(-0.0004, 3)` is -0.0 | `rint` odd |
| A5 | diffeval D1, D7, D11 | abs / median / np.sort signed zero | not expressible in RealLike | recorded limits (§6) |
| A6 | diffeval D4–D6, D8, D9 | Int64 inputs of abs/floor/sign/sumHorizontal/min/max; filter/cumSum in agg | dtype only / unused | stated as Float64-only / select-only (§2.3) |
| A7 | inventory Q1 | Convention 1 × `div` | zero divisor gives null in Python, `some 0` on ℝ | R-DIV0 |
| A8 | inventory Q2 | no rule for `**` | `x ** 2` ≠ `x * x` on 574 of 400,000 values | parameter `pow2` |
| A9 | inventory | `math.*`, Python `/` raise | OverflowError / ValueError / ZeroDivisionError | "Python raises" rule (preconditions) |
| A10 | inventory Q6 | `medians : Option (Table α)` | Int32 key joined to Int32 key | `medians : Option (Pl.Frame α)` |
| A11 | inventory Q3, Q4, Q7 | LinAlgError; union-typed `fit`; flag with no effect | — | §3 notes |
| A12 | inventory silences | item variants, mask filters, sort/group_by without maintain_order, ndarray.mean, column_stack… | — | rows added to §2.3 / §2.4 |
| A13 | pilot implementer | `full` for 2-operand reductions; float variables as operands | — | §2.3 rows |
| A14 | harness | `eval_decl` resolves only the item's own names | — | carrier item `def:zz_carrier`; `prompts/common.md` |

## Batch 2 — applied 2026-11-10 as RULEBOOK v3 (prelude items B5, B13 NOT applied: recorded limits) (bakeoff diff inspector, `stress-test/bakeoff_diff.md`; 15 rows: 6 rulebook right, 0 native right, 7 both defensible, 2 both wrong — both already fixed or recorded in batch 1)
| # | Source | Rule indicted / silence | Evidence | Change |
|---|---|---|---|---|
| B1 | inspector R1 | §2.2: module constant defined by an expression (`2.0**52`) | `2.0**52 == 4503599627370496.0` | constant = decimal literal of the value Python computes; `pow2` only for run-time `x ** 2` |
| B2 | inspector R2 | §2.6: zero-row table at a stage boundary | `Pl.ofTable [] = []` has no columns; Python on a zero-row Float64 frame still runs | every `run` precondition requires each input table to be non-empty and well-formed (recorded limit) |
| B3 | inspector R3 | §4 preconditions: frame wording | pilot precondition excludes a Boolean `default_flag` on which Python runs | fixed wording; comment for every input excluded although Python does not raise |
| B4 | inspector R4 | testing of `+ 0.0` | 1-row / multi-row / literal give 0.0 / -0.0 / 0.0 | diffeval: units with a scalar-zero add are tested on all three |
| B5 | B3 implementer | prelude `Col.append (.null a) (.null b)` returns `.null a` | merge of a 1-row Null column with a 3-row frame: Python Null × 3, Lean `.null 1` | prelude: `.null x, .null y => .null (x + y)` (apply with the next prelude batch; `merge_one_to_one_precond` then drops its second clause) |
| B6 | B3 implementer | a null in a `.cell` (Date) column: which `Cell`; `Col.isNull` never true | no Date column goes through a padding or null test in the pipeline | record as limit in §6 |
| B7 | B3 implementer | a `pl.Series` parameter's dtype | — | §4: the unit's precondition states the column kind; the body uses `asF64` |
| B8 | B3 implementer | diffeval kit `tC` has no `.null` case | — | harness fix |
| B9 | B4 reviewers | §4 trailer form | units disagree on `[high]` vs `high`; preconditions have none | trailer is exactly `-- PORT STATUS: confidence=high todos=0`; precondition items carry no trailer; header is `-- credit_risk/<file>:<lines>` |
| B10 | B3 reviewer 1 | zero-width frames with height (`df.drop(all)`) | polars shape (3, 0) | recorded limit in §6 |
| B11 | B4 reviewer 2 | frame-level `drop_nulls`, Series `.cast(pl.Float64)` not in §2.3 | — | rows added |
| B12 | B1 reviewer 1 | expression helpers (`lt`…`sas_round`, `flag`) have no precondition for the column dtypes on which polars raises or keeps another dtype | String operands raise; `flag` of an Int64 column stays Int64 | §4: an expression helper cannot see dtypes; the dtype requirement (Boolean condition for `flag`, numeric operands for comparisons, Float64 for abs/floor/sign/min/max) is stated in the precondition of the unit that evaluates the expression (the `run` steps) |
| B13 | B2 implementer | prelude `sumHorizontal` adds a length-1 zero operand (literal 0.0 / null literal) to a column; polars does not | `sum_horizontal(lit(0.0), col)` keeps `-0.0` | NOT applied to the prelude (a prelude change clears every accepted unit; no call site passes a literal to `sas_sum`): recorded limit in §6; DECISION: the prelude is frozen from here unless a `run` cannot be stated without a change. B5 (`Col.append` on Null columns) likewise stays a precondition clause |
| B14 | B2 implementer | a literal passed to `sql_*` inside `group_by().agg`; integer-only operands of `sas_min`/`sas_max`; Int64 input of `sql_min`/`sql_max` | dtype / broadcast differences, none reached by the package | recorded limits in §6 |

## Batch 3 — applied 2026-11-10 as RULEBOOK v4
| # | Source | Rule indicted / silence | Evidence | Change |
|---|---|---|---|---|
| C1 | B2 reviewer | limits list §6 | aggregate / bare-column operand of `sql_*`, `div`, `sas_log` inside `agg`; Boolean input of `sql_sum`; String columns are parsed (not raised) by `cast(pl.Float64)` | add to recorded limits; run-step preconditions exclude String operands explicitly |
| C2 | B7/B8 reviewer 1 | §3: position of a parameter that replaces a Python path parameter | `def:run` keeps `split_ids` in its Python position, `def:run_py_py` puts `medians` first | a table / frame / parsed-file parameter that stands for a Python path parameter takes that parameter's position (`input_dir` → what is read from it; `output_dir` dropped); routine and format parameters come first in §3 order |
| C3 | B6 / B7B8 reviewers | preconditions of joins, rename, drop | polars raises DuplicateError on a `_right` suffix clash, ColumnNotFound on rename/drop of a missing column | every step with a join / rename / drop states it in its precondition |

## Batch 4 — applied 2026-11-10 (limits only; preludes frozen)
| # | Source | Rule indicted / silence | Evidence | Change |
|---|---|---|---|---|
| D1 | prelude receipt regeneration | `Col.null` has no arm in `Col.fillNull`, `addCol`/`numBin`, `cmpBin` (String), `boolsOf`, `castI64`, `sum`, `mean` | 16 cases in suite `ff` (receipts/prelude.tsv, explained.tsv): e.g. `pl.lit(None).fill_null("x")` is String `["x"]` in polars, an empty Float64 column in the model; `NC.sum()` is null in polars, 0.0 in the model | recorded limit in §6; every `then(None)` / `otherwise(None)` / `pl.lit(None, …)` site of the package has a typed other branch (grep), so no unit reaches it; open item for the user (a prelude fix clears all 146 items) |

## Batch 5 — applied 2026-11-11 (limits only; preludes frozen; after the second B2 review)
| # | Source | Rule indicted / silence | Evidence | Change |
|---|---|---|---|---|
| E1 | B2 reviewer 2, F1 | §6 row `groupSum`/`groupMean`: Kahan in every `group_by().agg` | `df.sort("g").group_by("g").agg(sql_sum(a))` on `a=[0.1,0.2,0.3]`: polars 0.6000000000000001, model 0.6; unsorted frames agree | recorded limit (key with the sorted flag); not reachable in the package |
| E2 | B2 reviewer 2, F2 | §6 silent on `exp`/`log` last bit | `sas_log(2.851207288661306)`, `sas_exp(0.3573744013859572)`: 1 ulp between the Lean evaluator and polars | recorded as outside the model; receipts annotated |
| E3 | B2 reviewer 2, F3 | `full : Bool` covers every operand count | 9 operands, 2 or 3 threads: a value neither `full` gives, varying run to run; 1 to 8 operands match | recorded limit; precondition on `sas_sum` pending the user's decision |

## Batch 6 — applied 2026-11-12 (re-translation after commit 7927af7)
| # | Source | Rule indicted / silence | Evidence | Change |
|---|---|---|---|---|
| F1 | server | §2.5 "helper `def`s placed above the unit" | the server now refuses a statement with more than one declaration | helpers are local `let` functions inside the unit's def |
| F2 | user brief | §2.2 float literals | `_TIE_EPS = math.nextafter(math.sqrt(2.0**-53), 1.0)` is one binary64 value | a constant the code computes as one specific binary64 value is written as that exact value: an integer (NatCast) divided by a power of two, or its exact decimal |
| F3 | implementers | §2.3 / §2.4 silent | `Expr.forward_fill`, `.filter(mask).sum()` in `with_columns`, `Series.slice`, `concat(how="vertical_relaxed")` (36 dtype pairs run on polars 2.1.0), integer `np.sort` / `np.searchsorted`, `gg[i] = g`, 3-argument `min`, `float / int` | translated as local helpers with evaluation evidence (`diffeval/receipts/units_7927af7.tsv`) |
| F4 | implementer | §6 limit "padding a Null-dtype column in `merge_one_to_one`" | the unit no longer goes through `Col.append` | limit no longer applies to this unit; new limits: Float64 to String and Date casts under vertical_relaxed (TODO(port), excluded by precondition) |

## Batch 7 — applied 2026-11-16 as RULEBOOK v5, §2.7 (the port as changed on 2026-11-16; preludes still frozen)
| # | Source | Rule indicted / silence | Evidence | Change |
|---|---|---|---|---|
| G1 | lead, decision 1 | §2.6 result of a `run`; §1 "raise → precondition" for the designed stops | the port prints ERROR and raises `ValueError` after removing earlier results | result is `Option`; the stop is inside the function |
| G2 | scoping | removal of earlier result files | `unlink(missing_ok=True)` loops | stated in the `run` item's comment, with what `none` implies |
| G3 | lead, decision 2 | inputs that may be absent | `exists()` tests, `try` around the import | `Option` parameters, table in §2.7 |
| G4 | lead, decisions 3 and 4 | zero-row test file; header probe | ruling G44: a header-only test file is valid input; `Pl.ofTable [] = []` | `cs_test : Option (List (String × Bool) × Table α)`; predict result as triples (DEV-013, to be confirmed) |
| G5 | scoping | input checks; Unicode case mapping | E07: `"ß".upper()` is `SS`, polars the same | one unit per check; ASCII by precondition |
| G6–G13 | scoping | polars calls not in the prelude | E07 | local helpers with the stated behaviour |
| G14–G17 | scoping | `//`, `math.fsum`, array `** 2`, builtin `max`/`min` with a float | E07 | `Int.fdiv`; parameter `fsum`; `x * x`; written out |
| G18 | scoping | `_SE_EPS`, `_SQRTBIG` | E07 hex values | exact quotient; decimal literal |
| G19 | scoping | medians file written and read | port | parameter `income_medians` replaces `medians` |
| G20 | harness | carriers | five carrier items added 2026-11-16 | one per group |
