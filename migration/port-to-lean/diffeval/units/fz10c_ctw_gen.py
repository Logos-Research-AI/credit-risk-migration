"""Fidelity pass 2026-11-20, third attempt (label train-c): supplement for def:train_run_08_ctable
(credit_risk/train.py:479-535) with EXACT routines on both sides and wide designs, plus real-data windows.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10c_ctw_gen.py
  -> work/fz10c_ctw.json / .inputs.json / .fuzz.json   (seeded wide designs)
     work/fz10c_ctr.json / .inputs.json                (real-data windows)

Why: the main suite fz10c_ct (fz10c_train_gen.py) has designs of 1-3 columns and a Cramer stand-in `solve` for
1x1 / 2x2 only. Here the explicit parameters (RULEBOOK section 3) are routines that are exact mirrors on both sides:
  solve   Gaussian elimination with partial pivoting (Lean text and Python solve_sa of fz4_cim_gen, already shown
          equal there);
  dot, matmul (`@`)  sequential sums from 0.0: Lean DOT / MATMUL of fz10c_train_gen; Python: the arrays are an
          ndarray subclass whose `@` is that loop (fz4_cim_gen.NA), x_final made an NA by wrapping np.column_stack
          in the slice's namespace;
  einsum_q  sequential sum over j, k of (x_ij * v_jk) * x_ik from 0.0 (Lean EINSUM; Python NPX.einsum, the same loop);
  inv     the matrix with `a` at [0][0], 0 elsewhere (both sides); log1p = log(1 + x) (Lean Float.log, Python np.log);
  fmt_wd  "<bits or N>:w:d" (injective).
Seeds on which the Gaussian solve meets an exactly zero pivot (real np.linalg.solve raises LinAlgError there: outside
the model, RULEBOOK section 3) are dropped and counted.

Wide designs (seeded, built inside Lean): n in {0,1,2,3,4,5,6,8,10,13,17,30}; 2-5 predictors, each one of: random
ints -3..3, a 0/1 flag, tenths 0.0..99.9 (k / 10.0, correctly rounded on both sides), the constant 1 (collinear with
the intercept), twice x1, x1 + x(j-1) (collinear), all zeros; the last name repeated as "x1" in one seed of ten; rows
outside the mask with pd from {null, 0.5, 2.0, NaN}; pd = clamp(base + {-1,0,0,1} * spread); a null pd on the first
complete case 4 %; y 0/1; a fit 85 % with diagonal covariance from {1,1,1,0,-0,2.5,NaN,0}. Precondition as in
fz10c_train_gen.pre08.

Real-data windows: three windows of 40 consecutive rows (0-39, 50000-50039, 104960-104999) of the real step-08
inputs of train.run at HEAD on legacy/data (work/fz10c_real.pkl): fit_frame restricted to the 15 predictors of the
real final model (the unit reads only those columns), y_train, pd_logistic and fit_mask on the window, n_obs = 40,
the real final model's names, and its covariance reduced to the diagonal (the unit reads `final` only through
_left_out, which reads cov[i, i]; asserted below that the Python result is the same with the full real covariance).
The real run's own call (105,000 rows x 16 columns) is not evaluable: its fit_frame alone is 1.6 million floats
(far beyond an eval_decl input), and the Lean of the step-11 unit already exceeded the tool's time limit on 45,000
rows of 2 columns.
"""
from __future__ import annotations

import json
import pickle
import sys
import types
from pathlib import Path

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import fz10c_train_gen as g  # noqa: E402  (sets the carrier def:zz_carrier_fid_2)
import fz4_cim_gen as f4  # noqa: E402
import compare as cmp  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402

R = g.R
GEN = "migration/port-to-lean/diffeval/units/fz10c_ctw_gen.py"
_t = f4.LEAN
SOLVE_EXACT = _t[_t.index("let solve := fun"):_t.index("let dot := fun")]  # "let solve := ...; "

COMMON = (
    f"let FMT := {g.FMT}; let INV := {g.INV}; {SOLVE_EXACT}let DOT := {g.DOT}; let MATMUL := {g.MATMUL}; "
    f"let MATVEC := {g.MATVEC}; let EINSUM := {g.EINSUM}; let LOG1P := {g.LOG1P}; "
)
OUT = (
    "let r := train_run_08_ctable (α := Float) FMT (INV a) solve DOT MATMUL MATVEC EINSUM LOG1P mask ff fin names "
    "(n : Int) y sd; "
    "tR ff ++ tR sd ++ tC (Pl.Col.bool (mask.map some)) ++ tC (Pl.Col.f64 (y.map some)) ++ "
    "tC (Pl.Col.str (names.map some)) ++ tC (Pl.Col.f64 (diag.map some)) ++ [a.toBits] ++ "
    "(r.length.toUInt64 :: r.flatMap (fun (p : String × Tabular.Table Float) => tS p.1 ++ tA p.2))"
)

