"""Fuzz 2026-11-18 (after the fifth port diff): metrics steps 01, 02, 04 to 10 of metrics_calculation.run,
in composition, against the real port, on def:zz_carrier_e.

  cd migration/port-to-lean
  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz7_metrics_gen.py [first_seed count per_input]
  (eval_decl every input of work/fz7_m.inputs.json on def:zz_carrier_e / zz_carrier_e; save outputs one per line
   in work/fz7_m.out.txt; compare.py work/fz7_m.json work/fz7_m.out.txt)

One seed s builds, inside Lean (kit.GEN) and here (kit.gF / gI / hsh), the validation frame V(s)
(n rows, default_flag, pd_logistic, credit_risk_score; n = 0 is an imported header-only file replaced by the
0-row Float64 frame, valid_exists False) and the training frame T(s) (credit_risk_score only; 0 rows,
Float64 pool, grid, or all-null String). The Lean composes the units as `run` does; Python executes the REAL source
of the same lines of run (cut by marker text, exec with the module globals) in the same order. Units 05, 08, 09
are evaluated twice: valid_exists as it is (n > 0) and flipped (a flipped value is a legal argument of the unit;
the step 05 precondition says every clause holds for both). Unit 03 (confusion_metrics x5, concat) is Python-side
only as the threshold_analysis input of 09: Lean builds it with confusion_metrics and Pl.concat.
One case = one digest of the unit's result(s) for one seed. sas_best / float: lookup tables from the real functions;
sas_d8: a stand-in (decimal text of the bits) on both sides.
"""
from __future__ import annotations

import json
import math
import sys
import textwrap
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
_argv, sys.argv = sys.argv, [sys.argv[0]]
import suite as suite_mod  # noqa: E402

suite_mod.CARRIERS["identity"] = ("def:zz_carrier_e", "zz_carrier_e")
import compare as cmp  # noqa: E402
import fz_t14_gen as f14  # noqa: E402
import fz_t1_gen as f1  # noqa: E402  (math.fsum mirror, pre_roc)
import kit  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import WORK, Suite  # noqa: E402

from credit_risk import metrics_calculation as mc  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

sys.argv = _argv
NZ = f14.NZ
nan, inf = float("nan"), float("inf")
u = math.nextafter
UNITS = ["metrics_run_01_roc_auc", "metrics_run_02_ks", "metrics_run_04_deciles", "metrics_run_05_cumulative_lift",
         "metrics_run_05_cumulative_lift[valid_exists flipped]", "metrics_run_06_psi", "metrics_run_07_calibration",
         "metrics_run_08_validation_summary", "metrics_run_08_validation_summary[valid_exists flipped]",
         "metrics_run_09_model_performance", "metrics_run_09_model_performance[valid_exists flipped]",
         "metrics_run_10_printed_roc"]
TODAY = "2026-11-18"

# ------------------------------------------------------------------ real source, cut by markers
L = Path(mc.__file__).read_text().splitlines(keepends=True)


def cut(a, b, incl_b=False):
    i = next(k for k, l in enumerate(L) if a in l)
    j = next(k for k in range(i, len(L)) if b in L[k])
    return compile(textwrap.dedent("".join(L[i:j + (1 if incl_b else 0)])), f"mc:{i + 1}-{j}", "exec")


CA = cut("roc_stats = sas_compat.roc_association(", "# listing-only: PROC PRINT decile_analysis")
CB = cut("into = decile_data.select(", "# listing-only: PROC SGPLOT cumulative_lift")
CC = cut("train_scores_sorted = ", "# metrics_calculation.sas:459-473 validation_summary")
CD = cut("validation_summary = (", "# listing-only: PROC PRINT validation_summary")
CE = cut("at_50 = threshold_analysis", '.drop("threshold", "ROCModel")', True)
CF = cut("printed_roc_metrics = pl.DataFrame(", "# WORK.ROC_STATS does not exist")
assert "valid_exists" in "".join(L[next(k for k, l in enumerate(L) if "into = decile_data.select(" in l):][:60])


def ex(code, ns):
    exec(code, ns)  # noqa: S102


