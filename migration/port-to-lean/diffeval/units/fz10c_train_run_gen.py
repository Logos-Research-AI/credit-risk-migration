"""Fidelity pass 2026-11-20, third attempt, label compositions: def:run_py_py_py (train.run) as a whole, against the
REAL train.run at port HEAD 4a757fb, through the carrier def:zz_carrier_fid_2. Every input is built INSIDE Lean from
its seed (nothing per seed is typed), so one eval_decl call carries hundreds of whole runs.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10c_train_run_gen.py gen S0 N PER
      -> work/fz10c_train_run.json, .inputs.json, .stat.json
  eval_decl each input on def:zz_carrier_fid_2; diffeval/units/fz10c_collect.py; compare.py.

Feature files of seed s (42 columns, the header of the real feature file, all Float64; the cell / flag generator of
fz3_train_run_gen.py, imported unchanged): training rows 6 + hsh(s, 603) % 20, validation rows [1, 2, 5, 9][hsh(s, 604) % 4].
Stops: m = hsh(s, 640) % 12: 0 training file absent, 1 validation file absent, 2 both absent (Lean `none`).

The explicit parameters of def:run_py_py_py are opaque to the composition, so both sides get the SAME stand-ins
(the precedent of fz_run_py_gen.py's sas_d8, fz4_cim_gen.py's routines, t18_gen.py's formatters):
  stepwise   a StepwiseResult built from the seed on both sides (`sw_py` / Lean `SWG`): no fit (final, intercept_only
             None, no step) when hsh(s, 630) % 10 == 0; else intercept_only (loglik -25 - 5 * (hsh % 4)) and 0..4 steps
             following one of three enter/remove patterns over three distinct candidates (a step whose model is empty
             has the intercept-only fit, q == 0); final = the last step's fit, or intercept_only when there is no step.
             Each fit: beta from PB, cov symmetric with diagonal from PC (0.0 for a slope with hsh % 15 == 0: left out)
             and off-diagonal from PO, loglik from PL, converged unless hsh % 7 == 0, separation "quasicomplete" when
             hsh % 9 == 0. beta / cov are NA arrays (below) on the Python side.
  formatters t18_gen.ENCODERS (injective encodings of the arguments), Lean t18_gen.FMT
  chi2       x, d -> 1 / (1 + x / (d + 1))   (sas_compat.chi2_sf replaced on the Python side)
  solve      Gaussian elimination with partial pivoting (fz4_cim_gen.solve_sa, Lean copied); a seed where it meets an
             exactly zero pivot is the LinAlgError of numpy: outside the model (RULEBOOK §3), dropped
  inv        the columns solve(a, e_j)
  matmul / matvec / dot / einsum_q   sequential sums from 0.0 in index order; on the Python side numpy's `@` is routed
             to them by an ndarray subclass NA: np.column_stack returns NA views during the run (x_k, x_final), as do
             the stand-in results and the fits' arrays; np.einsum("ij,jk,ik->i") replaced
  log1p      x -> x * 0.5 (np.log1p replaced during the run)
  pow2       x -> x * x; Python's `** 2` cannot be replaced: a seed is used only if pow(x, 2.0) == x * x on every
             argument the run squares ((b / se) of step 06, (o - e) of the Hosmer-Lemeshow table)
  fsum       the exact-sum lambda FS of fz_run_py_gen.py; a seed is used only if it equals math.fsum on every list
  today      Cell.str of the run's date
Precondition def:run_py_py_py_precond rendered in Python (`pre`, after fz3_train_run_gen.pre): okT of both imports (asserted:
non-empty, 42 distinct names, Float64); intercept_only None iff final None, no step without fit (by construction);
step 03: for steps with q != 0, exp(-lr / n_obs) finite, exp(-m2ll0 / n_obs) finite and 1 - exp(-m2ll0 / n_obs) != 0;
step 04: pd_logistic != 0 wherever not null (exp(-eta) finite); step 06: cov[idx, idx] >= 0, sqrt != 0, the three exp
finite for the kept parameters; step 15: an exported ROC frame with rows has a ROCModel label. NOT rendered: the
preconditions of the library units reached through steps 05, 07, 08, 13, 14 (association_table, hosmer_lemeshow,
classification_table, roc_association, merge_one_to_one): a seed on which Python returns is taken as inside them, a
seed on which it raises is reported (not compared).
Expected per seed: W([number of files or -1, model.json tokens, W(tdn) per file in write order]) (t18_gen digests).
"""
from __future__ import annotations

import contextlib
import datetime as dt
import io
import json
import math
import sys
import tempfile
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import suite as suite_mod  # noqa: E402

suite_mod.CARRIERS["identity"] = ("def:zz_carrier_fid_2", "zz_carrier_fid_2")

import fz10c_common as C  # noqa: E402
import fz3_train_run_gen as F3  # noqa: E402  (frames, cell generator, LGEN, HSH, CAND_NAMES; main guarded)
import kit  # noqa: E402
import t18_gen as t18  # noqa: E402  (encoders, digests, Lean pieces; main guarded)
from suite import Suite  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402
from credit_risk import train  # noqa: E402

U = "run_py_py_py"
WORK = HERE.parent / "work"
hsh = kit.hsh
NAN = float("nan")

