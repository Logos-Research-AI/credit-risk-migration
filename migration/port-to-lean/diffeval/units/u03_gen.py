"""Update of 2026-11-17, changes (d) and (e): def:train_run_03_fit_global_rsquare alone.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/u03_gen.py
      -> work/u03_fit.json + work/u03_fit.inputs.json (ONE eval_decl input)

Python side.
  real   the real train.run on the 60 / 25 row sample of the real feature files (t18_gen.real_run,
         formatters as the injective encoding of their arguments): the stepwise result, the locals
         fit_frame, n_obs, y_train, m2ll0, ybar, and the three frames handed to write_sas_csv by
         step 03.
  slice  the source lines train.py:154-268 executed as they stand on those locals. On the real
         stepwise result its write_sas_csv calls must be the ones of the real run (asserted). The
         same lines are then run on hand-made step lists:
           q0     the real steps with a step whose fit is the intercept-only fit (q == 0) after the
                  first step and another one at the end
           only0  one step, with q == 0
           empty  no step
Lean side: the unit on the same arguments; formatters = the same encoding; chi2 = table of the real
values; solve / matmul / matvec / dot = numpy's results keyed on the digest of the arguments (a
sentinel otherwise). Compared, per case: the number of output pairs, then per pair the file name,
the number of rows and, when there is a row, the number of columns and one digest per column.
"""
from __future__ import annotations

import sys
import textwrap
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import math  # noqa: E402

import numpy as np  # noqa: E402
import polars as pl  # noqa: E402
import t18_gen as t  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402
from credit_risk import train  # noqa: E402

FIRST, LAST = 154, 268
UNIT = "train_run_03_fit_global_rsquare"


def run_slice(stepwise, L) -> list[tuple[str, pl.DataFrame]]:
    src = Path(train.__file__).read_text().splitlines()
    assert src[FIRST - 1].strip() == 'fs_step: list[str] = ["0"]' and "printed_rsquare.csv" in src[LAST - 1]
    code = textwrap.dedent("\n".join(src[FIRST - 1:LAST]))
    writes: list[tuple[str, pl.DataFrame]] = []
    proxy = types.SimpleNamespace(
        sas_d12_3=t.ENCODERS["sas_d12_3"], fmt_wd=t.ENCODERS["fmt_wd"], sas_pvalue=t.ENCODERS["sas_pvalue"],
        chi2_sf=sc.chi2_sf, write_sas_csv=lambda df, path, formats=None: writes.append((Path(path).name, df.clone())))
    ns = {"sas_compat": proxy, "np": np, "pl": pl, "math": math, "stepwise": stepwise, "output_dir": Path("out"),
          "m2ll0": L["m2ll0"], "n_obs": L["n_obs"], "fit_frame": L["fit_frame"], "y_train": L["y_train"], "ybar": L["ybar"]}
    exec(compile(code, "train.py:154-268", "exec"), ns)  # noqa: S102
    return writes


