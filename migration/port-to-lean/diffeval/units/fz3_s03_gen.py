"""Fuzz of the update of 2026-11-17 (third diff), a non-author: def:train_run_03_fit_global_rsquare and
its precondition, carrier def:zz_carrier_t, blueprint 5365851c-5549-44b7-9207-4bd4c422031d. Nothing is
changed on the blueprint.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz3_s03_gen.py \
      [--list A B] [--text A B]       (seed range)  /  --check

Case of seed s (built INSIDE Lean from hsh, mirrored here): a stepwise result of 0..3 steps whose fits are
SYNTHETIC (names, beta, cov, loglik drawn from edge pools, not a real stepwise run), a fit frame of the
columns a..d (n_obs 0..8 rows), y_train, ybar, m2ll0 and a candidates list. The cov of a step is built in one
of five modes so that the Wald sweep meets its thresholds: diagonal only (off-diagonals exactly 0: pivot =
the diagonal, drawn on and one ulp either side of 1.5e-16), pool off-diagonals, all entries equal (rank 1),
asymmetric, and diag d with off-diagonals d * r (r = 1 - k ulp: pivots of about 2e-16). A diagonal 0.0 / -0.0
on a slope gives the NaN Wald with DF q - left out. Candidates: a rotation of a..e, reversed or not,
doubled or not, the first name dropped now and then (a slope not in it makes Python raise).

Routines (parameters of the Lean) are stand-ins written identically on both sides, with numpy patched on the
Python side while the REAL source lines train.py:154-268 (u03_gen.run_slice, with chi2_sf a stand-in) and the
REAL sas_compat.global_wald run:
  solve  Gaussian elimination, partial pivoting (first strict max of |.|), no raise (a pivot that is exactly 0 after
         the swap is flagged: the real np.linalg.solve would raise LinAlgError, outside the model, RULEBOOK 3)
  matmul / matvec / dot  sequential sums from 0.0 in index order
  chi2   fun x d => x * 0.5 + float d
  formatters  the injective encodings of t18_gen (fw, d12, pv).
Compared per seed: the digest of the generated inputs (generator mirror) and the digest of the unit's output pairs.

Precondition (def:train_run_03_fit_global_rsquare_precond) rendered as `pre`: frame names distinct, column
lengths = height = n_obs = len y_train; for every step with len(names) - 1 != 0: 0 < n_obs; every slope is a
frame column (Float64, no null by construction) and is in candidates; beta 1-D and cov 2-D (by construction),
len(names) <= len(beta), len(cov) = len(beta), rows of len(cov) (by construction: m x m); exp(-lr/n_obs) finite;
exp(-m2ll0/n_obs) finite; 1 - exp(-m2ll0/n_obs) != 0.
"""
from __future__ import annotations

import json
import math
import struct
import sys
import types
from pathlib import Path

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import kit  # noqa: E402
import t18_gen as t  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402

M64 = (1 << 64) - 1
hsh = kit.hsh


def bits(x: float) -> int:
    return struct.unpack("<Q", struct.pack("<d", x))[0]


def flt(b: int) -> float:
    return struct.unpack("<d", struct.pack("<Q", b & M64))[0]


