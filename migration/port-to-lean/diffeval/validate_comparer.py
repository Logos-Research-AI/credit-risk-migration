"""Planted mismatches: the comparer must catch each one, and pass the identical pair.

  uv run python migration/diffeval/validate_comparer.py gen     -> work/validation.json (+ .inputs.json)
  (run the inputs with eval_decl, save the outputs to work/validation.out.txt, one per line)
  uv run python migration/diffeval/compare.py migration/diffeval/work/validation.json migration/diffeval/work/validation.out.txt
  uv run python migration/diffeval/validate_comparer.py check   -> receipts/comparer_validation.tsv
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import polars as pl

import compare as cmp
import leanterm as lt
from suite import WORK, Suite

HERE = Path(__file__).parent
NAN = float("nan")


def base() -> pl.DataFrame:
    return pl.DataFrame(
        {"a": [1.5, 0.0, NAN, None], "i": [1, -2, None, 4], "b": [True, None, False, True],
         "s": ["x\"y", None, "é\n,[", "none"]},
        schema={"a": pl.Float64, "i": pl.Int64, "b": pl.Boolean, "s": pl.String})


def plants() -> list[tuple[str, pl.DataFrame, bool]]:
    b = base()

    def seta(idx, v):
        vals = b.get_column("a").to_list()
        vals[idx] = v
        return b.with_columns(pl.Series("a", vals, dtype=pl.Float64))

    return [
        ("identical", b, True),
        ("one_ulp", seta(0, math.nextafter(1.5, 2.0)), False),
        ("neg_zero_vs_zero", seta(1, -0.0), False),
        ("nan_vs_null", seta(2, None), False),
        ("null_vs_nan", seta(3, NAN), False),
        ("int_vs_float64_column", b.with_columns(pl.col("i").cast(pl.Float64)), False),
        ("swapped_rows", b[[1, 0, 2, 3]], False),
        ("swapped_columns", b.select("i", "a", "b", "s"), False),
        ("renamed_column", b.rename({"b": "B"}), False),
        ("missing_row", b.head(3), False),
        ("string_differs", b.with_columns(pl.Series("s", ["x\"y", None, "é\n,[", "None"])), False),
        ("null_vs_empty_string", b.with_columns(pl.Series("s", ["x\"y", "", "é\n,[", "none"])), False),
        ("bool_differs", b.with_columns(pl.Series("b", [True, False, False, True])), False),
        ("int_differs", b.with_columns(pl.Series("i", [1, 2, None, 4])), False),
    ]


def _shared(b: pl.DataFrame):
    """Lean lets for the base columns / rows, and renderers of a plant that reuse them (keeps
    the eval_decl inputs short; every changed column or row is rendered by leanterm)."""
    cols = {n: lt.lean_col(b.get_column(n)) for n in b.columns}
    brows = lt.lean_rows(b)
    lets_f = "".join(f"let c{k} : Pl.Col Float := {cols[n]}; " for k, n in enumerate(b.columns))
    lets_t = "".join(f"let r{k} : Tabular.Row Float := {r}; " for k, r in enumerate(brows))

    def frame(df):
        items = []
        for n in df.columns:
            t = lt.lean_col(df.get_column(n))
            ref = [f"c{k}" for k, m in enumerate(b.columns) if cols[m] == t]
            items.append(f"({lt.lean_str(n)}, {ref[0] if ref else t})")
        return "([" + ", ".join(items) + "] : Pl.Frame Float)"

    def table(df):
        items = [f"r{brows.index(r)}" if r in brows else r for r in lt.lean_rows(df)]
        return "([" + ", ".join(items) + "] : Tabular.Table Float)"

    return lets_f, lets_t, frame, table


def gen():
    s = Suite("validation")
    exp_f, exp_t = cmp.canon_frame(base()), cmp.canon_table(base())
    exp_c = cmp.canon_series(base().get_column("a"))
    ps = plants()
    lets_f, lets_t, frame, table = _shared(base())
    # table plants: the int-vs-float plant is NOT a table difference (a table has numeric cells only)
    table_same = {"identical", "int_vs_float64_column"}
    s.dump(lets_f, "frame", [(f"dump_frame/{n}", n, frame(df), exp_f, {"must_pass": ok}) for n, df, ok in ps])
    core = ("identical", "one_ulp", "neg_zero_vs_zero", "nan_vs_null", "int_vs_float64_column", "swapped_rows",
            "swapped_columns", "renamed_column", "missing_row")
    tp = [p for p in ps if p[0] in core]
    s.dump(lets_t, "table", [(f"dump_table/{n}", n, table(df), exp_t, {"must_pass": n in table_same}) for n, df, ok in tp])
    colp = [p for p in ps if p[0] in ("identical", "one_ulp", "neg_zero_vs_zero", "nan_vs_null", "null_vs_nan", "swapped_rows", "missing_row")]
    s.dump("", "col", [(f"dump_col/{n}", n, lt.lean_col(df.get_column("a")), exp_c, {"must_pass": ok}) for n, df, ok in colp]
           + [("dump_col/int_vs_float64_column", "int_vs_float64_column", lt.lean_col(pl.Series([1.0, 2.0])),
               cmp.canon_series(pl.Series([1, 2])), {"must_pass": False})])
    s.digest(lets_f + lets_t,
             [(f"digest_frame/{n}", n, f"tR {frame(df)}", exp_f, {"must_pass": ok}) for n, df, ok in tp]
             + [(f"digest_table/{n}", n, f"tA {table(df)}", exp_t, {"must_pass": n in table_same}) for n, df, ok in tp[:3]],
             gen=False)
    for n, df, ok in [p for p in ps if p[0] == "swapped_columns"]:
        s.tokens(lets_f, f"tokens_frame/{n}", n, f"tR {frame(df)}", "frame", exp_f, gen=False, must_pass=ok)
    # ---- the old carrier (Np.cumsumInt, running sums) must still be undone correctly
    s.use_carrier("cumsum")
    s.digest(lets_f, [(f"cumsum_digest_frame/{n}", n, f"tR {frame(df)}", exp_f, {"must_pass": ok}) for n, df, ok in tp[:4]],
             gen=False, table=False)
    for n, df, ok in [p for p in ps if p[0] in ("identical", "one_ulp")]:
        s.tokens(lets_f, f"cumsum_tokens_frame/{n}", n, f"tR {frame(df)}", "frame", exp_f, gen=False, must_pass=ok)
    s.use_carrier("identity")
    # ---- Null-dtype column (`Pl.Col.null n`) against an all-null Float64 column, both directions
    N3, F3 = pl.Series("n", [None] * 3, dtype=pl.Null), pl.Series("n", [None] * 3, dtype=pl.Float64)
    N2 = pl.Series("n", [None] * 2, dtype=pl.Null)
    I3 = pl.Series("k", [1, 2, 3])
    nullp = [("null_identical", N3, N3, True), ("null_lean_vs_float64_allnull_python", N3, F3, False),
             ("float64_allnull_lean_vs_null_python", F3, N3, False), ("null_length_differs", N2, N3, False)]
    s.dump("", "col", [(f"dump_col/{n}", n, lt.lean_col(lean), cmp.canon_series(py), {"must_pass": ok}) for n, lean, py, ok in nullp])
    fr_ = lambda c: pl.DataFrame([I3.head(c.len()), c])  # noqa: E731
    s.dump("", "frame", [(f"dump_frame/{n}", n, lt.lean_frame(fr_(lean)), cmp.canon_frame(fr_(py)), {"must_pass": ok}) for n, lean, py, ok in nullp])
    s.digest("", [(f"digest_col/{n}", n, f"tC {lt.lean_col(lean)}", cmp.canon_series(py), {"must_pass": ok}) for n, lean, py, ok in nullp]
             + [(f"digest_frame/{n}", n, f"tR {lt.lean_frame(fr_(lean))}", cmp.canon_frame(fr_(py)), {"must_pass": ok}) for n, lean, py, ok in nullp],
             gen=False, table=False)
    for n, lean, py, ok in nullp[:2]:
        s.tokens("", f"tokens_frame/{n}", n, f"tR {lt.lean_frame(fr_(lean))}", "frame", cmp.canon_frame(fr_(py)), gen=False, must_pass=ok)
    # ---- ints mode (one integer per case)
    s.ints("", "[if true then 1 else 0, ((Float.ofBits 4609434218613702656).toBits.toNat : Int), dg (tC (Pl.Col.null 3)), (-7 : Int)]",
           [("ints/identical_bool", "identical", 1), ("ints/identical_bits", "identical", 4609434218613702656),
            ("ints/digest_null_vs_float64", "null_lean_vs_float64_allnull_python", cmp.digest(cmp.tokens(cmp.canon_series(F3))), {"must_pass": False}),
            ("ints/int_differs", "int_differs", 7, {"must_pass": False})])
    for c in s.cases:
        c.setdefault("must_pass", True)
    # ---- frame terms and dot notation (README "Frames and dot notation"): the helper's term and a
    # let-bound frame must elaborate under `.select`; (checked separately: the ascription form `([...] : Pl.Frame Float).select` does not elaborate)
    b = base()
    sel = cmp.canon_frame(b.select("a"))
    s.digest(lt.lean_frame_let("fb", b),
             [("digest_frame/dot_on_lean_frame", "identical", f'tR ({lt.lean_frame(b.select("a", "i"))}.select [(Pl.col (α := Float) "a").pos])', sel, {"must_pass": True}),
              ("digest_frame/dot_on_let_frame", "identical", 'tR (fb.select [(Pl.col (α := Float) "a").pos])', sel, {"must_pass": True})],
             gen=False, table=False)
    s.write()


def check():
    suite = json.loads((WORK / "validation.json").read_text())
    res = json.loads((WORK / "validation.result.json").read_text())
    rows, bad = ["plant\tchannel\tmust\tcomparer\tok\tfirst_difference"], 0
    for case, r in zip(suite["cases"], res, strict=True):
        must = "PASS" if case["must_pass"] else "FAIL"
        ok = r["status"] == must
        bad += not ok
        first = "" if not r["diffs"] else "{}: expected {} got {}".format(*r["diffs"][0])
        chan = case["id"].split("/")[1]
        rows.append(f"{case['primitive']}\t{chan}\t{must}\t{r['status']}\t{'ok' if ok else 'WRONG'}\t{first}")
    (HERE / "receipts").mkdir(exist_ok=True)
    (HERE / "receipts" / "comparer_validation.tsv").write_text("\n".join(rows) + "\n")
    print(f"{len(rows) - 1} planted pairs, {bad} wrong verdicts -> receipts/comparer_validation.tsv")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(gen() if sys.argv[1] == "gen" else check())
