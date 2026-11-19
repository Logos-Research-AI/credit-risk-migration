"""Fuzz 2026-11-18 (fifth port diff), by a non-author: def:metrics_run_08_validation_summary,
def:metrics_run_09_model_performance, def:metrics_run_10_printed_roc (+ preconditions), each on its own inputs.
(prefix fz8m: nothing here writes an fz7_ name)

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz8m_s0810_gen.py
      -> work/fz8m_s08, fz8m_s09, fz8m_s10 (.json .inputs.json .fuzz.json .in0.txt)
  eval_decl each input on def:zz_carrier_e / zz_carrier_e; outputs one per line in work/<suite>.out.txt; compare.py.

Case of seed s (built INSIDE Lean from kit.hsh, mirrored with kit.gF / gI / hsh):
  valid_exists  False for 1 seed in 3 (the argument is a Bool of the unit: both values on every shape)
  auc_summary   0, 1 or 2 rows: ROCModel (String), AUC, Gini (Float64, pool P: nulls, NaN, +-inf, +-0.0, 0.7 / 0.65 / 0.3 / 0.25 / 0.1 / 0.5 and
                one ulp either side, 1, 1e300, 5e-324)
  ks_statistic  0..2 rows: KS_Statistic, KS_Cutoff (pool P);  psi_summary 0..2 rows: PSI (pool P), PSI_interpretation (String with nulls)
  threshold_analysis (09)  0..6 rows: threshold (pool TH: null, NaN, 0.5 several times, 0.3 .. 0.7, 0.5 +- 1 ulp, -0.0), accuracy, precision, recall,
                f1_score, specificity (pool P)
  roc_stats (10) 1 row (2 in 1 seed of 8, 3 columns in none): ROCModel (String), Area StdErr LowerArea UpperArea SomersD Gamma TauA (pool P);
                sas_d8 a stand-in on both sides ("." for null, else the decimal text of the bits)
Expected: the real lines of metrics_calculation.py (cut by marker text, exec'd with the module globals); the Date column of 09 is
compared as a String cell (Lean `today` is the String cell of today's date, README).
Classes: every input satisfies the preconditions by construction (distinct names, Float64 / String kinds, columns of one length; 10: one row
at least); no rejected class.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import sys
import textwrap
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import b4_gen as b4  # noqa: E402
import compare as cmp  # noqa: E402
import kit  # noqa: E402
from suite import Suite  # noqa: E402
from credit_risk import metrics_calculation as mc  # noqa: E402
from credit_risk import sas_compat  # noqa: E402

WORK = HERE.parent / "work"
nan, inf = float("nan"), float("inf")
h = kit.hsh
u = math.nextafter
L = Path(mc.__file__).read_text().splitlines(keepends=True)
TODAY = dt.date.today().isoformat()


def cut(a, b, extra=0):
    i = next(k for k, ln in enumerate(L) if a in ln)
    j = next(k for k in range(i, len(L)) if b in L[k])
    return compile(textwrap.dedent("".join(L[i:j + 1 + extra])), f"mc:{i + 1}-{j + 1}", "exec")


S08 = cut("validation_summary = (\n", '[c for c in validation_summary.columns if c != "KS_Statistic"] + ["KS_Statistic"]', 1)
S09 = cut("at_50 = threshold_analysis.filter(", '.drop("threshold", "ROCModel")')
S10 = cut("printed_roc_metrics = pl.DataFrame(", "schema={c: pl.String for c in roc_stats.columns},", 1)


def run(code, **env):
    ns = dict(vars(mc)); ns.update(env); exec(code, ns); return ns


def d8(v):
    import struct
    return "." if v is None else str(struct.unpack("<Q", struct.pack("<d", v))[0])


P = [None, nan, inf, -inf, 0.0, -0.0, 0.7, u(0.7, 0), u(0.7, 1), 0.65, u(0.65, 0), u(0.65, 1), 0.3, u(0.3, 0), u(0.3, 1), 0.25, u(0.25, 0),
     u(0.25, 1), 0.1, u(0.1, 0), u(0.1, 1), 0.5, u(0.5, 0), u(0.5, 1), 1.0, 1e300, 5e-324]
TH = [None, nan, 0.5, 0.5, 0.5, 0.3, 0.4, 0.6, 0.7, u(0.5, 0), u(0.5, 1), -0.0]
INT = ["No significant change", "Some change", "Significant change"]
NR = [0, 1, 1, 1, 2]
NTH = [0, 1, 2, 3, 5, 6]


def f64(name, vals):
    return pl.Series(name, vals, dtype=pl.Float64, nan_to_null=False)


def strs(name, vals):
    return pl.Series(name, vals, dtype=pl.String)


def frames_py(s):
    ve = h(s, 9301) % 3 != 0
    na, nk, npp, nth = NR[h(s, 9302) % 5], NR[h(s, 9303) % 5], NR[h(s, 9304) % 5], NTH[h(s, 9305) % 6]
    auc = pl.DataFrame([strs("ROCModel", ["Logistic Model"] * na), f64("AUC", kit.gF(s + 1, na, 70, 2, P)), f64("Gini", kit.gF(s + 2, na, 70, 2, P))])
    ks = pl.DataFrame([f64("KS_Statistic", kit.gF(s + 3, nk, 70, 2, P)), f64("KS_Cutoff", kit.gF(s + 4, nk, 70, 2, P))])
    psi = pl.DataFrame([f64("PSI", kit.gF(s + 5, npp, 70, 2, P)),
                        strs("PSI_interpretation", [None if a is None else INT[a] for a in kit.gI(s + 6, npp, 20, 3, 0)])])
    thr = pl.DataFrame([f64("threshold", kit.gF(s + 7, nth, 80, 2, TH)), f64("accuracy", kit.gF(s + 8, nth, 40, 2, P)),
                        f64("precision", kit.gF(s + 9, nth, 40, 2, P)), f64("recall", kit.gF(s + 10, nth, 40, 2, P)),
                        f64("f1_score", kit.gF(s + 11, nth, 40, 2, P)), f64("specificity", kit.gF(s + 12, nth, 40, 2, P))])
    return ve, auc, ks, psi, thr


def roc_py(s):
    n = 2 if h(s, 9306) % 8 == 0 else 1
    cols = [strs("ROCModel", ["Logistic Model"] * n)] + [f64(c, kit.gF(s + 20 + k, n, 70, 2, P)) for k, c in
                                                          enumerate("Area StdErr LowerArea UpperArea SomersD Gamma TauA".split())]
    return pl.DataFrame(cols)


def canon09(df):
    c = cmp.canon_frame(df)
    for col in c["cols"]:
        if col[1]["kind"] == "other:Date":
            col[1] = {"type": "col", "kind": "cell", "values": [["str", v] for v in col[1]["values"]]}
    return c


def dg08(s):
    ve, auc, ks, psi, thr = frames_py(s)
    r = run(S08, valid_exists=ve, auc_summary=auc, ks_statistic=ks, psi_summary=psi)["validation_summary"]
    return cmp.digest(cmp.tokens(cmp.canon_frame(r)))


def dg09(s):
    ve, auc, ks, psi, thr = frames_py(s)
    r = run(S09, valid_exists=ve, auc_summary=auc, ks_statistic=ks, psi_summary=psi, threshold_analysis=thr)["model_performance_metrics"]
    return cmp.digest(cmp.tokens(canon09(r)))


def dg10(s):
    roc = roc_py(s)
    r = run(S10, roc_stats=roc, sas_compat=type("SC", (), {"sas_d8": staticmethod(d8)}))["printed_roc_metrics"]
    return cmp.digest(cmp.tokens(cmp.canon_frame(r)))


def lf_list(xs):
    return "[" + ", ".join("none" if x is None else f"some {b4.lf(x)}" for x in xs) + "]"


LETS = (
    b4.W + f"let P : List (Option Float) := {lf_list(P)}; let TH : List (Option Float) := {lf_list(TH)}; "
    f"let NR : List Nat := {NR}; let NTH : List Nat := {NTH}; "
    "let INT : List String := [\"No significant change\", \"Some change\", \"Significant change\"]; "
    "let H := fun (s k : Nat) => (hsh s k).toNat; "
    "let VE := fun (s : Nat) => H s 9301 % 3 != 0; "
    "let AUC := fun (s : Nat) => let n := NR.getD (H s 9302 % 5) 0; (\"x\", ([(\"ROCModel\", Pl.Col.str (List.replicate n (some \"Logistic Model\"))), "
    "(\"AUC\", Pl.Col.f64 (gF (s + 1) n 70 2 P)), (\"Gini\", Pl.Col.f64 (gF (s + 2) n 70 2 P))] : Pl.Frame Float)); "
    "let KS := fun (s : Nat) => let n := NR.getD (H s 9303 % 5) 0; (\"x\", ([(\"KS_Statistic\", Pl.Col.f64 (gF (s + 3) n 70 2 P)), "
    "(\"KS_Cutoff\", Pl.Col.f64 (gF (s + 4) n 70 2 P))] : Pl.Frame Float)); "
    "let PSI := fun (s : Nat) => let n := NR.getD (H s 9304 % 5) 0; (\"x\", ([(\"PSI\", Pl.Col.f64 (gF (s + 5) n 70 2 P)), "
    "(\"PSI_interpretation\", Pl.Col.str ((gI (s + 6) n 20 3 0).map (fun (o : Option Int) => o.map (fun (a : Int) => INT.getD a.toNat \"\"))))] : Pl.Frame Float)); "
    "let THR := fun (s : Nat) => let n := NTH.getD (H s 9305 % 6) 0; (\"x\", ([(\"threshold\", Pl.Col.f64 (gF (s + 7) n 80 2 TH)), "
    "(\"accuracy\", Pl.Col.f64 (gF (s + 8) n 40 2 P)), (\"precision\", Pl.Col.f64 (gF (s + 9) n 40 2 P)), (\"recall\", Pl.Col.f64 (gF (s + 10) n 40 2 P)), "
    "(\"f1_score\", Pl.Col.f64 (gF (s + 11) n 40 2 P)), (\"specificity\", Pl.Col.f64 (gF (s + 12) n 40 2 P))] : Pl.Frame Float)); "
)
LETS09 = LETS + "let today : Tabular.Cell Float := Tabular.Cell.str (some \"" + TODAY + "\"); "
LETS10 = (
    b4.W + f"let P : List (Option Float) := {lf_list(P)}; "
    "let D8 := fun (o : Option Float) => (match o with | none => \".\" | some x => toString x.toBits.toNat : String); "
    "let ROC := fun (s : Nat) => let n := if (hsh s 9306).toNat % 8 == 0 then 2 else 1; "
    "([(\"ROCModel\", Pl.Col.str (List.replicate n (some \"Logistic Model\"))), "
    "(\"Area\", Pl.Col.f64 (gF (s + 20) n 70 2 P)), (\"StdErr\", Pl.Col.f64 (gF (s + 21) n 70 2 P)), (\"LowerArea\", Pl.Col.f64 (gF (s + 22) n 70 2 P)), "
    "(\"UpperArea\", Pl.Col.f64 (gF (s + 23) n 70 2 P)), (\"SomersD\", Pl.Col.f64 (gF (s + 24) n 70 2 P)), (\"Gamma\", Pl.Col.f64 (gF (s + 25) n 70 2 P)), "
    "(\"TauA\", Pl.Col.f64 (gF (s + 26) n 70 2 P))] : Pl.Frame Float); "
)


def emit(name, unit, lets, one, pyfun, S0, N, table):
    st = Suite(name)
    st.item, st.decl = "def:zz_carrier_e", "zz_carrier_e"
    ds = [pyfun(s) for s in range(S0, S0 + N)]
    body = f"[W ((List.range {N}).map (fun (i : Nat) => let s := {S0} + i; {one}))]"
    st.ints(lets, body, [(f"seeds {S0}..{S0 + N - 1}: {N} inputs, one fold", unit, b4.w(ds), {"fz": "kept", "covers": N})], gen=True, table=table)
    st.write()
    (WORK / f"{name}.in0.txt").write_text(st.inputs[0]["text"])
    (WORK / f"{name}.fuzz.json").write_text(json.dumps({
        "fuzzer": "fuzzer-metrics-06-07-fifth", "generator": "diffeval/units/fz8m_s0810_gen.py",
        "blueprint": "5365851c-5549-44b7-9207-4bd4c422031d",
        "units": {unit: {"seeds": f"{S0}..{S0 + N - 1}", "generated": N, "kept": N, "python_raises_inside_precondition": [],
                         "note": "every input is inside the precondition by construction; one case = fold of the digests of the unit's result"}}}))


if __name__ == "__main__":
    N = 2400
    emit("fz8m_s08", "metrics_run_08_validation_summary", LETS,
         "let r := metrics_run_08_validation_summary (VE s) (AUC s).2 (KS s).2 (PSI s).2; dg (tR r)", dg08, 90000, N, False)
    emit("fz8m_s09", "metrics_run_09_model_performance", LETS09,
         "let r := metrics_run_09_model_performance today (VE s) (THR s).2 (AUC s).2 (KS s).2 (PSI s).2; dg (tR r)", dg09, 100000, N, True)
    emit("fz8m_s10", "metrics_run_10_printed_roc", LETS10,
         "let r := metrics_run_10_printed_roc D8 (ROC s); dg (tR r)", dg10, 110000, N, False)