NAN, INF = float("nan"), float("inf")
TOL = 1.5e-16
up, dn = (lambda x: math.nextafter(x, INF)), (lambda x: math.nextafter(x, -INF))
BE = [0.0, -0.0, 1.0, -1.0, 1e300, 1e-300, NAN, INF, -INF, 5e-324, 0.5]
DG = [0.0, -0.0, TOL, dn(TOL), up(TOL), 1e-16, 2e-16, 1.0, 1e-300, 5e-324, NAN, INF, -1.0, 1e300, 1e-15, 1e-17, 3e-16, 2.0]
OF = [0.0, -0.0, 1.0, -1.0, 0.5, 1e-8, TOL, NAN, 1e-16, 1e300, -TOL, 1e-300]
D4 = [1.0, 2.0, 0.5, 1e-8, 1e-16, 2e-16, TOL, 4.0]
DL = [1.0, 1 - 2.0**-53, 1 - 2.0**-52, 1 - 2.0**-51, 1 - 1e-15, 0.5, -1.0, -(1 - 2.0**-53), 1 - 2.0**-50]
LLE = [0.0, -0.0, -1.0, -100.0, -1e-300, -1e300, NAN, INF, -INF, -5e-324, -0.5, -353.0, -355.0]
M0E = [0.0, 1.0, 100.0, 1e300, -1.0, NAN, 1e-300, 5e-324, 700.0, 710.0, INF, -0.0]
XE = [0.0, -0.0, 1.0, -1.0, NAN, INF, 1e300, 1e-300, 5e-324, -INF]
YE = [0.0, 1.0, 0.5, NAN, -0.0, 1e300, 2.0, -1.0]
YBE = [0.0, 1.0, 0.5, NAN, -0.0, 1e-300, INF, 1 - 2.0**-53, 2.0**-53]
POOLS = dict(BE=BE, DG=DG, OF=OF, D4=D4, DL=DL, LLE=LLE, M0E=M0E, XE=XE, YE=YE, YBE=YBE)


def fpick(E, u):
    return E[(u >> 20) % len(E)]


def rnd(u, eh):
    b = (u & 0x8000000000000000) | (((1023 - eh + (u >> 52) % (2 * eh + 1)) * 0x10000000000000) & M64) | (u & 0xFFFFFFFFFFFFF)
    return flt(b)


def gen(E, pe, eh, tt, k):
    u = hsh(tt, k)
    return fpick(E, u) if (u >> 8) % 100 < pe else rnd(u, eh)


BASE = ["a", "b", "c", "d", "e"]
POOL4 = ["a", "b", "c", "d"]


def cand(s):
    r = hsh(s, 10) % 5
    l = BASE[r:] + BASE[:r]
    if hsh(s, 11) % 2 == 0:
        l = l[::-1]
    if hsh(s, 12) % 8 == 0:
        l = l + l
    return l[1:] if hsh(s, 13) % 12 == 0 else l


def nobs(s):
    return 0 if hsh(s, 40) % 10 == 0 else hsh(s, 41) % 8 + 1


def colv(s, c, n):
    out = []
    for i in range(n):
        u = hsh(s * 13 + 100 + c, i)
        out.append(fpick(XE, u) if (u >> 8) % 100 < 10 else float((u >> 20) % 5) - 2.0)
    return out


def yv(s, n):
    out = []
    for i in range(n):
        u = hsh(s * 13 + 99, i)
        out.append(fpick(YE, u) if (u >> 8) % 100 < 8 else (1.0 if (u >> 20) % 2 == 0 else 0.0))
    return out


def step(tt):
    q = hsh(tt, 0) % 5
    r = hsh(tt, 1) % 4
    pr = POOL4[r:] + POOL4[:r]
    if hsh(tt, 2) % 2 == 0:
        pr = pr[::-1]
    sl = pr[:q]
    if hsh(tt, 3) % 10 == 0 and q > 0:
        sl = sl + [POOL4[hsh(tt, 4) % 4]]
    names = [] if hsh(tt, 6) % 40 == 0 else ["Intercept"] + sl
    m = len(names)
    mode = hsh(tt, 5) % 5
    beta = [gen(BE, 45, 8, tt, 100 + i) for i in range(m)]

    def ent(i, j):
        a, b = min(i, j), max(i, j)
        if mode == 0:
            return gen(DG, 70, 30, tt, 200 + a) if a == b else 0.0
        if mode == 1:
            return gen(DG, 70, 30, tt, 200 + a) if a == b else gen(OF, 60, 20, tt, 300 + a * 8 + b)
        if mode == 2:
            return gen(DG, 70, 30, tt, 200)
        if mode == 3:
            return gen(DG, 70, 30, tt, 200 + i) if i == j else gen(OF, 60, 20, tt, 400 + i * 8 + j)
        d = fpick(D4, hsh(tt, 210))
        return d if i == j else d * fpick(DL, hsh(tt, 211))

    cov = [[ent(i, j) for j in range(m)] for i in range(m)]
    h = hsh(tt, 7)
    ll = fpick(LLE, h) if (h >> 8) % 100 < 25 else -float((h >> 20) % 8000) / 16.0
    return names, beta, cov, ll