PB = [0.5, -0.25, 1.0, -1.5, 0.125, 2.0, -0.75, 0.0, 3.0, -0.0625]
PC = [0.25, 1.0, 0.0625, 4.0, 0.015625, 0.5, 2.25]
PO = [0.0, 0.0, 0.0, 0.01, -0.02]
PL = [-3.5, -6.25, -10.0, -14.75, -20.5, -0.5]
PS = [0.5, 3.75, 12.0]
PW = [1.5, NAN]
PP = [0.01, 0.2, 0.5]
STEPS = 4
PAT = [[(+1, 0), (+1, 1), (+1, 2), (-1, 0)], [(+1, 0), (-1, 0), (+1, 1), (+1, 2)], [(+1, 0), (+1, 1), (-1, 1), (+1, 2)]]
NV = [1, 2, 5, 9]
CAND = F3.CAND_NAMES
assert len(CAND) == 36


def pick(L, s, i):
    return L[hsh(s, i) % len(L)]


# ------------------------------------------------------------------ stand-in routines (Python side)
FLAG = {"zero_pivot": False}


def _mm(a, b):
    a, b = np.asarray(a), np.asarray(b)
    if a.ndim == 2 and b.ndim == 2:
        r = np.zeros((a.shape[0], b.shape[1]))
        for i in range(a.shape[0]):
            for j in range(b.shape[1]):
                acc = 0.0
                for k in range(a.shape[1]):
                    acc += float(a[i, k]) * float(b[k, j])
                r[i, j] = acc
        return r.view(NA)
    if a.ndim == 2 and b.ndim == 1:
        r = np.zeros(a.shape[0])
        for i in range(a.shape[0]):
            acc = 0.0
            for k in range(a.shape[1]):
                acc += float(a[i, k]) * float(b[k])
            r[i] = acc
        return r.view(NA)
    assert a.ndim == 1 and b.ndim == 1, (a.shape, b.shape)
    acc = 0.0
    for k in range(a.shape[0]):
        acc += float(a[k]) * float(b[k])
    return np.float64(acc)


class NA(np.ndarray):
    def __matmul__(self, o):
        return _mm(self, o)

    def __rmatmul__(self, o):
        return _mm(o, self)


def na(a):
    return np.asarray(a, dtype=np.float64).view(NA)


def solve_sa(a, b):
    """fz4_cim_gen.solve_sa (copied)."""
    a = [[float(v) for v in r] for r in np.asarray(a)]
    n = len(a)
    b = [float(v) for v in np.asarray(b)]
    M = [a[i] + [b[i]] for i in range(n)]
    with np.errstate(all="ignore"):
        for k in range(n):
            p, best = k, abs(M[k][k])
            for i in range(k + 1, n):
                if abs(M[i][k]) > best:
                    p, best = i, abs(M[i][k])
            M[k], M[p] = M[p], M[k]
            if M[k][k] == 0.0:
                FLAG["zero_pivot"] = True
            for i in range(k + 1, n):
                f = np.float64(M[i][k]) / np.float64(M[k][k])
                for j in range(k, n + 1):
                    M[i][j] = float(np.float64(M[i][j]) - f * np.float64(M[k][j]))
        x = [0.0] * n
        for i in range(n - 1, -1, -1):
            s = M[i][n]
            for j in range(i + 1, n):
                s = float(np.float64(s) - np.float64(M[i][j]) * np.float64(x[j]))
            x[i] = float(np.float64(s) / np.float64(M[i][i]))
    return na(np.array(x, dtype=np.float64))


def inv_sa(a):
    a = np.asarray(a, dtype=np.float64)
    n = a.shape[0]
    cols = [np.asarray(solve_sa(a, np.array([1.0 if i == j else 0.0 for i in range(n)]))) for j in range(n)]
    return na(np.array([[float(cols[j][i]) for j in range(n)] for i in range(n)], dtype=np.float64).reshape(n, n))


def einsum_sa(spec, x, v, x2):
    assert spec == "ij,jk,ik->i"
    x, v = np.asarray(x), np.asarray(v)
    out = np.zeros(x.shape[0])
    for i in range(x.shape[0]):
        acc = 0.0
        for j in range(x.shape[1]):
            for k in range(x.shape[1]):
                acc += float(x[i, j]) * float(v[j, k]) * float(x[i, k])
        out[i] = acc
    return out.view(NA)


def chi2_sa(x, df):
    return 1.0 / (1.0 + float(x) / (float(df) + 1.0))


def log1p_sa(x):
    return np.asarray(x, dtype=np.float64) * 0.5


# ------------------------------------------------------------------ the stepwise result of seed s (Python side)
def fit_py(s: int, j: int, model: list[str], io):
    if not model:
        return io
    m = len(model) + 1
    t = s * 16 + j
    beta = [pick(PB, t, i) for i in range(m)]
    cov = [[0.0] * m for _ in range(m)]
    for i in range(m):
        cov[i][i] = 0.0 if (i > 0 and hsh(t, 300 + i) % 15 == 0) else pick(PC, t, 100 + i)
        for k in range(i + 1, m):
            cov[i][k] = cov[k][i] = pick(PO, t, 200 + i * 8 + k)
    return sc.LogisticFit(names=["Intercept", *model], beta=na(beta), cov=na(np.array(cov).reshape(m, m)),
                          loglik=pick(PL, t, 400), n_iter=5, converged=hsh(t, 401) % 7 != 0,
                          separation="quasicomplete" if hsh(t, 402) % 9 == 0 else None)


