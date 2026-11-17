"""Review (port-translator-2) of def:classification_table (written by port-translator-6), update of
2026-11-17: one declaration, intercept-only branch, level 1.000 as 1 + 1e-12 on every fit.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/rv_ct_gen.py
      -> work/rv_ct.json + work/rv_ct.inputs.json (ONE eval_decl input, on def:zz_carrier_c)

Inputs of the reviewer (none from the writer's suite), hand-made:
  intercept only (x = one column of ones), the three call forms (y, x, fit) / (X, y, pd) / pd=:
    leave-one-out means 1/6 and 1/3; all ones (every mean 1: the single level 1.000); means 0.4 and
    0.6 (equal to printed levels); means 0 and 0.1; two rows (means 0 and 1: the 51 levels);
    all zeros (every mean 0)
  two columns: probabilities given; a fit given; a fit whose linear predictor is +-40 on some rows
    (probability 1 in double precision, last level 1.000)
Python side: the real classification_table. Its np.linalg.inv, matrix products, einsum and log1p
are recomputed here with the same numpy expressions to give the Lean routines as tables keyed on
the digest of the arguments' bits (as t18_gen does).
Compared: the returned frame column by column (name, kind, values); CorrectNonevents and
IncorrectNonevents are Float64 columns in the Lean (R-F2I, TODO(port) of the unit), so the Python
columns are cast to Float64 before the digest.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import numpy as np  # noqa: E402
import polars as pl  # noqa: E402
import t18_gen as t  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402

UNIT = "classification_table"
T = {"matvec": {}, "matmul": {}, "inv": {}, "einsum": {}, "log1p": {}}


def record(x: np.ndarray, p: np.ndarray, beta: np.ndarray | None) -> None:
    """sas_compat.py:1278-1287 with the same numpy expressions."""
    with np.errstate(all="ignore"):
        if beta is not None:
            eta = x @ beta
            T["matvec"][(t.mw(x), t.vw(beta))] = eta
            p = sc._expit(eta)
        else:
            for v in p:
                T["log1p"][t.fb(-v)] = t.fb(np.log1p(-v))
        w = p * (1.0 - p)
        xw = x * w[:, None]
        mm = x.T @ xw
        T["matmul"][(t.mw(x.T), t.mw(xw))] = mm
        try:
            vi = np.linalg.inv(mm)
        except np.linalg.LinAlgError:
            return
        T["inv"][(t.mw(mm), 0)] = vi
        T["einsum"][(t.mw(x), t.mw(vi))] = np.einsum("ij,jk,ik->i", x, vi, x)


def arr1(v) -> str:
    return f"(Np.NDArray.d1 (FL {t.ul(v)}))"


def arr2(m) -> str:
    return f"(Np.NDArray.d2 ({t.ull(m)}.map FL))"


def fit_of(names, beta) -> sc.LogisticFit:
    k = len(beta)
    return sc.LogisticFit(list(names), np.array(beta, dtype=np.float64), np.eye(k), -1.0, 3, True)


def build():
    cases: list[tuple] = []
    terms: list[str] = []
    info: dict = {}

    def add(label: str, y, x, *, pd=None, fit=None, form: str):
        y = np.array(y, dtype=np.float64)
        x = np.array(x, dtype=np.float64)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if form == "fit":  # classification_table(y, x, fit)
                df = sc.classification_table(y, x, fit)
                record(x, None, fit.beta)
                lean = f"{arr1(y)} {arr2(x)} (some (Sum.inl {t.lean_fit(fit)})) none"
            elif form == "inventory":  # classification_table(X, y, pd)
                pd = np.array(pd, dtype=np.float64)
                df = sc.classification_table(x, y, pd)
                record(x, pd, None)
                lean = f"{arr2(x)} {arr1(y)} (some (Sum.inr {arr1(pd)})) none"
            else:  # classification_table(y, x, pd=pd)
                pd = np.array(pd, dtype=np.float64)
                df = sc.classification_table(y, x, pd=pd)
                record(x, pd, None)
                lean = f"{arr1(y)} {arr2(x)} none (some {arr1(pd)})"
        assert df.schema["CorrectNonevents"] == pl.Int64 and df.schema["IncorrectNonevents"] == pl.Int64
        dfc = df.with_columns(pl.col("CorrectNonevents").cast(pl.Float64), pl.col("IncorrectNonevents").cast(pl.Float64))
        labs = t.labels_fd(label, dfc)
        cases.extend((a, UNIT, int(b)) for a, b in zip(labs, t.fd(dfc), strict=True))
        terms.append(f"CT {lean}")
        info[label] = (form, df.height, df.get_column("ProbLevel").to_list()[:1] + df.get_column("ProbLevel").to_list()[-1:],
                       df.get_column("CorrectEvents").to_list()[-1], df.get_column("IncorrectEvents").to_list()[-1])

    def ones(n):
        return [[1.0]] * n

    def mean(y):
        return [sum(y) / len(y)] * len(y)

    def icpt_fit(y):
        m = sum(y) / len(y)
        return fit_of(["Intercept"], [float(np.log(m) - np.log1p(-m))])

    y1 = [0, 1, 0, 0, 1, 0, 0]
    add("intercept, means 1/6 and 1/3, pd=", y1, ones(7), pd=mean(y1), form="keyword")
    add("intercept, means 1/6 and 1/3, fit", y1, ones(7), fit=icpt_fit(y1), form="fit")
    y2 = [1, 1, 1, 1, 1]
    add("intercept, all ones, pd= 0.9", y2, ones(5), pd=[0.9] * 5, form="keyword")
    y3 = [1, 0, 1, 0, 1, 0]
    add("intercept, means 0.4 and 0.6, (X, y, pd)", y3, ones(6), pd=mean(y3), form="inventory")
    y4 = [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
    add("intercept, means 0 and 0.1, fit", y4, ones(11), fit=icpt_fit(y4), form="fit")
    y5 = [1, 0]
    add("intercept, two rows, pd=", y5, ones(2), pd=mean(y5), form="keyword")
    y6 = [0, 0, 0, 0]
    add("intercept, all zeros, (X, y, pd) 0.2", y6, ones(4), pd=[0.2] * 4, form="inventory")
    y7 = [1, 0, 0, 0, 1, 1, 0, 1, 0, 1]
    add("intercept, means 4/9 and 5/9, pd=", y7, ones(10), pd=mean(y7), form="keyword")

    xa = [[1.0, v] for v in (0.5, -1.25, 2.0, 0.0, 3.5, -0.75, 1.5, 2.25, -2.0, 0.25)]
    ya = [0, 0, 1, 0, 1, 0, 1, 1, 0, 1]
    pda = [0.31, 0.07, 0.72, 0.2, 0.93, 0.12, 0.6, 0.78, 0.04, 0.25]
    add("two columns, pd=", ya, xa, pd=pda, form="keyword")
    add("two columns, (X, y, pd)", ya, xa, pd=pda, form="inventory")
    add("two columns, fit", ya, xa, fit=fit_of(["Intercept", "v"], [-0.5, 0.875]), form="fit")
    xs = [[1.0, v] for v in (40.0, 40.0, -40.0, -40.0, 0.5, -0.5, 1.0, -1.0)]
    ys = [1, 1, 0, 0, 1, 0, 0, 1]
    add("two columns, fit with probabilities 1 and 0 in double", ys, xs, fit=fit_of(["Intercept", "v"], [0.0, 1.0]), form="fit")

    kvv = lambda d: "[" + ", ".join(f"({a}, {b}, {t.ul(out)})" for (a, b), out in d.items()) + "]"  # noqa: E731
    kmm = lambda d: "[" + ", ".join(f"({a}, {b}, {t.ull(out)})" for (a, b), out in d.items()) + "]"  # noqa: E731
    routines = (
        f"let MV : List (Int × Int × List UInt64) := {kvv(T['matvec'])}; "
        f"let EQ : List (Int × Int × List UInt64) := {kvv(T['einsum'])}; "
        f"let MM : List (Int × Int × List (List UInt64)) := {kmm(T['matmul'])}; "
        f"let IV : List (Int × Int × List (List UInt64)) := {kmm(T['inv'])}; "
        "let matvec := fun (a : List (List Float)) (b : List Float) => KVV MV (MW a) (VW b); "
        "let einsum := fun (a b : List (List Float)) => KVV EQ (MW a) (MW b); "
        "let matmul := fun (a b : List (List Float)) => KMM MM (MW a) (MW b); "
        "let inv := fun (a : List (List Float)) => KMM IV (MW a) 0; "
        f"let log1p := T1 [{', '.join(f'({a}, {b})' for a, b in T['log1p'].items())}]; "
        "let CT := fun (y x : FloatArray_ Float) (fit : Option (LogisticFit Float ⊕ FloatArray_ Float)) "
        "(pd : Option (FloatArray_ Float)) => (FD (classification_table inv matmul matvec einsum log1p y x fit pd) : List Int); ")
    lets = t.W + t.BI + t.OF + t.TS + t.TC + t.FD + t.FL + t.MW + t.KEYED + t.MKFIT + routines
    body = "(([" + ", ".join(terms) + "] : List (List Int)).flatten)"
    s = Suite("rv_ct")
    s.item, s.decl = "def:zz_carrier_c", "zz_carrier_c"
    s.ints(lets, body, cases, use_kit=False)
    s.notes = {UNIT: f"review by port-translator-2, inputs of the reviewer (form, levels, first and last level, CorrectEvents and "
                     f"IncorrectEvents at the last level): {info}; inv / matmul / matvec / einsum_q / log1p as tables of numpy's "
                     "results; the two nonevent count columns compared as Float64 (R-F2I)"}
    s.write()
    for k, v in info.items():
        print(k, v)
    print("input chars", (HERE.parent / "work" / "rv_ct.inputs.json").stat().st_size)


if __name__ == "__main__":
    build()