NSW = [0, 1, 2, 3, 4, 5, 6, 8, 10, 13, 17, 30]
KW = [2, 3, 3, 4, 4, 5]
LW = (
    COMMON
    + "let NS : List Nat := [0, 1, 2, 3, 4, 5, 6, 8, 10, 13, 17, 30]; "
    "let PB : List Float := [0.5, 0.25, 0.75, 0.3, 0.7, 0.02, 0.98, 0.125, 0.875]; "
    "let SP : List Float := [0.0, 0.0, 0.005, 0.01]; "
    "let CV : List Float := [1.0, 1.0, 1.0, 0.0, -0.0, 2.5, 0.0/0.0, 0.0]; "
    "let AA : List Float := [0.0, 0.0, 0.25, 1.0, 4.0]; "
    "let PX : List (Option Float) := [none, some 0.5, some 2.0, some (0.0/0.0)]; "
    "let DD : List Float := [-1.0, 0.0, 0.0, 1.0]; "
    "let cell := fun (s n md j i : Nat) (cols : List (List Float)) => (if md ≤ 1 then Float.ofInt (Int.ofNat (R s (1000*j+i) 7) - 3) "
    "else if md == 2 then Float.ofNat (R s (1000*j+i) 2) else if md == 3 then Float.ofNat (R s (1000*j+i) 1000) / 10.0 "
    "else if md == 4 then 1.0 else if md == 5 then (if j ≥ 2 then 2.0 * (cols.getD 0 []).getD i 0.0 else Float.ofInt (Int.ofNat (R s (1000*j+i) 7) - 3)) "
    "else if md == 6 then (if j ≥ 3 then (cols.getD 0 []).getD i 0.0 + (cols.getD (j - 2) []).getD i 0.0 else Float.ofNat (R s (1000*j+i) 2)) "
    "else 0.0 : Float); "
    "let tok := fun (s : Nat) => "
    "let n := NS.getD (R s 0 12) 0; "
    "let k := ([2, 3, 3, 4, 4, 5] : List Nat).getD (R s 1 6) 0; "
    "let cols : List (List Float) := (List.range k).foldl (fun (acc : List (List Float)) (j0 : Nat) => "
    "acc ++ [(List.range n).map (fun (i : Nat) => cell s n (R s (10 + j0 + 1) 8) (j0 + 1) i acc)]) []; "
    "let dup : Bool := R s 5 10 == 0; "
    "let names : List String := \"Intercept\" :: (List.range k).map (fun (j0 : Nat) => if dup && j0 + 1 == k then \"x1\" else \"x\" ++ toString (j0 + 1)); "
    "let ff : Pl.Frame Float := ((List.range k).filter (fun (j0 : Nat) => !(dup && j0 + 1 == k))).map "
    "(fun (j0 : Nat) => (\"x\" ++ toString (j0 + 1), Pl.Col.f64 ((cols.getD j0 []).map some))); "
    "let NN := n + ([0, 0, 1, 2] : List Nat).getD (R s 6 4) 0; "
    "let off := R s 7 (max NN 1); "
    "let mask : List Bool := (List.range NN).map (fun (i : Nat) => decide ((i + off) % NN < n)); "
    "let y : List Float := (List.range n).map (fun (i : Nat) => Float.ofNat (R s (4000+i) 2)); "
    "let pb := PB.getD (R s 9 9) 0.0; let sp := SP.getD (R s 10 4) 0.0; "
    "let nullAt : Nat := if R s 11 100 < 4 then mask.findIdx (fun (b : Bool) => b) else NN + 1; "
    "let pd : List (Option Float) := (List.range NN).map (fun (i : Nat) => if mask.getD i false then "
    "(if i == nullAt then none else (let v := pb + DD.getD (R s (5000+i) 4) 0.0 * sp; "
    "let v := (if v > 0.001 then v else 0.001); some (if v < 0.999 then v else 0.999))) "
    "else PX.getD (R s (5000+i) 4) none); "
    "let diag : List Float := (List.range names.length).map (fun (i : Nat) => CV.getD (R s (6000+i) 8) 0.0); "
    "let cov : List (List Float) := (List.range names.length).map (fun (i : Nat) => (List.range names.length).map "
    "(fun (j : Nat) => if i == j then diag.getD i 0.0 else 0.0)); "
    "let fin : Option (LogisticFit Float) := if R s 2 20 < 17 then some { names := names, beta := Np.NDArray.d1 [], "
    "cov := Np.NDArray.d2 cov, loglik := 0.0, n_iter := 0, converged := true } else none; "
    "let a := AA.getD (R s 12 5) 0.0; "
    "let sd : Pl.Frame Float := [(\"pd_logistic\", Pl.Col.f64 pd)]; "
    + OUT + "; "
)