# ------------------------------------------------------------------ pools (as fz5_metrics_pyside)
NS = [0, 1, 2, 3, 4, 5, 8, 9, 10, 13, 19, 20, 24, 40]
GEN_ = [None, nan, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, -0.0, 2.0, 0.5, inf]
FE = [GEN_, [0.0], [1.0], [0.0, 1.0], [0.0, 1.0], [0.0, 1.0, None]]
FPE = [97, 100, 100, 100, 100, 97]
EDGE = [None, nan, inf, -inf, 0.0, -0.0, 0.5, u(.5, 0), u(.5, 1), .25, .75, 1.0, 1e300, 1e-300, 5e-324, .1, .2, .3, .4, .6, .7,
        u(.3, 0), u(.3, 1), u(.7, 0), u(.7, 1), -1.0, 2.0]
PE = [EDGE, [0.25, 0.5, 0.75, None], EDGE, [0.1, 0.2, 0.3, 0.4]]
PPE = [70, 100, 20, 100]
T_ = [None, nan, inf, -inf, 0.0, -0.0, 1e300, 5e-324, 700.0, u(700., inf), u(700., 0), 650.0, 600.0, u(600., 0), u(600., inf), 1.0, 4.0]
SZ = [0, 1, 2, 3, 5, 9, 10, 11, 20, 37]


def f64(v):
    return pl.Series(v, dtype=pl.Float64, nan_to_null=False)


def score_col(s, n, m):
    if m == 0:
        return f64(kit.gF(s, n, 60, 3, T_))
    if m == 1:
        a, b = kit.gI(s, n, 10, 6, 0), kit.gI(s + 1, n, 0, 3, 0)
        return f64([None if x is None else u(float(600 + 10 * x), (0.0, -inf, inf)[y]) if y else float(600 + 10 * x)
                    for x, y in zip(a, b)])
    if m == 2:
        return f64([None if x is None else float(500 + 7 * x) for x in kit.gI(s, n, 5, 40, 0)])
    return pl.Series([None] * n, dtype=pl.String)


def V_of(s):
    n = NS[kit.hsh(s, 7) % len(NS)]
    fm, pm, mv = kit.hsh(s, 9) % 6, kit.hsh(s, 8) % 4, kit.hsh(s, 9004) % 3
    return pl.DataFrame({"default_flag": f64(kit.gF(2 * s, n, FPE[fm], 2, FE[fm])),
                         "pd_logistic": f64(kit.gF(2 * s + 1, n, PPE[pm], 2, PE[pm])),
                         "credit_risk_score": score_col(s + 500000, n, mv)})


def T_of(s):
    nt, mt = SZ[kit.hsh(s, 9001) % len(SZ)], kit.hsh(s, 9003) % 4
    return pl.DataFrame([score_col(s, nt, mt).alias("credit_risk_score")])


def pre_rank(x, k, desc):
    nn = x.len() - x.null_count()
    for r in x.rank("average", descending=desc).to_list():
        if r is not None and not (-2**63 <= math.floor(r * float(k) / float(nn + 1)) < 2**63):
            return False
    return True


# ------------------------------------------------------------------ canonical forms
def canon(df):
    ex_ = []
    for c in df.columns:
        dt_ = df.schema[c]
        if c in ("decile", "pred_bin"):
            assert dt_ == pl.Int64 or dt_ == pl.Float64, (c, dt_)
            ex_.append(pl.col(c).cast(pl.Float64))
        elif dt_ == pl.Date:
            ex_.append(pl.col(c).cast(pl.String))
    out = cmp.canon_frame(df.with_columns(ex_)) if ex_ else cmp.canon_frame(df)
    for n, col in out["cols"]:
        if n == "validation_date":
            col["kind"] = "cell"
            col["values"] = [["str", v] for v in col["values"]]
    return out


NZCOLS = {"decile_analysis": ["min_pd", "max_pd"], "cumulative_lift": ["cum_defaults", "cum_capture_rate", "cum_lift", "min_pd", "max_pd"]}


def canon_nz(df, names):
    c = canon(df)
    for n, col in c["cols"]:
        if n in names and col["kind"] == "f64":
            col["values"] = [0 if v == 0x8000000000000000 else v for v in col["values"]]
    return c


