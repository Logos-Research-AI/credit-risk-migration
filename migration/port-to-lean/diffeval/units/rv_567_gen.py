"""Review (port-translator-2) of the update of 2026-11-17 to def:train_run_05_association,
def:train_run_06_coefficients_odds, def:train_run_07_hl (written by port-translator-3): the
printed files are written only `if final_effects:`.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/rv_567_gen.py
      -> work/rv_567.json + work/rv_567.inputs.json (ONE eval_decl input)

Inputs of the reviewer (none from the writer's suite): three hand-made fit_scored frames (distinct
probabilities; probabilities with ties; one constant probability, as an intercept-only model
gives) and two hand-made final fits (two effects in an order other than the fit's, one name longer
than 20 characters; the intercept alone). Each with final_effects empty and not empty.
Python side: the source lines train.py:292-328, :334-375, :380-414 executed as they stand, with the
real association_table / hosmer_lemeshow / chi2_sf, the formatters as the injective encoding of
their arguments (t18_gen.ENCODERS) and write_sas_csv recorded.
Lean side: the three units; formatters = the same encoding; chi2 = table of the real values;
pow2 = x * x (asserted here equal to Python's `** 2` on every value squared).
"""
from __future__ import annotations

import math
import random
import sys
import textwrap
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import numpy as np  # noqa: E402
import polars as pl  # noqa: E402
import t18_gen as t  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402
from credit_risk import train  # noqa: E402

SRC = Path(train.__file__).read_text().splitlines()
CHI2: set[tuple[int, int, int]] = set()


def run_lines(first: int, last: int, ns: dict) -> list[tuple[str, pl.DataFrame]]:
    code = textwrap.dedent("\n".join(SRC[first - 1:last]))
    writes: list[tuple[str, pl.DataFrame]] = []

    o_chi2 = sc.chi2_sf

    def chi2(x, df):
        r = o_chi2(x, df)
        CHI2.add((t.fb(x), int(df), t.fb(r)))
        return r

    proxy = types.SimpleNamespace(
        association_table=sc.association_table, hosmer_lemeshow=sc.hosmer_lemeshow, chi2_sf=chi2, Z975=sc.Z975,
        write_sas_csv=lambda df, path, formats=None: writes.append((Path(path).name, df.clone())), **t.ENCODERS)
    sc.chi2_sf = chi2  # hosmer_lemeshow calls it inside sas_compat
    try:
        full = {"sas_compat": proxy, "pl": pl, "np": np, "math": math, "output_dir": Path("out"), **ns}
        exec(compile(code, f"train.py:{first}-{last}", "exec"), full)  # noqa: S102
    finally:
        sc.chi2_sf = o_chi2
    return writes, full


def frames() -> dict[str, pl.DataFrame]:
    rng = random.Random(20261117)
    n = 40
    p1 = sorted(rng.uniform(0.02, 0.95) for _ in range(n))
    rng.shuffle(p1)
    y1 = [1.0 if rng.random() < p else 0.0 for p in p1]
    p2 = [round(rng.uniform(0.05, 0.9), 1) for _ in range(n)]
    y2 = [1.0 if rng.random() < p else 0.0 for p in p2]
    y3 = [1.0 if i % 4 == 0 else 0.0 for i in range(n)]
    p3 = [sum(y3) / n] * n
    mk = lambda y, p: pl.DataFrame({"default_flag": y, "pd_logistic": p}, schema={"default_flag": pl.Float64, "pd_logistic": pl.Float64})  # noqa: E731
    return {"distinct": mk(y1, p1), "ties": mk(y2, p2), "constant": mk(y3, p3)}


def lean_frame(df: pl.DataFrame) -> str:
    return ("(mkFS " + t.ul(df.get_column("default_flag").to_list()) + " " + t.ul(df.get_column("pd_logistic").to_list()) + ")")


def lstrs(xs) -> str:
    return "[" + ", ".join(t.lstr(x) for x in xs) + "]"