def case(s):
    n = nobs(s)
    ns = hsh(s, 20) % 4
    steps = [step(s * 8 + j + 1) for j in range(ns)]
    cols = [c for c in POOL4 if not (c == "d" and hsh(s, 14) % 20 == 0)]
    frame = {c: colv(s, POOL4.index(c), n) for c in cols}
    y = yv(s, n)
    h = hsh(s, 15)
    ybar = fpick(YBE, hsh(s, 16)) if h % 100 < 12 else [0.5, 0.25, 0.3, 0.75, 0.4, 0.6][(h >> 20) % 6]
    h = hsh(s, 17)
    m0 = fpick(M0E, h) if (h >> 8) % 100 < 25 else 50.0 + float((hsh(s, 18) >> 20) % 4000) / 8.0
    return dict(s=s, n=n, steps=steps, frame=frame, y=y, ybar=ybar, m0=m0, cand=cand(s))


def in_digest(c):
    xs = [c["n"], len(c["steps"])]
    for names, beta, cov, ll in c["steps"]:
        xs += [len(names)] + [x for nm in names for x in t.ts(nm)] + [bits(b) for b in beta] + [bits(v) for r in cov for v in r] + [bits(ll)]
    for nm, v in c["frame"].items():
        xs += t.ts(nm) + [len(v)] + [bits(x) if x == x else bits(NAN) for x in v]
    xs += [bits(x) for x in c["y"]] + [bits(c["ybar"]), bits(c["m0"])] + [x for nm in c["cand"] for x in t.ts(nm)] + [len(c["cand"])]
    return t.w([x if x >= 0 else x for x in xs])


# ---- stand-in routines (mirrors of the Lean lets)
FLAG = {"zero_pivot": False}


class NA(np.ndarray):
    def __matmul__(self, o):
        a, b = np.asarray(self), np.asarray(o)
        if a.ndim == 2 and b.ndim == 2:
            r = np.zeros((a.shape[0], b.shape[1]))
            for i in range(a.shape[0]):
                for j in range(b.shape[1]):
                    acc = 0.0
                    for k in range(a.shape[1]):
                        acc += a[i, k] * b[k, j]
                    r[i, j] = acc
            return r.view(NA)
        if a.ndim == 2 and b.ndim == 1:
            r = np.zeros(a.shape[0])
            for i in range(a.shape[0]):
                acc = 0.0
                for k in range(a.shape[1]):
                    acc += a[i, k] * b[k]
                r[i] = acc
            return r.view(NA)
        assert a.ndim == 1 and b.ndim == 1, (a.shape, b.shape)
        acc = 0.0
        for k in range(a.shape[0]):
            acc += a[k] * b[k]
        return np.float64(acc)


def na(a):
    return np.asarray(a, dtype=np.float64).view(NA)


def solve_sa(a, b):
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


def chi2_st(x, df):
    return float(x) * 0.5 + float(df)