def sw_py(s: int):
    if hsh(s, 630) % 10 == 0:
        return sc.StepwiseResult([], None, None)
    io = sc.LogisticFit(names=["Intercept"], beta=na([pick(PB, s, 660)]), cov=na(np.array([[pick(PC, s, 661)]])),
                        loglik=-25.0 - 5.0 * (hsh(s, 662) % 4), n_iter=3, converged=True)
    a, b = hsh(s, 670) % 36, [1, 5, 7, 11, 13, 17][hsh(s, 671) % 6]
    vs = [CAND[(a + k * b) % 36] for k in range(3)]
    K = hsh(s, 672) % (STEPS + 1)
    pat = PAT[hsh(s, 673) % 3]
    model: list[str] = []
    steps = []
    for j in range(1, K + 1):
        sgn, v = pat[j - 1]
        name = vs[v]
        if sgn > 0:
            model = [*model, name]
        else:
            model = [x for x in model if x != name]
        f = fit_py(s, j, model, io)
        steps.append(sc.StepwiseStep(step=j, entered=name if sgn > 0 else None, removed=None if sgn > 0 else name, df=1,
                                     number_in_model=len(model), score_chisq=pick(PS, s * 16 + j, 500) if sgn > 0 else None,
                                     wald_chisq=None if sgn > 0 else pick(PW, s * 16 + j, 501), p_value=pick(PP, s * 16 + j, 502),
                                     fit=f))
    final = steps[-1].fit if steps else io
    return sc.StepwiseResult(steps, final, io)


# ------------------------------------------------------------------ one run (Python side)
def frames(s: int):
    nt, nv = 6 + hsh(s, 603) % 20, NV[hsh(s, 604) % 4]
    return F3.frame(s, s, nt), F3.frame(s, s + F3.OFFV, nv)


def stop_mode(s: int) -> int:
    return hsh(s, 640) % 12


FR_OVERRIDE: list = [None]  # real-data mode: (training frame, validation frame) in place of the seed's frames


def pyrun(s: int) -> dict:
    ft, fv = frames(s) if FR_OVERRIDE[0] is None else FR_OVERRIDE[0]
    m = stop_mode(s) if FR_OVERRIDE[0] is None else 3
    has_t, has_v = m not in (0, 2), m not in (1, 2)
    rec: dict = {"imports": [], "writes": [], "fsum_ok": True, "locals": None, "raised": None, "model_json": None,
                 "stop": not (has_t and has_v), "sw": sw_py(s), "nt": ft.height, "nv": fv.height}
    FLAG["zero_pivot"] = False
    o = dict(imp=sc.proc_import_csv, write=sc.write_sas_csv, step=sc.stepwise_logistic, chi2=sc.chi2_sf, solve=np.linalg.solve,
             inv=np.linalg.inv, cs=np.column_stack, es=np.einsum, l1p=np.log1p, fsum=math.fsum)
    enc_old = {k: getattr(sc, k) for k in t18.ENCODERS}

    def w_import(path, guessingrows=20):
        d = o["imp"](path, guessingrows=guessingrows)
        rec["imports"].append((Path(path).name, d.clone()))
        return d

    def w_fsum(xs):
        xs = [float(x) for x in xs]
        r = o["fsum"](xs)
        if t18.fb(C.fs_mirror(xs)) != t18.fb(r):
            rec["fsum_ok"] = False
        return r

    def prof(frame, event, arg):
        if event == "return" and frame.f_code is train.run.__code__:
            rec["locals"] = dict(frame.f_locals)

    sc.proc_import_csv = w_import
    sc.write_sas_csv = lambda df, path, formats=None: rec["writes"].append((Path(path).name, df.clone()))
    sc.stepwise_logistic = lambda *a, **k: rec["sw"]
    sc.chi2_sf = chi2_sa
    np.linalg.solve, np.linalg.inv = solve_sa, inv_sa
    np.column_stack = lambda arrs: o["cs"](arrs).view(NA)
    np.einsum = einsum_sa
    np.log1p = log1p_sa
    math.fsum = w_fsum
    for k, f in t18.ENCODERS.items():
        setattr(sc, k, f)
    try:
        with tempfile.TemporaryDirectory() as td, warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ind, outd = Path(td) / "in", Path(td) / "out"
            ind.mkdir()
            outd.mkdir()
            if has_t:
                ft.write_csv(ind / "model_features_train.csv")
            if has_v:
                fv.write_csv(ind / "model_features_validation.csv")
            sys.setprofile(prof)
            try:
                with contextlib.redirect_stdout(io.StringIO()), np.errstate(all="ignore"):
                    train.run(ind, outd)
            except Exception as e:  # noqa: BLE001
                rec["raised"] = f"{type(e).__name__}: {str(e)[:100]}"
            finally:
                sys.setprofile(None)
            if (outd / "model.json").exists():
                rec["model_json"] = json.loads((outd / "model.json").read_text())
    finally:
        sc.proc_import_csv, sc.write_sas_csv, sc.stepwise_logistic, sc.chi2_sf = o["imp"], o["write"], o["step"], o["chi2"]
        np.linalg.solve, np.linalg.inv, np.column_stack, np.einsum, np.log1p = o["solve"], o["inv"], o["cs"], o["es"], o["l1p"]
        math.fsum = o["fsum"]
        for k, f in enc_old.items():
            setattr(sc, k, f)
    rec["zero_pivot"] = FLAG["zero_pivot"]
    rec["held"] = True  # the files hold the generated tables (an all-null column is imported as String: not)
    for (nm, got), want in zip(rec["imports"], (ft, fv)):
        if not (got.columns == want.columns and all(t == pl.Float64 for t in got.dtypes) and t18.fd(got) == t18.fd(want)):
            rec["held"] = False
    return rec