def tk(*dfs, nz=None):
    return [t for d in dfs for t in cmp.tokens(canon_nz(d, nz) if nz else canon(d))]


# ------------------------------------------------------------------ Python side
def python_seed(s, best, d8_seen):
    """-> list of (status, digest or None) over UNITS; status kept / rejected / raises-kept / raises-rejected / upstream."""
    V, T = V_of(s), T_of(s)
    vex = V.height > 0
    out = {}
    o_best, o_d8 = sc.sas_best, sc.sas_d8

    def w_best(x, w):
        r = o_best(x, w)
        assert w == 8
        assert best.setdefault(None if x is None else cmp.fbits(float(x)), r) == r
        return r

    sc.sas_best = w_best
    sc.sas_d8 = lambda x: "" if x is None else str(cmp.fbits(float(x)))
    ns = dict(vars(mc))
    ns.update(logit_scored_valid=V, logit_scored_train=T, valid_exists=vex)
    st = {}

    def step(name, code, nsx, pre, outs):
        ok = pre()
        try:
            ex(code, nsx)
            st[name] = ("kept" if ok else "rejected", cmp.digest(tk(*[nsx[o] for o in outs], nz=NZCOLS.get(outs[0]))))
        except Exception as e:  # noqa: BLE001
            st[name] = ("raises-kept" if ok else "raises-rejected", None)
            print(f"[seed {s}] {name}: Python raises {type(e).__name__}: {str(e)[:100]} (precondition {'admits' if ok else 'rejects'})")
            return False
        return True

    try:
        # 01 + 02 + 03 + 04 are one slice in run; the units' results are read back from the namespace
        pre01 = lambda: f1.pre_roc(V["default_flag"], V["pd_logistic"])  # noqa: E731
        pre04 = lambda: pre_rank(V["pd_logistic"], 10, True)  # noqa: E731
        okA = True
        try:
            ex(CA, ns)
        except Exception as e:  # noqa: BLE001
            okA = False
            print(f"[seed {s}] slice 01-04 raises {type(e).__name__}: {str(e)[:100]}")
        if okA:
            st["01"] = ("kept" if pre01() else "rejected", cmp.digest(tk(ns["roc_stats"], ns["auc_summary"])))
            st["02"] = ("kept", cmp.digest(tk(ns["logit_scored_valid"], ns["ks_statistic"])))
            st["04"] = ("kept" if pre04() else "rejected", cmp.digest(tk(ns["decile_data"]) + tk(ns["decile_analysis"], nz=NZCOLS["decile_analysis"])))
        else:
            for k in ("01", "02", "04"):
                st[k] = ("raises-rejected" if not (k == "02" or (k == "01" and pre01()) or (k == "04" and pre04())) else "raises-kept", None)
        if okA:
            for flip, name in ((False, "05"), (True, "05f")):
                n2 = dict(ns)
                n2["valid_exists"] = (not vex) if flip else vex
                step(name, CB, n2, lambda: True, ["cumulative_lift"])
            okC = step("06", CC, dict(ns), lambda: T.height > 0, ["psi_calculation", "psi_summary"])
            n3 = dict(ns)
            if okC:
                ex(CC, n3)
                st["07"] = ("kept" if pre_rank(V["pd_logistic"], 20, False) else "rejected", cmp.digest(tk(n3["calibration_plot"])))
                for flip, nm8, nm9 in ((False, "08", "09"), (True, "08f", "09f")):
                    n4 = dict(n3)
                    n4["valid_exists"] = (not vex) if flip else vex
                    step(nm8, CD, n4, lambda: True, ["validation_summary"])
                    n5 = dict(n3)
                    n5["valid_exists"] = (not vex) if flip else vex
                    n5["dt"] = type("D", (), {"date": type("Dd", (), {"today": staticmethod(lambda: __import__("datetime").date.fromisoformat(TODAY))})})
                    step(nm9, CE, n5, lambda: True, ["model_performance_metrics"])
            step("10", CF, dict(ns), lambda: True, ["printed_roc_metrics"])
    finally:
        sc.sas_best, sc.sas_d8 = o_best, o_d8
    order = ["01", "02", "04", "05", "05f", "06", "07", "08", "08f", "09", "09f", "10"]
    return [st.get(k, ("upstream", None)) for k in order], (V.height, T.height)