def run_slice(stepwise, L):
    from credit_risk import train
    src = Path(train.__file__).read_text().splitlines()
    import textwrap
    assert src[161].strip() == 'fs_step: list[str] = ["0"]' and "printed_rsquare.csv" in src[282]
    code = textwrap.dedent("\n".join(src[161:283]))
    writes = []
    proxy = types.SimpleNamespace(sas_d12_3=t.ENCODERS["sas_d12_3"], fmt_wd=t.ENCODERS["fmt_wd"], sas_pvalue=t.ENCODERS["sas_pvalue"],
                                  chi2_sf=chi2_st, write_sas_csv=lambda df, path, formats=None: writes.append((Path(path).name, df.clone())),
                                  global_wald=sc.global_wald)
    ns = {"sas_compat": proxy, "np": np, "pl": pl, "math": math, "stepwise": stepwise, "output_dir": Path("out"),
          "candidates": L["cand"], **{k: L[k] for k in ("m2ll0", "n_obs", "fit_frame", "y_train", "ybar")}}
    o_solve, o_cs = np.linalg.solve, np.column_stack
    np.linalg.solve = solve_sa
    np.column_stack = lambda cols: na(o_cs(cols))
    try:
        exec(compile(code, "train.py:154-268", "exec"), ns)  # noqa: S102
    finally:
        np.linalg.solve, np.column_stack = o_solve, o_cs
    return writes


def pexp(x):
    try:
        return math.exp(x)
    except OverflowError:
        return INF


def pre(c, ll_steps):
    n = c["n"]
    cols = list(c["frame"])
    if not (len(set(cols)) == len(cols) and len(c["y"]) == n):
        return False
    for st, (names, beta, cov, ll) in zip(ll_steps, c["steps"]):
        if len(names) - 1 == 0:
            continue
        if not 0 < n:
            return False
        if not all(nm in c["frame"] for nm in names[1:]) or not all(nm in c["cand"] for nm in names[1:]):
            return False
        if not len(names) <= len(beta) or len(cov) != len(beta) or any(len(r) != len(cov) for r in cov):
            return False
        lr = c["m0"] - (-2.0) * ll
        with np.errstate(all="ignore"):
            e1 = pexp(-(c["m0"] - (-2.0) * ll) / n)
            e0 = pexp(-c["m0"] / n)
        if not math.isfinite(e1) or not math.isfinite(e0) or 1.0 - e0 == 0.0:
            return False
    return True


def py_case(c):
    """-> (class, digest or None, extra). class: kept | rejected | raise_in_pre | dropped | linalg"""
    fits = [sc.LogisticFit(names=list(nm), beta=na(np.array(b, dtype=np.float64)), cov=na(np.array(cv, dtype=np.float64).reshape(len(nm), len(nm))),
                           loglik=ll, n_iter=0, converged=True, separation=None) for nm, b, cv, ll in c["steps"]]
    steps = [sc.StepwiseStep(step=j + 1, entered=None, removed=None, df=1, number_in_model=0, score_chisq=None, wald_chisq=None, p_value=0.5, fit=f)
             for j, f in enumerate(fits)]
    sw = sc.StepwiseResult(steps, None, None)
    admits = pre(c, steps)
    ff = pl.DataFrame({k: pl.Series(v, dtype=pl.Float64) for k, v in c["frame"].items()}) if c["frame"] else pl.DataFrame()
    L = dict(m2ll0=c["m0"], n_obs=c["n"], fit_frame=ff, y_train=na(np.array(c["y"], dtype=np.float64)), ybar=c["ybar"], cand=c["cand"])
    FLAG["zero_pivot"] = False
    try:
        with np.errstate(all="ignore"):
            ws = run_slice(sw, L)
    except Exception as e:  # noqa: BLE001
        return ("raise_in_pre" if admits else "dropped"), None, f"{type(e).__name__}: {str(e)[:60]}"
    d = t.w([len(ws)] + [x for n_, df in ws for x in t.tdn(n_, df)])
    core, rs = [len(ws)], []
    for n_, df in ws:
        L = t.tdn(n_, df)
        if n_ == "printed_rsquare.csv":
            core += L[:5] + [L[7] if len(L) > 7 else 0]
            rs += [L[i] if i < len(L) else 0 for i in (5, 6, 8, 9)]
        else:
            core += L
    exl = []
    if c["n"] > 0:
        for names, beta, cov, ll in c["steps"]:
            if len(names) - 1 != 0:
                exl += [bits(pexp(-(c["m0"] - (-2.0) * ll) / c["n"])), bits(pexp(-c["m0"] / c["n"]))]
    LISTS[c["s"]] = (core, rs, exl)
    if FLAG["zero_pivot"]:
        return "linalg", d, ""
    return ("kept" if admits else "rejected"), d, ""


