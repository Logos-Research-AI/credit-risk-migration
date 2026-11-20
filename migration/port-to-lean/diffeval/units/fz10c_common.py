"""Pieces of fz_run_py_gen.py and t16_gen.py copied verbatim (fidelity pass 2026-11-20c, label compositions).

Copied rather than imported: importing t16_gen.py runs its main() (it regenerates work/t16_run.*).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import compare as cmp  # noqa: E402
import kit  # noqa: E402


# ---------------------------------------------------------------- from fz_run_py_gen.py
def nx(x: float, up: bool) -> float:
    return math.nextafter(x, math.inf if up else -math.inf)


EF = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, None]
EP = [None, 0.0, -0.0, 1.0, 0.5, nx(0.5, True), nx(0.5, False), 0.3, nx(0.3, True), nx(0.3, False), 0.4, nx(0.4, True),
      0.6, nx(0.6, False), 0.7, nx(0.7, True), 0.1, 0.9, 0.25, 0.25, 0.75, 1e-300, 5e-324, 0.1 + 1e-9, 0.1 + 1e-13,
      0.1, 0.5, 0.5, 2.0, -0.25]
ES = [None, 600.0, 850.0, 725.0, nx(725.0, True), nx(725.0, False), 612.5, 837.5, 725.0, 600.0, 1e300, -5.0, 0.0,
      -0.0, 700.0, 700.0, 650.25, 1e-300, 849.9999999999999, 600.0000000000001]
OV, OP, OS_, OT = 0, 100000, 200000, 300000


def n_rows(s: int, j: int) -> int:
    return 1 + kit.hsh(s, 1000 + j) % 9


def csv(df: pl.DataFrame) -> str:
    def cell(x):
        if x is None:
            return ""
        return str(int(x)) if x == int(x) and abs(x) < 1e15 and not (x == 0 and math.copysign(1, x) < 0) else repr(x)
    return ",".join(df.columns) + "\n" + "".join(",".join(cell(x) for x in r) + "\n" for r in df.rows())


def fs_mirror(xs: list[float]) -> float:
    """the Lean FS below, operation for operation"""
    ps: list[float] = []
    for x in xs:
        a, out = x, []
        for y in ps:
            s_ = a + y
            bb = s_ - a
            e = (a - (s_ - bb)) + (y - bb)
            if e != 0:
                out.append(e)
            a = s_
        ps = out + [a]
    r = 0.0
    for y in ps:
        r = r + y
    return r


FS = ("let FS := fun (xs : List Float) => (let ps := xs.foldl (fun (ps : List Float) (x : Float) => "
      "(let r := ps.foldl (fun (a : Float × List Float) (y : Float) => (let s := a.1 + y; let bb := s - a.1; "
      "let e := (a.1 - (s - bb)) + (y - bb); (s, if e != 0 then a.2 ++ [e] else a.2))) (x, ([] : List Float)); "
      "r.2 ++ [r.1])) ([] : List Float); ps.foldl (fun (a y : Float) => a + y) 0.0); ")
D8 = 'let d8 := fun (x : Option Float) => (match x with | none => "." | some v => toString v.toBits.toNat); '


def d8_standin(x):
    return "." if x is None else str(cmp.fbits(float(x)))


# ---------------------------------------------------------------- from t16_gen.py
def key(x):
    return None if x is None else cmp.fbits(float(x))


MK = ("let cell := fun (x : Float) => (Tabular.Cell.num (some x) : Tabular.Cell Float); "
      "let pairs := fun (L : Array Nat) => (List.range (L.size / 2)).map (fun (i : Nat) => (L[2 * i]!, L[2 * i + 1]!)); "
      "let mkR := fun (d ds : Nat) (L : Array Nat) => ((pairs L).map (fun (p : Nat × Nat) => "
      '[("default_flag", cell (Float.ofNat (p.1 % 2))), ("pd_logistic", cell (Float.ofScientific (p.1 / 2) true d)), '
      '("credit_risk_score", cell (Float.ofScientific p.2 true ds))]) : Tabular.Table Float); '
      "let mkV := fun (base d ds : Nat) (L : Array Nat) => ((List.zip (List.range (L.size / 2)) (mkR d ds L)).map "
      '(fun (q : Nat × Tabular.Row Float) => ("row_id", cell (Float.ofNat (base + q.1))) :: q.2) : Tabular.Table Float); '
      'let mkC := fun (ds : Nat) (L : List Nat) => (L.map (fun (s : Nat) => [("credit_risk_score", cell (Float.ofScientific s true ds))]) : Tabular.Table Float); ')


def dec(vals: list[float], cap: int = 13) -> int:
    for d in range(cap + 1):
        if all(cmp.fbits(float(f"{round(x * 10**d)}e-{d}")) == cmp.fbits(x) for x in vals):
            return d
    raise AssertionError("no decimal scale")


def vcodes(df: pl.DataFrame, d: int, ds: int) -> str:
    out = []
    for f, p, s in df.select("default_flag", "pd_logistic", "credit_risk_score").iter_rows():
        assert f in (0.0, 1.0) and p is not None and s is not None and p >= 0 and s >= 0
        out += [round(p * 10**d) * 2 + int(f), round(s * 10**ds)]
    return "#[" + ", ".join(map(str, out)) + "]"


def table_term(df: pl.DataFrame) -> str:
    assert all(t == pl.Float64 for t in df.dtypes), df.schema
    if df.columns == ["credit_risk_score"]:
        s = df.get_column("credit_risk_score").to_list()
        ds = dec(s)
        return f"(mkC {ds} [" + ", ".join(str(round(x * 10**ds)) for x in s) + "])"
    d, ds = dec(df.get_column("pd_logistic").to_list()), dec(df.get_column("credit_risk_score").to_list())
    if df.columns == ["default_flag", "pd_logistic", "credit_risk_score"]:
        return f"(mkR {d} {ds} {vcodes(df, d, ds)})"
    assert df.columns == ["row_id", "default_flag", "pd_logistic", "credit_risk_score"], df.columns
    rid = df.get_column("row_id").to_list()
    base = int(rid[0])
    assert all(r == base + i for i, r in enumerate(rid))
    return f"(mkV {base} {d} {ds} {vcodes(df, d, ds)})"


def dgt_in(df: pl.DataFrame) -> int:
    return cmp.digest(cmp.tokens(cmp.canon_table(df)))
