# diffeval — the judge: run the Lean and the Python on the same inputs, compare bit for bit

Run everything from the workspace root with `uv run python migration/diffeval/<script>`.
`eval_decl` is an MCP tool: only an agent can call it. So a run has three steps.

1. **Generate** — a script builds a `Suite` (`suite.py`): the Lean input terms and the expected
   Python results. `Suite.write()` saves `work/<name>.json` (inputs, cases, expected, generator)
   and `work/<name>.inputs.json` (the calls to make: `item`, `decl`, `inputs`).
2. **Evaluate** — read `work/<name>.inputs.json`; for each call run
   `eval_decl(blueprint_id, item_id=item, decl=decl, inputs=inputs)`; write the `output` of every
   input, in order, one per line (newlines removed), to `work/<name>.out.txt`. An input that did
   not run is the line `ERROR <message>` (a call returns each input separately: one input that
   does not elaborate does not stop the others).
3. **Compare** — `uv run python migration/diffeval/compare.py migration/diffeval/work/<name>.json migration/diffeval/work/<name>.out.txt`
   prints every case that is not PASS with `path: expected … got …` and writes `work/<name>.result.json`.
   Statuses: `PASS`, `FAIL`, `ULP` (only with `ulp_tol`), `ERROR` (input did not run / malformed
   output), `XFAIL` / `XPASS` (a case given `expect_diff=True` differs / no longer differs).

## Helpers

| File | What it gives |
|---|---|
| `leanterm.py` | Python value → Lean term at `α := Float`: `lean_float` (`(Float.ofBits N)`, exact), `lean_int`, `lean_str`, `lean_opt_floats`, `lean_col` (Series → `Pl.Col`, a Null-dtype Series → `(Pl.Col.null n)`), `lean_frame_let` / `lean_frame` (DataFrame → `Pl.Frame Float`, see "Frames and dot notation"), `lean_table` (DataFrame → `Tabular.Table Float`) |
| `kit.py` | the Lean lambdas: `DUMP_COL/FRAME/TABLE` (nested lists of names, kinds, `Option UInt64/Int/Bool/String`), the token/digest kit `KIT` / `KIT_NOTABLE`, the seeded generators `GEN` (`gF`, `gI`, mirrored in Python as `kit.gF`, `kit.gI`). Every match on a column is exhaustive over `.f64 / .int / .bool / .str / .cell / .null` |
| `suite.py` | `Suite(name, carrier="identity")` with `digest / digest_body / tokens / ints / bits / dump` — the ways to get a result back (below) |
| `compare.py` | `canon_frame / canon_series / canon_table / canon_floats / canon_nulls` (Python result → canonical), `parse_lean`, `diff` (exact: float bits, null ≠ NaN, kind, names, order, lengths), `digest`, `tokens`, CLI |
| `receipts.py` | `receipts.py units <bundle>` → `receipts/units.tsv` (one row per unit); `receipts.py` → `receipts/prelude.tsv` |
| `units/<bundle>_gen.py` | the unit tests of a bundle (below) |
| `dsl.py` | dual expressions (`add(col("a"), 0.5)` carries the polars `Expr` and the `Pl` term of RULEBOOK §2.3) and data columns generated on both sides; a Python `None` literal / a missing `otherwise` is `Pl.litNull` |
| `validate_comparer.py` | planted mismatches; `receipts/comparer_validation.tsv` (74 pairs, 0 wrong verdicts) |
| `prelude_suites.py`, `diag_suite.py`, `explain.py` | the prelude test: suites (carrier `cumsum`; small inputs in `dump` mode), minimal reproductions, check that each diagnosis accounts for the whole difference (`receipts/explained.tsv`) |

## Getting a Lean value back exactly (a `Float` prints with 6 decimals: never print one)

CARRIER is the suite's carrier, a `List Int → List Int` declared by the evaluated item:

| `Suite(..., carrier=)` | item / decl | Output | Use |
|---|---|---|---|
| `"identity"` (default) | `def:zz_carrier` / `zz_carrier` | the list itself | units: the item depends on both preludes and on every unit |
| `"cumsum"` | `def:FloatArray_` / `Np.cumsumInt` | running sums; `compare.py` takes the differences back | the prelude suites (no unit in scope) |

The carrier of each input is recorded in `work/<name>.json` (`"carrier"`); `compare.py` un-cumsums
only the inputs marked `cumsum` (and the suites written before the field existed).