def pow2_ok(rec: dict) -> bool:
    L, sw = rec["locals"], rec["sw"]
    args = []
    if sw.final is not None:
        for idx in [0, *L["final_index"]]:
            if idx in L["left_out"]:
                continue
            b, se = float(sw.final.beta[idx]), math.sqrt(float(sw.final.cov[idx, idx]))
            args.append(b / se)
    for row in L["hl_table"].iter_rows(named=True):
        for ob, ex in (("EventsObserved", "EventsExpected"), ("NoneventsObserved", "NoneventsExpected")):
            if row[ob] is not None and row[ex] is not None:
                args.append(float(row[ob]) - float(row[ex]))
    with np.errstate(all="ignore"):
        return all(t18.fb(math.pow(x, 2.0) if math.isfinite(x) else x * x) == t18.fb(x * x) for x in args)


def pre(rec: dict) -> tuple[bool, str]:
    """def:run_py_py_py_precond, as rendered (module docstring)."""
    L, sw = rec["locals"], rec["sw"]
    n = L["n_obs"]
    if sw.final is not None:
        if n == 0:
            return False, "n_obs = 0"
        m2ll0 = L["m2ll0"]
        try:
            any_q = False
            for st in sw.steps:
                if len(st.fit.names) - 1 == 0:
                    continue
                any_q = True
                if not math.isfinite(math.exp(-(m2ll0 - (-2.0) * st.fit.loglik) / n)):
                    return False, "step 03 exp not finite"
            e0 = math.exp(-m2ll0 / n)
            if any_q and (not math.isfinite(e0) or 1.0 - e0 == 0.0):
                return False, "step 03 exp(-m2ll0/n)"
            for idx in [0, *L["final_index"]]:
                if idx in L["left_out"]:
                    continue
                b, cv = float(sw.final.beta[idx]), float(sw.final.cov[idx, idx])
                if cv < 0 or math.sqrt(cv) == 0.0:
                    return False, "step 06 se"
                se = math.sqrt(cv)
                if idx != 0 and not all(math.isfinite(math.exp(a)) for a in (b, b - sc.Z975 * se, b + sc.Z975 * se)):
                    return False, "step 06 exp"
        except (OverflowError, ValueError):
            return False, "exp overflow"
    pdl = L["logit_scored_train"].get_column("pd_logistic").to_list()
    if any(v is not None and v == 0.0 for v in pdl):
        return False, "step 04 exp(-eta) overflow"
    for fr, on in ((L["roc_train"], True), (L["roc_valid"], bool(L["roc_valid_created"]))):
        lab = fr.get_column("ROCModel").to_list()
        if on and lab and all(v is None for v in lab):
            return False, "step 15 ROCModel labels all null"
    return True, ""


def expected(rec: dict) -> int:
    if rec["stop"]:
        return t18.w([-1])
    mj = rec["model_json"]
    mt = [0] if mj is None else [1] + t18.o(mj["intercept"]) + [t18.w([t for c, b in mj["coefficients"].items() for t in t18.ts(c) + [t18.fb(b)]])]
    return t18.w([len(rec["writes"])] + mt + [t18.w(t18.tdn(n, df)) for n, df in rec["writes"]])


def tags(rec: dict) -> list[str]:
    sw, L = rec["sw"], rec["locals"]
    if rec["stop"]:
        return ["stop"]
    t = []
    if sw.final is None:
        return ["no fit"]
    t += ["no step"] if not sw.steps else []
    t += ["final intercept only"] if len(sw.final.names) == 1 else []
    t += ["q == 0 step"] if any(len(x.fit.names) == 1 for x in sw.steps) else []
    t += ["left-out parameter in final"] if L["left_out"] else []
    t += ["validation of one class"] if not L["roc_valid_created"] else []
    t += ["no classification table"] if not L.get("ctable_made", True) else []
    t += ["HL written"] if L.get("hl_written") else []
    return t