LISTS = {}


# ---- Lean text
def u64(xs):
    return "[" + ", ".join(hex(bits(x)) for x in xs) + "]"


LEAN_POOLS = "".join(f"let {k} : List UInt64 := {u64(v)}; " for k, v in POOLS.items())
LEAN_ROUT = (
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
    "let dot := fun (a b : List Float) => (List.range a.length).foldl (fun (acc : Float) (k : Nat) => acc + a.getD k 0.0 * b.getD k 0.0) 0.0; "
    "let matvec := fun (a : List (List Float)) (v : List Float) => a.map (fun (r : List Float) => dot r v); "
    "let matmul := fun (a b : List (List Float)) => a.map (fun (r : List Float) => (List.range (b.headD []).length).map (fun (j : Nat) => "
    "(List.range r.length).foldl (fun (acc : Float) (k : Nat) => acc + r.getD k 0.0 * (b.getD k []).getD j 0.0) 0.0)); "
    "let chi2 := fun (x : Float) (d : Int) => x * 0.5 + Float.ofInt d; "
)
LEAN_GEN = (
    "let fpick := fun (E : List UInt64) (u : UInt64) => Float.ofBits (E.getD ((u >>> 20) % E.length.toUInt64).toNat 0); "
    "let rnd := fun (u : UInt64) (eh : UInt64) => let k : UInt64 := u >>> 52; Float.ofBits ((u &&& 0x8000000000000000) ||| ((1023 - eh + k % (2 * eh + 1)) * 0x10000000000000) ||| (u &&& 0xFFFFFFFFFFFFF)); "
    "let gen := fun (E : List UInt64) (pe eh : UInt64) (tt k : Nat) => let u := hsh tt k; if (u >>> 8) % 100 < pe then fpick E u else rnd u eh; "
    'let BASE : List String := ["a", "b", "c", "d", "e"]; let P4 : List String := ["a", "b", "c", "d"]; '
    "let cand := fun (s : Nat) => (let r := ((hsh s 10) % 5).toNat; let l := BASE.drop r ++ BASE.take r; let l := if (hsh s 11) % 2 == 0 then l.reverse else l; "
    "let l := if (hsh s 12) % 8 == 0 then l ++ l else l; if (hsh s 13) % 12 == 0 then l.drop 1 else l); "
    "let nobs := fun (s : Nat) => if (hsh s 40) % 10 == 0 then 0 else ((hsh s 41) % 8).toNat + 1; "
    "let colv := fun (s c n : Nat) => (List.range n).map (fun (i : Nat) => let u := hsh (s * 13 + 100 + c) i; "
    "if (u >>> 8) % 100 < 10 then fpick XE u else Float.ofNat ((u >>> 20) % 5).toNat - 2.0); "
    "let yv := fun (s n : Nat) => (List.range n).map (fun (i : Nat) => let u := hsh (s * 13 + 99) i; "
    "if (u >>> 8) % 100 < 8 then fpick YE u else if (u >>> 20) % 2 == 0 then 1.0 else 0.0); "
    "let step := fun (tt : Nat) => (let q := ((hsh tt 0) % 5).toNat; let r := ((hsh tt 1) % 4).toNat; let pr := P4.drop r ++ P4.take r; "
    "let pr := if (hsh tt 2) % 2 == 0 then pr.reverse else pr; let sl := pr.take q; "
    'let sl := if (hsh tt 3) % 10 == 0 && q > 0 then sl ++ [P4.getD ((hsh tt 4) % 4).toNat "a"] else sl; '
    'let names : List String := if (hsh tt 6) % 40 == 0 then [] else "Intercept" :: sl; let m := names.length; let mode := (hsh tt 5) % 5; '
    "let beta := (List.range m).map (fun (i : Nat) => gen BE 45 8 tt (100 + i)); "
    "let ent := fun (i j : Nat) => (let a := min i j; let b := max i j; "
    "if mode == 0 then (if a == b then gen DG 70 30 tt (200 + a) else 0.0) "
    "else if mode == 1 then (if a == b then gen DG 70 30 tt (200 + a) else gen OF 60 20 tt (300 + a * 8 + b)) "
    "else if mode == 2 then gen DG 70 30 tt 200 "
    "else if mode == 3 then (if i == j then gen DG 70 30 tt (200 + i) else gen OF 60 20 tt (400 + i * 8 + j)) "
    "else (let d := fpick D4 (hsh tt 210); if i == j then d else d * fpick DL (hsh tt 211))); "
    "let cov := (List.range m).map (fun (i : Nat) => (List.range m).map (fun (j : Nat) => ent i j)); "
    "let h := hsh tt 7; let ll := if (h >>> 8) % 100 < 25 then fpick LLE h else -(Float.ofNat ((h >>> 20) % 8000).toNat) / 16.0; "
    "(names, beta, cov, ll)); "
    "let mk := fun (s : Nat) => (let n := nobs s; let ns := ((hsh s 20) % 4).toNat; "
    "let sts := (List.range ns).map (fun (j : Nat) => step (s * 8 + j + 1)); "
    "let cols := P4.filter (fun (c : String) => !(c == \"d\" && (hsh s 14) % 20 == 0)); "
    "let ff : Pl.Frame Float := cols.map (fun (c : String) => (c, Pl.Col.f64 ((colv s (P4.idxOf c) n).map some))); "
    "let h := hsh s 15; let ybar := if h % 100 < 12 then fpick YBE (hsh s 16) else ([0.5, 0.25, 0.3, 0.75, 0.4, 0.6] : List Float).getD ((h >>> 20) % 6).toNat 0.0; "
    "let h := hsh s 17; let m0 := if (h >>> 8) % 100 < 25 then fpick M0E h else 50.0 + Float.ofNat ((hsh s 18 >>> 20) % 4000).toNat / 8.0; "
    "(sts, ff, n, yv s n, ybar, m0, cand s)); "
    "let SWof := fun (sts : List (List String × List Float × List (List Float) × Float)) => ({ steps := sts.mapIdx (fun (j : Nat) (p : List String × List Float × List (List Float) × Float) => "
    "({ step := (j : Int) + 1, entered := none, removed := none, df := 1, number_in_model := 0, score_chisq := none, wald_chisq := none, p_value := 0.5, "
    "fit := { names := p.1, beta := Np.NDArray.d1 p.2.1, cov := Np.NDArray.d2 p.2.2.1, loglik := p.2.2.2, n_iter := 0, converged := true, separation := none } } : StepwiseStep Float)) } : StepwiseResult Float); "
)
LEAN_DIG = (
    "let iw := fun (s : Nat) => (let (sts, ff, n, y, ybar, m0, cd) := mk s; "
    "W ([(n : Int), (sts.length : Int)] ++ sts.flatMap (fun (p : List String × List Float × List (List Float) × Float) => "
    "(p.1.length : Int) :: p.1.flatMap ts ++ p.2.1.map bi ++ p.2.2.1.flatMap (fun (r : List Float) => r.map bi) ++ [bi p.2.2.2]) ++ "
    "ff.flatMap (fun (p : String × Pl.Col Float) => ts p.1 ++ (match p.2 with | .f64 v => (v.length : Int) :: v.map (fun (o : Option Float) => (match o with | some x => bi x | none => 0)) | _ => [])) ++ "
    "y.map bi ++ [bi ybar, bi m0] ++ cd.flatMap ts ++ [(cd.length : Int)])); "
    "let ow := fun (s : Nat) => (let (sts, ff, n, y, ybar, m0, cd) := mk s; "
    "let o := train_run_03_fit_global_rsquare fw d12 pv chi2 (SWof sts) solve matmul matvec dot ff (n : Int) y m0 ybar cd; "
    "W ((o.length : Int) :: o.flatMap TDN)); "
)
LEAN_TRIP = (
    "let trip := fun (s : Nat) => (let (sts, ff, n, y, ybar, m0, cd) := mk s; "
    "let o := train_run_03_fit_global_rsquare fw d12 pv chi2 (SWof sts) solve matmul matvec dot ff (n : Int) y m0 ybar cd; "
    "let core : List Int := (o.length : Int) :: o.flatMap (fun (p : String \u00d7 Tabular.Table Float) => let L := TDN p; if p.1 == \"printed_rsquare.csv\" then L.take 5 ++ [L.getD 7 0] else L); "
    "let rsl : List Int := o.flatMap (fun (p : String \u00d7 Tabular.Table Float) => if p.1 == \"printed_rsquare.csv\" then (let L := TDN p; [L.getD 5 0, L.getD 6 0, L.getD 8 0, L.getD 9 0]) else []); "
    "let exl : List Int := sts.flatMap (fun (p : List String \u00d7 List Float \u00d7 List (List Float) \u00d7 Float) => if p.1.length != 1 then "
    "[bi (Float.exp ((-(m0 - (-(2.0 : Float)) * p.2.2.2)) / Float.ofNat n)), bi (Float.exp ((-m0) / Float.ofNat n))] else []); "
    "(core, rsl, exl)); "
    "let blk := fun (b : List Nat) => (let r := b.map trip; [W (r.flatMap (fun (t : List Int \u00d7 List Int \u00d7 List Int) => t.1)), W (r.flatMap (fun (t : List Int \u00d7 List Int \u00d7 List Int) => t.2.1)), W (r.flatMap (fun (t : List Int \u00d7 List Int \u00d7 List Int) => t.2.2))]); "
)
LEAN_PRE = t.W + t.BI + t.TS + t.TX + t.TD + t.FMT + kit.GEN.split("let gF")[0] + LEAN_POOLS + LEAN_ROUT + LEAN_GEN + LEAN_DIG + LEAN_TRIP