| Mode | Runs on | Use |
|---|---|---|
| `digest` / `digest_body` | CARRIER | `(KIT GEN <lets> [dg (tR frame1), dg (tC col2), dg (tA table3)])`: one 64-bit digest per case; hundreds of cases per call. A mismatch only says "differs": rerun that case as `tokens` on a small input. |
| `tokens` | CARRIER | `(KIT <lets> tk (tR frame))`: the whole value of one case, decoded and compared with paths. `cells=True` when the value holds `.cell` (Date) columns. |
| `ints` | CARRIER | `(KIT <lets> <body : List Int>)`: one integer per case, compared with the integer the generator computed — a Bool (`if b then 1 else 0`), the bits of a float (`(x.toBits.toNat : Int)`), an `Option Float`, a record tokenised by hand (`dg [..]` against `compare.digest([..])`). `use_kit=False` leaves the kit out. |
| `bits` | CARRIER | a `List Float` (an `Np` result) without the kit. |
| `dump` | `def:ExprOrNum` / `Pl.zipB` | `DUMP_FRAME (<lets> [frame1, frame2]) [()]`: the whole value as nested lists. PRELUDE TERMS ONLY: that item depends on no unit (and `Np` is not in scope), so a unit's result cannot be dumped — use `tokens`. |

`Float.toBits` returns `0x7FF8000000000000` for every NaN, so NaN payloads and signs are not
compared. Integer dtypes of polars are all the kind `int`.

### Null-dtype columns

The polars dtype Null (`pl.lit(None)`, `then(None)`, a missing `otherwise`, `pl.Series([None, None])`)
is the prelude column `Pl.Col.null n` (n nulls). In the harness it is its own kind `"null"`:
`lean_col` renders `(Pl.Col.null n)`, `canon_series` gives `{"kind": "null", "values": [None]*n}`,
the token is `[6, n]`, the dump is `("null", [], [none, …], [], [])`. It is NOT equal to a
Float64 column of n nulls: the comparison reports `….kind: expected f64 got null` (planted in
`validate_comparer.py`, both directions, in dump / digest / tokens). In a `Tabular.Table` a
Null-dtype value is a numeric missing cell (`Tabular.Cell.num none`).

### Frames and dot notation

`([("x", …)] : Pl.Frame Float).select […]` does NOT elaborate: the ascription elaborates to a
`List` and `.select` is looked up in `List`. Bind the frame with its type instead:

```python
lets = lt.lean_frame_let("f", df)          # 'let f : Pl.Frame Float := [("x", (Pl.Col.f64 […])), …]; '
term = 'tR (f.select [(sas_round (.expr (Pl.col (α := Float) "x"))).pos])'
```

`lt.lean_frame(df)` gives the same thing inline, `(let f_ : Pl.Frame Float := […]; f_)`, which can be
followed by `.select` / `.withColumns` / `.groupByAgg` or passed as an argument. When you write a
frame by hand, write `let f : Pl.Frame Float := […]; ` (not `let f := ([…] : Pl.Frame Float); `).