def cellp(s, md, j, i, cols):
    if md <= 1:
        return float(R(s, 1000 * j + i, 7) - 3)
    if md == 2:
        return float(R(s, 1000 * j + i, 2))
    if md == 3:
        return float(R(s, 1000 * j + i, 1000)) / 10.0
    if md == 4:
        return 1.0
    if md == 5:
        return 2.0 * cols[0][i] if j >= 2 else float(R(s, 1000 * j + i, 7) - 3)
    if md == 6:
        return cols[0][i] + cols[j - 2][i] if j >= 3 else float(R(s, 1000 * j + i, 2))
    return 0.0


def mkw(s):
    n, k = NSW[R(s, 0, 12)], KW[R(s, 1, 6)]
    cols = []
    for j0 in range(k):
        md = R(s, 10 + j0 + 1, 8)
        cols.append([cellp(s, md, j0 + 1, i, cols) for i in range(n)])
    dup = R(s, 5, 10) == 0
    names = ["Intercept"] + ["x1" if dup and j0 + 1 == k else f"x{j0 + 1}" for j0 in range(k)]
    cd = {f"x{j0 + 1}": cols[j0] for j0 in range(k) if not (dup and j0 + 1 == k)}
    NN = n + [0, 0, 1, 2][R(s, 6, 4)]
    off = R(s, 7, max(NN, 1))
    mask = [((i + off) % NN) < n for i in range(NN)]
    y = [float(R(s, 4000 + i, 2)) for i in range(n)]
    pb, sp = g.PB[R(s, 9, 9)], g.SP[R(s, 10, 4)]
    null_at = (mask.index(True) if True in mask else NN) if R(s, 11, 100) < 4 else NN + 1
    pd = []
    for i in range(NN):
        if mask[i]:
            if i == null_at:
                pd.append(None)
            else:
                v = pb + g.DD[R(s, 5000 + i, 4)] * sp
                v = v if v > 0.001 else 0.001
                pd.append(v if v < 0.999 else 0.999)
        else:
            pd.append(g.PX[R(s, 5000 + i, 4)])
    diag = [g.CV[R(s, 6000 + i, 8)] for i in range(len(names))]
    fin = diag if R(s, 2, 20) < 17 else None
    return dict(n=n, names=names, cols=cd, mask=mask, y=y, pd=pd, diag=diag, final=fin, a=AA_(s))


def AA_(s):
    return g.AA[R(s, 12, 5)]


class NPXE(g.NPX):
    """sas_compat.np with the exact routines: Gaussian solve, the einsum loop (inv, log1p as in g.NPX)."""

    def __init__(self, a):
        super().__init__(a)
        self.linalg = types.SimpleNamespace(solve=f4.solve_sa, inv=self.linalg.inv)

    def einsum(self, spec, x, v, x2):
        assert spec == "ij,jk,ik->i"
        x, v = np.asarray(x), np.asarray(v)
        out = []
        for r in x:
            s = 0.0
            for j in range(len(r)):
                for k in range(len(r)):
                    s = s + r[j] * v[j][k] * r[k]
            out.append(s)
        return np.array(out, dtype=np.float64)


NPSLICE = types.SimpleNamespace(**{k: getattr(np, k) for k in dir(np) if not k.startswith("__")})
NPSLICE.column_stack = lambda arrs: f4.na(np.column_stack(arrs))