CLS = {"dropped": "0", "kept": "1", "rejected": "2", "linalg": "3", "raise_in_pre": "4"}


def wald_stats(c):
    """what the Wald sweep of each step with q != 0 did (mirror of sas_compat.global_wald, with the stand-in solve)"""
    st = {"steps": 0, "nan": 0, "left_out_pivot": 0, "pivot_eq_tol": 0, "pivot_1ulp_above": 0, "pivot_1ulp_below": 0, "df_lt_q": 0, "empty_kept": 0}
    for names, beta, cov, ll in c["steps"]:
        if len(names) - 1 == 0:
            continue
        st["steps"] += 1
        m = len(names)
        diag0 = [i for i in range(m) if float(cov[i][i]) == 0.0 and names[i] != "Intercept"]
        if diag0:
            st["nan"] += 1
            continue
        slopes = sorted(names[1:], key=list(c["cand"]).index) if all(n in c["cand"] for n in names[1:]) else None
        if slopes is None:
            continue
        idx = [names.index(x) for x in slopes]
        v = np.array(cov, dtype=np.float64).reshape(m, m)[np.ix_(idx, idx)]
        kept = []
        for i in range(len(slopes)):
            pivot = float(v[i, i])
            if kept:
                cc = v[kept, i]
                pivot -= float(na(cc) @ solve_sa(v[np.ix_(kept, kept)], cc))
            st["pivot_eq_tol"] += pivot == TOL
            st["pivot_1ulp_above"] += pivot == up(TOL)
            st["pivot_1ulp_below"] += pivot == dn(TOL)
            if pivot > TOL:
                kept.append(i)
        st["left_out_pivot"] += len(kept) < len(slopes)
        st["empty_kept"] += not kept
    return st