Lean pitfalls met while building this (they cost a failed call each, the tool only says "did not
elaborate"): parenthesise and annotate every lambda (`(fun (i : Nat) => …)`); ascribe the type of a
`match` whose result type is not known (`(match … : T)`); a `match` on a `Pl.Col` must list all six
constructors (or end with `| _ => …`): a missing `.null` arm does not elaborate; do not mix
`>>>`/`<<<` with `+ - %` in one expression (bind the shift with `let k : UInt64 := u >>> 52`); a
name used by a `let` must be defined before it; `decl` must be declared in the item itself
(`zz_carrier` only on `def:zz_carrier`, `Pl.zipB` only on `def:ExprOrNum`).

## Testing a unit of the blueprint

`eval_decl` resolves `decl` only among the declarations of the item's OWN Lean, but the input
terms may use everything the item depends on. The item `def:zz_carrier` (decl `zz_carrier`, the
identity on `List Int`, source `carrier.py`) depends on the two preludes and on every unit: every
mode of the table above except `dump` runs through it, and it is the default of `Suite`. If
`eval_decl` cannot see a unit, connect it (`connect(item_id="def:zz_carrier", depends_on=["def:<unit>"])`)
and, if that cleared the carrier, re-submit it unchanged (see `prompts/common.md`).

Convention: one generator per bundle, `migration/diffeval/units/<bundle>_gen.py`, which writes its
suites to `work/<bundle>_<suite>.json`. In every case the `primitive` field is the NAME OF THE
UNIT under test: the receipt is built from it.

```python
# migration/diffeval/units/bx_gen.py
import sys
from pathlib import Path
import polars as pl
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parents[2]))
import compare as cmp, leanterm as lt
from suite import Suite
from credit_risk import sas_compat as sc

df = pl.DataFrame({"x": [1.5, None, float("nan"), -0.5]})
s = Suite("bx_round")                                      # carrier: def:zz_carrier
s.digest('let c := fun (n : String) => Pl.col (α := Float) n; ' + lt.lean_frame_let("f", df),
         [("select", "sas_round", 'tR (f.select [(sas_round (.expr (c "x"))).pos])',
           cmp.canon_frame(df.select(sc.sas_round(pl.col("x")))))],
         gen=False, table=False)
s.ints("", "[((_TWO52 (α := Float)).toBits.toNat : Int)]", [("bits", "_TWO52", cmp.fbits(sc._TWO52))], use_kit=False)
s.notes = {"sas_round": "…"}                               # optional: note of the unit's receipt row
s.write()
```

1. `uv run python migration/diffeval/units/bx_gen.py` → `work/bx_round.json`, `work/bx_round.inputs.json`
   (`[{"item": "def:zz_carrier", "decl": "zz_carrier", "inputs": ["(let mx := …)", "([…])"]}]`).
2. `eval_decl(item_id="def:zz_carrier", decl="zz_carrier", inputs=[…])`; save the two outputs,
   one per line, as `work/bx_round.out.txt` (here two lists of one integer each).
3. `uv run python migration/diffeval/compare.py migration/diffeval/work/bx_round.json migration/diffeval/work/bx_round.out.txt`
   prints `bx_round: 2 cases  PASS=2`, or `FAIL bx_round/select [sas_round] … digest: expected … got …`.
4. `uv run python migration/diffeval/receipts.py units bx` reads every `work/bx_*.result.json` and
   appends one row per unit to `receipts/units.tsv`
   (`unit	cases	differences	status	note	generator`; a row of the same unit and generator is
   replaced, so a re-run does not duplicate). `receipts.append_unit(…)` appends one row by hand.

Extra fields of a case (the optional last dict of a case tuple, or keyword arguments of `tokens`):
- `expect_diff=True, note="…"`: a difference that is known and explained. The case is `XFAIL`
  while it differs (`XPASS` when it no longer does); the unit's row is `KNOWN-DIFF` and its note
  lists the explanations. Use it only for a difference that has been reported.
- `covers=k`: the case is one digest over k results enumerated inside Lean (a sweep): the row
  counts k cases.
- `ulp_tol=n`: finite floats of the same sign within n ulps are reported as `ULP`, not `FAIL`.

Status of a row: `ERROR` > `DIFF` (a difference not marked expected) > `XPASS` > `KNOWN-DIFF` > `PASS`.

When Python raises where the Lean returns a value, give the expected value explicitly (an integer
that Lean cannot return, or the value the unit documents) and say so in the note; never drop the case.

Existing generators: `units/b1_gen.py`, `units/b3_gen.py`, `units/b4_gen.py`.

## The prelude suites

`prelude_suites.py`, `diag_suite.py` build their suites with `Suite(name, carrier="cumsum")`
(`def:FloatArray_` / `Np.cumsumInt`, both preludes in scope, no unit) and `dump` inputs on
`def:ExprOrNum` / `Pl.zipB` (the small hand-made inputs: the whole value comes back). `receipts.py`
(no argument) turns the nine results into `receipts/prelude.tsv`
(`primitive	cases	differences	status	note`, one row per primitive). That receipt describes the
preludes at the time the nine suites were last run together: after a change of `def:ExprOrNum` or
`def:FloatArray_`, regenerate and re-run all nine (and `diag`, `diag2`, `diag3`) before reading it.
Last run: against the frozen preludes of RULEBOOK v3.

- A recorded limit of the model (RULEBOOK §6) is a case built with `lim(note, under_diagnosis)`:
  `expect_diff` plus the value the prelude must return if the limit is the whole difference. Its
  row is `KNOWN-LIMIT` and the note cites RULEBOOK §6. The primitive name says which inputs are
  limited (`abs(-0.0)`, `median(zeros of both signs)`, `min(Int64 input)`, …); the plain name
  (`abs`, `median`, `min`) is tested on inputs outside the limit and must PASS.
- Any other difference is `DIFF`: its note (in `receipts.NOTES`) says what differs; a `DIFF` row
  without a note is printed `UNEXPLAINED`.
- `explain.py` → `receipts/explained.tsv`: every case that is not PASS, with the paths that differ
  from Python and, for a recorded limit, whether the Lean output EQUALS the value under the
  diagnosis (`yes`: the limit accounts for the whole difference; `NO`: something else differs too).