def run_exact(c, fit=None):
    writes = []
    proxy = types.SimpleNamespace(classification_table=sc.classification_table,
                                  classification_is_made=sc.classification_is_made, fmt_wd=g.fmt_py,
                                  write_sas_csv=lambda df, path, formats=None: writes.append((Path(path).name, df.clone())))
    ff = pl.DataFrame([pl.Series(k, v, dtype=pl.Float64) for k, v in c["cols"].items()])
    sd = pl.DataFrame({"pd_logistic": pl.Series(c["pd"], dtype=pl.Float64)})
    if fit is None and c["final"] is not None:
        kk = len(c["names"])
        cov = np.zeros((kk, kk))
        for i, v in enumerate(c["final"]):
            cov[i, i] = v
        fit = sc.LogisticFit(list(c["names"]), np.zeros(kk), cov, 0.0, 0, True)
    ns = {"np": NPSLICE, "pl": pl, "sas_compat": proxy, "fit_frame": ff, "n_obs": c["n"],
          "y_train": np.array(c["y"], dtype=np.float64), "final": fit, "final_names": list(c["names"]),
          "logit_scored_train": sd, "fit_mask": np.array(c["mask"], dtype=bool), "output_dir": Path("out")}
    old = sc.np
    sc.np = NPXE(c["a"])
    f4.FLAG["zero_pivot"] = False
    try:
        with np.errstate(all="ignore"):
            exec(g.S08, ns)  # noqa: S102
        ex = None
    except Exception as e:  # noqa: BLE001
        ex = e
    finally:
        sc.np = old
    return ns, writes, ex, ff, sd, f4.FLAG["zero_pivot"]


def toks(c, writes, ff, sd):
    t = cmp.tokens(cmp.canon_frame(ff)) + cmp.tokens(cmp.canon_frame(sd))
    t += cmp.tok_col(cmp.canon_bools(c["mask"])) + cmp.tok_col(cmp.canon_floats(c["y"]))
    t += cmp.tok_col(cmp.canon_strs(c["names"])) + cmp.tok_col(cmp.canon_floats(c["diag"])) + [cmp.fbits(c["a"])]
    t += [len(writes)]
    for name, df in writes:
        t += cmp.tok_str(name) + cmp.tokens(cmp.canon_table(df))
    return t


def wide(lo=7_300_000, N=700, block=350):
    s = Suite("fz10c_ctw", generator=GEN)
    kept, rej, raises_in, dropped, zp, tk = [], [], [], 0, 0, {}
    st = {"made": 0, "made, a dependent column": 0, "no table (fit)": 0, "no fit": 0, "width>=5": 0, "dupname": 0,
          "khi=50": 0, "level 0.000": 0}
    for sd_ in range(lo, lo + N):
        c = mkw(sd_)
        ns, writes, ex, ff, sdf, zpiv = run_exact(c)
        if zpiv:
            zp += 1
            continue
        pre = g.pre08(c, ns, ex)
        if ex is not None:
            (raises_in.append(sd_) if pre else None)
            dropped += 0 if pre else 1
            continue
        tk[sd_] = toks(c, writes, ff, sdf)
        (kept if pre else rej).append(sd_)
        if pre:
            made = bool(ns.get("ctable_made"))
            st["no fit" if c["final"] is None else ("made" if made else "no table (fit)")] += 1
            st["width>=5"] += len(c["names"]) >= 5
            st["dupname"] += c["names"][-1] == "x1" and len(c["names"]) > 2
            if made:
                x = np.asarray(ns["x_final"])
                kept_cols = sc._kept(np.asarray(x.T @ x)) if x.shape[0] else []
                st["made, a dependent column"] += len(kept_cols) < x.shape[1]
                lv = ns["ctable"].get_column("ProbLevel").to_list()
                st["khi=50"] += bool(lv) and lv[-1] == 1.0
                st["level 0.000"] += bool(lv) and lv[0] == 0.0
    for b0 in range(lo, lo + N, block):
        rng = list(range(b0, min(b0 + block, lo + N)))
        for cls, lst in (("kept", set(kept)), ("rejected", set(rej))):
            part = [x for x in rng if x in lst]
            if not part:
                continue
            m = sum(1 << (x - rng[0]) for x in part)
            body = (f"[dg (((List.range {len(rng)}).filter (fun (i : Nat) => Nat.testBit {m} i)).flatMap "
                    f"(fun (i : Nat) => tok ({rng[0]} + i)))]")
            s.ints(g.RLET + LW, body, [(f"{cls} {rng[0]}..{rng[-1]} ({len(part)})", g.U08,
                                        cmp.digest([x for q in part for x in tk[q]]),
                                        {"fz": cls, "covers": len(part), "seeds": part})], gen=True, table=True)
    s.write()
    fz = {"fuzzer": "port-translator (fidelity pass 2026-11-20 third attempt, train-c)", "generator": GEN,
          "blueprint": g.BP,
          "units": {g.U08: {"seeds": f"{lo}..{lo + N - 1}", "generated": N, "kept": len(kept),
                            "python_raises_inside_precondition": raises_in,
                            "note": f"EXACT routines, wide designs (2-5 predictors); rejected and Python returns: {len(rej)}; "
                                    f"rejected and Python raises (dropped): {dropped}; exact zero pivot of the Gaussian "
                                    f"solve (real numpy raises LinAlgError, outside the model, dropped): {zp}; reached: "
                                    + json.dumps(st)}}}
    (HERE.parent / "work" / "fz10c_ctw.fuzz.json").write_text(json.dumps(fz, indent=1))
    print("wide kept", len(kept), "rejected", len(rej), "raises inside", raises_in, "dropped", dropped, "zero pivot", zp)
    print("  ", st)