# ------------------------------------------------------------------ Lean side
SWG = (
    "let PB : List Float := [" + ", ".join(f"Float.ofBits {t18.fb(x)}" for x in PB) + "]; "
    "let PC : List Float := [" + ", ".join(f"Float.ofBits {t18.fb(x)}" for x in PC) + "]; "
    "let PO : List Float := [" + ", ".join(f"Float.ofBits {t18.fb(x)}" for x in PO) + "]; "
    "let PL : List Float := [" + ", ".join(f"Float.ofBits {t18.fb(x)}" for x in PL) + "]; "
    "let PS : List Float := [" + ", ".join(f"Float.ofBits {t18.fb(x)}" for x in PS) + "]; "
    "let PW : List Float := [" + ", ".join(f"Float.ofBits {t18.fb(x)}" for x in PW) + "]; "
    "let PP : List Float := [" + ", ".join(f"Float.ofBits {t18.fb(x)}" for x in PP) + "]; "
    "let CAND : List String := " + json.dumps(CAND) + "; "
    "let pk := fun (L : List Float) (s i : Nat) => L.getD ((hsh s i) % L.length.toUInt64).toNat 0.0; "
    "let fitG := fun (s j : Nat) (model : List String) (io : LogisticFit Float) => (if model.isEmpty then io else "
    "let m := model.length + 1; let t := s * 16 + j; "
    "let dg0 := fun (i : Nat) => (if i > 0 && (hsh t (300 + i)) % 15 == 0 then (0.0 : Float) else pk PC t (100 + i)); "
    "let cov := (List.range m).map (fun (i : Nat) => (List.range m).map (fun (k : Nat) => "
    "if i == k then dg0 i else if i < k then pk PO t (200 + i * 8 + k) else pk PO t (200 + k * 8 + i))); "
    "({ names := \"Intercept\" :: model, beta := Np.NDArray.d1 ((List.range m).map (fun (i : Nat) => pk PB t i)), "
    "cov := Np.NDArray.d2 cov, loglik := pk PL t 400, n_iter := 5, converged := (hsh t 401) % 7 != 0, "
    "separation := if (hsh t 402) % 9 == 0 then some \"quasicomplete\" else none } : LogisticFit Float)); "
    "let PAT : List (List (Int × Nat)) := [[(1, 0), (1, 1), (1, 2), (-1, 0)], [(1, 0), (-1, 0), (1, 1), (1, 2)], [(1, 0), (1, 1), (-1, 1), (1, 2)]]; "
    "let SWG := fun (s : Nat) => (if (hsh s 630) % 10 == 0 then ({ steps := [], final := none, intercept_only := none } : StepwiseResult Float) else "
    "let io : LogisticFit Float := { names := [\"Intercept\"], beta := Np.NDArray.d1 [pk PB s 660], cov := Np.NDArray.d2 [[pk PC s 661]], "
    "loglik := -25.0 - 5.0 * Float.ofNat ((hsh s 662) % 4).toNat, n_iter := 3, converged := true }; "
    "let a := ((hsh s 670) % 36).toNat; let b := [1, 5, 7, 11, 13, 17].getD ((hsh s 671) % 6).toNat 1; "
    "let vs := (List.range 3).map (fun (k : Nat) => CAND.getD ((a + k * b) % 36) \"\"); "
    f"let K := ((hsh s 672) % {STEPS + 1}).toNat; let pat := PAT.getD ((hsh s 673) % 3).toNat []; "
    "let st := (List.range K).foldl (fun (acc : List String × List (StepwiseStep Float)) (j0 : Nat) => "
    "let j := j0 + 1; let pv := pat.getD j0 (1, 0); let name := vs.getD pv.2 \"\"; "
    "let model := if pv.1 > 0 then acc.1 ++ [name] else acc.1.filter (fun (x : String) => x != name); "
    "let f := fitG s j model io; let t := s * 16 + j; "
    "(model, acc.2 ++ [({ step := (j : Int), entered := if pv.1 > 0 then some name else none, removed := if pv.1 > 0 then none else some name, "
    "df := 1, number_in_model := (model.length : Int), score_chisq := if pv.1 > 0 then some (pk PS t 500) else none, "
    "wald_chisq := if pv.1 > 0 then none else some (pk PW t 501), p_value := pk PP t 502, fit := f } : StepwiseStep Float)])) "
    "(([] : List String), ([] : List (StepwiseStep Float))); "
    "({ steps := st.2, final := some ((st.2.getLast?.map (fun (x : StepwiseStep Float) => x.fit)).getD io), intercept_only := some io } : StepwiseResult Float)); "
)

ROUT = (
    "let solve := fun (a : List (List Float)) (b : List Float) => (let n := a.length; "
    "let M0 : Array (Array Float) := (a.zip b).toArray.map (fun (p : List Float × Float) => p.1.toArray.push p.2); "
    "let M := (List.range n).foldl (fun (M : Array (Array Float)) (k : Nat) => "
    "let pb := (List.range n).foldl (fun (pb : Nat × Float) (i : Nat) => if k < i && ((M[i]!)[k]!).abs > pb.2 then (i, ((M[i]!)[k]!).abs) else pb) (k, ((M[k]!)[k]!).abs); "
    "let Mk := M[k]!; let Mp := M[pb.1]!; let M1 := (M.set! k Mp).set! pb.1 Mk; "
    "(List.range n).foldl (fun (Mm : Array (Array Float)) (i : Nat) => if k < i then "
    "(let f := (Mm[i]!)[k]! / (Mm[k]!)[k]!; Mm.set! i ((Mm[i]!).toList.mapIdx (fun (j : Nat) (x : Float) => if k ≤ j then x - f * (Mm[k]!)[j]! else x)).toArray) else Mm) M1) M0; "
    "((List.range n).reverse.foldl (fun (x : Array Float) (i : Nat) => "
    "let s := (List.range n).foldl (fun (acc : Float) (j : Nat) => if i < j then acc - (M[i]!)[j]! * x[j]! else acc) (M[i]!)[n]!; "
    "x.set! i (s / (M[i]!)[i]!)) (List.replicate n 0.0).toArray).toList : List Float); "
    "let inv := fun (a : List (List Float)) => (let n := a.length; "
    "let cols := (List.range n).map (fun (j : Nat) => solve a ((List.range n).map (fun (i : Nat) => if i == j then (1.0 : Float) else 0.0))); "
    "(List.range n).map (fun (i : Nat) => cols.map (fun (c : List Float) => c.getD i 0.0))); "
    "let dot := fun (a b : List Float) => (List.range a.length).foldl (fun (acc : Float) (k : Nat) => acc + a.getD k 0.0 * b.getD k 0.0) 0.0; "
    "let matmul := fun (a b : List (List Float)) => a.map (fun (r : List Float) => (List.range (b.headD []).length).map (fun (j : Nat) => "
    "(List.range r.length).foldl (fun (acc : Float) (k : Nat) => acc + r.getD k 0.0 * (b.getD k []).getD j 0.0) 0.0)); "
    "let matvec := fun (a : List (List Float)) (v : List Float) => a.map (fun (r : List Float) => dot r v); "
    "let einsum := fun (x v : List (List Float)) => x.map (fun (r : List Float) => (List.range r.length).foldl (fun (acc : Float) (j : Nat) => "
    "(List.range r.length).foldl (fun (acc2 : Float) (k : Nat) => acc2 + r.getD j 0.0 * (v.getD j []).getD k 0.0 * r.getD k 0.0) acc) 0.0); "
    "let log1p := fun (x : Float) => x * 0.5; "
    "let pow2 := fun (x : Float) => x * x; "
    "let chi2 := fun (x : Float) (d : Int) => 1.0 / (1.0 + x / (Float.ofInt d + 1.0)); "
)