# ------------------------------------------------------------------ Lean side
def olist(xs):
    return "[" + ", ".join("none" if x is None else f"some {lt.lean_float(x)}" for x in xs) + "]"


def lean_lets(best):
    sb = ", ".join(f"({'none' if k is None else f'some {k}'}, {lt.lean_str(v)})" for k, v in best.items())
    pf = ", ".join(f"({lt.lean_str(v)}, {cmp.fbits(float(v))})" for v in sorted({v for v in best.values() if v}))
    return (f"let SB : List (Option UInt64 × String) := [{sb}]; let PF : List (String × UInt64) := [{pf}]; "
            'let sb := fun (x : Option Float) (_ : Int) => (match SB.lookup (x.map Float.toBits) with | some s => s | none => "?"); '
            "let pf := fun (s : String) => Float.ofBits ((PF.lookup s).getD 1); "
            'let sd8 := fun (x : Option Float) => (match x with | none => "" | some v => toString v.toBits.toNat); '
            f"let today : Tabular.Cell Float := Tabular.Cell.str (some {lt.lean_str(TODAY)}); "
            + f1.FS_LET +
            f"let NS : List Nat := {NS}; let SZ : List Nat := {SZ}; "
            f"let G : List (Option Float) := {olist(GEN_)}; "
            f"let FE : List (List (Option Float)) := [G, {olist([0.0])}, {olist([1.0])}, {olist([0.0, 1.0])}, {olist([0.0, 1.0])}, {olist([0.0, 1.0, None])}]; "
            f"let FPE : List UInt64 := {FPE}; let ED : List (Option Float) := {olist(EDGE)}; "
            f"let PE : List (List (Option Float)) := [ED, {olist(PE[1])}, ED, {olist(PE[3])}]; let PPE : List UInt64 := {PPE}; "
            f"let TT : List (Option Float) := {olist(T_)}; "
            "let sc := fun (s n m : Nat) => (match m with "
            "| 0 => Pl.Col.f64 (gF s n 60 3 TT) "
            "| 1 => Pl.Col.f64 (List.zipWith (fun (a b : Option Int) => (match a, b with | some x, some y => "
            "(let v : Float := Float.ofInt (600 + 10 * x); if y == 0 then some v else if y == 1 then some (Float.ofBits (v.toBits - 1)) else some (Float.ofBits (v.toBits + 1))) "
            "| _, _ => (none : Option Float))) (gI s n 10 6 0) (gI (s + 1) n 0 3 0)) "
            "| 2 => Pl.Col.f64 ((gI s n 5 40 0).map (fun (o : Option Int) => o.map (fun (x : Int) => Float.ofInt (500 + 7 * x)))) "
            "| _ => Pl.Col.str (List.replicate n (none : Option String)) : Pl.Col Float); "
            "let nV := fun (s : Nat) => NS.getD ((hsh s 7) % 14).toNat 0; "
            "let mkV := fun (s : Nat) => (let n := nV s; let fm := ((hsh s 9) % 6).toNat; let pm := ((hsh s 8) % 4).toNat; let mv := ((hsh s 9004) % 3).toNat; "
            '([("default_flag", Pl.Col.f64 (gF (2 * s) n (FPE.getD fm 100) 2 (FE.getD fm []))), '
            '("pd_logistic", Pl.Col.f64 (gF (2 * s + 1) n (PPE.getD pm 100) 2 (PE.getD pm []))), '
            '("credit_risk_score", sc (s + 500000) n mv)] : Pl.Frame Float)); '
            "let mkT := fun (s : Nat) => (let nt := SZ.getD ((hsh s 9001) % 10).toNat 0; let mt := ((hsh s 9003) % 4).toNat; "
            '([("credit_risk_score", sc s nt mt)] : Pl.Frame Float)); '
            + NZ +
            "let dgi := fun (l : List Int) => ((l.foldl (fun (h : UInt64) (x : Int) => (let g := (h ^^^ x.toNat.toUInt64) * 1099511628211; g ^^^ (g >>> 32))) 14695981039346656037).toNat : Int); "
            "let one := fun (s : Nat) => (let V0 := mkV s; let T := mkT s; let vex : Bool := decide (nV s > 0); "
            "let r1 := metrics_run_01_roc_auc FS V0; let r2 := metrics_run_02_ks sb pf V0; let V := r2.1; "
            "let r4 := metrics_run_04_deciles V; "
            'let th := Pl.concat [(confusion_metrics (0.3 : Float) "03" V).2.2, (confusion_metrics (0.4 : Float) "04" V).2.2, '
            '(confusion_metrics (0.5 : Float) "05" V).2.2, (confusion_metrics (0.6 : Float) "06" V).2.2, (confusion_metrics (0.7 : Float) "07" V).2.2]; '
            "let r5 := metrics_run_05_cumulative_lift sb pf r4.1 r4.2 vex; let r5f := metrics_run_05_cumulative_lift sb pf r4.1 r4.2 (!vex); "
            "let r6 := metrics_run_06_psi T V; let r7 := metrics_run_07_calibration V; "
            "let r8 := metrics_run_08_validation_summary vex r1.2 r2.2 r6.2; let r8f := metrics_run_08_validation_summary (!vex) r1.2 r2.2 r6.2; "
            "let r9 := metrics_run_09_model_performance today vex th r1.2 r2.2 r6.2; let r9f := metrics_run_09_model_performance today (!vex) th r1.2 r2.2 r6.2; "
            "let r10 := metrics_run_10_printed_roc sd8 r1.1; "
            "[dg (tR r1.1 ++ tR r1.2), dg (tR r2.1 ++ tR r2.2), dg (tR r4.1 ++ tR (nz [\"min_pd\", \"max_pd\"] r4.2)), dg (tR (nz [\"cum_defaults\", \"cum_capture_rate\", \"cum_lift\", \"min_pd\", \"max_pd\"] r5)), dg (tR (nz [\"cum_defaults\", \"cum_capture_rate\", \"cum_lift\", \"min_pd\", \"max_pd\"] r5f)), dg (tR r6.1 ++ tR r6.2), "
            "dg (tR r7), dg (tR r8), dg (tR r8f), dg (tR r9), dg (tR r9f), dg (tR r10)]); ")