def lf(x: float) -> str:
    x = float(x)
    if x == int(x) and abs(x) < 1e15 and not (x == 0 and np.signbit(x)):
        return f"{int(x)}.0" if x >= 0 else f"(-{int(-x)}.0)"
    return f"(Float.ofBits {hex(cmp.fbits(x))})"


def real_windows():
    r = pickle.loads((HERE.parent / "work" / "fz10c_real.pkl").read_bytes())
    i8, o8 = r["s08"]
    names = list(i8["final_names"])
    ff_all = i8["fit_frame"].select(names[1:])
    pd_all = np.asarray(i8["logit_scored_train"].get_column("pd_logistic").to_numpy(), dtype=np.float64)
    mask_all = np.asarray(i8["fit_mask"], dtype=bool)
    assert mask_all.all() and len(mask_all) == ff_all.height == len(pd_all)
    y_all = np.asarray(i8["y_train"], dtype=np.float64)
    diag = [float(v) for v in np.diag(i8["final"].cov)]
    s = Suite("fz10c_ctr", generator=GEN)
    for a0 in (0, 104960):
        w = ff_all.slice(a0, 40)
        c = dict(n=40, names=names, cols={k: w.get_column(k).to_list() for k in w.columns}, mask=[True] * 40,
                 y=[float(v) for v in y_all[a0:a0 + 40]], pd=[float(v) for v in pd_all[a0:a0 + 40]], diag=diag,
                 final=diag, a=1.0)
        ns, writes, ex, ff, sdf, zpiv = run_exact(c)
        assert ex is None and not zpiv and g.pre08(c, ns, ex), (a0, ex, zpiv)
        # the full real covariance gives the same result (the unit reads cov only through _left_out: cov[i, i])
        ns2, writes2, ex2, *_ = run_exact(c, fit=i8["final"])
        assert ex2 is None and [cmp.canon_table(d) for _, d in writes2] == [cmp.canon_table(d) for _, d in writes]
        cols = ", ".join(f'("{k}", Pl.Col.f64 (([{", ".join(lf(v) for v in vs)}] : List Float).map some))' for k, vs in c["cols"].items())
        lets = (COMMON
                + f"let n : Nat := 40; let names : List String := [{', '.join(chr(34) + x + chr(34) for x in names)}]; "
                f"let ff : Pl.Frame Float := [{cols}]; let mask : List Bool := List.replicate 40 true; "
                f"let y : List Float := [{', '.join(lf(v) for v in c['y'])}]; "
                f"let sd : Pl.Frame Float := [(\"pd_logistic\", Pl.Col.f64 (([{', '.join(lf(v) for v in c['pd'])}] : List Float).map some))]; "
                f"let diag : List Float := [{', '.join(lf(v) for v in diag)}]; "
                "let cov : List (List Float) := (List.range names.length).map (fun (i : Nat) => (List.range names.length).map "
                "(fun (j : Nat) => if i == j then diag.getD i 0.0 else 0.0)); "
                "let fin : Option (LogisticFit Float) := some { names := names, beta := Np.NDArray.d1 [], "
                "cov := Np.NDArray.d2 cov, loglik := 0.0, n_iter := 0, converged := true }; let a : Float := 1.0; ")
        lv = ns["ctable"].get_column("ProbLevel").to_list()
        s.ints(lets, "[dg (" + OUT + ")]", [(f"real rows {a0}..{a0 + 39} (16 columns, {len(lv)} levels)", g.U08,
                                            cmp.digest(toks(c, writes, ff, sdf)), {"fz": "kept"})], table=True)
        print("window", a0, "made", ns["ctable_made"], "levels", len(lv), lv[:2], lv[-2:])
    s.write()


if __name__ == "__main__":
    wide()
    real_windows()