def lean_text(a, b, cls):
    ks = f'let cl : String := "{cls}"; let ids := fun (c : Char) => ((List.range cl.length).zip cl.toList).filterMap (fun (p : Nat \u00d7 Char) => if p.2 == c then some ({a} + p.1) else none); '
    body = "(" + " ++ ".join(f"[W ((ids '{c}').map iw), W ((ids '{c}').map ow)]" for c in "123") + ")"
    return LEAN_PRE + ks + body


def lean_trip(a, b, cls, B, K="1"):
    ks = f'let cl : String := "{cls}"; let ids := fun (c : Char) => ((List.range cl.length).zip cl.toList).filterMap (fun (p : Nat \u00d7 Char) => if p.2 == c then some ({a} + p.1) else none); '
    n = cls.count(K)
    blocks = [f"blk (((ids '{K}').drop {j * B}).take {B})" for j in range((n + B - 1) // B)]
    return LEAN_PRE + ks + "(" + " ++ ".join(blocks + [f"[W ((ids '{K}').map ow)]"]) + ")"


def py_trip(out, a, b, B, K="kept"):
    ks = [s for s in range(a, b) if out[s]["cls"] == K]
    res = []
    for j in range((len(ks) + B - 1) // B):
        bs = ks[j * B:(j + 1) * B]
        res += [t.w([x for s in bs for x in out[s]["core"]]), t.w([x for s in bs for x in out[s]["rs"]]), t.w([x for s in bs for x in out[s]["exl"]])]
    res.append(t.w([out[s]["ow"] for s in ks]))
    return res, ks


def py_blocks(out, a, b):
    res = []
    for c in "123":
        ss = [s for s in range(a, b) if CLS[out[s]["cls"]] == c]
        res += [t.w([out[s]["iw"] for s in ss]), t.w([out[s]["ow"] for s in ss])]
    return res


def main():
    mode, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    if mode == "--run":
        from collections import Counter
        out, stats = {}, Counter()
        for s in range(a, b):
            c = case(s)
            cl, d, ex = py_case(c)
            out[s] = dict(cls=cl, iw=in_digest(c), ow=d, ex=ex, core=LISTS.get(s, ([], [], []))[0], rs=LISTS.get(s, ([], [], []))[1], exl=LISTS.get(s, ([], [], []))[2])
            if cl in ("kept", "rejected", "linalg"):
                for k, v in wald_stats(c).items():
                    stats[(cl, k)] += v
        Path(HERE.parent / "work" / f"fz3_s03_{a}_{b}.py.json").write_text(json.dumps({str(k): v for k, v in out.items()}))
        print(Counter(v["cls"] for v in out.values()), Counter(v["ex"] for v in out.values() if v["ex"]))
        print(dict(stats))
    else:
        out = {int(k): v for k, v in json.loads(Path(HERE.parent / "work" / "fz3_s03_0_3600.py.json").read_text()).items()}
        cls = "".join(CLS[out[s]["cls"]] for s in range(a, b)) if mode != "--per" else ""
        if mode == "--trip":
            print(lean_trip(a, b, cls, int(sys.argv[4]), sys.argv[5] if len(sys.argv) > 5 else "1"))
        elif mode == "--tripexp":
            print(py_trip(out, a, b, int(sys.argv[4]), sys.argv[5] if len(sys.argv) > 5 else "kept")[0])
        elif mode == "--per":
            print(LEAN_PRE + f"(List.range {b - a}).flatMap (fun (i : Nat) => [iw ({a} + i), ow ({a} + i)])")
        elif mode == "--blk":
            print(lean_blk(a, b, cls, sys.argv[4], int(sys.argv[5])))
        elif mode == "--blkexp":
            print(py_blk(out, a, b, sys.argv[4], int(sys.argv[5]))[0])
        elif mode == "--text":
            print(lean_text(a, b, cls))
        else:
            print(py_blocks(out, a, b))


if __name__ == "__main__":
    main()