def main():
    first, count, per = (int(x) for x in (_argv[1:4] or [40000, 800, 25]))
    s = Suite("fz7_m")
    stat = {u_: {"kept": 0, "rejected": 0, "raises-kept": [], "raises-rejected": 0, "upstream": 0} for u_ in UNITS}
    flavours = {"empty_V": 0, "empty_T": 0, "strnull_T": 0}
    for a in range(first, first + count, per):
        best: dict = {}
        cases = []
        for seed in range(a, min(a + per, first + count)):
            res, (nv, nt) = python_seed(seed, best, None)
            flavours["empty_V"] += nv == 0
            flavours["empty_T"] += nt == 0
            raised = any(dg is None for _, dg in res)
            for unit, (status, dg) in zip(UNITS, res):
                stt = stat[unit]
                if status in ("kept", "rejected"):
                    stt[status] += 1
                elif status == "raises-kept":
                    stt["raises-kept"].append(seed)
                elif status == "raises-rejected":
                    stt["raises-rejected"] += 1
                else:
                    stt["upstream"] += 1
            extra = {"fz": "seed"}
            if raised:
                extra.update(expect_diff=True, note="Python raises in some unit of this seed")
            cases.append((f"seed {seed} ({nv}/{nt} rows) all units", "metrics", -1 if raised else cmp.digest([dg for _, dg in res]), extra))
        s.ints(lean_lets(best), f"((List.range' {a} {min(per, first + count - a)}).map (fun (i : Nat) => dgi (one i)))", cases, gen=True, table=True)
    s.write()
    (WORK / "fz7_m.fuzz.json").write_text(json.dumps({"generator": "diffeval/units/fz7_metrics_gen.py", "seeds": f"{first}..{first + count - 1}",
                                                       "units": stat, "flavours": flavours}, indent=1))
    for k, v in stat.items():
        print(k, {a: (b if not isinstance(b, list) else (len(b), b[:5])) for a, b in v.items()})
    print(flavours)


if __name__ == "__main__":
    main()