def build():
    ind = t.sample_inputs()
    real = t.real_run(ind, encoded=False)
    rec = t.real_run(ind, encoded=True)
    n_fmt = t.check_real_against_encoded(real, rec)
    L, sw = rec["locals"], rec["stepwise"]
    T = t.routine_tables(rec)
    real_writes = rec["writes"][1:4]
    assert [n for n, _ in real_writes] == ["printed_fit_statistics.csv", "printed_global_tests.csv", "printed_rsquare.csv"]
    sl = run_slice(sw, L)
    assert len(sl) == 3 and all(a[0] == b[0] and a[1].equals(b[1]) and a[1].schema == b[1].schema for a, b in zip(sl, real_writes, strict=True))

    io = sw.intercept_only
    assert io.names == ["Intercept"]

    def z(k: int):
        return sc.StepwiseStep(step=k, entered=None, removed="zz", df=1, number_in_model=0, score_chisq=None,
                               wald_chisq=1.5, p_value=0.5, fit=io)

    def with_steps(steps):
        return sc.StepwiseResult(list(steps), sw.final, sw.intercept_only)

    cases_py = [
        ("real", sw, "SW"),
        ("q0", with_steps([sw.steps[0], z(70), *sw.steps[1:], z(90)]),
         "{ SW with steps := [SW.steps.headD (Z 0), Z 70] ++ SW.steps.drop 1 ++ [Z 90] }"),
        ("only0", with_steps([z(1)]), "{ SW with steps := [Z 1] }"),
        ("empty", with_steps([]), "{ SW with steps := [] }"),
    ]
    assert len(sw.steps) >= 1

    kvv = lambda rows: "[" + ", ".join(f"({a}, {b}, {t.ul(out)})" for a, b, out in rows) + "]"  # noqa: E731
    kmm = lambda rows: "[" + ", ".join(f"({a}, {b}, {t.ull(out)})" for a, b, out in rows) + "]"  # noqa: E731
    mm = [r for r in T["matmul"] if any(r[0] == v[0] for v in T["matvec"])]  # the products of step 03 only
    routines = (
        f"let SV : List (Int × Int × List UInt64) := {kvv(T['solve'])}; "
        f"let MV : List (Int × Int × List UInt64) := {kvv(T['matvec'])}; "
        f"let MM : List (Int × Int × List (List UInt64)) := {kmm(mm)}; "
        f"let DT : List (Int × Int × UInt64) := [{', '.join(f'({a}, {b}, {t.fb(r)})' for a, b, r in T['dot'])}]; "
        "let solve := fun (a : List (List Float)) (b : List Float) => KVV SV (MW a) (VW b); "
        "let matvec := fun (a : List (List Float)) (b : List Float) => KVV MV (MW a) (VW b); "
        "let matmul := fun (a b : List (List Float)) => KMM MM (MW a) (MW b); "
        "let dot := fun (a b : List Float) => (match DT.find? (fun (t : Int × Int × UInt64) => t.1 == VW a && t.2.1 == VW b) with "
        f"| some t => Float.ofBits t.2.2 | none => Float.ofBits {t.SENT} : Float); "
        f"let chi2 := T2 [{', '.join(f'({a}, ({d}), {b})' for a, d, b in T['chi2'])}]; "
    )
    used = [c for c in L["fit_frame"].columns if any(c in st.fit.names for st in sw.steps)]
    ff = L["fit_frame"].select(["default_flag", *used, "age_group"])  # the columns a step names, the response, one column with a null
    L = {**L, "fit_frame": ff}
    sl2 = run_slice(sw, L)  # the reduced frame gives the same three frames
    assert all(a[0] == b[0] and a[1].equals(b[1]) for a, b in zip(sl2, real_writes, strict=True))
    lets = (t.W + t.BI + t.OF + t.TS + t.TC + t.FD + t.TX + t.TD + t.FL + t.MW + t.FMT + t.DEC + t.KEYED + t.MKFIT + routines
            + f"let SW := {t.lean_stepwise(sw)}; "
            + f"let IO := {t.lean_fit(io)}; "
            + 'let Z := fun (k : Int) => ({ step := k, entered := none, removed := some "zz", df := 1, number_in_model := 0, '
              "score_chisq := none, wald_chisq := some (Float.ofBits %d), p_value := Float.ofBits %d, fit := IO } : StepwiseStep Float); "
              % (t.fb(1.5), t.fb(0.5))
            + f"let ff := Pl.ofTable {t.lean_table(ff)}; "
            + f"let nobs : Int := {L['n_obs']}; let ytr := FL {t.ul(L['y_train'])}; "
            + f"let m2ll0 := Float.ofBits {t.fb(L['m2ll0'])}; let ybar := Float.ofBits {t.fb(L['ybar'])}; "
            + f"let R := fun (sw : StepwiseResult Float) => let o := {UNIT} fw d12 pv chi2 sw solve matmul matvec dot ff nobs ytr m2ll0 ybar; "
              "(o.length : Int) :: o.flatMap TDN; ")
    cases: list[tuple] = []
    terms: list[str] = []
    labs = t.labels_fd("input fit_frame", ff)
    cases += [(lab, UNIT, int(v)) for lab, v in zip(labs, t.fd(ff), strict=True)]
    terms.append("FD ff")
    info = {}
    for name, swp, term in cases_py:
        ws = real_writes if name == "real" else run_slice(swp, L)
        exp = [len(ws)] + [x for n, df in ws for x in t.tdn(n, df)]
        lab = [f"{name}: number of files"] + [f"{name}: {s}" for n, df in ws for s in t.labels_tdn(n, df)]
        assert len(exp) == len(lab)
        cases += [(a, UNIT, int(b)) for a, b in zip(lab, exp, strict=True)]
        terms.append(f"R ({term})")
        info[name] = [(n, df.height) for n, df in ws]
    body = "(" + " ++ ".join(f"({x})" for x in terms) + ")"
    s = Suite("u03_fit")
    s.item, s.decl = "def:zz_carrier_t", "zz_carrier_t"
    s.ints(lets, body, cases, use_kit=False)
    s.notes = {UNIT: (
        f"update 2026-11-17 (d), (e): real train.run on the 60-row sample (fit frame {L['n_obs']} rows, steps "
        f"{[(st.step, st.entered, st.removed) for st in sw.steps]}; {n_fmt} formatted cells of the run with the real formatters "
        f"checked against the encoded run); fit frame passed with the columns {ff.columns} only (the slice on it gives the frames of the real run); the source lines {FIRST}-{LAST} executed on hand step lists (asserted equal to the real "
        f"run on the real step list); files and rows per case: {info}")}
    s.write()
    print(info)
    print("steps", [(st.step, st.entered, st.removed, len(st.fit.names) - 1) for st in sw.steps])
    for name, swp, _ in cases_py[1:]:
        for n, df in run_slice(swp, L):
            if n == "printed_fit_statistics.csv":
                print(name, df.select("Step", "RowId").rows())
    p = HERE.parent / "work" / "u03_fit.inputs.json"
    print("input chars", p.stat().st_size if p.exists() else "?")


if __name__ == "__main__":
    build()