LGEN2 = (
    "let NV : List Nat := [1, 2, 5, 9]; "
    "let tT := fun (s : Nat) => gT s s (6 + ((hsh s 603) % 20).toNat); "
    "let tV := fun (s : Nat) => gT s (s + 1048576) (NV.getD ((hsh s 604) % 4).toNat 1); "
    "let OT := fun (s : Nat) => (let m := (hsh s 640) % 12; if m == 0 || m == 2 then none else some (tT s)); "
    "let OV := fun (s : Nat) => (let m := (hsh s 640) % 12; if m == 1 || m == 2 then none else some (tV s)); "
    "let RUN := fun (s : Nat) => run_py_py_py fw fo d8 d12 pv chi2 today (SWG s) C.FS inv solve matmul matvec dot einsum log1p pow2 (OT s) (OV s); "
    "let one := fun (s : Nat) => (match RUN s with | none => W [-1] | some r => "
    "W (((r.1.length : Int) :: (match r.2 with | none => [0] | some mj => (1 :: (match mj.1 with | none => [0] | some x => [1, bi x])) ++ "
    "[W (mj.2.flatMap (fun (p : String × Float) => ts p.1 ++ [bi p.2]))])) ++ r.1.map (fun (p : String × Tabular.Table Float) => W (TDN p)))); "
).replace("C.FS", "FS")

PREFIX = (t18.W + t18.BI + t18.TS + t18.TX + t18.TD + t18.FMT + F3.HSH + F3.LGEN + C.FS + ROUT + SWG)


def lean_input(lo: int, count: int, bad: list[int], today: str) -> str:
    return (f"({PREFIX}let today : Tabular.Cell Float := Tabular.Cell.str (some \"{today}\"); {LGEN2}"
            f"let BAD : List Nat := [{', '.join(map(str, bad))}]; "
            f"(((List.range {count}).map (fun (i : Nat) => {lo} + i)).filter (fun (s : Nat) => !(BAD.contains s))).map one)")


