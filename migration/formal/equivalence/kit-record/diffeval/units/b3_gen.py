"""Bundle B3 differential tests (_ratio, merge_one_to_one, proc_rank_groups, proc_rank_apply_groups).

  uv run python migration/diffeval/units/b3_gen.py
      -> work/b3_ratio, b3_rank, b3_apply, b3_merge (.json + .inputs.json)
  (eval_decl each work/b3_*.inputs.json on def:zz_carrier / zz_carrier, save work/b3_*.out.txt)
  uv run python migration/diffeval/compare.py migration/diffeval/work/b3_<suite>.json migration/diffeval/work/b3_<suite>.out.txt
  uv run python migration/diffeval/receipts.py units b3

The cases are the implementers' cases (ported from their scratch generator). Conventions they
used, kept here:
- proc_rank_groups / proc_rank_apply_groups return an Int64 Series in Python and a Float64 column
  of integral values in Lean (rule R-F2I, a TODO(port) of the units): the Python result is cast
  to Float64 before the comparison.
- proc_rank_apply_groups: where Python raises IndexError the expected value is an all-null
  column of the length of x.
- a Date column is the `.cell` column of its boundary cells (null -> `Cell.num none`, a date ->
  `Cell.str (some "YYYY-MM-DD")`).
- the random sweeps are enumerated inside Lean (kit.GEN) and one digest is returned per group of
  cases (`covers` = the number of cases in the group); a group that differs is rerun case by case.
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2]))

import compare as cmp  # noqa: E402
import kit  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402

nan, inf = float("nan"), float("inf")
F2I = "Python Int64 result compared as Float64 (R-F2I, TODO(port) of the unit)"


def fcol_digest(vals) -> int:
    return cmp.digest(cmp.tok_col(cmp.canon_floats(vals)))


# ---------------------------------------------------------------- _ratio
def suite_ratio() -> Suite:
    V = [0.0, -0.0, 1.0, -1.0, nan, inf, -inf, 1e308, 5e-324, 3.0, 0.1, -7.5]
    cases = []
    for a in V:
        for b in V:
            r = sc._ratio(a, b)
            cases.append((f"ratio({a},{b})", "_ratio", -1 if r is None else cmp.fbits(r)))
    body = ("(V.flatMap (fun (a : Float) => V.map (fun (b : Float) => (match _ratio (α := Float) a b with "
            "| none => (-1 : Int) | some q => (q.toBits.toNat : Int)))))")
    s = Suite("b3_ratio")
    s.ints("let V : List Float := [" + ", ".join(lt.lean_float(v) for v in V) + "]; ", body, cases, use_kit=False)
    return s


# ---------------------------------------------------------------- proc_rank_groups
def suite_rank() -> Suite:
    s = Suite("b3_rank")
    E = [None, nan, 1.0, 2.0, 0.0, -0.0, 0.5, inf, -inf, 2.0, -3.25, None]
    NS, PES, KS = [0, 1, 2, 3, 5, 8, 13, 30, 61], [0, 50, 90, 100], [10, 20, 7, 0, -3]
    body = (f"({NS}.map (fun (n : Nat) => dg ((({PES} : List Nat).flatMap (fun (pe : Nat) => ({KS} : List Int).flatMap (fun (k : Int) => "
            "[false, true].map (fun (d : Bool) => dg (tC (proc_rank_groups (α := Float) (Pl.Col.f64 (gF (n * 7 + pe) n pe.toUInt64 3 E)) k d)))))).map (fun (x : Int) => x.toNat.toUInt64))))")
    cases = []
    for n in NS:
        ds = []
        for pe in PES:
            for k in KS:
                for d in (False, True):
                    r = sc.proc_rank_groups(pl.Series("x", kit.gF(n * 7 + pe, n, pe, 3, E), dtype=pl.Float64), k, descending=d)
                    assert r.dtype == pl.Int64
                    ds.append(fcol_digest(r.cast(pl.Float64).to_list()))
        cases.append((f"sweep n={n} (pe in {PES}, k in {KS}, descending in F/T)", "proc_rank_groups", cmp.digest(ds), {"covers": len(ds)}))
    s.ints(f"let E := {lt.lean_opt_floats(E)}; ", body, cases, gen=True)
    # all-null / all-NaN / ties / mixed, explicit
    SPEC = [[None, None, None], [nan, nan], [1.0, 1.0, 1.0, 1.0], [3.0, 1.0, 2.0, None, 2.0, nan, 1.0, 2.0, -0.0, 0.0]]
    cases = []
    for x in SPEC:
        for k in (10, 20):
            for d in (False, True):
                r = sc.proc_rank_groups(pl.Series("x", x, dtype=pl.Float64), k, descending=d)
                cases.append((f"spec {x} k={k} d={d} -> {r.to_list()}", "proc_rank_groups", fcol_digest(r.cast(pl.Float64).to_list())))
    s.ints("let XS : List (List (Option Float)) := [" + ", ".join(lt.lean_list([lt.lean_opt_float(v) for v in x]) for x in SPEC) + "]; ",
           "(XS.flatMap (fun (x : List (Option Float)) => ([10, 20] : List Int).flatMap (fun (k : Int) => [false, true].map (fun (d : Bool) => "
           "dg (tC (proc_rank_groups (α := Float) (Pl.Col.f64 x) k d))))))", cases)
    s.notes = {"proc_rank_groups": F2I}
    return s


# ---------------------------------------------------------------- proc_rank_apply_groups
def suite_apply() -> Suite:
    s = Suite("b3_apply")
    ER = [None, nan, 1.0, 2.0, 0.0, -0.0, 0.5, 2.0, -3.25, 4.0, 4.0, None]
    EX = [None, nan, 1.0, 2.0, 0.0, -0.0, 0.5, inf, -inf, -3.25, 4.0, 1.5, 3.0, -1e300, 1e300]
    NR, PR, KS, NX = [0, 1, 2, 3, 7, 12, 25, 60], [0, 40, 85, 100], [10, 20, 3], 40
    body = (f"({NR}.map (fun (n : Nat) => dg ((({PR} : List Nat).flatMap (fun (pe : Nat) => ({KS} : List Int).map (fun (k : Int) => "
            f"dg (tC (proc_rank_apply_groups (α := Float) (Pl.Col.f64 (gF (1000 + n * 7 + pe) n pe.toUInt64 2 ER)) (Pl.Col.f64 (gF (2000 + n * 7 + pe) {NX} 55 3 EX)) k))))).map (fun (x : Int) => x.toNat.toUInt64))))")
    cases, nraise, total = [], 0, 0
    for n in NR:
        ds = []
        for pe in PR:
            for k in KS:
                ref = kit.gF(1000 + n * 7 + pe, n, pe, 2, ER)
                x = kit.gF(2000 + n * 7 + pe, NX, 55, 3, EX)
                try:
                    r = sc.proc_rank_apply_groups(pl.Series("r", ref, dtype=pl.Float64), pl.Series("x", x, dtype=pl.Float64), k)
                    assert r.dtype == pl.Int64
                    ds.append(fcol_digest(r.cast(pl.Float64).to_list()))
                except IndexError:
                    ds.append(fcol_digest([None] * NX))
                    nraise += 1
        total += len(ds)
        cases.append((f"sweep n={n} (pe in {PR}, k in {KS}, 40 x values)", "proc_rank_apply_groups", cmp.digest(ds), {"covers": len(ds)}))
    print(f"apply: python raises IndexError on {nraise} of {total} sweep cases")
    s.ints(f"let ER := {lt.lean_opt_floats(ER)}; let EX := {lt.lean_opt_floats(EX)}; ", body, cases, gen=True)
    SPEC = [([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0], [0.5, 1.0, 1.5, 6.5, 12.0, 99.0, None, nan, -inf, inf, 2.0, 2.0]),
            ([nan, nan, 1.0, None, 2.0, 3.0], [0.0, 1.0, 2.5, nan, None, 5.0, inf]), ([nan], [1.0, nan, inf]), ([5.0, 5.0, 5.0], [4.0, 5.0, 6.0]), ([1.0, 2.0], [])]
    cases = []
    for ref, x in SPEC:
        for k in (10, 20):
            r = sc.proc_rank_apply_groups(pl.Series("r", ref, dtype=pl.Float64), pl.Series("x", x, dtype=pl.Float64), k)
            cases.append((f"spec {ref} {x} k={k} -> {r.to_list()}", "proc_rank_apply_groups", fcol_digest(r.cast(pl.Float64).to_list())))
    s.ints("let PS : List (List (Option Float) × List (Option Float)) := ["
           + ", ".join("(" + lt.lean_list([lt.lean_opt_float(v) for v in r]) + ", " + lt.lean_list([lt.lean_opt_float(v) for v in x]) + ")" for r, x in SPEC) + "]; ",
           "(PS.flatMap (fun (p : List (Option Float) × List (Option Float)) => ([10, 20] : List Int).map (fun (k : Int) => "
           "dg (tC (proc_rank_apply_groups (α := Float) (Pl.Col.f64 p.1) (Pl.Col.f64 p.2) k)))))", cases)
    s.notes = {"proc_rank_apply_groups": F2I + f"; Python raises IndexError on {nraise} of {total} sweep cases (empty or all-null/NaN reference): "
               "expected there = all-null column"}
    return s


# ---------------------------------------------------------------- merge_one_to_one
def lcol(s: pl.Series) -> str:
    if s.dtype == pl.Date:
        return "(Pl.Col.cell [" + ", ".join("Tabular.Cell.num none" if v is None else f"Tabular.Cell.str (some {lt.lean_str(v.isoformat())})"
                                            for v in s.to_list()) + "])"
    return lt.lean_col(s)  # a Null-dtype Series is `(Pl.Col.null n)`


def lframe_items(df: pl.DataFrame) -> str:
    return "[" + ", ".join(f"({lt.lean_str(n)}, {lcol(df.get_column(n))})" for n in df.columns) + "]"


def ccol(s: pl.Series) -> dict:
    if s.dtype == pl.Date:
        return {"type": "col", "kind": "cell", "values": [["num", None] if v is None else ["str", v.isoformat()] for v in s.to_list()]}
    return cmp.canon_series(s)


def cframe(df: pl.DataFrame) -> dict:
    return {"type": "frame", "cols": [[n, ccol(df.get_column(n))] for n in df.columns]}


def suite_merge() -> Suite:
    s = Suite("b3_merge")
    D = dt.date
    a = pl.DataFrame({"d": [D(2024, 1, 2)], "x": [1.5], "s": ["p"]})
    b = pl.DataFrame({"y": [1, 2, 3], "x": ["a", "b", None]})
    c = pl.DataFrame({"x": [True, None], "z": [nan, -0.0], "y": [None, 2.5], "d": [None, D(1960, 1, 1)]})
    z = pl.DataFrame({"q": pl.Series([], dtype=pl.Float64), "y": pl.Series([], dtype=pl.String), "d": pl.Series([], dtype=pl.Date)})
    nl = pl.DataFrame({"n": pl.Series([None, None, None], dtype=pl.Null), "x": [7, 8, 9]})
    e = pl.DataFrame()
    one = pl.DataFrame({"AUC": [0.7], "Gini": [0.4]})
    ks = pl.DataFrame({"KS": [0.5, 0.3], "cut": [0.1, 0.2]})
    psi = pl.DataFrame({"PSI": [0.01], "PSI_interpretation": ["Stable"]})
    NAMES = {"a": a, "b": b, "c": c, "z": z, "nl": nl, "e": e, "one": one, "ks": ks, "psi": psi}
    lets = "".join(f"let f{n} : Pl.Frame Float := {lframe_items(f)}; " for n, f in NAMES.items())
    CASES = [[], ["a"], ["a", "b"], ["b", "a"], ["a", "b", "c"], ["c", "b", "a"], ["z"], ["z", "b"], ["b", "z"], ["z", "z"], ["e"], ["e", "b"],
             ["e", "e"], ["nl", "b"], ["b", "nl"], ["nl", "a"], ["a", "a"], ["one", "ks", "psi"], ["c", "c", "a", "z", "b"], ["ks", "one", "c"], ["c", "ks"]]
    terms, cases = [], []
    for k, fs in enumerate(CASES):
        terms.append("[" + ", ".join("f" + n for n in fs) + "]")
        r = sc.merge_one_to_one(*[NAMES[n] for n in fs])
        cases.append((f"{k:02d} merge({', '.join(fs)}) -> {dict(r.schema)} h={r.height}", "merge_one_to_one", cframe(r)))
    s.digest_body(lets, "(([" + ", ".join(terms) + "] : List (List (Pl.Frame Float))).map (fun (fs : List (Pl.Frame Float)) => "
                  "dg (tR (merge_one_to_one (α := Float) fs))))", cases, gen=False, table=True)
    # whole values (tokens): a Null-dtype column that has to be padded (the implementers' "mergegap",
    # outside the unit's precondition) and the merge of a, b, c
    gap = [pl.DataFrame({"n": pl.Series([None], dtype=pl.Null)}), b]
    s.tokens("let g0 : Pl.Frame Float := " + lframe_items(gap[0]) + "; let g1 : Pl.Frame Float := " + lframe_items(gap[1]) + "; ",
             "gap: Null-dtype column padded from 1 to 3 rows", "merge_one_to_one", "tR (merge_one_to_one (α := Float) [g0, g1])", "frame",
             cframe(sc.merge_one_to_one(*gap)), gen=False, expect_diff=True,
             note="padding a Null-dtype column: Python pads it to 3 nulls, Lean keeps `.null 1` (Pl.Col.append has no case for two "
                  "Null columns); documented in the unit as TODO(port), excluded by def:merge_one_to_one_precond")
    s.tokens("".join(f"let f{n} : Pl.Frame Float := {lframe_items(NAMES[n])}; " for n in "abc"),
             "tok: merge(a, b, c)", "merge_one_to_one", "tR (merge_one_to_one (α := Float) [fa, fb, fc])", "frame",
             cframe(sc.merge_one_to_one(a, b, c)), gen=False, cells=True)
    return s


if __name__ == "__main__":
    for mk in (suite_ratio, suite_rank, suite_apply, suite_merge):
        mk().write()