def build():
    terms: list[str] = []
    cases: list[tuple] = []
    info: dict = {}

    def expect(label, unit, ws, extra_lab=(), extra=()):
        exp = list(extra) + [len(ws)] + [x for n, df in ws for x in t.tdn(n, df)]
        lab = list(extra_lab) + ["number of files"] + [s for n, df in ws for s in t.labels_tdn(n, df)]
        assert len(exp) == len(lab)
        cases.extend((f"{label}: {a}", unit, int(b)) for a, b in zip(lab, exp, strict=True))
        info[label] = [(n, df.height) for n, df in ws]

    fr = frames()
    lets_fr = ""
    for name, df in fr.items():
        lets_fr += f"let F_{name} := {lean_frame(df)}; "
        for fe in (["some_effect"], []):
            tag = "effects" if fe else "no effect"
            try:
                ws5, _ = run_lines(292, 328, {"fit_scored": df, "final_effects": fe})
            except Exception as e:  # noqa: BLE001
                info[f"05 {name} / {tag}"] = f"Python raises {type(e).__name__}: outside the precondition, not evaluated"
            else:
                expect(f"05 {name} / {tag}", "train_run_05_association", ws5)
                terms.append(f"A5 F_{name} {lstrs(fe)}")
            try:
                ws7, ns7 = run_lines(380, 414, {"fit_scored": df, "final_effects": fe})
            except Exception as e:  # noqa: BLE001
                info[f"07 {name} / {tag}"] = f"Python raises {type(e).__name__}: outside the precondition, not evaluated"
            else:
                for _, _size, o1, e1, o0, e0 in ns7["hl_table"].iter_rows():
                    for v in (float(o1) - e1, float(o0) - e0):
                        assert v**2 == v * v
                expect(f"07 {name} / {tag}", "train_run_07_hl", ws7)
                terms.append(f"A7 F_{name} {lstrs(fe)}")

    long_name = "a_variable_name_of_thirty_chars"
    fits = {
        "two effects": (sc.LogisticFit(["Intercept", long_name, "x2"], np.array([-1.5, 0.25, -0.75]),
                                       np.array([[0.04, 0.001, -0.002], [0.001, 0.01, 0.0005], [-0.002, 0.0005, 0.09]]),
                                       -31.25, 6, True), ["x2", long_name], [2, 1]),
        "intercept only": (sc.LogisticFit(["Intercept"], np.array([-2.0]), np.array([[0.25]]), -20.5, 4, True), [], []),
    }
    lets_fit = ""
    probes = []
    for k, (name, (fit, fe, fi)) in enumerate(fits.items()):
        intercept = float(fit.beta[0])
        ws6, ns6 = run_lines(334, 375, {"final": fit, "final_effects": fe, "final_index": fi, "intercept": intercept})
        for idx in [0, *fi]:
            b, se = float(fit.beta[idx]), math.sqrt(float(fit.cov[idx, idx]))
            assert (b / se) ** 2 == (b / se) * (b / se)
            if idx != 0:
                probes += [(f"{name} idx {idx}", a, math.exp(a)) for a in (b, b - sc.Z975 * se, b + sc.Z975 * se)]
        mc = ns6["model_coefficients"]
        expect(f"06 {name}", "train_run_06_coefficients_odds", ws6,
               [f"model_coefficients{s[len('mc'):]}" for s in t.labels_fd("mc", mc)], t.fd(mc))
        lets_fit += f"let G{k} := {t.lean_fit(fit)}; "
        terms.append(f"A6 G{k} {lstrs(fe)} [{', '.join(str(i) for i in fi)}] (Float.ofBits {t.fb(intercept)})")
    for lab, a, r in probes:
        cases.append((f"probe Float.exp vs math.exp: {lab}", "train_run_06_coefficients_odds", t.fb(r)))
        terms.append(f"[bi (Float.exp (Float.ofBits {t.fb(a)}))]")

    chi2 = f"let chi2 := T2 [{', '.join(f'({a}, ({d}), {b})' for a, d, b in sorted(CHI2))}]; "
    lets = (t.W + t.BI + t.OF + t.TS + t.TC + t.FD + t.TX + t.TD + t.FL + t.FMT + t.KEYED + t.MKFIT + chi2
            + "let pow2 := fun (x : Float) => x * x; "
            + 'let mkFS := fun (y p : List UInt64) => ([("default_flag", Pl.Col.f64 ((FL y).map some)), '
              '("pd_logistic", Pl.Col.f64 ((FL p).map some))] : Pl.Frame Float); '
            + lets_fr + lets_fit
            + "let OUT := fun (o : List (String × Tabular.Table Float)) => ((o.length : Int) :: o.flatMap TDN : List Int); "
            + "let A5 := fun (F : Pl.Frame Float) (fe : List String) => OUT (train_run_05_association fw d12 F fe); "
            + "let A7 := fun (F : Pl.Frame Float) (fe : List String) => OUT (train_run_07_hl fw pv chi2 pow2 F fe); "
            + "let A6 := fun (G : LogisticFit Float) (fe : List String) (fi : List Int) (ic : Float) => "
              "let r := train_run_06_coefficients_odds fw fo d8 pv chi2 pow2 G fe fi ic; (FD r.1 ++ OUT r.2 : List Int); ")
    body = "(([" + ", ".join(terms) + "] : List (List Int)).flatten)"
    s = Suite("rv_567")
    s.item, s.decl = "def:zz_carrier_t", "zz_carrier_t"
    s.ints(lets, body, cases, use_kit=False)
    note = (f"review by port-translator-2, inputs of the reviewer: {info}; expected = the source lines executed as they stand, "
            "formatters as the injective encoding, chi2 as a table of the real values, pow2 = x * x (asserted equal to ** 2)")
    s.notes = {u: note for u in ("train_run_05_association", "train_run_06_coefficients_odds", "train_run_07_hl")}
    s.write()
    for k, v in info.items():
        print(k, v)
    print("input chars", (HERE.parent / "work" / "rv_567.inputs.json").stat().st_size)


if __name__ == "__main__":
    build()