def gen_main(s0: int, n: int, per: int, name: str = "fz10c_train_run") -> None:
    """Seeds s0 .. s0+n-1 in calls of `per` consecutive seeds; a call skips (BAD) the seeds that are not sent: Python
    raises (outside the rendered clauses), zero pivot (LinAlgError), fsum or pow2 stand-in differs from Python's own.
    Kept seeds (precondition admits) and rejected seeds (it rejects, Python returns) are both sent."""
    s = Suite(name, generator="diffeval/units/fz10c_train_run_gen.py")
    stat: dict = {"generated": 0, "kept": 0, "rejected": Counter(), "raised": Counter(), "zero_pivot": 0, "fsum": 0, "pow2": 0,
                  "tags": Counter(), "raised_seeds": [], "rejected_seeds": []}
    today = dt.date.today().isoformat()
    for c0 in range(s0, s0 + n, per):
        hi = min(c0 + per, s0 + n)
        bad, cases = [], []
        for seed in range(c0, hi):
            stat["generated"] += 1
            r = pyrun(seed)
            fz, tg = "kept", ["stop"]
            if r["stop"]:
                assert r["raised"] is not None and r["raised"].startswith("ValueError") and not r["writes"], r["raised"]
            elif not r["held"]:
                stat["not_held"] = stat.get("not_held", 0) + 1
                bad.append(seed)
                continue
            elif r["zero_pivot"]:
                stat["zero_pivot"] += 1
                bad.append(seed)
                continue
            elif r["raised"] is not None:
                stat["raised"][r["raised"][:60]] += 1
                stat["raised_seeds"].append(seed)
                bad.append(seed)
                continue
            elif not r["fsum_ok"]:
                stat["fsum"] += 1
                bad.append(seed)
                continue
            elif not pow2_ok(r):
                stat["pow2"] += 1
                bad.append(seed)
                continue
            else:
                ok, why = pre(r)
                tg = tags(r)
                if not ok:
                    fz = "rejected"
                    stat["rejected"][why] += 1
                    stat["rejected_seeds"].append(seed)
                    tg = [f"rejected: {why}"] + tg
            if fz == "kept":
                stat["kept"] += 1
                for t in tg:
                    stat["tags"][t] += 1
            cases.append((f"seed {seed} [{', '.join(tg) or 'fitted'}]: {r['nt']} training / {r['nv']} validation rows, "
                          f"{'stop' if r['stop'] else str(len(r['writes'])) + ' files'}", U, expected(r), {"fz": fz}))
        for pos, cc in enumerate(cases):
            s._case(cc[0], cc[1], cc[2], pos, "int", **cc[3])
        s._input("ints", lean_input(c0, hi - c0, bad, today))
    s.write()
    out = {k: (dict(v) if isinstance(v, Counter) else v) for k, v in stat.items()}
    (WORK / f"{name}.stat.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps({k: v for k, v in out.items() if k not in ("raised_seeds", "rejected_seeds")}, default=str))
    for g in json.loads((WORK / f"{name}.inputs.json").read_text()):
        print([len(x) for x in g["inputs"]])


def _old_gen_main(s0: int, n: int, per: int) -> None:  # superseded (kept-only, explicit seed lists)
    s = Suite("fz10c_train_run_old")
    stat: dict = {"generated": 0, "kept": 0, "rejected": Counter(), "raised": Counter(), "zero_pivot": 0, "fsum": 0, "pow2": 0,
                  "tags": Counter(), "raised_seeds": [], "rejected_seeds": {}}
    today = dt.date.today().isoformat()
    kept: list[tuple[int, int, list[str], dict]] = []
    for seed in range(s0, s0 + n):
        stat["generated"] += 1
        r = pyrun(seed)
        if r["stop"]:
            assert r["raised"] is not None and r["raised"].startswith("ValueError") and not r["writes"], r["raised"]
            kept.append((seed, expected(r), ["stop"], r))
            continue
        if r["zero_pivot"]:
            stat["zero_pivot"] += 1
            continue
        if r["raised"] is not None:
            stat["raised"][r["raised"][:60]] += 1
            stat["raised_seeds"].append(seed)
            continue
        if not r["fsum_ok"]:
            stat["fsum"] += 1
            continue
        if not pow2_ok(r):
            stat["pow2"] += 1
            continue
        ok, why = pre(r)
        if not ok:
            stat["rejected"][why] += 1
            stat["rejected_seeds"][seed] = (why, expected(r))
            continue
        kept.append((seed, expected(r), tags(r), r))
    for _, _, tg, _ in kept:
        for t in tg:
            stat["tags"][t] += 1
    stat["kept"] = len(kept)
    for c in range(0, len(kept), per):
        part = kept[c:c + per]
        cases = [(f"seed {sd} [{', '.join(tg) or 'fitted'}]: {r['nt']} training / {r['nv']} validation rows, "
                  f"{'stop' if r['stop'] else str(len(r['writes'])) + ' files'}", U, e, {"fz": "kept"}) for sd, e, tg, r in part]
        for pos, cc in enumerate(cases):
            s._case(cc[0], cc[1], cc[2], pos, "int", **cc[3])
        s._input("ints", lean_input([sd for sd, _, _, _ in part], today))
    s.write()
    out = {k: (dict(v) if isinstance(v, Counter) else v) for k, v in stat.items()}
    (WORK / "fz10c_train_run.stat.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps({k: v for k, v in out.items() if k not in ("raised_seeds", "rejected_seeds")}, default=str))
    for g in json.loads((WORK / "fz10c_train_run.inputs.json").read_text()):
        print([len(x) for x in g["inputs"]])


if __name__ == "__main__":
    if sys.argv[1] == "gen":
        gen_main(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), *(sys.argv[5:6]))
    elif sys.argv[1] == "one":
        r = pyrun(int(sys.argv[2]))
        print(r["stop"], r["raised"], r["zero_pivot"], r["fsum_ok"], [n for n, _ in r["writes"]], r["model_json"])
        if r["locals"] is not None:
            print(pre(r), pow2_ok(r), tags(r))


# ------------------------------------------------------------------ localisation of a differing seed
ONEL = ("let oneL : Nat → List Int := fun (s : Nat) => (match RUN s with | none => ([-1] : List Int) | some r => "
        "((r.1.length : Int) :: (match r.2 with | none => [0] | some mj => (1 :: (match mj.1 with | none => [0] | some x => [1, bi x])) ++ "
        "[W (mj.2.flatMap (fun (p : String × Float) => ts p.1 ++ [bi p.2]))])) ++ r.1.flatMap TDN); ")


def diag_main(seeds: list[int]) -> None:
    """per seed: number of files, model.json tokens, and per file [W(name), rows, columns, W(column)...] (t18 tdn),
    each value one case labelled by file and column."""
    s = Suite("fz10c_train_run_diag", generator="diffeval/units/fz10c_train_run_gen.py")
    today = dt.date.today().isoformat()
    cases = []
    for seed in seeds:
        r = pyrun(seed)
        mj = r["model_json"]
        mt = [0] if mj is None else [1] + t18.o(mj["intercept"]) + [t18.w([t for c, b in mj["coefficients"].items() for t in t18.ts(c) + [t18.fb(b)]])]
        vals = [(f"seed {seed}: number of files", len(r["writes"]))] + [(f"seed {seed}: model.json token {i}", v) for i, v in enumerate(mt)]
        for n, df in r["writes"]:
            labs = t18.labels_tdn(n, df)
            vals += [(f"seed {seed}: {lab}", v) for lab, v in zip(labs, t18.tdn(n, df), strict=True)]
        cases += [(lab, U, v, {"fz": "kept"}) for lab, v in vals]
    for pos, cc in enumerate(cases):
        s._case(cc[0], cc[1], cc[2], pos, "int", **cc[3])
    s._input("ints", f"({PREFIX}let today : Tabular.Cell Float := Tabular.Cell.str (some \"{today}\"); {LGEN2[:LGEN2.index('let one :=')]}{ONEL}"
                     f"[{', '.join(map(str, seeds))}].flatMap oneL)")
    s.write()
    print(len(s.inputs[0]["text"]))


if __name__ == "__main__" and sys.argv[1] == "diag":
    diag_main([int(x) for x in sys.argv[2:]])


# ------------------------------------------------------------------ real data (the real feature files, windows)
REAL_DIR = WORK / "fz10_glue_real_out"  # the port's own feature-engineering output on the real legacy data


def real_windows() -> list[tuple[str, pl.DataFrame, pl.DataFrame]]:
    ftr = sc.proc_import_csv(REAL_DIR / "model_features_train.csv")
    fva = sc.proc_import_csv(REAL_DIR / "model_features_validation.csv")
    assert ftr.columns == list(F3.NAMES) if hasattr(F3, "NAMES") and isinstance(F3.NAMES, list) else True
    d1 = ftr.with_row_index("_i").filter(pl.col("default_flag") == 1.0).head(4).get_column("_i").to_list()
    d0 = ftr.with_row_index("_i").filter(pl.col("default_flag") == 0.0).head(4).get_column("_i").to_list()
    v1 = fva.with_row_index("_i").filter(pl.col("default_flag") == 1.0).head(1).get_column("_i").to_list()
    v0 = fva.with_row_index("_i").filter(pl.col("default_flag") == 0.0).head(2).get_column("_i").to_list()
    return [
        ("train rows 0-7, validation rows 0-2", ftr[0:8], fva[0:3]),
        ("train rows 60000-60007, validation rows 30000-30002", ftr[60000:60008], fva[30000:30003]),
        (f"4 defaults + 4 non-defaults (train rows {sorted(d1 + d0)}), validation rows {sorted(v1 + v0)}",
         ftr[sorted(d1 + d0)], fva[sorted(v1 + v0)]),
    ]


def enc_real(x: float) -> int:
    """a non-negative integer value below 2^53 as itself, any other value as its bits (bits of the values of the
    real files are all >= 2^53: asserted by decoding)"""
    n = int(x) if x >= 0 and x == int(x) and x < 2.0**53 and math.copysign(1, x) > 0 else t18.fb(x)
    dec = float(n) if n < 2**53 else C.cmp.fbits.__class__ and np.frombuffer(np.uint64(n).tobytes(), dtype=np.float64)[0]
    assert t18.fb(float(dec)) == t18.fb(x), (x, n)
    return n


def real_main(seeds: list[int]) -> None:
    s = Suite("fz10c_train_run_real", generator="diffeval/units/fz10c_train_run_gen.py")
    today = dt.date.today().isoformat()
    wins = real_windows()
    names = wins[0][1].columns
    lets, calls, cases, stat = [], [], [], Counter()
    for wi, (lab, ft, fv) in enumerate(wins):
        assert ft.columns == names and fv.columns == names and all(t == pl.Float64 for t in ft.dtypes + fv.dtypes)
        for nm, df in ((f"T{wi}", ft), (f"V{wi}", fv)):
            rows = ", ".join("[" + ", ".join(str(enc_real(x)) for x in r) + "]" for r in df.rows())
            lets.append(f"let {nm} := mkT [{rows}]; ")
        for seed in seeds:
            FR_OVERRIDE[0] = (ft, fv)
            try:
                r = pyrun(seed)
            finally:
                FR_OVERRIDE[0] = None
            if not r["held"] or r["zero_pivot"] or r["raised"] is not None or not r["fsum_ok"] or not pow2_ok(r):
                stat["dropped: " + ("not held" if not r["held"] else "zero pivot" if r["zero_pivot"] else
                                    f"raised {r['raised'][:50]}" if r["raised"] else "fsum" if not r["fsum_ok"] else "pow2")] += 1
                continue
            ok, why = pre(r)
            fz = "kept" if ok else "rejected"
            stat[fz if ok else f"rejected: {why}"] += 1
            tg = ([] if ok else [f"rejected: {why}"]) + tags(r)
            cases.append((f"real window {wi} ({lab}), stepwise seed {seed} [{', '.join(tg) or 'fitted'}]: {len(r['writes'])} files",
                          U, expected(r), {"fz": fz}))
            calls.append(f"oneR {seed} T{wi} V{wi}")
    mk = ("let NAMESR : List String := " + json.dumps(names) + "; "
          "let mkT := fun (L : List (List Nat)) => (L.map (fun (r : List Nat) => (NAMESR.zip r).map (fun (p : String × Nat) => "
          "(p.1, Tabular.Cell.num (some (if p.2 < 9007199254740992 then Float.ofNat p.2 else Float.ofBits p.2.toUInt64))))) : Tabular.Table Float); ")
    oner = ("let oneR : Nat → Tabular.Table Float → Tabular.Table Float → Int := fun (s : Nat) (T V : Tabular.Table Float) => "
            "(match run_py_py_py fw fo d8 d12 pv chi2 today (SWG s) FS inv solve matmul matvec dot einsum log1p pow2 (some T) (some V) with "
            "| none => W [-1] | some r => "
            "W (((r.1.length : Int) :: (match r.2 with | none => [0] | some mj => (1 :: (match mj.1 with | none => [0] | some x => [1, bi x])) ++ "
            "[W (mj.2.flatMap (fun (p : String × Float) => ts p.1 ++ [bi p.2]))])) ++ r.1.map (fun (p : String × Tabular.Table Float) => W (TDN p)))); ")
    for pos, cc in enumerate(cases):
        s._case(cc[0], cc[1], cc[2], pos, "int", **cc[3])
    s._input("ints", f"({PREFIX}let today : Tabular.Cell Float := Tabular.Cell.str (some \"{today}\"); {mk}{''.join(lets)}{oner}"
                     f"[{', '.join(calls)}])")
    s.write()
    print(dict(stat), len(s.inputs[0]["text"]))
    (WORK / "fz10c_train_run_real.stat.json").write_text(json.dumps(dict(stat), indent=1))


if __name__ == "__main__" and sys.argv[1] == "real":
    real_main([int(x) for x in sys.argv[2:]])
